"""diy-wds-brief 常量表、工具与简报校验。"""

import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import check_tokens, enum_check, load_yaml_safe, nonempty, require, v, violation_line, walk_strings, warn_line  # noqa: E402

BRIEF_FILE = "wds-brief.yaml"

# 分诊与推进（`intake` 五键；前四键是分诊结论，`stage` 是续接锚点）
PROJECT_TYPE_ENUM = ("greenfield", "brownfield")
COMPLEXITY_ENUM = ("simple", "standard", "complex", "complex+mobile")
BRIEF_LEVEL_ENUM = ("complete", "simplified")
STRATEGIC_ENUM = ("full", "simplified", "skip")
STAGE_ENUM = ("分诊", "对齐", "签核", "核心", "内容", "视觉", "收尾")
INTAKE_KEYS = ("project_type", "complexity", "brief_level", "strategic_analysis", "stage")

# 单记录产物 → 顶层 `project.status`（零偏离）
STATUS_ENUM = ("草稿", "已定稿")
FINAL_STAGE = STAGE_ENUM[-1]            # 已定稿 ⟺ stage: 收尾（反向不成立，见 check_document）

# 签核段（三型并列，全留）
SIGNOFF_TYPE_ENUM = ("不签核", "对外合同", "服务协议", "内部审批")
SIGNOFF_STATUS_ENUM = ("未开始", "构建中", "已定稿")
RETAINER_MODEL = "长期聘用"             # 唯一触发合同 `availability` 条件必填的定价模式
PRICING_ENUM = ("固定价", "计时", RETAINER_MODEL, "混合")
BRANCH_OF_TYPE = {"对外合同": "external_contract", "服务协议": "service_agreement",
                  "内部审批": "internal"}

# 对齐段（源 10 节；`status: 不需要` 时十节全免）
ALIGNMENT_STATUS_ENUM = ("不需要", "未开始", "进行中", "已定稿")
ALIGNMENT_SECTIONS = ("realization", "why_it_matters", "how_we_see_it_working",
                      "paths_we_explored", "recommended_solution", "path_forward",
                      "value_we_create", "cost_of_inaction", "our_commitment", "summary")

# 客户画像四域（源模板把「决策文化/协作风格」并进 collaboration）
CLIENT_PROFILE_KEYS = ("organization", "key_people", "internal_drivers", "collaboration")

# 简报四段（§2.3）：本四段的键名同时是**跨技能读契约**（§2.3.1，三方逐键核对）
BRIEF_KEYS = ("core", "content", "visual", "platform")

CORE_REQUIRED = ("vision", "positioning", "business_model", "target_users",
                 "product_concept", "success_metrics", "competitive_landscape",
                 "constraints")
CORE_B2B_KEY = "business_customers"     # 仅 `business_model` 含 `B2B` 时必填（源 step-06 条件性）
CORE_SIMPLIFIED = ("vision", "target_users", "constraints")

CONTENT_KEYS = ("content_language",)    # 下游读键（§2.3.1，冻结）
CONTENT_LANGUAGE_KEYS = ("personality", "tone", "languages", "seo_keywords",
                         "content_structure")
CONTENT_LANGUAGE_SIMPLIFIED = ("languages",)

VISUAL_KEYS = ("visual_direction",)     # 下游读键（§2.3.1，冻结）
VISUAL_DIRECTION_KEYS = ("inspiration", "existing_brand", "references", "design_style",
                         "layout_effects", "imagery")   # 六维（源 19/21/22/23/24/25）
VISUAL_DIRECTION_SIMPLIFIED = ("design_style",)

PLATFORM_KEYS = ("platform_requirements",)              # 下游读键（§2.3.1，冻结）
PLATFORM_REQUIREMENTS_KEYS = ("tech_stack", "integrations", "contact_strategy",
                             "multilingual")
PLATFORM_REQUIREMENTS_SIMPLIFIED = ("tech_stack",)

