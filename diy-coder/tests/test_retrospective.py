# -*- coding: utf-8 -*-
"""diy-retrospective 确定性引擎 e2e 测试（B2 批 W2，任务书 §2.5/§4）。

覆盖：
- 用例 1：门禁拒绝（上游非 final / 目标 epic 不存在 / 无 done story）→ exit 1 +
          结构化拒绝 + 路由 + 零产出
- 用例 2：collect 指标守恒（stories 完成度 / loop rounds 合计 / blocked / augment fail /
          bug 三分类按 epic 归属）；epic 未收尾 → 警告 + 不拒
- 用例 3：collect 回带前一份 retro 的 action_items（prev_actions）+ 下一 epic 与共享 FR
- 用例 4：check 合法记录 --final exit 0 唯一放行；--output-dir 必填（用法错误 exit 2）
- 用例 5：check 违规路径（action item 缺 owner / evidence 悬空 UNKNOWN_ID / epic 悬空 /
          metrics 与集合真值不符 SET_MISMATCH / 枚举越界 / 零假设 / readiness 五键）
- 用例 6：SKILL.md 契约冒烟（冻结实例句 md5 + 写作纪律块 md5 + 终门句指向本技能引擎）
夹具全部落 tempdir 自建；不读写本仓库真实 diy-output。
运行：cd diy-coder && python -m unittest discover -s tests -p "test_retrospective.py" -v
"""
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.join(HERE, "..", "skills", "diy-retrospective")
ENGINE = os.path.join(SKILL_DIR, "scripts", "retrospective.py")
SKILL_MD = os.path.join(SKILL_DIR, "SKILL.md")
NL = chr(10)

# 冻结文本校验值（batch4/frozen-texts.md §1/§2：逐字复制，md5 口径 = 文本 + 行尾 LF）
INSTANCE_MD5 = "5445f98bc4d4821e6888b89406a97eac"
DISCIPLINE_MD5 = "f1b3b6fbb528f0cfab31f3196b3547ae"

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
    "- id: E-2",
    "  title: 史诗二",
    "  goal: 用户能完成第二件事",
    "  feature_refs: [F-2]",
    "  status: pending",
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
    "    refs: [FR-1.1]",
    "  status: done",
    "- id: S-2",
    "  epic: E-1",
    "  title: 故事二",
    "  narrative: 作为使用者，我希望完成第二件事",
    "  acceptance_criteria:",
    "  - id: AC-2.1",
    "    given: 前置",
    "    when: 动作",
    "    then: 结果",
    "    refs: [FR-1.2]",
    "  status: done",
    "- id: S-3",
    "  epic: E-1",
    "  title: 故事三",
    "  narrative: 作为使用者，我希望完成第三件事",
    "  acceptance_criteria:",
    "  - id: AC-3.1",
    "    given: 前置",
    "    when: 动作",
    "    then: 结果",
    "    refs: [FR-1.3]",
    "  status: in-progress",
    "- id: S-4",
    "  epic: E-2",
    "  title: 故事四",
    "  narrative: 作为使用者，我希望完成第四件事",
    "  acceptance_criteria:",
    "  - id: AC-4.1",
    "    given: 前置",
    "    when: 动作",
    "    then: 结果",
    "    refs: [FR-1.1]",
    "  status: done",
]) + NL

SPRINT_YAML = NL.join([
    "project:",
    "  name: mini",
    "  status: final",
    "  created: '2026-01-01'",
    "  updated: '2026-02-04'",
    "tasks:",
    "- story: S-1",
    "  status: done",
    "  test_refs: [TC-1.1.1]",
    "  loop: {at: '2026-02-01', rounds: 2, outcome: done}",
    "- story: S-2",
    "  status: done",
    "  test_refs: [TC-2.1.1]",
    "  augment: fail",
    "  loop: {at: '2026-02-02', rounds: 1, outcome: done}",
    "- story: S-3",
    "  status: blocked",
    "  test_refs: []",
    "  blocked_reason: 'AC-3.1 无用例（decision: pending）'",
    "  loop: {at: '2026-02-03', rounds: 3, outcome: blocked}",
    "- story: S-4",
    "  status: done",
    "  test_refs: [TC-4.1.1]",
    "  loop: {at: '2026-02-04', rounds: 4, outcome: done}",
]) + NL

