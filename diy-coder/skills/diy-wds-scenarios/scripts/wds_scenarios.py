# -*- coding: utf-8 -*-
"""diy-wds-scenarios 确定性引擎：产物列举（list）/ 单条或整份详情（show）/ 骨架铸造（init）
/ wds-scenarios.yaml 校验（check [--final]，含**页面覆盖矩阵**的机械核对）。

机制：本技能是 **WDS 链的第三环**（源 `wds-3-scenarios`：把触发图翻成场景大纲与页面树）。
产物 `{output_dir}/wds-scenarios.yaml` 是**内容型产物**——`scope` / `page_inventory[]` /
`scenarios[].pages[]` 由会话（LLM）逐步编辑写回，本引擎只做确定性的两件事：**铸造骨架**
与**机械校验**（含覆盖矩阵）。四个子命令里**只有 `init` 写盘**。

**裁定 12 的落地（本引擎最要紧的一条）**：源侧 step-05 会为每个场景建目录树
（`C-UX-Scenarios/[NN-slug]/`）+ 每个页面建文件夹与样板 md + `Sketches/` 空目录。
diy 侧**只产本 YAML**：逐场景写 `scenarios[]` 记录、其下写 `pages[]` 记录——**不建任何目录树、
不建 `Sketches/`**（那是 C·3 `diy-design` 的产物位）。故 `check` 的页面类判据全部落在
**记录与引用**上，不落在文件系统上。

**裁定 8 的 ID 体系（机械核对）**：场景 `SC-<nn>`（两位数、顺序递增、不重编不复用）；
页面 `SC-<nn>.P<n>`（**废止独立的 `P-*` 前缀**）；人物 `TG-<n>`（引用上游，不复制内容）。
页面 `slug` 保留源侧 `NN.<p>-<page-slug>` 形态作**展示名**，但它必须与 ID **同源**——
这一条由 `check` 机械核对（展示名与引用键漂移是本设计最可能的坏味道）。

**裁定 17 的交接契约（必携三键）**：每条记录含 `design_intent`（`[K|C|S|D|L]`）+
`design_status`（初值 `not-started`；本技能**只设初值**，后续推进归 `diy-design` 的 WDS 线分支，
故 `--final` 要求它**恰为初值**）+ `trigger_map_context`（`target_group: TG-<n>` +
`drivers[]`：所消费的驱动因素 ID，形态取上游实值 `DF-<人物号>.<条号>+|-`，
见 `diy-wds-trigger/SKILL.md` 结构段 + `business_goal: BG-<n>`）。
**所消费的驱动必须属本记录的人物群**——引擎从驱动 ID 里认出人物号并与 `target_group` 比对，
跨群引用判 `SET_MISMATCH`（这条替代了源侧「人工看有没有抄错群」）。

**三条骨律的机械落点**（源 step-05）：
① **阳光路径零分支** —— 结构保证：`pages[]` 是有序列表、页号连续、无分支键；
② **场景名必须含人物名** —— 上游 `wds-trigger.yaml` 可解析时逐条核对（解不出则降级 warning，
   不猜、不判红）；
③ **每页恰属一条战略链** —— **页面覆盖矩阵**：每条 `page_inventory[]` 的页在全部
   `scenarios[].pages[]` 里**恰出现一次**；漏配 / 重复分配 / 清单外的页各判一条。

  list    列场景摘要——只回六字段（对照源 `00-ux-scenarios.md` 摘要表列：
          `id` / `name` / `persona` / `pages` / `priority` / `status`），**不读正文**。
          `persona` 列 = 记录的 `trigger_map_context.target_group`（单一源，不复制人物名）。
          产物缺席是新项目常态 → 空列表 + `ok: true`；`--status` 按记录级 `status` 过滤。

  show    整份全文 + 覆盖矩阵（无 `--id`）；`--id SC-<nn>` 回该场景记录，
          `--id SC-<nn>.P<n>` 回该页面记录（§2.3 登记的两级记录 ID）；不存在 → `UNKNOWN_ID`。

  init    铸骨架：`project.status: 草稿` + `scope`（`--site-type` 必填）+ `page_inventory: []`
          + **首条记录骨架**（`SC-01`，只带 `id` / 留空 `name` / `status: 草稿`）
          + `revisions: []`。**上游门禁**（§2.3.1）：读 `{output_dir}/wds-trigger.yaml`，缺失
          → `MISSING_FILE` 且**零写入**（路由 `diy-wds-trigger`）；`project.status ≠ 已定稿`
          → `STATUS_MISMATCH` 且零写入。已有合法产物 → **不覆盖**（只刷 `project.updated`
          + warning）；产物损坏 → `UNPARSABLE_YAML` 拒绝且零写入。
          ── 记录级 ID 的铸号：`init` 铸 `SC-01`，其后各条由会话按 `SC-<nn>` 规则**顺序追加**；
          `check` 判唯一（`DUPLICATE_ID`）与连续（跳号 / 重编 → `SET_MISMATCH`）。

  check   schema / 枚举 / 必填键（下表）/ ID 链 / 覆盖矩阵 / 令牌 / `[假设]`。`--final` 附加：
          `project.status: 已定稿` + 全部记录 `status: 已大纲` + 各记录键表齐备 + 覆盖 100%
          + `design_status` 为初值。exit 0 唯一放行。

必填键表（`check --final`；草稿期只核结构与枚举）：
- `project`: name / created / updated / status
- `scope`: site_type / scale / scenario_format / page_strategy（`approach` 选填）
- `page_inventory`: 列表（每条 `name` / `purpose`；`name` 是覆盖矩阵的连接键，须唯一）
- `scenarios[]`（每条）：id / name / priority / status / **design_intent** / **design_status** /
  **trigger_map_context**(target_group / drivers / business_goal) / transaction / situation /
  driving_forces(hope / worry) / device / entry / success(user / business) / pages[]
- `scenarios[].pages[]`（每条）：id / slug / name / purpose（非末页另需 exit_action）
- `revisions`: 列表（无修订写空列表）

跨技能读契约（§2.3.1 冻结）：读 `{output_dir}/wds-trigger.yaml` 的 `business_goals[]` /
`personas[]`（`TG-<n>` + 其驱动因素）/ `priority`，门禁 = 其 `project.status: 已定稿`；
**只读不写**（上游写权 100% 归 `diy-wds-trigger`）。

违规码：复用 batch3-contract §3 冻结集——本引擎用到 `MISSING_FILE` / `UNPARSABLE_YAML` /
`DUPLICATE_ID` / `UNKNOWN_ID` / `EMPTY_FIELD` / `ENUM_INVALID` / `STATUS_MISMATCH` /
`SET_MISMATCH` / `ASSUMPTION_PRESENT` 共 9 个；`TOKEN_UNRESOLVED` 沿用 B6 的已批新增码与判定
流程（**本批不新增任何码**）。三处语义复用在此登记：① `SET_MISMATCH` 承载「ID 跳号 / 页号
不连续 / slug 与 ID 不同源 / 覆盖矩阵违规」四类（最近义项 = 「集合或取值不匹配」）；
② `ENUM_INVALID` 兼作 `list --status` 非法取值码；③ `UNKNOWN_ID` 兼作「场景里出现页清单外的
页」与「`show --id` 不存在」两用。

`--previous` 判 **no**（裁定 18）：`scenarios[]` 与 `pages[]` **只增不减**（重跑即新增记录，
不收缩集合），不存在「旧有新无」的 ID 集合可比对；改既有记录往 `revisions` 追加。

契约（承 batch3-contract §3 / 任务书 §2.2）：exit 0 唯一放行 / 1 = 违规或被拒绝 /
2 = 用法错误（argparse 默认）；`--json` → 单行回执（`ensure_ascii=False`）；无 `--json`
→ 中文人读行。回执共同键 `{ok, command, project_root, output_dir, instance, violations,
warnings, counts}`（`instance` 恒 `null` 但**键在位**，`warnings` 与 `violations` 同形），
`where` 正斜杠、相对 project-root；**写盘命令（`init`）回执另含 `updated`**，只读子命令不含。
`--project-root`（默认 `.`）全部子命令都收；`--output-dir` **写盘子命令必填**（不设默认、
**不得**私读 `diy-coder.yaml` 当默认），只读子命令可省（省了则回执为 `null`，需读产物的
子命令明确报缺而不静默按空处理）。**`--instance` 一律不做**：实例由 SKILL.md 委托
`diyc.py resolve` 解析后以 `--output-dir` 形式传入。
写回纪律：全文 load → 就地改 → `yaml.safe_dump(allow_unicode=True, sort_keys=False,
default_flow_style=False)` → 同目录临时文件 + `os.replace`（复用 `diyc_lib.save_yaml_atomic`
的同款实现——不另造一份语义不同的）。

★ **红线**：本技能的终门是**本引擎的 `check --final`**。**不得**教模型调用
`diyc.py check --type <WDS 型> --previous`——`diyc.py` 的 `CHECK_TYPES` 是 8 型封闭集，
WDS 型不在其中（`test_suite_texts.py` 有守卫会直接判红）。
"""
# trace: 迁移计划 §二 验收 #1（薄主文件 + 厚 steps）/#2（产物 schema + SC-<nn>/SC-<nn>.P<n>）
#        /#3（前置门禁：读 wds-trigger.yaml 的 project.status: 已定稿）/#4（ID 唯一性与顺序性）
#        /#6（viewer 标签缺口登记）/#8（frontmatter 六字段）/#12（领域引擎接线：b 终门 / c --previous 判 no）
import argparse
import json
import os
import re
import sys

