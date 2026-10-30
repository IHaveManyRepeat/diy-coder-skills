# -*- coding: utf-8 -*-
"""diy-teach-me-testing update/check 命令域：--session/--learner/--summary 三形态唯一写通道、写前同源校验与门禁 check [--final]。."""

import os

import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import display_path, emit_via, is_int, load_yaml_safe, now, receipt_base, save_yaml_atomic, today, v  # noqa: E402

from progress_checks import notes_path_problem, validate  # noqa: E402

from progress_lib import EXPERIENCE_ENUM, PROGRESS_FILE, RECOVERY_HINT, ROLE_ENUM, STATUS_ENUM, SUMMARY_FILE, compute_derived, curriculum_index, load_curriculum, print_human_tail, progress_damage  # noqa: E402

# ---------------------------------------------------------------- update

# trace: update --session 归一化（路径口径 + 文件在场）
def resolve_notes(value, session_id, out_dir, out_show):
    text = str(value)
    if os.path.isabs(text):
        rel = os.path.relpath(os.path.abspath(text), out_dir)
        text = rel.replace("\\", "/")
    problem = notes_path_problem(text, session_id)
    if problem:
        return None, [v("ENUM_INVALID", "update --session %d --notes" % session_id,
                        "notes 路径违例：%s（实为 %s；固定命名 notes/session-<NN>.md）"
                        % (problem, value))]
    if not os.path.isfile(os.path.join(out_dir, text.replace("/", os.sep))):
        return None, [v("MISSING_FILE", "update --session %d --notes" % session_id,
                        "%s/%s 不在场（先落笔记 md 再写回）" % (out_show, text))]
    return text, []

# trace: update --session 主干（幂等 upsert + 重做修订）
def apply_session(args, data, index_by_id, out_dir, out_show):
    sid = args.session
    if sid not in index_by_id:
        return None, None, [v("UNKNOWN_ID", "update --session %d" % sid,
                              "session id 须为课程集合内的整数：%s"
                              % "|".join(str(i) for i in sorted(index_by_id)))]
    row = None
    row_index = None
    for i, item in enumerate(data["sessions"]):
        if isinstance(item, dict) and item.get("id") == sid:
            row, row_index = item, i
            break
    if row is None:
        return None, None, [v("SET_MISMATCH", "update --session %d" % sid,
                              "进度文件缺 session %d 行"
                              "（session id 集合须与 curriculum.yaml 一致）" % sid)]
    violations = []
    exploratory = index_by_id[sid].get("min_topics") is not None
    if args.status is not None and str(args.status) not in STATUS_ENUM:
        violations.append(v("ENUM_INVALID", "update --session %d --status" % sid,
                            "status 越界：%s（合法集 %s）"
                            % (args.status, "|".join(STATUS_ENUM))))
        return None, None, violations
    status = args.status if args.status is not None else row.get("status")
    if args.score is not None:
        if exploratory:
            violations.append(v("STATUS_MISMATCH", "update --session %d --score" % sid,
                                "session %d 无 quiz：score 恒 null（不参与平均分）" % sid))
        elif status != "已完成":
            violations.append(v("STATUS_MISMATCH", "update --session %d --score" % sid,
                                "--score 仅在 --status 已完成 时接受（当前 %s）" % status))
        elif not is_int(args.score) or not 0 <= args.score <= 100:
            violations.append(v("ENUM_INVALID", "update --session %d --score" % sid,
                                "score 须为 0-100 整数，实为 %s" % args.score))
    if args.topics is not None:
        if not exploratory:
            violations.append(v("ENUM_INVALID", "update --session %d --topics" % sid,
                                "topics_explored 仅探索型课次（session 7）非空"
                                "（探索主题计数）"))
        elif not is_int(args.topics) or args.topics < 0:
            violations.append(v("ENUM_INVALID", "update --session %d --topics" % sid,
                                "topics_explored 须为非负整数，实为 %s" % args.topics))
    notes = None
    if args.notes is not None:
        notes, notes_violations = resolve_notes(args.notes, sid, out_dir, out_show)
        violations += notes_violations
    if violations:
        return None, None, violations

    stamp = today()
    updated = dict(row)
    updated["status"] = status
    if status == "已完成":
        updated["started_date"] = row.get("started_date") or stamp
        updated["completed_date"] = stamp
        if args.score is not None:
            updated["score"] = args.score
        if notes is not None:
            updated["notes"] = notes
    elif status == "进行中":
        updated["started_date"] = row.get("started_date") or stamp
        updated["completed_date"] = None
        updated["score"] = None
        if notes is not None:
            updated["notes"] = notes
    else:
        updated["started_date"] = None
        updated["completed_date"] = None
        updated["score"] = None
        if notes is not None:
            updated["notes"] = notes
    if exploratory and args.topics is not None:
        updated["topics_explored"] = args.topics

    redo = row.get("status") == "已完成" and status == "已完成"
    sessions = [dict(item) for item in data["sessions"]]
    sessions[row_index] = updated
    new_data = dict(data)
    new_data["sessions"] = sessions
    if redo:
        new_data["revisions"] = list(data.get("revisions") or []) + [
            {"date": stamp, "change": "session %d 重做" % sid, "reason": "重做"}]
    change = {"kind": "session", "session": sid, "from": row.get("status"),
              "to": status, "redo": redo}
    return new_data, change, []

