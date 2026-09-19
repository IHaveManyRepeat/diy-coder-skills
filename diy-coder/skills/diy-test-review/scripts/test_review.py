# -*- coding: utf-8 -*-
"""diy-test-review 确定性引擎：机械扫描 + 评分账本 + 三向走查 + 产物校验。

源能力蓝本：`bmad-testarch-test-review`（4 逻辑步；核心资产 criteria-registry.md
35 规则——本技能逐行留档为 `criteria.yaml`：M9/M10/L9 标 disabled（私有库绑定裁剪），
有效 32 行）。任务书 §6 的七条裁定全部落在此处：

  1. **评分账本全部沉到引擎**（裁定 1）：`score` 是纯函数——LLM 只产出 findings
     （规则命中 + 位置 + 说明，**severity 不由 LLM 填**），引擎按 criteria.yaml 行值
     **复算 severity**、按 convention 行 class **降档**、按 `file:location:row` **去重**
     （文件级行 FILE_LEVEL_ROWS 以 `file` 取代行号）、算分并校验 LLM 声明不参与计分。
  2. **convention 分类归属**（裁定 3）：`scan` 是机械可计数键的判定权威——5 个机械键
     （priority_markers / test_ids / network_first / data_factories / fixtures）直接产出
     {adopted, status}，阈值照源三行（sampled<4 → unknown；adopted==0 → absent；
     adopted/sampled ≥ 0.5 → established，否则 emerging）；`bdd_naming` / `assertion_style`
     在源文明确无机械信号 → 回执只标 `judged_by: llm`，由 LLM 读采样文件判读。
     降档由 `score` 应用（emerging → 降一档 floor LOW；absent / unknown → 该行不成立）。
  3. **维度分复算**（裁定 4）：与账本同一次调用；每维 = max(0, 100 − Σ去重后该维命中
     severity 权重 {CRITICAL:20, HIGH:10, MEDIUM:5, LOW:2})；行↔维度映射承载于
     criteria.yaml 的 `dimensions` 字段；仅展示，不进账本、不进 recommendation。
  4. **三向走查层**（裁定 5）：`walkthrough` 执行 AC ↔ 源码 ↔ 测试三向对账，四类缺口
     （no_impl / no_test / orphan_tc / never_run）。**跨文档核对一律委派 diyc**：
     源码面委派 `diyc.py trace`、orphan_tc 面委派 `diyc.py check --type test-plan`；
     子进程 rc∈{0,1} 均为正常回执（1 = 上游有违规，其 violations 计入判定、不吞掉），
     rc=2 / 不可解析 / 缺席 → TOOL_MISSING / TOOL_ERROR warning 降级，不崩溃。
  5. **机械/语义分界**（裁定 6）：`detect: mechanical|semantic` 是唯一权威；机械集初始 =
     C1/C2/C3/H1/H5/H6/H7/H8/H9/L4（可扩不可缩，扩展须回报登记），由 `scan` 直接产出。
  6. **findings.json 与 bonus**（裁定 7）：`score --findings` 消费 LLM 产出的
     `{findings: [{file, line|null, row, class|null, note}], bonus: [{key, points, note}]}`；
     note 与额外键不参与计分；bonus 六类各 0/5、上限 30，并做与该表规则行的**矛盾复核**
     （映射承载于 criteria.yaml 的 `bonus_guard` 字段）。
  7. **与 diy-review 的边界**：本引擎只审测试代码质量并出评分账本；实现代码的
     正确性/边界/验收/设计审查归 diy-review，两者不重叠、互不调用。

V 能力补项（2026-09-18，源 test-review 对账 `v-capability-inventory.md` §1.4；
**加校验，不动评分账本**——severity 权重 / convention 降档 / bonus 六类三处零漂移）：
  R-1 recommendations 排序纪律与 Top 10 上限（源 `steps-c/step-03f` §4）：排序判据
      （维度分 < 70 → HIGH）由 LLM 在 05 步照条文施加，**上限 10 由 `check` 机械拦**。
  R-2 convention **引用与实际语料独立复测**（源 `steps-c/step-02` §2b）：`basis:
      convention` 的 finding 其 `class` 必须与 `convention_baseline.keys.<key>.status`
      一致（键映射 = criteria.yaml 行字段 `convention_key`）——status 为 absent/unknown
      时该行本不成立、不得成条目；引用不可核（基线缺该键）同样拒绝。`check` 面执行。
  R-3 空 / 极简测试文件处置（源 `checklist.md` §Edge Cases）：空（无代码内容）→ 发现面
      归 excluded(out-of-scope) **不评分**，全部为空则走无测试文件的拒绝路径；极简
      （有内容零断言）→ `scan` warning "No meaningful tests"，须按 C4 成条目；
      `check` 另有拦阻：空文件不得出现在 `scope.paths`。
  R-4 pact 附加上报（源 `steps-c/step-03a` §1b，低危）：单 `it()` 内含 >1
      `addInteraction()` → `scan` warning（无 registry row，落 `recommendations` 散文）；
      配置经 `mergeConfig(` / `extends:` 组合致三条必需设置不可验证 → 合一降为 L4
      advisory（`pact-config-unverifiable`），带 `// tea:pact-ffi-safe` 标记则不报。

命令面（任务书 §6 钉死）：
  scan        [--paths P]... [--project-root R] [--output-dir D] [--json]
              测试文件发现 + 机械项检出 + convention baseline 采样（评审集之外的既有
              语料、上限 40 文件、7 key）。无测试文件 → 拒绝（exit 1，零产出）。
  score       --findings <findings.json> [--project-root R] [--output-dir D] [--json]
              账本计算（纯函数，不写文件）：severity 复算 → convention 降档 → 去重 →
              deductions / bonus → score / grade / recommendation → 维度分。
  walkthrough [--project-root R] [--output-dir D] [--json]
              三向对账（只读；跨文档核对委派 diyc）。四类缺口 + 就绪态 full|partial|skipped。
  check       [--final] [--project-root R] [--output-dir D] [--json]
              校验 {output_dir}/test-review.yaml：schema / 枚举 / 账本自洽 / row ∈ 有效 32 行 /
              coverage_gaps 形态 / walkthrough 自洽 / **convention 引用复核（R-2）** /
              **recommendations 上限（R-1）** / **空文件不得计入评审集（R-3）**；
              --final 附加：零 [ASSUMPTION]、excluded 理由三值、scope 非空、记录已落 final。

引擎契约（任务书 §2.2）：exit 0 唯一放行；1 = 违规/被拒绝；2 = 用法错误（argparse）；
--json → 单行 JSON 回执（ensure_ascii=False），无 --json → 中文人读行。回执共同键
{ok, command, project_root, output_dir, violations:[{code, where, msg}], warnings, counts}；
--output-dir 必填、不设默认；不做 --instance / 目录推导（实例解析由 SKILL.md 委托
`diyc.py resolve`）。`--previous` **不实现**：reviews[] 是追加式台账（RV-### 稳定不重用），
无 ID 集合收缩面，与 P1/B1/B2 的"追加式产物判 no"先例一致。

违规码：复用 batch3-contract §3 冻结集（MISSING_FILE / UNPARSABLE_YAML / DUPLICATE_ID /
ENUM_INVALID / EMPTY_FIELD / ASSUMPTION_PRESENT / STATUS_MISMATCH / SET_MISMATCH /
PENDING_DECISION）；**新增码仅两个**——`TOOL_MISSING` / `TOOL_ERROR`（diyc 委派降级专用，
B1 diy-readiness-check 首创，本批沿用），无其他新码。
"""
# trace: B3 diy-test-review #3 #4 #12

import argparse
import io
import json
import os
import re
import subprocess
import sys

import yaml

TEST_REVIEW_FILE = "test-review.yaml"
FINDINGS_FILE = "test-review-findings.json"
CRITERIA_FILE = "criteria.yaml"
STORIES_FILE = "stories.yaml"
TEST_PLAN_FILE = "test-plan.yaml"

# 裁定 1（源实现逐字）：文件级行以 `file` 取代行号（身份 = row @ file）
FILE_LEVEL_ROWS = frozenset({"H5", "H6", "H7", "H8", "L4"})
# 源评分账本（数值口径不得漂移）
DEDUCTION_WEIGHTS = {"CRITICAL": 10, "HIGH": 5, "MEDIUM": 2, "LOW": 1}
DIMENSION_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 2}
SEVERITIES = ("CRITICAL", "HIGH", "MEDIUM", "LOW")
SEVERITY_STEPS = {"CRITICAL": "HIGH", "HIGH": "MEDIUM", "MEDIUM": "LOW", "LOW": "LOW"}
BONUS_KEYS = ("excellentBdd", "comprehensiveFixtures", "dataFactories",
              "networkFirst", "perfectIsolation", "allTestIds")
BONUS_POINTS = 5
BONUS_MAX = 30
DIMENSIONS = ("determinism", "isolation", "maintainability", "performance")
GRADES = ("A", "B", "C", "D", "F")
RECOMMENDATIONS = ("Block", "Request-Changes", "Approve-with-Comments", "Approve")
RECORD_STATUSES = ("draft", "final")
CONVENTION_STATUSES = ("established", "emerging", "absent", "unknown")
CONVENTION_ENTRY_STATUSES = ("established", "emerging")  # absent / unknown → 该行不成立
CONVENTION_KEYS = ("priority_markers", "test_ids", "bdd_naming", "network_first",
                   "data_factories", "fixtures", "assertion_style")
MECHANICAL_KEYS = ("priority_markers", "test_ids", "network_first",
                   "data_factories", "fixtures")
# R-1：源 step-03f §4 取 Top 10（排序判据在 05 步条文，上限在此机械拦）
RECOMMENDATIONS_MAX = 10
LLM_JUDGED_KEYS = ("bdd_naming", "assertion_style")
SAMPLE_CAP = 40
BASELINE_MIN_CORPUS = 4  # sampled < 4 → unknown（源三行第一行）
ESTABLISHED_RATIO = 0.5  # adopted/sampled ≥ 0.5 → established
EXCLUDED_REASONS = ("unsupported-format", "generated", "out-of-scope")
WALKTHROUGH_STATUSES = ("full", "partial", "skipped")
GAP_KINDS = ("no_impl", "no_test", "orphan_tc", "never_run")
GAP_REF_KINDS = {"no_impl": "ac", "no_test": "ac", "orphan_tc": "tc", "never_run": "tc"}
GAP_ROUTES = {"no_impl": ("diy-dev",),
              "no_test": ("diy-test-design", "diy-test-author"),
              "orphan_tc": ("user",),
              "never_run": ("diy-test-author",)}
