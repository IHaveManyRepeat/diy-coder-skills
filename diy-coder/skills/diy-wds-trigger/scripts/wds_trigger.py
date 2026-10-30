# -*- coding: utf-8 -*-
"""diy-wds-trigger 确定性引擎：产物列举（list）/ 整份或单条详情（show）/ 顶层骨架铸造（init）
/ wds-trigger.yaml 校验（check [--final]）/ 计数体检（metrics）。

机制：本技能是 **WDS 线的第二环**——把业务目标映射到用户心理
（Effect Mapping，方法出处 Balic & Domingues / inUse）。产物 `{output_dir}/wds-trigger.yaml`
是**单记录多段**的内容型产物：`business_goals[]` / `personas[]`（内嵌驱动因素）/
`driver_patterns` / `priority` / `feature_impact[]` / `effect_map`，各段由会话（LLM）逐步编辑
写回；本引擎只做确定性的两件事：**铸造顶层骨架**与**机械校验**。分工写死：
`project.name` / `created` 与 `mode` / `entry` 由 `init` 铸造后不再由 LLM 改；五个子命令里
**只有 `init` 写盘**。

单记录形态的直接后果：两值口径**直接适用**——顶层
`project.status: 草稿|已定稿`。`list` 至多回一条；`show` 不带 `--id` 时整份全文返回、
带 `--id` 时按键寻址单条记录。

  list     列产物摘要——只回 `name` / `status` / `stage` / `mode` / `entry` / `goals` /
           `personas` / `updated` 八字段（续接锚点是 `stage`）。产物缺席是新项目常态 →
           空列表 + `ok: true`，不报错；产物损坏 → 结构化违规。`--status S` 过滤顶层
           `project.status`（非法值 `ENUM_INVALID`）。

  show     整份全文（`document` 键）。`--id TG-<n>` → 该人物记录（`record` 键）；
           不存在 → `UNKNOWN_ID`。产物缺席 → `MISSING_FILE`。

  init     铸顶层骨架（`--mode` 必填）：`project.status: 草稿` + `stage: 模式` +
           `business_goals` 的**首条记录**（`BG-1` 愿景节点空位）+ 其余五段空位 +
           `revisions: []`。**跨技能门禁（§2.3.1 冻结）**：须先有 `{output_dir}/wds-brief.yaml`
           且其 `project.status: 已定稿`，否则**零写入**（缺席 → `MISSING_FILE`；未定稿 →
           `STATUS_MISMATCH`）——缺失时提示**路由到 `diy-wds-brief`**。
           **已有合法产物 → 不覆盖**（只刷 `project.updated` + warning）；`--mode` 与产物
           不符 → `SET_MISMATCH` 且**零写入**（模式决定整条管线的参与方式，不得被静默改写）；
           产物损坏 → `UNPARSABLE_YAML` 拒绝且零写入。

  check    schema / 枚举 / 必填键（下表）/ `status` 与 `stage` 同档 / ID 形态与唯一性与
           引用可解析 / 评分重算 / 构图纪律逐条。`--final` 附加：`project.status: 已定稿` +
           `stage: 收尾` + 上游简报仍在场且已定稿 + 各段按下列键表齐备 + 零 `[假设]`。
           exit 0 唯一放行。

  metrics  人物/驱动因素**机械体检**（不阻断）：人物群 2–4、每人
           3–5 正 + 3–5 负、Effect Map 连接数 = 目标数 + 2×人物数；越界 → **warning**
           （exit 0）。`--id TG-<n>` 只窄化「每人驱动因素」那一族（群数与连接数是文档级，
           恒核）；不存在 → `UNKNOWN_ID`。

必填键表（`check --final`）：
- `project`: name / created / updated / status（`草稿|已定稿`）
- `stage` ∈ 模式/目标/驱动/优先级/特征/成品/收尾（**续接锚点**；`已定稿` ⟺ `收尾`）
- `mode` ∈ W/S/D（硬规则：模式由用户显式选择，禁止代选）；`entry` ∈ 工作坊/既有产物
- `business_goals[]`: **恰 1 条 `kind: 愿景` 且为首条**（Effect Map 的 `BG0` 节点）+
  **3–5 条 `kind: 目标`**；每条 id（`BG-<n>`）+ statement 非空；目标条目另需 metric /
  target / timeline 三键
- `personas[]` **2–4 条**：id（`TG-<n>`）/ name / role / priority（主|其他，
  **恰一条「主」**）/ summary / context / goals / frustrations / current_behavior；
  `priority: 主` 者另需 `transformation.{before, after}`
- `personas[].driving_forces`（**嵌在人物内，不设顶层并列段**）：
  `positive[]` **3–5 条**（每条 id `DF-<n>.<m>+` / statement / why / **promise**）+
  `negative[]` **3–5 条**（每条 id `DF-<n>.<m>-` / statement / why / **answer**）
- `driver_patterns`: shared / unique / tensions 三键（共/独/张力）；
  shared 与 unique 非空，tensions 可空；引用的驱动因素 ID 必须可解析
- `priority`: ranked_personas（覆盖全部人物恰一次，每条带 why）/ ranked_drivers（非空，带 why）/
  focus_statement.{top_group（= 排名第一的人物）, must（非空）, should, could}
- `feature_impact[]`: 每条 id（`FI-<n>`）/ name / scores.{primary, others[]} / score /
  decision（必须|应该|可选）/ rationale；score 与评分表重算一致
  （主人物 高=5/中=3/低=1；其他人物 高=3/中=1/低=0），decision 与 Must-Have 判据一致
  （必须 ⟺ 主人物命中「高」或 score ≥ max−3，max = 5 + 3×(人物数−1)）
- `effect_map`: derived_from / format / direction / config / nodes / connections /
  class_defs（**恰 4 条逐字**）/ diagram；nodes 与 business_goals / personas 一一对应；
  connections **恰为** BG→PLATFORM ∪ PLATFORM→TG ∪ TG→DF（配对严格）
- `revisions`: 列表（无修订写空列表）

跨技能读契约：本技能是 **WDS 线第二环**——入口门禁 = 上游
`{output_dir}/wds-brief.yaml` 的 `project.status: 已定稿`（读 `brief.core` / `brief.content` /
`brief.visual` / `brief.platform` 四组键）；下游 `diy-wds-scenarios` 读本产物的
`business_goals[]` / `personas[]`（`TG-<n>` + 其驱动因素） / `priority`，门禁 = 本产物的
`project.status: 已定稿`。**驱动因素数组按优先级降序排列，前 3 条即下游读取的 Top 3**。

违规码（复用冻结集 + 已批码，**零新增码**；两处语义复用在此登记）：
① `SET_MISMATCH` 承载「`init` 的 `--mode` 与既有产物不符」「`feature_impact[].score` 与评分表
重算不符」「`scores.others` 条数与人物数不匹配」「驱动因素 ID 的序号与所属人物不符」——
最近义项是「取值/形状与来源不匹配」；② `STATUS_MISMATCH` 承载「`project.status` 与 `stage`
不同档」「上游简报未定稿」「`feature_impact[].decision` 与 Must-Have 判据不符（含主人物高影响
却被判「可选」）」「`project.status: 已定稿` 而骨架段仍空」——最近义项是「状态/结论不自洽」。

`--previous` 判 **no**：本产物是**单记录多段**，段与记录只增不减（重跑即就地补段，
不收缩集合）——不存在「旧有新无」的 ID 集合可比对；改既有内容往 `revisions` 追加。

契约：exit 0 唯一放行 / 1 = 违规或被拒绝 /
2 = 用法错误（argparse 默认）/ 无 exit 3；`--json` → 单行回执（`ensure_ascii=False`），
无 `--json` → 中文人读行（每违规一行 `CODE where: msg` + 汇总行）；回执共同键
`{ok, command, project_root, output_dir, instance, violations, warnings, counts}`
（`instance` 恒 `null` 但**键在位**，`warnings` 与 `violations` 同形），`where` 正斜杠、
相对 project-root；**写盘命令（`init`）回执另含 `updated`**，只读子命令不含。
`--project-root`（默认 `.`）全部子命令都收；`--output-dir` **写盘子命令必填**（不设默认、
**不得**私读 `diy-coder.yaml` 当默认），只读子命令可省（省了则回执为 `null`，需读产物的
子命令明确报缺而不静默按空处理）。**`--instance` 一律不做**：实例由 SKILL.md 委托
`diyc.py resolve` 解析后以 `--output-dir` 形式传入，签名表内不出现它。
写回纪律：全文 load → 就地改 → `yaml.safe_dump(allow_unicode=True, sort_keys=False,
default_flow_style=False)` → 同目录临时文件 + `os.replace`（注释不保留；复用
`diyc_lib.save_yaml_atomic` 的同款实现——不另造一份语义不同的）。

★ **红线**：本技能的终门是**本引擎的 `check --final`**。**不得**教模型调用
`diyc.py check --type <WDS 型> --previous`——`diyc.py` 的 `CHECK_TYPES` 是 8 型封闭集，
WDS 型不在其中（`test_suite_texts.py` 有守卫会直接判红）。
"""
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

