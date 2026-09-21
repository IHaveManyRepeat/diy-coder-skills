# -*- coding: utf-8 -*-
"""diy-wds-scenarios 确定性引擎 e2e 测试（B7a 批 W3；任务书 §2.6 八类必备 + 本技能特有边界）。

覆盖（任务书 §2.6 ①–⑨）：
- ① 门禁：`init` 无 `--site-type` → exit 2（argparse 用法错误）；非法值 → ENUM_INVALID exit 1；
     空串 → EMPTY_FIELD exit 1；`--output-dir` 缺席 → exit 2；`--instance` 不存在（签名表不做）
- ② `init` 合法 exit 0 + 骨架（`project.status: 草稿` / `scope` / `page_inventory` / `scenarios`）
     且骨架即过 check
- ③ ID 铸号：`init` 铸 `SC-01`；会话按序追加 `SC-02`/`SC-03` → 放行；重复 ID → DUPLICATE_ID；
     跳号 / 重编 → SET_MISMATCH；重复 `init` 不覆盖已有记录
- ④ `list` 只回约定六字段（对照源摘要表：ID / 名称 / 人物 / 页数 / 优先级 / 状态）+ `--status` 过滤
- ⑤ `check` 各类违规检出（ENUM_INVALID / EMPTY_FIELD / STATUS_MISMATCH / TOKEN_UNRESOLVED /
     ASSUMPTION_PRESENT / MISSING_FILE / UNPARSABLE_YAML / UNKNOWN_ID）
- ⑥ 跨技能门禁（§2.3.1）：`wds-trigger.yaml` 缺失 / `project.status ≠ 已定稿` → 零产出停止
- ⑦ 回执键完整性（`instance` 键在位恒 null / `warnings` 与 `violations` 同形 / `where` 正斜杠）；
     只读子命令**不含** `updated`，`init` 含
- ⑧ SKILL.md 契约冒烟（母本 §1/§2/§3/§4/§5/§6 六节逐字 + 终门句指向本引擎 + 产物路径声明句
     + 四段 + ≤90 行 + steps 冻结名）
- ⑨ 本技能特有边界：`SC-<nn>` 与 `SC-<nn>.P<n>` 的**父子引用完整性**（前缀同源 / 页号连续 /
     `slug` 与 ID 同源）+ **页面覆盖矩阵机械判据**（每页恰属一条场景，重复/漏配即违规）

另含引擎内表核对（回报必答 ⑨ 的机械证据）：直接导入引擎模块，比对覆盖判据与键表常量。

夹具全部落 tempdir 自建；不读写本仓库真实 diy-output；不依赖本机 git 状态。
运行：cd diy-coder && python -m unittest discover -s tests -p "test_wds_scenarios.py" -v
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
SKILL_DIR = os.path.join(HERE, "..", "skills", "diy-wds-scenarios")
ENGINE = os.path.join(SKILL_DIR, "scripts", "wds_scenarios.py")
SKILL_MD = os.path.join(SKILL_DIR, "SKILL.md")
FINISH_STEP = os.path.join(SKILL_DIR, "steps", "06-finish.md")
NL = chr(10)

SCENARIOS_FILE = "wds-scenarios.yaml"
TRIGGER_FILE = "wds-trigger.yaml"

# §2.4：本技能 6 个步骤文件（冻结名）
STEP_FILES = ["01-context.md", "02-strategy.md", "03-plan.md",
              "04-outline.md", "05-overview.md", "06-finish.md"]

# 06-finish.md 的质检查表（4 维 25 项 + 五维并入 3+8+16+9，组 C 与维 1 去重不重复计）
CHECKLIST_TOTAL = 61
# 32 个源 `<gate>`（workflow.xml）抽取清单的标签（每类至少一行落位）
GATE_GROUP_LABELS = ("32 闸", "coverage-check", "quality-gates-pass",
                     "design-intent-saved", "append-only")

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

# 跨技能读契约（§2.3.1 冻结）：W3 从 wds-trigger.yaml 读的三组键
UPSTREAM_READ_KEYS = ("business_goals", "personas", "priority")


def run_engine(engine_path, args):
    return subprocess.run([sys.executable, engine_path] + args,
                          capture_output=True, text=True, encoding="utf-8")


def dump(node, indent=0):
    """极简 YAML 序列化（只覆盖本测试用到的形状；不依赖引擎实现）。"""
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
    # 纯词不加引号；日期类（`2026-09-18`）必须引号化——否则 PyYAML 会解成 date 对象
    if text and all(ch.isalnum() or ch in "-_" for ch in text) and not re.match(
            r"\d{4}-\d{2}-\d{2}", text):
        return text
    return '"%s"' % text.replace('"', '\\"')


def page(number, name, slug, exit_action="点击进入下一页", sid="SC-01"):
    node = {"id": "%s.P%d" % (sid, number), "slug": slug, "name": name,
            "purpose": "%s 的存在理由" % name, "entry_context": "上一页点进来"}
    if exit_action is not None:
        node["exit_action"] = exit_action
    return node


def scenario_yaml(sid="SC-01", name="Hasse 的紧急求助", persona="TG-1", priority=1,
                  status="已大纲", drivers=None, business_goal="BG-1",
                  design_intent="C", design_status="not-started",
                  pages=None, drop=None):
    """单条 `scenarios[]` 记录（各键可局部替换/删除）。"""
    number = sid.split("-")[1]
    pages = pages if pages is not None else [
        page(1, "首页", "%s.1-home" % number, "点「服务」进服务页", sid=sid),
        page(2, "服务页", "%s.2-services" % number, "点「联系」进联系页", sid=sid),
        page(3, "联系页", "%s.3-contact" % number, None, sid=sid),
    ]
    record = {
        "id": sid,
        "name": name,
        "priority": priority,
        "status": status,
        "trigger_map_context": {
            "target_group": persona,
            "drivers": drivers if drivers is not None else ["DF-1.1+", "DF-1.1-"],
            "business_goal": business_goal,
        },
        "design_intent": design_intent,
        "design_status": design_status,
        "transaction": "确认服务可用再下单",
        "situation": "房车坏了，带着家人在陌生小镇",
        "driving_forces": {"hope": "找到可信的修车点", "worry": "被不认识的人宰"},
        "device": "手机",
        "entry": "在加油站搜「修车 Öland」，点自然结果第一条",
        "success": {"user": "拿到位置与营业时间并放心打电话",
                    "business": "拦下一条高意向来电"},
        "pages": pages,
    }
    for key in drop or []:
        record.pop(key, None)
    return record


def product_yaml(status="已定稿", scenarios=None, inventory=None, scope=None,
                 revisions=None):
    """手搓完整产物（各段均可局部替换）——用于 check 面用例。"""
    scenarios = scenarios if scenarios is not None else [scenario_yaml()]
    inventory = inventory if inventory is not None else [
        {"name": "首页", "purpose": "一眼确认服务范围"},
        {"name": "服务页", "purpose": "看服务细节"},
        {"name": "联系页", "purpose": "找到电话与营业时间"},
    ]
    scope = scope if scope is not None else {
        "site_type": "presentation",
        "scale": "small",
        "scenario_format": "screen-flow",
        "page_strategy": {"individual": ["首页", "服务页", "联系页"], "templated": []},
    }
    body = {
        "project": {"name": "mini", "created": "2026-09-18", "updated": "2026-09-21",
                    "status": status},
        "scope": scope,
        "page_inventory": inventory,
        "scenarios": scenarios,
        "revisions": [] if revisions is None else revisions,
    }
    return dump(body)


def trigger_yaml(status="已定稿", personas=None):
    """上游 `wds-trigger.yaml` 夹具（只含本技能读的三组键）。"""
    personas = personas if personas is not None else [
        {"id": "TG-1", "name": "Hasse", "priority": "Primary",
         "driving_forces": {"positive": [{"id": "DF-1.1+", "text": "今天就修好"}],
                            "negative": [{"id": "DF-1.1-", "text": "被宰"}]}},
    ]
    return dump({"project": {"name": "mini", "created": "2026-09-18",
                             "updated": "2026-09-21", "status": status},
                 "business_goals": [{"id": "BG-1", "text": "少接问询电话"}],
                 "personas": personas,
                 "priority": {"primary": ["TG-1"]},
                 "revisions": []})


class EngineCase(unittest.TestCase):
    """tmp 项目根 + diy-output 目录的公共夹具。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="wdsscen-")
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
        return self.write("diy-output/" + SCENARIOS_FILE, content)

    def upstream(self, content=None, status="已定稿"):
        return self.write("diy-output/" + TRIGGER_FILE,
                          trigger_yaml(status=status) if content is None else content)

    def engine(self, *args):
        return run_engine(self.engine_path,
                          list(args) + ["--project-root", self.root,
                                        "--output-dir", self.out, "--json"])

    def raw(self, *args):
        return run_engine(self.engine_path, list(args))

    def init(self, *extra):
        if "--site-type" not in extra:
            extra = ("--site-type", "presentation") + tuple(extra)
        return self.engine("init", *extra)

    def check(self, *extra):
        return self.engine("check", *extra)

    def results(self, proc):
        return json.loads(proc.stdout)

    def codes(self, proc):
        return {x["code"] for x in self.results(proc)["violations"]}

    def places(self, proc):
        return [x["where"] for x in self.results(proc)["violations"]]


