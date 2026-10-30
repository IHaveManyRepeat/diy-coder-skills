# -*- coding: utf-8 -*-
"""diy-investigate collect 命令域：VCS 情报、区域扫描、候选面采集与 collect 回执（只读不写）。."""

import io
import os
import shutil
import subprocess

import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import count_by, display_path, emit_via, nonempty, v  # noqa: E402

from investigation_lib import MAX_CANDIDATES, MAX_COMMITS, MAX_LIST_FILES, MAX_SCAN_FILES, SCAN_EXCLUDE_DIRS, SOURCE_EXTS  # noqa: E402

# ---------------------------------------------------------------- VCS 情报

def git_run(root, args):
    """跑一条 git 命令；git 缺席 / 无法启动 → None（调用方降级，不崩）。"""
    if shutil.which("git") is None:
        return None
    try:
        return subprocess.run(["git", "-C", root] + list(args), capture_output=True,
                              text=True, encoding="utf-8", errors="replace")
    except OSError:
        return None

def parse_git_log(text):
    """解析 `git log --pretty=format:%h<US>%ad<US>%s --date=short --name-only` 输出。"""
    commits = []
    current = None
    for line in (text or "").splitlines():
        if "\x1f" in line:
            parts = (line.split("\x1f") + ["", ""])[:3]
            current = {"commit": parts[0].strip(), "date": parts[1].strip() or None,
                       "subject": parts[2].strip(), "files": []}
            commits.append(current)
        elif line.strip() and current is not None:
            current["files"].append(line.strip().replace("\\", "/"))
    return commits

def probe_vcs(root, since, project_root):
    """VCS 情报（git log 首扫）。
    返回 (vcs 块, warnings)。不可用/失败一律 NO_VCS warning 降级。"""
    where = display_path(root, project_root) or "."
    vcs = {"available": False, "head": None, "commits": [], "since": since}
    warnings = []
    if shutil.which("git") is None:
        warnings.append(v("NO_VCS", where, "git 不可用：VCS 情报降级（结构情报不受影响）"))
        return vcs, warnings
    inside = git_run(root, ["rev-parse", "--is-inside-work-tree"])
    if inside is None or inside.returncode != 0 or inside.stdout.strip() != "true":
        warnings.append(v("NO_VCS", where,
                          "项目根不在 git 仓库内：VCS 情报降级（结构情报不受影响）"))
        return vcs, warnings
    head = git_run(root, ["rev-parse", "--short", "HEAD"])
    log_args = ["log", "--pretty=format:%h\x1f%ad\x1f%s", "--date=short",
                "--name-only", "-n", str(MAX_COMMITS)]
    if nonempty(since):
        log_args += ["--since", str(since)]
    log = git_run(root, log_args)
    if log is None or log.returncode != 0:
        tail = " ".join(((log.stderr if log else "") or "").split())[-200:]
        warnings.append(v("NO_VCS", where,
                          "git log 失败：VCS 情报降级（%s）" % (tail or "无输出")))
        return vcs, warnings
    vcs = {"available": True,
           "head": head.stdout.strip() if head is not None and head.returncode == 0 else None,
           "commits": parse_git_log(log.stdout),
           "since": since}
    if not vcs["commits"]:
        warnings.append(v("NO_VCS", where, "git log 无提交（空仓库或 --since 范围内无提交）"))
    return vcs, warnings

# ---------------------------------------------------------------- 结构情报

def scan_source_files(root, out_dir):
    """遍历项目根收集文本类源文件（限定扩展集；排除输出目录与依赖/缓存目录）。"""
    out_key = os.path.normcase(os.path.abspath(out_dir))
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames
                       if d not in SCAN_EXCLUDE_DIRS
                       and os.path.normcase(os.path.abspath(os.path.join(dirpath, d))) != out_key]
        found += [os.path.join(dirpath, name) for name in sorted(filenames)
                  if os.path.splitext(name)[1].lower().lstrip(".") in SOURCE_EXTS]
        if len(found) > MAX_SCAN_FILES:
            return found, True
    return found, False

def count_lines(path):
    """二进制分块计行数（读失败 → None，不崩）。"""
    try:
        total = 0
        with io.open(path, "rb") as f:
            while True:
                chunk = f.read(65536)
                if not chunk:
                    break
                total += chunk.count(b"\n")
        return total
    except OSError:
        return None

def is_under(path, parent):
    try:
        return os.path.commonpath([os.path.abspath(path), os.path.abspath(parent)]) \
            == os.path.abspath(parent)
    except ValueError:
        return False

def is_test_basename(base, stem):
    """测试文件命名约定：test_<stem> / <stem>_test / <stem>.test / <stem>.spec。"""
    lowered = base.lower()
    return (lowered.startswith("test_" + stem) or lowered.startswith(stem + "_test")
            or lowered.startswith(stem + ".test") or lowered.startswith(stem + ".spec"))

