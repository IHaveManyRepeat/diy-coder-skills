"""diy-wds-scenarios 常量表、IO 工具与骨架模板。"""

import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import load_yaml_safe, nonempty, project_name, v, violation_line, warn_line  # noqa: E402

SCENARIOS_FILE = "wds-scenarios.yaml"
TRIGGER_FILE = "wds-trigger.yaml"

# 上游读契约（§2.3.1 冻结的三组键）+ 门禁判据
UPSTREAM_KEYS = ("business_goals", "personas", "priority")
FINAL_UPSTREAM_STATUS = "已定稿"

# 母本 §8 两值口径：单记录产品形态 → 顶层 `project.status`（裁定 2，零偏离）
STATUS_ENUM = ("草稿", "已定稿")
# 记录级子状态（裁定 2 的可选记录级域）：本技能定义为本条大纲的推进锚点
RECORD_STATUS_ENUM = ("草稿", "已大纲")

# 规模分析（源 step-02）四件
SITE_TYPE_ENUM = ("presentation", "dynamic", "mixed")
SCALE_ENUM = ("small", "medium", "large")
SCENARIO_FORMAT_ENUM = ("screen-flow", "storyboard", "mixed")
# 大纲模式（源 step-02 推荐 → 源 step-05 实际实现的两态；`approach` 选填）
APPROACH_ENUM = ("对话", "建议")

# 交接契约（裁定 17）：设计意图五值 + 设计状态九值（初值 not-started）
DESIGN_INTENT_ENUM = ("K", "C", "S", "D", "L")
DESIGN_STATUS_INITIAL = "not-started"
DESIGN_STATUS_ENUM = ("not-started", "discussed", "wireframed", "specified", "explored",
                      "building", "built", "approved", "removed")

# ID 形态（裁定 8）
SCENARIO_ID_RE = re.compile(r"^SC-\d{2}$")
PAGE_ID_RE = re.compile(r"^SC-(\d{2})\.P(\d+)$")
PAGE_SLUG_RE = re.compile(r"^(\d{2})\.(\d+)-")
# 上游驱动因素 ID（`DF-<人物号>.<条号>+|-`，见 `diy-wds-trigger/SKILL.md` 结构段）
# 与早期草案的 `TG-<n>.…` 兼容写法——两种都用于「所消费驱动须属本记录人物」的核对。
DRIVER_ID_RE = re.compile(r"\bDF-(\d+)\.")
TG_ID_RE = re.compile(r"\bTG-(\d+)\b")

SCOPE_REQUIRED = ("site_type", "scale", "scenario_format", "page_strategy")
SCOPE_ENUMS = (("site_type", SITE_TYPE_ENUM), ("scale", SCALE_ENUM),
               ("scenario_format", SCENARIO_FORMAT_ENUM), ("approach", APPROACH_ENUM))
INVENTORY_KEYS = ("name", "purpose")
SCENARIO_REQUIRED = ("name", "priority", "status", "design_intent", "design_status",
                     "transaction", "situation", "device", "entry")
SCENARIO_NESTED = (("trigger_map_context", "target_group"),
                   ("trigger_map_context", "drivers"),
                   ("trigger_map_context", "business_goal"),
                   ("driving_forces", "hope"), ("driving_forces", "worry"),
                   ("success", "user"), ("success", "business"))
PAGE_REQUIRED = ("id", "slug", "name", "purpose")

ASSUMPTION_MARK = "[假设]"
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}\Z")


def text_of(value):
    """取字符串值并去空白；非字符串给空串（供比较用）。"""
    return value.strip() if isinstance(value, str) else ""


# ---------------------------------------------------------------- 回执与产物读取

def emit(payload, as_json, summary_line=None, body_lines=None):
    """打印回执并返回 exit code：0 = 放行，1 = 有违规/被拒绝（契约 §3）。"""
    if as_json:
        print(json.dumps(payload, ensure_ascii=False))
        return 0 if payload.get("ok") else 1
    if not payload.get("ok"):
        for item in payload.get("violations") or []:
            print(violation_line(item))
    else:
        for line in body_lines or []:
            print(line)
        print(summary_line or "PASS：%s 完成" % payload["command"])
    for item in payload.get("warnings") or []:
        print(warn_line(item))
    if payload.get("violations"):
        print("FAIL：%d 条违规（exit 1）" % len(payload["violations"]))
    return 0 if payload.get("ok") else 1


def out_dir_or_violation(args, command):
    """只读子命令的 --output-dir：可省（§2.2），读产物的子命令省了须明确报缺。"""
    if nonempty(args.output_dir):
        return os.path.abspath(args.output_dir), None
    return None, v("EMPTY_FIELD", "--output-dir",
                   "%s 需读 %s，须给 --output-dir（取值由 `diyc.py resolve` 回执给；"
                   "引擎不设默认、不私读 diy-coder.yaml）" % (command, SCENARIOS_FILE))


