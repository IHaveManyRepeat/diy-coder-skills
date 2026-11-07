# -*- coding: utf-8 -*-
"""违规码集中表——唯一登记落点（违规码机器契约 §7-1 甲·两区结构）。

核心冻结区＝全 23 码（冻结，可扩展——扩须走契约审批）；
技能级区＝code -> (kind, owner 元组)。kind ∈ violation|warning|both；
owner＝该码字面量出现的技能（三形态：v( / .add( / code=）。
v() 构造前断言 code ∈ 两区并集（忘登记即红·运行时关卡）。
"""

# ---- 核心冻结区（23 码·冻结契约原文逐字）----
CORE = frozenset({
    "MISSING_FILE",
    "UNPARSABLE_YAML",
    "DUPLICATE_ID",
    "UNKNOWN_ID",
    "ENUM_INVALID",
    "EMPTY_FIELD",
    "ASSUMPTION_PRESENT",
    "PENDING_DECISION",
    "SET_MISMATCH",
    "PENDING_UNCOVERED",
    "BLOCKED_NO_REASON",
    "STATUS_MISMATCH",
    "EVIDENCE_MISSING",
    "EVIDENCE_ORDER",  # 零调用（2026-11-06 普查注记·清退另案登底单）
    "ID_UNSTABLE",
    "TRACE_UNRESOLVED",
    "ROUTE_INVALID",
    "ILLEGAL_TRANSITION",
    "STATIC_FAIL",
    "ENTRY_INVALID",
    "BASELINE_INVALID",
    "BASELINE_STALE",
    "DUPLICATE_KEY",
})

