# trace: S-16 AC-16.1 AC-16.2 TC-16.1.1 TC-16.2.1
"""实例机制测试（FR-4.5/D-9：目录即实例 + 激活参数解析 output_dir）。

- TC-16.1.1 实例隔离：实例 a 参数执行 skill 流程（viewer 真实渲染），实例 b 与主线零变化
- TC-16.2.1 主线兼容：无实例参数走主线平铺路径，不创建实例子目录
"""
import hashlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIEWER = HERE.parent / "skills" / "diy-viewer" / "scripts" / "viewer.py"

MINI_DOC = """project:
  name: fixture
  status: final
  created: '2026-09-09'
  updated: '2026-09-09'
"""


def make_root():
    # trace: S-16 AC-16.1 夹具根：diy-coder.yaml（auto_open 关闭，无头）
    root = Path(tempfile.mkdtemp(prefix="tmp-tc16-"))
    (root / "diy-coder.yaml").write_text(
        "paths:\n  output_dir: diy-output\nviewer:\n  auto_open: false\n",
        encoding="utf-8")
    return root


def write_doc(out_dir, name):
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / name).write_text(MINI_DOC, encoding="utf-8")


def run_viewer(root, *extra):
    return subprocess.run(
        [sys.executable, str(VIEWER), "--project-root", str(root),
         "--no-open", *extra],
        capture_output=True, text=True, timeout=60,
        stdin=subprocess.DEVNULL)


def snapshot(base, skip):
    # trace: S-16 AC-16.1 清单+内容指纹（相对路径→sha256），skip 为排除子树
    out = {}
    for f in sorted(base.rglob("*")):
        if f.is_file():
            rel = f.relative_to(base).as_posix()
            if rel != skip and not rel.startswith(skip + "/"):
                out[rel] = hashlib.sha256(f.read_bytes()).hexdigest()
    return out


class TC_16_1_1_InstanceIsolation(unittest.TestCase):
    # trace: S-16 AC-16.1 TC-16.1.1
    def setUp(self):
        self.root = make_root()
        self.out = self.root / "diy-output"
        write_doc(self.out, "prd.yaml")
        write_doc(self.out / "a", "prd.yaml")
        write_doc(self.out / "a", "sprint.yaml")
        write_doc(self.out / "b", "prd.yaml")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_instance_run_isolated(self):
        before = snapshot(self.out, "a")
        result = run_viewer(self.root, "--instance", "a")
        self.assertEqual(result.returncode, 0, result.stderr)
        view_a = self.out / "a" / ".view"
        self.assertTrue((view_a / "index.html").exists(),
                        "实例 a 渲染缺失（流程未生效，零变化断言空洞）")
        self.assertTrue((view_a / "prd.html").exists(), "实例 a 页面缺失")
        self.assertEqual(before, snapshot(self.out, "a"),
                         "实例 b 或主线目录清单/内容发生变化")


class TC_16_2_1_MainlineCompat(unittest.TestCase):
    # trace: S-16 AC-16.2 TC-16.2.1
    def setUp(self):
        self.root = make_root()
        self.out = self.root / "diy-output"
        write_doc(self.out, "prd.yaml")
        write_doc(self.out, "sprint.yaml")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_no_instance_flat_path_unchanged(self):
        before = snapshot(self.out, ".view")
        result = run_viewer(self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.out / ".view" / "index.html").exists(),
                        "主线平铺渲染缺失")
        self.assertEqual(before, snapshot(self.out, ".view"),
                         "主线 YAML 内容被修改（零迁移违约）")
        subdirs = {d.name for d in self.out.iterdir() if d.is_dir()}
        self.assertEqual(subdirs, {".view"},
                         "无实例参数却创建实例子目录: {}".format(subdirs))


if __name__ == "__main__":
    unittest.main()
