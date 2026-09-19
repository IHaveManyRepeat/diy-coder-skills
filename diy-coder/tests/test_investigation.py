# -*- coding: utf-8 -*-
"""diy-investigate 确定性引擎 e2e 测试（B2 批 W5，任务书 §2.5/§7）。

覆盖：
- 用例 1：check --final 合法案件记录 exit 0 唯一放行（counts 与集合一致）
- 用例 2：枚举违例（evidence grade / case mode / hypothesis status / backlog priority）各带对应
          violation code
- 用例 3：evidence_light=true 而 missing_evidence 为空 → EVIDENCE_MISSING
          （证据缺失也是发现——无据案件必须记账，复用冻结码不新增）
- 用例 4：假设生命周期（status 非「待验证」时 resolution 必填；待验证可无 resolution）
- 用例 5：collect 在无 VCS 环境下降级（NO_VCS warning + 不崩 + 仍 exit 0，回执键完整）
- 用例 6：collect 结构情报（--area 的文件清单 + 同名族并行实现 + 测试文件候选）
- 用例 7：check 缺文件 → MISSING_FILE 结构化违规（不 Traceback）；--output-dir 必填
- 用例 8（git 夹具，skipUnless）：collect 在临时 git 仓库上取近期提交
- 用例 9：SKILL.md 契约冒烟（母本 §1–§6 中文定稿逐字 + 终门句指向 investigation.py）
- 用例 10：B-18 落点锁（priority 值域 / ID 作用域 / bug-add 路由 / 委派分层闸值 / 状态映射等）

夹具全部落 tempdir 自建；不读写本仓库真实 diy-output；git 用例自建临时仓库（不依赖本机状态）。
运行：cd diy-coder && python -m unittest discover -s tests -p "test_investigation.py" -v
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

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.join(HERE, "..", "skills", "diy-investigate")
ENGINE = os.path.join(SKILL_DIR, "scripts", "investigation.py")
SKILL_MD = os.path.join(SKILL_DIR, "SKILL.md")
STEPS_DIR = os.path.join(SKILL_DIR, "steps")
NL = chr(10)

# 套件级句式母本（suite-texts.md §1 / §2 / §3 / §4 / §5 / §6 中文定稿，逐字）
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
RESOLVE_KEYS_ZH = ("解析 `project.communication_language` / "
                   "`project.document_output_language` / `paths.output_dir`")
READ_DISCIPLINE_ZH = ("读取纪律：预载预算 = 本文件、上述配置与回执、`steps/` 下当前那一个文件"
                      "——绝不批量预载；执行期读取以每个步骤开头的 `Read (input)` 行为唯一权威，"
                      "**主文件不列举封闭清单**。")
RENDER_SILENT_ZH = "渲染是静默旁路——只写调用命令"
PRECISE_ZH = ("- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；"
              "不复述上游已写的信息（引用 ID）；不写没有信息量的套话。")
# 英文原形（历史，批 4 冻结）——中文化后不得残留
INSTANCE_EN_MARK = "Instance resolution (FR-4.5/D-9)"
DISCIPLINE_EN_MARK = "- **Writing discipline."

STEPS = ("01-acknowledge.md", "02-stronghold.md", "03-perimeter.md",
         "04-reasoning.md", "05-source-trace.md", "06-report.md")

INVESTIGATION_YAML = NL.join([
    "project:",
    "  name: mini",
    "  status: 已定稿",
    "  created: '2026-01-01'",
    "  updated: '2026-09-14'",
    "cases:",
    "- id: IV-001",
    "  slug: login-500",
    "  date: '2026-09-14'",
    "  status: 已结论",
    "  mode: 症状驱动",
    "  evidence_light: false",
    "  handoff_brief: 登录并发下返回 500，根因是连接池未复用。",
    "  case_info:",
    "    inputs:",
    "    - kind: 工单",
    "      ref: TICKET-42",
    "    - kind: 日志",
    "      ref: var/log/app.log",
    "    scope: 登录链路",
    "    time_window: '2026-09-13 10:00 ~ 12:00'",
    "  problem_statement: 用户报告登录偶发 500。",
    "  stronghold:",
    "    ref: src/auth/login.py:88",
    "    why: 错误栈首帧指向该行",
    "  evidence:",
    "  - id: EV-001",
    "    grade: 已确证",
    "    ref: src/auth/login.py:88",
    "    note: 错误栈首帧",
    "    availability: 可得",
    "  - id: EV-002",
    "    grade: 已推断",
    "    ref: var/log/app.log",
    "    note: 日志显示连接池耗尽",
    "    availability: 部分可得",
    "  - id: EV-003",
    "    grade: 假设中",
    "    ref: commit:9f3a1c2",
    "    note: 疑似连接未释放",
    "    availability: 缺失",
    "  hypotheses:",
    "  - id: H-001",
    "    statement: 连接池未复用导致耗尽",
    "    status: 已确证",
    "    test: 压测复现连接数增长",
    "    resolution: 压测复现，EV-002 佐证",
    "  - id: H-002",
    "    statement: 网关超时",
    "    status: 已推翻",
    "    test: 查网关日志",
    "    resolution: 网关日志显示 500 由上游抛出",
    "  timeline:",
    "  - at: '2026-09-13 10:12'",
    "    event: 首次 500",
    "    ref: var/log/app.log:120",
    "  backlog:",
    "  - item: 复查连接池配置",
    "    priority: 中",
    "    status: 已完成",
    "  missing_evidence:",
    "  - what: 完整堆栈",
    "    would_resolve: 确认抛出点",
    "    how: 提高日志级别后复现",
    "  conclusion:",
    "    text: 连接池耗尽导致登录 500。",
    "    confidence: 高",
    "    fix_direction: 复用连接并在 finally 释放",
    "    diagnostic_steps: []",
    "    reproduction: 并发 50 压测",
    "  follow_ups: []",
    "revisions: []",
]) + NL


def run_engine(args, env=None):
    return subprocess.run([sys.executable, ENGINE] + args, capture_output=True,
                          text=True, encoding="utf-8", env=env)


def git_available():
    return shutil.which("git") is not None


class EngineCase(unittest.TestCase):
    """tmp 项目根 + diy-output 目录的公共夹具。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="inv-")
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

    def check(self, *extra, **kwargs):
        return run_engine(["check", "--project-root", self.root,
                           "--output-dir", self.out, "--json"] + list(extra), **kwargs)

    def collect(self, *extra, **kwargs):
        return run_engine(["collect", "--project-root", self.root,
                           "--output-dir", self.out, "--json"] + list(extra), **kwargs)

    def case_path(self):
        return os.path.join(self.out, "investigation.yaml")


