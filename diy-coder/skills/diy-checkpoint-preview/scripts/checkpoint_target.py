# -*- coding: utf-8 -*-
"""diy-checkpoint-preview 变更候选定位域：常量表、git 只读层与 target 四层级联命令。."""

import json
import os
import re
import subprocess

import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import display_path, load_yaml_safe, nonempty, v  # noqa: E402

CK_FILE = "checkpoint.yaml"
SPRINT_FILE = "sprint.yaml"
STORIES_FILE = "stories.yaml"

TARGET_SOURCES = ("显式指定", "冲刺任务", "Git 提交")
MODES = ("全程轨迹", "仅规格", "裸提交")
DECISIONS = ("批准", "返工", "讨论")
RECORD_STATUSES = ("草稿", "已定稿")
RISK_LABELS = ("认证", "公开 API", "数据模型", "计费", "基础设施", "安全",
               "配置", "其他")
WORKTREE_REF = "WORKTREE"

CK_RE = re.compile(r"CK-\d{3}")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
# BMAD step-01-orientation.md:54 —— "commit message is terse (under 10 words)" → 标 [inferred]
TERSE_WORDS = 10

# ---- git 层（只读；任何失败都降级为结构化原因，不抛异常） ----

def git(root, *args):
    """执行 git 子命令 → (rc, stdout, stderr)；git 可执行文件不可用 → (None, "", 原因)。"""
    try:
        p = subprocess.run(["git", "-C", root] + list(args),
                           capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
    except OSError as e:
        return None, "", str(e)
    return p.returncode, p.stdout, p.stderr

def is_git_repo(root):
    rc, out, _ = git(root, "rev-parse", "--is-inside-work-tree")
    return rc == 0 and out.strip() == "true"

def numstat_totals(root, *git_args):
    """git --numstat 输出聚合 → (files, insertions, deletions)；失败 → 全 0。"""
    rc, out, _ = git(root, *git_args)
    if rc != 0:
        return 0, 0, 0
    files = ins = dele = 0
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        files += 1
        ins += int(parts[0]) if parts[0].isdigit() else 0
        dele += int(parts[1]) if parts[1].isdigit() else 0
    return files, ins, dele

def commit_subject(root, ref):
    """单一提交的 subject 行；取不到（未知 ref / 非提交对象）→ None。"""
    rc, out, _ = git(root, "log", "-1", "--format=%s", ref)
    if rc != 0:
        return None
    return out.strip() or None

def intent_flag(root, commit_ref):
    """BMAD step-01 bare-commit 语义：意图源 = 提交信息；terse（< 10 词）→ 标 [inferred]。

    返回 (inferred, reason)：True/False = 已判定；None = 无单一提交信息可判定
    （工作区未提交改动 / range），交由人从 diff 核对。
    """
    subject = commit_subject(root, commit_ref)
    if subject is None:
        return None, "无单一提交信息可判定，意图从 diff 推断，请人工核对"
    words = len(subject.split())
    if words < TERSE_WORDS:
        return True, ("提交信息过短（%d 词 < %d），意图从 diff 推断，请人工核对"
                      % (words, TERSE_WORDS))
    return False, None

def candidate(ref, source, story=None, spec=None, mode="裸提交", diff_stat=None,
              inferred=None, inferred_reason=None):
    return {"ref": ref, "source": source, "story": story, "spec": spec,
            "mode": mode, "diff_stat": diff_stat,
            "inferred": inferred, "inferred_reason": inferred_reason}

def stat_dict(files, ins, dele):
    return {"files": files, "insertions": ins, "deletions": dele}

def explicit_candidate(root, ref):
    """层 1：显式 ref。返回 (候选 | None, 原因)。PR 引用无法本地解析 → 拒绝并给路由。"""
    if not is_git_repo(root):
        return None, "--ref %s 无法解析：项目不是 git 仓库" % ref
    if ".." in ref:
        rc, out, _ = git(root, "rev-list", "--count", ref)
        if rc != 0 or not out.strip():
            return None, "--ref %s 无法解析为 git range" % ref
        files, ins, dele = numstat_totals(root, "diff", "--numstat", ref)
        return candidate(ref, "显式指定", diff_stat=stat_dict(files, ins, dele),
                         inferred=None,
                         inferred_reason="range 无单一提交信息，意图从 diff 推断，请人工核对"), None
    rc, out, _ = git(root, "rev-parse", "--verify", "--quiet", ref + "^{commit}")
    if rc != 0 or not out.strip():
        return None, ("--ref %s 无法解析（PR 引用请先用 gh 解析为本地 commit/分支）" % ref)
    files, ins, dele = numstat_totals(root, "show", "--numstat", "--format=", ref)
    inferred, reason = intent_flag(root, ref)
    return candidate(ref, "显式指定", diff_stat=stat_dict(files, ins, dele),
                     inferred=inferred, inferred_reason=reason), None

def load_story_index(output_dir):
    """story 索引：{story_id: stories.yaml 条目 | None}。上游文件损坏 → warnings（不静默）。"""
    index = {}
    warnings = []
    sources = ((STORIES_FILE, "stories", None), (SPRINT_FILE, "tasks", "story"))
    for filename, key, sub in sources:
        path = os.path.join(output_dir, filename)
        data, err = load_yaml_safe(path)
        if err is not None:
            warnings.append(v("UNPARSABLE_YAML", filename,
                              "上游文档不可解析，story 引用无法核验：%s" % err))
            continue
        items = data.get(key) if isinstance(data, dict) else None
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            sid = item.get(sub) if sub else item.get("id")
            if nonempty(sid):
                index.setdefault(str(sid), None if sub else item)
    return index, warnings

def sprint_candidates(output_dir, project_root):
    """层 2：sprint.yaml 中 status: 待审查 的任务（取其 story 与 spec 锚点）。"""
    path = os.path.join(output_dir, SPRINT_FILE)
    data, err = load_yaml_safe(path)
    if data is None and err is None:
        return [], [], "%s 不存在" % display_path(path, project_root)
    if err is not None:
        return [], [], "%s 不可解析" % display_path(path, project_root)
    tasks = data.get("tasks") if isinstance(data, dict) else None
    if not isinstance(tasks, list):
        return [], [], "%s 无 tasks 列表" % display_path(path, project_root)
    reviews = [t for t in tasks if isinstance(t, dict) and t.get("status") == "待审查"]
    if not reviews:
        return [], [], "%s 中无 status: 待审查 的任务" % display_path(path, project_root)
    index, warnings = load_story_index(output_dir)
    stories_path = os.path.join(output_dir, STORIES_FILE)
    cands = []
    for task in reviews:
        sid = task.get("story")
        entry = index.get(str(sid)) if nonempty(sid) else None
        if entry is not None:
            spec = display_path(stories_path, project_root)
            # 全程轨迹仅在 spec 携带审查顺序（suggested_review_order 非空）时成立
            mode = "全程轨迹" if entry.get("suggested_review_order") else "仅规格"
        else:
            spec, mode = None, "裸提交"
        # 冲刺任务候选的意图锚点是 story/spec，不走提交信息判定（[inferred] 属裸提交路径）
        cands.append(candidate(None, "冲刺任务", story=str(sid) if nonempty(sid) else None,
                               spec=spec, mode=mode))
    return cands, warnings, "命中 %d 个 status: 待审查 的任务" % len(cands)

def git_candidates(root):
    """层 3：git 工作区改动 → HEAD 提交。返回 (候选列表, 原因)。"""
    if not is_git_repo(root):
        return [], "非 git 仓库（或 git 不可用）"
    rc, out, _ = git(root, "status", "--porcelain")
    if rc != 0:
        return [], "git status 执行失败"
    changed = [line for line in out.splitlines() if line.strip()]
    if changed:
        head_ok = git(root, "rev-parse", "--verify", "--quiet", "HEAD")[0] == 0
        args = ["diff", "--numstat", "HEAD"] if head_ok else ["diff", "--numstat"]
        _, ins, dele = numstat_totals(root, *args)
        return [candidate(WORKTREE_REF, "Git 提交",
                          diff_stat=stat_dict(len(changed), ins, dele),
                          inferred=None,
                          inferred_reason="工作区未提交改动无提交信息，意图从 diff 推断，请人工核对"
                          )], None
    rc, out, _ = git(root, "rev-parse", "--short", "HEAD")
    if rc == 0 and out.strip():
        sha = out.strip()
        files, ins, dele = numstat_totals(root, "show", "--numstat", "--format=", "HEAD")
        inferred, reason = intent_flag(root, "HEAD")
        return [candidate(sha, "Git 提交", diff_stat=stat_dict(files, ins, dele),
                          inferred=inferred, inferred_reason=reason)], None
    return [], "git 仓库无提交且工作区干净（无 diff）"

# ---- target 收口 ----

def cmd_target(args):
    root = os.path.abspath(args.project_root)
    out = args.output_dir
    checked = []
    warnings = []
    candidates = []

    if nonempty(args.ref):
        cand, why = explicit_candidate(root, args.ref)
        checked.append({"source": "显式指定", "hit": cand is not None, "reason": why})
        if cand is not None:
            candidates.append(cand)
    else:
        checked.append({"source": "显式指定", "hit": False, "reason": "未提供 --ref"})

    if not candidates:
        cands, warns, why = sprint_candidates(out, root)
        warnings += warns
        checked.append({"source": "冲刺任务", "hit": bool(cands), "reason": why})
        candidates += cands

    if not candidates:
        cands, why = git_candidates(root)
        checked.append({"source": "Git 提交", "hit": bool(cands), "reason": why})
        candidates += cands

    ok = bool(candidates)
    first = candidates[0] if candidates else {}
    reason = None
    violations = []
    if not ok:
        reason = ("未定位到被审变更：%s。请显式传 --ref（commit / range / 分支），"
                  "或先跑 diy-dev / diy-review 使任务进入 待审查 后重试。"
                  % "；".join(c["reason"] for c in checked))
        violations = [v("NO_TARGET", display_path(os.path.join(out, CK_FILE), root), reason)]
    payload = {
        "ok": ok,
        "command": "target",
        "project_root": args.project_root,
        "output_dir": os.path.normpath(out).replace("\\", "/"),
        "ref": first.get("ref"),
        "source": first.get("source"),
        "mode": first.get("mode"),
        "story": first.get("story"),
        "spec": first.get("spec"),
        "diff_stat": first.get("diff_stat"),
        "inferred": first.get("inferred"),
        "inferred_reason": first.get("inferred_reason"),
        "candidates": candidates,
        "checked": checked,
        "violations": violations,
        "warnings": warnings,
        "reason": reason,
        "counts": {"candidates": len(candidates)},
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        if ok:
            print("已定位被审变更候选 %d 个（首选项 source=%s）：" % (len(candidates),
                                                              first.get("source")))
            for c in candidates:
                detail = c.get("story") or c.get("ref") or "-"
                flag = " [inferred]" if c.get("inferred") else ""
                print("- [%s] %s spec=%s mode=%s%s" % (c["source"], detail,
                                                       c.get("spec"), c["mode"], flag))
        else:
            print("拒绝：%s" % reason)
    return 0 if ok else 1
