# -*- coding: utf-8 -*-
"""diy-prfaq 校验域：schema 枚举与 PQ/日期常量、FAQ 取号助手与 project/stage/FAQ/press/distillate/前稿校验族。."""

import os
import re

import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import display_path, load_yaml_safe, nonempty, v, walk_strings  # noqa: E402

PRFAQ_FILE = "prfaq.yaml"

CONCEPT_TYPES = ("商业", "内部", "开源", "社区")
STAGES = (1, 2, 3, 4, 5)
STRENGTHS = ("已锤炼", "欠火候", "地基裂缝")
PROJECT_STATUSES = ("草稿", "已定稿")
ESSENTIAL_KEYS = ("customer", "problem", "stakes", "solution")
# 源 assets/prfaq-template.md 的九节结构（Press Release 锻造面）
PRESS_KEYS = ("headline", "subheadline", "opening", "problem", "solution",
              "leader_quote", "how_it_works", "customer_quote", "getting_started")
# 源 references/verdict.md "Produce the Distillate" 的九类内容收敛入这五个键
DISTILLATE_KEYS = ("problem", "target_users", "value_props", "constraints",
                   "open_questions")
DISTILLATE_SCALARS = ("problem", "target_users")
DISTILLATE_LISTS = ("value_props", "constraints", "open_questions")

PQ_RE = re.compile(r"PQ-\d{3}")
# v4 批 3（§7-3b/d）：时间格式两格式兼容——纯日期 | 日期＋空格＋时分秒（秒级真值）
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}( \d{2}:\d{2}:\d{2})?")

def faq_ids(data):
    """文档内 PQ ID 集合（客户 FAQ ∪ 内部 FAQ——单一序列，见模块 docstring）。"""
    ids = set()
    doc = data.get("prfaq") if isinstance(data, dict) else None
    if not isinstance(doc, dict):
        return ids
    for key in ("customer_faq", "internal_faq"):
        items = doc.get(key)
        if not isinstance(items, list):
            continue
        for item in items:
            if isinstance(item, dict) and nonempty(item.get("id")):
                ids.add(str(item["id"]))
    return ids

def pq_sort(ids):
    """PQ-### 数字感知排序（PQ-2 < PQ-10）。"""
    def key(value):
        parts = str(value).split("-")
        return int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
    return sorted(ids, key=key)

# ---- check ----

def check_project(project, show, violations):
    """project 块：形状 + status 枚举（定稿义务在 check_final_duties）。"""
    if project is None:
        return
    if not isinstance(project, dict):
        violations.append(v("EMPTY_FIELD", show + " project", "project 不是映射"))
        return
    status = project.get("status")
    if nonempty(status) and str(status) not in PROJECT_STATUSES:
        violations.append(v("ENUM_INVALID", show + " project.status",
                            "status 越界：%s（合法集 %s）"
                            % (status, "|".join(PROJECT_STATUSES))))
    # 批 3 追裁②（2026-10-15）：created/updated 补非空门＋格式断——留空＝未盖章
    # （防忘跑 diyc stamp 闭环断口）；两格式同 brief 口径
    for key in ("created", "updated"):
        value = project.get(key)
        if not nonempty(value):
            violations.append(v("EMPTY_FIELD", "%s.project.%s" % (show, key),
                                "project.%s 留空＝未盖章，跑 diyc stamp --type prfaq 盖秒级章" % key))
        elif not DATE_RE.fullmatch(str(value)):
            violations.append(v("ENUM_INVALID", "%s.project.%s" % (show, key),
                                "project.%s 须为 YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS，实为 %s"
                                % (key, value)))

def check_revisions(revisions, show, violations):
    """revisions 段（§2.4 机制）：列表，条目 {date, change, reason} 三键非空。"""
    if revisions is None:
        return
    if not isinstance(revisions, list):
        violations.append(v("EMPTY_FIELD", show + " revisions", "revisions 不是列表"))
        return
    for i, entry in enumerate(revisions):
        where = "%s revisions[%d]" % (show, i)
        if not isinstance(entry, dict):
            violations.append(v("EMPTY_FIELD", where, "修订条目不是映射"))
            continue
        for key in ("date", "change", "reason"):
            if not nonempty(entry.get(key)):
                violations.append(v("EMPTY_FIELD", where + "." + key,
                                    "修订条目 %s 为空（{date, change, reason}）" % key))
        date = entry.get("date")
        if nonempty(date) and not DATE_RE.fullmatch(str(date)):
            violations.append(v("ENUM_INVALID", where + ".date",
                                "date 须为 YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS，实为 %s" % date))

