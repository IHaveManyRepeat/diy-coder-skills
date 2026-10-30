"""diy-viewer 专用渲染：distillate {text, src} 条目与 prd out_of_scope 两形态。"""

import viewer_refs as _refs
from viewer_refs import dangling_ref, esc, gloss, key_label, ref_cell, resolve_src_text
from viewer_render import cell


def _render_distillate_entries(key: str, entries: list, docs_by_name: dict) -> str:
    """distillate 四列表 {text, src} 专用渲染——text 列固定表头「内容」，src 走引用链。"""
    rows = []
    for item in entries:
        if not isinstance(item, dict):
            rows.append(f"<tr><td colspan=2>{esc(str(item))}</td></tr>")
            continue
        text = item.get("text", "")
        src = item.get("src")
        src_html = ""
        if src is not None:
            s = str(src).strip()
            hit = _refs.ID_INDEX.get(s)
            if hit is not None:
                src_html = ref_cell(s)
            elif s:
                src_html = dangling_ref(s)
        else:
            src_html = f'<span class="badge b-bad">{gloss("缺来源")}</span>'
        rows.append(f"<tr><td>{cell(text)}</td><td>{src_html}</td></tr>")
    th = f"<th>{gloss('内容')}</th><th>{gloss('来源')}</th>"
    return (f'<h3>{gloss(esc(key_label(key)))}</h3>'
            f'<div class="table-scroll"><table class="data">'
            f'<thead><tr>{th}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>')


def _render_out_of_scope(entries: list, docs_by_name: dict) -> str:
    """prd out_of_scope 两形态——继承 {src} 展开母体文本；自产 {id, statement} 照常。"""
    rows = []
    for item in entries:
        if not isinstance(item, dict):
            rows.append(f"<tr><td colspan=3>{esc(str(item))}</td></tr>")
            continue
        keys = set(item)
        if keys == {"src"}:
            src = str(item.get("src") or "").strip()
            text, err = resolve_src_text(src, docs_by_name)
            src_html = ref_cell(src) if _refs.ID_INDEX.get(src) else (
                dangling_ref(src) if src else
                f'<span class="badge b-bad">{gloss("缺来源")}</span>')
            if err:
                body = f'<span class="dangling">{esc(err)}</span>'
            else:
                body = cell(text)
            rows.append(f'<tr><td><span class="badge b-neutral">{gloss("继承")}</span></td>'
                        f"<td>{body}</td><td>{src_html}</td></tr>")
        elif keys == {"id", "statement"}:
            oid = item.get("id")
            anchor = f' id="{esc(str(oid))}"' if oid else ""
            rows.append(f'<tr{anchor}><td><span class="badge b-neutral">{gloss("自产")}</span></td>'
                        f"<td>{cell(item.get('statement'))}</td>"
                        f"<td>{ref_cell(str(oid)) if oid else ''}</td></tr>")
        else:
            rows.append(f'<tr><td><span class="badge b-bad">{gloss("形态非法")}</span></td>'
                        f'<td colspan=2>{esc(str(item))}</td></tr>')
    th = (f"<th>{gloss('形态')}</th><th>{gloss('内容')}</th><th>{gloss('来源')}</th>")
    return (f'<h3>{gloss("不在范围内")}</h3>'
            f'<div class="table-scroll"><table class="data">'
            f'<thead><tr>{th}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>')


_DISTILLATE_DOCS = {"research", "brief", "prfaq"}
