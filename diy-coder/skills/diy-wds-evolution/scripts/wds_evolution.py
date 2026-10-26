# -*- coding: utf-8 -*-
"""diy-wds-evolution 的领域引擎（B7b 工位 W3）。

机制与规则来源
--------------
- 契约：`batch3-contract.md` §2.2/§3/§5/§7（子命令面、回执 schema、违规码冻结集、
  原子写纪律、代码惯例）。本引擎是本技能终门的**唯一**执行者——WDS 型产物一律走本引擎的
  `check`，**不得**改用 `diyc.py check --type`（`CHECK_TYPES` 是主线 8 型封闭集）。
- 产物：`{output_dir}/wds-evolution.yaml`（B7b 任务书 §2.3；主体段 `rounds[]` + `kaizen_priority`，
  记录 ID `EV-<nn>`）。
- 门禁（任务书裁定 9）：本技能是**入口技能**（`precededBy: []`）——门禁 = **既有产物任一在场**
  （`design.yaml` / `sprint.yaml` / `wds-*.yaml`，**本技能自己的产物除外**——它是要被演进的对象之外的东西）。
- 裁定 10：[T] 只验**本轮增量**（全量验收归 `diy-dev` 的 WDS 模式）→ `rounds[].test.scope` 冻结值
  `本轮增量`，`check --final` 机械核对。
- Kaizen 优先级框架（本技能相对 `diy-dev` 的不可替代内容）：`Priority = Impact × Effort × Learning`，
  三因子各取 `high|medium|low`（权重 5/3/1），`score` 必须等于三因子权重之积——
  **源侧两处表述互斥在此归一**：`kaizen-principles.md` 把 Effort 的 High 记作「1–2 天」（省力最优）、
  `steps-a/step-01` 的表把 High 记作「1-2 days」——故三因子**一律「越大越好」**，
  `score` 高 = 优先；**不是**「工作量越大越优先」。

违规码：**零新增**，全部复用 `batch3-contract.md` §3 冻结集
（`MISSING_FILE` / `UNPARSABLE_YAML` / `DUPLICATE_ID` / `UNKNOWN_ID` / `ENUM_INVALID` /
`EMPTY_FIELD` / `STATUS_MISMATCH` / `SET_MISMATCH` / `ASSUMPTION_PRESENT`）。
模态语义复用三处（在此声明）：
  ① `MISSING_FILE` 在 `init` 上承载「**入口门禁**：无任何既有产物可演进」——源侧该情形
     由「口头接力」承担（census-5 §6.2），diy 侧升级为硬门；
  ② `STATUS_MISMATCH` 承载「`--final` 时 `project.status` 非 `已定稿`」「轮次未达 `已交付`」
     「本轮增量判据存在 `未通过`」三类；
  ③ 轮级 `analysis_refs` 依赖声明的一档硬报错（批 5e §7-2 甲）：缺席 `MISSING_FILE` /
     损坏 `UNPARSABLE_YAML` / 锚悬空 `UNKNOWN_ID` / 形态不良 `ENUM_INVALID`——
     见 `validate_analysis_refs`（空或缺席 → 不检不阻）。

写盘纪律：`init` 是**唯一写盘**命令；`list` / `show` / `check` 全程只读。
原子写 = 全文 load → 就地改 → 同目录临时文件 + `os.replace`（同 `diyc_lib.save_yaml_atomic`
的「同款」实现——本技能目录自带全部内容，不跨目录 import 共享库，见 NFR-4）。
"""

import argparse
import json
import os
import re
import sys

import yaml

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import now, receipt, save_yaml_atomic, today, v  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wds_evolution_checks import (
    ENTRIES, FACTORS, FACTOR_WEIGHT, INCREMENT_SCOPE, PRODUCT, ROUND_STATUS,
    build_counts, emit, gate_present, load_product_or_report, load_yaml_soft,
    norm, product_path, rounds_of, validate, validate_analysis_refs
)


# —— 冻结常量 ——

