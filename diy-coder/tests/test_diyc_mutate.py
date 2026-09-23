# -*- coding: utf-8 -*-
"""diyc mutate 沙箱机制测试（C·9；迁移计划 §五 阶段 C 第 9 项）。

覆盖：--tool 缺失拒绝 / 沙箱建成即销毁（零残留）/ --keep 保留 / --sandbox 显式给址 /
已存在路径拒绝 / {scope} 占位符替换 / 无占位符却在场的警告 / --full 全量 /
命令非 0 退出不判机制失败 / 超时被杀 / 工作区零污染 / 沙箱落项目内的警告 /
真工具端到端（cosmic-ray 在场时；不在场跳过）。

**ok 的语义**：描述**沙箱机制**是否走通，不描述变异结果——变异工具用非 0 退出码
表达「有存活体」属正常业务结果，把 rc 当机制失败会让每次有 survivors 的运行都红灯。
`rc` 与 `output_tail` 原样进回执，解释归调用方（`diy-augment`）。

夹具 `tests/fixtures/mutation_smoke/` 同时供真工具用例使用（微型项目：calc.py +
check_add.py + pytest.ini + config.toml），它自带收集规则故不被主项目 pytest 收集。
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)  # import diyc_fixture

import diyc_fixture as fx  # noqa: E402

DIYC = os.path.join(HERE, "..", "skills", "diy-tools", "scripts", "diyc.py")
FIXTURE = os.path.join(HERE, "fixtures", "mutation_smoke")

# 桩命令：立刻返回、输出定长文本——被测对象是沙箱行为，不是变异算法
STUB_TOOL = 'python -c "print(\'killed 9 total 11\')"'


def run_mutate(root, *args, timeout=300):
    return subprocess.run(
        [sys.executable, DIYC, "mutate", *args, "--project-root", str(root), "--json"],
        capture_output=True, text=True, encoding="utf-8", timeout=timeout,
        stdin=subprocess.DEVNULL)


def jload(proc):
    return json.loads(proc.stdout)


def codes(result):
    return {x["code"] for x in result["violations"]}


class MutateTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="diyc-mutate-t-")
        fx.make_project(self.root)
        self.marker = os.path.join(self.root, "MARKER.txt")
        with open(self.marker, "w", encoding="utf-8") as f:
            f.write("marker\n")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    # ------------------------------------------------------------ 参数面

    def test_tool_missing_rejected(self):
        result = jload(run_mutate(self.root))
        self.assertFalse(result["ok"])
        self.assertIn("TOOL_NOT_GIVEN", codes(result))

    def test_sandbox_exists_rejected(self):
        occupied = tempfile.mkdtemp(prefix="diyc-mutate-occupied-")
        self.addCleanup(shutil.rmtree, occupied, ignore_errors=True)
        result = jload(run_mutate(
            self.root, "--tool", STUB_TOOL, "--sandbox", occupied))
        self.assertFalse(result["ok"])
        self.assertIn("SANDBOX_EXISTS", codes(result))
        self.assertTrue(os.path.isdir(occupied), "拒绝路径不得被动过")

    def test_full_mode_reported(self):
        result = jload(run_mutate(self.root, "--tool", STUB_TOOL, "--full"))
        self.assertTrue(result["ok"])
        self.assertEqual("full", result["mode"])
        self.assertIsNone(result["scope"])

    def test_full_flag_silences_default_warning(self):
        """不给 --full 却在全量跑 → 提醒；给了 → 不提醒。"""
        warned = jload(run_mutate(self.root, "--tool", STUB_TOOL))
        quiet = jload(run_mutate(self.root, "--tool", STUB_TOOL, "--full"))
        self.assertTrue(any("全量变异执行" in w for w in warned["warnings"]))
        self.assertFalse(any("全量变异执行" in w for w in quiet["warnings"]))

    # ------------------------------------------------------------ {scope} 占位符

    def test_scope_placeholder_substituted(self):
        tool = 'python -c "print(\'SCOPE=[{scope}]\')"'
        result = jload(run_mutate(
            self.root, "--tool", tool, "--scope", "src/a.py", "--scope", "src/b.py"))
        self.assertTrue(result["ok"])
        self.assertEqual(["src/a.py", "src/b.py"], result["scope"])
        self.assertEqual(2, result["counts"]["scope_files"])
        self.assertIn("SCOPE=[src/a.py src/b.py]", " ".join(result["output_tail"]))

    def test_scope_without_placeholder_warns(self):
        result = jload(run_mutate(
            self.root, "--tool", STUB_TOOL, "--scope", "src/a.py"))
        self.assertTrue(any("占位符" in w for w in result["warnings"]))

    def test_scope_backslashes_normalised(self):
        tool = 'python -c "print(\'[{scope}]\')"'
        result = jload(run_mutate(
            self.root, "--tool", tool, "--scope", "src\\win\\path.py"))
        self.assertEqual(["src/win/path.py"], result["scope"])
        self.assertIn("[src/win/path.py]", " ".join(result["output_tail"]))

    # ------------------------------------------------------------ 沙箱生命周期

    def test_sandbox_created_then_destroyed(self):
        result = jload(run_mutate(self.root, "--tool", STUB_TOOL, "--full"))
        self.assertTrue(result["ok"])
        self.assertFalse(result["sandbox_kept"])
        self.assertFalse(os.path.exists(result["sandbox"]),
                         "默认跑完即销毁，零残留")

    def test_keep_preserves_sandbox(self):
        result = jload(run_mutate(
            self.root, "--tool", STUB_TOOL, "--full", "--keep"))
        sandbox = result["sandbox"]
        self.addCleanup(shutil.rmtree, sandbox, ignore_errors=True)
        self.assertTrue(result["sandbox_kept"])
        self.assertTrue(os.path.isdir(sandbox))
        self.assertTrue(os.path.isfile(os.path.join(sandbox, "MARKER.txt")),
                        "副本须含项目文件")

    def test_sandbox_excludes_vcs_and_caches(self):
        os.makedirs(os.path.join(self.root, "__pycache__"), exist_ok=True)
        result = jload(run_mutate(
            self.root, "--tool", STUB_TOOL, "--full", "--keep"))
        sandbox = result["sandbox"]
        self.addCleanup(shutil.rmtree, sandbox, ignore_errors=True)
        self.assertFalse(os.path.exists(os.path.join(sandbox, "__pycache__")))

    def test_explicit_sandbox_path_used(self):
        target = os.path.join(self.root, "..", "diyc-mutate-explicit-%d" % os.getpid())
        target = os.path.abspath(target)
        self.addCleanup(shutil.rmtree, target, ignore_errors=True)
        result = jload(run_mutate(
            self.root, "--tool", STUB_TOOL, "--full",
            "--sandbox", target, "--keep"))
        self.assertTrue(result["ok"])
        self.assertEqual(target.replace("\\", "/"), result["sandbox"])

    def test_sandbox_in_project_warns(self):
        inside = os.path.join(self.root, "sandbox-in")
        result = jload(run_mutate(
            self.root, "--tool", STUB_TOOL, "--full",
            "--sandbox", inside, "--keep"))
        self.addCleanup(shutil.rmtree, inside, ignore_errors=True)
        self.assertTrue(result["workspace"]["sandbox_in_project"])
        self.assertTrue(any("项目内" in w for w in result["warnings"]))

    # ------------------------------------------------------------ 命令结果面

    def test_nonzero_rc_keeps_mechanism_ok(self):
        """命令非 0 退出是变异工具的正常业务词汇（有存活体），机制仍算走通。"""
        result = jload(run_mutate(
            self.root, "--tool", "python -c \"import sys; sys.exit(1)\"", "--full"))
        self.assertEqual(1, result["rc"])
        self.assertTrue(result["ok"], "ok 描述机制，不描述变异结果")
        self.assertEqual([], result["violations"])

    def test_timeout_killed_and_reported(self):
        result = jload(run_mutate(
            self.root, "--tool", "python -c \"import time; time.sleep(30)\"",
            "--full", "--timeout", "2"))
        self.assertTrue(result["timed_out"])
        self.assertFalse(result["ok"])
        self.assertIn("MUTATE_TIMEOUT", codes(result))

    def test_output_tail_captured(self):
        result = jload(run_mutate(self.root, "--tool", STUB_TOOL, "--full"))
        self.assertTrue(any("killed 9 total 11" in ln for ln in result["output_tail"]))
        self.assertGreater(result["counts"]["output_lines"], 0)

    # ------------------------------------------------------------ 工作区保护

    def test_workspace_untouched_when_command_writes_in_sandbox(self):
        """命令在副本里改文件，工作区必须零变化。"""
        tool = 'python -c "open(\'MARKER.txt\',\'w\').write(\'mutated\')"'
        with open(self.marker, encoding="utf-8") as f:
            before = f.read()
        result = jload(run_mutate(self.root, "--tool", tool, "--full"))
        self.assertTrue(result["ok"])
        with open(self.marker, encoding="utf-8") as f:
            self.assertEqual(before, f.read(), "工作区文件不得被副本内的写动作影响")


@unittest.skipUnless(shutil.which("cosmic-ray"), "cosmic-ray 不在场（Python 变异工具，跨平台）")
class RealToolTests(unittest.TestCase):
    """真工具端到端：沙箱里跑 cosmic-ray，验证副本能承载真变异链路。

    夹具是微型项目（calc.py 的 `+` 是唯一靶点），秒级完成——完整项目上的变异
    耗时以小时计，不适合进回归套件（那是发版前的全量跑，见迁移计划 §五 C·9）。
    """

    def test_cosmic_ray_runs_in_sandbox(self):
        tool = ("cosmic-ray init config.toml session.sqlite && "
                "cosmic-ray exec config.toml session.sqlite && "
                "cosmic-ray dump session.sqlite")
        result = jload(run_mutate(FIXTURE, "--tool", tool, "--full"))
        self.assertTrue(result["ok"], result["violations"])
        self.assertEqual(0, result["rc"])
        rows = [json.loads(ln) for ln in result["output_tail"]
                if ln.strip().startswith("[")]
        self.assertGreater(len(rows), 0, "须拿到变异体记录")
        outcomes = [r[1].get("test_outcome") for r in rows
                    if isinstance(r, list) and len(r) == 2]
        self.assertIn("killed", outcomes, "`+` 变异成 `-` 必须被杀")


if __name__ == "__main__":
    unittest.main()