from wds_trigger_checks_base import (
    CLASS_DEFS, DECISION_ENUM, DRIVER_RANGE, ENTRY_ENUM, GOAL_KIND_ENUM,
    GOAL_RANGE, MODE_ENUM, PATTERN_KEYS, PERSONA_KEYS, PERSONA_RANGE,
    PRODUCT_FILE, STAGE_ENUM, STATUS_ENUM, TOP_KEYS, as_dict, as_list,
    blank_document, brief_summary, emit, out_dir_or_violation, read_document,
    upstream_gate)
from wds_trigger_checks_final import check_document, cmd_metrics



# ---------------------------------------------------------------- list / show

def cmd_list(args):
    payload = receipt_base("list", args, args.output_dir)
    out, missing = out_dir_or_violation(args, "list")
    if missing is not None:
        payload["violations"] = [missing]
        return emit(payload, args.json)
    root = os.path.abspath(args.project_root)
    path = os.path.join(out, PRODUCT_FILE)
    show = display_path(path, root)
    status = str(args.status).strip() if nonempty(args.status) else None
    violations = []
    if status is not None and status not in STATUS_ENUM:
        violations.append(v("ENUM_INVALID", "list --status",
                            "status 越界：%s（合法集 %s）" % (status, "|".join(STATUS_ENUM))))
    data, err = read_document(path)
    warnings = []
    if err is not None:
        violations.append(v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err))
    elif data is None:
        warnings.append(v("MISSING_FILE", show,
                          "%s 尚未建立（先跑 init 铸骨架）——按空列表处理" % PRODUCT_FILE))
    records = []
    if not violations and data is not None:
        item = brief_summary(data)
        if status is None or str(item.get("status") or "").strip() == status:
            records.append(item)
    payload["violations"] = violations
    payload["warnings"] = warnings
    payload["ok"] = not violations
    payload["records"] = records
    payload["counts"] = {"records": len(records),
                         "by_status": {r["status"]: 1 for r in records if nonempty(r["status"])}}
    body = ["- %s ｜ %s ｜ %s ｜ %s ｜ 目标 %s ｜ 人物 %s ｜ %s"
            % (r["name"], r["status"], r["stage"], r["mode"], r["goals"], r["personas"],
               r["updated"]) for r in records]
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
    path = os.path.join(out, PRODUCT_FILE)
    show = display_path(path, root)
    data, err = read_document(path)
    violations = []
    if err is not None:
        violations.append(v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err))
    elif data is None:
        violations.append(v("MISSING_FILE", show, "产物不存在（先跑 init 铸骨架）"))
    record = None
    wanted = str(args.id).strip() if nonempty(args.id) else None
    if not violations and wanted is not None:
        record = next((x for x in as_list(data.get("personas"))
                       if isinstance(x, dict) and str(x.get("id") or "").strip() == wanted),
                      None)
        if record is None:
            violations.append(v("UNKNOWN_ID", show + ".personas",
                                "找不到记录 %s（本技能记录 ID 取 TG-<n>）" % wanted))
    payload["violations"] = violations
    payload["ok"] = not violations
    payload["document"] = data if not violations and wanted is None else None
    payload["record"] = record
    payload["counts"] = {"records": 1 if not violations else 0}
    summary = None
    if not violations:
        item = brief_summary(data)
        summary = ("PASS：%s（%s / stage: %s / %s）"
                   % (show, item["status"], item["stage"], item["mode"])
                   if wanted is None else "PASS：%s 的 %s" % (show, wanted))
    return emit(payload, args.json, summary)