class GateTests(EngineCase):
    """§2.6 ① 门禁（用法错误 exit 2 ≠ 枚举违规 exit 1 ≠ 空值 EMPTY_FIELD）。"""

    # trace: 任务书 §2.6 ①（init 无 --site-type → exit 2）
    def test_gate_missing_site_type_is_usage_error(self):
        r = self.raw("init", "--project-root", self.root,
                     "--output-dir", self.out, "--json")
        self.assertEqual(r.returncode, 2, "缺 --site-type 须为 argparse 用法错误 exit 2：%s"
                         % (r.stdout + r.stderr))

    # trace: 任务书 §2.6 ①（非法值 → ENUM_INVALID exit 1）
    def test_gate_invalid_site_type_is_enum_invalid(self):
        self.upstream()
        r = self.init("--site-type", "brochure")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertEqual(self.codes(r), {"ENUM_INVALID"})
        self.assertFalse(os.path.exists(os.path.join(self.out, SCENARIOS_FILE)),
                         "门禁拒绝须零产出")

    # trace: 任务书 §2.6 ①（空值 → EMPTY_FIELD 零产出）
    def test_gate_blank_site_type_is_empty_field(self):
        self.upstream()
        r = self.init("--site-type", "   ")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertEqual(self.codes(r), {"EMPTY_FIELD"})
        self.assertFalse(os.path.exists(os.path.join(self.out, SCENARIOS_FILE)))

    # trace: 任务书 §2.2（--output-dir 必填于写盘子命令；--instance 一律不做）
    def test_gate_output_dir_mandatory_and_no_instance_flag(self):
        self.upstream()
        r = self.raw("init", "--site-type", "presentation",
                     "--project-root", self.root, "--json")
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        r2 = self.engine("list", "--instance", "demo")
        self.assertEqual(r2.returncode, 2, "--instance 不得进签名表：%s" % (r2.stdout + r2.stderr))


