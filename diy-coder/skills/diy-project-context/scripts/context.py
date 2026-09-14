# -*- coding: utf-8 -*-
"""diy-project-context 确定性引擎：棕地扫描（scan）+ project-context.yaml 校验（check）。

来源与分工（B1 批任务书 §7；能力蓝本 = bmad-document-project + bmad-generate-project-context）：
  scan   只读扫描，绝不写文件：部件探测（多部件/单仓识别）、项目类型分类
         （documentation-requirements.csv 的 key_file_patterns 判据）、清单解析
         （package.json / pyproject.toml / Cargo.toml / go.mod / pom.xml / requirements.txt /
         pubspec.yaml / composer.json / *.csproj 按存在性探测）。语言无关：先探测再解析，
         未知清单降级「存在但未解析」+ MANIFEST_UNPARSED warning，不崩、不假设特定工具链。
         另有既有文档发现（源 full-scan step-2 的 README/ARCHITECTURE/API/DEPLOYMENT/docs 模式）
         与源码树渲染（深度/条目上限为内置常量）。scan_level 三档：quick=模式分析不读源码；
         deep=加源文件计数；exhaustive=再加 LOC（读文件，受文件数/字节上限约束）。
         部件/类型判定是启发式——LLM 在步骤 01 与用户确认（源 full-scan step-1 同样要求确认）。
  check  校验 {output_dir}/project-context.yaml：schema / 枚举 / scan.parts 非空 /
         rules 的 PC-### 唯一与类别枚举；--previous 比对旧稿 PC-### 集合（rescan 防丢规则，
         旧有新无 → ID_UNSTABLE）；--final 附加定稿义务（zero [ASSUMPTION]、rules 非空且每条
         rule/why/where 非空、stack 非空）。exit 0 唯一放行。

新码登记（batch3-contract §3 冻结集之外）：
  - 违规码：无——全部复用冻结集（MISSING_FILE / UNPARSABLE_YAML / ENUM_INVALID / EMPTY_FIELD /
    DUPLICATE_ID / UNKNOWN_ID / ID_UNSTABLE / ASSUMPTION_PRESENT）。
  - warning 码：MANIFEST_UNPARSED（探测到清单但无内置解析器或解析失败：降级 + 结构化 warning，
    由 LLM 在步骤 01/02 向用户补齐，绝不静默）。

禁手写实例解析（任务书 §2.2）：引擎不做 --instance / 白名单 / 目录推导；--output-dir 必填，
由调用方传入（SKILL.md 从 diyc.py resolve 取）。源 project-scan-report.json 不迁——进度状态
落 {output_dir}/project-context.yaml 的 scan 字段，不建任何状态散文件（任务书 §0 纪律 1）。
"""
# trace: B1 diy-project-context 验收 #3（门禁零产出）/#4（ID 链）/#12（领域引擎接线）
import argparse
import io
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

import yaml

try:  # Python 3.11+ 标准库；3.10 环境降级为「存在但未解析」warning（语言无关承诺）
    import tomllib as _toml
except ImportError:  # pragma: no cover - 取决于运行时版本
    _toml = None

CTX_FILE = "project-context.yaml"

SCAN_MODES = ("full", "rescan", "deep-dive")
SCAN_LEVELS = ("quick", "deep", "exhaustive")
# 规则类别 = 源 generate-project-context step-02/step-03 的七个规则域（Technology Stack &
# Versions / Language / Framework / Testing / Quality & Style / Workflow / Critical Don't-Miss）
RULE_CATEGORIES = ("stack", "language", "framework", "testing", "quality", "workflow",
                   "anti-pattern")
# 部件类型 = documentation-requirements.csv 的项目类型列（11 行；源文宣称 12 类，CSV 实际 11 行）
# + unknown（畸形/未解析清单的降级值，与 scan 回执自洽）
PART_TYPES = ("web", "mobile", "backend", "cli", "library", "desktop", "game", "data",
              "extension", "infra", "embedded", "unknown")

PC_RE = re.compile(r"PC-\d{3}")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")

# 扫描排除目录（源码树/文档发现共用）：版本库、包缓存、构建产物、编辑器与 diy 自身产物
EXCLUDE_DIRS = frozenset({
    ".git", ".hg", ".svn", ".claude", ".analysis", ".view", ".idea", ".vscode",
    "node_modules", "__pycache__", ".venv", "venv", "env", "dist", "build", "coverage",
    ".next", ".nuxt", "target", "out", ".pytest_cache", ".mypy_cache", ".ruff_cache",
})
TREE_MAX_DEPTH = 3
TREE_MAX_ENTRIES = 240
DOCS_MAX_DEPTH = 4
DOCS_MAX_ENTRIES = 120
SOURCE_MAX_DEPTH = 6
LOC_MAX_FILES = 400
LOC_MAX_BYTES = 512 * 1024

SOURCE_EXTS = (".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".go", ".rs", ".java",
               ".kt", ".kts", ".cs", ".c", ".cc", ".cpp", ".cxx", ".h", ".hpp", ".rb", ".php",
               ".swift", ".m", ".mm", ".dart", ".scala", ".sh", ".sql", ".vue", ".svelte")

