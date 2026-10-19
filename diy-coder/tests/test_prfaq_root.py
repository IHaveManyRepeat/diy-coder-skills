# -*- coding: utf-8 -*-
"""diy-prfaq check：--output-dir 相对路径按 project-root 归一（夜队列 Q-002）。

覆盖：
- 相对 --output-dir + 子进程 cwd 与 project-root 不同 → 校验的是 project-root 侧文件
- cwd 侧同名非法诱饵不被读取（证明路径不再按进程 cwd 解析）
- 绝对 --output-dir 防回归

夹具全部落 tempdir 自建；不读写本仓库真实 diy-output。
运行：cd diy-coder && python -m pytest tests/test_prfaq_root.py -q
"""
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.abspath(
    os.path.join(HERE, "..", "skills", "diy-prfaq", "scripts", "prfaq.py"))
NL = chr(10)

# 合法草稿（精简自 tests/test_prfaq.py 的 PRFAQ_DRAFT：stage 2，FAQ 为空合法）
PRFAQ_DRAFT = NL.join([
    "project:",
    "  name: mini",
    "  status: 草稿",
    "  created: '2026-09-14'",
    "  updated: '2026-09-14'",
    "prfaq:",
    "  stage: 2",
    "  concept_type: 商业",
    "  essentials:",
    "    customer: 独立开发者",
    "    problem: 手工整理需求耗时",
    "    stakes: 交付延期",
    "    solution: 自动生成 PRFAQ 草稿",
    "  press_release:",
    "    headline: 需求整理从三小时到三分钟",
    "    subheadline: 独立开发者当天拿到成型概念",
    "  customer_faq: []",
    "  internal_faq: []",
    "  verdict: {}",
    "distillate:",
    "  problem: 需求整理耗时",
    "  target_users:",
    "  - 独立开发者",
    "  value_props: []",
    "  constraints: []",
    "  open_questions: []",
    "notes: []",
    "revisions: []",
]) + NL

# cwd 侧诱饵：空映射，凡被读取必报违规
DECOY = "{}" + NL


class RootRelativeOutputDirTests(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="prfaq-root-")
        # A = project_root；B = 子进程 cwd，两者不同
        self.root = os.path.join(self.tmp.name, "A")
        self.cwd = os.path.join(self.tmp.name, "B")
        self.out = os.path.join(self.root, "out")
        os.makedirs(self.out, exist_ok=True)
        os.makedirs(self.cwd, exist_ok=True)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, path, content):
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with io.open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def run_check(self, output_dir):
        # 引擎走绝对路径；子进程 cwd=B（与 project-root 不同）
        return subprocess.run(
            [sys.executable, ENGINE, "check", "--project-root", self.root,
             "--output-dir", output_dir, "--json"],
            capture_output=True, text=True, encoding="utf-8", cwd=self.cwd)

    # trace: 夜队列 Q-002（相对 --output-dir 按 project-root 归一，不按进程 cwd）
    def test_relative_output_dir_resolves_against_project_root(self):
        self.write(os.path.join(self.out, "prfaq.yaml"), PRFAQ_DRAFT)
        r = self.run_check("out")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertTrue(data["ok"], r.stdout)
        self.assertNotIn("MISSING_FILE", {x["code"] for x in data["violations"]})

    # trace: 夜队列 Q-002（cwd 侧同名非法诱饵不被读取 → 校验的是 A 侧文件）
    def test_relative_output_dir_ignores_decoy_in_cwd(self):
        self.write(os.path.join(self.out, "prfaq.yaml"), PRFAQ_DRAFT)
        self.write(os.path.join(self.cwd, "out", "prfaq.yaml"), DECOY)
        r = self.run_check("out")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertTrue(data["ok"], r.stdout)
        self.assertEqual(data["violations"], [], r.stdout)

    # trace: 夜队列 Q-002（绝对 --output-dir 行为不变，防回归）
    def test_absolute_output_dir_still_works(self):
        self.write(os.path.join(self.out, "prfaq.yaml"), PRFAQ_DRAFT)
        r = self.run_check(self.out)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertTrue(data["ok"], r.stdout)
        self.assertEqual(data["violations"], [], r.stdout)


if __name__ == "__main__":
    unittest.main()
