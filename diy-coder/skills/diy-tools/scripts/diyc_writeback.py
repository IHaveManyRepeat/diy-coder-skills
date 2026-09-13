# -*- coding: utf-8 -*-
"""diyc 写回命令模块（批次 3 / W3）：transition、green、done、bug-add、reconcile。

把散落在各 SKILL.md 提示词里的多文件手改 YAML 收敛为原子脚本操作。规则来源
（.analysis/2026-09-13-cross-skill/batch3-contract.md）：

- §4.5 transition：diy-build-loop HALT 状态迁移，合法边表冻结；review→done 故意不在
  边表——强制走 done 命令做真源回填（BUG-012 机制化）。
- §4.6 green：diy-dev / diy-build-loop 红绿证据写回——sprint 任务 evidence 追加
  （同 tc 替换，HALT 续跑幂等）+ test-plan 该 TC status: pass 回填。
- §4.7 done：review→done 终态写——sprint / stories / test-plan 三真源同批回填。
- §4.8 bug-add：diy-review 缺陷入库——枚举校验 + BUG- 序号铸造（现有最大 +1，三位补零）。
- §4.9 reconcile：diy-sprint Create/Update 机制化——任务集对账；TDD 门判定只经
  diyc_lib.Docs.story_covered()（与 check 共享唯一定义，禁止二份实现）。

写回纪律（契约 §3）：全文 load → 就地改 → safe_dump(allow_unicode=True,
sort_keys=False) → 同目录临时文件 + os.replace 原子替换，统一经
diyc_lib.save_yaml_atomic（对齐 runner.save_sprint 先例）。校验不过零写入；
诊断中文；回执 schema 见契约 §3，写回命令含 updated（bump 后日期）。
"""
import json
import os
import re

import yaml

import diyc_lib as lib

# ---- 冻结常量（契约 §4.5 / §4.8） ----

# 合法迁移边；review→done 缺席是刻意的（走 done 命令，禁止手工跳转）
LEGAL_EDGES = frozenset({
    ("pending", "in-progress"),
    ("pending", "blocked"),
    ("in-progress", "blocked"),
    ("review", "blocked"),
    ("in-progress", "review"),
    ("review", "in-progress"),
    ("blocked", "pending"),
    ("done", "in-progress"),
})

# reconcile 门重算域：review/done 是审计产物一律不动；blocked 参与（恢复覆盖可解除）
REGATE_STATUSES = ("pending", "in-progress", "blocked")

SOURCE_VALUES = ("dev", "audit", "falsification", "user")
CLASS_VALUES = ("functional", "non-functional")
SUBCLASS_VALUES = {
    "functional": ("logic", "boundary", "data", "state", "integration"),
    "non-functional": ("performance", "UX", "security", "compatibility", "reliability"),
}
BUG_REQUIRED = ("source", "story", "class", "subclass", "type", "symptom",
                "root_cause", "trigger", "fix", "prevention", "pattern")
BUG_ID_RE = re.compile(r"BUG-(\d+)\Z")


def run(args) -> dict:
    # 入口（契约 §2）：args 由 diyc.py 组装（含 resolved output_dir 与 args.command）
    if args.command == "transition":
        return _transition(args)
    if args.command == "green":
        return _green(args)
    if args.command == "done":
        return _done(args)
    if args.command == "bug-add":
        return _bug_add(args)
    if args.command == "reconcile":
        return _reconcile(args)
    raise ValueError(f"diyc_writeback 不认识的子命令：{args.command!r}（diyc.py 接线 bug）")


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
    proj["updated"] = lib.today()
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


# ---- transition（§4.5） ----

