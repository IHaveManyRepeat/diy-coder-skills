# -*- coding: utf-8 -*-
"""diy-analyze 确定性引擎：代码库分析的骨架铸造与机械核对。

子命令：
  init   铸 `{output_dir}/analysis.yaml` 骨架（**唯一写盘**）；门禁 = 代码库可读
  list   组件六字段清单（id / name / layer / responsibility / location / status），不读正文
  show   单条组件（`--id AN-nn`）/ 整份摘要
  check  骨架完备 + 枚举合法 + ID 纪律；`--final` 另核「已定稿 + 零 `[假设]` + 四段非空」

违规码：**复用 batch3-contract §3 冻结集**——`MISSING_FILE` / `UNPARSABLE_YAML` /
`EMPTY_FIELD` / `ENUM_INVALID` / `DUPLICATE_ID` / `UNKNOWN_ID` / `SET_MISMATCH` /
`STATUS_MISMATCH` / `ASSUMPTION_PRESENT`；**本技能零新增违规码**。
  - `MISSING_FILE` 承载门禁（代码库路径不存在 / 不是目录 / 不可读——统一按「前置物不可用」判）
  - `ENUM_INVALID` 兼作 mermaid 图纸类型非法、layer / severity / priority 越界
  - `SET_MISMATCH` 兼作 `AN-<nn>` 跳号与建议优先级逆序

`warnings` 用**描述性码**（非违规码，不进冻结集）：`ALREADY_EXISTS`。

实例解析由 SKILL.md 层完成（`diyc.py resolve`）；本引擎只吃 `--output-dir`，
不解析实例（对齐 §2.2「`--instance` 一律不做」）。
"""
import argparse
import io
import json
import os
import re
import sys

import yaml

LAYERS = ("展示层", "应用层", "领域层", "基础设施层", "未分层")
SCALES = ("高", "中", "低")
STATUSES = ("草稿", "已定稿")
COMPONENT_STATUS = ("已核实", "待核实")
ID_RE = re.compile(r"^AN-\d{2}$")
MERMAID_HEADS = ("graph", "flowchart", "sequenceDiagram", "classDiagram",
                 "stateDiagram", "erDiagram", "journey", "gantt", "pie")
ASSUMPTION = "[假设]"

SUBCOMMANDS = ("init", "list", "show", "check")


def today():
    import datetime
    return datetime.date.today().isoformat()


def load_yaml(path):
    with io.open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def safe_load_yaml(path):
    try:
        return load_yaml(path), None
    except yaml.YAMLError as e:
        return None, str(e)


def save_yaml_atomic(path, data):
    """同目录临时文件 + os.replace 原子替换（对齐 diyc_lib.save_yaml_atomic 先例）。"""
    folder = os.path.dirname(os.path.abspath(path))
    if folder and not os.path.isdir(folder):
        os.makedirs(folder, exist_ok=True)
    tmp = path + ".tmp"
    with io.open(tmp, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False,
                       default_flow_style=False)
    os.replace(tmp, path)


def v(code, where, msg):
    return {"code": code, "where": where, "msg": msg}


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


def resolve_output_dir(args):
    """回执里的 output_dir 统一正斜杠（对齐 batch3-contract §3 的 where 口径）。"""
    raw = args.output_dir or os.path.join(args.project_root, "diy-output")
    return os.path.normpath(raw).replace(os.sep, "/")


def read_product(args, command):
    """读产物；返回 (doc, result 或 None)。违规即回执。"""
    out_dir = resolve_output_dir(args)
    path = os.path.join(out_dir, "analysis.yaml")
    if not os.path.isfile(path):
        return None, receipt(command, False, args.project_root, out_dir, [
            v("MISSING_FILE", "analysis.yaml",
              "%s 不存在——先跑 init 铸骨架（路由：确认分析问题与代码库路径）" % path)])
    doc, err = safe_load_yaml(path)
    if err:
        return None, receipt(command, False, args.project_root, out_dir, [
            v("UNPARSABLE_YAML", "analysis.yaml", "解析失败：%s" % err)])
    return doc, None


# ---- init ------------------------------------------------------------------

