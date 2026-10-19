# -*- coding: utf-8 -*-
"""diy-investigate check 命令域：investigation.yaml 的枚举/ID/证据纪律校验、--final 定稿检与 check 回执。."""

import os

import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import count_by, count_items, display_path, emit_via, load_yaml_safe, nonempty, v, walk_strings  # noqa: E402

from investigation_lib import AVAILABILITIES, BACKLOG_PRIORITIES, BACKLOG_STATUSES, CONFIDENCES, DATE_RE, DOC_STATUSES, EV_RE, GRADES, HYPOTHESIS_STATUSES, H_RE, INPUT_KINDS, INVESTIGATION_FILE, IV_RE, MODES, RECORD_STATUSES, SLUG_RE, count_by_grade, count_open_hypotheses  # noqa: E402

# ---------------------------------------------------------------- check

def check_enum(value, allowed, where, label):
    if not nonempty(value):
        return [v("EMPTY_FIELD", where, "%s 缺失" % label)]
    if str(value) not in allowed:
        return [v("ENUM_INVALID", where, "%s 越界：%s（合法集 %s）"
                  % (label, value, "|".join(allowed)))]
    return []

def missing_field(mapping, key, where, label=None):
    """必填非空字段：缺失/空串 → EMPTY_FIELD。"""
    if nonempty(mapping.get(key)):
        return []
    return [v("EMPTY_FIELD", where + "." + key, "%s 缺失" % (label or key))]

def check_pattern(value, pattern, hint, where, label, seen=None):
    """格式锚点：缺失 → EMPTY_FIELD；越格式 → ENUM_INVALID；seen 给定时查记录内唯一。"""
    if not nonempty(value):
        return [v("EMPTY_FIELD", where, "%s 缺失" % label)]
    if not pattern.fullmatch(str(value)):
        return [v("ENUM_INVALID", where, "%s 须为 %s，实为 %s" % (label, hint, value))]
    if seen is not None:
        if str(value) in seen:
            return [v("DUPLICATE_ID", where, "%s 重复：%s" % (label, value))]
        seen.add(str(value))
    return []

def check_evidence(record, where):
    violations = []
    evidence = record.get("evidence")
    if evidence is None:
        return [v("EMPTY_FIELD", where + ".evidence",
                  "evidence 缺失（无证据写空列表——证据分级是本案核心）")]
    if not isinstance(evidence, list):
        return [v("EMPTY_FIELD", where + ".evidence", "evidence 不是列表")]
    seen = set()
    for i, ev in enumerate(evidence):
        ew = "%s.evidence[%d]" % (where, i)
        if not isinstance(ev, dict):
            violations.append(v("EMPTY_FIELD", ew, "evidence 项不是映射"))
            continue
        violations += check_pattern(ev.get("id"), EV_RE, "EV-0nn（三位零填充）",
                                    ew + ".id", "EV ID", seen)
        violations += check_enum(ev.get("grade"), GRADES, ew + ".grade", "grade")
        violations += check_enum(ev.get("availability"), AVAILABILITIES,
                                 ew + ".availability", "availability")
        violations += missing_field(ev, "ref", ew, "ref（path:line / timestamp / commit）")
        violations += missing_field(ev, "note", ew)
    return violations

def check_hypotheses(record, where):
    """假设生命周期：永不删除——状态转移必须带 Resolution（源纪律机械化）。"""
    violations = []
    hypotheses = record.get("hypotheses")
    if hypotheses is None:
        return [v("EMPTY_FIELD", where + ".hypotheses",
                  "hypotheses 缺失（无假设写空列表；假设永不删除）")]
    if not isinstance(hypotheses, list):
        return [v("EMPTY_FIELD", where + ".hypotheses", "hypotheses 不是列表")]
    seen = set()
    for i, hyp in enumerate(hypotheses):
        hw = "%s.hypotheses[%d]" % (where, i)
        if not isinstance(hyp, dict):
            violations.append(v("EMPTY_FIELD", hw, "hypotheses 项不是映射"))
            continue
        violations += check_pattern(hyp.get("id"), H_RE, "H-0nn（三位零填充）",
                                    hw + ".id", "H ID", seen)
        violations += missing_field(hyp, "statement", hw)
        status = hyp.get("status")
        violations += check_enum(status, HYPOTHESIS_STATUSES, hw + ".status", "status")
        if nonempty(status) and str(status) != "待验证":
            violations += missing_field(hyp, "resolution", hw, "resolution（何时/何证据结案）")
    return violations

