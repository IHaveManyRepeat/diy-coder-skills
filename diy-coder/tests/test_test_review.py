# -*- coding: utf-8 -*-
"""diy-test-review 确定性引擎测试（B3 批 W4，任务书 §6 + V 能力补项 §1.4）。

覆盖（任务书 §6 测试清单 ≥7 条，此处 33 条）：
- scan 无测试文件拒绝（门禁 + 零产出）
- scan 检出机械项 + convention baseline 采样（7 key：5 机械键出 {adopted,status}、
  bdd_naming / assertion_style 标 judged_by: llm）
- scan excluded 三值（unsupported-format / generated / out-of-scope）
- scan 空 / 极简测试文件处置（R-3：空 → excluded 不评分 + "No tests found"；
  零断言 → warning "No meaningful tests"）
- scan pact 附加上报（R-4：mergeConfig / extends → L4 pact-config-unverifiable +
  // tea:pact-ffi-safe 免报；单 it() 多 addInteraction() → warning）
- score 账本纯函数（已知 findings → 已知分；convention 降档；按 file:location:row 去重）
- score 分档与 recommendation 推导（参数化；数值口径照源）
- score bonus 数值域 + 与规则命中的矛盾复核
- criteria.yaml 完整性（35 行留档 / 32 有效 / 机械集 / 维度映射 / bonus_guard /
  convention 行的 convention_key 映射）
- walkthrough 四类缺口（合成 AC/代码/TC 三源）
- walkthrough 缺源降级（stories 缺 / 零 trace 标记护栏）
- check 账本不自洽违例
- check coverage_gaps 形态违例 + walkthrough 不自洽
- check 禁用行（disabled）不得成条目
- check convention 引用复核（R-2：class ↔ convention_baseline.keys.<key>.status）
- check 空文件不得计入评审集（R-3）
- check recommendations 上限（R-1：Top 10）
- check --final 附加义务（零 [假设] / excluded 理由 / scope 非空）
- check 合法产物 exit 0
- SKILL.md 契约冒烟（母本 §1 中文定稿逐字 + 终门句指向本技能引擎）

夹具全部落 tempfile 自建；不读写本仓库真实 diy-output、不写真实项目目录、不依赖本机 git。
运行：cd diy-coder && python -m unittest discover -s tests -p "test_test_review.py" -v
"""
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.join(HERE, "..", "skills", "diy-test-review")
ENGINE = os.path.join(SKILL_DIR, "scripts", "test_review.py")
SKILL_MD = os.path.join(SKILL_DIR, "SKILL.md")
CRITERIA = os.path.join(SKILL_DIR, "criteria.yaml")
NL = chr(10)

# 母本 §1 中文定稿（suite-texts.md，逐字）
INSTANCE_ZH = ("实例解析（FR-4.5/D-9）由工具脚本执行：运行 "
               "`python \"{project-root}/.claude/skills/diy-tools/scripts/diyc.py\" "
               "resolve [--instance <name>] --json`，把回执里的 `output_dir` "
               "当作本次运行唯一的读写根目录。")
# 母本 §2 中文定稿（写作纪律块）
DISCIPLINE_ZH = ("- **写作纪律。** 主字段 = 大白话主句；数字/枚举内联；"
                 "机器语法（命令/旗标/路径）进括号；机器锚点逐字保留"
                 "（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 "
                 "`diy-design` 的 detect 启发式。schema 若定义 `plain`："
                 "一行写清该条目为什么存在，绝不写是什么（转述会漂移）；"
                 "只写难懂的条目。若定义 `detail`：过程叙述——结论留在主字段。")
# 母本 §3 / §4 / §5 锚串（test_suite_texts.py 同口径）
ANCHOR_RESOLVE_KEYS = ("解析 `project.communication_language` / "
                       "`project.document_output_language` / `paths.output_dir`")
ANCHOR_READ_DISCIPLINE = ("读取纪律：预载预算 = 本文件、上述配置与回执、`steps/` 下当前那一个文件"
                          "——绝不批量预载；执行期读取以每个步骤开头的 `Read (input)` 行为唯一权威，"
                          "**主文件不列举封闭清单**。")
ANCHOR_RENDER_SILENT = "渲染是静默旁路——只写调用命令"


def load_engine():
    """按文件路径加载引擎模块（单元级纯函数测试用，不走子进程）。

    加载期间关掉字节码缓存——否则会在技能目录里留下 `__pycache__`（install.py
    copytree 会把它一起分发出去）。
    """
    spec = importlib.util.spec_from_file_location("test_review_engine", ENGINE)
    module = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


def run_engine(args):
    return subprocess.run([sys.executable, ENGINE] + args,
                          capture_output=True, text=True, encoding="utf-8")


STORIES_YAML = NL.join([
    "project:",
    "  name: mini",
    "  status: 已定稿",
    "  created: '2026-09-15'",
    "  updated: '2026-09-15'",
    "stories:",
    "- id: S-1",
    "  title: 结算",
    "  status: 进行中",
    "  acceptance_criteria:",
    "  - id: AC-1.1",
    "    given: 夹具",
    "    when: 夹具",
    "    then: 夹具",
    "    refs: []",
    "  - id: AC-1.2",
    "    given: 夹具",
    "    when: 夹具",
    "    then: 夹具",
    "    refs: []",
    "  - id: AC-1.3",
    "    given: 夹具",
    "    when: 夹具",
    "    then: 夹具",
    "    refs: []",
]) + NL

