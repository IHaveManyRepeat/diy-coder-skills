# -*- coding: utf-8 -*-
"""diy-correct-course 引擎常量与基础工具：产物文件名/枚举/路由白名单/target 形态校验 + 六产物装载与 ID 级摘要。."""

import os
import re

import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import items, load_yaml_safe, nonempty, v  # noqa: E402
PRD_FILE = "prd.yaml"
EPICS_FILE = "epics.yaml"
STORIES_FILE = "stories.yaml"
ARCH_FILE = "architecture.yaml"
OPENAPI_FILE = "openapi.yaml"
DESIGN_FILE = "design.yaml"
TESTPLAN_FILE = "test-plan.yaml"
SPRINT_FILE = "sprint.yaml"

# 六产物（影响面摘要面）；门禁三件套全部须 project.status: 已定稿（源 HALT 判据）
DOC_FILES = (PRD_FILE, EPICS_FILE, STORIES_FILE, ARCH_FILE, OPENAPI_FILE, DESIGN_FILE)
GATE_FILES = (PRD_FILE, EPICS_FILE, STORIES_FILE)
ROUTE_BY_FILE = {PRD_FILE: "diy-prd", EPICS_FILE: "diy-epics-stories",
                 STORIES_FILE: "diy-epics-stories"}
OPTIONAL_FILES = (ARCH_FILE, OPENAPI_FILE, DESIGN_FILE)

DIYC_TYPES = ("prd", "architecture", "openapi", "epics", "stories")
HTTP_METHODS = ("get", "put", "post", "delete", "options", "head", "patch", "trace")

STATUSES = ("草稿", "已定稿", "已批准", "已驳回")
FINAL_STATUSES = ("已定稿", "已批准")
MODES = ("增量", "批量")
SCOPES = ("轻微", "中等", "重大")
# 目标归属：产物类（target 用稳定 ID）+ infra 类（部署脚本 / CI 配置 / IaC / 监控，
# target 用 path:<相对路径>）——源 checklist §3.4「其他工件」的承接面；
# 2026-09-14 用户裁定：test-plan 与 infra 此前被整体裁剪且理由部分不实，修正为可表达
ARTIFACTS = ("prd", "epics", "stories", "architecture", "openapi", "design",
             "test-plan", "infra")
INFRA = "infra"
PATH_PREFIX = "path:"
KINDS = ("修改", "新增", "删除")
APPROACH_PATHS = ("直接调整", "回滚", "MVP 复审")

# 三级 scope → 交接对象（源 step-5：轻微 开发者直改 / 中等 backlog 重组 / 重大 规划层重规划）
ROUTE_DIRECT = ("diy-dev", "diy-quick-dev", "diy-prd", "diy-architecture", "diy-epics-stories",
                "diy-openapi", "diy-design", "diy-create-story", "diy-test-design",
                "diy-e2e-tests", "diy-review")
ROUTE_BACKLOG = ("diy-sprint", "diy-epics-stories", "diy-prd")
ROUTE_REPLAN = ("diy-prd", "diy-architecture", "diy-epics-stories")
ROUTE_SETS = {"轻微": ROUTE_DIRECT, "中等": ROUTE_BACKLOG, "重大": ROUTE_REPLAN}
KNOWN_ROUTES = tuple(sorted({r for routes in ROUTE_SETS.values() for r in routes}))

# target / impacts.target 的 ID 格式集（跨产物稳定 ID：prd F/FR/NFR/G/U/Q、epics E、
# stories S/AC、architecture D/C/R、design P、test-plan TC）
TARGET_PATTERNS = (r"F-\d+", r"FR-\d+\.\d+", r"NFR-\d+", r"G-\d+", r"U-\d+", r"Q-\d+",
                   r"E-\d+", r"S-\d+", r"AC-\d+\.\d+", r"D-\d+", r"C-\d+", r"R-\d+",
                   r"P-\d+", r"TC-\d+\.\d+\.\d+")
TARGET_RE = re.compile(r"(?:%s)\Z" % "|".join(TARGET_PATTERNS))

CP_RE = re.compile(r"CP-\d{3}")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")

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