# 清单探测表：文件名 → 解析形态（None = 存在性标记：识别生态，但不解析依赖）
MANIFEST_KINDS = (
    ("package.json", "package-json"),
    ("composer.json", "package-json"),
    ("pyproject.toml", "toml"),
    ("Cargo.toml", "toml"),
    ("go.mod", "go-mod"),
    ("pom.xml", "xml"),
    ("requirements.txt", "requirements"),
    ("pubspec.yaml", "yaml"),
    ("Gemfile", None),
    ("build.gradle", None),
    ("setup.py", None),
    ("CMakeLists.txt", None),
    ("Makefile", None),
    ("platformio.ini", None),
    ("dbt_project.yml", None),
    ("airflow.cfg", None),
)
# 信号文件：参与部件证据与语言判定，但不是待解析清单（不产 warning）
SIGNAL_MARKERS = ("tsconfig.json", "manifest.json")
# 标记清单的语言提示（仅为降低 LLM 猜测成本；类型一律 unknown 由人确认）
MARKER_LANGUAGE = {
    "Gemfile": "Ruby",
    "build.gradle": "Java/Kotlin",
    "setup.py": "Python",
    "CMakeLists.txt": "C/C++",
    "Makefile": "",
    "platformio.ini": "C/C++",
    "dbt_project.yml": "SQL",
    "airflow.cfg": "Python",
}
# 非清单但决定项目类型的强标记：glob → 类型（CSV key_file_patterns 的高置信子集）
MARKER_TYPE_GLOBS = (
    ("*.tf", "infra"), ("*.tfvars", "infra"), ("pulumi.yaml", "infra"), ("cdk.json", "infra"),
    ("*.ino", "embedded"), ("project.godot", "game"), ("*.unity", "game"), ("*.uproject", "game"),
)
# 依赖名 → 框架（有序：先具体后一般；命中即停）
FRAMEWORK_HINTS = (
    ("react-native", "react-native"), ("expo", "expo"), ("next", "next"), ("nuxt", "nuxt"),
    ("@angular/core", "angular"), ("svelte", "svelte"), ("vue", "vue"), ("react", "react"),
    ("electron", "electron"), ("@tauri-apps/api", "tauri"), ("tauri", "tauri"),
    ("@nestjs/core", "nestjs"), ("fastify", "fastify"), ("express", "express"),
    ("fastapi", "fastapi"), ("django", "django"), ("flask", "flask"),
    ("apache-airflow", "airflow"), ("dbt-core", "dbt"), ("pandas", "pandas"),
    ("gin-gonic/gin", "gin"), ("labstack/echo", "echo"), ("gofiber/fiber", "fiber"),
    ("google.golang.org/grpc", "grpc"), ("laravel/framework", "laravel"),
    ("symfony/", "symfony"), ("spring-boot", "spring-boot"), ("flutter", "flutter"),
    ("axum", "axum"), ("actix-web", "actix"),
)
# 既有文档发现规则（源 full-scan step-2）：文件名 → 类别；再按目录语义兜底
DOC_NAME_RULES = (
    ("readme", ("readme.md", "readme.rst", "readme.txt")),
    ("contributing", ("contributing.md", "contributing.rst")),
    ("architecture", ("architecture.md", "architecture.txt")),
    ("deployment", ("deployment.md", "deploy.md")),
    ("api", ("api.md",)),
)
DOC_DIR_RULES = (
    ("architecture", ("docs/architecture/",)),
    ("api", ("docs/api/",)),
    ("deployment", ("docs/deployment/",)),
)
DOC_DIRS = ("docs", "documentation", ".github")


def v(code, where, msg):
    return {"code": code, "where": where, "msg": msg}


def nonempty(value):
    return value is not None and str(value).strip() != ""


def display_path(path, project_root):
    """where 显示口径（对齐 diyc/checkpoint）：正斜杠 + 相对 project-root；越界则绝对路径。"""
    try:
        rel = os.path.relpath(path, project_root)
    except ValueError:
        rel = os.path.abspath(path)
    if rel.startswith(".."):
        return os.path.abspath(path).replace("\\", "/")
    return rel.replace("\\", "/")


def slash(path):
    return str(path).replace("\\", "/")


def load_yaml_safe(path):
    """读 YAML：(data, err)。文件缺失 → (None, None)；空文件 → ({}, None)；损坏 → (None, 原因)。"""
    if not os.path.isfile(path):
        return None, None
    try:
        with io.open(path, "r", encoding="utf-8") as f:
            return (yaml.safe_load(f) or {}), None
    except yaml.YAMLError as e:
        return None, str(e)
    except OSError as e:
        return None, str(e)


# ---- 清单解析（语言无关：先探测再解析；解析失败/无解析器 → 降级，不崩） ----

def clean_version(raw):
    """依赖声明 → 版本号：去掉 ^ ~ >= 等前缀与多余比较符；无法判定 → 原样。"""
    text = str(raw or "").strip()
    m = re.search(r"\d+(?:\.\d+)*", text)
    return m.group(0) if m else text


def first_hit(haystack, hints):
    """依赖集合（可迭代名）→ (命中的依赖名, 框架名)；无命中 → (None, "")。

    匹配含后缀式：go.mod / Maven 的依赖是全路径（github.com/gin-gonic/gin），
    endswith("/" + dep) 命中断言表里写的生态短名（gin-gonic/gin）。
    """
    names = {str(n) for n in haystack}
    for dep, framework in hints:
        if dep in names or any(name.endswith("/" + dep) for name in names):
            return dep, framework
    return None, ""


def degraded(path, language, reason, project_root):
    """降级回执：清单存在但未解析（不猜测、不崩溃）。"""
    return {
        "language": language,
        "framework": "",
        "version": "",
        "notes": "清单存在但未解析：%s" % reason,
        "unparsed": True,
        "deps": (),
        "warning": v("MANIFEST_UNPARSED", display_path(path, project_root),
                     "清单存在但未解析（%s）：语言与依赖待人工确认，不猜测" % reason),
    }


def parse_package_json(path, part_dir, project_root):
    try:
        with io.open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (ValueError, OSError) as e:
        return degraded(path, "PHP" if os.path.basename(path) == "composer.json" else "JavaScript",
                        str(e), project_root)
    if not isinstance(data, dict):
        return degraded(path, "JavaScript", "顶层不是对象", project_root)
    deps = []
    for key in ("dependencies", "devDependencies", "peerDependencies"):
        value = data.get(key)
        if isinstance(value, dict):
            deps += list(value.keys())
    dep, framework = first_hit(deps, FRAMEWORK_HINTS)
    version = ""
    if dep:
        for key in ("dependencies", "devDependencies", "peerDependencies"):
            value = data.get(key)
            if isinstance(value, dict) and dep in value:
                version = clean_version(value[dep])
                break
    is_php = os.path.basename(path) == "composer.json"
    language = "PHP" if is_php else (
        "TypeScript" if (os.path.isfile(os.path.join(part_dir, "tsconfig.json"))
                         or "typescript" in deps) else "JavaScript")
    return {
        "language": language,
        "framework": framework,
        "version": version,
        "notes": "",
        "unparsed": False,
        "deps": tuple(deps),
        "package_name": str(data.get("name") or ""),
        "has_bin": bool(data.get("bin")),
        "warning": None,
    }


