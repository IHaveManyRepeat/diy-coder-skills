# -*- coding: utf-8 -*-
"""diy-spec-scan 确定性引擎：扫描单元枚举（collect）+ spec-scan.yaml 歧义清单校验（check）。

机制：本技能扮演实现者预演「照着规格干活」，把规格里没写清、留人猜的地方记成歧义清单
（spec-scan.yaml）。引擎只做机械可判的两件事——

  collect  枚举扫描目标，产出扫描单元清单（覆盖清单：人/agent 靠它确认有没有漏扫）：
             目标为文件 → 该文件即唯一目标文件；
             目标为目录且含 SKILL.md → SKILL.md + steps/*.md（按文件名排序）；
             其余目录 → 该目录下 *.md（递归一层：本层 + 一层子目录，不再深挖）；
             都找不到 .md → MISSING_FILE，exit 1 零产出。
           每个目标文件给出：相对 project-root 的正斜杠路径、行数、切分建议——按 markdown
           二级标题 `## `（行首、井号后一个空格；`###` 不算）切出的单元名列表（标题文本去掉
           `## ` 前缀与首尾空白；无二级标题则整个文件算一个单元，单元名取文件名）。
           文件读了但无法按 UTF-8 解码 → SCAN_TRUNCATED warning（该文件仍列出、行数记 0、
           单元不切分），不阻断（exit 仍 0）。
           相对 --target 按 project-root 解析（对齐 investigation.py 先例）。

  check    校验 {output_dir}/spec-scan.yaml（本技能产出的歧义清单）。基础校验：YAML 可解析
           （异常转 UNPARSABLE_YAML，不让异常裸奔）；顶层 project{name,created,updated} +
           scans[] + revisions[] 缺项；scans[].id 形态 SS-0nn（三位数字）且全局唯一
           （DUPLICATE_ID / ENUM_INVALID）；scans[].target 在场且含 path；units[] 每项
           unit / path / scanned（布尔）；findings[] 每条 id 形态 SS-0nn-nn 且唯一、type 八值
           枚举（分支无定义 / 术语冲突 / 接口缺口 / 输入不明 /
           输出不明 / 时序不明 / 直接矛盾 / 隐含假设）、where 非空
           且形如 <path> 或 <path>:<行号>、quote / read_as / stuck / would_guess 四字段全非空
           （EMPTY_FIELD；would_guess = 若我是实现者我会猜成什么——没有它这条 finding 不成立）、
           severity ∈ 阻断|建议|观察；scans[].summary 的 total/blocker/major/minor 与
           findings 真值一致、units_total/units_scanned 与 units 数组一致（SET_MISMATCH）。
           --final 附加：全部 units[].scanned 为 true（未扫完 → SET_MISMATCH）、findings 的
           字符串字段零 [假设] 字面量（命中 → ASSUMPTION_PRESENT）——**`quote` 字段豁免**
           （2026-09-16 裁定）：该禁令管的是「扫描器自己未落定的推断」，而 quote 是**引文证据**，
           被扫规格本身可能就含该标记；对引文做字面量拦截会逼出全角改写，把「quote 逐字保留
           原文」这条本技能的立身纪律变成不可能。非 quote 字段若需提及该标记，写全角
           ［假设］（全角不是该禁令的字面量）。exit 0 唯一放行。

规则来源：违规码全部复用 batch3-contract §3 冻结集——本引擎用到 MISSING_FILE /
UNPARSABLE_YAML / DUPLICATE_ID / ENUM_INVALID / EMPTY_FIELD / ASSUMPTION_PRESENT /
SET_MISMATCH / SCAN_TRUNCATED 共 8 个，**无新增码**（UNKNOWN_ID 本技能无适用面，不产出）。
回执契约对齐 B1/B2 批既有先例：exit 0 唯一放行 / --json 单行 JSON（ensure_ascii=False）/
共同键 {ok, command, project_root, output_dir, violations[{code,where,msg}], warnings, counts}；
where 一律正斜杠、相对 project-root，无位置时为空字符串；人读态每条违规一行 `CODE where: msg`
+ 末尾汇总行；--output-dir 必填（argparse required，无默认值）。

分工裁定：本引擎不做实例解析、不做白名单、不推导目录（实例解析由 SKILL.md 委托 diyc.py
resolve，与本引擎无关）；只读——collect 只读目标文件，check 只读 spec-scan.yaml，两者都不写
任何文件（歧义清单由技能侧按引擎回执落盘）。
"""
import argparse
import io
import json
import os
import re
import sys

