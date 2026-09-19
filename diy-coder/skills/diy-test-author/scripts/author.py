# -*- coding: utf-8 -*-
"""diy-test-author 确定性引擎：技术栈/框架探测（detect）+ 测试代码纪律审计（audit）。

子命令：
  detect  语言无关的项目探测（只读）：依次读 package.json / pyproject.toml /
          requirements*.txt / Cargo.toml / go.mod / pom.xml / build.gradle* / Gemfile /
          composer.json 等清单判定 project_type 与既有测试框架；再识别测试目录、
          既有测试文件模式与既有 fixtures（本技能相对 diy-e2e-tests 的增量面）。
          无框架 → 回执给 suggested，**本技能不装框架**（框架脚手架是 diy-test-framework
          的职责，步进门禁据此拒绝并路由）。清单损坏/缺失降级为 warning，探测继续，不崩。
  audit   红相脚手架纪律审计（只读，**本技能的核心确定性资产**，源 atdd/automate 两份
          checklist 的手工核对在此下沉）。`--files` 必填（= 本次会话生成的测试文件集；
          不设「全测试目录」缺省——历史文件不进场）。三项判定合并在一条命令里：
          ① 上游门禁：test-plan.yaml 在场且 `project.status: final`；文件里每个 TC 锚
             （注释 `TC: TC-x.y.z`）可解析且 TC 现场自检（`technique` / `kill_target` 非空）；
             锚定 TC 的 `status` 必须是 `pending`（`fail` 是已激活测试、`pass` 已收口，
             都不得被脚手架覆盖；范围内全 pass 即拒绝，不静默空跑）；
          ② 规则集：无占位断言 / 无 CSS 与 XPath 定位 / 无硬编码业务数据 /
             断言指向期望行为（非空断言）/ 无 waitForTimeout 与 sleep /
             无 isVisible 条件流 / 无 page object / 单断言原子 / 文件行数上限 /
             用例名带 [P0]-[P3] 优先级标签且跟随锚定 TC 的 priority /
             Given-When-Then 结构注释 / 用例名可读 / 确定性隔离（无顺序依赖、
             无共享状态、用例体内无随机与时钟源）/ try-catch 只许清理 /
             测试代码无调试语句 / 夹具自建数据自带 teardown 清理；
          ③ 红相形态：每个 test 体含 skip 且每个用例带 TC 锚（本次新生成文件，
             无「人手写遗留」豁免）。

规则来源：`.claude/skills/bmad-testarch-atdd/checklist.md`（红相脚手架 / resilient
selector / data factory / 单断言 / network-first / Given-When-Then / P0-P3 标签 /
夹具 teardown 清理）与 `bmad-testarch-automate/checklist.md`
（禁 waitForTimeout / 禁 isVisible 条件流 / 禁 page object / 禁硬编码数据 /
确定性隔离 / try-catch 只许清理 / 禁调试语句 / 文件行数上限）。
语言无关实现 = 按扩展名装载的 pattern 表（js/ts 族、py 族、其余语言的 generic 兜底族）。
分层执行：**行级规则**（硬等待 / 条件流 / 脆选择器 / page object / 顺序依赖 /
顶层共享状态 / 调试语句）对全文生效（helper 等 test 体外代码同样在测试面上）；
**块级规则**（占位断言 / 断言面 / 硬编码数据 / skip 形态 / 锚 / 优先级标签 / 用例名 /
GWT / 随机与时钟源 / try-catch）判在 test 体内——工厂文件里的字面量是合法归宿，
不因硬编码规则受牵连（随机源与时钟源同理：造数据是工厂的本职）。
**夹具文件规则**（路径命中 fixtures 目录候选或文件名标记）判在文件级：建了数据的夹具
必须自带 teardown 清理。块级规则依赖 test 块切分，本引擎覆盖 js/ts 与 py 两族；
其余语言降级为文件级规则（硬编码数据随行级规则判定，断言面、skip 形态、锚、
优先级标签、用例名、GWT 与用例体内确定性项均不判）——该降级登记在回报中。

违规码：复用 batch3-contract §3 冻结集（MISSING_FILE UNPARSABLE_YAML UNKNOWN_ID
ENUM_INVALID EMPTY_FIELD STATUS_MISMATCH）；本引擎新增（本行即登记）：
  PLACEHOLDER_ASSERTION  占位断言（expect(true) / assert True 一类）
  BRITTLE_SELECTOR       CSS / XPath 定位（应用 getByRole/getByLabel/getByText 语义定位）
  HARDCODED_DATA         硬编码业务数据（应走工厂/faker）
  MISSING_ASSERTION      test 体无断言（断言须指向期望行为）
  NOT_ATOMIC             单 test 多断言（源「one assertion per test」）
  HARD_WAIT              waitForTimeout / sleep 一类硬等待
  CONDITIONAL_FLOW       isVisible() 条件流
  PAGE_OBJECT            page object 类
  FILE_TOO_LONG          文件行数超上限
  SKIP_MISSING           红相脚手架：test 体缺 skip（必须全部 skip，否则会污染 CI）
  ANCHOR_MISSING         红相脚手架：用例缺 TC 锚
  PRIORITY_TAG_MISSING   用例名缺 [P0]-[P3] 优先级标签（源 atdd/automate 硬纪律）
  PRIORITY_TAG_MISMATCH  用例名标签与锚定 TC 的 priority 不一致
  NAME_UNDESCRIPTIVE     用例名无信息（test1 / example 一类占位名）
  GWT_MISSING            用例缺 Given-When-Then 结构注释
  ORDER_DEPENDENCY       顺序依赖（describe.serial / pytest.mark.dependency 一类）
  SHARED_STATE           跨用例共享可变状态（顶层 let/var、函数内 global）
  NONDETERMINISTIC_SOURCE 用例体内用随机 / 时钟源（数据走工厂、时钟注入）
  TRY_CATCH_TEST_LOGIC   try-catch 包住测试逻辑（只许用于清理）
  DEBUG_STATEMENT        测试代码里的 console.log / print / debugger 一类调试语句
  FIXTURE_NO_TEARDOWN    夹具自建数据无 teardown 清理

分工裁定（任务书 §3 裁定 1/2）：本技能消费 diy-test-design 写的 TC，产出红相脚手架；
**零 YAML 写面**——本引擎不写任何文件，技能也不回填 TC status（脚手架不执行，没有实测
结果可回填；TC status 由 diy-dev 的 TDD 循环经 `diyc.py green` 回填）。
实例解析委托 SKILL.md 侧的 `diyc.py resolve`；本引擎不做 --instance / 白名单 / 目录推导，
--output-dir 必填（仅用于定位 test-plan.yaml）。契约同构（batch3-contract §3）：exit 0
唯一放行 / 1 = 违规或被拒绝 / 2 = 用法错误；--json 单行回执（ensure_ascii=False）；
violations[{code, where, msg}] + counts；where 正斜杠、相对 project-root。
"""
# trace: B3 diy-test-author 验收 #3 / #4 / #12（领域引擎 + TC 锚链 + 写权边界）
import argparse
import io
import json
import os
import re
import sys

