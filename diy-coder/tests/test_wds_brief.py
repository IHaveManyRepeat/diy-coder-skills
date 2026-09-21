# -*- coding: utf-8 -*-
"""diy-wds-brief 确定性引擎 e2e 测试（B7a 批 W1；任务书 §2.6 八类必备 + 本技能特有边界）。

覆盖（任务书 §2.6 ①–⑨）：
- ① 门禁：`init` 无 `--project-type` → exit 2（argparse 用法错误）；非法值 → ENUM_INVALID
     exit 1；空串 → EMPTY_FIELD exit 1；`--output-dir` 缺席 → exit 2；`--instance` 不存在
- ② `init` 合法 exit 0 + 骨架结构（`project.status: 草稿` / `intake.stage: 分诊`）且骨架即过 check
- ③ 单记录 → 无记录级 ID：**重复 `init` 不覆盖已有骨架**（改 `--project-type` → SET_MISMATCH
     零写入；同值 → 不动内容）；产物损坏 → UNPARSABLE_YAML 零写入
- ④ `list` 只回五字段、`--status` 过滤生效；`show` 整份全文
- ⑤ `check` 四类违规检出：ENUM_INVALID / EMPTY_FIELD / STATUS_MISMATCH / TOKEN_UNRESOLVED
- ⑥ 跨技能门禁（§2.3.1）：本技能是**链的起点**——门禁 = 分诊完成（`intake.project_type`
     非空）；交付的四个下游读键（`brief.core` 四键 / `brief.content.content_language` /
     `brief.visual.visual_direction` / `brief.platform.platform_requirements`）在定稿后必须在场
- ⑦ 回执键完整性（`instance` 键在位恒 null / `warnings` 与 `violations` 同形 / `where` 正斜杠）；
     只读子命令**不含** `updated`，`init` 含
- ⑧ SKILL.md 契约冒烟（母本 §1/§2/§3/§4/§5/§6 六节逐字 + 终门句指向本引擎 + 产物路径声明句）
- ⑨ 本技能特有边界：**签核三型的段结构**（裁定 13 / 外部合同 11 节 / 服务协议 12 节 /
     内部审批 7 节）+ **74 项校验判定**（`steps/07-finish.md` 的 `- [ ]` 恰 74 行）

另含引擎内表核对（回报必答 ③④ 的机械证据）：直接导入引擎模块，比对三型节表与 74 项总数。

夹具全部落 tempdir 自建；不读写本仓库真实 diy-output；不依赖本机 git 状态。
运行：cd diy-coder && python -m unittest discover -s tests -p "test_wds_brief.py" -v
"""
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.join(HERE, "..", "skills", "diy-wds-brief")
ENGINE = os.path.join(SKILL_DIR, "scripts", "wds_brief.py")
SKILL_MD = os.path.join(SKILL_DIR, "SKILL.md")
FINISH_STEP = os.path.join(SKILL_DIR, "steps", "07-finish.md")
NL = chr(10)

BRIEF_FILE = "wds-brief.yaml"

# ---------------------------------------------------------------- 独立内表（非实现拷贝）
# 源侧取数位置：`wds-0-alignment-signoff/workflow.md:98-111`（合同 11 节）、
# `wds-1-project-brief/templates/service-agreement.template.md`（服务协议 12 节）、
# `wds-0-alignment-signoff/steps-c/step-06a-build-internal-signoff.md:68-104`（内部 9 节 → 7 节）。
CONTRACT_SECTIONS = [
    "project_overview", "business_model", "scope_of_work", "payment_terms", "timeline",
    "availability", "confidentiality", "not_to_exceed", "work_initiation",
    "terms_and_conditions", "approval",
]
SERVICE_SECTIONS = [
    "project_overview", "scope_of_services", "our_commitment", "timeline",
    "why_it_matters", "expected_outcomes", "service_terms", "risks_and_considerations",
    "confidentiality", "not_to_exceed", "terms_and_conditions", "approval",
]
INTERNAL_SECTIONS = [
    "project_overview", "goals_and_metrics", "budget_and_resources", "ownership",
    "approval_and_signoff", "timeline_and_milestones", "optional_sections",
]

# §2.4：简报的 74 项校验（步骤 v1–v6 = 15+14+10+12+12+11）落 steps/07-finish.md
VALIDATION_TOTAL = 74

# 母本六节锚串（suite-texts.md §1/§2/§3/§4/§5/§6，逐字）
INSTANCE_ZH = ("实例解析（FR-4.5/D-9）由工具脚本执行：运行 "
               "`python \"{project-root}/.claude/skills/diy-tools/scripts/diyc.py\" "
               "resolve [--instance <name>] --json`，把回执里的 `output_dir` "
               "当作本次运行唯一的读写根目录。")
DISCIPLINE_ZH = ("- **写作纪律。** 主字段 = 大白话主句；数字/枚举内联；"
                 "机器语法（命令/旗标/路径）进括号；机器锚点逐字保留"
                 "（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 "
                 "`diy-design` 的 detect 启发式。schema 若定义 `plain`："
                 "一行写清该条目为什么存在，绝不写是什么（转述会漂移）；"
                 "只写难懂的条目。若定义 `detail`：过程叙述——结论留在主字段。")
ANCHOR_RESOLVE_KEYS = ("解析 `project.communication_language` / "
                       "`project.document_output_language` / `paths.output_dir`")
