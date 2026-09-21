# -*- coding: utf-8 -*-
"""diy-wds-trigger 确定性引擎 e2e 测试（B7a 批 W2；任务书 §2.6 八类必备 + 本技能特有边界）。

覆盖（任务书 §2.6 ①–⑨）：
- ① 门禁：`init` 无 `--mode` → exit 2（argparse 用法错误）；非法值 → ENUM_INVALID exit 1；
     空串 → EMPTY_FIELD exit 1；`--output-dir` 缺席 → exit 2；`--instance` 不在签名表
- ② `init` 合法 exit 0 + 骨架结构（`project.status: 草稿` / `stage: 模式` / 首条记录 `BG-1`）
- ③ ID 铸号：`BG-<n>` 由 `init` 铸首条、`TG-<n>` / `DF-<n>.<m>±` 靠 `check` 查唯一性
     （`DUPLICATE_ID`）与引用可解析（`UNKNOWN_ID`）
- ④ `list` 只回七字段、`--status` 过滤生效；`show` 整份全文 / `--id TG-<n>` 单条
- ⑤ `check` 各类违规检出：ENUM_INVALID / EMPTY_FIELD / STATUS_MISMATCH / SET_MISMATCH /
     DUPLICATE_ID / UNKNOWN_ID / TOKEN_UNRESOLVED / ASSUMPTION_PRESENT
- ⑥ **跨技能门禁（§2.3.1 冻结）**：读 `{output_dir}/wds-brief.yaml` 且 `project.status: 已定稿`；
     缺失 → MISSING_FILE 零产出；非定稿 → STATUS_MISMATCH 零产出
- ⑦ 回执键完整性（`instance` 键在位恒 null / `warnings` 与 `violations` 同形 / `where` 正斜杠）；
     只读子命令**不含** `updated`，`init` 含
- ⑧ SKILL.md 契约冒烟（母本 §1/§2/§3/§4/§5/§6 六节逐字 + 终门句指向本引擎 + 产物路径声明句
     + frontmatter 六字段取源实值）
- ⑨ 本技能特有边界：**`metrics` 的四条越界情形**（每人 3–5 正 / 3–5 负 / 2–4 群 /
     连接数 = 目标数 + 2×人物数）——越界一律 **warning 不阻断**（源侧「展示端自适应」口径）

另含引擎内表核对（回报必答 ③⑧⑩ 的机械证据）：直接导入引擎模块，比对常量与 Effect Map 四类样式。

夹具全部落 tempdir 自建；不读写本仓库真实 diy-output；不依赖本机 git 状态。
运行：cd diy-coder && python -m unittest discover -s tests -p "test_wds_trigger.py" -v
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
SKILL_DIR = os.path.join(HERE, "..", "skills", "diy-wds-trigger")
ENGINE = os.path.join(SKILL_DIR, "scripts", "wds_trigger.py")
SKILL_MD = os.path.join(SKILL_DIR, "SKILL.md")
FINISH_STEP = os.path.join(SKILL_DIR, "steps", "06-finish.md")
TEMPLATE = os.path.join(SKILL_DIR, "templates", "trigger-map.template.md")
NL = chr(10)

PRODUCT_FILE = "wds-trigger.yaml"
UPSTREAM_FILE = "wds-brief.yaml"

# ------------------------------------------------------------------ 独立内表（非实现拷贝）
# 源侧取数位置（裁定 6 / 08a–08h / templates/trigger-map.template.md）：
DRIVER_RANGE = (3, 5)          # `step-04-driving-forces.md:104,116`（采集端 3–5/类）
PERSONA_RANGE = (2, 4)         # `step-03-target-groups.md:39`（收窄到 2–4）
GOAL_RANGE = (3, 5)            # `step-02-business-goals.md`（3-5 SMART objectives）
CLASS_DEFS = (
    "classDef businessGoal fill:#f3f4f6,color:#1f2937,stroke:#d1d5db,stroke-width:2px",
    "classDef platform fill:#e5e7eb,color:#111827,stroke:#9ca3af,stroke-width:3px",
    "classDef targetGroup fill:#f9fafb,color:#1f2937,stroke:#d1d5db,stroke-width:2px",
    "classDef drivingForces fill:#f3f4f6,color:#1f2937,stroke:#d1d5db,stroke-width:2px",
)
# 源 `08g:63-66`；驱动因素 emoji 规则见 `08e:76-87`（WANTS/FEARS 标题不带 emoji）
DRIVER_EMOJI = ("✅", "❌")

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

# frontmatter 六字段取源实值（裁定 4；证据 = research/_req_check.txt 第 4 行）
FRONTMATTER = (("phase", "1-wds-strategy"), ("precededBy", '[diy-wds-brief]'),
               ("followedBy", "[]"), ("required", "true"), ("line", "wds"),
               ("outputs", "wds-trigger.yaml"))

# 质检承载位（§2.4 / 裁定 15）：13 维去重后的分组 + 源 steps-v 五维
FINISH_GROUPS = ("成品与图", "跨段一致与语言", "人物与驱动因素", "业务目标与特征影响", "链式校验")
VALIDATE_DIMS = ("目标群覆盖", "优先级一致性", "人物一致性", "特征影响对齐", "跨段连贯")
# 去重后实测的 `- [ ]` 项数（源 104 项经 13 维去重；详见 steps/06-finish.md）
FINISH_ITEMS = 48


def run_engine(engine_path, args):
    return subprocess.run([sys.executable, engine_path] + args,
                          capture_output=True, text=True, encoding="utf-8")


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
    # 纯词不加引号；但日期类（`2026-09-21`）必须引号化——否则 PyYAML 会解成 date 对象
    if text and all(ch.isalnum() or ch in "-_./+%" for ch in text) and not re.match(
            r"\d{4}-\d{2}-\d{2}", text):
        return text
    return '"%s"' % text.replace('"', '\\"')


def upstream_yaml(status="已定稿"):
    """上游 `wds-brief.yaml` 最小形状（§2.3.1：门禁只读 `project.status`）。"""
    return dump({"project": {"name": "mini", "created": "2026-09-18",
                             "updated": "2026-09-21", "status": status},
                 "revisions": []}) + NL


def driver(prefix, index, direction, promise_key):
    ident = "DF-%d.%d%s" % (prefix, index, direction)
    record = {"id": ident, "statement": "驱动 %s" % ident, "why": "因为 %s" % ident}
    record[promise_key] = "承诺 %s" % ident
    return record


def persona(index, priority="其他", positives=3, negatives=3, name=None,
            transformation=True):
    ident = "TG-%d" % index
    record = {"id": ident, "name": name or "人物 %d" % index,
              "role": "角色 %d" % index, "priority": priority,
              "summary": "%s 的一句话画像" % ident, "context": "处境",
              "goals": ["目标一"], "frustrations": ["受挫点"], "current_behavior": "今天怎么办",
              "driving_forces": {
                  "positive": [driver(index, i, "+", "promise") for i in range(1, positives + 1)],
                  "negative": [driver(index, i, "-", "answer") for i in range(1, negatives + 1)]}}
    if transformation:
        record["transformation"] = {"before": "之前", "after": "之后"}
    return record


def product_yaml(status="已定稿", stage="收尾", mode="W", entry="工作坊",
                 goals=4, personas=None, connections=None, decisions=None,
                 feature_count=3, patterns=True, priority=None, effect_map=True,
                 revisions=None, vision="让本地咖啡馆有可自助的官网"):
    """手搓完整产物（各段均可局部替换）——用于 check / metrics 面用例。"""
    if not isinstance(goals, list):
        goals = [{"id": "BG-%d" % i, "kind": "愿景" if i == 1 else "目标",
                  "statement": vision if i == 1 else "目标 %d" % i}
                 for i in range(1, goals + 1)]
    for item in goals:
        if item.get("kind") == "目标":
            item.setdefault("metric", "指标")
            item.setdefault("target", "数值")
            item.setdefault("timeline", "6 个月")
    if personas is None:
        personas = [persona(1, priority="主"), persona(2), persona(3)]
    ids = [p["id"] for p in personas]
    top = ids[0]
    must = [personas[0]["driving_forces"]["positive"][0]["id"]]
    driver_ids = []
    for item in personas:
        driver_ids += [d["id"] for d in item["driving_forces"]["positive"]]
        driver_ids += [d["id"] for d in item["driving_forces"]["negative"]]
    priority = priority if priority is not None else {
        "ranked_personas": [{"id": pid, "why": "因为 %s" % pid} for pid in ids],
        "ranked_drivers": [{"id": driver_ids[0], "why": "因为最重要"},
                           {"id": driver_ids[1], "why": "因为次之"}],
        "focus_statement": {"top_group": top, "must": must,
                            "should": [personas[1]["driving_forces"]["positive"][0]["id"]],
                            "could": []}}
    scoring = {"primary": "高", "others": ["高"] * (len(personas) - 1)}
    features = []
    for i in range(1, feature_count + 1):
        features.append({"id": "FI-%d" % i, "name": "特征 %d" % i,
                         "scores": {"primary": scoring["primary"],
                                    "others": list(scoring["others"])},
                         "score": 5 + 3 * (len(personas) - 1),
                         "decision": "必须", "rationale": "为什么是它 %d" % i})
    if decisions:
        for index, value in decisions.items():
            features[index]["decision"] = value
    graph = {}
    if effect_map:
        count = len(goals) if connections is None else connections
        lines = ["BG%d --> PLATFORM" % i for i in range(len(goals))]
        lines += ["PLATFORM --> TG%d" % i for i in range(len(personas))]
        lines += ["TG%d --> DF%d" % (i, i) for i in range(len(personas))]
        if connections is not None:
            lines = lines[:connections]
        diagram = NL.join(
            ["```mermaid", "%%{init: {'theme':'base'}}%%", "flowchart LR",
             '    PLATFORM["<br/>"]']
            + ['    BG%d["<br/>"]' % i for i in range(len(goals))]
            + ['    TG%d["<br/>"]' % i for i in range(len(personas))]
            + ['    DF%d["WANTS<br/>%s<br/>FEARS<br/>%s"]' % (i, DRIVER_EMOJI[0],
                                                              DRIVER_EMOJI[1])
               for i in range(len(personas))]
            + ["    " + ln for ln in lines]
            + ["    " + item for item in CLASS_DEFS]
            + ["```"])
        graph = {
            "derived_from": PRODUCT_FILE, "format": "mermaid", "direction": "LR",
            "config": "%%{init: {'theme':'base'}}%%",
            "nodes": {"business_goals": ["BG%d" % i for i in range(len(goals))],
                      "platform": "PLATFORM",
                      "target_groups": ["TG%d" % i for i in range(len(personas))],
                      "driving_forces": ["DF%d" % i for i in range(len(personas))]},
            "connections": lines, "class_defs": list(CLASS_DEFS),
            "diagram": diagram}
    patterns = ({"shared": [{"ids": [must[0]], "note": "共性"}],
                 "unique": [{"id": personas[1]["driving_forces"]["positive"][0]["id"],
                             "note": "独有"}],
                 "tensions": []} if patterns else {})
    body = {
        "project": {"name": "mini", "created": "2026-09-18", "updated": "2026-09-21",
                    "status": status},
        "stage": stage, "mode": mode, "entry": entry,
        "business_goals": goals, "personas": personas,
        "driver_patterns": patterns, "priority": priority,
        "feature_impact": features, "effect_map": graph,
        "revisions": revisions if revisions is not None else [],
    }
    return dump(body)


class EngineCase(unittest.TestCase):
    """tmp 项目根 + diy-output 目录的公共夹具（默认备好上游定稿简报）。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="wdstrigger-")
        self.root = self.tmp.name
        self.out = os.path.join(self.root, "diy-output")
        os.makedirs(self.out, exist_ok=True)
        self.write(UPSTREAM_FILE, upstream_yaml())
        self.engine_path = ENGINE

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, rel, content):
        path = os.path.join(self.root, rel) if rel.startswith("diy-output") else os.path.join(
            self.out, rel)
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with io.open(path, "w", encoding="utf-8", newline="") as handle:
            handle.write(content)
        return path

    def read_text(self, rel):
        with io.open(os.path.join(self.out, rel), encoding="utf-8") as handle:
            return handle.read()

    def drop(self, rel):
        path = os.path.join(self.out, rel)
        if os.path.isfile(path):
            os.remove(path)

    def product(self, content):
        return self.write(PRODUCT_FILE, content)

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

    def metrics(self, *extra):
        return self.engine("metrics", *extra)

    def results(self, proc):
        return json.loads(proc.stdout)

    def codes(self, proc):
        return {x["code"] for x in self.results(proc)["violations"]}

    def warn_codes(self, proc):
        return {x["code"] for x in self.results(proc)["warnings"]}