def check_stronghold(record, where):
    """据点先行（源纪律）：evidence_light=false 的案件必须有据点。"""
    stronghold = record.get("stronghold")
    if stronghold is None:
        if record.get("evidence_light") is True:
            return []
        return [v("EMPTY_FIELD", where + ".stronghold",
                  "据点缺失（先锚一条「已确证」证据再外扩；无据案件须标记 evidence_light: true）")]
    if not isinstance(stronghold, dict):
        return [v("EMPTY_FIELD", where + ".stronghold", "stronghold 不是映射")]
    violations = missing_field(stronghold, "ref", where + ".stronghold",
                               "ref（path:line / timestamp / commit）")
    return violations + missing_field(stronghold, "why", where + ".stronghold")

def check_case_info(record, where):
    violations = []
    info = record.get("case_info")
    if info is None:
        return [v("EMPTY_FIELD", where + ".case_info",
                  "case_info 缺失（inputs / scope / time_window）")]
    if not isinstance(info, dict):
        return [v("EMPTY_FIELD", where + ".case_info", "case_info 不是映射")]
    inputs = info.get("inputs")
    if not isinstance(inputs, list) or not inputs:
        violations.append(v("EMPTY_FIELD", where + ".case_info.inputs",
                            "inputs 须为非空列表（输入形：工单/归档/日志/描述/范围/提交）"))
    else:
        for i, entry in enumerate(inputs):
            iw = "%s.case_info.inputs[%d]" % (where, i)
            if not isinstance(entry, dict):
                violations.append(v("EMPTY_FIELD", iw, "输入项不是映射"))
                continue
            violations += check_enum(entry.get("kind"), INPUT_KINDS, iw + ".kind", "kind")
            if not nonempty(entry.get("ref")):
                violations.append(v("EMPTY_FIELD", iw + ".ref", "输入 ref 缺失"))
    return violations

def check_timeline(record, where, final):
    violations = []
    timeline = record.get("timeline")
    if timeline is None:
        if final:
            violations.append(v("EMPTY_FIELD", where + ".timeline",
                                "--final 要求 timeline 非空（时间线重建是定稿前提）"))
        return violations
    if not isinstance(timeline, list):
        return [v("EMPTY_FIELD", where + ".timeline", "timeline 不是列表")]
    for i, entry in enumerate(timeline):
        tw = "%s.timeline[%d]" % (where, i)
        if not isinstance(entry, dict):
            violations.append(v("EMPTY_FIELD", tw, "时间线项不是映射"))
            continue
        violations += missing_field(entry, "at", tw)
        violations += missing_field(entry, "event", tw)
    if final and not timeline:
        violations.append(v("EMPTY_FIELD", where + ".timeline", "--final 要求 timeline 非空"))
    return violations

def check_backlog(record, where):
    violations = []
    backlog = record.get("backlog")
    if backlog is None:
        return violations
    if not isinstance(backlog, list):
        return [v("EMPTY_FIELD", where + ".backlog", "backlog 不是列表")]
    for i, entry in enumerate(backlog):
        bw = "%s.backlog[%d]" % (where, i)
        if not isinstance(entry, dict):
            violations.append(v("EMPTY_FIELD", bw, "backlog 项不是映射"))
            continue
        violations += missing_field(entry, "item", bw)
        violations += check_enum(entry.get("priority"), BACKLOG_PRIORITIES,
                                 bw + ".priority", "priority")
        violations += check_enum(entry.get("status"), BACKLOG_STATUSES, bw + ".status", "status")
    return violations

def check_missing_evidence(record, where):
    """缺失证据也是发现（源纪律）：evidence-light 案件必须记账缺失面。"""
    violations = []
    missing = record.get("missing_evidence")
    if missing is None:
        missing = []
    if not isinstance(missing, list):
        return [v("EMPTY_FIELD", where + ".missing_evidence", "missing_evidence 不是列表")]
    for i, entry in enumerate(missing):
        mw = "%s.missing_evidence[%d]" % (where, i)
        if not isinstance(entry, dict):
            violations.append(v("EMPTY_FIELD", mw, "缺失证据项不是映射"))
            continue
        violations += missing_field(entry, "what", mw)
        violations += missing_field(entry, "how", mw, "how（如何取得）")
        if entry.get("would_resolve") is not None and not nonempty(entry.get("would_resolve")):
            violations.append(v("EMPTY_FIELD", mw + ".would_resolve",
                                "would_resolve 出现时不得为空"))
    if record.get("evidence_light") is True and not missing:
        violations.append(v("EVIDENCE_MISSING", where + ".missing_evidence",
                            "evidence_light: true 案件须记缺失证据（what/would_resolve/how）——"
                            "缺失证据也是发现"))
    return violations

