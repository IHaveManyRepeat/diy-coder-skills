# -*- coding: utf-8 -*-
"""diy-design 共享层：回执/读取/ID/颜色原语/token 扫描与校验共享件。."""

import json
import os
import re
import sys
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import load_yaml, v, violation_line  # noqa: E402
# 双模的明暗对 = tokens.color.dark 子块六角色（亮基暗覆盖），判据见 dark_pair_violation
DARK_ROLES = ("bg", "surface", "text", "text_muted", "accent", "accent_text")

# ---- 页状态机：5 值收敛 + 9 条合法边 ----
PAGE_STATUSES = ("未开始", "结构稿中", "待验收", "已批准", "已移除")

# 无障碍：触控目标下限
TOUCH_TARGET_MIN = 44
# 触控下限按 form_factor 分档——桌面 24（WCAG 2.5.8 AA Target Size Minimum）；移动端 44；响应式 Web/多端 44
# （最严端——静态扫描不模拟媒体查询，双档并判等价按 44 判）；缺键/表外值 44（存量零漂移）
TOUCH_TARGET_MIN_DESKTOP = 24

NL = "\n"

# ---------------------------------------------------------------- 回执与违规

def receipt(command, ok, file=None, violations=None, warnings=None, counts=None, **extra):
    """回执基础构造：公共键在前、命令专有键在后（公共键一个不少、专有键一个不删）。"""
    r = {"ok": bool(ok), "command": command,
         "violations": list(violations or []), "warnings": list(warnings or []),
         "counts": dict(counts or {}), "file": file}
    r.update(extra)
    return r

def norm_path(path):
    """回执表示层统一正斜杠（机器消费面须单形分隔符）。"""
    return os.path.normpath(str(path)).replace("\\", "/")

def _summary(result):
    note = "，".join("%s=%s" % (k, val) for k, val in (result.get("counts") or {}).items())
    note = "（%s）" % note if note else ""
    if result.get("ok"):
        return "diy-design %s：通过%s" % (result.get("command"), note)
    return "diy-design %s：%d 项违规（exit 1）%s" % (
        result.get("command"), len(result.get("violations") or []), note)

def emit(result, as_json, human_lines=None):
    """打印回执并返回退出码（ok → 0 否则 1）。--json 面为单行 JSON。"""
    if as_json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        lines = list(human_lines or [])
        lines += [violation_line(x)
                  for x in result.get("violations") or []]
        lines += ["WARN %s" % w for w in result.get("warnings") or []]
        lines.append(_summary(result))
        print(NL.join(lines))
    return 0 if result.get("ok") else 1

# ---------------------------------------------------------------- 读取与形状归一

def coerce_design(doc):  # trace: S-14 AC-14.3 TC-14.3.3 形状归一：半写/畸形容器降级为空并记录问题
    """把未知形状归一为可安全遍历的结构；返回 (归一后文档, 问题清单)。

    归一结果只用于**读**（校验/审计/自检）；写回（transition）一律用原样文档，
    绝不 dump 归一结果——否则畸形容器会被静默改写成空容器（数据丢失）。
    """
    problems = []

    def take_map(value, path):
        if isinstance(value, dict):
            return value
        if value is not None:
            problems.append("%s 不是映射（%s），已按缺失处理" % (path, type(value).__name__))
        return {}

    def take_seq(value, path):
        if isinstance(value, list):
            return value
        if value is not None:
            problems.append("%s 不是列表（%s），已按空处理" % (path, type(value).__name__))
        return []

    doc = take_map(doc, "design.yaml 顶层")
    tokens = take_map(doc.get("tokens"), "tokens")
    for fam in ("color", "spacing", "typography"):
        tokens = {**tokens, fam: take_map(tokens.get(fam), "tokens." + fam)}
    typo = tokens["typography"]
    tokens = {**tokens, "typography": {**typo,
              "scale": take_seq(typo.get("scale"), "tokens.typography.scale")}}
    pages = []
    for i, page in enumerate(take_seq(doc.get("pages"), "pages")):
        path = "pages[%d]" % i
        page = take_map(page, path)
        states = []
        for j, st in enumerate(take_seq(page.get("states"), path + ".states")):
            spath = "%s.states[%d]" % (path, j)
            st = take_map(st, spath)
            states.append({**st,
                           "signals": take_seq(st.get("signals"), spath + ".signals")})
        pages.append({**page, "states": states})
    return {**doc, "tokens": tokens, "pages": pages,
            "token_scope": take_seq(doc.get("token_scope"), "token_scope"),
            "open_questions": take_seq(doc.get("open_questions"), "open_questions")}, problems

