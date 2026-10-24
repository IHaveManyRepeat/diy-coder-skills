# -*- coding: utf-8 -*-
"""diy-prd 校验域：out_of_scope 两形态（继承 {src} / 自产 OS-###）与可选 src 语法。"""

import re
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_check_docs_lib import dup, nonempty, req  # noqa: E402

# 批 5a：OS-### 自产约束 ID；src 语法（ID 形态或点路径）
OS_RE = re.compile(r"OS-\d{3}")
SRC_ID_RE = re.compile(r"[A-Z]{1,4}-\d+(?:\.\d+)*")
SRC_PATH_RE = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+(\[\d+\])*$")


def check_src(src, w, report):
    """可选 src：出现即校验语法（ID 形态或点路径）；跨产物在场性归 prd 会话侧。"""
    if src is None:
        return
    if not nonempty(src):
        report.add("EMPTY_FIELD", w + ".src", "src 出现时不得为空")
        return
    s = str(src).strip()
    if SRC_ID_RE.fullmatch(s) or SRC_PATH_RE.fullmatch(s):
        return
    report.add("ENUM_INVALID", w + ".src",
               "src 须为 ID 形态或点路径，实为 %s" % s)




def check_out_of_scope(doc, rel, counts, report):
    # 批 5a：out_of_scope 两形态——恰好 {src}（继承）或恰好 {id: OS-###, statement}（自产）
    os_items = doc.get("out_of_scope")
    if os_items is not None:
        if not isinstance(os_items, list):
            report.add("EMPTY_FIELD", rel + " out_of_scope", "out_of_scope 须为列表")
        else:
            os_ids = []
            for i, item in enumerate(os_items):
                ow = "%s out_of_scope[%d]" % (rel, i)
                if not isinstance(item, dict):
                    report.add("EMPTY_FIELD", ow, "条目须为映射（两形态：{src} 或 {id, statement}）")
                    continue
                keys = set(item)
                if keys == {"src"}:
                    check_src(item.get("src"), ow, report)
                elif keys == {"id", "statement"}:
                    oid = item.get("id")
                    req(report, ow + ".id", oid, "OS id")
                    if nonempty(oid):
                        if not OS_RE.fullmatch(str(oid)):
                            report.add("ENUM_INVALID", ow + ".id",
                                       "id 须为 OS-###（三位零填充），实为 %s" % oid)
                        else:
                            os_ids.append((str(oid), ow + ".id"))
                    req(report, ow + ".statement", item.get("statement"), "OS statement")
                    counts["os"] += 1
                else:
                    report.add("EMPTY_FIELD", ow,
                               "条目混键/形态非法（恰为 {src} 或 {id, statement}；"
                               "禁止 {id, statement, src} 混形）：%s" % sorted(keys))
            dup(report, os_ids, "OS id")
    return
