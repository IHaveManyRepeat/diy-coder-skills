# -*- coding: utf-8 -*-
"""diy-cis-method 读写命令域：list/show/methods 枚举与方法库呈现、init 骨架铸造。."""

import os
import random

import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import count_by, display_path, is_int, load_yaml_safe, next_record_id, nonempty, now, project_name, read_sessions, receipt_base, save_yaml_atomic, today, v  # noqa: E402

from cis_method_lib import CATEGORY_ENUM, CIS_FILE, CM_RE, METHODS_FILE, METHOD_ENUM, REACHABLE_CATEGORIES, emit, load_methods, out_dir_or_violation  # noqa: E402

# ---------------------------------------------------------------- list / show

def cmd_list(args):
    payload = receipt_base("list", args, args.output_dir)
    out, missing = out_dir_or_violation(payload, args, "list")
    if missing is not None:
        payload["violations"] = [missing]
        return emit(payload, args.json)
    root = os.path.abspath(args.project_root)
    path = os.path.join(out, CIS_FILE)
    show = display_path(path, root)
    records, violations, warnings = read_sessions(path, show)
    payload["violations"] = violations
    payload["warnings"] = warnings
    method = str(args.method).strip() if nonempty(args.method) else None
    if method is not None and method not in METHOD_ENUM:
        payload["violations"] = violations + [
            v("ENUM_INVALID", "list --method", "method 越界：%s（合法集 %s）"
              % (method, "|".join(METHOD_ENUM)))]
    sessions = []
    for rec in records or []:
        if not isinstance(rec, dict):
            continue
        if method is not None and str(rec.get("method") or "").strip() != method:
            continue
        sessions.append({"id": rec.get("id"), "method": rec.get("method"),
                         "topic": rec.get("topic"), "date": rec.get("date"),
                         "status": rec.get("status"), "current_step": rec.get("current_step")})
    payload["ok"] = not payload["violations"]
    payload["sessions"] = sessions
    payload["counts"] = {"sessions": len(sessions),
                         "by_status": count_by([{"k": s["status"]} for s in sessions
                                                if nonempty(s["status"])], "k")}
    body = ["- %s ｜ %s ｜ %s ｜ %s ｜ %s ｜ 第 %s 步"
            % (s["id"], s["method"], s["topic"], s["date"], s["status"], s["current_step"])
            for s in sessions]
    return emit(payload, args.json,
                "PASS：%s 记录 %d 条%s" % (show, len(sessions),
                                          "（产物缺席，按空列表处理）" if records is None else ""),
                body)

def cmd_show(args):
    payload = receipt_base("show", args, args.output_dir)
    out, missing = out_dir_or_violation(payload, args, "show")
    if missing is not None:
        payload["violations"] = [missing]
        return emit(payload, args.json)
    root = os.path.abspath(args.project_root)
    path = os.path.join(out, CIS_FILE)
    show = display_path(path, root)
    records, violations, warnings = read_sessions(path, show)
    payload["warnings"] = warnings
    target = str(args.id).strip()
    if not CM_RE.fullmatch(target):
        violations.append(v("ENUM_INVALID", "show --id",
                            "id 须为 CM-###（三位零填充），实为 %s" % target))
    found = None
    for rec in records or []:
        if isinstance(rec, dict) and str(rec.get("id") or "").strip() == target:
            found = rec
            break
    if found is None and not violations:
        violations.append(v("UNKNOWN_ID", "show --id",
                            "%s 不在 %s 的 sessions[] 内" % (target, show)))
    payload["violations"] = violations
    payload["ok"] = not violations
    payload["session"] = found
    payload["counts"] = {"sessions": len(records or [])}
    return emit(payload, args.json,
                "PASS：%s 记录 %s（%s / %s）" % (show, target, (found or {}).get("method"),
                                               (found or {}).get("status")))

# ---------------------------------------------------------------- methods

