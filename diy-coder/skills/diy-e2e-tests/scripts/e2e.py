# -*- coding: utf-8 -*-
"""diy-e2e-tests 确定性引擎：测试框架探测（detect）+ e2e 用例追加写回（record）。

子命令：
  detect  语言无关的项目探测（只读）：依次读 package.json / pyproject.toml /
          requirements*.txt / Cargo.toml / go.mod / pom.xml / build.gradle* / Gemfile /
          composer.json 等清单判定 project_type 与既有测试框架；再识别测试目录与
          既有测试文件模式。无框架 → 回执给 suggested（建议框架，由用户确认），
          **绝不自动安装**。清单损坏/缺失降级为 warning，探测继续，不崩。
  record  把本次生成的 TC（JSON 文件，形态 [ {...} ] 或 {"test_cases": [...]}）
          追加进 {output_dir}/test-plan.yaml（diy-augment 窄写权先例：只追加，不改
          既有条目、不新增产物类型）。校验：id 规则 TC-{ac}.{seq} 且前缀与 ac 一致、
          续号不重号、ac 解析（stories.yaml）、type == 端到端、technique == 场景、
          dimension 五轴枚举、kill_target 引用 FH ID（新故障带 fault_hypothesis
          {id, ac, text} 联动落盘）、api_refs 可选复合锚（operationId/path/method）、
          title/steps 非空、status ∈ {通过, 失败}、priority ∈ {P0,P1,P2}。
          写回联动维护 schema：新 FH 追加进 fault_hypotheses、(ac, dimension) 审计格
          补录本 TC（not_applicable 格被实际用例推翻即转 tcs 型）。
          全部通过才写（原子：同目录临时文件 + os.replace）。随后委派
          `diyc.py check --type test-plan --json` 交叉验证追加后的全链——其违规并入
          回执 `diyc` 键（warning 面），不阻塞本命令的写权结论。

分工裁定（任务书 §8）：e2e 生成不新增产物类型，写权三面 = ① test-plan.yaml 追加 TC
② 项目测试目录的测试代码 ③ 收尾会话摘要；不写 sprint.yaml / stories.yaml / 其他产物。
实例解析委托 SKILL.md 侧的 `diyc.py resolve`；本引擎不做 --instance / 白名单 / 目录推导，
--output-dir 必填。契约同构（batch3-contract §3）：exit 0 唯一放行 / 1 = 违规或被拒绝 /
2 = 用法错误；--json 单行回执（ensure_ascii=False）；violations[{code, where, msg}] + counts；
where 正斜杠、相对 project-root。

违规码：复用 batch3-contract §3 冻结集（MISSING_FILE UNPARSABLE_YAML DUPLICATE_ID
UNKNOWN_ID ENUM_INVALID EMPTY_FIELD ENTRY_INVALID TOOL_MISSING TOOL_ERROR SET_MISMATCH）；
新增 MANIFEST_UNPARSABLE（detect 专用：清单文件存在但不可解析，探测降级不崩，回报登记）。
"""
# trace: 迁移计划 §二 验收 #3 / #4 / #12（领域引擎接线 + 窄写权）
import argparse
import json
import os
import sys


sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import display_path, diyc_script_path, nonempty, now, save_yaml_atomic, v  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from e2e_checks import PLAN_FILE, check_case, diyc_check_test_plan, load_known, load_tc_cases  # noqa: E402,F401
from e2e_detect import cmd_detect  # noqa: E402

