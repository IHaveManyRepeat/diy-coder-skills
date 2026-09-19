# -*- coding: utf-8 -*-
"""B3 五技能 steps 形态一致性（`skill-template-zh.md` §三标准）。

形态标准（2026-09-19 统一裁定，B3 窗口移交单 M-2）：
  - H1 = `# Step N — <中文步名>`（`Step` 保留作结构标记，步名须含中文，步号与文件序一致）
  - `**Read (input):**` / `**Write (output):**` 两行**逐字英文**（母本 §4 锚定）

末段段名各技能自定（`## 播报与下一步` / `## 摘要` 等），不在本测试强制。

trace: B3 窗口移交单 M-2（steps H1 步名统一 12 处）+ 范本 §三形态标准的测试锁。
"""
import io
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILLS = ["diy-test-author", "diy-test-gate", "diy-test-framework",
          "diy-test-review", "diy-teach-me-testing"]

H1_RE = re.compile(r"^# Step (\d+) — .*[一-鿿]")


class StepsShapeTests(unittest.TestCase):

    def steps_of(self, skill):
        d = os.path.join(HERE, "..", "skills", skill, "steps")
        names = sorted(n for n in os.listdir(d) if n.endswith(".md"))
        self.assertTrue(names, "%s 无 steps 文件" % skill)
        return d, names

    def test_h1_is_chinese_numbered_step(self):
        for skill in SKILLS:
            d, names = self.steps_of(skill)
            for i, name in enumerate(names, start=1):
                with io.open(os.path.join(d, name), encoding="utf-8") as fh:
                    first = fh.readline().rstrip("\r\n")
                m = H1_RE.match(first)
                self.assertTrue(m, "%s/%s 的 H1 须为 '# Step N — <中文步名>'，实为 %r"
                                % (skill, name, first))
                self.assertEqual(int(m.group(1)), i,
                                 "%s/%s 的步号与文件序不符（应 %d）" % (skill, name, i))

    def test_read_write_lines_verbatim(self):
        for skill in SKILLS:
            d, names = self.steps_of(skill)
            for name in names:
                with io.open(os.path.join(d, name), encoding="utf-8") as fh:
                    lines = fh.read().replace("\r\n", "\n").split("\n")
                self.assertTrue(any(ln.startswith("**Read (input):**") for ln in lines),
                                "%s/%s 缺 '**Read (input):**' 行（冒号须半角）" % (skill, name))
                self.assertTrue(any(ln.startswith("**Write (output):**") for ln in lines),
                                "%s/%s 缺 '**Write (output):**' 行（冒号须半角）" % (skill, name))


if __name__ == "__main__":
    unittest.main()
