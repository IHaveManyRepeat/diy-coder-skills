# -*- coding: utf-8 -*-
"""diy-quick-dev spec.yaml 分段校验件：枚举/intent/boundaries/tasks/acceptance/change_log/verification/review/review_order/deferred/code_map/io_matrix 十二检与检查常量表。."""

import re

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import nonempty, v  # noqa: E402

TYPES = ("新功能", "缺陷修复", "重构", "杂务")
ROUTES = ("一次成型", "计划-编码-审查")
STATUSES = ("草稿", "就绪", "进行中", "审查中", "已完成", "已阻塞")
REVIEWED_STATUSES = ("审查中", "已完成")
REVIEW_LAYERS = ("正确性", "边界", "覆盖审计")
REVIEW_ROUTES = ("意图缺口", "规格缺陷", "小修", "后置")

BOUNDARY_TIERS = ("总是", "先问", "从不")

SP_RE = re.compile(r"SP-\d{3}")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")

# ---------------------------------------------------------------- 分段校验

def check_enum(record, where, key, allowed, required=True):
    value = record.get(key)
    if not nonempty(value):
        if required:
            return [v("EMPTY_FIELD", "%s.%s" % (where, key), "%s 缺失" % key)]
        return []
    if str(value) not in allowed:
        return [v("ENUM_INVALID", "%s.%s" % (where, key),
                  "%s 越界：%s（合法集 %s）" % (key, value, "|".join(allowed)))]
    return []

def check_intent(record, where):
    """frozen 核心：approval 后只有人类能改（源 <frozen-after-approval> 的 Intent 段）。"""
    intent = record.get("intent")
    if intent is None:
        return [v("EMPTY_FIELD", where + ".intent", "intent 缺失（problem + approach）")]
    if not isinstance(intent, dict):
        return [v("EMPTY_FIELD", where + ".intent", "intent 不是映射")]
    violations = []
    for key in ("problem", "approach"):
        if not nonempty(intent.get(key)):
            violations.append(v("EMPTY_FIELD", "%s.intent.%s" % (where, key),
                                "intent.%s 为空（frozen 核心两键均须在场）" % key))
    return violations

def check_boundaries(record, where):
    boundaries = record.get("boundaries")
    if boundaries is None:
        return []
    if not isinstance(boundaries, dict):
        return [v("EMPTY_FIELD", where + ".boundaries", "boundaries 不是映射")]
    violations = []
    for tier in BOUNDARY_TIERS:
        if tier not in boundaries:
            continue
        values = boundaries.get(tier)
        if not isinstance(values, list):
            violations.append(v("EMPTY_FIELD", "%s.boundaries.%s" % (where, tier),
                                "%s 须为列表" % tier))
        elif any(not nonempty(x) for x in values):
            violations.append(v("EMPTY_FIELD", "%s.boundaries.%s" % (where, tier),
                                "%s 项不得为空" % tier))
    return violations

def check_tasks(record, where, final):
    raw = record.get("tasks")
    if raw is None or not isinstance(raw, list):
        return [v("EMPTY_FIELD", where + ".tasks", "tasks 缺失或不是列表（无任务写空列表）")]
    violations = []
    for i, task in enumerate(raw):
        tw = "%s.tasks[%d]" % (where, i)
        if not isinstance(task, dict):
            violations.append(v("EMPTY_FIELD", tw, "task 不是映射"))
            continue
        if not nonempty(task.get("task")):
            violations.append(v("EMPTY_FIELD", tw + ".task", "task 描述为空"))
        if not nonempty(task.get("file")):
            violations.append(v("EMPTY_FIELD", tw + ".file",
                                "file 为空（每条 task 须有具体落点文件）"))
        done = task.get("done")
        if done is not None and not isinstance(done, bool):
            violations.append(v("ENUM_INVALID", tw + ".done", "done 须为布尔（实为 %s）" % done))
        elif final and done is not True:
            violations.append(v("STATUS_MISMATCH", tw + ".done",
                                "--final 要求每条 task 已 done（实为 %s）" % done))
    if final and not raw:
        violations.append(v("EMPTY_FIELD", where + ".tasks", "--final 要求至少 1 条 task"))
    return violations

