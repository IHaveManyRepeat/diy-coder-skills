# -*- coding: utf-8 -*-
"""diy-reverse 校验域：形态/颜色/状态常量、回执与 design 读取助手、check 校验编排（entry 反向 import 本件 helpers）。."""

import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import args_output_dir, load_yaml_safe, v, walk_strings  # noqa: E402

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

def design_path(args):
    return os.path.join(args_output_dir(args), "design.yaml")

def read_design(args, command):
    path = design_path(args)
    if not os.path.isfile(path):
        return None, None, receipt(command, False, args.project_root,
                                   args_output_dir(args), [
            v("MISSING_FILE", "design.yaml",
              "%s 不存在——先跑 init 做初始生成（既有 design.yaml 由 diy-design 演进）"
              % path)])
    doc, err = load_yaml_safe(path)
    if err:
        return None, path, receipt(command, False, args.project_root,
                                   args_output_dir(args), [
            v("UNPARSABLE_YAML", "design.yaml", "解析失败：%s" % err)])
    return doc, path, None

# ---- check -----------------------------------------------------------------

def cmd_check(args):
    doc, path, bad = read_design(args, "check")
    out_dir = args_output_dir(args)
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
        for where, text in walk_strings(doc, "design"):
            if ASSUMPTION in text:
                vio.append(v("ASSUMPTION_PRESENT", where,
                             "定稿门要求零 %s：%s" % (ASSUMPTION, text[:60])))

    counts = {"pages": len(pages),
              "colors": len([x for x in color.values() if x]),
              "spacing_steps": len(spacing.get("scale") or []),
              "type_steps": len(typo.get("scale") or [])}
    return emit(receipt("check", not vio, args.project_root, out_dir, vio,
                        counts=counts), args.json)
