# -*- coding: utf-8 -*-
"""diy-research 校验域：条目级锚（RF/RK/RO）唯一/顺序、findings/synthesis/distillate 形状与 src 矩阵。"""

import re
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import nonempty, v, walk_strings  # noqa: E402
from diyc_distillate import (SRC_ID_RE, SRC_PATH_RE,  # noqa: E402
                             check_distillate_entries, check_src)

DIMENSIONS = ("市场", "技术", "领域")
STATUSES = ("草稿", "已定稿")
CONFIDENCES = ("高", "中", "低")
SYNTHESIS_KEYS = ("executive_summary", "key_points", "open_questions")
DISTILLATE_SCALARS = ("problem",)
DISTILLATE_LISTS = ("target_users", "value_props", "constraints", "open_questions")

RS_RE = re.compile(r"RS-\d{3}")
RF_RE = re.compile(r"RF-\d{3}")
RK_RE = re.compile(r"RK-\d{3}")
RO_RE = re.compile(r"RO-\d{3}")
# 条目级稳定 ID：finding=RF / synthesis 要点=RK / 待决=RO；src 锚只认这三前缀（本产物内）
ANCHOR_ID_RE = re.compile(r"(RF|RK|RO)-\d{3}")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
URL_RE = re.compile(r"https?://\S+")


def check_string_list(value, where, label):
    """非空字符串列表校验（goals 共用）。"""
    violations = []
    if not isinstance(value, list):
        return [v("EMPTY_FIELD", where, "%s 须为列表" % label)]
    if not value:
        return [v("EMPTY_FIELD", where, "%s 为空（至少 1 条）" % label)]
    for i, item in enumerate(value):
        if not nonempty(item):
            violations.append(v("EMPTY_FIELD", "%s[%d]" % (where, i),
                                "%s 条目为空" % label))
    return violations


def collect_anchor_ids(data):
    """全文件条目级锚集合（RF/RK/RO）与顺序表——ID 唯一性与顺序递增在文档序上核。"""
    found = []  # [(prefix, num, where)]
    def _take(item, prefix, where):
        if isinstance(item, dict) and nonempty(item.get("id")):
            m = re.fullmatch(r"(%s)-(\d{3})" % prefix, str(item["id"]))
            if m:
                found.append((m.group(1), int(m.group(2)), where))
    for ri, record in enumerate(items_list(data, "researches")):
        rw = "researches[%d]" % ri
        for fi, finding in enumerate(items_list(record, "findings")):
            _take(finding, "RF", "%s.findings[%d]" % (rw, fi))
        syn = record.get("synthesis") if isinstance(record, dict) else None
        if isinstance(syn, dict):
            for key, prefix in (("key_points", "RK"), ("open_questions", "RO")):
                for i, item in enumerate(items_list(syn, key)):
                    _take(item, prefix, "%s.synthesis.%s[%d]" % (rw, key, i))
    return found


def items_list(node, key):
    value = node.get(key) if isinstance(node, dict) else None
    return value if isinstance(value, list) else []


def check_anchor_ids(found):
    """RF/RK/RO：文件内全局唯一、顺序递增（格式已在发现时过滤）。"""
    violations = []
    seen = set()
    last_num = {}
    for prefix, num, where in found:
        key = "%s-%03d" % (prefix, num)
        if key in seen:
            violations.append(v("DUPLICATE_ID", where,
                                "条目 ID %s 重复（文件内全局唯一、永不重用）" % key))
        seen.add(key)
        prev = last_num.get(prefix)
        if prev is not None and num <= prev:
            violations.append(v("ENUM_INVALID", where,
                                "条目 ID %s 未顺序递增（上一同前缀 ID 数值 %d）" % (key, prev)))
        last_num[prefix] = num
    return violations


def local_anchor_set(data):
    """本文件全部合法 RF/RK/RO 锚集合（src 在场性核验用）。"""
    return {"%s-%03d" % (p, n) for p, n, _w in collect_anchor_ids(data)}


