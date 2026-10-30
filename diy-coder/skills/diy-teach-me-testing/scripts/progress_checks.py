# -*- coding: utf-8 -*-
"""diy-teach-me-testing 校验族：日期形态/notes 路径口径/单节/learner/summary/revisions 六检与 validate 全量编排（status 与 check 同源）。."""

import os
import re

import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import is_int, nonempty, v  # noqa: E402

from progress_lib import DATE_RE, DERIVED_FIELDS, EXPERIENCE_ENUM, NOTES_DIR, PROJECT_FIELDS, ROLE_ENUM, STATUS_ENUM, SUMMARY_FILE, compute_derived, curriculum_index  # noqa: E402

# ---------------------------------------------------------------- 校验（check 与 status 同源）

# trace: 日期字段形态（null 或 YYYY-MM-DD）
def check_date(value, where, label):
    if value is None:
        return []
    if not nonempty(value) or not DATE_RE.fullmatch(str(value)):
        return [v("ENUM_INVALID", where, "%s 须为 YYYY-MM-DD 或 null，实为 %s"
                  % (label, value))]
    return []

# trace: notes 路径口径（相对、正斜杠、归属 notes/、命名 notes/session-<NN>.md）
def notes_path_problem(value, session_id):
    text = str(value)
    if "\\" in text or text.startswith("/") or re.match(r"^[A-Za-z]:", text):
        return "须为相对 {output_dir} 的正斜杠路径"
    parts = text.split("/")
    if any(part in ("", ".", "..") for part in parts) or len(parts) < 2:
        return "路径含空段/./.. 段，或未归属 %s/ 目录" % NOTES_DIR
    if parts[0] != NOTES_DIR:
        return "须归属 %s/ 目录（实为 %s/）" % (NOTES_DIR, parts[0])
    if text != "%s/session-%02d.md" % (NOTES_DIR, session_id):
        return "命名须为 notes/session-<NN>.md（NN = 两位零填充 session id），实为 %s" % text
    return None

# trace: 单节校验（id 对齐 / 状态枚举 / 日期 / score / topics / notes）
def check_session(index, session, show, index_by_id, out_dir, project_root):
    where = "%s sessions[%d]" % (show, index)
    if not isinstance(session, dict):
        return [v("EMPTY_FIELD", where, "session 不是映射")]
    violations = []
    sid = session.get("id")
    if not is_int(sid):
        violations.append(v("ENUM_INVALID", where + ".id",
                            "session id 须为整数 1-7，实为 %s" % sid))
        return violations
    if sid not in index_by_id:
        return [v("UNKNOWN_ID", where + ".id",
                  "session id %d 不在 curriculum.yaml 的课程集合内" % sid)]
    definition = index_by_id[sid]
    if session.get("name") != definition.get("name"):
        violations.append(v("SET_MISMATCH", where + ".name",
                            "name 与 curriculum.yaml 不一致（定义态唯一源）："
                            "实为 %s，应为 %s" % (session.get("name"),
                                                definition.get("name"))))
    if session.get("duration_min") != definition.get("duration_min"):
        violations.append(v("SET_MISMATCH", where + ".duration_min",
                            "duration_min 与 curriculum.yaml 不一致：实为 %s，应为 %s"
                            % (session.get("duration_min"),
                               definition.get("duration_min"))))
    status = session.get("status")
    if not nonempty(status) or str(status) not in STATUS_ENUM:
        violations.append(v("ENUM_INVALID", where + ".status",
                            "status 越界：%s（合法集 %s）"
                            % (status, "|".join(STATUS_ENUM))))
        status = None
    violations += check_date(session.get("started_date"), where + ".started_date",
                             "started_date")
    violations += check_date(session.get("completed_date"), where + ".completed_date",
                             "completed_date")
    if status in ("进行中", "已完成") and not nonempty(session.get("started_date")):
        violations.append(v("STATUS_MISMATCH", where + ".started_date",
                            "%s 状态须有 started_date" % status))
    if status == "已完成" and not nonempty(session.get("completed_date")):
        violations.append(v("STATUS_MISMATCH", where + ".completed_date",
                            "已完成状态须有 completed_date（结业摘要按它统计）"))

    exploratory = definition.get("min_topics") is not None
    score = session.get("score")
    if score is not None:
        if not is_int(score) or not 0 <= score <= 100:
            violations.append(v("ENUM_INVALID", where + ".score",
                                "score 须为 0-100 整数或 null，实为 %s" % score))
        elif exploratory:
            violations.append(v("STATUS_MISMATCH", where + ".score",
                                "session %d 无 quiz：score 恒 null"
                                "（源硬编码 100 不照搬，不参与平均分）" % sid))
        elif status != "已完成":
            violations.append(v("STATUS_MISMATCH", where + ".score",
                                "score 仅已完成节非空（当前 status: %s）" % status))

    topics = session.get("topics_explored")
    if topics is not None:
        if not is_int(topics) or topics < 0:
            violations.append(v("ENUM_INVALID", where + ".topics_explored",
                                "topics_explored 须为非负整数或 null，实为 %s" % topics))
        elif not exploratory:
            violations.append(v("ENUM_INVALID", where + ".topics_explored",
                                "topics_explored 仅探索型课次（session 7）非空"
                                "（第 %d 节应为 null）" % sid))
    if exploratory and status == "已完成":
        minimum = definition["min_topics"]
        if topics is None:
            violations.append(v("EMPTY_FIELD", where + ".topics_explored",
                                "完成判据：session %d 完成须记 topics_explored"
                                "（>= %d）" % (sid, minimum)))
        elif is_int(topics) and topics < minimum:
            violations.append(v("SET_MISMATCH", where + ".topics_explored",
                                "完成判据：session %d 的 topics_explored=%d 未达 "
                                "curriculum.yaml 的 min_topics=%d"
                                % (sid, topics, minimum)))

    notes = session.get("notes")
    if notes is None:
        if status == "已完成":
            violations.append(v("EMPTY_FIELD", where + ".notes",
                                "已完成节必填 notes（notes/session-%02d.md）" % sid))
    elif not nonempty(notes):
        violations.append(v("EMPTY_FIELD", where + ".notes", "notes 为空字符串"))
    else:
        problem = notes_path_problem(notes, sid)
        if problem:
            violations.append(v("ENUM_INVALID", where + ".notes",
                                "notes 路径违例：%s（实为 %s）" % (problem, notes)))
        else:
            target = os.path.join(out_dir, str(notes).replace("/", os.sep))
            if not os.path.isfile(target):
                violations.append(v("MISSING_FILE", where + ".notes",
                                    "%s 不在场（先落笔记 md，再 update --session）"
                                    % notes))
    return violations

