# trace: S-10 AC-10.1 AC-10.2 AC-10.3 AC-10.4 TC-10.1.1 TC-10.2.1 TC-10.3.1 TC-10.4.1
"""runner.py 循环编排器测试。全部用任务桩（stub_claude.py）替代真实 claude spawn。

- TC-10.1.1 全量跑到终态且无人工输入（integration）
- TC-10.2.1 中断后断点续跑不重复执行（unit，metamorphic）
- TC-10.3.1 连续失败重试 2 次封顶后继续（unit，boundary）
- TC-10.4.1 全程串行，任一时刻至多一个 in-progress（e2e，state-transition）
"""
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
RUNNER = HERE.parent / "runner.py"
STUB = HERE / "stub_claude.py"

TERMINAL = ("done", "blocked")


def make_fixture(statuses):
    """建夹具项目根：diy-coder.yaml + diy-output/sprint.yaml（status final）。"""
    root = Path(tempfile.mkdtemp(prefix="tmp-tc10-"))
    out = root / "diy-output"
    out.mkdir(parents=True)
    (root / "diy-coder.yaml").write_text(
        "paths:\n  output_dir: diy-output\n", encoding="utf-8"
    )
    doc = {
        "project": {
            "name": "fixture",
            "status": "final",
            "created": "2026-09-09",
            "updated": "2026-09-09",
        },
        "tasks": [
            {"story": story, "status": status, "test_refs": []}
            for story, status in statuses.items()
        ],
    }
    sprint = out / "sprint.yaml"
    sprint.write_text(
        yaml.safe_dump(doc, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    return root, sprint


def run_runner(root, env_extra, timeout=60):
    env = {**os.environ, **env_extra}
    return subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--project-root",
            str(root),
            "--claude-cmd",
            sys.executable,
            str(STUB),
        ],
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
        stdin=subprocess.DEVNULL,
    )


def read_log(path):
    if not Path(path).exists():
        return []
    return Path(path).read_text(encoding="utf-8").splitlines()


def read_tasks(sprint):
    doc = yaml.safe_load(Path(sprint).read_text(encoding="utf-8"))
    return {t["story"]: t for t in doc["tasks"]}


