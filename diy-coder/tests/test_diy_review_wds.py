# -*- coding: utf-8 -*-
"""diy-review WDS 线审查路径 + 两透镜契约测试（C·3a 段2·W4）。

覆盖任务书 §5.6 交付表：
  1 WDS 模式判定（`## 激活时`，显式可机械核）· 2 审查目标 = `pages[].status: 待验收`
  · 3 独立复验（`states[].signals`，不采信 `diy-dev` 自述）· 4 判决语义（通过保持
  `待验收`、绝不代用户批准；失败走回修边）· 4b WDS 线 findings 路由落点表（四类逐条）
  · 5 写权（一律经 `transition`、不直改 YAML、不新增 schema 键）· 6 回执引用句
  （`one-off-*` 码族仍成立——实跑对账）· 7 两透镜三项接口事（映射表 / 格式归一 / HALT 对齐）。
外加 §9 #16 的判决语义证据与**引擎面实跑对账**：文档教的状态边与 L4 三维 token 码，
在引擎里必须真存在（「文档教了引擎会拒的值」是同库既有盲区，见 test_suite_texts 的
EngineContractGuardTests）。

与既有 `test_review_contract.py`（主线保真 + 93 行预算）不重复：本文件只断言 WDS /
两透镜的新增面，外加 §9 #1 的 `≤120` 控制线。
"""
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_REVIEW = os.path.join(HERE, "..", "skills", "diy-review", "SKILL.md")
DESIGN_PY = os.path.join(HERE, "..", "skills", "diy-design", "scripts", "design.py")
DIYC_PY = os.path.join(HERE, "..", "skills", "diy-tools", "scripts", "diyc.py")
NL = chr(10)

WDS_LINE_BUDGET = 120           # §2.1 / §9 #1：diy-review 放宽后的软控制线（现状 83 + 20% 曾为 100）
WDS_PAGE = "SC-01.P1"           # 上游 diy-wds-scenarios 定死的页 ID 形态（议事 7 订正：WDS 线不铸 P-*）

# L4 设计系统三维（§4.6 有意收严）：实现稿照抄字面值即违规——L4 必须纳入，否则与 check 分叉
DS_TOKEN_CODES = ("ds-token-color", "ds-token-font-size", "ds-token-spacing")

GOOD_PROTOTYPE = NL.join([
    "<!DOCTYPE html>",
    '<html lang="zh-CN">',
    "<head>",
    '<meta charset="utf-8">',
    "<title>首页</title>",
    "<style>",
    "  body { color: var(--color-text); font-size: var(--font-md); padding: var(--space-4); }",
    "</style>",
    "</head>",
    "<body>",
    "<h1>首页</h1>",
    '<img src="hero.png" alt="主视觉">',
    '<a href="/todos">待办</a>',
    "</body>",
    "</html>",
])

# 字面值实现稿：三维各触发一条（色值 / 字号 / 间距都不走 token）
LITERAL_PROTOTYPE = GOOD_PROTOTYPE.replace(
    "color: var(--color-text); font-size: var(--font-md); padding: var(--space-4);",
    "color: #123456; font-size: 21px; padding: 13px;")

# L4 (c) 的 token 单一源审计面：字面色值 + 字面字号 = 两条 one-off-*
ONE_OFF_IMPL = NL.join([
    "<!DOCTYPE html>",
    '<html lang="zh-CN">',
    "<head><meta charset=\"utf-8\"><title>首页</title></head>",
    '<body style="color: #ff0000; font-size: 17px;"><h1>首页</h1></body>',
    "</html>",
])


def read(path):
    with io.open(path, encoding="utf-8") as fh:
        return fh.read()


def run(script, args):
    return subprocess.run([sys.executable, script] + args,
                          capture_output=True, text=True, encoding="utf-8")


