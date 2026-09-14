# -*- coding: utf-8 -*-
"""diy-readiness-check 确定性引擎：开工前门禁 + 需求清点（跨文档核对委派 diyc）+ readiness.yaml 校验。

子命令：
  collect  开工前体检的确定性部分（只读检测，绝不写文件）：
             1 门禁（源技能 step-01 文档发现的门禁化）：prd.yaml / epics.yaml / stories.yaml
               三件套在场，且 epics / stories 的 project.status 为 final；不满足 →
               零产出 exit 1 + 结构化拒绝回执（violations 带码 + gate.route 给路由）。
               architecture.yaml / design.yaml 缺席不拒（源 step-04「无 UX 文档」分支保留；
               源 step-01 §4「Missing Documents (WARNING)」→ architecture 缺席出 warning）。
             2 需求清点单：读结构化 prd.yaml（features[].requirements[] 全量 FR + priority +
               归属 feature；nfrs[]）与 epics / stories 计数——替换源技能 step-02「人工通读
               md 提取全量 FR/NFR」的确定性下沉（diy 产物即结构化单一源）。
             3 跨文档核对委托（任务书 §2.3）：子进程跑 `diyc.py check --type prd|epics|stories
               --final --json`——diyc 是跨文档机械核对的唯一入口，本引擎不重实现其规则；
               回执违规并入 diyc.check.violations 证据键（readiness 会话据此裁决，不在此判死）。
               diyc 缺席 / 子进程失败 → 结构化 warning 降级（TOOL_MISSING / TOOL_ERROR），不崩。
             4 coverage：must 级 FR 与 stories AC refs 的覆盖与缺口（口径同 diyc stories 规则
               「每个 must FR 至少被一条 AC 的 refs 引用」；diyc 回执只给违规不给逐 FR 清单，
               故由结构化产物派生，跨文档判定权仍在 diyc）。
  check    校验 {output_dir}/readiness.yaml（IR-### 集合，形状对齐 bug-log.yaml）：schema /
           枚举 / finding area+severity 枚举 / verdict 与 findings 一致性（ready ⇒ 零
           critical|high；not-ready ⇒ 至少 1 条 critical|high）/ ID 唯一；--final 附加：
           status 已落 final、verdict 非空、每条 finding 有 evidence、counts 与集合一致
           （findings_by_severity 与 coverage 守恒）、零 [ASSUMPTION]。exit 0 唯一放行。

分工裁定（任务书 §2.2/§2.3/§6）：readiness 属新产物类型，不进 diyc.py check 的硬编码类型集；
本引擎契约同构（exit 0 唯一放行 / --json 单行回执 / violations[{code, where, msg}] + counts；
where 正斜杠、相对 project-root）；--previous 不实现（报告追加式，对齐 P1 §8.5 先例）。
违规码复用 batch3-contract §3 冻结集，新增 TOOL_MISSING / TOOL_ERROR（diyc 委派降级专用）。
diyc 路径由引擎自身位置推算（skills/ 根，源码与安装两种布局同构）；产物与 IR-### ID 由
diy-readiness-check 会话（LLM）创作，本引擎只校验格式与唯一性。
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

READINESS_FILE = "readiness.yaml"
PRD_FILE = "prd.yaml"
EPICS_FILE = "epics.yaml"
STORIES_FILE = "stories.yaml"
ARCH_FILE = "architecture.yaml"
DESIGN_FILE = "design.yaml"

# 门禁三件套（文件名，project.status 须为 final）；architecture/design 缺席不拒
GATE_FILES = ((PRD_FILE, False), (EPICS_FILE, True), (STORIES_FILE, True))
ROUTE_BY_FILE = {PRD_FILE: "diy-prd", EPICS_FILE: "diy-epics-stories",
                 STORIES_FILE: "diy-epics-stories"}
DIYC_REL = ("diy-tools", "scripts", "diyc.py")
DIYC_TYPES = ("prd", "epics", "stories")

VERDICTS = ("ready", "ready-with-risks", "not-ready")
FINDING_AREAS = ("prd", "epics", "stories", "ux", "architecture")
SEVERITIES = ("critical", "high", "medium", "low")
BLOCKING_SEVERITIES = ("critical", "high")
SCOPES = ("prd", "architecture", "epics", "stories", "design")
RECORD_STATUSES = ("draft", "final")
COUNT_KEYS = ("frs", "nfrs", "epics", "stories", "acs")

IR_RE = re.compile(r"IR-\d{3}")
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


def id_sort(ids):
    """数字感知排序（FR-1.2 < FR-1.10），对齐 diyc_lib.id_sort。"""
    def key(value):
        return tuple((0, int(p)) if p.isdigit() else (1, p)
                     for p in re.split(r"[-.]", str(value)))
    return sorted(ids, key=key)


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
        if must_final and status != "final":
            violations.append(v("STATUS_MISMATCH", show + " project.status",
                                "%s 的 project.status 须为 final（实为 %s）；"
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
    """must 级 FR 与 AC refs 的覆盖与缺口（口径同 diyc_check_docs.check_stories）。"""
    must = [f["id"] for f in frs if f.get("priority") == "must"]
    covered = [i for i in must if i in referenced]
    gaps = [i for i in must if i not in referenced]
    return {"must_frs": len(must), "covered": len(covered), "gaps": id_sort(gaps)}


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
    """跑 prd/epics/stories 三型 check，合并回执。返回 (diyc 块, warnings)。"""
    warnings = []
    script = diyc_script_path()
    block = {"available": False, "script": display_path(script, project_root),
             "checked": [], "check": {"violations": [], "counts": {}}}
    if not os.path.isfile(script):
        warnings.append(v("TOOL_MISSING", block["script"],
                          "diyc.py 缺席：跨文档核对降级，请从会话侧人工复核 ID 链与覆盖"))
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

def empty_payload(args):
    return {
        "ok": False,
        "command": "collect",
        "project_root": args.project_root,
        "output_dir": os.path.normpath(os.path.abspath(args.output_dir)).replace("\\", "/"),
        "gate": {"passed": False, "files": {}, "route": None},
        "requirements": None,
        "coverage": None,
        "docs": {},
        "diyc": {"available": False, "script": None, "checked": [],
                 "check": {"violations": [], "counts": {}}},
        "violations": [],
        "warnings": [],
        "counts": {},
    }


def cmd_collect(args):
    root = os.path.abspath(args.project_root)
    out = os.path.abspath(args.output_dir)
    docs = load_docs(out)
    warnings = []
    payload = empty_payload(args)
    payload["docs"] = doc_summaries(docs)

    passed, violations, route = gate_check(docs, out, root)
    payload["gate"] = {"passed": passed, "files": payload["docs"], "route": route}
    payload["violations"] = violations

    arch = docs[ARCH_FILE]
    if arch["err"] is not None:
        warnings.append(v("UNPARSABLE_YAML",
                          display_path(os.path.join(out, ARCH_FILE), root),
                          "architecture.yaml 不可解析，架构对齐评估受限"))
    elif not arch["present"]:
        # 源 step-01 §4「Missing Documents (WARNING)」：缺席只降评估完整性，不拒
        warnings.append(v("MISSING_FILE", display_path(os.path.join(out, ARCH_FILE), root),
                          "architecture.yaml 未找到：架构对齐评估将不完整（不阻断体检）"))

    if not passed:
        payload["warnings"] = warnings
        emit(payload, args.json, human_collect)
        return 1

    inventory = read_requirements(docs)
    coverage = compute_coverage(inventory["frs"], inventory["referenced"])
    diyc_block, diyc_warnings = run_diyc_checks(root, out)
    warnings += diyc_warnings

    payload["ok"] = True
    payload["requirements"] = {"frs": inventory["frs"], "nfrs": inventory["nfrs"],
                               "must_frs": [f["id"] for f in inventory["frs"]
                                            if f.get("priority") == "must"]}
    payload["coverage"] = coverage
    payload["diyc"] = diyc_block
    payload["warnings"] = warnings
    payload["counts"] = {
        "features": len({f["feature"] for f in inventory["frs"] if nonempty(f["feature"])}),
        "frs": len(inventory["frs"]),
        "nfrs": len(inventory["nfrs"]),
        "epics": inventory["epics"],
        "stories": inventory["stories"],
        "acs": inventory["acs"],
        "must_frs": coverage["must_frs"],
        "covered": coverage["covered"],
        "gaps": len(coverage["gaps"]),
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
    coverage = payload["coverage"]
    print("门禁通过：prd / epics / stories 齐备且定稿。")
    print("需求清点：FR %d（must %d）· NFR %d · epic %d · story %d · AC %d"
          % (counts["frs"], counts["must_frs"], counts["nfrs"],
             counts["epics"], counts["stories"], counts["acs"]))
    print("覆盖：must FR %d 中 %d 覆盖，缺口 %d %s"
          % (coverage["must_frs"], coverage["covered"], len(coverage["gaps"]),
             "（%s）" % "、".join(coverage["gaps"]) if coverage["gaps"] else ""))
    if payload["diyc"]["available"]:
        print("diyc 跨文档核对：%s 已跑，违规 %d 条（并入 diyc.check.violations 证据）"
              % (" / ".join(payload["diyc"]["checked"]),
                 len(payload["diyc"]["check"]["violations"])))
    else:
        print("diyc 跨文档核对：不可用（见 warnings）")
    for item in payload["warnings"]:
        print("警告 %s %s: %s" % (item["code"], item["where"], item["msg"]))


# ---------------------------------------------------------------- check

def check_findings(record, where, final):
    violations = []
    findings = record.get("findings")
    if findings is None:
        return [v("EMPTY_FIELD", where + ".findings",
                  "findings 缺失（无发现写空列表）")], []
    if not isinstance(findings, list):
        return [v("EMPTY_FIELD", where + ".findings", "findings 不是列表")], []
    for i, finding in enumerate(findings):
        fw = "%s.findings[%d]" % (where, i)
        if not isinstance(finding, dict):
            violations.append(v("EMPTY_FIELD", fw, "finding 不是映射"))
            continue
        area = finding.get("area")
        if not nonempty(area):
            violations.append(v("EMPTY_FIELD", fw + ".area", "area 缺失"))
        elif str(area) not in FINDING_AREAS:
            violations.append(v("ENUM_INVALID", fw + ".area",
                                "area 越界：%s（合法集 %s）"
                                % (area, "|".join(FINDING_AREAS))))
        severity = finding.get("severity")
        if not nonempty(severity):
            violations.append(v("EMPTY_FIELD", fw + ".severity", "severity 缺失"))
        elif str(severity) not in SEVERITIES:
            violations.append(v("ENUM_INVALID", fw + ".severity",
                                "severity 越界：%s（合法集 %s）"
                                % (severity, "|".join(SEVERITIES))))
        if not nonempty(finding.get("message")):
            violations.append(v("EMPTY_FIELD", fw + ".message", "message 为空"))
        evidence = finding.get("evidence")
        if final and not nonempty(evidence):
            violations.append(v("EVIDENCE_MISSING", fw + ".evidence",
                                "--final 要求每条 finding 带 evidence（具体落点）"))
        elif evidence is not None and not nonempty(evidence):
            violations.append(v("EMPTY_FIELD", fw + ".evidence",
                                "evidence 出现时不得为空"))
    return violations, findings


def check_coverage(record, where, final):
    violations = []
    coverage = record.get("coverage")
    if coverage is None:
        if final:
            violations.append(v("EMPTY_FIELD", where + ".coverage",
                                "--final 要求 coverage 在场（must_frs / covered / gaps）"))
        return violations
    if not isinstance(coverage, dict):
        return [v("EMPTY_FIELD", where + ".coverage", "coverage 不是映射")]
    counts = {}
    for key in ("must_frs", "covered"):
        value = coverage.get(key)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            violations.append(v("ENUM_INVALID", "%s.coverage.%s" % (where, key),
                                "%s 须为非负整数（实为 %s）" % (key, value)))
        else:
            counts[key] = value
    gaps = coverage.get("gaps")
    if not isinstance(gaps, list):
        violations.append(v("EMPTY_FIELD", where + ".coverage.gaps",
                            "gaps 缺失或不是列表（无缺口写空列表）"))
    elif any(not nonempty(g) for g in gaps):
        violations.append(v("EMPTY_FIELD", where + ".coverage.gaps",
                            "gaps 项不得为空（FR-x.y）"))
    if final and len(counts) == 2 and isinstance(gaps, list):
        if counts["must_frs"] != counts["covered"] + len(gaps):
            violations.append(v("SET_MISMATCH", where + ".coverage",
                                "counts 与集合不一致：must_frs=%d ≠ covered=%d + gaps=%d"
                                % (counts["must_frs"], counts["covered"], len(gaps))))
    return violations


def check_counts(record, where, final, findings):
    violations = []
    counts = record.get("counts")
    if counts is None:
        return violations
    if not isinstance(counts, dict):
        return [v("EMPTY_FIELD", where + ".counts", "counts 不是映射")]
    for key in COUNT_KEYS:
        value = counts.get(key)
        if value is None:
            if final:
                violations.append(v("EMPTY_FIELD", "%s.counts.%s" % (where, key),
                                    "--final 要求 counts.%s 在场" % key))
        elif not isinstance(value, int) or isinstance(value, bool) or value < 0:
            violations.append(v("ENUM_INVALID", "%s.counts.%s" % (where, key),
                                "%s 须为非负整数（实为 %s）" % (key, value)))
    by_severity = counts.get("findings_by_severity")
    if by_severity is None:
        if final:
            violations.append(v("EMPTY_FIELD", where + ".counts.findings_by_severity",
                                "--final 要求 counts.findings_by_severity 在场"))
        return violations
    if not isinstance(by_severity, dict):
        return violations + [v("EMPTY_FIELD", where + ".counts.findings_by_severity",
                               "findings_by_severity 不是映射")]
    if final:
        bad = [k for k, val in by_severity.items()
               if not isinstance(val, int) or isinstance(val, bool) or val < 0]
        if bad:
            violations.append(v("ENUM_INVALID", where + ".counts.findings_by_severity",
                                "计数须为非负整数：%s" % "、".join(str(k) for k in bad)))
        tally = {}
        for finding in findings:
            if isinstance(finding, dict) and nonempty(finding.get("severity")):
                key = str(finding["severity"])
                tally[key] = tally.get(key, 0) + 1
        declared = {str(k): val for k, val in by_severity.items()
                    if isinstance(val, int) and not isinstance(val, bool) and val}
        if declared != tally:
            violations.append(v("SET_MISMATCH", where + ".counts.findings_by_severity",
                                "counts 与集合不一致：声明 %s，实际 %s" % (declared, tally)))
    return violations


def check_verdict_findings(record, where, verdict, findings):
    """verdict 与 findings 一致性：ready ⇒ 零 critical|high；not-ready ⇒ 至少 1 条。"""
    if not nonempty(verdict) or str(verdict) not in VERDICTS:
        return []
    blocking = [f for f in findings
                if isinstance(f, dict) and str(f.get("severity")) in BLOCKING_SEVERITIES]
    if str(verdict) == "ready" and blocking:
        return [v("SET_MISMATCH", where + ".verdict",
                  "verdict=ready 但存在 %d 条 critical|high finding" % len(blocking))]
    if str(verdict) == "not-ready" and not blocking:
        return [v("SET_MISMATCH", where + ".verdict",
                  "verdict=not-ready 但无 critical|high finding（须至少 1 条）")]
    return []


def check_scope(record, where):
    violations = []
    scope = record.get("scope")
    if scope is None:
        return [v("EMPTY_FIELD", where + ".scope", "scope 缺失（实际清点到的文档）")]
    if not isinstance(scope, list) or not scope:
        return [v("EMPTY_FIELD", where + ".scope", "scope 须为非空列表")]
    seen = set()
    for i, name in enumerate(scope):
        if not nonempty(name):
            violations.append(v("EMPTY_FIELD", "%s.scope[%d]" % (where, i), "scope 项为空"))
        elif str(name) not in SCOPES:
            violations.append(v("ENUM_INVALID", "%s.scope[%d]" % (where, i),
                                "scope 越界：%s（合法集 %s）" % (name, "|".join(SCOPES))))
        elif str(name) in seen:
            violations.append(v("DUPLICATE_ID", "%s.scope[%d]" % (where, i),
                                "scope 项重复：%s" % name))
        else:
            seen.add(str(name))
    return violations


def check_record(index, record, final, where_base):
    violations = []
    where = "%s.checks[%d]" % (where_base, index)
    if not isinstance(record, dict):
        return [v("EMPTY_FIELD", where, "记录不是映射")], []

    rid = record.get("id")
    if not nonempty(rid):
        violations.append(v("EMPTY_FIELD", where + ".id", "id 缺失"))
    elif not IR_RE.fullmatch(str(rid)):
        violations.append(v("ENUM_INVALID", where + ".id",
                            "id 须为 IR-0nn（三位零填充），实为 %s" % rid))

    date = record.get("date")
    if not nonempty(date):
        violations.append(v("EMPTY_FIELD", where + ".date", "date 缺失"))
    elif not DATE_RE.fullmatch(str(date)):
        violations.append(v("ENUM_INVALID", where + ".date",
                            "date 须为 YYYY-MM-DD，实为 %s" % date))

    status = record.get("status")
    if not nonempty(status):
        violations.append(v("EMPTY_FIELD", where + ".status", "status 缺失"))
    elif str(status) not in RECORD_STATUSES:
        violations.append(v("ENUM_INVALID", where + ".status",
                            "status 越界：%s（合法集 %s）"
                            % (status, "|".join(RECORD_STATUSES))))

    verdict = record.get("verdict")
    if nonempty(verdict) and str(verdict) not in VERDICTS:
        violations.append(v("ENUM_INVALID", where + ".verdict",
                            "verdict 越界：%s（合法集 %s）"
                            % (verdict, "|".join(VERDICTS))))

    violations += check_scope(record, where)
    finding_violations, findings = check_findings(record, where, final)
    violations += finding_violations
    violations += check_verdict_findings(record, where, verdict, findings)
    violations += check_coverage(record, where, final)
    violations += check_counts(record, where, final, findings)

    if final:
        violations += check_final_duties(record, where, verdict, status)
    return violations, findings


def check_final_duties(record, where, verdict, status):
    """--final 附加义务：status 已落 final、verdict 已定、零假设。"""
    violations = []
    if str(status) != "final":
        violations.append(v("STATUS_MISMATCH", where + ".status",
                            "--final 要求 status 已落 final（实为 %s）" % status))
    if not nonempty(verdict):
        violations.append(v("PENDING_DECISION", where + ".verdict",
                            "--final 要求 verdict 已定（ready|ready-with-risks|not-ready）"))
    if any("[ASSUMPTION]" in s for s in collect_strings(record)):
        violations.append(v("ASSUMPTION_PRESENT", where,
                            "--final 要求零 [ASSUMPTION]；未决推断须先落定"))
    return violations


def cmd_check(args):
    root = os.path.abspath(args.project_root)
    out = os.path.abspath(args.output_dir)
    path = os.path.join(out, READINESS_FILE)
    show = display_path(path, root)
    violations = []
    warnings = []
    records = []

    data, err = load_yaml_safe(path)
    if data is None and err is None:
        violations.append(v("MISSING_FILE", show,
                            "%s 不存在（先完成一次 readiness 起草）" % READINESS_FILE))
    elif err is not None:
        violations.append(v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err))
    elif not isinstance(data, dict):
        violations.append(v("EMPTY_FIELD", show, "顶层不是映射（须为 project + checks）"))
    else:
        # 裁定：project 形状 {name, created, updated}；状态挂记录级（对齐 checkpoint 先例）
        project = data.get("project")
        if project is not None and not isinstance(project, dict):
            violations.append(v("EMPTY_FIELD", show + " project", "project 不是映射"))
        revisions = data.get("revisions")
        if revisions is not None and not isinstance(revisions, list):
            violations.append(v("EMPTY_FIELD", show + " revisions", "revisions 不是列表"))
        raw_records = data.get("checks")
        if raw_records is None:
            violations.append(v("EMPTY_FIELD", show + " checks",
                                "checks 缺失（集合形态；无记录写空列表）"))
        elif not isinstance(raw_records, list):
            violations.append(v("EMPTY_FIELD", show + " checks", "checks 不是列表"))
        else:
            records = raw_records
            seen = set()
            for i, record in enumerate(records):
                record_violations, _ = check_record(i, record, args.final, show)
                violations += record_violations
                if isinstance(record, dict) and nonempty(record.get("id")):
                    rid = str(record["id"])
                    if rid in seen:
                        violations.append(v("DUPLICATE_ID", "%s.checks[%d].id" % (show, i),
                                            "记录 ID %s 重复（IR ID 稳定不重用）" % rid))
                    seen.add(rid)
            if args.final and not records:
                violations.append(v("EMPTY_FIELD", show + " checks",
                                    "--final 要求至少 1 条记录"))

    counts = {
        "checks": len(records),
        "by_verdict": count_by(records, "verdict"),
        "by_status": count_by(records, "status"),
        "findings": count_items(records, "findings"),
        "gaps": count_gaps(records),
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


def count_gaps(records):
    total = 0
    for record in records:
        coverage = record.get("coverage") if isinstance(record, dict) else None
        if isinstance(coverage, dict) and isinstance(coverage.get("gaps"), list):
            total += len(coverage["gaps"])
    return total


def human_check(payload):
    if payload["ok"]:
        print("PASS：%s 校验通过（checks=%d）"
              % (payload["output_dir"] + "/" + READINESS_FILE, payload["counts"]["checks"]))
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
        description="diy-readiness-check 确定性引擎：开工前门禁 + 需求清点（委派 diyc）+ "
                    "readiness.yaml 校验")
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("collect", help="门禁检测 + 需求清点 + 委派 diyc 跨文档核对（只读）")
    c.add_argument("--project-root", default=".", help="项目根（默认 .）")
    c.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    c.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    c.set_defaults(func=cmd_collect)

    k = sub.add_parser("check", help="校验 readiness.yaml（schema/枚举/verdict 一致性；--final 附加定稿义务）")
    k.add_argument("--project-root", default=".", help="项目根（默认 .）")
    k.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    k.add_argument("--final", action="store_true",
                   help="定稿校验：status 已落 final + verdict 已定 + evidence/counts 义务 + 零假设")
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
