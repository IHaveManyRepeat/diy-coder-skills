# -*- coding: utf-8 -*-
"""diy-spec-scan check 校验域：spec-scan.yaml 顶层结构 / ID 形态 / 六要素枚举 / 计数一致性校验与 --final 定稿义务（违规码常量表同居）。."""

import re

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import nonempty, v, walk_strings  # noqa: E402

SS_ID_RE = re.compile(r"SS-\d{3}\Z")
FINDING_ID_RE = re.compile(r"SS-\d{3}-\d{2}\Z")
LINE_RE = re.compile(r"[0-9]+\Z")

FINDING_TYPES = ("分支无定义", "术语冲突", "接口缺口", "输入不明",
                 "输出不明", "时序不明", "直接矛盾", "隐含假设")
FINDING_TEXT_FIELDS = ("quote", "read_as", "stuck", "would_guess")
SEVERITIES = ("阻断", "建议", "观察")
FINDING_SOURCES = ("卡点", "穷举", "交叉认证")
SUMMARY_KEYS = ("total", "blocker", "major", "minor", "units_total", "by_source", "units_scanned")
PROJECT_KEYS = ("name", "created", "updated")
ASSUMPTION = "[假设]"

# ---------------------------------------------------------------- check：spec-scan.yaml 校验

# trace: diy-spec-scan 顶层结构校验（project 三键 + scans + revisions）
def check_top_level(data, show):
    violations = []
    project = data.get("project")
    if not isinstance(project, dict):
        violations.append(v("EMPTY_FIELD", show + " project",
                            "project 缺失或不是映射（须含 name/created/updated）"))
    else:
        for key in PROJECT_KEYS:
            if not nonempty(project.get(key)):
                violations.append(v("EMPTY_FIELD", "%s project.%s" % (show, key),
                                    "project.%s 缺失" % key))
    for key in ("scans", "revisions"):
        if key not in data:
            violations.append(v("EMPTY_FIELD", "%s %s" % (show, key),
                                "%s 缺失（无内容写空列表）" % key))
        elif not isinstance(data.get(key), list):
            violations.append(v("EMPTY_FIELD", "%s %s" % (show, key),
                                "%s 不是列表" % key))
    return violations

# trace: diy-spec-scan 顶层 schema 分层判定（schema ≥2 走新字段必填；缺失/非整数按存量
# 兼容——旧文件无 schema 键，新字段缺省生效）
def is_schema_v2(data):
    value = data.get("schema") if isinstance(data, dict) else None
    return isinstance(value, int) and not isinstance(value, bool) and value >= 2

# trace: diy-spec-scan scans[].id 形态（SS-0nn）与全局唯一校验
def check_scan_id(sid, where, seen):
    if not nonempty(sid):
        return [v("EMPTY_FIELD", where, "id 缺失（须为 SS-0nn）")]
    text = str(sid)
    if not SS_ID_RE.fullmatch(text):
        return [v("ENUM_INVALID", where, "id 须为 SS-0nn（三位零填充），实为 %s" % text)]
    if text in seen:
        return [v("DUPLICATE_ID", where, "scan ID %s 重复（ID 稳定不重用）" % text)]
    seen.add(text)
    return []

# trace: diy-spec-scan scans[].target 校验（在场且含 path）
def check_scan_target(scan, where):
    target = scan.get("target")
    if not isinstance(target, dict):
        return [v("EMPTY_FIELD", where + ".target", "target 缺失或不是映射（须含 path）")]
    if not nonempty(target.get("path")):
        return [v("EMPTY_FIELD", where + ".target.path",
                  "target.path 缺失（被扫目标相对 project-root 的路径）")]
    return []

