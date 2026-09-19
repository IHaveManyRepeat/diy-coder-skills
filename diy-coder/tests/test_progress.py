# -*- coding: utf-8 -*-
"""diy-teach-me-testing 进度引擎测试（7 节课程 + 跨会话进度跟踪）。

覆盖（清单来源 = B3 任务书 §7「测试」）：
 1  init 建 7 节全 not-started + 建 `notes/` 目录（定义态/运行态分离，session id 与
    curriculum.yaml 对齐）
 2  init 无 `--role` 合法（`learner.role` 与 `learner.assessed` 均为 null，SS-001-70）
 3  init 已存在 → 拒绝（零覆盖，指引 resume）
 4  update 幂等：同节二次完成不重复计数（派生三式仍 1/14/2，追加一条重做修订）
 5  派生字段与真值一致（基准 = 裁定 2 三式）+ 手改派生字段 → check / status 报
    SET_MISMATCH
 6  check 检出 completed 无 notes / notes 越界 / notes 文件不在场
 7  check 检出 session 7 无 topics_explored（完成判据 = topics_explored >= min_topics）
 8  `update --learner` 置 assessed 后 check 通过；缺 experience 的画像被写通道拒绝；
    experience 越界 → ENUM_INVALID
 9  completion 门未满（或 summary.generated=false）拒绝 `--final`
10  `update --summary` 三道门（7/7、路径口径、文件在场）
11  status 仪表盘回执（含裁定 3 分流表直出的 entry_step）
12  契约冒烟（--json 单行 + 共同键齐全 + 写命令含 updated；无 --json 时末行汇总；
    --output-dir 必填 → exit 2）
13  SKILL.md 契约冒烟（母本 §1/§2 中文定稿逐字 + §3/§4/§5 锚串 + 终门句指向
    progress.py check --final + ≤90 行四段）
14  T-6 进度文件损坏的恢复路径（V 能力清点 2026-09-18，乙类功能性缺陷）：损坏检测 +
    status 分流回 init 步 + `init --recover` 先备份后重建 + 文件可用时拒绝 + 无文件时
    等同普通 init（恢复由引擎做，不破单一写通道）
15  T-1~T-5 教学内容落点契约（curriculum.yaml 主题 / steps 条文；防返工时静默丢失）
16  附带修正：A1 裁定（2026-09-18 删 [B] 双模式）后教学内容不得再教 [A] / [B] 词汇

夹具全部落 tempdir 自建；不读写本仓库真实 diy-output，不依赖本机 git 状态。
运行：cd diy-coder && python -m unittest discover -s tests -p "test_progress.py" -v
"""
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
import datetime

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.join(HERE, "..", "skills", "diy-teach-me-testing")
ENGINE = os.path.join(SKILL_DIR, "scripts", "progress.py")
SKILL_MD = os.path.join(SKILL_DIR, "SKILL.md")
NL = chr(10)

# 母本（suite-texts.md）中文定稿逐字（§1 / §2 整句整块）
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
CONFIG_ANCHOR = ("解析 `project.communication_language` / "
                 "`project.document_output_language` / `paths.output_dir`")
READ_ANCHOR = ("读取纪律：预载预算 = 本文件、上述配置与回执、`steps/` 下当前那一个文件"
               "——绝不批量预载；执行期读取以每个步骤开头的 `Read (input)` 行为唯一权威，"
               "**主文件不列举封闭清单**。")
RENDER_ANCHOR = "渲染是静默旁路——只写调用命令"

SESSION_IDS = list(range(1, 8))
STATUSES = ("not-started", "in-progress", "completed")


def run_engine(args, cwd=None):
    return subprocess.run([sys.executable, ENGINE] + args, capture_output=True,
                          text=True, encoding="utf-8", cwd=cwd)


def min_topics():
    """session 7 完成判据阈值（取自技能内 curriculum.yaml，不硬编码）。"""
    with io.open(os.path.join(SKILL_DIR, "curriculum.yaml"), encoding="utf-8") as f:
        data = yaml.safe_load(f)
    session = [s for s in data["sessions"] if s["id"] == 7][0]
    return session["min_topics"]


