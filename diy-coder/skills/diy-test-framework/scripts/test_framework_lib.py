# -*- coding: utf-8 -*-
"""diy-test-framework 基础层：常量表 + 共享工具 + 模板层 + 回执输出。"""
import fnmatch
import io
import json
import os
import re
import sys

import yaml

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import display_path, nonempty, v  # noqa: E402

TF_FILE = "test-framework.yaml"
TEST_PLAN_FILE = "test-plan.yaml"
PLAN_JSON = "scaffold-plan.json"

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(SKILL_ROOT, "templates")

# 清单表：语言 → 清单文件名（支持 fnmatch 通配）。顺序即语言判定优先级；表可扩充（非封闭枚举）
LANG_MANIFESTS = (
    ("node", ("package.json",)),
    ("python", ("pyproject.toml", "setup.py", "requirements.txt", "requirements-dev.txt",
                "requirements-test.txt", "Pipfile")),
    ("java", ("pom.xml", "build.gradle", "build.gradle.kts")),
    ("go", ("go.mod",)),
    ("dotnet", ("*.csproj", "*.sln")),
    ("ruby", ("Gemfile",)),
    ("rust", ("Cargo.toml",)),
    ("php", ("composer.json",)),
)
KNOWN_MANIFESTS = tuple(name for _, names in LANG_MANIFESTS for name in names)

# 移动指示器（判定优先于前端，源 step-01 §1）
MOBILE_DIRS = (".maestro", "maestro")
MOBILE_FILES = ("app.json", "app.config.js", "app.config.ts", "Podfile", "pubspec.yaml",
                "*.xcodeproj", "*.xcworkspace")
MOBILE_PATHS = ("android/app/build.gradle",)
MOBILE_PACKAGES = ("react-native", "expo")

FRONTEND_PACKAGES = ("react", "react-dom", "vue", "@angular/core", "next", "nuxt", "svelte",
                     "vite", "webpack", "solid-js")
FRONTEND_FILES = ("vite.config.ts", "vite.config.js", "webpack.config.js", "next.config.js",
                  "next.config.mjs")
BACKEND_PACKAGES = ("express", "fastify", "koa", "@nestjs/core", "hapi", "restify")

# 既有框架配置（探测面；顺序即优先级）
FRAMEWORK_CONFIGS = (
    ("playwright", ("playwright.config.ts", "playwright.config.js", "playwright.config.mts")),
    ("cypress", ("cypress.config.ts", "cypress.config.js", "cypress.json")),
    ("vitest", ("vitest.config.ts", "vitest.config.mts", "vitest.config.js")),
    ("jest", ("jest.config.js", "jest.config.ts", "jest.config.mjs")),
    ("pytest", ("pytest.ini", "conftest.py", "tox.ini")),
    ("rspec", (".rspec",)),
    ("junit", ("src/test/java", "src/test/kotlin")),
    ("xunit", ("*.Tests.csproj",)),
    ("maestro", (".maestro", "maestro")),
)

# CI 平台 → 配置路径（探测面）
CI_PLATFORMS = ("github-actions", "gitlab-ci", "jenkins", "azure-devops", "harness")
CI_CONFIGS = (
    ("github-actions", (".github/workflows/*.yml", ".github/workflows/*.yaml")),
    ("gitlab-ci", (".gitlab-ci.yml",)),
    ("jenkins", ("Jenkinsfile",)),
    ("azure-devops", ("azure-pipelines.yml", "azure-pipelines.yaml")),
    ("harness", (".harness/pipeline.yaml", ".harness/pipeline.yml")),
    ("circle-ci", (".circleci/config.yml",)),
)
# 平台 → 模板（**五平台有模板；circle-ci 与移动端无模板覆盖**，见 detect 回执 templates 面）
CI_TEMPLATES = {
    "github-actions": "ci/github-actions/%s.yml.tpl",
    "gitlab-ci": "ci/gitlab-ci/%s.yml.tpl",
    "jenkins": "ci/jenkins/%s.groovy.tpl",
    "azure-devops": "ci/azure-devops/%s.yml.tpl",
    "harness": "ci/harness/%s.yaml.tpl",
}

