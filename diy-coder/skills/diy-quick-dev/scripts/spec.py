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
             审查中|已完成 → EMPTY_FIELD——轻量通道不做形式化红绿台账，但「进审查前
             每条 AC 有命令级实测证据」不可省（这是与 diy-dev 的明文差异）。
             status=已完成 另要求 `review_order` 非空（源 step-05 / step-oneshot 的
             Suggested Review Order 形态）。
             `--final` 附加：project.status=已定稿、记录 status=已完成、tasks 非空且全 done、
             acceptance 非空、verification.commands 非空且每条 result 非空、零 [假设]。
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
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import count_by, count_items, display_path, emit_via, items, load_yaml_safe, nonempty, v, walk_strings  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spec_checks import DATE_RE, ROUTES, SP_RE, STATUSES, TYPES, check_acceptance, check_boundaries, check_change_log, check_code_map, check_deferred, check_enum, check_intent, check_io_matrix, check_review, check_review_order, check_tasks, check_verification  # noqa: E402

SPEC_FILE = "spec.yaml"
PROJECT_STATUSES = ("草稿", "已定稿")

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
    if str(status) != "已完成":
        violations.append(v("STATUS_MISMATCH", where + ".status",
                            "--final 要求该记录 status 已完工（已完成），实为 %s"
                            % (status if nonempty(status) else "未声明")))
    if any("[假设]" in s for _p, s in walk_strings(record, "")):
        violations.append(v("ASSUMPTION_PRESENT", where,
                            "--final 要求零 [假设]；未决推断须先落定"))
    return violations

# ---------------------------------------------------------------- check

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
                                    "project.status 缺失（草稿|已定稿）"))
            elif str(status) not in PROJECT_STATUSES:
                violations.append(v("ENUM_INVALID", show + " project.status",
                                    "project.status 越界：%s（合法集 %s）"
                                    % (status, "|".join(PROJECT_STATUSES))))
            elif args.final and str(status) != "已定稿":
                violations.append(v("STATUS_MISMATCH", show + " project.status",
                                    "--final 要求 project.status 已落 已定稿（实为 %s）" % status))
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
    emit_via(payload, args.json, human_check)
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
                   help="定稿校验：project.status=已定稿 + 记录 已完成 + tasks 全 done + "
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
