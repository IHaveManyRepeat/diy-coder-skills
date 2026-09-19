# -*- coding: utf-8 -*-
# trace: 2026-09-13 裁定——augment 正交字段（diy-augment 编码后验证留痕）的 viewer 呈现：
# 任务卡片徽章（通过/失败/已跳过）+「补测待裁断」聚合面板（跨 test-plan/stories 反查）+
# 索引卡片徽章。无 fail 任务时面板与徽章零输出。
"""diy-viewer 对 sprint.aggregate augment 字段的渲染测试。

夹具：临时项目 + sprint.yaml（三种 augment 态）/ test-plan.yaml（fail 用例带
kill_target 与 note）/ stories.yaml（标题反查）。
"""
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
VIEWER = os.path.join(HERE, "..", "skills", "diy-viewer", "scripts", "viewer.py")
NL = chr(10)

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


if __name__ == "__main__":
    unittest.main()