import yaml

SPEC_SCAN_FILE = "spec-scan.yaml"
SKILL_FILE = "SKILL.md"
STEPS_DIR = "steps"
MD_SUFFIX = ".md"
HEADING = "## "

SS_ID_RE = re.compile(r"SS-\d{3}\Z")
FINDING_ID_RE = re.compile(r"SS-\d{3}-\d{2}\Z")
LINE_RE = re.compile(r"[0-9]+\Z")

FINDING_TYPES = ("分支无定义", "术语冲突", "接口缺口", "输入不明",
                 "输出不明", "时序不明", "直接矛盾", "隐含假设")
FINDING_TEXT_FIELDS = ("quote", "read_as", "stuck", "would_guess")
SEVERITIES = ("阻断", "建议", "观察")
SUMMARY_KEYS = ("total", "blocker", "major", "minor", "units_total", "units_scanned")
PROJECT_KEYS = ("name", "created", "updated")
ASSUMPTION = "[假设]"


# trace: diy-spec-scan 违规项构造（统一 {code, where, msg} 形态）
def v(code, where, msg):
    return {"code": code, "where": where, "msg": msg}


# trace: diy-spec-scan 非空判定（None / 空白字符串均视为空）
def nonempty(value):
    return value is not None and str(value).strip() != ""


# trace: diy-spec-scan where 显示口径（正斜杠 + 相对 project-root；越界回退绝对路径）
def display_path(path, project_root):
    try:
        rel = os.path.relpath(path, project_root)
    except ValueError:
        rel = os.path.abspath(path)
    if rel.startswith(".."):
        return os.path.abspath(path).replace("\\", "/")
    return rel.replace("\\", "/")


# trace: diy-spec-scan 递归收集任意节点的字符串值（[假设] 扫描用，只看值不看键）
def collect_strings(node):
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for value in node.values():
            for s in collect_strings(value):
                yield s
    elif isinstance(node, list):
        for item in node:
            for s in collect_strings(item):
                yield s


# trace: diy-spec-scan YAML 安全装载：(data, err)；缺失 (None, None)、空文件 ({}, None)、损坏 (None, 原因)
def load_yaml_safe(path):
    if not os.path.isfile(path):
        return None, None
    try:
        with io.open(path, "r", encoding="utf-8") as handle:
            return (yaml.safe_load(handle) or {}), None
    except yaml.YAMLError as e:
        return None, str(e)
    except OSError as e:
        return None, str(e)


# trace: diy-spec-scan 回执输出（--json 单行 / 人读行）
def emit(payload, as_json, human_lines):
    if as_json:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        human_lines(payload)


# trace: diy-spec-scan 集合字段取列表（缺失/非列表 → []，缺项由 check 层单独报）
def items(doc, key):
    if not isinstance(doc, dict):
        return []
    value = doc.get(key)
    return value if isinstance(value, list) else []


# ---------------------------------------------------------------- collect：扫描单元枚举

# trace: diy-spec-scan 目录一层枚举（本层 *.md 先、一层子目录 *.md 后，各按文件名排序，不深挖）
def list_md_files(directory):
    files = [os.path.join(directory, name) for name in sorted(os.listdir(directory))
             if name.lower().endswith(MD_SUFFIX)
             and os.path.isfile(os.path.join(directory, name))]
    for name in sorted(os.listdir(directory)):
        sub = os.path.join(directory, name)
        if not os.path.isdir(sub):
            continue
        files += [os.path.join(sub, entry) for entry in sorted(os.listdir(sub))
                  if entry.lower().endswith(MD_SUFFIX)
                  and os.path.isfile(os.path.join(sub, entry))]
    return files