BUG_LOG_YAML = NL.join([
    "project:",
    "  name: mini",
    "  created: '2026-01-01'",
    "  updated: '2026-02-05'",
    "bugs:",
    "- id: BUG-001",
    "  date: '2026-02-05'",
    "  source: dev",
    "  story: S-1",
    "  class: functional",
    "  subclass: state",
    "  type: 双写状态不同步",
    "  symptom: 症状一",
    "  root_cause: 根因一",
    "  trigger: 触发一",
    "  fix: 修复一",
    "  prevention: 预防一",
    "  pattern: 模式一",
    "- id: BUG-002",
    "  date: '2026-02-05'",
    "  source: audit",
    "  story: S-2",
    "  class: non-functional",
    "  subclass: reliability",
    "  type: 未知形态无降级",
    "  symptom: 症状二",
    "  root_cause: 根因二",
    "  trigger: 触发二",
    "  fix: 修复二",
    "  prevention: 预防二",
    "  pattern: 模式二",
    "- id: BUG-003",
    "  date: '2026-02-05'",
    "  source: dev",
    "  story: S-4",
    "  class: functional",
    "  subclass: logic",
    "  type: 分支漏判",
    "  symptom: 症状三",
    "  root_cause: 根因三",
    "  trigger: 触发三",
    "  fix: 修复三",
    "  prevention: 预防三",
    "  pattern: 模式三",
]) + NL

TEST_PLAN_YAML = NL.join([
    "project:",
    "  name: mini",
    "  status: final",
    "  created: '2026-01-01'",
    "  updated: '2026-02-04'",
    "test_cases:",
    "- id: TC-1.1.1",
    "  title: 用例一",
    "  ac: AC-1.1",
    "  type: unit",
    "  priority: P0",
    "  technique: boundary",
    "  kill_target: 边界错一",
    "  status: pass",
    "  steps: [步骤]",
    "- id: TC-2.1.1",
    "  title: 用例二",
    "  ac: AC-2.1",
    "  type: unit",
    "  priority: P0",
    "  technique: equivalence",
    "  kill_target: 等价类错",
    "  status: pass",
    "  steps: [步骤]",
    "- id: TC-4.1.1",
    "  title: 用例四",
    "  ac: AC-4.1",
    "  type: unit",
    "  priority: P0",
    "  technique: boundary",
    "  kill_target: 边界错四",
    "  status: pass",
    "  steps: [步骤]",
    "static_checks: []",
    "coverage_gaps:",
    "- ac: AC-3.1",
    "  story: S-3",
    "  reason: story 未 done",
    "  decision: pending",
]) + NL

RETRO_YAML = NL.join([
    "project:",
    "  name: mini",
    "  created: '2026-01-01'",
    "  updated: '2026-02-10'",
    "retros:",
    "- id: RT-001",
    "  epic: E-1",
    "  status: final",
    "  date: '2026-02-10'",
    "  partial: true",
    "  metrics:",
    "    stories_total: 3",
    "    stories_done: 2",
    "    rounds_total: 6",
    "    blocked_count: 1",
    "    augment_fail: 1",
    "    bugs: {functional: 1, non-functional: 1}",
    "  patterns:",
    "  - {theme: 状态双写反复出现, evidence: [S-1, BUG-001], count: 2}",
    "  wins: [回归证据补跑形成机制]",
    "  challenges: [用例缺口让队列任务阻塞]",
    "  insights: [状态真源必须单一]",
    "  action_items:",
    "  - {id: AI-001, action: 补齐 AC-3.1 的用例, owner: 用户, done_when: S-3 恢复 pending,"
    " category: process}",
    "  prep_items:",
    "  - {item: 建 e2e 冒烟链, class: critical, owner: 用户, effort: 中}",
    "  critical_path:",
    "  - {item: 补齐 AC-3.1 用例, why: 否则下一 epic 起始任务被门阻塞, owner: 用户}",
    "  readiness:",
    "    testing: 2 个故事通过回归，AC-3.1 仍无用例",
    "    deployment: 尚未部署",
    "    acceptance: 用户已口头接受",
    "    tech_health: 无悬空引用",
    "    blockers: AC-3.1 用例缺口待补",
    "  next_epic: {id: E-2, exists: true, dependencies: [共用 FR-1.1 的校验逻辑]}",
    "revisions: []",
]) + NL

