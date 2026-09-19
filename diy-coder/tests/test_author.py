# -*- coding: utf-8 -*-
"""diy-test-author 确定性引擎测试（B3 批 W1，任务书 §3 测试清单 / §2.5）。

覆盖（任务书 §3「测试」清单 11 项 + 回执/用法边界）：
- 用例 1：门禁——test-plan 非已定稿拒绝（STATUS_MISMATCH，零产出）
- 用例 2：门禁——TC 锚悬空拒绝（UNKNOWN_ID，零产出）
- 用例 3：门禁——范围内 TC 已通过拒绝（空跑不静默；红相脚手架只覆盖待办）
- 用例 4：门禁——kill_target 缺失拒绝（EMPTY_FIELD）
- 用例 5：detect 在合成 package.json 夹具上识别框架（playwright）
- 用例 6：audit 检出 skip 缺失（SKIP_MISSING）
- 用例 7：audit 检出缺 TC 锚（ANCHOR_MISSING）
- 用例 8：audit 检出 CSS selector（BRITTLE_SELECTOR）与 waitForTimeout（HARD_WAIT）
- 用例 9：audit 规则集（HARDCODED_DATA 判在 test 体内 / 工厂文件豁免 /
          PLACEHOLDER_ASSERTION / MISSING_ASSERTION / NOT_ATOMIC）
- 用例 10：audit 主命令合法 exit 0 + 回执键完整
- 用例 12：--files 必填 / 文件缺席 / --output-dir 必填（用法与门禁边界）
- 用例 13：SKILL.md 契约冒烟（母本 §1/§3/§4 定稿逐字 + §2 纪律块置 Rules 末尾 +
          终门句指向本技能引擎 audit）

V 能力补项返工（2026-09-18，能力清点 §1.1 六条丢失项 A-1..A-6）：
- 用例 14：A-1 用例名优先级标签（缺 → PRIORITY_TAG_MISSING / 与锚定 TC 的 priority
          不一致 → PRIORITY_TAG_MISMATCH / py 文档字符串载体放行）
- 用例 15：A-2 顺序依赖与共享状态（ORDER_DEPENDENCY / SHARED_STATE，含 py global）
- 用例 16：A-2 用例体内的随机与时钟源（NONDETERMINISTIC_SOURCE；工厂文件豁免）
- 用例 17：A-3 Given-When-Then 与用例名（GWT_MISSING / NAME_UNDESCRIPTIVE）
- 用例 18：A-4 夹具 teardown 清理（FIXTURE_NO_TEARDOWN；纯生成器工厂豁免）
- 用例 19：A-5 try-catch 只许清理（TRY_CATCH_TEST_LOGIC；清理用途放行）
- 用例 20：A-6 调试语句（DEBUG_STATEMENT；注释里的不算）
- 用例 21：引擎 docstring 违规码登记面（本次新增 10 码逐一在场）

夹具全部落 tempdir 自建；不读写本仓库真实 diy-output；不依赖本机 git 状态。
运行：cd diy-coder && python -m unittest discover -s tests -p "test_author.py" -v
"""
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.join(HERE, "..", "skills", "diy-test-author")
ENGINE = os.path.join(SKILL_DIR, "scripts", "author.py")
SKILL_MD = os.path.join(SKILL_DIR, "SKILL.md")
NL = chr(10)

# 套件级句式母本（suite-texts.md §1 / §2 / §3 / §4 中文定稿，逐字）
INSTANCE_ZH = ("实例解析（FR-4.5/D-9）由工具脚本执行：运行 "
               "`python \"{project-root}/.claude/skills/diy-tools/scripts/diyc.py\" "
               "resolve [--instance <name>] --json`，把回执里的 `output_dir` "
               "当作本次运行唯一的读写根目录。")
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