class CrossSkillGateTests(EngineCase):
    """§2.6 ⑥ 跨技能门禁（§2.3.1）：门禁 = 读 `wds-trigger.yaml` 且 `project.status: 已定稿`。"""

    # trace: 任务书 §2.3.1 + §8 验收 #3（上游缺失 → 零产出停止 + 路由）
    def test_missing_upstream_is_zero_output_stop(self):
        r = self.init()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertEqual(self.codes(r), {"MISSING_FILE"})
        data = self.results(r)
        self.assertIn("diy-wds-trigger", json.dumps(data, ensure_ascii=False),
                      "缺上游须给出路由目标")
        self.assertFalse(os.path.exists(os.path.join(self.out, SCENARIOS_FILE)),
                         "零产出停止不得写盘")

    # trace: 任务书 §2.3.1（上游存在但未定稿 → 拒不铸骨架）
    def test_draft_upstream_is_refused(self):
        self.upstream(status="草稿")
        r = self.init()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertEqual(self.codes(r), {"STATUS_MISMATCH"})
        self.assertFalse(os.path.exists(os.path.join(self.out, SCENARIOS_FILE)))

    # trace: 任务书 §2.2 红线（终门走自带引擎；全库零 `check --type <WDS 型> --previous`）
    def test_no_wds_type_previous_check_taught(self):
        targets = ["SKILL.md"] + ["steps/" + name for name in STEP_FILES]
        for rel in targets:
            path = os.path.join(SKILL_DIR, rel)
            if not os.path.isfile(path):
                continue
            with io.open(path, encoding="utf-8") as handle:
                text = handle.read()
            self.assertIsNone(PREVIOUS_CHECK_RE.search(text),
                              "%s 教了 `check --type <型> --previous`（diyc 8 型封闭集）" % rel)
            for wds_type in ("wds-brief", "wds-trigger", "wds-scenarios"):
                self.assertNotIn("--type %s" % wds_type, text,
                                 "%s 把 WDS 型当成了 diyc 的类型" % rel)


class InitTests(EngineCase):
    """§2.6 ②③ init 骨架、ID 铸号、不覆盖既有记录。"""

    # trace: 任务书 §2.6 ②（exit 0 + 骨架结构，含 project.status: 草稿 与首条记录铸号）
    def test_init_creates_skeleton_passing_check(self):
        self.upstream()
        r = self.init("--scale", "small", "--scenario-format", "screen-flow")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = self.results(r)
        self.assertIsNone(data["instance"])
        self.assertIn("updated", data)
        text = self.read_text("diy-output/" + SCENARIOS_FILE)
        self.assertIn("status: 草稿", text)
        self.assertIn("site_type: presentation", text)
        self.assertIn("page_inventory:", text)
        self.assertIn("scenarios:", text)
        self.assertIn("id: SC-01", text, "init 须铸首条记录的 ID（顺序性证据）")
        self.assertIn("revisions: []", text)
        c = self.check()
        self.assertEqual(c.returncode, 0, c.stdout + c.stderr)
        self.assertEqual(self.results(c)["counts"]["records"], 1)

    # trace: 任务书 §2.6 ③（重复 init 不覆盖；已有记录与骨架一字不动）
    def test_reinit_does_not_overwrite_existing_record(self):
        self.upstream()
        self.assertEqual(self.init().returncode, 0)
        doc = self.read_text("diy-output/" + SCENARIOS_FILE)
        for form in ("name: ''", 'name: ""'):     # 骨架须给首条记录留 name 空位
            if form in doc:
                doc = doc.replace(form, "name: 用户写的场景名", 1)
                break
        else:
            self.fail("骨架里没有可填的 name 空位：%s" % doc)
        self.product(doc)
        before = self.read_text("diy-output/" + SCENARIOS_FILE)
        same = self.init()
        self.assertEqual(same.returncode, 0, same.stdout + same.stderr)
        self.assertTrue(self.results(same)["warnings"], "同值重跑须给一行「未覆盖」warning")
        after = self.read_text("diy-output/" + SCENARIOS_FILE)
        self.assertIn("用户写的场景名", after, "重复 init 不得覆盖已有记录")
        self.assertEqual([ln for ln in after.split(NL) if not ln.startswith("  updated:")],
                         [ln for ln in before.split(NL) if not ln.startswith("  updated:")],
                         "除 project.updated 外不得改动任何一行")

    # trace: 任务书 §2.6 ③（损坏产物拒绝且零写入）
    def test_init_refuses_damaged_product_with_zero_write(self):
        self.upstream()
        self.product("project: [" + NL)
        before = self.read_text("diy-output/" + SCENARIOS_FILE)
        bad = self.init()
        self.assertEqual(bad.returncode, 1, bad.stdout)
        self.assertNotIn("Traceback", bad.stderr)
        self.assertEqual(self.codes(bad), {"UNPARSABLE_YAML"})
        self.assertEqual(self.read_text("diy-output/" + SCENARIOS_FILE), before,
                         "拒绝路径不得改动产物一个字节")


