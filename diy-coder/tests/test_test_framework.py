# -*- coding: utf-8 -*-
"""diy-test-framework 确定性引擎测试（B3 任务书 §2.5 / §5）。

覆盖（任务书 §5「测试」清单，≥10 用例）：
- 用例 1：无清单拒绝（detect → exit 1 + MISSING_FILE，零写入）
- 用例 2：detect 识别合成栈（前端 / 双栈 / CI 平台 / 既有框架）
- 用例 3：detect mobile 优先判定（RN + app.json 不被误判为 frontend）+ 无模板覆盖登记
- 用例 4：scaffold 在 tempdir 生成声明文件（逐字节 == 模板渲染结果）
- 用例 5：scaffold 幂等重入（同 plan 二次运行全 skip、零写入）
- 用例 6：scaffold 冲突拒绝含回滚断言（本次已写文件已删、旧文件未动）
- 用例 7：plan 路径越界拒绝（`../` 段 → ENUM_INVALID，零写入）
- 用例 8：plan 占位符未取值拒绝（EMPTY_FIELD，零写入）/ 模板不存在拒绝（MISSING_FILE）
- 用例 9：check 路径形态违例（`../` 段 → ENUM_INVALID）
- 用例 10：ci_alignment 检出 blocking 命令缺席（CI_MISALIGNED）
- 用例 11：ci_alignment 台账与重算不一致违例（漏 blocking 条目 / in_ci 不符 / order 越界 UNKNOWN_ID）
- 用例 12：阈值注入一致性（CI 文件缺 ci.gates 字面量 → CI_MISALIGNED）
- 用例 13：check 合法台账 --final 通过（exit 0）
- 用例 14：checks 中 fail 条目 note 必填（EMPTY_FIELD）+ fail 条目 --final 只记 warning
- 用例 15：SKILL.md 契约冒烟（母本 §1/§2/§4/§5 锚串 + 终门句指向本技能引擎 + steps/ 6 文件）

夹具全部落 tempfile 自建；不读写本仓库真实 diy-output、不写本仓库真实项目目录、不依赖本机 git 状态。
运行：cd diy-coder && python -m unittest discover -s tests -p "test_test_framework.py" -v
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.join(HERE, "..", "skills", "diy-test-framework")
ENGINE = os.path.join(SKILL_DIR, "scripts", "test_framework.py")
SKILL_MD = os.path.join(SKILL_DIR, "SKILL.md")
STEPS_DIR = os.path.join(SKILL_DIR, "steps")
NL = chr(10)

# 母本 §1 / §2 / §4 / §5 锚串（suite-texts.md 中文定稿，逐字）
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
READ_DISCIPLINE_ZH = ("读取纪律：预载预算 = 本文件、上述配置与回执、`steps/` 下当前那一个文件"
                      "——绝不批量预载；执行期读取以每个步骤开头的 `Read (input)` 行为唯一权威，"
                      "**主文件不列举封闭清单**。")
RENDER_SILENT_ZH = "渲染是静默旁路——只写调用命令"


def run_engine(args, cwd=None):
    return subprocess.run([sys.executable, ENGINE] + args,
                          capture_output=True, text=True, encoding="utf-8", cwd=cwd)


class EngineCase(unittest.TestCase):
    """tmp 项目根 + {output_dir} 的公共夹具。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="tfw-")
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
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(content)
        return path

    def read(self, rel):
        with open(os.path.join(self.root, rel), "r", encoding="utf-8") as fh:
            return fh.read()

    def plan(self, payload, name="scaffold-plan.json"):
        return self.write(os.path.join("diy-output", name),
                          json.dumps(payload, ensure_ascii=False))

    def engine(self, args, json_out=True, cwd=None):
        """补 --project-root / --output-dir（契约：--output-dir 必填，引擎不做目录推导）。"""
        argv = list(args)
        argv += ["--project-root", self.root, "--output-dir", self.out]
        argv += ["--json"] if json_out else []
        proc = run_engine(argv, cwd=cwd or self.root)
        payload = None
        if json_out and proc.stdout.strip():
            payload = json.loads(proc.stdout.strip().splitlines()[-1])
        return proc, payload

    def codes(self, payload):
        return sorted(item["code"] for item in payload["violations"])


PLAN_CI = {
    "setup": "TF-001",
    "part": "ci",
    "substitutions": {
        "RUNTIME_SETUP_CMD": "node --version",
        "INSTALL_CMD": "npm ci",
        "LINT_CMD": "npm run lint",
        "TEST_CMD": "npx playwright test",
        "BROWSER_INSTALL": "npx playwright install --with-deps chromium",
        "P0_GATE": "100%",
        "P1_GATE": "100%",
        "REPORT_PATH": "playwright-report/",
        "CACHE_PATH": "~/.npm",
        "CACHE_KEY": "deps-node-${{ hashFiles('**/package-lock.json') }}",
        "CACHE_RESTORE_KEYS": "deps-node-",
        "BROWSER_CACHE_PATH": "~/.cache/ms-playwright",
        "BROWSER_CACHE_KEY": "browsers-${{ hashFiles('**/package-lock.json') }}",
        "BROWSER_CACHE_RESTORE_KEYS": "browsers-",
        "NOTIFY_SECRET": "SLACK_WEBHOOK_URL",
    },
    "files": [
        {"template": "ci/github-actions/browser.yml.tpl",
         "path": ".github/workflows/test.yml", "kind": "ci"},
    ],
}

