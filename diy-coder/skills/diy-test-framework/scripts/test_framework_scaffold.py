# -*- coding: utf-8 -*-
"""diy-test-framework scaffold 面：plan 渲染落盘（只写新文件；冲突即回滚）。"""
import io
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import display_path, nonempty, v, write_atomic  # noqa: E402

from test_framework_lib import (  # noqa: E402
    FILE_KINDS, PENDING_COMMAND_KEYS, PLAN_JSON, SETUP_RE, emit, load_json_safe,
    out_dir, parse_template, path_form_error, render_template, template_abs,
)

# ---------------------------------------------------------------- scaffold

def prepare_plan(root, plan_path):
    """预检（零写入）→ (plan, prepared, violations, warnings)。
    prepared = [{template, path, target, rendered}]。"""
    violations, warnings = [], []
    data, err = load_json_safe(plan_path)
    if data is None and err is None:
        return None, [], [v("MISSING_FILE", os.path.basename(plan_path),
                            "plan 文件不存在（03/04 步须先写 %s）" % PLAN_JSON)], warnings
    if err is not None:
        return None, [], [v("UNPARSABLE_YAML", os.path.basename(plan_path),
                            "plan 不可解析：%s" % err)], warnings
    if not isinstance(data, dict):
        return None, [], [v("ENTRY_INVALID", os.path.basename(plan_path), "plan 顶层须为对象")], warnings

    setup = data.get("setup")
    if not nonempty(setup) or not SETUP_RE.fullmatch(str(setup)):
        violations.append(v("ENUM_INVALID", "plan.setup", "setup 须为 TF-###（三位零填充）"))
    part = data.get("part")
    if part not in ("框架", "CI"):
        violations.append(v("ENUM_INVALID", "plan.part", "part 须为 框架|CI"))
    subs = data.get("substitutions")
    if not isinstance(subs, dict):
        violations.append(v("ENTRY_INVALID", "plan.substitutions", "substitutions 须为映射"))
        subs = {}
    else:
        for key, value in subs.items():
            if not isinstance(value, str):
                violations.append(v("ENTRY_INVALID", "plan.substitutions.%s" % key,
                                    "取值须为字符串（数字/布尔请写成字符串）"))
    files = data.get("files")
    if not isinstance(files, list) or not files:
        violations.append(v("ENTRY_INVALID", "plan.files", "files 须为非空列表"))
        files = []

    prepared, seen, used = [], set(), set()
    for i, item in enumerate(files):
        where = "plan.files[%d]" % i
        if not isinstance(item, dict):
            violations.append(v("ENTRY_INVALID", where, "条目须为映射"))
            continue
        rel_template = item.get("template")
        rel_path = item.get("path")
        kind = item.get("kind")
        if kind not in FILE_KINDS:
            violations.append(v("ENUM_INVALID", where + ".kind",
                                "kind 越界：%s（合法集 %s）" % (kind, "|".join(FILE_KINDS))))
        err_path = path_form_error(rel_path)
        if err_path is not None:
            violations.append(v("ENUM_INVALID", where + ".path",
                                "path %r 形态非法：%s（对齐 path: 口径）" % (rel_path, err_path)))
        elif rel_path in seen:
            violations.append(v("ENTRY_INVALID", where + ".path", "path %s 在 plan 内重复" % rel_path))
        else:
            seen.add(rel_path)
        abs_tpl = template_abs(rel_template)
        if abs_tpl is None or not os.path.isfile(abs_tpl):
            violations.append(v("MISSING_FILE", where + ".template",
                                "技能内模板不存在：%r（模板集是唯一来源，禁手写冒充）" % rel_template))
            continue
        try:
            with io.open(abs_tpl, "r", encoding="utf-8", newline="") as fh:
                text = fh.read()
        except OSError as e:
            violations.append(v("MISSING_FILE", where + ".template", "模板读取失败：%s" % e))
            continue
        rendered, render_err = render_template(text, subs)
        if render_err is not None:
            if render_err.startswith("占位符未取值"):
                violations.append(v("EMPTY_FIELD", where + ".template", render_err))
            else:
                violations.append(v("ENTRY_INVALID", where + ".template", render_err))
            continue
        declared, _body, _err = parse_template(text)
        used.update(declared or ())
        prepared.append({"template": rel_template, "path": rel_path, "kind": kind,
                         "target": os.path.join(root, *str(rel_path).split("/")),
                         "rendered": rendered})
    extra = sorted(set(subs) - used)
    if extra:
        warnings.append(v("EMPTY_FIELD", "plan.substitutions",
                          "以下取值未被本次模板使用（可共享给另一次 scaffold 调用）：%s"
                          % " ".join(extra)))
    return data, prepared, violations, warnings


