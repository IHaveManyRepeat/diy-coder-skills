# -*- coding: utf-8 -*-
"""diyc trace 注释引用审计（契约 §4.3）。"""

import io
import os
import re

import diyc_lib  # noqa: E402
from diyc_lib import receipt, rel_path, v  # noqa: E402

# trace 扫描：文件扩展集与目录排除（契约 §4.3）
TRACE_SCAN_EXTS = {".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".go", ".rs",
                   ".java", ".kt", ".kts", ".cs", ".c", ".cc", ".cpp", ".cxx",
                   ".h", ".hpp", ".rb", ".php", ".swift", ".m", ".mm"}
TRACE_EXCLUDE_DIRS = {".git", ".claude", ".analysis", "node_modules", "__pycache__",
                      ".venv", "venv", "dist", "build"}
# 注释符紧邻 trace:（`# trace:` / `// trace:`）；括号内文本才是引用区
TRACE_LINE_RE = re.compile(r"(?:#|//)\s*trace:(.*)$")
TRACE_TOKENS = None  # 延迟绑定 diyc_lib 的正则常量

# ---------------------------------------------------------------- trace

def _token_specs():
    global TRACE_TOKENS
    if TRACE_TOKENS is None:
        TRACE_TOKENS = [(diyc_lib.STORY_RE, "story"), (diyc_lib.AC_RE, "ac"),
                        (diyc_lib.TC_RE, "tc"), (diyc_lib.DEC_RE, "decision")]
    return TRACE_TOKENS


def _extract_ids(text):
    """一行注释内提取引用 ID：返回 ([ids 按出现顺序去重], {id: kind})。"""
    hits = []
    for regex, kind in _token_specs():
        for m in regex.finditer(text):
            hits.append((m.start(), m.group(0), kind))
    hits.sort(key=lambda x: x[0])
    ids, kinds = [], {}
    for _, id_, kind in hits:
        if id_ not in kinds:
            kinds[id_] = kind
            ids.append(id_)
    return ids, kinds


def _scan_trace_file(path):
    """返回 [(行号, ids, kind_by_id)]；仅注释形态行，无 ID 行不计。"""
    try:
        with io.open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.read().splitlines()
    except OSError:
        return []
    out = []
    for lineno, line in enumerate(lines, 1):
        m = TRACE_LINE_RE.search(line)
        if not m:
            continue
        ids, kinds = _extract_ids(m.group(1))
        if ids:
            out.append((lineno, ids, kinds))
    return out


def _walk_trace_files(base, exclude_output_abs=None):
    for dirpath, dirnames, filenames in os.walk(base):
        for d in list(dirnames):
            if d in TRACE_EXCLUDE_DIRS:
                dirnames.remove(d)
                continue
            if exclude_output_abs is not None and os.path.normcase(
                    os.path.abspath(os.path.join(dirpath, d))) == exclude_output_abs:
                dirnames.remove(d)
        for f in filenames:
            if os.path.splitext(f)[1].lower() in TRACE_SCAN_EXTS:
                yield os.path.join(dirpath, f)


def _trace_targets(args):
    """待扫文件清单：默认 project-root（排除 output_dir/VCS 等）；--src 给定则只扫它们。"""
    root = args.project_root
    if args.src:
        for s in args.src:
            p = s if os.path.isabs(s) else os.path.join(root, s)
            if os.path.isdir(p):
                yield from _walk_trace_files(p)
            elif os.path.isfile(p):
                if os.path.splitext(p)[1].lower() in TRACE_SCAN_EXTS:
                    yield p
        return
    exclude = os.path.normcase(os.path.abspath(args.output_dir))
    yield from _walk_trace_files(root, exclude_output_abs=exclude)


def cmd_trace(args) -> dict:
    # trace: S-8 AC-8.1 引用审计（diy-review L1 的机械读取）
    docs = diyc_lib.Docs(args.project_root, args.output_dir)
    story_ids, ac_ids = set(docs.stories()), set(docs.acs())
    tc_ids = set(docs.tcs())
    dec_ids = set(docs.decisions())
    arch_exists = docs.doc("architecture") is not None

    references, unresolved = [], []
    files_with_trace = 0
    seen_kinds = set()
    for path in _trace_targets(args):
        rel = rel_path(args.project_root, path)
        hits = _scan_trace_file(path)
        if hits:
            files_with_trace += 1
        for lineno, ids, kinds in hits:
            references.append({"file": rel, "line": lineno, "ids": ids})
            for id_ in ids:
                kind = kinds[id_]
                seen_kinds.add(kind)
                if kind == "story":
                    ok = id_ in story_ids
                elif kind == "ac":
                    ok = id_ in ac_ids
                elif kind == "tc":
                    ok = id_ in tc_ids
                else:
                    ok = (not arch_exists) or (id_ in dec_ids)
                if not ok:
                    unresolved.append({"file": rel, "line": lineno,
                                       "id": id_, "kind": kind})
    references.sort(key=lambda r: (r["file"], r["line"]))
    unresolved.sort(key=lambda u: (u["file"], u["line"], u["id"]))
    warnings = []
    if ({"story", "ac"} & seen_kinds) and docs.doc("stories") is None:
        warnings.append("stories.yaml 缺失/损坏，story/ac 引用无法解析")
    if "tc" in seen_kinds and docs.doc("test-plan") is None:
        warnings.append("test-plan.yaml 缺失/损坏，tc 引用无法解析")
    violations = [v("TRACE_UNRESOLVED", "%s:%d" % (u["file"], u["line"]),
                    "%s（%s）在产物索引中不存在" % (u["id"], u["kind"]))
                  for u in unresolved]
    counts = {"refs": sum(len(r["ids"]) for r in references),
              "files_with_trace": files_with_trace, "unresolved": len(unresolved)}
    return receipt("trace", not unresolved, references=references,
                   unresolved=unresolved, violations=violations,
                   warnings=warnings, counts=counts)


def _human_trace(result) -> list:
    c = result["counts"]
    return ["引用 %d 条，%d 个文件含 trace，未解析 %d 条"
            % (c.get("refs", 0), c.get("files_with_trace", 0), c.get("unresolved", 0))]