import yaml

PLAN_FILE = "test-plan.yaml"

# ---------------------------------------------------------------- 探测面
# 三张常量表与 diy-e2e-tests/scripts/e2e.py 逐值对齐（同一套探测口径，不各写一份）。
NODE_MANIFESTS = ("package.json",)
PY_MANIFESTS = ("pyproject.toml", "setup.py", "requirements.txt", "requirements-dev.txt",
                "requirements-test.txt", "Pipfile")
JAVA_MANIFESTS = ("pom.xml", "build.gradle", "build.gradle.kts")
OTHER_MANIFESTS = ("Cargo.toml", "go.mod", "Gemfile", "composer.json")
ALL_MANIFESTS = NODE_MANIFESTS + PY_MANIFESTS + JAVA_MANIFESTS + OTHER_MANIFESTS

NODE_FRAMEWORKS = (("playwright", ("@playwright/test", "playwright")),
                   ("cypress", ("cypress",)),
                   ("vitest", ("vitest",)),
                   ("jest", ("jest",)),
                   ("mocha", ("mocha",)))
PY_FRAMEWORKS = (("playwright", ("playwright",)),
                 ("pytest", ("pytest",)),
                 ("behave", ("behave",)),
                 ("robotframework", ("robotframework",)))

TEST_DIR_CANDIDATES = ("tests", "test", "spec", "specs", "__tests__", "e2e", "cypress",
                       "integration", "qa")
TEST_FILE_SUFFIXES = (".spec.ts", ".spec.tsx", ".spec.js", ".spec.jsx", ".spec.py",
                      ".test.ts", ".test.tsx", ".test.js", ".test.jsx")
MAX_PATTERNS = 20
SCAN_DEPTH = 3

# fixtures 探测（本技能增量面：e2e.py 无此项）
FIXTURE_DIR_CANDIDATES = ("fixtures", "factories", "support", "__fixtures__", "mocks", "stubs")
FIXTURE_FILE_MARKERS = ("fixture", "factor", "conftest", "mock", "stub", "helper", "testdata")

SUGGESTS = {
    "node": "Playwright (@playwright/test) 或项目既有 runner——框架脚手架与依赖安装归 "
            "diy-test-framework（本技能只生成测试代码，不装框架）。",
    "python": "pytest（+ pytest-playwright 承接浏览器端到端）——框架脚手架与依赖安装归 "
              "diy-test-framework（本技能只生成测试代码，不装框架）。",
    "rust": "cargo test（内建；集成测试落 tests/ 目录）——确认配置后继续。",
    "go": "go test（内建；*_test.go 同包或 _test 包）——确认配置后继续。",
    "java": "JUnit 5 + Surefire/Gradle test——框架脚手架归 diy-test-framework。",
    "ruby": "RSpec（spec/ 目录）——框架脚手架归 diy-test-framework。",
    "php": "PHPUnit（tests/ 目录）——框架脚手架归 diy-test-framework。",
    "unknown": "未探测到项目清单——先用 diy-test-framework 建脚手架，或显式指定被测栈。",
}

# ---------------------------------------------------------------- 审计面
PLAN_FINAL = "final"

# 红相脚手架只覆盖 pending：fail 是已激活测试、pass 已收口，都不得被脚手架覆盖。
SCOPE_STATUS = "pending"

TC_RE = re.compile(r"TC-\d+(?:\.\d+)+")
# TC 锚 = 用例上方一行注释（`# TC: TC-x.y.z` / `// TC: TC-x.y.z`）；
# 与 diy-dev 的 `# trace: S-9 AC-9.1 TC-9.1.1` 形态区分，互不抢解析。
ANCHOR_RE = re.compile(r"(?:^|\s)(?:#|//|--|\*)\s*TC:\s*(TC-\d+(?:\.\d+)+)")
ANCHOR_LOOKBACK = 3

MAX_FILE_LINES = 400          # 文件行数上限（源 automate 的 max_file_lines，取 400）
MAX_ASSERTIONS_PER_TEST = 1   # 单断言原子（源「one assertion per test」）

JS = "js"
PY = "py"
GENERIC = "generic"

SUFFIX_FAMILY = {".js": JS, ".jsx": JS, ".ts": JS, ".tsx": JS, ".mjs": JS, ".cjs": JS,
                 ".mts": JS, ".cts": JS, ".py": PY}

EMAIL_LIT = r"""['"][\w.+-]+@[\w-]+\.[A-Za-z]{2,}['"]"""
PASSWORD_LIT = r"""(?:password|passwd|pwd|secret|token)\s*[:=]\s*['"][^'"]+['"]"""
WEAK_LIT = (r"""['"](?:password123|Password1!|Passw0rd!|changeme|admin123|123456|"""
            r"""test@example\.com|user@example\.com)['"]""")

