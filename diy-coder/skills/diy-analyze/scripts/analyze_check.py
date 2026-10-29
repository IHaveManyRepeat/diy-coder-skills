# -*- coding: utf-8 -*-
"""diy-analyze 校验域：层级/枚举常量、回执与 product 读取助手、骨架完备/枚举/ID 纪律校验编排。."""

import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import args_output_dir, load_yaml_safe, v, walk_strings  # noqa: E402

LAYERS = ("展示层", "应用层", "领域层", "基础设施层", "未分层")
SCALES = ("高", "中", "低")
STATUSES = ("草稿", "已定稿")
COMPONENT_STATUS = ("已核实", "待核实")
ID_RE = re.compile(r"^AN-\d{2}$")
MERMAID_HEADS = ("graph", "flowchart", "sequenceDiagram", "classDiagram",
                 "stateDiagram", "erDiagram", "journey", "gantt", "pie")
ASSUMPTION = "[假设]"

def receipt(command, ok, project_root, output_dir, violations=None,
            warnings=None, counts=None, **extra):
    out = {
        "ok": ok,
        "command": command,
        "project_root": project_root,
        "output_dir": output_dir,
        "instance": None,
        "violations": violations or [],
        "warnings": warnings or [],
        "counts": counts or {},
    }
    out.update(extra)
    return out

def emit(result, as_json, human_lines=None):
    """打印回执并返回 exit code：ok → 0；违规 → 1。"""
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    if as_json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        for line in (human_lines or _human_lines(result)):
            print(line)
    return 0 if result["ok"] else 1

def _human_lines(result):
    lines = ["%s: %s" % (result["command"], "通过" if result["ok"] else "未通过")]
    for item in result["violations"]:
        lines.append("违规 [%s] %s：%s" % (item["code"], item["where"], item["msg"]))
    for item in result["warnings"]:
        lines.append("提醒 [%s] %s：%s" % (item["code"], item["where"], item["msg"]))
    if result["counts"]:
        lines.append("计数：" + "，".join(
            "%s=%s" % (k, val) for k, val in result["counts"].items()))
    return lines

def read_product(args, command):
    """读产物；返回 (doc, result 或 None)。违规即回执。"""
    out_dir = args_output_dir(args)
    path = os.path.join(out_dir, "analysis.yaml")
    if not os.path.isfile(path):
        return None, receipt(command, False, args.project_root, out_dir, [
            v("MISSING_FILE", "analysis.yaml",
              "%s 不存在——先跑 init 铸骨架（路由：确认分析问题与代码库路径）" % path)])
    doc, err = load_yaml_safe(path)
    if err:
        return None, receipt(command, False, args.project_root, out_dir, [
            v("UNPARSABLE_YAML", "analysis.yaml", "解析失败：%s" % err)])
    return doc, None

# ---- check -----------------------------------------------------------------

