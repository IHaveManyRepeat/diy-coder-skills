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


def run_help(root, *extra):
    p = subprocess.run(
        [sys.executable, HELP_PY, "--project-root", root, "--json", *extra],
        capture_output=True, text=True, encoding="utf-8", timeout=60,
    )
    return p


def write_artifact(out, name, status):
    with open(os.path.join(out, name), "w", encoding="utf-8") as f:
        f.write("project:\n  status: %s\n" % status)



def planning_chain_final(out):
    for name in ("prd.yaml", "architecture.yaml",
                 "epics.yaml", "stories.yaml", "test-plan.yaml"):
        write_artifact(out, name, "已定稿")


def write_openapi(out, status, meta_key="x-project"):
    # 契约来源：diy-openapi/SKILL.md:19 —— 项目元数据在 x-project 扩展（非 project 根键）
    with open(os.path.join(out, "openapi.yaml"), "w", encoding="utf-8") as f:
        f.write("openapi: 3.1.0" + chr(10) + "%s:" % meta_key + chr(10)
                + "  status: %s" % status + chr(10))


def write_sprint(out, tasks):
    lines = ["project:", "  status: 已定稿", "tasks:"]
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
        # 前置：规划链五产物 已定稿（openapi 缺失=无 API 面，合法跳过），无 sprint.yaml
        for name in ("prd.yaml", "architecture.yaml",
                     "epics.yaml", "stories.yaml", "test-plan.yaml"):
            write_artifact(self.out, name, "已定稿")
        p = run_help(self.root)
        self.assertEqual(p.returncode, 0, p.stderr)
        data = json.loads(p.stdout)
        self.assertEqual(data["next_skill"], "diy-sprint")
        self.assertIsNone(data["blocked"])

    # trace: S-13 AC-13.1 TC-13.1.2
    def test_only_prd_recommends_architecture(self):
        write_artifact(self.out, "prd.yaml", "已定稿")
        p = run_help(self.root)
        self.assertEqual(p.returncode, 0, p.stderr)
        data = json.loads(p.stdout)
        self.assertEqual(data["next_skill"], "diy-architecture")
        self.assertIsNone(data["blocked"])

    # trace: S-13 AC-13.2 TC-13.2.1
    def test_draft_test_plan_reports_blocker(self):
        for name in ("prd.yaml", "architecture.yaml",
                     "epics.yaml", "stories.yaml"):
            write_artifact(self.out, name, "已定稿")
        write_artifact(self.out, "test-plan.yaml", "草稿")
        p = run_help(self.root)
        self.assertEqual(p.returncode, 0, p.stderr)
        data = json.loads(p.stdout)
        self.assertIsNone(data["next_skill"])
        blocked = data["blocked"]
        self.assertEqual(blocked["file"], "test-plan.yaml")
        self.assertEqual(blocked["status"], "草稿")
        self.assertIn("diy-test-design", blocked["action"])
        # 反静态菜单：人类输出指明文件与状态，而非罗列全部 skill
        pj = subprocess.run(
            [sys.executable, HELP_PY, "--project-root", self.root],
            capture_output=True, text=True, encoding="utf-8",
        )
        out = pj.stdout
        self.assertIn("test-plan.yaml", out)
        self.assertIn("草稿", out)
        # 反静态菜单：不得出现与当前阻塞状态无关的执行类 skill 罗列
        for s in ("diy-build-loop", "diy-dev", "diy-review",
                  "diy-help", "diy-viewer"):
            self.assertNotIn(s, out, "输出退化为静态菜单：包含无关 skill %s" % s)

    # trace: S-13 AC-13.1 TC-13.1.3
    def test_sprint_open_tasks_recommend_build_loop(self):
        planning_chain_final(self.out)
        write_sprint(self.out, [("S-1", "已完成"), ("S-2", "待办")])
        p = run_help(self.root)
        self.assertEqual(p.returncode, 0, p.stderr)
        data = json.loads(p.stdout)
        self.assertEqual(data["next_skill"], "diy-build-loop")
        self.assertIsNone(data["blocked"])

    # trace: S-13 AC-13.1 TC-13.1.4
    def test_sprint_all_done_workflow_complete(self):
        planning_chain_final(self.out)
        write_sprint(self.out, [("S-1", "已完成"), ("S-2", "已完成")])
        p = run_help(self.root)
        self.assertEqual(p.returncode, 0, p.stderr)
        data = json.loads(p.stdout)
        self.assertTrue(data["workflow_done"])
        self.assertIsNone(data["next_skill"])
        self.assertIsNone(data["blocked"])

    # trace: S-13 AC-13.1 TC-13.1.5
    def test_sprint_blocked_task_directs_human(self):
        planning_chain_final(self.out)
        write_sprint(self.out, [("S-1", "已完成"), ("S-9", "已阻塞")])
        p = run_help(self.root)
        self.assertEqual(p.returncode, 0, p.stderr)
        data = json.loads(p.stdout)
        self.assertIsNone(data["next_skill"])
        blocked = data["blocked"]
        self.assertEqual(blocked["file"], "sprint.yaml")
        self.assertEqual(blocked["status"], "已阻塞")
        self.assertIn("S-9", blocked["action"])
        self.assertIn("人工", blocked["action"])

    # trace: S-13 AC-13.1 TC-13.1.6
    def test_half_written_artifacts_do_not_crash(self):
        # 夹具一：sprint.yaml 的 project 与 tasks 均为 null（LLM 半写中断）
        planning_chain_final(self.out)
        with open(os.path.join(self.out, "sprint.yaml"), "w", encoding="utf-8") as f:
            f.write("project:" + chr(10) + "tasks:" + chr(10))
        p = run_help(self.root)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertNotIn("Traceback", p.stderr)
        data = json.loads(p.stdout)
        self.assertEqual(data["blocked"]["file"], "sprint.yaml")
        self.assertTrue(data["blocked"]["action"])
        # 夹具二：配置 paths 为 null
        os.remove(os.path.join(self.out, "sprint.yaml"))
        with open(os.path.join(self.root, "diy-coder.yaml"), "w", encoding="utf-8") as f:
            f.write("paths:" + chr(10))
        p2 = run_help(self.root)
        self.assertEqual(p2.returncode, 0, p2.stderr)
        self.assertNotIn("Traceback", p2.stderr)
        json.loads(p2.stdout)  # 输出仍是合法 JSON

    # trace: S-13 AC-13.1 TC-13.1.6
    def test_sprint_final_but_tasks_null_blocks_at_sprint_stage(self):
        # 对抗审查 R2：链全 final 时 tasks: null 不得被 `or []` 吞成"推荐 build-loop"
        planning_chain_final(self.out)
        with open(os.path.join(self.out, "sprint.yaml"), "w", encoding="utf-8") as f:
            f.write("project:" + chr(10) + "  status: 已定稿" + chr(10) + "tasks:" + chr(10))
        p = run_help(self.root)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertNotIn("Traceback", p.stderr)
        data = json.loads(p.stdout)
        self.assertEqual(data["blocked"]["file"], "sprint.yaml")
        self.assertEqual(data["blocked"]["status"], "unparsable")

    # trace: S-13 AC-13.1 TC-13.1.6
    def test_non_string_story_in_blocked_task_no_crash(self):
        # 对抗审查 R2：story 节点为映射时 ", ".join 不得裸栈
        planning_chain_final(self.out)
        with open(os.path.join(self.out, "sprint.yaml"), "w", encoding="utf-8") as f:
            f.write("project:" + chr(10) + "  status: 已定稿" + chr(10) + "tasks:" + chr(10)
                    + "- story:" + chr(10) + "    id: S-1" + chr(10)
                    + "  status: 已阻塞" + chr(10))
        p = run_help(self.root)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertNotIn("Traceback", p.stderr)
        data = json.loads(p.stdout)
        self.assertEqual(data["blocked"]["status"], "已阻塞")
        self.assertIn("S-1", data["blocked"]["action"])


    # trace: F-A1-1（openapi 定稿写在 x-project.status，链必须继续而非假阻塞）
    def test_openapi_x_project_final_advances_chain(self):
        planning_chain_final(self.out)
        write_openapi(self.out, "已定稿")
        p = run_help(self.root)
        self.assertEqual(p.returncode, 0, p.stderr)
        data = json.loads(p.stdout)
        self.assertEqual(data["next_skill"], "diy-sprint")
        self.assertIsNone(data["blocked"])
        self.assertIn("diy-openapi", data["completed_steps"])

    # trace: F-A1-1（声明路径读不到时回落 project.status，兼容两种 meta 位置）
    def test_openapi_project_status_fallback_still_reads(self):
        planning_chain_final(self.out)
        write_openapi(self.out, "已定稿", meta_key="project")
        p = run_help(self.root)
        self.assertEqual(p.returncode, 0, p.stderr)
        data = json.loads(p.stdout)
        self.assertEqual(data["next_skill"], "diy-sprint")
        self.assertIsNone(data["blocked"])

    # trace: F-A1-2（x-project.status: draft → 阻塞在 openapi，动作指向 diy-openapi）
    def test_openapi_x_project_draft_blocks_with_action(self):
        write_artifact(self.out, "prd.yaml", "已定稿")
        write_artifact(self.out, "architecture.yaml", "已定稿")
        write_openapi(self.out, "草稿")
        p = run_help(self.root)
        self.assertEqual(p.returncode, 0, p.stderr)
        data = json.loads(p.stdout)
        self.assertIsNone(data["next_skill"])
        self.assertEqual(data["blocked"]["file"], "openapi.yaml")
        self.assertEqual(data["blocked"]["status"], "草稿")
        self.assertIn("diy-openapi", data["blocked"]["action"])

    # trace: F-A2-1（design.yaml 缺失=optional 跳过，notes 给 diy-design 提示）
    def test_design_missing_is_optional_with_note(self):
        planning_chain_final(self.out)
        p = run_help(self.root)
        self.assertEqual(p.returncode, 0, p.stderr)
        data = json.loads(p.stdout)
        self.assertEqual(data["next_skill"], "diy-sprint")
        self.assertTrue(any("diy-design" in n for n in data["notes"]),
                        "design.yaml 缺失时未给出 diy-design 提示：%s" % data["notes"])

    # trace: F-A2-2（design.yaml 存在但 draft → 半成品不可静默跳过）
    def test_design_draft_blocks_at_design(self):
        write_artifact(self.out, "prd.yaml", "已定稿")
        write_artifact(self.out, "architecture.yaml", "已定稿")
        write_artifact(self.out, "design.yaml", "草稿")
        p = run_help(self.root)
        self.assertEqual(p.returncode, 0, p.stderr)
        data = json.loads(p.stdout)
        self.assertIsNone(data["next_skill"])
        self.assertEqual(data["blocked"]["file"], "design.yaml")
        self.assertEqual(data["blocked"]["status"], "草稿")
        self.assertIn("diy-design", data["blocked"]["action"])

    # trace: F-A2-3（design.yaml final → 计入 completed 并推进）
    def test_design_final_advances_to_epics(self):
        write_artifact(self.out, "prd.yaml", "已定稿")
        write_artifact(self.out, "architecture.yaml", "已定稿")
        write_artifact(self.out, "design.yaml", "已定稿")
        p = run_help(self.root)
        self.assertEqual(p.returncode, 0, p.stderr)
        data = json.loads(p.stdout)
        self.assertEqual(data["next_skill"], "diy-epics-stories")
        self.assertIn("diy-design", data["completed_steps"])

    # trace: F-A2-4（位置分母自动含 design 节点：7 步）
    def test_step_denominator_covers_seven_nodes(self):
        write_artifact(self.out, "prd.yaml", "已定稿")
        p = run_help(self.root)
        self.assertEqual(p.returncode, 0, p.stderr)
        data = json.loads(p.stdout)
        self.assertEqual(data["position"], "第 2/7 步：diy-architecture")

    # trace: F-A3a（多文件节点只落一半 → 不得计入 completed，推荐本节点 skill）
    def test_partial_multi_file_node_not_completed(self):
        write_artifact(self.out, "prd.yaml", "已定稿")
        write_artifact(self.out, "architecture.yaml", "已定稿")
        write_artifact(self.out, "epics.yaml", "已定稿")  # stories.yaml 缺失=半写
        p = run_help(self.root)
        self.assertEqual(p.returncode, 0, p.stderr)
        data = json.loads(p.stdout)
        self.assertEqual(data["next_skill"], "diy-epics-stories")
        self.assertNotIn("diy-epics-stories", data["completed_steps"])
        self.assertIsNone(data["blocked"])

    # trace: F-A3b（paths 为真值标量 → 降级默认值，不崩）
    def test_scalar_paths_config_degrades_to_default(self):
        with open(os.path.join(self.root, "diy-coder.yaml"), "w", encoding="utf-8") as f:
            f.write("paths: diy-output" + chr(10))
        p = run_help(self.root)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertNotIn("Traceback", p.stderr)
        data = json.loads(p.stdout)
        self.assertEqual(data["next_skill"], "diy-prd")

    # trace: 对抗审查修复——paths.output_dir 值非字符串（如 123）降级默认，不崩
    def test_non_string_output_dir_degrades_to_default(self):
        with open(os.path.join(self.root, "diy-coder.yaml"), "w", encoding="utf-8") as f:
            f.write("paths:" + chr(10) + "  output_dir: 123" + chr(10))
        p = run_help(self.root)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertNotIn("Traceback", p.stderr)
        data = json.loads(p.stdout)
        self.assertEqual(data["next_skill"], "diy-prd")

    # trace: 对抗审查修复——中段键值为标量（project: 3）判 unparsable，不静默回落 unknown
    def test_scalar_meta_section_marks_unparsable(self):
        with open(os.path.join(self.out, "prd.yaml"), "w", encoding="utf-8") as f:
            f.write("project: 3" + chr(10))
        p = run_help(self.root)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertNotIn("Traceback", p.stderr)
        data = json.loads(p.stdout)
        self.assertEqual(data["blocked"]["status"], "unparsable")

    # trace: 对抗审查修复——实例名白名单统一（fullmatch 去 $ 漏洞）："a\n"/尾点等必须拒
    def test_invalid_instance_name_rejected(self):
        for bad in ("a" + chr(10), "a.", ".hidden", "a/b"):
            with self.subTest(instance=bad):
                p = run_help(self.root, "--instance", bad)
                self.assertNotEqual(p.returncode, 0, f"{bad!r} 未被拒绝")
                self.assertNotIn("Traceback", p.stderr)
                self.assertIn("非法实例名", p.stderr)

    def test_legal_instance_name_accepted(self):
        p = run_help(self.root, "--instance", "case-a")
        self.assertEqual(p.returncode, 0, p.stderr)

    # trace: F-A3c（YAML 损坏 → 阻塞动作是「修复后重跑」，不是「继续定稿」）
    def test_corrupt_prd_yaml_blocks_with_repair_action(self):
        with open(os.path.join(self.out, "prd.yaml"), "w", encoding="utf-8") as f:
            f.write("project: [unclosed" + chr(10))
        p = run_help(self.root)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertNotIn("Traceback", p.stderr)
        data = json.loads(p.stdout)
        self.assertEqual(data["blocked"]["file"], "prd.yaml")
        self.assertEqual(data["blocked"]["status"], "unparsable")
        self.assertIn("修复", data["blocked"]["action"])

    # trace: F-A3c（status 为 null → 归一 unknown，不给「当前状态 None」）
    def test_null_status_normalized_to_unknown(self):
        with open(os.path.join(self.out, "prd.yaml"), "w", encoding="utf-8") as f:
            f.write("project:" + chr(10) + "  status:" + chr(10))
        p = run_help(self.root)
        self.assertEqual(p.returncode, 0, p.stderr)
        data = json.loads(p.stdout)
        self.assertEqual(data["blocked"]["status"], "unknown")
        self.assertIn("修复", data["blocked"]["action"])

    # trace: F-A3d（tasks: [] 与 tasks: null 同判阻断）
    def test_sprint_empty_tasks_blocks(self):
        planning_chain_final(self.out)
        with open(os.path.join(self.out, "sprint.yaml"), "w", encoding="utf-8") as f:
            f.write("project:" + chr(10) + "  status: 已定稿" + chr(10)
                    + "tasks: []" + chr(10))
        p = run_help(self.root)
        self.assertEqual(p.returncode, 0, p.stderr)
        data = json.loads(p.stdout)
        self.assertIsNone(data["next_skill"])
        self.assertEqual(data["blocked"]["file"], "sprint.yaml")
        self.assertIn("空", data["blocked"]["action"])


if __name__ == "__main__":
    unittest.main()
