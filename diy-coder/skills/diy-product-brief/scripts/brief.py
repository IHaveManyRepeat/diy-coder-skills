# -*- coding: utf-8 -*-
"""diy-product-brief 确定性引擎：intent 门禁（前置条件 + 路由）+ brief.yaml 校验。

子命令：
  intent  解析 intent（新建/更新/校验）的前置条件并给路由，确定性部分不留给 LLM：
            新建 → 不要求产物在场；产物已存在 → warning（resume/更新 语义，不得静默覆盖）
            更新 → {output_dir}/brief.yaml 必须存在
            校验 → 同上
          缺席且 intent ∈ {更新, 校验} → 零产出 exit 1 + 一行理由 + 路由（先新建）。
          只读检测，绝不写文件；回执给出 status 与 counts（读取成本纪律：模型读回执不读全文）。
  check   校验 {output_dir}/brief.yaml（单文档 + 附属集合，顶层 project 载文档级 status）：
            形状：project / brief 映射；decisions / addendum / revisions 列表
            枚举：project.status(草稿|已定稿)、stakes(个人兴趣|内部|投资人|公开)、
                  decisions[].status(生效|已反转)
            ID：BD-### 三位零填充、集合内唯一（稳定不重用不重编号，铸造权在会话）
            日期：YYYY-MM-DD
            内容：decision 文本、users[].who/need、value[].point、addendum 三键（section/
                  content/why_separate）恒非空；起草期容许叙事字段半写（实时持久化的前提）
          --previous PATH：读旧稿快照，比对 BD-### 集合，旧有新无 → ID_UNSTABLE（update 模式防丢决策）
          --final 附加定稿义务：project.status 已落「已定稿」、零 [假设]（含 assumptions 清空）、
                  title/problem/solution/users 非空、每条 decision 有 rationale、distillate
                  交出面在场且五字段非空（problem/target_users/value_props/constraints/
                  open_questions）。exit 0 唯一放行。
          --final 附加评审证据链（任务书 §12.1 ①ⓒ 六条）：顶层 review_refs 非空（缺失或空 →
                  EVIDENCE_MISSING）；{output_dir}/editorial-review.yaml 在场（缺席 →
                  MISSING_FILE）；每个 ID 在该台账 reviews[] 内（否则 UNKNOWN_ID）；该记录
                  status: 已定稿（否则 STATUS_MISMATCH）；其 target 归一化后指向本 brief.yaml
                  （否则 EVIDENCE_MISSING）；其 lenses 同时含 结构 与 文风（否则 EVIDENCE_MISSING）。
                  target 归一化四步顺序不可换：normpath → 统一正斜杠 → 相对 project-root →
                  比较（指向别处的记录不构成本文档的证据）。派发不可用（环境缺本技能的同套件
                  兄弟 diy-editorial-review 引擎）→ TOOL_MISSING warning 降级：六条一并转
                  warning、--final 放行（环境问题；技能在场而记录缺失或不合格仍硬拒）。

分工裁定（任务书 §2.2/§2.3）：brief 属新产物类型，不进 diyc.py check 的硬编码类型集；
本引擎沿用领域引擎形态（同 checkpoint.py / design.py），契约同构：exit 0 唯一放行 /
--json 单行回执 / violations[{code, where, msg}] + warnings + counts。违规码全部复用
batch3-contract §3 冻结集（MISSING_FILE UNPARSABLE_YAML EMPTY_FIELD ENUM_INVALID
DUPLICATE_ID ID_UNSTABLE ASSUMPTION_PRESENT STATUS_MISMATCH EVIDENCE_MISSING
UNKNOWN_ID），无新增码；降级 warning 码 TOOL_MISSING（兄弟引擎缺席专用，同 readiness 先例）。

禁手写实例解析：引擎不做 --instance / 白名单 / 目录推导；--output-dir 必填，由调用方传入
（SKILL.md 从 diyc.py resolve 取）。产物与产物 ID 由 diy-product-brief 会话（LLM）创作——
BD-0nn 由 LLM 铸造、本引擎只校验格式与唯一性；引擎全程只读，不写任何文件。
"""
# trace: B1 diy-product-brief 验收 #3（前置门禁零产出退出）/#4（ID 链接入）/#12（领域引擎接线）
import argparse
import json
import os
import sys


sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import count_by, display_path, load_yaml_safe, nonempty, v, walk_strings  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brief_checks import check_addendum, check_brief_section, check_decisions, check_distillate_final, check_project, check_review_evidence, check_revisions, list_len, previous_ids  # noqa: E402

BRIEF_FILE = "brief.yaml"
INTENTS = ("新建", "更新", "校验")
ROUTES = {
    "新建": "steps/01-discovery.md",
    "更新": "steps/04-update.md",
    "校验": "steps/05-validate.md",
}

def emit(payload, as_json, human_lines):
    """打印回执并返回 exit code（ok=true → 0，否则 1）。"""
    if as_json:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        for line in human_lines:
            print(line)
    return 0 if payload["ok"] else 1

# ---- intent（前置门禁 + 路由） ----

def cmd_intent(args):
    root = os.path.abspath(args.project_root)
    out = args.output_dir
    intent = args.intent
    path = os.path.join(out, BRIEF_FILE)
    show = display_path(path, root)
    exists = os.path.isfile(path)
    violations = []
    warnings = []
    counts = {}
    status = None

    if intent in ("更新", "校验") and not exists:
        violations.append(v("MISSING_FILE", show,
                            "%s 不存在：%s 需要既有产物；先跑「新建」（%s）"
                            % (BRIEF_FILE, intent, ROUTES["新建"])))
    if exists:
        data, err = load_yaml_safe(path)
        if err is not None:
            violations.append(v("UNPARSABLE_YAML", show,
                                "既有产物不可解析，无法确认可用：%s" % err))
        elif isinstance(data, dict):
            project = data.get("project")
            if isinstance(project, dict):
                status = project.get("status")
            brief = data.get("brief") if isinstance(data.get("brief"), dict) else {}
            decisions = data.get("decisions") if isinstance(data.get("decisions"), list) else []
            counts = {
                "decisions": sum(1 for d in decisions if isinstance(d, dict)),
                "decisions_by_status": count_by(decisions, "status"),
                "open_questions": list_len(brief.get("open_questions")),
                "addendum": list_len(data.get("addendum")),
                "revisions": list_len(data.get("revisions")),
            }
        if intent == "新建":
            warnings.append(v("STATUS_MISMATCH", show,
                              "已存在 brief.yaml（status=%s）：「新建」须先与用户确认 resume"
                              "或改走「更新」，禁止静默覆盖" % (status or "未知")))

    ok = not violations
    reason = None
    if not ok:
        reason = "；".join(x["msg"] for x in violations)
    payload = {
        "ok": ok,
        "command": "intent",
        "project_root": args.project_root,
        "output_dir": os.path.normpath(out).replace("\\", "/"),
        "intent": intent,
        "file": show,
        "exists": exists,
        "status": status,
        "route": ROUTES[intent],
        "violations": violations,
        "warnings": warnings,
        "reason": reason,
        "counts": counts,
    }
    if ok:
        human = ["intent=%s：%s（%s）→ 读 %s"
                 % (intent, show, status if exists else "不存在", ROUTES[intent])]
        human += ["WARNING %s" % w["msg"] for w in warnings]
    else:
        human = ["拒绝：%s" % reason]
    return emit(payload, args.json, human)