LINE_RULES = (
    ("HARD_WAIT", "硬等待/睡眠：改用事件或状态等待（源禁 page.waitForTimeout / sleep）", {
        JS: (r"waitForTimeout\s*\(", r"\bsetTimeout\s*\(", r"cy\.wait\s*\(\s*\d",
             r"browser\.pause\s*\("),
        PY: (r"wait_for_timeout\s*\(", r"\btime\.sleep\s*\(", r"\bsleep\s*\(\s*\d"),
        GENERIC: (r"waitForTimeout\s*\(", r"wait_for_timeout\s*\(", r"\bsleep\s*\(\s*\d"),
    }),
    ("CONDITIONAL_FLOW", "isVisible() 条件流：断言失败即失败，不用可见性分支吞掉", {
        JS: (r"\bif\s*\([^)]*isVisible\s*\(", r"\bif\s*\([^)]*is_visible\s*\("),
        PY: (r"\bif\b[^\n]*\.is_visible\s*\(", r"\bif\b[^\n]*isVisible\s*\("),
        GENERIC: (r"\bif\b[^\n]*isVisible", r"\bif\b[^\n]*is_visible"),
    }),
    ("BRITTLE_SELECTOR", "脆选择器：改用 getByRole / getByLabel / getByText 语义定位", {
        JS: (r"xpath\s*=", r"\.locator\s*\(\s*['\"`]\s*[#.]", r"\.locator\s*\(\s*['\"`]\s*//",
             r"cy\.get\s*\(\s*['\"`]\s*[#.]", r"querySelector(?:All)?\s*\(",
             r"document\.getElementById\s*\(", r"page\.\$\$?\s*\("),
        PY: (r"By\.CSS_SELECTOR", r"By\.XPATH", r"find_element_by_(?:css_selector|xpath)\s*\(",
             r"\.locator\s*\(\s*['\"`]\s*[#.]", r"\.locator\s*\(\s*['\"`]\s*//"),
        GENERIC: (r"xpath\s*=", r"\.locator\s*\(\s*['\"`]\s*[#.]",
                  r"querySelector(?:All)?\s*\(", r"By\.(?:CSS_SELECTOR|XPATH)"),
    }),
    ("PAGE_OBJECT", "page object 模式：用例保持直接、扁平（源质量禁则）", {
        JS: (r"class\s+\w*(?:Page|PageObject|Screen)\b", r"new\s+\w*(?:Page|PageObject)\s*\("),
        PY: (r"class\s+\w*(?:Page|PageObject|Screen)\b",),
        GENERIC: (r"class\s+\w*(?:Page|PageObject|Screen)\b",),
    }),
    ("ORDER_DEPENDENCY", "顺序依赖：用例须任意顺序可跑（源质量禁则）", {
        JS: (r"\.serial\s*\(", r"mode\s*:\s*['\"]serial['\"]", r"\.configure\s*\(\s*\{[^}]*serial"),
        PY: (r"@pytest\.mark\.dependency", r"@pytest\.mark\.run\s*\(",
             r"pytest\.mark\.order\s*\(", r"@pytest\.mark\.serial"),
        GENERIC: (r"\.serial\s*\(", r"mode\s*:\s*['\"]serial['\"]",
                  r"@pytest\.mark\.dependency", r"pytest\.mark\.order\s*\("),
    }),
    ("SHARED_STATE", "跨用例共享状态：顶层可变变量 / 函数内 global 会让用例互相污染", {
        # 顶层（零缩进）let/var 才是共享面；函数体内缩进的声明不判。
        JS: (r"^(?:export\s+)?(?:let|var)\s+\w",),
        PY: (r"^\s*global\s+\w",),
        GENERIC: (r"^(?:export\s+)?(?:let|var)\s+\w", r"^\s*global\s+\w"),
    }),
    ("DEBUG_STATEMENT", "调试语句：console.log / print / debugger 不进测试代码（源质量禁则）", {
        JS: (r"console\.(?:log|debug|trace)\s*\(", r"\bdebugger\b"),
        PY: (r"(?:^|[^\w.])print\s*\(", r"\bbreakpoint\s*\(", r"\bpdb\.set_trace\s*\("),
        GENERIC: (r"console\.(?:log|debug|trace)\s*\(", r"\bdebugger\b",
                  r"(?:^|[^\w.])print\s*\(", r"\bbreakpoint\s*\("),
    }),
)

# 硬编码业务数据：判在 **test 体内**（工厂正是字面量的合法归宿——工厂文件不因这条被误判）；
# 其余语言无 test 块可切，降级为文件级行规则（GENERIC_ONLY_LINE_RULES）。
HARDCODED_PATTERNS = (EMAIL_LIT, PASSWORD_LIT, WEAK_LIT)
HARDCODED_MSG = "硬编码业务数据：改用工厂/faker 生成（源 data factory 纪律）"
GENERIC_ONLY_LINE_RULES = (("HARDCODED_DATA", HARDCODED_MSG, {GENERIC: HARDCODED_PATTERNS}),)

ASSERT_PAT = {
    JS: (r"expect\s*\(", r"(?:^|[^\w.])assert\b", r"\.should\b", r"assertThat\s*\("),
    PY: (r"(?:^|[^\w.])assert\b", r"self\.assert\w*\s*\(", r"pytest\.raises\s*\("),
    GENERIC: (r"\bassert\w*\b", r"expect\s*\(", r"assertThat\s*\("),
}

PLACEHOLDER_PAT = {
    JS: (r"expect\s*\(\s*(?:true|false|1|0|null|undefined)\s*\)\s*\.\s*\w+\s*"
         r"\(\s*(?:true|false|1|0|null|undefined)?\s*\)",
         r"expect\s*\(\s*(?:true|false)\s*\)", r"assert\s*\(\s*true\s*\)"),
    PY: (r"(?:^|[^\w.])assert\s+True\b", r"(?:^|[^\w.])assert\s+False\b",
         r"assert\s+1\s*==\s*1", r"assertEqual\s*\(\s*True\s*,\s*True\s*\)"),
    GENERIC: (r"expect\s*\(\s*true\s*\)", r"assert\s*\(\s*true\s*\)",
              r"(?:^|[^\w.])assert\s+True\b"),
}

