# -*- coding: utf-8 -*-
"""diy-editorial-review 确定性引擎：目标文档结构统计（stats）+ editorial-review.yaml 校验（check）。

机制：本技能对同一份文稿跑两个透镜——结构透镜（删减 / 重组 / 简化的建议）与文风透镜
（沟通障碍的三列修订建议），一次评审出一份 findings 台账（editorial-review.yaml 的
reviews[]）。源技能（bmad-editorial-review-structure + -prose）把两件机械活留给了人：

  stats   目标文档结构统计（源 structure 透镜 Step 1/3 的 "section count / word count /
          map the document structure: each major section with its word count" 是确定性统计）：
            .md / 纯文本 → `#` 是**文档标题**（不计词、不切节），节由行首 `##` / `###` 切
                            （`####` 及更深不算），标题文本作节名；第一节之前若有正文，
                            归一个以文件名为名的节；无 `##`/`###` → 整文档一个节、节名取文件名；
            .yaml / .yml  → 按顶层键切节（键名作节名），节词数 = 该键子树全部字符串的词数；
            词数口径（唯一一处定义，findings 的 impact_words 同此）：中文字符按 1 词计
            （中文无空格分词），西文按 `[A-Za-z0-9_]+` 分词计；标题行不计入所在节词数。
            目标不存在 → MISSING_FILE；全文 < 3 词 → EMPTY_FIELD（源 HALT：「少于 3 词不足
            以评审」）；无法按 UTF-8 解码 → MISSING_FILE（文档读不出来，等同不在场）。
            同时校验本次评审的 `--lens`（结构|文风，可重复；缺省两透镜全跑）与
            `--reader-type`（人类|LLM，缺省 人类）——越界即 ENUM_INVALID，**在动手前**拒绝；
            回执原样给出 `lenses` / `reader_type`，记录侧照抄、不凭记忆重打。

  check   校验 {output_dir}/editorial-review.yaml（本技能产出的 findings 台账）。基础校验：
          YAML 可解析（异常转 UNPARSABLE_YAML）；顶层 project{name,created,updated} +
          reviews[] + revisions[] 缺项；reviews[].id 形态 ER-###（三位数字）且全局唯一
          （DUPLICATE_ID / ENUM_INVALID）；target 的**基准**（project-root 相对 + 正斜杠 +
          无 `path:` 前缀，越界即 ENUM_INVALID）与**在场性**（相对 project-root 解析，
          不存在 → MISSING_FILE）；date 非空；status ∈ 草稿|已定稿；lenses 非空、取值
          结构|文风、不重复；**lenses 与两槽一致性**（跑了哪个透镜 → 对应槽在场；槽在场而
          lenses 未声明同判）→ SET_MISMATCH；reader_type ∈ 人类|LLM；open_questions 为列表。
          structure 槽：model 五值枚举（教程线性 / 参考 MECE / 解释抽象到具体 /
          任务式 meta-first / 战略金字塔）；findings[].no 记录内序号自 1 起连续、不重复
          （**取值兼容 YAML 1.1 的裸键 `no`**——PyYAML 把 `no:` 解析成布尔 `False`，
          记录侧照 schema 写裸 `no` 即可，引擎两形同读）
          （跳号 SET_MISMATCH、重号 DUPLICATE_ID、非正整数 ENUM_INVALID）；
          category 六值枚举 CUT|MERGE|MOVE|CONDENSE|QUESTION|PRESERVE；target 章节名 /
          rationale 非空；impact_words 为整数（PRESERVE 的代价记负数，允许负值）；
          estimated_reduction_words 为整数、meets_length_target ∈ 是|否|未设目标。
          prose 槽：findings[].no 同规；original / revised / changes 非空；locations 为列表。
          --final 附加：status 已落 `已定稿`（否则 STATUS_MISMATCH）、记录内零 `[假设]`
          字面量（ASSUMPTION_PRESENT）、estimated_reduction_words 与 findings 的
          impact_words 之和一致（两者都填时；PRESERVE 的负值参与求和 → SET_MISMATCH）。
          `--id ER-xxx` 只校该条记录；给的 ID 不在场 → UNKNOWN_ID。
          **`--previous` 判 no**（追加式台账：reviews[] 只追加、无 ID 集合收缩面），不实现。

规则来源：违规码全部复用 batch3-contract §3 冻结集——本引擎用到 MISSING_FILE /
UNPARSABLE_YAML / DUPLICATE_ID / UNKNOWN_ID / ENUM_INVALID / EMPTY_FIELD /
ASSUMPTION_PRESENT / SET_MISMATCH / STATUS_MISMATCH 共 9 个，**无新增码**。回执契约对齐
B1/B2/B3 批既有先例：exit 0 唯一放行 / --json 单行 JSON（ensure_ascii=False）/ 共同键
{ok, command, project_root, output_dir, violations[{code,where,msg}], warnings, counts}；
where 一律正斜杠、相对 project-root；人读态每条违规一行 `CODE where: msg` + 末尾汇总行；
--output-dir 必填（argparse required，无默认值）。分工裁定：本引擎不做实例解析、不做白名单、
不推导目录（实例解析由 SKILL.md 委托 diyc.py resolve）；两个子命令都**只读**——stats 只读
目标文档、check 只读台账，都不写任何文件（台账由技能侧编辑，终门走 check --final）。
"""
import argparse
import io
import json
import os
import re
import sys

