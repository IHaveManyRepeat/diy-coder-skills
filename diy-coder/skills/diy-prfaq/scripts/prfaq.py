# -*- coding: utf-8 -*-
"""diy-prfaq 确定性引擎：headless 输入门禁 + prfaq.yaml 校验。

子命令：
  headless  校验 headless 模式的输入 schema：customer / problem / stakes / solution
            四项在场且非空（源 SKILL.md "Mode detection" 的确定性部分；"含糊"属 LLM
            语义判断，不在引擎内）。缺项 → exit 1 + 具名缺口（gaps）+ 指引，零产出
            （只读门禁，绝不写文件）。
  check     校验 {output_dir}/prfaq.yaml（单文档形态，顶层 project + prfaq + distillate
            + notes + revisions）：形状 / stage 1-5 / concept_type 枚举 / essentials
            四键非空 / FAQ 条目 id 须 PQ-### 且文档级唯一（客户与内部共用一条序列）、
            q 与 a 非空 / verdict.strength 枚举 / notes 条目 {stage: 1-5, content 非空}。
            --previous PATH：比对旧稿 PQ ID 集合，旧有新无 → ID_UNSTABLE。
            --final：附加定稿义务——stage=5、project.status: final、press_release
            九键非空、verdict 非空且 strength 在枚举内、distillate 非空、零 [ASSUMPTION]。
            exit 0 唯一放行。

分工裁定（任务书 §2.2 / P1 先例）：prfaq 属新产物类型，不进 diyc.py check 的硬编码类型集；
本引擎沿用领域引擎形态，契约同构：exit 0 唯一放行 / --json 单行回执 / violations[{code, where, msg}]
+ counts。违规码全部复用 batch3-contract §3 冻结集——本引擎无新增码。
禁手写实例解析：引擎不做 --instance / 白名单 / 目录推导；--output-dir 必填，由调用方传入
（SKILL.md 从 diyc.py resolve 取）。产物文档与 PQ ID 由 diy-prfaq 会话（LLM）创作，
本引擎只校验格式与唯一性，不铸造 ID、不写回。
"""
# trace: 迁移计划 §二 验收 #2（产物 schema）/#3（门禁零产出）/#4（稳定 ID 比对）/#12（领域引擎接线）
import argparse
import io
import json
import os
import re
import sys

import yaml

PRFAQ_FILE = "prfaq.yaml"

CONCEPT_TYPES = ("commercial", "internal", "open-source", "community")
STAGES = (1, 2, 3, 4, 5)
STRENGTHS = ("forged", "needs-heat", "foundation-cracks")
PROJECT_STATUSES = ("draft", "final")
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
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


def v(code, where, msg):
    return {"code": code, "where": where, "msg": msg}


def nonempty(value):
    return value is not None and str(value).strip() != ""


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


# ---- headless 输入门禁 ----