def _transition(args):
    # trace: S-9 AC-9.1 TC-9.1.1（diy-build-loop HALT 状态迁移写回；review→done 不在本命令）
    doc, path, viol = _load(args, "sprint")
    if viol:
        return _fail(args, viol)
    rel = _rel(args, path)
    tasks, viol = _task_list(args, path, doc)
    if viol:
        return _fail(args, viol)
    idx = _task_index(tasks, args.story)
    if idx is None:
        return _fail(args, lib.v("UNKNOWN_ID", rel,
                                 f"story {args.story} 不在 sprint.yaml 任务表中"))
    task = tasks[idx]
    src, dst = task.get("status"), args.to
    if (src, dst) not in LEGAL_EDGES:
        msg = f"非法迁移 {src} → {dst}"
        if dst == "done":
            msg += ("——review→done 必须走 diyc.py done（真源回填机制化，BUG-012），"
                    "不得经 transition 直接跳转")
        else:
            msg += "（合法边见 diyc.py transition 契约：含 pending/in-progress/review→blocked、"
            msg += "blocked→pending、done→in-progress 等）"
        return _fail(args, lib.v("ILLEGAL_TRANSITION",
                                 f"{rel} tasks[{args.story}].status", msg))
    if dst == "blocked" and not _nonempty(args.reason):
        return _fail(args, lib.v("EMPTY_FIELD", f"{rel} tasks[{args.story}].blocked_reason",
                                 "--to blocked 必须给 --reason（阻塞原因，写明缺口与解除路径）"))
    # 不可变组装：基于旧任务构建新条目后整体替换
    new_task = dict(task)
    new_task["status"] = dst
    if dst == "blocked":
        new_task["blocked_reason"] = args.reason
    elif src == "blocked" and dst == "pending":
        new_task.pop("blocked_reason", None)  # 阻塞解除：清 reason
    if args.rounds is not None:
        loop = {"at": lib.today(), "rounds": args.rounds}
        if dst == "blocked":
            loop["outcome"] = "blocked"  # loop.outcome 仅在终态出现
        new_task["loop"] = loop
    elif dst == "blocked" and isinstance(task.get("loop"), dict):
        loop = dict(task["loop"])
        loop["outcome"] = "blocked"
        new_task["loop"] = loop
    tasks[idx] = new_task
    if doc.get("tasks") is None:
        doc["tasks"] = tasks
    viol = _bump(args, path, doc)
    if viol:
        return _fail(args, viol)
    lib.save_yaml_atomic(path, doc)
    return _receipt(args, True, updated=doc["project"]["updated"],
                    story=args.story, **{"from": src, "to": dst})


# ---- green（§4.6） ----