# trace: diy-spec-scan units[] 三件套校验（unit / path / scanned 布尔）
def check_units(where, units):
    violations = []
    for i, unit in enumerate(units):
        uw = "%s.units[%d]" % (where, i)
        if not isinstance(unit, dict):
            violations.append(v("EMPTY_FIELD", uw, "unit 不是映射（须含 unit/path/scanned）"))
            continue
        if not nonempty(unit.get("unit")):
            violations.append(v("EMPTY_FIELD", uw + ".unit",
                                "单元名缺失（`## ` 标题文本或文件名）"))
        if not nonempty(unit.get("path")):
            violations.append(v("EMPTY_FIELD", uw + ".path", "单元所在文件路径缺失"))
        scanned = unit.get("scanned")
        if not isinstance(scanned, bool):
            violations.append(v("EMPTY_FIELD", uw + ".scanned",
                                "scanned 须为布尔（true/false），实为 %s"
                                % (scanned if nonempty(scanned) else "未声明")))
    return violations

# trace: diy-spec-scan findings[] 定位标签（msg 里指明是哪条 finding）
def finding_label(index, finding):
    fid = finding.get("id")
    if nonempty(fid):
        return "findings[%d]（%s）" % (index, fid)
    return "findings[%d]" % index

# trace: diy-spec-scan findings[].id 形态（SS-0nn-nn）与唯一校验
def check_finding_id(fid, where, index, seen):
    if not nonempty(fid):
        return [v("EMPTY_FIELD", where, "findings[%d] 的 id 缺失（须为 SS-0nn-nn）" % index)]
    text = str(fid)
    if not FINDING_ID_RE.fullmatch(text):
        return [v("ENUM_INVALID", where,
                  "findings[%d] 的 id 须为 SS-0nn-nn，实为 %s" % (index, text))]
    if text in seen:
        return [v("DUPLICATE_ID", where, "finding ID %s 重复（ID 稳定不重用）" % text)]
    seen.add(text)
    return []

# trace: diy-spec-scan findings[].where 形态（<path> 或 <path>:<行号>：无空白、行号纯数字）
def is_where(value):
    text = str(value)
    if not text or re.search(r"\s", text):
        return False
    head, sep, tail = text.rpartition(":")
    if not sep:
        return True
    return bool(head) and bool(LINE_RE.fullmatch(tail))

# trace: diy-spec-scan findings[] 六要素校验（id / type 八值 / where 形态 / 四字段非空 /
# severity 三值 / source 三值数组·schema 分层）
def check_findings(where, findings, seen, schema2):
    violations = []
    for i, finding in enumerate(findings):
        fw = "%s.findings[%d]" % (where, i)
        if not isinstance(finding, dict):
            violations.append(v("EMPTY_FIELD", fw,
                                "finding 不是映射（id/type/where/quote/read_as/stuck/"
                                "would_guess/severity/source 九件套）"))
            continue
        violations += check_finding_id(finding.get("id"), fw + ".id", i, seen)
        label = finding_label(i, finding)
        ftype = finding.get("type")
        if not nonempty(ftype):
            violations.append(v("EMPTY_FIELD", fw + ".type", "%s 的 type 缺失" % label))
        elif str(ftype) not in FINDING_TYPES:
            violations.append(v("ENUM_INVALID", fw + ".type",
                                "%s 的 type 越界：%s（合法集 %s）"
                                % (label, ftype, "|".join(FINDING_TYPES))))
        spot = finding.get("where")
        if not nonempty(spot):
            violations.append(v("EMPTY_FIELD", fw + ".where",
                                "%s 的 where 缺失（歧义在规格里的位置）" % label))
        elif not is_where(spot):
            violations.append(v("ENUM_INVALID", fw + ".where",
                                "%s 的 where 须形如 <path> 或 <path>:<行号>，实为 %s"
                                % (label, spot)))
        for field in FINDING_TEXT_FIELDS:
            if not nonempty(finding.get(field)):
                violations.append(v("EMPTY_FIELD", "%s.%s" % (fw, field),
                                    "%s 的 %s 为空（quote/read_as/stuck/would_guess 缺一不可；"
                                    "would_guess = 若我是实现者我会猜成什么）" % (label, field)))
        severity = finding.get("severity")
        if not nonempty(severity):
            violations.append(v("EMPTY_FIELD", fw + ".severity", "%s 的 severity 缺失" % label))
        elif str(severity) not in SEVERITIES:
            violations.append(v("ENUM_INVALID", fw + ".severity",
                                "%s 的 severity 越界：%s（合法集 %s）"
                                % (label, severity, "|".join(SEVERITIES))))
        source = finding.get("source")
        if source is None:
            if schema2:
                violations.append(v("EMPTY_FIELD", fw + ".source",
                                    "%s 的 source 缺失（schema ≥2 须为非空数组，"
                                    "元素 ∈ %s）" % (label, "|".join(FINDING_SOURCES))))
            # 无 schema 的存量文件：缺 source 缺省当 [卡点]，不报错（向后兼容）
        elif not isinstance(source, list):
            violations.append(v("EMPTY_FIELD", fw + ".source",
                                "%s 的 source 须为数组，实为 %s（元素 ∈ %s）"
                                % (label, source, "|".join(FINDING_SOURCES))))
        elif not source:
            violations.append(v("EMPTY_FIELD", fw + ".source",
                                "%s 的 source 为空数组（须含至少一个元素 ∈ %s）"
                                % (label, "|".join(FINDING_SOURCES))))
        else:
            for item in source:
                if str(item) not in FINDING_SOURCES:
                    violations.append(v("ENUM_INVALID", fw + ".source",
                                        "%s 的 source 越界：%s（合法集 %s）"
                                        % (label, item, "|".join(FINDING_SOURCES))))
    return violations