def design_text(page_status="待验收", with_status_key=True, page_id=WDS_PAGE):
    """合成 WDS 线 design.yaml：一页四态齐、原型在场——页级门可过。"""
    lines = [
        "project:",
        "  name: wds-mini",
        "  status: 已定稿",
        "  created: 2026-01-01",
        "  updated: 2026-01-01",
        "direction: 瑞士编辑风——大字阶对比、留白节奏、单强调色",
        "frontend_framework: html",
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
        "  prototype: prototypes/home.html",
    ]
    if with_status_key:
        lines.append("  status: %s" % page_status)
    lines += [
        "  states:",
        "  - name: 悬停",
        "    signals: [图标, 动效]",
        "  - name: 空态",
        "    signals: [文字]",
        "  - name: 加载中",
        "    signals: [图标, 动效]",
        "  - name: 错误",
        "    signals: [图标, 文字]",
    ]
    return NL.join(lines) + NL


class WdsReviewHarness(unittest.TestCase):
    """临时项目根 + 引擎子进程（验真回执，不验函数返回值）。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = os.path.join(self.tmp.name, "diy-output")
        os.makedirs(os.path.join(self.out, "prototypes"))

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, rel, content):
        path = os.path.join(self.out, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with io.open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
        return path

    def design(self, **kw):
        return self.write("design.yaml", design_text(**kw))


# ------------------------------------------------------- §5.6 #1–#5（文本契约）

class WdsBranchTextTests(unittest.TestCase):
    """WDS 分支的判定 / 目标 / 复验 / 判决四件（§5.6 #1–#4），逐条锚在 SKILL.md 上。"""

    @classmethod
    def setUpClass(cls):
        cls.raw = read(SKILL_REVIEW)
        cls.activation = cls.raw.split("## 激活时", 1)[1].split("## 工作流", 1)[0]
        cls.workflow = cls.raw.split("## 工作流", 1)[1].split("## 结构", 1)[0]

    # trace: §5.6 #1（WDS 模式判定句须显式、可机械核）
    def test_activation_declares_wds_branch(self):
        self.assertIn("WDS 线判定", self.activation, "激活时缺 WDS 分支判定")
        self.assertIn("`{output_dir}/design.yaml` 在场", self.activation,
                      "判定缺第一个合取项：design.yaml 在场")
        self.assertIn("**无主线任务上下文**", self.activation,
                      "判定缺第二个合取项：无主线任务上下文")
        self.assertIn("WDS 门 = `design.yaml` 的 `project.status: 已定稿`", self.activation,
                      "WDS 门未经单一判据（§5.1 同口径：无「或」）")
        self.assertIn("主线优先", self.activation, "两线皆在场时未定优先序")

    # trace: 保真面（§2.2）——WDS 分支不得吃掉主线硬门
    def test_mainline_gate_survives(self):
        self.assertIn("`{output_dir}/sprint.yaml` 的 `project.status: 已定稿`", self.activation,
                      "主线 sprint.yaml 硬门被改动")
        self.assertIn("`status: 待审查`", self.activation, "主线目标任务门被改动")
        self.assertIn("`已阻塞` 永远拒绝", self.activation, "主线拒绝态被改动")

    # trace: §5.6 #2（读 pages[].status 定位，不另立词表）
    def test_target_is_pending_acceptance_pages(self):
        self.assertIn("`pages[].status: 待验收`", self.workflow, "审查目标未绑 待验收 页")
        self.assertIn("不另立词表", self.workflow, "未声明词表从 diy-design 接")
        self.assertIn("`status` 键缺失即 `未开始`", self.workflow,
                      "旧稿兼容（键缺失 = 未开始）未写明")

    # trace: §5.6 回报必答②（零页可审的行为）
    def test_zero_auditable_page_is_zero_output(self):
        self.assertIn("零页可审", self.workflow, "未定义零页可审行为")
        self.assertIn("不报「通过」", self.workflow, "零页可审仍可能报通过")

    # trace: §5.6 #3（独立复验：判据同源、不采信 diy-dev 自述）
    def test_independent_reverification(self):
        self.assertIn("`states[].signals`", self.workflow, "复验判据未绑 states[].signals")
        self.assertIn("不采信 `diy-dev` 的自述", self.workflow, "未切断对 diy-dev 自述的采信")

    # trace: §5.6 #4 / §9 #16（判决语义：通过保持待验收，批准归用户）
    def test_verdict_never_approves_for_user(self):
        self.assertIn("页**保持 `待验收`**", self.workflow, "通过后未保持 待验收")
        self.assertIn("可呈用户批准", self.workflow, "通过未产出「可呈用户批准」结论")
        self.assertIn("**绝不代用户批准**", self.workflow, "缺不代用户批准的声明")
        self.assertNotIn("--to 已批准", self.raw,
                         "文本教了 `待验收 → 已批准` 这条用户边（审查者代批准）")

    # trace: §5.6 #4（失败 → 回修边，经 transition）
    def test_failure_routes_back_to_structure_draft(self):
        self.assertIn("--to 结构稿中", self.workflow, "失败未走回修边")
        self.assertIn("--to 结构稿中 --json", self.workflow, "回修边未给完整命令面")

    # trace: §5.6 #5（写权：一律经 transition、不直改 YAML、不新增 schema 键）
    def test_write_power_is_transition_only(self):
        self.assertIn("**一律经 `transition`**", self.workflow, "状态写权未收口到 transition")
        self.assertIn("不直改 YAML", self.workflow, "未禁直改 YAML")
        self.assertIn("**不新增 schema 键**", self.workflow, "未禁新增 schema 键")

    # trace: §4.6 / §9 #1 转交口径（L4 必须纳入设计系统三维，否则与 check 分叉）
    def test_l4_includes_design_system_dimensions(self):
        l4 = self.workflow.split("- **L4 设计采用", 1)[1].split(NL + NL, 1)[0]
        for code in DS_TOKEN_CODES:
            self.assertIn(code, l4, "L4 未纳入设计系统维度：%s" % code)
        self.assertIn("按 code 点名、不写维度计数", l4, "回执引用未按 code 点名")

    # trace: §5.6 #6（回执键同步：引用的是码族，不是键名）
    def test_receipt_reference_uses_code_family(self):
        self.assertIn("one-off-*", self.raw, "L4 的 audit 引用句丢了码族")

    # trace: §9 #1（软控制线 ≤120；现状 83）
    def test_line_budget(self):
        self.assertLessEqual(len(self.raw.splitlines()), WDS_LINE_BUDGET,
                             "主文件超出 diy-review 控制线 %d 行" % WDS_LINE_BUDGET)


