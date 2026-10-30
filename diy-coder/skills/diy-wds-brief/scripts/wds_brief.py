# -*- coding: utf-8 -*-
"""diy-wds-brief 确定性引擎：产物列举（list）/ 整份详情（show）/ 顶层骨架铸造（init）
/ wds-brief.yaml 校验（check [--final]）。

机制：本技能是 **WDS 线的入口**（三源合一：wds-0-project-setup 分诊 + wds-0-alignment-signoff
对齐签核 + wds-1-project-brief 战略简报）。产物 `{output_dir}/wds-brief.yaml` 是**单记录、
多段**的内容型产物——各段由会话（LLM）逐步编辑写回，本引擎只做确定性的两件事：**铸造顶层
骨架**与**机械校验**。分工写死：`project.name` / `created` 与 `intake` 的分诊
结论由 `init` 铸造后不再由 LLM 改；四个子命令里**只有 `init` 写盘**，`check` 只校验不写。

单记录形态的两个直接后果：
① **无记录级 ID**（不是 B6 那种「一个文件装 N 条记录」的集合）→ 母本 §8 的两值口径
   **直接适用**：顶层 `project.status: 草稿|已定稿`，零偏离；取数工具里的「ID 铸号递增」
   用例对本技能**不适用**，代之以「重复 `init` 不覆盖已有骨架」。
② `list` 至多回一条；`show` 不带 `--id`（无记录级 ID 可寻址），整份全文返回。

  list    列本产物摘要——只回 `name` / `status` / `stage` / `project_type` / `updated`
          五字段（续接锚点是 `stage`）。产物缺席是新项目常态 → 空列表 + `ok: true`，
          不报错；产物损坏 → 结构化违规。`--status S` 按 `S` 过滤顶层 `project.status`。

  show    整份全文返回（`document` 键）。产物缺席 → `MISSING_FILE`。

  init    铸顶层骨架（`--project-type` 必填）：`project.status: 草稿` + `intake` 分诊结论 +
          `client_profile` 四域空位 + `brief` 四段空位 + `alignment` / `signoff` 段骨架 +
          `revisions: []`。**已有合法产物 → 不覆盖**（只刷 `project.updated` + warning）；
          `--project-type` 与产物不符 → `SET_MISMATCH` 且**零写入**（分诊结论是整条 WDS 链
          路由的根，不得被静默改写；要改走 `revisions`）；产物损坏 → `UNPARSABLE_YAML`
          拒绝且零写入，绝不覆盖。

  check   schema / 枚举 / 必填键（下表）/ `status` 与 `stage` 同档 / 对齐十节 / 签核三型
          分列 / 未解析 `{...}` 令牌。`--final` 附加：`project.status: 已定稿` +
          `intake.stage: 收尾` + 简报四段按档位齐备 + 零 `[假设]`。exit 0 唯一放行。

必填键表（`check --final`，`brief_level: complete` 档；`simplified` 档各段收窄为括号内一组）：
- `project`: name / created / updated / status
- `intake`: project_type / complexity / brief_level / strategic_analysis / stage
- `client_profile` 四域: organization / key_people / internal_drivers / collaboration
- `brief.core` 9 键: vision / positioning / business_model / **business_customers（仅
  business_model 含 `B2B` 时）** / target_users / product_concept / success_metrics /
  competitive_landscape / constraints（简化档：vision / target_users / constraints）
- `brief.content.content_language` 5 键: personality / tone / languages / seo_keywords /
  content_structure（简化档：languages）
- `brief.visual.visual_direction` 6 键: inspiration / existing_brand / references /
  design_style / layout_effects / imagery（简化档：design_style）
- `brief.platform.platform_requirements` 4 键: tech_stack / integrations /
  contact_strategy / multilingual（简化档：tech_stack）
- `alignment`（`status ≠ 不需要` 时）十节: realization / why_it_matters /
  how_we_see_it_working / paths_we_explored / recommended_solution / path_forward /
  value_we_create / cost_of_inaction / our_commitment / summary
- `signoff`（`type ≠ 不签核` 时）分型齐备：对外合同 11 节（**其中 `availability` 是条件
  节**——仅 `pricing_model: 长期聘用` 时必填，其余模式接受缺省）/ 服务协议 12 节 / 内部审批
  7 节（三张节表与条件节表见下方常量）
- `revisions`: 列表（无修订写空列表）

跨技能读契约（**本技能是链的起点**）：下游 `diy-wds-trigger` 读
`brief.core`（vision / positioning / target_users / product_concept）· `brief.content.
content_language` · `brief.visual.visual_direction`（6 维）· `brief.platform.
platform_requirements`，门禁 = 本产物的 `project.status: 已定稿`。**这四组键名是三方唯一
契约**，本引擎的必填键表与之一一对应——改键名必须同步 W2/W3。

违规码：复用冻结集——本引擎用到 `MISSING_FILE` / `UNPARSABLE_YAML` /
`EMPTY_FIELD` / `ENUM_INVALID` / `STATUS_MISMATCH` / `ASSUMPTION_PRESENT` / `SET_MISMATCH`
共 7 个；**`TOKEN_UNRESOLVED` 沿用已批新增码与判定流程**（**不新增任何码**）。
两处语义复用在此登记：① `SET_MISMATCH` 承载「`init` 的 `--project-type` 与既有产物不符」
（最近义项是「集合/取值不匹配」，与 `bmb_module` 的同码用途同族）；② `ENUM_INVALID` 兼作
`list --status` 非法取值码（同族先例同款用法）。

`--previous` 判 **no**：本产物是**单记录多段**，段只增不减（重跑即就地补段，
不收缩集合）——不存在「旧有新无」的 ID 集合可比对；改既有段往 `revisions` 追加。

契约：exit 0 唯一放行 / 1 = 违规或被拒绝 /
2 = 用法错误（argparse 默认）/ 无 exit 3；`--json` → 单行回执（`ensure_ascii=False`），
无 `--json` → 中文人读行（每违规一行 `CODE where: msg` + 汇总行）；回执共同键
`{ok, command, project_root, output_dir, instance, violations, warnings, counts}`
（`instance` 恒 `null` 但**键在位**，`warnings` 与 `violations` 同形），`where` 正斜杠、
相对 project-root；**写盘命令（`init`）回执另含 `updated`**，只读子命令不含。
`--project-root`（默认 `.`）全部子命令都收；`--output-dir` **写盘子命令必填**（不设默认、
**不得**私读 `diy-coder.yaml` 当默认），只读子命令可省（省了则回执为 `null`，需读产物的
子命令明确报缺而不静默按空处理）。**`--instance` 一律不做**：实例由 SKILL.md
委托 `diyc.py resolve` 解析后以 `--output-dir` 形式传入，签名表内不出现它。
写回纪律：全文 load → 就地改 → `yaml.safe_dump(allow_unicode=True, sort_keys=False,
default_flow_style=False)` → 同目录临时文件 + `os.replace`（注释不保留；复用
`diyc_lib.save_yaml_atomic` 的同款实现——不另造一份语义不同的）。

★ **红线**：本技能的终门是**本引擎的 `check --final`**。**不得**教模型调用
`diyc.py check --type <WDS 型> --previous`——`diyc.py` 的 `CHECK_TYPES` 是 8 型封闭集，
WDS 型不在其中（`test_suite_texts.py` 有守卫会直接判红）。
"""
#        /#3（前置门禁：入口技能 = 分诊完成）/#6（viewer 标签缺口登记）
#        /#8（frontmatter 六字段）/#12（领域引擎接线：b 终门 / c --previous 判 no / e 写权边界）
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

