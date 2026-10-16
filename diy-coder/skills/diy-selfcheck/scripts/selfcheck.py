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
             --final 附加六义务（底单字面；**status 门不加**——已定稿不是终门检查对象）——
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
import io
import json
import os
import re
import sys

import yaml

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import display_path, emit_via, v  # noqa: E402

SPEC_SCAN_FILE = "spec-scan.yaml"

SC_ID_RE = re.compile(r"SC-\d{3}\Z")
STATUSES = ("草稿", "已定稿")
TARGET_KINDS = ("任务书", "技能", "规格", "文档")
FINDING_SOURCES = ("预演", "引用核对", "对抗")
LAYERS = ("盲猎", "边界猎手", "验收审计")
ANCHOR_KEYS = ("md5", "exec_form", "shards")   # commit 可缺——单锚降级不红
REF_KEYS = ("ref_checked", "ref_false")        # 义务②在场即可，不核数值关系
RESCAN_KEYS = ("round1", "round2")
ASSUMPTION = "[假设]"

# 违规码冻结集（自建 12 码；测试冻结，增删须同批改测试）
VIOLATION_CODES = ("EMPTY_FIELD", "ENUM_INVALID", "ID_FMT", "ID_DUP",
                   "MISSING_FILE", "UNPARSABLE_YAML",
                   "DUTY_B_REVIEW_MISSING", "DUTY_SUMMARY_REF_MISSING",
                   "DUTY_DISPOSAL_GAP", "DUTY_RESCAN_MISSING",
                   "HYPOTHESIS_FOUND", "SS_REF_UNRESOLVED")


# trace: diy-selfcheck 违规项构造（统一 {code, where, msg} 形态，照 spec_scan 先例）


# trace: diy-selfcheck 非空判定（None / 空白字符串均视为空）
def nonempty(value):
    return value is not None and str(value).strip() != ""


# trace: diy-selfcheck YAML 安全装载：(data, err)；缺失 (None, None)、空文件 ({}, None)、损坏 (None, 原因)
def load_yaml_safe(path):
    if not os.path.isfile(path):
        return None, None
    try:
        with io.open(path, "r", encoding="utf-8") as handle:
            return (yaml.safe_load(handle) or {}), None
    except yaml.YAMLError as e:
        return None, str(e)
    except OSError as e:
        return None, str(e)


# trace: diy-selfcheck 回执输出（--json 单行 / 人读行）


# trace: diy-selfcheck 递归遍历字符串值（义务⑤ [假设] 扫描用；quote 字段的值豁免——
# 照 spec_scan :542-545 先例，引文是证据、不是未落定推断）
def walk_strings(node, path):
    if isinstance(node, str):
        yield path, node
    elif isinstance(node, dict):
        for key, val in node.items():
            if key == "quote":
                continue
            for got in walk_strings(val, "%s.%s" % (path, key)):
                yield got
    elif isinstance(node, list):
        for i, item in enumerate(node):
            for got in walk_strings(item, "%s[%d]" % (path, i)):
                yield got


# ---------------------------------------------------------------- check：selfcheck.yaml 校验

# trace: diy-selfcheck 顶层结构校验（project / schema / checks 三键在场）
def check_top_level(data, show):
    violations = []
    if "project" not in data:
        violations.append(v("EMPTY_FIELD", show + " project",
                            "project 缺失（须为映射 name/created/updated）"))
    elif not isinstance(data.get("project"), dict):
        violations.append(v("EMPTY_FIELD", show + " project",
                            "project 不是映射（name/created/updated）"))
    if "schema" not in data:
        violations.append(v("EMPTY_FIELD", show + " schema",
                            "schema 缺失（顶层版本戳，schema: 2）"))
    if "checks" not in data:
        violations.append(v("EMPTY_FIELD", show + " checks",
                            "checks 缺失（无检查写空列表）"))
    elif not isinstance(data.get("checks"), list):
        violations.append(v("EMPTY_FIELD", show + " checks", "checks 不是列表"))
    return violations


# trace: diy-selfcheck checks[].id 形态（SC-###）与同文件唯一校验
def check_id(cid, where, seen):
    if not nonempty(cid):
        return [v("EMPTY_FIELD", where, "id 缺失（须为 SC-###）")]
    text = str(cid)
    if not SC_ID_RE.fullmatch(text):
        return [v("ID_FMT", where, "id 须为 SC-###（三位数字），实为 %s" % text)]
    if text in seen:
        return [v("ID_DUP", where, "检查 ID %s 重复（同文件内号段唯一）" % text)]
    seen.add(text)
    return []