# ------------------------------------------------- §5.6 #4b（路由落点表）

ROUTE_ROWS = ("意图缺口", "规格缺陷", "小修", "后置")
WDS_LANDING = {
    "意图缺口": "diy-wds-scenarios",
    "规格缺陷": "diy-design",
    "小修": "diy-dev",
    "后置": "不写 `design.yaml`",
}


def routing_rows(raw):
    """规则第 4 条路由表的 {路由: [单元格…]}（表首列 = 反引号包的路由名）。"""
    rows = {}
    for line in raw.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells and cells[0].strip("`") in ROUTE_ROWS:
            rows[cells[0].strip("`")] = cells
    return rows


class WdsRoutingLandingTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.raw = read(SKILL_REVIEW)

    # trace: §5.6 #4b（四类在 WDS 线的落点——主线处置列全绑 sprint/stories/test-plan）
    def test_routing_table_has_wds_landing_column(self):
        self.assertIn("WDS 线落点", self.raw, "路由表缺 WDS 落点列")
        rows = routing_rows(self.raw)
        self.assertEqual(set(rows), set(ROUTE_ROWS), "路由表四类不齐：%s" % sorted(rows))
        for route in ROUTE_ROWS:
            cells = rows[route]
            self.assertEqual(len(cells), 4, "路由 %s 的行仍是三列（缺 WDS 落点）" % route)
            self.assertTrue(cells[3], "路由 %s 的 WDS 落点为空" % route)
            self.assertIn(WDS_LANDING[route], cells[3],
                          "路由 %s 的 WDS 落点未指向 %s" % (route, WDS_LANDING[route]))

    # trace: §5.6 #4b（WDS 线无主线三产物——落点表存在的理由）
    def test_wds_line_has_no_mainline_artifacts(self):
        self.assertIn("WDS 线没有 `sprint.yaml` / `stories.yaml` / `test-plan.yaml` 三个落点",
                      self.raw, "未点明 WDS 线缺主线落点的理由")

    # trace: §2.2 保真（主线四类处置列一条不改）
    def test_mainline_dispositions_unchanged(self):
        rows = routing_rows(self.raw)
        self.assertIn("打回 diy-dev", rows["意图缺口"][2])
        self.assertIn("改 stories.yaml / test-plan.yaml，不改代码", rows["规格缺陷"][2])
        self.assertIn("打回 diy-dev（一行范围）", rows["小修"][2])
        self.assertIn("`review.findings[]`", rows["后置"][2])
        self.assertIn("`deferred-actions.yaml`", rows["后置"][2])


