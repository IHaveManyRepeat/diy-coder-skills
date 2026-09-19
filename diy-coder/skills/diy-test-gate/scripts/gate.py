# -*- coding: utf-8 -*-
"""diy-test-gate 确定性引擎入口：覆盖率矩阵 join + 单一门决策校验（跨文档核对委派 diyc）。

子命令：
  collect  质量门的确定性采集（只读，零写盘）：
             0 前置门禁（任务书 §4）：stories.yaml / test-plan.yaml（须 project.status:
               final）/ prd.yaml 三件套在场且可解析；`--story S-x` 给出时须在 stories.yaml
               可解析；AC 集为空 → 拒绝。任一项不满足 → 零产出 exit 1 + 结构化拒绝
               （violations + gate.route 给路由）。
             1 矩阵 join：AC（stories）× TC（test-plan）× 证据台账（sprint 任务
               test_refs / evidence）。覆盖判定表逐 TC（任务书 §4）：
               ① status: fail → blocker 不计（fail 胜，即使同 TC 留有 green 记录）；
               ② status: pass 且有 evidence（该 story 任务的台账条目 red/green 均非空；
                  test_refs 只用于查台账归属）→ 已验证；
               ③ status: pass 但无台账 → 已验证 + warning。**本引擎分不出这条 pass
                  是谁写的**（diy-e2e-tests / diy-augment 追加用例不写 evidence 属合法，
                  其余来源应经 diyc green 写回）——warning 带上 technique 供人工核对，
                  替读者摊事实、不替读者下结论；
               ④ pending → 不计。
               AC coverage 五值：无 TC / 全未验证 → NONE；全验证且 type 全 unit →
               UNIT-ONLY；全 integration → INTEGRATION-ONLY；全验证且含 e2e 或 ≥2 类
               type → FULL；部分验证 → PARTIAL。
             2 priority 推导：prd.yaml FR priority（must→P0 / should→P1 / could→P2），
               一 AC 多 FR 取最高；无 FR refs → P2 + warning。
             3 统计：totals / 三线（p0 / p1 / p2）/ by_level / by_tc / by_story + 缺口清单
               （kind：none | partial | blocker | heuristic | accepted_gap |
               test_plan_pending）。5 类盲区启发式按 AC 文本关键词 + 已验证 TC 的层级 /
               技术给**候选**（口径按可读数据面收窄，**不读源码**），最终判定留在
               steps/03-matrix-gaps.md。
             3b 证据时效（G-1）：台账 red/green 里的最新时间戳、`mutation-report.yaml`
               各 run 的 date，超过 EVIDENCE_TTL_DAYS（7）天 → `EVIDENCE_STALE` warning；
               处置（重跑 / 用户确认 + `gate.basis` 注明）留在 steps/03 与 steps/05。
             3c 跨层重复覆盖候选（G-2）：同一 AC 下「同一 technique + 同一 kill_target」
               在 ≥2 个 type 层级各有用例 → `coverage.duplicates`（可接受重叠 / 跨层冗余的
               判定与合并建议留在 steps/03 → `gate.recommendations`）。
             4 软指标六项（soft_metrics，任务书 §4 口径，带 分子 / 分母 / algorithm）。
             5 NFR 证据面（nfr_inputs）：四域 + 阈值载体实测（prd / architecture /
               test-plan 三处候选源均无结构化阈值载体）+ prd NFR 条目参考面 + 合规五标准
               静态清单（G-3，第五个走查维度）+ 跨域风险合成的两条规则（G-4）——两者都是
               **走查纪律的输入面**，判定与落点（`findings` / `recommendations`）在 steps/04，
               校验在 check。
             6 mutation 面：读 {output_dir}/mutation-report.yaml，缺席 → score=null +
               warning（过渡期口径，C 阶段前不拒绝）；在场 → 取全部 run 的 score
               最小值（保守口径）。
             7 跨文档核对委托（任务书 §2.3）：子进程 `diyc.py check --type test-plan
               --final --json`——rc 0|1 均为正常回执，其 violations 进 diyc.violations
               （计入本技能判定，不当失败吞掉）；diyc 缺席 / rc=2 / 回执不可解析 →
               TOOL_MISSING / TOOL_ERROR 结构化降级，不崩。
  check    校验 {output_dir}/test-gate.yaml（TG-### 集合）：schema / 枚举 / 记录 ID 唯一 /
           引用解析（产物自身的 AC / TC / S 存在性——test-gate 不在 diyc 类型集内，本引擎
           自实现，不与 diyc 已覆盖规则重复；跨文档一致性仍委派 diyc）/ totals 与 by_level
           重算 / 门决策自洽（重算硬判据 actual；overlay：synthetic 且 confidence≠high →
           至少 CONCERNS；NFR 域 CONCERNS 或软判据 fail → 至少 CONCERNS；任一硬判据
           fail → 必须 FAIL；全 pass 无域 CONCERNS 无 overlay → 才可 PASS）/ waiver 8 键
           契约（security 域 FAIL 不可豁免）/ 阈值 source 强制记出处；--final 附加：
           status 已落 final、basis 非空、hard / soft 两组判据齐、零 [ASSUMPTION]、
           合规五标准逐条记账（G-3：行形态 + 聚合 FAIL>PARTIAL>PASS 重算）、跨域合成
           候选的落点（G-4：命中而 findings / recommendations 无 `<域>×<域>` 行即违例）；
           mutation-report 缺席按过渡期口径只记 warning。
    check 只重算「同记录内可机械重算」的量（判据 actual、totals、by_level、overall_risk、
    nfr_critical、p0_uncovered、mutation_score）——不重跑 collect 的覆盖判定表（那是
    collect 与 steps/03 LLM 复核的职责），避免二份实现。
    本引擎不写盘：产物由会话（LLM）按 Schema 段创作，引擎只采集与校验。

模块切分对齐 `diy-tools` 先例：本文件 = 入口 + collect 面；`gate_lib.py` = 常量 / 索引 /
diyc 委派 / mutation 面；`gate_check.py` = check 面（懒加载）。违规码全表见 `gate_lib.py`
模块 docstring（W2 建设期 6 码：DECISION_INCONSISTENT / CRITERION_STALE /
WAIVER_INCOMPLETE / WAIVER_INAPPLICABLE / THRESHOLD_UNSOURCED / UNKNOWN_THRESHOLD_PASS；
能力补齐轮 4 码：EVIDENCE_STALE / COMPLIANCE_UNRECORDED /
COMPLIANCE_AGGREGATE_MISMATCH / CROSS_DOMAIN_UNRECORDED）。
"""
# trace: 迁移计划 §二 验收 #3（前置门禁零产出退出）/#4（ID 链接入）/#12（diyc 接线）
# trace: 任务书 §4 W2（门禁 / collect 判定表与软指标）/ §2.2 引擎契约
import argparse
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gate_lib import (  # noqa: E402
    AC_RE, ADR_ASSET, ARCH_FILE, BOUNDARY_TECHNIQUES, BUSINESS_TECHNIQUES,
    COMPLIANCE_STANDARDS, COVERED_VALUES, DOMAINS, EVIDENCE_TTL_DAYS, GATE_ROUTE,
    NEGATIVE_TECHNIQUES, PLAN_FILE, PRD_FILE, SPRINT_FILE, STORIES_FILE,
    TC_TYPES, ac_index, adr_rows, count_by, cross_domain_rules_doc,
    display_path, duplicate_candidates, emit, evidence_index, evidence_stamp,
    fr_index, heuristic_candidates, is_counted, items_of, judge_coverage,
    judge_tc, load_yaml_safe, meets, mutation_block, nonempty, pct_int, pct_str,
    priority_of, ratio, run_diyc_checks, tc_index, v,
)