def parse_toml(path, part_dir, project_root):
    name = os.path.basename(path)
    language = "Python" if name == "pyproject.toml" else "Rust"
    if _toml is None:
        return degraded(path, language, "运行环境无 tomllib（Python < 3.11）", project_root)
    try:
        with io.open(path, "rb") as f:
            data = _toml.load(f)
    except (ValueError, OSError) as e:
        return degraded(path, language, str(e), project_root)
    if not isinstance(data, dict):
        return degraded(path, language, "顶层不是表", project_root)
    deps = []
    section = data.get("project") if isinstance(data.get("project"), dict) else {}
    if isinstance(section.get("dependencies"), list):
        deps += [str(d).split("[")[0].split(">")[0].split("=")[0].strip()
                 for d in section["dependencies"]]
    optional = section.get("optional-dependencies")
    if isinstance(optional, dict):
        for value in optional.values():
            if isinstance(value, list):
                deps += [str(d).split("[")[0].split(">")[0].split("=")[0].strip() for d in value]
    poetry = ((data.get("tool") or {}).get("poetry")
              if isinstance(data.get("tool"), dict) else None)
    if isinstance(poetry, dict):
        for key in ("dependencies", "dev-dependencies"):
            if isinstance(poetry.get(key), dict):
                deps += [k for k in poetry[key] if k != "python"]
    cargo = data.get("package") if isinstance(data.get("package"), dict) else {}
    if isinstance(cargo.get("name"), str) and not section.get("name"):
        section = cargo
    for key in ("dependencies", "dev-dependencies"):
        value = data.get(key) if name == "Cargo.toml" else None
        if isinstance(value, dict):
            deps += [k for k in value if k != "python"]
    dep, framework = first_hit(deps, FRAMEWORK_HINTS)
    version = clean_version(section.get("version")) if section.get("version") else ""
    return {
        "language": language,
        "framework": framework,
        "version": version,
        "notes": "",
        "unparsed": False,
        "deps": tuple(deps),
        "package_name": str(section.get("name") or ""),
        "has_lib": isinstance(data.get("lib"), dict),
        "has_bin": False,
        "warning": None,
    }


def parse_go_mod(path, part_dir, project_root):
    try:
        with io.open(path, "r", encoding="utf-8") as f:
            text = f.read()
    except OSError as e:
        return degraded(path, "Go", str(e), project_root)
    module = re.search(r"^module\s+(\S+)", text, re.MULTILINE)
    goversion = re.search(r"^go\s+(\S+)", text, re.MULTILINE)
    # 依赖形态：路径式模块名 + 版本（require 单行与 require (...) 块同式）；
    # 去掉语义导入版本后缀 /vN，否则 labstack/echo/v4 之类命不中生态短名
    deps = [re.sub(r"/v\d+$", "", dep)
            for dep in re.findall(r"([\w.\-]+\.[\w.\-]+/[\w.\-/]+)\s+v\d\S*", text)]
    _, framework = first_hit(deps, FRAMEWORK_HINTS)
    return {
        "language": "Go",
        "framework": framework,
        "version": goversion.group(1) if goversion else "",
        "notes": "module %s" % module.group(1) if module else "",
        "unparsed": False,
        "deps": tuple(deps),
        "package_name": module.group(1) if module else "",
        "has_bin": False,
        "warning": None,
    }


def parse_xml(path, part_dir, project_root):
    is_csproj = path.lower().endswith(".csproj")
    language = "C#" if is_csproj else "Java"
    try:
        with io.open(path, "r", encoding="utf-8") as f:
            text = f.read()
        root = ET.fromstring(text)
    except (ET.ParseError, OSError) as e:
        return degraded(path, language, str(e), project_root)
    body = re.sub(r"\{[^}]+\}", "", text)  # 去 XML 命名空间前缀，便于键名匹配
    art = re.search(r"<artifactId>\s*([^<]+?)\s*</artifactId>", body)
    ver = re.search(r"<version>\s*([^<]+?)\s*</version>", body)
    _, framework = first_hit(re.findall(r"<artifactId>\s*([^<]+?)\s*</artifactId>", body)
                             + re.findall(r"PackageReference[^>]*Include=\"([^\"]+)\"", body),
                             FRAMEWORK_HINTS)
    return {
        "language": language,
        "framework": framework,
        "version": ver.group(1) if ver else "",
        "notes": root.tag.split("}")[-1] if root.tag else "",
        "unparsed": False,
        "deps": (),
        "package_name": art.group(1) if art else "",
        "has_bin": False,
        "csproj_desktop": bool(re.search(r"WPF|WinForms|WindowsForms|MAUI|Avalonia", body, re.I)),
        "warning": None,
    }


