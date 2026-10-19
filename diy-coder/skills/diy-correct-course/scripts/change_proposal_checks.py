# -*- coding: utf-8 -*-
"""diy-correct-course 引擎 check 命令域：CP 记录级校验族与 cmd_check/human_check 回执。."""

import os

import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import count_by, count_items, display_path, emit_via, load_yaml_safe, nonempty, v, walk_strings  # noqa: E402

from change_proposal_lib import APPROACH_PATHS, ARTIFACTS, CP_RE, DATE_RE, FINAL_STATUSES, KINDS, KNOWN_ROUTES, MODES, ROUTE_SETS, SCOPES, STATUSES, check_target  # noqa: E402

PROPOSAL_FILE = "change-proposal.yaml"

# ---------------------------------------------------------------- check

def check_id_date_status(record, where):
    violations = []
    rid = record.get("id")
    if not nonempty(rid):
        violations.append(v("EMPTY_FIELD", where + ".id", "id 缺失"))
    elif not CP_RE.fullmatch(str(rid)):
        violations.append(v("ENUM_INVALID", where + ".id",
                            "id 须为 CP-0nn（三位零填充），实为 %s" % rid))
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
    mode = record.get("mode")
    if not nonempty(mode):
        violations.append(v("EMPTY_FIELD", where + ".mode", "mode 缺失"))
    elif str(mode) not in MODES:
        violations.append(v("ENUM_INVALID", where + ".mode",
                            "mode 越界：%s（合法集 %s）" % (mode, "|".join(MODES))))
    if not nonempty(record.get("trigger")):
        violations.append(v("EMPTY_FIELD", where + ".trigger",
                            "trigger 缺失（触发问题的用户原话优先）"))
    return violations

def check_enum(value, allowed, where, label):
    """在场值的枚举校验（缺失由各调用点自行判空）。"""
    if nonempty(value) and str(value) not in allowed:
        return [v("ENUM_INVALID", where, "%s 越界：%s（合法集 %s）"
                  % (label, value, "|".join(allowed)))]
    return []

def check_impacts(record, where, final):
    violations = []
    impacts = record.get("impacts")
    if impacts is None:
        return [v("EMPTY_FIELD", where + ".impacts", "impacts 缺失（无影响写空列表）")]
    if not isinstance(impacts, list):
        return [v("EMPTY_FIELD", where + ".impacts", "impacts 不是列表")]
    if final and not impacts:
        violations.append(v("EMPTY_FIELD", where + ".impacts",
                            "--final 要求 impacts 非空（变更必影响至少一处）"))
    for i, impact in enumerate(impacts):
        iw = "%s.impacts[%d]" % (where, i)
        if not isinstance(impact, dict):
            violations.append(v("EMPTY_FIELD", iw, "impact 不是映射"))
            continue
        if not nonempty(impact.get("artifact")):
            violations.append(v("EMPTY_FIELD", iw + ".artifact", "artifact 缺失"))
        else:
            violations += check_enum(impact.get("artifact"), ARTIFACTS,
                                     iw + ".artifact", "artifact")
        violations += check_target(impact.get("artifact"), impact.get("target"),
                                   iw + ".target")
        if not nonempty(impact.get("kind")):
            violations.append(v("EMPTY_FIELD", iw + ".kind", "kind 缺失"))
        else:
            violations += check_enum(impact.get("kind"), KINDS, iw + ".kind", "kind")
        if not nonempty(impact.get("why")):
            violations.append(v("EMPTY_FIELD", iw + ".why", "why 为空（影响理由必须说明）"))
    return violations

def check_edits(record, where, final):
    violations = []
    edits = record.get("edits")
    if edits is None:
        return [v("EMPTY_FIELD", where + ".edits", "edits 缺失（无提案写空列表）")]
    if not isinstance(edits, list):
        return [v("EMPTY_FIELD", where + ".edits", "edits 不是列表")]
    if final and not edits:
        violations.append(v("EMPTY_FIELD", where + ".edits",
                            "--final 要求 edits 非空（提案须有具体改动）"))
    for i, edit in enumerate(edits):
        ew = "%s.edits[%d]" % (where, i)
        if not isinstance(edit, dict):
            violations.append(v("EMPTY_FIELD", ew, "edit 不是映射"))
            continue
        if not nonempty(edit.get("artifact")):
            violations.append(v("EMPTY_FIELD", ew + ".artifact", "artifact 缺失"))
        else:
            violations += check_enum(edit.get("artifact"), ARTIFACTS,
                                     ew + ".artifact", "artifact")
        violations += check_target(edit.get("artifact"), edit.get("target"),
                                   ew + ".target")
        if not nonempty(edit.get("field")):
            violations.append(v("EMPTY_FIELD", ew + ".field", "field 缺失（目标字段路径）"))
        old = edit.get("old")
        new = edit.get("new")
        if not nonempty(old):
            violations.append(v("EMPTY_FIELD", ew + ".old",
                                "old 为空（新增型也须写占位，如 (absent)）"))
        if not nonempty(new):
            violations.append(v("EMPTY_FIELD", ew + ".new", "new 为空"))
        if nonempty(old) and nonempty(new) and str(old) == str(new):
            violations.append(v("SET_MISMATCH", ew,
                                "old 与 new 相同：该提案没有实际改动"))
        if not nonempty(edit.get("rationale")):
            violations.append(v("EMPTY_FIELD", ew + ".rationale",
                                "rationale 为空（每处改动须有理由）"))
    return violations

