# -*- coding: utf-8 -*-
"""diyc check 入口与流程级规则（契约 §2/§4.2）。

- run(args) -> dict：文件定位 + 缺席语义 + 类型分派 + --final 的 [假设] 扫描
  + --previous 稳定 ID 集合比对；文档级规则在 diyc_check_docs，sprint/review
  （任务级）与跨文件真值在本文件。
- PENDING_UNCOVERED 只经 Docs.story_covered()（与 W3 reconcile 共用唯一定义源；
  契约 §4.2，禁止二份实现）；缺覆盖语义 = 无 TC 绑定 且（无 gap 条目 或
  decision == '待办'），已豁免 与 接受缺口 均豁免（team-lead 2026-09-13 裁定）。
- 跨文件真值（always-on，BUG-012 机制化）：已完成任务 → stories.yaml 的 story 必须
  已完成、test-plan.yaml 的 TC 必须通过；待审查/已完成 任务台账 → evidence 齐备且
  red/green 非空、green 与 TC status 一致（diy-review L3）。
"""
# trace: 2026-09-13 批次 3（统一脚本化）——check 入口/流程级规则，契约 §4.2

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import diyc_check_docs as d  # noqa: E402
import diyc_lib  # noqa: E402
from diyc_lib import Docs, receipt  # noqa: E402

TYPE_FILES = {
    "prd": "prd.yaml",
    "architecture": "architecture.yaml",
    "openapi": "openapi.yaml",
    "epics": "epics.yaml",
    "stories": "stories.yaml",
    "test-plan": "test-plan.yaml",
    "sprint": "sprint.yaml",
    "review": "sprint.yaml",   # 契约 §4.2：review 为任务级，落在 sprint.yaml
}

VERDICT_ROUTES = ("意图缺口", "规格缺陷", "小修", "后置")   # rule: diy-review/SKILL.md:Routing
FINDING_LAYERS = ("正确性", "边界", "覆盖审计", "设计采用")  # rule: diy-review/SKILL.md:Schema review.findings.layer
TASK_STATUSES = d.STORY_STATUSES  # rule: diy-sprint/SKILL.md:Schema tasks.status（五态与 story 同集）
AUGMENT_VERDICTS = ("通过", "失败", "已跳过")  # rule: diy-sprint/SKILL.md:Schema tasks.augment


def rel_path(root, path) -> str:
    return os.path.relpath(path, root).replace("\\", "/")


def _doc_rel(docs, filename) -> str:
    return rel_path(docs.project_root, os.path.join(docs.output_dir, filename))


def _done(report, counts) -> dict:
    return receipt("check", not report.violations, violations=report.violations,
                   warnings=report.warnings, counts=counts)


# ---------------------------------------------------------------- --previous

def _stable_ids(typ, doc) -> set:
    """按类型取稳定 ID 集合（契约 §4.2：prd=FR/NFR；openapi=operationId；
    epics=E；stories=S+AC；test-plan=TC）。"""
    ids = set()

    def add(value):
        if d.is_str(value) and value:
            ids.add(value)

    if typ == "prd":
        for f in d.items(doc, "features"):
            for r in d.items(f, "requirements"):
                add(r.get("id"))
        for n in d.items(doc, "nfrs"):
            add(n.get("id"))
    elif typ == "openapi":
        paths = doc.get("paths")
        if isinstance(paths, dict):
            for item in paths.values():
                if isinstance(item, dict):
                    for mkey, op in item.items():
                        if mkey in d.HTTP_METHODS and isinstance(op, dict):
                            add(op.get("operationId"))
    elif typ == "epics":
        for e in d.items(doc, "epics"):
            add(e.get("id"))
    elif typ == "stories":
        for s in d.items(doc, "stories"):
            add(s.get("id"))
            for a in d.items(s, "acceptance_criteria"):
                add(a.get("id"))
    elif typ == "test-plan":
        for t in d.items(doc, "test_cases"):
            add(t.get("id"))
    return ids


