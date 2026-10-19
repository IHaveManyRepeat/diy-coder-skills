# -*- coding: utf-8 -*-
"""diy-retrospective 共享层：常量表/正则、文档装载、epic/story 机械采集与指标单一计算源（collect_metrics/check_metrics）。."""

import os
import re

import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import display_path, id_sort, is_int, items, load_yaml_safe, nonempty, v  # noqa: E402

RETRO_FILE = "retrospective.yaml"
STORIES_FILE = "stories.yaml"
EPICS_FILE = "epics.yaml"
SPRINT_FILE = "sprint.yaml"
TEST_PLAN_FILE = "test-plan.yaml"
BUG_LOG_FILE = "bug-log.yaml"

# 门禁件（文件名 → 是否要求 project.status: 已定稿）
GATE_FILES = ((STORIES_FILE, True), (EPICS_FILE, True))
ROUTE_BY_FILE = {STORIES_FILE: "diy-epics-stories", EPICS_FILE: "diy-epics-stories"}

RECORD_STATUSES = ("草稿", "已定稿")
ACTION_CATEGORIES = ("流程", "技术", "文档", "团队")
PREP_CLASSES = ("关键", "可并行", "锦上添花")
FOLLOWUP_STATUSES = ("已完成", "部分完成", "未完成")
READINESS_KEYS = ("testing", "deployment", "acceptance", "tech_health", "blockers")
METRIC_INT_KEYS = ("stories_total", "stories_done", "rounds_total", "blocked_count",
                   "augment_fail")
BUG_CLASSES = ("功能型", "非功能型")
TEXT_LIST_KEYS = ("wins", "challenges", "insights")

EPIC_RE = re.compile(r"E-\d+")
RT_RE = re.compile(r"RT-\d{3}")
AI_RE = re.compile(r"AI-\d{3}")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
STORY_TOKEN_RE = re.compile(r"S-\d+")
BUG_TOKEN_RE = re.compile(r"BUG-\d{3}")

PATTERN_MIN_COUNT = 2  # 源 step-2：跨 story 才成模式（≥2 处证据）

# ---------------------------------------------------------------- 文档装载

def load_docs(out_dir):
    """一次性装载六份文档：{文件名: {"present", "data", "err"}}（只读，不落盘）。"""
    docs = {}
    for filename in (STORIES_FILE, EPICS_FILE, SPRINT_FILE, TEST_PLAN_FILE,
                     BUG_LOG_FILE, RETRO_FILE):
        data, err = load_yaml_safe(os.path.join(out_dir, filename))
        docs[filename] = {"present": data is not None or err is not None,
                          "data": data, "err": err}
    return docs

def doc_of(docs, filename):
    entry = docs.get(filename) or {}
    return entry.get("data") if entry.get("err") is None else None

def doc_summaries(docs, project_root, out_dir):
    """docs 回执键（短名 = 文件名去 .yaml）：在场 / 可解析 / project.status。"""
    summaries = {}
    for filename, entry in docs.items():
        status = None
        data = entry.get("data")
        if isinstance(data, dict) and isinstance(data.get("project"), dict):
            status = data["project"].get("status")
        summaries[filename[:-len(".yaml")]] = {
            "file": filename, "found": entry["present"], "parsable": entry["err"] is None,
            "status": status,
            "path": display_path(os.path.join(out_dir, filename), project_root)}
    return summaries

def normalize_epic(value):
    """epic 参数归一：接受 `E-3` 与 `3`；其余 → None。"""
    raw = str(value).strip()
    if EPIC_RE.fullmatch(raw):
        return raw
    if raw.isdigit():
        return "E-%d" % int(raw)
    return None

def epic_number(epic):
    m = re.search(r"\d+", str(epic))
    return int(m.group(0)) if m else -1

def epic_entries(docs):
    return [e for e in items(doc_of(docs, EPICS_FILE), "epics") if isinstance(e, dict)]

def epic_ids(docs):
    return {str(e["id"]) for e in epic_entries(docs) if nonempty(e.get("id"))}

def story_entries(docs):
    return [s for s in items(doc_of(docs, STORIES_FILE), "stories") if isinstance(s, dict)]

