# -*- coding: utf-8 -*-
"""diy-teach-me-testing 领域引擎：跨会话学习进度的生成（init）/ 仪表盘与校验（status）/
单一写通道（update）/ 门禁校验（check [--final]）。

机制：技能结构（7 节课程 id/名称/时长/先修/学习路径/角色适配）是**定义态**，落技能内静态资产
`curriculum.yaml`；学员进度是**运行态**，落 `{output_dir}/learning-progress.yaml`。两者用整数
session id（1-7）对齐，禁混为一文件。引擎负责全部机械判定：

  init    读 curriculum.yaml 建进度（7 节全未开始）+ 建 `{output_dir}/notes/` 目录；
          进度文件已存在且**可用** → 拒绝（ALREADY_EXISTS）并指引 resume（不覆盖）；
          已存在但**不可用**（解析失败 / 顶层非映射 / 缺 sessions 列表）→ 不带 `--recover`
          仍拒绝（同一判据的违规码）并把 `--recover` 指成唯一出路，带 `--recover` 则先把原
          文件逐字节备份为 `learning-progress.yaml.corrupt-<YYYYmmdd-HHMMSS>.bak`（shutil.copy2），
          再重建 7 节骨架——丢的只是台账断点，损坏件与笔记 md 都留在盘上。`--role` 可省
          （省略 → learner.role: null）；无论是否省略，`learner.assessed` 一律 null——
          画像采集归 02-assess（update --learner），init 不得置位。

  status  读进度 + 校验（与 check 同源）+ 输出仪表盘数据（每节状态 / 下一个推荐 / 完成度），
          并直出 `entry_step`——即 SKILL.md 里跨会话重入分流表的判定结果（进度文件不存在 →
          steps/01-init.md；进度文件不可用（损坏）→ steps/01-init.md（走 `init --recover`）；
          learner.assessed 为空 → steps/02-assess.md；sessions_completed < 7
          → steps/03-hub.md；7 节齐但 summary.generated 为假 → steps/05-completion.md；
          summary.generated 为真 → steps/03-hub.md）。分流表是唯一入口，判定输入就是本回执。

  update  唯一写通道，三形态互斥（--session / --learner / --summary 三者取一）：
            --session N [--status S] [--score S] [--notes P] [--topics N]
              幂等 upsert：以 session id 为键，重复完成不重复计数（sessions_completed 由
              status 计数得出）。重做（已完成的节再次完成）→ score/日期以最新为准
              + 追加一条 revisions（{date, change: "session N 重做", reason: "redo"}）；
              notes md 由技能侧覆盖同名文件，引擎只记路径。
            --learner [--role R] [--experience S] [--goals G] [--pain-points P]
              写 learner 区块并置 assessed = 当日（02-assess 专线）。
            --summary --path P
              置 summary = {generated: true, path: completion-summary.md, date: 当日}
              （05-completion 专线；P 须解析到 {output_dir}/completion-summary.md 且文件在场，
              且 7 节已修满）。
          任一形态落盘后一律按裁定 2 三式重算派生字段；**写前跑一遍与 check 同源的校验**
          （写通道与门禁同源：引擎不写一份会被 check 判违规的进度）。

  check   schema / session id 集合与 curriculum 一致（整数 1-7）/ 派生字段与真值一致
          （基准 = 裁定 2 三式：sessions_completed = status==已完成 计数、
          completion_percentage = floor(completed*100/7 + 0.5)、next_recommended = 最小未完成
          id，全完成 → null）/ score 范围与状态（0-100 整数、非已完成恒 null、session 7
          恒 null）/ session 7 完成判据（status==已完成 → topics_explored >=
          curriculum.sessions[7].min_topics）/ notes 路径口径（相对、正斜杠、归属 notes/、
          命名 notes/session-<NN>.md、文件在场；已完成节必填）/ learner 自洽（assessed
          非空 → role 与 experience 不得为空）/ summary 自洽 / --final 三条件（7 节全已完成
          且 summary.generated 为真 且 summary.path 文件在场）。exit 0 唯一放行。

派生字段（sessions_completed / completion_percentage / next_recommended）**只由本引擎写**；
LLM 手写与真值不符 → SET_MISMATCH。命令面互斥组由 argparse 强制；旗标组合错误（如 --score 配
--learner）走用法错误 exit 2。

违规码：复用 batch3-contract §3 冻结集——本引擎用到 MISSING_FILE / UNPARSABLE_YAML /
UNKNOWN_ID / ENUM_INVALID / EMPTY_FIELD / STATUS_MISMATCH / SET_MISMATCH / TOOL_ERROR 共 8 个。
**新增 1 码：`ALREADY_EXISTS`**（init 面：进度文件已存在 → 拒绝并指引 resume；冻结集里没有
「目标已存在」语义的码，DUPLICATE_ID 只指 ID 重复，复用会误导读回执的人）。
--previous 不适用：进度按 curriculum 固定 session 键幂等 upsert，无 ID 集合收缩面。

任务书偏离（须主 agent 仲裁，2 条）：

① update --session 在 §7 冻结签名 `[--score S] [--notes P] [--status S]` 之外**增补可选旗标
`[--topics N]`**。理由：§7 的运行态 schema 要求 session 7 以 `topics_explored >= min_topics`
作为完成判据、且该字段「仅 session 7 非空」，但冻结命令面没有任何通道能写它——不加此旗标则
session 7 永远无法经引擎完成，7/7 结业门与 check --final 三条件均不可达（单一写通道纪律又禁止
LLM 手写 YAML）。增补是**纯加性**的：冻结签名中的三个旗标语义一字未动，仅多一个可选入口
（2026-09-18 已追认，任务书变更登记 ⑤）。

② init 在 §7 冻结签名 `[--role R]` 之外**增补可选旗标 `[--recover]`**（V 能力清点 T-6，乙类：
功能性缺陷）。理由：损坏的进度文件让每条命令都只能报错——`status` / `update` / `check` 读不动
它，`init` 又因「已存在」一律拒绝，而单一写通道纪律禁止 LLM 手改 YAML ⇒ **损坏即死锁，需人工
干预且无步骤承载**（源 `instructions.md:110-113` 有「检测 + 自动备份 + 提供 fresh start」）。
该旗标把恢复收归引擎：备份（逐字节副本）→ 重建，人只发命令、不碰 YAML。**纯加性**：不带
`--recover` 时逐字保持原行为（文件可用 → ALREADY_EXISTS 拒绝），且文件可用时带 `--recover`
同样拒绝——「进度文件已存在 → 强制 resume」纪律一字未松。

回执契约对齐 B1/B2/B3 既有先例：共同键 {ok, command, project_root, output_dir, violations
[{code,where,msg}], warnings, counts}；写命令（init / update）另含 `updated`（bump 后日期）；
where 一律正斜杠、相对 project-root，无位置时用命令形态字符串；人读态每条违规一行
`CODE where: msg` + 末尾汇总行；--json 单行（ensure_ascii=False）；--output-dir 必填
（argparse required，无默认值）；引擎不做实例解析/白名单/目录推导（实例解析由 SKILL.md 委托
diyc.py resolve）。写回纪律：全文 load → 就地改 → yaml.safe_dump(allow_unicode=True,
sort_keys=False, default_flow_style=False) → 同目录临时文件 + os.replace（注释不保留）。
"""
import argparse
import datetime
import io
import json
import math
import os
import re
import shutil
import sys

