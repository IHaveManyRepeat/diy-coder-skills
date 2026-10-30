# -*- coding: utf-8 -*-
"""diy-test-gate check 面：`{output_dir}/test-gate.yaml` 校验（TG-### 集合）。

校验面：schema / 枚举（scope / status / coverage / priority / 域状态 / risk / decision /
判据名与 target / waiver 键）/ 记录 ID 唯一 / 引用解析（产物自身的 AC / TC / S 存在性——
test-gate 不在 diyc 类型集内，本模块自实现，不与 diyc 已覆盖规则重复）/ totals 与
by_level 重算 / 门决策自洽（硬判据 actual 重算 + 两组判据与 decision 的关系 + overlay
与 NFR 域状态）/ waiver 8 键契约（安全域 FAIL 不可豁免）/ 阈值 source 强制记出处 /
合规五标准的记账与聚合（G-3，第五个走查维度，落 `nfr.domains[].findings`）；
`--final` 附加：status 已落 已定稿、basis 非空、hard / soft 两组判据齐、零 [假设]、
合规五标准逐条记账、跨域合成候选的落点（G-4）；
`mutation-report.yaml` 缺席日常记 `n/a` + warning、`--final` 时判 `MISSING_FILE`

本模块只重算「同记录内可机械重算」的量（判据 actual、totals、by_level、overall_risk、
非功能致命、P0 未覆盖、变异得分、合规聚合）——不重跑 collect 的覆盖判定表
（那是 `gate.py collect` 与 steps/03 LLM 复核的职责），避免二份实现。本模块不写盘。

违约码：复用冻结集（MISSING_FILE / UNPARSABLE_YAML / DUPLICATE_ID /
UNKNOWN_ID / ENUM_INVALID / EMPTY_FIELD / ASSUMPTION_PRESENT / SET_MISMATCH /
STATUS_MISMATCH / EVIDENCE_MISSING / PENDING_DECISION）+ diyc 委派降级码 TOOL_MISSING /
TOOL_ERROR。本技能新增码：
  DECISION_INCONSISTENT  门决策与两组判据 / NFR 域状态 / overlay 不自洽
  CRITERION_STALE        判据 actual/result 与从同记录机械重算的值不一致
  WAIVER_INCOMPLETE      waiver 缺 8 键契约中的键（或值为空）
  WAIVER_INAPPLICABLE    waiver ref 指向 安全域（不可豁免）或不可解析的域名
  THRESHOLD_UNSOURCED    阈值 source 非「用户会话 <date>」形态（阈值不得猜测）
  UNKNOWN_THRESHOLD_PASS 域含 UNKNOWN 阈值却记 PASS（nfr-status-definitions 硬规则）
能力补齐轮新增 4 码（源 trace / nfr checklist 条目，2026-09-18 返工）：
  EVIDENCE_STALE            证据 >7 天（台账 red/green 时间戳 / mutation run 日期）——warning
  COMPLIANCE_UNRECORDED     合规五标准缺记录 / 缺聚合行 / 行形态不合（--final）
  COMPLIANCE_AGGREGATE_MISMATCH  标准聚合行与逐域观察行重算不符（FAIL>PARTIAL>PASS）
  CROSS_DOMAIN_UNRECORDED   跨域风险合成候选命中而未落 recommendations / findings（--final）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gate_check_record import check_record  # noqa: E402
from gate_evidence import mutation_block  # noqa: E402
from gate_lib import (  # noqa: E402
    GATE_FILE, PLAN_FILE, STORIES_FILE, ac_index, count_by, display_path,
    emit_via, items_of, load_yaml_safe, nonempty, tc_index, v,
)


def cmd_check(args):
    root = os.path.abspath(args.project_root)
    out = os.path.abspath(args.output_dir)
    path = os.path.join(out, GATE_FILE)
    show = display_path(path, root)
    violations, warnings, records = [], [], []
    data, err = load_yaml_safe(path)
    if data is None and err is None:
        violations.append(v("MISSING_FILE", show,
                            "%s 不存在（先完成一次 test-gate 起草）" % GATE_FILE))
    elif err is not None:
        violations.append(v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err))
    elif not isinstance(data, dict):
        violations.append(v("EMPTY_FIELD", show,
                            "顶层不是映射（须为 project + gates + revisions）"))
    else:
        project = data.get("project")
        if project is not None and not isinstance(project, dict):
            violations.append(v("EMPTY_FIELD", show + " project", "project 不是映射"))
        if data.get("revisions") is not None \
                and not isinstance(data.get("revisions"), list):
            violations.append(v("EMPTY_FIELD", show + " revisions",
                                "revisions 不是列表"))
        raw = data.get("gates")
        if raw is None:
            violations.append(v("EMPTY_FIELD", show + " gates",
                                "gates 缺失（集合形态；无记录写空列表）"))
        elif not isinstance(raw, list):
            violations.append(v("EMPTY_FIELD", show + " gates", "gates 不是列表"))
        else:
            records = raw
            stories, stories_err = load_yaml_safe(os.path.join(out, STORIES_FILE))
            plan, plan_err = load_yaml_safe(os.path.join(out, PLAN_FILE))
            if stories_err is not None or plan_err is not None:
                warnings.append(v("UNPARSABLE_YAML", STORIES_FILE,
                                  "上游产物不可解析：引用解析降级跳过"))
            if stories is None:
                warnings.append(v("MISSING_FILE", STORIES_FILE,
                                  "stories.yaml 缺席：AC / S 引用解析降级跳过"))
            if plan is None:
                warnings.append(v("MISSING_FILE", PLAN_FILE,
                                  "test-plan.yaml 缺席：TC 引用解析降级跳过"))
            _by_ac, tc_map = tc_index(plan or {})
            ctx = {
                "stories": {str(story.get("id") or "")
                            for story in items_of(stories or {}, "stories")
                            if isinstance(story, dict)},
                "acs": {str(ac.get("id") or "") for _story, ac in
                        ac_index(stories or {}) if nonempty(ac.get("id"))},
                "tcs": set(tc_map), "tc_map": tc_map,
                "mutation": mutation_block(out, warnings),
            }
            seen = set()
            for i, record in enumerate(records):
                check_record(i, record, args.final, show, ctx, violations,
                             warnings)
                if isinstance(record, dict) and nonempty(record.get("id")):
                    rid = str(record["id"])
                    if rid in seen:
                        violations.append(v("DUPLICATE_ID",
                                            "%s.gates[%d].id" % (show, i),
                                            "记录 ID %s 重复（TG ID 稳定不重用）"
                                            % rid))
                    seen.add(rid)
            if args.final and not records:
                violations.append(v("EMPTY_FIELD", show + " gates",
                                    "--final 要求至少 1 条记录"))
    gate_rows = [r for r in records if isinstance(r, dict)]
    counts = {
        "gates": len(records),
        "by_status": count_by(gate_rows, "status"),
        "by_decision": count_by(
            [{"decision": (r.get("gate") or {}).get("decision")}
             for r in gate_rows], "decision"),
        "items": sum(len((r.get("coverage") or {}).get("items") or [])
                     for r in gate_rows),
        "blockers": sum(len((r.get("gate") or {}).get("blockers") or [])
                        for r in gate_rows),
        "waivers": sum(len((r.get("gate") or {}).get("waivers") or [])
                       for r in gate_rows),
    }
    ok = not violations
    payload = {
        "ok": ok, "command": "check", "project_root": args.project_root,
        "output_dir": os.path.normpath(out).replace("\\", "/"),
        "final": args.final, "violations": violations, "warnings": warnings,
        "counts": counts,
    }
    emit_via(payload, args.json, human_check)
    return 0 if ok else 1


def human_check(payload):
    if payload["ok"]:
        print("PASS：%s 校验通过（gates=%d）"
              % (payload["output_dir"] + "/" + GATE_FILE,
                 payload["counts"]["gates"]))
        return
    print("FAIL：")
    for item in payload["violations"]:
        print("- %s %s: %s" % (item["code"], item["where"], item["msg"]))
