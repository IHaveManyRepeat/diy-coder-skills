# -*- coding: utf-8 -*-
"""diy-editorial-review 台账校验件：顶层结构/ID 形态/序号连续/两槽 findings/单条 review 全量校验与回执计数。."""

import os
import re

import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import is_int, nonempty, v, walk_strings  # noqa: E402

from editorial_review_text import ASSUMPTION, CATEGORIES, LENGTH_TARGETS, LENSES, PROJECT_KEYS, READER_TYPES, REVIEW_ID_RE, SLOTS, STATUSES, STRUCTURE_MODELS  # noqa: E402

# ---------------------------------------------------------------- check：台账校验

# trace: B4 diy-editorial-review check（顶层结构：project 三键 + reviews + revisions）
def check_top_level(data, show):
    violations = []
    project = data.get("project")
    if not isinstance(project, dict):
        violations.append(v("EMPTY_FIELD", show + " project",
                            "project 缺失或不是映射（须含 name/created/updated）"))
    else:
        for key in PROJECT_KEYS:
            if not nonempty(project.get(key)):
                violations.append(v("EMPTY_FIELD", "%s project.%s" % (show, key),
                                    "project.%s 缺失" % key))
    for key in ("reviews", "revisions"):
        if key not in data:
            violations.append(v("EMPTY_FIELD", "%s %s" % (show, key),
                                "%s 缺失（无内容写空列表）" % key))
        elif not isinstance(data.get(key), list):
            violations.append(v("EMPTY_FIELD", "%s %s" % (show, key),
                                "%s 不是列表" % key))
    return violations

# trace: B4 diy-editorial-review check（reviews[].id 形态 ER-### 与全局唯一）
def check_review_id(rid, where, seen):
    if not nonempty(rid):
        return [v("EMPTY_FIELD", where, "id 缺失（须为 ER-###）")]
    text = str(rid)
    if not REVIEW_ID_RE.fullmatch(text):
        return [v("ENUM_INVALID", where, "id 须为 ER-###（三位零填充），实为 %s" % text)]
    if text in seen:
        return [v("DUPLICATE_ID", where, "review ID %s 重复（ID 稳定不重用）" % text)]
    seen.add(text)
    return []

# trace: B4 diy-editorial-review check（target 基准：project-root 相对 + 正斜杠 + 无 `path:` 前缀）
def target_form_error(value):
    text = str(value)
    if os.path.isabs(text) or re.match(r"^[A-Za-z]:[\\/]", text):
        return "target 须为 project-root 相对路径，不得用绝对路径：%s" % text
    if "\\" in text:
        return "target 须用正斜杠（基准 = project-root 相对）：%s" % text
    if text.startswith("path:"):
        return "target 不得带 `path:` 前缀（就是路径本身）：%s" % text
    return None

# trace: B4 diy-editorial-review check（序号取值：YAML 1.1 的裸键 `no` 被 PyYAML 解析成布尔 False，两形同读）
def seq_no(finding):
    if not isinstance(finding, dict):
        return None
    if "no" in finding:
        return finding["no"]
    return finding.get(False)

# trace: B4 diy-editorial-review check（findings 记录内序号：自 1 起连续、不重号、不跳号）
def check_sequence(findings, where, label):
    violations = []
    seen = []
    for i, finding in enumerate(findings):
        if not isinstance(finding, dict):
            violations.append(v("EMPTY_FIELD", "%s[%d]" % (where, i),
                                "%s 不是映射" % label))
            continue
        no = seq_no(finding)
        nw = "%s[%d].no" % (where, i)
        if no is None:
            violations.append(v("EMPTY_FIELD", nw, "%s 的 no 缺失（自 1 起连续）" % label))
        elif not is_int(no):
            violations.append(v("ENUM_INVALID", nw, "no 须为正整数，实为 %r" % (no,)))
        elif no < 1:
            violations.append(v("ENUM_INVALID", nw, "no 须自 1 起，实为 %d" % no))
        elif no in seen:
            violations.append(v("DUPLICATE_ID", nw, "no 重复：%d（记录内序号不重用）" % no))
        else:
            seen.append(no)
    missing = [n for n in range(1, (max(seen) if seen else 0) + 1) if n not in seen]
    if missing:
        violations.append(v("SET_MISMATCH", where,
                            "%s 的 no 不连续，缺 %s（跳号会让「第几条建议」失去定位）"
                            % (label, "、".join(str(n) for n in missing))))
    return violations

