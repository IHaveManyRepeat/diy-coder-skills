# -*- coding: utf-8 -*-
"""diy-quick-dev 确定性引擎：spec.yaml 结构校验（轻量通道产物，任务书 §6）。

子命令：
  check    校验 {output_dir}/spec.yaml（SP-### 集合，形状对齐 bug-log.yaml）：
             schema / 枚举（project.status、type、route、status）/ SP-### 格式与唯一 /
             intent 两键（frozen 核心：problem + approach 均非空）/ tasks[].file 非空 /
             acceptance 三键非空 / change_log 完整性（finding + amended + avoided 非空、
             keep 为列表）/ 可选段（boundaries / code_map / io_matrix / deferred /
             open_questions）的结构校验。
             硬底线（任务书 §6 门禁）：`verification.commands` 为空而 status 前进到
             in-review|done → EMPTY_FIELD——轻量通道不做形式化红绿台账，但「进审查前
             每条 AC 有命令级实测证据」不可省（这是与 diy-dev 的明文差异）。
             status=done 另要求 `review_order` 非空（源 step-05 / step-oneshot 的
             Suggested Review Order 形态）。
             `--final` 附加：project.status=final、记录 status=done、tasks 非空且全 done、
             acceptance 非空、verification.commands 非空且每条 result 非空、零 [ASSUMPTION]。
             exit 0 唯一放行；1 = 违规；2 = 用法错误（argparse）。

分工裁定（任务书 §2.2/§6）：
  - spec.yaml 属新产物类型，不进 diyc.py check 的硬编码类型集；本引擎契约同构
    （exit 0 唯一放行 / --json 单行回执 / violations[{code, where, msg}] + counts；
    where 正斜杠、相对 project-root；--output-dir 必填且不设默认）。
  - 无 collect：澄清与代码勘察是 LLM 现场工作，无机械采集面（源技能里的机械动作只有
    token 计数与 md 读取，前者是提案非门、后者已被结构化产物取代）；跨文档核对仍归 diyc。
  - --previous 不实现：spec 记录按 status 逐条推进（同一记录原位更新，SP-### 稳定不重铸），
    不存在整份重写导致的 ID 集合收缩（对齐 P1 §8.5 与 B1 记账先例）。
  - 违规码全部复用 batch3-contract §3 冻结集，**零新增**。SP-### ID 由 diy-quick-dev
    会话（LLM）铸造，本引擎只校验格式与唯一性；不自动 git / 不开编辑器是技能纪律，
    本引擎无写回命令，不承担该面。
"""
# trace: 迁移计划 §二 验收 #2（产物 schema/稳定 ID）/#3（门禁零产出）/#4（ID 链接入）/#12（diyc 接线）
import argparse
import io
import json
import os
import re
import sys

import yaml

SPEC_FILE = "spec.yaml"

TYPES = ("feature", "bugfix", "refactor", "chore")
ROUTES = ("one-shot", "plan-code-review")
STATUSES = ("draft", "ready", "in-progress", "in-review", "done", "blocked")
PROJECT_STATUSES = ("draft", "final")
REVIEWED_STATUSES = ("in-review", "done")
REVIEW_LAYERS = ("correctness", "boundary", "coverage")
REVIEW_ROUTES = ("intent_gap", "bad_spec", "patch", "defer")

# 必填集合键（须在场，可为空列表）：无内容写空列表，缺席是 schema 缺口
REQUIRED_LISTS = ("tasks", "acceptance", "change_log", "deferred")
# 可选集合键（在场才校验其条目结构）
OPTIONAL_LISTS = ("code_map", "io_matrix", "review_order", "open_questions")
BOUNDARY_TIERS = ("always", "ask_first", "never")

SP_RE = re.compile(r"SP-\d{3}")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


def v(code, where, msg):
    return {"code": code, "where": where, "msg": msg}


def nonempty(value):
    return value is not None and str(value).strip() != ""


def items(doc, key):
    """取映射下的列表键；缺失/非列表 → []。"""
    if not isinstance(doc, dict):
        return []
    value = doc.get(key)
    return value if isinstance(value, list) else []


def load_yaml_safe(path):
    """读 YAML：(data, err)。文件缺失 → (None, None)；空文件 → ({}, None)；损坏 → (None, 原因)。"""
    if not os.path.isfile(path):
        return None, None
    try:
        with io.open(path, "r", encoding="utf-8") as f:
            return (yaml.safe_load(f) or {}), None
    except yaml.YAMLError as e:
        return None, str(e)
    except OSError as e:
        return None, str(e)


def display_path(path, project_root):
    """where 显示口径（对齐 diyc）：正斜杠 + 相对 project-root；越界则绝对路径。"""
    try:
        rel = os.path.relpath(path, project_root)
    except ValueError:
        rel = os.path.abspath(path)
    if rel.startswith(".."):
        return os.path.abspath(path).replace("\\", "/")
    return rel.replace("\\", "/")


