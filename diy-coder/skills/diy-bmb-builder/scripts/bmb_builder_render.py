# -*- coding: utf-8 -*-
"""bmb-builder 报告渲染：findings.json → md/html（禁手写 HTML）。"""

import html as html_mod
import json
import os
import sys

from bmb_builder_lib import (FINDINGS_FILE, GRADES, REPORT_HTML, REPORT_MD,
                             base_payload, finish, human_lines, read_text,
                             resolve_arg_path)
from diyc_lib import display_path, nonempty, v, write_atomic

# ---------------------------------------------------------------- render（报告渲染）

# trace: diy-bmb-builder findings 装载与形状校验（缺 schema_version/subject/findings → 拒绝渲染）
def load_findings(path, show):
    if not os.path.isfile(path):
        return None, [v("MISSING_FILE", show, "findings.json 不存在（先合成五透镜结果）")]
    text, err = read_text(path, show)
    if err is not None:
        return None, [err]
    try:
        data = json.loads(text)
    except ValueError as e:
        return None, [v("UNPARSABLE_YAML", show, "findings.json 解析失败：%s" % e)]
    if not isinstance(data, dict):
        return None, [v("EMPTY_FIELD", show, "findings.json 顶层不是对象")]
    violations = []
    if data.get("schema_version") != 2:
        violations.append(v("ENUM_INVALID", show + " schema_version",
                            "schema_version 须为 2（与既有 12 份报告可比）"))
    grade = data.get("grade")
    if grade is not None and str(grade) not in GRADES:
        violations.append(v("ENUM_INVALID", show + " grade",
                            "grade 越界：%r（合法集 %s，小写）" % (grade, "|".join(GRADES))))
    subject = data.get("subject")
    if not nonempty(subject) or str(subject).strip().lower() in ("subject", "<subject>"):
        violations.append(v("EMPTY_FIELD", show + " subject",
                            "subject 缺失或仍是占位（拒绝渲染占位报告）"))
    if not isinstance(data.get("findings"), list):
        violations.append(v("EMPTY_FIELD", show + " findings",
                            "findings 须为列表（无发现写空列表）"))
    if violations:
        return None, violations
    return data, []


# trace: diy-bmb-builder severity 计数由脚本派生（报告里不设 counts 字段）
def severity_counts(findings):
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for item in findings:
        if isinstance(item, dict):
            severity = str(item.get("severity", "")).lower()
            if severity in counts:
                counts[severity] += 1
    return counts


# trace: diy-bmb-builder 报告 markdown 生成（Grade / verdict / 主题 / 强项 / 建议 / 逐条 findings）
def render_md(data):
    counts = severity_counts(data["findings"])
    out = ["# Analysis Report: %s" % data["subject"], "",
           "Generated: %s · Schema: 2" % data.get("generated", ""), "",
           "**Grade: %s**" % (data.get("grade") or "—"), "",
           "> %s" % data.get("verdict", ""), "",
           data.get("summary", ""), "",
           "| Severity | Count |", "| --- | --- |"]
    for name in ("critical", "high", "medium", "low"):
        out.append("| %s | %d |" % (name.capitalize(), counts[name]))
    themes = data.get("themes") or []
    if themes:
        out += ["", "## Themes"]
        for i, theme in enumerate(themes, 1):
            out += ["", "### %d. %s" % (i, theme.get("title", "")),
                    "", "- Root cause: %s" % theme.get("root_cause", ""),
                    "- Fix: %s" % theme.get("action", "")]
            if theme.get("finding_ids"):
                out.append("- Findings: %s" % "、".join("`%s`" % i for i in theme["finding_ids"]))
    if data.get("strengths"):
        out += ["", "## Strengths"] + ["- %s" % item for item in data["strengths"]]
    if data.get("recommendations"):
        out += ["", "## Recommendations"]
        for rec in data["recommendations"]:
            out.append("%s. %s（resolves: %s）"
                       % (rec.get("rank", "-"), rec.get("action", ""),
                          "、".join("`%s`" % i for i in (rec.get("resolves") or []))))
    out += ["", "## Findings"]
    for item in data["findings"]:
        if not isinstance(item, dict):
            continue
        out += ["", "### `%s` %s" % (item.get("id", ""), item.get("title", "")),
                "", "- lens: %s ｜ severity: %s ｜ location: %s"
                % (item.get("lens", ""), item.get("severity", ""), item.get("location", "")),
                "- evidence: %s" % item.get("evidence", ""),
                "- recommendation: %s" % item.get("recommendation", "")]
        for extra in ("proposed_smallest", "predicted_delta"):
            if item.get(extra):
                out.append("- %s: %s" % (extra, item[extra]))
    return "\n".join(out).rstrip("\n") + "\n"


