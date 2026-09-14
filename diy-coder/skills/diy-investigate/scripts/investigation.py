# -*- coding: utf-8 -*-
"""diy-investigate 确定性引擎：证据现场采集（collect）+ investigation.yaml 校验（check）。

collect（只读，绝不写文件、绝不下结论）：
  1 VCS 情报（源 Outcome 2 证据类目 + Outcome 4 git log 首扫）：git 可用且根目录在仓库内时取
    `git log` 近期提交（--since 限范围）与涉及文件；git 缺席/非仓库/命令失败 → NO_VCS warning
    降级（结构情报不受影响，不崩）。
  2 目标区域（--area）文件清单：文件直取 / 目录递归取文本类扩展名，逐文件计行数——行数是
    「>10K tokens 须委派子代理返 JSON」的成本依据；清单即源纪律「错误串 grep 候选面」（grep
    由会话执行，引擎不做结论）。
  3 结构候选面：同名族并行实现（源 Outcome 4 glob the affected directory for parallel
    implementations）+ 测试文件（test_<stem> / <stem>_test / <stem>.test / <stem>.spec 约定）。
  回执 {ok, vcs, files, candidates, warnings, counts}；超扫描上限 → SCAN_TRUNCATED warning。

check（IV-### 集合，形状对齐 bug-log.yaml）：schema / 枚举（record status / mode / grade /
availability / hypothesis status / confidence / backlog status / input kind）/ IV+EV+H ID 格式
与记录内唯一 / evidence 三态齐全（grade + availability）/ hypotheses 生命周期完整性（status
非 open ⇒ resolution 非空——「假设永不删除，只更新状态 + 追加 Resolution」的机械化）/
stronghold 在场（evidence_light=false 时；源纪律「据点先行」）/ evidence_light=true ⇒
missing_evidence 非空（源纪律「缺失证据也是发现」）/ follow_ups 与 side_findings 追加块
（note 必填；side_findings 承接源 Side Findings——切向观察，非当前线程，与 evidence/backlog
语义区分；字段可选）。--final 附加：project.status final、conclusion 文本 + confidence、
handoff_brief 非空、timeline 非空、零 [ASSUMPTION]。exit 0 唯一放行。

分工裁定（任务书 §2.2/§7）：investigation 属新产物类型，不进 diyc.py check 硬编码类型集；
契约同构（exit 0 唯一放行 / --json 单行回执 / violations[{code, where, msg}] + counts；where
正斜杠、相对 project-root；--output-dir 必填、不做实例解析）。--previous 不实现（案件追加式，
resume 同 slug 原位更新，ID 集合只增不减）。无跨文档机械核对面（anytime 入口，不引用上游产物
ID），不委派 diyc；实例解析仍委托 `diyc.py resolve`（SKILL.md 激活句）。违规码复用
batch3-contract §3 冻结集，不新增；新增 warning 码 NO_VCS / SCAN_TRUNCATED。产物与 IV-/EV-/H-
ID 由会话（LLM）创作，本引擎只校验格式与唯一性。
"""
# trace: 迁移计划 §二 验收 #3（门禁形态：anytime 入口无上游门禁，拒绝路径=MISSING_FILE）
# trace: 迁移计划 §二 验收 #12（diyc 接线 a 实例委托 / b 终门 / c 记账不实现 / e 写权边界）
import argparse
import io
import json
import os
import re
import shutil
import subprocess
import sys

import yaml

INVESTIGATION_FILE = "investigation.yaml"

DOC_STATUSES = ("draft", "final")
RECORD_STATUSES = ("active", "concluded", "blocked-on-evidence")
MODES = ("symptom", "exploration")
GRADES = ("confirmed", "deduced", "hypothesized")
AVAILABILITIES = ("available", "partial", "missing")
HYPOTHESIS_STATUSES = ("open", "confirmed", "refuted")
CONFIDENCES = ("high", "medium", "low")
BACKLOG_STATUSES = ("open", "done", "unobtainable")
INPUT_KINDS = ("ticket", "archive", "log", "description", "area", "commit")

IV_RE = re.compile(r"IV-\d{3}")
EV_RE = re.compile(r"EV-\d{3}")
H_RE = re.compile(r"H-\d{3}")
SLUG_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")

