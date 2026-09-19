# -*- coding: utf-8 -*-
"""diy-viewer 浏览器自动打开的环境边界测试（2026-09-13 裁定）。

夹具：临时项目 + 假 webbrowser 模块（PYTHONPATH 注入，把 open 调用记录到标记
文件，绝不真开浏览器）。断言：非交互环境（子进程 stdout 为管道）默认不打开、
--open 强制打开、--no-open 一票否决；交互分支由 should_open 纯函数单测覆盖。
"""
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
VIEWER = os.path.join(HERE, "..", "skills", "diy-viewer", "scripts", "viewer.py")
NL = chr(10)

MINI_PRD = NL.join([
    "project:",
    "  name: mini",
    "  status: 已定稿",
    "features:",
    "- id: FG-1",
    "  name: 核心",
    "  requirements:",
    "  - id: FR-1.1",
    "    statement: 迷你需求",
    "    priority: 必须",
])

CONFIG_AUTO_OPEN = NL.join([
    "paths:",
    "  output_dir: diy-output",
    "viewer:",
    "  auto_open: true",
])

FAKE_BROWSER = NL.join([
    "import io",
    "import os",
    "",
    "",
    "def open(url, *args, **kwargs):",
    "    # io.open：模块级 open 已遮蔽内置 open，用 io.open 防自我递归",
    "    with io.open(os.environ['FAKE_BROWSER_MARK'], 'w', encoding='utf-8') as f:",
    "        f.write(url)",
    "    return True",
])


class ViewerBrowserOpenTests(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        out = os.path.join(self.root, "diy-output")
        os.makedirs(out)
        with open(os.path.join(out, "prd.yaml"), "w", encoding="utf-8") as f:
            f.write(MINI_PRD)
        with open(os.path.join(self.root, "diy-coder.yaml"), "w", encoding="utf-8") as f:
            f.write(CONFIG_AUTO_OPEN)
        # 假 webbrowser：记录调用而非真开浏览器（PYTHONPATH 先于 site-packages 命中）
        self.fake_dir = os.path.join(self.root, "fake-browser")
        os.makedirs(self.fake_dir)
        with open(os.path.join(self.fake_dir, "webbrowser.py"), "w", encoding="utf-8") as f:
            f.write(FAKE_BROWSER)
        self.mark = os.path.join(self.root, "opened.txt")

    def tearDown(self):
        self.tmp.cleanup()

    def run_viewer(self, *extra):
        env = os.environ.copy()
        env["PYTHONPATH"] = os.pathsep.join(
            [self.fake_dir] + ([env["PYTHONPATH"]] if env.get("PYTHONPATH") else []))
        env["FAKE_BROWSER_MARK"] = self.mark
        return subprocess.run(
            [sys.executable, VIEWER, "--project-root", self.root, *extra],
            capture_output=True, text=True, encoding="utf-8", timeout=60, env=env,
        )

    def opened(self):
        return os.path.exists(self.mark)

    # trace: 2026-09-13 裁定——非交互环境（stdout 非 TTY）默认不打开浏览器
    def test_non_interactive_does_not_open(self):
        r = self.run_viewer()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse(self.opened())

    # trace: 2026-09-13 裁定——--open 在非交互环境显式强制打开
    def test_open_flag_forces_in_non_interactive(self):
        r = self.run_viewer("--open")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(self.opened())

    # trace: 2026-09-13 裁定——--no-open 一票否决（即使 --open 同时给出）
    def test_no_open_vetoes_force_open(self):
        r = self.run_viewer("--open", "--no-open")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse(self.opened())


def load_viewer_module():
    spec = importlib.util.spec_from_file_location("diy_viewer_open_under_test", VIEWER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class ShouldOpenUnitTests(unittest.TestCase):
    # trace: 2026-09-13 裁定——should_open 四要素组合（交互分支子进程测不到，此处覆盖）

    @classmethod
    def setUpClass(cls):
        cls.mod = load_viewer_module()

    def test_interactive_with_auto_open_opens(self):
        self.assertTrue(self.mod.should_open(True, False, False, True))

    def test_non_interactive_skips(self):
        self.assertFalse(self.mod.should_open(True, False, False, False))

    def test_auto_open_off_never_opens(self):
        self.assertFalse(self.mod.should_open(False, False, False, True))

    def test_force_open_wins_in_non_interactive(self):
        self.assertTrue(self.mod.should_open(False, False, True, False))

    def test_no_open_vetoes_everything(self):
        self.assertFalse(self.mod.should_open(True, True, True, True))


if __name__ == "__main__":
    unittest.main()
