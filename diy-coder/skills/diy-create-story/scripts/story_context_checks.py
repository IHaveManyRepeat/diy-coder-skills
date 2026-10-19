# -*- coding: utf-8 -*-
"""diy-create-story check 校验族：身份/绑定/引用/文件义务/final 定稿逐项检查与记录级编排。."""

import os

import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import items, nonempty, v, walk_strings  # noqa: E402

from story_context_lib import CLOSED_PREFIX, DATE_RE, DIYC_ROUTE, FILE_ACTIONS, RECORD_STATUSES, SC_RE, ac_ids, is_safe_rel, rel_to_root  # noqa: E402

# ---------------------------------------------------------------- check

def check_identity(record, where):
    violations = []
    rid = record.get("id")
    if not nonempty(rid):
        violations.append(v("EMPTY_FIELD", where + ".id", "id 缺失"))
    elif not SC_RE.fullmatch(str(rid)):
        violations.append(v("ENUM_INVALID", where + ".id",
                            "id 须为 SC-0nn（三位零填充），实为 %s" % rid))
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
    return violations

def ref_list(record, key, where):
    """取引用列表键：(值列表, violations)。非列表 → 空列表 + 违规。"""
    value = record.get(key)
    if value is None:
        return [], []
    if not isinstance(value, list):
        return [], [v("EMPTY_FIELD", "%s.%s" % (where, key), "%s 不是列表" % key)]
    violations = []
    seen = set()
    result = []
    for i, item in enumerate(value):
        item_where = "%s.%s[%d]" % (where, key, i)
        if not nonempty(item):
            violations.append(v("EMPTY_FIELD", item_where, "%s 项为空" % key))
            continue
        text = str(item)
        if text in seen:
            violations.append(v("DUPLICATE_ID", item_where, "%s 项重复：%s" % (key, text)))
            continue
        seen.add(text)
        result.append(text)
    return result, violations

def check_story_binding(record, where, ctx):
    """story 解析 + epic 一致 + ac_refs ⊆ story AC。返回 (story_entry, acs, violations)。"""
    violations = []
    story = record.get("story")
    story_entry = None
    if not nonempty(story):
        violations.append(v("EMPTY_FIELD", where + ".story", "story 缺失（S-x 引用）"))
    elif not ctx["has_stories"]:
        violations.append(v("MISSING_FILE", "stories.yaml",
                            "stories.yaml 缺席：story 引用无法解析（先跑 %s 定稿）" % DIYC_ROUTE))
    elif str(story) not in ctx["stories"]:
        violations.append(v("UNKNOWN_ID", where + ".story",
                            "%s 在 stories.yaml 中不存在" % story))
    else:
        story_entry = ctx["stories"][str(story)]

    epic = record.get("epic")
    if not nonempty(epic):
        violations.append(v("EMPTY_FIELD", where + ".epic", "epic 缺失（E-x 引用）"))
    elif story_entry is not None and str(epic) != str(story_entry.get("epic")):
        violations.append(v("SET_MISMATCH", where + ".epic",
                            "epic 与 stories.yaml 不一致：声明 %s，实为 %s"
                            % (epic, story_entry.get("epic"))))

    acs = []
    refs, ref_violations = ref_list(record, "ac_refs", where)
    violations += ref_violations
    if not refs:
        violations.append(v("EMPTY_FIELD", where + ".ac_refs",
                            "ac_refs 为空（上下文包至少引用本 story 的一条 AC）"))
    if story_entry is not None:
        known = set(ac_ids(story_entry))
        acs = sorted(known)
        for i, ref in enumerate(refs):
            if ref not in known:
                violations.append(v("UNKNOWN_ID", "%s.ac_refs[%d]" % (where, i),
                                    "%s 不是 %s 的 AC（该 story 的 AC：%s）"
                                    % (ref, record.get("story"),
                                       "、".join(acs) if acs else "无")))
    return story_entry, acs, violations

