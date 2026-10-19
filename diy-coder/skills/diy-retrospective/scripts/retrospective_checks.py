# -*- coding: utf-8 -*-
"""diy-retrospective check 命令域：Refs 引用解析面、check_* 十件字段校验与 check_record 记录级编排。."""

import os

import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import display_path, is_int, items, nonempty, v, walk_strings  # noqa: E402

from retrospective_lib import ACTION_CATEGORIES, AI_RE, BUG_LOG_FILE, BUG_TOKEN_RE, DATE_RE, EPICS_FILE, EPIC_RE, FOLLOWUP_STATUSES, PATTERN_MIN_COUNT, PREP_CLASSES, READINESS_KEYS, RECORD_STATUSES, RT_RE, STORIES_FILE, STORY_TOKEN_RE, TEXT_LIST_KEYS, check_metrics, doc_of, epic_ids, story_entries  # noqa: E402

# ---------------------------------------------------------------- check

class Refs(object):
    """引用解析面：来源文件在场性 + 已知 ID 集；来源缺席 → 该面降级（调用方定升降级）。"""

    KIND_FILE = {"S": STORIES_FILE, "E": EPICS_FILE, "BUG": BUG_LOG_FILE}

    def __init__(self, docs, out_dir, project_root):
        self.show = {name: display_path(os.path.join(out_dir, name), project_root)
                     for name in (STORIES_FILE, EPICS_FILE, BUG_LOG_FILE)}
        self.sets = {
            "S": {str(s["id"]) for s in story_entries(docs) if nonempty(s.get("id"))},
            "E": epic_ids(docs),
            "BUG": {str(b["id"]) for b in items(doc_of(docs, BUG_LOG_FILE), "bugs")
                    if isinstance(b, dict) and nonempty(b.get("id"))},
        }
        self.unavailable = set()
        self.missing = []
        for kind, filename in self.KIND_FILE.items():
            entry = docs[filename]
            if entry["present"] and entry["err"] is None:
                continue
            self.unavailable.add(kind)
            self.missing.append(v("MISSING_FILE", self.show[filename],
                                  "%s %s：其中 ID 引用无法解析"
                                  % (filename, "不可解析" if entry["present"]
                                     else "未找到")))

    def resolve(self, kind, ref, where):
        """按来源解析引用；来源缺席 → 降级为空（调用方以 refs.missing 处理）。"""
        if kind in self.unavailable:
            return []
        if str(ref) in self.sets[kind]:
            return []
        return [v("UNKNOWN_ID", where, "%s 在 %s 中不存在"
                  % (ref, self.KIND_FILE[kind]))]

def check_patterns(record, where, refs):
    """patterns：跨 story 模式（≥2 成交付证据）+ evidence 引用解析（S-x / BUG-0xx）。"""
    violations = []
    patterns = record.get("patterns")
    if patterns is None:
        return [v("EMPTY_FIELD", where + ".patterns", "patterns 缺失（无模式写空列表）")]
    if not isinstance(patterns, list):
        return [v("EMPTY_FIELD", where + ".patterns", "patterns 不是列表")]
    for i, pattern in enumerate(patterns):
        pw = "%s.patterns[%d]" % (where, i)
        if not isinstance(pattern, dict):
            violations.append(v("EMPTY_FIELD", pw, "pattern 不是映射"))
            continue
        if not nonempty(pattern.get("theme")):
            violations.append(v("EMPTY_FIELD", pw + ".theme", "theme 为空"))
        count = pattern.get("count")
        if not is_int(count):
            violations.append(v("ENUM_INVALID", pw + ".count",
                                "count 须为整数（跨 story 出现次数），实为 %s" % count))
        elif count < PATTERN_MIN_COUNT:
            violations.append(v("ENUM_INVALID", pw + ".count",
                                "count 须 ≥%d：跨 story 才成模式" % PATTERN_MIN_COUNT))
        evidence = pattern.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            violations.append(v("EMPTY_FIELD", pw + ".evidence",
                                "evidence 须为非空列表（S-x / BUG-0xx）"))
            continue
        for j, ref in enumerate(evidence):
            ew = "%s.evidence[%d]" % (pw, j)
            if not nonempty(ref):
                violations.append(v("EMPTY_FIELD", ew, "evidence 项为空"))
            elif STORY_TOKEN_RE.fullmatch(str(ref)):
                violations += refs.resolve("S", ref, ew)
            elif BUG_TOKEN_RE.fullmatch(str(ref)):
                violations += refs.resolve("BUG", ref, ew)
            else:
                violations.append(v("ENUM_INVALID", ew,
                                    "evidence 须为 S-x 或 BUG-0xx，实为 %s" % ref))
    return violations

