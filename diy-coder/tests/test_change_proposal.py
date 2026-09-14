# -*- coding: utf-8 -*-
"""diy-correct-course 确定性引擎 e2e 测试（B2 批 W3，任务书 §2.5/§5）。

覆盖：
- 用例 1：门禁拒绝（缺 prd.yaml / epics project.status 非 final）→ exit 1 + 结构化拒绝
          + 路由 + 零产出
- 用例 2：--output-dir 必填（用法错误 exit 2）
- 用例 3：collect 六产物摘要 + 委派 diyc 五型交叉核对（真跑子进程；违规并入证据键）
- 用例 4：collect 在 diyc 缺席时降级（TOOL_MISSING warning + 不崩 + 仍 exit 0）
- 用例 5：collect --target 引用链（二跳：FR-1.1 → AC-1.1 → TC-1.1.1；含 depended-by）
- 用例 6：check 合法记录 --final exit 0 唯一放行
- 用例 7：check 违规（edits 缺 rationale / old == new / handoff 未知技能 / impacts target 格式）
- 用例 8：check --final 义务（status 未终态 / 零假设 / impacts 空 / approach 未定 /
          scope 与 handoff 不一致）
- 用例 9：SKILL.md 契约冒烟（冻结实例句 md5 + 写作纪律块 md5 + 终门句指向 change_proposal.py
          + 只出提案不改真源声明）
夹具全部落 tempdir 自建；不读写本仓库真实 diy-output。
运行：cd diy-coder && python -m unittest discover -s tests -p "test_change_proposal.py" -v
"""
import contextlib
import hashlib
import io
import json
import os
import re
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.join(HERE, "..", "skills", "diy-correct-course")
ENGINE = os.path.join(SKILL_DIR, "scripts", "change_proposal.py")
SKILL_MD = os.path.join(SKILL_DIR, "SKILL.md")
NL = chr(10)

# 冻结文本校验值（batch4/frozen-texts.md §1/§2：逐字复制，md5 口径 = 文本 + 行尾 LF）
INSTANCE_MD5 = "5445f98bc4d4821e6888b89406a97eac"
DISCIPLINE_MD5 = "f1b3b6fbb528f0cfab31f3196b3547ae"

PRD_YAML = NL.join([
    "project:",
    "  name: mini",
    "  status: final",
    "  created: '2026-01-01'",
    "  updated: '2026-01-02'",
    "purpose: 夹具用途",
    "goals:",
    "- id: G-1",
    "  goal: 目标一",
    "  metric: 指标一",
    "users:",
    "- id: U-1",
    "  name: 使用者",
    "  need: 需要",
    "features:",
    "- id: F-1",
    "  name: 能力一",
    "  description: 能力描述",
    "  requirements:",
    "  - id: FR-1.1",
    "    statement: 必须能力一",
    "    priority: must",
    "  - id: FR-1.2",
    "    statement: 应当能力二",
    "    priority: should",
    "nfrs:",
    "- id: NFR-1",
    "  statement: 性能要求",
]) + NL

EPICS_YAML = NL.join([
    "project:",
    "  name: mini",
    "  status: final",
    "  created: '2026-01-01'",
    "  updated: '2026-01-02'",
    "epics:",
    "- id: E-1",
    "  title: 史诗一",
    "  goal: 用户能完成一件事",
    "  feature_refs: [F-1]",
    "  status: in-progress",
]) + NL

STORIES_YAML = NL.join([
    "project:",
    "  name: mini",
    "  status: final",
    "  created: '2026-01-01'",
    "  updated: '2026-01-02'",
    "stories:",
    "- id: S-1",
    "  epic: E-1",
    "  title: 故事一",
    "  narrative: 作为使用者，我希望完成一件事",
    "  acceptance_criteria:",
    "  - id: AC-1.1",
    "    given: 前置",
    "    when: 动作",
    "    then: 结果",
    "    refs:",
    "    - FR-1.1",
    "  status: in-progress",
]) + NL

ARCH_YAML = NL.join([
    "project:",
    "  name: mini",
    "  status: final",
    "  created: '2026-01-01'",
    "  updated: '2026-01-02'",
    "stack:",
    "- choice: python",
    "  why: 夹具",
    "decisions:",
    "- id: D-1",
    "  title: 决策一",
    "  decision: 采用方案甲",
    "  rationale: 理由",
    "  alternatives:",
    "  - option: 方案乙",
    "    why_not: 更贵",
    "  affects: [FR-1.1]",
    "  status: accepted",
]) + NL

