# -*- coding: utf-8 -*-
"""diy-design check/validate 命令域：易用性自检与 design.yaml 结构契约校验。."""

import io

import os
import re
import sys

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import load_yaml, v  # noqa: E402

from design_a11y import SemanticChecker, collect_a11y_extras, collect_ds_violations, page_gate_violations, required_states, touch_target_min_for  # noqa: E402
from design_lib import PAGE_STATUSES, check_previous, contrast, dark_pair_violation, emit, norm_path, page_id_violations, read_design, receipt  # noqa: E402
CONTRAST_PAIRS = (
    ("text", "bg"), ("text", "surface"), ("text_muted", "bg"),
    ("text_muted", "surface"), ("accent_text", "accent"),
)
TEXT_CONTRAST_MIN = 4.5

# ---- design.yaml 顶层两键——形态/默认主题由「不并」改判「有承载」 ----
FORM_FACTORS = ("响应式 Web", "移动端", "桌面", "多端")  # 目标表面（写在什么上），与 frontend_framework 互补
MODES = ("亮", "暗", "双模")  # 默认主题模式；双模 触发 tokens 明暗对审计联动
# ---- pages[].meta 可选内容键（meta-content 判据级承载）----
META_KEYS = ("title", "description", "og_image")  # 三子键全可选；在场则须非空字符串

OPEN_QUESTION_STATUSES = ("待办", "已解决")

# 批 5b（裁 1b）：cm_refs 轻校验——CM-### 三位零填充（同 cis_method_lib.CM_RE 口径）
CM_REF_RE = re.compile(r"CM-\d{3}\Z")


def _validate_cm_refs(design, base, base_name, violations):
    """cm_refs 顶层引用位校验（批 5b 裁 1b 轻校验）：可选键——缺席零触。

    形状错（null / 非列表 / 非 CM-### / 空串 / 重复）恒判；解析核只在
    cis-method.yaml 在场时按 sessions[].id 做——文件缺席不判（不静默升格），
    文件损坏同样不判（设计引擎不越权判他产物完整性；输入面纪律管停下告知）。
    """
    if "cm_refs" not in design:
        return
    refs = design.get("cm_refs")
    where = base_name + " cm_refs"
    if not isinstance(refs, list):
        violations.append(v("UNPARSABLE_YAML", where,
                            "cm_refs 不是列表（可选顶层引用位，形如 [CM-###]）"))
        return
    seen = set()
    for i, ref in enumerate(refs):
        cell = "%s cm_refs[%d]" % (base_name, i)
        if not (isinstance(ref, str) and ref.strip()):
            if ref is None or isinstance(ref, str):
                violations.append(v("EMPTY_FIELD", cell,
                                    "cm_refs[%d] 为空（写非空 CM-### 或整键省略）" % i))
            else:
                violations.append(v("UNPARSABLE_YAML", cell,
                                    "cm_refs[%d]=%r 不是字符串（形如 CM-###）" % (i, ref)))
            continue
        rid = ref.strip()
        if not CM_REF_RE.fullmatch(rid):
            violations.append(v("UNPARSABLE_YAML", cell,
                                "cm_refs[%d]=%r 不是 CM-###（三位零填充）" % (i, rid)))
            continue
        if rid in seen:
            violations.append(v("DUPLICATE_ID", cell,
                                "cm_refs 的 %s 重复（同一记录只引一次）" % rid))
            continue
        seen.add(rid)
    # 解析核：cis-method.yaml 在场才按 id 判悬空；缺席/损坏不判
    cm_path = os.path.join(base, "cis-method.yaml")
    if not os.path.isfile(cm_path):
        return
    try:
        cm_doc = load_yaml(cm_path)
    except yaml.YAMLError:
        return
    ids = set()
    sessions = cm_doc.get("sessions") if isinstance(cm_doc, dict) else None
    if isinstance(sessions, list):
        for s in sessions:
            if isinstance(s, dict) and isinstance(s.get("id"), str):
                ids.add(s["id"].strip())
    for rid in sorted(seen):
        if rid not in ids:
            violations.append(v("UNKNOWN_ID", "%s cm_refs" % base_name,
                                "cm_refs 的 %s 不在 cis-method.yaml sessions[] 内" % rid))

def cmd_check(args):  # trace: S-14 AC-14.3 TC-14.3.1 TC-14.3.3 自检：fail 列违规清单（含形状问题）
    design, violations = read_design(args.design)
    rel = norm_path(args.design)
    if design is None:
        return emit(receipt("check", False, file=rel, violations=violations,
                            counts={"pages": 0, "prototypes": 0, "states": 0}), args.json)
    base = os.path.dirname(os.path.abspath(args.design))
    base_name = os.path.basename(args.design)
    tokens = (design.get("tokens") or {}).get("color") or {}
    pages = design.get("pages") or []
    # 触控下限按 form_factor 分档（桌面 24，其余/缺省 44）
    touch_min = touch_target_min_for(design.get("form_factor"))
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
    # 维度一（续）·双模暗色配对：对 dark 六角色算同款 5 组，阈值同 4.5:1；
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
        where = norm_path(proto)
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
        violations += collect_a11y_extras(where, text, touch_min)
        violations += collect_ds_violations(design, where, text)
    if getattr(args, "previous", None):
        violations += check_previous(design, args.previous, base_name)
    checked = {"contrast_pairs": contrast_pairs_checked,
               "signals": "states.signals 非色彩",
               "semantic_html": ["h1 唯一", "input 带 label", "img 带 alt"],
               "a11y_extras": ["触控目标 ≥%dpx" % touch_min,
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
    """open_questions 结构校验：id/question/status/answer 四字段与状态联动。"""
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
    """终门联动：已定稿 要求零 待办。"""
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
    rel = norm_path(args.design)
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
    # 顶层两键在场 + 值域（专项码首例——顶层键错误与条目字段错误不同层级，
    # 下游需要可 grep 的稳定锚）；dark 子块仅 双模 可有且必填
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
    required = required_states(design.get("form_factor"))  # 移动端 悬停 → 按压
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
        # meta 可选——在场才判，机械判仅一层
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
    _validate_cm_refs(design, base, base_name, violations)
    if getattr(args, "previous", None):
        violations += check_previous(design, args.previous, base_name)
    result = receipt("validate", not violations, file=rel, violations=violations,
                     counts={"pages": len(pages), "states": n_states,
                             "open_questions": len(design.get("open_questions") or [])})
    return emit(result, args.json, ["validate：%d 页" % len(pages)])
