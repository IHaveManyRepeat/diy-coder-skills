# -*- coding: utf-8 -*-
"""diy-eval-runner check 子命令：run 目录结构合规 + 结果自洽（终门）。"""
import io
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import display_path, v  # noqa: E402

from eval_runner_lib import (  # noqa: E402
    CASE_FILES, CONFIG_MODES, DEFAULT_SKILL_DIR, DEFAULT_THRESHOLD, EVAL_RUNS_SUBDIR,
    FAILURE_STATUS, MEMLOG_NAME, MODES, QUERIES_DIR, SUBJECT_CONFIG, emit, norm,
    read_json, receipt, resolve_path_arg,
)
from eval_runner_memlog import memlog_split  # noqa: E402


# --------------------------------------------------------------- check 子命令（终门）

def check_run_json(run_dir, root, violations):
    path = os.path.join(run_dir, "run.json")
    if not os.path.isfile(path):
        violations.append(v("MISSING_FILE", display_path(path, root),
                            "run.json 缺失——不是 run 目录"))
        return None
    data, err = read_json(path)
    if err is not None:
        violations.append(v("UNPARSABLE_JSON", display_path(path, root), "解析失败：%s" % err))
        return None
    for key in ("run_id", "skill_path", "mode", "configs", "runs_per_case",
                "adapter", "started_at", "case_count"):
        if key not in data:
            violations.append(v("EMPTY_FIELD", "%s.%s" % (display_path(path, root), key),
                                "run.json 缺必填字段 %s" % key))
    modes = data.get("mode")
    modes = modes if isinstance(modes, list) else [modes]
    # configs 只在真的跑了 config 模式时才要求非空（trigger-only 的 run 合法地没有 config）
    empties = [k for k in ("run_id", "skill_path", "runs_per_case", "started_at")
               if data.get(k) in (None, "", [], {})]
    if "adapter" not in data:
        empties.append("adapter")
    if data.get("case_count") is None:
        empties.append("case_count")
    if not modes:
        empties.append("mode")
    if any(m in CONFIG_MODES for m in modes) and not data.get("configs"):
        empties.append("configs")
    for key in empties:
        violations.append(v("EMPTY_FIELD", "%s.%s" % (display_path(path, root), key),
                            "run.json 的 %s 为空（缺必填面）" % key))
    for mode in modes:
        if mode not in MODES:
            violations.append(v("ENUM_INVALID", "%s.mode" % display_path(path, root),
                                "模式 %r 非法——合法值恰四个：%s" % (mode, " / ".join(MODES))))
    return data


def check_case_dirs(run_dir, root, results, modes, violations):
    """逐结果验目录与文件；quality 另验 grading.json 的举证非空。"""
    timings = set()
    for dirpath, _dirs, files in os.walk(run_dir):
        if "timing.json" in files:
            timings.add(norm(dirpath))
    seen = set()
    for res in results:
        reldir = res.get("dir")
        if not reldir:
            violations.append(v("EMPTY_FIELD", "execution-summary.json results[]",
                                "结果条目缺 dir——check 靠它定位 case 目录"))
            continue
        case_dir = norm(os.path.join(run_dir, reldir))
        seen.add(case_dir)
        if not os.path.isdir(case_dir):
            violations.append(v("MISSING_FILE", display_path(case_dir, root),
                                "结果声明的 case 目录不存在"))
            continue
        for name in CASE_FILES:
            if not os.path.isfile(os.path.join(case_dir, name)):
                violations.append(v("MISSING_FILE", "%s/%s" % (display_path(case_dir, root), name),
                                    "case 目录缺 %s" % name))
        if not os.path.isdir(os.path.join(case_dir, "cwd")):
            violations.append(v("MISSING_FILE", "%s/cwd" % display_path(case_dir, root),
                                "case 目录缺 cwd/"))
        if res.get("status") == "ok" and not os.path.isfile(
                os.path.join(case_dir, "transcript.jsonl")):
            violations.append(v("MISSING_FILE", "%s/transcript.jsonl"
                                % display_path(case_dir, root), "已执行的 case 缺 transcript"))
        if "quality" in modes and res.get("config") == SUBJECT_CONFIG \
                and res.get("status") == "ok":
            check_grading(case_dir, root, res.get("case_id"), violations)
    if timings != seen:
        missing = sorted(t for t in seen - timings)
        extra = sorted(t for t in timings - seen)
        violations.append(v("SET_MISMATCH", display_path(run_dir, root),
                            "execution-summary 的 results 与实际 timing.json 目录不符"
                            "（results 有而磁盘无：%s；磁盘有而 results 无：%s）"
                            % (len(missing), len(extra))))


