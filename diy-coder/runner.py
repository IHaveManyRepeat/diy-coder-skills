#!/usr/bin/env python3
# runner.py — diy-coder 循环编排器（外部循环器，D-4：spawn 无头 claude CLI 执行
# diy-build-loop 单次迭代，按 sprint.yaml 写回状态决定继续/停止）。
# 用法：python runner.py [--project-root DIR] [--claude-cmd claude ...] [--max-retries N]
import argparse
import os
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

import yaml

TERMINAL = {"done", "blocked"}
DEFAULT_MAX_RETRIES = 2  # R-4：重试上限 2 次封顶


def load_sprint(sprint_path: Path) -> dict:
    # trace: S-10 AC-10.2 AC-10.1 D-4 读取 sprint.yaml；final 硬门（非 final 拒绝，路由 diy-sprint）；
    # 语法损坏/形状异常一行中文报错（对抗审查 R3，BUG-011 同类：错误路径与主路径同等标准）
    try:
        doc = yaml.safe_load(sprint_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        raise SystemExit(f"[runner] sprint.yaml 解析失败（{e.__class__.__name__}）："
                         f"{sprint_path}——修复后重跑")
    proj = doc.get("project") if isinstance(doc, dict) else None
    if not isinstance(proj, dict) or proj.get("status") != "final":
        raise SystemExit(f"[runner] sprint.yaml 非 final，先运行 diy-sprint: {sprint_path}")
    return doc


def save_sprint(sprint_path: Path, doc: dict) -> None:
    # trace: S-10 AC-10.3 原子写回（tmp + replace），防读者见到半写文件
    tmp = sprint_path.with_suffix(sprint_path.suffix + ".tmp")
    tmp.write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False), encoding="utf-8")
    os.replace(tmp, sprint_path)


def pick_next(doc: dict):
    # trace: S-10 AC-10.2 挑第一个非终态任务；done/blocked 跳过即断点续跑（不重复执行）
    for task in doc.get("tasks", []):
        if task.get("status") not in TERMINAL:
            return task
    return None


def spawn_iteration(claude_cmd: list, project_root: Path, story_id: str,
                    allow: list) -> int:
    # trace: S-10 AC-10.1 D-4 R-1 spawn 无头 claude CLI 执行 diy-build-loop 单次迭代
    # stdin 继承（不重定向）：本 GLM 兼容 harness 按 stdin 句柄形态决定工具面——
    # DEVNULL/PIPE 会剥离子会话命令执行工具（实测复现）；claude -p 的 prompt 走 argv，
    # 不读 stdin，继承不构成人工输入通道（无人值守语义不变）
    # --permission-mode acceptEdits + --allowedTools 白名单：R-1 定稿——文件编辑自动接受，
    # 命令执行仅放行白名单（TDD red/green 必需），禁 skip-permissions；
    # 白名单默认 Bash/PowerShell 的 python+ruff 前缀，其他 stack 经 --allow 传入（语言无关）
    prompt = (
        f"运行 diy-build-loop skill 处理任务 {story_id}：读取本项目 diy-coder.yaml 解析 "
        f"output_dir 下的 sprint.yaml，把任务 {story_id} 从当前状态驱动到终态"
        f"（done 或 blocked），每次状态转移立即写回 sprint.yaml 并更新 project.updated。"
        f"无人值守模式：不要提问、不要等待人工确认。"
        f"提示：本会话的命令执行工具（PowerShell）是核心工具、不进入 ToolSearch 索引，"
        f"直接调用即可；先用 ToolSearch 搜索来确认其存在会得到假阴性。"
    )
    proc = subprocess.run(
        claude_cmd + ["-p", prompt,
                      "--output-format", "json",
                      "--permission-mode", "acceptEdits",
                      "--allowedTools"] + allow,
        cwd=str(project_root),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
    )
    return proc.returncode


def find_task(doc: dict, story_id: str) -> dict:
    # trace: S-10 AC-10.2 在（可能已被子进程写回的）文档中定位任务条目
    for task in doc.get("tasks", []):
        if task.get("story") == story_id:
            return task
    raise KeyError(story_id)