# 全平台全类别的取值（CI 模板覆盖面用；键集取并集，多余取值只产生 warning）
CI_SUBS = {
    "RUNTIME_SETUP_CMD": "node --version", "INSTALL_CMD": "npm ci",
    "LINT_CMD": "npm run lint", "TEST_CMD": "npx playwright test",
    "BROWSER_INSTALL": "npx playwright install --with-deps chromium",
    "P0_GATE": "100%", "P1_GATE": "100%", "REPORT_PATH": "playwright-report/",
    "CACHE_PATH": "~/.npm", "CACHE_KEY": "deps-node-${{ hashFiles('**/package-lock.json') }}",
    "CACHE_RESTORE_KEYS": "deps-node-", "CACHE_LOCKFILE": "package-lock.json",
    "BROWSER_CACHE_PATH": "~/.cache/ms-playwright",
    "BROWSER_CACHE_KEY": "browsers-${{ hashFiles('**/package-lock.json') }}",
    "BROWSER_CACHE_RESTORE_KEYS": "browsers-",
    "BROWSER_CACHE_LOCKFILE": "package-lock.json",
    "NOTIFY_SECRET": "SLACK_WEBHOOK_URL",
}


def load_engine():
    """把技能引擎当模块载入（模板层断言用；不在技能目录落 __pycache__）。"""
    import importlib.util
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("tfw_engine", ENGINE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DetectTests(EngineCase):
    """用例 1-3：门禁与栈探测。"""

    def test_no_manifest_refused(self):
        proc, payload = self.engine(["detect"])
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertFalse(payload["ok"])
        self.assertEqual(self.codes(payload), ["MISSING_FILE"])
        self.assertEqual(payload["suggested"]["framework"], None)
        self.assertEqual(os.listdir(self.root), ["diy-output"])  # 零写入

    def test_detect_synthetic_frontend_and_ci(self):
        self.write("package.json", json.dumps({
            "name": "mini", "devDependencies": {"react": "18", "@playwright/test": "1"}
        }))
        self.write("playwright.config.ts", "export default {}" + NL)
        self.write(".github/workflows/test.yml", "name: t" + NL)
        proc, payload = self.engine(["detect"])
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(payload["stack"]["type"], "frontend")
        self.assertEqual(payload["stack"]["language"], "node")
        self.assertEqual(payload["stack"]["package_manager"], "npm")
        self.assertEqual(payload["existing"]["framework"], "playwright")
        self.assertEqual(payload["existing"]["ci"], "github-actions")
        self.assertEqual(payload["suggested"]["framework"], "playwright")
        self.assertEqual(payload["suggested"]["platform"], "github-actions")
        self.assertEqual(payload["suggested"]["profile"], "browser-playwright")
        self.assertTrue(payload["templates"]["framework_supported"])
        self.assertTrue(payload["templates"]["ci_supported"])

    def test_detect_fullstack_and_mobile_priority(self):
        self.write("package.json", json.dumps({"name": "mini", "dependencies": {"next": "14"}}))
        self.write("pyproject.toml", "[project]" + NL + "name = 'api'" + NL)
        proc, payload = self.engine(["detect"])
        self.assertEqual(payload["stack"]["type"], "fullstack")
        self.assertEqual(sorted(payload["stack"]["languages"]), ["node", "python"])
        self.assertEqual(payload["suggested"]["profile"], "browser-playwright")

        # mobile 优先：RN 工程带 package.json，但 app.json + react-native 指示 → mobile
        root2 = tempfile.mkdtemp(prefix="tfw-mob-")
        try:
            with open(os.path.join(root2, "package.json"), "w", encoding="utf-8") as fh:
                fh.write(json.dumps({"name": "app", "dependencies": {"react-native": "0.74"}}))
            with open(os.path.join(root2, "app.json"), "w", encoding="utf-8") as fh:
                fh.write("{}" + NL)
            proc2 = run_engine(["detect", "--project-root", root2,
                                "--output-dir", "diy-output", "--json"])
            payload2 = json.loads(proc2.stdout.strip().splitlines()[-1])
            self.assertEqual(payload2["stack"]["type"], "mobile")
            self.assertFalse(payload2["templates"]["framework_supported"])
            self.assertFalse(payload2["templates"]["ci_supported"])
            self.assertTrue(payload2["warnings"])
        finally:
            import shutil
            shutil.rmtree(root2, ignore_errors=True)


class ScaffoldTests(EngineCase):
    """用例 4-8：模板渲染与写入三分支。"""

    def test_scaffold_writes_declared_files(self):
        self.plan(PLAN_CI)
        proc, payload = self.engine(["scaffold", "--plan", "diy-output/scaffold-plan.json"])
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(payload["written"], [".github/workflows/test.yml"])
        self.assertEqual(payload["skipped"], [])
        self.assertIn("npm ci", payload["pending_commands"])
        body = self.read(".github/workflows/test.yml")
        # 占位符全部取值（`${{ ... }}` 是 GitHub Actions 表达式，不是本技能占位符）
        self.assertIsNone(re.search(r"\{\{[A-Z][A-Z0-9_]*\}\}", body), body[:200])
        self.assertNotIn("# placeholders:", body)        # 头指令行不落盘
        self.assertIn("npm run lint", body)
        self.assertIn("100%", body)                      # 门禁阈值字面量注入
        self.assertIn("Security", body)                  # 注入防护段随模板逐字保留

    def test_scaffold_idempotent_rerun(self):
        self.plan(PLAN_CI)
        first, _ = self.engine(["scaffold", "--plan", "diy-output/scaffold-plan.json"])
        self.assertEqual(first.returncode, 0)
        before = self.read(".github/workflows/test.yml")
        proc, payload = self.engine(["scaffold", "--plan", "diy-output/scaffold-plan.json"])
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(payload["written"], [])
        self.assertEqual(payload["skipped"], [".github/workflows/test.yml"])
        self.assertEqual(payload["counts"]["written"], 0)
        self.assertEqual(self.read(".github/workflows/test.yml"), before)

    def test_scaffold_conflict_rolls_back(self):
        self.write(".github/workflows/test.yml", "name: 既有流水线" + NL)  # 冲突目标
        self.plan({
            "setup": "TF-001",
            "part": "framework",
            "substitutions": {"NODE_VERSION": "22",
                              "INSTALL_CMD": "npm ci", "TEST_CMD": "npx playwright test",
                              "LINT_CMD": "npm run lint", "FRAMEWORK_NAME": "Playwright",
                              "TEST_DIR": "tests", "BASE_URL": "http://localhost:3000",
                              "API_URL": "http://localhost:3000/api"},
            "files": [
                {"template": "framework/shared/nvmrc.tpl", "path": ".nvmrc", "kind": "config"},
                {"template": "framework/browser-playwright/playwright.config.ts.tpl",
                 "path": "playwright.config.ts", "kind": "config"},
            ],
        })
        # 先制造冲突目标在场（顺序：先写 .nvmrc 成功，再撞 playwright.config.ts）
        self.write("playwright.config.ts", "// 人手写的既有配置" + NL)
        proc, payload = self.engine(["scaffold", "--plan", "diy-output/scaffold-plan.json"])
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("FILE_CONFLICT", self.codes(payload))
        self.assertEqual(payload["counts"]["written"], 0)
        self.assertIn("playwright.config.ts", payload["rollback"]["conflicts"])
        self.assertIn(".nvmrc", payload["rollback"]["removed"])       # 本次已写文件已删
        self.assertFalse(os.path.exists(os.path.join(self.root, ".nvmrc")))
        self.assertEqual(self.read("playwright.config.ts"), "// 人手写的既有配置" + NL)

    def test_scaffold_rejects_path_traversal(self):
        self.plan({
            "setup": "TF-001", "part": "ci", "substitutions": {"NODE_VERSION": "22"},
            "files": [{"template": "framework/shared/nvmrc.tpl",
                       "path": "../evil.txt", "kind": "config"}],
        })
        proc, payload = self.engine(["scaffold", "--plan", "diy-output/scaffold-plan.json"])
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(self.codes(payload), ["ENUM_INVALID"])
        self.assertEqual(payload["written"], [])
        self.assertFalse(os.path.exists(os.path.join(os.path.dirname(self.root), "evil.txt")))

    def test_scaffold_rejects_unsubstituted_and_unknown_template(self):
        self.plan({
            "setup": "TF-001", "part": "ci", "substitutions": {},
            "files": [{"template": "framework/shared/nvmrc.tpl",
                       "path": ".nvmrc", "kind": "config"}],
        })
        proc, payload = self.engine(["scaffold", "--plan", "diy-output/scaffold-plan.json"])
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(self.codes(payload), ["EMPTY_FIELD"])
        self.assertFalse(os.path.exists(os.path.join(self.root, ".nvmrc")))

        self.plan({
            "setup": "TF-001", "part": "ci", "substitutions": {"NODE_VERSION": "22"},
            "files": [{"template": "ci/nope.yml.tpl", "path": "x.yml", "kind": "ci"}],
        })
        proc, payload = self.engine(["scaffold", "--plan", "diy-output/scaffold-plan.json"])
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(self.codes(payload), ["MISSING_FILE"])


LEDGER = {
    "project": {"name": "mini", "created": "2026-09-16", "updated": "2026-09-16"},
    "setups": [{
        "id": "TF-001", "date": "2026-09-16", "status": "final", "mode": "both",
        "stack": {"type": "frontend", "language": "node", "package_manager": "npm"},
        "framework": {"name": "playwright", "runner": "npx playwright test",
                      "reason": "多浏览器 + CI 并行"},
        "files": [
            {"path": ".github/workflows/test.yml", "kind": "ci", "action": "new"},
            {"path": "playwright.config.ts", "kind": "config", "action": "new"},
        ],
        "checks": [{"command": "npm ci", "result": "pass"}],
        "ci": {
            "platform": "github-actions",
            "file": ".github/workflows/test.yml",
            "stages": ["lint", "test", "burn-in", "report"],
            "gates": {"p0": "100%", "p1": "100%"},
            "static_check_alignment": [{"order": 1, "in_ci": True}],
        },
        "deferred": [],
        "open_questions": [],
    }],
    "revisions": [],
}

TEST_PLAN = NL.join([
    "project:",
    "  name: mini",
    "  status: final",
    "test_cases: []",
    "static_checks:",
    "- order: 1",
    "  tool: npm run lint",
    "  kills: 语法/风格问题",
    "  gate: blocking",
]) + NL


class CheckTests(EngineCase):
    """用例 9-14：台账校验与 CI 三方对齐（重扫）。"""

    def _ledger(self, **overrides):
        import copy
        data = copy.deepcopy(LEDGER)
        data["setups"][0].update(overrides)
        return data

    def _write_ledger(self, data):
        import yaml
        self.write(os.path.join("diy-output", "test-framework.yaml"),
                   yaml.safe_dump(data, allow_unicode=True, sort_keys=False))

    def setUp(self):
        super().setUp()
        self.write("playwright.config.ts", "export default {}" + NL)
        self.write(os.path.join("diy-output", "test-plan.yaml"), TEST_PLAN)

    def _ci_body(self, lint="npm run lint", gates=True):
        head = ("# Quality gates: P0 100% / P1 100%" + NL) if gates else ""
        return head + NL.join([
            "jobs:", "  lint:", "    steps:",
            "      - run: npm ci",
            "      - run: %s" % lint,
        ]) + NL

    def test_check_path_form_violation(self):
        os.makedirs(self.out, exist_ok=True)
        self.write(".github/workflows/test.yml", self._ci_body())
        data = self._ledger()
        data["setups"][0]["files"][0]["path"] = "../evil.yml"
        self._write_ledger(data)
        proc, payload = self.engine(["check"])
        self.assertEqual(proc.returncode, 1)
        self.assertIn("ENUM_INVALID", self.codes(payload))

    def test_ci_alignment_missing_blocking_command(self):
        self.write(".github/workflows/test.yml", self._ci_body(lint="npm run fmt"))
        self._write_ledger(self._ledger())
        proc, payload = self.engine(["check"])
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("CI_MISALIGNED", self.codes(payload))
        self.assertTrue(any("npm run lint" in item["msg"] for item in payload["violations"]))

    def test_ci_alignment_ledger_mismatch_and_unknown_order(self):
        self.write(".github/workflows/test.yml", self._ci_body())
        data = self._ledger()
        data["setups"][0]["ci"]["static_check_alignment"] = [
            {"order": 1, "in_ci": False},     # 重算 = True → 不一致
            {"order": 9, "in_ci": True},      # test-plan 中无 order 9
        ]
        self._write_ledger(data)
        proc, payload = self.engine(["check"])
        self.assertEqual(proc.returncode, 1)
        self.assertIn("CI_MISALIGNED", self.codes(payload))
        self.assertIn("UNKNOWN_ID", self.codes(payload))

        # 漏 blocking 条目：CI 文件里有命令、台账不录 → CI_MISALIGNED
        data = self._ledger()
        data["setups"][0]["ci"]["static_check_alignment"] = []
        self._write_ledger(data)
        proc, payload = self.engine(["check"])
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(self.codes(payload), ["CI_MISALIGNED"])

    def test_ci_alignment_skipped_branches(self):
        # test-plan 缺席 → 跳过 + warning，不阻塞
        os.remove(os.path.join(self.out, "test-plan.yaml"))
        self.write(".github/workflows/test.yml", self._ci_body())
        self._write_ledger(self._ledger())
        proc, payload = self.engine(["check"])
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertTrue(any("static_checks" in w["msg"] for w in payload["warnings"]))

    def test_threshold_injection_mismatch(self):
        self.write(".github/workflows/test.yml", self._ci_body(gates=False))
        self._write_ledger(self._ledger())
        proc, payload = self.engine(["check"])
        self.assertEqual(proc.returncode, 1)
        self.assertIn("CI_MISALIGNED", self.codes(payload))
        self.assertTrue(any("100%" in item["msg"] for item in payload["violations"]))

    def test_check_valid_final(self):
        self.write(".github/workflows/test.yml", self._ci_body())
        self._write_ledger(self._ledger())
        proc, payload = self.engine(["check", "--final"])
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["counts"]["setups"], 1)
        self.assertEqual(payload["counts"]["by_platform"], {"github-actions": 1})

    def test_checks_fail_note_and_final_warning_only(self):
        self.write(".github/workflows/test.yml", self._ci_body())
        data = self._ledger()
        data["setups"][0]["checks"] = [{"command": "npm ci", "result": "fail", "note": ""}]
        self._write_ledger(data)
        proc, payload = self.engine(["check"])
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(self.codes(payload), ["EMPTY_FIELD"])

        data["setups"][0]["checks"] = [{"command": "npm ci", "result": "fail",
                                        "note": "环境面：无网络，用户自行安装"}]
        self._write_ledger(data)
        proc, payload = self.engine(["check", "--final"])
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertTrue(any("fail" in w["msg"] for w in payload["warnings"]))