# trace: diy-spec-scan findings[].source 计数取值（summary 真值与回执计数同口径）：
# 数组合法元素逐个；缺失/非数组/空/全越界 → 缺省 [卡点]（存量兼容）
def source_values(finding):
    source = finding.get("source")
    if isinstance(source, list):
        valid = [str(name) for name in source if str(name) in FINDING_SOURCES]
        if valid:
            return valid
    return [FINDING_SOURCES[0]]

# trace: diy-spec-scan summary 真值计算（findings 计数 + source 分法按元素计 + units 计数）
def real_summary(units, findings):
    severity = {name: 0 for name in SEVERITIES}
    by_source = {name: 0 for name in FINDING_SOURCES}
    for finding in findings:
        if not isinstance(finding, dict):
            continue
        if str(finding.get("severity")) in severity:
            severity[str(finding["severity"])] += 1
        for name in source_values(finding):
            by_source[name] += 1
    return {
        "total": len(findings),
        "blocker": severity["阻断"],
        "major": severity["建议"],
        "minor": severity["观察"],
        "units_total": len(units),
        "by_source": by_source,
        "units_scanned": sum(1 for unit in units
                             if isinstance(unit, dict) and unit.get("scanned") is True),
    }

# trace: diy-spec-scan 计数值比对（布尔不得充当整数：true 不等于 1）
def count_matches(value, real):
    return isinstance(value, int) and not isinstance(value, bool) and value == real

# trace: diy-spec-scan by_source 映射比对（三键齐且各键计数与真值一致）
def source_counts_match(value, real):
    if not isinstance(value, dict) or set(value) != set(real):
        return False
    return all(count_matches(value.get(key), real[key]) for key in real)

# trace: diy-spec-scan summary 计数与真值一致性校验（不符 → SET_MISMATCH）；
# by_source 同享 schema 分层：schema ≥2 缺失报 EMPTY_FIELD，无 schema 存量缺省兼容不报
def check_summary(scan, where, units, findings, schema2):
    sw = where + ".summary"
    summary = scan.get("summary")
    if not isinstance(summary, dict):
        return [v("EMPTY_FIELD", sw,
                  "summary 缺失或不是映射（total/blocker/major/minor/units_total/"
                  "by_source/units_scanned）")]
    real = real_summary(units, findings)
    violations = []
    for key in SUMMARY_KEYS:
        if key not in summary:
            if key == "by_source" and not schema2:
                continue  # 无 schema 的存量文件：summary 无 by_source 键，缺省兼容
            violations.append(v("EMPTY_FIELD", "%s.%s" % (sw, key), "summary.%s 缺失" % key))
        elif key == "by_source":
            if not source_counts_match(summary.get(key), real[key]):
                violations.append(v("SET_MISMATCH", "%s.by_source" % (sw),
                                    "summary.by_source=%s 与实际计数 %s 不符"
                                    % (summary.get(key), real[key])))
        elif not count_matches(summary.get(key), real[key]):
            violations.append(v("SET_MISMATCH", "%s.%s" % (sw, key),
                                "summary.%s=%s 与实际计数 %d 不符"
                                % (key, summary.get(key), real[key])))
    return violations

