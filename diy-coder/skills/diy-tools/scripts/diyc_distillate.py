# -*- coding: utf-8 -*-
"""distillate {text, src} 条目公共校验件 —— src 语法/在场性矩阵与条目形状单源。

批 5a 四技能（research/brief/prfaq）check_src/check_distillate_entries 四胞胎抽合
（2026-10-25 用户裁随 Q-122）；各技能脚本照 diyc_lib 先例 sys.path 引入。
"""

import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diyc_lib import nonempty, v  # noqa: E402

# src 语法：ID 形态（本域前缀之外也放过——跨产物 ID 形态）或点路径（a.b.c）
SRC_ID_RE = re.compile(r"[A-Z]{1,4}-\d+(?:\.\d+)*")
SRC_PATH_RE = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+(\[\d+\])*$")


def src_syntax_ok(s):
    """src 语法合法＝ID 形态或点路径。"""
    return bool(SRC_ID_RE.fullmatch(s) or SRC_PATH_RE.fullmatch(s))


def check_src(src, where, local_re, local_name, local_ids, final, warnings, violations):
    """src 按批 5a §3 矩阵：本产物内锚不在场＝违规；语法不合＝违规；
    跨产物 ID/结构键缺源文件信息时只做语法与本产物内核验。
    local_re＝本域锚正则；local_name＝文案锚名；调用方传本域常量。"""
    if not nonempty(src):
        violations.append(v("EMPTY_FIELD", where + ".src",
                            "src 缺失（{text, src} 条目必带 src 锚）"))
        return
    s = str(src).strip()
    if local_re.fullmatch(s):
        if s not in local_ids:
            violations.append(v("UNKNOWN_ID", where + ".src",
                                "src %s 不在场（本产物内 %s 锚须真实存在）" % (s, local_name)))
        return
    if src_syntax_ok(s):
        return
    violations.append(v("ENUM_INVALID", where + ".src",
                        "src 须为 ID 形态（%s 或跨产物前缀）或点路径，实为 %s" % (local_name, s)))


def check_distillate_entries(value, where, local_re, local_name, local_ids, final,
                             warnings, violations):
    """distillate 列表条目：--final 硬校验 {text, src} 形态；起草期字符串旧形态 warning。"""
    if not isinstance(value, list):
        violations.append(v("EMPTY_FIELD", where, "须为列表"))
        return
    if not value:
        violations.append(v("EMPTY_FIELD", where, "为空（至少 1 条）"))
        return
    for i, item in enumerate(value):
        iw = "%s[%d]" % (where, i)
        if not isinstance(item, dict):
            if final:
                violations.append(v("EMPTY_FIELD", iw,
                                    "条目须为 {text, src} 映射（--final 硬校验）"))
            else:
                warnings.append(v("EMPTY_FIELD", iw,
                                  "条目为字符串旧形态；新写须 {text, src}（--final 将拒）"))
            continue
        extra = set(item) - {"text", "src"}
        if extra:
            violations.append(v("EMPTY_FIELD", iw,
                                "条目混入非法键：%s（恰为 {text, src}）" % sorted(extra)))
        if not nonempty(item.get("text")):
            violations.append(v("EMPTY_FIELD", iw + ".text", "text 缺失或为空"))
        check_src(item.get("src"), iw, local_re, local_name, local_ids, final,
                  warnings, violations)
