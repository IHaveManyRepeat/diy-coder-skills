# -*- coding: utf-8 -*-
"""diy-e2e-tests 确定性引擎：测试框架探测（detect）+ e2e 用例追加写回（record）。

子命令：
  detect  语言无关的项目探测（只读）：依次读 package.json / pyproject.toml /
          requirements*.txt / Cargo.toml / go.mod / pom.xml / build.gradle* / Gemfile /
          composer.json 等清单判定 project_type 与既有测试框架；再识别测试目录与
          既有测试文件模式。无框架 → 回执给 suggested（建议框架，由用户确认），
          **绝不自动安装**。清单损坏/缺失降级为 warning，探测继续，不崩。
  record  把本次生成的 TC（JSON 文件，形态 [ {...} ] 或 {"test_cases": [...]}）
          追加进 {output_dir}/test-plan.yaml（diy-augment 窄写权先例：只追加，不改
          既有条目、不新增产物类型）。校验：id 规则 TC-{ac}.{seq} 且前缀与 ac 一致、
          续号不重号、ac 解析（stories.yaml）、type == 端到端、technique == 场景、
          kill_target/title/steps 非空、status ∈ {通过, 失败}、priority ∈ {P0,P1,P2}。
          全部通过才写（原子：同目录临时文件 + os.replace）。随后委派
          `diyc.py check --type test-plan --json` 交叉验证追加后的全链——其违规并入
          回执 `diyc` 键（warning 面），不阻塞本命令的写权结论。

分工裁定（任务书 §8）：e2e 生成不新增产物类型，写权三面 = ① test-plan.yaml 追加 TC
② 项目测试目录的测试代码 ③ 收尾会话摘要；不写 sprint.yaml / stories.yaml / 其他产物。
实例解析委托 SKILL.md 侧的 `diyc.py resolve`；本引擎不做 --instance / 白名单 / 目录推导，
--output-dir 必填。契约同构（batch3-contract §3）：exit 0 唯一放行 / 1 = 违规或被拒绝 /
2 = 用法错误；--json 单行回执（ensure_ascii=False）；violations[{code, where, msg}] + counts；
where 正斜杠、相对 project-root。

违规码：复用 batch3-contract §3 冻结集（MISSING_FILE UNPARSABLE_YAML DUPLICATE_ID
UNKNOWN_ID ENUM_INVALID EMPTY_FIELD ENTRY_INVALID TOOL_MISSING TOOL_ERROR SET_MISMATCH）；
新增 MANIFEST_UNPARSABLE（detect 专用：清单文件存在但不可解析，探测降级不崩，回报登记）。
"""
# trace: 迁移计划 §二 验收 #3 / #4 / #12（领域引擎接线 + 窄写权）
import argparse
import datetime
import io
import json
import os
import re
import subprocess
import sys

import yaml

PLAN_FILE = "test-plan.yaml"
STORIES_FILE = "stories.yaml"

E2E_TYPE = "端到端"
E2E_TECHNIQUE = "场景"              # diy-test-design Schema：九技法在册值，端到端用户旅程
RECORD_STATUSES = ("通过", "失败")  # 实测结果：本技能只记已跑过的用例
PRIORITIES = ("P0", "P1", "P2")
TC_RE = re.compile(r"TC-\d+(?:\.\d+)+")
AC_RE = re.compile(r"AC-\d+(?:\.\d+)+")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")

# 探测面（语言无关：清单存在即读；顺序即 project_type 判定优先级）
NODE_MANIFESTS = ("package.json",)
PY_MANIFESTS = ("pyproject.toml", "setup.py", "requirements.txt", "requirements-dev.txt",
                "requirements-test.txt", "Pipfile")
JAVA_MANIFESTS = ("pom.xml", "build.gradle", "build.gradle.kts")
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
TEST_FILE_SUFFIXES = (".spec.ts", ".spec.tsx", ".spec.js", ".spec.jsx", ".spec.py",
                      ".test.ts", ".test.tsx", ".test.js", ".test.jsx")
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

