# -*- coding: utf-8 -*-
"""diy-product-brief 校验域：评审/枚举常量、target 归一与计数助手、brief 段落/决策/修订/评审证据校验族。."""

import os
import re

import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import display_path, load_yaml_safe, nonempty, v  # noqa: E402
REVIEW_FILE = "editorial-review.yaml"
REVIEW_SCRIPT_REL = ("diy-editorial-review", "scripts", "editorial_review.py")
REVIEW_STATUS = "已定稿"
REVIEW_LENSES = ("结构", "文风")
DOC_STATUSES = ("草稿", "已定稿")
STAKES = ("个人兴趣", "内部", "投资人", "公开")
DECISION_STATUSES = ("生效", "已反转")

BD_RE = re.compile(r"BD-\d{3}")
# v4 批 3（§7-3b/d）：时间格式两格式兼容——纯日期 | 日期＋空格＋时分秒（秒级真值）
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}( \d{2}:\d{2}:\d{2})?")

def normalize_rel(value, project_root):
    """target 归一化（任务书 §12.1 ①ⓒ(5)，**四步顺序不可换**）：① `os.path.normpath`
    → ② `replace("\\", "/")` 统一正斜杠（Windows 下 ① 产反斜杠）→ ③ 转为相对
    `project_root` 的形式 → ④ 返回比较用串。两侧——ER 记录的 `target` 与本
    `brief.yaml`——各跑一次再一次比较；指向别处的记录不构成本文档的证据。"""
    step = os.path.normpath(str(value)).replace("\\", "/")           # ① ②
    absolute = step if os.path.isabs(step) else os.path.join(project_root, step)
    try:
        rel = os.path.relpath(absolute, project_root)                # ③
    except ValueError:                                               # 跨盘（Windows）不可相对化
        return os.path.abspath(absolute).replace("\\", "/")
    if rel.startswith(".."):                                         # 越界（对齐 display_path）
        return os.path.abspath(absolute).replace("\\", "/")
    return rel.replace("\\", "/")

def list_len(value):
    return len(value) if isinstance(value, list) else 0

# ---- check ----

def check_text_list(value, where, label, violations):
    """字符串列表：非列表 → EMPTY_FIELD；元素空或非标量 → EMPTY_FIELD。"""
    if value is None or (isinstance(value, list) and not value):
        return []
    if not isinstance(value, list):
        violations.append(v("EMPTY_FIELD", where, "%s 不是列表" % label))
        return []
    for i, item in enumerate(value):
        if isinstance(item, (dict, list)) or not nonempty(item):
            violations.append(v("EMPTY_FIELD", "%s[%d]" % (where, i), "%s 条目为空" % label))
    return value

def check_pairs(value, where, keys, label, violations, optional=()):
    """映射列表：每项须为映射；keys 恒非空；optional 键出现时不得为空。"""
    if value is None:
        return
    if not isinstance(value, list):
        violations.append(v("EMPTY_FIELD", where, "%s 不是列表" % label))
        return
    for i, item in enumerate(value):
        iw = "%s[%d]" % (where, i)
        if not isinstance(item, dict):
            violations.append(v("EMPTY_FIELD", iw, "%s 条目不是映射" % label))
            continue
        for key in list(keys) + [k for k in optional if k in item]:
            if not nonempty(item.get(key)):
                violations.append(v("EMPTY_FIELD", "%s.%s" % (iw, key), "%s 为空" % key))

def check_brief_section(brief, where, final, violations):
    if brief is None:
        violations.append(v("EMPTY_FIELD", where, "brief 缺失（单文档主体）"))
        return {}
    if not isinstance(brief, dict):
        violations.append(v("EMPTY_FIELD", where, "brief 不是映射"))
        return {}

    stakes = brief.get("stakes")
    if nonempty(stakes) and str(stakes) not in STAKES:
        violations.append(v("ENUM_INVALID", where + ".stakes",
                            "stakes 越界：%s（合法集 %s）" % (stakes, "|".join(STAKES))))

    check_pairs(brief.get("users"), where + ".users", ("who", "need"), "users", violations)
    check_pairs(brief.get("value"), where + ".value", ("point",), "value", violations,
                optional=("evidence",))
    check_pairs(brief.get("extra_sections"), where + ".extra_sections",
                ("name", "content"), "extra_sections", violations)
    check_text_list(brief.get("open_questions"), where + ".open_questions",
                    "open_questions", violations)
    check_text_list(brief.get("assumptions"), where + ".assumptions",
                    "assumptions", violations)

    if final:
        for key in ("title", "problem", "solution"):
            if not nonempty(brief.get(key)):
                violations.append(v("EMPTY_FIELD", "%s.%s" % (where, key),
                                    "--final 要求 %s 非空" % key))
        users = brief.get("users")
        if not isinstance(users, list) or not users:
            violations.append(v("EMPTY_FIELD", where + ".users",
                                "--final 要求 users 非空"))
        if isinstance(brief.get("assumptions"), list) and brief["assumptions"]:
            violations.append(v("ASSUMPTION_PRESENT", where + ".assumptions",
                                "--final 要求 assumptions 清空（未决假设先落定或转 open_questions）"))
    return brief

