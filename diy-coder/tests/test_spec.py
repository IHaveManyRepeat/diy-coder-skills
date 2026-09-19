# -*- coding: utf-8 -*-
"""diy-quick-dev 确定性引擎 e2e 测试（B2 批 W4，任务书 §6 测试 / §2.5）。

覆盖：
- 用例 1：check 合法记录（起草态）exit 0 唯一放行 + 回执键完整（counts）
- 用例 2：check --final 合法记录 exit 0（status: 已完成 / tasks 全 done / verification 实测留证）
- 用例 3：status 枚举违例 → ENUM_INVALID；重复 SP id → DUPLICATE_ID；未知 --id → UNKNOWN_ID
- 用例 4：verification 空且 status 前进到 审查中 → EMPTY_FIELD（轻量 TDD 硬底线）
- 用例 5：tasks 未全 done 的 --final 拒绝；frozen intent 字段完整性（problem 缺失 → EMPTY_FIELD）
- 用例 6：SKILL.md 契约冒烟（冻结实例句 233/md5 + 写作纪律块 497/md5 + 终门句指向 spec.py
          + 读取成本纪律 + 渲染静默 + 无编辑器/自动提交 + steps 6 文件在场）
夹具全部落 tempdir 自建；不读写本仓库真实 diy-output。
运行：cd diy-coder && python -m unittest discover -s tests -p "test_spec.py" -v
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
SKILL_DIR = os.path.join(HERE, "..", "skills", "diy-quick-dev")
ENGINE = os.path.join(SKILL_DIR, "scripts", "spec.py")
SKILL_MD = os.path.join(SKILL_DIR, "SKILL.md")
NL = chr(10)

# 冻结文本校验值（batch4/frozen-texts.md §1/§2：逐字复制，md5 口径 = 文本 + 行尾 LF）
INSTANCE_MD5 = "5445f98bc4d4821e6888b89406a97eac"
DISCIPLINE_MD5 = "f1b3b6fbb528f0cfab31f3196b3547ae"
INSTANCE_ANCHOR = "Instance resolution (FR-4.5/D-9)"
DISCIPLINE_ANCHOR = "- **Writing discipline."

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
    """用例 6：SKILL.md / steps 契约冒烟（冻结文本逐字 + 终门句指向本技能引擎）。"""

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

    # trace: 任务书 §6 steps 切分（6 文件）/§2.1（终门句/读取纪律/渲染静默/不自动 git）
    def test_final_gate_and_disciplines(self):
        skill = self.read_skill()
        self.assertIn("spec.py", skill, "终门句未指向领域引擎")
        self.assertIn("check --final", skill, "终门句缺 check --final")
        self.assertIn("--json", skill, "终门句缺 --json 回执")
        self.assertIn("never batch-load", skill, "缺读取成本纪律")
        self.assertIn("viewer.py", skill, "缺渲染静默命令")
        self.assertNotIn("code -r", skill, "不得打开编辑器（源 step-05/oneshot 的 code -r 应裁剪）")
        self.assertNotIn("bmad-", skill, "不得引用不存在的技能")
        steps = ["01-clarify-route.md", "02-plan.md", "03-implement.md",
                 "04-review.md", "05-present.md", "06-oneshot.md"]
        for name in steps:
            path = os.path.join(SKILL_DIR, "steps", name)
            self.assertTrue(os.path.isfile(path), "缺步骤文件 %s" % name)


if __name__ == "__main__":
    unittest.main()