def story_ids_of_epic(epic, docs):
    return [str(s["id"]) for s in story_entries(docs)
            if str(s.get("epic")) == epic and nonempty(s.get("id"))]

def story_status_map(docs):
    return {str(s["id"]): s.get("status") for s in story_entries(docs)
            if nonempty(s.get("id"))}

def task_entries(docs):
    return [t for t in items(doc_of(docs, SPRINT_FILE), "tasks") if isinstance(t, dict)]

def ac_refs_of(story, key="refs"):
    """story 的 AC refs 全集（引用式：只取 ID，不复制文本）。"""
    refs = []
    for ac in items(story, "acceptance_criteria"):
        if isinstance(ac, dict):
            refs += [str(r) for r in items(ac, key) if nonempty(r)]
    return refs

# ---------------------------------------------------------------- 机械采集

def epic_stories_block(epic, docs):
    """该 epic 的 story 完成度块（源 step-1 完成度校验的机械面）。"""
    status = story_status_map(docs)
    ids = story_ids_of_epic(epic, docs)
    done = [i for i in ids if status.get(i) == "已完成"]
    pending = [{"id": i, "status": status.get(i)} for i in ids if status.get(i) != "已完成"]
    return {"total": len(ids), "done": len(done), "ids": ids, "done_ids": done,
            "pending": pending}

def epic_tasks(epic, docs):
    ids = set(story_ids_of_epic(epic, docs))
    return [t for t in task_entries(docs) if str(t.get("story")) in ids]

def sum_rounds(tasks):
    total = 0
    for task in tasks:
        loop = task.get("loop")
        if isinstance(loop, dict) and is_int(loop.get("rounds")) and loop["rounds"] > 0:
            total += loop["rounds"]
    return total

def epic_bugs(epic, docs):
    """bug-log 中 story 归属该 epic 的缺陷（story 值可为 `S-7/S-9` 复合形态 → 取 token）。"""
    ids = set(story_ids_of_epic(epic, docs))
    out = []
    for bug in items(doc_of(docs, BUG_LOG_FILE), "bugs"):
        if not isinstance(bug, dict):
            continue
        tokens = STORY_TOKEN_RE.findall(str(bug.get("story") or ""))
        if not tokens or not any(tok in ids for tok in tokens):
            continue
        out.append({"id": bug.get("id"), "class": bug.get("class"),
                    "subclass": bug.get("subclass"), "type": bug.get("type"),
                    "story": bug.get("story"), "symptom": bug.get("symptom")})
    return out

def bug_counts(bugs):
    counts = {name: 0 for name in BUG_CLASSES}
    for bug in bugs:
        name = str(bug.get("class"))
        if name in counts:
            counts[name] += 1
    return counts

def epic_coverage(epic, docs):
    """test-plan 对该 epic AC 的覆盖统计（covered = 有 ≥1 条 TC 绑定）。"""
    acs = []
    for story in story_entries(docs):
        if str(story.get("epic")) != epic:
            continue
        for ac in items(story, "acceptance_criteria"):
            if isinstance(ac, dict) and nonempty(ac.get("id")):
                acs.append(str(ac["id"]))
    ac_set = set(acs)
    tcs = [tc for tc in items(doc_of(docs, TEST_PLAN_FILE), "test_cases")
           if isinstance(tc, dict) and str(tc.get("ac")) in ac_set]
    covered = sorted({str(tc.get("ac")) for tc in tcs})
    gaps = id_sort([ac for ac in ac_set if ac not in set(covered)])
    return {"acs": len(ac_set), "covered": len(covered), "gaps": gaps, "tcs": len(tcs)}

def collect_metrics(epic, docs):
    """指标单一计算源——collect 与 check --final 共用（口径互证）。"""
    block = epic_stories_block(epic, docs)
    tasks = epic_tasks(epic, docs)
    bugs = epic_bugs(epic, docs)
    return {
        "stories_total": block["total"],
        "stories_done": block["done"],
        "rounds_total": sum_rounds(tasks),
        "blocked_count": len([t for t in tasks if t.get("status") == "已阻塞"]),
        "augment_fail": len([t for t in tasks if t.get("augment") == "失败"]),
        "bugs": bug_counts(bugs),
    }