# 结构情报扫描面：文本类扩展名（源码 + 配置 + 日志/文档）——「错误串 grep 候选面」
SOURCE_EXTS = ("py", "pyi", "ts", "tsx", "js", "jsx", "mjs", "cjs", "go", "rs", "java",
               "kt", "kts", "cs", "c", "cc", "cpp", "cxx", "h", "hpp", "rb", "php",
               "swift", "m", "mm", "sh", "bash", "ps1", "sql", "yaml", "yml", "json",
               "toml", "ini", "cfg", "conf", "md", "txt", "log")
SCAN_EXCLUDE_DIRS = (".git", ".claude", ".analysis", "node_modules", "__pycache__",
                     ".venv", "venv", "dist", "build", ".idea", ".vscode")
MAX_SCAN_FILES = 5000
MAX_LIST_FILES = 200
MAX_CANDIDATES = 100
MAX_COMMITS = 20

# 并发/测试边界外的语义（collect 只给候选面，判定权在会话）

def v(code, where, msg):
    return {"code": code, "where": where, "msg": msg}


def nonempty(value):
    return value is not None and str(value).strip() != ""


def items(doc, key):
    """取顶层列表键；缺失/非列表 → []。"""
    if not isinstance(doc, dict):
        return []
    value = doc.get(key)
    return value if isinstance(value, list) else []


def load_yaml_safe(path):
    """读 YAML：(data, err)。文件缺失 → (None, None)；空文件 → ({}, None)；损坏 → (None, 原因)。"""
    if not os.path.isfile(path):
        return None, None
    try:
        with io.open(path, "r", encoding="utf-8") as f:
            return (yaml.safe_load(f) or {}), None
    except yaml.YAMLError as e:
        return None, str(e)
    except OSError as e:
        return None, str(e)


def display_path(path, project_root):
    """where 显示口径（对齐 diyc）：正斜杠 + 相对 project-root；越界则绝对路径。"""
    try:
        rel = os.path.relpath(path, project_root)
    except ValueError:
        rel = os.path.abspath(path)
    if rel.startswith(".."):
        return os.path.abspath(path).replace("\\", "/")
    return rel.replace("\\", "/")


def collect_strings(node):
    """递归收集映射/列表内的全部字符串（键与值）——[ASSUMPTION] 扫描用。"""
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for key, value in node.items():
            yield str(key)
            for s in collect_strings(value):
                yield s
    elif isinstance(node, list):
        for item in node:
            for s in collect_strings(item):
                yield s


def iter_entries(records, key):
    """遍历各记录该列表键的映射条目（跳过非映射；计数助手共用）。"""
    for record in records:
        if isinstance(record, dict) and isinstance(record.get(key), list):
            for entry in record[key]:
                if isinstance(entry, dict):
                    yield entry


def count_by(entries, key):
    counts = {}
    for entry in entries:
        if isinstance(entry, dict) and nonempty(entry.get(key)):
            value = str(entry[key])
            counts[value] = counts.get(value, 0) + 1
    return counts


def count_items(records, key):
    return sum(len(record[key]) for record in records
               if isinstance(record, dict) and isinstance(record.get(key), list))


def count_open_hypotheses(records):
    return len([h for h in iter_entries(records, "hypotheses") if h.get("status") == "open"])


def count_by_grade(records):
    return count_by(iter_entries(records, "evidence"), "grade")


# ---------------------------------------------------------------- VCS 情报

def git_run(root, args):
    """跑一条 git 命令；git 缺席 / 无法启动 → None（调用方降级，不崩）。"""
    if shutil.which("git") is None:
        return None
    try:
        return subprocess.run(["git", "-C", root] + list(args), capture_output=True,
                              text=True, encoding="utf-8", errors="replace")
    except OSError:
        return None


def parse_git_log(text):
    """解析 `git log --pretty=format:%h<US>%ad<US>%s --date=short --name-only` 输出。"""
    commits = []
    current = None
    for line in (text or "").splitlines():
        if "\x1f" in line:
            parts = (line.split("\x1f") + ["", ""])[:3]
            current = {"commit": parts[0].strip(), "date": parts[1].strip() or None,
                       "subject": parts[2].strip(), "files": []}
            commits.append(current)
        elif line.strip() and current is not None:
            current["files"].append(line.strip().replace("\\", "/"))
    return commits