def check_decisions(decisions, where, final, violations):
    if decisions is None:
        return []
    if not isinstance(decisions, list):
        violations.append(v("EMPTY_FIELD", where, "decisions 不是列表"))
        return []
    seen = set()
    for i, item in enumerate(decisions):
        iw = "%s[%d]" % (where, i)
        if not isinstance(item, dict):
            violations.append(v("EMPTY_FIELD", iw, "decision 条目不是映射"))
            continue
        rid = item.get("id")
        if not nonempty(rid):
            violations.append(v("EMPTY_FIELD", iw + ".id", "id 缺失"))
        elif not BD_RE.fullmatch(str(rid)):
            violations.append(v("ENUM_INVALID", iw + ".id",
                                "id 须为 BD-0nn（三位零填充），实为 %s" % rid))
        elif str(rid) in seen:
            violations.append(v("DUPLICATE_ID", iw + ".id",
                                "决策 ID %s 重复（BD ID 稳定不重用）" % rid))
        else:
            seen.add(str(rid))
        date = item.get("date")
        if not nonempty(date):
            violations.append(v("EMPTY_FIELD", iw + ".date", "date 缺失"))
        elif not DATE_RE.fullmatch(str(date)):
            violations.append(v("ENUM_INVALID", iw + ".date",
                                "date 须为 YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS，实为 %s" % date))
        if not nonempty(item.get("decision")):
            violations.append(v("EMPTY_FIELD", iw + ".decision", "decision 为空"))
        status = item.get("status")
        if not nonempty(status):
            violations.append(v("EMPTY_FIELD", iw + ".status", "status 缺失"))
        elif str(status) not in DECISION_STATUSES:
            violations.append(v("ENUM_INVALID", iw + ".status",
                                "status 越界：%s（合法集 %s）"
                                % (status, "|".join(DECISION_STATUSES))))
        if final and not nonempty(item.get("rationale")):
            violations.append(v("EMPTY_FIELD", iw + ".rationale",
                                "--final 要求每条决策有 rationale（规范记忆的判据）"))
    return decisions

def check_addendum(addendum, where, violations):
    if addendum is None:
        return []
    if not isinstance(addendum, list):
        violations.append(v("EMPTY_FIELD", where, "addendum 不是列表"))
        return []
    for i, item in enumerate(addendum):
        iw = "%s[%d]" % (where, i)
        if not isinstance(item, dict):
            violations.append(v("EMPTY_FIELD", iw, "addendum 条目不是映射"))
            continue
        for key in ("section", "content", "why_separate"):
            if not nonempty(item.get(key)):
                violations.append(v("EMPTY_FIELD", "%s.%s" % (iw, key),
                                    "%s 为空（why_separate 记录为何不进简报正文）" % key))
    return addendum

def check_revisions(revisions, where, violations):
    if revisions is None:
        return []
    if not isinstance(revisions, list):
        violations.append(v("EMPTY_FIELD", where, "revisions 不是列表"))
        return []
    for i, item in enumerate(revisions):
        iw = "%s[%d]" % (where, i)
        if not isinstance(item, dict):
            violations.append(v("EMPTY_FIELD", iw, "revision 条目不是映射"))
            continue
        for key in ("date", "change", "reason"):
            if not nonempty(item.get(key)):
                violations.append(v("EMPTY_FIELD", "%s.%s" % (iw, key), "%s 为空" % key))
        date = item.get("date")
        if nonempty(date) and not DATE_RE.fullmatch(str(date)):
            violations.append(v("ENUM_INVALID", iw + ".date",
                                "date 须为 YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS，实为 %s" % date))
    return revisions

def check_project(project, where, violations, final):
    if not isinstance(project, dict):
        violations.append(v("EMPTY_FIELD", where, "project 缺失或不是映射"))
        return
    status = project.get("status")
    if not nonempty(status):
        violations.append(v("EMPTY_FIELD", where + ".status", "status 缺失（草稿|已定稿）"))
    elif str(status) not in DOC_STATUSES:
        violations.append(v("ENUM_INVALID", where + ".status",
                            "status 越界：%s（合法集 %s）"
                            % (status, "|".join(DOC_STATUSES))))
    elif final and str(status) != "已定稿":
        violations.append(v("STATUS_MISMATCH", where + ".status",
                            "--final 要求 project.status 为「已定稿」（先落定稿，再跑门禁）"))
    # 批 3 追裁②（2026-10-15）：补非空门——留空＝未盖章（防忘跑 diyc stamp 闭环断口）
    for key in ("created", "updated"):
        value = project.get(key)
        if not nonempty(value):
            violations.append(v("EMPTY_FIELD", "%s.%s" % (where, key),
                                "%s 留空＝未盖章，跑 diyc stamp --type brief 盖秒级章" % key))
        elif not DATE_RE.fullmatch(str(value)):
            violations.append(v("ENUM_INVALID", "%s.%s" % (where, key),
                                "%s 须为 YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS，实为 %s" % (key, value)))