# ---------------------------------------------------------------- collect


def gate_check(root, out, args):
    """前置门禁（任务书 §4）。返回 (docs, violations, route)。"""
    show = lambda name: display_path(os.path.join(out, name), root)  # noqa: E731
    violations, docs = [], {}

    def take(name, must_final=False):
        data, err = load_yaml_safe(os.path.join(out, name))
        where = show(name)
        if data is None and err is None:
            violations.append(v("MISSING_FILE", where, "%s 不存在" % name))
        elif err is not None:
            violations.append(v("UNPARSABLE_YAML", where, "YAML 解析失败：%s" % err))
        elif not isinstance(data, dict):
            violations.append(v("EMPTY_FIELD", where, "顶层不是映射"))
        else:
            project = data.get("project")
            status = str(project.get("status") or "") \
                if isinstance(project, dict) else ""
            if must_final and status != "final":
                violations.append(v("STATUS_MISMATCH", where + " project.status",
                                    "%s 的 project.status 须为 final（实为 %s）；"
                                    "路由 %s" % (name, status or "缺失",
                                              GATE_ROUTE[name])))
            docs[name] = data

    take(STORIES_FILE)
    take(PLAN_FILE, must_final=True)
    take(PRD_FILE)
    if violations:
        first = str(violations[0]["where"]).split("/")[-1].split()[0]
        return docs, violations, GATE_ROUTE.get(first)
    if str(args.scope or "story") != "story":
        return docs, [v("ENUM_INVALID", "collect --scope",
                        "scope 唯一合法值 = story（epic / release 为 v2 推迟项）")], None

    rows = ac_index(docs[STORIES_FILE])
    if not rows:
        return docs, [v("EMPTY_FIELD", show(STORIES_FILE) + " stories",
                        "oracle 解析不出：stories.yaml 无可用 AC"
                        "（AC 是 diy 默认主源）")], GATE_ROUTE[STORIES_FILE]
    selected = str(args.story or "").strip()
    if selected and selected not in {story for story, _ac in rows}:
        return docs, [v("UNKNOWN_ID", show(STORIES_FILE) + ".stories",
                        "%s 在 stories.yaml 中不存在（--story 定位）" % selected)], \
            GATE_ROUTE[STORIES_FILE]
    return docs, [], None