def _green(args):
    # trace: S-7 AC-7.1 TC-7.1.1（diy-dev 先红后绿证据写回 + test-plan 真源回填）
    tcs = list(args.tc or [])
    reds = list(args.red or [])
    greens = list(args.green or [])
    rel_sprint = _rel(args, _doc_path(args, "sprint"))
    if not tcs:
        return _fail(args, lib.v("EMPTY_FIELD", f"{rel_sprint} tasks.evidence",
                                 "至少给一组 --tc/--red/--green"))
    if not (len(tcs) == len(reds) == len(greens)):
        return _fail(args, lib.v("SET_MISMATCH", f"{rel_sprint} tasks.evidence",
                                 f"--tc/--red/--green 数量不一致（{len(tcs)}/{len(reds)}/"
                                 f"{len(greens)}）——三参数必须一一对应"))
    if len(set(tcs)) != len(tcs):
        return _fail(args, lib.v("DUPLICATE_ID", f"{rel_sprint} tasks.evidence",
                                 f"--tc 重复出现：{'、'.join(tcs)}"))
    for tc, red, green in zip(tcs, reds, greens):
        if not _nonempty(red):
            return _fail(args, lib.v("EMPTY_FIELD", f"{rel_sprint} tasks.evidence[{tc}]",
                                     f"--red 为空（{tc}）——红绿必须记录实际执行输出"))
        if not _nonempty(green):
            return _fail(args, lib.v("EMPTY_FIELD", f"{rel_sprint} tasks.evidence[{tc}]",
                                     f"--green 为空（{tc}）——红绿必须记录实际执行输出"))

    doc, path, viol = _load(args, "sprint")
    if viol:
        return _fail(args, viol)
    rel = _rel(args, path)
    tasks, viol = _task_list(args, path, doc)
    if viol:
        return _fail(args, viol)
    idx = _task_index(tasks, args.story)
    if idx is None:
        return _fail(args, lib.v("UNKNOWN_ID", rel, f"story {args.story} 不在 sprint.yaml 任务表中"))
    task = tasks[idx]
    if task.get("status") != "in-progress":
        return _fail(args, lib.v("STATUS_MISMATCH", f"{rel} tasks[{args.story}].status",
                                 f"任务状态为 {task.get('status')}，只有 in-progress 的任务可写证据"))
    refs = task.get("test_refs") or []
    for tc in tcs:
        if tc not in refs:
            return _fail(args, lib.v("UNKNOWN_ID", f"{rel} tasks[{args.story}].test_refs",
                                     f"{tc} 不在任务 {args.story} 的 test_refs 中——"
                                     f"先经 diy-sprint reconcile 更新任务范围"))

    # 跨文档核对经 Docs（唯一索引入口）：TC 必须在 test-plan 中存在
    docs = lib.Docs(args.project_root, args.output_dir)
    rel_tp = _rel(args, _doc_path(args, "test-plan"))
    err = docs.yaml_err("test-plan")
    if err:
        return _fail(args, lib.v("UNPARSABLE_YAML", rel_tp, f"{rel_tp} 解析失败：{err}"))
    known = docs.tcs()
    for tc in tcs:
        if tc not in known:
            return _fail(args, lib.v("UNKNOWN_ID", f"{rel_tp} test_cases",
                                     f"{tc} 在 test-plan.yaml 中不存在"))
    tp_doc, tp_path, viol = _load(args, "test-plan")
    if viol:
        return _fail(args, viol)
    tp_cases = tp_doc.get("test_cases")
    if not isinstance(tp_cases, list):
        return _fail(args, lib.v("UNPARSABLE_YAML", rel_tp,
                                 f"{rel_tp} 的 test_cases 不是列表（形状异常）——修复后重跑"))

    # sprint evidence 追加：同 tc 已有条目 → 替换（HALT 续跑幂等，不叠加重复）
    new_task = dict(task)
    evidence = list(new_task.get("evidence") or [])
    for tc, red, green in zip(tcs, reds, greens):
        entry = {"tc": tc, "red": red.strip(), "green": green.strip()}
        pos = _find_entry(evidence, "tc", tc)
        evidence = [e for e in evidence if not (isinstance(e, dict) and e.get("tc") == tc)]
        if pos is None:
            evidence.append(entry)
        else:
            evidence.insert(min(pos, len(evidence)), entry)
    new_task["evidence"] = evidence
    tasks[idx] = new_task
    if doc.get("tasks") is None:
        doc["tasks"] = tasks

    # test-plan 真源回填：本次 tc → status: pass（已是 pass 跳过）
    backfilled = []
    for tc in tcs:
        pos = _find_entry(tp_cases, "id", tc)
        if pos is not None and tp_cases[pos].get("status") != "pass":
            tp_cases[pos]["status"] = "pass"
            backfilled.append(tc)

    for p, d in ((path, doc), (tp_path, tp_doc)):
        viol = _bump(args, p, d)
        if viol:
            return _fail(args, viol)
    lib.save_yaml_atomic(path, doc)
    lib.save_yaml_atomic(tp_path, tp_doc)
    return _receipt(args, True, updated=doc["project"]["updated"], story=args.story,
                    evidence_written=tcs, test_plan_backfilled=backfilled)


# ---- done（§4.7） ----

