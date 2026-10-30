# -*- coding: utf-8 -*-
"""diyc 共享层回执与输出：receipt/emit/run_tool/baseline 台账。"""

import json
import os
import subprocess

from diyc_lib_base import (load_yaml, load_yaml_checked, load_yaml_safe, nonempty,
                           save_yaml_atomic, today, v)

# ---------------------------------------------------------------- 回执与输出

def receipt(command, ok, **fields) -> dict:
    """回执基础构造；公共键（project_root/output_dir/instance/violations/warnings/counts）
    由 diyc.py 收口补齐（契约 §2）。"""
    r = {"ok": bool(ok), "command": command}
    r.update(fields)
    return r


def receipt_base(command, args, output_dir) -> dict:
    """回执公共骨架（契约 §3 schema）：ok 恒 False 起步·`instance` 恒 null 但键在位；
    output_dir 缺席/空分开答（空 → None·不 normpath 成 "."）。`args` 传命令行对象
    （取其 project_root）。"""
    return {"ok": False,
            "command": command,
            "project_root": args.project_root,
            "output_dir": (os.path.normpath(output_dir).replace("\\", "/")
                           if nonempty(output_dir) else None),
            "instance": None,
            "violations": [],
            "warnings": [],
            "counts": {}}


def read_sessions(path, show):
    """读产物并取 sessions 列表 → (records | None, violations, warnings)。"""
    data, code, err = load_yaml_checked(path)
    if data is None and err is None:
        return None, [], []
    if err is not None:
        # DUPLICATE_KEY 与 UNPARSABLE_YAML 区分（重复键≠解析失败）
        return None, [v(code, show, "YAML %s：%s"
                        % ("重复键" if code == "DUPLICATE_KEY" else "解析失败", err))], []
    if not isinstance(data, dict):
        return None, [v("EMPTY_FIELD", show, "顶层不是映射（须为 project + sessions）")], []
    raw = data.get("sessions")
    if raw is None:
        return [], [], []
    if not isinstance(raw, list):
        return None, [v("EMPTY_FIELD", show + " sessions",
                        "sessions 不是列表（集合形态；无记录写空列表）")], []
    warnings = []
    for i, rec in enumerate(raw):
        if not isinstance(rec, dict):
            warnings.append(v("EMPTY_FIELD", "%s.sessions[%d]" % (show, i),
                              "记录不是映射，list 面跳过（check 面报违规）"))
    return raw, [], warnings


def violation_line(item) -> str:
    """通用违规行式样：`CODE where: msg`（全库 20+ 家逐字同款·单源化）。"""
    return "%s %s: %s" % (item.get("code"), item.get("where"), item.get("msg"))


def warn_line(item) -> str:
    """通用警告行式样：`WARN CODE where: msg`。"""
    return "WARN %s %s: %s" % (item.get("code"), item.get("where"), item.get("msg"))


def emit_via(payload, as_json, human_lines) -> None:
    """传话筒壳（主群模式·回调全权排版直接打印·无 return）。

    json → 单行回执；人读 → 回调自理。与 emit（lib 汇总模式·human_lines_fn 只供附加行）
    语义并列：谁拼违规/警告行由调用形态决定，勿混用（组7 裁定①·2026-10-16）。
    """
    if as_json:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        human_lines(payload)


def _summary_line(result) -> str:
    n = len(result.get("violations") or [])
    m = len(result.get("warnings") or [])
    k = len(result.get("known") or [])
    if result.get("ok"):
        base = "diyc %s：通过" % result.get("command", "?")
    else:
        base = "diyc %s：%d 项违规（exit 1）" % (result.get("command", "?"), n)
    if k:
        base += "，%d 项已知遗留（baseline 豁免）" % k
    if m:
        base += "，%d 项警告" % m
    return base


def emit(result, as_json, human_lines_fn=None) -> int:
    """打印回执并返回 exit code（ok → 0 否则 1）。

    - as_json：单行 JSON（ensure_ascii=False）。
    - 人类态：human_lines_fn(result) 提供附加信息行（可选，如 output_dir / 层清单），
      emit 之后统一渲染违规行 `CODE where: msg`、WARN 行与汇总行。
    """
    if as_json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        lines = list(human_lines_fn(result) or []) if human_lines_fn is not None else []
        lines += ["%s %s: %s" % (x.get("code"), x.get("where"), x.get("msg"))
                  for x in result.get("violations") or []]
        lines += ["KNOWN %s %s: %s" % (x.get("code"), x.get("where"), x.get("msg"))
                  for x in result.get("known") or []]
        lines += ["WARN %s" % w for w in result.get("warnings") or []]
        lines.append(_summary_line(result))
        for line in lines:
            print(line)
    return 0 if result.get("ok") else 1


