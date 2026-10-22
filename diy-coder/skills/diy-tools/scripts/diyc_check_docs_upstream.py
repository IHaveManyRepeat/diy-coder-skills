# -*- coding: utf-8 -*-
"""diyc check 文档级规则：prd / architecture / openapi / epics（契约 §4.2）。"""

from diyc_check_docs_lib import (DEC_STATUSES, EPIC_STATUSES, FR_PRIORITIES,
                                 HTTP_METHODS, PATH_ITEM_KEYS, STACK_KINDS, dup,
                                 enum, is_str, nonempty, req)
from diyc_lib import items  # noqa: E402

# ---------------------------------------------------------------- prd

def check_prd(doc, rel, docs, final, report) -> dict:
    """prd.yaml：结构形状 + 枚举 + 重复 ID；--final 由 run() 统一加 [假设] 扫描。"""
    # rule: diy-prd/SKILL.md:Schema（author exactly this shape）
    # rule: diy-prd/SKILL.md:PRD Discipline（ID chain is sacred / 编号分配后永不重编号）
    counts = {"goals": 0, "users": 0, "features": 0, "frs": 0, "nfrs": 0}
    project = doc.get("project")
    if not isinstance(project, dict):
        report.add("EMPTY_FIELD", rel + " project", "project 块缺失或形状异常")
    else:
        req(report, rel + " project.name", project.get("name"), "project.name")
        enum(report, rel + " project.status", project.get("status"),
             ("草稿", "已定稿"), "project.status")
    req(report, rel + " purpose", doc.get("purpose"), "purpose（一句话产品目的）")

    goals = items(doc, "goals", of_type=dict)
    counts["goals"] = len(goals)
    if not goals:
        report.add("EMPTY_FIELD", rel + " goals", "goals 缺失或为空（2-5 条可度量目标）")
    for g in goals:
        w = "%s goals[%s]" % (rel, g.get("id") or "?")
        req(report, w + ".id", g.get("id"), "goal id")
        req(report, w + ".goal", g.get("goal"), "goal")
        req(report, w + ".metric", g.get("metric"), "metric（成功如何度量）")

    users = items(doc, "users", of_type=dict)
    counts["users"] = len(users)
    for u in users:
        w = "%s users[%s]" % (rel, u.get("id") or "?")
        req(report, w + ".id", u.get("id"), "user id")
        req(report, w + ".name", u.get("name"), "persona name")
        req(report, w + ".need", u.get("need"), "need")
    dup(report, [(u.get("id"), "%s users[%s].id" % (rel, u.get("id") or "?")) for u in users],
        "user id")

    features = items(doc, "features", of_type=dict)
    counts["features"] = len(features)
    if not features:
        report.add("EMPTY_FIELD", rel + " features", "features 缺失或为空")
    dup(report, [(f.get("id"), "%s features[%s].id" % (rel, f.get("id") or "?"))
                 for f in features], "feature id")
    fr_pairs = []
    for f in features:
        fw = "%s features[%s]" % (rel, f.get("id") or "?")
        req(report, fw + ".id", f.get("id"), "feature id")
        req(report, fw + ".name", f.get("name"), "feature name")
        req(report, fw + ".description", f.get("description"), "feature description")
        reqs = items(f, "requirements", of_type=dict)
        if not reqs:
            report.add("EMPTY_FIELD", fw + ".requirements", "feature 下 requirements 缺失或为空")
        for r in reqs:
            rw = "%s.requirements[%s]" % (fw, r.get("id") or "?")
            req(report, rw + ".id", r.get("id"), "requirement id")
            req(report, rw + ".statement", r.get("statement"), "statement")
            enum(report, rw + ".priority", r.get("priority"), FR_PRIORITIES, "priority")
            fr_pairs.append((r.get("id"), rw + ".id"))
            counts["frs"] += 1
    dup(report, fr_pairs, "requirement id")

    nfrs = items(doc, "nfrs", of_type=dict)
    counts["nfrs"] = len(nfrs)
    for n in nfrs:
        w = "%s nfrs[%s]" % (rel, n.get("id") or "?")
        req(report, w + ".id", n.get("id"), "NFR id")
        req(report, w + ".statement", n.get("statement"), "NFR statement")
    dup(report, [(n.get("id"), "%s nfrs[%s].id" % (rel, n.get("id") or "?")) for n in nfrs],
        "NFR id")

    # rule: diy-prd/SKILL.md:PRD Discipline（Every pending decision lives in the file；
    #       用户确认后 [假设] 才可去除）→ --final 时未答问题 = 未决
    for q in items(doc, "open_questions", of_type=dict):
        w = "%s open_questions[%s]" % (rel, q.get("id") or "?")
        req(report, w + ".id", q.get("id"), "question id")
        req(report, w + ".question", q.get("question"), "question")
        if final and not nonempty(q.get("answer")):
            report.add("PENDING_DECISION", w,
                       "定稿前该开放问题须回答（answer 为空；回答保留在文件中供审计）")
    return counts