DIYC_REL = ("diy-tools", "scripts", "diyc.py")


def v(code, where, msg):
    return {"code": code, "where": where, "msg": msg}


def nonempty(value):
    return value is not None and str(value).strip() != ""


def today():
    return datetime.date.today().isoformat()


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
    """读 YAML：(data, err)。缺失 → (None, None)；空 → ({}, None)；损坏 → (None, 原因)。"""
    if not os.path.isfile(path):
        return None, None
    try:
        with io.open(path, "r", encoding="utf-8") as f:
            return (yaml.safe_load(f) or {}), None
    except yaml.YAMLError as e:
        return None, str(e)
    except OSError as e:
        return None, str(e)


def save_yaml_atomic(path, data):
    """全文 load → 就地改 → dump → 同目录临时文件 + os.replace（契约 §3 写回纪律）。

    对齐 diyc_lib.save_yaml_atomic 先例：注释不保留；失败清理 tmp 后原样抛出。
    """
    tmp = path + ".tmp"
    try:
        with io.open(tmp, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False,
                           default_flow_style=False)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise


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


def builtin_framework(root):
    """内建测试链（无需第三方框架）：Cargo / Go / JVM 构建。"""
    table = (("Cargo.toml", "cargo test", "rust"),
             ("go.mod", "go test", "go"),
             ("pom.xml", "maven-surefire", "java"),
             ("build.gradle", "gradle test", "java"),
             ("build.gradle.kts", "gradle test", "java"))
    for rel, name, ptype in table:
        if os.path.isfile(os.path.join(root, rel)):
            return {"name": name, "detected_from": rel}, ptype
    return None, None


def detect_project_type(root):
    """project_type 判定（清单存在性，顺序即优先级）。返回 (type, 命中清单)。"""
    table = (("node", NODE_MANIFESTS), ("python", PY_MANIFESTS), ("rust", ("Cargo.toml",)),
             ("go", ("go.mod",)), ("java", JAVA_MANIFESTS), ("ruby", ("Gemfile",)),
             ("php", ("composer.json",)))
    for ptype, manifests in table:
        for rel in manifests:
            if os.path.isfile(os.path.join(root, rel)):
                return ptype, rel
    return "unknown", None


def is_test_file(name):
    lower = name.lower()
    if any(lower.endswith(s) for s in TEST_FILE_SUFFIXES):
        return True
    if lower.startswith("test_") and lower.endswith(".py"):
        return True
    if lower.endswith(("_test.py", "_test.go", "_test.rb")):
        return True
    return name.endswith(("Test.java", "Test.php"))


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


# ---------------------------------------------------------------- record

def load_tc_cases(path, show):
    """读 TC JSON 文件 → (cases | None, violations)。形态：[...] 或 {"test_cases": [...]}。"""
    if not os.path.isfile(path):
        return None, [v("MISSING_FILE", show, "TC 文件不存在（先落本次生成的用例 JSON）")]
    try:
        with io.open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except ValueError as e:
        return None, [v("ENTRY_INVALID", show, "TC 文件不是合法 JSON：%s" % e)]
    except OSError as e:
        return None, [v("MISSING_FILE", show, "TC 文件不可读：%s" % e)]
    if isinstance(data, dict):
        data = data.get("test_cases")
    if not isinstance(data, list) or not data:
        return None, [v("ENTRY_INVALID", show,
                        "TC 文件须为用例数组（或 {\"test_cases\": [...]}）且非空")]
    return data, []


def ac_of(tc_id):
    """TC-5.1.2 → AC-5.1（id 的 AC 前缀，须与 ac 字段一致）。"""
    return "AC-" + str(tc_id)[len("TC-"):].rsplit(".", 1)[0]


def req(violations, where, value, label):
    if not nonempty(value):
        violations.append(v("EMPTY_FIELD", where, "%s 缺失或为空" % label))
        return False
    return True


