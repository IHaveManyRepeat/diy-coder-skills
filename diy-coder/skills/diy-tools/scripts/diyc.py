# -*- coding: utf-8 -*-
"""diyc CLI 入口：全部子命令定义 + 统一收口（契约 §2/§3/§4）。

- 本文件拥有全部 argparse 定义；行为模块只暴露 run(args) -> dict：
  check → diyc_check（懒加载）、写回五命令 → diyc_writeback（懒加载，按 args.command 分派）；
  resolve/trace/static 三个子命令由本文件直接实现。
- 统一收口：解析 output_dir 写入 args.output_dir、设置 args.command、补公共回执键、
  emit 输出并以 exit code 收尾（ok → 0，否则 1；用法错误 2 由 argparse 给出）；
  未预期内部异常（含配置读取失败）→ INTERNAL_ERROR 回执（exit 1，--json 面单行 JSON，
  绝不空 stdout；用法错误 SystemExit 不被捕获，原语义保持）。
- baseline（已知遗留台账）：审计命令（check/trace/static）收口后应用 diyc_lib.apply_baseline
  ——命中 (code, where) 降级 known、悬空条目 BASELINE_STALE；写回命令不消费（D1-D4 裁定 2026-09-13）；
  `baseline-add` 为唯一写入口（D3：仅用户裁定后调用，条目重复/文件损坏拒绝，零半写）。
"""
# trace: S-6 AC-6.2 S-16 AC-16.1

import argparse
import importlib
import io
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import diyc_lib  # noqa: E402
from diyc_lib import receipt, v  # noqa: E402

CHECK_TYPES = ("prd", "architecture", "openapi", "epics", "stories",
               "test-plan", "sprint", "review")
# --previous 稳定 ID 比对仅这些类型支持（契约 §4.2）
PREVIOUS_TYPES = ("prd", "openapi", "epics", "stories", "test-plan")
WRITEBACK_COMMANDS = ("transition", "green", "done", "bug-add", "defer-add", "reconcile")

# trace 扫描：文件扩展集与目录排除（契约 §4.3）
TRACE_SCAN_EXTS = {".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".go", ".rs",
                   ".java", ".kt", ".kts", ".cs", ".c", ".cc", ".cpp", ".cxx",
                   ".h", ".hpp", ".rb", ".php", ".swift", ".m", ".mm"}
TRACE_EXCLUDE_DIRS = {".git", ".claude", ".analysis", "node_modules", "__pycache__",
                      ".venv", "venv", "dist", "build"}
# 注释符紧邻 trace:（`# trace:` / `// trace:`）；括号内文本才是引用区
TRACE_LINE_RE = re.compile(r"(?:#|//)\s*trace:(.*)$")
TRACE_TOKENS = None  # 延迟绑定 diyc_lib 的正则常量


def _rel_path(root, path) -> str:
    return os.path.relpath(path, root).replace("\\", "/")


def _rel_to_output(args, filename) -> str:
    return _rel_path(args.project_root, os.path.join(args.output_dir, filename)).replace("\\", "/")


def _short(text, limit=72) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[:limit - 1] + "…"


# ---------------------------------------------------------------- resolve

def cmd_resolve(args) -> dict:
    # trace: S-16 AC-16.1 实例解析唯一入口（各 SKILL.md 激活句委托）
    cfg, warnings = diyc_lib.read_config(args.project_root)
    config_found = os.path.isfile(os.path.join(args.project_root, "diy-coder.yaml"))
    return receipt("resolve", True, output_dir=os.path.normpath(args.output_dir),
                   instance=args.instance, config_found=config_found,
                   warnings=warnings)


def _human_resolve(result) -> list:
    # .get：兜底回执（INTERNAL_ERROR）无 config_found 键，渲染不得再崩（V 复验 N-2）
    return ["output_dir: %s" % result.get("output_dir"),
            "config_found: %s" % result.get("config_found")]


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
        rel = _rel_path(args.project_root, path)
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


# ---------------------------------------------------------------- static

