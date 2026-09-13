# trace: S-10 AC-10.1 AC-10.2 AC-10.3 AC-10.4 TC-10.1.1 TC-10.2.1 TC-10.3.1 TC-10.4.1
#        FR-4.5 D-9（findings: diy-build-loop/enhancement-1、diy-sprint/enhancement-2）
"""runner.py 循环编排器测试。全部用任务桩（stub_claude.py）替代真实 claude spawn。

- TC-10.1.1 全量跑到终态且无人工输入（integration）
- TC-10.2.1 中断后断点续跑不重复执行（unit，metamorphic）
- TC-10.3.1 连续失败重试 2 次封顶后继续（unit，boundary）
- TC-10.4.1 全程串行，任一时刻至多一个 in-progress（e2e，state-transition）
- TC-Instance 实例模式（FR-4.5/D-9）：<output_dir>/<name>/sprint.yaml 读写、
  prompt 携带 --instance、非法名拒绝、无 --instance 主线回归
- TC-Augment 编码后补测接线：done 触发一次 diy-augment spawn，blocked 不触发；
  补测会话只写 augment 字段（窄写权，status 零写回）；--skip-augment / --augment-only /
  --reopen-failed 三开关；补测汇总行
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


def sprint_doc(statuses):
    return {
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


def write_sprint(path, statuses):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(sprint_doc(statuses), allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return path


def make_fixture(statuses, instance=None):
    """建夹具项目根：diy-coder.yaml + diy-output[/<instance>]/sprint.yaml（status final）。"""
    root = Path(tempfile.mkdtemp(prefix="tmp-tc10-"))
    (root / "diy-coder.yaml").write_text(
        "paths:\n  output_dir: diy-output\n", encoding="utf-8"
    )
    out = (root / "diy-output" / instance) if instance else (root / "diy-output")
    sprint = write_sprint(out / "sprint.yaml", statuses)
    return root, sprint


def run_runner(root, env_extra, timeout=60, runner_args=(), stub=None):
    # 编码确定性：PYTHONUTF8=1 让 runner（及孙进程桩）stdio 走 UTF-8，
    # 父端显式 utf-8 解码——不依赖宿主 code page（Windows 中文默认 GBK，
    # 父/子解码器偶发不一致会击穿中文断言，2026-09-13 实撞 flaky）
    env = {**os.environ, **env_extra, "PYTHONUTF8": "1"}
    return subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--project-root",
            str(root),
            *runner_args,
            "--claude-cmd",
            sys.executable,
            str(stub or STUB),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        env=env,
        stdin=subprocess.DEVNULL,
    )


# argv 记录代理：先记下子会话命令行（验证 prompt 内容），再委托给真实任务桩
SPY_SRC = (
    "import os, runpy, sys\n"
    "with open(os.environ['DIY_STUB_ARGV'], 'a', encoding='utf-8') as fh:\n"
    "    fh.write('\\n'.join(sys.argv[1:]) + '\\n')\n"
    "runpy.run_path(os.environ['DIY_STUB_PATH'], run_name='__main__')\n"
)


def make_spy(root):
    spy = root / "spy_claude.py"
    spy.write_text(SPY_SRC, encoding="utf-8")
    return spy


def read_log(path):
    if not Path(path).exists():
        return []
    return Path(path).read_text(encoding="utf-8").splitlines()


def read_tasks(sprint):
    doc = yaml.safe_load(Path(sprint).read_text(encoding="utf-8"))
    return {t["story"]: t for t in doc["tasks"]}


def patch_augment(sprint, story, value):
    """夹具预置补测结论（模拟 diy-augment 已留痕的历史状态）。"""
    doc = yaml.safe_load(Path(sprint).read_text(encoding="utf-8"))
    for t in doc["tasks"]:
        if t["story"] == story:
            t["augment"] = value
    Path(sprint).write_text(
        yaml.safe_dump(doc, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )


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
        lines = read_log(self.log)
        aug = [ln for ln in lines if ln.endswith(" augment")]
        self.assertEqual(len(lines) - len(aug), 3)
        self.assertEqual(len(aug), 2, f"2 个 done 任务应各触发一次补测: {lines}")


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
        self.assertEqual(
            log_lines, ["S-3 done", "S-3 augment"], f"done 任务被重复执行: {log_lines}"
        )
        self.assertEqual(read_tasks(self.sprint)["S-3"]["status"], "done")

        second = run_runner(self.root, env)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(
            len(read_log(self.log)), 2, "全终态重跑产生了新调用（非幂等）"
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


class TC_Instance_Mode(unittest.TestCase):
    # trace: FR-4.5 D-9（findings: diy-build-loop/enhancement-1、diy-sprint/enhancement-2）
    # 实例模式：--instance 从 <output_dir>/<name>/sprint.yaml 读任务并写回同一路径
    def setUp(self):
        self.root, self.sprint = make_fixture({"S-1": "pending"}, instance="case-a")
        self.log = self.root / "calls.log"

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def env(self):
        return {
            "DIY_STUB_ROUTING": "S-1:done",
            "DIY_STUB_LOG": str(self.log),
            "DIY_STUB_SPRINT": str(self.sprint),
        }

    def test_reads_and_writes_instance_sprint(self):
        # 主线 sprint 全终态：若 runner 误读主线则零 spawn（日志为空）、实例文件不动；
        # 出现 1 次 spawn 即证明任务来自实例路径，终态回写也只落在实例文件
        main_sprint = write_sprint(
            self.root / "diy-output" / "sprint.yaml", {"S-1": "done"}
        )
        result = run_runner(
            self.root, self.env(), runner_args=("--instance", "case-a")
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            read_log(self.log), ["S-1 done", "S-1 augment"], "未从实例 sprint 读到待办任务"
        )
        self.assertEqual(read_tasks(self.sprint)["S-1"]["status"], "done")
        self.assertEqual(read_tasks(main_sprint)["S-1"]["status"], "done")
        self.assertIn("[runner] S-1 → done", result.stdout)

    def test_prompt_carries_instance_flag(self):
        spy = make_spy(self.root)
        argv_log = self.root / "argv.log"
        result = run_runner(
            self.root,
            {**self.env(), "DIY_STUB_ARGV": str(argv_log), "DIY_STUB_PATH": str(STUB)},
            runner_args=("--instance", "case-a"),
            stub=spy,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        argv_text = Path(argv_log).read_text(encoding="utf-8")
        self.assertIn("--instance case-a", argv_text, "子会话 prompt 未携带实例激活参数")
        self.assertIn("case-a", argv_text)


class TC_Instance_InvalidName(unittest.TestCase):
    # trace: FR-4.5 D-9 实例名白名单（字母数字开头和结尾）：非法名一行报错 + 非零退出，不 spawn。
    # "a." 与 "a\n" 为对抗审查修复后锁定（尾点在 Windows 目录名折叠 → 破坏实例隔离）
    def setUp(self):
        self.root, self.sprint = make_fixture({"S-1": "pending"})
        self.log = self.root / "calls.log"

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_invalid_instance_rejected_no_spawn(self):
        for bad in ("../escape", "bad/name", ".hidden", "sub\\dir", "a b", "a.", "a\n"):
            with self.subTest(instance=bad):
                result = run_runner(
                    self.root,
                    {
                        "DIY_STUB_ROUTING": "S-1:done",
                        "DIY_STUB_LOG": str(self.log),
                        "DIY_STUB_SPRINT": str(self.sprint),
                    },
                    runner_args=("--instance", bad),
                )
                self.assertNotEqual(result.returncode, 0, f"{bad!r} 未被拒绝")
                self.assertNotIn("Traceback", result.stderr)
                self.assertIn("[runner]", result.stderr)
                self.assertIn("非法实例名", result.stderr)
                lines = [ln for ln in result.stderr.splitlines() if ln.strip()]
                self.assertEqual(len(lines), 1, f"应一行报错，实际: {result.stderr}")
                self.assertFalse(self.log.exists(), f"{bad!r} 被拒后仍 spawn 了子会话")
                self.assertEqual(read_tasks(self.sprint)["S-1"]["status"], "pending")


class TC_Instance_MainlineUnchanged(unittest.TestCase):
    # trace: FR-4.5 D-9 无 --instance 主线回归：路径与 prompt 均等价现状
    def setUp(self):
        self.root, self.sprint = make_fixture({"S-1": "pending"})
        self.log = self.root / "calls.log"

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_no_instance_flag_stays_mainline(self):
        spy = make_spy(self.root)
        argv_log = self.root / "argv.log"
        result = run_runner(
            self.root,
            {
                "DIY_STUB_ROUTING": "S-1:done",
                "DIY_STUB_LOG": str(self.log),
                "DIY_STUB_SPRINT": str(self.sprint),
                "DIY_STUB_ARGV": str(argv_log),
                "DIY_STUB_PATH": str(STUB),
            },
            stub=spy,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(read_tasks(self.sprint)["S-1"]["status"], "done")
        self.assertEqual(read_log(self.log), ["S-1 done", "S-1 augment"])
        argv_text = Path(argv_log).read_text(encoding="utf-8")
        self.assertNotIn("--instance", argv_text, "主线 prompt 混入了实例参数")
        self.assertIn(
            "运行 diy-build-loop skill 处理任务 S-1：", argv_text,
            "主线 prompt 前缀不再等价现状",
        )


class TC_Augment_AfterDone(unittest.TestCase):
    # trace: 2026-09-13 裁定——编码后补测接线：done 触发一次 diy-augment spawn，
    # blocked 不触发；补测会话窄写权：只写 augment 字段，任务 status 零写回
    def setUp(self):
        self.root, self.sprint = make_fixture(
            {"S-1": "pending", "S-2": "pending"}
        )
        self.log = self.root / "calls.log"

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def env(self):
        return {
            "DIY_STUB_ROUTING": "S-1:done,S-2:blocked",
            "DIY_STUB_LOG": str(self.log),
            "DIY_STUB_SPRINT": str(self.sprint),
        }

    def test_done_triggers_augment_blocked_does_not(self):
        result = run_runner(self.root, self.env())
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = read_log(self.log)
        self.assertIn("S-1 done", lines)
        self.assertIn("S-1 augment", lines)
        self.assertIn("S-2 blocked", lines)
        self.assertNotIn("S-2 augment", lines, "blocked 任务不应触发补测")
        self.assertIn("[runner] S-1 补测轮通过", result.stdout)
        self.assertNotIn("S-2 补测轮", result.stdout, "blocked 任务不应出现补测行")
        tasks = read_tasks(self.sprint)
        self.assertEqual(tasks["S-1"]["status"], "done", "补测会话篡改了任务状态")
        self.assertEqual(tasks["S-1"]["augment"], "pass", "补测结论未留痕")
        self.assertNotIn("augment", tasks["S-2"], "blocked 任务不应有补测结论")
        self.assertIn("补测汇总：通过 1 / 待裁断 0", result.stdout)

    def test_augment_prompt_targets_completed_story(self):
        spy = make_spy(self.root)
        argv_log = self.root / "argv.log"
        result = run_runner(
            self.root,
            {**self.env(), "DIY_STUB_ARGV": str(argv_log), "DIY_STUB_PATH": str(STUB)},
            stub=spy,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        argv_text = Path(argv_log).read_text(encoding="utf-8")
        self.assertIn("运行 diy-augment skill 对已完成任务 S-1", argv_text)
        self.assertNotIn("运行 diy-augment skill 对已完成任务 S-2", argv_text)


class TC_Augment_SkipFlag(unittest.TestCase):
    # --skip-augment：主循环本轮不补测（不留痕 = 之后 --augment-only 可补跑）
    def setUp(self):
        self.root, self.sprint = make_fixture({"S-1": "pending"})
        self.log = self.root / "calls.log"

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_skip_flag_no_augment_spawn(self):
        result = run_runner(
            self.root,
            {
                "DIY_STUB_ROUTING": "S-1:done",
                "DIY_STUB_LOG": str(self.log),
                "DIY_STUB_SPRINT": str(self.sprint),
            },
            runner_args=("--skip-augment",),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(read_log(self.log), ["S-1 done"], "skip 后仍 spawn 了补测")
        tasks = read_tasks(self.sprint)
        self.assertEqual(tasks["S-1"]["status"], "done")
        self.assertNotIn("augment", tasks["S-1"])
        self.assertIn("补测汇总：通过 0 / 待裁断 0 / 跳过 0 / 未跑 1", result.stdout)


class TC_Augment_Only(unittest.TestCase):
    # --augment-only：只补跑 done 且无结论的任务（pass/skip 跳过、fail 重跑覆盖结论）；
    # 主循环零驱动（pending 任务不动）
    def setUp(self):
        self.root, self.sprint = make_fixture(
            {"S-1": "done", "S-2": "done", "S-3": "pending", "S-4": "done"}
        )
        patch_augment(self.sprint, "S-1", "pass")
        patch_augment(self.sprint, "S-4", "skip")
        self.log = self.root / "calls.log"

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def env(self):
        return {
            "DIY_STUB_ROUTING": "S-1:done,S-3:done",
            "DIY_STUB_LOG": str(self.log),
            "DIY_STUB_SPRINT": str(self.sprint),
        }

    def test_only_unverified_done_tasks(self):
        result = run_runner(self.root, self.env(), runner_args=("--augment-only",))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            read_log(self.log), ["S-2 augment"],
            "应只补跑 S-2（S-1 已通过、S-4 缺工具跳过、S-3 未完成）",
        )
        tasks = read_tasks(self.sprint)
        self.assertEqual(tasks["S-2"]["augment"], "pass")
        self.assertEqual(tasks["S-1"]["augment"], "pass")
        self.assertEqual(tasks["S-3"]["status"], "pending", "--augment-only 驱动了主循环")
        self.assertIn("补测汇总：通过 2 / 待裁断 0 / 跳过 1 / 未跑 0", result.stdout)

    def test_failed_task_rerun_overwrites(self):
        # 裁断修复后重跑：fail 结论被新结论覆盖
        patch_augment(self.sprint, "S-2", "fail")
        result = run_runner(self.root, self.env(), runner_args=("--augment-only",))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(sorted(read_log(self.log)), ["S-2 augment"])
        self.assertEqual(
            read_tasks(self.sprint)["S-2"]["augment"], "pass", "重跑未覆盖旧结论"
        )

    def test_mutually_exclusive_with_skip(self):
        result = run_runner(
            self.root, self.env(), runner_args=("--augment-only", "--skip-augment")
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("互斥", result.stderr)
        self.assertFalse(self.log.exists(), "互斥参数下不应 spawn")


class TC_Reopen_Failed(unittest.TestCase):
    # --reopen-failed：augment:fail 任务批量重开（done→in-progress、清旧结论），
    # 随后主循环修复并重新补测；已通过任务不受影响
    def setUp(self):
        self.root, self.sprint = make_fixture(
            {"S-1": "done", "S-2": "done", "S-3": "pending"}
        )
        patch_augment(self.sprint, "S-1", "fail")
        patch_augment(self.sprint, "S-2", "pass")
        self.log = self.root / "calls.log"

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def env(self):
        return {
            "DIY_STUB_ROUTING": "S-1:done,S-3:done",
            "DIY_STUB_LOG": str(self.log),
            "DIY_STUB_SPRINT": str(self.sprint),
        }

    def test_reopen_fix_and_reaugment(self):
        result = run_runner(self.root, self.env(), runner_args=("--reopen-failed",))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("已重开 1 个补测未通过任务：S-1", result.stdout)
        self.assertEqual(
            read_log(self.log),
            ["S-1 done", "S-1 augment", "S-3 done", "S-3 augment"],
            "重开任务应被主循环修复并重新补测",
        )
        tasks = read_tasks(self.sprint)
        self.assertEqual(tasks["S-1"]["status"], "done")
        self.assertEqual(tasks["S-1"]["augment"], "pass", "修复后补测未留痕")
        self.assertEqual(tasks["S-2"]["augment"], "pass", "已通过任务不应被重开")

    def test_reopen_clears_stale_verdict(self):
        # 修复后本轮不补测（--skip-augment）：旧 fail 结论必须已被清除，不留悬空结论
        result = run_runner(
            self.root, self.env(), runner_args=("--reopen-failed", "--skip-augment")
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(read_log(self.log), ["S-1 done", "S-3 done"])
        tasks = read_tasks(self.sprint)
        self.assertEqual(tasks["S-1"]["status"], "done")
        self.assertNotIn("augment", tasks["S-1"], "重开后旧 fail 结论应被清除")


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