def check_effort(record, where):
    effort = record.get("effort")
    if effort is None:
        return []
    if not isinstance(effort, dict):
        return [v("EMPTY_FIELD", where + ".effort", "effort 不是映射")]
    violations = []
    for key in ("estimate", "risk", "timeline_impact"):
        if not nonempty(effort.get(key)):
            violations.append(v("EMPTY_FIELD", "%s.effort.%s" % (where, key),
                                "%s 为空（effort 一旦在场须三键齐备）" % key))
    return violations

def check_approach(record, where, final):
    approach = record.get("approach")
    if approach is None:
        if final:
            return [v("PENDING_DECISION", where + ".approach",
                      "--final 要求路径已选定（直接调整|回滚|MVP 复审）")]
        return []
    if not isinstance(approach, dict):
        return [v("EMPTY_FIELD", where + ".approach", "approach 不是映射")]
    violations = []
    path = approach.get("path")
    if not nonempty(path):
        violations.append(v("EMPTY_FIELD", where + ".approach.path", "path 缺失"))
    else:
        violations += check_enum(path, APPROACH_PATHS, where + ".approach.path", "path")
    if not nonempty(approach.get("why")):
        violations.append(v("EMPTY_FIELD", where + ".approach.why",
                            "why 为空（路径选择须给理由）"))
    return violations

def check_handoff(record, where, final):
    handoff = record.get("handoff")
    if handoff is None:
        if final:
            return [v("EMPTY_FIELD", where + ".handoff",
                      "--final 要求 handoff 在场（route + note）")]
        return []
    if not isinstance(handoff, dict):
        return [v("EMPTY_FIELD", where + ".handoff", "handoff 不是映射")]
    violations = []
    route = handoff.get("route")
    if not nonempty(route):
        violations.append(v("EMPTY_FIELD", where + ".handoff.route",
                            "route 缺失（交接给哪个 diy 技能）"))
    elif str(route) not in KNOWN_ROUTES:
        violations.append(v("ENUM_INVALID", where + ".handoff.route",
                            "route 不在已知 diy 技能白名单：%s（合法集 %s）"
                            % (route, "|".join(KNOWN_ROUTES))))
    if not nonempty(handoff.get("note")):
        violations.append(v("EMPTY_FIELD", where + ".handoff.note",
                            "note 为空（交接说明必须写明）"))
    return violations

def check_list_field(record, key, where):
    value = record.get(key)
    if value is None:
        return []
    if not isinstance(value, list):
        return [v("EMPTY_FIELD", "%s.%s" % (where, key), "%s 不是列表" % key)]
    if any(not nonempty(item) for item in value):
        return [v("EMPTY_FIELD", "%s.%s" % (where, key), "%s 项不得为空" % key)]
    return []

def check_scope_route(record, where, scope, handoff):
    """scope 与 handoff.route 一致性（源 step-5 三级交接语义）。"""
    if not nonempty(scope) or str(scope) not in SCOPES:
        return []
    if not isinstance(handoff, dict):
        return []
    route = handoff.get("route")
    if not nonempty(route) or str(route) not in KNOWN_ROUTES:
        return []
    allowed = ROUTE_SETS[str(scope)]
    if str(route) not in allowed:
        return [v("SET_MISMATCH", where + ".handoff.route",
                  "scope=%s 的交接对象不匹配：%s（该级允许 %s）"
                  % (scope, route, "|".join(allowed)))]
    return []