def test_plan(status="已定稿", tc_status="待办", kill_target="边界值未被拦截",
              technique="boundary", tc_id="TC-1.1.1"):
    """最小 test-plan.yaml 夹具（本技能只读：门禁 + TC 自检面）。"""
    lines = [
        "project:",
        "  name: mini",
        "  status: " + status,
        "  created: '2026-01-01'",
        "  updated: '2026-01-02'",
        "test_cases:",
        "- id: " + tc_id,
        "  title: 边界用例",
        "  ac: AC-1.1",
        "  type: unit",
        "  priority: P0",
        "  technique: " + technique,
        "  kill_target: " + kill_target,
        "  status: " + tc_status,
        "  steps:",
        "  - 跑夹具断言",
        "static_checks: []",
        "coverage_gaps: []",
    ]
    return NL.join(lines) + NL


JS_PRECODE_OK = NL.join([
    "// TC: TC-1.1.1",
    "test('[P0] 边界值被拦截', async () => {",
    "  test.skip();",
    "  // Given 一个未实现的边界输入",
    "  // When 调用 compute(1)",
    "  // Then 期望返回 2",
    "  // 实现指引：compute(1) 当前未实现，实现后去掉 skip",
    "  expect(compute(1)).toBe(2);",
    "});",
]) + NL

PY_PRECODE_OK = NL.join([
    "# TC: TC-1.1.1",
    "def test_boundary():",
    "    \"\"\"[P0] 边界值被拦截\"\"\"",
    "    pytest.skip('待实现')",
    "    # Given 一个未实现的边界输入",
    "    # When 调用 compute(1)",
    "    # Then 期望返回 2",
    "    # 实现指引：不要用 page.wait_for_timeout(500)——改为状态等待",
    "    assert compute(1) == 2",
]) + NL

PACKAGE_JSON = json.dumps({
    "name": "mini",
    "devDependencies": {"@playwright/test": "^1.40.0", "typescript": "^5.0.0"},
}, ensure_ascii=False) + NL


def run_engine(args):
    return subprocess.run([sys.executable, ENGINE] + args,
                          capture_output=True, text=True, encoding="utf-8")


def codes(result):
    """回执里的违规码集合。"""
    return {x["code"] for x in json.loads(result.stdout)["violations"]}


