# -*- coding: utf-8 -*-
"""diy-test-author 规则执行层：行级/命名/确定性/块级/夹具审计 + load_plan + audit 子命令。"""
import io
import json
import os
import sys


sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import display_path, load_yaml_safe, nonempty, v  # noqa: E402

from author_audit import (  # noqa: E402
    ASSERT_PAT, CLEANUP_PAT, CREATION_PAT, EMPTY_NAME_RE, FIXTURE_USE_PAT, GENERIC,
    GENERIC_ONLY_LINE_RULES, GWT_MARKERS, GWT_RE, HARDCODED_MSG, HARDCODED_PATTERNS,
    LINE_RULES, MAX_ASSERTIONS_PER_TEST, MAX_FILE_LINES, NONDETERMINISTIC_PAT,
    PLACEHOLDER_PAT, PLAN_FINAL, PRIORITY_TAG_RE, PRIORITY_TAGS, SCOPE_STATUS,
    SKIP_PAT, TAG_LOOKAHEAD, TAG_LOOKBACK, UNDESCRIPTIVE_NAME_RE, anchor_for,
    anchors_in_line, any_match, count_matches, family_of, strip_comments,
    strip_line_comments, test_blocks, try_bodies,
)
from author_detect import FIXTURE_DIR_CANDIDATES, FIXTURE_FILE_MARKERS  # noqa: E402

PLAN_FILE = "test-plan.yaml"

# ---------------------------------------------------------------- audit：规则执行

def audit_lines(lines, family, show, violations):
    """行级共用规则（去注释后判定，含 helper 等 test 体外代码）；每条违规记 `文件:行号`。"""
    rules = LINE_RULES + (GENERIC_ONLY_LINE_RULES if family == GENERIC else ())
    for no, raw in enumerate(lines, start=1):
        code_line = strip_comments(raw, family)
        if not code_line.strip():
            continue
        where = "%s:%d" % (show, no)
        for code, msg, table in rules:
            if any_match(table.get(family, table[GENERIC]), code_line):
                violations.append(v(code, where, "%s（第 %d 行）" % (msg, no)))


def audit_name(block, lines, known, where, violations):
    """用例名面：优先级标签（须跟随锚定 TC 的 priority）+ 名字可读性。"""
    name = block.get("name") or ""
    start = block["start"]
    region = "\n".join(lines[max(0, start - TAG_LOOKBACK):start + TAG_LOOKAHEAD])
    tags = PRIORITY_TAG_RE.findall(region)
    if not tags:
        violations.append(v("PRIORITY_TAG_MISSING", where,
                            "用例名缺优先级标签（[P0]-[P3]）——标签跟随锚定 TC 的 priority"))
    else:
        tc_id = anchor_for(lines, block["start"])
        case = known.get(tc_id) if tc_id else None
        want = str((case or {}).get("priority") or "").strip().upper()
        if want in PRIORITY_TAGS and want not in tags:
            violations.append(v("PRIORITY_TAG_MISMATCH", where,
                                "用例名标签 %s 与 %s 的 priority=%s 不一致——标签必须跟随 TC"
                                % ("/".join("[%s]" % t for t in tags), tc_id, want)))
    bare = PRIORITY_TAG_RE.sub("", name).strip()
    if UNDESCRIPTIVE_NAME_RE.match(bare) or EMPTY_NAME_RE.match(bare):
        violations.append(v("NAME_UNDESCRIPTIVE", where,
                            "用例名 %r 说不出测什么（test1 / example 一类占位名）"
                            "——名字须写明被测行为与期望" % name))


def audit_determinism(block, family, where, violations):
    """确定性隔离判在用例体内：随机 / 时钟源 + try-catch 包测试逻辑。"""
    body = strip_line_comments(block["body"], family)
    if any_match(NONDETERMINISTIC_PAT.get(family, NONDETERMINISTIC_PAT[GENERIC]), body):
        violations.append(v("NONDETERMINISTIC_SOURCE", where,
                            "用例体用了随机 / 时钟源——数据交给工厂（固定种子）、时钟注入，"
                            "同输入须同结果（源「tests are deterministic」）"))
    for chunk in try_bodies(block["body"], family):
        if any_match(CLEANUP_PAT, strip_line_comments(chunk, family)):
            continue
        violations.append(v("TRY_CATCH_TEST_LOGIC", where,
                            "try-catch 包住了测试逻辑（源「only for cleanup」）"
                            "——失败就让它失败；只有清理动作可包 try"))


