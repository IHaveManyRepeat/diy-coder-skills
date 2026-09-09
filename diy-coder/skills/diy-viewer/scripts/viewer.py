#!/usr/bin/env python3
"""diy-viewer: render diy-coder YAML artifacts (single source) into human-friendly HTML.

The YAML files are the single source of truth. This script only projects them
into disposable HTML under <output_dir>/<view_dir>/.

Usage:
    uv run --with pyyaml viewer.py --project-root . [yaml paths ...]
"""

import argparse
import html
import json
import re
import sys
import webbrowser
from pathlib import Path

import yaml

BADGE_KEYS = {"status", "priority", "state"}
ENUM_KEYS = BADGE_KEYS | {"type", "decision", "layer", "route", "verdict", "technique", "gate", "class", "subclass", "source"}
BADGE_CLASSES = {
    "final": "ok", "done": "ok", "pass": "ok", "passing": "ok", "must": "must",
    "draft": "dim", "could": "dim", "pending": "dim", "skipped": "dim",
    "in-progress": "warn", "in_review": "warn", "should": "warn", "wip": "warn",
    "blocked": "bad", "fail": "bad", "failed": "bad", "red": "bad",
    "blocking": "bad", "advisory": "warn",
}
KEY_RE = re.compile(r"[^a-z0-9]+")
META_KEYS = ("project", "x-project")
HTTP_METHODS = {"get", "put", "post", "delete", "options", "head", "patch", "trace"}

