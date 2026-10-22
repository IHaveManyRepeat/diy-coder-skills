# -*- coding: utf-8 -*-
"""diyc writeback 状态机命令：transition / green / done（契约 §4.5-4.7）。"""

import diyc_lib as lib

from diyc_writeback_lib import (LEGAL_EDGES, _bump, _doc_path, _fail, _find_entry,
                                _load, _nonempty, _receipt, _rel, _task_index,
                                _task_list)

# ---- transition（§4.5） ----

def _transition(args):
    # trace: S-9 AC-9.1 TC-9.1.1（diy-build-loop HALT 状态迁移写回；待审查→已完成 不在本命令）
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
        if dst == "已完成":
            msg += ("——待审查→已完成 必须走 diyc.py done（真源回填机制化，BUG-012），"
                    "不得经 transition 直接跳转")
        else:
            msg += "（合法边见 diyc.py transition 契约：含 待办/进行中/待审查→已阻塞、"
            msg += "已阻塞→待办、已完成→进行中 等）"
        return _fail(args, lib.v("ILLEGAL_TRANSITION",
                                 f"{rel} tasks[{args.story}].status", msg))
    if dst == "已阻塞" and not _nonempty(args.reason):
        return _fail(args, lib.v("EMPTY_FIELD", f"{rel} tasks[{args.story}].blocked_reason",
                                 "--to 已阻塞 必须给 --reason（阻塞原因，写明缺口与解除路径）"))
    # 不可变组装：基于旧任务构建新条目后整体替换
    new_task = dict(task)
    new_task["status"] = dst
    if dst == "已阻塞":
        new_task["blocked_reason"] = args.reason
    elif src == "已阻塞" and dst == "待办":
        new_task.pop("blocked_reason", None)  # 阻塞解除：清 reason
    elif src == "已完成" and dst == "进行中":
        # 重开即清旧 verdict（SS-012-04，与 runner.py --reopen-failed 同语义）；
        # 不清则留下「进行中 + 旧 augment」的陈旧组合，check 的枚举校验抓不到
        new_task.pop("augment", None)
    if args.rounds is not None:
        loop = {"at": lib.today(), "rounds": args.rounds}
        if dst == "已阻塞":
            loop["outcome"] = "已阻塞"  # loop.outcome 仅在终态出现
        new_task["loop"] = loop
    elif dst == "已阻塞" and isinstance(task.get("loop"), dict):
        loop = dict(task["loop"])
        loop["outcome"] = "已阻塞"
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
    if task.get("status") != "进行中":
        return _fail(args, lib.v("STATUS_MISMATCH", f"{rel} tasks[{args.story}].status",
                                 f"任务状态为 {task.get('status')}，只有进行中的任务可写证据"))
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
        # DUPLICATE_KEY 与 UNPARSABLE_YAML 区分（底单 :364 ⑤：重复键≠解析失败）
        code = docs.yaml_err_code("test-plan") or "UNPARSABLE_YAML"
        label = "重复键" if code == "DUPLICATE_KEY" else "解析失败"
        return _fail(args, lib.v(code, rel_tp, f"{rel_tp} {label}：{err}"))
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

    # Q-121 兜底：retired TC 跳过不写（evidence 与 test-plan status 回填均不落，其余照写）——
    # check 期主防线强制移出 test_refs，此为既有产物（test_refs 过时）的时间窗兜底，不打断开发循环
    active, skipped_retired = [], []
    for tc, red, green in zip(tcs, reds, greens):
        pos = _find_entry(tp_cases, "id", tc)
        if pos is not None and "retired" in tp_cases[pos]:
            skipped_retired.append(tc)
        else:
            active.append((tc, red, green))

    # sprint evidence 追加：同 tc 已有条目 → 替换（HALT 续跑幂等，不叠加重复）
    new_task = dict(task)
    if active:
        evidence = list(new_task.get("evidence") or [])
        for tc, red, green in active:
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

    # test-plan 真源回填：本次 tc → status: 通过（已是 通过 跳过；retired 跳过不写）
    backfilled = []
    for tc, red, green in active:
        pos = _find_entry(tp_cases, "id", tc)
        if pos is not None and tp_cases[pos].get("status") != "通过":
            tp_cases[pos]["status"] = "通过"
            backfilled.append(tc)

    if active:
        # 全部 skipped_retired 时零落盘（无可写内容：不 bump 不存，避免空 evidence 键副作用）
        for p, d in ((path, doc), (tp_path, tp_doc)):
            viol = _bump(args, p, d)
            if viol:
                return _fail(args, viol)
        lib.save_yaml_atomic(path, doc)
        lib.save_yaml_atomic(tp_path, tp_doc)
    proj = doc.get("project")
    return _receipt(args, True,
                    updated=proj.get("updated") if isinstance(proj, dict) else None,
                    story=args.story,
                    evidence_written=[tc for tc, _, _ in active],
                    test_plan_backfilled=backfilled, skipped_retired=skipped_retired)


# ---- done（§4.7） ----

def _done(args):
    # trace: S-9 AC-9.1 TC-9.1.2（待审查→已完成 终态；三真源同批回填，BUG-012）
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
    if task.get("status") != "待审查":
        return _fail(args, lib.v("STATUS_MISMATCH", f"{rel} tasks[{args.story}].status",
                                 f"任务状态为 {task.get('status')}，只有待审查态任务可定稿为已完成"
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
        # DUPLICATE_KEY 与 UNPARSABLE_YAML 区分（底单 :364 ⑤：重复键≠解析失败）
        code = docs.yaml_err_code("stories") or "UNPARSABLE_YAML"
        label = "重复键" if code == "DUPLICATE_KEY" else "解析失败"
        return _fail(args, lib.v(code, rel_stories, f"{rel_stories} {label}：{err}"))
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

    # 终态写：sprint 任务已完成（--rounds 时写 loop outcome: 已完成；已有 loop 补终态结论）
    new_task = dict(task)
    new_task["status"] = "已完成"
    if args.rounds is not None:
        new_task["loop"] = {"at": lib.today(), "rounds": args.rounds, "outcome": "已完成"}
    elif isinstance(new_task.get("loop"), dict):
        loop = dict(new_task["loop"])
        loop["outcome"] = "已完成"
        new_task["loop"] = loop
    tasks[idx] = new_task
    if doc.get("tasks") is None:
        doc["tasks"] = tasks

    stories_backfilled = s_entries[s_pos].get("status") != "已完成"
    s_entries[s_pos]["status"] = "已完成"

    tp_backfilled = []
    for tc in refs:
        if not any(e.get("tc") == tc and _nonempty(e.get("green")) for e in evidence):
            continue  # 只回填本任务已绿的 TC
        pos = _find_entry(tp_cases, "id", tc)
        if pos is not None and tp_cases[pos].get("status") != "通过":
            tp_cases[pos]["status"] = "通过"
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
