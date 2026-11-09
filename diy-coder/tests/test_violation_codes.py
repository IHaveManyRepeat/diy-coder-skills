# -*- coding: utf-8 -*-
"""违规码机器契约双关卡测试（违规码任务书 §5）。

关卡 (b1)：skills/ 源码三形态字面量（v(" / .add(" / code="）⊆ 集中表。
关卡 (b2)：动态调用点封闭豁免（新增未登记动态点＝红）。
深层对账：per-skill 技能级用码 == owner 登记（不挂 diyc check 运行时门）。
运行时关卡自证：v() 未登记码抛 UnknownViolationCode（忘登记即红的机械证明）。
扫描域只 skills/（tests 域不扩展——负样例故意落在 tests）。
"""
import re
import sys
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
DIY_ROOT = TESTS_DIR.parent          # diy-coder/
REPO_ROOT = DIY_ROOT.parent           # 仓库根（skills 相对定位锚）
SKILLS_ROOT = DIY_ROOT / "skills"
SCRIPTS_TOOLS = SKILLS_ROOT / "diy-tools" / "scripts"

sys.path.insert(0, str(SCRIPTS_TOOLS))
sys.path.insert(0, str(TESTS_DIR))    # noqa: F401 —— 与既有测试同惯例

import violation_codes  # noqa: E402
from violation_codes import (ALL, CORE, PARAM_POSITION_CODES,  # noqa: E402
                             SCAN_EXCLUDE, SKILL_CODES, UnknownViolationCode)

# ---- 扫描正则（三形态·与 census/gen 同口径；v 首参必码·跨行安全·含 design 域小写连字符）----
# .add 限定违规报告对象（report/violations/vio）——裸 .add 会误抓 set.add("open") 等
PAT_V = re.compile(r'v\(\s*"([^"]+)"')
PAT_ADD = re.compile(r'(?:report\.add|violations\.add|vio\.add)\(\s*["\']([^"\']+)["\']')
PAT_KW = re.compile(r'code\s*=\s*["\']([^"\']+)["\']')
# 数据表元组首形态：("CODE", "说明"...)——规则表住码、经动态点流入 v()
PAT_TUPLE = re.compile(r'\(\s*"([A-Z][A-Z0-9_]+)",\s*"')
# 动态点：v( 后非引号且首参为标识/容器形态；排除 def 定义行
PAT_DYN = re.compile(r'\bv\(\s*(?![\"\'])([A-Za-z_{\[])')
PAT_DEF = re.compile(r'^\s*def\s+v\s*\(')

REL_PREFIX = "diy-coder/skills/"

# 动态点封闭豁免（file → 该行动态调用 stripped 全文；census §4 18 点·SS-042-05）。
# 新增动态点不在表内＝红（忘登记即红在动态面的体现）。
EXEMPT_DYN = {
    "diy-coder/skills/diy-design/scripts/design_a11y.py": {
        'out.append(v(states_code, "%s pages[%s].states" % (rel, page.get("id")),',
        'out.append(v(file_code, "%s pages[%s].prototype" % (rel, page.get("id")),',
    },
    "diy-coder/skills/diy-editorial-review/scripts/editorial_review.py": {
        'violations.append(v(err["code"], show, err["msg"]))',
    },
    "diy-coder/skills/diy-teach-me-testing/scripts/progress_init.py": {
        'payload["violations"] = [v(damage[0], show, damage[1] + RECOVERY_HINT)]',
    },
    "diy-coder/skills/diy-teach-me-testing/scripts/progress_update.py": {
        'payload["violations"] = [v(damage[0], show, damage[1] + RECOVERY_HINT)]',
    },
    "diy-coder/skills/diy-test-author/scripts/author_rules.py": {
        'violations.append(v(code, where, "%s（第 %d 行）" % (msg, no)))',
    },
    "diy-coder/skills/diy-tools/scripts/diyc_check_docs_lib.py": {
        'self.violations.append(diyc_lib.v(code, where, msg))',
    },
    "diy-coder/skills/diy-tools/scripts/diyc_lib_report.py": {
        'return None, [v(code, show, "YAML %s：%s"',
    },
    "diy-coder/skills/diy-tools/scripts/diyc_writeback_reconcile.py": {
        'vio.append(lib.v(code, rel, f"{rel} {label}：{err}"))',
    },
    "diy-coder/skills/diy-tools/scripts/diyc_writeback_state.py": {
        'return _fail(args, lib.v(code, rel_tp, f"{rel_tp} {label}：{err}"))',
        'return _fail(args, lib.v(code, rel_stories, f"{rel_stories} {label}：{err}"))',
    },
    "diy-coder/skills/diy-wds-evolution/scripts/wds_evolution.py": {
        'violations.append(v(code or "UNPARSABLE_YAML", where,',
    },
    "diy-coder/skills/diy-wds-evolution/scripts/wds_evolution_checks.py": {
        'violations.append(v(code or "UNPARSABLE_YAML", where,',
    },
    "diy-coder/skills/diy-wds-system/scripts/wds_system.py": {
        'return {"violations": [v(code or "UNPARSABLE_YAML", where,',
    },
    "diy-coder/skills/diy-wds-system/scripts/wds_system_checks.py": {
        'return None, [v(code or "UNPARSABLE_YAML", where,',
        'return None, [v(code or "UNPARSABLE_YAML", where,',  # :104 与 :127 同文——集合去重见下
    },
}