def parse_requirements(path, part_dir, project_root):
    try:
        with io.open(path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
    except OSError as e:
        return degraded(path, "Python", str(e), project_root)
    deps = [re.split(r"[<>=!\[;]", line.strip(), 1)[0].strip()
            for line in lines
            if line.strip() and not line.strip().startswith("#")]
    _, framework = first_hit(deps, FRAMEWORK_HINTS)
    return {
        "language": "Python",
        "framework": framework,
        "version": "",
        "notes": "requirements（%d 条）" % len(deps),
        "unparsed": False,
        "deps": tuple(deps),
        "package_name": "",
        "has_bin": False,
        "warning": None,
    }


def parse_pubspec(path, part_dir, project_root):
    data, err = load_yaml_safe(path)
    if err is not None or not isinstance(data, dict):
        return degraded(path, "Dart", err or "顶层不是映射", project_root)
    deps = []
    for key in ("dependencies", "dev_dependencies"):
        if isinstance(data.get(key), dict):
            deps += list(data[key].keys())
    _, framework = first_hit(deps, FRAMEWORK_HINTS)
    return {
        "language": "Dart",
        "framework": framework,
        "version": str(data.get("version") or ""),
        "notes": "",
        "unparsed": False,
        "deps": tuple(deps),
        "package_name": str(data.get("name") or ""),
        "has_bin": False,
        "warning": None,
    }


def parse_marker(path, part_dir, project_root):
    """存在性标记清单：识别生态但不解析依赖（语言提示来自 MARKER_LANGUAGE）。"""
    name = os.path.basename(path)
    language = MARKER_LANGUAGE.get(name, "")
    return degraded(path, language, "无内置解析器（%s）" % (name or path), project_root)


def part_manifest_files(part_dir, project_root):
    """部件根的清单证据清单（真实清单 + 信号文件），for receipt `manifests`。"""
    names = [name for name, _ in MANIFEST_KINDS] + list(SIGNAL_MARKERS)
    return [display_path(os.path.join(part_dir, name), project_root)
            for name in names if os.path.isfile(os.path.join(part_dir, name))]


PARSERS = {
    "package-json": parse_package_json,
    "toml": parse_toml,
    "go-mod": parse_go_mod,
    "xml": parse_xml,
    "requirements": parse_requirements,
    "yaml": parse_pubspec,
}


def probe_manifests(part_dir, project_root):
    """探测部件根清单：返回 (解析结果列表, warnings)。未知/无解析器清单降级，不崩。"""
    found = []
    warnings = []
    import glob as _glob
    for filename, kind in MANIFEST_KINDS:
        path = os.path.join(part_dir, filename)
        if not os.path.isfile(path):
            continue
        if kind is None:
            found.append(parse_marker(path, part_dir, project_root))
        else:
            found.append(PARSERS[kind](path, part_dir, project_root))
    for pattern in ("*.csproj",):
        for path in _glob.glob(os.path.join(part_dir, pattern)):
            found.append(parse_xml(path, part_dir, project_root))
    for entry in found:
        if entry.get("warning"):
            warnings.append(entry["warning"])
    return found, warnings


def marker_type(part_dir):
    """强类型标记（CSV key_file_patterns 高置信子集）→ 类型 | None。"""
    import glob as _glob
    for pattern, ptype in MARKER_TYPE_GLOBS:
        if _glob.glob(os.path.join(part_dir, pattern)):
            return ptype
    return None


def classify_part(part_dir, manifests):
    """部件类型分类（启发式；LLM 在步骤 01 与用户确认）。CSV 的 key_file_patterns 判据。"""
    strong = marker_type(part_dir)
    if strong:
        return strong
    names = {m.get("package_name", "") for m in manifests}
    deps = set()
    for entry in manifests:
        deps.update(entry.get("deps") or ())
    _, framework = first_hit(deps, FRAMEWORK_HINTS)
    if framework in ("react-native", "expo", "flutter"):
        return "mobile"
    if framework in ("electron", "tauri"):
        return "desktop"
    if framework in ("next", "nuxt", "react", "vue", "svelte", "angular"):
        return "extension" if os.path.isfile(os.path.join(part_dir, "manifest.json")) else "web"
    if framework in ("airflow", "dbt"):
        return "data"
    if framework in ("fastapi", "django", "flask", "nestjs", "express", "fastify",
                     "spring-boot", "laravel", "symfony", "gin", "echo", "fiber", "grpc",
                     "actix", "axum"):
        return "backend"
    for entry in manifests:
        if entry.get("has_bin"):
            return "cli"
        if entry.get("csproj_desktop"):
            return "desktop"
        if entry.get("has_lib"):
            return "library"
    if os.path.isfile(os.path.join(part_dir, "go.mod")):
        return "backend"
    if os.path.isfile(os.path.join(part_dir, "pom.xml")):
        return "backend"
    return "unknown"


# ---- 部件探测（多部件 / 单仓 / 单块） ----

PART_DIR_HINTS = ("client", "server", "api", "web", "app", "apps", "frontend", "backend",
                  "mobile", "desktop", "packages", "libs", "services", "cmd", "internal",
                  "src", "ui", "gateway", "worker", "workers")
MONOREPO_MARKERS = ("pnpm-workspace.yaml", "lerna.json", "nx.json", "turbo.json",
                    "rush.json", "workspace.json", "go.work")
WORKSPACE_DIRS = ("packages", "apps", "libs", "services", "modules")


def has_manifest(part_dir):
    if any(os.path.isfile(os.path.join(part_dir, name)) for name, _ in MANIFEST_KINDS):
        return True
    import glob as _glob
    return bool(_glob.glob(os.path.join(part_dir, "*.csproj")))


def list_dirs(root, excludes=EXCLUDE_DIRS, cap=TREE_MAX_ENTRIES):
    try:
        names = sorted(os.listdir(root))
    except OSError:
        return []
    out = []
    for name in names:
        path = os.path.join(root, name)
        if os.path.isdir(path) and name not in excludes and not name.startswith("."):
            out.append((name, path))
        if len(out) >= cap:
            break
    return out


def detect_parts(root, excludes=EXCLUDE_DIRS):
    """部件探测：返回 (parts, repository_type, warnings)。parts 恒 ≥1（退化=根为单部件）。"""
    warnings = []
    monorepo = any(os.path.isfile(os.path.join(root, marker)) for marker in MONOREPO_MARKERS)
    candidates = []
    for name, path in list_dirs(root, excludes):
        if has_manifest(path):
            candidates.append((name, path))
        elif name in WORKSPACE_DIRS or monorepo:
            # 单仓/工作区：再下探一层（packages/* 等各自带清单才算部件）
            for sub, subpath in list_dirs(path, excludes):
                if has_manifest(subpath):
                    candidates.append((sub, subpath))
    repository_type = "monorepo" if monorepo and len(candidates) > 1 else (
        "multi-part" if len(candidates) > 1 else "monolith")
    if not candidates:
        candidates = [(os.path.basename(os.path.abspath(root)) or "project", root)]
        if not has_manifest(root):
            warnings.append(v("MANIFEST_UNPARSED", ".",
                              "未探测到任何清单：语言与类型待人工确认（不猜测）"))
    return candidates, repository_type, warnings


# ---- 源码树 / 文档发现 / 统计 ----

def render_tree(base, excludes=EXCLUDE_DIRS):
    """源码树文本：深度与条目上限为内置常量；超限以「… (截断)」标记（禁静默截断）。"""
    lines = [os.path.basename(os.path.abspath(base)) + "/"]
    state = {"count": 0, "truncated": False}

    def walk(current, prefix, depth):
        if depth > TREE_MAX_DEPTH or state["truncated"]:
            return
        dirs = list_dirs(current, excludes)
        files = []
        try:
            files = sorted(name for name in os.listdir(current)
                           if os.path.isfile(os.path.join(current, name)))
        except OSError:
            files = []
        entries = [(name, path, True) for name, path in dirs] + \
                  [(name, os.path.join(current, name), False) for name in files]
        for index, (name, path, is_dir) in enumerate(entries):
            if state["count"] >= TREE_MAX_ENTRIES:
                state["truncated"] = True
                return
            state["count"] += 1
            last = index == len(entries) - 1
            lines.append("%s%s %s" % (prefix, "└──" if last else "├──", name + ("/" if is_dir else "")))
            if is_dir:
                walk(path, prefix + ("    " if last else "│   "), depth + 1)

    walk(base, "", 1)
    if state["truncated"]:
        lines.append("… (节点超上限 %d，已截断；用于扫描请传 --part 缩小范围)" % TREE_MAX_ENTRIES)
    return "\n".join(lines)


def doc_kind(rel_path):
    name = os.path.basename(rel_path).lower()
    for kind, names in DOC_NAME_RULES:
        if name in names:
            return kind
    lowered = rel_path.lower()
    for kind, prefixes in DOC_DIR_RULES:
        if any(prefix in lowered for prefix in prefixes):
            return kind
    if any(lowered.startswith(d + "/") or ("/" + d + "/") in lowered for d in DOC_DIRS):
        return "docs"
    return None


def find_docs(root, project_root, parts, excludes=EXCLUDE_DIRS):
    """既有文档发现（源 full-scan step-2 模式）：返回 [{part, path, kind}]，上限内置。"""
    found = []
    parts_by_path = {}
    for part in parts:
        abspath = os.path.abspath(os.path.join(project_root, part["path"]))
        parts_by_path[abspath] = part["name"]
    for current, dirnames, filenames in os.walk(root):
        rel_dir = os.path.relpath(current, root)
        depth = 0 if rel_dir == "." else rel_dir.count(os.sep) + 1
        dirnames[:] = [d for d in sorted(dirnames)
                       if d not in excludes
                       and depth < DOCS_MAX_DEPTH + 1
                       and (not d.startswith(".") or d == ".github")]
        for name in sorted(filenames):
            path = os.path.join(current, name)
            rel = display_path(path, project_root) if current != root else slash(name)
            kind = doc_kind(rel)
            if kind is None:
                continue
            owner = ""
            for abspath, part_name in parts_by_path.items():
                if os.path.abspath(path).startswith(abspath + os.sep):
                    owner = part_name
                    break
            found.append({"part": owner, "path": rel, "kind": kind})
            if len(found) >= DOCS_MAX_ENTRIES:
                return found
    return found


def source_stats(part_dir, level, excludes=EXCLUDE_DIRS):
    """deep/exhaustive 的文件计数与（exhaustive 的）LOC；受深度/文件数/字节上限约束。"""
    files = 0
    loc = 0
    read_files = 0
    for current, dirnames, filenames in os.walk(part_dir):
        rel_dir = os.path.relpath(current, part_dir)
        depth = 0 if rel_dir == "." else rel_dir.count(os.sep) + 1
        dirnames[:] = [d for d in dirnames if d not in excludes]
        if depth > SOURCE_MAX_DEPTH:
            dirnames[:] = []
            continue
        for name in filenames:
            if not name.lower().endswith(SOURCE_EXTS):
                continue
            files += 1
            if level != "exhaustive" or read_files >= LOC_MAX_FILES:
                continue
            path = os.path.join(current, name)
            try:
                if os.path.getsize(path) > LOC_MAX_BYTES:
                    continue
                with io.open(path, "r", encoding="utf-8", errors="replace") as f:
                    loc += sum(1 for _ in f)
                read_files += 1
            except OSError:
                continue
    return {"files": files, "loc": loc}


# ---- scan ----

def build_part(project_root, name, path, level, excludes=EXCLUDE_DIRS):
    """单个部件的探测单元：parts / stack / stats 三条载荷一次算出。"""
    manifests, warnings = probe_manifests(path, project_root)
    ptype = classify_part(path, manifests)
    language = ""
    framework = ""
    version = ""
    notes = []
    for entry in manifests:
        if entry.get("unparsed"):
            if not language:
                language = entry.get("language") or ""
            notes.append(entry.get("notes") or "")
            continue
        if not framework and entry.get("framework"):
            framework = entry["framework"]
        if not version and entry.get("version"):
            version = entry["version"]
        if not language:
            language = entry.get("language") or ""
        if entry.get("notes"):
            notes.append(entry["notes"])
        package_name = entry.get("package_name")
        if package_name and not any(package_name in note for note in notes):
            notes.append(package_name)
    if not framework:
        _, framework = first_hit(
            {d for entry in manifests for d in (entry.get("deps") or ())}, FRAMEWORK_HINTS)
    rel_path = display_path(path, project_root)
    part = {"name": name, "type": ptype, "path": rel_path,
            "manifests": part_manifest_files(path, project_root)}
    stack = {"part": name, "language": language, "framework": framework, "version": version,
             "notes": "；".join(n for n in notes if n)}
    stats = source_stats(path, level, excludes) if level in ("deep", "exhaustive") else {}
    return part, stack, stats, warnings


def cmd_scan(args):
    root = os.path.abspath(args.project_root)
    out = args.output_dir
    violations = []
    warnings = []
    if not os.path.isdir(root):
        violations.append(v("MISSING_FILE", display_path(root, os.path.dirname(root) or root),
                            "项目根不存在：%s（扫描拒绝，零产出）" % slash(root)))
        return emit_scan(args, None, [], [], [], "", violations, warnings, "")

    # 产物目录属扫描对象之外（扫描的是代码库，不是 diy 自身产物）：按名排除
    excludes = frozenset(EXCLUDE_DIRS | {os.path.basename(os.path.abspath(out))})
    candidates, repository_type, part_warnings = detect_parts(root, excludes)
    warnings += part_warnings
    if args.part:
        wanted = [c for c in candidates if c[0] == args.part]
        if not wanted:
            violations.append(v("UNKNOWN_ID", "parts",
                                "部件 %s 不存在（候选：%s）"
                                % (args.part, ", ".join(c[0] for c in candidates))))
            return emit_scan(args, repository_type, [], [], [], "", violations, warnings,
                             args.part)
        candidates = wanted

    parts = []
    stack = []
    stats = {}
    for name, path in candidates:
        part, entry, part_stats, part_warn = build_part(root, name, path, args.level, excludes)
        parts.append(part)
        stack.append(entry)
        warnings += part_warn
        if part_stats:
            stats[name] = part_stats

    docs = find_docs(root, root, parts, excludes)
    if args.part:
        docs = [d for d in docs if d["part"] in ("", args.part)]
    tree = render_tree(candidates[0][1] if args.part else root, excludes)

    ctx_path = os.path.join(out, CTX_FILE)
    existing = {}
    data, err = load_yaml_safe(ctx_path)
    if isinstance(data, dict) and isinstance(data.get("scan"), dict):
        scan = data["scan"]
        existing = {"mode": scan.get("mode"), "level": scan.get("level"),
                    "date": scan.get("date")}
    elif err is not None:
        warnings.append(v("UNPARSABLE_YAML", display_path(ctx_path, root),
                          "既有 %s 不可解析，模式判定以用户确认为准：%s" % (CTX_FILE, err)))

    counts = {
        "parts": len(parts),
        "stack": len(stack),
        "docs_found": len(docs),
        "tree_lines": len(tree.splitlines()),
    }
    for name, entry in stats.items():
        counts.setdefault("files_by_part", {})[name] = entry["files"]
        counts.setdefault("loc_by_part", {})[name] = entry["loc"]
    counts["files"] = sum(e["files"] for e in stats.values())
    counts["loc"] = sum(e["loc"] for e in stats.values())
    return emit_scan(args, repository_type, parts, stack, docs, tree, violations, warnings,
                     args.part, existing, counts, stats)


def emit_scan(args, repository_type, parts, stack, docs, tree, violations, warnings,
              part=None, existing=None, counts=None, stats=None):
    ok = not violations
    payload = {
        "ok": ok,
        "command": "scan",
        "project_root": args.project_root,
        "output_dir": os.path.normpath(args.output_dir).replace("\\", "/"),
        "level": args.level,
        "levels": list(SCAN_LEVELS),
        "part": part,
        "repository_type": repository_type,
        "parts": parts,
        "stack": stack,
        "docs_found": docs,
        "tree": tree,
        "stats": stats or {},
        "existing_context": bool(existing),
        "existing_scan": existing or {},
        "violations": violations,
        "warnings": warnings,
        "counts": counts or {"parts": 0, "stack": 0, "docs_found": 0, "tree_lines": 0},
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False))
    elif ok:
        print("PASS：扫描完成（repository_type=%s, parts=%d, docs=%d, level=%s）"
              % (repository_type, len(parts), len(docs), args.level))
        for part_entry in parts:
            print("- %s [%s] %s" % (part_entry["name"], part_entry["type"], part_entry["path"]))
        for doc in docs:
            print("- 文档 %s (%s)" % (doc["path"], doc["kind"]))
        for item in warnings:
            print("- WARN %s %s: %s" % (item["code"], item["where"], item["msg"]))
    else:
        print("拒绝：")
        for item in violations:
            print("- %s %s: %s" % (item["code"], item["where"], item["msg"]))
    return 0 if ok else 1