TEST_PLAN_YAML = NL.join([
    "project:",
    "  name: mini",
    "  status: 已定稿",
    "  created: '2026-09-15'",
    "  updated: '2026-09-15'",
    "test_cases:",
    "- id: TC-1.2.1",
    "  title: 已绑定但未跑",
    "  ac: AC-1.2",
    "  type: 单元",
    "  priority: P1",
    "  technique: 边界",
    "  kill_target: off-by-one",
    "  status: 待办",
    "  steps:",
    "  - 断言",
    "- id: TC-1.9.1",
    "  title: 悬空 AC 绑定",
    "  ac: AC-9.9",
    "  type: 单元",
    "  priority: P1",
    "  technique: 边界",
    "  kill_target: 悬空引用",
    "  status: 待办",
    "  steps:",
    "  - 断言",
    "static_checks: []",
    "coverage_gaps: []",
]) + NL

SRC_WITH_TRACE = NL.join([
    "# -*- coding: utf-8 -*-",
    "def settle():",
    "    # trace: S-1 AC-1.2 TC-1.2.1",
    "    return 1",
]) + NL

REVIEW_YAML = NL.join([
    "project:",
    "  name: mini",
    "  created: '2026-09-15'",
    "  updated: '2026-09-15'",
    "reviews:",
    "- id: RV-001",
    "  date: '2026-09-15'",
    "  status: 已定稿",
    "  scope:",
    "    paths:",
    "    - tests/api.spec.ts",
    "    files_reviewed: 1",
    "    excluded: []",
    "  convention_baseline:",
    "    corpus_size: 5",
    "    sampled: 5",
    "    keys:",
    "      priority_markers: {adopted: 3, status: 已确立}",
    "      test_ids: {adopted: 1, status: 新现}",
    "      bdd_naming: {adopted: 2, status: 新现}",
    "      network_first: {adopted: 0, status: 缺失}",
    "      data_factories: {adopted: 0, status: 缺失}",
    "      fixtures: {adopted: 1, status: 新现}",
    "      assertion_style: {adopted: 2, status: 新现}",
    "  findings:",
    "  - row: L2",
    "    severity: LOW",
    "    file: tests/api.spec.ts",
    "    line: 12",
    "    note: 无优先级标记",
    "    basis: convention",
    "    class: 已确立",
    "  score:",
    "    deductions: {critical: 0, high: 0, medium: 0, low: 1, total: 1}",
    "    bonus: {applied: [], total: 0}",
    "    score: 99",
    "    grade: A",
    "    recommendation: 有保留批准",
    "  coverage_gaps:",
    "  - {kind: 无实现, ref: AC-1.1, note: 无实现引用, route: diy-dev}",
    "  walkthrough: {status: 部分覆盖, note: test-plan.yaml 未定稿：②③④类跳过}",
    "  dimensions: {determinism: 100, isolation: 100, maintainability: 100, performance: 100}",
    "  recommendations:",
    "  - 给用例补优先级标记",
    "  open_questions: []",
    "revisions: []",
]) + NL


