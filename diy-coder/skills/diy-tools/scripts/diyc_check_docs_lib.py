# -*- coding: utf-8 -*-
"""diyc check 文档级通用工具：常量/Report/锚点辅助（契约 §4.2）。"""

import re

import diyc_lib
from diyc_lib import items

# v4 批 3（§7-3b）：created/updated 格式断言——两格式兼容（纯日期 | 日期＋空格＋
# 时分秒；存量纯日期仍合法）。兼防忘跑 stamp 闭环：C 组产物留空（空串）/乱写即红；
# 键缺席归各 checker 的 project 非空门分工，此处不重复
TIME_RE = re.compile(r"\d{4}-\d{2}-\d{2}( \d{2}:\d{2}:\d{2})?")


def check_project_times(doc, rel, report):
    """全类型通用：project.created/updated 有值必合法（两格式）；空串＝未盖章红。"""
    project = doc.get("project")
    if not isinstance(project, dict):
        return
    for key in ("created", "updated"):
        value = project.get(key)
        if value is None:
            continue
        if not isinstance(value, str) or not TIME_RE.fullmatch(value.strip()):
            report.add("ENUM_INVALID", "%s project.%s" % (rel, key),
                       "时间键须为 YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS，实为 %r"
                       "（留空＝未盖章，跑 diyc stamp --type <类型>）" % (value,))

# 裁定 22（C·3a · W9）：`affects` 的 SC/P 域须经 `Docs` 读 wds-scenarios——注册项
# （`DOC_FILES["wds-scenarios"]`）已于 2026-09-28 收口期归位 `diyc_lib.py`，此处不再就地补登记。

# 枚举（逐条对照各 SKILL.md Schema 节的机器锚）
# rule: diy-test-design/SKILL.md:Schema technique 13 值（前 9 设计期 + 后 4 补测）
TECHNIQUES = ("等价类", "边界", "决策表", "状态迁移",
              "成对组合", "错误猜测", "蜕变测试", "属性测试", "场景",
              "覆盖分支", "MC-DC 覆盖", "白盒路径", "变异杀伤")
CASE_TYPES = ("单元", "集成", "端到端")              # rule: diy-test-design/SKILL.md:Design Discipline（Type maps to layer）
PRIORITIES = ("P0", "P1", "P2")                      # rule: diy-test-design/SKILL.md:Design Discipline（Priority maps to risk）
TC_STATUSES = ("待办", "通过", "失败")               # rule: diy-test-design/SKILL.md:Schema status
GAP_DECISIONS = ("待办", "已豁免", "接受缺口")       # rule: diy-test-design/SKILL.md:Schema coverage_gaps.decision
DIMENSIONS = ("正向", "边界", "异常", "安全", "性能")  # rule: diy-test-design/SKILL.md:Schema dimension（五轴·一条用例一个轴）
RADII = ("局部", "模块", "跨模块", "系统", "外部")    # rule: diy-test-design/SKILL.md:Schema radius（爆炸半径标注·FH/TC 同族）
FR_PRIORITIES = ("必须", "应该", "可选")             # rule: diy-prd/SKILL.md:Schema requirements.priority
DEC_STATUSES = ("待定", "已采纳")                    # rule: diy-architecture/SKILL.md:Schema decisions.status
STACK_KINDS = ("frontend", "scaffold", "language", "test", "lint", "typecheck",
               "build")  # rule: diy-architecture/SKILL.md:Schema stack.kind（封闭七类）
EPIC_STATUSES = ("待办", "进行中", "已完成")         # rule: diy-epics-stories/SKILL.md:Schema epics.status
STORY_STATUSES = ("待办", "进行中", "待审查", "已完成", "已阻塞")  # rule: diy-epics-stories/SKILL.md:Schema stories.status
HTTP_METHODS = ("get", "put", "post", "delete", "options", "head", "patch", "trace")
PATH_ITEM_KEYS = ("parameters", "summary", "description", "servers", "$ref")


class Report:
    """违规/警告收集器；where 统一正斜杠（契约 §3）。"""

    def __init__(self):
        self.violations = []
        self.warnings = []

    def add(self, code, where, msg):
        self.violations.append(diyc_lib.v(code, where, msg))

    def warn(self, msg):
        self.warnings.append(msg)


# ---------------------------------------------------------------- 通用形状工具


def is_str(value) -> bool:
    return isinstance(value, str)


def nonempty(value) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return len(value) > 0
    return value is not None and not isinstance(value, bool)


def req(report, where, value, label, code="EMPTY_FIELD") -> bool:
    """必填校验：字符串非空 / 列表字典非空。"""
    if nonempty(value):
        return True
    report.add(code, where, "%s 缺失或为空" % label)
    return False


def enum(report, where, value, allowed, label, code="ENUM_INVALID") -> bool:
    if value in allowed:
        return True
    report.add(code, where, "%s 取值 %r 非法，应为 %s" % (label, value, "/".join(allowed)))
    return False