# trace: B4 diy-editorial-review check（structure.findings[]：六分类 / 章节名 / 理由 / 影响词数）
def check_structure_findings(where, findings):
    violations = check_sequence(findings, where, "structure.findings")
    for i, finding in enumerate(findings):
        if not isinstance(finding, dict):
            continue
        fw = "%s[%d]" % (where, i)
        label = "structure.findings[%d]（no=%s）" % (i, seq_no(finding))
        category = finding.get("category")
        if not nonempty(category):
            violations.append(v("EMPTY_FIELD", fw + ".category",
                                "%s 的 category 缺失" % label))
        elif str(category) not in CATEGORIES:
            violations.append(v("ENUM_INVALID", fw + ".category",
                                "%s 的 category 越界：%s（合法集 %s）"
                                % (label, category, "|".join(CATEGORIES))))
        for field in ("target", "rationale"):
            if not nonempty(finding.get(field)):
                violations.append(v("EMPTY_FIELD", "%s.%s" % (fw, field),
                                    "%s 的 %s 为空（章节名与理由缺一不可）" % (label, field)))
        impact = finding.get("impact_words")
        if impact is None:
            violations.append(v("EMPTY_FIELD", fw + ".impact_words",
                                "%s 的 impact_words 缺失（估计改动词数，PRESERVE 记负数）"
                                % label))
        elif not is_int(impact):
            violations.append(v("ENUM_INVALID", fw + ".impact_words",
                                "%s 的 impact_words 须为整数，实为 %r" % (label, impact)))
    return violations

# trace: B4 diy-editorial-review check（prose.findings[]：原文 / 修订 / 说明 / 位置）
def check_prose_findings(where, findings):
    violations = check_sequence(findings, where, "prose.findings")
    for i, finding in enumerate(findings):
        if not isinstance(finding, dict):
            continue
        fw = "%s[%d]" % (where, i)
        label = "prose.findings[%d]（no=%s）" % (i, seq_no(finding))
        for field in ("original", "revised", "changes"):
            if not nonempty(finding.get(field)):
                violations.append(v("EMPTY_FIELD", "%s.%s" % (fw, field),
                                    "%s 的 %s 为空（三列缺一不可）" % (label, field)))
        locations = finding.get("locations")
        if not isinstance(locations, list):
            violations.append(v("EMPTY_FIELD", fw + ".locations",
                                "%s 的 locations 缺失或不是列表（同问题多处合并一条、列位置）"
                                % label))
        else:
            for j, spot in enumerate(locations):
                if not nonempty(spot):
                    violations.append(v("EMPTY_FIELD", "%s.locations[%d]" % (fw, j),
                                        "%s 的 locations[%d] 为空" % (label, j)))
    return violations

