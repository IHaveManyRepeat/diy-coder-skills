# -*- coding: utf-8 -*-
"""diy-test-gate check 面：`{output_dir}/test-gate.yaml` 校验（TG-### 集合）。

校验面：schema / 枚举（scope / status / coverage / priority / 域状态 / risk / decision /
判据名与 target / waiver 键）/ 记录 ID 唯一 / 引用解析（产物自身的 AC / TC / S 存在性——
test-gate 不在 diyc 类型集内，本模块自实现，不与 diyc 已覆盖规则重复）/ totals 与
by_level 重算 / 门决策自洽（硬判据 actual 重算 + 两组判据与 decision 的关系 + overlay
与 NFR 域状态）/ waiver 8 键契约（安全域 FAIL 不可豁免）/ 阈值 source 强制记出处 /
合规五标准的记账与聚合（G-3，第五个走查维度，落 `nfr.domains[].findings`）；
`--final` 附加：status 已落 已定稿、basis 非空、hard / soft 两组判据齐、零 [假设]、
合规五标准逐条记账、跨域合成候选的落点（G-4）；
`mutation-report.yaml` 缺席按过渡期口径只记 warning（C 阶段落地后翻硬门）。

本模块只重算「同记录内可机械重算」的量（判据 actual、totals、by_level、overall_risk、
非功能致命、P0 未覆盖、变异得分、合规聚合）——不重跑 collect 的覆盖判定表
（那是 `gate.py collect` 与 steps/03 LLM 复核的职责），避免二份实现。本模块不写盘。

违约码：复用 batch3-contract §3 冻结集（MISSING_FILE / UNPARSABLE_YAML / DUPLICATE_ID /
UNKNOWN_ID / ENUM_INVALID / EMPTY_FIELD / ASSUMPTION_PRESENT / SET_MISMATCH /
STATUS_MISMATCH / EVIDENCE_MISSING / PENDING_DECISION）+ diyc 委派降级码 TOOL_MISSING /
TOOL_ERROR（B1 diy-readiness-check 先例）。本技能新增码（本批申报，见回报）：
  DECISION_INCONSISTENT  门决策与两组判据 / NFR 域状态 / overlay 不自洽
  CRITERION_STALE        判据 actual/result 与从同记录机械重算的值不一致
  WAIVER_INCOMPLETE      waiver 缺 8 键契约中的键（或值为空）
  WAIVER_INAPPLICABLE    waiver ref 指向 安全域（不可豁免）或不可解析的域名
  THRESHOLD_UNSOURCED    阈值 source 非「用户会话 <date>」形态（阈值不得猜测）
  UNKNOWN_THRESHOLD_PASS 域含 UNKNOWN 阈值却记 PASS（nfr-status-definitions 硬规则）
能力补齐轮新增 4 码（源 trace / nfr checklist 条目，2026-09-18 返工）：
  EVIDENCE_STALE            证据 >7 天（台账 red/green 时间戳 / mutation run 日期）——warning
  COMPLIANCE_UNRECORDED     合规五标准缺记录 / 缺聚合行 / 行形态不合（--final）
  COMPLIANCE_AGGREGATE_MISMATCH  标准聚合行与逐域观察行重算不符（FAIL>PARTIAL>PASS）
  CROSS_DOMAIN_UNRECORDED   跨域风险合成候选命中而未落 recommendations / findings（--final）
"""
# trace: 任务书 §4 check（schema / 门决策自洽 / waiver 契约 / 引用解析 / --final 附加义务）
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gate_lib import (  # noqa: E402
    AC_RE, ADR_ASSET, BLOCKER_KINDS, COMPLIANCE_STANDARDS, COVERAGE_VALUES,
    COVERED_VALUES, CRITERION_RESULTS, DECISIONS,
    DOMAIN_STATUSES, DOMAINS, GATE_FILE, HARD_CRITERIA, ORACLE_CONFIDENCES,
    ORACLE_SOURCES, PLAN_FILE, PRIORITIES, RECORD_STATUSES, RISK_OF_STATUS,
    RISK_VALUES, SOFT_CRITERIA, STORIES_FILE, TC_RE, TC_TYPES, TG_RE,
    USER_SOURCE_RE, WAIVER_KEYS, ac_index, adr_rows, all_strings, compliance_lines,
    compliance_rollup, count_by, cross_domain_hits, display_path, emit, is_int,
    items_of, load_yaml_safe, meets, mutation_block, nonempty, pct_int, pct_str,
    tc_index, v,
)