# ---------------------------------------------------------------- init


def cmd_init(args):
    payload = receipt_base("init", args, args.output_dir)
    out = os.path.abspath(args.output_dir)
    root = os.path.abspath(args.project_root)
    path = os.path.join(out, PRODUCT_FILE)
    show = display_path(path, root)
    violations = []
    mode = str(args.mode).strip() if args.mode is not None else ""
    if not nonempty(mode):
        violations.append(v("EMPTY_FIELD", "init --mode",
                            "模式未选：硬规则——模式必须由用户显式选择（W 工作坊 / "
                            "S 建议降级 / D 代做降级），不得代选"))
    else:
        enum_check(mode, MODE_ENUM, "init --mode", "mode", violations)
    entry = str(args.entry).strip() if nonempty(args.entry) else ENTRY_ENUM[0]
    enum_check(entry, ENTRY_ENUM, "init --entry", "entry", violations)
    if violations:
        payload["violations"] = violations
        return emit(payload, args.json)
    # 跨技能门禁（§2.3.1）：上游简报必须在场且已定稿——不满足则零写入
    gate = upstream_gate(out, root)
    if gate:
        payload["violations"] = gate
        return emit(payload, args.json)
    stamp = now()
    data, err = read_document(path)
    if err is not None:
        payload["violations"] = [v("UNPARSABLE_YAML", show,
                                   "%s（拒绝且零写入——修好或另行归档后再 init）" % err)]
        return emit(payload, args.json)
    if data is None:
        doc, warnings = blank_document(root, stamp, mode, entry)
        payload["warnings"] = warnings
    else:
        # 已有骨架：**不覆盖**。模式决定整条管线的参与方式——改判走 revisions + 重跑。
        stored = str(data.get("mode") or "").strip()
        if nonempty(stored) and stored != mode:
            payload["violations"] = [v("SET_MISMATCH", "%s.mode" % show,
                                       "既有产物记录的是 %s，--mode 给的是 %s——不覆盖"
                                       "（模式决定参与方式；要改走 revisions 并经用户确认后"
                                       "再手工改，不改判则按既有值继续）" % (stored, mode))]
            return emit(payload, args.json)
        doc = data
        project = as_dict(doc.get("project"))
        warnings = []
        name = project.get("name")
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
        doc.setdefault("stage", STAGE_ENUM[0])
        doc.setdefault("mode", mode)
        doc.setdefault("entry", entry)
        doc.setdefault("business_goals",
                       [{"id": "BG-1", "kind": GOAL_KIND_ENUM[0]}])
        doc.setdefault("personas", [])
        doc.setdefault("driver_patterns", {key: [] for key in PATTERN_KEYS})
        doc.setdefault("priority", {})
        doc.setdefault("feature_impact", [])
        doc.setdefault("effect_map", {})
        doc.setdefault("revisions", [])
        warnings.append(v("SET_MISMATCH", show,
                          "产物已存在骨架——本次 init 未覆盖任何内容，只刷 project.updated；"
                          "续接请按 stage 定位"))
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
    payload["counts"] = {"records": 1, "stage": doc.get("stage")}
    return emit(payload, args.json,
                "PASS：已建 %s 骨架（%s / status: 草稿 / stage: 模式）" % (show, mode))