# trace: diy-bmb-builder 报告 HTML 生成（自包含、无外部资源、值一律转义）
def render_html(data):
    counts = severity_counts(data["findings"])
    esc = html_mod.escape
    rows = "".join("<tr><td>%s</td><td>%d</td></tr>" % (name, counts[name])
                   for name in ("critical", "high", "medium", "low"))
    themes = ""
    for theme in data.get("themes") or []:
        themes += ("<section class='theme'><h3>%s</h3><p><b>Root cause:</b> %s</p>"
                   "<p><b>Fix:</b> %s</p><p class='ids'>%s</p></section>"
                   % (esc(str(theme.get("title", ""))), esc(str(theme.get("root_cause", ""))),
                      esc(str(theme.get("action", ""))),
                      esc("、".join(str(i) for i in (theme.get("finding_ids") or [])))))
    findings = ""
    for item in data["findings"]:
        if not isinstance(item, dict):
            continue
        extra = ""
        for key in ("proposed_smallest", "predicted_delta"):
            if item.get(key):
                extra += "<p><b>%s:</b> %s</p>" % (esc(key), esc(str(item[key])))
        findings += ("<article class='finding sev-%s'><h3><code>%s</code> %s</h3>"
                     "<p class='meta'>lens %s ｜ %s ｜ %s</p><p>%s</p><p><b>建议：</b>%s</p>%s</article>"
                     % (esc(str(item.get("severity", ""))), esc(str(item.get("id", ""))),
                        esc(str(item.get("title", ""))), esc(str(item.get("lens", ""))),
                        esc(str(item.get("severity", ""))), esc(str(item.get("location", ""))),
                        esc(str(item.get("evidence", ""))),
                        esc(str(item.get("recommendation", ""))), extra))
    strengths = "".join("<li>%s</li>" % esc(str(item))
                        for item in (data.get("strengths") or []))
    recons = "".join("<li>%s <span class='ids'>%s</span></li>"
                     % (esc(str(rec.get("action", ""))),
                        esc("、".join(str(i) for i in (rec.get("resolves") or []))))
                     for rec in (data.get("recommendations") or []))
    return ("<!DOCTYPE html>\n<html lang=\"zh-CN\"><head><meta charset=\"utf-8\">"
            "<title>Analysis Report: %s</title><style>"
            "body{font-family:system-ui,sans-serif;max-width:900px;margin:2rem auto;padding:0 1rem;"
            "line-height:1.6;color:#1a1a1a}h1{font-size:1.5rem}.grade{display:inline-block;"
            "padding:.2rem .7rem;border-radius:4px;background:#eef;font-weight:700}"
            "blockquote{border-left:3px solid #ccd;margin:1rem 0;padding:.2rem 1rem;color:#334}"
            "table{border-collapse:collapse}td,th{border:1px solid #dde;padding:.2rem .8rem}"
            ".finding{border:1px solid #e5e5ef;border-radius:6px;padding:.6rem 1rem;margin:.7rem 0}"
            ".finding h3{font-size:1rem;margin:.2rem 0}.meta,.ids{color:#667;font-size:.85rem}"
            "code{background:#f4f4f8;padding:0 .25rem}</style></head><body>"
            "<h1>Analysis Report: %s</h1><p class='meta'>Generated: %s · Schema: 2</p>"
            "<p class='grade'>Grade: %s</p><blockquote>%s</blockquote><p>%s</p>"
            "<h2>Severity</h2><table><tr><th>Severity</th><th>Count</th></tr>%s</table>"
            "<h2>Themes</h2>%s<h2>Strengths</h2><ul>%s</ul>"
            "<h2>Recommendations</h2><ol>%s</ol><h2>Findings</h2>%s</body></html>\n"
            % (esc(str(data["subject"])), esc(str(data["subject"])),
               esc(str(data.get("generated", ""))), esc(str(data.get("grade") or "—")),
               esc(str(data.get("verdict", ""))), esc(str(data.get("summary", ""))),
               rows, themes or "<p>无</p>", strengths or "<li>无</li>",
               recons or "<li>无</li>", findings or "<p>无发现——五透镜全过。</p>"))


# trace: diy-bmb-builder render 子命令（脚本渲染 md/html，禁手写 HTML）
def cmd_render(args):
    root = os.path.abspath(args.project_root)
    payload = base_payload("render", args, {"rendered": 0})
    run_dir, dir_err = resolve_arg_path(args.dir, root)
    if dir_err is not None:
        payload["violations"].append(dir_err)
        return finish(payload, args, human_lines)
    show = display_path(run_dir, root)
    if not os.path.isdir(run_dir):
        payload["violations"].append(v("MISSING_FILE", show, "运行目录不存在"))
        return finish(payload, args, human_lines)
    findings_path = os.path.join(run_dir, FINDINGS_FILE)
    data, violations = load_findings(findings_path, display_path(findings_path, root))
    if violations:
        payload["violations"] += violations
        return finish(payload, args, human_lines)
    try:
        write_atomic(os.path.join(run_dir, REPORT_MD), render_md(data))
        write_atomic(os.path.join(run_dir, REPORT_HTML), render_html(data))
    except OSError as e:
        sys.stderr.write("诊断：报告渲染失败 %s：%s\n" % (show, e))
        payload["violations"].append(v("FILE_CONFLICT", show, "渲染失败：%s" % e))
        return finish(payload, args, human_lines)
    payload["rendered"] = [("%s/%s" % (show, REPORT_MD)), ("%s/%s" % (show, REPORT_HTML))]
    payload["counts"] = {"rendered": 2, "findings": len(data["findings"]),
                         "severity": severity_counts(data["findings"])}
    return finish(payload, args, human_render)


# trace: diy-bmb-builder render 人读态（落了两件 + 计数；不报路径等待查看、不开浏览器）
def human_render(payload):
    human_lines(payload)
    if payload["ok"]:
        for item in payload["rendered"]:
            print("- %s" % item)