import yaml

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import TOKEN_WHITELIST, check_tokens, display_path, enum_check, load_yaml_safe, nonempty, now, project_name, receipt_base, require, save_yaml_atomic, v, walk_strings  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wds_scenarios_checks import check_document
from wds_scenarios_lib import (
    DESIGN_INTENT_ENUM, DESIGN_STATUS_ENUM, DESIGN_STATUS_INITIAL,
    FINAL_UPSTREAM_STATUS, RECORD_STATUS_ENUM, SCALE_ENUM, SCENARIOS_FILE,
    SCENARIO_FORMAT_ENUM, SITE_TYPE_ENUM, STATUS_ENUM, TRIGGER_FILE,
    UPSTREAM_KEYS, blank_document, coverage_report, emit, find_record,
    out_dir_or_violation, read_document, scenario_summary, text_of
)


def cmd_list(args):
    payload = receipt_base("list", args, args.output_dir)
    out, missing = out_dir_or_violation(args, "list")
    if missing is not None:
        payload["violations"] = [missing]
        return emit(payload, args.json)
    root = os.path.abspath(args.project_root)
    path = os.path.join(out, SCENARIOS_FILE)
    show = display_path(path, root)
    status = text_of(args.status) or None
    violations = []
    if status is not None and status not in RECORD_STATUS_ENUM:
        violations.append(v("ENUM_INVALID", "list --status",
                            "status 越界：%s（合法集 %s）" % (status, "|".join(RECORD_STATUS_ENUM))))
    data, err = read_document(path)
    warnings = []
    if err is not None:
        violations.append(v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err))
    elif data is None:
        warnings.append(v("MISSING_FILE", show,
                          "%s 尚未建立（先跑 init 铸骨架）——按空列表处理" % SCENARIOS_FILE))
    records = []
    if not violations and data is not None:
        for record in data.get("scenarios") or []:
            if not isinstance(record, dict):
                continue
            item = scenario_summary(record)
            if status is None or text_of(item.get("status")) == status:
                records.append(item)
    payload["violations"] = violations
    payload["warnings"] = warnings
    payload["ok"] = not violations
    payload["records"] = records
    payload["counts"] = {"records": len(records),
                         "by_status": {r["status"]: sum(
                             1 for x in records if x["status"] == r["status"])
                             for r in records if nonempty(r["status"])}}
    body = ["- %s ｜ %s ｜ %s ｜ %s 页 ｜ P%s ｜ %s"
            % (r["id"], r["name"], r["persona"], r["pages"], r["priority"], r["status"])
            for r in records]
    return emit(payload, args.json,
                "PASS：%s 记录 %d 条%s" % (show, len(records),
                                          "（产物缺席，按空列表处理）" if data is None else ""),
                body)