# trace: learner 自洽（枚举 / 形态 / assessed 非空 → role 与 experience 须在）
def check_learner(learner, show):
    where = show + " learner"
    if not isinstance(learner, dict):
        return [v("EMPTY_FIELD", where, "learner 缺失或不是映射")]
    violations = []
    role = learner.get("role")
    if role is not None and (not nonempty(role) or str(role) not in ROLE_ENUM):
        violations.append(v("ENUM_INVALID", where + ".role",
                            "role 越界：%s（合法集 %s|null）"
                            % (role, "|".join(ROLE_ENUM))))
    experience = learner.get("experience")
    if experience is not None and (not nonempty(experience)
                                   or str(experience) not in EXPERIENCE_ENUM):
        violations.append(v("ENUM_INVALID", where + ".experience",
                            "experience 越界：%s（合法集 %s|null）"
                            % (experience, "|".join(EXPERIENCE_ENUM))))
    violations += check_date(learner.get("assessed"), where + ".assessed", "assessed")
    for key in ("goals", "pain_points"):
        value = learner.get(key)
        if not isinstance(value, list) or any(not nonempty(x) for x in value):
            violations.append(v("EMPTY_FIELD", "%s.%s" % (where, key),
                                "%s 须为字符串列表（无内容写空列表）" % key))
    if nonempty(learner.get("assessed")):
        for key in ("role", "experience"):
            if not nonempty(learner.get(key)):
                violations.append(v("EMPTY_FIELD", "%s.%s" % (where, key),
                                    "assessed 非空 → %s 不得为空（画像未采集完不得置 assessed）"
                                    % key))
    return violations

# trace: summary 自洽（generated 真假两态；path 口径与文件在场）
def check_summary(summary, show, out_dir):
    where = show + " summary"
    if not isinstance(summary, dict):
        return [v("EMPTY_FIELD", where, "summary 缺失或不是映射")]
    violations = []
    generated = summary.get("generated")
    if not isinstance(generated, bool):
        violations.append(v("EMPTY_FIELD", where + ".generated",
                            "summary.generated 须为布尔，实为 %s" % generated))
        return violations
    path = summary.get("path")
    date = summary.get("date")
    if not generated:
        if path is not None or date is not None:
            violations.append(v("STATUS_MISMATCH", where,
                                "generated 为假时 path 与 date 须为 null"
                                "（置位只经 update --summary）"))
        return violations
    if not nonempty(path) or str(path) != SUMMARY_FILE:
        violations.append(v("ENUM_INVALID", where + ".path",
                            "summary.path 须为 %s（相对 {output_dir}），实为 %s"
                            % (SUMMARY_FILE, path)))
    else:
        target = os.path.join(out_dir, SUMMARY_FILE)
        if not os.path.isfile(target):
            violations.append(v("MISSING_FILE", where + ".path",
                                "%s 不在场（先落摘要 md，再 update --summary）"
                                % SUMMARY_FILE))
    violations += check_date(date, where + ".date", "summary.date")
    if not nonempty(date):
        violations.append(v("EMPTY_FIELD", where + ".date", "generated 为真时 date 不得为空"))
    return violations

