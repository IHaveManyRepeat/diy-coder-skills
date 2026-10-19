# -*- coding: utf-8 -*-
"""diy-readiness-check 常量表与文档装载/门禁/需求清点/覆盖计算共用层。."""

import os
import re

import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import display_path, id_sort, items, load_yaml_safe, nonempty, v  # noqa: E402

READINESS_FILE = "readiness.yaml"
PRD_FILE = "prd.yaml"
EPICS_FILE = "epics.yaml"
STORIES_FILE = "stories.yaml"
ARCH_FILE = "architecture.yaml"
DESIGN_FILE = "design.yaml"

# 门禁三件套（文件名，project.status 须为 已定稿）；architecture/design 缺席不拒
GATE_FILES = ((PRD_FILE, False), (EPICS_FILE, True), (STORIES_FILE, True))
ROUTE_BY_FILE = {PRD_FILE: "diy-prd", EPICS_FILE: "diy-epics-stories",
                 STORIES_FILE: "diy-epics-stories"}
DIYC_TYPES = ("prd", "epics", "stories")

VERDICTS = ("就绪", "有风险就绪", "未就绪")
FINDING_AREAS = ("prd", "epics", "stories", "ux", "architecture")
SEVERITIES = ("严重", "高", "中", "低")
BLOCKING_SEVERITIES = ("严重", "高")
SCOPES = ("prd", "architecture", "epics", "stories", "design")
RECORD_STATUSES = ("草稿", "已定稿")
COUNT_KEYS = ("frs", "nfrs", "epics", "stories", "acs")

IR_RE = re.compile(r"IR-\d{3}")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")

# ---------------------------------------------------------------- 文档装载

def load_docs(out_dir):
    """一次性装载五份文档：{文件名: {"present", "data", "err"}}（只读，不落盘）。"""
    docs = {}
    for filename in (PRD_FILE, EPICS_FILE, STORIES_FILE, ARCH_FILE, DESIGN_FILE):
        data, err = load_yaml_safe(os.path.join(out_dir, filename))
        docs[filename] = {"present": data is not None or err is not None,
                          "data": data, "err": err}
    return docs

def doc_summaries(docs):
    """docs 回执键（短名 = 文件名去 .yaml，对齐 scope 枚举）：在场 / 可解析 / project.status。"""
    summaries = {}
    for filename, entry in docs.items():
        status = None
        if isinstance(entry.get("data"), dict):
            project = entry["data"].get("project")
            if isinstance(project, dict):
                status = project.get("status")
        summaries[filename[:-len(".yaml")]] = {"file": filename, "found": entry["present"],
                                               "parsable": entry["err"] is None,
                                               "status": status}
    return summaries

# ---------------------------------------------------------------- 门禁

def gate_check(docs, out_dir, project_root):
    """门禁：三件套在场且 epics/stories 定稿。返回 (passed, violations, route)。"""
    violations = []
    skills = []
    for filename, must_final in GATE_FILES:
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
        if must_final and status != "已定稿":
            violations.append(v("STATUS_MISMATCH", show + " project.status",
                                "%s 的 project.status 须为 已定稿（实为 %s）；"
                                "先跑 %s 定稿" % (filename,
                                              status if nonempty(status) else "未声明",
                                              ROUTE_BY_FILE[filename])))
            skills.append(ROUTE_BY_FILE[filename])
    route = None
    if violations:
        unique = list(dict.fromkeys(skills))
        route = ("先跑 %s 产出并定稿上游文档，再重跑本技能"
                 % " / ".join(unique) if unique else
                 "先修复上游文档（解析失败或状态未定稿），再重跑本技能")
    return (not violations), violations, route

# ---------------------------------------------------------------- 需求清点

def read_requirements(docs):
    """需求清点单：FR 全量（id/priority/归属 feature）+ NFR id 全量 + AC refs 引用集。"""
    prd = docs[PRD_FILE]["data"] if docs[PRD_FILE]["err"] is None else None
    frs = []
    for feature in items(prd, "features"):
        if not isinstance(feature, dict):
            continue
        fid = feature.get("id")
        for req in items(feature, "requirements"):
            if not isinstance(req, dict) or not nonempty(req.get("id")):
                continue
            frs.append({"id": str(req["id"]), "priority": req.get("priority"),
                        "feature": fid})
    nfrs = [str(n["id"]) for n in items(prd, "nfrs")
            if isinstance(n, dict) and nonempty(n.get("id"))]

    stories = docs[STORIES_FILE]["data"] if docs[STORIES_FILE]["err"] is None else None
    referenced = set()
    acs = 0
    for story in items(stories, "stories"):
        if not isinstance(story, dict):
            continue
        for ac in items(story, "acceptance_criteria"):
            acs += 1
            if not isinstance(ac, dict):
                continue
            for ref in items(ac, "refs"):
                if nonempty(ref):
                    referenced.add(str(ref))
    epics = [e for e in items(docs[EPICS_FILE]["data"], "epics") if isinstance(e, dict)]
    story_count = len([s for s in items(stories, "stories") if isinstance(s, dict)])
    return {"frs": frs, "nfrs": nfrs, "referenced": referenced, "acs": acs,
            "epics": len(epics), "stories": story_count}

def compute_coverage(frs, referenced):
    """必须级 FR 与 AC refs 的覆盖与缺口（口径同 diyc_check_docs.check_stories）。"""
    must = [f["id"] for f in frs if f.get("priority") == "必须"]
    covered = [i for i in must if i in referenced]
    gaps = [i for i in must if i not in referenced]
    return {"must_frs": len(must), "covered": len(covered), "gaps": id_sort(gaps)}