AC_RE = re.compile(r"AC-\d+(?:\.\d+)*")
TC_RE = re.compile(r"TC-\d+(?:\.\d+)*")
RV_RE = re.compile(r"RV-\d{3}")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
ASSUMPTION = "[ASSUMPTION]"

# ---------------------------------------------------------------- 扫描面常量

# 测试文件识别表（语言无关；命中即入评审集）
TEST_SUFFIXES = (".spec.ts", ".spec.tsx", ".spec.js", ".spec.jsx", ".spec.mjs",
                 ".test.ts", ".test.tsx", ".test.js", ".test.jsx", ".test.mjs",
                 ".pacttest.ts", ".cy.ts", ".cy.js",
                 "_test.py", "_test.go", "_test.rs", "_spec.rb",
                 "Test.java", "Tests.java", "IT.java", "Test.cs", "Tests.cs",
                 "Test.kt", "Test.php")
MAESTRO_FLOW_SUFFIXES = (".flow.yaml", ".flow.yml")
# registry 无谓词的格式 → excluded(unsupported-format)（"匹配不到任何规则得到的 100 不是 100"）
UNSUPPORTED_SUFFIXES = (".feature", ".robot", ".http", ".rest")
# 生成物标记 → excluded(generated)
GENERATED_MARKERS = ("@generated", "code generated", "do not edit", "auto-generated",
                     "autogenerated", "此文件自动生成")
EXCLUDE_DIRS = {".git", ".claude", ".analysis", "node_modules", "__pycache__",
                ".venv", "venv", "dist", "build", ".pytest_cache", ".tox",
                ".mypy_cache", "coverage", ".idea", ".vscode"}

# 机械集（裁定 6：可扩不可缩；本表与 criteria.yaml 的 detect: mechanical 行一致）
IMPLEMENTED_MECHANICAL = frozenset({"C1", "C2", "C3", "H1", "H5", "H6", "H7", "H8",
                                    "H9", "L4"})
C1_RE = re.compile(r"\b(?:test|it|describe)\.(?:skip|todo)\b|\bxit\b|\bxdescribe\b|"
                   r"@Ignore\b|@Disabled\b|pytest\.mark\.skip\w*")
C1_REASON_RE = re.compile(r"\breason\s*[:=]")
C2_RE = re.compile(r"\b(?:test|it|describe)\.only\b|\bfdescribe\b|\bfit\s*\(")
C3_RES = (re.compile(r"expect\(\s*([^()]+?)\s*\)\.(?:toBe|toEqual)\(\s*\1\s*\)"),
          re.compile(r"\bassert\s+([A-Za-z_$][\w.$]*)\s*==\s*\1\b"))
H1_RE = re.compile(r"waitForTimeout|\bsleep\(|time\.sleep\(|Thread\.sleep\(|"
                   r"cy\.wait\(\s*\d|^\s*-\s*sleep:")
H9_RE = re.compile(r"(?i)\b(?:password|passwd|pwd|token|api[_-]?key|apikey|secret|"
                   r"credential|access[_-]?key)\s*:\s*(?!\$\{|<|\{\{)[\"']?([^\s\"'#]+)")
H5_MAX_LINES = 1000
COMMENT_MARKERS = ("#", "//", "/*", "--")
PACT_CONFIG_NAMES = ("vitest.config.pact.ts", "vitest.config.contract.ts")
PACT_FILE_SUFFIX = ".pacttest.ts"

# convention baseline 机械键的探测表（启发式；源文只给"adopted when…"语义，无正则）
KEY_PATTERNS = {
    "priority_markers": (re.compile(r"\[P[0-3]\]"), re.compile(r"@P[0-3]\b"),
                         re.compile(r"(?i)\bpriority\s*[:=]\s*[\"']?P[0-3]")),
    "test_ids": (re.compile(r"data-testid"), re.compile(r"\bByTestId\b"),
                 re.compile(r"\bgetByTestId\b"), re.compile(r"\btest[_-]?id\s*[:=]")),
    "network_first": (re.compile(r"interceptNetworkCall"), re.compile(r"page\.route\("),
                      re.compile(r"cy\.intercept\("), re.compile(r"server\.use\("),
                      re.compile(r"\broutes?\s*\("), re.compile(r"responses?\s*\(")),
    "data_factories": (re.compile(r"\bfaker\b"), re.compile(r"\bFactory\b"),
                       re.compile(r"\bfactory\("), re.compile(r"\bbuild[A-Z]\w*\("),
                       re.compile(r"\bcreate[A-Z]\w*\(")),
    "fixtures": (re.compile(r"mergeTests"), re.compile(r"merged-fixtures"),
                 re.compile(r"pytest\.fixture"), re.compile(r"\bfixture\s*\("),
                 re.compile(r"\bbeforeEach\s*\("), re.compile(r"\btest\.extend\("),
                 re.compile(r"@BeforeEach\b")),
}

# R-3：空 / 极简测试文件（源 checklist §Edge Cases）。空 = 剥注释后无内容；
# 极简 = 有内容但零断言 token。断言集取**宽口径**——漏判只少报一条 advisory，
# 误判会把真实文件判成"无断言"，故宁宽勿窄。
CONTENT_IGNORE_PREFIX = ("#", "//", "/*", "--", "*")
ASSERTION_RE = re.compile(
    r"(?i)\bassert|\bexpect|\bverify|\bshould\b|\bpanic|\bfatal|\berrorf|"
    r"\brequire\s*[.!]|\bfail\s*\(|\bmust\b|\.to[A-Z]")

# R-4：pact 附加上报（源 step-03a §1b）。mergeConfig / extends 后三条必需设置可能落在
# 不可跟随的基础配置里 → literal 匹配只能得假阴性，转 LOW advisory（源逐字分类名）。
MERGE_CONFIG_RE = re.compile(r"\bmergeConfig\s*\(|\bextends\s*:")
FFI_SAFE_MARKER = "tea:pact-ffi-safe"
ADD_INTERACTION_RE = re.compile(r"\baddInteraction\s*\(")
TEST_BLOCK_RE = re.compile(r"\b(?:it|test)\s*\(")

DIYC_REL = ("diy-tools", "scripts", "diyc.py")


def v(code, where, msg):
    return {"code": code, "where": where, "msg": msg}


def nonempty(value):
    return value is not None and str(value).strip() != ""


def items(doc, key):
    if not isinstance(doc, dict):
        return []
    value = doc.get(key)
    return value if isinstance(value, list) else []


def load_yaml_safe(path):
    """读 YAML：(data, err)。缺失 → (None, None)；空文件 → ({}, None)；损坏 → (None, 原因)。"""
    if not os.path.isfile(path):
        return None, None
    try:
        with io.open(path, "r", encoding="utf-8") as f:
            return (yaml.safe_load(f) or {}), None
    except yaml.YAMLError as e:
        return None, str(e)
    except OSError as e:
        return None, str(e)


def read_text(path):
    try:
        with io.open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def display_path(path, project_root):
    """where 显示口径（对齐 diyc）：正斜杠 + 相对 project-root；越界则绝对路径。"""
    try:
        rel = os.path.relpath(path, project_root)
    except ValueError:
        rel = os.path.abspath(path)
    if rel.startswith(".."):
        return os.path.abspath(path).replace("\\", "/")
    return rel.replace("\\", "/")


def collect_strings(node):
    """递归收集映射/列表内的全部字符串（键与值）——[ASSUMPTION] 扫描用。"""
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for key, value in node.items():
            yield str(key)
            for s in collect_strings(value):
                yield s
    elif isinstance(node, list):
        for item in node:
            for s in collect_strings(item):
                yield s


def criteria_path():
    """criteria.yaml 路径：由引擎自身位置推算（技能根，源码与安装布局同构）。"""
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        CRITERIA_FILE)


def load_criteria():
    """规则注册表 → {row: {...}}；缺席 / 损坏 → 抛错（技能资产缺失属 bug，不静默）。"""
    data, err = load_yaml_safe(criteria_path())
    if err is not None or not isinstance(data, dict):
        raise RuntimeError("criteria.yaml 不可读或不可解析：%s" % (err or criteria_path()))
    table = {}
    for row in items(data, "rules"):
        if isinstance(row, dict) and nonempty(row.get("row")):
            table[str(row["row"])] = row
    return table


def valid_rows(table):
    """有效 32 行（disabled 行不入有效集）。"""
    return {row for row, spec in table.items() if not spec.get("disabled")}


def bonus_guard_map(table):
    """bonus 键 → 触发矛盾复核的规则行集合（映射承载于行字段 bonus_guard）。"""
    guards = {}
    for row, spec in table.items():
        for key in spec.get("bonus_guard") or []:
            guards.setdefault(str(key), set()).add(row)
    return guards


def downgrade_severity(severity, klass):
    """convention 降档（源表逐字）：emerging → 降一档 floor LOW；established 原档。"""
    if klass == "emerging":
        return SEVERITY_STEPS.get(severity, severity)
    return severity


def clamp_score(value):
    return max(0, min(100, int(value)))


def grade_of(score):
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def recommend_of(counts, score):
    """recommendation 由计算得出（源文逐条：数值口径不得漂移；此处只换连字符形态）。"""
    if counts["CRITICAL"] > 0:
        return "Block"
    if counts["HIGH"] > 0:
        return "Request-Changes"
    if score < 70:
        return "Request-Changes"
    if counts["MEDIUM"] + counts["LOW"] > 0:
        return "Approve-with-Comments"
    return "Approve"


def convention_status(adopted, sampled):
    """源 step-02 三行判据（逐字）：deterministic on purpose。"""
    if sampled < BASELINE_MIN_CORPUS:
        return "unknown"
    if adopted == 0:
        return "absent"
    return "established" if adopted / float(sampled) >= ESTABLISHED_RATIO else "emerging"


# ---------------------------------------------------------------- 文件发现

def is_maestro_flow(rel_path):
    name = os.path.basename(rel_path)
    if name.endswith(MAESTRO_FLOW_SUFFIXES):
        return True
    parts = rel_path.replace("\\", "/").split("/")
    return (name.endswith((".yaml", ".yml"))
            and any(p in ("maestro", ".maestro") for p in parts[:-1]))


def is_pact_config(rel_path):
    return os.path.basename(rel_path) in PACT_CONFIG_NAMES