def load_design_doc(path):
    """原样载入 design.yaml；返回 (文档或 None, 违规清单)。不做任何形状归一。"""
    rel = norm_path(path)
    if not os.path.isfile(path):
        return None, [v("MISSING_FILE", rel, "%s 不存在——先运行 diy-design 生成该产物" % rel)]
    try:
        doc = load_yaml(path)
    except yaml.YAMLError as e:
        return None, [v("UNPARSABLE_YAML", rel,
                        "%s 解析失败（%s）——修复后重跑" % (rel, e.__class__.__name__))]
    if not isinstance(doc, dict):
        return None, [v("UNPARSABLE_YAML", rel, "%s 顶层不是映射（形状异常）——修复后重跑" % rel)]
    return doc, []

def read_design(path):
    """读 design.yaml 供校验/自检/审计：返回 (归一文档或 None, 违规清单)。

    文件缺失 / 语法损坏 / 顶层非映射 → 文档为 None；半写畸形 → 归一后随文档返回问题清单。
    """
    doc, violations = load_design_doc(path)
    if doc is None:
        return None, violations
    design, problems = coerce_design(doc)
    return design, [v("UNPARSABLE_YAML", norm_path(path), p) for p in problems]

# ---------------------------------------------------------------- ID 稳定对账

def page_ids(doc):
    """取文档里的页 ID 集（稳定 ID 契约的对象是 pages[].id，非空字符串才算）。"""
    ids = set()
    pages = doc.get("pages") if isinstance(doc, dict) else None
    if isinstance(pages, list):
        for page in pages:
            if isinstance(page, dict) and isinstance(page.get("id"), str) and page["id"].strip():
                ids.add(page["id"])
    return ids

def page_id_violations(pages, base_name):
    """pages[].id 契约：ID 是唯一引用键，须为非空字符串（否则后续按 ID 定位/去重全失准）。

    缺失或空白 → EMPTY_FIELD；非字符串（列表/整数…）→ UNPARSABLE_YAML（形状异常）。
    非映射页条目不在此判（形状问题由 coerce_design 上报）。
    """
    out = []
    for i, page in enumerate(pages or []):
        if not isinstance(page, dict):
            continue
        pid = page.get("id")
        if isinstance(pid, str) and pid.strip():
            continue
        if pid is None or isinstance(pid, str):
            out.append(v("EMPTY_FIELD", "%s pages[%d].id" % (base_name, i),
                         "pages[%d].id 为空（ID 是唯一引用键，必写非空字符串）" % i))
        else:
            out.append(v("UNPARSABLE_YAML", "%s pages[%d].id" % (base_name, i),
                         "pages[%d].id=%r 不是字符串（ID 形状异常）——改回单个 ID 文本" % (i, pid)))
    return out

def check_previous(design, previous, rel):
    """--previous ID 稳定对账：旧稿有、新稿无的页 ID → ID_UNSTABLE。

    与 diyc_check._check_previous 同口径（错误码同名）：快照缺失 → MISSING_FILE、
    快照不可解析 → UNPARSABLE_YAML（两条都是「安全网失效，停手告知用户」）。
    """
    prev_rel = norm_path(previous)
    if not os.path.isfile(previous):
        return [v("MISSING_FILE", prev_rel,
                  "旧稿快照不存在：%s——更新重写前先 cp design.yaml design.yaml.prev" % prev_rel)]
    try:
        prev_doc = load_yaml(previous)
    except yaml.YAMLError as e:
        return [v("UNPARSABLE_YAML", prev_rel,
                  "旧稿快照解析失败（%s）——快照不可用、安全网失效，停手告知用户"
                  % e.__class__.__name__)]
    if not isinstance(prev_doc, dict):
        return [v("UNPARSABLE_YAML", prev_rel,
                  "旧稿快照顶层不是映射——快照不可用、安全网失效，停手告知用户")]
    gone = sorted(page_ids(prev_doc) - page_ids(design))
    return [v("ID_UNSTABLE", "%s pages[%s].id" % (rel, pid),
              "稳定 ID %s 在旧稿存在、新稿中缺失（ID 一旦分配永不重编号、永不复用；"
              "对照 --previous %s）" % (pid, prev_rel)) for pid in gone]

