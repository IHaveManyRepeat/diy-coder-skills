# -*- coding: utf-8 -*-
"""diy-retrospective 确定性引擎：epic 收尾回顾的门禁 + 指标机械采集 + retrospective.yaml 校验。

子命令：
  collect  --epic <E-x|N>  epic 收尾回顾的确定性部分（只读，绝不写文件）：
             1 门禁（源技能 step-1「Epic Discovery」的门禁化）：stories.yaml / epics.yaml
               在场且 project.status 为 已定稿；目标 epic 在 epics.yaml 中可解析；该 epic
               至少 1 个 已完成 story。不满足 → 零产出 exit 1 + 结构化拒绝回执
               （violations 带码 + gate.route 给路由）。epic 未收尾（有 story 非 已完成）
               不是拒绝：出 PENDING_DECISION 警告，partial 分流交会话（源 step-1 三分支：
               完成后再来 / partial 回顾 / 刷新 sprint）。
             2 指标机械采集（替换源技能 step-2「人工通读 story md 数数」的确定性下沉）：
               stories 完成度、sprint loop.rounds 合计、已阻塞 / augment: 失败 明细、
               bug-log 按 story→epic 归属的三分类计数、test-plan 对该 epic AC 的覆盖统计。
             3 前一份 retro 的 action_items 回带（源 step-3 的承诺跟踪输入，供 prev_followup）；
               下一 epic 存在性与共享 FR（源 step-4 预览的机械钩子）。
  check    [--final] [--id RT-xxx]  校验 {output_dir}/retrospective.yaml（RT-### 集合，形状对齐
           bug-log.yaml）：schema / 枚举 / epic 与 patterns evidence 的引用解析（S-x / BUG-0xx）/
           action item 完整性（action+owner+done_when）/ prev_followup 指向同文件既往记录 /
           next_epic.exists=true 时 id 解析 / ID 唯一；--final 附加：status 已落 已定稿、
           零 [假设]、metrics 与集合真值一致（SET_MISMATCH，与 collect 同一函数互证）、
           readiness 五键非空、action_items 非空。exit 0 唯一放行。

分工裁定（任务书 §2.2/§2.3/§4）：retrospective 属新产物类型，不进 diyc.py check 的硬编码类型集；
本引擎契约同构（exit 0 唯一放行 / --json 单行回执 / violations[{code, where, msg}] + counts；
where 正斜杠、相对 project-root；--output-dir 必填，实例解析由 SKILL.md 委托 diyc.py resolve）；
--previous 不实现——记录按 epic 追加、同 epic 重跑原位更新，无 ID 集合收缩风险（报告记账）。
违规码复用 batch3-contract §3 冻结集，不新增。diy 改造要点：输入面是结构化产物
（sprint.yaml 的 note/evidence/loop/review.findings + bug-log.yaml + test-plan.yaml + stories.yaml），
不是源技能的 story md 人工通读；指标由本引擎机械采集，会话不人工数数。
"""

# trace: B2 diy-retrospective 验收 #3（前置门禁零产出）/#4（ID 链接入）/#7（冒烟门禁路径）/#12（语言绑定与写权边界）
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import count_by, count_items, display_path, emit_via, load_yaml_safe, nonempty, v  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from retrospective_checks import Refs, check_record  # noqa: E402
from retrospective_collect import cmd_collect  # noqa: E402
from retrospective_lib import RETRO_FILE, load_docs  # noqa: E402


