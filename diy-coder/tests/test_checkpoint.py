# -*- coding: utf-8 -*-
"""diy-checkpoint-preview 确定性引擎 e2e 测试（P1 样板，任务书 §2.5）。

覆盖：
- 用例 1：target 级联命中 sprint.yaml 中 status=待审查 的任务（source=冲刺任务 + 候选字段）
- 用例 2：target 门禁拒绝（空项目 / 非 git / 显式 ref 不可解析）→ exit 1 + 结构化拒绝 + 零产出
- 用例 3：check --final 合法记录 exit 0；非法（decision 缺失 / 枚举外 label / 悬空 story）
          exit 1 且带对应 violation code
- 用例 4：SKILL.md 契约冒烟（母本 §1 中文定稿逐字 + 四段中文标题 + mode 枚举与引擎同源
          + 终门句指向 checkpoint.py check --final）
- 附加：自建临时 git 仓库的显式指定 / Git 提交层；空仓库无提交不崩溃；check 缺文件 MISSING_FILE

夹具全部落 tempdir 自建；不读写本仓库真实 diy-output；git 用例自建仓库，不依赖本机 git 状态。
运行：cd diy-coder && python -m unittest discover -s tests -v
"""
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.join(HERE, "..", "skills", "diy-checkpoint-preview",
                      "scripts", "checkpoint.py")
SKILL_MD = os.path.join(HERE, "..", "skills", "diy-checkpoint-preview", "SKILL.md")
NL = chr(10)

# 套件级句式母本（suite-texts.md §1 中文定稿，逐字）——2026-09-19 中文化轮：
# 英文原形（233 字符，md5 5445f98b…）随本技能转中文退役，改断中文定稿。
INSTANCE_ZH = ("实例解析（FR-4.5/D-9）由工具脚本执行：运行 "
               "`python \"{project-root}/.claude/skills/diy-tools/scripts/diyc.py\" "
               "resolve [--instance <name>] --json`，把回执里的 `output_dir` "
               "当作本次运行唯一的读写根目录。")
INSTANCE_EN_MARK = "Instance resolution (FR-4.5/D-9)"