class GateTests(EngineCase):
    """§2.6 ① 门禁（用法错误 exit 2 ≠ 枚举违规 exit 1 ≠ 空值 EMPTY_FIELD）。"""

    # trace: 任务书 §2.6 ①（init 无 --mode → exit 2）
    def test_gate_missing_mode_is_usage_error(self):
        r = self.raw("init", "--project-root", self.root,
                     "--output-dir", self.out, "--json")
        self.assertEqual(r.returncode, 2, "缺 --mode 须为 argparse 用法错误 exit 2：%s"
                         % (r.stdout + r.stderr))

    # trace: 任务书 §2.6 ①（非法值 → ENUM_INVALID exit 1）
    def test_gate_invalid_mode_is_enum_invalid(self):
        r = self.init("--mode", "X")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertEqual(self.codes(r), {"ENUM_INVALID"})

    # trace: 任务书 §2.6 ①（空值 → EMPTY_FIELD，且零产出）
    def test_gate_blank_mode_is_empty_field(self):
        r = self.init("--mode", "   ")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertEqual(self.codes(r), {"EMPTY_FIELD"})
        self.assertFalse(os.path.exists(os.path.join(self.out, PRODUCT_FILE)),
                         "门禁拒绝须零产出")

    # trace: 任务书 §2.2（--output-dir 必填于写盘子命令；--instance 一律不做）
    def test_gate_output_dir_mandatory_and_no_instance_flag(self):
        r = self.raw("init", "--mode", "W", "--project-root", self.root, "--json")
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        r2 = self.engine("list", "--instance", "demo")
        self.assertEqual(r2.returncode, 2, "--instance 不得进签名表：%s" % (r2.stdout + r2.stderr))

    # trace: 任务书 §2.2（--entry 非法值 → ENUM_INVALID）
    def test_gate_invalid_entry_is_enum_invalid(self):
        r = self.init("--mode", "W", "--entry", "凭空")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertEqual(self.codes(r), {"ENUM_INVALID"})


