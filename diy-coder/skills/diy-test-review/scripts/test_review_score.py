# -*- coding: utf-8 -*-
"""diy-test-review score 子命令面：severity 复算 + 降档 + 去重 + 分档 + 建议账本。"""
import io
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import display_path, emit_via, items, load_yaml_safe, nonempty, v  # noqa: E402

from test_review_lib import (  # noqa: E402
    BONUS_KEYS, BONUS_MAX, BONUS_POINTS, CONVENTION_ENTRY_STATUSES,
    DEDUCTION_WEIGHTS, DIMENSIONS, DIMENSION_WEIGHTS, FILE_LEVEL_ROWS, SEVERITIES,
    bonus_guard_map, clamp_score, downgrade_severity, grade_of, load_criteria,
    recommend_of,
)
# ---------------------------------------------------------------- score

def _finding_violations(raw, table):
    """逐条 finding 的入口校验 → (violations, [规范化 finding])。severity 不在输入面。"""
    violations, plain = [], []
    if not isinstance(raw, list):
        return [v("EMPTY_FIELD", "findings", "findings 不是列表")], []
    for i, item in enumerate(raw):
        where = "findings[%d]" % i
        if not isinstance(item, dict):
            violations.append(v("EMPTY_FIELD", where, "finding 不是映射"))
            continue
        row = item.get("row")
        spec = table.get(str(row)) if nonempty(row) else None
        if spec is None:
            violations.append(v("ENUM_INVALID", where + ".row",
                                "row 越界：%s（须为 criteria.yaml 有效行）" % row))
            continue
        if spec.get("disabled"):
            violations.append(v("ENUM_INVALID", where + ".row",
                                "row=%s 已 disabled 留档（私有库绑定裁剪），不得成条目" % row))
            continue
        if not nonempty(item.get("file")):
            violations.append(v("EMPTY_FIELD", where + ".file", "file 缺失"))
            continue
        line = item.get("line")
        if str(row) in FILE_LEVEL_ROWS:
            if line is not None:
                violations.append(v("ENUM_INVALID", where + ".line",
                                    "文件级行 %s 的 line 须为 null（以 file 取代行号）" % row))
                continue
        elif not isinstance(line, int) or isinstance(line, bool) or line < 1:
            violations.append(v("ENUM_INVALID", where + ".line",
                                "行级行的 line 须为正整数（实为 %s）" % line))
            continue
        klass = item.get("class")
        if spec.get("basis") == "惯例":
            if not nonempty(klass):
                violations.append(v("EMPTY_FIELD", where + ".class",
                                    "convention 行须带 class（已确立|新现）"))
                continue
            if str(klass) not in CONVENTION_ENTRY_STATUSES:
                violations.append(v("ENUM_INVALID", where + ".class",
                                    "class=%s 时该行不成立、不得成条目（缺失 / 未知 系 "
                                    "scan 内部判定值）" % klass))
                continue
        elif nonempty(klass):
            violations.append(v("ENUM_INVALID", where + ".class",
                                "class 仅 basis=惯例 行可带（%s 是 %s 行）"
                                % (row, spec.get("basis"))))
            continue
        severity = downgrade_severity(str(spec.get("severity")), str(klass))
        plain.append({"row": str(row), "file": str(item["file"]),
                      "line": None if line is None else int(line),
                      "class": str(klass) if nonempty(klass) else None,
                      "severity": severity})
    return violations, plain


def _dedupe(plain):
    """按 file:location:row 去重（文件级行以 file 取代行号）；去重在计分之前。"""
    seen, out, duplicates = set(), [], 0
    for item in plain:
        location = "file" if item["row"] in FILE_LEVEL_ROWS else item["line"]
        key = "%s:%s:%s" % (item["file"], location, item["row"])
        if key in seen:
            duplicates += 1
            continue
        seen.add(key)
        out.append(item)
    return out, duplicates


def _severity_counts(deduped):
    counts = {sev: 0 for sev in SEVERITIES}
    for item in deduped:
        counts[item["severity"]] += 1
    return counts


def _bonus_violations(raw, deduped, table):
    violations, applied, total = [], [], 0
    if raw is None:
        raw = []
    if not isinstance(raw, list):
        return [v("EMPTY_FIELD", "bonus", "bonus 不是列表")], applied, total
    guards = bonus_guard_map(table)
    hit_rows = {item["row"] for item in deduped}
    for i, item in enumerate(raw):
        where = "bonus[%d]" % i
        if not isinstance(item, dict):
            violations.append(v("EMPTY_FIELD", where, "bonus 项不是映射"))
            continue
        key = item.get("key")
        if not nonempty(key) or str(key) not in BONUS_KEYS:
            violations.append(v("ENUM_INVALID", where + ".key",
                                "key 越界：%s（合法集 %s）"
                                % (key, "|".join(BONUS_KEYS))))
            continue
        points = item.get("points")
        if points not in (0, BONUS_POINTS) or isinstance(points, bool):
            violations.append(v("ENUM_INVALID", where + ".points",
                                "points 只许 0 或 %d（无部分分），实为 %s"
                                % (BONUS_POINTS, points)))
            continue
        if points == BONUS_POINTS:
            conflicted = sorted(guards.get(str(key), set()) & hit_rows)
            if conflicted:
                violations.append(v("SET_MISMATCH", where,
                                    "矛盾复核：%s 得 %d 分，但对应规则行在 findings 中命中"
                                    "（%s）" % (key, BONUS_POINTS, "、".join(conflicted))))
                continue
            applied.append(str(key))
            total += points
    if total > BONUS_MAX:
        violations.append(v("SET_MISMATCH", "bonus",
                            "bonus 合计 %d 超过上限 %d" % (total, BONUS_MAX)))
    return violations, applied, total