def build_matrix(docs, args, warnings):
    """矩阵 join：AC × TC × 证据台账（只读）。"""
    stories, plan, prd = docs[STORIES_FILE], docs[PLAN_FILE], docs[PRD_FILE]
    sprint = docs.get(SPRINT_FILE) or {}
    has_sprint = SPRINT_FILE in docs
    frs, bad_frs = fr_index(prd)
    for rid, value in bad_frs:
        warnings.append(v("ENUM_INVALID", "%s %s.priority" % (PRD_FILE, rid),
                          "FR priority 越界：%s（合法 must|should|could）" % value))
    if not has_sprint:
        warnings.append(v("MISSING_FILE", SPRINT_FILE,
                          "sprint.yaml 缺席：live 证据面降级——覆盖只认 test-plan 的 "
                          "status（未经 evidence 台账交叉校验），"
                          "该说明须写进 gate.basis 末句"))
    by_ac, _by_id = tc_index(plan)
    evidence = evidence_index(sprint)
    selected = str(args.story or "").strip()
    today = date.today()
    items, by_tc = [], {key: [] for key in
                        ("verified", "blocked", "missing_evidence", "pending",
                         "unverified")}
    for story, ac in ac_index(stories):
        if selected and story != selected:
            continue
        ref = str(ac.get("id") or "").strip()
        if not nonempty(ref):
            warnings.append(v("EMPTY_FIELD", STORIES_FILE + " acceptance_criteria",
                              "AC 缺 id：跳过该行"))
            continue
        priority = priority_of(ac, frs, warnings,
                              "%s %s" % (STORIES_FILE, ref))
        tcs = []
        story_evidence = evidence.get(story, {})
        for tc in by_ac.get(ref, []):
            entry = story_evidence.get(str(tc.get("id")))
            verdict = judge_tc(tc, story_evidence)
            tcs.append({"id": str(tc["id"]),
                        "type": str(tc.get("type") or "").strip().lower(),
                        "technique": str(tc.get("technique") or "").strip(),
                        "priority": str(tc.get("priority") or "").strip(),
                        "kill_target": tc.get("kill_target"),
                        "steps": tc.get("steps"),
                        "verdict": verdict})
            by_tc[verdict].append(str(tc["id"]))
            if verdict == "missing_evidence" and has_sprint:
                warnings.append(v("EVIDENCE_MISSING",
                                  "%s %s evidence" % (SPRINT_FILE, story),
                                  "%s（technique=%s）status=pass 但该 story 任务无 "
                                  "red/green 台账——设计期技法的用例应经 diyc green "
                                  "写回，无台账需人工核对"
                                  % (tc["id"], tc.get("technique") or "缺")))
            stamp = evidence_stamp(entry, today)
            if stamp and stamp[1] > EVIDENCE_TTL_DAYS:
                warnings.append(v("EVIDENCE_STALE",
                                  "%s %s evidence" % (SPRINT_FILE, story),
                                  "%s 的台账最近记录 %s（%d 天前 > %d 天）：证据时效过期"
                                  "——重跑刷新，或经用户确认后沿用并在 gate.basis 注明"
                                  % (tc["id"], stamp[0], stamp[1],
                                     EVIDENCE_TTL_DAYS)))
        coverage = judge_coverage([tc["verdict"] for tc in tcs],
                                  [tc["type"] for tc in tcs])
        items.append({
            "ref": ref, "story": story, "priority": priority,
            "coverage": coverage,
            "tests": sorted(tc["id"] for tc in tcs if is_counted(tc["verdict"])),
            "blocked": sorted(tc["id"] for tc in tcs if tc["verdict"] == "blocked"),
            "missing_evidence": sorted(tc["id"] for tc in tcs
                                       if tc["verdict"] == "missing_evidence"),
            "_tcs": tcs,
            "_heuristics": heuristic_candidates(ref, story, ac, tcs),
            "_duplicates": duplicate_candidates(ref, story, priority, tcs),
        })
    return items, by_tc


