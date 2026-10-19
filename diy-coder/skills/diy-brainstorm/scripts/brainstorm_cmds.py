# -*- coding: utf-8 -*-
"""diy-brainstorm 读写命令域：list 会话列举、techniques 技术库呈现、init 记录骨架铸造。."""

import os

import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import count_by, display_path, is_int, load_yaml_safe, next_record_id, nonempty, now, project_name, read_sessions, receipt_base, save_yaml_atomic, today, v  # noqa: E402

from brainstorm_checks import DEFAULT_CANDIDATES  # noqa: E402

from brainstorm_lib import BRAINSTORM_FILE, BS_RE, emit, library_categories, load_methods, sample_cross_category  # noqa: E402

# ---- list ----

def cmd_list(args):
    root = os.path.abspath(args.project_root)
    out = os.path.abspath(args.output_dir)
    path = os.path.join(out, BRAINSTORM_FILE)
    show = display_path(path, root)
    payload = receipt_base("list", args, out)
    records, violations, warnings = read_sessions(path, show)
    payload["violations"] = violations
    payload["warnings"] = warnings
    sessions = []
    for rec in records or []:
        if not isinstance(rec, dict):
            continue
        sessions.append({"id": rec.get("id"), "topic": rec.get("topic"),
                         "date": rec.get("date"), "status": rec.get("status"),
                         "current_step": rec.get("current_step")})
    payload["ok"] = not violations
    payload["sessions"] = sessions
    payload["counts"] = {"sessions": len(sessions),
                         "by_status": count_by(
                             [{"k": s["status"]} for s in sessions if nonempty(s["status"])],
                             "k")}
    return emit(payload, args.json,
                "PASS：%s 记录 %d 条%s" % (show, len(sessions),
                                          "（产物缺席，按空列表处理）" if records is None else ""))

# ---- techniques ----

def cmd_techniques(args):
    root = os.path.abspath(args.project_root)
    out = os.path.abspath(args.output_dir)
    payload = receipt_base("techniques", args, out)
    rows, violations = load_methods(root)
    if violations:
        payload["violations"] = violations
        payload["counts"] = {"techniques": 0, "library": 0}
        return emit(payload, args.json)
    categories = library_categories(rows)
    picked = []
    if args.all:
        picked = list(rows)
    elif args.category is not None:
        if str(args.category) not in categories:
            payload["violations"] = [v("ENUM_INVALID", "techniques --category",
                                       "category 越界：%s（合法集 %s）"
                                       % (args.category, "|".join(categories)))]
            payload["counts"] = {"techniques": 0, "library": len(rows)}
            return emit(payload, args.json)
        picked = [row for row in rows if row["category"] == str(args.category)]
    else:
        count = args.random if args.random is not None else DEFAULT_CANDIDATES
        if not is_int(count) or count < 1:
            payload["violations"] = [v("ENUM_INVALID", "techniques --random",
                                       "抽样条数须为正整数，实为 %s" % args.random)]
            payload["counts"] = {"techniques": 0, "library": len(rows)}
            return emit(payload, args.json)
        if count > len(rows):
            payload["warnings"] = [v("ENUM_INVALID", "techniques --random",
                                     "请求 %d 条超出库容量 %d，按全库返回" % (count, len(rows)))]
            picked = list(rows)
        else:
            picked = sample_cross_category(rows, count)
    payload["ok"] = True
    payload["techniques"] = picked
    payload["counts"] = {"techniques": len(picked), "library": len(rows),
                         "by_category": count_by(picked, "category"),
                         "categories": len(categories)}
    return emit(payload, args.json,
                "PASS：技术库 %d 条 / %d 类，本次返回 %d 条"
                % (len(rows), len(categories), len(picked)))

# ---- init ----

def blank_document(project_root, stamp):
    """新建产物骨架：project 三键 + 空集合 + 空 revisions。"""
    name, warning = project_name(project_root)
    doc = {"project": {"name": name, "created": stamp, "updated": stamp},
           "sessions": [], "revisions": []}
    return doc, ([warning] if warning else [])

def new_record(record_id, topic, goals, stamp):
    """会话记录骨架：结论性字段全给空位，内容面由会话（LLM）直接编辑。"""
    return {"id": record_id, "topic": topic, "goals": goals or "", "approach": "",
            "date": stamp, "status": "草稿", "current_step": 1,
            "techniques": [], "ideas": [], "themes": [],
            "priorities": {"top": [], "quick_wins": [], "breakthroughs": []},
            "actions": [], "open_questions": []}

def cmd_init(args):
    root = os.path.abspath(args.project_root)
    out = os.path.abspath(args.output_dir)
    path = os.path.join(out, BRAINSTORM_FILE)
    show = display_path(path, root)
    payload = receipt_base("init", args, out)
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
        name = project.get("name")
        warnings = []
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
    record_id = next_record_id(doc.get("sessions") or [], BS_RE, "BS")
    record = new_record(record_id, args.topic, args.goals, today())
    doc["sessions"] = list(doc.get("sessions") or []) + [record]
    try:
        if out:
            os.makedirs(out, exist_ok=True)
        save_yaml_atomic(path, doc)
    except OSError as e:
        payload["violations"] = [v("TOOL_ERROR", show, "写盘失败：%s" % e)]
        return emit(payload, args.json)
    payload["ok"] = True
    payload["updated"] = stamp
    payload["id"] = record_id
    payload["counts"] = {"sessions": len(doc["sessions"]), "next_id": record_id}
    return emit(payload, args.json,
                "PASS：已建会话记录 %s（status: 草稿 / current_step: 1），"
                "产物共 %d 条记录" % (record_id, len(doc["sessions"])))
