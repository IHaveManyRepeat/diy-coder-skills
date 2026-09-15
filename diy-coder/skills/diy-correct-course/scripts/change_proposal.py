# -*- coding: utf-8 -*-
"""diy-correct-course 确定性引擎：影响面采集（委派 diyc 交叉核对）+ change-proposal.yaml 校验。

子命令：
  collect  执行期变更的影响面采集（只读，绝不写文件）：
             1 门禁（源 step-1 HALT 判据的机械面）：prd.yaml / epics.yaml / stories.yaml
               三件套在场且 project.status 均为 final；不满足 → 零产出 exit 1 +
               结构化拒绝回执（violations 带码 + gate.route 给路由）。
               architecture.yaml / openapi.yaml / design.yaml 缺席不拒（源「Architecture、
               UI/UX 可选」）→ warning。
             2 影响面摘要：读六产物（任务书 §5）的 ID 级摘要——prd features/FR/NFR、epics、
               stories + AC、architecture decisions、openapi operations、design pages。
               摘要只带 ID / 标题级信息，不复制内容（引用式纪律）。
             3 跨文档核对委托（任务书 §2.3）：子进程跑 `diyc.py check --type
               prd|architecture|openapi|epics|stories --final --json`——diyc 是跨文档机械核对
               的唯一入口，本引擎不重实现其规则；回执违规并入 diyc.check.violations 证据键
               （影响证据，不在此判死）。diyc 缺席 / 失败 → TOOL_MISSING / TOOL_ERROR 降级
               warning，不崩。
             4 引用链（--target ID）：跨文档扫描该 ID 的上游/下游引用点（epics.feature_refs /
               AC.refs / AC.design_ref / decisions.affects / openapi x-fr / TC.ac /
               sprint test_refs + prd feature→FR、story→AC 归属边），迭代两跳；命中集合即
               变更涟漪面（施工影响的机械证据）。引用链仅支持稳定 ID（文件类 path: 目标
               不参与遍历）；target 格式非法 → ENUM_INVALID，产物中无此 ID → UNKNOWN_ID，
               均 exit 1 零产出。
  check    校验 {output_dir}/change-proposal.yaml（CP-### 集合）：schema / 枚举
           （status/mode/scope/artifact/kind）/ edits 完整（old+new+rationale 非空且
           old != new）/ impacts 与 edits 的 target 形态（产物类稳定 ID / infra 类
           path:<相对路径>，形态与 artifact 双向绑定）/ handoff.route 白名单 / ID 唯一 /
           单项 --id 过滤；--final 附加：status ∈ {final, approved}、zero [ASSUMPTION]、
           handoff.route 在场且白名单、impacts 非空、approach 已选定（PENDING_DECISION）、
           scope 与 handoff 一致性（minor→单技能直改 / moderate→backlog 重组 /
           major→规划层）。exit 0 唯一放行。

分工裁定（任务书 §2.2/§5）：change-proposal 属新产物类型，不进 diyc.py check 的硬编码
类型集；本引擎契约同构（exit 0 唯一放行 / --json 单行回执 / violations[{code, where, msg}]
+ counts；where 正斜杠、相对 project-root）；--previous 不实现（提案记录追加式，同 key 原位
更新，无 ID 集合收缩风险，对齐 P1 §8.5 与 B1 记账先例）。违规码全部复用 batch3-contract
§3 冻结集；新增 TOOL_MISSING / TOOL_ERROR（diyc 委派降级专用，同 readiness 先例）。
只出提案、不改真源：本引擎与技能都不写 prd / epics / stories / architecture / openapi /
design / sprint —— 真源修改由各产物所属技能的 update 模式执行。
"""
# trace: 迁移计划 §二 验收 #3（前置门禁零产出退出）/#4（ID 链接入）/#12（diyc 接线）
import argparse
import io
import json
import os
import re
import subprocess
import sys

import yaml

PROPOSAL_FILE = "change-proposal.yaml"
PRD_FILE = "prd.yaml"
EPICS_FILE = "epics.yaml"
STORIES_FILE = "stories.yaml"
ARCH_FILE = "architecture.yaml"
OPENAPI_FILE = "openapi.yaml"
DESIGN_FILE = "design.yaml"
TESTPLAN_FILE = "test-plan.yaml"
SPRINT_FILE = "sprint.yaml"

# 六产物（影响面摘要面）；门禁三件套全部须 project.status: final（源 HALT 判据）
DOC_FILES = (PRD_FILE, EPICS_FILE, STORIES_FILE, ARCH_FILE, OPENAPI_FILE, DESIGN_FILE)
GATE_FILES = (PRD_FILE, EPICS_FILE, STORIES_FILE)
ROUTE_BY_FILE = {PRD_FILE: "diy-prd", EPICS_FILE: "diy-epics-stories",
                 STORIES_FILE: "diy-epics-stories"}