# ---------------------------------------------------------------- check

def check_criteria(record, where, violations):
    """两组判据：命名集合 / target 固定 / result 枚举 / estimated+algorithm / 齐备。"""
    gate = record.get("gate")
    if not isinstance(gate, dict):
        violations.append(v("EMPTY_FIELD", where + ".gate",
                            "gate 缺失（决策 / 两组判据的载体）"))
        return None, None
    blocks = {}
    for group, expected in (("hard_criteria", HARD_CRITERIA),
                            ("soft_criteria", SOFT_CRITERIA)):
        entries = gate.get(group)
        if not isinstance(entries, list):
            violations.append(v("EMPTY_FIELD", "%s.gate.%s" % (where, group),
                                "%s 缺失（须为列表）" % group))
            blocks[group] = {}
            continue
        allowed = dict(expected)
        by_name = {}
        for i, entry in enumerate(entries):
            spot = "%s.gate.%s[%d]" % (where, group, i)
            if not isinstance(entry, dict):
                violations.append(v("EMPTY_FIELD", spot, "判据条目不是映射"))
                continue
            name = str(entry.get("name") or "").strip()
            if not name:
                violations.append(v("EMPTY_FIELD", spot + ".name", "判据缺 name"))
                continue
            if name in by_name:
                violations.append(v("DUPLICATE_ID", spot + ".name",
                                    "判据 %s 重复" % name))
                continue
            by_name[name] = entry
            if name not in allowed:
                violations.append(v("ENUM_INVALID", spot + ".name",
                                    "未知判据：%s（合法集 %s）"
                                    % (name, "|".join(allowed))))
                continue
            if str(entry.get("target")) != str(allowed[name]):
                violations.append(v("ENUM_INVALID", spot + ".target",
                                    "target 固定为 %s（实为 %s）"
                                    % (allowed[name], entry.get("target"))))
            if str(entry.get("result")) not in CRITERION_RESULTS:
                violations.append(v("ENUM_INVALID", spot + ".result",
                                    "result 越界：%s（合法 通过|失败|n/a）"
                                    % entry.get("result")))
            if entry.get("estimated") is True and not nonempty(entry.get("algorithm")):
                violations.append(v("EMPTY_FIELD", spot + ".algorithm",
                                    "estimated: true 须附 algorithm"
                                    "（LLM 估值必须记算法）"))
        missing = [name for name, _target in expected if name not in by_name]
        if missing:
            violations.append(v("EMPTY_FIELD", "%s.gate.%s" % (where, group),
                                "判据不齐，缺：%s" % "、".join(missing)))
        blocks[group] = by_name
    return blocks.get("hard_criteria"), blocks.get("soft_criteria")


