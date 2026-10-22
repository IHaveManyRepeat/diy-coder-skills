#!/usr/bin/env python3
"""夜队列机械循环 runner —— 起跑门/建分支/状态写回/失败红标留审/熔断计数/晨报骨架。

分层协议（见 SKILL.md 执行循环）：主 agent 常驻调度，循环中每步调本脚本；派 subagent 与裁断判断归主 agent，本脚本只做确定性机械动作。
权威提交门在 done：脚本自跑 test_cmd，全量绿才统一 stage+提交（无半红入链）。
用法：python run_queue.py <start|gate|done|fail|report> --queue PATH [...]；stdout 一行 JSON（ok 字段），致命错误 stderr 一行说明 exit 1。
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

from rq_lib import (CIRCUIT_CAUSES, DEFAULT_PARAMS, DUE_FMT, SKIP_CAUSES, apply_relay,
                    branch_name, changed_rels, die, dump_queue, emit, find_task, git,
                    load_queue, make_tonight, next_runnable, non_scope, parse_deadline,
                    parse_dt, parse_phases, passes_start_gate, prev_tip, queue_skip,
                    relay_decision, render_report, report_filename, run_tests,
                    status_counts, task_index, tests_count_of, tonight_of)


def cmd_start(args: argparse.Namespace) -> None:
    """写 base＋tonight 五数值＋started_at/baseline_min（开工时用户定档后调）。"""
    path = Path(args.queue)
    data = load_queue(path)
    busy = [t["id"] for t in data["tasks"] if t.get("status") == "进行中"]
    if busy:
        die(f"存在进行中条目 {busy}——先按中断恢复处置（fail --cause interrupt）")
    now = datetime.now()
    params = {"grace_min": args.grace, "timeout_x": args.timeout_x,
              "circuit_limit": args.circuit, "buffer_min": args.buffer}
    data["base"] = git("rev-parse", "HEAD").stdout.strip()
    data["tonight"] = make_tonight(now, now.strftime("%Y-%m-%d"),
                                   parse_deadline(args.deadline), params, args.baseline_min)
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
    if not passes_start_gate(now, task["estimate_min"], t["buffer_min"],
                             parse_dt(t["deadline"])):
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
        die(f"全量红（回修后重跑 done；修不动则 fail --cause red）：\n{tail}")

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
    """失败处置（产物不浪费）：有改动→红标 WIP 提交留分支＋切回绿链基点（下一条从最近绿点起跑）；无改动→删空分支。记 result{elapsed_sec,cause[,branch,commit,kept]}。"""
    if args.cause not in SKIP_CAUSES:
        die(f"cause 须为 {SKIP_CAUSES}")
    if not args.reason.strip():
        die("reason 必填")
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

    # 红标留审：产物全在 scope 内才打包；越界属违规，交人处置，不自动打包
    rels = changed_rels(queue_skip(path))
    bad = non_scope(rels, scope)
    if bad:
        die(f"scope 外改动（{bad[0]}）——先处置越界再 fail（越界不自动打包）")
    wip = None
    if rels:
        if scope:
            git("add", "--", *scope)
        else:
            git("add", "-A")
        git("commit", "-m", f"wip: 夜队列 {args.id} {task.get('title') or args.id}（失败留审·{args.cause}）",
            "-m", f"reason: {args.reason}")
        wip = git("rev-parse", "HEAD").stdout.strip()
    git("checkout", "-f", tip)  # 工作树回绿链基点；红分支保留，绿链不受污染
    if not wip and git("show-ref", "--verify", "--quiet", f"refs/heads/{name}", check=False).returncode == 0:
        git("branch", "-D", name)  # 无产物：空分支无留审价值

    kind = "阻塞" if (args.cause == "ruling" or wip) else "跳过"
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


def cmd_report(args: argparse.Namespace) -> None:
    """晨报（队列同目录·不入库）＋runs 追加（同 date 行幂等更新）。"""
    path = Path(args.queue)
    data = load_queue(path)
    t = tonight_of(data)
    now = datetime.now()
    date = t["date"]
    report = report_filename(path)
    report.write_text(render_report(data, now), encoding="utf-8")
    tasks = data["tasks"]
    counts = status_counts(tasks)
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


def cmd_relay(args: argparse.Namespace) -> None:
    """队列接力：源队列无待跑后按 next 判定，并把下一队列初始化（base/tonight/relay_from）。"""
    path = Path(args.queue)
    data = load_queue(path)
    t = tonight_of(data)
    now = datetime.now()
    decision = relay_decision(data, t, path, now)
    if not decision["ok"]:
        emit(decision)
        return
    dirty = changed_rels(queue_skip(path))
    if dirty:
        die(f"工作树不净（{dirty[0]}）——先处置再接力")
    target_path = Path(decision["queue"])
    target = load_queue(target_path)
    apply_relay(target, now, t, str(path.resolve()))
    dump_queue(target_path, target)
    emit({**decision, "deadline": target["tonight"]["deadline"], "base": target["base"]})


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="run_queue", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    def common(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--queue", required=True, help="queue.yaml 路径")

    sp = sub.add_parser("start", help="写 base＋tonight（开工定档后调）")
    common(sp)
    sp.add_argument("--deadline", default="07:00", help="HH:MM（最近未来时刻）或完整 ISO")
    sp.add_argument("--grace", type=int, default=DEFAULT_PARAMS["grace_min"],
                    help="宽限分钟（缺省 45）")
    sp.add_argument("--timeout-x", type=float, default=DEFAULT_PARAMS["timeout_x"],
                    help="超时倍数（缺省 2×estimate）")
    sp.add_argument("--circuit", type=int, default=DEFAULT_PARAMS["circuit_limit"],
                    help="连跳熔断阈值（缺省 2）")
    sp.add_argument("--buffer", type=int, default=DEFAULT_PARAMS["buffer_min"],
                    help="测试缓冲分钟（缺省 15）")
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

    sp = sub.add_parser("fail", help="失败处置（有产物红标留审：WIP 提交留分支＋切回绿链基点）")
    common(sp)
    sp.add_argument("--id", required=True)
    sp.add_argument("--cause", required=True, choices=SKIP_CAUSES,
                    help="red|timeout 计熔断；context|interrupt 不计；ruling→阻塞")
    sp.add_argument("--reason", required=True, help="错误首行／裁断点引文")
    sp.set_defaults(fn=cmd_fail)

    sp = sub.add_parser("relay", help="队列接力：按 next 判定并初始化下一队列")
    common(sp)
    sp.set_defaults(fn=cmd_relay)

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
