# -*- coding: utf-8 -*-
"""diyc check 入口与流程级规则（契约 §2/§4.2）。

- run(args) -> dict：文件定位 + 缺席语义 + 类型分派 + --final 的 [假设] 扫描
  + --previous 稳定 ID 集合比对；文档级规则在 diyc_check_docs，sprint/review
  （任务级）与跨文件真值在本文件。
- PENDING_UNCOVERED 只经 Docs.story_covered()（与 W3 reconcile 共用唯一定义源；
  契约 §4.2，禁止二份实现）；缺覆盖语义 = 无 TC 绑定 且（无 gap 条目 或
  decision == '待办'），已豁免 与 接受缺口 均豁免（team-lead 2026-09-13 裁定）。
- 跨文件真值（always-on，BUG-012 机制化）：已完成任务 → stories.yaml 的 story 必须
  已完成、test-plan.yaml 的 TC 必须通过；待审查/已完成 任务台账 → evidence 齐备且
  red/green 非空、green 与 TC status 一致（diy-review L3）。
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import diyc_check_docs as d  # noqa: E402
import diyc_lib  # noqa: E402
from diyc_lib import Docs, receipt, rel_path  # noqa: E402
from diyc_lib_base import load_yaml_checked  # noqa: E402
from diyc_check_tasks import _check_previous, check_review, check_sprint  # noqa: E402

TYPE_FILES = {
    "prd": "prd.yaml",
    "architecture": "architecture.yaml",
    "openapi": "openapi.yaml",
    "epics": "epics.yaml",
    "stories": "stories.yaml",
    "test-plan": "test-plan.yaml",
    "sprint": "sprint.yaml",
    "review": "sprint.yaml",   # 契约 §4.2：review 为任务级，落在 sprint.yaml
    "mutation-report": "mutation-report.yaml",   # 纳入 doc-check 注册面
}


def _done(report, counts) -> dict:
    return receipt("check", not report.violations, violations=report.violations,
                   warnings=report.warnings, counts=counts)


# ---------------------------------------------------------------- 入口

def run(args) -> dict:
    """check 入口（契约 §2：args 由 diyc.py 收口，output_dir 已解析）。"""
    typ = args.type
    root = args.project_root
    out_dir = getattr(args, "output_dir", None)
    report = d.Report()
    if not out_dir:
        out_dir = os.path.join(root, diyc_lib.DEFAULT_OUTPUT_DIR)
        report.warn("args.output_dir 缺失（diyc.py 未收口），按默认 %s 处理"
                    % diyc_lib.DEFAULT_OUTPUT_DIR)
    final = bool(getattr(args, "final", False))
    story_filter = getattr(args, "story", None)
    filename = TYPE_FILES[typ]
    path = os.path.join(out_dir, filename)
    rel = rel_path(root, path)

    if not os.path.isfile(path):
        # rule: 契约 §4.2 缺席语义（openapi 缺席 = 可选文档合法跳过；其余 MISSING_FILE）
        if typ == "openapi":
            report.warn("openapi.yaml 不存在——本项目无可选接口文档，合法跳过")
            return _done(report, {})
        report.add("MISSING_FILE", rel, "%s 不存在" % filename)
        return _done(report, {})

    doc, dup_code, err = load_yaml_checked(path)
    if err:
        # DUPLICATE_KEY 与 UNPARSABLE_YAML 区分（重复键≠解析失败）
        report.add(dup_code, rel, "YAML %s：%s"
                   % ("重复键" if dup_code == "DUPLICATE_KEY" else "解析失败", err))
        return _done(report, {})
    if not isinstance(doc, dict):
        report.add("UNPARSABLE_YAML", rel, "顶层不是映射（实际 %s）" % type(doc).__name__)
        return _done(report, {})

    docs = Docs(root, out_dir)
    # 全类型通用 project 时间键格式断言（两格式兼容＋防忘跑 stamp）
    d.check_project_times(doc, rel, report)
    if typ in d.CHECKERS:
        counts = d.CHECKERS[typ](doc, rel, docs, final, report)
    elif typ == "sprint":
        counts = check_sprint(doc, rel, docs, story_filter, final, report)
    else:  # review
        counts = check_review(doc, rel, docs, story_filter, report)

    if final:
        # rule: diy-prd/architecture/openapi/epics-stories/test-plan/sprint SKILL.md:
        #       Final requires（zero [假设]）——全类型统一深度扫描
        for loc in d.scan_assumptions(doc, rel):
            report.add("ASSUMPTION_PRESENT", "%s %s" % (rel, loc),
                       "[假设] 未清除（定稿前须用户确认并去除前缀）")

    previous = getattr(args, "previous", None)
    if previous:
        _check_previous(typ, doc, previous, rel, root, report)

    return _done(report, counts)
