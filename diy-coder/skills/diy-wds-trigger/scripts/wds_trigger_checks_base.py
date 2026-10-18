"""diy-wds-trigger 基础检查与常量表。"""

import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import display_path, enum_check, load_yaml_safe, nonempty, project_name, require, v  # noqa: E402

PRODUCT_FILE = "wds-trigger.yaml"
UPSTREAM_FILE = "wds-brief.yaml"
UPSTREAM_SKILL = "diy-wds-brief"

# 推进与模式（`stage` 是续接锚点；`mode` / `entry` 是参与方式，由 init 铸造）
STAGE_ENUM = ("模式", "目标", "驱动", "优先级", "特征", "成品", "收尾")
MODE_ENUM = ("W", "S", "D")
ENTRY_ENUM = ("工作坊", "既有产物")
FINAL_STAGE = STAGE_ENUM[-1]

# 母本 §8 两值口径：单记录产物 → 顶层 `project.status`（裁定 2，零偏离）
STATUS_ENUM = ("草稿", "已定稿")

# 裁定 6：三组互斥口径取「采集端」较宽侧——驱动因素 3–5/类、人物群 2–4
DRIVER_RANGE = (3, 5)
PERSONA_RANGE = (2, 4)
GOAL_RANGE = (3, 5)

GOAL_KIND_ENUM = ("愿景", "目标")
PERSONA_PRIORITY_ENUM = ("主", "其他")
LEVEL_ENUM = ("高", "中", "低")
# 裁定 10：Feature Impact 保留（Primary 5/3/1、其他 3/1/0、Must-Have 阈值）
DECISION_ENUM = ("必须", "应该", "可选")
SCORE_PRIMARY = {"高": 5, "中": 3, "低": 1}
SCORE_OTHER = {"高": 3, "中": 1, "低": 0}
MUST_HAVE_SLACK = 3

# §2.3 冻结的主体段（缺一不可）；`driver_patterns` 是跨群模式，**不与 `personas[]` 并列放
# `driving_forces[]`**（裁定 16）
TOP_KEYS = ("business_goals", "personas", "driver_patterns", "priority", "feature_impact",
            "effect_map")
GOAL_KEYS = ("id", "kind", "statement")
GOAL_TARGET_KEYS = ("metric", "target", "timeline")
PERSONA_KEYS = ("id", "name", "role", "priority", "summary", "context", "goals",
                "frustrations", "current_behavior", "driving_forces")
DRIVER_KEYS = ("id", "statement", "why")
DRIVER_POSITIVE_KEY = "promise"     # 源侧：正向驱动因素各带 `[Product] Promise`
DRIVER_NEGATIVE_KEY = "answer"      # 源侧：负向驱动因素各带 `[Product] Answer`
PATTERN_KEYS = ("shared", "unique", "tensions")
PRIORITY_KEYS = ("ranked_personas", "ranked_drivers", "focus_statement")
FEATURE_KEYS = ("id", "name", "scores", "score", "decision", "rationale")
EFFECT_MAP_KEYS = ("derived_from", "format", "direction", "config", "nodes", "connections",
                   "class_defs", "diagram")

# Effect Map 构图纪律（裁定 7：08a–08h 收编为唯一定义）——四类样式色值逐字取自源 `08g:63-66`
CLASS_DEFS = ("classDef businessGoal fill:#f3f4f6,color:#1f2937,stroke:#d1d5db,stroke-width:2px",
              "classDef platform fill:#e5e7eb,color:#111827,stroke:#9ca3af,stroke-width:3px",
              "classDef targetGroup fill:#f9fafb,color:#1f2937,stroke:#d1d5db,stroke-width:2px",
              "classDef drivingForces fill:#f3f4f6,color:#1f2937,stroke:#d1d5db,stroke-width:2px")
DRIVER_EMOJI = ("✅", "❌")         # 正向 / 负向驱动因素（源 `08e`）
PLATFORM_NODE = "PLATFORM"          # 恒单个（源 `08a`）