# ---- check ----

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


def check_scan(scan, where, violations):
    if not isinstance(scan, dict):
        violations.append(v("EMPTY_FIELD", where, "scan 缺失或不是映射"))
        return
    mode = scan.get("mode")
    if not nonempty(mode):
        violations.append(v("EMPTY_FIELD", where + ".mode", "mode 缺失"))
    elif str(mode) not in SCAN_MODES:
        violations.append(v("ENUM_INVALID", where + ".mode",
                            "mode 越界：%s（合法集 %s）" % (mode, "|".join(SCAN_MODES))))
    level = scan.get("level")
    if not nonempty(level):
        violations.append(v("EMPTY_FIELD", where + ".level", "level 缺失"))
    elif str(level) not in SCAN_LEVELS:
        violations.append(v("ENUM_INVALID", where + ".level",
                            "level 越界：%s（合法集 %s）" % (level, "|".join(SCAN_LEVELS))))
    date = scan.get("date")
    if not nonempty(date):
        violations.append(v("EMPTY_FIELD", where + ".date", "date 缺失"))
    elif not DATE_RE.fullmatch(str(date)):
        violations.append(v("ENUM_INVALID", where + ".date", "date 须为 YYYY-MM-DD，实为 %s" % date))
    parts = scan.get("parts")
    if not isinstance(parts, list):
        violations.append(v("EMPTY_FIELD", where + ".parts", "parts 缺失或不是列表"))
        return
    if not parts:
        violations.append(v("EMPTY_FIELD", where + ".parts", "parts 不得为空（扫描是产物的前置证据）"))
    for i, part in enumerate(parts):
        pw = "%s.parts[%d]" % (where, i)
        if not isinstance(part, dict):
            violations.append(v("EMPTY_FIELD", pw, "part 不是映射"))
            continue
        for key in ("name", "type", "path"):
            if not nonempty(part.get(key)):
                violations.append(v("EMPTY_FIELD", pw + "." + key, "%s 缺失" % key))
        ptype = part.get("type")
        if nonempty(ptype) and str(ptype) not in PART_TYPES:
            violations.append(v("ENUM_INVALID", pw + ".type",
                                "type 越界：%s（合法集 %s）" % (ptype, "|".join(PART_TYPES))))


