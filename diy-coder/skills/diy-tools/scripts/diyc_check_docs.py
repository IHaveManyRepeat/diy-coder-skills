# -*- coding: utf-8 -*-
"""diyc check 文档级规则：prd / architecture / openapi / epics / stories / test-plan。

规则逐条读取对应 SKILL.md 的 Schema、Discipline 与 Final requires 原文对齐，
每条附 `# rule: <skill>/SKILL.md:<条款>` 注释；跨文档引用解析只经 diyc_lib.Docs
（契约 §5，禁止旁路读文件）。入口 run() 在 diyc_check.py；本模块 check_* 纯函数
就地追加违规并返回 counts（契约 §4.2）。

裁量声明（已在回报中报 team-lead）：
- 跨文档 UNKNOWN_ID 限于 team-lead 裁定的三条真链路（architecture.affects /
  openapi x-fr / stories refs）+ 契约钉住的 stories design_ref；
  epics.feature_refs、stories.epic 属同类链路但不在本次裁定范围，暂不查。
- prd open_questions 未答（answer 为空）在 --final 计 PENDING_DECISION。
"""
# trace: 2026-09-13 批次 3（统一脚本化）——文档级规则，契约 §4.2

import diyc_lib

# 枚举（逐条对照各 SKILL.md Schema 节的机器锚）
# rule: diy-test-design/SKILL.md:Schema technique 13 值（前 9 设计期 + 后 4 补测）
TECHNIQUES = ("等价类", "边界", "决策表", "状态迁移",
              "成对组合", "错误猜测", "蜕变测试", "属性测试", "场景",
              "覆盖分支", "MC-DC 覆盖", "白盒路径", "变异杀伤")
CASE_TYPES = ("单元", "集成", "端到端")              # rule: diy-test-design/SKILL.md:Design Discipline（Type maps to layer）
PRIORITIES = ("P0", "P1", "P2")                      # rule: diy-test-design/SKILL.md:Design Discipline（Priority maps to risk）
TC_STATUSES = ("待办", "通过", "失败")               # rule: diy-test-design/SKILL.md:Schema status
GAP_DECISIONS = ("待办", "已豁免", "接受缺口")       # rule: diy-test-design/SKILL.md:Schema coverage_gaps.decision
FR_PRIORITIES = ("必须", "应该", "可选")             # rule: diy-prd/SKILL.md:Schema requirements.priority
DEC_STATUSES = ("待定", "已采纳")                    # rule: diy-architecture/SKILL.md:Schema decisions.status
EPIC_STATUSES = ("待办", "进行中", "已完成")         # rule: diy-epics-stories/SKILL.md:Schema epics.status
STORY_STATUSES = ("待办", "进行中", "待审查", "已完成", "已阻塞")  # rule: diy-epics-stories/SKILL.md:Schema stories.status
HTTP_METHODS = ("get", "put", "post", "delete", "options", "head", "patch", "trace")
PATH_ITEM_KEYS = ("parameters", "summary", "description", "servers", "$ref")


class Report:
    """违规/警告收集器；where 统一正斜杠（契约 §3）。"""

    def __init__(self):
        self.violations = []
        self.warnings = []

    def add(self, code, where, msg):
        self.violations.append(diyc_lib.v(code, where, msg))

    def warn(self, msg):
        self.warnings.append(msg)


# ---------------------------------------------------------------- 通用形状工具

def items(container, key) -> list:
    """list-of-dicts 取值（形状异常 → []，非 dict 项剔除）。"""
    if not isinstance(container, dict):
        return []
    value = container.get(key)
    if not isinstance(value, list):
        return []
    return [x for x in value if isinstance(x, dict)]


def is_str(value) -> bool:
    return isinstance(value, str)


def nonempty(value) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return len(value) > 0
    return value is not None and not isinstance(value, bool)


def req(report, where, value, label, code="EMPTY_FIELD") -> bool:
    """必填校验：字符串非空 / 列表字典非空。"""
    if nonempty(value):
        return True
    report.add(code, where, "%s 缺失或为空" % label)
    return False


