# -*- coding: utf-8 -*-
"""diy-reverse 确定性引擎：外部目标逆向产物的初始生成与机械核对。

子命令：
  init   铸 `{output_dir}/design.yaml` **骨架**（唯一写盘）；门禁 = 外部目标可访问
         **只在初始生成时写**——`design.yaml` 已存在（可解析或损坏）一律拒绝覆盖
  list   页清单六字段（id / name / route / states / prototype / status）+ token 计数
  show   单页（`--id P-n`）/ 整份摘要
  check  既有 design.yaml schema 三道（direction+frontend_framework / tokens 三段 /
         pages 四态与原型在场）+ 页 ID 纪律与模块名禁用 + `--final` 定稿门
  tokens 「不抄像素」判据的机械面：按出现次数分流——**重复值（≥2）可作 token，
         单次值一律不得作 token**（对齐 `design.py audit` 的 `one-off-*` 口径）

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
import datetime
import io
import json
import os
import re
import sys

import yaml

REQUIRED_STATES = ("悬停", "空态", "加载中", "错误")
COLOR_REQUIRED = ("bg", "text", "accent")
COLOR_ALL = ("bg", "surface", "text", "text_muted", "accent", "accent_text")
STATUSES = ("草稿", "已定稿")
TRACKS = ("url", "screenshots")
ID_RE = re.compile(r"^P-\d+$")
HEX_RE = re.compile(r"^#[0-9a-fA-F]{3,8}$")
URL_RE = re.compile(r"^https?://[^\s/]+")
ASSUMPTION = "[假设]"
SIGNAL_COLOR = "色彩"


def today():
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


def design_path(args):
    return os.path.join(resolve_output_dir(args), "design.yaml")


def read_design(args, command):
    path = design_path(args)
    if not os.path.isfile(path):
        return None, None, receipt(command, False, args.project_root,
                                   resolve_output_dir(args), [
            v("MISSING_FILE", "design.yaml",
              "%s 不存在——先跑 init 做初始生成（既有 design.yaml 由 diy-design 演进）"
              % path)])
    doc, err = safe_load_yaml(path)
    if err:
        return None, path, receipt(command, False, args.project_root,
                                   resolve_output_dir(args), [
            v("UNPARSABLE_YAML", "design.yaml", "解析失败：%s" % err)])
    return doc, path, None


# ---- init ------------------------------------------------------------------

def skeleton(name):
    stamp = today()
    return {
        "project": {"name": name, "created": stamp, "updated": stamp,
                    "status": "草稿"},
        "direction": "",
        "frontend_framework": "",
        "tokens": {
            "color": {k: "" for k in COLOR_ALL},
            "spacing": {"unit": "", "scale": []},
            "typography": {"family_base": "", "family_heading": "", "scale": []},
        },
        "pages": [],
        "revisions": [],
    }


def cmd_init(args):
    out_dir = resolve_output_dir(args)
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
                                "截图路径不存在或不可读：%r（门禁 = 外部目标可访问）"
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
                        counts={"pages": 0}, updated=today()), args.json)


# ---- list / show -----------------------------------------------------------

def cmd_list(args):
    doc, _, bad = read_design(args, "list")
    if bad:
        return emit(bad, args.json)
    out_dir = resolve_output_dir(args)
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
    out_dir = resolve_output_dir(args)
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


# ---- check -----------------------------------------------------------------

def _walk_strings(node, path="design"):
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


def cmd_check(args):
    doc, path, bad = read_design(args, "check")
    out_dir = resolve_output_dir(args)
    if bad:
        return emit(bad, args.json)
    base = os.path.dirname(os.path.abspath(path))
    vio = []

    project = doc.get("project") or {}
    status = project.get("status")
    if status not in STATUSES:
        vio.append(v("ENUM_INVALID", "project.status",
                     "取值非法：%r（合法集 %s）" % (status, "|".join(STATUSES))))

    # 第一道：direction + frontend_framework（design.py validate 同判据）
    if not str(doc.get("direction") or "").strip():
        vio.append(v("EMPTY_FIELD", "direction",
                     "为空——具名方向 + 一行理由 + 2–3 条反模式禁令"))
    if not str(doc.get("frontend_framework") or "").strip():
        vio.append(v("EMPTY_FIELD", "frontend_framework",
                     "为空——取值路径见 diy-design SKILL 的 B9 条；纯 HTML 项目写 html"))

    # 第二道：tokens 三段必填键 + 色值形态
    tokens = doc.get("tokens") or {}
    color = tokens.get("color") or {}
    for key in COLOR_REQUIRED:
        if not str(color.get(key) or "").strip():
            vio.append(v("EMPTY_FIELD", "tokens.color.%s" % key, "为空"))
    for key, val in color.items():
        if str(val or "").strip() and not HEX_RE.match(str(val).strip()):
            vio.append(v("ENUM_INVALID", "tokens.color.%s" % key,
                         "不是合法 hex 色值：%r" % val))
    spacing = tokens.get("spacing") or {}
    if not str(spacing.get("unit") or "").strip():
        vio.append(v("EMPTY_FIELD", "tokens.spacing.unit", "为空——须给基准单位"))
    if not (spacing.get("scale") or []):
        vio.append(v("EMPTY_FIELD", "tokens.spacing.scale", "为空"))
    typo = tokens.get("typography") or {}
    if not str(typo.get("family_base") or "").strip():
        vio.append(v("EMPTY_FIELD", "tokens.typography.family_base", "为空"))
    if not (typo.get("scale") or []):
        vio.append(v("EMPTY_FIELD", "tokens.typography.scale", "为空"))

    # 第三道：pages 非空 + 四态齐 + 原型在场 + ID 纪律与原型同源
    pages = doc.get("pages") or []
    if not pages:
        vio.append(v("EMPTY_FIELD", "pages", "为空——逆向至少要落一页规格"))
    seen, ids = [], set()
    for i, page in enumerate(pages):
        where = "pages[%d]" % i
        pid = page.get("id")
        if not ID_RE.match(str(pid or "")):
            vio.append(v("ENUM_INVALID", where + ".id",
                         "ID 形态非法：%r（既有 schema 为 P-<n> 顺序铸号；"
                         "不得用 WDS 线的记录 ID 形态）" % pid))
        elif pid in ids:
            vio.append(v("DUPLICATE_ID", where + ".id", "%s 重复" % pid))
        else:
            ids.add(pid)
            seen.append(pid)
        for key in ("name", "route"):
            if not str(page.get(key) or "").strip():
                vio.append(v("EMPTY_FIELD", where + "." + key, "为空"))
        names = [s.get("name") for s in page.get("states") or []]
        missing = [s for s in REQUIRED_STATES if s not in names]
        if missing:
            vio.append(v("EMPTY_FIELD", where + ".states",
                         "缺交互状态 %s——四态不许省（不适用也给最小真实信号并注明）"
                         % "/".join(missing)))
        for j, st in enumerate(page.get("states") or []):
            signals = [s for s in (st.get("signals") or []) if s != SIGNAL_COLOR]
            if not signals:
                vio.append(v("ENUM_INVALID", "%s.states[%d].signals" % (where, j),
                             "仅有色彩信号，须补图标/文字/形状/动效等非色彩信号"))
        proto = page.get("prototype")
        if not str(proto or "").strip():
            vio.append(v("MISSING_FILE", where + ".prototype",
                         "为空——结构稿必须在场（既有 schema 的 validate 三道之一）"))
        else:
            if os.path.splitext(os.path.basename(str(proto)))[0] != str(pid):
                vio.append(v("SET_MISMATCH", where + ".prototype",
                             "原型文件名与页 ID 不同源：%s ↔ %s" % (proto, pid)))
            if not os.path.isfile(os.path.join(base, str(proto))):
                vio.append(v("MISSING_FILE", where + ".prototype",
                             "结构稿缺失：%s（不抄像素：画出**你**的结构稿，"
                             "不复制目标页面的代码与资产）" % proto))
        impl = page.get("implementation")
        if impl and not os.path.isfile(os.path.join(base, str(impl))):
            vio.append(v("MISSING_FILE", where + ".implementation",
                         "实现稿声明了但不存在：%s（纯 HTML 项目省略该键）" % impl))
    expect = ["P-%d" % (n + 1) for n in range(len(seen))]
    if seen != expect:
        vio.append(v("SET_MISMATCH", "pages[].id",
                     "ID 顺序断裂：实得 %s，应为 %s（顺序铸号、不重编不复用）"
                     % (seen, expect)))

    if args.final:
        if status != "已定稿":
            vio.append(v("STATUS_MISMATCH", "project.status",
                         "定稿门要求 已定稿，实得 %r" % status))
        for where, text in _walk_strings(doc):
            if ASSUMPTION in text:
                vio.append(v("ASSUMPTION_PRESENT", where,
                             "定稿门要求零 %s：%s" % (ASSUMPTION, text[:60])))

    counts = {"pages": len(pages),
              "colors": len([x for x in color.values() if x]),
              "spacing_steps": len(spacing.get("scale") or []),
              "type_steps": len(typo.get("scale") or [])}
    return emit(receipt("check", not vio, args.project_root, out_dir, vio,
                        counts=counts), args.json)


# ---- tokens（「不抄像素」判据的机械面） -------------------------------------

def cmd_tokens(args):
    out_dir = resolve_output_dir(args)
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