# trace: B4 diy-editorial-review check（structure 槽：五模型 / 削减估计 / 达标判断 / --final 对账）
def check_structure_slot(slot, where, final):
    violations = []
    model = slot.get("model")
    if not nonempty(model):
        violations.append(v("EMPTY_FIELD", where + ".model",
                            "model 缺失（五模型之一：%s）" % "|".join(STRUCTURE_MODELS)))
    elif str(model) not in STRUCTURE_MODELS:
        violations.append(v("ENUM_INVALID", where + ".model",
                            "model 越界：%s（合法集 %s）"
                            % (model, "|".join(STRUCTURE_MODELS))))
    findings = slot.get("findings")
    if not isinstance(findings, list):
        violations.append(v("EMPTY_FIELD", where + ".findings",
                            "findings 缺失或不是列表（无建议写空列表）"))
        findings = []
    else:
        violations += check_structure_findings(where + ".findings", findings)
    reduction = slot.get("estimated_reduction_words")
    if reduction is None:
        violations.append(v("EMPTY_FIELD", where + ".estimated_reduction_words",
                            "estimated_reduction_words 缺失（口径 = stats 词数；无建议写 0）"))
    elif not is_int(reduction):
        violations.append(v("ENUM_INVALID", where + ".estimated_reduction_words",
                            "estimated_reduction_words 须为整数，实为 %r" % (reduction,)))
    meets = slot.get("meets_length_target")
    if not nonempty(meets):
        violations.append(v("EMPTY_FIELD", where + ".meets_length_target",
                            "meets_length_target 缺失（是|否|未设目标）"))
    elif str(meets) not in LENGTH_TARGETS:
        violations.append(v("ENUM_INVALID", where + ".meets_length_target",
                            "meets_length_target 越界：%s（合法集 是|否|未设目标）" % meets))
    impacts = [finding.get("impact_words") for finding in findings
               if isinstance(finding, dict)]
    if (final and is_int(reduction) and impacts
            and all(is_int(impact) for impact in impacts)
            and sum(impacts) != reduction):
        violations.append(v("SET_MISMATCH", where + ".estimated_reduction_words",
                            "estimated_reduction_words=%d 与 findings 的 impact_words 之和 %d "
                            "不符（PRESERVE 的负值参与求和）" % (reduction, sum(impacts))))
    return violations

# trace: B4 diy-editorial-review check（lenses 与两槽一致性：声明与在场双向对账 → SET_MISMATCH）
def check_lens_slots(review, where):
    violations = []
    raw = review.get("lenses")
    lenses = []
    if not isinstance(raw, list) or not raw:
        violations.append(v("EMPTY_FIELD", where + ".lenses",
                            "lenses 缺失或为空（至少一个透镜：结构|文风）"))
    else:
        for i, lens in enumerate(raw):
            lw = "%s.lenses[%d]" % (where, i)
            if str(lens) not in LENSES:
                violations.append(v("ENUM_INVALID", lw,
                                    "透镜越界：%s（合法集 结构|文风）" % lens))
            elif str(lens) in lenses:
                violations.append(v("SET_MISMATCH", lw, "透镜重复：%s" % lens))
            else:
                lenses.append(str(lens))
    for lens, slot in SLOTS:
        present = review.get(slot) is not None
        if lens in lenses and not present:
            violations.append(v("SET_MISMATCH", where + "." + slot,
                                "lenses 含 `%s` 但 %s 槽缺席（跑了哪个透镜→对应槽必须在场）"
                                % (lens, slot)))
        if lens not in lenses and present:
            violations.append(v("SET_MISMATCH", where + "." + slot,
                                "%s 槽在场但 lenses 未含 `%s`（槽与声明不一致）"
                                % (slot, lens)))
    return violations, lenses