OPTIONAL_FILES = (ARCH_FILE, OPENAPI_FILE, DESIGN_FILE)

DIYC_REL = ("diy-tools", "scripts", "diyc.py")
DIYC_TYPES = ("prd", "architecture", "openapi", "epics", "stories")
HTTP_METHODS = ("get", "put", "post", "delete", "options", "head", "patch", "trace")

STATUSES = ("draft", "final", "approved", "rejected")
FINAL_STATUSES = ("final", "approved")
MODES = ("incremental", "batch")
SCOPES = ("minor", "moderate", "major")
# 目标归属：产物类（target 用稳定 ID）+ infra 类（部署脚本 / CI 配置 / IaC / 监控，
# target 用 path:<相对路径>）——源 checklist §3.4「其他工件」的承接面；
# 2026-09-14 用户裁定：test-plan 与 infra 此前被整体裁剪且理由部分不实，修正为可表达
ARTIFACTS = ("prd", "epics", "stories", "architecture", "openapi", "design",
             "test-plan", "infra")
INFRA = "infra"
PATH_PREFIX = "path:"
KINDS = ("modify", "add", "remove")
APPROACH_PATHS = ("direct-adjustment", "rollback", "mvp-review")

# 三级 scope → 交接对象（源 step-5：Minor 开发者直改 / Moderate backlog 重组 / Major 规划层重规划）
ROUTE_DIRECT = ("diy-dev", "diy-quick-dev", "diy-prd", "diy-architecture", "diy-epics-stories",
                "diy-openapi", "diy-design", "diy-create-story", "diy-test-design",
                "diy-e2e-tests", "diy-review")
ROUTE_BACKLOG = ("diy-sprint", "diy-epics-stories", "diy-prd")
ROUTE_REPLAN = ("diy-prd", "diy-architecture", "diy-epics-stories")
ROUTE_SETS = {"minor": ROUTE_DIRECT, "moderate": ROUTE_BACKLOG, "major": ROUTE_REPLAN}
KNOWN_ROUTES = tuple(sorted({r for routes in ROUTE_SETS.values() for r in routes}))

# target / impacts.target 的 ID 格式集（跨产物稳定 ID：prd F/FR/NFR/G/U/Q、epics E、
# stories S/AC、architecture D/C/R、design P、test-plan TC）
TARGET_PATTERNS = (r"F-\d+", r"FR-\d+\.\d+", r"NFR-\d+", r"G-\d+", r"U-\d+", r"Q-\d+",
                   r"E-\d+", r"S-\d+", r"AC-\d+\.\d+", r"D-\d+", r"C-\d+", r"R-\d+",
                   r"P-\d+", r"TC-\d+\.\d+\.\d+")
TARGET_RE = re.compile(r"(?:%s)\Z" % "|".join(TARGET_PATTERNS))

CP_RE = re.compile(r"CP-\d{3}")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


def v(code, where, msg):
    return {"code": code, "where": where, "msg": msg}


def nonempty(value):
    return value is not None and str(value).strip() != ""


def items(doc, key):
    """取顶层列表键；缺失/非列表 → []。"""
    if not isinstance(doc, dict):
        return []
    value = doc.get(key)
    return value if isinstance(value, list) else []


def load_yaml_safe(path):
    """读 YAML：(data, err)。文件缺失 → (None, None)；空文件 → ({}, None)；损坏 → (None, 原因)。"""
    if not os.path.isfile(path):
        return None, None
    try:
        with io.open(path, "r", encoding="utf-8") as f:
            return (yaml.safe_load(f) or {}), None
    except yaml.YAMLError as e:
        return None, str(e)
    except OSError as e:
        return None, str(e)


def display_path(path, project_root):
    """where 显示口径（对齐 diyc）：正斜杠 + 相对 project-root；越界则绝对路径。"""
    try:
        rel = os.path.relpath(path, project_root)
    except ValueError:
        rel = os.path.abspath(path)
    if rel.startswith(".."):
        return os.path.abspath(path).replace("\\", "/")
    return rel.replace("\\", "/")


def collect_strings(node):
    """递归收集映射/列表内的全部字符串（键与值）——[ASSUMPTION] 扫描用。"""
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for key, value in node.items():
            yield str(key)
            for s in collect_strings(value):
                yield s
    elif isinstance(node, list):
        for item in node:
            for s in collect_strings(item):
                yield s


def is_target_id(value):
    return bool(TARGET_RE.fullmatch(str(value)))


def is_path_target(value):
    """path:<相对路径> 形态：正斜杠、相对（无 / 开头、无盘符、无 . 与 .. 段）。"""
    s = str(value)
    if not s.startswith(PATH_PREFIX):
        return False
    body = s[len(PATH_PREFIX):]
    if not body or body.startswith("/") or "\\" in body or bool(re.match(r"^[A-Za-z]:", body)):
        return False
    return all(part not in ("", ".", "..") for part in body.split("/"))