class IdChainTests(EngineCase):
    """§2.6 ③⑨ ID 铸号、唯一性、父子引用完整性。"""

    # trace: 任务书 §2.6 ③（SC-<nn> 顺序递增、不重编不复用）
    def test_scenario_ids_sequential_and_unique(self):
        self.upstream()
        self.assertEqual(self.init().returncode, 0)
        second = scenario_yaml("SC-02", name="Hasse 的第二次到访", priority=2,
                               pages=[page(1, "新闻列表", "02.1-news", None, sid="SC-02")])
        third = scenario_yaml("SC-03", name="Hasse 的电话核实", priority=3,
                              pages=[page(1, "关于页", "03.1-about", None, sid="SC-03")])
        inventory = [{"name": "首页", "purpose": "确认服务范围"},
                     {"name": "服务页", "purpose": "看服务细节"},
                     {"name": "联系页", "purpose": "找到电话"},
                     {"name": "新闻列表", "purpose": "看动态"},
                     {"name": "关于页", "purpose": "看故事"}]
        self.product(product_yaml(scenarios=[scenario_yaml(), second, third],
                                  inventory=inventory))
        self.assertEqual(self.check().returncode, 0, self.read_text("diy-output/" + SCENARIOS_FILE))
        # 重复 ID → DUPLICATE_ID
        self.product(product_yaml(scenarios=[scenario_yaml("SC-01"),
                                             scenario_yaml("SC-01")]))
        dup = self.check()
        self.assertEqual(dup.returncode, 1, dup.stdout)
        self.assertIn("DUPLICATE_ID", self.codes(dup))
        # 跳号（SC-01 之后直接 SC-03）→ SET_MISMATCH
        self.product(product_yaml(scenarios=[scenario_yaml("SC-01"), third]))
        gap = self.check()
        self.assertEqual(gap.returncode, 1, gap.stdout)
        self.assertIn("SET_MISMATCH", self.codes(gap))
        # 越出 SC-<nn> 两位形态 → ENUM_INVALID
        self.product(product_yaml(scenarios=[scenario_yaml("SC-1")]))
        shape = self.check()
        self.assertEqual(shape.returncode, 1, shape.stdout)
        self.assertIn("ENUM_INVALID", self.codes(shape))

    # trace: 任务书 §2.6 ⑨（页面 ID 前缀须与其场景同源）
    def test_page_id_prefix_must_match_own_scenario(self):
        self.upstream()
        record = scenario_yaml("SC-02", name="Hasse 的第二次到访")
        # 故意让页面 ID 留 SC-01 前缀（sid 默认 SC-01）——父子引用必须同源
        record["pages"] = [page(1, "首页", "02.1-home", "点「服务」进服务页"),
                           page(2, "联系页", "02.2-contact", None)]
        self.product(product_yaml(scenarios=[scenario_yaml("SC-01"), record],
                                  inventory=[{"name": "首页", "purpose": "有"},
                                             {"name": "服务页", "purpose": "有"},
                                             {"name": "联系页", "purpose": "有"}]))
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        places = [x for x in self.places(r) if "pages" in x]
        self.assertTrue(places, self.places(r))
        self.assertIn("SET_MISMATCH", self.codes(r))

    # trace: 任务书 §2.6 ⑨（场景内页号须连续；缺号/重复即违规）
    def test_page_numbers_contiguous_within_scenario(self):
        self.upstream()
        pages = [page(1, "首页", "01.1-home", "点「服务」进服务页"),
                 page(3, "联系页", "01.3-contact", None)]
        self.product(product_yaml(scenarios=[scenario_yaml(pages=pages)]))
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("SET_MISMATCH", self.codes(r))

    # trace: 任务书 §0.2 裁定 8（slug 是展示名，须与 ID 同源）
    def test_page_slug_must_track_id(self):
        self.upstream()
        pages = [page(1, "首页", "01.1-home", "点「服务」进服务页"),
                 page(2, "联系页", "01.9-contact", None)]
        self.product(product_yaml(scenarios=[scenario_yaml(pages=pages)]))
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertTrue(any("slug" in x for x in self.places(r)), self.places(r))

    # trace: 任务书 §2.6 ③（重复页 ID → DUPLICATE_ID）
    def test_duplicate_page_id_detected(self):
        self.upstream()
        pages = [page(1, "首页", "01.1-home", "点「服务」进服务页"),
                 page(2, "联系页", "01.2-contact", None)]
        pages[1]["id"] = "SC-01.P1"
        self.product(product_yaml(scenarios=[scenario_yaml(pages=pages)]))
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("DUPLICATE_ID", self.codes(r))