from wds_brief_checks import (
    BRIEF_FILE, BRIEF_KEYS, BRIEF_LEVEL_ENUM, CLIENT_PROFILE_KEYS,
    COMPLEXITY_ENUM, CONTENT_KEYS, CONTRACT_SECTIONS, CORE_REQUIRED,
    INTERNAL_SECTIONS, PLATFORM_KEYS, PROJECT_TYPE_ENUM, SERVICE_SECTIONS,
    SIGNOFF_STATUS_ENUM, SIGNOFF_TYPE_ENUM, STAGE_ENUM, STATUS_ENUM,
    STRATEGIC_ENUM, VISUAL_DIRECTION_KEYS, VISUAL_KEYS, brief_summary,
    check_document, emit, out_dir_or_violation, read_document
)



# ---------------------------------------------------------------- list / show

def cmd_list(args):
    payload = receipt_base("list", args, args.output_dir)
    out, missing = out_dir_or_violation(args, "list")
    if missing is not None:
        payload["violations"] = [missing]
        return emit(payload, args.json)
    root = os.path.abspath(args.project_root)
    path = os.path.join(out, BRIEF_FILE)
    show = display_path(path, root)
    status = str(args.status).strip() if nonempty(args.status) else None
    violations = []
    if status is not None and status not in STATUS_ENUM:
        violations.append(v("ENUM_INVALID", "list --status",
                            "status 越界：%s（合法集 %s）" % (status, "|".join(STATUS_ENUM))))
    data, err = read_document(path, show)
    warnings = []
    if err is not None:
        violations.append(v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err))
    elif data is None:
        warnings.append(v("MISSING_FILE", show,
                          "%s 尚未建立（先跑 init 铸骨架）——按空列表处理" % BRIEF_FILE))
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
    body = ["- %s ｜ %s ｜ %s ｜ %s ｜ %s"
            % (r["name"], r["status"], r["stage"], r["project_type"], r["updated"])
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
    path = os.path.join(out, BRIEF_FILE)
    show = display_path(path, root)
    data, err = read_document(path, show)
    violations = []
    if err is not None:
        violations.append(v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err))
    elif data is None:
        violations.append(v("MISSING_FILE", show, "产物不存在（先跑 init 铸骨架）"))
    payload["violations"] = violations
    payload["ok"] = not violations
    payload["document"] = data if not violations else None
    payload["counts"] = {"records": 1 if not violations else 0}
    summary = None
    if not violations:
        item = brief_summary(data)
        summary = "PASS：%s（%s / stage: %s / %s）" % (show, item["status"], item["stage"],
                                                     item["project_type"])
    return emit(payload, args.json, summary)