def check_nfr(record, where, violations):
    """NFR 四域 / 阈值出处 / UNKNOWN 降级 / overall_risk 重算 / ADR 行数。"""
    nfr = record.get("nfr")
    domains = {}
    if not isinstance(nfr, dict):
        violations.append(v("EMPTY_FIELD", where + ".nfr", "nfr 缺失（四域证据面）"))
        return domains
    rows = nfr.get("domains")
    if not isinstance(rows, list):
        violations.append(v("EMPTY_FIELD", where + ".nfr.domains", "domains 须为列表"))
        return domains
    for i, domain in enumerate(rows):
        spot = "%s.nfr.domains[%d]" % (where, i)
        if not isinstance(domain, dict):
            violations.append(v("EMPTY_FIELD", spot, "域条目不是映射"))
            continue
        name = str(domain.get("name") or "").strip()
        if name not in DOMAINS:
            violations.append(v("ENUM_INVALID", spot + ".name",
                                "域越界：%s（合法集 %s）"
                                % (name, "|".join(DOMAINS))))
            continue
        if name in domains:
            violations.append(v("DUPLICATE_ID", spot + ".name", "域 %s 重复" % name))
            continue
        domains[name] = domain
        status = str(domain.get("status") or "").strip().upper()
        if status not in DOMAIN_STATUSES:
            violations.append(v("ENUM_INVALID", spot + ".status",
                                "域状态越界：%s（合法集 %s）"
                                % (domain.get("status"), "|".join(DOMAIN_STATUSES))))
        unknown = False
        thresholds = domain.get("thresholds")
        if not isinstance(thresholds, list):
            violations.append(v("EMPTY_FIELD", spot + ".thresholds",
                                "thresholds 须为列表（无阈值写空列表）"))
            thresholds = []
        for j, threshold in enumerate(thresholds):
            tide = "%s.thresholds[%d]" % (spot, j)
            if not isinstance(threshold, dict):
                violations.append(v("EMPTY_FIELD", tide, "阈值条目不是映射"))
                continue
            for key in ("name", "target", "source"):
                if not nonempty(threshold.get(key)):
                    violations.append(v("EMPTY_FIELD", tide + "." + key,
                                        "阈值 %s 缺失（阈值不得猜测）" % key))
            source = str(threshold.get("source") or "")
            if nonempty(source) and not USER_SOURCE_RE.match(source.strip()):
                violations.append(v("THRESHOLD_UNSOURCED", tide + ".source",
                                    "阈值出处须为「用户会话 <date>」形态（实为 %s）；"
                                    "其余来源一律 UNKNOWN + gap" % source))
            if str(threshold.get("target") or "").strip().upper() == "UNKNOWN":
                unknown = True
        if unknown and status == "PASS":
            violations.append(v("UNKNOWN_THRESHOLD_PASS", spot + ".status",
                                "域含 UNKNOWN 阈值却记 PASS：未测目标不得 PASS"
                                "（须 CONCERNS，见 nfr-status-definitions）"))
        if domain.get("findings") is not None \
                and not isinstance(domain.get("findings"), list):
            violations.append(v("EMPTY_FIELD", spot + ".findings", "findings 须为列表"))
    missing = [name for name in DOMAINS if name not in domains]
    if missing:
        violations.append(v("EMPTY_FIELD", where + ".nfr.domains",
                            "四域不齐，缺：%s" % "、".join(missing)))
    adr = nfr.get("adr")
    expected_rows = adr_rows()
    if not isinstance(adr, dict):
        violations.append(v("EMPTY_FIELD", where + ".nfr.adr",
                            "adr 缺失（{rows, passed}，行数 = 技能内 %s）" % ADR_ASSET))
    else:
        rows_n, passed = adr.get("rows"), adr.get("passed")
        if not is_int(rows_n) or not is_int(passed):
            violations.append(v("ENUM_INVALID", where + ".nfr.adr",
                                "adr.rows / adr.passed 须为非负整数"))
        else:
            if expected_rows is not None and rows_n != expected_rows:
                violations.append(v("SET_MISMATCH", where + ".nfr.adr.rows",
                                    "清单行数须为 %s（实为 %s）"
                                    % (expected_rows, rows_n)))
            if passed > rows_n or passed < 0:
                violations.append(v("ENUM_INVALID", where + ".nfr.adr.passed",
                                    "passed 越界：%s/%s" % (passed, rows_n)))
    gaps = nfr.get("gaps")
    if not isinstance(gaps, list):
        violations.append(v("EMPTY_FIELD", where + ".nfr.gaps",
                            "gaps 须为列表（证据缺口，替代猜阈值）"))
    else:
        for i, gap in enumerate(gaps):
            if not isinstance(gap, dict) or not nonempty(gap.get("what")) \
                    or not nonempty(gap.get("why")):
                violations.append(v("EMPTY_FIELD",
                                    "%s.nfr.gaps[%d]" % (where, i),
                                    "证据缺口须带 what + why"))
    declared = str(nfr.get("overall_risk") or "").strip().upper()
    if declared not in RISK_VALUES:
        violations.append(v("ENUM_INVALID", where + ".nfr.overall_risk",
                            "overall_risk 越界：%s（合法集 %s）"
                            % (nfr.get("overall_risk"), "|".join(RISK_VALUES))))
    else:
        computed = "NONE"
        for domain in domains.values():
            risk = RISK_OF_STATUS.get(str(domain.get("status") or "").upper())
            if risk and RISK_VALUES.index(risk) < RISK_VALUES.index(computed):
                computed = risk
        if computed != declared:
            violations.append(v("SET_MISMATCH", where + ".nfr.overall_risk",
                                "overall_risk 须为 max(域状态映射)（重算 %s，声明 %s）"
                                % (computed, declared)))
    return domains