def coverage_block(items):
    """totals / 三线 / by_level / by_story。"""
    def tally(subset):
        covered = sum(1 for it in subset if it["coverage"] in COVERED_VALUES)
        return {"covered": covered, "total": len(subset),
                "pct": pct_int(covered, len(subset))}

    types_of = {tc["id"]: tc["type"] for item in items for tc in item["_tcs"]
                if is_counted(tc["verdict"])}
    levels = {name: sum(1 for value in types_of.values() if value == name)
              for name in TC_TYPES}
    by_story = {}
    for item in items:
        entry = by_story.setdefault(item["story"], {"covered": 0, "total": 0})
        entry["total"] += 1
        if item["coverage"] in COVERED_VALUES:
            entry["covered"] += 1
    for entry in by_story.values():
        entry["pct"] = pct_int(entry["covered"], entry["total"])
    return {
        "totals": tally(items),
        "p0": tally([it for it in items if it["priority"] == "P0"]),
        "p1": tally([it for it in items if it["priority"] == "P1"]),
        "p2": tally([it for it in items if it["priority"] == "P2"]),
        "by_level": levels,
        "by_story": by_story,
    }


def soft_metrics_block(items, plan, ac_story):
    """软指标六项（任务书 §4 口径）。"""
    total_acs = len(items)
    by_technique = {"business": 0, "boundary": 0, "negative": 0}
    p0_depth = p0_total = 0
    for item in items:
        verified = [tc for tc in item["_tcs"] if is_counted(tc["verdict"])]
        techniques = {tc["technique"] for tc in verified}
        if techniques & set(BUSINESS_TECHNIQUES):
            by_technique["business"] += 1
        if techniques & set(BOUNDARY_TECHNIQUES):
            by_technique["boundary"] += 1
        if techniques & set(NEGATIVE_TECHNIQUES):
            by_technique["negative"] += 1
        if item["priority"] == "P0":
            p0_total += 1
            if len({tc["type"] for tc in verified}) >= 2 and \
                    (techniques & set(NEGATIVE_TECHNIQUES)):
                p0_depth += 1
    plan_tcs = [tc for tc in items_of(plan, "test_cases") if isinstance(tc, dict)]
    effective = 0
    chain = 0
    for tc in plan_tcs:
        ac = str(tc.get("ac") or "").strip()
        resolvable = bool(AC_RE.match(ac)) and ac in ac_story
        if resolvable and nonempty(tc.get("kill_target")) and tc.get("steps"):
            effective += 1
        if resolvable:
            chain += 1
    rows = (
        ("business_rule_coverage", "100%", by_technique["business"], total_acs),
        ("boundary_coverage", "100%", by_technique["boundary"], total_acs),
        ("negative_scenario_coverage", ">=90%", by_technique["negative"], total_acs),
        ("p0_depth_full", "100%", p0_depth, p0_total),
        ("effective_case_ratio", ">=95%", effective, len(plan_tcs)),
        ("id_chain_resolvable", "100%", chain, len(plan_tcs)),
    )
    block = {}
    for name, target, numerator, denominator in rows:
        block[name] = {
            "name": name, "target": target,
            "numerator": numerator, "denominator": denominator,
            "actual": pct_str(numerator, denominator),
            "result": "pass" if meets(ratio(numerator, denominator), target)
                      else "fail",
            "estimated": False,
            "algorithm": "矩阵判定表口径（分子 / 分母见同名回执字段）",
        }
    return block


