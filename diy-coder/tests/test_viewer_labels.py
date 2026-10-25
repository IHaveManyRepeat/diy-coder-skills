# -*- coding: utf-8 -*-
"""diy-viewer 标签与降级渲染契约测试（C·2，2026-09-21）。

夹具：临时项目 + 覆盖 C·2 四类修复点的产物；断言
  ① 假悬空守卫——REF_KEYS 列表里的非 ID 字符串（技能名）不得标红，真悬空 ID 仍标红
  ② 修订历史——顶层 revisions 渲染为默认折叠的中文「修订历史」块
  ③ 文档类型标签——DOC_LABELS 全表的中文标题（页面 h1 + 索引卡片），键清单从 viewer 导入
  ④ 键标签——B1–B5 新产物键中文化，无英文裸奔
"""
import os
import re
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
VIEWER_PATH = os.path.join(HERE, "..", "skills", "diy-viewer", "scripts", "viewer.py")
sys.path.insert(0, os.path.dirname(os.path.abspath(VIEWER_PATH)))
import viewer  # noqa: E402  仅取 DOC_LABELS 键清单，不执行渲染
from viewer_labels import FREE_TEXT_FIELDS  # noqa: E402

NL = chr(10)

MODULE_PLAN_DOC = NL.join([
    "project:",
    "  name: fx",
    "  created: 2026-09-21",
    "  updated: 2026-09-21",
    "plans:",
    "- id: MP-001",
    "  slug: demo",
    "  title: 演示模块",
    "  status: 草稿",
    "  skills:",
    "  - name: diy-alpha",
    "    kind: 工作流",
    "    brief: 说明",
    "    depends_on: [diy-elicit, diy-beta]",
    "  dependencies: [diy-elicit]",
    "  build_order: [diy-alpha]",
    "revisions: []",
])

BRAINSTORM_DOC = NL.join([
    "project:",
    "  name: fx",
    "  created: 2026-09-21",
    "  updated: 2026-09-21",
    "sessions:",
    "- id: BS-001",
    "  topic: 试探主题",
    "  status: 已完成",
    "revisions:",
    "- date: 2026-09-19",
    "  change: BS-001 标题改名",
    "  reason: 用户要求更短",
])

# 真悬空：prd 的 FR-1.1 存在，story 引用的 FR-9.9 不存在
DANGLING_DOC = NL.join([
    "project:",
    "  name: fx",
    "  status: 已定稿",
    "features:",
    "- id: FG-1",
    "  requirements:",
    "  - id: FR-1.1",
    "    statement: 迷你需求",
    "    priority: 必须",
])
STORIES_DANGLING = NL.join([
    "project:",
    "  name: fx",
    "  status: 草稿",
    "stories:",
    "- id: ST-1",
    "  title: 故事",
    "  refs: [FR-9.9]",
])

# spec-scan 的官方 ID 是三段短横形态（skills/diy-spec-scan/SKILL.md:64），
# is_id_string 的正则认不出它——但它在 ID 索引里，必须先查索引再判形态
SPEC_SCAN_DOC = NL.join([
    "project:",
    "  name: fx",
    "scans:",
    "- id: SS-001-01",
    "  type: 分支无定义",
    "  severity: 阻断",
])
STORIES_REF_SS = NL.join([
    "project:",
    "  name: fx",
    "stories:",
    "- id: ST-1",
    "  refs: [SS-001-01]",
])

# diy-augment 的变异运行记录（schema: diy-augment/SKILL.md:34）——V 验证补漏项
MUTATION_REPORT_DOC = NL.join([
    "project:",
    "  name: fx",
    "  status: 草稿",
    "runs:",
    "- date: 2026-09-21",
    "  task: S-1",
    "  scope: 本任务实现面",
    "  killed: 8",
    "  total: 10",
    "  score: 0.8",
    "  survivors:",
    "  - mutant: 改条件判断",
    "    file: src/a.py",
    "    line: 12",
    "  equivalents: []",
    "revisions: []",
])