# ---- 技能级区（code -> (kind, (owner...))）----
SKILL_CODES = {
    "ADAPTER_INVALID": ("warning", ("diy-eval-runner",)),
    "ADAPTER_MISSING": ("both", ("diy-eval-runner",)),
    "AGAINST_FALLBACK": ("both", ("diy-eval-runner",)),
    "ALREADY_EXISTS": ("both", ("diy-analyze", "diy-teach-me-testing",)),
    "ANCHOR_MISSING": ("violation", ("diy-test-author",)),
    "BASELINE_DUPLICATE": ("violation", ("diy-tools",)),
    "BODY_RULE": ("violation", ("diy-bmb-builder",)),
    "BRITTLE_SELECTOR": ("violation", ("diy-test-author",)),
    "CI_MISALIGNED": ("violation", ("diy-test-framework",)),
    "COMPLIANCE_AGGREGATE_MISMATCH": ("violation", ("diy-test-gate",)),
    "COMPLIANCE_UNRECORDED": ("violation", ("diy-test-gate",)),
    "CONDITIONAL_FLOW": ("violation", ("diy-test-author",)),
    "CRITERION_STALE": ("violation", ("diy-test-gate",)),
    "CROSS_DOMAIN_UNRECORDED": ("violation", ("diy-test-gate",)),
    "DEBUG_STATEMENT": ("violation", ("diy-test-author",)),
    "DECISION_INCONSISTENT": ("violation", ("diy-test-gate",)),
    "DUTY_B_REVIEW_MISSING": ("violation", ("diy-selfcheck",)),
    "DUTY_DISPOSAL_GAP": ("violation", ("diy-selfcheck",)),
    "DUTY_RESCAN_MISSING": ("violation", ("diy-selfcheck",)),
    "DUTY_SUMMARY_REF_MISSING": ("violation", ("diy-selfcheck",)),
    "EVIDENCE_STALE": ("both", ("diy-test-gate",)),
    "FILE_CONFLICT": ("both", ("diy-bmb-builder", "diy-eval-runner", "diy-test-framework",)),
    "FILE_TOO_LONG": ("violation", ("diy-test-author",)),
    "FIXTURE_NO_TEARDOWN": ("violation", ("diy-test-author",)),
    "FORM_FACTOR_INVALID": ("violation", ("diy-design",)),
    "FORM_FACTOR_MISSING": ("violation", ("diy-design",)),
    "GATE_FAILED": ("violation", ("diy-design",)),
    "GWT_MISSING": ("violation", ("diy-test-author",)),
    "HARDCODED_DATA": ("violation", ("diy-test-author",)),
    "HARD_WAIT": ("violation", ("diy-test-author",)),
    "HYPOTHESIS_FOUND": ("violation", ("diy-selfcheck",)),
    "ID_FMT": ("violation", ("diy-selfcheck",)),
    "INCOMPLETE_RUN": ("warning", ("diy-eval-runner",)),
    "INTERNAL_ERROR": ("violation", ("diy-bmb-builder", "diy-design", "diy-tools",)),
    "MANIFEST_UNPARSABLE": ("both", ("diy-e2e-tests", "diy-project-context", "diy-test-framework",)),
    "MISSING_ASSERTION": ("violation", ("diy-test-author",)),
    "MODES_INVALID": ("violation", ("diy-design",)),
    "MODES_MISSING": ("violation", ("diy-design",)),
    "MODES_TOKEN_PAIR_MISSING": ("violation", ("diy-design",)),
    "MODE_SKIPPED": ("both", ("diy-eval-runner",)),
    "MUTATE_TIMEOUT": ("violation", ("diy-tools",)),
    "NAME_ILLEGAL": ("violation", ("diy-bmb-builder", "diy-bmb-module", "diy-eval-runner",)),
    "NAME_UNDESCRIPTIVE": ("violation", ("diy-test-author",)),
    "NONDETERMINISTIC_SOURCE": ("violation", ("diy-test-author",)),
    "NOT_ATOMIC": ("violation", ("diy-test-author",)),
    "NO_TARGET": ("violation", ("diy-checkpoint-preview",)),
    "NO_VCS": ("both", ("diy-create-story", "diy-investigate",)),
    "ONE_OFF_VALUE": ("both", ("diy-reverse",)),
    "OPEN_QUESTION_PENDING": ("violation", ("diy-design",)),
    "ORDER_DEPENDENCY": ("violation", ("diy-test-author",)),
    "OVERWRITE_REFUSED": ("violation", ("diy-reverse",)),
    "PAGE_OBJECT": ("violation", ("diy-test-author",)),
    "PLACEHOLDER_ASSERTION": ("violation", ("diy-test-author",)),
    "PRIORITY_TAG_MISMATCH": ("violation", ("diy-test-author",)),
    "PRIORITY_TAG_MISSING": ("violation", ("diy-test-author",)),
    "SANDBOX_EXISTS": ("violation", ("diy-tools",)),
    "SANDBOX_FAILED": ("violation", ("diy-tools",)),
    "SCAN_TRUNCATED": ("both", ("diy-investigate", "diy-spec-scan",)),
    "SHARED_STATE": ("violation", ("diy-test-author",)),
    "SKIP_MISSING": ("violation", ("diy-test-author",)),
    "SS_REF_UNRESOLVED": ("violation", ("diy-selfcheck",)),
    "TARGET_UNREACHABLE": ("violation", ("diy-reverse",)),
    "TEMPLATE_UNSUPPORTED": ("both", ("diy-test-framework",)),
    "THRESHOLD_UNSOURCED": ("violation", ("diy-test-gate",)),
    "TOKEN_UNRESOLVED": ("violation", ("diy-bmb-builder", "diy-bmb-module", "diy-eval-runner", "diy-tools", "diy-wds-system",)),
    "TOOL_ERROR": ("both", ("diy-brainstorm", "diy-correct-course", "diy-e2e-tests", "diy-readiness-check", "diy-teach-me-testing", "diy-test-gate", "diy-test-review",)),
    "TOOL_MISSING": ("both", ("diy-correct-course", "diy-e2e-tests", "diy-product-brief", "diy-readiness-check", "diy-test-gate", "diy-test-review",)),
    "TOOL_NOT_GIVEN": ("violation", ("diy-tools",)),
    "TRY_CATCH_TEST_LOGIC": ("violation", ("diy-test-author",)),
    "TYPE_INVALID": ("violation", ("diy-tools",)),
    "UNKNOWN_THRESHOLD_PASS": ("violation", ("diy-test-gate",)),
    "UNPARSABLE_JSON": ("both", ("diy-eval-runner",)),
    "UNSAFE_INJECTION": ("violation", ("diy-test-framework",)),
    "WAIVER_INAPPLICABLE": ("violation", ("diy-test-gate",)),
    "WAIVER_INCOMPLETE": ("violation", ("diy-test-gate",)),
    "WORKSPACE_TOUCHED": ("violation", ("diy-tools",)),
    "a11y-focus-order": ("violation", ("diy-design",)),
    "a11y-keyboard": ("violation", ("diy-design",)),
    "a11y-reduced-motion": ("violation", ("diy-design",)),
    "a11y-touch-target": ("violation", ("diy-design",)),
    "color-only-signal": ("violation", ("diy-design",)),
    "contrast": ("violation", ("diy-design",)),
    "ds-token-color": ("violation", ("diy-design",)),
    "ds-token-font-size": ("violation", ("diy-design",)),
    "ds-token-spacing": ("violation", ("diy-design",)),
    "one-off-color": ("violation", ("diy-design",)),
    "one-off-font-size": ("violation", ("diy-design",)),
    "semantic-html": ("violation", ("diy-design",)),
}

ALL = CORE | frozenset(SKILL_CODES)

# 参数位码：码作实参传 helper——字面量扫描不可达，owner 对账以本集合豁免
# （运行时关卡仍全量把守；新发现逐个补入 EXTRA 与本集合）。
PARAM_POSITION_CODES = frozenset({
    "GATE_FAILED",
})

# 扫描排除：枚举常量/键名/env 键误报（元组首形态与码表同形）——非违规码，剔出表保纯度。
SCAN_EXCLUDE = frozenset({
    "CI",
    "CONCERNS",
    "CRITICAL",
    "CUT",
    "FAIL",
    "FULL",
    "HIGH",
    "HP",
    "INSTALL_CMD",
    "P0",
    "PASS",
    "PATH",
    "PRIORITIES",
    "QA",
    "SOC2",
})


class UnknownViolationCode(ValueError):
    """违规码未登记——v() 运行时关卡抛出（忘登记即红）。"""


def is_registered(code: str) -> bool:
    """码是否已登记（两区并集）。"""
    return code in ALL


def kind_of(code: str):
    """返回 kind；核心码默认 violation，未登记返回 None。"""
    if code in CORE:
        return "violation"
    entry = SKILL_CODES.get(code)
    return entry[0] if entry else None


def owners_of(code: str):
    """返回 owner 元组；核心码返回 None（全局）。"""
    if code in CORE:
        return None
    entry = SKILL_CODES.get(code)
    return entry[1] if entry else None

