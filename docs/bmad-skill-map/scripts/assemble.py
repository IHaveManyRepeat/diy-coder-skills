"""合并子 agent 提取的各模块 JSON，产出统一技能全景数据。

输入: docs/bmad-skill-map/raw/module-*.json
输出: docs/bmad-skill-map/raw/skill-map.json（合并结果 + 校验统计）
"""
import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, "raw")
SOURCES = [
    "module-core.json",
    "module-bmm-a.json",
    "module-bmm-b.json",
    "module-bmb-automator.json",
    "module-tea-cis.json",
    "module-wds.json",
    "module-bmm-missing.json",
    "module-bmm-b-fixed.json",
]

# 旧版文件仅在找不到新版时兜底（新版整份替换其中的技能条目）
SUPERSEDED = {"module-bmm-b.json": "module-bmm-b-fixed.json"}

MODULE_ORDER = ["core", "bmm", "bmb", "tea", "cis", "wds", "automator"]
MODULE_NAMES = {
    "core": "Core 核心层",
    "bmm": "BMad Method 主流程",
    "bmb": "BMad Builder 构建器",
    "tea": "Test Architecture Enterprise",
    "cis": "Creative Intelligence Suite",
    "wds": "Web Design Studio",
    "automator": "BMad Automator 自动化",
}
NEVER = {"memory", "sync"}

MODULE_INTRO = {
    "core": "跨模块通用能力：头脑风暴、对抗评审、文档处理、规格提炼、定制覆盖",
    "bmm": "主线开发流程：从分析到规划、方案设计、迭代实现",
    "bmb": "元能力：构建与质检 Agent、工作流、模块本身",
    "tea": "测试架构企业版：风险驱动测试设计到追溯门禁的完整流水线",
    "cis": "创意智能套件：创新策略、问题求解、设计思维、叙事",
    "wds": "Web 设计工作室：从产品简报、触发映射到 UX 规格与交付",
    "automator": "自动化执行：无人值守跑通故事构建与审查循环",
}


def load(path):
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def normalize_kind(kind):
    text = (kind or "").lower()
    if "agent" in text:
        return "agent"
    if "workflow" in text or "流程" in text:
        return "workflow"
    if "util" in text or "工具" in text:
        return "utility"
    return "utility"


def normalize_step(step):
    return {
        "name": step.get("name") or step.get("titleZh") or step.get("id") or "",
        "descZh": step.get("descZh") or step.get("summaryZh") or step.get("file") or "",
        "optional": bool(step.get("optional")),
    }


def normalize_menu(menu):
    return [{
        "code": m.get("code") or "",
        "labelEn": m.get("labelEn") or "",
        "labelZh": m.get("labelZh") or "",
        "descZh": m.get("descZh") or "",
    } for m in (menu or [])]


def normalize_deps(dep):
    """统一 dependencies 形态：统一成 {phase, primary, records[]}。"""
    records = dep if isinstance(dep, list) else ([dep] if isinstance(dep, dict) else [])
    records = [r for r in records if isinstance(r, dict)]
    primary = next((r for r in records if r.get("phase")), records[0] if records else {})
    return {
        "phase": primary.get("phase"),
        "required": primary.get("required"),
        "args": primary.get("args"),
        "precededBy": primary.get("precededBy"),
        "followedBy": primary.get("followedBy"),
        "outputLocation": primary.get("outputLocation"),
        "outputs": primary.get("outputs"),
        "records": records if len(records) > 1 else [],
    }


