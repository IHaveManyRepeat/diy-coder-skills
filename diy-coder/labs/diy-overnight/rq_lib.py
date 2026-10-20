#!/usr/bin/env python3
"""夜队列 runner 共享库 —— git/队列 IO/时间解析/校验原语（run_queue.py 专用内部件）。"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

from ruamel.yaml import YAML

SKIP_CAUSES = ("red", "timeout", "context", "interrupt", "ruling")
CIRCUIT_CAUSES = ("red", "timeout")  # 仅红修不动/超时计入熔断
DUE_FMT = "%Y-%m-%dT%H:%M:%S"
DUE_FMT_MIN = "%Y-%m-%dT%H:%M"  # 旧数据兼容（升级前入库的分钟粒度时间戳）
DEFAULT_PARAMS = {"grace_min": 45, "timeout_x": 2.0, "circuit_limit": 2, "buffer_min": 15}


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


def parse_dt(text: str) -> datetime:
    for fmt in (DUE_FMT, DUE_FMT_MIN):
        try:
            return datetime.strptime(text, fmt)
        except (ValueError, TypeError):
            continue
    die(f"时间格式错：{text}")


def parse_deadline(text: str) -> datetime:
    """接受 'HH:MM'（取最近的未来时刻）或完整 ISO 'YYYY-MM-DDTHH:MM[:SS]'。"""
    for fmt in (DUE_FMT, DUE_FMT_MIN):
        try:
            return datetime.strptime(text, fmt)
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


def parse_phases(text: str | None) -> dict | None:
    """'实施=25,自测=8,verify=2' → {'实施':25,'自测':8,'verify':2}；整数分钟（subagent 自报）。"""
    if not text:
        return None
    out: dict[str, int] = {}
    for part in text.split(","):
        k, _, v = part.partition("=")
        k, v = k.strip(), v.strip()
        if not k or not v.isdigit():
            die(f"--phases 格式错：{text}（用 实施=25,自测=8,verify=2）")
        out[k] = int(v)
    return out or None


def tests_count_of(text: str) -> int | None:
    """取描述首段连续数字为结构化测试数（如 '1723+248' → 1723）；无数字返回 None。"""
    m = re.match(r"\d+", (text or "").strip())
    return int(m.group()) if m else None


def run_tests(cmd: str) -> tuple[bool, str, int]:
    """以 shell 在仓根跑命令，返回 (是否绿, 合并输出, 墙钟秒)。"""
    t0 = datetime.now()
    proc = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", cwd=repo_root())
    sec = max(0, int((datetime.now() - t0).total_seconds()))
    return proc.returncode == 0, (proc.stdout or "") + (proc.stderr or ""), sec


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


def _peek_queue(path: Path) -> dict | None:
    """静默读队列（脏检查排除用；失败返回 None，不 die）。"""
    try:
        with open(path, encoding="utf-8") as fp:
            data = YAML().load(fp)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def relay_chain_paths(queue_path: Path) -> list[Path]:
    """沿 next 下行＋relay_from 上行递归解析整条接力链（防环；缺失/坏文件跳过该支）。"""
    out: list[Path] = []
    seen: set[Path] = set()
    stack = [queue_path]
    while stack:
        cur = stack.pop()
        key = cur.resolve()
        if key in seen or not key.is_file():
            continue
        seen.add(key)
        out.append(cur)
        data = _peek_queue(cur) or {}
        for rel in (data.get("next") or []):
            if isinstance(rel, str):
                stack.append(resolve_next_path(cur, rel))
        tonight = data.get("tonight")
        src = tonight.get("relay_from") if isinstance(tonight, dict) else None
        if isinstance(src, str):
            stack.append(Path(src))
    return out


def queue_skip(queue_path: Path) -> set[Path]:
    """队列文件、同目录晨报与接力链队列不入库，脏检查显式排除防误报。"""
    skip = {p.resolve() for p in relay_chain_paths(queue_path)}
    skip |= {p.resolve() for p in queue_path.parent.glob("report-*.md")}
    return skip


def changed_rels(skip: set[Path]) -> list[str]:
    """工作树相对 HEAD 的全部改动路径（已跟踪+未跟踪），排除 skip 集。"""
    root = repo_root()
    rels: list[str] = []
    for line in git("status", "--porcelain").stdout.splitlines():
        rel = line[3:].strip().strip('"')
        rel = rel.split(" -> ", 1)[-1] if " -> " in rel else rel
        if (root / rel).resolve() in skip:
            continue
        rels.append(rel)
    return rels


def non_scope(rels: list[str], scope: list[str]) -> list[str]:
    """落在 scope 白名单之外的改动路径；scope 空＝不设限（返回空）。"""
    if not scope:
        return []
    return [r for r in rels
            if not any(r == s or r.startswith(s.rstrip("/") + "/") for s in scope)]


def passes_start_gate(now: datetime, estimate_min: int, buffer_min: int,
                      deadline: datetime) -> bool:
    """起跑门：now+estimate+buffer 不晚于 deadline 才放行（gate/relay 共用）。"""
    return now + timedelta(minutes=estimate_min + buffer_min) <= deadline


def make_tonight(now: datetime, date: str, deadline: datetime, params: dict,
                 baseline_min: float | None, relay_from: str | None = None) -> dict:
    """构建 tonight 块（start/relay 共用）；params＝grace_min/timeout_x/circuit_limit/buffer_min。"""
    tonight = {
        "date": date,
        "deadline": deadline.strftime(DUE_FMT),
        "grace_min": params["grace_min"],
        "timeout_x": params["timeout_x"],
        "circuit_limit": params["circuit_limit"],
        "buffer_min": params["buffer_min"],
        "circuit_count": 0,
        "started_at": now.strftime(DUE_FMT),
        "baseline_min": baseline_min,
    }
    if relay_from is not None:
        tonight["relay_from"] = relay_from
    return tonight


def tonight_from_source(src: dict, now: datetime, relay_from: str) -> dict:
    """接力继承：date/deadline/五数值/baseline_min 照搬，circuit_count 清零、started_at=接力时刻。"""
    params = {k: src.get(k, v) for k, v in DEFAULT_PARAMS.items()}
    return make_tonight(now, src["date"], parse_dt(src["deadline"]), params,
                        src.get("baseline_min"), relay_from)


def resolve_next_path(queue_path: Path, rel: str) -> Path:
    """next 条目解析：相对路径以队列文件所在目录为基准。"""
    p = Path(rel)
    return p if p.is_absolute() else queue_path.parent / p


def relay_decision(data: dict, src_tonight: dict, queue_path: Path, now: datetime) -> dict:
    """接力判定（不写盘）：源队列无待跑→按 next 逐候选；命中返回目标队列与首个待跑任务。"""
    if next_runnable(data) is not None:
        die("源队列仍有待跑条目——禁止跳棒接力")
    warnings: list[str] = []
    entries = data.get("next") or []
    if not isinstance(entries, list):
        die("next 须为列表")
    if src_tonight.get("circuit_count", 0) >= src_tonight.get(
            "circuit_limit", DEFAULT_PARAMS["circuit_limit"]):
        return {"ok": False, "reason": "熔断", "warnings": warnings}
    deadline = parse_dt(src_tonight["deadline"])
    buffer_min = src_tonight.get("buffer_min", DEFAULT_PARAMS["buffer_min"])
    date = src_tonight["date"]
    for rel in entries:
        if not isinstance(rel, str):
            warnings.append(f"next 条目非字符串：{rel!r}")
            continue
        target_path = resolve_next_path(queue_path, rel)
        if not target_path.is_file():
            warnings.append(f"{rel}：文件不存在")
            continue
        target = load_queue(target_path)
        if any(x.get("status") == "进行中" for x in target["tasks"]):
            warnings.append(f"{rel}：存在进行中条目")
            continue
        tt = target.get("tonight")
        if isinstance(tt, dict) and tt.get("date") == date:
            warnings.append(f"{rel}：本晚已在接力链中")
            continue
        task = next_runnable(target)
        if task is None:
            warnings.append(f"{rel}：无待跑条目")
            continue
        if not passes_start_gate(now, task["estimate_min"], buffer_min, deadline):
            return {"ok": False, "reason": "起跑门不过", "queue": str(target_path),
                    "warnings": warnings}
        return {"ok": True, "queue": str(target_path), "id": task["id"],
                "title": task.get("title"), "estimate_min": task["estimate_min"],
                "warnings": warnings}
    return {"ok": False, "reason": "无后续队列", "warnings": warnings}


def apply_relay(target: dict, now: datetime, src_tonight: dict, src_path: str) -> None:
    """接力初始化（不写盘）：base=当前 HEAD、tonight=继承值、relay_from=源队列。"""
    target["base"] = git("rev-parse", "HEAD").stdout.strip()
    target["tonight"] = tonight_from_source(src_tonight, now, src_path)


def report_filename(queue_path: Path) -> Path:
    """晨报路径＝report-<队列文件stem>.md（同晚多队列不撞名）。"""
    return queue_path.parent / f"report-{queue_path.stem}.md"


def status_counts(tasks: list) -> dict:
    """按终态统计条目数。"""
    return {s: sum(1 for x in tasks if x.get("status") == s)
            for s in ("完成", "顺延", "跳过", "阻塞")}


def fmt_val(res: dict, key: str, suffix: str = "") -> str:
    v = res.get(key)
    return f"{v}{suffix}" if v is not None else "—"


def fmt_elapsed(res: dict) -> str:
    if res.get("elapsed_min") is not None:
        return f"{res['elapsed_min']}min"
    if res.get("elapsed_sec") is not None:  # 失败任务只记秒
        return f"{round(res['elapsed_sec'] / 60, 1)}min"
    return "—"


def render_report(data: dict, now: datetime) -> str:
    """晨报正文（队列序＝审核序）；纯渲染不写盘。"""
    t = tonight_of(data)
    tasks = data["tasks"]
    counts = status_counts(tasks)
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
    # 早审 diff 入口（2026-10-19 用户要求，Q-001 173d304 迁入）：逐支给出可直接复制的
    # `git diff 前支tip..本支tip`；摘要取提交 message 体，剔除 basis/测试 尾段
    diffs = []
    for i, task in enumerate(tasks):
        res = task.get("result") or {}
        if task.get("status") == "完成" and res.get("commit"):
            body = "；".join(git("log", "-1", "--format=%B", res["commit"]).stdout.splitlines()[1:])
            desc = [s.strip() for s in body.split("；")
                    if s.strip() and not s.strip().startswith(("basis", "测试"))]
            diffs.append(f"- {task.get('id')}：`git diff {prev_tip(data, i)[:7]}..{res['commit'][:7]}`"
                         f"（{'；'.join(desc)}）")
    if diffs:
        lines += ["", "## 早审 diff 入口（队列序）", ""] + diffs
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
    return "\n".join(lines)
