# -*- coding: utf-8 -*-
"""diy-checkpoint-preview checkpoint.yaml 校验域：concerns/risks/observations/记录级校验与 --final 定稿义务。."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import nonempty, v, walk_strings  # noqa: E402

from checkpoint_target import CK_RE, DATE_RE, DECISIONS, MODES, RECORD_STATUSES, RISK_LABELS, SPRINT_FILE, STORIES_FILE, TARGET_SOURCES  # noqa: E402

# ---- check ----

def check_concerns(record, where):
    violations = []
    concerns = record.get("concerns")
    if concerns is None:
        return [v("EMPTY_FIELD", where + ".concerns", "concerns 缺失")]
    if not isinstance(concerns, list):
        return [v("EMPTY_FIELD", where + ".concerns", "concerns 不是列表")]
    for i, concern in enumerate(concerns):
        cw = "%s.concerns[%d]" % (where, i)
        if not isinstance(concern, dict):
            violations.append(v("EMPTY_FIELD", cw, "concern 不是映射"))
            continue
        for key in ("name", "why"):
            if not nonempty(concern.get(key)):
                violations.append(v("EMPTY_FIELD", cw + "." + key, "%s 为空" % key))
        sites = concern.get("sites")
        if not isinstance(sites, list):
            violations.append(v("EMPTY_FIELD", cw + ".sites", "sites 缺失或不是列表"))
            continue
        for j, site in enumerate(sites):
            if not nonempty(site):
                violations.append(v("EMPTY_FIELD", "%s.sites[%d]" % (cw, j),
                                    "site 为空（须为 path:line）"))
    return violations

def check_risks(record, where):
    violations = []
    risks = record.get("risks")
    if risks is None:
        return [v("EMPTY_FIELD", where + ".risks", "risks 缺失（无高风险点写空列表）")]
    if not isinstance(risks, list):
        return [v("EMPTY_FIELD", where + ".risks", "risks 不是列表")]
    for i, risk in enumerate(risks):
        rw = "%s.risks[%d]" % (where, i)
        if not isinstance(risk, dict):
            violations.append(v("EMPTY_FIELD", rw, "risk 不是映射"))
            continue
        label = risk.get("label")
        if not nonempty(label):
            violations.append(v("EMPTY_FIELD", rw + ".label", "label 为空"))
        elif str(label) not in RISK_LABELS:
            violations.append(v("ENUM_INVALID", rw + ".label",
                                "label 越界：%s（合法集 %s）" % (label, "|".join(RISK_LABELS))))
        for key in ("where", "why"):
            if not nonempty(risk.get(key)):
                violations.append(v("EMPTY_FIELD", rw + "." + key, "%s 为空" % key))
    return violations

def check_observations(record, where):
    violations = []
    items = record.get("observations")
    if items is None:
        return [v("EMPTY_FIELD", where + ".observations",
                  "observations 缺失（无观察点写空列表）")]
    if not isinstance(items, list):
        return [v("EMPTY_FIELD", where + ".observations", "observations 不是列表")]
    for i, obs in enumerate(items):
        ow = "%s.observations[%d]" % (where, i)
        if not isinstance(obs, dict):
            violations.append(v("EMPTY_FIELD", ow, "observation 不是映射"))
            continue
        for key in ("do", "watch"):
            if not nonempty(obs.get(key)):
                violations.append(v("EMPTY_FIELD", ow + "." + key, "%s 为空" % key))
    return violations

def check_record(index, record, final, story_ids, where_base):
    violations = []
    where = "%s.checkpoints[%d]" % (where_base, index)
    if not isinstance(record, dict):
        return [v("EMPTY_FIELD", where, "记录不是映射")]

    rid = record.get("id")
    if not nonempty(rid):
        violations.append(v("EMPTY_FIELD", where + ".id", "id 缺失"))
    elif not CK_RE.fullmatch(str(rid)):
        violations.append(v("ENUM_INVALID", where + ".id",
                            "id 须为 CK-0nn（三位零填充），实为 %s" % rid))

    date = record.get("date")
    if not nonempty(date):
        violations.append(v("EMPTY_FIELD", where + ".date", "date 缺失"))
    elif not DATE_RE.fullmatch(str(date)):
        violations.append(v("ENUM_INVALID", where + ".date",
                            "date 须为 YYYY-MM-DD，实为 %s" % date))

    # §8.3 裁定：change_type 为开放字符串（commit|branch|PR|<自由文本>，默认 change）——
    # 可选、出现时非空即可；禁封闭枚举（用户自然语言命名不得被误判）
    change_type = record.get("change_type")
    if change_type is not None and not nonempty(change_type):
        violations.append(v("EMPTY_FIELD", where + ".change_type",
                            "change_type 出现时不得为空（开放字符串，默认 change）"))

    target = record.get("target")
    if not isinstance(target, dict):
        violations.append(v("EMPTY_FIELD", where + ".target", "target 缺失或不是映射"))
    else:
        source = target.get("source")
        if not nonempty(source):
            violations.append(v("EMPTY_FIELD", where + ".target.source", "source 缺失"))
        elif str(source) not in TARGET_SOURCES:
            violations.append(v("ENUM_INVALID", where + ".target.source",
                                "source 越界：%s（合法集 %s）"
                                % (source, "|".join(TARGET_SOURCES))))
        elif str(source) == "显式指定" and not nonempty(target.get("ref")):
            violations.append(v("EMPTY_FIELD", where + ".target.ref",
                                "source=显式指定 时 ref 必填"))
        elif str(source) == "冲刺任务" and not nonempty(target.get("story")):
            violations.append(v("EMPTY_FIELD", where + ".target.story",
                                "source=冲刺任务 时 story 必填"))
        story = target.get("story")
        if nonempty(story) and str(story) not in story_ids:
            violations.append(v("UNKNOWN_ID", where + ".target.story",
                                "story %s 在 %s / %s 中均不可解析"
                                % (story, STORIES_FILE, SPRINT_FILE)))
        if "inferred" in target and not isinstance(target.get("inferred"), bool):
            violations.append(v("ENUM_INVALID", where + ".target.inferred",
                                "inferred 若给出须为布尔（true|false）"))

    mode = record.get("mode")
    if not nonempty(mode):
        violations.append(v("EMPTY_FIELD", where + ".mode", "mode 缺失"))
    elif str(mode) not in MODES:
        violations.append(v("ENUM_INVALID", where + ".mode",
                            "mode 越界：%s（合法集 %s）" % (mode, "|".join(MODES))))

    decision = record.get("decision")
    if nonempty(decision) and str(decision) not in DECISIONS:
        violations.append(v("ENUM_INVALID", where + ".decision",
                            "decision 越界：%s（合法集 %s）"
                            % (decision, "|".join(DECISIONS))))

    status = record.get("status")
    if not nonempty(status):
        violations.append(v("EMPTY_FIELD", where + ".status", "status 缺失"))
    elif str(status) not in RECORD_STATUSES:
        violations.append(v("ENUM_INVALID", where + ".status",
                            "status 越界：%s（合法集 %s）"
                            % (status, "|".join(RECORD_STATUSES))))

    violations += check_concerns(record, where)
    violations += check_risks(record, where)
    violations += check_observations(record, where)

    if final:
        violations += check_final_duties(record, where, decision, status)
    return violations

def check_final_duties(record, where, decision, status):
    """--final 附加义务：decision 已定（非 讨论）、status 已落 已定稿、next 非空、零假设。"""
    violations = []
    if not nonempty(decision):
        violations.append(v("PENDING_DECISION", where + ".decision",
                            "--final 要求 decision 已定（批准|返工）；讨论后回到决策"))
    elif str(decision) == "讨论":
        if str(status) == "已定稿":
            violations.append(v("STATUS_MISMATCH", where + ".status",
                                "讨论决策不得落 status: 已定稿"))
        else:
            violations.append(v("PENDING_DECISION", where + ".decision",
                                "讨论未收敛：讨论后须回到 批准|返工 再定稿"))
    elif str(status) != "已定稿":
        violations.append(v("STATUS_MISMATCH", where + ".status",
                            "decision 已定（%s），须落 status: 已定稿" % decision))
    if not nonempty(record.get("next")):
        violations.append(v("EMPTY_FIELD", where + ".next", "--final 要求 next 路由行非空"))
    concerns = record.get("concerns")
    if isinstance(concerns, list) and not concerns:
        violations.append(v("EMPTY_FIELD", where + ".concerns",
                            "--final 要求至少 1 个 concern"))
    if any("[假设]" in s for _p, s in walk_strings(record, "")):
        violations.append(v("ASSUMPTION_PRESENT", where,
                            "--final 要求零 [假设]；未决假设须先落定"))
    return violations

def count_by(records, key):
    """按记录顶层字段值计数（空值跳过）；key='target' 时取 target.source。"""
    counts = {}
    for record in records:
        if not isinstance(record, dict):
            continue
        value = record.get(key)
        if key == "target" and isinstance(value, dict):
            value = value.get("source")
        if nonempty(value):
            counts[str(value)] = counts.get(str(value), 0) + 1
    return counts
