# -*- coding: utf-8 -*-
"""diyc check 文档级规则：test-plan（契约 §4.2）。"""

import diyc_lib

from diyc_check_docs_lib import (CASE_TYPES, DIMENSIONS, GAP_DECISIONS, PRIORITIES,
                                 RADII, TC_STATUSES, _api_anchor_ok, _anchor_resolves,
                                 _done_acs, _fh_matches_ac, _openapi_anchors,
                                 dup, enum, is_str, nonempty, req, tc_declarations)
from diyc_lib import items  # noqa: E402

# ---------------------------------------------------------------- test-plan

# Q-114（底单 :884/:889 + 2026-10-20/21 裁）：TC.producer 三生产方标识——前向强制，
# 存量零回填（当前无存量用例）。
TC_PRODUCERS = ("test-design", "augment", "e2e")


def _check_retired(report, where, tc, tc_ids) -> None:
    """Q-111（底单 :902-904 三裁）：TC.retired 可选嵌套键——键在场性即裁决开关
    （缺席＝活跃、在场＝已裁废弃·人闸凭证）；双键必填、replaced_by 指向现存 TC、禁自指。"""
    # rule: diy-test-design/SKILL.md:Schema TC.retired（可选嵌套键·两轴正交·覆盖三层剔除）
    r = tc.get("retired")
    if not isinstance(r, dict):
        report.add("EMPTY_FIELD", where + ".retired",
                   "retired 形状异常（应为 {reason, replaced_by} 映射；键在场＝已裁废弃）")
        return
    req(report, where + ".retired.reason", r.get("reason"),
        "retired.reason（键在场则双键必填）")
    rb = r.get("replaced_by")
    if req(report, where + ".retired.replaced_by", rb,
           "retired.replaced_by（键在场则双键必填·须指向现存 TC）"):
        if rb == tc.get("id"):
            report.add("SET_MISMATCH", where + ".retired.replaced_by",
                       "replaced_by 不得指向自身（须指向替代它的现存 TC）")
        elif not is_str(rb) or rb not in tc_ids:
            report.add("UNKNOWN_ID", where + ".retired.replaced_by",
                       "%r 不在 test_cases 中（须指向现存 TC ID）" % (rb,))