def collect_strings(node):
    """递归收集映射/列表内的全部字符串（键与值）——[ASSUMPTION] 扫描用。"""
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for key, value in node.items():
            yield str(key)
            for s in collect_strings(value):
                yield s
    elif isinstance(node, list):
        for item in node:
            for s in collect_strings(item):
                yield s


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
        if str(status) == "done":
            return [v("EMPTY_FIELD", where + ".review_order",
                      "status=done 要求 review_order 非空（源 Suggested Review Order）")]
        return []
    if not isinstance(raw, list):
        return [v("EMPTY_FIELD", where + ".review_order", "review_order 不是列表")]
    violations = []
    if str(status) == "done" and not raw:
        violations.append(v("EMPTY_FIELD", where + ".review_order",
                            "status=done 要求 review_order 非空（源 Suggested Review Order）"))
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


def check_record(index, record, final, where_base):
    where = "%s.specs[%d]" % (where_base, index)
    if not isinstance(record, dict):
        return [v("EMPTY_FIELD", where, "记录不是映射")], None

    violations = []
    rid = record.get("id")
    if not nonempty(rid):
        violations.append(v("EMPTY_FIELD", where + ".id", "id 缺失"))
    elif not SP_RE.fullmatch(str(rid)):
        violations.append(v("ENUM_INVALID", where + ".id",
                            "id 须为 SP-0nn（三位零填充），实为 %s" % rid))

    if not nonempty(record.get("title")):
        violations.append(v("EMPTY_FIELD", where + ".title", "title 为空"))

    date = record.get("date")
    if not nonempty(date):
        violations.append(v("EMPTY_FIELD", where + ".date", "date 缺失"))
    elif not DATE_RE.fullmatch(str(date)):
        violations.append(v("ENUM_INVALID", where + ".date",
                            "date 须为 YYYY-MM-DD，实为 %s" % date))

    violations += check_enum(record, where, "type", TYPES)
    violations += check_enum(record, where, "route", ROUTES)
    violations += check_enum(record, where, "status", STATUSES)
    status = record.get("status")

    violations += check_intent(record, where)
    violations += check_boundaries(record, where)
    violations += check_tasks(record, where, final)
    violations += check_acceptance(record, where, final)
    violations += check_change_log(record, where)
    violations += check_verification(record, where, status, final)
    violations += check_review(record, where, status, final)
    violations += check_review_order(record, where, status)
    violations += check_deferred(record, where)
    violations += check_code_map(record, where)
    violations += check_io_matrix(record, where)

    if final:
        violations += check_final_duties(record, where, status)
    return violations, record


def check_final_duties(record, where, status):
    """--final 附加义务：该记录已完工 + 零假设（project.status 与集合在场在 cmd_check 判）。"""
    violations = []
    if str(status) != "done":
        violations.append(v("STATUS_MISMATCH", where + ".status",
                            "--final 要求该记录 status 已完工（done），实为 %s"
                            % (status if nonempty(status) else "未声明")))
    if any("[ASSUMPTION]" in s for s in collect_strings(record)):
        violations.append(v("ASSUMPTION_PRESENT", where,
                            "--final 要求零 [ASSUMPTION]；未决推断须先落定"))
    return violations


# ---------------------------------------------------------------- check

def count_by(records, key):
    counts = {}
    for record in records:
        if not isinstance(record, dict):
            continue
        value = record.get(key)
        if nonempty(value):
            counts[str(value)] = counts.get(str(value), 0) + 1
    return counts


def count_items(records, key):
    total = 0
    for record in records:
        if isinstance(record, dict) and isinstance(record.get(key), list):
            total += len(record[key])
    return total


def count_tasks_done(records):
    total = 0
    for record in records:
        if not isinstance(record, dict):
            continue
        for task in items(record, "tasks"):
            if isinstance(task, dict) and task.get("done") is True:
                total += 1
    return total


def count_findings(records):
    total = 0
    for record in records:
        if not isinstance(record, dict):
            continue
        review = record.get("review")
        if isinstance(review, dict) and isinstance(review.get("findings"), list):
            total += len(review["findings"])
    return total


