# -*- coding: utf-8 -*-
"""diy-test-gate check 字段级规则：判据 / NFR / 合规 / 跨域 / waiver / 变异分重算。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gate_evidence import (  # noqa: E402
    compliance_lines, compliance_rollup, cross_domain_hits,
)
from gate_lib import (  # noqa: E402
    AC_RE, ADR_ASSET, COMPLIANCE_STANDARDS, CRITERION_RESULTS, DOMAIN_STATUSES,
    DOMAINS, HARD_CRITERIA, MUTANT_REF_PREFIX, RISK_OF_STATUS, RISK_VALUES,
    SOFT_CRITERIA, TC_RE, USER_SOURCE_RE, WAIVER_KEYS, adr_rows, is_int,
    items_of, nonempty, v,
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


def check_waivers(record, where, violations, candidates=None):
    """waiver 8 键契约 + 安全域不可豁免；返回 (已豁免域名集合, 已批准等价变异体集合)。

    ref 四种合法形态：域名（`安全` 不可豁免）/ `AC-x.y` / `TC-x.y.z` / `mutant:<标识>`。
    第四种承载**等价变异体裁定**——`diy-augment` 报的候选只有经用户在此登记后才
    出 `变异得分` 的分母（`candidates` 为本次 report 报出的候选集合，非空时校验
    ref 必须命中其一，防手写错标识导致的假豁免）。
    """
    gate = record.get("gate") if isinstance(record.get("gate"), dict) else {}
    waivers = gate.get("waivers")
    waived, waived_mutants = set(), set()
    if not isinstance(waivers, list):
        violations.append(v("EMPTY_FIELD", where + ".gate.waivers",
                            "waivers 须为列表（无豁免写空列表）"))
        return waived, waived_mutants
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
        elif ref.startswith(MUTANT_REF_PREFIX):
            name = ref[len(MUTANT_REF_PREFIX):].strip()
            if not name:
                violations.append(v("WAIVER_INAPPLICABLE", spot + ".ref",
                                    "%s 后须跟变异体标识（实为空）" % MUTANT_REF_PREFIX))
            elif candidates is not None and name not in candidates:
                violations.append(v("WAIVER_INAPPLICABLE", spot + ".ref",
                                    "变异体 %s 不在 mutation-report.yaml 的等价体候选里"
                                    "（防手写错标识的假豁免）" % name))
            else:
                waived_mutants.add(name)
        elif not (AC_RE.match(ref) or TC_RE.match(ref)):
            violations.append(v("WAIVER_INAPPLICABLE", spot + ".ref",
                                "waiver ref 须为域名 / AC-x.y / TC-x.y.z / "
                                "%s<变异体标识>（实为 %s）" % (MUTANT_REF_PREFIX, ref)))
    return waived, waived_mutants


def recompute_mutation_score(mutation, waived_mutants):
    """用已批准的等价体重算各 run 得分，取最小值；返回 (score, approved_n)。

    保守分（report 里写的，候选全留分母）→ 裁定分（已批准的候选出分母）。
    `score = round(killed / (total − 已批准数) × 100)`；无可用 run 时返回 (None, N)。
    """
    scores, approved_total = [], 0
    for run in mutation.get("detail") or []:
        killed, total = run.get("killed"), run.get("total")
        if not (isinstance(killed, int) and isinstance(total, int)):
            continue
        if isinstance(killed, bool) or isinstance(total, bool):
            continue
        approved = len(set(run.get("equivalents") or []) & set(waived_mutants))
        approved_total += approved
        denom = total - approved
        if denom <= 0:
            continue
        scores.append(killed / denom * 100)
    return (int(min(scores)) if scores else None), approved_total