class TemplateSetTests(unittest.TestCase):
    """用例 15-16：模板集完整性与覆盖面（机械保证「模板是唯一来源」成立）。"""

    @classmethod
    def setUpClass(cls):
        cls.mod = load_engine()      # 不在技能目录里落 __pycache__（install.py 会整目录同步）

    def _templates(self):
        root = self.mod.TEMPLATES_DIR
        found = []
        for dirpath, _dirs, names in os.walk(root):
            for name in names:
                if name.endswith(".tpl"):
                    found.append(os.path.join(dirpath, name))
        return found

    def test_every_template_parses_and_declares_its_placeholders(self):
        found = self._templates()
        self.assertGreaterEqual(len(found), 30, found)
        for path in found:
            with open(path, encoding="utf-8", newline="") as fh:
                text = fh.read()
            declared, body, err = self.mod.parse_template(text)
            self.assertIsNone(err, "%s：%s" % (path, err))
            self.assertEqual(sorted(declared),
                             sorted(set(self.mod.PLACEHOLDER_RE.findall(body))), path)
            self.assertNotIn("# placeholders:", body, path)

    # trace: N-2（V 审计查出：cypress config 的 `supportFile` 指向 `{{TEST_DIR}}/support/e2e.ts`，
    #         技能内须有对应模板——否则渲染出的配置指向一个不存在的文件）
    def test_cypress_support_file_has_template(self):
        profile = os.path.join(self.mod.TEMPLATES_DIR, "framework", "browser-cypress")
        with open(os.path.join(profile, "cypress.config.ts.tpl"),
                  encoding="utf-8", newline="") as fh:
            self.assertIn("{{TEST_DIR}}/support/e2e.ts", fh.read(),
                          "config 的 supportFile 引用变了，本守卫须同步")
        self.assertTrue(os.path.isfile(os.path.join(profile, "support-e2e.ts.tpl")),
                        "cypress.config.ts.tpl 引用了 {{TEST_DIR}}/support/e2e.ts，"
                        "技能内必须有对应模板（N-2：引用悬空）")

    def test_ci_matrix_and_profiles_covered(self):
        for platform in self.mod.CI_PLATFORMS:
            for cls_name in ("browser", "backend"):
                rel = self.mod.CI_TEMPLATES[platform] % cls_name
                self.assertTrue(os.path.isfile(self.mod.template_abs(rel)), rel)
        for profile in self.mod.BROWSER_PROFILES:
            self.assertTrue(os.listdir(os.path.join(self.mod.TEMPLATES_DIR, "framework", profile)),
                            profile)
        for lang in self.mod.BACKEND_PROFILES:
            profile = os.path.join(self.mod.TEMPLATES_DIR, "framework", "backend-%s" % lang)
            self.assertTrue(os.path.isdir(profile), profile)
            self.assertTrue(os.listdir(profile), profile)