def run_tool(tool, cwd, timeout):
    """跑一条外部命令：返回 (rc, 合并输出, timed_out)；超时 rc=None。

    两个调用面共用：`diyc static` 的逐层滤网、`diyc mutate` 的沙箱执行
    （2026-09-22 从 diyc.py 提取——两处实现同一件事就是漂移的开始）。
    """
    try:
        proc = subprocess.run(tool, shell=True, cwd=cwd, timeout=timeout,
                              capture_output=True, text=True, encoding="utf-8",
                              errors="replace")
        return proc.returncode, (proc.stdout or "") + (proc.stderr or ""), False
    except subprocess.TimeoutExpired as e:
        out = ""
        for chunk in (e.stdout, e.stderr):
            if isinstance(chunk, bytes):
                out += chunk.decode("utf-8", "replace")
            elif chunk:
                out += chunk
        return None, out, True

# ---------------------------------------------------------------- baseline

BASELINE_FILE = "diyc-baseline.yaml"
# baseline 仅作用于审计命令（D2 裁定）；写回命令的违规=动作拒绝，被豁免即静默放行（高危）
AUDIT_COMMANDS = ("check", "trace", "static")


def load_baseline(output_dir, base_rel) -> tuple:
    """读 {output_dir}/diyc-baseline.yaml → (entries, invalid)。

    entries: [{"code","where","reason"}]（where 规范化正斜杠）；
    invalid: BASELINE_INVALID 违规——文件存在但损坏/形状非法/条目缺必填字段时非空，
    此时整份 baseline 不生效（绝不静默吞违规，安全方向优先）。
    文件缺失 → ([], [])。
    """
    path = os.path.join(output_dir, BASELINE_FILE)
    if not os.path.isfile(path):
        return [], []
    data, err = load_yaml_safe(path)
    if err:
        return [], [v("BASELINE_INVALID", base_rel, "baseline 文件解析失败：%s" % err)]
    if not isinstance(data, dict):
        return [], [v("BASELINE_INVALID", base_rel, "baseline 顶层不是映射")]
    entries = data.get("baseline")
    if entries is None:
        return [], []
    if not isinstance(entries, list):
        return [], [v("BASELINE_INVALID", base_rel, "baseline 形状异常（应为列表）")]
    out = []
    for i, e in enumerate(entries):
        item = "%s baseline[%d]" % (base_rel, i)
        if not isinstance(e, dict):
            return [], [v("BASELINE_INVALID", item, "条目形状异常（应为映射）")]
        code, where, reason = e.get("code"), e.get("where"), e.get("reason")
        if not (isinstance(code, str) and code.strip()):
            return [], [v("BASELINE_INVALID", item, "缺 code（必填）")]
        if not (isinstance(where, str) and where.strip()):
            return [], [v("BASELINE_INVALID", item, "缺 where（必填）")]
        if not (isinstance(reason, str) and reason.strip()):
            return [], [v("BASELINE_INVALID", item, "缺 reason（必填：写明裁定理由与日期）")]
        out.append({"code": code.strip(), "where": where.strip().replace("\\", "/"),
                    "reason": reason.strip()})
    return out, []


def _scope(where) -> str:
    """违规域 = where 首 token（文件段，如 diy-output/sprint.yaml；trace 为 file:line 形态）。"""
    return str(where).split(" ", 1)[0]