ANCHOR_READ_DISCIPLINE = ("读取纪律：预载预算 = 本文件、上述配置与回执、`steps/` 下当前那一个文件"
                          "——绝不批量预载；执行期读取以每个步骤开头的 `Read (input)` 行为唯一权威，"
                          "**主文件不列举封闭清单**。")
ANCHOR_RENDER_SILENT = "渲染是静默旁路——只写调用命令"
ANCHOR_PRECISE = ("- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；"
                  "不复述上游已写的信息（引用 ID）；不写没有信息量的套话。")

RECEIPT_KEYS = ("ok", "command", "project_root", "output_dir", "instance",
                "violations", "warnings", "counts")
V_SHAPE = ("code", "where", "msg")
# 红线（与 test_suite_texts.py 的守卫同式）：教模型传引擎会拒的 --previous 类型
PREVIOUS_CHECK_RE = re.compile(r"check --type ([\w-]+) --previous")

# 下游读契约（§2.3.1 冻结）：W2 从 wds-brief.yaml 读这四组键
DOWNSTREAM_CORE_KEYS = ("vision", "positioning", "target_users", "product_concept")
DOWNSTREAM_KEYS = (("brief", "core"), ("brief", "content"), ("brief", "visual"),
                   ("brief", "platform"))


def run_engine(engine_path, args):
    return subprocess.run([sys.executable, engine_path] + args,
                          capture_output=True, text=True, encoding="utf-8")


def product_yaml(status="已定稿", stage="收尾", project_type="greenfield",
                 brief_level="complete", core=None, content=None, visual=None,
                 platform=None, alignment=None, signoff=None, client_profile=None):
    """手搓完整产物（各段均可局部替换）——用于 check 面用例。"""
    core = core if core is not None else {
        "vision": "让本地咖啡馆有可自助的官网",
        "positioning": "面向社区咖啡馆的平价建站服务",
        "business_model": "B2C",
        "target_users": "独立咖啡馆主理人",
        "product_concept": "一页式菜单 + 门店故事",
        "success_metrics": ["上线 4 周内 30 家签约"],
        "competitive_landscape": {"alternatives": ["通用模板站"], "advantage": "行业话术库"},
        "constraints": ["预算 3 万以内"],
    }
    content = content if content is not None else {
        "content_language": {
            "personality": {"attributes": ["温厚", "懂行", "不端着"]},
            "tone": {"core": "像熟客打招呼"},
            "languages": {"primary": "zh-CN"},
            "seo_keywords": {"primary": ["社区咖啡馆建站"]},
            "content_structure": {"type": "单页长滚动"},
        }}
    visual = visual if visual is not None else {
        "visual_direction": {
            "inspiration": {"sites": ["参考站 A"], "takeaways": ["暖色留白"]},
            "existing_brand": {"assets": ["logo"]},
            "references": {"sites": ["参考站 B"]},
            "design_style": {"ui_style": "极简编辑风"},
            "layout_effects": {"approach": "单列，轻滚动动效"},
            "imagery": {"style": "自然光实拍"},
        }}
    platform = platform if platform is not None else {
        "platform_requirements": {
            "tech_stack": {"cms": "Astro", "hosting": "Netlify"},
            "integrations": [{"name": "表单", "purpose": "收集线索"}],
            "contact_strategy": {"primary": "表单 + 微信"},
            "multilingual": {"supported": ["zh-CN"]},
        }}
    alignment = alignment if alignment is not None else {
        "status": "不需要",
    }
    signoff = signoff if signoff is not None else {
        "type": "不签核",
        "status": "未开始",
        "external_contract": {},
        "service_agreement": {},
        "internal": {},
    }
    client_profile = client_profile if client_profile is not None else {
        "organization": {"type": "startup", "size": "8 人"},
        "key_people": {"primary_contact": {"name": "林", "role": "创始人"}},
        "internal_drivers": {"trigger": "老客户流失"},
        "collaboration": {"communication": "微信，响应快"},
    }
    body = {
        "project": {"name": "mini", "created": "2026-09-18", "updated": "2026-09-21",
                    "status": status},
        "intake": {"project_type": project_type, "complexity": "standard",
                   "brief_level": brief_level, "strategic_analysis": "full",
                   "stage": stage},
        "client_profile": client_profile,
        "brief": {"core": core, "content": content, "visual": visual, "platform": platform},
        "alignment": alignment,
        "signoff": signoff,
        "revisions": [],
    }
    return dump(body)


def dump(node, indent=0):
    """极简 YAML 序列化（只覆盖本测试用到的形状；避免依赖引擎实现）。"""
    pad = "  " * indent
    if isinstance(node, dict):
        if not node:
            return pad + "{}"
        out = []
        for key, value in node.items():
            if isinstance(value, (dict, list)) and value:
                out.append("%s%s:" % (pad, key))
                out.append(dump(value, indent + 1))
            elif isinstance(value, (dict, list)):
                out.append("%s%s: %s" % (pad, key, "{}" if isinstance(value, dict) else "[]"))
            else:
                out.append("%s%s: %s" % (pad, key, scalar(value)))
        return NL.join(out)
    if isinstance(node, list):
        out = []
        for item in node:
            if isinstance(item, (dict, list)) and item:
                rendered = dump(item, indent + 1).split(NL)
                out.append("%s- %s" % (pad, rendered[0].strip()))
                out.extend(rendered[1:])
            elif isinstance(item, (dict, list)):
                out.append("%s- %s" % (pad, "{}" if isinstance(item, dict) else "[]"))
            else:
                out.append("%s- %s" % (pad, scalar(item)))
        return NL.join(out)
    return pad + scalar(node)