# trace: update --learner 主干（画像采集专线；置 assessed = 当日）
def apply_learner(args, data):
    learner = data.get("learner") if isinstance(data.get("learner"), dict) else {}
    role = args.role if args.role is not None else learner.get("role")
    experience = (args.experience if args.experience is not None
                  else learner.get("experience"))
    if role is not None and str(role) not in ROLE_ENUM:
        return None, None, [v("ENUM_INVALID", "update --learner --role",
                              "role 越界：%s（合法集 %s）" % (role, "|".join(ROLE_ENUM)))]
    if experience is not None and str(experience) not in EXPERIENCE_ENUM:
        return None, None, [v("ENUM_INVALID", "update --learner --experience",
                              "experience 越界：%s（合法集 %s）"
                              % (experience, "|".join(EXPERIENCE_ENUM)))]
    goals = list(args.goals) if args.goals is not None else list(learner.get("goals") or [])
    pains = (list(args.pain_points) if args.pain_points is not None
             else list(learner.get("pain_points") or []))
    new_data = dict(data)
    new_data["learner"] = {"role": role, "experience": experience, "goals": goals,
                           "pain_points": pains, "assessed": today()}
    return new_data, {"kind": "learner"}, []

# trace: update --summary 主干（结业门 7/7 + 路径口径 + 文件在场）
def apply_summary(args, data, out_dir, out_show, root):
    session_ids = data.get("sessions") if isinstance(data.get("sessions"), list) else []
    if data.get("sessions_completed") != len(session_ids):
        return None, None, [v("STATUS_MISMATCH", "update --summary",
                              "结业摘要门：7 节须全部 completed（当前 %s 节）——未满不得置位"
                              % data.get("sessions_completed"))]
    given = str(args.path)
    if os.path.isabs(given):
        target = os.path.abspath(given)
    else:
        candidates = [os.path.join(out_dir, given), os.path.join(root, given)]
        target = candidates[0]
        for candidate in candidates:
            if os.path.isfile(candidate):
                target = candidate
                break
    if os.path.normpath(target) != os.path.normpath(os.path.join(out_dir, SUMMARY_FILE)):
        return None, None, [v("ENUM_INVALID", "update --summary --path",
                              "path 须解析到 %s/%s（相对 {output_dir}），实为 %s"
                              % (out_show, SUMMARY_FILE, args.path))]
    if not os.path.isfile(target):
        return None, None, [v("MISSING_FILE", "update --summary --path",
                              "%s/%s 不在场"
                              "（先按 templates/completion-summary.md 生成摘要 md）"
                              % (out_show, SUMMARY_FILE))]
    new_data = dict(data)
    new_data["summary"] = {"generated": True, "path": SUMMARY_FILE, "date": today()}
    return new_data, {"kind": "summary"}, []