def check_text_lists(record, where):
    violations = []
    for key in TEXT_LIST_KEYS:
        value = record.get(key)
        if value is None:
            violations.append(v("EMPTY_FIELD", "%s.%s" % (where, key),
                                "%s 缺失（无内容写空列表）" % key))
        elif not isinstance(value, list):
            violations.append(v("EMPTY_FIELD", "%s.%s" % (where, key), "%s 不是列表" % key))
        elif any(not nonempty(item) for item in value):
            violations.append(v("EMPTY_FIELD", "%s.%s" % (where, key), "%s 项不得为空" % key))
    return violations

def check_action_items(record, where, final):
    violations = []
    actions = record.get("action_items")
    if actions is None:
        return [v("EMPTY_FIELD", where + ".action_items",
                  "action_items 缺失（无行动项写空列表）")]
    if not isinstance(actions, list):
        return [v("EMPTY_FIELD", where + ".action_items", "action_items 不是列表")]
    if final and not actions:
        violations.append(v("EMPTY_FIELD", where + ".action_items",
                            "--final 要求至少 1 条行动项（回顾的承诺面）"))
    seen = set()
    for i, action in enumerate(actions):
        aw = "%s.action_items[%d]" % (where, i)
        if not isinstance(action, dict):
            violations.append(v("EMPTY_FIELD", aw, "action item 不是映射"))
            continue
        aid = action.get("id")
        if not nonempty(aid):
            violations.append(v("EMPTY_FIELD", aw + ".id", "行动项 id 缺失"))
        elif not AI_RE.fullmatch(str(aid)):
            violations.append(v("ENUM_INVALID", aw + ".id",
                                "id 须为 AI-0nn（三位零填充），实为 %s" % aid))
        elif str(aid) in seen:
            violations.append(v("DUPLICATE_ID", aw + ".id", "行动项 ID %s 重复" % aid))
        else:
            seen.add(str(aid))
        for key in ("action", "owner", "done_when"):
            if not nonempty(action.get(key)):
                violations.append(v("EMPTY_FIELD", "%s.%s" % (aw, key),
                                    "%s 为空（SMART 行动项须有动作/归属/完成判据）" % key))
        category = action.get("category")
        if not nonempty(category):
            violations.append(v("EMPTY_FIELD", aw + ".category", "category 缺失"))
        elif str(category) not in ACTION_CATEGORIES:
            violations.append(v("ENUM_INVALID", aw + ".category",
                                "category 越界：%s（合法集 %s）"
                                % (category, "|".join(ACTION_CATEGORIES))))
    return violations

def check_prep_items(record, where):
    violations = []
    prep = record.get("prep_items")
    if prep is None:
        return [v("EMPTY_FIELD", where + ".prep_items", "prep_items 缺失（无准备项写空列表）")]
    if not isinstance(prep, list):
        return [v("EMPTY_FIELD", where + ".prep_items", "prep_items 不是列表")]
    for i, item in enumerate(prep):
        pw = "%s.prep_items[%d]" % (where, i)
        if not isinstance(item, dict):
            violations.append(v("EMPTY_FIELD", pw, "prep item 不是映射"))
            continue
        for key in ("item", "owner"):
            if not nonempty(item.get(key)):
                violations.append(v("EMPTY_FIELD", "%s.%s" % (pw, key), "%s 为空" % key))
        cls = item.get("class")
        if not nonempty(cls):
            violations.append(v("EMPTY_FIELD", pw + ".class", "class 缺失"))
        elif str(cls) not in PREP_CLASSES:
            violations.append(v("ENUM_INVALID", pw + ".class",
                                "class 越界：%s（合法集 %s）"
                                % (cls, "|".join(PREP_CLASSES))))
        if "effort" in item and not nonempty(item.get("effort")):
            violations.append(v("EMPTY_FIELD", pw + ".effort", "effort 出现时不得为空"))
    return violations