class UpstreamGateTests(EngineCase):
    """§2.6 ⑥ 跨技能门禁（§2.3.1 冻结）：读 wds-brief.yaml 且 project.status: 已定稿。"""

    # trace: 任务书 §2.3.1（上游产物缺失 → 一行说明 + 零产出停止 + 路由 diy-wds-brief）
    def test_missing_upstream_is_zero_write_stop(self):
        self.drop(UPSTREAM_FILE)
        r = self.init("--mode", "W")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertEqual(self.codes(r), {"MISSING_FILE"})
        self.assertIn("diy-wds-brief", json.dumps(self.results(r), ensure_ascii=False),
                      "缺失时的提示须点名路由到上游技能")
        self.assertFalse(os.path.exists(os.path.join(self.out, PRODUCT_FILE)), "须零产出")

    # trace: 任务书 §2.3.1（上游未定稿 → 门禁判据不满足，零产出停止）
    def test_upstream_not_final_is_zero_write_stop(self):
        self.write(UPSTREAM_FILE, upstream_yaml(status="草稿"))
        r = self.init("--mode", "W")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertEqual(self.codes(r), {"STATUS_MISMATCH"})
        self.assertFalse(os.path.exists(os.path.join(self.out, PRODUCT_FILE)), "须零产出")

    # trace: 任务书 §2.3.1（门禁满足 → 放行；check --final 复验上游仍在场且已定稿）
    def test_final_rechecks_upstream_gate(self):
        self.assertEqual(self.init("--mode", "W").returncode, 0)
        self.product(product_yaml(status="已定稿", stage="收尾"))
        self.assertEqual(self.check("--final").returncode, 0)
        self.write(UPSTREAM_FILE, upstream_yaml(status="草稿"))
        bad = self.check("--final")
        self.assertEqual(bad.returncode, 1, bad.stdout)
        self.assertEqual(self.codes(bad), {"STATUS_MISMATCH"})