def cmd_check(args):
    root = os.path.abspath(args.project_root)
    out = os.path.abspath(args.output_dir)
    path = os.path.join(out, SPEC_FILE)
    show = display_path(path, root)
    violations = []
    warnings = []
    records = []
    checked = []

    data, err = load_yaml_safe(path)
    if data is None and err is None:
        violations.append(v("MISSING_FILE", show,
                            "%s 不存在（先完成一次 quick-dev 起草）" % SPEC_FILE))
    elif err is not None:
        violations.append(v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err))
    elif not isinstance(data, dict):
        violations.append(v("EMPTY_FIELD", show, "顶层不是映射（须为 project + specs）"))
    else:
        project = data.get("project")
        if project is None:
            violations.append(v("EMPTY_FIELD", show + " project", "project 缺失"))
        elif not isinstance(project, dict):
            violations.append(v("EMPTY_FIELD", show + " project", "project 不是映射"))
        else:
            status = project.get("status")
            if not nonempty(status):
                violations.append(v("EMPTY_FIELD", show + " project.status",
                                    "project.status 缺失（draft|final）"))
            elif str(status) not in PROJECT_STATUSES:
                violations.append(v("ENUM_INVALID", show + " project.status",
                                    "project.status 越界：%s（合法集 %s）"
                                    % (status, "|".join(PROJECT_STATUSES))))
            elif args.final and str(status) != "final":
                violations.append(v("STATUS_MISMATCH", show + " project.status",
                                    "--final 要求 project.status 已落 final（实为 %s）" % status))
        revisions = data.get("revisions")
        if revisions is not None and not isinstance(revisions, list):
            violations.append(v("EMPTY_FIELD", show + " revisions", "revisions 不是列表"))
        raw_records = data.get("specs")
        if raw_records is None:
            violations.append(v("EMPTY_FIELD", show + " specs",
                                "specs 缺失（集合形态；无记录写空列表）"))
        elif not isinstance(raw_records, list):
            violations.append(v("EMPTY_FIELD", show + " specs", "specs 不是列表"))
        else:
            records = raw_records
            if args.id:
                checked = [r for r in records
                           if isinstance(r, dict) and str(r.get("id")) == args.id]
                if not checked:
                    violations.append(v("UNKNOWN_ID", show + " specs",
                                        "%s 在 spec.yaml 中不存在" % args.id))
            seen = set()
            for i, record in enumerate(records):
                if args.id and not (isinstance(record, dict)
                                    and str(record.get("id")) == args.id):
                    continue
                record_violations, _ = check_record(i, record, args.final, show)
                violations += record_violations
                if isinstance(record, dict) and nonempty(record.get("id")):
                    rid = str(record["id"])
                    if rid in seen:
                        violations.append(v("DUPLICATE_ID", "%s.specs[%d].id" % (show, i),
                                            "记录 ID %s 重复（SP ID 稳定不重用）" % rid))
                    seen.add(rid)
                if not args.id:
                    checked.append(record)
            if args.final and not checked:
                violations.append(v("EMPTY_FIELD", show + " specs",
                                    "--final 要求至少 1 条记录"))

    ok = not violations
    counts = {
        "specs": len(checked),
        "total_specs": len(records),
        "by_status": count_by(checked, "status"),
        "by_type": count_by(checked, "type"),
        "by_route": count_by(checked, "route"),
        "tasks": count_items(checked, "tasks"),
        "tasks_done": count_tasks_done(checked),
        "findings": count_findings(checked),
        "deferred": count_items(checked, "deferred"),
    }
    payload = {
        "ok": ok,
        "command": "check",
        "project_root": args.project_root,
        "output_dir": os.path.normpath(out).replace("\\", "/"),
        "final": args.final,
        "id": args.id,
        "violations": violations,
        "warnings": warnings,
        "counts": counts,
    }
    emit(payload, args.json, human_check)
    return 0 if ok else 1


def human_check(payload):
    if payload["ok"]:
        print("PASS：spec.yaml 校验通过（specs=%d，status=%s）"
              % (payload["counts"]["specs"],
                 "、".join("%s×%d" % (k, n)
                          for k, n in sorted(payload["counts"]["by_status"].items())) or "无"))
        for item in payload["warnings"]:
            print("警告 %s %s: %s" % (item["code"], item["where"], item["msg"]))
        return
    print("FAIL：")
    for item in payload["violations"]:
        print("- %s %s: %s" % (item["code"], item["where"], item["msg"]))
    for item in payload["warnings"]:
        print("警告 %s %s: %s" % (item["code"], item["where"], item["msg"]))


def emit(payload, as_json, human_lines):
    if as_json:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        human_lines(payload)


def build_parser():
    ap = argparse.ArgumentParser(
        description="diy-quick-dev 确定性引擎：spec.yaml 结构校验"
                    "（schema/枚举/frozen intent/验收实测证据；--final 定稿义务）")
    k = ap.add_subparsers(dest="cmd", required=True)
    c = k.add_parser("check", help="校验 spec.yaml（SP-### 集合；--final 附加定稿义务）")
    c.add_argument("--project-root", default=".", help="项目根（默认 .）")
    c.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    c.add_argument("--id", default=None, help="只校验该记录（SP-xxx）；缺省校验全部记录")
    c.add_argument("--final", action="store_true",
                   help="定稿校验：project.status=final + 记录 done + tasks 全 done + "
                        "命令实测 result + 零假设")
    c.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    c.set_defaults(func=cmd_check)
    return ap


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = build_parser().parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
