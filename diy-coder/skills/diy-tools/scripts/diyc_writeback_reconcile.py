# -*- coding: utf-8 -*-
"""diyc writeback 对账命令：reconcile（契约 §4.9）。"""

import os

import yaml

import diyc_lib as lib
from diyc_lib_base import DuplicateKeyError

from diyc_writeback_lib import (REGATE_STATUSES, _bump, _doc_path, _fail,
                                _nonempty, _receipt, _rel)

# ---- reconcile（§4.9） ----

def _gap_reason(missing):
    return (f"{'、'.join(missing)} 无用例（decision: 待办）——"
            f"补用例或裁 已豁免/接受缺口 后重跑 reconcile")


def _insert_by_order(tasks, new_task, order):
    """新任务按 story 顺序插到第一个更靠后的既有任务之前；既有任务相对顺序不变。"""
    pos = order.get(new_task["story"], len(order))
    for i, task in enumerate(tasks):
        if order.get(task.get("story"), len(order)) > pos:
            tasks.insert(i, new_task)
            return
    tasks.append(new_task)


def _reconcile(args):
    # trace: S-6 AC-6.1 TC-6.1.2（任务集与 story 集对账；门判定只经 Docs.story_covered）
    docs = lib.Docs(args.project_root, args.output_dir)
    vio = []
    for name in ("stories", "test-plan"):
        rel = _rel(args, _doc_path(args, name))
        err = docs.yaml_err(name)
        if err:
            # DUPLICATE_KEY 与 UNPARSABLE_YAML 区分（底单 :364 ⑤：重复键≠解析失败）
            code = docs.yaml_err_code(name) or "UNPARSABLE_YAML"
            vio.append(lib.v(code, rel, f"{rel} 解析失败：{err}"))
        elif docs.doc(name) is None:
            vio.append(lib.v("MISSING_FILE", rel,
                             f"{rel} 不存在——reconcile 依赖 stories 与 test-plan 计算 TDD 门"))
    if vio:
        return _fail(args, vio)
    stories = docs.stories()
    # 半写守卫：文档存在但零 story / 无 test_cases → 拒绝（否则全部任务会被当孤儿清除，
    # 与 BUG-011 同类——错误路径不得以静默破坏收场）
    if not stories:
        return _fail(args, lib.v("EMPTY_FIELD", _rel(args, _doc_path(args, "stories")),
                                 "stories.yaml 无 story 条目（空文件/半写产物）——"
                                 "先运行 diy-epics-stories 生成"))
    if not isinstance((docs.doc("test-plan") or {}).get("test_cases"), list):
        return _fail(args, lib.v("UNPARSABLE_YAML", _rel(args, _doc_path(args, "test-plan")),
                                 "test-plan.yaml 的 test_cases 缺失或不是列表（半写产物）——"
                                 "修复后重跑"))

    sprint_path = _doc_path(args, "sprint")
    srel = _rel(args, sprint_path)
    existing = None
    if os.path.isfile(sprint_path):
        try:
            existing = lib.load_yaml(sprint_path)
        except DuplicateKeyError as e:
            # DUPLICATE_KEY 与 UNPARSABLE_YAML 区分（底单 :364 ⑤）
            return _fail(args, lib.v("DUPLICATE_KEY", srel,
                                     f"{srel} 重复键（{e}）——修复后重跑"))
        except yaml.YAMLError as e:
            return _fail(args, lib.v("UNPARSABLE_YAML", srel,
                                     f"{srel} 解析失败（{e.__class__.__name__}）——修复后重跑"))
        if not isinstance(existing, dict):
            return _fail(args, lib.v("UNPARSABLE_YAML", srel, f"{srel} 顶层不是映射（形状异常）"))
    raw_tasks = [] if existing is None else (existing.get("tasks") or [])
    if not isinstance(raw_tasks, list):
        return _fail(args, lib.v("UNPARSABLE_YAML", srel,
                                 f"{srel} 的 tasks 不是列表（形状异常）——修复后重跑"))
    by_story = {}
    for task in raw_tasks:
        if not isinstance(task, dict):
            return _fail(args, lib.v("UNPARSABLE_YAML", f"{srel} tasks",
                                     f"{srel} tasks 含非映射条目（形状异常）——修复后重跑"))
        sid = task.get("story")
        if not _nonempty(sid):
            return _fail(args, lib.v("EMPTY_FIELD", f"{srel} tasks", "任务缺 story 字段"))
        if sid in by_story:
            return _fail(args, lib.v("DUPLICATE_ID", f"{srel} tasks",
                                     f"story {sid} 有多个任务条目——先人工裁定再 reconcile"))
        by_story[sid] = task

    order = {sid: i for i, sid in enumerate(stories)}
    # add：有 story 无任务（story 已完成 → 已完成；缺覆盖 → 已阻塞 + reason；否则 待办）
    add = []
    for sid, story in stories.items():
        if sid in by_story:
            continue
        covered, missing = docs.story_covered(sid)
        refs = docs.tcs_for_story(sid)
        if story.get("status") == "已完成":
            add.append({"story": sid, "status": "已完成", "test_refs": refs})
        elif not covered:
            add.append({"story": sid, "status": "已阻塞", "test_refs": refs,
                        "blocked_reason": _gap_reason(missing)})
        else:
            add.append({"story": sid, "status": "待办", "test_refs": refs})

    # remove：有任务无 story
    remove = [task.get("story") for task in raw_tasks if task.get("story") not in stories]

    # changed：非终态重算门 + test_refs 重推（待审查/已完成 审计产物一律不动）
    changed = []
    kept = []
    for task in raw_tasks:
        sid = task.get("story")
        if sid not in stories:
            continue
        new_task = dict(task)
        fields = []
        if new_task.get("status") in REGATE_STATUSES:
            covered, missing = docs.story_covered(sid)
            if not covered and new_task.get("status") != "已阻塞":
                new_task["status"] = "已阻塞"
                new_task["blocked_reason"] = _gap_reason(missing)
                fields += ["status", "blocked_reason"]
            elif covered and new_task.get("status") == "已阻塞":
                new_task["status"] = "待办"
                new_task.pop("blocked_reason", None)
                fields += ["status", "blocked_reason"]
            refs = docs.tcs_for_story(sid)
            if list(new_task.get("test_refs") or []) != refs:
                new_task["test_refs"] = refs
                fields.append("test_refs")
        if fields:
            changed.append({"story": sid, "fields": fields})
        kept.append(new_task)

    new_tasks = list(kept)
    for nt in sorted(add, key=lambda t: order.get(t["story"], len(order))):
        _insert_by_order(new_tasks, nt, order)

    warnings = []
    for task in new_tasks:
        sid = task.get("story")
        if task.get("status") == "已完成" and not _nonempty(task.get("note")):
            warnings.append(f"{sid} 任务已完成但无 note——审计追踪缺失，建议补记")
        story = stories.get(sid)
        if story is not None and story.get("status") == "已完成" and task.get("status") != "已完成":
            warnings.append(f"{sid} 的 story 已完成但任务仍 {task.get('status')}"
                            f"——不伪造交付，人工裁定（走 done 命令或重开）")

    actions = {
        "add": [{"story": t["story"], "status": t["status"], "test_refs": t["test_refs"]}
                for t in add],
        "remove": remove,
        "changed": changed,
    }
    counts = {"stories": len(stories), "tasks": len(new_tasks),
              "add": len(add), "remove": len(remove), "changed": len(changed)}

    updated = None
    if args.apply and (add or remove or changed):
        if existing is None:
            # Create（契约 §4.9 裁定）：sprint.yaml 缺席 → 建骨架 + tasks 全量（从 stories 构建）；
            # name 取 stories.yaml 的 project.name，缺省 "project"；status: 草稿，技能侧随后可改 已定稿
            sdoc = docs.doc("stories") or {}
            sproj = sdoc.get("project")
            sname = sproj.get("name") if isinstance(sproj, dict) else None
            existing = {"project": {"name": sname if _nonempty(sname) else "project",
                                    "status": "草稿", "created": lib.now(),
                                    "updated": lib.now()},
                        "tasks": new_tasks}
        else:
            existing["tasks"] = new_tasks
            viol = _bump(args, sprint_path, existing)
            if viol:
                return _fail(args, viol)
        lib.save_yaml_atomic(sprint_path, existing)
        updated = existing["project"]["updated"]
    return _receipt(args, True, warnings=warnings, counts=counts, updated=updated,
                    applied=bool(args.apply), actions=actions)
