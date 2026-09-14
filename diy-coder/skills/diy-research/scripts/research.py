# -*- coding: utf-8 -*-
"""diy-research 确定性引擎：research.yaml 结构校验 + 旧稿 ID 稳定性比对。

子命令：
  check   校验 {output_dir}/research.yaml（顶层 project + researches 集合，形状对齐
          bug-log.yaml）：schema / 枚举（dimension|status|confidence）/ RS-### ID 格式与
          唯一性 / 每条 finding 的 sources 非空且 url 为 http(s)、accessed 为 YYYY-MM-DD。
          --id RS-xxx 只校验指定记录（未命中 → UNKNOWN_ID）；--previous PATH 比对旧稿
          RS-### 集合，旧有新无 → ID_UNSTABLE（Update 防丢记录，任务书 B1 §2.2）。
          --final 附加定稿义务：zero [ASSUMPTION]、synthesis 三键非空、findings 非空、
          status 已落 final（定稿门须咬住记录状态，同 P1 样板 check_final_duties 语义）。
          exit 0 唯一放行。

分工裁定（任务书 B1 §2.2）：research 属新产物类型，不进 diyc.py check 的硬编码类型集；
本引擎沿用领域引擎形态（同 diy-checkpoint-preview/scripts/checkpoint.py 分工），契约同构：
exit 0 唯一放行 / 1 = 违规或被拒 / 2 = 用法错误（argparse）/ --json 单行回执（ensure_ascii=False）
/ violations[{code, where, msg}] + counts。违规码全部复用 batch3-contract §3 冻结集
（MISSING_FILE UNPARSABLE_YAML DUPLICATE_ID UNKNOWN_ID ENUM_INVALID EMPTY_FIELD
ASSUMPTION_PRESENT ID_UNSTABLE STATUS_MISMATCH），无新增码。

引用纪律的机制位置（源技能核心价值：每条断言带来源）：findings[].sources 为空、url 非
http(s)、accessed 非日期一律违规——来源缺失不得以「训练数据已知」补位（三份源技能
MANDATORY EXECUTION RULES 同款：NEVER generate content without web search verification）。

禁手写实例解析：引擎不做 --instance / 白名单 / 目录推导；--output-dir 必填，由调用方传入
（SKILL.md 从 diyc.py resolve 取）。产物与产物 ID 由 diy-research 会话（LLM）创作——
RS-0nn 由 LLM 铸造、本引擎只校验格式与唯一性。本引擎只读，不写任何文件。
"""
# trace: 迁移计划 §二 验收 #3（拒绝路径零产出）/#4（ID 链稳定）/#12（领域引擎接线）
import argparse
import io
import json
import os
import re
import sys

import yaml

RESEARCH_FILE = "research.yaml"

DIMENSIONS = ("market", "technical", "domain")
STATUSES = ("draft", "final")
CONFIDENCES = ("high", "medium", "low")
SYNTHESIS_KEYS = ("executive_summary", "key_points", "open_questions")

RS_RE = re.compile(r"RS-\d{3}")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
URL_RE = re.compile(r"https?://\S+")


def v(code, where, msg):
    return {"code": code, "where": where, "msg": msg}


def nonempty(value):
    return value is not None and str(value).strip() != ""


def load_yaml_safe(path):
    """读 YAML：(data, err)。文件缺失 → (None, None)；空文件 → ({}, None)；损坏 → (None, 原因)。"""
    if not os.path.isfile(path):
        return None, None
    try:
        with io.open(path, "r", encoding="utf-8") as f:
            return (yaml.safe_load(f) or {}), None
    except yaml.YAMLError as e:
        return None, str(e)
    except OSError as e:
        return None, str(e)


def display_path(path, project_root):
    """where 显示口径（对齐 diyc）：正斜杠 + 相对 project-root；越界则绝对路径。"""
    try:
        rel = os.path.relpath(path, project_root)
    except ValueError:
        rel = os.path.abspath(path)
    if rel.startswith(".."):
        return os.path.abspath(path).replace("\\", "/")
    return rel.replace("\\", "/")


def collect_strings(node):
    """递归收集映射/列表内的全部字符串（键与值）——[ASSUMPTION] 扫描用。"""
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for key, value in node.items():
            yield str(key)
            for s in collect_strings(value):
                yield s
    elif isinstance(node, list):
        for item in node:
            for s in collect_strings(item):
                yield s


