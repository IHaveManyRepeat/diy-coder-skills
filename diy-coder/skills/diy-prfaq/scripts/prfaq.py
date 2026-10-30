# -*- coding: utf-8 -*-
"""diy-prfaq 确定性引擎：headless 输入门禁 + prfaq.yaml 校验。

子命令：
  headless  校验 headless 模式的输入 schema：customer / problem / stakes / solution
            四项在场且非空（"含糊"属 LLM
            语义判断，不在引擎内）。缺项 → exit 1 + 具名缺口（gaps）+ 指引，零产出
            （只读门禁，绝不写文件）。
  check     校验 {output_dir}/prfaq.yaml（单文档形态，顶层 project + prfaq + distillate
            + notes + revisions）：形状 / stage 1-5 / concept_type 枚举 / essentials
            四键非空 / FAQ 条目 id 须 PQ-### 且文档级唯一（客户与内部共用一条序列）、
            q 与 a 非空 / verdict.strength 枚举 / notes 条目 {stage: 1-5, content 非空}。
            --previous PATH：比对旧稿 PQ ID 集合，旧有新无 → ID_UNSTABLE。
            --final：附加定稿义务——stage=5、project.status: 已定稿、press_release
            九键非空、verdict 非空且 strength 在枚举内、distillate 存在且五字段非空、
            零 [假设]。exit 0 唯一放行。

分工裁定：prfaq 属新产物类型，不进 diyc.py check 的硬编码类型集；
本引擎沿用领域引擎形态，契约同构：exit 0 唯一放行 / --json 单行回执 / violations[{code, where, msg}]
+ counts。违规码全部复用套件冻结集——本引擎无新增码。
禁手写实例解析：引擎不做 --instance / 白名单 / 目录推导；--output-dir 必填，由调用方传入
（SKILL.md 从 diyc.py resolve 取）。产物文档与 PQ ID 由 diy-prfaq 会话（LLM）创作，
本引擎只校验格式与唯一性，不铸造 ID、不写回。
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import display_path, load_yaml_safe, nonempty, v  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prfaq_checks import CONCEPT_TYPES, ESSENTIAL_KEYS, PRFAQ_FILE, check_distillate, check_faq_list, check_final_duties, check_notes, check_press_release, check_previous, check_project, check_revisions, check_stage, check_verdict, faq_ids, list_len  # noqa: E402

# ---- headless 输入门禁 ----

def cmd_headless(args):
    """只校验输入 schema 的在场/非空；缺项零产出 + 具名缺口。"""
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

def cmd_check(args):
    root = os.path.abspath(args.project_root)
    out = args.output_dir if os.path.isabs(args.output_dir) else os.path.join(root, args.output_dir)
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
                                   violations, warnings)

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
                   help="定稿校验：stage=5 + status: 已定稿 + 九键 + distillate 五字段非空"
                        " + 零假设")
    c.add_argument("--previous", default=None,
                   help="旧稿路径（Update 改写前留档；比对 PQ ID 集合）")
    c.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    c.set_defaults(func=cmd_check)

    args = ap.parse_args()
    sys.exit(args.func(args))

if __name__ == "__main__":
    main()