OPENAPI_YAML = NL.join([
    "openapi: 3.1.0",
    "x-project:",
    "  name: mini",
    "  status: final",
    "  created: '2026-01-01'",
    "  updated: '2026-01-02'",
    "info:",
    "  title: mini",
    "  version: 0.1.0",
    "  description: 夹具",
    "paths:",
    "  /items:",
    "    get:",
    "      operationId: listItems",
    "      summary: 列出条目",
    "      x-fr: [FR-1.1]",
    "      responses:",
    "        \"200\":",
    "          description: OK",
]) + NL

DESIGN_YAML = NL.join([
    "project:",
    "  name: mini",
    "  status: final",
    "  created: '2026-01-01'",
    "  updated: '2026-01-02'",
    "pages:",
    "- id: P-1",
    "  name: 首页",
    "  route: /",
    "  states:",
    "  - {name: hover, signals: [icon]}",
]) + NL

TESTPLAN_YAML = NL.join([
    "project:",
    "  name: mini",
    "  status: final",
    "  created: '2026-01-01'",
    "  updated: '2026-01-02'",
    "test_cases:",
    "- id: TC-1.1.1",
    "  title: 用例一",
    "  ac: AC-1.1",
    "  type: unit",
    "  priority: P0",
    "  technique: example",
    "  kill_target: 逻辑错误",
    "  status: pending",
    "  steps:",
    "  - 步骤一",
]) + NL

SPRINT_YAML = NL.join([
    "project:",
    "  name: mini",
    "  status: final",
    "  created: '2026-01-01'",
    "  updated: '2026-01-02'",
    "tasks:",
    "- story: S-1",
    "  status: in-progress",
    "  test_refs: [TC-1.1.1]",
]) + NL

PROPOSAL_YAML = NL.join([
    "project:",
    "  name: mini",
    "  created: '2026-09-14'",
    "  updated: '2026-09-14'",
    "proposals:",
    "- id: CP-001",
    "  date: '2026-09-14'",
    "  status: final",
    "  trigger: 实施中发现 2FA 是安全评审的必须项",
    "  mode: incremental",
    "  scope: moderate",
    "  impacts:",
    "  - {artifact: prd, target: FR-1.1, kind: modify, why: 需补 2FA 要求}",
    "  - {artifact: stories, target: AC-1.1, kind: add, why: 缺 2FA 验收标准}",
    "  edits:",
    "  - artifact: stories",
    "    target: AC-1.1",
    "    field: acceptance_criteria",
    "    old: AC-1.1 仅覆盖邮箱密码登录",
    "    new: AC-1.1 追加 2FA 启用步骤",
    "    rationale: 安全评审要求双因子",
    "  ripple:",
    "  - TC-1.1.1 需补 2FA 用例",
    "  effort: {estimate: 小, risk: 低, timeline_impact: 本 sprint 内}",
    "  approach: {path: direct-adjustment, why: 现有 epic 结构可承载}",
    "  handoff: {route: diy-epics-stories, note: 追加 AC 后重跑 sprint 门}",
    "  open_questions: []",
    "revisions: []",
]) + NL


def run_engine(args):
    import subprocess
    return subprocess.run([sys.executable, ENGINE] + args,
                          capture_output=True, text=True, encoding="utf-8")