class CheckValidationTests(EngineCase):

    # trace: 任务书 §2.5 用例 3（合法记录 --final exit 0 唯一放行）
    def test_check_final_legal_record_passes(self):
        self.write("diy-output/investigation.yaml", INVESTIGATION_YAML)
        r = self.check("--final")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertTrue(data["ok"])
        self.assertEqual(data["violations"], [])
        self.assertEqual(data["counts"]["cases"], 1)
        self.assertEqual(data["counts"]["by_status"], {"已结论": 1})
        self.assertEqual(data["counts"]["evidence"], 3)
        self.assertEqual(data["counts"]["hypotheses"], 2)
        self.assertEqual(data["counts"]["open_hypotheses"], 0)

    # trace: 任务书 §7 check（枚举面：grade / mode / hypothesis status）
    def test_check_reports_enum_violations(self):
        cases = [
            ("ENUM_INVALID", "    grade: 已确证", "    grade: certain"),
            ("ENUM_INVALID", "  mode: 症状驱动", "  mode: guesswork"),
            ("ENUM_INVALID", "    status: 已推翻", "    status: maybe"),
            ("ENUM_INVALID", "    availability: 缺失", "    availability: unknown"),
            ("ENUM_INVALID", "    priority: 中", "    priority: urgent"),
        ]
        for code, old, new in cases:
            self.write("diy-output/investigation.yaml", INVESTIGATION_YAML.replace(old, new))
            r = self.check()
            self.assertEqual(r.returncode, 1, "%s: %s" % (code, r.stdout))
            data = json.loads(r.stdout)
            self.assertIn(code, {x["code"] for x in data["violations"]}, r.stdout)
            self.assertTrue(all(x.get("where") and x.get("msg")
                                for x in data["violations"]), r.stdout)

    # trace: 任务书 §7 check（证据缺失也是发现；source 纪律：missing evidence is a finding）
    def test_evidence_light_requires_missing_evidence(self):
        light = (INVESTIGATION_YAML
                 .replace("  evidence_light: false", "  evidence_light: true")
                 .replace("  stronghold:" + NL + "    ref: src/auth/login.py:88" + NL
                          + "    why: 错误栈首帧指向该行" + NL, "")
                 .replace("  missing_evidence:" + NL + "  - what: 完整堆栈" + NL
                          + "    would_resolve: 确认抛出点" + NL
                          + "    how: 提高日志级别后复现" + NL,
                          "  missing_evidence: []" + NL))
        self.write("diy-output/investigation.yaml", light)
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        data = json.loads(r.stdout)
        self.assertIn("EVIDENCE_MISSING", {x["code"] for x in data["violations"]}, r.stdout)
        # 对照：evidence_light=true 且 missing_evidence 非空 → 合法（无据案件必须记账）
        kept = light.replace("  missing_evidence: []" + NL,
                             "  missing_evidence:" + NL + "  - what: 完整堆栈" + NL
                             + "    would_resolve: 确认抛出点" + NL
                             + "    how: 提高日志级别后复现" + NL)
        self.write("diy-output/investigation.yaml", kept)
        r2 = self.check()
        self.assertEqual(r2.returncode, 0, r2.stdout + r2.stderr)

    # trace: 任务书 §7 check（假设永不删除：status 转移必须带 resolution——生命周期闭环）
    def test_hypothesis_status_transition_requires_resolution(self):
        missing = INVESTIGATION_YAML.replace(
            "    resolution: 压测复现，EV-002 佐证" + NL, "")
        self.write("diy-output/investigation.yaml", missing)
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("EMPTY_FIELD", {x["code"] for x in json.loads(r.stdout)["violations"]})
        # 对照：待验证 假设可以没有 resolution（尚未结案）
        opened = INVESTIGATION_YAML.replace("    status: 已确证", "    status: 待验证")
        self.write("diy-output/investigation.yaml", opened.replace(
            "    resolution: 压测复现，EV-002 佐证" + NL, ""))
        r2 = self.check()
        self.assertEqual(r2.returncode, 0, r2.stdout + r2.stderr)
        self.assertEqual(json.loads(r2.stdout)["counts"]["open_hypotheses"], 1)

    # trace: 任务书 §7 check（--final 附加：零假设 / conclusion 三键 / handoff_brief / timeline）
    def test_check_final_duties(self):
        self.write("diy-output/investigation.yaml", INVESTIGATION_YAML)
        r = self.check("--final")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        cases = [
            ("ASSUMPTION_PRESENT", "  problem_statement: 用户报告登录偶发 500。",
             "  problem_statement: '[假设] 用户报告登录偶发 500。'"),
            ("STATUS_MISMATCH", "  status: 已定稿" + NL, "  status: 草稿" + NL),
            ("PENDING_DECISION", "    confidence: 高" + NL, ""),
            ("EMPTY_FIELD", "  handoff_brief: 登录并发下返回 500，根因是连接池未复用。", "  handoff_brief: ''"),
        ]
        for code, old, new in cases:
            self.write("diy-output/investigation.yaml", INVESTIGATION_YAML.replace(old, new))
            r = self.check("--final")
            self.assertEqual(r.returncode, 1, "%s: %s" % (code, r.stdout))
            self.assertIn(code, {x["code"] for x in json.loads(r.stdout)["violations"]},
                          "%s 未报出：%s" % (code, r.stdout))
        # 起草期宽松：草稿 + conclusion 未定合法（非 --final）
        draft = (INVESTIGATION_YAML.replace("  status: 已定稿" + NL, "  status: 草稿" + NL)
                 .replace("    confidence: 高" + NL, ""))
        self.write("diy-output/investigation.yaml", draft)
        r2 = self.check()
        self.assertEqual(r2.returncode, 0, r2.stdout + r2.stderr)

    # trace: V 补修（源 case-file-template「Side Findings」→ side_findings；note 必填、字段可选）
    def test_side_findings_note_required(self):
        with_side = INVESTIGATION_YAML.replace(
            "  follow_ups: []" + NL,
            "  side_findings:" + NL + "  - note: 顺带发现日志轮转缺省值偏小" + NL
            + "    ref: config/logging.yaml:12" + NL + "  follow_ups: []" + NL)
        self.write("diy-output/investigation.yaml", with_side)
        r = self.check()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(json.loads(r.stdout)["counts"]["side_findings"], 1)
        r_final = self.check("--final")  # 在场不强制非空、不影响 --final
        self.assertEqual(r_final.returncode, 0, r_final.stdout + r_final.stderr)
        empty = with_side.replace("  - note: 顺带发现日志轮转缺省值偏小", "  - note: ''")
        self.write("diy-output/investigation.yaml", empty)
        r2 = self.check()
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertIn("EMPTY_FIELD", {x["code"] for x in json.loads(r2.stdout)["violations"]})
        # 缺席合法：既有记录不受影响
        self.write("diy-output/investigation.yaml", INVESTIGATION_YAML)
        r3 = self.check()
        self.assertEqual(r3.returncode, 0, r3.stdout + r3.stderr)

    # trace: 任务书 §7 check（路径 / ID / --id 定点）
    def test_check_id_and_path_violations(self):
        self.write("diy-output/investigation.yaml",
                   INVESTIGATION_YAML.replace("id: IV-001", "id: IV-1"))
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ENUM_INVALID", {x["code"] for x in json.loads(r.stdout)["violations"]})
        self.write("diy-output/investigation.yaml",
                   INVESTIGATION_YAML.replace("id: IV-001", "id: IV-001") + "")
        r2 = self.check("--id", "IV-999")
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertIn("UNKNOWN_ID", {x["code"] for x in json.loads(r2.stdout)["violations"]})
        # 记录内 evidence ID 重复 → DUPLICATE_ID
        dup = INVESTIGATION_YAML.replace("  - id: EV-002", "  - id: EV-001")
        self.write("diy-output/investigation.yaml", dup)
        r3 = self.check()
        self.assertEqual(r3.returncode, 1, r3.stdout)
        self.assertIn("DUPLICATE_ID", {x["code"] for x in json.loads(r3.stdout)["violations"]})

    # trace: 任务书 §2.5 用例 2（缺文件 → 结构化违规，不 Traceback；--output-dir 必填）
    def test_check_missing_file_is_structured(self):
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertNotIn("Traceback", r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual(data["violations"][0]["code"], "MISSING_FILE")
        self.assertEqual(data["counts"]["cases"], 0)
        # 损坏 YAML 同样结构化
        self.write("diy-output/investigation.yaml", "cases: [" + NL)
        r2 = self.check()
        self.assertEqual(r2.returncode, 1)
        self.assertNotIn("Traceback", r2.stderr)
        self.assertEqual(json.loads(r2.stdout)["violations"][0]["code"], "UNPARSABLE_YAML")

    # trace: 任务书 §2.2（引擎不做实例解析/目录推导：--output-dir 必填）
    def test_output_dir_is_mandatory(self):
        for sub in ("collect", "check"):
            r = run_engine([sub, "--project-root", self.root, "--json"])
            self.assertEqual(r.returncode, 2, "%s: %s" % (sub, r.stdout + r.stderr))


class CollectTests(EngineCase):

    # trace: 任务书 §7 collect（VCS 不可用 → NO_VCS warning 降级不崩）
    def test_collect_degrades_without_vcs(self):
        env = dict(os.environ)
        env["PATH"] = ""  # 强制 git 不可发现：不依赖本机 git 状态
        r = self.collect(env=env)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("Traceback", r.stderr)
        data = json.loads(r.stdout)
        self.assertTrue(data["ok"])
        self.assertFalse(data["vcs"]["available"])
        self.assertIn("NO_VCS", {w["code"] for w in data["warnings"]}, data["warnings"])
        # 回执键完整性（任务书 §7：{ok, vcs, files, candidates, warnings}）
        for key in ("ok", "command", "project_root", "output_dir", "vcs", "files",
                    "candidates", "violations", "warnings", "counts"):
            self.assertIn(key, data, key)
        self.assertEqual(data["violations"], [])
        # 只读：collect 不写产物
        self.assertFalse(os.path.exists(self.case_path()))

    # trace: 任务书 §7 collect（目标区域文件清单 + 同名族并行实现 + 测试文件候选）
    def test_collect_maps_area_candidates(self):
        self.write("src/auth/login.py", "def login():" + NL + "    return 500" + NL)
        self.write("src/billing/login.py", "def login():" + NL + "    return 200" + NL)
        self.write("tests/test_login.py", "def test_login():" + NL + "    pass" + NL)
        env = dict(os.environ)
        env["PATH"] = ""  # 结构情报不依赖 git
        r = self.collect("--area", "src/auth/login.py", env=env)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertTrue(data["ok"])
        files = {f["path"] for f in data["files"]}
        self.assertIn("src/auth/login.py", files, data["files"])
        kinds = {(c["kind"], c["file"]) for c in data["candidates"]}
        self.assertIn(("parallel", "src/billing/login.py"), kinds, data["candidates"])
        self.assertIn(("test", "tests/test_login.py"), kinds, data["candidates"])
        self.assertEqual(data["counts"]["files"], len(data["files"]))
        self.assertEqual(data["counts"]["candidates"], len(data["candidates"]))
        # area 不存在 → 结构化 warning，不崩
        r2 = self.collect("--area", "src/nope.py", env=env)
        self.assertEqual(r2.returncode, 0, r2.stdout + r2.stderr)
        self.assertIn("MISSING_FILE",
                      {w["code"] for w in json.loads(r2.stdout)["warnings"]})


@unittest.skipUnless(git_available(), "git 不可用")
class GitCollectTests(EngineCase):
    """git 情报：自建临时仓库（不依赖本机 git 状态）。"""

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
        return self.git("-c", "user.email=inv@example.com", "-c", "user.name=inv",
                        "commit", "-q", "-m", message)

    # trace: 任务书 §7 collect（git log 近期提交 + 涉及文件）
    def test_collect_git_log(self):
        self.write("src/auth/login.py", "print(1)" + NL)
        self.commit("fix login")
        r = self.collect()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertTrue(data["vcs"]["available"])
        self.assertTrue(data["vcs"]["head"])
        subjects = [c["subject"] for c in data["vcs"]["commits"]]
        self.assertIn("fix login", subjects, data["vcs"])
        self.assertIn("src/auth/login.py", data["vcs"]["commits"][0]["files"])
        self.assertEqual(data["counts"]["commits"], len(data["vcs"]["commits"]))


class SkillContractTests(unittest.TestCase):
    """用例 9/10：SKILL.md 契约冒烟（母本 §1–§6 中文定稿逐字 + 终门句指向本技能引擎）。"""

    def read_skill(self):
        if not os.path.isfile(SKILL_MD):
            self.skipTest("SKILL.md 尚未交付")
        with io.open(SKILL_MD, encoding="utf-8", newline="") as f:
            return f.read().replace("\r\n", "\n")

    def read_step(self, name):
        with io.open(os.path.join(STEPS_DIR, name), encoding="utf-8", newline="") as f:
            return f.read().replace("\r\n", "\n")

    # trace: 母本 §1（实例解析句中文化定稿逐字；2026-09-19 中文化轮）
    def test_instance_sentence_verbatim(self):
        skill = self.read_skill()
        self.assertIn(INSTANCE_ZH, skill, "SKILL.md 缺母本 §1 中文定稿（逐字）")
        self.assertNotIn(INSTANCE_EN_MARK, skill, "已转中文定稿，不得残留英文原形")

    # trace: 母本 §2（写作纪律块逐字，置 Rules 段末尾）
    def test_writing_discipline_block_at_rules_end(self):
        skill = self.read_skill()
        self.assertIn(DISCIPLINE_ZH, skill, "SKILL.md 缺母本 §2 中文定稿")
        self.assertNotIn(DISCIPLINE_EN_MARK, skill, "已转中文定稿，不得残留英文原形")
        self.assertEqual(DISCIPLINE_ZH, skill.rstrip(NL).splitlines()[-1],
                         "写作纪律块须置 Rules 段末尾")

    # trace: 母本 §3 / §4 / §5 / §6（中文化轮落地锚串）
    def test_mother_text_anchors(self):
        skill = self.read_skill()
        for label, frag in (("§3 配置解析键", RESOLVE_KEYS_ZH),
                            ("§4 读取纪律", READ_DISCIPLINE_ZH),
                            ("§5 渲染静默", RENDER_SILENT_ZH),
                            ("§6 精准简练", PRECISE_ZH)):
            self.assertIn(frag, skill, "SKILL.md 缺母本 %s 逐字文本" % label)

    # trace: 任务书 §2.1/#11/#12（终门句指向 investigation.py；collect 接线；渲染静默）
    def test_final_gate_points_to_engine(self):
        skill = self.read_skill()
        self.assertIn("investigation.py", skill, "终门句未指向领域引擎")
        self.assertIn("check --final", skill, "终门句缺 check --final")
        self.assertIn("--json", skill, "终门句缺 --json 回执")
        self.assertIn("collect", skill, "激活段未接线 collect")
        self.assertIn("绝不批量预载", skill, "缺读取成本纪律（母本 §4）")
        self.assertIn("viewer.py", skill, "缺渲染静默命令")
        self.assertIn("diyc.py\" resolve", skill, "实例解析未委托 diyc.py resolve")
        self.assertNotIn("bmad-help", skill, "不得引用不存在的技能")
        self.assertNotIn("bmad-quick-dev", skill, "handoff 须指向 diy 技能名")

    # trace: 范本 §二 / 政策（四段中文标题 + ≤93 行预算 + description 中文注释 + 步名点名）
    def test_thin_main_file_structure(self):
        skill = self.read_skill()
        self.assertLessEqual(len(skill.splitlines()), 93, "薄主文件超出 93 行预算")
        self.assertIn("name: diy-investigate", skill)
        self.assertIn("outputs: investigation.yaml", skill)
        self.assertIn("# ↑ 中文：", skill, "description 缺中文注释")
        for section in ("## 激活时", "## 工作流", "## 结构", "## 规则"):
            self.assertIn(section, skill, "SKILL.md 缺四段：%s" % section)
        for name in STEPS:
            self.assertIn(name, skill, "工作流未点名 %s" % name)

    # trace: 母本 §三（steps 形态：H1 中文步名 + Read/Write 英文锚 + 末段点名下一个）
    def test_steps_shape(self):
        for i, name in enumerate(STEPS, start=1):
            self.assertTrue(os.path.isfile(os.path.join(STEPS_DIR, name)),
                            "缺步骤文件 %s" % name)
            text = self.read_step(name)
            lines = text.splitlines()
            self.assertTrue(lines[0].startswith("# Step %d — " % i),
                            "%s 的 H1 须为 '# Step %d — <中文步名>'，实为 %r"
                            % (name, i, lines[0]))
            self.assertTrue(re.search(r"[一-鿿]", lines[0]), "%s 的步名须含中文" % name)
            self.assertTrue(any(ln.startswith("**Read (input):**") for ln in lines),
                            "%s 缺 '**Read (input):**' 行" % name)
            self.assertTrue(any(ln.startswith("**Write (output):**") for ln in lines),
                            "%s 缺 '**Write (output):**' 行" % name)
            self.assertIn("## 播报与下一步", text, "%s 缺末段 '## 播报与下一步'" % name)
        for name, nxt in zip(STEPS[:5], STEPS[1:]):
            self.assertIn(nxt, self.read_step(name), "%s 未点名下一个 %s" % (name, nxt))
        self.assertIn("最后一个步骤文件", self.read_step(STEPS[-1]),
                      "%s 须声明本步是终局" % STEPS[-1])

    # trace: B-18 十五条落点锁（SS-022-02/04/05/06/07/08/09/10/11/12/13/14/16 + C9 + A-5）
    def test_b18_landings(self):
        skill = self.read_skill()
        # SS-022-02：输入形态 → 旗标映射表（step 1 的列）+ SKILL.md 指路
        ack = self.read_step("01-acknowledge.md")
        self.assertIn("`collect` 旗标", ack, "steps/01 缺 collect 旗标列")
        for flag in ("--area <归档所在目录>", "--area <入口路径>", "--since <commit>"):
            self.assertIn(flag, ack, "steps/01 的映射表缺 %s" % flag)
        self.assertIn("steps/01-acknowledge.md` 的表", skill, "SKILL.md 未指向映射表")
        # SS-022-04 / SS-022-11：availability 与 missing_evidence 分工；六类是测绘顺序
        perim = self.read_step("03-perimeter.md")
        self.assertIn("是缺口的载体", perim, "SS-022-04 分工句缺失")
        self.assertIn("只用于**已有条目跑丢**", perim, "SS-022-04 作用域句缺失")
        self.assertIn("**测绘顺序**，不是记录形状", perim, "SS-022-11 测绘顺序句缺失")
        # SS-022-12：priority 值域 + 引擎常量
        self.assertIn("priority: 高|中|低", skill, "SKILL.md schema 缺 priority 值域")
        self.assertIn("BACKLOG_PRIORITIES", perim, "steps/03 未点名引擎常量")
        # SS-022-10：ID 作用域（SKILL.md 括注 + step 2）
        self.assertIn("文件级唯一", skill, "SKILL.md 读取预算句缺 ID 作用域括注")
        self.assertIn("本 case 内**各自从 001 起", self.read_step("02-stronghold.md"),
                      "steps/02 缺 ID 作用域句")
        # SS-022-09：追加 case 前退回 草稿（B5 组）
        self.assertIn("退回 `草稿`", self.read_step("02-stronghold.md"),
                      "steps/02 缺状态回退句")
        # SS-022-07：线→步骤对照表 + 续案置回 调查中（revisions 追加）
        self.assertIn("| 未结假设（`status: 待验证`）及其 `test` 判据 | `./04-reasoning.md` |",
                      ack, "SS-022-07 线→步骤对照表缺失")
        self.assertIn("置回 `调查中`", ack, "SS-022-07 续案状态句缺失")
        # SS-022-08：scope 不一致 → 重跑 collect
        self.assertIn("重跑一次 `collect`", ack, "SS-022-08 重跑条款缺失")
        # SS-022-13：校正落 conclusion.text；problem_statement 永保原话
        reasoning = self.read_step("04-reasoning.md")
        self.assertIn("校正落 `conclusion.text`", reasoning, "SS-022-13 校正落点缺失")
        self.assertIn("`problem_statement` 永保用户原话，不覆盖", reasoning)
        # SS-022-16：状态 ← 完成判据映射
        report = self.read_step("06-report.md")
        for frag in ("已结论` ← 判据 ①", "待证据阻塞` ← 判据 ②", "调查中` ← 五条判据都不成立"):
            self.assertIn(frag, report, "SS-022-16 映射缺 %s" % frag)
        # SS-022-05 / C9：缺陷入库路由（bug-add + source: 用户），Rule 1 拆措辞
        self.assertIn("bug-add", skill, "SKILL.md Rule 1/路由缺 bug-add")
        self.assertIn("`source: 用户`", skill, "SKILL.md 缺 source: 用户")
        self.assertIn("bug-add --entry '<json>' --json", report, "step 6 路由表缺入库命令")
        self.assertIn("零写 `bug-log.yaml`", report, "step 6 缺零写声明")
        # SS-022-14：fix_direction 是诊断产出、绝不写源码
        trace = self.read_step("05-source-trace.md")
        self.assertIn("**诊断产出**", trace, "SS-022-14 诊断产出句缺失")
        self.assertIn("**绝不写入源码目录**", trace, "SS-022-14 写权边界缺失")
        # SS-022-06：委派闸值分层 + steps/03 收窄为引用
        self.assertIn("一个类别合计 >10K tokens → 该类别派", skill, "Rule 7 分层闸值缺失")
        self.assertIn("按 `SKILL.md` 规则 7 的**分层闸值**", perim, "steps/03 未收窄为引用")
        # A-5（C1）：§4 读取纪律（母本定稿逐字）已在 test_mother_text_anchors 锁；此处锁 steps 引用面
        self.assertIn("`Read (input)` 行", skill, "缺执行期读取权威句")


if __name__ == "__main__":
    unittest.main()
