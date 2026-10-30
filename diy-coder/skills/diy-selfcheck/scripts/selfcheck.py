# -*- coding: utf-8 -*-
"""diy-selfcheck 确定性引擎：selfcheck.yaml 校验（check）。

主产物 {output_dir}/selfcheck.yaml —— 集合形态（project / schema: 2 / checks[]），每条
check 记一次自检（SC-### 号段同文件内唯一）。引擎只做机械可判的校验，不写任何文件。

  check    校验 selfcheck.yaml（用法：check <selfcheck.yaml 路径> [--final] [--json]；
             路径缺席时走 --output-dir → <output-dir>/selfcheck.yaml，二者皆缺 exit 2——
             兼容 05-close 终门命令的 --output-dir 形态）。
             基础校验（每次跑）——
               顶层 project/schema/checks 在场（project 须为映射、checks 须为列表）；
               checks[].id 形态 SC-###（ID_FMT）且同文件内唯一（ID_DUP）；
               date/status 必填；status ∈ 草稿|已定稿（ENUM_INVALID）；
               anchor{md5,exec_form,shards} 必填——**commit 可缺**（01 单锚降级不红）；
               target{kind,path} 必填，kind ∈ 任务书|技能|规格|文档（ENUM_INVALID）；
               findings/disposals/rescans/b_review/revisions/summary 键在场；
               findings[] 元素：n 必填（disposals 对账键）、source 为非空数组且每元素
               ∈ 预演|引用核对|对抗（越界 ENUM_INVALID）、layer 在场时 ∈ 盲猎|边界猎手|
               验收审计（ENUM_INVALID）。
             --final 附加六义务（**status 门不加**——已定稿不是终门检查对象）——
               ① b_review 非空（B 部分必出）→ DUTY_B_REVIEW_MISSING
               ② summary.ref_checked 与 summary.ref_false 在场（在场即可，不核数值关系）
                  → DUTY_SUMMARY_REF_MISSING
               ③ disposals 以 finding n 对账 findings 全覆盖（缺/孤儿均算缺口）
                  → DUTY_DISPOSAL_GAP
               ④ rescans.round1 与 rescans.round2 在场且非空（两轮复扫凭证）
                  → DUTY_RESCAN_MISSING
               ⑤ 全文字符串零 [假设] 字面量——**quote 字段的值豁免**（照 spec_scan
                  check_final_duties 先例：引文是证据、不是未落定推断）→ HYPOTHESIS_FOUND
               ⑥ findings 在场的 ss_ref 逐条在**同目录 spec-scan.yaml** 可解析；spec-scan.yaml
                  不存在或 ss_ref 缺席＝对缺席项不红，带了 ss_ref 解析不到＝红
                  → SS_REF_UNRESOLVED
           exit 0 唯一放行。

违规码冻结集 VIOLATION_CODES（12 个，由 tests/test_selfcheck_engine.py 冻结）：
EMPTY_FIELD / ENUM_INVALID / ID_FMT / ID_DUP / MISSING_FILE / UNPARSABLE_YAML /
DUTY_B_REVIEW_MISSING / DUTY_SUMMARY_REF_MISSING / DUTY_DISPOSAL_GAP /
DUTY_RESCAN_MISSING / HYPOTHESIS_FOUND / SS_REF_UNRESOLVED。

回执契约照 spec_scan cmd_check：--json 单行 JSON（ensure_ascii=False）＋共同键
{ok, command, project_root, output_dir, final, violations[{code, where, msg}], warnings,
counts}；where 正斜杠、相对 project-root，check 级违规带检查 ID 定位；人读态每条违规
一行 `CODE where: msg` ＋末尾汇总行。YAGNI：只做 check，不做 init/list（不进 diyc
check --type 封闭集，同 analyze/teach/spec-scan 先例）。
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import display_path, emit_via, load_yaml_safe, v, violation_line  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from selfcheck_checks import ASSUMPTION, check_final_duties, check_one, check_top_level, doc_counts, load_spec_ids, walk_strings  # noqa: E402

# 违规码冻结集（自建 12 码；测试冻结，增删须同步改测试）
VIOLATION_CODES = ("EMPTY_FIELD", "ENUM_INVALID", "ID_FMT", "ID_DUP",
                   "MISSING_FILE", "UNPARSABLE_YAML",
                   "DUTY_B_REVIEW_MISSING", "DUTY_SUMMARY_REF_MISSING",
                   "DUTY_DISPOSAL_GAP", "DUTY_RESCAN_MISSING",
                   "HYPOTHESIS_FOUND", "SS_REF_UNRESOLVED")

# trace: diy-selfcheck check 子命令（selfcheck.yaml 校验；exit 0 唯一放行）
def cmd_check(args):
    root = os.path.abspath(args.project_root)
    if args.path:
        path = os.path.abspath(args.path)
    elif args.output_dir:
        path = os.path.abspath(os.path.join(args.output_dir, "selfcheck.yaml"))
    else:
        sys.stderr.write("用法错误：须给 selfcheck.yaml 路径或 --output-dir（二者皆缺）\n")
        return 2
    out = os.path.dirname(path)
    show = display_path(path, root)
    violations = []
    checks = []
    data, err = load_yaml_safe(path)
    if data is None and err is None:
        violations.append(v("MISSING_FILE", show,
                            "selfcheck.yaml 不存在（先跑自检产出主产物）"))
    elif err is not None:
        violations.append(v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err))
    elif not isinstance(data, dict):
        violations.append(v("EMPTY_FIELD", show,
                            "顶层不是映射（须为 project + schema + checks）"))
    else:
        violations += check_top_level(data, show)
        raw = data.get("checks")
        checks = raw if isinstance(raw, list) else []
        seen_ids = set()
        for i, check in enumerate(checks):
            violations += check_one(i, check, show, seen_ids)
        if args.final:
            # ⑤ 全字段零 [假设]（quote 字段的值豁免），遍历整棵 yaml
            for spath, text in walk_strings(data, show):
                if ASSUMPTION in text:
                    violations.append(v("HYPOTHESIS_FOUND", spath,
                                        "--final 义务⑤：零 %s（quote 引文豁免），命中：%s"
                                        % (ASSUMPTION, text[:60])))
            spec_ids = load_spec_ids(out)   # ⑥ 解析面（同目录 spec-scan.yaml）
            for i, check in enumerate(checks):
                if isinstance(check, dict):
                    violations += check_final_duties(show, check, i, spec_ids)
    payload = {
        "ok": not violations,
        "command": "check",
        "project_root": args.project_root,
        "output_dir": os.path.normpath(out).replace("\\", "/"),
        "final": bool(args.final),
        "violations": violations,
        "warnings": [],
        "counts": doc_counts(checks),
    }
    emit_via(payload, args.json, human_check)
    return 0 if payload["ok"] else 1

# trace: diy-selfcheck check 人读态（PASS 行或每条违规一行 `CODE where: msg` + 汇总行）
def human_check(payload):
    counts = payload["counts"]
    if payload["ok"]:
        print("PASS：%s selfcheck.yaml 校验通过（check %d · finding %d · disposal %d）"
              % (payload["output_dir"], counts["checks"], counts["findings"],
                 counts["disposals"]))
    else:
        for item in payload["violations"]:
            print(violation_line(item))
    print("汇总：违规 %d 条 · 警告 %d 条（exit %d）"
          % (len(payload["violations"]), len(payload["warnings"]),
             0 if payload["ok"] else 1))

# trace: diy-selfcheck 命令行面（check 子命令 + 路径位置参数；引擎不做实例解析）
def build_parser():
    ap = argparse.ArgumentParser(
        description="diy-selfcheck 确定性引擎：selfcheck.yaml 主产物校验（check）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    k = sub.add_parser("check", help="校验 selfcheck.yaml（schema/枚举/字段完整；"
                                     "--final 附加六义务）")
    k.add_argument("path", nargs="?", default=None,
                   help="selfcheck.yaml 路径（ss_ref 解析面＝同目录 spec-scan.yaml；"
                        "缺席时取 --output-dir/selfcheck.yaml）")
    k.add_argument("--output-dir", default=None,
                   help="产物目录（path 未给时必填，校验 <output-dir>/selfcheck.yaml）")
    k.add_argument("--project-root", default=".", help="项目根（默认 .；仅用于回执 where 显示）")
    k.add_argument("--final", action="store_true",
                   help="定稿六义务：b_review 非空 / summary ref 在场 / disposals 全覆盖 / "
                        "rescans 两轮 / 零 [假设]（quote 豁免）/ ss_ref 可解析")
    k.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    k.set_defaults(func=cmd_check)
    return ap

# trace: diy-selfcheck 入口（stdout/stderr 固定 UTF-8；退出码由子命令返回）
def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = build_parser().parse_args()
    sys.exit(args.func(args))

if __name__ == "__main__":
    main()