def check_test_plan(doc, rel, docs, final, report) -> dict:
    """test-plan.yaml：用例声明形状 + AC 解析 + 缺口形状；--final 禁 decision: 待办。"""
    # rule: diy-test-design/SKILL.md:Schema（test_cases / static_checks / coverage_gaps）
    # rule: diy-test-design/SKILL.md:Design Discipline（Gaps are decisions, not omissions；
    #       waived must cite prior user confirmation）
    # rule: diy-test-design/SKILL.md:Final requires（zero [假设]，zero decision: 待办
    #       gaps，every ac resolving in stories.yaml，schema-enum technique，non-empty kill_target）
    counts = {"cases": 0, "by_type": {}, "by_priority": {}, "acs_covered": 0,
              "gaps_by_decision": {}, "fhs": 0, "by_dimension": {}}
    project = doc.get("project")
    if not isinstance(project, dict):
        report.add("EMPTY_FIELD", rel + " project", "project 块缺失或形状异常")
    else:
        enum(report, rel + " project.status", project.get("status"),
             ("草稿", "已定稿"), "project.status")

    stories_available = docs.doc("stories") is not None
    known_acs = set(docs.acs()) if stories_available else set()
    if not stories_available:
        report.warn("stories.yaml 缺失/损坏：test_cases[].ac 引用无法解析（跳过该子检查）")
    done_acs = _done_acs(docs) if stories_available else set()

    # FH 段（先铸 id 集合，供 kill_target 引用校验）
    # rule: diy-test-design/SKILL.md:Schema fault_hypotheses（id: FH-x.y.z 与 ac 数字段对应）
    fh_ids = None
    fh_pairs = []
    fhs = doc.get("fault_hypotheses")
    if not isinstance(fhs, list) or not fhs:
        report.add("EMPTY_FIELD", rel + " fault_hypotheses",
                   "fault_hypotheses 缺失或为空（先列故障假设铸 FH，TC 的 kill_target 才有可引的 ID）")
    else:
        fh_ids = set()
        for h in fhs:
            if not isinstance(h, dict):
                report.add("EMPTY_FIELD", rel + " fault_hypotheses[]",
                           "FH 条目形状异常（应为映射）")
                continue
            hid = h.get("id")
            hw = "%s fault_hypotheses[%s]" % (rel, hid or "?")
            if req(report, hw + ".id", hid, "FH id"):
                fh_pairs.append((hid, hw + ".id"))
                fh_ids.add(hid)
            hac = h.get("ac")
            if req(report, hw + ".ac", hac, "FH ac"):
                if stories_available and hac not in known_acs:
                    report.add("UNKNOWN_ID", hw + ".ac",
                               "%s 在 stories.yaml 中不存在" % hac)
                elif is_str(hid) and not _fh_matches_ac(hid, hac):
                    report.add("ENUM_INVALID", hw + ".id",
                               "FH id 数字段须与其 ac 对应：%s ↔ %s（FH-x.y.z 的 x.y = AC-x.y）"
                               % (hid, hac))
            req(report, hw + ".text", h.get("text"), "FH text（具体错误实现的描述）")
            if h.get("radius") is not None:
                enum(report, hw + ".radius", h.get("radius"), RADII, "radius")
        counts["fhs"] = len(fh_ids or ())

    openapi_anchors = _openapi_anchors(docs) if docs.doc("openapi") is not None else {}
    ac_anchors = {}  # AC id -> [复合锚]（stories 铸造；接口门对账用）
    if stories_available:
        for ac_id, entry in docs.acs().items():
            refs = entry.get("api_refs")
            if isinstance(refs, list) and refs:
                ac_anchors[ac_id] = refs

    cases = items(doc, "test_cases", of_type=dict)
    # Q-111：replaced_by 目标集（现存 TC ID，含废弃条目自身——链合法性不在机械门内）
    tc_ids = {t.get("id") for t in cases if is_str(t.get("id"))}
    if not cases:
        report.add("EMPTY_FIELD", rel + " test_cases", "test_cases 缺失或为空")
    tc_pairs = []
    covered = set()
    active_cases = 0
    for t in cases:
        w = "%s test_cases[%s]" % (rel, t.get("id") or "?")
        # Q-111：键在场性即裁决开关——在场＝已裁废弃，覆盖类输入不收废料（虚报活跃数防护）
        is_retired = "retired" in t
        req(report, w + ".id", t.get("id"), "case id")
        req(report, w + ".title", t.get("title"), "title")
        tc_pairs.append((t.get("id"), w + ".id"))
        if not is_retired:
            active_cases += 1
        ac_value = t.get("ac")
        ac_list = diyc_lib._ac_ids(t)
        if not ac_list:
            report.add("EMPTY_FIELD", w + ".ac", "ac 缺失或为空（每个用例须绑定现有 AC ID）")
        elif stories_available:
            for j, ref in enumerate(ac_list):
                where = w + ".ac" if is_str(ac_value) else "%s.ac[%d]" % (w, j)
                if ref not in known_acs:
                    report.add("UNKNOWN_ID", where, "%s 在 stories.yaml 中不存在" % ref)
                elif not is_retired:
                    covered.add(ref)
        if enum(report, w + ".type", t.get("type"), CASE_TYPES, "type") and not is_retired:
            counts["by_type"][t["type"]] = counts["by_type"].get(t["type"], 0) + 1
        if enum(report, w + ".priority", t.get("priority"), PRIORITIES, "priority") \
                and not is_retired:
            counts["by_priority"][t["priority"]] = counts["by_priority"].get(t["priority"], 0) + 1
        if enum(report, w + ".dimension", t.get("dimension"), DIMENSIONS, "dimension") \
                and not is_retired:
            counts["by_dimension"][t["dimension"]] = \
                counts["by_dimension"].get(t["dimension"], 0) + 1
        enum(report, w + ".status", t.get("status"), TC_STATUSES, "status")
        # Q-114：producer 必填（缺失 EMPTY_FIELD）+ 三值枚举（非法值 ENUM_INVALID）——
        # 三生产方（diy-test-design/diy-augment/diy-e2e-tests）追加用例时落笔各自标识。
        # rule: diy-test-design/SKILL.md:Schema TC.producer（必填·前向强制·三生产方标识）
        if req(report, w + ".producer", t.get("producer"), "producer（三生产方标识）"):
            enum(report, w + ".producer", t.get("producer"), TC_PRODUCERS, "producer")
        if is_retired:
            _check_retired(report, w, t, tc_ids)
        tc_declarations(t, w, report, fh_ids=fh_ids)
        api_refs = t.get("api_refs")
        if api_refs is not None:
            # rule: diy-test-design/SKILL.md:Schema TC.api_refs（可选复合锚·点名 AC 锚定的端点）
            if not (isinstance(api_refs, list) and api_refs):
                report.add("EMPTY_FIELD", w + ".api_refs",
                           "api_refs 形状异常（非空列表；缺席即整键省略）")
            else:
                for j, anchor in enumerate(api_refs):
                    pw = "%s.api_refs[%d]" % (w, j)
                    if not _api_anchor_ok(anchor):
                        report.add("EMPTY_FIELD", pw,
                                   "复合锚形状异常（须含 operationId/path/method 三键）")
                    elif openapi_anchors and not _anchor_resolves(anchor, openapi_anchors):
                        report.add("UNKNOWN_ID", pw,
                                   "operationId=%s path=%s method=%s 与 openapi.yaml 不一致"
                                   % (anchor.get("operationId"), anchor.get("path"),
                                      anchor.get("method")))
        steps = t.get("steps")
        if not (isinstance(steps, list) and any(is_str(x) and x.strip() for x in steps)):
            report.add("EMPTY_FIELD", w + ".steps",
                       "steps 缺失或为空（用例须可执行：具体验证步骤 + 预期结果）")
    dup(report, tc_pairs, "case id")
    counts["cases"] = active_cases  # Q-111：counts 剔除 retired（虚报活跃数防护）
    counts["acs_covered"] = len(covered)

    checks = doc.get("static_checks")
    if checks is not None:
        if not isinstance(checks, list):
            report.add("EMPTY_FIELD", rel + " static_checks", "static_checks 形状异常（应为列表）")
        else:
            order_pairs = []
            for i, c in enumerate(checks):
                if not isinstance(c, dict):
                    report.add("EMPTY_FIELD", "%s static_checks[%d]" % (rel, i),
                               "static_check 形状异常（应为映射）")
                    continue
                w = "%s static_checks[order=%s]" % (rel, c.get("order"))
                order = c.get("order")
                if not isinstance(order, int) or isinstance(order, bool):
                    report.add("ENUM_INVALID", w, "order 应为整数（层序，从 1 起）")
                else:
                    order_pairs.append((str(order), w + ".order"))
                req(report, w + ".tool", c.get("tool"), "tool（具体命令或工具名）")
                req(report, w + ".kills", c.get("kills"),
                    "kills（本层杀掉而上层杀不掉的问题类）")
                enum(report, w + ".gate", c.get("gate"), ("阻断", "记录不阻断"), "gate")
            dup(report, order_pairs, "static_checks order")

    gaps = doc.get("coverage_gaps")
    if gaps is not None:
        if not isinstance(gaps, list):
            report.add("EMPTY_FIELD", rel + " coverage_gaps", "coverage_gaps 形状异常（应为列表）")
        else:
            gap_pairs = []
            pending_acs = []
            for i, g in enumerate(gaps or []):
                if not isinstance(g, dict):
                    report.add("EMPTY_FIELD", "%s coverage_gaps[%d]" % (rel, i),
                               "coverage_gap 形状异常（应为映射）")
                    continue
                ac = g.get("ac")
                w = "%s coverage_gaps[%s]" % (rel, ac or "?")
                req(report, w + ".ac", ac, "gap.ac")
                req(report, w + ".reason", g.get("reason"), "reason")
                req(report, w + ".story", g.get("story"), "gap.story")
                if is_str(ac):
                    gap_pairs.append((ac, w + ".ac"))
                    if stories_available and ac not in known_acs:
                        report.add("UNKNOWN_ID", w + ".ac",
                                   "%s 在 stories.yaml 中不存在" % ac)
                decision = g.get("decision")
                if enum(report, w + ".decision", decision, GAP_DECISIONS, "decision"):
                    counts["gaps_by_decision"][decision] = \
                        counts["gaps_by_decision"].get(decision, 0) + 1
                    if decision == "待办":
                        pending_acs.append(str(ac))
                    if decision == "已豁免" and not nonempty(g.get("note")):
                        report.add("EMPTY_FIELD", w + ".note",
                                   "已豁免须注明先前用户确认（日期 + 确认了什么）")
            dup(report, gap_pairs, "coverage_gaps ac")
            if final and pending_acs:
                # rule: diy-test-design/SKILL.md:Final requires（zero decision: 待办 gaps）
                report.add("PENDING_DECISION", rel + " coverage_gaps",
                           "定稿前缺口须由用户裁决（decision: 待办 → 已豁免 / 接受缺口 / 补用例）：%s"
                           % "、".join(pending_acs))

    # 五轴审计段：非已完成 AC × 5 轴每格二选一（tcs 或 not_applicable），双向一致
    # rule: diy-test-design/SKILL.md:Schema dimension_audit（audit 列的 TC 须真绑该 AC 且
    #       dimension 对应；TC.dimension 须出现在其 AC 对应轴；已完成故事整段豁免）
    audit = doc.get("dimension_audit")
    tc_by_id = {t.get("id"): t for t in cases if is_str(t.get("id"))}
    # Q-120：废弃不算覆盖——正向 audited 计入须有非 retired 的 tcs，反向不要求废弃 TC 在场
    retired_ids = {t.get("id") for t in cases
                   if "retired" in t and is_str(t.get("id"))}
    audited = set()
    if audit is None:
        report.add("EMPTY_FIELD", rel + " dimension_audit",
                   "dimension_audit 缺失（每 AC × 5 轴：TC 列表或 not_applicable 理由，二选一）")
    elif not isinstance(audit, list):
        report.add("EMPTY_FIELD", rel + " dimension_audit", "dimension_audit 形状异常（应为列表）")
    else:
        pairs = []
        for e in audit:
            if not isinstance(e, dict):
                report.add("EMPTY_FIELD", rel + " dimension_audit[]",
                           "audit 条目形状异常（应为映射）")
                continue
            ac_id = e.get("ac")
            axis = e.get("axis")
            ew = "%s dimension_audit[%s/%s]" % (rel, ac_id or "?", axis or "?")
            if req(report, ew + ".ac", ac_id, "audit ac") \
                    and stories_available and ac_id not in known_acs:
                report.add("UNKNOWN_ID", ew + ".ac", "%s 在 stories.yaml 中不存在" % ac_id)
            enum(report, ew + ".axis", axis, DIMENSIONS, "axis")
            if is_str(ac_id) and is_str(axis) and axis in DIMENSIONS:
                pairs.append(((ac_id, axis), ew))
                if ac_id not in done_acs:
                    _tcs, _na = e.get("tcs"), e.get("not_applicable")
                    # Q-120：计入条件＝not_applicable 在场，或 tcs 至少一条非 retired
                    #（悬空 ID 不在 retired 集合，保持既有 UNKNOWN_ID 判定不误伤）；
                    # 全废弃＝该格未填（走缺审计格 SET_MISMATCH）；空/畸形格维持既有单错误行为
                    if not (isinstance(_tcs, list) and _tcs) or _na is not None:
                        audited.add((ac_id, axis))
                    elif any(tid not in retired_ids for tid in _tcs):
                        audited.add((ac_id, axis))
            if ac_id in done_acs:
                continue  # 已完成故事豁免：形状查过即过，不进对账
            tcs = e.get("tcs")
            na = e.get("not_applicable")
            if tcs is not None:
                if not (isinstance(tcs, list) and tcs):
                    report.add("EMPTY_FIELD", ew + ".tcs",
                               "tcs 形状异常（非空列表；不适用改用 not_applicable）")
                else:
                    for j, tid in enumerate(tcs):
                        hit = tc_by_id.get(tid)
                        if hit is None:
                            report.add("UNKNOWN_ID", "%s.tcs[%d]" % (ew, j),
                                       "%s 不在 test_cases 中" % tid)
                        elif ac_id not in diyc_lib._ac_ids(hit):
                            report.add("SET_MISMATCH", "%s.tcs[%d]" % (ew, j),
                                       "%s 未绑定 %s（audit 列的 TC 须真绑该 AC）" % (tid, ac_id))
                        elif hit.get("dimension") != axis:
                            report.add("SET_MISMATCH", "%s.tcs[%d]" % (ew, j),
                                       "%s.dimension=%r 与轴 %s 不对应"
                                       % (tid, hit.get("dimension"), axis))
                if na is not None:
                    report.add("EMPTY_FIELD", ew,
                               "tcs 与 not_applicable 二选一，不得并存")
            elif na is not None:
                if not nonempty(na):
                    report.add("EMPTY_FIELD", ew + ".not_applicable",
                               "不适用理由须非空（一行）")
            else:
                report.add("EMPTY_FIELD", ew, "audit 格须二选一：tcs 或 not_applicable")
        dup(report, pairs, "dimension_audit 格")

    if stories_available and isinstance(audit, list):
        expected = {(ac_id, axis) for ac_id in known_acs - done_acs
                    for axis in DIMENSIONS}
        missing = sorted(expected - audited)
        if missing:
            report.add("SET_MISMATCH", rel + " dimension_audit",
                       "缺审计格：%s（每条非已完成 AC × 5 轴逐轴审过：适用→TC，不适用→一行理由）"
                       % "、".join("%s/%s" % m for m in missing))
        for t in cases:
            tid, dim = t.get("id"), t.get("dimension")
            if "retired" in t:
                continue  # Q-120：废弃 TC 不要求出现在 audit（废弃不算覆盖）
            if not (is_str(tid) and dim in DIMENSIONS):
                continue
            for ac_id in diyc_lib._ac_ids(t):
                if ac_id in done_acs:
                    continue
                hit = [e for e in audit
                       if isinstance(e, dict) and e.get("ac") == ac_id
                       and e.get("axis") == dim and tid in (e.get("tcs") or [])]
                if not hit:
                    report.add("SET_MISMATCH", "%s test_cases[%s]" % (rel, tid),
                               "%s.dimension=%r 未出现在 %s 对应轴的 audit tcs 里"
                               % (tid, dim, ac_id))

    if final:
        # 接口门：带 api_refs 的非已完成 AC → 每锚 ≥1 条 type: 集成 TC 点名
        # rule: diy-test-design/SKILL.md:锚定（门联动·强门；被引 operation ≥1 TC）
        if stories_available and ac_anchors:
            tc_anchor_hits = set()
            for t in cases:
                if t.get("type") != "集成" or "retired" in t:
                    continue  # Q-111：接口锚门剔除 retired（废弃不算覆盖）
                for anchor in (t.get("api_refs") or []):
                    if isinstance(anchor, dict):
                        tc_anchor_hits.add((anchor.get("operationId"),
                                            anchor.get("path"), anchor.get("method")))
            for ac_id in sorted(ac_anchors):
                if ac_id in done_acs:
                    continue
                for anchor in ac_anchors[ac_id]:
                    key = (anchor.get("operationId"), anchor.get("path"),
                           anchor.get("method"))
                    if key not in tc_anchor_hits:
                        report.add("SET_MISMATCH", rel + " test_cases",
                                   "%s 的接口锚（%s %s）无 type: 集成 用例点名"
                                   "（带 api_refs 的 AC 接口用例必做）"
                                   % (ac_id, anchor.get("method"), anchor.get("path")))
        # FH 被杀双口径（底单 :683 2026-10-16 裁·R2=A TC.status 机械判据）：
        # 全部 TC 待办＝设计期引用口径（只查引用）；出现 通过/失败＝编码期收紧
        # （仅 status: 通过 的 TC 引用计数）。
        # rule: diy-test-design/SKILL.md:Final requires（双口径分时点·杀不掉的 FH 记
        #       [FH-GAP] 缺口交用户当轮裁决；两出口收口后终态仍是被杀或已删）
        if fh_ids:
            # Q-111：相位探测同剔 retired——废弃条目的历史 通过/失败 不得把活跃面拖进编码期口径
            coding_phase = any(t.get("status") in ("通过", "失败") and "retired" not in t
                               for t in cases)
            killed = set()
            for t in cases:
                if "retired" in t:
                    continue  # Q-111：FH 被杀门剔除 retired（废弃不算覆盖·FH 侧红走既有 SET_MISMATCH）
                if coding_phase and t.get("status") != "通过":
                    continue  # 编码期仅 status: 通过 的引用计数
                kt = t.get("kill_target")
                if isinstance(kt, list):
                    killed.update(x for x in kt if is_str(x))
                elif is_str(kt):
                    killed.add(kt)
            unkilled = sorted(fh_ids - killed)
            if unkilled:
                if coding_phase:
                    hint = ("编码期口径：FH 须被 ≥1 条 status: 通过 的 TC 引用；"
                            "杀不掉记 [FH-GAP] 缺口交用户裁决，裁『不删』必须补/修至通过")
                else:
                    hint = ("设计期口径：每条 FH 须 ≥1 TC 引用；"
                            "杀不掉记 [FH-GAP] 缺口交用户裁决，裁『不删』必须补 TC")
                report.add("SET_MISMATCH", rel + " fault_hypotheses",
                           "FH 未被任何用例杀掉：%s（%s）" % ("、".join(unkilled), hint))

    # mutation 段（在场时校验形状；缺席按 enabled: true 消费，不报）
    # rule: diy-test-design/SKILL.md:Schema mutation（enabled 布尔·tool 可选；唯一出处在本技能）
    mutation = doc.get("mutation")
    if mutation is not None:
        if not isinstance(mutation, dict):
            report.add("EMPTY_FIELD", rel + " mutation", "mutation 形状异常（应为映射）")
        else:
            if not isinstance(mutation.get("enabled"), bool):
                report.add("ENUM_INVALID", rel + " mutation.enabled",
                           "enabled 应为布尔（true|false，缺省 true）")
            if mutation.get("tool") is not None and not nonempty(mutation.get("tool")):
                report.add("EMPTY_FIELD", rel + " mutation.tool",
                           "tool 在场须非空（缺席走按栈选：Python→cosmic-ray、JS→stryker）")
    return counts
