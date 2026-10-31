# -*- coding: utf-8 -*-
"""批6 追加判据 guard：源锚/拍板引语/批次名词增量防线（2026-10-25 用户裁·常态化）。

扫描 `diy-coder/skills/**` 随包文本（.py/.md/.yaml/.csv），命中扩展标记词即红；
豁免键＝文件相对路径＋命中原文（对齐 taskbook-batch6 §8「豁免键＝文件＋anchor_text」）。

口径备注（随批 6 呈审）：
- 作用域＝安装面（skills/**）。tests/ 面存量历史注记（175 处·测试作者痕迹）不在批 6
  清理面，本 guard 不护；若要清另立批。
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
EXTS = (".py", ".md", ".yaml", ".csv")

# 词表单源（2026-10-31 裁）：PATTERNS/EXEMPT 下沉 diyc_body_rules（diy-tools 共享
# 底座），与 bmb-builder check_body_rules.py 同引；本测试只留扫描逻辑。
sys.path.insert(0, os.path.join(SKILLS, "diy-tools", "scripts"))
from diyc_body_rules import EXEMPT, PATTERNS  # noqa: E402


def _iter_files():
    for dirpath, dirnames, filenames in os.walk(SKILLS):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for name in filenames:
            if name.endswith(EXTS):
                yield os.path.join(dirpath, name)


class SourceAnchorGuardTests(unittest.TestCase):
    def test_no_new_source_anchors_in_skills(self):
        hits = []
        for path in _iter_files():
            rel = os.path.relpath(path, SKILLS).replace(os.sep, "/")
            try:
                text = io.open(path, encoding="utf-8").read()
            except (UnicodeDecodeError, OSError):
                continue
            for label, pattern in PATTERNS:
                for match in pattern.finditer(text):
                    anchor = match.group(0)
                    if (rel, anchor) in EXEMPT:
                        continue
                    hits.append("%s [%s] %r" % (rel, label, anchor))
        self.assertEqual(
            hits, [],
            "skills/ 出现源锚/拍板引语/批次名词（增量即红；豁免须走 EXEMPT 登记）：\n"
            + "\n".join(hits))


if __name__ == "__main__":
    unittest.main()