# trace: diy-selfcheck findings[] 基础校验（n 对账键 / source 三值数组 / layer 在场枚举）
def check_findings(base, findings):
    violations = []
    for i, finding in enumerate(findings):
        fw = "%s.findings[%d]" % (base, i)
        if not isinstance(finding, dict):
            violations.append(v("EMPTY_FIELD", fw,
                                "finding 不是映射（n/source/severity 三件套）"))
            continue
        if not nonempty(finding.get("n")):
            violations.append(v("EMPTY_FIELD", fw + ".n",
                                "findings[%d] 的 n 缺失（disposals 对账键）" % i))
        source = finding.get("source")
        if source is None:
            violations.append(v("EMPTY_FIELD", fw + ".source",
                                "source 缺失（须为非空数组，元素 ∈ %s）"
                                % "|".join(FINDING_SOURCES)))
        elif not isinstance(source, list):
            violations.append(v("EMPTY_FIELD", fw + ".source",
                                "source 须为数组，实为 %s（元素 ∈ %s）"
                                % (source, "|".join(FINDING_SOURCES))))
        elif not source:
            violations.append(v("EMPTY_FIELD", fw + ".source",
                                "source 为空数组（须含至少一个元素 ∈ %s）"
                                % "|".join(FINDING_SOURCES)))
        else:
            for item in source:
                if str(item) not in FINDING_SOURCES:
                    violations.append(v("ENUM_INVALID", fw + ".source",
                                        "source 越界：%s（合法集 %s）"
                                        % (item, "|".join(FINDING_SOURCES))))
        if "layer" in finding and str(finding.get("layer")) not in LAYERS:
            violations.append(v("ENUM_INVALID", fw + ".layer",
                                "layer 越界：%s（合法集 %s）"
                                % (finding.get("layer"), "|".join(LAYERS))))
    return violations


# trace: diy-selfcheck 单条 check 基础校验（id/date/status/anchor/target/六区块键）
def check_one(index, check, show, seen_ids):
    w = "%s.checks[%d]" % (show, index)
    if not isinstance(check, dict):
        return [v("EMPTY_FIELD", w,
                  "check 不是映射（id/date/status/anchor/target/findings/disposals/"
                  "rescans/b_review/revisions/summary）")]
    violations = check_id(check.get("id"), w + ".id", seen_ids)
    base = w
    if nonempty(check.get("id")):
        base = "%s.%s" % (w, str(check.get("id")))
    if not nonempty(check.get("date")):
        violations.append(v("EMPTY_FIELD", base + ".date", "date 缺失（YYYY-MM-DD）"))
    status = check.get("status")
    if not nonempty(status):
        violations.append(v("EMPTY_FIELD", base + ".status",
                            "status 缺失（草稿|已定稿）"))
    elif str(status) not in STATUSES:
        violations.append(v("ENUM_INVALID", base + ".status",
                            "status 越界：%s（合法集 %s）"
                            % (status, "|".join(STATUSES))))
    anchor = check.get("anchor")
    if not isinstance(anchor, dict):
        violations.append(v("EMPTY_FIELD", base + ".anchor",
                            "anchor 缺失或不是映射（md5/exec_form/shards 必填，commit 可缺）"))
    else:
        for key in ANCHOR_KEYS:
            if not nonempty(anchor.get(key)):
                violations.append(v("EMPTY_FIELD", base + ".anchor." + key,
                                    "anchor.%s 缺失" % key))
    target = check.get("target")
    if not isinstance(target, dict):
        violations.append(v("EMPTY_FIELD", base + ".target",
                            "target 缺失或不是映射（kind/path）"))
    else:
        kind = target.get("kind")
        if not nonempty(kind):
            violations.append(v("EMPTY_FIELD", base + ".target.kind",
                                "target.kind 缺失（任务书|技能|规格|文档）"))
        elif str(kind) not in TARGET_KINDS:
            violations.append(v("ENUM_INVALID", base + ".target.kind",
                                "target.kind 越界：%s（合法集 %s）"
                                % (kind, "|".join(TARGET_KINDS))))
        if not nonempty(target.get("path")):
            violations.append(v("EMPTY_FIELD", base + ".target.path",
                                "target.path 缺失（被自检目标相对路径）"))
    findings = check.get("findings")
    if not isinstance(findings, list):
        violations.append(v("EMPTY_FIELD", base + ".findings",
                            "findings 缺失或不是列表（无发现写空列表）"))
    else:
        violations += check_findings(base, findings)
    if not isinstance(check.get("disposals"), list):
        violations.append(v("EMPTY_FIELD", base + ".disposals",
                            "disposals 缺失或不是列表（D 表）"))
    if not isinstance(check.get("rescans"), dict):
        violations.append(v("EMPTY_FIELD", base + ".rescans",
                            "rescans 缺失或不是映射（round1/round2/cleared）"))
    if "b_review" not in check:
        violations.append(v("EMPTY_FIELD", base + ".b_review",
                            "b_review 缺失（B 部分必出；空值由 --final 义务①判）"))
    if not isinstance(check.get("revisions"), list):
        violations.append(v("EMPTY_FIELD", base + ".revisions",
                            "revisions 缺失或不是列表（无修订写空列表）"))
    if not isinstance(check.get("summary"), dict):
        violations.append(v("EMPTY_FIELD", base + ".summary",
                            "summary 缺失或不是映射（total/by_source/ref_checked/ref_false）"))
    return violations


# trace: diy-selfcheck 集合字段取列表（缺失/非列表 → []，缺项由 check 层单独报）
def items(doc, key):
    if not isinstance(doc, dict):
        return []
    value = doc.get(key)
    return value if isinstance(value, list) else []


