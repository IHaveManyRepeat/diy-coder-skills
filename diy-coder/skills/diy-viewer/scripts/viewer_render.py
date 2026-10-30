"""diy-viewer 值渲染与 CSS/JS 模板。"""

import re
from pathlib import Path

import viewer_refs as _refs
from viewer_glossary import BADGE_VALUES, VALUE_LABELS, _VALUE_LABELS_CI
from viewer_labels import BADGE_CLASSES, KEY_RE
from viewer_refs import (FOLDED_KEYS, FOLDED_NOTE_LEN, ORPHAN_IDS, REF_KEYS,
                         _diag_unmapped, asset_link, cell, doc_path_value,
                         esc, gloss, is_asset_path, is_doc_path, is_enum_key,
                         is_id_string, key_label, ref_cell, render_ref_list)


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


def slugify(s: str) -> str:
    return KEY_RE.sub("-", str(s).strip().lower()).strip("-") or "x"


def value_html(k: str, v) -> str:
    """标量值渲染：资产/文档路径 → 相对链接；枚举键 → 徽章；其余回落 cell() 纯文本。"""
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
    parts = []
    for i, h in _refs.ID_INDEX.items():
        prev, _refs._RENDER_DOC = _refs._RENDER_DOC, h.get("doc", "")
        try:
            parts.append(f'<template data-detail="{esc(i)}">{render_detail(h["node"])}</template>')
        finally:
            _refs._RENDER_DOC = prev
    return "".join(parts)


def render_value(key: str, v, depth: int) -> str:
    # 空修订史不渲染：revisions 是全产物通用段，新建产物常态为空列表，
    # 逐页留一块「展开修订历史（0 项）」纯属噪音（有记录才折叠展示）
    if key == "revisions" and isinstance(v, list) and not v:
        return ""
    # retired 键在场即已裁废弃：活跃面照常、废料收折叠区（ret 侧 key 置空防二次标题/递归）
    if isinstance(v, list) and any(isinstance(x, dict) and "retired" in x for x in v):
        act, ret = _refs.split_retired(v)
        body = _render_value_raw(key, act, depth) if act else ""
        return body + _refs.folded_section(_render_value_raw("", ret, depth), len(ret))
    out = _render_value_raw(key, v, depth)
    fold = key in FOLDED_KEYS or (key == "note" and isinstance(v, str) and len(v) > FOLDED_NOTE_LEN)
    if fold:
        n = len(v) if isinstance(v, list) else ""
        label = key_label(key) + (f"（{n} 项）" if n != "" else "")
        return (f'<details class="detail"><summary>展开{esc(label)}</summary>'
                f'<div class="d-body">{out}</div></details>')
    return out


def _render_value_raw(key: str, v, depth: int) -> str:
    lvl = min(depth + 2, 6)
    title = f'<h{lvl} id="{slugify(key)}">{gloss(esc(key_label(key)))}</h{lvl}>' if key else ""
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
                           f'<div class="d-body">{render_value("", d, depth + 1)}</div></details>')
        out = title + plain_html
        if scalars:
            out += render_dict_fields(scalars)
        for k, x in complex_.items():
            out += render_value(k, x, depth + 1)
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
                cards.append(f'<div class="card"{anchor}>{render_value("", x, depth + 1)}</div>')
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
    if is_asset_path(key):
        return title + f"<p>{asset_link(v)}</p>"
    if is_doc_path(key):
        return title + f"<p>{doc_path_value(v)}</p>"
    return title + (badge(key, v) if is_enum_key(key) else f"<p>{cell(v)}</p>")


