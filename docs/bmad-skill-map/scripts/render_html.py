"""把合并后的技能全景数据渲染为单文件 HTML（自包含，内嵌 JSON）。

输入: docs/bmad-skill-map/raw/skill-map.json
输出: docs/bmad-skill-map/index.html
"""
import html
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(BASE, "raw", "skill-map.json")
DEST = os.path.join(BASE, "index.html")

CSS = """
:root{--ink:#1a2333;--mut:#6b7280;--line:#e3e8ef;--bg:#f6f8fa;--card:#fff;
--accent:#2563eb;--ok:#0f7b47;--warn:#a15c07;--bad:#b42318;--dim:#6b7280}
*{box-sizing:border-box}
body{margin:0;font-family:"Segoe UI","Microsoft YaHei",system-ui,sans-serif;
color:var(--ink);background:var(--bg);line-height:1.65}
header.top{background:#fff;border-bottom:1px solid var(--line);padding:20px 28px;position:sticky;top:0;z-index:20}
header.top h1{margin:0 0 6px;font-size:20px}
header.top .sub{color:var(--mut);font-size:13px}
.wrap{display:flex;align-items:flex-start;gap:20px;padding:20px 28px 60px;max-width:1600px;margin:0 auto}
nav.side{position:sticky;top:96px;width:230px;flex:0 0 230px;background:var(--card);
border:1px solid var(--line);border-radius:10px;padding:12px}
nav.side a{display:block;padding:7px 10px;border-radius:6px;color:var(--ink);
text-decoration:none;font-size:13.5px}
nav.side a:hover{background:#eef2f7}
nav.side a .cnt{float:right;color:var(--mut);font-size:12px}
main{flex:1;min-width:0}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:18px 20px;margin-bottom:18px}
h2.mod{margin:0 0 4px;font-size:17px;display:flex;align-items:center;gap:10px}
h2.mod .pill{font-size:11px;font-weight:600;color:var(--accent);background:#eff4ff;
border:1px solid #cddcff;border-radius:99px;padding:1px 9px}
.mod-desc{color:var(--mut);font-size:13px;margin:0 0 14px}
h3.skill{margin:18px 0 8px;font-size:15px;display:flex;align-items:baseline;gap:9px;flex-wrap:wrap}
h3.skill .cid{font-family:Consolas,monospace;font-size:12.5px;color:var(--mut);font-weight:400}
table{width:100%;border-collapse:collapse;font-size:13px;background:var(--card);
border:1px solid var(--line);border-radius:8px;overflow:hidden}
th,td{padding:7px 10px;text-align:left;vertical-align:top;border-bottom:1px solid var(--line)}
thead th{background:#eef2f7;font-weight:600;font-size:12.5px}
tbody tr:last-child td{border-bottom:0}
tbody tr:hover td{background:#fafbfd}
code{font-family:Consolas,monospace;font-size:12.5px}
.tag{display:inline-block;font-size:11.5px;font-weight:600;padding:1px 8px;border-radius:99px;
border:1px solid transparent}
.t-must{color:#fff;background:var(--accent);border-color:var(--accent)}
.t-opt{color:var(--dim);background:#f3f4f6;border-color:#e0e2e6}
.t-local{color:var(--ok);background:#ecfdf3;border-color:#b7e7c8}
.t-cat{color:var(--warn);background:#fff8eb;border-color:#f3ddab}
.t-agent{color:#6d28d9;background:#f5f3ff;border-color:#ddd6fe}
.t-flow{color:#0e7490;background:#ecfeff;border-color:#a5f3fc}
.t-util{color:var(--mut);background:#f3f4f6;border-color:#e0e2e6}
.t-never{color:var(--bad);background:#fef2f2;border-color:#f3c1c1}
.sum{font-size:13.5px;margin:4px 0 10px}
.kv{font-size:12.5px;color:var(--mut);margin:0 0 8px}
.kv b{color:var(--ink);font-weight:600}
details.dep{margin:6px 0 0;font-size:12.5px}
details.dep summary{cursor:pointer;color:var(--accent)}
details.dep .box{padding:8px 12px;margin-top:6px;background:#f8fafc;border:1px solid var(--line);border-radius:8px}
.menu-code{font-family:Consolas,monospace;font-weight:600;color:var(--accent)}
.steps{counter-reset:st;margin:8px 0 0;padding:0;list-style:none}
.steps li{counter-increment:st;padding:5px 0 5px 30px;position:relative;font-size:13px;
border-bottom:1px dashed var(--line)}
.steps li:last-child{border-bottom:0}
.steps li::before{content:counter(st);position:absolute;left:0;top:5px;width:21px;height:21px;
border-radius:50%;background:#eef2f7;color:var(--mut);font-size:11.5px;text-align:center;line-height:21px}
.steps li.o::before{background:#fff3d6;color:var(--warn)}
.empty{color:var(--mut);font-size:12.5px;font-style:italic}
.stats{display:flex;flex-wrap:wrap;gap:10px;margin:10px 0 0}
.stat{background:#f8fafc;border:1px solid var(--line);border-radius:8px;padding:8px 14px;font-size:12.5px;color:var(--mut)}
.stat b{display:block;font-size:19px;color:var(--ink)}
.alert{background:#fff8eb;border:1px solid #f3ddab;color:var(--warn);border-radius:8px;
padding:10px 14px;font-size:13px;margin-bottom:14px}
.alert-bad{background:#fef2f2;border-color:#f3c1c1;color:var(--bad)}
.phase-wrap{overflow-x:auto;padding-bottom:8px}
.phase-row{display:flex;gap:14px;min-width:max-content}
.phase-col{min-width:210px;max-width:250px;flex:0 0 auto}
.phase-col h4{margin:0 0 8px;font-size:12.5px;color:var(--mut);font-weight:600;text-transform:none}
.node{background:#fff;border:1px solid var(--line);border-left:3px solid var(--accent);
border-radius:7px;padding:6px 9px;margin-bottom:7px;font-size:12.5px}
.node .c{font-family:Consolas,monospace;font-weight:700;color:var(--accent);font-size:11.5px}
.node .n{color:var(--ink)}
.node .zh{display:block;color:var(--mut);font-size:11.5px}
footer{color:var(--mut);font-size:12px;padding:0 28px 40px;max-width:1600px;margin:0 auto}
"""