GOAL_RE = re.compile(r"^BG-\d+$")
PERSONA_RE = re.compile(r"^TG-\d+$")
DRIVER_RE = re.compile(r"^DF-(\d+)\.(\d+)([+-])$")
FEATURE_RE = re.compile(r"^FI-\d+$")

ASSUMPTION_MARK = "[假设]"


def as_list(value):
    return value if isinstance(value, list) else []


def as_dict(value):
    return value if isinstance(value, dict) else {}


# ---------------------------------------------------------------- 回执与产物读取

def emit(payload, as_json, summary_line=None, body_lines=None):
    """打印回执并返回 exit code：0 = 放行，1 = 有违规/被拒绝（契约 §3）。"""
    if as_json:
        print(json.dumps(payload, ensure_ascii=False))
        return 0 if payload.get("ok") else 1
    if not payload.get("ok"):
        for item in payload.get("violations") or []:
            print("%s %s: %s" % (item["code"], item["where"], item["msg"]))
    else:
        for line in body_lines or []:
            print(line)
        print(summary_line or "PASS：%s 完成" % payload["command"])
    for item in payload.get("warnings") or []:
        print("WARN %s %s: %s" % (item["code"], item["where"], item["msg"]))
    if payload.get("violations"):
        print("FAIL：%d 条违规（exit 1）" % len(payload["violations"]))
    return 0 if payload.get("ok") else 1


def out_dir_or_violation(args, command):
    """只读子命令的 --output-dir：可省（§2.2），读产物的子命令省了须明确报缺。"""
    if nonempty(args.output_dir):
        return os.path.abspath(args.output_dir), None
    return None, v("EMPTY_FIELD", "--output-dir",
                   "%s 需读 %s，须给 --output-dir（取值由 `diyc.py resolve` 回执给；"
                   "引擎不设默认、不私读 diy-coder.yaml）" % (command, PRODUCT_FILE))


def read_document(path):
    """读产物 → (data | None, err)。None + err None = 缺席。"""
    data, err = load_yaml_safe(path)
    if data is not None and not isinstance(data, dict):
        return None, "顶层不是映射（须为 project + 六个主体段 + revisions）"
    return data, err


def upstream_gate(output_dir, root):
    """跨技能门禁（§2.3.1 冻结）：读 {output_dir}/wds-brief.yaml 且 project.status: 已定稿。

    返回违规列表——空列表 = 放行。缺失/未定稿一律**零写入**。
    """
    path = os.path.join(output_dir, UPSTREAM_FILE)
    show = display_path(path, root)
    data, err = load_yaml_safe(path)
    if err is not None:
        return [v("UNPARSABLE_YAML", show, "上游产物解析失败：%s（先修好简报再跑本技能）" % err)]
    if data is None:
        return [v("MISSING_FILE", show,
                  "缺上游产物——本技能的门禁 = %s 的 `project.status: 已定稿`；"
                  "请先跑 `%s`，本技能零产出停止" % (UPSTREAM_FILE, UPSTREAM_SKILL))]
    status = as_dict(data.get("project")).get("status")
    if str(status or "").strip() != STATUS_ENUM[1]:
        return [v("STATUS_MISMATCH", "%s.project.status" % show,
                  "上游简报 status = %s，门禁要求 %s（先跑 `%s` 定稿，本技能零产出停止）"
                  % (status if nonempty(status) else "空", STATUS_ENUM[1], UPSTREAM_SKILL))]
    return []


def brief_summary(data):
    """`list` 只回约定字段（不读正文）。"""
    project = as_dict(data.get("project"))
    return {"name": project.get("name"), "status": project.get("status"),
            "stage": data.get("stage"), "mode": data.get("mode"),
            "entry": data.get("entry"),
            "goals": len(as_list(data.get("business_goals"))),
            "personas": len(as_list(data.get("personas"))),
            "updated": project.get("updated")}


# ---------------------------------------------------------------- 计数体检（单一定义源）