def cmd_show(args):
    payload = receipt_base("show", args, args.output_dir)
    out, missing = out_dir_or_violation(args, "show")
    if missing is not None:
        payload["violations"] = [missing]
        return emit(payload, args.json)
    root = os.path.abspath(args.project_root)
    path = os.path.join(out, SCENARIOS_FILE)
    show = display_path(path, root)
    data, err = read_document(path)
    violations = []
    if err is not None:
        violations.append(v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err))
    elif data is None:
        violations.append(v("MISSING_FILE", show, "产物不存在（先跑 init 铸骨架）"))
    target = text_of(args.id) or None
    body = None
    if not violations and target is not None:
        body = find_record(data, target)
        if body is None:
            violations.append(v("UNKNOWN_ID", "%s %s" % (show, target),
                                "记录 ID 不存在（场景取 SC-<nn>，页面取 SC-<nn>.P<n>）"))
    payload["violations"] = violations
    payload["ok"] = not violations
    payload["document"] = (data if target is None else body) if not violations else None
    report = coverage_report(data) if not violations else None
    if report is not None:
        payload["coverage"] = report
    payload["counts"] = {"records": 1 if not violations else 0,
                         "scenarios": len([x for x in (data or {}).get("scenarios") or []
                                           if isinstance(x, dict)]) if not violations else 0,
                         "inventory": report["total"] if report else 0,
                         "assigned": report["covered"] if report else 0}
    summary = None
    if not violations:
        if target is None:
            summary = "PASS：%s（%d 条场景 ｜ 覆盖 %s）" % (show, payload["counts"]["scenarios"],
                                                          report["rate"])
        else:
            summary = "PASS：%s %s（%s）" % (show, target, text_of(body.get("name")) or "—")
    return emit(payload, args.json, summary)