import yaml

PROGRESS_FILE = "learning-progress.yaml"
CURRICULUM_FILE = "curriculum.yaml"
NOTES_DIR = "notes"
SUMMARY_FILE = "completion-summary.md"

STATUS_ENUM = ("未开始", "进行中", "已完成")
ROLE_ENUM = ("QA", "开发", "组长", "负责人")
EXPERIENCE_ENUM = ("入门", "进阶", "资深")
SESSION_FIELDS = ("id", "name", "duration_min", "status", "started_date",
                  "completed_date", "score", "topics_explored", "notes")
LEARNER_FIELDS = ("role", "experience", "goals", "pain_points", "assessed")
DERIVED_FIELDS = ("sessions_completed", "completion_percentage", "next_recommended")
PROJECT_FIELDS = ("name", "created", "updated")

DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}\Z")
NOTES_RE = re.compile(r"notes/session-(\d{2})\.md\Z")

ENTRY_INIT = "steps/01-init.md"
ENTRY_ASSESS = "steps/02-assess.md"
ENTRY_HUB = "steps/03-hub.md"
ENTRY_COMPLETION = "steps/05-completion.md"

# trace: T-6 损坏出路（单一写通道下恢复只能由引擎做；本句即唯一指路文案，四处复用）
RECOVERY_HINT = ("；唯一出路 = 跑 init --recover（引擎先把原文件备份为 *.corrupt-<时间戳>.bak "
                 "再重建 7 节骨架；禁止手改 YAML 或自行删除）")
