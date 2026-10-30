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
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS = os.path.join(ROOT, "skills")
EXTS = (".py", ".md", ".yaml", ".csv")

# 扩展标记词（批 6 已清零族）；顺序无关，逐 pattern 独立断言
PATTERNS = [
    ("源侧", re.compile(r"源侧")),
    ("trace 批次头", re.compile(r"# trace: B\d")),
    ("batch3-contract", re.compile(r"batch3-contract")),
    ("拍板引语式裁定", re.compile(r"裁定 ?[0-9]")),
    ("批次号 C·N", re.compile(r"C·[0-9]")),
    ("census 编号", re.compile(r"census-", re.IGNORECASE)),
    ("保真照搬", re.compile(r"保真照搬")),
    ("收编自/裁自", re.compile(r"收编自|裁自")),
    # 源+反引号路径锚（census 类①）——排除产品复合词（单一源/护栏源/来源 等）
    ("源+反引号锚", re.compile(
        r"(?<!单一)(?<!两)(?<!护栏)(?<!情报)(?<!测试)(?<!来)(?<!真)(?<!数据)"
        r"(?<!散)(?<!唯一)源 `")),
    (".analysis/ 目录引用", re.compile(r"\.analysis/")),
]

# 豁免清单：(skills/ 相对路径, 命中原文) —— 逐条有裁定依据
EXEMPT = {
    # 乙-4 用户裁 2026-10-29：bmb-builder 产品行为＝分析报告落点约定
    ("diy-bmb-builder/SKILL.md", ".analysis/"),
    ("diy-bmb-builder/steps/03-analyze.md", ".analysis/"),
    ("diy-bmb-builder/steps/05-finish.md", ".analysis/"),
}


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