# trace: diy-selfcheck 同目录 spec-scan.yaml 的 finding id 集合（义务⑥解析面；
# 文件不存在/损坏 → 空集，带 ss_ref 者按解析不到判红）
def load_spec_ids(out_dir):
    data, _ = load_yaml_safe(os.path.join(out_dir, SPEC_SCAN_FILE))
    ids = set()
    for scan in items(data, "scans"):
        if not isinstance(scan, dict):
            continue
        for finding in items(scan, "findings"):
            if isinstance(finding, dict) and nonempty(finding.get("id")):
                ids.add(str(finding["id"]))
    return ids


# trace: diy-selfcheck 非空凭证判定（字符串非空白 / 列表映射非空 / 其余标量在场即算）
def present(value):
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() != ""
    if isinstance(value, (list, dict)):
        return len(value) > 0
    return True


# trace: diy-selfcheck --final 六义务（①b_review ②summary ref ③disposals 对账 ④rescans 两轮
# ⑥ss_ref 可解析——⑤全文件零 [假设] 在 cmd_check 层跑，须遍历整棵 yaml）
def check_final_duties(show, check, index, spec_ids):
    w = "%s.checks[%d]" % (show, index)
    base = w
    if nonempty(check.get("id")):
        base = "%s.%s" % (w, str(check.get("id")))
    violations = []
    # ① B 部分必出：b_review 非空
    if not nonempty(check.get("b_review")):
        violations.append(v("DUTY_B_REVIEW_MISSING", base + ".b_review",
                            "--final 义务①：b_review 非空（B 部分必出）"))
    # ② 引用核对必报总数：ref_checked/ref_false 在场即可，不核数值关系
    summary = check.get("summary")
    if not isinstance(summary, dict):
        violations.append(v("DUTY_SUMMARY_REF_MISSING", base + ".summary",
                            "--final 义务②：summary 缺失（须含 ref_checked/ref_false）"))
    else:
        missing = [key for key in REF_KEYS if key not in summary]
        if missing:
            violations.append(v("DUTY_SUMMARY_REF_MISSING", base + ".summary",
                                "--final 义务②：summary 缺 %s（引用核对必报总数，在场即可）"
                                % "/".join(missing)))
    # ③ disposals 以 finding n 对账 findings 全覆盖（缺/孤儿均算缺口）
    find_ns = {}
    for i, finding in enumerate(items(check, "findings")):
        if isinstance(finding, dict) and nonempty(finding.get("n")):
            find_ns[str(finding["n"])] = "%s.findings[%d]" % (base, i)
    covered = set()
    for i, disposal in enumerate(items(check, "disposals")):
        dw = "%s.disposals[%d]" % (base, i)
        if not isinstance(disposal, dict) or not nonempty(disposal.get("finding")):
            violations.append(v("DUTY_DISPOSAL_GAP", dw,
                                "--final 义务③：disposals[%d] 缺 finding 对账键" % i))
            continue
        ntext = str(disposal["finding"])
        covered.add(ntext)
        if ntext not in find_ns:
            violations.append(v("DUTY_DISPOSAL_GAP", dw,
                                "--final 义务③：disposals 指向不存在的 finding n=%s" % ntext))
    for ntext, fw in find_ns.items():
        if ntext not in covered:
            violations.append(v("DUTY_DISPOSAL_GAP", fw,
                                "--final 义务③：finding n=%s 无处置记录（须全覆盖）" % ntext))
    # ④ rescans 两轮复扫凭证在场且非空
    rescans = check.get("rescans")
    if not isinstance(rescans, dict):
        violations.append(v("DUTY_RESCAN_MISSING", base + ".rescans",
                            "--final 义务④：rescans 缺失（须含 round1/round2 两轮凭证）"))
    else:
        for key in RESCAN_KEYS:
            if not present(rescans.get(key)):
                violations.append(v("DUTY_RESCAN_MISSING", base + ".rescans." + key,
                                    "--final 义务④：rescans.%s 缺席或为空（两轮复扫）" % key))
    # ⑥ 在场的 ss_ref 逐条在同目录 spec-scan.yaml 可解析
    for i, finding in enumerate(items(check, "findings")):
        if not isinstance(finding, dict):
            continue
        ss_ref = finding.get("ss_ref")
        if not nonempty(ss_ref):
            continue   # ss_ref 缺席＝义务对缺席项不红
        if str(ss_ref) not in spec_ids:
            violations.append(v("SS_REF_UNRESOLVED",
                                "%s.findings[%d].ss_ref" % (base, i),
                                "--final 义务⑥：ss_ref %s 在同目录 %s 解析不到"
                                % (ss_ref, SPEC_SCAN_FILE)))
    return violations


# trace: diy-selfcheck 回执计数（check / finding / disposal）
def doc_counts(checks):
    findings = disposals = 0
    for check in checks:
        if not isinstance(check, dict):
            continue
        findings += len(items(check, "findings"))
        disposals += len(items(check, "disposals"))
    return {"checks": len(checks), "findings": findings, "disposals": disposals}


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
            print("%s %s: %s" % (item["code"], item["where"], item["msg"]))
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
