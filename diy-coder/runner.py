#!/usr/bin/env python3
# runner.py — diy-coder 循环编排器（外部循环器，D-4：spawn 无头 claude CLI 执行
# diy-build-loop 单次迭代，按 sprint.yaml 写回状态决定继续/停止）。
# 分线（C·3a W6，§5b）：--line mainline（缺省，行为零变化）/ --line wds（design.yaml 逐页
# 驱动 diy-dev WDS 模式 → diy-review WDS 路径，终点 = 待验收即待用户批准）。
# 用法：python runner.py [--project-root DIR] [--claude-cmd claude ...] [--max-retries N]
#       [--line {mainline,wds}] [--instance NAME]
#       [--skip-augment | --augment-only | --reopen-failed]（augment 面仅主线，WDS 线显式拒绝）
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

# —— 分线（C·3a W6，§5b）——
# 页状态词表归 diy-design 引擎（design.py PAGE_STATUSES，裁定 5）：此处只读、不另铸——
# 下面这份副本只服务汇总计数，与引擎常量的一致性由 tests/test_runner.py::TC_WDS_StatusLexicon
# 的机械对账钉死（引擎词表增删/改序即红，不靠人读注释）。
PAGE_DRAFT = "结构稿中"       # §5b #3：页级驱动单元（对应主线 pick_next 语义）
PAGE_ACCEPT = "待验收"        # §5b #3b：无头侧终点（用户批准不代做）
PAGE_INITIAL = "未开始"       # 键缺失 = 未开始（旧稿兼容）
PAGE_APPROVED = "已批准"      # 用户批准边终点：任何驱动环都不得自行推进（典型越界落点）
PAGE_REMOVED = "已移除"       # 页离开工作集（该页本轮被废弃）——不是驱动环的落点
PAGE_STATUSES_ALL = ("未开始", "结构稿中", "待验收", "已批准", "已移除")
WDS_LOCK_NAME = ".runner-wds.lock"  # §5b #7③：并发实例闸（仅 WDS 线）

# —— 无头会话命令白名单（迁移计划 §五 C·8；§十三 2026-09-15 副作用纪律裁定）——
# 三档处置的落地：写代码/测试链条内的命令属「自动执行」档，交互式与无头一致。
# 工具名两套：Bash 与 PowerShell（Windows 无头会话的命令工具名为 PowerShell，
# 见 _spawn 注释）；规则写法统一为空格式（官方 --help 示例形式；冒号 :* 是等价
# legacy 写法，个别版本有静默失效报告）。
_TOOLS = ("Bash", "PowerShell")
# 跨语言命令族：Python / JS-TS / Go / Rust / Java 的构建、测试、lint、依赖安装，
# 外加 git 三步（add / commit / push）。规格列举见 §五 C·8。
_ALLOWED_COMMANDS = (
    "python", "pip", "ruff", "pytest",
    "npm", "npx", "node", "pnpm", "yarn", "playwright",
    "go", "cargo", "mvn", "gradle",
    "git add", "git commit", "git push",
)
DEFAULT_ALLOW = [f"{tool}({cmd} *)" for tool in _TOOLS for cmd in _ALLOWED_COMMANDS]
# 拒止表（deny）：破坏性 git 操作保留确认语义（§十三 二次修订裁定：保留确认档的
# git 项收窄为破坏性操作）。求值序 deny → ask → allow，deny 永远赢——这是
# 「push 进白名单」与「force 保留确认」能同时成立的唯一机制：allowedTools 是纯前缀
# 匹配、看不见后缀 flag，无法在 allow 侧表达"放行 push 但排除 force"。
# ⚠ 已知缺口：`-f` 短写无法在不误伤分支名（如 bug-fix）的前提下表达，故未纳入；
# 该缺口由技能侧行为条款承担第一道防线，此处登记备查（见 C·8 裁定记录）。
_DENIED_PATTERNS = (
    "git push *--force*",      # 覆盖 --force 与 --force-with-lease
    "git push *--delete*",     # 删远端分支
    "git reset *--hard*",
    "git branch *-D*", "git branch *--delete*",
)
DEFAULT_DENY = [f"{tool}({pat})" for tool in _TOOLS for pat in _DENIED_PATTERNS]
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
                    allow: list, deny: list, instance: str = None) -> int:
    # trace: S-10 AC-10.1 D-4 R-1 spawn 无头 claude CLI 执行 diy-build-loop 单次迭代
    # trace: FR-4.5 D-9（finding: diy-build-loop/enhancement-1）实例模式经 prompt 透传
    # --instance 激活参数，子会话按各技能 On Activation 约定解析到 <output_dir>/<name>/；
    # 无实例时不加任何前缀（主线 prompt 逐字节等价现状）
    # stdin 继承（不重定向）：本 GLM 兼容 harness 按 stdin 句柄形态决定工具面——
    # DEVNULL/PIPE 会剥离子会话命令执行工具（实测复现）；claude -p 的 prompt 走 argv，
    # 不读 stdin，继承不构成人工输入通道（无人值守语义不变）
    # --permission-mode acceptEdits + --allowedTools 白名单：R-1 定稿——文件编辑自动接受，
    # 命令执行仅放行白名单（TDD red/green 必需），禁 skip-permissions；
    # 白名单默认跨语言构建/测试链条（DEFAULT_ALLOW），其他命令经 --allow 传入；
    # --disallowedTools 拒止表兜破坏性 git（DEFAULT_DENY），经 --deny 覆盖
    prompt = _instance_clause(instance) + (
        f"运行 diy-build-loop skill 处理任务 {story_id}：读取本项目 diy-coder.yaml 解析 "
        f"output_dir 下的 sprint.yaml，把任务 {story_id} 从当前状态驱动到终态"
        f"（已完成 或 已阻塞），每次状态转移立即写回 sprint.yaml 并更新 project.updated。"
        f"无人值守模式：不要提问、不要等待人工确认。"
        f"提示：本会话的命令执行工具（PowerShell）是核心工具、不进入 ToolSearch 索引，"
        f"直接调用即可；先用 ToolSearch 搜索来确认其存在会得到假阴性。"
    )
    return _spawn(claude_cmd, project_root, prompt, allow, deny)