def _rel(path: Path) -> str:
    s = str(path).replace("\\", "/")
    idx = s.index(REL_PREFIX)
    return s[idx:]


def _iter_py():
    for f in sorted(SKILLS_ROOT.rglob("*.py")):
        yield f, _rel(f), f.read_text(encoding="utf-8", errors="replace")


class TestLiteralScan(unittest.TestCase):
    """关卡 (b1)：三形态字面量 ⊆ 码表。"""

    def test_literal_codes_subset_of_table(self):
        bad = []
        for f, rel, text in _iter_py():
            for pat in (PAT_V, PAT_ADD, PAT_KW, PAT_TUPLE):
                for m in pat.finditer(text):
                    code = m.group(1)
                    if code in SCAN_EXCLUDE:
                        continue
                    if code not in ALL:
                        line = text[: m.start()].count("\n") + 1
                        bad.append(f"{rel}:{line} {code}")
        self.assertEqual(bad, [], "字面量码未登记（忘登记即红）：\n" + "\n".join(bad))

    def test_table_not_silently_shrunk(self):
        # 反向兜底：核心 22 全在表、技能级键自洽
        self.assertEqual(len(CORE), 22, "核心冻结区必须恰为 22 码")
        for code, (kind, owners) in SKILL_CODES.items():
            self.assertIn(kind, ("violation", "warning", "both"), code)
            self.assertTrue(owners, f"{code} 必须有 owner")
            self.assertNotIn(code, CORE, f"{code} 不得同时属两区")


class TestDynamicExempt(unittest.TestCase):
    """关卡 (b2)：动态点封闭豁免——新动态点未登记＝红。"""

    def test_dynamic_points_closed_world(self):
        found = {}
        for f, rel, text in _iter_py():
            for i, line in enumerate(text.splitlines(), 1):
                if PAT_DEF.match(line):
                    continue
                if PAT_DYN.search(line):
                    found.setdefault(rel, set()).add(line.strip())
        violations = []
        for rel, lines in found.items():
            exempt = EXEMPT_DYN.get(rel, set())
            for ln in lines:
                if ln not in exempt:
                    violations.append(f"{rel}: {ln[:110]}")
        self.assertEqual(
            violations, [],
            "未登记的动态调用点（登记进 EXEMPT_DYN 或改字面量）：\n" + "\n".join(violations))

    def test_exempt_entries_still_present(self):
        # 豁免名单里的点必须还在场（防止代码删了名单烂掉）
        stale = []
        for rel, lines in EXEMPT_DYN.items():
            f = REPO_ROOT / rel
            if not f.exists():
                stale.append(f"{rel} 文件不存在")
                continue
            text = f.read_text(encoding="utf-8", errors="replace")
            present = {ln.strip() for ln in text.splitlines()}
            for ln in lines:
                if ln not in present:
                    stale.append(f"{rel}: 豁免行已漂/删 → {ln[:90]}")
        self.assertEqual(stale, [], "豁免清单陈旧：\n" + "\n".join(stale))


class TestOwnerRoundtrip(unittest.TestCase):
    """深层对账：per-skill 技能级用码 == owner 登记（超集覆盖浅层）。"""

    def test_used_equals_owned(self):
        used = {}
        for f, rel, text in _iter_py():
            skill = rel.split("/")[2]   # diy-coder/skills/<skill>/...
            for pat in (PAT_V, PAT_ADD, PAT_KW, PAT_TUPLE):
                for m in pat.finditer(text):
                    code = m.group(1)
                    if code in CORE or code in SCAN_EXCLUDE:
                        continue
                    used.setdefault(skill, set()).add(code)
        owned = {}
        for code, (_kind, owners) in SKILL_CODES.items():
            for sk in owners:
                owned.setdefault(sk, set()).add(code)
        # 参数位码扫描不可达：owned 比 used 多出的必须全在豁免集合；used 不得有 owned 没有的
        for sk in used:
            extra_used = used[sk] - owned.get(sk, set())
            self.assertEqual(extra_used, set(),
                             f"{sk} 用码未进 owner 登记（跑 gen_violation_codes.py）：{extra_used}")
        for sk in owned:
            extra_owned = owned[sk] - used.get(sk, set())
            self.assertTrue(
                extra_owned <= PARAM_POSITION_CODES,
                f"{sk} owner 多出的码非参数位码豁免：{extra_owned - PARAM_POSITION_CODES}")


class TestRuntimeGate(unittest.TestCase):
    """运行时关卡：忘登记即红的机械证明。"""

    def test_registered_ok(self):
        from diyc_lib_base import v
        d = v("EMPTY_FIELD", "a/b", "x")
        self.assertEqual(d["code"], "EMPTY_FIELD")
        self.assertEqual(d["where"], "a/b")

    def test_private_code_raises(self):
        from diyc_lib_base import v
        with self.assertRaises(UnknownViolationCode):
            v("NOT_REGISTERED", "a", "x")

    def test_negative_sample_not_in_scan_domain(self):
        # 负样例本体在 tests/ 域——扫描面只 skills/，二者不打架
        self.assertTrue((TESTS_DIR / "test_violation_codes.py").exists())


if __name__ == "__main__":
    unittest.main()
