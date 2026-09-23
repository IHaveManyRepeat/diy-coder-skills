# -*- coding: utf-8 -*-
"""diyc mutate 行为模块 —— 变异执行的沙箱机制（迁移计划 §五 阶段 C 第 9 项 / C·9）。

职责边界（语言无关纪律）：本模块只做「建副本 → 跑命令 → 销毁 → 出回执」，
**不解析任何工具的输出**——survivors / equivalents 的语义归 `diy-augment`。
各工具的词汇本就不同（mutmut 报 `survived`；cosmic-ray 报
`test_outcome ∈ killed|survived|incompetent|timeout`；Stryker 报
`Killed|Survived|Timeout`），把解析下沉到脚本等于把某一家工具的词汇固化成套件契约。
故回执只给 `rc` 与 `output_tail`，解释归模型。

为什么必须建副本：变异工具**原地改文件**再还原（mutmut / cosmic-ray 皆如此，
2026-09-22 实测确认），进程被杀或工具崩溃会把半变异状态留在工作区。

为什么默认落系统临时目录：副本若建在项目内，会同时污染两处——① `git status
--porcelain` 基线（`diy-augment` 规则 5 用它判「工作区是否被碰」，副本自身会
把该判定变成恒真）；② pytest 的收集面（副本里的测试文件被主项目再收集一遍）。
`--sandbox` 可显式改址，责任随之转移给调用方。
"""
import os
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import diyc_lib  # noqa: E402
from diyc_lib import receipt, v  # noqa: E402

# 不进副本的条目（按 basename 匹配）：VCS 元数据、各类缓存、依赖目录、编辑器
SANDBOX_EXCLUDES = (".git", ".hg", ".svn", "__pycache__", ".pytest_cache",
                    ".ruff_cache", ".mypy_cache", ".tox", "node_modules",
                    ".venv", "venv", ".idea", ".vscode", "dist", "build")

DEFAULT_TIMEOUT = 3600
SCOPE_PLACEHOLDER = "{scope}"


def _norm(path) -> str:
    return str(path).replace("\\", "/")


def _under_project(path, project_root) -> bool:
    """path 是否落在 project_root 内。

    跨盘符（Windows：沙箱常落 C:\\Users\\…\\Temp，项目在 D:\\）时 commonpath 抛
    ValueError——那正是「不在项目内」的情形，故按 False 收口（2026-09-22 冒烟实测）。
    """
    try:
        root = os.path.abspath(project_root)
        return os.path.commonpath([os.path.abspath(path), root]) == root
    except ValueError:
        return False


