# -*- coding: utf-8 -*-
"""diyc check 文档级规则：prd / architecture / openapi / epics / stories / test-plan。

规则逐条读取对应 SKILL.md 的 Schema、Discipline 与 Final requires 原文对齐，
每条附 `# rule: <skill>/SKILL.md:<条款>` 注释；跨文档引用解析只经 diyc_lib.Docs
（契约 §5，禁止旁路读文件）。入口 run() 在 diyc_check.py；本模块 check_* 纯函数
就地追加违规并返回 counts（契约 §4.2）。另持枚举面一致性：跨技能枚举常量
的出现面清单封闭登记，逐面提取与常量断言集合相等，经通用门 check_project_times 挂载。

裁量声明（已在回报中报 team-lead）：
- 跨文档 UNKNOWN_ID 限于 team-lead 裁定的三条真链路（architecture.affects /
  openapi x-fr / stories refs）+ 契约钉住的 stories design_ref；
  epics.feature_refs、stories.epic 属同类链路但不在本次裁定范围，暂不查。
- **第四条真链路**：architecture.affects 的解析域
  在主线 FR/NFR 之外并入 WDS 线的 SC-<nn> / SC-<nn>.P<n>（源 wds-scenarios.yaml），
  使 WDS 线决策不被终门误拒；其余类型不扩散。
- prd open_questions 未答（answer 为空）在 --final 计 PENDING_DECISION。
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from diyc_check_docs_lib import (CASE_TYPES, DEC_STATUSES, DIMENSIONS, EPIC_STATUSES,
                                 FR_PRIORITIES, GAP_DECISIONS, HTTP_METHODS, PRIORITIES,
                                 RADII, STACK_KINDS, STORY_STATUSES, TC_STATUSES,
                                 TECHNIQUES, Report, dup, enum, is_str, nonempty,
                                 req, scan_assumptions, tc_declarations)  # noqa: E402
from diyc_check_docs_lib import check_project_times as _check_project_times  # noqa: E402
from diyc_check_docs_stories import check_stories  # noqa: E402
from diyc_check_docs_testplan import check_test_plan  # noqa: E402
from diyc_check_docs_upstream import (check_architecture, check_epics,
                                      check_openapi, check_prd)  # noqa: E402
from diyc_lib import items, is_int  # noqa: E402


# ------------------------------------------------- 枚举面一致性
# 封闭世界：每个跨技能枚举登记「出现面」，逐面提取枚举文本与常量断言集合相等；
# 漂移（面值 ≠ 常量）/ 缺值 / 清单外新面私加 = SET_MISMATCH。方案 A 未开工，此为兜底关卡。
# 面形态（rel 相对 skills 根，正斜杠）：
#   ("pipe", key)           行首 `key:` 的 `|` 分隔值表——每行集合都须 == 常量
#   ("pipe_after", ctx, key) 同 pipe，但只取 ctx 之后最近的一条 key 行（同文件多枚举消歧）
#   ("pipe_subset", key)     值表须为常量非空子集（单值/子集指派面，如 e2e 恒值行）
#   ("text", needle)         文件须含 needle（散文句面：四值技法 / kind 四选一句）
#   ("values", needles)      文件须含每个 needle（散记多值面）
def _registry():
    """面清单（集中登记处）；TC_PRODUCERS/KINDS 定义在别的模块，惰性取防循环 import。"""
    from diyc_check_docs_testplan import TC_PRODUCERS
    from diyc_kind import KINDS
    return (
        ("TECHNIQUES", TECHNIQUES, (
            ("diy-test-design/SKILL.md", ("pipe", "technique")),
            ("diy-e2e-tests/SKILL.md", ("pipe_subset", "technique")),
            ("diy-augment/SKILL.md",
             ("values", ("覆盖分支", "MC-DC 覆盖", "白盒路径", "变异杀伤"))),
        )),
        ("CASE_TYPES", CASE_TYPES, (
            ("diy-test-design/SKILL.md", ("pipe", "type")),
            ("diy-e2e-tests/SKILL.md", ("pipe_subset", "type")),
        )),
        ("PRIORITIES", PRIORITIES, (
            ("diy-test-design/SKILL.md", ("pipe", "priority")),
            ("diy-e2e-tests/SKILL.md", ("pipe", "priority")),
        )),
        ("TC_STATUSES", TC_STATUSES, (
            ("diy-test-design/SKILL.md", ("pipe", "status")),
            ("diy-e2e-tests/SKILL.md", ("pipe_subset", "status")),
        )),
        ("GAP_DECISIONS", GAP_DECISIONS, (
            ("diy-test-design/SKILL.md", ("pipe", "decision")),
        )),
        ("DIMENSIONS", DIMENSIONS, (
            ("diy-test-design/SKILL.md", ("pipe", "dimension")),
            ("diy-test-design/SKILL.md", ("pipe", "axis")),
            ("diy-e2e-tests/SKILL.md", ("pipe", "dimension")),
        )),
        ("RADII", RADII, (
            ("diy-test-design/SKILL.md", ("pipe", "radius")),
            ("diy-review/SKILL.md", ("pipe", "radius")),
            ("diy-review/SKILL.md", ("text", "局部 / 模块 / 跨模块 / 系统 / 外部")),
        )),
        ("FR_PRIORITIES", FR_PRIORITIES, (
            ("diy-prd/SKILL.md", ("pipe", "priority")),
        )),
        ("DEC_STATUSES", DEC_STATUSES, (
            ("diy-architecture/SKILL.md", ("pipe_after", "- id: D-1", "status")),
        )),
        ("STACK_KINDS", STACK_KINDS, (
            ("diy-architecture/SKILL.md", ("pipe", "kind")),
        )),
        ("EPIC_STATUSES", EPIC_STATUSES, (
            ("diy-epics-stories/SKILL.md", ("pipe_after", "- id: E-1", "status")),
        )),
        ("STORY_STATUSES", STORY_STATUSES, (
            ("diy-epics-stories/SKILL.md", ("pipe_after", "- id: S-1", "status")),
            ("diy-sprint/SKILL.md", ("pipe_after", "- story: S-1", "status")),
        )),
        ("TC_PRODUCERS", TC_PRODUCERS, (
            ("diy-test-design/SKILL.md", ("text", "producer: test-design")),
            ("diy-augment/SKILL.md", ("text", "producer: augment")),
            ("diy-e2e-tests/SKILL.md", ("text", "producer: e2e")),
        )),
        ("KINDS", KINDS, (
            ("diy-spec-scan/steps/01-collect.md", ("text", "任务书 | 技能 | 规格 | 文档")),
            ("diy-selfcheck/steps/01-freeze.md", ("text", "任务书 | 技能 | 规格 | 文档")),
        )),
    )


# 封闭世界扫掠键：键名在库内近独有（或值域可辨——同名键族如 status 不扫，
# 各自走面断言）。命中判据＝行值表与常量**相交**（research 的 dimension 市场|技术|领域
# 与五轴不相交，不误报）；membership 键＝按成员判（producer 标量行）。
_ENUM_SWEEP_KEYS = {
    "radius": ("RADII",),
    "technique": ("TECHNIQUES",),
    "type": ("CASE_TYPES",),
    "priority": ("PRIORITIES", "FR_PRIORITIES"),
    "decision": ("GAP_DECISIONS",),
    "dimension": ("DIMENSIONS",),
    "kind": ("STACK_KINDS",),
    "producer": ("TC_PRODUCERS",),
}
_ENUM_MEMBERSHIP_SWEEP = frozenset({"producer"})

_MD_CACHE = {}


def _md_texts(root):
    """skills 根下全部 *.md → {rel: text}；进程内缓存（CLI 单进程，安装面只读）。"""
    key = os.path.abspath(root)
    hit = _MD_CACHE.get(key)
    if hit is None:
        hit = {}
        for dirpath, _dirs, files in os.walk(key):
            for fn in files:
                if not fn.endswith(".md"):
                    continue
                full = os.path.join(dirpath, fn)
                rel = os.path.relpath(full, key).replace(os.sep, "/")
                try:
                    with open(full, encoding="utf-8") as fh:
                        hit[rel] = fh.read()
                except (OSError, UnicodeDecodeError):
                    continue
        _MD_CACHE[key] = hit
    return hit


def _pipe_sets(text, key):
    """行首 `key:` 值表 → [frozenset]（`|`/`｜` 分隔、剥 `#` 注释与空白）。"""
    pat = re.compile(r"^\s*%s:\s*(.+?)\s*$" % re.escape(key))
    out = []
    for line in text.splitlines():
        m = pat.match(line)
        if not m:
            continue
        raw = m.group(1).split("#", 1)[0]
        parts = [p.strip() for p in re.split(r"[|｜]", raw) if p.strip()]
        if parts:
            out.append(frozenset(parts))
    return out


def _pipe_set_after(text, context, key):
    """context 之后最近的一条 key 值表（同文件多枚举消歧）；无 → None。"""
    idx = text.find(context)
    if idx < 0:
        return None
    sets = _pipe_sets(text[idx + len(context):], key)
    return sets[0] if sets else None


def _covered_files(reg, name):
    return {rel for n, _v, faces in reg if n == name for rel, _s in faces}


def check_enum_faces(report, skills_root=None, registry=None, sweep_keys=None):
    """逐面提取枚举文本与常量断言集合相等（封闭世界·漂移/缺值/新面私加=红）。

    skills_root 缺省＝本脚本旁的 skills 安装根（仓库与安装布局同构）；
    registry/sweep_keys 供测试注入迷你世界。
    """
    root = skills_root or os.path.abspath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
    reg = registry if registry is not None else _registry()
    sw = sweep_keys if sweep_keys is not None else _ENUM_SWEEP_KEYS
    values_by_name = {name: set(values) for name, values, _f in reg}
    texts = _md_texts(root)
    for name, values, faces in reg:
        want = set(values)
        for rel, spec in faces:
            where = "skills/%s" % rel
            text = texts.get(rel)
            if text is None:
                report.add("SET_MISMATCH", where,
                           "%s 面文件缺席（面清单登记在案）" % name)
                continue
            mode = spec[0]
            if mode == "pipe":
                sets = _pipe_sets(text, spec[1])
                if not sets:
                    report.add("SET_MISMATCH", "%s %s" % (where, spec[1]),
                               "%s 面值表缺席（键 %s 无行首定义）" % (name, spec[1]))
                for got in sets:
                    if got != want:
                        report.add("SET_MISMATCH", "%s %s" % (where, spec[1]),
                                   "%s 面值表与常量不一致：面 {%s} vs 常量 {%s}"
                                   % (name, "|".join(sorted(got)),
                                      "|".join(sorted(want))))
            elif mode == "pipe_after":
                got = _pipe_set_after(text, spec[1], spec[2])
                if got is None:
                    report.add("SET_MISMATCH", "%s %s" % (where, spec[2]),
                               "%s 面值表缺席（锚 %r 之后无 %s 行）"
                               % (name, spec[1], spec[2]))
                elif got != want:
                    report.add("SET_MISMATCH", "%s %s" % (where, spec[2]),
                               "%s 面值表与常量不一致：面 {%s} vs 常量 {%s}"
                               % (name, "|".join(sorted(got)),
                                  "|".join(sorted(want))))
            elif mode == "pipe_subset":
                sets = _pipe_sets(text, spec[1])
                if not sets:
                    report.add("SET_MISMATCH", "%s %s" % (where, spec[1]),
                               "%s 面值表缺席（键 %s 无行首定义）" % (name, spec[1]))
                for got in sets:
                    if not got <= want:
                        report.add("SET_MISMATCH", "%s %s" % (where, spec[1]),
                                   "%s 面值表超出常量域：面 {%s} ⊄ {%s}"
                                   % (name, "|".join(sorted(got)),
                                      "|".join(sorted(want))))
            elif mode == "text":
                if spec[1] not in text:
                    report.add("SET_MISMATCH", where,
                               "%s 面缺枚举句 %r（漂移或面被改写）" % (name, spec[1]))
            elif mode == "values":
                for needle in spec[1]:
                    if needle not in text:
                        report.add("SET_MISMATCH", where,
                                   "%s 面缺枚举值 %r（漂移或面被改写）" % (name, needle))
    # 封闭世界扫掠：清单外的面出现该枚举 = 新面私加
    for key, names in sw.items():
        membership = key in _ENUM_MEMBERSHIP_SWEEP
        for rel, text in texts.items():
            for line in text.splitlines():
                m = re.match(r"^\s*%s:\s*(.+?)\s*$" % re.escape(key), line)
                if not m:
                    continue
                raw = m.group(1).split("#", 1)[0]
                parts = [p.strip() for p in re.split(r"[|｜]", raw) if p.strip()]
                if not parts:
                    continue
                got = frozenset(parts)
                for name in names:
                    want = values_by_name[name]
                    if membership:
                        bad = (rel not in _covered_files(reg, name)) or not got <= want
                    else:
                        bad = (rel not in _covered_files(reg, name)) and bool(got & want)
                    if bad:
                        report.add("SET_MISMATCH", "skills/%s" % rel,
                                   "清单外出现 %s 枚举（%s 值表 {%s}）——新面须先登记面清单"
                                   % (name, key, "|".join(sorted(got))))
                        break


def check_project_times(doc, rel, report):
    """全类型通用门（diyc_check.run 每类型必经）：
    ① 枚举面一致性（封闭世界回查）② project 时间键格式（lib）。"""
    check_enum_faces(report)
    return _check_project_times(doc, rel, report)


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
    """mutation-report.yaml —— diy-augment 的变异运行记录。

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
