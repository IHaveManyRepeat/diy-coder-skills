#!/usr/bin/env python3
# runner.py — diy-coder 循环编排器（外部循环器，D-4：spawn 无头 claude CLI 执行
# diy-build-loop 单次迭代，按 sprint.yaml 写回状态决定继续/停止）。
# 用法：python runner.py [--project-root DIR] [--claude-cmd claude ...] [--max-retries N]
#       [--instance NAME] [--skip-augment | --augment-only | --reopen-failed]
import argparse
import os
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

import yaml

TERMINAL = {"已完成", "已阻塞"}
DEFAULT_MAX_RETRIES = 2  # R-4：重试上限 2 次封顶
# trace: FR-4.5 D-9 实例名白名单（与 viewer/help 同源）：字母数字开头和结尾，中间可含 . _ -。
# 首字符字母数字拒绝点目录/分隔符；末字符禁点（Windows 尾点目录被静默折叠，b. ≡ b 破坏实例隔离）
INSTANCE_RE = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9_-])?")


def load_sprint(sprint_path: Path) -> dict:
    # trace: S-10 AC-10.2 AC-10.1 D-4 读取 sprint.yaml；已定稿硬门（非 已定稿 拒绝，路由 diy-sprint）；
    # 语法损坏/形状异常一行中文报错（对抗审查 R3，BUG-011 同类：错误路径与主路径同等标准）
    try:
        doc = yaml.safe_load(sprint_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        raise SystemExit(f"[runner] sprint.yaml 解析失败（{e.__class__.__name__}）："
                         f"{sprint_path}——修复后重跑")
    proj = doc.get("project") if isinstance(doc, dict) else None
    if not isinstance(proj, dict) or proj.get("status") != "已定稿":
        raise SystemExit(f"[runner] sprint.yaml 非已定稿，先运行 diy-sprint: {sprint_path}")
    return doc


def save_sprint(sprint_path: Path, doc: dict) -> None:
    # trace: S-10 AC-10.3 原子写回（tmp + replace），防读者见到半写文件
    tmp = sprint_path.with_suffix(sprint_path.suffix + ".tmp")
    tmp.write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False), encoding="utf-8")
    os.replace(tmp, sprint_path)


def pick_next(doc: dict):
    # trace: S-10 AC-10.2 挑第一个非终态任务；已完成/已阻塞 跳过即断点续跑（不重复执行）
    for task in doc.get("tasks", []):
        if task.get("status") not in TERMINAL:
            return task
    return None


def spawn_iteration(claude_cmd: list, project_root: Path, story_id: str,
                    allow: list, instance: str = None) -> int:
    # trace: S-10 AC-10.1 D-4 R-1 spawn 无头 claude CLI 执行 diy-build-loop 单次迭代
    # trace: FR-4.5 D-9（finding: diy-build-loop/enhancement-1）实例模式经 prompt 透传
    # --instance 激活参数，子会话按各技能 On Activation 约定解析到 <output_dir>/<name>/；
    # 无实例时不加任何前缀（主线 prompt 逐字节等价现状）
    # stdin 继承（不重定向）：本 GLM 兼容 harness 按 stdin 句柄形态决定工具面——
    # DEVNULL/PIPE 会剥离子会话命令执行工具（实测复现）；claude -p 的 prompt 走 argv，
    # 不读 stdin，继承不构成人工输入通道（无人值守语义不变）
    # --permission-mode acceptEdits + --allowedTools 白名单：R-1 定稿——文件编辑自动接受，
    # 命令执行仅放行白名单（TDD red/green 必需），禁 skip-permissions；
    # 白名单默认 Bash/PowerShell 的 python+ruff 前缀，其他 stack 经 --allow 传入（语言无关）
    prompt = _instance_clause(instance) + (
        f"运行 diy-build-loop skill 处理任务 {story_id}：读取本项目 diy-coder.yaml 解析 "
        f"output_dir 下的 sprint.yaml，把任务 {story_id} 从当前状态驱动到终态"
        f"（已完成 或 已阻塞），每次状态转移立即写回 sprint.yaml 并更新 project.updated。"
        f"无人值守模式：不要提问、不要等待人工确认。"
        f"提示：本会话的命令执行工具（PowerShell）是核心工具、不进入 ToolSearch 索引，"
        f"直接调用即可；先用 ToolSearch 搜索来确认其存在会得到假阴性。"
    )
    return _spawn(claude_cmd, project_root, prompt, allow)


