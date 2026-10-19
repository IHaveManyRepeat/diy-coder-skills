# -*- coding: utf-8 -*-
"""diy-project-context check 命令域：scan/stack/structure/records/integration/rules 六检与总编排。."""

import json
import os

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import count_by, display_path, load_yaml_safe, nonempty, v, walk_strings  # noqa: E402

from context_lib import CTX_FILE, DATE_RE, PART_TYPES, PC_RE, RULE_CATEGORIES, SCAN_LEVELS, SCAN_MODES, safe_len, slash  # noqa: E402

# ---- check ----

def check_scan(scan, where, violations):
    if not isinstance(scan, dict):
        violations.append(v("EMPTY_FIELD", where, "scan 缺失或不是映射"))
        return
    mode = scan.get("mode")
    if not nonempty(mode):
        violations.append(v("EMPTY_FIELD", where + ".mode", "mode 缺失"))
    elif str(mode) not in SCAN_MODES:
        violations.append(v("ENUM_INVALID", where + ".mode",
                            "mode 越界：%s（合法集 %s）" % (mode, "|".join(SCAN_MODES))))
    level = scan.get("level")
    if not nonempty(level):
        violations.append(v("EMPTY_FIELD", where + ".level", "level 缺失"))
    elif str(level) not in SCAN_LEVELS:
        violations.append(v("ENUM_INVALID", where + ".level",
                            "level 越界：%s（合法集 %s）" % (level, "|".join(SCAN_LEVELS))))
    date = scan.get("date")
    if not nonempty(date):
        violations.append(v("EMPTY_FIELD", where + ".date", "date 缺失"))
    elif not DATE_RE.fullmatch(str(date)):
        violations.append(v("ENUM_INVALID", where + ".date", "date 须为 YYYY-MM-DD，实为 %s" % date))
    parts = scan.get("parts")
    if not isinstance(parts, list):
        violations.append(v("EMPTY_FIELD", where + ".parts", "parts 缺失或不是列表"))
        return
    if not parts:
        violations.append(v("EMPTY_FIELD", where + ".parts", "parts 不得为空（扫描是产物的前置证据）"))
    for i, part in enumerate(parts):
        pw = "%s.parts[%d]" % (where, i)
        if not isinstance(part, dict):
            violations.append(v("EMPTY_FIELD", pw, "part 不是映射"))
            continue
        for key in ("name", "type", "path"):
            if not nonempty(part.get(key)):
                violations.append(v("EMPTY_FIELD", pw + "." + key, "%s 缺失" % key))
        ptype = part.get("type")
        if nonempty(ptype) and str(ptype) not in PART_TYPES:
            violations.append(v("ENUM_INVALID", pw + ".type",
                                "type 越界：%s（合法集 %s）" % (ptype, "|".join(PART_TYPES))))

def check_stack(stack, where, violations):
    if stack is None:
        violations.append(v("EMPTY_FIELD", where, "stack 缺失（无内容写空列表）"))
        return
    if not isinstance(stack, list):
        violations.append(v("EMPTY_FIELD", where, "stack 不是列表"))
        return
    for i, entry in enumerate(stack):
        sw = "%s[%d]" % (where, i)
        if not isinstance(entry, dict):
            violations.append(v("EMPTY_FIELD", sw, "stack 条目不是映射"))
            continue
        if not nonempty(entry.get("part")):
            violations.append(v("EMPTY_FIELD", sw + ".part", "part 缺失（stack 须归属部件）"))
        for key in ("language", "framework", "version", "notes"):
            if key in entry and entry.get(key) is not None and not isinstance(entry.get(key), str):
                violations.append(v("ENUM_INVALID", sw + "." + key,
                                    "%s 若给出须为字符串（未知写空串）" % key))

def check_structure(structure, where, violations):
    if structure is None:
        violations.append(v("EMPTY_FIELD", where, "structure 缺失"))
        return
    if not isinstance(structure, dict):
        violations.append(v("EMPTY_FIELD", where, "structure 不是映射"))
        return
    tree = structure.get("tree")
    if tree is not None and not isinstance(tree, str):
        violations.append(v("ENUM_INVALID", where + ".tree", "tree 若给出须为字符串"))
    key_dirs = structure.get("key_dirs")
    if key_dirs is None:
        return
    if not isinstance(key_dirs, list):
        violations.append(v("EMPTY_FIELD", where + ".key_dirs", "key_dirs 不是列表"))
        return
    for i, entry in enumerate(key_dirs):
        kw = "%s.key_dirs[%d]" % (where, i)
        if not isinstance(entry, dict):
            violations.append(v("EMPTY_FIELD", kw, "key_dirs 条目不是映射"))
            continue
        for key in ("path", "purpose"):
            if not nonempty(entry.get(key)):
                violations.append(v("EMPTY_FIELD", kw + "." + key, "%s 缺失" % key))