def is_test_file(rel_path):
    name = os.path.basename(rel_path)
    if name.startswith("test_") and name.endswith(".py"):
        return True
    if any(name.endswith(suffix) for suffix in TEST_SUFFIXES):
        return True
    return is_maestro_flow(rel_path)


def is_unsupported_format(rel_path):
    return os.path.basename(rel_path).endswith(UNSUPPORTED_SUFFIXES)


def has_generated_marker(path):
    head = read_text(path)[:2000].lower()
    return any(marker.lower() in head for marker in GENERATED_MARKERS)


def has_code(text):
    """R-3：剥掉空行与注释行后是否还有内容（空文件判定，源 "No tests found"）。"""
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(CONTENT_IGNORE_PREFIX):
            continue
        return True
    return False


def assertion_free(text):
    """R-3：文件内零断言 token（源 "No meaningful tests"）。宽口径，见 ASSERTION_RE。"""
    return not ASSERTION_RE.search(text)


def walk_files(base, exclude_abs=None):
    """递归目录下的全部文件；跳过排除目录与 resolved output_dir。"""
    for dirpath, dirnames, filenames in os.walk(base):
        for d in list(dirnames):
            if d in EXCLUDE_DIRS:
                dirnames.remove(d)
                continue
            if exclude_abs is not None and os.path.normcase(
                    os.path.abspath(os.path.join(dirpath, d))) == exclude_abs:
                dirnames.remove(d)
        for name in filenames:
            yield os.path.join(dirpath, name)


def classify_file(path, root):
    """→ (kind, rel)。kind ∈ test | empty | unsupported | generated | pact | other。

    `empty`（R-3）= 测试文件名下剥注释后无任何内容：没有可审的用例，匹配不到任何规则
    ⇒ 不评分（源 checklist "No tests found"）。
    """
    rel = os.path.relpath(path, root).replace("\\", "/")
    if is_pact_config(rel):
        return "pact", rel
    if has_generated_marker(path):
        return "generated", rel
    if is_test_file(rel):
        return ("test" if has_code(read_text(path)) else "empty"), rel
    if is_unsupported_format(rel):
        return "unsupported", rel
    return "other", rel


def discover_scope(args, root, out):
    """评审集发现。返回 (files, excluded, pact_configs, warnings)。

    --paths 给定时逐条判定（文件 → 分类；目录 → 递归）；缺席时按 suite 口径扫
    project-root（排除 output_dir / VCS / 依赖 / 构建目录）。两个 excluded 理由
    （源"文件不存在"与"解析不出"）在 diy 侧映射为 `out-of-scope`，详见 docstring。
    """
    warnings = []
    files, excluded, pacts = [], [], []
    seen = set()
    show_out = os.path.normcase(os.path.abspath(out))

    def take(path):
        kind, rel = classify_file(path, root)
        if kind == "test" and rel not in seen:
            seen.add(rel)
            files.append(rel)
        elif kind == "pact":
            if rel not in {p for p in pacts}:
                pacts.append(rel)
        elif kind in ("unsupported", "generated"):
            excluded.append({"path": rel, "reason": kind if kind != "unsupported"
                             else "unsupported-format"})
        elif kind == "empty":
            # R-3：空测试文件匹配不到任何规则 ⇒ excluded 不评分（源 "No tests found"）
            if not any(e["path"] == rel for e in excluded):
                excluded.append({"path": rel, "reason": "out-of-scope"})
                warnings.append(v("EMPTY_FIELD", rel,
                                  "No tests found：空测试文件（无可审内容）→ 不评分"))
        elif kind == "other":
            excluded.append({"path": rel, "reason": "out-of-scope"})

    if args.paths:
        for raw in args.paths:
            path = raw if os.path.isabs(raw) else os.path.join(root, raw)
            path = os.path.abspath(path)
            if not os.path.exists(path):
                rel = os.path.relpath(path, root).replace("\\", "/")
                excluded.append({"path": rel, "reason": "out-of-scope"})
                warnings.append(v("MISSING_FILE", rel, "路径不存在：既不评审也不计入语料"))
                continue
            if os.path.isdir(path):
                for found in sorted(walk_files(path, show_out)):
                    take(found)
            else:
                take(path)
    else:
        for found in sorted(walk_files(root, show_out)):
            take(found)
    return files, excluded, pacts, warnings


def build_corpus(review_files, root, out):
    """convention baseline 语料：评审集之外的既有测试文件，上限 40，就近优先。"""
    review_abs = {os.path.normcase(os.path.abspath(os.path.join(root, f)))
                  for f in review_files}
    corpus = []
    for path in walk_files(root, os.path.normcase(os.path.abspath(out))):
        if os.path.normcase(os.path.abspath(path)) in review_abs:
            continue
        rel = os.path.relpath(path, root).replace("\\", "/")
        if is_test_file(rel):
            corpus.append(rel)

    def distance(rel):
        parts = set(os.path.dirname(rel).replace("\\", "/").split("/"))
        best = 0
        for reviewed in review_files:
            rparts = set(os.path.dirname(reviewed).replace("\\", "/").split("/"))
            best = max(best, len(parts ^ rparts))
        return best

    corpus.sort(key=lambda rel: (distance(rel) if review_files else 0, rel))
    return corpus, corpus[:SAMPLE_CAP]


def build_baseline(corpus, sampled, root):
    """5 机械键 {adopted, status}；2 判读键只标 judged_by: llm（裁定 3）。"""
    keys = {}
    for key in MECHANICAL_KEYS:
        patterns = KEY_PATTERNS[key]
        adopted = 0
        for rel in sampled:
            text = read_text(os.path.join(root, rel))
            if any(p.search(text) for p in patterns):
                adopted += 1
        keys[key] = {"adopted": adopted,
                     "status": convention_status(adopted, len(sampled))}
    for key in LLM_JUDGED_KEYS:
        keys[key] = {"judged_by": "llm"}
    return {"corpus_size": len(corpus), "sampled": len(sampled), "keys": keys,
            "baseline_unavailable": len(sampled) == 0}


def mechanical_scan(files, pacts, root):
    """机械集检出（裁定 6）：C1/C2/C3/H1/H5/H6/H7/H8/H9/L4。

    行级行报告命中行号；文件级行（FILE_LEVEL_ROWS）line 为 null。
    """
    found = []
    for rel in files:
        path = os.path.join(root, rel)
        text = read_text(path)
        lines = text.splitlines()
        maestro = is_maestro_flow(rel)
        for idx, line in enumerate(lines, 1):
            if C1_RE.search(line) and not _documented_reason(lines, idx):
                found.append({"row": "C1", "file": rel, "line": idx,
                              "note": "被禁用的用例：%s" % _short(line)})
            if C2_RE.search(line):
                found.append({"row": "C2", "file": rel, "line": idx,
                              "note": "聚焦标记会静默停用同文件其余用例：%s" % _short(line)})
            if any(rx.search(line) for rx in C3_RES):
                found.append({"row": "C3", "file": rel, "line": idx,
                              "note": "恒真断言无法失败：%s" % _short(line)})
            if H1_RE.search(line):
                found.append({"row": "H1", "file": rel, "line": idx,
                              "note": "裸计时器排序步骤：%s" % _short(line)})
            if maestro and H9_RE.search(line):
                found.append({"row": "H9", "file": rel, "line": idx,
                              "note": "flow 内联明文凭据（应走 ${ENV_VAR}）：%s" % _short(line)})
        if len(lines) > H5_MAX_LINES:
            found.append({"row": "H5", "file": rel, "line": None,
                          "note": "文件 %d 行，超过 %d 行上限" % (len(lines), H5_MAX_LINES)})
    found.extend(_pact_scan(pacts, root))
    return found


def _documented_reason(lines, idx):
    """C1 豁免：命中行或上一行有注释说明 / 行内 reason= （源"documented, still-true reason"）。"""
    for lineno in (idx, idx - 1):
        if 1 <= lineno <= len(lines):
            line = lines[lineno - 1]
            for marker in COMMENT_MARKERS:
                pos = line.find(marker)
                if pos >= 0 and line[pos + len(marker):].strip(" */\t") != "":
                    return True
            if C1_REASON_RE.search(line):
                return True
    return False


def _pact_scan(pacts, root):
    """pact vitest 配置行：H6（worker 并行）/ H7 与 L4（pool 隔离，按同对文件数分档）/ H8。

    R-4（源 step-03a §1b 违规发射规则末条）：配置经 `mergeConfig(` / `extends:` 组合时，
    三条必需设置可能落在不可跟随的基础配置里——literal 匹配只能得假阴性 ⇒ 不再冒充
    H6/H7，合一降为 L4 advisory（源逐字分类名 `pact-config-unverifiable`），给出两条
    出路（叶子配置内联 / `// tea:pact-ffi-safe` 标记）；带该标记即视为已验证，不报。
    H8 是显式击穿（本文件内的字面量），不受 mergeConfig 影响，照报。
    """
    found = []
    pacttest_count = 0
    for path in walk_files(root, None):
        if os.path.basename(path).endswith(PACT_FILE_SUFFIX):
            pacttest_count += 1
    for rel in pacts:
        text = read_text(os.path.join(root, rel))
        has_file_parallelism = re.search(r"\bfileParallelism\s*:\s*false\b", text)
        has_forks = (re.search(r"\bpool\s*:\s*['\"]forks['\"]", text)
                     and re.search(r"\bsingleFork\s*:\s*true\b", text))
        if MERGE_CONFIG_RE.search(text) and not (has_file_parallelism and has_forks):
            if FFI_SAFE_MARKER not in text:
                found.append({"row": "L4", "file": rel, "line": None,
                              "note": "pact-config-unverifiable：配置经 mergeConfig / "
                                      "extends 组合，三条必需设置的 literal 匹配不可验证"
                                      "（同对 .pacttest.ts %d 个）——在叶子配置内联 pool / "
                                      "singleFork / fileParallelism，或加 "
                                      "// %s 标记" % (pacttest_count, FFI_SAFE_MARKER)})
        else:
            if not has_file_parallelism:
                found.append({"row": "H6", "file": rel, "line": None,
                              "note": "配置缺 fileParallelism: false（并行 worker 争用共享 pact JSON）"})
            if not has_forks:
                row = "H7" if pacttest_count >= 2 else "L4"
                found.append({"row": row, "file": rel, "line": None,
                              "note": "配置缺 pool: 'forks' / singleFork: true"
                                      "（同对 .pacttest.ts %d 个）" % pacttest_count})
        if any(rx.search(text) for rx in (
                re.compile(r"\bsequence\s*:\s*\{[^}]*\bconcurrent\s*:\s*true"),
                re.compile(r"\bmaxConcurrency\s*:\s*([2-9]|\d{2,})"),
                re.compile(r"\bmaxWorkers\s*:\s*([2-9]|\d{2,})"),
                re.compile(r"\bisolate\s*:\s*false\b"))):
            found.append({"row": "H8", "file": rel, "line": None,
                          "note": "配置显式击穿序列化（concurrent / maxConcurrency / "
                                  "maxWorkers / isolate: false）"})
    return found


