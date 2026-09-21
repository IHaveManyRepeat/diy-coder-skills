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


if __name__ == "__main__":
    unittest.main()
