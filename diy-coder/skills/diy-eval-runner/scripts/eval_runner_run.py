# -*- coding: utf-8 -*-
"""diy-eval-runner run 子命令：四模式执行器（baseline / variant / quality / trigger）。"""
import os
import shutil
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import display_path, stamp_file, v  # noqa: E402

from eval_runner_case import (  # noqa: E402
    find_adapter, load_adapter, parse_skill_md, resolve_fixtures, run_case,
    run_query_once, validate_load_signal,
)
from eval_runner_lib import (  # noqa: E402
    CONFIG_MODES, CONFIG_ORDER, DEFAULT_MODE, DEFAULT_THRESHOLD, EVAL_RUNS_SUBDIR,
    FAILURE_STATUS, MEMLOG_NAME, MODES, QUERIES_DIR, emit, norm, read_json, receipt,
    resolve_path_arg, utc_now_iso, write_json, write_text,
)
from eval_runner_memlog import memlog_append, memlog_init  # noqa: E402
# --------------------------------------------------------------- run 子命令

def configs_for(modes):
    out = []
    for mode in ("baseline", "variant", "quality"):
        if mode in modes:
            for cfg in CONFIG_ORDER[mode]:
                if cfg not in out:
                    out.append(cfg)
    return out


def discover_cases(skill_dir, explicit, project_root):
    """用例发现链（找不到就停——运行器不发明用例）。"""
    chain = []
    if explicit:
        chain.append(explicit)
    chain.append(os.path.join(skill_dir, "evals", "cases.json"))
    name = os.path.basename(os.path.normpath(skill_dir))
    chain.append(os.path.join(project_root, "evals", name, "cases.json"))
    chain.append(os.path.join(project_root, "evals", "cases.json"))
    for cand in chain:
        if os.path.isfile(cand):
            return cand
    return None


def unique_run_dir(base, label):
    """run 目录唯一化：同名已存在则另铸后缀，**绝不覆盖**既有 run。"""
    cand = os.path.join(base, "%s-%s" % (stamp_file(), label))
    n = 2
    while os.path.exists(cand):
        cand = os.path.join(base, "%s-%s-%d" % (stamp_file(), label, n))
        n += 1
    return cand


def finish_run(args, root, out, violations, warnings, counts, run_id=None, run_dir=None,
               modes=None):
    payload = receipt("run", not violations, args.project_root, norm(out) if out else "",
                      violations, warnings, counts,
                      run_id=run_id, run_dir=norm(run_dir) if run_dir else None,
                      modes=list(modes or []))
    lines = ["评测运行：%s" % (run_id or "未开始"),
             "run 目录：%s" % (norm(run_dir) if run_dir else "（未创建）")]
    return emit(payload, args.json, lines)


