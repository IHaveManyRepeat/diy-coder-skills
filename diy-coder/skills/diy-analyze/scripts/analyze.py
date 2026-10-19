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
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import args_output_dir, load_yaml_safe, now, save_yaml_atomic, v  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze_check import COMPONENT_STATUS, cmd_check, emit, read_product, receipt  # noqa: E402

# ---- init ------------------------------------------------------------------

def skeleton(name, question, scope, output_format, time_box, codebase):
    stamp = now()
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
    out_dir = args_output_dir(args)
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
        old, err = load_yaml_safe(path)
        if err:
            violations.append(v("UNPARSABLE_YAML", "analysis.yaml",
                                "既有产物解析失败：%s" % err))
        elif violations:
            pass  # 前面已有违规：一并回，零写入
        else:
            warnings.append(v("ALREADY_EXISTS", "analysis.yaml",
                              "既有产物在场：不覆盖，只刷 project.updated"
                              "（要改内容就地编辑，改既有条目往 revisions 追加）"))
            old.setdefault("project", {})["updated"] = now()
            save_yaml_atomic(path, old)
            return emit(receipt("init", True, args.project_root, out_dir,
                                warnings=warnings,
                                counts={"components": len(old.get("components") or [])},
                                updated=now()), args.json)
    if violations:
        return emit(receipt("init", False, args.project_root, out_dir,
                            violations), args.json)
    doc = skeleton(os.path.basename(os.path.abspath(args.project_root)),
                   args.question.strip(), args.scope or "", args.output_format or "",
                   args.time_box or "", codebase)
    save_yaml_atomic(path, doc)
    return emit(receipt("init", True, args.project_root, out_dir,
                        counts={"components": 0, "risks": 0, "recommendations": 0},
                        updated=now()), args.json)

# ---- list / show -----------------------------------------------------------

def cmd_list(args):
    doc, bad = read_product(args, "list")
    if bad:
        return emit(bad, args.json)
    if args.status and args.status not in COMPONENT_STATUS:
        return emit(receipt("list", False, args.project_root,
                            args_output_dir(args),
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
    return emit(receipt("list", True, args.project_root, args_output_dir(args),
                        counts={"components": len(items)}, items=items), args.json,
                human_lines=["组件 %d 条：" % len(items)] + [
                    "%s %s [%s] %s" % (i["id"], i["name"], i["layer"],
                                       i["responsibility"]) for i in items])

def cmd_show(args):
    doc, bad = read_product(args, "show")
    if bad:
        return emit(bad, args.json)
    out_dir = args_output_dir(args)
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