def probe_vcs(root, since, project_root):
    """VCS 情报（源 Outcome 2「version control」/ Outcome 4 git log 首扫）。
    返回 (vcs 块, warnings)。不可用/失败一律 NO_VCS warning 降级。"""
    where = display_path(root, project_root) or "."
    vcs = {"available": False, "head": None, "commits": [], "since": since}
    warnings = []
    if shutil.which("git") is None:
        warnings.append(v("NO_VCS", where, "git 不可用：VCS 情报降级（结构情报不受影响）"))
        return vcs, warnings
    inside = git_run(root, ["rev-parse", "--is-inside-work-tree"])
    if inside is None or inside.returncode != 0 or inside.stdout.strip() != "true":
        warnings.append(v("NO_VCS", where,
                          "项目根不在 git 仓库内：VCS 情报降级（结构情报不受影响）"))
        return vcs, warnings
    head = git_run(root, ["rev-parse", "--short", "HEAD"])
    log_args = ["log", "--pretty=format:%h\x1f%ad\x1f%s", "--date=short",
                "--name-only", "-n", str(MAX_COMMITS)]
    if nonempty(since):
        log_args += ["--since", str(since)]
    log = git_run(root, log_args)
    if log is None or log.returncode != 0:
        tail = " ".join(((log.stderr if log else "") or "").split())[-200:]
        warnings.append(v("NO_VCS", where,
                          "git log 失败：VCS 情报降级（%s）" % (tail or "无输出")))
        return vcs, warnings
    vcs = {"available": True,
           "head": head.stdout.strip() if head is not None and head.returncode == 0 else None,
           "commits": parse_git_log(log.stdout),
           "since": since}
    if not vcs["commits"]:
        warnings.append(v("NO_VCS", where, "git log 无提交（空仓库或 --since 范围内无提交）"))
    return vcs, warnings


# ---------------------------------------------------------------- 结构情报

def scan_source_files(root, out_dir):
    """遍历项目根收集文本类源文件（限定扩展集；排除输出目录与依赖/缓存目录）。"""
    out_key = os.path.normcase(os.path.abspath(out_dir))
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames
                       if d not in SCAN_EXCLUDE_DIRS
                       and os.path.normcase(os.path.abspath(os.path.join(dirpath, d))) != out_key]
        found += [os.path.join(dirpath, name) for name in sorted(filenames)
                  if os.path.splitext(name)[1].lower().lstrip(".") in SOURCE_EXTS]
        if len(found) > MAX_SCAN_FILES:
            return found, True
    return found, False


def count_lines(path):
    """二进制分块计行数（读失败 → None，不崩）。"""
    try:
        total = 0
        with io.open(path, "rb") as f:
            while True:
                chunk = f.read(65536)
                if not chunk:
                    break
                total += chunk.count(b"\n")
        return total
    except OSError:
        return None


def is_under(path, parent):
    try:
        return os.path.commonpath([os.path.abspath(path), os.path.abspath(parent)]) \
            == os.path.abspath(parent)
    except ValueError:
        return False


def is_test_basename(base, stem):
    """测试文件命名约定：test_<stem> / <stem>_test / <stem>.test / <stem>.spec。"""
    lowered = base.lower()
    return (lowered.startswith("test_" + stem) or lowered.startswith(stem + "_test")
            or lowered.startswith(stem + ".test") or lowered.startswith(stem + ".spec"))


def area_targets(root, area, project_root):
    """--area 目标解析：返回 (目标文件绝对路径列表 | None, 是否目录, warnings)。"""
    path = area if os.path.isabs(area) else os.path.join(root, area)
    if not os.path.exists(path):
        return None, False, [v("MISSING_FILE", display_path(path, project_root),
                               "目标区域不存在：结构情报降级（--area 拼写或路径核对后重试）")]
    return path, os.path.isdir(path), []