# ---------------------------------------------------------------- init

def blank_document(project_root, stamp, project_type, complexity, brief_level, strategic):
    """新建产物骨架：分诊结论 + 各段空位（内容型字段由会话逐步编辑）。"""
    name, warning = project_name(project_root)
    doc = {
        "project": {"name": name, "created": stamp, "updated": stamp,
                    "status": STATUS_ENUM[0]},
        "intake": {"project_type": project_type, "complexity": complexity,
                   "brief_level": brief_level, "strategic_analysis": strategic,
                   "stage": STAGE_ENUM[0]},
        "client_profile": {key: {} for key in CLIENT_PROFILE_KEYS},
        "brief": {key: {} for key in BRIEF_KEYS},
        "alignment": {"status": "未开始"},
        "signoff": {"type": SIGNOFF_TYPE_ENUM[0], "status": SIGNOFF_STATUS_ENUM[0],
                    "external_contract": {}, "service_agreement": {}, "internal": {}},
        "revisions": [],
    }
    return doc, ([warning] if warning else [])


def cmd_init(args):
    payload = receipt_base("init", args, args.output_dir)
    out = os.path.abspath(args.output_dir)
    root = os.path.abspath(args.project_root)
    path = os.path.join(out, BRIEF_FILE)
    show = display_path(path, root)
    violations = []
    project_type = str(args.project_type).strip() if args.project_type is not None else ""
    if not nonempty(project_type):
        violations.append(v("EMPTY_FIELD", "init --project-type",
                            "分诊未完成：项目类型为空（入口技能的门禁 = 分诊问答完成；"
                            "拒答则零产出停止，不代拟）"))
    else:
        enum_check(project_type, PROJECT_TYPE_ENUM, "init --project-type",
                   "project_type", violations)
    for value, allowed, flag, label in (
            (args.complexity, COMPLEXITY_ENUM, "init --complexity", "complexity"),
            (args.brief_level, BRIEF_LEVEL_ENUM, "init --brief-level", "brief_level"),
            (args.strategic_analysis, STRATEGIC_ENUM, "init --strategic-analysis",
             "strategic_analysis")):
        if value is not None and nonempty(value):
            enum_check(value, allowed, flag, label, violations)
    if violations:
        payload["violations"] = violations
        return emit(payload, args.json)
    stamp = now()
    data, err = read_document(path, show)
    if err is not None:
        payload["violations"] = [v("UNPARSABLE_YAML", show,
                                   "%s（拒绝且零写入——修好或另行归档后再 init）" % err)]
        return emit(payload, args.json)
    if data is None:
        doc, warnings = blank_document(
            root, stamp, project_type,
            str(args.complexity).strip() if nonempty(args.complexity) else COMPLEXITY_ENUM[1],
            str(args.brief_level).strip() if nonempty(args.brief_level) else BRIEF_LEVEL_ENUM[0],
            str(args.strategic_analysis).strip() if nonempty(args.strategic_analysis)
            else STRATEGIC_ENUM[0])
        payload["warnings"] = warnings
    else:
        # 已有骨架：**不覆盖**。分诊结论是整条 WDS 链路由的根——改判走 revisions + 重跑。
        stored = data.get("intake") if isinstance(data.get("intake"), dict) else {}
        existing = str(stored.get("project_type") or "").strip()
        if nonempty(existing) and existing != project_type:
            payload["violations"] = [v("SET_MISMATCH", "%s.intake.project_type" % show,
                                       "既有产物记录的是 %s，--project-type 给的是 %s——"
                                       "不覆盖（分诊结论决定整链路由；要改走 revisions 并经"
                                       "用户确认后再手工改，不改判则按既有值继续）"
                                       % (existing, project_type))]
            return emit(payload, args.json)
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
        doc.setdefault("intake", {"project_type": project_type})
        doc.setdefault("client_profile", {key: {} for key in CLIENT_PROFILE_KEYS})
        doc.setdefault("brief", {key: {} for key in BRIEF_KEYS})
        doc.setdefault("alignment", {"status": "未开始"})
        doc.setdefault("signoff", {"type": SIGNOFF_TYPE_ENUM[0],
                                   "status": SIGNOFF_STATUS_ENUM[0],
                                   "external_contract": {}, "service_agreement": {},
                                   "internal": {}})
        doc.setdefault("revisions", [])
        warnings.append(v("SET_MISMATCH", show,
                          "产物已存在骨架——本次 init 未覆盖任何内容，只刷 project.updated；"
                          "续接请按 intake.stage 定位"))
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
    payload["counts"] = {"records": 1, "stage": doc["intake"].get("stage")}
    return emit(payload, args.json,
                "PASS：已建 %s 骨架（%s / status: 草稿 / stage: 分诊）"
                % (show, project_type))


