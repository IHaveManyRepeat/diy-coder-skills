# -*- coding: utf-8 -*-
"""diyc kind —— 扫描目标类型判定。

三阶判据链的第②阶（规则表机械判）由本模块承载；①用户明示照录与
③ambiguous 先问一次留在技能提示词层（spec-scan 01-collect / selfcheck 01-freeze）。

判定依据（2026-10-21 用户裁定下沉引擎，两技能 01 步同文表为唯一来源）：
- 对照表（封闭世界，产物真名以代码为准）：按目标文件 stem / 路径成分精确匹配——
    规格  prd / brief / prfaq / epics / stories / architecture / openapi /
          design / test-plan / spec / spec-kernel / story-context /
          change-proposal / project-context；WDS 四产物按真名 wds-trigger /
          wds-scenarios / wds-design-system / wds-brief（表内短名 trigger /
          scenarios / system 不入裸名表——裸名 system 歧义大，表外走③问）。
    技能  SKILL.md（文件）/ steps / templates（路径成分；模板与教学资产）。
    文档  sprint / review / mutation-report / selfcheck / spec-scan /
          investigation / research / retrospective / checkpoint /
          editorial-review / readiness；WDS assets 清单 wds-assets /
          evolution 按真名 wds-evolution。
- 结构判：目录含 SKILL.md → 技能。
- 文件名：basename stem 以 taskbook 开头 → 任务书。

输出 {kind, matched_by, ambiguous}：
- kind ∈ 任务书|技能|规格|文档；判不出或多类冲突 → null（调用方走第③阶先问一次）。
- matched_by 命中依据（对照表|结构判|文件名，多种 '+' 连接；无命中「无命中」；
  冲突「冲突:<kind>(<依据>)…」）。
- ambiguous 布尔：无命中或多类冲突为 true。
纯判定不碰存在性门（表名匹配对不存在的路径同样成立；结构判仅在路径为目录时生效）。
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from diyc_lib import receipt, rel_path  # noqa: E402

KINDS = ("任务书", "技能", "规格", "文档")

# 对照表（stem 小写精确匹配；与两技能 01 步表同源——改表须三处同批）
SPEC_STEMS = frozenset({
    "prd", "brief", "prfaq", "epics", "stories", "architecture", "openapi",
    "design", "test-plan", "spec", "spec-kernel", "story-context",
    "change-proposal", "project-context",
    "wds-trigger", "wds-scenarios", "wds-design-system", "wds-brief",
})
DOC_STEMS = frozenset({
    "sprint", "review", "mutation-report", "selfcheck", "spec-scan",
    "investigation", "research", "retrospective", "checkpoint",
    "editorial-review", "readiness",
    "wds-assets", "wds-evolution",
})
SKILL_FILE = "SKILL.md"
SKILL_PATH_TOKENS = frozenset({"steps", "templates"})
TASKBOOK_PREFIX = "taskbook"


def classify(target: str) -> dict:
    """判定 target（文件或目录路径）→ {kind, matched_by, ambiguous}。"""
    path = os.path.normpath(str(target)).replace("\\", "/")
    base = path.rstrip("/").rsplit("/", 1)[-1]
    stem = base
    if "." in base and not base.startswith("."):
        stem = base.rsplit(".", 1)[0]
    low = stem.lower()
    hits = []  # 保序 (kind, basis)

    def add(kind, basis):
        if (kind, basis) not in hits:
            hits.append((kind, basis))

    # 文件名：taskbook* → 任务书
    if low.startswith(TASKBOOK_PREFIX):
        add("任务书", "文件名")
    # 对照表：文件 stem + 路径成分（steps / templates 归技能）
    if base == SKILL_FILE:
        add("技能", "对照表")
    if low in SPEC_STEMS:
        add("规格", "对照表")
    if low in DOC_STEMS:
        add("文档", "对照表")
    for comp in path.split("/"):
        if comp.lower() in SKILL_PATH_TOKENS:
            add("技能", "对照表")
    # 结构判：目录含 SKILL.md → 技能
    if os.path.isdir(target) and os.path.isfile(os.path.join(target, SKILL_FILE)):
        add("技能", "结构判")

    kinds = []
    for kind, _ in hits:
        if kind not in kinds:
            kinds.append(kind)
    if not kinds:
        return {"kind": None, "matched_by": "无命中", "ambiguous": True}
    if len(kinds) > 1:
        detail = "+".join("%s(%s)" % (k, b) for k, b in hits)
        return {"kind": None, "matched_by": "冲突:" + detail, "ambiguous": True}
    bases = "+".join(b for _, b in hits)
    return {"kind": kinds[0], "matched_by": bases, "ambiguous": False}


def run(args) -> dict:
    """kind 入口（args 由 diyc.py 收口；相对 target 按 project-root 解析）。"""
    target = args.target
    if not os.path.isabs(target):
        target = os.path.join(args.project_root, target)
    verdict = classify(target)
    show = rel_path(os.path.abspath(args.project_root), os.path.abspath(target))
    return receipt("kind", True, target=show, **verdict)