def cmd_check(args):
    root = os.path.abspath(args.project_root)
    out = os.path.abspath(args.output_dir)
    path = os.path.join(out, RETRO_FILE)
    show = display_path(path, root)
    docs = load_docs(out)
    refs = Refs(docs, out, root)
    violations = []
    warnings = []
    records = []

    data, err = load_yaml_safe(path)
    if data is None and err is None:
        violations.append(v("MISSING_FILE", show,
                            "%s 不存在（先完成一次 retrospective 起草）" % RETRO_FILE))
    elif err is not None:
        violations.append(v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err))
    elif not isinstance(data, dict):
        violations.append(v("EMPTY_FIELD", show, "顶层不是映射（须为 project + retros）"))
    else:
        project = data.get("project")
        if project is not None and not isinstance(project, dict):
            violations.append(v("EMPTY_FIELD", show + " project", "project 不是映射"))
        revisions = data.get("revisions")
        if revisions is not None and not isinstance(revisions, list):
            violations.append(v("EMPTY_FIELD", show + " revisions", "revisions 不是列表"))
        raw = data.get("retros")
        if raw is None:
            violations.append(v("EMPTY_FIELD", show + " retros",
                                "retros 缺失（集合形态；无记录写空列表）"))
        elif not isinstance(raw, list):
            violations.append(v("EMPTY_FIELD", show + " retros", "retros 不是列表"))
        else:
            records = raw
            ids = [str(r.get("id")) for r in records
                   if isinstance(r, dict) and nonempty(r.get("id"))]
            seen = set()
            for i, record in enumerate(records):
                if isinstance(record, dict) and nonempty(record.get("id")):
                    rid = str(record["id"])
                    if rid in seen:
                        violations.append(v("DUPLICATE_ID", "%s.retros[%d].id" % (show, i),
                                            "记录 ID %s 重复（RT ID 稳定不重用）" % rid))
                    seen.add(rid)
            if args.id:
                selected = [i for i, r in enumerate(records)
                            if isinstance(r, dict) and str(r.get("id")) == args.id]
                if not selected:
                    violations.append(v("UNKNOWN_ID", "%s.retros" % show,
                                        "记录 %s 不存在" % args.id))
                records = [records[i] for i in selected]
            for i, record in enumerate(records):
                other_ids = set(ids)
                if isinstance(record, dict) and nonempty(record.get("id")):
                    other_ids.discard(str(record["id"]))
                record_violations, _ = check_record(i, record, args.final, docs, show,
                                                    other_ids, refs)
                violations += record_violations
            if args.final and not records and not args.id:
                violations.append(v("EMPTY_FIELD", show + " retros",
                                    "--final 要求至少 1 条记录"))

    # 来源文件缺席：final 升为违规（引用面无法验证），起草期降为警告
    if refs.missing:
        if args.final:
            violations += refs.missing
        else:
            warnings += [{**item, "msg": item["msg"] + "（起草期降级警告）"}
                         for item in refs.missing]

    counts = {
        "retros": len(records),
        "by_status": count_by(records, "status"),
        "action_items": count_items(records, "action_items"),
        "prep_items": count_items(records, "prep_items"),
        "critical_path": count_items(records, "critical_path"),
        "patterns": count_items(records, "patterns"),
        "by_category": count_nested(records, "action_items", "category"),
    }
    ok = not violations
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

def count_nested(records, list_key, field):
    counts = {}
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get(list_key), list):
            continue
        for item in record[list_key]:
            if isinstance(item, dict) and nonempty(item.get(field)):
                name = str(item[field])
                counts[name] = counts.get(name, 0) + 1
    return counts

def human_check(payload):
    if payload["ok"]:
        print("PASS：%s 校验通过（retros=%d，行动项 %d）"
              % (payload["output_dir"] + "/" + RETRO_FILE, payload["counts"]["retros"],
                 payload["counts"]["action_items"]))
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
        description="diy-retrospective 确定性引擎：epic 收尾回顾的门禁 + 指标机械采集 + "
                    "retrospective.yaml 校验")
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("collect", help="门禁 + 指标机械采集 + 接续面回带（只读）")
    c.add_argument("--epic", required=True, help="目标 epic：E-<n> 或 <n>")
    c.add_argument("--project-root", default=".", help="项目根（默认 .）")
    c.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    c.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    c.set_defaults(func=cmd_collect)

    k = sub.add_parser("check", help="校验 retrospective.yaml（schema/枚举/引用；--final 附加定稿义务）")
    k.add_argument("--project-root", default=".", help="项目根（默认 .）")
    k.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    k.add_argument("--id", help="只校验指定记录 RT-xxx")
    k.add_argument("--final", action="store_true",
                   help="定稿校验：status 已落 final + 零假设 + metrics 互证 + readiness/行动项义务")
    k.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    k.set_defaults(func=cmd_check)
    return ap

def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = build_parser().parse_args()
    sys.exit(args.func(args))

if __name__ == "__main__":
    main()