# ---------------------------------------------------------------- architecture

def _wds_scenario_ids(docs) -> tuple:
    """wds-scenarios.yaml 的 SC-<nn> / SC-<nn>.P<n> ID 集 → (ids, err)。

    ID 形态由段1 的 W1 定义（`diy-wds-scenarios` 规则 6：场景 `SC-<nn>`、页面
    `SC-<nn>.P<n>`，废止独立 `P-*` 前缀）——本处只消费、不重定义（裁定 22）。
    err=None 且 ids 空 = 文件缺席（主线项目常态，调用方不告警）；文件在场但
    损坏/形状异常 → err 非空（错误经 `Docs.yaml_err` 透出，不静默吞）。
    """
    doc = docs.doc("wds-scenarios")
    if doc is None:
        return set(), docs.yaml_err("wds-scenarios")
    ids = set()
    for s in items(doc, "scenarios", of_type=dict):
        sid = s.get("id")
        if is_str(sid) and sid:
            ids.add(sid)
        for p in items(s, "pages", of_type=dict):
            pid = p.get("id")
            if is_str(pid) and pid:
                ids.add(pid)
    return ids, None


def _affects_known(docs, report) -> tuple:
    """affects 的解析域 → (known, resolvable)。

    主线 prd.yaml 的 FR/NFR ∪ WDS 线 wds-scenarios.yaml 的 SC/P（裁定 22：第四条真链路，
    与既有三条同型）。两源俱不可用 → resolvable=False，跳过该子检查并告警（不虚报通过）。
    """
    wds_ids, wds_err = _wds_scenario_ids(docs)
    if wds_err:
        report.warn("wds-scenarios.yaml 损坏：architecture affects 的 SC/P 引用无法解析"
                    "（跳过该子检查）：%s" % wds_err)
    prd_ok = docs.doc("prd") is not None
    if not prd_ok and not wds_ids:
        report.warn("prd.yaml / wds-scenarios.yaml 均缺失或不可用："
                    "architecture affects 引用无法解析（跳过该子检查）")
        return set(), False
    return set(docs.frs()) | set(docs.nfrs()) | wds_ids, True


