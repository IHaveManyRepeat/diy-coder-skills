# -*- coding: utf-8 -*-
"""diy-create-story 确定性引擎测试（任务书 §2.5 / §3）。

覆盖：
- 用例 1：门禁拒绝——stories.yaml 缺席 / 非 已定稿 → collect exit 1 + 零产出 + gate.route
- 用例 2：collect 目标 story 悬空 → UNKNOWN_ID + suggestions（story 选择降级为人工）
- 用例 3：collect 回执键与取值完整性（acs/tcs/prior/decisions/git/counts/gate）
- 用例 4：前序 story 取「编号最高且小于当前者」；首故事 prior 为 null
- 用例 5：VCS 不可用 → NO_VCS warning 降级，collect 仍 exit 0
- 用例 6：check --final 合法记录 exit 0
- 用例 7：更新 型 current_state 缺失 → EMPTY_FIELD
- 用例 8：更新 型 path 不存在 → MISSING_FILE
- 用例 9：story 引用悬空 → UNKNOWN_ID
- 用例 10：--final 义务（status / verify / [假设] / open_questions 闭合）
- 用例 11：同一 story 两条记录 → DUPLICATE_ID
- 用例 12：SKILL.md 契约冒烟（两段冻结文本逐字 md5 + 终门句指向本技能引擎）

夹具全部落 tempdir 自建；不读写本仓库真实 diy-output；git 相用改写 PATH 的空环境模拟 VCS 缺席。
运行：cd diy-coder && python -m unittest discover -s tests -p "test_story_context.py" -v
"""
import hashlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.join(HERE, "..", "skills", "diy-create-story",
                      "scripts", "story_context.py")
SKILL_MD = os.path.join(HERE, "..", "skills", "diy-create-story", "SKILL.md")
NL = chr(10)

# 冻结文本校验值（batch4/frozen-texts.md §1/§2；md5 口径 = 整行 + 行尾 LF）
INSTANCE_MD5 = "5445f98bc4d4821e6888b89406a97eac"
INSTANCE_LEN = 233
INSTANCE_ANCHOR = "Instance resolution (FR-4.5/D-9)"
WRITING_MD5 = "f1b3b6fbb528f0cfab31f3196b3547ae"
WRITING_LEN = 497
WRITING_ANCHOR = "- **Writing discipline."

STORIES_YAML = """\
project:
  name: mini
  status: 已定稿
  created: '2026-01-01'
  updated: '2026-09-14'
stories:
- id: S-1
  epic: E-1
  title: 一
  narrative: 作为开发者我希望甲以便乙
  acceptance_criteria:
  - id: AC-1.1
    given: 夹具
    when: 夹具
    then: 夹具
    refs: [FR-1.1]
  status: 已完成
- id: S-2
  epic: E-1
  title: 二
  narrative: 作为开发者我希望甲以便乙
  acceptance_criteria:
  - id: AC-2.1
    given: 夹具
    when: 夹具
    then: 夹具
    refs: [FR-1.1]
  status: 待审查
- id: S-3
  epic: E-1
  title: 三
  narrative: 作为开发者我希望甲以便乙
  acceptance_criteria:
  - id: AC-3.1
    given: 夹具
    when: 夹具
    then: 夹具
    refs: [FR-1.1]
    design_ref: P-1
  status: 待办
"""

STORIES_DRAFT_YAML = STORIES_YAML.replace("status: 已定稿", "status: 草稿", 1)

TEST_PLAN_YAML = """\
project:
  name: mini
  status: 已定稿
  created: '2026-01-01'
  updated: '2026-09-14'
test_cases:
- id: TC-2.1.1
  title: 二用例
  ac: AC-2.1
  type: 单元
  priority: P0
  technique: 边界
  kill_target: 夹具
  status: 待办
  steps: [一]
- id: TC-3.1.1
  title: 三用例
  ac: AC-3.1
  type: 单元
  priority: P0
  technique: 等价类
  kill_target: 夹具
  status: 待办
  steps: [一]
"""

SPRINT_YAML = """\
project:
  name: mini
  status: 已定稿
  created: '2026-01-01'
  updated: '2026-09-14'
tasks:
- story: S-1
  status: 已完成
  test_refs: []
  note: 回填：首故事完成
- story: S-2
  status: 待审查
  test_refs: [TC-2.1.1]
  note: 待评审；既有实现复用 src/app.py
- story: S-3
  status: 待办
  test_refs: [TC-3.1.1]
"""

