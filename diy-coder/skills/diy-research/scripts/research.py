# -*- coding: utf-8 -*-
"""diy-research 确定性引擎：research.yaml 结构校验 + 旧稿 ID 稳定性比对。

子命令：
  check   校验 {output_dir}/research.yaml（顶层 project + researches 集合，形状对齐
          bug-log.yaml）：schema / 枚举（dimension|status|confidence）/ RS-### ID 格式与
          唯一性 / 条目级锚 RF/RK/RO 全局唯一与顺序递增 / 每条 finding 的 sources 非空
          且 url 为 http(s)、accessed 为 YYYY-MM-DD。
          --id RS-xxx 只校验指定记录（未命中 → UNKNOWN_ID）；--previous PATH 比对旧稿
          RS-### 集合，旧有新无 → ID_UNSTABLE（Update 防丢记录）。
          --final 附加定稿义务：零 [假设]、synthesis 三键非空、findings 非空、
          status 已落「已定稿」（定稿门须咬住记录状态）、
          顶层 distillate 交出面存在且五字段非空（四列表条目恰为 {text, src}——
          形态例外，--final 硬校验；文档级，下游 PRD 输入）。exit 0 唯一放行。

分工裁定：research 属新产物类型，不进 diyc.py check 的硬编码类型集；
本引擎沿用领域引擎形态（同 diy-checkpoint-preview/scripts/checkpoint.py 分工），契约同构：
exit 0 唯一放行 / 1 = 违规或被拒 / 2 = 用法错误（argparse）/ --json 单行回执（ensure_ascii=False）
/ violations[{code, where, msg}] + counts。违规码全部复用套件冻结集
（MISSING_FILE UNPARSABLE_YAML DUPLICATE_ID UNKNOWN_ID ENUM_INVALID EMPTY_FIELD
ASSUMPTION_PRESENT ID_UNSTABLE STATUS_MISMATCH），无新增码。

引用纪律的机制位置（每条断言带来源）：findings[].sources 为空、url 非
http(s)、accessed 非日期一律违规——来源缺失不得以「训练数据已知」补位。

禁手写实例解析：引擎不做 --instance / 白名单 / 目录推导；--output-dir 必填，由调用方传入
（SKILL.md 从 diyc.py resolve 取）。产物与产物 ID 由 diy-research 会话（LLM）创作——
RS-0nn 由 LLM 铸造、本引擎只校验格式与唯一性。本引擎只读，不写任何文件。
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from research_checks import (  # noqa: E402
    check_anchor_ids, check_distillate_final, check_record, collect_anchor_ids,
    local_anchor_set, record_ids)

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import count_by, count_items, display_path, load_yaml_safe, nonempty, v  # noqa: E402

RESEARCH_FILE = "research.yaml"


def count_sources(records):
    total = 0
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("findings"), list):
            continue
        for finding in record["findings"]:
            if isinstance(finding, dict) and isinstance(finding.get("sources"), list):
                total += len(finding["sources"])
    return total


def check_previous(path, current_ids, project_root):
    """旧稿 RS-### 集合比对：旧有新无 → ID_UNSTABLE（记录稳定不重用、不消失）。"""
    show = display_path(path, project_root)
    data, err = load_yaml_safe(path)
    if data is None and err is None:
        return [v("MISSING_FILE", show, "旧稿 %s 不存在" % show)]
    if err is not None:
        return [v("UNPARSABLE_YAML", show, "旧稿 YAML 解析失败：%s" % err)]
    if not isinstance(data, dict) or not isinstance(data.get("researches"), list):
        return []
    violations = []
    for rid in record_ids(data["researches"]):
        if rid not in current_ids:
            violations.append(v("ID_UNSTABLE", show,
                                "旧稿记录 %s 在新稿中消失（RS ID 稳定不重用；删除须落 revisions 说明）"
                                % rid))
    return violations