def check_architecture(doc, rel, docs, final, report) -> dict:
    """architecture.yaml：决策形状 + affects 引用解析；--final 禁 待定 决策。"""
    # rule: diy-architecture/SKILL.md:Decision Discipline（every affects entry must be an
    #       existing FR/NFR ID from prd.yaml；every decision records at least one rejected alternative）
    # rule: diy-architecture/SKILL.md:Final requires（zero [假设]，zero proposed decisions，
    #       every affects ID resolving in prd.yaml）
    counts = {"decisions": 0, "已采纳": 0, "待定": 0}
    project = doc.get("project")
    if not isinstance(project, dict):
        report.add("EMPTY_FIELD", rel + " project", "project 块缺失或形状异常")
    else:
        enum(report, rel + " project.status", project.get("status"),
             ("草稿", "已定稿"), "project.status")
    stack = items(doc, "stack", of_type=dict)
    for i, s in enumerate(stack):
        w = "%s stack[%d]" % (rel, i)
        req(report, w + ".choice", s.get("choice"), "stack.choice")
        req(report, w + ".why", s.get("why"), "stack.why")
        # rule: diy-architecture/SKILL.md:Schema stack（新写条目必须带 id/kind；
        #       存量缺 id/kind → warning 不阻塞，下游按 kind 取值）
        sid = s.get("id")
        if not (is_str(sid) and sid.strip()):
            report.warn("%s stack[%d] 缺 id（存量条目过渡态；新写条目须带 ST-###）" % (rel, i))
        elif not (sid.startswith("ST-") and len(sid) == 6 and sid[3:].isdigit()):
            report.add("ENUM_INVALID", w + ".id",
                       "stack id %r 非 ST-### 形态（三位数字，如 ST-001）" % (sid,))
        kind = s.get("kind")
        if not (is_str(kind) and kind.strip()):
            report.warn("%s stack[%d] 缺 kind（存量条目过渡态；新写条目须带 kind，"
                        "封闭七类：%s）" % (rel, i, "/".join(STACK_KINDS)))
        else:
            enum(report, w + ".kind", kind, STACK_KINDS, "stack.kind")
    dup(report, [(s.get("id"), "%s stack[%s].id" % (rel, s.get("id") or "?"))
                 for s in stack if is_str(s.get("id")) and s.get("id").strip()],
        "stack id")
    for kind in ("frontend", "scaffold"):
        idxs = [i for i, s in enumerate(stack) if s.get("kind") == kind]
        if len(idxs) > 1:
            report.add("DUPLICATE_ID", "%s stack kind=%s" % (rel, kind),
                       "kind %s 至多一条（出现于 stack[%s]）"
                       % (kind, ", ".join(str(i) for i in idxs)))

    decisions = items(doc, "decisions", of_type=dict)
    counts["decisions"] = len(decisions)
    if not decisions:
        report.add("EMPTY_FIELD", rel + " decisions", "decisions 缺失或为空")
    known, affects_resolvable = _affects_known(docs, report)
    dup(report, [(d.get("id"), "%s decisions[%s].id" % (rel, d.get("id") or "?"))
                 for d in decisions], "decision id")
    for d in decisions:
        w = "%s decisions[%s]" % (rel, d.get("id") or "?")
        req(report, w + ".id", d.get("id"), "decision id")
        req(report, w + ".title", d.get("title"), "title")
        req(report, w + ".decision", d.get("decision"), "decision（选了什么）")
        req(report, w + ".rationale", d.get("rationale"), "rationale（为什么）")
        status = d.get("status")
        if enum(report, w + ".status", status, DEC_STATUSES, "status"):
            counts[status] += 1
            if final and status == "待定":
                report.add("PENDING_DECISION", w + ".status",
                           "定稿前决策须被用户接受（status: 待定 → 已采纳）")
        alternatives = items(d, "alternatives", of_type=dict)
        if not alternatives:
            report.add("EMPTY_FIELD", w + ".alternatives",
                       "缺少被否决备选（alternatives 至少一条；无备选的决策通常是未检验的默认）")
        for j, alt in enumerate(alternatives):
            req(report, "%s.alternatives[%d].option" % (w, j), alt.get("option"), "option")
            req(report, "%s.alternatives[%d].why_not" % (w, j), alt.get("why_not"), "why_not")
        affects = d.get("affects")
        if not nonempty(affects) or not isinstance(affects, list):
            report.add("EMPTY_FIELD", w + ".affects",
                       "affects 缺失或为空（须列出影响的 FR/NFR 或 SC/P ID）")
        elif affects_resolvable:
            # team-lead 裁定：decisions[].affects[] 必须在主线 prd.yaml（FR/NFR）或
            # WDS 线 wds-scenarios.yaml（SC-<nn> / SC-<nn>.P<n>，裁定 22）可解析 → UNKNOWN_ID
            for j, ref in enumerate(affects):
                if not is_str(ref) or not ref:
                    report.add("EMPTY_FIELD", "%s.affects[%d]" % (w, j), "affects 项缺失或非字符串")
                elif ref not in known:
                    report.add("UNKNOWN_ID", "%s.affects[%d]" % (w, j),
                               "%s 在主线 prd.yaml 与 WDS 线 wds-scenarios.yaml 中均不存在"
                               "（affects 只引用现有 FR/NFR 或 SC-<nn> / SC-<nn>.P<n>，不复制需求文本）"
                               % ref)

    for i, c in enumerate(items(doc, "components", of_type=dict)):
        w = "%s components[%d]" % (rel, i)
        req(report, w + ".id", c.get("id"), "component id")
        req(report, w + ".name", c.get("name"), "component name")
        req(report, w + ".responsibility", c.get("responsibility"), "responsibility")
    for i, r in enumerate(items(doc, "risks", of_type=dict)):
        w = "%s risks[%d]" % (rel, i)
        req(report, w + ".id", r.get("id"), "risk id")
        req(report, w + ".risk", r.get("risk"), "risk")
        req(report, w + ".mitigation", r.get("mitigation"), "mitigation")
    return counts