def as_stage(raw):
    """stage 取值 → 1-5 的整数；缺失/布尔/非整数/越界 → None。"""
    if not nonempty(raw) or isinstance(raw, bool):
        return None
    try:
        value = int(str(raw))
    except ValueError:
        return None
    return value if value in STAGES else None

def check_stage(doc, where, violations):
    raw = doc.get("stage")
    if not nonempty(raw):
        violations.append(v("EMPTY_FIELD", where + ".stage",
                            "stage 缺失（续跑锚点，1-5）"))
        return None
    stage = as_stage(raw)
    if stage is None:
        violations.append(v("ENUM_INVALID", where + ".stage",
                            "stage 须为 1-5 的整数，实为 %s" % raw))
    return stage

def check_notes(notes, show, violations):
    """notes 段（coaching notes 承载，2026-09-14 主 agent 改判）：出现时校验——
    列表 + 条目 {stage: 1-5, content 非空}；缺席合法（起草期可先不加）。"""
    if notes is None:
        return
    if not isinstance(notes, list):
        violations.append(v("EMPTY_FIELD", show + " notes",
                            "notes 不是列表（[{stage, content}]；无过程留痕写空列表）"))
        return
    for i, entry in enumerate(notes):
        where = "%s notes[%d]" % (show, i)
        if not isinstance(entry, dict):
            violations.append(v("EMPTY_FIELD", where, "条目不是映射（{stage, content}）"))
            continue
        if as_stage(entry.get("stage")) is None:
            violations.append(v("ENUM_INVALID", where + ".stage",
                                "stage 须为 1-5 的整数，实为 %s" % entry.get("stage")))
        if not nonempty(entry.get("content")):
            violations.append(v("EMPTY_FIELD", where + ".content",
                                "content 为空（每条 coaching notes 须自足）"))

def check_verdict(verdict, where, violations, final):
    """verdict.strength 枚举 + narrative 非空；--final 要求两者俱在。"""
    if verdict is None:
        if final:
            violations.append(v("EMPTY_FIELD", where + ".verdict",
                                "--final 要求 verdict 非空（strength + narrative）"))
        return
    if not isinstance(verdict, dict):
        violations.append(v("EMPTY_FIELD", where + ".verdict", "verdict 不是映射"))
        return
    strength = verdict.get("strength")
    if not nonempty(strength):
        if final:
            violations.append(v("EMPTY_FIELD", where + ".verdict.strength",
                                "--final 要求 verdict.strength 已定"))
    elif str(strength) not in STRENGTHS:
        violations.append(v("ENUM_INVALID", where + ".verdict.strength",
                            "strength 越界：%s（合法集 %s）"
                            % (strength, "|".join(STRENGTHS))))
    if "narrative" in verdict and not nonempty(verdict.get("narrative")):
        violations.append(v("EMPTY_FIELD", where + ".verdict.narrative",
                            "narrative 出现时不得为空"))
    elif final and nonempty(strength) and not nonempty(verdict.get("narrative")):
        violations.append(v("EMPTY_FIELD", where + ".verdict.narrative",
                            "--final 要求 verdict.narrative 非空"))

def check_faq_list(items, where, seen_ids, violations):
    """FAQ 列表：id 格式 PQ-### + 文档级唯一；q 与 a 非空（无条目写空列表）。"""
    if items is None:
        violations.append(v("EMPTY_FIELD", where, "缺失（无条目写空列表）"))
        return 0
    if not isinstance(items, list):
        violations.append(v("EMPTY_FIELD", where, "不是列表"))
        return 0
    for i, item in enumerate(items):
        iw = "%s[%d]" % (where, i)
        if not isinstance(item, dict):
            violations.append(v("EMPTY_FIELD", iw, "条目不是映射（{id, q, a}）"))
            continue
        rid = item.get("id")
        if not nonempty(rid):
            violations.append(v("EMPTY_FIELD", iw + ".id", "id 缺失"))
        else:
            rid = str(rid)
            if not PQ_RE.fullmatch(rid):
                violations.append(v("ENUM_INVALID", iw + ".id",
                                    "id 须为 PQ-###（三位零填充），实为 %s" % rid))
            if rid in seen_ids:
                violations.append(v("DUPLICATE_ID", iw + ".id",
                                    "ID %s 重复（客户与内部 FAQ 共用一条文档级序列）" % rid))
            seen_ids.add(rid)
        for key in ("q", "a"):
            if not nonempty(item.get(key)):
                violations.append(v("EMPTY_FIELD", iw + "." + key, "%s 为空" % key))
    return len(items)