def check_target(artifact, target, where):
    """target 形态校验 + 与 artifact 的双向绑定：产物类用稳定 ID，infra 用 path:。"""
    if not nonempty(target):
        return [v("EMPTY_FIELD", where, "target 缺失")]
    t = str(target)
    if is_target_id(t):
        if str(artifact) == INFRA:
            return [v("ENUM_INVALID", where,
                      "artifact: infra 的目标须为文件路径（path:<相对路径>），"
                      "不能是产物 ID：%s" % t)]
        return []
    if is_path_target(t):
        if nonempty(artifact) and str(artifact) != INFRA:
            return [v("ENUM_INVALID", where,
                      "path: 文件目标须配 artifact: infra（实为 %s）：%s" % (artifact, t))]
        return []
    return [v("ENUM_INVALID", where,
              "target 须为稳定 ID（如 FR-x.y / F-x / S-x / AC-x.y / D-x / TC-x.y.z）"
              "或文件路径（path:<相对路径>），实为 %s" % t)]


# ---------------------------------------------------------------- 文档装载与摘要

def load_docs(out_dir):
    """一次性装载六产物 + 只读邻接产物（test-plan / sprint）：{文件名: {present,data,err}}。"""
    docs = {}
    for filename in DOC_FILES + (TESTPLAN_FILE, SPRINT_FILE):
        data, err = load_yaml_safe(os.path.join(out_dir, filename))
        docs[filename] = {"present": data is not None or err is not None,
                          "data": data, "err": err}
    return docs


def operations(openapi_data):
    """openapi paths 展开为 operation 摘要（operationId/path/method/x-fr）。"""
    out = []
    paths = openapi_data.get("paths") if isinstance(openapi_data, dict) else None
    if not isinstance(paths, dict):
        return out
    for path, item in paths.items():
        if not isinstance(item, dict):
            continue
        for method, op in item.items():
            if str(method).lower() not in HTTP_METHODS or not isinstance(op, dict):
                continue
            out.append({"operationId": op.get("operationId"), "path": str(path),
                        "method": str(method).lower(),
                        "x_fr": [str(r) for r in items(op, "x-fr") if nonempty(r)]})
    return out


def doc_summaries(docs):
    """六产物 ID 级摘要（影响面采集面；只带 ID / 标题级信息，不复制内容）。"""
    prd = docs[PRD_FILE]["data"]
    features = []
    for feature in items(prd, "features"):
        if not isinstance(feature, dict):
            continue
        features.append({"id": feature.get("id"), "name": feature.get("name"),
                         "requirements": [r.get("id") for r in items(feature, "requirements")
                                          if isinstance(r, dict) and nonempty(r.get("id"))]})
    stories = []
    for story in items(docs[STORIES_FILE]["data"], "stories"):
        if not isinstance(story, dict):
            continue
        stories.append({"id": story.get("id"), "epic": story.get("epic"),
                        "title": story.get("title"), "status": story.get("status"),
                        "acs": [ac.get("id") for ac in items(story, "acceptance_criteria")
                                if isinstance(ac, dict) and nonempty(ac.get("id"))]})
    decisions = []
    for dec in items(docs[ARCH_FILE]["data"], "decisions"):
        if not isinstance(dec, dict):
            continue
        decisions.append({"id": dec.get("id"), "title": dec.get("title"),
                          "affects": [str(r) for r in items(dec, "affects") if nonempty(r)],
                          "status": dec.get("status")})
    pages = []
    for page in items(docs[DESIGN_FILE]["data"], "pages"):
        if not isinstance(page, dict):
            continue
        pages.append({"id": page.get("id"), "name": page.get("name"),
                      "route": page.get("route")})
    return {
        "prd": {"file": PRD_FILE, "features": features,
                "nfrs": [n.get("id") for n in items(prd, "nfrs")
                         if isinstance(n, dict) and nonempty(n.get("id"))]},
        "epics": {"file": EPICS_FILE,
                  "epics": [{"id": e.get("id"), "title": e.get("title"),
                             "feature_refs": [str(r) for r in items(e, "feature_refs")
                                              if nonempty(r)],
                             "status": e.get("status")}
                            for e in items(docs[EPICS_FILE]["data"], "epics")
                            if isinstance(e, dict)]},
        "stories": {"file": STORIES_FILE, "stories": stories},
        "architecture": {"file": ARCH_FILE, "decisions": decisions},
        "openapi": {"file": OPENAPI_FILE, "operations": operations(docs[OPENAPI_FILE]["data"])},
        "design": {"file": DESIGN_FILE, "pages": pages},
    }