def _instance_clause(instance: str) -> str:
    # 实例激活子句（build-loop 与 augment 两处 spawn 共用，保证 prompt 前缀逐字同源）
    return (
        f"激活参数 --instance {instance}（实例目录 output_dir/{instance}/，"
        f"本次运行读取与写回仅限该实例）。"
        if instance is not None else ""
    )


def _spawn(claude_cmd: list, project_root: Path, prompt: str, allow: list) -> int:
    # diy-build-loop / diy-augment 共用的 spawn 机制：--permission-mode acceptEdits +
    # --allowedTools 白名单（TDD 与补测命令仅放行 python/ruff 前缀）
    # errors="replace"：子会话（或桩）stderr 跟随宿主 locale（Windows 中文 = GBK），
    # 其增量输出若非 UTF-8 不应打断 runner——本函数只取退出码，decode 失败无信息价值
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
        errors="replace",
    )
    return proc.returncode


def spawn_augment(claude_cmd: list, project_root: Path, story_id: str,
                  allow: list, instance: str = None) -> int:
    # trace: 2026-09-13 裁定——编码后补测（diy-augment）：每任务已完成 后触发，
    # 覆盖率驱动追加 TC 写回 test-plan.yaml；本函数只负责 spawn，
    # 失败由调用方降级为一行提示，不阻塞串行主循环
    prompt = _instance_clause(instance) + (
        f"运行 diy-augment skill 对已完成任务 {story_id} 做编码后补测：读取本项目 diy-coder.yaml 解析 "
        f"output_dir 下的 sprint.yaml、test-plan.yaml 及该任务的实现面，先跑覆盖率工具采集缺口，"
        f"再按 coverage-branch / coverage-mc-dc / whitebox-path 三技法追加补测用例到 test-plan.yaml "
        f"（TC ID 延续既有每-AC 序列），执行并回填 status；最后把本次结论（通过=全部通过 / "
        f"失败=发现缺陷 / 已跳过=缺工具未跑）写入 sprint.yaml 中任务 {story_id} 的 augment 字段"
        f"（只写 augment 字段，任务 status 零写回）。"
        f"无人值守模式：不要提问、不要等待人工确认。"
        f"提示：本会话的命令执行工具（PowerShell）是核心工具、不进入 ToolSearch 索引，"
        f"直接调用即可；先用 ToolSearch 搜索来确认其存在会得到假阴性。"
    )
    return _spawn(claude_cmd, project_root, prompt, allow)


def augment_note(sprint_path: Path, story_id: str, rc: int) -> str:
    # trace: 2026-09-13 裁定——补测结论以 sprint.yaml 的 augment 字段为准
    # （AI 会话无法可靠设置退出码）；rc 仅在未留痕时作回退提示信息
    task = find_task(load_sprint(sprint_path), story_id)
    verdict = task.get("augment")
    if verdict == "通过":
        return "补测轮通过"
    if verdict == "失败":
        return "补测轮发现缺陷（待裁断）"
    if verdict == "已跳过":
        return "补测轮跳过（缺工具）"
    return f"补测轮未留痕（退出码 {rc}，不阻塞）"


def augment_summary(doc: dict) -> list:
    # trace: 2026-09-13 裁定——补测汇总（已完成 任务口径）：任务状态与补测结论正交，
    # 已阻塞 任务不参与统计；失败 时附待裁断名单（裁断三途径提示）
    pass_n = fail_n = skip_n = unrun_n = 0
    failed = []
    for task in doc.get("tasks", []):
        if task.get("status") != "已完成":
            continue
        verdict = task.get("augment")
        if verdict == "通过":
            pass_n += 1
        elif verdict == "失败":
            fail_n += 1
            failed.append(task["story"])
        elif verdict == "已跳过":
            skip_n += 1
        else:
            unrun_n += 1
    lines = [f"[runner] 补测汇总：通过 {pass_n} / 待裁断 {fail_n} / 跳过 {skip_n} / 未跑 {unrun_n}"]
    if failed:
        lines.append(
            f"[runner] 待裁断：{'、'.join(failed)}"
            f"（见 sprint.html 补测面板；--reopen-failed 批量重开）"
        )
    return lines