class EngineCase(unittest.TestCase):
    """tmp 项目根 + diy-output 目录的公共夹具。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="correct-course-")
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

    def write_core(self, prd=PRD_YAML, epics=EPICS_YAML, stories=STORIES_YAML):
        self.write("diy-output/prd.yaml", prd)
        self.write("diy-output/epics.yaml", epics)
        self.write("diy-output/stories.yaml", stories)

    def write_six(self):
        self.write_core()
        self.write("diy-output/architecture.yaml", ARCH_YAML)
        self.write("diy-output/openapi.yaml", OPENAPI_YAML)
        self.write("diy-output/design.yaml", DESIGN_YAML)

    def collect(self, *extra):
        return run_engine(["collect", "--project-root", self.root,
                           "--output-dir", self.out, "--json"] + list(extra))

    def check(self, *extra):
        return run_engine(["check", "--project-root", self.root,
                           "--output-dir", self.out, "--json"] + list(extra))

    def proposal_path(self):
        return os.path.join(self.out, "change-proposal.yaml")

    def out_files(self):
        return sorted(os.listdir(self.out))


class GateTests(EngineCase):

    # trace: 任务书 §5 门禁（prd 缺失 → 零产出退出 + 路由）
    def test_gate_refuses_missing_prd_with_zero_output(self):
        self.write("diy-output/epics.yaml", EPICS_YAML)
        self.write("diy-output/stories.yaml", STORIES_YAML)
        r = self.collect()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertNotIn("Traceback", r.stderr)
        data = json.loads(r.stdout)
        self.assertFalse(data["ok"])
        self.assertFalse(data["gate"]["passed"])
        self.assertEqual([x["code"] for x in data["violations"]], ["MISSING_FILE"])
        self.assertIn("prd.yaml", data["violations"][0]["where"])
        self.assertIn("diy-prd", data["gate"]["route"])
        self.assertNotIn("change-proposal.yaml", self.out_files(),
                         "拒绝路径不得产出 change-proposal.yaml")
        self.assertEqual(self.out_files(), ["epics.yaml", "stories.yaml"])

    # trace: 任务书 §5 门禁（三件套须 project.status: final）
    def test_gate_refuses_non_final_epics(self):
        self.write_core(epics=EPICS_YAML.replace("status: final", "status: draft", 1))
        r = self.collect()
        self.assertEqual(r.returncode, 1, r.stdout)
        data = json.loads(r.stdout)
        self.assertFalse(data["ok"])
        self.assertEqual([x["code"] for x in data["violations"]], ["STATUS_MISMATCH"])
        self.assertIn("diy-epics-stories", data["gate"]["route"])
        self.assertNotIn("change-proposal.yaml", self.out_files())

    # trace: 任务书 §2.2（引擎不做实例解析/目录推导：--output-dir 必填）
    def test_output_dir_is_mandatory(self):
        r = run_engine(["collect", "--project-root", self.root, "--json"])
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        r2 = run_engine(["check", "--project-root", self.root, "--json"])
        self.assertEqual(r2.returncode, 2, r2.stdout + r2.stderr)


class CollectTests(EngineCase):

    # trace: 任务书 §5 collect ①②（六产物 ID 级摘要 + 委派 diyc 五型交叉核对）
    def test_collect_summarizes_six_docs_and_delegates_diyc(self):
        self.write_six()
        r = self.collect()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertTrue(data["ok"])
        self.assertTrue(data["gate"]["passed"])
        docs = data["docs"]
        self.assertEqual([f["id"] for f in docs["prd"]["features"]], ["F-1"])
        self.assertEqual(docs["prd"]["features"][0]["requirements"], ["FR-1.1", "FR-1.2"])
        self.assertEqual(docs["prd"]["nfrs"], ["NFR-1"])
        self.assertEqual([e["id"] for e in docs["epics"]["epics"]], ["E-1"])
        self.assertEqual(docs["stories"]["stories"][0]["acs"], ["AC-1.1"])
        self.assertEqual([d["id"] for d in docs["architecture"]["decisions"]], ["D-1"])
        self.assertEqual(docs["architecture"]["decisions"][0]["affects"], ["FR-1.1"])
        self.assertEqual([o["operationId"] for o in docs["openapi"]["operations"]], ["listItems"])
        self.assertEqual([p["id"] for p in docs["design"]["pages"]], ["P-1"])
        # 委派 diyc 五型（跨文档机械核对的唯一入口；违规并入证据键，不判死）
        self.assertTrue(data["diyc"]["available"])
        self.assertEqual(data["diyc"]["checked"], ["prd", "architecture", "openapi", "epics", "stories"])
        self.assertIsInstance(data["diyc"]["check"]["violations"], list)
        self.assertIn("stories", data["diyc"]["check"]["counts"])
        self.assertEqual(data["counts"]["frs"], 2)
        self.assertEqual(data["counts"]["acs"], 1)

    # trace: 任务书 §2.3/§5 collect（diyc 缺席 → 结构化 warning 降级，不崩）
    def test_collect_degrades_when_diyc_missing(self):
        self.write_six()
        sys.path.insert(0, os.path.join(SKILL_DIR, "scripts"))
        old_bytecode = sys.dont_write_bytecode
        sys.dont_write_bytecode = True  # 不把 __pycache__ 落进技能目录
        try:
            import change_proposal
        finally:
            sys.dont_write_bytecode = old_bytecode
            sys.path.pop(0)
        original = change_proposal.diyc_script_path
        change_proposal.diyc_script_path = lambda: os.path.join(self.root, "no-such-diyc.py")
        try:
            args = change_proposal.build_parser().parse_args(
                ["collect", "--project-root", self.root, "--output-dir", self.out,
                 "--json"])
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = args.func(args)
        finally:
            change_proposal.diyc_script_path = original
        self.assertEqual(rc, 0, buf.getvalue())
        data = json.loads(buf.getvalue())
        self.assertTrue(data["ok"])
        self.assertFalse(data["diyc"]["available"])
        self.assertEqual(data["diyc"]["check"]["violations"], [])
        self.assertEqual([w["code"] for w in data["warnings"]], ["TOOL_MISSING"])

    # trace: 任务书 §5 collect ③（--target 引用链：跨文档上游/下游引用点，二跳）
    def test_collect_chain_for_target(self):
        self.write_six()
        self.write("diy-output/test-plan.yaml", TESTPLAN_YAML)
        self.write("diy-output/sprint.yaml", SPRINT_YAML)
        r = self.collect("--target", "FR-1.1")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        chain = {(c["doc"], str(c["id"]), c["field"], c["ref"], c["direction"])
                 for c in data["chain"]}
        self.assertIn(("stories", "AC-1.1", "refs", "FR-1.1", "depended-by"), chain)
        self.assertIn(("architecture", "D-1", "affects", "FR-1.1", "depended-by"), chain)
        self.assertIn(("openapi", "listItems", "x-fr", "FR-1.1", "depended-by"), chain)
        # 二跳：命中的 AC-1.1 继续展开到 TC（施工影响面）
        self.assertIn(("test-plan", "TC-1.1.1", "ac", "AC-1.1", "depended-by"), chain)
        self.assertIn(("stories", "S-1", "acceptance_criteria", "AC-1.1", "depended-by"), chain)
        self.assertEqual(data["counts"]["chain"], len(data["chain"]))

    # trace: 任务书 §5 collect（target 未命中 → UNKNOWN_ID 拒绝；格式非法 → ENUM_INVALID）
    def test_collect_target_unknown_and_invalid(self):
        self.write_six()
        r = self.collect("--target", "FR-9.9")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("UNKNOWN_ID", {x["code"] for x in json.loads(r.stdout)["violations"]})
        r2 = self.collect("--target", "wat")
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertIn("ENUM_INVALID", {x["code"] for x in json.loads(r2.stdout)["violations"]})


class CheckValidationTests(EngineCase):

    # trace: 任务书 §2.5 用例 3（合法记录 --final exit 0 唯一放行）
    def test_check_final_legal_record_passes(self):
        self.write("diy-output/change-proposal.yaml", PROPOSAL_YAML)
        r = self.check("--final")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertTrue(data["ok"])
        self.assertEqual(data["violations"], [])
        self.assertEqual(data["counts"]["proposals"], 1)
        self.assertEqual(data["counts"]["by_scope"], {"moderate": 1})

    # trace: 任务书 §5 check（edits 完整：old+new+rationale 非空且 old != new）
    def test_check_edits_completeness(self):
        no_rationale = PROPOSAL_YAML.replace(NL + "    rationale: 安全评审要求双因子", "")
        self.write("diy-output/change-proposal.yaml", no_rationale)
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("EMPTY_FIELD", {x["code"] for x in json.loads(r.stdout)["violations"]})
        same = PROPOSAL_YAML.replace("    new: AC-1.1 追加 2FA 启用步骤",
                                     "    new: AC-1.1 仅覆盖邮箱密码登录")
        self.write("diy-output/change-proposal.yaml", same)
        r2 = self.check()
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertIn("SET_MISMATCH", {x["code"] for x in json.loads(r2.stdout)["violations"]})

    # trace: 任务书 §5 check（handoff.route 未知技能违例 / impacts target 格式）
    def test_check_handoff_and_impact_target(self):
        bad_route = PROPOSAL_YAML.replace("route: diy-epics-stories", "route: diy-nope")
        self.write("diy-output/change-proposal.yaml", bad_route)
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ENUM_INVALID", {x["code"] for x in json.loads(r.stdout)["violations"]})
        bad_target = PROPOSAL_YAML.replace("target: FR-1.1, kind: modify", "target: req-one, kind: modify")
        self.write("diy-output/change-proposal.yaml", bad_target)
        r2 = self.check()
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertIn("ENUM_INVALID", {x["code"] for x in json.loads(r2.stdout)["violations"]})

    # trace: 任务书 §5 check（枚举 / 重复 ID / schema）
    def test_check_schema_violations(self):
        cases = [
            ("ENUM_INVALID", "status: final", "status: done"),
            ("ENUM_INVALID", "mode: incremental", "mode: freestyle"),
            ("ENUM_INVALID", "scope: moderate", "scope: huge"),
            ("ENUM_INVALID", "id: CP-001", "id: CP-1"),
            ("UNPARSABLE_YAML", None, None),
        ]
        for code, old, new in cases:
            text = ("proposals: [" + NL) if old is None else PROPOSAL_YAML.replace(old, new)
            self.write("diy-output/change-proposal.yaml", text)
            r = self.check()
            self.assertEqual(r.returncode, 1, r.stdout)
            self.assertIn(code, {x["code"] for x in json.loads(r.stdout)["violations"]},
                          "%s 未报出：%s" % (code, r.stdout))
        body = PROPOSAL_YAML.split("proposals:" + NL, 1)[1].replace("revisions: []" + NL, "")
        self.write("diy-output/change-proposal.yaml",
                   PROPOSAL_YAML.replace("revisions: []" + NL, "") + body)
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("DUPLICATE_ID", {x["code"] for x in json.loads(r.stdout)["violations"]})

    # trace: 任务书 §5 check --final（终态 status / 零假设 / impacts 非空 / approach 已定 /
    #        scope 与 handoff 一致性）
    def test_check_final_duties(self):
        draft = PROPOSAL_YAML.replace("status: final", "status: draft")
        self.write("diy-output/change-proposal.yaml", draft)
        r = self.check("--final")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("STATUS_MISMATCH", {x["code"] for x in json.loads(r.stdout)["violations"]})

        assumption = PROPOSAL_YAML.replace("trigger: 实施中发现 2FA 是安全评审的必须项",
                                           "trigger: '[ASSUMPTION] 疑似缺 2FA'")
        self.write("diy-output/change-proposal.yaml", assumption)
        r2 = self.check("--final")
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertIn("ASSUMPTION_PRESENT", {x["code"] for x in json.loads(r2.stdout)["violations"]})

        no_impacts = PROPOSAL_YAML.replace(NL + "  - {artifact: stories, target: AC-1.1,"
                                               " kind: add, why: 缺 2FA 验收标准}", "")
        self.write("diy-output/change-proposal.yaml", no_impacts.replace(
            NL + "  - {artifact: prd, target: FR-1.1, kind: modify, why: 需补 2FA 要求}", ""))
        r3 = self.check("--final")
        self.assertEqual(r3.returncode, 1, r3.stdout)
        self.assertIn("EMPTY_FIELD", {x["code"] for x in json.loads(r3.stdout)["violations"]})

        no_approach = PROPOSAL_YAML.replace(
            NL + "  approach: {path: direct-adjustment, why: 现有 epic 结构可承载}", "")
        self.write("diy-output/change-proposal.yaml", no_approach)
        r4 = self.check("--final")
        self.assertEqual(r4.returncode, 1, r4.stdout)
        self.assertIn("PENDING_DECISION", {x["code"] for x in json.loads(r4.stdout)["violations"]})

        # scope=major（规划层）却交接给 diy-sprint（backlog 层）→ 不一致
        mismatch = (PROPOSAL_YAML.replace("scope: moderate", "scope: major")
                    .replace("route: diy-epics-stories", "route: diy-sprint"))
        self.write("diy-output/change-proposal.yaml", mismatch)
        r5 = self.check("--final")
        self.assertEqual(r5.returncode, 1, r5.stdout)
        self.assertIn("SET_MISMATCH", {x["code"] for x in json.loads(r5.stdout)["violations"]})

    # trace: 任务书 §5 check（--id 单项过滤：只校验指定记录；未命中 → UNKNOWN_ID）
    def test_check_single_id_filter(self):
        body = PROPOSAL_YAML.split("proposals:" + NL, 1)[1].replace("revisions: []" + NL, "")
        second = body.replace("id: CP-001", "id: CP-002").replace("status: final", "status: done")
        self.write("diy-output/change-proposal.yaml",
                   PROPOSAL_YAML.replace("revisions: []" + NL, "") + second)
        r = self.check("--id", "CP-001")
        self.assertEqual(r.returncode, 0, r.stdout)  # 坏的第二条被过滤掉
        r2 = self.check("--id", "CP-002")
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertIn("ENUM_INVALID", {x["code"] for x in json.loads(r2.stdout)["violations"]})
        r3 = self.check("--id", "CP-009")
        self.assertEqual(r3.returncode, 1, r3.stdout)
        self.assertIn("UNKNOWN_ID", {x["code"] for x in json.loads(r3.stdout)["violations"]})

    # trace: 任务书 §2.5 用例 3（缺文件 → 结构化违规，不 Traceback）
    def test_check_missing_file_is_structured(self):
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertNotIn("Traceback", r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual(data["violations"][0]["code"], "MISSING_FILE")
        self.assertEqual(data["counts"]["proposals"], 0)


class SkillContractTests(unittest.TestCase):
    """用例 9：SKILL.md 契约冒烟（冻结文本逐字 + 终门句指向本技能引擎 + 写权边界）。"""

    def read_skill(self):
        if not os.path.isfile(SKILL_MD):
            self.skipTest("SKILL.md 尚未交付")
        with io.open(SKILL_MD, encoding="utf-8") as f:
            return f.read()

    # trace: 任务书 §2.1（冻结实例句逐字；md5 口径同 frozen-texts §3 复现命令）
    def test_instance_sentence_is_frozen_verbatim(self):
        raw = self.read_skill()
        m = re.search(r"Instance resolution \(FR-4\.5/D-9\)[^\r\n]*", raw)
        self.assertTrue(m, "SKILL.md 缺实例解析样板句")
        frag = m.group(0)
        self.assertEqual(len(frag), 233, "实例句字符数偏离冻结文本（233）")
        self.assertEqual(hashlib.md5((frag + NL).encode("utf-8")).hexdigest(), INSTANCE_MD5,
                         "实例句与冻结文本不一致：%s" % frag)

    # trace: 任务书 §2.1（写作纪律块逐字；md5 口径同 frozen-texts §3 复现命令）
    def test_writing_discipline_block_is_frozen_verbatim(self):
        raw = self.read_skill()
        m = re.search(r"^- \*\*Writing discipline\.[^\r\n]*", raw, re.M)
        self.assertTrue(m, "SKILL.md 缺写作纪律块")
        frag = m.group(0)
        self.assertEqual(len(frag), 497, "纪律块字符数偏离冻结文本（497）")
        self.assertEqual(hashlib.md5((frag + NL).encode("utf-8")).hexdigest(), DISCIPLINE_MD5,
                         "纪律块与冻结文本不一致：%s" % frag)

    # trace: 任务书 §5/#11/#12（终门句指向 change_proposal.py check --final；渲染静默；
    #        读一条加载一条；只出提案不改真源）
    def test_final_gate_points_to_engine(self):
        skill = self.read_skill()
        self.assertIn("change_proposal.py", skill, "终门句未指向领域引擎")
        self.assertIn("check --final", skill, "终门句缺 check --final")
        self.assertIn("--json", skill, "终门句缺 --json 回执")
        self.assertIn("collect", skill, "激活段未接线 collect")
        self.assertIn("never batch-load", skill, "缺读取成本纪律")
        self.assertIn("viewer.py", skill, "缺渲染静默命令")
        self.assertIn("never edit", skill, "缺写权边界声明")
        self.assertNotIn("bmad-help", skill, "不得引用不存在的技能")


if __name__ == "__main__":
    unittest.main()