# 上一份 retro（供 collect --epic E-2 的 prev_actions 回带用例）
PREV_RETRO_YAML = NL.join([
    "project:",
    "  name: mini",
    "  created: '2026-01-01'",
    "  updated: '2026-02-10'",
    "retros:",
    "- id: RT-001",
    "  epic: E-1",
    "  status: final",
    "  date: '2026-02-10'",
    "  partial: false",
    "  metrics:",
    "    stories_total: 3",
    "    stories_done: 2",
    "    rounds_total: 6",
    "    blocked_count: 1",
    "    augment_fail: 1",
    "    bugs: {functional: 1, non-functional: 1}",
    "  patterns: []",
    "  wins: [w]",
    "  challenges: [c]",
    "  insights: [i]",
    "  action_items:",
    "  - {id: AI-001, action: 补齐 AC-3.1 的用例, owner: 用户, done_when: S-3 恢复 pending,"
    " category: process}",
    "  prep_items: []",
    "  critical_path: []",
    "  readiness:",
    "    testing: t",
    "    deployment: d",
    "    acceptance: a",
    "    tech_health: h",
    "    blockers: b",
    "  next_epic: {id: E-2, exists: true, dependencies: []}",
    "revisions: []",
]) + NL


def run_engine(args):
    return subprocess.run([sys.executable, ENGINE] + args,
                          capture_output=True, text=True, encoding="utf-8")