# trace: B4 diy-editorial-review check（单条 review 全量校验 + --final 义务）
def check_review(index, review, show, root, final, seen_ids):
    where = "%s.reviews[%d]" % (show, index)
    if not isinstance(review, dict):
        return [v("EMPTY_FIELD", where,
                  "review 不是映射（须含 id/target/date/status/lenses/reader_type/"
                  "open_questions）")]
    violations = check_review_id(review.get("id"), where + ".id", seen_ids)
    target = review.get("target")
    if not nonempty(target):
        violations.append(v("EMPTY_FIELD", where + ".target",
                            "target 缺失（被评审文档的 project-root 相对路径）"))
    else:
        form = target_form_error(target)
        if form:
            violations.append(v("ENUM_INVALID", where + ".target", form))
        elif not os.path.isfile(os.path.join(root, str(target))):
            violations.append(v("MISSING_FILE", where + ".target",
                                "target 指向的文档不在场：%s（基准 = project-root 相对）"
                                % target))
    if not nonempty(review.get("date")):
        violations.append(v("EMPTY_FIELD", where + ".date", "date 缺失（本次评审的日子）"))
    status = review.get("status")
    if not nonempty(status):
        violations.append(v("EMPTY_FIELD", where + ".status", "status 缺失（草稿|已定稿）"))
    elif str(status) not in STATUSES:
        violations.append(v("ENUM_INVALID", where + ".status",
                            "status 越界：%s（合法集 草稿|已定稿）" % status))
    lens_violations, lenses = check_lens_slots(review, where)
    violations += lens_violations
    reader = review.get("reader_type")
    if not nonempty(reader):
        violations.append(v("EMPTY_FIELD", where + ".reader_type",
                            "reader_type 缺失（人类|LLM；用户没指定时写 人类）"))
    elif str(reader) not in READER_TYPES:
        violations.append(v("ENUM_INVALID", where + ".reader_type",
                            "reader_type 越界：%s（合法集 人类|LLM）" % reader))
    structure = review.get("structure")
    if structure is not None:
        if not isinstance(structure, dict):
            violations.append(v("EMPTY_FIELD", where + ".structure",
                                "structure 槽不是映射（model/findings/"
                                "estimated_reduction_words/meets_length_target）"))
        elif "结构" in lenses:
            violations += check_structure_slot(structure, where + ".structure", final)
    prose = review.get("prose")
    if prose is not None:
        if not isinstance(prose, dict):
            violations.append(v("EMPTY_FIELD", where + ".prose",
                                "prose 槽不是映射（findings）"))
        elif "文风" in lenses:
            findings = prose.get("findings")
            if not isinstance(findings, list):
                violations.append(v("EMPTY_FIELD", where + ".prose.findings",
                                    "findings 缺失或不是列表（无建议写空列表）"))
            else:
                violations += check_prose_findings(where + ".prose.findings", findings)
    if not isinstance(review.get("open_questions"), list):
        violations.append(v("EMPTY_FIELD", where + ".open_questions",
                            "open_questions 缺失或不是列表（没有未决项写空列表）"))
    if final:
        if nonempty(status) and str(status) != "已定稿":
            violations.append(v("STATUS_MISMATCH", where + ".status",
                                "--final 要求 status: 已定稿，实为 %s" % status))
        if any(ASSUMPTION in s for _p, s in walk_strings(review, "")):
            violations.append(v("ASSUMPTION_PRESENT", where,
                                "--final 要求零 [假设]；未决项落 open_questions，不用假设标记"))
    return violations

# trace: B4 diy-editorial-review check（回执计数：review / 两透镜 findings / 分类分布）
def review_counts(reviews):
    structure = prose = 0
    by_category = {}
    by_reader = {}
    for review in reviews:
        if not isinstance(review, dict):
            continue
        reader = review.get("reader_type")
        if nonempty(reader):
            by_reader[str(reader)] = by_reader.get(str(reader), 0) + 1
        slot = review.get("structure")
        findings = slot.get("findings") if isinstance(slot, dict) else None
        for finding in findings if isinstance(findings, list) else []:
            structure += 1
            if isinstance(finding, dict) and nonempty(finding.get("category")):
                key = str(finding["category"])
                by_category[key] = by_category.get(key, 0) + 1
        slot = review.get("prose")
        findings = slot.get("findings") if isinstance(slot, dict) else None
        prose += len(findings) if isinstance(findings, list) else 0
    return {"reviews": len(reviews), "structure_findings": structure,
            "prose_findings": prose, "by_category": by_category,
            "by_reader_type": by_reader}
