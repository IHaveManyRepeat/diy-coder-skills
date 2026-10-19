# -*- coding: utf-8 -*-
"""diy-create-story 常量表与通用工具（路径安全/story 解析/文档装载/门禁/采集读取/git 情报/回执底座）。."""

import os
import re
import subprocess

import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import display_path, id_sort, id_sort_key, items, load_yaml_safe, nonempty, v  # noqa: E402

STORIES_FILE = "stories.yaml"
TEST_PLAN_FILE = "test-plan.yaml"
SPRINT_FILE = "sprint.yaml"
ARCH_FILE = "architecture.yaml"
CONTEXT_FILE = "story-context.yaml"

DIYC_ROUTE = "diy-epics-stories"
SC_RE = re.compile(r"SC-\d{3}")
STORY_RE = re.compile(r"S-(\d+)")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")

RECORD_STATUSES = ("草稿", "已定稿")
FILE_ACTIONS = ("新建", "更新")
CLOSED_PREFIX = "[CLOSED]"
GIT_COMMITS = 5
GIT_FILES_PER_COMMIT = 20
GIT_SEP = "@@"

def rel_to_root(root, rel_path):
    """把产物里的正斜杠相对路径落成磁盘绝对路径。"""
    return os.path.join(root, *str(rel_path).replace("\\", "/").split("/"))

def is_safe_rel(rel_path):
    """相对 project-root 的正斜杠路径（禁绝对路径 / 盘符 / 上跳）。"""
    text = str(rel_path).replace("\\", "/")
    if not text or text.startswith("/") or os.path.isabs(str(rel_path)):
        return False
    return ".." not in text.split("/")

def story_num(story_id):
    """S-x → x（int）；非 story ID → None。"""
    m = STORY_RE.fullmatch(str(story_id)) if nonempty(story_id) else None
    return int(m.group(1)) if m else None

def story_map(doc):
    """stories.yaml → {S-x: 条目}。"""
    result = {}
    for entry in items(doc, "stories"):
        if isinstance(entry, dict) and nonempty(entry.get("id")):
            result[str(entry["id"])] = entry
    return result

def ac_ids(story_entry):
    """该 story 的 AC ID 序列（文件顺序）。"""
    return [str(ac["id"]) for ac in items(story_entry, "acceptance_criteria")
            if isinstance(ac, dict) and nonempty(ac.get("id"))]

# ---------------------------------------------------------------- 文档装载

def load_doc(out_dir, filename):
    data, err = load_yaml_safe(os.path.join(out_dir, filename))
    return {"present": data is not None or err is not None, "data": data, "err": err}

def load_docs(out_dir):
    """一次性装载四份上游文档（只读，不落盘）。"""
    return {name: load_doc(out_dir, name)
            for name in (STORIES_FILE, TEST_PLAN_FILE, SPRINT_FILE, ARCH_FILE)}

def missing_warning(out_dir, filename, note, project_root):
    return v("MISSING_FILE", display_path(os.path.join(out_dir, filename), project_root), note)

# ---------------------------------------------------------------- 门禁

def gate_check(docs, out_dir, project_root, story):
    """门禁：stories.yaml 在场/可解析/定稿，且目标 story 存在。

    返回 (passed, violations, route, story_entry, suggestions)。
    """
    show = display_path(os.path.join(out_dir, STORIES_FILE), project_root)
    entry = docs[STORIES_FILE]
    if not entry["present"]:
        return (False, [v("MISSING_FILE", show, "stories.yaml 不存在；先跑 %s 产出并定稿故事清单" % DIYC_ROUTE)],
                "先跑 %s 产出并定稿 stories.yaml，再重跑本技能" % DIYC_ROUTE, None, [])
    if entry["err"] is not None:
        return (False, [v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % entry["err"])],
                "先修复 stories.yaml 的 YAML 语法，再重跑本技能", None, [])
    data = entry["data"]
    project = data.get("project") if isinstance(data, dict) else None
    status = project.get("status") if isinstance(project, dict) else None
    if status != "已定稿":
        return (False, [v("STATUS_MISMATCH", show + " project.status",
                          "stories.yaml 的 project.status 须为 已定稿（实为 %s）；先跑 %s 定稿"
                          % (status if nonempty(status) else "未声明", DIYC_ROUTE))],
                "先跑 %s 定稿 stories.yaml，再重跑本技能" % DIYC_ROUTE, None, [])
    stories = story_map(data)
    story_entry = stories.get(str(story))
    if story_entry is None:
        todo = [sid for sid, e in stories.items() if e.get("status") != "已完成"]
        return (False, [v("UNKNOWN_ID", show + " stories",
                          "目标 story %s 在 stories.yaml 中不存在" % story)],
                "确认 story ID；若故事尚未定义，先跑 %s 补建" % DIYC_ROUTE, None, id_sort(todo))
    return True, [], None, story_entry, []