class EngineCase(unittest.TestCase):
    """tmp 项目根 + diy-output 目录的公共夹具。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="retrospective-")
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

    def write_inputs(self, epics=EPICS_YAML, stories=STORIES_YAML, sprint=SPRINT_YAML,
                     bug_log=BUG_LOG_YAML, test_plan=TEST_PLAN_YAML):
        self.write("diy-output/epics.yaml", epics)
        self.write("diy-output/stories.yaml", stories)
        self.write("diy-output/sprint.yaml", sprint)
        self.write("diy-output/bug-log.yaml", bug_log)
        self.write("diy-output/test-plan.yaml", test_plan)

    def collect(self, *extra):
        return run_engine(["collect", "--project-root", self.root,
                           "--output-dir", self.out, "--json"] + list(extra))

    def check(self, *extra):
        return run_engine(["check", "--project-root", self.root,
                           "--output-dir", self.out, "--json"] + list(extra))

    def out_files(self):
        return sorted(os.listdir(self.out))


class GateTests(EngineCase):

    # trace: 任务书 §4 门禁（目标 epic 不存在 → 零产出退出 + 路由）
    def test_gate_refuses_unknown_epic_with_zero_output(self):
        self.write_inputs()
        r = self.collect("--epic", "E-9")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertNotIn("Traceback", r.stderr)
        data = json.loads(r.stdout)
        self.assertFalse(data["ok"])
        self.assertEqual([x["code"] for x in data["violations"]], ["UNKNOWN_ID"])
        self.assertTrue(data["gate"]["route"])
        self.assertIn("diy-epics-stories", data["gate"]["route"])
        self.assertNotIn("retrospective.yaml", self.out_files(), "拒绝路径不得产出产物")

    # trace: 任务书 §4 门禁（epics/stories 须 project.status: final）
    def test_gate_refuses_non_final_upstream(self):
        self.write_inputs(epics=EPICS_YAML.replace("status: final", "status: draft", 1))
        r = self.collect("--epic", "E-1")
        self.assertEqual(r.returncode, 1, r.stdout)
        data = json.loads(r.stdout)
        self.assertFalse(data["ok"])
        self.assertIn("STATUS_MISMATCH", {x["code"] for x in data["violations"]})
        self.assertNotIn("retrospective.yaml", self.out_files())

    # trace: 任务书 §4 门禁（epic 无 done story → 拒；上游缺失 → 拒）
    def test_gate_refuses_epic_without_done_story(self):
        self.write_inputs(stories=STORIES_YAML.replace("  status: done", "  status: pending"))
        r = self.collect("--epic", "E-1")
        self.assertEqual(r.returncode, 1, r.stdout)
        data = json.loads(r.stdout)
        self.assertIn("EMPTY_FIELD", {x["code"] for x in data["violations"]})
        self.write_inputs()
        os.remove(os.path.join(self.out, "stories.yaml"))
        r2 = self.collect("--epic", "E-1")
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertIn("MISSING_FILE", {x["code"] for x in json.loads(r2.stdout)["violations"]})

    # trace: 任务书 §2.2（引擎不做实例解析/目录推导：--output-dir 必填；--epic 必填）
    def test_arguments_are_mandatory(self):
        self.write_inputs()
        r = run_engine(["collect", "--project-root", self.root, "--json"])
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        r2 = run_engine(["check", "--project-root", self.root, "--json"])
        self.assertEqual(r2.returncode, 2, r2.stdout + r2.stderr)


class CollectTests(EngineCase):

    # trace: 任务书 §4 collect（机械采集：完成度 / rounds 合计 / blocked / augment / bug 归属）
    def test_collect_metrics_conservation(self):
        self.write_inputs()
        r = self.collect("--epic", "E-1")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertTrue(data["ok"])
        self.assertTrue(data["gate"]["passed"])
        self.assertEqual(data["epic"], "E-1")
        self.assertEqual(data["metrics"], {
            "stories_total": 3, "stories_done": 2, "rounds_total": 6,
            "blocked_count": 1, "augment_fail": 1,
            "bugs": {"functional": 1, "non-functional": 1}})
        self.assertEqual(data["stories"]["total"], 3)
        self.assertEqual(data["stories"]["done"], 2)
        self.assertEqual([b["id"] for b in data["bugs"]], ["BUG-001", "BUG-002"])
        self.assertEqual(data["coverage"]["acs"], 3)
        self.assertEqual(data["coverage"]["covered"], 2)
        self.assertEqual(data["coverage"]["gaps"], ["AC-3.1"])
        self.assertEqual(data["next_epic"]["id"], "E-2")
        self.assertTrue(data["next_epic"]["exists"])
        self.assertEqual(data["next_epic"]["shared_frs"], ["FR-1.1"])
        # epic 未收尾：警告（partial 分流交会话），不拒
        self.assertIn("PENDING_DECISION", {w["code"] for w in data["warnings"]})
        self.assertEqual(data["counts"]["rounds"], 6)
        self.assertNotIn("retrospective.yaml", self.out_files(), "采集只读，不写产物")

    # trace: 任务书 §4 collect（前一份 retro 的 action_items 回带 + 首份 retro 判定）
    def test_collect_carries_previous_actions(self):
        self.write_inputs()
        self.write("diy-output/retrospective.yaml", PREV_RETRO_YAML)
        r = self.collect("--epic", "E-2")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertFalse(data["first_retro"])
        self.assertEqual(len(data["prev_actions"]), 1)
        prev = data["prev_actions"][0]
        self.assertEqual((prev["retro"], prev["id"], prev["category"]),
                         ("RT-001", "AI-001", "process"))
        self.assertTrue(prev["action"] and prev["owner"] and prev["done_when"])
        # 无 retro 记录时 → 首份 retro，不报错
        os.remove(os.path.join(self.out, "retrospective.yaml"))
        r2 = self.collect("--epic", "E-2")
        data2 = json.loads(r2.stdout)
        self.assertTrue(data2["first_retro"])
        self.assertEqual(data2["prev_actions"], [])

    # trace: 任务书 §4 collect（sprint/bug-log 缺席 → 结构化 warning 降级，不崩）
    def test_collect_degrades_without_optional_sources(self):
        self.write_inputs()
        os.remove(os.path.join(self.out, "sprint.yaml"))
        os.remove(os.path.join(self.out, "bug-log.yaml"))
        r = self.collect("--epic", "E-1")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual([w["code"] for w in data["warnings"]],
                         ["MISSING_FILE", "MISSING_FILE", "PENDING_DECISION"])
        self.assertEqual(data["metrics"]["rounds_total"], 0)
        self.assertEqual(data["metrics"]["blocked_count"], 0)
        self.assertEqual(data["metrics"]["bugs"], {"functional": 0, "non-functional": 0})


class CheckValidationTests(EngineCase):

    # trace: 任务书 §2.5 用例 3（合法记录 --final exit 0 唯一放行）
    def test_check_final_legal_record_passes(self):
        self.write_inputs()
        self.write("diy-output/retrospective.yaml", RETRO_YAML)
        r = self.check("--final")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertTrue(data["ok"])
        self.assertEqual(data["violations"], [])
        self.assertEqual(data["counts"]["retros"], 1)
        self.assertEqual(data["counts"]["action_items"], 1)

    # trace: 任务书 §4 check（action item 完整性 + category 枚举）
    def test_check_action_item_completeness(self):
        self.write_inputs()
        no_owner = RETRO_YAML.replace(", owner: 用户, done_when: S-3 恢复 pending",
                                      ", owner: '', done_when: S-3 恢复 pending")
        self.write("diy-output/retrospective.yaml", no_owner)
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        data = json.loads(r.stdout)
        self.assertIn("EMPTY_FIELD", {x["code"] for x in data["violations"]})
        self.assertTrue(any("owner" in x["where"] for x in data["violations"]))
        bad_cat = RETRO_YAML.replace("category: process}", "category: unknown}")
        self.write("diy-output/retrospective.yaml", bad_cat)
        r2 = self.check()
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertIn("ENUM_INVALID", {x["code"] for x in json.loads(r2.stdout)["violations"]})

    # trace: 任务书 §4 check（epic 引用解析 + patterns evidence 引用解析 S-x / BUG-0xx）
    def test_check_dangling_references(self):
        self.write_inputs()
        dangling = (RETRO_YAML
                    .replace("evidence: [S-1, BUG-001]", "evidence: [S-1, BUG-099]")
                    .replace("epic: E-1", "epic: E-9"))
        self.write("diy-output/retrospective.yaml", dangling)
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        codes = {x["code"] for x in json.loads(r.stdout)["violations"]}
        self.assertIn("UNKNOWN_ID", codes)
        data = json.loads(r.stdout)
        where = " ".join(x["where"] for x in data["violations"] if x["code"] == "UNKNOWN_ID")
        self.assertIn("epic", where)
        self.assertIn("evidence", where)

    # trace: 任务书 §4 check --final（metrics 与集合真值一致 SET_MISMATCH）
    def test_check_final_metrics_mismatch(self):
        self.write_inputs()
        self.write("diy-output/retrospective.yaml",
                   RETRO_YAML.replace("rounds_total: 6", "rounds_total: 5"))
        r = self.check("--final")
        self.assertEqual(r.returncode, 1, r.stdout)
        data = json.loads(r.stdout)
        self.assertIn("SET_MISMATCH", {x["code"] for x in data["violations"]})
        self.assertTrue(any("rounds_total" in x["msg"] for x in data["violations"]))

    # trace: 任务书 §4 check --final（零假设 / readiness 五键 / action_items 非空）
    def test_check_final_duties(self):
        self.write_inputs()
        assumption = RETRO_YAML.replace("wins: [回归证据补跑形成机制]",
                                        "wins: ['[ASSUMPTION] 回归证据补跑形成机制']")
        self.write("diy-output/retrospective.yaml", assumption)
        r = self.check("--final")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ASSUMPTION_PRESENT",
                      {x["code"] for x in json.loads(r.stdout)["violations"]})
        no_key = RETRO_YAML.replace(NL + "    blockers: AC-3.1 用例缺口待补", "")
        self.write("diy-output/retrospective.yaml", no_key)
        r2 = self.check("--final")
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertIn("EMPTY_FIELD", {x["code"] for x in json.loads(r2.stdout)["violations"]})
        no_actions = RETRO_YAML.replace(
            "  action_items:" + NL
            + "  - {id: AI-001, action: 补齐 AC-3.1 的用例, owner: 用户,"
              " done_when: S-3 恢复 pending, category: process}",
            "  action_items: []")
        self.write("diy-output/retrospective.yaml", no_actions)
        r3 = self.check("--final")
        self.assertEqual(r3.returncode, 1, r3.stdout)
        self.assertIn("EMPTY_FIELD", {x["code"] for x in json.loads(r3.stdout)["violations"]})

    # trace: 任务书 §4 check（prev_followup 枚举与引用 + 记录 ID 稳定格式）
    def test_check_prev_followup_and_record_id(self):
        self.write_inputs()
        with_followup = RETRO_YAML.replace(
            "  patterns:" + NL,
            "  prev_followup:" + NL
            + "  - {retro: RT-001, action: 上次承诺, status: done, evidence: S-2 证据}" + NL
            + "  patterns:" + NL)
        self.write("diy-output/retrospective.yaml", with_followup)
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        codes = [x["code"] for x in json.loads(r.stdout)["violations"]]
        self.assertIn("UNKNOWN_ID", codes)   # RT-001 即自身，不算上一份 → 悬空
        bad_status = with_followup.replace(
            "{retro: RT-001, action: 上次承诺, status: done",
            "{retro: RT-002, action: 上次承诺, status: maybe")
        self.write("diy-output/retrospective.yaml", bad_status)
        r2 = self.check()
        codes2 = {x["code"] for x in json.loads(r2.stdout)["violations"]}
        self.assertIn("ENUM_INVALID", codes2)
        bad_id = RETRO_YAML.replace("id: RT-001", "id: RT-1")
        self.write("diy-output/retrospective.yaml", bad_id)
        r3 = self.check()
        self.assertEqual(r3.returncode, 1, r3.stdout)
        self.assertIn("ENUM_INVALID", {x["code"] for x in json.loads(r3.stdout)["violations"]})

    # trace: 任务书 §2.5 用例 3（缺文件 → 结构化违规，不 Traceback）
    def test_check_missing_file_is_structured(self):
        self.write_inputs()
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertNotIn("Traceback", r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual(data["violations"][0]["code"], "MISSING_FILE")
        self.assertEqual(data["counts"]["retros"], 0)


class SkillContractTests(unittest.TestCase):
    """用例 6：SKILL.md 契约冒烟（冻结文本逐字 + 终门句指向本技能引擎）。"""

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

    # trace: 任务书 §2.1/#11/#12（终门句指向 retrospective.py；渲染静默；读一条加载一条）
    def test_final_gate_points_to_engine(self):
        skill = self.read_skill()
        self.assertIn("retrospective.py", skill, "终门句未指向领域引擎")
        self.assertIn("check --final", skill, "终门句缺 check --final")
        self.assertIn("--json", skill, "终门句缺 --json 回执")
        self.assertIn("collect --epic", skill, "激活段未接线 collect")
        self.assertIn("never batch-load", skill, "缺读取成本纪律")
        self.assertIn("viewer.py", skill, "缺渲染静默命令")
        self.assertNotIn("bmad-help", skill, "不得引用不存在的技能")
        self.assertNotIn("party-mode", skill, "不得引用不存在的技能")


if __name__ == "__main__":
    unittest.main()
