# -*- coding: utf-8 -*-
"""diy-cis-method 校验命令域：deliverable 键表检查、单记录 schema/枚举/同档校验与 check 总编排。."""

import os

import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import check_tokens, count_by, display_path, is_int, load_yaml_safe, nonempty, receipt_base, v, walk_strings  # noqa: E402

from cis_method_lib import ASSUMPTION_MARK, BRANCH_KEYS, BRANCH_STEPS, CIS_FILE, CM_RE, COMPLETED_STEPS, DATE_RE, INJECTION_KEYS, METHOD_ENUM, STATUS_ENUM, STEP_KEYS, emit, out_dir_or_violation  # noqa: E402

# ---------------------------------------------------------------- check

def check_deliverable(record, where, method, status, step):
    """`deliverable` 面：空态 / 分支必填键（按进度）/ 多余键（warning）。"""
    violations = []
    warnings = []
    deliverable = record.get("deliverable")
    if deliverable is None:
        deliverable = {}
    if not isinstance(deliverable, dict):
        return [v("EMPTY_FIELD", where + ".deliverable", "deliverable 不是映射")], warnings
    draft = str(status) == "草稿"
    if not deliverable and not draft:
        violations.append(v("EMPTY_FIELD", where + ".deliverable",
                            "deliverable 为空而 status: %s（草稿以外的记录须有内容键）" % status))
    if method not in STEP_KEYS:
        return violations, warnings
    if not draft:
        for index, key in enumerate(STEP_KEYS[method]):
            if index + 1 > (step if is_int(step) else 0):
                break
            if not nonempty(deliverable.get(key)):
                violations.append(v("EMPTY_FIELD", "%s.deliverable.%s" % (where, key),
                                    "缺 %s 第 %d 步的必填键（该步 <template-output> 首键）"
                                    % (method, index + 1)))
    for key in deliverable:
        if key in INJECTION_KEYS:
            # 注入项由模板首部/运行环境注入，不是任何 step 的产出（叙事分支的 agent_role /
            # agent_name 是 agent 线残留，diy 侧整裁）——落进 deliverable 即无源字段。
            warnings.append(v("ENUM_INVALID", "%s.deliverable.%s" % (where, key),
                              "%s 是注入项（非步骤产出，由模板首部/运行环境注入），"
                              "不得写进 deliverable" % key))
        elif key not in BRANCH_KEYS[method]:
            warnings.append(v("ENUM_INVALID", "%s.deliverable.%s" % (where, key),
                              "不在 %s 分支的模板键表内（模板键表为建议结构，非封闭集；"
                              "放行但请确认不是串分支）" % method))
    return violations, warnings

def check_record(index, record, final, show):
    """单条记录的 schema / 枚举 / 同档 / 键表 / 令牌检查。"""
    violations = []
    warnings = []
    where = "%s.sessions[%d]" % (show, index)
    if not isinstance(record, dict):
        return [v("EMPTY_FIELD", where, "记录不是映射")], warnings

    rid = record.get("id")
    if not nonempty(rid):
        violations.append(v("EMPTY_FIELD", where + ".id", "id 缺失"))
    elif not CM_RE.fullmatch(str(rid).strip()):
        violations.append(v("ENUM_INVALID", where + ".id",
                            "id 须为 CM-###（三位零填充），实为 %s" % rid))

    topic = record.get("topic")
    if not nonempty(topic):
        violations.append(v("EMPTY_FIELD", where + ".topic", "topic 为空（会话门禁要求议题在场）"))

    date = record.get("date")
    if not nonempty(date):
        violations.append(v("EMPTY_FIELD", where + ".date", "date 缺失"))
    elif not DATE_RE.fullmatch(str(date).strip()):
        violations.append(v("ENUM_INVALID", where + ".date",
                            "date 须为 YYYY-MM-DD，实为 %s" % date))

    method = record.get("method")
    method_ok = False
    if not nonempty(method):
        violations.append(v("EMPTY_FIELD", where + ".method", "method 缺失"))
    elif str(method).strip() not in METHOD_ENUM:
        violations.append(v("ENUM_INVALID", where + ".method",
                            "method 越界：%s（合法集 %s）" % (method, "|".join(METHOD_ENUM))))
    else:
        method = str(method).strip()
        method_ok = True

    status = record.get("status")
    status_ok = False
    if not nonempty(status):
        violations.append(v("EMPTY_FIELD", where + ".status", "status 缺失"))
    elif str(status).strip() not in STATUS_ENUM:
        violations.append(v("ENUM_INVALID", where + ".status",
                            "status 越界：%s（合法集 %s）"
                            % (status, "|".join(STATUS_ENUM))))
    else:
        status = str(status).strip()
        status_ok = True

    step = record.get("current_step")
    step_max = BRANCH_STEPS[method] if method_ok else max(BRANCH_STEPS.values())
    step_ok = False
    if not is_int(step):
        violations.append(v("ENUM_INVALID", where + ".current_step",
                            "current_step 须为整数，实为 %r" % (step,)))
    elif not (1 <= step <= step_max):
        violations.append(v("ENUM_INVALID", where + ".current_step",
                            "current_step 越界：%s（%s 合法集 1-%d）"
                            % (step, method if method_ok else "四分支并集", step_max)))
    else:
        step_ok = True

    if status_ok and step_ok and method_ok:
        if status == "草稿":
            legal = (1,)
        elif status == "进行中":
            legal = tuple(range(2, step_max))
        else:
            legal = COMPLETED_STEPS[method]
        if step not in legal:
            note = "（问题求解第 9 步 optional，跳过时第 8 步收尾）" if method == "问题求解" else ""
            violations.append(v("STATUS_MISMATCH", where + ".current_step",
                                "status: %s 要求 current_step ∈ %s，实为 %s%s（续接锚点必须"
                                "与会话阶段同档）"
                                % (status, "|".join(str(x) for x in legal), step, note)))

    deliverable_violations, deliverable_warnings = check_deliverable(
        record, where, method if method_ok else "", status, step)
    violations += deliverable_violations
    warnings += deliverable_warnings

    questions = record.get("open_questions")
    if questions is None:
        violations.append(v("EMPTY_FIELD", where + ".open_questions",
                            "open_questions 缺失（无内容写空列表）"))
    elif not isinstance(questions, list):
        violations.append(v("EMPTY_FIELD", where + ".open_questions",
                            "open_questions 不是列表"))
    else:
        for i, question in enumerate(questions):
            if not nonempty(question):
                violations.append(v("EMPTY_FIELD", "%s.open_questions[%d]" % (where, i),
                                    "条目为空"))

    violations += check_tokens(record, where)

    if final:
        if str(status) != "已完成":
            violations.append(v("STATUS_MISMATCH", where + ".status",
                                "--final 要求 status: 已完成，实为 %s（先走完本分支的步骤序列）"
                                % status))
        if any(ASSUMPTION_MARK in text for _p, text in walk_strings(record, "")):
            violations.append(v("ASSUMPTION_PRESENT", where,
                                "--final 要求零 [假设]；未决项写进 open_questions 再定稿"))
    return violations, warnings

