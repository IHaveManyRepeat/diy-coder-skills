# -*- coding: utf-8 -*-
"""exp-sync 经验库同步器交付验收（S-17）。

夹具策略：临时目录造最小项目（diy-coder.yaml + bug-log.yaml）与临时经验库
（git init + bugs/），验证跨项目合并写入、路径归一与异常路径一行报错。
不触碰真实经验库与真实 diy-output。
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.join(HERE, "..", "exp-sync.py")

BUG_TMPL = """\
project:
  name: {proj}
bugs:
  - id: {bid}
    date: 2026-09-13
    source: 开发
    class: 功能型
    subclass: 逻辑
    type: 逻辑错误
    trigger: 触发路径
    fix: 修复方案
    prevention: 防复发机制
"""


def git_init(repo):
    subprocess.run(["git", "init", "-q", repo], check=True)


def write_project(base, name, bugs_yaml, repo):
    out = os.path.join(base, "diy-output")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(base, "diy-coder.yaml"), "w", encoding="utf-8") as f:
        f.write("project:\n  name: %s\npaths:\n  output_dir: diy-output\n"
                "  experience_repo: \"%s\"\n" % (name, repo.replace(os.sep, "/")))
    with open(os.path.join(out, "bug-log.yaml"), "w", encoding="utf-8") as f:
        f.write(bugs_yaml)


def run_exp(args, cwd, env_extra=None):
    env = {**os.environ, **(env_extra or {})}
    return subprocess.run([sys.executable, EXP] + args, cwd=cwd,
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace", env=env)


class ExpSyncTests(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        self.repo = os.path.join(self.root, "exp")
        os.makedirs(os.path.join(self.repo, "bugs"))
        git_init(self.repo)
        self.proj_a = os.path.join(self.root, "proj-a")
        self.proj_b = os.path.join(self.root, "proj-b")

    def tearDown(self):
        self.tmp.cleanup()

    def bucket_ids(self):
        # 桶文件名 = 中类取值（exp-sync 按 subclass 分桶）
        with open(os.path.join(self.repo, "bugs", "逻辑.yaml"), encoding="utf-8") as f:
            return [e["id"] for e in (yaml.safe_load(f) or {}).get("bugs") or []]

    # trace: S-17 AC-17.1 TC-17.1.1
    def test_cross_project_push_merges_and_is_idempotent(self):
        write_project(self.proj_a, "proj-a",
                      BUG_TMPL.format(proj="proj-a", bid="BUG-A1"), self.repo)
        write_project(self.proj_b, "proj-b",
                      BUG_TMPL.format(proj="proj-b", bid="BUG-B1"), self.repo)
        p = run_exp(["push"], cwd=self.proj_a)
        self.assertEqual(p.returncode, 0, p.stderr)
        p = run_exp(["push"], cwd=self.proj_b)
        self.assertEqual(p.returncode, 0, p.stderr)
        ids = self.bucket_ids()
        self.assertIn("BUG-A1", ids, "第二个项目 push 冲掉了第一个项目的条目")
        self.assertIn("BUG-B1", ids)
        with open(os.path.join(self.repo, "index.html"), encoding="utf-8") as f:
            html = f.read()
        self.assertIn("BUG-A1", html)
        self.assertIn("BUG-B1", html)
        # 幂等：A 再次 push 不重复、不删 B
        p = run_exp(["push"], cwd=self.proj_a)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(sorted(self.bucket_ids()), ["BUG-A1", "BUG-B1"])

    # trace: S-17 AC-17.2 TC-17.2.1
    def test_tilde_path_expanded(self):
        name = "diy-exp-probe-%d" % os.getpid()
        home_dir = os.path.join(os.path.expanduser("~"), name)
        self.addCleanup(lambda: shutil.rmtree(home_dir, ignore_errors=True))
        os.makedirs(os.path.join(self.root, "diy-output"))
        with open(os.path.join(self.root, "diy-coder.yaml"), "w", encoding="utf-8") as f:
            f.write("project:\n  name: probe\npaths:\n  output_dir: diy-output\n"
                    "  experience_repo: \"~/%s\"\n" % name)
        p = run_exp(["init"], cwd=self.root)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertTrue(os.path.isdir(os.path.join(home_dir, "bugs")), "~ 未展开为家目录")
        self.assertFalse(os.path.exists(os.path.join(self.root, "~")), "项目根出现字面 ~ 目录")

    # trace: S-17 AC-17.1 TC-17.1.1
    def test_non_list_bugs_bucket_reports_one_line(self):
        # 对抗审查 R1：桶文件 bugs 值为映射时，合并写入会把键字符串当条目搬进新桶
        write_project(self.proj_a, "proj-a",
                      BUG_TMPL.format(proj="proj-a", bid="BUG-A1"), self.repo)
        bad = os.path.join(self.repo, "bugs", "逻辑.yaml")
        with open(bad, "w", encoding="utf-8") as f:
            f.write("bugs:" + chr(10) + "  BUG-A1:" + chr(10) + "    id: BUG-A1" + chr(10))
        p = run_exp(["push"], cwd=self.proj_a)
        self.assertNotEqual(p.returncode, 0)
        self.assertNotIn("Traceback", p.stderr)
        self.assertIn("逻辑.yaml", p.stderr)
        with open(bad, encoding="utf-8") as f:
            raw = f.read()
        self.assertNotIn("- BUG-A1" + chr(10), raw, "坏桶被污染改写")

    # trace: S-17 AC-17.2 TC-17.2.1
    def test_env_var_path_expanded(self):
        # 对抗审查 R5：$VAR 形式路径同样必须展开（expanduser 之外）
        fake_home = os.path.join(self.root, "fake-home")
        os.makedirs(os.path.join(self.root, "diy-output"))
        with open(os.path.join(self.root, "diy-coder.yaml"), "w", encoding="utf-8") as f:
            f.write("project:\n  name: probe\npaths:\n  output_dir: diy-output\n"
                    "  experience_repo: \"$EXP_SYNC_PROBE_HOME/exp\"\n")
        p = run_exp(["init"], cwd=self.root,
                    env_extra={"EXP_SYNC_PROBE_HOME": fake_home})
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertTrue(os.path.isdir(os.path.join(fake_home, "exp", "bugs")),
                        "$VAR 未展开为环境变量值")

    # trace: S-17 AC-17.2 TC-17.2.2
    def test_corrupt_bug_log_reports_one_line(self):
        write_project(self.proj_a, "proj-a",
                      "bugs:\n  - id: BUG-X\n   bad indent: [\n", self.repo)
        p = run_exp(["push"], cwd=self.proj_a)
        self.assertNotEqual(p.returncode, 0)
        self.assertNotIn("Traceback", p.stderr)
        self.assertIn("[exp-sync]", p.stderr)

    # trace: S-17 AC-17.2 TC-17.2.2
    def test_missing_bucket_dir_reports_one_line(self):
        repo2 = os.path.join(self.root, "exp-bare")
        os.makedirs(repo2)
        git_init(repo2)
        write_project(self.proj_b, "proj-b",
                      BUG_TMPL.format(proj="proj-b", bid="BUG-B1"), repo2)
        p = run_exp(["push"], cwd=self.proj_b)
        self.assertNotEqual(p.returncode, 0)
        self.assertNotIn("Traceback", p.stderr)
        self.assertIn("init", p.stderr)

    # trace: 2026-09-13 质量分析 F-customization-1（实例模式 push 提示失效，硬编码主线 bug-log 路径）
    def test_push_instance_reads_instance_bug_log(self):
        write_project(self.proj_a, "proj-a",
                      BUG_TMPL.format(proj="proj-a", bid="BUG-MAIN"), self.repo)
        inst = os.path.join(self.proj_a, "diy-output", "inst-x")
        os.makedirs(inst)
        with open(os.path.join(inst, "bug-log.yaml"), "w", encoding="utf-8") as f:
            f.write(BUG_TMPL.format(proj="proj-a", bid="BUG-INST"))
        p = run_exp(["push", "--instance", "inst-x"], cwd=self.proj_a)
        self.assertEqual(p.returncode, 0, p.stderr)
        ids = self.bucket_ids()
        self.assertIn("BUG-INST", ids)
        self.assertNotIn("BUG-MAIN", ids, "实例 push 读到了主线 bug-log")

    # trace: 2026-09-13 质量分析 F-customization-1（实例名校验同各 skill 规则 FR-4.5/D-9）；
    # 对抗审查修复后锁定：尾点（Windows 目录名折叠）、尾换行（$ 锚点漏洞）必须拒
    def test_push_invalid_instance_name_refused(self):
        write_project(self.proj_a, "proj-a",
                      BUG_TMPL.format(proj="proj-a", bid="BUG-A1"), self.repo)
        for bad in ("../evil", "a.", "a" + chr(10)):
            with self.subTest(instance=bad):
                p = run_exp(["push", "--instance", bad], cwd=self.proj_a)
                self.assertNotEqual(p.returncode, 0, f"{bad!r} 未被拒绝")
                self.assertNotIn("Traceback", p.stderr)
                self.assertIn("[exp-sync]", p.stderr)

    # trace: 对抗审查修复（P2）——paths 段标量（resolve_repo 拒）或 output_dir 值非字符串（do_push 拒）
    # 时一行报错，不裸栈
    def test_malformed_paths_config_reports_one_line(self):
        repo_fwd = self.repo.replace(os.sep, "/")
        cases = [
            "paths: diy-output" + chr(10),
            "paths:" + chr(10) + "  output_dir: 123" + chr(10)
            + "  experience_repo: \"%s\"" % repo_fwd + chr(10),
        ]
        for cfg in cases:
            with self.subTest(cfg=cfg.strip()):
                write_project(self.proj_a, "proj-a",
                              BUG_TMPL.format(proj="proj-a", bid="BUG-A1"), self.repo)
                with open(os.path.join(self.proj_a, "diy-coder.yaml"), "w",
                          encoding="utf-8") as f:
                    f.write("project:" + chr(10) + "  name: proj-a" + chr(10) + cfg)
                p = run_exp(["push"], cwd=self.proj_a)
                self.assertNotEqual(p.returncode, 0)
                self.assertNotIn("Traceback", p.stderr)
                self.assertIn("[exp-sync]", p.stderr)
                self.assertIn("diy-coder.yaml", p.stderr)

    # trace: 2026-09-13 质量分析 F-customization-1（--instance 仅 push 有意义，静默忽略即撒谎）
    def test_instance_flag_refused_for_status(self):
        write_project(self.proj_a, "proj-a",
                      BUG_TMPL.format(proj="proj-a", bid="BUG-A1"), self.repo)
        p = run_exp(["status", "--instance", "inst-x"], cwd=self.proj_a)
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("[exp-sync]", p.stderr)


if __name__ == "__main__":
    unittest.main()