def cmd_init(args):
    violations, warnings = [], []
    where = norm(product_path(args.output_dir))
    if not args.target or not str(args.target).strip():
        violations.append(v("EMPTY_FIELD", where, "--target 必填，不得为空"))
    if args.entry not in ENTRIES:
        violations.append(v("ENUM_INVALID", "--entry",
                            "取值 {} 不在 {}".format(args.entry, "|".join(ENTRIES))))
    counts = {"rounds": 0, "by_status": {}, "candidates": 0, "delivered": 0}
    if violations:
        return receipt("init", False, instance=None, project_root=args.project_root,
                       output_dir=norm(args.output_dir), violations=violations,
                       warnings=warnings, counts=counts)

    # 入口门禁（裁定 9）：既有产物任一在场
    hits = gate_present(args.output_dir)
    if not hits:
        violations.append(v("MISSING_FILE", where,
                            "入口门禁：{} 下无任何既有产物（design.yaml / sprint.yaml / "
                            "wds-*.yaml）可演进——本技能不产零起点项目".format(
                                norm(args.output_dir))))
        return receipt("init", False, instance=None, project_root=args.project_root,
                       output_dir=norm(args.output_dir), violations=violations,
                       warnings=warnings, counts=counts)

    # 已有产物 → 不覆盖（只刷 updated + warning）
    if os.path.exists(product_path(args.output_dir)):
        data, err, code = load_yaml_soft(product_path(args.output_dir))
        if err and err != "missing":
            violations.append(v(code or "UNPARSABLE_YAML", where,
                                "产物损坏，拒绝写入：{}".format(err)))
            return receipt("init", False, instance=None, project_root=args.project_root,
                           output_dir=norm(args.output_dir), violations=violations,
                           warnings=warnings, counts=counts)
        if not isinstance(data, dict):
            violations.append(v("UNPARSABLE_YAML", where, "产物顶层不是映射，拒绝写入"))
            return receipt("init", False, instance=None, project_root=args.project_root,
                           output_dir=norm(args.output_dir), violations=violations,
                           warnings=warnings, counts=counts)
        data.setdefault("project", {})["updated"] = now()
        save_yaml_atomic(product_path(args.output_dir), data)
        warnings.append(v("SET_MISMATCH", where,
                          "产物已存在：骨架与 EV-01 未重建，只刷 project.updated"))
        return receipt("init", True, instance=None, project_root=args.project_root,
                       output_dir=norm(args.output_dir), violations=violations,
                       warnings=warnings, counts=build_counts(data), updated=now())

    # 铸骨架 + 首轮铸号
    name = os.path.basename(os.path.abspath(args.project_root)) or "project"
    data = {
        "project": {"name": name, "created": now(), "updated": now(),
                    "status": "草稿"},
        "kaizen_priority": {
            "formula": "Priority = Impact × Effort × Learning",
            "scale": {factor: dict(FACTOR_WEIGHT) for factor in FACTORS},
            "candidates": [],
        },
        "rounds": [{
            "id": "EV-01",
            "target": str(args.target).strip(),
            "status": "草稿",
            "entry": args.entry,
            "analysis": {},
            "scope": {},
            "design": {},
            "implement": {},
            "test": {"scope": INCREMENT_SCOPE, "criteria": []},
            "delivery": {},
        }],
        "revisions": [],
    }
    save_yaml_atomic(product_path(args.output_dir), data)
    return receipt("init", True, instance=None, project_root=args.project_root,
                   output_dir=norm(args.output_dir), violations=violations,
                   warnings=warnings, counts=build_counts(data), updated=now())


def cmd_list(args):
    violations, warnings = [], []
    if args.status and args.status not in ROUND_STATUS:
        violations.append(v("ENUM_INVALID", "--status",
                            "取值 {} 不在 {}".format(args.status, "|".join(ROUND_STATUS))))
        return receipt("list", False, instance=None, project_root=args.project_root,
                       output_dir=norm(args.output_dir), violations=violations,
                       warnings=warnings, counts={})
    data = load_product_or_report(args.output_dir, violations)
    if data is None:
        return receipt("list", False, instance=None, project_root=args.project_root,
                       output_dir=norm(args.output_dir), violations=violations,
                       warnings=warnings, counts={})
    rows = []
    for rnd in rounds_of(data):
        if not isinstance(rnd, dict):
            continue
        if args.status and rnd.get("status") != args.status:
            continue
        rows.append({"id": rnd.get("id"), "target": rnd.get("target"),
                     "status": rnd.get("status"), "entry": rnd.get("entry")})
    return receipt("list", True, instance=None, project_root=args.project_root,
                   output_dir=norm(args.output_dir), violations=violations,
                   warnings=warnings, counts=build_counts(data), rounds=rows)


