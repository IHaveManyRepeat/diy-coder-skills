# -*- coding: utf-8 -*-
"""diy-test-framework 确定性引擎：栈探测（detect）+ 模板渲染落盘（scaffold）+ 台账与 CI 三方对齐校验（check）。

子命令
------
detect   语言无关的栈探测（只读）。清单表（`LANG_MANIFESTS`）判语言与包管理器；移动指示器
         （`.maestro/` / `maestro/` / `app.json` / `Podfile` / `android/app/build.gradle` /
         `*.xcodeproj` / `*.xcworkspace` / `pubspec.yaml` / package.json 的 react-native|expo 依赖）
         **优先判定** 移动端（否则 RN/Expo 工程会被误判为前端）；前后端并存 → 全栈；
         既有框架配置 → `existing.framework`；CI 平台（.github/workflows/*.yml / .gitlab-ci.yml /
         Jenkinsfile / azure-pipelines.yml / .harness/pipeline.yaml / .circleci/config.yml）→
         `existing.ci`；`suggested` = 选型建议（框架 / 平台 / 脚手架 profile）；`templates` 给出
         模板覆盖面（移动端面**无模板覆盖**，据任务书 §5 裁定 5 与 §12.11：HALT + 登记）；
         `git` = 仓库事实（`.git` 在场 / origin 远端名；源 ci/step-01 §1「Git repository required」）；
         `context` = 架构文档与 auth 线索（源 fw/step-01 §2「Check for architecture docs /
         Note auth requirements」）——只报事实，不做推断。
         清单全不命中 → `ok: false` + `MISSING_FILE`（门禁拒绝，零产出）；清单在场但不可解析 →
         `MANIFEST_UNPARSABLE` warning 降级（对齐 e2e.py 先例），探测继续。
scaffold --plan <plan.json>  按 plan 渲染技能内模板写入项目——**只写 plan 声明的路径、只写新增
         文件，不做任何形式的 merge，绝不删除或覆盖任何既有文件**。
         预检零写入：plan 可解析 + 字段齐全（缺席 MISSING_FILE / 不可解析 UNPARSABLE_YAML /
         字段非法 ENTRY_INVALID）+ 每个 `files[].template` 命中技能内实际模板（不命中 MISSING_FILE）
         + 所选模板的占位符取值完备（未取值 EMPTY_FIELD）+ 每个 path 过形态校验（相对、正斜杠、
         无 `.` `..` 段 → ENUM_INVALID，对齐 correct-course `path:` 口径），全部通过才写第一个字节。
         写入阶段逐文件判定三分支：目标不存在 → 原子写（同目录临时文件 + os.replace）；
         目标存在且内容 == 同模板同 plan 的渲染结果（逐字节）→ skip（幂等重入，崩溃后重入同样成立）；
         目标存在且内容不同 → 冲突 → 删除本次已写文件（回滚，删除失败不静默：warning + 残留清单）
         → 整条拒绝 exit 1（`FILE_CONFLICT`，回执列出冲突 path）。
         回执 `pending_commands` = plan `substitutions` 里 INSTALL_CMD / BROWSER_INSTALL /
         LINT_CMD / TEST_CMD 的非空取值（**命令执行归步骤层，本引擎保持纯文件操作**）。
         模板渲染协议：模板首行指令 `# placeholders: A B`（或 `// placeholders:`）声明占位符集，
         该行渲染时剥除；正文出现的 `{{NAME}}` 集须与该声明相等，取值来自 plan `substitutions`；
         渲染 = 逐字节复制 + 占位符替换，不注入时间戳/随机/环境值（同模板同 plan → 同字节）。
check [--final]  台账 schema / 枚举 / files[].path 形态 / 生成文件存在性 / `ci_alignment`（**重扫
         不采信台账**：现场从 test-plan.yaml + CI 文件重算 阻断 命令覆盖与阈值注入，与台账
         `static_check_alignment` 比对，漏 阻断 条目或 `in_ci` 不符 → `CI_MISALIGNED`；
         台账 order 不在 static_checks → `UNKNOWN_ID`；test-plan 缺席 / static_checks 字段缺席 /
         列表为空 → 同一处置：跳过对齐判定 + warning，不阻塞；mode=框架 或 platform=none →
         不适用，后者记 warning）/ **生成物脚本块注入扫描**（现场扫 CI 文件的 `run:` / `script:` /
         `command:` / `sh` 块，块内出现不可信上下文直接插值 → `UNSAFE_INJECTION`；注释行不参与，
         comment 内的示例不算违规）/ `checks` 中 失败 条目 note 非空。
         `--final` 附加：zero `[假设]`、framework 非空、mode=两者|CI 时 ci 段完整
         （platform ∈ 五平台、file 在场、stages / gates / static_check_alignment 齐）、
         `ci.gates` 拉满 P0/P1 双 `100%`（2026-09-15 用户裁定，源为 P1≥95%）。

违规码
------
复用 batch3-contract §3 冻结集：`MISSING_FILE` `UNPARSABLE_YAML` `DUPLICATE_ID` `UNKNOWN_ID`
`ENUM_INVALID` `EMPTY_FIELD` `ENTRY_INVALID` `ASSUMPTION_PRESENT`。
新增（本引擎专用，已在回报中登记）：
  - `FILE_CONFLICT`   scaffold 目标已存在且内容不同（不覆盖既有文件）→ 回滚 + 整条拒绝。
  - `CI_MISALIGNED`   CI 三方对齐失败：阻断 工具命令未出现在 CI 文件、台账 `in_ci` 与现场
                      重算不符、台账漏 阻断 条目、或 CI 文件缺台账 `ci.gates` 阈值字面量。
  - `UNSAFE_INJECTION` 生成物脚本块内直接插值不可信上下文（`${{ inputs.* }}` /
                      `${{ github.event.* }}` / `${{ github.head_ref }}` / `${{ parameters.* }}` /
                      Harness `<+input>` / `<+trigger.*>` / `<+pipeline.variables.*>`）——源
                      steps-v/step-01 §2a 的 FAIL 项；inputs 只能是 DATA 不能是 COMMAND。
沿用先例扩展码：`MANIFEST_UNPARSABLE`（detect 专用降级，B2 diy-e2e-tests 首创同码）。
warning 专用扩展码：`TEMPLATE_UNSUPPORTED`（detect 专用：栈已识别但 `templates/` 未覆盖，
面 = 移动端；告警随门禁 HALT 一起给出，不单列违规）。

分工裁定（任务书 §2.3 / §5）：test-framework.yaml 是新产物类型，不进 diyc.py check 的硬编码
类型集；本引擎沿用领域引擎形态（同 checkpoint.py / e2e.py）。实例解析委托 SKILL.md 侧的
`diyc.py resolve`；本引擎不做 --instance / 白名单 / 目录推导，`--output-dir` 必填。
产物与产物 ID（TF-###）由 LLM 会话铸造，本引擎只校验格式与唯一性。
"""
# trace: B3 diy-test-framework 验收 #3（前置门禁零产出退出）/#4（ID 链接入）/#12（领域引擎接线）
# trace: S-2 AC-2.2 CI 三方对齐（correct-course path: 口径 + test-plan static_checks 链）
import argparse
import datetime
import fnmatch
import io
import json
import os
import re
import sys
import tempfile

