# -*- coding: utf-8 -*-
"""diy-test-framework check 面：CI 注入扫描 + 三方对齐 + check_record 编排。"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import load_yaml_safe, nonempty, v, walk_strings  # noqa: E402

from test_framework_lib import (  # noqa: E402
    ACTIONS, BLOCK_SCALAR_RE, CHECK_RESULTS, CI_PLATFORMS, CODE_KEY_RE,
    COMMENT_LINE_PREFIXES, DATE_RE, DA_RE, FILE_KINDS, JENKINS_SH_RE, MODES, SETUP_RE,
    STACK_TYPES, STAGE_NAMES, TEST_PLAN_FILE, UNSAFE_EXPR_RE, UNSAFE_HARNESS_RE,
    command_in_text, path_form_error,
)

# ---------------------------------------------------------------- check

def load_static_checks(output_dir):
    """读 test-plan.yaml 的 static_checks → (entries, skip_reason)。
    三类分支（文件缺席 / 字段缺席 / 列表为空）统一返回 (None, 原因)：跳过对齐判定 + warning。"""
    path = os.path.join(output_dir, TEST_PLAN_FILE)
    data, err = load_yaml_safe(path)
    if data is None and err is None:
        return None, "test-plan.yaml 缺席 → 跳过 CI 三方对齐判定（static_checks 不可得）"
    if err is not None:
        return None, "test-plan.yaml 不可解析 → 跳过 CI 三方对齐判定：%s" % err
    checks = data.get("static_checks") if isinstance(data, dict) else None
    if not isinstance(checks, list) or not checks:
        return None, "test-plan.yaml 的 static_checks 缺席或为空 → 跳过 CI 三方对齐判定"
    entries = []
    for i, item in enumerate(checks):
        if not isinstance(item, dict):
            continue
        entries.append({"order": item.get("order"), "tool": item.get("tool"),
                        "gate": item.get("gate"), "index": i})
    if not entries:
        return None, "test-plan.yaml 的 static_checks 无可解析条目 → 跳过 CI 三方对齐判定"
    return entries, None


def embedded_code_lines(text):
    """粗粒度提取「被 shell 执行的脚本块」行 → [(行号, 行文本)]。
    覆盖：YAML 的 `run:` / `script:` / `command:`（内联值与 `|` / `>` 块标量、列表项）
    与 Jenkins 的 `sh '''…'''`；注释行一律不参与（不执行，模板里的反例都在注释里）。"""
    found = []
    lines = text.splitlines()
    block_indent = None            # YAML 块标量/列表体：进入时的键缩进
    jenkins_quote = None           # Jenkins sh 引号态
    for index, raw in enumerate(lines, start=1):
        stripped = raw.strip()
        if stripped.startswith(COMMENT_LINE_PREFIXES):
            continue
        if jenkins_quote is not None:
            end = raw.find(jenkins_quote)
            if end < 0:
                found.append((index, raw))
                continue
            found.append((index, raw[:end]))
            jenkins_quote = None
            continue
        if block_indent is not None:
            indent = len(raw) - len(raw.lstrip())
            if stripped and indent <= block_indent:
                block_indent = None
            else:
                found.append((index, raw))
                continue
        match = JENKINS_SH_RE.search(raw)
        if match:
            quote = match.group("quote")
            rest = match.group("rest")
            if len(quote) == 3 and quote not in rest:
                jenkins_quote = quote
            elif len(quote) == 1 and quote in rest:
                found.append((index, raw[:match.start("rest") + rest.find(quote)]))
            else:
                found.append((index, rest))
            continue
        match = CODE_KEY_RE.match(raw)
        if not match:
            continue
        rest = match.group("rest").strip()
        if rest and not BLOCK_SCALAR_RE.match(rest):
            found.append((index, raw))
        else:
            block_indent = len(match.group("indent"))
    return found


def scan_ci_injection(text):
    """生成物脚本块内的不安全插值扫描（F-12，源 ci/steps-v/step-01 §2a）→ [(行号, 片段)]。"""
    hits = []
    for lineno, line in embedded_code_lines(text):
        for pattern in (UNSAFE_EXPR_RE, UNSAFE_HARNESS_RE):
            for match in pattern.finditer(line):
                hits.append((lineno, match.group(0)))
    return hits


def check_ci_injection(text, rel_file, violations):
    """脚本块注入扫描的违规落点（只要有 CI 文件就扫，与 mode 无关：手改面同样裸奔）。"""
    for lineno, fragment in scan_ci_injection(text):
        violations.append(v("UNSAFE_INJECTION", "%s:%d" % (rel_file, lineno),
                            "脚本块内直接插值不可信上下文 %r —— 须经 env: / variables: / "
                            "envVariables 中转后以双引号 \"$ENV_VAR\" 引用（inputs 只能是 DATA、"
                            "不能是 COMMAND）" % fragment))


def check_ci_alignment(project_root, output_dir, record, where, violations, warnings):
    """CI 三方对齐（重扫不采信台账）：现场从 test-plan.yaml + CI 文件重算，与台账比对。
    同时执行脚本块注入扫描（F-12）：文件在场即扫，不受 mode / 对齐分支影响。"""
    mode = record.get("mode")
    ci = record.get("ci")
    if not isinstance(ci, dict):
        return
    platform = ci.get("platform")
    rel_file = ci.get("file")
    text = None
    if nonempty(rel_file) and path_form_error(rel_file) is None:
        ci_path = os.path.join(project_root, *str(rel_file).split("/"))
        if os.path.isfile(ci_path):
            try:
                with io.open(ci_path, "r", encoding="utf-8", newline="") as fh:
                    text = fh.read()
            except (OSError, UnicodeDecodeError) as e:
                violations.append(v("MISSING_FILE", str(rel_file), "CI 文件不可读：%s" % e))
                return
    if text is not None:
        check_ci_injection(text, str(rel_file), violations)
    if mode == "框架":
        return
    if platform == "none":
        warnings.append(v("EMPTY_FIELD", where + ".ci.platform",
                          "platform=none → 跳过 CI 三方对齐判定（无流水线文件）"))
        return
    if text is None:
        return

    entries, skip = load_static_checks(output_dir)
    if entries is None:
        warnings.append(v("EMPTY_FIELD", where + ".ci.static_check_alignment", skip))
    else:
        orders = {}
        for entry in entries:
            if isinstance(entry["order"], int):
                orders[entry["order"]] = entry
        ledger = ci.get("static_check_alignment")
        ledger_map = {}
        if isinstance(ledger, list):
            for i, item in enumerate(ledger):
                item_where = "%s.ci.static_check_alignment[%d]" % (where, i)
                shape_ok = (isinstance(item, dict)
                            and isinstance(item.get("order"), int)
                            and isinstance(item.get("in_ci"), bool))
                if not shape_ok:
                    violations.append(v("ENUM_INVALID", item_where,
                                        "条目须为 {order: <int>, in_ci: <bool>}"))
                    continue
                ledger_map[item["order"]] = item["in_ci"]
                if item["order"] not in orders:
                    violations.append(v("UNKNOWN_ID", item_where + ".order",
                                        "order %s 不在 test-plan.yaml 的 static_checks 中" % item["order"]))
        for entry in entries:
            order, gate = entry["order"], entry["gate"]
            if not isinstance(order, int) or not nonempty(entry["tool"]):
                continue
            in_ci = command_in_text(entry["tool"], text)
            if gate == "阻断" and order not in ledger_map:
                violations.append(v("CI_MISALIGNED", "%s.ci.static_check_alignment" % where,
                                    "漏 阻断 条目 order=%s（tool: %s）——阻断 层必录"
                                    % (order, entry["tool"])))
            if order in ledger_map and ledger_map[order] != in_ci:
                violations.append(v("CI_MISALIGNED", "%s.ci.static_check_alignment" % where,
                                    "order=%s（tool: %s）台账 in_ci=%s，现场重算=%s"
                                    "（重扫不采信台账）"
                                    % (order, entry["tool"], ledger_map[order], in_ci)))
    gates = ci.get("gates")
    if isinstance(gates, dict):
        for key in ("p0", "p1"):
            value = gates.get(key)
            if nonempty(value) and str(value) not in text:
                violations.append(v("CI_MISALIGNED", "%s.ci.gates.%s" % (where, key),
                                    "CI 文件缺阈值字面量 %r（事实源 = 台账 ci.gates，经 plan "
                                    "substitutions 注入）" % value))


def check_record(project_root, output_dir, index, record, final, show, warnings):
    violations = []
    where = "%s.setups[%d]" % (show, index)
    if not isinstance(record, dict):
        return [v("EMPTY_FIELD", where, "记录不是映射")]

    rid = record.get("id")
    if not nonempty(rid):
        violations.append(v("EMPTY_FIELD", where + ".id", "id 缺失"))
    elif not SETUP_RE.fullmatch(str(rid)):
        violations.append(v("ENUM_INVALID", where + ".id", "id 须为 TF-###（三位零填充），实为 %s" % rid))
    date = record.get("date")
    if not nonempty(date) or not DATE_RE.fullmatch(str(date)):
        violations.append(v("EMPTY_FIELD", where + ".date", "date 须为 YYYY-MM-DD"))
    status = record.get("status")
    if status not in ("草稿", "已定稿"):
        violations.append(v("ENUM_INVALID", where + ".status", "status 越界：%s（合法集 草稿|已定稿）" % status))
    mode = record.get("mode")
    if mode not in MODES:
        violations.append(v("ENUM_INVALID", where + ".mode", "mode 越界：%s（合法集 %s）"
                            % (mode, "|".join(MODES))))

    stack = record.get("stack")
    stack_type = None
    if not isinstance(stack, dict):
        violations.append(v("EMPTY_FIELD", where + ".stack", "stack 缺失或不是映射"))
    else:
        stack_type = stack.get("type")
        if stack_type not in STACK_TYPES:
            violations.append(v("ENUM_INVALID", where + ".stack.type",
                                "stack.type 越界：%s（合法集 %s）" % (stack_type, "|".join(STACK_TYPES))))
        for key in ("language", "package_manager"):
            if not nonempty(stack.get(key)):
                violations.append(v("EMPTY_FIELD", where + ".stack." + key, "%s 为空" % key))

    framework = record.get("framework")
    if framework is not None and not isinstance(framework, dict):
        violations.append(v("EMPTY_FIELD", where + ".framework", "framework 不是映射"))
    elif isinstance(framework, dict):
        for key in ("name", "runner", "reason"):
            if not nonempty(framework.get(key)):
                violations.append(v("EMPTY_FIELD", "%s.framework.%s" % (where, key),
                                    "framework.%s 为空（选型理由源 02 步保留）" % key))
    elif final:
        violations.append(v("EMPTY_FIELD", where + ".framework", "--final 要求 framework 非空"))

    if stack_type in ("移动端", "全栈"):
        unit = record.get("unit_layer")
        if not isinstance(unit, dict) or not nonempty(unit.get("name")):
            violations.append(v("EMPTY_FIELD", where + ".unit_layer",
                                "stack.type=%s 时 unit_layer.name 必填" % stack_type))

    files = record.get("files")
    if not isinstance(files, list) or not files:
        violations.append(v("EMPTY_FIELD", where + ".files", "files 须为非空列表"))
    else:
        for i, item in enumerate(files):
            item_where = "%s.files[%d]" % (where, i)
            if not isinstance(item, dict):
                violations.append(v("EMPTY_FIELD", item_where, "条目须为映射"))
                continue
            rel = item.get("path")
            err = path_form_error(rel)
            if err is not None:
                violations.append(v("ENUM_INVALID", item_where + ".path",
                                    "path %r 形态非法：%s（对齐 path: 口径）" % (rel, err)))
                continue
            if item.get("kind") not in FILE_KINDS:
                violations.append(v("ENUM_INVALID", item_where + ".kind",
                                    "kind 越界：%s" % item.get("kind")))
            if item.get("action") not in ACTIONS:
                violations.append(v("ENUM_INVALID", item_where + ".action",
                                    "action 越界：%s（合法集 新建|更新）" % item.get("action")))
            if not os.path.isfile(os.path.join(project_root, *str(rel).split("/"))):
                violations.append(v("MISSING_FILE", rel,
                                    "台账声明的生成文件不在场（action=%s）" % item.get("action")))

    checks = record.get("checks")
    failed = 0
    if not isinstance(checks, list):
        violations.append(v("EMPTY_FIELD", where + ".checks", "checks 缺失（无命令写空列表）"))
    else:
        for i, item in enumerate(checks):
            item_where = "%s.checks[%d]" % (where, i)
            if not isinstance(item, dict):
                violations.append(v("EMPTY_FIELD", item_where, "条目须为映射"))
                continue
            if not nonempty(item.get("command")):
                violations.append(v("EMPTY_FIELD", item_where + ".command", "command 为空"))
            result = item.get("result")
            if result not in CHECK_RESULTS:
                violations.append(v("ENUM_INVALID", item_where + ".result",
                                    "result 越界：%s（合法集 通过|失败）" % result))
            if result == "失败":
                failed += 1
                if not nonempty(item.get("note")):
                    violations.append(v("EMPTY_FIELD", item_where + ".note",
                                        "result=失败 时 note 必填（失败不得静默）"))
        if failed:
            warnings.append(v("EMPTY_FIELD", where + ".checks",
                              "checks 中 result: 失败 共 %d 条（环境面/人工处置项，已记 note）："
                              "--final 只记 warning、不拒绝；产物面失败须修后重跑，"
                              "修不了即停下报用户" % failed))

    ci = record.get("ci")
    if ci is not None and not isinstance(ci, dict):
        violations.append(v("EMPTY_FIELD", where + ".ci", "ci 不是映射"))
    elif isinstance(ci, dict):
        platform = ci.get("platform")
        if platform not in CI_PLATFORMS + ("none",):
            violations.append(v("ENUM_INVALID", where + ".ci.platform",
                                "platform 越界：%s（合法集 %s|none）"
                                % (platform, "|".join(CI_PLATFORMS))))
        rel_file = ci.get("file")
        if platform == "none":
            if nonempty(rel_file):
                violations.append(v("ENUM_INVALID", where + ".ci.file",
                                    "platform=none 时省略 file（schema 明文）"))
        elif platform in CI_PLATFORMS:
            if not nonempty(rel_file):
                violations.append(v("MISSING_FILE", where + ".ci.file",
                                    "platform=%s 时 ci.file 必填" % platform))
            else:
                err = path_form_error(rel_file)
                if err is not None:
                    violations.append(v("ENUM_INVALID", where + ".ci.file",
                                        "ci.file %r 形态非法：%s" % (rel_file, err)))
                elif not os.path.isfile(os.path.join(project_root, *str(rel_file).split("/"))):
                    violations.append(v("MISSING_FILE", str(rel_file), "CI 流水线文件不在场"))
        stages = ci.get("stages")
        if not isinstance(stages, list) or not all(nonempty(s) for s in stages):
            violations.append(v("EMPTY_FIELD", where + ".ci.stages",
                                "stages 须为非空字符串列表（%s）" % "|".join(STAGE_NAMES)))
        else:
            unknown = [s for s in stages if str(s) not in STAGE_NAMES]
            if unknown:
                warnings.append(v("ENUM_INVALID", where + ".ci.stages",
                                  "非标准阶段名（源五阶段之外的扩展）：%s" % " ".join(map(str, unknown))))
        gates = ci.get("gates")
        if not isinstance(gates, dict):
            violations.append(v("EMPTY_FIELD", where + ".ci.gates", "gates 须为 {p0, p1}"))
        else:
            for key in ("p0", "p1"):
                if not nonempty(gates.get(key)):
                    violations.append(v("EMPTY_FIELD", "%s.ci.gates.%s" % (where, key), "%s 为空" % key))
                elif final and str(gates.get(key)) != "100%":
                    violations.append(v("ENUM_INVALID", "%s.ci.gates.%s" % (where, key),
                                        "diy 口径拉满为 100%%（2026-09-15 用户裁定；源 P1≥95%% 已作废），实为 %s"
                                        % gates.get(key)))
        alignment = ci.get("static_check_alignment")
        if alignment is not None and not isinstance(alignment, list):
            violations.append(v("EMPTY_FIELD", where + ".ci.static_check_alignment",
                                "static_check_alignment 须为列表"))
        check_ci_alignment(project_root, output_dir, record, where, violations, warnings)

    deferred = record.get("deferred")
    if not isinstance(deferred, list):
        violations.append(v("EMPTY_FIELD", where + ".deferred",
                            "deferred 须为列表（无入队写空列表）"))
    else:
        for i, item in enumerate(deferred):
            if not nonempty(item) or not DA_RE.fullmatch(str(item)):
                violations.append(v("ENUM_INVALID", "%s.deferred[%d]" % (where, i),
                                    "deferred 条目须为 DA-###（ID 引用 deferred-actions.yaml）"))
    open_questions = record.get("open_questions")
    if not isinstance(open_questions, list):
        violations.append(v("EMPTY_FIELD", where + ".open_questions", "open_questions 须为列表"))

    if final:
        if any("[假设]" in s for _p, s in walk_strings(record, "")):
            violations.append(v("ASSUMPTION_PRESENT", where, "--final 要求零 [假设]"))
        if mode in ("CI", "两者"):
            if not isinstance(ci, dict):
                violations.append(v("EMPTY_FIELD", where + ".ci", "mode=%s 时 ci 段必填" % mode))
            else:
                if ci.get("platform") not in CI_PLATFORMS:
                    violations.append(v("ENUM_INVALID", where + ".ci.platform",
                                        "mode=%s 时 platform 须为五平台之一（none 不成立）" % mode))
                if not isinstance(ci.get("static_check_alignment"), list):
                    violations.append(v("EMPTY_FIELD", where + ".ci.static_check_alignment",
                                        "mode=%s 时 static_check_alignment 必填（可为空列表）" % mode))
    return violations
