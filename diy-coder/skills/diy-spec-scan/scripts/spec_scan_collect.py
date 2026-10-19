# -*- coding: utf-8 -*-
"""diy-spec-scan collect 命令域：扫描目标枚举（文件 / 含 SKILL.md 的技能目录 / 普通目录一层 .md）、目标文件读取与二级标题单元切分建议、collect 回执（只读不写）。."""

import io
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import display_path, emit_via, v  # noqa: E402
SKILL_FILE = "SKILL.md"
STEPS_DIR = "steps"
MD_SUFFIX = ".md"
HEADING = "## "

# trace: diy-spec-scan 违规项构造（统一 {code, where, msg} 形态）

# trace: diy-spec-scan 非空判定（None / 空白字符串均视为空）

# trace: diy-spec-scan 递归收集任意节点的字符串值（[假设] 扫描用，只看值不看键）

# trace: diy-spec-scan YAML 安全装载：(data, err)；缺失 (None, None)、空文件 ({}, None)、损坏 (None, 原因)

# trace: diy-spec-scan 回执输出（--json 单行 / 人读行）

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
    emit_via(payload, args.json, human_collect)
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