def esc(value):
    return html.escape(str(value if value is not None else ""))


def kind_tag(kind):
    text = (kind or "").lower()
    if "agent" in text or "人设" in text:
        return '<span class="tag t-agent">Agent 角色</span>'
    if "workflow" in text or "流程" in text:
        return '<span class="tag t-flow">工作流</span>'
    if "util" in text or "工具" in text:
        return '<span class="tag t-util">工具</span>'
    return f'<span class="tag t-util">{esc(kind or "未分类")}</span>'


def evidence_tag(level):
    if level == "local-source":
        return '<span class="tag t-local">本机已装</span>'
    return '<span class="tag t-cat">仅目录登记</span>'


def req_tag(required):
    if str(required).lower() in ("true", "是", "required"):
        return '<span class="tag t-must">必需门禁</span>'
    return '<span class="tag t-opt">可选</span>'


def menu_table(menu):
    if not menu:
        return '<div class="empty">无内部菜单（单一动作技能）</div>'
    rows = "".join(
        f"<tr><td><span class='menu-code'>{esc(m.get('code'))}</span></td>"
        f"<td>{esc(m.get('labelZh') or '—')}</td>"
        f"<td><code>{esc(m.get('labelEn') or '')}</code></td>"
        f"<td>{esc(m.get('descZh') or '')}</td></tr>"
        for m in menu
    )
    return (
        "<table><thead><tr><th style='width:64px'>菜单码</th><th style='width:22%'>中文名</th>"
        f"<th style='width:20%'>英文原名</th><th>说明</th></tr></thead><tbody>{rows}</tbody></table>"
    )