class EngineCase(unittest.TestCase):
    """tmp 项目根 + diy-output 目录的公共夹具。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="author-")
        self.root = self.tmp.name
        self.out = os.path.join(self.root, "diy-output")
        os.makedirs(self.out, exist_ok=True)
        self.write("diy-output/test-plan.yaml", test_plan())

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

    def snapshot(self):
        """项目根下的全部文件与内容（零产出的证据面）。"""
        seen = {}
        for dirpath, _dirnames, filenames in os.walk(self.root):
            for name in filenames:
                full = os.path.join(dirpath, name)
                with io.open(full, "rb") as f:
                    seen[os.path.relpath(full, self.root).replace("\\", "/")] = f.read()
        return seen

    def spec(self, rel, content):
        """写一份测试规格文件，返回其绝对路径。"""
        return self.write(rel, content)

    def audit(self, files, *extra):
        args = ["audit"]
        for path in files:
            args += ["--files", path]
        args += ["--project-root", self.root, "--output-dir", self.out, "--json"]
        return run_engine(args + list(extra))

    def detect(self, *extra):
        return run_engine(["detect", "--project-root", self.root,
                           "--output-dir", self.out, "--json"] + list(extra))


class GateTests(EngineCase):
    """门禁面：不满足即拒绝（exit 1 + 对应违规码 + 零产出）。"""

    # trace: 任务书 §3 门禁（test-plan 存在且 status: 已定稿）
    def test_gate_rejects_non_final_test_plan(self):
        spec = self.spec("tests/boundary.spec.ts", JS_PRECODE_OK)
        self.write("diy-output/test-plan.yaml", test_plan(status="草稿"))
        before = self.snapshot()
        r = self.audit([spec])
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertFalse(data["ok"])
        self.assertIn("STATUS_MISMATCH", {x["code"] for x in data["violations"]})
        self.assertEqual(self.snapshot(), before, "零产出：拒绝路径不得写任何文件")

    # trace: 任务书 §3 门禁（选定范围内的 TC 存在/锚可解析）
    def test_gate_rejects_unknown_tc_anchor(self):
        spec = self.spec("tests/boundary.spec.ts",
                         JS_PRECODE_OK.replace("TC-1.1.1", "TC-9.9.9"))
        before = self.snapshot()
        r = self.audit([spec])
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertIn("UNKNOWN_ID", {x["code"] for x in data["violations"]})
        self.assertEqual(self.snapshot(), before, "零产出：悬空 TC 锚不得落任何文件")

    # trace: 任务书 §3 门禁（范围内无可做 TC：全通过不得静默空跑）
    def test_gate_rejects_pass_tc_in_scope(self):
        spec = self.spec("tests/boundary.spec.ts", JS_PRECODE_OK)
        self.write("diy-output/test-plan.yaml", test_plan(tc_status="通过"))
        self.assertEqual(run_engine(["audit"]).returncode, 2)  # 缺 --files → 用法错误
        r = self.audit([spec])
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("STATUS_MISMATCH", {x["code"] for x in json.loads(r.stdout)["violations"]})

    # trace: 任务书 §3 门禁（TC 现场自检：technique / kill_target 非空）
    def test_gate_rejects_empty_kill_target(self):
        spec = self.spec("tests/boundary.spec.ts", JS_PRECODE_OK)
        self.write("diy-output/test-plan.yaml", test_plan(kill_target="''"))
        r = self.audit([spec])
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("EMPTY_FIELD", {x["code"] for x in json.loads(r.stdout)["violations"]})


class DetectTests(EngineCase):

    # trace: 任务书 §3（技术栈推断：清单探测 → 框架识别；探测面与 e2e.py 三张常量表对齐）
    def test_detect_identifies_framework_in_package_json(self):
        self.write("package.json", PACKAGE_JSON)
        self.write("tests/support/factories/user.ts", "export const user = () => ({});" + NL)
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
        self.assertTrue(any("factories" in p for p in data["fixtures"]["files"]),
                        data["fixtures"])
        self.assertIsNone(data["suggested"])

    # trace: 任务书 §3（无框架 → suggested 非空；本技能不装框架，路由 diy-test-framework）
    def test_detect_without_framework_suggests_and_never_installs(self):
        r = self.detect()
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        data = json.loads(r.stdout)
        self.assertIsNone(data["framework"])
        self.assertTrue(data["suggested"], "无框架须给出建议（路由 diy-test-framework，不自动安装）")
        self.assertEqual(sorted(os.listdir(self.root)), ["diy-output"], "探测不得写任何文件")


class AuditPreCodeTests(EngineCase):

    # trace: 任务书 §3（红相形态：每个 test 体含 skip）
    def test_audit_precode_flags_missing_skip(self):
        spec = self.spec("tests/boundary.spec.ts", JS_PRECODE_OK.replace("  test.skip();" + NL, ""))
        r = self.audit([spec])
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("SKIP_MISSING", {x["code"] for x in json.loads(r.stdout)["violations"]})

    # trace: 任务书 §3（红相形态：每个用例带 TC 锚）
    def test_audit_precode_flags_missing_tc_anchor(self):
        spec = self.spec("tests/boundary.spec.ts", JS_PRECODE_OK.replace("// TC: TC-1.1.1" + NL, ""))
        r = self.audit([spec])
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ANCHOR_MISSING", {x["code"] for x in json.loads(r.stdout)["violations"]})

    # trace: 任务书 §3（语言无关规则表：Python 族同规则；实现指引注释不参与代码规则判定）
    def test_audit_precode_python_family_and_comment_exemption(self):
        spec = self.spec("tests/test_boundary.py", PY_PRECODE_OK)
        r = self.audit([spec])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(json.loads(r.stdout)["violations"], [],
                         "注释里提到的 page.wait_for_timeout 不算代码规则违例")

    # trace: 任务书 §3（主命令合法路径 exit 0 + 回执键完整）
    def test_audit_precode_clean_scaffold_passes(self):
        spec = self.spec("tests/boundary.spec.ts", JS_PRECODE_OK)
        r = self.audit([spec])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertTrue(data["ok"])
        self.assertEqual(data["violations"], [])
        self.assertEqual(data["command"], "audit")
        for key in ("ok", "command", "project_root", "output_dir",
                    "violations", "warnings", "counts"):
            self.assertIn(key, data, "回执缺共同键 %s" % key)
        self.assertEqual(data["counts"]["tests"], 1)
        self.assertEqual(data["counts"]["tcs"], 1)


class AuditRuleSetTests(EngineCase):
    """规则集面：与产出模式无关，同一条禁则在任何合法脚手架上都要检出。"""

    # trace: 任务书 §3（规则集：脆选择器禁则——CSS / XPath 一律换语义定位）
    def test_audit_flags_brittle_selector(self):
        spec = self.spec("tests/login.spec.ts", NL.join([
            "// TC: TC-1.1.1",
            "test('登录后跳转', async () => {",
            "  test.skip();",
            "  await page.locator('#submit').click();",
            "  expect(await page.title()).toBe('Done');",
            "});",
        ]) + NL)
        r = self.audit([spec])
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("BRITTLE_SELECTOR", {x["code"] for x in json.loads(r.stdout)["violations"]})

    # trace: 任务书 §3（规则集：硬等待禁则）
    def test_audit_flags_hard_wait(self):
        spec = self.spec("tests/login.spec.ts", NL.join([
            "// TC: TC-1.1.1",
            "test('等待状态就绪', async () => {",
            "  test.skip();",
            "  await page.waitForTimeout(500);",
            "  expect(await page.getByRole('status').textContent()).toBe('ready');",
            "});",
        ]) + NL)
        r = self.audit([spec])
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("HARD_WAIT", {x["code"] for x in json.loads(r.stdout)["violations"]})

    # trace: 任务书 §3（规则集：硬编码业务数据判在 test 体内；工厂文件是字面量的合法归宿）
    def test_audit_flags_hardcoded_data_in_test_but_not_factory_file(self):
        spec = self.spec("tests/login.spec.ts", NL.join([
            "// TC: TC-1.1.1",
            "test('登录成功', async () => {",
            "  test.skip();",
            "  await page.getByLabel('邮箱').fill('user@example.com');",
            "  expect(await page.title()).toBe('Done');",
            "});",
        ]) + NL)
        r = self.audit([spec])
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("HARDCODED_DATA", {x["code"] for x in json.loads(r.stdout)["violations"]})
        factory = self.spec("tests/support/factories/user.ts",
                            "export const makeUser = () => ({ email: 'user@example.com' });" + NL)
        r2 = self.audit([factory])
        self.assertEqual(r2.returncode, 0, r2.stdout + r2.stderr)

    # trace: 任务书 §3（规则集：占位断言 / 非空断言 / 单断言原子）
    def test_audit_flags_assertion_quality_rules(self):
        placeholder = self.spec("tests/placeholder.spec.ts", NL.join([
            "// TC: TC-1.1.1",
            "test('假断言', async () => {",
            "  test.skip();",
            "  expect(true).toBe(true);",
            "});",
        ]) + NL)
        r = self.audit([placeholder])
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("PLACEHOLDER_ASSERTION",
                      {x["code"] for x in json.loads(r.stdout)["violations"]})
        empty = self.spec("tests/empty.spec.ts", NL.join([
            "// TC: TC-1.1.1",
            "test('没有断言', async () => {",
            "  test.skip();",
            "  await doSomething();",
            "});",
        ]) + NL)
        r2 = self.audit([empty])
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertIn("MISSING_ASSERTION", {x["code"] for x in json.loads(r2.stdout)["violations"]})
        multi = self.spec("tests/multi.spec.ts", NL.join([
            "// TC: TC-1.1.1",
            "test('多断言', async () => {",
            "  test.skip();",
            "  expect(compute(1)).toBe(2);",
            "  expect(compute(2)).toBe(4);",
            "});",
        ]) + NL)
        r3 = self.audit([multi])
        self.assertEqual(r3.returncode, 1, r3.stdout)
        self.assertIn("NOT_ATOMIC", {x["code"] for x in json.loads(r3.stdout)["violations"]})


class UsageTests(EngineCase):

    # trace: 任务书 §3（--files 必填且空集拒绝；文件缺席；--output-dir 必填）
    def test_files_mandatory_and_missing_file_refused(self):
        spec = self.spec("tests/boundary.spec.ts", JS_PRECODE_OK)
        r = run_engine(["audit", "--project-root", self.root,
                        "--output-dir", self.out, "--json"])
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)  # 缺 --files → 用法错误
        r2 = self.audit([os.path.join(self.root, "tests", "absent.spec.ts")])
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertIn("MISSING_FILE", {x["code"] for x in json.loads(r2.stdout)["violations"]})
        r3 = run_engine(["audit", "--files", spec,
                         "--project-root", self.root, "--json"])
        self.assertEqual(r3.returncode, 2, r3.stdout + r3.stderr)  # --output-dir 必填
        # 人类可读面：每违规一行 CODE where: msg
        r4 = self.audit([os.path.join("tests", "absent.spec.ts")])
        self.assertEqual(r4.returncode, 1, r4.stdout)
        self.assertIn("MISSING_FILE", r4.stdout)


class CapabilityTests(EngineCase):
    """用例 14–20：V 能力清点 §1.1 六条丢失项（A-1..A-6）的落地面。"""

    def js(self, body, name="[P0] 边界值被拦截"):
        """一条合法红相脚手架（锚 / 标签 / GWT 齐备），供单点注入缺陷。"""
        return NL.join([
            "// TC: TC-1.1.1",
            "test('%s', async () => {" % name,
            "  test.skip();",
            "  // Given 一个未实现的边界输入",
            "  // When 调用 compute(1)",
            "  // Then 期望返回 2",
        ] + list(body) + ["});"]) + NL

    # trace: V 清点 A-1（源 atdd/steps-c/step-04a:146、04b:194、automate/checklist.md:176）
    def test_audit_flags_priority_tag_missing_or_mismatched(self):
        no_tag = self.spec("tests/a.spec.ts",
                           self.js(["  expect(compute(1)).toBe(2);"], name="边界值被拦截"))
        r = self.audit([no_tag])
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("PRIORITY_TAG_MISSING", codes(r))

        wrong = self.spec("tests/b.spec.ts",
                          self.js(["  expect(compute(1)).toBe(2);"], name="[P2] 边界值被拦截"))
        r2 = self.audit([wrong])
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertIn("PRIORITY_TAG_MISMATCH", codes(r2),
                      "夹具 TC 的 priority=P0——标签 [P2] 必须被检出")

        # py 侧标签落文档字符串（def 名不能带方括号）：合法载体 → 放行
        py = self.spec("tests/test_tag.py", NL.join([
            "# TC: TC-1.1.1",
            "def test_boundary():",
            "    \"\"\"[P0] 边界值被拦截\"\"\"",
            "    pytest.skip('待实现')",
            "    # Given 一个未实现的边界输入",
            "    # When 调用 compute(1)",
            "    # Then 期望返回 2",
            "    assert compute(1) == 2",
        ]) + NL)
        r3 = self.audit([py])
        self.assertEqual(r3.returncode, 0, r3.stdout + r3.stderr)

    # trace: V 清点 A-2（源 automate/checklist.md:246 无顺序依赖、:254 无共享状态）
    def test_audit_flags_order_dependency_and_shared_state(self):
        serial = self.spec("tests/serial.spec.ts", NL.join([
            "// TC: TC-1.1.1",
            "test.describe.configure({ mode: 'serial' });",
            "test('[P0] 边界值被拦截', async () => {",
            "  test.skip();",
            "  // Given 一个未实现的边界输入",
            "  // When 调用 compute(1)",
            "  // Then 期望返回 2",
            "  expect(compute(1)).toBe(2);",
            "});",
        ]) + NL)
        r = self.audit([serial])
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ORDER_DEPENDENCY", codes(r))

        shared = self.spec("tests/shared.spec.ts",
                           "let sharedUser = null;" + NL + self.js(["  expect(compute(1)).toBe(2);"]))
        r2 = self.audit([shared])
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertIn("SHARED_STATE", codes(r2))

        py_shared = self.spec("tests/test_shared.py", NL.join([
            "# TC: TC-1.1.1",
            "def test_boundary():",
            "    \"\"\"[P0] 边界值被拦截\"\"\"",
            "    global CACHE",
            "    pytest.skip('待实现')",
            "    # Given 一个未实现的边界输入",
            "    # When 调用 compute(1)",
            "    # Then 期望返回 2",
            "    assert compute(1) == 2",
        ]) + NL)
        r3 = self.audit([py_shared])
        self.assertEqual(r3.returncode, 1, r3.stdout)
        self.assertIn("SHARED_STATE", codes(r3))

    # trace: V 清点 A-2（源 automate/checklist.md:245,247 无 flaky / 同输入同结果）
    def test_audit_flags_nondeterministic_source_but_exempts_factory(self):
        spec = self.spec("tests/clock.spec.ts",
                         self.js(["  const at = Date.now();",
                                  "  expect(compute(at)).toBe(2);"]))
        r = self.audit([spec])
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("NONDETERMINISTIC_SOURCE", codes(r))

        # 工厂造数据用随机源是本职（判在 test 体内）：不在用例体内 → 不判
        factory = self.spec("tests/support/factories/user.ts",
                            "export const makeUser = () => ({ at: Date.now() });" + NL)
        r2 = self.audit([factory])
        self.assertEqual(r2.returncode, 0, r2.stdout + r2.stderr)

    # trace: V 清点 A-3（源 atdd/checklist.md:66,77,97、automate/checklist.md:242-243）
    def test_audit_flags_missing_gwt_and_undescriptive_name(self):
        no_gwt = self.spec("tests/nogwt.spec.ts", NL.join([
            "// TC: TC-1.1.1",
            "test('[P0] 边界值被拦截', async () => {",
            "  test.skip();",
            "  expect(compute(1)).toBe(2);",
            "});",
        ]) + NL)
        r = self.audit([no_gwt])
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("GWT_MISSING", codes(r))

        vague = self.spec("tests/vague.spec.ts",
                          self.js(["  expect(compute(1)).toBe(2);"], name="[P0] test1"))
        r2 = self.audit([vague])
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertIn("NAME_UNDESCRIPTIVE", codes(r2))

        # py 的标签落 def 上方注释、GWT 中文紧贴（`# Given一个…`）：两种写法都放行
        py = self.spec("tests/test_gwt.py", NL.join([
            "# TC: TC-1.1.1",
            "# [P0] 边界值被拦截",
            "def test_boundary():",
            "    pytest.skip('待实现')",
            "    # Given一个未实现的边界输入",
            "    # When调用 compute(1)",
            "    # Then期望返回 2",
            "    assert compute(1) == 2",
        ]) + NL)
        r3 = self.audit([py])
        self.assertEqual(r3.returncode, 0, r3.stdout + r3.stderr)

    # trace: V 清点 A-4（源 atdd/checklist.md:122,321,367-375、automate/checklist.md:131）
    def test_audit_flags_fixture_without_teardown_but_exempts_pure_factory(self):
        head = NL.join([
            "export const test = base.extend({",
            "  user: async ({ db }, use) => {",
            "    const user = await createUser(db);",
            "    await use(user);",
        ]) + NL
        spec = self.spec("tests/support/fixtures/user.ts",
                         head + "  }," + NL + "});" + NL)
        r = self.audit([spec])
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("FIXTURE_NO_TEARDOWN", codes(r))

        cleaned = self.spec("tests/support/fixtures/clean.ts",
                            head + "    await deleteUser(user.id);" + NL + "  }," + NL + "});" + NL)
        r2 = self.audit([cleaned])
        self.assertEqual(r2.returncode, 0, r2.stdout + r2.stderr)

    # trace: V 清点 A-5（源 automate/checklist.md:251 禁 try-catch 用于测试逻辑）
    def test_audit_flags_try_catch_for_test_logic_but_allows_cleanup(self):
        logic = self.spec("tests/try.spec.ts", NL.join([
            "// TC: TC-1.1.1",
            "test('[P0] 边界值被拦截', async () => {",
            "  test.skip();",
            "  // Given 一个未实现的边界输入",
            "  // When 调用 compute(1)",
            "  // Then 期望返回 2",
            "  try {",
            "    expect(compute(1)).toBe(2);",
            "  } catch (e) {",
            "    // 吞掉失败",
            "  }",
            "});",
        ]) + NL)
        r = self.audit([logic])
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("TRY_CATCH_TEST_LOGIC", codes(r))

        cleanup = self.spec("tests/tryclean.spec.ts", NL.join([
            "// TC: TC-1.1.1",
            "test('[P0] 边界值被拦截', async () => {",
            "  test.skip();",
            "  // Given 一个未实现的边界输入",
            "  // When 调用 compute(1)",
            "  // Then 期望返回 2",
            "  try {",
            "    await cleanupUser(1);",
            "  } catch (e) {",
            "    // 清理失败不掩盖断言",
            "  }",
            "  expect(compute(1)).toBe(2);",
            "});",
        ]) + NL)
        r2 = self.audit([cleanup])
        self.assertEqual(r2.returncode, 0, r2.stdout + r2.stderr)

    # trace: V 清点 A-6（源 automate/checklist.md:457 禁 console.log / 调试语句）
    def test_audit_flags_debug_statement_but_exempts_comment(self):
        spec = self.spec("tests/debug.spec.ts",
                         self.js(["  console.log(compute(1));",
                                  "  expect(compute(1)).toBe(2);"]))
        r = self.audit([spec])
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("DEBUG_STATEMENT", codes(r))

        commented = self.spec("tests/debug_comment.spec.ts",
                              self.js(["  // console.log(compute(1));",
                                       "  expect(compute(1)).toBe(2);"]))
        r2 = self.audit([commented])
        self.assertEqual(r2.returncode, 0, r2.stdout + r2.stderr)

        py = self.spec("tests/test_debug.py", NL.join([
            "# TC: TC-1.1.1",
            "def test_boundary():",
            "    \"\"\"[P0] 边界值被拦截\"\"\"",
            "    pytest.skip('待实现')",
            "    # Given 一个未实现的边界输入",
            "    # When 调用 compute(1)",
            "    # Then 期望返回 2",
            "    print(compute(1))",
            "    assert compute(1) == 2",
        ]) + NL)
        r3 = self.audit([py])
        self.assertEqual(r3.returncode, 1, r3.stdout)
        self.assertIn("DEBUG_STATEMENT", codes(r3))


class EngineRegistryTests(unittest.TestCase):
    """用例 21：违规码登记面——新增码必须在引擎模块 docstring 的登记表里（硬约束 6）。"""

    NEW_CODES = ("PRIORITY_TAG_MISSING", "PRIORITY_TAG_MISMATCH", "NAME_UNDESCRIPTIVE",
                 "GWT_MISSING", "ORDER_DEPENDENCY", "SHARED_STATE",
                 "NONDETERMINISTIC_SOURCE", "TRY_CATCH_TEST_LOGIC",
                 "DEBUG_STATEMENT", "FIXTURE_NO_TEARDOWN")

    # trace: 任务书 §2.2（引擎契约：违规码表是登记面）+ 本轮返工硬约束 6
    def test_engine_docstring_registers_new_codes(self):
        with io.open(ENGINE, encoding="utf-8") as f:
            doc = f.read().split('"""')[1]
        for code in self.NEW_CODES:
            self.assertIn(code, doc, "引擎 docstring 违规码表缺 %s" % code)


