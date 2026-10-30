# -*- coding: utf-8 -*-
"""diy-test-gate check 记录级：coverage 重算 + 门决策自洽 + check_record 编排。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gate_check_rules import (  # noqa: E402
    check_compliance, check_criteria, check_cross_domain, check_nfr,
    check_waivers, recompute_mutation_score,
)
from gate_lib import (  # noqa: E402
    AC_RE, BLOCKER_KINDS, COVERAGE_VALUES, COVERED_VALUES, CRITERION_RESULTS,
    DECISIONS, ORACLE_CONFIDENCES, ORACLE_SOURCES, PRIORITIES, RECORD_STATUSES,
    TC_TYPES, TG_RE, all_strings, is_int, items_of, meets, nonempty, pct_int,
    pct_str, v,
)

def check_coverage(record, where, violations, ctx):
    """引用解析 + totals / by_level 重算（产物自身 schema 校验，自实现）。"""
    coverage = record.get("coverage")
    if not isinstance(coverage, dict):
        violations.append(v("EMPTY_FIELD", where + ".coverage", "coverage 缺失"))
        return []
    rows = coverage.get("items")
    if not isinstance(rows, list) or not rows:
        violations.append(v("EMPTY_FIELD", where + ".coverage.items",
                            "items 须为非空列表（矩阵行）"))
        return []
    seen, items = set(), []
    for i, item in enumerate(rows):
        spot = "%s.coverage.items[%d]" % (where, i)
        if not isinstance(item, dict):
            violations.append(v("EMPTY_FIELD", spot, "矩阵行不是映射"))
            continue
        ref = str(item.get("ref") or "").strip()
        if not ref:
            violations.append(v("EMPTY_FIELD", spot + ".ref", "矩阵行缺 ref"))
            continue
        if not AC_RE.match(ref):
            violations.append(v("ENUM_INVALID", spot + ".ref",
                                "ref 形态须为 AC-x.y（实为 %s）" % ref))
        elif ref in seen:
            violations.append(v("DUPLICATE_ID", spot + ".ref", "矩阵行 %s 重复" % ref))
        seen.add(ref)
        if ctx["acs"] and ref not in ctx["acs"]:
            violations.append(v("UNKNOWN_ID", spot + ".ref",
                                "%s 在 stories.yaml 中不存在" % ref))
        story = str(item.get("story") or "").strip()
        if not story:
            violations.append(v("EMPTY_FIELD", spot + ".story", "矩阵行缺 story"))
        elif ctx["stories"] and story not in ctx["stories"]:
            violations.append(v("UNKNOWN_ID", spot + ".story",
                                "%s 在 stories.yaml 中不存在" % story))
        priority = str(item.get("priority") or "").strip()
        if priority not in PRIORITIES:
            violations.append(v("ENUM_INVALID", spot + ".priority",
                                "priority 越界：%s（合法集 P0|P1|P2）"
                                % item.get("priority")))
        value = str(item.get("coverage") or "").strip()
        if value not in COVERAGE_VALUES:
            violations.append(v("ENUM_INVALID", spot + ".coverage",
                                "coverage 越界：%s（合法集 %s）"
                                % (item.get("coverage"), "|".join(COVERAGE_VALUES))))
        tests = item.get("tests")
        if not isinstance(tests, list):
            violations.append(v("EMPTY_FIELD", spot + ".tests",
                                "tests 须为列表（已验证 TC，无则空列表）"))
            tests = []
        for j, tid in enumerate(tests):
            if not nonempty(tid):
                violations.append(v("EMPTY_FIELD", "%s.tests[%d]" % (spot, j),
                                    "TC 引用为空"))
            elif ctx["tcs"] and str(tid) not in ctx["tcs"]:
                violations.append(v("UNKNOWN_ID", "%s.tests[%d]" % (spot, j),
                                    "%s 在 test-plan.yaml 中不存在" % tid))
        items.append({"ref": ref, "priority": priority, "coverage": value,
                      "tests": [str(t) for t in tests if nonempty(t)]})
    if not isinstance(coverage.get("heuristics"), list):
        violations.append(v("EMPTY_FIELD", where + ".coverage.heuristics",
                            "heuristics 须为列表（盲区命中，无则空列表）"))
    derived = {"covered": sum(1 for it in items
                              if it["coverage"] in COVERED_VALUES),
               "total": len(items)}
    derived["pct"] = pct_int(derived["covered"], derived["total"])
    declared = coverage.get("totals")
    if not isinstance(declared, dict):
        violations.append(v("EMPTY_FIELD", where + ".coverage.totals",
                            "totals 缺失（covered / total / pct）"))
    elif any(str(declared.get(key)) != str(derived[key])
             for key in ("covered", "total", "pct")):
        violations.append(v("SET_MISMATCH", where + ".coverage.totals",
                            "totals 与矩阵行重算不一致：声明 %s，实际 %s"
                            % (declared, derived)))
    levels = dict.fromkeys(TC_TYPES, 0)
    for item in items:
        for tid in item["tests"]:
            kind = str((ctx["tc_map"].get(tid) or {}).get("type") or "") \
                .strip().lower()
            if kind in levels:
                levels[kind] += 1
    declared_levels = coverage.get("by_level")
    if not isinstance(declared_levels, dict):
        violations.append(v("EMPTY_FIELD", where + ".coverage.by_level",
                            "by_level 缺失（unit / integration / e2e）"))
    elif any(declared_levels.get(key) != levels[key] for key in levels):
        violations.append(v("SET_MISMATCH", where + ".coverage.by_level",
                            "by_level 与已验证 TC 重算不一致：声明 %s，实际 %s"
                            % (declared_levels, levels)))
    return items


def check_gate_decision(record, where, violations, warnings, criteria, domains,
                        waived, coverage_items, ctx, waived_mutants=None):
    """硬判据重算 + decision 自洽（overlay / 域状态 / 两组判据）。

    `waived_mutants` ＝ waivers 里已批准的等价变异体标识：`变异得分` 用它
    从保守分重算为裁定分——未裁定的候选仍留在分母，只有用户登记过的那部分出分母。
    """
    gate = record.get("gate") if isinstance(record.get("gate"), dict) else {}
    decision = str(gate.get("decision") or "").strip().upper()
    status = str(record.get("status") or "").strip()
    hard, soft = criteria
    if not decision:
        if status == "已定稿":
            violations.append(v("EMPTY_FIELD", where + ".gate.decision",
                                "定稿记录须有 decision（PASS|CONCERNS|FAIL）"))
        else:
            warnings.append(v("PENDING_DECISION", where + ".gate.decision",
                              "草稿记录 decision 未定：门决策自洽判定跳过"))
        return
    if decision not in DECISIONS:
        violations.append(v("ENUM_INVALID", where + ".gate.decision",
                            "decision 越界：%s（合法集 PASS|CONCERNS|FAIL；"
                            "无法评估不设档——走 HALT 不落产物）"
                            % gate.get("decision")))
        return
    if not hard or not soft:
        return
    p0 = [it for it in coverage_items if it["priority"] == "P0"]
    p1 = [it for it in coverage_items if it["priority"] == "P1"]
    mutation = ctx["mutation"]
    # 裁定分（用 waivers 里已批准的等价体重算）优先于 report 里的保守分
    final_score, approved_n = recompute_mutation_score(mutation, waived_mutants or set())
    if approved_n:
        mutation["approved_equivalents"] = approved_n
        mutation["score_conservative"] = mutation.get("score")
        mutation["score"] = final_score
        critical = mutation.get("critical")
        if critical and critical.get("score") != 100:
            violations.append(v("CRITERION_STALE",
                                "%s.gate.hard_criteria.变异得分" % where,
                                "critical.score = %s%%（关键路径硬判据须 100%%）"
                                % critical.get("score")))
    derived = {
        "P0 覆盖": pct_str(sum(1 for it in p0
                                   if it["coverage"] in COVERED_VALUES), len(p0))
        if p0 else "n/a",
        "总覆盖": pct_str(
            sum(1 for it in coverage_items if it["coverage"] in COVERED_VALUES),
            len(coverage_items)),
        "P1 覆盖": pct_str(sum(1 for it in p1
                                   if it["coverage"] in COVERED_VALUES), len(p1))
        if p1 else "100%",
        "变异得分": "%d%%" % mutation["score"]
        if mutation["present"] and mutation["score"] is not None else "n/a",
        "非功能致命": len([name for name in domains
                             if str(domains[name].get("status") or "").upper()
                             == "FAIL" and name not in waived]),
        "P0 未覆盖": len([it for it in p0 if it["coverage"] == "NONE"]),
    }
    for name, entry in hard.items():
        if name not in derived:
            continue
        actual = str(entry.get("actual")).strip()
        result = str(entry.get("result")).strip().lower()
        want_actual = str(derived[name])
        if actual != want_actual:
            violations.append(v("CRITERION_STALE",
                                "%s.gate.hard_criteria.%s.actual" % (where, name),
                                "actual 与机械重算不符：声明 %s，重算 %s"
                                % (entry.get("actual"), want_actual)))
        if name == "变异得分" and not mutation["present"] and result != "n/a":
            violations.append(v("CRITERION_STALE",
                                "%s.gate.hard_criteria.%s.result" % (where, name),
                                "mutation-report.yaml 缺席时 result 只能记 n/a"
                                "（日常口径；定稿另判 MISSING_FILE，见 --final 附加）"))
        if want_actual == "n/a":
            want_result = "n/a"
        elif name in ("非功能致命", "P0 未覆盖"):
            want_result = "通过" if int(derived[name]) == 0 else "失败"
        else:
            value = float(want_actual.rstrip("%") or 0)
            want_result = "通过" if meets(value, entry.get("target")) else "失败"
        if result in CRITERION_RESULTS and result != want_result:
            violations.append(v("CRITERION_STALE",
                                "%s.gate.hard_criteria.%s.result" % (where, name),
                                "result 与重算不符：声明 %s，重算 %s"
                                % (result, want_result)))
    hard_fail = [name for name, entry in hard.items()
                 if str(entry.get("result")).strip().lower() == "失败"]
    soft_fail = [name for name, entry in soft.items()
                 if str(entry.get("result")).strip().lower() == "失败"]
    concerns = [name for name in domains
                if str(domains[name].get("status") or "").upper() == "CONCERNS"]
    oracle = record.get("oracle") if isinstance(record.get("oracle"), dict) else {}
    confidence = str(oracle.get("confidence") or "").strip().lower()
    if confidence == "高" and not any(it["tests"] for it in coverage_items):
        confidence = "中"
    overlay = (str(oracle.get("source") or "").strip() == "合成"
               and confidence != "高")
    if hard_fail:
        if decision != "FAIL":
            violations.append(v("DECISION_INCONSISTENT", where + ".gate.decision",
                                "硬判据 失败（%s）而 decision=%s：任一硬指标 失败 → "
                                "必须 FAIL" % ("、".join(hard_fail), decision)))
    elif soft_fail or concerns or overlay:
        if decision == "PASS":
            reason = []
            if soft_fail:
                reason.append("软判据 失败（%s）" % "、".join(soft_fail))
            if concerns:
                reason.append("NFR 域 CONCERNS（%s）" % "、".join(concerns))
            if overlay:
                reason.append("overlay 命中（合成 oracle 且 confidence≠高）")
            violations.append(v("DECISION_INCONSISTENT", where + ".gate.decision",
                                "%s → 门至少 CONCERNS，不得 PASS" % "；".join(reason)))
    elif decision != "PASS":
        violations.append(v("DECISION_INCONSISTENT", where + ".gate.decision",
                            "两组判据全 通过 且无域 CONCERNS / overlay 命中："
                            "decision 须为 PASS（实为 %s）" % decision))


def check_record(index, record, final, show, ctx, violations, warnings):
    where = "%s gates[%d]" % (show, index)
    if not isinstance(record, dict):
        violations.append(v("EMPTY_FIELD", where, "记录不是映射"))
        return
    rid = str(record.get("id") or "").strip()
    if not rid:
        violations.append(v("EMPTY_FIELD", where + ".id", "记录缺 id"))
    elif not TG_RE.match(rid):
        violations.append(v("ENUM_INVALID", where + ".id",
                            "ID 形态须为 TG-###（实为 %s）" % rid))
    if not nonempty(record.get("date")):
        violations.append(v("EMPTY_FIELD", where + ".date", "记录缺 date"))
    status = str(record.get("status") or "").strip()
    if status not in RECORD_STATUSES:
        violations.append(v("ENUM_INVALID", where + ".status",
                            "status 越界：%s（合法集 草稿|已定稿）"
                            % record.get("status")))
    if str(record.get("scope") or "").strip() != "story":
        violations.append(v("ENUM_INVALID", where + ".scope",
                            "scope 唯一合法值 = story（epic / release 为 v2 推迟项）"))
    story = str(record.get("story") or "").strip()
    if not story:
        violations.append(v("EMPTY_FIELD", where + ".story", "记录缺 story"))
    elif ctx["stories"] and story not in ctx["stories"]:
        violations.append(v("UNKNOWN_ID", where + ".story",
                            "%s 在 stories.yaml 中不存在" % story))
    oracle = record.get("oracle")
    if not isinstance(oracle, dict):
        violations.append(v("EMPTY_FIELD", where + ".oracle", "oracle 缺失"))
    else:
        source = str(oracle.get("source") or "").strip()
        if source not in ORACLE_SOURCES:
            violations.append(v("ENUM_INVALID", where + ".oracle.source",
                                "oracle.source 越界：%s（合法集 %s）"
                                % (oracle.get("source"), "|".join(ORACLE_SOURCES))))
        if str(oracle.get("confidence") or "").strip() not in ORACLE_CONFIDENCES:
            violations.append(v("ENUM_INVALID", where + ".oracle.confidence",
                                "oracle.confidence 越界：%s（合法集 高|中|低）"
                                % oracle.get("confidence")))
        if not is_int(oracle.get("items")):
            violations.append(v("ENUM_INVALID", where + ".oracle.items",
                                "oracle.items 须为整数"))
        if source == "合成" and not items_of(oracle, "inferred"):
            violations.append(v("EMPTY_FIELD", where + ".oracle.inferred",
                                "source=合成 时 inferred 必填"
                                "（合成推断条目清单）"))
        if oracle.get("unresolved") is not None \
                and not isinstance(oracle.get("unresolved"), list):
            violations.append(v("EMPTY_FIELD", where + ".oracle.unresolved",
                                "unresolved 须为列表"))
    items = check_coverage(record, where, violations, ctx)
    domains = check_nfr(record, where, violations)
    check_compliance(record, where, violations, final)
    check_cross_domain(record, where, violations, domains, final)
    waived, waived_mutants = check_waivers(
        record, where, violations,
        candidates=(ctx.get("mutation") or {}).get("candidates"))
    criteria = check_criteria(record, where, violations)
    gate = record.get("gate") if isinstance(record.get("gate"), dict) else {}
    if gate.get("blockers") is not None \
            and not isinstance(gate.get("blockers"), list):
        violations.append(v("EMPTY_FIELD", where + ".gate.blockers",
                            "blockers 须为列表"))
    for i, blocker in enumerate(items_of(gate, "blockers")):
        spot = "%s.gate.blockers[%d]" % (where, i)
        if not isinstance(blocker, dict) or not nonempty(blocker.get("ref")):
            violations.append(v("EMPTY_FIELD", spot + ".ref", "blocker 缺 ref"))
            continue
        if str(blocker.get("kind") or "").strip() not in BLOCKER_KINDS:
            violations.append(v("ENUM_INVALID", spot + ".kind",
                                "kind 越界：%s（合法集 %s）"
                                % (blocker.get("kind"), "|".join(BLOCKER_KINDS))))
        if not nonempty(blocker.get("why")):
            violations.append(v("EMPTY_FIELD", spot + ".why", "blocker 缺 why"))
    if not isinstance(gate.get("recommendations"), list):
        violations.append(v("EMPTY_FIELD", where + ".gate.recommendations",
                            "recommendations 须为列表"))
    if not isinstance(record.get("open_questions"), list):
        violations.append(v("EMPTY_FIELD", where + ".open_questions",
                            "open_questions 须为列表（未决项显式落点）"))
    check_gate_decision(record, where, violations, warnings, criteria, domains,
                        waived, items, ctx, waived_mutants)
    if final:
        if status != "已定稿":
            violations.append(v("STATUS_MISMATCH", where + ".status",
                                "--final 要求 status 已落「已定稿」（实为 %s）"
                                % (record.get("status") or "缺失")))
        if not (ctx.get("mutation") or {}).get("present"):
            violations.append(v("MISSING_FILE",
                                where + ".gate.hard_criteria.变异得分",
                                "--final 要求 mutation-report.yaml 在场（日常 run 记 n/a 合法，"
                                "定稿不得）：先经 `diyc.py mutate` 真跑一次变异"))
        if not nonempty(gate.get("basis")):
            violations.append(v("EMPTY_FIELD", where + ".gate.basis",
                                "--final 要求 basis 非空（决策依据一句话）"))
        if any("[假设]" in text for text in all_strings(record)):
            violations.append(v("ASSUMPTION_PRESENT", where,
                                "--final 要求零 [假设]；未决推断须先落定"))