def cmd_check(args):
    root = os.path.abspath(args.project_root)
    out = args.output_dir
    path = os.path.join(out, RESEARCH_FILE)
    show = display_path(path, root)
    violations = []
    warnings = []
    records = []
    comparable = False

    data, err = load_yaml_safe(path)
    if data is None and err is None:
        violations.append(v("MISSING_FILE", show,
                            "%s 不存在（先完成一次研究起草）" % RESEARCH_FILE))
    elif err is not None:
        violations.append(v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err))
    elif not isinstance(data, dict):
        violations.append(v("EMPTY_FIELD", show, "顶层不是映射（须为 project + researches）"))
    else:
        comparable = True
        project = data.get("project")
        if project is not None and not isinstance(project, dict):
            violations.append(v("EMPTY_FIELD", show + " project", "project 不是映射"))
        revisions = data.get("revisions")
        if revisions is not None and not isinstance(revisions, list):
            violations.append(v("EMPTY_FIELD", show + " revisions", "revisions 不是列表"))
        raw_records = data.get("researches")
        if raw_records is None:
            violations.append(v("EMPTY_FIELD", show + " researches",
                                "researches 缺失（集合形态；无记录写空列表）"))
        elif not isinstance(raw_records, list):
            violations.append(v("EMPTY_FIELD", show + " researches", "researches 不是列表"))
        else:
            records = raw_records
            # ID 唯一性是文件级完整性：无论是否 --id 过滤都在全量上核
            seen = set()
            for i, record in enumerate(records):
                if not isinstance(record, dict) or not nonempty(record.get("id")):
                    continue
                rid = str(record["id"])
                if rid in seen:
                    violations.append(v("DUPLICATE_ID", "%s.researches[%d].id" % (show, i),
                                        "记录 ID %s 重复（RS ID 稳定不重用）" % rid))
                seen.add(rid)

    scope_indexed = [(i, r) for i, r in enumerate(records)
                     if isinstance(r, dict)
                     and (not nonempty(args.id) or str(r.get("id")) == str(args.id))]
    scope = [r for _i, r in scope_indexed]
    if nonempty(args.id) and not scope:
        violations.append(v("UNKNOWN_ID", "%s.researches" % show,
                            "记录 %s 不存在（--id 未命中）" % args.id))

    # 条目级锚（RF/RK/RO）唯一性与顺序：文件级完整性，无论 --id 过滤都在全量上核
    if comparable:
        violations += check_anchor_ids(collect_anchor_ids(data))

    for i, record in scope_indexed:
        violations += check_record(i, record, args.final, show, warnings)
    if args.final and not scope and not violations:
        violations.append(v("EMPTY_FIELD", show + " researches",
                            "--final 要求至少 1 条记录"))
    if args.final and comparable:
        violations += check_distillate_final(
            data.get("distillate"), show, local_anchor_set(data), warnings)

    if nonempty(args.previous) and comparable:
        # 当前稿缺失/损坏时不再叠加 ID 比对噪音（MISSING_FILE / UNPARSABLE_YAML 已定因）
        violations += check_previous(args.previous, record_ids(records), root)

    counts = {
        "researches": len(scope),
        "total_researches": len(records),
        "by_dimension": count_by(scope, "dimension"),
        "by_status": count_by(scope, "status"),
        "findings": count_items(scope, "findings"),
        "sources": count_sources(scope),
        "open_questions": sum(len(r.get("synthesis", {}).get("open_questions") or [])
                              for r in scope
                              if isinstance(r, dict)
                              and isinstance(r.get("synthesis"), dict)),
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
    if args.json:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        if ok:
            print("PASS：%s 校验通过（researches=%d）" % (show, counts["researches"]))
        else:
            print("FAIL：")
            for item in violations:
                print("- %s %s: %s" % (item["code"], item["where"], item["msg"]))
    return 0 if ok else 1


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(
        description="diy-research 确定性引擎：research.yaml 结构校验（含旧稿 ID 稳定性比对）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("check",
                       help="校验 research.yaml（schema/枚举/来源纪律；--final 附加定稿义务）")
    c.add_argument("--project-root", default=".", help="项目根（默认 .）")
    c.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    c.add_argument("--final", action="store_true",
                   help="定稿校验：status 已落「已定稿」+ findings/synthesis 非空 + 零假设"
                        " + distillate 交出面五字段非空")
    c.add_argument("--id", default=None, help="只校验指定记录（RS-0nn；未命中 → UNKNOWN_ID）")
    c.add_argument("--previous", default=None,
                   help="旧稿路径：比对 RS ID 集合，旧有新无 → ID_UNSTABLE（Update 防丢记录）")
    c.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    c.set_defaults(func=cmd_check)

    args = ap.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
