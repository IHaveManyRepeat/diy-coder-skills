# -*- coding: utf-8 -*-
"""diy-test-review walkthrough 子命令面：diyc 委派 + AC ↔ 源码 ↔ 测试三向对账。"""
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import display_path, diyc_script_path, emit_via, items, load_yaml_safe, nonempty, v  # noqa: E402

from test_review_lib import (  # noqa: E402
    AC_RE, GAP_KINDS, STORIES_FILE, TEST_PLAN_FILE,
)


# ---------------------------------------------------------------- diyc 委派


def diyc_call(script, args_list):
    """跑 diyc 子命令。rc∈{0,1} = 正常回执；rc=2/不可解析/缺席 → (None, warning)。"""
    where = "diyc.py %s" % " ".join(args_list[0:1] + args_list[-2:])
    cmd = [sys.executable, script] + args_list
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              encoding="utf-8", errors="replace")
    except OSError as e:
        return None, v("TOOL_ERROR", where, "diyc 子进程无法启动：%s" % e)
    if proc.returncode not in (0, 1):
        tail = " ".join((proc.stderr or proc.stdout or "").split())[-200:]
        return None, v("TOOL_ERROR", where,
                       "diyc 非预期退出码 %s（期望 0|1）：%s"
                       % (proc.returncode, tail or "无输出"))
    for line in reversed((proc.stdout or "").splitlines()):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except ValueError:
            continue
        if isinstance(payload, dict):
            return payload, None
    return None, v("TOOL_ERROR", where, "diyc 回执不可解析（--json 面单行 JSON 缺失）")


def delegation_ready(script, project_root):
    if not os.path.isfile(script):
        return False, v("TOOL_MISSING", display_path(script, project_root),
                        "diyc.py 缺席：跨文档核对降级，请从会话侧人工复核")
    return True, None


# ---------------------------------------------------------------- walkthrough

def load_final_doc(out_dir, filename):
    """读须定稿的产物 → (ok, data, violation_or_None)。ok = 在场 + 可解析 + status: final。"""
    path = os.path.join(out_dir, filename)
    data, err = load_yaml_safe(path)
    if data is None and err is None:
        return False, None, v("MISSING_FILE", filename, "%s 缺失" % filename)
    if err is not None:
        return False, None, v("UNPARSABLE_YAML", filename, "%s 解析失败：%s" % (filename, err))
    project = data.get("project") if isinstance(data, dict) else None
    status = project.get("status") if isinstance(project, dict) else None
    if status != "已定稿":
        return False, None, v("STATUS_MISMATCH", filename + " project.status",
                              "%s 未定稿（实为 %s）" % (filename,
                                                    status if nonempty(status) else "未声明"))
    return True, data, None


def _ac_ids(stories_doc):
    ids = []
    for story in items(stories_doc, "stories"):
        if not isinstance(story, dict):
            continue
        for ac in items(story, "acceptance_criteria"):
            if isinstance(ac, dict) and nonempty(ac.get("id")):
                ids.append(str(ac["id"]))
    return ids


def _tc_entries(test_plan_doc):
    out = []
    for tc in items(test_plan_doc, "test_cases"):
        if not isinstance(tc, dict) or not nonempty(tc.get("id")):
            continue
        out.append({"id": str(tc["id"]), "ac": tc.get("ac"),
                    "status": tc.get("status")})
    return out


