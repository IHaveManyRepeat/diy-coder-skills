# -*- coding: utf-8 -*-
"""diy-e2e-tests 确定性引擎测试（B2 批 W6，任务书 §8 / §2.5）。

覆盖：
- 用例 1：detect 在合成 package.json 夹具上识别框架（playwright）
- 用例 2：detect 在 pyproject.toml 夹具上识别 pytest；损坏清单降级不崩
- 用例 3：detect 无清单 → framework null + suggested 非空（不自动安装）
- 用例 4：record 追加合法 TC（status: pass）→ exit 0 + diyc 交叉核对键在场
- 用例 5：record 拒绝重号 TC（DUPLICATE_ID）、technique 非 scenario（ENUM_INVALID）、
          悬空 ac（UNKNOWN_ID）—— 全部零写入
- 用例 6：record 缺 test-plan.yaml（MISSING_FILE）/ --output-dir 必填（exit 2）
- 用例 7：SKILL.md 契约冒烟（冻结实例句 + 写作纪律块逐字 md5；终门句指向 e2e.py record）

夹具全部落 tempdir 自建；不读写本仓库真实 diy-output；不依赖本机 git 状态。
运行：cd diy-coder && python -m unittest discover -s tests -p "test_e2e.py" -v
"""
import hashlib
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
ENGINE = os.path.join(HERE, "..", "skills", "diy-e2e-tests", "scripts", "e2e.py")
SKILL_MD = os.path.join(HERE, "..", "skills", "diy-e2e-tests", "SKILL.md")
NL = chr(10)

# 冻结文本校验值（batch4/frozen-texts.md：实例句 233 字符 / 纪律块 497 字符，逐字复制）
INSTANCE_MD5 = "5445f98bc4d4821e6888b89406a97eac"
DISCIPLINE_MD5 = "f1b3b6fbb528f0cfab31f3196b3547ae"

STORIES_YAML = NL.join([
    "project:",
    "  name: mini",
    "  status: final",
    "  created: '2026-01-01'",
    "  updated: '2026-01-02'",
    "stories:",
    "- id: S-1",
    "  title: 一",
    "  status: done",
    "  acceptance_criteria:",
    "  - id: AC-1.1",
    "    given: 夹具",
    "    when: 夹具",
    "    then: 夹具",
    "    refs: []",
]) + NL

TEST_PLAN_YAML = NL.join([
    "project:",
    "  name: mini",
    "  status: final",
    "  created: '2026-01-01'",
    "  updated: '2026-01-02'",
    "test_cases:",
    "- id: TC-1.1.1",
    "  title: 既有单元用例",
    "  ac: AC-1.1",
    "  type: unit",
    "  priority: P0",
    "  technique: boundary",
    "  kill_target: 边界值未被拦截",
    "  status: pass",
    "  steps:",
    "  - 跑夹具断言",
    "coverage_gaps: []",
    "static_checks: []",
]) + NL

PACKAGE_JSON = json.dumps({
    "name": "mini",
    "devDependencies": {"@playwright/test": "^1.40.0", "typescript": "^5.0.0"},
}, ensure_ascii=False) + NL


def run_engine(args):
    return subprocess.run([sys.executable, ENGINE] + args,
                          capture_output=True, text=True, encoding="utf-8")


def tc_json(tc_id="TC-1.1.2", technique="scenario", ac="AC-1.1", status="pass",
            type_name="e2e"):
    return json.dumps([{
        "id": tc_id,
        "title": "登录流程端到端",
        "ac": ac,
        "type": type_name,
        "priority": "P0",
        "technique": technique,
        "kill_target": "用户旅程在中途静默中断（页面已跳转但状态未持久化）",
        "status": status,
        "steps": ["打开 /login", "填写表单并提交", "断言跳转且会话可复用"],
    }], ensure_ascii=False)