def _instance_clause(instance: str) -> str:
    # 实例激活子句（build-loop 与 augment 两处 spawn 共用，保证 prompt 前缀逐字同源）
    return (
        f"激活参数 --instance {instance}（实例目录 output_dir/{instance}/，"
        f"本次运行读取与写回仅限该实例）。"
        if instance is not None else ""
    )


def _spawn(claude_cmd: list, project_root: Path, prompt: str,
           allow: list, deny: list) -> int:
    # diy-build-loop / diy-augment 共用的 spawn 机制：--permission-mode acceptEdits +
    # --allowedTools 白名单 + --disallowedTools 拒止表（前者放行构建/测试链条，
    # 后者兜破坏性 git——deny 与 allow 求值序 deny → ask → allow，前者永远赢）
    # errors="replace"：子会话（或桩）stderr 跟随宿主 locale（Windows 中文 = GBK），
    # 其增量输出若非 UTF-8 不应打断 runner——本函数只取退出码，decode 失败无信息价值
    cmd = claude_cmd + ["-p", prompt,
                        "--output-format", "json",
                        "--permission-mode", "acceptEdits",
                        "--allowedTools"] + allow
    if deny:
        cmd += ["--disallowedTools"] + deny
    proc = subprocess.run(
        cmd,
        cwd=str(project_root),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return proc.returncode


def spawn_augment(claude_cmd: list, project_root: Path, story_id: str,
                  allow: list, deny: list, instance: str = None) -> int:
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
    return _spawn(claude_cmd, project_root, prompt, allow, deny)


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


def deferred_summary(output_dir: Path) -> list:
    # trace: 迁移计划 §五 C·8②——runner 结束时的待确认动作汇总。副作用纪律的保留确认档
    # 在无头下不阻塞任务（经 diyc.py defer-add 入队），代价是用户"挨个产物翻"才发现——
    # 本汇总行让循环结束时一眼看到累积量（仿 augment_summary 形态：有则一行，无则零行）。
    # 读取容错与 viewer 同源：文件缺席/坏 YAML/形状异常一律降级为不打扰（汇总非门禁）
    path = output_dir / "deferred-actions.yaml"
    if not path.is_file():
        return []
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (yaml.YAMLError, OSError):
        return [f"[runner] {path.name} 读取失败（解析/IO），待确认动作未汇总"]
    actions = doc.get("actions") if isinstance(doc, dict) else None
    if not isinstance(actions, list):
        return []
    pending = [a for a in actions
               if isinstance(a, dict) and a.get("status") == "待办"]
    if not pending:
        return []
    ids = "、".join(str(a.get("id") or "?") for a in pending)
    return [f"[runner] 待确认动作 {len(pending)} 条待办：{ids}"
            f"——见 {path.name}，用户确认执行后用 diyc.py defer-set 翻转 status"]


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
               story_id: str, max_retries: int, allow: list, deny: list,
               instance: str = None) -> str:
    # trace: S-10 AC-10.3 TC-10.3.1 驱动单任务：初次 + 至多 max_retries 次重试，
    # 重试用尽仍非终态 → 已阻塞 写回原因，返回由调用方继续后续任务
    for _attempt in range(1 + max_retries):
        spawn_iteration(claude_cmd, project_root, story_id, allow, deny, instance)
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


# ---------------------------------------------------------------- WDS 线（§5b：分线编排 + 无头集成）