def _dimension_scores(deduped, table):
    scores = {}
    for dim in DIMENSIONS:
        penalty = 0
        for item in deduped:
            spec = table.get(item["row"], {})
            if dim in (spec.get("dimensions") or []):
                penalty += DIMENSION_WEIGHTS[item["severity"]]
        scores[dim] = max(0, 100 - penalty)
    return scores


def compute_ledger(findings_doc, table):
    """账本纯函数：入口校验 → severity 复算 → 去重 → 账本 + 维度分。"""
    violations, plain = _finding_violations(items(findings_doc, "findings"), table)
    deduped, duplicates = _dedupe(plain)
    counts = _severity_counts(deduped)
    ded_total = sum(counts[sev] * DEDUCTION_WEIGHTS[sev] for sev in SEVERITIES)
    bonus_violations, applied, bonus_total = _bonus_violations(
        findings_doc.get("bonus") if isinstance(findings_doc, dict) else None,
        deduped, table)
    violations += bonus_violations
    score = clamp_score(100 - ded_total + bonus_total)
    return {
        "violations": violations,
        "deductions": {"critical": counts["CRITICAL"], "high": counts["HIGH"],
                       "medium": counts["MEDIUM"], "low": counts["LOW"],
                       "total": ded_total},
        "bonus": {"applied": applied, "total": bonus_total},
        "dimensions": _dimension_scores(deduped, table),
        "score": score,
        "grade": grade_of(score),
        "recommendation": recommend_of(counts, score),
        "counts": {"findings": len(items(findings_doc, "findings")),
                   "deduped": len(deduped), "duplicates": duplicates,
                   "by_severity": {k: val for k, val in counts.items() if val}},
    }


def cmd_score(args):
    criteria = load_criteria()
    root = os.path.abspath(args.project_root)
    out = os.path.abspath(args.output_dir)
    path = args.findings if os.path.isabs(args.findings) \
        else os.path.join(root, args.findings)
    show = display_path(path, root)
    payload = {"ok": False, "command": "score", "project_root": args.project_root,
               "output_dir": os.path.normpath(out).replace("\\", "/"),
               "deductions": {}, "bonus": {}, "dimensions": {}, "score": None,
               "grade": None, "recommendation": None,
               "violations": [], "warnings": [], "counts": {}}
    findings_doc, err = load_yaml_safe(path) if path.endswith(".yaml") else _load_json(path)
    if findings_doc is None and err is None:
        payload["violations"] = [v("MISSING_FILE", show,
                                   "findings.json 不存在（03 步先产出 findings 载体）")]
        emit_via(payload, args.json, human_score)
        return 1
    if err is not None:
        payload["violations"] = [v("UNPARSABLE_YAML", show, "findings 载体解析失败：%s" % err)]
        emit_via(payload, args.json, human_score)
        return 1
    if not isinstance(findings_doc, dict):
        payload["violations"] = [v("EMPTY_FIELD", show, "findings 载体顶层不是映射")]
        emit_via(payload, args.json, human_score)
        return 1
    ledger = compute_ledger(findings_doc, criteria)
    payload.update({k: ledger[k] for k in ("deductions", "bonus", "dimensions", "score",
                                           "grade", "recommendation", "counts")})
    payload["violations"] = ledger["violations"]
    payload["ok"] = not ledger["violations"]
    emit_via(payload, args.json, human_score)
    return 0 if payload["ok"] else 1


def _load_json(path):
    if not os.path.isfile(path):
        return None, None
    try:
        with io.open(path, "r", encoding="utf-8") as f:
            return json.load(f), None
    except (ValueError, OSError) as e:
        return None, str(e)


def human_score(payload):
    if not payload["ok"]:
        for item in payload["violations"]:
            print("拒绝 %s %s: %s" % (item["code"], item["where"], item["msg"]))
        return
    d = payload["deductions"]
    print("账本：CRITICAL %d / HIGH %d / MEDIUM %d / LOW %d → 扣分 %d；bonus %d"
          % (d["critical"], d["high"], d["medium"], d["low"], d["total"],
             payload["bonus"]["total"]))
    print("评分：%d（%s）→ %s" % (payload["score"], payload["grade"],
                                payload["recommendation"]))
    print("维度：" + " ".join("%s=%d" % (k, val)
                              for k, val in payload["dimensions"].items()))
