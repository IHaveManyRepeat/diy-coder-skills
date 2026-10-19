# -*- coding: utf-8 -*-
"""diy-create-story collect 命令域：门禁后的 AC/TC/前序/决策/git 装配与人读输出。."""

import os

import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import display_path, emit_via, items, v  # noqa: E402

from story_context_lib import ARCH_FILE, SPRINT_FILE, STORIES_FILE, TEST_PLAN_FILE, ac_ids, base_payload, gate_check, git_intel, load_docs, missing_warning, read_decisions, read_prior, read_tcs, story_map  # noqa: E402

def cmd_collect(args):
    root = os.path.abspath(args.project_root)
    out = os.path.abspath(args.output_dir)
    docs = load_docs(out)
    payload = base_payload("collect", args, out)
    payload["story"] = args.story
    payload["epic"] = None
    payload["acs"] = []
    payload["tcs"] = []
    payload["prior"] = None
    payload["decisions"] = []
    payload["git"] = {"available": False, "commits": []}
    payload["suggestions"] = []
    warnings = []

    passed, violations, route, story_entry, suggestions = gate_check(docs, out, root, args.story)
    payload["violations"] = violations
    payload["gate"] = {"passed": passed, "route": route,
                       "files": {STORIES_FILE: docs[STORIES_FILE]["present"]}}
    payload["suggestions"] = suggestions

    for name, note in ((SPRINT_FILE, "sprint.yaml 缺席：前序情报与任务定位降级，story 选择退化为显式指定"),
                       (TEST_PLAN_FILE, "test-plan.yaml 缺席：TC 引用面为空（TDD 门将拦下缺覆盖任务，先跑 diy-test-design）"),
                       (ARCH_FILE, "architecture.yaml 缺席：决策引用面为空")):
        entry = docs[name]
        if entry["err"] is not None:
            warnings.append(v("UNPARSABLE_YAML", display_path(os.path.join(out, name), root),
                              "%s 不可解析：相关引用面降级" % name))
        elif not entry["present"]:
            warnings.append(missing_warning(out, name, note, root))

    if not passed:
        payload["warnings"] = warnings
        emit_via(payload, args.json, human_collect)
        return 1

    stories = story_map(docs[STORIES_FILE]["data"])
    acs = [ac for ac in items(story_entry, "acceptance_criteria") if isinstance(ac, dict)]
    ids = ac_ids(story_entry)
    tcs = read_tcs(docs, ids)
    prior = read_prior(docs, args.story, stories)
    decisions = read_decisions(docs)
    git, git_warnings = git_intel(root)
    warnings += git_warnings

    if not docs[TEST_PLAN_FILE]["present"]:
        tcs = []

    payload["ok"] = True
    payload["epic"] = story_entry.get("epic")
    payload["acs"] = acs
    payload["tcs"] = tcs
    payload["prior"] = prior
    payload["decisions"] = decisions
    payload["git"] = git
    payload["warnings"] = warnings
    payload["counts"] = {
        "acs": len(acs),
        "tcs": len(tcs),
        "decisions": len(decisions),
        "commits": len(git["commits"]),
        "files_recent": sum(len(c["files"]) for c in git["commits"]),
        "prior": 1 if prior else 0,
        "warnings": len(warnings),
    }
    emit_via(payload, args.json, human_collect)
    return 0

def human_collect(payload):
    if not payload["ok"]:
        print("拒绝：")
        for item in payload["violations"]:
            print("- %s %s: %s" % (item["code"], item["where"], item["msg"]))
        if payload.get("suggestions"):
            print("候选 story：%s" % "、".join(payload["suggestions"]))
        print("路由：%s" % payload["gate"]["route"])
        return
    counts = payload["counts"]
    print("目标 %s：AC %d · TC %d · 架构决策 %d · 前序 %s"
          % (payload["story"], counts["acs"], counts["tcs"], counts["decisions"],
             payload["prior"]["ref"] if payload["prior"] else "无"))
    if payload["git"]["available"]:
        print("git 情报：最近 %d 次提交（涉及文件 %d）"
              % (counts["commits"], counts["files_recent"]))
    else:
        print("git 情报：不可用（见 warnings）")
    for item in payload["warnings"]:
        print("警告 %s %s: %s" % (item["code"], item["where"], item["msg"]))