def _run_tool(tool, cwd, timeout):
    """跑一层静态检查：返回 (rc, 合并输出, timed_out)；超时 rc=None。"""
    try:
        proc = subprocess.run(tool, shell=True, cwd=cwd, timeout=timeout,
                              capture_output=True, text=True, encoding="utf-8",
                              errors="replace")
        return proc.returncode, (proc.stdout or "") + (proc.stderr or ""), False
    except subprocess.TimeoutExpired as e:
        out = ""
        for chunk in (e.stdout, e.stderr):
            if isinstance(chunk, bytes):
                out += chunk.decode("utf-8", "replace")
            elif chunk:
                out += chunk
        return None, out, True


def _tail(text, limit=20) -> list:
    lines = [ln for ln in (text or "").splitlines() if ln.strip()]
    return lines[-limit:]


def cmd_static(args) -> dict:
    # trace: S-7 AC-7.1 static_checks 链机械执行（阻断失败即停）
    docs = diyc_lib.Docs(args.project_root, args.output_dir)
    doc = docs.doc("test-plan")
    if doc is None:
        err = docs.yaml_err("test-plan")
        msg = err or "test-plan.yaml 不存在"
        return receipt("static", False, layers=[], counts={},
                       violations=[v("MISSING_FILE", _rel_to_output(args, "test-plan.yaml"), msg)])
    checks = doc.get("static_checks")
    if not isinstance(checks, list) or not checks:
        return receipt("static", True, layers=[], violations=[],
                       warnings=["test-plan.yaml 无 static_checks（跳过静态检查链）"],
                       counts={"run": 0, "failed": 0, "skipped": 0})
    ordered = sorted((c for c in checks if isinstance(c, dict)),
                     key=lambda c: c.get("order") if isinstance(c.get("order"), int) else 0)
    layers, warnings, violations = [], [], []
    stopped = False
    run_n = failed_n = skipped_n = 0
    for c in ordered:
        order, tool = c.get("order"), c.get("tool")
        gate = c.get("gate", "阻断")
        if gate not in ("阻断", "记录不阻断"):
            warnings.append("static_checks[order=%s] gate 值 %r 非法，按阻断处理" % (order, gate))
            gate = "阻断"
        if not isinstance(tool, str) or not tool.strip():
            warnings.append("static_checks[order=%s] tool 缺失/非字符串，按已跳过处理" % order)
            layers.append({"order": order, "tool": tool, "gate": gate, "rc": None,
                           "verdict": "已跳过", "tail": []})
            skipped_n += 1
            continue
        if stopped:
            layers.append({"order": order, "tool": tool, "gate": gate, "rc": None,
                           "verdict": "已跳过", "tail": []})
            skipped_n += 1
            continue
        rc, out, timed_out = _run_tool(tool, args.project_root, args.timeout)
        verdict = "通过" if rc == 0 else "失败"
        if timed_out:
            out = ("[diyc] 超时（>%ss）被杀\n" % args.timeout) + out
            violations.append(v("STATIC_FAIL", "static_checks[order=%s]" % order,
                                "工具超时（>%ss）：%s" % (args.timeout, _short(tool, 48))))
        layers.append({"order": order, "tool": tool, "gate": gate, "rc": rc,
                       "verdict": verdict, "tail": _tail(out)})
        run_n += 1
        if verdict == "失败":
            failed_n += 1
            if not timed_out:
                violations.append(v("STATIC_FAIL", "static_checks[order=%s]" % order,
                                    "%s 层失败（rc=%s）：%s"
                                    % (gate, rc, _short(tool, 48))))
            if gate == "阻断":
                stopped = True
    ok = not any(x["verdict"] == "失败" and x["gate"] == "阻断" for x in layers)
    return receipt("static", ok, layers=layers, violations=violations,
                   warnings=warnings, counts={"run": run_n, "failed": failed_n,
                                              "skipped": skipped_n})


def _human_static(result) -> list:
    return ["[%s] %s %s → %s (rc=%s)"
            % (x.get("order"), x.get("gate"), _short(x.get("tool"), 48),
               x.get("verdict"), x.get("rc"))
            for x in result.get("layers") or []]


# ---------------------------------------------------------------- baseline-add