SKIP_PAT = {
    JS: (r"(?:^|[^\w.])(?:test|it|describe)\.skip\s*\(", r"(?:^|\s)x(?:it|test|describe)\s*\(",
         r"test\.fixme\s*\(", r"\bskip\s*:\s*true"),
    PY: (r"pytest\.skip\s*\(", r"@pytest\.mark\.skip", r"@unittest\.skip",
         r"self\.skipTest\s*\(", r"\bskip\s*=\s*True", r"unittest\.SkipTest"),
    GENERIC: (r"\bskip\b",),
}

# 确定性隔离：判在 **test 体内**——工厂用随机与时钟造数据是本职，用例用它才是 flaky。
NONDETERMINISTIC_PAT = {
    JS: (r"\bMath\.random\s*\(", r"\bDate\.now\s*\(", r"new\s+Date\s*\(",
         r"\bperformance\.now\s*\(", r"crypto\.randomUUID\s*\("),
    PY: (r"\btime\.time\s*\(", r"\bdatetime\.now\s*\(", r"\bdatetime\.today\s*\(",
         r"\bdate\.today\s*\(", r"\brandom\.\w+\s*\(", r"\buuid\.uuid4\s*\(",
         r"\btime\.monotonic\s*\("),
    GENERIC: (r"\bMath\.random\s*\(", r"\bDate\.now\s*\(", r"\brandom\.\w+\s*\("),
}

# 清理面（try-catch 合法用途 + 夹具 teardown 两处共用，语言无关词表）。
CLEANUP_PAT = (r"\bdelete\w*\s*\(", r"\bremove\w*\s*\(", r"\bcleanup\w*\s*\(",
               r"\bteardown\w*\b", r"\bdestroy\w*\s*\(", r"\.close\s*\(",
               r"\breset\s*\(", r"\btruncate\w*\s*\(", r"\brollback\s*\(",
               r"\bdrop\w*\s*\(")
# 夹具建数据信号：只有「建」过才谈得上「清」（纯生成器工厂不受牵连）。
CREATION_PAT = (r"\bcreate\w*\s*\(", r"\binsert\w*\s*\(", r"\bregister\w*\s*\(",
                r"\bseed\w*\s*\(", r"\bsave\w*\s*\(", r"\bmake\w*\s*\(",
                r"\bbuild\w*\s*\(", r"\bsetup\w*\s*\(", r"\.post\s*\(")
# 夹具门（有 setup/teardown 相位的形态）：JS 的 test.extend 夹具 = await use()；py 夹具 = yield。
FIXTURE_USE_PAT = (r"await\s+use\s*\(", r"(?:^|\n)\s*yield\b")

TRY_JS_RE = re.compile(r"\btry\s*\{")
TRY_PY_RE = re.compile(r"^(?P<indent>[ \t]*)try\s*:", re.M)

# 优先级标签（源硬纪律：用例名带 [P0]-[P3]），取值集与源文一致。
PRIORITY_TAGS = ("P0", "P1", "P2", "P3")
PRIORITY_TAG_RE = re.compile(r"\[(P[0-3])\]")
# 标签载体窗：声明行 + 紧随一行（py 的文档字符串），向上含锚回看窗
# （py 的 def 名不能带方括号，标签常写在上方注释里）。
TAG_LOOKBACK = ANCHOR_LOOKBACK
TAG_LOOKAHEAD = 2
GWT_MARKERS = ("given", "when", "then")
# 尾界只看 ASCII 字母：`# Given一个边界输入` 这种中文紧贴的写法不得漏判。
GWT_RE = re.compile(r"\b(given|when|then)(?![a-z])", re.I)
UNDESCRIPTIVE_NAME_RE = re.compile(
    r"^\s*(?:it|test|tests|spec|case|example|sample|demo|tmp|temp|todo|fixme|"
    r"用例|测试|示例)\s*\d*\s*$", re.I)
EMPTY_NAME_RE = re.compile(r"^\s*[\W_]*\s*$")

JS_TEST_RE = re.compile(r"(?:^|[^\w.$])(?:it|test)\s*(?P<paren>\()\s*"
                        r"(?P<quote>['\"`])(?P<name>[^'\"`]*)")
PY_TEST_RE = re.compile(r"^(?P<indent>[ \t]*)def\s+(?P<name>test\w*)\s*\(", re.M)


def v(code, where, msg):
    return {"code": code, "where": where, "msg": msg}


def nonempty(value):
    return value is not None and str(value).strip() != ""


def display_path(path, project_root):
    """where 显示口径（对齐 diyc）：正斜杠 + 相对 project-root；越界则绝对路径。"""
    try:
        rel = os.path.relpath(path, project_root)
    except ValueError:
        rel = os.path.abspath(path)
    if rel.startswith(".."):
        return os.path.abspath(path).replace("\\", "/")
    return rel.replace("\\", "/")


def load_yaml_safe(path):
    """读 YAML：(data, err)。缺失 → (None, None)；空 → ({}, None)；损坏 → (None, 原因)。"""
    if not os.path.isfile(path):
        return None, None
    try:
        with io.open(path, "r", encoding="utf-8") as f:
            return (yaml.safe_load(f) or {}), None
    except yaml.YAMLError as e:
        return None, str(e)
    except OSError as e:
        return None, str(e)


# ---------------------------------------------------------------- detect

def read_manifest(path):
    """读清单文本：(text | None, warning | None)。损坏/不可读 → MANIFEST_UNPARSABLE。"""
    try:
        with io.open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read(), None
    except OSError as e:
        return None, v("MISSING_FILE", path.replace("\\", "/"), "清单不可读，探测降级：%s" % e)


def node_framework(root, warnings):
    """package.json：解析 JSON 后按优先级匹配 dependencies / devDependencies。"""
    path = os.path.join(root, "package.json")
    text, warning = read_manifest(path)
    if warning is not None:
        warnings.append(warning)
        return None
    try:
        data = json.loads(text)
    except ValueError as e:
        warnings.append(v("UNPARSABLE_YAML", display_path(path, root),
                          "package.json 不是合法 JSON，探测降级：%s" % e))
        return None
    deps = set()
    if isinstance(data, dict):
        for key in ("dependencies", "devDependencies", "peerDependencies"):
            block = data.get(key)
            if isinstance(block, dict):
                deps.update(str(k) for k in block)
    for name, markers in NODE_FRAMEWORKS:
        if any(m in deps for m in markers):
            return {"name": name, "detected_from": "package.json"}
    return None