def cmd_show(args):
    violations, warnings = [], []
    data = load_product_or_report(args.output_dir, violations)
    if data is None:
        return receipt("show", False, instance=None, project_root=args.project_root,
                       output_dir=norm(args.output_dir), violations=violations,
                       warnings=warnings, counts={})
    if args.id:
        hit = None
        for rnd in rounds_of(data):
            if isinstance(rnd, dict) and rnd.get("id") == args.id:
                hit = rnd
                break
        if hit is None:
            violations.append(v("UNKNOWN_ID", "rounds[].id",
                                "{} 在 {} 中不存在".format(args.id, PRODUCT)))
            return receipt("show", False, instance=None, project_root=args.project_root,
                           output_dir=norm(args.output_dir), violations=violations,
                           warnings=warnings, counts=build_counts(data))
        return receipt("show", True, instance=None, project_root=args.project_root,
                       output_dir=norm(args.output_dir), violations=violations,
                       warnings=warnings, counts=build_counts(data), round=hit)
    return receipt("show", True, instance=None, project_root=args.project_root,
                   output_dir=norm(args.output_dir), violations=violations,
                   warnings=warnings, counts=build_counts(data), document=data)


def cmd_check(args):
    violations, warnings = [], []
    data = load_product_or_report(args.output_dir, violations)
    if data is None:
        return receipt("check", False, instance=None, project_root=args.project_root,
                       output_dir=norm(args.output_dir), violations=violations,
                       warnings=warnings, counts={})
    validate(data, violations, warnings, bool(args.final))
    validate_analysis_refs(data, args.output_dir, violations)
    return receipt("check", not violations, instance=None, project_root=args.project_root,
                   output_dir=norm(args.output_dir), violations=violations,
                   warnings=warnings, counts=build_counts(data))


# —— CLI ——


def build_parser():
    ap = argparse.ArgumentParser(
        prog="wds_evolution.py",
        description="diy-wds-evolution 领域引擎：init 铸骨架 / list 续接 / show 取件 / check 终门",
    )
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--project-root", default=".", help="项目根（默认 .）")
    common.add_argument("--output-dir", default=None,
                        help="产物目录（相对 project-root；init 必填）")
    common.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    sub = ap.add_subparsers(dest="command")

    p_init = sub.add_parser("init", parents=[common], help="铸骨架与首轮 EV-01（唯一写盘）")
    p_init.add_argument("--entry", help="双轨入口：存量接入|上线后持续")
    p_init.add_argument("--target", help="本轮选定目标（必填）")
    p_init.set_defaults(func=cmd_init, requires_output=True)

    p_list = sub.add_parser("list", parents=[common], help="只回约定字段，不读正文")
    p_list.add_argument("--status", help="按记录级 status 过滤")
    p_list.set_defaults(func=cmd_list, requires_output=False)

    p_show = sub.add_parser("show", parents=[common], help="整份或单轮全文")
    p_show.add_argument("--id", help="EV-<nn>")
    p_show.set_defaults(func=cmd_show, requires_output=False)

    p_check = sub.add_parser("check", parents=[common], help="终门：--final 为定稿级")
    p_check.add_argument("--final", action="store_true", help="定稿级校验")
    p_check.set_defaults(func=cmd_check, requires_output=False)
    return ap


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = build_parser()
    args = ap.parse_args(argv)
    if not getattr(args, "func", None):
        ap.print_usage(sys.stderr)
        return 2
    if args.requires_output and not args.output_dir:
        ap.error("--output-dir 必填于写盘子命令")
    # 缺省回落 `{project_root}/diy-output`（**不是** CWD 相对——否则 `--project-root X`
    # 的调用方会静默读到另一个项目的产物）。同 wds_system.py / analyze.py / reverse.py。
    args.output_dir = args.output_dir or os.path.join(args.project_root, "diy-output")
    result = args.func(args)
    return emit(result, args.json)


if __name__ == "__main__":
    sys.exit(main())