# ------------------------------------------------------- §5.6 #7（两透镜）

class LensTests(unittest.TestCase):
    """两透镜 + 三项接口事（映射表 / 格式归一 / HALT 对齐），各有实做落点。"""

    @classmethod
    def setUpClass(cls):
        cls.raw = read(SKILL_REVIEW)

    # trace: §5.6 #7①（映射表：两透镜 ↔ 既有 L1–L4）
    def test_lens_layer_mapping(self):
        self.assertIn("`批判式`（attitude-driven", self.raw, "缺批判式透镜（含方法驱动力）")
        self.assertIn("`边界穷举`（method-driven", self.raw, "缺边界穷举透镜")
        self.assertIn("L1 / L3 补强", self.raw, "批判式未映射到 L1/L3")
        self.assertIn("**L2 的机械化路径枚举**", self.raw, "边界穷举未映射到 L2")

    # trace: §5.6 #7③（HALT 语义对齐：零 findings 即 HALT / 空数组合法）
    def test_lens_halt_semantics(self):
        self.assertIn("**零 findings 即 HALT**", self.raw, "批判式的零 findings HALT 未落")
        self.assertIn("**空数组合法**", self.raw, "边界穷举的空数组合法性未落")

    # trace: §5.6 #7②（格式归一：落既有形状 + 四类路由，不新增 schema 键）
    def test_lens_findings_reuse_existing_shape(self):
        self.assertIn("`review.findings{layer,route,note}`", self.raw,
                      "透镜 findings 未归一到既有形状")
        self.assertIn("**不新增 schema 键**", self.raw, "透镜未禁新增 schema 键")
        self.assertIn("`layer` 只取既有四值", self.raw, "layer 未收口到既有枚举")


# ------------------------------------------------------- 引擎面实跑（§9 #16 / #19）

LEGAL_EDGES_BLOCK_RE = re.compile(r"LEGAL_EDGES\s*=\s*frozenset\(\{(.*?)\}\)", re.S)
EDGE_PAIR_RE = re.compile(r'\("([^"]+)"\s*,\s*"([^"]+)"\)')
TRANSITION_TO_RE = re.compile(r"design\.py\"\s+transition[^\n]*?--to\s+([^\s\"`]+)")


def legal_edges():
    """design.py 的 LEGAL_EDGES——读源码，不复制常量（防两处漂移）。"""
    block = LEGAL_EDGES_BLOCK_RE.search(read(DESIGN_PY))
    assert block, "未能从 design.py 取到 LEGAL_EDGES"
    return set(EDGE_PAIR_RE.findall(block.group(1)))