import yaml

REVIEW_FILE = "editorial-review.yaml"
LENSES = ("结构", "文风")
SLOTS = (("结构", "structure"), ("文风", "prose"))
READER_TYPES = ("人类", "LLM")
STATUSES = ("草稿", "已定稿")
STRUCTURE_MODELS = ("教程线性", "参考 MECE", "解释抽象到具体", "任务式 meta-first",
                    "战略金字塔")
CATEGORIES = ("CUT", "MERGE", "MOVE", "CONDENSE", "QUESTION", "PRESERVE")
LENGTH_TARGETS = ("是", "否", "未设目标")
REVIEW_ID_RE = re.compile(r"ER-\d{3}\Z")
HEADING_RE = re.compile(r"^(#{1,3})[ \t]+(.*?)[ \t]*#*[ \t]*$")
CJK_RE = re.compile(r"[㐀-䶿一-鿿豈-﫿]")
WORD_RE = re.compile(r"[A-Za-z0-9_]+")
YAML_SUFFIXES = (".yaml", ".yml")
PROJECT_KEYS = ("name", "created", "updated")
ASSUMPTION = "[假设]"
NL = "\n"


# trace: B4 diy-editorial-review 契约（违规项统一 {code, where, msg} 形态）
def v(code, where, msg):
    return {"code": code, "where": where, "msg": msg}


# trace: B4 diy-editorial-review 契约（非空判定：None / 空白字符串均视为空）
def nonempty(value):
    return value is not None and str(value).strip() != ""


# trace: B4 diy-editorial-review 契约（整数判定：布尔不得充当整数）
def is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


# trace: B4 diy-editorial-review 契约（where 显示口径：正斜杠 + 相对 project-root；越界回退绝对路径）
def display_path(path, project_root):
    try:
        rel = os.path.relpath(path, project_root)
    except ValueError:
        rel = os.path.abspath(path)
    if rel.startswith(".."):
        return os.path.abspath(path).replace("\\", "/")
    return rel.replace("\\", "/")


# trace: B4 diy-editorial-review stats（递归收集任意节点的字符串值，只看值不看键）
def collect_strings(node):
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for value in node.values():
            for s in collect_strings(value):
                yield s
    elif isinstance(node, list):
        for item in node:
            for s in collect_strings(item):
                yield s


# trace: B4 diy-editorial-review 契约（YAML 安全装载：(data, err)；缺失 (None, None)、损坏 (None, 原因)）
def load_yaml_safe(path):
    if not os.path.isfile(path):
        return None, None
    try:
        with io.open(path, "r", encoding="utf-8") as handle:
            return (yaml.safe_load(handle) or {}), None
    except yaml.YAMLError as e:
        return None, str(e)
    except (OSError, UnicodeDecodeError) as e:
        return None, str(e)


# trace: B4 diy-editorial-review 契约（--json 单行 / 人读行）
def emit(payload, as_json, human_lines):
    if as_json:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        human_lines(payload)


# trace: B4 diy-editorial-review 契约（集合字段取列表；缺失/非列表 → []，缺项由 check 层单独报）
def items(doc, key):
    if not isinstance(doc, dict):
        return []
    value = doc.get(key)
    return value if isinstance(value, list) else []


# ---------------------------------------------------------------- stats：结构统计

# trace: B4 diy-editorial-review stats（词数口径：中文按字计 + 西文按分词计）
def word_count(text):
    return len(CJK_RE.findall(text)) + len(WORD_RE.findall(text))


# trace: B4 diy-editorial-review stats（md 切节：`#` 是文档标题；节由 `##`/`###` 切）
def md_sections(text, fallback):
    sections = []
    pending = []
    current = None
    for line in text.splitlines():
        match = HEADING_RE.match(line)
        if match is None:
            pending.append(line)
            continue
        if len(match.group(1)) == 1:
            continue  # `#` 文档标题：不计词、不切节（标题不是正文）
        if current is None:
            head_words = word_count(NL.join(pending))
            if head_words:
                sections.append({"name": fallback, "words": head_words})
        else:
            sections.append({"name": current, "words": word_count(NL.join(pending))})
        current = match.group(2).strip() or fallback
        pending = []
    tail_words = word_count(NL.join(pending))
    if current is None:
        sections.append({"name": fallback, "words": tail_words})
    else:
        sections.append({"name": current, "words": tail_words})
    return sections


