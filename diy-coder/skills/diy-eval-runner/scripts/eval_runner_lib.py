# -*- coding: utf-8 -*-
"""diy-eval-runner 基础层：模式常量 + I/O 工具 + 回执/emit。"""
import io
import json
import os
import re
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import v  # noqa: E402
MODES = ("baseline", "variant", "quality", "trigger")
CONFIG_MODES = ("baseline", "variant", "quality")
# 每个模式用到的 config；顺序固定（`skill` 恒为被测侧 = delta 的被减项）
CONFIG_ORDER = {"baseline": ("skill", "bare"),
                "variant": ("skill", "variant"),
                "quality": ("skill",)}
SUBJECT_CONFIG = "skill"
DEFAULT_AGAINST = "bare"
DEFAULT_MODE = "quality"
EVAL_RUNS_SUBDIR = "eval-runs"
MEMLOG_NAME = ".memlog.md"
QUERIES_DIR = "queries"
ENTRY_TYPES = ("decision", "direction", "assumption", "gap", "note", "event")
FAILURE_STATUS = ("error", "timeout", "exception", "adapter-missing")
CASE_FILES = ("prompt.txt", "case.json", "timing.json")
DEFAULT_SKILL_DIR = ".claude/skills"
DEFAULT_THRESHOLD = 0.5
TOKEN_RE = re.compile(r"\{([^{}]*)\}")


# --------------------------------------------------------------- 基础工具

def utc_now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def memlog_now():
    return datetime.now().strftime("%Y-%m-%dT%H:%M")


def norm(path):
    return os.path.normpath(os.path.abspath(path)).replace("\\", "/")


def write_json(path, data):
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def read_json(path):
    """读 JSON；(数据, 错误) —— 不抛，调用方决定记违规还是降级。"""
    try:
        with io.open(path, "r", encoding="utf-8", errors="replace") as fh:
            return json.load(fh), None
    except (OSError, ValueError) as e:
        return None, str(e)


def write_text(path, text):
    """写文本。`newline="\\n"` 关掉平台换行翻译——transcript 必须逐字节保真落盘。"""
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def resolve_path_arg(raw, project_root, flag, violations):
    """路径参数解析：`{project-root}` 自解析，其余 `{...}` 令牌一律拒绝（纪律 2）。"""
    if raw is None:
        return None
    text = str(raw)
    if "{project-root}" in text:
        text = text.replace("{project-root}", project_root)
    leftovers = TOKEN_RE.findall(text)
    if leftovers:
        violations.append(v("TOKEN_UNRESOLVED", flag,
                            "路径参数含未解析令牌 {%s}——除 {project-root}（由 --project-root "
                            "自解析）外，其余 {...} 令牌一律拒绝" % leftovers[0]))
        return None
    return os.path.abspath(text)


def emit(payload, as_json, human_lines=None):
    """统一收口：--json 单行回执；否则中文人读行。返回 exit code。"""
    ok = bool(payload.get("ok"))
    if as_json:
        print(json.dumps(payload, ensure_ascii=False))
        return 0 if ok else 1
    for line in (human_lines or []):
        print(line)
    for item in payload.get("violations", []):
        print("VIOL %s %s: %s" % (item["code"], item["where"], item["msg"]))
    for item in payload.get("warnings", []):
        print("WARN %s %s: %s" % (item["code"], item["where"], item["msg"]))
    print("汇总：%s（违规 %d / 警告 %d）"
          % ("OK" if ok else "FAIL", len(payload.get("violations", [])),
             len(payload.get("warnings", []))))
    return 0 if ok else 1


def receipt(command, ok, project_root, output_dir, violations, warnings, counts, **extra):
    payload = {
        "ok": ok,
        "command": command,
        "project_root": project_root,
        "output_dir": output_dir,
        "violations": violations,
        "warnings": warnings,
        "counts": counts,
    }
    payload.update(extra)
    return payload