class _Fixture(unittest.TestCase):
    """临时工程夹具：output_dir 平铺写入 YAML。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        self.out = os.path.join(self.root, "diy-output")
        os.makedirs(self.out)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, content):
        with open(os.path.join(self.out, name), "w", encoding="utf-8") as f:
            f.write(content)

    def render(self):
        return subprocess.run(
            [sys.executable, VIEWER_PATH, "--project-root", self.root, "--no-open"],
            capture_output=True, text=True, encoding="utf-8", timeout=60)

    def page(self, name):
        return open(os.path.join(self.out, ".view", name + ".html"),
                    encoding="utf-8").read()


class ViewerRefGuardTests(_Fixture):
    # trace: C·2 ① 假悬空守卫——与 collect_dangling 的 is_id_string 守卫对称
    def test_non_id_ref_values_not_marked_dangling(self):
        # module-plan 的 skills[].depends_on 装技能名（diy-*），不是 ID：不得标红
        self.write("module-plan.yaml", MODULE_PLAN_DOC)
        p = self.render()
        self.assertEqual(p.returncode, 0, p.stderr)
        html = self.page("module-plan")
        self.assertNotIn("引用不存在", html, "技能名被误标悬空引用")
        self.assertNotIn('class="dangling"', html, "技能名被误标红字")
        for name in ("diy-elicit", "diy-alpha", "diy-beta"):
            self.assertIn(name, html, "技能名内容丢失：%s" % name)

    def test_registered_nonstandard_id_keeps_full_link(self):
        # V 独立验证阻断项回归：判序必须是「先查索引，再判形态」。若先判形态，SS-001-01 会被
        # 降级成纯文本、再经 linkify 半匹配成指向 SS-001 的错链（锚点错位、整链断裂）
        self.write("spec-scan.yaml", SPEC_SCAN_DOC)
        self.write("stories.yaml", STORIES_REF_SS)
        p = self.render()
        self.assertEqual(p.returncode, 0, p.stderr)
        html = self.page("stories")
        self.assertIn('href="spec-scan.html#SS-001-01"', html, "已登记的非标准 ID 未出整链")
        self.assertNotIn('href="spec-scan.html#SS-001"', html, "半匹配错链（指向 SS-001）")

    def test_real_dangling_id_still_marked(self):
        # 过度修复防线：真悬空 ID 仍须标红 + 顶部告警
        self.write("prd.yaml", DANGLING_DOC)
        self.write("stories.yaml", STORIES_DANGLING)
        p = self.render()
        self.assertEqual(p.returncode, 0, p.stderr)
        html = self.page("stories")
        self.assertIn("引用不存在", html, "真悬空 ID 未标红")
        self.assertIn("FR-9.9", html)
        self.assertIn("悬空引用", html, "顶部悬空告警丢失")


class ViewerRevisionsTests(_Fixture):
    # trace: C·2 ② 迁移计划「修订历史留痕」——默认折叠的修订历史卡片
    def test_revisions_renders_as_folded_block(self):
        self.write("brainstorm.yaml", BRAINSTORM_DOC)
        p = self.render()
        self.assertEqual(p.returncode, 0, p.stderr)
        html = self.page("brainstorm")
        self.assertIn("修订历史", html, "revisions 未映射为「修订历史」")
        self.assertIsNotNone(
            re.search(r"<details[^>]*>\s*<summary>[^<]*修订历史", html),
            "修订历史未落在默认折叠块内")
        # 默认折叠 = details 不带 open 属性
        m = re.search(r"<details([^>]*)>\s*<summary>[^<]*修订历史", html)
        self.assertNotIn("open", m.group(1), "修订历史块默认展开（应折叠）")
        for label in ("日期", "变更", "原因"):
            self.assertIn(label, html, "修订记录键 %s 未中文化" % label)
        self.assertIn("标题改名", html, "修订内容丢失")
        self.assertIn("用户要求更短", html, "修订理由丢失")

    def test_empty_or_absent_revisions_render_no_block(self):
        # 空列表是新建产物的常态：与「段缺失」同样静默，不留「展开修订历史（0 项）」噪音
        self.write("prd.yaml", DANGLING_DOC)
        self.write("module-plan.yaml", MODULE_PLAN_DOC)
        p = self.render()
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertNotIn("修订历史", self.page("prd"), "无 revisions 段却渲染了修订历史块")
        self.assertNotIn("修订历史", self.page("module-plan"),
                         "空 revisions 列表仍渲染了修订历史块")


class ViewerDocLabelTests(_Fixture):
    # trace: C·2 ③ 文档类型标签全表——键清单从 viewer 导入，新增类型自动纳入
    def test_all_doc_types_have_chinese_titles(self):
        names = sorted(viewer.DOC_LABELS)
        self.assertGreaterEqual(len(names), 30, "DOC_LABELS 覆盖数异常偏少")
        for name in names:
            self.write(name + ".yaml", "project:" + NL + "  name: fx" + NL)
        p = self.render()
        self.assertEqual(p.returncode, 0, p.stderr)
        index = open(os.path.join(self.out, ".view", "index.html"),
                     encoding="utf-8").read()
        for name in names:
            html = self.page(name)
            m = re.search(r"<h1>([^<]+)</h1>", html)
            self.assertIsNotNone(m, "%s 页面缺标题" % name)
            title = m.group(1)
            # 判据是「未回落英文原名」而非「零 ASCII」——PRFAQ / SPEC 属方法论专名，按项目
            # 口径逐字保留（同机器锚点），中文化要求的是标题可读而非消灭全部字母
            self.assertTrue(any(ord(c) > 0x2E80 for c in title),
                            "%s 标题非中文：%s" % (name, title))
            self.assertNotEqual(title, name,
                                "%s 标题回落英文原名（DOC_LABELS 未映射）" % name)
            seg = index.split('href="%s.html"' % name, 1)[1][:160]
            self.assertTrue(any(ord(c) > 0x2E80 for c in seg),
                            "%s 索引卡片非中文" % name)


class ViewerKeyLabelTests(_Fixture):
    # trace: C·2 ④ B1–B5 新产物键中文化——英文键名直出回归防线
    def test_new_artifact_keys_are_chinese(self):
        self.write("module-plan.yaml", MODULE_PLAN_DOC)
        self.write("brainstorm.yaml", BRAINSTORM_DOC)
        p = self.render()
        self.assertEqual(p.returncode, 0, p.stderr)
        plan = self.page("module-plan")
        for leak in (">plans<", ">slug<", ">vision<", ">kind<", ">brief<",
                     ">dropped<", ">build_order<"):
            self.assertNotIn(leak, plan, "module-plan 英文键名直出：%s" % leak)
        bs = self.page("brainstorm")
        for leak in (">sessions<", ">topic<"):
            self.assertNotIn(leak, bs, "brainstorm 英文键名直出：%s" % leak)

    def test_mutation_report_page_is_chinese(self):
        # V 独立验证补漏项回归（此前整页英文裸奔，且类型名回落文件名）
        self.write("mutation-report.yaml", MUTATION_REPORT_DOC)
        p = self.render()
        self.assertEqual(p.returncode, 0, p.stderr)
        html = self.page("mutation-report")
        self.assertIn("<h1>变异测试报告</h1>", html, "mutation-report 标题未映射")
        for label in ("运行记录", "杀死数", "幸存变异体", "等价变异体", "变异体"):
            self.assertIn(label, html, "mutation-report 键 %s 未映射" % label)
        for leak in (">runs<", ">killed<", ">survivors<", ">equivalents<", ">mutant<"):
            self.assertNotIn(leak, html, "mutation-report 英文键名直出：%s" % leak)


# ---------------------------------------------------------------------------
# C·11 W3（§5.1 标签缺口 / §5.2 链接档 + 诊断档）
# ---------------------------------------------------------------------------

WDS_ASSETS_DOC = NL.join([
    "project:",
    "  name: fx",
    "  status: 已定稿",
    "stage: 收尾",
    "activities:",
    "- id: AS-01",
    "  code: W",
    "  name: 线框",
    "  status: 已评审",
    "  items:",
    "  - id: AS-01.1",
    "    title: 首页线框",
    "    prompt: 画一张首页线框",
    "    prompt_lang: zh",
    "    scope: all",
    "    assets:",
    "    - {path: assets/wireframes/home-desktop.html, format: html}",
    "    review: {checks: [布局清晰], verdict: 通过}",
    "  - id: AS-01.2",
    "    title: 二次线框",
    "    prompt: another",
    "    prompt_lang: en",
    "    scope: missing",
    "    assets:",
    "    - {path: assets/wireframes/gone.html, format: html}",
    "    review: {checks: [], verdict: 重生}",
    "  - id: AS-01.3",
    "    title: 批量件",
    "    prompt: batch prompt",
    "    prompt_lang: zh",
    "    scope: batch",
    "    assets:",
    "    - {path: assets/wireframes/batch.png, format: png}",
    "    review: {checks: [], verdict: 待定}",
    "- id: AS-08",
    "  code: S",
    "  name: 演示",
    "  status: 已评审",
    "  scope: all",
    "  style: {design: null, content: null, format: sd-slides}",
    "  items:",
    "  - id: AS-08.1",
    "    name: 演示 主件",
    "    prompt: 生成一张演示",
    "    prompt_lang: zh",
    "    assets:",
    "    - {path: assets/presentation/deck.html, format: html}",
    "    review: {checks: [], verdict: 通过}",
    "prompts:",
    "- {id: AS-01.1, activity: AS-01, target: 外部服务,",
    "   file: assets/wireframes/prompts/home-desktop.md, exported: true}",
    "presentation:",
    "- id: AS-08.1",
    "  recipe: SD",
    "  audience: 投资人",
    "  format_card: data/presentation-formats/sd-slides.md",
    "  frames:",
    "  - {n: 1, job: inform, headline: 标题, notes: 备注}",
    "  assets:",
    "  - {path: assets/presentation/deck.html, format: html}",
    "  review: {principles: [视觉层级], verdict: 待定}",
])

WDS_SYSTEM_DOC = NL.join([
    "project:",
    "  name: fx",
    "  status: 已定稿",
    "design_system_mode: 'on'",
    "tokens:",
    "  source: {file: design.yaml, path: tokens, mode: 派生}",
    "  namespaces: {color: [brand], spacing: [sm], typography: [body]}",
    "categories: [Interactive, Form, Layout, Content, Feedback, Navigation]",
    "prefixes:",
    "- {type: Button, prefix: btn, category: Interactive}",
    "- {type: Form, prefix: frm, category: Form}",
    "components:",
    "- id: btn-001",
    "  name: Button",
    "  prefix: btn",
    "  category: Interactive",
    "  complexity: complex",
    "  status: 在用",
    "  variants: [primary]",
    "  states: [{name: 默认, signals: [图标]}]",
    "  styling: {visual_properties: {bg: '#fff'}, layout: {}, library_component: null}",
    "  behavior: {interactions: [点击], animations: [淡入], rules: []}",
    "  accessibility: {aria: aria-label, keyboard: [Enter], screen_reader: 读作按钮}",
    "  usage: {when_to_use: 主操作, when_not_to_use: [次要操作], best_practices: [一屏一个]}",
    "  used_in: [SC-01.P1]",
    "  token_refs: [color.brand]",
    "  related: []",
    "  version: {created: 2026-09-23, updated: 2026-09-23, changes: 1}",
    "  notes: null",
    "- id: btn-002",
    "  name: Button ghost",
    "  prefix: btn",
    "  category: Interactive",
    "  complexity: moderate",
    "  status: 已废弃",
    "  variants: [ghost]",
    "  states: []",
    "  styling: {}",
    "  behavior: {}",
    "  accessibility: {}",
    "  usage: {}",
    "  used_in: []",
    "  token_refs: []",
    "  related: []",
    "  version: {}",
    "  notes: null",
])

WDS_EVOLUTION_DOC = NL.join([
    "project:",
    "  name: fx",
    "  status: 已定稿",
    "kaizen_priority:",
    "  formula: 'Priority = Impact x Effort x Learning'",
    "  candidates:",
    "  - {target: 提速, impact: high, effort: low, learning: medium, score: 0.9}",
    "rounds:",
    "- id: EV-01",
    "  target: 提速",
    "  status: 已交付",
    "  entry: 存量接入",
    "  analysis: {snapshot: 现状, root_cause: 慢查询, hypothesis: 加索引}",
    "  scope: {target: 提速, risk: Low, data_changes: 无}",
    "  design: {approach: quick-fix, change_summary: 加索引}",
    "  implement: {branch: feat/x, files: [src/a.py]}",
    "  test:",
    "    scope: 本轮增量",
    "    criteria:",
    "    - {kind: HP, criterion: P95, how: 压测, expected: 1, actual: 0.5, verdict: 通过}",
    "    - {kind: EC, criterion: 空输入, how: 手工, expected: 不崩, actual: 崩了, verdict: 未通过}",
    "  delivery:",
    "    summary: 完成",
    "    artifacts: {analysis: ok, scope: ok, design: ok, implement: ok, test: ok, pr: PR-1}",
    "    monitoring: {metrics: [P95], period: 一周}",
])

ANALYSIS_DOC = NL.join([
    "project:",
    "  name: fx",
    "  status: 已定稿",
    "question: {text: 鉴权怎么组织, scope: 认证与会话, output_format: 架构图, time_box: 30 分钟}",
    "architecture:",
    "  summary: 分层应用",
    "  tech_stack: [Python]",
    "  overview: 三层",
    "  mermaid: 'graph TD'",
    "  layers: [展示层, 应用层, 领域层, 基础设施层, 未分层]",
    "components:",
    "- {id: AN-01, name: Auth, layer: 领域层, responsibility: 登录, location: src/auth, status: 已核实}",
    "- {id: AN-02, name: DB, layer: 基础设施层, responsibility: 存储, location: src/db, status: 待核实}",
    "data_flow:",
    "- {name: 登录流, steps: [表单, 校验], components: [AN-01]}",
    "dependencies:",
    "- {from: AN-01, to: AN-02, type: 外部库, note: 取会话}",
    "risks:",
    "- {risk: 无校验, severity: 高, location: src/routes, impact: 漏洞}",
    "recommendations:",
    "- {action: 补校验, priority: 高, effort: 2 小时, target: src/routes}",
])

# 同键异义的旁证产物：这些键在本文档里不是枚举（值不进值表也**不得**报诊断）
SAME_KEY_DOCS = {
    # diyc-baseline：code 是违规码（全局标签），不是活动码
    "diyc-baseline": NL.join([
        "project:", "  name: fx", "  status: 已定稿",
        "baseline: {created: 2026-09-23}",
        "waivers:",
        "- {id: WV-1, code: MISSING_FILE, where: diy-output/sprint.yaml, by: 我, on: 2026-09-23}",
    ]),
    # mutation-report（diy-augment）：scope 是本次采样的实现面
    "mutation-report": NL.join([
        "project:", "  name: fx", "  status: 已定稿",
        "runs:",
        "- {date: 2026-09-23, task: S-1, scope: 本任务实现面, killed: 8, total: 10, score: 0.8}",
    ]),
    # prfaq：stage 是 1..5 的续跑锚点
    "prfaq": NL.join([
        "project:", "  name: fx", "  status: 草稿",
        "stage: 3",
        "press_release: 稿子",
    ]),
    # wds-brief：stage 是另一套中文锚点（与 wds-assets 的九值不同源）
    "wds-brief": NL.join([
        "project:", "  name: fx", "  status: 草稿",
        "intake: {project_type: greenfield, complexity: standard, brief_level: complete,",
        "         strategic_analysis: full, stage: 分诊}",
    ]),
    # wds-trigger：mode 是 W/S/D、entry 是 工作坊|既有产物、stage 是第三套中文锚点
    "wds-trigger": NL.join([
        "project:", "  name: fx", "  status: 草稿",
        "stage: 目标",
        "mode: W",
        "entry: 工作坊",
    ]),
    # wds-scenarios：entry 是 Q6 的自由文本答案
    "wds-scenarios": NL.join([
        "project:", "  name: fx", "  status: 已定稿",
        "scenarios:",
        "- {id: SC-01, name: 场景, entry: 用户从首页进入下单}",
    ]),
    # readiness / research / wds-evolution：scope 都不是枚举
    "readiness": NL.join([
        "project:", "  name: fx", "  status: 已定稿",
        "checks:",
        "- {no: 1, scope: [prd, architecture], verdict: 就绪}",
    ]),
    "research": NL.join([
        "project:", "  name: fx", "  status: 已定稿",
        "topic: 领域调研",
        "scope: 竞品与市场，不含定价",
    ]),
}


class ViewerB7bLabelTests(_Fixture):
    # trace: C·11 W3 §5.1——B7b 五产物的文档名 / 键名 / 值名三张标签表补齐
    def test_new_doc_types_have_chinese_titles(self):
        for name, label in (("wds-design-system", "设计系统"), ("wds-assets", "资产工厂"),
                            ("wds-evolution", "Kaizen 迭代"), ("analysis", "单问架构分析")):
            self.write(name + ".yaml", "project:" + NL + "  name: fx" + NL)
        p = self.render()
        self.assertEqual(p.returncode, 0, p.stderr)
        index = open(os.path.join(self.out, ".view", "index.html"), encoding="utf-8").read()
        for name, label in (("wds-design-system", "设计系统"), ("wds-assets", "资产工厂"),
                            ("wds-evolution", "Kaizen 迭代"), ("analysis", "单问架构分析")):
            self.assertIn("<h1>%s</h1>" % label, self.page(name),
                          "%s 页面标题未映射为 %s" % (name, label))
            self.assertIn(label, index.split('href="%s.html"' % name, 1)[1][:160],
                          "%s 索引卡片未映射为 %s" % (name, label))

    def test_b7b_artifact_keys_are_chinese(self):
        self.write("wds-design-system.yaml", WDS_SYSTEM_DOC)
        self.write("wds-assets.yaml", WDS_ASSETS_DOC)
        self.write("wds-evolution.yaml", WDS_EVOLUTION_DOC)
        self.write("analysis.yaml", ANALYSIS_DOC)
        p = self.render()
        self.assertEqual(p.returncode, 0, p.stderr)
        for name, leaks in (
            ("wds-design-system", (">accessibility<", ">behavior<", ">styling<", ">variants<",
                                   ">prefixes<", ">token_refs<", ">used_in<", ">when_to_use<",
                                   ">design_system_mode<", ">complexity<", ">related<")),
            ("wds-assets", (">activities<", ">assets<", ">format<", ">format_card<", ">frames<",
                            ">job<", ">n<", ">presentation<", ">principles<", ">prompts<",
                            ">recipe<", ">style<", ">prompt_lang<", ">stage<")),
            ("wds-evolution", (">analysis<", ">candidates<", ">criteria<", ">delivery<",
                               ">entry<", ">formula<", ">implement<", ">learning<",
                               ">kaizen_priority<", ">pr<")),
            ("analysis", (">codebase<", ">data_flow<", ">layers<", ">location<", ">mermaid<",
                          ">overview<", ">tech_stack<", ">time_box<")),
        ):
            html = self.page(name)
            for leak in leaks:
                self.assertNotIn(leak, html, "%s 英文键名直出：%s" % (name, leak))

    def test_every_enum_key_has_a_chinese_key_label(self):
        # 枚举键缺键标签 → 键名裸出 + 每次渲染报一行 `unmapped enum: <键名>`（§5.1 实测症状）
        labelled = set(viewer.KEY_LABELS)
        for doc in viewer.DOC_KEY_LABELS.values():
            labelled.update(doc)
        self.assertEqual(sorted(k for k in viewer.ENUM_KEYS if k not in labelled), [],
                         "ENUM_KEYS 里有键没有中文键标签")

    def test_new_enum_keys_and_values_are_badged(self):
        # 键进 ENUM_KEYS + 值进值表 → 徽章在场（此前一律回落纯文本）
        self.write("wds-design-system.yaml", WDS_SYSTEM_DOC)
        self.write("wds-assets.yaml", WDS_ASSETS_DOC)
        self.write("wds-evolution.yaml", WDS_EVOLUTION_DOC)
        self.write("analysis.yaml", ANALYSIS_DOC)
        p = self.render()
        self.assertEqual(p.returncode, 0, p.stderr)
        cases = (
            ("wds-design-system", ("在用", "已废弃", "复杂", "中等", "交互", "派生")),
            # 收口后裁定（M2）补三值：scope 的 batch / format 的 png / style.format 的配方卡名
            ("wds-assets", ("已评审", "重生", "全部", "缺失项", "收尾", "中文",
                            "批量", "png", "多页幻灯片")),
            ("wds-evolution", ("已交付", "存量接入", "未通过")),
            ("analysis", ("领域层", "基础设施层", "已核实", "待核实", "外部库")),
        )
        for name, values in cases:
            html = self.page(name)
            for v in values:
                self.assertIn('class="badge b-neutral">%s</span>' % v, html,
                              "%s 的值 %s 未出徽章" % (name, v))
        # 键标签（非枚举键的值不出徽章，但标签必须中文化）
        evo = self.page("wds-evolution")
        for label in ("Kaizen 优先级", "优先级公式", "候选清单", "判据清单", "学习因子", "变更请求"):
            self.assertIn(label, evo, "wds-evolution 键 %s 未映射" % label)

    def test_strict_enum_keys_report_no_drift_after_table_fill(self):
        # 改表前这五份产物共刷 13 行 unmapped enum；补表后一个字都不许再报
        for name, doc in (("wds-design-system", WDS_SYSTEM_DOC), ("wds-assets", WDS_ASSETS_DOC),
                          ("wds-evolution", WDS_EVOLUTION_DOC), ("analysis", ANALYSIS_DOC)):
            self.write(name + ".yaml", doc)
        p = self.render()
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertNotIn("unmapped enum", p.stderr, "补表后仍报枚举漂移：%s" % p.stderr)

    def test_code_label_is_doc_scoped(self):
        # code 同键异义：wds-assets 是活动码、diyc-baseline 仍是违规码（全局键不动）。
        # 断言只看本文档正文——页尾的 ID 详情模板含跨文档内容
        self.write("wds-assets.yaml", WDS_ASSETS_DOC)
        self.write("diyc-baseline.yaml", SAME_KEY_DOCS["diyc-baseline"])
        p = self.render()
        self.assertEqual(p.returncode, 0, p.stderr)
        assets_body = self.page("wds-assets").split("</main>")[0]
        self.assertIn("<th>活动码</th>", assets_body)
        self.assertNotIn("违规码", assets_body)
        self.assertIn("违规码", self.page("diyc-baseline").split("</main>")[0])

    def test_same_key_different_meaning_reports_no_drift(self):
        # trace: §5.1 FREE_TEXT_FIELDS 连带——新增枚举键在别处装非枚举内容，不得灌诊断
        for name, doc in SAME_KEY_DOCS.items():
            self.write(name + ".yaml", doc)
        p = self.render()
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertNotIn("unmapped enum", p.stderr, "同键异义被误报枚举漂移：%s" % p.stderr)

    def test_prefixes_type_is_not_an_enum_in_design_system(self):
        # trace: R-02——prefixes[].type 装 26 个组件类型名（Button…Spacer），不是枚举
        self.write("wds-design-system.yaml", WDS_SYSTEM_DOC)
        p = self.render()
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertNotIn("unmapped enum", p.stderr, "组件类型名被误报枚举漂移")
        html = self.page("wds-design-system")
        self.assertIn("Button", html, "类型名内容丢失")
        # 前缀表内：类型列必须是裸文本（回落 cell()）；若被当枚举，值会换成徽章里的「表单」
        seg = html.split("</main>")[0].split('<h2 id="prefixes">', 1)[1].split("<h2", 1)[0]
        for type_name in ("Button", "Form"):
            self.assertIn(">%s</td>" % type_name, seg,
                          "类型名 %s 被徽章化（应回落纯文本）" % type_name)


class ViewerAssetLinkTests(_Fixture):
    # trace: C·11 W3 §5.2 链接档（裁定 11）——assets[].path 出相对链接且真能到达目标文件
    def write_asset(self, rel, body="<html>ok</html>"):
        path = os.path.join(self.out, *rel.split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(body)
        return path

    def test_asset_path_renders_relative_link_that_reaches_the_file(self):
        target = self.write_asset("assets/wireframes/home-desktop.html")
        deck = self.write_asset("assets/presentation/deck.html")
        self.write("wds-assets.yaml", WDS_ASSETS_DOC)
        p = self.render()
        self.assertEqual(p.returncode, 0, p.stderr)
        html = self.page("wds-assets")
        for rel in ("assets/wireframes/home-desktop.html", "assets/presentation/deck.html"):
            self.assertIn(f'href="../{rel}"', html, "资产路径未出相对链接：%s" % rel)
        # 判据不是「href 文案对」，是「从页面出发真能到达该文件」——按页面所在目录解析 href
        page_dir = os.path.dirname(os.path.join(self.out, ".view", "wds-assets.html"))
        for rel, want in (("assets/wireframes/home-desktop.html", target),
                          ("assets/presentation/deck.html", deck)):
            got = os.path.normpath(os.path.join(page_dir, "..", rel))
            self.assertEqual(got, os.path.normpath(want),
                             "链接落点不是真实文件：%s" % rel)
            self.assertTrue(os.path.isfile(got), "链接目标不存在：%s" % got)

    def test_non_asset_path_stays_plain_text(self):
        # 同键 path 在别的产物是路由/路径，不得被链接化（不造死链）
        self.write("wds-assets.yaml", WDS_ASSETS_DOC)
        self.write("spec-scan.yaml", NL.join([
            "project:", "  name: fx", "  status: 草稿",
            "scans:",
            "- {id: SS-001-01, type: 分支无定义, severity: 阻断,",
            "   target: src/a.py, files: 3, lines: 10}",
        ]))
        p = self.render()
        self.assertEqual(p.returncode, 0, p.stderr)
        # 只看 spec-scan 本文档正文的单元格：`src/a.py` 是扫描目标，不是资产路径
        body = self.page("spec-scan").split("</main>")[0]
        self.assertIn("src/a.py", body)
        self.assertNotIn('href="../src/a.py"', body, "非资产路径被链接化")


class ViewerAssetsNoteTests(_Fixture):
    # trace: C·11 W3 §5.2 诊断档（裁定 12）——assets/ 有内容 → 一行 stderr；无内容 → 静默
    def test_note_when_assets_dir_has_files(self):
        path = os.path.join(self.out, "assets", "wireframes")
        os.makedirs(path)
        with open(os.path.join(path, "home.html"), "w", encoding="utf-8") as f:
            f.write("<html>ok</html>")
        self.write("wds-assets.yaml", WDS_ASSETS_DOC)
        p = self.render()
        self.assertEqual(p.returncode, 0, p.stderr)  # 诊断不改 rc
        notes = [ln for ln in p.stderr.splitlines() if "assets" in ln]
        self.assertEqual(len(notes), 1, "诊断不是一行：%r" % p.stderr)
        # C·12 收口订正（用户裁定 A）：清单页落地后「未渲染」成假事实，锚改「已列入清单页」
        self.assertIn("已列入清单页", notes[0])
        self.assertIn("点开查看", notes[0])

    def test_no_note_when_assets_dir_absent_or_empty(self):
        self.write("wds-assets.yaml", WDS_ASSETS_DOC)
        p = self.render()
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertNotIn("已列入清单页", p.stderr, "无 assets/ 却报了资产诊断")
        os.makedirs(os.path.join(self.out, "assets", "wireframes"))
        p2 = self.render()
        self.assertEqual(p2.returncode, 0, p2.stderr)
        self.assertNotIn("已列入清单页", p2.stderr, "空 assets/ 却报了资产诊断")


# ---------------------------------------------------------------------------
# C·3a 收口链④（§2.3：新增键 3 个 + 从属字段 1 个 · 页状态 5 值）
# ---------------------------------------------------------------------------

# design.yaml 的增量面：token_scope / open_questions（形状同 prd）/ pages[].status 5 值 +
# 仅 已移除 时写的 removed_reason。改前实测：4 行 `unmapped enum`（结构稿中 / 待验收 /
# 已移除 / 已解决）+ 两个键名英文直出（token_scope / removed_reason）。
DESIGN_C3A_DOC = NL.join([
    "project:",
    "  name: fx",
    "  status: 草稿",
    "  created: 2026-09-28",
    "  updated: 2026-09-28",
    "direction: 一句话方向",
    "frontend_framework: react",
    "tokens:",
    "  color: {bg: '#fff', surface: '#eee', text: '#111', text_muted: '#666',",
    "          accent: '#06f', accent_text: '#fff'}",
    "  spacing: {unit: 4, scale: [4, 8]}",
    "  typography: {family_base: Inter, family_heading: Inter, scale: [12, 16]}",
    "token_scope: [src/thirdparty]",
    "open_questions:",
    "- {id: Q-1, question: 用哪种导航, status: 待办}",
    "- {id: Q-2, question: 主色是否换, status: 已解决, answer: 不换}",
    "pages:",
    "- id: P-1",
    "  name: 首页",
    "  route: /",
    "  status: 未开始",
    "  states:",
    "  - {name: 悬停, signals: [图标]}",
    "- id: P-2",
    "  name: 列表",
    "  route: /list",
    "  status: 结构稿中",
    "  states:",
    "  - {name: 悬停, signals: [图标]}",
    "- id: P-3",
    "  name: 详情",
    "  route: /detail",
    "  status: 待验收",
    "  states:",
    "  - {name: 悬停, signals: [图标]}",
    "- id: P-4",
    "  name: 设置",
    "  route: /settings",
    "  status: 已批准",
    "  states:",
    "  - {name: 悬停, signals: [图标]}",
    "- id: P-5",
    "  name: 旧页",
    "  route: /old",
    "  status: 已移除",
    "  removed_reason: 被 v2 首页取代",
    "  states:",
    "  - {name: 悬停, signals: [图标]}",
    "revisions: []",
])


class ViewerC3aDesignLabelTests(_Fixture):
    # trace: C·3a 收口链④——design.yaml 增量面的徽章与键标签（改前：4 行假诊断 + 2 键裸出）
    def test_page_and_question_statuses_are_badged_without_drift(self):
        self.write("design.yaml", DESIGN_C3A_DOC)
        p = self.render()
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertNotIn("unmapped enum", p.stderr, "增量值仍报枚举漂移：%s" % p.stderr)
        html = self.page("design")
        # 5 页状态 + open_questions[].status 的两值；未开始 / 已批准 / 待办 为既有映射，一并钉住
        for value, cls in (("未开始", "dim"), ("结构稿中", "warn"), ("待验收", "warn"),
                           ("已批准", "ok"), ("已移除", "dim"),
                           ("待办", "dim"), ("已解决", "ok")):
            self.assertIn('class="badge b-%s">%s</span>' % (cls, value), html,
                          "值 %s 未按 %s 档出徽章" % (value, cls))

    def test_c3a_new_keys_are_chinese_and_reason_stays_plain(self):
        self.write("design.yaml", DESIGN_C3A_DOC)
        p = self.render()
        self.assertEqual(p.returncode, 0, p.stderr)
        html = self.page("design")
        for label in ("令牌豁免路径", "移除原因", "待决问题"):
            self.assertIn(label, html, "键标签缺失：%s" % label)
        for leak in (">token_scope<", ">removed_reason<"):
            self.assertNotIn(leak, html, "英文键名直出：%s" % leak)
        # removed_reason 是自由文本（不进 ENUM_KEYS）：原句在场，且不得被徽章化
        self.assertIn("被 v2 首页取代", html, "移除原因内容丢失")
        self.assertNotIn(">被 v2 首页取代</span>", html, "自由文本被误徽章化")


# ---------------------------------------------------------------------------
# C·12 W2（裁定 C12-2：渲染通道修复 + 两键标签；Layer 1 增补：决策时间轴页）
# ---------------------------------------------------------------------------

# 双模 design 夹具：form_factor / modes 两键（值照任务书 §0 表）+ tokens.color.dark
# 六角色（§7-5① 明暗对形状）+ 带 ID 形态路径的 prototype / implementation（§7.3 第 2 条场景）
DESIGN_C12_DOC = NL.join([
    "project:",
    "  name: fx",
    "  status: 草稿",
    "form_factor: 响应式 Web",
    "modes: 双模",
    "tokens:",
    "  color:",
    "    bg: '#f6f8fa'",
    "    surface: '#ffffff'",
    "    text: '#1a2333'",
    "    text_muted: '#6b7280'",
    "    accent: '#1d4ed8'",
    "    accent_text: '#ffffff'",
    "    dark:",
    "      bg: '#0b1220'",
    "      surface: '#111a2c'",
    "      text: '#e6ecf5'",
    "      text_muted: '#8a93a5'",
    "      accent: '#5b8cff'",
    "      accent_text: '#0b1220'",
    "pages:",
    "- id: P-1",
    "  name: 首页",
    "  route: /",
    "  status: 未开始",
    "  prototype: prototypes/P-1.html",
    "- id: P-2",
    "  name: 列表",
    "  route: /list",
    "  status: 未开始",
    "  implementation: src/pages/list.tsx",
    "- id: P-3",
    "  name: 详情",
    "  route: /detail",
    "  status: 未开始",
    "  prototype: prototypes/P-3.html",
    "revisions:",
    "- date: 2026-10-01",
    "  change: 首页结构稿落位",
    "  reason: 首页先行",
])


class ViewerC12DesignLabelTests(_Fixture):
    # trace: C·12 W2（裁定 C12-1/C12-2 ③）——两键标签 + 值标签 + dark 子块零裸键
    def test_form_factor_and_modes_labels_and_badges(self):
        self.write("design.yaml", DESIGN_C12_DOC)
        p = self.render()
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertNotIn("unmapped enum", p.stderr, "两键值仍报枚举漂移：%s" % p.stderr)
        html = self.page("design")
        for label in ("目标形态", "主题模式"):
            self.assertIn(label, html, "键标签缺失：%s" % label)
        for leak in (">form_factor<", ">modes<"):
            self.assertNotIn(leak, html, "英文键名直出：%s" % leak)
        for value in ("响应式 Web", "双模"):
            self.assertIn('class="badge b-neutral">%s</span>' % value, html,
                          "值 %s 未出中性徽章" % value)

    def test_form_factor_and_modes_value_tables_complete(self):
        # §0 表逐字：四值/三值全在值表（「移动端」为 R3 既有值，一并钉住），
        # 且不进 BADGE_CLASSES（归类语义 → 中性徽章，同 2026-09-19 口径）
        for value in ("响应式 Web", "移动端", "桌面", "多端", "亮", "暗", "双模"):
            self.assertIn(value, viewer.VALUE_LABELS, "值标签缺失：%s" % value)
            self.assertNotIn(value, viewer.BADGE_CLASSES, "归类值不得带极性：%s" % value)

    def test_dark_subblock_all_seven_keys_are_chinese(self):
        # ★零裸键纪律（2026-10-01 用户裁定收严）：dark 自身 + 六角色七键全部中文标签，
        # 裸英文键名零在场——漏登记 = 显示缺陷而非可接受态
        self.write("design.yaml", DESIGN_C12_DOC)
        p = self.render()
        self.assertEqual(p.returncode, 0, p.stderr)
        html = self.page("design")
        for label in ("暗色", "背景", "表面", "文字", "次要文字", "强调色", "强调色文字"):
            self.assertIn(label, html, "dark 子块键标签缺失：%s" % label)
        for leak in (">dark<", ">bg<", ">surface<", ">text<", ">text_muted<",
                     ">accent<", ">accent_text<"):
            self.assertNotIn(leak, html, "dark 子块英文键名直出：%s" % leak)
        # 暗色 hex 值不因渲染丢失（six 角色在场即可证）
        self.assertIn("#0b1220", html, "暗色 token 值丢失")


class ViewerC12PathLinkTests(_Fixture):
    # trace: C·12 W2（裁定 C12-2 ②）——prototype/implementation 链接化 + 跳过 ID linkify
    def write_output_file(self, rel, body="x"):
        path = os.path.join(self.out, *rel.split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(body)
        return path

    def test_existing_files_render_as_relative_links(self):
        proto = self.write_output_file("prototypes/P-1.html", "<html>P1</html>")
        impl = self.write_output_file("src/pages/list.tsx", "export {}")
        self.write("design.yaml", DESIGN_C12_DOC)
        p = self.render()
        self.assertEqual(p.returncode, 0, p.stderr)
        html = self.page("design")
        # §7.3 第 2 条场景回归：prototypes/P-1.html 渲染为文件相对链接
        self.assertIn('href="../prototypes/P-1.html"', html, "prototype 未出文件直链")
        self.assertIn('href="../src/pages/list.tsx"', html, "implementation 未出文件直链")
        self.assertIn(">prototypes/P-1.html</a>", html, "prototype 链接文本不完整（截断）")
        # 无 ID 截断：不得出现 prototypes/<a…（腰斩）与指向页锚的错链
        self.assertNotIn("prototypes/<a", html, "prototype 被 ID 链接腰斩（§7.3 第 2 条回归）")
        # 链接落点真实存在（从页面目录出发解析 href）
        page_dir = os.path.dirname(os.path.join(self.out, ".view", "design.html"))
        for rel, want in (("prototypes/P-1.html", proto), ("src/pages/list.tsx", impl)):
            got = os.path.normpath(os.path.join(page_dir, "..", rel))
            self.assertTrue(os.path.isfile(got), "链接落点不是真实文件：%s" % got)
            self.assertEqual(got, os.path.normpath(want), "链接落点错位：%s" % rel)

    def test_missing_file_path_stays_plain_without_id_truncation(self):
        # prototypes/P-3.html 在产物里但文件不存在 → 纯文本，且仍不得被 linkify 截断
        self.write("design.yaml", DESIGN_C12_DOC)
        p = self.render()
        self.assertEqual(p.returncode, 0, p.stderr)
        html = self.page("design")
        self.assertIn("prototypes/P-3.html", html, "路径文本丢失")
        self.assertNotIn("prototypes/<a", html, "不存在的文件路径仍被 ID 链接腰斩")
        self.assertNotIn('href="../prototypes/P-3.html"', html, "不存在的文件被造成死链")

    def test_absolute_and_url_paths_stay_plain(self):
        doc = NL.join([
            "project:", "  name: fx", "  status: 草稿",
            "form_factor: 桌面", "modes: 亮",
            "pages:",
            "- id: P-1",
            "  name: 首页",
            "  prototype: https://example.com/P-1.html",
            "- id: P-2",
            "  name: 列表",
            "  implementation: /abs/P-2.tsx",
        ])
        self.write("design.yaml", doc)
        p = self.render()
        self.assertEqual(p.returncode, 0, p.stderr)
        html = self.page("design")
        self.assertNotIn('href="https://example.com', html, "URL 值被链接化")
        self.assertNotIn('href="/abs/', html, "绝对路径被链接化")
        self.assertNotIn("example.com/<a", html, "URL 中的 ID 形态被腰斩")
        # 顺带钉住：桌面 / 亮 两值照常出徽章（§0 表另两值）
        self.assertIn('class="badge b-neutral">桌面</span>', html)
        self.assertIn('class="badge b-neutral">亮</span>', html)


# ---------------------------------------------------------------------------
# 批 5b（cm_refs——design.yaml 顶层引用位：中文标签 + REF_KEYS 悬空标红）
# ---------------------------------------------------------------------------

DESIGN_CM_REFS_DOC = NL.join([
    "project:",
    "  name: fx",
    "  status: 草稿",
    "direction: 一句话方向",
    "frontend_framework: html",
    "cm_refs: [CM-001, CM-999]",
    "pages:",
    "- id: P-1",
    "  name: 首页",
    "  route: /",
    "  states:",
    "  - {name: 悬停, signals: [图标]}",
    "revisions: []",
])


class ViewerCmRefsTests(_Fixture):
    # trace: 批 5b 1a/1c（cm_refs 中文标签零裸键 + 入 REF_KEYS——CM-001 可解析出链接、
    #        CM-999 悬空标红；CM-### 被 ID_FULL_RE 天然覆盖，零新逻辑）
    def test_cm_refs_labelled_and_dangling_marked(self):
        self.write("design.yaml", DESIGN_CM_REFS_DOC)
        self.write("cis-method.yaml", NL.join([
            "project:",
            "  name: fx",
            "sessions:",
            "- id: CM-001",
            "  method: 设计思维",
            "  topic: 探索导航",
            "  date: 2026-10-25",
            "  status: 已完成",
            "  current_step: 7",
            "revisions: []",
        ]))
        p = self.render()
        self.assertEqual(p.returncode, 0, p.stderr)
        html = self.page("design")
        self.assertIn("设计思维引用", html, "cm_refs 中文标签缺失")
        self.assertNotIn(">cm_refs<", html, "cm_refs 英文键名直出")
        # 可解析：CM-001 链到 cis-method 页
        self.assertIn('href="cis-method.html#CM-001"', html, "cm_refs 已解析 ID 未出链接")
        # 悬空：CM-999 标红（同 design_ref 款）
        self.assertIn("引用不存在", html, "cm_refs 悬空未标红")
        self.assertIn("CM-999", html)


class ViewerC12AssetsPageTests(_Fixture):
    # trace: C·12 W2（裁定 C12-2 ①）——assets 产物清单页：按活动分组 + 相对路径直链
    NINE_DOCS = ("prd", "architecture", "epics", "stories", "test-plan", "design",
                 "wds-brief", "wds-assets", "wds-design-system")

    def write_asset_file(self, rel):
        path = os.path.join(self.out, *rel.split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write("<html>ok</html>")
        return path

    def test_assets_page_groups_by_activity_with_direct_links(self):
        # 夹具产物树：9 产物 + assets/ 多活动子目录（裁定原文「8 活动全盲」的回归面）
        for name in self.NINE_DOCS:
            self.write(name + ".yaml", "project:" + NL + "  name: fx" + NL)
        files = [self.write_asset_file(r) for r in (
            "assets/wireframes/home-desktop.html",
            "assets/wireframes/home-mobile.html",
            "assets/presentation/deck.html",
            "assets/icons/logo.svg")]
        p = self.render()
        self.assertEqual(p.returncode, 0, p.stderr)
        page_path = os.path.join(self.out, ".view", "assets.html")
        self.assertTrue(os.path.isfile(page_path), "assets 产物清单页缺失")
        html = open(page_path, encoding="utf-8").read()
        # 按活动分组：四个一级子目录各成组
        for group in ("wireframes", "presentation", "icons"):
            self.assertIn(group, html, "活动分组缺失：%s" % group)
        # 逐文件相对路径直链
        for rel in ("assets/wireframes/home-desktop.html",
                    "assets/wireframes/home-mobile.html",
                    "assets/presentation/deck.html",
                    "assets/icons/logo.svg"):
            self.assertIn('href="../%s"' % rel, html, "文件未出直链：%s" % rel)
        # 链接落点真实存在
        page_dir = os.path.dirname(page_path)
        for rel, want in zip(("assets/wireframes/home-desktop.html",
                              "assets/wireframes/home-mobile.html",
                              "assets/presentation/deck.html",
                              "assets/icons/logo.svg"), files):
            got = os.path.normpath(os.path.join(page_dir, "..", rel))
            self.assertTrue(os.path.isfile(got), "链接落点不存在：%s" % got)
        # 索引页有清单卡片（只增不改：产物卡片不受影响）
        index = open(os.path.join(self.out, ".view", "index.html"),
                     encoding="utf-8").read()
        self.assertIn('href="assets.html"', index, "索引缺清单页卡片")
        for name in self.NINE_DOCS:
            self.assertIn('href="%s.html"' % name, index, "产物卡片丢失：%s" % name)

    def test_no_assets_page_when_dir_absent_or_empty(self):
        self.write("wds-assets.yaml", WDS_ASSETS_DOC)
        p = self.render()
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertFalse(os.path.exists(os.path.join(self.out, ".view", "assets.html")),
                         "无 assets/ 却渲染了清单页")
        os.makedirs(os.path.join(self.out, "assets", "wireframes"))
        p2 = self.render()
        self.assertEqual(p2.returncode, 0, p2.stderr)
        self.assertFalse(os.path.exists(os.path.join(self.out, ".view", "assets.html")),
                         "空 assets/ 却渲染了清单页")

    def test_ungrouped_toplevel_files_have_their_own_group(self):
        # assets/ 顶层散文件（无活动子目录）不丢失，归「（未分组）」
        self.write("wds-assets.yaml", WDS_ASSETS_DOC)
        self.write_asset_file("assets/loose.html")
        p = self.render()
        self.assertEqual(p.returncode, 0, p.stderr)
        html = open(os.path.join(self.out, ".view", "assets.html"),
                    encoding="utf-8").read()
        self.assertIn("（未分组）", html)
        self.assertIn('href="../assets/loose.html"', html)


class ViewerC12TimelineTests(_Fixture):
    # trace: C·12 W2（Layer 1 裁定归入）——跨产物决策时间轴页
    def _two_docs_with_revisions(self):
        self.write("brainstorm.yaml", BRAINSTORM_DOC)  # 1 条：2026-09-19
        self.write("prd.yaml", NL.join([
            "project:", "  name: fx", "  status: 已定稿",
            "revisions:",
            "- date: 2026-09-21",
            "  change: FR-1.1 拆分",
            "  reason: 范围过大",
        ]))
        self.write("design.yaml", NL.join([
            "project:", "  name: fx", "  status: 草稿",
            "revisions:",
            "- date: 2026-09-25",
            "  change: tokens 定稿",
            "  reason: 双模落地",
        ]))

    def test_timeline_page_aggregates_and_sorts_revisions(self):
        self._two_docs_with_revisions()
        p = self.render()
        self.assertEqual(p.returncode, 0, p.stderr)
        page_path = os.path.join(self.out, ".view", "timeline.html")
        self.assertTrue(os.path.isfile(page_path), "决策时间轴页缺失")
        html = open(page_path, encoding="utf-8").read()
        # 表头四列（date/change/reason + 产物名锚）
        for th in ("日期", "产物", "变更", "原因"):
            self.assertIn("<th>%s</th>" % th, html, "表头缺失：%s" % th)
        # 条目 = date/change/reason + 产物名锚（链到产物页）
        self.assertIn('href="brainstorm.html"', html, "产物名锚缺失：brainstorm")
        self.assertIn('href="prd.html"', html, "产物名锚缺失：prd")
        self.assertIn('href="design.html"', html, "产物名锚缺失：design")
        for text in ("标题改名", "FR-1.1 拆分", "tokens 定稿"):
            self.assertIn(text, html, "change 内容丢失：%s" % text)
        for text in ("用户要求更短", "范围过大", "双模落地"):
            self.assertIn(text, html, "reason 内容丢失：%s" % text)
        # 按时间排序（旧 → 新）：三条日期在 HTML 中的出现顺序单调
        i1, i2, i3 = (html.index(d) for d in ("2026-09-19", "2026-09-21", "2026-09-25"))
        self.assertTrue(i1 < i2 < i3, "时间轴未按时间排序")
        # 索引有卡片
        index = open(os.path.join(self.out, ".view", "index.html"),
                     encoding="utf-8").read()
        self.assertIn('href="timeline.html"', index, "索引缺时间轴卡片")

    def test_no_timeline_page_when_all_revisions_empty(self):
        self.write("module-plan.yaml", MODULE_PLAN_DOC)  # revisions: []
        self.write("prd.yaml", DANGLING_DOC)             # 无 revisions 键
        p = self.render()
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertFalse(os.path.exists(os.path.join(self.out, ".view", "timeline.html")),
                         "revisions 全空却渲染了时间轴页")

    def test_single_doc_revision_block_unchanged(self):
        # 只增不改：产物页内的「修订历史」折叠块仍在（既有渲染路径不受聚合页影响）
        self._two_docs_with_revisions()
        p = self.render()
        self.assertEqual(p.returncode, 0, p.stderr)
        bs = self.page("brainstorm")
        self.assertIsNotNone(
            re.search(r"<details[^>]*>\s*<summary>[^<]*修订历史", bs),
            "单产物修订历史折叠块丢失")
        self.assertIn("标题改名", bs, "单产物修订内容丢失")


# ---------------------------------------------------------------------------
# v4 批 1（五轴/FH/api_refs/radius/mutation——diy-test-design schema 升级的渲染面）
# ---------------------------------------------------------------------------

FIVE_AXIS_PLAN_DOC = NL.join([
    "project:",
    "  name: fx",
    "  status: 已定稿",
    "  created: 2026-10-09",
    "  updated: 2026-10-09",
    "fault_hypotheses:",
    "- id: FH-1.1.1",
    "  ac: AC-1.1",
    "  text: 边界值未被拦截",
    "  radius: 跨模块",
    "test_cases:",
    "- id: TC-1.1.1",
    "  title: 边界用例",
    "  ac: AC-1.1",
    "  type: 单元",
    "  priority: P0",
    "  technique: 边界",
    "  dimension: 边界",
    "  kill_target: FH-1.1.1",
    "  radius: 模块",
    "  api_refs:",
    "  - {operationId: listUsers, path: /users, method: get}",
    "  status: 待办",
    "  steps: [一]",
    "dimension_audit:",
    "- ac: AC-1.1",
    "  axis: 边界",
    "  tcs: [TC-1.1.1]",
    "- ac: AC-1.1",
    "  axis: 正向",
    "  not_applicable: 夹具不适用",
    "mutation: {enabled: true}",
    "static_checks: []",
    "coverage_gaps: []",
    "revisions: []",
])


class FiveAxisLabelTests(_Fixture):
    """批 1 新段新键零裸键（故障假设/五轴审计/变异配置/维度/半径/接口锚）。"""

    def test_five_axis_sections_are_chinese(self):
        self.write("test-plan.yaml", FIVE_AXIS_PLAN_DOC)
        p = self.render()
        self.assertEqual(p.returncode, 0, p.stderr)
        # trace: Q-105——method 入 ENUM_KEYS 后，test-plan 的 api_refs[].method 装
        # HTTP 动词：FREE_TEXT_FIELDS 例外须生效（零 unmapped + 纯文本无徽章）
        self.assertNotIn("unmapped enum", p.stderr,
                         "api_refs[].method 例外失效：%s" % p.stderr)
        html = self.page("test-plan")
        self.assertNotIn('b-neutral">get</span>', html,
                         "HTTP 动词被误当 cis-method 枚举值出徽章")
        for label in ("故障假设", "五轴审计", "变异配置", "维度",
                      "爆炸半径", "接口锚", "审计轴", "不适用理由", "是否启用"):
            self.assertIn(label, html, "批 1 新键 %s 未映射中文标签" % label)
        for leak in (">fault_hypotheses<", ">dimension_audit<", ">mutation<",
                     ">dimension<", ">radius<", ">api_refs<", ">axis<",
                     ">not_applicable<", ">enabled<"):
            self.assertNotIn(leak, html, "批 1 英文键名直出：%s" % leak)


# ---------------------------------------------------------------------------
# v4 批 2a（diy-spec-scan source 数组 + summary by_source 分法计数的渲染面）
# ---------------------------------------------------------------------------

# schema: 2 稿：findings.source 三值样例（[卡点] + 多值 [卡点, 穷举, 交叉认证]）+
# summary.by_source 按元素各计（卡点 2 / 穷举 1 / 交叉认证 1）
SPEC_SCAN_SOURCE_DOC = NL.join([
    "project:",
    "  name: fx",
    "schema: 2",
    "scans:",
    "- id: SS-001",
    "  target: {kind: file, path: docs/spec.md}",
    "  units:",
    "  - {unit: 激活段, path: docs/spec.md, scanned: true}",
    "  findings:",
    "  - id: SS-001-01",
    "    type: 分支无定义",
    "    where: docs/spec.md:3",
    "    quote: 按需选择",
    "    read_as: 作者默认实现者会选",
    "    stuck: 不知道走哪条分支",
    "    would_guess: 我会走默认路径",
    "    severity: 阻断",
    "    source: [卡点]",
    "  - id: SS-001-02",
    "    type: 术语冲突",
    "    where: docs/spec.md",
    "    quote: 优先级高的先做",
    "    read_as: 排序规则未定义",
    "    stuck: 无法判断先后",
    "    would_guess: 我会按出现顺序执行",
    "    severity: 观察",
    "    source: [卡点, 穷举, 交叉认证]",
    ("  summary: {total: 2, blocker: 1, major: 0, minor: 1, units_total: 1, "
     "by_source: {卡点: 2, 穷举: 1, 交叉认证: 1}, units_scanned: 1}"),
    "revisions: []",
])


class SpecScanSourceLabelTests(_Fixture):
    """批 2a ⑥甲：by_source 键标签 + source 三值（卡点/穷举/交叉认证）值域与渲染面。"""

    # trace: 批 2a ⑥甲（表层）——键进 KEY_LABELS、三值进值域白名单（徽章判定依据），
    # 且归类语义不带极性 → 中性徽章（对 form_factor/modes 值表先例）
    def test_by_source_key_and_three_source_values_registered(self):
        self.assertEqual(viewer.KEY_LABELS.get("by_source"), "分法计数",
                         "by_source 键标签未登记")
        for value in ("卡点", "穷举", "交叉认证"):
            self.assertIn(value, viewer.VALUE_LABELS, "source 三值未入值域：%s" % value)
            self.assertNotIn(value, viewer.BADGE_CLASSES,
                             "分法值须中性徽章（不带极性）：%s" % value)

    # trace: 批 2a ⑥甲（渲染面·用户裁补徽章）——schema: 2 稿落页：零裸键 + by_source 键标签 +
    # 三值中性徽章（source 列表项 + by_source 映射行头）+ 零枚举漂移
    def test_spec_scan_by_source_renders_chinese_without_drift(self):
        self.write("spec-scan.yaml", SPEC_SCAN_SOURCE_DOC)
        p = self.render()
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertNotIn("unmapped enum", p.stderr, "source/by_source 值域漂移：%s" % p.stderr)
        html = self.page("spec-scan")
        self.assertIn("分法计数", html, "by_source 键标签未落页")
        # by_source 映射：三键以中文行头入 kv 表（值词表命中 → 中性徽章），计数为按元素各计的真值
        seg = html.split("分法计数", 1)[1][:500]
        for value, count in (("卡点", 2), ("穷举", 1), ("交叉认证", 1)):
            self.assertIn(
                '<th><span class="badge b-neutral">%s</span></th><td>%d</td>' % (value, count),
                seg,
                          "by_source 行 %s:%d 未按分法落页" % (value, count))
        # findings.source 数组三值在场且逐元素出中性徽章（枚举键列表标量走徽章路径）
        for value in ("卡点", "穷举", "交叉认证"):
            self.assertIn('<li><span class="badge b-neutral">%s</span></li>' % value, html,
                          "source 值 %s 未出徽章" % value)
        for leak in (">by_source<", ">source<"):
            self.assertNotIn(leak, html, "spec-scan 英文键名直出：%s" % leak)


# trace: 批 2c——selfcheck.yaml 完整夹具（照任务书 §5-3 覆盖清单：三源 findings 含
# layer 三值＋多元素 source 交叉命中 confidence＋disposals 全覆盖＋rescans 完整子键
# ＋anchor 完整子键＋b_review＋summary 含 ref_checked/ref_false——夹具最小化则
# 清单外键全体漏网）
SELFCHECK_DOC = """project:
  name: demo
  created: 2026-10-11
  updated: 2026-10-11
