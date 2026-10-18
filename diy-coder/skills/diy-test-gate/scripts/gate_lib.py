# -*- coding: utf-8 -*-
"""diy-test-gate 共享层：常量 / 只读索引层 / 回执输出。

模块切分对齐 `diy-tools` 先例（`diyc.py` + `diyc_check.py` + `diyc_lib.py`）：
  `gate.py`      入口与 check 懒加载，命令行唯一入口；
  `gate_collect.py` collect 面（前置门禁 + 矩阵 join + 软指标 + 证据面）；
  `gate_check.py` check 面（test-gate.yaml 校验），由 `gate.py` 懒加载；
  `gate_evidence.py` 证据面（G-1 时效 / G-2 重复覆盖 / G-3 合规 / G-4 跨域
                 + diyc 委派 + mutation 面）；
  本模块        共用：常量、只读索引（stories / test-plan / sprint / prd 的 join 源）、
                 回执输出。**本层不做实例解析、不推导目录、不写盘。**

违规码：复用 batch3-contract §3 冻结集（MISSING_FILE / UNPARSABLE_YAML / DUPLICATE_ID /
UNKNOWN_ID / ENUM_INVALID / EMPTY_FIELD / ASSUMPTION_PRESENT / SET_MISMATCH /
STATUS_MISMATCH / EVIDENCE_MISSING / PENDING_DECISION）+ diyc 委派降级码 TOOL_MISSING /
TOOL_ERROR（B1 diy-readiness-check 先例）。本技能新增码（本批申报，见回报）：
  DECISION_INCONSISTENT  门决策与两组判据 / NFR 域状态 / overlay 不自洽
  CRITERION_STALE        判据 actual/result 与从同记录机械重算的值不一致
  WAIVER_INCOMPLETE      waiver 缺 8 键契约中的键（或值为空）
  WAIVER_INAPPLICABLE    waiver ref 指向 安全域（不可豁免）或不可解析的域名
  THRESHOLD_UNSOURCED    阈值 source 非「用户会话 <date>」形态（阈值不得猜测）
  UNKNOWN_THRESHOLD_PASS 域含 UNKNOWN 阈值却记 PASS（nfr-status-definitions 硬规则）
能力补齐轮新增 4 码（源 trace / nfr checklist 条目，2026-09-18 返工）：
  EVIDENCE_STALE            证据 >7 天（台账 red/green 时间戳 / mutation run 日期）——warning
  COMPLIANCE_UNRECORDED     合规五标准缺记录 / 缺聚合行 / 行形态不合（--final）
  COMPLIANCE_AGGREGATE_MISMATCH  标准聚合行与逐域观察行重算不符（FAIL>PARTIAL>PASS）
  CROSS_DOMAIN_UNRECORDED   跨域风险合成候选命中而未落 recommendations / findings（--final）
"""
# trace: 任务书 §2.2 引擎契约（exit 0 唯一放行 / --json 单行回执 / 回执共同键 / --output-dir 必填）
# trace: 任务书 §2.3（diyc 委派：rc 0|1 均为正常回执；rc=2 / 不可解析 / 缺席 → 结构化降级）
# trace: 任务书 §4（mutation 面多 run 保守聚合 = 全部 run 的 score 最小值）
import json
import os
import re
import subprocess
import sys
from datetime import date


sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import count_by, display_path, diyc_script_path, emit_via, is_int, load_yaml_safe, nonempty, v  # noqa: E402

GATE_FILE = "test-gate.yaml"
STORIES_FILE = "stories.yaml"
PLAN_FILE = "test-plan.yaml"
PRD_FILE = "prd.yaml"
SPRINT_FILE = "sprint.yaml"
ARCH_FILE = "architecture.yaml"
MUTATION_FILE = "mutation-report.yaml"
ADR_ASSET = "adr-checklist.yaml"

DIYC_TYPES = ("test-plan",)

GATE_ROUTE = {STORIES_FILE: "diy-epics-stories",
              PLAN_FILE: "diy-test-design",
              PRD_FILE: "diy-prd"}

