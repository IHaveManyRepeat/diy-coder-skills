"""从 _bmad/_config 的双 CSV 构建规范化技能基线，并解析每个技能的实体目录。

输出: docs/bmad-skill-map/raw/catalog-baseline.json
"""
import csv
import glob
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
CFG = os.path.join(ROOT, "_bmad", "_config")
OUT = os.path.join(ROOT, "docs", "bmad-skill-map", "raw", "catalog-baseline.json")
SKILL_DIRS = [
    ("project", os.path.join(ROOT, ".claude", "skills")),
    ("global", os.path.expanduser("~/.claude/skills")),
]


def dir_names(base):
    return {os.path.basename(p) for p in glob.glob(os.path.join(base, "*")) if os.path.isdir(p)}


def main():
    with open(os.path.join(CFG, "skill-manifest.csv"), encoding="utf-8") as f:
        manifest = list(csv.DictReader(f))
    with open(os.path.join(CFG, "bmad-help.csv"), encoding="utf-8") as f:
        help_rows = [r for r in csv.DictReader(f) if r["skill"] != "_meta"]

    help_by = {}
    for r in help_rows:
        help_by.setdefault(r["skill"], []).append(r)

    index = [(tag, base, dir_names(base)) for tag, base in SKILL_DIRS]
    skills = []
    for row in manifest:
        cid = row["canonicalId"]
        found_tag = found_dir = None
        for tag, base, names in index:
            if cid in names:
                found_tag, found_dir = tag, os.path.join(base, cid).replace("\\", "/")
                break
        entries = help_by.get(cid, [])
        skills.append({
            "canonicalId": cid,
            "module": row["module"],
            "description": row["description"],
            "manifestPath": row["path"],
            "skillDir": found_dir,
            "location": found_tag,
            "installedAs": cid if found_dir else None,
            "helpEntries": [{
                "displayName": e["display-name"],
                "menuCode": e["menu-code"],
                "action": e["action"],
                "args": e["args"],
                "phase": e["phase"],
                "precededBy": e["preceded-by"],
                "followedBy": e["followed-by"],
                "required": e["required"],
                "outputLocation": e["output-location"],
                "outputs": e["outputs"],
            } for e in entries],
            "inHelpCatalog": bool(entries),
        })

    data = {
        "generated": "2026-09-13",
        "source": {
            "catalog": "_bmad/_config/bmad-help.csv",
            "manifest": "_bmad/_config/skill-manifest.csv",
        },
        "skillDirSearch": {tag: base.replace("\\", "/") for tag, base in SKILL_DIRS},
        "skills": skills,
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)

    missing = [s for s in skills if not s["skillDir"]]
    no_help = [s for s in skills if not s["inHelpCatalog"]]
    print("skills:", len(skills), "| 有实体:", len(skills) - len(missing), "| 缺实体:", len(missing))
    print("未登记进 help 目录:", len(no_help))
    for s in missing:
        print("  MISSING:", s["module"], s["canonicalId"])
    for s in no_help:
        print("  NO-HELP:", s["module"], s["canonicalId"])


if __name__ == "__main__":
    main()