def check_test_refs(record, where, ctx, acs):
    """tc_refs 解析（test-plan.yaml）+ 归属校验（tc.ac 须属本 story）。"""
    violations = []
    refs, ref_violations = ref_list(record, "tc_refs", where)
    violations += ref_violations
    if refs and not ctx["has_test_plan"]:
        violations.append(v("MISSING_FILE", "test-plan.yaml",
                            "test-plan.yaml 缺席：%d 条 tc_refs 无法解析（先跑 diy-test-design）"
                            % len(refs)))
        return violations
    known = set(acs)
    for i, ref in enumerate(refs):
        tc = ctx["tcs"].get(ref)
        if tc is None:
            violations.append(v("UNKNOWN_ID", "%s.tc_refs[%d]" % (where, i),
                                "%s 在 test-plan.yaml 中不存在" % ref))
        elif known and str(tc.get("ac")) not in known:
            violations.append(v("SET_MISMATCH", "%s.tc_refs[%d]" % (where, i),
                                "%s 归属 %s，不属于 %s" % (ref, tc.get("ac"), record.get("story"))))
    return violations

def check_api_refs(record, where, story_entry):
    """api_refs 归属校验：记录的复合锚 ⊆ 该故事全部 AC 的 api_refs 并集（三键全等）。"""
    violations = []
    api_refs = record.get("api_refs")
    if api_refs is None:
        return violations
    if not (isinstance(api_refs, list) and api_refs):
        violations.append(v("EMPTY_FIELD", where + ".api_refs",
                            "api_refs 形状异常（非空列表；缺席即省略）"))
        return violations
    if story_entry is None:
        return violations
    known = set()
    for ac in items(story_entry, "acceptance_criteria"):
        for anchor in (ac.get("api_refs") or []):
            if isinstance(anchor, dict):
                known.add((anchor.get("operationId"), anchor.get("path"),
                           anchor.get("method")))
    for i, anchor in enumerate(api_refs):
        aw = "%s.api_refs[%d]" % (where, i)
        if not isinstance(anchor, dict) or not all(
                isinstance(anchor.get(k), str) and anchor.get(k).strip()
                for k in ("operationId", "path", "method")):
            violations.append(v("EMPTY_FIELD", aw,
                                "复合锚形状异常（须含 operationId/path/method 三键）"))
            continue
        if (anchor.get("operationId"), anchor.get("path"),
                anchor.get("method")) not in known:
            violations.append(v("UNKNOWN_ID", aw,
                                "锚 %s %s（%s）不属于 %s 任一 AC 的 api_refs"
                                % (anchor.get("method"), anchor.get("path"),
                                   anchor.get("operationId"), record.get("story"))))
    return violations

def check_decisions(record, where, ctx):
    violations = []
    refs, ref_violations = ref_list(record, "decisions", where)
    violations += ref_violations
    if refs and not ctx["has_arch"]:
        violations.append(v("MISSING_FILE", "architecture.yaml",
                            "architecture.yaml 缺席：%d 条 decisions 无法解析" % len(refs)))
        return violations
    for i, ref in enumerate(refs):
        if ref not in ctx["decisions"]:
            violations.append(v("UNKNOWN_ID", "%s.decisions[%d]" % (where, i),
                                "%s 在 architecture.yaml 中不存在" % ref))
    return violations

def check_files(record, where, ctx, final):
    """files[] 现场勘察义务：更新 型必须存在且带 current_state；--final 另需 preserve。"""
    violations = []
    files = record.get("files")
    if files is None:
        return [v("EMPTY_FIELD", where + ".files",
                  "files 缺失（本故事将触碰的文件；无文件写空列表）")]
    if not isinstance(files, list):
        return [v("EMPTY_FIELD", where + ".files", "files 不是列表")]
    if final and not files:
        violations.append(v("EMPTY_FIELD", where + ".files",
                            "--final 要求 files 非空（至少一个将触碰的文件）"))
    for i, item in enumerate(files):
        fw = "%s.files[%d]" % (where, i)
        if not isinstance(item, dict):
            violations.append(v("EMPTY_FIELD", fw, "file 条目不是映射"))
            continue
        path = item.get("path")
        action = item.get("action")
        if not nonempty(path):
            violations.append(v("EMPTY_FIELD", fw + ".path", "path 缺失"))
        elif not is_safe_rel(path):
            violations.append(v("ENUM_INVALID", fw + ".path",
                                "path 须为相对 project-root 的正斜杠路径，实为 %s" % path))
        if not nonempty(action):
            violations.append(v("EMPTY_FIELD", fw + ".action", "action 缺失（新建|更新）"))
        elif str(action) not in FILE_ACTIONS:
            violations.append(v("ENUM_INVALID", fw + ".action",
                                "action 越界：%s（合法集 %s）"
                                % (action, "|".join(FILE_ACTIONS))))
        if not nonempty(item.get("why")):
            violations.append(v("EMPTY_FIELD", fw + ".why", "why 缺失（一行说明该文件为何被触碰）"))
        if str(action) != "更新" or not nonempty(path) or not is_safe_rel(path):
            continue
        if not os.path.isfile(rel_to_root(ctx["root"], path)):
            violations.append(v("MISSING_FILE", fw + ".path",
                                "更新 目标不存在：%s（新建 型才会被创建）" % path))
        if not nonempty(item.get("current_state")):
            violations.append(v("EMPTY_FIELD", fw + ".current_state",
                                "更新 型必填：先读该文件，写它今天的行为"))
        elif final and not nonempty(item.get("preserve")):
            violations.append(v("EMPTY_FIELD", fw + ".preserve",
                                "--final 要求 更新 型写明须保持的既有行为"))
    return violations

