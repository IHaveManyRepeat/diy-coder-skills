# -*- coding: utf-8 -*-
"""diy-teach-me-testing 常量表与通用工具：路径/枚举/正则/入口常量、损坏探测与备份、人读收尾、课程装载与派生三式。."""

import datetime
import math
import os
import re
import shutil

import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import display_path, is_int, load_yaml_safe, nonempty, v  # noqa: E402

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

# trace: B3 diy-teach-me-testing 非空判定（None / 空白字符串均视为空）

# trace: B3 diy-teach-me-testing 整数判定（布尔不得充当整数：true 不是 1）

# trace: B3 diy-teach-me-testing 日期口径（today = YYYY-MM-DD，对齐契约 §3）

# trace: B3 diy-teach-me-testing YAML 安全装载：(data, err)；缺失 (None, None)、空 ({}, None)、损坏 (None, 原因)

# trace: B3 diy-teach-me-testing 原子写（全文 load → 就地改 → dump → 同目录 tmp + os.replace）

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