# ---------------------------------------------------------------- a11y 底层：对比度与语义

def rel_lum(channel):  # trace: S-14 AC-14.3 WCAG 相对亮度（sRGB→linear）
    c = channel / 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

def parse_hex(color):  # trace: S-14 AC-14.3 TC-14.3.2 单一权威 hex 解析：3/4 位展开、8 位截 alpha；非法抛 ValueError
    """#abc / #aabbcc / #rgba / #rrggbbaa → (r, g, b)；非字符串或非法长度抛 ValueError。"""
    if not isinstance(color, str):
        raise ValueError(color)
    h = color.strip().lstrip("#").lower()
    if len(h) in (3, 4):
        h = "".join(c * 2 for c in h[:3])
    elif len(h) == 8:
        h = h[:6]
    if len(h) != 6 or any(c not in "0123456789abcdef" for c in h):
        raise ValueError(color)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

def normalize_hex(color):  # trace: S-14 AC-14.3 TC-14.3.2 归一形 #rrggbb（check/audit 同口径比较的权威实现）
    r, g, b = parse_hex(color)
    return "#%02x%02x%02x" % (r, g, b)

def hex_lum(color):  # trace: S-14 AC-14.3 hex → 相对亮度 L
    r, g, b = parse_hex(color)
    return 0.2126 * rel_lum(r) + 0.7152 * rel_lum(g) + 0.0722 * rel_lum(b)

def contrast(a, b):  # trace: S-14 AC-14.3 对比度比率（亮/暗有序）
    la, lb = hex_lum(a), hex_lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)
_FONT_SIZE_RE = re.compile(r"font-size:\s*([^;{}]+)")

def dark_pair_violation(design, base_name):
    """双模明暗对判据：tokens.color.dark 六角色全合法 hex 才算成对。

    双模缺 dark / dark 非映射 / 角色残 / 值非 hex → MODES_TOKEN_PAIR_MISSING
    （validate 与 audit 同判据——audit 是 modes 的核心消费价值）；单模不触发
    （亮/暗 携 dark 归 validate 的 MODES_INVALID 管）。
    """
    if str(design.get("modes") or "").strip() != "双模":
        return None
    dark = ((design.get("tokens") or {}).get("color") or {}).get("dark")
    ok = isinstance(dark, dict)
    if ok:
        for role in DARK_ROLES:
            try:
                normalize_hex(dark.get(role))
            except ValueError:
                ok = False
                break
    if ok:
        return None
    return v("MODES_TOKEN_PAIR_MISSING", "%s tokens.color.dark" % base_name,
             "modes=双模 须带明暗对：tokens.color.dark 六角色（%s）全为合法 hex（亮基暗覆盖）"
             % "/".join(DARK_ROLES))

# ---------------------------------------------------------------- audit

def collect_token_hexes(design):  # trace: S-15 AC-15.2 TC-14.3.2 token 色值归一集（与 check 共用 parse_hex 口径）
    colors = (design.get("tokens") or {}).get("color") or {}
    hexes = set()
    for value in colors.values():
        # dark 子块展开：嵌套 dict（dark 六角色）不再被静默跳过——暗色 hex 进白名单，
        # 否则 audit 会把暗色 token 自判 one-off-color（打自己）
        for item in (value.values() if isinstance(value, dict) else (value,)):
            try:
                hexes.add(normalize_hex(item))
            except ValueError:
                continue
    return hexes

def collect_font_sizes(design):  # trace: S-15 AC-15.2 合法字号集合（typography.scale）
    typo = (design.get("tokens") or {}).get("typography") or {}
    return {str(s).strip() for s in (typo.get("scale") or [])}