# trace: diy-spec-scan --final 附加义务（全单元已扫 + findings 零 [假设]，quote 豁免）
def check_final_duties(where, units, findings):
    violations = []
    for i, unit in enumerate(units):
        if isinstance(unit, dict) and unit.get("scanned") is not True:
            name = unit.get("path") or unit.get("unit") or "第 %d 个单元" % (i + 1)
            violations.append(v("SET_MISMATCH", "%s.units[%d].scanned" % (where, i),
                                "--final 要求全部单元 scanned: true；%s 尚未扫"
                                "（漏扫单元会漏掉歧义）" % name))
    for i, finding in enumerate(findings):
        # quote 豁免（2026-09-16 裁定）：引文是证据、不是未落定推断，而被扫规格本身可能
        # 就含该标记——拦引文会逼出全角改写，让「逐字引原文」变成不可能。
        scanned = ({k: val for k, val in finding.items() if k != "quote"}
                   if isinstance(finding, dict) else finding)
        if any(ASSUMPTION in s for _p, s in walk_strings(scanned, "")):
            violations.append(v("ASSUMPTION_PRESENT", "%s.findings[%d]" % (where, i),
                                "--final 要求零 [假设]（quote 引文豁免）；"
                                "未决推断须先落定再交"))
    return violations

# trace: diy-spec-scan 单条 scan 全量校验（id/target/units/findings/summary + --final 义务）
def check_scan(index, scan, show, final, schema2, seen_scan_ids, seen_finding_ids):
    where = "%s.scans[%d]" % (show, index)
    if not isinstance(scan, dict):
        return [v("EMPTY_FIELD", where, "scan 不是映射")]
    violations = check_scan_id(scan.get("id"), where + ".id", seen_scan_ids)
    violations += check_scan_target(scan, where)
    units = scan.get("units")
    if not isinstance(units, list):
        violations.append(v("EMPTY_FIELD", where + ".units", "units 缺失或不是列表"))
        units = []
    else:
        violations += check_units(where, units)
    findings = scan.get("findings")
    if not isinstance(findings, list):
        violations.append(v("EMPTY_FIELD", where + ".findings",
                            "findings 缺失或不是列表（无歧义写空列表）"))
        findings = []
    else:
        violations += check_findings(where, findings, seen_finding_ids, schema2)
    violations += check_summary(scan, where, units, findings, schema2)
    if final:
        violations += check_final_duties(where, units, findings)
    return violations

# trace: diy-spec-scan check 回执计数（scan / 单元 / finding + 分档分型分法）
def scan_counts(scans):
    units = findings = scanned = 0
    by_severity = {}
    by_type = {}
    by_source = {name: 0 for name in FINDING_SOURCES}
    for scan in scans:
        if not isinstance(scan, dict):
            continue
        scan_units = scan.get("units")
        if isinstance(scan_units, list):
            units += len(scan_units)
            scanned += sum(1 for unit in scan_units
                           if isinstance(unit, dict) and unit.get("scanned") is True)
        scan_findings = scan.get("findings")
        if not isinstance(scan_findings, list):
            continue
        findings += len(scan_findings)
        for finding in scan_findings:
            if not isinstance(finding, dict):
                continue
            severity = finding.get("severity")
            if nonempty(severity):
                by_severity[str(severity)] = by_severity.get(str(severity), 0) + 1
            ftype = finding.get("type")
            if nonempty(ftype):
                by_type[str(ftype)] = by_type.get(str(ftype), 0) + 1
            for name in source_values(finding):
                by_source[name] += 1
    return {"scans": len(scans), "units": units, "units_scanned": scanned,
            "findings": findings, "by_severity": by_severity, "by_type": by_type,
            "by_source": by_source}