CSS = """
:root{--ink:#1a2333;--mut:#6b7280;--line:#e3e8ef;--bg:#f6f8fa;--card:#fff;
--accent:#1d4ed8;--ok:#15803d;--warn:#b45309;--bad:#b91c1c;--dim:#6b7280}
*{box-sizing:border-box}body{margin:0;font-family:"Segoe UI","Microsoft YaHei",
system-ui,sans-serif;color:var(--ink);background:var(--bg);line-height:1.65}
main{max-width:1080px;margin:0 auto;padding:32px 24px 64px}
header.top{background:#fff;border-bottom:1px solid var(--line);padding:14px 24px}
header.top .wrap{max-width:1080px;margin:0 auto;display:flex;justify-content:
space-between;align-items:baseline}header.top a{color:var(--accent);
text-decoration:none;font-size:.9em}h1{font-size:1.6em;margin:0 0 4px}
h2,h3,h4,h5,h6{margin:1.6em 0 .5em}h2{font-size:1.25em;border-bottom:
1px solid var(--line);padding-bottom:.3em}table{border-collapse:collapse;
width:100%;background:var(--card);border:1px solid var(--line);border-radius:
8px;overflow:hidden;font-size:.92em}th,td{padding:8px 12px;text-align:left;
vertical-align:top;border-bottom:1px solid var(--line)}thead th{background:
#eef2f7;font-weight:600}tbody tr:last-child td{border-bottom:none}
table.kv th{width:180px;background:#eef2f7;font-weight:600}ul{padding-left:22px}
.table-scroll{overflow-x:auto}table.data th,table.data td{white-space:nowrap}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;
padding:4px 18px;margin:10px 0}.card h3,.card h4,.card h5{margin:.7em 0 .3em}
.badge{display:inline-block;padding:1px 10px;border-radius:999px;font-size:.8em;
font-weight:600;border:1px solid transparent}.b-ok{color:var(--ok);background:
#ecfdf3;border-color:#b7e7c8}.b-warn{color:var(--warn);background:#fff8eb;
border-color:#f3ddab}.b-bad{color:var(--bad);background:#fef2f2;
border-color:#f3c1c1}.b-dim{color:var(--dim);background:#f3f4f6;
border-color:#e0e2e6}.b-must{color:#fff;background:var(--accent)}.b-neutral{
color:var(--ink);background:#eef2f7;border-color:var(--line)}
.assume{background:#fef9c3;padding:0 4px;border-radius:4px}.refsum{
color:var(--dim);font-size:.85em;margin-left:6px}
.dangling{color:var(--bad);font-weight:600}
.alert-bad{background:#fef2f2;border-color:#f3c1c1;color:var(--bad)}
tr.orphan td{background:#fef2f2}
.idl,.asset{color:var(--accent);text-decoration:underline dotted;text-underline-offset:3px}
.idl:hover{background:#eef2f7;border-radius:3px}
.asset:hover{background:#eef2f7;border-radius:3px}
.reflist{list-style:none;padding-left:0;margin:4px 0}
.reflist>li{margin:6px 0}
main{transition:margin-right .25s ease}
body.pane-open main{margin-right:46%}
#refpane{position:fixed;top:0;right:0;width:46%;height:100vh;background:var(--card);
border-left:1px solid var(--line);box-shadow:-6px 0 20px rgba(0,0,0,.08);
transform:translateX(105%);transition:transform .25s ease;overflow-y:auto;z-index:50}
#refpane.open{transform:translateX(0)}
#refpane .rp-head{position:sticky;top:0;background:var(--card);border-bottom:
1px solid var(--line);padding:12px 20px;display:flex;align-items:center;gap:12px;z-index:1}
#refpane .rp-head h3{margin:0;font-size:1.05em}
#refpane .rp-head .src{color:var(--accent);text-decoration:none;font-size:.85em;margin-left:auto}
#refpane .rp-close{border:1px solid var(--line);background:#fff;border-radius:6px;
padding:2px 10px;cursor:pointer;font-size:.85em;color:var(--ink)}
#refpane .rp-close:hover{background:#eef2f7}
#refpane .rp-body{padding:4px 20px 32px}
@media(max-width:860px){#refpane{width:100vw}body.pane-open main{margin-right:0}}
tr:target td{background:#fff8eb}
.card:target{border-color:var(--warn);box-shadow:0 0 0 3px #fff8eb}
.dim{color:var(--mut)}p{margin:.4em 0}
.doc-meta{color:var(--mut);font-size:.9em;margin-bottom:8px}
.alert{background:#fff8eb;border:1px solid #f3ddab;color:var(--warn);border-radius:
8px;padding:10px 16px;margin:0 0 18px;font-weight:600}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));
gap:16px}a.doc-card{display:block;background:var(--card);border:1px solid
var(--line);border-radius:10px;padding:18px 20px;text-decoration:none;
color:var(--ink);transition:box-shadow .15s}a.doc-card:hover{box-shadow:0 4px
14px rgba(0,0,0,.08)}a.doc-card .name{font-weight:700;color:var(--accent);
font-size:1.05em}a.doc-card .sub{color:var(--mut);font-size:.85em;margin-top:4px}
.term{border-bottom:1px dotted var(--accent);cursor:help}
.term:hover{background:#eef2f7;border-radius:3px}
#gloss-tip{position:fixed;display:none;z-index:99;max-width:340px;background:
#1a2333;color:#fff;font-size:.85em;line-height:1.5;padding:8px 12px;border-radius:
8px;box-shadow:0 4px 14px rgba(0,0,0,.25);pointer-events:none}
.plain{color:var(--mut);font-size:.95em;background:#f6f8fa;border-left:3px
solid #cbd5e1;padding:6px 12px;margin:6px 0 10px;border-radius:0 6px 6px 0}
details.detail{margin:10px 0 4px;border:1px dashed var(--line);border-radius:8px}
details.detail summary{cursor:pointer;padding:7px 14px;color:var(--mut);
font-size:.88em;user-select:none}
details.detail summary:hover{color:var(--accent)}
details.detail[open] summary{border-bottom:1px dashed var(--line)}
details.detail .d-body{padding:6px 14px 10px;font-size:.95em;color:var(--mut)}
.foot{color:var(--mut);font-size:.85em;border-top:1px solid var(--line);
margin-top:40px;padding-top:12px}
.copy-id{margin-left:6px;padding:0 6px;font-size:.8em;color:var(--mut);background:#f6f8fa;border:1px solid var(--line);border-radius:4px;cursor:pointer}
.copy-id:hover{color:var(--accent);border-color:var(--accent)}
"""


