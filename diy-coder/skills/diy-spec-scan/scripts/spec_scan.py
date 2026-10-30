# -*- coding: utf-8 -*-
"""diy-spec-scan 确定性引擎：扫描单元枚举（collect）+ spec-scan.yaml 歧义清单校验（check）。

机制：本技能扮演实现者预演「照着规格干活」，把规格里没写清、留人猜的地方记成歧义清单
（spec-scan.yaml）。引擎只做机械可判的两件事——

  collect  枚举扫描目标，产出扫描单元清单（覆盖清单：人/agent 靠它确认有没有漏扫）：
             目标为文件 → 该文件即唯一目标文件；
             目标为目录且含 SKILL.md → SKILL.md + steps/*.md（按文件名排序）；
             其余目录 → 该目录下 *.md（递归一层：本层 + 一层子目录，不再深挖）；
             都找不到 .md → MISSING_FILE，exit 1 零产出。
           每个目标文件给出：相对 project-root 的正斜杠路径、行数、切分建议——按 markdown
           二级标题 `## `（行首、井号后一个空格；`###` 不算）切出的单元名列表（标题文本去掉
           `## ` 前缀与首尾空白；无二级标题则整个文件算一个单元，单元名取文件名）。
           文件读了但无法按 UTF-8 解码 → SCAN_TRUNCATED warning（该文件仍列出、行数记 0、
           单元不切分），不阻断（exit 仍 0）。
           相对 --target 按 project-root 解析（对齐 investigation.py 先例）。

  check    校验 {output_dir}/spec-scan.yaml（本技能产出的歧义清单）。基础校验：YAML 可解析
           （异常转 UNPARSABLE_YAML，不让异常裸奔）；顶层 project{name,created,updated} +
           scans[] + revisions[] 缺项；scans[].id 形态 SS-0nn（三位数字）且全局唯一
           （DUPLICATE_ID / ENUM_INVALID）；scans[].target 在场且含 path；units[] 每项
           unit / path / scanned（布尔）；findings[] 每条 id 形态 SS-0nn-nn 且唯一、type 八值
           枚举（分支无定义 / 术语冲突 / 接口缺口 / 输入不明 /
           输出不明 / 时序不明 / 直接矛盾 / 隐含假设）、where 非空
           且形如 <path> 或 <path>:<行号>、quote / read_as / stuck / would_guess 四字段全非空
           （EMPTY_FIELD；would_guess = 若我是实现者我会猜成什么——没有它这条 finding 不成立）、
           severity ∈ 阻断|建议|观察、source 为数组且元素 ∈ 卡点|穷举|交叉认证（越界
           ENUM_INVALID；schema 分层：顶层 schema ≥2 时 source 缺失或空数组 → EMPTY_FIELD，
           无 schema 的存量文件缺 source 缺省当 [卡点] 不报错）；scans[].summary 的
           total/blocker/major/minor 与 findings 真值一致、units_total/units_scanned 与
           units 数组一致、by_source 三键映射（卡点/穷举/交叉认证）与 source 分法计数一致
           （按元素各计，存量缺 source 按 [卡点] 计；by_source 同享 schema 分层——
           schema ≥2 缺失报 EMPTY_FIELD，无 schema 存量缺 summary.by_source 键缺省
           兼容不报，SET_MISMATCH）。
           --final 附加：全部 units[].scanned 为 true（未扫完 → SET_MISMATCH）、findings 的
           字符串字段零 [假设] 字面量（命中 → ASSUMPTION_PRESENT）——**`quote` 字段豁免**
           （2026-09-16 裁定）：该禁令管的是「扫描器自己未落定的推断」，而 quote 是**引文证据**，
           被扫规格本身可能就含该标记；对引文做字面量拦截会逼出全角改写，把「quote 逐字保留
           原文」这条本技能的立身纪律变成不可能。非 quote 字段若需提及该标记，写全角
           ［假设］（全角不是该禁令的字面量）。exit 0 唯一放行。

规则来源：违规码全部复用冻结集——本引擎用到 MISSING_FILE /
UNPARSABLE_YAML / DUPLICATE_ID / ENUM_INVALID / EMPTY_FIELD / ASSUMPTION_PRESENT /
SET_MISMATCH / SCAN_TRUNCATED 共 8 个，**无新增码**（UNKNOWN_ID 本技能无适用面，不产出）。
回执契约对齐 B1/B2 批既有先例：exit 0 唯一放行 / --json 单行 JSON（ensure_ascii=False）/
共同键 {ok, command, project_root, output_dir, violations[{code,where,msg}], warnings, counts}；
where 一律正斜杠、相对 project-root，无位置时为空字符串；人读态每条违规一行 `CODE where: msg`
+ 末尾汇总行；--output-dir 必填（argparse required，无默认值）。

分工裁定：本引擎不做实例解析、不做白名单、不推导目录（实例解析由 SKILL.md 委托 diyc.py
resolve，与本引擎无关）；只读——collect 只读目标文件，check 只读 spec-scan.yaml，两者都不写
任何文件（歧义清单由技能侧按引擎回执落盘）。
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import display_path, emit_via, load_yaml_safe, v, violation_line  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spec_scan_checks import check_scan, check_top_level, is_schema_v2, scan_counts  # noqa: E402
from spec_scan_collect import cmd_collect  # noqa: E402

SPEC_SCAN_FILE = "spec-scan.yaml"

# trace: diy-spec-scan check 子命令（spec-scan.yaml 校验；exit 0 唯一放行）
def cmd_check(args):
    root = os.path.abspath(args.project_root)
    out = os.path.abspath(args.output_dir)
    path = os.path.join(out, SPEC_SCAN_FILE)
    show = display_path(path, root)
    violations = []
    scans = []
    data, err = load_yaml_safe(path)
    if data is None and err is None:
        violations.append(v("MISSING_FILE", show,
                            "%s 不存在（先跑一次规格预演扫描产出歧义清单）" % SPEC_SCAN_FILE))
    elif err is not None:
        violations.append(v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err))
    elif not isinstance(data, dict):
        violations.append(v("EMPTY_FIELD", show,
                            "顶层不是映射（须为 project + scans + revisions）"))
    else:
        violations += check_top_level(data, show)
        schema2 = is_schema_v2(data)
        raw = data.get("scans")
        scans = raw if isinstance(raw, list) else []
        seen_scan_ids = set()
        seen_finding_ids = set()
        for i, scan in enumerate(scans):
            violations += check_scan(i, scan, show, args.final, schema2,
                                     seen_scan_ids, seen_finding_ids)
    counts = scan_counts(scans)
    payload = {
        "ok": not violations,
        "command": "check",
        "project_root": args.project_root,
        "output_dir": os.path.normpath(out).replace("\\", "/"),
        "final": args.final,
        "violations": violations,
        "warnings": [],
        "counts": counts,
    }
    emit_via(payload, args.json, human_check)
    return 0 if payload["ok"] else 1

# trace: diy-spec-scan check 人读态（每条违规一行 `CODE where: msg` + 末尾汇总行）
def human_check(payload):
    counts = payload["counts"]
    if payload["ok"]:
        print("PASS：%s 校验通过（scan %d · 单元 %d · finding %d）"
              % (payload["output_dir"] + "/" + SPEC_SCAN_FILE,
                 counts["scans"], counts["units"], counts["findings"]))
    else:
        for item in payload["violations"]:
            print(violation_line(item))
    print("汇总：违规 %d 条 · 警告 %d 条（exit %d）"
          % (len(payload["violations"]), len(payload["warnings"]), 0 if payload["ok"] else 1))

# trace: diy-spec-scan 命令行面（--output-dir 必填；引擎不做实例解析/目录推导）
def build_parser():
    ap = argparse.ArgumentParser(
        description="diy-spec-scan 确定性引擎：扫描单元枚举（collect）+ "
                    "spec-scan.yaml 歧义清单校验（check）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("collect", help="枚举扫描目标 → 扫描单元清单（覆盖清单；只读）")
    c.add_argument("--target", required=True,
                   help="扫描目标（文件或目录；相对路径按 project-root 解析）")
    c.add_argument("--project-root", default=".", help="项目根（默认 .）")
    c.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    c.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    c.set_defaults(func=cmd_collect)

    k = sub.add_parser("check", help="校验 spec-scan.yaml（schema/枚举/字段完整/计数一致；"
                                     "--final 附加全单元已扫与零假设）")
    k.add_argument("--project-root", default=".", help="项目根（默认 .）")
    k.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    k.add_argument("--final", action="store_true",
                   help="定稿校验：全部单元 scanned: true + findings 任意字段零 [假设]")
    k.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    k.set_defaults(func=cmd_check)
    return ap

# trace: diy-spec-scan 入口（stdout/stderr 固定 UTF-8；退出码由子命令返回）
def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = build_parser().parse_args()
    sys.exit(args.func(args))

if __name__ == "__main__":
    main()