class SkillContractTests(unittest.TestCase):
    """用例 13：SKILL.md 契约冒烟（母本定稿逐字 + 四段结构 + 终门指向本引擎）。"""

    def read_skill(self):
        with io.open(SKILL_MD, encoding="utf-8") as f:
            return f.read()

    # trace: 任务书 §2.1 / 母本 §1（实例解析句中文定稿逐字）
    def test_instance_resolution_sentence_verbatim(self):
        self.assertIn(INSTANCE_ZH, self.read_skill(), "SKILL.md 缺母本 §1 中文定稿（逐字）")

    # trace: 任务书 §2.1 / 母本 §3（配置键全路径带 project. 前缀）
    def test_resolve_keys_anchor(self):
        self.assertIn(RESOLVE_KEYS_ZH, self.read_skill(), "SKILL.md 缺母本 §3 键路径锚串")

    # trace: 任务书 §2.1 / 母本 §4（读取纪律逐字）
    def test_read_discipline_verbatim(self):
        self.assertIn(READ_DISCIPLINE_ZH, self.read_skill(), "SKILL.md 缺母本 §4 定稿（逐字）")

    # trace: 任务书 §2.1 / 母本 §2（写作纪律块逐字，置 Rules 段末尾）
    def test_writing_discipline_block_at_rules_end(self):
        raw = self.read_skill()
        self.assertIn(DISCIPLINE_ZH, raw, "SKILL.md 缺母本 §2 中文定稿")
        self.assertEqual(DISCIPLINE_ZH, raw.rstrip(NL).splitlines()[-1],
                         "写作纪律块须置 Rules 段末尾")

    # trace: 验收 #1（薄主文件四段 + 标题含技能名 + ≤93 行；
    #         2026-09-19 中文化：母本 §6 条款与 description 注释为强制内容，净增 3 行）
    def test_thin_main_file_structure(self):
        raw = self.read_skill()
        for section in ("## 激活时", "## 工作流", "## 结构", "## 规则"):
            self.assertIn(section, raw, "缺段 %s" % section)
        self.assertIn("diy-test-author", raw.splitlines()[0] + raw[:400], "标题未含技能名")
        self.assertLessEqual(len(raw.splitlines()), 93, "薄主文件超出 93 行预算")
        for name in ("01-preflight.md", "02-scope.md", "03-generate.md",
                     "04-audit.md", "05-confirm.md", "06-finish.md"):
            self.assertIn(name, raw, "Workflow 未点名 %s" % name)

    # trace: 验收 #12b（终门句指向本技能领域引擎的 audit 子命令）
    def test_final_gate_points_to_engine_audit(self):
        raw = self.read_skill()
        self.assertIn("diy-test-author/scripts/author.py", raw, "终门句未指向领域引擎")
        self.assertIn("audit --files", raw, "终门句缺 audit --files 形态")
        self.assertIn("--json", raw, "终门句缺 --json 回执")
        self.assertIn("--json", raw, "终门句缺 --json 回执")

    # trace: 任务书 §2.1（W1 无 YAML 产物 → 无渲染步骤，须在 Rules 写明理由）
    def test_no_render_step_with_reason(self):
        raw = self.read_skill()
        self.assertNotIn("diy-viewer/scripts/viewer.py", raw,
                         "W1 无 YAML 产物——不得出现渲染调用（须在 Rules 写明理由）")
        self.assertIn("无渲染", raw, "Rules 未写明无渲染步骤的理由")


if __name__ == "__main__":
    unittest.main()