def steps_list(steps):
    if not steps:
        return '<div class="empty">无独立流程文件</div>'
    items = ""
    for s in steps:
        optional = bool(s.get("optional"))
        cls = " class='o'" if optional else ""
        flag = " <span class='tag t-opt'>可跳过</span>" if optional else ""
        items += f"<li{cls}><b>{esc(s.get('name'))}</b>{flag}<br>{esc(s.get('descZh') or '')}</li>"
    return f"<ul class='steps'>{items}</ul>"


def dep_block(dep, skill):
    if not dep:
        return '<div class="empty">无依赖登记</div>'
    pairs = [
        ("阶段", dep.get("phase")),
        ("参数", dep.get("args")),
        ("前置", dep.get("precededBy")),
        ("后续", dep.get("followedBy")),
        ("输出位置", dep.get("outputLocation")),
        ("产出物", dep.get("outputs")),
    ]
    body = "".join(
        f"<div><b>{esc(k)}：</b>{esc(v) if v else '—'}</div>" for k, v in pairs
    )
    never = ""
    if skill.get("neverDirect"):
        never = "<div style='color:#b42318'><b>注意：</b>该工具由系统内部调用，不应直接对用户暴露</div>"
    return f"<div class='box'>{body}{never}</div>"


def skill_block(s):
    cid = esc(s.get("canonicalId"))
    name = esc(s.get("displayName") or s.get("nameZh") or "")
    title = f"{name} <span class='cid'>{cid}</span>" if name else f"<span class='cid'>{cid}</span>"
    flags = kind_tag(s.get("kind")) + " " + evidence_tag(s.get("evidenceLevel"))
    if s.get("neverDirect"):
        flags += ' <span class="tag t-never">禁止直接调用</span>'
    dep = s.get("dependencies") or {}
    head = f"<h3 class='skill'>{title} {flags}</h3>"
    meta = (
        f"<div class='kv'><b>阶段</b> {esc(dep.get('phase') or '—')} ｜ "
        f"<b>门禁</b> {req_tag(dep.get('required'))} ｜ "
        f"<b>来源文件</b> {esc(', '.join(s.get('sourceFiles') or []) or '—')}</div>"
    )
    parts = [head, f"<div class='sum'>{esc(s.get('summaryZh') or '—')}</div>", meta]
    parts.append("<details class='dep'><summary>内部可选分支（菜单/动作）</summary>" + menu_table(s.get("menu")) + "</details>")
    parts.append("<details class='dep'><summary>流程步骤</summary>" + steps_list(s.get("steps")) + "</details>")
    parts.append("<details class='dep'><summary>依赖与产出</summary>" + dep_block(dep, s) + "</details>")
    if s.get("notes"):
        parts.append(f"<div class='alert' style='margin-top:8px'>备注：{esc(s['notes'])}</div>")
    return f"<div class='card' style='padding:14px 18px'>{''.join(parts)}</div>"


def phase_diagram(skills, module_names):
    phases = {}
    for s in skills:
        dep = s.get("dependencies") or {}
        phases.setdefault(dep.get("phase") or "未标阶段", []).append(s)

    def sort_key(p):
        return (p.startswith("未"), p)

    cols = ""
    for ph in sorted(phases, key=sort_key):
        nodes = ""
        for s in phases[ph]:
            code = s.get("menuCode") or s.get("code") or ""
            dep = s.get("dependencies") or {}
            title_cn = s.get("displayName") or s.get("nameZh") or s.get("canonicalId")
            must = " ●" if str(dep.get("required")).lower() == "true" else ""
            nodes += (
                f"<div class='node'><span class='c'>{esc(code)}{must}</span> "
                f"<span class='n'>{esc(title_cn)}</span>"
                f"<span class='zh'>{esc(s.get('canonicalId'))}</span></div>"
            )
        cols += f"<div class='phase-col'><h4>{esc(ph)}（{len(phases[ph])}）</h4>{nodes}</div>"
    return f"<div class='phase-wrap'><div class='phase-row'>{cols}</div></div>"


