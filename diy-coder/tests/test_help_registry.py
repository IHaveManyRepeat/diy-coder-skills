# -*- coding: utf-8 -*-
"""diy-help 登记表守卫（C·1 登记表驱动）。

表 = `skills/diy-help/registry.yaml`（链序 + 提示文案 + 线级入口/执行技能）
实物 = 各技能 `SKILL.md` 的 frontmatter 六字段（phase / precededBy / followedBy / required / line / outputs）

**双向严格**（用户 2026-09-21 拍板）：
  · 表 → 实物：链上每个技能目录在场、frontmatter 齐、`line` 与本线一致、`outputs` 可机械解析
  · 实物 → 表：每个 `skills/diy-*/` 都有六字段（新技能落地时由该批收口链补齐）

**这不是故障，是设计**：新技能未登记即本文件红——与 `tests/test_suite_texts.py` 的
`NEW_SKILLS` 同范式（B5/B6 批备注即写着「登记前 2 红」）。
"""
import importlib.util
import io
import os
import re
import unittest

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
SKILLS_DIR = os.path.join(HERE, "..", "skills")
HELP_PY = os.path.join(SKILLS_DIR, "diy-help", "scripts", "help.py")
SIX_FIELDS = ("phase", "precededBy", "followedBy", "required", "line", "outputs")
# 链节点的 outputs 须为 `+` 分隔的裸文件名（与 help.py 的 _OUTPUT_TOKEN_RE 同式）
OUTPUT_TOKEN_RE = re.compile(r"^[A-Za-z0-9_.\-]+$")


