# -*- coding: utf-8 -*-
"""diy-retrospective 确定性引擎：epic 收尾回顾的门禁 + 指标机械采集 + retrospective.yaml 校验。

子命令：
  collect  --epic <E-x|N>  epic 收尾回顾的确定性部分（只读，绝不写文件）：
             1 门禁（源技能 step-1「Epic Discovery」的门禁化）：stories.yaml / epics.yaml
               在场且 project.status 为 final；目标 epic 在 epics.yaml 中可解析；该 epic
               至少 1 个 done story。不满足 → 零产出 exit 1 + 结构化拒绝回执
               （violations 带码 + gate.route 给路由）。epic 未收尾（有 story 非 done）
               不是拒绝：出 PENDING_DECISION 警告，partial 分流交会话（源 step-1 三分支：
               完成后再来 / partial 回顾 / 刷新 sprint）。
             2 指标机械采集（替换源技能 step-2「人工通读 story md 数数」的确定性下沉）：
               stories 完成度、sprint loop.rounds 合计、blocked / augment: fail 明细、
               bug-log 按 story→epic 归属的三分类计数、test-plan 对该 epic AC 的覆盖统计。
             3 前一份 retro 的 action_items 回带（源 step-3 的承诺跟踪输入，供 prev_followup）；
               下一 epic 存在性与共享 FR（源 step-4 预览的机械钩子）。
  check    [--final] [--id RT-xxx]  校验 {output_dir}/retrospective.yaml（RT-### 集合，形状对齐
           bug-log.yaml）：schema / 枚举 / epic 与 patterns evidence 的引用解析（S-x / BUG-0xx）/
           action item 完整性（action+owner+done_when）/ prev_followup 指向同文件既往记录 /
           next_epic.exists=true 时 id 解析 / ID 唯一；--final 附加：status 已落 final、
           零 [ASSUMPTION]、metrics 与集合真值一致（SET_MISMATCH，与 collect 同一函数互证）、
           readiness 五键非空、action_items 非空。exit 0 唯一放行。

分工裁定（任务书 §2.2/§2.3/§4）：retrospective 属新产物类型，不进 diyc.py check 的硬编码类型集；
本引擎契约同构（exit 0 唯一放行 / --json 单行回执 / violations[{code, where, msg}] + counts；
where 正斜杠、相对 project-root；--output-dir 必填，实例解析由 SKILL.md 委托 diyc.py resolve）；
--previous 不实现——记录按 epic 追加、同 epic 重跑原位更新，无 ID 集合收缩风险（报告记账）。
违规码复用 batch3-contract §3 冻结集，不新增。diy 改造要点：输入面是结构化产物
（sprint.yaml 的 note/evidence/loop/review.findings + bug-log.yaml + test-plan.yaml + stories.yaml），
不是源技能的 story md 人工通读；指标由本引擎机械采集，会话不人工数数。
"""

# trace: B2 diy-retrospective 验收 #3（前置门禁零产出）/#4（ID 链接入）/#7（冒烟门禁路径）/#12（语言绑定与写权边界）
import argparse
import io
import json
import os
import re
import sys

import yaml

RETRO_FILE = "retrospective.yaml"
STORIES_FILE = "stories.yaml"
EPICS_FILE = "epics.yaml"
SPRINT_FILE = "sprint.yaml"
TEST_PLAN_FILE = "test-plan.yaml"
BUG_LOG_FILE = "bug-log.yaml"

# 门禁件（文件名 → 是否要求 project.status: final）
GATE_FILES = ((STORIES_FILE, True), (EPICS_FILE, True))
ROUTE_BY_FILE = {STORIES_FILE: "diy-epics-stories", EPICS_FILE: "diy-epics-stories"}

RECORD_STATUSES = ("draft", "final")
ACTION_CATEGORIES = ("process", "technical", "docs", "team")
PREP_CLASSES = ("critical", "parallel", "nice")
FOLLOWUP_STATUSES = ("done", "partial", "missed")
READINESS_KEYS = ("testing", "deployment", "acceptance", "tech_health", "blockers")
METRIC_INT_KEYS = ("stories_total", "stories_done", "rounds_total", "blocked_count",
                   "augment_fail")
BUG_CLASSES = ("functional", "non-functional")
TEXT_LIST_KEYS = ("wins", "challenges", "insights")

EPIC_RE = re.compile(r"E-\d+")
RT_RE = re.compile(r"RT-\d{3}")
AI_RE = re.compile(r"AI-\d{3}")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
STORY_TOKEN_RE = re.compile(r"S-\d+")
BUG_TOKEN_RE = re.compile(r"BUG-\d{3}")

PATTERN_MIN_COUNT = 2  # 源 step-2：跨 story 才成模式（≥2 处证据）


def v(code, where, msg):
    return {"code": code, "where": where, "msg": msg}


def nonempty(value):
    return value is not None and str(value).strip() != ""


def items(doc, key):
    """取顶层列表键；缺失/非列表 → []。"""
    if not isinstance(doc, dict):
        return []
    value = doc.get(key)
    return value if isinstance(value, list) else []


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


def id_sort(ids):
    """数字感知排序（S-2 < S-10），对齐 diyc_lib.id_sort。"""
    def key(value):
        return tuple((0, int(p)) if p.isdigit() else (1, p)
                     for p in re.split(r"[-.]", str(value)))
    return sorted(ids, key=key)


def is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


# ---------------------------------------------------------------- 文档装载

def load_docs(out_dir):
    """一次性装载六份文档：{文件名: {"present", "data", "err"}}（只读，不落盘）。"""
    docs = {}
    for filename in (STORIES_FILE, EPICS_FILE, SPRINT_FILE, TEST_PLAN_FILE,
                     BUG_LOG_FILE, RETRO_FILE):
        data, err = load_yaml_safe(os.path.join(out_dir, filename))
        docs[filename] = {"present": data is not None or err is not None,
                          "data": data, "err": err}
    return docs


