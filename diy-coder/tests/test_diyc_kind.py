# -*- coding: utf-8 -*-
"""diyc kind 引擎测试（kind 判据表引擎化，Q-113）。

覆盖：
- 对照表命中：规格 stem（prd / wds-brief 等）／文档 stem（selfcheck / wds-assets 等）／
  技能（SKILL.md 文件、steps / templates 路径成分）
- 文件名：taskbook* → 任务书
- 结构判：目录含 SKILL.md → 技能
- ambiguous：无命中 / 多类冲突（如 taskbook 目录含 SKILL.md）→ kind null + ambiguous
- 匹配口径：stem 精确匹配（spec 不吃 spec-scan）、大小写不敏感、相对路径按 project-root 解析
- CLI 回执形状：kind / matched_by / ambiguous 三键 + 共同键；人类态渲染
夹具全部落 tempdir 自建；不读写本仓库真实 diy-output。
运行：cd diy-coder && python -m unittest discover -s tests -p "test_diyc_kind.py" -v
"""
# trace: Q-113 kind 判据表引擎化（2026-10-21 用户裁定）

import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "skills", "diy-tools", "scripts"))

import diyc_kind  # noqa: E402

DIYC = os.path.join(HERE, "..", "skills", "diy-tools", "scripts", "diyc.py")


def run_diyc(root, *args):
    return subprocess.run(
        [sys.executable, DIYC, *args, "--project-root", str(root)],
        capture_output=True, text=True, encoding="utf-8", timeout=60,
        stdin=subprocess.DEVNULL)


class ClassifyTests(unittest.TestCase):
    """纯函数面：classify 不经 CLI。"""

    def test_spec_stem_hit(self):
        for name in ("prd.yaml", "brief.md", "epics.yml", "story-context.yaml",
                     "wds-trigger.yaml", "wds-design-system.yaml"):
            r = diyc_kind.classify(name)
            self.assertEqual(r["kind"], "规格", name)
            self.assertEqual(r["matched_by"], "对照表", name)
            self.assertFalse(r["ambiguous"], name)

    def test_doc_stem_hit(self):
        for name in ("sprint.yaml", "selfcheck.yaml", "spec-scan.yaml",
                     "editorial-review.yaml", "wds-assets.yaml",
                     "wds-evolution.yaml"):
            r = diyc_kind.classify(name)
            self.assertEqual(r["kind"], "文档", name)
            self.assertFalse(r["ambiguous"], name)

    def test_skill_file_and_path_tokens(self):
        r = diyc_kind.classify("skills/diy-dev/SKILL.md")
        self.assertEqual(r["kind"], "技能")
        self.assertIn("对照表", r["matched_by"])
        r = diyc_kind.classify("skills/diy-dev/steps/01-x.md")
        self.assertEqual(r["kind"], "技能")
        r = diyc_kind.classify("skills/diy-wds-brief/templates/card.html")
        self.assertEqual(r["kind"], "技能")

    def test_taskbook_filename(self):
        r = diyc_kind.classify(".analysis/2026-09-13-migration-p1/taskbook.md")
        self.assertEqual(r["kind"], "任务书")
        self.assertEqual(r["matched_by"], "文件名")
        self.assertFalse(r["ambiguous"])
        r = diyc_kind.classify("taskbook-b7a.md")
        self.assertEqual(r["kind"], "任务书")

    def test_structure_dir_with_skill_md(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill = os.path.join(tmp, "diy-foo")
            os.makedirs(skill)
            with open(os.path.join(skill, "SKILL.md"), "w", encoding="utf-8"):
                pass
            r = diyc_kind.classify(skill)
            self.assertEqual(r["kind"], "技能")
            self.assertEqual(r["matched_by"], "结构判")
            self.assertFalse(r["ambiguous"])

    def test_stem_exact_not_prefix(self):
        # spec 精确匹配；spec-scan 是另一个产物（文档），不得被 spec 吃掉
        self.assertEqual(diyc_kind.classify("spec.yaml")["kind"], "规格")
        self.assertEqual(diyc_kind.classify("spec-scan.yaml")["kind"], "文档")

    def test_case_insensitive_stem(self):
        self.assertEqual(diyc_kind.classify("PRD.YAML")["kind"], "规格")

    def test_no_hit_is_ambiguous(self):
        r = diyc_kind.classify("random-notes.txt")
        self.assertIsNone(r["kind"])
        self.assertEqual(r["matched_by"], "无命中")
        self.assertTrue(r["ambiguous"])

    def test_conflict_is_ambiguous(self):
        # taskbook* 文件名（任务书）+ 目录含 SKILL.md（技能）→ 冲突
        with tempfile.TemporaryDirectory() as tmp:
            d = os.path.join(tmp, "taskbook-c99")
            os.makedirs(d)
            with open(os.path.join(d, "SKILL.md"), "w", encoding="utf-8"):
                pass
            r = diyc_kind.classify(d)
            self.assertIsNone(r["kind"])
            self.assertTrue(r["ambiguous"])
            self.assertIn("冲突:", r["matched_by"])
            self.assertIn("任务书(文件名)", r["matched_by"])
            self.assertIn("技能(结构判)", r["matched_by"])


class CliTests(unittest.TestCase):
    """CLI 面：diyc.py kind --target --json。"""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="diyc-kind-")
        self.addCleanup(lambda: __import__("shutil").rmtree(self.root, True))

    def test_json_receipt_shape(self):
        with open(os.path.join(self.root, "prd.yaml"), "w", encoding="utf-8"):
            pass
        p = run_diyc(self.root, "kind", "--target", "prd.yaml", "--json")
        self.assertEqual(p.returncode, 0, p.stderr)
        r = json.loads(p.stdout)
        self.assertTrue(r["ok"])
        self.assertEqual(r["command"], "kind")
        self.assertEqual(r["kind"], "规格")
        self.assertEqual(r["matched_by"], "对照表")
        self.assertIs(r["ambiguous"], False)
        self.assertEqual(r["target"], "prd.yaml")
        self.assertIn("project_root", r)
        self.assertIn("output_dir", r)
        self.assertEqual(r["violations"], [])

    def test_relative_target_resolved_against_project_root(self):
        os.makedirs(os.path.join(self.root, "skills", "diy-x"))
        with open(os.path.join(self.root, "skills", "diy-x", "SKILL.md"),
                  "w", encoding="utf-8"):
            pass
        p = run_diyc(self.root, "kind", "--target", "skills/diy-x", "--json")
        self.assertEqual(p.returncode, 0, p.stderr)
        r = json.loads(p.stdout)
        self.assertEqual(r["kind"], "技能")
        self.assertEqual(r["matched_by"], "结构判")

    def test_ambiguous_still_exit_zero(self):
        p = run_diyc(self.root, "kind", "--target", "nope.md", "--json")
        self.assertEqual(p.returncode, 0, p.stderr)
        r = json.loads(p.stdout)
        self.assertTrue(r["ok"])
        self.assertIsNone(r["kind"])
        self.assertTrue(r["ambiguous"])

    def test_human_render(self):
        p = run_diyc(self.root, "kind", "--target", "selfcheck.yaml")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("kind: 文档", p.stdout)
        self.assertIn("matched_by: 对照表", p.stdout)

    def test_target_required(self):
        p = run_diyc(self.root, "kind")
        self.assertEqual(p.returncode, 2)


if __name__ == "__main__":
    unittest.main()