def _range_finding(seq, low, high, where, label, require_present):
    """区间核对：越界 → (where, msg)；require_present=False 时空集合不报（草稿态常态）。"""
    count = len(seq)
    if count == 0 and not require_present:
        return None
    if low <= count <= high:
        return None
    return (where, "%s %d 条，越出 %d–%d" % (label, count, low, high))


def connection_shape(goals, personas):
    """Effect Map 连接数口径（源 `08f:70-77`）：目标数 + 2×人物数。"""
    return len(goals) + 2 * len(personas)


def expected_connections(goals, personas):
    """Effect Map 的连接（源 `08f`）：BG→PLATFORM ∪ PLATFORM→TG ∪ TG→DF（配对严格）。"""
    return (["BG%d --> PLATFORM" % i for i in range(len(goals))]
            + ["PLATFORM --> TG%d" % i for i in range(len(personas))]
            + ["TG%d --> DF%d" % (i, i) for i in range(len(personas))])


def count_findings(data, show, only_id=None, require_present=False):
    """四条越界情形的**单一定义源**：metrics 取 warning、check --final 取违规。

    四条：① 人物群 2–4；② 每人正向驱动 3–5；③ 每人负向驱动 3–5；④ 连接数 = 目标数 + 2×人物数。
    返回 (findings, needed) —— findings 为 (where, msg) 列表；needed 为连接数的实况字典。
    """
    findings = []
    personas = [x for x in as_list(data.get("personas")) if isinstance(x, dict)]
    goals = [x for x in as_list(data.get("business_goals")) if isinstance(x, dict)]
    # 群数与连接数是**文档级**——`--id` 只窄化「每人驱动因素」那一族
    label = "人物群（%s）" % "|".join(str(x.get("id") or "?") for x in personas)
    item = _range_finding(personas, PERSONA_RANGE[0], PERSONA_RANGE[1],
                          "%s.counts.personas" % show, label, require_present)
    if item is not None:
        findings.append(item)
    for index, record in enumerate(personas):
        pid = str(record.get("id") or "TG-?")
        if only_id is not None and pid != only_id:
            continue
        forces = as_dict(record.get("driving_forces"))
        for key, label in (("positive", "正向驱动因素"), ("negative", "负向驱动因素")):
            item = _range_finding(as_list(forces.get(key)),
                                  DRIVER_RANGE[0], DRIVER_RANGE[1],
                                  "%s.personas[%d].driving_forces.%s" % (show, index, key),
                                  "%s（%s）的%s" % (pid, key, label), require_present)
            if item is not None:
                findings.append(item)
    graph = as_dict(data.get("effect_map"))
    connections = as_list(graph.get("connections"))
    expected = connection_shape(goals, personas)
    needed = {"personas": len(personas), "goals": len(goals),
              "connections_expected": expected, "connections_actual": len(connections)}
    if len(connections) != expected:
        findings.append(("%s.effect_map.connections" % show,
                         "Effect Map 连接数 %d ≠ 目标数 %d + 2×人物数 %d = %d"
                         % (len(connections), len(goals), len(personas), expected)))
    return findings, needed


# ---------------------------------------------------------------- 校验