class EngineCase(unittest.TestCase):
    """tmp 项目根 + diy-output 目录的公共夹具。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="e2e-")
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

    def read(self, rel):
        with io.open(os.path.join(self.root, rel), encoding="utf-8") as f:
            return f.read()

    def detect(self, *extra):
        return run_engine(["detect", "--project-root", self.root,
                           "--output-dir", self.out, "--json"] + list(extra))

    def record(self, tc_file, *extra):
        return run_engine(["record", "--tc-file", tc_file,
                           "--project-root", self.root,
                           "--output-dir", self.out, "--json"] + list(extra))

    def plan_path(self):
        return os.path.join(self.out, "test-plan.yaml")


class DetectTests(EngineCase):

    # trace: 任务书 §8（detect 语言无关：清单探测 → 框架识别）
    def test_detect_finds_playwright_in_package_json(self):
        self.write("package.json", PACKAGE_JSON)
        self.write("tests/e2e/login.spec.ts", "// spec" + NL)
        r = self.detect()
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        data = json.loads(r.stdout)
        self.assertTrue(data["ok"])
        self.assertEqual(data["framework"]["name"], "playwright")
        self.assertEqual(data["framework"]["detected_from"], "package.json")
        self.assertEqual(data["project_type"], "node")
        self.assertIn("tests", data["test_dirs"])
        self.assertTrue(any("login.spec.ts" in p for p in data["existing_patterns"]),
                        data["existing_patterns"])
        self.assertIsNone(data["suggested"])

    # trace: 任务书 §8（Python 清单探测；损坏清单降级 warning 不崩）
    def test_detect_python_manifest_and_broken_manifest_degrades(self):
        self.write("pyproject.toml", NL.join([
            "[project]",
            'name = "mini"',
            "[project.optional-dependencies]",
            'test = ["pytest>=8", "pytest-cov"]',
        ]) + NL)
        data = json.loads(self.detect().stdout)
        self.assertEqual(data["framework"]["name"], "pytest")
        self.assertEqual(data["project_type"], "python")
        # 损坏清单：不 Traceback、降级为 warning、探测继续
        self.write("package.json", "{ not json" + NL)
        r2 = self.detect()
        self.assertEqual(r2.returncode, 0, r2.stderr + r2.stdout)
        self.assertNotIn("Traceback", r2.stderr)
        data2 = json.loads(r2.stdout)
        self.assertTrue(data2["warnings"], "损坏清单须有结构化 warning")
        self.assertEqual(data2["framework"]["name"], "pytest")

    # trace: 任务书 §8（无框架 → 回 suggested，不自动安装）
    def test_detect_without_framework_suggests_not_installs(self):
        r = self.detect()  # 空项目
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        data = json.loads(r.stdout)
        self.assertIsNone(data["framework"])
        self.assertTrue(data["suggested"], "无框架须给出建议（人类确认，不自动安装）")
        self.assertEqual(data["existing_patterns"], [])
        # 未安装任何东西：项目根保持空（除 diy-output）
        self.assertEqual(sorted(os.listdir(self.root)), ["diy-output"])


class RecordTests(EngineCase):

    def setUp(self):
        super().setUp()
        self.write("diy-output/stories.yaml", STORIES_YAML)
        self.write("diy-output/test-plan.yaml", TEST_PLAN_YAML)
        self.before = self.read("diy-output/test-plan.yaml")

    # trace: 任务书 §8（record 追加合法 TC + diyc 交叉核对）
    def test_record_appends_legal_tc(self):
        tc = self.write("new-tc.json", tc_json())
        r = self.record(tc)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        data = json.loads(r.stdout)
        self.assertTrue(data["ok"])
        self.assertEqual(data["appended"], ["TC-1.1.2"])
        self.assertEqual(data["counts"]["appended"], 1)
        plan = self.read("diy-output/test-plan.yaml")
        self.assertIn("id: TC-1.1.2", plan)
        self.assertIn("technique: scenario", plan)
        self.assertIn("type: e2e", plan)
        # 既有条目不被触碰
        self.assertIn("id: TC-1.1.1", plan)
        self.assertIn("technique: boundary", plan)
        # diyc 交叉核对键在场（不阻塞写权结论）
        self.assertIn("diyc", data)
        self.assertTrue(data["diyc"]["available"])
        self.assertEqual(data["diyc"]["check"]["violations"], [], data["diyc"])

    # trace: 任务书 §8（重号拒绝：DUPLICATE_ID，零写入）
    def test_record_rejects_duplicate_id_with_zero_write(self):
        tc = self.write("new-tc.json", tc_json(tc_id="TC-1.1.1"))
        r = self.record(tc)
        self.assertEqual(r.returncode, 1, r.stdout)
        data = json.loads(r.stdout)
        self.assertFalse(data["ok"])
        self.assertIn("DUPLICATE_ID", {x["code"] for x in data["violations"]})
        self.assertEqual(self.read("diy-output/test-plan.yaml"), self.before)

    # trace: 任务书 §8（technique 非 scenario 拒绝：ENUM_INVALID）
    def test_record_rejects_non_scenario_technique(self):
        tc = self.write("new-tc.json", tc_json(technique="boundary"))
        r = self.record(tc)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ENUM_INVALID", {x["code"] for x in json.loads(r.stdout)["violations"]})
        self.assertEqual(self.read("diy-output/test-plan.yaml"), self.before)
        # type 非 e2e 同样拒绝
        tc2 = self.write("new-tc2.json", tc_json(type_name="unit"))
        r2 = self.record(tc2)
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertIn("ENUM_INVALID", {x["code"] for x in json.loads(r2.stdout)["violations"]})
        self.assertEqual(self.read("diy-output/test-plan.yaml"), self.before)

    # trace: 任务书 §8（ac 悬空拒绝：UNKNOWN_ID；id 须与 ac 前缀一致）
    def test_record_rejects_unknown_ac_and_id_ac_mismatch(self):
        tc = self.write("new-tc.json", tc_json(tc_id="TC-9.9.1", ac="AC-9.9"))
        r = self.record(tc)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("UNKNOWN_ID", {x["code"] for x in json.loads(r.stdout)["violations"]})
        self.assertEqual(self.read("diy-output/test-plan.yaml"), self.before)
        # id 的 AC 前缀与 ac 不一致 → 条目非法（ENTRY_INVALID）
        tc2 = self.write("new-tc2.json", tc_json(tc_id="TC-1.2.1", ac="AC-1.1"))
        r2 = self.record(tc2)
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertIn("ENTRY_INVALID", {x["code"] for x in json.loads(r2.stdout)["violations"]})
        self.assertEqual(self.read("diy-output/test-plan.yaml"), self.before)

    # trace: 任务书 §8（status 集合 / steps 非空 / kill_target 非空）
    def test_record_rejects_pending_status_and_empty_fields(self):
        tc = self.write("new-tc.json", tc_json(status="pending"))
        r = self.record(tc)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ENUM_INVALID", {x["code"] for x in json.loads(r.stdout)["violations"]})
        # kill_target 空 → EMPTY_FIELD
        entry = json.loads(tc_json())
        entry[0]["kill_target"] = "  "
        tc2 = self.write("new-tc2.json", json.dumps(entry, ensure_ascii=False))
        r2 = self.record(tc2)
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertIn("EMPTY_FIELD", {x["code"] for x in json.loads(r2.stdout)["violations"]})
        # steps 空 → EMPTY_FIELD
        entry[0]["kill_target"] = "有效的故障假设"
        entry[0]["steps"] = []
        tc3 = self.write("new-tc3.json", json.dumps(entry, ensure_ascii=False))
        r3 = self.record(tc3)
        self.assertEqual(r3.returncode, 1, r3.stdout)
        self.assertIn("EMPTY_FIELD", {x["code"] for x in json.loads(r3.stdout)["violations"]})
        self.assertEqual(self.read("diy-output/test-plan.yaml"), self.before)

    # trace: 任务书 §8（上游缺席 → MISSING_FILE；--output-dir 必填 → exit 2）
    def test_record_gate_and_mandatory_output_dir(self):
        os.remove(self.plan_path())
        tc = self.write("new-tc.json", tc_json())
        r = self.record(tc)
        self.assertEqual(r.returncode, 1, r.stdout)
        data = json.loads(r.stdout)
        self.assertNotIn("Traceback", r.stderr)
        self.assertEqual(data["violations"][0]["code"], "MISSING_FILE")
        self.assertFalse(os.path.exists(self.plan_path()), "零产出：不得新建 test-plan.yaml")
        # tc-file 缺失 → 结构化违规
        r2 = self.record(os.path.join(self.root, "absent.json"))
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertIn("MISSING_FILE", {x["code"] for x in json.loads(r2.stdout)["violations"]})
        # --output-dir 必填（引擎不做实例解析/目录推导）
        r3 = run_engine(["record", "--tc-file", tc, "--project-root", self.root, "--json"])
        self.assertEqual(r3.returncode, 2, r3.stdout + r3.stderr)
        r4 = run_engine(["detect", "--project-root", self.root, "--json"])
        self.assertEqual(r4.returncode, 2, r4.stdout + r4.stderr)


class DiycDegradeTests(unittest.TestCase):
    """用例 7：diyc 缺席 → TOOL_MISSING 降级，不崩不阻塞写权结论（契约 §2.3）。"""

    def test_diyc_missing_degrades_to_warning(self):
        if not os.path.isfile(ENGINE):
            self.skipTest("引擎尚未交付")
        import importlib.util
        prev = sys.dont_write_bytecode
        sys.dont_write_bytecode = True  # 不在技能目录留 __pycache__（install.py 会整树复制）
        try:
            spec = importlib.util.spec_from_file_location("e2e_engine", ENGINE)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
        finally:
            sys.dont_write_bytecode = prev
        tmp = tempfile.mkdtemp(prefix="e2e-degrade-")
        try:
            block, warnings = mod.diyc_check_test_plan(
                os.path.join(tmp, "absent", "diyc.py"), tmp,
                os.path.join(tmp, "diy-output"))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        self.assertFalse(block["available"])
        self.assertEqual([w["code"] for w in warnings], ["TOOL_MISSING"])
        self.assertEqual(block["check"]["violations"], [])


class SkillContractTests(unittest.TestCase):
    """用例 8：SKILL.md 契约冒烟（冻结文本逐字 + 终门指向本技能引擎）。"""

    def read_skill(self):
        if not os.path.isfile(SKILL_MD):
            self.skipTest("SKILL.md 尚未交付（W6 并行中）——契约用例待补")
        with io.open(SKILL_MD, encoding="utf-8") as f:
            return f.read()

    # trace: 任务书 §2.1（冻结实例句逐字；md5 口径同 frozen-texts §3 复现命令）
    def test_instance_sentence_is_frozen_verbatim(self):
        raw = self.read_skill()
        m = re.search(r"Instance resolution \(FR-4\.5/D-9\)[^\r\n]*", raw)
        self.assertTrue(m, "SKILL.md 缺实例解析样板句")
        frag = m.group(0)
        self.assertEqual(len(frag), 233, "实例句字符数偏离冻结文本（233）")
        self.assertEqual(hashlib.md5((frag + NL).encode("utf-8")).hexdigest(), INSTANCE_MD5)

    # trace: 任务书 §2.1（写作纪律块逐字，置 Rules 段末尾）
    def test_writing_discipline_block_is_frozen_verbatim(self):
        raw = self.read_skill()
        m = re.search(r"^- \*\*Writing discipline\..*$", raw, re.MULTILINE)
        self.assertTrue(m, "SKILL.md 缺写作纪律块")
        frag = m.group(0)
        self.assertEqual(len(frag), 497, "纪律块字符数偏离冻结文本（497）")
        self.assertEqual(hashlib.md5((frag + NL).encode("utf-8")).hexdigest(), DISCIPLINE_MD5)
        self.assertEqual(frag, raw.rstrip(NL).splitlines()[-1], "纪律块须置 Rules 段末尾")

    # trace: 任务书 §2.1（终门句指向本技能引擎 record）
    def test_final_gate_points_to_engine(self):
        skill = self.read_skill()
        self.assertIn("e2e.py", skill, "终门句未指向领域引擎")
        self.assertIn("record", skill, "终门句缺 record 子命令")
        self.assertIn("--json", skill, "终门句缺 --json 回执")


if __name__ == "__main__":
    unittest.main()