BACKUP_STAMP = "%Y%m%d-%H%M%S"


# trace: B3 diy-teach-me-testing 违规项构造（统一 {code, where, msg} 形态）
def v(code, where, msg):
    return {"code": code, "where": where, "msg": msg}


# trace: B3 diy-teach-me-testing 非空判定（None / 空白字符串均视为空）
def nonempty(value):
    return value is not None and str(value).strip() != ""


# trace: B3 diy-teach-me-testing 整数判定（布尔不得充当整数：true 不是 1）
def is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


# trace: B3 diy-teach-me-testing 日期口径（today = YYYY-MM-DD，对齐契约 §3）
def today():
    return datetime.date.today().isoformat()


# trace: B3 diy-teach-me-testing where 显示口径（正斜杠 + 相对 project-root；越界回退绝对路径）
def display_path(path, project_root):
    try:
        rel = os.path.relpath(path, project_root)
    except ValueError:
        rel = os.path.abspath(path)
    if rel.startswith(".."):
        return os.path.abspath(path).replace("\\", "/")
    return rel.replace("\\", "/")


# trace: B3 diy-teach-me-testing YAML 安全装载：(data, err)；缺失 (None, None)、空 ({}, None)、损坏 (None, 原因)
def load_yaml_safe(path):
    if not os.path.isfile(path):
        return None, None
    try:
        with io.open(path, "r", encoding="utf-8") as handle:
            return (yaml.safe_load(handle) or {}), None
    except yaml.YAMLError as e:
        return None, str(e)
    except OSError as e:
        return None, str(e)


# trace: B3 diy-teach-me-testing 原子写（全文 load → 就地改 → dump → 同目录 tmp + os.replace）
def save_yaml_atomic(path, data):
    tmp = path + ".tmp"
    try:
        with io.open(tmp, "w", encoding="utf-8") as handle:
            yaml.safe_dump(data, handle, allow_unicode=True, sort_keys=False,
                           default_flow_style=False)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise


# trace: T-6 进度文件可用性探测（唯一判据，init 的恢复门与 status/update/check 的报错同源）
def progress_damage(path):
    if not os.path.isfile(path):
        return None
    data, err = load_yaml_safe(path)
    if err is not None:
        return "UNPARSABLE_YAML", "进度文件解析失败：%s" % err
    if not isinstance(data, dict) or not isinstance(data.get("sessions"), list):
        return "EMPTY_FIELD", "进度文件顶层不是映射或缺 sessions 列表"
    return None


# trace: T-6 损坏件备份（逐字节副本；名字不带 .yaml 后缀 → 不进 viewer 的 *.yaml 扫描面）
def backup_progress(path):
    stamp = datetime.datetime.now().strftime(BACKUP_STAMP)
    backup = "%s.corrupt-%s.bak" % (path, stamp)
    shutil.copy2(path, backup)
    return backup


# trace: B3 diy-teach-me-testing 回执输出（--json 单行 / 人读行）
def emit(payload, as_json, human_lines):
    if as_json:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        human_lines(payload)


# trace: B3 diy-teach-me-testing 回执公共头（共同键 + 命令名 + 归一化 output_dir）
def receipt_base(command, args, out):
    return {
        "ok": False,
        "command": command,
        "project_root": args.project_root,
        "output_dir": os.path.normpath(out).replace("\\", "/"),
        "violations": [],
        "warnings": [],
        "counts": {},
    }


