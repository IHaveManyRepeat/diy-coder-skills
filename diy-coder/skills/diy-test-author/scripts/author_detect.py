# -*- coding: utf-8 -*-
"""diy-test-author 探测面：清单/框架/扫描常量 + detect 子命令（只读探测）。"""
import io
import json
import os
import sys


sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import (JAVA_MANIFESTS, NODE_MANIFESTS, PY_MANIFESTS,  # noqa: E402
                      builtin_framework, detect_project_type, display_path,
                      is_test_file, v)

# ---------------------------------------------------------------- 探测面
# NODE/PY/JAVA 三清单与 e2e 同源（diyc_lib 单源：detect_project_type 同库）；OTHER 留本地
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
