# -*- coding: utf-8 -*-
"""diy-help CLI 入口：渲染人类/JSON 回执，编排多实例聚合总览。核心判定见 help_lib。"""
# trace: S-13 AC-13.1 AC-13.2 TC-13.1.1 TC-13.1.2 TC-13.2.1
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # 兄弟件 help_lib
import help_lib  # noqa: E402  先导入：注入 diy-tools/scripts 到 sys.path
from diyc_lib import INSTANCE_RE, resolve_output_dir  # noqa: E402
from help_lib import _fail, chain_nodes, evaluate, load_registry, started_lines  # noqa: E402


def discover_instances(output_dir, lines_meta, chains):
    """合规子目录（INSTANCE_RE）且含链产物 → [(name, path)]，按名字典序。"""
    if not os.path.isdir(output_dir):
        return []
    found = []
    for name in sorted(os.listdir(output_dir)):
        sub = os.path.join(output_dir, name)
        if os.path.isdir(sub) and INSTANCE_RE.fullmatch(name) and \
                started_lines(sub, lines_meta, chains):
            found.append((name, sub))
    return found


def aggregate_result(output_dir, lines_meta, chains, branches, include_root):
    """多实例总览回执。include_root 且平铺根有产物时加 (root) 行（裁 4）。"""
    targets = []
    if include_root and started_lines(output_dir, lines_meta, chains):
        targets.append(("(root)", output_dir))
    targets += discover_instances(output_dir, lines_meta, chains)
    instances = []
    for name, path in targets:
        item = evaluate(path, lines_meta, chains, branches, None)
        item["instance"] = name
        if item["position"] != "零起点" and item["branches"]:
            item["notes"].append(
                "两线并存——用 --instance %s --line <线名> 查看单线进度" % name)
        instances.append(item)
    return {
        "mode": "aggregate",
        "position": "多版本总览（%d 个实例）" % len(instances),
        "line": None,
        "branches": None,
        "output_dir": output_dir,
        "completed_steps": [],
        "next_skill": None,
        "blocked": None,
        "notes": [],
        "workflow_done": False,
        "instances": instances,
    }


def render_human(result):  # trace: S-13 AC-13.2 TC-13.2.1 阻塞优先聚焦；blocked 时抑制可选提示
    lines = []
    lines.append("当前位置：%s" % result["position"])
    if result["completed_steps"]:
        lines.append("已完成：%s" % "、".join(result["completed_steps"]))
    if result["blocked"]:
        b = result["blocked"]
        lines.append("阻塞项：%s（当前状态 %s）" % (b["file"], b["status"]))
        lines.append("需要的动作：%s" % b["action"])
    else:
        if result["next_skill"]:
            lines.append("下一步：运行 %s" % result["next_skill"])
        elif result["workflow_done"]:
            lines.append("下一步：工作流已全部完成。可选收尾：证伪轮（diy-review --falsify all）、bug-log 经验入库。")
        if result.get("branches"):
            lines.append("分叉：%s" % "；".join(
                "%s → %s" % (b["label"], b["entry"]) for b in result["branches"]))
        for n in result["notes"]:
            lines.append("提示：%s" % n)
    return "\n".join(lines)


def render_human_aggregate(result, lines_meta):
    """多实例总览表：版本｜线｜位置｜下一步｜阻塞；阻塞项置顶（稳定排序）。"""
    rows = []
    for item in result["instances"]:
        if item["position"] == "零起点":
            line_label = "零起点"
        elif item["branches"]:
            line_label = "多线并存"
        else:
            line_label = lines_meta[item["line"]]["label"]
        if item["blocked"]:
            nxt, blk = "—", item["blocked"]["action"]
        else:
            nxt = item["next_skill"] or ("已完成" if item["workflow_done"] else "—")
            blk = "—"
        rows.append((0 if item["blocked"] else 1, item["instance"],
                     line_label, item["position"], nxt, blk))
    rows.sort(key=lambda r: r[0])  # 稳定排序：组内保持版本字典序
    lines_out = ["当前位置：%s" % result["position"],
                 "版本 | 线 | 位置 | 下一步 | 阻塞"]
    for _, ver, line_label, pos, nxt, blk in rows:
        lines_out.append("%s | %s | %s | %s | %s" % (ver, line_label, pos, nxt, blk))
    for n in result["notes"]:
        lines_out.append("提示：%s" % n)
    return "\n".join(lines_out)


def main():  # trace: S-13 AC-13.1 TC-13.1.1 组装位置/推荐/阻塞（零起点→该线入口 + 分叉候选）
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="diy-coder 工作流状态机导航")
    ap.add_argument("--project-root", default=".", help="项目根目录")
    ap.add_argument("--instance", default=None, help="实例名")
    ap.add_argument("--line", default=None, help="强制指定当前线（登记表 lines 的键）")
    ap.add_argument("--all-instances", action="store_true",
                    help="强制聚合 output_dir 下全部实例（含平铺根 (root) 行）")
    ap.add_argument("--json", action="store_true", help="机器可读 JSON 输出")
    args = ap.parse_args()

    reg = load_registry()
    lines_meta = reg["lines"]
    if args.line is not None and args.line not in lines_meta:
        _fail("未知的线 %r（登记表只有：%s）" % (args.line, "、".join(sorted(lines_meta))))
    chains = {name: chain_nodes(reg, name) for name in lines_meta}
    branches = [{"line": n, "label": lines_meta[n]["label"], "entry": lines_meta[n]["entry"]}
                for n in lines_meta]

    output_dir = resolve_output_dir(args.project_root, args.instance)
    # 聚合：显式 --all-instances，或平铺根无产物且存在含链产物的合规子目录
    aggregate = False
    if args.instance is None:
        if args.all_instances:
            aggregate = True
        elif not started_lines(output_dir, lines_meta, chains) and \
                discover_instances(output_dir, lines_meta, chains):
            aggregate = True
    result = None
    if aggregate:
        agg = aggregate_result(output_dir, lines_meta, chains, branches,
                               include_root=args.all_instances)
        if agg["instances"]:
            if args.line is not None:  # 裁 2：先选版本，再选线
                _fail("聚合模式不能用 --line——先用 --instance <版本> 选定版本，"
                      "再用 --line <线名> 指定线")
            result = agg
    if result is None:  # 单目录模式（含 --all-instances 空目录回退）
        result = evaluate(output_dir, lines_meta, chains, branches, args.line)
        if args.instance is None:  # 裁 3：混合态提示，不改主判定
            others = discover_instances(output_dir, lines_meta, chains)
            if others:
                result["notes"].append(
                    "另发现 %d 个实例目录——用 --all-instances 查看汇总" % len(others))

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif result.get("mode") == "aggregate":
        print(render_human_aggregate(result, lines_meta))
    else:
        print(render_human(result))


if __name__ == "__main__":
    main()