def cmd_headless(args):
    """源 SKILL.md Mode detection：只校验输入 schema 的在场/非空；缺项零产出 + 具名缺口。"""
    gaps = [key for key in ESSENTIAL_KEYS
            if not nonempty(getattr(args, key.replace("-", "_")))]
    violations = [
        v("EMPTY_FIELD", "headless.%s" % key,
          "%s 缺失或为空：headless 模式要求 customer/problem/stakes/solution 四项在场且非空"
          % key)
        for key in gaps
    ]
    ok = not gaps
    reason = None
    if not ok:
        reason = ("headless 输入不足：缺 %d 项（%s）。补齐后重试——四项输入（customer / "
                  "problem / stakes / solution）是无人值守起草的最低要求。"
                  % (len(gaps), "、".join(gaps)))
    payload = {
        "ok": ok,
        "command": "headless",
        "project_root": args.project_root,
        "output_dir": os.path.normpath(args.output_dir).replace("\\", "/"),
        "gaps": gaps,
        "reason": reason,
        "violations": violations,
        "warnings": [],
        "counts": {"essential_fields": len(ESSENTIAL_KEYS) - len(gaps),
                   "essential_required": len(ESSENTIAL_KEYS)},
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False))
    elif ok:
        print("PASS：headless 输入 schema 完整（customer/problem/stakes/solution 四项在场且非空）")
    else:
        for item in violations:
            print("- %s %s: %s" % (item["code"], item["where"], item["msg"]))
        print("拒绝：%s" % reason)
    return 0 if ok else 1


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
                                "date 须为 YYYY-MM-DD，实为 %s" % date))


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
    """--final 附加义务（任务书 §5）：stage=5 / status: final / 九键 / verdict /
    distillate 非空 / 零 [ASSUMPTION]。"""
    if stage != 5:
        violations.append(v("STATUS_MISMATCH", "%s.prfaq.stage" % show,
                            "--final 要求 stage=5（终局）；当前 stage=%s" % stage))
    status = project.get("status") if isinstance(project, dict) else None
    if not nonempty(status) or str(status) != "final":
        violations.append(v("STATUS_MISMATCH", "%s.project.status" % show,
                            "--final 要求 project.status: final"))
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
    if any("[ASSUMPTION]" in s for s in collect_strings(data)):
        violations.append(v("ASSUMPTION_PRESENT", show,
                            "--final 要求零 [ASSUMPTION]；未决推断须清空或落为 "
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


def cmd_check(args):
    root = os.path.abspath(args.project_root)
    out = args.output_dir
    path = os.path.join(out, PRFAQ_FILE)
    show = display_path(path, root)
    violations = []
    warnings = []
    stage = None
    customer_faq = 0
    internal_faq = 0
    distillate = None
    notes = None

    data, err = load_yaml_safe(path)
    if data is None and err is None:
        violations.append(v("MISSING_FILE", show,
                            "%s 不存在（先完成一次 PRFAQ 起草）" % PRFAQ_FILE))
    elif err is not None:
        violations.append(v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err))
    elif not isinstance(data, dict):
        violations.append(v("EMPTY_FIELD", show,
                            "顶层不是映射（须为 project + prfaq + distillate）"))
    else:
        check_project(data.get("project"), show, violations)
        check_revisions(data.get("revisions"), show, violations)
        check_distillate(data.get("distillate"), show, violations)
        notes = data.get("notes")
        check_notes(notes, show, violations)
        distillate = data.get("distillate")
        doc = data.get("prfaq")
        if not isinstance(doc, dict):
            violations.append(v("EMPTY_FIELD", show + " prfaq",
                                "prfaq 缺失或不是映射（单文档形态）"))
        else:
            doc_where = show + ".prfaq"
            stage = check_stage(doc, doc_where, violations)
            concept_type = doc.get("concept_type")
            if not nonempty(concept_type):
                violations.append(v("EMPTY_FIELD", doc_where + ".concept_type",
                                    "concept_type 缺失（校准 Stage 3-4 提问框架）"))
            elif str(concept_type) not in CONCEPT_TYPES:
                violations.append(v("ENUM_INVALID", doc_where + ".concept_type",
                                    "concept_type 越界：%s（合法集 %s）"
                                    % (concept_type, "|".join(CONCEPT_TYPES))))
            essentials = doc.get("essentials")
            if not isinstance(essentials, dict):
                violations.append(v("EMPTY_FIELD", doc_where + ".essentials",
                                    "essentials 缺失或不是映射（四要素 customer / "
                                    "problem / stakes / solution）"))
            else:
                for key in ESSENTIAL_KEYS:
                    if not nonempty(essentials.get(key)):
                        violations.append(v("EMPTY_FIELD",
                                            "%s.essentials.%s" % (doc_where, key),
                                            "%s 为空（四要素是 Stage 1 的出口条件）" % key))
            check_press_release(doc.get("press_release"), doc_where, violations)
            seen_ids = set()
            customer_items = doc.get("customer_faq")
            internal_items = doc.get("internal_faq")
            customer_faq = check_faq_list(customer_items, doc_where + ".customer_faq",
                                          seen_ids, violations)
            internal_faq = check_faq_list(internal_items, doc_where + ".internal_faq",
                                          seen_ids, violations)
            check_verdict(doc.get("verdict"), doc_where, violations, args.final)
            if args.previous:
                check_previous(faq_ids(data), args.previous, show, root, violations)
            if args.final:
                check_final_duties(data, doc, data.get("project"), stage, show,
                                   violations)

    counts = {
        "stage": stage,
        "customer_faq": customer_faq,
        "internal_faq": internal_faq,
        "faqs": customer_faq + internal_faq,
        "value_props": list_len(distillate, "value_props"),
        "constraints": list_len(distillate, "constraints"),
        "open_questions": list_len(distillate, "open_questions"),
        "notes": len(notes) if isinstance(notes, list) else 0,
    }
    ok = not violations
    payload = {
        "ok": ok,
        "command": "check",
        "project_root": args.project_root,
        "output_dir": os.path.normpath(out).replace("\\", "/"),
        "final": args.final,
        "violations": violations,
        "warnings": warnings,
        "counts": counts,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False))
    elif ok:
        print("PASS：%s 校验通过（stage=%s，FAQ %d 条）" % (show, stage, counts["faqs"]))
    else:
        print("FAIL：")
        for item in violations:
            print("- %s %s: %s" % (item["code"], item["where"], item["msg"]))
    return 0 if ok else 1


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(
        description="diy-prfaq 确定性引擎：headless 输入门禁 + prfaq.yaml 校验")
    sub = ap.add_subparsers(dest="cmd", required=True)

    h = sub.add_parser("headless", help="headless 输入 schema 门禁（四项在场且非空）")
    h.add_argument("--project-root", default=".", help="项目根（默认 .）")
    h.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    h.add_argument("--customer", default=None, help="输入：客户/用户（具体人群）")
    h.add_argument("--problem", default=None, help="输入：问题（具体可感）")
    h.add_argument("--stakes", default=None, help="输入：为何重要（代价与后果）")
    h.add_argument("--solution", default=None, help="输入：解法概念（可以粗糙）")
    h.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    h.set_defaults(func=cmd_headless)

    c = sub.add_parser("check", help="校验 prfaq.yaml（schema/枚举/ID；--final 附加定稿义务）")
    c.add_argument("--project-root", default=".", help="项目根（默认 .）")
    c.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    c.add_argument("--final", action="store_true",
                   help="定稿校验：stage=5 + status: final + 九键 + distillate + 零假设")
    c.add_argument("--previous", default=None,
                   help="旧稿路径（Update 改写前留档；比对 PQ ID 集合）")
    c.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    c.set_defaults(func=cmd_check)

    args = ap.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