# 签核三型节表（三张表合计 30 节）
# 对外合同 11 节 = `steps/03-signoff.md` 第 3 步节表（逐节落 `signoff.external_contract.sections`）
CONTRACT_SECTIONS = ("project_overview", "business_model", "scope_of_work", "payment_terms",
                     "timeline", "availability", "confidentiality", "not_to_exceed",
                     "work_initiation", "terms_and_conditions", "approval")
# 服务协议 12 节 = `steps/03-signoff.md` 第 4 步节表（逐节落 `signoff.service_agreement.sections`）
SERVICE_SECTIONS = ("project_overview", "scope_of_services", "our_commitment", "timeline",
                    "why_it_matters", "expected_outcomes", "service_terms",
                    "risks_and_considerations", "confidentiality", "not_to_exceed",
                    "terms_and_conditions", "approval")
# 内部审批 7 节 = `steps/03-signoff.md` 第 5 步节表
# （「风险/保密/路径」并成第 7 节 Optional Sections）
INTERNAL_SECTIONS = ("project_overview", "goals_and_metrics", "budget_and_resources",
                     "ownership", "approval_and_signoff", "timeline_and_milestones",
                     "optional_sections")
# 合同**条件节**表：节 → 触发它必填的定价模式。`availability` 只在
# `pricing_model: 长期聘用` 时计入必填集，其余模式接受缺省（键在场则照常校验）。
# 本表与 `steps/03-signoff.md` 第 3 步第 6 行的「条件节：仅 `pricing_model: 长期聘用` 时
# 必填——其余模式整节可缺省」逐字一致。
CONTRACT_CONDITIONAL = {"availability": RETAINER_MODEL}

ASSUMPTION_MARK = "[假设]"
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}\Z")


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
                   "引擎不设默认、不私读 diy-coder.yaml）" % (command, BRIEF_FILE))


def read_document(path, show):
    """读产物 → (data | None, err)。None + err None = 缺席。"""
    data, err = load_yaml_safe(path)
    if data is not None and not isinstance(data, dict):
        return None, "顶层不是映射（须为 project + intake + client_profile + brief）"
    return data, err


def brief_summary(data):
    """`list` 只回五字段（不读正文）。"""
    project = data.get("project") if isinstance(data.get("project"), dict) else {}
    intake = data.get("intake") if isinstance(data.get("intake"), dict) else {}
    return {"name": project.get("name"), "status": project.get("status"),
            "stage": intake.get("stage"), "project_type": intake.get("project_type"),
            "updated": project.get("updated")}


def check_signoff(signoff, where, final, out):
    """签核段：type 枚举 + 分型齐备（三型节表）。"""
    if not isinstance(signoff, dict):
        out.append(v("EMPTY_FIELD", where, "signoff 不是映射（三型并列：external_contract / "
                                           "service_agreement / internal）"))
        return
    stype = enum_check(signoff.get("type"), SIGNOFF_TYPE_ENUM, where + ".type",
                       "signoff.type", out)
    enum_check(signoff.get("status"), SIGNOFF_STATUS_ENUM, where + ".status",
               "signoff.status", out)
    for key in ("external_contract", "service_agreement", "internal"):
        if key in signoff and not isinstance(signoff.get(key), dict):
            out.append(v("EMPTY_FIELD", "%s.%s" % (where, key), "须为映射（三型并列）"))
    if stype in (None, SIGNOFF_TYPE_ENUM[0]):
        return
    branch = BRANCH_OF_TYPE.get(stype)
    payload = signoff.get(branch)
    if not isinstance(payload, dict):
        payload = {}
    if not payload:
        out.append(v("EMPTY_FIELD", "%s.%s" % (where, branch),
                     "signoff.type: %s 要求 %s 段齐备（分型与已填段必须一致）"
                     % (stype, branch)))
        return
    sections = {t: s for t, s in ((SIGNOFF_TYPE_ENUM[1], CONTRACT_SECTIONS),
                                  (SIGNOFF_TYPE_ENUM[2], SERVICE_SECTIONS),
                                  (SIGNOFF_TYPE_ENUM[3], INTERNAL_SECTIONS))}[stype]
    if branch != "internal":
        enum_check(payload.get("pricing_model"), PRICING_ENUM,
                   "%s.%s.pricing_model" % (where, branch), "pricing_model", out)
    if not final:
        return
    if payload.get("finalized") is not True:
        out.append(v("STATUS_MISMATCH", "%s.%s.finalized" % (where, branch),
                     "--final 要求该型已定稿（finalized: true）"))
    body = payload.get("sections")
    if not isinstance(body, dict):
        out.append(v("EMPTY_FIELD", "%s.%s.sections" % (where, branch),
                     "sections 须为映射（%s 共 %d 节）" % (stype, len(sections))))
        return
    # 条件节（源 05f）：「长期聘用才谈可用性」——非该模式时 `availability` 不入必填集，
    # 但**键在场则照常校验**（留空仍报 EMPTY_FIELD）。其余模式与其余 10 节不变。
    required = sections
    if stype == SIGNOFF_TYPE_ENUM[1]:
        mode = str(payload.get("pricing_model") or "").strip()
        for key, trigger in CONTRACT_CONDITIONAL.items():
            if mode != trigger and key not in body:
                required = tuple(item for item in required if item != key)
    require(body, required, "%s.%s.sections" % (where, branch), out)