def audit_blocks(lines, blocks, family, show, violations, known):
    """块级规则：断言面 + 红相形态（skip + TC 锚）+ 用例名 / GWT / 确定性隔离。"""
    for block in blocks:
        body = strip_line_comments(block["body"], family)
        where = "%s:%d" % (show, block["start"] + 1)

        if any_match(PLACEHOLDER_PAT.get(family, PLACEHOLDER_PAT[GENERIC]), body):
            violations.append(v("PLACEHOLDER_ASSERTION", where,
                                "占位断言（expect(true) / assert True 一类）——断言须指向期望行为"))
        if any_match(HARDCODED_PATTERNS, body):
            violations.append(v("HARDCODED_DATA", where, HARDCODED_MSG))
        assertions = count_matches(ASSERT_PAT.get(family, ASSERT_PAT[GENERIC]), body)
        if assertions == 0:
            violations.append(v("MISSING_ASSERTION", where,
                                "用例无断言——测试必须断言期望行为"))
        elif assertions > MAX_ASSERTIONS_PER_TEST:
            violations.append(v("NOT_ATOMIC", where,
                                "单用例 %d 条断言（上限 %d）——拆成原子用例"
                                % (assertions, MAX_ASSERTIONS_PER_TEST)))

        skipped = count_matches(SKIP_PAT.get(family, SKIP_PAT[GENERIC]), body)
        if skipped == 0:
            violations.append(v("SKIP_MISSING", where,
                                "红相脚手架缺 skip——产物必须全部 skip（否则会污染 CI）"))

        if anchor_for(lines, block["start"]) is None:
            violations.append(v("ANCHOR_MISSING", where,
                                "用例缺 TC 锚（上方一行 `TC: TC-x.y.z`）——新生成文件无遗留豁免"))

        audit_name(block, lines, known, where, violations)
        audit_determinism(block, family, where, violations)

        markers = {m.group(1).lower() for m in GWT_RE.finditer(block["body"])}
        missing = [m.upper() for m in GWT_MARKERS if m not in markers]
        if missing:
            violations.append(v("GWT_MISSING", where,
                                "用例缺 Given-When-Then 结构注释（缺 %s）——源硬纪律："
                                "用例以 GWT 组织，一屏看懂前置 / 动作 / 期望"
                                % " / ".join(missing)))


def is_fixture_file(show):
    """夹具/工厂文件的路径判据（复用探测面的常量，不另立一套词表）。"""
    parts = show.replace("\\", "/").split("/")
    name = parts[-1].lower()
    if any(seg in FIXTURE_DIR_CANDIDATES for seg in parts[:-1]):
        return True
    if name == "conftest.py":
        return True
    return any(m in name for m in FIXTURE_FILE_MARKERS)


def audit_fixture(text, family, show, violations):
    """夹具文件级：建了数据的夹具必须自带 teardown 清理（源「auto-cleanup (delete created data)」）。

    三条件齐备才判：有 setup/teardown 相位（`await use(` / `yield`）＋ 有建数据动作 ＋
    无任何清理动作。纯生成器工厂（无 use/yield 相位）不受牵连——造数据是它的本职。
    """
    body = strip_line_comments(text, family)
    if not any_match(FIXTURE_USE_PAT, body):
        return
    if not any_match(CREATION_PAT, body) or any_match(CLEANUP_PAT, body):
        return
    violations.append(v("FIXTURE_NO_TEARDOWN", show,
                        "夹具建了数据却没有 teardown 清理（源硬纪律：自动清理自建数据）"
                        "——`await use(data)` / `yield` 之后补删除"))


def audit_file(path, show, violations, known):
    """单文件审计 → 文件内的 TC 锚集合（去重，保序）。"""
    try:
        with io.open(path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
    except OSError as e:
        violations.append(v("MISSING_FILE", show, "文件不可读：%s" % e))
        return [], 0

    lines = text.splitlines()
    family = family_of(path)
    if len(lines) > MAX_FILE_LINES:
        violations.append(v("FILE_TOO_LONG", show,
                            "文件 %d 行超上限 %d——拆文件（源 max_file_lines 禁则）"
                            % (len(lines), MAX_FILE_LINES)))

    anchors = []
    for raw in lines:
        for tc in anchors_in_line(raw):
            if tc not in anchors:
                anchors.append(tc)

    audit_lines(lines, family, show, violations)
    if is_fixture_file(show):
        audit_fixture(text, family, show, violations)
    blocks = test_blocks(text, family)
    audit_blocks(lines, blocks, family, show, violations, known)
    return anchors, len(blocks)


def load_plan(out, root, violations):
    """上游门禁：test-plan.yaml 在场 + final + test_cases 可解析 → {tc_id: entry}。"""
    path = os.path.join(out, PLAN_FILE)
    show = display_path(path, root)
    plan, err = load_yaml_safe(path)
    if plan is None and err is None:
        violations.append(v("MISSING_FILE", show,
                            "%s 不存在（TC 由 diy-test-design 写——先跑它）" % PLAN_FILE))
        return {}
    if err is not None:
        violations.append(v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err))
        return {}
    if not isinstance(plan, dict):
        violations.append(v("EMPTY_FIELD", show, "顶层不是映射（须含 project + test_cases）"))
        return {}
    project = plan.get("project")
    status = project.get("status") if isinstance(project, dict) else None
    if str(status) != PLAN_FINAL:
        violations.append(v("STATUS_MISMATCH", show + " project.status",
                            "上游不是已定稿（当前 %s）——先跑 diy-test-design 定稿"
                            % (status or "缺")))
    cases = plan.get("test_cases")
    if not isinstance(cases, list):
        violations.append(v("EMPTY_FIELD", show + " test_cases",
                            "test_cases 缺失或不是列表（TC 是本源唯一输入）"))
        return {}
    return {str(c["id"]): c for c in cases
            if isinstance(c, dict) and nonempty(c.get("id"))}