def cmd_record(args):
    root = os.path.abspath(args.project_root)
    out = os.path.abspath(args.output_dir)
    plan_path = os.path.join(out, PLAN_FILE)
    show = display_path(plan_path, root)
    tc_show = display_path(os.path.abspath(args.tc_file), root)
    violations = []
    warnings = []

    cases, tc_violations = load_tc_cases(os.path.abspath(args.tc_file), tc_show)
    violations += tc_violations
    plan = known_ids = known_acs = None
    stories_available = False
    if cases is not None:
        plan, known_ids, known_acs, stories_available = load_known(
            out, show, violations, warnings)

    if cases is not None and plan is not None:
        known_fh = {str(h.get("id")) for h in
                    (plan.get("fault_hypotheses") or [])
                    if isinstance(h, dict) and nonempty(h.get("id"))} \
            if isinstance(plan, dict) else set()
        seen_new = set()
        for i, case in enumerate(cases):
            violations += check_case(case, i, show, known_ids, seen_new,
                                     known_acs, stories_available, known_fh)
            if isinstance(case, dict) and nonempty(case.get("id")):
                seen_new.add(str(case["id"]))
            if isinstance(case, dict) and isinstance(case.get("fault_hypothesis"), dict):
                known_fh.add(str(case["fault_hypothesis"].get("id")))

    appended = [str(c["id"]) for c in cases
                if isinstance(c, dict) and nonempty(c.get("id"))] if cases else []
    if not violations:
        # FH 联动追加：kill_target 引的新 FH 随 TC 落盘（先落 FH 再写 TC——追加权裁定）
        merged_fhs = [dict(h) for h in (plan.get("fault_hypotheses") or [])
                      if isinstance(h, dict)]
        fh_seen = {h.get("id") for h in merged_fhs}
        for c in cases:
            fh = c.get("fault_hypothesis")
            if isinstance(fh, dict) and fh.get("id") not in fh_seen:
                fh_seen.add(fh.get("id"))
                merged_fhs.append({"id": fh.get("id"), "ac": fh.get("ac"),
                                   "text": fh.get("text")})
        # 五轴 audit 维护：(ac, dimension) 格补录本 TC；not_applicable 格被实际用例推翻即转 tcs 型
        audit = [dict(e) for e in (plan.get("dimension_audit") or [])]
        for c in cases:
            ac_id, dim, tid = c.get("ac"), c.get("dimension"), c.get("id")
            if not (isinstance(ac_id, str) and isinstance(dim, str) and nonempty(tid)):
                continue
            hit = next((e for e in audit if isinstance(e, dict)
                        and e.get("ac") == ac_id and e.get("axis") == dim), None)
            if hit is None:
                audit.append({"ac": ac_id, "axis": dim, "tcs": [tid]})
            elif isinstance(hit.get("tcs"), list):
                if tid not in hit["tcs"]:
                    hit["tcs"] = list(hit["tcs"]) + [tid]
            else:
                hit.pop("not_applicable", None)
                hit["tcs"] = [tid]
        merged = list(plan.get("test_cases"))
        merged += [{k: x for k, x in c.items() if k != "fault_hypothesis"}
                   for c in cases]
        project = plan.get("project")
        new_project = dict(project) if isinstance(project, dict) else {}
        new_project["updated"] = now()
        updated_plan = dict(plan)
        updated_plan["project"] = new_project
        updated_plan["test_cases"] = merged
        updated_plan["fault_hypotheses"] = merged_fhs
        updated_plan["dimension_audit"] = audit
        try:
            save_yaml_atomic(plan_path, updated_plan)
        except OSError as e:
            violations.append(v("TOOL_ERROR", show, "写回失败（原文件未改）：%s" % e))
            appended = []
        else:
            plan = updated_plan

    diyc_block = {"available": False, "script": None,
                  "check": {"ok": None, "violations": [], "counts": {}}}
    if not violations:
        diyc_block, diyc_warnings = diyc_check_test_plan(
            diyc_script_path(), root, out)
        warnings += diyc_warnings

    cases_total = 0
    if isinstance(plan, dict) and isinstance(plan.get("test_cases"), list):
        cases_total = len(plan["test_cases"])
    ok = not violations
    payload = {
        "ok": ok,
        "command": "record",
        "project_root": args.project_root,
        "output_dir": os.path.normpath(out).replace("\\", "/"),
        "appended": appended if ok else [],
        "violations": violations,
        "warnings": warnings,
        "counts": {"appended": len(appended) if ok else 0, "cases_total": cases_total},
        "diyc": diyc_block,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        if ok:
            print("PASS：追加 %d 条 e2e 用例（%s）→ %s（总用例 %d）"
                  % (len(appended), ", ".join(appended), show, cases_total))
            for item in diyc_block["check"]["violations"]:
                print("- [diyc] %s %s: %s" % (item.get("code"), item.get("where"),
                                              item.get("msg")))
        else:
            print("FAIL：追加被拒绝，零写入")
            for item in violations:
                print("- %s %s: %s" % (item["code"], item["where"], item["msg"]))
        for item in warnings:
            print("- %s %s: %s" % (item["code"], item["where"], item["msg"]))
    return 0 if ok else 1

def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(
        description="diy-e2e-tests 确定性引擎：测试框架探测（detect）+ e2e 用例追加（record）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("detect", help="语言无关框架探测（只读；无框架回 suggested，不自动安装）")
    d.add_argument("--project-root", default=".", help="项目根（默认 .）")
    d.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    d.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    d.set_defaults(func=cmd_detect)

    r = sub.add_parser("record", help="把生成的 e2e 用例追加进 test-plan.yaml（校验通过才写）")
    r.add_argument("--tc-file", required=True, help="本次生成的 TC JSON 文件")
    r.add_argument("--project-root", default=".", help="项目根（默认 .）")
    r.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    r.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    r.set_defaults(func=cmd_record)

    args = ap.parse_args()
    sys.exit(args.func(args))

if __name__ == "__main__":
    main()
