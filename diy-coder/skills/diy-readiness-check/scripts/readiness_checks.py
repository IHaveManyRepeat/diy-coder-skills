# -*- coding: utf-8 -*-
"""diy-readiness-check check 命令域：readiness.yaml 记录级校验（schema/枚举/一致性/final 义务）与回执。."""

import os

import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import count_by, count_items, display_path, emit_via, load_yaml_safe, nonempty, v, walk_strings  # noqa: E402

from readiness_lib import BLOCKING_SEVERITIES, COUNT_KEYS, DATE_RE, FINDING_AREAS, IR_RE, READINESS_FILE, RECORD_STATUSES, SCOPES, SEVERITIES, VERDICTS  # noqa: E402

# ---------------------------------------------------------------- check

def check_findings(record, where, final):
    violations = []
    findings = record.get("findings")
    if findings is None:
        return [v("EMPTY_FIELD", where + ".findings",
                  "findings 缺失（无发现写空列表）")], []
    if not isinstance(findings, list):
        return [v("EMPTY_FIELD", where + ".findings", "findings 不是列表")], []
    for i, finding in enumerate(findings):
        fw = "%s.findings[%d]" % (where, i)
        if not isinstance(finding, dict):
            violations.append(v("EMPTY_FIELD", fw, "finding 不是映射"))
            continue
        area = finding.get("area")
        if not nonempty(area):
            violations.append(v("EMPTY_FIELD", fw + ".area", "area 缺失"))
        elif str(area) not in FINDING_AREAS:
            violations.append(v("ENUM_INVALID", fw + ".area",
                                "area 越界：%s（合法集 %s）"
                                % (area, "|".join(FINDING_AREAS))))
        severity = finding.get("severity")
        if not nonempty(severity):
            violations.append(v("EMPTY_FIELD", fw + ".severity", "severity 缺失"))
        elif str(severity) not in SEVERITIES:
            violations.append(v("ENUM_INVALID", fw + ".severity",
                                "severity 越界：%s（合法集 %s）"
                                % (severity, "|".join(SEVERITIES))))
        if not nonempty(finding.get("message")):
            violations.append(v("EMPTY_FIELD", fw + ".message", "message 为空"))
        evidence = finding.get("evidence")
        if final and not nonempty(evidence):
            violations.append(v("EVIDENCE_MISSING", fw + ".evidence",
                                "--final 要求每条 finding 带 evidence（具体落点）"))
        elif evidence is not None and not nonempty(evidence):
            violations.append(v("EMPTY_FIELD", fw + ".evidence",
                                "evidence 出现时不得为空"))
    return violations, findings

def check_coverage(record, where, final):
    violations = []
    coverage = record.get("coverage")
    if coverage is None:
        if final:
            violations.append(v("EMPTY_FIELD", where + ".coverage",
                                "--final 要求 coverage 在场（must_frs / covered / gaps）"))
        return violations
    if not isinstance(coverage, dict):
        return [v("EMPTY_FIELD", where + ".coverage", "coverage 不是映射")]
    counts = {}
    for key in ("must_frs", "covered"):
        value = coverage.get(key)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            violations.append(v("ENUM_INVALID", "%s.coverage.%s" % (where, key),
                                "%s 须为非负整数（实为 %s）" % (key, value)))
        else:
            counts[key] = value
    gaps = coverage.get("gaps")
    if not isinstance(gaps, list):
        violations.append(v("EMPTY_FIELD", where + ".coverage.gaps",
                            "gaps 缺失或不是列表（无缺口写空列表）"))
    elif any(not nonempty(g) for g in gaps):
        violations.append(v("EMPTY_FIELD", where + ".coverage.gaps",
                            "gaps 项不得为空（FR-x.y）"))
    if final and len(counts) == 2 and isinstance(gaps, list):
        if counts["must_frs"] != counts["covered"] + len(gaps):
            violations.append(v("SET_MISMATCH", where + ".coverage",
                                "counts 与集合不一致：must_frs=%d ≠ covered=%d + gaps=%d"
                                % (counts["must_frs"], counts["covered"], len(gaps))))
    return violations