FR_PRIORITY = {"必须": "P0", "应该": "P1", "可选": "P2"}
PRIORITIES = ("P0", "P1", "P2")
COVERAGE_VALUES = ("FULL", "PARTIAL", "NONE", "UNIT-ONLY", "INTEGRATION-ONLY")
COVERED_VALUES = ("FULL", "UNIT-ONLY", "INTEGRATION-ONLY")
# 判定表 ②（有台账）与 ③（无台账 + warning）均计「已验证」；失败 / 待办 不计
COVERED_VERDICTS = ("verified", "missing_evidence")
TC_TYPES = ("单元", "集成", "端到端")
DOMAINS = ("安全", "性能", "可靠性", "可维护性")
DOMAIN_STATUSES = ("PASS", "CONCERNS", "FAIL", "N/A")
RISK_VALUES = ("HIGH", "MEDIUM", "NONE")
RISK_OF_STATUS = {"FAIL": "HIGH", "CONCERNS": "MEDIUM", "PASS": "NONE"}
DECISIONS = ("PASS", "CONCERNS", "FAIL")
ORACLE_SOURCES = ("stories", "合成")
ORACLE_CONFIDENCES = ("高", "中", "低")
RECORD_STATUSES = ("草稿", "已定稿")
BLOCKER_KINDS = ("覆盖", "非功能需求", "启发式")
CRITERION_RESULTS = ("通过", "失败", "n/a")
HARD_CRITERIA = (("P0 覆盖", "100%"), ("总覆盖", "100%"),
                 ("P1 覆盖", "100%"), ("变异得分", ">=90%"),
                 ("非功能致命", 0), ("P0 未覆盖", 0))
SOFT_CRITERIA = (("业务规则覆盖", "100%"),
                 ("边界覆盖", "100%"),
                 ("负向场景覆盖", ">=90%"),
                 ("P0 深度完整", "100%"),
                 ("有效用例比", ">=95%"),
                 ("ID 链可解析", "100%"))
WAIVER_KEYS = ("ref", "approved_by", "date", "reason", "expires", "monitoring",
               "fix_owner", "fix_target")
# waiver ref 的第四种合法形态（除 域名 / AC-x.y / TC-x.y.z 外）：等价变异体标识。
# 用**前缀**而不是固定形态——各变异工具的标识互不相同（cosmic-ray 报
# `core/ReplaceBinaryOperator_Add_Sub`、mutmut 报 `x_add__mutmut_1`、Stryker 报 mutator 名），
# 把形态定死等于把某一家的词汇固化成套件契约（与 diyc mutate 不解析输出的同一条纪律）。
MUTANT_REF_PREFIX = "mutant:"
BUSINESS_TECHNIQUES = ("决策表", "状态迁移")
BOUNDARY_TECHNIQUES = ("边界",)
NEGATIVE_TECHNIQUES = ("错误猜测",)

AUTH_HINTS = ("登录", "认证", "鉴权", "权限", "授权", "会话", "登出",
              "login", "auth", "token", "session", "logout")
UI_HINTS = ("页面", "界面", "路由", "跳转", "表单", "按钮", "导航", "首页",
            "ui", "page", "screen", "route", "form", "click")
API_HINTS = ("接口", "端点", "请求", "响应", "api", "endpoint", "http",
             "rest", "grpc")

TG_RE = re.compile(r"^TG-\d{3}$")
AC_RE = re.compile(r"^AC-\d+\.\d+$")
TC_RE = re.compile(r"^TC-[\d.]+$")
USER_SOURCE_RE = re.compile(r"^用户会话\s*\d{4}-\d{2}-\d{2}")

# G-1 证据时效（源 trace checklist「Evidence freshness validated (warn if >7 days old)」）
EVIDENCE_TTL_DAYS = 7
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")

# G-3 合规标准（源 nfr step-04a「Common compliance standards」）——第五个走查维度
COMPLIANCE_STANDARDS = ("SOC2", "GDPR", "HIPAA", "PCI-DSS", "ISO27001")
COMPLIANCE_STATUSES = ("PASS", "PARTIAL", "FAIL", "N/A")
COMPLIANCE_ORDER = ("FAIL", "PARTIAL", "PASS", "N/A")   # 聚合 = FAIL > PARTIAL > PASS
COMPLIANCE_RE = re.compile(
    r"^(SOC2|GDPR|HIPAA|PCI-DSS|ISO27001)"
    r"(?:@(安全|性能|可靠性|可维护性))?"
    r"\s*[:：]\s*(PASS|PARTIAL|FAIL|N/A)(?![A-Za-z])")
COMPLIANCE_HEAD_RE = re.compile(r"^(SOC2|GDPR|HIPAA|PCI-DSS|ISO27001)(?![A-Za-z-])")

