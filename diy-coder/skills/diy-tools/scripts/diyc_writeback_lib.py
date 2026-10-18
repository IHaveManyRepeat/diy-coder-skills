# -*- coding: utf-8 -*-
"""diyc writeback 冻结常量与通用小件（契约 §3/§4.5-4.10）。"""

import os
import re

import yaml

import diyc_lib as lib

# ---- 冻结常量（契约 §4.5 / §4.8） ----

# 合法迁移边；待审查→已完成 缺席是刻意的（走 done 命令，禁止手工跳转）
LEGAL_EDGES = frozenset({
    ("待办", "进行中"),
    ("待办", "已阻塞"),
    ("进行中", "已阻塞"),
    ("待审查", "已阻塞"),
    ("进行中", "待审查"),
    ("待审查", "进行中"),
    ("已阻塞", "待办"),
    ("已完成", "进行中"),
})

# reconcile 门重算域：待审查/已完成 是审计产物一律不动；已阻塞 参与（恢复覆盖可解除）
REGATE_STATUSES = ("待办", "进行中", "已阻塞")

SOURCE_VALUES = ("开发", "审查发现", "证伪轮", "用户")
CLASS_VALUES = ("功能型", "非功能型")
SUBCLASS_VALUES = {
    "功能型": ("逻辑", "边界", "数据", "状态", "集成"),
    "非功能型": ("性能", "用户体验", "安全", "兼容性", "可靠性"),
}
BUG_REQUIRED = ("source", "story", "class", "subclass", "type", "symptom",
                "root_cause", "trigger", "fix", "prevention", "pattern")
BUG_ID_RE = re.compile(r"BUG-(\d+)\Z")

# defer-add（2026-09-15 副作用纪律修订）：保留确认类动作的入队原因枚举——
# 用户配置 改用户级配置 / 破坏性操作 破坏性或共享操作 / 越界改动 越界写盘 /
# 仅人工可做 AI 做不了（secrets、登录、外部服务授权）
DEFER_REASONS = ("用户配置", "破坏性操作", "越界改动", "仅人工可做")
DEFER_REQUIRED = ("skill", "action", "reason")
DEFER_ID_RE = re.compile(r"DA-(\d+)\Z")
# 翻转目标（§五 C·8②）：待办 是唯一可翻转态，这两个是终态
DEFER_RESOLVED = ("已完成", "已拒绝")

# ---- 通用小件 ----

def _doc_path(args, name):
    return os.path.join(args.output_dir, name + ".yaml")


def _rel(args, path):
    # where / 回执路径统一相对 project-root、正斜杠（契约 §3）
    try:
        rel = os.path.relpath(path, args.project_root)
    except ValueError:
        rel = path
    return rel.replace(os.sep, "/")


def _receipt(args, ok, violations=None, warnings=None, counts=None, updated=None, **extra):
    fields = {
        "project_root": args.project_root,
        "output_dir": args.output_dir,
        "instance": getattr(args, "instance", None),
        "violations": violations or [],
        "warnings": warnings or [],
        "counts": counts or {},
    }
    if updated is not None:
        fields["updated"] = updated
    fields.update(extra)
    return lib.receipt(args.command, ok, **fields)


def _fail(args, violations):
    if isinstance(violations, dict):
        violations = [violations]
    return _receipt(args, False, violations=violations)


def _load(args, name):
    """读一个写回目标产物；返回 (doc, path, violation)。缺失/解析错/顶层非映射 → 违规
    （不为半写产物兜底，BUG-011 同类：错误路径与主路径同等标准）。"""
    path = _doc_path(args, name)
    rel = _rel(args, path)
    if not os.path.isfile(path):
        return None, path, lib.v("MISSING_FILE", rel,
                                 f"{rel} 不存在——先运行上游技能生成该产物")
    try:
        doc = lib.load_yaml(path)
    except yaml.YAMLError as e:
        return None, path, lib.v("UNPARSABLE_YAML", rel,
                                 f"{rel} 解析失败（{e.__class__.__name__}）——修复后重跑")
    if not isinstance(doc, dict):
        return None, path, lib.v("UNPARSABLE_YAML", rel,
                                 f"{rel} 顶层不是映射（形状异常）——修复后重跑")
    return doc, path, None


def _bump(args, path, doc):
    """bump project.updated；返回违规或 None。project 形状异常拒绝写（不猜不补）。"""
    proj = doc.get("project")
    rel = _rel(args, path)
    if not isinstance(proj, dict):
        return lib.v("EMPTY_FIELD", rel, f"{rel} 的 project 缺失或不是映射——形状异常，拒绝写回")
    proj["updated"] = lib.now()
    return None


def _task_list(args, path, doc):
    """取 tasks 列表；返回 (tasks, violation)。键缺失视为空表，非列表 → 形状违规。"""
    tasks = doc.get("tasks")
    if tasks is None:
        return [], None
    if not isinstance(tasks, list):
        rel = _rel(args, path)
        return None, lib.v("UNPARSABLE_YAML", rel, f"{rel} 的 tasks 不是列表（形状异常）——修复后重跑")
    return tasks, None


def _task_index(tasks, story):
    for i, task in enumerate(tasks):
        if isinstance(task, dict) and task.get("story") == story:
            return i
    return None


def _find_entry(entries, key, value):
    """在条目列表中按 key 找首个匹配项，返回索引或 None。"""
    for i, item in enumerate(entries):
        if isinstance(item, dict) and item.get(key) == value:
            return i
    return None


def _nonempty(value):
    return isinstance(value, str) and value.strip() != ""
