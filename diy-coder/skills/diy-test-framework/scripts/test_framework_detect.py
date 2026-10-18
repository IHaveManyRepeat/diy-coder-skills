# -*- coding: utf-8 -*-
"""diy-test-framework detect 面：栈/语言/包管理器/既有框架/CI 平台探测。"""
import fnmatch
import io
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import display_path, v  # noqa: E402

from test_framework_lib import (  # noqa: E402
    AUTH_HINTS, BACKEND_FRAMEWORKS, BACKEND_PACKAGES, BACKEND_PROFILES, BROWSER_PROFILES,
    CI_CONFIGS, CI_PLATFORMS, CI_TEMPLATES, CONTEXT_DOC_DIRS, CONTEXT_DOC_GLOBS,
    FRAMEWORK_CONFIGS, FRONTEND_FILES, FRONTEND_PACKAGES, KNOWN_MANIFESTS, LANG_MANIFESTS,
    MOBILE_DIRS, MOBILE_FILES, MOBILE_PACKAGES, MOBILE_PATHS, PACKAGE_MANAGERS,
    TEMPLATES_DIR, emit, find_files, load_json_safe, out_dir, template_abs,
)

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
