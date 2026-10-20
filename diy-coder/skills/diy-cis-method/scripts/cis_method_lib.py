# -*- coding: utf-8 -*-
"""diy-cis-method 常量表（产物/枚举/分支键表/可达集/正则）与方法库加载、回执打印、output-dir 取值工具。."""

import csv
import io
import json
import os
import re

import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import display_path, methods_path, nonempty, v, violation_line, warn_line  # noqa: E402

CIS_FILE = "cis-method.yaml"
METHODS_FILE = "cis-methods.csv"
# 表头冻结（§0 裁定 5(a)：6 列，保英文；多出的 `method` 判别列是四库归并的新增列）
LIB_COLUMNS = ("method", "category", "name", "slug", "description", "prompts")

METHOD_ENUM = ("创新策略", "问题求解", "设计思维", "叙事")
STATUS_ENUM = ("草稿", "进行中", "已完成")
ASSUMPTION_MARK = "[假设]"

# 分支步数（源侧 workflow 的 step 数）与 `已完成` 的 current_step 域
BRANCH_STEPS = {"创新策略": 9, "问题求解": 9, "设计思维": 7, "叙事": 10}
# 问题求解源侧第 9 步 `optional="true"`：跳过时第 8 步收尾（源侧「optional 缺省则终结指令前移」）
COMPLETED_STEPS = {"创新策略": (9,), "问题求解": (8, 9), "设计思维": (7,), "叙事": (10,)}

# 注入项：不由任何 step 产出、而由模板首部或运行环境注入的占位符（四项，一律不入必填表）
INJECTION_KEYS = ("date", "user_name", "agent_role", "agent_name")

# 分支必填键表：每分支 = 每个源 step 的第一个「非注入」<template-output> 键（9+9+7+9 = 34）
STEP_KEYS = {
    "创新策略": ("company_name", "market_landscape", "current_business_model",
                 "disruption_vectors", "innovation_initiatives", "option_a_name",
                 "recommended_strategy", "phase_1", "leading_indicators"),
    "问题求解": ("problem_title", "problem_boundaries", "root_cause_analysis",
                 "driving_forces", "solution_methods", "evaluation_criteria",
                 "implementation_approach", "success_metrics", "key_learnings"),
    "设计思维": ("design_challenge", "user_insights", "pov_statement", "ideation_methods",
                 "prototype_approach", "testing_plan", "refinements"),
    # 第 10 步的唯一标签 `agent_role, agent_name, user_name, date` 全是注入项 → 该步无实键
    "叙事": ("story_purpose", "story_type", "story_beats", "emotional_arc", "opening_hook",
             "complete_story", "short_version", "best_channels", "resolution"),
}

# 各分支 `deliverable` 合法键全集（源 `template.md` 占位符去注入项）——**只用于「多余键」
# 的 warning**（非封闭集，不阻断）；键名逐字取自源模板，与 W2 分支文件的「本分支结构」节同源。
BRANCH_KEYS = {
    "创新策略": (
        "company_name", "strategic_focus", "current_situation", "strategic_challenge",
        "market_landscape", "competitive_dynamics", "market_opportunities", "market_insights",
        "current_business_model", "value_proposition", "revenue_cost_structure",
        "model_weaknesses", "disruption_vectors", "unmet_jobs", "technology_enablers",
        "strategic_whitespace", "innovation_initiatives", "business_model_innovation",
        "value_chain_opportunities", "partnership_opportunities",
        "option_a_name", "option_a_description", "option_a_pros", "option_a_cons",
        "option_b_name", "option_b_description", "option_b_pros", "option_b_cons",
        "option_c_name", "option_c_description", "option_c_pros", "option_c_cons",
        "recommended_strategy", "key_hypotheses", "success_factors",
        "phase_1", "phase_2", "phase_3",
        "leading_indicators", "lagging_indicators", "decision_gates",
        "key_risks", "risk_mitigation"),
    "问题求解": (
        "problem_title", "problem_category", "initial_problem", "refined_problem_statement",
        "problem_context", "success_criteria", "problem_boundaries", "root_cause_analysis",
        "contributing_factors", "system_dynamics", "driving_forces", "restraining_forces",
        "constraints", "key_insights", "solution_methods", "generated_solutions",
        "creative_alternatives", "evaluation_criteria", "solution_analysis",
        "recommended_solution", "solution_rationale", "implementation_approach",
        "action_steps", "timeline", "resources_needed", "responsible_parties",
        "success_metrics", "validation_plan", "risk_mitigation", "adjustment_triggers",
        "key_learnings", "what_worked", "what_to_avoid"),
    "设计思维": (
        "project_name", "design_challenge", "challenge_statement", "user_insights",
        "key_observations", "empathy_map", "pov_statement", "hmw_questions",
        "problem_insights", "ideation_methods", "generated_ideas", "top_concepts",
        "prototype_approach", "prototype_description", "features_to_test", "testing_plan",
        "user_feedback", "key_learnings", "refinements", "action_items", "success_metrics"),
    "叙事": (
        "story_type", "framework_name", "story_purpose", "target_audience", "opening_hook",
        "core_narrative", "story_beats", "emotional_arc", "resolution", "complete_story",
        "character_voice", "conflict_tension", "transformation", "emotional_touchpoints",
        "key_messages", "short_version", "medium_version", "extended_version",
        "best_channels", "audience_considerations", "tone_notes", "adaptation_suggestions",
        "refinement_opportunities", "additional_versions", "feedback_plan"),
}

