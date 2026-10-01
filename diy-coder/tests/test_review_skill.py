# -*- coding: utf-8 -*-
"""diy-review 技能文档契约（C·12 · W3，裁定 C12-3）。

review 拆 `steps/` 七件后的机械面：
  - 主文件点名的 steps 集合 == 磁盘实况（抄 `test_design_skill.py` 先例）
  - 主文件 §4 读取纪律锚串在场（与 `test_suite_texts.py` 的 `_steppers()` 同步）
  - 行数线 = 拆后实测 ×1.2 取 ceil（裁定 3 同口径）
  - 每件 step 文件声明 `Read (input)` / `Write (output)` 行（先例同款）

锚串下沉内容的断言归 `test_review_contract.py`（读源已改指对应 steps 文件，
逐条申报见 `.analysis/2026-09-28-c12/w3-report.md`），本文件不重复。
"""
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILLS = os.path.join(HERE, "..", "skills")
SKILL_MD = os.path.join(SKILLS, "diy-review", "SKILL.md")
STEPS_DIR = os.path.join(SKILLS, "diy-review", "steps")

# 拆后实测 ×1.2 取 ceil（2026-10-01 实测 79 行 → 95；裁定 3）
LINE_BUDGET = 95

# 值同 `test_suite_texts.py` 的 `ANCHOR_READ_DISCIPLINE`（母本 §4）
READ_DISCIPLINE = ("读取纪律：预载预算 = 本文件、上述配置与回执、`steps/` 下当前那一个文件"
                   "——绝不批量预载；执行期读取以每个步骤开头的 `Read (input)` 行为唯一权威，"
                   "**主文件不列举封闭清单**。")

# 七件拆分表（任务书 §2.3）：文件名 → 下沉内容的标志性锚串（每件至少一枚）
STEP_ANCHORS = {
    "l1-correctness.md": 'diyc.py" trace --src <本任务实现文件/目录> --json',
    "l2-boundary.md": "只报真会咬人的未处理情形",
    "l3-coverage.md": "`EVIDENCE_MISSING`",
    "l4-design-adoption.md": "ds-token-color",
    "lenses.md": "**零 findings 即 HALT**",
    "wds-review.md": "**绝不代用户批准**",
    "falsify.md": 'pop("augment")',
}


class ReviewSkillStepsTests(unittest.TestCase):

    def setUp(self):
        with open(SKILL_MD, encoding="utf-8") as fh:
            self.raw = fh.read()

    # trace: C·12 §2.3（主文件点名 7 件 == 磁盘 7 件；抄 test_design_skill.py 先例）
    def test_routed_step_files_exist(self):
        routed = set(re.findall(r"steps/([a-z0-9-]+\.md)", self.raw))
        self.assertEqual(len(routed), 7, "主文件点名的 steps 文件数变了：%s" % sorted(routed))
        on_disk = set(n for n in os.listdir(STEPS_DIR) if n.endswith(".md"))
        self.assertEqual(routed, on_disk,
                         "主文件路由与 steps/ 实况不符——缺文件 %s；未路由 %s"
                         % (sorted(routed - on_disk), sorted(on_disk - routed)))

    # trace: C·12 §2.3（每件 step 承载其下沉内容的标志锚——文件在而内容空 = 空壳）
    def test_step_files_carry_their_content(self):
        for name, anchor in sorted(STEP_ANCHORS.items()):
            with open(os.path.join(STEPS_DIR, name), encoding="utf-8") as fh:
                body = fh.read()
            self.assertIn(anchor, body, "%s 缺下沉内容锚串 %r" % (name, anchor))

    # trace: 母本 §4 锚串承诺的步骤形态——每个步骤文件都须有 Read/Write 行（先例同款）
    def test_every_step_file_declares_read_write(self):
        names = sorted(n for n in os.listdir(STEPS_DIR) if n.endswith(".md"))
        self.assertTrue(names, "steps/ 为空")
        for name in names:
            with open(os.path.join(STEPS_DIR, name), encoding="utf-8") as fh:
                body = fh.read()
            self.assertIn("**Read (input):**", body, "%s 缺 `Read (input)` 行" % name)
            self.assertIn("**Write (output):**", body, "%s 缺 `Write (output)` 行" % name)

    # trace: C·12 裁定 C12-3（长出 steps/ → 必补母本 §4 读取纪律锚串）
    def test_read_discipline_anchor_landed(self):
        self.assertIn(READ_DISCIPLINE, self.raw, "缺母本 §4 读取纪律锚串（steps/ 已落地）")

    # trace: C·12 裁定 3（行数线 = 拆后实测 ×1.2 取 ceil，与 test_review_contract 同值）
    def test_line_budget(self):
        self.assertLessEqual(len(self.raw.splitlines()), LINE_BUDGET,
                             "主文件超出 diy-review 控制线 %d 行" % LINE_BUDGET)

    # trace: C·12 §2.3（工作流骨架保留面——四层指路 + 透镜指路 + WDS 指路在主文件）
    def test_workflow_skeleton_routes_layers(self):
        for token in ("L1", "L2", "L3", "L4", "design_ref",
                      "`steps/lenses.md`", "`steps/wds-review.md`", "`steps/falsify.md`"):
            self.assertIn(token, self.raw, "工作流骨架缺路由锚：%s" % token)


if __name__ == "__main__":
    unittest.main()