# ---------------------------------------------------------------- check / metrics

def cmd_check(args):
    payload = receipt_base("check", args, args.output_dir)
    out, missing = out_dir_or_violation(args, "check")
    if missing is not None:
        payload["violations"] = [missing]
        return emit(payload, args.json)
    root = os.path.abspath(args.project_root)
    path = os.path.join(out, PRODUCT_FILE)
    show = display_path(path, root)
    data, err = read_document(path)
    if err is not None:
        payload["violations"] = [v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err)]
        return emit(payload, args.json)
    if data is None:
        payload["violations"] = [v("MISSING_FILE", show,
                                   "%s 不存在（先跑 init 铸骨架）" % PRODUCT_FILE)]
        return emit(payload, args.json)
    violations, warnings, counts = check_document(data, show, args)
    if args.final:
        # 定稿时复验跨技能门禁：上游简报须仍在场且已定稿（§2.3.1）
        violations = upstream_gate(out, root) + violations
    payload["violations"] = violations
    payload["warnings"] = warnings
    payload["ok"] = not violations
    payload["final"] = bool(args.final)
    payload["counts"] = counts
    return emit(payload, args.json,
                "PASS：%s 校验通过（%s；目标 %d / 人物 %d / 特征 %d）"
                % (show, "已定稿" if args.final else "草稿可用",
                   counts["goals"], counts["personas"], counts["features"]))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(
        description="diy-wds-trigger 确定性引擎：产物列举（list）/ 详情（show）/ 骨架铸造"
                    "（init）/ wds-trigger.yaml 校验（check）/ 计数体检（metrics）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(parser, output_required=False):
        parser.add_argument("--project-root", default=".",
                            help="项目根（默认 .）")
        parser.add_argument("--output-dir", required=output_required, default=None,
                            help="产物目录（写盘子命令必填；只读子命令可省，取值由 "
                                 "`diyc.py resolve` 回执给）")
        parser.add_argument("--json", action="store_true", help="输出单行 JSON 回执")

    ls = sub.add_parser("list", help="列产物摘要（只回 name/status/stage/mode/entry/goals/"
                                     "personas/updated）")
    common(ls)
    ls.add_argument("--status", default=None, help="按 project.status 过滤（草稿|已定稿）")
    ls.set_defaults(func=cmd_list)

    sh = sub.add_parser("show", help="整份全文；--id TG-<n> 取单个人物记录")
    common(sh)
    sh.add_argument("--id", default=None, help="记录 ID（TG-<n>）；不存在 → UNKNOWN_ID")
    sh.set_defaults(func=cmd_show)

    ini = sub.add_parser("init", help="铸顶层骨架（--mode 必填；上游简报须已定稿）")
    common(ini, output_required=True)
    ini.add_argument("--mode", required=True,
                     help="参与模式（必填：W|S|D；空值 → EMPTY_FIELD 零产出，"
                          "禁止代选）")
    ini.add_argument("--entry", default=None,
                     help="入口（工作坊|既有产物，默认 工作坊）")
    ini.set_defaults(func=cmd_init)

    ck = sub.add_parser("check", help="校验 wds-trigger.yaml（schema/枚举/必填键/ID/评分/构图；"
                                      "--final 附加定稿义务）")
    common(ck)
    ck.add_argument("--final", action="store_true",
                    help="定稿校验：status: 已定稿 + stage: 收尾 + 上游已定稿 + 各段齐备 + "
                         "零 [假设]")
    ck.set_defaults(func=cmd_check)

    mt = sub.add_parser("metrics", help="计数体检（人物群 2–4 / 每人 3–5 正 + 3–5 负 / "
                                        "连接数 = 目标数 + 2×人物数；越界只给 warning）")
    common(mt)
    mt.add_argument("--id", default=None, help="窄化到单个人物（TG-<n>）")
    mt.set_defaults(func=cmd_metrics)

    args = ap.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
