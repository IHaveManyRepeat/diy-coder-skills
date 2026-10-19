# -*- coding: utf-8 -*-
"""diy-design 无障碍/设计系统检测件：语义与 a11y checker 及配套正则。."""

import re
from html.parser import HTMLParser

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import v  # noqa: E402

from design_lib import HEX_RE, TOUCH_TARGET_MIN, TOUCH_TARGET_MIN_DESKTOP, _FONT_SIZE_RE, collect_font_sizes, collect_token_hexes, iter_color_value_spans, normalize_hex, strip_comments  # noqa: E402

REQUIRED_STATES = ("悬停", "空态", "加载中", "错误")
REQUIRED_STATES_TOUCH = ("按压", "空态", "加载中", "错误")  # 移动端四态：悬停 → 按压（无 hover，触控用按压）

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

# ---- 无障碍扩展（源 steps-h/step-03「Define Accessibility Tests」四项中，对比度与屏幕阅读器
#      已由既有 contrast / semantic-html 承载；本组补「触控目标 ≥44px」与「键盘可达」） ----

_INTERACTIVE_TAGS = frozenset(("button", "input", "select", "textarea", "summary"))
_INTERACTIVE_ROLES = frozenset(("button", "link", "tab", "checkbox", "radio", "menuitem"))
# CSS 标签位选择器（排除 .a / #a / -a 这类类名·ID·命名空间误命中）
_INTERACTIVE_SELECTOR_RE = re.compile(
    r"(?<![\w.#-])(?:button|input|select|textarea|summary|a)(?![\w-])|\[role\s*=", re.IGNORECASE)
_RULE_RE = re.compile(r"(?P<sel>[^{}]+)\{(?P<body>[^{}]*)\}", re.DOTALL)
# 盒模型显式尺寸（只判显式 px 声明；未声明不判——静态文本推不出渲染尺寸，宁漏不误报）
_BOX_DECL_RE = re.compile(
    r"(?P<prop>min-width|min-height|width|height)\s*:\s*(?P<val>\d+(?:\.\d+)?)px",
    re.IGNORECASE)
# C·13：动效声明（CSS 属性形态，带冒号；-webkit- 前缀不收——宁漏不误报）与动效降级字样
_MOTION_DECL_RE = re.compile(r"(?<!-)(?:animation|transition)\s*:", re.IGNORECASE)
_REDUCED_MOTION_RE = re.compile(r"prefers-reduced-motion")
# 间距声明（自定义属性 --* 的定义位不算：那是 token 自身，不是使用位）
_SPACING_DECL_RE = re.compile(
    r"(?<![\w-])(?P<prop>padding|margin|gap|row-gap|column-gap|grid-gap)"
    r"(?:-(?:top|right|bottom|left|block|inline)(?:-(?:start|end))?)?"
    r"\s*:\s*(?P<val>[^;{}\n\"']*)", re.IGNORECASE)
_PX_TOKEN_RE = re.compile(r"^-?\d+(?:\.\d+)?px$")

def is_interactive(tag, attrs):
    """可交互元素判定：原生控件 / 带 href 的 a / 交互 role / 显式 tabindex。"""
    if tag in _INTERACTIVE_TAGS:
        return True
    if tag == "a" and attrs.get("href"):
        return True
    if str(attrs.get("role") or "").strip().lower() in _INTERACTIVE_ROLES:
        return True
    return attrs.get("tabindex") is not None

def small_box_decls(text, minimum=TOUCH_TARGET_MIN):
    """产出显式声明且 < 触控下限（分档）的盒模型尺寸 [(prop, px)]。"""
    out = []
    for m in _BOX_DECL_RE.finditer(text or ""):
        px = float(m.group("val"))
        if px < minimum:
            out.append((m.group("prop").lower(), px))
    return out

def touch_target_min_for(form_factor):
    """触控下限分档（C·13 呈核 2/3/8）：桌面 = 24；其余（含缺键/表外值）= 44。"""
    if form_factor == "桌面":
        return TOUCH_TARGET_MIN_DESKTOP
    return TOUCH_TARGET_MIN

def _touch_violation(where, target, prop, px, minimum):
    return v("a11y-touch-target", where,
             "%s 的 %s: %gpx < %dpx——触控目标最小 %d×%dpx"
             % (target, prop, px, minimum, minimum, minimum))