def cmd_baseline_add(args) -> dict:
    # trace: baseline 台账唯一写入口（D1-D4 用户裁定 2026-09-13；仅用户裁定后调用）
    base_rel = _rel_path(args.project_root,
                         os.path.join(args.output_dir, diyc_lib.BASELINE_FILE))
    entry, violations = diyc_lib.baseline_add(
        args.project_root, args.output_dir, args.code, args.where, args.reason)
    if entry is None:
        return receipt("baseline-add", False, violations=violations)
    entries, _ = diyc_lib.load_baseline(args.output_dir, base_rel)  # 写后回读自检
    return receipt("baseline-add", True, entry=entry, updated=diyc_lib.today(),
                   counts={"entries": len(entries)}, violations=[])


# ---------------------------------------------------------------- main

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="diyc", description="diy-coder 产物检查器/写回器（统一脚本化，批次 3）")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--project-root", default=".", help="项目根目录")
    common.add_argument("--instance", default=None, help="实例名（FR-4.5/D-9）")
    common.add_argument("--json", action="store_true", help="机器可读单行 JSON 回执")
    sub = ap.add_subparsers(dest="command", required=True, metavar="<子命令>")

    sub.add_parser("resolve", parents=[common], help="解析 output_dir（实例透传唯一入口）")

    p = sub.add_parser("check", parents=[common], help="产物机械核对（diyc_check）")
    p.add_argument("--type", required=True, choices=CHECK_TYPES, help="文档类型")
    p.add_argument("--final", action="store_true", help="定稿级检查（--final 义务清单）")
    p.add_argument("--previous", default=None, help="旧稿路径（稳定 ID 集合比对）")
    p.add_argument("--story", default=None, help="限定 story（sprint/review 任务级检查）")
    p.add_argument("--strict", action="store_true", help="忽略 baseline 台账（发布/CI 复核）")

    p = sub.add_parser("trace", parents=[common], help="trace 注释引用审计")
    p.add_argument("--src", action="append", default=None,
                   help="只扫这些路径（可重复；相对 project-root）")
    p.add_argument("--strict", action="store_true", help="忽略 baseline 台账（发布/CI 复核）")

    p = sub.add_parser("static", parents=[common], help="执行 test-plan static_checks 链")
    p.add_argument("--timeout", type=int, default=600, help="单层超时秒数（默认 600）")
    p.add_argument("--strict", action="store_true", help="忽略 baseline 台账（发布/CI 复核）")

    p = sub.add_parser("transition", parents=[common], help="HALT 状态迁移（diyc_writeback）")
    p.add_argument("--story", required=True)
    p.add_argument("--to", required=True, help="目标状态")
    p.add_argument("--reason", default=None, help="已阻塞时必填")
    p.add_argument("--rounds", type=int, default=None)

    p = sub.add_parser("green", parents=[common], help="TDD 绿线证据写回")
    p.add_argument("--story", required=True)
    p.add_argument("--tc", action="append", default=None)
    p.add_argument("--red", action="append", default=None)
    p.add_argument("--green", action="append", default=None)

    p = sub.add_parser("done", parents=[common], help="待审查→已完成 终态写（真源回填）")
    p.add_argument("--story", required=True)
    p.add_argument("--rounds", type=int, default=None)

    p = sub.add_parser("bug-add", parents=[common], help="缺陷入库（bug-log.yaml）")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--entry", default=None, help="JSON 对象字符串")
    g.add_argument("--entry-file", default=None, help="JSON 对象文件路径")

    p = sub.add_parser("defer-add", parents=[common],
                       help="待确认动作入队（deferred-actions.yaml）")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--entry", default=None, help="JSON 对象字符串")
    g.add_argument("--entry-file", default=None, help="JSON 对象文件路径")

    p = sub.add_parser("reconcile", parents=[common], help="sprint 任务与故事集对账")
    p.add_argument("--apply", action="store_true", help="执行写回（默认 dry-run 只算不写）")

    p = sub.add_parser("baseline-add", parents=[common],
                       help="追加已知遗留台账条目（仅用户裁定后；D3 纪律）")
    p.add_argument("--code", required=True, help="违规码（须与 check 回执逐字一致）")
    p.add_argument("--where", required=True, help="违规位置（须与 check 回执逐字一致）")
    p.add_argument("--reason", required=True, help="裁定理由与日期（进台账，供追溯）")
    return ap