def check_compliance(record, where, violations, final):
    """G-3 第五走查维度：五标准的行形态 / 记账完整 / 聚合 FAIL>PARTIAL>PASS。"""
    nfr = record.get("nfr") if isinstance(record.get("nfr"), dict) else {}
    if not items_of(nfr, "domains"):
        return          # 域面整体缺失由 check_nfr 报；此处不叠五条噪声
    findings = {}
    for domain in items_of(nfr, "domains"):
        if isinstance(domain, dict) and isinstance(domain.get("findings"), list):
            findings[str(domain.get("name") or "")] = [
                str(row) for row in domain["findings"] if nonempty(row)]
    parsed, problems = compliance_lines(findings)
    spot = where + ".nfr.domains[].findings"
    for standard, text in problems:
        violations.append(v("COMPLIANCE_UNRECORDED", spot,
                            "合规行形态不合（%s）：%s——须 `<标准>[@<域>]: "
                            "PASS|PARTIAL|FAIL|N/A — <依据>`" % (standard, text)))
    for standard in COMPLIANCE_STANDARDS:
        entry = parsed.get(standard)
        if entry is None:
            if final:
                violations.append(v("COMPLIANCE_UNRECORDED", spot,
                                    "%s 无合规记录（--final 要求五标准逐条记账；"
                                    "不适用写 `%s: N/A — <理由>`）"
                                    % (standard, standard)))
            continue
        if not entry["aggregates"]:
            if final:
                violations.append(v("COMPLIANCE_UNRECORDED", spot,
                                    "%s 只有逐域观察行、缺聚合行（`%s: <状态> — <依据>`）"
                                    % (standard, standard)))
            continue
        if len(entry["aggregates"]) > 1:
            violations.append(v("COMPLIANCE_AGGREGATE_MISMATCH", spot,
                                "%s 的聚合行自相矛盾：%s"
                                % (standard, "、".join(entry["aggregates"]))))
            continue
        want = compliance_rollup([state for _name, state in entry["observations"]])
        if want and entry["aggregates"][0] != want:
            violations.append(v("COMPLIANCE_AGGREGATE_MISMATCH", spot,
                                "%s 聚合须为 %s（FAIL>PARTIAL>PASS 由逐域观察行重算），"
                                "声明 %s" % (standard, want, entry["aggregates"][0])))