def cmd_check(args):
    payload = receipt_base("check", args, args.output_dir)
    out, missing = out_dir_or_violation(payload, args, "check")
    if missing is not None:
        payload["violations"] = [missing]
        return emit(payload, args.json)
    root = os.path.abspath(args.project_root)
    path = os.path.join(out, CIS_FILE)
    show = display_path(path, root)
    violations = []
    warnings = []
    records = []
    data, err = load_yaml_safe(path)
    if data is None and err is None:
        violations.append(v("MISSING_FILE", show,
                            "%s 不存在（先跑 init 建会话记录）" % CIS_FILE))
    elif err is not None:
        violations.append(v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err))
    elif not isinstance(data, dict):
        violations.append(v("EMPTY_FIELD", show, "顶层不是映射（须为 project + sessions）"))
    else:
        project = data.get("project")
        if project is not None and not isinstance(project, dict):
            violations.append(v("EMPTY_FIELD", show + " project", "project 不是映射"))
        for key in ("name", "created", "updated"):
            if isinstance(project, dict) and not nonempty(project.get(key)):
                violations.append(v("EMPTY_FIELD", "%s.project.%s" % (show, key), "%s 为空" % key))
        revisions = data.get("revisions")
        if revisions is None:
            violations.append(v("EMPTY_FIELD", show + " revisions",
                                "revisions 缺失（无修订写空列表）"))
        elif not isinstance(revisions, list):
            violations.append(v("EMPTY_FIELD", show + " revisions", "revisions 不是列表"))
        raw = data.get("sessions")
        if raw is None:
            violations.append(v("EMPTY_FIELD", show + " sessions",
                                "sessions 缺失（集合形态；无记录写空列表）"))
        elif not isinstance(raw, list):
            violations.append(v("EMPTY_FIELD", show + " sessions", "sessions 不是列表"))
        else:
            records = raw
            seen = set()
            for i, record in enumerate(records):
                if isinstance(record, dict) and nonempty(record.get("id")):
                    rid = str(record["id"]).strip()
                    if rid in seen:
                        violations.append(v("DUPLICATE_ID", "%s.sessions[%d].id" % (show, i),
                                            "记录 ID %s 重复（CM ID 稳定不重用）" % rid))
                    seen.add(rid)
            target = str(args.id).strip() if nonempty(args.id) else None
            if target is not None and target not in seen:
                violations.append(v("UNKNOWN_ID", "check --id",
                                    "%s 不在 %s 的 sessions[] 内" % (target, show)))
            for i, record in enumerate(records):
                if target is not None and (not isinstance(record, dict)
                                           or str(record.get("id") or "").strip() != target):
                    continue
                record_violations, record_warnings = check_record(i, record, args.final, show)
                violations += record_violations
                warnings += record_warnings
            if args.final and not records:
                violations.append(v("EMPTY_FIELD", show + " sessions",
                                    "--final 要求至少 1 条会话记录（空集合不得冒充全部定稿）"))
    payload["ok"] = not violations
    payload["violations"] = violations
    payload["warnings"] = warnings
    payload["final"] = bool(args.final)
    payload["counts"] = {"sessions": len(records),
                         "by_method": count_by([r for r in records if isinstance(r, dict)
                                                and nonempty(r.get("method"))], "method"),
                         "by_status": count_by([r for r in records if isinstance(r, dict)
                                                and nonempty(r.get("status"))], "status")}
    return emit(payload, args.json,
                "PASS：%s 校验通过（sessions=%d；%s 必填键表 %d 键）"
                % (show, len(records), "四分支", sum(len(k) for k in STEP_KEYS.values())))
