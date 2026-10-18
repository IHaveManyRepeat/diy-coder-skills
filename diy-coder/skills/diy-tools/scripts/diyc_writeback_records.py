# -*- coding: utf-8 -*-
"""diyc writeback 记录类命令：bug-add / stamp / defer-add / defer-set（契约 §4.8/§4.10）。"""

import json
import os

import yaml

import diyc_lib as lib

from diyc_writeback_lib import (BUG_ID_RE, BUG_REQUIRED, CLASS_VALUES, DEFER_ID_RE,
                                DEFER_REASONS, DEFER_REQUIRED, DEFER_RESOLVED,
                                SOURCE_VALUES, SUBCLASS_VALUES, _bump, _doc_path,
                                _fail, _load, _nonempty, _receipt, _rel)

# ---- bug-add（§4.8） ----

def _read_entry(args, command):
    """解析 --entry / --entry-file 的 JSON 对象；返回 (entry, violation)。"""
    entry_arg = args.entry
    entry_file = args.entry_file
    if entry_arg and entry_file:
        return None, lib.v("SET_MISMATCH", f"{command} --entry",
                           "--entry 与 --entry-file 互斥，只给其一")
    if not entry_arg and not entry_file:
        return None, lib.v("EMPTY_FIELD", f"{command} --entry",
                           "必须给 --entry '<json>' 或 --entry-file PATH")
    if entry_file:
        if not os.path.isfile(entry_file):
            return None, lib.v("MISSING_FILE", entry_file, f"entry 文件不存在：{entry_file}")
        try:
            with open(entry_file, encoding="utf-8") as f:
                text = f.read()
        except OSError as e:
            return None, lib.v("MISSING_FILE", entry_file,
                               f"entry 文件读取失败（{e.__class__.__name__}）：{entry_file}")
    else:
        text = entry_arg
    try:
        data = json.loads(text)
    except (ValueError, TypeError) as e:
        return None, lib.v("ENTRY_INVALID", f"{command} --entry",
                           f"entry 不是合法 JSON（{e.__class__.__name__}）——检查引号与转义")
    if not isinstance(data, dict):
        return None, lib.v("ENTRY_INVALID", f"{command} --entry", "entry 顶层必须是 JSON 对象")
    return data, None


def _project_name(args):
    # 新建 bug-log 骨架时取项目名：优先同目录 sprint/stories 的 project.name，回退根目录名
    for name in ("sprint", "stories"):
        path = _doc_path(args, name)
        if not os.path.isfile(path):
            continue
        try:
            doc = lib.load_yaml(path)
        except yaml.YAMLError:
            continue  # 仅用于取名，解析失败降级回目录名（不阻塞入库）
        proj = doc.get("project") if isinstance(doc, dict) else None
        if isinstance(proj, dict) and _nonempty(proj.get("name")):
            return proj["name"]
    return os.path.basename(os.path.abspath(args.project_root)) or "project"


