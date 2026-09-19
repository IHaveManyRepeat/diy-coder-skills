# -*- coding: utf-8 -*-
"""diy-viewer 形状降级与逐文件隔离测试（S-11，BUG-008 回归）。

夹具：临时项目 + output_dir 混入未知形态 YAML（顶层 list / 顶层标量）
与正常产物；断言 rc=0、正常页面与 index.html 产出、坏文件在索引中
以错误卡片可见、stderr 无 Traceback。
"""
import os
import re
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
VIEWER = os.path.join(HERE, "..", "skills", "diy-viewer", "scripts", "viewer.py")
NL = chr(10)

GOOD_PRD = NL.join([
    "project:",
    "  name: mini",
    "  status: 已定稿",
    "  updated: 2026-09-13",
    "features:",
    "- id: FG-1",
    "  name: 核心",
    "  requirements:",
    "  - id: FR-1.1",
    "    statement: 迷你需求",
    "    priority: 必须",
])


def run_viewer(root):
    return subprocess.run(
        [sys.executable, VIEWER, "--project-root", root, "--no-open"],
        capture_output=True, text=True, encoding="utf-8", timeout=60,
    )


class ViewerShapeDegradeTests(unittest.TestCase):

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

    # trace: S-11 AC-11.1 TC-11.1.1
    def test_unknown_shape_degrades_without_breaking_batch(self):
        self.write("prd.yaml", GOOD_PRD)
        self.write("shapes.yaml", "- 顶层是列表" + NL + "- 不是映射" + NL)
        self.write("scalar.yaml", "just a plain string" + NL)
        p = run_viewer(self.root)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertNotIn("Traceback", p.stderr)
        view = os.path.join(self.out, ".view")
        self.assertTrue(os.path.isfile(os.path.join(view, "index.html")), "索引缺失")
        self.assertTrue(os.path.isfile(os.path.join(view, "prd.html")), "正常产物页面缺失")
        index = open(os.path.join(view, "index.html"), encoding="utf-8").read()
        self.assertIn("shapes", index, "坏文件在索引中不可见（错误卡片缺失）")
        self.assertIn("scalar", index, "坏文件在索引中不可见（错误卡片缺失）")
        prd_html = open(os.path.join(view, "prd.html"), encoding="utf-8").read()
        self.assertIn("迷你需求", prd_html)

    # trace: S-11 AC-11.1 TC-11.1.1
    def test_recursive_anchor_degrades_without_crash(self):
        # 对抗审查 R4：YAML 合法但自引用（递归锚点）——ID 索引遍历不得无限递归崩溃
        self.write("prd.yaml", GOOD_PRD)
        self.write("recursive.yaml",
                   "project: &p" + NL + "  name: x" + NL + "  loop: *p" + NL)
        p = run_viewer(self.root)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertNotIn("Traceback", p.stderr)
        view = os.path.join(self.out, ".view")
        self.assertTrue(os.path.isfile(os.path.join(view, "index.html")), "索引缺失")
        self.assertTrue(os.path.isfile(os.path.join(view, "prd.html")), "正常产物页面缺失")


# --- 质量评估修复回归（B1-B4，2026-09-13 skill-analysis determinism-1/2、architecture-1、enhancement-1）---

TEST_PLAN_DOC = NL.join([
    "project:",
    "  name: fx",
    "  status: 已定稿",
    "test_cases:",
    "- id: TC-1.1.1",
    "  ac: AC-1.1",
    "  type: 单元",
    "  priority: P0",
    "  status: 待办",
    "  steps:",
    "  - 第一步",
    "- id: TC-1.1.2",
    "  ac: AC-1.1",
    "  type:",
    "  priority: P1",
    "  status: 待办",
    "  steps:",
    "  - 第二步",
])

BUG_LOG_DOC = NL.join([
    "project:",
    "  name: fx",
    "  status: 已定稿",
    "bugs:",
    "- id: BUG-1",
    "  class: 功能型",
    "  subclass: 逻辑",
    "  type: 双写状态不同步",
    "  symptom: 症状一行",
])

ARCH_DOC = NL.join([
    "project:",
    "  name: fx",
    "  status: 草稿",
    "decisions:",
    "- id: D-1",
    "  title: 载体选择",
    "  decision: 选用 React，因为团队熟悉",
    "  status: 已采纳",
    "- id: D-2",
    "  title: 备选",
    "  decision: 改用 Vue",
    "  status: 待定",
])

