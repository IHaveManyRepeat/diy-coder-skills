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
    # 脚本自身把 stdout/stderr 重配置为 UTF-8；父进程按同编码解码（Windows 默认 cp936 会崩）
    return subprocess.run(
        [sys.executable, str(VIEWER), "--project-root", str(root),
         "--no-open", *extra],
        capture_output=True, text=True, encoding="utf-8", timeout=60,
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


class InstanceHintTests(unittest.TestCase):
    # trace: architecture-4 修复（B5①）：忘传 --instance 时 stderr 一行可见诊断
    def setUp(self):
        self.root = make_root()
        self.out = self.root / "diy-output"

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_missing_instance_hint_when_mainline_empty(self):
        write_doc(self.out / "a", "prd.yaml")
        write_doc(self.out / "b", "sprint.yaml")
        result = run_viewer(self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("found instance dirs: a, b", result.stderr,
                      "主线空且存在实例目录时无提示")
        self.assertIn("--instance", result.stderr, "提示未给出参数形式")
        # 对照组：主线有 YAML 时不提示
        write_doc(self.out, "prd.yaml")
        result2 = run_viewer(self.root)
        self.assertNotIn("found instance dirs", result2.stderr)


class ExplicitPathTests(unittest.TestCase):
    # trace: customization-1 修复（B5②）：显式路径存在 → 按给定文件渲染，不做同名替换
    def setUp(self):
        self.root = make_root()
        self.out = self.root / "diy-output"
        write_doc(self.out, "prd.yaml")
        (self.out / "prd.yaml").write_text(
            "project:\n  name: MAINLINE-FIXTURE\n  status: final\n", encoding="utf-8")
        write_doc(self.out / "a", "prd.yaml")
        (self.out / "a" / "prd.yaml").write_text(
            "project:\n  name: INSTANCE-FIXTURE\n  status: final\n", encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def rendered(self):
        return (self.out / "a" / ".view" / "prd.html").read_text(encoding="utf-8")

    def test_explicit_mainline_path_wins_over_instance_same_name(self):
        result = run_viewer(self.root, "--instance", "a", str(self.out / "prd.yaml"))
        self.assertEqual(result.returncode, 0, result.stderr)
        html = self.rendered()
        self.assertIn("MAINLINE-FIXTURE", html, "给定路径内容未渲染（被同名实例文件替换）")
        self.assertNotIn("INSTANCE-FIXTURE", html, "实例同名文件静默替换了给定路径")
        self.assertIn("warning", result.stderr, "根外路径无警告")

    def test_absent_path_falls_back_to_basename(self):
        result = run_viewer(self.root, "--instance", "a", "no-such-dir/prd.yaml")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("INSTANCE-FIXTURE", self.rendered(),
                      "路径不存在时未回落 basename 查找")

    # trace: 对抗审查修复——显式路径非 .yaml 扩展（prd.yml）此前被 f"{stem}.yaml" 过滤静默丢弃
    def test_explicit_yml_extension_not_dropped(self):
        yml = self.out / "a" / "prd.yml"
        yml.write_text("project:\n  name: YML-FIXTURE\n  status: final\n", encoding="utf-8")
        result = run_viewer(self.root, "--instance", "a", str(yml))
        self.assertEqual(result.returncode, 0, result.stderr)
        html = self.rendered()
        self.assertIn("YML-FIXTURE", html, "显式 .yml 文件被静默丢弃")
        self.assertNotIn("INSTANCE-FIXTURE", html, "显式 .yml 未覆盖同名条目")


class InstanceNameWhitelistTests(unittest.TestCase):
    # trace: 对抗审查修复——末字符禁点（Windows 尾点目录折叠 b. ≡ b），非法名一行报错不裸栈
    def setUp(self):
        self.root = make_root()
        self.out = self.root / "diy-output"
        write_doc(self.out, "prd.yaml")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_trailing_dot_instance_rejected(self):
        for bad in ("b.", "b..", "b.c."):
            with self.subTest(instance=bad):
                result = run_viewer(self.root, "--instance", bad)
                self.assertNotEqual(result.returncode, 0, f"{bad!r} 未被拒绝")
                self.assertNotIn("Traceback", result.stderr)
                self.assertIn("非法实例名", result.stderr)

    def test_legal_names_still_accepted(self):
        for good in ("a", "ab", "a.b", "a_b-c9", "9x"):
            with self.subTest(instance=good):
                write_doc(self.out / good, "prd.yaml")
                result = run_viewer(self.root, "--instance", good)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertNotIn("非法实例名", result.stderr)


if __name__ == "__main__":
    unittest.main()
