# -*- coding: utf-8 -*-
"""diy-test-author 审计面：审计常量 + 源码切分层（注释剥离/测试块/锚点）。"""
import os
import re
# ---------------------------------------------------------------- 审计面
PLAN_FINAL = "已定稿"

# 红相脚手架只覆盖待办：失败是已激活测试、通过已收口，都不得被脚手架覆盖。
SCOPE_STATUS = "待办"

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
