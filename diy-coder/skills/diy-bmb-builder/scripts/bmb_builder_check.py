# -*- coding: utf-8 -*-
"""bmb-builder 过程日志与产物终门：mlog / check。"""

import os
from datetime import datetime

import yaml

from bmb_builder_lib import (ENTRY_TYPES, ESCAPE_RE, FROZEN_ANCHORS, LOCAL_DIR_RE,
                             NAME_RE, REGISTRY_FIELDS, SECTION_TITLES, SKILL_FILE, SKILL_MD_MAX_LINES,
                             STEPS_DIR, STEP_H1_RE, STEP_MENTION_RE, base_payload,
                             emit, finish, human_lines, read_text,
                             resolve_arg_path)
from bmb_builder_scan import skill_md_files  # noqa: E402
from diyc_lib import display_path, nonempty, v, write_atomic

# ---------------------------------------------------------------- mlog（过程日志）

# trace: diy-bmb-builder memlog 文件拆分（(frontmatter, body)；围栏按整行 --- 判定）
def split_memlog(text):
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("缺 frontmatter")
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        raise ValueError("frontmatter 未闭合")
    meta = {}
    for line in lines[1:end]:
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
    return meta, "\n".join(lines[end + 1:]).lstrip("\n")


# trace: diy-bmb-builder memlog 渲染（frontmatter 单行值 + 空行 + 条目体）
def render_memlog(meta, body):
    front = "\n".join("%s: %s" % (key, " ".join(str(value).splitlines()))
                      for key, value in meta.items())
    return "---\n" + front + "\n---\n\n" + body.rstrip("\n") + "\n"


# trace: diy-bmb-builder memlog 条目计数（`- ` 起始行）
def memlog_count(body):
    return sum(1 for line in body.splitlines() if line.startswith("- "))


# trace: diy-bmb-builder mlog 子命令（只追加 + 原子写 + 恒发一行 JSON ack）
def cmd_mlog(args):
    root = os.path.abspath(args.project_root)
    payload = base_payload("mlog", args, {"n": 0})
    directory, dir_err = resolve_arg_path(args.dir, root)
    name = str(args.file)
    # 文件名校验（与 W3 的 mlog 同构）：只收纯文件名——路径分隔符 / `.` / `..` / 空白名一律拒绝，
    # 否则 --dir 的边界形同虚设，写面会越出 {output_dir}/build-logs。
    if "/" in name or "\\" in name or name in (".", "..") or not name.strip():
        payload["violations"].append(v(
            "NAME_ILLEGAL", "--file",
            "只收文件名、不收路径（不靠 --dir 反推、也不许越出 --dir）：%r" % name))
    path = os.path.join(directory or root, name) if name.strip() else (directory or root)
    show = display_path(path, root)
    payload["file"] = show
    payload["action"] = args.action
    if dir_err is not None:
        payload["violations"].append(dir_err)
    if payload["violations"]:
        return finish(payload, args, human_lines)
    action = args.action
    if action == "init":
        if os.path.exists(path):
            payload["violations"].append(v("FILE_CONFLICT", show,
                                           "日志已存在：续写走 append（init 只建新档）"))
            return finish(payload, args, human_lines)
        meta = {}
        if nonempty(args.subject):
            meta["subject"] = str(args.subject)
        meta["status"] = "active"
        meta["updated"] = datetime.now().strftime("%Y-%m-%dT%H:%M")
        write_atomic(path, render_memlog(meta, ""))
        payload["n"] = 0
    else:
        if not os.path.isfile(path):
            payload["violations"].append(v("MISSING_FILE", show,
                                           "日志不存在：先跑 `mlog init --subject S`"))
            return finish(payload, args, human_lines)
        text, err = read_text(path, show)
        if err is not None:
            payload["violations"].append(err)
            return finish(payload, args, human_lines)
        try:
            meta, body = split_memlog(text)
        except ValueError as e:
            payload["violations"].append(v("UNPARSABLE_YAML", show, "memlog 形状非法：%s" % e))
            return finish(payload, args, human_lines)
        if action == "append":
            if args.type not in ENTRY_TYPES:
                payload["violations"].append(v(
                    "ENUM_INVALID", "mlog --type",
                    "类型越界：%r（合法集 %s）" % (args.type, "|".join(ENTRY_TYPES))))
                return finish(payload, args, human_lines)
            if not nonempty(args.text):
                payload["violations"].append(v("EMPTY_FIELD", "mlog --text", "条目内容为空"))
                return finish(payload, args, human_lines)
            entry = "- (%s) %s" % (args.type, " ".join(str(args.text).split()))
            body = (body.rstrip("\n") + "\n" + entry) if body.strip() else entry
            payload["appended"] = True
        elif action == "set-complete":
            meta["status"] = "complete"
            payload["appended"] = False
        else:
            payload["violations"].append(v("ENUM_INVALID", "mlog",
                                           "未知动作 %r（合法集 init|append|set-complete）" % action))
            return finish(payload, args, human_lines)
        meta.pop("updated", None)
        meta["updated"] = datetime.now().strftime("%Y-%m-%dT%H:%M")
        write_atomic(path, render_memlog(meta, body))
        payload["n"] = memlog_count(body)
    payload["appended"] = bool(payload.get("appended", False))
    payload["counts"] = {"n": payload["n"]}
    payload["ok"] = True
    emit(payload, True, None)
    return 0


