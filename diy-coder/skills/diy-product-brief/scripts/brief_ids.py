# -*- coding: utf-8 -*-
"""diy-product-brief ID 与 distillate 域：VD-### 序列、src 矩阵、{text, src} 条目形状。"""

import re
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import nonempty, v  # noqa: E402
from diyc_distillate import check_distillate_entries, check_src  # noqa: E402

VD_RE = re.compile(r"VD-\d{3}")


def check_pairs(value, where, keys, label, violations, optional=(), warnings=None):
    """映射列表：每项须为映射；keys 恒非空；optional 键出现时不得为空。
    users/value 额外带 id（VD-### 文件级序列）——缺 ID warning 不阻塞（存量口径）。"""
    if value is None:
        return
    if not isinstance(value, list):
        violations.append(v("EMPTY_FIELD", where, "%s 不是列表" % label))
        return
    for i, item in enumerate(value):
        iw = "%s[%d]" % (where, i)
        if not isinstance(item, dict):
            violations.append(v("EMPTY_FIELD", iw, "%s 条目不是映射" % label))
            continue
        for key in list(keys) + [k for k in optional if k in item]:
            if not nonempty(item.get(key)):
                violations.append(v("EMPTY_FIELD", "%s.%s" % (iw, key), "%s 为空" % key))
        if label in ("users", "value"):
            iid = item.get("id")
            if nonempty(iid):
                if not VD_RE.fullmatch(str(iid)):
                    violations.append(v("ENUM_INVALID", iw + ".id",
                                        "id 须为 VD-###（三位零填充），实为 %s" % iid))
            elif warnings is not None:
                warnings.append(v("EMPTY_FIELD", iw + ".id",
                                  "缺 id（新写必铸 VD-###；存量缺 ID 不阻塞）"))


def collect_vd_ids(data):
    """users[] + value[] 的 VD-### 顺序表（两列表共用文件级序列，按文档块出现顺序）。"""
    found = []
    brief = data.get("brief") if isinstance(data, dict) else None
    if not isinstance(brief, dict):
        return found
    for label in ("users", "value"):
        items = brief.get(label)
        if not isinstance(items, list):
            continue
        for i, item in enumerate(items):
            if isinstance(item, dict) and nonempty(item.get("id")):
                m = re.fullmatch(r"VD-(\d{3})", str(item["id"]))
                if m:
                    found.append((int(m.group(1)), "brief.%s[%d]" % (label, i)))
    return found


def check_vd_ids(found):
    """VD 文件内唯一、顺序递增（按 users→value 文档序）。"""
    violations = []
    seen = set()
    last = None
    for num, where in found:
        key = "VD-%03d" % num
        if key in seen:
            violations.append(v("DUPLICATE_ID", where,
                                "VD ID %s 重复（两列表共用文件级序列、永不重用）" % key))
        seen.add(key)
        if last is not None and num <= last:
            violations.append(v("ENUM_INVALID", where,
                                "VD ID %s 未顺序递增（上一 VD 数值 %d）" % (key, last)))
        last = num
    return violations


def local_vd_set(data):
    return {"VD-%03d" % n for n, _w in collect_vd_ids(data)}