def _test_blocks(text):
    """逐个 `it(` / `test(` 块体（括号配平扫描）→ [(行号, 块体)]。"""
    blocks = []
    for match in TEST_BLOCK_RE.finditer(text):
        start, depth, i, quote = match.end() - 1, 0, match.end() - 1, None
        while i < len(text):
            char = text[i]
            if quote is not None:
                if char == "\\":
                    i += 2
                    continue
                if char == quote:
                    quote = None
            elif char in "\"'`":
                quote = char
            elif char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        blocks.append((text.count("\n", 0, match.start()) + 1, text[start:i + 1]))
    return blocks


def _pact_interaction_warnings(files, root):
    """R-4（源 step-03a §1b）：单 `it()` 内含 >1 `addInteraction()` → advisory。

    该条**无 registry row**（源列在四个 registry 身份之外）⇒ 只出 warning、不给
    severity、不进账本，由 03 步写进 `recommendations` 散文（来源：Rust FFI 非确定性
    丢 interaction）。单块内计数，避免多 it 文件被整片误判。
    """
    warnings = []
    for rel in files:
        if not rel.endswith(PACT_FILE_SUFFIX):
            continue
        for line, body in _test_blocks(read_text(os.path.join(root, rel))):
            count = len(ADD_INTERACTION_RE.findall(body))
            if count > 1:
                warnings.append(v("SET_MISMATCH", "%s:%d" % (rel, line),
                                  "单 it() 内 %d 个 addInteraction()：Rust FFI 会非确定性"
                                  "丢 interaction——一 interaction 一 it()（注册表无此行，"
                                  "写进 recommendations 散文）" % count))
    return warnings


def _content_warnings(files, root):
    """R-3：极简测试文件（有内容但零断言，源 "No meaningful tests"）→ warning。

    空文件已在发现面归 excluded（本表只收有内容的）；判定为**提示**不是计分：命中文件的
    C4 条目（CRITICAL）由 03 步判定产出，分数随账本反映内容缺失。
    """
    warnings = []
    for rel in files:
        if assertion_free(read_text(os.path.join(root, rel))):
            warnings.append(v("EMPTY_FIELD", rel,
                              "No meaningful tests：文件内零断言——按 C4 成条目"
                              "（note 用该锚串），分数须反映内容缺失"))
    return warnings


def _short(text, limit=60):
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[:limit - 1] + "…"


def pact_config_paths(root, out, pacts):
    """pact vitest 配置发现：显式进面者优先，另扫 project-root（排除 output_dir 等）。"""
    found = list(pacts)
    for path in walk_files(root, os.path.normcase(os.path.abspath(out))):
        rel = os.path.relpath(path, root).replace("\\", "/")
        if is_pact_config(rel) and rel not in found:
            found.append(rel)
    return sorted(found)


# ---------------------------------------------------------------- diyc 委派

def diyc_script_path():
    """diyc.py 路径：由引擎自身位置推算 skills 根（源码与安装布局同构，任务书 §2.3）。"""
    skills_root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    return os.path.join(skills_root, *DIYC_REL)


def diyc_call(script, args_list):
    """跑 diyc 子命令。rc∈{0,1} = 正常回执；rc=2/不可解析/缺席 → (None, warning)。"""
    where = "diyc.py %s" % " ".join(args_list[0:1] + args_list[-2:])
    cmd = [sys.executable, script] + args_list
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              encoding="utf-8", errors="replace")
    except OSError as e:
        return None, v("TOOL_ERROR", where, "diyc 子进程无法启动：%s" % e)
    if proc.returncode not in (0, 1):
        tail = " ".join((proc.stderr or proc.stdout or "").split())[-200:]
        return None, v("TOOL_ERROR", where,
                       "diyc 非预期退出码 %s（期望 0|1）：%s"
                       % (proc.returncode, tail or "无输出"))
    for line in reversed((proc.stdout or "").splitlines()):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except ValueError:
            continue
        if isinstance(payload, dict):
            return payload, None
    return None, v("TOOL_ERROR", where, "diyc 回执不可解析（--json 面单行 JSON 缺失）")


def delegation_ready(script, project_root):
    if not os.path.isfile(script):
        return False, v("TOOL_MISSING", display_path(script, project_root),
                        "diyc.py 缺席：跨文档核对降级，请从会话侧人工复核")
    return True, None


# ---------------------------------------------------------------- scan

def cmd_scan(args):
    root = os.path.abspath(args.project_root)
    out = os.path.abspath(args.output_dir)
    criteria = load_criteria()
    files, excluded, pacts, warnings = discover_scope(args, root, out)
    files = sorted(files)
    payload = {"ok": False, "command": "scan", "project_root": args.project_root,
               "output_dir": os.path.normpath(out).replace("\\", "/"),
               "files": files, "excluded": sorted(excluded, key=lambda e: e["path"]),
               "mechanical": [], "baseline": {}, "violations": [], "warnings": warnings,
               "counts": {}}

    if not files:
        # 门禁（源"无测试文件 → Halt"）：零产出 + 一行路由
        payload["violations"] = [v(
            "MISSING_FILE", display_path(out, root) + "/<测试文件>",
            "scope 内未发现测试文件：先给 --paths 指定测试文件/目录，或先跑 "
            "diy-test-author 产出测试代码；匹配不到任何规则得到的 100 不是 100")]
        payload["counts"] = {"files": 0, "excluded": len(excluded), "mechanical": 0}
        emit(payload, args.json, human_scan)
        return 1

    pacts = pact_config_paths(root, out, pacts)
    mechanical = mechanical_scan(files, pacts, root)
    mechanical = [m for m in mechanical
                  if criteria.get(m["row"], {}).get("detect") == "mechanical"]
    warnings.extend(_content_warnings(files, root))
    warnings.extend(_pact_interaction_warnings(files, root))
    corpus, sampled = build_corpus(files, root, out)
    baseline = build_baseline(corpus, sampled, root)
    if baseline["baseline_unavailable"]:
        warnings.append(v("EMPTY_FIELD", "convention_baseline",
                          "评审集之外无语料：7 个惯例键全部 unknown，Convention 行一律 "
                          "PASS (n/a)（不得从评审文件自身推断惯例）"))
    # 机械集完整性（裁定 6：可扩不可缩）：criteria 声明的 mechanical 行必须都有引擎实现
    declared = {r for r, spec in criteria.items() if spec.get("detect") == "mechanical"}
    missing = sorted(declared - IMPLEMENTED_MECHANICAL)
    if missing:
        warnings.append(v("ENUM_INVALID", "criteria.yaml mechanical 集",
                          "声明的机械行无引擎实现（须补实现或回报登记）：%s"
                          % "、".join(missing)))

    payload["ok"] = True
    payload["mechanical"] = mechanical
    payload["baseline"] = baseline
    payload["counts"] = {"files": len(files), "excluded": len(excluded),
                         "mechanical": len(mechanical),
                         "pact_configs": len(pacts),
                         "corpus_size": baseline["corpus_size"],
                         "sampled": baseline["sampled"],
                         "by_row": _count_rows(mechanical)}
    emit(payload, args.json, human_scan)
    return 0


def _count_rows(entries):
    counts = {}
    for entry in entries:
        counts[entry["row"]] = counts.get(entry["row"], 0) + 1
    return counts


def human_scan(payload):
    if not payload["ok"]:
        for item in payload["violations"]:
            print("拒绝 %s %s: %s" % (item["code"], item["where"], item["msg"]))
        return
    counts = payload["counts"]
    print("扫描完成：测试文件 %d 个（excluded %d，pact 配置 %d，机械项 %d 条）"
          % (counts["files"], counts["excluded"], counts["pact_configs"],
             counts["mechanical"]))
    for entry in payload["mechanical"]:
        where = entry["file"] if entry["line"] is None else "%s:%d" % (entry["file"], entry["line"])
        print("- %s %s：%s" % (entry["row"], where, entry["note"]))
    baseline = payload["baseline"]
    print("惯例语料：%d 个（采样 %d）" % (baseline["corpus_size"], baseline["sampled"]))
    for key in CONVENTION_KEYS:
        entry = baseline["keys"][key]
        if "status" in entry:
            print("- %s: adopted=%d status=%s" % (key, entry["adopted"], entry["status"]))
        else:
            print("- %s: judged_by=llm（读采样文件判读，入产物 convention_baseline）" % key)
    for item in payload["warnings"]:
        print("警告 %s %s: %s" % (item["code"], item["where"], item["msg"]))


# ---------------------------------------------------------------- score

def _finding_violations(raw, table):
    """逐条 finding 的入口校验 → (violations, [规范化 finding])。severity 不在输入面。"""
    violations, plain = [], []
    if not isinstance(raw, list):
        return [v("EMPTY_FIELD", "findings", "findings 不是列表")], []
    for i, item in enumerate(raw):
        where = "findings[%d]" % i
        if not isinstance(item, dict):
            violations.append(v("EMPTY_FIELD", where, "finding 不是映射"))
            continue
        row = item.get("row")
        spec = table.get(str(row)) if nonempty(row) else None
        if spec is None:
            violations.append(v("ENUM_INVALID", where + ".row",
                                "row 越界：%s（须为 criteria.yaml 有效行）" % row))
            continue
        if spec.get("disabled"):
            violations.append(v("ENUM_INVALID", where + ".row",
                                "row=%s 已 disabled 留档（私有库绑定裁剪），不得成条目" % row))
            continue
        if not nonempty(item.get("file")):
            violations.append(v("EMPTY_FIELD", where + ".file", "file 缺失"))
            continue
        line = item.get("line")
        if str(row) in FILE_LEVEL_ROWS:
            if line is not None:
                violations.append(v("ENUM_INVALID", where + ".line",
                                    "文件级行 %s 的 line 须为 null（以 file 取代行号）" % row))
                continue
        elif not isinstance(line, int) or isinstance(line, bool) or line < 1:
            violations.append(v("ENUM_INVALID", where + ".line",
                                "行级行的 line 须为正整数（实为 %s）" % line))
            continue
        klass = item.get("class")
        if spec.get("basis") == "convention":
            if not nonempty(klass):
                violations.append(v("EMPTY_FIELD", where + ".class",
                                    "convention 行须带 class（established|emerging）"))
                continue
            if str(klass) not in CONVENTION_ENTRY_STATUSES:
                violations.append(v("ENUM_INVALID", where + ".class",
                                    "class=%s 时该行不成立、不得成条目（absent / unknown 系 "
                                    "scan 内部判定值）" % klass))
                continue
        elif nonempty(klass):
            violations.append(v("ENUM_INVALID", where + ".class",
                                "class 仅 basis=convention 行可带（%s 是 %s 行）"
                                % (row, spec.get("basis"))))
            continue
        severity = downgrade_severity(str(spec.get("severity")), str(klass))
        plain.append({"row": str(row), "file": str(item["file"]),
                      "line": None if line is None else int(line),
                      "class": str(klass) if nonempty(klass) else None,
                      "severity": severity})
    return violations, plain


