# -*- coding: utf-8 -*-
"""diy-readiness-check 确定性引擎 e2e 测试（B1 批 W4，任务书 §2.5/§6）。

覆盖：
- 用例 1：门禁拒绝（缺 stories.yaml / epics project.status 非已定稿）→ exit 1 + 结构化拒绝
          + 路由 + 零产出
- 用例 2：collect 需求清点（FR/NFR 全量 + 优先级 + 归属 feature；epic/story/AC 计数）
- 用例 3：collect 委派 diyc（真跑子进程；必须 FR 缺口同时出现在 diyc.check.violations
          与本引擎 coverage.gaps —— 委派不重实现规则）
- 用例 4：collect 在 diyc 缺席时降级（TOOL_MISSING warning + 不崩 + 仍 exit 0）
- 用例 5：check 合法记录 --final exit 0 唯一放行；违规码（verdict 一致性 / severity 枚举 /
          evidence 缺失 / 零假设 / counts 与集合一致）
- 用例 6：SKILL.md 契约冒烟（母本 §1 / §2 / §3 / §4 / §5 / §6 中文定稿逐字 + 四段中文标题
          + 薄主文件 ≤93 行 + 终门句指向 readiness.py + steps/ 逐个点名下一文件）
夹具全部落 tempdir 自建；不读写本仓库真实 diy-output。
运行：cd diy-coder && python -m unittest discover -s tests -p "test_readiness.py" -v
"""
import contextlib
import io
import json
import os
import re
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.join(HERE, "..", "skills", "diy-readiness-check")
ENGINE = os.path.join(SKILL_DIR, "scripts", "readiness.py")
SKILL_MD = os.path.join(SKILL_DIR, "SKILL.md")
STEPS_DIR = os.path.join(SKILL_DIR, "steps")
NL = chr(10)

# 套件级句式母本（suite-texts.md §1 / §2 / §3 / §4 / §5 / §6 中文定稿，逐字）
# 2026-09-19 中文化轮：英文原形（§1 md5 5445f98b… / §2 md5 f1b3b6fb…）随本技能转中文退役。
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

PRD_YAML = NL.join([
    "project:",
    "  name: mini",
    "  status: 已定稿",
    "  created: '2026-01-01'",
    "  updated: '2026-01-02'",
    "purpose: 夹具用途",
    "goals:",
    "- id: G-1",
    "  goal: 目标一",
    "  metric: 指标一",
    "users:",
    "- id: U-1",
    "  name: 使用者",
    "  need: 需要",
    "features:",
    "- id: F-1",
    "  name: 能力一",
    "  description: 能力描述",
    "  requirements:",
    "  - id: FR-1.1",
    "    statement: 必须能力一",
    "    priority: 必须",
    "  - id: FR-1.2",
    "    statement: 应当能力二",
    "    priority: 应该",
    "nfrs:",
    "- id: NFR-1",
    "  statement: 性能要求",
]) + NL

EPICS_YAML = NL.join([
    "project:",
    "  name: mini",
    "  status: 已定稿",
    "  created: '2026-01-01'",
    "  updated: '2026-01-02'",
    "epics:",
    "- id: E-1",
    "  title: 史诗一",
    "  goal: 用户能完成一件事",
    "  feature_refs: [F-1]",
    "  status: 进行中",
]) + NL

STORIES_YAML = NL.join([
    "project:",
    "  name: mini",
    "  status: 已定稿",
    "  created: '2026-01-01'",
    "  updated: '2026-01-02'",
    "stories:",
    "- id: S-1",
    "  epic: E-1",
    "  title: 故事一",
    "  narrative: 作为使用者，我希望完成一件事",
    "  acceptance_criteria:",
    "  - id: AC-1.1",
    "    given: 前置",
    "    when: 动作",
    "    then: 结果",
    "    refs:",
    "    - FR-1.1",
    "  status: 待办",
]) + NL