def doc_of(docs, filename):
    entry = docs.get(filename) or {}
    return entry.get("data") if entry.get("err") is None else None


def doc_summaries(docs, project_root, out_dir):
    """docs 回执键（短名 = 文件名去 .yaml）：在场 / 可解析 / project.status。"""
    summaries = {}
    for filename, entry in docs.items():
        status = None
        data = entry.get("data")
        if isinstance(data, dict) and isinstance(data.get("project"), dict):
            status = data["project"].get("status")
        summaries[filename[:-len(".yaml")]] = {
            "file": filename, "found": entry["present"], "parsable": entry["err"] is None,
            "status": status,
            "path": display_path(os.path.join(out_dir, filename), project_root)}
    return summaries


def normalize_epic(value):
    """epic 参数归一：接受 `E-3` 与 `3`；其余 → None。"""
    raw = str(value).strip()
    if EPIC_RE.fullmatch(raw):
        return raw
    if raw.isdigit():
        return "E-%d" % int(raw)
    return None


def epic_number(epic):
    m = re.search(r"\d+", str(epic))
    return int(m.group(0)) if m else -1


def epic_entries(docs):
    return [e for e in items(doc_of(docs, EPICS_FILE), "epics") if isinstance(e, dict)]


def epic_ids(docs):
    return {str(e["id"]) for e in epic_entries(docs) if nonempty(e.get("id"))}


def story_entries(docs):
    return [s for s in items(doc_of(docs, STORIES_FILE), "stories") if isinstance(s, dict)]


def story_ids_of_epic(epic, docs):
    return [str(s["id"]) for s in story_entries(docs)
            if str(s.get("epic")) == epic and nonempty(s.get("id"))]


def story_status_map(docs):
    return {str(s["id"]): s.get("status") for s in story_entries(docs)
            if nonempty(s.get("id"))}


def task_entries(docs):
    return [t for t in items(doc_of(docs, SPRINT_FILE), "tasks") if isinstance(t, dict)]


def ac_refs_of(story, key="refs"):
    """story 的 AC refs 全集（引用式：只取 ID，不复制文本）。"""
    refs = []
    for ac in items(story, "acceptance_criteria"):
        if isinstance(ac, dict):
            refs += [str(r) for r in items(ac, key) if nonempty(r)]
    return refs


# ---------------------------------------------------------------- 机械采集

def epic_stories_block(epic, docs):
    """该 epic 的 story 完成度块（源 step-1 完成度校验的机械面）。"""
    status = story_status_map(docs)
    ids = story_ids_of_epic(epic, docs)
    done = [i for i in ids if status.get(i) == "done"]
    pending = [{"id": i, "status": status.get(i)} for i in ids if status.get(i) != "done"]
    return {"total": len(ids), "done": len(done), "ids": ids, "done_ids": done,
            "pending": pending}


def epic_tasks(epic, docs):
    ids = set(story_ids_of_epic(epic, docs))
    return [t for t in task_entries(docs) if str(t.get("story")) in ids]


def sum_rounds(tasks):
    total = 0
    for task in tasks:
        loop = task.get("loop")
        if isinstance(loop, dict) and is_int(loop.get("rounds")) and loop["rounds"] > 0:
            total += loop["rounds"]
    return total


def epic_bugs(epic, docs):
    """bug-log 中 story 归属该 epic 的缺陷（story 值可为 `S-7/S-9` 复合形态 → 取 token）。"""
    ids = set(story_ids_of_epic(epic, docs))
    out = []
    for bug in items(doc_of(docs, BUG_LOG_FILE), "bugs"):
        if not isinstance(bug, dict):
            continue
        tokens = STORY_TOKEN_RE.findall(str(bug.get("story") or ""))
        if not tokens or not any(tok in ids for tok in tokens):
            continue
        out.append({"id": bug.get("id"), "class": bug.get("class"),
                    "subclass": bug.get("subclass"), "type": bug.get("type"),
                    "story": bug.get("story"), "symptom": bug.get("symptom")})
    return out


def bug_counts(bugs):
    counts = {name: 0 for name in BUG_CLASSES}
    for bug in bugs:
        name = str(bug.get("class"))
        if name in counts:
            counts[name] += 1
    return counts


def epic_coverage(epic, docs):
    """test-plan 对该 epic AC 的覆盖统计（covered = 有 ≥1 条 TC 绑定）。"""
    acs = []
    for story in story_entries(docs):
        if str(story.get("epic")) != epic:
            continue
        for ac in items(story, "acceptance_criteria"):
            if isinstance(ac, dict) and nonempty(ac.get("id")):
                acs.append(str(ac["id"]))
    ac_set = set(acs)
    tcs = [tc for tc in items(doc_of(docs, TEST_PLAN_FILE), "test_cases")
           if isinstance(tc, dict) and str(tc.get("ac")) in ac_set]
    covered = sorted({str(tc.get("ac")) for tc in tcs})
    gaps = id_sort([ac for ac in ac_set if ac not in set(covered)])
    return {"acs": len(ac_set), "covered": len(covered), "gaps": gaps, "tcs": len(tcs)}


def collect_metrics(epic, docs):
    """指标单一计算源——collect 与 check --final 共用（口径互证）。"""
    block = epic_stories_block(epic, docs)
    tasks = epic_tasks(epic, docs)
    bugs = epic_bugs(epic, docs)
    return {
        "stories_total": block["total"],
        "stories_done": block["done"],
        "rounds_total": sum_rounds(tasks),
        "blocked_count": len([t for t in tasks if t.get("status") == "blocked"]),
        "augment_fail": len([t for t in tasks if t.get("augment") == "fail"]),
        "bugs": bug_counts(bugs),
    }