def check_string_list(value, where, label):
    """非空字符串列表校验（goals / key_points / open_questions 共用）。"""
    violations = []
    if not isinstance(value, list):
        return [v("EMPTY_FIELD", where, "%s 须为列表" % label)]
    if not value:
        return [v("EMPTY_FIELD", where, "%s 为空（至少 1 条）" % label)]
    for i, item in enumerate(value):
        if not nonempty(item):
            violations.append(v("EMPTY_FIELD", "%s[%d]" % (where, i),
                                "%s 条目为空" % label))
    return violations


# trace: 源技能引用纪律（每条断言带来源）——sources 非空 + url http(s) + accessed 日期
def check_finding(finding, where):
    violations = []
    if not isinstance(finding, dict):
        return [v("EMPTY_FIELD", where, "finding 不是映射")]
    for key in ("area", "claim"):
        if not nonempty(finding.get(key)):
            violations.append(v("EMPTY_FIELD", where + "." + key, "%s 缺失或为空" % key))
    confidence = finding.get("confidence")
    if not nonempty(confidence):
        violations.append(v("EMPTY_FIELD", where + ".confidence", "confidence 缺失"))
    elif str(confidence) not in CONFIDENCES:
        violations.append(v("ENUM_INVALID", where + ".confidence",
                            "confidence 越界：%s（合法集 %s）"
                            % (confidence, "|".join(CONFIDENCES))))
    sources = finding.get("sources")
    if not isinstance(sources, list):
        violations.append(v("EMPTY_FIELD", where + ".sources",
                            "sources 缺失或不是列表（每条断言须带来源）"))
        return violations
    if not sources:
        violations.append(v("EMPTY_FIELD", where + ".sources",
                            "sources 为空（每条断言须带来源，不得留空）"))
    for i, source in enumerate(sources):
        sw = "%s.sources[%d]" % (where, i)
        if not isinstance(source, dict):
            violations.append(v("EMPTY_FIELD", sw, "source 不是映射"))
            continue
        if not nonempty(source.get("title")):
            violations.append(v("EMPTY_FIELD", sw + ".title", "title 缺失或为空"))
        url = source.get("url")
        if not nonempty(url):
            violations.append(v("EMPTY_FIELD", sw + ".url", "url 缺失（须为 http(s) 地址）"))
        elif not URL_RE.fullmatch(str(url).strip()):
            violations.append(v("ENUM_INVALID", sw + ".url",
                                "url 须为 http(s) 绝对地址，实为 %s" % url))
        accessed = source.get("accessed")
        if not nonempty(accessed):
            violations.append(v("EMPTY_FIELD", sw + ".accessed", "accessed 缺失"))
        elif not DATE_RE.fullmatch(str(accessed)):
            violations.append(v("ENUM_INVALID", sw + ".accessed",
                                "accessed 须为 YYYY-MM-DD，实为 %s" % accessed))
    return violations


def check_synthesis(synthesis, where, final):
    """synthesis 三键：起草期只查类型，--final 要求三键非空（executive_summary 字符串；
    key_points / open_questions 非空列表——源技能的综合步必带结论、要点与研究局限）。"""
    if synthesis is None:
        if final:
            return [v("EMPTY_FIELD", where, "--final 要求 synthesis 三键非空")]
        return []
    if not isinstance(synthesis, dict):
        return [v("EMPTY_FIELD", where, "synthesis 不是映射")]
    violations = []
    for key in SYNTHESIS_KEYS:
        value = synthesis.get(key)
        sw = "%s.%s" % (where, key)
        if value is None:
            if final:
                violations.append(v("EMPTY_FIELD", sw, "--final 要求 %s 非空" % key))
            continue
        if key == "executive_summary":
            if not isinstance(value, str) or not nonempty(value):
                violations.append(v("EMPTY_FIELD", sw, "executive_summary 须为非空字符串"))
        else:
            violations += check_string_list(value, sw, key)
    return violations