def check_acceptance(record, where, final):
    raw = record.get("acceptance")
    if raw is None or not isinstance(raw, list):
        return [v("EMPTY_FIELD", where + ".acceptance",
                  "acceptance 缺失或不是列表（无验收写空列表）")]
    violations = []
    for i, ac in enumerate(raw):
        aw = "%s.acceptance[%d]" % (where, i)
        if not isinstance(ac, dict):
            violations.append(v("EMPTY_FIELD", aw, "acceptance 项不是映射"))
            continue
        for key in ("given", "when", "then"):
            if not nonempty(ac.get(key)):
                violations.append(v("EMPTY_FIELD", "%s.%s" % (aw, key),
                                    "%s 为空（Given/When/Then 三键均须在场）" % key))
    if final and not raw:
        violations.append(v("EMPTY_FIELD", where + ".acceptance",
                            "--final 要求至少 1 条 acceptance"))
    return violations

def check_change_log(record, where):
    """源 Spec Change Log：append-only，每条记录触发finding / 修正内容 / 避开的坏态 / KEEP。"""
    raw = record.get("change_log")
    if raw is None or not isinstance(raw, list):
        return [v("EMPTY_FIELD", where + ".change_log",
                  "change_log 缺失或不是列表（无日志写空列表）")]
    violations = []
    for i, entry in enumerate(raw):
        cw = "%s.change_log[%d]" % (where, i)
        if not isinstance(entry, dict):
            violations.append(v("EMPTY_FIELD", cw, "change_log 项不是映射"))
            continue
        for key in ("finding", "amended", "avoided"):
            if not nonempty(entry.get(key)):
                violations.append(v("EMPTY_FIELD", "%s.%s" % (cw, key),
                                    "change_log 项缺 %s（触发/修正/避开的坏态须齐）" % key))
        keep = entry.get("keep")
        if keep is not None and not isinstance(keep, list):
            violations.append(v("EMPTY_FIELD", cw + ".keep", "keep 须为列表（KEEP 指令）"))
        elif isinstance(keep, list) and any(not nonempty(x) for x in keep):
            violations.append(v("EMPTY_FIELD", cw + ".keep", "keep 项不得为空"))
    return violations

def check_verification(record, where, status, final):
    """轻量 TDD 硬底线：进审查/完工前每条命令有实测结果。"""
    verification = record.get("verification")
    commands = []
    if verification is not None:
        if not isinstance(verification, dict):
            return [v("EMPTY_FIELD", where + ".verification", "verification 不是映射")]
        raw = verification.get("commands")
        if raw is None:
            raw = []
        if not isinstance(raw, list):
            return [v("EMPTY_FIELD", where + ".verification.commands",
                      "commands 不是列表（无命令写空列表）")]
        commands = raw
    elif str(status) in REVIEWED_STATUSES or final:
        commands = []
    violations = []
    if not commands and (str(status) in REVIEWED_STATUSES or final):
        violations.append(v("EMPTY_FIELD", where + ".verification.commands",
                            "verification.commands 为空：status 为 %s 前每条验收须有"
                            "命令级实测证据（{cmd, expect, result}）" % (status or "未声明")))
    for i, entry in enumerate(commands):
        cw = "%s.verification.commands[%d]" % (where, i)
        if not isinstance(entry, dict):
            violations.append(v("EMPTY_FIELD", cw, "命令项不是映射"))
            continue
        for key in ("cmd", "expect"):
            if not nonempty(entry.get(key)):
                violations.append(v("EMPTY_FIELD", "%s.%s" % (cw, key), "%s 为空" % key))
        if final and not nonempty(entry.get("result")):
            violations.append(v("EMPTY_FIELD", cw + ".result",
                                "--final 要求每条命令有实测 result（跑过才写）"))
        elif not final and nonempty(status) and str(status) in REVIEWED_STATUSES \
                and not nonempty(entry.get("result")):
            violations.append(v("EMPTY_FIELD", cw + ".result",
                                "status 已到 %s，命令须有实测 result" % status))
    manual = verification.get("manual") if isinstance(verification, dict) else None
    if manual is not None:
        if not isinstance(manual, list):
            violations.append(v("EMPTY_FIELD", where + ".verification.manual", "manual 须为列表"))
        elif any(not nonempty(x) for x in manual):
            violations.append(v("EMPTY_FIELD", where + ".verification.manual",
                                "manual 项不得为空"))
    return violations