def prev_actions(epic, docs):
    """前一份 retro 的 action_items 回带（源 step-3 承诺跟踪的输入）。"""
    target = epic_number(epic)
    earlier = [e for e in epic_entries(docs)
               if nonempty(e.get("id")) and epic_number(e["id"]) < target]
    if not earlier:
        return True, []
    prev = max(earlier, key=lambda e: epic_number(e["id"]))
    prev_id = str(prev["id"])
    record = None
    for rec in items(doc_of(docs, RETRO_FILE), "retros"):
        if isinstance(rec, dict) and str(rec.get("epic")) == prev_id:
            record = rec   # 同 epic 多份取最后一份（追加式，最新在后）
    if record is None:
        return True, []
    out = []
    for action in items(record, "action_items"):
        if not isinstance(action, dict):
            continue
        out.append({"retro": record.get("id"), "id": action.get("id"),
                    "action": action.get("action"), "owner": action.get("owner"),
                    "done_when": action.get("done_when"),
                    "category": action.get("category")})
    return False, out


def next_epic_info(epic, docs):
    """下一 epic 存在性 + 与当前 epic 的共享 FR（源 step-4 预览的机械钩子）。"""
    target = epic_number(epic)
    later = [e for e in epic_entries(docs)
             if nonempty(e.get("id")) and epic_number(e["id"]) > target]
    if not later:
        return {"id": None, "exists": False, "title": None, "stories": [], "shared_frs": []}
    nxt = min(later, key=lambda e: epic_number(e["id"]))
    nxt_id = str(nxt["id"])
    current_frs = set()
    for story in story_entries(docs):
        if str(story.get("epic")) == epic:
            current_frs.update(ac_refs_of(story))
    next_frs = set()
    for story in story_entries(docs):
        if str(story.get("epic")) == nxt_id:
            next_frs.update(ac_refs_of(story))
    nxt_stories = [s for s in story_entries(docs) if str(s.get("epic")) == nxt_id]
    return {"id": nxt_id, "exists": True, "title": nxt.get("title"),
            "stories": [str(s.get("id")) for s in nxt_stories],
            "shared_frs": id_sort(current_frs & next_frs)}


# ---------------------------------------------------------------- 门禁

def gate_check(epic, docs, out_dir, project_root):
    """门禁：上游两件套在场且定稿 + epic 可解析 + 至少 1 个 done story。
    返回 (passed, violations, route)。"""
    violations = []
    skills = []
    for filename, must_final in GATE_FILES:
        entry = docs[filename]
        show = display_path(os.path.join(out_dir, filename), project_root)
        if not entry["present"]:
            violations.append(v("MISSING_FILE", show,
                                "%s 不存在；先跑 %s 产出上游文档"
                                % (filename, ROUTE_BY_FILE[filename])))
            skills.append(ROUTE_BY_FILE[filename])
            continue
        if entry["err"] is not None:
            violations.append(v("UNPARSABLE_YAML", show,
                                "YAML 解析失败：%s" % entry["err"]))
            continue
        data = entry["data"]
        project = data.get("project") if isinstance(data, dict) else None
        status = project.get("status") if isinstance(project, dict) else None
        if must_final and status != "final":
            violations.append(v("STATUS_MISMATCH", show + " project.status",
                                "%s 的 project.status 须为 final（实为 %s）；先跑 %s 定稿"
                                % (filename, status if nonempty(status) else "未声明",
                                   ROUTE_BY_FILE[filename])))
            skills.append(ROUTE_BY_FILE[filename])

    known = epic_ids(docs)
    if not known:
        if not [x for x in violations if EPICS_FILE in x["where"]]:
            violations.append(v("UNKNOWN_ID", display_path(
                os.path.join(out_dir, EPICS_FILE), project_root) + " epics",
                "epics.yaml 无可解析的 epic 条目，无法定位目标 %s" % epic))
            skills.append("diy-epics-stories")
    elif epic not in known:
        violations.append(v("UNKNOWN_ID",
                            display_path(os.path.join(out_dir, EPICS_FILE), project_root)
                            + " epics",
                            "目标 epic %s 不在 epics.yaml（已知 %s）"
                            % (epic, "、".join(id_sort(known)))))
        skills.append("diy-epics-stories")
    else:
        block = epic_stories_block(epic, docs)
        if block["total"] == 0:
            violations.append(v("EMPTY_FIELD",
                                display_path(os.path.join(out_dir, STORIES_FILE),
                                             project_root) + " stories[epic=%s]" % epic,
                                "该 epic 下没有 story，无可回顾"))
            skills.append("diy-epics-stories")
        elif block["done"] == 0:
            violations.append(v("EMPTY_FIELD",
                                display_path(os.path.join(out_dir, STORIES_FILE),
                                             project_root) + " stories[epic=%s].status" % epic,
                                "该 epic 没有 done story（回顾针对已交付工作）"))
            skills.append("diy-epics-stories")

    route = None
    if violations:
        unique = list(dict.fromkeys(skills))
        route = ("先跑 %s 补齐并定稿上游文档，再重跑本技能" % " / ".join(unique)
                 if unique else "先修复上游文档（解析失败或状态未定稿），再重跑本技能")
    return (not violations), violations, route


# ---------------------------------------------------------------- collect

def empty_payload(args, epic):
    out = os.path.normpath(os.path.abspath(args.output_dir)).replace("\\", "/")
    return {
        "ok": False,
        "command": "collect",
        "project_root": args.project_root,
        "output_dir": out,
        "epic": epic,
        "gate": {"passed": False, "files": {}, "route": None},
        "stories": None,
        "metrics": None,
        "bugs": [],
        "coverage": None,
        "prev_actions": [],
        "first_retro": True,
        "next_epic": None,
        "docs": {},
        "violations": [],
        "warnings": [],
        "counts": {},
    }