class CoverageTests(EngineCase):
    """§2.6 ⑨ 页面覆盖矩阵机械判据（三条骨律之一：每页恰属一条战略链）。"""

    # trace: 任务书 §5 W3 卡 ⑨（覆盖矩阵：每页恰属一条场景）
    def test_coverage_matrix_full_and_clean(self):
        self.upstream()
        self.product(product_yaml())
        r = self.check()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        cov = self.results(r)["coverage"]
        self.assertEqual(cov["total"], 3)
        self.assertEqual(cov["covered"], 3)
        self.assertEqual(cov["rate"], "3/3")
        self.assertEqual(len(cov["matrix"]), 3)
        for row in cov["matrix"]:
            self.assertEqual(row["scenario"], "SC-01")

    # trace: 任务书 §5 W3 卡 ⑨（漏配 → 违规；覆盖率不足 → --final 不放行）
    def test_unassigned_page_is_violation(self):
        self.upstream()
        inventory = [{"name": "首页", "purpose": "一眼确认服务范围"},
                     {"name": "服务页", "purpose": "看服务细节"},
                     {"name": "联系页", "purpose": "找到电话与营业时间"},
                     {"name": "关于页", "purpose": "看故事"}]
        self.product(product_yaml(inventory=inventory))
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertEqual(self.results(r)["coverage"]["rate"], "3/4")
        places = self.places(r)
        self.assertTrue(any("关于页" in x for x in places), places)

    # trace: 任务书 §5 W3 卡 ⑨（重复分配 → 违规：一页不得属两条链）
    def test_repeated_page_across_scenarios_is_violation(self):
        self.upstream()
        # 第二场景**只**复用了首页（ID 前缀与页号都对，唯一问题就是重复分配）
        second = scenario_yaml("SC-02", name="Hasse 的第二次到访", priority=2,
                               pages=[page(1, "首页", "02.1-home", None, sid="SC-02")])
        first = scenario_yaml(pages=[page(1, "首页", "01.1-home", "点「服务」进服务页"),
                                     page(2, "服务页", "01.2-services", "点「联系」进联系页"),
                                     page(3, "联系页", "01.3-contact", None)])
        self.product(product_yaml(scenarios=[first, second]))
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertTrue(any("首页" in x for x in self.places(r)), self.places(r))

    # trace: 任务书 §5 W3 卡 ⑨（场景里出现清单外的页 → UNKNOWN_ID）
    def test_page_outside_inventory_is_unknown_id(self):
        self.upstream()
        pages = [page(1, "首页", "01.1-home", "点「服务」进服务页"),
                 page(2, "服务页", "01.2-services", "点「联系」进联系页"),
                 page(3, "联系页", "01.3-contact", None)]
        pages[2]["name"] = "价目页"
        inventory = [{"name": "首页", "purpose": "有"},
                     {"name": "服务页", "purpose": "有"},
                     {"name": "联系页", "purpose": "有"}]
        self.product(product_yaml(scenarios=[scenario_yaml(pages=pages)], inventory=inventory))
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("UNKNOWN_ID", self.codes(r))

    # trace: 任务书 §0.2 裁定 8 / 骨律（场景名必须含人物名；上游可解析时机械核）
    def test_scenario_name_must_contain_persona_name(self):
        self.upstream()
        self.product(product_yaml(scenarios=[scenario_yaml(name="紧急求助流程")]))
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertTrue(any("name" in x for x in self.places(r)), self.places(r))
        # 上游缺席时不猜：降级为 warning，不判违规
        os.remove(os.path.join(self.out, TRIGGER_FILE))
        ok = self.check()
        self.assertEqual(ok.returncode, 0, ok.stdout + ok.stderr)
        self.assertTrue(self.results(ok)["warnings"])