def _dedupe(plain):
    """按 file:location:row 去重（文件级行以 file 取代行号）；去重在计分之前。"""
    seen, out, duplicates = set(), [], 0
    for item in plain:
        location = "file" if item["row"] in FILE_LEVEL_ROWS else item["line"]
        key = "%s:%s:%s" % (item["file"], location, item["row"])
        if key in seen:
            duplicates += 1
            continue
        seen.add(key)
        out.append(item)
    return out, duplicates


def _severity_counts(deduped):
    counts = {sev: 0 for sev in SEVERITIES}
    for item in deduped:
        counts[item["severity"]] += 1
    return counts


def _bonus_violations(raw, deduped, table):
    violations, applied, total = [], [], 0
    if raw is None:
        raw = []
    if not isinstance(raw, list):
        return [v("EMPTY_FIELD", "bonus", "bonus 不是列表")], applied, total
    guards = bonus_guard_map(table)
    hit_rows = {item["row"] for item in deduped}
    for i, item in enumerate(raw):
        where = "bonus[%d]" % i
        if not isinstance(item, dict):
            violations.append(v("EMPTY_FIELD", where, "bonus 项不是映射"))
            continue
        key = item.get("key")
        if not nonempty(key) or str(key) not in BONUS_KEYS:
            violations.append(v("ENUM_INVALID", where + ".key",
                                "key 越界：%s（合法集 %s）"
                                % (key, "|".join(BONUS_KEYS))))
            continue
        points = item.get("points")
        if points not in (0, BONUS_POINTS) or isinstance(points, bool):
            violations.append(v("ENUM_INVALID", where + ".points",
                                "points 只许 0 或 %d（无部分分），实为 %s"
                                % (BONUS_POINTS, points)))
            continue
        if points == BONUS_POINTS:
            conflicted = sorted(guards.get(str(key), set()) & hit_rows)
            if conflicted:
                violations.append(v("SET_MISMATCH", where,
                                    "矛盾复核：%s 得 %d 分，但对应规则行在 findings 中命中"
                                    "（%s）" % (key, BONUS_POINTS, "、".join(conflicted))))
                continue
            applied.append(str(key))
            total += points
    if total > BONUS_MAX:
        violations.append(v("SET_MISMATCH", "bonus",
                            "bonus 合计 %d 超过上限 %d" % (total, BONUS_MAX)))
    return violations, applied, total


def _dimension_scores(deduped, table):
    scores = {}
    for dim in DIMENSIONS:
        penalty = 0
        for item in deduped:
            spec = table.get(item["row"], {})
            if dim in (spec.get("dimensions") or []):
                penalty += DIMENSION_WEIGHTS[item["severity"]]
        scores[dim] = max(0, 100 - penalty)
    return scores


def compute_ledger(findings_doc, table):
    """账本纯函数（裁定 1）：入口校验 → severity 复算 → 去重 → 账本 + 维度分。"""
    violations, plain = _finding_violations(items(findings_doc, "findings"), table)
    deduped, duplicates = _dedupe(plain)
    counts = _severity_counts(deduped)
    ded_total = sum(counts[sev] * DEDUCTION_WEIGHTS[sev] for sev in SEVERITIES)
    bonus_violations, applied, bonus_total = _bonus_violations(
        findings_doc.get("bonus") if isinstance(findings_doc, dict) else None,
        deduped, table)
    violations += bonus_violations
    score = clamp_score(100 - ded_total + bonus_total)
    return {
        "violations": violations,
        "deductions": {"critical": counts["CRITICAL"], "high": counts["HIGH"],
                       "medium": counts["MEDIUM"], "low": counts["LOW"],
                       "total": ded_total},
        "bonus": {"applied": applied, "total": bonus_total},
        "dimensions": _dimension_scores(deduped, table),
        "score": score,
        "grade": grade_of(score),
        "recommendation": recommend_of(counts, score),
        "counts": {"findings": len(items(findings_doc, "findings")),
                   "deduped": len(deduped), "duplicates": duplicates,
                   "by_severity": {k: val for k, val in counts.items() if val}},
    }


def cmd_score(args):
    criteria = load_criteria()
    root = os.path.abspath(args.project_root)
    out = os.path.abspath(args.output_dir)
    path = args.findings if os.path.isabs(args.findings) \
        else os.path.join(root, args.findings)
    show = display_path(path, root)
    payload = {"ok": False, "command": "score", "project_root": args.project_root,
               "output_dir": os.path.normpath(out).replace("\\", "/"),
               "deductions": {}, "bonus": {}, "dimensions": {}, "score": None,
               "grade": None, "recommendation": None,
               "violations": [], "warnings": [], "counts": {}}
    findings_doc, err = load_yaml_safe(path) if path.endswith(".yaml") else _load_json(path)
    if findings_doc is None and err is None:
        payload["violations"] = [v("MISSING_FILE", show,
                                   "findings.json 不存在（03 步先产出 findings 载体）")]
        emit(payload, args.json, human_score)
        return 1
    if err is not None:
        payload["violations"] = [v("UNPARSABLE_YAML", show, "findings 载体解析失败：%s" % err)]
        emit(payload, args.json, human_score)
        return 1
    if not isinstance(findings_doc, dict):
        payload["violations"] = [v("EMPTY_FIELD", show, "findings 载体顶层不是映射")]
        emit(payload, args.json, human_score)
        return 1
    ledger = compute_ledger(findings_doc, criteria)
    payload.update({k: ledger[k] for k in ("deductions", "bonus", "dimensions", "score",
                                           "grade", "recommendation", "counts")})
    payload["violations"] = ledger["violations"]
    payload["ok"] = not ledger["violations"]
    emit(payload, args.json, human_score)
    return 0 if payload["ok"] else 1


def _load_json(path):
    if not os.path.isfile(path):
        return None, None
    try:
        with io.open(path, "r", encoding="utf-8") as f:
            return json.load(f), None
    except (ValueError, OSError) as e:
        return None, str(e)


def human_score(payload):
    if not payload["ok"]:
        for item in payload["violations"]:
            print("拒绝 %s %s: %s" % (item["code"], item["where"], item["msg"]))
        return
    d = payload["deductions"]
    print("账本：CRITICAL %d / HIGH %d / MEDIUM %d / LOW %d → 扣分 %d；bonus %d"
          % (d["critical"], d["high"], d["medium"], d["low"], d["total"],
             payload["bonus"]["total"]))
    print("评分：%d（%s）→ %s" % (payload["score"], payload["grade"],
                                payload["recommendation"]))
    print("维度：" + " ".join("%s=%d" % (k, val)
                              for k, val in payload["dimensions"].items()))


# ---------------------------------------------------------------- walkthrough

def load_final_doc(out_dir, filename):
    """读须定稿的产物 → (ok, data, violation_or_None)。ok = 在场 + 可解析 + status: final。"""
    path = os.path.join(out_dir, filename)
    data, err = load_yaml_safe(path)
    if data is None and err is None:
        return False, None, v("MISSING_FILE", filename, "%s 缺失" % filename)
    if err is not None:
        return False, None, v("UNPARSABLE_YAML", filename, "%s 解析失败：%s" % (filename, err))
    project = data.get("project") if isinstance(data, dict) else None
    status = project.get("status") if isinstance(project, dict) else None
    if status != "final":
        return False, None, v("STATUS_MISMATCH", filename + " project.status",
                              "%s 未定稿（实为 %s）" % (filename,
                                                    status if nonempty(status) else "未声明"))
    return True, data, None


def _ac_ids(stories_doc):
    ids = []
    for story in items(stories_doc, "stories"):
        if not isinstance(story, dict):
            continue
        for ac in items(story, "acceptance_criteria"):
            if isinstance(ac, dict) and nonempty(ac.get("id")):
                ids.append(str(ac["id"]))
    return ids


def _tc_entries(test_plan_doc):
    out = []
    for tc in items(test_plan_doc, "test_cases"):
        if not isinstance(tc, dict) or not nonempty(tc.get("id")):
            continue
        out.append({"id": str(tc["id"]), "ac": tc.get("ac"),
                    "status": tc.get("status")})
    return out