# ---------------------------------------------------------------- openapi

def check_openapi(doc, rel, docs, final, report) -> dict:
    """openapi.yaml：轻量 3.1 结构自检（契约 §4.2 硬点）+ x-fr / 功能 tags 引用解析。

    v4 批 4a：每 operation 通用错误 $ref（components/responses）＋功能 tags（F-x
    解析到 prd features）＋ securitySchemes/security 在场（终门硬门·批 4a §7-2）。
    prd 缺席/损坏：x-fr 与 F-x 解析一并改硬 violation（三档总则一档·§7-1 ⑪——
    同函数两处口径不得分裂，废 warning 跳过）。
    """
    # rule: diy-openapi/SKILL.md:Contract Discipline（Valid OpenAPI 3.1 above all；
    #       each operation carries x-fr referencing existing FR IDs from prd.yaml）
    # rule: diy-openapi/SKILL.md:鉴权必答（securitySchemes + security 在场·终门硬校验）
    # rule: diy-openapi/SKILL.md:结构（每 operation 至少一条 $ref 指向 components/responses/*；
    #       operation 必挂功能 tags，锚 F-x 须在 prd.yaml features 解析到）
    # rule: diy-openapi/SKILL.md:Final requires（openapi field is 3.1.x，zero [假设]，
    #       every x-fr ID / F-x anchor resolving in prd.yaml）
    counts = {"paths": 0, "operations": 0}
    version = doc.get("openapi")
    if not is_str(version) or not version.startswith("3.1"):
        report.add("ENUM_INVALID", rel + " openapi",
                   "openapi 字段应为 3.1.x（实际 %r）" % (version,))
    info = doc.get("info")
    if not isinstance(info, dict):
        report.add("EMPTY_FIELD", rel + " info", "info 块缺失或形状异常")
    else:
        req(report, rel + " info.title", info.get("title"), "info.title")
        req(report, rel + " info.version", info.get("version"), "info.version")
    xp = doc.get("x-project")
    if xp is not None:
        if not isinstance(xp, dict):
            report.add("EMPTY_FIELD", rel + " x-project", "x-project 形状异常（应为映射）")
        else:
            enum(report, rel + " x-project.status", xp.get("status"),
                 ("草稿", "已定稿"), "x-project.status")
    schemes = None
    components = doc.get("components")
    if isinstance(components, dict):
        schemes = components.get("securitySchemes")
    if not isinstance(schemes, dict) or not schemes:
        report.add("EMPTY_FIELD", rel + " components.securitySchemes",
                   "securitySchemes 缺失或为空（接口面必设计鉴权方案；"
                   "无鉴权 = security: [] 显式留痕）")
    if "security" not in doc:
        report.add("EMPTY_FIELD", rel + " security",
                   "security 缺失（顶层安全要求块必在场；显式无鉴权 = security: []）")

    paths = doc.get("paths")
    if not isinstance(paths, dict) or not paths:
        report.add("EMPTY_FIELD", rel + " paths", "paths 缺失或为空")
        return counts
    prd = docs.doc("prd")
    prd_available = prd is not None
    if not prd_available:
        # 三档总则一档（批 4a §7-1 ⑪）：prd 缺席/损坏 → 硬 violation（exit 1），
        # x-fr 与 F-x 两处解析口径同函数一并改硬，不再 warning 跳过
        report.add("UNKNOWN_ID", rel,
                   "prd.yaml 缺失或损坏：x-fr 与功能 tags 的 F-x 引用无法解析"
                   "（每个操作须引用 prd 既有 ID；硬门不再跳过）")
        known, known_features = set(), set()
    else:
        known = set(docs.frs()) | set(docs.nfrs())
        known_features = {f.get("id") for f in items(prd, "features", of_type=dict)
                          if is_str(f.get("id")) and f.get("id")}
    op_ids = []
    for pkey, item in paths.items():
        w = "%s paths[%s]" % (rel, pkey)
        if not is_str(pkey) or not pkey.startswith("/"):
            report.add("ENUM_INVALID", w, "paths 键必须以 / 开头（实际 %r）" % (pkey,))
        if not isinstance(item, dict):
            report.add("EMPTY_FIELD", w, "路径项形状异常（应为映射）")
            continue
        counts["paths"] += 1
        for mkey, op in item.items():
            if mkey in PATH_ITEM_KEYS:
                continue
            if mkey not in HTTP_METHODS:
                report.add("ENUM_INVALID", w,
                           "非法的 HTTP 方法或未知键：%r（合法方法 %s）"
                           % (mkey, "/".join(HTTP_METHODS)))
                continue
            ow = "%s.%s" % (w, mkey)
            if not isinstance(op, dict):
                report.add("EMPTY_FIELD", ow, "操作定义形状异常（应为映射）")
                continue
            counts["operations"] += 1
            op_id = op.get("operationId")
            if req(report, ow + ".operationId", op_id, "operationId（稳定，永不改名）"):
                op_ids.append((op_id, ow + ".operationId"))
            responses = op.get("responses")
            if not nonempty(responses) or not isinstance(responses, dict):
                report.add("EMPTY_FIELD", ow + ".responses", "responses 缺失或为空")
            elif not any(is_str(r.get("$ref"))
                         and r["$ref"].startswith("#/components/responses/")
                         and len(r["$ref"]) > len("#/components/responses/")
                         for r in responses.values() if isinstance(r, dict)):
                report.add("EMPTY_FIELD", ow + ".responses",
                           "缺少通用错误 $ref（responses 至少一条 $ref 指向 "
                           "components/responses/*，RFC 9457 problem details）")
            tags = op.get("tags")
            if not nonempty(tags) or not isinstance(tags, list):
                report.add("EMPTY_FIELD", ow + ".tags",
                           "tags 缺失或为空（每个操作须挂功能 tags：F-x 功能名）")
            elif prd_available:
                for j, tag in enumerate(tags):
                    if not is_str(tag) or not tag:
                        report.add("EMPTY_FIELD", "%s.tags[%d]" % (ow, j),
                                   "tags 项缺失或非字符串")
                        continue
                    anchor = tag.split(None, 1)[0]
                    if anchor not in known_features:
                        report.add("UNKNOWN_ID", "%s.tags[%d]" % (ow, j),
                                   "%s 的功能锚在 prd.yaml features 中不存在"
                                   "（tag 形态 = F-x 功能名，只引用既有功能 ID）" % anchor)
            xfr = op.get("x-fr")
            if not nonempty(xfr) or not isinstance(xfr, list):
                report.add("EMPTY_FIELD", ow + ".x-fr",
                           "x-fr 缺失或为空（每个操作须引用现有 FR ID，不复制需求文本）")
            elif prd_available:
                for j, ref in enumerate(xfr):
                    if not is_str(ref) or not ref:
                        report.add("EMPTY_FIELD", "%s.x-fr[%d]" % (ow, j),
                                   "x-fr 项缺失或非字符串")
                    elif ref not in known:
                        report.add("UNKNOWN_ID", "%s.x-fr[%d]" % (ow, j),
                                   "%s 在 prd.yaml 中不存在" % ref)
    dup(report, op_ids, "operationId")
    return counts