def check_counts(record, where, final, findings):
    violations = []
    counts = record.get("counts")
    if counts is None:
        return violations
    if not isinstance(counts, dict):
        return [v("EMPTY_FIELD", where + ".counts", "counts 不是映射")]
    for key in COUNT_KEYS:
        value = counts.get(key)
        if value is None:
            if final:
                violations.append(v("EMPTY_FIELD", "%s.counts.%s" % (where, key),
                                    "--final 要求 counts.%s 在场" % key))
        elif not isinstance(value, int) or isinstance(value, bool) or value < 0:
            violations.append(v("ENUM_INVALID", "%s.counts.%s" % (where, key),
                                "%s 须为非负整数（实为 %s）" % (key, value)))
    by_severity = counts.get("findings_by_severity")
    if by_severity is None:
        if final:
            violations.append(v("EMPTY_FIELD", where + ".counts.findings_by_severity",
                                "--final 要求 counts.findings_by_severity 在场"))
        return violations
    if not isinstance(by_severity, dict):
        return violations + [v("EMPTY_FIELD", where + ".counts.findings_by_severity",
                               "findings_by_severity 不是映射")]
    if final:
        bad = [k for k, val in by_severity.items()
               if not isinstance(val, int) or isinstance(val, bool) or val < 0]
        if bad:
            violations.append(v("ENUM_INVALID", where + ".counts.findings_by_severity",
                                "计数须为非负整数：%s" % "、".join(str(k) for k in bad)))
        tally = {}
        for finding in findings:
            if isinstance(finding, dict) and nonempty(finding.get("severity")):
                key = str(finding["severity"])
                tally[key] = tally.get(key, 0) + 1
        declared = {str(k): val for k, val in by_severity.items()
                    if isinstance(val, int) and not isinstance(val, bool) and val}
        if declared != tally:
            violations.append(v("SET_MISMATCH", where + ".counts.findings_by_severity",
                                "counts 与集合不一致：声明 %s，实际 %s" % (declared, tally)))
    return violations

def check_verdict_findings(record, where, verdict, findings):
    """verdict 与 findings 一致性：就绪 ⇒ 零 严重|高；未就绪 ⇒ 至少 1 条。"""
    if not nonempty(verdict) or str(verdict) not in VERDICTS:
        return []
    blocking = [f for f in findings
                if isinstance(f, dict) and str(f.get("severity")) in BLOCKING_SEVERITIES]
    if str(verdict) == "就绪" and blocking:
        return [v("SET_MISMATCH", where + ".verdict",
                  "verdict=就绪 但存在 %d 条 严重|高 finding" % len(blocking))]
    if str(verdict) == "未就绪" and not blocking:
        return [v("SET_MISMATCH", where + ".verdict",
                  "verdict=未就绪 但无 严重|高 finding（须至少 1 条）")]
    return []

def check_scope(record, where):
    violations = []
    scope = record.get("scope")
    if scope is None:
        return [v("EMPTY_FIELD", where + ".scope", "scope 缺失（实际清点到的文档）")]
    if not isinstance(scope, list) or not scope:
        return [v("EMPTY_FIELD", where + ".scope", "scope 须为非空列表")]
    seen = set()
    for i, name in enumerate(scope):
        if not nonempty(name):
            violations.append(v("EMPTY_FIELD", "%s.scope[%d]" % (where, i), "scope 项为空"))
        elif str(name) not in SCOPES:
            violations.append(v("ENUM_INVALID", "%s.scope[%d]" % (where, i),
                                "scope 越界：%s（合法集 %s）" % (name, "|".join(SCOPES))))
        elif str(name) in seen:
            violations.append(v("DUPLICATE_ID", "%s.scope[%d]" % (where, i),
                                "scope 项重复：%s" % name))
        else:
            seen.add(str(name))
    return violations

def check_record(index, record, final, where_base):
    violations = []
    where = "%s.checks[%d]" % (where_base, index)
    if not isinstance(record, dict):
        return [v("EMPTY_FIELD", where, "记录不是映射")], []

    rid = record.get("id")
    if not nonempty(rid):
        violations.append(v("EMPTY_FIELD", where + ".id", "id 缺失"))
    elif not IR_RE.fullmatch(str(rid)):
        violations.append(v("ENUM_INVALID", where + ".id",
                            "id 须为 IR-0nn（三位零填充），实为 %s" % rid))

    date = record.get("date")
    if not nonempty(date):
        violations.append(v("EMPTY_FIELD", where + ".date", "date 缺失"))
    elif not DATE_RE.fullmatch(str(date)):
        violations.append(v("ENUM_INVALID", where + ".date",
                            "date 须为 YYYY-MM-DD，实为 %s" % date))

    status = record.get("status")
    if not nonempty(status):
        violations.append(v("EMPTY_FIELD", where + ".status", "status 缺失"))
    elif str(status) not in RECORD_STATUSES:
        violations.append(v("ENUM_INVALID", where + ".status",
                            "status 越界：%s（合法集 %s）"
                            % (status, "|".join(RECORD_STATUSES))))

    verdict = record.get("verdict")
    if nonempty(verdict) and str(verdict) not in VERDICTS:
        violations.append(v("ENUM_INVALID", where + ".verdict",
                            "verdict 越界：%s（合法集 %s）"
                            % (verdict, "|".join(VERDICTS))))

    violations += check_scope(record, where)
    finding_violations, findings = check_findings(record, where, final)
    violations += finding_violations
    violations += check_verdict_findings(record, where, verdict, findings)
    violations += check_coverage(record, where, final)
    violations += check_counts(record, where, final, findings)

    if final:
        violations += check_final_duties(record, where, verdict, status)
    return violations, findings