def check_critical_path(record, where):
    violations = []
    path = record.get("critical_path")
    if path is None:
        return [v("EMPTY_FIELD", where + ".critical_path",
                  "critical_path 缺失（无关键路径项写空列表）")]
    if not isinstance(path, list):
        return [v("EMPTY_FIELD", where + ".critical_path", "critical_path 不是列表")]
    for i, item in enumerate(path):
        cw = "%s.critical_path[%d]" % (where, i)
        if not isinstance(item, dict):
            violations.append(v("EMPTY_FIELD", cw, "critical path 项不是映射"))
            continue
        for key in ("item", "why", "owner"):
            if not nonempty(item.get(key)):
                violations.append(v("EMPTY_FIELD", "%s.%s" % (cw, key), "%s 为空" % key))
    return violations

def check_readiness(record, where, final):
    """就绪度五维：键必须在场；值非空为 --final 义务（源 step-9 五问）。"""
    violations = []
    readiness = record.get("readiness")
    if not isinstance(readiness, dict):
        return [v("EMPTY_FIELD", where + ".readiness",
                  "readiness 缺失或不是映射（五键 %s）" % "|".join(READINESS_KEYS))]
    for key in READINESS_KEYS:
        if key not in readiness:
            violations.append(v("EMPTY_FIELD", "%s.readiness.%s" % (where, key),
                                "readiness.%s 缺失" % key))
        elif final and not nonempty(readiness[key]):
            violations.append(v("EMPTY_FIELD", "%s.readiness.%s" % (where, key),
                                "--final 要求 readiness.%s 非空" % key))
    return violations

def check_prev_followup(record, where, refs, other_ids):
    """前一份 retro 的承诺跟踪：retro 须指向同文件内的既往记录（非自身）。"""
    violations = []
    followup = record.get("prev_followup")
    if followup is None:
        return violations
    if not isinstance(followup, list):
        return [v("EMPTY_FIELD", where + ".prev_followup", "prev_followup 不是列表")]
    for i, item in enumerate(followup):
        fw = "%s.prev_followup[%d]" % (where, i)
        if not isinstance(item, dict):
            violations.append(v("EMPTY_FIELD", fw, "prev_followup 项不是映射"))
            continue
        ref = item.get("retro")
        if not nonempty(ref):
            violations.append(v("EMPTY_FIELD", fw + ".retro", "retro 引用缺失"))
        elif not RT_RE.fullmatch(str(ref)):
            violations.append(v("ENUM_INVALID", fw + ".retro",
                                "retro 须为 RT-0nn，实为 %s" % ref))
        elif str(ref) not in other_ids:
            violations.append(v("UNKNOWN_ID", fw + ".retro",
                                "%s 不是本文件内既往记录（承诺跟踪只能指向同期已存的 retro）"
                                % ref))
        for key in ("action", "evidence"):
            if not nonempty(item.get(key)):
                violations.append(v("EMPTY_FIELD", "%s.%s" % (fw, key), "%s 为空" % key))
        status = item.get("status")
        if not nonempty(status):
            violations.append(v("EMPTY_FIELD", fw + ".status", "status 缺失"))
        elif str(status) not in FOLLOWUP_STATUSES:
            violations.append(v("ENUM_INVALID", fw + ".status",
                                "status 越界：%s（合法集 %s）"
                                % (status, "|".join(FOLLOWUP_STATUSES))))
    return violations

def check_significant_changes(record, where):
    violations = []
    changes = record.get("significant_changes")
    if changes is None:
        return violations
    if not isinstance(changes, list):
        return [v("EMPTY_FIELD", where + ".significant_changes",
                  "significant_changes 不是列表")]
    for i, item in enumerate(changes):
        cw = "%s.significant_changes[%d]" % (where, i)
        if not isinstance(item, dict):
            violations.append(v("EMPTY_FIELD", cw, "significant change 项不是映射"))
            continue
        for key in ("change", "impact", "recommended_action"):
            if not nonempty(item.get(key)):
                violations.append(v("EMPTY_FIELD", "%s.%s" % (cw, key), "%s 为空" % key))
    return violations