def read_document(path):
    """读产物 → (data | None, err)。None + err None = 缺席。"""
    data, err = load_yaml_safe(path)
    if data is not None and not isinstance(data, dict):
        return None, "顶层不是映射（须为 project + scope + page_inventory + scenarios）"
    return data, err


def upstream_personas(output_dir):
    """上游读契约（§2.3.1）：(TG-n → 人物记录, 上游路径, err)。缺席 → ({}, path, None)。"""
    path = os.path.join(output_dir, TRIGGER_FILE)
    data, err = load_yaml_safe(path)
    if not isinstance(data, dict):
        return {}, path, err
    people = {}
    for item in data.get("personas") or []:
        if isinstance(item, dict) and nonempty(item.get("id")):
            people[text_of(item.get("id"))] = item
    return people, path, None


def coverage_of(data):
    """页面覆盖矩阵（★ 本引擎的核心机械核对）。

    返回 (inventory_names, rows)：`rows` 逐行 = 场景内的每一页（含它在哪条链上）。
    连接键 = 页面的**展示名**（`page_inventory[].name` ↔ `pages[].name`）；
    引用键 = `SC-<nn>.P<n>`（父子引用）——两者都核（前者核覆盖，后者核同源）。
    """
    names = []
    for item in data.get("page_inventory") or []:
        if isinstance(item, dict) and nonempty(item.get("name")):
            names.append(text_of(item.get("name")))
    rows = []
    for record in data.get("scenarios") or []:
        if not isinstance(record, dict):
            continue
        for node in record.get("pages") or []:
            if not isinstance(node, dict):
                continue
            rows.append({"page": text_of(node.get("name")) or None,
                         "scenario": text_of(record.get("id")) or None,
                         "purpose_in_flow": node.get("purpose")})
    return names, rows


def coverage_report(data):
    """覆盖矩阵回执（`check` / `show` 共用）：counts + 行 + 三条差集。"""
    names, rows = coverage_of(data)
    assigned = [row["page"] for row in rows if row["page"]]
    seen = {}
    for name in assigned:
        seen[name] = seen.get(name, 0) + 1
    inventory_closed = set(names)
    covered = [name for name in names if seen.get(name)]
    return {"total": len(names), "covered": len(covered),
            "rate": "%d/%d" % (len(covered), len(names)),
            "matrix": rows,
            "unassigned": [name for name in names if not seen.get(name)],
            "repeated": [name for name, count in seen.items() if count > 1],
            "unknown": [name for name in seen if name not in inventory_closed],
            "duplicated": [name for name in inventory_closed
                           if names.count(name) > 1]}


# ---------------------------------------------------------------- list / show

def scenario_summary(record):
    """`list` 只回六字段（对照源 `00-ux-scenarios.md` 摘要表列；不读正文）。"""
    context = record.get("trigger_map_context")
    context = context if isinstance(context, dict) else {}
    pages = record.get("pages")
    return {"id": record.get("id"),
            "name": record.get("name"),
            "persona": context.get("target_group"),
            "pages": len(pages) if isinstance(pages, list) else 0,
            "priority": record.get("priority"),
            "status": record.get("status")}


def blank_document(project_root, stamp, site_type, scale, scenario_format):
    """新建产物骨架：分诊后段（scope）空位 + 页清单空表 + 首条记录铸号（`SC-01`）。

    首条记录只有 `id` / 留空 `name` / `status: 草稿`——场景名与人物引用要到 03-plan
    「用户关卡 2」之后才存在；此处铸号保证 **ID 顺序递增且不重编不复用**。
    """
    name, warning = project_name(project_root)
    scope = {"site_type": site_type}
    if nonempty(scale):
        scope["scale"] = scale
    if nonempty(scenario_format):
        scope["scenario_format"] = scenario_format
    doc = {
        "project": {"name": name, "created": stamp, "updated": stamp,
                    "status": STATUS_ENUM[0]},
        "scope": scope,
        "page_inventory": [],
        "scenarios": [{"id": "SC-01", "name": "", "status": RECORD_STATUS_ENUM[0]}],
        "revisions": [],
    }
    return doc, ([warning] if warning else [])


def find_record(data, target):
    """按记录 ID 找场景或页面：`SC-<nn>` / `SC-<nn>.P<n>`；找不到 → None。"""
    for record in data.get("scenarios") or []:
        if not isinstance(record, dict):
            continue
        if text_of(record.get("id")) == target:
            return record
        for node in record.get("pages") or []:
            if isinstance(node, dict) and text_of(node.get("id")) == target:
                return node
    return None