def _check_previous(typ, doc, previous, rel, root, report):
    # 相对 --previous 按 project-root 解析（与 trace --src 同语义，见 diyc.py:_trace_targets）；
    # 先绝对化再 rel_path/isfile——跨盘 cwd 下 os.path.relpath 对相对路径抛未捕获 ValueError（V 验证 B1）
    if not os.path.isabs(previous):
        previous = os.path.join(root, previous)
    prev_rel = rel_path(root, previous)
    if not os.path.isfile(previous):
        report.add("MISSING_FILE", prev_rel, "旧稿不存在（--previous 路径无效）")
        return
    prev, err = diyc_lib.safe_load_yaml(previous)
    if err:
        report.add("UNPARSABLE_YAML", prev_rel, "旧稿解析失败：%s" % err)
        return
    if not isinstance(prev, dict):
        report.add("UNPARSABLE_YAML", prev_rel, "旧稿顶层不是映射")
        return
    # rule: diy-prd/epics-stories 等 SKILL.md:ID 链神圣（Update 保持 ID 稳定，旧有新无 = 重编号事故）
    gone = diyc_lib.id_sort(_stable_ids(typ, prev) - _stable_ids(typ, doc))
    for stable_id in gone:
        report.add("ID_UNSTABLE", rel,
                   "稳定 ID %s 在旧稿存在、新稿中缺失（ID 一旦分配永不重编号；对照 --previous %s）"
                   % (stable_id, prev_rel))


# ---------------------------------------------------------------- sprint（任务级）