class A11yChecker(HTMLParser):
    """无障碍扩展扫描：触控目标（内联 style + <style> 规则，下限分档）与键盘可达/焦点序。"""

    def __init__(self, where, touch_min=TOUCH_TARGET_MIN):
        super().__init__()
        self.where = where
        self.touch_min = touch_min
        self.violations = []
        self._style_text = []
        self._in_style = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "style":
            self._in_style = True
            return
        if is_interactive(tag, a):
            for prop, px in small_box_decls(a.get("style") or "", self.touch_min):
                self.violations.append(
                    _touch_violation(self.where, tag, prop, px, self.touch_min))
            tabindex = str(a.get("tabindex") or "").strip()
            if tabindex == "-1":
                self.violations.append(v(
                    "a11y-keyboard", self.where,
                    "%s 的 tabindex=\"-1\" 移出 Tab 序——键盘不可达（源判据：交互元素均可 Tab 到达）"
                    % tag))
            elif tabindex.isascii() and tabindex.isdigit() and int(tabindex) > 0:
                # C·13：正 tabindex 强改 Tab 序（tabindex="0" 自然序合法不报）
                self.violations.append(v(
                    "a11y-focus-order", self.where,
                    "%s 的 tabindex=\"%s\" 为正值——正 tabindex 强改 Tab 序，应以 DOM 阅读顺序为准"
                    "（源判据：焦点遍历遵循阅读顺序）" % (tag, tabindex)))
        elif a.get("onclick") is not None and not a.get("role"):
            self.violations.append(v(
                "a11y-keyboard", self.where,
                "%s 挂了 onclick 但无 role/tabindex——键盘够不着（改用 button/a，或补 role + tabindex + 键处理）"
                % tag))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_data(self, data):
        if self._in_style:
            self._style_text.append(data)

    def handle_endtag(self, tag):
        if tag == "style":
            self._in_style = False

    def finish(self):
        """收尾：<style> 规则里的交互选择器尺寸判定。"""
        for m in _RULE_RE.finditer("".join(self._style_text)):
            if not _INTERACTIVE_SELECTOR_RE.search(m.group("sel")):
                continue
            selector = m.group("sel").strip()
            for prop, px in small_box_decls(m.group("body"), self.touch_min):
                self.violations.append(
                    _touch_violation(self.where, selector, prop, px, self.touch_min))
        return self.violations

def collect_a11y_extras(where, text, touch_min=TOUCH_TARGET_MIN):
    """无障碍扩展入口（C·13：touch_min 由 cmd_check 按 form_factor 分档后传入）。"""
    sc = A11yChecker(where, touch_min)
    sc.feed(text)
    sc.close()
    out = sc.finish()
    # C·13 floor ③（Reduce Motion）：动效声明在场且全文无降级字样（宁漏不误报：
    # -webkit- 前缀与 transition-* 子属性不收；降级块不解析结构、字样在场即认可）
    if _MOTION_DECL_RE.search(text) and not _REDUCED_MOTION_RE.search(text):
        out.append(v("a11y-reduced-motion", where,
                     "动效声明（animation/transition）在场但全文无 prefers-reduced-motion 降级"
                     "——Reduce Motion 用户无法跳过动效（源判据：动效须可跳过）"))
    return out

# ---- 设计系统校验 ds-token-*（源 steps-h/step-03「Define token verification」：色值 / 字阶 / 间距走 token）----

def collect_spacing_values(design):
    """合法间距值集合：tokens.spacing.unit + scale（px 口径，逐字比较）。"""
    spacing = (design.get("tokens") or {}).get("spacing") or {}
    values = {str(spacing.get("unit") or "").strip()}
    values |= {str(s).strip() for s in (spacing.get("scale") or [])}
    return {x for x in values if x}

def collect_ds_violations(design, where, text):
    """设计系统校验（ds-token-*）：原型里的色值 / 字号 / 间距不走 token 即违规（code 走新命名空间）。"""
    out = []
    ext = os.path.splitext(where)[1].lower() or ".html"
    body = strip_comments(text, ext)
    hex_ok = collect_token_hexes(design)
    fs_ok = collect_font_sizes(design)
    sp_ok = collect_spacing_values(design)
    for value in iter_color_value_spans(body, ext):
        for m in HEX_RE.finditer(value):
            try:
                norm = normalize_hex(m.group(0))
            except ValueError:
                norm = None
            if norm not in hex_ok:
                out.append(v("ds-token-color", where,
                             "色值 %s 不在 design token（设计系统校验：色值须走 token）"
                             % m.group(0)))
    for m in _FONT_SIZE_RE.finditer(body):
        val = m.group(1).strip()
        if not (val.startswith("var(") or val in fs_ok):
            out.append(v("ds-token-font-size", where,
                         "font-size: %s 既非 var() 也非 token 字阶（设计系统校验：字号须走字阶）" % val))
    for m in _SPACING_DECL_RE.finditer(body):
        val = m.group("val").strip()
        if "var(" in val or "calc(" in val:
            continue
        for token in val.split():
            if _PX_TOKEN_RE.match(token) and token not in sp_ok:
                out.append(v("ds-token-spacing", where,
                             "%s: %s 不在 token 间距系统（设计系统校验：间距须走 spacing.unit/scale）"
                             % (m.group("prop").lower(), token)))
    return out

def required_states(form_factor):
    """必填四态按 form_factor 取值（§7-5③）：移动端 无 hover、触控用 按压；其余形态四态逐字不动。"""
    return REQUIRED_STATES_TOUCH if form_factor == "移动端" else REQUIRED_STATES

def page_gate_violations(base, page, rel, states_code, file_code, required=None):
    """页级门（同 validate 判据）：四态缺一 / 结构稿缺失。transition 的 GATE_FAILED 复用本函数。

    required = 必填态集，按 form_factor 取值（§7-5③）；缺省 REQUIRED_STATES（非移动端既有行为逐字不动）。
    """
    out = []
    names = {s.get("name") for s in page.get("states") or [] if isinstance(s, dict)}
    missing = [s for s in (required or REQUIRED_STATES) if s not in names]
    if missing:
        out.append(v(states_code, "%s pages[%s].states" % (rel, page.get("id")),
                     "%s 缺交互状态 %s" % (page.get("id"), "/".join(missing))))
    proto = page.get("prototype")
    if not proto or not os.path.isfile(os.path.join(base, str(proto))):
        out.append(v(file_code, "%s pages[%s].prototype" % (rel, page.get("id")),
                     "%s 结构稿缺失：%s" % (page.get("id"), proto)))
    return out