def cmd_methods(args):
    payload = receipt_base("methods", args, args.output_dir)
    root = os.path.abspath(args.project_root)
    method = str(args.method).strip() if nonempty(args.method) else ""
    if not method:
        payload["violations"] = [v("EMPTY_FIELD", "methods --method",
                                   "--method 必填（四条分支：%s）" % "|".join(METHOD_ENUM))]
        payload["counts"] = {"methods": 0, "library": 0}
        return emit(payload, args.json)
    if method not in METHOD_ENUM:
        payload["violations"] = [v("ENUM_INVALID", "methods --method",
                                   "method 越界：%s（合法集 %s）"
                                   % (method, "|".join(METHOD_ENUM)))]
        payload["counts"] = {"methods": 0, "library": 0}
        return emit(payload, args.json)
    rows, violations = load_methods(root)
    if violations:
        payload["violations"] = violations
        payload["counts"] = {"methods": 0, "library": 0}
        return emit(payload, args.json)
    method_rows = [row for row in rows if row["method"] == method]
    if not method_rows:
        payload["violations"] = [v("EMPTY_FIELD", METHODS_FILE,
                                   "库内无 %s 分支的条目" % method)]
        payload["counts"] = {"methods": 0, "library": len(rows)}
        return emit(payload, args.json)
    warnings = []
    # 默认集 = 该分支工作流实际接入的类（可达集）；--all = 该 method 全部条目（不跨分支）
    picked = list(method_rows) if args.all else [
        row for row in method_rows if row["category"] in REACHABLE_CATEGORIES[method]]
    if args.category is not None:
        category = str(args.category).strip()
        if category not in CATEGORY_ENUM[method]:
            payload["violations"] = [v("ENUM_INVALID", "methods --category",
                                       "category 越界：%s（%s 的合法类名 %s）"
                                       % (category, method, "|".join(CATEGORY_ENUM[method])))]
            payload["counts"] = {"methods": 0, "library": len(rows)}
            return emit(payload, args.json)
        picked = [row for row in picked if row["category"] == category]
        if not picked and category not in REACHABLE_CATEGORIES[method] and not args.all:
            warnings.append(v("ENUM_INVALID", "methods --category",
                              "「%s」类不在 %s 的默认可达集（源侧工作流未接入该类）；"
                              "加 --all 可见其全部条目" % (category, method)))
    if args.random is not None:
        if not is_int(args.random) or args.random < 1:
            payload["violations"] = [v("ENUM_INVALID", "methods --random",
                                       "抽样条数须为正整数，实为 %s" % args.random)]
            payload["counts"] = {"methods": 0, "library": len(rows)}
            return emit(payload, args.json)
        if args.random > len(picked):
            warnings.append(v("ENUM_INVALID", "methods --random",
                              "请求 %d 条超出结果集 %d 条，按全部返回"
                              % (args.random, len(picked))))
        else:
            picked = random.sample(picked, args.random)
    payload["ok"] = True
    payload["warnings"] = warnings
    payload["methods"] = picked
    payload["counts"] = {"methods": len(picked), "library": len(rows),
                         "branch": len(method_rows),
                         "by_category": count_by(picked, "category")}
    return emit(payload, args.json,
                "PASS：方法库 %d 条；%s 本次返回 %d 条（%s）"
                % (len(rows), method, len(picked), "--all 全分支" if args.all else "默认可达集"),
                ["- [%s] %s：%s" % (row["category"], row["name"], row["description"])
                 for row in picked])

# ---------------------------------------------------------------- init

def blank_document(project_root, stamp):
    """新建产物骨架：project 三键 + 空集合 + 空 revisions。"""
    name, warning = project_name(project_root)
    doc = {"project": {"name": name, "created": stamp, "updated": stamp},
           "sessions": [], "revisions": []}
    return doc, ([warning] if warning else [])

def new_record(record_id, method, topic, stamp):
    """记录骨架：内容型字段全给空位（`deliverable` / `open_questions` 由会话逐步编辑）。"""
    return {"id": record_id, "method": method, "topic": topic, "date": stamp,
            "status": "草稿", "current_step": 1, "deliverable": {}, "open_questions": []}

def cmd_init(args):
    payload = receipt_base("init", args, args.output_dir)
    out = os.path.abspath(args.output_dir)
    root = os.path.abspath(args.project_root)
    path = os.path.join(out, CIS_FILE)
    show = display_path(path, root)
    method = str(args.method).strip()
    topic = str(args.topic).strip()
    violations = []
    if method not in METHOD_ENUM:
        violations.append(v("ENUM_INVALID", "init --method",
                            "method 越界：%s（合法集 %s）" % (method, "|".join(METHOD_ENUM))))
    if not nonempty(topic):
        violations.append(v("EMPTY_FIELD", "init --topic",
                            "议题为空（门禁：无议题零产出停止，不代拟议题）"))
    if violations:
        payload["violations"] = violations
        return emit(payload, args.json)
    stamp = now()
    data, err = load_yaml_safe(path)
    if err is not None:
        payload["violations"] = [v("UNPARSABLE_YAML", show,
                                   "YAML 解析失败：%s（拒绝且零写入——修好或另行归档后再 init）" % err)]
        return emit(payload, args.json)
    if data is None:
        doc, warnings = blank_document(root, stamp)
        payload["warnings"] = warnings
    elif not isinstance(data, dict):
        payload["violations"] = [v("EMPTY_FIELD", show, "顶层不是映射（须为 project + sessions）")]
        return emit(payload, args.json)
    else:
        sessions = data.get("sessions")
        if sessions is None:
            sessions = []
        if not isinstance(sessions, list):
            payload["violations"] = [v("EMPTY_FIELD", show + " sessions",
                                       "sessions 不是列表（拒绝且零写入）")]
            return emit(payload, args.json)
        doc = data
        project = doc.get("project")
        if not isinstance(project, dict):
            project = {}
        warnings = []
        name = project.get("name")
        if not nonempty(name):
            name, warning = project_name(root)
            if warning is not None:
                warnings.append(warning)
        doc["project"] = {"name": name,
                          "created": project.get("created") if nonempty(project.get("created"))
                          else stamp,
                          "updated": stamp}
        doc["sessions"] = sessions
        doc.setdefault("revisions", [])
        payload["warnings"] = warnings
    record_id = next_record_id(doc.get("sessions") or [], CM_RE, "CM")
    record = new_record(record_id, method, topic, today())
    doc["sessions"] = list(doc.get("sessions") or []) + [record]
    try:
        if out:
            os.makedirs(out, exist_ok=True)
        save_yaml_atomic(path, doc)
    except OSError as e:
        payload["violations"] = [v("MISSING_FILE", show, "写盘失败：%s" % e)]
        return emit(payload, args.json)
    payload["ok"] = True
    payload["updated"] = stamp
    payload["id"] = record_id
    payload["counts"] = {"sessions": len(doc["sessions"]), "next_id": record_id}
    return emit(payload, args.json,
                "PASS：已建会话记录 %s（%s / status: 草稿 / current_step: 1），产物共 %d 条记录"
                % (record_id, method, len(doc["sessions"])))