def cmd_check(args):
    doc, bad = read_product(args, "check")
    out_dir = args_output_dir(args)
    if bad:
        return emit(bad, args.json)
    vio = []

    project = doc.get("project") or {}
    status = project.get("status")
    if status not in STATUSES:
        vio.append(v("ENUM_INVALID", "project.status",
                     "取值非法：%r（合法集 %s）" % (status, "|".join(STATUSES))))

    question = doc.get("question") or {}
    for key in ("text", "scope", "output_format", "time_box"):
        if not str(question.get(key) or "").strip():
            vio.append(v("EMPTY_FIELD", "question.%s" % key,
                         "为空——四项定义不得省"))

    arch = doc.get("architecture") or {}
    for key in ("summary", "overview"):
        if not str(arch.get(key) or "").strip():
            vio.append(v("EMPTY_FIELD", "architecture.%s" % key, "为空"))
    mermaid = str(arch.get("mermaid") or "").strip()
    if mermaid and mermaid.split()[0] not in MERMAID_HEADS:
        vio.append(v("ENUM_INVALID", "architecture.mermaid",
                     "图纸类型非法：%s（合法集 %s）"
                     % (mermaid.split()[0], "|".join(MERMAID_HEADS))))

    components = doc.get("components") or []
    seen = []
    ids = set()
    for i, c in enumerate(components):
        where = "components[%d]" % i
        cid = c.get("id")
        if not ID_RE.match(str(cid or "")):
            vio.append(v("ENUM_INVALID", where + ".id",
                         "ID 形态非法：%r（须 AN-<两位序号>）" % cid))
        elif cid in ids:
            vio.append(v("DUPLICATE_ID", where + ".id", "%s 重复" % cid))
        else:
            ids.add(cid)
            seen.append(cid)
        for key in ("name", "responsibility", "location"):
            if not str(c.get(key) or "").strip():
                vio.append(v("EMPTY_FIELD", where + "." + key, "为空"))
        if c.get("layer") not in LAYERS:
            vio.append(v("ENUM_INVALID", where + ".layer",
                         "取值非法：%r（合法集 %s）" % (c.get("layer"), "|".join(LAYERS))))
        if c.get("status") and c.get("status") not in COMPONENT_STATUS:
            vio.append(v("ENUM_INVALID", where + ".status",
                         "取值非法：%r（合法集 %s）"
                         % (c.get("status"), "|".join(COMPONENT_STATUS))))
    expect = ["AN-%02d" % (n + 1) for n in range(len(seen))]
    if seen != expect:
        vio.append(v("SET_MISMATCH", "components[].id",
                     "ID 顺序断裂：实得 %s，应为 %s（顺序递增、不重编不复用）"
                     % (seen, expect)))

    for i, f in enumerate(doc.get("data_flow") or []):
        where = "data_flow[%d]" % i
        if not str(f.get("name") or "").strip() or not (f.get("steps") or []):
            vio.append(v("EMPTY_FIELD", where, "名称与步骤都不得为空"))
        for ref in f.get("components") or []:
            if ref not in ids:
                vio.append(v("UNKNOWN_ID", where + ".components",
                             "%s 不在 components[] 中" % ref))

    for i, d in enumerate(doc.get("dependencies") or []):
        where = "dependencies[%d]" % i
        for key in ("from", "to"):
            ref = d.get(key)
            if not str(ref or "").strip():
                vio.append(v("EMPTY_FIELD", where + "." + key, "为空"))
            elif str(ref).startswith("AN-") and ref not in ids:
                vio.append(v("UNKNOWN_ID", where + "." + key,
                             "%s 不在 components[] 中" % ref))

    for i, r in enumerate(doc.get("risks") or []):
        where = "risks[%d]" % i
        for key in ("risk", "location", "impact"):
            if not str(r.get(key) or "").strip():
                vio.append(v("EMPTY_FIELD", where + "." + key, "为空"))
        if r.get("severity") not in SCALES:
            vio.append(v("ENUM_INVALID", where + ".severity",
                         "取值非法：%r（合法集 %s）" % (r.get("severity"), "|".join(SCALES))))

    ranks = []
    for i, r in enumerate(doc.get("recommendations") or []):
        where = "recommendations[%d]" % i
        if not str(r.get("action") or "").strip():
            vio.append(v("EMPTY_FIELD", where + ".action", "为空"))
        pri = r.get("priority")
        if pri not in SCALES:
            vio.append(v("ENUM_INVALID", where + ".priority",
                         "取值非法：%r（合法集 %s）" % (pri, "|".join(SCALES))))
        else:
            ranks.append(SCALES.index(pri))
    if ranks != sorted(ranks):
        vio.append(v("SET_MISMATCH", "recommendations[].priority",
                     "建议未按优先级排序：实得 %s（高 → 中 → 低）" % ranks))

    if args.final:
        if status != "已定稿":
            vio.append(v("STATUS_MISMATCH", "project.status",
                         "定稿门要求 已定稿，实得 %r" % status))
        for path, text in walk_strings(doc, "analysis"):
            if ASSUMPTION in text:
                vio.append(v("ASSUMPTION_PRESENT", path,
                             "定稿门要求零 %s：%s" % (ASSUMPTION, text[:60])))
        for key in ("components", "data_flow", "risks", "recommendations"):
            if not doc.get(key):
                vio.append(v("EMPTY_FIELD", key, "定稿门要求非空"))
        if not (arch.get("tech_stack") or []):
            vio.append(v("EMPTY_FIELD", "architecture.tech_stack", "定稿门要求非空"))
        if not mermaid:
            vio.append(v("EMPTY_FIELD", "architecture.mermaid", "定稿门要求非空"))

    counts = {"components": len(components),
              "data_flow": len(doc.get("data_flow") or []),
              "dependencies": len(doc.get("dependencies") or []),
              "risks": len(doc.get("risks") or []),
              "recommendations": len(doc.get("recommendations") or [])}
    return emit(receipt("check", not vio, args.project_root, out_dir, vio,
                        counts=counts), args.json)
