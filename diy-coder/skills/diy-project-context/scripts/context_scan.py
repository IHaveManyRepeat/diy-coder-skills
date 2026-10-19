# -*- coding: utf-8 -*-
"""diy-project-context scan 命令域：探测装配、人读输出与 scan 回执。."""

import json
import os

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import display_path, load_yaml_safe, v  # noqa: E402

from context_lib import CTX_FILE, EXCLUDE_DIRS, SCAN_LEVELS, slash  # noqa: E402

from context_probes import build_part, critical_dirs, detect_parts, find_docs, render_tree  # noqa: E402

def cmd_scan(args):
    root = os.path.abspath(args.project_root)
    out = args.output_dir
    violations = []
    warnings = []
    if not os.path.isdir(root):
        violations.append(v("MISSING_FILE", display_path(root, os.path.dirname(root) or root),
                            "项目根不存在：%s（扫描拒绝，零产出）" % slash(root)))
        return emit_scan(args, None, [], [], [], "", violations, warnings, "")

    # 产物目录属扫描对象之外（扫描的是代码库，不是 diy 自身产物）：按名排除
    excludes = frozenset(EXCLUDE_DIRS | {os.path.basename(os.path.abspath(out))})
    candidates, repository_type, part_warnings = detect_parts(root, excludes)
    warnings += part_warnings
    if args.part:
        wanted = [c for c in candidates if c[0] == args.part]
        if not wanted:
            violations.append(v("UNKNOWN_ID", "parts",
                                "部件 %s 不存在（候选：%s）"
                                % (args.part, ", ".join(c[0] for c in candidates))))
            return emit_scan(args, repository_type, [], [], [], "", violations, warnings,
                             args.part)
        candidates = wanted

    parts = []
    stack = []
    stats = {}
    dirs_by_part = []
    for name, path in candidates:
        part, entry, part_stats, part_warn = build_part(root, name, path, args.level, excludes)
        parts.append(part)
        stack.append(entry)
        warnings += part_warn
        if part_stats:
            stats[name] = part_stats
        dirs_by_part.append({"part": name,
                             "dirs": critical_dirs(path, part["type"], root)})

    docs = find_docs(root, root, parts, excludes)
    if args.part:
        docs = [d for d in docs if d["part"] in ("", args.part)]
    tree = render_tree(candidates[0][1] if args.part else root, excludes)

    ctx_path = os.path.join(out, CTX_FILE)
    existing = {}
    data, err = load_yaml_safe(ctx_path)
    if isinstance(data, dict) and isinstance(data.get("scan"), dict):
        scan = data["scan"]
        existing = {"mode": scan.get("mode"), "level": scan.get("level"),
                    "date": scan.get("date")}
    elif err is not None:
        warnings.append(v("UNPARSABLE_YAML", display_path(ctx_path, root),
                          "既有 %s 不可解析，模式判定以用户确认为准：%s" % (CTX_FILE, err)))

    counts = {
        "parts": len(parts),
        "stack": len(stack),
        "docs_found": len(docs),
        "tree_lines": len(tree.splitlines()),
    }
    for name, entry in stats.items():
        counts.setdefault("files_by_part", {})[name] = entry["files"]
        counts.setdefault("loc_by_part", {})[name] = entry["loc"]
    counts["files"] = sum(e["files"] for e in stats.values())
    counts["loc"] = sum(e["loc"] for e in stats.values())
    return emit_scan(args, repository_type, parts, stack, docs, tree, violations, warnings,
                     args.part, existing, counts, stats, dirs_by_part)

def emit_scan(args, repository_type, parts, stack, docs, tree, violations, warnings,
              part=None, existing=None, counts=None, stats=None, critical=None):
    ok = not violations
    payload = {
        "ok": ok,
        "command": "scan",
        "project_root": args.project_root,
        "output_dir": os.path.normpath(args.output_dir).replace("\\", "/"),
        "level": args.level,
        "levels": list(SCAN_LEVELS),
        "part": part,
        "repository_type": repository_type,
        "parts": parts,
        "stack": stack,
        "docs_found": docs,
        "tree": tree,
        "critical_dirs": critical or [],
        "stats": stats or {},
        "existing_context": bool(existing),
        "existing_scan": existing or {},
        "violations": violations,
        "warnings": warnings,
        "counts": counts or {"parts": 0, "stack": 0, "docs_found": 0, "tree_lines": 0},
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False))
    elif ok:
        print("PASS：扫描完成（repository_type=%s, parts=%d, docs=%d, level=%s）"
              % (repository_type, len(parts), len(docs), args.level))
        for part_entry in parts:
            print("- %s [%s] %s" % (part_entry["name"], part_entry["type"], part_entry["path"]))
        for doc in docs:
            print("- 文档 %s (%s)" % (doc["path"], doc["kind"]))
        for item in warnings:
            print("- WARN %s %s: %s" % (item["code"], item["where"], item["msg"]))
    else:
        print("拒绝：")
        for item in violations:
            print("- %s %s: %s" % (item["code"], item["where"], item["msg"]))
    return 0 if ok else 1