def check_sprint(doc, rel, docs, story_filter, final, report) -> dict:
    """sprint.yaml：状态机枚举 + 门 + ID 链 + 跨文件真值；--final 加集合相等/空 refs 门。"""
    # rule: diy-sprint/SKILL.md:Design Discipline（one story one task, exact set equality；
    #       TDD gate：缺覆盖 → 已阻塞 + blocked_reason；done stories land as done）
    # rule: diy-sprint/SKILL.md:Final requires（zero [假设]；task story 集 == story 集；
    #       已阻塞 必有 blocked_reason；待办 任务 test_refs 非空且可解析）
    counts = {"tasks_by_status": {}, "blocked": 0, "gated": 0}
    project = doc.get("project")
    if not isinstance(project, dict):
        report.add("EMPTY_FIELD", rel + " project", "project 块缺失或形状异常")
    else:
        d.enum(report, rel + " project.status", project.get("status"),
               ("草稿", "已定稿"), "project.status")
    all_tasks = d.items(doc, "tasks")
    if not all_tasks:
        report.add("EMPTY_FIELD", rel + " tasks", "tasks 缺失或为空")
    scan = all_tasks
    if story_filter:
        scan = [t for t in all_tasks if t.get("story") == story_filter]
        if not scan:
            report.add("UNKNOWN_ID", rel + " tasks",
                       "sprint.yaml 中不存在 story %s 的任务" % story_filter)

    stories_doc = docs.doc("stories")
    tp_doc = docs.doc("test-plan")
    stories_available = stories_doc is not None
    tp_available = tp_doc is not None
    if not stories_available:
        report.warn("stories.yaml 缺失/损坏：任务 story 解析与 done 真值核对跳过")
    if not tp_available:
        report.warn("test-plan.yaml 缺失/损坏：test_refs 解析与 TC 真值核对跳过")
    story_ids = set(docs.stories()) if stories_available else set()
    story_status = {sid: s.get("status") for sid, s in docs.stories().items()} \
        if stories_available else {}
    tc_status = {tid: t.get("status") for tid, t in docs.tcs().items()} \
        if tp_available else {}

    d.dup(report, [(t.get("story"), "%s tasks[%s].story" % (rel, t.get("story") or "?"))
                   for t in all_tasks], "task story")

    # 文档级形状与计数（--story 收窄只作用于任务级核对，形状始终全量）
    for t in all_tasks:
        w = "%s tasks[%s]" % (rel, t.get("story") or "?")
        d.req(report, w + ".story", t.get("story"), "story（任务标识）")
        status = t.get("status")
        if d.enum(report, w + ".status", status, TASK_STATUSES, "status"):
            counts["tasks_by_status"][status] = counts["tasks_by_status"].get(status, 0) + 1
            if status in ("待办", "进行中"):
                counts["gated"] += 1
        if status == "已阻塞":
            counts["blocked"] += 1
            # rule: diy-sprint/SKILL.md:Schema（blocked_reason required iff status: 已阻塞）
            if not d.nonempty(t.get("blocked_reason")):
                report.add("BLOCKED_NO_REASON", w + ".blocked_reason",
                           "已阻塞任务必须写 blocked_reason（缺覆盖示例：「AC-x.y 无用例（decision: 待办）」）")
        if t.get("augment") is not None:
            d.enum(report, w + ".augment", t.get("augment"), AUGMENT_VERDICTS, "augment")
        if t.get("test_refs") is not None and not isinstance(t.get("test_refs"), list):
            report.add("EMPTY_FIELD", w + ".test_refs", "test_refs 形状异常（应为列表）")
        evidence = t.get("evidence")
        if evidence is not None:
            if not isinstance(evidence, list):
                report.add("EMPTY_FIELD", w + ".evidence", "evidence 形状异常（应为列表）")
            else:
                for i, e in enumerate(evidence):
                    if not isinstance(e, dict):
                        report.add("EMPTY_FIELD", "%s.evidence[%d]" % (w, i),
                                   "evidence 条目形状异常（应为映射 {tc, red, green}）")

    # 任务级核对（--story 时只查该任务）
    for t in scan:
        story = t.get("story")
        w = "%s tasks[%s]" % (rel, story or "?")
        refs = t.get("test_refs") if isinstance(t.get("test_refs"), list) else []
        for j, ref in enumerate(refs):
            if not d.nonempty(ref):
                report.add("EMPTY_FIELD", "%s.test_refs[%d]" % (w, j), "test_refs 项为空或非字符串")
            elif tp_available and ref not in tc_status:
                # rule: diy-sprint/SKILL.md:Workflow 1（every test_refs entry resolves in test-plan.yaml）
                report.add("UNKNOWN_ID", "%s.test_refs[%d]" % (w, j),
                           "%s 在 test-plan.yaml 中不存在" % ref)
        if stories_available and d.is_str(story) and story not in story_ids:
            report.add("UNKNOWN_ID", w + ".story", "%s 在 stories.yaml 中不存在" % story)

        status = t.get("status")
        if status in ("待办", "进行中") and stories_available and story in story_ids:
            # rule: diy-sprint/SKILL.md:Design Discipline（TDD gate 默认姿态：缺覆盖 → 已阻塞）
            # 唯一定义源：Docs.story_covered()（契约 §4.2；已豁免/接受缺口 豁免由该函数承载）
            covered, missing = docs.story_covered(story)
            if not covered:
                report.add("PENDING_UNCOVERED", w,
                           "缺覆盖 AC：%s —— 该任务须置已阻塞并写 blocked_reason（如「%s 无用例"
                           "（decision: 待办）」），或补用例 / 裁已豁免 / 接受缺口"
                           % ("、".join(missing), missing[0]))
        if status == "已完成":
            # 跨文件真值（always-on，BUG-012 机制化）：已完成任务的两个真源必须同步
            # rule: diy-dev/SKILL.md:Design Discipline（Backfill the source of truth——绿线同刻
            #       回填 test-plan TC status: 通过 与 stories 状态；本检查即该机制的机器审计面）
            if stories_available and story in story_ids and story_status.get(story) != "已完成":
                report.add("STATUS_MISMATCH", w,
                           "任务已完成但 stories.yaml 中 %s status=%r（终态必须回填真源）"
                           % (story, story_status.get(story)))
            if tp_available:
                for j, ref in enumerate(refs):
                    if d.is_str(ref) and ref in tc_status and tc_status.get(ref) != "通过":
                        report.add("STATUS_MISMATCH", "%s.test_refs[%d]" % (w, j),
                                   "任务已完成但 %s 在 test-plan.yaml 中 status=%r（必须通过）"
                                   % (ref, tc_status.get(ref)))

    if final and stories_available:
        # rule: diy-sprint/SKILL.md:Final requires（task story set == story ID set，双向）
        task_set = {t.get("story") for t in all_tasks if d.is_str(t.get("story"))}
        missing_tasks = diyc_lib.id_sort(story_ids - task_set)
        for sid in missing_tasks:
            report.add("SET_MISMATCH", rel + " tasks",
                       "story %s 无对应任务（一故事一任务，集合精确相等）" % sid)
        for t in all_tasks:
            if t.get("status") != "待办":
                continue
            refs = t.get("test_refs") if isinstance(t.get("test_refs"), list) else []
            if refs:
                continue
            story = t.get("story")
            if d.is_str(story) and docs.tcs_for_story(story):
                report.add("SET_MISMATCH", "%s tasks[%s].test_refs" % (rel, story),
                           "待办任务 test_refs 为空，但该 story 在 test-plan.yaml 中已有用例"
                           "（引用集合未同步）")
    return counts


# ---------------------------------------------------------------- review（任务级）