def load_engine():
    spec = importlib.util.spec_from_file_location("diy_help_engine", HELP_PY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def skill_names():
    return sorted(d for d in os.listdir(SKILLS_DIR)
                  if d.startswith("diy-") and os.path.isdir(os.path.join(SKILLS_DIR, d)))


def frontmatter(skill):
    """读某技能的 frontmatter 映射；无 frontmatter 或缺文件返回 None。"""
    path = os.path.join(SKILLS_DIR, skill, "SKILL.md")
    if not os.path.isfile(path):
        return None
    raw = io.open(path, encoding="utf-8").read()
    m = re.match(r"^---[ \t]*\r?\n(.*?)\r?\n---[ \t]*\r?\n", raw, re.S)
    if not m:
        return None
    return yaml.safe_load(m.group(1)) or {}


def registry():
    try:
        return load_engine().load_registry()
    except SystemExit:  # 引擎对非法登记表硬失败（C·1 裁定 3）
        raise AssertionError(
            "引擎读取登记表失败（registry.yaml 形状非法或缺失）——见 stderr 的 FATAL 行")


class RegistryShapeTests(unittest.TestCase):
    """表自身的形状（引擎与守卫同读一份）。"""

    def test_engine_can_load_registry(self):
        reg = registry()
        self.assertIn("mainline", reg["lines"])

    def test_line_entry_and_exec(self):
        for name, line in registry()["lines"].items():
            with self.subTest(line=name):
                self.assertEqual(line["entry"], line["chain"][0],
                                 "%s 的 entry 必须是 chain 第一个" % name)
                if line["exec"] is None:
                    self.assertTrue(str(line.get("exec_note", "")).strip(),
                                    "%s 的 exec 为 null 时必须给 exec_note" % name)
                else:
                    self.assertIn(line["exec"], skill_names(),
                                  "%s 的 exec (%s) 不是已装技能" % (name, line["exec"]))

    def test_chain_skills_installed(self):
        for name, line in registry()["lines"].items():
            for skill in line["chain"]:
                with self.subTest(line=name, skill=skill):
                    self.assertTrue(
                        os.path.isfile(os.path.join(SKILLS_DIR, skill, "SKILL.md")),
                        "%s.chain 指向 %s，但该技能目录不在" % (name, skill))


class TableToRealityTests(unittest.TestCase):
    """表 → 实物：链上节点的自声明必须与本线一致。"""

    def test_chain_node_line_matches(self):
        for name, line in registry()["lines"].items():
            for skill in line["chain"]:
                with self.subTest(skill=skill):
                    fm = frontmatter(skill)
                    self.assertIsNotNone(fm, "%s 无 frontmatter" % skill)
                    self.assertEqual(fm.get("line"), name,
                                     "%s 的 frontmatter line 应为 %s（登记表把它挂在 %s 线上）"
                                     % (skill, name, name))

    def test_chain_outputs_machine_parseable(self):
        for name, line in registry()["lines"].items():
            for skill in line["chain"]:
                with self.subTest(skill=skill):
                    out = str(frontmatter(skill).get("outputs") or "")
                    toks = [t.strip() for t in out.split("+") if t.strip()]
                    self.assertTrue(toks, "%s 是链节点但 outputs 为空" % skill)
                    for t in toks:
                        self.assertRegex(t, OUTPUT_TOKEN_RE,
                                         "%s 的 outputs 含非文件名片段 %r（链节点须为裸文件名）"
                                         % (skill, t))

    def test_chain_node_required_is_bool(self):
        for name, line in registry()["lines"].items():
            for skill in line["chain"]:
                with self.subTest(skill=skill):
                    self.assertIsInstance(frontmatter(skill).get("required"), bool,
                                          "%s 的 required 须为布尔（六字段封闭集）" % skill)

    def test_notes_cover_exactly_the_optional_nodes(self):
        """可选节点（required: false）必须有缺席提示；必做节点不得有提示。"""
        for name, line in registry()["lines"].items():
            with self.subTest(line=name):
                optional = {s for s in line["chain"]
                            if frontmatter(s).get("required") is False}
                self.assertEqual(set(line.get("notes") or {}), optional,
                                 "%s 的 notes 键应恰为可选节点集合" % name)

    def test_notes_keys_are_chain_members(self):
        for name, line in registry()["lines"].items():
            extra = set(line.get("notes") or {}) - set(line["chain"])
            with self.subTest(line=name):
                self.assertFalse(extra, "%s 的 notes 含非链上技能：%s" % (name, sorted(extra)))

    def test_status_paths_keys_are_chain_members(self):
        for name, line in registry()["lines"].items():
            extra = set(line.get("status_paths") or {}) - set(line["chain"])
            with self.subTest(line=name):
                self.assertFalse(extra, "%s 的 status_paths 含非链上技能：%s" % (name, sorted(extra)))


class RealityToTableTests(unittest.TestCase):
    """实物 → 表：全库技能都已登记（漏登即红——新技能收口链须补）。"""

    def test_every_skill_declares_six_fields(self):
        missing = []
        for skill in skill_names():
            fm = frontmatter(skill)
            if fm is None:
                missing.append("%s（无 SKILL.md 或无可解析 frontmatter）" % skill)
                continue
            absent = [f for f in SIX_FIELDS if f not in fm]
            if absent:
                missing.append("%s（缺 %s）" % (skill, "、".join(absent)))
        self.assertFalse(missing,
                         "以下技能未登记六字段，请在收口链补齐后重跑：\n  " + "\n  ".join(missing))

    def test_dependency_targets_are_installed(self):
        """依赖边零悬空（对齐 diy-bmb-module 的 UNKNOWN_ID 口径）。"""
        installed = set(skill_names())
        dangling = []
        for skill in skill_names():
            fm = frontmatter(skill) or {}
            for field in ("precededBy", "followedBy"):
                for target in fm.get(field) or []:
                    if target not in installed:
                        dangling.append("%s.%s → %s" % (skill, field, target))
        self.assertFalse(dangling,
                         "frontmatter 依赖边指向未安装技能：\n  " + "\n  ".join(dangling))


if __name__ == "__main__":
    unittest.main()
