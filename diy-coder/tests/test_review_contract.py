# -*- coding: utf-8 -*-
"""diy-review 分层审查契约测试（2026-09-13 skill 质量分析发现固化）。

契约来源：diy-review/.analysis/2026-09-13-1117（19 项发现，rank1-4 修复轮）——
- architecture-1：L4 设计采用必须接进可执行路径（Workflow + schema 枚举 + 命名一致）
- architecture-2：schema layer 枚举须能记录 L4 命中
- architecture-3：证伪轮命中须授权 done → in-progress 回退
- architecture-4：bad_spec 分流与 Routing 表 / diy-build-loop 冲突
- enhancement-1：旧「三层」回述导致 L4 被默认漏掉
- enhancement-3：全部任务完成后证伪轮无可达入口
"""
import io
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_REVIEW = os.path.join(HERE, "..", "skills", "diy-review", "SKILL.md")
SKILL_LOOP = os.path.join(HERE, "..", "skills", "diy-build-loop", "SKILL.md")
VIEWER = os.path.join(HERE, "..", "skills", "diy-viewer", "scripts", "viewer.py")
HELP = os.path.join(HERE, "..", "skills", "diy-help", "scripts", "help.py")


def read(path):
    with io.open(path, encoding="utf-8") as f:
        return f.read()


class ReviewL4WiringTests(unittest.TestCase):

    # trace: F-architecture-1（L4 只写在 Layers 节，Workflow 不执行）
    def test_l4_runs_inside_workflow(self):
        workflow = read(SKILL_REVIEW).split("## Workflow", 1)[1]
        self.assertIn("L4", workflow, "Workflow 未接 L4 设计采用")
        self.assertIn("design_ref", workflow, "Workflow 缺 design_ref 触发条件")

    # trace: F-architecture-2（layer 枚举缺 design）
    def test_schema_layer_enum_has_design(self):
        self.assertIn("正确性|边界|覆盖审计|设计采用", read(SKILL_REVIEW),
                      "schema layer 枚举缺 设计采用（L4 命中无法记录）")

    # trace: F-enhancement-1（description 仍称三层）
    def test_description_covers_l4(self):
        self.assertIn("design adoption", read(SKILL_REVIEW), "description 未覆盖 L4")


class StaleNamingTests(unittest.TestCase):

    # trace: F-enhancement-1（回述旧「三层」模式使 L4 默认漏掉）
    def test_review_skill_drops_three_layer_naming(self):
        review = read(SKILL_REVIEW)
        self.assertNotIn("## Three Layers", review, "仍用 Three Layers 标题")
        self.assertNotIn("three layers", review.lower(), "仍称 three layers")

    # trace: F-enhancement-1（build-loop 回述三层）
    def test_build_loop_names_l1_l4(self):
        loop = read(SKILL_LOOP)
        self.assertNotIn("three layers", loop.lower(), "build-loop 仍称 three layers")
        self.assertIn("L1-L4", loop, "build-loop 未按 L1-L4 描述审查阶段")

    # trace: F-enhancement-1（viewer 术语仍称三层审查 / 缺 design 层映射）
    def test_viewer_terms_updated(self):
        viewer = read(VIEWER)
        self.assertNotIn("三层审查（正确性/边界/覆盖审计）", viewer, "审查记录术语未更新")
        self.assertNotIn("等待三层审查", viewer, "待审查术语未更新")
        self.assertIn('"设计采用": "设计采用"', viewer, "viewer 缺 设计采用 层展示映射（英文值直出）")


class FalsificationEntryTests(unittest.TestCase):

    # trace: F-enhancement-3（硬门禁只开 review 态，done 后无入口）
    def test_falsify_accepted_for_done_targets(self):
        act = read(SKILL_REVIEW).split("## On Activation", 1)[1].split("## Layers", 1)[0]
        self.assertIn("--falsify", act, "硬门禁未给 --falsify 开 done 例外")

    # trace: F-architecture-3（状态写入权「Nothing else」与证伪回退冲突）
    def test_falsification_reopen_is_authorized(self):
        self.assertIn("已完成 → 进行中", read(SKILL_REVIEW), "缺证伪回退的授权条款")

    # trace: F-enhancement-3（help 收尾提示未给命令入口）
    def test_help_points_to_falsify(self):
        self.assertIn("--falsify", read(HELP), "help 收尾未给证伪轮命令入口")


class VerdictRoutingTests(unittest.TestCase):

    # trace: F-architecture-4（bad_spec 原分流到 in-progress，与 Routing 表 / loop 冲突）
    def test_bad_spec_disposition_is_blocked(self):
        verdict = read(SKILL_REVIEW).split("## Verdict Rules", 1)[1].split("## Schema", 1)[0]
        self.assertIn("规格缺陷", verdict)
        self.assertIn("已阻塞", verdict, "规格缺陷 未分流到 已阻塞")


if __name__ == "__main__":
    unittest.main()
