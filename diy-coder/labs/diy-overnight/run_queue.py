#!/usr/bin/env python3
"""夜队列机械循环 runner —— 起跑门/建分支/状态写回/失败还原/熔断计数/晨报骨架。

分层协议（见 SKILL.md 执行循环）：主 agent 常驻调度，循环中每步调本脚本；派 subagent 与裁断判断归主 agent，本脚本只做确定性机械动作。
权威提交门在 done：脚本自跑 test_cmd，全量绿才统一 stage+提交（无半红入链）。
用法：python run_queue.py <start|gate|done|fail|report> --queue PATH [...]；stdout 一行 JSON（ok 字段），致命错误 stderr 一行说明 exit 1。
"""
from __future__ import annotations

import argparse
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path

from rq_lib import (CIRCUIT_CAUSES, DUE_FMT, SKIP_CAUSES, branch_name, changed_rels,
                    die, dump_queue, emit, find_task, git, load_queue, next_runnable,
                    non_scope, parse_deadline, parse_dt, parse_phases, prev_tip,
                    queue_skip, repo_root, run_tests, task_index, tests_count_of,
                    tonight_of)


def cmd_start(args: argparse.Namespace) -> None:
    """写 base＋tonight 五数值＋started_at/baseline_min（开工时用户定档后调）。"""
    path = Path(args.queue)
    data = load_queue(path)
    busy = [t["id"] for t in data["tasks"] if t.get("status") == "进行中"]
    if busy:
        die(f"存在进行中条目 {busy}——先按中断恢复处置（fail --cause interrupt）")
    now = datetime.now()
    deadline = parse_deadline(args.deadline)
    data["base"] = git("rev-parse", "HEAD").stdout.strip()
    data["tonight"] = {
        "date": now.strftime("%Y-%m-%d"),
        "deadline": deadline.strftime(DUE_FMT),
        "grace_min": args.grace,
        "timeout_x": args.timeout_x,
        "circuit_limit": args.circuit,
        "buffer_min": args.buffer,
        "circuit_count": 0,
        "started_at": now.strftime(DUE_FMT),
        "baseline_min": args.baseline_min,
    }
    dump_queue(path, data)
    emit({"ok": True, "base": data["base"], "tonight": data["tonight"]})


def cmd_gate(args: argparse.Namespace) -> None:
    """起跑门＋建分支＋置进行中；门不过→余下待跑全转顺延。"""
    path = Path(args.queue)
    data = load_queue(path)
    t = tonight_of(data)
    if args.id:
        task = find_task(data, args.id)
        if task.get("status") not in ("待跑", "顺延", "跳过"):
            die(f"{args.id} 状态不可跑：{task.get('status')}")
    else:
        task = next_runnable(data)
        if task is None:
            emit({"ok": False, "reason": "无可跑条目"})
            return

    now = datetime.now()
    deadline = parse_dt(t["deadline"])
    gate_at = now + timedelta(minutes=task["estimate_min"] + t["buffer_min"])
    if gate_at > deadline:
        deferred = 0
        for other in data["tasks"][task_index(data, task["id"]):]:
            if other.get("status") == "待跑":
                other["status"] = "顺延"
                other["reason"] = "起跑门不过（now+estimate+buffer>deadline）"
                deferred += 1
        dump_queue(path, data)
        emit({"ok": False, "reason": "起跑门不过", "deferred": deferred})
        return

    idx = task_index(data, task["id"])
    tip = prev_tip(data, idx)
    head = git("rev-parse", "HEAD").stdout.strip()
    if not head.startswith(tip) and not tip.startswith(head):
        die(f"HEAD({head[:7]})≠链基点({tip[:7]})——先还原到上支 tip")
    name = branch_name(t["date"], task["id"])
    if git("show-ref", "--verify", "--quiet", f"refs/heads/{name}", check=False).returncode == 0:
        die(f"分支已存在：{name}")
    git("checkout", "-b", name, tip)
    task["status"] = "进行中"
    task["started_at"] = now.strftime(DUE_FMT)
    dump_queue(path, data)
    emit({"ok": True, "id": task["id"], "title": task.get("title"), "branch": name,
          "scope": task.get("scope") or [], "estimate_min": task["estimate_min"],
          "verify": task.get("verify") or [], "basis": task.get("basis")})


