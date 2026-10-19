# -*- coding: utf-8 -*-
"""diy-project-context 清单解析器族：package.json/toml/go.mod/xml/requirements/pubspec 与 PARSERS 注册。."""

import io
import json
import os
import re
import xml.etree.ElementTree as ET

try:  # Python 3.11+ 标准库；3.10 环境降级为「存在但未解析」warning（语言无关承诺）
    import tomllib as _toml
except ImportError:  # pragma: no cover - 取决于运行时版本
    _toml = None

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import display_path, load_yaml_safe  # noqa: E402

from context_lib import FRAMEWORK_HINTS, MANIFEST_KINDS, MARKER_LANGUAGE, SIGNAL_MARKERS, clean_version, degraded, first_hit  # noqa: E402

try:  # Python 3.11+ 标准库；3.10 环境降级为「存在但未解析」warning（语言无关承诺）
    import tomllib as _toml
except ImportError:  # pragma: no cover - 取决于运行时版本
    _toml = None

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
