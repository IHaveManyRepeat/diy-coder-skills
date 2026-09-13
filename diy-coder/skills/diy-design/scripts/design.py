# -*- coding: utf-8 -*-
"""diy-design 确定性引擎：前端需求检测 + 易用性自检 + schema 校验。

子命令：
  detect  扫 prd.yaml FR statement → has_frontend（命中词∩¬排除词，启发式；
          LLM 在 SKILL.md 层保留语义复核权）
  check   design.yaml + 原型三项自检：WCAG AA 对比度（角色配对）、
          非色彩唯一信号（states.signals）、语义 HTML（h1/input label/img alt）
  validate design.yaml 结构契约：direction 非空、token 三类、每页四交互状态、原型存在

只读检测；design.yaml 与原型由 diy-design 会话（LLM）创作。实例解析对齐 FR-4.5/D-9。
"""
# trace: S-14 AC-14.1 AC-14.2 AC-14.3 TC-14.1.1 TC-14.2.1 TC-14.3.1
import argparse
import io
import json
import os
import re
import sys
from html.parser import HTMLParser

import yaml

INSTANCE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")

HIT_WORDS = ("页面", "界面", "登录", "表单", "图表", "看板", "仪表盘",
             "导航栏", "弹窗", "轮播", "输入框", "按钮", "列表页", "详情页")
EXCLUDE_WORDS = ("yaml", "skill", "diy-", "渲染", "产出", "生成", "原型",
                 "token", "html", "浏览器", "查看器")

REQUIRED_STATES = ("hover", "empty", "loading", "error")
CONTRAST_PAIRS = (
    ("text", "bg"), ("text", "surface"), ("text_muted", "bg"),
    ("text_muted", "surface"), ("accent_text", "accent"),
)
TEXT_CONTRAST_MIN = 4.5


def load_yaml(path):
    with io.open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def resolve_output_dir(project_root, instance):  # trace: S-16 AC-16.1 D-9 实例目录解析（白名单拒注入）
    cfg_path = os.path.join(project_root, "diy-coder.yaml")
    output_dir = "diy-output"
    if os.path.isfile(cfg_path):
        output_dir = load_yaml(cfg_path).get("paths", {}).get("output_dir", output_dir)
    if instance:
        if not INSTANCE_RE.match(instance):
            sys.stderr.write("invalid instance name: %s\n" % instance)
            sys.exit(1)
        output_dir = os.path.join(output_dir, instance)
    return os.path.join(project_root, output_dir)


def cmd_detect(args):  # trace: S-14 AC-14.2 TC-14.2.1 前端需求启发式（命中词+排除词），skip 判定证据
    output_dir = resolve_output_dir(args.project_root, args.instance)
    prd_path = os.path.join(output_dir, "prd.yaml")
    if not os.path.isfile(prd_path):
        sys.stderr.write("prd.yaml not found: %s\n" % prd_path)
        sys.exit(1)
    prd = load_yaml(prd_path)
    hits = []
    for group in prd.get("features", []) or []:
        for fr in group.get("requirements", []) or []:
            text = str(fr.get("statement", ""))
            if any(w in text for w in HIT_WORDS) and not any(
                    w in text.lower() or w in text for w in EXCLUDE_WORDS):
                hits.append({"fr": fr.get("id"), "text": text[:80]})
    result = {
        "has_frontend": bool(hits),
        "hits": hits,
        "skip_reason": None if hits else
        "PRD 未检测到面向用户的界面需求（启发式零命中）；LLM 可语义复核否决",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json
          else ("检测到前端需求：%s" % json.dumps(hits, ensure_ascii=False)
                if hits else "SKIP：%s" % result["skip_reason"]))


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


class SemanticChecker(HTMLParser):  # trace: S-14 AC-14.3 语义 HTML 启发式（h1 唯一/label 关联/img alt）
    def __init__(self):
        super().__init__()
        self.h1 = 0
        self.img_missing_alt = 0
        self.input_unlabeled = 0
        self._label_for = set()
        self._pending_inputs = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "h1":
            self.h1 += 1
        elif tag == "img" and not a.get("alt"):
            self.img_missing_alt += 1
        elif tag == "label" and a.get("for"):
            self._label_for.add(a["for"])
        elif tag == "input":
            if not a.get("aria-label") and a.get("id") not in self._label_for:
                self._pending_inputs.append(a.get("id"))

    def close(self):
        super().close()
        self.input_unlabeled = len([i for i in self._pending_inputs
                                    if i not in self._label_for])


