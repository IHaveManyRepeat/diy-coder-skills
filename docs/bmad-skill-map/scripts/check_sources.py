"""校验装配产物中每条技能的 sourceFiles 是否真实存在于基线 skillDir（项目副本）下。

用途：捕捉"提取时读了另一份副本（全局目录）"的问题。
校验对象是 raw/skill-map.json（装配后的最终口径），而非各模块原始文件。
"""
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, "raw")


def load(name):
    with open(os.path.join(RAW, name), encoding="utf-8") as f:
        return json.load(f)


def resolve(skill_dir, ref):
    """把各种路径写法还原为绝对路径候选。"""
    ref = (ref or "").strip()
    if not ref:
        return []
    ref = ref.replace("\\", "/")
    cands = []
    if os.path.isabs(ref) or (len(ref) > 1 and ref[1] == ":"):
        cands.append(ref)
    else:
        if ref.startswith("./"):
            ref = ref[2:]
        cands.append(os.path.join(skill_dir, ref))
        cands.append(os.path.join(skill_dir, os.path.basename(ref)))
        if ref.startswith(".claude/skills/"):
            cands.append(os.path.join(skill_dir, ref.split("/", 3)[-1]))
        # 形如 <skillDirName>/相对路径 的写法
        skill_name = os.path.basename(skill_dir)
        if ref.startswith(skill_name + "/"):
            cands.append(os.path.join(skill_dir, ref[len(skill_name) + 1:]))
    return cands


def main():
    baseline = {s["canonicalId"]: s for s in load("catalog-baseline.json")["skills"]}
    assembled = load("skill-map.json")
    rows, checked, bad = [], 0, 0
    for s in [item for items in assembled["modules"].values() for item in items]:
        cid = s.get("canonicalId")
        source_module = s.get("_source", "?")
        skill_dir = s.get("skillDir") or (baseline.get(cid) or {}).get("skillDir")
        refs = s.get("sourceFiles") or []
        if not skill_dir or not refs:
            continue
        miss = [r for r in refs
                if not any(os.path.exists(c) for c in resolve(skill_dir, r))]
        checked += len(refs)
        if miss:
            bad += len(miss)
            rows.append((source_module, cid, miss, skill_dir))

    print(f"检查 sourceFiles 引用 {checked} 处，失配 {bad} 处，涉及技能 {len(rows)} 条")
    for name, cid, miss, skill_dir in rows:
        print(f"\n[{name}] {cid}")
        print(f"  skillDir: {skill_dir}")
        for m in miss:
            print(f"  缺: {m}")


if __name__ == "__main__":
    main()