PANE_JS = """
(function(){
var pane=document.getElementById('refpane');
var body=document.getElementById('rp-body');
var title=document.getElementById('rp-title');
var src=document.getElementById('rp-src');
function closePane(){pane.classList.remove('open');document.body.classList.remove('pane-open');}
document.getElementById('rp-close').addEventListener('click',closePane);
document.addEventListener('keydown',function(e){if(e.key==='Escape')closePane();});
document.addEventListener('click',function(e){
  var a=e.target.closest('a.idl');
  if(!a)return;
  var id=(a.textContent||'').trim();
  var tpl=document.querySelector('template[data-detail="'+id+'"]');
  if(!tpl)return;
  e.preventDefault();
  title.textContent=id;
  src.setAttribute('href',a.getAttribute('href')||'#');
  body.innerHTML='';
  body.appendChild(tpl.content.cloneNode(true));
  pane.classList.add('open');
  document.body.classList.add('pane-open');
  pane.scrollTop=0;
});
})();
"""


TOOLTIP_JS = """
(function(){
var tip=null;
function show(t){
  if(!tip){tip=document.createElement('div');tip.id='gloss-tip';
  document.body.appendChild(tip);}
  tip.textContent=t.getAttribute('data-tip');
  tip.style.display='block';
  var r=t.getBoundingClientRect();
  var left=Math.max(8,Math.min(r.left,window.innerWidth-tip.offsetWidth-8));
  var top=r.bottom+6;
  if(top+tip.offsetHeight>window.innerHeight){top=r.top-tip.offsetHeight-6;}
  tip.style.left=left+'px';tip.style.top=top+'px';
}
function hide(){if(tip){tip.style.display='none';}}
document.addEventListener('mouseover',function(e){
  var t=e.target.closest('.term');
  if(t){show(t);}else{hide();}
});
document.addEventListener('scroll',hide,true);
})();
"""


COPY_JS = """
(function(){
document.addEventListener('click',function(e){
  var btn=e.target.closest('button.copy-id');if(!btn)return;
  var file=btn.getAttribute('data-file')||'',id=btn.getAttribute('data-id')||'';
  var text='请打开产物文件 '+file+'，定位条目 '+id+'，读取该条目的完整内容，然后按我的后续指令处理（解释/修改等）。';
  function done(){var old=btn.textContent;btn.textContent='已复制';
    setTimeout(function(){btn.textContent=old;},1200);}
  function legacy(){
    var ta=document.createElement('textarea');ta.value=text;
    ta.style.position='fixed';ta.style.top='-9999px';
    document.body.appendChild(ta);ta.select();
    var ok=false;try{ok=document.execCommand('copy');}catch(err){ok=false;}
    document.body.removeChild(ta);if(ok){done();}
  }
  if(!navigator.clipboard||!navigator.clipboard.writeText){legacy();return;}
  navigator.clipboard.writeText(text).then(done,legacy);
});
})();
"""
