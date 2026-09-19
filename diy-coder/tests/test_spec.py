# -*- coding: utf-8 -*-
"""diy-quick-dev 确定性引擎 e2e 测试（B2 批 W4，任务书 §6 测试 / §2.5）。

覆盖：
- 用例 1：check 合法记录（起草态）exit 0 唯一放行 + 回执键完整（counts）
- 用例 2：check --final 合法记录 exit 0（status: 已完成 / tasks 全 done / verification 实测留证）
- 用例 3：status 枚举违例 → ENUM_INVALID；重复 SP id → DUPLICATE_ID；未知 --id → UNKNOWN_ID
- 用例 4：verification 空且 status 前进到 审查中 → EMPTY_FIELD（轻量 TDD 硬底线）
- 用例 5：tasks 未全 done 的 --final 拒绝；frozen intent 字段完整性（problem 缺失 → EMPTY_FIELD）
- 用例 6：SKILL.md 契约冒烟（母本 §1/§2/§3/§4 中文定稿逐字 + 四段中文标题 ≤93 行
          + 终门句指向 spec.py 且三处写死实参 + 读取纪律 + 渲染静默 + 无编辑器/自动提交
          + steps 6 文件在场且 B-15 语义条目锚串在位）
夹具全部落 tempdir 自建；不读写本仓库真实 diy-output。
运行：cd diy-coder && python -m unittest discover -s tests -p "test_spec.py" -v
"""
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.join(HERE, "..", "skills", "diy-quick-dev")
ENGINE = os.path.join(SKILL_DIR, "scripts", "spec.py")
SKILL_MD = os.path.join(SKILL_DIR, "SKILL.md")
NL = chr(10)

# 套件级句式母本（suite-texts.md §1 / §2 / §3 / §4 中文定稿，逐字）——2026-09-19 中文化轮：
# 英文原形（实例句 233 字符 / 纪律块 497 字符）随本技能转中文退役，改断中文定稿。
INSTANCE_ZH = ("实例解析（FR-4.5/D-9）由工具脚本执行：运行 "
               "`python \"{project-root}/.claude/skills/diy-tools/scripts/diyc.py\" "
               "resolve [--instance <name>] --json`，把回执里的 `output_dir` "
               "当作本次运行唯一的读写根目录。")
INSTANCE_EN_MARK = "Instance resolution (FR-4.5/D-9)"
RESOLVE_KEYS_ZH = ("解析 `project.communication_language` / "
                   "`project.document_output_language` / `paths.output_dir`")
READ_DISCIPLINE_ZH = ("读取纪律：预载预算 = 本文件、上述配置与回执、`steps/` 下当前那一个文件"
                      "——绝不批量预载；执行期读取以每个步骤开头的 `Read (input)` 行为唯一权威，"
                      "**主文件不列举封闭清单**。")
DISCIPLINE_ZH = ("- **写作纪律。** 主字段 = 大白话主句；数字/枚举内联；"
                 "机器语法（命令/旗标/路径）进括号；机器锚点逐字保留"
                 "（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 "
                 "`diy-design` 的 detect 启发式。schema 若定义 `plain`："
                 "一行写清该条目为什么存在，绝不写是什么（转述会漂移）；"
                 "只写难懂的条目。若定义 `detail`：过程叙述——结论留在主字段。")
PRECISE_ZH = ("- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；"
              "不复述上游已写的信息（引用 ID）；不写没有信息量的套话。")
# B-15 · SS-016-02：三处终门/结构检查命令写死实参，删「same as activation」指代
GATE_ARGS = "--project-root \"{project-root}\" --output-dir \"{output_dir}\""

STEPS_DIR = os.path.join(SKILL_DIR, "steps")

# 验收段（独立常量：测试用 replace 制造「verification 缺失」场景）
VERIFY_BLOCK = NL.join([
    "  verification:",
    "    commands:",
    "    - cmd: pytest tests/test_login.py",
    "      expect: 全绿",
    "      result: 3 passed",
]) + NL

ACCEPTANCE_BLOCK = NL.join([
    "  acceptance:",
    "  - given: 服务端返回 500",
    "    when: 客户端发起登录",
    "    then: 最多重试一次后返回失败",
    "    refs: []",
]) + NL

