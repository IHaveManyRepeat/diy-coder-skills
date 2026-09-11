# -*- coding: utf-8 -*-
"""diy-help 状态机引擎 e2e 测试（S-13）。

夹具策略：临时目录写最小 YAML（仅 status 字段）——引擎按设计只读产物
存在性与 status，夹具聚焦该契约本身。不触碰真实 diy-output。
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
HELP_PY = os.path.join(HERE, "..", "skills", "diy-help", "scripts", "help.py")


def run_help(root):
    p = subprocess.run(
        [sys.executable, HELP_PY, "--project-root", root, "--json"],
        capture_output=True, text=True, encoding="utf-8",
    )
    return p


def write_artifact(out, name, status):
    with open(os.path.join(out, name), "w", encoding="utf-8") as f:
        f.write("project:\n  status: %s\n" % status)



def planning_chain_final(out):
    for name in ("prd.yaml", "architecture.yaml",
                 "epics.yaml", "stories.yaml", "test-plan.yaml"):
        write_artifact(out, name, "final")


def write_sprint(out, tasks):
    lines = ["project:", "  status: final", "tasks:"]
    for sid, st in tasks:
        lines += ["- story: %s" % sid, "  status: %s" % st]
    with open(os.path.join(out, "sprint.yaml"), "w", encoding="utf-8") as f:
        f.write(chr(10).join(lines) + chr(10))


class HelpStateMachineTests(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        self.out = os.path.join(self.root, "diy-output")
        os.makedirs(self.out)

    def tearDown(self):
        self.tmp.cleanup()

    # trace: S-13 AC-13.1 TC-13.1.1
    def test_full_planning_chain_recommends_sprint(self):
        # 前置：规划链五产物 final（openapi 缺失=无 API 面，合法跳过），无 sprint.yaml
        for name in ("prd.yaml", "architecture.yaml",
                     "epics.yaml", "stories.yaml", "test-plan.yaml"):
            write_artifact(self.out, name, "final")
        p = run_help(self.root)
        self.assertEqual(p.returncode, 0, p.stderr)
        data = json.loads(p.stdout)
        self.assertEqual(data["next_skill"], "diy-sprint")
        self.assertIsNone(data["blocked"])

    # trace: S-13 AC-13.1 TC-13.1.2
    def test_only_prd_recommends_architecture(self):
        write_artifact(self.out, "prd.yaml", "final")
        p = run_help(self.root)
        self.assertEqual(p.returncode, 0, p.stderr)
        data = json.loads(p.stdout)
        self.assertEqual(data["next_skill"], "diy-architecture")
        self.assertIsNone(data["blocked"])

    # trace: S-13 AC-13.2 TC-13.2.1
    def test_draft_test_plan_reports_blocker(self):
        for name in ("prd.yaml", "architecture.yaml",
                     "epics.yaml", "stories.yaml"):
            write_artifact(self.out, name, "final")
        write_artifact(self.out, "test-plan.yaml", "draft")
        p = run_help(self.root)
        self.assertEqual(p.returncode, 0, p.stderr)
        data = json.loads(p.stdout)
        self.assertIsNone(data["next_skill"])
        blocked = data["blocked"]
        self.assertEqual(blocked["file"], "test-plan.yaml")
        self.assertEqual(blocked["status"], "draft")
        self.assertIn("diy-test-design", blocked["action"])
        # 反静态菜单：人类输出指明文件与状态，而非罗列全部 skill
        pj = subprocess.run(
            [sys.executable, HELP_PY, "--project-root", self.root],
            capture_output=True, text=True, encoding="utf-8",
        )
        out = pj.stdout
        self.assertIn("test-plan.yaml", out)
        self.assertIn("draft", out)
        # 反静态菜单：不得出现与当前阻塞状态无关的执行类 skill 罗列
        for s in ("diy-build-loop", "diy-dev", "diy-review",
                  "diy-help", "diy-viewer"):
            self.assertNotIn(s, out, "输出退化为静态菜单：包含无关 skill %s" % s)

    # trace: S-13 AC-13.1 TC-13.1.3
    def test_sprint_open_tasks_recommend_build_loop(self):
        planning_chain_final(self.out)
        write_sprint(self.out, [("S-1", "done"), ("S-2", "pending")])
        p = run_help(self.root)
        self.assertEqual(p.returncode, 0, p.stderr)
        data = json.loads(p.stdout)
        self.assertEqual(data["next_skill"], "diy-build-loop")
        self.assertIsNone(data["blocked"])

    # trace: S-13 AC-13.1 TC-13.1.4
    def test_sprint_all_done_workflow_complete(self):
        planning_chain_final(self.out)
        write_sprint(self.out, [("S-1", "done"), ("S-2", "done")])
        p = run_help(self.root)
        self.assertEqual(p.returncode, 0, p.stderr)
        data = json.loads(p.stdout)
        self.assertTrue(data["workflow_done"])
        self.assertIsNone(data["next_skill"])
        self.assertIsNone(data["blocked"])

    # trace: S-13 AC-13.1 TC-13.1.5
    def test_sprint_blocked_task_directs_human(self):
        planning_chain_final(self.out)
        write_sprint(self.out, [("S-1", "done"), ("S-9", "blocked")])
        p = run_help(self.root)
        self.assertEqual(p.returncode, 0, p.stderr)
        data = json.loads(p.stdout)
        self.assertIsNone(data["next_skill"])
        blocked = data["blocked"]
        self.assertEqual(blocked["file"], "sprint.yaml")
        self.assertEqual(blocked["status"], "blocked")
        self.assertIn("S-9", blocked["action"])
        self.assertIn("人工", blocked["action"])


if __name__ == "__main__":
    unittest.main()