def prev_actions(epic, docs):
    """前一份 retro 的 action_items 回带（源 step-3 承诺跟踪的输入）。"""
    target = epic_number(epic)
    earlier = [e for e in epic_entries(docs)
               if nonempty(e.get("id")) and epic_number(e["id"]) < target]
    if not earlier:
        return True, []
    prev = max(earlier, key=lambda e: epic_number(e["id"]))
    prev_id = str(prev["id"])
    record = None
    for rec in items(doc_of(docs, RETRO_FILE), "retros"):
        if isinstance(rec, dict) and str(rec.get("epic")) == prev_id:
            record = rec   # 同 epic 多份取最后一份（追加式，最新在后）
    if record is None:
        return True, []
    out = []
    for action in items(record, "action_items"):
        if not isinstance(action, dict):
            continue
        out.append({"retro": record.get("id"), "id": action.get("id"),
                    "action": action.get("action"), "owner": action.get("owner"),
                    "done_when": action.get("done_when"),
                    "category": action.get("category")})
    return False, out

def next_epic_info(epic, docs):
    """下一 epic 存在性 + 与当前 epic 的共享 FR（源 step-4 预览的机械钩子）。"""
    target = epic_number(epic)
    later = [e for e in epic_entries(docs)
             if nonempty(e.get("id")) and epic_number(e["id"]) > target]
    if not later:
        return {"id": None, "exists": False, "title": None, "stories": [], "shared_frs": []}
    nxt = min(later, key=lambda e: epic_number(e["id"]))
    nxt_id = str(nxt["id"])
    current_frs = set()
    for story in story_entries(docs):
        if str(story.get("epic")) == epic:
            current_frs.update(ac_refs_of(story))
    next_frs = set()
    for story in story_entries(docs):
        if str(story.get("epic")) == nxt_id:
            next_frs.update(ac_refs_of(story))
    nxt_stories = [s for s in story_entries(docs) if str(s.get("epic")) == nxt_id]
    return {"id": nxt_id, "exists": True, "title": nxt.get("title"),
            "stories": [str(s.get("id")) for s in nxt_stories],
            "shared_frs": id_sort(current_frs & next_frs)}

def check_metrics(record, where, final, docs, epic):
    violations = []
    metrics = record.get("metrics")
    if not isinstance(metrics, dict):
        return [v("EMPTY_FIELD", where + ".metrics", "metrics 缺失或不是映射")]
    for key in METRIC_INT_KEYS:
        value = metrics.get(key)
        if value is None:
            violations.append(v("EMPTY_FIELD", "%s.metrics.%s" % (where, key),
                                "metrics.%s 缺失" % key))
        elif not is_int(value) or value < 0:
            violations.append(v("ENUM_INVALID", "%s.metrics.%s" % (where, key),
                                "%s 须为非负整数（实为 %s）" % (key, value)))
    bugs = metrics.get("bugs")
    if not isinstance(bugs, dict):
        violations.append(v("EMPTY_FIELD", where + ".metrics.bugs",
                            "metrics.bugs 缺失（须含 功能型 / 非功能型）"))
    else:
        for name in BUG_CLASSES:
            value = bugs.get(name)
            if not is_int(value) or value < 0:
                violations.append(v("ENUM_INVALID", "%s.metrics.bugs.%s" % (where, name),
                                    "%s 须为非负整数（实为 %s）" % (name, value)))
    if final and not epic_is_known(docs, epic):
        return violations
    if final and not violations:
        actual = collect_metrics(epic, docs)
        diff = []
        for key in METRIC_INT_KEYS:
            if metrics.get(key) != actual[key]:
                diff.append("%s 声明 %s ≠ 实际 %s" % (key, metrics.get(key), actual[key]))
        if isinstance(bugs, dict):
            for name in BUG_CLASSES:
                if bugs.get(name) != actual["bugs"][name]:
                    diff.append("bugs.%s 声明 %s ≠ 实际 %s"
                                % (name, bugs.get(name), actual["bugs"][name]))
        if diff:
            violations.append(v("SET_MISMATCH", where + ".metrics",
                                "metrics 与集合真值不符：%s（口径同 collect）"
                                % "；".join(diff)))
    return violations

def epic_is_known(docs, epic):
    return nonempty(epic) and str(epic) in epic_ids(docs)
