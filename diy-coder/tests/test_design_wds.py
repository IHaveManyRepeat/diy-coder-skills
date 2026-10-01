# -*- coding: utf-8 -*-
"""W7 跨工位测试（C·3a 任务书 §6 断言面 1 / 2 / 3 / 6 / 7 / 8）。

**定位（§6 原文）**：只测「需要两个以上工位产物合力才能断言」的面——单工位能自测的
一律不归本文件。面 4（`transition` 后重跑 `validate` 自洽）与面 5（终门联动）在同批
新增的 `test_design_open_questions.py`。

| 类 | 断言面 | 为什么必须跨工位 |
| --- | --- | --- |
| `UpstreamToDesignHandoverTests` | 1 | 上游 `diy-wds-scenarios`（B7a 产物 schema + 终门）↔ W1 的源判定/场景桥 |
| `DesignToDevFieldTests` | 2 | W1 的产物 schema ↔ W3 的 WDS 读契约（两端分属两工位） |
| `ScenarioBridgeTests` | 3 | W1 的场景桥（`steps/scenario-bridge.md`）↔ W2 的 `detect` / `validate` |
| `DualSourceZeroOutputTests` | 6 | W1 的双源门禁句 ↔ W2 的引擎「不写盘」 |
| `MotherTextMatrixTests` | 7 | 四份主文件分属 W1 / W3 / W4 / W5——须一次覆盖 |
| `WdsPageChainTests` | 8 | W1 工作流 + W2 `transition` + W3 实现 + W4 审查判定，四工位产物合一 |

**去重纪律（§6 末段）**：本文件与 W1/W2/W3/W4/W5/W6/W8/W9 的测试文件逐条比对过断言串
（`grep` 机械比对，见回报的去重表）；单工位已自测的断言一律不在此重复，各保留项的
差异点写在类 docstring 的「与既有测试的分工」行。
"""
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
SKILLS = os.path.join(HERE, "..", "skills")
DESIGN_SKILL_MD = os.path.join(SKILLS, "diy-design", "SKILL.md")
DESIGN_STEPS = os.path.join(SKILLS, "diy-design", "steps")
DEV_SKILL_MD = os.path.join(SKILLS, "diy-dev", "SKILL.md")
SCENARIOS_SKILL_MD = os.path.join(SKILLS, "diy-wds-scenarios", "SKILL.md")
SCENARIOS_PY = os.path.join(SKILLS, "diy-wds-scenarios", "scripts", "wds_scenarios.py")
DESIGN_PY = os.path.join(SKILLS, "diy-design", "scripts", "design.py")
NL = chr(10)

# §6 断言面 7 的「四技能」= W1 / W3 / W4 / W5 各改一份主文件的那些技能
MOTHER_SKILLS = ("diy-design", "diy-dev", "diy-review", "diy-wds-evolution")

# 面 1：下游 `diy-design` 消费的上游字段（字段 → 该消费点所在的技能文件）
DESIGN_CONSUMED_FIELDS = {
    "design_intent": "SKILL.md",
    "design_status": "SKILL.md",
    "target_group": "c-discuss.md",
    "purpose": "p-specify.md",
    "entry_context": "p-specify.md",
    "exit_action": "p-specify.md",
    "on_page_interactions": "p-specify.md",
}

FOUR_STATES = NL.join([
    "  states:",
    "  - name: 悬停",
    "    signals: [图标, 动效]",
    "  - name: 空态",
    "    signals: [文字]",
    "  - name: 加载中",
    "    signals: [图标, 动效]",
    "  - name: 错误",
    "    signals: [图标, 文字]",
])

# 结构稿 HTML：色值全走 token 变量定义位、字阶/间距走 var()、语义面齐（check 可过）
GOOD_PROTOTYPE = NL.join([
    "<!DOCTYPE html>",
    '<html lang="zh-CN">',
    "<head>",
    '<meta charset="utf-8">',
    "<title>首页</title>",
    "<style>",
    ":root {",
    "  --color-bg: #ffffff;",
    "  --color-surface: #f5f5f2;",
    "  --color-text: #1a1a1a;",
    "  --color-accent: #0a5c8c;",
    "  --space-unit: 4px;",
    "}",
    "body { background: var(--color-bg); color: var(--color-text);"
    " padding: var(--space-4); }",
    "button { background: var(--color-accent); color: var(--color-bg); }",
    ".state { font-size: var(--font-md); }",
    "</style>",
    "</head>",
    "<body>",
    "<h1>首页</h1>",
    '<p class="state" data-state="悬停">悬停显示更多</p>',
    '<ul class="state" data-state="空态"><li>暂无内容</li></ul>',
    '<div class="state" data-state="加载中">加载中…</div>',
    '<div class="state" data-state="错误">加载失败</div>',
    '<button type="button">开始</button>',
    "</body>",
    "</html>",
])