# 展示层中文标签：YAML 单一源保持英文 key/值不变，仅在渲染时映射。
KEY_LABELS = {
    "id": "编号", "title": "标题", "name": "名称", "status": "状态",
    "created": "创建日期", "updated": "更新日期", "description": "描述",
    "goal": "目标", "goals": "目标", "metric": "度量标准", "priority": "优先级",
    "type": "类型", "state": "状态", "project": "项目信息",
    "purpose": "项目定位", "users": "目标用户", "need": "核心需求",
    "features": "功能组", "requirements": "需求条目", "statement": "需求描述",
    "nfrs": "非功能需求", "out_of_scope": "不在范围内",
    "open_questions": "待决问题", "question": "问题", "answer": "结论",
    "strictness": "严格度",
    "decisions": "技术决策", "alternatives": "备选方案", "choice": "选定方案",
    "option": "选项", "rationale": "理由", "why": "理由", "why_not": "未选原因",
    "affects": "影响需求", "components": "组件", "responsibility": "职责",
    "stack": "技术栈", "depends_on": "依赖",
    "risks": "风险", "risk": "风险", "mitigation": "缓解措施",
    "epics": "史诗", "epic": "所属史诗", "feature_refs": "关联功能组",
    "stories": "故事", "story": "所属故事", "narrative": "用户故事",
    "acceptance_criteria": "验收标准", "ac": "验收标准",
    "given": "给定", "when": "当", "then": "那么", "refs": "关联需求",
    "test_cases": "测试用例", "steps": "验证步骤", "coverage_gaps": "覆盖缺口",
    "reason": "原因", "decision": "处理决定", "note": "备注", "notes": "备注",
    "method": "方法", "path": "路径", "operationId": "操作 ID",
    "summary": "摘要", "x-fr": "关联需求",
    "tasks": "任务", "blocked_reason": "阻塞原因", "test_refs": "关联用例",
    "evidence": "执行证据", "tc": "用例", "red": "红", "green": "绿",
    "review": "审查记录", "verdict": "结论", "findings": "发现清单",
    "layer": "层", "route": "路由",
    "loop": "迭代记录", "rounds": "修复轮数", "outcome": "结果", "at": "时间",
    "technique": "设计技术", "kill_target": "目标缺陷",
    "static_checks": "静态检查链", "order": "顺序", "tool": "工具",
    "kills": "消灭问题", "gate": "门禁",
    "bugs": "缺陷记录", "class": "大类", "subclass": "中类",
    "symptom": "症状", "root_cause": "根因", "pattern": "模式",
    "source": "来源", "date": "日期",
    "type": "小类", "trigger": "触发方法", "fix": "修复方案",
    "prevention": "根治机制", "taxonomy": "分类注册表",
}
VALUE_LABELS = {
    "draft": "草稿", "final": "已定稿", "pending": "待办",
    "in-progress": "进行中", "review": "待审查", "done": "已完成",
    "blocked": "已阻塞", "pass": "通过", "fail": "失败", "skipped": "已跳过",
    "must": "必须", "should": "应该", "could": "可选",
    "unit": "单元", "integration": "集成", "e2e": "端到端",
    "waived": "已豁免", "accept-gap": "接受缺口",
    "correctness": "正确性", "boundary": "边界", "coverage": "覆盖审计",
    "intent_gap": "意图缺口", "bad_spec": "规格缺陷", "patch": "小修", "defer": "后置",
    "equivalence": "等价类", "decision-table": "决策表", "state-transition": "状态迁移",
    "pairwise": "成对组合", "error-guessing": "错误猜测", "metamorphic": "蜕变测试",
    "property": "属性测试", "scenario": "场景",
    "blocking": "阻断", "advisory": "记录不阻断",
    "functional": "功能型", "non-functional": "非功能型",
    "logic": "逻辑", "data": "数据", "state": "状态",
    "performance": "性能", "UX": "用户体验", "security": "安全",
    "compatibility": "兼容性", "reliability": "可靠性",
    "dev": "开发", "audit": "审查发现", "falsification": "证伪轮", "user": "用户",
}
DOC_LABELS = {
    "prd": "产品需求文档", "architecture": "架构设计", "epics": "史诗列表",
    "stories": "故事列表", "test-plan": "测试计划", "openapi": "接口契约",
    "sprint": "冲刺任务",
    "bug-log": "缺陷模式库",
}
# ID 链：带 id 字段的条目卡片生成锚点；文本中命中的 ID 链接到其所在文档并带悬停预览。
# 引用型字段（REF_KEYS）在正文只显示编号链接；点击后右侧浮动详情面板展示完整内容
# （页面尾部以 <template> 预渲染全部 ID 详情，面板内链接可链式查看）。
ID_RE = re.compile(r"\b[A-Z]{1,4}-\d+(?:\.\d+)*\b")
ID_FULL_RE = re.compile(r"[A-Z]{1,4}-\d+(?:\.\d+)*")
REF_KEYS = {"affects", "refs", "depends_on", "feature_refs", "story", "test_refs", "ac", "epic", "x-fr"}
PREVIEW_KEYS = ("statement", "then", "title", "question", "goal", "risk", "name",
                "decision", "description", "narrative")
ID_INDEX: dict = {}


def key_label(k: str) -> str:
    return KEY_LABELS.get(k, k)


def _collect_ids(node, doc: str) -> None:
    if isinstance(node, dict):
        i = node.get("id")
        if isinstance(i, str) and i not in ID_INDEX:
            preview = next(
                (str(node[k]) for k in PREVIEW_KEYS
                 if isinstance(node.get(k), str) and node[k].strip()),
                i,
            )
            ID_INDEX[i] = {"doc": doc, "preview": preview[:120], "node": node}
        for v in node.values():
            _collect_ids(v, doc)
    elif isinstance(node, list):
        for x in node:
            _collect_ids(x, doc)


def is_id_string(v) -> bool:
    return isinstance(v, str) and ID_FULL_RE.fullmatch(v.strip()) is not None


def id_link(i: str, hit: dict) -> str:
    return (f'<a class="idl" href="{esc(hit["doc"])}.html#{esc(i)}"'
            f' title="{esc(hit["preview"])}">{esc(i)}</a>')