def build_candidates(targets, all_files, root, project_root):
    """候选面：同名族并行实现（source Outcome 4）+ 测试文件（命名约定）。只列不判。"""
    by_name = {}
    for path in all_files:
        by_name.setdefault(os.path.basename(path), []).append(path)
    candidates = []
    seen = set()
    target_keys = {os.path.normcase(os.path.abspath(t)) for t in targets}
    for target in targets:
        rel_target = display_path(target, project_root)
        stem = os.path.splitext(os.path.basename(target))[0].lower()
        pairs = [("parallel", other, "同名族（与 %s 同名不同路径）" % rel_target)
                 for other in by_name.get(os.path.basename(target), [])]
        pairs += [("test", other, "%s 的测试候选（按命名约定）" % rel_target)
                  for other in all_files
                  if is_test_basename(os.path.basename(other), stem)]
        for kind, other, note in sorted(pairs):
            key = (kind, os.path.normcase(other))
            if key in seen or os.path.normcase(other) in target_keys:
                continue
            seen.add(key)
            candidates.append({"file": display_path(other, project_root),
                               "kind": kind, "note": note})
    candidates.sort(key=lambda c: (c["kind"], c["file"]))
    return candidates


def collect_structure(root, out_dir, area, project_root):
    """结构情报：区域文件清单 + 同名族/测试候选面。返回 (files, candidates, warnings)。"""
    if not nonempty(area):
        return [], [], []
    target, is_dir, warnings = area_targets(root, area, project_root)
    if target is None:
        return [], [], warnings
    where = display_path(target, project_root)
    all_files, truncated = scan_source_files(root, out_dir)
    if truncated:
        warnings.append(v("SCAN_TRUNCATED", display_path(root, project_root),
                          "文件扫描达上限 %d：候选面不完整（缩小 --area 范围重试）"
                          % MAX_SCAN_FILES))
    targets = [f for f in all_files if is_under(f, target)] if is_dir else [target]
    if len(targets) > MAX_LIST_FILES:
        warnings.append(v("SCAN_TRUNCATED", where, "区域文件 %d 个超清单上限 %d：仅列前 %d 个"
                          % (len(targets), MAX_LIST_FILES, MAX_LIST_FILES)))
    files = [{"path": display_path(f, project_root), "lines": count_lines(f)}
             for f in sorted(targets)[:MAX_LIST_FILES]]
    candidates = build_candidates(targets, all_files, root, project_root)
    if len(candidates) > MAX_CANDIDATES:
        warnings.append(v("SCAN_TRUNCATED", where, "候选面 %d 条超上限 %d：仅保留前 %d 条"
                          % (len(candidates), MAX_CANDIDATES, MAX_CANDIDATES)))
        candidates = candidates[:MAX_CANDIDATES]
    return files, candidates, warnings


# ---------------------------------------------------------------- collect

def cmd_collect(args):
    root = os.path.abspath(args.project_root)
    out = os.path.abspath(args.output_dir)
    vcs, warnings = probe_vcs(root, args.since, root)
    files, candidates, struct_warnings = collect_structure(root, out, args.area, root)
    warnings += struct_warnings
    payload = {"ok": True, "command": "collect", "project_root": args.project_root,
               "output_dir": os.path.normpath(out).replace("\\", "/"),
               "area": args.area, "since": args.since, "vcs": vcs, "files": files,
               "candidates": candidates, "violations": [], "warnings": warnings,
               "counts": {"commits": len(vcs["commits"]), "files": len(files),
                          "candidates": len(candidates),
                          "by_kind": count_by(candidates, "kind")}}
    emit(payload, args.json, human_collect)
    return 0


def human_collect(payload):
    counts = payload["counts"]
    if payload["vcs"]["available"]:
        print("VCS：可用（head %s，近期提交 %d 条）"
              % (payload["vcs"]["head"] or "无", counts["commits"]))
    else:
        print("VCS：不可用（降级——见 warnings）")
    if payload["area"]:
        print("区域 %s：文件 %d 个 · 候选面 %d 条"
              % (payload["area"], counts["files"], counts["candidates"]))
    else:
        print("未给 --area：跳过结构情报（只做 VCS 采集）")
    for warning in payload["warnings"]:
        print("警告 %s %s: %s" % (warning["code"], warning["where"], warning["msg"]))


# ---------------------------------------------------------------- check

def check_enum(value, allowed, where, label):
    if not nonempty(value):
        return [v("EMPTY_FIELD", where, "%s 缺失" % label)]
    if str(value) not in allowed:
        return [v("ENUM_INVALID", where, "%s 越界：%s（合法集 %s）"
                  % (label, value, "|".join(allowed)))]
    return []


def missing_field(mapping, key, where, label=None):
    """必填非空字段：缺失/空串 → EMPTY_FIELD。"""
    if nonempty(mapping.get(key)):
        return []
    return [v("EMPTY_FIELD", where + "." + key, "%s 缺失" % (label or key))]


