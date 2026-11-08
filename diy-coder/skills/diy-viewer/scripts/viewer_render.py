"""diy-viewer 值渲染（CSS/JS 模板在 viewer_templates，slugify/标题 id 在 viewer_anchor）。"""

import re
from pathlib import Path

import viewer_refs as _refs
from viewer_anchor import mint_heading_id, reset_heading_ids
from viewer_anchor import slugify  # noqa: F401  再导出供 viewer_pages（assets 组锚）
from viewer_glossary import BADGE_VALUES
from viewer_labels import BADGE_CLASSES
from viewer_value_labels import (NULL_NA_KEYS, NULL_NA_LABEL, VALUE_LABELS,
                                 _VALUE_LABELS_CI)
from viewer_refs import (FOLDED_KEYS, FOLDED_NOTE_LEN, ORPHAN_IDS, REF_KEYS,
                         _diag_unmapped, asset_link, cell, doc_path_value,
                         esc, gloss, is_asset_path, is_doc_path, is_enum_key,
                         is_id_string, key_label, ref_cell, render_ref_list)
from viewer_templates import (COPY_JS, CSS,  # noqa: F401  再导出（viewer_pages 导入面不变）
                              PANE_JS, TOOLTIP_JS)


def resolve_instance(out_dir: Path, instance):
    # trace: S-16 AC-16.1 AC-16.2 TC-16.1.1 TC-16.2.1 D-9
    # 目录即实例：带实例名 → <output_dir>/<实例名>/；无 → 主线平铺零迁移。
    # 白名单首字符字母数字，天然拒绝点目录、分隔符与盘符注入；
    # 末字符禁点（对抗审查修复：Windows 目录名尾点被静默折叠，b. ≡ b 破坏实例隔离）
    if instance is None:
        return out_dir
    if not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9_-])?", instance):
        raise SystemExit(
            f"[diy-viewer] 非法实例名: {instance!r}（字母数字开头和结尾，中间可含 . _ -）")
    return out_dir / instance


def na_badge() -> str:
    """表态键 null（如 stack `choice: null`）的「不适用」态徽章；文案单源 viewer_value_labels。"""
    return f'<span class="badge b-neutral">{gloss(esc(NULL_NA_LABEL))}</span>'


def value_html(k: str, v) -> str:
    """标量值渲染：表态键 null → 「不适用」徽章；资产/文档路径 → 相对链接；
    枚举键 → 徽章；其余回落 cell() 纯文本（其余 null 仍是「—」）。"""
    if v is None and k in NULL_NA_KEYS:
        return na_badge()
    if is_asset_path(k):
        return asset_link(v)
    if is_doc_path(k):
        return doc_path_value(v)
    return badge(k, v) if is_enum_key(k) else cell(v)


def badge(key: str, v) -> str:
    # trace: 值感知——值不在词汇表（决策自由文本/route URL 等）→ 回落 cell() 纯文本；
    # None 与非标量同样回落 cell()（「—」/降级），不再输出字面 None
    if v is not None and not isinstance(v, (dict, list)):
        s = str(v).strip()
        if s.lower() in BADGE_VALUES:
            cls = BADGE_CLASSES.get(s.lower(), "neutral")
            text = _VALUE_LABELS_CI.get(s.lower(), s)
            return f'<span class="badge b-{cls}">{gloss(esc(text))}</span>'
        _diag_unmapped(s)
    return cell(v)


_RENDER_SOURCE = ""

def set_render_source(source) -> None:
    global _RENDER_SOURCE
    _RENDER_SOURCE = source or ""


def _copy_file_ref() -> str:
    doc = _refs._RENDER_DOC
    if not doc:
        return ""
    return f"{_RENDER_SOURCE}/{doc}.yaml" if _RENDER_SOURCE else f"{doc}.yaml"


def copy_button(rid: str) -> str:
    # 表格 ID 旁复制按钮，单击复制「文件 + 条目 ID」定位提示词（文案 A）
    return (f'<button class="copy-id" type="button" data-file="{esc(_copy_file_ref())}" '
            f'data-id="{esc(rid)}" title="复制定位提示词">复制</button>')