def check_review(record, where, status, final):
    """审查块：diy-review 的 L1-L3 层与四类路由（不另造审查体系）。"""
    review = record.get("review")
    reviewed = str(status) in REVIEWED_STATUSES or final
    if review is None:
        if reviewed:
            return [v("EMPTY_FIELD", where + ".review",
                      "review 缺失：status 为 %s 的记录须带 review 块"
                      "（rounds + findings，层/路由取 diy-review）" % (status or "未声明"))]
        return []
    if not isinstance(review, dict):
        return [v("EMPTY_FIELD", where + ".review", "review 不是映射")]
    violations = []
    rounds = review.get("rounds")
    if rounds is None:
        violations.append(v("EMPTY_FIELD", where + ".review.rounds", "rounds 缺失"))
    elif not isinstance(rounds, int) or isinstance(rounds, bool) or rounds < 0:
        violations.append(v("ENUM_INVALID", where + ".review.rounds",
                            "rounds 须为非负整数（实为 %s）" % rounds))
    findings = review.get("findings")
    if findings is None:
        violations.append(v("EMPTY_FIELD", where + ".review.findings",
                            "findings 缺失（无发现写空列表）"))
        return violations
    if not isinstance(findings, list):
        return violations + [v("EMPTY_FIELD", where + ".review.findings",
                               "findings 不是列表")]
    for i, finding in enumerate(findings):
        fw = "%s.review.findings[%d]" % (where, i)
        if not isinstance(finding, dict):
            violations.append(v("EMPTY_FIELD", fw, "finding 不是映射"))
            continue
        layer = finding.get("layer")
        if not nonempty(layer):
            violations.append(v("EMPTY_FIELD", fw + ".layer", "layer 缺失"))
        elif str(layer) not in REVIEW_LAYERS:
            violations.append(v("ENUM_INVALID", fw + ".layer",
                                "layer 越界：%s（合法集 %s，diy-review L1-L3）"
                                % (layer, "|".join(REVIEW_LAYERS))))
        route = finding.get("route")
        if not nonempty(route):
            violations.append(v("EMPTY_FIELD", fw + ".route", "route 缺失"))
        elif str(route) not in REVIEW_ROUTES:
            violations.append(v("ENUM_INVALID", fw + ".route",
                                "route 越界：%s（合法集 %s）" % (route, "|".join(REVIEW_ROUTES))))
        if not nonempty(finding.get("note")):
            violations.append(v("EMPTY_FIELD", fw + ".note", "note 为空（一行发现描述）"))
    return violations