def check_records(items, where, required_keys, violations):
    """通用集合段：每条须为映射且 required_keys 非空（architecture / deep_dives 共用）。"""
    if items is None:
        violations.append(v("EMPTY_FIELD", where, "段落缺失（无内容写空列表）"))
        return
    if not isinstance(items, list):
        violations.append(v("EMPTY_FIELD", where, "不是列表"))
        return
    for i, entry in enumerate(items):
        iw = "%s[%d]" % (where, i)
        if not isinstance(entry, dict):
            violations.append(v("EMPTY_FIELD", iw, "条目不是映射"))
            continue
        for key in required_keys:
            if not nonempty(entry.get(key)):
                violations.append(v("EMPTY_FIELD", iw + "." + key, "%s 缺失" % key))

def check_integration(integration, where, violations):
    if integration is None:
        return  # 多部件才填（源 step-8 条件步）：单部件项目缺席合法
    if not isinstance(integration, list):
        violations.append(v("EMPTY_FIELD", where, "integration 不是列表"))
        return
    for i, entry in enumerate(integration):
        iw = "%s[%d]" % (where, i)
        if not isinstance(entry, dict):
            violations.append(v("EMPTY_FIELD", iw, "条目不是映射"))
            continue
        between = entry.get("between")
        if not isinstance(between, list) or len(between) != 2 or \
                not all(nonempty(x) for x in between):
            violations.append(v("EMPTY_FIELD", iw + ".between",
                                "between 须为两个部件名的列表（如 [client, server]）"))
        for key in ("contract", "notes"):
            if key in entry and entry.get(key) is not None and not isinstance(entry.get(key), str):
                violations.append(v("ENUM_INVALID", iw + "." + key, "%s 若给出须为字符串" % key))

def check_rules(rules, where, final, violations):
    if rules is None:
        violations.append(v("EMPTY_FIELD", where, "rules 缺失（LLM 规则集合）"))
        return
    if not isinstance(rules, list):
        violations.append(v("EMPTY_FIELD", where, "rules 不是列表"))
        return
    seen = set()
    for i, rule in enumerate(rules):
        rw = "%s[%d]" % (where, i)
        if not isinstance(rule, dict):
            violations.append(v("EMPTY_FIELD", rw, "rule 不是映射"))
            continue
        rid = rule.get("id")
        if not nonempty(rid):
            violations.append(v("EMPTY_FIELD", rw + ".id", "id 缺失"))
        elif not PC_RE.fullmatch(str(rid)):
            violations.append(v("ENUM_INVALID", rw + ".id",
                                "id 须为 PC-0nn（三位零填充），实为 %s" % rid))
        else:
            if str(rid) in seen:
                violations.append(v("DUPLICATE_ID", rw + ".id",
                                    "规则 ID %s 重复（PC ID 稳定不重用）" % rid))
            seen.add(str(rid))
        category = rule.get("category")
        if not nonempty(category):
            violations.append(v("EMPTY_FIELD", rw + ".category", "category 缺失"))
        elif str(category) not in RULE_CATEGORIES:
            violations.append(v("ENUM_INVALID", rw + ".category",
                                "category 越界：%s（合法集 %s）"
                                % (category, "|".join(RULE_CATEGORIES))))
        if not nonempty(rule.get("rule")):
            violations.append(v("EMPTY_FIELD", rw + ".rule", "rule 缺失（规则正文）"))
        if final:
            for key in ("why", "where"):
                if not nonempty(rule.get(key)):
                    violations.append(v("EMPTY_FIELD", rw + "." + key,
                                        "--final 要求每条规则 %s 非空" % key))
    if final and not rules:
        violations.append(v("EMPTY_FIELD", where, "--final 要求至少 1 条规则"))