import yaml

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


def v(code, where, msg):
    return {"code": code, "where": where, "msg": msg}


def nonempty(value):
    return value is not None and str(value).strip() != ""


def today():
    return datetime.date.today().isoformat()


def out_dir(args):
    """--output-dir 的解析基准 = project-root（相对路径按项目根解析；绝对路径原样）。
    引擎不做实例解析 / 白名单 / 目录推导——基准钉住只为让 `where` 稳定相对 project-root。"""
    out = args.output_dir
    if not os.path.isabs(out):
        out = os.path.join(os.path.abspath(args.project_root), out)
    return out


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
    """读 YAML：(data, err)。文件缺失 → (None, None)；空文件 → ({}, None)；损坏 → (None, 原因)。"""
    if not os.path.isfile(path):
        return None, None
    try:
        with io.open(path, "r", encoding="utf-8") as fh:
            return (yaml.safe_load(fh) or {}), None
    except yaml.YAMLError as e:
        return None, str(e)
    except OSError as e:
        return None, str(e)


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


def collect_strings(node):
    """递归收集映射/列表内的全部字符串（键与值）——[假设] 扫描用。"""
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


def write_atomic(path, text):
    """同目录临时文件 + os.replace（同卷原子替换；不保留既有内容）。"""
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".tfw-", suffix=".tmp", dir=parent or ".")
    try:
        with io.open(fd, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
        os.replace(tmp, path)
    except OSError:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


# ---------------------------------------------------------------- detect

def read_node_deps(root, warnings):
    """package.json → (deps:set, flags)。不可解析 → MANIFEST_UNPARSABLE warning（不崩）。"""
    path = os.path.join(root, "package.json")
    data, err = load_json_safe(path)
    if err is not None:
        warnings.append(v("MANIFEST_UNPARSABLE", "package.json",
                          "清单存在但不可解析，前端/后端判定降级：%s" % err))
        return set()
    if not isinstance(data, dict):
        return set()
    deps = set()
    for key in ("dependencies", "devDependencies", "peerDependencies"):
        block = data.get(key)
        if isinstance(block, dict):
            deps.update(str(name) for name in block)
    return deps


def detect_stack(root, warnings):
    """清单表 → 语言集合 + 栈类型（移动端优先；前后端并存 → 全栈）。"""
    manifests = find_files(root, KNOWN_MANIFESTS)
    languages = []
    for lang, names in LANG_MANIFESTS:
        if any(fnmatch.fnmatch(m, name) for m in manifests for name in names):
            languages.append(lang)
    mobile_hits = [d for d in MOBILE_DIRS if os.path.isdir(os.path.join(root, d))]
    mobile_hits += find_files(root, MOBILE_FILES) + find_files(root, MOBILE_PATHS)
    node_deps = read_node_deps(root, warnings) if "node" in languages else set()
    if node_deps & set(MOBILE_PACKAGES):
        mobile_hits.append("package.json:react-native|expo")

    frontend = bool(node_deps & set(FRONTEND_PACKAGES)) or bool(find_files(root, FRONTEND_FILES))
    backend = bool(set(languages) - {"node"}) or bool(node_deps & set(BACKEND_PACKAGES))
    if "node" in languages and not frontend and not backend:
        frontend = True  # 纯 node 工程默认按浏览器面处理（对齐源 backward compatibility）

    if mobile_hits:
        stack_type = "移动端"
    elif frontend and backend:
        stack_type = "全栈"
    elif frontend:
        stack_type = "前端"
    else:
        stack_type = "后端"

    package_manager = None
    primary = languages[0] if languages else None
    for lang, locks in PACKAGE_MANAGERS:
        if lang == primary:
            for lock, name in locks:
                if os.path.isfile(os.path.join(root, lock)):
                    package_manager = name
                    break
    if package_manager is None:
        package_manager = {"node": "npm", "python": "pip", "java": "gradle", "go": "go modules",
                           "dotnet": "nuget", "ruby": "bundler", "rust": "cargo",
                           "php": "composer"}.get(primary)
    return {"type": stack_type, "language": primary, "languages": languages,
            "package_manager": package_manager, "manifests": manifests,
            "mobile_indicators": sorted(set(mobile_hits)),
            "frontend": frontend, "backend": backend}


def detect_existing(root):
    """既有框架与 CI 平台探测 → (existing, conflicts 素材)。"""
    framework = None
    for name, patterns in FRAMEWORK_CONFIGS:
        if find_files(root, patterns):
            framework = name
            break
    platform = None
    for name, patterns in CI_CONFIGS:
        if find_files(root, patterns):
            platform = name
            break
    return {"framework": framework, "ci": platform}


def read_text_safe(path):
    """只读文本；不可读/非 UTF-8 → ""（探测面不因单个文件崩）。"""
    try:
        with io.open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


def detect_git(root):
    """仓库事实（F-10；源 ci/step-01 §1「Git repository required」）。
    `.git` 目录（常规仓库）或 `.git` 文件（worktree / submodule）都算在场。"""
    git_path = os.path.join(root, ".git")
    repository = os.path.isdir(git_path) or os.path.isfile(git_path)
    remote = None
    text = read_text_safe(os.path.join(git_path, "config"))
    match = re.search(r'\[remote\s+"([^"]+)"\]', text)
    if match:
        remote = match.group(1)
    return {"repository": repository, "remote": remote}


def detect_context(root):
    """架构文档与 auth 线索（F-9；源 fw/step-01 §2）。
    只在已知目录里按模式找（不递归全树）；auth 线索 = 文档正文命中关键词，供 step 1 定点读。"""
    docs = []
    for sub in CONTEXT_DOC_DIRS:
        base = os.path.join(root, sub) if sub else root
        if not os.path.isdir(base):
            continue
        for name in sorted(os.listdir(base)):
            if not os.path.isfile(os.path.join(base, name)):
                continue
            if any(fnmatch.fnmatch(name, pattern) for pattern in CONTEXT_DOC_GLOBS):
                rel = display_path(os.path.join(base, name), root)
                if rel not in docs:
                    docs.append(rel)
    auth = []
    for rel in sorted(docs):
        low = read_text_safe(os.path.join(root, *rel.split("/"))).lower()
        hits = [key for key in AUTH_HINTS if key in low]
        if hits:
            auth.append({"doc": rel, "hints": hits})
    return {"docs": sorted(docs), "auth": auth}


def suggest_for(stack, existing):
    """选型建议（源 step-02 规则）：浏览器 → Playwright（默认）/ Cypress；后端按语言；移动端 → Maestro。"""
    if stack["type"] == "移动端":
        return {"framework": "maestro", "runner": "maestro test", "platform": existing.get("ci"),
                "profile": None, "unit_layer": "按 app 语言选（Jest/Vitest、XCTest、JUnit、flutter test）"}
    if stack["type"] in ("前端", "全栈"):
        profile = "browser-playwright"
        if existing.get("framework") == "cypress":
            profile = "browser-cypress"
        name = "cypress" if profile.endswith("cypress") else "playwright"
        return {"framework": name, "runner": ("npx cypress run" if name == "cypress"
                                              else "npx playwright test"),
                "platform": existing.get("ci"), "profile": profile, "unit_layer": None}
    lang = stack.get("language")
    if lang in BACKEND_PROFILES:
        return {"framework": BACKEND_FRAMEWORKS[lang], "runner": None,
                "platform": existing.get("ci"), "profile": "backend-%s" % lang,
                "unit_layer": None}
    return {"framework": None, "runner": None, "platform": existing.get("ci"),
            "profile": None, "unit_layer": None}


def template_coverage(suggested, stack):
    """模板覆盖面：profile 与 CI 类别是否有模板（移动端无模板覆盖 → HALT 登记）。"""
    profile = suggested.get("profile")
    browser = stack["type"] in ("前端", "全栈") and (profile or "").startswith("browser")
    framework_supported = bool(profile) and os.path.isdir(
        os.path.join(TEMPLATES_DIR, "framework", profile or ""))
    ci_class = "browser" if browser else "backend"
    ci_supported = framework_supported and all(
        os.path.isfile(template_abs(CI_TEMPLATES[platform] % ci_class) or "")
        for platform in CI_PLATFORMS)
    reason = None
    if not framework_supported or not ci_supported:
        reason = ("移动端面（Maestro 设备流 / 设备实验场 runner）无模板覆盖——"
                  "按任务书 §5 裁定 5 + §12.11：HALT + 一行报告 + 登记，不降级 LLM 手写。"
                  if stack["type"] == "移动端" else "profile 无模板目录")
    return {"profiles": sorted(BROWSER_PROFILES + tuple("backend-%s" % p for p in BACKEND_PROFILES)),
            "ci_platforms": list(CI_PLATFORMS), "ci_classes": ["browser", "backend"],
            "framework_supported": framework_supported, "ci_supported": ci_supported,
            "profile": profile, "reason": reason}


def cmd_detect(args):
    root = os.path.abspath(args.project_root)
    out = out_dir(args)
    warnings = []
    stack = detect_stack(root, warnings)
    existing = detect_existing(root)
    suggested = suggest_for(stack, existing)
    coverage = template_coverage(suggested, stack)
    git = detect_git(root)
    context = detect_context(root)
    conflicts = []
    if existing["framework"] and suggested["framework"] and \
            existing["framework"] != suggested["framework"]:
        conflicts.append({"what": "既有测试框架", "where": existing["framework"],
                          "why": "与建议框架 %s 不同：替换属内容决策，须用户确认"
                                 "（引擎不删除、不覆盖任何既有文件）" % suggested["framework"]})
    if existing["ci"] and existing["ci"] not in CI_PLATFORMS:
        conflicts.append({"what": "CI 平台", "where": existing["ci"],
                          "why": "识别到该平台但技能内无模板（circle-ci）：须用户确认改用五平台之一"})
    if stack["manifests"] and (not coverage["framework_supported"]
                               or not coverage["ci_supported"]):
        warnings.append(v("TEMPLATE_UNSUPPORTED", "templates",
                          "模板覆盖面：不支持（%s）" % coverage["reason"]))
    violations = []
    if not stack["manifests"]:
        violations.append(v("MISSING_FILE", ".",
                            "项目清单全不命中（%s 等）——无法判定技术栈，"
                            "本技能 HALT；请在项目根放置清单后重入。"
                            % " / ".join(KNOWN_MANIFESTS[:6])))
    ok = not violations
    counts = {"manifests": len(stack["manifests"]), "languages": len(stack["languages"]),
              "conflicts": len(conflicts)}
    payload = {"ok": ok, "command": "detect",
               "project_root": args.project_root,
               "output_dir": os.path.normpath(out).replace("\\", "/"),
               "stack": stack, "existing": existing, "conflicts": conflicts,
               "suggested": suggested, "templates": coverage,
               "git": git, "context": context,
               "violations": violations, "warnings": warnings, "counts": counts}
    emit(payload, args.json, human_detect)
    return 0 if ok else 1


def human_detect(payload):
    stack = payload["stack"]
    print("栈探测：type=%s language=%s package_manager=%s" % (stack["type"], stack["language"],
                                                          stack["package_manager"]))
    print("既有：framework=%s ci=%s" % (payload["existing"]["framework"],
                                      payload["existing"]["ci"]))
    print("建议：framework=%s platform=%s profile=%s" % (payload["suggested"]["framework"],
                                                       payload["suggested"]["platform"],
                                                       payload["suggested"]["profile"]))
    print("仓库：git=%s remote=%s ｜ 上下文文档 %d 份（auth 线索 %d 份）"
          % (payload["git"]["repository"], payload["git"]["remote"],
             len(payload["context"]["docs"]), len(payload["context"]["auth"])))
    for item in payload["conflicts"]:
        print("冲突：%s（%s）—— %s" % (item["what"], item["where"], item["why"]))
    if not payload["templates"]["framework_supported"] or not payload["templates"]["ci_supported"]:
        print("模板覆盖：不支持（%s）" % payload["templates"]["reason"])


# ---------------------------------------------------------------- scaffold

def prepare_plan(root, plan_path):
    """预检（零写入）→ (plan, prepared, violations, warnings)。
    prepared = [{template, path, target, rendered}]。"""
    violations, warnings = [], []
    data, err = load_json_safe(plan_path)
    if data is None and err is None:
        return None, [], [v("MISSING_FILE", os.path.basename(plan_path),
                            "plan 文件不存在（03/04 步须先写 %s）" % PLAN_JSON)], warnings
    if err is not None:
        return None, [], [v("UNPARSABLE_YAML", os.path.basename(plan_path),
                            "plan 不可解析：%s" % err)], warnings
    if not isinstance(data, dict):
        return None, [], [v("ENTRY_INVALID", os.path.basename(plan_path), "plan 顶层须为对象")], warnings

    setup = data.get("setup")
    if not nonempty(setup) or not SETUP_RE.fullmatch(str(setup)):
        violations.append(v("ENUM_INVALID", "plan.setup", "setup 须为 TF-###（三位零填充）"))
    part = data.get("part")
    if part not in ("框架", "CI"):
        violations.append(v("ENUM_INVALID", "plan.part", "part 须为 框架|CI"))
    subs = data.get("substitutions")
    if not isinstance(subs, dict):
        violations.append(v("ENTRY_INVALID", "plan.substitutions", "substitutions 须为映射"))
        subs = {}
    else:
        for key, value in subs.items():
            if not isinstance(value, str):
                violations.append(v("ENTRY_INVALID", "plan.substitutions.%s" % key,
                                    "取值须为字符串（数字/布尔请写成字符串）"))
    files = data.get("files")
    if not isinstance(files, list) or not files:
        violations.append(v("ENTRY_INVALID", "plan.files", "files 须为非空列表"))
        files = []

    prepared, seen, used = [], set(), set()
    for i, item in enumerate(files):
        where = "plan.files[%d]" % i
        if not isinstance(item, dict):
            violations.append(v("ENTRY_INVALID", where, "条目须为映射"))
            continue
        rel_template = item.get("template")
        rel_path = item.get("path")
        kind = item.get("kind")
        if kind not in FILE_KINDS:
            violations.append(v("ENUM_INVALID", where + ".kind",
                                "kind 越界：%s（合法集 %s）" % (kind, "|".join(FILE_KINDS))))
        err_path = path_form_error(rel_path)
        if err_path is not None:
            violations.append(v("ENUM_INVALID", where + ".path",
                                "path %r 形态非法：%s（对齐 path: 口径）" % (rel_path, err_path)))
        elif rel_path in seen:
            violations.append(v("ENTRY_INVALID", where + ".path", "path %s 在 plan 内重复" % rel_path))
        else:
            seen.add(rel_path)
        abs_tpl = template_abs(rel_template)
        if abs_tpl is None or not os.path.isfile(abs_tpl):
            violations.append(v("MISSING_FILE", where + ".template",
                                "技能内模板不存在：%r（模板集是唯一来源，禁手写冒充）" % rel_template))
            continue
        try:
            with io.open(abs_tpl, "r", encoding="utf-8", newline="") as fh:
                text = fh.read()
        except OSError as e:
            violations.append(v("MISSING_FILE", where + ".template", "模板读取失败：%s" % e))
            continue
        rendered, render_err = render_template(text, subs)
        if render_err is not None:
            if render_err.startswith("占位符未取值"):
                violations.append(v("EMPTY_FIELD", where + ".template", render_err))
            else:
                violations.append(v("ENTRY_INVALID", where + ".template", render_err))
            continue
        declared, _body, _err = parse_template(text)
        used.update(declared or ())
        prepared.append({"template": rel_template, "path": rel_path, "kind": kind,
                         "target": os.path.join(root, *str(rel_path).split("/")),
                         "rendered": rendered})
    extra = sorted(set(subs) - used)
    if extra:
        warnings.append(v("EMPTY_FIELD", "plan.substitutions",
                          "以下取值未被本次模板使用（可共享给另一次 scaffold 调用）：%s"
                          % " ".join(extra)))
    return data, prepared, violations, warnings


def cmd_scaffold(args):
    root = os.path.abspath(args.project_root)
    out = out_dir(args)
    plan_path = args.plan if os.path.isabs(args.plan) else os.path.join(root, args.plan)
    show = display_path(plan_path, root)
    data, prepared, violations, warnings = prepare_plan(root, plan_path)
    written, skipped, conflicts, removed, failed = [], [], [], [], []
    setup = (data or {}).get("setup")
    part = (data or {}).get("part")
    subs = (data or {}).get("substitutions") if isinstance((data or {}).get("substitutions"),
                                                           dict) else {}
    if not violations:
        for entry in prepared:
            target = entry["target"]
            rel = entry["path"]
            if not os.path.exists(target):
                try:
                    write_atomic(target, entry["rendered"])
                except OSError as e:
                    violations.append(v("MISSING_FILE", rel, "写入失败：%s" % e))
                    break
                written.append(rel)
                continue
            try:
                with io.open(target, "r", encoding="utf-8", newline="") as fh:
                    current = fh.read()
            except (OSError, UnicodeDecodeError) as e:
                conflicts.append(rel)
                violations.append(v("FILE_CONFLICT", rel, "既有文件不可读，视为冲突：%s" % e))
                continue
            if current == entry["rendered"]:
                skipped.append(rel)                       # 幂等重入：同模板同 plan → 同字节
            else:
                conflicts.append(rel)
        if conflicts:
            # 回滚 = 撤销本次全部写入：整条拒绝后的净写入为 0，被撤销的路径记 rollback.removed
            pending_written = list(written)
            written = []
            for rel in reversed(pending_written):
                target = os.path.join(root, *rel.split("/"))
                try:
                    os.remove(target)
                    removed.append(rel)
                except OSError as e:
                    failed.append(rel)
                    warnings.append(v("MISSING_FILE", rel,
                                      "回滚删除失败（残留本次已写文件）：%s" % e))
            for rel in conflicts:
                violations.append(v("FILE_CONFLICT", rel,
                                    "目标已存在且内容与渲染结果不同——本技能不覆盖、不 merge 既有文件；"
                                    "请用户裁决（移除/改名旧文件后重入，或把该 path 移出 plan）"))
    pending = []
    for key in PENDING_COMMAND_KEYS:
        value = subs.get(key) if isinstance(subs, dict) else None
        if nonempty(value) and value not in pending:
            pending.append(value)
    ok = not violations
    counts = {"written": len(written), "skipped": len(skipped), "conflicts": len(conflicts),
              "files": len(prepared), "removed": len(removed), "failed_removed": len(failed)}
    payload = {"ok": ok, "command": "scaffold",
               "project_root": args.project_root,
               "output_dir": os.path.normpath(out).replace("\\", "/"),
               "plan": show, "setup": setup, "part": part,
               "written": written, "skipped": skipped, "conflicts": conflicts,
               "rollback": {"removed": removed, "conflicts": conflicts, "failed": failed},
               "pending_commands": pending,
               "violations": violations, "warnings": warnings, "counts": counts}
    emit(payload, args.json, human_scaffold)
    return 0 if ok else 1


def human_scaffold(payload):
    print("scaffold[%s] 写入 %d / 跳过 %d / 冲突 %d"
          % (payload["part"], payload["counts"]["written"], payload["counts"]["skipped"],
             payload["counts"]["conflicts"]))
    for rel in payload["written"]:
        print("+ %s" % rel)
    for rel in payload["skipped"]:
        print("= %s（内容等价，幂等跳过）" % rel)
    for rel in payload["rollback"]["removed"]:
        print("- %s（回滚删除）" % rel)
    if payload["pending_commands"]:
        print("待执行命令（步骤层）：")
        for cmd in payload["pending_commands"]:
            print("  $ %s" % cmd)


# ---------------------------------------------------------------- check

def load_static_checks(output_dir):
    """读 test-plan.yaml 的 static_checks → (entries, skip_reason)。
    三类分支（文件缺席 / 字段缺席 / 列表为空）统一返回 (None, 原因)：跳过对齐判定 + warning。"""
    path = os.path.join(output_dir, TEST_PLAN_FILE)
    data, err = load_yaml_safe(path)
    if data is None and err is None:
        return None, "test-plan.yaml 缺席 → 跳过 CI 三方对齐判定（static_checks 不可得）"
    if err is not None:
        return None, "test-plan.yaml 不可解析 → 跳过 CI 三方对齐判定：%s" % err
    checks = data.get("static_checks") if isinstance(data, dict) else None
    if not isinstance(checks, list) or not checks:
        return None, "test-plan.yaml 的 static_checks 缺席或为空 → 跳过 CI 三方对齐判定"
    entries = []
    for i, item in enumerate(checks):
        if not isinstance(item, dict):
            continue
        entries.append({"order": item.get("order"), "tool": item.get("tool"),
                        "gate": item.get("gate"), "index": i})
    if not entries:
        return None, "test-plan.yaml 的 static_checks 无可解析条目 → 跳过 CI 三方对齐判定"
    return entries, None


def embedded_code_lines(text):
    """粗粒度提取「被 shell 执行的脚本块」行 → [(行号, 行文本)]。
    覆盖：YAML 的 `run:` / `script:` / `command:`（内联值与 `|` / `>` 块标量、列表项）
    与 Jenkins 的 `sh '''…'''`；注释行一律不参与（不执行，模板里的反例都在注释里）。"""
    found = []
    lines = text.splitlines()
    block_indent = None            # YAML 块标量/列表体：进入时的键缩进
    jenkins_quote = None           # Jenkins sh 引号态
    for index, raw in enumerate(lines, start=1):
        stripped = raw.strip()
        if stripped.startswith(COMMENT_LINE_PREFIXES):
            continue
        if jenkins_quote is not None:
            end = raw.find(jenkins_quote)
            if end < 0:
                found.append((index, raw))
                continue
            found.append((index, raw[:end]))
            jenkins_quote = None
            continue
        if block_indent is not None:
            indent = len(raw) - len(raw.lstrip())
            if stripped and indent <= block_indent:
                block_indent = None
            else:
                found.append((index, raw))
                continue
        match = JENKINS_SH_RE.search(raw)
        if match:
            quote = match.group("quote")
            rest = match.group("rest")
            if len(quote) == 3 and quote not in rest:
                jenkins_quote = quote
            elif len(quote) == 1 and quote in rest:
                found.append((index, raw[:match.start("rest") + rest.find(quote)]))
            else:
                found.append((index, rest))
            continue
        match = CODE_KEY_RE.match(raw)
        if not match:
            continue
        rest = match.group("rest").strip()
        if rest and not BLOCK_SCALAR_RE.match(rest):
            found.append((index, raw))
        else:
            block_indent = len(match.group("indent"))
    return found


def scan_ci_injection(text):
    """生成物脚本块内的不安全插值扫描（F-12，源 ci/steps-v/step-01 §2a）→ [(行号, 片段)]。"""
    hits = []
    for lineno, line in embedded_code_lines(text):
        for pattern in (UNSAFE_EXPR_RE, UNSAFE_HARNESS_RE):
            for match in pattern.finditer(line):
                hits.append((lineno, match.group(0)))
    return hits


def check_ci_injection(text, rel_file, violations):
    """脚本块注入扫描的违规落点（只要有 CI 文件就扫，与 mode 无关：手改面同样裸奔）。"""
    for lineno, fragment in scan_ci_injection(text):
        violations.append(v("UNSAFE_INJECTION", "%s:%d" % (rel_file, lineno),
                            "脚本块内直接插值不可信上下文 %r —— 须经 env: / variables: / "
                            "envVariables 中转后以双引号 \"$ENV_VAR\" 引用（inputs 只能是 DATA、"
                            "不能是 COMMAND）" % fragment))


def check_ci_alignment(project_root, output_dir, record, where, violations, warnings):
    """CI 三方对齐（重扫不采信台账）：现场从 test-plan.yaml + CI 文件重算，与台账比对。
    同时执行脚本块注入扫描（F-12）：文件在场即扫，不受 mode / 对齐分支影响。"""
    mode = record.get("mode")
    ci = record.get("ci")
    if not isinstance(ci, dict):
        return
    platform = ci.get("platform")
    rel_file = ci.get("file")
    text = None
    if nonempty(rel_file) and path_form_error(rel_file) is None:
        ci_path = os.path.join(project_root, *str(rel_file).split("/"))
        if os.path.isfile(ci_path):
            try:
                with io.open(ci_path, "r", encoding="utf-8", newline="") as fh:
                    text = fh.read()
            except (OSError, UnicodeDecodeError) as e:
                violations.append(v("MISSING_FILE", str(rel_file), "CI 文件不可读：%s" % e))
                return
    if text is not None:
        check_ci_injection(text, str(rel_file), violations)
    if mode == "框架":
        return
    if platform == "none":
        warnings.append(v("EMPTY_FIELD", where + ".ci.platform",
                          "platform=none → 跳过 CI 三方对齐判定（无流水线文件）"))
        return
    if text is None:
        return

    entries, skip = load_static_checks(output_dir)
    if entries is None:
        warnings.append(v("EMPTY_FIELD", where + ".ci.static_check_alignment", skip))
    else:
        orders = {}
        for entry in entries:
            if isinstance(entry["order"], int):
                orders[entry["order"]] = entry
        ledger = ci.get("static_check_alignment")
        ledger_map = {}
        if isinstance(ledger, list):
            for i, item in enumerate(ledger):
                item_where = "%s.ci.static_check_alignment[%d]" % (where, i)
                shape_ok = (isinstance(item, dict)
                            and isinstance(item.get("order"), int)
                            and isinstance(item.get("in_ci"), bool))
                if not shape_ok:
                    violations.append(v("ENUM_INVALID", item_where,
                                        "条目须为 {order: <int>, in_ci: <bool>}"))
                    continue
                ledger_map[item["order"]] = item["in_ci"]
                if item["order"] not in orders:
                    violations.append(v("UNKNOWN_ID", item_where + ".order",
                                        "order %s 不在 test-plan.yaml 的 static_checks 中" % item["order"]))
        for entry in entries:
            order, gate = entry["order"], entry["gate"]
            if not isinstance(order, int) or not nonempty(entry["tool"]):
                continue
            in_ci = command_in_text(entry["tool"], text)
            if gate == "阻断" and order not in ledger_map:
                violations.append(v("CI_MISALIGNED", "%s.ci.static_check_alignment" % where,
                                    "漏 阻断 条目 order=%s（tool: %s）——阻断 层必录"
                                    % (order, entry["tool"])))
            if order in ledger_map and ledger_map[order] != in_ci:
                violations.append(v("CI_MISALIGNED", "%s.ci.static_check_alignment" % where,
                                    "order=%s（tool: %s）台账 in_ci=%s，现场重算=%s"
                                    "（重扫不采信台账）"
                                    % (order, entry["tool"], ledger_map[order], in_ci)))
    gates = ci.get("gates")
    if isinstance(gates, dict):
        for key in ("p0", "p1"):
            value = gates.get(key)
            if nonempty(value) and str(value) not in text:
                violations.append(v("CI_MISALIGNED", "%s.ci.gates.%s" % (where, key),
                                    "CI 文件缺阈值字面量 %r（事实源 = 台账 ci.gates，经 plan "
                                    "substitutions 注入）" % value))


def check_record(project_root, output_dir, index, record, final, show, warnings):
    violations = []
    where = "%s.setups[%d]" % (show, index)
    if not isinstance(record, dict):
        return [v("EMPTY_FIELD", where, "记录不是映射")]

    rid = record.get("id")
    if not nonempty(rid):
        violations.append(v("EMPTY_FIELD", where + ".id", "id 缺失"))
    elif not SETUP_RE.fullmatch(str(rid)):
        violations.append(v("ENUM_INVALID", where + ".id", "id 须为 TF-###（三位零填充），实为 %s" % rid))
    date = record.get("date")
    if not nonempty(date) or not DATE_RE.fullmatch(str(date)):
        violations.append(v("EMPTY_FIELD", where + ".date", "date 须为 YYYY-MM-DD"))
    status = record.get("status")
    if status not in ("草稿", "已定稿"):
        violations.append(v("ENUM_INVALID", where + ".status", "status 越界：%s（合法集 草稿|已定稿）" % status))
    mode = record.get("mode")
    if mode not in MODES:
        violations.append(v("ENUM_INVALID", where + ".mode", "mode 越界：%s（合法集 %s）"
                            % (mode, "|".join(MODES))))

    stack = record.get("stack")
    stack_type = None
    if not isinstance(stack, dict):
        violations.append(v("EMPTY_FIELD", where + ".stack", "stack 缺失或不是映射"))
    else:
        stack_type = stack.get("type")
        if stack_type not in STACK_TYPES:
            violations.append(v("ENUM_INVALID", where + ".stack.type",
                                "stack.type 越界：%s（合法集 %s）" % (stack_type, "|".join(STACK_TYPES))))
        for key in ("language", "package_manager"):
            if not nonempty(stack.get(key)):
                violations.append(v("EMPTY_FIELD", where + ".stack." + key, "%s 为空" % key))

    framework = record.get("framework")
    if framework is not None and not isinstance(framework, dict):
        violations.append(v("EMPTY_FIELD", where + ".framework", "framework 不是映射"))
    elif isinstance(framework, dict):
        for key in ("name", "runner", "reason"):
            if not nonempty(framework.get(key)):
                violations.append(v("EMPTY_FIELD", "%s.framework.%s" % (where, key),
                                    "framework.%s 为空（选型理由源 02 步保留）" % key))
    elif final:
        violations.append(v("EMPTY_FIELD", where + ".framework", "--final 要求 framework 非空"))

    if stack_type in ("移动端", "全栈"):
        unit = record.get("unit_layer")
        if not isinstance(unit, dict) or not nonempty(unit.get("name")):
            violations.append(v("EMPTY_FIELD", where + ".unit_layer",
                                "stack.type=%s 时 unit_layer.name 必填" % stack_type))

    files = record.get("files")
    if not isinstance(files, list) or not files:
        violations.append(v("EMPTY_FIELD", where + ".files", "files 须为非空列表"))
    else:
        for i, item in enumerate(files):
            item_where = "%s.files[%d]" % (where, i)
            if not isinstance(item, dict):
                violations.append(v("EMPTY_FIELD", item_where, "条目须为映射"))
                continue
            rel = item.get("path")
            err = path_form_error(rel)
            if err is not None:
                violations.append(v("ENUM_INVALID", item_where + ".path",
                                    "path %r 形态非法：%s（对齐 path: 口径）" % (rel, err)))
                continue
            if item.get("kind") not in FILE_KINDS:
                violations.append(v("ENUM_INVALID", item_where + ".kind",
                                    "kind 越界：%s" % item.get("kind")))
            if item.get("action") not in ACTIONS:
                violations.append(v("ENUM_INVALID", item_where + ".action",
                                    "action 越界：%s（合法集 新建|更新）" % item.get("action")))
            if not os.path.isfile(os.path.join(project_root, *str(rel).split("/"))):
                violations.append(v("MISSING_FILE", rel,
                                    "台账声明的生成文件不在场（action=%s）" % item.get("action")))

    checks = record.get("checks")
    failed = 0
    if not isinstance(checks, list):
        violations.append(v("EMPTY_FIELD", where + ".checks", "checks 缺失（无命令写空列表）"))
    else:
        for i, item in enumerate(checks):
            item_where = "%s.checks[%d]" % (where, i)
            if not isinstance(item, dict):
                violations.append(v("EMPTY_FIELD", item_where, "条目须为映射"))
                continue
            if not nonempty(item.get("command")):
                violations.append(v("EMPTY_FIELD", item_where + ".command", "command 为空"))
            result = item.get("result")
            if result not in CHECK_RESULTS:
                violations.append(v("ENUM_INVALID", item_where + ".result",
                                    "result 越界：%s（合法集 通过|失败）" % result))
            if result == "失败":
                failed += 1
                if not nonempty(item.get("note")):
                    violations.append(v("EMPTY_FIELD", item_where + ".note",
                                        "result=失败 时 note 必填（失败不得静默）"))
        if failed:
            warnings.append(v("EMPTY_FIELD", where + ".checks",
                              "checks 中 result: 失败 共 %d 条（环境面/人工处置项，已记 note）："
                              "--final 只记 warning、不拒绝；产物面失败须修后重跑，"
                              "修不了即停下报用户" % failed))

    ci = record.get("ci")
    if ci is not None and not isinstance(ci, dict):
        violations.append(v("EMPTY_FIELD", where + ".ci", "ci 不是映射"))
    elif isinstance(ci, dict):
        platform = ci.get("platform")
        if platform not in CI_PLATFORMS + ("none",):
            violations.append(v("ENUM_INVALID", where + ".ci.platform",
                                "platform 越界：%s（合法集 %s|none）"
                                % (platform, "|".join(CI_PLATFORMS))))
        rel_file = ci.get("file")
        if platform == "none":
            if nonempty(rel_file):
                violations.append(v("ENUM_INVALID", where + ".ci.file",
                                    "platform=none 时省略 file（schema 明文）"))
        elif platform in CI_PLATFORMS:
            if not nonempty(rel_file):
                violations.append(v("MISSING_FILE", where + ".ci.file",
                                    "platform=%s 时 ci.file 必填" % platform))
            else:
                err = path_form_error(rel_file)
                if err is not None:
                    violations.append(v("ENUM_INVALID", where + ".ci.file",
                                        "ci.file %r 形态非法：%s" % (rel_file, err)))
                elif not os.path.isfile(os.path.join(project_root, *str(rel_file).split("/"))):
                    violations.append(v("MISSING_FILE", str(rel_file), "CI 流水线文件不在场"))
        stages = ci.get("stages")
        if not isinstance(stages, list) or not all(nonempty(s) for s in stages):
            violations.append(v("EMPTY_FIELD", where + ".ci.stages",
                                "stages 须为非空字符串列表（%s）" % "|".join(STAGE_NAMES)))
        else:
            unknown = [s for s in stages if str(s) not in STAGE_NAMES]
            if unknown:
                warnings.append(v("ENUM_INVALID", where + ".ci.stages",
                                  "非标准阶段名（源五阶段之外的扩展）：%s" % " ".join(map(str, unknown))))
        gates = ci.get("gates")
        if not isinstance(gates, dict):
            violations.append(v("EMPTY_FIELD", where + ".ci.gates", "gates 须为 {p0, p1}"))
        else:
            for key in ("p0", "p1"):
                if not nonempty(gates.get(key)):
                    violations.append(v("EMPTY_FIELD", "%s.ci.gates.%s" % (where, key), "%s 为空" % key))
                elif final and str(gates.get(key)) != "100%":
                    violations.append(v("ENUM_INVALID", "%s.ci.gates.%s" % (where, key),
                                        "diy 口径拉满为 100%%（2026-09-15 用户裁定；源 P1≥95%% 已作废），实为 %s"
                                        % gates.get(key)))
        alignment = ci.get("static_check_alignment")
        if alignment is not None and not isinstance(alignment, list):
            violations.append(v("EMPTY_FIELD", where + ".ci.static_check_alignment",
                                "static_check_alignment 须为列表"))
        check_ci_alignment(project_root, output_dir, record, where, violations, warnings)

    deferred = record.get("deferred")
    if not isinstance(deferred, list):
        violations.append(v("EMPTY_FIELD", where + ".deferred",
                            "deferred 须为列表（无入队写空列表）"))
    else:
        for i, item in enumerate(deferred):
            if not nonempty(item) or not DA_RE.fullmatch(str(item)):
                violations.append(v("ENUM_INVALID", "%s.deferred[%d]" % (where, i),
                                    "deferred 条目须为 DA-###（ID 引用 deferred-actions.yaml）"))
    open_questions = record.get("open_questions")
    if not isinstance(open_questions, list):
        violations.append(v("EMPTY_FIELD", where + ".open_questions", "open_questions 须为列表"))

    if final:
        if any("[假设]" in s for s in collect_strings(record)):
            violations.append(v("ASSUMPTION_PRESENT", where, "--final 要求零 [假设]"))
        if mode in ("CI", "两者"):
            if not isinstance(ci, dict):
                violations.append(v("EMPTY_FIELD", where + ".ci", "mode=%s 时 ci 段必填" % mode))
            else:
                if ci.get("platform") not in CI_PLATFORMS:
                    violations.append(v("ENUM_INVALID", where + ".ci.platform",
                                        "mode=%s 时 platform 须为五平台之一（none 不成立）" % mode))
                if not isinstance(ci.get("static_check_alignment"), list):
                    violations.append(v("EMPTY_FIELD", where + ".ci.static_check_alignment",
                                        "mode=%s 时 static_check_alignment 必填（可为空列表）" % mode))
    return violations


def count_by(records, key, sub=None):
    counts = {}
    for record in records:
        if not isinstance(record, dict):
            continue
        value = record.get(key)
        if sub is not None and isinstance(value, dict):
            value = value.get(sub)
        if nonempty(value):
            counts[str(value)] = counts.get(str(value), 0) + 1
    return counts


def count_items(records, key):
    total = 0
    for record in records:
        if isinstance(record, dict) and isinstance(record.get(key), list):
            total += len(record[key])
    return total


def cmd_check(args):
    root = os.path.abspath(args.project_root)
    out = out_dir(args)
    path = os.path.join(out, TF_FILE)
    show = display_path(path, root)
    violations, warnings, records = [], [], []
    data, err = load_yaml_safe(path)
    if data is None and err is None:
        violations.append(v("MISSING_FILE", show, "%s 不存在（先完成一次测试基建会话）" % TF_FILE))
    elif err is not None:
        violations.append(v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err))
    elif not isinstance(data, dict):
        violations.append(v("EMPTY_FIELD", show, "顶层不是映射（须为 project + setups）"))
    else:
        project = data.get("project")
        if project is not None and not isinstance(project, dict):
            violations.append(v("EMPTY_FIELD", show + " project", "project 不是映射"))
        if data.get("revisions") is not None and not isinstance(data.get("revisions"), list):
            violations.append(v("EMPTY_FIELD", show + " revisions", "revisions 不是列表"))
        raw = data.get("setups")
        if raw is None:
            violations.append(v("EMPTY_FIELD", show + " setups", "setups 缺失（无记录写空列表）"))
        elif not isinstance(raw, list):
            violations.append(v("EMPTY_FIELD", show + " setups", "setups 不是列表"))
        else:
            records = raw
            seen = set()
            for i, record in enumerate(records):
                violations += check_record(root, out, i, record, args.final, show, warnings)
                if isinstance(record, dict) and nonempty(record.get("id")):
                    rid = str(record["id"])
                    if rid in seen:
                        violations.append(v("DUPLICATE_ID", "%s.setups[%d].id" % (show, i),
                                            "记录 ID %s 重复（TF ID 稳定不重用）" % rid))
                    seen.add(rid)
            if args.final and not records:
                violations.append(v("EMPTY_FIELD", show + " setups", "--final 要求至少 1 条记录"))
    counts = {"setups": len(records), "by_mode": count_by(records, "mode"),
              "by_status": count_by(records, "status"),
              "by_platform": count_by(records, "ci", "platform"),
              "files": count_items(records, "files"), "checks": count_items(records, "checks"),
              "deferred": count_items(records, "deferred")}
    ok = not violations
    payload = {"ok": ok, "command": "check", "project_root": args.project_root,
               "output_dir": os.path.normpath(out).replace("\\", "/"), "final": args.final,
               "violations": violations, "warnings": warnings, "counts": counts}
    emit(payload, args.json, human_check)
    return 0 if ok else 1