# 实现稿：色值走 var()、字阶走 var()，`// trace:` 取 WDS 形态（`diy-dev/SKILL.md:75`）
IMPL_JS = NL.join([
    "// trace: SC-01.P1 加载中",
    "export function mount(root) {",
    "  root.style.background = 'var(--color-bg)';",
    "  root.style.color = 'var(--color-text)';",
    "}",
])


def read(path):
    with io.open(path, encoding="utf-8") as fh:
        return fh.read()


def run(script, args, cwd=None):
    return subprocess.run([sys.executable, script] + args,
                          capture_output=True, text=True, encoding="utf-8", cwd=cwd)


def run_json(script, args, cwd=None):
    proc = run(script, args, cwd=cwd)
    try:
        return proc.returncode, json.loads(proc.stdout)
    except ValueError:
        raise AssertionError("回执不是单行 JSON：rc=%s%s%s"
                             % (proc.returncode, NL, proc.stdout + proc.stderr))


def design_text(project_status="草稿", page_status="未开始", page_id="SC-01.P1",
                with_status_key=True, implementation=None, extra_pages=()):
    """WDS 线 design.yaml：一页四态齐 + 结构稿在场（页级门可过）。"""
    lines = [
        "project:",
        "  name: wds-mini",
        "  status: %s" % project_status,
        "  created: 2026-01-01",
        "  updated: 2026-01-01",
        "direction: 瑞士编辑风——大字阶对比、留白节奏、单强调色",
        "frontend_framework: html",
        "form_factor: 响应式 Web",
        "modes: 亮",
        "tokens:",
        "  color:",
        "    bg: '#ffffff'",
        "    surface: '#f5f5f2'",
        "    text: '#1a1a1a'",
        "    text_muted: '#5a5a5a'",
        "    accent: '#0a5c8c'",
        "    accent_text: '#ffffff'",
        "  spacing:",
        "    unit: 4px",
        "    scale: [4px, 8px, 16px, 24px, 48px]",
        "  typography:",
        "    family_base: \"'Source Han Sans', sans-serif\"",
        "    family_heading: \"'Source Han Serif', serif\"",
        "    scale: [0.875rem, 1rem, 1.25rem, 2rem, 3rem]",
        "pages:",
        "- id: %s" % page_id,
        "  name: 首页",
        "  route: /",
    ]
    if with_status_key:
        lines.append("  status: %s" % page_status)
    lines.append(FOUR_STATES)
    lines.append("  prototype: prototypes/%s.html" % page_id)
    if implementation:
        lines.append("  implementation: %s" % implementation)
    for pid in extra_pages:
        lines += ["- id: %s" % pid, "  name: 页 %s" % pid, "  route: /%s" % pid.lower(),
                  "  status: 未开始", FOUR_STATES,
                  "  prototype: prototypes/%s.html" % pid]
    return NL.join(lines) + NL


def upstream_scenarios_doc():
    """上游 `diy-wds-scenarios` 的合法产物（终门 `check --final` 可过）。"""
    return {
        "project": {"name": "wds-mini", "created": "2026-01-01",
                    "updated": "2026-01-02", "status": "已定稿"},
        "scope": {"site_type": "presentation", "scale": "small",
                  "scenario_format": "screen-flow",
                  "page_strategy": {"individual": ["首页"], "templated": []}},
        "page_inventory": [{"name": "首页", "purpose": "承接落地"}],
        "scenarios": [{
            "id": "SC-01",
            "name": "游客 的 看首页",
            "priority": 1,
            "status": "已大纲",
            "trigger_map_context": {"target_group": "TG-1", "drivers": ["DF-1.1+"],
                                    "business_goal": "BG-1"},
            "design_intent": "K",
            "design_status": "not-started",
            "transaction": "看清产品做什么",
            "situation": "首访",
            "device": "桌面",
            "entry": "搜索引擎",
            "driving_forces": {"hope": "一眼看懂", "worry": "看不懂"},
            "success": {"user": "知道下一步", "business": "留下线索"},
            "pages": [{"id": "SC-01.P1", "slug": "01.1-home", "name": "首页",
                       "purpose": "承接落地", "entry_context": "从搜索结果来",
                       "exit_action": "点开始", "on_page_interactions": []}],
        }],
        "revisions": [],
    }