def cmd_run(args):
    violations, warnings = [], []
    root = os.path.abspath(args.project_root)
    out = resolve_path_arg(args.output_dir, root, "--output-dir", violations)
    skill = resolve_path_arg(args.skill, root, "--skill", violations)
    cases_arg = resolve_path_arg(args.evals, root, "--evals", violations)
    variant = resolve_path_arg(args.variant_path, root, "--variant-path", violations)
    adapter_arg = resolve_path_arg(args.adapter, root, "--adapter", violations)
    queries_arg = resolve_path_arg(args.queries, root, "--queries", violations)
    counts = {"cases": 0, "configs": 0, "results": 0, "executed": 0, "skipped": 0,
              "failures": 0, "trigger_queries": 0}
    if violations:
        return finish_run(args, root, out, violations, warnings, counts)

    modes = list(args.mode) if args.mode else [DEFAULT_MODE]
    bad = [m for m in modes if m not in MODES]
    if bad:
        violations.append(v("ENUM_INVALID", "--mode",
                            "模式 %r 非法——合法值恰四个：%s" % (bad[0], " / ".join(MODES))))
        return finish_run(args, root, out, violations, warnings, counts)
    modes = [m for m in MODES if m in modes]

    # 门禁①：target 技能必须存在且含 SKILL.md
    if not skill or not os.path.isdir(skill) or not os.path.isfile(os.path.join(skill, "SKILL.md")):
        violations.append(v("MISSING_FILE", display_path(args.skill, root) if skill else "--skill",
                            "target 技能目录不存在或不含 SKILL.md——评测对象必须是技能目录"))
    if violations:
        return finish_run(args, root, out, violations, warnings, counts)

    # 用法错误（exit 2）：variant 必须给 --variant-path
    if "variant" in modes and not variant:
        print("diy-eval-runner: --mode variant 必须同时给 --variant-path（对比用的精简最小版）",
              file=sys.stderr)
        return 2
    if variant and not os.path.isfile(os.path.join(variant, "SKILL.md")):
        violations.append(v("MISSING_FILE", display_path(variant, root),
                            "--variant-path 不含 SKILL.md"))
    need_config = any(m in CONFIG_MODES for m in modes)

    # 门禁②：用例文件（找不到就停——运行器不发明用例）
    cases_file = None
    if need_config:
        cases_file = discover_cases(skill, cases_arg, root)
        if cases_file is None:
            violations.append(v("MISSING_FILE", "%s/evals/cases.json" % os.path.basename(skill),
                                "找不到用例文件（--evals > <技能>/evals/cases.json > "
                                "<project-root>/evals/<技能名>/cases.json）——运行器不发明用例"))
    queries = None
    if "trigger" in modes:
        if not queries_arg or not os.path.isfile(queries_arg):
            violations.append(v("MISSING_FILE", display_path(queries_arg, root) if queries_arg
                                else "--queries",
                                "trigger 模式需要 --queries（问句文件，形态 "
                                '{"query": ..., "should_trigger": true|false}）'))
        else:
            queries, err = read_json(queries_arg)
            if err is not None or not isinstance(queries, list):
                violations.append(v("UNPARSABLE_JSON", display_path(queries_arg, root),
                                    "问句文件必须是 JSON 数组：%s" % (err or "形状不是数组")))
                queries = None
    if violations:
        return finish_run(args, root, out, violations, warnings, counts)

    # adapter：缺席取默认键、形状非法降级 + warning
    adapter, adapter_note = None, "none"
    anchor_dir = os.path.dirname(cases_file or queries_arg or skill)
    adapter_path = find_adapter(adapter_arg, anchor_dir)
    if adapter_path is not None:
        try:
            adapter = load_adapter(adapter_path)
            adapter_note = display_path(adapter_path, root)
        except ValueError as e:
            warnings.append(v("ADAPTER_INVALID", display_path(adapter_path, root),
                              "%s——逐键取默认继续" % e))
            adapter, adapter_note = None, "invalid"
    if args.invocation:
        adapter = dict(adapter or {})
        adapter["invocation"] = list(args.invocation)

    # 门禁④：子串式 load_signal 拒跑（源侧硬规则）
    if "trigger" in modes and adapter is not None:
        msg = validate_load_signal(adapter.get("load_signal"))
        if msg:
            violations.append(v("ENUM_INVALID", adapter_note or "--adapter", msg))
            return finish_run(args, root, out, violations, warnings, counts)

    invocation = (adapter or {}).get("invocation")
    skip_reason = ""
    if not invocation:
        warnings.append(v("ADAPTER_MISSING", "--invocation",
                          "未配置 invocation（既无 --invocation 也无 adapter.json 的 "
                          "invocation 键）：只 stage、结果记 skipped，既不崩也不静默。"
                          "给 --invocation <命令…> 或 adapter.json 的 invocation 键即可真跑。"))
        skip_reason = "未配置 invocation"
    else:
        exe = str(invocation[0])
        if shutil.which(exe) is None and not os.path.isfile(exe):
            for mode in modes:
                warnings.append(v("MODE_SKIPPED", mode,
                                  "invocation 命令 `%s` 不可解析（无头下即 runner.py 白名单"
                                  "未覆盖该命令族）——跳过 mode `%s`：只 stage、不执行，"
                                  "不入队；调用方需额外命令族时经 `runner.py --allow` 传入。"
                                  % (exe, mode)))
            skip_reason = "invocation 命令不可解析：%s" % exe

    if need_config:
        try:
            cases, err = read_json(cases_file)
        except Exception as e:  # 读取层兜底：任何意外都转成违规，不裸栈
            cases, err = None, str(e)
        if err is not None:
            violations.append(v("UNPARSABLE_JSON", display_path(cases_file, root),
                                "用例文件不可读：%s" % err))
            return finish_run(args, root, out, violations, warnings, counts)
        if isinstance(cases, dict) and "cases" in cases:
            cases = cases["cases"]
        if not isinstance(cases, list):
            violations.append(v("EMPTY_FIELD", display_path(cases_file, root),
                                "用例文件必须是数组或 {cases: [...]}"))
            return finish_run(args, root, out, violations, warnings, counts)
    else:
        cases = []

    configs = configs_for(modes)
    label = args.label or (("%s-triggers" % os.path.basename(os.path.normpath(skill)))
                           if modes == ["trigger"] else "evals")
    runs_base = os.path.join(out, EVAL_RUNS_SUBDIR)
    os.makedirs(runs_base, exist_ok=True)
    run_dir = unique_run_dir(runs_base, label)

    # 续接提示（不自动续跑、不合并、不覆盖；本批不做 --resume）
    for name in sorted(os.listdir(runs_base)):
        cand = os.path.join(runs_base, name)
        if not name.endswith("-%s" % label) or not os.path.isdir(cand):
            continue
        if not os.path.isfile(os.path.join(cand, "execution-summary.json")):
            warnings.append(v("INCOMPLETE_RUN", display_path(cand, root),
                              "已有未完成 run `%s`；如需重跑请另起 run-id"
                              "（时间戳天然不同）——不自动续跑、不合并、不覆盖。" % name))
    os.makedirs(run_dir, exist_ok=True)

    skill_name = os.path.basename(os.path.normpath(skill))
    try:
        memlog_init(os.path.join(run_dir, MEMLOG_NAME), os.path.basename(run_dir))
        memlog_append(os.path.join(run_dir, MEMLOG_NAME), "event",
                      "run 启动：mode=%s configs=%s" % ("/".join(modes), "/".join(configs) or "-"))
    except (OSError, ValueError) as e:
        warnings.append(v("EMPTY_FIELD", MEMLOG_NAME, "run memlog 初始化失败：%s" % e))

    case_count = len(cases) if need_config else len(queries or [])
    write_json(os.path.join(run_dir, "run.json"), {
        "run_id": os.path.basename(run_dir),
        "cases_file": display_path(cases_file, root) if cases_file else None,
        "skill_path": norm(skill),
        "variant_path": norm(variant) if variant else None,
        "mode": modes,
        "configs": configs,
        "runs_per_case": max(1, args.runs),
        "adapter": adapter_note,
        "started_at": utc_now_iso(),
        "case_count": case_count,
        "query_count": len(queries or []),
        "load_signal": (adapter or {}).get("load_signal") or {},
    })

    results, skipped_modes = [], []
    if skip_reason:
        skipped_modes = [{"mode": m, "reason": skip_reason} for m in modes]

    # 模式面：config 三模式（baseline / variant / quality）
    for config in configs:
        config_skill = variant if config == "variant" else (
            None if config == "bare" else skill)
        for case in cases:
            case_id = str(case.get("id", "unnamed"))
            fixtures = resolve_fixtures(case.get("files", []), root,
                                        os.path.dirname(cases_file), warnings,
                                        "cases[%s]" % case_id)
            for i in range(max(1, args.runs)):
                base_dir = os.path.join(run_dir, config, case_id)
                case_dir = os.path.join(base_dir, "run-%d" % (i + 1)) \
                    if args.runs > 1 else base_dir
                results.append(run_case(case, case_dir, run_dir, adapter,
                                        int(case.get("timeout", args.timeout)), config,
                                        config_skill, fixtures, skip_reason))

    # trigger 模式：合成技能 + 逐问句真跑，只认 tool_use
    if "trigger" in modes:
        queries_dir = os.path.join(run_dir, QUERIES_DIR)
        os.makedirs(queries_dir, exist_ok=True)
        if skip_reason:
            counts["trigger_queries"] = len(queries)
            write_json(os.path.join(run_dir, "triggers-result.json"), {
                "run_id": os.path.basename(run_dir), "completed_at": utc_now_iso(),
                "skill_name": skill_name, "status": "skipped", "reason": skip_reason,
                "detection": "tool_use", "results": [],
                "summary": {"total": len(queries), "passed": 0, "failed": 0,
                            "skipped": len(queries)}})
        else:
            try:
                skill_name, description = parse_skill_md(skill)
            except (OSError, ValueError) as e:
                violations.append(v("EMPTY_FIELD", display_path(skill, root),
                                    "SKILL.md frontmatter 不可解析：%s" % e))
                return finish_run(args, root, out, violations, warnings, counts)
            threshold = DEFAULT_THRESHOLD
            per_query, synthetics, ran = {}, {}, {}
            for idx, item in enumerate(queries):
                runs = []
                unique = uuid.uuid4().hex[:8]      # 每个问句一个后缀，其多次重复共用
                for run_idx in range(1, max(1, args.runs) + 1):
                    stage = os.path.join(queries_dir, "q%03d-r%d" % (idx, run_idx))
                    os.makedirs(stage, exist_ok=True)
                    hit, clean_name, text = run_query_once(
                        str(item.get("query", "")), skill_name, description, adapter,
                        stage, args.timeout, skip_reason, unique)
                    if text is not None:
                        write_text(os.path.join(stage, "transcript.jsonl"), text)
                    synthetics[idx] = clean_name
                    if text is None:
                        ran[idx] = False
                    runs.append(hit)
                per_query[idx] = runs
            if ran:
                # 预检之后命令仍不可解析（竞态/被清出 PATH）：不静默——按源侧语义记
                # adapter-missing，本轮不出触发率
                reason = "invocation 命令在运行期不可解析：%s" % invocation[0]
                warnings.append(v("MODE_SKIPPED", "trigger", "%s——本 mode 无触发率可出。" % reason))
                skipped_modes.append({"mode": "trigger", "reason": reason})
                counts["trigger_queries"] = len(queries)
                write_json(os.path.join(run_dir, "triggers-result.json"), {
                    "run_id": os.path.basename(run_dir), "completed_at": utc_now_iso(),
                    "skill_name": skill_name, "status": "adapter-missing",
                    "reason": reason, "detection": "tool_use", "results": [],
                    "summary": {"total": len(queries), "passed": 0, "failed": 0}})
            else:
                trig_results = []
                for idx, item in enumerate(queries):
                    runs = per_query.get(idx, [])
                    rate = (sum(1 for x in runs if x) / len(runs)) if runs else 0.0
                    should = bool(item.get("should_trigger", True))
                    passed = (rate >= threshold) if should else (rate < threshold)
                    trig_results.append({
                        "query": item.get("query", ""), "should_trigger": should,
                        "trigger_rate": round(rate, 3),
                        "triggers": sum(1 for x in runs if x), "runs": len(runs),
                        "pass": passed, "synthetic": synthetics.get(idx, ""),
                    })
                counts["trigger_queries"] = len(trig_results)
                write_json(os.path.join(run_dir, "triggers-result.json"), {
                    "run_id": os.path.basename(run_dir), "completed_at": utc_now_iso(),
                    "skill_name": skill_name, "description": description,
                    "detection": "tool_use", "threshold": threshold,
                    "runs_per_query": max(1, args.runs), "results": trig_results,
                    "summary": {"total": len(trig_results),
                                "passed": sum(1 for x in trig_results if x["pass"]),
                                "failed": sum(1 for x in trig_results if not x["pass"])},
                })

    executed = sum(1 for x in results if x.get("status") == "ok")
    skipped = sum(1 for x in results if x.get("status") == "skipped")
    failures = sum(1 for x in results if x.get("status") in FAILURE_STATUS)
    write_json(os.path.join(run_dir, "execution-summary.json"), {
        "run_id": os.path.basename(run_dir), "completed_at": utc_now_iso(),
        "mode": modes, "total": len(results), "executed": executed,
        "skipped": skipped, "failures": failures, "run_dir": norm(run_dir),
        "skipped_modes": skipped_modes, "results": results,
    })
    counts.update({"cases": len(cases), "configs": len(configs), "results": len(results),
                   "executed": executed, "skipped": skipped, "failures": failures})
    return finish_run(args, root, out, violations, warnings, counts,
                      run_id=os.path.basename(run_dir), run_dir=run_dir, modes=modes)
