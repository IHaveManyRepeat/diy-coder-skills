"""diy-viewer 页面组装与文档/资产/时间线页。"""

import datetime
import re
from pathlib import Path

import viewer_refs as _refs
from viewer_glossary import (CHAIN_RANK, DOC_LABELS, _DT_MAX, _NO_CHAIN)
from viewer_labels import HTTP_METHODS, META_KEYS
from viewer_refs import gloss, render_ref_item
from viewer_render import (COPY_JS, CSS, PANE_JS, TOOLTIP_JS, badge, build_templates,
                           cell, esc, render_table, render_value, set_render_source,
                           slugify)


def page(title: str, body: str, nav: str = "", source: str = "") -> str:
    # trace: B4 新鲜度 meta：页脚落生成时间与来源目录（含实例名），.view 落后于 YAML 一眼可见
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    src = f" · 来源 {esc(source)}" if source else ""
    foot = f'<footer class="foot">生成于 {stamp}{src}</footer>'
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<style>{CSS}</style>
</head>
<body>
<header class="top"><div class="wrap"><h1>{esc(title)}</h1><nav>{nav}</nav></div></header>
<main>
{body}
{foot}
</main>
<aside id="refpane" aria-label="引用详情">
<div class="rp-head"><h3 id="rp-title"></h3>
<a class="src" id="rp-src" href="#">在原文档中打开 ↗</a>
<button class="rp-close" id="rp-close" type="button">✕ 关闭</button></div>
<div class="rp-body" id="rp-body"></div>
</aside>
{build_templates()}
<script>{PANE_JS}</script>
<script>{TOOLTIP_JS}</script>
<script>{COPY_JS}</script>
</body>
</html>
"""


def count_assumptions(node, _seen=None) -> int:
    # trace: S-11 AC-11.1 TC-11.1.1 防环：自引用结构只访问一次（build_index 卡片在渲染隔离外，不得崩）
    if _seen is None:
        _seen = set()
    if isinstance(node, str):
        return 1 if node.startswith("[假设]") else 0
    if isinstance(node, dict):
        if id(node) in _seen:
            return 0
        _seen.add(id(node))
        return sum(count_assumptions(v, _seen) for v in node.values())
    if isinstance(node, list):
        if id(node) in _seen:
            return 0
        _seen.add(id(node))
        return sum(count_assumptions(x, _seen) for x in node)
    return 0


def get_meta(data) -> dict:
    """Project meta block: `project` (diy docs) or `x-project` (OpenAPI extension)."""
    if not isinstance(data, dict):
        return {}
    for k in META_KEYS:
        if isinstance(data.get(k), dict):
            return data[k]
    return {}


def _parse_created(raw):
    """created 两格式解析（`YYYY-MM-DD` | `YYYY-MM-DD HH:MM:SS`）；纯日期补当日
    零点（底单三项裁定：存量纯日期不回填、按当日零点参与排序）。缺失/空白/
    形状或数值非法 → None（排序面走链序兜底，不炸）。"""
    if not isinstance(raw, str):
        return None
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})(?: (\d{2}):(\d{2}):(\d{2}))?",
                     raw.strip())
    if not m:
        return None
    y, mo, d, h, mi, s = (int(g or 0) for g in m.groups())
    try:
        return datetime.datetime(y, mo, d, h, mi, s)
    except ValueError:
        return None


def _dynamic_ranks(all_docs: list) -> dict:
    """editorial-review / selfcheck 动态挂位（§7-5 甲）：读产物内最新一条记录的
    target，解析 stem 匹配在场链序产物 → 挂该产物紧后（同挂时 editorial-review
    前、selfcheck 后）；匹配不上（target 指任务书/技能/外部文档，或目标不在场
    /非链产物）→ 不给位，按通用桶序排。"""
    by_name = dict(all_docs)
    ranks = {}
    for name, key, pick in (
        ("editorial-review", "reviews",
         lambda r: r.get("target") if isinstance(r.get("target"), str) else None),
        ("selfcheck", "checks",
         lambda r: (r.get("target") or {}).get("path")
         if isinstance(r.get("target"), dict) else None),
    ):
        data = by_name.get(name)
        recs = data.get(key) if isinstance(data, dict) else None
        if not isinstance(recs, list) or not recs or not isinstance(recs[-1], dict):
            continue
        target = pick(recs[-1])
        if not isinstance(target, str) or not target.strip():
            continue
        stem = Path(target).stem
        if stem in by_name and stem in CHAIN_RANK:
            ranks[name] = CHAIN_RANK[stem] + (0.1 if name == "editorial-review" else 0.2)
    return ranks


def sort_docs(all_docs: list) -> list:
    """三桶全局序（底单 :387 段三项裁定落形）：桶一＝created 可解析组按值升序
    （值并列或不可解析者按链序位兜底排，非链排链后）；桶二＝非链产物（按文件
    名字母序）；桶三＝缺 created 组排最后（组内按链序位、无位按文件名）。动态
    挂位并入链序位参与兜底。返回新列表，不改入参。"""
    dyn = _dynamic_ranks(all_docs)

    def key(entry):
        name, data = entry
        rank = dyn.get(name)
        if rank is None:
            rank = CHAIN_RANK.get(name, _NO_CHAIN)
        raw = get_meta(data).get("created")
        parsed = _parse_created(raw)
        if parsed is not None:
            return (0, parsed, rank, name)
        if isinstance(raw, str) and raw.strip():
            # 有值但不可解析：有链位归桶一尾（链序兜底），非链落桶二（文件名序）
            if rank < _NO_CHAIN:
                return (0, _DT_MAX, rank, name)
            return (1, _DT_MAX, 0, name)
        return (2, _DT_MAX, rank, name)  # 缺 created：桶三（无位 → 按文件名殿后）

    return sorted(all_docs, key=key)


def render_openapi_section(data: dict) -> str:
    """OpenAPI doc extras: 3.1 sanity check + endpoint overview table."""
    alerts = []
    version = data.get("openapi")
    if not isinstance(version, str) or not version.startswith("3.1"):
        alerts.append(f"⚠ openapi 字段缺失或非 3.1（当前：{version}）——不符合 OpenAPI 3.1 语法")
    rows = []
    for path, item in (data.get("paths") or {}).items():
        if not isinstance(item, dict):
            continue
        for method, op in item.items():
            if method.lower() not in HTTP_METHODS or not isinstance(op, dict):
                continue
            fr = op.get("x-fr")
            rows.append({
                "method": method.upper(),
                "path": path,
                "operationId": op.get("operationId"),
                "summary": op.get("summary"),
                "x-fr": ", ".join(str(x) for x in fr) if isinstance(fr, list) else fr,
            })
    out = "".join(f'<div class="alert">{a}</div>' for a in alerts)
    if rows:
        out += '<h2 id="api-overview">接口总览</h2>' + render_table(rows)
    return out


def render_augment_panel(data, others: list) -> str:
    # trace: 2026-09-13 裁定——补测待裁断聚合面板：sprint 页集中列出 augment:失败 任务
    # 与其失败用例（跨 test-plan/stories 反查），裁断三途径同屏可见；无失败任务零输出
    fails = [t for t in (data.get("tasks") or [])
             if isinstance(t, dict) and t.get("augment") == "失败"]
    if not fails:
        return ""
    tp = next((d for n, d in others if n == "test-plan"), None)
    tc_by_id = {}
    if isinstance(tp, dict):
        for tc in tp.get("test_cases") or []:
            if isinstance(tc, dict) and isinstance(tc.get("id"), str):
                tc_by_id[tc["id"].strip()] = tc
    story_title = {}
    st = next((d for n, d in others if n == "stories"), None)
    if isinstance(st, dict):
        for s in st.get("stories") or []:
            if isinstance(s, dict) and isinstance(s.get("id"), str):
                story_title[s["id"].strip()] = str(s.get("title", "")).strip()
    rows = []
    for t in fails:
        sid = str(t.get("story", "")).strip()
        head = render_ref_item(sid) if sid else '<span class="dim">—</span>'
        title = story_title.get(sid)
        if title:
            head += f'<span class="refsum">{esc(title)}</span>'
        refs = t.get("test_refs") if isinstance(t.get("test_refs"), list) else []
        hits = []
        for r in refs:
            tc = tc_by_id.get(str(r).strip())
            if not isinstance(tc, dict) or tc.get("status") != "失败":
                continue
            item = render_ref_item(str(r))
            kt = str(tc.get("kill_target", "")).strip()
            if kt:
                item += f'<span class="refsum">{esc(kt)}</span>'
            n = tc.get("note")
            if isinstance(n, str) and n.strip():
                item += f'<div class="dim">{cell(n)}</div>'
            hits.append(item)
        hits_html = "<br>".join(hits) if hits else '<span class="dim">（test_refs 中无 fail 用例记录）</span>'
        rows.append(f"<tr><td>{head}</td><td>{hits_html}</td></tr>")
    return (
        '<h2 id="augment-panel">补测待裁断</h2>'
        f'<div class="alert alert-bad">⚠ {len(fails)} 个任务编码后验证未通过 —— '
        '裁断三途径：代码缺陷 → <code>python runner.py --reopen-failed</code> 批量重开修复；'
        '用例设计问题 → 直接更新 test-plan.yaml；规格问题 → 回 stories.yaml / prd.yaml 层处理</div>'
        f'<table class="data"><thead><tr><th>{gloss("任务")}</th>'
        f'<th>失败用例与目标缺陷</th></tr></thead><tbody>{"".join(rows)}</tbody></table>'
    )


def render_doc_page(name: str, data, others: list, source: str = "") -> str:
    _refs._RENDER_DOC = name  # trace: B1 文档级标签覆盖上下文
    set_render_source(source)  # trace: Q-003 复制按钮取 output_dir 相对路径（含实例名）
    meta = get_meta(data)
    meta_line = []
    if isinstance(meta, dict):
        for k in ("name", "status", "updated", "created"):
            if meta.get(k) is not None:
                meta_line.append(badge(k, meta[k]) if k == "status" else esc(meta[k]))
    n_open = count_assumptions(data)
    alert = (
        f'<div class="alert">⚠ {gloss("待确认假设")} {n_open} 项 —— 即页面中黄底标注内容，逐条确认后方可定稿</div>'
        if n_open else ""
    )
    # trace: S-12 AC-12.1 TC-12.1.1 悬空引用计入页面顶部告警
    dang = _refs.DANGLING_BY_DOC.get(name) or []
    if dang:
        ids = "、".join(f"<code>{esc(i)}</code>" for i in dang)
        alert += f'<div class="alert alert-bad">⚠ {gloss("悬空引用")}：{ids}（未定义的 ID）</div>'
    body = f'<p class="doc-meta">{" · ".join(meta_line)}</p>' + alert
    if name == "sprint":
        body += render_augment_panel(data, others)  # trace: 2026-09-13 裁定 补测待裁断面板
    if name == "openapi":
        body += render_openapi_section(data)
    for k, v in (data or {}).items():
        if k in META_KEYS:
            body += render_value(k, v, 0)
            break
    body += "".join(
        render_value(k, v, 0) for k, v in (data or {}).items() if k not in META_KEYS
    )
    links = ['<a href="index.html">⌂ 首页</a>'] + [
        f'<a href="{esc(n)}.html">{gloss(esc(DOC_LABELS.get(n, n)))}</a>' for n, _ in others if n != name
    ]
    return page(DOC_LABELS.get(name, name), body, " · ".join(links), source)


def build_index(docs: list, errors=None, source: str = "", extra_cards=()) -> str:
    cards = []
    for name, data in docs:
        meta = get_meta(data)
        st = meta.get("status")
        status_html = badge("status", st) if st else ""
        n_open = count_assumptions(data)
        open_html = f'<span class="badge b-warn">待确认 {n_open}</span>' if n_open else ""
        # trace: 2026-09-13 裁定——索引卡片露出补测待裁断数（不点进 sprint 页也可见）
        if name == "sprint":
            n_fail = len([t for t in (data.get("tasks") or [])
                          if isinstance(t, dict) and t.get("augment") == "失败"])
            if n_fail:
                open_html += f'<span class="badge b-bad">补测待裁断 {n_fail}</span>'
        cards.append(
            f'<a class="doc-card" href="{esc(name)}.html">'
            f'<div class="name">{gloss(esc(DOC_LABELS.get(name, name)))}'
            f'<span class="sub"> {esc(name)}.yaml</span></div>'
            f'<div class="sub">{status_html} {open_html} {esc(meta.get("updated", ""))}</div></a>'
        )
    # trace: C·12 W2——清单页/时间轴页的索引卡片（只在对应页面渲染时由 main 传入，只增不改）
    cards.extend(extra_cards)
    if not cards:
        body = '<p class="dim">未找到 YAML 文档。</p>'
    else:
        body = f'<div class="grid">{"".join(cards)}</div>'
    # trace: S-11 AC-11.1 TC-11.1.1 跳过的文件在索引中保留错误卡片（HTML 可见标记）
    if errors:
        body += (f'<div class="alert alert-bad">⚠ {len(errors)} 个文件未能渲染'
                 f'（形状异常、语法损坏或渲染失败）</div>'
                 + "<ul>" + "".join(f"<li>{esc(e)}</li>" for e in errors) + "</ul>")
    return page("diy-coder 文档索引", body, source=source)


def collect_asset_files(assets_dir: Path) -> dict:
    """assets/ 下全部文件按一级子目录（活动）分组：{活动: [相对路径...]}。
    目录缺失/为空/不可读 → {}（调用方据此不渲染清单页，不报错）。"""
    groups: dict = {}
    try:
        files = sorted(p for p in assets_dir.rglob("*") if p.is_file())
    except OSError:
        return {}
    for p in files:
        rel = p.relative_to(assets_dir)
        group = rel.parts[0] if len(rel.parts) > 1 else "（未分组）"
        groups.setdefault(group, []).append(rel.as_posix())
    return groups


def build_assets_page(groups: dict, source: str = "") -> str:
    """assets 产物清单页（裁定 C12-2 ①）：wds-assets 直出的 HTML/SVG/CSS 落在
    assets/<活动>/ 子目录，不在顶层 YAML 扫描面（8 活动全盲的根因）——此页按活动
    分组列出，逐文件给 output_dir 相对直链。"""
    sections = []
    for group in sorted(groups):
        items = "".join(
            f'<li><a class="asset" href="{esc(_refs._ASSET_REL_PREFIX + "assets/" + rel)}">'
            f'{esc("assets/" + rel)}</a></li>'
            for rel in groups[group])
        sections.append(
            f'<h2 id="assets-{esc(slugify(group))}">{esc(group)}'
            f'（{len(groups[group])} 件）</h2><ul>{items}</ul>')
    return page("资产产物清单", "".join(sections),
                '<a href="index.html">⌂ 首页</a>', source)


def collect_timeline(docs: list) -> list:
    """跨产物决策时间轴数据（Layer 1 裁定归入 C·12）：聚合全部产物的 revisions
    为 (date, 产物名, 条目) 并按 date 升序（ISO 日期字典序即时间序；缺 date 排最前）。
    与单产物页内的修订历史折叠块（render_value 的 revisions 分支）互不影响。"""
    items = []
    for name, data in docs:
        revs = data.get("revisions") if isinstance(data, dict) else None
        for r in revs or []:
            if isinstance(r, dict):
                items.append((str(r.get("date") or ""), name, r))
    items.sort(key=lambda t: t[0])
    return items


def build_timeline_page(items: list, source: str = "") -> str:
    """跨产物决策时间轴页：条目 = 日期 / 变更 / 原因 + 产物名锚（链到该产物页）。"""
    rows = []
    for _, name, r in items:
        doc_label = gloss(esc(DOC_LABELS.get(name, name)))
        rows.append(
            f'<tr><td>{cell(r.get("date"))}</td>'
            f'<td><a class="asset" href="{esc(name)}.html">{doc_label}</a></td>'
            f'<td>{cell(r.get("change"))}</td><td>{cell(r.get("reason"))}</td></tr>')
    body = ('<div class="table-scroll"><table class="data"><thead><tr>'
            '<th>日期</th><th>产物</th><th>变更</th><th>原因</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div>')
    return page("决策时间轴", body, '<a href="index.html">⌂ 首页</a>', source)