class EngineCase(unittest.TestCase):
    """tmp 项目根 + diy-output 目录的公共夹具。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="progress-")
        self.root = self.tmp.name
        self.out = os.path.join(self.root, "diy-output")
        os.makedirs(self.out, exist_ok=True)
        self.today = datetime.date.today().isoformat()

    def tearDown(self):
        self.tmp.cleanup()

    # ------------------------------------------------------------ 夹具与调用

    def write(self, rel, content):
        path = os.path.join(self.root, rel)
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with io.open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def read_text(self, path):
        with io.open(path, encoding="utf-8") as f:
            return f.read()

    def progress_path(self):
        return os.path.join(self.out, "learning-progress.yaml")

    def read_progress(self):
        with io.open(self.progress_path(), encoding="utf-8") as f:
            return yaml.safe_load(f)

    def write_progress(self, doc):
        with io.open(self.progress_path(), "w", encoding="utf-8") as f:
            yaml.safe_dump(doc, f, allow_unicode=True, sort_keys=False,
                           default_flow_style=False)

    def init(self, *extra):
        return run_engine(["init", "--project-root", self.root,
                           "--output-dir", self.out, "--json"] + list(extra))

    def status(self, *extra):
        return run_engine(["status", "--project-root", self.root,
                           "--output-dir", self.out, "--json"] + list(extra))

    def update(self, *extra):
        return run_engine(["update", "--project-root", self.root,
                           "--output-dir", self.out, "--json"] + list(extra))

    def check(self, *extra):
        return run_engine(["check", "--project-root", self.root,
                           "--output-dir", self.out, "--json"] + list(extra))

    def codes(self, result):
        return [item["code"] for item in json.loads(result.stdout)["violations"]]

    def notes_rel(self, session_id):
        return "notes/session-%02d.md" % session_id

    def write_notes(self, session_id, text="课堂笔记。"):
        return self.write(os.path.join("diy-output", self.notes_rel(session_id)), text)

    def write_summary(self, text="结业摘要。"):
        return self.write(os.path.join("diy-output", "completion-summary.md"), text)

    def complete(self, session_id, score=100, topics=None):
        """完成一节：先落 notes md（写通道要求文件在场），再 update --session。"""
        self.write_notes(session_id)
        extra = ["--session", str(session_id), "--status", "completed",
                 "--notes", self.notes_rel(session_id)]
        if score is not None:
            extra += ["--score", str(score)]
        if topics is not None:
            extra += ["--topics", str(topics)]
        result = self.update(*extra)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def complete_all(self):
        for sid in SESSION_IDS:
            score = None if sid == 7 else 100
            topics = min_topics() if sid == 7 else None
            self.complete(sid, score=score, topics=topics)


class InitTests(EngineCase):

    # trace: §7 测试 1（init 建 7 节全 not-started + 建 notes/ 目录）
    def test_init_creates_seven_sessions_and_notes_dir(self):
        r = self.init()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertTrue(data["ok"])
        self.assertEqual(data["counts"]["sessions"], 7)
        self.assertEqual(data["counts"]["sessions_completed"], 0)
        self.assertEqual(data["counts"]["completion_percentage"], 0)

        doc = self.read_progress()
        self.assertEqual(sorted(doc["project"].keys()), ["created", "name", "updated"])
        self.assertEqual([s["id"] for s in doc["sessions"]], SESSION_IDS)
        for session in doc["sessions"]:
            self.assertEqual(session["status"], "not-started")
            self.assertIsNone(session["started_date"])
            self.assertIsNone(session["completed_date"])
            self.assertIsNone(session["score"])
            self.assertIsNone(session["topics_explored"])
            self.assertIsNone(session["notes"])
        self.assertEqual(doc["sessions_completed"], 0)
        self.assertEqual(doc["completion_percentage"], 0)
        self.assertEqual(doc["next_recommended"], 1)
        self.assertEqual(doc["summary"], {"generated": False, "path": None,
                                          "date": None})
        self.assertEqual(doc["revisions"], [])
        self.assertTrue(os.path.isdir(os.path.join(self.out, "notes")),
                        "init 须同时建 notes/ 目录（LLM 不自建）")
        self.assertTrue(os.path.isfile(self.progress_path()))

    # trace: §7 测试 2（init 无 --role 合法，assessed 恒 null）
    def test_init_role_optional_and_assessed_null(self):
        r = self.init()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        learner = self.read_progress()["learner"]
        self.assertIsNone(learner["role"])
        self.assertIsNone(learner["assessed"])
        self.assertEqual(sorted(learner.keys()),
                         ["assessed", "experience", "goals", "pain_points", "role"])

        self.tearDown()
        self.setUp()
        r2 = self.init("--role", "QA")
        self.assertEqual(r2.returncode, 0, r2.stdout + r2.stderr)
        learner2 = self.read_progress()["learner"]
        self.assertEqual(learner2["role"], "QA")
        self.assertIsNone(learner2["assessed"],
                          "assessed 归 02-assess（update --learner），init 不得置位")

        self.tearDown()
        self.setUp()
        r3 = self.init("--role", "CEO")
        self.assertEqual(r3.returncode, 1, r3.stdout)
        self.assertIn("ENUM_INVALID", self.codes(r3))
        self.assertFalse(os.path.isfile(self.progress_path()), "拒绝路径零产出")

    # trace: §7 测试 3（init 已存在 → 拒绝 + 指引 resume）
    def test_init_refuses_when_progress_exists(self):
        self.assertEqual(self.init().returncode, 0)
        before = self.read_text(self.progress_path())
        r = self.init()
        self.assertEqual(r.returncode, 1, r.stdout)
        data = json.loads(r.stdout)
        self.assertFalse(data["ok"])
        self.assertIn("ALREADY_EXISTS", self.codes(r))
        self.assertIn("status", data["violations"][0]["msg"])
        self.assertEqual(self.read_text(self.progress_path()), before,
                         "拒绝路径不得覆盖既有进度")


class UpdateSessionTests(EngineCase):

    def setUp(self):
        super().setUp()
        self.assertEqual(self.init().returncode, 0)

    # trace: §7 测试 4（幂等 upsert：同节二次完成不重复计数 + 重做修订）
    def test_update_is_idempotent_on_repeat_completion(self):
        r = self.complete(1, score=100)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        receipt = json.loads(r.stdout)
        self.assertEqual(receipt["counts"]["sessions_completed"], 1)
        self.assertEqual(receipt["counts"]["completion_percentage"], 14)
        self.assertEqual(receipt["sessions_completed"], 1)
        self.assertEqual(receipt["completion_percentage"], 14)
        self.assertEqual(receipt["next_recommended"], 2)
        self.assertEqual(receipt["updated"], self.today)
        self.assertEqual(receipt["change"],
                         {"kind": "session", "session": 1,
                          "from": "not-started", "to": "completed", "redo": False})

        r2 = self.complete(1, score=67)
        self.assertEqual(r2.returncode, 0, r2.stdout + r2.stderr)
        receipt2 = json.loads(r2.stdout)
        self.assertEqual(receipt2["counts"]["sessions_completed"], 1,
                         "重做同一节不得重复计数")
        self.assertEqual(receipt2["counts"]["completion_percentage"], 14)
        self.assertTrue(receipt2["change"]["redo"])

        doc = self.read_progress()
        session = doc["sessions"][0]
        self.assertEqual(session["score"], 67, "重做以最新一次为准")
        self.assertEqual(session["completed_date"], self.today)
        self.assertEqual(len(doc["revisions"]), 1)
        self.assertEqual(doc["revisions"][0]["change"], "session 1 重做")
        self.assertEqual(doc["revisions"][0]["reason"], "redo")
        self.assertEqual(doc["revisions"][0]["date"], self.today)

    # trace: §7 测试 5（派生字段基准 = 裁定 2 三式；手改 → SET_MISMATCH）
    def test_derived_fields_follow_three_formulas(self):
        for sid in (1, 2, 3):
            self.assertEqual(self.complete(sid).returncode, 0)
        doc = self.read_progress()
        self.assertEqual(doc["sessions_completed"], 3)
        self.assertEqual(doc["completion_percentage"], 43)  # floor(3*100/7+0.5)=43
        self.assertEqual(doc["next_recommended"], 4)
        self.assertEqual(self.check().returncode, 0)

        doc["sessions_completed"] = 6
        doc["completion_percentage"] = 86
        self.write_progress(doc)
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("SET_MISMATCH", self.codes(r))
        r2 = self.status()
        self.assertEqual(r2.returncode, 1, r2.stdout + " status 与 check 同源校验派生字段")
        self.assertIn("SET_MISMATCH", self.codes(r2))

    # trace: §7 测试 10（update --summary 三道门）+ §7 测试 9（--final 门）
    def test_completion_gate_and_final(self):
        self.complete_all()
        doc = self.read_progress()
        self.assertEqual(doc["sessions_completed"], 7)
        self.assertEqual(doc["completion_percentage"], 100)
        self.assertIsNone(doc["next_recommended"])
        self.assertEqual(self.check().returncode, 0)

        r = self.check("--final")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("SET_MISMATCH", self.codes(r))

        r2 = self.update("--summary", "--path", "notes/completion-summary.md")
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertIn("ENUM_INVALID", self.codes(r2))

        r3 = self.update("--summary", "--path", "completion-summary.md")
        self.assertEqual(r3.returncode, 1, r3.stdout)
        self.assertIn("MISSING_FILE", self.codes(r3))

        self.write_summary()
        r4 = self.update("--summary", "--path", "completion-summary.md")
        self.assertEqual(r4.returncode, 0, r4.stdout + r4.stderr)
        self.assertEqual(json.loads(r4.stdout)["change"], {"kind": "summary"})
        summary = self.read_progress()["summary"]
        self.assertEqual(summary, {"generated": True, "path": "completion-summary.md",
                                   "date": self.today})
        self.assertEqual(self.check("--final").returncode, 0)

    # trace: §7 测试 6 前置（summary 门：未满 7 节不得生成结业摘要）
    def test_summary_refused_before_seven_sessions(self):
        self.complete(1)
        self.write_summary()
        r = self.update("--summary", "--path", "completion-summary.md")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("STATUS_MISMATCH", self.codes(r))
        self.assertFalse(self.read_progress()["summary"]["generated"])

    # trace: §7 测试 8（update --learner 写通道）
    def test_update_learner_channel(self):
        r0 = self.update("--learner", "--role", "Lead")
        self.assertEqual(r0.returncode, 1, r0.stdout)
        self.assertIn("EMPTY_FIELD", self.codes(r0),
                      "assessed 非空 → role 与 experience 不得为空")
        self.assertIsNone(self.read_progress()["learner"]["assessed"],
                          "画像未采集完 → 写通道拒绝，零写入")

        r = self.update("--learner", "--role", "Dev", "--experience", "beginner",
                        "--goals", "把测试接进开发流程")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(json.loads(r.stdout)["change"], {"kind": "learner"})
        learner = self.read_progress()["learner"]
        self.assertEqual(learner["role"], "Dev")
        self.assertEqual(learner["experience"], "beginner")
        self.assertEqual(learner["goals"], ["把测试接进开发流程"])
        self.assertEqual(learner["assessed"], self.today)
        self.assertEqual(self.check().returncode, 0)

        r2 = self.update("--learner", "--role", "Lead")
        self.assertEqual(r2.returncode, 0, r2.stdout + r2.stderr)
        self.assertEqual(self.read_progress()["learner"]["role"], "Lead",
                         "补采单项时其余字段保持既有值")

        r3 = self.update("--learner", "--experience", "expert")
        self.assertEqual(r3.returncode, 1, r3.stdout)
        self.assertIn("ENUM_INVALID", self.codes(r3))
        self.assertEqual(self.read_progress()["learner"]["experience"], "beginner")

    # trace: §7 门禁（quiz 未达线不自动通过；score 仅在 completed 时接受且 0-100）
    def test_update_session_score_rules(self):
        r = self.update("--session", "1", "--status", "in-progress")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        doc = self.read_progress()
        self.assertEqual(doc["sessions"][0]["status"], "in-progress")
        self.assertEqual(doc["sessions"][0]["started_date"], self.today)

        self.write_notes(1)
        r2 = self.update("--session", "1", "--status", "in-progress",
                         "--score", "67", "--notes", self.notes_rel(1))
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertIn("STATUS_MISMATCH", self.codes(r2),
                      "score 仅在 --status completed 时接受")
        self.assertEqual(self.read_progress()["sessions"][0]["score"], None,
                         "拒绝路径零写入")

        r3 = self.update("--session", "1", "--status", "completed",
                         "--notes", self.notes_rel(1), "--score", "101")
        self.assertEqual(r3.returncode, 1, r3.stdout)
        self.assertIn("ENUM_INVALID", self.codes(r3))

        r4 = self.update("--session", "9", "--status", "completed")
        self.assertEqual(r4.returncode, 1, r4.stdout)
        self.assertIn("UNKNOWN_ID", self.codes(r4))

        r5 = self.update("--session", "1", "--status", "done")
        self.assertEqual(r5.returncode, 1, r5.stdout)
        self.assertIn("ENUM_INVALID", self.codes(r5))

    # trace: §7 测试 6（completed 无 notes / notes 越界 / 文件不在场）
    def test_check_flags_notes_problems(self):
        self.write_notes(1)
        self.assertEqual(self.update("--session", "1", "--status", "completed",
                                     "--notes", self.notes_rel(1)).returncode, 0)
        doc = self.read_progress()
        doc["sessions"][0]["notes"] = None
        self.write_progress(doc)
        self.assertEqual(self.check().returncode, 1)
        self.assertIn("EMPTY_FIELD", self.codes(self.check()))

        doc["sessions"][0]["notes"] = "docs/session-01.md"
        self.write_progress(doc)
        self.assertIn("ENUM_INVALID", self.codes(self.check()))

        doc["sessions"][0]["notes"] = "notes/session-02.md"
        self.write_progress(doc)
        self.assertIn("ENUM_INVALID", self.codes(self.check()))

        doc["sessions"][0]["notes"] = "notes/session-01.md"
        os.remove(os.path.join(self.out, "notes", "session-01.md"))
        self.write_progress(doc)
        self.assertIn("MISSING_FILE", self.codes(self.check()))

        r = self.update("--session", "2", "--status", "completed",
                        "--notes", self.notes_rel(2))
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("MISSING_FILE", self.codes(r), "写通道须校验 notes 文件在场")


class Session7Tests(EngineCase):

    def setUp(self):
        super().setUp()
        self.assertEqual(self.init().returncode, 0)

    # trace: §7 测试 7（session 7 完成判据 = topics_explored >= min_topics）
    def test_check_flags_session7_completion_criteria(self):
        self.write_notes(7)
        self.assertEqual(self.update("--session", "7", "--status", "completed",
                                     "--notes", self.notes_rel(7),
                                     "--topics", str(min_topics())).returncode, 0)
        self.assertEqual(self.check().returncode, 0, self.check().stdout)

        doc = self.read_progress()
        doc["sessions"][6]["topics_explored"] = None
        self.write_progress(doc)
        self.assertIn("EMPTY_FIELD", self.codes(self.check()),
                      "session 7 完成须交代 topics_explored")

        doc["sessions"][6]["topics_explored"] = min_topics() - 1
        self.write_progress(doc)
        self.assertIn("SET_MISMATCH", self.codes(self.check()))

        doc["sessions"][6]["topics_explored"] = min_topics()
        doc["sessions"][6]["score"] = 100
        self.write_progress(doc)
        self.assertIn("STATUS_MISMATCH", self.codes(self.check()),
                      "session 7 无 quiz：score 恒 null")

        doc["sessions"][6]["score"] = None
        doc["sessions"][0]["topics_explored"] = 2
        self.write_progress(doc)
        self.assertIn("ENUM_INVALID", self.codes(self.check()),
                       "topics_explored 仅 session 7 非空")

        doc["sessions"][0]["topics_explored"] = None
        self.write_progress(doc)
        r = self.update("--session", "1", "--topics", "2")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ENUM_INVALID", self.codes(r),
                      "写通道同样限制 --topics 仅 session 7")

    # trace: §7 终态定义（session 7 的 score 恒 null，不参与平均）
    def test_update_session7_score_refused(self):
        self.write_notes(7)
        r = self.update("--session", "7", "--status", "completed",
                        "--notes", self.notes_rel(7), "--score", "100")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("STATUS_MISMATCH", self.codes(r))


class StatusTests(EngineCase):

    # trace: §7 裁定 3（status 回执 = 分流表判定输入；文件缺席 → MISSING_FILE + 回 init）
    def test_status_entry_routing(self):
        r = self.status()
        self.assertEqual(r.returncode, 1, r.stdout)
        data = json.loads(r.stdout)
        self.assertIn("MISSING_FILE", self.codes(r))
        self.assertEqual(data["entry_step"], "steps/01-init.md")

        self.assertEqual(self.init().returncode, 0)
        self.assertEqual(json.loads(self.status().stdout)["entry_step"],
                         "steps/02-assess.md")

        self.assertEqual(self.update("--learner", "--role", "QA",
                                     "--experience", "experienced").returncode, 0)
        data = json.loads(self.status().stdout)
        self.assertEqual(data["entry_step"], "steps/03-hub.md")
        self.assertEqual(data["dashboard"]["sessions_completed"], 0)
        self.assertEqual(data["dashboard"]["next_recommended"], 1)
        self.assertEqual(data["dashboard"]["learner"]["role"], "QA")
        self.assertEqual(len(data["dashboard"]["sessions"]), 7)

    def test_status_routes_to_completion_and_hub(self):
        self.assertEqual(self.init().returncode, 0)
        self.assertEqual(self.update("--learner", "--role", "QA",
                                     "--experience", "experienced").returncode, 0)
        self.complete_all()
        self.assertEqual(json.loads(self.status().stdout)["entry_step"],
                         "steps/05-completion.md")
        self.write_summary()
        self.assertEqual(self.update("--summary", "--path",
                                     "completion-summary.md").returncode, 0)
        data = json.loads(self.status().stdout)
        self.assertEqual(data["entry_step"], "steps/03-hub.md")
        self.assertTrue(data["dashboard"]["summary"]["generated"])


class RecoveryTests(EngineCase):
    """T-6：进度文件损坏的出路（检测 + 自动备份 + fresh start，恢复只由引擎做）。"""

    CORRUPT = "sessions: [{{\n"

    def corrupt(self, text=CORRUPT):
        with io.open(self.progress_path(), "w", encoding="utf-8") as f:
            f.write(text)
        return text

    def backups(self):
        return sorted(name for name in os.listdir(self.out)
                      if name.startswith("learning-progress.yaml.corrupt-")
                      and name.endswith(".bak"))

    # trace: T-6（损坏检测 + 分流回 init 步 + 三条读通道给出路）
    def test_damaged_file_is_detected_and_points_to_recovery(self):
        self.assertEqual(self.init().returncode, 0)
        self.corrupt()
        r = self.status()
        self.assertEqual(r.returncode, 1, r.stdout)
        data = json.loads(r.stdout)
        self.assertIn("UNPARSABLE_YAML", self.codes(r))
        self.assertEqual(data["entry_step"], "steps/01-init.md",
                         "损坏即回 init 步：恢复的唯一出口在那里")
        self.assertIn("--recover", data["violations"][0]["msg"])
        for result in (self.check(), self.update("--learner", "--role", "QA")):
            self.assertEqual(result.returncode, 1, result.stdout)
            violation = json.loads(result.stdout)["violations"][0]
            self.assertEqual(violation["code"], "UNPARSABLE_YAML")
            self.assertIn("--recover", violation["msg"], "报错须给出路，不留死锁")

    # trace: T-6（不带 --recover 只报错零写入；带了 → 先备份后重建）
    def test_init_recover_backs_up_then_rebuilds(self):
        self.assertEqual(self.init().returncode, 0)
        self.write_notes(1, "上一轮的笔记，恢复后应原样留在盘上。")
        original = self.corrupt()

        r = self.init()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("UNPARSABLE_YAML", self.codes(r))
        self.assertIn("--recover", json.loads(r.stdout)["violations"][0]["msg"])
        self.assertEqual(self.backups(), [], "拒绝路径不得产生备份")
        self.assertEqual(self.read_text(self.progress_path()), original,
                         "拒绝路径零写入")

        r2 = self.init("--recover")
        self.assertEqual(r2.returncode, 0, r2.stdout + r2.stderr)
        receipt = json.loads(r2.stdout)
        self.assertEqual(receipt["counts"]["sessions"], 7)
        backup = os.path.join(self.root, receipt["recovered"]["backup"])
        self.assertTrue(os.path.isfile(backup), "回执须报出备份路径")
        self.assertEqual(self.read_text(backup), original, "备份 = 原文件逐字节副本")
        doc = self.read_progress()
        self.assertEqual([s["status"] for s in doc["sessions"]],
                         ["not-started"] * 7, "恢复 = 重建 7 节骨架")
        self.assertEqual(self.check().returncode, 0, "重建后 check 干净")
        self.assertTrue(os.path.isfile(os.path.join(self.out, "notes",
                                                    "session-01.md")),
                        "恢复只清台账断点，笔记 md 不动")

    # trace: T-6（结构不可用同样可恢复：顶层非映射）
    def test_recover_handles_unusable_structure(self):
        self.assertEqual(self.init().returncode, 0)
        self.corrupt("- not-a-mapping\n")
        r = self.status()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("EMPTY_FIELD", self.codes(r))
        self.assertEqual(json.loads(r.stdout)["entry_step"], "steps/01-init.md")

        r2 = self.init("--recover")
        self.assertEqual(r2.returncode, 0, r2.stdout + r2.stderr)
        self.assertEqual(self.read_progress()["sessions_completed"], 0)

    # trace: T-6（文件可用 → --recover 照样拒绝：「强制 resume」纪律不松）
    def test_recover_refuses_on_healthy_progress(self):
        self.assertEqual(self.init().returncode, 0)
        before = self.read_text(self.progress_path())
        r = self.init("--recover")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ALREADY_EXISTS", self.codes(r))
        self.assertEqual(self.backups(), [], "可用文件不得被 --recover 备份或覆盖")
        self.assertEqual(self.read_text(self.progress_path()), before)

    # trace: T-6（文件缺席 → --recover 等同普通 init，无备份）
    def test_recover_without_progress_is_plain_init(self):
        r = self.init("--recover")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("recovered", json.loads(r.stdout))
        self.assertEqual(self.backups(), [])


class ContractTests(EngineCase):
    # trace: 引擎契约冒烟（--json 单行 + 共同键 + 写命令 updated + 人读态汇总行）
    def test_json_receipt_and_human_output(self):
        common = {"ok", "command", "project_root", "output_dir", "violations",
                  "warnings", "counts"}
        r = self.init()
        self.assertEqual(len(r.stdout.strip().splitlines()), 1, "init --json 须单行")
        data = json.loads(r.stdout)
        self.assertTrue(common <= set(data), "init 回执缺共同键")
        self.assertEqual(data["command"], "init")
        self.assertEqual(data["project_root"], self.root)
        self.assertEqual(data["output_dir"], self.out.replace("\\", "/"))
        self.assertEqual(data["updated"], self.today, "写命令回执含 updated")

        self.write_notes(1)
        r2 = self.update("--session", "1", "--status", "completed",
                         "--notes", self.notes_rel(1))
        data2 = json.loads(r2.stdout)
        self.assertTrue(common <= set(data2))
        self.assertEqual(data2["updated"], self.today)

        r3 = self.check()
        data3 = json.loads(r3.stdout)
        self.assertTrue(common <= set(data3))
        self.assertEqual(data3["command"], "check")
        self.assertFalse(data3["final"])

        r4 = run_engine(["status", "--project-root", self.root,
                         "--output-dir", self.out])
        self.assertEqual(r4.returncode, 0, r4.stdout)
        self.assertTrue(r4.stdout.strip().splitlines()[-1].startswith("汇总："))
        self.assertNotIn("{", r4.stdout)

        r5 = run_engine(["init", "--project-root", self.root, "--output-dir", self.out])
        self.assertEqual(r5.returncode, 1)
        lines = [line for line in r5.stdout.strip().splitlines() if line.strip()]
        self.assertTrue(lines[0].startswith("ALREADY_EXISTS "), lines[0])
        self.assertTrue(lines[-1].startswith("汇总："), r5.stdout)

    # trace: 引擎契约（--output-dir 必填 / update 三形态互斥 → exit 2 用法错误）
    def test_usage_errors(self):
        self.assertEqual(run_engine(["check", "--project-root", self.root]).returncode, 2)
        self.assertEqual(run_engine(["init", "--project-root", self.root]).returncode, 2)
        self.assertEqual(self.init().returncode, 0)
        self.assertEqual(run_engine(["update", "--project-root", self.root,
                                     "--output-dir", self.out]).returncode, 2)
        self.assertEqual(run_engine(["update", "--session", "1", "--learner",
                                     "--project-root", self.root,
                                     "--output-dir", self.out]).returncode, 2)
        self.assertEqual(run_engine(["update", "--learner", "--score", "90",
                                     "--project-root", self.root,
                                     "--output-dir", self.out]).returncode, 2)


class SkillContractTests(unittest.TestCase):
    """SKILL.md 契约冒烟（母本片段 + 终门句 + 四段结构）。"""

    def read_skill(self):
        if not os.path.isfile(SKILL_MD):
            self.fail("SKILL.md 尚未交付")
        with io.open(SKILL_MD, encoding="utf-8") as f:
            return f.read()

    # trace: §2.5（母本 §1 / §2 中文定稿逐字；§3 / §4 / §5 锚串落地）
    def test_mother_texts_verbatim(self):
        skill = self.read_skill()
        for label, frag in (("§1 实例解析句", INSTANCE_ZH),
                            ("§2 写作纪律块", DISCIPLINE_ZH),
                            ("§3 配置解析键", CONFIG_ANCHOR),
                            ("§4 读取纪律", READ_ANCHOR),
                            ("§5 渲染静默", RENDER_ANCHOR)):
            self.assertIn(frag, skill, "SKILL.md 缺母本 %s 逐字文本" % label)

    # trace: §2.5（终门句指向本技能引擎）
    def test_final_gate_points_to_engine(self):
        skill = self.read_skill()
        self.assertIn("progress.py", skill, "终门句未指向本技能引擎")
        self.assertIn("check --final", skill, "终门句缺 check --final")
        self.assertIn("--json", skill, "终门句缺 --json 回执")

    # trace: 验收 #1 / #8（薄主文件 ≤90 行 + 四段 + frontmatter 登记元数据）
    def test_thin_main_file_shape(self):
        skill = self.read_skill()
        self.assertLessEqual(len(skill.splitlines()), 90, "SKILL.md 超过 90 行")
        for section in ("## On Activation", "## Workflow", "## Schema", "## Rules"):
            self.assertIn(section, skill, "SKILL.md 缺四段：%s" % section)
        self.assertIn("name: diy-teach-me-testing", skill)
        self.assertIn("phase: 0-learning", skill)
        self.assertIn("line: any", skill)
        self.assertIn("outputs: learning-progress.yaml", skill)


class TeachingContentTests(unittest.TestCase):
    """T-1~T-5：教学内容落点契约（curriculum.yaml 主题 / steps 条文）。

    这些是 V 能力清点（2026-09-18）判定的丢失项：本类把「补在哪、补了什么」钉成契约，
    防止后续返工把补入的主题与条文又静默抹掉（母本漂移测试同款思路，对象是技能内资产）。
    """

    def curriculum(self):
        with io.open(os.path.join(SKILL_DIR, "curriculum.yaml"), encoding="utf-8") as f:
            return yaml.safe_load(f)

    def outline(self, session_id):
        session = [s for s in self.curriculum()["sessions"] if s["id"] == session_id][0]
        return "\n".join(session["outline"])

    def step_text(self, name):
        with io.open(os.path.join(SKILL_DIR, "steps", name), encoding="utf-8") as f:
            return f.read()

    # trace: T-1 / T-2（S1 五种投入档位；S3 微文件架构主题）
    def test_s1_engagement_models_and_s3_step_file_architecture(self):
        s1 = self.outline(1)
        self.assertIn("五种投入档位", s1)
        for rung in ("单点", "按需", "全链", "存量接入"):
            self.assertIn(rung, s1, "S1 缺投入档位：%s" % rung)
        self.assertIn("微文件架构（step-file architecture）", self.outline(3))

    # trace: T-3（S2 完成定义第 6/7 条 / S5 组件级红绿循环 / S6 质量指标块）
    def test_s2_dod_s5_component_tdd_s6_metrics(self):
        s2 = self.outline(2)
        self.assertIn("测试就近源码", s2)
        self.assertIn("低维护", s2)
        self.assertIn("组件级红绿重构循环", self.outline(5))
        s6 = self.outline(6)
        self.assertIn("虚荣指标", s6)
        self.assertIn("dimensions.determinism", s6)

    # trace: T-4（S4 覆盖规划 + 覆盖目标：门强判三线全 100%，无中间档、不按优先级递减）
    def test_s4_coverage_planning_and_flat_target(self):
        s4 = self.outline(4)
        self.assertIn("覆盖规划", s4)
        self.assertIn("覆盖目标一律 100%", s4)
        self.assertIn("p0_coverage", s4)
        self.assertIn("不按优先级递减", s4)

    # trace: T-5（quiz 每题 3 次作答机会；计分口径不动）
    def test_quiz_three_attempts_per_question(self):
        step = self.step_text("04-session.md")
        self.assertIn("每题最多 3 次作答机会", step)
        self.assertIn("第 3 次仍错", step)
        self.assertIn("score = round(答对数 × 100 / 3)", step, "计分口径不得随之改动")

    # trace: 附带（A1 裁定 2026-09-18 删 [B]）：教学内容不得再教已删除的双模式词汇
    def test_no_legacy_mode_vocabulary(self):
        for name in ("curriculum.yaml", "quiz-questions.yaml"):
            with io.open(os.path.join(SKILL_DIR, name), encoding="utf-8") as f:
                text = f.read()
            self.assertNotIn("[A]", text, "%s 仍教已删除的模式词汇" % name)
            self.assertNotIn("[B]", text, "%s 仍教已删除的模式词汇" % name)


if __name__ == "__main__":
    unittest.main()