def check_next_epic(record, where, refs):
    violations = []
    nxt = record.get("next_epic")
    if nxt is None:
        return violations
    if not isinstance(nxt, dict):
        return [v("EMPTY_FIELD", where + ".next_epic", "next_epic 不是映射")]
    exists = nxt.get("exists")
    if not isinstance(exists, bool):
        violations.append(v("EMPTY_FIELD", where + ".next_epic.exists",
                            "exists 须为布尔值（实为 %s）" % exists))
        exists = None
    nid = nxt.get("id")
    if exists is True:
        if not nonempty(nid):
            violations.append(v("EMPTY_FIELD", where + ".next_epic.id",
                                "exists=true 时 id 必填"))
        elif not EPIC_RE.fullmatch(str(nid)):
            violations.append(v("ENUM_INVALID", where + ".next_epic.id",
                                "id 须为 E-<n>，实为 %s" % nid))
        else:
            violations += refs.resolve("E", nid, where + ".next_epic.id")
    deps = nxt.get("dependencies")
    if not isinstance(deps, list):
        violations.append(v("EMPTY_FIELD", where + ".next_epic.dependencies",
                            "dependencies 缺失或不是列表（无依赖写空列表）"))
    elif any(not nonempty(d) for d in deps):
        violations.append(v("EMPTY_FIELD", where + ".next_epic.dependencies",
                            "dependencies 项不得为空"))
    return violations

def check_final_duties(record, where, status):
    """--final 附加：status 已落 final、零假设（metrics 互证在 check_metrics 内完成）。"""
    violations = []
    if str(status) != "已定稿":
        violations.append(v("STATUS_MISMATCH", where + ".status",
                            "--final 要求 status 已落 final（实为 %s）" % status))
    if any("[假设]" in s for _p, s in walk_strings(record, "")):
        violations.append(v("ASSUMPTION_PRESENT", where,
                            "--final 要求零 [假设]；未决推断须先落定"))
    return violations

def check_record(index, record, final, docs, where_base, other_ids, refs):
    violations = []
    where = "%s.retros[%d]" % (where_base, index)
    if not isinstance(record, dict):
        return [v("EMPTY_FIELD", where, "记录不是映射")], None

    rid = record.get("id")
    if not nonempty(rid):
        violations.append(v("EMPTY_FIELD", where + ".id", "id 缺失"))
    elif not RT_RE.fullmatch(str(rid)):
        violations.append(v("ENUM_INVALID", where + ".id",
                            "id 须为 RT-0nn（三位零填充），实为 %s" % rid))

    date = record.get("date")
    if not nonempty(date):
        violations.append(v("EMPTY_FIELD", where + ".date", "date 缺失"))
    elif not DATE_RE.fullmatch(str(date)):
        violations.append(v("ENUM_INVALID", where + ".date",
                            "date 须为 YYYY-MM-DD，实为 %s" % date))

    status = record.get("status")
    if not nonempty(status):
        violations.append(v("EMPTY_FIELD", where + ".status", "status 缺失"))
    elif str(status) not in RECORD_STATUSES:
        violations.append(v("ENUM_INVALID", where + ".status",
                            "status 越界：%s（合法集 %s）"
                            % (status, "|".join(RECORD_STATUSES))))

    if not isinstance(record.get("partial"), bool):
        violations.append(v("ENUM_INVALID", where + ".partial",
                            "partial 须为布尔值（实为 %s）" % record.get("partial")))

    epic = record.get("epic")
    if not nonempty(epic):
        violations.append(v("EMPTY_FIELD", where + ".epic", "epic 引用缺失"))
    elif not EPIC_RE.fullmatch(str(epic)):
        violations.append(v("ENUM_INVALID", where + ".epic",
                            "epic 须为 E-<n>，实为 %s" % epic))
    else:
        violations += refs.resolve("E", epic, where + ".epic")

    violations += check_metrics(record, where, final, docs, epic)
    violations += check_patterns(record, where, refs)
    violations += check_text_lists(record, where)
    violations += check_action_items(record, where, final)
    violations += check_prep_items(record, where)
    violations += check_critical_path(record, where)
    violations += check_readiness(record, where, final)
    violations += check_prev_followup(record, where, refs, other_ids)
    violations += check_significant_changes(record, where)
    violations += check_next_epic(record, where, refs)
    if final:
        violations += check_final_duties(record, where, status)
    return violations, epic