# trace: 源技能引用纪律（每条断言带来源）——sources 非空 + url http(s) + accessed 日期
def check_finding(finding, where, warnings):
    violations = []
    if not isinstance(finding, dict):
        return [v("EMPTY_FIELD", where, "finding 不是映射")]
    fid = finding.get("id")
    if nonempty(fid):
        if not RF_RE.fullmatch(str(fid)):
            violations.append(v("ENUM_INVALID", where + ".id",
                                "id 须为 RF-###（三位零填充），实为 %s" % fid))
    else:
        warnings.append(v("EMPTY_FIELD", where + ".id",
                          "finding 缺 id（新写必铸 RF-###；存量缺 ID 不阻塞）"))
    for key in ("area", "claim"):
        if not nonempty(finding.get(key)):
            violations.append(v("EMPTY_FIELD", where + "." + key, "%s 缺失或为空" % key))
    confidence = finding.get("confidence")
    if not nonempty(confidence):
        violations.append(v("EMPTY_FIELD", where + ".confidence", "confidence 缺失"))
    elif str(confidence) not in CONFIDENCES:
        violations.append(v("ENUM_INVALID", where + ".confidence",
                            "confidence 越界：%s（合法集 %s）"
                            % (confidence, "|".join(CONFIDENCES))))
    sources = finding.get("sources")
    if not isinstance(sources, list):
        violations.append(v("EMPTY_FIELD", where + ".sources",
                            "sources 缺失或不是列表（每条断言须带来源）"))
        return violations
    if not sources:
        violations.append(v("EMPTY_FIELD", where + ".sources",
                            "sources 为空（每条断言须带来源，不得留空）"))
    for i, source in enumerate(sources):
        sw = "%s.sources[%d]" % (where, i)
        if not isinstance(source, dict):
            violations.append(v("EMPTY_FIELD", sw, "source 不是映射"))
            continue
        if not nonempty(source.get("title")):
            violations.append(v("EMPTY_FIELD", sw + ".title", "title 缺失或为空"))
        url = source.get("url")
        if not nonempty(url):
            violations.append(v("EMPTY_FIELD", sw + ".url", "url 缺失（须为 http(s) 地址）"))
        elif not URL_RE.fullmatch(str(url).strip()):
            violations.append(v("ENUM_INVALID", sw + ".url",
                                "url 须为 http(s) 绝对地址，实为 %s" % url))
        accessed = source.get("accessed")
        if not nonempty(accessed):
            violations.append(v("EMPTY_FIELD", sw + ".accessed", "accessed 缺失"))
        elif not DATE_RE.fullmatch(str(accessed)):
            violations.append(v("ENUM_INVALID", sw + ".accessed",
                                "accessed 须为 YYYY-MM-DD，实为 %s" % accessed))
    return violations


def check_synthesis_list(value, where, prefix, final, warnings):
    """key_points / open_questions：条目 {id, text}；字符串旧形态 → 缺 ID warning。"""
    violations = []
    if not isinstance(value, list):
        return [v("EMPTY_FIELD", where, "须为列表")]
    if not value:
        return [v("EMPTY_FIELD", where, "为空（至少 1 条）")]
    for i, item in enumerate(value):
        iw = "%s[%d]" % (where, i)
        if not isinstance(item, dict):
            warnings.append(v("EMPTY_FIELD", iw,
                              "条目为字符串旧形态；新写须 {id: %s-###, text}" % prefix))
            if not nonempty(item):
                violations.append(v("EMPTY_FIELD", iw, "条目为空"))
            continue
        iid = item.get("id")
        if nonempty(iid):
            if not re.fullmatch(r"%s-\d{3}" % prefix, str(iid)):
                violations.append(v("ENUM_INVALID", iw + ".id",
                                    "id 须为 %s-###（三位零填充），实为 %s" % (prefix, iid)))
        else:
            warnings.append(v("EMPTY_FIELD", iw + ".id",
                              "缺 id（新写必铸 %s-###；存量缺 ID 不阻塞）" % prefix))
        if not nonempty(item.get("text")):
            violations.append(v("EMPTY_FIELD", iw + ".text", "text 缺失或为空"))
    return violations


def check_synthesis(synthesis, where, final, warnings):
    """synthesis 三键：executive_summary 字符串；key_points / open_questions 对象列表。"""
    if synthesis is None:
        if final:
            return [v("EMPTY_FIELD", where, "--final 要求 synthesis 三键非空")]
        return []
    if not isinstance(synthesis, dict):
        return [v("EMPTY_FIELD", where, "synthesis 不是映射")]
    violations = []
    for key in SYNTHESIS_KEYS:
        value = synthesis.get(key)
        sw = "%s.%s" % (where, key)
        if value is None:
            if final:
                violations.append(v("EMPTY_FIELD", sw, "--final 要求 %s 非空" % key))
            continue
        if key == "executive_summary":
            if not isinstance(value, str) or not nonempty(value):
                violations.append(v("EMPTY_FIELD", sw, "executive_summary 须为非空字符串"))
        else:
            prefix = "RK" if key == "key_points" else "RO"
            violations += check_synthesis_list(value, sw, prefix, final, warnings)
    return violations