# trace: diy-spec-scan 目标枚举（文件 / 含 SKILL.md 的技能目录 / 普通目录），返回 (kind, path, files, violations)
def enumerate_target_files(target, project_root):
    path = target if os.path.isabs(target) else os.path.join(project_root, target)
    path = os.path.abspath(path)
    show = display_path(path, project_root)
    if os.path.isfile(path):
        return "file", show, [path], []
    if not os.path.isdir(path):
        # 目标不存在：kind 回退 file（target 块 schema 是 file|dir 闭集，拒绝路径不破形）
        return "file", show, [], [v("MISSING_FILE", show,
                                    "扫描目标不存在：--target 须指向文件或目录")]
    skill = os.path.join(path, SKILL_FILE)
    if os.path.isfile(skill):
        files = [skill]
        steps = os.path.join(path, STEPS_DIR)
        if os.path.isdir(steps):
            files += sorted(os.path.join(steps, name) for name in os.listdir(steps)
                            if name.lower().endswith(MD_SUFFIX)
                            and os.path.isfile(os.path.join(steps, name)))
        return "dir", show, files, []
    try:
        files = list_md_files(path)
    except OSError as e:
        sys.stderr.write("诊断：目录枚举失败 %s：%s\n" % (show, e))
        return "dir", show, [], [v("MISSING_FILE", show, "目录无法枚举：%s" % e)]
    if not files:
        return "dir", show, [], [v("MISSING_FILE", show,
                                   "目录下未找到任何 .md（须含 SKILL.md 或至少一个 *.md）："
                                   "扫描面为空，拒绝放行")]
    return "dir", show, files, []


# trace: diy-spec-scan 单元切分建议（行首 `## ` 标题文本；无二级标题 → 整文件一单元，单元名取文件名）
def split_units(text, fallback_name):
    units = []
    for line in text.splitlines():
        if line.startswith(HEADING):
            title = line[len(HEADING):].strip()
            units.append(title if title else fallback_name)
    return units if units else [fallback_name]


# trace: diy-spec-scan 单目标文件读取与切分（非 UTF-8 → SCAN_TRUNCATED warning，行数记 0、单元不切）
def read_target_file(path, project_root):
    rel = display_path(path, project_root)
    try:
        with io.open(path, "rb") as handle:
            raw = handle.read()
    except OSError as e:
        sys.stderr.write("诊断：目标文件读取失败 %s：%s\n" % (rel, e))
        return None, [v("MISSING_FILE", rel, "文件无法读取：%s" % e)], []
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        return ({"path": rel, "lines": 0, "units": []}, [],
                [v("SCAN_TRUNCATED", rel,
                   "无法按 UTF-8 解码（%s）：行数记 0、单元未切分——该文件须人工目检"
                   % e.reason)])
    return ({"path": rel, "lines": len(text.splitlines()),
             "units": split_units(text, os.path.basename(path))}, [], [])


# trace: diy-spec-scan collect 子命令（枚举目标 → 扫描单元清单；只读，exit 0 唯一放行）
def cmd_collect(args):
    root = os.path.abspath(args.project_root)
    out = os.path.abspath(args.output_dir)
    payload = {
        "ok": False,
        "command": "collect",
        "project_root": args.project_root,
        "output_dir": os.path.normpath(out).replace("\\", "/"),
        "violations": [],
        "warnings": [],
        "counts": {"files": 0, "lines": 0, "units": 0},
        "target": {"kind": None, "path": str(args.target).replace("\\", "/"),
                   "files": [], "total_lines": 0},
    }
    kind, show, files, violations = enumerate_target_files(args.target, root)
    target = {"kind": kind, "path": show, "files": [], "total_lines": 0}
    entries = []
    warnings = []
    for path in files:
        entry, errs, warns = read_target_file(path, root)
        violations += errs
        warnings += warns
        if entry is not None:
            entries.append(entry)
    target["files"] = entries
    target["total_lines"] = sum(entry["lines"] for entry in entries)
    counts = {"files": len(entries), "lines": target["total_lines"],
              "units": sum(len(entry["units"]) for entry in entries)}
    payload["violations"] = violations
    payload["warnings"] = warnings
    payload["counts"] = counts
    payload["target"] = target
    payload["ok"] = not violations
    emit(payload, args.json, human_collect)
    return 0 if payload["ok"] else 1