# trace: B3 diy-teach-me-testing 人读态统一收尾（每条违规一行 CODE where: msg + 汇总行）
def print_human_tail(payload, headline=None):
    if payload.get("ok") and headline:
        print(headline)
    for item in payload["violations"]:
        print("%s %s: %s" % (item["code"], item["where"], item["msg"]))
    for item in payload["warnings"]:
        print("警告 %s %s: %s" % (item["code"], item["where"], item["msg"]))
    counts = payload["counts"]
    detail = " · ".join("%s %s" % (k, counts[k]) for k in sorted(counts))
    print("汇总：%s · 违规 %d 条 · 警告 %d 条（exit %d）"
          % (detail, len(payload["violations"]), len(payload["warnings"]),
             0 if payload["ok"] else 1))


# ---------------------------------------------------------------- curriculum（定义态）

# trace: B3 diy-teach-me-testing 课程结构装载（定义态唯一源；session id 集合即对齐键）
def load_curriculum(project_root):
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        CURRICULUM_FILE)
    show = display_path(path, project_root)
    data, err = load_yaml_safe(path)
    if data is None and err is None:
        return None, [v("MISSING_FILE", show, "%s 不存在（技能自带静态资产）" % CURRICULUM_FILE)]
    if err is not None:
        return None, [v("UNPARSABLE_YAML", show, "课程结构解析失败：%s" % err)]
    if not isinstance(data, dict) or not isinstance(data.get("sessions"), list):
        return None, [v("EMPTY_FIELD", show, "课程结构缺 sessions 列表")]
    violations = []
    seen = set()
    for i, session in enumerate(data["sessions"]):
        where = "%s sessions[%d]" % (show, i)
        if not isinstance(session, dict):
            violations.append(v("EMPTY_FIELD", where, "session 不是映射"))
            continue
        sid = session.get("id")
        if not is_int(sid):
            violations.append(v("ENUM_INVALID", where + ".id",
                                "session id 须为整数（1-7），实为 %s" % sid))
            continue
        if sid in seen:
            violations.append(v("DUPLICATE_ID", where + ".id", "session id %d 重复" % sid))
        seen.add(sid)
        if not nonempty(session.get("name")):
            violations.append(v("EMPTY_FIELD", where + ".name", "session 缺 name"))
    if violations:
        return None, violations
    return data, []


# trace: B3 diy-teach-me-testing curriculum 索引（id → 节定义；id 集合即运行态对齐基准）
def curriculum_index(curriculum):
    return {s["id"]: s for s in curriculum["sessions"]}


# ---------------------------------------------------------------- 派生字段（裁定 2 三式）

# trace: B3 diy-teach-me-testing 派生三式（基准：check/status 的比对真值，唯一算法）
def compute_derived(session_ids, sessions):
    known = set(session_ids)
    done = set()
    for row in sessions:
        if not isinstance(row, dict) or row.get("status") != "已完成":
            continue
        sid = row.get("id")
        if is_int(sid) and sid in known:
            done.add(sid)
    completed = len(done)
    percentage = math.floor(completed * 100 / len(session_ids) + 0.5)
    remaining = [sid for sid in session_ids if sid not in done]
    return completed, percentage, (min(remaining) if remaining else None)


# ---------------------------------------------------------------- 校验（check 与 status 同源）

# trace: B3 diy-teach-me-testing 日期字段形态（null 或 YYYY-MM-DD）
def check_date(value, where, label):
    if value is None:
        return []
    if not nonempty(value) or not DATE_RE.fullmatch(str(value)):
        return [v("ENUM_INVALID", where, "%s 须为 YYYY-MM-DD 或 null，实为 %s"
                  % (label, value))]
    return []


# trace: B3 diy-teach-me-testing notes 路径口径（相对、正斜杠、归属 notes/、命名 notes/session-<NN>.md）
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


# trace: B3 diy-teach-me-testing 单节校验（id 对齐 / 状态枚举 / 日期 / score / topics / notes）
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


# trace: B3 diy-teach-me-testing learner 自洽（枚举 / 形态 / assessed 非空 → role 与 experience 须在）
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


# trace: B3 diy-teach-me-testing summary 自洽（generated 真假两态；path 口径与文件在场）
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


# trace: B3 diy-teach-me-testing revisions 形态（{date, change, reason} 三字段非空）
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


