# -*- coding: utf-8 -*-
"""diyc check 文档级规则：prd / architecture / openapi / epics / stories / test-plan。

规则逐条读取对应 SKILL.md 的 Schema、Discipline 与 Final requires 原文对齐，
每条附 `# rule: <skill>/SKILL.md:<条款>` 注释；跨文档引用解析只经 diyc_lib.Docs
（契约 §5，禁止旁路读文件）。入口 run() 在 diyc_check.py；本模块 check_* 纯函数
就地追加违规并返回 counts（契约 §4.2）。

裁量声明（已在回报中报 team-lead）：
- 跨文档 UNKNOWN_ID 限于 team-lead 裁定的三条真链路（architecture.affects /
  openapi x-fr / stories refs）+ 契约钉住的 stories design_ref；
  epics.feature_refs、stories.epic 属同类链路但不在本次裁定范围，暂不查。
- **第四条真链路（C·3a 裁定 22，2026-09-28）**：architecture.affects 的解析域
  在主线 FR/NFR 之外并入 WDS 线的 SC-<nn> / SC-<nn>.P<n>（源 wds-scenarios.yaml），
  使 WDS 线决策不被终门误拒；其余类型不扩散。
- prd open_questions 未答（answer 为空）在 --final 计 PENDING_DECISION。
"""
# trace: 2026-09-13 批次 3（统一脚本化）——文档级规则，契约 §4.2

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from diyc_check_docs_lib import (HTTP_METHODS, RADII, STORY_STATUSES, Report,
                                 check_project_times, dup, enum, is_str, nonempty,
                                 req, scan_assumptions, tc_declarations)  # noqa: E402
from diyc_check_docs_stories import check_stories  # noqa: E402
from diyc_check_docs_testplan import check_test_plan  # noqa: E402
from diyc_check_docs_upstream import (check_architecture, check_epics,
                                      check_openapi, check_prd)  # noqa: E402
from diyc_lib import items, is_int  # noqa: E402


# ---------------------------------------------------------------- mutation-report

def _tally(report, spot, block):
    """一组 killed / total / score：值域 + **保守口径**自洽。

    保守口径 ＝ `score == round(killed / total × 100)`，候选等价体仍留在分母——
    裁定分由 gate 用 `waivers` 里的 `mutant:` 条目重算，本文件永远记保守值。
    """
    killed, total, score = block.get("killed"), block.get("total"), block.get("score")
    for name, value in (("killed", killed), ("total", total)):
        if not is_int(value) or value < 0:
            report.add("TYPE_INVALID", "%s.%s" % (spot, name), "%s 须为非负整数" % name)
    if is_int(total) and total <= 0:
        report.add("ENUM_INVALID", spot + ".total", "total 须为正整数（分母不可为 0）")
    if not is_int(score):
        report.add("TYPE_INVALID", spot + ".score", "score 须为整数百分数（0–100）")
        return
    if is_int(killed) and is_int(total) and total > 0:
        want = round(killed / total * 100)
        if score != want:
            report.add("SET_MISMATCH", spot + ".score",
                       "score 与保守口径不符：声明 %s，按 killed/total 重算 %s"
                       "（候选等价体仍留在分母；裁定分由 gate 重算）" % (score, want))


def check_mutation_report(doc, rel, docs, final, report) -> dict:
    """mutation-report.yaml —— diy-augment 的变异运行记录（C·9 纳入注册面）。

    rule: diy-augment/SKILL.md:结构（Schema）。是套件里唯一由补测技能产、
    此前无校验器的产物——schema 漂移（score 口径、critical 形状）无人拦截。
    """
    counts = {"runs": 0, "survivors": 0, "equivalents": 0, "critical_runs": 0}
    project = doc.get("project")
    if not isinstance(project, dict):
        report.add("EMPTY_FIELD", rel + " project", "project 块缺失或形状异常")
    else:
        enum(report, rel + " project.status", project.get("status"),
             ("草稿", "已定稿"), "project.status")
    runs = items(doc, "runs", of_type=dict)
    if not runs:
        report.add("EMPTY_FIELD", rel + " runs",
                   "runs 缺失或为空——本产物只在真跑过变异时写")
    for i, run in enumerate(runs):
        w = "%s runs[%d]" % (rel, i)
        if not isinstance(run, dict):
            report.add("TYPE_INVALID", w, "run 须为映射")
            continue
        counts["runs"] += 1
        req(report, w + ".date", run.get("date"), "date")
        req(report, w + ".task", run.get("task"), "task")
        _tally(report, w, run)
        critical = run.get("critical")
        if critical is not None:
            if not isinstance(critical, dict):
                report.add("TYPE_INVALID", w + ".critical",
                           "critical 须为映射（本任务无关键路径文件时省略该键，不写空块）")
            else:
                counts["critical_runs"] += 1
                _tally(report, w + ".critical", critical)
        for s in items(run, "survivors", of_type=dict):
            counts["survivors"] += 1
            if not isinstance(s, dict):
                report.add("TYPE_INVALID", w + " survivors[]", "survivor 须为映射")
                continue
            sw = "%s survivors[%s]" % (w, s.get("mutant") or "?")
            req(report, sw + ".mutant", s.get("mutant"), "mutant")
            req(report, sw + ".file", s.get("file"), "file")
        for e in items(run, "equivalents", of_type=dict):
            counts["equivalents"] += 1
            if not isinstance(e, dict):
                report.add("TYPE_INVALID", w + " equivalents[]", "equivalent 须为映射")
                continue
            ew = "%s equivalents[%s]" % (w, e.get("mutant") or "?")
            req(report, ew + ".mutant", e.get("mutant"), "mutant")
            req(report, ew + ".reason", e.get("reason"), "reason")
    return counts


# 入口分派由 diyc_check.run() 持有；本模块只暴露 check_* 纯函数
CHECKERS = {
    "prd": check_prd,
    "architecture": check_architecture,
    "openapi": check_openapi,
    "epics": check_epics,
    "stories": check_stories,
    "test-plan": check_test_plan,
    "mutation-report": check_mutation_report,
}