def cmd_scaffold(args):
    root = os.path.abspath(args.project_root)
    out = out_dir(args)
    plan_path = args.plan if os.path.isabs(args.plan) else os.path.join(root, args.plan)
    show = display_path(plan_path, root)
    data, prepared, violations, warnings = prepare_plan(root, plan_path)
    written, skipped, conflicts, removed, failed = [], [], [], [], []
    setup = (data or {}).get("setup")
    part = (data or {}).get("part")
    subs = (data or {}).get("substitutions") if isinstance((data or {}).get("substitutions"),
                                                           dict) else {}
    if not violations:
        for entry in prepared:
            target = entry["target"]
            rel = entry["path"]
            if not os.path.exists(target):
                try:
                    write_atomic(target, entry["rendered"])
                except OSError as e:
                    violations.append(v("MISSING_FILE", rel, "写入失败：%s" % e))
                    break
                written.append(rel)
                continue
            try:
                with io.open(target, "r", encoding="utf-8", newline="") as fh:
                    current = fh.read()
            except (OSError, UnicodeDecodeError) as e:
                conflicts.append(rel)
                violations.append(v("FILE_CONFLICT", rel, "既有文件不可读，视为冲突：%s" % e))
                continue
            if current == entry["rendered"]:
                skipped.append(rel)                       # 幂等重入：同模板同 plan → 同字节
            else:
                conflicts.append(rel)
        if conflicts:
            # 回滚 = 撤销本次全部写入：整条拒绝后的净写入为 0，被撤销的路径记 rollback.removed
            pending_written = list(written)
            written = []
            for rel in reversed(pending_written):
                target = os.path.join(root, *rel.split("/"))
                try:
                    os.remove(target)
                    removed.append(rel)
                except OSError as e:
                    failed.append(rel)
                    warnings.append(v("MISSING_FILE", rel,
                                      "回滚删除失败（残留本次已写文件）：%s" % e))
            for rel in conflicts:
                violations.append(v("FILE_CONFLICT", rel,
                                    "目标已存在且内容与渲染结果不同——本技能不覆盖、不 merge 既有文件；"
                                    "请用户裁决（移除/改名旧文件后重入，或把该 path 移出 plan）"))
    pending = []
    for key in PENDING_COMMAND_KEYS:
        value = subs.get(key) if isinstance(subs, dict) else None
        if nonempty(value) and value not in pending:
            pending.append(value)
    ok = not violations
    counts = {"written": len(written), "skipped": len(skipped), "conflicts": len(conflicts),
              "files": len(prepared), "removed": len(removed), "failed_removed": len(failed)}
    payload = {"ok": ok, "command": "scaffold",
               "project_root": args.project_root,
               "output_dir": os.path.normpath(out).replace("\\", "/"),
               "plan": show, "setup": setup, "part": part,
               "written": written, "skipped": skipped, "conflicts": conflicts,
               "rollback": {"removed": removed, "conflicts": conflicts, "failed": failed},
               "pending_commands": pending,
               "violations": violations, "warnings": warnings, "counts": counts}
    emit(payload, args.json, human_scaffold)
    return 0 if ok else 1


def human_scaffold(payload):
    print("scaffold[%s] 写入 %d / 跳过 %d / 冲突 %d"
          % (payload["part"], payload["counts"]["written"], payload["counts"]["skipped"],
             payload["counts"]["conflicts"]))
    for rel in payload["written"]:
        print("+ %s" % rel)
    for rel in payload["skipped"]:
        print("= %s（内容等价，幂等跳过）" % rel)
    for rel in payload["rollback"]["removed"]:
        print("- %s（回滚删除）" % rel)
    if payload["pending_commands"]:
        print("待执行命令（步骤层）：")
        for cmd in payload["pending_commands"]:
            print("  $ %s" % cmd)
