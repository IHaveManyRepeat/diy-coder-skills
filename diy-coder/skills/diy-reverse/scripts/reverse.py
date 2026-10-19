# -*- coding: utf-8 -*-
"""diy-reverse 确定性引擎：外部目标逆向产物的初始生成与机械核对。

子命令：
  init   铸 `{output_dir}/design.yaml` **骨架**（唯一写盘）；门禁 = 目标形态合法且（截图轨）路径在场可读
         **只在初始生成时写**——`design.yaml` 已存在（可解析或损坏）一律拒绝覆盖
  list   页清单六字段（id / name / route / states / prototype / status）+ token 计数
  show   单页（`--id P-n`）/ 整份摘要
  check  既有 design.yaml schema 三道（direction+frontend_framework / tokens 三段 /
         pages 四态与原型在场）+ 页 ID 纪律与模块名禁用 + `--final` 定稿门
  tokens 「不抄像素」判据的机械面：按出现次数分流——**重复值（≥2）可作 token，
         单次值一律不得作 token**（对齐 `design.py audit` 的 `one-off-*` 口径）

★ **第五子命令 `tokens` 是本批对 §2.2「四子命令」的一处登记性偏离**（W4 回报必答 ④ 已列）：
  §2.2 冻结「`init` / `list` / `show` / `check` 四子命令」，而裁定 13 要求把「不抄像素」判据
  落成机械面（**允许重复值作 token、禁止单次值**，复用套件 `one-off-*` 口径）——两条并存的
  最小满足 = 在四子命令之外加一个**只读、零写盘**的第五子命令。先例：`diy-wds-system` 的
  `similarity`（本批）与 B7a `diy-wds-trigger` 的 `metrics` 亦为同款登记项。**不写盘**。

违规码：复用 batch3-contract §3 冻结集——`MISSING_FILE` / `UNPARSABLE_YAML` /
`EMPTY_FIELD` / `ENUM_INVALID` / `DUPLICATE_ID` / `UNKNOWN_ID` / `SET_MISMATCH` /
`STATUS_MISMATCH` / `ASSUMPTION_PRESENT` + **本技能新增 2 个**（裁定 13 的写权边界，
需新码故在 docstring 标注并单独列出）：
  - **`TARGET_UNREACHABLE`**（新）：外部目标不可访问——URL 形态非 http(s) / 截图路径
    不存在或不可读。门禁不满足即零产出。
  - **`OVERWRITE_REFUSED`**（新）：`design.yaml` 已存在，拒绝覆盖（生成权归本技能、
    演进权归 `diy-design`）。零写入，路由 `diy-design`。
`warnings` 用**描述性码**（非违规码）：`ONE_OFF_VALUE`（单次值，不得作 token）。

`check` 是**本技能自带引擎的终门**；既有 `design.py validate` / `check` 是设计域
schema 与易用性权威，作为**交叉核对**另行跑一次（两者都必须 exit 0）。
实例解析由 SKILL.md 层完成（`diyc.py resolve`）；本引擎不解析实例。
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import args_output_dir, now, save_yaml_atomic, v  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reverse_check import COLOR_ALL, TRACKS, URL_RE, cmd_check, design_path, emit, read_design, receipt  # noqa: E402

# ---- init ------------------------------------------------------------------

def skeleton(name):
    stamp = now()
    return {
        "project": {"name": name, "created": stamp, "updated": stamp,
                    "status": "草稿"},
        "direction": "",
        "frontend_framework": "",
        # C·15（清偿 C·12 欠账）：两键空串——逆向形态 init 时未知不预设默认值；
        # design.py:747/:754 空串≡缺失同码，键位拓扑同 tokens_doc()
        "form_factor": "",
        "modes": "",
        "tokens": {
            "color": {k: "" for k in COLOR_ALL},
            "spacing": {"unit": "", "scale": []},
            "typography": {"family_base": "", "family_heading": "", "scale": []},
        },
        "pages": [],
        "revisions": [],
    }

def cmd_init(args):
    out_dir = args_output_dir(args)
    violations = []
    if args.track not in TRACKS:
        violations.append(v("ENUM_INVALID", "--track",
                            "取值非法：%r（裁定 11 只留 External 两轨：%s）"
                            % (args.track, "|".join(TRACKS))))
    elif args.track == "url":
        if not URL_RE.match(str(args.target or "").strip()):
            violations.append(v("TARGET_UNREACHABLE", "--target",
                                "URL 形态非法：%r（须 http:// 或 https:// 开头的公开目标）"
                                % args.target))
    else:
        target = str(args.target or "").strip()
        if not target or not os.path.exists(target) or not os.access(target, os.R_OK):
            violations.append(v("TARGET_UNREACHABLE", "--target",
                                "截图路径不存在或不可读：%r（门禁 = 形态与在场；真实可达性由会话确认）"
                                % args.target))
    path = design_path(args)
    if os.path.isfile(path):
        violations.append(v("OVERWRITE_REFUSED", "design.yaml",
                            "已存在，拒绝覆盖：本技能只在**初始生成**时写 "
                            "design.yaml（裁定 13）；改走 diy-design 的 Update，"
                            "差异写成 revisions 建议并路由 diy-design"))
    if violations:
        return emit(receipt("init", False, args.project_root, out_dir, violations),
                    args.json)
    save_yaml_atomic(path, skeleton(os.path.basename(os.path.abspath(
        args.project_root))))
    return emit(receipt("init", True, args.project_root, out_dir,
                        counts={"pages": 0}, updated=now()), args.json)

# ---- list / show -----------------------------------------------------------

def cmd_list(args):
    doc, _, bad = read_design(args, "list")
    if bad:
        return emit(bad, args.json)
    out_dir = args_output_dir(args)
    items = []
    for page in doc.get("pages") or []:
        states = [s.get("name") for s in page.get("states") or []]
        items.append({"id": page.get("id"), "name": page.get("name"),
                      "route": page.get("route"), "states": states,
                      "prototype": page.get("prototype"),
                      "status": (doc.get("project") or {}).get("status")})
    tokens = doc.get("tokens") or {}
    color = tokens.get("color") or {}
    counts = {"pages": len(items),
              "colors": len([k for k, val in color.items() if val]),
              "spacing_steps": len((tokens.get("spacing") or {}).get("scale") or []),
              "type_steps": len((tokens.get("typography") or {}).get("scale") or [])}
    return emit(receipt("list", True, args.project_root, out_dir, counts=counts,
                        items=items), args.json,
                human_lines=["页 %d 条：" % len(items)] + [
                    "%s %s (%s) 四态 %d" % (i["id"], i["name"], i["route"],
                                            len(i["states"])) for i in items])

def cmd_show(args):
    doc, _, bad = read_design(args, "show")
    if bad:
        return emit(bad, args.json)
    out_dir = args_output_dir(args)
    if not args.id:
        tokens = doc.get("tokens") or {}
        lines = ["方向：%s" % str(doc.get("direction") or "").splitlines()[:1],
                 "框架：%s" % doc.get("frontend_framework", ""),
                 "token：色 %d / 间距 %d / 字号 %d，页 %d"
                 % (len([x for x in (tokens.get("color") or {}).values() if x]),
                    len((tokens.get("spacing") or {}).get("scale") or []),
                    len((tokens.get("typography") or {}).get("scale") or []),
                    len(doc.get("pages") or []))]
        return emit(receipt("show", True, args.project_root, out_dir,
                            counts={"pages": len(doc.get("pages") or [])}),
                    args.json, human_lines=lines)
    for page in doc.get("pages") or []:
        if page.get("id") == args.id:
            return emit(receipt("show", True, args.project_root, out_dir,
                                counts={"pages": 1}, page=page), args.json,
                        human_lines=["%s %s (%s)" % (page.get("id"),
                                                     page.get("name"),
                                                     page.get("route"))])
    return emit(receipt("show", False, args.project_root, out_dir, [
        v("UNKNOWN_ID", "pages", "%s 不存在" % args.id)]), args.json)

# ---- tokens（「不抄像素」判据的机械面） -------------------------------------

def cmd_tokens(args):
    out_dir = args_output_dir(args)
    raw = [x.strip() for x in str(args.values or "").split(",")]
    values = [x for x in raw if x]
    if not values:
        return emit(receipt("tokens", False, args.project_root, out_dir, [
            v("EMPTY_FIELD", "--values",
              "无有效值——给逗号分隔的候选值（色值 / 字号 / 间距）")]), args.json)
    order, counts = [], {}
    for val in values:
        if val not in counts:
            order.append(val)
            counts[val] = 0
        counts[val] += 1
    keep = [x for x in order if counts[x] >= args.min]
    drop = [x for x in order if counts[x] < args.min]
    warnings = [v("ONE_OFF_VALUE", "tokens",
                  "%s 只出现 %d 次（< %d）——单次值不得作 token，"
                  "它与 design.py audit 的 one-off-* 判据同口径" %
                  (x, counts[x], args.min)) for x in drop]
    result = receipt("tokens", True, args.project_root, out_dir,
                     warnings=warnings,
                     counts={"values": len(values), "repeat": len(keep),
                             "one_off": len(drop), "min": args.min,
                             "tokens": keep, "dropped": drop})
    return emit(result, args.json,
                human_lines=["可作 token（重复出现）：%s" % "，".join(keep),
                             "剔除（单次值）：%s" % ("，".join(drop) or "无")])

# ---- CLI -------------------------------------------------------------------

def build_parser():
    parser = argparse.ArgumentParser(
        prog="reverse.py",
        description="diy-reverse 领域引擎（design.yaml 初始生成与逆向纪律核对）")
    sub = parser.add_subparsers(dest="command", required=True)

    def common(p, need_out=False):
        p.add_argument("--project-root", default=".")
        p.add_argument("--output-dir", required=need_out)
        p.add_argument("--json", action="store_true")

    p_init = sub.add_parser("init", help="铸 design.yaml 骨架（唯一写盘；已存在即拒绝）")
    common(p_init, need_out=True)
    p_init.add_argument("--track", required=True, help="url | screenshots（裁定 11）")
    p_init.add_argument("--target", required=True, help="外部目标 URL 或截图路径")
    p_init.set_defaults(func=cmd_init)

    p_list = sub.add_parser("list", help="页清单六字段 + token 计数")
    common(p_list)
    p_list.set_defaults(func=cmd_list)

    p_show = sub.add_parser("show", help="单页 / 整份摘要")
    common(p_show)
    p_show.add_argument("--id", default=None)
    p_show.set_defaults(func=cmd_show)

    p_check = sub.add_parser("check", help="schema 三道 + ID 纪律（--final 为终门）")
    common(p_check)
    p_check.add_argument("--final", action="store_true")
    p_check.set_defaults(func=cmd_check)

    p_tokens = sub.add_parser("tokens", help="重复值 / 单次值分流（不抄像素判据）")
    common(p_tokens)
    p_tokens.add_argument("--values", required=True, help="逗号分隔的候选值")
    p_tokens.add_argument("--min", type=int, default=2, help="作 token 的最低出现次数（默认 2）")
    p_tokens.set_defaults(func=cmd_tokens)
    return parser

def main(argv=None):
    args = build_parser().parse_args(argv)
    return args.func(args)

if __name__ == "__main__":
    sys.exit(main())
