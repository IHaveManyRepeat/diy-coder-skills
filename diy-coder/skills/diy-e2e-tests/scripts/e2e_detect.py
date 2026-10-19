# -*- coding: utf-8 -*-
"""diy-e2e-tests detect 域：清单/框架常量表与只读探测（read_manifest/node_framework/text_framework/scan_tests/cmd_detect）。."""

import io
import json
import os

import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import JAVA_MANIFESTS, NODE_MANIFESTS, PY_MANIFESTS, builtin_framework, detect_project_type, display_path, is_test_file, v  # noqa: E402

# 探测面（语言无关：清单存在即读；顺序即 project_type 判定优先级）
# NODE/PY/JAVA 三清单在 diyc_lib（detect_project_type 同源同值）；OTHER 留本地
OTHER_MANIFESTS = ("Cargo.toml", "go.mod", "Gemfile", "composer.json")
ALL_MANIFESTS = NODE_MANIFESTS + PY_MANIFESTS + JAVA_MANIFESTS + OTHER_MANIFESTS

# 框架优先级：e2e 能力强者在前（多命中也报最能承接 e2e 的那个）
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
MAX_PATTERNS = 20
SCAN_DEPTH = 3

SUGGESTS = {
    "node": "Playwright (@playwright/test) — 浏览器端到端；API 层可用既有 runner。"
            "装包由用户确认后执行，本技能不自动安装。",
    "python": "pytest（+ pytest-playwright 承接浏览器端到端）— 由用户确认后安装，"
              "本技能不自动安装。",
    "rust": "cargo test（内建；集成测试落 tests/ 目录）。无需装包。",
    "go": "go test（内建；*_test.go 同包或 _test 包）。无需装包。",
    "java": "JUnit 5 + Surefire/Gradle test（项目既有构建链）。由用户确认后配置。",
    "ruby": "RSpec（spec/ 目录）。由用户确认后加入 Gemfile。",
    "php": "PHPUnit（tests/ 目录）。由用户确认后安装。",
    "unknown": "未探测到项目清单——请显式指定被测特性的框架（本技能不自动安装）。",
}

# ---------------------------------------------------------------- detect

def read_manifest(path):
    """读清单文本：(text | None, warning | None)。损坏/不可读 → MANIFEST_UNPARSABLE。"""
    try:
        with io.open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read(), None
    except OSError as e:
        return None, v("MANIFEST_UNPARSABLE", path.replace("\\", "/"),
                       "清单不可读，探测降级：%s" % e)

def node_framework(root, warnings, project_root):
    """package.json：解析 JSON 后按优先级匹配 dependencies / devDependencies。"""
    path = os.path.join(root, "package.json")
    text, warning = read_manifest(path)
    if warning is not None:
        warnings.append(dict(warning, where=display_path(path, project_root)))
        return None
    try:
        data = json.loads(text)
    except ValueError as e:
        warnings.append(v("MANIFEST_UNPARSABLE", display_path(path, project_root),
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

def text_framework(root, manifests, frameworks, warnings, project_root):
    """文本清单（pyproject/requirements/Cargo/go.mod/...）：子串匹配框架标记。"""
    for rel in manifests:
        path = os.path.join(root, rel)
        if not os.path.isfile(path):
            continue
        text, warning = read_manifest(path)
        if warning is not None:
            warnings.append(dict(warning, where=display_path(path, project_root)))
            continue
        for name, markers in frameworks:
            if any(m in text for m in markers):
                return {"name": name, "detected_from": rel}
    return None

def scan_tests(root):
    """既有测试面：存在的测试目录 + 测试文件相对路径（深度受限，上限 MAX_PATTERNS）。"""
    dirs = [d for d in TEST_DIR_CANDIDATES if os.path.isdir(os.path.join(root, d))]
    patterns = []
    for test_dir in dirs:
        base = os.path.join(root, test_dir)
        for dirpath, dirnames, filenames in os.walk(base):
            rel_dir = os.path.relpath(dirpath, base)
            depth = 0 if rel_dir == "." else rel_dir.count(os.sep) + 1
            if depth >= SCAN_DEPTH:
                dirnames[:] = []
            for name in sorted(filenames):
                if is_test_file(name):
                    rel = os.path.relpath(os.path.join(dirpath, name), root)
                    patterns.append(rel.replace("\\", "/"))
                    if len(patterns) >= MAX_PATTERNS:
                        return dirs, patterns
    return dirs, patterns

def cmd_detect(args):
    root = os.path.abspath(args.project_root)
    warnings = []
    manifests = [rel for rel in ALL_MANIFESTS if os.path.isfile(os.path.join(root, rel))]
    project_type, from_manifest = detect_project_type(root)

    framework = None
    if any(os.path.isfile(os.path.join(root, m)) for m in NODE_MANIFESTS):
        framework = node_framework(root, warnings, root)
    if framework is None and any(os.path.isfile(os.path.join(root, m))
                                 for m in PY_MANIFESTS):
        framework = text_framework(root, PY_MANIFESTS, PY_FRAMEWORKS, warnings, root)
    if framework is None:
        built_in, built_type = builtin_framework(root)
        if built_in is not None:
            framework = built_in
            if project_type == "unknown":
                project_type = built_type

    test_dirs, existing_patterns = scan_tests(root)
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
        "suggested": suggested,
        "violations": [],
        "warnings": warnings,
        "counts": {"manifests": len(manifests), "test_dirs": len(test_dirs),
                   "existing_patterns": len(existing_patterns)},
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        if framework is None:
            print("未探测到既有测试框架（project_type=%s，清单：%s）"
                  % (project_type, ", ".join(manifests) or "无"))
            print("建议：%s" % suggested)
        else:
            print("框架 %s（来自 %s）｜project_type=%s｜测试目录 %s"
                  % (framework["name"], framework["detected_from"], project_type,
                     ", ".join(test_dirs) or "无"))
        for item in warnings:
            print("- %s %s: %s" % (item["code"], item["where"], item["msg"]))
    return 0