class InitTests(EngineCase):
    """§2.6 ②③ init 骨架、重复 init 不覆盖、拒绝损坏。"""

    # trace: 任务书 §2.6 ②（exit 0 + 骨架结构，含 project.status: 草稿）
    def test_init_creates_skeleton_passing_check(self):
        r = self.init("--mode", "W", "--entry", "既有产物")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = self.results(r)
        self.assertIsNone(data["instance"])
        self.assertIn("updated", data)
        text = self.read_text(PRODUCT_FILE)
        self.assertIn("status: 草稿", text)
        self.assertIn("stage: 模式", text)
        self.assertIn("entry: 既有产物", text)
        self.assertIn("kind: 愿景", text, "骨架须含首条记录 BG-1（愿景节点）")
        self.assertIn("id: BG-1", text)
        self.assertIn("revisions: []", text)
        # 骨架即过 check（草稿期宽松：主体段可空）
        c = self.check()
        self.assertEqual(c.returncode, 0, c.stdout + c.stderr)
        self.assertEqual(self.results(c)["counts"]["records"], 1)

    # trace: 任务书 §2.6 ③（重复 init 不覆盖已有骨架；改模式 → SET_MISMATCH 零写入）
    def test_reinit_does_not_overwrite_existing_skeleton(self):
        self.assertEqual(self.init("--mode", "W").returncode, 0)
        # 用户已填的内容：手工落一段，重跑 init 后必须一字不动
        self.product(self.read_text(PRODUCT_FILE)
                     .replace("- id: BG-1" + NL,
                              "- id: BG-1" + NL + "  statement: 用户写的愿景" + NL))
        before = self.read_text(PRODUCT_FILE)
        same = self.init("--mode", "W")
        self.assertEqual(same.returncode, 0, same.stdout + same.stderr)
        self.assertTrue(self.results(same)["warnings"], "同值重跑须给一行「未覆盖」warning")
        after = self.read_text(PRODUCT_FILE)
        self.assertIn("用户写的愿景", after, "重复 init 不得覆盖已有内容")
        self.assertEqual([ln for ln in after.split(NL) if not ln.startswith("  updated:")],
                         [ln for ln in before.split(NL) if not ln.startswith("  updated:")],
                         "除 project.updated 外不得改动任何一行")
        # 改模式 → SET_MISMATCH 且零写入（模式决定整条管线，不得被静默改写）
        diff = self.init("--mode", "D")
        self.assertEqual(diff.returncode, 1, diff.stdout)
        self.assertEqual(self.codes(diff), {"SET_MISMATCH"})
        self.assertNotIn("mode: D", self.read_text(PRODUCT_FILE))

    # trace: 任务书 §2.6 ③（损坏产物拒绝且零写入）
    def test_init_refuses_damaged_product_with_zero_write(self):
        self.product("project: [" + NL)
        before = self.read_text(PRODUCT_FILE)
        bad = self.init("--mode", "W")
        self.assertEqual(bad.returncode, 1, bad.stdout)
        self.assertNotIn("Traceback", bad.stderr)
        self.assertEqual(self.codes(bad), {"UNPARSABLE_YAML"})
        self.assertEqual(self.read_text(PRODUCT_FILE), before,
                         "拒绝路径不得改动产物一个字节")


