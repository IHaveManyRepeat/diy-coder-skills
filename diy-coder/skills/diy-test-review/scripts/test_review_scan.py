# -*- coding: utf-8 -*-
"""diy-test-review scan 子命令面：发现 + 机械项检出 + convention baseline 采样。"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import display_path, emit_via, items, v  # noqa: E402

from test_review_discover import (  # noqa: E402
    _content_warnings, _pact_interaction_warnings, build_baseline, build_corpus,
    discover_scope, mechanical_scan, pact_config_paths,
)
from test_review_lib import (  # noqa: E402
    CONVENTION_KEYS, IMPLEMENTED_MECHANICAL, load_criteria,
)
# ---------------------------------------------------------------- scan

def cmd_scan(args):
    root = os.path.abspath(args.project_root)
    out = os.path.abspath(args.output_dir)
    criteria = load_criteria()
    files, excluded, pacts, warnings = discover_scope(args, root, out)
    files = sorted(files)
    payload = {"ok": False, "command": "scan", "project_root": args.project_root,
               "output_dir": os.path.normpath(out).replace("\\", "/"),
               "files": files, "excluded": sorted(excluded, key=lambda e: e["path"]),
               "mechanical": [], "baseline": {}, "violations": [], "warnings": warnings,
               "counts": {}}

    if not files:
        # 门禁（源"无测试文件 → Halt"）：零产出 + 一行路由
        payload["violations"] = [v(
            "MISSING_FILE", display_path(out, root) + "/<测试文件>",
            "scope 内未发现测试文件：先给 --paths 指定测试文件/目录，或先跑 "
            "diy-test-author 产出测试代码；匹配不到任何规则得到的 100 不是 100")]
        payload["counts"] = {"files": 0, "excluded": len(excluded), "mechanical": 0}
        emit_via(payload, args.json, human_scan)
        return 1

    pacts = pact_config_paths(root, out, pacts)
    mechanical = mechanical_scan(files, pacts, root)
    mechanical = [m for m in mechanical
                  if criteria.get(m["row"], {}).get("detect") == "mechanical"]
    warnings.extend(_content_warnings(files, root))
    warnings.extend(_pact_interaction_warnings(files, root))
    corpus, sampled = build_corpus(files, root, out)
    baseline = build_baseline(corpus, sampled, root)
    if baseline["baseline_unavailable"]:
        warnings.append(v("EMPTY_FIELD", "convention_baseline",
                          "评审集之外无语料：7 个惯例键全部未知，Convention 行一律 "
                          "PASS (n/a)（不得从评审文件自身推断惯例）"))
    # 机械集完整性（裁定 6：可扩不可缩）：criteria 声明的 mechanical 行必须都有引擎实现
    declared = {r for r, spec in criteria.items() if spec.get("detect") == "mechanical"}
    missing = sorted(declared - IMPLEMENTED_MECHANICAL)
    if missing:
        warnings.append(v("ENUM_INVALID", "criteria.yaml mechanical 集",
                          "声明的机械行无引擎实现（须补实现或回报登记）：%s"
                          % "、".join(missing)))

    payload["ok"] = True
    payload["mechanical"] = mechanical
    payload["baseline"] = baseline
    payload["counts"] = {"files": len(files), "excluded": len(excluded),
                         "mechanical": len(mechanical),
                         "pact_configs": len(pacts),
                         "corpus_size": baseline["corpus_size"],
                         "sampled": baseline["sampled"],
                         "by_row": _count_rows(mechanical)}
    emit_via(payload, args.json, human_scan)
    return 0


def _count_rows(entries):
    counts = {}
    for entry in entries:
        counts[entry["row"]] = counts.get(entry["row"], 0) + 1
    return counts


def human_scan(payload):
    if not payload["ok"]:
        for item in payload["violations"]:
            print("拒绝 %s %s: %s" % (item["code"], item["where"], item["msg"]))
        return
    counts = payload["counts"]
    print("扫描完成：测试文件 %d 个（excluded %d，pact 配置 %d，机械项 %d 条）"
          % (counts["files"], counts["excluded"], counts["pact_configs"],
             counts["mechanical"]))
    for entry in payload["mechanical"]:
        where = entry["file"] if entry["line"] is None else "%s:%d" % (entry["file"], entry["line"])
        print("- %s %s：%s" % (entry["row"], where, entry["note"]))
    baseline = payload["baseline"]
    print("惯例语料：%d 个（采样 %d）" % (baseline["corpus_size"], baseline["sampled"]))
    for key in CONVENTION_KEYS:
        entry = baseline["keys"][key]
        if "status" in entry:
            print("- %s: adopted=%d status=%s" % (key, entry["adopted"], entry["status"]))
        else:
            print("- %s: judged_by=llm（读采样文件判读，入产物 convention_baseline）" % key)
    for item in payload["warnings"]:
        print("警告 %s %s: %s" % (item["code"], item["where"], item["msg"]))
