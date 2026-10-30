# -*- coding: utf-8 -*-
"""diy-test-gate 证据面：G-1 时效 / G-2 重复覆盖 / G-3 合规 / G-4 跨域 + diyc 委派 + mutation 面。"""
import json
import os
import subprocess
import sys
from datetime import date


sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import display_path, load_yaml_safe, nonempty, v  # noqa: E402

import gate_lib  # noqa: E402
from gate_lib import (  # noqa: E402
    COMPLIANCE_HEAD_RE, COMPLIANCE_ORDER, COMPLIANCE_RE, CROSS_DOMAIN_MARK,
    CROSS_DOMAIN_RULES, DATE_RE, DIYC_TYPES, EVIDENCE_TTL_DAYS, GATE_ROUTE,
    MUTATION_FILE, is_counted, items_of,
)

# ------------------------------------------------- G-1 证据时效 / G-2 重复覆盖

def latest_stamp(texts, today):
    """文本集里最新的 YYYY-MM-DD → (iso, 距 today 天数)；无可用时间戳 → None。"""
    found = []
    for text in texts:
        for stamp in DATE_RE.findall(str(text or "")):
            try:
                found.append(date.fromisoformat(stamp))
            except ValueError:
                continue
    if not found:
        return None
    newest = max(found)
    return newest.isoformat(), (today - newest).days


def evidence_stamp(entry, today):
    """台账条目的时效（red/green 里的时间戳，取最新）。"""
    if not isinstance(entry, dict):
        return None
    return latest_stamp([entry.get("red"), entry.get("green")], today)


def duplicate_candidates(ref, story, priority, tcs):
    """G-2 跨层重复覆盖候选：同一 technique + 同一 kill_target 在 ≥2 个 type 层级各有用例。

    口径收窄在可读数据面：只比对已验证 TC 的 `technique` / `kill_target` / `type`
    （不读源码、不做语义去重）；可接受重叠（P0 纵深防御）与跨层冗余的**判定留在
    steps/03-matrix-gaps.md**。
    """
    groups = {}
    for tc in tcs:
        if not is_counted(tc["verdict"]):
            continue
        technique = str(tc.get("technique") or "").strip()
        target = str(tc.get("kill_target") or "").strip()
        if technique and target:
            groups.setdefault((technique, target), []).append(tc)
    found = []
    for (technique, target), group in groups.items():
        levels = sorted({str(tc["type"]) for tc in group})
        if len(levels) < 2:
            continue
        found.append({
            "ref": ref, "story": story, "priority": priority,
            "technique": technique, "kill_target": target,
            "levels": levels, "tests": sorted(str(tc["id"]) for tc in group),
            "why": "同一技法 + 同一击杀目标跨 %d 个层级各有用例：P0 关键路径可视为可接受重叠"
                   "（纵深防御），非 P0 为跨层冗余（给合并建议）" % len(levels),
        })
    return found


# ------------------------------------------------- G-3 合规标准 / G-4 跨域合成

def compliance_lines(findings):
    """扫各域 `findings` 的合规行 → (parsed, problems)。

    行形态（steps/04-nfr.md）：`<标准>[@<域>]: <PASS|PARTIAL|FAIL|N/A> — <依据>`。
    parsed = {标准: {aggregates: [状态], observations: [(域, 状态)], lines: [原文]}}；
    problems = [(标准, 行原文)]——以标准名开头但形态不合的行（不计入 parsed）。
    """
    parsed, problems = {}, []
    for lines in findings.values():
        for raw in lines:
            text = str(raw or "").strip()
            match = COMPLIANCE_RE.match(text)
            if not match:
                head = COMPLIANCE_HEAD_RE.match(text)
                if head:
                    problems.append((head.group(1), text))
                continue
            standard, domain, status = match.groups()
            entry = parsed.setdefault(standard, {"aggregates": [], "observations": [],
                                                 "lines": []})
            entry["lines"].append(text)
            if domain:
                entry["observations"].append((domain, status))
            elif status not in entry["aggregates"]:
                entry["aggregates"].append(status)
    return parsed, problems


def compliance_rollup(statuses):
    """合规聚合 = FAIL > PARTIAL > PASS（全 N/A → N/A）；空集 → None。"""
    values = {str(item).strip().upper() for item in statuses if nonempty(item)}
    if not values:
        return None
    return next((state for state in COMPLIANCE_ORDER if state in values), None)


def cross_domain_hits(statuses):
    """G-4 候选：按源两条规则判域状态组合（trigger 命中的 pair 全落区间才算命中）。"""
    hits = []
    for rule in CROSS_DOMAIN_RULES:
        left, right = rule["pair"]
        if all(str(statuses.get(name) or "").upper() in rule["trigger"][name]
               for name in rule["pair"]):
            hits.append({"pair": [left, right], "impact": rule["impact"],
                         "marker": left + CROSS_DOMAIN_MARK + right,
                         "why": rule["why"]})
    return hits


# ---------------------------------------------------------------- diyc 委派


def diyc_type_check(script, project_root, type_name):
    """委派 diyc check --type T --final。返回 (回执 dict | None, warning | None)。"""
    where = "diyc.py check --type %s" % type_name
    cmd = [sys.executable, script, "check", "--type", type_name, "--final",
           "--project-root", project_root, "--json"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              encoding="utf-8", errors="replace")
    except OSError as err:
        return None, v("TOOL_ERROR", where, "diyc 子进程无法启动：%s" % err)
    if proc.returncode not in (0, 1):
        tail = " ".join((proc.stderr or proc.stdout or "").split())[-200:]
        return None, v("TOOL_ERROR", where,
                       "diyc 非预期退出码 %s（期望 0|1）：%s"
                       % (proc.returncode, tail or "无输出"))
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
        return None, v("TOOL_ERROR", where, "diyc 回执不可解析（--json 面单行 JSON 缺失）")
    return payload, None


