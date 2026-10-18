#!/usr/bin/env python3
"""diy-wds-assets 领域引擎（B7b / W2）。

子命令：init（唯一写盘）/ list / show / check / prompts。
- 全部子命令收 `--project-root`（默认 `.`）；`--output-dir` 缺省回落 `{project_root}/diy-output`
  （写盘子命令 `init` 必填）；只读子命令四个（list / show / check / prompts）零写盘。
- **`--instance` 一律不做**（键恒 `null` 在位）。
- 回执共同键：{ok, command, project_root, output_dir, instance, violations, warnings, counts}
  —— `warnings` 与 `violations` 同形；`init` 另含 `updated`，只读子命令不含。
  `project_root` 按 as-given 回显（不 resolve），`output_dir` 为 resolved + 正斜杠；
  违规项 schema = `{code, where, msg}`（`where` 正斜杠、路径型相对 project-root）。

★ **第五子命令 `prompts` 是对 §2.2「四子命令」的一处登记性偏离**（V3-12）：
  任务书 §3 要求「提示词导出索引」独立成面——`prompts[]` 的 `exported` 翻转与导出文件是
  本技能**照片类资产通道 + 用户可选项**（裁定 6：不接任何外部服务；其余产物由各活动直出），
  而 §2.2 冻结「四子命令」（init / list / show / check）——两条并存的最小满足 = 加一个
  **只读、零写盘**的第五子命令。
  先例：B7a 的 `diy-wds-trigger` 亦在四子命令之外加了 `metrics`；本批 `diy-wds-system`
  同款加 `similarity`。**不写盘**。
- 退出码：0 放行 / 1 违规 / 2 用法错误。
- 违规码：**复用冻结集**（MISSING_FILE / UNPARSABLE_YAML / DUPLICATE_ID / UNKNOWN_ID /
  EMPTY_FIELD / ENUM_INVALID / STATUS_MISMATCH / SET_MISMATCH / ASSUMPTION_PRESENT）
  + B6 已批码 TOKEN_UNRESOLVED。**本批不新增码**。
- 写范围：`{output_dir}/wds-assets.yaml`（唯一写盘面）；
  `{output_dir}/assets/<活动>/` 下的产物由会话写（裁定 12），本引擎只校验其路径引用。
- 跨技能机械核（任务书 §2.3.1 的**必读键** `scenarios[].pages[].id`）：`items[].pages[]` 逐条
  核形态 `SC-<nn>.P<n>`（不合 → `SET_MISMATCH`）并解析到上游 `wds-scenarios.yaml` 的页面清单
  （解析不到 → `UNKNOWN_ID`）；`check` 与 `init` **同门禁**（上游缺席 / 未定稿 → 停止）。
- 文档化陷阱：产物是 WDS 型，**不得**改用 `diyc.py check --type`（主线 8 型封闭集）。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "diy-tools" / "scripts"))
from diyc_lib import display_path, nonempty, now, project_name  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))

from wds_assets_checks import cmd_check, summarize
from wds_assets_lib import (
    ACTIVITY_STATUS, DIR_OF, PRODUCT, Report, gate_upstream, load_yaml,
    read_design_system, save_yaml_atomic, skeleton
)

try:
    import yaml
except ImportError:  # pragma: no cover
    print("需要 PyYAML：pip install pyyaml", file=sys.stderr)
    raise SystemExit(2)



# --------------------------------------------------------------------- init


def cmd_init(args, report: Report):
    output_dir = Path(args.output_dir).resolve()
    if gate_upstream(report, output_dir) is None:
        report.counts = {"activities": 0, "items": 0, "written": False, "has_design_system": False}
        report.extra["updated"] = False
        return report.exit_code()
    ds = read_design_system(report, output_dir)

    path = output_dir / PRODUCT
    if path.exists():
        existing = load_yaml(path, report)
        if existing is None:
            report.extra["updated"] = False
            return report.exit_code()
        report.counts = summarize(existing)
        report.counts["written"] = False
        report.counts["has_design_system"] = ds is not None
        report.extra["updated"] = False
        return report.exit_code()

    doc = skeleton(Path(args.project_root).resolve())
    save_yaml_atomic(path, doc)
    report.counts = summarize(doc)
    report.counts["written"] = True
    report.counts["has_design_system"] = ds is not None
    report.extra["updated"] = True
    return report.exit_code()




# --------------------------------------------------------------------- list


def cmd_list(args, report: Report):
    output_dir = Path(args.output_dir).resolve()
    doc = load_yaml(output_dir / PRODUCT, report)
    if doc is None:
        return report.exit_code()
    wanted = getattr(args, "status", None)
    if wanted and wanted not in ACTIVITY_STATUS:
        report.bad("ENUM_INVALID", "--status", f"非法活动状态：{wanted}")
        return report.exit_code()
    rows = []
    for act in doc.get("activities") or []:
        if wanted and act.get("status") != wanted:
            continue
        exported = len(
            [
                p
                for p in (doc.get("prompts") or [])
                if p.get("activity") == act.get("id") and p.get("exported")
            ]
        )
        rows.append(
            {
                "id": act.get("id"),
                "code": act.get("code"),
                "name": act.get("name"),
                "status": act.get("status"),
                "items": len(act.get("items") or []),
                "exported": exported,
            }
        )
    report.extra["activities"] = rows
    report.counts = summarize(doc)
    report.counts["listed"] = len(rows)
    return report.exit_code()


# --------------------------------------------------------------------- show


def find_record(doc: dict, ident: str):
    """按 ID 找记录：活动 / 条目 / 演示记录 / 提示词条目——**与 `check` 同一 ID 空间**（裁定 9）。"""
    for act in doc.get("activities") or []:
        if act.get("id") == ident:
            return act
        for item in act.get("items") or []:
            if item.get("id") == ident:
                return item
    for key in ("presentation", "prompts"):
        for entry in doc.get(key) or []:
            if (entry or {}).get("id") == ident:
                return entry
    return None


def cmd_show(args, report: Report):
    output_dir = Path(args.output_dir).resolve()
    doc = load_yaml(output_dir / PRODUCT, report)
    if doc is None:
        return report.exit_code()
    ident = getattr(args, "id", None)
    if not ident:
        report.extra["doc"] = doc
        report.counts = summarize(doc)
        return report.exit_code()
    record = find_record(doc, ident)
    if record is None:
        report.bad("UNKNOWN_ID", ident, f"产物里没有 {ident}")
        return report.exit_code()
    report.extra["record"] = record
    report.counts = summarize(doc)
    return report.exit_code()


# ------------------------------------------------------------------- prompts


def cmd_prompts(args, report: Report):
    output_dir = Path(args.output_dir).resolve()
    doc = load_yaml(output_dir / PRODUCT, report)
    if doc is None:
        return report.exit_code()
    wanted = getattr(args, "activity", None)
    if wanted and wanted not in DIR_OF:
        report.bad("ENUM_INVALID", "--activity", f"非法活动 ID：{wanted}")
        return report.exit_code()
    rows = [p for p in (doc.get("prompts") or []) if not wanted or p.get("activity") == wanted]
    report.extra["prompts"] = rows
    report.counts = summarize(doc)
    report.counts["listed"] = len(rows)
    return report.exit_code()


# ---------------------------------------------------------------------- CLI


def _common_flags(parser):
    """共同旗标：`--project-root` 全部子命令都收；`--output-dir` 由 main 兜底（仅 init 必填）。"""
    parser.add_argument("--project-root", default=argparse.SUPPRESS, help="项目根（默认 .）")
    parser.add_argument("--output-dir", default=argparse.SUPPRESS,
                        help="产物目录（缺省 {project-root}/diy-output；写盘子命令 init 必填）")
    parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help="以 JSON 回执输出")
    return parser


def build_parser():
    common = _common_flags(argparse.ArgumentParser(add_help=False))
    parser = _common_flags(
        argparse.ArgumentParser(prog="wds_assets.py", description="diy-wds-assets 领域引擎")
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("init", parents=[common], help="铸骨架（唯一写盘）")
    p_list = sub.add_parser("list", parents=[common], help="只回约定字段")
    p_list.add_argument("--status")
    p_show = sub.add_parser("show", parents=[common], help="单条 / 整份")
    p_show.add_argument("--id")
    p_check = sub.add_parser("check", parents=[common], help="终门（--final 唯一放行）")
    p_check.add_argument("--final", action="store_true")
    p_prompts = sub.add_parser("prompts", parents=[common], help="提示词导出索引（只读）")
    p_prompts.add_argument("--activity")
    return parser


def main(argv=None):
    # 回执是机器读面：stdout/stderr 一律 UTF-8（VA-01；与其余四引擎逐字同款两行）
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    parser = build_parser()
    args = parser.parse_args(argv)
    root_given = str(getattr(args, "project_root", "."))
    project_root = Path(root_given).resolve()
    raw_output = getattr(args, "output_dir", None)
    # 只读子命令缺省回落 `{project_root}/diy-output`（V3-03；对齐 wds_system / evolution / analyze / reverse）
    output_dir = Path(raw_output).resolve() if raw_output else project_root / "diy-output"
    args.output_dir = str(output_dir)          # 各 handler 统一从 args 取（含回落值）
    as_json = bool(getattr(args, "json", False))

    if not args.command:
        report = Report("", project_root, output_dir, root_given)
        report.bad("ENUM_INVALID", "command", "缺少子命令：init / list / show / check / prompts")
        emit(report, as_json, exit_code=2)
        return 2
    if args.command == "init" and not raw_output:
        report = Report(args.command, project_root, output_dir, root_given)
        report.bad("ENUM_INVALID", "--output-dir", "写盘子命令 init 必填 --output-dir")
        emit(report, as_json, exit_code=2)
        return 2

    report = Report(args.command, project_root, output_dir, root_given)
    handler = {
        "init": cmd_init,
        "list": cmd_list,
        "show": cmd_show,
        "check": cmd_check,
        "prompts": cmd_prompts,
    }[args.command]
    code = handler(args, report)
    emit(report, as_json, code)
    return code


def emit(report: Report, as_json: bool, exit_code: int):
    """回执输出：`--json` = 单行 JSON（契约 §3）；无 `--json` = 每违规一行 `CODE where: msg` + 汇总行。"""
    payload = report.receipt(ok=(exit_code == 0))
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, default=str))
    else:
        for item in report.violations:
            print(f"{item['code']} {item['where']}: {item['msg']}")
        for item in report.warnings:
            print(f"WARN {item['code']} {item['where']}: {item['msg']}")
        print(f"ok={payload['ok']} violations={len(report.violations)} warnings={len(report.warnings)}")


if __name__ == "__main__":
    raise SystemExit(main())