def check_goals(goals, show, final, out):
    """业务目标段：恰一条愿景（首条）+ 3–5 条目标；由 `init` 铸 `BG-<n>`。"""
    seen = set()
    vision_at = []
    targets = 0
    for index, record in enumerate(goals):
        where = "%s.business_goals[%d]" % (show, index)
        if not isinstance(record, dict):
            out.append(v("EMPTY_FIELD", where, "须为映射（id / kind / statement）"))
            continue
        ident = record.get("id")
        text = str(ident).strip() if isinstance(ident, str) else ""
        if not GOAL_RE.match(text):
            out.append(v("ENUM_INVALID", where + ".id",
                         "ID 形态越界：%s（须为 BG-<n>，裁定 8）" % (text or "空")))
        if text in seen:
            out.append(v("DUPLICATE_ID", where + ".id", "ID 重复：%s" % text))
        seen.add(text)
        kind = enum_check(record.get("kind"), GOAL_KIND_ENUM, where + ".kind",
                          "kind", out)
        if kind == GOAL_KIND_ENUM[0]:
            vision_at.append(index)
            if final:
                require(record, ("id", "statement"), where, out)
        elif kind == GOAL_KIND_ENUM[1]:
            targets += 1
            if final:
                require(record, GOAL_KEYS + GOAL_TARGET_KEYS, where, out)
    if final:
        if vision_at != [0]:
            out.append(v("STATUS_MISMATCH", "%s.business_goals" % show,
                         "须恰 1 条 `kind: 愿景` 且为首条（Effect Map 的 BG0 节点），"
                         "实为第 %s 条" % (", ".join(str(i) for i in vision_at) or "无")))
        low, high = GOAL_RANGE
        if not (low <= targets <= high):
            out.append(v("EMPTY_FIELD", "%s.business_goals" % show,
                         "业务目标须 %d–%d 条（源侧 SMART 目标口径），实为 %d"
                         % (low, high, targets)))


def persona_ids(data):
    return [str(as_dict(x).get("id") or "") for x in as_list(data.get("personas"))
            if isinstance(x, dict)]


def driver_index(data, out, show):
    """驱动因素 ID → 归属人物序号；顺带做形态 / 唯一性 / 归属核对。"""
    index = {}
    for pindex, record in enumerate(as_list(data.get("personas"))):
        if not isinstance(record, dict):
            continue
        pid = str(record.get("id") or "").strip()
        where = "%s.personas[%d]" % (show, pindex)
        if not PERSONA_RE.match(pid):
            out.append(v("ENUM_INVALID", where + ".id",
                         "ID 形态越界：%s（须为 TG-<n>，裁定 8）" % (pid or "空")))
        forces = as_dict(record.get("driving_forces"))
        for key in ("positive", "negative"):
            direction = "+" if key == "positive" else "-"
            for dindex, driver in enumerate(as_list(forces.get(key))):
                dw = "%s.driving_forces.%s[%d]" % (where, key, dindex)
                if not isinstance(driver, dict):
                    out.append(v("EMPTY_FIELD", dw, "须为映射（id / statement / why …）"))
                    continue
                ident = str(driver.get("id") or "").strip()
                match = DRIVER_RE.match(ident)
                if match is None:
                    out.append(v("ENUM_INVALID", dw + ".id",
                                 "ID 形态越界：%s（须为 DF-<n>.<m>+ / DF-<n>.<m>-，裁定 8）"
                                 % (ident or "空")))
                    continue
                if match.group(3) != direction:
                    out.append(v("SET_MISMATCH", dw + ".id",
                                 "%s 与所属数组 %s 方向不符" % (ident, key)))
                number = int(match.group(1))
                if pid and PERSONA_RE.match(pid) and number != pindex + 1:
                    out.append(v("SET_MISMATCH", dw + ".id",
                                 "%s 的序号 %d 与所属人物 %s 不符（序号 = 人物序号）"
                                 % (ident, number, pid)))
                if ident in index:
                    out.append(v("DUPLICATE_ID", dw + ".id", "驱动因素 ID 重复：%s" % ident))
                index[ident] = pid
    return index


def resolve_ids(values, known, where, label, out):
    """引用可解析核对（`id` / `ids` 两形态）。"""
    for item in as_list(values):
        if isinstance(item, str):
            ident = item
        elif isinstance(item, dict):
            ident = str(item.get("id") or "").strip()
            if not nonempty(item.get("why")):
                out.append(v("EMPTY_FIELD", where, "%s 的排序必须给 why（源侧硬要求）" % label))
        else:
            continue
        if ident and ident not in known:
            out.append(v("UNKNOWN_ID", where, "%s 引用的 ID %s 不存在" % (label, ident)))