def _git_dirty(project_root):
    """工作区脏度基线：返回 (行数, 明细)；非 git 仓库返回 (None, [])。"""
    try:
        proc = subprocess.run(["git", "status", "--porcelain"],
                              cwd=project_root, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None, []
    if proc.returncode != 0:
        return None, []
    lines = [ln for ln in (proc.stdout or "").splitlines() if ln.strip()]
    return len(lines), lines


def _resolve_tool(args):
    """变异命令来源：只认 `--tool`（显式传入）。

    为什么不做「从 test-plan.yaml 的 static_checks 里挑」：契约要求挑的是
    **用户确认为变异工具**的那条，而该确认是语义判断，`static_checks[].tool`
    里没有任何机器可读的标记能承载它（`kills` 是自然语言）。机械猜测哪条是
    变异条目会把「用户确认」偷换成「脚本猜」——故判定归技能，diyc 只收结果。
    """
    tool = getattr(args, "tool", None)
    if isinstance(tool, str) and tool.strip():
        return tool.strip()
    return None


def _resolve_scope(args):
    """变异范围：`--scope` 显式 > 全量。返回 (文件列表, 模式)。"""
    scope = [s.strip() for s in (getattr(args, "scope", None) or []) if str(s).strip()]
    if scope:
        return [_norm(s) for s in scope], "scope"
    return [], "full"


def run(args) -> dict:
    project_root = os.path.abspath(args.project_root)
    warnings = []

    tool = _resolve_tool(args)
    if tool is None:
        return receipt("mutate", False, violations=[v(
            "TOOL_NOT_GIVEN", "args.tool",
            "未给 --tool：变异命令须由调用方显式传入（技能侧按 test-plan.yaml 的 "
            "static_checks 判定哪条是变异条目，diyc 不做该语义判断）")])

    scope, mode = _resolve_scope(args)
    if mode == "full" and not getattr(args, "full", False):
        warnings.append("未给 --scope 也未给 --full：按全量变异执行（可能很慢）")
    if scope and not getattr(args, "full", False) and SCOPE_PLACEHOLDER not in tool:
        warnings.append("给了 --scope 但命令里没有 %s 占位符——范围不会生效，"
                        "整份副本都会被变异" % SCOPE_PLACEHOLDER)

    sandbox_arg = getattr(args, "sandbox", None)
    if sandbox_arg and os.path.exists(sandbox_arg):
        return receipt("mutate", False, violations=[v(
            "SANDBOX_EXISTS", _norm(sandbox_arg),
            "指定的沙箱路径已存在——本命令只创建不覆盖，请给一个不存在的路径")])

    dirty_before, _ = _git_dirty(project_root)
    keep = bool(getattr(args, "keep", False))
    timeout = int(getattr(args, "timeout", None) or DEFAULT_TIMEOUT)
    cmd = tool.replace(SCOPE_PLACEHOLDER, " ".join(scope)) if scope else tool
    violations = []
    rc, out, timed_out = None, "", False
    created = False
    in_project = False
    # 沙箱的创建到销毁全在 try 内：中途任何异常都经 finally 收走副本，绝不泄漏临时目录
    sandbox = os.path.abspath(sandbox_arg) if sandbox_arg else None
    try:
        if sandbox is None:
            sandbox = tempfile.mkdtemp(prefix="diyc-mutate-")
        in_project = _under_project(sandbox, project_root)
        if in_project:
            warnings.append("沙箱落在项目内（%s）：副本自身会进入 git status 与测试收集面，"
                            "建议改到项目外" % _norm(sandbox))
        shutil.copytree(project_root, sandbox,
                        ignore=shutil.ignore_patterns(*SANDBOX_EXCLUDES),
                        dirs_exist_ok=True)
        created = True
        rc, out, timed_out = diyc_lib.run_tool(cmd, sandbox, timeout)
        if timed_out:
            violations.append(v("MUTATE_TIMEOUT", _norm(sandbox),
                                "变异命令超时（>%ss）被杀：%s" % (timeout, _short(cmd))))
    except OSError as e:
        violations.append(v("SANDBOX_FAILED", _norm(sandbox),
                            "沙箱副本创建/执行失败：%s: %s" % (type(e).__name__, e)))
    finally:
        dirty_after, _ = _git_dirty(project_root)
        if sandbox and not keep:
            shutil.rmtree(sandbox, ignore_errors=True)

    if dirty_before is not None and dirty_after is not None and dirty_after > dirty_before:
        violations.append(v("WORKSPACE_TOUCHED", _norm(project_root),
                            "工作区脏度在执行后上升（%d → %d 行）——命令可能越出沙箱跑了"
                            "绝对路径或工作区外的写面，请核对现场"
                            % (dirty_before, dirty_after)))

    ok = created and not timed_out and not any(
        x["code"] in ("SANDBOX_FAILED", "WORKSPACE_TOUCHED") for x in violations)
    return receipt("mutate", ok,
                   tool=cmd, mode=mode, scope=scope or None,
                   sandbox=_norm(sandbox), sandbox_kept=keep and created,
                   rc=rc, timed_out=timed_out, output_tail=_tail(out),
                   workspace={"dirty_before": dirty_before, "dirty_after": dirty_after,
                              "sandbox_in_project": in_project},
                   violations=violations, warnings=warnings,
                   counts={"scope_files": len(scope),
                           "output_lines": len((out or "").splitlines())})


def _short(text, limit=72) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[:limit - 1] + "…"


def _tail(text, limit=20) -> list:
    lines = [ln for ln in (text or "").splitlines() if ln.strip()]
    return lines[-limit:]