def collect_warnings(epic, docs, out_dir, project_root):
    """可选源缺席 / epic 未收尾 → 结构化 warning（不拒）。"""
    warnings = []
    for filename, why in ((SPRINT_FILE, "rounds / blocked / augment 统计退化为 0"),
                          (BUG_LOG_FILE, "缺陷按 epic 归属的统计退化为空"),
                          (TEST_PLAN_FILE, "AC 覆盖统计退化为空")):
        entry = docs[filename]
        show = display_path(os.path.join(out_dir, filename), project_root)
        if not entry["present"]:
            warnings.append(v("MISSING_FILE", show,
                              "%s 未找到：%s（不阻断回顾）" % (filename, why)))
        elif entry["err"] is not None:
            warnings.append(v("UNPARSABLE_YAML", show,
                              "%s 不可解析：%s" % (filename, entry["err"])))
    if docs[RETRO_FILE]["err"] is not None:
        warnings.append(v("UNPARSABLE_YAML",
                          display_path(os.path.join(out_dir, RETRO_FILE), project_root),
                          "retrospective.yaml 不可解析：上一份 retro 的承诺跟踪不可用"))
    block = epic_stories_block(epic, docs)
    if block["done"] < block["total"]:
        warnings.append(v("PENDING_DECISION",
                          display_path(os.path.join(out_dir, STORIES_FILE), project_root)
                          + " stories[epic=%s].status" % epic,
                          "epic 未收尾（%d/%d done，未完成 %s）；partial 回顾需用户确认后"
                          "写 partial: true，否则先完成剩余 story 或刷新 sprint"
                          % (block["done"], block["total"],
                             "、".join(p["id"] for p in block["pending"]))))
    return warnings


def cmd_collect(args):
    root = os.path.abspath(args.project_root)
    out = os.path.abspath(args.output_dir)
    epic = normalize_epic(args.epic)
    docs = load_docs(out)
    payload = empty_payload(args, epic)
    payload["docs"] = doc_summaries(docs, root, out)

    if epic is None:
        payload["violations"] = [v("ENUM_INVALID", "args --epic",
                                   "epic 须为 E-<n> 或 <n>，实为 %s" % args.epic)]
        payload["gate"]["route"] = "传入 --epic E-<n>（或编号）后重跑本技能"
        emit(payload, args.json, human_collect)
        return 1

    passed, violations, route = gate_check(epic, docs, out, root)
    payload["gate"] = {"passed": passed, "files": payload["docs"], "route": route}
    payload["violations"] = violations
    if not passed:
        emit(payload, args.json, human_collect)
        return 1

    block = epic_stories_block(epic, docs)
    tasks = epic_tasks(epic, docs)
    bugs = epic_bugs(epic, docs)
    coverage = epic_coverage(epic, docs)
    first_retro, prev = prev_actions(epic, docs)
    metrics = collect_metrics(epic, docs)

    payload["ok"] = True
    payload["stories"] = block
    payload["metrics"] = metrics
    payload["bugs"] = bugs
    payload["coverage"] = coverage
    payload["first_retro"] = first_retro
    payload["prev_actions"] = prev
    payload["next_epic"] = next_epic_info(epic, docs)
    payload["warnings"] = collect_warnings(epic, docs, out, root)
    payload["counts"] = {
        "stories": block["total"], "done": block["done"],
        "rounds": metrics["rounds_total"], "blocked": metrics["blocked_count"],
        "augment_fail": metrics["augment_fail"], "bugs": len(bugs),
        "prev_actions": len(prev), "tcs": coverage["tcs"],
    }
    emit(payload, args.json, human_collect)
    return 0


def human_collect(payload):
    if not payload["ok"]:
        if payload["violations"]:
            print("拒绝：")
            for item in payload["violations"]:
                print("- %s %s: %s" % (item["code"], item["where"], item["msg"]))
        else:   # 冗余防御：ok=False 必带 violation（当前不可达）
            print("拒绝：门禁未通过")
        print("路由：%s" % payload["gate"]["route"])
        return
    counts = payload["counts"]
    metrics = payload["metrics"]
    print("门禁通过：epic %s（stories %d，done %d）。"
          % (payload["epic"], payload["stories"]["total"], payload["stories"]["done"]))
    print("指标：rounds %d · blocked %d · augment fail %d · 缺陷 functional %d / "
          "non-functional %d"
          % (metrics["rounds_total"], metrics["blocked_count"], metrics["augment_fail"],
             metrics["bugs"]["functional"], metrics["bugs"]["non-functional"]))
    coverage = payload["coverage"]
    print("覆盖：AC %d 中 %d 有用例，缺口 %d %s"
          % (coverage["acs"], coverage["covered"], len(coverage["gaps"]),
             "（%s）" % "、".join(coverage["gaps"]) if coverage["gaps"] else ""))
    if payload["first_retro"]:
        print("接续：首份 retro（无上一份 action_items 可跟踪）")
    else:
        print("接续：回带上一份 retro 的 action_items %d 条" % counts["prev_actions"])
    nxt = payload["next_epic"]
    print("下一 epic：%s" % ("%s（共享 FR %s）"
                             % (nxt["id"], "、".join(nxt["shared_frs"]) or "无")
                             if nxt["exists"] else "未定义（回顾照做，行动项照留）"))
    for item in payload["warnings"]:
        print("警告 %s %s: %s" % (item["code"], item["where"], item["msg"]))


# ---------------------------------------------------------------- check

