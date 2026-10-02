# -*- coding: utf-8 -*-
"""diy-design 确定性引擎：前端需求检测 + 易用性自检 + schema 校验 + 页状态迁移。

子命令（回执 = 全家族统一形状，单行 JSON：{ok, command, violations[{code, where, msg}],
warnings[], counts{}, file}；退出码 0 成功 / 1 拒绝 / 2 用法错误）：
  detect      扫 prd.yaml FR statement → has_frontend（命中词 ∩ ¬机器锚词，启发式；
              普通动词不构成否决，机器锚词按词边界锚定；LLM 在 SKILL.md 层保留语义复核权）
  validate    design.yaml 结构契约：direction 非空、token 三类、每页四交互状态、原型存在、
              pages[].id 非空字符串与 status 枚举/removed_reason、open_questions 结构与终门、
              token_scope 形状；
              --previous <旧稿> 追加 ID 稳定对账（ID_UNSTABLE / MISSING_FILE / UNPARSABLE_YAML）
  check       design.yaml + 原型自检（判据面 = 回执 violations[].code）：易用性 contrast /
              color-only-signal / semantic-html · 无障碍 a11y-touch-target / a11y-keyboard ·
              设计系统 ds-token-color / ds-token-font-size / ds-token-spacing
  audit       扫 src 实现源码的 one-off 色值/字号（hex 按语法位置判定：只判声明值/内联 style
              等真实色值位，var() fallback 与选择器/注释不算）；token_scope 内的路径跳过
  transition  页状态迁移写回（9 条合法边冻结；重写 design.yaml 前落 .prev 快照；
              → 已移除 必填 --reason；破坏性边追加 revisions[]）

写回纪律（transition）：原样载入 → 就地改 → safe_dump(allow_unicode, sort_keys=False)
→ 同目录 .tmp + os.replace 原子替换；校验不过零写入。实例解析对齐 FR-4.5/D-9。
"""
# trace: S-14 AC-14.1 AC-14.2 AC-14.3 TC-14.1.1 TC-14.2.1 TC-14.3.1
import argparse
import datetime
import io
import json
import os
import re
import sys
from html.parser import HTMLParser

import yaml

# 实例名白名单（与 viewer/help/runner/exp-sync 同源）：字母数字开头和结尾，中间可含 . _ -。
# 末字符禁点：Windows 目录名尾点被静默折叠（b. ≡ b），会破坏实例隔离；fullmatch 避免 $ 放行尾换行
INSTANCE_RE = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9_-])?")

HIT_WORDS = ("页面", "界面", "登录", "表单", "图表", "看板", "仪表盘",
             "导航栏", "弹窗", "轮播", "输入框", "按钮", "列表页", "详情页")
# 机器锚词否决（finding determinism-1 修复）：只有工具链/文档语境的机器锚词能否决命中——
# 文件名扩展名（prd.yaml）、技能名前缀（diy-）、技术术语（html/token/skill）与套件组件名
# （viewer），按词边界锚定。普通动词（生成/渲染/产出…）不再构成否决：它们出现在真实 UI
# 需求句中是常态（如「系统应生成订单详情页」，靠 viewer/diy- 等锚词而非动词排除）。
MACHINE_VETO_RE = re.compile(
    r"(?<![a-z0-9])(?:yaml|html|tokens?|skills?|viewers?)(?![a-z0-9])|diy-[a-z0-9]",
    re.IGNORECASE)

REQUIRED_STATES = ("悬停", "空态", "加载中", "错误")
REQUIRED_STATES_TOUCH = ("按压", "空态", "加载中", "错误")  # 移动端四态：悬停 → 按压（无 hover，触控用按压）
CONTRAST_PAIRS = (
    ("text", "bg"), ("text", "surface"), ("text_muted", "bg"),
    ("text_muted", "surface"), ("accent_text", "accent"),
)
TEXT_CONTRAST_MIN = 4.5

# ---- 裁定 C12-1（2026-09-28）：design.yaml 顶层两键——形态/默认主题由「不并」改判「有承载」 ----
FORM_FACTORS = ("响应式 Web", "移动端", "桌面", "多端")  # 目标表面（写在什么上），与 frontend_framework 互补
MODES = ("亮", "暗", "双模")  # 默认主题模式；双模 触发 tokens 明暗对审计联动
# ---- C·7 裁定 2（2026-10-02）：pages[].meta 可选内容键（meta-content 判据级承载）----
META_KEYS = ("title", "description", "og_image")  # 三子键全可选；在场则须非空字符串
# §7-5①：双模的明暗对 = tokens.color.dark 子块六角色（亮基暗覆盖），判据见 dark_pair_violation
DARK_ROLES = ("bg", "surface", "text", "text_muted", "accent", "accent_text")

# ---- 页状态机（裁定 5/6/14）：5 值收敛 + 9 条合法边 ----
PAGE_STATUSES = ("未开始", "结构稿中", "待验收", "已批准", "已移除")
PAGE_STATUS_INITIAL = "未开始"
LEGAL_EDGES = frozenset({
    ("未开始", "结构稿中"),
    ("结构稿中", "待验收"),
    ("结构稿中", "已移除"),
    ("待验收", "已批准"),
    ("待验收", "结构稿中"),
    ("待验收", "已移除"),
    ("已批准", "结构稿中"),
    ("已批准", "已移除"),
    ("已移除", "结构稿中"),
})
# 页级门的落点边（不重跑 check）：→ 待验收 / 已批准 须先满足该页的 validate 判据
GATED_TARGETS = ("待验收", "已批准")

