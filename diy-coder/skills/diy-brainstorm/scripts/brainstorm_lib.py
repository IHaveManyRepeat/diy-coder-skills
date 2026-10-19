# -*- coding: utf-8 -*-
"""diy-brainstorm 常量表（产物/枚举/状态机/正则）与技术库加载、类名集、跨类抽样与回执打印。."""

import csv
import io
import json
import os
import random
import re

import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import display_path, methods_path, v  # noqa: E402

BRAINSTORM_FILE = "brainstorm.yaml"
METHODS_FILE = "brain-methods.csv"
LIB_COLUMNS = ("category", "technique_name", "description")

STATUS_ENUM = ("草稿", "进行中", "已完成")
APPROACH_ENUM = ("用户自选", "AI 推荐", "随机", "渐进流")
# 记录级状态机与续接锚点同档（裁定 1：current_step 是续接点，不是进度装饰）
STEP_BY_STATUS = {"草稿": (1,), "进行中": (2, 3, 4), "已完成": (5,)}
ASSUMPTION_MARK = "[假设]"
PROJECT_FIELDS = ("name", "created", "updated")

BS_RE = re.compile(r"BS-(\d{3})\Z")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}\Z")

# ---------------------------------------------------------------- 技术库

def load_methods(project_root):
    """加载技术库 → (rows | None, violations)。行结构 {category, technique_name, description}。"""
    path = methods_path(__file__, METHODS_FILE)
    show = display_path(path, project_root)
    if not os.path.isfile(path):
        return None, [v("MISSING_FILE", show, "%s 不存在（技能自带技术库）" % METHODS_FILE)]
    violations = []
    rows = []
    try:
        with io.open(path, "r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            missing = [c for c in LIB_COLUMNS if c not in (reader.fieldnames or [])]
            if missing:
                return None, [v("EMPTY_FIELD", show,
                                "技术库缺列：%s（须为 %s）" % ("|".join(missing),
                                                              "|".join(LIB_COLUMNS)))]
            for i, row in enumerate(reader):
                item = {key: (row.get(key) or "").strip() for key in LIB_COLUMNS}
                where = "%s 第 %d 行" % (show, i + 2)
                empty = [key for key in LIB_COLUMNS if not item[key]]
                if empty:
                    violations.append(v("EMPTY_FIELD", where,
                                        "技术条目缺 %s" % "|".join(empty)))
                    continue
                rows.append(item)
    except (csv.Error, OSError, UnicodeDecodeError) as e:
        return None, [v("UNPARSABLE_YAML", show, "技术库解析失败：%s" % e)]
    if violations:
        return None, violations
    if not rows:
        return None, [v("EMPTY_FIELD", show, "技术库无数据行")]
    return rows, []

def library_categories(rows):
    """库内类名（CSV 出现序去重）——`--category` 的合法集与 check 的枚举来源。"""
    seen = []
    for row in rows:
        if row["category"] not in seen:
            seen.append(row["category"])
    return seen

def sample_cross_category(rows, count):
    """跨类别优先抽样：按类分桶后轮转取，各类耗尽再补齐——保证组合多样（源 02c 语义）。"""
    buckets = {}
    for row in rows:
        buckets.setdefault(row["category"], []).append(row)
    order = list(buckets)
    random.shuffle(order)
    for bucket in buckets.values():
        random.shuffle(bucket)
    picked = []
    while len(picked) < count:
        before = len(picked)
        for category in order:
            if len(picked) >= count:
                break
            if buckets[category]:
                picked.append(buckets[category].pop())
        if len(picked) == before:
            break
    return picked

# ---------------------------------------------------------------- 命令面

def emit(payload, as_json, summary_line=None):
    """打印回执并返回 exit code：0 = 放行，1 = 有违规（契约 §3）。"""
    if as_json:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        if payload.get("ok"):
            print(summary_line or "PASS：%s 完成" % payload["command"])
        else:
            for item in payload.get("violations") or []:
                print("%s %s: %s" % (item["code"], item["where"], item["msg"]))
        for item in payload.get("warnings") or []:
            print("WARN %s %s: %s" % (item["code"], item["where"], item["msg"]))
        if payload.get("violations"):
            print("FAIL：%d 条违规（exit 1）" % len(payload["violations"]))
    return 0 if payload.get("ok") else 1