# trace: revisions 形态（{date, change, reason} 三字段非空）
def check_revisions(revisions, show):
    where = show + " revisions"
    if not isinstance(revisions, list):
        return [v("EMPTY_FIELD", where, "revisions 缺失或不是列表（无内容写空列表）")]
    violations = []
    for i, entry in enumerate(revisions):
        ew = "%s[%d]" % (where, i)
        if not isinstance(entry, dict):
            violations.append(v("EMPTY_FIELD", ew, "修订条目不是映射"))
            continue
        for key in ("date", "change", "reason"):
            if not nonempty(entry.get(key)):
                violations.append(v("EMPTY_FIELD", "%s.%s" % (ew, key),
                                    "修订条目的 %s 不得为空" % key))
        violations += check_date(entry.get("date"), ew + ".date", "修订日期")
    return violations

# trace: 进度文件全量校验（status 与 check 同源，--final 加三条件）
def validate(data, curriculum, show, out_dir, project_root, final=False):
    if not isinstance(data, dict):
        return [v("EMPTY_FIELD", show,
                  "顶层不是映射（须为 project + learner + sessions + 派生三键 + summary"
                  " + revisions）")], (0, 0, None)
    violations = []
    project = data.get("project")
    if not isinstance(project, dict):
        violations.append(v("EMPTY_FIELD", show + " project",
                            "project 缺失或不是映射（须含 name/created/updated）"))
    else:
        for key in PROJECT_FIELDS:
            if not nonempty(project.get(key)):
                violations.append(v("EMPTY_FIELD", "%s project.%s" % (show, key),
                                    "project.%s 缺失" % key))
    index_by_id = curriculum_index(curriculum)
    session_ids = sorted(index_by_id)
    raw_sessions = data.get("sessions")
    sessions = raw_sessions if isinstance(raw_sessions, list) else []
    if not isinstance(raw_sessions, list):
        violations.append(v("EMPTY_FIELD", show + " sessions",
                            "sessions 缺失或不是列表（7 节全列）"))
    seen = set()
    for i, session in enumerate(sessions):
        violations += check_session(i, session, show, index_by_id, out_dir, project_root)
        if isinstance(session, dict) and is_int(session.get("id")):
            sid = session["id"]
            if sid in seen:
                violations.append(v("DUPLICATE_ID", "%s sessions[%d].id" % (show, i),
                                    "session id %d 重复（id 即键，不重编不重用）" % sid))
            seen.add(sid)
    for sid in session_ids:
        if sid not in seen:
            violations.append(v("SET_MISMATCH", show + " sessions",
                                "缺 session %d：session id 集合须与 curriculum.yaml 一致"
                                "（1-%d）" % (sid, session_ids[-1])))
    violations += check_learner(data.get("learner"), show)
    violations += check_summary(data.get("summary"), show, out_dir)
    violations += check_revisions(data.get("revisions"), show)

    completed, percentage, next_recommended = compute_derived(session_ids, sessions)
    real = {"sessions_completed": completed,
            "completion_percentage": percentage,
            "next_recommended": next_recommended}
    for key in DERIVED_FIELDS:
        if key not in data:
            violations.append(v("EMPTY_FIELD", "%s %s" % (show, key),
                                "%s 缺失（派生字段由引擎写）" % key))
        elif data.get(key) != real[key]:
            violations.append(v("SET_MISMATCH", "%s %s" % (show, key),
                                "%s=%s 与 sessions[] 真值 %s 不符（基准 = 三式，"
                                "派生字段只由引擎写）"
                                % (key, data.get(key), real[key])))
    if final:
        if completed != len(session_ids):
            violations.append(v("SET_MISMATCH", "%s sessions_completed" % show,
                                "--final 要求 %d 节全部 completed，当前 %d 节"
                                % (len(session_ids), completed)))
        summary = data.get("summary")
        if not isinstance(summary, dict) or summary.get("generated") is not True:
            violations.append(v("SET_MISMATCH", "%s summary.generated" % show,
                                "--final 要求 summary.generated 为真"
                                "（结业摘要经 update --summary --path 置位）"))
        elif not nonempty(summary.get("path")) or not os.path.isfile(
                os.path.join(out_dir, str(summary.get("path")))):
            violations.append(v("MISSING_FILE", "%s summary.path" % show,
                                "--final 要求 summary.path 指向的文件在场"))
    return violations, (completed, percentage, next_recommended)