schema: 2
checks:
  - id: SC-001
    date: 2026-10-11
    status: 草稿
    anchor:
      md5: d41d8cd98f00b204e9800998ecf8427e
      commit: 03b4e35
      exec_form: 编排者合并
      shards: 3
    target:
      kind: 技能
      path: skills/diy-selfcheck/SKILL.md
    findings:
      - n: 1
        source: [预演]
        ss_ref: SS-001-01
        severity: 阻断
      - n: 2
        source: [引用核对]
        claim: 文中称三片合并 28 条
        actual: spec-scan.yaml 实为 28 条
        severity: 建议
      - n: 3
        source: [对抗]
        layer: 盲猎
        issue: B 部分缺收口出口
        severity: 观察
      - n: 4
        source: [对抗]
        layer: 边界猎手
        issue: 并发写同一产物
        severity: 建议
      - n: 5
        source: [对抗]
        layer: 验收审计
        issue: 验收标准缺负向
        severity: 观察
      - n: 6
        source: [预演, 对抗]
        layer: 验收审计
        ss_ref: SS-001-02
        confidence: 2
        issue: 交叉命中同一条歧义
        severity: 阻断
    disposals:
      - {finding: 1, level: 阻断, action: 修入, landing: 'SKILL.md:23'}
      - {finding: 2, level: 建议, action: 采纳, landing: '03-merge.md:6'}
      - {finding: 3, level: 观察, action: 留痕, landing: revisions}
      - {finding: 4, level: 建议, action: 合并, landing: '05-close.md:13'}
      - {finding: 5, level: 观察, action: 采纳, landing: '01-freeze.md:24'}
      - {finding: 6, level: 阻断, action: 修入, landing: '02-dispatch.md:11'}
    rescans:
      round1: 复扫一轮：旧值全清
      round2: 复扫二轮：零回归
      cleared:
        - 旧值 A
    b_review: B 部分：三机制评价，编排闭环成立。
    revisions:
      - date: 2026-10-11
        change: 处置后 anchor 重记
        reason: finding 1 修入
    summary:
      total: 6
      by_source:
        预演: 2
        引用核对: 1
        对抗: 4
      ref_checked: 12
      ref_false: 1