def enum(report, where, value, allowed, label, code="ENUM_INVALID") -> bool:
    if value in allowed:
        return True
    report.add(code, where, "%s 取值 %r 非法，应为 %s" % (label, value, "/".join(allowed)))
    return False


def dup(report, pairs, label):
    """pairs: [(id, where)]；重复 ID → DUPLICATE_ID（msg 注明首次出现位置）。"""
    seen = {}
    for value, where in pairs:
        if not nonempty(value):
            continue
        if value in seen:
            report.add("DUPLICATE_ID", where,
                       "%s 重复：%s（首次出现在 %s）" % (label, value, seen[value]))
        else:
            seen[value] = where


def scan_assumptions(doc, rel) -> list:
    """深度扫描 [假设] 前缀（契约 §4.2：--final 义务 = zero [假设]）。

    判定与 viewer.py render 同源（值以 `[假设]` 开头即标记）；正文里
    提到该词（如 AC 文本「全部 [假设] 已清除」）不算标记，避免误报。
    """
    hits = []

    def walk(node, path):
        if isinstance(node, dict):
            for key, value in node.items():
                walk(value, "%s.%s" % (path, key) if path else str(key))
        elif isinstance(node, list):
            for i, value in enumerate(node):
                walk(value, "%s[%d]" % (path, i))
        elif isinstance(node, str) and node.startswith("[假设]"):
            hits.append(path)

    walk(doc, "")
    return hits


def tc_declarations(entry, where, report):
    """L3 kill-target 纪律（diy-review L3 / diy-test-design Schema）：technique 枚举 + kill_target 非空。"""
    # rule: diy-review/SKILL.md:L3（every TC bound to the task carries non-empty kill_target
    #       and a technique valid against the test-plan schema enum）
    # rule: diy-test-design/SKILL.md:Final requires（every case carrying a schema-enum technique
    #       and non-empty kill_target）
    enum(report, where + ".technique", entry.get("technique"), TECHNIQUES, "technique")
    req(report, where + ".kill_target", entry.get("kill_target"), "kill_target（故障假设）")


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

    goals = items(doc, "goals")
    counts["goals"] = len(goals)
    if not goals:
        report.add("EMPTY_FIELD", rel + " goals", "goals 缺失或为空（2-5 条可度量目标）")
    for g in goals:
        w = "%s goals[%s]" % (rel, g.get("id") or "?")
        req(report, w + ".id", g.get("id"), "goal id")
        req(report, w + ".goal", g.get("goal"), "goal")
        req(report, w + ".metric", g.get("metric"), "metric（成功如何度量）")

    users = items(doc, "users")
    counts["users"] = len(users)
    for u in users:
        w = "%s users[%s]" % (rel, u.get("id") or "?")
        req(report, w + ".id", u.get("id"), "user id")
        req(report, w + ".name", u.get("name"), "persona name")
        req(report, w + ".need", u.get("need"), "need")
    dup(report, [(u.get("id"), "%s users[%s].id" % (rel, u.get("id") or "?")) for u in users],
        "user id")

    features = items(doc, "features")
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
        reqs = items(f, "requirements")
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

    nfrs = items(doc, "nfrs")
    counts["nfrs"] = len(nfrs)
    for n in nfrs:
        w = "%s nfrs[%s]" % (rel, n.get("id") or "?")
        req(report, w + ".id", n.get("id"), "NFR id")
        req(report, w + ".statement", n.get("statement"), "NFR statement")
    dup(report, [(n.get("id"), "%s nfrs[%s].id" % (rel, n.get("id") or "?")) for n in nfrs],
        "NFR id")

    # rule: diy-prd/SKILL.md:PRD Discipline（Every pending decision lives in the file；
    #       用户确认后 [假设] 才可去除）→ --final 时未答问题 = 未决
    for q in items(doc, "open_questions"):
        w = "%s open_questions[%s]" % (rel, q.get("id") or "?")
        req(report, w + ".id", q.get("id"), "question id")
        req(report, w + ".question", q.get("question"), "question")
        if final and not nonempty(q.get("answer")):
            report.add("PENDING_DECISION", w,
                       "定稿前该开放问题须回答（answer 为空；回答保留在文件中供审计）")
    return counts