def check_final_duties(record, where, verdict, status):
    """--final 附加义务：status 已落 已定稿、verdict 已定、零假设。"""
    violations = []
    if str(status) != "已定稿":
        violations.append(v("STATUS_MISMATCH", where + ".status",
                            "--final 要求 status 已落 已定稿（实为 %s）" % status))
    if not nonempty(verdict):
        violations.append(v("PENDING_DECISION", where + ".verdict",
                            "--final 要求 verdict 已定（就绪|有风险就绪|未就绪）"))
    if any("[假设]" in s for _p, s in walk_strings(record, "")):
        violations.append(v("ASSUMPTION_PRESENT", where,
                            "--final 要求零 [假设]；未决推断须先落定"))
    return violations

def cmd_check(args):
    root = os.path.abspath(args.project_root)
    out = os.path.abspath(args.output_dir)
    path = os.path.join(out, READINESS_FILE)
    show = display_path(path, root)
    violations = []
    warnings = []
    records = []

    data, err = load_yaml_safe(path)
    if data is None and err is None:
        violations.append(v("MISSING_FILE", show,
                            "%s 不存在（先完成一次 readiness 起草）" % READINESS_FILE))
    elif err is not None:
        violations.append(v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err))
    elif not isinstance(data, dict):
        violations.append(v("EMPTY_FIELD", show, "顶层不是映射（须为 project + checks）"))
    else:
        # project 形状 {name, created, updated}；状态挂记录级
        project = data.get("project")
        if project is not None and not isinstance(project, dict):
            violations.append(v("EMPTY_FIELD", show + " project", "project 不是映射"))
        revisions = data.get("revisions")
        if revisions is not None and not isinstance(revisions, list):
            violations.append(v("EMPTY_FIELD", show + " revisions", "revisions 不是列表"))
        raw_records = data.get("checks")
        if raw_records is None:
            violations.append(v("EMPTY_FIELD", show + " checks",
                                "checks 缺失（集合形态；无记录写空列表）"))
        elif not isinstance(raw_records, list):
            violations.append(v("EMPTY_FIELD", show + " checks", "checks 不是列表"))
        else:
            records = raw_records
            seen = set()
            for i, record in enumerate(records):
                record_violations, _ = check_record(i, record, args.final, show)
                violations += record_violations
                if isinstance(record, dict) and nonempty(record.get("id")):
                    rid = str(record["id"])
                    if rid in seen:
                        violations.append(v("DUPLICATE_ID", "%s.checks[%d].id" % (show, i),
                                            "记录 ID %s 重复（IR ID 稳定不重用）" % rid))
                    seen.add(rid)
            if args.final and not records:
                violations.append(v("EMPTY_FIELD", show + " checks",
                                    "--final 要求至少 1 条记录"))

    counts = {
        "checks": len(records),
        "by_verdict": count_by(records, "verdict"),
        "by_status": count_by(records, "status"),
        "findings": count_items(records, "findings"),
        "gaps": count_gaps(records),
    }
    ok = not violations
    payload = {
        "ok": ok,
        "command": "check",
        "project_root": args.project_root,
        "output_dir": os.path.normpath(out).replace("\\", "/"),
        "final": args.final,
        "violations": violations,
        "warnings": warnings,
        "counts": counts,
    }
    emit_via(payload, args.json, human_check)
    return 0 if ok else 1

def count_gaps(records):
    total = 0
    for record in records:
        coverage = record.get("coverage") if isinstance(record, dict) else None
        if isinstance(coverage, dict) and isinstance(coverage.get("gaps"), list):
            total += len(coverage["gaps"])
    return total

def human_check(payload):
    if payload["ok"]:
        print("PASS：%s 校验通过（checks=%d）"
              % (payload["output_dir"] + "/" + READINESS_FILE, payload["counts"]["checks"]))
        return
    print("FAIL：")
    for item in payload["violations"]:
        print("- %s %s: %s" % (item["code"], item["where"], item["msg"]))