# 23 个冻结中文类名（§0 裁定 5(d)：三工位逐字一致；同名跨分支由 method 列消歧）
CATEGORY_ENUM = {
    "创新策略": ("市场分析", "商业模式", "颠覆", "战略", "价值链", "技术"),
    "问题求解": ("诊断", "分析", "综合", "评估", "实施", "创意"),
    "设计思维": ("共情", "定义", "构思", "原型", "测试", "落地"),
    "叙事": ("转变", "战略", "说服", "分析", "情感"),
}

# 可达集：源侧工作流实际接入的类别（保真照搬；叙事 = 源侧缺陷修复后按类呈现全部 25 条）
REACHABLE_CATEGORIES = {
    "创新策略": ("市场分析", "商业模式", "颠覆", "战略", "价值链"),
    "问题求解": ("诊断", "分析", "综合", "评估", "实施", "创意"),
    "设计思维": ("共情", "构思", "原型"),
    "叙事": ("转变", "战略", "说服", "分析", "情感"),
}

CM_RE = re.compile(r"CM-(\d{3})\Z")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}\Z")

# ---------------------------------------------------------------- 方法库

def load_methods(project_root):
    """加载方法库 → (rows | None, violations)。行结构 = LIB_COLUMNS 六列。

    表头须逐字等于冻结表头（缺列 / 列名不符 / 改序 → `UNPARSABLE_YAML`，msg 点名）；
    每行的 `method` 与 `category` 逐行核对冻结枚举（跨工位漂移在此暴露）；
    `slug` 仅叙事分支填（源 `story-types.csv` 的 `story_type` 无他处可落，单列承载）。
    """
    path = methods_path(__file__, METHODS_FILE)
    show = display_path(path, project_root)
    if not os.path.isfile(path):
        return None, [v("MISSING_FILE", show, "%s 不存在（技能自带方法库）" % METHODS_FILE)]
    violations = []
    rows = []
    try:
        # utf-8-sig：容忍 Windows 编辑器写入的 BOM（表头冻结不受 BOM 干扰）
        with io.open(path, "r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            header = tuple((name or "").strip() for name in (reader.fieldnames or []))
            if header != LIB_COLUMNS:
                return None, [v("UNPARSABLE_YAML", show,
                                "方法库表头不符：实为 %s（须逐字为 %s）"
                                % ("|".join(header) or "空", "|".join(LIB_COLUMNS)))]
            for index, raw in enumerate(reader):
                item = {key: (raw.get(key) or "").strip() for key in LIB_COLUMNS}
                where = "%s 第 %d 行" % (show, index + 2)
                method = item["method"]
                if method not in METHOD_ENUM:
                    violations.append(v("ENUM_INVALID", where + " method",
                                        "method 越界：%s（合法集 %s）"
                                        % (method or "空", "|".join(METHOD_ENUM))))
                    continue
                if item["category"] not in CATEGORY_ENUM[method]:
                    violations.append(v("ENUM_INVALID", where + " category",
                                        "category 越界：%s（%s 的冻结类名 %s）"
                                        % (item["category"] or "空", method,
                                           "|".join(CATEGORY_ENUM[method]))))
                    continue
                empty = [key for key in LIB_COLUMNS if key != "slug" and not item[key]]
                if empty:
                    violations.append(v("EMPTY_FIELD", where,
                                        "方法条目缺 %s" % "|".join(empty)))
                    continue
                if method == "叙事" and not item["slug"]:
                    violations.append(v("EMPTY_FIELD", where + " slug",
                                        "叙事分支的 slug（源 story_type）不得为空"))
                    continue
                rows.append(item)
    except (csv.Error, OSError, UnicodeDecodeError) as e:
        return None, [v("UNPARSABLE_YAML", show, "方法库解析失败：%s" % e)]
    if violations:
        return None, violations
    if not rows:
        return None, [v("EMPTY_FIELD", show, "方法库无数据行")]
    return rows, []

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

def out_dir_or_violation(payload, args, command):
    """只读子命令的 --output-dir：可省（§2.2），读产物的子命令省了须明确报缺。"""
    if nonempty(args.output_dir):
        return os.path.abspath(args.output_dir), None
    return None, v("EMPTY_FIELD", "--output-dir",
                   "%s 需读 %s，须给 --output-dir（取值由 `diyc.py resolve` 回执给；"
                   "引擎不设默认、不私读 diy-coder.yaml）" % (command, CIS_FILE))
