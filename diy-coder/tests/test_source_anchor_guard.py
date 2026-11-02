# -*- coding: utf-8 -*-
"""源锚/拍板引语/批次名词增量防线（2026-10-25 用户裁·常态化；2026-11-02 扩面含 tests）。

扫描 `diy-coder/skills/**` 与 `diy-coder/tests/**` 随包文本（.py/.md/.yaml/.csv），
命中扩展标记词即红；豁免键＝文件相对路径＋命中原文
（对齐 taskbook-batch6 §8「豁免键＝文件＋anchor_text」）。

口径备注：
- 作用域＝安装面 skills/** ＋ tests/**（tests 面历史注释已清零；存量真断言/夹具数据
  按同机制登记于本文件 TESTS_EXEMPT——断言本体不动）。
- 词表与安装面 EXEMPT 单源 diyc_body_rules（bmb-builder 正文门同引）；tests 面豁免
  键登记在本文件（scope 内单写面；锚串以字面拆分拼装，避免本文件正文自命中）。
- FR-4.5/D-9 族按门②裁定归批 8（显式表在册），本词表不含该类；批 8 落地后可扩。
- 「裁定」不带数字＝产品用词（「用户裁定/请人裁定」），只拦「裁定+数字」拍板引语式。
- SS-0nn＝diy-spec-scan 产品 ID 形态（非批次名词），不入词表。
"""
import io
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS = os.path.join(ROOT, "skills")
TESTS = os.path.join(ROOT, "tests")
EXTS = (".py", ".md", ".yaml", ".csv")

# 词表单源（2026-10-31 裁）：PATTERNS/EXEMPT 下沉 diyc_body_rules（diy-tools 共享
# 底座），与 bmb-builder check_body_rules.py 同引；本测试只留扫描逻辑。
sys.path.insert(0, os.path.join(SKILLS, "diy-tools", "scripts"))
from diyc_body_rules import EXEMPT, PATTERNS  # noqa: E402

# tests 面豁免（Q-135 登记）：真断言消息/期望串与夹具数据——断言本体不动，按
# 与安装面 EXEMPT 同机制豁免。键＝tests/ 相对路径＋命中原文；锚串拆字面拼装。
TESTS_EXEMPT = {
    # dirty 夹具内嵌的批次头样例（test_dirty_sample_is_red 构造红样例）
    ("tests/test_bmb_builder.py", "# trace: " + "B3"),
    # 断言失败消息中的取数侧措辞（assertLess / assertIn 文案）
    ("tests/test_cis_method.py", "源" + "侧"),
    ("tests/test_diy_architecture.py", "源" + "侧"),
    # 断言消息里的拍板引语原文（钉住术语/边界措辞，改即触断言）
    ("tests/test_design_skill.py", "裁定" + " 1"),
    ("tests/test_diy_dev_wds.py", "裁定" + " 1"),
    ("tests/test_diy_dev_wds.py", "裁定" + " 2"),
    ("tests/test_diy_dev_wds.py", "裁定" + " 4"),
    ("tests/test_diy_dev_wds.py", "裁定" + " 6"),
    ("tests/test_diy_dev_wds.py", "C·" + "7"),
    ("tests/test_runner.py", "裁定" + " 2"),
    ("tests/test_wds_trigger.py", "裁定" + " 1"),
    # 夹具数据串（归档路径按字面喂被测函数/渲染器，删即断测试意图）
    ("tests/test_diyc_kind.py", ".analysis" + "/"),
    ("tests/test_selfcheck_engine.py", ".analysis" + "/"),
    ("tests/test_viewer_labels.py", ".analysis" + "/"),
}


def _iter_files():
    for base in (SKILLS, TESTS):
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if not d.startswith(".")]
            for name in filenames:
                if name.endswith(EXTS):
                    yield os.path.join(dirpath, name)


def _rel(path):
    """豁免键命名空间：安装面沿用 skills/ 相对路径；tests 面带 tests/ 前缀。"""
    if path.startswith(SKILLS + os.sep):
        return os.path.relpath(path, SKILLS).replace(os.sep, "/")
    return "tests/" + os.path.relpath(path, TESTS).replace(os.sep, "/")


class SourceAnchorGuardTests(unittest.TestCase):
    def test_no_new_source_anchors_in_scope(self):
        hits = []
        for path in _iter_files():
            rel = _rel(path)
            try:
                text = io.open(path, encoding="utf-8").read()
            except (UnicodeDecodeError, OSError):
                continue
            for label, pattern in PATTERNS:
                for match in pattern.finditer(text):
                    anchor = match.group(0)
                    if (rel, anchor) in EXEMPT or (rel, anchor) in TESTS_EXEMPT:
                        continue
                    hits.append("%s [%s] %r" % (rel, label, anchor))
        self.assertEqual(
            hits, [],
            "skills/ 或 tests/ 出现源锚/拍板引语/批次名词"
            "（增量即红；豁免须走 EXEMPT / TESTS_EXEMPT 登记）：\n"
            + "\n".join(hits))


if __name__ == "__main__":
    unittest.main()
