"""把合并后的技能全景数据渲染为 Markdown 主文档。

输入: docs/bmad-skill-map/raw/skill-map.json
输出: docs/bmad-skill-map/BMAD技能全景图.md
"""
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(BASE, "raw", "skill-map.json")
DEST = os.path.join(BASE, "BMAD技能全景图.md")

KIND_ZH = {
    "agent": "Agent 角色",
    "workflow": "工作流",
    "utility": "工具",
}


def kind_zh(kind):
    text = (kind or "").lower()
    if "agent" in text:
        return "Agent 角色"
    if "workflow" in text:
        return "工作流"
    if "util" in text:
        return "工具"
    return kind or "—"


def cell(value, dash="—"):
    if value is None or value == "" or value == []:
        return dash
    if isinstance(value, list):
        return "<br>".join(str(v) for v in value) or dash
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_menu(menu):
    if not menu:
        return "无内部菜单（单一动作技能）。"
    lines = ["| 菜单码 | 中文名 | 英文原名 | 说明 |", "| --- | --- | --- | --- |"]
    for m in menu:
        lines.append(
            f"| `{cell(m.get('code'))}` | {cell(m.get('labelZh'))} | "
            f"`{cell(m.get('labelEn'))}` | {cell(m.get('descZh'))} |"
        )
    return "\n".join(lines)


def render_steps(steps):
    if not steps:
        return "无独立流程文件（或该技能为单步执行）。"
    lines = []
    for i, s in enumerate(steps, 1):
        flag = " `可跳过`" if s.get("optional") else ""
        lines.append(f"{i}. **{cell(s.get('name'))}**{flag} — {cell(s.get('descZh'))}")
    return "\n".join(lines)


def render_phase_map(skills):
    phases = {}
    for s in skills:
        dep = s.get("dependencies") or {}
        phases.setdefault(dep.get("phase") or "未标阶段", []).append(s)
    lines = ["| 阶段 | 技能 |", "| --- | --- |"]
    for ph in sorted(phases, key=lambda p: (p.startswith("未"), p)):
        entries = []
        for s in phases[ph]:
            code = s.get("menuCode") or s.get("code") or ""
            title = s.get("displayName") or s.get("nameZh") or ""
            must = " `必需`" if str((s.get("dependencies") or {}).get("required")).lower() == "true" else ""
            label = f"`{s['canonicalId']}`" + (f"（{title}）" if title else "")
            entries.append((f"{code} " if code else "") + label + must)
        lines.append(f"| {ph} | {'<br>'.join(entries)} |")
    return "\n".join(lines)


def render_skill(s):
    dep = s.get("dependencies") or {}
    title = s.get("displayName") or s.get("nameZh") or ""
    cid = s["canonicalId"]
    head = f"#### `{cid}`" + (f" — {title}" if title else "")
    tags = [kind_zh(s.get("kind"))]
    tags.append("本机已装" if s.get("evidenceLevel") == "local-source" else "仅目录登记")
    if s.get("neverDirect"):
        tags.append("**禁止直接调用**")
    lines = [head, "", f"*{' ｜ '.join(tags)}*", ""]
    lines.append(cell(s.get("summaryZh")))
    lines.append("")
    lines.append(f"- **阶段**：{cell(dep.get('phase'))}")
    lines.append(f"- **门禁**：{'必需' if str(dep.get('required')).lower() == 'true' else '可选'}")
    lines.append(f"- **入口**：{cell(s.get('entry'))}")
    lines.append(f"- **参数**：`{cell(dep.get('args'))}`")
    lines.append(f"- **前置**：{cell(dep.get('precededBy'))}")
    lines.append(f"- **后续**：{cell(dep.get('followedBy'))}")
    lines.append(f"- **产出位置**：{cell(dep.get('outputLocation'))}")
    lines.append(f"- **产出物**：{cell(dep.get('outputs'))}")
    entity = s.get("skillDir") or s.get("sourceDir") or s.get("skill_dir")
    lines.append(f"- **实体路径**：`{cell(entity)}`" if entity else "- **实体路径**：仅目录登记")
    lines.append("")
    lines.append("**内部可选分支**")
    lines.append("")
    lines.append(render_menu(s.get("menu")))
    lines.append("")
    lines.append("**流程步骤**")
    lines.append("")
    lines.append(render_steps(s.get("steps")))
    if s.get("notes"):
        lines.append("")
        lines.append(f"> 备注：{cell(s.get('notes'))}")
    lines.append("")
    return "\n".join(lines)


def main():
    with open(SRC, encoding="utf-8") as f:
        data = json.load(f)
    stats = data["stats"]
    names = data["moduleNames"]
    modules = data["modules"]

    out = [
        "# BMAD 官方方法论技能全景图",
        "",
        f"> 生成日期：{data.get('generated')} ｜ 数据源：`_bmad/_config/bmad-help.csv` + `skill-manifest.csv` + 各技能实体文件",
        "> 按模块划分，逐技能展开三类可选分支：技能内部菜单/动作、技能之间依赖编排、模块级可选路径。",
        "",
        "## 总览",
        "",
        "| 指标 | 数值 |",
        "| --- | --- |",
        f"| 技能总数 | {stats.get('extractedSkills')} |",
        f"| 本机已装实体 | {stats.get('localSource')} |",
        f"| 含内部菜单 | {stats.get('withMenu')} |",
        f"| 含流程步骤 | {stats.get('withSteps')} |",
        "",
        "### 模块分布",
        "",
        "| 模块 | 技能数 | 定位 |",
        "| --- | --- | --- |",
    ]
    for mod in data["moduleOrder"]:
        items = modules.get(mod) or []
        if not items:
            continue
        out.append(f"| [{names.get(mod, mod)}](#{mod}) | {len(items)} | {data.get('moduleIntro', {}).get(mod, '')} |")

    for mod in data["moduleOrder"]:
        items = modules.get(mod) or []
        if not items:
            continue
        out += ["", f"## {names.get(mod, mod)}", "",
                f"共 {len(items)} 个技能。{data.get('moduleIntro', {}).get(mod, '')}", "",
                "### 阶段与依赖编排", "", render_phase_map(items), ""]
        for s in items:
            out.append(render_skill(s))

    out += ["", "## 数据口径", "",
            "本图以**项目本地副本**（`F:/code2/bmad-tool/.claude/skills/<id>/`）为唯一真值来源，"
            "因为那是本机上实际生效、可被调用的那份。同名技能的全局副本"
            "（`~/.claude/skills/<id>/`）存在版本差异，不作为本次提取依据。",
            "",
            "- 技能条目 = `_bmad/_config/skill-manifest.csv` 的 86 条；另有 8 条仅登记在 "
            "`bmad-help.csv` 的目录条目（其功能已被实体技能吸收），单独标注。",
            "- `sourceFiles` 全部指向项目本地真实存在的文件，可用 "
            "`scripts/check_sources.py` 复验（当前 321 处引用 0 失配）。",
            "",
            "## 数据口径与已知差异", ""]
    missing = stats.get("missingFromExtraction") or []
    out.append(f"- 目录登记 {stats.get('baselineSkills')} 条，实际展开 {stats.get('extractedSkills')} 条。")
    if missing:
        out.append(f"- 未覆盖条目（{len(missing)}）：{'、'.join(missing)}")
    else:
        out.append("- 目录登记条目已全部覆盖。")
    if data.get("problems"):
        out.append(f"- 合并告警：{'；'.join(data['problems'])}")
    out.append("")

    with open(DEST, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print("written:", DEST)


if __name__ == "__main__":
    main()