def coerce_design(doc):  # trace: S-14 AC-14.3 TC-14.3.3 形状归一：半写/畸形容器降级为空并记录问题
    """把未知形状归一为可安全遍历的结构；返回 (归一后文档, 问题清单)。"""
    problems = []

    def take_map(v, path):
        if isinstance(v, dict):
            return v
        if v is not None:
            problems.append("%s 不是映射（%s），已按缺失处理" % (path, type(v).__name__))
        return {}

    def take_seq(v, path):
        if isinstance(v, list):
            return v
        if v is not None:
            problems.append("%s 不是列表（%s），已按空处理" % (path, type(v).__name__))
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
    return {**doc, "tokens": tokens, "pages": pages}, problems


def load_design_or_die(path):  # trace: S-14 AC-14.3 TC-14.3.3 损坏 YAML 一行报错；形状问题随返回值上报（列违规）
    """读 design.yaml：语法损坏 → 一行报错退出；形状未知 → 归一 + 问题清单。"""
    try:
        doc = load_yaml(path)
    except yaml.YAMLError as e:
        sys.stderr.write("design.yaml unparsable: %s" % e)
        sys.exit(1)
    return coerce_design(doc)


def cmd_check(args):  # trace: S-14 AC-14.3 TC-14.3.1 TC-14.3.3 三项自检：fail 列违规清单（含形状问题）
    design, shape_problems = load_design_or_die(args.design)
    base = os.path.dirname(os.path.abspath(args.design))
    tokens = (design.get("tokens") or {}).get("color") or {}
    violations = [{"kind": "malformed", "detail": p} for p in shape_problems]
    for fg, bg in CONTRAST_PAIRS:
        if fg in tokens and bg in tokens:
            try:
                ratio = contrast(tokens[fg], tokens[bg])
            except ValueError:
                violations.append({
                    "kind": "contrast",
                    "detail": "%s(%s)/%s(%s) 不是合法 hex 色值" % (
                        fg, tokens[fg], bg, tokens[bg])})
                continue
            if ratio < TEXT_CONTRAST_MIN:
                violations.append({
                    "kind": "contrast",
                    "detail": "%s(%s) on %s(%s) = %.2f:1 < %.1f:1" % (
                        fg, tokens[fg], bg, tokens[bg], ratio, TEXT_CONTRAST_MIN)})
    for page in design.get("pages", []) or []:
        for st in page.get("states", []) or []:
            signals = [s for s in (st.get("signals") or []) if s != "color"]
            if not signals:
                violations.append({
                    "kind": "color-only-signal",
                    "detail": "%s 状态 %s 仅有色彩信号，需补 icon/text/shape/motion 等非色彩信号" % (
                        page.get("id"), st.get("name"))})
        proto = page.get("prototype")
        if not proto:
            continue
        ppath = os.path.join(base, str(proto))
        if not os.path.isfile(ppath):
            violations.append({
                "kind": "semantic-html",
                "detail": "%s 原型文件缺失：%s" % (page.get("id"), proto)})
        else:
            sc = SemanticChecker()
            sc.feed(io.open(ppath, encoding="utf-8").read())
            sc.close()
            if sc.h1 != 1:
                violations.append({
                    "kind": "semantic-html",
                    "detail": "%s 原型 h1 数量=%d（应为 1）" % (page.get("id"), sc.h1)})
            if sc.img_missing_alt:
                violations.append({
                    "kind": "semantic-html",
                    "detail": "%s 原型 %d 个 img 缺 alt" % (page.get("id"), sc.img_missing_alt)})
            if sc.input_unlabeled:
                violations.append({
                    "kind": "semantic-html",
                    "detail": "%s 原型 %d 个 input 无 label/aria-label" % (
                        page.get("id"), sc.input_unlabeled)})
    result = {"pass": not violations, "violations": violations,
              "checked": {"contrast_pairs": list(CONTRAST_PAIRS),
                          "signals": "states.signals 非色彩",
                          "semantic_html": ["h1 唯一", "input 带 label", "img 带 alt"]}}
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json
          else ("PASS：易用性自检通过" if not violations else
                "FAIL：\n" + "\n".join("- [%s] %s" % (v["kind"], v["detail"])
                                       for v in violations)))
    if violations:
        sys.exit(1)