SPEC_YAML = NL.join([
    "project:",
    "  name: mini",
    "  status: 已定稿",
    "  created: '2026-01-01'",
    "  updated: '2026-09-14'",
    "specs:",
    "- id: SP-001",
    "  title: 登录失败重试",
    "  type: 缺陷修复",
    "  route: 计划-编码-审查",
    "  status: 已完成",
    "  date: '2026-09-14'",
    "  baseline: abc1234",
    "  intent:",
    "    problem: 登录失败后不重试",
    "    approach: 客户端加一次指数退避重试",
    "  boundaries:",
    "    总是:",
    "    - 保持既有 API 形状",
    "    先问:",
    "    - 改默认超时值",
    "    从不:",
    "    - 改后端协议",
    "  code_map:",
    "  - path: src/login_client.py",
    "    role: 重试逻辑落点",
    "  tasks:",
    "  - task: 加退避重试",
    "    file: src/login_client.py",
    "    done: true",
]) + NL + ACCEPTANCE_BLOCK + NL.join([
    "  change_log: []",
]) + NL + VERIFY_BLOCK + NL.join([
    "  deferred: []",
    "  review:",
    "    rounds: 1",
    "    findings: []",
    "  review_order:",
    "  - concern: 重试路径",
    "    stops:",
    "    - path: src/login_client.py",
    "      line: 42",
    "      why: 退避决策点",
    "  open_questions: []",
    "revisions: []",
]) + NL


def run_engine(args):
    return subprocess.run([sys.executable, ENGINE] + args,
                          capture_output=True, text=True, encoding="utf-8")