class ListShowTests(EngineCase):
    """§2.6 ④ list / show（单记录 → 至多一条；--id 取 TG-<n>）。"""

    # trace: 任务书 §2.6 ④（只回七字段 + --status 过滤生效）
    def test_list_returns_fixed_fields_and_filters_by_status(self):
        self.init("--mode", "W")
        r = self.engine("list")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = self.results(r)
        self.assertEqual(len(data["records"]), 1)
        self.assertEqual(sorted(data["records"][0]),
                         ["entry", "goals", "mode", "name", "personas", "stage",
                          "status", "updated"])
        keep = self.engine("list", "--status", "草稿")
        self.assertEqual(len(self.results(keep)["records"]), 1)
        none = self.engine("list", "--status", "已定稿")
        self.assertEqual(self.results(none)["records"], [])
        bad = self.engine("list", "--status", "草稿中")
        self.assertEqual(bad.returncode, 1, bad.stdout)
        self.assertEqual(self.codes(bad), {"ENUM_INVALID"})
        # 产物缺席：按空列表处理，不报错
        self.drop(PRODUCT_FILE)
        empty = self.engine("list")
        self.assertEqual(empty.returncode, 0, empty.stdout + empty.stderr)
        self.assertEqual(self.results(empty)["records"], [])

    # trace: 任务书 §2.2（show 整份 / --id TG-<n> 单条；不存在 → UNKNOWN_ID）
    def test_show_whole_document_and_single_persona(self):
        self.product(product_yaml())
        whole = self.engine("show")
        self.assertEqual(whole.returncode, 0, whole.stdout + whole.stderr)
        doc = self.results(whole)["document"]
        self.assertEqual(doc["project"]["status"], "已定稿")
        self.assertEqual(len(doc["personas"]), 3)
        one = self.engine("show", "--id", "TG-2")
        self.assertEqual(one.returncode, 0, one.stdout + one.stderr)
        self.assertEqual(self.results(one)["record"]["id"], "TG-2")
        miss = self.engine("show", "--id", "TG-9")
        self.assertEqual(miss.returncode, 1, miss.stdout)
        self.assertEqual(self.codes(miss), {"UNKNOWN_ID"})
        # 产物缺席 → MISSING_FILE
        self.drop(PRODUCT_FILE)
        absent = self.engine("show")
        self.assertEqual(absent.returncode, 1, absent.stdout)
        self.assertEqual(self.codes(absent), {"MISSING_FILE"})