def gaps_block(items, plan, warnings):
    """缺口清单：none / partial / blocker / heuristic / accepted_gap / pending。"""
    gaps = []
    for item in items:
        if item["coverage"] == "NONE":
            gaps.append({"ref": item["ref"], "story": item["story"],
                         "priority": item["priority"], "kind": "none",
                         "why": "无 TC 或全部未验证（判定表口径）"})
        elif item["coverage"] == "PARTIAL":
            gaps.append({"ref": item["ref"], "story": item["story"],
                         "priority": item["priority"], "kind": "partial",
                         "why": "部分 TC 已验证，未达全验证"})
        for tid in item["blocked"]:
            gaps.append({"ref": tid, "story": item["story"],
                         "priority": item["priority"], "kind": "blocker",
                         "why": "判定表 ①：status=fail（fail 胜）——须落 gate.blockers"})
        gaps.extend(item["_heuristics"])
    for gap in items_of(plan, "coverage_gaps"):
        if not isinstance(gap, dict):
            continue
        decision = str(gap.get("decision") or "").strip()
        entry = {"ref": str(gap.get("ac") or ""),
                 "story": str(gap.get("story") or ""), "priority": "",
                 "kind": "accepted_gap",
                 "why": "test-plan coverage_gaps decision=%s：%s"
                        % (decision, gap.get("reason") or "")}
        if decision == "pending":
            entry["kind"] = "test_plan_pending"
            warnings.append(v("PENDING_DECISION", "%s coverage_gaps" % PLAN_FILE,
                              "缺口 %s 仍为 decision: pending（test-plan --final 会拦）"
                              % entry["ref"]))
        gaps.append(entry)
    return gaps


def nfr_block(docs, warnings):
    """NFR 证据面（阈值载体实测 + prd NFR 参考面）。"""
    prd = docs.get(PRD_FILE) or {}
    arch = docs.get(ARCH_FILE) or {}
    plan = docs.get(PLAN_FILE) or {}
    carriers = {"prd": False, "architecture": False, "test_plan": False}
    for nfr in items_of(prd, "nfrs"):
        if isinstance(nfr, dict) and any(key in nfr for key in
                                         ("target", "threshold", "measured")):
            carriers["prd"] = True
    for decision in items_of(arch, "decisions"):
        if isinstance(decision, dict) and any(key in decision for key in
                                              ("threshold", "target", "measured")):
            carriers["architecture"] = True
    if isinstance(plan.get("nfr"), list) or isinstance(plan.get("nfr_thresholds"), list):
        carriers["test_plan"] = True
    if not all(carriers.values()):
        warnings.append(v("EMPTY_FIELD", "nfr_inputs.threshold_carriers",
                          "候选阈值源无结构化阈值载体：阈值唯一合法来源 = 用户会话显式给出"))
    return {
        "domains": list(DOMAINS),
        "threshold_carriers": carriers,
        "threshold_policy": "阈值唯一合法来源 = 用户会话显式给出；其余一律 UNKNOWN + gap"
                            "（禁猜，见 steps/04-nfr.md）",
        "nfr_refs": [{"id": str(nfr.get("id") or ""),
                      "statement": str(nfr.get("statement") or "")}
                     for nfr in items_of(prd, "nfrs") if isinstance(nfr, dict)],
        "architecture_affects": [
            {"id": str(decision.get("id") or ""),
             "affects": [str(x) for x in (decision.get("affects") or [])]}
            for decision in items_of(arch, "decisions")
            if isinstance(decision, dict) and decision.get("affects")],
        "adr_checklist": ADR_ASSET,
        "adr_rows": adr_rows(),
        "compliance_standards": list(COMPLIANCE_STANDARDS),
        "cross_domain_rules": cross_domain_rules_doc(),
    }