def build(data):
    stats = data["stats"]
    modules = data["modules"]
    names = data["moduleNames"]

    nav = ""
    sections = ""
    for mod in data["moduleOrder"]:
        items = modules.get(mod) or []
        if not items:
            continue
        nav += f"<a href='#mod-{mod}'>{esc(names.get(mod, mod))}<span class='cnt'>{len(items)}</span></a>"

    for mod in data["moduleOrder"]:
        items = modules.get(mod) or []
        if not items:
            continue
        cards = "".join(skill_block(s) for s in items)
        sections += (
            f"<section class='card' id='mod-{mod}'>"
            f"<h2 class='mod'>{esc(names.get(mod, mod))}<span class='pill'>{len(items)} 个技能</span></h2>"
            f"<div class='phase-wrap' style='margin:10px 0 6px'>{phase_diagram(items, names)}</div>"
            f"<h3 class='skill' style='margin-top:22px'>技能明细</h3>{cards}</section>"
        )

    problems = data.get("problems") or []
    alerts = ""
    if problems:
        alerts += f"<div class='alert alert-bad'>合并告警：{esc('；'.join(problems))}</div>"
    missing = stats.get("missingFromExtraction") or []
    if missing:
        alerts += f"<div class='alert'>未覆盖条目（{len(missing)}）：{esc('、'.join(missing))}</div>"

    stat_cards = "".join(
        f"<div class='stat'><b>{esc(v)}</b>{esc(k)}</div>"
        for k, v in [
            ("技能总数", stats.get("extractedSkills")),
            ("本机已装", stats.get("localSource")),
            ("仅目录登记", stats.get("catalogOnly")),
            ("含内部菜单", stats.get("withMenu")),
            ("含流程步骤", stats.get("withSteps")),
        ]
    )

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>BMAD 官方技能全景图</title>
<style>{CSS}</style>
</head>
<body>
<header class="top">
  <h1>BMAD 官方方法论技能全景图</h1>
  <div class="sub">7 个模块 ｜ 按模块划分技能与可选分支 ｜ 生成日期 {esc(data.get('generated'))} ｜ 数据源：_bmad/_config 目录清单 + 本机技能实体</div>
  <div class="stats">{stat_cards}</div>
</header>
<div class="wrap">
  <nav class="side">
    <a href="#overview" style="font-weight:600">总览</a>
    {nav}
  </nav>
  <main>
    <section class="card" id="overview">
      <h2 class="mod">总览</h2>
      <p class="mod-desc">本图按模块归纳 BMAD 全部官方技能，并展开三类可选分支：技能内部菜单/动作、技能之间的依赖编排、模块级的可选路径。</p>
      {alerts}
      <table>
        <thead><tr><th>模块</th><th style="width:90px">技能数</th><th>模块定位</th></tr></thead>
        <tbody>{''.join(
            f"<tr><td><a href='#mod-{m}'>{esc(names.get(m, m))}</a></td>"
            f"<td>{len(modules.get(m) or [])}</td><td>{esc((data.get('moduleIntro') or {}).get(m, ''))}</td></tr>"
            for m in data['moduleOrder'] if modules.get(m)
        )}</tbody>
      </table>
    </section>
    {sections}
  </main>
</div>
<footer>生成脚本：docs/bmad-skill-map/scripts/render_html.py ｜ 原始数据：docs/bmad-skill-map/raw/skill-map.json ｜ 全部英文术语保留原文，说明文字为中文</footer>
</body>
</html>
"""


def main():
    with open(SRC, encoding="utf-8") as f:
        data = json.load(f)
    with open(DEST, "w", encoding="utf-8") as f:
        f.write(build(data))
    print("written:", DEST)


if __name__ == "__main__":
    main()