def enum(violations, where, value, allowed, label):
    if not nonempty(value):
        violations.append(v("EMPTY_FIELD", where, "%s 缺失或为空" % label))
        return False
    if str(value) not in allowed:
        violations.append(v("ENUM_INVALID", where, "%s 越界：%s（合法集 %s）"
                            % (label, value, "|".join(allowed))))
        return False
    return True


def check_case(case, index, show, known_ids, seen_new, known_acs, stories_available):
    """单条 TC 校验；where 相对 project-root、正斜杠。"""
    where = "%s test_cases[%d]" % (show, index)
    violations = []
    if not isinstance(case, dict):
        return [v("ENTRY_INVALID", where, "用例不是映射")]

    tc_id = case.get("id")
    where_id = "%s.id" % where
    if req(violations, where_id, tc_id, "id"):
        tc_id = str(tc_id)
        if not TC_RE.fullmatch(tc_id):
            violations.append(v("ENUM_INVALID", where_id,
                                "id 须为 TC-{ac}.{seq}（如 TC-5.1.2），实为 %s" % tc_id))
        elif tc_id in seen_new or tc_id in known_ids:
            violations.append(v("DUPLICATE_ID", where_id,
                                "TC ID %s 已存在（续号不重号：取该 AC 现有最大序号 + 1）"
                                % tc_id))

    ac = case.get("ac")
    where_ac = "%s.ac" % where
    if not nonempty(ac):
        violations.append(v("EMPTY_FIELD", where_ac,
                            "ac 缺失或为空（每个用例须绑定一个现有 AC ID）"))
    elif not isinstance(ac, str):
        violations.append(v("ENTRY_INVALID", where_ac,
                            "ac 须为单个 AC ID 字符串（e2e 用例一条绑一个 AC）"))
    elif not AC_RE.fullmatch(ac):
        violations.append(v("ENUM_INVALID", where_ac, "ac 须为 AC-x.y 形态，实为 %s" % ac))
    elif nonempty(tc_id) and TC_RE.fullmatch(str(tc_id)) and ac_of(tc_id) != ac:
        violations.append(v("ENTRY_INVALID", where_id,
                            "id 的 AC 前缀须与 ac 一致：%s 对应 %s，实为 %s"
                            % (tc_id, ac_of(tc_id), ac)))
    elif stories_available and ac not in known_acs:
        violations.append(v("UNKNOWN_ID", where_ac, "%s 在 %s 中不存在" % (ac, STORIES_FILE)))

    req(violations, "%s.title" % where, case.get("title"), "title")
    enum(violations, "%s.type" % where, case.get("type"), (E2E_TYPE,), "type")
    enum(violations, "%s.priority" % where, case.get("priority"), PRIORITIES, "priority")
    enum(violations, "%s.technique" % where, case.get("technique"),
         (E2E_TECHNIQUE,), "technique")
    req(violations, "%s.kill_target" % where, case.get("kill_target"), "kill_target（故障假设）")
    enum(violations, "%s.status" % where, case.get("status"), RECORD_STATUSES, "status")
    steps = case.get("steps")
    if not (isinstance(steps, list) and any(nonempty(x) for x in steps)):
        violations.append(v("EMPTY_FIELD", "%s.steps" % where,
                            "steps 缺失或为空（用例须可执行：具体步骤 + 预期结果）"))
    return violations