# ---------------------------------------------------------------- check（产物终门）

# trace: diy-bmb-builder frontmatter 解析（缺失/未闭合/非映射 → 违规）
def parse_frontmatter(text, show):
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, [v("EMPTY_FIELD", show, "缺 YAML frontmatter（须以 `---` 起）")]
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        return None, [v("EMPTY_FIELD", show, "frontmatter 未闭合")]
    try:
        data = yaml.safe_load("\n".join(lines[1:end])) or {}
    except yaml.YAMLError as e:
        return None, [v("UNPARSABLE_YAML", show, "frontmatter 解析失败：%s" % str(e).splitlines()[0])]
    if not isinstance(data, dict):
        return None, [v("EMPTY_FIELD", show, "frontmatter 不是映射")]
    return data, []


# trace: diy-bmb-builder frontmatter 六字段校验（形态：phase/line/outputs 非空、required 布尔、precededBy/followedBy 列表）
def check_frontmatter(data, show):
    violations = []
    name = data.get("name")
    if not nonempty(name):
        violations.append(v("EMPTY_FIELD", show + " frontmatter.name", "name 缺失"))
    elif not NAME_RE.match(str(name)):
        violations.append(v("NAME_ILLEGAL", show + " frontmatter.name",
                            "name 须为 hyphen-case：%r" % name))
    if not nonempty(data.get("description")):
        violations.append(v("EMPTY_FIELD", show + " frontmatter.description", "description 缺失"))
    for field in REGISTRY_FIELDS:
        if field not in data:
            violations.append(v("EMPTY_FIELD", "%s frontmatter.%s" % (show, field),
                                "登记元数据 %s 缺失（六字段封闭集）" % field))
    for field in ("phase", "line", "outputs"):
        if field in data and not nonempty(data.get(field)):
            violations.append(v("EMPTY_FIELD", "%s frontmatter.%s" % (show, field),
                                "%s 为空" % field))
    if "required" in data and not isinstance(data.get("required"), bool):
        violations.append(v("ENUM_INVALID", show + " frontmatter.required",
                            "required 须为布尔"))
    for field in ("precededBy", "followedBy"):
        if field in data and not isinstance(data.get(field), list):
            violations.append(v("ENUM_INVALID", "%s frontmatter.%s" % (show, field),
                                "%s 须为列表（空则 []）" % field))
    return violations


# trace: diy-bmb-builder 自足性（技能根相对引用须在目录内；../ 越界判内容依赖）
def check_self_sufficiency(target, root, texts):
    violations = []
    for show, text in texts:
        match = ESCAPE_RE.search(text)
        if match:
            line = text[:match.start()].count("\n") + 1
            violations.append(v("FILE_CONFLICT", "%s:%d" % (show, line),
                                "`../` 越界引用：技能目录外的内容依赖（自足判据禁内容依赖；"
                                "套件级调用与 {project-root} 令牌路径豁免）"))
        for hit in LOCAL_DIR_RE.finditer(text):
            rel = "%s/%s" % (hit.group(1), hit.group(2).rstrip("/"))
            if not os.path.exists(os.path.join(target, hit.group(1), hit.group(2))):
                violations.append(v("MISSING_FILE", show, "引用的 `%s` 不在技能目录内" % rel))
    return violations