def previous_ids(previous, project_root, violations):
    """读旧稿快照的 BD-### 集合；读失败记违规并返回 None。"""
    show = display_path(previous, project_root)
    data, err = load_yaml_safe(previous)
    if data is None and err is None:
        violations.append(v("MISSING_FILE", show,
                            "旧稿快照不存在（更新重写前先 cp brief.yaml brief.yaml.prev）"))
        return None
    if err is not None:
        violations.append(v("UNPARSABLE_YAML", show, "旧稿快照不可解析：%s" % err))
        return None
    if not isinstance(data, dict):
        violations.append(v("EMPTY_FIELD", show, "旧稿快照顶层不是映射"))
        return None
    items = data.get("decisions")
    if not isinstance(items, list):
        return set()
    return {str(d["id"]) for d in items
            if isinstance(d, dict) and nonempty(d.get("id"))}

def review_script_path():
    """diy-editorial-review 的引擎路径：由本引擎自身位置推算 skills 根
    （源码与安装两种布局同构，对齐 readiness 的 diyc_script_path 先例）。"""
    skills_root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    return os.path.join(skills_root, *REVIEW_SCRIPT_REL)

# trace: B4 任务书 §12.1 ①ⓒ（--final 评审证据链：review_refs → editorial-review.yaml 的 ER-###）
def check_review_evidence(data, root, out, path, show, violations, warnings):
    """--final 的六条证据校验：`review_refs` 非空 → 台账在场 → ID 在 `reviews[]` 内 →
    该记录 `status: 已定稿` → `target` 归一化后指向本 `brief.yaml` → `lenses` 两透镜齐全
    （忠实源 `doc_standards` 的两条 append-only 标准提供者语义）。派发不可用（环境缺兄弟
    引擎）→ `TOOL_MISSING` 降级：六条一并转 warning、放行；与「技能在场而记录缺失或不合格
    → 硬拒」分工不重叠——前者是环境问题、后者是产物问题。"""
    script = review_script_path()
    if not os.path.isfile(script):
        warnings.append(v("TOOL_MISSING", display_path(script, root),
                          "diy-editorial-review 引擎缺席：评审证据校验（六条）降级为 warning、"
                          "--final 放行；请从会话侧人工确认本稿已过结构 + 文风两透镜评审"))
        return
    raw_refs = data.get("review_refs")
    refs = [str(r) for r in raw_refs if nonempty(r)] if isinstance(raw_refs, list) else []
    if not refs:
        violations.append(v("EVIDENCE_MISSING", show + " review_refs",
                            "--final 要求 review_refs 非空（存量的已定稿记录同样要补，"
                            "不静默放行）：调 diy-editorial-review 评审本稿，"
                            "把 ER-### 写进 review_refs 再定稿"))
        return
    review_path = os.path.join(out, REVIEW_FILE)
    review_show = display_path(review_path, root)
    review, err = load_yaml_safe(review_path)
    if review is None and err is None:
        violations.append(v("MISSING_FILE", review_show,
                            "%s 不存在：review_refs 指向的记录无处可查"
                            "（先调 diy-editorial-review 产出 ER-###）" % REVIEW_FILE))
        return
    if err is not None:
        violations.append(v("UNPARSABLE_YAML", review_show, "评审台账不可解析：%s" % err))
        return
    if not isinstance(review, dict):
        violations.append(v("EMPTY_FIELD", review_show, "评审台账顶层不是映射"))
        return
    raw_records = review.get("reviews")
    records = raw_records if isinstance(raw_records, list) else []
    by_id = {}
    for item in records:
        if isinstance(item, dict) and nonempty(item.get("id")):
            by_id.setdefault(str(item["id"]), item)
    brief_rel = normalize_rel(path, root)
    for rid in refs:
        record = by_id.get(rid)
        if record is None:
            violations.append(v("UNKNOWN_ID", show + " review_refs",
                                "%s 不在 %s 的 reviews[] 内" % (rid, review_show)))
            continue
        rw = "%s reviews[%s]" % (review_show, rid)
        status = record.get("status")
        if str(status) != REVIEW_STATUS:
            violations.append(v("STATUS_MISMATCH", rw + ".status",
                                "--final 要求证据记录 status: 已定稿，实为 %s"
                                % (status if nonempty(status) else "缺失")))
        target = record.get("target")
        if not nonempty(target) or normalize_rel(target, root) != brief_rel:
            violations.append(v("EVIDENCE_MISSING", rw + ".target",
                                "该记录评审的是 %s，不是本 brief.yaml"
                                "——指向别处的记录不构成本文档的证据"
                                % (target if nonempty(target) else "（target 缺失）")))
        lenses = record.get("lenses")
        seen = {str(x) for x in lenses} if isinstance(lenses, list) else set()
        if set(REVIEW_LENSES) - seen:
            violations.append(v("EVIDENCE_MISSING", rw + ".lenses",
                                "该记录 lenses=%s 未同时含 结构 与 文风"
                                "（定稿路径要求两透镜齐全）" % (lenses,)))