def run_diyc_checks(project_root, out_dir):
    """跑 test-plan 型 check，合并回执。返回 (diyc 块, warnings)。"""
    warnings = []
    script = gate_lib.diyc_script_path()
    block = {"available": False, "script": display_path(script, project_root),
             "checked": [], "violations": [], "counts": {}}
    if not os.path.isfile(script):
        warnings.append(v("TOOL_MISSING", block["script"],
                          "diyc.py 缺席：跨文档核对降级，请从会话侧人工复核 TC 台账一致性"))
        return block, warnings
    block["available"] = True
    for type_name in DIYC_TYPES:
        payload, warning = diyc_type_check(script, project_root, type_name)
        if warning is not None:
            warnings.append(warning)
            continue
        block["checked"].append(type_name)
        resolved = payload.get("output_dir")
        if nonempty(resolved) and os.path.normpath(str(resolved)) \
                != os.path.normpath(out_dir):
            warnings.append(v("TOOL_ERROR", "diyc.py check --type %s" % type_name,
                              "diyc 解析到的 output_dir 与本次 --output-dir 不一致：%s"
                              % resolved))
        for item in payload.get("violations") or []:
            block["violations"].append(item)
            warnings.append(v("EVIDENCE_MISSING", item.get("where") or type_name,
                              "diyc 报上游违规，须落 gate.blockers：%s" % item.get("msg")))
        block["counts"][type_name] = payload.get("counts") or {}
    return block, warnings


# ---------------------------------------------------------------- mutation 面

def mutation_block(out, warnings, today=None):
    """mutation-report.yaml → 保守聚合面（多 run 取最小值）+ 时效面（run 日期 >7 天）。

    `score` 的量纲是**百分数整数**（0–100，e.g. 90 = 90%），与 `HARD_CRITERIA` 的
    `("变异得分", ">=90%")` 同一量纲——report 里若写小数（0.9）会被 `int()` 截成 0，
    故 `diy-augment` 的 schema 明写百分数。

    `candidates` 是全部 run 的等价体候选标识（扁平化），供 `gate_check` 把 waivers 里的
    `mutant:<id>` ref 匹配回具体 run。**裁定的落点在 waivers、不在本文件**：此处只报候选
    与保守分（未裁定的候选仍留在分母），用户裁定后才由 check 侧重算。
    """
    block = {"present": False, "source": MUTATION_FILE, "runs": 0,
             "score": None, "target": ">=90%", "equivalents": 0,
             "candidates": [], "detail": [], "critical": None}
    data, err = load_yaml_safe(os.path.join(out, MUTATION_FILE))
    if err is not None:
        warnings.append(v("UNPARSABLE_YAML", MUTATION_FILE,
                          "mutation-report.yaml 解析失败，变异得分 记 n/a：%s" % err))
        return block
    if data is None:
        warnings.append(v("MISSING_FILE", MUTATION_FILE,
                          "mutation-report.yaml 缺席（diy-augment 未跑变异）："
                          "变异得分 记 n/a + warning（日常口径；`--final` 时必须，"
                          "见 gate_check 的同码违规）"))
        return block
    runs = items_of(data, "runs")
    scores = [run.get("score") for run in runs if isinstance(run, dict)
              and isinstance(run.get("score"), (int, float))
              and not isinstance(run.get("score"), bool)]
    equivalents = sum(len(items_of(run, "equivalents")) for run in runs
                      if isinstance(run, dict))
    candidates, detail, crit_scores = [], [], []
    for run in runs:
        if not isinstance(run, dict):
            continue
        eqs = [str(e.get("mutant")).strip() for e in items_of(run, "equivalents")
               if isinstance(e, dict) and str(e.get("mutant") or "").strip()]
        candidates.extend(eqs)
        crit = run.get("critical")
        crit_score = crit.get("score") if isinstance(crit, dict) else None
        if isinstance(crit_score, (int, float)) and not isinstance(crit_score, bool):
            crit_scores.append(crit_score)
        detail.append({"killed": run.get("killed"), "total": run.get("total"),
                       "equivalents": eqs, "score": run.get("score")})
    block.update({"present": True, "runs": len(runs),
                  "score": int(min(scores)) if scores else None,
                  "equivalents": equivalents, "candidates": candidates,
                  "detail": detail,
                  "critical": {"score": int(min(crit_scores)), "target": "100%"}
                              if crit_scores else None})
    if runs and len(scores) != len(runs):
        warnings.append(v("EMPTY_FIELD", MUTATION_FILE + " runs[].score",
                          "部分 run 缺 score：聚合只取可读项"))
    today = today or date.today()
    for run in runs:
        stamp = latest_stamp([run.get("date")], today) if isinstance(run, dict) else None
        if stamp and stamp[1] > EVIDENCE_TTL_DAYS:
            warnings.append(v("EVIDENCE_STALE", MUTATION_FILE + " runs[].date",
                              "run %s 的变异结果 %s（%d 天前 > %d 天）：证据时效过期——重跑"
                              "刷新，或经用户确认后沿用并在 gate.basis 注明"
                              % (run.get("task") or run.get("date"), stamp[0],
                                 stamp[1], EVIDENCE_TTL_DAYS)))
    return block