def text_list(record, key, where):
    """字符串列表键的形状校验（可缺席；缺席视为空）。"""
    value = record.get(key)
    if value is None:
        return []
    if not isinstance(value, list):
        return [v("EMPTY_FIELD", "%s.%s" % (where, key), "%s 不是列表" % key)]
    violations = []
    for i, item in enumerate(value):
        if not nonempty(item):
            violations.append(v("EMPTY_FIELD", "%s.%s[%d]" % (where, key, i),
                                "%s 项不得为空" % key))
    return violations

def check_final_duties(record, where, status):
    """--final 附加义务：status 已落 已定稿、verify 非空、open_questions 闭合、零假设。"""
    violations = []
    if str(status) != "已定稿":
        violations.append(v("STATUS_MISMATCH", where + ".status",
                            "--final 要求 status 已落 已定稿（实为 %s）" % status))
    if not items(record, "verify"):
        violations.append(v("EMPTY_FIELD", where + ".verify",
                            "--final 要求 verify 非空（命令级完成判据）"))
    for i, question in enumerate(items(record, "open_questions")):
        if not str(question).startswith(CLOSED_PREFIX):
            violations.append(v("PENDING_DECISION", "%s.open_questions[%d]" % (where, i),
                                "open_questions 须清零或逐条以 %s 标注处置" % CLOSED_PREFIX))
    if any("[假设]" in s for _p, s in walk_strings(record, "")):
        violations.append(v("ASSUMPTION_PRESENT", where,
                            "--final 要求零 [假设]；未决推断须先落定"))
    return violations

def check_record(index, record, ctx, final, where_base):
    where = "%s.contexts[%d]" % (where_base, index)
    if not isinstance(record, dict):
        return [v("EMPTY_FIELD", where, "记录不是映射")]
    violations = check_identity(record, where)
    story_entry, acs, story_violations = check_story_binding(record, where, ctx)
    violations += story_violations
    if story_entry is not None:
        acs = ac_ids(story_entry)
    violations += check_test_refs(record, where, ctx, acs)
    violations += check_api_refs(record, where, story_entry)
    violations += check_decisions(record, where, ctx)
    violations += check_files(record, where, ctx, final)
    violations += text_list(record, "risks", where)
    violations += text_list(record, "verify", where)
    violations += text_list(record, "open_questions", where)
    prior = record.get("prior_story")
    if prior is not None and not isinstance(prior, dict):
        violations.append(v("EMPTY_FIELD", where + ".prior_story", "prior_story 不是映射"))
    elif isinstance(prior, dict):
        if not nonempty(prior.get("ref")):
            violations.append(v("EMPTY_FIELD", where + ".prior_story.ref", "ref 缺失（S-y）"))
        elif ctx["has_stories"] and str(prior["ref"]) not in ctx["stories"]:
            violations.append(v("UNKNOWN_ID", where + ".prior_story.ref",
                                "%s 在 stories.yaml 中不存在" % prior["ref"]))
        carry = prior.get("carryover")
        if carry is not None and not isinstance(carry, list):
            violations.append(v("EMPTY_FIELD", where + ".prior_story.carryover",
                                "carryover 不是列表"))
    if final:
        violations += check_final_duties(record, where, record.get("status"))
    return violations