def cmd_done(args: argparse.Namespace) -> None:
    """权威门：scope 校验→跑全量（计时）→绿才 stage+提交→写 result 置完成。红 die 不写盘（交回修循环）。"""
    path = Path(args.queue)
    data = load_queue(path)
    t = tonight_of(data)
    task = find_task(data, args.id)
    if task.get("status") != "进行中":
        die(f"{args.id} 非进行中：{task.get('status')}")
    name = branch_name(t["date"], args.id)
    cur = git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    if cur != name:
        die(f"当前分支 {cur}≠任务分支 {name}")

    scope = task.get("scope") or []
    rels = changed_rels(queue_skip(path))
    bad = non_scope(rels, scope)
    if bad:
        die(f"scope 外改动（{bad[0]}）——先处置")
    if not rels:
        die("无改动——尚未到达提交点")

    grace_end = parse_dt(t["deadline"]) + timedelta(minutes=t["grace_min"])
    if datetime.now() > grace_end:
        die(f"已过宽限（deadline+{t['grace_min']}min）——改走 fail --cause timeout")

    test_cmd = data.get("test_cmd")
    if not test_cmd:
        die("test_cmd 缺失")
    green, out, test_sec = run_tests(test_cmd)
    if not green:
        tail = "\n".join(out.strip().splitlines()[-15:])
        die(f"全量红（回修后重跑 done；修不动则 fail --cause red --keep-branch）：\n{tail}")

    if scope:
        git("add", "--", *scope)
    else:
        git("add", "-A")
    now = datetime.now()
    elapsed_sec = max(0, int((now - parse_dt(task["started_at"])).total_seconds()))
    elapsed_min = round(elapsed_sec / 60, 1)
    overtime = elapsed_sec > task["estimate_min"] * t["timeout_x"] * 60
    est = task.get("estimate_min")
    msg = f"{args.type}: 夜队列 {args.id} {task.get('title') or args.id}"
    body = "\n".join([
        f"scope: {', '.join(scope) if scope else '(全库)'}",
        f"basis: {task.get('basis') or '—'}",
        f"tests: {args.tests}（脚本全量 {test_sec}s）",
    ])
    git("commit", "-m", msg, "-m", body)
    commit = git("rev-parse", "HEAD").stdout.strip()

    result = {
        "branch": name, "commit": commit, "tests": args.tests,
        "elapsed_sec": elapsed_sec, "elapsed_min": elapsed_min, "test_sec": test_sec,
        "ratio": round(elapsed_min / est, 2) if est else None,
    }
    tc = tests_count_of(args.tests)
    if tc is not None:
        result["tests_count"] = tc
    phase_warn = None
    phases = parse_phases(args.phases)
    if phases:
        result["phases"] = phases
        dev_min = (elapsed_sec - test_sec) / 60
        diff = abs(sum(phases.values()) - dev_min)
        if diff > 2:
            phase_warn = (f"phases 合计 {sum(phases.values())}min 与 "
                          f"实施段≈{dev_min:.1f}min 差 {diff:.1f}min")

    task["status"] = "完成"
    task["done_at"] = now.strftime(DUE_FMT)
    task["result"] = result
    t["circuit_count"] = 0  # 成功清零
    dump_queue(path, data)
    payload = {"ok": True, "id": args.id, "commit": commit, "elapsed_sec": elapsed_sec,
               "test_sec": test_sec, "overtime": overtime}
    if phase_warn:
        payload["phase_warn"] = phase_warn
    emit(payload)