def check_press_release(pr, where, violations):
    """press_release：形状 + 出现键非空（缺席键由 --final 九键义务兜底）。"""
    if pr is None:
        return
    if not isinstance(pr, dict):
        violations.append(v("EMPTY_FIELD", where + ".press_release",
                            "press_release 不是映射（九键结构）"))
        return
    for key, value in pr.items():
        if not nonempty(value):
            violations.append(v("EMPTY_FIELD", "%s.press_release.%s" % (where, key),
                                "%s 出现时不得为空" % key))

def check_distillate(distillate, show, violations):
    """distillate：形状；--final 义务见 check_final_duties。"""
    if distillate is not None and not isinstance(distillate, dict):
        violations.append(v("EMPTY_FIELD", show + " distillate", "distillate 不是映射"))

def check_final_duties(data, doc, project, stage, show, violations):
    """--final 附加义务（任务书 §5）：stage=5 / status: 已定稿 / 九键 / verdict /
    distillate 非空 / 零 [假设]。"""
    if stage != 5:
        violations.append(v("STATUS_MISMATCH", "%s.prfaq.stage" % show,
                            "--final 要求 stage=5（终局）；当前 stage=%s" % stage))
    status = project.get("status") if isinstance(project, dict) else None
    if not nonempty(status) or str(status) != "已定稿":
        violations.append(v("STATUS_MISMATCH", "%s.project.status" % show,
                            "--final 要求 project.status: 已定稿"))
    pr = doc.get("press_release")
    if not isinstance(pr, dict):
        violations.append(v("EMPTY_FIELD", "%s.prfaq.press_release" % show,
                            "--final 要求 press_release 九键非空"))
    else:
        for key in PRESS_KEYS:
            if not nonempty(pr.get(key)):
                violations.append(v("EMPTY_FIELD", "%s.prfaq.press_release.%s" % (show, key),
                                    "--final 要求 %s 非空" % key))
    distillate = data.get("distillate")
    if not isinstance(distillate, dict):
        violations.append(v("EMPTY_FIELD", "%s distillate" % show,
                            "--final 要求 distillate 非空（下游 PRD 输入）"))
    else:
        for key in DISTILLATE_SCALARS:
            if not nonempty(distillate.get(key)):
                violations.append(v("EMPTY_FIELD", "%s distillate.%s" % (show, key),
                                    "--final 要求 distillate.%s 非空" % key))
        for key in DISTILLATE_LISTS:
            if not isinstance(distillate.get(key), list):
                violations.append(v("EMPTY_FIELD", "%s distillate.%s" % (show, key),
                                    "--final 要求 distillate.%s 为列表" % key))
        if isinstance(distillate.get("value_props"), list) \
                and not distillate.get("value_props"):
            violations.append(v("EMPTY_FIELD", "%s distillate.value_props" % show,
                                "--final 要求至少 1 条 value_props"))
    if any("[假设]" in s for _p, s in walk_strings(data, "")):
        violations.append(v("ASSUMPTION_PRESENT", show,
                            "--final 要求零 [假设]；未决推断须清空或落为 "
                            "distillate.open_questions"))

def list_len(distillate, key):
    """distillate 列表键长度（非列表计 0）——counts 用。"""
    items = distillate.get(key) if isinstance(distillate, dict) else None
    return len(items) if isinstance(items, list) else 0

def check_previous(doc_ids, previous, show, root, violations):
    """--previous：比对旧稿 PQ ID 集合，旧有新无 → ID_UNSTABLE（对齐 diyc 口径）。"""
    prev_path = previous if os.path.isabs(previous) else os.path.join(root, previous)
    prev_rel = display_path(prev_path, root)
    prev_data, err = load_yaml_safe(prev_path)
    if prev_data is None and err is None:
        violations.append(v("MISSING_FILE", prev_rel, "旧稿不存在（--previous 路径无效）"))
        return
    if err is not None:
        violations.append(v("UNPARSABLE_YAML", prev_rel, "旧稿 YAML 解析失败：%s" % err))
        return
    for oid in pq_sort(faq_ids(prev_data)):
        if oid not in doc_ids:
            violations.append(v("ID_UNSTABLE", show,
                                "稳定 ID %s 在旧稿存在、新稿中缺失（ID 一旦分配永不重编号；"
                                "对照 --previous %s）" % (oid, prev_rel)))