def render_compact_kv(d: dict) -> str:
    """紧凑 kv 表（字段竖排）：详情面板内的条目渲染。"""
    rows = "".join(
        f'<tr><th>{esc(key_label(k))}</th>'
        f'<td>{badge(k, v) if k in ENUM_KEYS else cell(v)}</td></tr>'
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


def render_ref_item(i: str) -> str:
    """单个 ID 引用：仅编号链接，详情点击后在右侧面板查看。"""
    hit = ID_INDEX.get(i.strip())
    if not hit:
        return esc(i)
    return id_link(i, hit)


def ref_cell(i: str) -> str:
    """正文引用字段：编号链接 + 目标摘要，审阅无需跳页。"""
    s = i.strip()
    hit = ID_INDEX.get(s)
    if not hit:
        return esc(i)
    out = id_link(i, hit)
    if hit["preview"] and hit["preview"] != s:
        out += f'<span class="refsum">{esc(hit["preview"])}</span>'
    return out


def render_ref_list(items: list) -> str:
    """ID 引用列表：纯编号链接。"""
    lis = []
    for x in items:
        hit = ID_INDEX.get(str(x).strip())
        if hit is None:
            lis.append(f"<li>{esc(x)}</li>")
        else:
            lis.append(f"<li>{id_link(str(x), hit)}</li>")
    return f'<ul class="reflist">{"".join(lis)}</ul>'


def build_templates() -> str:
    """全量 ID 详情模板：点击编号链接时填充右侧面板。"""
    return "".join(
        f'<template data-detail="{esc(i)}">{render_detail(h["node"])}</template>'
        for i, h in ID_INDEX.items()
    )


def build_id_index(docs: list) -> None:
    ID_INDEX.clear()
    for name, data in docs:
        _collect_ids(data, name)


def linkify(text: str) -> str:
    def sub(m):
        i = m.group(0)
        hit = ID_INDEX.get(i)
        if not hit:
            return i
        return (f'<a class="idl" href="{esc(hit["doc"])}.html#{esc(i)}"'
                f' title="{esc(hit["preview"])}">{i}</a>')

    return ID_RE.sub(sub, text)


def load_config(project_root: Path) -> dict:
    cfg_path = project_root / "diy-coder.yaml"
    cfg = {}
    if cfg_path.exists():
        try:
            cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as e:
            print(f"[diy-viewer] warning: cannot parse {cfg_path}: {e}", file=sys.stderr)
    paths = cfg.get("paths", {}) or {}
    return {
        "output_dir": paths.get("output_dir", "diy-output"),
        "view_dir": paths.get("view_dir", ".view"),
        "auto_open": bool((cfg.get("viewer", {}) or {}).get("auto_open", True)),
        "language": (cfg.get("project", {}) or {}).get("communication_language", "zh-CN"),
    }


def slugify(s: str) -> str:
    return KEY_RE.sub("-", str(s).strip().lower()).strip("-") or "x"


def esc(v) -> str:
    return html.escape(str(v), quote=True)


def cell(v) -> str:
    """Render a scalar value; keeps line breaks, highlights [ASSUMPTION]."""
    if v is None:
        return '<span class="dim">—</span>'
    if isinstance(v, (dict, list)):
        return f'<code class="dim">{esc(json.dumps(v, ensure_ascii=False, default=str))}</code>'
    text = esc(v)
    if text.startswith("[ASSUMPTION]"):
        return f'<span class="assume" title="assumption, needs confirmation">{linkify(text)}</span>'
    return linkify(text).replace("\n", "<br>")


def badge(key: str, v) -> str:
    cls = BADGE_CLASSES.get(str(v).strip().lower(), "neutral")
    text = VALUE_LABELS.get(str(v), str(v))
    return f'<span class="badge b-{cls}">{esc(text)}</span>'


def render_table(items: list, with_row_ids: bool = True) -> str:
    headers: list = []
    for item in items:
        for k in item:
            if k not in headers:
                headers.append(k)
    th = "".join(f"<th>{esc(key_label(h))}</th>" for h in headers)
    rows = []
    for item in items:
        tds = []
        for h in headers:
            v = item.get(h)
            tds.append(f"<td>{badge(h, v) if h in ENUM_KEYS else cell(v)}</td>")
        rid = item.get("id") if with_row_ids else None
        anchor = f' id="{esc(rid)}"' if isinstance(rid, str) and rid else ""
        rows.append(f"<tr{anchor}>{''.join(tds)}</tr>")
    return (f'<div class="table-scroll"><table class="data">'
            f'<thead><tr>{th}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>')


def render_dict_fields(d: dict) -> str:
    def field(k, v):
        if k in REF_KEYS and is_id_string(v):
            return ref_cell(str(v))
        return badge(k, v) if k in ENUM_KEYS else cell(v)

    rows = "".join(
        f'<tr><th>{esc(key_label(k))}</th><td>{field(k, v)}</td></tr>'
        for k, v in d.items()
    )
    return f'<table class="kv"><tbody>{rows}</tbody></table>'


def is_flat_dict(d) -> bool:
    return isinstance(d, dict) and all(not isinstance(x, (dict, list)) for x in d.values())


def render_value(key: str, v, depth: int) -> str:
    lvl = min(depth + 2, 6)
    title = f'<h{lvl} id="{slugify(key)}">{esc(key_label(key))}</h{lvl}>' if key else ""
    if isinstance(v, dict):
        if not v:
            return title + '<p class="dim">（空）</p>'
        scalars = {k: x for k, x in v.items() if not isinstance(x, (dict, list))}
        complex_ = {k: x for k, x in v.items() if isinstance(x, (dict, list))}
        out = title
        if scalars:
            out += render_dict_fields(scalars)
        for k, x in complex_.items():
            out += render_value(k, x, depth + 1)
        return out
    if isinstance(v, list):
        if not v:
            return title + '<p class="dim">（空）</p>'
        if key in REF_KEYS and all(isinstance(x, str) for x in v):
            return title + render_ref_list(v)
        if all(is_flat_dict(x) for x in v):
            return title + render_table(v)
        if all(isinstance(x, dict) for x in v):
            cards = []
            for x in v:
                cid = x.get("id")
                anchor = f' id="{esc(cid)}"' if isinstance(cid, str) and cid else ""
                cards.append(f'<div class="card"{anchor}>{render_value("", x, depth + 1)}</div>')
            return title + "".join(cards)
        return title + "<ul>" + "".join(f"<li>{cell(x)}</li>" for x in v) + "</ul>"
    if key in REF_KEYS and is_id_string(v):
        return title + ref_cell(v)
    return title + (badge(key, v) if key in ENUM_KEYS else f"<p>{cell(v)}</p>")


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
.idl{color:var(--accent);text-decoration:underline dotted;text-underline-offset:3px}
.idl:hover{background:#eef2f7;border-radius:3px}
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


def page(title: str, body: str, nav: str = "") -> str:
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
</main>
<aside id="refpane" aria-label="引用详情">
<div class="rp-head"><h3 id="rp-title"></h3>
<a class="src" id="rp-src" href="#">在原文档中打开 ↗</a>
<button class="rp-close" id="rp-close" type="button">✕ 关闭</button></div>
<div class="rp-body" id="rp-body"></div>
</aside>
{build_templates()}
<script>{PANE_JS}</script>
</body>
</html>
"""


def count_assumptions(node) -> int:
    if isinstance(node, str):
        return 1 if node.startswith("[ASSUMPTION]") else 0
    if isinstance(node, dict):
        return sum(count_assumptions(v) for v in node.values())
    if isinstance(node, list):
        return sum(count_assumptions(x) for x in node)
    return 0


def get_meta(data) -> dict:
    """Project meta block: `project` (diy docs) or `x-project` (OpenAPI extension)."""
    if not isinstance(data, dict):
        return {}
    for k in META_KEYS:
        if isinstance(data.get(k), dict):
            return data[k]
    return {}


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


def render_doc_page(name: str, data, others: list) -> str:
    meta = get_meta(data)
    meta_line = []
    if isinstance(meta, dict):
        for k in ("name", "status", "updated", "created"):
            if meta.get(k) is not None:
                meta_line.append(badge(k, meta[k]) if k == "status" else esc(meta[k]))
    n_open = count_assumptions(data)
    alert = (
        f'<div class="alert">⚠ 待确认假设 {n_open} 项 —— 即页面中黄底标注内容，逐条确认后方可定稿</div>'
        if n_open else ""
    )
    body = f'<p class="doc-meta">{" · ".join(meta_line)}</p>' + alert
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
        f'<a href="{esc(n)}.html">{esc(DOC_LABELS.get(n, n))}</a>' for n, _ in others if n != name
    ]
    return page(DOC_LABELS.get(name, name), body, " · ".join(links))


def build_index(docs: list) -> str:
    cards = []
    for name, data in docs:
        meta = get_meta(data)
        st = meta.get("status")
        status_html = badge("status", st) if st else ""
        n_open = count_assumptions(data)
        open_html = f'<span class="badge b-warn">待确认 {n_open}</span>' if n_open else ""
        cards.append(
            f'<a class="doc-card" href="{esc(name)}.html">'
            f'<div class="name">{esc(DOC_LABELS.get(name, name))}'
            f'<span class="sub"> {esc(name)}.yaml</span></div>'
            f'<div class="sub">{status_html} {open_html} {esc(meta.get("updated", ""))}</div></a>'
        )
    if not cards:
        body = '<p class="dim">未找到 YAML 文档。</p>'
    else:
        body = f'<div class="grid">{"".join(cards)}</div>'
    return page("diy-coder 文档索引", body)


def load_docs(paths) -> tuple:
    docs, errors = [], []
    for p in paths:
        try:
            data = yaml.safe_load(p.read_text(encoding="utf-8"))
        except (yaml.YAMLError, OSError) as e:
            errors.append(f"{p.name}: {e}")
            continue
        if data is None:
            errors.append(f"{p.name}: empty document")
            continue
        docs.append((p.stem, data))
    return docs, errors


def main() -> int:
    ap = argparse.ArgumentParser(description="diy-coder YAML → HTML viewer")
    ap.add_argument("--project-root", default=".", help="project root directory")
    ap.add_argument("--no-open", action="store_true", help="do not open the browser")
    ap.add_argument("files", nargs="*", help="specific yaml files (default: all under output_dir)")
    args = ap.parse_args()

    root = Path(args.project_root).resolve()
    cfg = load_config(root)
    out_dir = root / cfg["output_dir"]

    if not out_dir.exists():
        print(f"[diy-viewer] output dir not found: {out_dir}. Run a diy-* workflow first.", file=sys.stderr)
        return 1

    # ID 链接索引与跨文档导航必须基于全量文档构建，即使本次只渲染子集。
    all_docs, errors = load_docs(sorted(out_dir.glob("*.yaml")))
    docs = all_docs
    if args.files:
        req = {Path(f).name for f in args.files}
        docs = [(n, d) for n, d in all_docs if f"{n}.yaml" in req]
        for m in sorted(req - {f"{n}.yaml" for n, _ in all_docs}):
            errors.append(f"{m}: not found under {out_dir}")

    if errors:
        for e in errors:
            print(f"[diy-viewer] skipped — {e}", file=sys.stderr)

    view_dir = out_dir / cfg["view_dir"]
    view_dir.mkdir(parents=True, exist_ok=True)

    written = []
    build_id_index(all_docs)
    for name, data in docs:
        others = all_docs
        f = view_dir / f"{name}.html"
        f.write_text(render_doc_page(name, data, others), encoding="utf-8")
        written.append(f)
    index = view_dir / "index.html"
    index.write_text(build_index(all_docs), encoding="utf-8")

    print(f"[diy-viewer] rendered {len(written)} doc(s) -> {view_dir}")
    if errors:
        print(f"[diy-viewer] {len(errors)} file(s) skipped (see stderr)", file=sys.stderr)

    if cfg["auto_open"] and not args.no_open and docs:
        webbrowser.open(index.resolve().as_uri())
    return 0


if __name__ == "__main__":
    sys.exit(main())