# trace: diy-spec-scan collect 人读态（目标 / 文件行 / 警告 / 末尾汇总行）
def human_collect(payload):
    target = payload["target"]
    if payload["violations"]:
        print("拒绝：目标 %s %s" % (target["kind"] or "未知", target["path"]))
    else:
        print("目标：%s %s" % (target["kind"], target["path"]))
        for entry in target["files"]:
            print("- %s（%d 行 · %d 单元）"
                  % (entry["path"], entry["lines"], len(entry["units"])))
    for item in payload["violations"]:
        print("%s %s: %s" % (item["code"], item["where"], item["msg"]))
    for item in payload["warnings"]:
        print("警告 %s %s: %s" % (item["code"], item["where"], item["msg"]))
    counts = payload["counts"]
    print("汇总：文件 %d · 行 %d · 单元 %d · 违规 %d 条 · 警告 %d 条（exit %d）"
          % (counts["files"], counts["lines"], counts["units"],
             len(payload["violations"]), len(payload["warnings"]), 0 if payload["ok"] else 1))


# ---------------------------------------------------------------- check：spec-scan.yaml 校验

# trace: diy-spec-scan 顶层结构校验（project 三键 + scans + revisions）
def check_top_level(data, show):
    violations = []
    project = data.get("project")
    if not isinstance(project, dict):
        violations.append(v("EMPTY_FIELD", show + " project",
                            "project 缺失或不是映射（须含 name/created/updated）"))
    else:
        for key in PROJECT_KEYS:
            if not nonempty(project.get(key)):
                violations.append(v("EMPTY_FIELD", "%s project.%s" % (show, key),
                                    "project.%s 缺失" % key))
    for key in ("scans", "revisions"):
        if key not in data:
            violations.append(v("EMPTY_FIELD", "%s %s" % (show, key),
                                "%s 缺失（无内容写空列表）" % key))
        elif not isinstance(data.get(key), list):
            violations.append(v("EMPTY_FIELD", "%s %s" % (show, key),
                                "%s 不是列表" % key))
    return violations


# trace: diy-spec-scan scans[].id 形态（SS-0nn）与全局唯一校验
def check_scan_id(sid, where, seen):
    if not nonempty(sid):
        return [v("EMPTY_FIELD", where, "id 缺失（须为 SS-0nn）")]
    text = str(sid)
    if not SS_ID_RE.fullmatch(text):
        return [v("ENUM_INVALID", where, "id 须为 SS-0nn（三位零填充），实为 %s" % text)]
    if text in seen:
        return [v("DUPLICATE_ID", where, "scan ID %s 重复（ID 稳定不重用）" % text)]
    seen.add(text)
    return []


# trace: diy-spec-scan scans[].target 校验（在场且含 path）
def check_scan_target(scan, where):
    target = scan.get("target")
    if not isinstance(target, dict):
        return [v("EMPTY_FIELD", where + ".target", "target 缺失或不是映射（须含 path）")]
    if not nonempty(target.get("path")):
        return [v("EMPTY_FIELD", where + ".target.path",
                  "target.path 缺失（被扫目标相对 project-root 的路径）")]
    return []


# trace: diy-spec-scan units[] 三件套校验（unit / path / scanned 布尔）
def check_units(where, units):
    violations = []
    for i, unit in enumerate(units):
        uw = "%s.units[%d]" % (where, i)
        if not isinstance(unit, dict):
            violations.append(v("EMPTY_FIELD", uw, "unit 不是映射（须含 unit/path/scanned）"))
            continue
        if not nonempty(unit.get("unit")):
            violations.append(v("EMPTY_FIELD", uw + ".unit",
                                "单元名缺失（`## ` 标题文本或文件名）"))
        if not nonempty(unit.get("path")):
            violations.append(v("EMPTY_FIELD", uw + ".path", "单元所在文件路径缺失"))
        scanned = unit.get("scanned")
        if not isinstance(scanned, bool):
            violations.append(v("EMPTY_FIELD", uw + ".scanned",
                                "scanned 须为布尔（true/false），实为 %s"
                                % (scanned if nonempty(scanned) else "未声明")))
    return violations


