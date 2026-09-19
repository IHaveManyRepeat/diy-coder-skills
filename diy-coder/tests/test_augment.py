# -*- coding: utf-8 -*-
# trace: 2026-09-13 裁定——augment 正交字段（diy-augment 编码后验证留痕）的 viewer 呈现：
# 任务卡片徽章（通过/失败/已跳过）+「补测待裁断」聚合面板（跨 test-plan/stories 反查）+
# 索引卡片徽章。无 fail 任务时面板与徽章零输出。
"""diy-viewer 对 sprint.aggregate augment 字段的渲染测试。

夹具：临时项目 + sprint.yaml（三种 augment 态）/ test-plan.yaml（fail 用例带
kill_target 与 note）/ stories.yaml（标题反查）。
另：diy-augment 的 SKILL.md 契约冒烟（中文化轮 2026-09-19——母本 §1/§2/§3/§5/§6 逐字
+ 四段中文标题 + B-16 九条语义锚串 + A-8/A-9）。
"""
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
VIEWER = os.path.join(HERE, "..", "skills", "diy-viewer", "scripts", "viewer.py")
NL = chr(10)
SKILL_MD = os.path.join(HERE, "..", "skills", "diy-augment", "SKILL.md")

# 套件级句式母本（suite-texts.md §1/§2/§3/§5/§6）中文定稿——逐字；与
# tests/test_suite_texts.py 的常量同文（那边是套件级强制，这里是本技能局部冒烟）
INSTANCE_ZH = ("实例解析（FR-4.5/D-9）由工具脚本执行：运行 "
               "`python \"{project-root}/.claude/skills/diy-tools/scripts/diyc.py\" "
               "resolve [--instance <name>] --json`，把回执里的 `output_dir` "
               "当作本次运行唯一的读写根目录。")
INSTANCE_EN_MARK = "Instance resolution (FR-4.5/D-9)"
RESOLVE_KEYS_ZH = ("解析 `project.communication_language` / "
                   "`project.document_output_language` / `paths.output_dir`")
RENDER_SILENT_ZH = ("渲染是静默旁路——只写调用命令，不新增「打开浏览器 / 报告路径等待查看 / "
                    "阻塞等待」交互点：`python \"{project-root}/.claude/skills/diy-viewer/"
                    "scripts/viewer.py\" --project-root \"{project-root}\"`"
                    "（resolved 实例时附 `--instance <name>`）。")
PRECISE_ZH = ("- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；"
              "不复述上游已写的信息（引用 ID）；不写没有信息量的套话。")
DISCIPLINE_ZH = ("- **写作纪律。** 主字段 = 大白话主句；数字/枚举内联；"
                 "机器语法（命令/旗标/路径）进括号；机器锚点逐字保留"
                 "（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 "
                 "`diy-design` 的 detect 启发式。schema 若定义 `plain`："
                 "一行写清该条目为什么存在，绝不写是什么（转述会漂移）；"
                 "只写难懂的条目。若定义 `detail`：过程叙述——结论留在主字段。")

SPRINT_WITH_FAIL = NL.join([
    "project:",
    "  name: t",
    "  status: 已定稿",
    "tasks:",
    "- story: S-1",
    "  status: 已完成",
    "  test_refs: [TC-1.1.1]",
    "  augment: 失败",
    "- story: S-2",
    "  status: 已完成",
    "  test_refs: [TC-1.1.2]",
    "  augment: 通过",
    "- story: S-3",
    "  status: 已完成",
    "  test_refs: []",
    "  augment: 已跳过",
])

SPRINT_NO_FAIL = NL.join([
    "project:",
    "  name: t",
    "  status: 已定稿",
    "tasks:",
    "- story: S-2",
    "  status: 已完成",
    "  test_refs: [TC-1.1.2]",
    "  augment: 通过",
])

TEST_PLAN = NL.join([
    "project:",
    "  name: t",
    "  status: 已定稿",
    "test_cases:",
    "- id: TC-1.1.1",
    "  title: 空输入边界",
    "  ac: AC-1.1",
    "  status: 失败",
    "  technique: 覆盖分支",
    "  kill_target: 空输入未拦截",
    "  note: 覆盖率证据：分支未覆盖",
    "- id: TC-1.1.2",
    "  title: 正常路径",
    "  ac: AC-1.1",
    "  status: 通过",
])

STORIES = NL.join([
    "project:",
    "  name: t",
    "  status: 已定稿",
    "stories:",
    "- id: S-1",
    "  title: 用户登录",
    "  status: 已完成",
    "- id: S-2",
    "  title: 用户登出",
    "  status: 已完成",
])


def run_viewer(root):
    return subprocess.run(
        [sys.executable, VIEWER, "--project-root", root, "--no-open"],
        capture_output=True, text=True, encoding="utf-8", timeout=60,
    )