def check_alignment(alignment, where, final, out):
    """对齐段：四态枚举 + 十节（`status: 不需要` 时全免）。"""
    if not isinstance(alignment, dict):
        out.append(v("EMPTY_FIELD", where, "alignment 不是映射"))
        return
    status = enum_check(alignment.get("status"), ALIGNMENT_STATUS_ENUM, where + ".status",
                        "alignment.status", out)
    if status in (None, "不需要"):
        return
    if final and status != "已定稿":
        out.append(v("STATUS_MISMATCH", where + ".status",
                     "--final 要求 alignment.status ∈ {不需要, 已定稿}，实为 %s"
                     "（走了一半的对齐要么补完，要么经用户确认改判为「不需要」）" % status))
        return
    if final:
        require(alignment, ALIGNMENT_SECTIONS, where, out)


def check_document(data, show, args):
    """全量校验；返回 (violations, warnings, counts)。"""
    violations = []
    warnings = []
    project = data.get("project")
    if not isinstance(project, dict):
        violations.append(v("EMPTY_FIELD", show + " project", "project 不是映射"))
        project = {}
    for key in ("name", "created", "updated", "status"):
        if not nonempty(project.get(key)):
            violations.append(v("EMPTY_FIELD", "%s.project.%s" % (show, key), "%s 为空" % key))
    status = project.get("status")
    status_ok = False
    if isinstance(status, str) and status.strip() in STATUS_ENUM:
        status = status.strip()
        status_ok = True
    elif nonempty(status):
        violations.append(v("ENUM_INVALID", show + ".project.status",
                            "status 越界：%s（合法集 %s）"
                            % (status, "|".join(STATUS_ENUM))))
    elif not nonempty(status) and nonempty(project.get("name")):
        violations.append(v("EMPTY_FIELD", show + ".project.status", "status 为空"))

    intake = data.get("intake")
    if not isinstance(intake, dict):
        violations.append(v("EMPTY_FIELD", show + " intake", "intake 不是映射"))
        intake = {}
    for key in INTAKE_KEYS:
        if not nonempty(intake.get(key)):
            violations.append(v("EMPTY_FIELD", "%s.intake.%s" % (show, key), "必填键 %s 为空" % key))
    for key, allowed in (("project_type", PROJECT_TYPE_ENUM), ("complexity", COMPLEXITY_ENUM),
                         ("brief_level", BRIEF_LEVEL_ENUM),
                         ("strategic_analysis", STRATEGIC_ENUM), ("stage", STAGE_ENUM)):
        if nonempty(intake.get(key)):
            enum_check(intake.get(key), allowed, "%s.intake.%s" % (show, key), key, violations)
    stage = str(intake.get("stage") or "").strip()
    # 同档规则：`已定稿` ⟺ `stage: 收尾`；反向不成立——`收尾` 也是 07-finish 进行中的合法中间态
    if status_ok and status == STATUS_ENUM[1] and stage != FINAL_STAGE:
        violations.append(v("STATUS_MISMATCH", "%s.intake.stage" % show,
                            "status: 已定稿 要求 stage: %s，实为 %s"
                            % (FINAL_STAGE, stage or "空")))

    profile = data.get("client_profile")
    if not isinstance(profile, dict):
        profile = {}
    for key in CLIENT_PROFILE_KEYS:
        if key not in profile:
            violations.append(v("EMPTY_FIELD", "%s.client_profile.%s" % (show, key),
                                "客户画像四域缺 %s（organization / key_people / "
                                "internal_drivers / collaboration）" % key))

    brief = data.get("brief")
    if not isinstance(brief, dict):
        violations.append(v("EMPTY_FIELD", show + " brief", "brief 不是映射"))
        brief = {}
    for key in BRIEF_KEYS:
        if key not in brief:
            violations.append(v("EMPTY_FIELD", "%s.brief.%s" % (show, key),
                                "简报四段缺 %s（core / content / visual / platform）" % key))

    level = str(intake.get("brief_level") or "").strip()
    simplified = level == BRIEF_LEVEL_ENUM[1]
    if args.final:
        core = brief.get("core")
        if not isinstance(core, dict):
            violations.append(v("EMPTY_FIELD", show + ".brief.core", "core 不是映射"))
            core = {}
        require(core, CORE_SIMPLIFIED if simplified else CORE_REQUIRED,
                show + ".brief.core", violations)
        business_model = str(core.get("business_model") or "")
        if (not simplified) and "B2B" in business_model and not nonempty(core.get(CORE_B2B_KEY)):
            violations.append(v("EMPTY_FIELD", "%s.brief.core.%s" % (show, CORE_B2B_KEY),
                                "business_model 含 B2B → 必须给 B2B 客户画像"
                                "（源 step-06 条件性步骤）"))
        content = brief.get("content")
        if not isinstance(content, dict):
            content = {}
        language = content.get("content_language")
        if not isinstance(language, dict):
            language = {}
        require(language, CONTENT_LANGUAGE_SIMPLIFIED if simplified
                else CONTENT_LANGUAGE_KEYS, show + ".brief.content.content_language",
                violations)
        visual = brief.get("visual")
        if not isinstance(visual, dict):
            visual = {}
        direction = visual.get("visual_direction")
        if not isinstance(direction, dict):
            direction = {}
        require(direction, VISUAL_DIRECTION_SIMPLIFIED if simplified
                else VISUAL_DIRECTION_KEYS, show + ".brief.visual.visual_direction",
                violations)
        platform = brief.get("platform")
        if not isinstance(platform, dict):
            platform = {}
        requirements = platform.get("platform_requirements")
        if not isinstance(requirements, dict):
            requirements = {}
        require(requirements, PLATFORM_REQUIREMENTS_SIMPLIFIED if simplified
                else PLATFORM_REQUIREMENTS_KEYS,
                show + ".brief.platform.platform_requirements", violations)

    check_alignment(data.get("alignment"), show + ".alignment", args.final, violations)
    check_signoff(data.get("signoff"), show + ".signoff", args.final, violations)

    revisions = data.get("revisions")
    if revisions is None:
        violations.append(v("EMPTY_FIELD", show + " revisions", "revisions 缺失（无修订写空列表）"))
    elif not isinstance(revisions, list):
        violations.append(v("EMPTY_FIELD", show + " revisions", "revisions 不是列表"))

    violations += check_tokens(data, show)

    if args.final:
        if status_ok and status != STATUS_ENUM[1]:
            violations.append(v("STATUS_MISMATCH", show + ".project.status",
                                "--final 要求 status: 已定稿，实为 %s（先走完 wds-brief 的七个"
                                "步骤文件，再按 §2.5 六拍落盘定稿）" % status))
        if any(ASSUMPTION_MARK in text for _p, text in walk_strings(data, "")):
            violations.append(v("ASSUMPTION_PRESENT", show,
                                "--final 要求零 [假设]；未决项写进 revisions 或就地补问"))
    counts = {"records": 1,
              "by_status": {status: 1} if status_ok else {},
              "by_stage": {stage: 1} if stage else {}}
    return violations, warnings, counts