class Refs(object):
    """引用解析面：来源文件在场性 + 已知 ID 集；来源缺席 → 该面降级（调用方定升降级）。"""

    KIND_FILE = {"S": STORIES_FILE, "E": EPICS_FILE, "BUG": BUG_LOG_FILE}

    def __init__(self, docs, out_dir, project_root):
        self.show = {name: display_path(os.path.join(out_dir, name), project_root)
                     for name in (STORIES_FILE, EPICS_FILE, BUG_LOG_FILE)}
        self.sets = {
            "S": {str(s["id"]) for s in story_entries(docs) if nonempty(s.get("id"))},
            "E": epic_ids(docs),
            "BUG": {str(b["id"]) for b in items(doc_of(docs, BUG_LOG_FILE), "bugs")
                    if isinstance(b, dict) and nonempty(b.get("id"))},
        }
        self.unavailable = set()
        self.missing = []
        for kind, filename in self.KIND_FILE.items():
            entry = docs[filename]
            if entry["present"] and entry["err"] is None:
                continue
            self.unavailable.add(kind)
            self.missing.append(v("MISSING_FILE", self.show[filename],
                                  "%s %s：其中 ID 引用无法解析"
                                  % (filename, "不可解析" if entry["present"]
                                     else "未找到")))

    def resolve(self, kind, ref, where):
        """按来源解析引用；来源缺席 → 降级为空（调用方以 refs.missing 处理）。"""
        if kind in self.unavailable:
            return []
        if str(ref) in self.sets[kind]:
            return []
        return [v("UNKNOWN_ID", where, "%s 在 %s 中不存在"
                  % (ref, self.KIND_FILE[kind]))]


def check_metrics(record, where, final, docs, epic):
    violations = []
    metrics = record.get("metrics")
    if not isinstance(metrics, dict):
        return [v("EMPTY_FIELD", where + ".metrics", "metrics 缺失或不是映射")]
    for key in METRIC_INT_KEYS:
        value = metrics.get(key)
        if value is None:
            violations.append(v("EMPTY_FIELD", "%s.metrics.%s" % (where, key),
                                "metrics.%s 缺失" % key))
        elif not is_int(value) or value < 0:
            violations.append(v("ENUM_INVALID", "%s.metrics.%s" % (where, key),
                                "%s 须为非负整数（实为 %s）" % (key, value)))
    bugs = metrics.get("bugs")
    if not isinstance(bugs, dict):
        violations.append(v("EMPTY_FIELD", where + ".metrics.bugs",
                            "metrics.bugs 缺失（须含 functional / non-functional）"))
    else:
        for name in BUG_CLASSES:
            value = bugs.get(name)
            if not is_int(value) or value < 0:
                violations.append(v("ENUM_INVALID", "%s.metrics.bugs.%s" % (where, name),
                                    "%s 须为非负整数（实为 %s）" % (name, value)))
    if final and not epic_is_known(docs, epic):
        return violations
    if final and not violations:
        actual = collect_metrics(epic, docs)
        diff = []
        for key in METRIC_INT_KEYS:
            if metrics.get(key) != actual[key]:
                diff.append("%s 声明 %s ≠ 实际 %s" % (key, metrics.get(key), actual[key]))
        if isinstance(bugs, dict):
            for name in BUG_CLASSES:
                if bugs.get(name) != actual["bugs"][name]:
                    diff.append("bugs.%s 声明 %s ≠ 实际 %s"
                                % (name, bugs.get(name), actual["bugs"][name]))
        if diff:
            violations.append(v("SET_MISMATCH", where + ".metrics",
                                "metrics 与集合真值不符：%s（口径同 collect）"
                                % "；".join(diff)))
    return violations


def epic_is_known(docs, epic):
    return nonempty(epic) and str(epic) in epic_ids(docs)


def check_patterns(record, where, refs):
    """patterns：跨 story 模式（≥2 成交付证据）+ evidence 引用解析（S-x / BUG-0xx）。"""
    violations = []
    patterns = record.get("patterns")
    if patterns is None:
        return [v("EMPTY_FIELD", where + ".patterns", "patterns 缺失（无模式写空列表）")]
    if not isinstance(patterns, list):
        return [v("EMPTY_FIELD", where + ".patterns", "patterns 不是列表")]
    for i, pattern in enumerate(patterns):
        pw = "%s.patterns[%d]" % (where, i)
        if not isinstance(pattern, dict):
            violations.append(v("EMPTY_FIELD", pw, "pattern 不是映射"))
            continue
        if not nonempty(pattern.get("theme")):
            violations.append(v("EMPTY_FIELD", pw + ".theme", "theme 为空"))
        count = pattern.get("count")
        if not is_int(count):
            violations.append(v("ENUM_INVALID", pw + ".count",
                                "count 须为整数（跨 story 出现次数），实为 %s" % count))
        elif count < PATTERN_MIN_COUNT:
            violations.append(v("ENUM_INVALID", pw + ".count",
                                "count 须 ≥%d：跨 story 才成模式" % PATTERN_MIN_COUNT))
        evidence = pattern.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            violations.append(v("EMPTY_FIELD", pw + ".evidence",
                                "evidence 须为非空列表（S-x / BUG-0xx）"))
            continue
        for j, ref in enumerate(evidence):
            ew = "%s.evidence[%d]" % (pw, j)
            if not nonempty(ref):
                violations.append(v("EMPTY_FIELD", ew, "evidence 项为空"))
            elif STORY_TOKEN_RE.fullmatch(str(ref)):
                violations += refs.resolve("S", ref, ew)
            elif BUG_TOKEN_RE.fullmatch(str(ref)):
                violations += refs.resolve("BUG", ref, ew)
            else:
                violations.append(v("ENUM_INVALID", ew,
                                    "evidence 须为 S-x 或 BUG-0xx，实为 %s" % ref))
    return violations


def check_text_lists(record, where):
    violations = []
    for key in TEXT_LIST_KEYS:
        value = record.get(key)
        if value is None:
            violations.append(v("EMPTY_FIELD", "%s.%s" % (where, key),
                                "%s 缺失（无内容写空列表）" % key))
        elif not isinstance(value, list):
            violations.append(v("EMPTY_FIELD", "%s.%s" % (where, key), "%s 不是列表" % key))
        elif any(not nonempty(item) for item in value):
            violations.append(v("EMPTY_FIELD", "%s.%s" % (where, key), "%s 项不得为空" % key))
    return violations