def doc_status(docs):
    """六产物在场/可解析/project.status（门禁细节面）。"""
    out = {}
    for filename in DOC_FILES:
        entry = docs[filename]
        data = entry["data"]
        project = data.get("project") if isinstance(data, dict) else None
        out[filename[:-len(".yaml")]] = {
            "file": filename, "found": entry["present"], "parsable": entry["err"] is None,
            "status": project.get("status") if isinstance(project, dict) else None}
    return out


# ---------------------------------------------------------------- 门禁

def gate_check(docs, out_dir, project_root):
    """门禁：三件套在场且 project.status 均为 final。返回 (passed, violations, route)。"""
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
        if status != "final":
            violations.append(v("STATUS_MISMATCH", show + " project.status",
                                "%s 的 project.status 须为 final（实为 %s）；先跑 %s 定稿"
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


# ---------------------------------------------------------------- diyc 委派

def diyc_script_path():
    """diyc.py 路径：由引擎自身位置推算 skills 根（源码与安装布局同构，任务书 §2.3）。"""
    skills_root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    return os.path.join(skills_root, *DIYC_REL)


def diyc_type_check(script, project_root, type_name):
    """委派 diyc check --type T --final。返回 (回执 dict | None, warning | None)。"""
    where = "diyc.py check --type %s" % type_name
    cmd = [sys.executable, script, "check", "--type", type_name, "--final",
           "--project-root", project_root, "--json"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              encoding="utf-8", errors="replace")
    except OSError as e:
        return None, v("TOOL_ERROR", where, "diyc 子进程无法启动：%s" % e)
    if proc.returncode not in (0, 1):
        tail = " ".join((proc.stderr or proc.stdout or "").split())[-200:]
        return None, v("TOOL_ERROR", where,
                       "diyc 非预期退出码 %s（期望 0|1）：%s"
                       % (proc.returncode, tail or "无输出"))
    payload = None
    for line in reversed((proc.stdout or "").splitlines()):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
            break
        except ValueError:
            continue
    if not isinstance(payload, dict):
        return None, v("TOOL_ERROR", where, "diyc 回执不可解析（--json 面单行 JSON 缺失）")
    return payload, None


def run_diyc_checks(project_root, out_dir):
    """跑五型 check，合并回执。返回 (diyc 块, warnings)。"""
    warnings = []
    script = diyc_script_path()
    block = {"available": False, "script": display_path(script, project_root),
             "checked": [], "check": {"violations": [], "counts": {}}}
    if not os.path.isfile(script):
        warnings.append(v("TOOL_MISSING", block["script"],
                          "diyc.py 缺席：跨文档核对降级，请从会话侧人工复核 ID 链与引用面"))
        return block, warnings
    block["available"] = True
    for type_name in DIYC_TYPES:
        payload, warning = diyc_type_check(script, project_root, type_name)
        if warning is not None:
            warnings.append(warning)
            continue
        block["checked"].append(type_name)
        # diyc 自解析产物目录：与本引擎 --output-dir 不一致时证据来自另一目录，须显式告警
        resolved = payload.get("output_dir")
        if nonempty(resolved):
            a = os.path.normcase(os.path.abspath(os.path.join(project_root, str(resolved))))
            if a != os.path.normcase(out_dir):
                warnings.append(v("SET_MISMATCH", str(resolved),
                                  "diyc 解析的产物目录与本引擎 --output-dir 不一致："
                                  "跨文档证据可能来自另一目录"))
        for item in payload.get("violations") or []:
            if isinstance(item, dict):
                block["check"]["violations"].append(dict(item, type=type_name))
        if isinstance(payload.get("counts"), dict):
            block["check"]["counts"][type_name] = payload["counts"]
        if payload.get("warnings"):
            block["check"].setdefault("warnings", []).extend(payload["warnings"])
    return block, warnings


# ---------------------------------------------------------------- collect

def empty_payload(args, command):
    return {
        "ok": False,
        "command": command,
        "project_root": args.project_root,
        "output_dir": os.path.normpath(os.path.abspath(args.output_dir)).replace("\\", "/"),
        "violations": [],
        "warnings": [],
        "counts": {},
    }


def cmd_collect(args):
    root = os.path.abspath(args.project_root)
    out = os.path.abspath(args.output_dir)
    docs = load_docs(out)
    warnings = []
    payload = empty_payload(args, "collect")
    payload.update({
        "gate": {"passed": False, "files": doc_status(docs), "route": None},
        "docs": {},
        "chain": [],
        "diyc": {"available": False, "script": None, "checked": [],
                 "check": {"violations": [], "counts": {}}},
    })

    passed, violations, route = gate_check(docs, out, root)
    payload["gate"] = {"passed": passed, "files": doc_status(docs), "route": route}
    payload["violations"] = violations

    for filename in OPTIONAL_FILES:
        entry = docs[filename]
        show = display_path(os.path.join(out, filename), root)
        if entry["err"] is not None:
            warnings.append(v("UNPARSABLE_YAML", show,
                              "%s 不可解析，影响面采集将跳过该文档" % filename))
        elif not entry["present"]:
            warnings.append(v("MISSING_FILE", show,
                              "%s 未找到：影响面采集粒度受限（源「可选文档」语义，不阻断）"
                              % filename))

    if not passed:
        payload["warnings"] = warnings
        emit(payload, args.json, human_collect)
        return 1

    summaries = doc_summaries(docs)
    payload["docs"] = summaries

    target = args.target
    if nonempty(target) and not is_target_id(str(target)):
        payload["violations"] = [v("ENUM_INVALID", "--target",
                                   "引用链遍历仅支持稳定 ID（如 FR-x.y / F-x / S-x / "
                                   "AC-x.y / D-x / TC-x.y.z）；文件类目标（path:...）"
                                   "不参与引用链，实为 %s" % target)]
        payload["warnings"] = warnings
        emit(payload, args.json, human_collect)
        return 1
    if nonempty(target) and str(target) not in known_ids(docs):
        payload["violations"] = [v("UNKNOWN_ID", "--target",
                                   "%s 在六产物与 test-plan / sprint 中均不存在" % target)]
        payload["warnings"] = warnings
        emit(payload, args.json, human_collect)
        return 1

    chain = scan_chain(str(target), ref_sites(docs)) if nonempty(target) else []
    diyc_block, diyc_warnings = run_diyc_checks(root, out)
    warnings += diyc_warnings

    payload["ok"] = True
    payload["chain"] = chain
    payload["diyc"] = diyc_block
    payload["warnings"] = warnings
    payload["counts"] = {
        "features": len(summaries["prd"]["features"]),
        "frs": sum(len(f["requirements"]) for f in summaries["prd"]["features"]),
        "nfrs": len(summaries["prd"]["nfrs"]),
        "epics": len(summaries["epics"]["epics"]),
        "stories": len(summaries["stories"]["stories"]),
        "acs": sum(len(s["acs"]) for s in summaries["stories"]["stories"]),
        "decisions": len(summaries["architecture"]["decisions"]),
        "operations": len(summaries["openapi"]["operations"]),
        "pages": len(summaries["design"]["pages"]),
        "chain": len(chain),
        "diyc_violations": len(diyc_block["check"]["violations"]),
    }
    emit(payload, args.json, human_collect)
    return 0


def human_collect(payload):
    if not payload["ok"]:
        if payload["violations"]:
            print("拒绝：")
            for item in payload["violations"]:
                print("- %s %s: %s" % (item["code"], item["where"], item["msg"]))
        else:  # 冗余防御：ok=False 必带 violation（当前不可达）
            print("拒绝：门禁未通过")
        print("路由：%s" % payload["gate"]["route"])
        return
    counts = payload["counts"]
    print("门禁通过：prd / epics / stories 齐备且定稿。")
    print("影响面摘要：FR %d · NFR %d · epic %d · story %d · AC %d · 决策 %d · 操作 %d · 页面 %d"
          % (counts["frs"], counts["nfrs"], counts["epics"], counts["stories"],
             counts["acs"], counts["decisions"], counts["operations"], counts["pages"]))
    if counts["chain"]:
        print("引用链：%d 个引用点" % counts["chain"])
        for hit in payload["chain"]:
            print("- %s %s.%s → %s（%s）"
                  % (hit["doc"], hit["id"], hit["field"], hit["ref"], hit["direction"]))
    if payload["diyc"]["available"]:
        print("diyc 跨文档核对：%s 已跑，违规 %d 条（并入 diyc.check.violations 证据）"
              % (" / ".join(payload["diyc"]["checked"]),
                 len(payload["diyc"]["check"]["violations"])))
    else:
        print("diyc 跨文档核对：不可用（见 warnings）")
    for item in payload["warnings"]:
        print("警告 %s %s: %s" % (item["code"], item["where"], item["msg"]))


# ---------------------------------------------------------------- check

def check_id_date_status(record, where):
    violations = []
    rid = record.get("id")
    if not nonempty(rid):
        violations.append(v("EMPTY_FIELD", where + ".id", "id 缺失"))
    elif not CP_RE.fullmatch(str(rid)):
        violations.append(v("ENUM_INVALID", where + ".id",
                            "id 须为 CP-0nn（三位零填充），实为 %s" % rid))
    date = record.get("date")
    if not nonempty(date):
        violations.append(v("EMPTY_FIELD", where + ".date", "date 缺失"))
    elif not DATE_RE.fullmatch(str(date)):
        violations.append(v("ENUM_INVALID", where + ".date",
                            "date 须为 YYYY-MM-DD，实为 %s" % date))
    status = record.get("status")
    if not nonempty(status):
        violations.append(v("EMPTY_FIELD", where + ".status", "status 缺失"))
    elif str(status) not in STATUSES:
        violations.append(v("ENUM_INVALID", where + ".status",
                            "status 越界：%s（合法集 %s）"
                            % (status, "|".join(STATUSES))))
    mode = record.get("mode")
    if not nonempty(mode):
        violations.append(v("EMPTY_FIELD", where + ".mode", "mode 缺失"))
    elif str(mode) not in MODES:
        violations.append(v("ENUM_INVALID", where + ".mode",
                            "mode 越界：%s（合法集 %s）" % (mode, "|".join(MODES))))
    if not nonempty(record.get("trigger")):
        violations.append(v("EMPTY_FIELD", where + ".trigger",
                            "trigger 缺失（触发问题的用户原话优先）"))
    return violations


def check_enum(value, allowed, where, label):
    """在场值的枚举校验（缺失由各调用点自行判空）。"""
    if nonempty(value) and str(value) not in allowed:
        return [v("ENUM_INVALID", where, "%s 越界：%s（合法集 %s）"
                  % (label, value, "|".join(allowed)))]
    return []


def check_impacts(record, where, final):
    violations = []
    impacts = record.get("impacts")
    if impacts is None:
        return [v("EMPTY_FIELD", where + ".impacts", "impacts 缺失（无影响写空列表）")]
    if not isinstance(impacts, list):
        return [v("EMPTY_FIELD", where + ".impacts", "impacts 不是列表")]
    if final and not impacts:
        violations.append(v("EMPTY_FIELD", where + ".impacts",
                            "--final 要求 impacts 非空（变更必影响至少一处）"))
    for i, impact in enumerate(impacts):
        iw = "%s.impacts[%d]" % (where, i)
        if not isinstance(impact, dict):
            violations.append(v("EMPTY_FIELD", iw, "impact 不是映射"))
            continue
        if not nonempty(impact.get("artifact")):
            violations.append(v("EMPTY_FIELD", iw + ".artifact", "artifact 缺失"))
        else:
            violations += check_enum(impact.get("artifact"), ARTIFACTS,
                                     iw + ".artifact", "artifact")
        violations += check_target(impact.get("artifact"), impact.get("target"),
                                   iw + ".target")
        if not nonempty(impact.get("kind")):
            violations.append(v("EMPTY_FIELD", iw + ".kind", "kind 缺失"))
        else:
            violations += check_enum(impact.get("kind"), KINDS, iw + ".kind", "kind")
        if not nonempty(impact.get("why")):
            violations.append(v("EMPTY_FIELD", iw + ".why", "why 为空（影响理由必须说明）"))
    return violations


def check_edits(record, where, final):
    violations = []
    edits = record.get("edits")
    if edits is None:
        return [v("EMPTY_FIELD", where + ".edits", "edits 缺失（无提案写空列表）")]
    if not isinstance(edits, list):
        return [v("EMPTY_FIELD", where + ".edits", "edits 不是列表")]
    if final and not edits:
        violations.append(v("EMPTY_FIELD", where + ".edits",
                            "--final 要求 edits 非空（提案须有具体改动）"))
    for i, edit in enumerate(edits):
        ew = "%s.edits[%d]" % (where, i)
        if not isinstance(edit, dict):
            violations.append(v("EMPTY_FIELD", ew, "edit 不是映射"))
            continue
        if not nonempty(edit.get("artifact")):
            violations.append(v("EMPTY_FIELD", ew + ".artifact", "artifact 缺失"))
        else:
            violations += check_enum(edit.get("artifact"), ARTIFACTS,
                                     ew + ".artifact", "artifact")
        violations += check_target(edit.get("artifact"), edit.get("target"),
                                   ew + ".target")
        if not nonempty(edit.get("field")):
            violations.append(v("EMPTY_FIELD", ew + ".field", "field 缺失（目标字段路径）"))
        old = edit.get("old")
        new = edit.get("new")
        if not nonempty(old):
            violations.append(v("EMPTY_FIELD", ew + ".old",
                                "old 为空（add 型也须写占位，如 (absent)）"))
        if not nonempty(new):
            violations.append(v("EMPTY_FIELD", ew + ".new", "new 为空"))
        if nonempty(old) and nonempty(new) and str(old) == str(new):
            violations.append(v("SET_MISMATCH", ew,
                                "old 与 new 相同：该提案没有实际改动"))
        if not nonempty(edit.get("rationale")):
            violations.append(v("EMPTY_FIELD", ew + ".rationale",
                                "rationale 为空（每处改动须有理由）"))
    return violations


def check_effort(record, where):
    effort = record.get("effort")
    if effort is None:
        return []
    if not isinstance(effort, dict):
        return [v("EMPTY_FIELD", where + ".effort", "effort 不是映射")]
    violations = []
    for key in ("estimate", "risk", "timeline_impact"):
        if not nonempty(effort.get(key)):
            violations.append(v("EMPTY_FIELD", "%s.effort.%s" % (where, key),
                                "%s 为空（effort 一旦在场须三键齐备）" % key))
    return violations


def check_approach(record, where, final):
    approach = record.get("approach")
    if approach is None:
        if final:
            return [v("PENDING_DECISION", where + ".approach",
                      "--final 要求路径已选定（direct-adjustment|rollback|mvp-review）")]
        return []
    if not isinstance(approach, dict):
        return [v("EMPTY_FIELD", where + ".approach", "approach 不是映射")]
    violations = []
    path = approach.get("path")
    if not nonempty(path):
        violations.append(v("EMPTY_FIELD", where + ".approach.path", "path 缺失"))
    else:
        violations += check_enum(path, APPROACH_PATHS, where + ".approach.path", "path")
    if not nonempty(approach.get("why")):
        violations.append(v("EMPTY_FIELD", where + ".approach.why",
                            "why 为空（路径选择须给理由）"))
    return violations


def check_handoff(record, where, final):
    handoff = record.get("handoff")
    if handoff is None:
        if final:
            return [v("EMPTY_FIELD", where + ".handoff",
                      "--final 要求 handoff 在场（route + note）")]
        return []
    if not isinstance(handoff, dict):
        return [v("EMPTY_FIELD", where + ".handoff", "handoff 不是映射")]
    violations = []
    route = handoff.get("route")
    if not nonempty(route):
        violations.append(v("EMPTY_FIELD", where + ".handoff.route",
                            "route 缺失（交接给哪个 diy 技能）"))
    elif str(route) not in KNOWN_ROUTES:
        violations.append(v("ENUM_INVALID", where + ".handoff.route",
                            "route 不在已知 diy 技能白名单：%s（合法集 %s）"
                            % (route, "|".join(KNOWN_ROUTES))))
    if not nonempty(handoff.get("note")):
        violations.append(v("EMPTY_FIELD", where + ".handoff.note",
                            "note 为空（交接说明必须写明）"))
    return violations


def check_list_field(record, key, where):
    value = record.get(key)
    if value is None:
        return []
    if not isinstance(value, list):
        return [v("EMPTY_FIELD", "%s.%s" % (where, key), "%s 不是列表" % key)]
    if any(not nonempty(item) for item in value):
        return [v("EMPTY_FIELD", "%s.%s" % (where, key), "%s 项不得为空" % key)]
    return []


def check_scope_route(record, where, scope, handoff):
    """scope 与 handoff.route 一致性（源 step-5 三级交接语义）。"""
    if not nonempty(scope) or str(scope) not in SCOPES:
        return []
    if not isinstance(handoff, dict):
        return []
    route = handoff.get("route")
    if not nonempty(route) or str(route) not in KNOWN_ROUTES:
        return []
    allowed = ROUTE_SETS[str(scope)]
    if str(route) not in allowed:
        return [v("SET_MISMATCH", where + ".handoff.route",
                  "scope=%s 的交接对象不匹配：%s（该级允许 %s）"
                  % (scope, route, "|".join(allowed)))]
    return []


def check_final_duties(record, where, status):
    """--final 附加义务：终态 status、零假设。"""
    violations = []
    if str(status) not in FINAL_STATUSES:
        violations.append(v("STATUS_MISMATCH", where + ".status",
                            "--final 要求 status ∈ {%s}（实为 %s）"
                            % ("|".join(FINAL_STATUSES), status)))
    if any("[ASSUMPTION]" in s for s in collect_strings(record)):
        violations.append(v("ASSUMPTION_PRESENT", where,
                            "--final 要求零 [ASSUMPTION]；未决推断须先落定"))
    return violations


def check_record(index, record, final, where_base):
    violations = []
    where = "%s.proposals[%d]" % (where_base, index)
    if not isinstance(record, dict):
        return [v("EMPTY_FIELD", where, "记录不是映射")]
    violations += check_id_date_status(record, where)
    scope = record.get("scope")
    if not nonempty(scope):
        violations.append(v("EMPTY_FIELD", where + ".scope", "scope 缺失"))
    else:
        violations += check_enum(scope, SCOPES, where + ".scope", "scope")
    violations += check_impacts(record, where, final)
    violations += check_edits(record, where, final)
    violations += check_list_field(record, "ripple", where)
    violations += check_effort(record, where)
    violations += check_approach(record, where, final)
    violations += check_handoff(record, where, final)
    violations += check_list_field(record, "open_questions", where)
    if final:
        violations += check_final_duties(record, where, record.get("status"))
        violations += check_scope_route(record, where, scope, record.get("handoff"))
    return violations


def cmd_check(args):
    root = os.path.abspath(args.project_root)
    out = os.path.abspath(args.output_dir)
    path = os.path.join(out, PROPOSAL_FILE)
    show = display_path(path, root)
    violations = []
    warnings = []
    records = []
    matched = 0
    only = args.id

    if nonempty(only) and not CP_RE.fullmatch(str(only)):
        violations.append(v("ENUM_INVALID", show + " id",
                            "id 须为 CP-0nn（三位零填充），实为 %s" % only))

    data, err = load_yaml_safe(path)
    if data is None and err is None:
        violations.append(v("MISSING_FILE", show,
                            "%s 不存在（先完成一次提案起草）" % PROPOSAL_FILE))
    elif err is not None:
        violations.append(v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err))
    elif not isinstance(data, dict):
        violations.append(v("EMPTY_FIELD", show, "顶层不是映射（须为 project + proposals）"))
    else:
        project = data.get("project")
        if project is not None and not isinstance(project, dict):
            violations.append(v("EMPTY_FIELD", show + " project", "project 不是映射"))
        revisions = data.get("revisions")
        if revisions is not None and not isinstance(revisions, list):
            violations.append(v("EMPTY_FIELD", show + " revisions", "revisions 不是列表"))
        raw_records = data.get("proposals")
        if raw_records is None:
            violations.append(v("EMPTY_FIELD", show + " proposals",
                                "proposals 缺失（集合形态；无记录写空列表）"))
        elif not isinstance(raw_records, list):
            violations.append(v("EMPTY_FIELD", show + " proposals", "proposals 不是列表"))
        else:
            records = raw_records
            seen = set()
            for i, record in enumerate(records):
                rid = record.get("id") if isinstance(record, dict) else None
                if nonempty(only) and str(rid) != str(only):
                    continue
                matched += 1
                violations += check_record(i, record, args.final, show)
                if nonempty(rid):
                    if str(rid) in seen:
                        violations.append(v("DUPLICATE_ID", "%s.proposals[%d].id" % (show, i),
                                            "记录 ID %s 重复（CP ID 稳定不重用）" % rid))
                    seen.add(str(rid))
            if nonempty(only) and matched == 0:
                violations.append(v("UNKNOWN_ID", show + " proposals",
                                    "指定 ID %s 不存在" % only))
            if args.final and not records:
                violations.append(v("EMPTY_FIELD", show + " proposals",
                                    "--final 要求至少 1 条记录"))

    counts = {
        "proposals": len(records),
        "matched": matched,
        "by_status": count_by(records, "status"),
        "by_scope": count_by(records, "scope"),
        "by_mode": count_by(records, "mode"),
        "impacts": count_items(records, "impacts"),
        "edits": count_items(records, "edits"),
        "open_questions": count_items(records, "open_questions"),
    }
    ok = not violations
    payload = {
        "ok": ok,
        "command": "check",
        "project_root": args.project_root,
        "output_dir": os.path.normpath(out).replace("\\", "/"),
        "final": args.final,
        "violations": violations,
        "warnings": warnings,
        "counts": counts,
    }
    emit(payload, args.json, human_check)
    return 0 if ok else 1


def count_by(records, key):
    counts = {}
    for record in records:
        if not isinstance(record, dict):
            continue
        value = record.get(key)
        if nonempty(value):
            counts[str(value)] = counts.get(str(value), 0) + 1
    return counts


def count_items(records, key):
    total = 0
    for record in records:
        if isinstance(record, dict) and isinstance(record.get(key), list):
            total += len(record[key])
    return total


def human_check(payload):
    if payload["ok"]:
        print("PASS：%s 校验通过（proposals=%d）"
              % (payload["output_dir"] + "/" + PROPOSAL_FILE, payload["counts"]["proposals"]))
        return
    print("FAIL：")
    for item in payload["violations"]:
        print("- %s %s: %s" % (item["code"], item["where"], item["msg"]))


def emit(payload, as_json, human_lines):
    if as_json:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        human_lines(payload)


def build_parser():
    ap = argparse.ArgumentParser(
        description="diy-correct-course 确定性引擎：影响面采集（委派 diyc）+ "
                    "change-proposal.yaml 校验")
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("collect", help="门禁 + 六产物影响面摘要 + 委派 diyc 交叉核对 + 引用链（只读）")
    c.add_argument("--project-root", default=".", help="项目根（默认 .）")
    c.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    c.add_argument("--target", default=None,
                   help="变更目标 ID（如 FR-1.1 / S-1 / AC-1.1）：输出其上游/下游引用链")
    c.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    c.set_defaults(func=cmd_collect)

    k = sub.add_parser("check", help="校验 change-proposal.yaml（schema/枚举/edits 完整性；"
                                     "--final 附加定稿与交接义务）")
    k.add_argument("--project-root", default=".", help="项目根（默认 .）")
    k.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    k.add_argument("--id", default=None, help="只校验指定记录（CP-###；缺省校验全部）")
    k.add_argument("--final", action="store_true",
                   help="定稿校验：status ∈ {final, approved} + 零假设 + handoff/impacts/approach 义务")
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