def check_grading(case_dir, root, case_id, violations):
    """quality 的评分账本：不给部分分（passed 是布尔）、举证责任在通过方（证据非空）。"""
    path = os.path.join(case_dir, "grading.json")
    where = display_path(path, root)
    if not os.path.isfile(path):
        violations.append(v("MISSING_FILE", where,
                            "quality 模式已执行的 case 缺 grading.json——评分账本归 grader，"
                            "引擎不代填、不默认通过"))
        return
    data, err = read_json(path)
    if err is not None:
        violations.append(v("UNPARSABLE_JSON", where, "解析失败：%s" % err))
        return
    exps = data.get("expectations")
    if not isinstance(exps, list) or not exps:
        violations.append(v("EMPTY_FIELD", "%s.expectations" % where,
                            "expectations 缺失或为空——rubric 逐条判、不给部分分"))
        return
    for i, exp in enumerate(exps):
        spot = "%s.expectations[%d]" % (where, i)
        if not isinstance(exp, dict):
            violations.append(v("EMPTY_FIELD", spot, "条目不是对象"))
            continue
        if not str(exp.get("text", "")).strip():
            violations.append(v("EMPTY_FIELD", "%s.text" % spot, "expectation 缺 text"))
        if not isinstance(exp.get("passed"), bool):
            violations.append(v("ENUM_INVALID", "%s.passed" % spot,
                                "passed 必须是布尔——不给部分分"))
        if not str(exp.get("evidence", "")).strip():
            violations.append(v("EMPTY_FIELD", "%s.evidence" % spot,
                                "evidence 为空——举证责任在通过方，无证据不得判过"))
    summary = data.get("summary") if isinstance(data.get("summary"), dict) else {}
    passed = sum(1 for e in exps if isinstance(e, dict) and e.get("passed") is True)
    if summary.get("passed") != passed or summary.get("total") != len(exps) \
            or summary.get("failed") != len(exps) - passed:
        violations.append(v("SET_MISMATCH", "%s.summary" % where,
                            "summary 与 expectations 不符（应 passed=%d / failed=%d / total=%d）"
                            % (passed, len(exps) - passed, len(exps))))
    fb = data.get("rubric_feedback")
    if not isinstance(fb, dict):
        violations.append(v("EMPTY_FIELD", "%s.rubric_feedback" % where,
                            "grader 必须反向批评 rubric（weak / uncovered / overall 三键在场，"
                            "哪怕是空数组）"))
    else:
        for key in ("weak", "uncovered", "overall"):
            if key not in fb:
                violations.append(v("EMPTY_FIELD", "%s.rubric_feedback.%s" % (where, key),
                                    "缺 rubric 反馈键 %s" % key))


def check_trigger(run_dir, root, modes, violations):
    path = os.path.join(run_dir, "triggers-result.json")
    where = display_path(path, root)
    if not os.path.isfile(path):
        violations.append(v("MISSING_FILE", where, "trigger 模式的 run 缺 triggers-result.json"))
        return 0
    data, err = read_json(path)
    if err is not None:
        violations.append(v("UNPARSABLE_JSON", where, "解析失败：%s" % err))
        return 0
    if data.get("status") in ("skipped", "adapter-missing"):
        if not str(data.get("reason", "")).strip():
            violations.append(v("EMPTY_FIELD", "%s.reason" % where,
                                "降级跳过的 trigger run 必须写明 reason（不静默）"))
        return 0
    if data.get("detection") != "tool_use":
        violations.append(v("ENUM_INVALID", "%s.detection" % where,
                            "触发判定必须是 tool_use——整篇 transcript 子串匹配会让触发率恒为 "
                            "100%，本技能禁止"))
    results = data.get("results")
    if not isinstance(results, list) or not results:
        violations.append(v("EMPTY_FIELD", "%s.results" % where, "results 缺失或为空"))
        return 0
    threshold = data.get("threshold", DEFAULT_THRESHOLD)
    passed = 0
    for i, item in enumerate(results):
        spot = "%s.results[%d]" % (where, i)
        if not isinstance(item, dict):
            violations.append(v("EMPTY_FIELD", spot, "条目不是对象"))
            continue
        runs, triggers = item.get("runs"), item.get("triggers")
        if not isinstance(runs, int) or runs < 1 or not isinstance(triggers, int):
            violations.append(v("EMPTY_FIELD", spot, "runs / triggers 缺失或非整数"))
            continue
        rate = round(triggers / runs, 3)
        if abs(float(item.get("trigger_rate", -1)) - rate) > 1e-9:
            violations.append(v("SET_MISMATCH", "%s.trigger_rate" % spot,
                                "触发率与 triggers/runs 不符（应 %s）" % rate))
        should = bool(item.get("should_trigger", True))
        want = (rate >= threshold) if should else (rate < threshold)
        if bool(item.get("pass")) != want:
            violations.append(v("SET_MISMATCH", "%s.pass" % spot,
                                "pass 与阈值判定不符（threshold=%s / should_trigger=%s）"
                                % (threshold, should)))
        if item.get("pass"):
            passed += 1
        for run_idx in range(1, runs + 1):
            stage = os.path.join(run_dir, QUERIES_DIR, "q%03d-r%d" % (i, run_idx))
            if not os.path.isdir(stage):
                violations.append(v("MISSING_FILE", display_path(stage, root),
                                    "缺问句运行目录"))
                continue
            if not os.path.isdir(os.path.join(stage, ".home")):
                violations.append(v("MISSING_FILE", "%s/.home" % display_path(stage, root),
                                    "问句运行目录缺清场 HOME"))
            name = str(item.get("synthetic", ""))
            if not name or not os.path.isdir(os.path.join(stage, DEFAULT_SKILL_DIR, name)):
                violations.append(v("MISSING_FILE", "%s/%s/%s" % (display_path(stage, root),
                                    DEFAULT_SKILL_DIR, name or "<synthetic>"),
                                    "问句运行目录缺合成技能（唯一名后缀）"))
    summary = data.get("summary") if isinstance(data.get("summary"), dict) else {}
    if summary.get("total") != len(results) or summary.get("passed") != passed \
            or summary.get("failed") != len(results) - passed:
        violations.append(v("SET_MISMATCH", "%s.summary" % where,
                            "summary 与 results 不符（应 passed=%d / failed=%d / total=%d）"
                            % (passed, len(results) - passed, len(results))))
    return len(results)