# trace: B3 diy-teach-me-testing 进度文件全量校验（status 与 check 同源，--final 加三条件）
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
                                "%s=%s 与 sessions[] 真值 %s 不符（基准 = 裁定 2 三式，"
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


# ---------------------------------------------------------------- init

# trace: B3 diy-teach-me-testing 项目名（取 diy-coder.yaml 的 project.name，缺则回落目录名 + warning）
def project_name(root):
    cfg, err = load_yaml_safe(os.path.join(root, "diy-coder.yaml"))
    if isinstance(cfg, dict):
        project = cfg.get("project")
        if isinstance(project, dict) and nonempty(project.get("name")):
            return str(project["name"]), None
    note = "diy-coder.yaml project.name 不可用（%s），回落项目目录名" % (err or "缺该键")
    return os.path.basename(os.path.abspath(root)), v("MISSING_FILE", "diy-coder.yaml",
                                                      note)


# trace: B3 diy-teach-me-testing 空白进度骨架（7 节全未开始；派生字段由引擎写）
def blank_progress(curriculum, name, role):
    stamp = today()
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
        emit(payload, args.json, human_init)
        return 1
    role = args.role
    if role is not None and str(role) not in ROLE_ENUM:
        payload["violations"] = [v("ENUM_INVALID", "init --role",
                                   "role 越界：%s（合法集 %s）"
                                   % (role, "|".join(ROLE_ENUM)))]
        emit(payload, args.json, human_init)
        return 1
    backup = None
    if os.path.exists(path):
        damage = progress_damage(path)
        if damage is None:
            payload["violations"] = [
                v("ALREADY_EXISTS", show,
                  "进度文件已存在 → 走 resume：先跑 status 拿分流，"
                  "禁止覆盖重建（断点即进度，覆盖等于抹掉学习历史）")]
            emit(payload, args.json, human_init)
            return 1
        if not args.recover:
            payload["violations"] = [v(damage[0], show, damage[1] + RECOVERY_HINT)]
            emit(payload, args.json, human_init)
            return 1
        try:
            backup = backup_progress(path)
        except OSError as e:
            payload["violations"] = [v("TOOL_ERROR", show, "备份损坏件失败（零写入）：%s" % e)]
            emit(payload, args.json, human_init)
            return 1
    name, warning = project_name(root)
    doc = blank_progress(curriculum, name, role)
    try:
        os.makedirs(os.path.join(out, NOTES_DIR), exist_ok=True)
        save_yaml_atomic(path, doc)
    except OSError as e:
        payload["violations"] = [v("TOOL_ERROR", show, "写盘失败：%s" % e)]
        emit(payload, args.json, human_init)
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
    emit(payload, args.json, human_init)
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
        emit(payload, args.json, human_status)
        return 1
    if not os.path.isfile(path):
        payload["violations"] = [v("MISSING_FILE", show,
                                   "进度文件不存在 → 先 init 建进度（零 mtime 覆盖）")]
        payload["entry_step"] = ENTRY_INIT
        payload["dashboard"] = dashboard({})
        emit(payload, args.json, human_status)
        return 1
    damage = progress_damage(path)
    if damage is not None:
        payload["violations"] = [v(damage[0], show, damage[1] + RECOVERY_HINT)]
        payload["entry_step"] = ENTRY_INIT
        payload["dashboard"] = dashboard({})
        emit(payload, args.json, human_status)
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
    emit(payload, args.json, human_status)
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


# ---------------------------------------------------------------- update

# trace: B3 diy-teach-me-testing update --session 归一化（路径口径 + 文件在场）
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


# trace: B3 diy-teach-me-testing update --session 主干（幂等 upsert + 重做修订）
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
            {"date": stamp, "change": "session %d 重做" % sid, "reason": "redo"}]
    change = {"kind": "session", "session": sid, "from": row.get("status"),
              "to": status, "redo": redo}
    return new_data, change, []


# trace: B3 diy-teach-me-testing update --learner 主干（画像采集专线；置 assessed = 当日）
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


# trace: B3 diy-teach-me-testing update --summary 主干（结业门 7/7 + 路径口径 + 文件在场）
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