def check_record(index, record, final, where_base):
    violations = []
    where = "%s.researches[%d]" % (where_base, index)
    if not isinstance(record, dict):
        return [v("EMPTY_FIELD", where, "记录不是映射")]

    rid = record.get("id")
    if not nonempty(rid):
        violations.append(v("EMPTY_FIELD", where + ".id", "id 缺失"))
    elif not RS_RE.fullmatch(str(rid)):
        violations.append(v("ENUM_INVALID", where + ".id",
                            "id 须为 RS-0nn（三位零填充），实为 %s" % rid))

    dimension = record.get("dimension")
    if not nonempty(dimension):
        violations.append(v("EMPTY_FIELD", where + ".dimension", "dimension 缺失"))
    elif str(dimension) not in DIMENSIONS:
        violations.append(v("ENUM_INVALID", where + ".dimension",
                            "dimension 越界：%s（合法集 %s）"
                            % (dimension, "|".join(DIMENSIONS))))

    for key in ("topic", "scope"):
        if not nonempty(record.get(key)):
            violations.append(v("EMPTY_FIELD", where + "." + key, "%s 缺失或为空" % key))

    violations += check_string_list(record.get("goals"), where + ".goals", "goals")

    date = record.get("date")
    if not nonempty(date):
        violations.append(v("EMPTY_FIELD", where + ".date", "date 缺失"))
    elif not DATE_RE.fullmatch(str(date)):
        violations.append(v("ENUM_INVALID", where + ".date",
                            "date 须为 YYYY-MM-DD，实为 %s" % date))

    status = record.get("status")
    if not nonempty(status):
        violations.append(v("EMPTY_FIELD", where + ".status", "status 缺失"))
    elif str(status) not in STATUSES:
        violations.append(v("ENUM_INVALID", where + ".status",
                            "status 越界：%s（合法集 %s）"
                            % (status, "|".join(STATUSES))))

    findings = record.get("findings")
    if findings is None:
        if final:
            violations.append(v("EMPTY_FIELD", where + ".findings",
                                "--final 要求 findings 非空（至少 1 条带来源的断言）"))
    elif not isinstance(findings, list):
        violations.append(v("EMPTY_FIELD", where + ".findings", "findings 不是列表"))
    else:
        if final and not findings:
            violations.append(v("EMPTY_FIELD", where + ".findings",
                                "--final 要求 findings 非空（至少 1 条带来源的断言）"))
        for i, finding in enumerate(findings):
            violations += check_finding(finding, "%s.findings[%d]" % (where, i))

    violations += check_synthesis(record.get("synthesis"), where + ".synthesis", final)

    if final:
        if nonempty(status) and str(status) != "final":
            violations.append(v("STATUS_MISMATCH", where + ".status",
                                "记录未定稿（status: %s）；--final 要求 status: final" % status))
        if any("[ASSUMPTION]" in s for s in collect_strings(record)):
            violations.append(v("ASSUMPTION_PRESENT", where,
                                "--final 要求零 [ASSUMPTION]；未决假设须落为 open_questions 后再定稿"))
    return violations


def count_by(records, key):
    counts = {}
    for record in records:
        if not isinstance(record, dict):
            continue
        value = record.get(key)
        if nonempty(value):
            counts[str(value)] = counts.get(str(value), 0) + 1
    return counts


def count_items(records, key):
    total = 0
    for record in records:
        if not isinstance(record, dict):
            continue
        items = record.get(key)
        if isinstance(items, list):
            total += len(items)
    return total


def count_sources(records):
    total = 0
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("findings"), list):
            continue
        for finding in record["findings"]:
            if isinstance(finding, dict) and isinstance(finding.get("sources"), list):
                total += len(finding["sources"])
    return total


def record_ids(records):
    return [str(r["id"]) for r in records
            if isinstance(r, dict) and nonempty(r.get("id"))]


def check_previous(path, current_ids, project_root):
    """旧稿 RS-### 集合比对：旧有新无 → ID_UNSTABLE（记录稳定不重用、不消失）。"""
    show = display_path(path, project_root)
    data, err = load_yaml_safe(path)
    if data is None and err is None:
        return [v("MISSING_FILE", show, "旧稿 %s 不存在" % show)]
    if err is not None:
        return [v("UNPARSABLE_YAML", show, "旧稿 YAML 解析失败：%s" % err)]
    if not isinstance(data, dict) or not isinstance(data.get("researches"), list):
        return []
    violations = []
    for rid in record_ids(data["researches"]):
        if rid not in current_ids:
            violations.append(v("ID_UNSTABLE", show,
                                "旧稿记录 %s 在新稿中消失（RS ID 稳定不重用；删除须落 revisions 说明）"
                                % rid))
    return violations