def check_action_items(record, where, final):
    violations = []
    actions = record.get("action_items")
    if actions is None:
        return [v("EMPTY_FIELD", where + ".action_items",
                  "action_items 缺失（无行动项写空列表）")]
    if not isinstance(actions, list):
        return [v("EMPTY_FIELD", where + ".action_items", "action_items 不是列表")]
    if final and not actions:
        violations.append(v("EMPTY_FIELD", where + ".action_items",
                            "--final 要求至少 1 条行动项（回顾的承诺面）"))
    seen = set()
    for i, action in enumerate(actions):
        aw = "%s.action_items[%d]" % (where, i)
        if not isinstance(action, dict):
            violations.append(v("EMPTY_FIELD", aw, "action item 不是映射"))
            continue
        aid = action.get("id")
        if not nonempty(aid):
            violations.append(v("EMPTY_FIELD", aw + ".id", "行动项 id 缺失"))
        elif not AI_RE.fullmatch(str(aid)):
            violations.append(v("ENUM_INVALID", aw + ".id",
                                "id 须为 AI-0nn（三位零填充），实为 %s" % aid))
        elif str(aid) in seen:
            violations.append(v("DUPLICATE_ID", aw + ".id", "行动项 ID %s 重复" % aid))
        else:
            seen.add(str(aid))
        for key in ("action", "owner", "done_when"):
            if not nonempty(action.get(key)):
                violations.append(v("EMPTY_FIELD", "%s.%s" % (aw, key),
                                    "%s 为空（SMART 行动项须有动作/归属/完成判据）" % key))
        category = action.get("category")
        if not nonempty(category):
            violations.append(v("EMPTY_FIELD", aw + ".category", "category 缺失"))
        elif str(category) not in ACTION_CATEGORIES:
            violations.append(v("ENUM_INVALID", aw + ".category",
                                "category 越界：%s（合法集 %s）"
                                % (category, "|".join(ACTION_CATEGORIES))))
    return violations


def check_prep_items(record, where):
    violations = []
    prep = record.get("prep_items")
    if prep is None:
        return [v("EMPTY_FIELD", where + ".prep_items", "prep_items 缺失（无准备项写空列表）")]
    if not isinstance(prep, list):
        return [v("EMPTY_FIELD", where + ".prep_items", "prep_items 不是列表")]
    for i, item in enumerate(prep):
        pw = "%s.prep_items[%d]" % (where, i)
        if not isinstance(item, dict):
            violations.append(v("EMPTY_FIELD", pw, "prep item 不是映射"))
            continue
        for key in ("item", "owner"):
            if not nonempty(item.get(key)):
                violations.append(v("EMPTY_FIELD", "%s.%s" % (pw, key), "%s 为空" % key))
        cls = item.get("class")
        if not nonempty(cls):
            violations.append(v("EMPTY_FIELD", pw + ".class", "class 缺失"))
        elif str(cls) not in PREP_CLASSES:
            violations.append(v("ENUM_INVALID", pw + ".class",
                                "class 越界：%s（合法集 %s）"
                                % (cls, "|".join(PREP_CLASSES))))
        if "effort" in item and not nonempty(item.get("effort")):
            violations.append(v("EMPTY_FIELD", pw + ".effort", "effort 出现时不得为空"))
    return violations


def check_critical_path(record, where):
    violations = []
    path = record.get("critical_path")
    if path is None:
        return [v("EMPTY_FIELD", where + ".critical_path",
                  "critical_path 缺失（无关键路径项写空列表）")]
    if not isinstance(path, list):
        return [v("EMPTY_FIELD", where + ".critical_path", "critical_path 不是列表")]
    for i, item in enumerate(path):
        cw = "%s.critical_path[%d]" % (where, i)
        if not isinstance(item, dict):
            violations.append(v("EMPTY_FIELD", cw, "critical path 项不是映射"))
            continue
        for key in ("item", "why", "owner"):
            if not nonempty(item.get(key)):
                violations.append(v("EMPTY_FIELD", "%s.%s" % (cw, key), "%s 为空" % key))
    return violations


def check_readiness(record, where, final):
    """就绪度五维：键必须在场；值非空为 --final 义务（源 step-9 五问）。"""
    violations = []
    readiness = record.get("readiness")
    if not isinstance(readiness, dict):
        return [v("EMPTY_FIELD", where + ".readiness",
                  "readiness 缺失或不是映射（五键 %s）" % "|".join(READINESS_KEYS))]
    for key in READINESS_KEYS:
        if key not in readiness:
            violations.append(v("EMPTY_FIELD", "%s.readiness.%s" % (where, key),
                                "readiness.%s 缺失" % key))
        elif final and not nonempty(readiness[key]):
            violations.append(v("EMPTY_FIELD", "%s.readiness.%s" % (where, key),
                                "--final 要求 readiness.%s 非空" % key))
    return violations