def load_known(output_dir, show, violations, warnings):
    """既有 test-plan.yaml → (plan, 既有 TC id 集, 故事 AC 集)。缺失 → 违规（零产出）。"""
    plan, err = load_yaml_safe(os.path.join(output_dir, PLAN_FILE))
    if plan is None and err is None:
        violations.append(v("MISSING_FILE", show,
                            "%s 不存在（用例须追加进既有测试计划——先跑 diy-test-design）"
                            % PLAN_FILE))
        return None, set(), set(), False
    if err is not None:
        violations.append(v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err))
        return None, set(), set(), False
    if not isinstance(plan, dict):
        violations.append(v("EMPTY_FIELD", show, "顶层不是映射（须为 project + test_cases）"))
        return None, set(), set(), False
    cases = plan.get("test_cases")
    if not isinstance(cases, list):
        violations.append(v("EMPTY_FIELD", show + " test_cases",
                            "test_cases 缺失或不是列表（追加目标不存在）"))
        return None, set(), set(), False
    known_ids = {str(c["id"]) for c in cases
                 if isinstance(c, dict) and nonempty(c.get("id"))}

    stories, s_err = load_yaml_safe(os.path.join(output_dir, STORIES_FILE))
    known_acs = set()
    stories_available = False
    if s_err is not None:
        warnings.append(v("UNPARSABLE_YAML", STORIES_FILE,
                          "上游文档不可解析，ac 引用无法核验：%s" % s_err))
    elif stories is None:
        warnings.append(v("MISSING_FILE", STORIES_FILE,
                          "stories.yaml 缺席：ac 引用无法核验（追加仍放行，由 diyc 复查）"))
    else:
        stories_available = True
        items = stories.get("stories") if isinstance(stories, dict) else None
        for story in items if isinstance(items, list) else []:
            if not isinstance(story, dict):
                continue
            acs = story.get("acceptance_criteria")
            for ac in acs if isinstance(acs, list) else []:
                if isinstance(ac, dict) and nonempty(ac.get("id")):
                    known_acs.add(str(ac["id"]))
    return plan, known_ids, known_acs, stories_available


def diyc_script_path():
    """diyc.py 路径：由引擎自身位置推算 skills 根（源码与安装布局同构，任务书 §2.3）。"""
    skills_root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    return os.path.join(skills_root, *DIYC_REL)


def diyc_check_test_plan(script, project_root, output_dir):
    """委派 diyc check --type test-plan（§2.3 跨文档核对唯一入口）。

    返回 (block, warnings)：违规并入 block.check.violations（warning 面），不阻塞 exit。
    """
    warnings = []
    block = {"available": False, "script": None, "check": {"ok": None, "violations": [],
                                                           "counts": {}}}
    if not os.path.isfile(script):
        warnings.append(v("TOOL_MISSING", "diy-tools/scripts/diyc.py",
                          "diyc.py 缺席：追加后全链交叉核对降级，请会话侧人工复核"))
        return block, warnings
    block["available"] = True
    block["script"] = display_path(script, project_root)
    cmd = [sys.executable, script, "check", "--type", "test-plan",
           "--project-root", project_root, "--json"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              encoding="utf-8", errors="replace")
    except OSError as e:
        warnings.append(v("TOOL_ERROR", "diyc.py check --type test-plan",
                          "diyc 子进程无法启动：%s" % e))
        return block, warnings
    if proc.returncode not in (0, 1):
        tail = " ".join((proc.stderr or proc.stdout or "").split())[-200:]
        warnings.append(v("TOOL_ERROR", "diyc.py check --type test-plan",
                          "diyc 非预期退出码 %s（期望 0|1）：%s"
                          % (proc.returncode, tail or "无输出")))
        return block, warnings
    payload = None
    for line in reversed((proc.stdout or "").splitlines()):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
            break
        except ValueError:
            continue
    if not isinstance(payload, dict):
        warnings.append(v("TOOL_ERROR", "diyc.py check --type test-plan",
                          "diyc 回执不可解析（--json 面单行 JSON 缺失）"))
        return block, warnings
    # diyc 自解析产物目录：与本引擎 --output-dir 不一致时证据来自另一目录，须显式告警
    resolved = payload.get("output_dir")
    if nonempty(resolved):
        a = os.path.normcase(os.path.abspath(os.path.join(project_root, str(resolved))))
        if a != os.path.normcase(os.path.abspath(output_dir)):
            warnings.append(v("SET_MISMATCH", str(resolved),
                              "diyc 解析的产物目录与本引擎 --output-dir 不一致："
                              "交叉核对证据可能来自另一目录"))
    block["check"] = {"ok": payload.get("ok"),
                      "violations": [x for x in payload.get("violations") or []
                                     if isinstance(x, dict)],
                      "counts": payload.get("counts") if isinstance(
                          payload.get("counts"), dict) else {}}
    return block, warnings


