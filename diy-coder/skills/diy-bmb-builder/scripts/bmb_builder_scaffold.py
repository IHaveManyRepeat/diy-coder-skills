# -*- coding: utf-8 -*-
"""bmb-builder 脚手架与模板机：scaffold / template。"""

import argparse
import os
import re
import shutil
import sys

from bmb_builder_lib import (IF_BLOCK_RE, IF_MARKER_RE, INSTALL_REL, KNOWN_DIRS,
                             NAME_MAX, PROJECT_ROOT_TOKEN, SKILL_FILE, SKILL_TEMPLATE,
                             SOURCE_REL, TOKEN_RE, base_payload, emit, finish, human_lines,
                             normalize_name, protected_names, read_text,
                             resolve_arg_path)
from diyc_lib import display_path, v, write_atomic

# ---------------------------------------------------------------- scaffold

# trace: diy-bmb-builder 子目录参数解析（KNOWN_DIRS 闭集，越界 → ENUM_INVALID）
def parse_dirs(raw):
    requested = []
    for item in str(raw or "").split(","):
        name = item.strip()
        if not name:
            continue
        if name not in KNOWN_DIRS:
            return None, v("ENUM_INVALID", "scaffold --dirs", "未知子目录 %r（合法集 %s）"
                           % (name, "|".join(KNOWN_DIRS)))
        requested.append(name)
    return requested, None


# trace: diy-bmb-builder 目标基准目录（安装面 / 套件源 / --dest，三者互斥规则见 docstring）
def scaffold_base(args, root):
    if args.to_source:
        base = os.path.join(root, *SOURCE_REL)
        if not os.path.isdir(base):
            return None, v("MISSING_FILE", os.path.join(*SOURCE_REL).replace("\\", "/") + "/",
                           "套件源目录缺席：--to-source 只对 diy-coder 仓有效，不代建父目录")
        return base, None
    resolved, err = resolve_arg_path(args.dest or os.path.join(PROJECT_ROOT_TOKEN, *INSTALL_REL),
                                     root)
    if err is not None:
        return None, err
    return resolved, None


# trace: diy-bmb-builder scaffold 子命令（建技能目录骨架；护栏 + 落点 + files_created）
def cmd_scaffold(args):
    root = os.path.abspath(args.project_root)
    payload = base_payload("scaffold", args, {"files_created": 0, "dirs_stubbed": 0})
    raw = args.name
    name = normalize_name(raw)
    if not name or name != str(raw).strip():
        payload["violations"].append(v(
            "NAME_ILLEGAL", "scaffold --name",
            "技能名须为 hyphen-case（≤%d 字符）：%r 归一后为 %r；请直接用归一形态重跑"
            % (NAME_MAX, raw, name)))
        return finish(payload, args, human_scaffold)
    if args.to_source and not name.startswith("diy-"):
        payload["violations"].append(v(
            "NAME_ILLEGAL", "scaffold --name",
            "--to-source 落套件源，技能名须带 `diy-` 前缀（install.py 只分发该前缀）：%r" % name))
        return finish(payload, args, human_scaffold)
    dirs, dir_err = parse_dirs(args.dirs)
    if dir_err is not None:
        payload["violations"].append(dir_err)
        return finish(payload, args, human_scaffold)
    base, base_err = scaffold_base(args, root)
    if base_err is not None:
        payload["violations"].append(base_err)
        return finish(payload, args, human_scaffold)
    target = os.path.join(base, name)
    show = display_path(target, root)
    if args.force and name in protected_names():
        payload["violations"].append(v(
            "FILE_CONFLICT", show,
            "硬护栏：%r 命中套件已建技能名或禁改面，--force 也不得覆盖（改别的名字，"
            "或按 Edit 意图在交互态逐文件改）" % name))
        return finish(payload, args, human_scaffold)
    if os.path.exists(target):
        if not args.force:
            payload["violations"].append(v(
                "FILE_CONFLICT", show,
                "目标已存在：默认拒绝覆盖（Edit 意图改造走交互确认；无头态经 "
                "`diyc.py defer-add --reason 破坏性操作` 入队后不推进）"))
            return finish(payload, args, human_scaffold)
        shutil.rmtree(target)
    if os.path.exists(target):
        payload["violations"].append(v("FILE_CONFLICT", show, "目标仍存在：清场失败，已中止"))
        return finish(payload, args, human_scaffold)
    files_created = []
    try:
        os.makedirs(target)
        skill_md = os.path.join(target, SKILL_FILE)
        write_atomic(skill_md, SKILL_TEMPLATE.replace("{skill-name}", name))
        files_created.append(display_path(target, root) + "/")
        files_created.append(display_path(skill_md, root))
        for sub in dirs:
            os.makedirs(os.path.join(target, sub))
            files_created.append(display_path(os.path.join(target, sub), root) + "/")
    except OSError as e:
        sys.stderr.write("诊断：脚手架落盘失败 %s：%s\n" % (show, e))
        payload["violations"].append(v("FILE_CONFLICT", show, "落盘失败：%s" % e))
        return finish(payload, args, human_scaffold)
    payload["files_created"] = files_created
    payload["counts"] = {"files_created": len(files_created), "dirs_stubbed": len(dirs)}
    payload["skill"] = show
    payload["force"] = bool(args.force)
    return finish(payload, args, human_scaffold)