def dup(report, pairs, label):
    """pairs: [(id, where)]；重复 ID → DUPLICATE_ID（msg 注明首次出现位置）。"""
    seen = {}
    for value, where in pairs:
        if not nonempty(value):
            continue
        if value in seen:
            report.add("DUPLICATE_ID", where,
                       "%s 重复：%s（首次出现在 %s）" % (label, value, seen[value]))
        else:
            seen[value] = where


def scan_assumptions(doc, rel) -> list:
    """深度扫描 [假设] 前缀（契约 §4.2：--final 义务 = zero [假设]）。

    判定与 viewer.py render 同源（值以 `[假设]` 开头即标记）；正文里
    提到该词（如 AC 文本「全部 [假设] 已清除」）不算标记，避免误报。
    """
    hits = []

    def walk(node, path):
        if isinstance(node, dict):
            for key, value in node.items():
                walk(value, "%s.%s" % (path, key) if path else str(key))
        elif isinstance(node, list):
            for i, value in enumerate(node):
                walk(value, "%s[%d]" % (path, i))
        elif isinstance(node, str) and node.startswith("[假设]"):
            hits.append(path)

    walk(doc, "")
    return hits


def tc_declarations(entry, where, report, fh_ids=None):
    """L3 kill-target 纪律（diy-review L3 / diy-test-design Schema）：technique/dimension 枚举
    + kill_target 非空且引用 FH ID（fh_ids 为 None 时退回非空校验——review L3 等旁路调用）。"""
    # rule: diy-review/SKILL.md:L3（every TC bound to the task carries non-empty kill_target
    #       and a technique valid against the test-plan schema enum）
    # rule: diy-test-design/SKILL.md:Final requires（every case carrying a schema-enum technique
    #       and non-empty kill_target）
    enum(report, where + ".technique", entry.get("technique"), TECHNIQUES, "technique")
    kt = entry.get("kill_target")
    if req(report, where + ".kill_target", kt, "kill_target（引用 FH ID）") and fh_ids is not None:
        # rule: diy-test-design/SKILL.md:Schema（kill_target 引用 fault_hypotheses[].id；一杀多允许列表）
        refs = kt if isinstance(kt, list) else [kt]
        for j, ref in enumerate(refs):
            if not (is_str(ref) and ref in fh_ids):
                report.add("UNKNOWN_ID",
                           "%s.kill_target[%d]" % (where, j) if isinstance(kt, list)
                           else where + ".kill_target",
                           "%r 不是 fault_hypotheses 里的 FH ID（须先落 FH 再引）" % (ref,))
    # rule: diy-test-design/SKILL.md:Schema dimension（5 值枚举·一条用例一个轴）
    enum(report, where + ".dimension", entry.get("dimension"), DIMENSIONS, "dimension")
    if entry.get("radius") is not None:
        # rule: diy-test-design/SKILL.md:Schema radius（可选·爆炸半径标注）
        enum(report, where + ".radius", entry.get("radius"), RADII, "radius")


def _api_anchor_ok(anchor) -> bool:
    """api_refs 复合锚三键形状：operationId/path/method 皆非空字符串。"""
    if not isinstance(anchor, dict):
        return False
    return all(is_str(anchor.get(k)) and anchor.get(k).strip()
               for k in ("operationId", "path", "method"))


def _openapi_anchors(docs) -> dict:
    """openapi.yaml → {operationId: (path, method)}；文档缺失/损坏 → {}。

    rule: diy-test-design/SKILL.md:锚定（operationId 即接口唯一身份·复合锚＝
    operationId＋path+method；openapi 缺席时调用方降级 warning 跳过，不加硬门）
    """
    spec = docs.doc("openapi")
    if not isinstance(spec, dict):
        return {}
    out = {}
    for path, item in (spec.get("paths") or {}).items():
        if not isinstance(item, dict):
            continue
        for method, op in item.items():
            if method in PATH_ITEM_KEYS or not isinstance(op, dict):
                continue
            oid = op.get("operationId")
            if is_str(oid) and oid.strip():
                out[oid] = (str(path), method)
    return out


def _anchor_resolves(anchor, anchors) -> bool:
    """复合锚可解析：operationId 在场且 (path, method) 与 openapi 一致。"""
    hit = anchors.get(anchor.get("operationId"))
    return hit is not None and hit == (anchor.get("path"), anchor.get("method"))


def _done_acs(docs) -> set:
    """已完成故事的 AC id 集合（五轴 audit 与接口门豁免口径同 ≥1 TC 豁免）。"""
    stories = docs.doc("stories")
    return {a.get("id") for s in items(stories, "stories", of_type=dict)
            if s.get("status") == "已完成"
            for a in items(s, "acceptance_criteria", of_type=dict)
            if is_str(a.get("id"))}


def _fh_matches_ac(hid, ac_id) -> bool:
    """FH-x.y.z 的 x.y 与 AC-x.y 数字段对应（z 为该 AC 内自由序号）。"""
    def parts(value):
        try:
            return value.split("-", 1)[1].split(".")
        except (AttributeError, IndexError):
            return []
    hp, ap = parts(hid), parts(ac_id)
    return (len(hp) == 3 and len(ap) == 2
            and hp[:2] == ap and all(p.isdigit() for p in hp))
