# -*- coding: utf-8 -*-
"""diy-design audit 命令域：one-off 色值/字号审计（token 单一源）。."""

import io

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import v  # noqa: E402

from design_lib import HEX_RE, _FONT_SIZE_RE, collect_font_sizes, collect_token_hexes, dark_pair_violation, emit, iter_color_value_spans, norm_path, normalize_hex, read_design, receipt, strip_comments  # noqa: E402
AUDIT_EXTS = (".html", ".css", ".js", ".ts", ".jsx", ".tsx", ".vue")

def in_token_scope(path, scopes):
    """路径是否落在 token_scope 内（归一绝对路径后按前缀判定）。"""
    p = os.path.normcase(os.path.abspath(path))
    for scope in scopes:
        if p == scope or p.startswith(scope + os.sep):
            return True
    return False

def resolve_token_scope(design, src):
    """token_scope 解析为归一绝对路径：相对项按 --src 解析、绝对项原样。

    解析基 = `--src` 所在位置：目录形态即 src 本身（文档口径：`--src` 取项目根 src 或
    prototypes/）；文件形态取 dirname(src)——否则相对项会拼成 `<文件>/<相对项>` 这种
    永不命中的退化路径。命中判定仍是前缀包含（`in_token_scope`）：单文件形态下，相对项
    解析后恰好指向该文件（如 `--src …/src/app.css` + `[app.css]`）或绝对项为祖先目录/该
    文件时才跳过；相对项指祖先子树（`--src …/src/vendor/lib.css` + `[vendor]`）不命中
    ——要给单文件用相对项跳过，把 `--src` 给成目录，或写绝对项。
    """
    base = src if os.path.isdir(src) else os.path.dirname(src)
    scopes = []
    for entry in design.get("token_scope") or []:
        if not (isinstance(entry, str) and entry.strip()):
            continue
        raw = entry if os.path.isabs(entry) else os.path.join(base, entry)
        scopes.append(os.path.normcase(os.path.abspath(raw)))
    return scopes

def _rel_to(path, root):
    """相对化（跨盘等无法相对化时回退原值）。"""
    try:
        return norm_path(os.path.relpath(path, root))
    except ValueError:
        return norm_path(path)

def cmd_audit(args):  # trace: S-15 AC-15.2 TC-15.2.1 TC-14.3.2 one-off 色值/字号审计（归一比较，token 单一源）
    design, violations = read_design(args.design)
    rel = norm_path(args.design)
    counts = {"files": 0, "skipped": 0, "skipped_dirs": 0}
    if design is None:
        return emit(receipt("audit", False, file=rel, violations=violations, counts=counts),
                    args.json)
    if not os.path.exists(args.src):
        violations.append(v("MISSING_FILE", norm_path(args.src),
                            "src 不存在：%s——--src 取项目根 src 或 {output_dir}/prototypes"
                            % norm_path(args.src)))
        return emit(receipt("audit", False, file=rel, violations=violations, counts=counts),
                    args.json)
    hex_ok = collect_token_hexes(design)
    fs_ok = collect_font_sizes(design)
    dark_pair = dark_pair_violation(design, os.path.basename(args.design))  # modes 核心消费价值
    if dark_pair:
        violations.append(dark_pair)
    scopes = resolve_token_scope(design, args.src)
    warnings = []
    skipped = 0
    pruned = 0
    src_is_dir = os.path.isdir(args.src)
    root = os.path.dirname(os.path.abspath(args.src)) if src_is_dir else None
    if src_is_dir:
        files = []
        for dirpath, dirs, names in os.walk(args.src):
            keep = []
            for d in dirs:
                if scopes and in_token_scope(os.path.join(dirpath, d), scopes):
                    pruned += 1
                else:
                    keep.append(d)
            dirs[:] = keep
            for name in sorted(names):
                if not name.endswith(AUDIT_EXTS):
                    continue
                fpath = os.path.join(dirpath, name)
                if scopes and in_token_scope(fpath, scopes):
                    skipped += 1
                    continue
                files.append(fpath)
    else:
        files = [] if (scopes and in_token_scope(args.src, scopes)) else [args.src]
        skipped = 1 if not files else 0
    if scopes and (skipped or pruned):
        warnings.append("token_scope 生效：跳过 %d 个目录 / %d 个文件（%s）"
                        % (pruned, skipped, "、".join(norm_path(s) for s in scopes)))
    for fpath in files:
        ext = os.path.splitext(fpath)[1].lower()
        text = strip_comments(io.open(fpath, encoding="utf-8").read(), ext)
        where = _rel_to(fpath, root) if root else norm_path(fpath)
        for value in iter_color_value_spans(text, ext):
            for m in HEX_RE.finditer(value):
                try:
                    norm = normalize_hex(m.group(0))
                except ValueError:
                    norm = None
                if norm not in hex_ok:
                    violations.append(v("one-off-color", where,
                                        "色值 %s 不在 design token（单一源违规）" % m.group(0)))
        for m in _FONT_SIZE_RE.finditer(text):
            val = m.group(1).strip()
            if not (val.startswith("var(") or val in fs_ok):
                violations.append(v("one-off-font-size", where,
                                    "font-size: %s 既非 var() 也非 token 字阶" % val))
    result = receipt("audit", not violations, file=rel, violations=violations, warnings=warnings,
                     counts={"files": len(files), "skipped": skipped, "skipped_dirs": pruned},
                     audited=len(files))
    return emit(result, args.json, ["audit：审计 %d 文件%s"
                                    % (len(files), "，跳过 %d" % skipped if skipped else "")])