class CiTemplateCapabilityTests(unittest.TestCase):
    """返工 F-1 / F-2 / F-7 / F-11：CI 模板的缓存、失败通知、产物归档与报告聚合面。"""

    @classmethod
    def setUpClass(cls):
        cls.mod = load_engine()

    def _render(self, platform, cls_name):
        rel = self.mod.CI_TEMPLATES[platform] % cls_name
        with open(self.mod.template_abs(rel), encoding="utf-8", newline="") as fh:
            text = fh.read()
        declared, _body, err = self.mod.parse_template(text)
        self.assertIsNone(err, "%s：%s" % (rel, err))
        rendered, render_err = self.mod.render_template(text, CI_SUBS)
        self.assertIsNone(render_err, "%s：%s" % (rel, render_err))
        return declared, rendered

    def test_dependency_and_browser_cache_declared(self):
        """F-1：依赖缓存 + 浏览器缓存 + 回退键在模板里（键含锁文件哈希）。"""
        for platform in self.mod.CI_PLATFORMS:
            for cls_name in ("browser", "backend"):
                declared, rendered = self._render(platform, cls_name)
                rel = "%s/%s" % (platform, cls_name)
                self.assertIn("CACHE_PATH", declared, rel)
                self.assertTrue({"CACHE_KEY", "CACHE_LOCKFILE"} & set(declared), rel)
                self.assertIn("~/.npm", rendered, rel)      # 缓存路径确实注入到生成物
                self.assertIn("package-lock.json", rendered, rel)   # 键含锁文件
                if cls_name == "browser":
                    self.assertIn("BROWSER_CACHE_PATH", declared, rel)
                    self.assertIn("~/.cache/ms-playwright", rendered, rel)
        # 回退键（restore-keys）只在有该概念的两平台
        for platform in ("github-actions", "azure-devops"):
            _declared, rendered = self._render(platform, "backend")
            self.assertTrue("restore-keys" in rendered or "restoreKeys" in rendered, platform)

    def test_failure_notification_secret_guarded(self):
        """F-2：失败通知一步在模板里，秘密名经 NOTIFY_SECRET 注入且未配置即跳过。"""
        for platform in self.mod.CI_PLATFORMS:
            for cls_name in ("browser", "backend"):
                declared, rendered = self._render(platform, cls_name)
                rel = "%s/%s" % (platform, cls_name)
                self.assertIn("NOTIFY_SECRET", declared, rel)
                self.assertIn("SLACK_WEBHOOK_URL", rendered, rel)     # 秘密名落进生成物
                self.assertIn("未配置", rendered, rel)                 # 未配置即跳过的守卫
                self.assertIn("docs/ci-secrets-checklist.md", rendered, rel)

    def test_artifact_paths_and_report_aggregation(self):
        """F-7 / F-11：失败产物路径含报告目录；报告阶段聚合各分片产物。"""
        _declared, gha = self._render("github-actions", "browser")
        self.assertIn("playwright-report/", gha)                    # 报告目录不再是硬编码 playwright 专属
        self.assertIn("download-artifact", gha)                     # 聚合
        self.assertIn("test-results/", gha)
        _declared, azure = self._render("azure-devops", "browser")
        self.assertIn("download: current", azure)
        _declared, jenkins = self._render("jenkins", "browser")
        self.assertIn("archiveArtifacts", jenkins)                  # Jenkins 归档
        self.assertIn("junit", jenkins)                             # JUnit 发布
        self.assertIn("playwright-report/", jenkins)
        _declared, gitlab = self._render("gitlab-ci", "browser")
        self.assertIn("playwright-report/", gitlab)

    def test_rendered_ci_files_have_no_unsafe_injection(self):
        """F-12 反面：本技能自己的十个 CI 模板渲染后，脚本块里零不可信插值。"""
        for platform in self.mod.CI_PLATFORMS:
            for cls_name in ("browser", "backend"):
                _declared, rendered = self._render(platform, cls_name)
                self.assertEqual(self.mod.scan_ci_injection(rendered), [],
                                 "%s/%s 的脚本块出现不可信插值" % (platform, cls_name))