class AugmentPanelTests(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        self.out = os.path.join(self.root, "diy-output")
        os.makedirs(self.out)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, content):
        path = os.path.join(self.out, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def render(self):
        p = run_viewer(self.root)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertNotIn("Traceback", p.stderr)
        view = os.path.join(self.out, ".view")
        return (
            open(os.path.join(view, "sprint.html"), encoding="utf-8").read(),
            open(os.path.join(view, "index.html"), encoding="utf-8").read(),
        )

    # trace: 2026-09-13 裁定——fail 任务聚合面板：任务+失败用例+目标缺陷+裁断三途径
    def test_fail_task_renders_panel_with_tc_details(self):
        self.write("sprint.yaml", SPRINT_WITH_FAIL)
        self.write("test-plan.yaml", TEST_PLAN)
        self.write("stories.yaml", STORIES)
        sprint_html, index_html = self.render()
        self.assertIn("补测待裁断", sprint_html, "聚合面板缺失")
        self.assertIn("--reopen-failed", sprint_html, "裁断途径提示缺失")
        self.assertIn("TC-1.1.1", sprint_html, "失败用例未列出")
        self.assertIn("空输入未拦截", sprint_html, "目标缺陷未列出")
        self.assertIn("覆盖率证据：分支未覆盖", sprint_html, "用例证据未列出")
        self.assertIn("用户登录", sprint_html, "任务标题反查缺失")
        self.assertIn("补测待裁断 1", index_html, "索引卡片徽章缺失")

    # trace: 2026-09-13 裁定——augment 三态徽章：中文标签 + 语义色
    def test_augment_badges_rendered(self):
        self.write("sprint.yaml", SPRINT_WITH_FAIL)
        self.write("test-plan.yaml", TEST_PLAN)
        self.write("stories.yaml", STORIES)
        sprint_html, _ = self.render()
        self.assertIn("编码后验证", sprint_html, "augment 字段标签未中文化")
        self.assertIn('class="badge b-bad">失败</span>', sprint_html, "fail 徽章缺失")
        self.assertIn('class="badge b-dim">已跳过</span>', sprint_html, "skip 徽章缺失")

    # trace: 2026-09-13 裁定——无 fail 任务时面板与索引徽章零输出
    def test_no_fail_no_panel_no_badge(self):
        self.write("sprint.yaml", SPRINT_NO_FAIL)
        self.write("test-plan.yaml", TEST_PLAN)
        self.write("stories.yaml", STORIES)
        sprint_html, index_html = self.render()
        self.assertNotIn("补测待裁断", sprint_html, "无 fail 任务仍出现面板")
        self.assertNotIn("补测待裁断", index_html, "无 fail 任务仍出现索引徽章")


class AugmentSkillContractTests(unittest.TestCase):
    """diy-augment 的 SKILL.md 契约冒烟（中文化轮 2026-09-19）。"""

    def read_skill(self):
        with open(SKILL_MD, encoding="utf-8") as f:
            return f.read()

    # trace: 中文化轮（母本 §1/§2/§3/§5/§6 中文定稿逐字；英文原形随中文化退役）
    def test_mother_texts_verbatim(self):
        raw = self.read_skill()
        self.assertIn(INSTANCE_ZH, raw, "缺母本 §1 中文定稿实例解析句")
        self.assertNotIn(INSTANCE_EN_MARK, raw, "已转中文定稿，仍残留 §1 英文原形")
        self.assertIn(RESOLVE_KEYS_ZH, raw, "缺母本 §3 配置解析键（A-3：project. 前缀）")
        self.assertIn(RENDER_SILENT_ZH, raw, "缺母本 §5 渲染静默整句")
        self.assertIn(PRECISE_ZH, raw, "缺母本 §6 精准简练条款")
        self.assertIn(DISCIPLINE_ZH, raw, "缺母本 §2 写作纪律块")

    # trace: 2026-09-19 中文化政策（四段中文标题 + description 中文注释 + ≤93 行预算）
    def test_four_chinese_sections_and_budget(self):
        raw = self.read_skill()
        self.assertLessEqual(len(raw.splitlines()), 93, "薄主文件超出 93 行预算")
        for section in ("## 激活时", "## 工作流", "## 结构", "## 规则"):
            self.assertIn(section, raw, "缺四段结构：%s" % section)
        self.assertIn("# ↑ 中文：", raw, "description 缺中文注释")
        # 无 steps/ —— §4 读取纪律永久不适用（2026-09-19 裁定），不得写成假事实
        self.assertNotIn("Read (input)", raw, "无 steps/ 的技能不得出现 §4 的步骤锚串")

    # trace: B-16 SS-019-03（实现面口径与 diy-review 同句 + static_checks 来源照抄 C1 措辞）
    def test_implementation_surface_and_static_checks_source(self):
        raw = self.read_skill()
        self.assertIn("`{output_dir}/test-plan.yaml` 的 `static_checks` 链", raw,
                      "覆盖率工具链未点名 test-plan.yaml 的 static_checks 链")
        self.assertIn("链的定义源在 `diy-test-design`，此处只引用不重定义", raw,
                      "static_checks 链未声明权威出处")
        self.assertIn("`references[].file` 里引用了本任务 `S-x` 的文件集合", raw,
                      "实现面未写死 trace 回执口径")
        self.assertIn("`git status --porcelain` 里本任务的未跟踪实现文件", raw,
                      "实现面缺未跟踪文件半边")
        self.assertIn("开场一行声明本次采样的实现面", raw, "实现面采样未要求声明")

    # trace: B-16 SS-019-05（mutation 取值路径 + 「未配置」兜底 + 沙箱基线）
    def test_mutation_config_path_fallback_and_sandbox(self):
        raw = self.read_skill()
        self.assertIn("`static_checks[].tool` 中用户确认为变异工具的条目", raw,
                      "mutation 配置载体未点名取值路径")
        self.assertIn("按「未配置」处置", raw, "mutation 缺「未配置」兜底")
        self.assertIn("不写 `mutation-report.yaml`、不设判定", raw, "未配置的处置不完整")
        self.assertIn("本技能不复制工作树", raw, "沙箱基线未声明由命令自建")
        self.assertIn("执行前用 `git status --porcelain` 留基线", raw, "缺沙箱执行前基线")

    # trace: B-16 SS-019-07（覆盖率门槛取值顺序 + AC path 判据）
    def test_coverage_gate_order_and_ac_path(self):
        raw = self.read_skill()
        self.assertIn("门槛顺序：① 用户本次给出的阈值 > ②", raw, "覆盖率门槛取值顺序缺失")
        self.assertIn("③ 都没有 → **不过滤**", raw, "无门槛时的兜底未写死")
        self.assertIn("落在 AC path 上的条目即使低于门槛也保留", raw, "AC path 例外未写")
        self.assertIn("`AC path` ＝ 该未覆盖项位于某条 AC 的 TC `steps` 点名的文件/符号内", raw,
                      "AC path 判据未写死")

    # trace: B-16 SS-019-04（删 waivers 从句 + score 公式自足）
    def test_no_waivers_clause_and_score_formula(self):
        raw = self.read_skill()
        self.assertNotIn("waivers", raw, "仍残留门不存在的 waivers 从句（B10 同法：删）")
        self.assertIn("score = killed / (total − equivalents)", raw, "score 公式缺失")
        self.assertIn("不计入 `score` 分母", raw, "等价体不计入分母的口径缺失")

    # trace: B-16 SS-019-06（零缺口 = 不写用例但判定照落）
    def test_zero_gap_still_leaves_verdict(self):
        raw = self.read_skill()
        self.assertIn("零缺口 → 不写用例、**判定照落**", raw, "零缺口与判定的关系未写死")
        self.assertIn("**零缺口 → 不写用例、只落判定**", raw, "规则段零缺口口径缺失")
        self.assertIn("每轮结束恰落一个 `augment` 值", raw, "判定必落条款缺失")

    # trace: B-16 SS-019-09 + B8 组（证据交接点：下一次 in-progress 周期写 evidence）
    def test_evidence_handoff_point(self):
        raw = self.read_skill()
        self.assertIn("它由**下一次 `进行中` 周期**经 `diyc.py green` 写入", raw,
                      "缺证据交接点（谁在下一次进行中周期写）")
        self.assertIn("该命令只对 `进行中` 任务生效", raw, "evidence 写入的前置状态未写死")
        self.assertIn("唯一写者是 `diy-dev` / `diy-build-loop`", raw, "evidence 写者未点名")
        self.assertIn("`EVIDENCE_MISSING` 是**信号**", raw,
                      "追加件无 evidence 的口径未写成信号（B8 另一半）")
        self.assertIn("不是豁免", raw, "EVIDENCE_MISSING 不得被当豁免未写")

    # trace: B-16 SS-011-04 / A-9（runner 安装形态路径 + 由人手动执行）
    def test_runner_installed_path(self):
        raw = self.read_skill()
        self.assertIn(".claude/skills/diy-tools/scripts/runner.py", raw,
                      "runner 引用未写安装形态路径")
        self.assertIn("--reopen-failed", raw, "缺重开入口")
        self.assertIn("人手动执行", raw, "缺「由人手动执行」注明")

    # trace: B-16 A-8（priority 映射只引用不重定义，权威出处 = diy-test-design）
    def test_priority_mapping_referenced_not_redefined(self):
        raw = self.read_skill()
        self.assertIn("映射（`必须`→P0 / `应该`→P1 / `可选`→P2 / NFR 引用的 AC→P0）", raw,
                      "priority 映射引用不完整")
        self.assertIn("唯一权威出处 = `diy-test-design`，只引用不重定义", raw,
                      "priority 映射未声明只引用不重定义")

    # trace: B-16 A-4（硬门写读哪一层：任务级 status，不是 project.status）
    def test_hard_gate_names_the_field_layer(self):
        raw = self.read_skill()
        self.assertIn("该任务在 `tasks[]` 里的 `status` 必须是 `已完成`", raw,
                      "硬门未写死读取层")
        self.assertIn("`project.status` 是文件水位线，不是本门的读取层", raw,
                      "硬门未排除 project.status 层")


if __name__ == "__main__":
    unittest.main()
