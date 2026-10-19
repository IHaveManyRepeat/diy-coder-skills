# -*- coding: utf-8 -*-
"""跨技能 import 红线守卫（v4·精简插队·己批·2026-10-19 裁甲）。

A 防再犯：AST 扫 diy-coder/skills/*/scripts/*.py 全部 import/from-import——
顶层模块命中「他技能 stem 归属表」即违规；豁免＝diyc* 共享底座前缀＋本技能内互 import。
B 在场守卫：理念文档第⑤条红线句两半句＋CLAUDE.md 复用纪律节在场（防立法句被删）。
"""
import ast
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILLS_ROOT = os.path.join(HERE, "..", "skills")
CODE_QUALITY = os.path.join(HERE, "..", "docs", "code-quality.md")
CLAUDE_MD = os.path.join(HERE, "..", "..", "CLAUDE.md")


def _skill_dirs():
    for name in sorted(os.listdir(SKILLS_ROOT)):
        scripts = os.path.join(SKILLS_ROOT, name, "scripts")
        if os.path.isdir(scripts):
            yield name, scripts


def _stem_owners():
    """stem -> set(skill names)；同名异技能 = 多 owner。"""
    owners = {}
    for skill, scripts in _skill_dirs():
        for fn in os.listdir(scripts):
            if fn.endswith(".py"):
                owners.setdefault(fn[:-3], set()).add(skill)
    return owners


def _imports_of(path):
    """文件内全部顶层 import 的模块顶名（相对导入 level>0 不计）。"""
    with open(path, "r", encoding="utf-8") as f:
        source = f.read()
    tree = ast.parse(source, filename=path)
    tops = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                tops.append(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            tops.append(node.module.split(".")[0])
    return tops


class CrossSkillImportGuardTests(unittest.TestCase):
    def test_no_cross_skill_imports(self):
        owners = _stem_owners()
        violations = []
        for skill, scripts in _skill_dirs():
            for fn in sorted(os.listdir(scripts)):
                if not fn.endswith(".py"):
                    continue
                path = os.path.join(scripts, fn)
                rel = os.path.relpath(path, SKILLS_ROOT).replace("\\", "/")
                for top in _imports_of(path):
                    if top.startswith("diyc"):
                        continue  # diy-tools 共享底座（diyc_lib 家族）
                    owner = owners.get(top)
                    if owner is not None and owner != {skill}:
                        violations.append(
                            "%s: import %s（归属 %s）"
                            % (rel, top, "/".join(sorted(owner))))
        self.assertEqual(
            violations, [],
            "跨技能 import 违规（公共函数唯一去处＝diyc_lib，见 docs/code-quality.md 第⑤条）：\n"
            + "\n".join(violations))

    def test_red_line_sentences_present(self):
        with open(CODE_QUALITY, "r", encoding="utf-8") as f:
            docs = f.read()
        self.assertIn("公共函数唯一去处", docs,
                      "code-quality.md 第⑤条红线句（公共函数唯一去处）被删")
        self.assertIn("技能间不互相 import 对方脚本", docs,
                      "code-quality.md 第⑤条红线句（技能间不互相 import）被删")
        with open(CLAUDE_MD, "r", encoding="utf-8") as f:
            md = f.read()
        self.assertIn("复用纪律", md,
                      "项目 CLAUDE.md 复用纪律节被删")


if __name__ == "__main__":
    unittest.main()