def _bug_add(args):
    # trace: S-8 AC-8.1 TC-8.2.1（diy-review 缺陷入库：枚举校验 + BUG 序号铸造）
    entry, viol = _read_entry(args, "bug-add")
    if viol:
        return _fail(args, viol)
    entry = {k: (v.strip() if isinstance(v, str) else v) for k, v in entry.items()}
    missing = [k for k in BUG_REQUIRED if not _nonempty(entry.get(k))]
    if missing:
        return _fail(args, lib.v("EMPTY_FIELD", "bug-add --entry",
                                 f"必填字段缺失或为空：{'、'.join(missing)}"))
    if entry["source"] not in SOURCE_VALUES:
        return _fail(args, lib.v("ENUM_INVALID", "bug-add --entry.source",
                                 f"source={entry['source']!r} 非法，合法值：{'/'.join(SOURCE_VALUES)}"))
    if entry["class"] not in CLASS_VALUES:
        return _fail(args, lib.v("ENUM_INVALID", "bug-add --entry.class",
                                 f"class={entry['class']!r} 非法，合法值：{'/'.join(CLASS_VALUES)}"))
    allowed = SUBCLASS_VALUES[entry["class"]]
    if entry["subclass"] not in allowed:
        return _fail(args, lib.v("ENUM_INVALID", "bug-add --entry.subclass",
                                 f"subclass={entry['subclass']!r} 不属于大类 {entry['class']}，"
                                 f"合法值：{'/'.join(allowed)}"))

    bug_path = _doc_path(args, "bug-log")
    rel = _rel(args, bug_path)
    if os.path.isfile(bug_path):
        doc, _, viol = _load(args, "bug-log")
        if viol:
            return _fail(args, viol)
        viol = _bump(args, bug_path, doc)
        if viol:
            return _fail(args, viol)
        bugs = doc.get("bugs")
        if bugs is None:
            bugs = []
            doc["bugs"] = bugs
        elif not isinstance(bugs, list):
            return _fail(args, lib.v("UNPARSABLE_YAML", f"{rel} bugs",
                                     f"{rel} 的 bugs 不是列表（形状异常）——拒绝改写"))
    else:
        # 无文件 → 新建骨架（首个 bug 或新实例）
        doc = {"project": {"name": _project_name(args), "created": lib.now(),
                           "updated": lib.now()},
               "bugs": []}
        bugs = doc["bugs"]

    max_n = 0
    for b in bugs:
        if not isinstance(b, dict):
            continue
        m = BUG_ID_RE.match(str(b.get("id") or ""))
        if m:
            max_n = max(max_n, int(m.group(1)))
    new_id = f"BUG-{max_n + 1:03d}"

    bugs.append({
        "id": new_id,
        "date": entry["date"].strip() if _nonempty(entry.get("date")) else lib.today(),
        "source": entry["source"], "story": entry["story"],
        "class": entry["class"], "subclass": entry["subclass"],
        "type": entry["type"], "symptom": entry["symptom"],
        "root_cause": entry["root_cause"], "trigger": entry["trigger"],
        "fix": entry["fix"], "prevention": entry["prevention"],
        "pattern": entry["pattern"],
    })
    # 新建骨架是明确支持场景（首个缺陷/新实例），output_dir 可能尚未创建
    os.makedirs(os.path.dirname(bug_path), exist_ok=True)
    lib.save_yaml_atomic(bug_path, doc)
    return _receipt(args, True, updated=doc["project"]["updated"], id=new_id, file=rel)


# ---- stamp（v4 批 3·二裁全量程序盖章：C 组 AI 建产物「时间键留空＋跑 stamp」） ----

def _stamp(args):
    """产物时间盖章：created 缺则补秒级真值、已有不动（「建文件时设此后不改」
    ＋存量纯日期不回填）；updated 每次刷当前秒级。定位照写回族既有法
    （output_dir 平铺 <type>.yaml，--instance 经 diyc.py resolve 透传）。"""
    doc, path, viol = _load(args, args.type)
    if viol:
        return _fail(args, viol)
    rel = _rel(args, path)
    proj = doc.get("project")
    if not isinstance(proj, dict):
        return _fail(args, lib.v("EMPTY_FIELD", rel,
                                 f"{rel} 的 project 缺失或不是映射——形状异常，拒绝盖章"))
    now = lib.now()
    if not _nonempty(proj.get("created")):
        proj["created"] = now
    proj["updated"] = now
    lib.save_yaml_atomic(path, doc)
    return _receipt(args, True, created=proj["created"], updated=now, file=rel)


# ---- defer-add（2026-09-15 副作用纪律修订） ----