class W7Harness(unittest.TestCase):
    """临时项目根 + 产物写读（一律走子进程调引擎，验真回执）。"""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="w7-")
        self.root = self.tmp
        self.out = os.path.join(self.root, "diy-output")
        os.makedirs(self.out, exist_ok=True)
        with io.open(os.path.join(self.root, "diy-coder.yaml"), "w", encoding="utf-8") as fh:
            fh.write("paths:" + NL + "  output_dir: diy-output" + NL)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write(self, rel, content):
        """写 <root>/diy-output/<rel>（content 为 str 或 dict → safe_dump）。"""
        path = os.path.join(self.out, rel)
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        text = content if isinstance(content, str) else yaml.safe_dump(
            content, allow_unicode=True, sort_keys=False, default_flow_style=False)
        with io.open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
        return path

    def doc(self, rel):
        with io.open(os.path.join(self.out, rel), encoding="utf-8") as fh:
            return yaml.safe_load(fh)

    def files_under(self, path):
        found = []
        for dirpath, _dirs, names in os.walk(path):
            found += [os.path.join(dirpath, n) for n in names]
        return sorted(found)

    def design(self, **kwargs):
        return self.write("design.yaml", design_text(**kwargs))

    def prototype(self, page_id="SC-01.P1"):
        return self.write("prototypes/%s.html" % page_id, GOOD_PROTOTYPE)


# ---------------------------------------------------------------- 面 1

class UpstreamToDesignHandoverTests(W7Harness):
    """断言面 1：`wds-scenarios.yaml` → `diy-design` 字段级对账。

    两端分属两批施工：上游 schema / 终门（B7a，本批只读）与下游源判定 + 场景桥
    （W1）。**与既有测试的分工**：W1 的 `test_wds_upstream_contract_matches` 只断言
    3 个键名在场；本类跑「合法上游产物」并用上游引擎的必填常量反向核下游消费面。
    """

    def setUp(self):
        super().setUp()
        self.write("wds-trigger.yaml", {
            "project": {"name": "wds-mini", "status": "已定稿"},
            "personas": [{"id": "TG-1", "name": "游客"}],
        })
        self.scenarios_path = self.write("wds-scenarios.yaml", upstream_scenarios_doc())

    # trace: C·3a §6 面 1（上游产物的合法性由上游引擎判定——本夹具是「真产物」）
    def test_upstream_fixture_passes_its_own_final_gate(self):
        rc, data = run_json(SCENARIOS_PY, [
            "check", "--final", "--project-root", self.root,
            "--output-dir", self.out, "--json"])
        self.assertEqual(rc, 0, json.dumps(data, ensure_ascii=False))
        self.assertTrue(data["ok"], data.get("violations"))
        self.assertEqual(data["counts"]["coverage"], "1/1", data["counts"])

    # trace: C·3a §6 面 1（字段级对账：下游消费的每个字段 ∈ 上游结构块声明的模式）
    def test_every_consumed_field_is_declared_upstream(self):
        block = read(SCENARIOS_SKILL_MD)
        for field, where in sorted(DESIGN_CONSUMED_FIELDS.items()):
            with self.subTest(field=field):
                self.assertIn(field, block,
                              "上游结构块不再声明 %s（下游消费面越出上游模式）" % field)
                design_doc = read(DESIGN_SKILL_MD) if where == "SKILL.md" \
                    else read(os.path.join(DESIGN_STEPS, where))
                self.assertIn(field, design_doc,
                              "设计侧消费点 %s 未出现上游字段 %s" % (where, field))
        # 上游终门的必填面由上游引擎常量机械取数，须逐名在上游结构块里声明
        source = read(SCENARIOS_PY)
        for const in ("SCENARIO_REQUIRED", "SCENARIO_NESTED", "PAGE_REQUIRED",
                      "INVENTORY_KEYS"):
            block_const = re.search(r"%s\s*=\s*\((.*?)\)\n" % const, source, re.S)
            self.assertIsNotNone(block_const, "上游不再定义 %s" % const)
            names = set(re.findall(r'"([a-z_]+)"', block_const.group(1)))
            self.assertTrue(names, "上游 %s 未提取到任何字段名——取数规则脱钩" % const)
            for name in sorted(names):
                self.assertIn(name, block, "上游引擎终门要求 %s，结构块未声明" % name)

    # trace: C·3a §6 面 1（上游五值意图域 → 设计侧活动路由：值域两处必须同源）
    def test_design_intent_domain_matches_upstream_enum(self):
        source = read(SCENARIOS_PY)
        enum = re.search(r"DESIGN_INTENT_ENUM\s*=\s*\((.*?)\)", source)
        self.assertIsNotNone(enum, "上游不再定义 DESIGN_INTENT_ENUM")
        values = re.findall(r'"([A-Z])"', enum.group(1))
        self.assertEqual(len(values), 5, "上游意图值数变了：%s" % values)
        declared = re.search(r"`design_intent`（`([^`]+)`）", read(DESIGN_SKILL_MD))
        self.assertIsNotNone(declared, "设计侧未声明 design_intent 的值域")
        self.assertEqual(set(declared.group(1).split("|")), set(values),
                         "设计侧声明的意图值域与上游枚举不同源")
        # 值的落点：K/C/S/D 各有活动步骤文件（L = Later，落点见回报的未决项）
        routing = read(DESIGN_SKILL_MD).split("## 工作流", 1)[1].split("## 结构", 1)[0]
        for value, step in (("K", "k-sketch.md"), ("C", "c-discuss.md"),
                            ("S", "s-suggest.md"), ("D", "d-dream.md")):
            with self.subTest(intent=value):
                paired = re.findall(r"\[%s\][^%s]*%s" % (value, NL, re.escape(step)), routing)
                self.assertEqual(len(paired), 1,
                                 "活动 [%s] 未与步骤文件 %s 同行路由（命中 %d 处）"
                                 % (value, step, len(paired)))
                self.assertTrue(os.path.isfile(os.path.join(DESIGN_STEPS, step)),
                                "路由目标步骤文件不在场：%s" % step)

    # trace: C·3a §6 面 1（覆盖矩阵：上游机械核过 → 下游显式声明「不重核」）
    def test_coverage_matrix_is_upstream_gated_and_not_rechecked(self):
        self.assertIn("def check_coverage", read(SCENARIOS_PY),
                      "上游不再机械核覆盖矩阵——下游的「不重核」失去前提")
        rule = [ln for ln in read(DESIGN_SKILL_MD).splitlines()
                if "覆盖矩阵" in ln and "不重核" in ln]
        self.assertEqual(len(rule), 1,
                         "设计侧未声明「覆盖矩阵不重核」（命中 %d 行）" % len(rule))