def drive_task(sprint_path: Path, claude_cmd: list, project_root: Path,
               story_id: str, max_retries: int, allow: list) -> str:
    # trace: S-10 AC-10.3 TC-10.3.1 驱动单任务：初次 + 至多 max_retries 次重试，
    # 重试用尽仍非终态 → blocked 写回原因，返回由调用方继续后续任务
    for _attempt in range(1 + max_retries):
        spawn_iteration(claude_cmd, project_root, story_id, allow)
        current = find_task(load_sprint(sprint_path), story_id)
        if current.get("status") in TERMINAL:
            return current["status"]
    doc = load_sprint(sprint_path)
    current = find_task(doc, story_id)
    if current.get("status") not in TERMINAL:
        current["status"] = "blocked"
        current["blocked_reason"] = (
            f"runner 重试 {max_retries} 次用尽（迭代连续未达终态），"
            f"人工检查该任务后重跑 runner.py"
        )
        doc["project"]["updated"] = date.today().isoformat()
        save_sprint(sprint_path, doc)
    return "blocked"


def main(argv=None) -> int:
    # trace: S-10 AC-10.1 AC-10.4 TC-10.1.1 TC-10.1.2 TC-10.4.1 串行主循环：一次至多驱动一个任务
    # （不并发 spawn），直至全部任务终态
    parser = argparse.ArgumentParser(description="diy-coder 循环编排器（无人值守驱动 sprint 全部任务）")
    parser.add_argument("--project-root", default=".", help="项目根目录（默认当前目录）")
    parser.add_argument("--claude-cmd", nargs="+", default=["claude"],
                        help="claude CLI 命令及前置参数（测试注入任务桩用）")
    parser.add_argument("--max-retries", type=int, default=DEFAULT_MAX_RETRIES,
                        help="单任务重试上限（默认 2，对齐 R-4）")
    parser.add_argument("--allow", action="append", default=None,
                        help="无头会话命令白名单条目（可重复，如 'Bash(go test:*)'）；"
                             "默认 Bash/PowerShell 的 python+ruff 前缀（TDD 执行与 static_checks 必需，"
                             "语言无关——其他 stack 自行传入，本机 Windows 无头会话工具名为 PowerShell）")
    args = parser.parse_args(argv)
    allow = args.allow or [
        "Bash(python:*)", "Bash(ruff:*)",
        "PowerShell(python *)", "PowerShell(ruff *)",
    ]

    # trace: S-10 AC-10.1 L2 边界修复——Windows 上 claude 是 claude.cmd，
    # CreateProcess 不解析 PATHEXT，直接 spawn "claude" 会 FileNotFoundError；
    # shutil.which 按 PATHEXT 解析出全路径（绝对路径/桩命令不受影响）
    resolved = shutil.which(args.claude_cmd[0])
    if resolved:
        args.claude_cmd[0] = resolved
    # trace: S-10 AC-10.1 TC-10.1.2 BUG-011 前置显式校验：外部依赖缺失给一行中文报错，
    # 不落 spawn 层 FileNotFoundError 裸栈
    if resolved is None:
        print(f"[runner] 找不到命令 {args.claude_cmd[0]}（PATH 中无此可执行文件）——"
              f"安装 claude CLI，或用 --claude-cmd 指定完整路径", file=sys.stderr)
        return 1

    root = Path(args.project_root).resolve()
    cfg_path = root / "diy-coder.yaml"
    if not cfg_path.exists():
        print(f"[runner] 找不到 {cfg_path}——请在项目根目录运行，或用 --project-root 指定",
              file=sys.stderr)
        return 1
    try:
        config = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        print(f"[runner] diy-coder.yaml 解析失败（{e.__class__.__name__}）：{cfg_path}",
              file=sys.stderr)
        return 1
    if not isinstance(config, dict):
        print(f"[runner] diy-coder.yaml 顶层不是映射：{cfg_path}", file=sys.stderr)
        return 1
    output_dir = root / (config.get("paths") or {}).get("output_dir", "diy-output")
    sprint_path = output_dir / "sprint.yaml"
    if not sprint_path.exists():
        print(f"[runner] 找不到 {sprint_path}——先运行 diy-sprint 生成 sprint.yaml",
              file=sys.stderr)
        return 1
    load_sprint(sprint_path)

    while True:
        doc = load_sprint(sprint_path)
        task = pick_next(doc)
        if task is None:
            break
        story_id = task["story"]
        outcome = drive_task(sprint_path, args.claude_cmd, root, story_id,
                             args.max_retries, allow)
        print(f"[runner] {story_id} → {outcome}", flush=True)

    print("[runner] 全部任务已到终态（done/blocked），退出", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