# trace: diy-spec-scan findings[] 定位标签（msg 里指明是哪条 finding）
def finding_label(index, finding):
    fid = finding.get("id")
    if nonempty(fid):
        return "findings[%d]（%s）" % (index, fid)
    return "findings[%d]" % index


# trace: diy-spec-scan findings[].id 形态（SS-0nn-nn）与唯一校验
def check_finding_id(fid, where, index, seen):
    if not nonempty(fid):
        return [v("EMPTY_FIELD", where, "findings[%d] 的 id 缺失（须为 SS-0nn-nn）" % index)]
    text = str(fid)
    if not FINDING_ID_RE.fullmatch(text):
        return [v("ENUM_INVALID", where,
                  "findings[%d] 的 id 须为 SS-0nn-nn，实为 %s" % (index, text))]
    if text in seen:
        return [v("DUPLICATE_ID", where, "finding ID %s 重复（ID 稳定不重用）" % text)]
    seen.add(text)
    return []


# trace: diy-spec-scan findings[].where 形态（<path> 或 <path>:<行号>：无空白、行号纯数字）
def is_where(value):
    text = str(value)
    if not text or re.search(r"\s", text):
        return False
    head, sep, tail = text.rpartition(":")
    if not sep:
        return True
    return bool(head) and bool(LINE_RE.fullmatch(tail))


# trace: diy-spec-scan findings[] 五要素校验（id / type 八值 / where 形态 / 四字段非空 / severity 三值）
def check_findings(where, findings, seen):
    violations = []
    for i, finding in enumerate(findings):
        fw = "%s.findings[%d]" % (where, i)
        if not isinstance(finding, dict):
            violations.append(v("EMPTY_FIELD", fw,
                                "finding 不是映射（id/type/where/quote/read_as/stuck/"
                                "would_guess/severity 八件套）"))
            continue
        violations += check_finding_id(finding.get("id"), fw + ".id", i, seen)
        label = finding_label(i, finding)
        ftype = finding.get("type")
        if not nonempty(ftype):
            violations.append(v("EMPTY_FIELD", fw + ".type", "%s 的 type 缺失" % label))
        elif str(ftype) not in FINDING_TYPES:
            violations.append(v("ENUM_INVALID", fw + ".type",
                                "%s 的 type 越界：%s（合法集 %s）"
                                % (label, ftype, "|".join(FINDING_TYPES))))
        spot = finding.get("where")
        if not nonempty(spot):
            violations.append(v("EMPTY_FIELD", fw + ".where",
                                "%s 的 where 缺失（歧义在规格里的位置）" % label))
        elif not is_where(spot):
            violations.append(v("ENUM_INVALID", fw + ".where",
                                "%s 的 where 须形如 <path> 或 <path>:<行号>，实为 %s"
                                % (label, spot)))
        for field in FINDING_TEXT_FIELDS:
            if not nonempty(finding.get(field)):
                violations.append(v("EMPTY_FIELD", "%s.%s" % (fw, field),
                                    "%s 的 %s 为空（quote/read_as/stuck/would_guess 缺一不可；"
                                    "would_guess = 若我是实现者我会猜成什么）" % (label, field)))
        severity = finding.get("severity")
        if not nonempty(severity):
            violations.append(v("EMPTY_FIELD", fw + ".severity", "%s 的 severity 缺失" % label))
        elif str(severity) not in SEVERITIES:
            violations.append(v("ENUM_INVALID", fw + ".severity",
                                "%s 的 severity 越界：%s（合法集 %s）"
                                % (label, severity, "|".join(SEVERITIES))))
    return violations


# trace: diy-spec-scan summary 真值计算（findings 计数 + units 计数）
def real_summary(units, findings):
    severity = {name: 0 for name in SEVERITIES}
    for finding in findings:
        if isinstance(finding, dict) and str(finding.get("severity")) in severity:
            severity[str(finding["severity"])] += 1
    return {
        "total": len(findings),
        "blocker": severity["阻断"],
        "major": severity["建议"],
        "minor": severity["观察"],
        "units_total": len(units),
        "units_scanned": sum(1 for unit in units
                             if isinstance(unit, dict) and unit.get("scanned") is True),
    }