# ---------------------------------------------------------------- 面 2

class DesignToDevFieldTests(W7Harness):
    """断言面 2：`diy-design` 产物 → `diy-dev` WDS 模式的字段级对账。

    schema 侧归 W1、读契约与写权归 W3——两端分属两工位。**与既有测试的分工**：W3 自建
    夹具跑单条命令（transition / audit / GATE_FAILED）；本类核「设计侧 schema 的字段
    面 == dev 侧读契约的字段面」，并验多次写回只动 dev 声称的那一个字段。
    """

    DEV_CONSUMED = {
        "project.status": ["diy-dev/SKILL.md"],
        "pages[].status": ["diy-dev/SKILL.md", "steps/wds-finalize.md"],
        "states[].signals": ["diy-dev/SKILL.md", "steps/wds-implement.md"],
        "prototype": ["diy-dev/SKILL.md", "steps/wds-implement.md"],
        "implementation": ["diy-dev/SKILL.md", "steps/wds-implement.md"],
        "design_status": ["diy-dev/SKILL.md"],
        "SC-<nn>.P<n>": ["diy-dev/SKILL.md"],
    }

    def dev_docs(self):
        docs = {"diy-dev/SKILL.md": read(DEV_SKILL_MD)}
        steps = os.path.join(SKILLS, "diy-dev", "steps")
        for name in sorted(n for n in os.listdir(steps) if n.endswith(".md")):
            docs["steps/" + name] = read(os.path.join(steps, name))
        return docs

    # trace: C·3a §6 面 2（design 产物字段 → dev 消费点，逐字段对账）
    def test_dev_consumes_design_page_fields(self):
        docs = self.dev_docs()
        design_block = read(DESIGN_SKILL_MD)
        for field, locators in sorted(self.DEV_CONSUMED.items()):
            with self.subTest(field=field):
                self.assertIn(field, design_block,
                              "设计侧结构/规则段不再声明 %s（dev 读契约悬空）" % field)
                for rel in locators:
                    self.assertIn(field, docs[rel], "%s 未消费 %s" % (rel, field))
        # token 单一源：设计侧 tokens 面 ↔ dev 侧的 audit 红线
        self.assertIn("tokens:", design_block)
        self.assertIn("audit --design", docs["diy-dev/SKILL.md"])
        self.assertIn("diy-design/scripts/design.py", docs["diy-dev/SKILL.md"])

    # trace: C·3a §6 面 2（反向：dev 读的页级键不得越出设计侧声明的页 schema）
    def test_dev_invents_no_page_keys(self):
        declared = set(re.findall(r"^  ([a-z_]+):", read(DESIGN_SKILL_MD), re.M))
        # 设计侧「结构」段的页级键（页记录层：`- id:` 与缩进二级的键）
        pages_block = read(DESIGN_SKILL_MD).split("pages:", 1)[1].split("revisions:", 1)[0]
        page_keys = set(re.findall(r"^\s{2,6}(?:- )?([a-z_]+):", pages_block, re.M))
        self.assertTrue({"status", "prototype", "implementation"} <= page_keys,
                        "设计侧页 schema 的键集取数失败：%s" % sorted(page_keys))
        used = set()
        for rel, body in self.dev_docs().items():
            for pattern in (r"`pages\[\]\.([a-z_]+)`",
                            r"该页 `([a-z_]+)`",
                            r"该页记录（`([a-z_]+)\[\]\.",
                            r"其 `([a-z_]+)`"):
                used |= set(re.findall(pattern, body))
        self.assertTrue({"status", "implementation", "prototype", "states"} <= used,
                        "dev 页级键的取数面不足（扫到 %s）——取数规则已脱钩" % sorted(used))
        self.assertEqual(used - page_keys - declared, set(),
                         "dev 读了设计侧页 schema 之外的键：%s"
                         % sorted(used - page_keys - declared))

    # trace: C·3a §6 面 2（写权窄的字段级证据：写回只动 pages[].status + project.updated）
    def test_writeback_preserves_every_design_owned_field(self):
        path = self.write("design.yaml", design_text(
            page_status="结构稿中", implementation="src/pages/SC-01.P1.html"))
        self.prototype()
        self.write("src/pages/SC-01.P1.html", GOOD_PROTOTYPE)
        before = self.doc("design.yaml")
        rc, data = run_json(DESIGN_PY, ["transition", "--design", path, "--page", "SC-01.P1",
                                        "--to", "待验收", "--json"])
        self.assertEqual(rc, 0, json.dumps(data, ensure_ascii=False))
        after = self.doc("design.yaml")
        before.pop("project")["updated"] = None
        after.pop("project")["updated"] = None
        before["pages"][0].pop("status")
        after["pages"][0].pop("status")
        self.assertEqual(after, before,
                         "写回改动了 dev 声称的窄写面之外的字段（设计侧 schema 被侵蚀）")
        self.assertEqual(sorted(after), sorted(before),
                         "写回新增/删除了顶层键")
        self.assertTrue(os.path.isfile(path + ".prev"), "写回未落 .prev 快照")