# trace: diy-bmb-builder steps 形态（H1 中文步名 / Read-Write 行 / 结尾点名下一步；--final 面）
def check_steps(target, root, final):
    violations = []
    warnings = []
    directory = os.path.join(target, STEPS_DIR)
    steps = []
    if os.path.isdir(directory):
        steps = sorted(name for name in os.listdir(directory)
                       if os.path.isfile(os.path.join(directory, name))
                       and name.lower().endswith(".md"))
    if not steps and final:
        violations.append(v("MISSING_FILE", STEPS_DIR + "/",
                            "结构终门要求至少一个步骤文件（steps/ 在场且非空）："
                            "SKILL.md 的读取纪律以步骤文件为执行单元"))
        return violations, warnings
    for index, name in enumerate(steps, start=1):
        rel = "%s/%s" % (STEPS_DIR, name)
        text, err = read_text(os.path.join(directory, name), rel)
        if err is not None:
            violations.append(err)
            continue
        lines = text.replace("\r\n", "\n").split("\n")
        first = lines[0] if lines else ""
        if not STEP_H1_RE.match(first):
            violations.append(v("EMPTY_FIELD", rel, "H1 须为 `# Step N — <中文步名>`，实为 %r" % first))
        if not any(line.startswith("**Read (input):**") for line in lines):
            violations.append(v("EMPTY_FIELD", rel, "缺 `**Read (input):**` 行（冒号须半角）"))
        if not any(line.startswith("**Write (output):**") for line in lines):
            violations.append(v("EMPTY_FIELD", rel, "缺 `**Write (output):**` 行（冒号须半角）"))
        if final:
            if index < len(steps):
                if not any(other != name and other in text for other in steps):
                    violations.append(v("EMPTY_FIELD", rel,
                                        "步尾未点名下一个要读的步骤文件（可含分支路由）："
                                        "候选 %s" % "、".join(other for other in steps if other != name)))
            elif STEP_MENTION_RE.search(text):
                warnings.append(v("EMPTY_FIELD", rel,
                                  "末步仍点名步骤文件：末步须声明不再读任何 `steps/` 文件"))
    return violations, warnings


# trace: diy-bmb-builder check 子命令（基础项 + --final 结构终门）
def cmd_check(args):
    root = os.path.abspath(args.project_root)
    payload = base_payload("check", args, {"steps": 0, "lines": 0, "violations": 0})
    target, target_err = resolve_arg_path(args.target, root)
    if target_err is not None:
        payload["violations"].append(target_err)
        return finish(payload, args, human_lines)
    show = display_path(target, root)
    skill_md = os.path.join(target, SKILL_FILE)
    skill_show = display_path(skill_md, root)
    if not os.path.isdir(target):
        payload["violations"].append(v("MISSING_FILE", show, "技能目录不存在"))
        return finish(payload, args, human_lines)
    if not os.path.isfile(skill_md):
        payload["violations"].append(v("MISSING_FILE", skill_show, "%s 不存在" % SKILL_FILE))
        return finish(payload, args, human_lines)
    text, err = read_text(skill_md, skill_show)
    if err is not None:
        payload["violations"].append(err)
        return finish(payload, args, human_lines)
    lines = text.splitlines()
    for section in SECTION_TITLES:
        if not any(line.strip() == section for line in lines):
            payload["violations"].append(v("EMPTY_FIELD", skill_show, "缺四段之一 `%s`" % section))
    for anchor in FROZEN_ANCHORS:
        if anchor not in text:
            payload["violations"].append(v(
                "EMPTY_FIELD", skill_show,
                "母本锚串未逐字在场（须逐字复制、禁改写）：%r" % anchor[:32]))
    data, fm_violations = parse_frontmatter(text, skill_show)
    payload["violations"] += fm_violations
    if data is not None:
        payload["violations"] += check_frontmatter(data, skill_show)
    texts = [(skill_show, text)]
    for path in skill_md_files(target):
        if os.path.abspath(path) == os.path.abspath(skill_md):
            continue
        rel = display_path(path, root)
        body, body_err = read_text(path, rel)
        if body_err is None:
            texts.append((rel, body))
    payload["violations"] += check_self_sufficiency(target, root, texts)
    step_violations, step_warnings = check_steps(target, root, args.final)
    payload["violations"] += step_violations
    payload["warnings"] += step_warnings
    if args.final and len(lines) > SKILL_MD_MAX_LINES:
        payload["violations"].append(v(
            "SET_MISMATCH", skill_show,
            "SKILL.md 行数 %d 超固定阈值 %d（唯一硬阈值；token 计数只作信息面，不作门禁）"
            % (len(lines), SKILL_MD_MAX_LINES)))
    payload["target"] = show
    payload["final"] = bool(args.final)
    payload["counts"] = {"steps": _steps_count(target), "lines": len(lines),
                         "violations": len(payload["violations"])}
    payload["ok"] = not payload["violations"]
    emit(payload, args.json, human_lines)
    return 0 if payload["ok"] else 1


# trace: diy-bmb-builder 步骤文件计数（终门计数用）
def _steps_count(target):
    directory = os.path.join(target, STEPS_DIR)
    if not os.path.isdir(directory):
        return 0
    return sum(1 for name in os.listdir(directory)
               if name.lower().endswith(".md")
               and os.path.isfile(os.path.join(directory, name)))