def cmd_walkthrough(args):
    root = os.path.abspath(args.project_root)
    out = os.path.abspath(args.output_dir)
    warnings, gaps = [], {kind: [] for kind in GAP_KINDS}
    evaluated, skipped = set(), []

    stories_ok, stories_doc, stories_err = load_final_doc(out, STORIES_FILE)
    tp_ok, tp_doc, tp_err = load_final_doc(out, TEST_PLAN_FILE)
    for err in (stories_err, tp_err):
        if err is not None:
            warnings.append(err)

    script = diyc_script_path()
    ready, warn = delegation_ready(script, root)
    trace_payload = check_payload = None
    if ready:
        trace_payload, trace_warn = diyc_call(
            script, ["trace", "--project-root", root, "--json"])
        if trace_warn is not None:
            warnings.append(trace_warn)
        check_payload, check_warn = diyc_call(
            script, ["check", "--type", "test-plan", "--final",
                     "--project-root", root, "--json"])
        if check_warn is not None:
            warnings.append(check_warn)
        for payload in (trace_payload, check_payload):
            resolved = payload.get("output_dir") if isinstance(payload, dict) else None
            if nonempty(resolved):
                a = os.path.normcase(os.path.abspath(os.path.join(root, str(resolved))))
                if a != os.path.normcase(out):
                    warnings.append(v("SET_MISMATCH", str(resolved),
                                      "diyc 解析的产物目录与本引擎 --output-dir 不一致："
                                      "跨文档证据可能来自另一目录"))
    else:
        warnings.append(warn)

    # ① no_impl：AC 从未出现在 trace 引用的 AC ID 中（护栏：全量零 trace → 整类跳过）
    if stories_ok and trace_payload is not None:
        files_with_trace = (trace_payload.get("counts") or {}).get("files_with_trace", 0)
        if not files_with_trace:
            skipped.append("无实现")
            warnings.append(v("EMPTY_FIELD", "diyc trace",
                              "项目全量零 trace 标记（files_with_trace==0）：实现面不可判，"
                              "无实现类整体跳过"))
        else:
            referenced = set()
            for ref in trace_payload.get("references") or []:
                if isinstance(ref, dict):
                    for id_ in ref.get("ids") or []:
                        if AC_RE.fullmatch(str(id_)):
                            referenced.add(str(id_))
            for ac in _ac_ids(stories_doc):
                if ac not in referenced:
                    gaps["无实现"].append({
                        "kind": "无实现", "ref": ac, "route": "diy-dev",
                        "note": "AC 从未出现在 # trace: 引用的 AC ID 中（实现面无可判证据）"})
            evaluated.add("无实现")
            unresolved = trace_payload.get("unresolved") or []
            if unresolved:
                warnings.append(v("TRACE_UNRESOLVED", "diyc trace",
                                  "trace 引用了 %d 处不可解析 ID（不属四类缺口，须人工复核）"
                                  % len(unresolved)))
    else:
        skipped.append("无实现")

    # ② no_test：AC 无 TC 绑定，或绑定的 TC 全为 pending
    if stories_ok and tp_ok:
        tcs = _tc_entries(tp_doc)
        for ac in _ac_ids(stories_doc):
            bound = [tc for tc in tcs if str(tc["ac"]) == ac]
            if not bound:
                gaps["无测试"].append({
                    "kind": "无测试", "ref": ac, "route": "diy-test-design",
                    "note": "AC 无任何 TC 绑定"})
            elif all(str(tc["status"]) == "待办" for tc in bound):
                gaps["无测试"].append({
                    "kind": "无测试", "ref": ac, "route": "diy-test-author",
                    "note": "AC 的 TC 全部待办（有 TC 未落地）：%s"
                            % "、".join(tc["id"] for tc in bound)})
        evaluated.add("无测试")
    else:
        skipped.append("无测试")

    # ③ 孤儿用例：TC 的 ac 不可解析（委派 diyc check --type test-plan 的 ac-UNKNOWN_ID 转记）
    if tp_ok and stories_ok and check_payload is not None:
        others = 0
        for item in check_payload.get("violations") or []:
            if not isinstance(item, dict):
                continue
            where = str(item.get("where") or "")
            match = re.search(r"test_cases\[([^\]]+)\]\.ac(?:\[\d+\])?$", where)
            if item.get("code") == "UNKNOWN_ID" and match:
                gaps["孤儿用例"].append({
                    "kind": "孤儿用例", "ref": match.group(1), "route": "用户",
                    "note": "TC 的 ac 不可解析：%s（%s）"
                            % (item.get("msg"), display_path(
                                os.path.join(out, TEST_PLAN_FILE), root))})
            else:
                others += 1
        if others:
            warnings.append(v("ENUM_INVALID", "diyc check --type test-plan",
                              "另报 %d 条非 ac 违规（不属本技能走查面，未吞掉）" % others))
        evaluated.add("孤儿用例")
    else:
        skipped.append("孤儿用例")

    # ④ 从未运行：TC status: 待办
    if tp_ok:
        for tc in _tc_entries(tp_doc):
            if str(tc["status"]) == "待办":
                gaps["从未运行"].append({
                    "kind": "从未运行", "ref": tc["id"], "route": "diy-test-author",
                    "note": "TC 尚未激活/复跑（status: 待办）"})
        evaluated.add("从未运行")
    else:
        skipped.append("从未运行")

    if not evaluated:
        status = "已跳过"
    elif skipped:
        status = "部分覆盖"
    else:
        status = "全覆盖"
    if skipped:
        warnings.append(v("PENDING_DECISION", "walkthrough",
                          "跳过类：%s（就绪态 %s，原因见上方 warning）"
                          % ("、".join(skipped), status)))
    payload = {"ok": True, "command": "walkthrough", "project_root": args.project_root,
               "output_dir": os.path.normpath(out).replace("\\", "/"),
               "status": status, "gaps": gaps, "violations": [], "warnings": warnings,
               "counts": {kind: len(gaps[kind]) for kind in GAP_KINDS}}
    payload["counts"].update({"evaluated": len(evaluated), "skipped": len(skipped)})
    emit_via(payload, args.json, human_walkthrough)
    return 0


def human_walkthrough(payload):
    print("三向走查：%s（缺口 %s）"
          % (payload["status"],
             " ".join("%s=%d" % (k, val) for k, val in payload["counts"].items()
                      if k in GAP_KINDS)))
    for kind in GAP_KINDS:
        for gap in payload["gaps"][kind]:
            print("- %s %s → %s：%s" % (gap["kind"], gap["ref"], gap["route"], gap["note"]))
    for item in payload["warnings"]:
        print("警告 %s %s: %s" % (item["code"], item["where"], item["msg"]))