# ---------------------------------------------------------------- 面 3

class ScenarioBridgeTests(W7Harness):
    """断言面 3：主线端到端 `prd.yaml` → 场景桥 → 页面树 → 逐页规格。

    桥的流程在 W1 的 `steps/scenario-bridge.md`，它调的命令在 W2——两侧分开才可跑完。
    **与既有测试的分工**：W2 测 `detect` 的开关与 `validate` 的单点报错；本类只跑
    「桥的四步序列」：判前端面 → 落骨架（含预期 FAIL）→ 补逐页规格 → 引擎放行。
    """

    def prd(self, statements):
        features = [{"id": "FG-1", "name": "mini", "requirements": [
            {"id": "F-%d" % i, "statement": text}
            for i, text in enumerate(statements, 1)]}]
        return self.write("prd.yaml", {"project": {"name": "mini", "status": "已定稿"},
                                       "features": features})

    # trace: C·3a §3.4 / §6 面 3（桥第 1 步「只取前端面 FR」——按 FR 逐条判定）
    def test_detect_yields_exactly_the_frontend_frs(self):
        self.prd(["页面以列表展示待办事项", "系统按周期导出 CSV 报表并归档",
                  "用户可在详情页查看订单状态"])
        rc, data = run_json(DESIGN_PY, ["detect", "--project-root", self.root, "--json"])
        self.assertEqual(rc, 0, json.dumps(data, ensure_ascii=False))
        self.assertTrue(data["has_frontend"], data)
        self.assertEqual([hit["fr"] for hit in data["hits"]], ["F-1", "F-3"],
                         "前端面判定未按 FR 逐条收敛（桥的取数源会漂移）")

    # trace: C·3a §6 面 3（桥第 4 步：骨架落盘 → validate 必然 FAIL 且缺的是 states）
    def test_skeleton_fails_validate_for_the_documented_reason(self):
        self.prd(["页面以列表展示待办事项"])
        skeleton = {
            "project": {"name": "mini", "status": "草稿", "created": "2026-01-01",
                        "updated": "2026-01-01"},
            "pages": [{"id": "P-1", "name": "待办列表", "route": "/todos",
                       "states": [], "prototype": "prototypes/P-1.html"}],
            "revisions": [],
        }
        path = self.write("design.yaml", skeleton)
        rc, data = run_json(DESIGN_PY, ["validate", "--design", path, "--json"])
        self.assertEqual(rc, 1, json.dumps(data, ensure_ascii=False))
        wheres = [x["where"] for x in data["violations"]]
        self.assertIn("design.yaml pages[P-1].states", wheres,
                      "骨架自检的预期 FAIL 未落在 states（桥的收尾句失准）：%s" % wheres)

    # trace: C·3a §6 面 3（逐页规格补齐 → 桥的终点是「引擎放行的 design.yaml」；铸号不复用）
    def test_bridge_completes_to_engine_valid_pages(self):
        self.prd(["页面以列表展示待办事项"])
        self.write("design.yaml", design_text(project_status="草稿", page_id="P-1",
                                              extra_pages=("P-3",)))
        self.prototype("P-1")
        self.prototype("P-3")
        rc, data = run_json(DESIGN_PY, ["validate", "--design",
                                        os.path.join(self.out, "design.yaml"), "--json"])
        self.assertEqual(rc, 0, json.dumps(data, ensure_ascii=False))
        # 桥的铸号纪律：P-1 / P-3 并存合法（删页不复用号）
        doc = self.doc("design.yaml")
        self.assertEqual([p["id"] for p in doc["pages"]], ["P-1", "P-3"])
        self.assertIn("P-2 → P-1", read(os.path.join(DESIGN_STEPS, "scenario-bridge.md")))