def render_table(items: list, with_row_ids: bool = True) -> str:
    headers: list = []
    for item in items:
        for k in item:
            if k not in headers:
                headers.append(k)
    th = "".join(f"<th>{gloss(esc(key_label(h)))}</th>" for h in headers)
    rows = []
    for item in items:
        rid = item.get("id") if with_row_ids else None
        tds = []
        for h in headers:
            v = item.get(h)
            html = value_html(h, v)
            if h == "id" and isinstance(rid, str) and rid:
                html += copy_button(rid)
            tds.append(f"<td>{html}</td>")
        anchor = f' id="{esc(rid)}"' if isinstance(rid, str) and rid else ""
        # trace: S-12 AC-12.2 TC-12.2.1 孤儿 must FR：行标红 + 徽章提示
        if isinstance(rid, str) and rid in ORPHAN_IDS:
            tds[0] = f'<span class="badge b-bad">{gloss("孤儿")}</span>' + tds[0]
            rows.append(f'<tr class="orphan"{anchor}>{"".join(tds)}</tr>')
        else:
            rows.append(f"<tr{anchor}>{''.join(tds)}</tr>")
    return (f'<div class="table-scroll"><table class="data">'
            f'<thead><tr>{th}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>')


def render_dict_fields(d: dict) -> str:
    def field(k, v):
        if k in REF_KEYS and is_id_string(v):
            return ref_cell(str(v))
        return value_html(k, v)

    # 行头键原文本身就是值词且渲染不换词（如 by_source 的
    # 卡点/穷举/交叉认证）→ 中性徽章；英文键名（type/priority 值词表也收英文）键标签异文，
    # 不符合同文条件，维持纯文本表头
    def head(k):
        label = key_label(k)
        if k in VALUE_LABELS and label == k:
            return f'<span class="badge b-neutral">{gloss(esc(label))}</span>'
        return gloss(esc(label))

    rows = "".join(
        f'<tr><th>{head(k)}</th><td>{field(k, v)}</td></tr>'
        for k, v in d.items()
    )
    return f'<table class="kv"><tbody>{rows}</tbody></table>'


def is_flat_dict(d) -> bool:
    return isinstance(d, dict) and all(not isinstance(x, (dict, list)) for x in d.values())


def render_compact_kv(d: dict) -> str:
    """紧凑 kv 表（字段竖排）：详情面板内的条目渲染。"""
    rows = "".join(
        f'<tr><th>{gloss(esc(key_label(k)))}</th>'
        f'<td>{value_html(k, v)}</td></tr>'
        for k, v in d.items()
    )
    return f'<table class="kv compact"><tbody>{rows}</tbody></table>'


def render_detail(node) -> str:
    """引用目标完整详情（供右侧面板）：引用字段显示为编号链接，可链式查看。"""
    if is_flat_dict(node):
        return render_compact_kv(node)
    scalars = {k: x for k, x in node.items() if not isinstance(x, (dict, list))}
    complex_ = {k: x for k, x in node.items() if isinstance(x, (dict, list))}
    out = render_compact_kv(scalars) if scalars else ""
    for k, x in complex_.items():
        out += render_value(k, x, 4)
    return out


def build_templates() -> str:
    """全量 ID 详情模板：点击编号链接时填充右侧面板。"""
    # trace: 详情模板按节点归属文档切换标签上下文（跨文档打开面板时 type 仍按源文档语义）
    # （状态定义在 viewer_refs 模块，跨件写/读走模块属性形态）
    reset_heading_ids()  # 模板批量与页面正文互不污染页内去重登记
    parts = []
    for i, h in _refs.ID_INDEX.items():
        prev, _refs._RENDER_DOC = _refs._RENDER_DOC, h.get("doc", "")
        try:
            parts.append(f'<template data-detail="{esc(i)}">{render_detail(h["node"])}</template>')
        finally:
            _refs._RENDER_DOC = prev
    return "".join(parts)


def render_value(key: str, v, depth: int, ctx=()) -> str:
    # 空修订史不渲染：revisions 是全产物通用段，新建产物常态为空列表，
    # 逐页留一块「展开修订历史（0 项）」纯属噪音（有记录才折叠展示）
    if key == "revisions" and isinstance(v, list) and not v:
        return ""
    if depth == 0:
        reset_heading_ids()  # Q-130：每顶层节一页内去重登记清零（节间互不污染）
    # retired 键在场即已裁废弃：活跃面照常、废料收折叠区（ret 侧 key 置空防二次标题/递归）
    if isinstance(v, list) and any(isinstance(x, dict) and "retired" in x for x in v):
        act, ret = _refs.split_retired(v)
        my_ctx = (ctx + ((False, key),)) if key else ctx
        body = _render_value_raw(key, act, depth, ctx) if act else ""
        return body + _refs.folded_section(
            _render_value_raw("", ret, depth, my_ctx), len(ret))
    out = _render_value_raw(key, v, depth, ctx)
    fold = key in FOLDED_KEYS or (key == "note" and isinstance(v, str) and len(v) > FOLDED_NOTE_LEN)
    if fold:
        n = len(v) if isinstance(v, list) else ""
        label = key_label(key) + (f"（{n} 项）" if n != "" else "")
        return (f'<details class="detail"><summary>展开{esc(label)}</summary>'
                f'<div class="d-body">{out}</div></details>')
    return out