# G-4 跨域风险合成（源 nfr step-04e「Identify Cross-Domain Risks」两条规则）
CROSS_DOMAIN_MARK = "×"
CROSS_DOMAIN_RULES = (
    {"pair": ("可靠性", "可维护性"), "impact": "HIGH",
     "trigger": {"可靠性": ("CONCERNS", "FAIL"),
                 "可维护性": ("CONCERNS", "FAIL")},
     "why": "低覆盖 / 缺观测可能掩盖可靠性回归（源 可靠性×可维护性 合成）"},
    {"pair": ("安全", "可靠性"), "impact": "HIGH",
     "trigger": {"安全": ("FAIL",), "可靠性": ("CONCERNS", "FAIL")},
     "why": "安全缺陷可能演变为可靠性事故（源 安全×可靠性 合成；源 impact "
            "CRITICAL 在 diy 三值尺度 HIGH|MEDIUM|NONE 压缩为 HIGH）"},
)


def cross_domain_rules_doc():
    """G-4 规则的可读形态（进 collect 回执 `nfr_inputs`，供 steps/04 逐条走查）。"""
    return [{"pair": list(rule["pair"]), "impact": rule["impact"],
             "trigger": {name: list(states)
                         for name, states in rule["trigger"].items()},
             "why": rule["why"]} for rule in CROSS_DOMAIN_RULES]


def is_counted(verdict):
    """覆盖判定口径：② verified 与 ③ missing_evidence 都算「已验证」。"""
    return verdict in COVERED_VERDICTS


def items_of(doc, key):
    """取顶层列表键；缺失 / 非列表 → []。"""
    if not isinstance(doc, dict):
        return []
    value = doc.get(key)
    return value if isinstance(value, list) else []


def all_strings(node):
    """深度收集全部字符串（[假设] 扫描用）。"""
    found = []
    stack = [node]
    while stack:
        current = stack.pop()
        if isinstance(current, str):
            found.append(current)
        elif isinstance(current, dict):
            stack.extend(current.values())
        elif isinstance(current, list):
            stack.extend(current)
    return found


def ratio(numerator, denominator):
    return 100.0 if not denominator else 100.0 * numerator / denominator


def pct_str(numerator, denominator):
    return "%d%%" % int(round(ratio(numerator, denominator)))


def pct_int(numerator, denominator):
    return int(round(ratio(numerator, denominator)))


def threshold_of(target):
    """target 形态 '100%' / '>=90%' / 0 → 数值阈值。"""
    text = str(target).strip().lstrip(">=").strip().rstrip("%").strip()
    return float(text or 0)


def meets(value, target):
    """软 / 硬指标达线判定：target 形态 '100%' 或 '>=90%'。"""
    return value >= threshold_of(target) - 1e-9


def adr_rows():
    """技能内静态资产 adr-checklist.yaml 的行数（29）。缺席 / 损坏 → None。"""
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        ADR_ASSET)
    data, err = load_yaml_safe(path)
    if err is not None or not isinstance(data, dict):
        return None
    rows = data.get("rows")
    return len(rows) if isinstance(rows, list) else None


# ---------------------------------------------------------------- 索引层（只读）

def fr_index(prd):
    """FR-x.y → P0|P1|P2；priority 越界项另列。"""
    mapping, bad = {}, []
    for feature in items_of(prd, "features"):
        for req in items_of(feature, "requirements"):
            rid = req.get("id") if isinstance(req, dict) else None
            if not nonempty(rid):
                continue
            priority = str(req.get("priority") or "").strip().lower()
            if priority in FR_PRIORITY:
                mapping[str(rid)] = FR_PRIORITY[priority]
            else:
                bad.append((str(rid), req.get("priority")))
    return mapping, bad


def ac_index(stories):
    """[(story_id, ac_dict)]，顺序按 stories / acceptance_criteria 顺序。"""
    rows = []
    for story in items_of(stories, "stories"):
        if not isinstance(story, dict):
            continue
        for ac in items_of(story, "acceptance_criteria"):
            if isinstance(ac, dict):
                rows.append((str(story.get("id") or ""), ac))
    return rows


def tc_index(plan):
    """AC-x.y → [TC dict]（test-plan 顺序）；TC-x.y.z → TC dict。"""
    by_ac, by_id = {}, {}
    for tc in items_of(plan, "test_cases"):
        if not isinstance(tc, dict) or not nonempty(tc.get("id")):
            continue
        tid = str(tc["id"])
        by_id[tid] = tc
        by_ac.setdefault(str(tc.get("ac") or "").strip(), []).append(tc)
    return by_ac, by_id