def apply_baseline(result, project_root, output_dir, allow_stale=True) -> None:
    """审计命令回执的 baseline 后处理（就地改写 result）。

    - 命中 (code, where) 精确匹配 → 移入 known（附 reason），不计违规、不影响 exit code；
    - 条目在本轮产出过同码违规的域（文件段）内仍未命中 → BASELINE_STALE
      （域匹配：避免 trace / check --type prd 等不同命令互相误报；债已还清？逼删条目）；
    - allow_stale=False（--story 任务级单点校验）→ 跳过 STALE 判定：
      缩域检查不构成该域的完整审计，未命中 ≠ 悬空（known 吸收仍生效）；
    - 文件损坏/条目非法 → BASELINE_INVALID，整份不生效（load_baseline 保证）。
    """
    base_rel = os.path.relpath(
        os.path.join(output_dir, BASELINE_FILE), project_root).replace("\\", "/")
    entries, invalid = load_baseline(output_dir, base_rel)
    violations = list(result.get("violations") or [])
    if invalid:
        result["violations"] = violations + invalid
        result["ok"] = False
        return
    if not entries:
        return
    reason_by_key = {(e["code"], e["where"]): e["reason"] for e in entries}
    known, remaining, used = [], [], set()
    for x in violations:
        key = (x.get("code"), x.get("where"))
        if key in reason_by_key:
            entry = dict(x)
            entry["reason"] = reason_by_key[key]
            known.append(entry)
            used.add(key)
        else:
            remaining.append(x)
    scopes_present = {(x.get("code"), _scope(x.get("where"))) for x in violations}
    stale = [] if not allow_stale else [
        v("BASELINE_STALE", "%s baseline[%d]" % (base_rel, i),
          "条目所在域仍有 %s 违规但本条未命中（%s %s）——债已还清？删除该条目以维持台账可信"
          % (e["code"], e["code"], e["where"]))
        for i, e in enumerate(entries)
        if (e["code"], _scope(e["where"])) in scopes_present
        and (e["code"], e["where"]) not in used]
    result["known"] = known
    counts = dict(result.get("counts") or {})
    counts["known"] = len(known)
    result["counts"] = counts
    result["violations"] = remaining + stale
    result["ok"] = (bool(result.get("ok")) or not remaining) and not stale


def baseline_add(project_root, output_dir, code, where, reason) -> tuple:
    """追加一条 known-legacy 台账条目（D3 纪律：仅用户裁定后调用）。

    返回 (entry, violations)：成功 (写入条目, [])；拒绝 (None, [违规])。
    - 必填非空（code/where/reason 均 strip）；where 反斜杠规范化（与 load_baseline 同）。
    - 条目字段 code/where/reason + on(today) + by("user")；既有条目与其余顶层键原样保留。
    - 重复 (code, where) → BASELINE_DUPLICATE——按 load_baseline 规范化语义比较
      （既有手工条目的空白/反斜杠形态同样命中，防静默重复条目）。
    - 现有文件损坏/条目非法 → BASELINE_INVALID 透传拒绝——不覆盖用户数据（先修后加）。
    - output_dir 不存在 → MISSING_FILE 拒绝（project-root/instance 指错的防呆，不代建目录）。
    """
    base_rel = os.path.relpath(
        os.path.join(output_dir, BASELINE_FILE), project_root).replace("\\", "/")
    if not os.path.isdir(output_dir):
        out_rel = os.path.relpath(output_dir, project_root).replace("\\", "/")
        return None, [v("MISSING_FILE", base_rel,
                        "output_dir 不存在（%s）——project-root/instance 是否正确？" % out_rel)]
    code = str(code).strip()
    where = str(where).strip().replace("\\", "/")
    reason = str(reason).strip()
    for value, name in ((code, "code"), (where, "where"), (reason, "reason")):
        if not value:
            return None, [v("BASELINE_INVALID", base_rel, "缺 %s（必填）" % name)]
    entries, invalid = load_baseline(output_dir, base_rel)
    if invalid:
        return None, invalid
    path = os.path.join(output_dir, BASELINE_FILE)
    doc = load_yaml(path) if os.path.isfile(path) else {}
    if not isinstance(doc, dict):  # 防御：两次读之间文件被改坏
        doc = {}
    items = doc.get("baseline")
    items = list(items) if isinstance(items, list) else []
    if any(e["code"] == code and e["where"] == where for e in entries):
        return None, [v("BASELINE_DUPLICATE", base_rel,
                        "条目已存在（%s %s）——台账只减不增，重复录入无意义" % (code, where))]
    entry = {"code": code, "where": where, "reason": reason,
             "on": today(), "by": "user"}
    doc["baseline"] = items + [entry]
    save_yaml_atomic(path, doc)
    return entry, []