def cmd_check(args):
    violations, warnings = [], []
    root = os.path.abspath(args.project_root)
    run_dir = resolve_path_arg(args.run_dir, root, "--run-dir", violations)
    out = resolve_path_arg(args.output_dir, root, "--output-dir", violations)
    if violations:
        return emit(receipt("check", False, args.project_root, "", violations, warnings, {}),
                    args.json)
    if not out:
        parent = os.path.dirname(norm(run_dir))
        out = os.path.dirname(parent) if os.path.basename(parent) == EVAL_RUNS_SUBDIR else ""
    if not os.path.isdir(run_dir):
        violations.append(v("MISSING_FILE", display_path(run_dir, root), "run 目录不存在"))
        return emit(receipt("check", False, args.project_root, norm(out) if out else "",
                            violations, warnings, {}), args.json)

    run_json = check_run_json(run_dir, root, violations)
    modes = (run_json or {}).get("mode") or []
    modes = modes if isinstance(modes, list) else [modes]

    summary, err = read_json(os.path.join(run_dir, "execution-summary.json"))
    if err is not None:
        violations.append(v("MISSING_FILE" if not os.path.isfile(
            os.path.join(run_dir, "execution-summary.json")) else "UNPARSABLE_JSON",
            "execution-summary.json",
            "缺 execution-summary.json（run 未完成）或不可解析：%s" % err))
        summary = None
    results = []
    if isinstance(summary, dict):
        results = summary.get("results") if isinstance(summary.get("results"), list) else []
        if summary.get("total") != len(results):
            violations.append(v("SET_MISMATCH", "execution-summary.json total",
                                "total=%s 与 results 条数 %d 不符"
                                % (summary.get("total"), len(results))))
        for key, want in (("executed", sum(1 for x in results if x.get("status") == "ok")),
                          ("skipped", sum(1 for x in results if x.get("status") == "skipped")),
                          ("failures", sum(1 for x in results
                                           if x.get("status") in FAILURE_STATUS))):
            if summary.get(key) != want:
                violations.append(v("SET_MISMATCH", "execution-summary.json %s" % key,
                                    "%s=%s 与 results 实际 %d 不符" % (key, summary.get(key), want)))
        check_case_dirs(run_dir, root, results, modes, violations)

    memlog = os.path.join(run_dir, MEMLOG_NAME)
    if not os.path.isfile(memlog):
        violations.append(v("MISSING_FILE", display_path(memlog, root),
                            "run 根缺 .memlog.md（决策与轮次 trail）"))
    else:
        try:
            meta, _body = memlog_split(io.open(memlog, encoding="utf-8").read())
            if not str(meta.get("updated", "")).strip():
                violations.append(v("EMPTY_FIELD", "%s.updated" % display_path(memlog, root),
                                    "memlog frontmatter 缺 updated"))
        except (OSError, ValueError) as e:
            violations.append(v("EMPTY_FIELD", display_path(memlog, root),
                                "memlog 不可解析：%s" % e))

    trigger_queries = check_trigger(run_dir, root, modes, violations) if "trigger" in modes else 0
    runs_root = os.path.dirname(norm(run_dir))
    run_dirs = 0
    if os.path.isdir(runs_root):
        run_dirs = len([d for d in os.listdir(runs_root)
                        if os.path.isdir(os.path.join(runs_root, d))])
    counts = {"results": len(results), "case_dirs": len(results),
              "executed": sum(1 for x in results if x.get("status") == "ok"),
              "skipped": sum(1 for x in results if x.get("status") == "skipped"),
              "failures": sum(1 for x in results if x.get("status") in FAILURE_STATUS),
              "trigger_queries": trigger_queries, "run_dirs": run_dirs}
    payload = receipt("check", not violations, args.project_root, norm(out) if out else "",
                      violations, warnings, counts, run_dir=norm(run_dir),
                      modes=modes, runs_root=runs_root)
    lines = ["终门 check：%s" % norm(run_dir),
             "结果 %d / run 目录累计 %d（run 目录永不删除、覆盖、轮转；清理归用户决定）"
             % (len(results), run_dirs)]
    return emit(payload, args.json, lines)