def check_pattern(value, pattern, hint, where, label, seen=None):
    """格式锚点：缺失 → EMPTY_FIELD；越格式 → ENUM_INVALID；seen 给定时查记录内唯一。"""
    if not nonempty(value):
        return [v("EMPTY_FIELD", where, "%s 缺失" % label)]
    if not pattern.fullmatch(str(value)):
        return [v("ENUM_INVALID", where, "%s 须为 %s，实为 %s" % (label, hint, value))]
    if seen is not None:
        if str(value) in seen:
            return [v("DUPLICATE_ID", where, "%s 重复：%s" % (label, value))]
        seen.add(str(value))
    return []


def check_evidence(record, where):
    violations = []
    evidence = record.get("evidence")
    if evidence is None:
        return [v("EMPTY_FIELD", where + ".evidence",
                  "evidence 缺失（无证据写空列表——证据分级是本案核心）")]
    if not isinstance(evidence, list):
        return [v("EMPTY_FIELD", where + ".evidence", "evidence 不是列表")]
    seen = set()
    for i, ev in enumerate(evidence):
        ew = "%s.evidence[%d]" % (where, i)
        if not isinstance(ev, dict):
            violations.append(v("EMPTY_FIELD", ew, "evidence 项不是映射"))
            continue
        violations += check_pattern(ev.get("id"), EV_RE, "EV-0nn（三位零填充）",
                                    ew + ".id", "EV ID", seen)
        violations += check_enum(ev.get("grade"), GRADES, ew + ".grade", "grade")
        violations += check_enum(ev.get("availability"), AVAILABILITIES,
                                 ew + ".availability", "availability")
        violations += missing_field(ev, "ref", ew, "ref（path:line / timestamp / commit）")
        violations += missing_field(ev, "note", ew)
    return violations


def check_hypotheses(record, where):
    """假设生命周期：永不删除——状态转移必须带 Resolution（源纪律机械化）。"""
    violations = []
    hypotheses = record.get("hypotheses")
    if hypotheses is None:
        return [v("EMPTY_FIELD", where + ".hypotheses",
                  "hypotheses 缺失（无假设写空列表；假设永不删除）")]
    if not isinstance(hypotheses, list):
        return [v("EMPTY_FIELD", where + ".hypotheses", "hypotheses 不是列表")]
    seen = set()
    for i, hyp in enumerate(hypotheses):
        hw = "%s.hypotheses[%d]" % (where, i)
        if not isinstance(hyp, dict):
            violations.append(v("EMPTY_FIELD", hw, "hypotheses 项不是映射"))
            continue
        violations += check_pattern(hyp.get("id"), H_RE, "H-0nn（三位零填充）",
                                    hw + ".id", "H ID", seen)
        violations += missing_field(hyp, "statement", hw)
        status = hyp.get("status")
        violations += check_enum(status, HYPOTHESIS_STATUSES, hw + ".status", "status")
        if nonempty(status) and str(status) != "open":
            violations += missing_field(hyp, "resolution", hw, "resolution（何时/何证据结案）")
    return violations


def check_stronghold(record, where):
    """据点先行（源纪律）：evidence_light=false 的案件必须有据点。"""
    stronghold = record.get("stronghold")
    if stronghold is None:
        if record.get("evidence_light") is True:
            return []
        return [v("EMPTY_FIELD", where + ".stronghold",
                  "据点缺失（先锚一条 confirmed 证据再外扩；无据案件须标记 evidence_light: true）")]
    if not isinstance(stronghold, dict):
        return [v("EMPTY_FIELD", where + ".stronghold", "stronghold 不是映射")]
    violations = missing_field(stronghold, "ref", where + ".stronghold",
                               "ref（path:line / timestamp / commit）")
    return violations + missing_field(stronghold, "why", where + ".stronghold")