class NewTemplateCapabilityTests(EngineCase):
    """返工 F-3 / F-4 / F-5 / F-6 / F-8：助手脚本、CI 文档、语言版本文件、dotnet 示例、support 布局。"""

    def _scaffold(self, files, substitutions):
        self.plan({"setup": "TF-001", "part": "framework",
                   "substitutions": substitutions, "files": files})
        return self.engine(["scaffold", "--plan", "diy-output/scaffold-plan.json"])

    def test_helper_scripts_render_with_shebang(self):
        """F-3：三个助手脚本从模板落盘，产物第一行是 shebang、指令行已剥除。"""
        subs = {"INSTALL_CMD": "npm ci", "LINT_CMD": "npm run lint",
                "TEST_CMD": "npx playwright test", "TEST_GLOB": "**/*.spec.ts",
                "BASE_BRANCH": "main", "BURN_IN_ITERATIONS": "10"}
        names = ("ci-local.sh", "burn-in.sh", "test-changed.sh")
        files = [{"template": "framework/shared/scripts/%s.tpl" % name,
                  "path": "scripts/%s" % name, "kind": "script"} for name in names]
        proc, payload = self._scaffold(files, subs)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(sorted(payload["written"]), sorted(item["path"] for item in files))
        for item in files:
            body = self.read(item["path"])
            self.assertTrue(body.startswith("#!/usr/bin/env bash"), item["path"])
            self.assertNotIn("# placeholders:", body, item["path"])
        self.assertIn("npx playwright test", self.read("scripts/burn-in.sh"))
        self.assertIn("BURN_IN_ITERATIONS", self.read("scripts/burn-in.sh"))

    def test_docs_templates_render(self):
        """F-4：docs/ci.md 与 docs/ci-secrets-checklist.md 从模板落盘（kind: doc）。"""
        subs = dict(CI_SUBS, CI_PLATFORM="github-actions", CI_FILE=".github/workflows/test.yml",
                    FRAMEWORK_NAME="Playwright", TEST_DIR="tests",
                    CI_PLATFORM_SECRETS_UI="Repository Settings → Secrets and variables → Actions",
                    BASE_URL="http://localhost:3000", API_URL="http://localhost:3000/api")
        files = [{"template": "ci/docs/ci.md.tpl", "path": "docs/ci.md", "kind": "doc"},
                 {"template": "ci/docs/ci-secrets-checklist.md.tpl",
                  "path": "docs/ci-secrets-checklist.md", "kind": "doc"}]
        proc, payload = self._scaffold(files, subs)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        ci_doc = self.read("docs/ci.md")
        self.assertIn(".github/workflows/test.yml", ci_doc)
        self.assertIn("scripts/ci-local.sh", ci_doc)
        self.assertIn("SLACK_WEBHOOK_URL", self.read("docs/ci-secrets-checklist.md"))

    def test_language_version_files_and_dotnet_example(self):
        """F-5 / F-6：java / dotnet / ruby 版本文件 + dotnet 示例测试（[Fact]/[Theory] + 夹具注入）。"""
        files = [{"template": "framework/backend-java/.java-version.tpl",
                  "path": ".java-version", "kind": "config"},
                 {"template": "framework/backend-dotnet/global.json.tpl",
                  "path": "global.json", "kind": "config"},
                 {"template": "framework/backend-ruby/.ruby-version.tpl",
                  "path": ".ruby-version", "kind": "config"},
                 {"template": "framework/backend-dotnet/ExampleTests.cs.tpl",
                  "path": "tests/ExampleTests.cs", "kind": "scaffold"}]
        subs = {"JAVA_VERSION": "21", "DOTNET_SDK_VERSION": "8.0.400",
                "RUBY_VERSION": "3.3.5", "TEST_PROJECT_NAME": "Mini.Tests"}
        proc, payload = self._scaffold(files, subs)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(self.read(".java-version").strip(), "21")
        self.assertEqual(self.read(".ruby-version").strip(), "3.3.5")
        self.assertIn('"version": "8.0.400"', self.read("global.json"))
        cs = self.read("tests/ExampleTests.cs")
        self.assertIn("[Fact]", cs)
        self.assertIn("[Theory]", cs)
        self.assertIn("IClassFixture<ExampleFixture>", cs)
        self.assertIn("namespace Mini.Tests;", cs)

    def test_support_layout_and_empty_dir_channel(self):
        """F-8：support/ 布局文档 + 空目录占位文件通道（一个模板多次落点）。"""
        subs = {"TEST_DIR": "tests"}
        files = [{"template": "framework/shared/support-readme.md.tpl",
                  "path": "tests/support/README.md", "kind": "doc"},
                 {"template": "framework/shared/gitkeep.tpl",
                  "path": "tests/support/helpers/.gitkeep", "kind": "scaffold"},
                 {"template": "framework/shared/gitkeep.tpl",
                  "path": "tests/support/page-objects/.gitkeep", "kind": "scaffold"}]
        proc, payload = self._scaffold(files, subs)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("support/page-objects", self.read("tests/support/README.md"))
        for rel in ("tests/support/helpers/.gitkeep", "tests/support/page-objects/.gitkeep"):
            self.assertTrue(os.path.isfile(os.path.join(self.root, rel)), rel)