# trace: B4 diy-editorial-review stats（yaml 切节：顶层键作节名，节词数 = 该键子树字符串词数）
def yaml_sections(doc, fallback):
    if not isinstance(doc, dict):
        return [{"name": fallback, "words": word_count(NL.join(collect_strings(doc)))}]
    sections = [{"name": str(key), "words": word_count(NL.join(collect_strings(value)))}
                for key, value in doc.items()]
    return sections or [{"name": fallback, "words": 0}]


# trace: B4 diy-editorial-review stats（目标读取与切节；.md/纯文本 vs .yaml/.yml 分派）
def read_target(path, fallback):
    try:
        with io.open(path, "rb") as handle:
            raw = handle.read()
    except OSError as e:
        return None, None, v("MISSING_FILE", "", "目标文档无法读取：%s" % e)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        return None, None, v("MISSING_FILE", "",
                             "目标文档无法按 UTF-8 解码（%s）：读不出来等同不在场" % e.reason)
    lines = len(text.splitlines())
    if path.lower().endswith(YAML_SUFFIXES):
        try:
            doc = yaml.safe_load(text) or {}
        except yaml.YAMLError as e:
            return None, lines, v("UNPARSABLE_YAML", "", "目标 YAML 解析失败：%s" % e)
        return yaml_sections(doc, fallback), lines, None
    return md_sections(text, fallback), lines, None


# trace: B4 diy-editorial-review stats（--lens / --reader-type 越界判定，见 §7 门禁：非法值 ENUM_INVALID）
def check_scope_flags(lens_args, reader_type):
    violations = []
    lenses = []
    for value in lens_args or []:
        if str(value) not in LENSES:
            violations.append(v("ENUM_INVALID", "--lens",
                                "透镜越界：%s（合法集 结构|文风）" % value))
        elif str(value) not in lenses:
            lenses.append(str(value))
    if reader_type not in READER_TYPES:
        violations.append(v("ENUM_INVALID", "--reader-type",
                            "reader_type 越界：%s（合法集 人类|LLM）" % reader_type))
    if not violations and not lenses:
        lenses = list(LENSES)
    return [name for name in LENSES if name in lenses], violations


# trace: B4 diy-editorial-review stats 子命令（结构地图 + 门禁；只读，exit 0 唯一放行）
def cmd_stats(args):
    root = os.path.abspath(args.project_root)
    out = os.path.abspath(args.output_dir)
    path = os.path.abspath(args.target if os.path.isabs(args.target)
                           else os.path.join(root, args.target))
    show = display_path(path, root)
    lenses, violations = check_scope_flags(args.lens, args.reader_type)
    target = {"path": show, "kind": "yaml" if path.lower().endswith(YAML_SUFFIXES) else "md",
              "lines": 0, "sections": [], "total_words": 0}
    if not violations:
        if not os.path.isfile(path):
            violations.append(v("MISSING_FILE", show,
                                "目标文档不存在：--target 须指向一份 md/yaml 文档"))
        else:
            sections, lines, err = read_target(path, os.path.basename(path))
            if err is not None:
                violations.append(v(err["code"], show, err["msg"]))
            else:
                target["lines"] = lines
                target["sections"] = sections
                target["total_words"] = sum(section["words"] for section in sections)
                if target["total_words"] < 3:
                    violations.append(v("EMPTY_FIELD", show,
                                        "内容不足 3 词（实为 %d 词）：不足以评审，"
                                        "源 HALT 同款门槛" % target["total_words"]))
    payload = {
        "ok": not violations,
        "command": "stats",
        "project_root": args.project_root,
        "output_dir": os.path.normpath(out).replace("\\", "/"),
        "violations": violations,
        "warnings": [],
        "counts": {"sections": len(target["sections"]),
                   "words": target["total_words"], "lines": target["lines"]},
        "lenses": lenses,
        "reader_type": args.reader_type,
        "target": target,
    }
    emit(payload, args.json, human_stats)
    return 0 if payload["ok"] else 1