def text_framework(root, manifests, frameworks, warnings):
    """文本清单（pyproject/requirements/Cargo/go.mod/...）：子串匹配框架标记。"""
    for rel in manifests:
        path = os.path.join(root, rel)
        if not os.path.isfile(path):
            continue
        text, warning = read_manifest(path)
        if warning is not None:
            warnings.append(warning)
            continue
        for name, markers in frameworks:
            if any(m in text for m in markers):
                return {"name": name, "detected_from": rel}
    return None


def builtin_framework(root):
    """内建测试链（无需第三方框架）：Cargo / Go / JVM 构建。"""
    table = (("Cargo.toml", "cargo test", "rust"),
             ("go.mod", "go test", "go"),
             ("pom.xml", "maven-surefire", "java"),
             ("build.gradle", "gradle test", "java"),
             ("build.gradle.kts", "gradle test", "java"))
    for rel, name, ptype in table:
        if os.path.isfile(os.path.join(root, rel)):
            return {"name": name, "detected_from": rel}, ptype
    return None, None


def detect_project_type(root):
    """project_type 判定（清单存在性，顺序即优先级）。返回 (type, 命中清单)。"""
    table = (("node", NODE_MANIFESTS), ("python", PY_MANIFESTS), ("rust", ("Cargo.toml",)),
             ("go", ("go.mod",)), ("java", JAVA_MANIFESTS), ("ruby", ("Gemfile",)),
             ("php", ("composer.json",)))
    for ptype, manifests in table:
        for rel in manifests:
            if os.path.isfile(os.path.join(root, rel)):
                return ptype, rel
    return "unknown", None


def is_test_file(name):
    lower = name.lower()
    if any(lower.endswith(s) for s in TEST_FILE_SUFFIXES):
        return True
    if lower.startswith("test_") and lower.endswith(".py"):
        return True
    if lower.endswith(("_test.py", "_test.go", "_test.rb")):
        return True
    return name.endswith(("Test.java", "Test.php"))


def walk_files(base, root, predicate, limit):
    """受限遍历：深度 SCAN_DEPTH、上限 limit 条；命中 predicate 的收相对路径。"""
    found = []
    for dirpath, dirnames, filenames in os.walk(base):
        rel_dir = os.path.relpath(dirpath, base)
        depth = 0 if rel_dir == "." else rel_dir.count(os.sep) + 1
        if depth >= SCAN_DEPTH:
            dirnames[:] = []
        for name in sorted(filenames):
            if predicate(name):
                found.append(os.path.relpath(os.path.join(dirpath, name),
                                             root).replace("\\", "/"))
                if len(found) >= limit:
                    return found
    return found


def scan_tests(root):
    """既有测试面：存在的测试目录 + 测试文件相对路径（模式来源，供生成时对齐）。"""
    dirs = [d for d in TEST_DIR_CANDIDATES if os.path.isdir(os.path.join(root, d))]
    patterns = []
    for test_dir in dirs:
        patterns += walk_files(os.path.join(root, test_dir), root, is_test_file,
                               MAX_PATTERNS - len(patterns))
        if len(patterns) >= MAX_PATTERNS:
            break
    return dirs, patterns


def scan_fixtures(root, test_dirs):
    """既有 fixtures / 工厂（本技能增量面）：目录候选 + 文件名标记，两处都算命中。"""
    dirs = []
    for test_dir in [""] + [td + "/" for td in test_dirs]:
        for name in FIXTURE_DIR_CANDIDATES:
            rel = test_dir + name
            if os.path.isdir(os.path.join(root, rel.replace("/", os.sep))) and rel not in dirs:
                dirs.append(rel)
    files = []
    for rel in dirs:
        # 命中 fixtures 候选目录的，其内容按位置即 fixtures（不再按文件名二次过滤）
        files += walk_files(os.path.join(root, rel.replace("/", os.sep)), root,
                            lambda _name: True, MAX_PATTERNS - len(files))
    # 无 fixtures 目录、但文件名自带标记的（tests/testdata.json / tests/helpers.py 一类）
    for test_dir in test_dirs:
        for rel in walk_files(os.path.join(root, test_dir), root,
                              lambda n: any(m in n.lower() for m in FIXTURE_FILE_MARKERS),
                              MAX_PATTERNS - len(files)):
            if rel not in files:
                files.append(rel)
    return dirs, files