class ContextAndInjectionTests(EngineCase):
    """返工 F-9 / F-10 / F-12：上下文采集、git 门禁事实、生成物脚本块注入扫描。"""

    def test_detect_reports_git_and_context_docs(self):
        """F-9 / F-10：detect 报 git 事实与架构文档 / auth 线索。"""
        self.write("package.json", json.dumps({"name": "mini", "devDependencies": {"react": "18"}}))
        proc, payload = self.engine(["detect"])
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertFalse(payload["git"]["repository"])     # tempdir 不是仓库
        self.assertEqual(payload["context"]["docs"], [])

        os.makedirs(os.path.join(self.root, ".git"), exist_ok=True)
        self.write(os.path.join(".git", "config"),
                   '[core]\n\trepositoryformatversion = 0\n'
                   '[remote "origin"]\n\turl = git@example.com:mini.git\n')
        self.write("docs/architecture.md", "# 架构\n\n认证走 OAuth2；对外 API 见下表。\n")
        proc, payload = self.engine(["detect"])
        self.assertTrue(payload["git"]["repository"])
        self.assertEqual(payload["git"]["remote"], "origin")
        self.assertIn("docs/architecture.md", payload["context"]["docs"])
        self.assertEqual(payload["context"]["auth"][0]["doc"], "docs/architecture.md")
        self.assertIn("oauth", payload["context"]["auth"][0]["hints"])

    def test_check_flags_unsafe_run_block(self):
        """F-12：生成物脚本块里直接插值不可信上下文 → UNSAFE_INJECTION（注释里的示例不算）。"""
        self.write(os.path.join("diy-output", "test-plan.yaml"), TEST_PLAN)
        self.write("playwright.config.ts", "export default {}" + NL)
        os.makedirs(self.out, exist_ok=True)
        body = NL.join([
            "jobs:", "  lint:", "    steps:",
            "      - run: npm ci",
            "      - run: npm run lint",
            "      - name: Unsafe",
            "        run: |",
            "          # 安全上下文：${{ steps.x.outputs.y }}",
            "          npx playwright test --grep \"${{ inputs.grep }}\"",
            "# 注释里的示例不算违规：- run: echo \"${{ github.head_ref }}\"",
        ]) + NL
        self.write(".github/workflows/test.yml", body)
        import copy
        import yaml
        data = copy.deepcopy(LEDGER)
        self.write(os.path.join("diy-output", "test-framework.yaml"),
                   yaml.safe_dump(data, allow_unicode=True, sort_keys=False))
        proc, payload = self.engine(["check"])
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("UNSAFE_INJECTION", self.codes(payload))
        self.assertTrue(any("inputs." in item["msg"] for item in payload["violations"]))
        # 脚本块只命中 run 块那一条：注释行（含 head_ref 示例）不参与
        hits = [item for item in payload["violations"] if item["code"] == "UNSAFE_INJECTION"]
        self.assertEqual(len(hits), 1, hits)

    def test_scan_covers_yaml_list_and_jenkins_quotes(self):
        """F-12 扫描面：GitLab `script:` 列表项与 Jenkins `sh '''` 块同样在扫。"""
        mod = load_engine()
        gitlab = NL.join([
            "test:", "  script:",
            "    - npm ci",
            "    - echo \"${{ inputs.install-command }}\"",
        ]) + NL
        self.assertEqual(len(mod.scan_ci_injection(gitlab)), 1, gitlab)
        jenkins = NL.join([
            "        steps {",
            "            sh '''",
            "                echo \"${params.CMD}\"",
            "                sh 'npx playwright test --grep \"' + params.TEST_GREP + '\"'",
            "            '''",
            "        }",
        ]) + NL
        self.assertEqual(mod.scan_ci_injection(jenkins), [], jenkins)
        harness = NL.join([
            "                    command: |",
            "                      npx playwright test --grep \"<+input>.testGrep\"",
        ]) + NL
        self.assertEqual(len(mod.scan_ci_injection(harness)), 1, harness)

    def test_check_passes_on_rendered_template(self):
        """F-12 正面（端到端）：本技能渲染出的 GHA 浏览器面流水线过终门——注入扫描零违规。"""
        self.plan(PLAN_CI)
        proc, _payload = self.engine(["scaffold", "--plan", "diy-output/scaffold-plan.json"])
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.write(os.path.join("diy-output", "test-plan.yaml"), TEST_PLAN)
        self.write("playwright.config.ts", "export default {}" + NL)
        import copy
        import yaml
        data = copy.deepcopy(LEDGER)
        data["setups"][0]["mode"] = "ci"
        data["setups"][0]["files"] = [{"path": ".github/workflows/test.yml",
                                       "kind": "ci", "action": "new"}]
        self.write(os.path.join("diy-output", "test-framework.yaml"),
                   yaml.safe_dump(data, allow_unicode=True, sort_keys=False))
        proc, payload = self.engine(["check", "--final"])
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertTrue(payload["ok"])