ARCH_YAML = """\
project:
  name: mini
  status: 已定稿
  created: '2026-01-01'
  updated: '2026-09-14'
decisions:
- id: D-1
  title: 工作流载体
  decision: 夹具
  rationale: 夹具
  alternatives:
  - {option: 甲, why_not: 乙}
  affects: [FR-1.1]
  status: 已采纳
- id: D-2
  title: 状态机
  decision: 夹具
  rationale: 夹具
  alternatives:
  - {option: 甲, why_not: 乙}
  affects: [FR-1.2]
  status: 已采纳
"""

CONTEXT_YAML = """\
project:
  name: mini
  created: '2026-01-01'
  updated: '2026-09-14'
contexts:
- id: SC-001
  story: S-3
  status: 已定稿
  date: '2026-09-14'
  epic: E-1
  ac_refs: [AC-3.1]
  tc_refs: [TC-3.1.1]
  design_ref: P-1
  decisions: [D-1]
  files:
  - path: src/app.py
    action: 更新
    why: 接线新行为
    current_state: 当前只打印一行
    preserve: 既有输出格式不得改变
  - path: src/new_mod.py
    action: 新建
    why: AC-3.1 需要的新模块
  prior_story:
    ref: S-2
    carryover:
    - 'sprint S-2 note：既有实现复用 src/app.py'
  risks:
  - 旧路径回归
  verify:
  - python -m unittest discover -s tests -v
  open_questions: []
revisions: []
"""

APP_PY = "print('app')" + NL

# 重复记录夹具：同一 story 两条记录（故事键原位重写纪律的负例）
_RECORD_START = CONTEXT_YAML.index("- id: SC-001")
_REVISIONS_AT = CONTEXT_YAML.index("revisions:")
DUPLICATE_CONTEXT_YAML = (CONTEXT_YAML[:_REVISIONS_AT]
                          + CONTEXT_YAML[_RECORD_START:_REVISIONS_AT].replace("SC-001", "SC-002")
                          + CONTEXT_YAML[_REVISIONS_AT:])


def run_engine(args, env=None, cwd=None):
    return subprocess.run([sys.executable, ENGINE] + args,
                          capture_output=True, text=True, encoding="utf-8",
                          env=env, cwd=cwd)