def cmd_detect(args):
    root = os.path.abspath(args.project_root)
    warnings = []
    manifests = [rel for rel in ALL_MANIFESTS if os.path.isfile(os.path.join(root, rel))]
    project_type, _from = detect_project_type(root)

    framework = None
    if any(os.path.isfile(os.path.join(root, m)) for m in NODE_MANIFESTS):
        framework = node_framework(root, warnings)
    if framework is None and any(os.path.isfile(os.path.join(root, m))
                                 for m in PY_MANIFESTS):
        framework = text_framework(root, PY_MANIFESTS, PY_FRAMEWORKS, warnings)
    if framework is None:
        built_in, built_type = builtin_framework(root)
        if built_in is not None:
            framework = built_in
            if project_type == "unknown":
                project_type = built_type

    test_dirs, existing_patterns = scan_tests(root)
    fixture_dirs, fixture_files = scan_fixtures(root, test_dirs)
    suggested = None if framework is not None else SUGGESTS.get(
        project_type, SUGGESTS["unknown"])

    payload = {
        "ok": True,
        "command": "detect",
        "project_root": args.project_root,
        "output_dir": os.path.normpath(args.output_dir).replace("\\", "/"),
        "framework": framework,
        "project_type": project_type,
        "manifests": manifests,
        "test_dirs": test_dirs,
        "existing_patterns": existing_patterns,
        "fixtures": {"dirs": fixture_dirs, "files": fixture_files},
        "suggested": suggested,
        "violations": [],
        "warnings": warnings,
        "counts": {"manifests": len(manifests), "test_dirs": len(test_dirs),
                   "existing_patterns": len(existing_patterns),
                   "fixture_dirs": len(fixture_dirs), "fixture_files": len(fixture_files)},
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        if framework is None:
            print("未探测到既有测试框架（project_type=%s，清单：%s）"
                  % (project_type, ", ".join(manifests) or "无"))
            print("建议：%s" % suggested)
        else:
            print("框架 %s（来自 %s）｜project_type=%s｜测试目录 %s｜fixtures %d 个"
                  % (framework["name"], framework["detected_from"], project_type,
                     ", ".join(test_dirs) or "无", len(fixture_files)))
        for item in warnings:
            print("- %s %s: %s" % (item["code"], item["where"], item["msg"]))
    return 0


# ---------------------------------------------------------------- audit：源码切分

def family_of(path):
    return SUFFIX_FAMILY.get(os.path.splitext(path)[1].lower(), GENERIC)


def strip_line_comments(text, family):
    """逐行去注释后再跑代码规则：实现指引注释（[A] 强制携带）不得触发禁则。"""
    return "\n".join(strip_comments(line, family) for line in text.splitlines())


def strip_comments(line, family):
    """单行去注释（js/ts：`//` 与 `/* */`，URL 的 `://` 不误伤；py：`#`）。"""
    out = line
    if family in (JS, GENERIC):
        out = re.sub(r"/\*.*?\*/", "", out)
        m = re.search(r"(?<!:)//", out)
        if m:
            out = out[:m.start()]
    if family in (PY, GENERIC):
        idx = out.find("#")
        if idx >= 0:
            out = out[:idx]
    return out


def match_delim(text, start, open_ch, close_ch):
    """从 text[start] 的 open_ch 起做定界符配平（跳过字符串字面量），返回闭符下标。"""
    depth = 0
    quote = None
    i = start
    while i < len(text):
        ch = text[i]
        if quote:
            if ch == "\\":
                i += 2
                continue
            if ch == quote:
                quote = None
        elif ch in "'\"`":
            quote = ch
        elif ch == open_ch:
            depth += 1
        elif ch == close_ch:
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


def js_test_blocks(text):
    """js/ts 族：it()/test() 调用整体（含回调体）→ [{start, end, name, body}]（行号 0 基）。"""
    blocks = []
    for m in JS_TEST_RE.finditer(text):
        end = match_delim(text, m.start("paren"), "(", ")")
        if end < 0:
            end = len(text) - 1
        blocks.append({"start": text.count("\n", 0, m.start()),
                       "end": text.count("\n", 0, end),
                       "name": m.group("name"),
                       "body": text[m.start():end + 1]})
    return blocks


def py_test_blocks(text):
    """py 族：def test_* 到缩进回退为止 → [{start, end, name, body}]（行号 0 基）。"""
    lines = text.splitlines()
    blocks = []
    for m in PY_TEST_RE.finditer(text):
        start = text.count("\n", 0, m.start())
        indent = len(m.group("indent"))
        end = start + 1
        while end < len(lines):
            stripped = lines[end]
            if stripped.strip() == "":
                end += 1
                continue
            cur = len(stripped) - len(stripped.lstrip(" \t"))
            if cur <= indent:
                break
            end += 1
        blocks.append({"start": start, "end": end - 1, "name": m.group("name"),
                       "body": "\n".join(lines[start:end])})
    return blocks


def test_blocks(text, family):
    if family == JS:
        return js_test_blocks(text)
    if family == PY:
        return py_test_blocks(text)
    return []


def try_bodies(text, family):
    """try 块体（js：定界符配平；py：缩进块）；用于判 try-catch 是否只包清理。"""
    if family == JS:
        out = []
        for m in TRY_JS_RE.finditer(text):
            end = match_delim(text, m.end() - 1, "{", "}")
            if end > 0:
                out.append(text[m.end():end])
        return out
    if family == PY:
        lines = text.splitlines()
        out = []
        for m in TRY_PY_RE.finditer(text):
            start = text.count("\n", 0, m.start())
            indent = len(m.group("indent"))
            chunk = []
            i = start + 1
            while i < len(lines):
                line = lines[i]
                if line.strip() == "":
                    chunk.append(line)
                    i += 1
                    continue
                if len(line) - len(line.lstrip(" \t")) <= indent:
                    break
                chunk.append(line)
                i += 1
            out.append("\n".join(chunk))
        return out
    return []


def anchors_in_line(line):
    return ANCHOR_RE.findall(line)


def anchor_for(lines, index):
    """用例锚 = 用例上方一行注释（回看 ANCHOR_LOOKBACK 行，含本行）。"""
    for i in range(max(0, index - ANCHOR_LOOKBACK), min(len(lines), index + 1)):
        found = anchors_in_line(lines[i])
        if found:
            return found[0]
    return None


def any_match(patterns, text):
    """任一 pattern 命中即真（行级禁则用）。"""
    return any(re.search(p, text) for p in patterns)


def count_matches(patterns, text):
    """命中次数合计（断言面计数用：断言条数决定是否原子）。"""
    return sum(len(re.findall(p, text)) for p in patterns)


# ---------------------------------------------------------------- audit：规则执行

def audit_lines(lines, family, show, violations):
    """行级共用规则（去注释后判定，含 helper 等 test 体外代码）；每条违规记 `文件:行号`。"""
    rules = LINE_RULES + (GENERIC_ONLY_LINE_RULES if family == GENERIC else ())
    for no, raw in enumerate(lines, start=1):
        code_line = strip_comments(raw, family)
        if not code_line.strip():
            continue
        where = "%s:%d" % (show, no)
        for code, msg, table in rules:
            if any_match(table.get(family, table[GENERIC]), code_line):
                violations.append(v(code, where, "%s（第 %d 行）" % (msg, no)))


def audit_name(block, lines, known, where, violations):
    """用例名面：优先级标签（须跟随锚定 TC 的 priority）+ 名字可读性。"""
    name = block.get("name") or ""
    start = block["start"]
    region = "\n".join(lines[max(0, start - TAG_LOOKBACK):start + TAG_LOOKAHEAD])
    tags = PRIORITY_TAG_RE.findall(region)
    if not tags:
        violations.append(v("PRIORITY_TAG_MISSING", where,
                            "用例名缺优先级标签（[P0]-[P3]）——标签跟随锚定 TC 的 priority"))
    else:
        tc_id = anchor_for(lines, block["start"])
        case = known.get(tc_id) if tc_id else None
        want = str((case or {}).get("priority") or "").strip().upper()
        if want in PRIORITY_TAGS and want not in tags:
            violations.append(v("PRIORITY_TAG_MISMATCH", where,
                                "用例名标签 %s 与 %s 的 priority=%s 不一致——标签必须跟随 TC"
                                % ("/".join("[%s]" % t for t in tags), tc_id, want)))
    bare = PRIORITY_TAG_RE.sub("", name).strip()
    if UNDESCRIPTIVE_NAME_RE.match(bare) or EMPTY_NAME_RE.match(bare):
        violations.append(v("NAME_UNDESCRIPTIVE", where,
                            "用例名 %r 说不出测什么（test1 / example 一类占位名）"
                            "——名字须写明被测行为与期望" % name))


def audit_determinism(block, family, where, violations):
    """确定性隔离判在用例体内：随机 / 时钟源 + try-catch 包测试逻辑。"""
    body = strip_line_comments(block["body"], family)
    if any_match(NONDETERMINISTIC_PAT.get(family, NONDETERMINISTIC_PAT[GENERIC]), body):
        violations.append(v("NONDETERMINISTIC_SOURCE", where,
                            "用例体用了随机 / 时钟源——数据交给工厂（固定种子）、时钟注入，"
                            "同输入须同结果（源「tests are deterministic」）"))
    for chunk in try_bodies(block["body"], family):
        if any_match(CLEANUP_PAT, strip_line_comments(chunk, family)):
            continue
        violations.append(v("TRY_CATCH_TEST_LOGIC", where,
                            "try-catch 包住了测试逻辑（源「only for cleanup」）"
                            "——失败就让它失败；只有清理动作可包 try"))


def audit_blocks(lines, blocks, family, show, violations, known):
    """块级规则：断言面 + 红相形态（skip + TC 锚）+ 用例名 / GWT / 确定性隔离。"""
    for block in blocks:
        body = strip_line_comments(block["body"], family)
        where = "%s:%d" % (show, block["start"] + 1)

        if any_match(PLACEHOLDER_PAT.get(family, PLACEHOLDER_PAT[GENERIC]), body):
            violations.append(v("PLACEHOLDER_ASSERTION", where,
                                "占位断言（expect(true) / assert True 一类）——断言须指向期望行为"))
        if any_match(HARDCODED_PATTERNS, body):
            violations.append(v("HARDCODED_DATA", where, HARDCODED_MSG))
        assertions = count_matches(ASSERT_PAT.get(family, ASSERT_PAT[GENERIC]), body)
        if assertions == 0:
            violations.append(v("MISSING_ASSERTION", where,
                                "用例无断言——测试必须断言期望行为"))
        elif assertions > MAX_ASSERTIONS_PER_TEST:
            violations.append(v("NOT_ATOMIC", where,
                                "单用例 %d 条断言（上限 %d）——拆成原子用例"
                                % (assertions, MAX_ASSERTIONS_PER_TEST)))

        skipped = count_matches(SKIP_PAT.get(family, SKIP_PAT[GENERIC]), body)
        if skipped == 0:
            violations.append(v("SKIP_MISSING", where,
                                "红相脚手架缺 skip——产物必须全部 skip（否则会污染 CI）"))

        if anchor_for(lines, block["start"]) is None:
            violations.append(v("ANCHOR_MISSING", where,
                                "用例缺 TC 锚（上方一行 `TC: TC-x.y.z`）——新生成文件无遗留豁免"))

        audit_name(block, lines, known, where, violations)
        audit_determinism(block, family, where, violations)

        markers = {m.group(1).lower() for m in GWT_RE.finditer(block["body"])}
        missing = [m.upper() for m in GWT_MARKERS if m not in markers]
        if missing:
            violations.append(v("GWT_MISSING", where,
                                "用例缺 Given-When-Then 结构注释（缺 %s）——源硬纪律："
                                "用例以 GWT 组织，一屏看懂前置 / 动作 / 期望"
                                % " / ".join(missing)))


def is_fixture_file(show):
    """夹具/工厂文件的路径判据（复用探测面的常量，不另立一套词表）。"""
    parts = show.replace("\\", "/").split("/")
    name = parts[-1].lower()
    if any(seg in FIXTURE_DIR_CANDIDATES for seg in parts[:-1]):
        return True
    if name == "conftest.py":
        return True
    return any(m in name for m in FIXTURE_FILE_MARKERS)


def audit_fixture(text, family, show, violations):
    """夹具文件级：建了数据的夹具必须自带 teardown 清理（源「auto-cleanup (delete created data)」）。

    三条件齐备才判：有 setup/teardown 相位（`await use(` / `yield`）＋ 有建数据动作 ＋
    无任何清理动作。纯生成器工厂（无 use/yield 相位）不受牵连——造数据是它的本职。
    """
    body = strip_line_comments(text, family)
    if not any_match(FIXTURE_USE_PAT, body):
        return
    if not any_match(CREATION_PAT, body) or any_match(CLEANUP_PAT, body):
        return
    violations.append(v("FIXTURE_NO_TEARDOWN", show,
                        "夹具建了数据却没有 teardown 清理（源硬纪律：自动清理自建数据）"
                        "——`await use(data)` / `yield` 之后补删除"))


def audit_file(path, show, violations, known):
    """单文件审计 → 文件内的 TC 锚集合（去重，保序）。"""
    try:
        with io.open(path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
    except OSError as e:
        violations.append(v("MISSING_FILE", show, "文件不可读：%s" % e))
        return [], 0

    lines = text.splitlines()
    family = family_of(path)
    if len(lines) > MAX_FILE_LINES:
        violations.append(v("FILE_TOO_LONG", show,
                            "文件 %d 行超上限 %d——拆文件（源 max_file_lines 禁则）"
                            % (len(lines), MAX_FILE_LINES)))

    anchors = []
    for raw in lines:
        for tc in anchors_in_line(raw):
            if tc not in anchors:
                anchors.append(tc)

    audit_lines(lines, family, show, violations)
    if is_fixture_file(show):
        audit_fixture(text, family, show, violations)
    blocks = test_blocks(text, family)
    audit_blocks(lines, blocks, family, show, violations, known)
    return anchors, len(blocks)


def load_plan(out, root, violations):
    """上游门禁：test-plan.yaml 在场 + final + test_cases 可解析 → {tc_id: entry}。"""
    path = os.path.join(out, PLAN_FILE)
    show = display_path(path, root)
    plan, err = load_yaml_safe(path)
    if plan is None and err is None:
        violations.append(v("MISSING_FILE", show,
                            "%s 不存在（TC 由 diy-test-design 写——先跑它）" % PLAN_FILE))
        return {}
    if err is not None:
        violations.append(v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err))
        return {}
    if not isinstance(plan, dict):
        violations.append(v("EMPTY_FIELD", show, "顶层不是映射（须含 project + test_cases）"))
        return {}
    project = plan.get("project")
    status = project.get("status") if isinstance(project, dict) else None
    if str(status) != PLAN_FINAL:
        violations.append(v("STATUS_MISMATCH", show + " project.status",
                            "上游不是 final（当前 %s）——先跑 diy-test-design 定稿"
                            % (status or "缺")))
    cases = plan.get("test_cases")
    if not isinstance(cases, list):
        violations.append(v("EMPTY_FIELD", show + " test_cases",
                            "test_cases 缺失或不是列表（TC 是本源唯一输入）"))
        return {}
    return {str(c["id"]): c for c in cases
            if isinstance(c, dict) and nonempty(c.get("id"))}


def check_scoped_tcs(tc_ids, known, out, root, violations):
    """锚定 TC 现场自检：存在 / technique / kill_target 非空 / status 必须是 pending。"""
    show = display_path(os.path.join(out, PLAN_FILE), root)
    for tc_id in tc_ids:
        case = known.get(tc_id)
        where = "%s test_cases[%s]" % (show, tc_id)
        if case is None:
            violations.append(v("UNKNOWN_ID", where,
                                "%s 在 %s 中不存在——锚必须指向既有 TC" % (tc_id, PLAN_FILE)))
            continue
        for field in ("technique", "kill_target"):
            if not nonempty(case.get(field)):
                violations.append(v("EMPTY_FIELD", "%s.%s" % (where, field),
                                    "%s 缺失或为空（TC 须带 %s）" % (field, field)))
        status = case.get("status")
        if str(status) != SCOPE_STATUS:
            violations.append(v("STATUS_MISMATCH", "%s.status" % where,
                                "%s 的 status=%s 不是 %s——红相脚手架只覆盖未激活的 TC"
                                "（fail 是已激活测试、pass 已收口）；范围内无可做 TC 时"
                                "不静默空跑" % (tc_id, status or "缺", SCOPE_STATUS)))


def cmd_audit(args):
    root = os.path.abspath(args.project_root)
    out = os.path.abspath(args.output_dir)
    violations = []
    warnings = []

    raw_files = list(args.files or [])
    if not raw_files:
        violations.append(v("EMPTY_FIELD", "--files",
                            "文件集为空——只审本次产出/触碰的文件，无「全测试目录」缺省"))
    resolved = []
    seen = set()
    for raw in raw_files:
        if not nonempty(raw):
            violations.append(v("EMPTY_FIELD", "--files", "空的文件项——去掉空串或补上本次文件"))
            continue
        path = raw if os.path.isabs(raw) else os.path.join(root, raw)
        show = display_path(path, root)
        if show in seen:
            continue
        seen.add(show)
        if not os.path.isfile(path):
            violations.append(v("MISSING_FILE", show,
                                "文件不存在（--files 只带本次会话产出/触碰的文件集）"))
            continue
        resolved.append((path, show))

    known = load_plan(out, root, violations)

    tc_ids = []
    test_count = 0
    for path, show in resolved:
        anchors, blocks = audit_file(path, show, violations, known)
        test_count += blocks
        for tc_id in anchors:
            if tc_id not in tc_ids:
                tc_ids.append(tc_id)

    if known:
        check_scoped_tcs(tc_ids, known, out, root, violations)

    ok = not violations
    payload = {
        "ok": ok,
        "command": "audit",
        "project_root": args.project_root,
        "output_dir": os.path.normpath(out).replace("\\", "/"),
        "files": [show for _path, show in resolved],
        "tcs": tc_ids,
        "violations": violations,
        "warnings": warnings,
        "counts": {"files": len(resolved), "tests": test_count, "tcs": len(tc_ids),
                   "violations": len(violations), "warnings": len(warnings)},
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        if ok:
            print("PASS：审计通过（文件 %d / 用例 %d / TC %d）"
                  % (len(resolved), test_count, len(tc_ids)))
        else:
            print("FAIL：审计不通过，零写入")
            for item in violations:
                print("- %s %s: %s" % (item["code"], item["where"], item["msg"]))
        for item in warnings:
            print("- %s %s: %s" % (item["code"], item["where"], item["msg"]))
    return 0 if ok else 1


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(
        description="diy-test-author 确定性引擎：栈/框架探测（detect）+ 测试代码纪律审计（audit）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("detect", help="语言无关框架探测（只读；无框架回 suggested，不装框架）")
    d.add_argument("--project-root", default=".", help="项目根（默认 .）")
    d.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    d.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    d.set_defaults(func=cmd_detect)

    a = sub.add_parser("audit", help="红相脚手架纪律审计（只读；exit 0 唯一放行）")
    a.add_argument("--files", action="append", required=True,
                   help="本次会话生成的测试文件（可重复；必填，无全目录缺省）")
    a.add_argument("--project-root", default=".", help="项目根（默认 .）")
    a.add_argument("--output-dir", required=True,
                   help="产物目录（必填；用于定位 test-plan.yaml，引擎不写任何文件）")
    a.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    a.set_defaults(func=cmd_audit)

    args = ap.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
