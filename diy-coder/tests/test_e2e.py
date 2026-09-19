# -*- coding: utf-8 -*-
"""diy-e2e-tests 确定性引擎测试（B2 批 W6，任务书 §8 / §2.5）。

覆盖：
- 用例 1：detect 在合成 package.json 夹具上识别框架（playwright）
- 用例 2：detect 在 pyproject.toml 夹具上识别 pytest；损坏清单降级不崩
- 用例 3：detect 无清单 → framework null + suggested 非空（不自动安装）
- 用例 4：record 追加合法 TC（status: 通过）→ exit 0 + diyc 交叉核对键在场
- 用例 5：record 拒绝重号 TC（DUPLICATE_ID）、technique 非 场景（ENUM_INVALID）、
          悬空 ac（UNKNOWN_ID）—— 全部零写入
- 用例 6：record 缺 test-plan.yaml（MISSING_FILE）/ --output-dir 必填（exit 2）
- 用例 7：SKILL.md 契约冒烟（母本 §1/§2/§3/§4/§5/§6 中文定稿逐字 + 四段中文标题
          + 薄主文件 ≤93 行 + 终门句指向 e2e.py record）
- 用例 8：B-17 施工件（runner 推导顺序 / defer-add 入队 / 三步可达路径 / `type` 轴脱钩 / A-8 引用）

夹具全部落 tempdir 自建；不读写本仓库真实 diy-output；不依赖本机 git 状态。
运行：cd diy-coder && python -m unittest discover -s tests -p "test_e2e.py" -v
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
SKILL_DIR = os.path.join(HERE, "..", "skills", "diy-e2e-tests")
ENGINE = os.path.join(SKILL_DIR, "scripts", "e2e.py")
SKILL_MD = os.path.join(SKILL_DIR, "SKILL.md")
STEPS_DIR = os.path.join(SKILL_DIR, "steps")
NL = chr(10)

# 母本句式（suite-texts.md §1–§6）中文定稿，逐字；2026-09-19 中文化轮
# 英文原形（§1 md5 5445f98b… / §2 md5 f1b3b6fb…）由中文定稿取代，不再断言 md5。
INSTANCE_ZH = ("实例解析（FR-4.5/D-9）由工具脚本执行：运行 "
               "`python \"{project-root}/.claude/skills/diy-tools/scripts/diyc.py\" "
               "resolve [--instance <name>] --json`，把回执里的 `output_dir` "
               "当作本次运行唯一的读写根目录。")
RESOLVE_KEYS_ZH = ("解析 `project.communication_language` / "
                   "`project.document_output_language` / `paths.output_dir`")
READ_DISCIPLINE_ZH = ("读取纪律：预载预算 = 本文件、上述配置与回执、`steps/` 下当前那一个文件"
                      "——绝不批量预载；执行期读取以每个步骤开头的 `Read (input)` 行为唯一权威，"
                      "**主文件不列举封闭清单**。")
RENDER_SILENT_ZH = "渲染是静默旁路——只写调用命令"
PRECISE_ZH = ("- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；"
              "不复述上游已写的信息（引用 ID）；不写没有信息量的套话。")
DISCIPLINE_ZH = ("- **写作纪律。** 主字段 = 大白话主句；数字/枚举内联；"
                 "机器语法（命令/旗标/路径）进括号；机器锚点逐字保留"
                 "（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 "
                 "`diy-design` 的 detect 启发式。schema 若定义 `plain`："
                 "一行写清该条目为什么存在，绝不写是什么（转述会漂移）；"
                 "只写难懂的条目。若定义 `detail`：过程叙述——结论留在主字段。")
INSTANCE_EN_MARK = "Instance resolution (FR-4.5/D-9)"

H1_RE = re.compile(r"^# Step (\d+) — .*[一-鿿]")

STEPS = ("01-detect.md", "02-targets.md", "03-generate-api.md",
         "04-generate-e2e.md", "05-record.md")

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
    "  status: 已定稿",
    "  created: '2026-01-01'",
    "  updated: '2026-01-02'",
    "test_cases:",
    "- id: TC-1.1.1",
    "  title: 既有单元用例",
    "  ac: AC-1.1",
    "  type: 单元",
    "  priority: P0",
    "  technique: 边界",
    "  kill_target: 边界值未被拦截",
    "  status: 通过",
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


def tc_json(tc_id="TC-1.1.2", technique="场景", ac="AC-1.1", status="通过",
            type_name="端到端"):
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
        self.assertIn("technique: 场景", plan)
        self.assertIn("type: 端到端", plan)
        # 既有条目不被触碰
        self.assertIn("id: TC-1.1.1", plan)
        self.assertIn("technique: 边界", plan)
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

    # trace: 任务书 §8（technique 非 场景 拒绝：ENUM_INVALID）
    def test_record_rejects_non_scenario_technique(self):
        tc = self.write("new-tc.json", tc_json(technique="边界"))
        r = self.record(tc)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ENUM_INVALID", {x["code"] for x in json.loads(r.stdout)["violations"]})
        self.assertEqual(self.read("diy-output/test-plan.yaml"), self.before)
        # type 非 端到端 同样拒绝
        tc2 = self.write("new-tc2.json", tc_json(type_name="单元"))
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
        tc = self.write("new-tc.json", tc_json(status="待办"))
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
    """用例 7：SKILL.md / steps 契约冒烟（母本中文定稿逐字 + 结构与路由纪律）。"""

    def read(self, path):
        if not os.path.isfile(path):
            self.skipTest("%s 尚未交付——契约用例待补" % os.path.basename(path))
        with io.open(path, encoding="utf-8") as f:
            return f.read()

    def read_skill(self):
        return self.read(SKILL_MD)

    # trace: 母本 §1（实例解析句中文定稿逐字；2026-09-19 中文化轮）
    def test_instance_resolution_sentence_verbatim(self):
        raw = self.read_skill()
        self.assertIn(INSTANCE_ZH, raw, "SKILL.md 缺母本 §1 中文定稿（逐字）")
        self.assertNotIn(INSTANCE_EN_MARK, raw, "已转中文定稿，仍残留英文原形")

    # trace: 母本 §3（配置键全路径带 project. 前缀；A-1/A-2/A-3）
    def test_resolve_keys_anchor(self):
        raw = self.read_skill()
        self.assertIn(RESOLVE_KEYS_ZH, raw, "SKILL.md 缺母本 §3 键路径锚串")
        self.assertIn("缺省链：", raw, "SKILL.md 缺母本 §3 缺省链")
        self.assertIn("`--instance <name>` 时才传", raw, "SKILL.md 缺母本 §3 实例触发条款")

    # trace: 母本 §4（读取纪律逐字；C1 拆法）
    def test_read_discipline_verbatim(self):
        self.assertIn(READ_DISCIPLINE_ZH, self.read_skill(), "SKILL.md 缺母本 §4 定稿（逐字）")

    # trace: 母本 §5（渲染静默整句 + viewer 命令全文，A-12 同式）
    def test_render_silent_line(self):
        raw = self.read_skill()
        self.assertIn(RENDER_SILENT_ZH, raw, "SKILL.md 缺母本 §5 渲染静默句")
        self.assertIn("diy-viewer/scripts/viewer.py", raw, "渲染句缺 viewer 命令全文")

    # trace: 母本 §6 + §2（Rules 段末尾顺序：§6 在前、§2 收尾）
    def test_precise_and_writing_discipline_at_rules_end(self):
        raw = self.read_skill()
        self.assertIn(PRECISE_ZH, raw, "SKILL.md 缺母本 §6 精准简练条款")
        self.assertIn(DISCIPLINE_ZH, raw, "SKILL.md 缺母本 §2 中文定稿")
        self.assertEqual(DISCIPLINE_ZH, raw.rstrip(NL).splitlines()[-1],
                         "写作纪律块须置 Rules 段末尾（文件收尾行）")
        self.assertLess(raw.index(PRECISE_ZH), raw.index(DISCIPLINE_ZH),
                        "Rules 末尾顺序应为 §6 精准简练 → §2 写作纪律块")

    # trace: 母本 §5 / 任务书 §2.1（终门句指向 e2e.py record + --output-dir 实参写全）
    def test_final_gate_points_to_engine(self):
        skill = self.read_skill()
        self.assertIn("e2e.py", skill, "终门句未指向领域引擎")
        self.assertIn("record", skill, "终门句缺 record 子命令")
        self.assertIn("--json", skill, "终门句缺 --json 回执")
        self.assertIn("--output-dir", skill, "终门句缺 --output-dir 实参（必填、不写「同 activation」）")
        self.assertIn("diyc.py", skill, "激活句须委托 diyc.py resolve 做实例解析")
        self.assertIn("viewer.py", skill, "缺渲染静默命令")

    # trace: 2026-09-19 中文化政策（薄主文件 ≤93 行 + 四段中文标题 + 工作流点名五步）
    def test_thin_main_file_four_chinese_sections(self):
        raw = self.read_skill()
        self.assertLessEqual(len(raw.splitlines()), 93, "薄主文件超出 93 行预算")
        self.assertIn("diy-e2e-tests", raw.splitlines()[0] + raw[:400], "标题未含技能名")
        for section in ("## 激活时", "## 工作流", "## 结构", "## 规则"):
            self.assertIn(section, raw, "缺四段结构：%s" % section)
        for name in STEPS:
            self.assertIn(name, raw, "工作流未点名 %s" % name)

    # trace: 范本 §三（steps H1 = `# Step N — <中文步名>`；Read/Write 两行逐字英文）
    def test_steps_shape_and_chain(self):
        names = sorted(n for n in os.listdir(STEPS_DIR) if n.endswith(".md"))
        self.assertEqual(names, sorted(STEPS), "steps 文件集与工作流点名不符")
        for i, name in enumerate(names, start=1):
            raw = self.read(os.path.join(STEPS_DIR, name))
            m = H1_RE.match(raw.splitlines()[0])
            self.assertTrue(m, "%s 的 H1 须为 '# Step N — <中文步名>'" % name)
            self.assertEqual(int(m.group(1)), i, "%s 的步号与文件序不符" % name)
            self.assertIn(NL + "**Read (input):**", raw, "%s 缺 '**Read (input):**' 行" % name)
            self.assertIn(NL + "**Write (output):**", raw, "%s 缺 '**Write (output):**' 行" % name)
            self.assertIn("## 播报与下一步", raw, "%s 缺末段「播报与下一步」" % name)
        # 逐步点名下一个文件；末步指向重入口（零下一步）
        for cur, nxt in zip(names, names[1:]):
            self.assertIn("`./" + nxt + "`", self.read(os.path.join(STEPS_DIR, cur)),
                          "%s 未点名下一个步骤 %s" % (cur, nxt))


class B17DispositionTests(unittest.TestCase):
    """用例 8：B-17 五条施工件的落点断言（SS-020-01/03/04/05 + A-8）。"""

    def read(self, path):
        if not os.path.isfile(path):
            self.skipTest("%s 尚未交付——B-17 用例待补" % os.path.basename(path))
        with io.open(path, encoding="utf-8") as f:
            return f.read()

    def step(self, name):
        return self.read(os.path.join(STEPS_DIR, name))

    # trace: SS-020-01（runner 命令推导顺序：项目脚本 > framework 惯例 > 明写「按惯例推导」）
    def test_runner_derivation_order(self):
        raw = self.step("01-detect.md")
        self.assertIn("runner 命令取值顺序", raw)
        self.assertIn("`scripts.test`", raw, "缺项目脚本一级（package.json scripts.test）")
        self.assertIn("惯例命令", raw, "缺 framework 惯例命令一层")
        self.assertIn("按惯例推导", raw, "缺都取不到时的显式声明")
        self.assertIn("第 4 步的 runner 不可用分支据此上报", raw, "缺上一步来源的接续说明")
        e2e = self.step("04-generate-e2e.md")
        self.assertIn("第 1 步的 runner 取值顺序", e2e, "第 4 步未指向 runner 推导来源")

    # trace: SS-020-03（未决绑定 → diyc.py defer-add 入队，reason: 仅人工可做）
    def test_unresolved_binding_queues_defer_add(self):
        raw = self.step("02-targets.md")
        self.assertIn('diyc.py" defer-add --entry', raw, "缺 defer-add 入队命令")
        self.assertIn('"reason": "仅人工可做"', raw, "reason 须为「仅人工可做」")
        self.assertIn("headless 或未获裁定", raw, "缺入队触发条件")
        self.assertIn("`DA-###`", raw, "缺收尾摘要列出 DA 序号的义务")
        self.assertNotIn("[ASSUMPTION]", raw, "C7①：本条无值可挂，不得留旧令牌")
        self.assertNotIn("user-only", raw, "机器层已切中文，旧枚举值不得残留")

    # trace: SS-020-05（三步可达路径：报 TC + `待审查` 归 L3 + `已完成` 走 --falsify）
    def test_three_step_reachable_path(self):
        raw = self.step("05-record.md")
        self.assertIn("三步可达路径", raw)
        self.assertIn("`TC-x.y.z`", raw, "缺逐条报 TC ID")
        self.assertIn("待审查", raw, "缺 review 态归 diy-review L3 的路径")
        self.assertIn("diy-review --falsify <S-x>", raw, "缺 done 态的唯一入口")
        self.assertIn("`bug-add`", raw, "缺 falsify 命中后的入库去向")
        self.assertIn("零写 `sprint.yaml`", raw, "缺「本技能不写 sprint.yaml」的边界句")

    # trace: SS-020-04（`type` 轴脱钩：层信息落 title，type 恒为 端到端）
    def test_type_axis_decoupled_from_layer(self):
        for label, raw in (("SKILL.md", self.read(SKILL_MD)),
                           ("steps/02-targets.md", self.step("02-targets.md")),
                           ("steps/05-record.md", self.step("05-record.md"))):
            self.assertIn("生成层轴", raw, "%s 缺层轴声明" % label)
            self.assertIn("`title`", raw, "%s 缺层信息落 title" % label)
            self.assertIn("恒为 `端到端`", raw, "%s 缺 type 固定值口径" % label)
        api = self.step("03-generate-api.md")
        self.assertIn("不写进 `test-plan.yaml` 的 `type` 字段", api, "步骤 3 未同此口径")

    # trace: A-8 / B4（priority 映射只引用 diy-test-design，不重定义）
    def test_priority_mapping_referenced_not_redefined(self):
        skill = self.read(SKILL_MD)
        self.assertIn("diy-test-design", skill, "未点名 priority 映射的权威出处")
        self.assertIn("priority 映射到风险", skill, "未点名权威条款名")
        self.assertIn("只引用，不重定义", skill, "缺「只引用不重定义」的措辞")
        for frag in ("`必须`→P0", "应该`→P1", "可选`→P2"):
            self.assertNotIn(frag, skill, "A-8：优先级映射不得在 e2e-tests 重定义（%s）" % frag)
        self.assertIn("priority 映射到风险", self.step("05-record.md"),
                      "步骤 5 的用例 JSON 处未引用权威出处")


if __name__ == "__main__":
    unittest.main()
