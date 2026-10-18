# -*- coding: utf-8 -*-
"""diy-test-review check 面：scope / findings / score / gaps / walkthrough / 建议逐项校验。"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import nonempty, v  # noqa: E402

from test_review_discover import has_code, is_test_file  # noqa: E402
from test_review_lib import (  # noqa: E402
    AC_RE, BONUS_KEYS, BONUS_MAX, BONUS_POINTS, CONVENTION_ENTRY_STATUSES,
    DEDUCTION_WEIGHTS, DIMENSIONS, EXCLUDED_REASONS, FILE_LEVEL_ROWS, GAP_KINDS,
    GAP_REF_KINDS, GAP_ROUTES, RECOMMENDATIONS_MAX, SEVERITIES, TC_RE,
    WALKTHROUGH_STATUSES, bonus_guard_map, clamp_score, downgrade_severity,
    grade_of, read_text, recommend_of, valid_rows,
)
from test_review_score import _dimension_scores, _severity_counts  # noqa: E402
# ---------------------------------------------------------------- check

def _check_scope(record, where, final):
    violations = []
    scope = record.get("scope")
    if not isinstance(scope, dict):
        return [v("EMPTY_FIELD", where + ".scope", "scope 缺失（paths / files_reviewed / excluded）")]
    paths = scope.get("paths")
    if not isinstance(paths, list):
        violations.append(v("EMPTY_FIELD", where + ".scope.paths", "paths 缺失或不是列表"))
    else:
        for i, p in enumerate(paths):
            if not nonempty(p):
                violations.append(v("EMPTY_FIELD", "%s.scope.paths[%d]" % (where, i),
                                    "paths 项为空"))
        if final and not paths:
            violations.append(v("EMPTY_FIELD", where + ".scope.paths",
                                "--final 要求 scope.paths 非空（scope 非空义务）"))
    reviewed = scope.get("files_reviewed")
    if not isinstance(reviewed, int) or isinstance(reviewed, bool) or reviewed < 0:
        violations.append(v("ENUM_INVALID", where + ".scope.files_reviewed",
                            "files_reviewed 须为非负整数（实为 %s）" % reviewed))
    excluded = scope.get("excluded")
    if not isinstance(excluded, list):
        violations.append(v("EMPTY_FIELD", where + ".scope.excluded",
                            "excluded 缺失或不是列表（无排除写空列表）"))
    else:
        for i, entry in enumerate(excluded):
            ew = "%s.scope.excluded[%d]" % (where, i)
            if not isinstance(entry, dict) or not nonempty(entry.get("path")):
                violations.append(v("EMPTY_FIELD", ew, "excluded 项须带 path"))
                continue
            reason = entry.get("reason")
            if not nonempty(reason):
                violations.append(v("EMPTY_FIELD", ew + ".reason", "reason 缺失"))
            elif str(reason) not in EXCLUDED_REASONS:
                violations.append(v("ENUM_INVALID", ew + ".reason",
                                    "reason 越界：%s（合法集 %s）"
                                    % (reason, "|".join(EXCLUDED_REASONS))))
    return violations


def _check_findings(record, where, table):
    """artifact findings 校验 + 引擎复算（severity / 行号身份 / row ∈ 有效 32 行）。"""
    violations = []
    findings = record.get("findings")
    if not isinstance(findings, list):
        return [v("EMPTY_FIELD", where + ".findings", "findings 缺失或不是列表")], []
    valid = valid_rows(table)
    plain = []
    for i, item in enumerate(findings):
        fw = "%s.findings[%d]" % (where, i)
        if not isinstance(item, dict):
            violations.append(v("EMPTY_FIELD", fw, "finding 不是映射"))
            continue
        row = item.get("row")
        if not nonempty(row) or str(row) not in valid:
            violations.append(v("ENUM_INVALID", fw + ".row",
                                "row 越界：%s（须为有效 32 行；disabled 行 M9/M10/L9 不得出现）"
                                % row))
            continue
        spec = table[str(row)]
        if not nonempty(item.get("file")):
            violations.append(v("EMPTY_FIELD", fw + ".file", "file 缺失"))
            continue
        if not nonempty(item.get("note")):
            violations.append(v("EMPTY_FIELD", fw + ".note", "note 为空（发现须能说清命中什么）"))
            continue
        basis = item.get("basis")
        if nonempty(basis) and str(basis) != str(spec.get("basis")):
            violations.append(v("SET_MISMATCH", fw + ".basis",
                                "声明 basis=%s 与 criteria.yaml 的 %s 不符"
                                % (basis, spec.get("basis"))))
            continue
        line = item.get("line")
        if str(row) in FILE_LEVEL_ROWS:
            if line is not None:
                violations.append(v("ENUM_INVALID", fw + ".line",
                                    "文件级行 %s 的 line 须为 null" % row))
                continue
        elif not isinstance(line, int) or isinstance(line, bool) or line < 1:
            violations.append(v("ENUM_INVALID", fw + ".line",
                                "行级行的 line 须为正整数（实为 %s）" % line))
            continue
        klass = item.get("class")
        if spec.get("basis") == "惯例":
            if str(klass) not in CONVENTION_ENTRY_STATUSES:
                violations.append(v("ENUM_INVALID", fw + ".class",
                                    "convention 行的 class 须为 已确立|新现（实为 %s）"
                                    % klass))
                continue
        elif nonempty(klass):
            violations.append(v("ENUM_INVALID", fw + ".class",
                                "class 仅 basis=惯例 行可带（%s 是 %s 行）"
                                % (row, spec.get("basis"))))
            continue
        expected = downgrade_severity(str(spec.get("severity")), str(klass))
        declared = item.get("severity")
        if str(declared) != expected:
            violations.append(v("SET_MISMATCH", fw + ".severity",
                                "声明 %s 与引擎复算 %s 不符（row=%s，class=%s）"
                                % (declared, expected, row, klass)))
            continue
        plain.append({"row": str(row), "file": str(item["file"]),
                      "line": None if line is None else int(line),
                      "class": str(klass) if nonempty(klass) else None,
                      "severity": expected})
    return violations, plain


def _check_score_block(record, where, deduped, table):
    """账本自洽：findings 计数 → deductions → score/grade/recommendation → 维度分。"""
    violations = []
    block = record.get("score")
    if not isinstance(block, dict):
        return [v("EMPTY_FIELD", where + ".score", "score 区块缺失（五键由 score 命令复算）")]
    counts = _severity_counts(deduped)
    expect_total = sum(counts[sev] * DEDUCTION_WEIGHTS[sev] for sev in SEVERITIES)
    deductions = block.get("deductions")
    if not isinstance(deductions, dict):
        violations.append(v("EMPTY_FIELD", where + ".score.deductions", "deductions 缺失"))
        deductions = {}
    else:
        for key, sev in (("critical", "CRITICAL"), ("high", "HIGH"),
                         ("medium", "MEDIUM"), ("low", "LOW")):
            if deductions.get(key) != counts[sev]:
                violations.append(v("SET_MISMATCH", "%s.score.deductions.%s" % (where, key),
                                    "声明 %s 与 findings 计数 %d 不符"
                                    % (deductions.get(key), counts[sev])))
        if deductions.get("total") != expect_total:
            violations.append(v("SET_MISMATCH", where + ".score.deductions.total",
                                "行相加 %s 与实际 %d 不符（CRITICAL*10 + HIGH*5 + "
                                "MEDIUM*2 + LOW*1）"
                                % (deductions.get("total"), expect_total)))

    bonus_block = block.get("bonus")
    applied = []
    bonus_total = 0
    if not isinstance(bonus_block, dict):
        violations.append(v("EMPTY_FIELD", where + ".score.bonus", "bonus 缺失"))
    else:
        applied = [str(k) for k in (bonus_block.get("applied") or [])]
        for key in applied:
            if key not in BONUS_KEYS:
                violations.append(v("ENUM_INVALID", where + ".score.bonus.applied",
                                    "bonus 键越界：%s（合法集 %s）"
                                    % (key, "|".join(BONUS_KEYS))))
        bonus_total = len(applied) * BONUS_POINTS
        if bonus_block.get("total") != bonus_total:
            violations.append(v("SET_MISMATCH", where + ".score.bonus.total",
                                "声明 %s 与 applied 数 × %d = %d 不符"
                                % (bonus_block.get("total"), BONUS_POINTS, bonus_total)))
        if bonus_total > BONUS_MAX:
            violations.append(v("SET_MISMATCH", where + ".score.bonus",
                                "bonus 合计 %d 超过上限 %d" % (bonus_total, BONUS_MAX)))
        guards = bonus_guard_map(table)
        hit_rows = {item["row"] for item in deduped}
        for key in applied:
            conflicted = sorted(guards.get(key, set()) & hit_rows)
            if conflicted:
                violations.append(v("SET_MISMATCH", "%s.score.bonus.applied" % where,
                                    "矛盾复核：%s 得 %d 分，但对应规则行有命中（%s）"
                                    % (key, BONUS_POINTS, "、".join(conflicted))))

    expected_score = clamp_score(100 - expect_total + bonus_total)
    if block.get("score") != expected_score:
        violations.append(v("SET_MISMATCH", where + ".score.score",
                            "声明 %s 与账本 %d 不符（clamp(100 - deductions + bonus, 0, 100)）"
                            % (block.get("score"), expected_score)))
    if block.get("grade") != grade_of(expected_score):
        violations.append(v("SET_MISMATCH", where + ".score.grade",
                            "声明 %s 与分档 %s 不符（A≥90/B≥80/C≥70/D≥60/F<60）"
                            % (block.get("grade"), grade_of(expected_score))))
    expected_rec = recommend_of(counts, expected_score)
    if block.get("recommendation") != expected_rec:
        violations.append(v("SET_MISMATCH", where + ".score.recommendation",
                            "声明 %s 与推导 %s 不符（recommendation 由计算得出）"
                            % (block.get("recommendation"), expected_rec)))

    dims = record.get("dimensions")
    expected_dims = _dimension_scores(deduped, table)
    if not isinstance(dims, dict):
        violations.append(v("EMPTY_FIELD", where + ".dimensions", "dimensions 缺失"))
    else:
        for dim in DIMENSIONS:
            if dims.get(dim) != expected_dims[dim]:
                violations.append(v("SET_MISMATCH", "%s.dimensions.%s" % (where, dim),
                                    "声明 %s 与复算 %d 不符（每维 = max(0, 100 − Σ该维命中权重))"
                                    % (dims.get(dim), expected_dims[dim])))
    return violations


def _check_gaps(record, where):
    """coverage_gaps 形态：kind 四值 / ref 与 kind 配型 / route ∈ 该 kind 合法集。"""
    violations = []
    gaps = record.get("coverage_gaps")
    if not isinstance(gaps, list):
        return [v("EMPTY_FIELD", where + ".coverage_gaps",
                  "coverage_gaps 缺失或不是列表（无缺口写空列表）")]
    for i, gap in enumerate(gaps):
        gw = "%s.coverage_gaps[%d]" % (where, i)
        if not isinstance(gap, dict):
            violations.append(v("EMPTY_FIELD", gw, "缺口项不是映射"))
            continue
        kind = gap.get("kind")
        ref = gap.get("ref")
        if not nonempty(kind) or str(kind) not in GAP_KINDS:
            violations.append(v("ENUM_INVALID", gw + ".kind",
                                "kind 越界：%s（合法集 %s）" % (kind, "|".join(GAP_KINDS))))
            continue
        pattern = AC_RE if GAP_REF_KINDS[str(kind)] == "ac" else TC_RE
        if not nonempty(ref) or not pattern.fullmatch(str(ref)):
            violations.append(v("SET_MISMATCH", gw + ".ref",
                                "%s 的 ref 须为 %s（实为 %s）"
                                % (kind, "AC-x.y" if GAP_REF_KINDS[str(kind)] == "ac"
                                   else "TC-x.y.z", ref)))
        route = gap.get("route")
        if not nonempty(route):
            violations.append(v("EMPTY_FIELD", gw + ".route", "route 缺失（建议路由必填）"))
        elif str(route) not in GAP_ROUTES[str(kind)]:
            violations.append(v("ENUM_INVALID", gw + ".route",
                                "%s 的 route 越界：%s（合法集 %s）"
                                % (kind, route, "|".join(GAP_ROUTES[str(kind)]))))
        if not nonempty(gap.get("note")):
            violations.append(v("EMPTY_FIELD", gw + ".note", "note 为空"))
    return violations


def _check_walkthrough(record, where, gaps):
    """walkthrough 自洽：skipped → 缺口必空且 note 非空；partial → note 非空。"""
    violations = []
    block = record.get("walkthrough")
    if not isinstance(block, dict):
        return [v("EMPTY_FIELD", where + ".walkthrough", "walkthrough 区块缺失（status / note）")]
    status = block.get("status")
    note = block.get("note")
    if not nonempty(status) or str(status) not in WALKTHROUGH_STATUSES:
        violations.append(v("ENUM_INVALID", where + ".walkthrough.status",
                            "status 越界：%s（合法集 %s）"
                            % (status, "|".join(WALKTHROUGH_STATUSES))))
        return violations
    if str(status) == "已跳过" and gaps:
        violations.append(v("SET_MISMATCH", where + ".walkthrough",
                            "status=已跳过 但 coverage_gaps 非空（%d 条）" % len(gaps)))
    if str(status) in ("已跳过", "部分覆盖") and not nonempty(note):
        violations.append(v("EMPTY_FIELD", where + ".walkthrough.note",
                            "status=%s 时 note 须记缺源与跳过类" % status))
    return violations


def _check_convention_citation(record, where, deduped, table):
    """R-2：convention finding 的 `class` 与 `convention_baseline.keys.<key>.status` 复核。

    源 step-02 §2b 的 CLI 口径逐字：报告里的 `Convention: <key> (<adopted> of <sampled>)`
    引用要与实际测量过的语料对得上，**对不上即拒**（"rejects a report that disagrees"）。
    diy 侧引用面 = finding 的 `class`，测量面 = 产物的 `convention_baseline`；键映射承载于
    criteria.yaml 行字段 `convention_key`（L2→priority_markers / L3→test_ids /
    L5→bdd_naming / L7→assertion_style）。三类拒绝：基线缺该键（引用不可核）、
    status 为 absent/unknown（该行本不成立、不得成条目）、class 与 status 不符。
    """
    violations = []
    keyed = [item for item in deduped
             if table.get(item["row"], {}).get("basis") == "惯例"]
    if not keyed:
        return violations
    baseline = record.get("convention_baseline")
    keys = baseline.get("keys") if isinstance(baseline, dict) else None
    for item in keyed:
        key = table[item["row"]].get("convention_key")
        if not nonempty(key):
            continue  # 注册表未挂键 ⇒ 不可核（该缺口由 criteria 面测试钉住）
        entry = keys.get(str(key)) if isinstance(keys, dict) else None
        status = entry.get("status") if isinstance(entry, dict) else None
        at = "%s.findings[row=%s].class" % (where, item["row"])
        if not nonempty(status):
            violations.append(v("EMPTY_FIELD", at,
                                "convention 引用不可核：convention_baseline.keys.%s.status "
                                "缺席（引用与实际语料独立复测）" % key))
            continue
        if str(status) not in CONVENTION_ENTRY_STATUSES:
            violations.append(v("SET_MISMATCH", at,
                                "基线测到 %s=%s → 该行不成立、不得成条目（引用与实际语料不符）"
                                % (key, status)))
            continue
        if str(item["class"]) != str(status):
            violations.append(v("SET_MISMATCH", at,
                                "声明 class=%s 与 convention_baseline.keys.%s.status=%s 不符"
                                "（引用与实际语料独立复测）"
                                % (item["class"], key, status)))
    return violations


def _check_recommendations(record, where):
    """R-1：`recommendations` 为列表且不超过 Top 10（源 step-03f §4）。

    排序判据（所在维度分 < 70 → HIGH 优先）需要维度归属，由 05 步条文施加；此处只拦
    可机械判定的上限——超限意味着排序切片没有执行。
    """
    recs = record.get("recommendations")
    if not isinstance(recs, list):
        return [v("EMPTY_FIELD", where + ".recommendations",
                  "recommendations 缺失或不是列表（无意见写空列表）")]
    if len(recs) > RECOMMENDATIONS_MAX:
        return [v("SET_MISMATCH", where + ".recommendations",
                  "有 %d 条，超过 Top %d 上限（先按影响力排序：所在维度分 < 70 → HIGH "
                  "在前，再取前 %d）" % (len(recs), RECOMMENDATIONS_MAX,
                                     RECOMMENDATIONS_MAX))]
    return []


def _check_empty_scope_paths(record, where, root):
    """R-3 拦阻：空测试文件不得计入评审集。

    发现面已把空文件归 `excluded`（不评分）；产物若仍把它写进 `scope.paths`，等于把一份
    证明不了任何事的东西记成"已评审"——"100 不是 100" 的入口在此关闭。只判**在场文件**
    （目录条目与已不存在的路径跳过，后者由 excluded 面承载）。
    """
    violations = []
    scope = record.get("scope")
    paths = scope.get("paths") if isinstance(scope, dict) else None
    if not isinstance(paths, list):
        return violations
    for i, rel in enumerate(paths):
        if not nonempty(rel):
            continue
        name = str(rel)
        path = name if os.path.isabs(name) else os.path.join(root, name)
        if not os.path.isfile(path) or not is_test_file(name):
            continue
        if not has_code(read_text(path)):
            violations.append(v("SET_MISMATCH", "%s.scope.paths[%d]" % (where, i),
                                "No tests found：空测试文件不得计入评审集"
                                "（归 excluded(out-of-scope) 不评分）"))
    return violations
