# -*- coding: utf-8 -*-
"""bmb-builder 预扫与机械扫描：prepass / scan。"""

import ast
import os
import re

from bmb_builder_lib import (ABS_PATH_RE, BACKREF_PATTERNS, CROSS_DIR_RE,
                             DIRECTNESS_PATTERNS, ESCAPE_RE, FENCE_RE, IF_MARKER_RE,
                             INVALID_SECTIONS, LOCAL_DIR_RE, SCRIPT_DOCSTRING_ZH_RE,
                             SCAN_MD_DIRS, SECTION_TITLES, SKILL_FILE, STEPS_DIR,
                             STEP_FILE_RE, WASTE_PATTERNS, base_payload, emit, finish,
                             human_lines, read_text, resolve_arg_path, write_out)
from diyc_lib import display_path, v

# ---------------------------------------------------------------- 预扫（metrics / integrity）

# trace: diy-bmb-builder 技能内 .md 清单（根 + steps/references/assets 一层，不深挖）
def skill_md_files(target):
    files = []
    root_md = os.path.join(target, SKILL_FILE)
    if os.path.isfile(root_md):
        files.append(root_md)
    for sub in SCAN_MD_DIRS:
        directory = os.path.join(target, sub)
        if not os.path.isdir(directory):
            continue
        files += sorted(os.path.join(directory, name) for name in os.listdir(directory)
                        if name.lower().endswith(".md")
                        and os.path.isfile(os.path.join(directory, name)))
    return files


# trace: diy-bmb-builder .md 清单（全量，供 path-standards 扫）
def all_md_files(target):
    files = []
    for name in sorted(os.listdir(target)):
        path = os.path.join(target, name)
        if os.path.isfile(path) and name.lower().endswith(".md"):
            files.append(path)
    for sub in SCAN_MD_DIRS:
        directory = os.path.join(target, sub)
        if not os.path.isdir(directory):
            continue
        files += sorted(os.path.join(directory, name) for name in os.listdir(directory)
                        if name.lower().endswith(".md")
                        and os.path.isfile(os.path.join(directory, name)))
    return files


# trace: diy-bmb-builder token 计数（tiktoken cl100k_base；缺席降级 chars//4 并标 method）
_ENCODER = None


def count_tokens(text):
    global _ENCODER
    if _ENCODER is None:
        try:
            import tiktoken
            _ENCODER = tiktoken.get_encoding("cl100k_base")
        except Exception:
            _ENCODER = False
    if _ENCODER is False:
        return len(text) // 4, "fallback"
    return len(_ENCODER.encode(text)), "tiktoken"


# trace: diy-bmb-builder 模式命中（返 [{line, label, quote}]，行号 1 基）
def grep_patterns(text, patterns):
    hits = []
    for pattern, label in patterns:
        for match in pattern.finditer(text):
            line = text[:match.start()].count("\n") + 1
            raw = text.splitlines()[line - 1].strip() if line - 1 < len(text.splitlines()) else ""
            hits.append({"line": line, "label": label, "quote": raw[:120]})
    return hits


# trace: diy-bmb-builder metrics 面（只出数不判违规；废话/回指进 warning）
def metrics_result(target, root):
    entries = []
    warnings = []
    for path in skill_md_files(target):
        text, err = read_text(path, display_path(path, root))
        if err is not None:
            continue
        tokens, method = count_tokens(text)
        waste = grep_patterns(text, WASTE_PATTERNS)
        backrefs = grep_patterns(text, BACKREF_PATTERNS)
        numbered = bool(re.match(r"^\d{2}[-_]", os.path.basename(path)))
        entries.append({"file": display_path(path, root), "lines": len(text.splitlines()),
                        "tokens": tokens, "method": method, "waste": waste,
                        "backrefs": backrefs, "numbered_prefix": numbered})
        for hit in waste:
            warnings.append(v("ENUM_INVALID", "%s:%d" % (display_path(path, root), hit["line"]),
                              "废话模式（%s）：%s" % (hit["label"], hit["quote"])))
        for hit in backrefs:
            warnings.append(v("ENUM_INVALID", "%s:%d" % (display_path(path, root), hit["line"]),
                              "回指模式（%s）：%s" % (hit["label"], hit["quote"])))
    result = {
        "files": entries,
        "counts": {
            "files": len(entries),
            "lines": sum(e["lines"] for e in entries),
            "tokens": sum(e["tokens"] for e in entries),
            "waste": sum(len(e["waste"]) for e in entries),
            "backrefs": sum(len(e["backrefs"]) for e in entries),
            "numbered_prefix": sum(1 for e in entries if e["numbered_prefix"]),
        },
    }
    return result, warnings


# trace: diy-bmb-builder 围栏块位置判定（示例里的错形态不算违规）
def in_fenced_block(text, pos):
    return len(FENCE_RE.findall(text[:pos])) % 2 == 1


