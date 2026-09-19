# -*- coding: utf-8 -*-
"""S-7/S-9 真源回填条款测试（BUG-012 回归，2026-09-13 证伪轮）。

契约测试：执行链 skill 的 SKILL.md 必须写明状态真源回填——
- diy-dev：绿线后回填 test-plan.yaml 对应 TC 的 status: 通过 并 bump project.updated
- diy-build-loop：待审查→已完成 回填 stories.yaml 故事 status: 已完成 与 test-plan.yaml
  执行过的绿 TC status: 通过；已阻塞 终态不回写真源
- diy-review：独立路径的 待审查→已完成 同样回填（2026-09-13 质量分析 F-enhancement-2）
条款缺失 = 无人值守路径只写 sprint 投影，真源留 待办（BUG-012 复发）。
"""
import io
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DEV = os.path.join(HERE, "..", "skills", "diy-dev", "SKILL.md")
SKILL_LOOP = os.path.join(HERE, "..", "skills", "diy-build-loop", "SKILL.md")
SKILL_REVIEW = os.path.join(HERE, "..", "skills", "diy-review", "SKILL.md")


class WritebackTermsTests(unittest.TestCase):

    # trace: S-7 AC-7.1 TC-7.1.2
    def test_dev_contract_backfills_test_plan(self):
        dev = io.open(SKILL_DEV, encoding="utf-8").read()
        self.assertIn("真源回填", dev, "diy-dev 缺真源回填条款")
        self.assertIn("test-plan.yaml", dev)
        self.assertIn("status: 通过", dev, "缺 TC 状态回填动作")
        self.assertIn("project.updated", dev, "缺 updated 提升")

    # trace: S-7 AC-7.1 TC-7.1.2
    def test_dev_clause_not_duplicated(self):
        # 对抗审查 R6：条款被重复插入两次时 assertIn 天然查不出
        dev = io.open(SKILL_DEV, encoding="utf-8").read()
        self.assertEqual(dev.count("真源回填"), 1, "diy-dev 真源回填条款重复插入")

    # trace: S-9 AC-9.1 TC-9.1.2
    def test_build_loop_contract_backfills_terminal_sources(self):
        loop = io.open(SKILL_LOOP, encoding="utf-8").read()
        self.assertIn("真源回填", loop, "diy-build-loop 缺真源回填条款")
        self.assertIn("stories.yaml", loop)
        self.assertIn("status: 已完成", loop, "缺故事终态回填")
        self.assertIn("test-plan.yaml", loop)
        self.assertIn("status: 通过", loop, "缺绿 TC 回填")
        self.assertIn("不写 `stories.yaml`", loop, "缺 已阻塞 不回写真源的边界")

    # trace: F-enhancement-2（独立 review 路径 待审查→已完成 不回写真源）
    def test_review_contract_backfills_terminal_sources(self):
        with io.open(SKILL_REVIEW, encoding="utf-8") as f:
            review = f.read()
        self.assertIn("真源回填", review, "diy-review 缺真源回填条款")
        self.assertIn("stories.yaml", review)
        self.assertIn("status: 已完成", review, "缺故事终态回填")
        self.assertIn("test-plan.yaml", review)
        self.assertIn("status: 通过", review, "缺绿 TC 回填")

    # trace: F-enhancement-2（对抗审查 R6 同款：重复插入 assertIn 查不出）
    def test_review_clause_not_duplicated(self):
        with io.open(SKILL_REVIEW, encoding="utf-8") as f:
            review = f.read()
        self.assertEqual(review.count("真源回填"), 1, "diy-review 真源回填条款重复插入")


if __name__ == "__main__":
    unittest.main()