def check_stack(stack, where, violations):
    if stack is None:
        violations.append(v("EMPTY_FIELD", where, "stack 缺失（无内容写空列表）"))
        return
    if not isinstance(stack, list):
        violations.append(v("EMPTY_FIELD", where, "stack 不是列表"))
        return
    for i, entry in enumerate(stack):
        sw = "%s[%d]" % (where, i)
        if not isinstance(entry, dict):
            violations.append(v("EMPTY_FIELD", sw, "stack 条目不是映射"))
            continue
        if not nonempty(entry.get("part")):
            violations.append(v("EMPTY_FIELD", sw + ".part", "part 缺失（stack 须归属部件）"))
        for key in ("language", "framework", "version", "notes"):
            if key in entry and entry.get(key) is not None and not isinstance(entry.get(key), str):
                violations.append(v("ENUM_INVALID", sw + "." + key,
                                    "%s 若给出须为字符串（未知写空串）" % key))


def check_structure(structure, where, violations):
    if structure is None:
        violations.append(v("EMPTY_FIELD", where, "structure 缺失"))
        return
    if not isinstance(structure, dict):
        violations.append(v("EMPTY_FIELD", where, "structure 不是映射"))
        return
    tree = structure.get("tree")
    if tree is not None and not isinstance(tree, str):
        violations.append(v("ENUM_INVALID", where + ".tree", "tree 若给出须为字符串"))
    key_dirs = structure.get("key_dirs")
    if key_dirs is None:
        return
    if not isinstance(key_dirs, list):
        violations.append(v("EMPTY_FIELD", where + ".key_dirs", "key_dirs 不是列表"))
        return
    for i, entry in enumerate(key_dirs):
        kw = "%s.key_dirs[%d]" % (where, i)
        if not isinstance(entry, dict):
            violations.append(v("EMPTY_FIELD", kw, "key_dirs 条目不是映射"))
            continue
        for key in ("path", "purpose"):
            if not nonempty(entry.get(key)):
                violations.append(v("EMPTY_FIELD", kw + "." + key, "%s 缺失" % key))