def _done(args):
    # trace: S-9 AC-9.1 TC-9.1.2（review→done 终态；三真源同批回填，BUG-012）
    doc, path, viol = _load(args, "sprint")
    if viol:
        return _fail(args, viol)
    rel = _rel(args, path)
    tasks, viol = _task_list(args, path, doc)
    if viol:
        return _fail(args, viol)
    idx = _task_index(tasks, args.story)
    if idx is None:
        return _fail(args, lib.v("UNKNOWN_ID", rel, f"story {args.story} 不在 sprint.yaml 任务表中"))
    task = tasks[idx]
    if task.get("status") != "review":
        return _fail(args, lib.v("STATUS_MISMATCH", f"{rel} tasks[{args.story}].status",
                                 f"任务状态为 {task.get('status')}，只有 review 态任务可定稿 done"
                                 f"（先经 diy-review 三层审查）"))
    refs = list(task.get("test_refs") or [])
    evidence = [e for e in (task.get("evidence") or []) if isinstance(e, dict)]
    misses = []
    for tc in refs:
        entry = next((e for e in evidence if e.get("tc") == tc), None)
        if entry is None or not _nonempty(entry.get("red")) or not _nonempty(entry.get("green")):
            misses.append(tc)
    if misses:
        return _fail(args, lib.v("EVIDENCE_MISSING", f"{rel} tasks[{args.story}].evidence",
                                 f"test_refs 中 {'、'.join(misses)} 缺完整 evidence"
                                 f"（red/green 均非空）——补 diyc.py green 后重跑"))

    docs = lib.Docs(args.project_root, args.output_dir)
    rel_stories = _rel(args, _doc_path(args, "stories"))
    err = docs.yaml_err("stories")
    if err:
        return _fail(args, lib.v("UNPARSABLE_YAML", rel_stories, f"{rel_stories} 解析失败：{err}"))
    if args.story not in docs.stories():
        return _fail(args, lib.v("UNKNOWN_ID", f"{rel_stories} stories",
                                 f"story {args.story} 不在 stories.yaml 中"))
    stories_doc, stories_path, viol = _load(args, "stories")
    if viol:
        return _fail(args, viol)
    s_entries = stories_doc.get("stories")
    if not isinstance(s_entries, list):
        return _fail(args, lib.v("UNPARSABLE_YAML", rel_stories,
                                 f"{rel_stories} 的 stories 不是列表（形状异常）——修复后重跑"))
    s_pos = _find_entry(s_entries, "id", args.story)
    if s_pos is None:
        return _fail(args, lib.v("UNKNOWN_ID", rel_stories,
                                 f"story {args.story} 不在 stories.yaml 中"))
    tp_doc, tp_path, viol = _load(args, "test-plan")
    if viol:
        return _fail(args, viol)
    rel_tp = _rel(args, tp_path)
    tp_cases = tp_doc.get("test_cases")
    if not isinstance(tp_cases, list):
        return _fail(args, lib.v("UNPARSABLE_YAML", rel_tp,
                                 f"{rel_tp} 的 test_cases 不是列表（形状异常）——修复后重跑"))

    # 终态写：sprint 任务 done（--rounds 时写 loop outcome: done；已有 loop 补终态结论）
    new_task = dict(task)
    new_task["status"] = "done"
    if args.rounds is not None:
        new_task["loop"] = {"at": lib.today(), "rounds": args.rounds, "outcome": "done"}
    elif isinstance(new_task.get("loop"), dict):
        loop = dict(new_task["loop"])
        loop["outcome"] = "done"
        new_task["loop"] = loop
    tasks[idx] = new_task
    if doc.get("tasks") is None:
        doc["tasks"] = tasks

    stories_backfilled = s_entries[s_pos].get("status") != "done"
    s_entries[s_pos]["status"] = "done"

    tp_backfilled = []
    for tc in refs:
        if not any(e.get("tc") == tc and _nonempty(e.get("green")) for e in evidence):
            continue  # 只回填本任务已绿的 TC
        pos = _find_entry(tp_cases, "id", tc)
        if pos is not None and tp_cases[pos].get("status") != "pass":
            tp_cases[pos]["status"] = "pass"
            tp_backfilled.append(tc)

    for p, d in ((path, doc), (stories_path, stories_doc), (tp_path, tp_doc)):
        viol = _bump(args, p, d)
        if viol:
            return _fail(args, viol)
    lib.save_yaml_atomic(path, doc)
    lib.save_yaml_atomic(stories_path, stories_doc)
    lib.save_yaml_atomic(tp_path, tp_doc)
    return _receipt(args, True, updated=doc["project"]["updated"], story=args.story,
                    backfilled={"stories": stories_backfilled, "test_plan": tp_backfilled})