class ContractSmokeTests(unittest.TestCase):
    """用例 17：SKILL.md 契约冒烟（母本锚串 + 终门句 + steps 计数）。"""

    @classmethod
    def setUpClass(cls):
        with open(SKILL_MD, encoding="utf-8") as fh:
            cls.text = fh.read()

    def test_mother_text_anchors(self):
        self.assertIn(INSTANCE_ZH, self.text)
        self.assertIn(DISCIPLINE_ZH, self.text)
        self.assertIn(READ_DISCIPLINE_ZH, self.text)
        self.assertIn(RENDER_SILENT_ZH, self.text)
        self.assertIn("解析 `project.communication_language` / "
                      "`project.document_output_language` / `paths.output_dir`", self.text)

    def test_final_gate_points_to_engine(self):
        self.assertIn("test_framework.py", self.text)
        self.assertIn("detect", self.text)
        self.assertIn("scaffold", self.text)
        self.assertIn("check --final", self.text)
        self.assertIn("exit 0", self.text)
        # 三命令写入面的完整调用形态落在 steps（主文件只给路由，细节不进主文件）
        with open(os.path.join(STEPS_DIR, "03-scaffold.md"), encoding="utf-8") as fh:
            self.assertIn("scaffold --plan", fh.read())

    def test_frontmatter_and_steps(self):
        self.assertIn("name: diy-test-framework", self.text)
        self.assertIn("outputs: test-framework.yaml", self.text)
        self.assertIn("phase: 3-solutioning", self.text)
        steps = sorted(f for f in os.listdir(STEPS_DIR) if f.endswith(".md"))
        self.assertEqual(len(steps), 6, steps)
        self.assertEqual(steps[0], "01-preflight.md")
        self.assertEqual(steps[-1], "06-finish.md")
        for name in steps:
            with open(os.path.join(STEPS_DIR, name), encoding="utf-8") as fh:
                body = fh.read()
            self.assertIn("**Read (input):**", body, name)
            self.assertIn("## Next", body, name)


if __name__ == "__main__":
    unittest.main()