def skeleton(name, question, scope, output_format, time_box, codebase):
    stamp = today()
    return {
        "project": {"name": name, "created": stamp, "updated": stamp,
                    "status": "草稿"},
        "question": {"text": question, "scope": scope,
                     "output_format": output_format, "time_box": time_box,
                     "codebase": codebase},
        "architecture": {"summary": "", "tech_stack": [], "overview": "",
                         "mermaid": "", "patterns": [], "layers": []},
        "components": [],
        "data_flow": [],
        "dependencies": [],
        "risks": [],
        "recommendations": [],
        "revisions": [],
    }


def cmd_init(args):
    out_dir = resolve_output_dir(args)
    violations, warnings = [], []
    codebase = args.codebase or args.project_root
    if not os.path.isdir(codebase) or not os.access(codebase, os.R_OK):
        violations.append(v("MISSING_FILE", "codebase",
                            "代码库目录不存在或不可读：%s（门禁 = 代码库可读；零产出停止）"
                            % codebase))
    if not str(args.question or "").strip():
        violations.append(v("EMPTY_FIELD", "question.text",
                            "分析问题为空——先成文再动手（源 step-01 第 1 指令）"))
    path = os.path.join(out_dir, "analysis.yaml")
    if os.path.isfile(path):
        old, err = safe_load_yaml(path)
        if err:
            violations.append(v("UNPARSABLE_YAML", "analysis.yaml",
                                "既有产物解析失败：%s" % err))
        elif violations:
            pass  # 前面已有违规：一并回，零写入
        else:
            warnings.append(v("ALREADY_EXISTS", "analysis.yaml",
                              "既有产物在场：不覆盖，只刷 project.updated"
                              "（要改内容就地编辑，改既有条目往 revisions 追加）"))
            old.setdefault("project", {})["updated"] = today()
            save_yaml_atomic(path, old)
            return emit(receipt("init", True, args.project_root, out_dir,
                                warnings=warnings,
                                counts={"components": len(old.get("components") or [])},
                                updated=today()), args.json)
    if violations:
        return emit(receipt("init", False, args.project_root, out_dir,
                            violations), args.json)
    doc = skeleton(os.path.basename(os.path.abspath(args.project_root)),
                   args.question.strip(), args.scope or "", args.output_format or "",
                   args.time_box or "", codebase)
    save_yaml_atomic(path, doc)
    return emit(receipt("init", True, args.project_root, out_dir,
                        counts={"components": 0, "risks": 0, "recommendations": 0},
                        updated=today()), args.json)


# ---- list / show -----------------------------------------------------------

def cmd_list(args):
    doc, bad = read_product(args, "list")
    if bad:
        return emit(bad, args.json)
    if args.status and args.status not in COMPONENT_STATUS:
        return emit(receipt("list", False, args.project_root,
                            resolve_output_dir(args),
                            [v("ENUM_INVALID", "--status", "取值非法：%s（合法集 %s）"
                               % (args.status, "|".join(COMPONENT_STATUS)))]),
                    args.json)
    items = []
    for c in doc.get("components") or []:
        item = {"id": c.get("id"), "name": c.get("name"), "layer": c.get("layer"),
                "responsibility": c.get("responsibility"),
                "location": c.get("location"),
                "status": c.get("status") or COMPONENT_STATUS[0]}
        if args.status and item["status"] != args.status:
            continue
        items.append(item)
    return emit(receipt("list", True, args.project_root, resolve_output_dir(args),
                        counts={"components": len(items)}, items=items), args.json,
                human_lines=["组件 %d 条：" % len(items)] + [
                    "%s %s [%s] %s" % (i["id"], i["name"], i["layer"],
                                       i["responsibility"]) for i in items])