def scalar(value):
    text = str(value)
    # 纯词不加引号；但日期类（`2026-09-18`）必须引号化——否则 PyYAML 会解成 date 对象
    if text and all(ch.isalnum() or ch in "-_" for ch in text) and not re.match(
            r"\d{4}-\d{2}-\d{2}", text):
        return text
    return '"%s"' % text.replace('"', '\\"')


class EngineCase(unittest.TestCase):
    """tmp 项目根 + diy-output 目录的公共夹具。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="wdsbrief-")
        self.root = self.tmp.name
        self.out = os.path.join(self.root, "diy-output")
        os.makedirs(self.out, exist_ok=True)
        self.engine_path = ENGINE

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, rel, content):
        path = os.path.join(self.root, rel)
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with io.open(path, "w", encoding="utf-8", newline="") as handle:
            handle.write(content)
        return path

    def read_text(self, rel):
        with io.open(os.path.join(self.root, rel), encoding="utf-8") as handle:
            return handle.read()

    def product(self, content):
        return self.write("diy-output/" + BRIEF_FILE, content)

    def engine(self, *args):
        return run_engine(self.engine_path,
                          list(args) + ["--project-root", self.root,
                                        "--output-dir", self.out, "--json"])

    def raw(self, *args):
        return run_engine(self.engine_path, list(args))

    def init(self, *extra):
        return self.engine("init", *extra)

    def check(self, *extra):
        return self.engine("check", *extra)

    def results(self, proc):
        return json.loads(proc.stdout)

    def codes(self, proc):
        return {x["code"] for x in self.results(proc)["violations"]}


class GateTests(EngineCase):
    """§2.6 ① 门禁（用法错误 exit 2 ≠ 枚举违规 exit 1 ≠ 空值 EMPTY_FIELD）。"""

    # trace: 任务书 §2.6 ①（init 无 --project-type → exit 2）
    def test_gate_missing_project_type_is_usage_error(self):
        r = self.raw("init", "--project-root", self.root,
                     "--output-dir", self.out, "--json")
        self.assertEqual(r.returncode, 2, "缺 --project-type 须为 argparse 用法错误 exit 2：%s"
                         % (r.stdout + r.stderr))

    # trace: 任务书 §2.6 ①（非法值 → ENUM_INVALID exit 1）
    def test_gate_invalid_project_type_is_enum_invalid(self):
        r = self.init("--project-type", "brownfield2")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertEqual(self.codes(r), {"ENUM_INVALID"})

    # trace: 任务书 §2.6 ① / §2.3.1（分诊未完成 = 项目类型为空 → 零产出停止）
    def test_gate_blank_project_type_is_empty_field(self):
        r = self.init("--project-type", "   ")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertEqual(self.codes(r), {"EMPTY_FIELD"})
        self.assertFalse(os.path.exists(os.path.join(self.out, BRIEF_FILE)),
                         "门禁拒绝须零产出")

    # trace: 任务书 §2.2（--output-dir 必填于写盘子命令；--instance 一律不做）
    def test_gate_output_dir_mandatory_and_no_instance_flag(self):
        r = self.raw("init", "--project-type", "greenfield",
                     "--project-root", self.root, "--json")
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        r2 = self.engine("list", "--instance", "demo")
        self.assertEqual(r2.returncode, 2, "--instance 不得进签名表：%s" % (r2.stdout + r2.stderr))


class InitTests(EngineCase):
    """§2.6 ②③ init 骨架、单记录不覆盖、拒绝损坏。"""

    # trace: 任务书 §2.6 ②（exit 0 + 骨架结构，含 project.status: 草稿）
    def test_init_creates_skeleton_passing_check(self):
        r = self.init("--project-type", "greenfield", "--complexity", "complex")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = self.results(r)
        self.assertIsNone(data["instance"])
        self.assertIn("updated", data)
        text = self.read_text("diy-output/" + BRIEF_FILE)
        self.assertIn("status: 草稿", text)
        self.assertIn("project_type: greenfield", text)
        self.assertIn("complexity: complex", text)
        self.assertIn("stage: 分诊", text)
        self.assertIn("client_profile:", text)
        self.assertIn("revisions: []", text)
        # 骨架即过 check（草稿期宽松：主体段可空）
        c = self.check()
        self.assertEqual(c.returncode, 0, c.stdout + c.stderr)
        self.assertEqual(self.results(c)["counts"]["records"], 1)

    # trace: 任务书 §2.6 ③（单记录 → 改「重复 init 不覆盖已有骨架」为非 ID 用例）
    def test_reinit_does_not_overwrite_existing_skeleton(self):
        self.assertEqual(self.init("--project-type", "greenfield").returncode, 0)
        # 用户已填的内容：手工落一段，重跑 init 后必须一字不动
        self.product(self.read_text("diy-output/" + BRIEF_FILE)
                     .replace("  core: {}", "  core:" + NL + "    vision: 用户写的愿景"))
        before = self.read_text("diy-output/" + BRIEF_FILE)
        same = self.init("--project-type", "greenfield")
        self.assertEqual(same.returncode, 0, same.stdout + same.stderr)
        self.assertTrue(self.results(same)["warnings"], "同值重跑须给一行「未覆盖」warning")
        after = self.read_text("diy-output/" + BRIEF_FILE)
        self.assertIn("vision: 用户写的愿景", after, "重复 init 不得覆盖已有内容")
        self.assertEqual([ln for ln in after.split(NL) if not ln.startswith("  updated:")],
                         [ln for ln in before.split(NL) if not ln.startswith("  updated:")],
                         "除 project.updated 外不得改动任何一行")
        # 改分诊结论 → SET_MISMATCH 且零写入（分诊是整链路由的根，不得被静默改写）
        diff = self.init("--project-type", "brownfield")
        self.assertEqual(diff.returncode, 1, diff.stdout)
        self.assertEqual(self.codes(diff), {"SET_MISMATCH"})
        self.assertNotIn("project_type: brownfield",
                         self.read_text("diy-output/" + BRIEF_FILE))

    # trace: 任务书 §2.6 ③（损坏产物拒绝且零写入）
    def test_init_refuses_damaged_product_with_zero_write(self):
        self.product("project: [" + NL)
        before = self.read_text("diy-output/" + BRIEF_FILE)
        bad = self.init("--project-type", "greenfield")
        self.assertEqual(bad.returncode, 1, bad.stdout)
        self.assertNotIn("Traceback", bad.stderr)
        self.assertEqual(self.codes(bad), {"UNPARSABLE_YAML"})
        self.assertEqual(self.read_text("diy-output/" + BRIEF_FILE), before,
                         "拒绝路径不得改动产物一个字节")


class ListShowTests(EngineCase):
    """§2.6 ④ list / show（单记录 → 至多一条）。"""

    # trace: 任务书 §2.6 ④（只回五字段 + --status 过滤生效）
    def test_list_returns_five_fields_and_filters_by_status(self):
        self.init("--project-type", "greenfield")
        r = self.engine("list")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = self.results(r)
        self.assertEqual(len(data["records"]), 1)
        self.assertEqual(sorted(data["records"][0]),
                         ["name", "project_type", "stage", "status", "updated"])
        keep = self.engine("list", "--status", "草稿")
        self.assertEqual(len(self.results(keep)["records"]), 1)
        none = self.engine("list", "--status", "已定稿")
        self.assertEqual(self.results(none)["records"], [])
        bad = self.engine("list", "--status", "草稿中")
        self.assertEqual(bad.returncode, 1, bad.stdout)
        self.assertEqual(self.codes(bad), {"ENUM_INVALID"})
        # 产物缺席：按空列表处理，不报错
        os.remove(os.path.join(self.out, BRIEF_FILE))
        empty = self.engine("list")
        self.assertEqual(empty.returncode, 0, empty.stdout + empty.stderr)
        self.assertEqual(self.results(empty)["records"], [])

    # trace: 任务书 §2.6 ④（show 整份全文，单记录无 --id）
    def test_show_returns_whole_document(self):
        self.init("--project-type", "brownfield")
        r = self.engine("show")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        doc = self.results(r)["document"]
        self.assertEqual(doc["intake"]["project_type"], "brownfield")
        self.assertIn("brief", doc)
        self.assertIn("signoff", doc)
        # 产物缺席 → MISSING_FILE
        os.remove(os.path.join(self.out, BRIEF_FILE))
        miss = self.engine("show")
        self.assertEqual(miss.returncode, 1, miss.stdout)
        self.assertEqual(self.codes(miss), {"MISSING_FILE"})


class CheckTests(EngineCase):
    """§2.6 ⑤ check 的四类检出 + 定稿同档规则。"""

    def complete(self, **kwargs):
        self.product(product_yaml(**kwargs))
        return os.path.join(self.out, BRIEF_FILE)

    # trace: 任务书 §2.6 ⑤（枚举越界 → ENUM_INVALID）
    def test_check_detects_enum_invalid(self):
        self.complete(status="已定稿", stage="收尾")
        ok = self.check("--final")
        self.assertEqual(ok.returncode, 0, ok.stdout + ok.stderr)
        self.complete(status="定稿")
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ENUM_INVALID", self.codes(r))

    # trace: 任务书 §2.6 ⑤（必填键缺失 → EMPTY_FIELD，where 点名键名）
    def test_check_detects_missing_required_key_with_name(self):
        core = {"vision": "有", "target_users": "有"}   # 缺 positioning 等
        self.complete(core=core)
        r = self.check("--final")
        self.assertEqual(r.returncode, 1, r.stdout)
        places = [x["where"] for x in self.results(r)["violations"] if x["code"] == "EMPTY_FIELD"]
        self.assertTrue(any(x.endswith("brief.core.positioning") for x in places), places)

    # trace: 任务书 §2.6 ⑤（status 与 stage 不同档 → STATUS_MISMATCH）
    def test_check_detects_status_stage_mismatch(self):
        self.complete(status="已定稿", stage="视觉")
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("STATUS_MISMATCH", self.codes(r))
        # --final 要求 status: 已定稿
        self.complete(status="草稿", stage="收尾")
        final = self.check("--final")
        self.assertEqual(final.returncode, 1, final.stdout)

    # trace: 任务书 §2.6 ⑤ / §10 项 7（未解析令牌 → TOKEN_UNRESOLVED）
    def test_check_detects_unresolved_token_and_assumption(self):
        core = {"vision": "使用 {skill-name} 生成", "positioning": "有",
                "business_model": "B2C", "target_users": "有", "product_concept": "有",
                "success_metrics": ["有"], "competitive_landscape": {"a": "有"},
                "constraints": ["有"]}
        self.complete(core=core)
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("TOKEN_UNRESOLVED", self.codes(r))
        self.assertIn("{skill-name}", r.stdout)
        # 白名单令牌不报
        core["vision"] = "{project-root}/diy-output 与 {output_dir}"
        self.complete(core=core)
        self.assertEqual(self.check().returncode, 0)

    # trace: 任务书 §2.6 ⑤ + §10 项 7（--final 零 [假设]）
    def test_final_rejects_assumption_mark(self):
        core = {"vision": "[假设] 客户会买", "positioning": "有",
                "business_model": "B2C", "target_users": "有", "product_concept": "有",
                "success_metrics": ["有"], "competitive_landscape": {"a": "有"},
                "constraints": ["有"]}
        self.complete(core=core)
        r = self.check("--final")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ASSUMPTION_PRESENT", self.codes(r))

    # trace: 任务书 §2.6 ⑤（产物缺席 → MISSING_FILE；损坏 → UNPARSABLE_YAML）
    def test_check_missing_and_damaged_product(self):
        miss = self.check()
        self.assertEqual(miss.returncode, 1, miss.stdout)
        self.assertEqual(self.codes(miss), {"MISSING_FILE"})
        self.product("intake: [" + NL)
        bad = self.check()
        self.assertEqual(bad.returncode, 1, bad.stdout)
        self.assertEqual(self.codes(bad), {"UNPARSABLE_YAML"})

    # trace: 任务书 §0.2 裁定 14（简报档位=简化 → 各段收窄必填集）
    def test_simplified_brief_level_narrows_required_set(self):
        core = {"vision": "有", "target_users": "有", "constraints": ["有"]}
        content = {"content_language": {"languages": {"primary": "zh-CN"}}}
        visual = {"visual_direction": {"design_style": {"ui_style": "极简"}}}
        platform = {"platform_requirements": {"tech_stack": {"cms": "Astro"}}}
        self.complete(brief_level="simplified", core=core, content=content,
                      visual=visual, platform=platform)
        r = self.check("--final")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    # trace: 任务书 §2.3 + §2.3.1（B2B 时 business_customers 必填）
    def test_b2b_requires_business_customers(self):
        core = {"vision": "有", "positioning": "有", "business_model": "B2B",
                "target_users": "有", "product_concept": "有", "success_metrics": ["有"],
                "competitive_landscape": {"a": "有"}, "constraints": ["有"]}
        self.complete(core=core)
        r = self.check("--final")
        self.assertEqual(r.returncode, 1, r.stdout)
        places = [x["where"] for x in self.results(r)["violations"]]
        self.assertTrue(any(x.endswith("brief.core.business_customers") for x in places), places)


class CrossSkillGateTests(EngineCase):
    """§2.6 ⑥ 跨技能门禁（§2.3.1）：W1 是链的起点，交付四组下游读键。"""

    # trace: 任务书 §2.3.1（入口技能门禁 = 分诊完成；上游产物门禁不存在）
    def test_entry_gate_is_triage_not_upstream_product(self):
        # 库里没有任何上游产物时 init 照常放行——本技能无上游门禁
        self.assertEqual(sorted(os.listdir(self.out)), [])
        r = self.init("--project-type", "greenfield")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        # 分诊未完成（project_type 空）→ check 报违规，且不得定稿
        self.product(product_yaml(status="已定稿", stage="收尾", project_type=""))
        bad = self.check("--final")
        self.assertEqual(bad.returncode, 1, bad.stdout)
        places = [x["where"] for x in self.results(bad)["violations"]]
        self.assertTrue(any("intake.project_type" in x for x in places), places)

    # trace: 任务书 §2.3.1（下游读四键在定稿后必须在场——W2/W3 的契约锚点）
    def test_frozen_downstream_keys_present_after_final(self):
        self.product(product_yaml(status="已定稿", stage="收尾"))
        r = self.check("--final")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        doc = self.results(self.engine("show"))["document"]
        self.assertEqual(doc["project"]["status"], "已定稿")
        core = doc["brief"]["core"]
        for key in DOWNSTREAM_CORE_KEYS:
            self.assertTrue(core.get(key), "下游读键 brief.core.%s 缺席" % key)
        self.assertTrue(doc["brief"]["content"]["content_language"])
        self.assertEqual(sorted(doc["brief"]["visual"]["visual_direction"]),
                         sorted(["inspiration", "existing_brand", "references",
                                 "design_style", "layout_effects", "imagery"]))
        self.assertTrue(doc["brief"]["platform"]["platform_requirements"])

    # trace: 任务书 §2.2 红线（终门走自带引擎；全库零 `check --type <WDS 型> --previous`）
    def test_no_wds_type_previous_check_taught(self):
        for rel in ["SKILL.md"] + ["steps/" + n for n in sorted(
                os.listdir(os.path.join(SKILL_DIR, "steps"))) if n.endswith(".md")]:
            with io.open(os.path.join(SKILL_DIR, rel), encoding="utf-8") as handle:
                text = handle.read()
            self.assertIsNone(PREVIOUS_CHECK_RE.search(text),
                              "%s 教了 `check --type <型> --previous`（diyc 8 型封闭集）" % rel)
            for wds_type in ("wds-brief", "wds-trigger", "wds-scenarios"):
                self.assertNotIn("--type %s" % wds_type, text,
                                 "%s 把 WDS 型当成了 diyc 的类型" % rel)


class ReceiptTests(EngineCase):
    """§2.6 ⑦ 回执 schema。"""

    # trace: 任务书 §2.2（公共键 + instance 恒 null + warnings 同形 + 单行 JSON）
    def test_receipt_keys_and_json_single_line(self):
        self.assertFalse(os.path.exists(os.path.join(self.out, BRIEF_FILE)))
        r = self.engine("list")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip().count(NL), 0, "须为单行 JSON")
        data = self.results(r)
        for key in RECEIPT_KEYS:
            self.assertIn(key, data, "回执缺公共键 %s" % key)
        self.assertIsNone(data["instance"], "本批不做实例，但键在位恒 null")
        self.assertEqual(data["command"], "list")
        self.assertEqual(data["project_root"], self.root)
        self.assertNotIn("updated", data, "只读子命令回执不含 updated")
        self.assertFalse(os.path.exists(os.path.join(self.out, BRIEF_FILE)),
                         "只读子命令不得写盘")
        init = self.results(self.init("--project-type", "greenfield"))
        self.assertIn("updated", init, "init 写盘回执须含 updated")
        bad = self.init("--project-type", "")
        for item in self.results(bad)["violations"]:
            self.assertEqual(sorted(item), sorted(V_SHAPE))
            self.assertNotIn("\\\\", item["where"])

    # trace: 任务书 §2.2（--output-dir 必填于写盘子命令；只读子命令签名可省 → 需读产物时
    #        明确报缺：exit 1 结构化违规，而非 exit 2 argparse 用法错误）
    def test_output_dir_optional_in_signature_but_reported_when_needed(self):
        for command in ("list", "show", "check"):
            r = self.raw(command, "--project-root", self.root, "--json")
            self.assertEqual(r.returncode, 1,
                             "%s 省 --output-dir 须为结构化违规 exit 1（签名可省）：%s"
                             % (command, r.stdout + r.stderr))
            data = json.loads(r.stdout)
            self.assertIsNone(data["output_dir"])
            self.assertEqual({x["code"] for x in data["violations"]}, {"EMPTY_FIELD"})
            self.assertIn("--output-dir", data["violations"][0]["where"])


class SignoffSchemaTests(EngineCase):
    """§2.6 ⑨ 本技能特有边界：签核三型的段结构（裁定 13）。"""

    def contract_signoff(self, sections=None, mode="固定价"):
        payload = {"pricing_model": mode, "finalized": True,
                   "sections": sections if sections is not None else
                   {key: "%s 的内容" % key for key in CONTRACT_SECTIONS}}
        return {"type": "对外合同", "status": "已定稿", "external_contract": payload,
                "service_agreement": {}, "internal": {}}

    def contract_sections_without(self, *dropped):
        return {key: "%s 的内容" % key for key in CONTRACT_SECTIONS if key not in dropped}

    # trace: V-01（高）——`availability`（源 05f）是**条件节**：源侧语义为「长期聘用才谈可用性」，
    #        引擎此前把它当无条件必填，与 steps/03-signoff.md 第 3 节的口径对打。
    def test_external_contract_availability_is_conditional(self):
        # 前置：11 节齐全（含 availability）→ 通过
        self.product(product_yaml(status="已定稿", stage="收尾",
                                  signoff=self.contract_signoff()))
        r = self.check("--final")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        # ① 非长期聘用模式 + 10 节（缺 availability）→ **rc=0 通过**（接受缺省）
        ten = self.contract_sections_without("availability")
        for mode in ("固定价", "计时", "混合"):
            self.product(product_yaml(status="已定稿", stage="收尾",
                                      signoff=self.contract_signoff(ten, mode=mode)))
            ok = self.check("--final")
            self.assertEqual(ok.returncode, 0,
                             "%s 模式不该要求 availability：%s" % (mode, ok.stdout + ok.stderr))
        # ② 长期聘用 + 缺 availability → **rc=1**（条件性生效，where 点名该节）
        self.product(product_yaml(status="已定稿", stage="收尾",
                                  signoff=self.contract_signoff(ten, mode="长期聘用")))
        bad = self.check("--final")
        self.assertEqual(bad.returncode, 1, bad.stdout)
        places = [x["where"] for x in self.results(bad)["violations"]]
        self.assertTrue(any(x.endswith("sections.availability") for x in places), places)
        # 填了但留空 → 仍报 EMPTY_FIELD（「若填了则照常校验」）
        blank = self.contract_sections_without()
        blank["availability"] = "   "
        self.product(product_yaml(status="已定稿", stage="收尾",
                                  signoff=self.contract_signoff(blank, mode="固定价")))
        empty = self.check("--final")
        self.assertEqual(empty.returncode, 1, empty.stdout)
        places = [x["where"] for x in self.results(empty)["violations"]]
        self.assertTrue(any(x.endswith("sections.availability") for x in places), places)

    # trace: V-01 连带的边界——条件性只放宽 availability 一节，其余 10 节仍逐节硬性
    def test_external_contract_other_sections_remain_mandatory(self):
        for dropped in ("confidentiality", "not_to_exceed", "approval", "scope_of_work"):
            ten = self.contract_sections_without(dropped)
            self.product(product_yaml(status="已定稿", stage="收尾",
                                      signoff=self.contract_signoff(ten, mode="固定价")))
            r = self.check("--final")
            self.assertEqual(r.returncode, 1, "%s 仍是必填：%s" % (dropped, r.stdout))
            places = [x["where"] for x in self.results(r)["violations"]]
            self.assertTrue(any(x.endswith("sections." + dropped) for x in places), places)

    # trace: 任务书 §3 W1 卡（服务协议无构建步 → 本批补齐 12 节构建）
    def test_service_agreement_requires_twelve_sections(self):
        payload = {"pricing_model": "计时", "finalized": True,
                   "sections": {key: "内容" for key in SERVICE_SECTIONS}}
        signoff = {"type": "服务协议", "status": "已定稿", "external_contract": {},
                   "service_agreement": payload, "internal": {}}
        self.product(product_yaml(status="已定稿", stage="收尾", signoff=signoff))
        r = self.check("--final")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        payload["sections"].pop("service_terms")
        self.product(product_yaml(status="已定稿", stage="收尾", signoff=signoff))
        bad = self.check("--final")
        self.assertEqual(bad.returncode, 1, bad.stdout)
        places = [x["where"] for x in self.results(bad)["violations"]]
        self.assertTrue(any(x.endswith("sections.service_terms") for x in places), places)

    # trace: 任务书 §3 W1 卡（内部审批型：源 06a 的 9 节 → 7 节落位）
    def test_internal_signoff_requires_seven_sections(self):
        payload = {"finalized": True,
                   "sections": {key: "内容" for key in INTERNAL_SECTIONS}}
        signoff = {"type": "内部审批", "status": "已定稿", "external_contract": {},
                   "service_agreement": {}, "internal": payload}
        self.product(product_yaml(status="已定稿", stage="收尾", signoff=signoff))
        r = self.check("--final")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    # trace: 任务书 §3 W1 卡（分型门：type 与已填段必须一致）
    def test_signoff_type_must_match_filled_branch(self):
        signoff = {"type": "对外合同", "status": "已定稿", "external_contract": {},
                   "service_agreement": {}, "internal": {}}
        self.product(product_yaml(status="已定稿", stage="收尾", signoff=signoff))
        r = self.check("--final")
        self.assertEqual(r.returncode, 1, r.stdout)
        places = [x["where"] for x in self.results(r)["violations"]]
        self.assertTrue(any("external_contract" in x for x in places), places)

    # trace: 任务书 §3 W1 卡（「跳过」是合法分型，不阻断定稿）
    def test_skip_branch_is_legal(self):
        self.product(product_yaml(status="已定稿", stage="收尾"))
        r = self.check("--final")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    # trace: 任务书 §3 W1 卡（对齐段：不需要 / 未开始 / 进行中 / 已定稿 四态）
    def test_alignment_status_enum_and_required_sections(self):
        self.product(product_yaml(status="已定稿", stage="收尾",
                                  alignment={"status": "已定稿", "realization": "有"}))
        bad = self.check("--final")
        self.assertEqual(bad.returncode, 1, bad.stdout)
        places = [x["where"] for x in self.results(bad)["violations"]]
        self.assertTrue(any(x.endswith("alignment.summary") for x in places), places)
        # 十节齐全 → 放行
        full = {"status": "已定稿"}
        for key in ("realization", "why_it_matters", "how_we_see_it_working",
                    "paths_we_explored", "recommended_solution", "path_forward",
                    "value_we_create", "cost_of_inaction", "our_commitment", "summary"):
            full[key] = "内容"
        self.product(product_yaml(status="已定稿", stage="收尾", alignment=full))
        self.assertEqual(self.check("--final").returncode, 0)


class SkillContractTests(unittest.TestCase):
    """§2.6 ⑧ SKILL.md 契约冒烟（母本六节逐字 + 终门句 + 产物路径声明句）。"""

    def read_skill(self):
        if not os.path.isfile(SKILL_MD):
            self.skipTest("SKILL.md 尚未交付——契约冒烟待补")
        with io.open(SKILL_MD, encoding="utf-8") as handle:
            return handle.read()

    # trace: 任务书 §2.1 / §8 验收 #8#9#11（六节在场 + 四段 + ≤90 行）
    def test_skill_contract_smoke(self):
        raw = self.read_skill()
        for anchor, label in ((INSTANCE_ZH, "母本 §1 实例解析中文定稿"),
                              (DISCIPLINE_ZH, "母本 §2 写作纪律块"),
                              (ANCHOR_RESOLVE_KEYS, "母本 §3 配置解析键路径"),
                              (ANCHOR_READ_DISCIPLINE, "母本 §4 读取纪律"),
                              (ANCHOR_RENDER_SILENT, "母本 §5 渲染静默"),
                              (ANCHOR_PRECISE, "母本 §6 精准简练")):
            self.assertIn(anchor, raw, "缺 %s（逐字）" % label)
        for section in ("## 激活时", "## 工作流", "## 结构", "## 规则"):
            self.assertIn(section, raw, "缺段 %s" % section)
        self.assertIn("wds_brief.py", raw, "终门句未指向本技能领域引擎")
        self.assertIn("check --final", raw, "终门句缺 check --final")
        self.assertIn("wds-brief.yaml", raw, "产物路径声明句不在场")
        self.assertIn("diy-wds-brief", raw)
        self.assertIsNone(PREVIOUS_CHECK_RE.search(raw),
                          "红线：不得教 diyc.py 会拒的 `check --type <型> --previous`")
        lines = raw.replace(NL + chr(13), NL).replace(chr(13) + NL, NL).rstrip(NL).split(NL)
        self.assertLessEqual(len(lines), 90, "SKILL.md 超 90 行（薄主文件硬阈值）")

    # trace: 任务书 §2.4（7 个步骤文件冻结名 + 一行指路一致）
    def test_step_files_frozen_names(self):
        names = sorted(n for n in os.listdir(os.path.join(SKILL_DIR, "steps"))
                       if n.endswith(".md"))
        self.assertEqual(names, ["01-intake.md", "02-alignment.md", "03-signoff.md",
                                 "04-core.md", "05-content.md", "06-visual.md",
                                 "07-finish.md"])
        raw = self.read_skill()
        for name in names:
            self.assertIn(name, raw, "SKILL.md 工作流段缺 %s 的一行指路" % name)


class ValidationChecklistTests(unittest.TestCase):
    """§2.6 ⑨ 74 项校验判定（§2.4：简报 74 项落 07-finish.md）。"""

    def read_finish(self):
        if not os.path.isfile(FINISH_STEP):
            self.skipTest("steps/07-finish.md 尚未交付——74 项校验待补")
        with io.open(FINISH_STEP, encoding="utf-8") as handle:
            return handle.read()

    # trace: 任务书 §2.4 / §0.2 裁定 14 P7（74 项全保但去重）
    def test_seventy_four_checkbox_items(self):
        raw = self.read_finish()
        items = [ln for ln in raw.replace(chr(13) + NL, NL).split(NL)
                 if ln.strip().startswith("- [ ]")]
        self.assertEqual(len(items), VALIDATION_TOTAL,
                         "07-finish.md 的 `- [ ]` 须恰 %d 项（源 steps-v 6 步 74 项），实为 %d"
                         % (VALIDATION_TOTAL, len(items)))

    # trace: 任务书 §2.4（六步维度分组在场）
    def test_six_dimension_groups_present(self):
        raw = self.read_finish()
        for label in ("简报完备", "触发图一致", "SEO 策略", "内容与语言",
                      "视觉方向", "平台需求"):
            self.assertIn(label, raw, "缺质检维度分组 %s" % label)


class InternalTableTests(unittest.TestCase):
    """引擎内表核对（回报必答 ③④ 的机械证据；直接导入引擎模块）。"""

    def load_module(self):
        if not os.path.isfile(ENGINE):
            self.skipTest("wds_brief.py 尚未交付")
        spec = importlib.util.spec_from_file_location("wds_brief_under_test", ENGINE)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    # trace: 任务书 §3 W1 卡（三型节表：11 / 12 / 7）
    def test_signoff_section_tables(self):
        mod = self.load_module()
        contract = list(getattr(mod, "CONTRACT_SECTIONS", ()))
        service = list(getattr(mod, "SERVICE_SECTIONS", ()))
        internal = list(getattr(mod, "INTERNAL_SECTIONS", ()))
        self.assertEqual(contract, CONTRACT_SECTIONS, "合同节表须与源 11 节逐字一致")
        self.assertEqual(service, SERVICE_SECTIONS, "服务协议节表须与模板 12 节逐字一致")
        self.assertEqual(internal, INTERNAL_SECTIONS, "内部审批节表须与源 06a 逐字一致")
        self.assertEqual(len(contract), 11)
        self.assertEqual(len(service), 12)
        self.assertEqual(len(internal), 7)

    # trace: 任务书 §2.3.1（下游读四键名冻结）
    def test_frozen_downstream_contract_keys(self):
        mod = self.load_module()
        self.assertEqual(tuple(getattr(mod, "CORE_REQUIRED", ())),
                         ("vision", "positioning", "business_model", "target_users",
                          "product_concept", "success_metrics",
                          "competitive_landscape", "constraints"))
        self.assertEqual(tuple(getattr(mod, "CONTENT_KEYS", ())), ("content_language",))
        self.assertEqual(tuple(getattr(mod, "VISUAL_KEYS", ())), ("visual_direction",))
        self.assertEqual(tuple(getattr(mod, "PLATFORM_KEYS", ())), ("platform_requirements",))
        self.assertEqual(tuple(getattr(mod, "VISUAL_DIRECTION_KEYS", ())),
                         ("inspiration", "existing_brand", "references",
                          "design_style", "layout_effects", "imagery"))
        self.assertEqual(tuple(getattr(mod, "TOKEN_WHITELIST", ())),
                         ("{project-root}", "{output_dir}"))

    # trace: 任务书 §2.2（母本 §8 两值口径：单记录 → 顶层 project.status）
    def test_status_enum_is_master_two_values(self):
        mod = self.load_module()
        self.assertEqual(tuple(getattr(mod, "STATUS_ENUM", ())), ("草稿", "已定稿"))
        self.assertEqual(tuple(getattr(mod, "STAGE_ENUM", ())),
                         ("分诊", "对齐", "签核", "核心", "内容", "视觉", "收尾"))
        self.assertEqual(tuple(getattr(mod, "SIGNOFF_TYPE_ENUM", ())),
                         ("不签核", "对外合同", "服务协议", "内部审批"))


if __name__ == "__main__":
    unittest.main()