def cmd_walkthrough(args):
    root = os.path.abspath(args.project_root)
    out = os.path.abspath(args.output_dir)
    warnings, gaps = [], {kind: [] for kind in GAP_KINDS}
    evaluated, skipped = set(), []

    stories_ok, stories_doc, stories_err = load_final_doc(out, STORIES_FILE)
    tp_ok, tp_doc, tp_err = load_final_doc(out, TEST_PLAN_FILE)
    for err in (stories_err, tp_err):
        if err is not None:
            warnings.append(err)

    script = diyc_script_path()
    ready, warn = delegation_ready(script, root)
    trace_payload = check_payload = None
    if ready:
        trace_payload, trace_warn = diyc_call(
            script, ["trace", "--project-root", root, "--json"])
        if trace_warn is not None:
            warnings.append(trace_warn)
        check_payload, check_warn = diyc_call(
            script, ["check", "--type", "test-plan", "--final",
                     "--project-root", root, "--json"])
        if check_warn is not None:
            warnings.append(check_warn)
        for payload in (trace_payload, check_payload):
            resolved = payload.get("output_dir") if isinstance(payload, dict) else None
            if nonempty(resolved):
                a = os.path.normcase(os.path.abspath(os.path.join(root, str(resolved))))
                if a != os.path.normcase(out):
                    warnings.append(v("SET_MISMATCH", str(resolved),
                                      "diyc 解析的产物目录与本引擎 --output-dir 不一致："
                                      "跨文档证据可能来自另一目录"))
    else:
        warnings.append(warn)

    # ① no_impl：AC 从未出现在 trace 引用的 AC ID 中（护栏：全量零 trace → 整类跳过）
    if stories_ok and trace_payload is not None:
        files_with_trace = (trace_payload.get("counts") or {}).get("files_with_trace", 0)
        if not files_with_trace:
            skipped.append("no_impl")
            warnings.append(v("EMPTY_FIELD", "diyc trace",
                              "项目全量零 trace 标记（files_with_trace==0）：实现面不可判，"
                              "no_impl 类整体跳过"))
        else:
            referenced = set()
            for ref in trace_payload.get("references") or []:
                if isinstance(ref, dict):
                    for id_ in ref.get("ids") or []:
                        if AC_RE.fullmatch(str(id_)):
                            referenced.add(str(id_))
            for ac in _ac_ids(stories_doc):
                if ac not in referenced:
                    gaps["no_impl"].append({
                        "kind": "no_impl", "ref": ac, "route": "diy-dev",
                        "note": "AC 从未出现在 # trace: 引用的 AC ID 中（实现面无可判证据）"})
            evaluated.add("no_impl")
            unresolved = trace_payload.get("unresolved") or []
            if unresolved:
                warnings.append(v("TRACE_UNRESOLVED", "diyc trace",
                                  "trace 引用了 %d 处不可解析 ID（不属四类缺口，须人工复核）"
                                  % len(unresolved)))
    else:
        skipped.append("no_impl")

    # ② no_test：AC 无 TC 绑定，或绑定的 TC 全为 pending
    if stories_ok and tp_ok:
        tcs = _tc_entries(tp_doc)
        for ac in _ac_ids(stories_doc):
            bound = [tc for tc in tcs if str(tc["ac"]) == ac]
            if not bound:
                gaps["no_test"].append({
                    "kind": "no_test", "ref": ac, "route": "diy-test-design",
                    "note": "AC 无任何 TC 绑定"})
            elif all(str(tc["status"]) == "pending" for tc in bound):
                gaps["no_test"].append({
                    "kind": "no_test", "ref": ac, "route": "diy-test-author",
                    "note": "AC 的 TC 全部 pending（有 TC 未落地）：%s"
                            % "、".join(tc["id"] for tc in bound)})
        evaluated.add("no_test")
    else:
        skipped.append("no_test")

    # ③ orphan_tc：TC 的 ac 不可解析（委派 diyc check --type test-plan 的 ac-UNKNOWN_ID 转记）
    if tp_ok and stories_ok and check_payload is not None:
        others = 0
        for item in check_payload.get("violations") or []:
            if not isinstance(item, dict):
                continue
            where = str(item.get("where") or "")
            match = re.search(r"test_cases\[([^\]]+)\]\.ac(?:\[\d+\])?$", where)
            if item.get("code") == "UNKNOWN_ID" and match:
                gaps["orphan_tc"].append({
                    "kind": "orphan_tc", "ref": match.group(1), "route": "user",
                    "note": "TC 的 ac 不可解析：%s（%s）"
                            % (item.get("msg"), display_path(
                                os.path.join(out, TEST_PLAN_FILE), root))})
            else:
                others += 1
        if others:
            warnings.append(v("ENUM_INVALID", "diyc check --type test-plan",
                              "另报 %d 条非 ac 违规（不属本技能走查面，未吞掉）" % others))
        evaluated.add("orphan_tc")
    else:
        skipped.append("orphan_tc")

    # ④ never_run：TC status: pending
    if tp_ok:
        for tc in _tc_entries(tp_doc):
            if str(tc["status"]) == "pending":
                gaps["never_run"].append({
                    "kind": "never_run", "ref": tc["id"], "route": "diy-test-author",
                    "note": "TC 尚未激活/复跑（status: pending）"})
        evaluated.add("never_run")
    else:
        skipped.append("never_run")

    if not evaluated:
        status = "skipped"
    elif skipped:
        status = "partial"
    else:
        status = "full"
    if skipped:
        warnings.append(v("PENDING_DECISION", "walkthrough",
                          "跳过类：%s（就绪态 %s，原因见上方 warning）"
                          % ("、".join(skipped), status)))
    payload = {"ok": True, "command": "walkthrough", "project_root": args.project_root,
               "output_dir": os.path.normpath(out).replace("\\", "/"),
               "status": status, "gaps": gaps, "violations": [], "warnings": warnings,
               "counts": {kind: len(gaps[kind]) for kind in GAP_KINDS}}
    payload["counts"].update({"evaluated": len(evaluated), "skipped": len(skipped)})
    emit(payload, args.json, human_walkthrough)
    return 0


def human_walkthrough(payload):
    print("三向走查：%s（缺口 %s）"
          % (payload["status"],
             " ".join("%s=%d" % (k, val) for k, val in payload["counts"].items()
                      if k in GAP_KINDS)))
    for kind in GAP_KINDS:
        for gap in payload["gaps"][kind]:
            print("- %s %s → %s：%s" % (gap["kind"], gap["ref"], gap["route"], gap["note"]))
    for item in payload["warnings"]:
        print("警告 %s %s: %s" % (item["code"], item["where"], item["msg"]))


# ---------------------------------------------------------------- check

def _check_scope(record, where, final):
    violations = []
    scope = record.get("scope")
    if not isinstance(scope, dict):
        return [v("EMPTY_FIELD", where + ".scope", "scope 缺失（paths / files_reviewed / excluded）")]
    paths = scope.get("paths")
    if not isinstance(paths, list):
        violations.append(v("EMPTY_FIELD", where + ".scope.paths", "paths 缺失或不是列表"))
    else:
        for i, p in enumerate(paths):
            if not nonempty(p):
                violations.append(v("EMPTY_FIELD", "%s.scope.paths[%d]" % (where, i),
                                    "paths 项为空"))
        if final and not paths:
            violations.append(v("EMPTY_FIELD", where + ".scope.paths",
                                "--final 要求 scope.paths 非空（scope 非空义务）"))
    reviewed = scope.get("files_reviewed")
    if not isinstance(reviewed, int) or isinstance(reviewed, bool) or reviewed < 0:
        violations.append(v("ENUM_INVALID", where + ".scope.files_reviewed",
                            "files_reviewed 须为非负整数（实为 %s）" % reviewed))
    excluded = scope.get("excluded")
    if not isinstance(excluded, list):
        violations.append(v("EMPTY_FIELD", where + ".scope.excluded",
                            "excluded 缺失或不是列表（无排除写空列表）"))
    else:
        for i, entry in enumerate(excluded):
            ew = "%s.scope.excluded[%d]" % (where, i)
            if not isinstance(entry, dict) or not nonempty(entry.get("path")):
                violations.append(v("EMPTY_FIELD", ew, "excluded 项须带 path"))
                continue
            reason = entry.get("reason")
            if not nonempty(reason):
                violations.append(v("EMPTY_FIELD", ew + ".reason", "reason 缺失"))
            elif str(reason) not in EXCLUDED_REASONS:
                violations.append(v("ENUM_INVALID", ew + ".reason",
                                    "reason 越界：%s（合法集 %s）"
                                    % (reason, "|".join(EXCLUDED_REASONS))))
    return violations


def _check_findings(record, where, table):
    """artifact findings 校验 + 引擎复算（severity / 行号身份 / row ∈ 有效 32 行）。"""
    violations = []
    findings = record.get("findings")
    if not isinstance(findings, list):
        return [v("EMPTY_FIELD", where + ".findings", "findings 缺失或不是列表")], []
    valid = valid_rows(table)
    plain = []
    for i, item in enumerate(findings):
        fw = "%s.findings[%d]" % (where, i)
        if not isinstance(item, dict):
            violations.append(v("EMPTY_FIELD", fw, "finding 不是映射"))
            continue
        row = item.get("row")
        if not nonempty(row) or str(row) not in valid:
            violations.append(v("ENUM_INVALID", fw + ".row",
                                "row 越界：%s（须为有效 32 行；disabled 行 M9/M10/L9 不得出现）"
                                % row))
            continue
        spec = table[str(row)]
        if not nonempty(item.get("file")):
            violations.append(v("EMPTY_FIELD", fw + ".file", "file 缺失"))
            continue
        if not nonempty(item.get("note")):
            violations.append(v("EMPTY_FIELD", fw + ".note", "note 为空（发现须能说清命中什么）"))
            continue
        basis = item.get("basis")
        if nonempty(basis) and str(basis) != str(spec.get("basis")):
            violations.append(v("SET_MISMATCH", fw + ".basis",
                                "声明 basis=%s 与 criteria.yaml 的 %s 不符"
                                % (basis, spec.get("basis"))))
            continue
        line = item.get("line")
        if str(row) in FILE_LEVEL_ROWS:
            if line is not None:
                violations.append(v("ENUM_INVALID", fw + ".line",
                                    "文件级行 %s 的 line 须为 null" % row))
                continue
        elif not isinstance(line, int) or isinstance(line, bool) or line < 1:
            violations.append(v("ENUM_INVALID", fw + ".line",
                                "行级行的 line 须为正整数（实为 %s）" % line))
            continue
        klass = item.get("class")
        if spec.get("basis") == "convention":
            if str(klass) not in CONVENTION_ENTRY_STATUSES:
                violations.append(v("ENUM_INVALID", fw + ".class",
                                    "convention 行的 class 须为 established|emerging（实为 %s）"
                                    % klass))
                continue
        elif nonempty(klass):
            violations.append(v("ENUM_INVALID", fw + ".class",
                                "class 仅 basis=convention 行可带（%s 是 %s 行）"
                                % (row, spec.get("basis"))))
            continue
        expected = downgrade_severity(str(spec.get("severity")), str(klass))
        declared = item.get("severity")
        if str(declared) != expected:
            violations.append(v("SET_MISMATCH", fw + ".severity",
                                "声明 %s 与引擎复算 %s 不符（row=%s，class=%s）"
                                % (declared, expected, row, klass)))
            continue
        plain.append({"row": str(row), "file": str(item["file"]),
                      "line": None if line is None else int(line),
                      "class": str(klass) if nonempty(klass) else None,
                      "severity": expected})
    return violations, plain