def cmd_check(args):
    root = os.path.abspath(args.project_root)
    out = args.output_dir
    path = os.path.join(out, BRIEF_FILE)
    show = display_path(path, root)
    violations = []
    warnings = []
    decisions = []
    brief = {}
    addendum = []
    revisions = []

    data, err = load_yaml_safe(path)
    if data is None and err is None:
        violations.append(v("MISSING_FILE", show,
                            "%s 不存在（先完成一次「新建」起草）" % BRIEF_FILE))
    elif err is not None:
        violations.append(v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err))
    elif not isinstance(data, dict):
        violations.append(v("EMPTY_FIELD", show, "顶层不是映射（须为 project + brief）"))
    else:
        check_project(data.get("project"), show + " project", violations, args.final)
        brief = check_brief_section(data.get("brief"), show + " brief", args.final, violations)
        decisions = check_decisions(data.get("decisions"), show + " decisions",
                                    args.final, violations)
        addendum = check_addendum(data.get("addendum"), show + " addendum", violations)
        revisions = check_revisions(data.get("revisions"), show + " revisions", violations)
        if args.final and any("[假设]" in s for _p, s in walk_strings(data, "")):
            violations.append(v("ASSUMPTION_PRESENT", show,
                                "--final 要求零 [假设]；未决假设须先落定"))
        if args.final:
            check_review_evidence(data, root, out, path, show, violations, warnings)
            check_distillate_final(data.get("distillate"), show, violations)

    if args.previous:
        old = previous_ids(args.previous, root, violations)
        if old is not None:
            current = {str(d["id"]) for d in decisions
                       if isinstance(d, dict) and nonempty(d.get("id"))}
            for rid in sorted(old - current):
                violations.append(v("ID_UNSTABLE", show + " decisions",
                                    "旧 ID %s 在新稿中消失（BD ID 稳定：不重编号、不重用）"
                                    % rid))

    counts = {
        "decisions": list_len(decisions),
        "decisions_by_status": count_by(decisions if isinstance(decisions, list) else [], "status"),
        "users": list_len(brief.get("users") if isinstance(brief, dict) else None),
        "value": list_len(brief.get("value") if isinstance(brief, dict) else None),
        "open_questions": list_len(brief.get("open_questions") if isinstance(brief, dict) else None),
        "assumptions": list_len(brief.get("assumptions") if isinstance(brief, dict) else None),
        "extra_sections": list_len(brief.get("extra_sections") if isinstance(brief, dict) else None),
        "addendum": list_len(addendum),
        "revisions": list_len(revisions),
    }
    ok = not violations
    payload = {
        "ok": ok,
        "command": "check",
        "project_root": args.project_root,
        "output_dir": os.path.normpath(out).replace("\\", "/"),
        "final": args.final,
        "previous": display_path(args.previous, root) if args.previous else None,
        "violations": violations,
        "warnings": warnings,
        "counts": counts,
    }
    if ok:
        human = ["PASS：%s 校验通过（decisions=%d%s）"
                 % (show, counts["decisions"], "，final" if args.final else "")]
        human += ["WARNING %s %s: %s" % (w["code"], w["where"], w["msg"])
                  for w in warnings]
    else:
        human = ["FAIL："] + ["- %s %s: %s" % (x["code"], x["where"], x["msg"])
                              for x in violations]
    return emit(payload, args.json, human)

def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(
        description="diy-product-brief 确定性引擎：intent 门禁（零产出拒绝 + 路由）+ brief.yaml 校验")
    sub = ap.add_subparsers(dest="cmd", required=True)

    i = sub.add_parser("intent", help="解析 intent 前置条件并给路由（更新/校验 无产物 → 零产出拒绝）")
    i.add_argument("--intent", required=True, choices=INTENTS,
                   help="会话判定的意图：新建 / 更新 / 校验")
    i.add_argument("--project-root", default=".", help="项目根（默认 .）")
    i.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    i.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    i.set_defaults(func=cmd_intent)

    c = sub.add_parser("check", help="校验 brief.yaml（schema/枚举/ID；--final 附加定稿义务）")
    c.add_argument("--project-root", default=".", help="项目根（默认 .）")
    c.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    c.add_argument("--final", action="store_true",
                   help="定稿校验：status 已落「已定稿」+ 零假设 + 主体非空 + 每条决策有 "
                        "rationale + distillate 交出面五字段非空 + review_refs 评审证据链"
                        "（六条）")
    c.add_argument("--previous", default=None,
                   help="旧稿快照路径：比对 BD-### 集合，旧有新无 → ID_UNSTABLE")
    c.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    c.set_defaults(func=cmd_check)

    args = ap.parse_args()
    sys.exit(args.func(args))

if __name__ == "__main__":
    main()
