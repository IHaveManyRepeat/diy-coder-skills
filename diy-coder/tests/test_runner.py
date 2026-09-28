# trace: S-10 AC-10.1 AC-10.2 AC-10.3 AC-10.4 TC-10.1.1 TC-10.2.1 TC-10.3.1 TC-10.4.1
#        FR-4.5 D-9（findings: diy-build-loop/enhancement-1、diy-sprint/enhancement-2）
"""runner.py 循环编排器测试。全部用任务桩（stub_claude.py）替代真实 claude spawn。

- TC-10.1.1 全量跑到终态且无人工输入（集成）
- TC-10.2.1 中断后断点续跑不重复执行（单元，蜕变测试）
- TC-10.3.1 连续失败重试 2 次封顶后继续（单元，边界）
- TC-10.4.1 全程串行，任一时刻至多一个进行中（端到端，状态迁移）
- TC-Instance 实例模式（FR-4.5/D-9）：<output_dir>/<name>/sprint.yaml 读写、
  prompt 携带 --instance、非法名拒绝、无 --instance 主线回归
- TC-Augment 编码后补测接线：已完成 触发一次 diy-augment spawn，已阻塞 不触发；
  补测会话只写 augment 字段（窄写权，status 零写回）；--skip-augment / --augment-only /
  --reopen-failed 三开关；补测汇总行
- TC-AllowDeny（迁移计划 §五 C·8①）：默认白名单跨语言覆盖（两套工具名 × 构建/测试链条）、
  默认拒止表兜破坏性 git、--allow / --deny 各自替换默认
- TC-Deferred（迁移计划 §五 C·8②）：结束时待确认动作汇总——有 待办 则一行、全终态/无文件
  零行、坏 YAML 降级一行不崩
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

TERMINAL = ("已完成", "已阻塞")


def sprint_doc(statuses):
    return {
        "project": {
            "name": "fixture",
            "status": "已定稿",
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
    """建夹具项目根：diy-coder.yaml + diy-output[/<instance>]/sprint.yaml（status 已定稿）。"""
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
            {"S-1": "待办", "S-2": "待办", "S-3": "待办"}
        )
        self.log = self.root / "calls.log"
        self.sentinel = self.root / "stdin-sentinel"

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_all_terminal_and_no_stdin(self):
        result = run_runner(
            self.root,
            {
                "DIY_STUB_ROUTING": "S-1:已完成,S-2:已阻塞,S-3:已完成",
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
        self.assertEqual(len(aug), 2, f"2 个已完成任务应各触发一次补测: {lines}")


class TC_10_2_1_ResumeNoRerun(unittest.TestCase):
    # trace: S-10 AC-10.2 TC-10.2.1
    def setUp(self):
        self.root, self.sprint = make_fixture(
            {"S-1": "已完成", "S-2": "已完成", "S-3": "待办"}
        )
        self.log = self.root / "calls.log"

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_done_tasks_not_reexecuted(self):
        env = {
            "DIY_STUB_ROUTING": "S-3:已完成",
            "DIY_STUB_LOG": str(self.log),
            "DIY_STUB_SPRINT": str(self.sprint),
        }
        first = run_runner(self.root, env)
        self.assertEqual(first.returncode, 0, first.stderr)
        log_lines = read_log(self.log)
        self.assertEqual(
            log_lines, ["S-3 已完成", "S-3 augment"], f"已完成任务被重复执行: {log_lines}"
        )
        self.assertEqual(read_tasks(self.sprint)["S-3"]["status"], "已完成")

        second = run_runner(self.root, env)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(
            len(read_log(self.log)), 2, "全终态重跑产生了新调用（非幂等）"
        )


class TC_10_3_1_RetryCapThenContinue(unittest.TestCase):
    # trace: S-10 AC-10.3 TC-10.3.1
    def setUp(self):
        self.root, self.sprint = make_fixture(
            {"S-1": "待办", "S-2": "待办"}
        )
        self.log = self.root / "calls.log"

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_retry_exactly_twice_then_blocked_and_continue(self):
        result = run_runner(
            self.root,
            {
                "DIY_STUB_ROUTING": "S-1:失败,S-2:已完成",
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
        self.assertEqual(tasks["S-1"]["status"], "已阻塞")
        self.assertIn("重试", tasks["S-1"].get("blocked_reason", ""))
        self.assertEqual(tasks["S-2"]["status"], "已完成", "封顶后未继续后续任务")


class TC_10_4_1_StrictlySerial(unittest.TestCase):
    # trace: S-10 AC-10.4 TC-10.4.1
    def setUp(self):
        self.root, self.sprint = make_fixture(
            {"S-1": "待办", "S-2": "待办"}
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
                        sum(1 for t in tasks.values() if t["status"] == "进行中")
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
                    "DIY_STUB_ROUTING": "S-1:已完成,S-2:已完成",
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
            max(samples), 1, f"任一时刻出现 >1 个进行中: max={max(samples)}"
        )
        tasks = read_tasks(self.sprint)
        self.assertEqual(tasks["S-1"]["status"], "已完成")
        self.assertEqual(tasks["S-2"]["status"], "已完成")


class TC_Instance_Mode(unittest.TestCase):
    # trace: FR-4.5 D-9（findings: diy-build-loop/enhancement-1、diy-sprint/enhancement-2）
    # 实例模式：--instance 从 <output_dir>/<name>/sprint.yaml 读任务并写回同一路径
    def setUp(self):
        self.root, self.sprint = make_fixture({"S-1": "待办"}, instance="case-a")
        self.log = self.root / "calls.log"

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def env(self):
        return {
            "DIY_STUB_ROUTING": "S-1:已完成",
            "DIY_STUB_LOG": str(self.log),
            "DIY_STUB_SPRINT": str(self.sprint),
        }

    def test_reads_and_writes_instance_sprint(self):
        # 主线 sprint 全终态：若 runner 误读主线则零 spawn（日志为空）、实例文件不动；
        # 出现 1 次 spawn 即证明任务来自实例路径，终态回写也只落在实例文件
        main_sprint = write_sprint(
            self.root / "diy-output" / "sprint.yaml", {"S-1": "已完成"}
        )
        result = run_runner(
            self.root, self.env(), runner_args=("--instance", "case-a")
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            read_log(self.log), ["S-1 已完成", "S-1 augment"], "未从实例 sprint 读到待办任务"
        )
        self.assertEqual(read_tasks(self.sprint)["S-1"]["status"], "已完成")
        self.assertEqual(read_tasks(main_sprint)["S-1"]["status"], "已完成")
        self.assertIn("[runner] S-1 → 已完成", result.stdout)

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
        self.root, self.sprint = make_fixture({"S-1": "待办"})
        self.log = self.root / "calls.log"

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_invalid_instance_rejected_no_spawn(self):
        for bad in ("../escape", "bad/name", ".hidden", "sub\\dir", "a b", "a.", "a\n"):
            with self.subTest(instance=bad):
                result = run_runner(
                    self.root,
                    {
                        "DIY_STUB_ROUTING": "S-1:已完成",
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
                self.assertEqual(read_tasks(self.sprint)["S-1"]["status"], "待办")


class TC_Instance_MainlineUnchanged(unittest.TestCase):
    # trace: FR-4.5 D-9 无 --instance 主线回归：路径与 prompt 均等价现状
    def setUp(self):
        self.root, self.sprint = make_fixture({"S-1": "待办"})
        self.log = self.root / "calls.log"

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_no_instance_flag_stays_mainline(self):
        spy = make_spy(self.root)
        argv_log = self.root / "argv.log"
        result = run_runner(
            self.root,
            {
                "DIY_STUB_ROUTING": "S-1:已完成",
                "DIY_STUB_LOG": str(self.log),
                "DIY_STUB_SPRINT": str(self.sprint),
                "DIY_STUB_ARGV": str(argv_log),
                "DIY_STUB_PATH": str(STUB),
            },
            stub=spy,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(read_tasks(self.sprint)["S-1"]["status"], "已完成")
        self.assertEqual(read_log(self.log), ["S-1 已完成", "S-1 augment"])
        argv_text = Path(argv_log).read_text(encoding="utf-8")
        self.assertNotIn("--instance", argv_text, "主线 prompt 混入了实例参数")
        self.assertIn(
            "运行 diy-build-loop skill 处理任务 S-1：", argv_text,
            "主线 prompt 前缀不再等价现状",
        )


class TC_Augment_AfterDone(unittest.TestCase):
    # trace: 2026-09-13 裁定——编码后补测接线：已完成 触发一次 diy-augment spawn，
    # 已阻塞 不触发；补测会话窄写权：只写 augment 字段，任务 status 零写回
    def setUp(self):
        self.root, self.sprint = make_fixture(
            {"S-1": "待办", "S-2": "待办"}
        )
        self.log = self.root / "calls.log"

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def env(self):
        return {
            "DIY_STUB_ROUTING": "S-1:已完成,S-2:已阻塞",
            "DIY_STUB_LOG": str(self.log),
            "DIY_STUB_SPRINT": str(self.sprint),
        }

    def test_done_triggers_augment_blocked_does_not(self):
        result = run_runner(self.root, self.env())
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = read_log(self.log)
        self.assertIn("S-1 已完成", lines)
        self.assertIn("S-1 augment", lines)
        self.assertIn("S-2 已阻塞", lines)
        self.assertNotIn("S-2 augment", lines, "已阻塞任务不应触发补测")
        self.assertIn("[runner] S-1 补测轮通过", result.stdout)
        self.assertNotIn("S-2 补测轮", result.stdout, "已阻塞任务不应出现补测行")
        tasks = read_tasks(self.sprint)
        self.assertEqual(tasks["S-1"]["status"], "已完成", "补测会话篡改了任务状态")
        self.assertEqual(tasks["S-1"]["augment"], "通过", "补测结论未留痕")
        self.assertNotIn("augment", tasks["S-2"], "已阻塞任务不应有补测结论")
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
        self.root, self.sprint = make_fixture({"S-1": "待办"})
        self.log = self.root / "calls.log"

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_skip_flag_no_augment_spawn(self):
        result = run_runner(
            self.root,
            {
                "DIY_STUB_ROUTING": "S-1:已完成",
                "DIY_STUB_LOG": str(self.log),
                "DIY_STUB_SPRINT": str(self.sprint),
            },
            runner_args=("--skip-augment",),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(read_log(self.log), ["S-1 已完成"], "--skip-augment 后仍 spawn 了补测")
        tasks = read_tasks(self.sprint)
        self.assertEqual(tasks["S-1"]["status"], "已完成")
        self.assertNotIn("augment", tasks["S-1"])
        self.assertIn("补测汇总：通过 0 / 待裁断 0 / 跳过 0 / 未跑 1", result.stdout)


class TC_Augment_Only(unittest.TestCase):
    # --augment-only：只补跑已完成 且无结论的任务（通过/已跳过 跳过、失败 重跑覆盖结论）；
    # 主循环零驱动（待办 任务不动）
    def setUp(self):
        self.root, self.sprint = make_fixture(
            {"S-1": "已完成", "S-2": "已完成", "S-3": "待办", "S-4": "已完成"}
        )
        patch_augment(self.sprint, "S-1", "通过")
        patch_augment(self.sprint, "S-4", "已跳过")
        self.log = self.root / "calls.log"

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def env(self):
        return {
            "DIY_STUB_ROUTING": "S-1:已完成,S-3:已完成",
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
        self.assertEqual(tasks["S-2"]["augment"], "通过")
        self.assertEqual(tasks["S-1"]["augment"], "通过")
        self.assertEqual(tasks["S-3"]["status"], "待办", "--augment-only 驱动了主循环")
        self.assertIn("补测汇总：通过 2 / 待裁断 0 / 跳过 1 / 未跑 0", result.stdout)

    def test_failed_task_rerun_overwrites(self):
        # 裁断修复后重跑：失败 结论被新结论覆盖
        patch_augment(self.sprint, "S-2", "失败")
        result = run_runner(self.root, self.env(), runner_args=("--augment-only",))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(sorted(read_log(self.log)), ["S-2 augment"])
        self.assertEqual(
            read_tasks(self.sprint)["S-2"]["augment"], "通过", "重跑未覆盖旧结论"
        )

    def test_mutually_exclusive_with_skip(self):
        result = run_runner(
            self.root, self.env(), runner_args=("--augment-only", "--skip-augment")
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("互斥", result.stderr)
        self.assertFalse(self.log.exists(), "互斥参数下不应 spawn")


class TC_Reopen_Failed(unittest.TestCase):
    # --reopen-failed：augment:失败 任务批量重开（已完成→进行中、清旧结论），
    # 随后主循环修复并重新补测；已通过任务不受影响
    def setUp(self):
        self.root, self.sprint = make_fixture(
            {"S-1": "已完成", "S-2": "已完成", "S-3": "待办"}
        )
        patch_augment(self.sprint, "S-1", "失败")
        patch_augment(self.sprint, "S-2", "通过")
        self.log = self.root / "calls.log"

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def env(self):
        return {
            "DIY_STUB_ROUTING": "S-1:已完成,S-3:已完成",
            "DIY_STUB_LOG": str(self.log),
            "DIY_STUB_SPRINT": str(self.sprint),
        }

    def test_reopen_fix_and_reaugment(self):
        result = run_runner(self.root, self.env(), runner_args=("--reopen-failed",))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("已重开 1 个补测未通过任务：S-1", result.stdout)
        self.assertEqual(
            read_log(self.log),
            ["S-1 已完成", "S-1 augment", "S-3 已完成", "S-3 augment"],
            "重开任务应被主循环修复并重新补测",
        )
        tasks = read_tasks(self.sprint)
        self.assertEqual(tasks["S-1"]["status"], "已完成")
        self.assertEqual(tasks["S-1"]["augment"], "通过", "修复后补测未留痕")
        self.assertEqual(tasks["S-2"]["augment"], "通过", "已通过任务不应被重开")

    def test_reopen_clears_stale_verdict(self):
        # 修复后本轮不补测（--skip-augment）：旧失败结论必须已被清除，不留悬空结论
        result = run_runner(
            self.root, self.env(), runner_args=("--reopen-failed", "--skip-augment")
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(read_log(self.log), ["S-1 已完成", "S-3 已完成"])
        tasks = read_tasks(self.sprint)
        self.assertEqual(tasks["S-1"]["status"], "已完成")
        self.assertNotIn("augment", tasks["S-1"], "重开后旧失败结论应被清除")


class TC_10_1_2_MissingClaudeCmd(unittest.TestCase):
    # trace: S-10 AC-10.1 TC-10.1.2
    def setUp(self):
        self.root, self.sprint = make_fixture({"S-1": "待办"})

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
        self.root, self.sprint = make_fixture({"S-1": "待办"})

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


def make_deferred(out_dir, statuses):
    doc = {
        "project": {"name": "fixture", "created": "2026-01-01", "updated": "2026-01-01"},
        "actions": [
            {"id": f"DA-{i:03d}", "date": "2026-01-01", "skill": "diy-dev",
             "action": f"动作 {i}", "reason": "用户配置", "status": st}
            for i, st in enumerate(statuses, start=1)
        ],
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "deferred-actions.yaml").write_text(
        yaml.safe_dump(doc, allow_unicode=True, sort_keys=False), encoding="utf-8")


class TC_AllowDeny(unittest.TestCase):
    # trace: 迁移计划 §五 C·8①——无头会话命令白名单扩容（跨语言构建/测试链条）
    # + --disallowedTools 拒止表兜破坏性 git（§十三 保留确认档）
    def setUp(self):
        self.root, self.sprint = make_fixture({"S-1": "待办"})
        self.log = self.root / "calls.log"

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def spy_argv(self, runner_args=()):
        spy = make_spy(self.root)
        argv_log = self.root / "argv.log"
        result = run_runner(
            self.root,
            {
                "DIY_STUB_ROUTING": "S-1:已完成",
                "DIY_STUB_LOG": str(self.log),
                "DIY_STUB_SPRINT": str(self.sprint),
                "DIY_STUB_ARGV": str(argv_log),
                "DIY_STUB_PATH": str(STUB),
            },
            runner_args=runner_args,
            stub=spy,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return Path(argv_log).read_text(encoding="utf-8")

    def test_default_allow_covers_language_toolchains(self):
        argv = self.spy_argv()
        for entry in ("Bash(python *)", "PowerShell(python *)",
                      "Bash(pip *)", "Bash(ruff *)", "Bash(pytest *)",
                      "Bash(npm *)", "Bash(npx *)", "Bash(node *)",
                      "Bash(pnpm *)", "Bash(yarn *)", "Bash(playwright *)",
                      "Bash(go *)", "Bash(cargo *)", "Bash(mvn *)", "Bash(gradle *)",
                      "Bash(git add *)", "Bash(git commit *)", "Bash(git push *)",
                      "PowerShell(cargo *)", "PowerShell(git push *)"):
            with self.subTest(entry=entry):
                self.assertIn(entry + "\n", argv, f"白名单缺 {entry}")
        # 规则写法统一为空格形式（冒号 :* 是等价 legacy 写法，个别版本有静默失效报告）
        self.assertNotIn("python:*)", argv, "白名单残留冒号写法")

    def test_default_deny_guards_destructive_git(self):
        argv = self.spy_argv()
        self.assertIn("--disallowedTools\n", argv, "未传拒止表")
        for entry in ("Bash(git push *--force*)", "PowerShell(git push *--force*)",
                      "Bash(git push *--delete*)", "Bash(git reset *--hard*)",
                      "Bash(git branch *-D*)", "Bash(git branch *--delete*)"):
            with self.subTest(entry=entry):
                self.assertIn(entry + "\n", argv, f"拒止表缺 {entry}")

    def test_custom_allow_replaces_default(self):
        argv = self.spy_argv(runner_args=("--allow", "Bash(echo *)"))
        self.assertIn("Bash(echo *)\n", argv)
        self.assertNotIn("Bash(npm *)\n", argv, "自定义 --allow 未替换默认清单")

    def test_custom_deny_replaces_default(self):
        argv = self.spy_argv(runner_args=("--deny", "Bash(rm *)"))
        self.assertIn("Bash(rm *)\n", argv)
        self.assertNotIn("Bash(git push *--force*)\n", argv,
                         "自定义 --deny 未替换默认拒止表")


class TC_Deferred_Summary(unittest.TestCase):
    # trace: 迁移计划 §五 C·8②——runner 结束时的待确认动作汇总（有则一行，无则零行）
    def setUp(self):
        self.root, self.sprint = make_fixture({"S-1": "已完成"})  # 全终态：零 spawn

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_pending_actions_reported(self):
        make_deferred(self.root / "diy-output", ("待办", "已完成", "待办"))
        result = run_runner(self.root, {})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("待确认动作 2 条待办：DA-001、DA-003", result.stdout)

    def test_no_pending_no_line(self):
        make_deferred(self.root / "diy-output", ("已完成", "已拒绝"))
        result = run_runner(self.root, {})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("待确认动作", result.stdout)

    def test_no_file_no_line(self):
        result = run_runner(self.root, {})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("待确认动作", result.stdout)

    def test_broken_yaml_degrades_to_one_line(self):
        out = self.root / "diy-output"
        out.mkdir(parents=True, exist_ok=True)
        (out / "deferred-actions.yaml").write_text("actions: [broken", encoding="utf-8")
        result = run_runner(self.root, {})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("读取失败", result.stdout)


# ================================================================ C·3a W6：分线编排（--line wds，§5b）
#
# 新增面（既有 27 条主线用例逐字未动）：
# - TC-WDS-Gate     §5b #2 WDS 硬门：design.yaml 的 project.status: 已定稿；缺失/未定稿 → 拒绝 + 路由
# - TC-WDS-Drive    §5b #3/#3b 页级驱动链（diy-dev WDS 模式 → diy-review WDS 路径），终点 = 待验收
# - TC-WDS-Repair   审查回修边（待验收 → 结构稿中）→ 整环重试；dev 未推进不进审查环
# - TC-WDS-Prompt   §5b #5 子会话提示词点名目标技能（不得沿用 diy-build-loop）
# - TC-WDS-Serial   页级严格串行 + 待验收页不重驱动 + 汇总
# - TC-WDS-Instance §5b #6 --instance 语义与主线一致
# - TC-WDS-Refuse   §5b #7 三个「不做」项的显式拒绝（augment 面 / 并发实例 / 演进轮不驱动）
# - TC-Line-*       分线对照实跑 + 主线路径零变化

DESIGN_ENGINE = HERE.parent / "skills" / "diy-design" / "scripts" / "design.py"
import importlib.util  # noqa: E402 —— 新段专用（既有段零改动：不回头改文件头 import 区）


def load_module(name, path):
    """importlib 按路径载入模块（不装包、不动 sys.path）——供机械对账取常量用。"""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


NL = chr(10)
# 负载余量（承 V-F §5.1：R1 全量并行下 WDS 驱动面偶发 9 红 / 出现过 subprocess.TimeoutExpired）：
# WDS 用例拉起的是「runner → 子会话桩 → 引擎」三层嵌套 spawn 链，隔离复跑 <3s，但全量并行
# （多路 pytest / 杀软扫临时目录）时尾延迟放大；显式 timeout 给足余量，避免把「机器忙」
# 误判成「runner 坏了」。run_runner 的缺省 60s 供既有主线用例使用，不动。
WDS_RUN_TIMEOUT = 180
WDS_LOCK_WAIT = 60      # 等第一个 runner 建出并发锁的窗口（原 20s：负载下曾误报「未持锁」）
WDS_FIRST_RUN_TIMEOUT = 180  # 第一个 runner 跑完的窗口（原 90s）
WDS_HTML = NL.join([
    "<!DOCTYPE html>",
    '<html lang="zh-CN">',
    "<head>",
    '<meta charset="utf-8">',
    "<title>WDS 页</title>",
    "</head>",
    "<body>",
    "<h1>WDS 页</h1>",
    "<button>动作</button>",
    "</body>",
    "</html>",
])


def write_design(path, page_statuses, project_status="已定稿"):
    """写 WDS 夹具 design.yaml（每页四态齐 + 结构稿在场，过引擎页级门）+ 其 prototypes。

    page_statuses = {页 ID: 页状态}；None 表示该页不写 status 键（旧稿形态 = 未开始）。
    """
    lines = [
        "project:",
        "  name: fixture-wds",
        "  status: %s" % project_status,
        "  updated: 2026-09-27",
        "direction: 瑞士编辑风——大字阶对比、留白节奏、单强调色",
        "frontend_framework: html",
        "tokens:",
        "  color:",
        "    bg: '#ffffff'",
        "    surface: '#f5f5f2'",
        "    text: '#1a1a1a'",
        "    text_muted: '#5a5a5a'",
        "    accent: '#0a5c8c'",
        "    accent_text: '#ffffff'",
        "  spacing:",
        "    unit: 4px",
        "    scale: [4px, 8px, 16px, 24px, 48px]",
        "  typography:",
        "    family_base: Inter",
        "    scale: [1rem, 1.25rem, 2rem]",
        "pages:",
    ]
    for pid, status in page_statuses.items():
        lines.append("- id: %s" % pid)
        lines.append("  name: 页 %s" % pid)
        lines.append("  route: /%s" % str(pid).lower().replace(".", "-"))
        if status is not None:
            lines.append("  status: %s" % status)
        lines.append("  states:")
        lines.append("  - {name: 悬停, signals: [图标, 动效]}")
        lines.append("  - {name: 空态, signals: [文字]}")
        lines.append("  - {name: 加载中, signals: [图标, 动效]}")
        lines.append("  - {name: 错误, signals: [图标, 文字]}")
        lines.append("  prototype: prototypes/%s.html" % pid)
    lines.append("revisions: []")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(NL.join(lines) + NL, encoding="utf-8")
    for pid in page_statuses:
        proto = path.parent / "prototypes" / ("%s.html" % pid)
        proto.parent.mkdir(parents=True, exist_ok=True)
        proto.write_text(WDS_HTML, encoding="utf-8")
    return path


def make_wds_fixture(page_statuses, project_status="已定稿", instance=None,
                     sprint_statuses=None):
    """建 WDS 夹具根：diy-coder.yaml + diy-output[/<instance>]/design.yaml + 结构稿 + 引擎副本。

    design.py 副本落 <root>/.claude/skills/diy-design/scripts/——子会话桩按该规范路径调引擎，
    使「状态回填写回」走真引擎（transition）而非测试自造。
    `page_statuses=None` = 不写 design.yaml（缺失门用例）；`sprint_statuses` 给了才写 sprint.yaml。
    """
    root = Path(tempfile.mkdtemp(prefix="tmp-wds-"))
    (root / "diy-coder.yaml").write_text(
        "paths:\n  output_dir: diy-output\n", encoding="utf-8"
    )
    out = (root / "diy-output" / instance) if instance else (root / "diy-output")
    if page_statuses is not None:
        write_design(out / "design.yaml", page_statuses, project_status)
    if sprint_statuses is not None:
        write_sprint(out / "sprint.yaml", sprint_statuses)
    engine = root / ".claude" / "skills" / "diy-design" / "scripts" / "design.py"
    engine.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(DESIGN_ENGINE, engine)
    return root


# WDS 子会话桩：按 phase（prompt 含 diy-dev / diy-review）模拟两个环，回填一律调真引擎
# transition（§5b #4）。DIY_WDS_ROUTING 键 = "<页 ID> <phase>" 或 "<页 ID>"，值 = 判决词，
# 分号序列 "A|B" 按该 (页,phase) 的第 n 次出现取第 n 项（末项重复）——用于「首轮失败后通过」。
#   实现未推进 = dev 不写回（页停 结构稿中）；失败 = review 走回修边（→ 结构稿中）
#   代批 = review 越权写 已批准（反例）；审查崩了 = review 非零退出 + 零写回（反例）
WDS_STUB_SRC = r'''
import os, re, subprocess, sys, time

joined = " ".join(sys.argv)
m = re.search(r"SC-\d+\.P\d+", joined)
if not m:
    sys.stderr.write("wds-stub: prompt 未携带页 ID\n")
    sys.exit(2)
page = m.group(0)
phase = "review" if "diy-review" in joined else "dev"
log = os.environ.get("DIY_WDS_LOG")


def prior_count(text):
    if not log or not os.path.exists(log):
        return 0
    with open(log, encoding="utf-8") as fh:
        return sum(1 for ln in fh if ln.strip() == text)


def logline(text):
    if log:
        with open(log, "a", encoding="utf-8") as fh:
            fh.write(text + "\n")


idx = prior_count("%s %s" % (page, phase))
logline("%s %s" % (page, phase))
sleep_for = float(os.environ.get("DIY_WDS_SLEEP", "0"))
if sleep_for:
    time.sleep(sleep_for)

routing = dict(
    item.split(":", 1)
    for item in os.environ.get("DIY_WDS_ROUTING", "").split(",")
    if ":" in item
)
raw = routing.get("%s %s" % (page, phase)) or routing.get(page) or "通过"
verdicts = raw.split("|")
verdict = verdicts[min(idx, len(verdicts) - 1)]

if phase == "dev":
    if verdict == "实现未推进":
        sys.exit(1)
    to = "待验收"
elif verdict == "失败":
    to = "结构稿中"
elif verdict == "代批":
    to = "已批准"      # 反例（F-2）：审查越权代批——本轮不该出现的落点
elif verdict == "审查崩了":
    sys.exit(7)        # 反例（F-1）：审查非零退出且零写回——与「审查通过」在产物上不可区分
else:
    sys.exit(0)  # 审查通过：页保持 待验收（不代用户批准）

design = os.environ["DIY_WDS_DESIGN"]
engine = os.environ["DIY_WDS_ENGINE"]
proc = subprocess.run(
    [sys.executable, engine, "transition", "--design", design,
     "--page", page, "--to", to, "--json"],
    capture_output=True, text=True, encoding="utf-8",
)
logline("transition %s -> %s ok=%s rc=%d"
        % (page, to, '"ok": true' in (proc.stdout or ""), proc.returncode))
sys.exit(proc.returncode)
'''


def make_wds_stub(root):
    stub = root / "wds_stub_claude.py"
    stub.write_text(WDS_STUB_SRC, encoding="utf-8")
    return stub


# 越界落点桩（中-1 / 低-1 反例用）：把指定环（DIY_WDS_OFFTRACK_PHASE = dev|review）的页经
# 真引擎 transition 推到指定落点（DIY_WDS_OFFTRACK_TO，典型 已移除），其余环照正常链走
# （dev → 待验收；review → 零写回通过）。日志格式与 WDS_STUB_SRC 同源，便于数 spawn 次数。
WDS_OFFTRACK_STUB_SRC = r'''
import os, re, subprocess, sys

joined = " ".join(sys.argv)
m = re.search(r"SC-\d+\.P\d+", joined)
if not m:
    sys.stderr.write("wds-stub: prompt 未携带页 ID\n")
    sys.exit(2)
page = m.group(0)
phase = "review" if "diy-review" in joined else "dev"
log = os.environ.get("DIY_WDS_LOG")


def logline(text):
    if log:
        with open(log, "a", encoding="utf-8") as fh:
            fh.write(text + "\n")


logline("%s %s" % (page, phase))
engine = os.environ["DIY_WDS_ENGINE"]
design = os.environ["DIY_WDS_DESIGN"]


def transition(to):
    cmd = [sys.executable, engine, "transition", "--design", design,
           "--page", page, "--to", to, "--json"]
    if to == "已移除":
        cmd += ["--reason", "夹具：越界落点反例（该页本轮被废弃）"]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    logline("transition %s -> %s ok=%s rc=%d"
            % (page, to, '"ok": true' in (proc.stdout or ""), proc.returncode))
    return proc.returncode


if phase == os.environ.get("DIY_WDS_OFFTRACK_PHASE"):
    sys.exit(transition(os.environ["DIY_WDS_OFFTRACK_TO"]))
if phase == "dev":
    sys.exit(transition("待验收"))
sys.exit(0)  # 审查通过：页保持 待验收（不代用户批准）
'''


def make_wds_offtrack_stub(root):
    stub = root / "wds_offtrack_stub.py"
    stub.write_text(WDS_OFFTRACK_STUB_SRC, encoding="utf-8")
    return stub


class WdsCase(unittest.TestCase):
    """WDS 用例公共夹具（页 SC-01.P1 结构稿中；日志 / 设计稿 / 引擎副本路径集中在此）。"""

    def setUp(self):
        self.root = None
        self.rebuild({"SC-01.P1": "结构稿中"})

    def tearDown(self):
        if self.root is not None:
            shutil.rmtree(self.root, ignore_errors=True)

    def rebuild(self, page_statuses, project_status="已定稿", instance=None,
                sprint_statuses=None):
        """换一个 WDS 夹具（用例内需要不同页分布时用；旧夹具整棵删除）。"""
        if self.root is not None:
            shutil.rmtree(self.root, ignore_errors=True)
        self.root = make_wds_fixture(page_statuses, project_status=project_status,
                                     instance=instance, sprint_statuses=sprint_statuses)
        out = (self.root / "diy-output" / instance) if instance else (self.root / "diy-output")
        self.design = out / "design.yaml"
        self.log = self.root / "wds.log"
        self.stub = make_wds_stub(self.root)

    def env(self, **extra):
        return {
            "DIY_WDS_LOG": str(self.log),
            "DIY_WDS_DESIGN": str(self.design),
            "DIY_WDS_ENGINE": str(self.root / ".claude" / "skills" / "diy-design"
                                  / "scripts" / "design.py"),
            **extra,
        }

    def run_wds(self, runner_args=("--line", "wds"), env_extra=None, stub=None):
        return run_runner(self.root, env_extra if env_extra is not None else self.env(),
                          timeout=WDS_RUN_TIMEOUT,
                          runner_args=runner_args, stub=stub or self.stub)

    def status_of(self, page_id="SC-01.P1", design=None):
        doc = yaml.safe_load(Path(design or self.design).read_text(encoding="utf-8"))
        for page in doc["pages"]:
            if page["id"] == page_id:
                return page.get("status")
        return None

    def lock_path(self):
        return self.root / "diy-output" / ".runner-wds.lock"


class TC_WDS_Gate(WdsCase):
    # trace: §5b #2 WDS 硬门：design.yaml 的 project.status: 已定稿；缺失/未定稿 → 拒绝并路由
    def test_missing_design_refused_with_routes(self):
        self.rebuild(None)  # 无 design.yaml
        result = self.run_wds()
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("Traceback", result.stderr)
        self.assertIn("[runner]", result.stderr)
        self.assertIn("diy-wds-brief", result.stderr, "缺失源未路由 WDS 入口")
        self.assertIn("diy-prd", result.stderr, "缺失源未给产品线路由")
        lines = [ln for ln in result.stderr.splitlines() if ln.strip()]
        self.assertEqual(len(lines), 1, f"应一行报错，实际: {result.stderr}")
        self.assertFalse(self.log.exists(), "门禁拒绝仍 spawn 了子会话")

    def test_draft_design_refused(self):
        self.rebuild({"SC-01.P1": "结构稿中"}, project_status="草稿")
        result = self.run_wds()
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("Traceback", result.stderr)
        self.assertIn("非已定稿", result.stderr)
        self.assertIn("diy-design", result.stderr)
        self.assertFalse(self.log.exists(), "未定稿仍 spawn 了子会话")
        self.assertEqual(self.status_of(), "结构稿中", "门禁拒绝却改了设计稿")

    def test_unparsable_design_reports_one_line(self):
        self.design.write_text("project: [broken" + NL, encoding="utf-8")
        result = self.run_wds()
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("Traceback", result.stderr)
        self.assertIn("[runner]", result.stderr)
        self.assertFalse(self.log.exists())

    def test_pages_shape_anomaly_reports_one_line(self):
        self.design.write_text(
            "project: {name: fixture-wds, status: 已定稿}" + NL + "pages: {a: 1}" + NL,
            encoding="utf-8")
        result = self.run_wds()
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("Traceback", result.stderr)
        self.assertIn("pages 不是列表", result.stderr)
        self.assertFalse(self.log.exists())


class TC_WDS_DriveOnePage(WdsCase):
    # trace: §5b #3/#3b 页 结构稿中 → 待验收（dev 经 transition 回填）→ review 通过保持 待验收
    def test_page_reaches_accept_and_waits_for_user(self):
        result = self.run_wds()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.status_of(), "待验收", "页未到无头侧终点")
        self.assertIn("[runner] SC-01.P1 → 待用户批准", result.stdout)
        self.assertIn("页保持 待验收", result.stdout)
        self.assertLess(
            result.stdout.index("SC-01.P1 → 待用户批准"),
            result.stdout.index("演进轮"),
        )
        # 回填经 transition 的机械证据：① 引擎写 .prev 快照（直改 YAML 不会产生）
        # ② 桩日志里的 transition 回执 ok=True；③ 页状态确为 待验收
        self.assertTrue((self.design.parent / "design.yaml.prev").is_file(),
                        "缺 .prev 快照——回填未经引擎 transition")
        self.assertEqual(read_log(self.log), [
            "SC-01.P1 dev",
            "transition SC-01.P1 -> 待验收 ok=True rc=0",
            "SC-01.P1 review",
        ])
        self.assertFalse(self.lock_path().exists(), "锁未释放（并发闸会误挡下一次运行）")

    def test_second_page_not_driven_when_already_accepted(self):
        # 待验收（等用户批准）的页不是驱动单元：只驱动 结构稿中 的页；汇总把「本轮审查通过」
        # 与「本轮未复验」分列（SC-01.P1 的审查结论来自更早的会话＝未知），后者计入 rc（高-1）
        self.rebuild({"SC-01.P1": "待验收", "SC-02.P1": "结构稿中"})
        result = self.run_wds()
        self.assertNotEqual(result.returncode, 0, "本轮未复验的 待验收 页未计入 rc")
        self.assertEqual(
            [ln for ln in read_log(self.log) if ln.endswith(" dev")], ["SC-02.P1 dev"],
            "待验收页被重复驱动",
        )
        self.assertIn("待用户批准 1 页（本轮审查通过）：SC-02.P1", result.stdout)
        self.assertIn("本轮未复验 1 页：SC-01.P1", result.stdout)

    def test_preexisting_pending_page_flagged_unverified_not_approvable(self):
        # 高-1（主 agent 终裁）：上一轮审查崩掉（或进程被杀）留在 待验收 的页，本轮既不被驱动、
        # 也不被标记——不得与「本轮审查通过」的页同列呈用户批准（用户照单批准的就是未经复验的
        # 页，与 F-1 同源，只是延迟一轮暴露）。台账在内存里：本轮未复验的 待验收 页单列点名
        # 并计入 rc（非零）；零新键、design.yaml 由子会话经 transition 写（runner 不直改）。
        self.rebuild({"SC-01.P1": "待验收", "SC-02.P1": "结构稿中"})
        result = self.run_wds()
        self.assertNotEqual(result.returncode, 0, "未复验页的存在未计入 rc（非零）")
        self.assertIn("本轮未复验 1 页：SC-01.P1", result.stdout)
        self.assertIn("审查结论未知", result.stdout)
        self.assertIn("勿直接批准", result.stdout)
        self.assertIn("待用户批准 1 页（本轮审查通过）：SC-02.P1", result.stdout)
        self.assertNotIn("待用户批准 2 页", result.stdout)
        pending_lines = [ln for ln in result.stdout.splitlines()
                         if ln.startswith("[runner] 待用户批准")]
        self.assertEqual(len(pending_lines), 1, f"待批准名单应恰一行: {pending_lines}")
        self.assertNotIn("SC-01.P1", pending_lines[0], "未复验页混进了待批准名单")
        # 未复验页零 spawn：不得靠自动重跑审查掩盖「本轮没复验」这一事实
        self.assertEqual(read_log(self.log), [
            "SC-02.P1 dev",
            "transition SC-02.P1 -> 待验收 ok=True rc=0",
            "SC-02.P1 review",
        ])
        self.assertEqual(self.status_of("SC-01.P1"), "待验收")
        self.assertEqual(self.status_of("SC-02.P1"), "待验收")
        self.assertFalse(self.lock_path().exists(), "锁未释放")

    def test_serial_order_two_pages(self):
        # 页级严格串行：整页（dev → review）走完才进下一页，不交叉
        self.rebuild({"SC-01.P1": "结构稿中", "SC-02.P1": "结构稿中"})
        result = self.run_wds()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(read_log(self.log)[0::3], ["SC-01.P1 dev", "SC-02.P1 dev"])
        self.assertEqual(read_log(self.log)[2::3], ["SC-01.P1 review", "SC-02.P1 review"])
        self.assertEqual(self.status_of("SC-01.P1"), "待验收")
        self.assertEqual(self.status_of("SC-02.P1"), "待验收")

    def test_no_draft_page_summary(self):
        # 无 结构稿中 页 → 零 spawn、一行状态分布；全 未开始/已批准 也照此
        self.rebuild({"SC-01.P1": "已批准", "SC-02.P1": None})
        result = self.run_wds()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.log.exists(), "无驱动单元却 spawn 了子会话")
        self.assertIn("无 结构稿中 的页可驱动", result.stdout)
        self.assertIn("未开始 1", result.stdout, "status 键缺失应按 未开始 计")
        self.assertNotIn("待用户批准", result.stdout)

    def test_nameless_draft_page_named_not_silently_skipped(self):
        # 汇总句自相矛盾修正（主 agent 终裁项）：结构稿中 但缺 id 的页不能静默跳过——否则汇总句「无 结构稿中 的页可驱动
        # （… 结构稿中 1 …）」同句自相矛盾且 rc=0。现改为：逐个点名 + 本轮按未达终点计（rc≠0）
        self.rebuild({})
        text = self.design.read_text(encoding="utf-8")
        nameless_page = NL.join([
            "- name: 无号页",
            "  route: /nameless",
            "  status: 结构稿中",
            "  states:",
            "  - {name: 悬停, signals: [图标, 动效]}",
            "  - {name: 空态, signals: [文字]}",
            "  - {name: 加载中, signals: [图标, 动效]}",
            "  - {name: 错误, signals: [图标, 文字]}",
            "  prototype: prototypes/nolabel.html",
        ])
        self.design.write_text(
            text.replace("pages:" + NL, "pages:" + NL + nameless_page + NL), encoding="utf-8")
        result = self.run_wds()
        self.assertNotEqual(result.returncode, 0, "缺 id 的驱动单元被静默跳过（rc=0）")
        self.assertFalse(self.log.exists(), "缺 id 页却被 spawn（无页 ID 可传）")
        self.assertIn("无 结构稿中 的页可驱动", result.stdout)
        self.assertIn("结构稿中 但缺 id 被跳过 1 页：pages[0]（name=无号页）", result.stdout)
        self.assertNotIn("待用户批准", result.stdout)


class TC_WDS_ReviewRepair(WdsCase):
    # trace: §5b #3b 审查失败 → 回修边（待验收 → 结构稿中）→ 整环重试（上限照主线 R-4）
    def test_fail_then_pass_retries_whole_chain(self):
        result = self.run_wds(env_extra=self.env(**{"DIY_WDS_ROUTING": "SC-01.P1 review:失败|通过"}))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.status_of(), "待验收")
        self.assertEqual(read_log(self.log), [
            "SC-01.P1 dev",
            "transition SC-01.P1 -> 待验收 ok=True rc=0",
            "SC-01.P1 review",
            "transition SC-01.P1 -> 结构稿中 ok=True rc=0",
            "SC-01.P1 dev",
            "transition SC-01.P1 -> 待验收 ok=True rc=0",
            "SC-01.P1 review",
        ], "回修后未整环重跑（dev → review）")
        self.assertIn("SC-01.P1 → 待用户批准", result.stdout)

    def test_review_always_fails_caps_at_retry_limit(self):
        result = self.run_wds(env_extra=self.env(**{"DIY_WDS_ROUTING": "SC-01.P1 review:失败"}))
        self.assertNotEqual(result.returncode, 0, "重试用尽应非零退出（页未达无头侧终点）")
        self.assertEqual(self.status_of(), "结构稿中")
        devs = [ln for ln in read_log(self.log) if ln.endswith(" dev")]
        reviews = [ln for ln in read_log(self.log) if ln.endswith(" review")]
        self.assertEqual(len(devs), 3, f"应恰 3 轮（初次+2 重试）: {devs}")
        self.assertEqual(len(reviews), 3)
        # 审查判失败 → 回修边（页回 结构稿中）→ 整环重试到底：收尾句保留「未达 待验收」
        # 落点事实，并点名原因（审查未通过，非 dev 未推进）
        self.assertIn("SC-01.P1 → 结构稿中（3 轮未达 待验收（审查未通过，已走回修边）），本轮跳过该页",
                      result.stdout)
        self.assertNotIn("待用户批准", result.stdout, "回修中的页被计入待批准")

    def test_review_nonzero_exit_never_counted_as_passed(self):
        # F-1（主 agent 按阻断级处理）：审查环非零退出（崩了/没跑成）在产物上的表现与
        # 「审查通过」同为「零写回」——runner 必须接住退出码：rc != 0 一律不得判「审查通过」，
        # 按失败处理并如实点名；页虽停在 待验收，也不得计入「待用户批准」（否则用户批准的
        # 就是未经审查的页）
        result = self.run_wds(
            env_extra=self.env(**{"DIY_WDS_ROUTING": "SC-01.P1 review:审查崩了"}))
        self.assertNotEqual(result.returncode, 0, "审查非零退出仍报 rc=0（静默假过）")
        self.assertNotIn("SC-01.P1 → 待用户批准", result.stdout)
        self.assertNotIn("待用户批准", result.stdout, "未过审查的页被计入待批准")
        self.assertIn("审查未通过/没跑成", result.stdout)
        self.assertIn("diy-review 退出码 7", result.stdout, "退出码未如实点名")
        self.assertIn("审查未通过/没跑成 1 页：SC-01.P1", result.stdout)
        self.assertEqual(self.status_of(), "待验收", "审查崩掉的会话意外改动了页状态")
        devs = [ln for ln in read_log(self.log) if ln.endswith(" dev")]
        reviews = [ln for ln in read_log(self.log) if ln.endswith(" review")]
        self.assertEqual((len(devs), len(reviews)), (3, 3), "审查非零退出未走既有整环重试路径")
        self.assertFalse(self.lock_path().exists(), "锁未释放")

    def test_review_stepping_to_approved_stops_without_retry(self):
        # F-2：审查不得代批（待验收 → 已批准 是用户批准边）。页被推到本轮不该出现的落点
        # （既非 待验收 也非回修边的 结构稿中）→ 报错停手、不重试（不得在 已批准 页上再
        # spawn dev），输出如实点名「审查可能代批」
        result = self.run_wds(env_extra=self.env(**{"DIY_WDS_ROUTING": "SC-01.P1 review:代批"}))
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.status_of(), "已批准")
        self.assertIn("审查可能代批", result.stderr)
        self.assertIn("SC-01.P1", result.stderr)
        self.assertIn("已批准", result.stderr)
        self.assertIn("停手不重试", result.stderr)
        devs = [ln for ln in read_log(self.log) if ln.endswith(" dev")]
        reviews = [ln for ln in read_log(self.log) if ln.endswith(" review")]
        self.assertEqual((len(devs), len(reviews)), (1, 1), "代批后仍在 已批准 页上重试")
        self.assertNotIn("待用户批准", result.stdout)
        self.assertFalse(self.lock_path().exists(), "锁未释放")

    def test_dev_stepping_off_track_stops_without_retry(self):
        # 中-1（主 agent 终裁）：dev 把页推到 已移除（引擎合法边 = 该页本轮被废弃）——现实现按
        # 「未达 待验收」整环重试 3 次、在废弃页上重复 spawn dev（与 F-2 同构，白烧 2 次真会话）。
        # 要求：dev 后回读做与审查侧对称的落点收紧——合法落点只有 结构稿中（本次未推进/待重试）
        # 与 待验收（推进成功）；越界即报错停手、不重试，且病因归 dev 环（不是审查代批）
        stub = make_wds_offtrack_stub(self.root)
        result = self.run_wds(
            env_extra=self.env(**{"DIY_WDS_OFFTRACK_PHASE": "dev",
                                  "DIY_WDS_OFFTRACK_TO": "已移除"}),
            stub=stub)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.status_of(), "已移除")
        self.assertEqual(read_log(self.log), [
            "SC-01.P1 dev",
            "transition SC-01.P1 -> 已移除 ok=True rc=0",
        ], "dev 越界后仍在 已移除 页上重试")
        self.assertIn("已移除", result.stderr)
        self.assertIn("diy-dev", result.stderr, "停手句未点名 dev 环")
        self.assertIn("停手不重试", result.stderr)
        self.assertIn("废弃", result.stderr, "未说清 已移除 的语义（该页本轮被废弃）")
        self.assertNotIn("审查可能代批", result.stderr, "dev 环病因被硬编码成审查代批")
        self.assertNotIn("待用户批准", result.stdout)
        self.assertFalse(self.lock_path().exists(), "锁未释放")

    def test_review_stepping_to_removed_names_actual_cause(self):
        # 低-1（主 agent 终裁）：停手行为对（1 dev + 1 review、rc≠0），但病因不得硬编码
        # 「审查可能代批」——只有 已批准 才是代批；其余越界落点（此处 已移除）按实际落点给因，
        # 并保留 diy-review 的核查指引
        stub = make_wds_offtrack_stub(self.root)
        result = self.run_wds(
            env_extra=self.env(**{"DIY_WDS_OFFTRACK_PHASE": "review",
                                  "DIY_WDS_OFFTRACK_TO": "已移除"}),
            stub=stub)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.status_of(), "已移除")
        devs = [ln for ln in read_log(self.log) if ln.endswith(" dev")]
        reviews = [ln for ln in read_log(self.log) if ln.endswith(" review")]
        self.assertEqual((len(devs), len(reviews)), (1, 1), "越界后未停手")
        self.assertIn("审查落点越界", result.stderr)
        self.assertIn("已移除", result.stderr)
        self.assertIn("停手不重试", result.stderr)
        self.assertIn("diy-review", result.stderr, "停手句未保留 diy-review 核查指引")
        self.assertNotIn("审查可能代批", result.stderr, "非 已批准 落点仍硬编码「代批」病因")
        self.assertNotIn("待用户批准", result.stdout)
        self.assertFalse(self.lock_path().exists(), "锁未释放")

    def test_dev_not_advanced_skips_review_loop(self):
        result = self.run_wds(env_extra=self.env(**{"DIY_WDS_ROUTING": "SC-01.P1 dev:实现未推进"}))
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.status_of(), "结构稿中")
        self.assertEqual(read_log(self.log), ["SC-01.P1 dev"] * 3,
                         "dev 未把页推到 待验收却进了审查环")
        self.assertFalse((self.design.parent / "design.yaml.prev").exists(),
                         "页未推进却被写回")


class TC_WDS_PromptShape(WdsCase):
    # trace: §5b #5 子会话提示词：点名 diy-dev（WDS 模式）/ diy-review（WDS 路径），
    # 不得沿用主线 diy-build-loop；按页级语义写（页 ID / states[].signals / 浏览器门 / 终态）
    def test_prompts_name_wds_skills_not_build_loop(self):
        spy = make_spy(self.root)
        argv_log = self.root / "argv.log"
        result = self.run_wds(
            env_extra=self.env(**{"DIY_STUB_ARGV": str(argv_log), "DIY_STUB_PATH": str(self.stub)}),
            stub=spy,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        argv_text = Path(argv_log).read_text(encoding="utf-8")
        prompts = [ln for ln in argv_text.splitlines() if "运行 diy-" in ln]
        self.assertEqual(len(prompts), 2, f"应恰两次 spawn: {prompts}")
        dev_prompt, review_prompt = prompts
        self.assertTrue(dev_prompt.startswith("运行 diy-dev skill 的 WDS 模式"), dev_prompt[:40])
        self.assertTrue(review_prompt.startswith("运行 diy-review skill 的 WDS 路径"),
                        review_prompt[:40])
        for prompt in prompts:
            self.assertIn("SC-01.P1", prompt, "提示词未点名页 ID")
            self.assertIn("states[].signals", prompt, "提示词未点名判据真源")
        # 实现环：回填经 transition + 浏览器门（含裁定 21 的环境不可用处置）+ 终态 待验收
        self.assertIn("经 design.py transition 迁移到 待验收", dev_prompt)
        self.assertIn("浏览器强制门", dev_prompt)
        self.assertIn("裁定 21", dev_prompt)
        # 审查环：独立复验 + 判决不代用户批准 + 失败走回修边
        self.assertIn("经 design.py transition 把页 SC-01.P1 迁移到 结构稿中", review_prompt)
        self.assertIn("不采信 diy-dev 的自述", review_prompt)
        self.assertIn("绝不代批", review_prompt)
        self.assertNotIn("diy-build-loop", argv_text, "WDS 线沿用了主线 build-loop（硬门读 sprint.yaml）")
        self.assertNotIn("diy-wds-evolution", argv_text, "演进轮不在无人值守环内")
        self.assertNotIn("--instance", argv_text, "无 --instance 时提示词混入了实例参数")


class TC_WDS_Instance(WdsCase):
    # trace: §5b #6 --instance 语义与主线一致：读写 <output_dir>/<name>/design.yaml
    def test_instance_design_driven_others_untouched(self):
        self.rebuild({"SC-01.P1": "结构稿中"}, instance="case-a")
        main_design = write_design(self.root / "diy-output" / "design.yaml",
                                   {"SC-01.P1": "已批准"})
        before = main_design.read_text(encoding="utf-8")
        spy = make_spy(self.root)
        argv_log = self.root / "argv.log"
        result = self.run_wds(
            runner_args=("--line", "wds", "--instance", "case-a"),
            env_extra=self.env(**{"DIY_STUB_ARGV": str(argv_log),
                                  "DIY_STUB_PATH": str(self.stub)}),
            stub=spy,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.status_of(), "待验收")
        self.assertEqual(main_design.read_text(encoding="utf-8"), before,
                         "实例运行改动了主线平铺的设计稿")
        argv_text = Path(argv_log).read_text(encoding="utf-8")
        self.assertIn("--instance case-a", argv_text, "子会话 prompt 未携带实例激活参数")


class TC_WDS_Refuse(WdsCase):
    # trace: §5b #7 三个「不做」项的显式拒绝（不静默忽略）
    def test_augment_flags_refused_on_wds_line(self):
        # ② augment 面（--skip-augment / --augment-only / 同族 --reopen-failed）
        for flag in ("--skip-augment", "--augment-only", "--reopen-failed"):
            with self.subTest(flag=flag):
                result = self.run_wds(runner_args=("--line", "wds", flag))
                self.assertNotEqual(result.returncode, 0, f"{flag} 未被拒绝")
                self.assertNotIn("Traceback", result.stderr)
                self.assertIn(flag, result.stderr)
                self.assertIn("未定义", result.stderr)
                self.assertIn("[runner]", result.stderr)
                lines = [ln for ln in result.stderr.splitlines() if ln.strip()]
                self.assertEqual(len(lines), 1, f"应一行报错，实际: {result.stderr}")
                self.assertFalse(self.log.exists(), f"{flag} 被拒后仍 spawn 了子会话")
                self.assertEqual(self.status_of(), "结构稿中")
                self.assertFalse((self.design.parent / "design.yaml.prev").exists())

    def test_preexisting_lock_refuses_second_run(self):
        # ③ 并发实例：锁在场 = 显式拒绝（零 spawn、一行报错、给解锁出口）
        lock = self.lock_path()
        lock.parent.mkdir(parents=True, exist_ok=True)
        lock.write_text("pid=999999" + NL, encoding="utf-8")
        result = self.run_wds()
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("Traceback", result.stderr)
        self.assertIn("并发实例被拒", result.stderr)
        self.assertIn("pid=999999", result.stderr)
        self.assertIn("删除该文件", result.stderr)
        self.assertFalse(self.log.exists(), "锁拒绝后仍 spawn 了子会话")
        self.assertEqual(self.status_of(), "结构稿中")
        lock.unlink()

    def test_second_runner_refused_while_first_holds_lock(self):
        # ③ 真并发：第一个 runner 持锁在跑 → 第二个被拒；第一个跑完锁释放
        env = {**os.environ, **self.env(**{"DIY_WDS_SLEEP": "1.2"}), "PYTHONUTF8": "1"}
        proc = subprocess.Popen(
            [sys.executable, str(RUNNER), "--project-root", str(self.root),
             "--line", "wds", "--claude-cmd", sys.executable, str(self.stub)],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8",
            errors="replace", stdin=subprocess.DEVNULL, env=env,
        )
        try:
            deadline = time.time() + WDS_LOCK_WAIT
            while not self.lock_path().exists() and time.time() < deadline:
                time.sleep(0.02)
            self.assertTrue(self.lock_path().exists(), "第一个 runner 未持锁（并发闸未生效）")
            second = self.run_wds()
            self.assertNotEqual(second.returncode, 0, "并发第二个 runner 未被拒绝")
            self.assertIn("并发实例被拒", second.stderr)
            first_out, _ = proc.communicate(timeout=WDS_FIRST_RUN_TIMEOUT)
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.communicate()
        self.assertEqual(proc.returncode, 0, first_out)
        self.assertEqual(self.status_of(), "待验收")
        self.assertFalse(self.lock_path().exists(), "首个 runner 结束未释放锁")

    def test_evolution_round_explicitly_not_driven(self):
        # ① 演进轮：无人值守环不驱动（显式声明 + 机械无 spawn）
        result = self.run_wds()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("演进轮（diy-wds-evolution）由人发起、不在无人值守环内——本轮未驱动",
                      result.stdout)
        self.assertNotIn("diy-wds-evolution", NL.join(read_log(self.log)),
                         "演进轮被无头驱动")


class TC_WDS_EvolutionNotice(WdsCase):
    # trace: §5b #7① + 低-2（主 agent 终裁）：「演进轮由人发起、不在无人值守环内——本轮未驱动」
    # 声明行属「任何退出路径都不得缺失」的收尾面。原先只在 wds_summary 内打印，F-2 的停手路径
    # （WdsPageOffTrack）绕过汇总使该行消失；现由 run_wds_line 的统一收尾（finally）打印。
    NOTICE = "[runner] 演进轮（diy-wds-evolution）由人发起、不在无人值守环内——本轮未驱动"

    def test_notice_on_normal_path_exactly_once(self):
        result = self.run_wds()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.count(self.NOTICE), 1, "声明行缺失或重复打印")
        self.assertLess(result.stdout.index("SC-01.P1 → 待用户批准"),
                        result.stdout.index("演进轮"), "声明行应在汇总（含待批准）之后")

    def test_notice_on_every_exit_path(self):
        # 四条退出路径逐一钉死：正常汇总 / 停手报错 / 门禁拒绝 / 锁拒绝
        with self.subTest(path="正常汇总"):
            self.rebuild({"SC-01.P1": "结构稿中"})
            self.assertIn(self.NOTICE, self.run_wds().stdout)
        with self.subTest(path="停手（审查代批）"):
            self.rebuild({"SC-01.P1": "结构稿中"})
            result = self.run_wds(
                env_extra=self.env(**{"DIY_WDS_ROUTING": "SC-01.P1 review:代批"}))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("停手不重试", result.stderr)
            self.assertIn(self.NOTICE, result.stdout, "停手路径缺演进轮声明行")
        with self.subTest(path="门禁拒绝"):
            self.rebuild(None)
            result = self.run_wds()
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(self.NOTICE, result.stdout)
            self.assertFalse(self.log.exists(), "门禁拒绝仍 spawn 了子会话")
        with self.subTest(path="锁拒绝"):
            self.rebuild({"SC-01.P1": "结构稿中"})
            lock = self.lock_path()
            lock.parent.mkdir(parents=True, exist_ok=True)
            lock.write_text("pid=999999" + NL, encoding="utf-8")
            result = self.run_wds()
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("并发实例被拒", result.stderr)
            self.assertIn(self.NOTICE, result.stdout, "锁拒绝路径缺演进轮声明行")


class TC_Line_Contrast(WdsCase):
    # trace: §5b 回报必答①（分线对照实跑）+ 保真面（主线路径零变化）
    def test_same_output_dir_two_lines(self):
        self.rebuild({"SC-01.P1": "结构稿中"}, sprint_statuses={"S-1": "待办"})
        sprint = self.root / "diy-output" / "sprint.yaml"
        design_before = self.design.read_text(encoding="utf-8")
        main_log = self.root / "calls.log"
        mainline = run_runner(self.root, {
            "DIY_STUB_ROUTING": "S-1:已完成",
            "DIY_STUB_LOG": str(main_log),
            "DIY_STUB_SPRINT": str(sprint),
        })
        self.assertEqual(mainline.returncode, 0, mainline.stderr)
        self.assertEqual(read_tasks(sprint)["S-1"]["status"], "已完成")
        self.assertEqual(read_log(main_log), ["S-1 已完成", "S-1 augment"])
        self.assertEqual(self.design.read_text(encoding="utf-8"), design_before,
                         "主线入口改动了 design.yaml")
        sprint_after_mainline = sprint.read_text(encoding="utf-8")

        wds = self.run_wds()
        self.assertEqual(wds.returncode, 0, wds.stderr)
        self.assertEqual(self.status_of(), "待验收")
        self.assertEqual(sprint.read_text(encoding="utf-8"), sprint_after_mainline,
                         "WDS 入口改动了 sprint.yaml")

    def test_explicit_mainline_equals_default(self):
        # --line mainline 显式给 = 缺省不给：两次同构运行的日志与终态逐字相等
        logs = []
        for runner_args in ((), ("--line", "mainline")):
            root, sprint = make_fixture({"S-1": "待办", "S-2": "待办"})
            log = root / "calls.log"
            result = run_runner(root, {
                "DIY_STUB_ROUTING": "S-1:已完成,S-2:已阻塞",
                "DIY_STUB_LOG": str(log),
                "DIY_STUB_SPRINT": str(sprint),
            }, runner_args=runner_args)
            self.assertEqual(result.returncode, 0, result.stderr)
            logs.append((read_log(log), read_tasks(sprint),
                         [ln for ln in result.stdout.splitlines() if ln.startswith("[runner]")]))
            shutil.rmtree(root, ignore_errors=True)
        self.assertEqual(logs[0], logs[1], "--line mainline 与缺省行为不一致")

    def test_mainline_still_refuses_missing_sprint(self):
        # 主线门禁零变化：WDS 夹具（有 design.yaml、无 sprint.yaml）走主线仍拒
        result = run_runner(self.root, {}, stub=STUB)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("diy-sprint", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_invalid_line_value_is_usage_error(self):
        result = self.run_wds(runner_args=("--line", "wds2"))
        self.assertEqual(result.returncode, 2, "表外线名应走 argparse 用法错误")
        self.assertIn("--line", result.stderr)


class TC_WDS_StatusLexicon(unittest.TestCase):
    # trace: 裁定 5 / §5b #3——页状态词表归 diy-design 引擎（design.py PAGE_STATUSES），
    # runner 的 PAGE_STATUSES_ALL 只是汇总计数用的只读副本。本类把「只读、不另铸」机械钉死：
    # 引擎词表增删/改序（或 runner 侧副本漂移）即红，不靠人读注释对账（F-5 登记项落地）
    def test_page_statuses_all_matches_engine(self):
        engine = load_module("diy_design_engine", DESIGN_ENGINE)
        runner_mod = load_module("w6_runner", RUNNER)
        self.assertEqual(tuple(runner_mod.PAGE_STATUSES_ALL), tuple(engine.PAGE_STATUSES),
                         "runner 的页状态词表与引擎 design.py PAGE_STATUSES 不一致"
                         "（词表归引擎，runner 只读不另铸）")
        for name in ("PAGE_DRAFT", "PAGE_ACCEPT", "PAGE_INITIAL"):
            with self.subTest(constant=name):
                self.assertIn(getattr(runner_mod, name), engine.PAGE_STATUSES,
                              f"runner 的 {name} 不在引擎词表内")


if __name__ == "__main__":
    unittest.main()