# ---------------------------------------------------------------- 面 6

class DualSourceZeroOutputTests(W7Harness):
    """断言面 6：双源判定的四情形与「两源皆缺 → 全链路零文件产出」。

    门禁句在 W1、不写盘在 W2——两工位产物合力才可断言。**与既有测试的分工**：W2 的
    `test_no_frontend_prd_skips` 只覆盖主线 SKIP 的零产出；W1 只断言两条门禁句在场。
    本类把门禁句**机械解析**出来对四种夹具逐条判别，并把「零产出」落到文件数上。
    """

    def gate(self, filename):
        """从设计侧主文件解析 `{output_dir}/<file>` 的 `project.status: <值>` 门禁句。"""
        pattern = (r"`\{output_dir\}/%s`\s*的\s*`project\.status:\s*([^`]+)`"
                   % re.escape(filename))
        found = re.findall(pattern, read(DESIGN_SKILL_MD))
        self.assertEqual(len(found), 1,
                         "未从设计侧主文件解析出唯一门禁句：%s（命中 %d 次）"
                         % (filename, len(found)))
        return found[0].strip()

    # trace: C·3a §6 面 6（四情形：两条门禁句对四种夹具的判别 + 分流句）
    def test_four_source_cases_are_discriminating(self):
        self.assertEqual(self.gate("prd.yaml"), "已定稿", "设计侧主线门禁的取值漂移")
        self.assertEqual(self.gate("wds-scenarios.yaml"), "已定稿", "设计侧 WDS 门禁的取值漂移")
        verdict = {}
        for name, status in (("prd.yaml", "已定稿"), ("prd.yaml", "草稿"),
                             ("wds-scenarios.yaml", "已定稿"), ("wds-scenarios.yaml", "草稿")):
            key = "%s/%s" % (name, status)
            path = self.write("case-%s/%s" % (status, name),
                              {"project": {"name": "x", "status": status}})
            with io.open(path, encoding="utf-8") as fh:
                verdict[key] = (self.gate(name) in fh.read())
        self.assertEqual(verdict, {
            "prd.yaml/已定稿": True, "prd.yaml/草稿": False,
            "wds-scenarios.yaml/已定稿": True, "wds-scenarios.yaml/草稿": False,
        }, "双源门禁句不可判别：%s" % verdict)
        # 分流句：两源俱在 → 问用户；两者皆缺 → 停下 + 零产出
        src = read(DESIGN_SKILL_MD)
        both = re.search(r"两源俱在 → ([^；]+)；", src)
        self.assertIsNotNone(both, "缺「两源俱在」的分流句")
        self.assertIn("问用户", both.group(1), "两源俱在未交出决定权：%s" % both.group(1))
        none = re.search(r"两者都缺[^；]*；", src)
        self.assertIsNotNone(none, "缺「两者都缺」的分流句")
        self.assertIn("零产出", src.split("两者都缺", 1)[1][:120],
                      "设计侧的缺源分支未带零产出声明")

    # trace: C·3a §6 面 6（零产出落到文件数：两源皆缺时全链路零文件）
    def test_zero_sources_zero_output(self):
        rc, data = run_json(DESIGN_PY, ["detect", "--project-root", self.root, "--json"])
        self.assertEqual(rc, 1, json.dumps(data, ensure_ascii=False))
        self.assertEqual([x["code"] for x in data["violations"]], ["MISSING_FILE"])
        rc2, data2 = run_json(DESIGN_PY, ["validate", "--design",
                                          os.path.join(self.out, "design.yaml"), "--json"])
        self.assertEqual(rc2, 1, json.dumps(data2, ensure_ascii=False))
        self.assertEqual([x["code"] for x in data2["violations"]], ["MISSING_FILE"])
        self.assertEqual(self.files_under(self.out), [],
                         "缺源路径写盘了：%s" % self.files_under(self.out))
        self.assertFalse(os.path.isdir(os.path.join(self.out, "prototypes")),
                         "缺源路径建了 prototype 目录")