# trace: update 子命令（唯一写通道；写前跑与 check 同源的校验）
def cmd_update(args):
    root = os.path.abspath(args.project_root)
    out = os.path.abspath(args.output_dir)
    path = os.path.join(out, PROGRESS_FILE)
    show = display_path(path, root)
    out_show = display_path(out, root)
    payload = receipt_base("update", args, out)
    curriculum, cv = load_curriculum(root)
    if cv:
        payload["violations"] = cv
        emit_via(payload, args.json, human_update)
        return 1
    index_by_id = curriculum_index(curriculum)
    if not os.path.isfile(path):
        payload["violations"] = [v("MISSING_FILE", show,
                                   "进度文件不存在 → 先 init 建进度（本命令是写通道，不建文件）")]
        emit_via(payload, args.json, human_update)
        return 1
    damage = progress_damage(path)
    if damage is not None:
        payload["violations"] = [v(damage[0], show, damage[1] + RECOVERY_HINT)]
        emit_via(payload, args.json, human_update)
        return 1
    data, _ = load_yaml_safe(path)          # damage 已判过：此处必为 dict + sessions 列表

    if args.learner:
        new_data, change, violations = apply_learner(args, data)
    elif args.summary:
        new_data, change, violations = apply_summary(args, data, out, out_show, root)
    else:
        new_data, change, violations = apply_session(args, data, index_by_id, out,
                                                     out_show)
    if not violations and new_data is not None:
        completed, percentage, next_recommended = compute_derived(
            sorted(index_by_id), new_data["sessions"])
        new_data["sessions_completed"] = completed
        new_data["completion_percentage"] = percentage
        new_data["next_recommended"] = next_recommended
        project = dict(new_data.get("project") or {})
        project["updated"] = now()
        new_data["project"] = project
        gate, _ = validate(new_data, curriculum, show, out, root)
        violations = gate
    if violations:
        payload["violations"] = violations
        emit_via(payload, args.json, human_update)
        return 1
    try:
        save_yaml_atomic(path, new_data)
    except OSError as e:
        payload["violations"] = [v("TOOL_ERROR", show, "写回失败（原文件未改）：%s" % e)]
        emit_via(payload, args.json, human_update)
        return 1
    payload["ok"] = True
    payload["updated"] = new_data["project"]["updated"]
    payload["change"] = change
    payload["sessions_completed"] = new_data["sessions_completed"]
    payload["completion_percentage"] = new_data["completion_percentage"]
    payload["next_recommended"] = new_data["next_recommended"]
    payload["counts"] = {"sessions": len(new_data["sessions"]),
                         "sessions_completed": new_data["sessions_completed"],
                         "completion_percentage": new_data["completion_percentage"]}
    emit_via(payload, args.json, human_update)
    return 0

# trace: update 人读态
def human_update(payload):
    if payload["ok"]:
        print("PASS：写回成功（%s）· 完成 %s/7 节 · %s%% · 下一个推荐：%s"
              % (payload["change"]["kind"], payload["sessions_completed"],
                 payload["completion_percentage"], payload["next_recommended"]))
    print_human_tail(payload)

# ---------------------------------------------------------------- check

# trace: check 子命令（门禁：exit 0 唯一放行）
def cmd_check(args):
    root = os.path.abspath(args.project_root)
    out = os.path.abspath(args.output_dir)
    path = os.path.join(out, PROGRESS_FILE)
    show = display_path(path, root)
    payload = receipt_base("check", args, out)
    payload["final"] = args.final
    curriculum, cv = load_curriculum(root)
    if cv:
        payload["violations"] = cv
        emit_via(payload, args.json, human_check)
        return 1
    if not os.path.isfile(path):
        payload["violations"] = [v("MISSING_FILE", show,
                                   "%s 不存在（先跑 init 建进度）" % PROGRESS_FILE)]
        emit_via(payload, args.json, human_check)
        return 1
    damage = progress_damage(path)
    if damage is not None:
        payload["violations"] = [v(damage[0], show, damage[1] + RECOVERY_HINT)]
        emit_via(payload, args.json, human_check)
        return 1
    data, _ = load_yaml_safe(path)          # damage 已判过：此处必为 dict + sessions 列表
    violations, (completed, percentage, next_recommended) = validate(
        data, curriculum, show, out, root, final=args.final)
    payload["violations"] = violations
    payload["counts"] = {"sessions": len(curriculum["sessions"]),
                         "sessions_completed": completed,
                         "completion_percentage": percentage}
    payload["ok"] = not violations
    emit_via(payload, args.json, human_check)
    return 0 if payload["ok"] else 1

# trace: check 人读态
def human_check(payload):
    if payload["ok"]:
        print("PASS：进度文件校验通过（%s）· 完成 %s/7 节 · %s%%%s"
              % (payload["output_dir"] + "/" + PROGRESS_FILE,
                 payload["counts"]["sessions_completed"],
                 payload["counts"]["completion_percentage"],
                 "（--final）" if payload["final"] else ""))
    print_human_tail(payload)