# trace: diy-spec-scan 计数值比对（布尔不得充当整数：true 不等于 1）
def count_matches(value, real):
    return isinstance(value, int) and not isinstance(value, bool) and value == real


# trace: diy-spec-scan summary 计数与真值一致性校验（不符 → SET_MISMATCH）
def check_summary(scan, where, units, findings):
    sw = where + ".summary"
    summary = scan.get("summary")
    if not isinstance(summary, dict):
        return [v("EMPTY_FIELD", sw,
                  "summary 缺失或不是映射（total/blocker/major/minor/units_total/"
                  "units_scanned）")]
    real = real_summary(units, findings)
    violations = []
    for key in SUMMARY_KEYS:
        if key not in summary:
            violations.append(v("EMPTY_FIELD", "%s.%s" % (sw, key), "summary.%s 缺失" % key))
        elif not count_matches(summary.get(key), real[key]):
            violations.append(v("SET_MISMATCH", "%s.%s" % (sw, key),
                                "summary.%s=%s 与实际计数 %d 不符"
                                % (key, summary.get(key), real[key])))
    return violations


# trace: diy-spec-scan --final 附加义务（全单元已扫 + findings 零 [假设]，quote 豁免）
def check_final_duties(where, units, findings):
    violations = []
    for i, unit in enumerate(units):
        if isinstance(unit, dict) and unit.get("scanned") is not True:
            name = unit.get("path") or unit.get("unit") or "第 %d 个单元" % (i + 1)
            violations.append(v("SET_MISMATCH", "%s.units[%d].scanned" % (where, i),
                                "--final 要求全部单元 scanned: true；%s 尚未扫"
                                "（漏扫单元会漏掉歧义）" % name))
    for i, finding in enumerate(findings):
        # quote 豁免（2026-09-16 裁定）：引文是证据、不是未落定推断，而被扫规格本身可能
        # 就含该标记——拦引文会逼出全角改写，让「逐字引原文」变成不可能。
        scanned = ({k: val for k, val in finding.items() if k != "quote"}
                   if isinstance(finding, dict) else finding)
        if any(ASSUMPTION in s for s in collect_strings(scanned)):
            violations.append(v("ASSUMPTION_PRESENT", "%s.findings[%d]" % (where, i),
                                "--final 要求零 [假设]（quote 引文豁免）；"
                                "未决推断须先落定再交"))
    return violations


# trace: diy-spec-scan 单条 scan 全量校验（id/target/units/findings/summary + --final 义务）
def check_scan(index, scan, show, final, seen_scan_ids, seen_finding_ids):
    where = "%s.scans[%d]" % (show, index)
    if not isinstance(scan, dict):
        return [v("EMPTY_FIELD", where, "scan 不是映射")]
    violations = check_scan_id(scan.get("id"), where + ".id", seen_scan_ids)
    violations += check_scan_target(scan, where)
    units = scan.get("units")
    if not isinstance(units, list):
        violations.append(v("EMPTY_FIELD", where + ".units", "units 缺失或不是列表"))
        units = []
    else:
        violations += check_units(where, units)
    findings = scan.get("findings")
    if not isinstance(findings, list):
        violations.append(v("EMPTY_FIELD", where + ".findings",
                            "findings 缺失或不是列表（无歧义写空列表）"))
        findings = []
    else:
        violations += check_findings(where, findings, seen_finding_ids)
    violations += check_summary(scan, where, units, findings)
    if final:
        violations += check_final_duties(where, units, findings)
    return violations