def check_cross_domain(record, where, violations, domains, final):
    """G-4 跨域风险合成：候选命中时须在 recommendations / findings 留 `<域>×<域>` 行。"""
    if not final:
        return
    statuses = {name: str(domains[name].get("status") or "").upper()
                for name in domains}
    gate = record.get("gate") if isinstance(record.get("gate"), dict) else {}
    lines = [str(row) for row in items_of(gate, "recommendations")]
    for domain in domains.values():
        lines.extend(str(row) for row in items_of(domain, "findings"))
    text = "\n".join(lines)
    for hit in cross_domain_hits(statuses):
        if hit["marker"] in text:
            continue
        state = "、".join("%s=%s" % (name, statuses[name]) for name in hit["pair"])
        violations.append(v("CROSS_DOMAIN_UNRECORDED", where + ".gate.recommendations",
                            "跨域合成候选命中（%s；impact=%s）：须在 recommendations 或"
                            "相关域 findings 写一行 `%s: <判定与理由>`——判定不成立也要"
                            "写明为什么不成立"
                            % (state, hit["impact"], hit["marker"])))


def check_waivers(record, where, violations):
    """waiver 8 键契约 + 安全域不可豁免；返回已豁免域名集合。"""
    gate = record.get("gate") if isinstance(record.get("gate"), dict) else {}
    waivers = gate.get("waivers")
    waived = set()
    if not isinstance(waivers, list):
        violations.append(v("EMPTY_FIELD", where + ".gate.waivers",
                            "waivers 须为列表（无豁免写空列表）"))
        return waived
    for i, waiver in enumerate(waivers):
        spot = "%s.gate.waivers[%d]" % (where, i)
        if not isinstance(waiver, dict):
            violations.append(v("WAIVER_INCOMPLETE", spot, "waiver 条目不是映射"))
            continue
        missing = [key for key in WAIVER_KEYS if not nonempty(waiver.get(key))]
        if missing:
            violations.append(v("WAIVER_INCOMPLETE", spot,
                                "豁免契约缺键（或值为空）：%s；8 键 = %s"
                                % ("、".join(missing), "、".join(WAIVER_KEYS))))
            continue
        ref = str(waiver["ref"]).strip()
        if ref in DOMAINS:
            if ref == "安全":
                violations.append(v("WAIVER_INAPPLICABLE", spot + ".ref",
                                    "安全域 FAIL 不可豁免（源 checklist 硬规则）"))
            else:
                waived.add(ref)
        elif not (AC_RE.match(ref) or TC_RE.match(ref)):
            violations.append(v("WAIVER_INAPPLICABLE", spot + ".ref",
                                "waiver ref 须为域名 / AC-x.y / TC-x.y.z（实为 %s）"
                                % ref))
    return waived


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
                        waived, coverage_items, ctx):
    """硬判据重算 + decision 自洽（overlay / 域状态 / 两组判据）。"""
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
                                "（过渡期口径，C 阶段前不拒绝）"))
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
    waived = check_waivers(record, where, violations)
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
                        waived, items, ctx)
    if final:
        if status != "已定稿":
            violations.append(v("STATUS_MISMATCH", where + ".status",
                                "--final 要求 status 已落「已定稿」（实为 %s）"
                                % (record.get("status") or "缺失")))
        if not nonempty(gate.get("basis")):
            violations.append(v("EMPTY_FIELD", where + ".gate.basis",
                                "--final 要求 basis 非空（决策依据一句话）"))
        if any("[假设]" in text for text in all_strings(record)):
            violations.append(v("ASSUMPTION_PRESENT", where,
                                "--final 要求零 [假设]；未决推断须先落定"))


