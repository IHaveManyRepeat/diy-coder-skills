# -*- coding: utf-8 -*-
"""diy-correct-course 确定性引擎：影响面采集（委派 diyc 交叉核对）+ change-proposal.yaml 校验。

子命令：
  collect  执行期变更的影响面采集（只读，绝不写文件）：
             1 门禁（HALT 判据的机械面）：prd.yaml / epics.yaml / stories.yaml
               三件套在场且 project.status 均为 已定稿；不满足 → 零产出 exit 1 +
               结构化拒绝回执（violations 带码 + gate.route 给路由）。
               architecture.yaml / openapi.yaml / design.yaml 缺席不拒（源「Architecture、
               UI/UX 可选」）→ warning。
             2 影响面摘要：读六产物的 ID 级摘要——prd features/FR/NFR、epics、
               stories + AC、architecture decisions、openapi operations、design pages。
               摘要只带 ID / 标题级信息，不复制内容（引用式纪律）。
             3 跨文档核对委托：子进程跑 `diyc.py check --type
               prd|architecture|openapi|epics|stories --final --json`——diyc 是跨文档机械核对
               的唯一入口，本引擎不重实现其规则；回执违规并入 diyc.check.violations 证据键
               （影响证据，不在此判死）。diyc 缺席 / 失败 → TOOL_MISSING / TOOL_ERROR 降级
               warning，不崩。
             4 引用链（--target ID）：跨文档扫描该 ID 的上游/下游引用点（epics.feature_refs /
               AC.refs / AC.design_ref / decisions.affects / openapi x-fr / TC.ac /
               sprint test_refs + prd feature→FR、story→AC 归属边），迭代两跳；命中集合即
               变更涟漪面（施工影响的机械证据）。引用链仅支持稳定 ID（文件类 path: 目标
               不参与遍历）；target 格式非法 → ENUM_INVALID，产物中无此 ID → UNKNOWN_ID，
               均 exit 1 零产出。
  check    校验 {output_dir}/change-proposal.yaml（CP-### 集合）：schema / 枚举
           （status/mode/scope/artifact/kind）/ edits 完整（old+new+rationale 非空且
           old != new）/ impacts 与 edits 的 target 形态（产物类稳定 ID / infra 类
           path:<相对路径>，形态与 artifact 双向绑定）/ handoff.route 白名单 / ID 唯一 /
           单项 --id 过滤；--final 附加：status ∈ {已定稿, 已批准}、zero [假设]、
           handoff.route 在场且白名单、impacts 非空、approach 已选定（PENDING_DECISION）、
           scope 与 handoff 一致性（轻微→单技能直改 / 中等→backlog 重组 /
           重大→规划层）。exit 0 唯一放行。

分工裁定：change-proposal 属新产物类型，不进 diyc.py check 的硬编码
类型集；本引擎契约同构（exit 0 唯一放行 / --json 单行回执 / violations[{code, where, msg}]
+ counts；where 正斜杠、相对 project-root）；--previous 不实现（提案记录追加式，同 key 原位
更新，无 ID 集合收缩风险）。违规码全部复用冻结集；新增 TOOL_MISSING / TOOL_ERROR（diyc 委派降级专用，同 readiness 先例）。
只出提案、不改真源：本引擎与技能都不写 prd / epics / stories / architecture / openapi /
design / sprint —— 真源修改由各产物所属技能的 update 模式执行。
"""
# trace: 前置门禁零产出退出 + ID 链接入 + diyc 接线
import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import display_path, diyc_script_path, emit_via, nonempty, v  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from change_proposal_checks import cmd_check  # noqa: E402
from change_proposal_lib import DIYC_TYPES, OPTIONAL_FILES, doc_status, doc_summaries, is_target_id, load_docs  # noqa: E402
from change_proposal_refs import gate_check, known_ids, ref_sites, scan_chain  # noqa: E402

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
    """跑五型 check，合并回执。返回 (diyc 块, warnings)。"""
    warnings = []
    script = diyc_script_path()
    block = {"available": False, "script": display_path(script, project_root),
             "checked": [], "check": {"violations": [], "counts": {}}}
    if not os.path.isfile(script):
        warnings.append(v("TOOL_MISSING", block["script"],
                          "diyc.py 缺席：跨文档核对降级，请从会话侧人工复核 ID 链与引用面"))
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

def empty_payload(args, command):
    return {
        "ok": False,
        "command": command,
        "project_root": args.project_root,
        "output_dir": os.path.normpath(os.path.abspath(args.output_dir)).replace("\\", "/"),
        "violations": [],
        "warnings": [],
        "counts": {},
    }

