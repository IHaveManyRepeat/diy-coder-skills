# -*- coding: utf-8 -*-
"""diy-project-context 常量表与通用工具（路径/版本/取词/降级/安全长度）。."""

import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import display_path, v  # noqa: E402

CTX_FILE = "project-context.yaml"

SCAN_MODES = ("全量", "重扫", "深挖")
SCAN_LEVELS = ("快速", "深入", "穷尽")
# 规则类别 = 七个规则域（Technology Stack &
# Versions / Language / Framework / Testing / Quality & Style / Workflow / Critical Don't-Miss）
RULE_CATEGORIES = ("技术栈", "语言", "框架", "测试", "质量", "工作流",
                   "反模式")
# 部件类型 = documentation-requirements.csv 的项目类型列（11 行）
# + 未知（畸形/未解析清单的降级值，与 scan 回执自洽）
PART_TYPES = ("网页", "移动端", "后端", "命令行", "库", "桌面端", "游戏", "数据",
              "扩展", "基础设施", "嵌入式", "未知")

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
# 既有文档发现规则：文件名 → 类别；再按目录语义兜底
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

def slash(path):
    return str(path).replace("\\", "/")

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

def safe_len(data, key, sub=None):
    """集合段长度（形状不合法记 0——具体违规由对应 check_* 报出，不在此重复）。"""
    node = data.get(key) if isinstance(data, dict) else None
    if sub is not None:
        node = node.get(sub) if isinstance(node, dict) else None
    return len(node) if isinstance(node, list) else 0