HUMAN_RENDERERS = {
    "resolve": _human_resolve,
    "trace": _human_trace,
    "static": _human_static,
}


def _validate_check_flags(parser, args) -> None:
    """check 的类型相关旗标约束（契约 §4.2）：违规即用法错误 exit 2。

    argparse choices 只能约束 --type 取值本身；组合约束（--final×review、
    --previous 类型白名单）在解析后由本函数以 parser.error 收口。
    """
    if args.command != "check":
        return
    if args.final and args.type == "review":
        parser.error("check --type review 不支持 --final（review 无定稿级检查）")
    if args.previous and args.type not in PREVIOUS_TYPES:
        parser.error("check --previous 仅适用于 %s（当前 --type %s）"
                     % ("/".join(PREVIOUS_TYPES), args.type))


def _finalize(result, args) -> dict:
    """补公共回执键（契约 §3 schema），公共键在前、命令特有键在后。

    output_dir 在回执表示层统一正斜杠（V 验证 S5 裁定）：回执是机器消费面，
    分隔符须单形，避免 AI 拼接出 `C:/...\\diy-output` 混形；内部文件系统操作
    仍使用 args.output_dir 原值（本函数只改表示层）。
    """
    result = result or {}
    final = {
        "ok": bool(result.get("ok")),
        "command": args.command,
        "project_root": args.project_root,
        "output_dir": os.path.normpath(args.output_dir).replace("\\", "/"),
        "instance": args.instance,
        "violations": list(result.get("violations") or []),
        "warnings": list(result.get("warnings") or []),
        "counts": dict(result.get("counts") or {}),
    }
    for key, value in result.items():
        if key not in final:
            final[key] = value
    return final


def _run_behavior(args) -> dict:
    """懒加载行为模块；模块缺失与用法错误同级（exit 2），模块内部 ImportError 照常抛出。"""
    module_name = "diyc_check" if args.command == "check" else "diyc_writeback"
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError as e:
        if e.name != module_name:
            raise
        sys.stderr.write("diyc %s 行为模块缺失：%s.py 不在脚本目录（四脚本须同装）\n"
                         % (args.command, module_name))
        return None
    return module.run(args)


def main(argv=None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    parser = build_parser()
    args = parser.parse_args(argv)
    _validate_check_flags(parser, args)
    # 兜底占位：resolve 失败（如配置非 UTF-8）时回执仍需 output_dir（V 复验 N-1）
    args.output_dir = os.path.join(args.project_root, diyc_lib.DEFAULT_OUTPUT_DIR)
    try:
        args.output_dir = diyc_lib.resolve_output_dir(args.project_root, args.instance)
        if args.command == "resolve":
            result = cmd_resolve(args)
        elif args.command == "trace":
            result = cmd_trace(args)
        elif args.command == "static":
            result = cmd_static(args)
        elif args.command == "baseline-add":
            result = cmd_baseline_add(args)
        else:
            result = _run_behavior(args)
            if result is None:
                return 2
        final = _finalize(result, args)
        if args.command in diyc_lib.AUDIT_COMMANDS and not getattr(args, "strict", False):
            diyc_lib.apply_baseline(final, args.project_root, args.output_dir,
                                    allow_stale=not getattr(args, "story", None))
    except Exception as e:  # 顶层兜底（V 复验 F-1）：任何未预期异常转回执，
        # 绝不空 stdout 静默失败；--json 面保持单行 JSON；异常回执不消费 baseline
        final = _finalize(receipt(args.command, False, violations=[v(
            "INTERNAL_ERROR", _rel_path(args.project_root, args.output_dir),
            "未预期内部异常：%s: %s（操作可能部分完成，请核对现场后重试）" % (type(e).__name__, e))]), args)
    return diyc_lib.emit(final, args.json,
                         human_lines_fn=HUMAN_RENDERERS.get(args.command))


if __name__ == "__main__":
    sys.exit(main())