def check_record(index, record, final, where_base, warnings):
    violations = []
    where = "%s.researches[%d]" % (where_base, index)
    if not isinstance(record, dict):
        return [v("EMPTY_FIELD", where, "记录不是映射")]

    rid = record.get("id")
    if not nonempty(rid):
        violations.append(v("EMPTY_FIELD", where + ".id", "id 缺失"))
    elif not RS_RE.fullmatch(str(rid)):
        violations.append(v("ENUM_INVALID", where + ".id",
                            "id 须为 RS-0nn（三位零填充），实为 %s" % rid))

    dimension = record.get("dimension")
    if not nonempty(dimension):
        violations.append(v("EMPTY_FIELD", where + ".dimension", "dimension 缺失"))
    elif str(dimension) not in DIMENSIONS:
        violations.append(v("ENUM_INVALID", where + ".dimension",
                            "dimension 越界：%s（合法集 %s）"
                            % (dimension, "|".join(DIMENSIONS))))

    for key in ("topic", "scope"):
        if not nonempty(record.get(key)):
            violations.append(v("EMPTY_FIELD", where + "." + key, "%s 缺失或为空" % key))

    violations += check_string_list(record.get("goals"), where + ".goals", "goals")

    date = record.get("date")
    if not nonempty(date):
        violations.append(v("EMPTY_FIELD", where + ".date", "date 缺失"))
    elif not DATE_RE.fullmatch(str(date)):
        violations.append(v("ENUM_INVALID", where + ".date",
                            "date 须为 YYYY-MM-DD，实为 %s" % date))

    status = record.get("status")
    if not nonempty(status):
        violations.append(v("EMPTY_FIELD", where + ".status", "status 缺失"))
    elif str(status) not in STATUSES:
        violations.append(v("ENUM_INVALID", where + ".status",
                            "status 越界：%s（合法集 %s）"
                            % (status, "|".join(STATUSES))))

    findings = record.get("findings")
    if findings is None:
        if final:
            violations.append(v("EMPTY_FIELD", where + ".findings",
                                "--final 要求 findings 非空（至少 1 条带来源的断言）"))
    elif not isinstance(findings, list):
        violations.append(v("EMPTY_FIELD", where + ".findings", "findings 不是列表"))
    else:
        if final and not findings:
            violations.append(v("EMPTY_FIELD", where + ".findings",
                                "--final 要求 findings 非空（至少 1 条带来源的断言）"))
        for i, finding in enumerate(findings):
            violations += check_finding(finding, "%s.findings[%d]" % (where, i), warnings)

    violations += check_synthesis(record.get("synthesis"), where + ".synthesis", final, warnings)

    if final:
        if nonempty(status) and str(status) != "已定稿":
            violations.append(v("STATUS_MISMATCH", where + ".status",
                                "记录未定稿（status: %s）；--final 要求 status: 已定稿" % status))
        if any("[假设]" in s for _p, s in walk_strings(record, "")):
            violations.append(v("ASSUMPTION_PRESENT", where,
                                "--final 要求零 [假设]；未决假设须落为 open_questions 后再定稿"))
    return violations


# trace: 夜队列 Q-103（底单 :361 ②：check --final 加 distillate 存在＋五字段非空校验）
# trace: 批 5a——target_users 条目化入 LISTS；四列表条目 {text, src} 硬校验（--final）
def check_distillate_final(distillate, show, local_ids, warnings):
    """--final 文档级交出面义务：顶层 `distillate` 在场（映射）且五字段非空——
    `problem` 标量非空；四列表条目恰为 `{text, src}`（形态例外，--final 硬校验）；
    src 按批 5a §3 矩阵。起草期不查。"""
    if not isinstance(distillate, dict):
        return [v("EMPTY_FIELD", show + " distillate",
                  "--final 要求 distillate 非空（交出面：下游 PRD 输入）")]
    violations = []
    for key in DISTILLATE_SCALARS:
        if not nonempty(distillate.get(key)):
            violations.append(v("EMPTY_FIELD", "%s distillate.%s" % (show, key),
                                "--final 要求 distillate.%s 非空" % key))
    for key in DISTILLATE_LISTS:
        value = distillate.get(key)
        where = "%s distillate.%s" % (show, key)
        if not isinstance(value, list):
            violations.append(v("EMPTY_FIELD", where, "--final 要求 distillate.%s 为列表" % key))
            continue
        if not value:
            violations.append(v("EMPTY_FIELD", where,
                                "--final 要求 distillate.%s 非空（至少 1 条）" % key))
            continue
        check_distillate_entries(value, where, ANCHOR_ID_RE, "RF/RK/RO", local_ids,
                                 True, warnings, violations)
    return violations


def record_ids(records):
    return [str(r["id"]) for r in records
            if isinstance(r, dict) and nonempty(r.get("id"))]