class EngineCase(unittest.TestCase):
    """tmp 项目根 + diy-output 目录的公共夹具。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="treview-")
        self.root = self.tmp.name
        self.out = os.path.join(self.root, "diy-output")
        os.makedirs(self.out, exist_ok=True)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, rel, content):
        path = os.path.join(self.root, rel)
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with io.open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def write_findings(self, data):
        return self.write("diy-output/test-review-findings.json",
                          json.dumps(data, ensure_ascii=False))

    def scan(self, *extra):
        return run_engine(["scan", "--project-root", self.root,
                           "--output-dir", self.out, "--json"] + list(extra))

    def score(self, *extra):
        return run_engine(["score", "--project-root", self.root,
                           "--output-dir", self.out, "--json"] + list(extra))

    def walkthrough(self, *extra):
        return run_engine(["walkthrough", "--project-root", self.root,
                           "--output-dir", self.out, "--json"] + list(extra))

    def check(self, *extra):
        return run_engine(["check", "--project-root", self.root,
                           "--output-dir", self.out, "--json"] + list(extra))


class ScanTests(EngineCase):

    # trace: BC-3 门禁拒绝路径（无测试文件 → exit 1 + 零产出）
    def test_scan_refuses_with_no_test_files(self):
        self.write("src/app.py", "print(1)" + NL)
        r = self.scan()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertNotIn("Traceback", r.stderr)
        data = json.loads(r.stdout)
        self.assertFalse(data["ok"])
        self.assertIn("MISSING_FILE", {x["code"] for x in data["violations"]})
        self.assertFalse(os.listdir(self.out), "拒绝路径不得写任何文件")

    # trace: BC-2 机械项检出 + convention baseline 采样（7 key）
    def test_scan_detects_mechanical_rows_and_baseline(self):
        body = NL.join([
            "test('跳过用例', () => {",
            "  test.skip('待实现', () => {});",
            "  expect(true).toBe(true);",
            "  await page.waitForTimeout(500);",
            "});",
        ]) + NL
        self.write("tests/api.spec.ts", body)
        # 语料（评审集之外）：4 个文件，1 个带优先级标记 → emerging
        for i in range(4):
            marker = "test('[P0] 结算', () => {});" if i == 0 else "test('结算', () => {});"
            self.write("tests/legacy/spec%d.spec.ts" % i, marker + NL)
        r = self.scan("--paths", "tests/api.spec.ts")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertTrue(data["ok"])
        rows = {m["row"]: m for m in data["mechanical"]}
        for expected in ("C1", "C3", "H1"):
            self.assertIn(expected, rows, data["mechanical"])
            self.assertTrue(rows[expected]["note"], data["mechanical"])
        self.assertEqual(len(data["files"]), 1)
        baseline = data["baseline"]
        self.assertEqual(baseline["corpus_size"], 4)
        self.assertEqual(baseline["sampled"], 4)
        for key in ("priority_markers", "test_ids", "network_first",
                    "data_factories", "fixtures"):
            entry = baseline["keys"][key]
            self.assertIn("adopted", entry, key)
            self.assertIn(entry["status"],
                          ("已确立", "新现", "缺失", "未知"), key)
        self.assertEqual(baseline["keys"]["priority_markers"]["adopted"], 1)
        self.assertEqual(baseline["keys"]["priority_markers"]["status"], "新现")
        for key in ("bdd_naming", "assertion_style"):
            self.assertEqual(baseline["keys"][key], {"judged_by": "llm"}, key)

    # trace: BC-2 契约冒烟（回执共同键 + counts）
    def test_scan_receipt_has_common_keys(self):
        self.write("tests/a.spec.ts", "test('x', () => {});" + NL)
        r = self.scan("--paths", "tests/a.spec.ts")
        data = json.loads(r.stdout)
        for key in ("ok", "command", "project_root", "output_dir",
                    "violations", "warnings", "counts"):
            self.assertIn(key, data)
        self.assertEqual(data["command"], "scan")

    # trace: §6 门禁（excluded 三值：unsupported-format / generated / out-of-scope）
    def test_scan_classifies_excluded_reasons(self):
        self.write("tests/legacy.feature", "Feature: 结算" + NL)
        self.write("tests/gen.spec.ts", "// Code generated by tool. DO NOT EDIT." + NL)
        self.write("tests/real.spec.ts", "test('x', () => {});" + NL)
        r = self.scan("--paths", "tests/legacy.feature", "--paths", "tests/gen.spec.ts",
                      "--paths", "tests/real.spec.ts", "--paths", "tests/absent.spec.ts")
        data = json.loads(r.stdout)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        reasons = {e["path"].replace("\\", "/"): e["reason"] for e in data["excluded"]}
        self.assertEqual(reasons["tests/legacy.feature"], "格式不支持")
        self.assertEqual(reasons["tests/gen.spec.ts"], "自动生成")
        self.assertEqual(reasons["tests/absent.spec.ts"], "超出范围")
        self.assertEqual([f.replace("\\", "/") for f in data["files"]], ["tests/real.spec.ts"])

    # trace: V §1.4 R-3（空测试文件 → excluded 不评分 + "No tests found"）
    def test_scan_excludes_empty_test_file(self):
        self.write("tests/blank.spec.ts", NL + "   " + NL)
        self.write("tests/comments.spec.ts", "// TODO 待补" + NL + "/* 说明 */" + NL)
        self.write("tests/real.spec.ts", "test('x', () => { expect(1).toBe(1); });" + NL)
        r = self.scan("--paths", "tests")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        # 空文件不评分：既不在评审集，也不假装"已评审"
        self.assertEqual([f.replace("\\", "/") for f in data["files"]], ["tests/real.spec.ts"])
        reasons = {e["path"].replace("\\", "/"): e["reason"] for e in data["excluded"]}
        self.assertEqual(reasons["tests/blank.spec.ts"], "超出范围")
        self.assertEqual(reasons["tests/comments.spec.ts"], "超出范围")
        notes = " ".join(w["msg"] for w in data["warnings"])
        self.assertIn("No tests found", notes, data["warnings"])
        # 全空 → 走无测试文件的拒绝路径（exit 1 + 零产出）
        r2 = self.scan("--paths", "tests/blank.spec.ts")
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertIn("MISSING_FILE", {x["code"] for x in json.loads(r2.stdout)["violations"]})

    # trace: V §1.4 R-3（极简测试文件 → warning "No meaningful tests"）
    def test_scan_warns_minimal_test_file(self):
        self.write("tests/placeholder.spec.ts", "test('结算', () => {});" + NL)
        self.write("tests/api.spec.ts",
                   "test('结算', () => { expect(res.status).toBe(200); });" + NL)
        r = self.scan("--paths", "tests")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        flagged = [w for w in data["warnings"] if "No meaningful tests" in w["msg"]]
        self.assertEqual([w["where"] for w in flagged],
                         ["tests/placeholder.spec.ts"], data["warnings"])
        # 有断言的文件不得被误报（宽口径断言集的反证方向）
        self.assertNotIn("tests/api.spec.ts", " ".join(w["where"] for w in data["warnings"]))

    # trace: V §1.4 R-4（mergeConfig 不可验证 → L4 advisory；ffi-safe 标记免报）
    def test_scan_pact_merge_config_advisory(self):
        merge_cfg = NL.join([
            "import { mergeConfig } from 'vitest/config';",
            "import base from './vitest.config';",
            "export default mergeConfig(base, { test: {} });",
        ]) + NL
        self.write("vitest.config.pact.ts", merge_cfg)
        self.write("vitest.config.contract.ts",
                   merge_cfg + "// " + "tea:pact-ffi-safe" + NL)
        self.write("tests/contract/orders.pacttest.ts",
                   "it('下单', () => { expect(pact).toBeTruthy(); });" + NL)
        r = self.scan("--paths", "tests/contract")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        rows = {m["row"]: m for m in data["mechanical"]}
        # 三条必需设置落在不可跟随的基础配置里 ⇒ 不冒充 H6/H7，合一降为 L4 advisory
        self.assertNotIn("H6", rows, data["mechanical"])
        self.assertNotIn("H7", rows, data["mechanical"])
        self.assertIn("L4", rows, data["mechanical"])
        self.assertIn("pact-config-unverifiable", rows["L4"]["note"])
        self.assertIn("tea:pact-ffi-safe", rows["L4"]["note"])
        self.assertEqual(rows["L4"]["file"], "vitest.config.pact.ts")
        # 带 // tea:pact-ffi-safe 标记的配置视为已验证，不报
        self.assertNotIn("vitest.config.contract.ts",
                         [m["file"] for m in data["mechanical"]])

    # trace: V §1.4 R-4（单 it() 多 addInteraction() → 无 registry row 的 warning）
    def test_scan_pact_single_it_multiple_interactions(self):
        self.write("tests/contract/a.pacttest.ts", NL.join([
            "it('多契约', async () => {",
            "  await pact.addInteraction().uponReceiving('一');",
            "  await pact.addInteraction().uponReceiving('二');",
            "  expect(res.status).toBe(200);",
            "});",
        ]) + NL)
        self.write("tests/contract/b.pacttest.ts", NL.join([
            "it('契约一', async () => {",
            "  await pact.addInteraction().uponReceiving('一');",
            "  expect(res.status).toBe(200);",
            "});",
            "it('契约二', async () => {",
            "  await pact.addInteraction().uponReceiving('二');",
            "  expect(res.status).toBe(200);",
            "});",
        ]) + NL)
        r = self.scan("--paths", "tests/contract")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        flagged = [w for w in data["warnings"] if "addInteraction" in w["msg"]]
        self.assertEqual(len(flagged), 1, data["warnings"])
        self.assertIn("a.pacttest.ts", flagged[0]["where"])
        # 一 it 一 interaction 的文件整片不得误判
        self.assertNotIn("b.pacttest.ts", flagged[0]["where"])


class ScoreTests(EngineCase):

    def findings_doc(self, findings, bonus=None):
        return {"findings": findings, "bonus": bonus or []}

    # trace: §6 裁定 1（账本纯函数：已知 findings → 已知分；去重 + convention 降档）
    def test_score_ledger_dedupes(self):
        self.write_findings(self.findings_doc([
            {"file": "tests/a.spec.ts", "line": 10, "row": "H1", "note": "硬等待"},
            {"file": "tests/a.spec.ts", "line": 10, "row": "H1", "note": "同点重复描述"},
            {"file": "tests/a.spec.ts", "line": 20, "row": "L2", "class": "已确立",
             "note": "无优先级标记"},
        ]))
        r = self.score("--findings", os.path.join(self.out, "test-review-findings.json"))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual(data["deductions"], {"critical": 0, "high": 1, "medium": 0,
                                              "low": 1, "total": 6})
        self.assertEqual(data["score"], 94)
        self.assertEqual(data["grade"], "A")
        self.assertEqual(data["recommendation"], "要求修改")
        self.assertEqual(data["counts"]["duplicates"], 1)
        # 维度分复算：H1 → determinism；L2 → 空映射（源表未归属）
        self.assertEqual(data["dimensions"]["determinism"], 90)
        self.assertEqual(data["dimensions"]["maintainability"], 100)

    # trace: §6 裁定 3（emerging 降一档 floor LOW；降档由 score 应用）
    def test_convention_downgrade_step(self):
        engine = load_engine()
        self.assertEqual(engine.downgrade_severity("MEDIUM", "新现"), "LOW")
        self.assertEqual(engine.downgrade_severity("CRITICAL", "新现"), "HIGH")
        self.assertEqual(engine.downgrade_severity("LOW", "新现"), "LOW")
        self.assertEqual(engine.downgrade_severity("HIGH", "已确立"), "HIGH")
        # 集成面：新现行落 LOW；缺失 / 未知 不得成条目（该行不成立）
        self.write_findings(self.findings_doc([
            {"file": "tests/a.spec.ts", "line": 5, "row": "L2", "class": "新现",
             "note": "惯例未普及"},
        ]))
        r = self.score("--findings", os.path.join(self.out, "test-review-findings.json"))
        self.assertEqual(json.loads(r.stdout)["deductions"]["low"], 1)
        self.write_findings(self.findings_doc([
            {"file": "tests/a.spec.ts", "line": 5, "row": "L2", "class": "缺失",
             "note": "该行不成立"},
        ]))
        r2 = self.score("--findings", os.path.join(self.out, "test-review-findings.json"))
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertIn("ENUM_INVALID", {x["code"] for x in json.loads(r2.stdout)["violations"]})

    # trace: §6 裁定 1/评分账本（分档与 recommendation 数值口径照源）
    def test_grade_and_recommendation_parametric(self):
        cases = [
            ([{"file": "t.spec.ts", "line": 1, "row": "C1", "note": "跳过"}],
             "A", "打回"),
            ([{"file": "t.spec.ts", "line": 1, "row": "H1", "note": "硬等待"}],
             "A", "要求修改"),
            ([{"file": "t.spec.ts", "line": i, "row": "M6", "note": "未 await"}
              for i in range(1, 17)], "D", "要求修改"),
            ([{"file": "t.spec.ts", "line": 1, "row": "M6", "note": "未 await"}],
             "A", "有保留批准"),
            ([], "A", "批准"),
        ]
        for findings, grade, recommendation in cases:
            self.write_findings(self.findings_doc(findings))
            r = self.score("--findings", os.path.join(self.out, "test-review-findings.json"))
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            data = json.loads(r.stdout)
            self.assertEqual(data["grade"], grade, data)
            self.assertEqual(data["recommendation"], recommendation, data)

    # trace: §6 裁定 7（bonus 六类数值域 + 矛盾复核）
    def test_bonus_domain_and_guard(self):
        # 数值域：points 只许 0 或 5
        self.write_findings(self.findings_doc(
            [], [{"key": "perfectIsolation", "points": 3, "note": "部分分"}],
        ))
        r = self.score("--findings", os.path.join(self.out, "test-review-findings.json"))
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ENUM_INVALID", {x["code"] for x in json.loads(r.stdout)["violations"]})
        # 矛盾复核：bonus 得 5 而对应规则行有命中（perfectIsolation ↔ H4）
        self.write_findings(self.findings_doc(
            [{"file": "t.spec.ts", "line": 3, "row": "H4", "note": "共享状态未重置"}],
            [{"key": "perfectIsolation", "points": 5, "note": "全文件干净"}],
        ))
        r2 = self.score("--findings", os.path.join(self.out, "test-review-findings.json"))
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertIn("SET_MISMATCH", {x["code"] for x in json.loads(r2.stdout)["violations"]})
        # 上限 30 与总分：六类全给 → 100 - 0 + 30
        self.write_findings(self.findings_doc([], [
            {"key": k, "points": 5, "note": "全文件成立"} for k in
            ("excellentBdd", "comprehensiveFixtures", "dataFactories",
             "networkFirst", "perfectIsolation", "allTestIds")]))
        r3 = self.score("--findings", os.path.join(self.out, "test-review-findings.json"))
        data = json.loads(r3.stdout)
        self.assertEqual(data["bonus"]["total"], 30)
        self.assertEqual(data["score"], 100)
        self.assertEqual(len(data["bonus"]["applied"]), 6)

    # trace: §6（findings.json 缺席 / 不可解析 → 结构化拒绝，不崩溃）
    def test_score_rejects_missing_or_broken_findings(self):
        r = self.score("--findings", os.path.join(self.out, "test-review-findings.json"))
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertNotIn("Traceback", r.stderr)
        self.assertIn("MISSING_FILE", {x["code"] for x in json.loads(r.stdout)["violations"]})
        self.write("diy-output/test-review-findings.json", "{not json")
        r2 = self.score("--findings", os.path.join(self.out, "test-review-findings.json"))
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertNotIn("Traceback", r2.stderr)
        self.assertIn("UNPARSABLE_YAML",
                      {x["code"] for x in json.loads(r2.stdout)["violations"]})


class WalkthroughTests(EngineCase):

    # trace: §6 裁定 5（四类缺口 + 建议路由）
    def test_walkthrough_detects_four_gap_kinds(self):
        self.write("diy-output/stories.yaml", STORIES_YAML)
        self.write("diy-output/test-plan.yaml", TEST_PLAN_YAML)
        self.write("src/settle.py", SRC_WITH_TRACE)
        r = self.walkthrough()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual(data["status"], "全覆盖", data)
        for kind in ("无实现", "无测试", "孤儿用例", "从未运行"):
            self.assertIn(kind, data["gaps"], data)
        refs = {kind: {(g["ref"], g["route"]) for g in data["gaps"][kind]}
                for kind in ("无实现", "无测试", "孤儿用例", "从未运行")}
        self.assertIn(("AC-1.1", "diy-dev"), refs["无实现"])
        self.assertIn(("AC-1.3", "diy-dev"), refs["无实现"])
        self.assertIn(("AC-1.1", "diy-test-design"), refs["无测试"])
        self.assertIn(("AC-1.2", "diy-test-author"), refs["无测试"])
        self.assertIn(("TC-1.9.1", "user"), refs["孤儿用例"])
        self.assertIn(("TC-1.2.1", "diy-test-author"), refs["从未运行"])
        self.assertEqual(data["counts"]["无实现"], 2)
        self.assertEqual(data["counts"]["孤儿用例"], 1)

    # trace: §6 裁定 5（no_impl 护栏：项目全量零 trace 标记 → 该类整体跳过 + warning）
    def test_walkthrough_skips_no_impl_without_trace_marks(self):
        self.write("diy-output/stories.yaml", STORIES_YAML)
        self.write("diy-output/test-plan.yaml", TEST_PLAN_YAML)
        self.write("src/settle.py", "def settle():" + NL + "    return 1" + NL)
        r = self.walkthrough()
        data = json.loads(r.stdout)
        self.assertEqual(data["gaps"]["无实现"], [], data)
        self.assertTrue(any("实现面不可判" in w["msg"] for w in data["warnings"]), data)
        self.assertEqual(data["status"], "部分覆盖", data)
        self.assertIn("无实现", "".join(w["msg"] for w in data["warnings"]), data)

    # trace: §6 裁定 5（缺源降级：stories 缺 → ①②③跳过；全缺 → skipped + note）
    def test_walkthrough_degrades_when_sources_missing(self):
        r = self.walkthrough()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual(data["status"], "已跳过", data)
        self.assertEqual(sum(len(v) for v in data["gaps"].values()), 0)
        self.assertTrue(data["warnings"], data)
        self.assertIn("stories.yaml",
                      " ".join(w["where"] for w in data["warnings"]), data)
        # stories 缺席、test-plan 定稿：②③ 跳过、④ 仍可评
        self.write("diy-output/test-plan.yaml", TEST_PLAN_YAML)
        r2 = self.walkthrough()
        data2 = json.loads(r2.stdout)
        self.assertEqual(data2["status"], "部分覆盖", data2)
        self.assertEqual(data2["gaps"]["无测试"], [], data2)
        self.assertIn(("TC-1.2.1", "diy-test-author"),
                      {(g["ref"], g["route"]) for g in data2["gaps"]["从未运行"]})


class CheckTests(EngineCase):

    def write_review(self, text):
        return self.write("diy-output/test-review.yaml", text)

    # trace: 验收 #2 产物 schema（合法记录 exit 0 唯一放行 + 回执键完整性）
    def test_check_final_legal_record_passes(self):
        self.write_review(REVIEW_YAML)
        r = self.check("--final")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertTrue(data["ok"])
        self.assertEqual(data["violations"], [])
        self.assertEqual(data["counts"]["reviews"], 1)
        self.assertEqual(data["counts"]["findings"], 1)
        for key in ("ok", "command", "project_root", "output_dir",
                    "violations", "warnings", "counts"):
            self.assertIn(key, data)

    # trace: §6 check（账本自洽：severity 计数 / 行相加 / recommendation）
    def test_check_rejects_inconsistent_ledger(self):
        bad_total = REVIEW_YAML.replace("total: 1", "total: 3")
        self.write_review(bad_total)
        r = self.check("--final")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("SET_MISMATCH", {x["code"] for x in json.loads(r.stdout)["violations"]})
        bad_rec = REVIEW_YAML.replace("recommendation: 有保留批准",
                                      "recommendation: 批准")
        self.write_review(bad_rec)
        r2 = self.check("--final")
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertIn("SET_MISMATCH", {x["code"] for x in json.loads(r2.stdout)["violations"]})
        # 声明 severity 与引擎复算不符（L2 convention 新现 → LOW；声明成 MEDIUM 须拒）
        bad_sev = REVIEW_YAML.replace("severity: LOW", "severity: MEDIUM")
        self.write_review(bad_sev)
        r3 = self.check("--final")
        self.assertEqual(r3.returncode, 1, r3.stdout)
        self.assertIn("SET_MISMATCH", {x["code"] for x in json.loads(r3.stdout)["violations"]})

    # trace: §6 check（coverage_gaps 形态 + walkthrough 自洽）
    def test_check_rejects_gap_shape_and_walkthrough_mismatch(self):
        self.write_review(REVIEW_YAML.replace("ref: AC-1.1", "ref: TC-1.1.1"))
        r = self.check("--final")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("SET_MISMATCH", {x["code"] for x in json.loads(r.stdout)["violations"]})
        self.write_review(REVIEW_YAML.replace("route: diy-dev", "route: diy-sprint"))
        r2 = self.check("--final")
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertIn("ENUM_INVALID", {x["code"] for x in json.loads(r2.stdout)["violations"]})
        self.write_review(REVIEW_YAML.replace(
            "walkthrough: {status: 部分覆盖, note: test-plan.yaml 未定稿：②③④类跳过}",
            "walkthrough: {status: 部分覆盖, note: ''}"))
        r3 = self.check("--final")
        self.assertEqual(r3.returncode, 1, r3.stdout)
        self.assertIn("EMPTY_FIELD", {x["code"] for x in json.loads(r3.stdout)["violations"]})
        self.write_review(REVIEW_YAML.replace(
            "walkthrough: {status: 部分覆盖, note: test-plan.yaml 未定稿：②③④类跳过}",
            "walkthrough: {status: 已跳过, note: 三源全缺}"))
        r4 = self.check("--final")
        self.assertEqual(r4.returncode, 1, r4.stdout)
        self.assertIn("SET_MISMATCH", {x["code"] for x in json.loads(r4.stdout)["violations"]})

    # trace: §6 check（valid 32 行：disabled 行不得成条目）
    def test_check_rejects_disabled_row(self):
        self.write_review(REVIEW_YAML.replace("row: L2", "row: M9"))
        r = self.check("--final")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ENUM_INVALID", {x["code"] for x in json.loads(r.stdout)["violations"]})
        self.write_review(REVIEW_YAML.replace("row: L2", "row: Z9"))
        r2 = self.check("--final")
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertIn("ENUM_INVALID", {x["code"] for x in json.loads(r2.stdout)["violations"]})

    # trace: §6 check --final 附加（零 [假设] / excluded 三值 / scope 非空）
    def test_check_final_duties(self):
        self.write_review(REVIEW_YAML.replace("note: 无优先级标记",
                                              "note: '[假设] 待定'"))
        r = self.check("--final")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ASSUMPTION_PRESENT",
                      {x["code"] for x in json.loads(r.stdout)["violations"]})
        self.write_review(REVIEW_YAML.replace("    excluded: []",
                                              "    excluded:" + NL
                                              + "    - {path: a.ts, reason: 不合法理由}"))
        r2 = self.check("--final")
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertIn("ENUM_INVALID", {x["code"] for x in json.loads(r2.stdout)["violations"]})
        self.write_review(REVIEW_YAML.replace("    files_reviewed: 1", "    files_reviewed: 0")
                          .replace("    paths:" + NL + "    - tests/api.spec.ts",
                                   "    paths: []"))
        r3 = self.check("--final")
        self.assertEqual(r3.returncode, 1, r3.stdout)
        self.assertIn("EMPTY_FIELD", {x["code"] for x in json.loads(r3.stdout)["violations"]})

    # trace: V §1.4 R-2（convention 引用与实际语料独立复测：class ↔ baseline.status）
    def test_check_rejects_class_baseline_mismatch(self):
        # ① class 与 status 不符（谎报 已确立）= 引用与测量不符 → 拒
        self.write_review(REVIEW_YAML.replace(
            "priority_markers: {adopted: 3, status: 已确立}",
            "priority_markers: {adopted: 3, status: 新现}"))
        r = self.check("--final")
        self.assertEqual(r.returncode, 1, r.stdout)
        bad = [x for x in json.loads(r.stdout)["violations"]
               if x["where"].endswith("findings[row=L2].class")]
        self.assertEqual([x["code"] for x in bad], ["SET_MISMATCH"], bad)
        # ② baseline 测到 缺失 → 该行本不成立、不得成条目 → 拒
        self.write_review(REVIEW_YAML.replace(
            "priority_markers: {adopted: 3, status: 已确立}",
            "priority_markers: {adopted: 0, status: 缺失}"))
        r2 = self.check("--final")
        self.assertEqual(r2.returncode, 1, r2.stdout)
        bad2 = [x for x in json.loads(r2.stdout)["violations"]
                if x["where"].endswith("findings[row=L2].class")]
        self.assertEqual([x["code"] for x in bad2], ["SET_MISMATCH"], bad2)
        # ③ 引用不可核（基线缺该键）→ 拒
        self.write_review(REVIEW_YAML.replace(
            "      priority_markers: {adopted: 3, status: 已确立}" + NL, ""))
        r3 = self.check("--final")
        self.assertEqual(r3.returncode, 1, r3.stdout)
        bad3 = [x for x in json.loads(r3.stdout)["violations"]
                if x["where"].endswith("findings[row=L2].class")]
        self.assertEqual([x["code"] for x in bad3], ["EMPTY_FIELD"], bad3)
        # ④ 引用与测量一致（已确立 ↔ 已确立 / 新现 ↔ 新现）→ 放行
        self.write_review(REVIEW_YAML.replace(
            "priority_markers: {adopted: 3, status: 已确立}",
            "priority_markers: {adopted: 3, status: 新现}").replace(
            "    class: 已确立", "    class: 新现"))
        r4 = self.check("--final")
        self.assertEqual(r4.returncode, 0, r4.stdout + r4.stderr)

    # trace: V §1.4 R-3（空文件不得计入评审集）
    def test_check_rejects_empty_file_in_scope(self):
        self.write("tests/api.spec.ts", "// 待补" + NL)
        self.write_review(REVIEW_YAML)
        r = self.check("--final")
        self.assertEqual(r.returncode, 1, r.stdout)
        bad = [x for x in json.loads(r.stdout)["violations"]
               if x["where"].endswith("scope.paths[0]")]
        self.assertEqual([x["code"] for x in bad], ["SET_MISMATCH"], bad)
        self.assertIn("No tests found", bad[0]["msg"])
        # 有真实内容 → 该条不成立
        self.write("tests/api.spec.ts", "test('x', () => { expect(1).toBe(1); });" + NL)
        r2 = self.check("--final")
        self.assertEqual(r2.returncode, 0, r2.stdout + r2.stderr)

    # trace: V §1.4 R-1（recommendations 上限 = Top 10）
    def test_check_caps_recommendations(self):
        ten = NL.join("  - 意见 %d" % i for i in range(10))
        self.write_review(REVIEW_YAML.replace(
            "  recommendations:" + NL + "  - 给用例补优先级标记",
            "  recommendations:" + NL + ten))
        r = self.check("--final")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        eleven = NL.join("  - 意见 %d" % i for i in range(11))
        self.write_review(REVIEW_YAML.replace(
            "  recommendations:" + NL + "  - 给用例补优先级标记",
            "  recommendations:" + NL + eleven))
        r2 = self.check("--final")
        self.assertEqual(r2.returncode, 1, r2.stdout)
        bad = [x for x in json.loads(r2.stdout)["violations"]
               if x["where"].endswith(".recommendations")]
        self.assertEqual([x["code"] for x in bad], ["SET_MISMATCH"], bad)

    # trace: §6 check（缺文件 / 不可解析 → 结构化违规，不 Traceback）
    def test_check_missing_or_broken_file(self):
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertNotIn("Traceback", r.stderr)
        self.assertEqual(json.loads(r.stdout)["violations"][0]["code"], "MISSING_FILE")
        self.write_review("reviews: [" + NL)
        r2 = self.check()
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertNotIn("Traceback", r2.stderr)
        self.assertEqual(json.loads(r2.stdout)["violations"][0]["code"], "UNPARSABLE_YAML")


class CriteriaRegistryTests(unittest.TestCase):
    """criteria.yaml 逐行留档完整性（35 行 / 32 有效 / 机械集 / 维度 / bonus_guard）。"""

    def setUp(self):
        import yaml
        with io.open(CRITERIA, encoding="utf-8") as f:
            self.doc = yaml.safe_load(f)
        self.rows = {r["row"]: r for r in self.doc["rules"]}

    # trace: §6 裁定 3/6/7（35 规则迁移对账的机械面）
    def test_registry_has_35_rows_32_enabled(self):
        self.assertEqual(len(self.rows), 35)
        disabled = {r["row"] for r in self.doc["rules"] if r.get("disabled")}
        self.assertEqual(disabled, {"M9", "M10", "L9"})
        for prefix, count in (("C", 7), ("H", 9), ("M", 10), ("L", 9)):
            got = [r for r in self.rows if r.startswith(prefix)]
            self.assertEqual(len(got), count, prefix)

    # trace: §6 裁定 6（机械集初始 = C1/C2/C3/H1/H5/H6/H7/H8/H9/L4）
    def test_mechanical_set_matches_spec(self):
        mechanical = {r["row"] for r in self.doc["rules"] if r["detect"] == "mechanical"}
        self.assertEqual(mechanical,
                         {"C1", "C2", "C3", "H1", "H5", "H6", "H7", "H8", "H9", "L4"})
        for row in self.doc["rules"]:
            self.assertIn(row["detect"], ("mechanical", "semantic"), row["row"])

    # trace: §6 裁定 4（维度映射照源四 worker 表；H9/M8/L2/L8 空映射）
    def test_dimension_mapping_matches_source(self):
        expected = {
            "determinism": {"C1", "C2", "C3", "C4", "C6", "C7", "H1", "H2", "H3",
                            "H6", "H7", "H8", "L4"},
            "isolation": {"C5", "H4", "M4"},
            "maintainability": {"M2", "M3", "M4", "M5", "M7", "M9", "M10", "H5",
                                "L1", "L3", "L5", "L6", "L7", "L9"},
            "performance": {"M1", "M6", "H5"},
        }
        for dim, rows in expected.items():
            got = {r["row"] for r in self.doc["rules"] if dim in (r.get("dimensions") or [])}
            self.assertEqual(got, rows, dim)
        empty = {r["row"] for r in self.doc["rules"] if not (r.get("dimensions") or [])}
        self.assertEqual(empty, {"H9", "M8", "L2", "L8"})

    # trace: V §1.4 R-2（class ↔ baseline 复核的键映射权威 = 行字段 convention_key）
    def test_convention_rows_carry_baseline_key(self):
        keys = ("priority_markers", "test_ids", "bdd_naming", "network_first",
                "data_factories", "fixtures", "assertion_style")
        convention = [r for r in self.doc["rules"] if r["basis"] == "convention"]
        self.assertTrue(convention, "convention 行缺失（三类门之一）")
        for row in convention:
            self.assertTrue(row.get("convention_key"), row["row"])
        # 有效 convention 行必须落在产物 7 键内，否则 R-2 复核会静默失能；
        # disabled 行（M9 / L9）留档的 playwright_utils 随私有库裁剪出 7 键（裁定 3）
        enabled = {r["row"]: r["convention_key"] for r in convention if not r.get("disabled")}
        self.assertEqual(enabled, {"L2": "priority_markers", "L3": "test_ids",
                                   "L5": "bdd_naming", "L7": "assertion_style"})
        for key in enabled.values():
            self.assertIn(key, keys)

    # trace: §6 裁定 7（bonus_guard 映射六类）
    def test_bonus_guard_mapping(self):
        guards = {}
        for row in self.doc["rules"]:
            for key in row.get("bonus_guard") or []:
                guards.setdefault(key, set()).add(row["row"])
        self.assertEqual(guards, {
            "excellentBdd": {"L5"},
            "comprehensiveFixtures": {"M2"},
            "dataFactories": {"M2"},
            "networkFirst": {"M1"},
            "perfectIsolation": {"H4"},
            "allTestIds": {"L1", "L3"},
        })


class SkillContractTests(unittest.TestCase):
    """契约冒烟：母本片段 + 评分口径 + 边界声明 + 终门句。"""

    def read_skill(self):
        with io.open(SKILL_MD, encoding="utf-8") as f:
            return f.read()

    # trace: 验收 #9/#12d（母本 §1 / §2 中文定稿逐字 + §3/§4/§5 锚串在场）
    def test_master_text_fragments_verbatim(self):
        skill = self.read_skill()
        self.assertIn(INSTANCE_ZH, skill)
        self.assertIn(DISCIPLINE_ZH, skill)
        self.assertIn(ANCHOR_RESOLVE_KEYS, skill)
        self.assertIn(ANCHOR_READ_DISCIPLINE, skill)
        self.assertIn(ANCHOR_RENDER_SILENT, skill)
        self.assertNotIn("Instance resolution (FR-4.5/D-9)", skill)
        self.assertNotIn("- **Writing discipline.**", skill)

    # trace: 验收 #12b（终门句指向本技能引擎）
    def test_final_gate_points_to_engine(self):
        skill = self.read_skill()
        self.assertIn("test_review.py", skill)
        self.assertIn("check --final", skill)
        self.assertIn("--json", skill)

    # trace: §6 硬约束 4（评分口径不得漂移）+ 裁定 2（与 diy-review 的边界）
    def test_scoring_formula_and_boundary_declared(self):
        skill = self.read_skill()
        self.assertIn("CRITICAL*10 + HIGH*5 + MEDIUM*2 + LOW*1", skill)
        self.assertIn("clamp(100 - deductions + bonus, 0, 100)", skill)
        self.assertIn("diy-review", skill)
        self.assertIn("审**测试代码**", skill)


if __name__ == "__main__":
    unittest.main()