class EngineContractRunTests(WdsReviewHarness):

    # trace: EngineContractGuardTests 同型盲区——文档不得教引擎会拒的状态边
    def test_taught_design_edges_are_engine_legal(self):
        targets = {dst for (_src, dst) in legal_edges()}
        taught = set(TRANSITION_TO_RE.findall(read(SKILL_REVIEW)))
        self.assertTrue(taught, "守卫空转：未从 diy-review 扫到 design.py transition 的 --to 值")
        self.assertEqual(taught - targets, set(),
                         "diy-review 教了 design.py 会拒的状态：%s" % sorted(taught - targets))

    # trace: §5.6 #4（失败回修边实跑：待验收 → 结构稿中）
    def test_repair_edge_runs_and_reports_next_hint(self):
        dpath = self.design(page_status="待验收")
        self.write("prototypes/home.html", GOOD_PROTOTYPE)
        r = run(DESIGN_PY, ["transition", "--design", dpath, "--page", WDS_PAGE,
                            "--to", "结构稿中", "--json"])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(r.stdout.rstrip(NL).count(NL), 0, "回执不是单行 JSON")
        data = json.loads(r.stdout)
        self.assertEqual((data["ok"], data["command"]), (True, "transition"))
        self.assertEqual((data["page"], data["from"], data["to"]),
                         (WDS_PAGE, "待验收", "结构稿中"))
        self.assertTrue(data["next_hint"], "回修边未给 next_hint")
        after = read(dpath)
        self.assertIn("status: 结构稿中", after, "页状态未落盘")

    # trace: §5.6 #2（旧稿兼容：`status` 键缺失 = `未开始`，不是待审页）
    def test_missing_status_key_reads_as_not_started(self):
        dpath = self.design(with_status_key=False)
        self.write("prototypes/home.html", GOOD_PROTOTYPE)
        r = run(DESIGN_PY, ["transition", "--design", dpath, "--page", WDS_PAGE,
                            "--to", "结构稿中", "--json"])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(json.loads(r.stdout)["from"], "未开始", "键缺失未按 未开始 起算")
        dpath = self.design(with_status_key=False)
        r = run(DESIGN_PY, ["transition", "--design", dpath, "--page", WDS_PAGE,
                            "--to", "已批准", "--json"])
        self.assertEqual(r.returncode, 1, "未开始的页竟可直接批准")
        self.assertEqual([x["code"] for x in json.loads(r.stdout)["violations"]],
                         ["ILLEGAL_TRANSITION"], "非待审页的状态边应被引擎拒绝")

    # trace: §5.6 回报必答①（同一 design.yaml：主线入口拒绝）
    def test_mainline_entry_rejects_without_sprint_yaml(self):
        self.design(page_status="待验收")
        r = run(DIYC_PY, ["check", "--type", "review", "--story", "S-1",
                          "--project-root", self.tmp.name, "--json"])
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertFalse(data["ok"])
        self.assertIn("MISSING_FILE", {x["code"] for x in data["violations"]},
                      "主线入口未以文件缺失拒绝")

    # trace: §5.6 回报必答①（同一 design.yaml：WDS 入口接受——无 sprint.yaml 也能走）
    def test_wds_entry_accepts_without_sprint_yaml(self):
        dpath = self.design(page_status="待验收")
        self.write("prototypes/home.html", GOOD_PROTOTYPE)
        self.assertFalse(os.path.isfile(os.path.join(self.out, "sprint.yaml")))
        r = run(DESIGN_PY, ["check", "--design", dpath, "--json"])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(json.loads(r.stdout)["ok"], "WDS 入口在无 sprint.yaml 时未被接受")

    # trace: §9 #1 转交口径（L4 三维：check 的三个 ds-token-* 必须真在引擎里）
    def test_design_system_dimension_codes_fire(self):
        dpath = self.design(page_status="结构稿中")
        self.write("prototypes/home.html", LITERAL_PROTOTYPE)
        r = run(DESIGN_PY, ["check", "--design", dpath, "--json"])
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        codes = {x["code"] for x in json.loads(r.stdout)["violations"]}
        for code in DS_TOKEN_CODES:
            self.assertIn(code, codes, "设计系统维度未在 check 里报出：%s" % code)

    # trace: §5.6 #6（L4 (c) 引用的码族在回执归一后仍成立）
    def test_l4_one_off_code_family_is_live(self):
        dpath = self.design(page_status="结构稿中")
        impl = self.write("impl/index.html", ONE_OFF_IMPL)
        r = run(DESIGN_PY, ["audit", "--design", dpath, "--src", impl, "--json"])
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        codes = {x["code"] for x in json.loads(r.stdout)["violations"]}
        self.assertTrue(codes, "audit 未报出任何违规")
        self.assertEqual([c for c in codes if not c.startswith("one-off-")], [],
                         "audit 回执的 code 不再是 one-off-* 码族：%s" % sorted(codes))


if __name__ == "__main__":
    unittest.main()