class ListShowTests(EngineCase):
    """§2.6 ④ list / show。"""

    # trace: 任务书 §2.6 ④（只回约定六字段 + --status 过滤生效）
    def test_list_returns_contract_fields_and_filters(self):
        self.upstream()
        self.product(product_yaml())
        r = self.engine("list")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = self.results(r)
        self.assertEqual(len(data["records"]), 1)
        self.assertEqual(sorted(data["records"][0]),
                         ["id", "name", "pages", "persona", "priority", "status"])
        self.assertEqual(data["records"][0]["pages"], 3)
        self.assertEqual(data["records"][0]["persona"], "TG-1")
        keep = self.engine("list", "--status", "已大纲")
        self.assertEqual(len(self.results(keep)["records"]), 1)
        none = self.engine("list", "--status", "草稿")
        self.assertEqual(self.results(none)["records"], [])
        bad = self.engine("list", "--status", "已定稿")
        self.assertEqual(bad.returncode, 1, bad.stdout)
        self.assertEqual(self.codes(bad), {"ENUM_INVALID"})
        # 产物缺席：按空列表处理，不报错
        os.remove(os.path.join(self.out, SCENARIOS_FILE))
        empty = self.engine("list")
        self.assertEqual(empty.returncode, 0, empty.stdout + empty.stderr)
        self.assertEqual(self.results(empty)["records"], [])

    # trace: 任务书 §2.2（show --id 取 SC-<nn>；不存在 → UNKNOWN_ID）
    def test_show_by_id_and_unknown_id(self):
        self.upstream()
        self.product(product_yaml(scenarios=[scenario_yaml("SC-01"),
                                             scenario_yaml("SC-02", name="Hasse 的第二次到访")]))
        one = self.engine("show", "--id", "SC-01")
        self.assertEqual(one.returncode, 0, one.stdout + one.stderr)
        self.assertEqual(self.results(one)["document"]["id"], "SC-01")
        page = self.engine("show", "--id", "SC-01.P2")
        self.assertEqual(page.returncode, 0, page.stdout + page.stderr)
        self.assertEqual(self.results(page)["document"]["id"], "SC-01.P2")
        miss = self.engine("show", "--id", "SC-09")
        self.assertEqual(miss.returncode, 1, miss.stdout)
        self.assertEqual(self.codes(miss), {"UNKNOWN_ID"})
        # 无 --id → 整份全文 + 覆盖矩阵
        doc = self.engine("show")
        self.assertEqual(doc.returncode, 0, doc.stdout + doc.stderr)
        body = self.results(doc)
        self.assertIn("scenarios", body["document"])
        self.assertEqual(body["coverage"]["total"], 3)

    # trace: 任务书 §2.6 ④（产物缺席 → MISSING_FILE）
    def test_show_missing_product(self):
        miss = self.engine("show")
        self.assertEqual(miss.returncode, 1, miss.stdout)
        self.assertEqual(self.codes(miss), {"MISSING_FILE"})