def check_case_info(record, where):
    violations = []
    info = record.get("case_info")
    if info is None:
        return [v("EMPTY_FIELD", where + ".case_info",
                  "case_info 缺失（inputs / scope / time_window）")]
    if not isinstance(info, dict):
        return [v("EMPTY_FIELD", where + ".case_info", "case_info 不是映射")]
    inputs = info.get("inputs")
    if not isinstance(inputs, list) or not inputs:
        violations.append(v("EMPTY_FIELD", where + ".case_info.inputs",
                            "inputs 须为非空列表（输入形：ticket/archive/log/description/area/commit）"))
    else:
        for i, entry in enumerate(inputs):
            iw = "%s.case_info.inputs[%d]" % (where, i)
            if not isinstance(entry, dict):
                violations.append(v("EMPTY_FIELD", iw, "输入项不是映射"))
                continue
            violations += check_enum(entry.get("kind"), INPUT_KINDS, iw + ".kind", "kind")
            if not nonempty(entry.get("ref")):
                violations.append(v("EMPTY_FIELD", iw + ".ref", "输入 ref 缺失"))
    return violations


def check_timeline(record, where, final):
    violations = []
    timeline = record.get("timeline")
    if timeline is None:
        if final:
            violations.append(v("EMPTY_FIELD", where + ".timeline",
                                "--final 要求 timeline 非空（时间线重建是定稿前提）"))
        return violations
    if not isinstance(timeline, list):
        return [v("EMPTY_FIELD", where + ".timeline", "timeline 不是列表")]
    for i, entry in enumerate(timeline):
        tw = "%s.timeline[%d]" % (where, i)
        if not isinstance(entry, dict):
            violations.append(v("EMPTY_FIELD", tw, "时间线项不是映射"))
            continue
        violations += missing_field(entry, "at", tw)
        violations += missing_field(entry, "event", tw)
    if final and not timeline:
        violations.append(v("EMPTY_FIELD", where + ".timeline", "--final 要求 timeline 非空"))
    return violations


def check_backlog(record, where):
    violations = []
    backlog = record.get("backlog")
    if backlog is None:
        return violations
    if not isinstance(backlog, list):
        return [v("EMPTY_FIELD", where + ".backlog", "backlog 不是列表")]
    for i, entry in enumerate(backlog):
        bw = "%s.backlog[%d]" % (where, i)
        if not isinstance(entry, dict):
            violations.append(v("EMPTY_FIELD", bw, "backlog 项不是映射"))
            continue
        violations += missing_field(entry, "item", bw)
        violations += missing_field(entry, "priority", bw)
        violations += check_enum(entry.get("status"), BACKLOG_STATUSES, bw + ".status", "status")
    return violations


def check_missing_evidence(record, where):
    """缺失证据也是发现（源纪律）：evidence-light 案件必须记账缺失面。"""
    violations = []
    missing = record.get("missing_evidence")
    if missing is None:
        missing = []
    if not isinstance(missing, list):
        return [v("EMPTY_FIELD", where + ".missing_evidence", "missing_evidence 不是列表")]
    for i, entry in enumerate(missing):
        mw = "%s.missing_evidence[%d]" % (where, i)
        if not isinstance(entry, dict):
            violations.append(v("EMPTY_FIELD", mw, "缺失证据项不是映射"))
            continue
        violations += missing_field(entry, "what", mw)
        violations += missing_field(entry, "how", mw, "how（如何取得）")
        if entry.get("would_resolve") is not None and not nonempty(entry.get("would_resolve")):
            violations.append(v("EMPTY_FIELD", mw + ".would_resolve",
                                "would_resolve 出现时不得为空"))
    if record.get("evidence_light") is True and not missing:
        violations.append(v("EVIDENCE_MISSING", where + ".missing_evidence",
                            "evidence_light: true 案件须记缺失证据（what/would_resolve/how）——"
                            "缺失证据也是发现"))
    return violations


def check_note_entries(record, key, where, with_date=False):
    """追加式列表共用（follow_ups / side_findings）：条目映射 + note 必填；with_date 时 date 必填。"""
    entries = record.get(key)
    if entries is None:
        return []
    if not isinstance(entries, list):
        return [v("EMPTY_FIELD", "%s.%s" % (where, key), "%s 不是列表" % key)]
    violations = []
    for i, entry in enumerate(entries):
        ew = "%s.%s[%d]" % (where, key, i)
        if not isinstance(entry, dict):
            violations.append(v("EMPTY_FIELD", ew, "%s 项不是映射" % key))
            continue
        violations += missing_field(entry, "note", ew)
        if with_date:
            violations += check_pattern(entry.get("date"), DATE_RE, "YYYY-MM-DD",
                                        ew + ".date", "date")
    return violations


