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


def queue_skip(queue_path: Path) -> set[Path]:
    """队列文件与同目录晨报不入库，脏检查显式排除防误报。"""
    skip = {queue_path.resolve()}
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