class CheckTests(EngineCase):
    """§2.6 ⑤ check 的四类检出 + 定稿义务。"""

    # trace: 任务书 §2.6 ⑤（枚举越界 → ENUM_INVALID）
    def test_check_detects_enum_invalid(self):
        self.upstream()
        self.product(product_yaml())
        self.assertEqual(self.check("--final").returncode, 0)
        self.product(product_yaml(status="定稿"))
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ENUM_INVALID", self.codes(r))

    # trace: 任务书 §2.6 ⑤（必填键缺失 → EMPTY_FIELD，where 点名键名）
    def test_check_detects_missing_required_key_with_name(self):
        self.upstream()
        self.product(product_yaml(scenarios=[scenario_yaml(drop=["design_intent"])]))
        r = self.check("--final")
        self.assertEqual(r.returncode, 1, r.stdout)
        places = [x["where"] for x in self.results(r)["violations"]
                  if x["code"] == "EMPTY_FIELD"]
        self.assertTrue(any(x.endswith("scenarios[0].design_intent") for x in places), places)

    # trace: 任务书 §0.2 裁定 17（三条交接契约键必携）
    def test_handover_contract_keys_required(self):
        self.upstream()
        self.product(product_yaml(scenarios=[scenario_yaml(drop=["trigger_map_context"])]))
        r = self.check("--final")
        self.assertEqual(r.returncode, 1, r.stdout)
        places = self.places(r)
        self.assertTrue(any("trigger_map_context" in x for x in places), places)
        # design_status 初值必须是 not-started（本技能只设初值，推进归 C·3 的 diy-design）
        self.product(product_yaml(scenarios=[scenario_yaml(design_status="built")]))
        bad = self.check("--final")
        self.assertEqual(bad.returncode, 1, bad.stdout)
        self.assertIn("STATUS_MISMATCH", self.codes(bad))

    # trace: 任务书 §2.6 ⑤（记录级 status 与 --final 同档；skip 不放行未大纲记录）
    def test_final_requires_all_records_outlined(self):
        self.upstream()
        self.product(product_yaml(scenarios=[scenario_yaml(status="草稿")]))
        r = self.check("--final")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("STATUS_MISMATCH", self.codes(r))

    # trace: 任务书 §2.6 ⑤ / §10 项 7（未解析令牌 → TOKEN_UNRESOLVED）
    def test_check_detects_unresolved_token(self):
        self.upstream()
        record = scenario_yaml()
        record["transaction"] = "按 {skill-name} 生成"
        self.product(product_yaml(scenarios=[record]))
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("TOKEN_UNRESOLVED", self.codes(r))
        record["transaction"] = "看 {output_dir} 与 {project-root}"
        self.product(product_yaml(scenarios=[record]))
        self.assertEqual(self.check().returncode, 0, self.read_text("diy-output/" + SCENARIOS_FILE))

    # trace: 任务书 §2.6 ⑤（--final 零 [假设]）
    def test_final_rejects_assumption_mark(self):
        self.upstream()
        record = scenario_yaml()
        record["situation"] = "[假设] 用户在陌生小镇"
        self.product(product_yaml(scenarios=[record]))
        r = self.check("--final")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ASSUMPTION_PRESENT", self.codes(r))

    # trace: 任务书 §2.6 ⑤（产物缺席 → MISSING_FILE；损坏 → UNPARSABLE_YAML；--final 要求已定稿）
    def test_check_missing_damaged_and_draft(self):
        self.upstream()
        miss = self.check()
        self.assertEqual(miss.returncode, 1, miss.stdout)
        self.assertEqual(self.codes(miss), {"MISSING_FILE"})
        self.product("scope: [" + NL)
        bad = self.check()
        self.assertEqual(bad.returncode, 1, bad.stdout)
        self.assertEqual(self.codes(bad), {"UNPARSABLE_YAML"})
        self.product(product_yaml(status="草稿"))
        draft = self.check("--final")
        self.assertEqual(draft.returncode, 1, draft.stdout)
        self.assertIn("STATUS_MISMATCH", self.codes(draft))

    # trace: 任务书 §5 W3 卡（驱动因素跨群引用 → 违规：所消费驱动须属本记录人物）
    def test_drivers_must_belong_to_own_target_group(self):
        self.upstream()
        # W2 的驱动因素 ID 形态 = `DF-<人物号>.<条号>+|-`（`wds-trigger/SKILL.md` 结构段）
        self.product(product_yaml(scenarios=[
            scenario_yaml(drivers=["DF-1.1+", "DF-2.1-"])]))
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertTrue(any("drivers" in x for x in self.places(r)), self.places(r))
        # 同群引用 → 放行
        self.product(product_yaml(scenarios=[scenario_yaml(drivers=["DF-1.1+", "DF-1.2-"])]))
        self.assertEqual(self.check().returncode, 0)


class ReceiptTests(EngineCase):
    """§2.6 ⑦ 回执 schema。"""

    # trace: 任务书 §2.2（公共键 + instance 恒 null + warnings 同形 + 单行 JSON）
    def test_receipt_keys_and_json_single_line(self):
        self.upstream()
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
        init = self.results(self.init())
        self.assertIn("updated", init, "init 写盘回执须含 updated")
        bad = self.init("--site-type", "")
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

    # trace: 任务书 §2.2（counts 口径：记录数 + 覆盖计数）
    def test_counts_shape(self):
        self.upstream()
        self.product(product_yaml())
        data = self.results(self.check())
        self.assertEqual(data["counts"]["records"], 1)
        self.assertEqual(data["counts"]["inventory"], 3)
        self.assertEqual(data["counts"]["assigned"], 3)


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
        self.assertIn("wds_scenarios.py", raw, "终门句未指向本技能领域引擎")
        self.assertIn("check --final", raw, "终门句缺 check --final")
        self.assertIn("wds-scenarios.yaml", raw, "产物路径声明句不在场")
        self.assertIn("diy-wds-scenarios", raw)
        self.assertIn("wds-trigger.yaml", raw, "上游门禁句不在场（§2.3.1）")
        self.assertIsNone(PREVIOUS_CHECK_RE.search(raw),
                          "红线：不得教 diyc.py 会拒的 `check --type <型> --previous`")
        lines = raw.replace(NL + chr(13), NL).replace(chr(13) + NL, NL).rstrip(NL).split(NL)
        self.assertLessEqual(len(lines), 90, "SKILL.md 超 90 行（薄主文件硬阈值）")

    # trace: 任务书 §2.4（6 个步骤文件冻结名 + 一行指路一致）
    def test_step_files_frozen_names(self):
        names = sorted(n for n in os.listdir(os.path.join(SKILL_DIR, "steps"))
                       if n.endswith(".md"))
        self.assertEqual(names, STEP_FILES)
        raw = self.read_skill()
        for name in names:
            self.assertIn(name, raw, "SKILL.md 工作流段缺 %s 的一行指路" % name)

    # trace: 任务书 §2.4（每文件的小节用 `## 第 N 步 —— ` 二级标题承载）
    def test_step_sections_use_frozen_heading(self):
        total = 0
        for name in STEP_FILES:
            path = os.path.join(SKILL_DIR, "steps", name)
            if not os.path.isfile(path):
                self.skipTest("steps/ 尚未交付")
            with io.open(path, encoding="utf-8") as handle:
                text = handle.read()
            count = len(re.findall(r"^## 第 \d+ 步 —— ", text, re.M))
            self.assertGreater(count, 0, "%s 无 `## 第 N 步 —— ` 小节" % name)
            total += count
        self.assertEqual(total, 16, "六文件小节合计须为 16（回报的映射表口径）")


