"""diy-wds-scenarios 场景校验。"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import check_tokens, display_path, enum_check, nonempty, require, v, walk_strings  # noqa: E402

from wds_scenarios_lib import (
    ASSUMPTION_MARK, DESIGN_INTENT_ENUM, DESIGN_STATUS_ENUM, DESIGN_STATUS_INITIAL,
    DRIVER_ID_RE, INVENTORY_KEYS, PAGE_ID_RE, PAGE_REQUIRED, PAGE_SLUG_RE,
    RECORD_STATUS_ENUM, SCENARIO_ID_RE, SCENARIO_NESTED, SCENARIO_REQUIRED,
    SCOPE_ENUMS, SCOPE_REQUIRED, STATUS_ENUM, TG_ID_RE, TRIGGER_FILE,
    coverage_report, text_of, upstream_personas)



# ---------------------------------------------------------------- check

def check_scope(scope, where, final, out):
    """规模分析段（源 step-02 四件）。"""
    if not isinstance(scope, dict):
        out.append(v("EMPTY_FIELD", where, "scope 须为映射（site_type / scale / "
                                           "scenario_format / page_strategy）"))
        return
    for key, allowed in SCOPE_ENUMS:
        if nonempty(scope.get(key)):
            enum_check(scope.get(key), allowed, "%s.%s" % (where, key), key, out)
    if final:
        require(scope, SCOPE_REQUIRED, where, out)
    if final and isinstance(scope.get("page_strategy"), dict):
        strategy = scope["page_strategy"]
        if not nonempty(strategy.get("individual")) and not nonempty(strategy.get("templated")):
            out.append(v("EMPTY_FIELD", "%s.page_strategy" % where,
                         "逐页/模板化两类至少要落到一类（源 step-02 的页面文档化策略）"))


def check_inventory(inventory, where, final, out):
    """页清单（源 step-02 第 2 指令）：每条 `name` / `purpose`。"""
    if not isinstance(inventory, list):
        out.append(v("EMPTY_FIELD", where, "page_inventory 须为列表"))
        return
    if final and not inventory:
        out.append(v("EMPTY_FIELD", where, "页清单为空——覆盖矩阵无从核起"))
    for index, item in enumerate(inventory):
        ref = "%s[%d]" % (where, index)
        if not isinstance(item, dict):
            out.append(v("EMPTY_FIELD", ref, "页清单每条须为映射（name / purpose）"))
            continue
        require(item, INVENTORY_KEYS, ref, out)


def check_pages(record, ref, ctx):
    """`pages[]`：父子引用完整性 + 页号连续 + slug 与 ID 同源 + 非末页 exit_action。"""
    pages = record.get("pages")
    if pages is None:
        # 铸骨架时首条记录只带 id/name/status——页要到 04-outline 的循环里才长出来
        if ctx["final"]:
            ctx["out"].append(v("EMPTY_FIELD", "%s pages" % ref,
                                "场景至少要有一条页面记录（Q8 的最短路径）"))
        return
    if not isinstance(pages, list):
        ctx["out"].append(v("EMPTY_FIELD", "%s pages" % ref, "pages 须为列表（8 问的 Q8 路径）"))
        return
    if ctx["final"] and not pages:
        ctx["out"].append(v("EMPTY_FIELD", "%s pages" % ref, "场景至少要有一条页面记录"))
    sid = text_of(record.get("id"))
    for index, node in enumerate(pages):
        ref_p = "%s.pages[%d]" % (ref, index)
        if not isinstance(node, dict):
            ctx["out"].append(v("EMPTY_FIELD", ref_p, "页面记录须为映射"))
            continue
        pid = text_of(node.get("id"))
        if not nonempty(pid):
            ctx["out"].append(v("EMPTY_FIELD", "%s.id" % ref_p, "页面 ID 为空（须 SC-<nn>.P<n>）"))
        else:
            ctx["page_ids"].append(pid)
            match = PAGE_ID_RE.match(pid)
            if match is None:
                ctx["out"].append(v("ENUM_INVALID", "%s.id" % ref_p,
                                    "页面 ID 越界：%s（须 SC-<nn>.P<n> 两位场景号）" % pid))
            else:
                if nonempty(sid) and pid != "%s.P%s" % (sid, match.group(2)):
                    ctx["out"].append(v(
                        "SET_MISMATCH", "%s.id" % ref_p,
                        "页面 ID 前缀与所属场景不同源：页 %s 挂在 %s 下（父子引用完整性）"
                        % (pid, sid or "—")))
                if int(match.group(2)) != index + 1:
                    ctx["out"].append(v(
                        "SET_MISMATCH", "%s.id" % ref_p,
                        "页号不连续：第 %d 条记录的 ID 是 %s（阳光路径要求有序、连续、零分支）"
                        % (index + 1, pid)))
                slug = text_of(node.get("slug"))
                slug_match = PAGE_SLUG_RE.match(slug)
                if nonempty(slug) and slug_match is not None:
                    if (slug_match.group(1) != match.group(1)
                            or int(slug_match.group(2)) != int(match.group(2))):
                        ctx["out"].append(v(
                            "SET_MISMATCH", "%s.slug" % ref_p,
                            "展示名 %s 与引用键 %s 不同源（slug 的 NN.<p> 必须与 ID 一致）"
                            % (slug, pid)))
        require(node, PAGE_REQUIRED, ref_p, ctx["out"])
        if index < len(pages) - 1 and not nonempty(node.get("exit_action")):
            ctx["out"].append(v("EMPTY_FIELD", "%s.exit_action" % ref_p,
                                "非末页必须写清「什么动作带去下一步」（末页收在成功态）"))


def check_scenario(record, index, show, ctx):
    """单条 `scenarios[]` 记录（含三条交接契约键）。"""
    ref = "scenarios[%d]" % index
    if not isinstance(record, dict):
        ctx["out"].append(v("EMPTY_FIELD", "%s %s" % (show, ref), "记录须为映射"))
        return
    sid = text_of(record.get("id"))
    if not nonempty(sid):
        ctx["out"].append(v("EMPTY_FIELD", "%s %s.id" % (show, ref), "场景 ID 为空（须 SC-<nn>）"))
    elif SCENARIO_ID_RE.match(sid) is None:
        ctx["out"].append(v("ENUM_INVALID", "%s %s.id" % (show, ref),
                            "场景 ID 越界：%s（须 SC-<nn> 两位序号）" % sid))
    else:
        ctx["ids"].append(sid)
    if nonempty(record.get("status")):
        enum_check(record.get("status"), RECORD_STATUS_ENUM, "%s %s.status" % (show, ref),
                   "status", ctx["out"])
    priority = record.get("priority")
    if nonempty(priority) and str(priority).strip() not in ("1", "2", "3"):
        ctx["out"].append(v("ENUM_INVALID", "%s %s.priority" % (show, ref),
                            "priority 越界：%s（合法集 1|2|3）" % priority))
    intent = record.get("design_intent")
    if nonempty(intent):
        enum_check(intent, DESIGN_INTENT_ENUM, "%s %s.design_intent" % (show, ref),
                   "design_intent", ctx["out"])
    design_status = record.get("design_status")
    if nonempty(design_status):
        enum_check(design_status, DESIGN_STATUS_ENUM, "%s %s.design_status" % (show, ref),
                   "design_status", ctx["out"])
        if ctx["final"] and text_of(design_status) != DESIGN_STATUS_INITIAL:
            ctx["out"].append(v(
                "STATUS_MISMATCH", "%s %s.design_status" % (show, ref),
                "本技能只设初值 %s（实为 %s）——设计期的推进归 `diy-design` 的 WDS 线分支"
                % (DESIGN_STATUS_INITIAL, design_status)))
    if ctx["final"]:
        require(record, SCENARIO_REQUIRED, "%s %s" % (show, ref), ctx["out"])
        for head, leaf in SCENARIO_NESTED:
            node = record.get(head)
            if not isinstance(node, dict):
                ctx["out"].append(v("EMPTY_FIELD", "%s %s.%s" % (show, ref, head),
                                    "%s 须为映射（缺 %s）" % (head, leaf)))
            elif not nonempty(node.get(leaf)):
                ctx["out"].append(v("EMPTY_FIELD", "%s %s.%s.%s" % (show, ref, head, leaf),
                                    "必填键 %s 为空" % leaf))
        if text_of(record.get("status")) != RECORD_STATUS_ENUM[1]:
            ctx["out"].append(v("STATUS_MISMATCH", "%s %s.status" % (show, ref),
                                "--final 要求每条记录 status: %s，实为 %s"
                                % (RECORD_STATUS_ENUM[1], text_of(record.get("status")) or "空")))
    context = record.get("trigger_map_context")
    context = context if isinstance(context, dict) else {}
    target = text_of(context.get("target_group"))
    drivers = context.get("drivers")
    if isinstance(drivers, list):
        for index_d, driver in enumerate(drivers):
            text = text_of(driver)
            # 驱动因素 ID 形态（上游 `wds-trigger` 的方案）：`DF-<人物号>.<条号>+|-`
            # 兼容写法：`TG-<n>.…`（早期草案）。两种都从字符串里认出人物号再比。
            match = DRIVER_ID_RE.search(text) or TG_ID_RE.search(text)
            if match is not None and nonempty(target) and ("TG-%s" % match.group(1)) != target:
                ctx["out"].append(v(
                    "SET_MISMATCH", "%s %s.trigger_map_context.drivers[%d]" % (show, ref, index_d),
                    "所消费的驱动因素 %s 属另一人物群（本记录的人物是 %s）——"
                    "场景只消费自己那条链上的驱动" % (text, target)))
    if nonempty(target) and nonempty(record.get("name")) and ctx["people"]:
        person = ctx["people"].get(target)
        person_name = text_of((person or {}).get("name")) if isinstance(person, dict) else ""
        if nonempty(person_name) and person_name not in text_of(record.get("name")):
            ctx["out"].append(v("SET_MISMATCH", "%s %s.name" % (show, ref),
                                "场景名必须含人物名（骨律）：%s 里找不到 %s"
                                % (text_of(record.get("name")), person_name)))
    check_pages(record, "%s %s" % (show, ref), ctx)


def check_ids(ids, page_ids, show, out):
    """ID 链：唯一（重复 → DUPLICATE_ID）+ 顺序连续（跳号/重编 → SET_MISMATCH）。"""
    seen = set()
    for value in ids:
        if value in seen:
            out.append(v("DUPLICATE_ID", "%s scenarios[%s]" % (show, value),
                         "场景 ID 重复：%s（稳定 ID 不得复用）" % value))
        seen.add(value)
    for index, value in enumerate(ids):
        if SCENARIO_ID_RE.match(value) is not None and value != "SC-%02d" % (index + 1):
            out.append(v("SET_MISMATCH", "%s scenarios[%d].id" % (show, index),
                         "场景 ID 须顺序递增且不重编：第 %d 条应为 SC-%02d，实为 %s"
                         % (index + 1, index + 1, value)))
    counts = {}
    for value in page_ids:
        counts[value] = counts.get(value, 0) + 1
    for value, count in counts.items():
        if count > 1:
            out.append(v("DUPLICATE_ID", "%s %s" % (show, value),
                         "页面 ID 重复 %d 次（稳定 ID 不得复用）" % count))


def check_coverage(data, show, final, out):
    """★ 页面覆盖矩阵的机械核对（三条骨律之三：每页恰属一条战略链）。"""
    report = coverage_report(data)
    for name in report["duplicated"]:
        out.append(v("DUPLICATE_ID", "%s page_inventory[%s]" % (show, name),
                     "页清单里出现了两次同名页（展示名是覆盖矩阵的连接键，须唯一）"))
    for name in report["unassigned"]:
        out.append(v("SET_MISMATCH", "%s page_inventory[%s]" % (show, name),
                     "这一页没有分给任何场景——每页必须恰属一条战略链（漏配）"))
    for name in report["repeated"]:
        out.append(v("SET_MISMATCH", "%s page_inventory[%s]" % (show, name),
                     "这一页被分给了多于一条战略链（重复分配）——每页恰属一条"))
    for name in report["unknown"]:
        out.append(v("UNKNOWN_ID", "%s page_inventory[%s]" % (show, name),
                     "场景里出现了页清单之外的页——先回 page_inventory 补条再分配"))
    if final and report["total"] and report["covered"] != report["total"]:
        out.append(v("SET_MISMATCH", "%s page_inventory" % show,
                     "--final 要求覆盖率 100%%，实为 %s" % report["rate"]))
    return report


def check_document(data, show, args, output_dir):
    """全量校验；返回 (violations, warnings, counts, coverage)。"""
    violations = []
    warnings = []
    project = data.get("project")
    if not isinstance(project, dict):
        violations.append(v("EMPTY_FIELD", show + " project", "project 不是映射"))
        project = {}
    for key in ("name", "created", "updated", "status"):
        if not nonempty(project.get(key)):
            violations.append(v("EMPTY_FIELD", "%s.project.%s" % (show, key), "%s 为空" % key))
    status = text_of(project.get("status"))
    status_ok = status in STATUS_ENUM
    if nonempty(project.get("status")) and not status_ok:
        violations.append(v("ENUM_INVALID", show + ".project.status",
                            "status 越界：%s（合法集 %s）"
                            % (project.get("status"), "|".join(STATUS_ENUM))))

    check_scope(data.get("scope"), show + ".scope", args.final, violations)
    check_inventory(data.get("page_inventory"), show + ".page_inventory", args.final, violations)

    scenarios = data.get("scenarios")
    if not isinstance(scenarios, list):
        violations.append(v("EMPTY_FIELD", show + " scenarios", "scenarios 须为列表"))
        scenarios = []
    people, upstream_path, upstream_err = upstream_personas(output_dir)
    if not people:
        warnings.append(v("MISSING_FILE",
                          display_path(upstream_path, os.path.abspath(args.project_root)),
                          "上游 %s 不可读（%s）——「场景名含人物名」的机械核对跳过"
                          "（人工在 04-outline 第 2 步的闸清单里判）"
                          % (TRIGGER_FILE, upstream_err or "文件不存在")))
    ctx = {"out": violations, "ids": [], "page_ids": [], "people": people, "final": args.final}
    for index, record in enumerate(scenarios):
        check_scenario(record, index, show, ctx)
    check_ids(ctx["ids"], ctx["page_ids"], show, violations)

    report = check_coverage(data, show, args.final, violations)

    revisions = data.get("revisions")
    if revisions is None:
        violations.append(v("EMPTY_FIELD", show + " revisions", "revisions 缺失（无修订写空列表）"))
    elif not isinstance(revisions, list):
        violations.append(v("EMPTY_FIELD", show + " revisions", "revisions 不是列表"))

    violations += check_tokens(data, show)

    if args.final:
        if status_ok and status != STATUS_ENUM[1]:
            violations.append(v("STATUS_MISMATCH", show + ".project.status",
                                "--final 要求 status: 已定稿，实为 %s（先走完 wds-scenarios 的"
                                "六个步骤文件，再按 §2.5 六拍落盘定稿）" % status))
        if not scenarios:
            violations.append(v("EMPTY_FIELD", show + " scenarios",
                                "--final 要求至少一条场景记录"))
        if any(ASSUMPTION_MARK in text for _p, text in walk_strings(data, "")):
            violations.append(v("ASSUMPTION_PRESENT", show,
                                "--final 要求零 [假设]；未决项写进 revisions 或就地补问"))
    counts = {"records": len([x for x in scenarios if isinstance(x, dict)]),
              "by_status": {name: sum(1 for x in scenarios if isinstance(x, dict)
                                      and text_of(x.get("status")) == name)
                            for name in RECORD_STATUS_ENUM},
              "inventory": report["total"], "assigned": report["covered"],
              "pages": len(report["matrix"]), "coverage": report["rate"]}
    return violations, warnings, counts, report