def check_records(items, where, required_keys, violations):
    """通用集合段：每条须为映射且 required_keys 非空（architecture / deep_dives 共用）。"""
    if items is None:
        violations.append(v("EMPTY_FIELD", where, "段落缺失（无内容写空列表）"))
        return
    if not isinstance(items, list):
        violations.append(v("EMPTY_FIELD", where, "不是列表"))
        return
    for i, entry in enumerate(items):
        iw = "%s[%d]" % (where, i)
        if not isinstance(entry, dict):
            violations.append(v("EMPTY_FIELD", iw, "条目不是映射"))
            continue
        for key in required_keys:
            if not nonempty(entry.get(key)):
                violations.append(v("EMPTY_FIELD", iw + "." + key, "%s 缺失" % key))


def check_integration(integration, where, violations):
    if integration is None:
        return  # 多部件才填（源 step-8 条件步）：单部件项目缺席合法
    if not isinstance(integration, list):
        violations.append(v("EMPTY_FIELD", where, "integration 不是列表"))
        return
    for i, entry in enumerate(integration):
        iw = "%s[%d]" % (where, i)
        if not isinstance(entry, dict):
            violations.append(v("EMPTY_FIELD", iw, "条目不是映射"))
            continue
        between = entry.get("between")
        if not isinstance(between, list) or len(between) != 2 or \
                not all(nonempty(x) for x in between):
            violations.append(v("EMPTY_FIELD", iw + ".between",
                                "between 须为两个部件名的列表（如 [client, server]）"))
        for key in ("contract", "notes"):
            if key in entry and entry.get(key) is not None and not isinstance(entry.get(key), str):
                violations.append(v("ENUM_INVALID", iw + "." + key, "%s 若给出须为字符串" % key))


def check_rules(rules, where, final, violations):
    if rules is None:
        violations.append(v("EMPTY_FIELD", where, "rules 缺失（LLM 规则集合）"))
        return
    if not isinstance(rules, list):
        violations.append(v("EMPTY_FIELD", where, "rules 不是列表"))
        return
    seen = set()
    for i, rule in enumerate(rules):
        rw = "%s[%d]" % (where, i)
        if not isinstance(rule, dict):
            violations.append(v("EMPTY_FIELD", rw, "rule 不是映射"))
            continue
        rid = rule.get("id")
        if not nonempty(rid):
            violations.append(v("EMPTY_FIELD", rw + ".id", "id 缺失"))
        elif not PC_RE.fullmatch(str(rid)):
            violations.append(v("ENUM_INVALID", rw + ".id",
                                "id 须为 PC-0nn（三位零填充），实为 %s" % rid))
        else:
            if str(rid) in seen:
                violations.append(v("DUPLICATE_ID", rw + ".id",
                                    "规则 ID %s 重复（PC ID 稳定不重用）" % rid))
            seen.add(str(rid))
        category = rule.get("category")
        if not nonempty(category):
            violations.append(v("EMPTY_FIELD", rw + ".category", "category 缺失"))
        elif str(category) not in RULE_CATEGORIES:
            violations.append(v("ENUM_INVALID", rw + ".category",
                                "category 越界：%s（合法集 %s）"
                                % (category, "|".join(RULE_CATEGORIES))))
        if not nonempty(rule.get("rule")):
            violations.append(v("EMPTY_FIELD", rw + ".rule", "rule 缺失（规则正文）"))
        if final:
            for key in ("why", "where"):
                if not nonempty(rule.get(key)):
                    violations.append(v("EMPTY_FIELD", rw + "." + key,
                                        "--final 要求每条规则 %s 非空" % key))
    if final and not rules:
        violations.append(v("EMPTY_FIELD", where, "--final 要求至少 1 条规则"))