# ---------------------------------------------------------------- 面 7

class MotherTextMatrixTests(unittest.TestCase):
    """断言面 7：§2.8 母本在场——改造后四技能主文件的锚串（矩阵式一次性核定）。

    四份主文件分属 W1 / W3 / W4 / W5（各改自己那一份），单工位测试各只看自己一份；
    §4 的适用面还取决于各技能是否长出 `steps/`——只有把四份放在一起才可断言。
    **与既有测试的分工**：各技能自测断言「自己那份含锚串」；本类断言**矩阵**：
    四技能 × 四类锚串的在场/适用面一次性相等（含 `diy-review` 无 `steps/` 这一
    负向单元格），并与 `test_suite_texts.py` 的台账同源（常量直接导入，防第二份口径）。
    """

    @classmethod
    def setUpClass(cls):
        # 同目录测试模块：常量即母本定稿（不复制第二份口径）
        sys.path.insert(0, HERE)
        import test_suite_texts as ledger       # noqa: E402
        cls.ledger = ledger

    def skill_body(self, skill):
        return read(os.path.join(SKILLS, skill, "SKILL.md"))

    def has_steps(self, skill):
        return os.path.isdir(os.path.join(SKILLS, skill, "steps"))

    # trace: C·3a §2.8 / §6 面 7（四技能 × 四类锚串的适用面矩阵）
    def test_anchor_applicability_matrix(self):
        lg = self.ledger
        anchors = {"§1": lg.INSTANCE_ZH, "§2": lg.DISCIPLINE_ZH,
                   "§3": lg.ANCHOR_RESOLVE_KEYS, "§5": lg.ANCHOR_RENDER_SILENT,
                   "§6": lg.ANCHOR_PRECISE}
        expected = {}
        for skill in MOTHER_SKILLS:
            steps = self.has_steps(skill)
            row = {label: text in self.skill_body(skill)
                   for label, text in anchors.items()}
            row["§4"] = lg.ANCHOR_READ_DISCIPLINE in self.skill_body(skill)
            row["steps/"] = steps
            expected[skill] = row
        for skill, row in expected.items():
            with self.subTest(skill=skill):
                for label in ("§1", "§2", "§3", "§5", "§6"):
                    self.assertTrue(row[label], "%s 主文件缺母本 %s 锚串" % (skill, label))
                self.assertEqual(row["§4"], row["steps/"],
                                 "%s 的 §4 锚串在场性与 steps/ 实况不符（适用面=有 steps/）"
                                 % skill)
        # 本批拆出 steps/ 的工位（非 B7 新建技能）必须已在 LANDED 台账登记
        steppers = set(lg._steppers())
        for skill in MOTHER_SKILLS:
            short = skill[len("diy-"):]
            if not self.has_steps(skill) or short in lg.NEW_SKILLS:
                continue
            with self.subTest(skill=skill):
                self.assertIn(short, steppers, "%s 有 steps/ 却不在 _steppers() 适用面" % skill)
                self.assertIn(short, lg.LANDED_READ_DISCIPLINE,
                              "%s 长出 steps/ 并补了 §4 锚串，但未登记 LANDED_READ_DISCIPLINE"
                              % skill)


# ---------------------------------------------------------------- 面 8