def cmd_show(args):
    doc, bad = read_product(args, "show")
    if bad:
        return emit(bad, args.json)
    out_dir = resolve_output_dir(args)
    if not args.id:
        arch = doc.get("architecture") or {}
        lines = ["问题：%s" % (doc.get("question") or {}).get("text", ""),
                 "摘要：%s" % arch.get("summary", ""),
                 "计数：组件 %d / 数据流 %d / 依赖 %d / 风险 %d / 建议 %d"
                 % (len(doc.get("components") or []), len(doc.get("data_flow") or []),
                    len(doc.get("dependencies") or []), len(doc.get("risks") or []),
                    len(doc.get("recommendations") or []))]
        return emit(receipt("show", True, args.project_root, out_dir,
                            counts={"components": len(doc.get("components") or [])}),
                    args.json, human_lines=lines)
    for c in doc.get("components") or []:
        if c.get("id") == args.id:
            return emit(receipt("show", True, args.project_root, out_dir,
                                counts={"components": 1}, component=c), args.json,
                        human_lines=["%s %s" % (c.get("id"), c.get("name")),
                                     "职责：%s" % c.get("responsibility", ""),
                                     "位置：%s" % c.get("location", "")])
    return emit(receipt("show", False, args.project_root, out_dir, [
        v("UNKNOWN_ID", "components", "%s 不存在" % args.id)]), args.json)


# ---- check -----------------------------------------------------------------

def _texts(node):
    """递归取全部字符串（键与值都算）——`[假设]` 全扫口径。"""
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for k, val in node.items():
            yield str(k)
            for t in _texts(val):
                yield t
    elif isinstance(node, list):
        for item in node:
            for t in _texts(item):
                yield t


def cmd_check(args):
    doc, bad = read_product(args, "check")
    out_dir = resolve_output_dir(args)
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
                         "为空——源 step-01 的四项定义不得省"))

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
        for path, text in _walk_strings(doc):
            if ASSUMPTION in text:
                vio.append(v("ASSUMPTION_PRESENT", path,
                             "定稿门要求零 %s：%s" % (ASSUMPTION, text[:60])))
        for key in ("components", "data_flow", "risks", "recommendations"):
            if not doc.get(key):
                vio.append(v("EMPTY_FIELD", key, "定稿门要求非空"))
        if not (arch.get("tech_stack") or []):
            vio.append(v("EMPTY_FIELD", "architecture.tech_stack", "定稿门要求非空"))

    counts = {"components": len(components),
              "data_flow": len(doc.get("data_flow") or []),
              "dependencies": len(doc.get("dependencies") or []),
              "risks": len(doc.get("risks") or []),
              "recommendations": len(doc.get("recommendations") or [])}
    return emit(receipt("check", not vio, args.project_root, out_dir, vio,
                        counts=counts), args.json)


def _walk_strings(node, path="analysis"):
    if isinstance(node, str):
        yield path, node
    elif isinstance(node, dict):
        for k, val in node.items():
            for got in _walk_strings(val, "%s.%s" % (path, k)):
                yield got
    elif isinstance(node, list):
        for i, item in enumerate(node):
            for got in _walk_strings(item, "%s[%d]" % (path, i)):
                yield got


# ---- CLI -------------------------------------------------------------------

def build_parser():
    parser = argparse.ArgumentParser(
        prog="analyze.py", description="diy-analyze 领域引擎（analysis.yaml 铸造与核对）")
    sub = parser.add_subparsers(dest="command", required=True)

    def common(p, need_out=False):
        p.add_argument("--project-root", default=".")
        p.add_argument("--output-dir", required=need_out)
        p.add_argument("--json", action="store_true")

    p_init = sub.add_parser("init", help="铸 analysis.yaml 骨架（唯一写盘）")
    common(p_init, need_out=True)
    p_init.add_argument("--question", required=True, help="分析问题（源 step-01 第 1 指令）")
    p_init.add_argument("--scope", default="", help="范围边界")
    p_init.add_argument("--output-format", default="", help="期望产出形制")
    p_init.add_argument("--time-box", default="", help="时间盒")
    p_init.add_argument("--codebase", default=None, help="被分析的代码库路径（默认 project-root）")
    p_init.set_defaults(func=cmd_init)

    p_list = sub.add_parser("list", help="组件六字段清单")
    common(p_list)
    p_list.add_argument("--status", default=None)
    p_list.set_defaults(func=cmd_list)

    p_show = sub.add_parser("show", help="单条组件 / 整份摘要")
    common(p_show)
    p_show.add_argument("--id", default=None)
    p_show.set_defaults(func=cmd_show)

    p_check = sub.add_parser("check", help="骨架与 ID 纪律核对（--final 为终门）")
    common(p_check)
    p_check.add_argument("--final", action="store_true")
    p_check.set_defaults(func=cmd_check)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