def check_personas(data, show, final, out):
    """人物段：2–4 条、必填键、恰一条「主」、驱动因素嵌在人物内（裁定 16）。"""
    personas = as_list(data.get("personas"))
    seen = set()
    mains = 0
    for index, record in enumerate(personas):
        where = "%s.personas[%d]" % (show, index)
        if not isinstance(record, dict):
            out.append(v("EMPTY_FIELD", where, "须为映射（键表 %s）" % " / ".join(PERSONA_KEYS)))
            continue
        ident = str(record.get("id") or "").strip()
        if ident in seen:
            out.append(v("DUPLICATE_ID", where + ".id", "人物 ID 重复：%s" % ident))
        seen.add(ident)
        priority = enum_check(record.get("priority"), PERSONA_PRIORITY_ENUM,
                              where + ".priority", "priority", out)
        if priority == PERSONA_PRIORITY_ENUM[0]:
            mains += 1
        forces = as_dict(record.get("driving_forces"))
        if not final:
            continue
        require(record, PERSONA_KEYS, where, out)
        for key in ("positive", "negative"):
            mark = DRIVER_POSITIVE_KEY if key == "positive" else DRIVER_NEGATIVE_KEY
            for dindex, driver in enumerate(as_list(forces.get(key))):
                if not isinstance(driver, dict):
                    continue
                dw = "%s.driving_forces.%s[%d]" % (where, key, dindex)
                require(driver, DRIVER_KEYS + (mark,), dw, out)
        if priority == PERSONA_PRIORITY_ENUM[0]:
            require(as_dict(record.get("transformation")), ("before", "after"),
                    where + ".transformation", out)
    if final and mains != 1:
        out.append(v("STATUS_MISMATCH", "%s.personas" % show,
                     "须恰 1 条 `priority: 主`（Feature Impact 的加权基准），实为 %d 条" % mains))


def check_patterns(patterns, known, show, final, out):
    """跨群模式段（裁定 16）：共 / 独 / 张力。ID 解析恒核，键齐备只在 `--final`。"""
    if not isinstance(patterns, dict):
        out.append(v("EMPTY_FIELD", show + ".driver_patterns",
                     "须为映射（shared / unique / tensions）"))
        return
    for key in PATTERN_KEYS:
        for index, item in enumerate(as_list(patterns.get(key))):
            where = "%s.driver_patterns.%s[%d]" % (show, key, index)
            if not isinstance(item, dict):
                if final:
                    out.append(v("EMPTY_FIELD", where, "须为映射（ids / id + note）"))
                continue
            resolve_ids(item.get("ids") if key != "unique" else [item.get("id")],
                        known, where, key, out)
            if final and not nonempty(item.get("note")):
                out.append(v("EMPTY_FIELD", where + ".note", "note 为空"))
    if not final:
        return
    for key in PATTERN_KEYS:
        if key not in patterns:
            out.append(v("EMPTY_FIELD", "%s.driver_patterns.%s" % (show, key),
                         "缺跨群模式键 %s（共 / 独 / 张力）" % key))
    for key in ("shared", "unique"):
        if not nonempty(patterns.get(key)):
            out.append(v("EMPTY_FIELD", "%s.driver_patterns.%s" % (show, key),
                         "%s 为空——跨群共性与独有必须在场（张力允许为空）" % key))


def blank_document(project_root, stamp, mode, entry):
    """新建产物骨架：模式结论 + 首条记录（`BG-1` 愿景节点空位）+ 五段空位。"""
    name, warning = project_name(project_root)
    doc = {
        "project": {"name": name, "created": stamp, "updated": stamp,
                    "status": STATUS_ENUM[0]},
        "stage": STAGE_ENUM[0],
        "mode": mode,
        "entry": entry,
        "business_goals": [{"id": "BG-1", "kind": GOAL_KIND_ENUM[0]}],
        "personas": [],
        "driver_patterns": {key: [] for key in PATTERN_KEYS},
        "priority": {},
        "feature_impact": [],
        "effect_map": {},
        "revisions": [],
    }
    return doc, ([warning] if warning else [])
