# -*- coding: utf-8 -*-
"""diyc check 文档级规则：stories（契约 §4.2）。"""

import diyc_lib

from diyc_check_docs_lib import (STORY_STATUSES, _api_anchor_ok, _anchor_resolves,
                                 _openapi_anchors, dup, enum, is_str, nonempty, req)
from diyc_lib import items  # noqa: E402

# ---------------------------------------------------------------- stories

def _design_pages(docs):
    """design.yaml pages 的 P-x 集合；文档缺失/损坏 → None（跳过解析）。"""
    design = docs.doc("design")
    if not isinstance(design, dict):
        return None
    return {p.get("id") for p in items(design, "pages", of_type=dict) if is_str(p.get("id"))}


def check_stories(doc, rel, docs, final, report) -> dict:
    """stories.yaml：AC 形状 + refs 引用解析 + design_ref 解析；--final 加必须级 FR 覆盖。"""
    # rule: diy-epics-stories/SKILL.md:Derivation Discipline（AC refs existing FR/NFR IDs，
    #       never copy requirement text；design_ref must resolve；Coverage is complete：
    #       every must-priority FR is referenced by at least one AC）
    # rule: diy-epics-stories/SKILL.md:Final requires（zero [假设]；every AC ref
    #       resolving in prd.yaml；every must-FR covered）
    counts = {"stories": 0, "acs": 0, "must_frs": 0}
    project = doc.get("project")
    if not isinstance(project, dict):
        report.add("EMPTY_FIELD", rel + " project", "project 块缺失或形状异常")
    else:
        enum(report, rel + " project.status", project.get("status"),
             ("草稿", "已定稿"), "project.status")
    stories = items(doc, "stories", of_type=dict)
    counts["stories"] = len(stories)
    if not stories:
        report.add("EMPTY_FIELD", rel + " stories", "stories 缺失或为空")
    dup(report, [(s.get("id"), "%s stories[%s].id" % (rel, s.get("id") or "?"))
                 for s in stories], "story id")
    prd_available = docs.doc("prd") is not None
    known = set(docs.frs()) | set(docs.nfrs()) if prd_available else set()
    if not prd_available:
        report.warn("prd.yaml 缺失/损坏：stories refs 引用无法解析（跳过该子检查）")
    pages = _design_pages(docs)
    openapi_anchors = _openapi_anchors(docs)
    openapi_available = docs.doc("openapi") is not None
    if not openapi_available:
        openapi_anchors = {}
    anchored_ops = set()
    ac_has_api = False
    referenced = set()
    ac_pairs = []
    for s in stories:
        w = "%s stories[%s]" % (rel, s.get("id") or "?")
        req(report, w + ".id", s.get("id"), "story id")
        req(report, w + ".epic", s.get("epic"), "epic（E-x 引用）")
        req(report, w + ".title", s.get("title"), "title")
        req(report, w + ".narrative", s.get("narrative"), "narrative")
        enum(report, w + ".status", s.get("status"), STORY_STATUSES, "status")
        acs = items(s, "acceptance_criteria", of_type=dict)
        if not acs:
            report.add("EMPTY_FIELD", w + ".acceptance_criteria",
                       "acceptance_criteria 缺失或为空")
        for a in acs:
            ac_id = a.get("id")
            aw = "%s.acceptance_criteria[%s]" % (w, ac_id or "?")
            req(report, aw + ".id", ac_id, "AC id")
            req(report, aw + ".given", a.get("given"), "given")
            req(report, aw + ".when", a.get("when"), "when")
            req(report, aw + ".then", a.get("then"), "then")
            counts["acs"] += 1
            ac_pairs.append((ac_id, aw + ".id"))
            refs = a.get("refs")
            if not nonempty(refs) or not isinstance(refs, list):
                report.add("EMPTY_FIELD", aw + ".refs",
                           "refs 缺失或为空（每个 AC 须引用现有 FR/NFR ID）")
            elif prd_available:
                # team-lead 裁定：acceptance_criteria[].refs[] 必须在 prd.yaml 可解析
                for j, ref in enumerate(refs):
                    if not is_str(ref) or not ref:
                        report.add("EMPTY_FIELD", "%s.refs[%d]" % (aw, j),
                                   "refs 项缺失或非字符串")
                    elif ref not in known:
                        report.add("UNKNOWN_ID", "%s.refs[%d]" % (aw, j),
                                   "%s 在 prd.yaml 中不存在（引用而非复制）" % ref)
                    else:
                        referenced.add(ref)
            design_ref = a.get("design_ref")
            if design_ref is not None:
                # rule: diy-epics-stories/SKILL.md:Design binding FR-2.4（every design_ref must resolve）
                if pages is None:
                    report.add("UNKNOWN_ID", aw + ".design_ref",
                               "%s 无法解析：design.yaml 不存在或不可读（绑定须以 design.yaml 为基线）"
                               % design_ref)
                elif design_ref not in pages:
                    report.add("UNKNOWN_ID", aw + ".design_ref",
                               "%s 在 design.yaml pages 中不存在" % design_ref)
            api_refs = a.get("api_refs")
            if api_refs is not None:
                # rule: diy-epics-stories/SKILL.md:Schema AC.api_refs（可选复合锚·须可解析·与 design_ref 同构）
                if not (isinstance(api_refs, list) and api_refs):
                    report.add("EMPTY_FIELD", aw + ".api_refs",
                               "api_refs 形状异常（应为非空列表，缺席即整键省略）")
                else:
                    for j, anchor in enumerate(api_refs):
                        pw = "%s.api_refs[%d]" % (aw, j)
                        if not _api_anchor_ok(anchor):
                            report.add("EMPTY_FIELD", pw,
                                       "复合锚形状异常（须含 operationId/path/method 三键）")
                        elif openapi_anchors == {}:
                            pass  # openapi 缺席：跳过解析（warning 一次，见下）
                        elif not _anchor_resolves(anchor, openapi_anchors):
                            report.add("UNKNOWN_ID", pw,
                                       "operationId=%s path=%s method=%s 与 openapi.yaml 不一致"
                                       % (anchor.get("operationId"), anchor.get("path"),
                                          anchor.get("method")))
                        else:
                            anchored_ops.add(anchor.get("operationId"))
    dup(report, ac_pairs, "AC id")
    must_frs = {fid for fid, r in docs.frs().items() if r.get("priority") == "必须"}
    counts["must_frs"] = len(must_frs)
    if final:
        # rule: diy-epics-stories/SKILL.md:Derivation Discipline（Coverage is complete）
        missing = diyc_lib.id_sort(must_frs - referenced)
        if missing:
            report.add("SET_MISMATCH", rel + " acceptance_criteria",
                       "必须级 FR 未被任何 AC 引用：%s（每个必须 FR 至少被一条 AC 的 refs 覆盖）"
                       % "、".join(missing))
    if openapi_available and openapi_anchors:
        # rule: diy-test-design/SKILL.md:锚定（反向悬空 operation → notes skip line 显式登记，不静默）
        dangling = sorted(set(openapi_anchors) - anchored_ops)
        if dangling:
            notes = doc.get("notes")
            notes_text = notes if is_str(notes) else "\n".join(
                x for x in (notes or []) if is_str(x))
            unregistered = [op for op in dangling
                            if op not in (notes_text or "")]
            if unregistered:
                report.add("SET_MISMATCH", rel + " notes",
                           "悬空 operation 未登记 skip line：%s（openapi 有端点、无 AC 引——"
                           "顶层 notes 逐行写 '<operationId>: <为什么>' 或补 AC 绑定）"
                           % "、".join(unregistered))
    return counts