def area_targets(root, area, project_root):
    """--area 目标解析：返回 (目标文件绝对路径列表 | None, 是否目录, warnings)。"""
    path = area if os.path.isabs(area) else os.path.join(root, area)
    if not os.path.exists(path):
        return None, False, [v("MISSING_FILE", display_path(path, project_root),
                               "目标区域不存在：结构情报降级（--area 拼写或路径核对后重试）")]
    return path, os.path.isdir(path), []

def build_candidates(targets, all_files, root, project_root):
    """候选面：同名族并行实现（source Outcome 4）+ 测试文件（命名约定）。只列不判。"""
    by_name = {}
    for path in all_files:
        by_name.setdefault(os.path.basename(path), []).append(path)
    candidates = []
    seen = set()
    target_keys = {os.path.normcase(os.path.abspath(t)) for t in targets}
    for target in targets:
        rel_target = display_path(target, project_root)
        stem = os.path.splitext(os.path.basename(target))[0].lower()
        pairs = [("parallel", other, "同名族（与 %s 同名不同路径）" % rel_target)
                 for other in by_name.get(os.path.basename(target), [])]
        pairs += [("test", other, "%s 的测试候选（按命名约定）" % rel_target)
                  for other in all_files
                  if is_test_basename(os.path.basename(other), stem)]
        for kind, other, note in sorted(pairs):
            key = (kind, os.path.normcase(other))
            if key in seen or os.path.normcase(other) in target_keys:
                continue
            seen.add(key)
            candidates.append({"file": display_path(other, project_root),
                               "kind": kind, "note": note})
    candidates.sort(key=lambda c: (c["kind"], c["file"]))
    return candidates

def collect_structure(root, out_dir, area, project_root):
    """结构情报：区域文件清单 + 同名族/测试候选面。返回 (files, candidates, warnings)。"""
    if not nonempty(area):
        return [], [], []
    target, is_dir, warnings = area_targets(root, area, project_root)
    if target is None:
        return [], [], warnings
    where = display_path(target, project_root)
    all_files, truncated = scan_source_files(root, out_dir)
    if truncated:
        warnings.append(v("SCAN_TRUNCATED", display_path(root, project_root),
                          "文件扫描达上限 %d：候选面不完整（缩小 --area 范围重试）"
                          % MAX_SCAN_FILES))
    targets = [f for f in all_files if is_under(f, target)] if is_dir else [target]
    if len(targets) > MAX_LIST_FILES:
        warnings.append(v("SCAN_TRUNCATED", where, "区域文件 %d 个超清单上限 %d：仅列前 %d 个"
                          % (len(targets), MAX_LIST_FILES, MAX_LIST_FILES)))
    files = [{"path": display_path(f, project_root), "lines": count_lines(f)}
             for f in sorted(targets)[:MAX_LIST_FILES]]
    candidates = build_candidates(targets, all_files, root, project_root)
    if len(candidates) > MAX_CANDIDATES:
        warnings.append(v("SCAN_TRUNCATED", where, "候选面 %d 条超上限 %d：仅保留前 %d 条"
                          % (len(candidates), MAX_CANDIDATES, MAX_CANDIDATES)))
        candidates = candidates[:MAX_CANDIDATES]
    return files, candidates, warnings

# ---------------------------------------------------------------- collect

def cmd_collect(args):
    root = os.path.abspath(args.project_root)
    out = os.path.abspath(args.output_dir)
    vcs, warnings = probe_vcs(root, args.since, root)
    files, candidates, struct_warnings = collect_structure(root, out, args.area, root)
    warnings += struct_warnings
    payload = {"ok": True, "command": "collect", "project_root": args.project_root,
               "output_dir": os.path.normpath(out).replace("\\", "/"),
               "area": args.area, "since": args.since, "vcs": vcs, "files": files,
               "candidates": candidates, "violations": [], "warnings": warnings,
               "counts": {"commits": len(vcs["commits"]), "files": len(files),
                          "candidates": len(candidates),
                          "by_kind": count_by(candidates, "kind")}}
    emit_via(payload, args.json, human_collect)
    return 0

def human_collect(payload):
    counts = payload["counts"]
    if payload["vcs"]["available"]:
        print("VCS：可用（head %s，近期提交 %d 条）"
              % (payload["vcs"]["head"] or "无", counts["commits"]))
    else:
        print("VCS：不可用（降级——见 warnings）")
    if payload["area"]:
        print("区域 %s：文件 %d 个 · 候选面 %d 条"
              % (payload["area"], counts["files"], counts["candidates"]))
    else:
        print("未给 --area：跳过结构情报（只做 VCS 采集）")
    for warning in payload["warnings"]:
        print("警告 %s %s: %s" % (warning["code"], warning["where"], warning["msg"]))