def check_note_entries(record, key, where, with_date=False):
    """追加式列表共用（follow_ups / side_findings）：条目映射 + note 必填；with_date 时 date 必填。"""
    entries = record.get(key)
    if entries is None:
        return []
    if not isinstance(entries, list):
        return [v("EMPTY_FIELD", "%s.%s" % (where, key), "%s 不是列表" % key)]
    violations = []
    for i, entry in enumerate(entries):
        ew = "%s.%s[%d]" % (where, key, i)
        if not isinstance(entry, dict):
            violations.append(v("EMPTY_FIELD", ew, "%s 项不是映射" % key))
            continue
        violations += missing_field(entry, "note", ew)
        if with_date:
            violations += check_pattern(entry.get("date"), DATE_RE, "YYYY-MM-DD",
                                        ew + ".date", "date")
    return violations

def check_conclusion(record, where, final):
    violations = []
    conclusion = record.get("conclusion")
    if conclusion is None:
        if final:
            violations.append(v("EMPTY_FIELD", where + ".conclusion",
                                "--final 要求 conclusion 在场（结论 + confidence）"))
        return violations
    if not isinstance(conclusion, dict):
        return [v("EMPTY_FIELD", where + ".conclusion", "conclusion 不是映射")]
    if final and not nonempty(conclusion.get("text")):
        violations.append(v("EMPTY_FIELD", where + ".conclusion.text",
                            "--final 要求结论文本非空"))
    confidence = conclusion.get("confidence")
    if not nonempty(confidence):
        if final:
            violations.append(v("PENDING_DECISION", where + ".conclusion.confidence",
                                "--final 要求 confidence 已定（高|中|低）"))
    elif str(confidence) not in CONFIDENCES:
        violations.append(v("ENUM_INVALID", where + ".conclusion.confidence",
                            "confidence 越界：%s（合法集 %s）"
                            % (confidence, "|".join(CONFIDENCES))))
    return violations

def check_final_duties(record, where):
    violations = []
    if not nonempty(record.get("handoff_brief")):
        violations.append(v("EMPTY_FIELD", where + ".handoff_brief",
                            "--final 要求 handoff_brief 非空（3 句、15 秒读完）"))
    if any("[假设]" in s for _p, s in walk_strings(record, "")):
        violations.append(v("ASSUMPTION_PRESENT", where,
                            "--final 要求零 [假设]；未决推断须先落定"))
    return violations

def check_record(index, record, final, where_base):
    violations = []
    where = "%s.cases[%d]" % (where_base, index)
    if not isinstance(record, dict):
        return [v("EMPTY_FIELD", where, "记录不是映射")]

    violations += check_pattern(record.get("id"), IV_RE, "IV-0nn（三位零填充）",
                                where + ".id", "id", set())
    violations += check_pattern(record.get("slug"), SLUG_RE, "小写字母数字连字符（kebab）",
                                where + ".slug", "slug")
    violations += check_pattern(record.get("date"), DATE_RE, "YYYY-MM-DD",
                                where + ".date", "date")
    violations += check_enum(record.get("status"), RECORD_STATUSES, where + ".status", "status")
    violations += check_enum(record.get("mode"), MODES, where + ".mode", "mode")
    light = record.get("evidence_light")
    if not isinstance(light, bool):
        violations.append(v("ENUM_INVALID", where + ".evidence_light",
                            "evidence_light 须为布尔（实为 %s）" % light))
    if not nonempty(record.get("problem_statement")):
        violations.append(v("EMPTY_FIELD", where + ".problem_statement",
                            "problem_statement 缺失（用户原述优先，作为假设待验证）"))

    violations += check_case_info(record, where)
    violations += check_stronghold(record, where)
    violations += check_evidence(record, where)
    violations += check_hypotheses(record, where)
    violations += check_timeline(record, where, final)
    violations += check_backlog(record, where)
    violations += check_missing_evidence(record, where)
    violations += check_conclusion(record, where, final)

    violations += check_note_entries(record, "follow_ups", where, with_date=True)
    violations += check_note_entries(record, "side_findings", where)

    if final:
        violations += check_final_duties(record, where)
    return violations