def read_design(design_path: Path) -> dict:
    # trace: §5b #4 WDS 线只读面——runner 不直改 YAML，页状态一律由子会话经 design.py
    # transition 写回；本函数只在驱动前后回读，判「页到了哪一步」。
    # 语法/形状异常一行中文报错（与 load_sprint 同标准，不落 yaml 裸栈）
    try:
        doc = yaml.safe_load(design_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        raise SystemExit(f"[runner] design.yaml 解析失败（{e.__class__.__name__}）："
                         f"{design_path}——修复后重跑")
    if not isinstance(doc, dict):
        raise SystemExit(f"[runner] design.yaml 顶层不是映射：{design_path}")
    pages = doc.get("pages")
    if pages is not None and not isinstance(pages, list):
        raise SystemExit(f"[runner] design.yaml 的 pages 不是列表（形状异常）：{design_path}")
    return doc


def wds_gate(design_path: Path) -> dict:
    # trace: §5b #2 WDS 硬门：design.yaml 的 project.status: 已定稿；缺失/未定稿 → 拒绝并
    # 路由（WDS 线 → diy-wds-brief / diy-design；产品线项目 → diy-prd + --line mainline）
    if not design_path.exists():
        raise SystemExit(f"[runner] 找不到 {design_path}——WDS 线先运行 diy-wds-brief 建场景、"
                         f"再运行 diy-design 产出 design.yaml（产品线项目走 diy-prd 的 PRD 主线）")
    doc = read_design(design_path)
    proj = doc.get("project")
    status = proj.get("status") if isinstance(proj, dict) else None
    if status != "已定稿":
        raise SystemExit(f"[runner] design.yaml 非已定稿（project.status={status!r}）——"
                         f"先运行 diy-design 定稿；产品线项目走 diy-prd + --line mainline："
                         f"{design_path}")
    return doc


def page_status(page: dict) -> str:
    # 键缺失 = 未开始（旧稿兼容，不是失败——段1 裁决）；值在词表外按原值回读（只读面不改稿）
    return str(page.get("status") or PAGE_INITIAL)


def find_page(doc: dict, page_id: str):
    for page in doc.get("pages") or []:
        if isinstance(page, dict) and page.get("id") == page_id:
            return page
    return None


def page_has_id(page: dict) -> bool:
    # 页 ID 是驱动单元的必需键（非空字符串才算；None/数值/空白串不可作驱动单元）。
    # pick_next_page 与「缺 id 点名」两处共用一个谓词，防两处判据漂移
    pid = page.get("id")
    return isinstance(pid, str) and bool(pid.strip())


def pick_next_page(doc: dict, skip=frozenset()):
    # trace: §5b #3 取第一条 pages[].status: 结构稿中 的页（对应主线 pick_next 的语义）。
    # skip = 本轮已驱动且重试用尽的页——runner 不写 YAML，防死循环只能靠会话内跳过
    for page in doc.get("pages") or []:
        if not isinstance(page, dict) or not page_has_id(page):
            continue
        if page.get("id") in skip:
            continue
        if page.get("status") == PAGE_DRAFT:
            return page
    return None


def nameless_draft_pages(doc: dict) -> list:
    # trace: §5b #3 页 ID 是驱动单元的必需键——页是 结构稿中 却缺 id 时不能静默跳过：
    # 汇总里逐个点名（给出 pages[] 下标，缺 id 时下标是唯一可指认的坐标），
    # 且本轮按「有页未达终点」计（rc 非零），不静默降级
    labels = []
    for index, page in enumerate(doc.get("pages") or []):
        if not isinstance(page, dict) or page_has_id(page):
            continue
        if page_status(page) == PAGE_DRAFT:
            name = page.get("name")
            labels.append("pages[%d]%s" % (index, "（name=%s）" % name if name else ""))
    return labels


def spawn_wds_dev(claude_cmd: list, project_root: Path, page_id: str,
                  allow: list, deny: list, instance: str = None) -> int:
    # trace: §5b #5 WDS 实现环点名 diy-dev 的 WDS 模式——不得沿用主线 diy-build-loop
    # （其硬门读 sprint.yaml，与 WDS 线不相容）；提示词按页级语义写（页 ID / 判据 =
    # states[].signals / 浏览器门 §2.6 + 裁定 21 / 终态 待验收 / 回填只经 transition）
    prompt = _instance_clause(instance) + (
        f"运行 diy-dev skill 的 WDS 模式实现页面 {page_id}：读取本项目 diy-coder.yaml 解析 "
        f"output_dir 下的 design.yaml 该页记录（判据唯一真源 = 该页 states[].signals，"
        f"prototype 是结构稿、implementation 是实现基线），按该技能 steps/wds-implement.md 逐项实现。"
        f"浏览器强制门：判据 = 该页 states[].signals，未过不得呈给用户；环境不可用则停下"
        f"如实上报（探测方式 + 结论）、由用户决定安装或跳过（裁定 21），不得静默降级。"
        f"实现完毕把页 {page_id} 经 design.py transition 迁移到 待验收"
        f"（状态回填只经 transition，不手改 YAML）。环转不了绿或门不过就停下如实上报，"
        f"绝不削弱判据。"
        f"无人值守模式：不要提问、不要等待人工确认。"
        f"提示：本会话的命令执行工具（PowerShell）是核心工具、不进入 ToolSearch 索引，"
        f"直接调用即可；先用 ToolSearch 搜索来确认其存在会得到假阴性。"
    )
    return _spawn(claude_cmd, project_root, prompt, allow, deny)


def spawn_wds_review(claude_cmd: list, project_root: Path, page_id: str,
                     allow: list, deny: list, instance: str = None) -> int:
    # trace: §5b #5 审查环点名 diy-review 的 WDS 路径（§5.6 #4b）：独立复验、判决不代用户批准
    prompt = _instance_clause(instance) + (
        f"运行 diy-review skill 的 WDS 路径审查页面 {page_id}：读取本项目 diy-coder.yaml 解析 "
        f"output_dir 下的 design.yaml，目标是 pages[].status: 待验收 的页 {page_id}；"
        f"判据 = 该页 states[].signals（与浏览器强制门同源）+ prototype 结构稿 + 实现面，"
        f"独立复验、不采信 diy-dev 的自述。判决落点：通过 → 页保持 待验收，只出「可呈用户批准」"
        f"结论（待验收 → 已批准 是用户批准，绝不代批、不调这条边）；失败 → 经 design.py transition "
        f"把页 {page_id} 迁移到 结构稿中（回修边；状态写入只经 transition，不手改 YAML、不新增键）。"
        f"无人值守模式：不要提问、不要等待人工确认。"
        f"提示：本会话的命令执行工具（PowerShell）是核心工具、不进入 ToolSearch 索引，"
        f"直接调用即可；先用 ToolSearch 搜索来确认其存在会得到假阴性。"
    )
    return _spawn(claude_cmd, project_root, prompt, allow, deny)


class WdsPageOffTrack(Exception):
    # F-2 / 中-1（主 agent 终裁）：驱动环回读页状态，若页不在该环的合法落点内
    # = 页被推到了本轮不该出现的状态（典型：审查代批到 已批准；dev 或审查把页 已移除）
    # → 报错停手、绝不重试。原实现按「未达终态」重试，会在越界页上再 spawn 子会话
    # （烧真会话），收尾句还把违规信号稀释成普通失败。
    # stage 记录是哪个环越界（dev / review）：两个环的合法落点与病因不同，
    # 停手句按 stage + 实际落点生成（低-1：病因不得硬编码）。
    def __init__(self, page_id: str, status, attempt: int, stage: str = "review"):
        self.page_id = page_id
        self.status = status
        self.attempt = attempt
        self.stage = stage
        super().__init__("%s → %r（第 %d 轮，%s 环）" % (page_id, status, attempt, stage))


def wds_stop_note(exc: WdsPageOffTrack) -> str:
    # F-2 / 中-1 / 低-1（主 agent 终裁）：停手句的病因按「越界的环 + 实际落点」生成，不硬编码。
    # 合法落点两侧不同：审查环只应 保持 待验收 或回 结构稿中；dev 环只应停在 结构稿中
    # （未推进/待重试）或推进到 待验收。硬编码「审查可能代批」会把 dev 环的越界说反——
    # 已批准 才叫可能代批，其余落点（已移除 = 该页本轮被废弃 / 未开始 = 被退回起点 /
    # 不在 pages[]）各自如实点名含义。
    shown = exc.status if exc.status is not None else "不在 pages[] 中"
    if exc.stage == "dev":
        meaning = {
            PAGE_REMOVED: "已移除 = 该页本轮被废弃、已离开工作集",
            PAGE_APPROVED: "已批准 是用户批准边，dev 不得代批",
            PAGE_INITIAL: "未开始 = 页被退回起点，dev 不该产生该落点",
        }.get(exc.status, "该落点不在 dev 环本轮允许的范围内")
        return (f"[runner] {exc.page_id} 第 {exc.attempt} 轮后页被 diy-dev 推到 {shown}"
                f"（本轮 dev 后只应停在 结构稿中（未推进/待重试）或 待验收（推进成功））——"
                f"{meaning}，可能是该页被废弃或 dev 误改，停手不重试；"
                f"请核查该页与 diy-dev 的判决落点后重跑")
    if exc.status == PAGE_APPROVED:
        why = "审查可能代批（待验收 → 已批准 是用户批准边，审查不得代批）"
    elif exc.status == PAGE_REMOVED:
        why = "审查落点越界（已移除 = 页被移出工作集，审查只应 保持 待验收 或回到 结构稿中）"
    elif exc.status is None:
        why = "审查落点越界（页审查后从 pages[] 消失）"
    else:
        why = f"审查落点越界（{shown} 不在本轮合法落点内）"
    return (f"[runner] {exc.page_id} 第 {exc.attempt} 轮后页被推到 {shown}"
            f"（本轮只应停在 待验收 或回到 结构稿中）——{why}，停手不重试；"
            f"请核查该页与 diy-review 的判决落点后重跑")


def drive_page(design_path: Path, claude_cmd: list, project_root: Path, page_id: str,
               max_retries: int, allow: list, deny: list, instance: str = None):
    # trace: §5b #3b 一页的无人值守链 = diy-dev（WDS 模式）实现 → diy-review（WDS 路径）审查。
    # 审查判决「通过」→ 页保持 待验收（用户批准不代做）＝该页在无头侧的终点；失败 → 回修边
    # （待验收 → 结构稿中）→ 整环重试，上限照主线 R-4（1 + max_retries 轮）。
    # 判据一律回读 design.yaml（子会话经 transition 写；runner 不直改 YAML）。
    # F-1（主 agent 按阻断级处理）：「审查通过」在产物上的表现就是「不写」，与「审查崩了/
    # 没跑成」不可区分——故必须接住审查环退出码，rc != 0 一律不得判通过（按失败处理，
    # 如实点名「审查未通过/没跑成」）。dev 侧 rc 仍可忽略：dev 有正向信号（页必须动到 待验收）。
    # 中-1（主 agent 终裁）：dev 侧同样要做落点收紧——dev 后回读的合法落点只有
    # 结构稿中（本次未推进/待重试）与 待验收（推进成功）；页被推到其它值（典型 已移除 =
    # 该页本轮被废弃）说明它已不是驱动单元，重试只是在废弃页上重复 spawn（与 F-2 同构）。
    # 返回 (终态, 轮数, 是否通过, 不过时的原因)：通过 = 审查 rc=0 且页停 待验收；
    # 任一环把页推到本轮不该出现的状态 → 抛 WdsPageOffTrack（报错停手，不重试）。
    detail = "未达 待验收"  # dev 侧落点：页没动到 待验收（有正向信号，rc 不作判据）
    for attempt in range(1, 1 + max_retries + 1):
        spawn_wds_dev(claude_cmd, project_root, page_id, allow, deny, instance)
        page = find_page(read_design(design_path), page_id)
        dev_status = page.get("status") if isinstance(page, dict) else None
        if dev_status != PAGE_ACCEPT:
            if dev_status == PAGE_DRAFT:
                continue  # dev 本次未推进：页仍在 结构稿中，本轮作废、重试
            raise WdsPageOffTrack(page_id, dev_status, attempt, stage="dev")
        review_rc = spawn_wds_review(claude_cmd, project_root, page_id, allow, deny, instance)
        page = find_page(read_design(design_path), page_id)
        status = page.get("status") if isinstance(page, dict) else None
        if status not in (PAGE_ACCEPT, PAGE_DRAFT):
            # 本轮合法落点只有两个：审查通过留在 待验收、审查判失败回 结构稿中（回修边）
            raise WdsPageOffTrack(page_id, status, attempt, stage="review")
        if review_rc != 0:
            # 审查环非零退出：页可能停在 待验收（零写回），但这是「没跑成」不是「通过」
            detail = "审查未通过/没跑成，diy-review 退出码 %d" % review_rc
            continue
        if status == PAGE_ACCEPT:
            return PAGE_ACCEPT, attempt, True, ""  # 审查通过且未代批：页停在 待验收
        # 审查判失败（rc=0）走回修边：页落点 结构稿中，仍属「未达 待验收」，但如实点名原因
        detail = "未达 待验收（审查未通过，已走回修边）"
    page = find_page(read_design(design_path), page_id)
    if not isinstance(page, dict):
        return f"页 {page_id} 不在 pages[]", 1 + max_retries, False, "页在驱动中消失"
    return page_status(page), 1 + max_retries, False, detail


def wds_unverified_pages(doc: dict, unreviewed=(), verified=()) -> list:
    # 高-1（主 agent 终裁）：停在 待验收 的页里，只有「本轮走完整审查环且通过」（verified）
    # 才可呈用户批准；不在本轮台账内（既非本轮通过、也非本轮未过）的 待验收 页 = 本轮未复验、
    # 审查结论未知（上一轮审查崩掉/进程被杀遗留，或本轮零驱动的旧页）——必须单列点名
    # （勿直接批准）并计入 rc，否则用户照单批准的就是未经复验的页（与 F-1 同源的后果面）。
    # 台账在内存里，不新增 YAML 键、不写 design.yaml。
    unreviewed = {str(pid) for pid in unreviewed}
    verified = {str(pid) for pid in verified}
    return [str(p.get("id")) for p in doc.get("pages") or []
            if isinstance(p, dict) and p.get("status") == PAGE_ACCEPT
            and str(p.get("id")) not in unreviewed and str(p.get("id")) not in verified]


def wds_summary(doc: dict, driven: int, failed: int, nameless=(), unreviewed=(),
                verified=()) -> list:
    # trace: §5b #3b 终点呈报（待用户批准；演进轮声明行由 run_wds_line 的统一收尾打印，见低-2）。
    # unreviewed（F-1）：本轮审查未通过/没跑成却停在 待验收 的页——不得混入「待用户批准」
    # （未过审查 ≠ 可呈批准，否则用户照单批准的就是未经审查的页）。
    # verified（高-1）：本轮走完整审查环且通过的页——待批准名单只收这一类的 待验收 页；
    # 其余 待验收 页（本轮未复验/审查结论未知）单列警示。
    # nameless（主 agent 终裁「汇总句自相矛盾」项）：结构稿中 但缺 id、不能作驱动单元的页——单独点名，
    # 与「无 结构稿中 的页可驱动（… 结构稿中 1 …）」不再同句自相矛盾。
    pages = [p for p in doc.get("pages") or [] if isinstance(p, dict)]
    unreviewed = {str(pid) for pid in unreviewed}
    verified = {str(pid) for pid in verified}
    pending = [str(p.get("id")) for p in pages
               if p.get("status") == PAGE_ACCEPT and str(p.get("id")) in verified
               and str(p.get("id")) not in unreviewed]
    lines = []
    if driven == 0 and failed == 0:
        counts = {s: sum(1 for p in pages if page_status(p) == s) for s in PAGE_STATUSES_ALL}
        other = len(pages) - sum(counts.values())
        parts = ["%s %d" % (s, counts[s]) for s in PAGE_STATUSES_ALL]
        if other:
            parts.append("词表外 %d" % other)
        lines.append("[runner] WDS 线无 结构稿中 的页可驱动（%s）" % " / ".join(parts))
    if nameless:
        lines.append("[runner] 结构稿中 但缺 id 被跳过 %d 页：%s——页 ID 是驱动单元的必需键，"
                     "补 id 后重跑" % (len(nameless), "、".join(nameless)))
    if unreviewed:
        lines.append("[runner] 审查未通过/没跑成 %d 页：%s——页停在 待验收 但不构成"
                     "「可呈用户批准」，勿批准；修复后重跑"
                     % (len(unreviewed), "、".join(sorted(unreviewed))))
    unverified = wds_unverified_pages(doc, unreviewed, verified)
    if unverified:
        lines.append("[runner] 本轮未复验 %d 页：%s——审查结论未知（不早于上次会话）、"
                     "不构成「可呈用户批准」，勿直接批准；先确认其审查结论或重跑复核后再批"
                     % (len(unverified), "、".join(unverified)))
    if pending:
        lines.append("[runner] 待用户批准 %d 页（本轮审查通过）：%s——已批准归用户"
                     "（design.py transition --to 已批准），无人值守不代批"
                     % (len(pending), "、".join(pending)))
    return lines


def _lock_holder(lock_path: Path) -> str:
    try:
        text = lock_path.read_text(encoding="utf-8").strip()
    except OSError:
        return "持有者未知"
    return text or "持有者未知"


def acquire_wds_lock(lock_path: Path):
    # trace: §5b #7③ 并发实例 = 不做（显式拒绝，不静默忽略）：O_EXCL 原子建锁，
    # 锁在场即拒第二个 runner——绝不静默并行驱动同一 output_dir
    try:
        fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        return None
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write("pid=%d\n" % os.getpid())
    return lock_path


def release_wds_lock(lock_path: Path) -> None:
    try:
        lock_path.unlink()
    except OSError as e:
        print(f"[runner] 锁文件清理失败（{e.__class__.__name__}）：{lock_path}——"
              f"确认无 runner 在跑后手工删除", file=sys.stderr)


def print_wds_evolution_notice() -> None:
    # trace: §5b #7① 演进轮显式不驱动声明（不静默忽略）。
    # 低-2（主 agent 终裁）：该声明属「任何退出路径都不得缺失」的收尾面——原先只在
    # wds_summary 内打印，而 F-2/WdsPageOffTrack 的停手路径绕过汇总，声明行随之消失。
    # 现由 run_wds_line 的统一收尾（finally）打印：正常汇总 / 停手报错 / 门禁与锁拒绝全覆盖。
    print("[runner] 演进轮（diy-wds-evolution）由人发起、不在无人值守环内——本轮未驱动", flush=True)


def run_wds_line(args, root: Path, output_dir: Path, base_output_dir: Path,
                 allow: list, deny: list) -> int:
    # trace: §5b WDS 线主循环：门禁 → 页级串行驱动（dev → review）→ 汇总。不做：演进轮
    # 无人值守（#7①，收尾统一声明）· augment 面（#7②，入口已显式拒）· 并发实例（#7③，锁闸）
    design_path = output_dir / "design.yaml"
    lock_path = base_output_dir / WDS_LOCK_NAME
    lock = None
    try:
        wds_gate(design_path)  # 缺失/未定稿 → SystemExit 一行报错 + 路由（exit 1，零 spawn）
        lock = acquire_wds_lock(lock_path)
        if lock is None:
            print(f"[runner] 并发实例被拒：{lock_path} 已被占用（{_lock_holder(lock_path)}）——"
                  f"WDS 线不做并发实例（一次只驱动一个 output_dir）；"
                  f"确认无 runner 在跑后删除该文件重跑", file=sys.stderr)
            return 1
        driven = failed = 0
        skipped = set()
        unreviewed = set()  # F-1：本轮审查未过却停在 待验收 的页（不得计入待批准）
        verified = set()    # 高-1：本轮走完整审查环且通过的页——待批准名单的唯一来源
        nameless = []
        stop_note = None
        while True:
            page = pick_next_page(read_design(design_path), skipped)
            if page is None:
                break
            page_id = page["id"]
            print(f"[runner] {page_id} 驱动中（diy-dev WDS 模式 → diy-review WDS 路径）", flush=True)
            try:
                status, attempts, passed, detail = drive_page(
                    design_path, args.claude_cmd, root, page_id,
                    args.max_retries, allow, deny, args.instance)
            except WdsPageOffTrack as exc:
                # F-2 / 中-1：报错停手（不重试、不继续下一页），病因按环与实际落点生成（低-1）
                stop_note = wds_stop_note(exc)
                break
            if passed:
                driven += 1
                verified.add(page_id)  # 本页走了完整审查环且通过 → 才可呈用户批准
                print(f"[runner] {page_id} → 待用户批准（审查通过，页保持 待验收；已批准归用户）",
                      flush=True)
            else:
                failed += 1
                skipped.add(page_id)  # 重试用尽：本轮跳过，转下一页（镜像主线封顶后继续）
                if status == PAGE_ACCEPT:
                    unreviewed.add(page_id)  # 页停 待验收 但审查未过 → 不是「可呈批准」
                print(f"[runner] {page_id} → {status}（{attempts} 轮{detail}），本轮跳过该页",
                      flush=True)
        unverified = []
        if stop_note is None:
            doc = read_design(design_path)
            nameless = nameless_draft_pages(doc)
            # 高-1：本轮未复验的 待验收 页单列警示，并与其它「未达终点」同口径计入 rc（非零）
            unverified = wds_unverified_pages(doc, unreviewed, verified)
            for line in wds_summary(doc, driven, failed, nameless, unreviewed, verified):
                print(line, flush=True)
        else:
            print(stop_note, file=sys.stderr, flush=True)
        return 1 if (failed or nameless or unverified or stop_note is not None) else 0
    finally:
        if lock is not None:
            release_wds_lock(lock)
        print_wds_evolution_notice()


# ---------------------------------------------------------------- 引导（两条线共用）

def _resolve_claude_cmd(args) -> bool:
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
        return False
    return True


def _resolve_paths(args):
    # trace: S-10 AC-10.1 AC-10.4 项目根 + output_dir（--instance → <output_dir>/<name>/）；
    # 形状异常一律一行中文报错（与 viewer/exp-sync 同源守卫）。
    # 返回 (root, output_dir, base_output_dir)——第三项供 WDS 线放并发闸（实例前基址）
    root = Path(args.project_root).resolve()
    cfg_path = root / "diy-coder.yaml"
    if not cfg_path.exists():
        print(f"[runner] 找不到 {cfg_path}——请在项目根目录运行，或用 --project-root 指定",
              file=sys.stderr)
        return None
    try:
        config = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        print(f"[runner] diy-coder.yaml 解析失败（{e.__class__.__name__}）：{cfg_path}",
              file=sys.stderr)
        return None
    if not isinstance(config, dict):
        print(f"[runner] diy-coder.yaml 顶层不是映射：{cfg_path}", file=sys.stderr)
        return None
    # trace: 对抗审查修复——paths 段或 output_dir 值形状异常时一行中文报错（与 viewer/exp-sync 同源守卫）
    paths = config.get("paths")
    if paths is not None and not isinstance(paths, dict):
        print(f"[runner] diy-coder.yaml 的 paths 不是映射：{cfg_path}", file=sys.stderr)
        return None
    output_dir_name = (paths or {}).get("output_dir", "diy-output")
    if not isinstance(output_dir_name, str):
        print(f"[runner] diy-coder.yaml 的 output_dir 不是字符串：{cfg_path}", file=sys.stderr)
        return None
    base_output_dir = root / output_dir_name
    output_dir = base_output_dir
    # trace: FR-4.5 D-9 目录即实例：--instance → <output_dir>/<name>/；无 → 主线平铺零变化
    if args.instance is not None:
        output_dir = output_dir / args.instance
    return root, output_dir, base_output_dir


def main(argv=None) -> int:
    # trace: S-10 AC-10.1 AC-10.4 TC-10.1.1 TC-10.1.2 TC-10.4.1 串行主循环：一次至多驱动一个任务
    # （不并发 spawn），直至全部任务终态
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(
        description="diy-coder 循环编排器（无人值守驱动 sprint 全部任务；--line wds 驱动 WDS 线页面）")
    parser.add_argument("--project-root", default=".", help="项目根目录（默认当前目录）")
    parser.add_argument("--claude-cmd", nargs="+", default=["claude"],
                        help="claude CLI 命令及前置参数（测试注入任务桩用）")
    parser.add_argument("--max-retries", type=int, default=DEFAULT_MAX_RETRIES,
                        help="单任务重试上限（默认 2，对齐 R-4）")
    parser.add_argument("--allow", action="append", default=None,
                        help="无头会话命令白名单条目（可重复，如 'Bash(go test:*)'）；"
                             "默认跨语言构建/测试链条：Bash 与 PowerShell 两套工具名 × "
                             "python/pip/ruff/pytest、npm/npx/node/pnpm/yarn/playwright、"
                             "go、cargo、mvn/gradle、git add|commit|push"
                             "（§五 C·8；本机 Windows 无头会话工具名为 PowerShell）")
    parser.add_argument("--deny", action="append", default=None,
                        help="无头会话命令拒止条目（可重复，如 'Bash(git push *--force*)'）；"
                             "默认拒破坏性 git：force/force-with-lease 推送、删远端分支、"
                             "reset --hard、删分支（§十三 保留确认档；求值序 deny 永远赢）")
    parser.add_argument("--line", choices=("mainline", "wds"), default="mainline",
                        help="分线（C·3a §5b）：mainline = sprint.yaml 任务环（缺省，行为零变化）；"
                             "wds = design.yaml 逐页驱动（diy-dev WDS 模式 → diy-review WDS 路径，"
                             "终点 = 待验收即待用户批准）。显式旗标、不做自动探测")
    parser.add_argument("--instance", default=None,
                        help="实例名（FR-4.5/D-9）：读写 <output_dir>/<实例名>/sprint.yaml"
                             "（--line wds 时为该实例下的 design.yaml）；"
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

    # trace: §5b #7② augment 面 = 不做（显式拒绝，不静默忽略）——WDS 线无 sprint.yaml /
    # augment 字段，三开关在 WDS 线未定义；给了即拒（含同族的 --reopen-failed：它只对
    # sprint.yaml 的 augment:失败 有意义），绝不静默忽略
    if args.line == "wds":
        wds_void = [flag for flag, on in (("--skip-augment", args.skip_augment),
                                          ("--augment-only", args.augment_only),
                                          ("--reopen-failed", args.reopen_failed)) if on]
        if wds_void:
            print(f"[runner] {'、'.join(wds_void)} 在 WDS 线未定义（augment 面是主线概念："
                  f"sprint.yaml 的 augment 字段），拒绝启动——去掉该旗标后重跑", file=sys.stderr)
            return 1

    # trace: FR-4.5 D-9（finding: diy-sprint/enhancement-2）白名单校验：非法实例名不落 spawn，
    # 一行中文报错 + 非零退出（与 viewer/help 的 INSTANCE_RE 同源）
    if args.instance is not None and not INSTANCE_RE.fullmatch(args.instance):
        print(f"[runner] 非法实例名 {args.instance!r}（字母数字开头和结尾，中间可含 . _ -），拒绝启动",
              file=sys.stderr)
        return 1

    allow = args.allow or DEFAULT_ALLOW
    deny = args.deny or DEFAULT_DENY

    if not _resolve_claude_cmd(args):
        return 1
    resolved_paths = _resolve_paths(args)
    if resolved_paths is None:
        return 1
    root, output_dir, base_output_dir = resolved_paths

    # trace: §5b #1 分线判定（显式旗标，缺省 mainline）：无头编排要确定性，不做自动探测
    # （探测歧义 = 静默走错线）；主线分支以下逐字未动
    if args.line == "wds":
        return run_wds_line(args, root, output_dir, base_output_dir, allow, deny)

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
            rc = spawn_augment(args.claude_cmd, root, story_id, allow, deny, args.instance)
            print(f"[runner] {story_id} {augment_note(sprint_path, story_id, rc)}", flush=True)
        for line in augment_summary(load_sprint(sprint_path)):
            print(line, flush=True)
        for line in deferred_summary(output_dir):
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
                             args.max_retries, allow, deny, args.instance)
        print(f"[runner] {story_id} → {outcome}", flush=True)
        if outcome == "已完成" and not args.skip_augment:
            # trace: 2026-09-13 裁定——已完成 后编码后补测（diy-augment）；
            # 结论以 augment 字段为准（通过/失败/已跳过），未留痕降级为提示行，
            # 不阻塞主循环、不回退任务状态
            rc = spawn_augment(args.claude_cmd, root, story_id, allow, deny, args.instance)
            print(f"[runner] {story_id} {augment_note(sprint_path, story_id, rc)}", flush=True)

    for line in augment_summary(load_sprint(sprint_path)):
        print(line, flush=True)
    for line in deferred_summary(output_dir):
        print(line, flush=True)
    print("[runner] 全部任务已到终态（已完成/已阻塞），退出", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