# trace: B4 diy-editorial-review stats 人读态（结构地图 + 末尾汇总行）
def human_stats(payload):
    target = payload["target"]
    if payload["violations"]:
        print("拒绝：目标 %s" % target["path"])
    else:
        print("目标：%s（%s · %d 行 · %d 词）· 透镜 %s · reader_type %s"
              % (target["path"], target["kind"], target["lines"], target["total_words"],
                 "+".join(payload["lenses"]), payload["reader_type"]))
        for section in target["sections"]:
            print("- %s（%d 词）" % (section["name"], section["words"]))
    for item in payload["violations"]:
        print("%s %s: %s" % (item["code"], item["where"], item["msg"]))
    counts = payload["counts"]
    print("汇总：节 %d · 词 %d · 行 %d · 违规 %d 条（exit %d）"
          % (counts["sections"], counts["words"], counts["lines"],
             len(payload["violations"]), 0 if payload["ok"] else 1))


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
        if any(ASSUMPTION in s for s in collect_strings(review)):
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


# trace: B4 diy-editorial-review check 子命令（台账校验；exit 0 唯一放行）
def cmd_check(args):
    root = os.path.abspath(args.project_root)
    out = os.path.abspath(args.output_dir)
    path = os.path.join(out, REVIEW_FILE)
    show = display_path(path, root)
    violations = []
    checked = []
    data, err = load_yaml_safe(path)
    if data is None and err is None:
        violations.append(v("MISSING_FILE", show,
                            "%s 不存在（先跑一次文稿评审产出 findings 台账）" % REVIEW_FILE))
    elif err is not None:
        violations.append(v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err))
    elif not isinstance(data, dict):
        violations.append(v("EMPTY_FIELD", show,
                            "顶层不是映射（须为 project + reviews + revisions）"))
    else:
        violations += check_top_level(data, show)
        reviews = items(data, "reviews")
        seen_ids = set()
        for i, review in enumerate(reviews):
            rid = review.get("id") if isinstance(review, dict) else None
            if args.id and str(rid) != args.id:
                continue
            checked.append(review)
            violations += check_review(i, review, show, root, args.final, seen_ids)
        if args.id and not checked:
            violations.append(v("UNKNOWN_ID", show + ".reviews",
                                "台账里没有 id: %s 的记录" % args.id))
    counts = review_counts(checked)
    payload = {
        "ok": not violations,
        "command": "check",
        "project_root": args.project_root,
        "output_dir": os.path.normpath(out).replace("\\", "/"),
        "final": args.final,
        "violations": violations,
        "warnings": [],
        "counts": counts,
    }
    emit(payload, args.json, human_check)
    return 0 if payload["ok"] else 1


# trace: B4 diy-editorial-review check 人读态（每条违规一行 `CODE where: msg` + 末尾汇总行）
def human_check(payload):
    counts = payload["counts"]
    if payload["ok"]:
        print("PASS：%s 校验通过（review %d · 结构 findings %d · 文风 findings %d）"
              % (payload["output_dir"] + "/" + REVIEW_FILE, counts["reviews"],
                 counts["structure_findings"], counts["prose_findings"]))
    else:
        for item in payload["violations"]:
            print("%s %s: %s" % (item["code"], item["where"], item["msg"]))
    print("汇总：违规 %d 条 · 警告 %d 条（exit %d）"
          % (len(payload["violations"]), len(payload["warnings"]),
             0 if payload["ok"] else 1))


# trace: B4 diy-editorial-review 命令行面（--output-dir 必填；引擎不做实例解析/目录推导）
def build_parser():
    ap = argparse.ArgumentParser(
        description="diy-editorial-review 确定性引擎：目标文档结构统计（stats）+ "
                    "editorial-review.yaml 校验（check）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("stats", help="文档结构地图（章节 / 顶层键 + 各节词数）+ 透镜与 "
                                     "reader_type 门禁（只读）")
    s.add_argument("--target", required=True,
                   help="被评审文档（md/yaml；相对路径按 project-root 解析）")
    s.add_argument("--lens", action="append", default=None,
                   help="本次评审的透镜：结构 / 文风（可重复；缺省两透镜全跑）")
    s.add_argument("--reader-type", default="人类",
                   help="读者档：人类（缺省）| LLM")
    s.add_argument("--project-root", default=".", help="项目根（默认 .）")
    s.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    s.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    s.set_defaults(func=cmd_stats)

    k = sub.add_parser("check", help="校验 editorial-review.yaml（schema/枚举/一透镜一槽/"
                                     "序号连续；--final 附加定稿义务）")
    k.add_argument("--project-root", default=".", help="项目根（默认 .）")
    k.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    k.add_argument("--final", action="store_true",
                   help="定稿校验：status 已定稿 + 零 [假设] + 削减估计与 findings 一致")
    k.add_argument("--id", default=None, help="只校该条记录（ER-###）；给出的 ID 不在场 → UNKNOWN_ID")
    k.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    k.set_defaults(func=cmd_check)
    return ap


# trace: B4 diy-editorial-review 入口（stdout/stderr 固定 UTF-8；退出码由子命令返回）
def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = build_parser().parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