def check_review_order(record, where, status):
    raw = record.get("review_order")
    if raw is None:
        if str(status) == "已完成":
            return [v("EMPTY_FIELD", where + ".review_order",
                      "status=已完成 要求 review_order 非空（源 Suggested Review Order）")]
        return []
    if not isinstance(raw, list):
        return [v("EMPTY_FIELD", where + ".review_order", "review_order 不是列表")]
    violations = []
    if str(status) == "已完成" and not raw:
        violations.append(v("EMPTY_FIELD", where + ".review_order",
                            "status=已完成 要求 review_order 非空（源 Suggested Review Order）"))
    for i, concern in enumerate(raw):
        cw = "%s.review_order[%d]" % (where, i)
        if not isinstance(concern, dict):
            violations.append(v("EMPTY_FIELD", cw, "concern 不是映射"))
            continue
        if not nonempty(concern.get("concern")):
            violations.append(v("EMPTY_FIELD", cw + ".concern", "concern 名称为空"))
        stops = concern.get("stops")
        if not isinstance(stops, list):
            violations.append(v("EMPTY_FIELD", cw + ".stops", "stops 须为列表"))
            continue
        for j, stop in enumerate(stops):
            sw = "%s.stops[%d]" % (cw, j)
            if not isinstance(stop, dict):
                violations.append(v("EMPTY_FIELD", sw, "stop 不是映射"))
                continue
            if not nonempty(stop.get("path")):
                violations.append(v("EMPTY_FIELD", sw + ".path", "path 为空（相对路径）"))
            if not isinstance(stop.get("line"), int) or isinstance(stop.get("line"), bool):
                violations.append(v("ENUM_INVALID", sw + ".line",
                                    "line 须为整数（实为 %s）" % stop.get("line")))
            if not nonempty(stop.get("why")):
                violations.append(v("EMPTY_FIELD", sw + ".why", "why 为空（一行框架说明）"))
    return violations

def check_deferred(record, where):
    raw = record.get("deferred")
    if raw is None or not isinstance(raw, list):
        return [v("EMPTY_FIELD", where + ".deferred",
                  "deferred 缺失或不是列表（无延期写空列表）")]
    violations = []
    for i, entry in enumerate(raw):
        dw = "%s.deferred[%d]" % (where, i)
        if not isinstance(entry, dict):
            violations.append(v("EMPTY_FIELD", dw, "deferred 项不是映射"))
            continue
        for key in ("finding", "why"):
            if not nonempty(entry.get(key)):
                violations.append(v("EMPTY_FIELD", "%s.%s" % (dw, key), "%s 为空" % key))
        date = entry.get("date")
        if not nonempty(date):
            violations.append(v("EMPTY_FIELD", dw + ".date", "date 缺失"))
        elif not DATE_RE.fullmatch(str(date)):
            violations.append(v("ENUM_INVALID", dw + ".date",
                                "date 须为 YYYY-MM-DD（实为 %s）" % date))
    return violations

def check_code_map(record, where):
    raw = record.get("code_map")
    if raw is None:
        return []
    if not isinstance(raw, list):
        return [v("EMPTY_FIELD", where + ".code_map", "code_map 不是列表")]
    violations = []
    for i, entry in enumerate(raw):
        cw = "%s.code_map[%d]" % (where, i)
        if not isinstance(entry, dict):
            violations.append(v("EMPTY_FIELD", cw, "code_map 项不是映射"))
            continue
        if not nonempty(entry.get("path")):
            violations.append(v("EMPTY_FIELD", cw + ".path", "path 为空"))
        if not nonempty(entry.get("role")):
            violations.append(v("EMPTY_FIELD", cw + ".role", "role 为空"))
    return violations

def check_io_matrix(record, where):
    raw = record.get("io_matrix")
    if raw is None:
        return []
    if not isinstance(raw, list):
        return [v("EMPTY_FIELD", where + ".io_matrix", "io_matrix 不是列表")]
    violations = []
    for i, entry in enumerate(raw):
        iw = "%s.io_matrix[%d]" % (where, i)
        if not isinstance(entry, dict):
            violations.append(v("EMPTY_FIELD", iw, "io_matrix 项不是映射"))
            continue
        for key in ("scenario", "input", "expected"):
            if not nonempty(entry.get(key)):
                violations.append(v("EMPTY_FIELD", "%s.%s" % (iw, key), "%s 为空" % key))
    return violations