# trace: diy-spec-scan check 回执计数（scan / 单元 / finding + 分档分型）
def scan_counts(scans):
    units = findings = scanned = 0
    by_severity = {}
    by_type = {}
    for scan in scans:
        if not isinstance(scan, dict):
            continue
        scan_units = scan.get("units")
        if isinstance(scan_units, list):
            units += len(scan_units)
            scanned += sum(1 for unit in scan_units
                           if isinstance(unit, dict) and unit.get("scanned") is True)
        scan_findings = scan.get("findings")
        if not isinstance(scan_findings, list):
            continue
        findings += len(scan_findings)
        for finding in scan_findings:
            if not isinstance(finding, dict):
                continue
            severity = finding.get("severity")
            if nonempty(severity):
                by_severity[str(severity)] = by_severity.get(str(severity), 0) + 1
            ftype = finding.get("type")
            if nonempty(ftype):
                by_type[str(ftype)] = by_type.get(str(ftype), 0) + 1
    return {"scans": len(scans), "units": units, "units_scanned": scanned,
            "findings": findings, "by_severity": by_severity, "by_type": by_type}


# trace: diy-spec-scan check 子命令（spec-scan.yaml 校验；exit 0 唯一放行）
def cmd_check(args):
    root = os.path.abspath(args.project_root)
    out = os.path.abspath(args.output_dir)
    path = os.path.join(out, SPEC_SCAN_FILE)
    show = display_path(path, root)
    violations = []
    scans = []
    data, err = load_yaml_safe(path)
    if data is None and err is None:
        violations.append(v("MISSING_FILE", show,
                            "%s 不存在（先跑一次规格预演扫描产出歧义清单）" % SPEC_SCAN_FILE))
    elif err is not None:
        violations.append(v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err))
    elif not isinstance(data, dict):
        violations.append(v("EMPTY_FIELD", show,
                            "顶层不是映射（须为 project + scans + revisions）"))
    else:
        violations += check_top_level(data, show)
        raw = data.get("scans")
        scans = raw if isinstance(raw, list) else []
        seen_scan_ids = set()
        seen_finding_ids = set()
        for i, scan in enumerate(scans):
            violations += check_scan(i, scan, show, args.final, seen_scan_ids, seen_finding_ids)
    counts = scan_counts(scans)
    payload = {
        "ok": not violations,
        "command": "check",
        "project_root": args.project_root,
        "output_dir": os.path.normpath(out).replace("\\", "/"),
        "final": args.final,
        "violations": violations,
        "warnings": [],
        "counts": counts,
    }
    emit(payload, args.json, human_check)
    return 0 if payload["ok"] else 1


# trace: diy-spec-scan check 人读态（每条违规一行 `CODE where: msg` + 末尾汇总行）
def human_check(payload):
    counts = payload["counts"]
    if payload["ok"]:
        print("PASS：%s 校验通过（scan %d · 单元 %d · finding %d）"
              % (payload["output_dir"] + "/" + SPEC_SCAN_FILE,
                 counts["scans"], counts["units"], counts["findings"]))
    else:
        for item in payload["violations"]:
            print("%s %s: %s" % (item["code"], item["where"], item["msg"]))
    print("汇总：违规 %d 条 · 警告 %d 条（exit %d）"
          % (len(payload["violations"]), len(payload["warnings"]), 0 if payload["ok"] else 1))


# trace: diy-spec-scan 命令行面（--output-dir 必填；引擎不做实例解析/目录推导）
def build_parser():
    ap = argparse.ArgumentParser(
        description="diy-spec-scan 确定性引擎：扫描单元枚举（collect）+ "
                    "spec-scan.yaml 歧义清单校验（check）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("collect", help="枚举扫描目标 → 扫描单元清单（覆盖清单；只读）")
    c.add_argument("--target", required=True,
                   help="扫描目标（文件或目录；相对路径按 project-root 解析）")
    c.add_argument("--project-root", default=".", help="项目根（默认 .）")
    c.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    c.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    c.set_defaults(func=cmd_collect)

    k = sub.add_parser("check", help="校验 spec-scan.yaml（schema/枚举/字段完整/计数一致；"
                                     "--final 附加全单元已扫与零假设）")
    k.add_argument("--project-root", default=".", help="项目根（默认 .）")
    k.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    k.add_argument("--final", action="store_true",
                   help="定稿校验：全部单元 scanned: true + findings 任意字段零 [假设]")
    k.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    k.set_defaults(func=cmd_check)
    return ap


# trace: diy-spec-scan 入口（stdout/stderr 固定 UTF-8；退出码由子命令返回）
def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = build_parser().parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
