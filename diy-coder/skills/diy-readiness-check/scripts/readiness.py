# -*- coding: utf-8 -*-
"""diy-readiness-check 确定性引擎：开工前门禁 + 需求清点（跨文档核对委派 diyc）+ readiness.yaml 校验。

子命令：
  collect  开工前体检的确定性部分（只读检测，绝不写文件）：
             1 门禁：prd.yaml / architecture.yaml /
               epics.yaml / stories.yaml 在场，且 epics / stories 的 project.status 为
               已定稿；不满足 → 零产出 exit 1 + 结构化拒绝回执（violations 带码 +
               gate.route 给路由）。architecture 一档：缺席/损坏 → gate
               拒跑、route diy-architecture；只判在场/可解析，不要求已定稿。
               design.yaml 缺席维持现状（零检查零 warning）。
             2 需求清点单：读结构化 prd.yaml（features[].requirements[] 全量 FR + priority +
               归属 feature；nfrs[]）与 epics / stories 计数——「人工通读
               md 提取全量 FR/NFR」的确定性下沉（diy 产物即结构化单一源）。
             3 跨文档核对委托：子进程跑 `diyc.py check --type prd|epics|stories
               --final --json`——diyc 是跨文档机械核对的唯一入口，本引擎不重实现其规则；
               回执违规并入 diyc.check.violations 证据键（readiness 会话据此裁决，不在此判死）。
               diyc 缺席 / 子进程失败 → 结构化 warning 降级（TOOL_MISSING / TOOL_ERROR），不崩。
             4 coverage：必须级 FR 与 stories AC refs 的覆盖与缺口（口径同 diyc stories 规则
               「每个必须 FR 至少被一条 AC 的 refs 引用」；diyc 回执只给违规不给逐 FR 清单，
               故由结构化产物派生，跨文档判定权仍在 diyc）。
  check    校验 {output_dir}/readiness.yaml（IR-### 集合，形状对齐 bug-log.yaml）：schema /
           枚举 / finding area+severity 枚举 / verdict 与 findings 一致性（就绪 ⇒ 零
           严重|高；未就绪 ⇒ 至少 1 条 严重|高）/ ID 唯一；--final 附加：
           status 已落 已定稿、verdict 非空、每条 finding 有 evidence、counts 与集合一致
           （findings_by_severity 与 coverage 守恒）、零 [假设]。exit 0 唯一放行。

分工裁定：readiness 属新产物类型，不进 diyc.py check 的硬编码类型集；
本引擎契约同构（exit 0 唯一放行 / --json 单行回执 / violations[{code, where, msg}] + counts；
where 正斜杠、相对 project-root）；--previous 不实现（报告追加式）。
违规码复用套件冻结集，新增 TOOL_MISSING / TOOL_ERROR（diyc 委派降级专用）。
diyc 路径由引擎自身位置推算（skills/ 根，源码与安装两种布局同构）；产物与 IR-### ID 由
diy-readiness-check 会话（LLM）创作，本引擎只校验格式与唯一性。
"""
import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import display_path, diyc_script_path, emit_via, nonempty, v  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from readiness_checks import cmd_check  # noqa: E402
from readiness_lib import DIYC_TYPES, compute_coverage, doc_summaries, gate_check, load_docs, read_requirements  # noqa: E402

# ---------------------------------------------------------------- diyc 委派

def diyc_type_check(script, project_root, type_name):
    """委派 diyc check --type T --final。返回 (回执 dict | None, warning | None)。"""
    where = "diyc.py check --type %s" % type_name
    cmd = [sys.executable, script, "check", "--type", type_name, "--final",
           "--project-root", project_root, "--json"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              encoding="utf-8", errors="replace")
    except OSError as e:
        return None, v("TOOL_ERROR", where, "diyc 子进程无法启动：%s" % e)
    if proc.returncode not in (0, 1):
        tail = " ".join((proc.stderr or proc.stdout or "").split())[-200:]
        return None, v("TOOL_ERROR", where,
                       "diyc 非预期退出码 %s（期望 0|1）：%s"
                       % (proc.returncode, tail or "无输出"))
    payload = None
    for line in reversed((proc.stdout or "").splitlines()):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
            break
        except ValueError:
            continue
    if not isinstance(payload, dict):
        return None, v("TOOL_ERROR", where, "diyc 回执不可解析（--json 面单行 JSON 缺失）")
    return payload, None

def run_diyc_checks(project_root, out_dir):
    """跑 prd/epics/stories 三型 check，合并回执。返回 (diyc 块, warnings)。"""
    warnings = []
    script = diyc_script_path()
    block = {"available": False, "script": display_path(script, project_root),
             "checked": [], "check": {"violations": [], "counts": {}}}
    if not os.path.isfile(script):
        warnings.append(v("TOOL_MISSING", block["script"],
                          "diyc.py 缺席：跨文档核对降级，请从会话侧人工复核 ID 链与覆盖"))
        return block, warnings
    block["available"] = True
    for type_name in DIYC_TYPES:
        payload, warning = diyc_type_check(script, project_root, type_name)
        if warning is not None:
            warnings.append(warning)
            continue
        block["checked"].append(type_name)
        # diyc 自解析产物目录：与本引擎 --output-dir 不一致时证据来自另一目录，须显式告警
        resolved = payload.get("output_dir")
        if nonempty(resolved):
            a = os.path.normcase(os.path.abspath(os.path.join(project_root, str(resolved))))
            if a != os.path.normcase(out_dir):
                warnings.append(v("SET_MISMATCH", str(resolved),
                                  "diyc 解析的产物目录与本引擎 --output-dir 不一致："
                                  "跨文档证据可能来自另一目录"))
        for item in payload.get("violations") or []:
            if isinstance(item, dict):
                block["check"]["violations"].append(dict(item, type=type_name))
        if isinstance(payload.get("counts"), dict):
            block["check"]["counts"][type_name] = payload["counts"]
        if payload.get("warnings"):
            block["check"].setdefault("warnings", []).extend(payload["warnings"])
    return block, warnings

