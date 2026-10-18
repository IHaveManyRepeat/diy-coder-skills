# -*- coding: utf-8 -*-
"""diy-eval-runner memlog 域：内存日志引擎 + mlog 子命令（init / append / set-complete）。"""
import io
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import display_path, v, write_atomic  # noqa: E402

from eval_runner_lib import (  # noqa: E402
    ENTRY_TYPES, emit, memlog_now, norm, receipt, resolve_path_arg,
)

# --------------------------------------------------------------- memlog（与 W1 同构）

def memlog_split(text):
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise ValueError(".memlog.md 缺 frontmatter")
    end = next((i for i in range(1, len(lines)) if lines[i] == "---"), None)
    if end is None:
        raise ValueError(".memlog.md 的 frontmatter 未闭合")
    meta = {}
    for line in lines[1:end]:
        if ":" in line:
            k, val = line.split(":", 1)
            meta[k.strip()] = val.strip()
    return meta, "\n".join(lines[end + 1:]).lstrip("\n")


def memlog_render(meta, body):
    fm = "\n".join("%s: %s" % (k, " ".join(str(val).splitlines())) for k, val in meta.items())
    return "---\n%s\n---\n\n%s\n" % (fm, body.rstrip("\n"))


def memlog_touch(meta):
    meta.pop("updated", None)
    meta["updated"] = memlog_now()


def memlog_count(body):
    return sum(1 for ln in body.splitlines() if ln.startswith("- "))


def memlog_init(path, subject):
    """建 memlog；已存在抛 FileExistsError（只追加，永不覆盖）。"""
    if os.path.exists(path):
        raise FileExistsError(path)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    meta = {"status": "active"}
    if subject:
        meta = {"subject": subject, "status": "active"}
    memlog_touch(meta)
    write_atomic(path, memlog_render(meta, ""))
    return 0


def memlog_append(path, entry_type, text):
    meta, body = memlog_split(io.open(path, encoding="utf-8").read())
    entry = "- (%s) %s" % (entry_type, " ".join(str(text).split()))
    body = (body.rstrip("\n") + "\n" + entry) if body.strip() else entry
    memlog_touch(meta)
    write_atomic(path, memlog_render(meta, body))
    return memlog_count(body)


def memlog_set_complete(path):
    meta, body = memlog_split(io.open(path, encoding="utf-8").read())
    meta["status"] = "complete"
    memlog_touch(meta)
    write_atomic(path, memlog_render(meta, body))
    return memlog_count(body)

# --------------------------------------------------------------- mlog 子命令

def cmd_mlog(args):
    """memlog：原子追加、只追加。

    每次操作**恒发一行 JSON ack**（与 W1 的 mlog 同构）：共同键 + 命令级附加键
    `{file, n, appended}`（另带 `action`），人读态与 `--json` 开关都不改这条形状——
    调用方永远不必回读文件就知道新状态。
    """
    violations, warnings = [], []
    root = os.path.abspath(args.project_root)
    out = resolve_path_arg(args.output_dir, root, "--output-dir", violations)
    directory = resolve_path_arg(args.dir, root, "--dir", violations)
    name = str(args.file)
    if "/" in name or "\\" in name or name in (".", ".."):
        violations.append(v("NAME_ILLEGAL", "--file",
                            "只收文件名、不收路径（不靠 --dir 反推、也不许越出 --dir）：%r" % name))
    path = os.path.join(directory or root, name)
    payload = receipt("mlog", False, args.project_root, norm(out) if out else "",
                      violations, warnings, {"n": 0},
                      file=display_path(path, root), action=args.action)

    def finish(ok, n=0, appended=False, as_json=True):
        """成功的 ack = 共同键 + `{file, n, appended}`（恒发一行 JSON，与人读态无关）；
        被拒路径只回共同键 + `file` / `action`，并照 §2.2 的 `--json` 开关——与 W1 同形。"""
        payload["ok"] = bool(ok)
        payload["counts"] = {"n": n}
        if ok:
            payload["n"] = n
            payload["appended"] = bool(appended)
        return emit(payload, as_json,
                    ["mlog %s：%s（条目 %d）" % (args.action, "OK" if ok else "被拒绝", n)])

    if violations:
        return finish(False, as_json=args.json)
    try:
        if args.action == "init":
            memlog_init(path, args.subject)
            return finish(True, 0, False)
        if args.action == "set-complete":
            return finish(True, memlog_set_complete(path), False)
        if args.type not in ENTRY_TYPES:
            violations.append(v("ENUM_INVALID", "mlog --type",
                                "类型越界：%r（合法集 %s）" % (args.type, "|".join(ENTRY_TYPES))))
            return finish(False, as_json=args.json)
        if not str(args.text or "").strip():
            violations.append(v("EMPTY_FIELD", "mlog --text", "条目内容为空"))
            return finish(False, as_json=args.json)
        n = memlog_append(path, args.type, args.text)
        return finish(True, n, True)
    except FileExistsError:
        violations.append(v("FILE_CONFLICT", display_path(path, root),
                            "日志已存在：续写走 append（init 只建新档，只追加、永不覆盖）"))
    except OSError as e:
        violations.append(v("MISSING_FILE", display_path(path, root),
                            "日志不存在或不可写：先跑 `mlog init --subject S`（%s）" % e))
    except ValueError as e:
        violations.append(v("UNPARSABLE_YAML", display_path(path, root),
                            "memlog 形状非法：%s" % e))
    return finish(False, as_json=args.json)
