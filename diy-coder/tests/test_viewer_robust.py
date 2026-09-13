# -*- coding: utf-8 -*-
"""diy-viewer 形状降级与逐文件隔离测试（S-11，BUG-008 回归）。

夹具：临时项目 + output_dir 混入未知形态 YAML（顶层 list / 顶层标量）
与正常产物；断言 rc=0、正常页面与 index.html 产出、坏文件在索引中
以错误卡片可见、stderr 无 Traceback。
"""
import os
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
    "  status: final",
    "  updated: 2026-09-13",
    "features:",
    "- id: FG-1",
    "  name: 核心",
    "  requirements:",
    "  - id: FR-1.1",
    "    statement: 迷你需求",
    "    priority: must",
])


def run_viewer(root):
    return subprocess.run(
        [sys.executable, VIEWER, "--project-root", root, "--no-open"],
        capture_output=True, text=True, encoding="utf-8",
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


if __name__ == "__main__":
    unittest.main()