def check_final_duties(record, where, status):
    """--final 附加义务：终态 status、零假设。"""
    violations = []
    if str(status) not in FINAL_STATUSES:
        violations.append(v("STATUS_MISMATCH", where + ".status",
                            "--final 要求 status ∈ {%s}（实为 %s）"
                            % ("|".join(FINAL_STATUSES), status)))
    if any("[假设]" in s for _p, s in walk_strings(record, "")):
        violations.append(v("ASSUMPTION_PRESENT", where,
                            "--final 要求零 [假设]；未决推断须先落定"))
    return violations

def check_record(index, record, final, where_base):
    violations = []
    where = "%s.proposals[%d]" % (where_base, index)
    if not isinstance(record, dict):
        return [v("EMPTY_FIELD", where, "记录不是映射")]
    violations += check_id_date_status(record, where)
    scope = record.get("scope")
    if not nonempty(scope):
        violations.append(v("EMPTY_FIELD", where + ".scope", "scope 缺失"))
    else:
        violations += check_enum(scope, SCOPES, where + ".scope", "scope")
    violations += check_impacts(record, where, final)
    violations += check_edits(record, where, final)
    violations += check_list_field(record, "ripple", where)
    violations += check_effort(record, where)
    violations += check_approach(record, where, final)
    violations += check_handoff(record, where, final)
    violations += check_list_field(record, "open_questions", where)
    if final:
        violations += check_final_duties(record, where, record.get("status"))
        violations += check_scope_route(record, where, scope, record.get("handoff"))
    return violations

def cmd_check(args):
    root = os.path.abspath(args.project_root)
    out = os.path.abspath(args.output_dir)
    path = os.path.join(out, PROPOSAL_FILE)
    show = display_path(path, root)
    violations = []
    warnings = []
    records = []
    matched = 0
    only = args.id

    if nonempty(only) and not CP_RE.fullmatch(str(only)):
        violations.append(v("ENUM_INVALID", show + " id",
                            "id 须为 CP-0nn（三位零填充），实为 %s" % only))

    data, err = load_yaml_safe(path)
    if data is None and err is None:
        violations.append(v("MISSING_FILE", show,
                            "%s 不存在（先完成一次提案起草）" % PROPOSAL_FILE))
    elif err is not None:
        violations.append(v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err))
    elif not isinstance(data, dict):
        violations.append(v("EMPTY_FIELD", show, "顶层不是映射（须为 project + proposals）"))
    else:
        project = data.get("project")
        if project is not None and not isinstance(project, dict):
            violations.append(v("EMPTY_FIELD", show + " project", "project 不是映射"))
        revisions = data.get("revisions")
        if revisions is not None and not isinstance(revisions, list):
            violations.append(v("EMPTY_FIELD", show + " revisions", "revisions 不是列表"))
        raw_records = data.get("proposals")
        if raw_records is None:
            violations.append(v("EMPTY_FIELD", show + " proposals",
                                "proposals 缺失（集合形态；无记录写空列表）"))
        elif not isinstance(raw_records, list):
            violations.append(v("EMPTY_FIELD", show + " proposals", "proposals 不是列表"))
        else:
            records = raw_records
            seen = set()
            for i, record in enumerate(records):
                rid = record.get("id") if isinstance(record, dict) else None
                if nonempty(only) and str(rid) != str(only):
                    continue
                matched += 1
                violations += check_record(i, record, args.final, show)
                if nonempty(rid):
                    if str(rid) in seen:
                        violations.append(v("DUPLICATE_ID", "%s.proposals[%d].id" % (show, i),
                                            "记录 ID %s 重复（CP ID 稳定不重用）" % rid))
                    seen.add(str(rid))
            if nonempty(only) and matched == 0:
                violations.append(v("UNKNOWN_ID", show + " proposals",
                                    "指定 ID %s 不存在" % only))
            if args.final and not records:
                violations.append(v("EMPTY_FIELD", show + " proposals",
                                    "--final 要求至少 1 条记录"))

    counts = {
        "proposals": len(records),
        "matched": matched,
        "by_status": count_by(records, "status"),
        "by_scope": count_by(records, "scope"),
        "by_mode": count_by(records, "mode"),
        "impacts": count_items(records, "impacts"),
        "edits": count_items(records, "edits"),
        "open_questions": count_items(records, "open_questions"),
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

def human_check(payload):
    if payload["ok"]:
        print("PASS：%s 校验通过（proposals=%d）"
              % (payload["output_dir"] + "/" + PROPOSAL_FILE, payload["counts"]["proposals"]))
        return
    print("FAIL：")
    for item in payload["violations"]:
        print("- %s %s: %s" % (item["code"], item["where"], item["msg"]))
