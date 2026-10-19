# -*- coding: utf-8 -*-
"""diy-retrospective collect 命令域：门禁、空回执、警告降级与 collect 命令编排/人读输出。."""

import os

import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import display_path, emit_via, id_sort, nonempty, v  # noqa: E402

from retrospective_lib import BUG_LOG_FILE, EPICS_FILE, GATE_FILES, RETRO_FILE, ROUTE_BY_FILE, SPRINT_FILE, STORIES_FILE, TEST_PLAN_FILE, collect_metrics, doc_summaries, epic_bugs, epic_coverage, epic_ids, epic_stories_block, load_docs, next_epic_info, normalize_epic, prev_actions  # noqa: E402

# ---------------------------------------------------------------- 门禁

def gate_check(epic, docs, out_dir, project_root):
    """门禁：上游两件套在场且定稿 + epic 可解析 + 至少 1 个 已完成 story。
    返回 (passed, violations, route)。"""
    violations = []
    skills = []
    for filename, must_final in GATE_FILES:
        entry = docs[filename]
        show = display_path(os.path.join(out_dir, filename), project_root)
        if not entry["present"]:
            violations.append(v("MISSING_FILE", show,
                                "%s 不存在；先跑 %s 产出上游文档"
                                % (filename, ROUTE_BY_FILE[filename])))
            skills.append(ROUTE_BY_FILE[filename])
            continue
        if entry["err"] is not None:
            violations.append(v("UNPARSABLE_YAML", show,
                                "YAML 解析失败：%s" % entry["err"]))
            continue
        data = entry["data"]
        project = data.get("project") if isinstance(data, dict) else None
        status = project.get("status") if isinstance(project, dict) else None
        if must_final and status != "已定稿":
            violations.append(v("STATUS_MISMATCH", show + " project.status",
                                "%s 的 project.status 须为 已定稿（实为 %s）；先跑 %s 定稿"
                                % (filename, status if nonempty(status) else "未声明",
                                   ROUTE_BY_FILE[filename])))
            skills.append(ROUTE_BY_FILE[filename])

    known = epic_ids(docs)
    if not known:
        if not [x for x in violations if EPICS_FILE in x["where"]]:
            violations.append(v("UNKNOWN_ID", display_path(
                os.path.join(out_dir, EPICS_FILE), project_root) + " epics",
                "epics.yaml 无可解析的 epic 条目，无法定位目标 %s" % epic))
            skills.append("diy-epics-stories")
    elif epic not in known:
        violations.append(v("UNKNOWN_ID",
                            display_path(os.path.join(out_dir, EPICS_FILE), project_root)
                            + " epics",
                            "目标 epic %s 不在 epics.yaml（已知 %s）"
                            % (epic, "、".join(id_sort(known)))))
        skills.append("diy-epics-stories")
    else:
        block = epic_stories_block(epic, docs)
        if block["total"] == 0:
            violations.append(v("EMPTY_FIELD",
                                display_path(os.path.join(out_dir, STORIES_FILE),
                                             project_root) + " stories[epic=%s]" % epic,
                                "该 epic 下没有 story，无可回顾"))
            skills.append("diy-epics-stories")
        elif block["done"] == 0:
            violations.append(v("EMPTY_FIELD",
                                display_path(os.path.join(out_dir, STORIES_FILE),
                                             project_root) + " stories[epic=%s].status" % epic,
                                "该 epic 没有 已完成 story（回顾针对已交付工作）"))
            skills.append("diy-epics-stories")

    route = None
    if violations:
        unique = list(dict.fromkeys(skills))
        route = ("先跑 %s 补齐并定稿上游文档，再重跑本技能" % " / ".join(unique)
                 if unique else "先修复上游文档（解析失败或状态未定稿），再重跑本技能")
    return (not violations), violations, route

# ---------------------------------------------------------------- collect

def empty_payload(args, epic):
    out = os.path.normpath(os.path.abspath(args.output_dir)).replace("\\", "/")
    return {
        "ok": False,
        "command": "collect",
        "project_root": args.project_root,
        "output_dir": out,
        "epic": epic,
        "gate": {"passed": False, "files": {}, "route": None},
        "stories": None,
        "metrics": None,
        "bugs": [],
        "coverage": None,
        "prev_actions": [],
        "first_retro": True,
        "next_epic": None,
        "docs": {},
        "violations": [],
        "warnings": [],
        "counts": {},
    }