def previous_rules(path, project_root, warnings):
    """--previous：读旧稿 PC-### 集合；不可读 → 结构化 warning（比对无法进行，不静默）。"""
    data, err = load_yaml_safe(path)
    if data is None and err is None:
        warnings.append(v("MISSING_FILE", display_path(path, project_root),
                          "旧稿不存在，--previous 比对跳过"))
        return None
    if err is not None:
        warnings.append(v("UNPARSABLE_YAML", display_path(path, project_root),
                          "旧稿不可解析，--previous 比对跳过：%s" % err))
        return None
    rules = data.get("rules") if isinstance(data, dict) else None
    if not isinstance(rules, list):
        return set()
    return {str(r.get("id")) for r in rules
            if isinstance(r, dict) and PC_RE.fullmatch(str(r.get("id") or ""))}


def cmd_check(args):
    root = os.path.abspath(args.project_root)
    out = args.output_dir
    path = os.path.join(out, CTX_FILE)
    show = display_path(path, root)
    violations = []
    warnings = []
    rules = []

    data, err = load_yaml_safe(path)
    if data is None and err is None:
        violations.append(v("MISSING_FILE", show,
                            "%s 不存在（先跑一次 scan 与起草）" % CTX_FILE))
    elif err is not None:
        violations.append(v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err))
    elif not isinstance(data, dict):
        violations.append(v("EMPTY_FIELD", show, "顶层不是映射（须为 project + scan + …）"))
    else:
        project = data.get("project")
        if project is not None and not isinstance(project, dict):
            violations.append(v("EMPTY_FIELD", show + " project", "project 不是映射"))
        check_scan(data.get("scan"), show + " scan", violations)
        check_stack(data.get("stack"), show + " stack", violations)
        check_structure(data.get("structure"), show + " structure", violations)
        check_records(data.get("architecture"), show + " architecture",
                      ("part", "summary"), violations)
        check_integration(data.get("integration"), show + " integration", violations)
        rules = data.get("rules") if isinstance(data.get("rules"), list) else []
        check_rules(data.get("rules"), show + " rules", args.final, violations)
        if data.get("deep_dives") is not None:  # 事件驱动段：未跑过深挖时缺席合法
            check_records(data.get("deep_dives"), show + " deep_dives",
                          ("area", "date", "files_scanned"), violations)
        revisions = data.get("revisions")
        if revisions is not None and not isinstance(revisions, list):
            violations.append(v("EMPTY_FIELD", show + " revisions", "revisions 不是列表"))
        if args.final:
            if any("[ASSUMPTION]" in s for s in collect_strings(data)):
                violations.append(v("ASSUMPTION_PRESENT", show,
                                    "--final 要求零 [ASSUMPTION]；未决假设须先落定"))
            if isinstance(data.get("stack"), list) and not data["stack"]:
                violations.append(v("EMPTY_FIELD", show + " stack", "--final 要求 stack 非空"))

    if args.previous:
        old_ids = previous_rules(args.previous, root, warnings)
        if old_ids is not None:
            new_ids = {str(r.get("id")) for r in rules
                       if isinstance(r, dict) and PC_RE.fullmatch(str(r.get("id") or ""))}
            for rid in sorted(old_ids - new_ids):
                violations.append(v("ID_UNSTABLE", show + " rules",
                                    "旧稿规则 %s 在新稿中丢失（PC ID 稳定不重用；"
                                    "确删请追加 revisions 留痕）" % rid))

    counts = {
        "parts": safe_len(data, "scan", "parts"),
        "stack": safe_len(data, "stack"),
        "rules": len(rules),
        "rules_by_category": count_by_attr(rules, "category"),
        "architecture": safe_len(data, "architecture"),
        "integration": safe_len(data, "integration"),
        "deep_dives": safe_len(data, "deep_dives"),
    }
    ok = not violations
    payload = {
        "ok": ok,
        "command": "check",
        "project_root": args.project_root,
        "output_dir": os.path.normpath(out).replace("\\", "/"),
        "final": args.final,
        "previous": slash(args.previous) if args.previous else None,
        "violations": violations,
        "warnings": warnings,
        "counts": counts,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False))
    elif ok:
        print("PASS：%s 校验通过（rules=%d, parts=%d）" % (show, len(rules), counts["parts"]))
        for item in warnings:
            print("- WARN %s %s: %s" % (item["code"], item["where"], item["msg"]))
    else:
        print("FAIL：")
        for item in violations:
            print("- %s %s: %s" % (item["code"], item["where"], item["msg"]))
        print("共 %d 条违规；exit 0 是唯一放行" % len(violations))
    return 0 if ok else 1


def count_by_attr(records, key):
    counts = {}
    for record in records:
        if isinstance(record, dict) and nonempty(record.get(key)):
            value = str(record[key])
            counts[value] = counts.get(value, 0) + 1
    return counts


def safe_len(data, key, sub=None):
    """集合段长度（形状不合法记 0——具体违规由对应 check_* 报出，不在此重复）。"""
    node = data.get(key) if isinstance(data, dict) else None
    if sub is not None:
        node = node.get(sub) if isinstance(node, dict) else None
    return len(node) if isinstance(node, list) else 0


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(
        description="diy-project-context 确定性引擎：棕地扫描（scan，只读）+ project-context.yaml 校验（check）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("scan", help="扫描棕地项目：部件/类型/清单/既有文档/源码树（只读，不写产物）")
    s.add_argument("--project-root", default=".", help="项目根（默认 .）")
    s.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    s.add_argument("--level", default="quick", choices=list(SCAN_LEVELS),
                   help="扫描档位：quick=模式分析（默认）/ deep=加文件计数 / exhaustive=加 LOC")
    s.add_argument("--part", default=None, help="只扫指定部件（部件名以扫描回执为准）")
    s.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    s.set_defaults(func=cmd_scan)

    c = sub.add_parser("check", help="校验 project-context.yaml（schema/枚举/ID；--final 附加定稿义务）")
    c.add_argument("--project-root", default=".", help="项目根（默认 .）")
    c.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    c.add_argument("--final", action="store_true",
                   help="定稿校验：rules 非空且 rule/why/where 非空 + stack 非空 + 零假设")
    c.add_argument("--previous", default=None,
                   help="旧稿路径（rescan 防丢规则：比对 PC-### 集合，旧有新无 → ID_UNSTABLE）")
    c.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    c.set_defaults(func=cmd_check)

    args = ap.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