def reopen_augment_failed(sprint_path: Path) -> list:
    # trace: 2026-09-13 裁定——失败 裁断处置之一（代码缺陷→重开）：已完成+augment:失败
    # 批量重开（已完成→进行中、清旧结论、note 记裁断动作），随后主循环修复并重新补测；
    # 失败 的另两种处置（TC 设计问题→改 test-plan、规格问题→回 story/PRD）不经此路径
    doc = load_sprint(sprint_path)
    reopened = []
    for task in doc.get("tasks", []):
        if task.get("status") == "已完成" and task.get("augment") == "失败":
            task["status"] = "进行中"
            task.pop("augment", None)
            verdict_note = "编码后验证未通过，用户裁断重开（runner --reopen-failed）"
            prior = task.get("note")
            task["note"] = f"{prior}；{verdict_note}" if prior else verdict_note
            reopened.append(task["story"])
    if reopened:
        doc["project"]["updated"] = date.today().isoformat()
        save_sprint(sprint_path, doc)
    return reopened


def find_task(doc: dict, story_id: str) -> dict:
    # trace: S-10 AC-10.2 在（可能已被子进程写回的）文档中定位任务条目
    for task in doc.get("tasks", []):
        if task.get("story") == story_id:
            return task
    raise KeyError(story_id)


def drive_task(sprint_path: Path, claude_cmd: list, project_root: Path,
               story_id: str, max_retries: int, allow: list,
               instance: str = None) -> str:
    # trace: S-10 AC-10.3 TC-10.3.1 驱动单任务：初次 + 至多 max_retries 次重试，
    # 重试用尽仍非终态 → 已阻塞 写回原因，返回由调用方继续后续任务
    for _attempt in range(1 + max_retries):
        spawn_iteration(claude_cmd, project_root, story_id, allow, instance)
        current = find_task(load_sprint(sprint_path), story_id)
        if current.get("status") in TERMINAL:
            return current["status"]
    doc = load_sprint(sprint_path)
    current = find_task(doc, story_id)
    if current.get("status") not in TERMINAL:
        current["status"] = "已阻塞"
        current["blocked_reason"] = (
            f"runner 重试 {max_retries} 次用尽（迭代连续未达终态），"
            f"人工检查该任务后重跑 runner.py"
        )
        doc["project"]["updated"] = date.today().isoformat()
        save_sprint(sprint_path, doc)
    return "已阻塞"