class FinishChecklistTests(unittest.TestCase):
    """§2.6 ⑨ + 裁定 15：06-finish.md 的质检查表与 32 闸清单在场。"""

    def read_finish(self):
        if not os.path.isfile(FINISH_STEP):
            self.skipTest("steps/06-finish.md 尚未交付——质检查表待补")
        with io.open(FINISH_STEP, encoding="utf-8") as handle:
            return handle.read()

    # trace: 任务书 §0.2 裁定 15（校验维度并入 finish 质检查表，条数机械可核）
    def test_checklist_item_count(self):
        raw = self.read_finish()
        items = [ln for ln in raw.replace(chr(13) + NL, NL).split(NL)
                 if ln.strip().startswith("- [ ]")]
        self.assertEqual(len(items), CHECKLIST_TOTAL,
                         "06-finish.md 的 `- [ ]` 须恰 %d 项，实为 %d"
                         % (CHECKLIST_TOTAL, len(items)))

    # trace: 任务书 §0.2 裁定 15（源 steps-v 五维全部在场）
    def test_five_validation_dimensions_present(self):
        raw = self.read_finish()
        for label in ("场景覆盖", "导航模式", "大纲完整", "跨场景一致", "SEO 关键词对齐"):
            self.assertIn(label, raw, "缺校验维度 %s" % label)

    # trace: 任务书 §5 W3 卡（32 个 `<gate>` 的抽取清单落 finish）
    def test_thirty_two_gates_extracted(self):
        raw = self.read_finish()
        for label in GATE_GROUP_LABELS:
            self.assertIn(label, raw, "32 闸抽取清单缺 %s" % label)

    # trace: 任务书 §0.2 裁定 6（避坑维度取 checklist 权威版 7 项）
    def test_mistake_dimension_is_seven(self):
        raw = self.read_finish()
        self.assertIn("7/7", raw, "避坑维度阈值须取 checklist 权威版 7 项")


class InternalTableTests(unittest.TestCase):
    """引擎内表核对（回报必答 ⑨ 的机械证据；直接导入引擎模块）。"""

    def load_module(self):
        if not os.path.isfile(ENGINE):
            self.skipTest("wds_scenarios.py 尚未交付")
        spec = importlib.util.spec_from_file_location("wds_scenarios_under_test", ENGINE)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    # trace: 任务书 §2.2（母本 §8 两值口径：单记录顶层 status；记录级两值）
    def test_status_enums(self):
        mod = self.load_module()
        self.assertEqual(tuple(getattr(mod, "STATUS_ENUM", ())), ("草稿", "已定稿"))
        self.assertEqual(tuple(getattr(mod, "RECORD_STATUS_ENUM", ())), ("草稿", "已大纲"))
        self.assertEqual(tuple(getattr(mod, "SITE_TYPE_ENUM", ())),
                         ("presentation", "dynamic", "mixed"))
        self.assertEqual(tuple(getattr(mod, "SCALE_ENUM", ())), ("small", "medium", "large"))
        self.assertEqual(tuple(getattr(mod, "SCENARIO_FORMAT_ENUM", ())),
                         ("screen-flow", "storyboard", "mixed"))

    # trace: 任务书 §0.2 裁定 17（design_intent 五值 + design_status 初值）
    def test_handover_contract_enums(self):
        mod = self.load_module()
        self.assertEqual(tuple(getattr(mod, "DESIGN_INTENT_ENUM", ())),
                         ("K", "C", "S", "D", "L"))
        self.assertEqual(str(getattr(mod, "DESIGN_STATUS_INITIAL", "")), "not-started")
        self.assertIn("not-started", tuple(getattr(mod, "DESIGN_STATUS_ENUM", ())))

    # trace: 任务书 §2.3.1（跨技能读契约：上游文件与键名冻结）
    def test_upstream_contract_keys(self):
        mod = self.load_module()
        self.assertEqual(str(getattr(mod, "TRIGGER_FILE", "")), TRIGGER_FILE)
        self.assertEqual(tuple(getattr(mod, "UPSTREAM_KEYS", ())), UPSTREAM_READ_KEYS)
        self.assertEqual(tuple(getattr(mod, "TOKEN_WHITELIST", ())),
                         ("{project-root}", "{output_dir}"))
        self.assertEqual(str(getattr(mod, "FINAL_UPSTREAM_STATUS", "")), "已定稿")


if __name__ == "__main__":
    unittest.main()