def _defer_add(args):
    # trace: 2026-09-15 副作用纪律修订（B3 任务书 §0 纪律 5 / 迁移计划 §十三）——
    # 保留确认类动作入队（不阻塞任务）：reason 枚举校验 + DA 序号铸造 + 追加写
    entry, viol = _read_entry(args, "defer-add")
    if viol:
        return _fail(args, viol)
    entry = {k: (v.strip() if isinstance(v, str) else v) for k, v in entry.items()}
    missing = [k for k in DEFER_REQUIRED if not _nonempty(entry.get(k))]
    if missing:
        return _fail(args, lib.v("EMPTY_FIELD", "defer-add --entry",
                                 f"必填字段缺失或为空：{'、'.join(missing)}"))
    if entry["reason"] not in DEFER_REASONS:
        return _fail(args, lib.v("ENUM_INVALID", "defer-add --entry.reason",
                                 f"reason={entry['reason']!r} 非法，"
                                 f"合法值：{'/'.join(DEFER_REASONS)}"))

    path = _doc_path(args, "deferred-actions")
    rel = _rel(args, path)
    if os.path.isfile(path):
        doc, _, viol = _load(args, "deferred-actions")
        if viol:
            return _fail(args, viol)
        viol = _bump(args, path, doc)
        if viol:
            return _fail(args, viol)
        actions = doc.get("actions")
        if actions is None:
            actions = []
            doc["actions"] = actions
        elif not isinstance(actions, list):
            return _fail(args, lib.v("UNPARSABLE_YAML", f"{rel} actions",
                                     f"{rel} 的 actions 不是列表（形状异常）——拒绝改写"))
    else:
        # 无文件 → 新建骨架（本体系首个待确认动作；output_dir 可能尚未创建）
        doc = {"project": {"name": _project_name(args), "created": lib.now(),
                           "updated": lib.now()},
               "actions": []}
        actions = doc["actions"]

    max_n = 0
    for a in actions:
        if not isinstance(a, dict):
            continue
        m = DEFER_ID_RE.match(str(a.get("id") or ""))
        if m:
            max_n = max(max_n, int(m.group(1)))
    new_id = f"DA-{max_n + 1:03d}"

    item = {
        "id": new_id,
        "date": entry["date"].strip() if _nonempty(entry.get("date")) else lib.today(),
        "skill": entry["skill"],
        "action": entry["action"],
    }
    if _nonempty(entry.get("command")):
        item["command"] = entry["command"]
    if _nonempty(entry.get("target")):
        item["target"] = entry["target"]
    item["reason"] = entry["reason"]
    item["status"] = "待办"
    actions.append(item)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    lib.save_yaml_atomic(path, doc)
    return _receipt(args, True, updated=doc["project"]["updated"], id=new_id, file=rel)


def _defer_set(args):
    # trace: 迁移计划 §五 C·8②——待确认动作的 status 翻转命令，队列的出口侧。
    # 入队（defer-add）把保留确认类动作由"阻塞任务"改为"留痕待办"；本命令是它的
    # 消费端：用户确认并自行执行后标 已完成，裁定不做后标 已拒绝。只允许
    # 待办 → 已完成|已拒绝 单向（已是终态再翻转一律拒绝，不静默改历史）；
    # 本命令只动 status，动作本身永远由用户执行。
    if args.status not in DEFER_RESOLVED:
        return _fail(args, lib.v("ENUM_INVALID", "defer-set --status",
                                 f"status={args.status!r} 非法，"
                                 f"合法值：{'/'.join(DEFER_RESOLVED)}"))
    doc, path, viol = _load(args, "deferred-actions")
    if viol:
        return _fail(args, viol)
    rel = _rel(args, path)
    actions = doc.get("actions")
    if not isinstance(actions, list):
        return _fail(args, lib.v("UNPARSABLE_YAML", f"{rel} actions",
                                 f"{rel} 的 actions 不是列表（形状异常）——拒绝改写"))
    target = next((a for a in actions
                   if isinstance(a, dict) and a.get("id") == args.id), None)
    if target is None:
        return _fail(args, lib.v("UNKNOWN_ID", rel,
                                 f"{args.id} 不在 {rel} 的 actions 表中"))
    if target.get("status") != "待办":
        return _fail(args, lib.v("ILLEGAL_TRANSITION", f"{rel} {args.id}",
                                 f"{args.id} 当前 status={target.get('status')!r}——"
                                 f"只有 待办 可翻转，已完成/已拒绝 是终态"))
    target["status"] = args.status
    viol = _bump(args, path, doc)
    if viol:
        return _fail(args, viol)
    lib.save_yaml_atomic(path, doc)
    return _receipt(args, True, updated=doc["project"]["updated"],
                    id=args.id, status=args.status, file=rel)
