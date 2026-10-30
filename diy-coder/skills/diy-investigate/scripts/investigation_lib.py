# -*- coding: utf-8 -*-
"""diy-investigate 常量表（状态/枚举/ID 正则/扫描上限）与共用助手：条目计数、字段检查三件套。."""

import re

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import count_by  # noqa: E402

INVESTIGATION_FILE = "investigation.yaml"

DOC_STATUSES = ("草稿", "已定稿")
RECORD_STATUSES = ("调查中", "已结论", "待证据阻塞")
MODES = ("症状驱动", "探索")
GRADES = ("已确证", "已推断", "假设中")
AVAILABILITIES = ("可得", "部分可得", "缺失")
HYPOTHESIS_STATUSES = ("待验证", "已确证", "已推翻")
CONFIDENCES = ("高", "中", "低")
BACKLOG_PRIORITIES = ("高", "中", "低")           # 数据采集项的自然刻度
BACKLOG_STATUSES = ("待办", "已完成", "无法获取")
INPUT_KINDS = ("工单", "归档", "日志", "描述", "范围", "提交")

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

def iter_entries(records, key):
    """遍历各记录该列表键的映射条目（跳过非映射；计数助手共用）。"""
    for record in records:
        if isinstance(record, dict) and isinstance(record.get(key), list):
            for entry in record[key]:
                if isinstance(entry, dict):
                    yield entry

def count_open_hypotheses(records):
    return len([h for h in iter_entries(records, "hypotheses") if h.get("status") == "待验证"])

def count_by_grade(records):
    return count_by(iter_entries(records, "evidence"), "grade")
