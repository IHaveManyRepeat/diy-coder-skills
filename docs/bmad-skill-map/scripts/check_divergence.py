"""对比技能的项目本地副本与全局副本，找出内容不一致的条目。

发现背景：同名的全局副本可能是不同版本（如全局版带 workflow.md，项目版带 customize.toml），
如果安装脚本搬运的是全局副本，用户实际得到的流程与本文档描述会不一致。
"""
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, "raw")
PROJECT = "F:/code2/bmad-tool/.claude/skills"
GLOBAL = os.path.expanduser("~/.claude/skills")


def inventory(root):
    files = set()
    for dirpath, _dirnames, filenames in os.walk(root):
        for fn in filenames:
            rel = os.path.relpath(os.path.join(dirpath, fn), root).replace("\\", "/")
            files.add(rel)
    return files


def main():
    with open(os.path.join(RAW, "catalog-baseline.json"), encoding="utf-8") as f:
        baseline = json.load(f)

    rows = []
    for s in baseline["skills"]:
        cid = s["canonicalId"]
        proj = os.path.join(PROJECT, cid)
        glob = os.path.join(GLOBAL, cid)
        proj_ok, glob_ok = os.path.isdir(proj), os.path.isdir(glob)
        if not proj_ok and not glob_ok:
            continue
        if proj_ok and not glob_ok:
            rows.append((cid, "仅项目副本", "", ""))
            continue
        if glob_ok and not proj_ok:
            rows.append((cid, "仅全局副本", "", ""))
            continue
        pf, gf = inventory(proj), inventory(glob)
        only_proj = sorted(pf - gf)
        only_glob = sorted(gf - pf)
        if only_proj or only_glob:
            rows.append((
                cid,
                "内容不一致",
                "；".join(only_proj[:6]) + ("…" if len(only_proj) > 6 else ""),
                "；".join(only_glob[:6]) + ("…" if len(only_glob) > 6 else ""),
            ))

    print(f"共 {len(baseline['skills'])} 条技能，发现 {len(rows)} 条副本差异：\n")
    header = f"{'技能':42} {'状态':10} 仅项目副本有的文件"
    print(header)
    print("-" * 110)
    for cid, status, op, og in rows:
        print(f"{cid:42} {status:10} {op}")
        if og:
            print(f"{'':54} 仅全局副本有的文件: {og}")

    dest = os.path.join(RAW, "copy-divergence.json")
    with open(dest, "w", encoding="utf-8") as f:
        json.dump([{"canonicalId": c, "status": st,
                    "onlyInProject": op, "onlyInGlobal": og}
                   for c, st, op, og in rows], f, ensure_ascii=False, indent=1)
    print("\nwritten:", dest)


if __name__ == "__main__":
    main()
