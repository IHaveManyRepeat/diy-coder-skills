# -*- coding: utf-8 -*-
"""diy-test-review 确定性引擎：机械扫描 + 评分账本 + 三向走查 + 产物校验。

能力蓝本：测试评审（4 逻辑步；核心资产规则注册表
35 规则——本技能规则表 `criteria.yaml`：M9/M10/L9 标 disabled（私有库绑定不适用），
有效 32 行）。七条裁定全部落在此处：

  1. **评分账本全部沉到引擎**：`score` 是纯函数——LLM 只产出 findings
     （规则命中 + 位置 + 说明，**severity 不由 LLM 填**），引擎按 criteria.yaml 行值
     **复算 severity**、按 convention 行 class **降档**、按 `file:location:row` **去重**
     （文件级行 FILE_LEVEL_ROWS 以 `file` 取代行号）、算分并校验 LLM 声明不参与计分。
  2. **convention 分类归属**：`scan` 是机械可计数键的判定权威——5 个机械键
     （priority_markers / test_ids / network_first / data_factories / fixtures）直接产出
     {adopted, status}，阈值照源三行（sampled<4 → 未知；adopted==0 → 缺失；
     adopted/sampled ≥ 0.5 → 已确立，否则 新现）；`bdd_naming` / `assertion_style`
     在源文明确无机械信号 → 回执只标 `judged_by: llm`，由 LLM 读采样文件判读。
     降档由 `score` 应用（新现 → 降一档 floor LOW；缺失 / 未知 → 该行不成立）。
  3. **维度分复算**：与账本同一次调用；每维 = max(0, 100 − Σ去重后该维命中
     severity 权重 {CRITICAL:20, HIGH:10, MEDIUM:5, LOW:2})；行↔维度映射承载于
     criteria.yaml 的 `dimensions` 字段；仅展示，不进账本、不进 recommendation。
  4. **三向走查层**：`walkthrough` 执行 AC ↔ 源码 ↔ 测试三向对账，四类缺口
     （无实现 / 无测试 / 孤儿用例 / 从未运行）。**跨文档核对一律委派 diyc**：
     源码面委派 `diyc.py trace`、orphan_tc 面委派 `diyc.py check --type test-plan`；
     子进程 rc∈{0,1} 均为正常回执（1 = 上游有违规，其 violations 计入判定、不吞掉），
     rc=2 / 不可解析 / 缺席 → TOOL_MISSING / TOOL_ERROR warning 降级，不崩溃。
  5. **机械/语义分界**：`detect: mechanical|semantic` 是唯一权威；机械集初始 =
     C1/C2/C3/H1/H5/H6/H7/H8/H9/L4（可扩不可缩，扩展须回报登记），由 `scan` 直接产出。
  6. **findings.json 与 bonus**：`score --findings` 消费 LLM 产出的
     `{findings: [{file, line|null, row, class|null, note}], bonus: [{key, points, note}]}`；
     note 与额外键不参与计分；bonus 六类各 0/5、上限 30，并做与该表规则行的**矛盾复核**
     （映射承载于 criteria.yaml 的 `bonus_guard` 字段）。
  7. **与 diy-review 的边界**：本引擎只审测试代码质量并出评分账本；实现代码的
     正确性/边界/验收/设计审查归 diy-review，两者不重叠、互不调用。

V 能力补项（2026-09-18，源 test-review 对账 `v-capability-inventory.md` §1.4；
**加校验，不动评分账本**——severity 权重 / convention 降档 / bonus 六类三处零漂移）：
  R-1 recommendations 排序纪律与 Top 10 上限：排序判据
      （维度分 < 70 → HIGH）由 LLM 在 05 步照条文施加，**上限 10 由 `check` 机械拦**。
  R-2 convention **引用与实际语料独立复测**：`basis:
      convention` 的 finding 其 `class` 必须与 `convention_baseline.keys.<key>.status`
      一致（键映射 = criteria.yaml 行字段 `convention_key`）——status 为 absent/unknown
      时该行本不成立、不得成条目；引用不可核（基线缺该键）同样拒绝。`check` 面执行。
  R-3 空 / 极简测试文件处置：空（无代码内容）→ 发现面
      归 excluded(out-of-scope) **不评分**，全部为空则走无测试文件的拒绝路径；极简
      （有内容零断言）→ `scan` warning "No meaningful tests"，须按 C4 成条目；
      `check` 另有拦阻：空文件不得出现在 `scope.paths`。
  R-4 pact 附加上报（低危）：单 `it()` 内含 >1
      `addInteraction()` → `scan` warning（无 registry row，落 `recommendations` 散文）；
      配置经 `mergeConfig(` / `extends:` 组合致三条必需设置不可验证 → 合一降为 L4
      advisory（`pact-config-unverifiable`），带 `// tea:pact-ffi-safe` 标记则不报。

命令面：
  scan        [--paths P]... [--project-root R] [--output-dir D] [--json]
              测试文件发现 + 机械项检出 + convention baseline 采样（评审集之外的既有
              语料、上限 40 文件、7 key）。无测试文件 → 拒绝（exit 1，零产出）。
  score       --findings <findings.json> [--project-root R] [--output-dir D] [--json]
              账本计算（纯函数，不写文件）：severity 复算 → convention 降档 → 去重 →
              deductions / bonus → score / grade / recommendation → 维度分。
  walkthrough [--project-root R] [--output-dir D] [--json]
              三向对账（只读；跨文档核对委派 diyc）。四类缺口 + 就绪态 全覆盖|部分覆盖|已跳过。
  check       [--final] [--project-root R] [--output-dir D] [--json]
              校验 {output_dir}/test-review.yaml：schema / 枚举 / 账本自洽 / row ∈ 有效 32 行 /
              coverage_gaps 形态 / walkthrough 自洽 / **convention 引用复核（R-2）** /
              **recommendations 上限（R-1）** / **空文件不得计入评审集（R-3）**；
              --final 附加：零 [假设]、excluded 理由三值、scope 非空、记录已定稿。

引擎契约：exit 0 唯一放行；1 = 违规/被拒绝；2 = 用法错误（argparse）；
--json → 单行 JSON 回执（ensure_ascii=False），无 --json → 中文人读行。回执共同键
{ok, command, project_root, output_dir, violations:[{code, where, msg}], warnings, counts}；
--output-dir 必填、不设默认；不做 --instance / 目录推导（实例解析由 SKILL.md 委托
`diyc.py resolve`）。`--previous` **不实现**：reviews[] 是追加式台账（RV-### 稳定不重用），
无 ID 集合收缩面，与 P1/B1/B2 的"追加式产物判 no"先例一致。

违规码：复用冻结集（MISSING_FILE / UNPARSABLE_YAML / DUPLICATE_ID /
ENUM_INVALID / EMPTY_FIELD / ASSUMPTION_PRESENT / STATUS_MISMATCH / SET_MISMATCH /
PENDING_DECISION）；**新增码仅两个**——`TOOL_MISSING` / `TOOL_ERROR`（diyc 委派降级专用），无其他新码。
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import count_by, display_path, emit_via, load_yaml_safe, nonempty, v, walk_strings  # noqa: E402

from test_review_checks import (  # noqa: E402
    _check_convention_citation, _check_empty_scope_paths, _check_findings,
    _check_gaps, _check_recommendations, _check_score_block, _check_scope,
    _check_walkthrough,
)
from test_review_lib import (  # noqa: E402
    ASSUMPTION, BONUS_KEYS, CONVENTION_KEYS, CONVENTION_STATUSES, DATE_RE,
    MECHANICAL_KEYS, RECORD_STATUSES, RV_RE, TEST_REVIEW_FILE, downgrade_severity,
    load_criteria,
)
from test_review_scan import cmd_scan  # noqa: E402
from test_review_score import cmd_score  # noqa: E402
from test_review_walkthrough import cmd_walkthrough  # noqa: E402


def check_record(index, record, table, final, show, root="."):
    violations = []
    where = "%s.reviews[%d]" % (show, index)
    if not isinstance(record, dict):
        return [v("EMPTY_FIELD", where, "记录不是映射")], []
    rid = record.get("id")
    if not nonempty(rid):
        violations.append(v("EMPTY_FIELD", where + ".id", "id 缺失"))
    elif not RV_RE.fullmatch(str(rid)):
        violations.append(v("ENUM_INVALID", where + ".id",
                            "id 须为 RV-0nn（三位零填充），实为 %s" % rid))
    date = record.get("date")
    if not nonempty(date):
        violations.append(v("EMPTY_FIELD", where + ".date", "date 缺失"))
    elif not DATE_RE.fullmatch(str(date)):
        violations.append(v("ENUM_INVALID", where + ".date", "date 须为 YYYY-MM-DD"))
    status = record.get("status")
    if not nonempty(status):
        violations.append(v("EMPTY_FIELD", where + ".status", "status 缺失"))
    elif str(status) not in RECORD_STATUSES:
        violations.append(v("ENUM_INVALID", where + ".status",
                            "status 越界：%s（合法集 %s）"
                            % (status, "|".join(RECORD_STATUSES))))
    elif final and str(status) != "已定稿":
        violations.append(v("STATUS_MISMATCH", where + ".status",
                            "--final 要求 status 已定稿（实为 %s）" % status))

    violations += _check_scope(record, where, final)
    violations += _check_empty_scope_paths(record, where, root)
    finding_violations, deduped = _check_findings(record, where, table)
    violations += finding_violations
    violations += _check_convention_citation(record, where, deduped, table)
    violations += _check_score_block(record, where, deduped, table)
    violations += _check_gaps(record, where)
    violations += _check_walkthrough(record, where, record.get("coverage_gaps"))
    violations += _check_recommendations(record, where)

    baseline = record.get("convention_baseline")
    if not isinstance(baseline, dict):
        violations.append(v("EMPTY_FIELD", where + ".convention_baseline",
                            "convention_baseline 缺失或不是映射——须为映射且 keys 七键全量"
                            "（省略与「未采样」不可区分；评审集之外无语料时七键全记 unknown）"))
    else:
        keys = baseline.get("keys")
        if not isinstance(keys, dict):
            violations.append(v("EMPTY_FIELD", where + ".convention_baseline.keys",
                                "keys 缺失（7 个惯例键全量在场）"))
        else:
            missing = [k for k in CONVENTION_KEYS if k not in keys]
            if missing:
                violations.append(v("EMPTY_FIELD", where + ".convention_baseline.keys",
                                    "缺惯例键：%s（缺席与未测量不可区分）"
                                    % "、".join(missing)))
            for key in CONVENTION_KEYS:
                entry = keys.get(key)
                if not isinstance(entry, dict):
                    continue
                status = entry.get("status")
                if nonempty(status) and str(status) not in CONVENTION_STATUSES:
                    violations.append(v("ENUM_INVALID",
                                        "%s.convention_baseline.keys.%s.status" % (where, key),
                                        "status 越界：%s（合法集 %s）"
                                        % (status, "|".join(CONVENTION_STATUSES))))
            if final:
                for key in MECHANICAL_KEYS:
                    entry = keys.get(key)
                    if isinstance(entry, dict) and not isinstance(entry.get("adopted"), int):
                        violations.append(v("EMPTY_FIELD",
                                            "%s.convention_baseline.keys.%s.adopted"
                                            % (where, key),
                                            "--final 要求机械键带 adopted 计数（scan 判定）"))
    if final and any(ASSUMPTION in s for _p, s in walk_strings(record, "")):
        violations.append(v("ASSUMPTION_PRESENT", where,
                            "--final 要求零 [假设]；未决推断须落 open_questions"))
    return violations, deduped


def cmd_check(args):
    root = os.path.abspath(args.project_root)
    out = os.path.abspath(args.output_dir)
    criteria = load_criteria()
    path = os.path.join(out, TEST_REVIEW_FILE)
    show = display_path(path, root)
    violations, records = [], []
    data, err = load_yaml_safe(path)
    if data is None and err is None:
        violations.append(v("MISSING_FILE", show,
                            "%s 不存在（先完成一次 test-review 起草）" % TEST_REVIEW_FILE))
    elif err is not None:
        violations.append(v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err))
    elif not isinstance(data, dict):
        violations.append(v("EMPTY_FIELD", show, "顶层不是映射（须为 project + reviews）"))
    else:
        project = data.get("project")
        if project is not None and not isinstance(project, dict):
            violations.append(v("EMPTY_FIELD", show + " project", "project 不是映射"))
        revisions = data.get("revisions")
        if revisions is not None and not isinstance(revisions, list):
            violations.append(v("EMPTY_FIELD", show + " revisions", "revisions 不是列表"))
        raw_records = data.get("reviews")
        if raw_records is None:
            violations.append(v("EMPTY_FIELD", show + " reviews",
                                "reviews 缺失（集合形态；无记录写空列表）"))
        elif not isinstance(raw_records, list):
            violations.append(v("EMPTY_FIELD", show + " reviews", "reviews 不是列表"))
        else:
            records = raw_records
            seen = set()
            for i, record in enumerate(records):
                record_violations, _ = check_record(i, record, criteria, args.final,
                                                    show, root)
                violations += record_violations
                if isinstance(record, dict) and nonempty(record.get("id")):
                    rid = str(record["id"])
                    if rid in seen:
                        violations.append(v("DUPLICATE_ID", "%s.reviews[%d].id" % (show, i),
                                            "记录 ID %s 重复（RV ID 稳定不重用）" % rid))
                    seen.add(rid)
            if args.final and not records:
                violations.append(v("EMPTY_FIELD", show + " reviews",
                                    "--final 要求至少 1 条记录"))
    counts = {"reviews": len(records),
              "findings": sum(len(r.get("findings") or []) for r in records
                              if isinstance(r, dict)),
              "gaps": sum(len(r.get("coverage_gaps") or []) for r in records
                          if isinstance(r, dict)),
              "by_status": count_by(records, "status")}
    payload = {"ok": not violations, "command": "check", "project_root": args.project_root,
               "output_dir": os.path.normpath(out).replace("\\", "/"),
               "final": bool(args.final), "violations": violations, "warnings": [],
               "counts": counts}
    emit_via(payload, args.json, human_check)
    return 0 if payload["ok"] else 1


def human_check(payload):
    if payload["ok"]:
        print("PASS：%s 校验通过（reviews=%d，final=%s）"
              % (payload["output_dir"] + "/" + TEST_REVIEW_FILE,
                 payload["counts"]["reviews"], payload["final"]))
        return
    print("FAIL：")
    for item in payload["violations"]:
        print("- %s %s: %s" % (item["code"], item["where"], item["msg"]))


# ---------------------------------------------------------------- CLI


def build_parser():
    ap = argparse.ArgumentParser(
        description="diy-test-review 确定性引擎：机械扫描（scan）+ 评分账本（score）+ "
                    "三向走查（walkthrough，委派 diyc）+ test-review.yaml 校验（check）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("scan", help="测试文件发现 + 机械项检出 + convention baseline 采样")
    s.add_argument("--paths", action="append", default=None,
                   help="评审集路径（可重复；文件或目录。省略 = 扫 project-root）")
    s.add_argument("--project-root", default=".", help="项目根（默认 .）")
    s.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    s.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    s.set_defaults(func=cmd_scan)

    o = sub.add_parser("score", help="评分账本：severity 复算 + 降档 + 去重 + 分档 + 建议")
    o.add_argument("--findings", required=True, help="findings 载体路径（findings.json）")
    o.add_argument("--project-root", default=".", help="项目根（默认 .）")
    o.add_argument("--output-dir", required=True, help="产物目录（必填）")
    o.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    o.set_defaults(func=cmd_score)

    w = sub.add_parser("walkthrough", help="AC ↔ 源码 ↔ 测试三向对账（只读；委派 diyc）")
    w.add_argument("--project-root", default=".", help="项目根（默认 .）")
    w.add_argument("--output-dir", required=True, help="产物目录（必填）")
    w.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    w.set_defaults(func=cmd_walkthrough)

    k = sub.add_parser("check", help="校验 test-review.yaml（schema/账本自洽/走查自洽）")
    k.add_argument("--final", action="store_true",
                   help="定稿校验：status 已定稿 + zero [假设] + excluded 理由 + scope 非空")
    k.add_argument("--project-root", default=".", help="项目根（默认 .）")
    k.add_argument("--output-dir", required=True, help="产物目录（必填）")
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