def cmd_collect(args):
    root = os.path.abspath(args.project_root)
    out = os.path.abspath(args.output_dir)
    docs = load_docs(out)
    warnings = []
    payload = empty_payload(args, "collect")
    payload.update({
        "gate": {"passed": False, "files": doc_status(docs), "route": None},
        "docs": {},
        "chain": [],
        "diyc": {"available": False, "script": None, "checked": [],
                 "check": {"violations": [], "counts": {}}},
    })

    passed, violations, route = gate_check(docs, out, root)
    payload["gate"] = {"passed": passed, "files": doc_status(docs), "route": route}
    payload["violations"] = violations

    for filename in OPTIONAL_FILES:
        entry = docs[filename]
        show = display_path(os.path.join(out, filename), root)
        if entry["err"] is not None:
            warnings.append(v("UNPARSABLE_YAML", show,
                              "%s 不可解析，影响面采集将跳过该文档" % filename))
        elif not entry["present"]:
            warnings.append(v("MISSING_FILE", show,
                              "%s 未找到：影响面采集粒度受限（源「可选文档」语义，不阻断）"
                              % filename))

    if not passed:
        payload["warnings"] = warnings
        emit_via(payload, args.json, human_collect)
        return 1

    summaries = doc_summaries(docs)
    payload["docs"] = summaries

    target = args.target
    if nonempty(target) and not is_target_id(str(target)):
        payload["violations"] = [v("ENUM_INVALID", "--target",
                                   "引用链遍历仅支持稳定 ID（如 FR-x.y / F-x / S-x / "
                                   "AC-x.y / D-x / TC-x.y.z）；文件类目标（path:...）"
                                   "不参与引用链，实为 %s" % target)]
        payload["warnings"] = warnings
        emit_via(payload, args.json, human_collect)
        return 1
    if nonempty(target) and str(target) not in known_ids(docs):
        payload["violations"] = [v("UNKNOWN_ID", "--target",
                                   "%s 在六产物与 test-plan / sprint 中均不存在" % target)]
        payload["warnings"] = warnings
        emit_via(payload, args.json, human_collect)
        return 1

    chain = scan_chain(str(target), ref_sites(docs)) if nonempty(target) else []
    diyc_block, diyc_warnings = run_diyc_checks(root, out)
    warnings += diyc_warnings

    payload["ok"] = True
    payload["chain"] = chain
    payload["diyc"] = diyc_block
    payload["warnings"] = warnings
    payload["counts"] = {
        "features": len(summaries["prd"]["features"]),
        "frs": sum(len(f["requirements"]) for f in summaries["prd"]["features"]),
        "nfrs": len(summaries["prd"]["nfrs"]),
        "epics": len(summaries["epics"]["epics"]),
        "stories": len(summaries["stories"]["stories"]),
        "acs": sum(len(s["acs"]) for s in summaries["stories"]["stories"]),
        "decisions": len(summaries["architecture"]["decisions"]),
        "operations": len(summaries["openapi"]["operations"]),
        "pages": len(summaries["design"]["pages"]),
        "chain": len(chain),
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
    print("门禁通过：prd / epics / stories 齐备且定稿。")
    print("影响面摘要：FR %d · NFR %d · epic %d · story %d · AC %d · 决策 %d · 操作 %d · 页面 %d"
          % (counts["frs"], counts["nfrs"], counts["epics"], counts["stories"],
             counts["acs"], counts["decisions"], counts["operations"], counts["pages"]))
    if counts["chain"]:
        print("引用链：%d 个引用点" % counts["chain"])
        for hit in payload["chain"]:
            print("- %s %s.%s → %s（%s）"
                  % (hit["doc"], hit["id"], hit["field"], hit["ref"], hit["direction"]))
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
        description="diy-correct-course 确定性引擎：影响面采集（委派 diyc）+ "
                    "change-proposal.yaml 校验")
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("collect", help="门禁 + 六产物影响面摘要 + 委派 diyc 交叉核对 + 引用链（只读）")
    c.add_argument("--project-root", default=".", help="项目根（默认 .）")
    c.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    c.add_argument("--target", default=None,
                   help="变更目标 ID（如 FR-1.1 / S-1 / AC-1.1）：输出其上游/下游引用链")
    c.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    c.set_defaults(func=cmd_collect)

    k = sub.add_parser("check", help="校验 change-proposal.yaml（schema/枚举/edits 完整性；"
                                     "--final 附加定稿与交接义务）")
    k.add_argument("--project-root", default=".", help="项目根（默认 .）")
    k.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    k.add_argument("--id", default=None, help="只校验指定记录（CP-###；缺省校验全部）")
    k.add_argument("--final", action="store_true",
                   help="定稿校验：status ∈ {已定稿, 已批准} + 零假设 + handoff/impacts/approach 义务")
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