# ---------------------------------------------------------------- 采集

def read_tcs(docs, acs):
    """test-plan.yaml 中 ac 属该 story AC 集的用例（摘要级）。"""
    wanted = set(acs)
    result = []
    for tc in items(docs[TEST_PLAN_FILE]["data"], "test_cases"):
        if not isinstance(tc, dict) or not nonempty(tc.get("id")):
            continue
        if str(tc.get("ac")) not in wanted:
            continue
        result.append({k: tc.get(k) for k in ("id", "ac", "title", "type", "priority",
                                              "technique", "status")})
    return sorted(result, key=lambda t: id_sort_key(t["id"]))

def read_prior(docs, story, stories):
    """前序 story = 编号最高且小于当前者；内容取 sprint 任务（缺席则 task 为 None）。"""
    num = story_num(story)
    if num is None:
        return None
    lower = [n for n in (story_num(s) for s in stories) if n is not None and n < num]
    if not lower:
        return None
    ref = "S-%d" % max(lower)
    prior = {"ref": ref, "story_status": stories[ref].get("status"), "task": None}
    for task in items(docs[SPRINT_FILE]["data"], "tasks"):
        if not isinstance(task, dict) or str(task.get("story")) != ref:
            continue
        prior["task"] = {k: task.get(k) for k in ("status", "note", "evidence", "loop",
                                                  "blocked_reason")}
        break
    return prior

def read_decisions(docs):
    """architecture.yaml decisions[] 摘要级（适用面判定留给会话）。"""
    result = []
    for dec in items(docs[ARCH_FILE]["data"], "decisions"):
        if isinstance(dec, dict) and nonempty(dec.get("id")):
            result.append({k: dec.get(k) for k in ("id", "title", "status", "affects")})
    return sorted(result, key=lambda d: id_sort_key(d["id"]))

def git_intel(project_root):
    """最近 GIT_COMMITS 次提交摘要。VCS 不可用 / 无提交 → (block, [NO_VCS warning])。"""
    block = {"available": False, "commits": []}
    cmd = ["git", "-C", project_root, "log", "-n", str(GIT_COMMITS), "--date=short",
           "--name-only", "--pretty=format:" + GIT_SEP + "%h" + chr(9) + "%ad" + chr(9) + "%s"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                              errors="replace")
    except OSError as e:
        return block, [v("NO_VCS", "git log", "VCS 不可用（%s）：git 情报跳过" % e)]
    if proc.returncode != 0:
        return block, [v("NO_VCS", "git log",
                         "VCS 不可用（非 git 仓库或无提交）：git 情报跳过")]
    commits = []
    current = None
    for line in (proc.stdout or "").splitlines():
        if line.startswith(GIT_SEP):
            parts = line[len(GIT_SEP):].split(chr(9))
            current = {"hash": parts[0] if len(parts) > 0 else "",
                       "date": parts[1] if len(parts) > 1 else "",
                       "subject": parts[2] if len(parts) > 2 else "",
                       "files": [], "files_total": 0, "files_truncated": False}
            commits.append(current)
        elif line.strip() and current is not None:
            current["files_total"] += 1
            if len(current["files"]) < GIT_FILES_PER_COMMIT:
                current["files"].append(line.strip().replace("\\", "/"))
            else:
                current["files_truncated"] = True
    block["commits"] = commits
    block["available"] = True
    return block, []

# ---------------------------------------------------------------- collect

def base_payload(command, args, out_dir):
    return {
        "ok": False,
        "command": command,
        "project_root": args.project_root,
        "output_dir": os.path.normpath(out_dir).replace("\\", "/"),
        "violations": [],
        "warnings": [],
        "counts": {},
    }