# 脚手架 profile（目录名 = templates/framework/<profile>/）
BACKEND_PROFILES = ("node", "python", "java", "go", "dotnet", "ruby", "rust", "php")
BROWSER_PROFILES = ("browser-playwright", "browser-cypress")
BACKEND_FRAMEWORKS = {
    "node": "vitest", "python": "pytest", "java": "JUnit 5", "go": "go test",
    "dotnet": "xUnit", "ruby": "RSpec", "rust": "cargo test", "php": "PHPUnit",
}
PACKAGE_MANAGERS = (
    ("node", (("pnpm-lock.yaml", "pnpm"), ("yarn.lock", "yarn"), ("package-lock.json", "npm"))),
    ("python", (("uv.lock", "uv"), ("poetry.lock", "poetry"), ("Pipfile.lock", "pipenv"))),
)

# 上下文文档（F-9，源 fw/step-01 §2）：只在这些目录里找，不递归全树（node_modules 代价）
CONTEXT_DOC_DIRS = ("", "docs", "doc", "adr", "docs/adr", "architecture", "docs/architecture")
CONTEXT_DOC_GLOBS = ("architecture.md", "tech-spec*.md", "adr-*.md", "*.adr.md")
# auth 线索关键词（命中即提示 step 1 去读该文档；只报事实，不做判定）
AUTH_HINTS = ("auth", "oauth", "jwt", "login", "session", "token")

MODES = ("框架", "CI", "两者")
STACK_TYPES = ("前端", "后端", "全栈", "移动端")
FILE_KINDS = ("脚手架", "配置", "CI", "钩子", "脚本", "文档")
ACTIONS = ("新建", "更新")
CHECK_RESULTS = ("通过", "失败")
STAGE_NAMES = ("静态检查", "测试", "契约", "预热", "报告")
SETUP_RE = re.compile(r"TF-\d{3}")
DA_RE = re.compile(r"DA-\d{3}")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
PLACEHOLDER_RE = re.compile(r"\{\{([A-Z][A-Z0-9_]*)\}\}")
HEADER_RE = re.compile(r"^\s*(?:#|//|<!--)\s*placeholders:\s*(.*?)\s*(?:-->)?\s*$")
# 命令匹配边界（任务书 §5 裁定 4：挡 `npm run lint` 误配 `npm run lint:fix`）
COMMAND_BOUNDARIES = " \t\n\r;|&\"'`"
# 回执 pending_commands 的取值来源（顺序即输出顺序）
PENDING_COMMAND_KEYS = ("INSTALL_CMD", "BROWSER_INSTALL", "LINT_CMD", "TEST_CMD")

# 生成物脚本块扫描（F-12；源 ci/steps-v/step-01 §2a）
CODE_KEY_RE = re.compile(r"^(?P<indent>[ \t]*)(?:-[ \t]+)?(?:run|script|command|sh|bash)\s*:\s*(?P<rest>.*)$")
JENKINS_SH_RE = re.compile(r"\bsh\s+(?P<quote>'''|\"\"\"|'|\")(?P<rest>.*)$")
BLOCK_SCALAR_RE = re.compile(r"^[|>]")
UNSAFE_EXPR_RE = re.compile(r"\$\{\{\s*(inputs\.|github\.event\.|github\.head_ref\b|parameters\.)")
UNSAFE_HARNESS_RE = re.compile(r"<\+input|<\+trigger|<\+pipeline\.variables")
COMMENT_LINE_PREFIXES = ("#", "//", "<!--", "*")


def out_dir(args):
    """--output-dir 的解析基准 = project-root（相对路径按项目根解析；绝对路径原样）。
    引擎不做实例解析 / 白名单 / 目录推导——基准钉住只为让 `where` 稳定相对 project-root。"""
    out = args.output_dir
    if not os.path.isabs(out):
        out = os.path.join(os.path.abspath(args.project_root), out)
    return out


def load_json_safe(path):
    """读 JSON：(data, err)。文件缺失 → (None, None)；损坏 → (None, 原因)。"""
    if not os.path.isfile(path):
        return None, None
    try:
        with io.open(path, "r", encoding="utf-8") as fh:
            return json.load(fh), None
    except (ValueError, UnicodeDecodeError) as e:
        return None, str(e)
    except OSError as e:
        return None, str(e)


def path_form_error(rel):
    """路径形态校验（correct-course `path:` 口径，任务书 §5 裁定 4）：相对 / 正斜杠 / 无 `.` `..` 段。"""
    if not isinstance(rel, str) or not rel.strip():
        return "路径为空"
    if rel.startswith("/") or re.match(r"^[A-Za-z]:", rel):
        return "不得为绝对路径（须相对项目根）"
    if "\\" in rel:
        return "须用正斜杠（不得含反斜杠）"
    if any(seg in ("", ".", "..") for seg in rel.split("/")):
        return "不得含空段 / `.` / `..` 段"
    return None