# trace: diy-bmb-builder integrity 面（结构判违规：阶段文件落点 / 禁用段 / 残留标记 / 四段 / steps 编号与引用 / 直白度）
def integrity_result(target, root):
    violations = []
    warnings = []
    skill_md = os.path.join(target, SKILL_FILE)
    show = display_path(skill_md, root)
    text, err = read_text(skill_md, show)
    if err is not None:
        violations.append(err)
        return violations, warnings, {"steps": 0, "issues": 1}
    for name in sorted(os.listdir(target)):
        path = os.path.join(target, name)
        if os.path.isfile(path) and name.lower().endswith(".md") and name != SKILL_FILE:
            violations.append(v(
                "NAME_ILLEGAL", display_path(path, root),
                "阶段文件散在技能根：一律落 `steps/NN-<名>.md`（技能根只许 SKILL.md）"))
    lines = text.splitlines()
    for i, line in enumerate(lines, 1):
        title = line.strip()
        if title in INVALID_SECTIONS:
            violations.append(v("ENUM_INVALID", "%s:%d" % (show, i),
                                "`%s` 段：diy 无 exit hook，该段永不执行，删掉" % title))
    for marker in sorted(set(IF_MARKER_RE.findall(text))):
        violations.append(v("TOKEN_UNRESOLVED", show,
                            "残留模板标记 %s：模板未展开就落盘" % marker))
    for section in SECTION_TITLES:
        if not any(line.strip() == section for line in lines):
            violations.append(v("EMPTY_FIELD", show, "缺必备段 `%s`" % section))
    steps_dir = os.path.join(target, STEPS_DIR)
    steps = []
    if os.path.isdir(steps_dir):
        steps = sorted(name for name in os.listdir(steps_dir)
                       if os.path.isfile(os.path.join(steps_dir, name))
                       and name.lower().endswith(".md"))
        numbers = []
        for name in steps:
            match = STEP_FILE_RE.match(name)
            if not match:
                violations.append(v("NAME_ILLEGAL", "%s/%s" % (STEPS_DIR, name),
                                    "步骤文件名须为 `NN-<名>.md`（两位数字前缀）"))
                continue
            numbers.append(int(match.group(1)))
        if numbers:
            expected = list(range(1, len(numbers) + 1))
            if numbers != expected:
                violations.append(v("SET_MISMATCH", STEPS_DIR,
                                    "步骤编号不连续：实为 %s，应为 %s"
                                    % (numbers, expected)))
    for match in LOCAL_DIR_RE.finditer(text):
        rel = "%s/%s" % (match.group(1), match.group(2).rstrip("/"))
        if not os.path.exists(os.path.join(target, match.group(1), match.group(2))):
            violations.append(v("MISSING_FILE", show, "SKILL.md 引用的 `%s` 不存在" % rel))
    for i, line in enumerate(lines, 1):
        for pattern, label in DIRECTNESS_PATTERNS:
            if pattern.search(line):
                warnings.append(v("ENUM_INVALID", "%s:%d" % (show, i), label))
    return violations, warnings, {"steps": len(steps), "issues": len(violations)}


# trace: diy-bmb-builder prepass 子命令（两套合一，一份 JSON；--set 默认 all）
def cmd_prepass(args):
    root = os.path.abspath(args.project_root)
    payload = base_payload("prepass", args, {})
    target, target_err = resolve_arg_path(args.target, root)
    if target_err is not None:
        payload["violations"].append(target_err)
        return finish(payload, args)
    show = display_path(target, root)
    if not os.path.isdir(target):
        payload["violations"].append(v("MISSING_FILE", show,
                                       "技能目录不存在：--target 须指向含 SKILL.md 的技能目录"))
        return finish(payload, args)
    if not os.path.isfile(os.path.join(target, SKILL_FILE)):
        payload["violations"].append(v("MISSING_FILE", show + "/" + SKILL_FILE,
                                       "%s 不存在：目标不是技能目录" % SKILL_FILE))
        return finish(payload, args)
    sets = set(args.set or ["all"])
    if "all" in sets:
        sets = {"metrics", "integrity"}
    counts = {}
    if "metrics" in sets:
        result, warns = metrics_result(target, root)
        payload["metrics"] = result
        payload["warnings"] += warns
        counts["metrics_files"] = result["counts"]["files"]
        counts["tokens"] = result["counts"]["tokens"]
    if "integrity" in sets:
        violations, warns, info = integrity_result(target, root)
        payload["integrity"] = {"steps": info["steps"], "issues": info["issues"]}
        payload["violations"] += violations
        payload["warnings"] += warns
        counts["steps"] = info["steps"]
    payload["counts"] = counts
    payload["target"] = show
    payload["sets"] = sorted(sets)
    payload["ok"] = not payload["violations"]
    write_out(args.out, payload)
    emit(payload, args.json, human_prepass)
    return 0 if payload["ok"] else 1


# trace: diy-bmb-builder prepass 人读态
def human_prepass(payload):
    human_lines(payload)
    counts = payload["counts"]
    if "tokens" in counts:
        print("metrics：文件 %d · token %d" % (counts.get("metrics_files", 0), counts["tokens"]))
    if "steps" in counts:
        print("integrity：步骤文件 %d · 违规 %d" % (counts["steps"], counts.get("issues", 0)))


