# -*- coding: utf-8 -*-
"""diy-correct-course 引擎门禁与引用链：三件套定稿门禁 + 跨文档引用点扫描与二跳涟漪链。."""

import os

import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import display_path, items, nonempty, v  # noqa: E402

from change_proposal_lib import ARCH_FILE, DESIGN_FILE, EPICS_FILE, GATE_FILES, OPENAPI_FILE, PRD_FILE, ROUTE_BY_FILE, SPRINT_FILE, STORIES_FILE, TESTPLAN_FILE, operations  # noqa: E402

# ---------------------------------------------------------------- 门禁

def gate_check(docs, out_dir, project_root):
    """门禁：三件套在场且 project.status 均为 已定稿。返回 (passed, violations, route)。"""
    violations = []
    skills = []
    for filename in GATE_FILES:
        entry = docs[filename]
        show = display_path(os.path.join(out_dir, filename), project_root)
        if not entry["present"]:
            violations.append(v("MISSING_FILE", show,
                                "%s 不存在；先跑 %s 产出上游文档" % (filename,
                                                              ROUTE_BY_FILE[filename])))
            skills.append(ROUTE_BY_FILE[filename])
            continue
        if entry["err"] is not None:
            violations.append(v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % entry["err"]))
            continue
        data = entry["data"]
        project = data.get("project") if isinstance(data, dict) else None
        status = project.get("status") if isinstance(project, dict) else None
        if status != "已定稿":
            violations.append(v("STATUS_MISMATCH", show + " project.status",
                                "%s 的 project.status 须为 已定稿（实为 %s）；先跑 %s 定稿"
                                % (filename, status if nonempty(status) else "未声明",
                                   ROUTE_BY_FILE[filename])))
            skills.append(ROUTE_BY_FILE[filename])
    route = None
    if violations:
        unique = list(dict.fromkeys(skills))
        route = ("先跑 %s 产出并定稿上游文档，再重跑本技能" % " / ".join(unique) if unique else
                 "先修复上游文档（解析失败或状态未定稿），再重跑本技能")
    return (not violations), violations, route

# ---------------------------------------------------------------- 引用链

def ref_sites(docs):
    """全部引用/归属点四元组 (doc, owner_id, field, ref_id)——引用链唯一数据源。

    覆盖六产物 + 只读邻接产物（test-plan 的 TC.ac、sprint 的 test_refs）：
    变更影响面必然穿过用例与任务，缺这两条边则涟漪链断在 AC。
    """
    sites = []

    def add(doc, owner, field, ref):
        if nonempty(owner) and nonempty(ref):
            sites.append((doc, str(owner), field, str(ref)))

    for feature in items(docs[PRD_FILE]["data"], "features"):
        if isinstance(feature, dict):
            for req in items(feature, "requirements"):
                if isinstance(req, dict):
                    add("prd", feature.get("id"), "requirements", req.get("id"))
    for epic in items(docs[EPICS_FILE]["data"], "epics"):
        if isinstance(epic, dict):
            for ref in items(epic, "feature_refs"):
                add("epics", epic.get("id"), "feature_refs", ref)
    for story in items(docs[STORIES_FILE]["data"], "stories"):
        if not isinstance(story, dict):
            continue
        for ac in items(story, "acceptance_criteria"):
            if not isinstance(ac, dict):
                continue
            add("stories", story.get("id"), "acceptance_criteria", ac.get("id"))
            for ref in items(ac, "refs"):
                add("stories", ac.get("id"), "refs", ref)
            add("stories", ac.get("id"), "design_ref", ac.get("design_ref"))
    for dec in items(docs[ARCH_FILE]["data"], "decisions"):
        if isinstance(dec, dict):
            for ref in items(dec, "affects"):
                add("architecture", dec.get("id"), "affects", ref)
    for op in operations(docs[OPENAPI_FILE]["data"]):
        for ref in op["x_fr"]:
            add("openapi", op.get("operationId"), "x-fr", ref)
    for tc in items(docs[TESTPLAN_FILE]["data"], "test_cases"):
        if isinstance(tc, dict):
            add("test-plan", tc.get("id"), "ac", tc.get("ac"))
    for task in items(docs[SPRINT_FILE]["data"], "tasks"):
        if isinstance(task, dict):
            for ref in items(task, "test_refs"):
                add("sprint", task.get("story"), "test_refs", ref)
    return sites

def scan_chain(target, sites):
    """从 target 出发最多两跳收集引用点。

    direction: depended-by = 该处引用 target（改 target 会波及它）；
               depends-on  = target 引用/包含它（改它会影响 target）。
    """
    hits = []
    frontier = {target}
    visited = set()
    for _ in range(2):
        if not frontier:
            break
        new_frontier = set()
        for doc, owner, field, ref in sites:
            if ref in frontier and owner != ref:
                hits.append({"doc": doc, "id": owner, "field": field, "ref": ref,
                             "direction": "depended-by"})
                new_frontier.add(owner)
            elif owner in frontier and ref != owner:
                hits.append({"doc": doc, "id": owner, "field": field, "ref": ref,
                             "direction": "depends-on"})
                new_frontier.add(ref)
        visited |= frontier
        frontier = new_frontier - visited
    uniq = []
    seen = set()
    for hit in hits:
        # 同一引用点可能在两跳中各命中一次（方向相反）——按首次命中保留，近跳优先
        key = (hit["doc"], hit["id"], hit["field"], hit["ref"])
        if key in seen:
            continue
        seen.add(key)
        uniq.append(hit)
    return uniq

def known_ids(docs):
    """产物中出现过的全部 ID（含无引用者）——target 存在性判定用。"""
    ids = set()

    def add(value):
        if nonempty(value):
            ids.add(str(value))

    for feature in items(docs[PRD_FILE]["data"], "features"):
        if isinstance(feature, dict):
            add(feature.get("id"))
            for req in items(feature, "requirements"):
                if isinstance(req, dict):
                    add(req.get("id"))
    for key, coll in ((PRD_FILE, "nfrs"), (PRD_FILE, "goals"), (PRD_FILE, "users"),
                      (EPICS_FILE, "epics"), (STORIES_FILE, "stories"),
                      (ARCH_FILE, "decisions"), (ARCH_FILE, "components"),
                      (ARCH_FILE, "risks"), (DESIGN_FILE, "pages")):
        for item in items(docs[key]["data"], coll):
            if isinstance(item, dict):
                add(item.get("id"))
    for story in items(docs[STORIES_FILE]["data"], "stories"):
        if isinstance(story, dict):
            for ac in items(story, "acceptance_criteria"):
                if isinstance(ac, dict):
                    add(ac.get("id"))
    for op in operations(docs[OPENAPI_FILE]["data"]):
        add(op.get("operationId"))
    for tc in items(docs[TESTPLAN_FILE]["data"], "test_cases"):
        if isinstance(tc, dict):
            add(tc.get("id"))
    for task in items(docs[SPRINT_FILE]["data"], "tasks"):
        if isinstance(task, dict):
            add(task.get("story"))
    return ids