def cmd_fail(args: argparse.Namespace) -> None:
    """失败处置：缺省零痕迹还原；--keep-branch（仅 red）＝三次仍红红标留审。均记 result{elapsed_sec,cause}。"""
    if args.cause not in SKIP_CAUSES:
        die(f"cause 须为 {SKIP_CAUSES}")
    if not args.reason.strip():
        die("reason 必填")
    if args.keep_branch and args.cause != "red":
        die("--keep-branch 仅配 --cause red（三次仍红留审）")
    path = Path(args.queue)
    data = load_queue(path)
    t = tonight_of(data)
    task = find_task(data, args.id)
    if task.get("status") != "进行中":
        die(f"{args.id} 非进行中：{task.get('status')}")
    idx = task_index(data, args.id)
    tip = prev_tip(data, idx)
    name = branch_name(t["date"], args.id)
    elapsed_sec = max(0, int((datetime.now() - parse_dt(task["started_at"])).total_seconds()))
    scope = task.get("scope") or []

    wip = None
    if args.keep_branch:
        rels = changed_rels(queue_skip(path))
        bad = non_scope(rels, scope)
        if bad:
            die(f"scope 外改动（{bad[0]}）——红标留审前先处置")
        if not rels:
            die("无改动可留——直接 fail 不带 --keep-branch")
        if scope:
            git("add", "--", *scope)
        else:
            git("add", "-A")
        git("commit", "-m", f"wip: 夜队列 {args.id} {task.get('title') or args.id}（三次仍红·留审）",
            "-m", f"reason: {args.reason}")
        wip = git("rev-parse", "HEAD").stdout.strip()
        git("checkout", "-f", tip)  # 留分支不删；链基点回退，绿链不受红标污染
    else:
        # 零痕迹还原：已跟踪回基点 → 清 scope 内自产未跟踪 → 删失败分支
        git("checkout", "-f", tip)
        if scope:
            proc = git("ls-files", "--others", "--exclude-standard", "--", *scope)
            for rel in (ln for ln in proc.stdout.splitlines() if ln.strip()):
                target = repo_root() / rel
                if target.is_dir():
                    shutil.rmtree(target, ignore_errors=True)
                elif target.exists():
                    target.unlink()
        if git("show-ref", "--verify", "--quiet", f"refs/heads/{name}", check=False).returncode == 0:
            git("branch", "-D", name)

    kind = "阻塞" if (args.cause == "ruling" or args.keep_branch) else "跳过"
    task["status"] = kind
    task["reason"] = f"[{args.cause}] {args.reason}"
    result = {"elapsed_sec": elapsed_sec, "cause": args.cause}
    if wip:
        result.update({"branch": name, "commit": wip, "kept": True})
    task["result"] = result
    circuit = False
    if args.cause in CIRCUIT_CAUSES:
        t["circuit_count"] = t.get("circuit_count", 0) + 1
        circuit = t["circuit_count"] >= t["circuit_limit"]
    dump_queue(path, data)
    emit({"ok": True, "id": args.id, "kind": kind, "circuit": circuit,
          "circuit_count": t.get("circuit_count", 0)})


def fmt_val(res: dict, key: str, suffix: str = "") -> str:
    v = res.get(key)
    return f"{v}{suffix}" if v is not None else "—"


def fmt_elapsed(res: dict) -> str:
    if res.get("elapsed_min") is not None:
        return f"{res['elapsed_min']}min"
    if res.get("elapsed_sec") is not None:  # 失败任务只记秒
        return f"{round(res['elapsed_sec'] / 60, 1)}min"
    return "—"