def cmd_validate(args):  # trace: S-14 AC-14.1 TC-14.1.1 TC-14.3.3 design.yaml 结构契约校验（含形状问题）；D-10 三段式字段
    design, shape_problems = load_design_or_die(args.design)
    base = os.path.dirname(os.path.abspath(args.design))
    errors = list(shape_problems)
    if not str(design.get("direction") or "").strip():
        errors.append("direction（承诺式美学方向）为空")
    if not str(design.get("frontend_framework") or "").strip():
        errors.append("frontend_framework 为空（从 architecture stack 选定；纯 HTML 项目写 html）")
    tokens = design.get("tokens") or {}
    for family, keys in (("color", ("bg", "text", "accent")),
                         ("spacing", ("unit", "scale")),
                         ("typography", ("family_base", "scale"))):
        node = tokens.get(family) or {}
        missing = [k for k in keys if not node.get(k)]
        if missing:
            errors.append("tokens.%s 缺 %s" % (family, "/".join(missing)))
    pages = design.get("pages") or []
    if not pages:
        errors.append("pages 为空")
    for page in pages:
        names = {s.get("name") for s in page.get("states") or []}
        missing = [s for s in REQUIRED_STATES if s not in names]
        if missing:
            errors.append("%s 缺交互状态 %s" % (page.get("id"), "/".join(missing)))
        proto = page.get("prototype")
        if not proto or not os.path.isfile(os.path.join(base, str(proto))):
            errors.append("%s 结构稿缺失：%s" % (page.get("id"), proto))
        impl = page.get("implementation")
        if impl and not os.path.isfile(os.path.join(base, str(impl))):
            errors.append("%s 实现稿缺失：%s" % (page.get("id"), impl))
    result = {"valid": not errors, "errors": errors}
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json
          else ("VALID" if not errors else "INVALID：\n" + "\n".join(errors)))
    if errors:
        sys.exit(1)


def collect_token_hexes(design):  # trace: S-15 AC-15.2 TC-14.3.2 token 色值归一集（与 check 共用 parse_hex 口径）
    colors = (design.get("tokens") or {}).get("color") or {}
    hexes = set()
    for v in colors.values():
        try:
            hexes.add(normalize_hex(v))
        except ValueError:
            continue
    return hexes


def collect_font_sizes(design):  # trace: S-15 AC-15.2 合法字号集合（typography.scale）
    typo = (design.get("tokens") or {}).get("typography") or {}
    return {str(s).strip() for s in (typo.get("scale") or [])}


def cmd_audit(args):  # trace: S-15 AC-15.2 TC-15.2.1 TC-14.3.2 one-off 色值/字号审计（归一比较，token 单一源）
    design, shape_problems = load_design_or_die(args.design)
    hex_ok = collect_token_hexes(design)
    fs_ok = collect_font_sizes(design)
    violations = [{"kind": "malformed", "detail": p} for p in shape_problems]
    hex_re = re.compile(r"#[0-9a-fA-F]{3,8}\b")
    fs_re = re.compile(r"font-size:\s*([^;{}]+)")
    if not os.path.exists(args.src):
        sys.stderr.write("src not found: %s\n" % args.src)
        sys.exit(1)
    if os.path.isdir(args.src):
        files = []
        for root, _, names in os.walk(args.src):
            files += [os.path.join(root, n) for n in names
                      if n.endswith((".html", ".css", ".js", ".ts",
                                     ".jsx", ".tsx", ".vue"))]
    else:
        files = [args.src]
    for fpath in files:
        text = io.open(fpath, encoding="utf-8").read()
        rel = os.path.basename(fpath)
        for m in hex_re.finditer(text):
            try:
                norm = normalize_hex(m.group(0))
            except ValueError:
                norm = None
            if norm not in hex_ok:
                violations.append({
                    "kind": "one-off-color",
                    "detail": "%s: 色值 %s 不在 design token（单一源违规）" % (
                        rel, m.group(0))})
        for m in fs_re.finditer(text):
            val = m.group(1).strip()
            if not (val.startswith("var(") or val in fs_ok):
                violations.append({
                    "kind": "one-off-font-size",
                    "detail": '%s: font-size: %s 既非 var() 也非 token 字阶' % (rel, val)})
    result = {"pass": not violations, "violations": violations,
              "audited": len(files)}
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json
          else ("PASS：token 单一源审计通过（%d 文件）" % len(files) if not violations
                else "FAIL：" + chr(10).join(
                    "- [%s] %s" % (x["kind"], x["detail"]) for x in violations)))
    if violations:
        sys.exit(1)


def main():  # trace: S-14 AC-14.1 子命令路由（utf-8 输出确定性）；D-10：compare 已删除
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="diy-design 检测/自检/校验引擎")
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("detect", help="检测 PRD 前端需求")
    d.add_argument("--project-root", default=".")
    d.add_argument("--instance", default=None)
    d.add_argument("--json", action="store_true")
    d.set_defaults(func=cmd_detect)
    c = sub.add_parser("check", help="易用性三项自检")
    c.add_argument("--design", required=True)
    c.add_argument("--json", action="store_true")
    c.set_defaults(func=cmd_check)
    v = sub.add_parser("validate", help="design.yaml 结构契约校验")
    v.add_argument("--design", required=True)
    v.add_argument("--json", action="store_true")
    v.set_defaults(func=cmd_validate)
    a = sub.add_parser("audit", help="one-off 色值/字号审计（token 单一源）")
    a.add_argument("--design", required=True)
    a.add_argument("--src", required=True)
    a.add_argument("--json", action="store_true")
    a.set_defaults(func=cmd_audit)
    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