# trace: B3 diy-teach-me-testing update 子命令（唯一写通道；写前跑与 check 同源的校验）
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
        emit(payload, args.json, human_update)
        return 1
    index_by_id = curriculum_index(curriculum)
    if not os.path.isfile(path):
        payload["violations"] = [v("MISSING_FILE", show,
                                   "进度文件不存在 → 先 init 建进度（本命令是写通道，不建文件）")]
        emit(payload, args.json, human_update)
        return 1
    damage = progress_damage(path)
    if damage is not None:
        payload["violations"] = [v(damage[0], show, damage[1] + RECOVERY_HINT)]
        emit(payload, args.json, human_update)
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
        project["updated"] = today()
        new_data["project"] = project
        gate, _ = validate(new_data, curriculum, show, out, root)
        violations = gate
    if violations:
        payload["violations"] = violations
        emit(payload, args.json, human_update)
        return 1
    try:
        save_yaml_atomic(path, new_data)
    except OSError as e:
        payload["violations"] = [v("TOOL_ERROR", show, "写回失败（原文件未改）：%s" % e)]
        emit(payload, args.json, human_update)
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
    emit(payload, args.json, human_update)
    return 0


# trace: B3 diy-teach-me-testing update 人读态
def human_update(payload):
    if payload["ok"]:
        print("PASS：写回成功（%s）· 完成 %s/7 节 · %s%% · 下一个推荐：%s"
              % (payload["change"]["kind"], payload["sessions_completed"],
                 payload["completion_percentage"], payload["next_recommended"]))
    print_human_tail(payload)


# ---------------------------------------------------------------- check

# trace: B3 diy-teach-me-testing check 子命令（门禁：exit 0 唯一放行）
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
        emit(payload, args.json, human_check)
        return 1
    if not os.path.isfile(path):
        payload["violations"] = [v("MISSING_FILE", show,
                                   "%s 不存在（先跑 init 建进度）" % PROGRESS_FILE)]
        emit(payload, args.json, human_check)
        return 1
    damage = progress_damage(path)
    if damage is not None:
        payload["violations"] = [v(damage[0], show, damage[1] + RECOVERY_HINT)]
        emit(payload, args.json, human_check)
        return 1
    data, _ = load_yaml_safe(path)          # damage 已判过：此处必为 dict + sessions 列表
    violations, (completed, percentage, next_recommended) = validate(
        data, curriculum, show, out, root, final=args.final)
    payload["violations"] = violations
    payload["counts"] = {"sessions": len(curriculum["sessions"]),
                         "sessions_completed": completed,
                         "completion_percentage": percentage}
    payload["ok"] = not violations
    emit(payload, args.json, human_check)
    return 0 if payload["ok"] else 1


# trace: B3 diy-teach-me-testing check 人读态
def human_check(payload):
    if payload["ok"]:
        print("PASS：进度文件校验通过（%s）· 完成 %s/7 节 · %s%%%s"
              % (payload["output_dir"] + "/" + PROGRESS_FILE,
                 payload["counts"]["sessions_completed"],
                 payload["counts"]["completion_percentage"],
                 "（--final）" if payload["final"] else ""))
    print_human_tail(payload)


# ---------------------------------------------------------------- 命令行面