class CheckTests(EngineCase):
    """§2.6 ⑤ check 的各类检出 + 定稿同档规则。"""

    def complete(self, **kwargs):
        self.product(product_yaml(**kwargs))
        return os.path.join(self.out, PRODUCT_FILE)

    # trace: 任务书 §2.6 ⑤（枚举越界 → ENUM_INVALID）
    def test_check_detects_enum_invalid(self):
        self.complete()
        ok = self.check("--final")
        self.assertEqual(ok.returncode, 0, ok.stdout + ok.stderr)
        self.complete(status="定稿")
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ENUM_INVALID", self.codes(r))
        self.complete(stage="做梦")
        r2 = self.check()
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertIn("ENUM_INVALID", self.codes(r2))

    # trace: 任务书 §2.6 ⑤（必填键缺失 → EMPTY_FIELD，where 点名键名）
    def test_check_detects_missing_required_key_with_name(self):
        goals = [{"id": "BG-1", "kind": "愿景", "statement": "愿景"},
                 {"id": "BG-2", "kind": "目标", "statement": "目标"}]  # 只有 1 条目标
        self.complete(goals=goals)
        r = self.check("--final")
        self.assertEqual(r.returncode, 1, r.stdout)
        places = [x["where"] for x in self.results(r)["violations"] if x["code"] == "EMPTY_FIELD"]
        self.assertTrue(any("business_goals" in x for x in places), places)
        # 人物缺必填键 → where 点名键名
        broken = [dict(persona(1, priority="主"), context=""),
                  persona(2), persona(3)]
        self.complete(personas=broken)
        r2 = self.check("--final")
        places2 = [x["where"] for x in self.results(r2)["violations"]
                   if x["code"] == "EMPTY_FIELD"]
        self.assertTrue(any(x.endswith("personas[0].context") for x in places2), places2)

    # trace: 任务书 §2.6 ⑤（status 与 stage 不同档 → STATUS_MISMATCH）
    def test_check_detects_status_stage_mismatch(self):
        self.complete(status="已定稿", stage="驱动")
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("STATUS_MISMATCH", self.codes(r))
        # --final 要求 status: 已定稿 + stage: 收尾
        self.complete(status="草稿", stage="收尾")
        final = self.check("--final")
        self.assertEqual(final.returncode, 1, final.stdout)

    # trace: 任务书 §2.6 ⑤ + 裁定 16（驱动因素数量越界 → EMPTY_FIELD 点名键）
    def test_check_enforces_driver_and_persona_ranges(self):
        self.complete(personas=[persona(1, priority="主", positives=2), persona(2)])
        r = self.check("--final")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertTrue(any("driving_forces" in x["where"]
                            for x in self.results(r)["violations"]), self.results(r))
        self.complete(personas=[persona(i) for i in range(1, 6)])
        r2 = self.check("--final")
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertTrue(any("personas" in x["where"]
                            for x in self.results(r2)["violations"]), self.results(r2))

    # trace: 任务书 §2.6 ⑤ + 裁定 8/16（ID 唯一性与引用可解析）
    def test_check_detects_duplicate_and_unknown_ids(self):
        twins = [persona(1, priority="主"), persona(1)]
        self.complete(personas=twins)
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("DUPLICATE_ID", self.codes(r))
        # 引用不存在的驱动因素 ID（只动引用、不动驱动因素本体）→ UNKNOWN_ID
        data = product_yaml()
        broken = data.replace("    must:" + NL + "      - DF-1.1+",
                              "    must:" + NL + "      - DF-9.9+")
        self.assertNotEqual(data, broken, "夹具替换须命中 focus_statement.must")
        self.product(broken)
        r2 = self.check()
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertIn("UNKNOWN_ID", self.codes(r2))

    # trace: 任务书 §2.6 ⑤ / 裁定 10（评分重算不符 → SET_MISMATCH）
    def test_check_detects_score_and_decision_mismatch(self):
        data = product_yaml()
        self.product(data.replace("score: 11", "score: 99"))
        r = self.check("--final")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("SET_MISMATCH", self.codes(r))
        # 主人物高影响却判「可选」→ 源 steps-v 04 的硬规则
        self.product(product_yaml(decisions={0: "可选"}))
        r2 = self.check("--final")
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertIn("STATUS_MISMATCH", self.codes(r2))

    # trace: 任务书 §2.6 ⑤ / §10 项 7（未解析令牌 + 零 [假设]）
    def test_check_detects_unresolved_token_and_assumption(self):
        self.product(product_yaml(vision="使用 {skill-name} 生成"))
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("TOKEN_UNRESOLVED", self.codes(r))
        self.assertIn("{skill-name}", r.stdout)
        # 白名单令牌不报
        self.product(product_yaml(vision="{project-root}/diy-output 与 {output_dir}"))
        self.assertEqual(self.check().returncode, 0)
        self.product(product_yaml(vision="[假设] 客户会买"))
        f = self.check("--final")
        self.assertEqual(f.returncode, 1, f.stdout)
        self.assertIn("ASSUMPTION_PRESENT", self.codes(f))

    # trace: 任务书 §2.6 ⑤（产物缺席 → MISSING_FILE；损坏 → UNPARSABLE_YAML）
    def test_check_missing_and_damaged_product(self):
        miss = self.check()
        self.assertEqual(miss.returncode, 1, miss.stdout)
        self.assertEqual(self.codes(miss), {"MISSING_FILE"})
        self.product("personas: [" + NL)
        bad = self.check()
        self.assertEqual(bad.returncode, 1, bad.stdout)
        self.assertEqual(self.codes(bad), {"UNPARSABLE_YAML"})


class MetricsTests(EngineCase):
    """§2.6 ⑨ 本技能特有边界：`metrics` 的四条越界情形（一律 warning 不阻断）。"""

    # trace: 任务书 §2.2（合规产物的 metrics 零 warning + exit 0 + counts 在场）
    def test_metrics_clean_document(self):
        self.product(product_yaml())
        r = self.metrics()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = self.results(r)
        self.assertEqual(data["warnings"], [])
        self.assertEqual(data["counts"]["personas"], 3)
        self.assertEqual(data["counts"]["connections_expected"], 10)
        self.assertEqual(data["counts"]["connections_actual"], 10)

    # trace: 任务书 §2.2（越界情形 1/2：每人 3–5 正 + 3–5 负）
    def test_metrics_warns_on_driver_range(self):
        self.product(product_yaml(personas=[persona(1, priority="主", positives=2),
                                            persona(2, negatives=6)]))
        r = self.metrics()
        self.assertEqual(r.returncode, 0, "越界只给 warning，不阻断：%s" % r.stdout)
        codes = self.warn_codes(r)
        self.assertIn("EMPTY_FIELD", codes)
        text = json.dumps(self.results(r), ensure_ascii=False)
        self.assertIn("TG-1", text)
        self.assertIn("TG-2", text)

    # trace: 任务书 §2.2（越界情形 3：人物群 2–4）
    def test_metrics_warns_on_persona_range(self):
        self.product(product_yaml(personas=[persona(i) for i in range(1, 6)]))
        r = self.metrics()
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertTrue(self.results(r)["warnings"], "5 群须给 warning")
        self.assertIn("TG-5", json.dumps(self.results(r), ensure_ascii=False))

    # trace: 任务书 §2.2（越界情形 4：连接数 = 目标数 + 2×人物数）
    def test_metrics_warns_on_connection_count(self):
        self.product(product_yaml(connections=8))
        r = self.metrics()
        self.assertEqual(r.returncode, 0, r.stdout)
        data = self.results(r)
        self.assertEqual(data["counts"]["connections_expected"], 10)
        self.assertEqual(data["counts"]["connections_actual"], 8)
        self.assertTrue(data["warnings"], "连接数不符须给 warning")

    # trace: 任务书 §2.2（--id 窄化到单个人物；不存在 → UNKNOWN_ID；缺席 → MISSING_FILE）
    def test_metrics_id_narrowing_and_absence(self):
        self.product(product_yaml(connections=8))
        one = self.metrics("--id", "TG-2")
        self.assertEqual(one.returncode, 0, one.stdout)
        self.assertFalse(any("TG-1" in x["msg"] for x in self.results(one)["warnings"]),
                         "窄化后不得再报别的人物")
        miss = self.metrics("--id", "TG-9")
        self.assertEqual(miss.returncode, 1, miss.stdout)
        self.assertEqual(self.codes(miss), {"UNKNOWN_ID"})
        self.drop(PRODUCT_FILE)
        absent = self.metrics()
        self.assertEqual(absent.returncode, 1, absent.stdout)
        self.assertEqual(self.codes(absent), {"MISSING_FILE"})