def evidence_index(sprint):
    """story → {TC id: 台账条目}（归属按该 story 的任务 test_refs / evidence）。"""
    table = {}
    for task in items_of(sprint, "tasks"):
        if not isinstance(task, dict):
            continue
        entries = {}
        for entry in items_of(task, "evidence"):
            if isinstance(entry, dict) and nonempty(entry.get("tc")):
                entries[str(entry["tc"])] = entry
        table[str(task.get("story") or "").strip()] = entries
    return table


def judge_tc(tc, evidence):
    """覆盖判定表逐 TC（任务书 §4）→ 五值之一。"""
    status = str(tc.get("status") or "").strip().lower()
    if status == "失败":
        return "blocked"
    if status == "待办":
        return "pending"
    if status != "通过":
        return "unverified"
    entry = evidence.get(str(tc.get("id") or ""))
    if isinstance(entry, dict) and nonempty(entry.get("red")) \
            and nonempty(entry.get("green")):
        return "verified"
    return "missing_evidence"


def judge_coverage(verdicts, types):
    """AC coverage 五值：NONE / PARTIAL / UNIT-ONLY / INTEGRATION-ONLY / FULL。"""
    if not verdicts:
        return "NONE"
    verified_types = {t for t, verdict in zip(types, verdicts)
                      if is_counted(verdict)}
    verified_count = sum(1 for verdict in verdicts if is_counted(verdict))
    if verified_count == 0:
        return "NONE"
    if verified_count < len(verdicts):
        return "PARTIAL"
    if verified_types == {"单元"}:
        return "UNIT-ONLY"
    if verified_types == {"集成"}:
        return "INTEGRATION-ONLY"
    return "FULL"


def priority_of(ac, frs, warnings, where):
    """prd FR priority 推导：多 FR 取最高；无 refs → P2 + warning。"""
    refs = [str(ref) for ref in (ac.get("refs") or []) if nonempty(ref)]
    if not refs:
        warnings.append(v("EMPTY_FIELD", where + ".refs",
                          "AC 无 FR refs：priority 落 P2（prd.yaml 无法推导）"))
        return "P2"
    found = [frs[ref] for ref in refs if ref in frs]
    if not found:
        warnings.append(v("UNKNOWN_ID", where + ".refs",
                          "FR refs 均不在 prd.yaml：priority 落 P2"))
        return "P2"
    return min(found, key=PRIORITIES.index)


def heuristic_candidates(ref, story, ac, tcs):
    """5 类盲区启发式候选（机械可算面：AC 文本关键词 + 已验证 TC 的层级 / 技术）。"""
    text = " ".join(str(ac.get(key) or "")
                    for key in ("given", "when", "then", "title")).lower()
    verified = [tc for tc in tcs if is_counted(tc["verdict"])]
    techniques = {tc["technique"] for tc in verified}
    types = {tc["type"] for tc in verified}
    negative = bool(techniques & set(NEGATIVE_TECHNIQUES))
    hits_ui = any(hint in text for hint in UI_HINTS)
    found = []
    if verified and not negative:
        found.append(("happy-path-only",
                      "AC 有已验证用例但全为正常路径（无 error-guessing 用例）"))
    if any(hint in text for hint in AUTH_HINTS) and not negative:
        found.append(("auth-missing-negative-path",
                      "AC 涉认证 / 权限，但无负面路径用例（源 5 类之一）"))
    if hits_ui and not verified:
        found.append(("ui-journey-without-e2e",
                      "AC 涉 UI 旅程，但无已验证用例（端到端缺位）"))
    elif hits_ui and "端到端" not in types:
        found.append(("ui-journey-without-e2e",
                      "AC 涉 UI 旅程，但已验证用例无端到端层"))
    if hits_ui and verified and types == {"端到端"} and not negative:
        found.append(("ui-state-unasserted",
                      "UI 旅程仅有端到端正常路径，未见状态断言用例"))
    if any(hint in text for hint in API_HINTS) and "集成" not in types:
        found.append(("endpoint-without-test",
                      "AC 涉接口 / 端点，但无已验证的集成用例"))
    return [{"ref": ref, "story": story, "kind": "heuristic",
             "name": name, "why": why} for name, why in found]

# ---------------------------------------------------------------- 回执输出

