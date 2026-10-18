# -*- coding: utf-8 -*-
"""diy-eval-runner aggregate 子命令：按 config 聚合 timing 指标（mean / n-1 标准差 / delta）。"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import display_path, v  # noqa: E402

from eval_runner_lib import (  # noqa: E402
    DEFAULT_AGAINST, QUERIES_DIR, SUBJECT_CONFIG, emit, norm, read_json, receipt,
    resolve_path_arg,
)

# --------------------------------------------------------------- aggregate 子命令

NUMERIC = (int, float)


def sample_stddev(values):
    """样本标准差（n-1 贝塞尔校正）；少于两个值时返回 0.0（样本方差无定义）。"""
    n = len(values)
    if n < 2:
        return 0.0
    mean = sum(values) / n
    return math.sqrt(sum((x - mean) ** 2 for x in values) / (n - 1))


def summarize_metric(values):
    return {"n": len(values),
            "mean": (sum(values) / len(values)) if values else 0.0,
            "stddev": sample_stddev(values),
            "min": min(values) if values else 0.0,
            "max": max(values) if values else 0.0}


def summarize_config(records):
    by_metric = {}
    for rec in records:
        if not isinstance(rec, dict):
            continue
        for key, val in rec.items():
            if isinstance(val, bool) or not isinstance(val, NUMERIC):
                continue    # bool 在 Python 里是 int，但不是指标
            by_metric.setdefault(key, []).append(float(val))
    return {"runs": len(records),
            "metrics": {k: summarize_metric(x) for k, x in sorted(by_metric.items())}}


def load_records(run_dir, warnings):
    """读 run 目录下全部 timing.json（跳过 trigger 的 query 目录）。"""
    records, bad = [], []
    for dirpath, _dirs, files in os.walk(run_dir):
        if "timing.json" not in files:
            continue
        if os.path.sep + QUERIES_DIR + os.path.sep in dirpath + os.path.sep:
            continue
        path = os.path.join(dirpath, "timing.json")
        data, err = read_json(path)
        if err is not None:
            bad.append((path, err))
            continue
        records.append(data)
    for path, err in bad:
        warnings.append(v("UNPARSABLE_JSON", display_path(path, run_dir),
                          "timing.json 不可解析、已跳过：%s" % err))
    return records


def delta_configs(subject, against):
    """逐共享指标：delta = subject.mean − against.mean（源侧同形：B − A）。"""
    out = {}
    for name in sorted(set(subject["metrics"]) & set(against["metrics"])):
        s, a = subject["metrics"][name], against["metrics"][name]
        diff = s["mean"] - a["mean"]
        pct = (diff / a["mean"] * 100.0) if a["mean"] != 0 else None
        out[name] = {"subject_mean": s["mean"], "against_mean": a["mean"],
                     "delta": diff, "delta_pct": pct,
                     "subject_stddev": s["stddev"], "against_stddev": a["stddev"]}
    return out


def aggregate_self_test():
    """固定夹具校验 mean / n-1 标准差 / min / max / delta（源侧 --self-test 同款数值）。"""
    config_a = [{"elapsed_s": 10.0, "total_tokens": 100},
                {"elapsed_s": 12.0, "total_tokens": 200},
                {"elapsed_s": 14.0, "total_tokens": 300}]
    config_b = [{"elapsed_s": 13.0, "total_tokens": 90},
                {"elapsed_s": 15.0, "total_tokens": 110},
                {"elapsed_s": 17.0, "total_tokens": 100}]
    a, b = summarize_config(config_a), summarize_config(config_b)
    el = a["metrics"]["elapsed_s"]
    assert el["n"] == 3 and abs(el["mean"] - 12.0) < 1e-9
    assert abs(el["stddev"] - 2.0) < 1e-9, el      # 10,12,14 → sqrt((4+0+4)/2) = 2
    assert el["min"] == 10.0 and el["max"] == 14.0
    assert abs(a["metrics"]["total_tokens"]["stddev"] - 100.0) < 1e-9
    assert summarize_config([{"x": 5}])["metrics"]["x"]["stddev"] == 0.0
    with_bool = summarize_config([{"ok": True, "x": 1}, {"ok": False, "x": 3}])
    assert "ok" not in with_bool["metrics"]
    d = delta_configs(b, a)     # subject = b（13,15,17 → 15）− against = a（12）→ +3
    assert abs(d["elapsed_s"]["delta"] - 3.0) < 1e-9, d
    assert abs(d["elapsed_s"]["delta_pct"] - 25.0) < 1e-9, d
    return ["mean", "stddev_n_minus_1", "min", "max", "single_value_stddev",
            "bool_excluded", "delta", "delta_pct"]


def cmd_aggregate(args):
    violations, warnings = [], []
    root = os.path.abspath(args.project_root)
    out = resolve_path_arg(args.output_dir, root, "--output-dir", violations)
    if violations:
        return emit(receipt("aggregate", False, args.project_root, "", violations,
                            warnings, {}), args.json)
    if args.self_test:
        checked = aggregate_self_test()
        payload = receipt("aggregate", True, args.project_root, norm(out) if out else "",
                          [], [], {"checked": len(checked)}, self_test="passed",
                          checked=checked)
        return emit(payload, args.json, ["aggregate 自检通过：%s" % " / ".join(checked)])
    if not args.run_dir:
        print("diy-eval-runner: aggregate 需要 --run-dir D（或改用 --self-test）", file=sys.stderr)
        return 2
    run_dir = resolve_path_arg(args.run_dir, root, "--run-dir", violations)
    if violations:
        return emit(receipt("aggregate", False, args.project_root, "", violations,
                            warnings, {}), args.json)
    if not os.path.isdir(run_dir):
        violations.append(v("MISSING_FILE", display_path(run_dir, root), "run 目录不存在"))
        return emit(receipt("aggregate", False, args.project_root, "", violations,
                            warnings, {}), args.json)

    records = load_records(run_dir, warnings)
    grouped = {}
    for rec in records:
        if isinstance(rec, dict):
            grouped.setdefault(str(rec.get("config", "?")), []).append(rec)
    run_json, _err = read_json(os.path.join(run_dir, "run.json"))
    known = []
    if isinstance(run_json, dict) and isinstance(run_json.get("configs"), list):
        known = [str(c) for c in run_json["configs"]]
    for cfg in known:
        grouped.setdefault(cfg, [])
    configs = {name: summarize_config(recs) for name, recs in sorted(grouped.items())}
    counts = {"configs": len(configs), "runs": sum(c["runs"] for c in configs.values()),
              "metrics": len(configs.get(SUBJECT_CONFIG, {}).get("metrics", {}))}

    against = args.against or DEFAULT_AGAINST
    subject = SUBJECT_CONFIG if SUBJECT_CONFIG in configs else None
    delta = {}
    if subject is None:
        warnings.append(v("EMPTY_FIELD", display_path(run_dir, root),
                          "本次 run 无 `skill` config（trigger 模式无配置对比面）——"
                          "只出各 config 的均值与离散度，无 delta"))
    elif against not in configs:
        others = [c for c in configs if c != subject]
        if args.against:
            violations.append(v("UNKNOWN_ID", "--against",
                                "基准 config `%s` 不在本次 run 里（在场：%s）"
                                % (against, " / ".join(configs))))
        elif len(others) == 1:
            warnings.append(v("AGAINST_FALLBACK", "--against",
                              "缺省基准 config `%s` 不在场——退回 `%s` 作基准"
                              "（delta = %s − %s）" % (against, others[0], subject, others[0])))
            against = others[0]
        else:
            warnings.append(v("EMPTY_FIELD", "--against",
                              "缺省基准 config `%s` 不在场且无法唯一退回（在场：%s）——"
                              "本次不出 delta" % (against, " / ".join(configs))))
    if not violations and subject is not None and against in configs and against != subject:
        delta = delta_configs(configs[subject], configs[against])

    payload = receipt("aggregate", not violations, args.project_root,
                      norm(out) if out else "", violations, warnings, counts,
                      run_dir=norm(run_dir), subject=subject, against=against,
                      configs=configs, delta=delta)
    lines = ["聚合：%s" % norm(run_dir)]
    for name, conf in configs.items():
        mean = conf["metrics"].get("elapsed_s", {}).get("mean")
        lines.append("- %s：runs=%d elapsed_s 均值=%s" % (name, conf["runs"], mean))
    if delta:
        lines.append("- delta（%s − %s）：%s" % (subject, against,
                                                json.dumps(delta, ensure_ascii=False)))
    return emit(payload, args.json, lines)