# trace: diy-bmb-builder scaffold 人读态（落了什么 + 下一步）
def human_scaffold(payload):
    human_lines(payload)
    if payload["ok"]:
        print("技能骨架：%s" % payload["skill"])
        for item in payload["files_created"]:
            print("- %s" % item)


# ---------------------------------------------------------------- template

# trace: diy-bmb-builder 条件块展开（由内向外；真则留内容、假则删块；塌掉多余空行）
def process_conditionals(text, true_conditions):
    kept = []
    dropped = []
    changed = True
    while changed:
        changed = False
        match = IF_BLOCK_RE.search(text)
        if match:
            changed = True
            condition, inner = match.group(1), match.group(2)
            if condition in true_conditions:
                replacement = inner
                if condition not in kept:
                    kept.append(condition)
            else:
                replacement = ""
                if condition not in dropped:
                    dropped.append(condition)
            text = text[:match.start()] + replacement + text[match.end():]
    return re.sub(r"\n{3,}", "\n\n", text), kept, dropped


# trace: diy-bmb-builder 变量替换（只换给了值的键；未给的原样留给 tokens_remaining）
def process_variables(text, variables):
    substituted = []
    for key, value in variables.items():
        placeholder = "{%s}" % key
        if placeholder in text:
            text = text.replace(placeholder, value)
            substituted.append(key)
    return text, substituted


# trace: diy-bmb-builder --set k=v 解析（无等号 → argparse 用法错误 exit 2）
def parse_set(raw):
    if "=" not in raw:
        raise argparse.ArgumentTypeError("--set 须为 k=v：%r" % raw)
    key, _, value = raw.partition("=")
    if not key.strip():
        raise argparse.ArgumentTypeError("--set 的键为空：%r" % raw)
    return key.strip(), value


# trace: diy-bmb-builder template 子命令（两级失败语义：残留 {if-} exit 3 / 残留 {token} 交人判断）
def cmd_template(args):
    root = os.path.abspath(args.project_root)
    payload = base_payload("template", args, {"substituted": 0, "conditions_true": 0,
                                              "conditions_false": 0, "tokens_remaining": 0})
    src, src_err = resolve_arg_path(args.src, root)
    if src_err is not None:
        payload["violations"].append(src_err)
        return finish(payload, args, human_template)
    dest, dest_err = resolve_arg_path(args.dest, root)
    if dest_err is not None:
        payload["violations"].append(dest_err)
        return finish(payload, args, human_template)
    src_show = display_path(src, root)
    if not os.path.isfile(src):
        payload["violations"].append(v("MISSING_FILE", src_show, "模板文件不存在"))
        return finish(payload, args, human_template)
    text, err = read_text(src, src_show)
    if err is not None:
        payload["violations"].append(err)
        return finish(payload, args, human_template)
    variables = dict(args.set or [])
    text, kept, dropped = process_conditionals(text, set(args.true or []))
    text, substituted = process_variables(text, variables)
    leftovers = sorted(set(IF_MARKER_RE.findall(text)))
    if leftovers:
        payload["violations"].append(v(
            "TOKEN_UNRESOLVED", src_show,
            "残留条件块标记 %s：模板括号写错，原样输出会把标记 ship 出去（本轮硬失败、零产出）"
            % "、".join(leftovers)))
        payload["ok"] = False
        emit(payload, args.json, human_lines)
        return 3
    tokens = sorted(tok for tok in set(TOKEN_RE.findall(text)) if not tok.startswith("if-"))
    try:
        write_atomic(dest, text)
    except OSError as e:
        sys.stderr.write("诊断：模板输出失败 %s：%s\n" % (display_path(dest, root), e))
        payload["violations"].append(v("FILE_CONFLICT", display_path(dest, root),
                                       "输出失败：%s" % e))
        return finish(payload, args, human_template)
    payload["tokens_remaining"] = ["{%s}" % tok for tok in tokens]
    payload["counts"] = {"substituted": len(substituted), "conditions_true": len(kept),
                         "conditions_false": len(dropped),
                         "tokens_remaining": len(payload["tokens_remaining"])}
    return finish(payload, args, human_template)


# trace: diy-bmb-builder template 人读态（替换了什么 / 还剩什么令牌）
def human_template(payload):
    human_lines(payload)
    if payload["ok"]:
        print("输出：%s" % payload["output_dir"])
        print("剩余令牌（交人判断，不算失败）：%s"
              % ("、".join(payload["tokens_remaining"]) or "无"))