def _render_value_raw(key: str, v, depth: int, ctx=()) -> str:
    # Q-130 全名制：标题 id 带祖先上下文（最近 id 祖先前缀；无 id 祖先→键路径链），
    # 防同页跨卡同键撞号；my_ctx 下传供子孙铸造（本键入链、卡片 id 段同路）
    lvl = min(depth + 2, 6)
    my_ctx = (ctx + ((False, key),)) if key else ctx
    hid = mint_heading_id(key, ctx) if key else ""
    title = f'<h{lvl} id="{hid}">{gloss(esc(key_label(key)))}</h{lvl}>' if key else ""
    if isinstance(v, dict):
        if not v:
            return title + '<p class="dim">（空）</p>'
        # plain（通俗速览）置顶、detail（过程详情）折叠置底，其余字段按原序渲染
        plain_html = (f'<p class="plain">{cell(v["plain"])}</p>'
                      if isinstance(v.get("plain"), str) else "")
        skip = {"plain", "detail"}
        scalars = {k: x for k, x in v.items()
                   if k not in skip and not isinstance(x, (dict, list))}
        complex_ = {k: x for k, x in v.items()
                    if k not in skip and isinstance(x, (dict, list))}
        detail_html = ""
        d = v.get("detail")
        if isinstance(d, str) and d.strip():
            detail_html = ('<details class="detail"><summary>展开过程详情</summary>'
                           f'<div class="d-body">{cell(d)}</div></details>')
        elif isinstance(d, (dict, list)):
            detail_html = ('<details class="detail"><summary>展开过程详情</summary>'
                           f'<div class="d-body">{render_value("", d, depth + 1, my_ctx)}</div></details>')
        out = title + plain_html
        if scalars:
            out += render_dict_fields(scalars)
        for k, x in complex_.items():
            out += render_value(k, x, depth + 1, my_ctx)
        return out + detail_html
    if isinstance(v, list):
        if not v:
            return title + '<p class="dim">（空）</p>'
        if key in REF_KEYS and all(isinstance(x, str) for x in v):
            return title + render_ref_list(v)
        # 含 plain/detail 的条目走卡片（速览行+折叠块形态），纯 flat 条目保持表格总览
        if all(is_flat_dict(x) for x in v) and not any(
                ("plain" in x or "detail" in x) for x in v if isinstance(x, dict)):
            return title + render_table(v)
        if all(isinstance(x, dict) for x in v):
            cards = []
            for x in v:
                cid = x.get("id")
                anchor = f' id="{esc(cid)}"' if isinstance(cid, str) and cid else ""
                card_ctx = (my_ctx + ((True, cid),)) if anchor else my_ctx
                cards.append(f'<div class="card"{anchor}>'
                             f'{render_value("", x, depth + 1, card_ctx)}</div>')
            return title + "".join(cards)
        # trace: 对抗审查修复——列表标量命中值词表（signals: icon/motion 等）时中文化，未命中原样；
        # 枚举键（如 spec-scan source）的列表元素逐个出中性徽章，
        # 与标量 badge 路径同规则：值命中词表 → 徽章，未命中 → 维持中文化纯文本
        lis = []
        for x in v:
            if is_enum_key(key) and x is not None and not isinstance(x, (dict, list)) \
                    and str(x).strip().lower() in BADGE_VALUES:
                lis.append(f"<li>{badge(key, x)}</li>")
                continue
            label = _VALUE_LABELS_CI.get(str(x).strip().lower()) if isinstance(x, str) else None
            lis.append(f"<li>{cell(label or x)}</li>")
        return title + "<ul>" + "".join(lis) + "</ul>"
    if key in REF_KEYS and is_id_string(v):
        return title + ref_cell(v)
    if v is None and key in NULL_NA_KEYS:  # 表态键 null → 「不适用」（与 value_html 同源）
        return title + f"<p>{na_badge()}</p>"
    if is_asset_path(key):
        return title + f"<p>{asset_link(v)}</p>"
    if is_doc_path(key):
        return title + f"<p>{doc_path_value(v)}</p>"
    return title + (badge(key, v) if is_enum_key(key) else f"<p>{cell(v)}</p>")