class ReceiptTests(EngineCase):
    """§2.6 ⑦ 回执 schema。"""

    # trace: 任务书 §2.2（公共键 + instance 恒 null + warnings 同形 + 单行 JSON）
    def test_receipt_keys_and_json_single_line(self):
        self.assertFalse(os.path.exists(os.path.join(self.out, PRODUCT_FILE)))
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
        self.assertFalse(os.path.exists(os.path.join(self.out, PRODUCT_FILE)),
                         "只读子命令不得写盘")
        init = self.results(self.init("--mode", "W"))
        self.assertIn("updated", init, "init 写盘回执须含 updated")
        bad = self.init("--mode", "")
        for item in self.results(bad)["violations"]:
            self.assertEqual(sorted(item), sorted(V_SHAPE))
            self.assertNotIn("\\\\", item["where"])

    # trace: 任务书 §2.2（--output-dir 必填于写盘子命令；只读子命令签名可省 → 需读产物时
    #        明确报缺：exit 1 结构化违规，而非 exit 2 argparse 用法错误）
    def test_output_dir_optional_in_signature_but_reported_when_needed(self):
        for command in ("list", "show", "check", "metrics"):
            r = self.raw(command, "--project-root", self.root, "--json")
            self.assertEqual(r.returncode, 1,
                             "%s 省 --output-dir 须为结构化违规 exit 1（签名可省）：%s"
                             % (command, r.stdout + r.stderr))
            data = json.loads(r.stdout)
            self.assertIsNone(data["output_dir"])
            self.assertEqual({x["code"] for x in data["violations"]}, {"EMPTY_FIELD"})
            self.assertIn("--output-dir", data["violations"][0]["where"])


class SkillContractTests(unittest.TestCase):
    """§2.6 ⑧ SKILL.md 契约冒烟（母本六节逐字 + 终门句 + 产物路径句 + frontmatter 实值）。"""

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
        self.assertIn("wds_trigger.py", raw, "终门句未指向本技能领域引擎")
        self.assertIn("check --final", raw, "终门句缺 check --final")
        self.assertIn("wds-trigger.yaml", raw, "产物路径声明句不在场")
        self.assertIn("diy-wds-trigger", raw)
        self.assertIsNone(PREVIOUS_CHECK_RE.search(raw),
                          "红线：不得教 diyc.py 会拒的 `check --type <型> --previous`")
        lines = raw.replace(NL + chr(13), NL).replace(chr(13) + NL, NL).rstrip(NL).split(NL)
        self.assertLessEqual(len(lines), 90, "SKILL.md 超 90 行（薄主文件硬阈值）")

    # trace: 任务书 §8 验收 #8 / 裁定 4（frontmatter 六字段逐字取源实值）
    def test_frontmatter_six_fields_take_source_values(self):
        raw = self.read_skill()
        head = raw.split("---")[1]
        for key, value in FRONTMATTER:
            self.assertIn("%s: %s" % (key, value), head,
                          "frontmatter %s 须取源实值 %s" % (key, value))
        self.assertIn("diy-wds-brief", head, "缺中文注释行（WDS 线交接说明）")

    # trace: 任务书 §2.4（6 个步骤文件冻结名 + 一行指路一致）
    def test_step_files_frozen_names(self):
        names = sorted(n for n in os.listdir(os.path.join(SKILL_DIR, "steps"))
                       if n.endswith(".md"))
        self.assertEqual(names, ["01-mode.md", "02-goals.md", "03-drivers.md",
                                 "04-features.md", "05-documents.md", "06-finish.md"])
        raw = self.read_skill()
        for name in names:
            self.assertIn(name, raw, "SKILL.md 工作流段缺 %s 的一行指路" % name)

    # trace: 任务书 §2.2 红线 + 裁定 7（Effect Map 收编骨架在场）
    def test_no_wds_type_previous_check_taught_and_template_present(self):
        steps = os.path.join(SKILL_DIR, "steps")
        for rel in ["SKILL.md"] + ["steps/" + n for n in sorted(os.listdir(steps))
                                   if n.endswith(".md")] + ["templates/trigger-map.template.md"]:
            path = os.path.join(SKILL_DIR, rel)
            if not os.path.isfile(path):
                self.fail("%s 尚未交付" % rel)
            with io.open(path, encoding="utf-8") as handle:
                text = handle.read()
            self.assertIsNone(PREVIOUS_CHECK_RE.search(text),
                              "%s 教了 `check --type <型> --previous`（diyc 8 型封闭集）" % rel)
            for wds_type in ("wds-brief", "wds-trigger", "wds-scenarios"):
                self.assertNotIn("--type %s" % wds_type, text,
                                 "%s 把 WDS 型当成了 diyc 的类型" % rel)