# trace: B3 diy-teach-me-testing 命令行面（--output-dir 必填；update 三形态互斥）
def build_parser():
    ap = argparse.ArgumentParser(
        description="diy-teach-me-testing 领域引擎：学习进度生成（init）/ 仪表盘与校验（status）"
                    "/ 单一写通道（update）/ 门禁校验（check --final）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    i = sub.add_parser("init", help="建 {output_dir}/learning-progress.yaml（7 节全未开始）"
                                    "+ notes/ 目录；已存在 → 拒绝并指引 resume"
                                    "（不可用的损坏件走 --recover：先备份再重建）")
    i.add_argument("--role", default=None,
                   help="学员角色（可省；省略 → learner.role: null。assessed 一律 null）")
    i.add_argument("--recover", action="store_true",
                   help="损坏件恢复通道：进度文件不可用（解析失败 / 顶层非映射 / 缺 sessions "
                        "列表）时先把原文件备份为 learning-progress.yaml.corrupt-"
                        "<YYYYmmdd-HHMMSS>.bak 再重建 7 节骨架；不带本旗标只报错指路，"
                        "文件可用时带本旗标也一律拒绝（走 resume）")
    i.add_argument("--project-root", default=".", help="项目根（默认 .）")
    i.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    i.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    i.set_defaults(func=cmd_init)

    s = sub.add_parser("status", help="读进度 + 校验（与 check 同源）+ 仪表盘 + 分流 entry_step")
    s.add_argument("--project-root", default=".", help="项目根（默认 .）")
    s.add_argument("--output-dir", required=True, help="产物目录（必填）")
    s.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    s.set_defaults(func=cmd_status)

    u = sub.add_parser("update", help="唯一写通道：--session / --learner / --summary 三形态互斥")
    form = u.add_mutually_exclusive_group(required=True)
    form.add_argument("--session", type=int, default=None, help="session id（整数 1-7）")
    form.add_argument("--learner", action="store_true", help="写 learner 区块（画像采集专线）")
    form.add_argument("--summary", action="store_true", help="置 summary.generated（结业专线）")
    u.add_argument("--status", default=None,
                   help="session 形态：目标状态（未开始|进行中|已完成）")
    u.add_argument("--score", type=int, default=None,
                   help="session 形态：quiz 分 0-100（仅 --status 已完成；session 7 无 quiz）")
    u.add_argument("--notes", default=None,
                   help="session 形态：笔记路径，固定命名 notes/session-<NN>.md（文件须在场）")
    u.add_argument("--topics", type=int, default=None,
                   help="session 形态：探索主题数（仅 session 7；完成判据 >= min_topics）")
    u.add_argument("--role", default=None, help="learner 形态：角色（QA|开发|组长|负责人）")
    u.add_argument("--experience", default=None,
                   help="learner 形态：经验等级（learning_paths 的键）")
    u.add_argument("--goals", action="append", default=None,
                   help="learner 形态：学习目标（可重复）")
    u.add_argument("--pain-points", action="append", default=None,
                   help="learner 形态：当前痛点（可重复）")
    u.add_argument("--path", default=None, help="summary 形态：结业摘要路径（completion-summary.md）")
    u.add_argument("--project-root", default=".", help="项目根（默认 .）")
    u.add_argument("--output-dir", required=True, help="产物目录（必填）")
    u.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    u.set_defaults(func=cmd_update)

    k = sub.add_parser("check", help="进度文件校验（schema/派生三式/score/topics/notes/learner）；"
                                     "--final 附加 7 节齐 + 摘要置位 + 摘要文件在场")
    k.add_argument("--final", action="store_true",
                   help="结业门校验：sessions_completed == 7 且 summary.generated == true"
                        " 且 summary.path 文件在场")
    k.add_argument("--project-root", default=".", help="项目根（默认 .）")
    k.add_argument("--output-dir", required=True, help="产物目录（必填）")
    k.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    k.set_defaults(func=cmd_check)
    return ap


# trace: B3 diy-teach-me-testing 旗标组合纪律（形态专属旗标配错形态 → 用法错误 exit 2）
def check_flag_forms(parser, args):
    session_flags = ("status", "score", "notes", "topics")
    learner_flags = ("role", "experience", "goals", "pain_points")

    def given(names):
        return [name for name in names if getattr(args, name) is not None]

    if args.learner:
        bad = given(session_flags + ("path",))
        if bad:
            parser.error("--learner 形态不接 --%s" % " --".join(bad))
        return
    if args.summary:
        bad = given(session_flags + learner_flags)
        if bad:
            parser.error("--summary 形态不接 --%s" % " --".join(bad))
        if args.path is None:
            parser.error("--summary 形态须给 --path（completion-summary.md）")
        return
    bad = given(learner_flags + ("path",))
    if bad:
        parser.error("--session 形态不接 --%s" % " --".join(bad))
    if not given(session_flags):
        parser.error("--session 形态须至少给 --status / --score / --notes / --topics 之一")


# trace: B3 diy-teach-me-testing 入口（stdout/stderr 固定 UTF-8；退出码由子命令返回）
def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    parser = build_parser()
    args = parser.parse_args()
    if args.cmd == "update":
        check_flag_forms(parser, args)
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