class WdsPageChainTests(W7Harness):
    """断言面 8：WDS 全链贯通——一页从 `未开始` 走到 `待验收`。

    W1 的工作流（结构稿段）+ W2 的 `transition` + W3 的实现与自验 + W4 的审查判定，
    四工位产物合一才可断言。**与既有测试的分工**：各工位各测自己那条边的单点回执；
    本类测**链**——每步写回后 `validate` 仍绿、设计侧字段跨两次写回零改动、审查动作
    零写盘、终点仍是 `待验收`（批准不代做）。
    """

    def setUp(self):
        super().setUp()
        self.write("wds-scenarios.yaml", upstream_scenarios_doc())
        self.write("wds-trigger.yaml", {
            "project": {"name": "wds-mini", "status": "已定稿"},
            "personas": [{"id": "TG-1", "name": "游客"}],
        })

    def steps_validate(self):
        rc, data = run_json(DESIGN_PY, ["validate", "--design",
                                        os.path.join(self.out, "design.yaml"), "--json"])
        self.assertEqual(rc, 0, json.dumps(data, ensure_ascii=False))
        return data

    # trace: C·3a §9 #14 / §6 面 8（未开始 → 结构稿中 → 待验收；各步后 validate 仍绿）
    def test_page_walks_from_not_started_to_pending_acceptance(self):
        # 起点：旧稿形态（该页无 status 键 = 未开始），结构稿与实现稿落位
        path = self.design(with_status_key=False, implementation="src/pages/SC-01.P1.html")
        self.prototype()
        self.write("src/pages/SC-01.P1.js", IMPL_JS)
        self.write("src/pages/SC-01.P1.html", GOOD_PROTOTYPE)
        upstream_before = read(os.path.join(self.out, "wds-scenarios.yaml"))

        # 第 1 步（W1 结构稿段）：推到 结构稿中
        rc, data = run_json(DESIGN_PY, ["transition", "--design", path, "--page", "SC-01.P1",
                                        "--to", "结构稿中", "--json"])
        self.assertEqual(rc, 0, json.dumps(data, ensure_ascii=False))
        self.assertEqual(data["to"], "结构稿中")
        self.steps_validate()
        first_prev = read(path + ".prev")

        # 第 2 步（W3 实现环）：dev 的 trace 形态 + token 闸 → 推到 待验收
        impl_js = read(os.path.join(self.out, "src/pages/SC-01.P1.js"))
        trace_shape = re.search(r"`# trace: (SC-\S+ \S+)`", read(DEV_SKILL_MD))
        self.assertIsNotNone(trace_shape, "dev 主文件不再给出 WDS 的 trace 形态")
        self.assertIn(trace_shape.group(1), impl_js.splitlines()[0],
                      "实现稿的 trace 行不是 dev 教的形态：%s" % trace_shape.group(1))
        self.assertTrue(impl_js.splitlines()[0].startswith("// trace:"),
                        "C 族的 trace 前缀应为 // trace:（dev 规则 4）")
        rc, data = run_json(DESIGN_PY, ["audit", "--design", path, "--src",
                                        os.path.join(self.out, "src"), "--json"])
        self.assertEqual(rc, 0, json.dumps(data, ensure_ascii=False))
        rc, data = run_json(DESIGN_PY, ["transition", "--design", path, "--page", "SC-01.P1",
                                        "--to", "待验收", "--json"])
        self.assertEqual(rc, 0, json.dumps(data, ensure_ascii=False))
        self.assertEqual((data["from"], data["to"]), ("结构稿中", "待验收"))
        self.steps_validate()

        # 第 3 步（W4 审查判定）：独立复验 = 自己跑判据（check），通过后页仍是 待验收
        snapshot = read(path)
        rc, data = run_json(DESIGN_PY, ["check", "--design", path, "--json"])
        self.assertEqual(rc, 0, json.dumps(data, ensure_ascii=False))
        self.assertEqual(read(path), snapshot, "审查动作写盘了（判决不得改状态）")
        self.assertEqual(self.doc("design.yaml")["pages"][0]["status"], "待验收",
                         "审查通过后页必须仍是 待验收（批准是用户动作，不代做）")
        # 链的终态：两次写回都有留痕，且未发生非破坏性边之外的额外改写
        self.assertNotIn("status", yaml.safe_load(first_prev)["pages"][0],
                         "起点应是缺 status 键的旧稿形态")
        self.assertEqual(yaml.safe_load(read(path + ".prev"))["pages"][0]["status"],
                         "结构稿中", "第二次写回前的快照不持有中间态")
        self.assertNotIn("revisions", self.doc("design.yaml"),
                         "非破坏性边被追加了 revisions")
        # 上游产物在引擎面零改动（design_status 的推进是会话内编辑，另有其纪律）
        self.assertEqual(read(os.path.join(self.out, "wds-scenarios.yaml")), upstream_before,
                         "本链的引擎命令改动了上游产物")


if __name__ == "__main__":
    unittest.main()