def cmd_check(args):
    root = os.path.abspath(args.project_root)
    out = args.output_dir
    path = os.path.join(out, RESEARCH_FILE)
    show = display_path(path, root)
    violations = []
    warnings = []
    records = []
    comparable = False

    data, err = load_yaml_safe(path)
    if data is None and err is None:
        violations.append(v("MISSING_FILE", show,
                            "%s 不存在（先完成一次研究起草）" % RESEARCH_FILE))
    elif err is not None:
        violations.append(v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err))
    elif not isinstance(data, dict):
        violations.append(v("EMPTY_FIELD", show, "顶层不是映射（须为 project + researches）"))
    else:
        comparable = True
        project = data.get("project")
        if project is not None and not isinstance(project, dict):
            violations.append(v("EMPTY_FIELD", show + " project", "project 不是映射"))
        revisions = data.get("revisions")
        if revisions is not None and not isinstance(revisions, list):
            violations.append(v("EMPTY_FIELD", show + " revisions", "revisions 不是列表"))
        raw_records = data.get("researches")
        if raw_records is None:
            violations.append(v("EMPTY_FIELD", show + " researches",
                                "researches 缺失（集合形态；无记录写空列表）"))
        elif not isinstance(raw_records, list):
            violations.append(v("EMPTY_FIELD", show + " researches", "researches 不是列表"))
        else:
            records = raw_records
            # ID 唯一性是文件级完整性：无论是否 --id 过滤都在全量上核
            seen = set()
            for i, record in enumerate(records):
                if not isinstance(record, dict) or not nonempty(record.get("id")):
                    continue
                rid = str(record["id"])
                if rid in seen:
                    violations.append(v("DUPLICATE_ID", "%s.researches[%d].id" % (show, i),
                                        "记录 ID %s 重复（RS ID 稳定不重用）" % rid))
                seen.add(rid)

    scope_indexed = [(i, r) for i, r in enumerate(records)
                     if isinstance(r, dict)
                     and (not nonempty(args.id) or str(r.get("id")) == str(args.id))]
    scope = [r for _i, r in scope_indexed]
    if nonempty(args.id) and not scope:
        violations.append(v("UNKNOWN_ID", "%s.researches" % show,
                            "记录 %s 不存在（--id 未命中）" % args.id))

    for i, record in scope_indexed:
        violations += check_record(i, record, args.final, show)
    if args.final and not scope and not violations:
        violations.append(v("EMPTY_FIELD", show + " researches",
                            "--final 要求至少 1 条记录"))

    if nonempty(args.previous) and comparable:
        # 当前稿缺失/损坏时不再叠加 ID 比对噪音（MISSING_FILE / UNPARSABLE_YAML 已定因）
        violations += check_previous(args.previous, record_ids(records), root)

    counts = {
        "researches": len(scope),
        "total_researches": len(records),
        "by_dimension": count_by(scope, "dimension"),
        "by_status": count_by(scope, "status"),
        "findings": count_items(scope, "findings"),
        "sources": count_sources(scope),
        "open_questions": sum(len(r.get("synthesis", {}).get("open_questions") or [])
                              for r in scope
                              if isinstance(r, dict)
                              and isinstance(r.get("synthesis"), dict)),
    }
    ok = not violations
    payload = {
        "ok": ok,
        "command": "check",
        "project_root": args.project_root,
        "output_dir": os.path.normpath(out).replace("\\", "/"),
        "final": args.final,
        "id": args.id,
        "violations": violations,
        "warnings": warnings,
        "counts": counts,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        if ok:
            print("PASS：%s 校验通过（researches=%d）" % (show, counts["researches"]))
        else:
            print("FAIL：")
            for item in violations:
                print("- %s %s: %s" % (item["code"], item["where"], item["msg"]))
    return 0 if ok else 1


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(
        description="diy-research 确定性引擎：research.yaml 结构校验（含旧稿 ID 稳定性比对）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("check",
                       help="校验 research.yaml（schema/枚举/来源纪律；--final 附加定稿义务）")
    c.add_argument("--project-root", default=".", help="项目根（默认 .）")
    c.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    c.add_argument("--final", action="store_true",
                   help="定稿校验：status 已落 final + findings/synthesis 非空 + 零假设")
    c.add_argument("--id", default=None, help="只校验指定记录（RS-0nn；未命中 → UNKNOWN_ID）")
    c.add_argument("--previous", default=None,
                   help="旧稿路径：比对 RS ID 集合，旧有新无 → ID_UNSTABLE（Update 防丢记录）")
    c.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    c.set_defaults(func=cmd_check)

    args = ap.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