# ---------------------------------------------------------------- architecture

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
    for i, s in enumerate(items(doc, "stack")):
        w = "%s stack[%d]" % (rel, i)
        req(report, w + ".choice", s.get("choice"), "stack.choice")
        req(report, w + ".why", s.get("why"), "stack.why")

    decisions = items(doc, "decisions")
    counts["decisions"] = len(decisions)
    if not decisions:
        report.add("EMPTY_FIELD", rel + " decisions", "decisions 缺失或为空")
    prd_available = docs.doc("prd") is not None
    if not prd_available:
        report.warn("prd.yaml 缺失/损坏：architecture affects 引用无法解析（跳过该子检查）")
    else:
        known = set(docs.frs()) | set(docs.nfrs())
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
        alternatives = items(d, "alternatives")
        if not alternatives:
            report.add("EMPTY_FIELD", w + ".alternatives",
                       "缺少被否决备选（alternatives 至少一条；无备选的决策通常是未检验的默认）")
        for j, alt in enumerate(alternatives):
            req(report, "%s.alternatives[%d].option" % (w, j), alt.get("option"), "option")
            req(report, "%s.alternatives[%d].why_not" % (w, j), alt.get("why_not"), "why_not")
        affects = d.get("affects")
        if not nonempty(affects) or not isinstance(affects, list):
            report.add("EMPTY_FIELD", w + ".affects", "affects 缺失或为空（须列出影响的 FR/NFR ID）")
        elif prd_available:
            # team-lead 裁定：decisions[].affects[] 必须在 prd.yaml 可解析 → UNKNOWN_ID
            for j, ref in enumerate(affects):
                if not is_str(ref) or not ref:
                    report.add("EMPTY_FIELD", "%s.affects[%d]" % (w, j), "affects 项缺失或非字符串")
                elif ref not in known:
                    report.add("UNKNOWN_ID", "%s.affects[%d]" % (w, j),
                               "%s 在 prd.yaml 中不存在（affects 只引用现有 FR/NFR ID，不复制需求文本）"
                               % ref)

    for i, c in enumerate(items(doc, "components")):
        w = "%s components[%d]" % (rel, i)
        req(report, w + ".id", c.get("id"), "component id")
        req(report, w + ".name", c.get("name"), "component name")
        req(report, w + ".responsibility", c.get("responsibility"), "responsibility")
    for i, r in enumerate(items(doc, "risks")):
        w = "%s risks[%d]" % (rel, i)
        req(report, w + ".id", r.get("id"), "risk id")
        req(report, w + ".risk", r.get("risk"), "risk")
        req(report, w + ".mitigation", r.get("mitigation"), "mitigation")
    return counts


# ---------------------------------------------------------------- openapi

def check_openapi(doc, rel, docs, final, report) -> dict:
    """openapi.yaml：轻量 3.1 结构自检（契约 §4.2 硬点）+ x-fr 引用解析。"""
    # rule: diy-openapi/SKILL.md:Contract Discipline（Valid OpenAPI 3.1 above all；
    #       each operation carries x-fr referencing existing FR IDs from prd.yaml）
    # rule: diy-openapi/SKILL.md:Final requires（openapi field is 3.1.x，zero [假设]，
    #       every x-fr ID resolving in prd.yaml）
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

    paths = doc.get("paths")
    if not isinstance(paths, dict) or not paths:
        report.add("EMPTY_FIELD", rel + " paths", "paths 缺失或为空")
        return counts
    prd_available = docs.doc("prd") is not None
    if not prd_available:
        report.warn("prd.yaml 缺失/损坏：openapi x-fr 引用无法解析（跳过该子检查）")
    else:
        known = set(docs.frs()) | set(docs.nfrs())
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
            if not nonempty(op.get("responses")) or not isinstance(op.get("responses"), dict):
                report.add("EMPTY_FIELD", ow + ".responses", "responses 缺失或为空")
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
    epics = items(doc, "epics")
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