# ---------------------------------------------------------------- check



def cmd_check(args):
    payload = receipt_base("check", args, args.output_dir)
    out, missing = out_dir_or_violation(args, "check")
    if missing is not None:
        payload["violations"] = [missing]
        return emit(payload, args.json)
    root = os.path.abspath(args.project_root)
    path = os.path.join(out, BRIEF_FILE)
    show = display_path(path, root)
    data, err = read_document(path, show)
    if err is not None:
        payload["violations"] = [v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err)]
        return emit(payload, args.json)
    if data is None:
        payload["violations"] = [v("MISSING_FILE", show,
                                   "%s 不存在（先跑 init 铸骨架）" % BRIEF_FILE)]
        return emit(payload, args.json)
    violations, warnings, counts = check_document(data, show, args)
    payload["violations"] = violations
    payload["warnings"] = warnings
    payload["ok"] = not violations
    payload["final"] = bool(args.final)
    payload["counts"] = counts
    return emit(payload, args.json,
                "PASS：%s 校验通过（%s；签核三型节表 11/12/7，简报四段按 %s 档）"
                % (show, "已定稿" if args.final else "草稿可用",
                   "simplified" if str((data.get("intake") or {}).get("brief_level") or "")
                   .strip() == BRIEF_LEVEL_ENUM[1] else "complete"))


# ---------------------------------------------------------------- CLI

def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(
        description="diy-wds-brief 确定性引擎：产物列举（list）/ 整份详情（show）/ "
                    "顶层骨架铸造（init）/ wds-brief.yaml 校验（check）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(parser, output_required=False):
        parser.add_argument("--project-root", default=".",
                            help="项目根（默认 .）")
        parser.add_argument("--output-dir", required=output_required, default=None,
                            help="产物目录（写盘子命令必填；只读子命令可省，取值由 "
                                 "`diyc.py resolve` 回执给）")
        parser.add_argument("--json", action="store_true", help="输出单行 JSON 回执")

    ls = sub.add_parser("list", help="列产物摘要（只回 name/status/stage/project_type/updated）")
    common(ls)
    ls.add_argument("--status", default=None, help="按 project.status 过滤（草稿|已定稿）")
    ls.set_defaults(func=cmd_list)

    sh = sub.add_parser("show", help="整份全文（单记录产物，无记录级 ID）")
    common(sh)
    sh.set_defaults(func=cmd_show)

    ini = sub.add_parser("init", help="铸顶层骨架（--project-type 必填；已有骨架不覆盖）")
    common(ini, output_required=True)
    ini.add_argument("--project-type", required=True,
                     help="分诊结论（必填：greenfield|brownfield；空值 → EMPTY_FIELD 零产出）")
    ini.add_argument("--complexity", default=None,
                     help="产品复杂度（simple|standard|complex|complex+mobile，默认 standard）")
    ini.add_argument("--brief-level", default=None, help="简报档位（complete|simplified）")
    ini.add_argument("--strategic-analysis", default=None,
                     help="战略分析深度（full|simplified|skip）")
    ini.set_defaults(func=cmd_init)

    ck = sub.add_parser("check", help="校验 wds-brief.yaml（schema/枚举/必填键/令牌；"
                                      "--final 附加定稿义务）")
    common(ck)
    ck.add_argument("--final", action="store_true",
                    help="定稿校验：status: 已定稿 + stage: 收尾 + 简报四段齐备 + 零 [假设]")
    ck.set_defaults(func=cmd_check)

    args = ap.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