DESIGN_DOC = NL.join([
    "project:",
    "  name: fx",
    "  status: 草稿",
    "direction: 瑞士编辑风",
    "frontend_framework: html",
    "tokens:",
    "  color:",
    "    bg: '#ffffff'",
    "  spacing:",
    "    scale: [4px, 8px]",
    "pages:",
    "- id: P-1",
    "  name: 待办列表",
    "  route: /home",
    "  states:",
    "  - {name: 悬停, signals: [图标, 动效]}",
    "  prototype: prototypes/P-1.html",
    "  implementation: src/pages/P-1.jsx",
])

DOC_NAMES = ["prd", "architecture", "epics", "stories", "test-plan",
             "openapi", "sprint", "bug-log", "design"]


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
        path = os.path.join(self.out, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def page_body(self, name):
        html = open(os.path.join(self.out, ".view", name + ".html"),
                    encoding="utf-8").read()
        return html, html.split("</main>")[0]


class ViewerDocScopedTypeLabelTests(_Fixture):
    # trace: determinism-1（B1）：type 标签文档级覆盖，test-plan 不得再渲染成小类
    def test_type_label_is_doc_scoped(self):
        self.write("test-plan.yaml", TEST_PLAN_DOC)
        self.write("bug-log.yaml", BUG_LOG_DOC)
        p = run_viewer(self.root)
        self.assertEqual(p.returncode, 0, p.stderr)
        _, plan = self.page_body("test-plan")
        self.assertIn("<th>类型</th>", plan, "test-plan 的 type 表头非「类型」")
        self.assertNotIn("小类", plan, "test-plan 的 type 误挂缺陷三级分类标签")
        _, blog = self.page_body("bug-log")
        self.assertIn("小类", blog, "bug-log 的 type 未按缺陷三级分类渲染")
        self.assertNotIn(">类型<", blog, "bug-log 的 type 标签回落成了「类型」")
        # 自由文本小类（schema 无枚举约束）不得触发漂移诊断——诊断只留给严格枚举键
        self.assertNotIn("unmapped enum", p.stderr,
                         "bug-log 自由文本小类被误报为枚举漂移")


class ViewerDesignFamilyTests(_Fixture):
    # trace: architecture-1（B2）：design 整族中文映射 + 全文档标题防漏
    def test_design_page_is_chinese(self):
        self.write("design.yaml", DESIGN_DOC)
        self.write("prd.yaml", GOOD_PRD)
        p = run_viewer(self.root)
        self.assertEqual(p.returncode, 0, p.stderr)
        html, body = self.page_body("design")
        self.assertIn("<h1>设计稿</h1>", html, "design 页面标题未映射为中文")
        for label in ("方向", "前端框架", "设计令牌", "颜色", "间距", "页面",
                      "信号", "结构稿", "实现路径"):
            self.assertIn(label, body, "design 键 %s 未映射为中文" % label)
        # trace: 对抗审查修复——states[].signals 列表标量消费值词表（中文值原样渲染，不再英文裸奔）
        self.assertIn("图标", body, "signals 列表图标值未渲染")
        self.assertIn("动效", body, "signals 列表动效值未渲染")
        prd_html, _ = self.page_body("prd")
        self.assertIn("设计稿", prd_html.split("<main>")[0], "prd 导航未中文化 design")
        index = open(os.path.join(self.out, ".view", "index.html"),
                     encoding="utf-8").read()
        seg = index.split('href="design.html"', 1)[1][:120]
        self.assertIn("设计稿", seg, "index 卡片未中文化 design")

    def test_all_doc_titles_are_chinese(self):
        for name in DOC_NAMES:
            self.write(name + ".yaml", "project:" + NL + "  name: fx" + NL)
        p = run_viewer(self.root)
        self.assertEqual(p.returncode, 0, p.stderr)
        index = open(os.path.join(self.out, ".view", "index.html"),
                     encoding="utf-8").read()
        for name in DOC_NAMES:
            html, _ = self.page_body(name)
            m = re.search(r"<h1>([^<]+)</h1>", html)
            self.assertIsNotNone(m, "%s 页面缺标题" % name)
            title = m.group(1)
            self.assertTrue(any(ord(c) > 0x2E80 for c in title),
                            "%s 页面标题非中文：%s" % (name, title))
            self.assertIsNone(re.search(r"[A-Za-z]", title),
                              "%s 页面标题残留英文：%s" % (name, title))
            seg = index.split('href="%s.html"' % name, 1)[1][:120]
            self.assertTrue(any(ord(c) > 0x2E80 for c in seg),
                            "%s 索引卡片非中文" % name)


class ViewerBadgeValueAwareTests(_Fixture):
    # trace: determinism-2/3（B3）：值感知徽章 + 空枚举回落 — + proposed/accepted 映射
    def test_free_text_decision_and_route_are_plain_text(self):
        self.write("architecture.yaml", ARCH_DOC)
        self.write("design.yaml", DESIGN_DOC)
        p = run_viewer(self.root)
        self.assertEqual(p.returncode, 0, p.stderr)
        _, arch = self.page_body("architecture")
        self.assertIn("选用 React", arch, "决策自由文本丢失")
        self.assertIsNone(re.search(r'class="badge[^"]*">[^<]*选用', arch),
                          "决策自由文本被塞进徽章")
        self.assertIn("已采纳", arch, "accepted 未映射为中文")
        self.assertIn("待定", arch, "proposed 未映射为中文")
        _, design = self.page_body("design")
        self.assertIn("/home", design, "route 丢失")
        self.assertIsNone(re.search(r'class="badge[^"]*">[^<]*/home', design),
                          "route URL 被当状态徽章")
        # 自由文本（决策/route URL）不得报枚举漂移；诊断信号只留给真越界
        self.assertNotIn("unmapped enum", p.stderr,
                         "自由文本决策/route 被误报为枚举漂移")

    def test_unknown_enum_value_still_diagnosed(self):
        # 诊断的正向契约：严格枚举键（test-plan technique）上的越界值必须一行可见
        self.write("test-plan.yaml", TEST_PLAN_DOC.replace(
            "  type: 单元", "  type: 单元" + NL + "  technique: 未登记技法"))
        p = run_viewer(self.root)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("unmapped enum: 未登记技法", p.stderr,
                      "严格枚举键的越界值未报漂移")

    def test_documented_enum_keeps_badge_and_tooltip(self):
        self.write("test-plan.yaml", TEST_PLAN_DOC)
        p = run_viewer(self.root)
        self.assertEqual(p.returncode, 0, p.stderr)
        _, plan = self.page_body("test-plan")
        self.assertIn('class="badge b-neutral"', plan, "P0 优先级丢失徽章")
        self.assertIn("最高优先级", plan, "P0 丢失术语表悬浮解释")
        self.assertNotIn("unmapped enum: P0", p.stderr, "P0 被误报未映射")

    def test_none_enum_renders_dash_not_none(self):
        self.write("test-plan.yaml", TEST_PLAN_DOC)
        p = run_viewer(self.root)
        self.assertEqual(p.returncode, 0, p.stderr)
        _, plan = self.page_body("test-plan")
        self.assertNotIn("None", plan, "空枚举值渲染出字面 None")
        self.assertIn('<span class="dim">—</span>', plan, "空值未回落为 —")


class ViewerConfigShapeTests(_Fixture):
    # trace: 对抗审查修复（P2）——配置形状异常（顶层/paths/值）降级默认 + 一行警告，不裸栈
    def write_config(self, content):
        with open(os.path.join(self.root, "diy-coder.yaml"), "w", encoding="utf-8") as f:
            f.write(content)

    def assert_rendered_ok(self, p):
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertNotIn("Traceback", p.stderr)
        self.assertTrue(os.path.isfile(os.path.join(self.out, ".view", "index.html")),
                        "形状异常配置下正常产物未渲染")

    def test_scalar_paths_degrades(self):
        self.write("prd.yaml", GOOD_PRD)
        self.write_config("paths: not-a-map" + NL)
        p = run_viewer(self.root)
        self.assert_rendered_ok(p)
        self.assertIn("paths", p.stderr, "paths 形状异常无警告")

    def test_non_string_output_dir_degrades(self):
        self.write("prd.yaml", GOOD_PRD)
        self.write_config("paths:" + NL + "  output_dir: 123" + NL)
        p = run_viewer(self.root)
        self.assert_rendered_ok(p)
        self.assertIn("output_dir", p.stderr, "output_dir 值类型异常无警告")

    def test_top_level_list_ignored(self):
        self.write("prd.yaml", GOOD_PRD)
        self.write_config("- just" + NL + "- a list" + NL)
        p = run_viewer(self.root)
        self.assert_rendered_ok(p)


class ViewerFreshnessMetaTests(_Fixture):
    # trace: enhancement-1（B4）：.view 新鲜度 meta（生成时间 + 来源目录）
    def test_generated_at_and_source_in_pages(self):
        self.write("prd.yaml", GOOD_PRD)
        p = run_viewer(self.root)
        self.assertEqual(p.returncode, 0, p.stderr)
        for name in ("prd", "index"):
            html = open(os.path.join(self.out, ".view", name + ".html"),
                        encoding="utf-8").read()
            self.assertIn("生成于", html, "%s 缺生成时间" % name)
            self.assertIn("来源 diy-output", html, "%s 缺来源目录" % name)


if __name__ == "__main__":
    unittest.main()
