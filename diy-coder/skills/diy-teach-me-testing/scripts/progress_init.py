# -*- coding: utf-8 -*-
"""diy-teach-me-testing init/status 命令域：空白进度骨架、损坏恢复（--recover）、仪表盘与 entry_step 分流直出。."""

import os

import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import display_path, emit_via, is_int, load_yaml_safe, nonempty, now, project_name, receipt_base, save_yaml_atomic, v  # noqa: E402

from progress_checks import validate  # noqa: E402

from progress_lib import ENTRY_ASSESS, ENTRY_COMPLETION, ENTRY_HUB, ENTRY_INIT, LEARNER_FIELDS, NOTES_DIR, PROGRESS_FILE, RECOVERY_HINT, ROLE_ENUM, backup_progress, compute_derived, curriculum_index, load_curriculum, print_human_tail, progress_damage  # noqa: E402

# ---------------------------------------------------------------- init

# trace: B3 diy-teach-me-testing 空白进度骨架（7 节全未开始；派生字段由引擎写）
def blank_progress(curriculum, name, role):
    stamp = now()
    index_by_id = curriculum_index(curriculum)
    sessions = []
    for sid in sorted(index_by_id):
        definition = index_by_id[sid]
        sessions.append({
            "id": sid,
            "name": definition["name"],
            "duration_min": definition.get("duration_min"),
            "status": "未开始",
            "started_date": None,
            "completed_date": None,
            "score": None,
            "topics_explored": None,
            "notes": None,
        })
    completed, percentage, next_recommended = compute_derived(sorted(index_by_id), sessions)
    return {
        "project": {"name": name, "created": stamp, "updated": stamp},
        "learner": {"role": role, "experience": None, "goals": [], "pain_points": [],
                    "assessed": None},
        "sessions": sessions,
        "sessions_completed": completed,
        "completion_percentage": percentage,
        "next_recommended": next_recommended,
        "summary": {"generated": False, "path": None, "date": None},
        "revisions": [],
    }

# trace: B3 diy-teach-me-testing init 子命令（建 7 节 + notes/ 目录；已存在 → ALREADY_EXISTS；
# T-6 损坏件 → 报错指路，带 --recover 才「备份 + 重建」）
def cmd_init(args):
    root = os.path.abspath(args.project_root)
    out = os.path.abspath(args.output_dir)
    path = os.path.join(out, PROGRESS_FILE)
    show = display_path(path, root)
    payload = receipt_base("init", args, out)
    curriculum, cv = load_curriculum(root)
    if cv:
        payload["violations"] = cv
        emit_via(payload, args.json, human_init)
        return 1
    role = args.role
    if role is not None and str(role) not in ROLE_ENUM:
        payload["violations"] = [v("ENUM_INVALID", "init --role",
                                   "role 越界：%s（合法集 %s）"
                                   % (role, "|".join(ROLE_ENUM)))]
        emit_via(payload, args.json, human_init)
        return 1
    backup = None
    if os.path.exists(path):
        damage = progress_damage(path)
        if damage is None:
            payload["violations"] = [
                v("ALREADY_EXISTS", show,
                  "进度文件已存在 → 走 resume：先跑 status 拿分流，"
                  "禁止覆盖重建（断点即进度，覆盖等于抹掉学习历史）")]
            emit_via(payload, args.json, human_init)
            return 1
        if not args.recover:
            payload["violations"] = [v(damage[0], show, damage[1] + RECOVERY_HINT)]
            emit_via(payload, args.json, human_init)
            return 1
        try:
            backup = backup_progress(path)
        except OSError as e:
            payload["violations"] = [v("TOOL_ERROR", show, "备份损坏件失败（零写入）：%s" % e)]
            emit_via(payload, args.json, human_init)
            return 1
    name, warning = project_name(root)
    doc = blank_progress(curriculum, name, role)
    try:
        os.makedirs(os.path.join(out, NOTES_DIR), exist_ok=True)
        save_yaml_atomic(path, doc)
    except OSError as e:
        payload["violations"] = [v("TOOL_ERROR", show, "写盘失败：%s" % e)]
        emit_via(payload, args.json, human_init)
        return 1
    if backup is not None:
        payload["recovered"] = {"backup": display_path(backup, root)}
    if warning is not None:
        payload["warnings"] = [warning]
    payload["ok"] = True
    payload["updated"] = doc["project"]["updated"]
    payload["counts"] = {"sessions": len(doc["sessions"]),
                         "sessions_completed": doc["sessions_completed"],
                         "completion_percentage": doc["completion_percentage"]}
    emit_via(payload, args.json, human_init)
    return 0