def check_prev_followup(record, where, refs, other_ids):
    """前一份 retro 的承诺跟踪：retro 须指向同文件内的既往记录（非自身）。"""
    violations = []
    followup = record.get("prev_followup")
    if followup is None:
        return violations
    if not isinstance(followup, list):
        return [v("EMPTY_FIELD", where + ".prev_followup", "prev_followup 不是列表")]
    for i, item in enumerate(followup):
        fw = "%s.prev_followup[%d]" % (where, i)
        if not isinstance(item, dict):
            violations.append(v("EMPTY_FIELD", fw, "prev_followup 项不是映射"))
            continue
        ref = item.get("retro")
        if not nonempty(ref):
            violations.append(v("EMPTY_FIELD", fw + ".retro", "retro 引用缺失"))
        elif not RT_RE.fullmatch(str(ref)):
            violations.append(v("ENUM_INVALID", fw + ".retro",
                                "retro 须为 RT-0nn，实为 %s" % ref))
        elif str(ref) not in other_ids:
            violations.append(v("UNKNOWN_ID", fw + ".retro",
                                "%s 不是本文件内既往记录（承诺跟踪只能指向同期已存的 retro）"
                                % ref))
        for key in ("action", "evidence"):
            if not nonempty(item.get(key)):
                violations.append(v("EMPTY_FIELD", "%s.%s" % (fw, key), "%s 为空" % key))
        status = item.get("status")
        if not nonempty(status):
            violations.append(v("EMPTY_FIELD", fw + ".status", "status 缺失"))
        elif str(status) not in FOLLOWUP_STATUSES:
            violations.append(v("ENUM_INVALID", fw + ".status",
                                "status 越界：%s（合法集 %s）"
                                % (status, "|".join(FOLLOWUP_STATUSES))))
    return violations


def check_significant_changes(record, where):
    violations = []
    changes = record.get("significant_changes")
    if changes is None:
        return violations
    if not isinstance(changes, list):
        return [v("EMPTY_FIELD", where + ".significant_changes",
                  "significant_changes 不是列表")]
    for i, item in enumerate(changes):
        cw = "%s.significant_changes[%d]" % (where, i)
        if not isinstance(item, dict):
            violations.append(v("EMPTY_FIELD", cw, "significant change 项不是映射"))
            continue
        for key in ("change", "impact", "recommended_action"):
            if not nonempty(item.get(key)):
                violations.append(v("EMPTY_FIELD", "%s.%s" % (cw, key), "%s 为空" % key))
    return violations


def check_next_epic(record, where, refs):
    violations = []
    nxt = record.get("next_epic")
    if nxt is None:
        return violations
    if not isinstance(nxt, dict):
        return [v("EMPTY_FIELD", where + ".next_epic", "next_epic 不是映射")]
    exists = nxt.get("exists")
    if not isinstance(exists, bool):
        violations.append(v("EMPTY_FIELD", where + ".next_epic.exists",
                            "exists 须为布尔值（实为 %s）" % exists))
        exists = None
    nid = nxt.get("id")
    if exists is True:
        if not nonempty(nid):
            violations.append(v("EMPTY_FIELD", where + ".next_epic.id",
                                "exists=true 时 id 必填"))
        elif not EPIC_RE.fullmatch(str(nid)):
            violations.append(v("ENUM_INVALID", where + ".next_epic.id",
                                "id 须为 E-<n>，实为 %s" % nid))
        else:
            violations += refs.resolve("E", nid, where + ".next_epic.id")
    deps = nxt.get("dependencies")
    if not isinstance(deps, list):
        violations.append(v("EMPTY_FIELD", where + ".next_epic.dependencies",
                            "dependencies 缺失或不是列表（无依赖写空列表）"))
    elif any(not nonempty(d) for d in deps):
        violations.append(v("EMPTY_FIELD", where + ".next_epic.dependencies",
                            "dependencies 项不得为空"))
    return violations


def check_final_duties(record, where, status):
    """--final 附加：status 已落 final、零假设（metrics 互证在 check_metrics 内完成）。"""
    violations = []
    if str(status) != "final":
        violations.append(v("STATUS_MISMATCH", where + ".status",
                            "--final 要求 status 已落 final（实为 %s）" % status))
    if any("[ASSUMPTION]" in s for s in collect_strings(record)):
        violations.append(v("ASSUMPTION_PRESENT", where,
                            "--final 要求零 [ASSUMPTION]；未决推断须先落定"))
    return violations


def check_record(index, record, final, docs, where_base, other_ids, refs):
    violations = []
    where = "%s.retros[%d]" % (where_base, index)
    if not isinstance(record, dict):
        return [v("EMPTY_FIELD", where, "记录不是映射")], None

    rid = record.get("id")
    if not nonempty(rid):
        violations.append(v("EMPTY_FIELD", where + ".id", "id 缺失"))
    elif not RT_RE.fullmatch(str(rid)):
        violations.append(v("ENUM_INVALID", where + ".id",
                            "id 须为 RT-0nn（三位零填充），实为 %s" % rid))

    date = record.get("date")
    if not nonempty(date):
        violations.append(v("EMPTY_FIELD", where + ".date", "date 缺失"))
    elif not DATE_RE.fullmatch(str(date)):
        violations.append(v("ENUM_INVALID", where + ".date",
                            "date 须为 YYYY-MM-DD，实为 %s" % date))

    status = record.get("status")
    if not nonempty(status):
        violations.append(v("EMPTY_FIELD", where + ".status", "status 缺失"))
    elif str(status) not in RECORD_STATUSES:
        violations.append(v("ENUM_INVALID", where + ".status",
                            "status 越界：%s（合法集 %s）"
                            % (status, "|".join(RECORD_STATUSES))))

    if not isinstance(record.get("partial"), bool):
        violations.append(v("ENUM_INVALID", where + ".partial",
                            "partial 须为布尔值（实为 %s）" % record.get("partial")))

    epic = record.get("epic")
    if not nonempty(epic):
        violations.append(v("EMPTY_FIELD", where + ".epic", "epic 引用缺失"))
    elif not EPIC_RE.fullmatch(str(epic)):
        violations.append(v("ENUM_INVALID", where + ".epic",
                            "epic 须为 E-<n>，实为 %s" % epic))
    else:
        violations += refs.resolve("E", epic, where + ".epic")

    violations += check_metrics(record, where, final, docs, epic)
    violations += check_patterns(record, where, refs)
    violations += check_text_lists(record, where)
    violations += check_action_items(record, where, final)
    violations += check_prep_items(record, where)
    violations += check_critical_path(record, where)
    violations += check_readiness(record, where, final)
    violations += check_prev_followup(record, where, refs, other_ids)
    violations += check_significant_changes(record, where)
    violations += check_next_epic(record, where, refs)
    if final:
        violations += check_final_duties(record, where, status)
    return violations, epic