class TC_10_1_1_FullRunNoStdin(unittest.TestCase):
    # trace: S-10 AC-10.1 TC-10.1.1
    def setUp(self):
        self.root, self.sprint = make_fixture(
            {"S-1": "pending", "S-2": "pending", "S-3": "pending"}
        )
        self.log = self.root / "calls.log"
        self.sentinel = self.root / "stdin-sentinel"

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_all_terminal_and_no_stdin(self):
        result = run_runner(
            self.root,
            {
                "DIY_STUB_ROUTING": "S-1:done,S-2:blocked,S-3:done",
                "DIY_STUB_LOG": str(self.log),
                "DIY_STUB_SPRINT": str(self.sprint),
                "DIY_STUB_SENTINEL": str(self.sentinel),
            },
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        tasks = read_tasks(self.sprint)
        for story in ("S-1", "S-2", "S-3"):
            self.assertIn(tasks[story]["status"], TERMINAL, story)
        self.assertFalse(self.sentinel.exists(), "runner 向子进程传入了 stdin 数据")
        self.assertEqual(len(read_log(self.log)), 3)


class TC_10_2_1_ResumeNoRerun(unittest.TestCase):
    # trace: S-10 AC-10.2 TC-10.2.1
    def setUp(self):
        self.root, self.sprint = make_fixture(
            {"S-1": "done", "S-2": "done", "S-3": "pending"}
        )
        self.log = self.root / "calls.log"

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_done_tasks_not_reexecuted(self):
        env = {
            "DIY_STUB_ROUTING": "S-3:done",
            "DIY_STUB_LOG": str(self.log),
            "DIY_STUB_SPRINT": str(self.sprint),
        }
        first = run_runner(self.root, env)
        self.assertEqual(first.returncode, 0, first.stderr)
        log_lines = read_log(self.log)
        self.assertEqual(log_lines, ["S-3 done"], f"done 任务被重复执行: {log_lines}")
        self.assertEqual(read_tasks(self.sprint)["S-3"]["status"], "done")

        second = run_runner(self.root, env)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(
            len(read_log(self.log)), 1, "全终态重跑产生了新调用（非幂等）"
        )


class TC_10_3_1_RetryCapThenContinue(unittest.TestCase):
    # trace: S-10 AC-10.3 TC-10.3.1
    def setUp(self):
        self.root, self.sprint = make_fixture(
            {"S-1": "pending", "S-2": "pending"}
        )
        self.log = self.root / "calls.log"

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_retry_exactly_twice_then_blocked_and_continue(self):
        result = run_runner(
            self.root,
            {
                "DIY_STUB_ROUTING": "S-1:fail,S-2:done",
                "DIY_STUB_LOG": str(self.log),
                "DIY_STUB_SPRINT": str(self.sprint),
            },
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = [line for line in read_log(self.log) if line.startswith("S-1")]
        self.assertEqual(
            len(calls), 3, f"应恰执行 3 次（初次+2 重试），实际 {len(calls)}: {calls}"
        )
        tasks = read_tasks(self.sprint)
        self.assertEqual(tasks["S-1"]["status"], "blocked")
        self.assertIn("重试", tasks["S-1"].get("blocked_reason", ""))
        self.assertEqual(tasks["S-2"]["status"], "done", "封顶后未继续后续任务")


class TC_10_4_1_StrictlySerial(unittest.TestCase):
    # trace: S-10 AC-10.4 TC-10.4.1
    def setUp(self):
        self.root, self.sprint = make_fixture(
            {"S-1": "pending", "S-2": "pending"}
        )
        self.log = self.root / "calls.log"

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_at_most_one_in_progress(self):
        samples = []
        stop = threading.Event()

        def scan():
            while not stop.is_set():
                try:
                    tasks = read_tasks(self.sprint)
                    samples.append(
                        sum(1 for t in tasks.values() if t["status"] == "in-progress")
                    )
                except (OSError, yaml.YAMLError):
                    pass
                time.sleep(0.05)

        watcher = threading.Thread(target=scan)
        watcher.start()
        try:
            result = run_runner(
                self.root,
                {
                    "DIY_STUB_ROUTING": "S-1:done,S-2:done",
                    "DIY_STUB_LOG": str(self.log),
                    "DIY_STUB_SPRINT": str(self.sprint),
                    "DIY_STUB_SLEEP": "0.3",
                },
                timeout=120,
            )
        finally:
            stop.set()
            watcher.join()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(samples, "扫描线程未采到任何样本")
        self.assertLessEqual(
            max(samples), 1, f"任一时刻出现 >1 个 in-progress: max={max(samples)}"
        )
        tasks = read_tasks(self.sprint)
        self.assertEqual(tasks["S-1"]["status"], "done")
        self.assertEqual(tasks["S-2"]["status"], "done")


class TC_10_1_2_MissingClaudeCmd(unittest.TestCase):
    # trace: S-10 AC-10.1 TC-10.1.2
    def setUp(self):
        self.root, self.sprint = make_fixture({"S-1": "pending"})

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_missing_cli_reports_one_line(self):
        result = subprocess.run(
            [
                sys.executable,
                str(RUNNER),
                "--project-root",
                str(self.root),
                "--claude-cmd",
                "definitely-not-a-real-binary-xyz",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdin=subprocess.DEVNULL,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("Traceback", result.stderr)
        self.assertIn("[runner]", result.stderr)
        self.assertIn("definitely-not-a-real-binary-xyz", result.stderr)


class TC_10_1_2_CorruptSprintGate(unittest.TestCase):
    # trace: S-10 AC-10.1 TC-10.1.2
    def setUp(self):
        self.root, self.sprint = make_fixture({"S-1": "pending"})

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def run_gate(self):
        return subprocess.run(
            [sys.executable, str(RUNNER), "--project-root", str(self.root),
             "--claude-cmd", sys.executable, str(STUB)],
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", stdin=subprocess.DEVNULL, timeout=60,
        )

    def test_unparsable_sprint_reports_one_line(self):
        # 对抗审查 R3：sprint.yaml 语法损坏必须一行报错，不落 yaml 裸栈
        self.sprint.write_text("project: [broken" + chr(10), encoding="utf-8")
        r = self.run_gate()
        self.assertNotEqual(r.returncode, 0)
        self.assertNotIn("Traceback", r.stderr)
        self.assertIn("[runner]", r.stderr)

    def test_non_map_project_reports_one_line(self):
        # 对抗审查 R3：project 节点形状异常（列表）同样一行报错
        self.sprint.write_text(
            "project:" + chr(10) + "  - not-a-map" + chr(10), encoding="utf-8")
        r = self.run_gate()
        self.assertNotEqual(r.returncode, 0)
        self.assertNotIn("Traceback", r.stderr)
        self.assertIn("[runner]", r.stderr)


if __name__ == "__main__":
    unittest.main()