# ---------------------------------------------------------------- collect

def empty_payload(args):
    return {
        "ok": False,
        "command": "collect",
        "project_root": args.project_root,
        "output_dir": os.path.normpath(os.path.abspath(args.output_dir)).replace("\\", "/"),
        "gate": {"passed": False, "files": {}, "route": None},
        "requirements": None,
        "coverage": None,
        "docs": {},
        "diyc": {"available": False, "script": None, "checked": [],
                 "check": {"violations": [], "counts": {}}},
        "violations": [],
        "warnings": [],
        "counts": {},
    }

def cmd_collect(args):
    root = os.path.abspath(args.project_root)
    out = os.path.abspath(args.output_dir)
    docs = load_docs(out)
    warnings = []
    payload = empty_payload(args)
    payload["docs"] = doc_summaries(docs)

    passed, violations, route = gate_check(docs, out, root)
    payload["gate"] = {"passed": passed, "files": payload["docs"], "route": route}
    payload["violations"] = violations

    if not passed:
        payload["warnings"] = warnings
        emit_via(payload, args.json, human_collect)
        return 1

    inventory = read_requirements(docs)
    coverage = compute_coverage(inventory["frs"], inventory["referenced"])
    diyc_block, diyc_warnings = run_diyc_checks(root, out)
    warnings += diyc_warnings

    payload["ok"] = True
    payload["requirements"] = {"frs": inventory["frs"], "nfrs": inventory["nfrs"],
                               "must_frs": [f["id"] for f in inventory["frs"]
                                            if f.get("priority") == "必须"]}
    payload["coverage"] = coverage
    payload["diyc"] = diyc_block
    payload["warnings"] = warnings
    payload["counts"] = {
        "features": len({f["feature"] for f in inventory["frs"] if nonempty(f["feature"])}),
        "frs": len(inventory["frs"]),
        "nfrs": len(inventory["nfrs"]),
        "epics": inventory["epics"],
        "stories": inventory["stories"],
        "acs": inventory["acs"],
        "must_frs": coverage["must_frs"],
        "covered": coverage["covered"],
        "gaps": len(coverage["gaps"]),
        "diyc_violations": len(diyc_block["check"]["violations"]),
    }
    emit_via(payload, args.json, human_collect)
    return 0

def human_collect(payload):
    if not payload["ok"]:
        if payload["violations"]:
            print("拒绝：")
            for item in payload["violations"]:
                print("- %s %s: %s" % (item["code"], item["where"], item["msg"]))
        else:  # 冗余防御：ok=False 必带 violation（当前不可达）
            print("拒绝：门禁未通过")
        print("路由：%s" % payload["gate"]["route"])
        return
    counts = payload["counts"]
    coverage = payload["coverage"]
    print("门禁通过：prd / architecture 在场，epics / stories 齐备且定稿。")
    print("需求清点：FR %d（必须 %d）· NFR %d · epic %d · story %d · AC %d"
          % (counts["frs"], counts["must_frs"], counts["nfrs"],
             counts["epics"], counts["stories"], counts["acs"]))
    print("覆盖：必须 FR %d 中 %d 覆盖，缺口 %d %s"
          % (coverage["must_frs"], coverage["covered"], len(coverage["gaps"]),
             "（%s）" % "、".join(coverage["gaps"]) if coverage["gaps"] else ""))
    if payload["diyc"]["available"]:
        print("diyc 跨文档核对：%s 已跑，违规 %d 条（并入 diyc.check.violations 证据）"
              % (" / ".join(payload["diyc"]["checked"]),
                 len(payload["diyc"]["check"]["violations"])))
    else:
        print("diyc 跨文档核对：不可用（见 warnings）")
    for item in payload["warnings"]:
        print("警告 %s %s: %s" % (item["code"], item["where"], item["msg"]))

def build_parser():
    ap = argparse.ArgumentParser(
        description="diy-readiness-check 确定性引擎：开工前门禁 + 需求清点（委派 diyc）+ "
                    "readiness.yaml 校验")
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("collect", help="门禁检测 + 需求清点 + 委派 diyc 跨文档核对（只读）")
    c.add_argument("--project-root", default=".", help="项目根（默认 .）")
    c.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    c.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    c.set_defaults(func=cmd_collect)

    k = sub.add_parser("check", help="校验 readiness.yaml（schema/枚举/verdict 一致性；--final 附加定稿义务）")
    k.add_argument("--project-root", default=".", help="项目根（默认 .）")
    k.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    k.add_argument("--final", action="store_true",
                   help="定稿校验：status 已落 已定稿 + verdict 已定 + evidence/counts 义务 + 零假设")
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