class EngineCase(unittest.TestCase):
    """tmp 项目根 + diy-output 目录的公共夹具。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="storyctx-")
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
        with io.open(path, "w", encoding="utf-8", newline="") as f:
            f.write(content)
        return path

    def write_full_project(self):
        self.write("diy-output/stories.yaml", STORIES_YAML)
        self.write("diy-output/test-plan.yaml", TEST_PLAN_YAML)
        self.write("diy-output/sprint.yaml", SPRINT_YAML)
        self.write("diy-output/architecture.yaml", ARCH_YAML)
        self.write("src/app.py", APP_PY)

    def collect(self, story, *extra):
        return run_engine(["collect", "--story", story,
                           "--project-root", self.root,
                           "--output-dir", self.out, "--json"] + list(extra))

    def check(self, *extra):
        return run_engine(["check", "--project-root", self.root,
                           "--output-dir", self.out, "--json"] + list(extra))


class GateTests(EngineCase):
    """用例 1/2：门禁与目标解析的零产出拒绝。"""

    # trace: 任务书 §3 门禁（stories.yaml 缺席 → 零产出 + 路由）
    def test_refuses_when_stories_missing(self):
        r = self.collect("S-1")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertFalse(data["ok"])
        self.assertEqual([v["code"] for v in data["violations"]], ["MISSING_FILE"])
        self.assertIn("diy-epics-stories", data["gate"]["route"])
        self.assertFalse(os.path.exists(os.path.join(self.out, "story-context.yaml")),
                         "拒绝路径必须零产出")

    # trace: 任务书 §3 门禁（stories.yaml 未定稿 → STATUS_MISMATCH）
    def test_refuses_when_stories_not_final(self):
        self.write("diy-output/stories.yaml", STORIES_DRAFT_YAML)
        r = self.collect("S-1")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual([v["code"] for v in data["violations"]], ["STATUS_MISMATCH"])
        self.assertIn("diy-epics-stories", data["gate"]["route"])

    # trace: 任务书 §3 门禁（目标 story 不存在 → UNKNOWN_ID + 候选提示）
    def test_refuses_unknown_story_with_suggestions(self):
        self.write_full_project()
        r = self.collect("S-9")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual([v["code"] for v in data["violations"]], ["UNKNOWN_ID"])
        self.assertIn("S-3", data["suggestions"], "候选应为未完成（status 非 已完成）的 story")
        self.assertFalse(os.path.exists(os.path.join(self.out, "story-context.yaml")))


class CollectTests(EngineCase):
    """用例 3/4/5：collect 回执面。"""

    # trace: 任务书 §3 collect 回执
    def test_receipt_keys_and_values(self):
        self.write_full_project()
        r = self.collect("S-3")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        for key in ("ok", "command", "project_root", "output_dir", "story", "gate",
                    "acs", "tcs", "prior", "decisions", "git", "violations",
                    "warnings", "counts"):
            self.assertIn(key, data, "回执缺键 %s" % key)
        self.assertEqual([a["id"] for a in data["acs"]], ["AC-3.1"])
        self.assertEqual(data["acs"][0]["design_ref"], "P-1", "AC 携带的 design_ref 须透出")
        self.assertEqual([t["id"] for t in data["tcs"]], ["TC-3.1.1"])
        self.assertEqual([d["id"] for d in data["decisions"]], ["D-1", "D-2"])
        self.assertEqual(data["prior"]["ref"], "S-2")
        self.assertEqual(data["prior"]["story_status"], "待审查")
        self.assertIn("既有实现复用", data["prior"]["task"]["note"])
        self.assertTrue(data["gate"]["passed"])
        self.assertEqual(data["counts"]["acs"], 1)
        self.assertEqual(data["counts"]["tcs"], 1)

    # trace: 任务书 §3 collect（前序 story = 编号最高且小于当前者）
    def test_first_story_has_no_prior(self):
        self.write_full_project()
        r = self.collect("S-1")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertIsNone(data["prior"])

    # trace: 任务书 §3 collect（git 情报失败降级 warning，不崩溃）
    def test_git_unavailable_degrades_to_warning(self):
        self.write_full_project()
        env = dict(os.environ)
        env["PATH"] = ""
        r = run_engine(["collect", "--story", "S-3", "--project-root", self.root,
                        "--output-dir", self.out, "--json"], env=env)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertIn("git", data)
        self.assertFalse(data["git"]["available"])
        self.assertIn("NO_VCS", [w["code"] for w in data["warnings"]])

    # trace: 任务书 §3（optional 上游缺席仅 warning）
    def test_missing_optional_upstreams_warn_only(self):
        self.write("diy-output/stories.yaml", STORIES_YAML)
        r = self.collect("S-3")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        codes = [w["code"] for w in data["warnings"]]
        self.assertEqual(codes.count("MISSING_FILE"), 3, data["warnings"])
        self.assertEqual(data["tcs"], [])


class CheckTests(EngineCase):
    """用例 6-11：story-context.yaml 校验面。"""

    def setUp(self):
        super(CheckTests, self).setUp()
        self.write_full_project()

    def write_context(self, text):
        return self.write("diy-output/story-context.yaml", text)

    # trace: 任务书 §3 check（合法记录唯一放行）
    def test_check_accepts_valid_final_record(self):
        self.write_context(CONTEXT_YAML)
        r = self.check("--final")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertTrue(data["ok"])
        self.assertEqual(data["counts"]["contexts"], 1)
        self.assertEqual(data["violations"], [])

    # trace: 任务书 §3 check（更新 型 current_state 必填）
    def test_update_entry_missing_current_state(self):
        self.write_context(CONTEXT_YAML.replace("    current_state: 当前只打印一行" + NL, ""))
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual([v["code"] for v in data["violations"]], ["EMPTY_FIELD"])
        self.assertIn("current_state", data["violations"][0]["where"])

    # trace: 任务书 §3 check（更新 型 path 须存在）
    def test_update_entry_path_must_exist(self):
        self.write_context(CONTEXT_YAML.replace("path: src/app.py", "path: src/absent.py"))
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual([v["code"] for v in data["violations"]], ["MISSING_FILE"])
        self.assertIn("src/absent.py", data["violations"][0]["msg"])

    # trace: 任务书 §3 check（story 引用解析）
    def test_unknown_story_reference(self):
        self.write_context(CONTEXT_YAML.replace("story: S-3", "story: S-9"))
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual([v["code"] for v in data["violations"]], ["UNKNOWN_ID"])
        self.assertIn("S-9", data["violations"][0]["msg"])

    # trace: 任务书 §3 check（ac_refs ⊆ 该 story 的 AC；tc_refs 归属校验）
    def test_dangling_ac_and_tc_references(self):
        text = (CONTEXT_YAML.replace("ac_refs: [AC-3.1]", "ac_refs: [AC-2.1]")
                .replace("tc_refs: [TC-3.1.1]", "tc_refs: [TC-2.1.1]"))
        self.write_context(text)
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        codes = sorted(v["code"] for v in data["violations"])
        self.assertEqual(codes, ["SET_MISMATCH", "UNKNOWN_ID"])

    # trace: 任务书 §3 check（--final 附加义务）
    def test_final_duties(self):
        text = (CONTEXT_YAML
                .replace("  status: 已定稿", "  status: 草稿")
                .replace("  verify:" + NL + "  - python -m unittest discover -s tests -v",
                         "  verify: []")
                .replace("  risks:" + NL,
                         "  risks:" + NL + "  - '[假设] 待确认的回归面'" + NL)
                .replace("  open_questions: []",
                         "  open_questions:" + NL + "  - 是否需要兼容旧入口"))
        self.write_context(text)
        r = self.check("--final")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        codes = sorted(v["code"] for v in data["violations"])
        self.assertEqual(codes, ["ASSUMPTION_PRESENT", "EMPTY_FIELD",
                                 "PENDING_DECISION", "STATUS_MISMATCH"], data["violations"])

    # trace: 任务书 §3 check（open_questions 显式闭合可放行）
    def test_closed_open_question_passes_final(self):
        self.write_context(CONTEXT_YAML.replace(
            "  open_questions: []",
            "  open_questions:" + NL + "  - '[CLOSED] 兼容旧入口：用户裁定本期不做'"))
        r = self.check("--final")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    # trace: 任务书 §2.4（记录按 story 键原位重写：重复 story 拒绝）
    def test_duplicate_story_records(self):
        self.write_context(DUPLICATE_CONTEXT_YAML)
        r = self.check("--final")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertIn("DUPLICATE_ID", [v["code"] for v in data["violations"]])


class SkillContractTests(unittest.TestCase):
    """用例 12：SKILL.md 契约冒烟（交付物同批落盘，缺席即失败）。"""

    def read_skill(self):
        if not os.path.isfile(SKILL_MD):
            self.fail("SKILL.md 尚未交付：%s" % SKILL_MD)
        with io.open(SKILL_MD, encoding="utf-8", newline="") as f:
            return f.read().replace("\r\n", "\n")

    # trace: 任务书 §2.1（冻结实例句逐字；md5 口径同 frozen-texts §3）
    def test_instance_sentence_is_frozen_verbatim(self):
        raw = self.read_skill()
        line = [ln for ln in raw.split(NL) if INSTANCE_ANCHOR in ln]
        self.assertEqual(len(line), 1, "SKILL.md 缺实例解析样板句")
        frag = line[0][line[0].index(INSTANCE_ANCHOR):]
        self.assertEqual(len(frag), INSTANCE_LEN, "实例句字符数偏离冻结文本（233）")
        self.assertEqual(hashlib.md5((frag + NL).encode("utf-8")).hexdigest(), INSTANCE_MD5)

    # trace: 任务书 §2.1（写作纪律块逐字；md5 口径同 frozen-texts §3）
    def test_writing_discipline_block_is_frozen_verbatim(self):
        raw = self.read_skill()
        line = [ln for ln in raw.split(NL) if ln.startswith(WRITING_ANCHOR)]
        self.assertEqual(len(line), 1, "SKILL.md 缺写作纪律块")
        self.assertEqual(len(line[0]), WRITING_LEN, "纪律块字符数偏离冻结文本（497）")
        self.assertEqual(hashlib.md5((line[0] + NL).encode("utf-8")).hexdigest(), WRITING_MD5)

    # trace: 任务书 §2.1/§3（终门句指向本技能引擎；实例解析委托 diyc）
    def test_final_gate_points_to_engine(self):
        skill = self.read_skill()
        self.assertIn("story_context.py", skill, "终门句未指向领域引擎")
        self.assertIn("check --final", skill, "终门句缺 check --final")
        self.assertIn("--json", skill, "终门句缺 --json 回执")
        self.assertIn("diyc.py\" resolve", skill, "实例解析未委托 diyc.py resolve")


if __name__ == "__main__":
    unittest.main()