def cmd_check(args):
    root = os.path.abspath(args.project_root)
    out = os.path.abspath(args.output_dir)
    path = os.path.join(out, RETRO_FILE)
    show = display_path(path, root)
    docs = load_docs(out)
    refs = Refs(docs, out, root)
    violations = []
    warnings = []
    records = []

    data, err = load_yaml_safe(path)
    if data is None and err is None:
        violations.append(v("MISSING_FILE", show,
                            "%s 不存在（先完成一次 retrospective 起草）" % RETRO_FILE))
    elif err is not None:
        violations.append(v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err))
    elif not isinstance(data, dict):
        violations.append(v("EMPTY_FIELD", show, "顶层不是映射（须为 project + retros）"))
    else:
        project = data.get("project")
        if project is not None and not isinstance(project, dict):
            violations.append(v("EMPTY_FIELD", show + " project", "project 不是映射"))
        revisions = data.get("revisions")
        if revisions is not None and not isinstance(revisions, list):
            violations.append(v("EMPTY_FIELD", show + " revisions", "revisions 不是列表"))
        raw = data.get("retros")
        if raw is None:
            violations.append(v("EMPTY_FIELD", show + " retros",
                                "retros 缺失（集合形态；无记录写空列表）"))
        elif not isinstance(raw, list):
            violations.append(v("EMPTY_FIELD", show + " retros", "retros 不是列表"))
        else:
            records = raw
            ids = [str(r.get("id")) for r in records
                   if isinstance(r, dict) and nonempty(r.get("id"))]
            seen = set()
            for i, record in enumerate(records):
                if isinstance(record, dict) and nonempty(record.get("id")):
                    rid = str(record["id"])
                    if rid in seen:
                        violations.append(v("DUPLICATE_ID", "%s.retros[%d].id" % (show, i),
                                            "记录 ID %s 重复（RT ID 稳定不重用）" % rid))
                    seen.add(rid)
            if args.id:
                selected = [i for i, r in enumerate(records)
                            if isinstance(r, dict) and str(r.get("id")) == args.id]
                if not selected:
                    violations.append(v("UNKNOWN_ID", "%s.retros" % show,
                                        "记录 %s 不存在" % args.id))
                records = [records[i] for i in selected]
            for i, record in enumerate(records):
                other_ids = set(ids)
                if isinstance(record, dict) and nonempty(record.get("id")):
                    other_ids.discard(str(record["id"]))
                record_violations, _ = check_record(i, record, args.final, docs, show,
                                                    other_ids, refs)
                violations += record_violations
            if args.final and not records and not args.id:
                violations.append(v("EMPTY_FIELD", show + " retros",
                                    "--final 要求至少 1 条记录"))

    # 来源文件缺席：final 升为违规（引用面无法验证），起草期降为警告
    if refs.missing:
        if args.final:
            violations += refs.missing
        else:
            warnings += [{**item, "msg": item["msg"] + "（起草期降级警告）"}
                         for item in refs.missing]

    counts = {
        "retros": len(records),
        "by_status": count_by(records, "status"),
        "action_items": count_items(records, "action_items"),
        "prep_items": count_items(records, "prep_items"),
        "critical_path": count_items(records, "critical_path"),
        "patterns": count_items(records, "patterns"),
        "by_category": count_nested(records, "action_items", "category"),
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
    emit(payload, args.json, human_check)
    return 0 if ok else 1


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
        if isinstance(record, dict) and isinstance(record.get(key), list):
            total += len(record[key])
    return total


def count_nested(records, list_key, field):
    counts = {}
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get(list_key), list):
            continue
        for item in record[list_key]:
            if isinstance(item, dict) and nonempty(item.get(field)):
                name = str(item[field])
                counts[name] = counts.get(name, 0) + 1
    return counts


def human_check(payload):
    if payload["ok"]:
        print("PASS：%s 校验通过（retros=%d，行动项 %d）"
              % (payload["output_dir"] + "/" + RETRO_FILE, payload["counts"]["retros"],
                 payload["counts"]["action_items"]))
        for item in payload["warnings"]:
            print("警告 %s %s: %s" % (item["code"], item["where"], item["msg"]))
        return
    print("FAIL：")
    for item in payload["violations"]:
        print("- %s %s: %s" % (item["code"], item["where"], item["msg"]))
    for item in payload["warnings"]:
        print("警告 %s %s: %s" % (item["code"], item["where"], item["msg"]))


def emit(payload, as_json, human_lines):
    if as_json:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        human_lines(payload)


def build_parser():
    ap = argparse.ArgumentParser(
        description="diy-retrospective 确定性引擎：epic 收尾回顾的门禁 + 指标机械采集 + "
                    "retrospective.yaml 校验")
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("collect", help="门禁 + 指标机械采集 + 接续面回带（只读）")
    c.add_argument("--epic", required=True, help="目标 epic：E-<n> 或 <n>")
    c.add_argument("--project-root", default=".", help="项目根（默认 .）")
    c.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    c.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    c.set_defaults(func=cmd_collect)

    k = sub.add_parser("check", help="校验 retrospective.yaml（schema/枚举/引用；--final 附加定稿义务）")
    k.add_argument("--project-root", default=".", help="项目根（默认 .）")
    k.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    k.add_argument("--id", help="只校验指定记录 RT-xxx")
    k.add_argument("--final", action="store_true",
                   help="定稿校验：status 已落 final + 零假设 + metrics 互证 + readiness/行动项义务")
    k.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    k.set_defaults(func=cmd_check)
    return ap


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = build_parser().parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