def cmd_record(args):
    root = os.path.abspath(args.project_root)
    out = os.path.abspath(args.output_dir)
    plan_path = os.path.join(out, PLAN_FILE)
    show = display_path(plan_path, root)
    tc_show = display_path(os.path.abspath(args.tc_file), root)
    violations = []
    warnings = []

    cases, tc_violations = load_tc_cases(os.path.abspath(args.tc_file), tc_show)
    violations += tc_violations
    plan = known_ids = known_acs = None
    stories_available = False
    if cases is not None:
        plan, known_ids, known_acs, stories_available = load_known(
            out, show, violations, warnings)

    if cases is not None and plan is not None:
        seen_new = set()
        for i, case in enumerate(cases):
            violations += check_case(case, i, show, known_ids, seen_new,
                                     known_acs, stories_available)
            if isinstance(case, dict) and nonempty(case.get("id")):
                seen_new.add(str(case["id"]))

    appended = [str(c["id"]) for c in cases
                if isinstance(c, dict) and nonempty(c.get("id"))] if cases else []
    if not violations:
        merged = list(plan.get("test_cases"))
        merged += [dict(c) for c in cases]
        project = plan.get("project")
        new_project = dict(project) if isinstance(project, dict) else {}
        new_project["updated"] = today()
        updated_plan = dict(plan)
        updated_plan["project"] = new_project
        updated_plan["test_cases"] = merged
        try:
            save_yaml_atomic(plan_path, updated_plan)
        except OSError as e:
            violations.append(v("TOOL_ERROR", show, "写回失败（原文件未改）：%s" % e))
            appended = []
        else:
            plan = updated_plan

    diyc_block = {"available": False, "script": None,
                  "check": {"ok": None, "violations": [], "counts": {}}}
    if not violations:
        diyc_block, diyc_warnings = diyc_check_test_plan(
            diyc_script_path(), root, out)
        warnings += diyc_warnings

    cases_total = 0
    if isinstance(plan, dict) and isinstance(plan.get("test_cases"), list):
        cases_total = len(plan["test_cases"])
    ok = not violations
    payload = {
        "ok": ok,
        "command": "record",
        "project_root": args.project_root,
        "output_dir": os.path.normpath(out).replace("\\", "/"),
        "appended": appended if ok else [],
        "violations": violations,
        "warnings": warnings,
        "counts": {"appended": len(appended) if ok else 0, "cases_total": cases_total},
        "diyc": diyc_block,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        if ok:
            print("PASS：追加 %d 条 e2e 用例（%s）→ %s（总用例 %d）"
                  % (len(appended), ", ".join(appended), show, cases_total))
            for item in diyc_block["check"]["violations"]:
                print("- [diyc] %s %s: %s" % (item.get("code"), item.get("where"),
                                              item.get("msg")))
        else:
            print("FAIL：追加被拒绝，零写入")
            for item in violations:
                print("- %s %s: %s" % (item["code"], item["where"], item["msg"]))
        for item in warnings:
            print("- %s %s: %s" % (item["code"], item["where"], item["msg"]))
    return 0 if ok else 1


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(
        description="diy-e2e-tests 确定性引擎：测试框架探测（detect）+ e2e 用例追加（record）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("detect", help="语言无关框架探测（只读；无框架回 suggested，不自动安装）")
    d.add_argument("--project-root", default=".", help="项目根（默认 .）")
    d.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    d.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    d.set_defaults(func=cmd_detect)

    r = sub.add_parser("record", help="把生成的 e2e 用例追加进 test-plan.yaml（校验通过才写）")
    r.add_argument("--tc-file", required=True, help="本次生成的 TC JSON 文件")
    r.add_argument("--project-root", default=".", help="项目根（默认 .）")
    r.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    r.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    r.set_defaults(func=cmd_record)

    args = ap.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