# ---- bug-add（§4.8） ----

def _read_entry(args):
    """解析 --entry / --entry-file 的 JSON 对象；返回 (entry, violation)。"""
    entry_arg = args.entry
    entry_file = args.entry_file
    if entry_arg and entry_file:
        return None, lib.v("SET_MISMATCH", "bug-add --entry",
                           "--entry 与 --entry-file 互斥，只给其一")
    if not entry_arg and not entry_file:
        return None, lib.v("EMPTY_FIELD", "bug-add --entry",
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
        return None, lib.v("ENTRY_INVALID", "bug-add --entry",
                           f"entry 不是合法 JSON（{e.__class__.__name__}）——检查引号与转义")
    if not isinstance(data, dict):
        return None, lib.v("ENTRY_INVALID", "bug-add --entry", "entry 顶层必须是 JSON 对象")
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
    entry, viol = _read_entry(args)
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
        doc = {"project": {"name": _project_name(args), "created": lib.today(),
                           "updated": lib.today()},
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


# ---- reconcile（§4.9） ----

def _gap_reason(missing):
    return (f"{'、'.join(missing)} 无用例（decision: pending）——"
            f"补用例或裁 waived/accept-gap 后重跑 reconcile")


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
            vio.append(lib.v("UNPARSABLE_YAML", rel, f"{rel} 解析失败：{err}"))
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
    # add：有 story 无任务（story done → done；缺覆盖 → blocked + reason；否则 pending）
    add = []
    for sid, story in stories.items():
        if sid in by_story:
            continue
        covered, missing = docs.story_covered(sid)
        refs = docs.tcs_for_story(sid)
        if story.get("status") == "done":
            add.append({"story": sid, "status": "done", "test_refs": refs})
        elif not covered:
            add.append({"story": sid, "status": "blocked", "test_refs": refs,
                        "blocked_reason": _gap_reason(missing)})
        else:
            add.append({"story": sid, "status": "pending", "test_refs": refs})

    # remove：有任务无 story
    remove = [task.get("story") for task in raw_tasks if task.get("story") not in stories]

    # changed：非终态重算门 + test_refs 重推（review/done 审计产物一律不动）
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
            if not covered and new_task.get("status") != "blocked":
                new_task["status"] = "blocked"
                new_task["blocked_reason"] = _gap_reason(missing)
                fields += ["status", "blocked_reason"]
            elif covered and new_task.get("status") == "blocked":
                new_task["status"] = "pending"
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
        if task.get("status") == "done" and not _nonempty(task.get("note")):
            warnings.append(f"{sid} 任务 done 但无 note——审计追踪缺失，建议补记")
        story = stories.get(sid)
        if story is not None and story.get("status") == "done" and task.get("status") != "done":
            warnings.append(f"{sid} 的 story 已 done 但任务仍 {task.get('status')}"
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
            # name 取 stories.yaml 的 project.name，缺省 "project"；status: draft，技能侧随后可改 final
            sdoc = docs.doc("stories") or {}
            sproj = sdoc.get("project")
            sname = sproj.get("name") if isinstance(sproj, dict) else None
            existing = {"project": {"name": sname if _nonempty(sname) else "project",
                                    "status": "draft", "created": lib.today(),
                                    "updated": lib.today()},
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