def check_conclusion(record, where, final):
    violations = []
    conclusion = record.get("conclusion")
    if conclusion is None:
        if final:
            violations.append(v("EMPTY_FIELD", where + ".conclusion",
                                "--final 要求 conclusion 在场（结论 + confidence）"))
        return violations
    if not isinstance(conclusion, dict):
        return [v("EMPTY_FIELD", where + ".conclusion", "conclusion 不是映射")]
    if final and not nonempty(conclusion.get("text")):
        violations.append(v("EMPTY_FIELD", where + ".conclusion.text",
                            "--final 要求结论文本非空"))
    confidence = conclusion.get("confidence")
    if not nonempty(confidence):
        if final:
            violations.append(v("PENDING_DECISION", where + ".conclusion.confidence",
                                "--final 要求 confidence 已定（high|medium|low）"))
    elif str(confidence) not in CONFIDENCES:
        violations.append(v("ENUM_INVALID", where + ".conclusion.confidence",
                            "confidence 越界：%s（合法集 %s）"
                            % (confidence, "|".join(CONFIDENCES))))
    return violations


def check_final_duties(record, where):
    violations = []
    if not nonempty(record.get("handoff_brief")):
        violations.append(v("EMPTY_FIELD", where + ".handoff_brief",
                            "--final 要求 handoff_brief 非空（3 句、15 秒读完）"))
    if any("[ASSUMPTION]" in s for s in collect_strings(record)):
        violations.append(v("ASSUMPTION_PRESENT", where,
                            "--final 要求零 [ASSUMPTION]；未决推断须先落定"))
    return violations


def check_record(index, record, final, where_base):
    violations = []
    where = "%s.cases[%d]" % (where_base, index)
    if not isinstance(record, dict):
        return [v("EMPTY_FIELD", where, "记录不是映射")]

    violations += check_pattern(record.get("id"), IV_RE, "IV-0nn（三位零填充）",
                                where + ".id", "id", set())
    violations += check_pattern(record.get("slug"), SLUG_RE, "小写字母数字连字符（kebab）",
                                where + ".slug", "slug")
    violations += check_pattern(record.get("date"), DATE_RE, "YYYY-MM-DD",
                                where + ".date", "date")
    violations += check_enum(record.get("status"), RECORD_STATUSES, where + ".status", "status")
    violations += check_enum(record.get("mode"), MODES, where + ".mode", "mode")
    light = record.get("evidence_light")
    if not isinstance(light, bool):
        violations.append(v("ENUM_INVALID", where + ".evidence_light",
                            "evidence_light 须为布尔（实为 %s）" % light))
    if not nonempty(record.get("problem_statement")):
        violations.append(v("EMPTY_FIELD", where + ".problem_statement",
                            "problem_statement 缺失（用户原述优先，作为假设待验证）"))

    violations += check_case_info(record, where)
    violations += check_stronghold(record, where)
    violations += check_evidence(record, where)
    violations += check_hypotheses(record, where)
    violations += check_timeline(record, where, final)
    violations += check_backlog(record, where)
    violations += check_missing_evidence(record, where)
    violations += check_conclusion(record, where, final)

    violations += check_note_entries(record, "follow_ups", where, with_date=True)
    violations += check_note_entries(record, "side_findings", where)

    if final:
        violations += check_final_duties(record, where)
    return violations