def cmd_report(args: argparse.Namespace) -> None:
    """晨报（队列同目录·不入库）＋runs 追加（同 date 行幂等更新）。"""
    path = Path(args.queue)
    data = load_queue(path)
    t = tonight_of(data)
    tasks = data["tasks"]
    counts = {s: sum(1 for x in tasks if x.get("status") == s)
              for s in ("完成", "顺延", "跳过", "阻塞")}
    now = datetime.now()
    date = t["date"]
    base_min = t.get("baseline_min")

    lines = [
        f"# 夜队列晨报 {date}",
        "",
        f"- base：`{data.get('base')}`",
        f"- deadline：{t['deadline']}（宽限 {t['grace_min']}min／超时 {t['timeout_x']}×estimate／熔断 {t['circuit_limit']}／缓冲 {t['buffer_min']}min）",
        f"- 基线测试：{base_min if base_min is not None else '—'}min",
        f"- 运行窗：{t.get('started_at', '?')} → {now.strftime(DUE_FMT)}",
        f"- 完成 {counts['完成']} · 顺延 {counts['顺延']} · 跳过 {counts['跳过']} · 阻塞 {counts['阻塞']}",
        "",
        "| 任务 | 状态 | 预估 | 耗时 | 偏差 | 分支 | commit | 测试 | 备注 |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for task in tasks:
        res = task.get("result") or {}
        est = task.get("estimate_min")
        note = task.get("reason") or ""
        lines.append(
            f"| {task.get('id')} | {task.get('status')} | {est if est is not None else '—'} "
            f"| {fmt_elapsed(res)} | {fmt_val(res, 'ratio', '×')} "
            f"| {res.get('branch', '—')} | {(res.get('commit') or '—')[:7]} "
            f"| {res.get('tests', '—')} | {note or '—'} |"
        )
    pending = [x for x in tasks if x.get("status") in ("顺延", "跳过", "阻塞")]
    if pending:
        lines += ["", "## 未完成项（原因＋建议处置）", ""] + [
            f"- **{t2.get('id')}** `{t2.get('status')}`：{t2.get('reason') or '—'}"
            for t2 in pending]
    blocked = [x for x in tasks if x.get("status") == "阻塞"]
    if blocked:
        lines += ["", "## 待裁点（阻塞条目）", ""] + [
            f"- {t2.get('id')}：{t2.get('reason')}"
            + ("（红标分支留审：`git checkout " + branch_name(date, t2['id']) + "` 亲验）"
               if (t2.get("result") or {}).get("kept") else "")
            for t2 in blocked]
    lines += ["", "## 早审指引（照队列序逐支，每支三步）", "",
              "1. 看变更：`git diff <前支tip>..<本支tip>`（首支＝`<base>..<首支>`）；可 checkout 亲验跑 `test_cmd`。",
              "2. 裁断：过 → `git merge <支> --no-ff` 入 dev；否 → 不合、记待办（含分支名）继续下一支；拿不准 → 停，余支记待办。",
              "3. 全过完：删链 `git branch -d overnight/<日期>/*` ＋归档队列完成条目。", ""]
    report = path.parent / f"report-{date}.md"
    report.write_text("\n".join(lines), encoding="utf-8")

    fail_dist: dict[str, int] = {}
    for x in tasks:
        cause = (x.get("result") or {}).get("cause")
        if cause:
            fail_dist[cause] = fail_dist.get(cause, 0) + 1
    run_row = {
        "date": date, "base": data.get("base"), "deadline": t["deadline"],
        "完成": counts["完成"], "顺延": counts["顺延"],
        "跳过": counts["跳过"], "阻塞": counts["阻塞"],
        "estimate_合计": sum(x.get("estimate_min") or 0 for x in tasks),
        "实际_合计_秒": sum((x.get("result") or {}).get("elapsed_sec") or 0 for x in tasks),
        "失败分布": fail_dist,
        "熔断": bool(t.get("circuit_count", 0) >= t.get("circuit_limit", 1 << 30)),
    }
    runs = data.setdefault("runs", [])
    for i, row in enumerate(runs):
        if isinstance(row, dict) and row.get("date") == date:
            runs[i] = run_row
            break
    else:
        runs.append(run_row)
    dump_queue(path, data)
    emit({"ok": True, "report": str(report), "counts": counts})


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="run_queue", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    def common(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--queue", required=True, help="queue.yaml 路径")

    sp = sub.add_parser("start", help="写 base＋tonight（开工定档后调）")
    common(sp)
    sp.add_argument("--deadline", default="07:00", help="HH:MM（最近未来时刻）或完整 ISO")
    sp.add_argument("--grace", type=int, default=45, help="宽限分钟（缺省 45）")
    sp.add_argument("--timeout-x", type=float, default=2.0, help="超时倍数（缺省 2×estimate）")
    sp.add_argument("--circuit", type=int, default=2, help="连跳熔断阈值（缺省 2）")
    sp.add_argument("--buffer", type=int, default=15, help="测试缓冲分钟（缺省 15）")
    sp.add_argument("--baseline-min", type=float, default=None,
                    help="基线自证全量墙钟分钟（开工前置那次跑的耗时）")
    sp.set_defaults(fn=cmd_start)

    sp = sub.add_parser("gate", help="起跑门＋建分支＋置进行中")
    common(sp)
    sp.add_argument("--id", help="任务 id（缺省＝队列序第一个待跑）")
    sp.set_defaults(fn=cmd_gate)

    sp = sub.add_parser("done", help="跑全量绿→脚本提交→写 result 置完成")
    common(sp)
    sp.add_argument("--id", required=True)
    sp.add_argument("--type", required=True, choices=("feat", "fix", "refactor"),
                    help="提交信息类型")
    sp.add_argument("--tests", required=True, help="测试结果描述（如 '1723+248'；首段数字结构化为 tests_count）")
    sp.add_argument("--phases", default=None,
                    help="subagent 自报阶段耗时 整数分钟：实施=25,自测=8,verify=2")
    sp.set_defaults(fn=cmd_done)

    sp = sub.add_parser("fail", help="失败处置（缺省零痕迹还原；red 可 --keep-branch 红标留审）")
    common(sp)
    sp.add_argument("--id", required=True)
    sp.add_argument("--cause", required=True, choices=SKIP_CAUSES,
                    help="red|timeout 计熔断；context|interrupt 不计；ruling→阻塞")
    sp.add_argument("--reason", required=True, help="错误首行／裁断点引文")
    sp.add_argument("--keep-branch", action="store_true",
                    help="三次仍红：红标 WIP 提交留分支置阻塞（仅 --cause red）")
    sp.set_defaults(fn=cmd_fail)

    sp = sub.add_parser("report", help="晨报＋runs 追加（幂等）")
    common(sp)
    sp.set_defaults(fn=cmd_report)
    return p


def main() -> None:
    # Windows 控制台默认 GBK，锁 utf-8 保证主 agent 能读 JSON/报错里的中文
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    args = build_parser().parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