def command_in_text(tool, text):
    """命令匹配算法（任务书 §5 裁定 4）：空白归一化、大小写敏感、独立命令形态（边界字符集）。"""
    needle = " ".join(str(tool).split())
    if not needle:
        return False
    hay = " ".join(str(text).split())
    start = 0
    while True:
        i = hay.find(needle, start)
        if i < 0:
            return False
        before = hay[i - 1] if i > 0 else None
        end = i + len(needle)
        after = hay[end] if end < len(hay) else None
        if (before is None or before in COMMAND_BOUNDARIES) and \
           (after is None or after in COMMAND_BOUNDARIES):
            return True
        start = i + 1


def find_files(root, patterns):
    """项目根下的模式匹配（相对路径正斜杠输出，相对根单层 + 已知子路径）。"""
    hits = []
    for pattern in patterns:
        if "/" in pattern or pattern.startswith("."):
            if "*" in pattern:
                for dirpath, _dirs, names in os.walk(root):
                    for name in names:
                        rel = display_path(os.path.join(dirpath, name), root)
                        if fnmatch.fnmatch(rel, pattern):
                            hits.append(rel)
            elif os.path.exists(os.path.join(root, pattern)):
                hits.append(pattern)
        else:
            for name in os.listdir(root):
                if fnmatch.fnmatch(name, pattern):
                    hits.append(name)
    return sorted(set(hits))

# ---------------------------------------------------------------- 模板层

def parse_template(text):
    """模板 → (declared, body, err)。首行指令 `# placeholders: A B`（或 `//` / `<!--` 形态）
    声明占位符集，该行自渲染结果剥除（它是模板指令，不是产物内容）。
    脚本模板例外（F-3）：`#!` 开头的首行是 shebang——shebang 必须是产物第一行，
    故指令行落在第二行，渲染只剥除指令行、**保留 shebang**。"""
    lines = text.splitlines(keepends=True)
    if not lines:
        return None, None, "模板为空"
    offset = 1 if lines[0].startswith("#!") else 0
    if len(lines) <= offset:
        return None, None, "模板缺 `# placeholders:`（或 `// placeholders:`）指令"
    head = lines[offset].rstrip("\r\n")
    match = HEADER_RE.match(head)
    if not match:
        return None, None, ("模板%s缺 `# placeholders:`（或 `// placeholders:`）指令"
                            % ("第二行" if offset else "首行"))
    declared = tuple(match.group(1).split())
    body = "".join(lines[:offset] + lines[offset + 1:])
    present = tuple(sorted(set(PLACEHOLDER_RE.findall(body))))
    if sorted(declared) != list(present):
        return None, None, ("占位符声明与正文不符：声明 %s / 正文 %s"
                            % (sorted(declared), list(present)))
    return declared, body, None


def render_template(text, substitutions):
    """渲染 = 逐字节复制 + 封闭占位符替换。→ (rendered, err)。未取值 → err（整条拒绝）。"""
    declared, body, err = parse_template(text)
    if err is not None:
        return None, err
    missing = [name for name in declared if not nonempty(substitutions.get(name))]
    if missing:
        return None, "占位符未取值：%s" % " ".join(missing)
    rendered = PLACEHOLDER_RE.sub(lambda m: str(substitutions[m.group(1)]), body)
    return rendered, None


def template_abs(rel):
    """技能内模板相对路径 → 绝对路径；越界 → None。"""
    if not isinstance(rel, str) or not rel.strip() or path_form_error(rel) is not None:
        return None
    path = os.path.normpath(os.path.join(TEMPLATES_DIR, *rel.split("/")))
    root = os.path.normpath(TEMPLATES_DIR)
    if path != root and not path.startswith(root + os.sep):
        return None
    return path

# ---------------------------------------------------------------- 回执输出
def emit(payload, as_json, human_fn):
    if as_json:
        print(json.dumps(payload, ensure_ascii=False))
        return
    for item in payload["warnings"]:
        sys.stderr.write("warning: %s %s: %s\n" % (item["code"], item["where"], item["msg"]))
    human_fn(payload)