def previous_rules(path, project_root, warnings):
    """--previous：读旧稿 PC-### 集合；不可读 → 结构化 warning（比对无法进行，不静默）。"""
    data, err = load_yaml_safe(path)
    if data is None and err is None:
        warnings.append(v("MISSING_FILE", display_path(path, project_root),
                          "旧稿不存在，--previous 比对跳过"))
        return None
    if err is not None:
        warnings.append(v("UNPARSABLE_YAML", display_path(path, project_root),
                          "旧稿不可解析，--previous 比对跳过：%s" % err))
        return None
    rules = data.get("rules") if isinstance(data, dict) else None
    if not isinstance(rules, list):
        return set()
    return {str(r.get("id")) for r in rules
            if isinstance(r, dict) and PC_RE.fullmatch(str(r.get("id") or ""))}

def cmd_check(args):
    root = os.path.abspath(args.project_root)
    out = args.output_dir
    path = os.path.join(out, CTX_FILE)
    show = display_path(path, root)
    violations = []
    warnings = []
    rules = []

    data, err = load_yaml_safe(path)
    if data is None and err is None:
        violations.append(v("MISSING_FILE", show,
                            "%s 不存在（先跑一次 scan 与起草）" % CTX_FILE))
    elif err is not None:
        violations.append(v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err))
    elif not isinstance(data, dict):
        violations.append(v("EMPTY_FIELD", show, "顶层不是映射（须为 project + scan + …）"))
    else:
        project = data.get("project")
        if project is not None and not isinstance(project, dict):
            violations.append(v("EMPTY_FIELD", show + " project", "project 不是映射"))
        check_scan(data.get("scan"), show + " scan", violations)
        check_stack(data.get("stack"), show + " stack", violations)
        check_structure(data.get("structure"), show + " structure", violations)
        check_records(data.get("architecture"), show + " architecture",
                      ("part", "summary"), violations)
        check_integration(data.get("integration"), show + " integration", violations)
        rules = data.get("rules") if isinstance(data.get("rules"), list) else []
        check_rules(data.get("rules"), show + " rules", args.final, violations)
        if data.get("deep_dives") is not None:  # 事件驱动段：未跑过深挖时缺席合法
            check_records(data.get("deep_dives"), show + " deep_dives",
                          ("area", "date", "files_scanned"), violations)
        revisions = data.get("revisions")
        if revisions is not None and not isinstance(revisions, list):
            violations.append(v("EMPTY_FIELD", show + " revisions", "revisions 不是列表"))
        if args.final:
            if any("[假设]" in s for _p, s in walk_strings(data, "")):
                violations.append(v("ASSUMPTION_PRESENT", show,
                                    "--final 要求零 [假设]；未决假设须先落定"))
            if isinstance(data.get("stack"), list) and not data["stack"]:
                violations.append(v("EMPTY_FIELD", show + " stack", "--final 要求 stack 非空"))

    if args.previous:
        old_ids = previous_rules(args.previous, root, warnings)
        if old_ids is not None:
            new_ids = {str(r.get("id")) for r in rules
                       if isinstance(r, dict) and PC_RE.fullmatch(str(r.get("id") or ""))}
            for rid in sorted(old_ids - new_ids):
                violations.append(v("ID_UNSTABLE", show + " rules",
                                    "旧稿规则 %s 在新稿中丢失（PC ID 稳定不重用；"
                                    "确删请追加 revisions 留痕）" % rid))

    counts = {
        "parts": safe_len(data, "scan", "parts"),
        "stack": safe_len(data, "stack"),
        "rules": len(rules),
        "rules_by_category": count_by(rules, "category"),
        "architecture": safe_len(data, "architecture"),
        "integration": safe_len(data, "integration"),
        "deep_dives": safe_len(data, "deep_dives"),
    }
    ok = not violations
    payload = {
        "ok": ok,
        "command": "check",
        "project_root": args.project_root,
        "output_dir": os.path.normpath(out).replace("\\", "/"),
        "final": args.final,
        "previous": slash(args.previous) if args.previous else None,
        "violations": violations,
        "warnings": warnings,
        "counts": counts,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False))
    elif ok:
        print("PASS：%s 校验通过（rules=%d, parts=%d）" % (show, len(rules), counts["parts"]))
        for item in warnings:
            print("- WARN %s %s: %s" % (item["code"], item["where"], item["msg"]))
    else:
        print("FAIL：")
        for item in violations:
            print("- %s %s: %s" % (item["code"], item["where"], item["msg"]))
        print("共 %d 条违规；exit 0 是唯一放行" % len(violations))
    return 0 if ok else 1