def _check_score_block(record, where, deduped, table):
    """账本自洽：findings 计数 → deductions → score/grade/recommendation → 维度分。"""
    violations = []
    block = record.get("score")
    if not isinstance(block, dict):
        return [v("EMPTY_FIELD", where + ".score", "score 区块缺失（五键由 score 命令复算）")]
    counts = _severity_counts(deduped)
    expect_total = sum(counts[sev] * DEDUCTION_WEIGHTS[sev] for sev in SEVERITIES)
    deductions = block.get("deductions")
    if not isinstance(deductions, dict):
        violations.append(v("EMPTY_FIELD", where + ".score.deductions", "deductions 缺失"))
        deductions = {}
    else:
        for key, sev in (("critical", "CRITICAL"), ("high", "HIGH"),
                         ("medium", "MEDIUM"), ("low", "LOW")):
            if deductions.get(key) != counts[sev]:
                violations.append(v("SET_MISMATCH", "%s.score.deductions.%s" % (where, key),
                                    "声明 %s 与 findings 计数 %d 不符"
                                    % (deductions.get(key), counts[sev])))
        if deductions.get("total") != expect_total:
            violations.append(v("SET_MISMATCH", where + ".score.deductions.total",
                                "行相加 %s 与实际 %d 不符（CRITICAL*10 + HIGH*5 + "
                                "MEDIUM*2 + LOW*1）"
                                % (deductions.get("total"), expect_total)))

    bonus_block = block.get("bonus")
    applied = []
    bonus_total = 0
    if not isinstance(bonus_block, dict):
        violations.append(v("EMPTY_FIELD", where + ".score.bonus", "bonus 缺失"))
    else:
        applied = [str(k) for k in (bonus_block.get("applied") or [])]
        for key in applied:
            if key not in BONUS_KEYS:
                violations.append(v("ENUM_INVALID", where + ".score.bonus.applied",
                                    "bonus 键越界：%s（合法集 %s）"
                                    % (key, "|".join(BONUS_KEYS))))
        bonus_total = len(applied) * BONUS_POINTS
        if bonus_block.get("total") != bonus_total:
            violations.append(v("SET_MISMATCH", where + ".score.bonus.total",
                                "声明 %s 与 applied 数 × %d = %d 不符"
                                % (bonus_block.get("total"), BONUS_POINTS, bonus_total)))
        if bonus_total > BONUS_MAX:
            violations.append(v("SET_MISMATCH", where + ".score.bonus",
                                "bonus 合计 %d 超过上限 %d" % (bonus_total, BONUS_MAX)))
        guards = bonus_guard_map(table)
        hit_rows = {item["row"] for item in deduped}
        for key in applied:
            conflicted = sorted(guards.get(key, set()) & hit_rows)
            if conflicted:
                violations.append(v("SET_MISMATCH", "%s.score.bonus.applied" % where,
                                    "矛盾复核：%s 得 %d 分，但对应规则行有命中（%s）"
                                    % (key, BONUS_POINTS, "、".join(conflicted))))

    expected_score = clamp_score(100 - expect_total + bonus_total)
    if block.get("score") != expected_score:
        violations.append(v("SET_MISMATCH", where + ".score.score",
                            "声明 %s 与账本 %d 不符（clamp(100 - deductions + bonus, 0, 100)）"
                            % (block.get("score"), expected_score)))
    if block.get("grade") != grade_of(expected_score):
        violations.append(v("SET_MISMATCH", where + ".score.grade",
                            "声明 %s 与分档 %s 不符（A≥90/B≥80/C≥70/D≥60/F<60）"
                            % (block.get("grade"), grade_of(expected_score))))
    expected_rec = recommend_of(counts, expected_score)
    if block.get("recommendation") != expected_rec:
        violations.append(v("SET_MISMATCH", where + ".score.recommendation",
                            "声明 %s 与推导 %s 不符（recommendation 由计算得出）"
                            % (block.get("recommendation"), expected_rec)))

    dims = record.get("dimensions")
    expected_dims = _dimension_scores(deduped, table)
    if not isinstance(dims, dict):
        violations.append(v("EMPTY_FIELD", where + ".dimensions", "dimensions 缺失"))
    else:
        for dim in DIMENSIONS:
            if dims.get(dim) != expected_dims[dim]:
                violations.append(v("SET_MISMATCH", "%s.dimensions.%s" % (where, dim),
                                    "声明 %s 与复算 %d 不符（每维 = max(0, 100 − Σ该维命中权重))"
                                    % (dims.get(dim), expected_dims[dim])))
    return violations


def _check_gaps(record, where):
    """coverage_gaps 形态：kind 四值 / ref 与 kind 配型 / route ∈ 该 kind 合法集。"""
    violations = []
    gaps = record.get("coverage_gaps")
    if not isinstance(gaps, list):
        return [v("EMPTY_FIELD", where + ".coverage_gaps",
                  "coverage_gaps 缺失或不是列表（无缺口写空列表）")]
    for i, gap in enumerate(gaps):
        gw = "%s.coverage_gaps[%d]" % (where, i)
        if not isinstance(gap, dict):
            violations.append(v("EMPTY_FIELD", gw, "缺口项不是映射"))
            continue
        kind = gap.get("kind")
        ref = gap.get("ref")
        if not nonempty(kind) or str(kind) not in GAP_KINDS:
            violations.append(v("ENUM_INVALID", gw + ".kind",
                                "kind 越界：%s（合法集 %s）" % (kind, "|".join(GAP_KINDS))))
            continue
        pattern = AC_RE if GAP_REF_KINDS[str(kind)] == "ac" else TC_RE
        if not nonempty(ref) or not pattern.fullmatch(str(ref)):
            violations.append(v("SET_MISMATCH", gw + ".ref",
                                "%s 的 ref 须为 %s（实为 %s）"
                                % (kind, "AC-x.y" if GAP_REF_KINDS[str(kind)] == "ac"
                                   else "TC-x.y.z", ref)))
        route = gap.get("route")
        if not nonempty(route):
            violations.append(v("EMPTY_FIELD", gw + ".route", "route 缺失（建议路由必填）"))
        elif str(route) not in GAP_ROUTES[str(kind)]:
            violations.append(v("ENUM_INVALID", gw + ".route",
                                "%s 的 route 越界：%s（合法集 %s）"
                                % (kind, route, "|".join(GAP_ROUTES[str(kind)]))))
        if not nonempty(gap.get("note")):
            violations.append(v("EMPTY_FIELD", gw + ".note", "note 为空"))
    return violations


def _check_walkthrough(record, where, gaps):
    """walkthrough 自洽：skipped → 缺口必空且 note 非空；partial → note 非空。"""
    violations = []
    block = record.get("walkthrough")
    if not isinstance(block, dict):
        return [v("EMPTY_FIELD", where + ".walkthrough", "walkthrough 区块缺失（status / note）")]
    status = block.get("status")
    note = block.get("note")
    if not nonempty(status) or str(status) not in WALKTHROUGH_STATUSES:
        violations.append(v("ENUM_INVALID", where + ".walkthrough.status",
                            "status 越界：%s（合法集 %s）"
                            % (status, "|".join(WALKTHROUGH_STATUSES))))
        return violations
    if str(status) == "skipped" and gaps:
        violations.append(v("SET_MISMATCH", where + ".walkthrough",
                            "status=skipped 但 coverage_gaps 非空（%d 条）" % len(gaps)))
    if str(status) in ("skipped", "partial") and not nonempty(note):
        violations.append(v("EMPTY_FIELD", where + ".walkthrough.note",
                            "status=%s 时 note 须记缺源与跳过类" % status))
    return violations


def _check_convention_citation(record, where, deduped, table):
    """R-2：convention finding 的 `class` 与 `convention_baseline.keys.<key>.status` 复核。

    源 step-02 §2b 的 CLI 口径逐字：报告里的 `Convention: <key> (<adopted> of <sampled>)`
    引用要与实际测量过的语料对得上，**对不上即拒**（"rejects a report that disagrees"）。
    diy 侧引用面 = finding 的 `class`，测量面 = 产物的 `convention_baseline`；键映射承载于
    criteria.yaml 行字段 `convention_key`（L2→priority_markers / L3→test_ids /
    L5→bdd_naming / L7→assertion_style）。三类拒绝：基线缺该键（引用不可核）、
    status 为 absent/unknown（该行本不成立、不得成条目）、class 与 status 不符。
    """
    violations = []
    keyed = [item for item in deduped
             if table.get(item["row"], {}).get("basis") == "convention"]
    if not keyed:
        return violations
    baseline = record.get("convention_baseline")
    keys = baseline.get("keys") if isinstance(baseline, dict) else None
    for item in keyed:
        key = table[item["row"]].get("convention_key")
        if not nonempty(key):
            continue  # 注册表未挂键 ⇒ 不可核（该缺口由 criteria 面测试钉住）
        entry = keys.get(str(key)) if isinstance(keys, dict) else None
        status = entry.get("status") if isinstance(entry, dict) else None
        at = "%s.findings[row=%s].class" % (where, item["row"])
        if not nonempty(status):
            violations.append(v("EMPTY_FIELD", at,
                                "convention 引用不可核：convention_baseline.keys.%s.status "
                                "缺席（引用与实际语料独立复测）" % key))
            continue
        if str(status) not in CONVENTION_ENTRY_STATUSES:
            violations.append(v("SET_MISMATCH", at,
                                "基线测到 %s=%s → 该行不成立、不得成条目（引用与实际语料不符）"
                                % (key, status)))
            continue
        if str(item["class"]) != str(status):
            violations.append(v("SET_MISMATCH", at,
                                "声明 class=%s 与 convention_baseline.keys.%s.status=%s 不符"
                                "（引用与实际语料独立复测）"
                                % (item["class"], key, status)))
    return violations


def _check_recommendations(record, where):
    """R-1：`recommendations` 为列表且不超过 Top 10（源 step-03f §4）。

    排序判据（所在维度分 < 70 → HIGH 优先）需要维度归属，由 05 步条文施加；此处只拦
    可机械判定的上限——超限意味着排序切片没有执行。
    """
    recs = record.get("recommendations")
    if not isinstance(recs, list):
        return [v("EMPTY_FIELD", where + ".recommendations",
                  "recommendations 缺失或不是列表（无意见写空列表）")]
    if len(recs) > RECOMMENDATIONS_MAX:
        return [v("SET_MISMATCH", where + ".recommendations",
                  "有 %d 条，超过 Top %d 上限（先按影响力排序：所在维度分 < 70 → HIGH "
                  "在前，再取前 %d）" % (len(recs), RECOMMENDATIONS_MAX,
                                     RECOMMENDATIONS_MAX))]
    return []