"""


class SelfcheckYamlLabelTests(_Fixture):
    """批 2c：selfcheck.yaml 标签面——DOC 标题、新键标签、source/layer 值域
    中性徽章、渲染零裸键、零 unmapped enum。"""

    def test_selfcheck_doc_title_and_value_domain_registered(self):
        self.assertEqual(viewer.DOC_LABELS.get("selfcheck"), "自检产物",
                         "selfcheck 页面标题未登记")
        # 归类语义 → 中性徽章：值入表不入 BADGE_CLASSES（照 2a 裁定）
        for value in ("预演", "引用核对", "对抗", "盲猎", "边界猎手", "验收审计"):
            self.assertIn(value, viewer.VALUE_LABELS, "值域未入表：%s" % value)
            self.assertNotIn(value, viewer.BADGE_CLASSES,
                             "归类语义须中性徽章（值入表不入徽章）：%s" % value)
        self.assertEqual(viewer.DOC_KEY_LABELS.get("selfcheck", {}).get("kind"),
                         "目标类型", "selfcheck kind 未做 doc 级覆盖")
        self.assertEqual(viewer.DOC_KEY_LABELS.get("selfcheck", {}).get("layer"),
                         "审查层", "selfcheck layer 未做 doc 级覆盖")
        for key in ("schema", "anchor", "disposals", "rescans", "b_review",
                    "ss_ref", "exec_form", "shards", "ref_checked", "ref_false",
                    "landing", "issue", "round1", "round2", "cleared"):
            self.assertIn(key, viewer.KEY_LABELS, "新键标签未登记：%s" % key)

    def test_selfcheck_renders_chinese_without_drift(self):
        self.write("selfcheck.yaml", SELFCHECK_DOC)
        p = self.render()
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertNotIn("unmapped enum", p.stderr, "selfcheck 值域漂移：%s" % p.stderr)
        html = self.page("selfcheck")
        for label in ("锚点", "处置记录", "复扫记录", "B 部分机制评价",
                      "关联预演条目", "执行形态", "分片数", "已核引用数",
                      "失实引用数", "落点", "目标类型", "审查层"):
            self.assertIn(label, html, "键标签未落页：%s" % label)
        for key in ("anchor", "disposals", "rescans", "b_review", "ss_ref",
                    "exec_form", "shards", "ref_checked", "ref_false", "landing",
                    "source", "layer", "kind", "claim", "actual", "issue",
                    "confidence", "round1", "round2", "cleared", "level", "action"):
            self.assertNotIn(">%s<" % key, html, "英文键名直出：%s" % key)
        # findings.source 数组逐元素出中性徽章（列表项走徽章路径，照 2a 先例）
        for value in ("预演", "引用核对", "对抗"):
            self.assertIn('<li><span class="badge b-neutral">%s</span></li>' % value,
                          html, "source 值未出中性徽章：%s" % value)
        # layer 三值落页（标量字段形态随渲染器，值在场即证标签链通）
        for value in ("盲猎", "边界猎手", "验收审计"):
            self.assertIn(value, html, "layer 值未落页：%s" % value)
        self.assertIn("编排闭环成立", html, "b_review 内容丢失")


class ViewerSortOrderTests(unittest.TestCase):
    """v4 批 3（底单 :387 段三项裁定）——index 卡片序按 created 生成时间排：
    五态＋动态挂两例。三消费点（index 卡片序 / others 导航序 / 渲染循环序）
    全走 sort_docs 的 all_docs 序，此处单点断言即全覆盖。"""

    @staticmethod
    def _doc(created="2026-10-13 10:00:00"):
        proj = {"name": "fx", "updated": "2026-10-13"}
        if created is not None:
            proj["created"] = created
        return {"project": proj}

    def test_time_order_strict(self):
        # 态一：时分秒严格序（同日内先后可比）
        docs = [("prd", self._doc("2026-10-01 09:00:00")),
                ("architecture", self._doc("2026-10-01 08:59:59")),
                ("design", self._doc("2026-09-30 23:00:00"))]
        self.assertEqual([n for n, _ in viewer.sort_docs(docs)],
                         ["design", "architecture", "prd"])

    def test_same_second_tie_uses_chain_order(self):
        # 态二：同秒并列走链序兜底；非链产物（链序表无位）排链产物之后
        same = "2026-10-01 09:00:00"
        docs = [("architecture", self._doc(same)),
                ("analysis", self._doc(same)),
                ("prd", self._doc(same))]
        self.assertEqual([n for n, _ in viewer.sort_docs(docs)],
                         ["prd", "architecture", "analysis"])

    def test_pure_date_sorts_as_midnight(self):
        # 态三：存量纯日期不回填、按当日零点参与（旧日期 vs 带时分秒新日期交排）
        docs = [("prd", self._doc("2026-10-01")),
                ("architecture", self._doc("2026-09-30 23:59:59")),
                ("design", self._doc("2026-10-01 00:00:01"))]
        self.assertEqual([n for n, _ in viewer.sort_docs(docs)],
                         ["architecture", "prd", "design"])

    def test_unparseable_created_falls_back_to_chain(self):
        # 态四：created 值不可比不炸——链产物归桶一尾按链序兜底；非链落桶二按文件名
        docs = [("prd", self._doc("2026-10-01 09:00:00")),
                ("architecture", self._doc("不是日期")),
                ("analysis", self._doc("也是乱写"))]
        self.assertEqual([n for n, _ in viewer.sort_docs(docs)],
                         ["prd", "architecture", "analysis"])

    def test_missing_created_sorts_last(self):
        # 态五：缺 created 排最后（桶三组内按链序位、无位按文件名殿后）
        docs = [("sprint", self._doc(None)),
                ("analysis", self._doc(None)),
                ("prd", self._doc("2026-10-01 09:00:00"))]
        self.assertEqual([n for n, _ in viewer.sort_docs(docs)],
                         ["prd", "sprint", "analysis"])

    def test_editorial_review_attaches_after_target(self):
        # 动态挂例一（§7-5 甲）：editorial-review/selfcheck 读最新记录 target
        # 匹配产物挂紧后；同挂时 editorial-review 前、selfcheck 后
        er = {"project": self._doc()["project"],
              "reviews": [{"id": "ER-001", "target": "diy-output/brief.yaml"}]}
        sc = {"project": self._doc()["project"],
              "checks": [{"id": "SC-001",
                          "target": {"kind": "文档", "path": "diy-output/brief.yaml"}}]}
        same = "2026-10-12 08:00:00"  # 四产物并列，逼出链序兜底位
        er["project"]["created"] = same
        sc["project"]["created"] = same
        docs = [("editorial-review", er), ("selfcheck", sc),
                ("brief", self._doc(same)), ("prd", self._doc(same))]
        self.assertEqual([n for n, _ in viewer.sort_docs(docs)],
                         ["brief", "editorial-review", "selfcheck", "prd"])

    def test_unmatched_target_falls_to_non_chain_bucket(self):
        # 动态挂例二（§7-5 甲）：target 非产物（任务书路径）匹配不上 → 按非链
        # 产物处理（桶二，文件名字母序）
        er = {"project": {"name": "fx", "created": "手写时间",
                          "updated": "2026-10-13"},
              "reviews": [{"id": "ER-001",
                           "target": "diy-coder/.analysis/x/taskbook.md"}]}
        docs = [("editorial-review", er),
                ("zebra-note", self._doc("另一乱值")),
                ("prd", self._doc("2026-10-01 09:00:00"))]
        self.assertEqual([n for n, _ in viewer.sort_docs(docs)],
                         ["prd", "editorial-review", "zebra-note"])


# ---------------------------------------------------------------------------
# Q-105（底单 :363 ④ + :367 ⑧ · R3=A+ 封闭世界断言）——brainstorm 61 枚举 +
# cis-method 全键 + 全产物/全键/全值缺标签即红
# ---------------------------------------------------------------------------

# brainstorm 技术库全量（brain-methods.csv 61 条·techniques[].technique 值域）
BRAINSTORM_TECHNIQUES = [
    "是而且接龙", "静默轮写", "随机刺激", "角色扮演", "想法接力赛",
    "假如情景", "类比思维", "反转倒置", "第一性原理", "强制关联",
    "时间位移", "隐喻映射", "跨界授粉", "概念融合", "反向头脑风暴",
    "感官探索", "连续五问", "形态分析", "挑衅式刺激", "假设反转",
    "问题风暴", "约束地图", "失败分析", "涌现式思考", "内在小孩会议",
    "阴影挖掘", "价值观考古", "未来自我访谈", "身体智慧对话", "许可授权",
    "SCAMPER 七镜头法", "六顶思考帽", "思维导图", "资源约束", "决策树映射",
    "方案矩阵", "特质迁移", "时间旅行脱口秀", "外星人类学家", "梦境融合实验室",
    "情绪管弦乐队", "平行宇宙咖啡馆", "人格面具之旅", "混沌工程", "游击园艺式创意",
    "海盗法则头脑风暴", "僵尸末日预案", "醉汉说史式复述", "反方案", "量子叠加",
    "元素之力", "自然解法", "生态系统思维", "演化压力", "观察者效应",
    "纠缠思维", "叠加坍缩", "原住民智慧", "融合料理", "仪式创新", "神话框架",
]
BRAINSTORM_CATEGORIES = [
    "协作", "创意", "深度分析", "内省之乐", "结构化",
    "戏剧化", "狂野", "仿生", "量子", "文化",
]

# cis-method 四分支 deliverable 键全集（steps/02~05「本分支结构」节·119 键 + deliverable）
CIS_INNOVATION_KEYS = [
    "company_name", "strategic_focus", "current_situation", "strategic_challenge",
    "market_landscape", "competitive_dynamics", "market_opportunities", "market_insights",
    "current_business_model", "value_proposition", "revenue_cost_structure", "model_weaknesses",
    "disruption_vectors", "unmet_jobs", "technology_enablers", "strategic_whitespace",
    "innovation_initiatives", "business_model_innovation", "value_chain_opportunities",
    "partnership_opportunities", "option_a_name", "option_a_description", "option_a_pros",
    "option_a_cons", "option_b_name", "option_b_description", "option_b_pros", "option_b_cons",
    "option_c_name", "option_c_description", "option_c_pros", "option_c_cons",
    "recommended_strategy", "key_hypotheses", "success_factors", "phase_1", "phase_2", "phase_3",
    "leading_indicators", "lagging_indicators", "decision_gates", "key_risks", "risk_mitigation",
]
CIS_PROBLEM_KEYS = [
    "problem_title", "problem_category", "initial_problem", "refined_problem_statement",
    "problem_context", "success_criteria", "problem_boundaries", "root_cause_analysis",
    "contributing_factors", "system_dynamics", "driving_forces", "restraining_forces",
    "constraints", "key_insights", "solution_methods", "generated_solutions",
    "creative_alternatives", "evaluation_criteria", "solution_analysis", "recommended_solution",
    "solution_rationale", "implementation_approach", "action_steps", "timeline",
    "resources_needed", "responsible_parties", "success_metrics", "validation_plan",
    "risk_mitigation", "adjustment_triggers", "key_learnings", "what_worked", "what_to_avoid",
]
CIS_DESIGN_KEYS = [
    "project_name", "design_challenge", "challenge_statement", "user_insights",
    "key_observations", "empathy_map", "pov_statement", "hmw_questions", "problem_insights",
    "ideation_methods", "generated_ideas", "top_concepts", "prototype_approach",
    "prototype_description", "features_to_test", "testing_plan", "user_feedback",
    "key_learnings", "refinements", "action_items", "success_metrics",
]
CIS_STORY_KEYS = [
    "story_type", "framework_name", "story_purpose", "target_audience", "key_messages",
    "opening_hook", "core_narrative", "story_beats", "emotional_arc", "resolution",
    "complete_story", "character_voice", "conflict_tension", "transformation",
    "emotional_touchpoints", "short_version", "medium_version", "extended_version",
    "best_channels", "audience_considerations", "tone_notes", "adaptation_suggestions",
    "refinement_opportunities", "additional_versions", "feedback_plan",
]
CIS_METHOD_VALUES = ["创新策略", "问题求解", "设计思维", "叙事"]


def _walk_closed_world(doc_name, node, missing_keys, missing_values, _seen=None):
    """封闭世界遍历（R3=A+）：dict 键须有中文键标签；枚举键标量值须有值标签
    （FREE_TEXT_FIELDS 除外）。缺一即收集，测试断言收集为空。"""
    if _seen is None:
        _seen = set()
    if isinstance(node, dict):
        if id(node) in _seen:
            return
        _seen.add(id(node))
        doc_over = viewer.DOC_KEY_LABELS.get(doc_name, {})
        for k, v in node.items():
            if k not in viewer.KEY_LABELS and k not in doc_over:
                missing_keys.append((doc_name, k))
            if (k in viewer.ENUM_KEYS
                    and (doc_name, k) not in FREE_TEXT_FIELDS
                    and v is not None and not isinstance(v, (dict, list))):
                s = str(v).strip()
                if s and s.lower() not in {x.lower() for x in viewer.VALUE_LABELS}:
                    missing_values.append((doc_name, k, s))
            _walk_closed_world(doc_name, v, missing_keys, missing_values, _seen)
    elif isinstance(node, list):
        if id(node) in _seen:
            return
        _seen.add(id(node))
        for x in node:
            _walk_closed_world(doc_name, x, missing_keys, missing_values, _seen)


def _mk_brainstorm_yaml():
    """brainstorm 夹具：一条会话带 61 技术全量（techniques 列表 + category 枚举）。"""
    lines = [
        "project:", "  name: fx", "  created: 2026-10-19", "  updated: 2026-10-19",
        "sessions:", "- id: BS-001", "  topic: 全量技术库回归", "  status: 已完成",
        "  goals: 覆盖 61 技术", "  techniques:",
    ]
    for i, t in enumerate(BRAINSTORM_TECHNIQUES):
        cat = BRAINSTORM_CATEGORIES[i % len(BRAINSTORM_CATEGORIES)]
        lines.append(f"  - {{technique: {t}, category: {cat}}}")
    lines.append("  steps: [发散, 收敛]")
    lines.append("  actions: [落盘]")
    lines.append("revisions: []")
    return NL.join(lines)


def _mk_cis_method_yaml(method_value, deliverable_keys):
    """cis-method 夹具：一条会话，deliverable 覆盖指定分支全部键。"""
    lines = [
        "project:", "  name: fx", "  created: 2026-10-19", "  updated: 2026-10-19",
        "sessions:", "- id: CM-001", f"  method: {method_value}", "  topic: 全键回归",
        "  date: 2026-10-19", "  status: 已完成", "  current_step: 9",
        "  deliverable:",
    ]
    for k in deliverable_keys:
        lines.append(f"    {k}: 样例内容")
    lines.append("  open_questions: []")
    lines.append("revisions: []")
    return NL.join(lines)


class ClosedWorldLabelTests(_Fixture):
    """R3=A+ 封闭世界断言：渲染路径遍历产物全键/全值，凡不在词典即红（缺标签零容忍）。"""

    def _assert_closed_world(self, doc_name, data):
        missing_keys, missing_values = [], []
        _walk_closed_world(doc_name, data, missing_keys, missing_values)
        self.assertEqual(missing_keys, [],
                         "封闭世界断言失败——缺中文键标签：%s" % missing_keys[:10])
        self.assertEqual(missing_values, [],
                         "封闭世界断言失败——缺值标签：%s" % missing_values[:10])

    def test_brainstorm_all_61_techniques_have_value_labels(self):
        # 底单 :363 ④——技术库 61 条逐条入值表，缺一即渲染 unmapped（零裸键漏网）
        for t in BRAINSTORM_TECHNIQUES:
            self.assertIn(t, viewer.VALUE_LABELS, "技术名缺值标签：%s" % t)
        for c in BRAINSTORM_CATEGORIES:
            self.assertIn(c, viewer.VALUE_LABELS, "类名缺值标签：%s" % c)
        self.assertEqual(len(BRAINSTORM_TECHNIQUES), 61, "技术库应为 61 条")

    def test_cis_method_all_deliverable_keys_have_key_labels(self):
        # 底单 :367 ⑧——四分支 deliverable 键 + deliverable 顶层键全量入 KEY_LABELS
        all_keys = sorted(set(
            CIS_INNOVATION_KEYS + CIS_PROBLEM_KEYS + CIS_DESIGN_KEYS + CIS_STORY_KEYS))
        for k in all_keys:
            self.assertIn(k, viewer.KEY_LABELS, "cis-method 键缺标签：%s" % k)
        self.assertIn("deliverable", viewer.KEY_LABELS, "deliverable 顶层键缺标签")
        # 四分支 method 值域
        for m in CIS_METHOD_VALUES:
            self.assertIn(m, viewer.VALUE_LABELS, "method 值缺标签：%s" % m)

    def test_brainstorm_closed_world_and_render(self):
        # 封闭世界：全键/全值在词典；渲染：零 unmapped + 零英文裸键 + 技术徽章在场
        import yaml
        data = yaml.safe_load(_mk_brainstorm_yaml())
        self._assert_closed_world("brainstorm", data)
        self.write("brainstorm.yaml", _mk_brainstorm_yaml())
        p = self.render()
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertNotIn("unmapped enum", p.stderr,
                         "brainstorm 渲染仍报枚举漂移：%s" % p.stderr)
        html = self.page("brainstorm")
        # 技术值出徽章（technique ∈ ENUM_KEYS → badge 路径）
        self.assertIn('class="badge b-neutral">是而且接龙</span>', html,
                      "技术名未出中性徽章")
        self.assertIn('class="badge b-neutral">SCAMPER 七镜头法</span>', html,
                      "SCAMPER 技术名未出中性徽章")
        self.assertIn('class="badge b-neutral">神话框架</span>', html,
                      "末条技术名未出中性徽章")
        # 类名值徽章
        self.assertIn('class="badge b-neutral">协作</span>', html)
        # 英文键名不裸出
        for leak in (">technique<", ">category<", ">actions<", ">goals<"):
            self.assertNotIn(leak, html, "brainstorm 英文键名直出：%s" % leak)
        self.assertIn("头脑风暴方法", html, "technique 键标签未映射")
        self.assertIn("行动计划", html, "actions 键标签未映射")

    def test_cis_method_closed_world_and_render_all_branches(self):
        # 四分支各渲一遍：封闭世界全绿 + 零 unmapped + 键标签中文化 + method 徽章
        import yaml
        branches = (
            ("创新策略", CIS_INNOVATION_KEYS),
            ("问题求解", CIS_PROBLEM_KEYS),
            ("设计思维", CIS_DESIGN_KEYS),
            ("叙事", CIS_STORY_KEYS),
        )
        for method_value, keys in branches:
            yaml_text = _mk_cis_method_yaml(method_value, keys)
            data = yaml.safe_load(yaml_text)
            self._assert_closed_world("cis-method", data)
            self.write("cis-method.yaml", yaml_text)
            p = self.render()
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertNotIn("unmapped enum", p.stderr,
                             "%s 分支渲染仍报枚举漂移：%s" % (method_value, p.stderr))
            html = self.page("cis-method")
            # 页面标题中文化（DOC_LABELS）
            self.assertIn("<h1>创意方法引导器</h1>", html,
                          "%s：cis-method 页面标题未中文化" % method_value)
            # method ∈ ENUM_KEYS（用户裁定）→ 值出中性徽章
            self.assertIn('class="badge b-neutral">%s</span>' % method_value, html,
                          "%s：method 值未出中性徽章" % method_value)
            self.assertIn("<th>方法</th>", html, "method 键标签未映射")
            # deliverable 键标签：抽样分支首键不裸出（全键量大，封闭世界已全量断言）
            first_key = keys[0]
            self.assertNotIn(">%s<" % first_key, html,
                             "%s：键 %s 英文直出" % (method_value, first_key))
            self.assertIn("交付内容", html, "deliverable 键标签未映射")

    def test_closed_world_catches_missing_label(self):
        # 封闭世界断言的反向防线：人为注入未知键/未知枚举值 → 必须被收集（红），
        # 证明断言真的在工作而非空转
        data = {
            "project": {"name": "fx", "created": "2026-10-19", "updated": "2026-10-19"},
            "sessions": [{"id": "CM-001", "method": "创新策略", "topic": "t",
                          "date": "2026-10-19", "status": "草稿", "current_step": 1,
                          "deliverable": {"zzz_unknown_key": "x"},
                          "open_questions": []}],
            "revisions": [],
        }
        missing_keys, missing_values = [], []
        _walk_closed_world("cis-method", data, missing_keys, missing_values)
        self.assertIn(("cis-method", "zzz_unknown_key"), missing_keys,
                      "封闭世界断言未捕获未知键")
        # 注入未知枚举值（method 之外的枚举键用一个假值）
        data2 = {"project": {"name": "fx"},
                 "status": "草稿",
                 "priority": "不存在的极性值"}
        missing_keys2, missing_values2 = [], []
        _walk_closed_world("prd", data2, missing_keys2, missing_values2)
        self.assertIn(("prd", "priority", "不存在的极性值"), missing_values2,
                      "封闭世界断言未捕获未知枚举值")


class EnumValueAlignmentTest(unittest.TestCase):
    """Q-115 值域对齐：viewer 常量单点同源＋值标签覆盖跨技能枚举常量。"""

    # 豁免集（登记债，非放行口径）：RADII 五值与 DIMENSIONS 的 正向/异常 此前
    # 从未进 VALUE_LABELS（徽章缺档仅影响着色，中文值渲染自身不裸奔）；glossary
    # 不在 Q-115 scope，随夜队列回报登记，补注册后即从本表删除。
    _EXEMPT = frozenset({("RADII", "局部"), ("RADII", "模块"), ("RADII", "跨模块"),
                         ("RADII", "系统"), ("RADII", "外部"),
                         ("DIMENSIONS", "正向"), ("DIMENSIONS", "异常")})

    def test_http_methods_single_source(self):
        """HTTP 动词值域＝check 引擎常量单点（渲染侧 set 包装，不另持字面量）。"""
        from viewer_labels import HTTP_METHODS
        from diyc_check_docs_lib import HTTP_METHODS as LIB_HTTP_METHODS
        self.assertEqual(set(HTTP_METHODS), set(LIB_HTTP_METHODS))

    def test_registry_chinese_values_in_value_labels(self):
        """面清单枚举的每个中文值须在值标签表（缺档=徽章失灵）。"""
        from diyc_check_docs import _registry
        for name, values, _faces in _registry():
            for value in values:
                if not any(ord(ch) > 127 for ch in value):
                    continue  # 英文机器锚点（P0/frontend/test-design 等）走译名表，非本断言
                if (name, value) in self._EXEMPT:
                    continue
                self.assertIn(value, viewer.VALUE_LABELS,
                              "值域缺标签：%s.%s（面清单枚举）" % (name, value))


if __name__ == "__main__":
    unittest.main()
