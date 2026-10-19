# -*- coding: utf-8 -*-
"""diy-project-context 探测件：部件分类/目录树/文档发现/源码统计与 build_part 装配。."""

import io
import os

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import display_path, v  # noqa: E402

from context_lib import DOCS_MAX_DEPTH, DOCS_MAX_ENTRIES, DOC_DIRS, DOC_DIR_RULES, DOC_NAME_RULES, EXCLUDE_DIRS, FRAMEWORK_HINTS, LOC_MAX_BYTES, LOC_MAX_FILES, MANIFEST_KINDS, SOURCE_EXTS, SOURCE_MAX_DEPTH, TREE_MAX_DEPTH, TREE_MAX_ENTRIES, first_hit, slash  # noqa: E402

from context_parsers import part_manifest_files, probe_manifests  # noqa: E402
# 部件类型 → 该类型的关键目录（documentation-requirements.csv 的 critical_directories 列，逐项照录）：
# 深入档的阅读面；回执只报部件里**实际存在**的那些（大小写不敏感匹配，见 critical_dirs）。
CRITICAL_DIRS = {
    "网页": ("src", "app", "pages", "components", "api", "lib", "styles", "public", "static"),
    "移动端": ("src", "app", "screens", "components", "services", "models", "assets", "ios", "android"),
    "后端": ("src", "api", "services", "models", "routes", "controllers", "middleware",
             "handlers", "repositories", "domain"),
    "命令行": ("src", "cmd", "cli", "bin", "lib", "commands"),
    "库": ("src", "lib", "dist", "pkg", "build", "target"),
    "桌面端": ("src", "app", "components", "main", "renderer", "resources", "assets", "build"),
    "游戏": ("Assets", "Scenes", "Scripts", "Prefabs", "Resources", "Content", "Source",
             "src", "scenes", "scripts"),
    "数据": ("dags", "pipelines", "models", "transformations", "notebooks", "sql", "etl", "jobs"),
    "扩展": ("src", "popup", "content", "background", "assets", "components"),
    "基础设施": ("terraform", "modules", "k8s", "charts", "playbooks", "roles", "policies", "stacks"),
    "嵌入式": ("src", "lib", "include", "firmware", "drivers", "hal", "bsp", "components"),
    # 「未知」不设表：类型未定 → 无从取关键目录
}
# 非清单但决定项目类型的强标记：glob → 类型（CSV key_file_patterns 的高置信子集）
MARKER_TYPE_GLOBS = (
    ("*.tf", "基础设施"), ("*.tfvars", "基础设施"), ("pulumi.yaml", "基础设施"), ("cdk.json", "基础设施"),
    ("*.ino", "嵌入式"), ("project.godot", "游戏"), ("*.unity", "游戏"), ("*.uproject", "游戏"),
)

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
    deps = set()
    for entry in manifests:
        deps.update(entry.get("deps") or ())
    _, framework = first_hit(deps, FRAMEWORK_HINTS)
    if framework in ("react-native", "expo", "flutter"):
        return "移动端"
    if framework in ("electron", "tauri"):
        return "桌面端"
    if framework in ("next", "nuxt", "react", "vue", "svelte", "angular"):
        return "扩展" if os.path.isfile(os.path.join(part_dir, "manifest.json")) else "网页"
    if framework in ("airflow", "dbt"):
        return "数据"
    if framework in ("fastapi", "django", "flask", "nestjs", "express", "fastify",
                     "spring-boot", "laravel", "symfony", "gin", "echo", "fiber", "grpc",
                     "actix", "axum"):
        return "后端"
    for entry in manifests:
        if entry.get("has_bin"):
            return "命令行"
        if entry.get("csproj_desktop"):
            return "桌面端"
        if entry.get("has_lib"):
            return "库"
    if os.path.isfile(os.path.join(part_dir, "go.mod")):
        return "后端"
    if os.path.isfile(os.path.join(part_dir, "pom.xml")):
        return "后端"
    return "未知"

def critical_dirs(part_dir, ptype, project_root):
    """该类型的关键目录里**实际存在**的那些（CSV critical_directories 列；深入档的阅读面）。

    兼容大小写差异（CSV 的 `Assets/` 对上 `assets/`）；声明序即返回序，去重；
    类型无表（`未知`）或目录不可读 → 空列表（不猜、不崩）。
    """
    declared = CRITICAL_DIRS.get(ptype)
    if not declared:
        return []
    try:
        actual = {}
        for name in os.listdir(part_dir):
            if os.path.isdir(os.path.join(part_dir, name)):
                actual.setdefault(name.casefold(), name)
    except OSError:
        return []
    found = []
    seen = set()
    for name in declared:
        real = actual.get(name.casefold())
        if not real or real in seen:
            continue
        seen.add(real)
        found.append(display_path(os.path.join(part_dir, real), project_root))
    return found

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
    """深入/穷尽的文件计数与（穷尽的）LOC；受深度/文件数/字节上限约束。"""
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
            if level != "穷尽" or read_files >= LOC_MAX_FILES:
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
    stats = source_stats(path, level, excludes) if level in ("深入", "穷尽") else {}
    return part, stack, stats, warnings