def cmd_check(args):
    root = os.path.abspath(args.project_root)
    out = os.path.abspath(args.output_dir)
    path = os.path.join(out, GATE_FILE)
    show = display_path(path, root)
    violations, warnings, records = [], [], []
    data, err = load_yaml_safe(path)
    if data is None and err is None:
        violations.append(v("MISSING_FILE", show,
                            "%s 不存在（先完成一次 test-gate 起草）" % GATE_FILE))
    elif err is not None:
        violations.append(v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err))
    elif not isinstance(data, dict):
        violations.append(v("EMPTY_FIELD", show,
                            "顶层不是映射（须为 project + gates + revisions）"))
    else:
        project = data.get("project")
        if project is not None and not isinstance(project, dict):
            violations.append(v("EMPTY_FIELD", show + " project", "project 不是映射"))
        if data.get("revisions") is not None \
                and not isinstance(data.get("revisions"), list):
            violations.append(v("EMPTY_FIELD", show + " revisions",
                                "revisions 不是列表"))
        raw = data.get("gates")
        if raw is None:
            violations.append(v("EMPTY_FIELD", show + " gates",
                                "gates 缺失（集合形态；无记录写空列表）"))
        elif not isinstance(raw, list):
            violations.append(v("EMPTY_FIELD", show + " gates", "gates 不是列表"))
        else:
            records = raw
            stories, stories_err = load_yaml_safe(os.path.join(out, STORIES_FILE))
            plan, plan_err = load_yaml_safe(os.path.join(out, PLAN_FILE))
            if stories_err is not None or plan_err is not None:
                warnings.append(v("UNPARSABLE_YAML", STORIES_FILE,
                                  "上游产物不可解析：引用解析降级跳过"))
            if stories is None:
                warnings.append(v("MISSING_FILE", STORIES_FILE,
                                  "stories.yaml 缺席：AC / S 引用解析降级跳过"))
            if plan is None:
                warnings.append(v("MISSING_FILE", PLAN_FILE,
                                  "test-plan.yaml 缺席：TC 引用解析降级跳过"))
            _by_ac, tc_map = tc_index(plan or {})
            ctx = {
                "stories": {str(story.get("id") or "")
                            for story in items_of(stories or {}, "stories")
                            if isinstance(story, dict)},
                "acs": {str(ac.get("id") or "") for _story, ac in
                        ac_index(stories or {}) if nonempty(ac.get("id"))},
                "tcs": set(tc_map), "tc_map": tc_map,
                "mutation": mutation_block(out, warnings),
            }
            seen = set()
            for i, record in enumerate(records):
                check_record(i, record, args.final, show, ctx, violations,
                             warnings)
                if isinstance(record, dict) and nonempty(record.get("id")):
                    rid = str(record["id"])
                    if rid in seen:
                        violations.append(v("DUPLICATE_ID",
                                            "%s.gates[%d].id" % (show, i),
                                            "记录 ID %s 重复（TG ID 稳定不重用）"
                                            % rid))
                    seen.add(rid)
            if args.final and not records:
                violations.append(v("EMPTY_FIELD", show + " gates",
                                    "--final 要求至少 1 条记录"))
    gate_rows = [r for r in records if isinstance(r, dict)]
    counts = {
        "gates": len(records),
        "by_status": count_by(gate_rows, "status"),
        "by_decision": count_by(
            [{"decision": (r.get("gate") or {}).get("decision")}
             for r in gate_rows], "decision"),
        "items": sum(len((r.get("coverage") or {}).get("items") or [])
                     for r in gate_rows),
        "blockers": sum(len((r.get("gate") or {}).get("blockers") or [])
                        for r in gate_rows),
        "waivers": sum(len((r.get("gate") or {}).get("waivers") or [])
                       for r in gate_rows),
    }
    ok = not violations
    payload = {
        "ok": ok, "command": "check", "project_root": args.project_root,
        "output_dir": os.path.normpath(out).replace("\\", "/"),
        "final": args.final, "violations": violations, "warnings": warnings,
        "counts": counts,
    }
    emit(payload, args.json, human_check)
    return 0 if ok else 1


def human_check(payload):
    if payload["ok"]:
        print("PASS：%s 校验通过（gates=%d）"
              % (payload["output_dir"] + "/" + GATE_FILE,
                 payload["counts"]["gates"]))
        return
    print("FAIL：")
    for item in payload["violations"]:
        print("- %s %s: %s" % (item["code"], item["where"], item["msg"]))