OPEN_QUESTION_STATUSES = ("待办", "已解决")

# 无障碍：触控目标下限（源 steps-h/step-03「Minimum 44x44px interactive areas」）
TOUCH_TARGET_MIN = 44

NL = "\n"


# ---------------------------------------------------------------- 回执与违规（契约 §2.4）

def v(code, where, msg):
    """违规构造；where 统一正斜杠（承 diyc 契约 §3）。"""
    return {"code": code, "where": str(where).replace("\\", "/"), "msg": msg}


def receipt(command, ok, file=None, violations=None, warnings=None, counts=None, **extra):
    """回执基础构造：公共键在前、命令专有键在后（公共键一个不少、专有键一个不删）。"""
    r = {"ok": bool(ok), "command": command,
         "violations": list(violations or []), "warnings": list(warnings or []),
         "counts": dict(counts or {}), "file": file}
    r.update(extra)
    return r


def display_path(path):
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
        lines += ["%s %s: %s" % (x.get("code"), x.get("where"), x.get("msg"))
                  for x in result.get("violations") or []]
        lines += ["WARN %s" % w for w in result.get("warnings") or []]
        lines.append(_summary(result))
        print(NL.join(lines))
    return 0 if result.get("ok") else 1


def today():
    return datetime.date.today().isoformat()


def load_yaml(path):
    with io.open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def resolve_output_dir(project_root, instance):  # trace: S-16 AC-16.1 D-9 实例目录解析（白名单拒注入）
    cfg_path = os.path.join(project_root, "diy-coder.yaml")
    output_dir = "diy-output"
    if os.path.isfile(cfg_path):
        output_dir = load_yaml(cfg_path).get("paths", {}).get("output_dir", output_dir)
    if instance:
        if not INSTANCE_RE.fullmatch(instance):
            sys.stderr.write("非法实例名: %s（字母数字开头和结尾，中间可含 . _ -）\n" % instance)
            sys.exit(2)
        output_dir = os.path.join(output_dir, instance)
    return os.path.join(project_root, output_dir)


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
    rel = display_path(path)
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
    return design, [v("UNPARSABLE_YAML", display_path(path), p) for p in problems]


# ---------------------------------------------------------------- ID 稳定对账（裁定 15）

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
    prev_rel = display_path(previous)
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


# ---------------------------------------------------------------- detect

def cmd_detect(args):  # trace: S-14 AC-14.2 TC-14.2.1 前端需求启发式（命中词+机器锚词否决），skip 判定证据
    output_dir = resolve_output_dir(args.project_root, args.instance)
    prd_path = os.path.join(output_dir, "prd.yaml")
    rel = display_path(prd_path)
    if not os.path.isfile(prd_path):
        return emit(receipt("detect", False, file=rel,
                            violations=[v("MISSING_FILE", rel,
                                          "%s 不存在——先运行 diy-prd 生成该产物" % rel)],
                            counts={"requirements": 0, "hits": 0}), args.json)
    prd = load_yaml(prd_path)
    hits = []
    total = 0
    for group in prd.get("features", []) or []:
        for fr in group.get("requirements", []) or []:
            total += 1
            text = str(fr.get("statement", ""))
            if any(w in text for w in HIT_WORDS) and not MACHINE_VETO_RE.search(text):
                hits.append({"fr": fr.get("id"), "text": text[:80]})
    skip_reason = None if hits else \
        "PRD 未检测到面向用户的界面需求（启发式：命中词零命中或机器锚词否决）；LLM 可语义复核否决"
    result = receipt("detect", True, file=rel, violations=[],
                     counts={"requirements": total, "hits": len(hits)},
                     has_frontend=bool(hits), hits=hits, skip_reason=skip_reason)
    line = ("检测到前端需求：%s" % json.dumps(hits, ensure_ascii=False)
            if hits else "SKIP：%s" % skip_reason)
    return emit(result, args.json, [line])


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
_FONT_SIZE_RE = re.compile(r"font-size:\s*([^;{}]+)")
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


def small_box_decls(text):
    """产出显式声明且 <44px 的盒模型尺寸 [(prop, px)]。"""
    out = []
    for m in _BOX_DECL_RE.finditer(text or ""):
        px = float(m.group("val"))
        if px < TOUCH_TARGET_MIN:
            out.append((m.group("prop").lower(), px))
    return out


def _touch_violation(where, target, prop, px):
    return v("a11y-touch-target", where,
             "%s 的 %s: %gpx < %dpx——触控目标最小 %d×%dpx"
             % (target, prop, px, TOUCH_TARGET_MIN, TOUCH_TARGET_MIN, TOUCH_TARGET_MIN))


class A11yChecker(HTMLParser):
    """无障碍扩展扫描：触控目标（内联 style + <style> 规则）与键盘可达。"""

    def __init__(self, where):
        super().__init__()
        self.where = where
        self.violations = []
        self._style_text = []
        self._in_style = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "style":
            self._in_style = True
            return
        if is_interactive(tag, a):
            for prop, px in small_box_decls(a.get("style") or ""):
                self.violations.append(_touch_violation(self.where, tag, prop, px))
            if str(a.get("tabindex") or "").strip() == "-1":
                self.violations.append(v(
                    "a11y-keyboard", self.where,
                    "%s 的 tabindex=\"-1\" 移出 Tab 序——键盘不可达（源判据：交互元素均可 Tab 到达）"
                    % tag))
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
            for prop, px in small_box_decls(m.group("body")):
                self.violations.append(_touch_violation(self.where, selector, prop, px))
        return self.violations