def cmd_collect(args):
    root = os.path.abspath(args.project_root)
    out = os.path.abspath(args.output_dir)
    warnings = []
    docs, violations, route = gate_check(root, out, args)
    empty_diyc = {"available": False, "script": "", "checked": [],
                  "violations": [], "counts": {}}
    base = {
        "command": "collect", "project_root": args.project_root,
        "output_dir": os.path.normpath(out).replace("\\", "/"),
        "scope": "story", "story": str(args.story or "").strip() or None,
        "violations": violations, "warnings": warnings,
    }
    if violations:
        base.update({"ok": False, "stories": [], "items": [], "coverage": {},
                     "soft_metrics": {}, "gaps": [], "nfr_inputs": {},
                     "mutation": {}, "diyc": empty_diyc,
                     "gate": {"passed": False, "route": route},
                     "counts": {"items": 0}})
        emit(base, args.json, human_collect)
        return 1
    for name in (SPRINT_FILE, ARCH_FILE):
        data, err = load_yaml_safe(os.path.join(out, name))
        if err is not None:
            warnings.append(v("UNPARSABLE_YAML", name,
                              "%s 解析失败：证据面按缺席处置（%s）" % (name, err)))
        elif isinstance(data, dict):
            docs[name] = data
    diyc_block, diyc_warnings = run_diyc_checks(root, out)
    warnings.extend(diyc_warnings)
    items, by_tc = build_matrix(docs, args, warnings)
    coverage = coverage_block(items)
    coverage["by_tc"] = by_tc
    coverage["duplicates"] = [row for item in items for row in item["_duplicates"]]
    plan = docs[PLAN_FILE]
    ac_story = {str(ac.get("id") or ""): story
                for story, ac in ac_index(docs[STORIES_FILE])}
    storage = [{key: value for key, value in item.items()
                if not key.startswith("_")} for item in items]
    gaps = gaps_block(items, plan, warnings)
    base.update({
        "ok": True,
        "stories": sorted({item["story"] for item in items}),
        "items": storage,
        "coverage": coverage,
        "soft_metrics": soft_metrics_block(items, plan, ac_story),
        "gaps": gaps,
        "nfr_inputs": nfr_block(docs, warnings),
        "mutation": mutation_block(out, warnings),
        "diyc": diyc_block,
        "gate": {"passed": True, "route": None},
        "counts": {"items": len(items),
                   "by_coverage": count_by(storage, "coverage"),
                   "by_priority": count_by(storage, "priority"),
                   "gaps": len(gaps),
                   "blocked_tcs": len(by_tc["blocked"]),
                   "duplicates": len(coverage["duplicates"]),
                   "stale_evidence": len([warn for warn in warnings
                                          if warn["code"] == "EVIDENCE_STALE"]),
                   "diyc_violations": len(diyc_block["violations"])},
    })
    emit(base, args.json, human_collect)
    return 0


# ---------------------------------------------------------------- check（懒加载）

def cmd_check(args):
    """check 子命令：懒加载 gate_check（模块缺失与 argparse 用法错误同级处理，rc=2）。"""
    try:
        import gate_check
    except ImportError as err:
        print("gate_check.py 缺失或不可导入：%s" % err, file=sys.stderr)
        return 2
    return gate_check.cmd_check(args)


# ---------------------------------------------------------------- 输出

def human_collect(payload):
    if payload["ok"]:
        print("PASS：矩阵 %d 行（覆盖 %s%%），缺口 %d 条，重复覆盖候选 %d 条"
              "（时效告警 %d），diyc 违规 %d 条"
              % (payload["counts"]["items"],
                 payload["coverage"]["totals"]["pct"],
                 payload["counts"]["gaps"],
                 payload["counts"].get("duplicates", 0),
                 payload["counts"].get("stale_evidence", 0),
                 payload["counts"].get("diyc_violations", 0)))
        for item in payload["warnings"]:
            print("- WARN %s %s: %s" % (item["code"], item["where"], item["msg"]))
        return
    print("FAIL：")
    for item in payload["violations"]:
        print("- %s %s: %s" % (item["code"], item["where"], item["msg"]))
    if payload["gate"].get("route"):
        print("路由：%s" % payload["gate"]["route"])


def build_parser():
    ap = argparse.ArgumentParser(
        description="diy-test-gate 确定性引擎：覆盖率矩阵 join + 单一门决策校验"
                    "（跨文档核对委派 diyc）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("collect",
                       help="前置门禁 + 矩阵 join + 软指标 + NFR / mutation 证据面（只读）")
    c.add_argument("--scope", default="story", help="门范围（唯一合法值 story）")
    c.add_argument("--story", default=None, help="限定单个 story（S-x；缺省扫全部）")
    c.add_argument("--project-root", default=".", help="项目根（默认 .）")
    c.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    c.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    c.set_defaults(func=cmd_collect)

    k = sub.add_parser("check",
                       help="校验 test-gate.yaml（schema/枚举/门决策自洽/waiver 契约；"
                            "--final 附加定稿义务）")
    k.add_argument("--project-root", default=".", help="项目根（默认 .）")
    k.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    k.add_argument("--final", action="store_true",
                   help="定稿校验：status 已落 final + basis 非空 + 两组判据齐 + 零假设")
    k.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    k.set_defaults(func=cmd_check)
    return ap


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = build_parser().parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
