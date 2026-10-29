# -*- coding: utf-8 -*-
"""diy-brainstorm 校验命令域：三级稳定 ID（想法 `BI-###` / 主题聚类 `BT-###` / 行动计划
`BA-###`）的形态·文件内唯一·引用完整性、记录级 schema 枚举锚点校验、--final 定稿义务、
--previous 三失败分支对账（load_previous / check_previous，三级全参与）与 cmd_check 总编排
（含随行常量 DEFAULT_CANDIDATES、STEP_MIN/STEP_MAX、LEVELS）。"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import display_path, is_int, load_yaml_safe, nonempty, receipt_base, v, walk_strings  # noqa: E402

from brainstorm_lib import APPROACH_ENUM, ASSUMPTION_MARK, BRAINSTORM_FILE, BS_RE, DATE_RE, STATUS_ENUM, STEP_BY_STATUS, emit, library_categories, load_methods  # noqa: E402
STEP_MIN, STEP_MAX = 1, 5
DEFAULT_CANDIDATES = 5

# 三级稳定 ID：(键, 前缀, 中文名, 正则, 旧键)。
# 三位零填充；**文件内按前缀全局唯一**（前缀天然隔离，不跨级比较）。
# 稳定 ID 不重编号 → 空号合法，故不设「连续不跳号」约束（SET_MISMATCH 随 `no` 退场不再触发）。
IDEA_RE = re.compile(r"BI-\d{3}\Z")
THEME_RE = re.compile(r"BT-\d{3}\Z")
ACTION_RE = re.compile(r"BA-\d{3}\Z")
LEVELS = (("ideas", "BI", "想法", IDEA_RE, "no"),
          ("themes", "BT", "主题聚类", THEME_RE, None),
          ("actions", "BA", "行动计划", ACTION_RE, None))

# ---- check ----

def _items(record, key):
    """记录内某级条目（非映射条目不入——形状问题由各段检查上报）。"""
    raw = record.get(key)
    return [x for x in raw if isinstance(x, dict)] if isinstance(raw, list) else []

def check_idea_refs(refs, where, ids):
    """引用检查：`BI-###` 必须落在本记录的 `ideas[].id` 集合内（否则 UNKNOWN_ID）。"""
    violations = []
    if not isinstance(refs, list):
        return [v("EMPTY_FIELD", where, "缺失或不是列表（无引用写空列表）")]
    for i, ref in enumerate(refs):
        if isinstance(ref, str) and ref.strip() in ids:
            continue
        violations.append(v("UNKNOWN_ID", "%s[%d]" % (where, i),
                            "%s 不在本记录 ideas[].id 内（可引用集 %s）"
                            % (ref, sorted(ids) or "空")))
    return violations

def check_stable_ids(record, where):
    """三级稳定 ID 形态：条目在场须铸 id，前缀与三位序号正确（缺失/越界各一码）。"""
    violations = []
    for key, prefix, label, pattern, _legacy in LEVELS:
        for i, item in enumerate(_items(record, key)):
            iw = "%s.%s[%d].id" % (where, key, i)
            iid = item.get("id")
            if not nonempty(iid):
                violations.append(v("EMPTY_FIELD", iw,
                                    "%s缺稳定 id（铸 %s-###，全文件按前缀唯一）" % (label, prefix)))
            elif not pattern.fullmatch(str(iid).strip()):
                violations.append(v("ENUM_INVALID", iw,
                                    "%s id 须为 %s-###（三位零填充），实为 %s"
                                    % (label, prefix, iid)))
    return violations

def check_id_uniqueness(records, show):
    """三级 ID 文件内按前缀全局唯一（ruling：每级各自唯一、不跨级比较；重复 → DUPLICATE_ID）。"""
    violations = []
    seen = set()
    for i, record in enumerate(records):
        if not isinstance(record, dict):
            continue
        for key, _prefix, label, _pattern, _legacy in LEVELS:
            for j, item in enumerate(_items(record, key)):
                iid = item.get("id")
                if not nonempty(iid):
                    continue
                where = "%s.sessions[%d].%s[%d].id" % (show, i, key, j)
                mark = (label, str(iid).strip())
                if mark in seen:
                    violations.append(v("DUPLICATE_ID", where,
                                        "ID %s 重复（%s 全文件唯一，永不重用）" % (mark[1], label)))
                seen.add(mark)
    return violations

def check_ideas(record, where):
    violations = []
    ideas = record.get("ideas")
    if ideas is None:
        return [v("EMPTY_FIELD", where + ".ideas", "ideas 缺失（无内容写空列表）")]
    if not isinstance(ideas, list):
        return [v("EMPTY_FIELD", where + ".ideas", "ideas 不是列表")]
    for i, idea in enumerate(ideas):
        iw = "%s.ideas[%d]" % (where, i)
        if not isinstance(idea, dict):
            violations.append(v("EMPTY_FIELD", iw, "想法不是映射"))
            continue
        if "no" in idea:
            violations.append(v("ENUM_INVALID", iw + ".no",
                                "no 废字段——改写为 ideas[].id: BI-###"))
        for key in ("title", "concept", "novelty", "technique"):
            if not nonempty(idea.get(key)):
                violations.append(v("EMPTY_FIELD", iw + "." + key, "%s 为空" % key))
    return violations

def check_themes(record, where, ids):
    violations = []
    themes = record.get("themes")
    if themes is None:
        return [v("EMPTY_FIELD", where + ".themes", "themes 缺失（无内容写空列表）")]
    if not isinstance(themes, list):
        return [v("EMPTY_FIELD", where + ".themes", "themes 不是列表")]
    for i, theme in enumerate(themes):
        tw = "%s.themes[%d]" % (where, i)
        if not isinstance(theme, dict):
            violations.append(v("EMPTY_FIELD", tw, "主题不是映射"))
            continue
        for key in ("name", "focus"):
            if not nonempty(theme.get(key)):
                violations.append(v("EMPTY_FIELD", tw + "." + key, "%s 为空" % key))
        refs = theme.get("ideas")
        if refs is None:
            violations.append(v("EMPTY_FIELD", tw + ".ideas",
                                "ideas 缺失（无引用写空列表）"))
            continue
        violations += check_idea_refs(refs, tw + ".ideas", ids)
    return violations

def check_priorities(record, where, ids):
    violations = []
    priorities = record.get("priorities")
    if priorities is None:
        return [v("EMPTY_FIELD", where + ".priorities",
                  "priorities 缺失（三键 top / quick_wins / breakthroughs，无内容写空列表）")]
    if not isinstance(priorities, dict):
        return [v("EMPTY_FIELD", where + ".priorities", "priorities 不是映射")]
    for key in ("top", "quick_wins", "breakthroughs"):
        refs = priorities.get(key)
        if refs is None:
            violations.append(v("EMPTY_FIELD", "%s.priorities.%s" % (where, key),
                                "%s 缺失（无引用写空列表）" % key))
            continue
        violations += check_idea_refs(refs, "%s.priorities.%s" % (where, key), ids)
    return violations

def check_actions(record, where, ids):
    violations = []
    actions = record.get("actions")
    if actions is None:
        return [v("EMPTY_FIELD", where + ".actions", "actions 缺失（无内容写空列表）")]
    if not isinstance(actions, list):
        return [v("EMPTY_FIELD", where + ".actions", "actions 不是列表")]
    for i, action in enumerate(actions):
        aw = "%s.actions[%d]" % (where, i)
        if not isinstance(action, dict):
            violations.append(v("EMPTY_FIELD", aw, "行动计划不是映射"))
            continue
        if action.get("idea") is None:
            violations.append(v("EMPTY_FIELD", aw + ".idea",
                                "idea 缺失（须指向 ideas[].id 的 BI-###）"))
        else:
            violations += check_idea_refs([action.get("idea")], aw + ".idea", ids)
        for key in ("why", "resources", "timeline", "success"):
            if not nonempty(action.get(key)):
                violations.append(v("EMPTY_FIELD", aw + "." + key, "%s 为空" % key))
        steps = action.get("steps")
        if steps is None:
            violations.append(v("EMPTY_FIELD", aw + ".steps", "steps 缺失（至少一步）"))
        elif not isinstance(steps, list):
            violations.append(v("EMPTY_FIELD", aw + ".steps", "steps 不是列表"))
        else:
            if not steps:
                violations.append(v("EMPTY_FIELD", aw + ".steps", "steps 为空（至少一步）"))
            for j, step in enumerate(steps):
                if not nonempty(step):
                    violations.append(v("EMPTY_FIELD", "%s.steps[%d]" % (aw, j),
                                        "step 为空"))
    return violations

def check_record(index, record, final, categories, show):
    """单条记录的 schema / 枚举 / 引用 / 锚点一致性检查。"""
    violations = []
    where = "%s.sessions[%d]" % (show, index)
    if not isinstance(record, dict):
        return [v("EMPTY_FIELD", where, "记录不是映射")]

    rid = record.get("id")
    if not nonempty(rid):
        violations.append(v("EMPTY_FIELD", where + ".id", "id 缺失"))
    elif not BS_RE.fullmatch(str(rid).strip()):
        violations.append(v("ENUM_INVALID", where + ".id",
                            "id 须为 BS-0nn（三位零填充），实为 %s" % rid))

    for key in ("topic", "goals"):
        if not nonempty(record.get(key)):
            violations.append(v("EMPTY_FIELD", where + "." + key,
                                "%s 为空（会话门禁要求议题与目标在场）" % key))

    date = record.get("date")
    if not nonempty(date):
        violations.append(v("EMPTY_FIELD", where + ".date", "date 缺失"))
    elif not DATE_RE.fullmatch(str(date).strip()):
        violations.append(v("ENUM_INVALID", where + ".date",
                            "date 须为 YYYY-MM-DD，实为 %s" % date))

    approach = record.get("approach")
    if nonempty(approach) and str(approach) not in APPROACH_ENUM:
        violations.append(v("ENUM_INVALID", where + ".approach",
                            "approach 越界：%s（合法集 %s）"
                            % (approach, "|".join(APPROACH_ENUM))))

    status = record.get("status")
    status_ok = False
    if not nonempty(status):
        violations.append(v("EMPTY_FIELD", where + ".status", "status 缺失"))
    elif str(status) not in STATUS_ENUM:
        violations.append(v("ENUM_INVALID", where + ".status",
                            "status 越界：%s（合法集 %s）"
                            % (status, "|".join(STATUS_ENUM))))
    else:
        status_ok = True

    step = record.get("current_step")
    step_ok = False
    if not is_int(step):
        violations.append(v("ENUM_INVALID", where + ".current_step",
                            "current_step 须为 1-5 整数，实为 %r" % (step,)))
    elif not (STEP_MIN <= step <= STEP_MAX):
        violations.append(v("ENUM_INVALID", where + ".current_step",
                            "current_step 越界：%s（合法集 1-5）" % step))
    else:
        step_ok = True

    if status_ok and step_ok:
        legal = STEP_BY_STATUS[str(status)]
        if step not in legal:
            violations.append(v("STATUS_MISMATCH", where + ".current_step",
                                "status: %s 要求 current_step ∈ %s，实为 %s（续接锚点必须与"
                                "会话阶段同档）"
                                % (status, "|".join(str(x) for x in legal), step)))
        if step >= 2 and not nonempty(approach):
            violations.append(v("EMPTY_FIELD", where + ".approach",
                                "current_step: %s 要求 approach 已选（%s）"
                                % (step, "|".join(APPROACH_ENUM))))

    techniques = record.get("techniques")
    if techniques is None:
        violations.append(v("EMPTY_FIELD", where + ".techniques",
                            "techniques 缺失（无内容写空列表）"))
    elif not isinstance(techniques, list):
        violations.append(v("EMPTY_FIELD", where + ".techniques", "techniques 不是列表"))
    else:
        for i, technique in enumerate(techniques):
            tw = "%s.techniques[%d]" % (where, i)
            if not isinstance(technique, dict):
                violations.append(v("EMPTY_FIELD", tw, "技术条目不是映射"))
                continue
            for key in ("name", "category"):
                if not nonempty(technique.get(key)):
                    violations.append(v("EMPTY_FIELD", tw + "." + key, "%s 为空" % key))
            category = technique.get("category")
            if nonempty(category) and categories and str(category) not in categories:
                violations.append(v("ENUM_INVALID", tw + ".category",
                                    "category 越界：%s（合法集 = 技术库类名 %s）"
                                    % (category, "|".join(categories))))
        if step_ok and step >= 3 and not techniques:
            violations.append(v("EMPTY_FIELD", where + ".techniques",
                                "current_step: %s 要求已选技术（step 2 的产出）" % step))

    violations += check_ideas(record, where)
    ids = {str(x["id"]).strip() for x in _items(record, "ideas") if nonempty(x.get("id"))}
    violations += check_themes(record, where, ids)
    violations += check_priorities(record, where, ids)
    violations += check_actions(record, where, ids)
    violations += check_stable_ids(record, where)

    questions = record.get("open_questions")
    if questions is None:
        violations.append(v("EMPTY_FIELD", where + ".open_questions",
                            "open_questions 缺失（无内容写空列表）"))
    elif not isinstance(questions, list):
        violations.append(v("EMPTY_FIELD", where + ".open_questions",
                            "open_questions 不是列表"))
    else:
        for i, question in enumerate(questions):
            if not nonempty(question):
                violations.append(v("EMPTY_FIELD", "%s.open_questions[%d]" % (where, i),
                                    "条目为空"))

    if step_ok and step == STEP_MAX:
        # 源纪律「无行动计划不得收尾」：收尾态必须有组织结论与行动计划
        for key, msg in (("themes", "至少 1 个主题"),
                         ("actions", "至少 1 条行动计划")):
            if isinstance(record.get(key), list) and not record[key]:
                violations.append(v("EMPTY_FIELD", where + "." + key,
                                    "current_step: 5 要求%s（组织步的产出）" % msg))
        priorities = record.get("priorities")
        if isinstance(priorities, dict) and not priorities.get("top"):
            violations.append(v("EMPTY_FIELD", where + ".priorities.top",
                                "current_step: 5 要求 top 非空（优先级四维的收敛结果）"))

    if final:
        violations += check_final_duties(record, where, status)
    return violations

def check_final_duties(record, where, status):
    """`--final` 附加义务：`status: 已完成` + 零 `[假设]`（定稿前清零）。"""
    violations = []
    if str(status) != "已完成":
        violations.append(v("STATUS_MISMATCH", where + ".status",
                            "--final 要求 status: 已完成，实为 %s（先走完 5 步收尾）" % status))
    if any(ASSUMPTION_MARK in text for _p, text in walk_strings(record, "")):
        violations.append(v("ASSUMPTION_PRESENT", where,
                            "--final 要求零 [假设]；未决项写进 open_questions 再定稿"))
    return violations

def load_previous(prev_path, root):
    """读 .prev → (doc|None, violations)：缺失 → MISSING_FILE；不可解析 → UNPARSABLE_YAML。"""
    prev_show = display_path(prev_path, root)
    data, err = load_yaml_safe(prev_path)
    if data is None and err is None:
        return None, [v("MISSING_FILE", prev_show, "旧稿快照 .prev 缺失（每轮开工先跑 snapshot）")]
    if err is not None:
        return None, [v("UNPARSABLE_YAML", prev_show, "旧稿快照解析失败：%s（兜底失效，停手告知用户）" % err)]
    if not isinstance(data, dict):
        return None, [v("UNPARSABLE_YAML", prev_show, "旧稿快照顶层不是映射（须为 project + sessions）")]
    return data, []

def _index(records):
    """配对面 {BS-###: record}：非映射 / 空 id 条目不入（形状问题由 check_record 上报）。"""
    return {str(r["id"]).strip(): r for r in records
            if isinstance(r, dict) and nonempty(r.get("id"))}

def _face(record, key, legacy=None):
    """记录内某级标识集：id 面（BI/BT/BA）；legacy 给旧键面（仅 ideas 的 no）且无 id 时用。"""
    items = _items(record, key)
    if legacy is None:
        return {str(x["id"]).strip() for x in items if nonempty(x.get("id"))}
    return {x.get(legacy) for x in items if is_int(x.get(legacy))}

def check_previous(prev_doc, records, show, prev_show):
    """ID 稳定对账（三失败分支之 ID_UNSTABLE，三级）：旧稿有、新稿无的
    会话记录 / 记录内想法·主题聚类·行动计划标识 → ID_UNSTABLE；某级从无 id 迁到有 id 的那一轮
    （迁移轮）跳过该级比对，首拍 / 迁移不误报。"""
    violations = []
    prev_raw = prev_doc.get("sessions")
    prev_recs = _index(prev_raw if isinstance(prev_raw, list) else [])
    cur_recs = _index(records)
    for rid in sorted(set(prev_recs) - set(cur_recs)):
        violations.append(v("ID_UNSTABLE", "%s.sessions[id=%s]" % (show, rid),
                            "会话记录 %s 旧稿有、新稿无（BS ID 稳定不重用；对照 %s）" % (rid, prev_show)))
    for rid in sorted(set(prev_recs) & set(cur_recs)):
        old, new = prev_recs[rid], cur_recs[rid]
        for key, _prefix, label, _pattern, legacy in LEVELS:
            old_ids, new_ids = _face(old, key), _face(new, key)
            if old_ids:
                gone, tag = sorted(old_ids - new_ids), "id"
            elif new_ids:
                continue  # 迁移轮（该级无 id → 有 id 当轮）：跳过比对，不误报
            elif legacy:
                gone, tag = sorted(_face(old, key, legacy) - _face(new, key, legacy)), legacy
            else:
                continue  # 改版前的 themes/actions 两侧皆无 id：无稳定标识可比对
            violations += [v("ID_UNSTABLE",
                             "%s.sessions[id=%s].%s[%s=%s]" % (show, rid, key, tag, k),
                             "%s %s 旧稿有、新稿无（丢失即下游断链；对照 %s）"
                             % (label, k, prev_show)) for k in gone]
    return violations

def cmd_check(args):
    root = os.path.abspath(args.project_root)
    out = os.path.abspath(args.output_dir)
    path = os.path.join(out, BRAINSTORM_FILE)
    show = display_path(path, root)
    payload = receipt_base("check", args, out)
    violations = []
    warnings = []
    records = []
    categories = None

    rows, lib_violations = load_methods(root)
    if lib_violations:
        warnings += lib_violations  # 库缺席 → 类名枚举降级（不阻断产物校验）
    else:
        categories = library_categories(rows)

    data, err = load_yaml_safe(path)
    if data is None and err is None:
        violations.append(v("MISSING_FILE", show,
                            "%s 不存在（先跑 init 建会话记录）" % BRAINSTORM_FILE))
    elif err is not None:
        violations.append(v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err))
    elif not isinstance(data, dict):
        violations.append(v("EMPTY_FIELD", show, "顶层不是映射（须为 project + sessions）"))
    else:
        project = data.get("project")
        if project is not None and not isinstance(project, dict):
            violations.append(v("EMPTY_FIELD", show + " project", "project 不是映射"))
        revisions = data.get("revisions")
        if revisions is not None and not isinstance(revisions, list):
            violations.append(v("EMPTY_FIELD", show + " revisions", "revisions 不是列表"))
        raw = data.get("sessions")
        if raw is None:
            violations.append(v("EMPTY_FIELD", show + " sessions",
                                "sessions 缺失（集合形态；无记录写空列表）"))
        elif not isinstance(raw, list):
            violations.append(v("EMPTY_FIELD", show + " sessions", "sessions 不是列表"))
        else:
            records = raw
            seen = set()
            for i, record in enumerate(records):
                if isinstance(record, dict) and nonempty(record.get("id")):
                    rid = str(record["id"]).strip()
                    if rid in seen:
                        violations.append(v("DUPLICATE_ID", "%s.sessions[%d].id" % (show, i),
                                            "记录 ID %s 重复（BS ID 稳定不重用）" % rid))
                    seen.add(rid)
            # 三级稳定 ID 的文件内唯一性独立成趟（ruling：全文件按前缀唯一，不随 --id 收窄）
            violations += check_id_uniqueness(records, show)
            target_id = str(args.id).strip() if nonempty(args.id) else None
            if target_id is not None and target_id not in seen:
                violations.append(v("UNKNOWN_ID", "check --id",
                                    "%s 不在 %s 的 sessions[] 内" % (target_id, show)))
            for i, record in enumerate(records):
                if target_id is not None and (
                        not isinstance(record, dict)
                        or str(record.get("id") or "").strip() != target_id):
                    continue
                violations += check_record(i, record, args.final, categories, show)
            if args.final and not records:
                violations.append(v("EMPTY_FIELD", show + " sessions",
                                    "--final 要求至少 1 条会话记录"))
            if args.previous:
                prev_doc, prev_violations = load_previous(path + ".prev", root)
                violations += prev_violations
                if prev_doc is not None:
                    violations += check_previous(prev_doc, records, show, display_path(path + ".prev", root))

    statuses = {}
    ideas = 0
    for record in records:
        if not isinstance(record, dict):
            continue
        if nonempty(record.get("status")):
            statuses[str(record["status"])] = statuses.get(str(record["status"]), 0) + 1
        if isinstance(record.get("ideas"), list):
            ideas += len(record["ideas"])
    payload["ok"] = not violations
    payload["violations"] = violations
    payload["warnings"] = warnings
    payload["final"] = bool(args.final)
    payload["counts"] = {"sessions": len(records), "by_status": statuses, "ideas": ideas}
    return emit(payload, args.json,
                "PASS：%s 校验通过（sessions=%d / ideas=%d%s）"
                % (show, len(records), ideas, " / --final" if args.final else ""))