# ---------------------------------------------------------------- stories

def _design_pages(docs):
    """design.yaml pages 的 P-x 集合；文档缺失/损坏 → None（跳过解析）。"""
    design = docs.doc("design")
    if not isinstance(design, dict):
        return None
    return {p.get("id") for p in items(design, "pages") if is_str(p.get("id"))}


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
    stories = items(doc, "stories")
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
    referenced = set()
    ac_pairs = []
    for s in stories:
        w = "%s stories[%s]" % (rel, s.get("id") or "?")
        req(report, w + ".id", s.get("id"), "story id")
        req(report, w + ".epic", s.get("epic"), "epic（E-x 引用）")
        req(report, w + ".title", s.get("title"), "title")
        req(report, w + ".narrative", s.get("narrative"), "narrative")
        enum(report, w + ".status", s.get("status"), STORY_STATUSES, "status")
        acs = items(s, "acceptance_criteria")
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
    return counts


# ---------------------------------------------------------------- test-plan

def check_test_plan(doc, rel, docs, final, report) -> dict:
    """test-plan.yaml：用例声明形状 + AC 解析 + 缺口形状；--final 禁 decision: 待办。"""
    # rule: diy-test-design/SKILL.md:Schema（test_cases / static_checks / coverage_gaps）
    # rule: diy-test-design/SKILL.md:Design Discipline（Gaps are decisions, not omissions；
    #       waived must cite prior user confirmation）
    # rule: diy-test-design/SKILL.md:Final requires（zero [假设]，zero decision: 待办
    #       gaps，every ac resolving in stories.yaml，schema-enum technique，non-empty kill_target）
    counts = {"cases": 0, "by_type": {}, "by_priority": {}, "acs_covered": 0,
              "gaps_by_decision": {}}
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
    cases = items(doc, "test_cases")
    counts["cases"] = len(cases)
    if not cases:
        report.add("EMPTY_FIELD", rel + " test_cases", "test_cases 缺失或为空")
    tc_pairs = []
    covered = set()
    for t in cases:
        w = "%s test_cases[%s]" % (rel, t.get("id") or "?")
        req(report, w + ".id", t.get("id"), "case id")
        req(report, w + ".title", t.get("title"), "title")
        tc_pairs.append((t.get("id"), w + ".id"))
        ac_value = t.get("ac")
        ac_list = diyc_lib._ac_ids(t)
        if not ac_list:
            report.add("EMPTY_FIELD", w + ".ac", "ac 缺失或为空（每个用例须绑定现有 AC ID）")
        elif stories_available:
            for j, ref in enumerate(ac_list):
                where = w + ".ac" if is_str(ac_value) else "%s.ac[%d]" % (w, j)
                if ref not in known_acs:
                    report.add("UNKNOWN_ID", where, "%s 在 stories.yaml 中不存在" % ref)
                else:
                    covered.add(ref)
        if enum(report, w + ".type", t.get("type"), CASE_TYPES, "type"):
            counts["by_type"][t["type"]] = counts["by_type"].get(t["type"], 0) + 1
        if enum(report, w + ".priority", t.get("priority"), PRIORITIES, "priority"):
            counts["by_priority"][t["priority"]] = counts["by_priority"].get(t["priority"], 0) + 1
        enum(report, w + ".status", t.get("status"), TC_STATUSES, "status")
        tc_declarations(t, w, report)
        steps = t.get("steps")
        if not (isinstance(steps, list) and any(is_str(x) and x.strip() for x in steps)):
            report.add("EMPTY_FIELD", w + ".steps",
                       "steps 缺失或为空（用例须可执行：具体验证步骤 + 预期结果）")
    dup(report, tc_pairs, "case id")
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
    return counts


# 入口分派由 diyc_check.run() 持有；本模块只暴露 check_* 纯函数
CHECKERS = {
    "prd": check_prd,
    "architecture": check_architecture,
    "openapi": check_openapi,
    "epics": check_epics,
    "stories": check_stories,
    "test-plan": check_test_plan,
}