def main(argv=None) -> int:
    # trace: S-10 AC-10.1 AC-10.4 TC-10.1.1 TC-10.1.2 TC-10.4.1 串行主循环：一次至多驱动一个任务
    # （不并发 spawn），直至全部任务终态
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
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
    parser.add_argument("--instance", default=None,
                        help="实例名（FR-4.5/D-9）：读写 <output_dir>/<实例名>/sprint.yaml；"
                             "默认 None = 主线平铺（零迁移）")
    parser.add_argument("--skip-augment", action="store_true",
                        help="主循环任务已完成 后不触发编码后补测（不留痕，之后可用 --augment-only 补跑）")
    parser.add_argument("--augment-only", action="store_true",
                        help="只补跑已完成 且无终结结论（通过/已跳过）的任务（失败 结论由重跑覆盖），"
                             "不驱动主循环")
    parser.add_argument("--reopen-failed", action="store_true",
                        help="批量重开补测未通过（augment:失败）的任务（已完成→进行中、清旧结论），"
                             "随后主循环修复并重新补测")
    args = parser.parse_args(argv)

    # trace: 2026-09-13 裁定——--augment-only 与另两开关互斥（补跑不驱动主循环；
    # 重开任务需主循环修复，--skip-augment 与补跑语义矛盾），一行报错零 spawn
    if args.augment_only and (args.skip_augment or args.reopen_failed):
        print("[runner] --augment-only 与 --skip-augment/--reopen-failed 互斥"
              "（补跑不驱动主循环，重开需主循环修复），拒绝启动", file=sys.stderr)
        return 1

    # trace: FR-4.5 D-9（finding: diy-sprint/enhancement-2）白名单校验：非法实例名不落 spawn，
    # 一行中文报错 + 非零退出（与 viewer/help 的 INSTANCE_RE 同源）
    if args.instance is not None and not INSTANCE_RE.fullmatch(args.instance):
        print(f"[runner] 非法实例名 {args.instance!r}（字母数字开头和结尾，中间可含 . _ -），拒绝启动",
              file=sys.stderr)
        return 1

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
    # trace: 对抗审查修复——paths 段或 output_dir 值形状异常时一行中文报错（与 viewer/exp-sync 同源守卫）
    paths = config.get("paths")
    if paths is not None and not isinstance(paths, dict):
        print(f"[runner] diy-coder.yaml 的 paths 不是映射：{cfg_path}", file=sys.stderr)
        return 1
    output_dir_name = (paths or {}).get("output_dir", "diy-output")
    if not isinstance(output_dir_name, str):
        print(f"[runner] diy-coder.yaml 的 output_dir 不是字符串：{cfg_path}", file=sys.stderr)
        return 1
    output_dir = root / output_dir_name
    # trace: FR-4.5 D-9 目录即实例：--instance → <output_dir>/<name>/；无 → 主线平铺零变化
    if args.instance is not None:
        output_dir = output_dir / args.instance
    sprint_path = output_dir / "sprint.yaml"
    if not sprint_path.exists():
        print(f"[runner] 找不到 {sprint_path}——先运行 diy-sprint 生成 sprint.yaml",
              file=sys.stderr)
        return 1
    load_sprint(sprint_path)

    # trace: 2026-09-13 裁定——--reopen-failed 先批量重开再进主循环
    # （重开任务由主循环修复，已完成 后重新补测覆盖结论）
    if args.reopen_failed:
        reopened = reopen_augment_failed(sprint_path)
        if reopened:
            print(f"[runner] 已重开 {len(reopened)} 个补测未通过任务："
                  f"{'、'.join(reopened)}", flush=True)
        else:
            print("[runner] 无补测未通过任务（--reopen-failed 零操作）", flush=True)

    # trace: 2026-09-13 裁定——--augment-only：只补跑已完成 且无终结结论的任务，
    # 不驱动主循环（待办/进行中 原样不动）
    if args.augment_only:
        doc = load_sprint(sprint_path)
        targets = [t["story"] for t in doc.get("tasks", [])
                   if t.get("status") == "已完成"
                   and t.get("augment") not in ("通过", "已跳过")]
        for story_id in targets:
            rc = spawn_augment(args.claude_cmd, root, story_id, allow, args.instance)
            print(f"[runner] {story_id} {augment_note(sprint_path, story_id, rc)}", flush=True)
        for line in augment_summary(load_sprint(sprint_path)):
            print(line, flush=True)
        print("[runner] 补测补跑完成（--augment-only），退出", flush=True)
        return 0

    while True:
        doc = load_sprint(sprint_path)
        task = pick_next(doc)
        if task is None:
            break
        story_id = task["story"]
        outcome = drive_task(sprint_path, args.claude_cmd, root, story_id,
                             args.max_retries, allow, args.instance)
        print(f"[runner] {story_id} → {outcome}", flush=True)
        if outcome == "已完成" and not args.skip_augment:
            # trace: 2026-09-13 裁定——已完成 后编码后补测（diy-augment）；
            # 结论以 augment 字段为准（通过/失败/已跳过），未留痕降级为提示行，
            # 不阻塞主循环、不回退任务状态
            rc = spawn_augment(args.claude_cmd, root, story_id, allow, args.instance)
            print(f"[runner] {story_id} {augment_note(sprint_path, story_id, rc)}", flush=True)

    for line in augment_summary(load_sprint(sprint_path)):
        print(line, flush=True)
    print("[runner] 全部任务已到终态（已完成/已阻塞），退出", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