# ---------------------------------------------------------------- init



def cmd_init(args):
    payload = receipt_base("init", args, args.output_dir)
    out = os.path.abspath(args.output_dir)
    root = os.path.abspath(args.project_root)
    path = os.path.join(out, SCENARIOS_FILE)
    show = display_path(path, root)
    violations = []
    site_type = text_of(args.site_type)
    if not nonempty(site_type):
        violations.append(v("EMPTY_FIELD", "init --site-type",
                            "规模分析未完成：站点类型为空（用户关卡 1 未获点头 → 零产出停止，不代拟）"))
    else:
        enum_check(site_type, SITE_TYPE_ENUM, "init --site-type", "site_type", violations)
    for value, allowed, flag, label in (
            (args.scale, SCALE_ENUM, "init --scale", "scale"),
            (args.scenario_format, SCENARIO_FORMAT_ENUM, "init --scenario-format",
             "scenario_format")):
        if nonempty(value):
            enum_check(value, allowed, flag, label, violations)
    if violations:
        payload["violations"] = violations
        return emit(payload, args.json)
    # 上游门禁（§2.3.1）：读 wds-trigger.yaml 且 project.status: 已定稿；否则零产出停止
    upstream_path = os.path.join(out, TRIGGER_FILE)
    upstream, upstream_err = load_yaml_safe(upstream_path)
    upstream_show = display_path(upstream_path, root)
    if upstream is None:
        payload["violations"] = [v(
            "MISSING_FILE", upstream_show,
            "上游产物缺失或不可解析（%s）→ 零产出停止：先跑 `diy-wds-trigger` 把触发图定稿"
            "（本技能按 project.status: 已定稿 门禁只读它的 %s）"
            % (upstream_err or "文件不存在", " / ".join(UPSTREAM_KEYS)))]
        return emit(payload, args.json)
    stored_status = text_of((upstream.get("project") or {}).get("status")) \
        if isinstance(upstream.get("project"), dict) else ""
    if stored_status != FINAL_UPSTREAM_STATUS:
        payload["violations"] = [v(
            "STATUS_MISMATCH", "%s project.status" % upstream_show,
            "上游未定稿（实为 %s，要求 %s）→ 零产出停止：回 `diy-wds-trigger` 收尾"
            % (stored_status or "空", FINAL_UPSTREAM_STATUS))]
        return emit(payload, args.json)
    stamp = now()
    data, err = read_document(path)
    if err is not None:
        payload["violations"] = [v("UNPARSABLE_YAML", show,
                                   "%s（拒绝且零写入——修好或另行归档后再 init）" % err)]
        return emit(payload, args.json)
    if data is None:
        doc, warnings = blank_document(
            root, stamp, site_type,
            text_of(args.scale) or None, text_of(args.scenario_format) or None)
        payload["warnings"] = warnings
    else:
        # 已有骨架：**不覆盖**。记录与页清单是会话逐步长出来的——重跑只刷 updated。
        doc = data
        project = doc.get("project")
        if not isinstance(project, dict):
            project = {}
        name = project.get("name")
        warnings = []
        if not nonempty(name):
            name, warning = project_name(root)
            if warning is not None:
                warnings.append(warning)
        doc["project"] = {"name": name,
                          "created": project.get("created") if nonempty(project.get("created"))
                          else stamp,
                          "updated": stamp,
                          "status": project.get("status") if nonempty(project.get("status"))
                          else STATUS_ENUM[0]}
        doc.setdefault("scope", {"site_type": site_type})
        doc.setdefault("page_inventory", [])
        doc.setdefault("scenarios", [{"id": "SC-01", "name": "",
                                      "status": RECORD_STATUS_ENUM[0]}])
        doc.setdefault("revisions", [])
        warnings.append(v("SET_MISMATCH", show,
                          "产物已存在——本次 init 未覆盖任何内容，只刷 project.updated；"
                          "续接请按记录级 status 定位（已大纲/草稿）"))
        payload["warnings"] = warnings
    try:
        if out:
            os.makedirs(out, exist_ok=True)
        save_yaml_atomic(path, doc)
    except OSError as e:
        payload["violations"] = [v("MISSING_FILE", show, "写盘失败：%s" % e)]
        return emit(payload, args.json)
    payload["ok"] = True
    payload["updated"] = stamp
    payload["counts"] = {"records": len(doc.get("scenarios") or []),
                         "inventory": len(doc.get("page_inventory") or [])}
    return emit(payload, args.json,
                "PASS：已建 %s 骨架（%s / status: 草稿 / 首条记录 SC-01 铸号）"
                % (show, site_type))