READINESS_YAML = NL.join([
    "project:",
    "  name: mini",
    "  created: '2026-01-01'",
    "  updated: '2026-09-14'",
    "checks:",
    "- id: IR-001",
    "  date: '2026-09-14'",
    "  status: 已定稿",
    "  scope: [prd, epics, stories]",
    "  verdict: 有风险就绪",
    "  findings:",
    "  - area: epics",
    "    severity: 中",
    "    message: 史诗目标描述偏技术",
    "    evidence: epics.yaml epics[E-1].goal",
    "  coverage: {must_frs: 1, covered: 1, gaps: []}",
    "  counts: {frs: 2, nfrs: 1, epics: 1, stories: 1, acs: 1,"
    " findings_by_severity: {中: 1}}",
    "revisions: []",
]) + NL


def run_engine(args):
    import subprocess
    return subprocess.run([sys.executable, ENGINE] + args,
                          capture_output=True, text=True, encoding="utf-8")


class EngineCase(unittest.TestCase):
    """tmp 项目根 + diy-output 目录的公共夹具。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="readiness-")
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

    def write_trio(self, prd=PRD_YAML, epics=EPICS_YAML, stories=STORIES_YAML):
        self.write("diy-output/prd.yaml", prd)
        self.write("diy-output/epics.yaml", epics)
        self.write("diy-output/stories.yaml", stories)

    def collect(self, *extra):
        return run_engine(["collect", "--project-root", self.root,
                           "--output-dir", self.out, "--json"] + list(extra))

    def check(self, *extra):
        return run_engine(["check", "--project-root", self.root,
                           "--output-dir", self.out, "--json"] + list(extra))

    def readiness_path(self):
        return os.path.join(self.out, "readiness.yaml")

    def out_files(self):
        return sorted(os.listdir(self.out))


class GateTests(EngineCase):

    # trace: 任务书 §6 门禁（三件套缺席 → 零产出退出 + 路由）
    def test_gate_refuses_missing_stories_with_zero_output(self):
        self.write("diy-output/prd.yaml", PRD_YAML)
        self.write("diy-output/epics.yaml", EPICS_YAML)
        r = self.collect()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertNotIn("Traceback", r.stderr)
        data = json.loads(r.stdout)
        self.assertFalse(data["ok"])
        self.assertFalse(data["gate"]["passed"])
        self.assertEqual([x["code"] for x in data["violations"]], ["MISSING_FILE"])
        self.assertIn("stories.yaml", data["violations"][0]["where"])
        self.assertTrue(data["gate"]["route"])
        self.assertNotIn("readiness.yaml", self.out_files(), "拒绝路径不得产出 readiness.yaml")
        self.assertEqual(self.out_files(), ["epics.yaml", "prd.yaml"])

    # trace: 任务书 §6 门禁（epics/stories 须 project.status: 已定稿）
    def test_gate_refuses_non_final_epics(self):
        self.write_trio(epics=EPICS_YAML.replace("status: 已定稿", "status: 草稿", 1))
        r = self.collect()
        self.assertEqual(r.returncode, 1, r.stdout)
        data = json.loads(r.stdout)
        self.assertFalse(data["ok"])
        self.assertEqual([x["code"] for x in data["violations"]], ["STATUS_MISMATCH"])
        self.assertIn("diy-epics-stories", data["gate"]["route"])
        self.assertNotIn("readiness.yaml", self.out_files())

    # trace: 任务书 §2.2（引擎不做实例解析/目录推导：--output-dir 必填）
    def test_output_dir_is_mandatory(self):
        r = run_engine(["collect", "--project-root", self.root, "--json"])
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        r2 = run_engine(["check", "--project-root", self.root, "--json"])
        self.assertEqual(r2.returncode, 2, r2.stdout + r2.stderr)


class CollectTests(EngineCase):

    # trace: 任务书 §6 collect ②（需求清点单：FR/NFR 全量 + 优先级 + 归属 feat
    #        ure；epic/story/AC 计数）
    def test_collect_inventory_reports_requirements(self):
        self.write_trio()
        r = self.collect()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertTrue(data["ok"])
        self.assertTrue(data["gate"]["passed"])
        frs = data["requirements"]["frs"]
        self.assertEqual([(f["id"], f["priority"], f["feature"]) for f in frs],
                         [("FR-1.1", "必须", "F-1"), ("FR-1.2", "应该", "F-1")])
        self.assertEqual(data["requirements"]["nfrs"], ["NFR-1"])
        self.assertEqual(data["requirements"]["must_frs"], ["FR-1.1"])
        self.assertEqual(data["coverage"], {"must_frs": 1, "covered": 1, "gaps": []})
        self.assertEqual(data["counts"]["epics"], 1)
        self.assertEqual(data["counts"]["stories"], 1)
        self.assertEqual(data["counts"]["acs"], 1)
        self.assertEqual(data["docs"]["design"]["found"], False)

    # trace: 任务书 §2.3/§6 collect ③④（跨文档核对委派 diyc；缺口两侧同现）
    def test_collect_delegates_diyc_and_surfaces_gap(self):
        self.write_trio(stories=STORIES_YAML.replace(NL + "    - FR-1.1", ""))
        r = self.collect()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertTrue(data["diyc"]["available"])
        self.assertEqual(data["diyc"]["checked"], ["prd", "epics", "stories"])
        self.assertIn("SET_MISMATCH",
                      {x["code"] for x in data["diyc"]["check"]["violations"]})
        self.assertEqual(data["coverage"]["gaps"], ["FR-1.1"])
        self.assertEqual(data["coverage"]["covered"], 0)
        # diyc 真跑：回执 counts 在场（stories 22 行级计数）
        self.assertIn("stories", data["diyc"]["check"]["counts"])

    # trace: 任务书 §2.3（diyc 缺席 → 结构化 warning 降级，不崩）
    def test_collect_degrades_when_diyc_missing(self):
        self.write_trio()
        sys.path.insert(0, os.path.join(SKILL_DIR, "scripts"))
        old_bytecode = sys.dont_write_bytecode
        sys.dont_write_bytecode = True  # 不把 __pycache__ 落进技能目录
        try:
            import readiness
        finally:
            sys.dont_write_bytecode = old_bytecode
            sys.path.pop(0)
        original = readiness.diyc_script_path
        readiness.diyc_script_path = lambda: os.path.join(self.root, "no-such-diyc.py")
        try:
            args = readiness.build_parser().parse_args(
                ["collect", "--project-root", self.root, "--output-dir", self.out,
                 "--json"])
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = args.func(args)
        finally:
            readiness.diyc_script_path = original
        self.assertEqual(rc, 0, buf.getvalue())
        data = json.loads(buf.getvalue())
        self.assertTrue(data["ok"])
        self.assertFalse(data["diyc"]["available"])
        self.assertEqual(data["diyc"]["check"]["violations"], [])
        # 降级面：architecture 缺席 warning（源 step-01 §4）+ diyc 缺席 warning，不崩
        self.assertEqual([w["code"] for w in data["warnings"]],
                         ["MISSING_FILE", "TOOL_MISSING"], data["warnings"])


class CheckValidationTests(EngineCase):

    # trace: 任务书 §2.5 用例 3（合法记录 --final exit 0 唯一放行）
    def test_check_final_legal_record_passes(self):
        self.write("diy-output/readiness.yaml", READINESS_YAML)
        r = self.check("--final")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertTrue(data["ok"])
        self.assertEqual(data["violations"], [])
        self.assertEqual(data["counts"]["checks"], 1)
        self.assertEqual(data["counts"]["by_verdict"], {"有风险就绪": 1})

    # trace: 任务书 §6 check（verdict 与 findings 一致性）
    def test_check_verdict_findings_consistency(self):
        ready = (READINESS_YAML
                 .replace("verdict: 有风险就绪", "verdict: 就绪")
                 .replace("severity: 中", "severity: 高"))
        self.write("diy-output/readiness.yaml", ready)
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("SET_MISMATCH",
                      {x["code"] for x in json.loads(r.stdout)["violations"]})
        # 有风险就绪 不要求阻塞项；未就绪 则必须有
        risky = READINESS_YAML.replace("verdict: 有风险就绪", "verdict: 未就绪")
        self.write("diy-output/readiness.yaml", risky)
        r2 = self.check()
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertIn("SET_MISMATCH",
                      {x["code"] for x in json.loads(r2.stdout)["violations"]})

    # trace: 任务书 §6 check（schema/枚举/severity 枚举 + 重复 ID）
    def test_check_reports_schema_violations(self):
        cases = [
            ("ENUM_INVALID", "severity: 中", "severity: blocker"),
            ("ENUM_INVALID", "id: IR-001", "id: IR-1"),
            ("ENUM_INVALID", "area: epics", "area: sprint"),
            ("UNPARSABLE_YAML", None, None),
        ]
        for code, old, new in cases:
            text = ("checks: [" + NL) if old is None else READINESS_YAML.replace(old, new)
            self.write("diy-output/readiness.yaml", text)
            r = self.check()
            self.assertEqual(r.returncode, 1, r.stdout)
            self.assertIn(code, {x["code"] for x in json.loads(r.stdout)["violations"]},
                          "%s 未报出：%s" % (code, r.stdout))
        # 重复 IR id → DUPLICATE_ID
        body = READINESS_YAML.split("checks:" + NL, 1)[1].replace("revisions: []" + NL, "")
        self.write("diy-output/readiness.yaml",
                   READINESS_YAML.replace("revisions: []" + NL, "") + body)
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("DUPLICATE_ID", {x["code"] for x in json.loads(r.stdout)["violations"]})

    # trace: 任务书 §6 check --final（evidence 必填 / counts 与集合一致 / 零假设）
    def test_check_final_duties(self):
        no_evidence = READINESS_YAML.replace(NL + "    evidence: epics.yaml epics[E-1].goal", "")
        self.write("diy-output/readiness.yaml", no_evidence)
        r = self.check("--final")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("EVIDENCE_MISSING",
                      {x["code"] for x in json.loads(r.stdout)["violations"]})
        bad_counts = READINESS_YAML.replace("findings_by_severity: {中: 1}",
                                            "findings_by_severity: {中: 2}")
        self.write("diy-output/readiness.yaml", bad_counts)
        r2 = self.check("--final")
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertIn("SET_MISMATCH",
                      {x["code"] for x in json.loads(r2.stdout)["violations"]})
        assumption = READINESS_YAML.replace("message: 史诗目标描述偏技术",
                                            "message: '[假设] 史诗目标偏技术'")
        self.write("diy-output/readiness.yaml", assumption)
        r3 = self.check("--final")
        self.assertEqual(r3.returncode, 1, r3.stdout)
        self.assertIn("ASSUMPTION_PRESENT",
                      {x["code"] for x in json.loads(r3.stdout)["violations"]})

    # trace: 任务书 §2.5 用例 3（缺文件 → 结构化违规，不 Traceback）
    def test_check_missing_file_is_structured(self):
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertNotIn("Traceback", r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual(data["violations"][0]["code"], "MISSING_FILE")
        self.assertEqual(data["counts"]["checks"], 0)


class SkillContractTests(unittest.TestCase):
    """用例 6：SKILL.md / steps 契约冒烟（母本中文定稿逐字 + 结构与路由纪律）。"""

    def read(self, path):
        if not os.path.isfile(path):
            self.skipTest("%s 尚未交付——契约用例待补" % os.path.basename(path))
        with io.open(path, encoding="utf-8") as f:
            return f.read()

    # trace: 任务书 §2.1 / 母本 §1（实例解析句中文定稿逐字；2026-09-19 中文化轮）
    def test_instance_resolution_sentence_verbatim(self):
        raw = self.read(SKILL_MD)
        self.assertIn(INSTANCE_ZH, raw, "SKILL.md 缺母本 §1 中文定稿（逐字）")
        self.assertNotIn("Instance resolution (FR-4.5/D-9)", raw, "已转中文定稿，仍残留英文原形")

    # trace: 任务书 §2.1 / 母本 §3（配置键全路径带 project. 前缀）
    def test_resolve_keys_anchor(self):
        self.assertIn(RESOLVE_KEYS_ZH, self.read(SKILL_MD), "SKILL.md 缺母本 §3 键路径锚串")

    # trace: 任务书 §2.1 / 母本 §4（读取纪律逐字；C1 拆法）
    def test_read_discipline_verbatim(self):
        self.assertIn(READ_DISCIPLINE_ZH, self.read(SKILL_MD), "SKILL.md 缺母本 §4 定稿（逐字）")

    # trace: 任务书 §2.1 / 母本 §5（渲染静默整句，A-12 命令全文形态）
    def test_render_silent_line(self):
        raw = self.read(SKILL_MD)
        self.assertIn(RENDER_SILENT_ZH, raw, "SKILL.md 缺母本 §5 渲染静默句")
        self.assertIn("diy-viewer/scripts/viewer.py", raw, "渲染句缺 viewer 命令全文")

    # trace: 任务书 §2.1 / 母本 §6 + §2（Rules 段末尾顺序：§6 在前、§2 收尾）
    def test_precise_and_writing_discipline_at_rules_end(self):
        raw = self.read(SKILL_MD)
        self.assertIn(PRECISE_ZH, raw, "SKILL.md 缺母本 §6 精准简练条款")
        self.assertIn(DISCIPLINE_ZH, raw, "SKILL.md 缺母本 §2 中文定稿")
        self.assertEqual(DISCIPLINE_ZH, raw.rstrip(NL).splitlines()[-1],
                         "写作纪律块须置 Rules 段末尾（文件收尾行）")
        self.assertLess(raw.index(PRECISE_ZH), raw.index(DISCIPLINE_ZH),
                        "Rules 末尾顺序应为 §6 精准简练 → §2 写作纪律块")

    # trace: 任务书 §2.1/#11/#12（终门句指向 readiness.py check --final；渲染静默；读一条加载一条）
    def test_final_gate_points_to_engine(self):
        skill = self.read(SKILL_MD)
        self.assertIn("readiness.py", skill, "终门句未指向领域引擎")
        self.assertIn("check --final", skill, "终门句缺 check --final")
        self.assertIn("--json", skill, "终门句缺 --json 回执")
        self.assertIn("--output-dir", skill, "激活句/终门句须声明 --output-dir 必填")
        self.assertIn("collect", skill, "激活段未接线 collect")
        self.assertIn("diyc.py", skill, "激活句须委托 diyc.py resolve 做实例解析")
        self.assertIn("viewer.py", skill, "缺渲染静默命令")
        self.assertNotIn("bmad-help", skill, "不得引用不存在的技能")

    # trace: 任务书 §2.1 / 2026-09-19 中文化政策（薄主文件 ≤93 行 + 四段中文标题 + 工作流点名）
    def test_thin_main_file_four_chinese_sections(self):
        raw = self.read(SKILL_MD)
        self.assertLessEqual(len(raw.splitlines()), 93, "薄主文件超出 93 行预算")
        self.assertIn("diy-readiness-check", raw.splitlines()[0] + raw[:400], "标题未含技能名")
        for section in ("## 激活时", "## 工作流", "## 结构", "## 规则"):
            self.assertIn(section, raw, "缺四段结构：%s" % section)
        for name in ("01-document-discovery.md", "02-requirement-inventory.md",
                     "03-coverage-validation.md", "04-ux-alignment.md",
                     "05-epic-quality-review.md", "06-final-assessment.md"):
            self.assertIn(name, raw, "工作流未点名 %s" % name)

    # trace: 任务书 §2.1（steps/ 读一条加载一条，每步结尾点名下一个文件）
    def test_steps_chain_names_next_file(self):
        steps = ("01-document-discovery.md", "02-requirement-inventory.md",
                 "03-coverage-validation.md", "04-ux-alignment.md",
                 "05-epic-quality-review.md", "06-final-assessment.md")
        for name, nxt in zip(steps, steps[1:]):
            text = self.read(os.path.join(STEPS_DIR, name))
            self.assertIn("## 播报与下一步", text, "%s 缺「播报与下一步」段" % name)
            self.assertIn(nxt, text, "%s 未点名下一个文件 %s" % (name, nxt))
        last = self.read(os.path.join(STEPS_DIR, steps[-1]))
        self.assertIn("最后一个步骤文件", last, "末步须声明本步是终局")

    # trace: 任务书 §0.3（未建技能引用一律裁剪——技能面不得留悬空 bmad- 引用）
    def test_no_dangling_bmad_references(self):
        targets = [SKILL_MD]
        if os.path.isdir(STEPS_DIR):
            targets += [os.path.join(STEPS_DIR, n)
                        for n in sorted(os.listdir(STEPS_DIR)) if n.endswith(".md")]
        for path in targets:
            text = self.read(path)
            hits = re.findall(r"bmad-[a-z0-9-]+", text)
            self.assertEqual(hits, [], "%s 含悬空 bmad- 引用：%s" % (path, hits))


if __name__ == "__main__":
    unittest.main()
