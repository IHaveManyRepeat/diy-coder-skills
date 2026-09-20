# -*- coding: utf-8 -*-
"""diy-test-gate 共享层：常量 / 只读索引层 / diyc 委派 / mutation 面 / 回执输出。

模块切分对齐 `diy-tools` 先例（`diyc.py` + `diyc_check.py` + `diyc_lib.py`）：
  `gate.py`      入口与 collect 面（前置门禁 + 矩阵 join + 软指标 + 证据面），命令行唯一入口；
  `gate_check.py` check 面（test-gate.yaml 校验），由 `gate.py` 懒加载；
  本模块        两者共用：常量、只读索引（stories / test-plan / sprint / prd 的 join 源）、
                 `diyc.py` 委派（唯一跨文档机械核对入口）、`mutation-report.yaml` 读取、
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

import yaml

GATE_FILE = "test-gate.yaml"
STORIES_FILE = "stories.yaml"
PLAN_FILE = "test-plan.yaml"
PRD_FILE = "prd.yaml"
SPRINT_FILE = "sprint.yaml"
ARCH_FILE = "architecture.yaml"
MUTATION_FILE = "mutation-report.yaml"
ADR_ASSET = "adr-checklist.yaml"

DIYC_REL = ("diy-tools", "scripts", "diyc.py")
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


def v(code, where, msg):
    return {"code": code, "where": where, "msg": msg}


def nonempty(value):
    return value is not None and str(value).strip() != ""


def is_counted(verdict):
    """覆盖判定口径：② verified 与 ③ missing_evidence 都算「已验证」。"""
    return verdict in COVERED_VERDICTS


def items_of(doc, key):
    """取顶层列表键；缺失 / 非列表 → []。"""
    if not isinstance(doc, dict):
        return []
    value = doc.get(key)
    return value if isinstance(value, list) else []


def display_path(path, root):
    try:
        rel = os.path.relpath(path, root)
    except ValueError:
        rel = path
    return rel.replace("\\", "/")


def load_yaml_safe(path):
    """读 YAML：(data, err)。缺失 → (None, None)；空文件 → ({}, None)；损坏 → (None, 原因)。"""
    if not os.path.isfile(path):
        return None, None
    try:
        with open(path, encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except (OSError, yaml.YAMLError) as err:
        return None, str(err)
    return ({} if data is None else data), None


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


def is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def adr_rows():
    """技能内静态资产 adr-checklist.yaml 的行数（29）。缺席 / 损坏 → None。"""
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        ADR_ASSET)
    data, err = load_yaml_safe(path)
    if err is not None or not isinstance(data, dict):
        return None
    rows = data.get("rows")
    return len(rows) if isinstance(rows, list) else None


def count_by(rows, key):
    counts = {}
    for row in rows:
        value = row.get(key) if isinstance(row, dict) else None
        if nonempty(value):
            counts[str(value)] = counts.get(str(value), 0) + 1
    return counts


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


# ------------------------------------------------- G-1 证据时效 / G-2 重复覆盖

def latest_stamp(texts, today):
    """文本集里最新的 YYYY-MM-DD → (iso, 距 today 天数)；无可用时间戳 → None。"""
    found = []
    for text in texts:
        for stamp in DATE_RE.findall(str(text or "")):
            try:
                found.append(date.fromisoformat(stamp))
            except ValueError:
                continue
    if not found:
        return None
    newest = max(found)
    return newest.isoformat(), (today - newest).days


def evidence_stamp(entry, today):
    """台账条目的时效（red/green 里的时间戳，取最新）。"""
    if not isinstance(entry, dict):
        return None
    return latest_stamp([entry.get("red"), entry.get("green")], today)


def duplicate_candidates(ref, story, priority, tcs):
    """G-2 跨层重复覆盖候选：同一 technique + 同一 kill_target 在 ≥2 个 type 层级各有用例。

    口径收窄在可读数据面：只比对已验证 TC 的 `technique` / `kill_target` / `type`
    （不读源码、不做语义去重）；可接受重叠（P0 纵深防御）与跨层冗余的**判定留在
    steps/03-matrix-gaps.md**。
    """
    groups = {}
    for tc in tcs:
        if not is_counted(tc["verdict"]):
            continue
        technique = str(tc.get("technique") or "").strip()
        target = str(tc.get("kill_target") or "").strip()
        if technique and target:
            groups.setdefault((technique, target), []).append(tc)
    found = []
    for (technique, target), group in groups.items():
        levels = sorted({str(tc["type"]) for tc in group})
        if len(levels) < 2:
            continue
        found.append({
            "ref": ref, "story": story, "priority": priority,
            "technique": technique, "kill_target": target,
            "levels": levels, "tests": sorted(str(tc["id"]) for tc in group),
            "why": "同一技法 + 同一击杀目标跨 %d 个层级各有用例：P0 关键路径可视为可接受重叠"
                   "（纵深防御），非 P0 为跨层冗余（给合并建议）" % len(levels),
        })
    return found


# ------------------------------------------------- G-3 合规标准 / G-4 跨域合成

def compliance_lines(findings):
    """扫各域 `findings` 的合规行 → (parsed, problems)。

    行形态（steps/04-nfr.md）：`<标准>[@<域>]: <PASS|PARTIAL|FAIL|N/A> — <依据>`。
    parsed = {标准: {aggregates: [状态], observations: [(域, 状态)], lines: [原文]}}；
    problems = [(标准, 行原文)]——以标准名开头但形态不合的行（不计入 parsed）。
    """
    parsed, problems = {}, []
    for lines in findings.values():
        for raw in lines:
            text = str(raw or "").strip()
            match = COMPLIANCE_RE.match(text)
            if not match:
                head = COMPLIANCE_HEAD_RE.match(text)
                if head:
                    problems.append((head.group(1), text))
                continue
            standard, domain, status = match.groups()
            entry = parsed.setdefault(standard, {"aggregates": [], "observations": [],
                                                 "lines": []})
            entry["lines"].append(text)
            if domain:
                entry["observations"].append((domain, status))
            elif status not in entry["aggregates"]:
                entry["aggregates"].append(status)
    return parsed, problems


def compliance_rollup(statuses):
    """合规聚合 = FAIL > PARTIAL > PASS（全 N/A → N/A）；空集 → None。"""
    values = {str(item).strip().upper() for item in statuses if nonempty(item)}
    if not values:
        return None
    return next((state for state in COMPLIANCE_ORDER if state in values), None)


def cross_domain_hits(statuses):
    """G-4 候选：按源两条规则判域状态组合（trigger 命中的 pair 全落区间才算命中）。"""
    hits = []
    for rule in CROSS_DOMAIN_RULES:
        left, right = rule["pair"]
        if all(str(statuses.get(name) or "").upper() in rule["trigger"][name]
               for name in rule["pair"]):
            hits.append({"pair": [left, right], "impact": rule["impact"],
                         "marker": left + CROSS_DOMAIN_MARK + right,
                         "why": rule["why"]})
    return hits


# ---------------------------------------------------------------- diyc 委派

def diyc_script_path():
    """diyc.py 路径：由引擎自身位置推算 skills 根（源码与安装布局同构，任务书 §2.3）。"""
    skills_root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    return os.path.join(skills_root, *DIYC_REL)


def diyc_type_check(script, project_root, type_name):
    """委派 diyc check --type T --final。返回 (回执 dict | None, warning | None)。"""
    where = "diyc.py check --type %s" % type_name
    cmd = [sys.executable, script, "check", "--type", type_name, "--final",
           "--project-root", project_root, "--json"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              encoding="utf-8", errors="replace")
    except OSError as err:
        return None, v("TOOL_ERROR", where, "diyc 子进程无法启动：%s" % err)
    if proc.returncode not in (0, 1):
        tail = " ".join((proc.stderr or proc.stdout or "").split())[-200:]
        return None, v("TOOL_ERROR", where,
                       "diyc 非预期退出码 %s（期望 0|1）：%s"
                       % (proc.returncode, tail or "无输出"))
    payload = None
    for line in reversed((proc.stdout or "").splitlines()):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
            break
        except ValueError:
            continue
    if not isinstance(payload, dict):
        return None, v("TOOL_ERROR", where, "diyc 回执不可解析（--json 面单行 JSON 缺失）")
    return payload, None


def run_diyc_checks(project_root, out_dir):
    """跑 test-plan 型 check，合并回执。返回 (diyc 块, warnings)。"""
    warnings = []
    script = diyc_script_path()
    block = {"available": False, "script": display_path(script, project_root),
             "checked": [], "violations": [], "counts": {}}
    if not os.path.isfile(script):
        warnings.append(v("TOOL_MISSING", block["script"],
                          "diyc.py 缺席：跨文档核对降级，请从会话侧人工复核 TC 台账一致性"))
        return block, warnings
    block["available"] = True
    for type_name in DIYC_TYPES:
        payload, warning = diyc_type_check(script, project_root, type_name)
        if warning is not None:
            warnings.append(warning)
            continue
        block["checked"].append(type_name)
        resolved = payload.get("output_dir")
        if nonempty(resolved) and os.path.normpath(str(resolved)) \
                != os.path.normpath(out_dir):
            warnings.append(v("TOOL_ERROR", "diyc.py check --type %s" % type_name,
                              "diyc 解析到的 output_dir 与本次 --output-dir 不一致：%s"
                              % resolved))
        for item in payload.get("violations") or []:
            block["violations"].append(item)
            warnings.append(v("EVIDENCE_MISSING", item.get("where") or type_name,
                              "diyc 报上游违规，须落 gate.blockers：%s" % item.get("msg")))
        block["counts"][type_name] = payload.get("counts") or {}
    return block, warnings


# ---------------------------------------------------------------- mutation 面

def mutation_block(out, warnings, today=None):
    """mutation-report.yaml → 保守聚合面（多 run 取最小值）+ 时效面（run 日期 >7 天）。"""
    block = {"present": False, "source": MUTATION_FILE, "runs": 0,
             "score": None, "target": ">=90%", "equivalents": 0}
    data, err = load_yaml_safe(os.path.join(out, MUTATION_FILE))
    if err is not None:
        warnings.append(v("UNPARSABLE_YAML", MUTATION_FILE,
                          "mutation-report.yaml 解析失败，变异得分 记 n/a：%s" % err))
        return block
    if data is None:
        warnings.append(v("MISSING_FILE", MUTATION_FILE,
                          "mutation-report.yaml 缺席（diy-augment 未跑变异）："
                          "变异得分 记 n/a + warning"
                          "（过渡期口径，C 阶段前不拒绝）"))
        return block
    runs = items_of(data, "runs")
    scores = [run.get("score") for run in runs if isinstance(run, dict)
              and isinstance(run.get("score"), (int, float))
              and not isinstance(run.get("score"), bool)]
    equivalents = sum(len(items_of(run, "equivalents")) for run in runs
                      if isinstance(run, dict))
    block.update({"present": True, "runs": len(runs),
                  "score": int(min(scores)) if scores else None,
                  "equivalents": equivalents})
    if runs and len(scores) != len(runs):
        warnings.append(v("EMPTY_FIELD", MUTATION_FILE + " runs[].score",
                          "部分 run 缺 score：聚合只取可读项"))
    today = today or date.today()
    for run in runs:
        stamp = latest_stamp([run.get("date")], today) if isinstance(run, dict) else None
        if stamp and stamp[1] > EVIDENCE_TTL_DAYS:
            warnings.append(v("EVIDENCE_STALE", MUTATION_FILE + " runs[].date",
                              "run %s 的变异结果 %s（%d 天前 > %d 天）：证据时效过期——重跑"
                              "刷新，或经用户确认后沿用并在 gate.basis 注明"
                              % (run.get("task") or run.get("date"), stamp[0],
                                 stamp[1], EVIDENCE_TTL_DAYS)))
    return block


# ---------------------------------------------------------------- 回执输出

def emit(payload, as_json, human_lines):
    if as_json:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        human_lines(payload)
