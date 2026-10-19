#!/usr/bin/env python3
"""夜队列机械循环 runner —— 起跑门/建分支/状态写回/失败还原/熔断计数/晨报骨架。

分层协议（见 SKILL.md 执行循环）：主 agent 常驻调度，循环中每步调本脚本；派 subagent 与裁断判断归主 agent，本脚本只做确定性机械动作。
用法：python run_queue.py <start|gate|done|fail|report> --queue PATH [...]；stdout 一行 JSON（ok 字段），致命错误 stderr 一行说明 exit 1。
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

from ruamel.yaml import YAML

SKIP_CAUSES = ("red", "timeout", "context", "interrupt", "ruling")
CIRCUIT_CAUSES = ("red", "timeout")  # 仅红修不动/超时计入熔断
DUE_FMT = "%Y-%m-%dT%H:%M"


def die(msg: str) -> None:
    print(msg, file=sys.stderr)
    sys.exit(1)


def emit(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False))


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    # git 输出是 utf-8；不锁编码在 Windows 上会按 GBK 读崩（中文/特殊字节）
    proc = subprocess.run(["git", *args], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if check and proc.returncode != 0:
        die(f"git {' '.join(args)} 失败：{proc.stderr.strip()}")
    return proc


def repo_root() -> Path:
    proc = git("rev-parse", "--show-toplevel")
    return Path(proc.stdout.strip())


def load_queue(path: Path) -> dict:
    if not path.is_file():
        die(f"队列不存在：{path}")
    yml = YAML()  # round-trip：保注释保键序
    with open(path, encoding="utf-8") as fp:  # Windows 平台默认编码是 GBK，必须锁 utf-8
        data = yml.load(fp)
    if not isinstance(data, dict) or not isinstance(data.get("tasks"), list):
        die("队列格式错：缺 tasks 列表")
    return data


def dump_queue(path: Path, data: dict) -> None:
    yml = YAML()
    with open(path, "w", encoding="utf-8") as fp:
        yml.dump(data, fp)


def tonight_of(data: dict) -> dict:
    t = data.get("tonight")
    if not isinstance(t, dict) or "deadline" not in t:
        die("tonight 缺失——先跑 start 开工")
    return t


def parse_deadline(text: str) -> datetime:
    """接受 'HH:MM'（取最近的未来时刻）或完整 ISO 'YYYY-MM-DDTHH:MM'。"""
    try:
        return datetime.strptime(text, DUE_FMT)
    except ValueError:
        pass
    try:
        hh, mm = (int(x) for x in text.split(":"))
    except ValueError:
        die(f"deadline 格式错：{text}（用 HH:MM 或 YYYY-MM-DDTHH:MM）")
    now = datetime.now()
    cand = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
    if cand <= now:
        cand += timedelta(days=1)
    return cand


def task_index(data: dict, tid: str) -> int:
    for i, task in enumerate(data["tasks"]):
        if task.get("id") == tid:
            return i
    die(f"队列无此任务：{tid}")


def find_task(data: dict, tid: str) -> dict:
    return data["tasks"][task_index(data, tid)]


def next_runnable(data: dict) -> dict | None:
    """队列序第一个 `待跑`（顺延/跳过/阻塞须整肃回待跑或显式 --id 才重选）。"""
    for task in data["tasks"]:
        if task.get("status") == "待跑":
            return task
    return None


def prev_tip(data: dict, idx: int) -> str:
    """分支链基点：本任务之前最近一个完成任务的 commit，否则 base。"""
    for task in reversed(data["tasks"][:idx]):
        if task.get("status") == "完成" and (task.get("result") or {}).get("commit"):
            return task["result"]["commit"]
    base = data.get("base")
    if not base:
        die("base 缺失——先跑 start 开工")
    return base


def branch_name(date: str, tid: str) -> str:
    return f"overnight/{date}/{tid}"


def assert_clean_tree(queue_path: Path) -> None:
    """树净校验；队列文件与同目录晨报不入库，显式排除防误报。"""
    root = repo_root()
    skip = {queue_path.resolve()}
    skip |= {p.resolve() for p in queue_path.parent.glob("report-*.md")}
    for line in git("status", "--porcelain").stdout.splitlines():
        rel = line[3:].strip().strip('"')
        rel = rel.split(" -> ", 1)[-1] if " -> " in rel else rel
        if (root / rel).resolve() not in skip:
            die(f"工作树不净（{rel}）——先还原再继续")


def cmd_start(args: argparse.Namespace) -> None:
    """写 base＋tonight 五数值（开工时用户定档后调）。"""
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
    deadline = datetime.strptime(t["deadline"], DUE_FMT)
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
    """写 result 置完成（前提：已在任务分支、已提交、树净、verify 逐项过）。"""
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
    assert_clean_tree(path)
    commit = git("rev-parse", "HEAD").stdout.strip()
    tip = prev_tip(data, task_index(data, args.id))
    if commit == tip:
        die("无提交——尚未到达提交点")
    deadline = datetime.strptime(t["deadline"], DUE_FMT)
    grace_end = deadline + timedelta(minutes=t["grace_min"])
    now = datetime.now()
    if now > grace_end:
        die(f"已过宽限（deadline+{t['grace_min']}min）——改走 fail --cause timeout")
    started = datetime.strptime(task["started_at"], DUE_FMT)
    elapsed = max(0, int((now - started).total_seconds() // 60))
    overtime = elapsed > task["estimate_min"] * t["timeout_x"]
    task["status"] = "完成"
    task["result"] = {
        "branch": name, "commit": commit, "tests": args.tests,
        "elapsed_min": elapsed,
    }
    t["circuit_count"] = 0  # 成功清零
    dump_queue(path, data)
    emit({"ok": True, "id": args.id, "commit": commit, "elapsed_min": elapsed,
          "overtime": overtime})


def cmd_fail(args: argparse.Namespace) -> None:
    """零痕迹还原＋置跳过/阻塞＋熔断计数（仅 red/timeout 计）。"""
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

    # 还原：已跟踪文件回基点（checkout -f）→ 清 scope 内自产未跟踪 → 删失败分支
    git("checkout", "-f", tip)
    scope = task.get("scope") or []
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

    kind = "阻塞" if args.cause == "ruling" else "跳过"
    task["status"] = kind
    task["reason"] = f"[{args.cause}] {args.reason}"
    task["result"] = None
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
    tasks = data["tasks"]
    counts = {s: sum(1 for x in tasks if x.get("status") == s)
              for s in ("完成", "顺延", "跳过", "阻塞")}
    now = datetime.now()
    date = t["date"]

    lines = [
        f"# 夜队列晨报 {date}",
        "",
        f"- base：`{data.get('base')}`",
        f"- deadline：{t['deadline']}（宽限 {t['grace_min']}min／超时 {t['timeout_x']}×estimate／熔断 {t['circuit_limit']}／缓冲 {t['buffer_min']}min）",
        f"- 运行窗：{t.get('started_at', '?')} → {now.strftime(DUE_FMT)}",
        f"- 完成 {counts['完成']} · 顺延 {counts['顺延']} · 跳过 {counts['跳过']} · 阻塞 {counts['阻塞']}",
        "",
        "| 任务 | 状态 | 分支 | commit | 测试 | 备注 |",
        "|---|---|---|---|---|---|",
    ]
    for task in tasks:
        res = task.get("result") or {}
        note = task.get("reason") or ""
        lines.append(
            f"| {task.get('id')} | {task.get('status')} | {res.get('branch', '—')} "
            f"| {(res.get('commit') or '—')[:7]} | {res.get('tests', '—')} | {note or '—'} |"
        )
    pending = [x for x in tasks if x.get("status") in ("顺延", "跳过", "阻塞")]
    if pending:
        lines += ["", "## 未完成项（原因＋建议处置）", ""] + [
            f"- **{t2.get('id')}** `{t2.get('status')}`：{t2.get('reason') or '—'}"
            for t2 in pending]
    blocked = [x for x in tasks if x.get("status") == "阻塞"]
    if blocked:
        lines += ["", "## 待裁点（阻塞条目）", ""] + [
            f"- {t2.get('id')}：{t2.get('reason')}" for t2 in blocked]
    lines += ["", "## 早审指引（照队列序逐支，每支三步）", "",
              "1. 看变更：`git diff <前支tip>..<本支tip>`（首支＝`<base>..<首支>`）；可 checkout 亲验跑 `test_cmd`。",
              "2. 裁断：过 → `git merge <支> --no-ff` 入 dev；否 → 不合、记待办（含分支名）继续下一支；拿不准 → 停，余支记待办。",
              "3. 全过完：删链 `git branch -d overnight/<日期>/*` ＋归档队列完成条目。", ""]
    report = path.parent / f"report-{date}.md"
    report.write_text("\n".join(lines), encoding="utf-8")

    run_row = {"date": date, "base": data.get("base"), "deadline": t["deadline"],
               "完成": counts["完成"], "顺延": counts["顺延"],
               "跳过": counts["跳过"], "阻塞": counts["阻塞"]}
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

    def common(sp: argparse.ArgumentParser) -> argparse.ArgumentParser:
        sp.add_argument("--queue", required=True, help="queue.yaml 路径")

    sp = sub.add_parser("start", help="写 base＋tonight 五数值（开工定档后调）")
    common(sp)
    sp.add_argument("--deadline", default="07:00", help="HH:MM（最近未来时刻）或完整 ISO")
    sp.add_argument("--grace", type=int, default=45, help="宽限分钟（缺省 45）")
    sp.add_argument("--timeout-x", type=float, default=2.0, help="超时倍数（缺省 2×estimate）")
    sp.add_argument("--circuit", type=int, default=2, help="连跳熔断阈值（缺省 2）")
    sp.add_argument("--buffer", type=int, default=15, help="测试缓冲分钟（缺省 15）")
    sp.set_defaults(fn=cmd_start)

    sp = sub.add_parser("gate", help="起跑门＋建分支＋置进行中")
    common(sp)
    sp.add_argument("--id", help="任务 id（缺省＝队列序第一个待跑）")
    sp.set_defaults(fn=cmd_gate)

    sp = sub.add_parser("done", help="写 result 置完成")
    common(sp)
    sp.add_argument("--id", required=True)
    sp.add_argument("--tests", required=True, help="测试结果描述（如 '1723+248'）")
    sp.set_defaults(fn=cmd_done)

    sp = sub.add_parser("fail", help="零痕迹还原＋跳过/阻塞＋熔断计数")
    common(sp)
    sp.add_argument("--id", required=True)
    sp.add_argument("--cause", required=True, choices=SKIP_CAUSES,
                    help="red|timeout 计熔断；context|interrupt 不计；ruling→阻塞")
    sp.add_argument("--reason", required=True, help="错误首行／裁断点引文")
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