def _check_empty_scope_paths(record, where, root):
    """R-3 拦阻：空测试文件不得计入评审集。

    发现面已把空文件归 `excluded`（不评分）；产物若仍把它写进 `scope.paths`，等于把一份
    证明不了任何事的东西记成"已评审"——"100 不是 100" 的入口在此关闭。只判**在场文件**
    （目录条目与已不存在的路径跳过，后者由 excluded 面承载）。
    """
    violations = []
    scope = record.get("scope")
    paths = scope.get("paths") if isinstance(scope, dict) else None
    if not isinstance(paths, list):
        return violations
    for i, rel in enumerate(paths):
        if not nonempty(rel):
            continue
        name = str(rel)
        path = name if os.path.isabs(name) else os.path.join(root, name)
        if not os.path.isfile(path) or not is_test_file(name):
            continue
        if not has_code(read_text(path)):
            violations.append(v("SET_MISMATCH", "%s.scope.paths[%d]" % (where, i),
                                "No tests found：空测试文件不得计入评审集"
                                "（归 excluded(out-of-scope) 不评分）"))
    return violations


def check_record(index, record, table, final, show, root="."):
    violations = []
    where = "%s.reviews[%d]" % (show, index)
    if not isinstance(record, dict):
        return [v("EMPTY_FIELD", where, "记录不是映射")], []
    rid = record.get("id")
    if not nonempty(rid):
        violations.append(v("EMPTY_FIELD", where + ".id", "id 缺失"))
    elif not RV_RE.fullmatch(str(rid)):
        violations.append(v("ENUM_INVALID", where + ".id",
                            "id 须为 RV-0nn（三位零填充），实为 %s" % rid))
    date = record.get("date")
    if not nonempty(date):
        violations.append(v("EMPTY_FIELD", where + ".date", "date 缺失"))
    elif not DATE_RE.fullmatch(str(date)):
        violations.append(v("ENUM_INVALID", where + ".date", "date 须为 YYYY-MM-DD"))
    status = record.get("status")
    if not nonempty(status):
        violations.append(v("EMPTY_FIELD", where + ".status", "status 缺失"))
    elif str(status) not in RECORD_STATUSES:
        violations.append(v("ENUM_INVALID", where + ".status",
                            "status 越界：%s（合法集 %s）"
                            % (status, "|".join(RECORD_STATUSES))))
    elif final and str(status) != "final":
        violations.append(v("STATUS_MISMATCH", where + ".status",
                            "--final 要求 status 已落 final（实为 %s）" % status))

    violations += _check_scope(record, where, final)
    violations += _check_empty_scope_paths(record, where, root)
    finding_violations, deduped = _check_findings(record, where, table)
    violations += finding_violations
    violations += _check_convention_citation(record, where, deduped, table)
    violations += _check_score_block(record, where, deduped, table)
    violations += _check_gaps(record, where)
    violations += _check_walkthrough(record, where, record.get("coverage_gaps"))
    violations += _check_recommendations(record, where)

    baseline = record.get("convention_baseline")
    if not isinstance(baseline, dict):
        violations.append(v("EMPTY_FIELD", where + ".convention_baseline",
                            "convention_baseline 缺失或不是映射——须为映射且 keys 七键全量"
                            "（省略与「未采样」不可区分；评审集之外无语料时七键全记 unknown）"))
    else:
        keys = baseline.get("keys")
        if not isinstance(keys, dict):
            violations.append(v("EMPTY_FIELD", where + ".convention_baseline.keys",
                                "keys 缺失（7 个惯例键全量在场）"))
        else:
            missing = [k for k in CONVENTION_KEYS if k not in keys]
            if missing:
                violations.append(v("EMPTY_FIELD", where + ".convention_baseline.keys",
                                    "缺惯例键：%s（缺席与未测量不可区分）"
                                    % "、".join(missing)))
            for key in CONVENTION_KEYS:
                entry = keys.get(key)
                if not isinstance(entry, dict):
                    continue
                status = entry.get("status")
                if nonempty(status) and str(status) not in CONVENTION_STATUSES:
                    violations.append(v("ENUM_INVALID",
                                        "%s.convention_baseline.keys.%s.status" % (where, key),
                                        "status 越界：%s（合法集 %s）"
                                        % (status, "|".join(CONVENTION_STATUSES))))
            if final:
                for key in MECHANICAL_KEYS:
                    entry = keys.get(key)
                    if isinstance(entry, dict) and not isinstance(entry.get("adopted"), int):
                        violations.append(v("EMPTY_FIELD",
                                            "%s.convention_baseline.keys.%s.adopted"
                                            % (where, key),
                                            "--final 要求机械键带 adopted 计数（scan 判定）"))
    if final and any(ASSUMPTION in s for s in collect_strings(record)):
        violations.append(v("ASSUMPTION_PRESENT", where,
                            "--final 要求零 [ASSUMPTION]；未决推断须落 open_questions"))
    return violations, deduped


def cmd_check(args):
    root = os.path.abspath(args.project_root)
    out = os.path.abspath(args.output_dir)
    criteria = load_criteria()
    path = os.path.join(out, TEST_REVIEW_FILE)
    show = display_path(path, root)
    violations, records = [], []
    data, err = load_yaml_safe(path)
    if data is None and err is None:
        violations.append(v("MISSING_FILE", show,
                            "%s 不存在（先完成一次 test-review 起草）" % TEST_REVIEW_FILE))
    elif err is not None:
        violations.append(v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err))
    elif not isinstance(data, dict):
        violations.append(v("EMPTY_FIELD", show, "顶层不是映射（须为 project + reviews）"))
    else:
        project = data.get("project")
        if project is not None and not isinstance(project, dict):
            violations.append(v("EMPTY_FIELD", show + " project", "project 不是映射"))
        revisions = data.get("revisions")
        if revisions is not None and not isinstance(revisions, list):
            violations.append(v("EMPTY_FIELD", show + " revisions", "revisions 不是列表"))
        raw_records = data.get("reviews")
        if raw_records is None:
            violations.append(v("EMPTY_FIELD", show + " reviews",
                                "reviews 缺失（集合形态；无记录写空列表）"))
        elif not isinstance(raw_records, list):
            violations.append(v("EMPTY_FIELD", show + " reviews", "reviews 不是列表"))
        else:
            records = raw_records
            seen = set()
            for i, record in enumerate(records):
                record_violations, _ = check_record(i, record, criteria, args.final,
                                                    show, root)
                violations += record_violations
                if isinstance(record, dict) and nonempty(record.get("id")):
                    rid = str(record["id"])
                    if rid in seen:
                        violations.append(v("DUPLICATE_ID", "%s.reviews[%d].id" % (show, i),
                                            "记录 ID %s 重复（RV ID 稳定不重用）" % rid))
                    seen.add(rid)
            if args.final and not records:
                violations.append(v("EMPTY_FIELD", show + " reviews",
                                    "--final 要求至少 1 条记录"))
    counts = {"reviews": len(records),
              "findings": sum(len(r.get("findings") or []) for r in records
                              if isinstance(r, dict)),
              "gaps": sum(len(r.get("coverage_gaps") or []) for r in records
                          if isinstance(r, dict)),
              "by_status": _count_by(records, "status")}
    payload = {"ok": not violations, "command": "check", "project_root": args.project_root,
               "output_dir": os.path.normpath(out).replace("\\", "/"),
               "final": bool(args.final), "violations": violations, "warnings": [],
               "counts": counts}
    emit(payload, args.json, human_check)
    return 0 if payload["ok"] else 1


def _count_by(records, key):
    counts = {}
    for record in records:
        if isinstance(record, dict) and nonempty(record.get(key)):
            counts[str(record[key])] = counts.get(str(record[key]), 0) + 1
    return counts


def human_check(payload):
    if payload["ok"]:
        print("PASS：%s 校验通过（reviews=%d，final=%s）"
              % (payload["output_dir"] + "/" + TEST_REVIEW_FILE,
                 payload["counts"]["reviews"], payload["final"]))
        return
    print("FAIL：")
    for item in payload["violations"]:
        print("- %s %s: %s" % (item["code"], item["where"], item["msg"]))


# ---------------------------------------------------------------- CLI

def emit(payload, as_json, human_lines):
    if as_json:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        human_lines(payload)


def build_parser():
    ap = argparse.ArgumentParser(
        description="diy-test-review 确定性引擎：机械扫描（scan）+ 评分账本（score）+ "
                    "三向走查（walkthrough，委派 diyc）+ test-review.yaml 校验（check）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("scan", help="测试文件发现 + 机械项检出 + convention baseline 采样")
    s.add_argument("--paths", action="append", default=None,
                   help="评审集路径（可重复；文件或目录。省略 = 扫 project-root）")
    s.add_argument("--project-root", default=".", help="项目根（默认 .）")
    s.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    s.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    s.set_defaults(func=cmd_scan)

    o = sub.add_parser("score", help="评分账本：severity 复算 + 降档 + 去重 + 分档 + 建议")
    o.add_argument("--findings", required=True, help="findings 载体路径（findings.json）")
    o.add_argument("--project-root", default=".", help="项目根（默认 .）")
    o.add_argument("--output-dir", required=True, help="产物目录（必填）")
    o.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    o.set_defaults(func=cmd_score)

    w = sub.add_parser("walkthrough", help="AC ↔ 源码 ↔ 测试三向对账（只读；委派 diyc）")
    w.add_argument("--project-root", default=".", help="项目根（默认 .）")
    w.add_argument("--output-dir", required=True, help="产物目录（必填）")
    w.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    w.set_defaults(func=cmd_walkthrough)

    k = sub.add_parser("check", help="校验 test-review.yaml（schema/账本自洽/走查自洽）")
    k.add_argument("--final", action="store_true",
                   help="定稿校验：status 已落 final + zero [ASSUMPTION] + excluded 理由 + scope 非空")
    k.add_argument("--project-root", default=".", help="项目根（默认 .）")
    k.add_argument("--output-dir", required=True, help="产物目录（必填）")
    k.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    k.set_defaults(func=cmd_check)
    return ap


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = build_parser().parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