def main():
    baseline = load(os.path.join(RAW, "catalog-baseline.json"))
    if baseline is None:
        sys.exit("缺少 catalog-baseline.json")

    skills, problems, sources_used = [], [], []
    for name in SOURCES:
        data = load(os.path.join(RAW, name))
        if data is None:
            problems.append(f"缺失模块文件: {name}")
            continue
        # 被新版取代的模块：仅保留新版未覆盖的条目（如 anytime 组）
        replacement = SUPERSEDED.get(name)
        if replacement:
            fresh = load(os.path.join(RAW, replacement))
            if fresh is not None:
                fresh_ids = {s.get("canonicalId") for s in fresh.get("skills", [])}
                data = dict(data, skills=[
                    s for s in data.get("skills", []) if s.get("canonicalId") not in fresh_ids
                ])
        sources_used.append({"file": name, "skills": len(data.get("skills", []))})
        for row in list(data.get("skills", [])) + list(data.get("catalogOnlySkills", [])):
            row.setdefault("canonicalId", "?")
            row["_source"] = name
            row["kind"] = normalize_kind(row.get("kind"))
            row["menu"] = normalize_menu(row.get("menu"))
            row["steps"] = [normalize_step(s) for s in (row.get("steps") or [])] or None
            row["dependencies"] = normalize_deps(row.get("dependencies"))
            skills.append(row)

    def score(s):
        return (len(s.get("menu") or []), len(s.get("steps") or []), len(s.get("notes") or ""))

    best, dupes = {}, []
    for s in skills:
        cid = s["canonicalId"]
        if cid not in best:
            best[cid] = s
            continue
        keep_new = score(s) >= score(best[cid])
        winner, loser = (s, best[cid]) if keep_new else (best[cid], s)
        dupes.append({"id": cid, "kept": winner["_source"], "dropped": loser["_source"]})
        best[cid] = winner

    skills = list(best.values())
    baseline_ids_all = {b["canonicalId"] for b in baseline["skills"]}
    baseline_dirs = {b["canonicalId"]: b.get("skillDir") for b in baseline["skills"]}
    for s in skills:
        cid = s["canonicalId"]
        if cid in NEVER or cid.rsplit("/", 1)[-1] in NEVER:
            s["neverDirect"] = True
        if cid not in baseline_ids_all:
            s["catalogEntryOnly"] = True
            s["module"] = "wds"
        # 实体路径以基线解析结果为准；解不出实体即为"仅目录登记"
        skill_dir = s.get("skillDir") or baseline_dirs.get(cid)
        if skill_dir:
            s["skillDir"] = skill_dir
            s["evidenceLevel"] = "local-source"
        else:
            s["skillDir"] = None
            s["evidenceLevel"] = "catalog-only"

    baseline_ids = {s["canonicalId"] for s in baseline["skills"]}
    covered = {s["canonicalId"] for s in skills}
    missing = sorted(baseline_ids - covered)
    extra = sorted(covered - baseline_ids)

    by_module = {}
    for s in skills:
        by_module.setdefault(s.get("module", "?"), []).append(s)
    for lst in by_module.values():
        lst.sort(key=lambda x: ((x.get("dependencies") or {}).get("phase") or "zz", x["canonicalId"]))

    extras_count = sum(1 for s in skills if s.get("catalogEntryOnly"))
    stats = {
        "baselineSkills": len(baseline_ids),
        "extractedSkills": len(skills),
        "baselineCovered": sum(1 for s in skills if not s.get("catalogEntryOnly")),
        "extraCatalogEntries": extras_count,
        "missingFromExtraction": missing,
        "extraBeyondBaseline": extra,
        "duplicates": dupes,
        "byModule": {m: len(v) for m, v in by_module.items()},
        "localSource": sum(1 for s in skills if s.get("evidenceLevel") == "local-source"),
        "catalogOnly": sum(1 for s in skills if s.get("evidenceLevel") == "catalog-only"),
        "withMenu": sum(1 for s in skills if s.get("menu")),
        "withSteps": sum(1 for s in skills if s.get("steps")),
    }

    phases = {}
    for s in skills:
        dep = s.get("dependencies") or {}
        ph = dep.get("phase") or "unphased"
        phases.setdefault(ph, []).append(s["canonicalId"])
    stats["byPhase"] = {k: len(v) for k, v in sorted(phases.items())}

    out = {
        "generated": "2026-09-13",
        "moduleOrder": MODULE_ORDER,
        "moduleNames": MODULE_NAMES,
        "moduleIntro": MODULE_INTRO,
        "neverCallDirectly": sorted(NEVER),
        "stats": stats,
        "problems": problems,
        "sources": sources_used,
        "modules": {m: by_module.get(m, []) for m in MODULE_ORDER},
    }
    dest = os.path.join(RAW, "skill-map.json")
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    print(json.dumps(stats, ensure_ascii=False, indent=1))
    if problems:
        print("PROBLEMS:", problems)
    print("written:", dest)


if __name__ == "__main__":
    main()