class EngineCase(unittest.TestCase):
    """tmp 项目根 + diy-output 目录的公共夹具。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="quickdev-")
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

    def spec(self, text=SPEC_YAML):
        return self.write("diy-output/spec.yaml", text)

    def check(self, *extra):
        return run_engine(["check", "--project-root", self.root,
                           "--output-dir", self.out, "--json"] + list(extra))

    def spec_path(self):
        return os.path.join(self.out, "spec.yaml")


class CheckPassTests(EngineCase):

    # trace: 任务书 §6 引擎 check（合法记录 exit 0 唯一放行 + 回执键完整）
    def test_check_legal_record_passes(self):
        self.spec()
        r = self.check()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("Traceback", r.stderr)
        data = json.loads(r.stdout)
        self.assertTrue(data["ok"])
        self.assertEqual(data["violations"], [])
        for key in ("ok", "command", "project_root", "output_dir", "violations",
                    "warnings", "counts"):
            self.assertIn(key, data, "回执缺共同键 %s" % key)
        self.assertEqual(data["counts"]["specs"], 1)
        self.assertEqual(data["counts"]["by_status"], {"已完成": 1})
        self.assertEqual(data["counts"]["by_route"], {"计划-编码-审查": 1})
        self.assertEqual(data["counts"]["tasks"], 1)

    # trace: 任务书 §6 check --final（status 已完成 / tasks 全 done / verification 实测留证）
    def test_check_final_legal_record_passes(self):
        self.spec()
        r = self.check("--final")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertTrue(data["ok"])
        self.assertEqual(data["violations"], [])

    # trace: 任务书 §6 check（--id 缩域：只校验该记录）
    def test_check_by_id_scopes_to_one_record(self):
        active = SPEC_YAML.replace("  status: 已完成", "  status: 草稿")
        self.spec(active)
        r = self.check("--id", "SP-001")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(json.loads(r.stdout)["ok"])
        r2 = self.check("--id", "SP-009")
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertIn("UNKNOWN_ID",
                      {x["code"] for x in json.loads(r2.stdout)["violations"]})


class CheckViolationTests(EngineCase):

    # trace: 任务书 §6 check（枚举：type / route / status）
    def test_check_reports_enum_violations(self):
        cases = [
            ("status", "  status: 已完成", "  status: shipped"),
            ("type", "  type: 缺陷修复", "  type: hotfix"),
            ("route", "  route: 计划-编码-审查", "  route: quick"),
        ]
        for name, old, new in cases:
            self.spec(SPEC_YAML.replace(old, new))
            r = self.check()
            self.assertEqual(r.returncode, 1, "%s: %s" % (name, r.stdout + r.stderr))
            data = json.loads(r.stdout)
            self.assertIn("ENUM_INVALID", {x["code"] for x in data["violations"]},
                          "%s 未报 ENUM_INVALID：%s" % (name, r.stdout))
            self.assertTrue(all(x.get("where") and x.get("msg")
                                for x in data["violations"]), r.stdout)

    # trace: 任务书 §6 门禁（verification 空 + status 前进到 审查中 → EMPTY_FIELD，
    #        轻量 TDD 的硬底线）
    def test_check_refuses_empty_verification_at_in_review(self):
        text = (SPEC_YAML.replace("  status: 已完成", "  status: 审查中")
                .replace(VERIFY_BLOCK, ""))
        self.spec(text)
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        data = json.loads(r.stdout)
        self.assertIn("EMPTY_FIELD", {x["code"] for x in data["violations"]})
        self.assertTrue(any("verification" in x["where"] for x in data["violations"]),
                        r.stdout)

    # trace: 任务书 §6 check --final（tasks 未全 done → 拒绝）
    def test_check_final_rejects_undone_task(self):
        self.spec(SPEC_YAML.replace("    done: true", "    done: false"))
        r = self.check("--final")
        self.assertEqual(r.returncode, 1, r.stdout)
        data = json.loads(r.stdout)
        self.assertIn("STATUS_MISMATCH", {x["code"] for x in data["violations"]})
        self.assertTrue(any("tasks[0]" in x["where"] for x in data["violations"]), r.stdout)

    # trace: 任务书 §6 check（frozen intent 两键完整性）
    def test_check_requires_frozen_intent_keys(self):
        self.spec(SPEC_YAML.replace("    problem: 登录失败后不重试" + NL, ""))
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        data = json.loads(r.stdout)
        self.assertIn("EMPTY_FIELD", {x["code"] for x in data["violations"]})
        self.assertTrue(any("intent.problem" in x["where"] for x in data["violations"]),
                        r.stdout)

    # trace: 任务书 §6 check --final（可实证性：verification.result 为空 → 拒绝 + 零假设）
    def test_check_final_duties(self):
        no_result = SPEC_YAML.replace("      result: 3 passed" + NL, "")
        self.spec(no_result)
        r = self.check("--final")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("EMPTY_FIELD", {x["code"] for x in json.loads(r.stdout)["violations"]})
        assumption = SPEC_YAML.replace("  title: 登录失败重试",
                                       "  title: '[假设] 登录失败重试'")
        self.spec(assumption)
        r2 = self.check("--final")
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertIn("ASSUMPTION_PRESENT",
                      {x["code"] for x in json.loads(r2.stdout)["violations"]})

    # trace: 任务书 §2.4（SP-### 格式 + 稳定 ID 不重用）
    def test_check_reports_id_shape_and_duplicates(self):
        self.spec(SPEC_YAML.replace("id: SP-001", "id: SP-1"))
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ENUM_INVALID", {x["code"] for x in json.loads(r.stdout)["violations"]})
        body = SPEC_YAML.split("specs:" + NL, 1)[1].replace("revisions: []" + NL, "")
        self.spec(SPEC_YAML.replace("revisions: []" + NL, "") + body)
        r2 = self.check()
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertIn("DUPLICATE_ID", {x["code"] for x in json.loads(r2.stdout)["violations"]})

    # trace: 任务书 §6 引擎（缺文件/损坏 → 结构化违规，不 Traceback；
    #        --output-dir 必填，引擎不做实例解析/目录推导）
    def test_check_missing_file_and_mandatory_output_dir(self):
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertNotIn("Traceback", r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual(data["violations"][0]["code"], "MISSING_FILE")
        self.assertEqual(data["counts"]["specs"], 0)
        self.spec("specs: [" + NL)
        r2 = self.check()
        self.assertEqual(r2.returncode, 1)
        self.assertNotIn("Traceback", r2.stderr)
        self.assertEqual(json.loads(r2.stdout)["violations"][0]["code"], "UNPARSABLE_YAML")
        r3 = run_engine(["check", "--project-root", self.root, "--json"])
        self.assertEqual(r3.returncode, 2, r3.stdout + r3.stderr)


class SkillContractTests(unittest.TestCase):
    """用例 6：SKILL.md / steps 契约冒烟（母本中文定稿逐字 + 终门句指向本技能引擎）。"""

    def read(self, path):
        if not os.path.isfile(path):
            self.skipTest("%s 尚未交付" % os.path.basename(path))
        with io.open(path, encoding="utf-8") as f:
            return f.read()

    def read_skill(self):
        return self.read(SKILL_MD)

    # trace: 任务书 §2.1 / 母本 §1（实例解析句中文定稿逐字；英文原形已随中文化退役）
    def test_instance_sentence_is_mother_copy_verbatim(self):
        raw = self.read_skill()
        self.assertIn(INSTANCE_ZH, raw, "SKILL.md 缺母本 §1 中文定稿（逐字）")
        self.assertNotIn(INSTANCE_EN_MARK, raw, "已转中文定稿，仍残留英文原形")

    # trace: 任务书 §2.1 / 母本 §3（配置键全路径带 project. 前缀 + 读取纪律 §4）
    def test_resolve_keys_and_read_discipline_verbatim(self):
        raw = self.read_skill()
        self.assertIn(RESOLVE_KEYS_ZH, raw, "SKILL.md 缺母本 §3 键路径锚串")
        self.assertIn(READ_DISCIPLINE_ZH, raw, "SKILL.md 缺母本 §4 定稿（逐字）")

    # trace: 任务书 §2.1 / 母本 §2 + §6（两板块逐字；§6 在前、§2 收尾）
    def test_precise_and_writing_discipline_at_rules_end(self):
        raw = self.read_skill()
        self.assertIn(PRECISE_ZH, raw, "SKILL.md 缺母本 §6 中文定稿")
        self.assertIn(DISCIPLINE_ZH, raw, "SKILL.md 缺母本 §2 中文定稿")
        self.assertLess(raw.index(PRECISE_ZH), raw.index(DISCIPLINE_ZH),
                        "Rules 末尾顺序须为：§6 精准简练 → §2 写作纪律")
        self.assertEqual(DISCIPLINE_ZH, raw.rstrip(NL).splitlines()[-1],
                         "写作纪律块须置 Rules 段末尾（文件收尾行）")

    # trace: 中文化轮（薄主文件 ≤93 行 + 四段中文标题 + 工作流点名六步）
    def test_thin_main_file_four_chinese_sections(self):
        raw = self.read_skill()
        self.assertLessEqual(len(raw.splitlines()), 93, "薄主文件超出 93 行预算")
        for section in ("## 激活时", "## 工作流", "## 结构", "## 规则"):
            self.assertIn(section, raw, "缺四段结构：%s" % section)
        for name in ("01-clarify-route.md", "02-plan.md", "03-implement.md",
                     "04-review.md", "05-present.md", "06-oneshot.md"):
            self.assertIn(name, raw, "工作流未点名 %s" % name)

    # trace: 任务书 §6 steps 切分（6 文件）/§2.1（终门句/渲染静默/不自动 git）
    def test_final_gate_and_disciplines(self):
        skill = self.read_skill()
        self.assertIn("spec.py", skill, "终门句未指向领域引擎")
        self.assertIn("check --final", skill, "终门句缺 check --final")
        self.assertIn("--json", skill, "终门句缺 --json 回执")
        self.assertIn("绝不批量预载", skill, "缺读取成本纪律")
        self.assertIn("viewer.py", skill, "缺渲染静默命令")
        self.assertNotIn("code -r", skill, "不得打开编辑器（源 step-05/oneshot 的 code -r 应裁剪）")
        self.assertNotIn("bmad-", skill, "不得引用不存在的技能")
        steps = ["01-clarify-route.md", "02-plan.md", "03-implement.md",
                 "04-review.md", "05-present.md", "06-oneshot.md"]
        for name in steps:
            path = os.path.join(STEPS_DIR, name)
            self.assertTrue(os.path.isfile(path), "缺步骤文件 %s" % name)

    # trace: B-15 · SS-016-02（三处写死 `--project-root` / `--output-dir` 实参，
    #         删「同 activation」指代：SKILL.md Rule 8 + steps/05 + steps/06）
    def test_gate_commands_spell_out_arguments(self):
        for path in (SKILL_MD,
                     os.path.join(STEPS_DIR, "05-present.md"),
                     os.path.join(STEPS_DIR, "06-oneshot.md")):
            text = self.read(path)
            self.assertIn(GATE_ARGS, text, "%s 终门命令未写死实参" % os.path.basename(path))
            self.assertNotIn("as activation", text, "%s 仍留「同 activation」指代"
                             % os.path.basename(path))

    # trace: B-15 · SS-016-05/08（水位线语义 + L4 边界等价命令全路径）
    def test_waterline_and_l4_boundary(self):
        raw = self.read_skill()
        self.assertIn("文件水位线", raw, "缺 SS-016-05 水位线语义")
        self.assertIn("L4 边界", raw, "缺 SS-016-08 L4 边界声明")
        self.assertIn('skills/diy-design/scripts/design.py" audit --design', raw,
                      "L4 等价检查须写 design.py 全路径（A-11）")
        self.assertIn('skills/diy-design/scripts/design.py" check --design', raw,
                      "L4 等价检查须写 design.py 全路径（A-11）")

    # trace: B-15 · SS-016-03/04/07 · SS-016-06（steps 侧口径与断点恢复补句）
    def test_b15_step_level_anchors(self):
        checks = [
            ("02-plan.md", "字符数 ÷ 2", "SS-016-07 spec body 计数口径未钉死"),
            ("02-plan.md", "不构成阻断", "SS-016-07 须声明计数误差不构成阻断"),
            ("06-oneshot.md", "L3 由上面的「验证」段承担", "SS-016-04 缺 L3 归属声明"),
            ("06-oneshot.md", "覆盖审计", "SS-016-04 覆盖类问题的 layer 取值未点名"),
            ("06-oneshot.md", "code_map` ＝ 改动文件一行一条", "SS-016-03 缺 code_map 口径"),
            ("06-oneshot.md", "`tasks` ≥1 条", "SS-016-03 缺 tasks 非空口径"),
            ("01-clarify-route.md", "先建草稿记录", "SS-016-06 缺「先建 draft 记录」"),
            ("01-clarify-route.md", "尚未定 `route`", "SS-016-06 缺断点恢复补句"),
        ]
        for name, anchor, msg in checks:
            self.assertIn(anchor, self.read(os.path.join(STEPS_DIR, name)),
                          "%s：%s" % (name, msg))


if __name__ == "__main__":
    unittest.main()