def check_scoped_tcs(tc_ids, known, out, root, violations):
    """锚定 TC 现场自检：存在 / technique / kill_target 非空 / status 必须是 pending。"""
    show = display_path(os.path.join(out, PLAN_FILE), root)
    for tc_id in tc_ids:
        case = known.get(tc_id)
        where = "%s test_cases[%s]" % (show, tc_id)
        if case is None:
            violations.append(v("UNKNOWN_ID", where,
                                "%s 在 %s 中不存在——锚必须指向既有 TC" % (tc_id, PLAN_FILE)))
            continue
        for field in ("technique", "kill_target"):
            if not nonempty(case.get(field)):
                violations.append(v("EMPTY_FIELD", "%s.%s" % (where, field),
                                    "%s 缺失或为空（TC 须带 %s）" % (field, field)))
        status = case.get("status")
        if str(status) != SCOPE_STATUS:
            violations.append(v("STATUS_MISMATCH", "%s.status" % where,
                                "%s 的 status=%s 不是 %s——红相脚手架只覆盖未激活的 TC"
                                "（失败是已激活测试、通过已收口）；范围内无可做 TC 时"
                                "不静默空跑" % (tc_id, status or "缺", SCOPE_STATUS)))


def cmd_audit(args):
    root = os.path.abspath(args.project_root)
    out = os.path.abspath(args.output_dir)
    violations = []
    warnings = []

    raw_files = list(args.files or [])
    if not raw_files:
        violations.append(v("EMPTY_FIELD", "--files",
                            "文件集为空——只审本次产出/触碰的文件，无「全测试目录」缺省"))
    resolved = []
    seen = set()
    for raw in raw_files:
        if not nonempty(raw):
            violations.append(v("EMPTY_FIELD", "--files", "空的文件项——去掉空串或补上本次文件"))
            continue
        path = raw if os.path.isabs(raw) else os.path.join(root, raw)
        show = display_path(path, root)
        if show in seen:
            continue
        seen.add(show)
        if not os.path.isfile(path):
            violations.append(v("MISSING_FILE", show,
                                "文件不存在（--files 只带本次会话产出/触碰的文件集）"))
            continue
        resolved.append((path, show))

    known = load_plan(out, root, violations)

    tc_ids = []
    test_count = 0
    for path, show in resolved:
        anchors, blocks = audit_file(path, show, violations, known)
        test_count += blocks
        for tc_id in anchors:
            if tc_id not in tc_ids:
                tc_ids.append(tc_id)

    if known:
        check_scoped_tcs(tc_ids, known, out, root, violations)

    ok = not violations
    payload = {
        "ok": ok,
        "command": "audit",
        "project_root": args.project_root,
        "output_dir": os.path.normpath(out).replace("\\", "/"),
        "files": [show for _path, show in resolved],
        "tcs": tc_ids,
        "violations": violations,
        "warnings": warnings,
        "counts": {"files": len(resolved), "tests": test_count, "tcs": len(tc_ids),
                   "violations": len(violations), "warnings": len(warnings)},
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        if ok:
            print("PASS：审计通过（文件 %d / 用例 %d / TC %d）"
                  % (len(resolved), test_count, len(tc_ids)))
        else:
            print("FAIL：审计不通过，零写入")
            for item in violations:
                print("- %s %s: %s" % (item["code"], item["where"], item["msg"]))
        for item in warnings:
            print("- %s %s: %s" % (item["code"], item["where"], item["msg"]))
    return 0 if ok else 1