# ---------------------------------------------------------------- scan（路径形态 / 脚本合规）

# trace: diy-bmb-builder path-standards 面（绝对路径 / ../ 越界 / ./<目录>/ 跨目录；围栏内豁免）
def scan_path_standards(target, root):
    violations = []
    files = []
    for path in all_md_files(target):
        show = display_path(path, root)
        files.append(show)
        text, err = read_text(path, show)
        if err is not None:
            violations.append(err)
            continue
        for pattern, message in ((ABS_PATH_RE, "绝对路径：换机即失效（改 project-root 相对或 {project-root} 令牌路径）"),
                                 (ESCAPE_RE, "`../` 越界引用：越出技能目录（内容依赖，改技能根相对 bare 路径）"),
                                 (CROSS_DIR_RE, "`./<目录>/` 跨目录引用：`./` 只表示同目录（改 bare 技能根相对路径）")):
            for match in pattern.finditer(text):
                if in_fenced_block(text, match.start()):
                    continue
                line = text[:match.start()].count("\n") + 1
                quote = text.splitlines()[line - 1].strip()[:120]
                violations.append(v("ENUM_INVALID", "%s:%d" % (show, line),
                                    "%s —— %s" % (message, quote)))
    return violations, {"files_scanned": len(files)}


# trace: diy-bmb-builder 内置 input() 调用判定（AST 精确判定；不靠正则，免得命中注释与文档里的字面提及）
def calls_input_builtin(text):
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id == "input"):
            return True
    return False


# trace: diy-bmb-builder scripts 面（套件代码惯例四件 + input( 违规；argparse/sys.exit 记 warning）
def scan_scripts(target):
    violations = []
    warnings = []
    directory = os.path.join(target, "scripts")
    scripts = []
    if os.path.isdir(directory):
        scripts = sorted(os.path.join(directory, name) for name in os.listdir(directory)
                         if name.lower().endswith(".py")
                         and os.path.isfile(os.path.join(directory, name)))
    for path in scripts:
        rel = "scripts/" + os.path.basename(path)
        text, err = read_text(path, rel)
        if err is not None:
            violations.append(err)
            continue
        head = text.splitlines()[0] if text.splitlines() else ""
        if head.strip() != "# -*- coding: utf-8 -*-":
            violations.append(v("EMPTY_FIELD", rel, "缺 `# -*- coding: utf-8 -*-` 头（套件代码惯例）"))
        if 'reconfigure(encoding="utf-8")' not in text:
            violations.append(v("EMPTY_FIELD", rel, "缺 `sys.stdout.reconfigure(encoding=\"utf-8\")`"))
        if not SCRIPT_DOCSTRING_ZH_RE.search(text.split('"""')[1] if text.count('"""') >= 2 else ""):
            violations.append(v("EMPTY_FIELD", rel, "缺中文模块 docstring"))
        if "# trace:" not in text:
            violations.append(v("EMPTY_FIELD", rel, "缺 `# trace:` 注释（实现自身也吃自家 trace 规范）"))
        if calls_input_builtin(text):
            violations.append(v("ENUM_INVALID", rel, "含 input() 调用：无头态阻塞，改旗标传入"))
        if "argparse" not in text:
            warnings.append(v("EMPTY_FIELD", rel, "未用 argparse：脚本无 CLI 面（若为纯库可忽略）"))
        if "sys.exit" not in text:
            warnings.append(v("EMPTY_FIELD", rel, "无 sys.exit：退出码面缺失"))
    return violations, warnings, {"scripts_scanned": len(scripts)}


# trace: diy-bmb-builder scan 子命令（机械面；--check 默认 all）
def cmd_scan(args):
    root = os.path.abspath(args.project_root)
    payload = base_payload("scan", args, {})
    target, target_err = resolve_arg_path(args.target, root)
    if target_err is not None:
        payload["violations"].append(target_err)
        return finish(payload, args)
    show = display_path(target, root)
    if not os.path.isdir(target) or not os.path.isfile(os.path.join(target, SKILL_FILE)):
        payload["violations"].append(v("MISSING_FILE", show,
                                       "技能目录不存在或缺 SKILL.md"))
        return finish(payload, args)
    checks = args.check
    summary = {}
    if checks in ("all", "path-standards"):
        violations, info = scan_path_standards(target, root)
        payload["violations"] += violations
        summary.update(info)
    if checks in ("all", "scripts"):
        violations, warns, info = scan_scripts(target)
        payload["violations"] += violations
        payload["warnings"] += warns
        summary.update(info)
    payload["scan"] = {"checks": checks, "files_scanned": summary.get("files_scanned", 0),
                       "scripts_scanned": summary.get("scripts_scanned", 0)}
    payload["counts"] = {"files_scanned": summary.get("files_scanned", 0),
                         "scripts_scanned": summary.get("scripts_scanned", 0)}
    payload["ok"] = not payload["violations"]
    write_out(args.out, payload)
    emit(payload, args.json, human_lines)
    return 0 if payload["ok"] else 1