def _task_chain(t, w, docs, tp_available, tc_ids, report):
    """任务 ID 链：test_refs / evidence.tc 在 test-plan.yaml 可解析。"""
    # rule: diy-review/SKILL.md:On Activation 3（material = evidence entries + TC steps）
    for j, ref in enumerate(t.get("test_refs") if isinstance(t.get("test_refs"), list) else []):
        if d.nonempty(ref) and tp_available and ref not in tc_ids:
            report.add("UNKNOWN_ID", "%s.test_refs[%d]" % (w, j),
                       "%s 在 test-plan.yaml 中不存在" % ref)
    for i, e in enumerate(d.items(t, "evidence")):
        tc = e.get("tc")
        if not d.nonempty(tc):
            report.add("EMPTY_FIELD", "%s.evidence[%d].tc" % (w, i), "evidence.tc 缺失或为空")
        elif tp_available and tc not in tc_ids:
            report.add("UNKNOWN_ID", "%s.evidence[%d].tc" % (w, i),
                       "%s 在 test-plan.yaml 中不存在" % tc)


def _review_block(review, w, report) -> tuple:
    """review 块校验；返回 (layers, routes)（仅枚举合法项，供 counts 聚合）。"""
    # rule: diy-review/SKILL.md:Schema（review.verdict + findings[].layer/route）
    # rule: diy-review/SKILL.md:Verdict Rules（fail if any finding routes 意图缺口/小修/规格缺陷；
    #       pass if findings empty or all 后置）
    rw = w + ".review"
    if not isinstance(review, dict):
        report.add("EMPTY_FIELD", rw, "review 块形状异常（应为映射）")
        return [], []
    verdict_ok = d.enum(report, rw + ".verdict", review.get("verdict"),
                        ("通过", "失败"), "verdict")
    findings = review.get("findings")
    if findings is None:
        findings = []
    if not isinstance(findings, list):
        report.add("EMPTY_FIELD", rw + ".findings", "findings 形状异常（应为列表）")
        return [], []
    layers, routes = [], []
    for i, f in enumerate(findings):
        fw = "%s.findings[%d]" % (rw, i)
        if not isinstance(f, dict):
            report.add("EMPTY_FIELD", fw, "finding 形状异常（应为映射）")
            continue
        if d.enum(report, fw + ".layer", f.get("layer"), FINDING_LAYERS, "layer"):
            layers.append(f["layer"])
        if d.enum(report, fw + ".route", f.get("route"), VERDICT_ROUTES, "route",
                  code="ROUTE_INVALID"):
            routes.append(f["route"])
    if verdict_ok and review.get("verdict") == "通过":
        bad = [r for r in routes if r != "后置"]
        if bad:
            report.add("ROUTE_INVALID", rw,
                       "verdict: 通过 但 findings 含非后置路由（%s）——通过 仅当 findings 为空或全部后置"
                       % "、".join(bad))
    if verdict_ok and review.get("verdict") == "失败":
        if not any(r != "后置" for r in routes):
            report.add("ROUTE_INVALID", rw,
                       "verdict: 失败 但无任何非后置发现（意图缺口 / 规格缺陷 / 小修）")
    return layers, routes


def _ledger(t, w, docs, tp_available, tc_status, report):
    """L3 验收覆盖台账：evidence 齐备 + red/green 非空 + green 与 TC status 一致 + 声明纪律。"""
    # rule: diy-review/SKILL.md:L3（every test_refs TC has an evidence entry；red precedes green；
    #       evidence agrees with test-plan TC status；kill_target/technique 纪律）
    refs = [r for r in (t.get("test_refs") if isinstance(t.get("test_refs"), list) else [])
            if d.nonempty(r)]
    ev_by_tc = {}
    for e in d.items(t, "evidence"):
        tc = e.get("tc")
        if d.nonempty(tc):
            ev_by_tc[tc] = e   # 同 tc 多条 → 取最后一条（HALT 续跑的最新记录）
    tcs = docs.tcs() if tp_available else {}
    tp_rel = _doc_rel(docs, "test-plan.yaml")
    for ref in refs:
        entry = ev_by_tc.get(ref)
        if entry is None:
            report.add("EVIDENCE_MISSING", w + ".evidence",
                       "%s 无 evidence 条目（每个 test_refs 用例须有执行证据）" % ref)
            continue
        red, green = entry.get("red"), entry.get("green")
        if not (d.nonempty(red) and d.nonempty(green)):
            report.add("EVIDENCE_MISSING", "%s.evidence[tc=%s]" % (w, ref),
                       "red/green 记录不完整（red 先于 green，两条均须非空；同条目两键存在即序证据）")
        tc_entry = tcs.get(ref)
        if tp_available and tc_entry is not None:
            if d.nonempty(green) and tc_entry.get("status") != "通过":
                report.add("STATUS_MISMATCH", "%s.evidence[tc=%s]" % (w, ref),
                           "evidence 有 green 记录但 test-plan.yaml 中 %s status=%r（真源未回填，BUG-012）"
                           % (ref, tc_entry.get("status")))
            d.tc_declarations(tc_entry, "%s test_cases[%s]" % (tp_rel, ref), report)