def collect_a11y_extras(where, text):
    sc = A11yChecker(where)
    sc.feed(text)
    sc.close()
    return sc.finish()


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


def dark_pair_violation(design, base_name):
    """双模明暗对判据（§7-5①）：tokens.color.dark 六角色全合法 hex 才算成对。

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


def cmd_check(args):  # trace: S-14 AC-14.3 TC-14.3.1 TC-14.3.3 自检：fail 列违规清单（含形状问题）
    design, violations = read_design(args.design)
    rel = display_path(args.design)
    if design is None:
        return emit(receipt("check", False, file=rel, violations=violations,
                            counts={"pages": 0, "prototypes": 0, "states": 0}), args.json)
    base = os.path.dirname(os.path.abspath(args.design))
    base_name = os.path.basename(args.design)
    tokens = (design.get("tokens") or {}).get("color") or {}
    pages = design.get("pages") or []
    # 维度一：对比度（既有，不得删改/降级）
    for fg, bg in CONTRAST_PAIRS:
        if fg in tokens and bg in tokens:
            try:
                ratio = contrast(tokens[fg], tokens[bg])
            except ValueError:
                violations.append(v("contrast", "%s tokens.color.%s/%s" % (base_name, fg, bg),
                                    "%s(%s)/%s(%s) 不是合法 hex 色值" % (
                                        fg, tokens[fg], bg, tokens[bg])))
                continue
            if ratio < TEXT_CONTRAST_MIN:
                violations.append(v("contrast", "%s tokens.color.%s/%s" % (base_name, fg, bg),
                                    "%s(%s) on %s(%s) = %.2f:1 < %.1f:1" % (
                                        fg, tokens[fg], bg, tokens[bg], ratio, TEXT_CONTRAST_MIN)))
    # 维度一（续）·双模暗色配对（§7-5② 部分解冻）：对 dark 六角色算同款 5 组，阈值同 4.5:1；
    # 回执 contrast_pairs 以 dark.<role> 形态原样枚举暗色对（checked/counts 计数含）；单模零暗色对
    dark_pairs = []
    dark = tokens.get("dark")
    if str(design.get("modes") or "").strip() == "双模" and isinstance(dark, dict):
        dark_pairs = [("dark." + fg, "dark." + bg) for fg, bg in CONTRAST_PAIRS]
        for fg, bg in CONTRAST_PAIRS:
            if fg in dark and bg in dark:
                try:
                    ratio = contrast(dark[fg], dark[bg])
                except ValueError:
                    violations.append(v("contrast",
                                        "%s tokens.color.dark.%s/%s" % (base_name, fg, bg),
                                        "dark.%s(%s)/dark.%s(%s) 不是合法 hex 色值" % (
                                            fg, dark[fg], bg, dark[bg])))
                    continue
                if ratio < TEXT_CONTRAST_MIN:
                    violations.append(v("contrast",
                                        "%s tokens.color.dark.%s/%s" % (base_name, fg, bg),
                                        "dark.%s(%s) on dark.%s(%s) = %.2f:1 < %.1f:1" % (
                                            fg, dark[fg], bg, dark[bg], ratio, TEXT_CONTRAST_MIN)))
    contrast_pairs_checked = list(CONTRAST_PAIRS) + dark_pairs
    n_proto = 0
    n_states = 0
    for page in pages:
        pid = page.get("id")
        for st in page.get("states") or []:
            n_states += 1
            signals = [s for s in (st.get("signals") or []) if s != "色彩"]
            if not signals:
                # 维度二：非色彩唯一信号（既有）
                violations.append(v("color-only-signal",
                                    "%s pages[%s].states[%s].signals"
                                    % (base_name, pid, st.get("name")),
                                    "%s 状态 %s 仅有色彩信号，需补图标/文字/形状/动效等非色彩信号"
                                    % (pid, st.get("name"))))
        proto = page.get("prototype")
        if not proto:
            continue
        ppath = os.path.join(base, str(proto))
        if not os.path.isfile(ppath):
            # 维度三：语义 HTML（既有）——原型文件缺失
            violations.append(v("semantic-html", "%s pages[%s].prototype" % (base_name, pid),
                                "%s 原型文件缺失：%s" % (pid, proto)))
            continue
        n_proto += 1
        text = io.open(ppath, encoding="utf-8").read()
        where = display_path(proto)
        sc = SemanticChecker()
        sc.feed(text)
        sc.close()
        if sc.h1 != 1:
            violations.append(v("semantic-html", where,
                                "%s 原型 h1 数量=%d（应为 1）" % (pid, sc.h1)))
        if sc.img_missing_alt:
            violations.append(v("semantic-html", where,
                                "%s 原型 %d 个 img 缺 alt" % (pid, sc.img_missing_alt)))
        if sc.input_unlabeled:
            violations.append(v("semantic-html", where,
                                "%s 原型 %d 个 input 无 label/aria-label" % (pid, sc.input_unlabeled)))
        # 维度四/五：无障碍扩展 + 设计系统（新增，code 走新命名空间）
        violations += collect_a11y_extras(where, text)
        violations += collect_ds_violations(design, where, text)
    if getattr(args, "previous", None):
        violations += check_previous(design, args.previous, base_name)
    checked = {"contrast_pairs": contrast_pairs_checked,
               "signals": "states.signals 非色彩",
               "semantic_html": ["h1 唯一", "input 带 label", "img 带 alt"],
               "a11y_extras": ["触控目标 ≥%dpx" % TOUCH_TARGET_MIN,
                               "键盘可达（tabindex/onclick）"],
               "design_system": ["色值走 token", "字阶走 token", "间距走 token"]}
    result = receipt("check", not violations, file=rel, violations=violations,
                     counts={"pages": len(pages), "prototypes": n_proto,
                             "states": n_states,
                             "contrast_pairs": len(contrast_pairs_checked)},
                     checked=checked)
    return emit(result, args.json, ["check：%d 页 / %d 原型" % (len(pages), n_proto)])


# ---------------------------------------------------------------- validate

def _validate_open_questions(design, base_name, violations):
    """open_questions 结构校验（裁定 8）：id/question/status/answer 四字段与状态联动。"""
    seen = set()
    for i, item in enumerate(design.get("open_questions") or []):
        where = "%s open_questions[%d]" % (base_name, i)
        if not isinstance(item, dict):
            violations.append(v("UNPARSABLE_YAML", where,
                                "open_questions[%d] 不是映射（%s）——形状异常，不当合法条目"
                                % (i, type(item).__name__)))
            continue
        qid = item.get("id")
        if not (isinstance(qid, str) and qid.strip()):
            violations.append(v("EMPTY_FIELD", where + ".id", "open_questions[%d].id 为空" % i))
        elif qid in seen:
            violations.append(v("DUPLICATE_ID", where + ".id",
                                "open_questions 的 id %s 重复" % qid))
        else:
            seen.add(qid)
        if not (isinstance(item.get("question"), str) and item["question"].strip()):
            violations.append(v("EMPTY_FIELD", where + ".question",
                                "open_questions[%d].question 为空（问题本身必写）" % i))
        status = item.get("status")
        if status not in OPEN_QUESTION_STATUSES:
            violations.append(v("ENUM_INVALID", where + ".status",
                                "open_questions[%d].status=%r 不在 %s"
                                % (i, status, "/".join(OPEN_QUESTION_STATUSES))))
        elif status == "已解决" and not (isinstance(item.get("answer"), str)
                                       and item["answer"].strip()):
            violations.append(v("EMPTY_FIELD", where + ".answer",
                                "open_questions[%d] 已解决但 answer 为空（回答必写）" % i))


def _validate_final_gate(design, base_name, violations):
    """终门联动（裁定 8）：已定稿 要求零 待办。"""
    if str((design.get("project") or {}).get("status") or "").strip() != "已定稿":
        return
    for i, item in enumerate(design.get("open_questions") or []):
        if isinstance(item, dict) and item.get("status") == "待办":
            violations.append(v("OPEN_QUESTION_PENDING",
                                "%s open_questions[%d].status" % (base_name, i),
                                "已定稿 要求零 待办：%s 仍待办（先与用户确认，再转 已解决）"
                                % (item.get("id") or ("open_questions[%d]" % i))))


def cmd_validate(args):  # trace: S-14 AC-14.1 TC-14.1.1 TC-14.3.3 design.yaml 结构契约校验（含形状问题）；D-10 三段式字段
    design, violations = read_design(args.design)
    rel = display_path(args.design)
    if design is None:
        return emit(receipt("validate", False, file=rel, violations=violations,
                            counts={"pages": 0, "states": 0, "open_questions": 0}), args.json)
    base = os.path.dirname(os.path.abspath(args.design))
    base_name = os.path.basename(args.design)
    if not str(design.get("direction") or "").strip():
        violations.append(v("EMPTY_FIELD", base_name + " direction", "direction（承诺式美学方向）为空"))
    if not str(design.get("frontend_framework") or "").strip():
        violations.append(v("EMPTY_FIELD", base_name + " frontend_framework",
                            "frontend_framework 为空（从 architecture stack 选定；纯 HTML 项目写 html）"))
    # 裁定 C12-1：顶层两键在场 + 值域（专项码首例——顶层键错误与条目字段错误不同层级，
    # 下游需要可 grep 的稳定锚）；§7-5①：dark 子块仅 双模 可有且必填
    form_factor = design.get("form_factor")
    if form_factor is None or (isinstance(form_factor, str) and not form_factor.strip()):
        violations.append(v("FORM_FACTOR_MISSING", base_name + " form_factor",
                            "form_factor 缺失（目标表面：响应式 Web/移动端/桌面/多端——开工先定，写在什么上）"))
    elif form_factor not in FORM_FACTORS:
        violations.append(v("FORM_FACTOR_INVALID", base_name + " form_factor",
                            "form_factor=%r 不在 %s" % (form_factor, "/".join(FORM_FACTORS))))
    modes = design.get("modes")
    if modes is None or (isinstance(modes, str) and not modes.strip()):
        violations.append(v("MODES_MISSING", base_name + " modes",
                            "modes 缺失（默认主题模式：亮/暗/双模）"))
    elif modes not in MODES:
        violations.append(v("MODES_INVALID", base_name + " modes",
                            "modes=%r 不在 %s" % (modes, "/".join(MODES))))
    elif modes in ("亮", "暗") and \
            ((design.get("tokens") or {}).get("color") or {}).get("dark") is not None:
        violations.append(v("MODES_INVALID", "%s tokens.color.dark" % base_name,
                            "dark 仅 双模 可有（%s 单模不携明暗对）" % modes))
    dark_pair = dark_pair_violation(design, base_name)
    if dark_pair:
        violations.append(dark_pair)
    tokens = design.get("tokens") or {}
    for family, keys in (("color", ("bg", "text", "accent")),
                         ("spacing", ("unit", "scale")),
                         ("typography", ("family_base", "scale"))):
        node = tokens.get(family) or {}
        missing = [k for k in keys if not node.get(k)]
        if missing:
            violations.append(v("EMPTY_FIELD", "%s tokens.%s" % (base_name, family),
                                "tokens.%s 缺 %s" % (family, "/".join(missing))))
    for i, entry in enumerate(design.get("token_scope") or []):
        if not (isinstance(entry, str) and entry.strip()):
            violations.append(v("UNPARSABLE_YAML", "%s token_scope[%d]" % (base_name, i),
                                "token_scope[%d] 不是非空路径字符串（audit 的跳过清单）" % i))
    pages = design.get("pages") or []
    n_states = 0
    if not pages:
        violations.append(v("EMPTY_FIELD", base_name + " pages", "pages 为空"))
    violations += page_id_violations(pages, base_name)
    required = required_states(design.get("form_factor"))  # §7-5③：移动端 悬停 → 按压
    for page in pages:
        pid = page.get("id")
        states = page.get("states") or []
        n_states += len(states)
        violations += page_gate_violations(base, page, base_name, "EMPTY_FIELD",
                                           "MISSING_FILE", required)
        for i, st in enumerate(states):
            if not st.get("name"):
                violations.append(v("EMPTY_FIELD",
                                    "%s pages[%s].states[%d]" % (base_name, pid, i),
                                    "%s 有交互状态缺 name" % pid))
        status = page.get("status")
        if status is not None:
            if status not in PAGE_STATUSES:
                violations.append(v("ENUM_INVALID", "%s pages[%s].status" % (base_name, pid),
                                    "%s 的 status=%r 不在 %s"
                                    % (pid, status, "/".join(PAGE_STATUSES))))
            elif status == "已移除" and not (isinstance(page.get("removed_reason"), str)
                                           and page["removed_reason"].strip()):
                violations.append(v("EMPTY_FIELD", "%s pages[%s].removed_reason" % (base_name, pid),
                                    "%s 已移除 但 removed_reason 为空（移除原因必写）" % pid))
        impl = page.get("implementation")
        if impl and not os.path.isfile(os.path.join(base, str(impl))):
            violations.append(v("MISSING_FILE", "%s pages[%s].implementation" % (base_name, pid),
                                "%s 实现稿缺失：%s" % (pid, impl)))
        # C·7 裁定 2 / SS-030-06：meta 可选——在场才判，机械判仅一层
        # （子键在场须非空字符串；空串与非字符串均 EMPTY_FIELD、msg 区分两态；
        #  不用 UNPARSABLE_YAML——那是 YAML 解析层。缺失不违规：「公开站点应填」
        #  是引导判据（p-specify 两层分写），不进 validate——防把文学判断伪装成机械判定）
        meta = page.get("meta")
        if isinstance(meta, dict):
            for key in META_KEYS:
                val = meta.get(key)
                if val is None:
                    continue
                if not isinstance(val, str):
                    violations.append(v("EMPTY_FIELD",
                                        "%s pages[%s].meta.%s" % (base_name, pid, key),
                                        "pages[%s].meta.%s=%r 不是字符串" % (pid, key, val)))
                elif not val.strip():
                    violations.append(v("EMPTY_FIELD",
                                        "%s pages[%s].meta.%s" % (base_name, pid, key),
                                        "pages[%s].meta.%s 为空（在场则必写非空字符串）" % (pid, key)))
        elif meta is not None:
            violations.append(v("EMPTY_FIELD", "%s pages[%s].meta" % (base_name, pid),
                                "pages[%s].meta 不是映射（三子键 %s）" % (pid, "/".join(META_KEYS))))
    _validate_open_questions(design, base_name, violations)
    _validate_final_gate(design, base_name, violations)
    if getattr(args, "previous", None):
        violations += check_previous(design, args.previous, base_name)
    result = receipt("validate", not violations, file=rel, violations=violations,
                     counts={"pages": len(pages), "states": n_states,
                             "open_questions": len(design.get("open_questions") or [])})
    return emit(result, args.json, ["validate：%d 页" % len(pages)])


# ---------------------------------------------------------------- audit

def collect_token_hexes(design):  # trace: S-15 AC-15.2 TC-14.3.2 token 色值归一集（与 check 共用 parse_hex 口径）
    colors = (design.get("tokens") or {}).get("color") or {}
    hexes = set()
    for value in colors.values():
        # §7-5① dark 子块展开：嵌套 dict（dark 六角色）不再被静默跳过——暗色 hex 进白名单，
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
AUDIT_EXTS = (".html", ".css", ".js", ".ts", ".jsx", ".tsx", ".vue")

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


def in_token_scope(path, scopes):
    """路径是否落在 token_scope 内（归一绝对路径后按前缀判定）。"""
    p = os.path.normcase(os.path.abspath(path))
    for scope in scopes:
        if p == scope or p.startswith(scope + os.sep):
            return True
    return False


def resolve_token_scope(design, src):
    """token_scope 解析为归一绝对路径：相对项按 --src 解析、绝对项原样（裁定 10）。

    解析基 = `--src` 所在位置：目录形态即 src 本身（文档口径：`--src` 取项目根 src 或
    prototypes/）；文件形态取 dirname(src)——否则相对项会拼成 `<文件>/<相对项>` 这种
    永不命中的退化路径。命中判定仍是前缀包含（`in_token_scope`）：单文件形态下，相对项
    解析后恰好指向该文件（如 `--src …/src/app.css` + `[app.css]`）或绝对项为祖先目录/该
    文件时才跳过；相对项指祖先子树（`--src …/src/vendor/lib.css` + `[vendor]`）不命中
    ——要给单文件用相对项跳过，把 `--src` 给成目录，或写绝对项。
    """
    base = src if os.path.isdir(src) else os.path.dirname(src)
    scopes = []
    for entry in design.get("token_scope") or []:
        if not (isinstance(entry, str) and entry.strip()):
            continue
        raw = entry if os.path.isabs(entry) else os.path.join(base, entry)
        scopes.append(os.path.normcase(os.path.abspath(raw)))
    return scopes


def _rel_to(path, root):
    """相对化（跨盘等无法相对化时回退原值）。"""
    try:
        return display_path(os.path.relpath(path, root))
    except ValueError:
        return display_path(path)


def cmd_audit(args):  # trace: S-15 AC-15.2 TC-15.2.1 TC-14.3.2 one-off 色值/字号审计（归一比较，token 单一源）
    design, violations = read_design(args.design)
    rel = display_path(args.design)
    counts = {"files": 0, "skipped": 0, "skipped_dirs": 0}
    if design is None:
        return emit(receipt("audit", False, file=rel, violations=violations, counts=counts),
                    args.json)
    if not os.path.exists(args.src):
        violations.append(v("MISSING_FILE", display_path(args.src),
                            "src 不存在：%s——--src 取项目根 src 或 {output_dir}/prototypes"
                            % display_path(args.src)))
        return emit(receipt("audit", False, file=rel, violations=violations, counts=counts),
                    args.json)
    hex_ok = collect_token_hexes(design)
    fs_ok = collect_font_sizes(design)
    dark_pair = dark_pair_violation(design, os.path.basename(args.design))  # 裁定 C12-1：modes 核心消费价值
    if dark_pair:
        violations.append(dark_pair)
    scopes = resolve_token_scope(design, args.src)
    warnings = []
    skipped = 0
    pruned = 0
    src_is_dir = os.path.isdir(args.src)
    root = os.path.dirname(os.path.abspath(args.src)) if src_is_dir else None
    if src_is_dir:
        files = []
        for dirpath, dirs, names in os.walk(args.src):
            keep = []
            for d in dirs:
                if scopes and in_token_scope(os.path.join(dirpath, d), scopes):
                    pruned += 1
                else:
                    keep.append(d)
            dirs[:] = keep
            for name in sorted(names):
                if not name.endswith(AUDIT_EXTS):
                    continue
                fpath = os.path.join(dirpath, name)
                if scopes and in_token_scope(fpath, scopes):
                    skipped += 1
                    continue
                files.append(fpath)
    else:
        files = [] if (scopes and in_token_scope(args.src, scopes)) else [args.src]
        skipped = 1 if not files else 0
    if scopes and (skipped or pruned):
        warnings.append("token_scope 生效：跳过 %d 个目录 / %d 个文件（%s）"
                        % (pruned, skipped, "、".join(display_path(s) for s in scopes)))
    for fpath in files:
        ext = os.path.splitext(fpath)[1].lower()
        text = strip_comments(io.open(fpath, encoding="utf-8").read(), ext)
        where = _rel_to(fpath, root) if root else display_path(fpath)
        for value in iter_color_value_spans(text, ext):
            for m in HEX_RE.finditer(value):
                try:
                    norm = normalize_hex(m.group(0))
                except ValueError:
                    norm = None
                if norm not in hex_ok:
                    violations.append(v("one-off-color", where,
                                        "色值 %s 不在 design token（单一源违规）" % m.group(0)))
        for m in _FONT_SIZE_RE.finditer(text):
            val = m.group(1).strip()
            if not (val.startswith("var(") or val in fs_ok):
                violations.append(v("one-off-font-size", where,
                                    "font-size: %s 既非 var() 也非 token 字阶" % val))
    result = receipt("audit", not violations, file=rel, violations=violations, warnings=warnings,
                     counts={"files": len(files), "skipped": skipped, "skipped_dirs": pruned},
                     audited=len(files))
    return emit(result, args.json, ["audit：审计 %d 文件%s"
                                    % (len(files), "，跳过 %d" % skipped if skipped else "")])


# ---------------------------------------------------------------- transition（裁定 6/14）

def save_yaml_atomic(path, doc):
    """同目录 .tmp + os.replace 原子替换（照 diyc_lib.save_yaml_atomic 范式）。"""
    tmp = path + ".tmp"
    try:
        with io.open(tmp, "w", encoding="utf-8") as f:
            yaml.safe_dump(doc, f, allow_unicode=True, sort_keys=False,
                           default_flow_style=False)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise


def write_prev_snapshot(path):
    """重写既有产物前落 .prev 快照（逐字节复制 + 同目录 tmp + os.replace）。"""
    tmp = path + ".prev.tmp"
    with io.open(path, "rb") as f:
        data = f.read()
    try:
        with io.open(tmp, "wb") as f:
            f.write(data)
        os.replace(tmp, path + ".prev")
    except BaseException:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise


def dangling_design_refs(design_path, page_id):
    """stories.yaml 里 AC[].design_ref == page_id 的悬空 AC 清单（本技能只读，路由 diy-epics-stories）。"""
    stories_path = os.path.join(os.path.dirname(os.path.abspath(design_path)), "stories.yaml")
    if not os.path.isfile(stories_path):
        return []
    try:
        doc = load_yaml(stories_path)
    except yaml.YAMLError:
        return ["stories.yaml 解析失败——无法核对 AC[].design_ref 悬空项，请人工核对（路由 diy-epics-stories）"]
    out = []
    for story in doc.get("stories") or []:
        if not isinstance(story, dict):
            continue
        for ac in story.get("acceptance_criteria") or []:
            if isinstance(ac, dict) and ac.get("design_ref") == page_id:
                out.append("stories.yaml %s %s 的 design_ref=%s 已悬空——路由 diy-epics-stories 回写（本技能只读）"
                           % (story.get("id"), ac.get("id"), page_id))
    return out


def next_hint_for(src, dst, page_id):
    """迁移后点名下一步（状态闸 ≠ 质量闸：不重跑 check，改用回执点名）。"""
    if dst == "已移除":
        return "核对 AC[].design_ref 悬空项已路由 diy-epics-stories"
    table = {
        ("未开始", "结构稿中"): "写 prototypes/%s.html 结构稿（先出结构、经用户确认，再进详细规格）" % page_id,
        ("结构稿中", "待验收"): "跑 check / audit 自检全过，再请审查（diy-review 的 WDS 路径）",
        ("待验收", "已批准"): "用户批准（人裁，无自动后续步）——审查通过后页仍留 待验收，只报「待用户批准」",
        ("待验收", "结构稿中"): "按审查 findings 回修结构稿，改完重走 待验收",
        ("已批准", "结构稿中"): "重开：按变更信号改结构稿，改完重走 待验收",
        ("已移除", "结构稿中"): "恢复：重建结构稿并重走验收",
    }
    return table.get((src, dst), "继续设计工作流")


def _dup_page_ids(pages):
    seen, dups = set(), []
    for page in pages:
        if not isinstance(page, dict):
            continue
        pid = page.get("id")
        if not (isinstance(pid, str) and pid.strip()):
            continue  # 非字符串/空 ID 走 page_id_violations，不当重复键（列表不可哈希）
        if pid in seen and pid not in dups:
            dups.append(pid)
        seen.add(pid)
    return dups


def _transition_fail(args, violations, counts):
    return emit(receipt("transition", False, file=display_path(args.design),
                        violations=violations, counts=counts, page=args.page), args.json)


def cmd_transition(args):  # trace: S-14 AC-14.1 页状态迁移写回（9 条合法边；破坏性边追加 revisions）
    path = args.design
    rel = display_path(path)
    base_name = os.path.basename(path)
    doc, violations = load_design_doc(path)
    if doc is None:
        return _transition_fail(args, violations, {"pages": 0})
    problems = coerce_design(doc)[1]  # 只取形状问题清单（写回一律用原样文档，不用归一结果）
    if problems:
        return _transition_fail(args, [v("UNPARSABLE_YAML", rel, p) for p in problems],
                                {"pages": 0})
    raw_pages = doc.get("pages") if doc.get("pages") is not None else []
    if not isinstance(raw_pages, list):
        return _transition_fail(args, [v("UNPARSABLE_YAML", rel,
                                         "%s 的 pages 不是列表（形状异常）——拒绝写回" % rel)],
                                {"pages": 0})
    pages = raw_pages
    counts = {"pages": len(pages)}
    id_problems = page_id_violations(pages, base_name)
    if id_problems:
        return _transition_fail(args, id_problems, counts)
    dups = _dup_page_ids(pages)
    if dups:
        return _transition_fail(args, [v("DUPLICATE_ID", "%s pages[].id" % base_name,
                                         "页 ID 重复：%s——ID 是唯一引用键，先去重"
                                         % "/".join(str(d) for d in dups))], counts)
    page = next((p for p in pages if isinstance(p, dict) and p.get("id") == args.page), None)
    if page is None:
        return _transition_fail(args, [v("UNKNOWN_ID", "%s pages[%s]" % (base_name, args.page),
                                         "页 %s 不在 design.yaml 的 pages[] 中（ID 是唯一引用键）"
                                         % args.page)], counts)
    src = page.get("status") or PAGE_STATUS_INITIAL
    dst = args.to
    if src not in PAGE_STATUSES:
        return _transition_fail(args, [v("ENUM_INVALID",
                                         "%s pages[%s].status" % (base_name, args.page),
                                         "%s 的 status=%r 不在 %s——先修状态值再迁移"
                                         % (args.page, src, "/".join(PAGE_STATUSES)))], counts)
    if (src, dst) not in LEGAL_EDGES:
        legal = sorted({d for (s, d) in LEGAL_EDGES if s == src})
        return _transition_fail(args, [v("ILLEGAL_TRANSITION",
                                         "%s pages[%s].status" % (base_name, args.page),
                                         "非法迁移 %s → %s；从 %s 只能去 %s（合法边见 design.py "
                                         "transition 契约；跨态跳转须逐边走）"
                                         % (src, dst, src, "/".join(legal) or "（无出口）"))], counts)
    reason = (args.reason or "").strip()
    if dst == "已移除" and not reason:
        return _transition_fail(args, [v("EMPTY_FIELD",
                                         "%s pages[%s].removed_reason" % (base_name, args.page),
                                         "--to 已移除 必须给 --reason（移除原因，写进 removed_reason）")],
                                counts)
    if dst in GATED_TARGETS:
        gate = page_gate_violations(os.path.dirname(os.path.abspath(path)), page, base_name,
                                    "GATE_FAILED", "GATE_FAILED",
                                    required_states(doc.get("form_factor")))
        if gate:
            return _transition_fail(args, gate, counts)
    project = doc.get("project")
    if not isinstance(project, dict):
        return _transition_fail(args, [v("EMPTY_FIELD", base_name + " project",
                                         "project 缺失或不是映射——形状异常，拒绝写回")], counts)
    stamp = today()
    new_page = dict(page)
    new_page["status"] = dst
    if dst == "已移除":
        new_page["removed_reason"] = reason
    elif src == "已移除":
        new_page.pop("removed_reason", None)  # 恢复：清陈旧 reason（removed_reason 仅 已移除 时写）
    new_doc = {**doc, "pages": [new_page if p is page else p for p in pages],
               "project": {**project, "updated": stamp}}
    if dst == "已移除" or (src, dst) == ("已批准", "结构稿中"):
        # 破坏性边才追加 revisions（裁定 14）：纯推进不记
        new_doc["revisions"] = list(doc.get("revisions") or []) + [
            {"date": stamp, "change": args.page, "reason": reason or ("%s → %s" % (src, dst))}]
    warnings = dangling_design_refs(path, args.page) if dst == "已移除" else []
    write_prev_snapshot(path)  # 重写前落 .prev 快照（裁定 15）
    save_yaml_atomic(path, new_doc)
    result = receipt("transition", True, file=rel, page=args.page, violations=[], warnings=warnings,
                     counts={"pages": len(new_doc["pages"]),
                             "revisions": len(new_doc.get("revisions") or [])},
                     **{"from": src, "to": dst, "updated": stamp,
                        "next_hint": next_hint_for(src, dst, args.page)})
    return emit(result, args.json,
                ["transition：%s %s → %s" % (args.page, src, dst),
                 "下一步：%s" % result["next_hint"]])


# ---------------------------------------------------------------- CLI

def build_parser():
    ap = argparse.ArgumentParser(description="diy-design 检测/自检/校验/迁移引擎")
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("detect", help="检测 PRD 前端需求")
    d.add_argument("--project-root", default=".")
    d.add_argument("--instance", default=None)
    d.add_argument("--json", action="store_true")
    d.set_defaults(func=cmd_detect)
    for name, helptext, handler in (
            ("check", "易用性 / 无障碍 / 设计系统自检（判据 = 回执 violations[].code）",
             cmd_check),
            ("validate", "design.yaml 结构契约校验", cmd_validate)):
        p = sub.add_parser(name, help=helptext)
        p.add_argument("--design", required=True)
        p.add_argument("--previous", default=None,
                       help="旧稿快照（如 design.yaml.prev）：追加 ID 稳定对账")
        p.add_argument("--json", action="store_true")
        p.set_defaults(func=handler)
    a = sub.add_parser("audit", help="one-off 色值/字号审计（token 单一源）")
    a.add_argument("--design", required=True)
    a.add_argument("--src", required=True)
    a.add_argument("--json", action="store_true")
    a.set_defaults(func=cmd_audit)
    t = sub.add_parser("transition", help="页状态迁移写回（9 条合法边）")
    t.add_argument("--design", required=True)
    t.add_argument("--page", required=True)
    t.add_argument("--to", required=True, choices=list(PAGE_STATUSES))
    t.add_argument("--reason", default=None)
    t.add_argument("--json", action="store_true")
    t.set_defaults(func=cmd_transition)
    return ap


def main():  # trace: S-14 AC-14.1 子命令路由（utf-8 输出确定性）；D-10：compare 已删除
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = build_parser().parse_args()
    try:
        return args.func(args)
    except Exception as e:  # 顶层兜底（照 diyc.py）：未预期异常也出回执，绝不空 stdout 静默失败
        result = receipt(args.cmd, False, file=getattr(args, "design", None),
                         violations=[v("INTERNAL_ERROR", getattr(args, "design", None) or args.cmd,
                                       "未预期内部异常：%s: %s（操作可能部分完成，请核对现场后重试）"
                                       % (type(e).__name__, e))])
        return emit(result, getattr(args, "json", False))


if __name__ == "__main__":
    sys.exit(main())