class FinishChecklistTests(unittest.TestCase):
    """§2.6 ⑨ / §2.4：13 维去重后的质检分组 + 源 steps-v 五维承载位。"""

    def read_finish(self):
        if not os.path.isfile(FINISH_STEP):
            self.skipTest("steps/06-finish.md 尚未交付——质检查表待补")
        with io.open(FINISH_STEP, encoding="utf-8") as handle:
            return handle.read()

    # trace: 任务书 §2.4 / 裁定 15（五维校验并入 06-finish.md 质检查表）
    def test_checklist_groups_and_validation_dimensions(self):
        raw = self.read_finish()
        for label in FINISH_GROUPS:
            self.assertIn(label, raw, "缺质检分组 %s" % label)
        for label in VALIDATE_DIMS:
            self.assertIn(label, raw, "缺源 steps-v 校验维 %s" % label)

    # trace: 任务书 §2.4（13 维去重后的机械项数）
    def test_checkbox_item_count(self):
        raw = self.read_finish()
        items = [ln for ln in raw.replace(chr(13) + NL, NL).split(NL)
                 if ln.strip().startswith("- [ ]")]
        self.assertEqual(len(items), FINISH_ITEMS,
                         "06-finish.md 的 `- [ ]` 须恰 %d 项（源 104 项经 13 维去重），实为 %d"
                         % (FINISH_ITEMS, len(items)))


class InternalTableTests(unittest.TestCase):
    """引擎内表核对（回报必答 ③⑧⑨⑩ 的机械证据；直接导入引擎模块）。"""

    def load_module(self):
        if not os.path.isfile(ENGINE):
            self.skipTest("wds_trigger.py 尚未交付")
        spec = importlib.util.spec_from_file_location("wds_trigger_under_test", ENGINE)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    # trace: 任务书 §0.2 裁定 6（三组互斥口径归一的取值）
    def test_ranges_match_ruling_six(self):
        mod = self.load_module()
        self.assertEqual(tuple(getattr(mod, "DRIVER_RANGE", ())), DRIVER_RANGE)
        self.assertEqual(tuple(getattr(mod, "PERSONA_RANGE", ())), PERSONA_RANGE)
        self.assertEqual(tuple(getattr(mod, "GOAL_RANGE", ())), GOAL_RANGE)

    # trace: 任务书 §0.2 裁定 7（08g 的四类样式色值逐字收编）
    def test_class_defs_are_verbatim(self):
        mod = self.load_module()
        defs = list(getattr(mod, "CLASS_DEFS", ()))
        self.assertEqual(defs, list(CLASS_DEFS), "四类样式须与 08g:63-66 逐字一致")
        self.assertEqual(len(defs), 4)

    # trace: 任务书 §0.2 裁定 16（driving_forces 嵌在 personas[] 内，不设顶层并列段）
    def test_driving_forces_are_nested_not_top_level(self):
        mod = self.load_module()
        self.assertEqual(tuple(getattr(mod, "PERSONA_KEYS", ()))[:1], ("id",))
        self.assertIn("driving_forces", getattr(mod, "PERSONA_KEYS", ()))
        self.assertNotIn("driving_forces", getattr(mod, "TOP_KEYS", ()),
                         "裁定 16：不得设与 personas[] 并列的顶层 driving_forces[]")
        self.assertIn("driver_patterns", getattr(mod, "TOP_KEYS", ()))

    # trace: 任务书 §2.2（母本 §8 两值口径：单记录 → 顶层 project.status）
    def test_status_enum_is_master_two_values(self):
        mod = self.load_module()
        self.assertEqual(tuple(getattr(mod, "STATUS_ENUM", ())), ("草稿", "已定稿"))
        self.assertEqual(tuple(getattr(mod, "MODE_ENUM", ())), ("W", "S", "D"))
        self.assertEqual(tuple(getattr(mod, "ENTRY_ENUM", ())), ("工作坊", "既有产物"))
        self.assertEqual(tuple(getattr(mod, "DECISION_ENUM", ())), ("必须", "应该", "可选"))
        self.assertEqual(tuple(getattr(mod, "TOKEN_WHITELIST", ())),
                         ("{project-root}", "{output_dir}"))


if __name__ == "__main__":
    unittest.main()