def human_check(payload):
    if payload["ok"]:
        print("PASS：%s 校验通过（setups=%d）" % (TF_FILE, payload["counts"]["setups"]))
        return
    print("FAIL：")
    for item in payload["violations"]:
        print("- %s %s: %s" % (item["code"], item["where"], item["msg"]))


# ---------------------------------------------------------------- CLI

def emit(payload, as_json, human_fn):
    if as_json:
        print(json.dumps(payload, ensure_ascii=False))
        return
    for item in payload["warnings"]:
        sys.stderr.write("warning: %s %s: %s\n" % (item["code"], item["where"], item["msg"]))
    human_fn(payload)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(
        description="diy-test-framework 确定性引擎：栈探测（detect）+ 模板渲染落盘（scaffold）"
                    "+ 台账与 CI 三方对齐校验（check）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("detect", help="栈/语言/包管理器/既有框架/CI 平台探测（只读；无清单 → 拒绝）")
    d.add_argument("--project-root", default=".", help="项目根（默认 .）")
    d.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    d.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    d.set_defaults(func=cmd_detect)

    s = sub.add_parser("scaffold", help="按 plan 渲染模板写项目（只写新文件；冲突即回滚 + 整条拒绝）")
    s.add_argument("--plan", required=True, help="plan JSON 路径（相对 project-root 或绝对路径）")
    s.add_argument("--project-root", default=".", help="项目根（默认 .）")
    s.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    s.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    s.set_defaults(func=cmd_scaffold)

    c = sub.add_parser("check", help="校验 test-framework.yaml（schema/枚举/路径/CI 三方对齐）")
    c.add_argument("--project-root", default=".", help="项目根（默认 .）")
    c.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    c.add_argument("--final", action="store_true",
                   help="定稿校验：zero [假设] + framework 非空 + ci 段完整 + 阈值拉满 100%")
    c.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    c.set_defaults(func=cmd_check)

    args = ap.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