# trace: B3 diy-teach-me-testing init 人读态（恢复路径额外播报备份路径）
def human_init(payload):
    if payload["ok"]:
        print("PASS：学习进度已建立 %s（%d 节全未开始 + notes/ 目录）"
              % (payload["output_dir"] + "/" + PROGRESS_FILE,
                 payload["counts"]["sessions"]))
        if payload.get("recovered"):
            print("已从损坏件恢复：原文件备份在 %s（笔记 md 未受影响）"
                  % payload["recovered"]["backup"])
    print_human_tail(payload)

# ---------------------------------------------------------------- status

# trace: B3 diy-teach-me-testing 分流表直出（裁定 3 唯一入口；判定输入 = 本回执；
# T-6：文件缺席与文件不可用一律回 init 步——恢复的唯一出口在那里）
def entry_step(present, data):
    if not present or not isinstance(data, dict):
        return ENTRY_INIT
    learner = data.get("learner")
    assessed = learner.get("assessed") if isinstance(learner, dict) else None
    if not nonempty(assessed):
        return ENTRY_ASSESS
    completed = data.get("sessions_completed")
    summary = data.get("summary")
    generated = summary.get("generated") if isinstance(summary, dict) else None
    if not is_int(completed) or completed < 7:
        return ENTRY_HUB
    return ENTRY_HUB if generated is True else ENTRY_COMPLETION

# trace: B3 diy-teach-me-testing 仪表盘数据（每节状态 / 下一个推荐 / 完成度；供 Hub 与分流）
def dashboard(data):
    sessions = data.get("sessions") if isinstance(data.get("sessions"), list) else []
    rows = []
    for session in sessions:
        if not isinstance(session, dict):
            continue
        rows.append({key: session.get(key) for key in
                     ("id", "name", "status", "score", "started_date",
                      "completed_date", "topics_explored", "notes")})
    learner = data.get("learner") if isinstance(data.get("learner"), dict) else {}
    summary = data.get("summary") if isinstance(data.get("summary"), dict) else {}
    return {
        "learner": {key: learner.get(key) for key in LEARNER_FIELDS},
        "sessions": rows,
        "sessions_completed": data.get("sessions_completed"),
        "completion_percentage": data.get("completion_percentage"),
        "next_recommended": data.get("next_recommended"),
        "summary": {"generated": summary.get("generated"),
                    "path": summary.get("path"), "date": summary.get("date")},
    }

# trace: B3 diy-teach-me-testing status 子命令（读 + 校验 + 仪表盘 + 分流；只读命令）
def cmd_status(args):
    root = os.path.abspath(args.project_root)
    out = os.path.abspath(args.output_dir)
    path = os.path.join(out, PROGRESS_FILE)
    show = display_path(path, root)
    payload = receipt_base("status", args, out)
    curriculum, cv = load_curriculum(root)
    if cv:
        payload["violations"] = cv
        payload["entry_step"] = None
        payload["dashboard"] = dashboard({})
        emit_via(payload, args.json, human_status)
        return 1
    if not os.path.isfile(path):
        payload["violations"] = [v("MISSING_FILE", show,
                                   "进度文件不存在 → 先 init 建进度（零 mtime 覆盖）")]
        payload["entry_step"] = ENTRY_INIT
        payload["dashboard"] = dashboard({})
        emit_via(payload, args.json, human_status)
        return 1
    damage = progress_damage(path)
    if damage is not None:
        payload["violations"] = [v(damage[0], show, damage[1] + RECOVERY_HINT)]
        payload["entry_step"] = ENTRY_INIT
        payload["dashboard"] = dashboard({})
        emit_via(payload, args.json, human_status)
        return 1
    data, _ = load_yaml_safe(path)          # damage 已判过：此处必为 dict + sessions 列表
    violations, (completed, percentage, next_recommended) = validate(
        data, curriculum, show, out, root)
    payload["violations"] = violations
    payload["entry_step"] = entry_step(True, data)
    payload["dashboard"] = dashboard(data)
    payload["counts"] = {"sessions": len(curriculum["sessions"]),
                         "sessions_completed": completed,
                         "completion_percentage": percentage}
    payload["ok"] = not violations
    emit_via(payload, args.json, human_status)
    return 0 if payload["ok"] else 1

# trace: B3 diy-teach-me-testing status 人读态（进度概览 + 逐节 + 推荐）
def human_status(payload):
    if payload["ok"]:
        dash = payload["dashboard"]
        print("进度 %s%%（%s / 7 节完成）· 下一个推荐：%s"
              % (dash["completion_percentage"], dash["sessions_completed"],
                 dash["next_recommended"]))
        for row in dash["sessions"]:
            mark = {"已完成": "[完成]", "进行中": "[进行]"}.get(row["status"],
                                                                   "[未开始]")
            print("- %s session %s %s（%s）"
                  % (mark, row["id"], row["name"], row["status"]))
        print("分流：%s" % payload["entry_step"])
    print_human_tail(payload)