def check_review(doc, rel, docs, story_filter, report) -> dict:
    """review：review 块裁决校验 + 待审查/已完成 任务台账（契约 §4.2）。"""
    counts = {"findings_by_layer": {}, "findings_by_route": {}}
    all_tasks = d.items(doc, "tasks")
    if story_filter:
        scan = [t for t in all_tasks if t.get("story") == story_filter]
        if not scan:
            report.add("UNKNOWN_ID", rel + " tasks",
                       "sprint.yaml 中不存在 story %s 的任务" % story_filter)
    else:
        scan = [t for t in all_tasks if t.get("status") in ("待审查", "已完成")]
    tp_available = docs.doc("test-plan") is not None
    if not tp_available:
        report.warn("test-plan.yaml 缺失/损坏：review 台账的用例解析与真值核对跳过")
    tc_ids = set(docs.tcs()) if tp_available else set()
    tc_status = {tid: t.get("status") for tid, t in docs.tcs().items()} if tp_available else {}
    for t in scan:
        story = t.get("story")
        w = "%s tasks[%s]" % (rel, story or "?")
        _task_chain(t, w, docs, tp_available, tc_ids, report)
        layers, routes = [], []
        if t.get("review") is not None:
            layers, routes = _review_block(t.get("review"), w, report)
        for layer in layers:
            counts["findings_by_layer"][layer] = counts["findings_by_layer"].get(layer, 0) + 1
        for route in routes:
            counts["findings_by_route"][route] = counts["findings_by_route"].get(route, 0) + 1
        _ledger(t, w, docs, tp_available, tc_status, report)
    return counts


# ---------------------------------------------------------------- 入口

def run(args) -> dict:
    """check 入口（契约 §2：args 由 diyc.py 收口，output_dir 已解析）。"""
    typ = args.type
    root = args.project_root
    out_dir = getattr(args, "output_dir", None)
    report = d.Report()
    if not out_dir:
        out_dir = os.path.join(root, diyc_lib.DEFAULT_OUTPUT_DIR)
        report.warn("args.output_dir 缺失（diyc.py 未收口），按默认 %s 处理"
                    % diyc_lib.DEFAULT_OUTPUT_DIR)
    final = bool(getattr(args, "final", False))
    story_filter = getattr(args, "story", None)
    filename = TYPE_FILES[typ]
    path = os.path.join(out_dir, filename)
    rel = rel_path(root, path)

    if not os.path.isfile(path):
        # rule: 契约 §4.2 缺席语义（openapi 缺席 = 可选文档合法跳过；其余 MISSING_FILE）
        if typ == "openapi":
            report.warn("openapi.yaml 不存在——本项目无可选接口文档，合法跳过")
            return _done(report, {})
        report.add("MISSING_FILE", rel, "%s 不存在" % filename)
        return _done(report, {})

    doc, err = diyc_lib.safe_load_yaml(path)
    if err:
        report.add("UNPARSABLE_YAML", rel, err)
        return _done(report, {})
    if not isinstance(doc, dict):
        report.add("UNPARSABLE_YAML", rel, "顶层不是映射（实际 %s）" % type(doc).__name__)
        return _done(report, {})

    docs = Docs(root, out_dir)
    if typ in d.CHECKERS:
        counts = d.CHECKERS[typ](doc, rel, docs, final, report)
    elif typ == "sprint":
        counts = check_sprint(doc, rel, docs, story_filter, final, report)
    else:  # review
        counts = check_review(doc, rel, docs, story_filter, report)

    if final:
        # rule: diy-prd/architecture/openapi/epics-stories/test-plan/sprint SKILL.md:
        #       Final requires（zero [假设]）——全类型统一深度扫描
        for loc in d.scan_assumptions(doc, rel):
            report.add("ASSUMPTION_PRESENT", "%s %s" % (rel, loc),
                       "[假设] 未清除（定稿前须用户确认并去除前缀）")

    previous = getattr(args, "previous", None)
    if previous:
        _check_previous(typ, doc, previous, rel, root, report)

    return _done(report, counts)