def cmd_check(args):
    root = os.path.abspath(args.project_root)
    out = os.path.abspath(args.output_dir)
    path = os.path.join(out, INVESTIGATION_FILE)
    show = display_path(path, root)
    violations = []
    warnings = []
    cases = []
    selected = None

    data, err = load_yaml_safe(path)
    if data is None and err is None:
        violations.append(v("MISSING_FILE", show,
                            "%s 不存在（先完成一次案件起草）" % INVESTIGATION_FILE))
    elif err is not None:
        violations.append(v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err))
    elif not isinstance(data, dict):
        violations.append(v("EMPTY_FIELD", show, "顶层不是映射（须为 project + cases）"))
    else:
        project = data.get("project")
        if project is not None and not isinstance(project, dict):
            violations.append(v("EMPTY_FIELD", show + " project", "project 不是映射"))
        status = project.get("status") if isinstance(project, dict) else None
        if nonempty(status) and str(status) not in DOC_STATUSES:
            violations.append(v("ENUM_INVALID", show + " project.status",
                                "status 越界：%s（合法集 %s）"
                                % (status, "|".join(DOC_STATUSES))))
        if args.final and str(status) != "已定稿":
            violations.append(v("STATUS_MISMATCH", show + " project.status",
                                "--final 要求 project.status 为「已定稿」（实为 %s）"
                                % (status if nonempty(status) else "未声明")))
        revisions = data.get("revisions")
        if revisions is not None and not isinstance(revisions, list):
            violations.append(v("EMPTY_FIELD", show + " revisions", "revisions 不是列表"))
        raw_cases = data.get("cases")
        if raw_cases is None:
            violations.append(v("EMPTY_FIELD", show + " cases",
                                "cases 缺失（集合形态；无记录写空列表）"))
        elif not isinstance(raw_cases, list):
            violations.append(v("EMPTY_FIELD", show + " cases", "cases 不是列表"))
        else:
            cases = raw_cases
            seen = set()
            for i, record in enumerate(cases):
                if isinstance(record, dict) and nonempty(record.get("id")):
                    rid = str(record["id"])
                    if rid in seen:
                        violations.append(v("DUPLICATE_ID", "%s.cases[%d].id" % (show, i),
                                            "记录 ID %s 重复（IV ID 稳定不重用）" % rid))
                    seen.add(rid)
            selected = None
            if nonempty(args.id):
                selected = [r for r in cases
                            if isinstance(r, dict) and str(r.get("id")) == str(args.id)]
                if not selected:
                    violations.append(v("UNKNOWN_ID", show + " cases[].id",
                                        "%s 不存在（--id 只校验已存在的案件）" % args.id))
            else:
                selected = cases
            for i, record in enumerate(cases):
                if selected is not None and record not in selected:
                    continue
                violations += check_record(i, record, args.final, show)
            if args.final and not selected:
                violations.append(v("EMPTY_FIELD", show + " cases",
                                    "--final 要求至少 1 条记录"))

    counts = {
        "cases": len(cases),
        "by_status": count_by(cases, "status"),
        "by_mode": count_by(cases, "mode"),
        "evidence": count_items(cases, "evidence"),
        "by_grade": count_by_grade(cases),
        "hypotheses": count_items(cases, "hypotheses"),
        "open_hypotheses": count_open_hypotheses(cases),
        "missing_evidence": count_items(cases, "missing_evidence"),
        "side_findings": count_items(cases, "side_findings"),
    }
    ok = not violations
    payload = {"ok": ok, "command": "check", "project_root": args.project_root,
               "output_dir": os.path.normpath(out).replace("\\", "/"),
               "final": args.final, "violations": violations, "warnings": warnings,
               "counts": counts}
    emit_via(payload, args.json, human_check)
    return 0 if ok else 1

def human_check(payload):
    if payload["ok"]:
        print("PASS：%s 校验通过（cases=%d）"
              % (payload["output_dir"] + "/" + INVESTIGATION_FILE,
                 payload["counts"]["cases"]))
        return
    print("FAIL：")
    for item in payload["violations"]:
        print("- %s %s: %s" % (item["code"], item["where"], item["msg"]))