def cmd_check(args):
    root = os.path.abspath(args.project_root)
    out = os.path.abspath(args.output_dir)
    path = os.path.join(out, INVESTIGATION_FILE)
    show = display_path(path, root)
    violations = []
    warnings = []
    cases = []
    selected = None

    data, err = load_yaml_safe(path)
    if data is None and err is None:
        violations.append(v("MISSING_FILE", show,
                            "%s 不存在（先完成一次案件起草）" % INVESTIGATION_FILE))
    elif err is not None:
        violations.append(v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err))
    elif not isinstance(data, dict):
        violations.append(v("EMPTY_FIELD", show, "顶层不是映射（须为 project + cases）"))
    else:
        project = data.get("project")
        if project is not None and not isinstance(project, dict):
            violations.append(v("EMPTY_FIELD", show + " project", "project 不是映射"))
        status = project.get("status") if isinstance(project, dict) else None
        if nonempty(status) and str(status) not in DOC_STATUSES:
            violations.append(v("ENUM_INVALID", show + " project.status",
                                "status 越界：%s（合法集 %s）"
                                % (status, "|".join(DOC_STATUSES))))
        if args.final and str(status) != "final":
            violations.append(v("STATUS_MISMATCH", show + " project.status",
                                "--final 要求 project.status 已落 final（实为 %s）"
                                % (status if nonempty(status) else "未声明")))
        revisions = data.get("revisions")
        if revisions is not None and not isinstance(revisions, list):
            violations.append(v("EMPTY_FIELD", show + " revisions", "revisions 不是列表"))
        raw_cases = data.get("cases")
        if raw_cases is None:
            violations.append(v("EMPTY_FIELD", show + " cases",
                                "cases 缺失（集合形态；无记录写空列表）"))
        elif not isinstance(raw_cases, list):
            violations.append(v("EMPTY_FIELD", show + " cases", "cases 不是列表"))
        else:
            cases = raw_cases
            seen = set()
            for i, record in enumerate(cases):
                if isinstance(record, dict) and nonempty(record.get("id")):
                    rid = str(record["id"])
                    if rid in seen:
                        violations.append(v("DUPLICATE_ID", "%s.cases[%d].id" % (show, i),
                                            "记录 ID %s 重复（IV ID 稳定不重用）" % rid))
                    seen.add(rid)
            selected = None
            if nonempty(args.id):
                selected = [r for r in cases
                            if isinstance(r, dict) and str(r.get("id")) == str(args.id)]
                if not selected:
                    violations.append(v("UNKNOWN_ID", show + " cases[].id",
                                        "%s 不存在（--id 只校验已存在的案件）" % args.id))
            else:
                selected = cases
            for i, record in enumerate(cases):
                if selected is not None and record not in selected:
                    continue
                violations += check_record(i, record, args.final, show)
            if args.final and not selected:
                violations.append(v("EMPTY_FIELD", show + " cases",
                                    "--final 要求至少 1 条记录"))

    counts = {
        "cases": len(cases),
        "by_status": count_by(cases, "status"),
        "by_mode": count_by(cases, "mode"),
        "evidence": count_items(cases, "evidence"),
        "by_grade": count_by_grade(cases),
        "hypotheses": count_items(cases, "hypotheses"),
        "open_hypotheses": count_open_hypotheses(cases),
        "missing_evidence": count_items(cases, "missing_evidence"),
        "side_findings": count_items(cases, "side_findings"),
    }
    ok = not violations
    payload = {"ok": ok, "command": "check", "project_root": args.project_root,
               "output_dir": os.path.normpath(out).replace("\\", "/"),
               "final": args.final, "violations": violations, "warnings": warnings,
               "counts": counts}
    emit(payload, args.json, human_check)
    return 0 if ok else 1


def human_check(payload):
    if payload["ok"]:
        print("PASS：%s 校验通过（cases=%d）"
              % (payload["output_dir"] + "/" + INVESTIGATION_FILE,
                 payload["counts"]["cases"]))
        return
    print("FAIL：")
    for item in payload["violations"]:
        print("- %s %s: %s" % (item["code"], item["where"], item["msg"]))


def emit(payload, as_json, human_lines):
    if as_json:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        human_lines(payload)


def build_parser():
    ap = argparse.ArgumentParser(
        description="diy-investigate 确定性引擎：证据现场采集（collect）+ "
                    "investigation.yaml 校验（check）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("collect", help="证据现场采集：VCS 情报 + 区域文件清单 + 候选面（只读）")
    p.add_argument("--area", default=None,
                   help="目标区域（文件或目录；结构情报的锚点）")
    p.add_argument("--since", default=None,
                   help="git log 起始（如 '2026-09-01' 或 '3 days ago'）")
    p.add_argument("--project-root", default=".", help="项目根（默认 .）")
    p.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    p.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    p.set_defaults(func=cmd_collect)

    k = sub.add_parser("check", help="校验 investigation.yaml（schema/枚举/ID/证据纪律）")
    k.add_argument("--id", default=None, help="只校验指定案件（IV-xxx）")
    k.add_argument("--project-root", default=".", help="项目根（默认 .）")
    k.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    k.add_argument("--final", action="store_true",
                   help="定稿校验：project.status final + conclusion/handoff_brief/timeline + 零假设")
    k.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    k.set_defaults(func=cmd_check)
    return ap


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = build_parser().parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