def cmd_check(args):
    payload = receipt_base("check", args, args.output_dir)
    out, missing = out_dir_or_violation(args, "check")
    if missing is not None:
        payload["violations"] = [missing]
        return emit(payload, args.json)
    root = os.path.abspath(args.project_root)
    path = os.path.join(out, SCENARIOS_FILE)
    show = display_path(path, root)
    data, err = read_document(path)
    if err is not None:
        payload["violations"] = [v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err)]
        return emit(payload, args.json)
    if data is None:
        payload["violations"] = [v("MISSING_FILE", show,
                                   "%s 不存在（先跑 init 铸骨架）" % SCENARIOS_FILE)]
        return emit(payload, args.json)
    violations, warnings, counts, report = check_document(data, show, args, out)
    payload["violations"] = violations
    payload["warnings"] = warnings
    payload["ok"] = not violations
    payload["final"] = bool(args.final)
    payload["coverage"] = report
    payload["counts"] = counts
    return emit(payload, args.json,
                "PASS：%s 校验通过（%s；%d 条场景 ｜ 覆盖 %s）"
                % (show, "已定稿" if args.final else "草稿可用",
                   counts["records"], counts["coverage"]))


# ---------------------------------------------------------------- CLI

def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(
        description="diy-wds-scenarios 确定性引擎：产物列举（list）/ 单条或整份详情（show）/ "
                    "骨架铸造（init）/ wds-scenarios.yaml 校验（check，含页面覆盖矩阵）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(parser, output_required=False):
        parser.add_argument("--project-root", default=".",
                            help="项目根（默认 .）")
        parser.add_argument("--output-dir", required=output_required, default=None,
                            help="产物目录（写盘子命令必填；只读子命令可省，取值由 "
                                 "`diyc.py resolve` 回执给）")
        parser.add_argument("--json", action="store_true", help="输出单行 JSON 回执")

    ls = sub.add_parser("list", help="列场景摘要（只回 id/name/persona/pages/priority/status）")
    common(ls)
    ls.add_argument("--status", default=None, help="按记录级 status 过滤（草稿|已大纲）")
    ls.set_defaults(func=cmd_list)

    sh = sub.add_parser("show", help="整份全文 + 覆盖矩阵（--id 取 SC-<nn> / SC-<nn>.P<n>）")
    common(sh)
    sh.add_argument("--id", default=None, help="记录 ID（场景 SC-<nn> 或页面 SC-<nn>.P<n>）")
    sh.set_defaults(func=cmd_show)

    ini = sub.add_parser("init", help="铸骨架（--site-type 必填；上游须已定稿；不覆盖已有产物）")
    common(ini, output_required=True)
    ini.add_argument("--site-type", required=True,
                     help="站点类型（必填：presentation|dynamic|mixed；空值 → EMPTY_FIELD 零产出）")
    ini.add_argument("--scale", default=None, help="规模带（small|medium|large）")
    ini.add_argument("--scenario-format", default=None, dest="scenario_format",
                     help="场景格式（screen-flow|storyboard|mixed）")
    ini.set_defaults(func=cmd_init)

    ck = sub.add_parser("check", help="校验 wds-scenarios.yaml（schema/ID 链/覆盖矩阵/令牌；"
                                      "--final 附加定稿义务）")
    common(ck)
    ck.add_argument("--final", action="store_true",
                    help="定稿校验：status: 已定稿 + 全部记录已大纲 + 键表齐备 + 覆盖 100% + 零 [假设]")
    ck.set_defaults(func=cmd_check)

    args = ap.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