def engine_modes():
    """引擎 MODES（契约：SKILL.md 的 mode 枚举与引擎同源，A-10 决策 2）。"""
    spec = importlib.util.spec_from_file_location("ckpt_engine_modes", ENGINE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return tuple(mod.MODES)

SPRINT_YAML = NL.join([
    "project:",
    "  name: mini",
    "  status: 已定稿",
    "  created: '2026-01-01'",
    "  updated: '2026-01-02'",
    "tasks:",
    "- story: S-1",
    "  status: 已完成",
    "  test_refs: []",
    "- story: S-2",
    "  status: 待审查",
    "  test_refs: []",
]) + NL

STORIES_YAML = NL.join([
    "project:",
    "  name: mini",
    "  status: 已定稿",
    "  created: '2026-01-01'",
    "  updated: '2026-01-02'",
    "stories:",
    "- id: S-1",
    "  title: 一",
    "  status: 已完成",
    "  acceptance_criteria: []",
    "- id: S-2",
    "  title: 二",
    "  status: 待审查",
    "  acceptance_criteria:",
    "  - id: AC-2.1",
    "    given: 夹具",
    "    when: 夹具",
    "    then: 夹具",
    "    refs: []",
]) + NL

CHECKPOINT_YAML = NL.join([
    "project:",
    "  name: mini",
    "  created: '2026-01-01'",
    "  updated: '2026-09-13'",
    "checkpoints:",
    "- id: CK-001",
    "  date: '2026-09-13'",
    "  change_type: commit",
    "  target:",
    "    ref: WORKTREE",
    "    source: Git 提交",
    "    story: S-2",
    "    inferred: false",
    "  mode: 裸提交",
    "  concerns:",
    "  - name: 变更候选定位",
    "    why: 门禁须确定钉住被审变更",
    "    sites:",
    "    - diy-coder/skills/diy-checkpoint-preview/scripts/checkpoint.py:1",
    "  risks:",
    "  - label: schema",
    "    where: diy-output/checkpoint.yaml checkpoints[0]",
    "    why: 新增产物形状需人工确认",
    "  observations:",
    "  - do: python checkpoint.py check --final --json",
    "    watch: exit 0",
    "    why: 唯一放行",
    "  decision: 批准",
    "  reason: 引擎与测试通过",
    "  next: 运行 diy-viewer 渲染",
    "  status: 已定稿",
    "revisions: []",
]) + NL


def run_engine(args):
    return subprocess.run([sys.executable, ENGINE] + args,
                          capture_output=True, text=True, encoding="utf-8")


class EngineCase(unittest.TestCase):
    """tmp 项目根 + diy-output 目录的公共夹具。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="ckpt-")
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

    def target(self, *extra):
        return run_engine(["target", "--project-root", self.root,
                           "--output-dir", self.out, "--json"] + list(extra))

    def check(self, *extra):
        return run_engine(["check", "--project-root", self.root,
                           "--output-dir", self.out, "--json"] + list(extra))

    def checkpoint_path(self):
        return os.path.join(self.out, "checkpoint.yaml")


class TargetCascadeTests(EngineCase):

    # trace: 任务书 §2.5 用例 1（级联 2 层：sprint review 任务）
    def test_target_cascade_hits_sprint_review_task(self):
        self.write("diy-output/sprint.yaml", SPRINT_YAML)
        self.write("diy-output/stories.yaml", STORIES_YAML)
        r = self.target()
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        data = json.loads(r.stdout)
        self.assertTrue(data["ok"])
        self.assertEqual(data["source"], "冲刺任务")
        self.assertEqual(data["counts"]["candidates"], 1)
        cand = data["candidates"][0]
        self.assertEqual(cand["story"], "S-2")
        self.assertEqual(cand["mode"], "仅规格")
        self.assertTrue(str(cand["spec"]).replace("\\", "/").endswith("stories.yaml"))
        # 级联短路：命中即停（BMAD step-01 语义），已查层留痕（诊断面）
        self.assertEqual([c["source"] for c in data["checked"]], ["显式指定", "冲刺任务"])
        self.assertTrue(data["checked"][1]["hit"])

    # trace: 任务书 §2.5 用例 2（门禁拒绝 + 零产出）
    def test_target_gate_refuses_with_zero_output(self):
        r = self.target()  # 空项目：无 sprint / 非 git / 无 --ref
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertNotIn("Traceback", r.stderr)
        data = json.loads(r.stdout)
        self.assertFalse(data["ok"])
        self.assertEqual(data["candidates"], [])
        self.assertTrue(data["reason"])
        self.assertEqual([x["code"] for x in data["violations"]], ["NO_TARGET"])
        self.assertFalse(os.path.exists(self.checkpoint_path()),
                         "门禁拒绝路径不得产出 checkpoint.yaml")
        self.assertFalse(os.listdir(self.out), "拒绝路径不得写任何文件")

    # trace: 任务书 §2.3（显式 ref 不可解析 → 结构化拒绝，不崩溃）
    def test_unresolvable_ref_is_structured_refusal(self):
        r = self.target("--ref", "HEAD")  # 非 git 目录
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertNotIn("Traceback", r.stderr)
        data = json.loads(r.stdout)
        self.assertFalse(data["ok"])
        self.assertEqual(data["candidates"], [])
        self.assertEqual(data["violations"][0]["code"], "NO_TARGET")
        self.assertIn("HEAD", data["reason"])
        self.assertFalse(os.path.exists(self.checkpoint_path()))

    # trace: 任务书 §2.3（引擎不做实例解析/目录推导：--output-dir 必填）
    def test_output_dir_is_mandatory(self):
        r = run_engine(["target", "--project-root", self.root, "--json"])
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        r2 = run_engine(["check", "--project-root", self.root, "--json"])
        self.assertEqual(r2.returncode, 2, r2.stdout + r2.stderr)


class CheckValidationTests(EngineCase):

    # trace: 任务书 §2.5 用例 3（合法记录 exit 0 唯一放行）
    def test_check_final_legal_record_passes(self):
        self.write("diy-output/checkpoint.yaml", CHECKPOINT_YAML)
        self.write("diy-output/sprint.yaml", SPRINT_YAML)
        self.write("diy-output/stories.yaml", STORIES_YAML)
        r = self.check("--final")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertTrue(data["ok"])
        self.assertEqual(data["violations"], [])
        self.assertEqual(data["counts"]["checkpoints"], 1)
        self.assertEqual(data["counts"]["by_decision"], {"批准": 1})
        self.assertEqual(data["counts"]["by_source"], {"Git 提交": 1})

    # trace: 任务书 §2.5 用例 3（三类非法各带 violation code）
    def test_check_final_reports_violation_codes(self):
        self.write("diy-output/sprint.yaml", SPRINT_YAML)
        self.write("diy-output/stories.yaml", STORIES_YAML)
        cases = [
            ("PENDING_DECISION", CHECKPOINT_YAML.replace("  decision: 批准" + NL, "")),
            ("ENUM_INVALID", CHECKPOINT_YAML.replace("label: schema", "label: performance")),
            ("UNKNOWN_ID", CHECKPOINT_YAML.replace("story: S-2", "story: S-99")),
        ]
        for code, text in cases:
            self.write("diy-output/checkpoint.yaml", text)
            r = self.check("--final")
            self.assertEqual(r.returncode, 1, "%s: %s" % (code, r.stdout + r.stderr))
            data = json.loads(r.stdout)
            self.assertFalse(data["ok"])
            self.assertIn(code, {x["code"] for x in data["violations"]},
                          "%s 未报出：%s" % (code, r.stdout))
            self.assertTrue(all(x.get("where") and x.get("msg")
                                for x in data["violations"]), r.stdout)

    # trace: 任务书 §2.1（record id 格式 CK-0nn / 重复 ID）
    def test_check_reports_id_shape_and_duplicates(self):
        bad_id = CHECKPOINT_YAML.replace("id: CK-001", "id: CK-1")
        self.write("diy-output/checkpoint.yaml", bad_id)
        self.write("diy-output/stories.yaml", STORIES_YAML)
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ENUM_INVALID", {x["code"] for x in json.loads(r.stdout)["violations"]})
        # 重复：同一条记录行落两份（CK ID 稳定不重用）
        body = (CHECKPOINT_YAML.split("checkpoints:" + NL, 1)[1]
                .replace("revisions: []" + NL, ""))
        dup = CHECKPOINT_YAML.replace("revisions: []" + NL, "") + body
        self.write("diy-output/checkpoint.yaml", dup)
        r2 = self.check()
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertIn("DUPLICATE_ID", {x["code"] for x in json.loads(r2.stdout)["violations"]})

    # trace: 任务书 §7.2（target.inferred 由引擎输出、schema 承载；类型须为布尔）
    def test_check_validates_target_inferred_type(self):
        self.write("diy-output/stories.yaml", STORIES_YAML)
        self.write("diy-output/checkpoint.yaml", CHECKPOINT_YAML)  # 夹具带 inferred: false
        r = self.check("--final")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        bad = CHECKPOINT_YAML.replace("    inferred: false", "    inferred: maybe")
        self.write("diy-output/checkpoint.yaml", bad)
        r2 = self.check()
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertIn("ENUM_INVALID", {x["code"] for x in json.loads(r2.stdout)["violations"]})

    # trace: 任务书 §8.3（change_type 开放字符串：可选、出现时非空，禁封闭枚举）
    def test_check_change_type_is_open_but_not_empty(self):
        self.write("diy-output/stories.yaml", STORIES_YAML)
        free = CHECKPOINT_YAML.replace("change_type: commit", "change_type: 认证重构")
        self.write("diy-output/checkpoint.yaml", free)
        r = self.check("--final")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)  # 自由文本不判越界
        absent = CHECKPOINT_YAML.replace("  change_type: commit" + NL, "")
        self.write("diy-output/checkpoint.yaml", absent)
        r2 = self.check("--final")  # 可选：缺席合法
        self.assertEqual(r2.returncode, 0, r2.stdout + r2.stderr)
        blank = CHECKPOINT_YAML.replace("change_type: commit", "change_type: ''")
        self.write("diy-output/checkpoint.yaml", blank)
        r3 = self.check()
        self.assertEqual(r3.returncode, 1, r3.stdout)
        self.assertIn("EMPTY_FIELD", {x["code"] for x in json.loads(r3.stdout)["violations"]})

    # trace: 任务书 §2.2（discuss 不落 final）
    def test_check_final_rejects_discuss_decision(self):
        text = CHECKPOINT_YAML.replace("decision: 批准", "decision: 讨论")
        self.write("diy-output/checkpoint.yaml", text)
        self.write("diy-output/stories.yaml", STORIES_YAML)
        r = self.check("--final")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("STATUS_MISMATCH",
                      {x["code"] for x in json.loads(r.stdout)["violations"]})

    # trace: 任务书 §2.3（缺文件 → 结构化违规，不 Traceback）
    def test_check_missing_file_is_structured(self):
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertNotIn("Traceback", r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual(data["violations"][0]["code"], "MISSING_FILE")
        self.assertEqual(data["counts"]["checkpoints"], 0)
        # 损坏 YAML 同样结构化
        self.write("diy-output/checkpoint.yaml", "checkpoints: [" + NL)
        r2 = self.check()
        self.assertEqual(r2.returncode, 1)
        self.assertNotIn("Traceback", r2.stderr)
        self.assertEqual(json.loads(r2.stdout)["violations"][0]["code"], "UNPARSABLE_YAML")

    # trace: 任务书 §2.1（起草期宽松：decision 未定 / status: 草稿 合法）
    def test_check_draft_record_is_lenient(self):
        text = (CHECKPOINT_YAML
                .replace("  decision: 批准" + NL, "")
                .replace("  status: 已定稿", "  status: 草稿"))
        self.write("diy-output/checkpoint.yaml", text)
        self.write("diy-output/stories.yaml", STORIES_YAML)
        r = self.check()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(json.loads(r.stdout)["violations"], [])


def git_available():
    return shutil.which("git") is not None


@unittest.skipUnless(git_available(), "git 不可用")
class GitLayerTests(EngineCase):
    """git 层：自建临时仓库（不依赖本机 git 状态）。"""

    def git(self, *args):
        return subprocess.run(["git", "-C", self.root] + list(args),
                              capture_output=True, text=True, encoding="utf-8")

    def setUp(self):
        super().setUp()
        if self.git("init", "-q").returncode != 0:
            self.skipTest("临时 git 仓库初始化失败")
        if self.git("rev-parse", "--is-inside-work-tree").returncode != 0:
            self.skipTest("git 无法识别临时仓库（环境限制）")

    def commit(self, message):
        self.git("add", "-A")
        return self.git("-c", "user.email=ckpt@example.com",
                        "-c", "user.name=ckpt", "commit", "-q", "-m", message)

    # trace: 任务书 §2.3（无提交 / 无 diff 不得崩溃）
    def test_empty_repo_yields_no_candidate(self):
        r = self.target()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertNotIn("Traceback", r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual(data["candidates"], [])
        self.assertEqual(data["violations"][0]["code"], "NO_TARGET")

    # trace: 任务书 §2.3（级联 3 层：git 工作区 / HEAD）
    def test_git_layer_prefers_worktree_then_head(self):
        self.write("src/app.py", "print(1)" + NL)
        self.commit("init")
        r = self.target()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        head = json.loads(r.stdout)
        self.assertEqual(head["source"], "Git 提交")
        self.assertEqual(head["mode"], "裸提交")
        self.assertRegex(head["ref"], r"^[0-9a-f]{7,}$")
        self.assertIsInstance(head["diff_stat"], dict)
        # 工作区改动优先于 HEAD
        self.write("src/app.py", "print(2)" + NL)
        r2 = self.target()
        self.assertEqual(r2.returncode, 0, r2.stdout + r2.stderr)
        wt = json.loads(r2.stdout)
        self.assertEqual(wt["ref"], "WORKTREE")
        self.assertGreaterEqual(wt["diff_stat"]["files"], 1)

    # trace: 任务书 §7.2（bare-commit 意图源=提交信息；原文阈值 under 10 words）
    def test_terse_commit_message_is_flagged_inferred(self):
        self.write("src/app.py", "print(1)" + NL)
        self.commit("one two three four five six seven eight nine")  # 9 词 < 10
        data = json.loads(self.target().stdout)
        cand = data["candidates"][0]
        self.assertEqual(cand["mode"], "裸提交")
        self.assertIs(cand["inferred"], True, data)
        self.assertTrue(cand["inferred_reason"], data)
        self.assertIs(data["inferred"], True)

    # trace: 任务书 §7.2（阈值边界：恰好 10 词不算 terse）
    def test_commit_message_at_threshold_is_not_inferred(self):
        self.write("src/app.py", "print(1)" + NL)
        self.commit("one two three four five six seven eight nine ten")  # 10 词
        data = json.loads(self.target().stdout)
        cand = data["candidates"][0]
        self.assertIs(cand["inferred"], False, data)
        self.assertIsNone(cand["inferred_reason"])
        # 工作区未提交改动无单一提交信息 → 不可判定（null，而非 false）
        self.write("src/app.py", "print(2)" + NL)
        wt = json.loads(self.target().stdout)["candidates"][0]
        self.assertEqual(wt["ref"], "WORKTREE")
        self.assertIsNone(wt["inferred"], wt)
        self.assertTrue(wt["inferred_reason"], wt)

    # trace: 任务书 §7.2（显式 ref 同为 bare-commit，判定同源）
    def test_explicit_commit_ref_carries_intent_flag(self):
        self.write("src/app.py", "print(1)" + NL)
        self.commit("tight fix")
        data = json.loads(self.target("--ref", "HEAD").stdout)
        self.assertIs(data["candidates"][0]["inferred"], True, data)

    # trace: 任务书 §2.3（级联 1 层：显式 ref）
    def test_explicit_ref_wins_over_sprint_and_git(self):
        self.write("src/app.py", "print(1)" + NL)
        self.commit("init")
        self.write("diy-output/sprint.yaml", SPRINT_YAML)
        self.write("diy-output/stories.yaml", STORIES_YAML)
        r = self.target("--ref", "HEAD")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual(data["source"], "显式指定")
        self.assertEqual(data["ref"], "HEAD")
        self.assertEqual(data["counts"]["candidates"], 1)


class SkillContractTests(unittest.TestCase):
    """用例 4：SKILL.md 契约冒烟（W2 交付物；缺席时 skip 待补）。"""

    def read_skill(self):
        if not os.path.isfile(SKILL_MD):
            self.skipTest("SKILL.md 尚未交付（W2 并行中）——用例 4 待补")
        with io.open(SKILL_MD, encoding="utf-8") as f:
            return f.read()

    # trace: 任务书 §2.4 / 母本 §1（实例解析句中文定稿逐字；英文原形已随中文化退役）
    def test_instance_sentence_is_mother_copy_verbatim(self):
        raw = self.read_skill()
        self.assertIn(INSTANCE_ZH, raw, "SKILL.md 缺母本 §1 中文定稿（逐字）")
        self.assertNotIn(INSTANCE_EN_MARK, raw, "已转中文定稿，仍残留英文原形")

    # trace: 中文化轮（薄主文件四段标题中文化；2026-09-19 政策）
    def test_four_sections_are_chinese(self):
        raw = self.read_skill()
        for section in ("## 激活时", "## 工作流", "## 结构", "## 规则"):
            self.assertIn(section, raw, "缺段 %s" % section)

    # trace: A-10 决策 2（`全程轨迹` 在本生态不可达：引擎 MODES 保留三值，
    #         技能侧枚举标「本生态不适用」；键路径以 schema/引擎为准）
    def test_mode_enum_matches_engine_and_marks_unreachable(self):
        raw = self.read_skill()
        for value in engine_modes():
            self.assertIn(value, raw, "SKILL.md 的 mode 枚举缺引擎值 %s" % value)
        self.assertIn("本生态不适用", raw, "`全程轨迹` 须标「本生态不适用」")

    # trace: 任务书 §2.4（终门句指向 checkpoint.py check --final）
    def test_final_gate_points_to_engine(self):
        skill = self.read_skill()
        self.assertIn("checkpoint.py", skill, "终门句未指向领域引擎")
        self.assertIn("check --final", skill, "终门句缺 check --final")
        self.assertIn("--json", skill, "终门句缺 --json 回执")


if __name__ == "__main__":
    unittest.main()