# ---- audit 位置判定（finding determinism-2 修复）：hex 只判「真实颜色值位」 ----

# 色属性白名单（闸门）：只有这些属性的值位才算色值；键按小写去连字符归一（兼容 JSX camelCase）
_COLOR_PROPS = frozenset((
    "color", "backgroundcolor", "backgroundimage", "bordercolor", "outline", "outlinecolor",
    "boxshadow", "textshadow", "fill", "stroke", "caretcolor", "accentcolor",
    "textdecorationcolor", "columnrulecolor", "filter",
))
JS_EXTS = (".js", ".ts", ".jsx", ".tsx")

HEX_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b")
# CSS/HTML 声明位：prop: value（止于 ; } 换行或引号；值内逗号合法不作终止）
_DECL_RE = re.compile(r"(?P<prop>--[a-zA-Z][\w-]*|[a-zA-Z][\w-]*)\s*:\s*(?P<val>[^;{}\n\"']*)")
# JS 声明位：无引号值的 prop: value（值止于 ; { } , 换行或引号，不吞同对象下一键）
_JS_DECL_RE = re.compile(r"(?P<prop>--[a-zA-Z][\w-]*|[a-zA-Z][\w-]*)\s*:\s*(?P<val>[^;{},\n\"']+)")
# 引号值位：color: '#fff' / 'backgroundColor': "#fff"
_QUOTED_DECL_RE = re.compile(
    r"['\"]?(?P<prop>[a-zA-Z][\w-]*)['\"]?\s*:\s*['\"](?P<val>[^'\"]*)['\"]")
# 属性/赋值位：<Button color="#fff">、el.style.color = '#fff'
_ATTR_RE = re.compile(r"(?P<prop>[a-zA-Z][\w-]*)\s*=\s*['\"](?P<val>[^'\"]*)['\"]")
_FUNC_RE = re.compile(r"(?<![a-z0-9-])(?:var|url)\s*\(", re.IGNORECASE)
_BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_LINE_COMMENT_RE = re.compile(r"(?m)(?<![\w:])//[^\n]*")

def is_color_prop(prop):
    """色属性白名单：CSS 色属性 / JSX camelCase 样式键 / CSS 自定义属性（--* 定义位）。"""
    if prop.startswith("--"):
        return True
    p = prop.lower().replace("-", "").replace("_", "")
    return p in _COLOR_PROPS or p.startswith("border") or p.startswith("background")

def strip_css_functions(value):
    """剥离 var(...)/url(...) 整体（配平括号含嵌套 fallback）：它们不是 one-off 色值。"""
    out, i = [], 0
    while i < len(value):
        m = _FUNC_RE.match(value, i)
        if not m:
            out.append(value[i])
            i += 1
            continue
        depth, j = 1, m.end()
        while j < len(value) and depth:
            depth += 1 if value[j] == "(" else (-1 if value[j] == ")" else 0)
            j += 1
        i = j
    return "".join(out)

def strip_comments(text, ext):
    """按语法剥注释：块注释与 HTML 注释全部剥；JS 系另剥行注释（避开 http:// 形态）。"""
    text = _BLOCK_COMMENT_RE.sub(" ", text)
    text = _HTML_COMMENT_RE.sub(" ", text)
    if ext in JS_EXTS:
        text = _LINE_COMMENT_RE.sub(" ", text)
    return text

def iter_color_value_spans(text, ext):
    """产出「真实颜色值位」的文本（已剥 var()/url()）：声明值/引号样式键/属性赋值位。

    选择器（#fade）、注释（/* #ccc */）、var() fallback 不在此列；重叠匹配只产出一次。
    """
    rxs = (_JS_DECL_RE if ext in JS_EXTS else _DECL_RE, _QUOTED_DECL_RE, _ATTR_RE)
    taken = []
    for rx in rxs:
        for m in rx.finditer(text):
            if not is_color_prop(m.group("prop")):
                continue
            s, e = m.span("val")
            if any(s < te and ts < e for ts, te in taken):
                continue
            taken.append((s, e))
            yield strip_css_functions(m.group("val"))