# ---------------------------------------------------------------- epics

def check_epics(doc, rel, docs, final, report) -> dict:
    """epics.yaml：形状 + 枚举 + 重复 ID（跨文档链路按裁定范围不扩散）。"""
    # rule: diy-epics-stories/SKILL.md:Schema（epics.yaml）
    counts = {"epics": 0}
    project = doc.get("project")
    if not isinstance(project, dict):
        report.add("EMPTY_FIELD", rel + " project", "project 块缺失或形状异常")
    else:
        enum(report, rel + " project.status", project.get("status"),
             ("草稿", "已定稿"), "project.status")
    epics = items(doc, "epics", of_type=dict)
    counts["epics"] = len(epics)
    if not epics:
        report.add("EMPTY_FIELD", rel + " epics", "epics 缺失或为空")
    dup(report, [(e.get("id"), "%s epics[%s].id" % (rel, e.get("id") or "?"))
                 for e in epics], "epic id")
    for e in epics:
        w = "%s epics[%s]" % (rel, e.get("id") or "?")
        req(report, w + ".id", e.get("id"), "epic id")
        req(report, w + ".title", e.get("title"), "title")
        req(report, w + ".goal", e.get("goal"), "goal")
        if not nonempty(e.get("feature_refs")) or not isinstance(e.get("feature_refs"), list):
            report.add("EMPTY_FIELD", w + ".feature_refs", "feature_refs 缺失或为空")
        enum(report, w + ".status", e.get("status"), EPIC_STATUSES, "status")
    return counts