def collect_warnings(epic, docs, out_dir, project_root):
    """可选源缺席 / epic 未收尾 → 结构化 warning（不拒）。"""
    warnings = []
    for filename, why in ((SPRINT_FILE, "rounds / blocked / augment 统计退化为 0"),
                          (BUG_LOG_FILE, "缺陷按 epic 归属的统计退化为空"),
                          (TEST_PLAN_FILE, "AC 覆盖统计退化为空")):
        entry = docs[filename]
        show = display_path(os.path.join(out_dir, filename), project_root)
        if not entry["present"]:
            warnings.append(v("MISSING_FILE", show,
                              "%s 未找到：%s（不阻断回顾）" % (filename, why)))
        elif entry["err"] is not None:
            warnings.append(v("UNPARSABLE_YAML", show,
                              "%s 不可解析：%s" % (filename, entry["err"])))
    if docs[RETRO_FILE]["err"] is not None:
        warnings.append(v("UNPARSABLE_YAML",
                          display_path(os.path.join(out_dir, RETRO_FILE), project_root),
                          "retrospective.yaml 不可解析：上一份 retro 的承诺跟踪不可用"))
    block = epic_stories_block(epic, docs)
    if block["done"] < block["total"]:
        warnings.append(v("PENDING_DECISION",
                          display_path(os.path.join(out_dir, STORIES_FILE), project_root)
                          + " stories[epic=%s].status" % epic,
                          "epic 未收尾（%d/%d 已完成，待完成 %s）；partial 回顾需用户确认后"
                          "写 partial: true，否则先完成剩余 story 或刷新 sprint"
                          % (block["done"], block["total"],
                             "、".join(p["id"] for p in block["pending"]))))
    return warnings

def cmd_collect(args):
    root = os.path.abspath(args.project_root)
    out = os.path.abspath(args.output_dir)
    epic = normalize_epic(args.epic)
    docs = load_docs(out)
    payload = empty_payload(args, epic)
    payload["docs"] = doc_summaries(docs, root, out)

    if epic is None:
        payload["violations"] = [v("ENUM_INVALID", "args --epic",
                                   "epic 须为 E-<n> 或 <n>，实为 %s" % args.epic)]
        payload["gate"]["route"] = "传入 --epic E-<n>（或编号）后重跑本技能"
        emit_via(payload, args.json, human_collect)
        return 1

    passed, violations, route = gate_check(epic, docs, out, root)
    payload["gate"] = {"passed": passed, "files": payload["docs"], "route": route}
    payload["violations"] = violations
    if not passed:
        emit_via(payload, args.json, human_collect)
        return 1

    block = epic_stories_block(epic, docs)
    bugs = epic_bugs(epic, docs)
    coverage = epic_coverage(epic, docs)
    first_retro, prev = prev_actions(epic, docs)
    metrics = collect_metrics(epic, docs)

    payload["ok"] = True
    payload["stories"] = block
    payload["metrics"] = metrics
    payload["bugs"] = bugs
    payload["coverage"] = coverage
    payload["first_retro"] = first_retro
    payload["prev_actions"] = prev
    payload["next_epic"] = next_epic_info(epic, docs)
    payload["warnings"] = collect_warnings(epic, docs, out, root)
    payload["counts"] = {
        "stories": block["total"], "done": block["done"],
        "rounds": metrics["rounds_total"], "blocked": metrics["blocked_count"],
        "augment_fail": metrics["augment_fail"], "bugs": len(bugs),
        "prev_actions": len(prev), "tcs": coverage["tcs"],
    }
    emit_via(payload, args.json, human_collect)
    return 0

def human_collect(payload):
    if not payload["ok"]:
        if payload["violations"]:
            print("拒绝：")
            for item in payload["violations"]:
                print("- %s %s: %s" % (item["code"], item["where"], item["msg"]))
        else:   # 冗余防御：ok=False 必带 violation（当前不可达）
            print("拒绝：门禁未通过")
        print("路由：%s" % payload["gate"]["route"])
        return
    counts = payload["counts"]
    metrics = payload["metrics"]
    print("门禁通过：epic %s（stories %d，done %d）。"
          % (payload["epic"], payload["stories"]["total"], payload["stories"]["done"]))
    print("指标：rounds %d · blocked %d · augment fail %d · 缺陷 功能型 %d / "
          "非功能型 %d"
          % (metrics["rounds_total"], metrics["blocked_count"], metrics["augment_fail"],
             metrics["bugs"]["功能型"], metrics["bugs"]["非功能型"]))
    coverage = payload["coverage"]
    print("覆盖：AC %d 中 %d 有用例，缺口 %d %s"
          % (coverage["acs"], coverage["covered"], len(coverage["gaps"]),
             "（%s）" % "、".join(coverage["gaps"]) if coverage["gaps"] else ""))
    if payload["first_retro"]:
        print("接续：首份 retro（无上一份 action_items 可跟踪）")
    else:
        print("接续：回带上一份 retro 的 action_items %d 条" % counts["prev_actions"])
    nxt = payload["next_epic"]
    print("下一 epic：%s" % ("%s（共享 FR %s）"
                             % (nxt["id"], "、".join(nxt["shared_frs"]) or "无")
                             if nxt["exists"] else "未定义（回顾照做，行动项照留）"))
    for item in payload["warnings"]:
        print("警告 %s %s: %s" % (item["code"], item["where"], item["msg"]))
