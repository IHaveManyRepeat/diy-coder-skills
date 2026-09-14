# -*- coding: utf-8 -*-
"""diy-create-story 确定性引擎：目标 story 的情报采集（只读）+ story-context.yaml 校验。

子命令：
  collect  目标 story 的确定性采集（只读，绝不写文件）：
             1 门禁（源技能 step-1「确定目标故事」的门禁化）：stories.yaml 在场、可解析、
               project.status == final，且 --story 指向的 story 存在；不满足 → 零产出 exit 1
               + 结构化拒绝回执（violations 带码 + gate.route 给路由）。story 悬空时回执附
               suggestions（候选 story ID，供会话降级为用户选择）。
               sprint.yaml / test-plan.yaml / architecture.yaml 缺席不拒（源输入表 fallback
               语义：上游未生成则引用面为空，降级为 warning）。
             2 AC 清点：目标 story 的全部 acceptance_criteria（id/given/when/then/refs +
               可选 design_ref）——替换源 step-2「人工通读 epics 分片提取故事基础」。
             3 TC 清点：test-plan.yaml 中 ac 属该 story AC 集的用例（id/ac/title/type/
               priority/technique/status）——源需人工核对，此处机械匹配。
             4 前序情报：stories.yaml 中编号最高且小于当前者（S-y, y < x）的 story 及其
               sprint 任务 note/evidence/loop/blocked_reason——替换源 step-2「扫描
               implementation_artifacts 找上一故事文件」。
             5 决策清单：architecture.yaml decisions[] 的 {id, title, status, affects} 摘要级
               ——替换源 step-3「通读架构文档提取护栏」的取材面（适用面判定留给会话）。
             6 git 情报：最近 5 次提交（hash/date/subject/files，每提交最多 20 个文件路径）
               ——替换源 step-2 的 git 分析；VCS 不可用 / 无提交 → NO_VCS warning 降级，不崩。
  check    校验 {output_dir}/story-context.yaml（SC-### 集合，形状对齐 bug-log.yaml）：
           schema / id 格式与唯一 / story 解析（stories.yaml）/ epic 与 story 一致 /
           ac_refs ⊆ 该 story 的 AC / tc_refs 解析（test-plan.yaml）且归属该 story /
           decisions 解析（architecture.yaml）/ files[].path 相对 project-root 且 update 型
           存在 + current_state 非空 / 同一 story 仅一条记录（按 story 键原位重写）。
           --final 附加：status=final、zero [ASSUMPTION]、files 非空、verify 非空、
           update 型 preserve 非空、open_questions 空或逐条 [CLOSED] 显式闭合。
           上游缺席（stories 拒跑；test-plan/architecture 出 warning）时相关解析降级。

分工裁定（任务书 §2.2/§2.3/§3）：story-context 属新产物类型，不进 diyc.py check 的硬编码
类型集；本引擎契约同构（exit 0 唯一放行 / --json 单行回执 / violations[{code, where, msg}]
+ counts；where 正斜杠、相对 project-root）；--output-dir 必填，实例解析由 SKILL.md 委托
diyc.py resolve（引擎内不做）。--previous 不实现：记录按 story 键原位重写，SC ID 集合不会
收缩（任务书 §2.2 逐技能记账）。违规码复用 batch3-contract §3 冻结集；新增 NO_VCS（VCS 情报
不可用 / 无提交的降级专用，同 W5 diy-investigate 同名语义）。产物与 SC-### ID 由
diy-create-story 会话（LLM）创作，本引擎只校验格式与唯一性；两个子命令都不写盘。
"""
# trace: B2 diy-create-story 验收#3（前置门禁）/ #4（ID 链接入）/ #12（diyc 接线）
import argparse
import io
import json
import os
import re
import subprocess
import sys

import yaml

STORIES_FILE = "stories.yaml"
TEST_PLAN_FILE = "test-plan.yaml"
SPRINT_FILE = "sprint.yaml"
ARCH_FILE = "architecture.yaml"
CONTEXT_FILE = "story-context.yaml"

DIYC_ROUTE = "diy-epics-stories"
SC_RE = re.compile(r"SC-\d{3}")
STORY_RE = re.compile(r"S-(\d+)")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")

RECORD_STATUSES = ("draft", "final")
FILE_ACTIONS = ("new", "update")
CLOSED_PREFIX = "[CLOSED]"
GIT_COMMITS = 5
GIT_FILES_PER_COMMIT = 20
GIT_SEP = "@@"


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


def rel_to_root(root, rel_path):
    """把产物里的正斜杠相对路径落成磁盘绝对路径。"""
    return os.path.join(root, *str(rel_path).replace("\\", "/").split("/"))


def is_safe_rel(rel_path):
    """相对 project-root 的正斜杠路径（禁绝对路径 / 盘符 / 上跳）。"""
    text = str(rel_path).replace("\\", "/")
    if not text or text.startswith("/") or os.path.isabs(str(rel_path)):
        return False
    return ".." not in text.split("/")


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


def natural_key(value):
    """数字感知排序键（S-2 < S-10 / TC-3.1.2 < TC-3.1.10），对齐 diyc_lib.id_sort。"""
    return tuple((0, int(p)) if p.isdigit() else (1, p)
                 for p in re.split(r"[-.]", str(value)))


def id_sort(ids):
    return sorted(ids, key=natural_key)


def story_num(story_id):
    """S-x → x（int）；非 story ID → None。"""
    m = STORY_RE.fullmatch(str(story_id)) if nonempty(story_id) else None
    return int(m.group(1)) if m else None


def story_map(doc):
    """stories.yaml → {S-x: 条目}。"""
    result = {}
    for entry in items(doc, "stories"):
        if isinstance(entry, dict) and nonempty(entry.get("id")):
            result[str(entry["id"])] = entry
    return result


def ac_ids(story_entry):
    """该 story 的 AC ID 序列（文件顺序）。"""
    return [str(ac["id"]) for ac in items(story_entry, "acceptance_criteria")
            if isinstance(ac, dict) and nonempty(ac.get("id"))]


# ---------------------------------------------------------------- 文档装载

def load_doc(out_dir, filename):
    data, err = load_yaml_safe(os.path.join(out_dir, filename))
    return {"present": data is not None or err is not None, "data": data, "err": err}


def load_docs(out_dir):
    """一次性装载四份上游文档（只读，不落盘）。"""
    return {name: load_doc(out_dir, name)
            for name in (STORIES_FILE, TEST_PLAN_FILE, SPRINT_FILE, ARCH_FILE)}


def missing_warning(out_dir, filename, note, project_root):
    return v("MISSING_FILE", display_path(os.path.join(out_dir, filename), project_root), note)


# ---------------------------------------------------------------- 门禁

def gate_check(docs, out_dir, project_root, story):
    """门禁：stories.yaml 在场/可解析/定稿，且目标 story 存在。

    返回 (passed, violations, route, story_entry, suggestions)。
    """
    show = display_path(os.path.join(out_dir, STORIES_FILE), project_root)
    entry = docs[STORIES_FILE]
    if not entry["present"]:
        return (False, [v("MISSING_FILE", show, "stories.yaml 不存在；先跑 %s 产出并定稿故事清单" % DIYC_ROUTE)],
                "先跑 %s 产出并定稿 stories.yaml，再重跑本技能" % DIYC_ROUTE, None, [])
    if entry["err"] is not None:
        return (False, [v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % entry["err"])],
                "先修复 stories.yaml 的 YAML 语法，再重跑本技能", None, [])
    data = entry["data"]
    project = data.get("project") if isinstance(data, dict) else None
    status = project.get("status") if isinstance(project, dict) else None
    if status != "final":
        return (False, [v("STATUS_MISMATCH", show + " project.status",
                          "stories.yaml 的 project.status 须为 final（实为 %s）；先跑 %s 定稿"
                          % (status if nonempty(status) else "未声明", DIYC_ROUTE))],
                "先跑 %s 定稿 stories.yaml，再重跑本技能" % DIYC_ROUTE, None, [])
    stories = story_map(data)
    story_entry = stories.get(str(story))
    if story_entry is None:
        todo = [sid for sid, e in stories.items() if e.get("status") != "done"]
        return (False, [v("UNKNOWN_ID", show + " stories",
                          "目标 story %s 在 stories.yaml 中不存在" % story)],
                "确认 story ID；若故事尚未定义，先跑 %s 补建" % DIYC_ROUTE, None, id_sort(todo))
    return True, [], None, story_entry, []


# ---------------------------------------------------------------- 采集

def read_tcs(docs, acs):
    """test-plan.yaml 中 ac 属该 story AC 集的用例（摘要级）。"""
    wanted = set(acs)
    result = []
    for tc in items(docs[TEST_PLAN_FILE]["data"], "test_cases"):
        if not isinstance(tc, dict) or not nonempty(tc.get("id")):
            continue
        if str(tc.get("ac")) not in wanted:
            continue
        result.append({k: tc.get(k) for k in ("id", "ac", "title", "type", "priority",
                                              "technique", "status")})
    return sorted(result, key=lambda t: natural_key(t["id"]))


def read_prior(docs, story, stories):
    """前序 story = 编号最高且小于当前者；内容取 sprint 任务（缺席则 task 为 None）。"""
    num = story_num(story)
    if num is None:
        return None
    lower = [n for n in (story_num(s) for s in stories) if n is not None and n < num]
    if not lower:
        return None
    ref = "S-%d" % max(lower)
    prior = {"ref": ref, "story_status": stories[ref].get("status"), "task": None}
    for task in items(docs[SPRINT_FILE]["data"], "tasks"):
        if not isinstance(task, dict) or str(task.get("story")) != ref:
            continue
        prior["task"] = {k: task.get(k) for k in ("status", "note", "evidence", "loop",
                                                  "blocked_reason")}
        break
    return prior


def read_decisions(docs):
    """architecture.yaml decisions[] 摘要级（适用面判定留给会话）。"""
    result = []
    for dec in items(docs[ARCH_FILE]["data"], "decisions"):
        if isinstance(dec, dict) and nonempty(dec.get("id")):
            result.append({k: dec.get(k) for k in ("id", "title", "status", "affects")})
    return sorted(result, key=lambda d: natural_key(d["id"]))


def git_intel(project_root):
    """最近 GIT_COMMITS 次提交摘要。VCS 不可用 / 无提交 → (block, [NO_VCS warning])。"""
    block = {"available": False, "commits": []}
    cmd = ["git", "-C", project_root, "log", "-n", str(GIT_COMMITS), "--date=short",
           "--name-only", "--pretty=format:" + GIT_SEP + "%h" + chr(9) + "%ad" + chr(9) + "%s"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                              errors="replace")
    except OSError as e:
        return block, [v("NO_VCS", "git log", "VCS 不可用（%s）：git 情报跳过" % e)]
    if proc.returncode != 0:
        return block, [v("NO_VCS", "git log",
                         "VCS 不可用（非 git 仓库或无提交）：git 情报跳过")]
    commits = []
    current = None
    for line in (proc.stdout or "").splitlines():
        if line.startswith(GIT_SEP):
            parts = line[len(GIT_SEP):].split(chr(9))
            current = {"hash": parts[0] if len(parts) > 0 else "",
                       "date": parts[1] if len(parts) > 1 else "",
                       "subject": parts[2] if len(parts) > 2 else "",
                       "files": [], "files_total": 0, "files_truncated": False}
            commits.append(current)
        elif line.strip() and current is not None:
            current["files_total"] += 1
            if len(current["files"]) < GIT_FILES_PER_COMMIT:
                current["files"].append(line.strip().replace("\\", "/"))
            else:
                current["files_truncated"] = True
    block["commits"] = commits
    block["available"] = True
    return block, []


# ---------------------------------------------------------------- collect

def base_payload(command, args, out_dir):
    return {
        "ok": False,
        "command": command,
        "project_root": args.project_root,
        "output_dir": os.path.normpath(out_dir).replace("\\", "/"),
        "violations": [],
        "warnings": [],
        "counts": {},
    }


def cmd_collect(args):
    root = os.path.abspath(args.project_root)
    out = os.path.abspath(args.output_dir)
    docs = load_docs(out)
    payload = base_payload("collect", args, out)
    payload["story"] = args.story
    payload["acs"] = []
    payload["tcs"] = []
    payload["prior"] = None
    payload["decisions"] = []
    payload["git"] = {"available": False, "commits": []}
    payload["suggestions"] = []
    warnings = []

    passed, violations, route, story_entry, suggestions = gate_check(docs, out, root, args.story)
    payload["violations"] = violations
    payload["gate"] = {"passed": passed, "route": route,
                       "files": {STORIES_FILE: docs[STORIES_FILE]["present"]}}
    payload["suggestions"] = suggestions

    for name, note in ((SPRINT_FILE, "sprint.yaml 缺席：前序情报与任务定位降级，story 选择退化为显式指定"),
                       (TEST_PLAN_FILE, "test-plan.yaml 缺席：TC 引用面为空（TDD 门将拦下缺覆盖任务，先跑 diy-test-design）"),
                       (ARCH_FILE, "architecture.yaml 缺席：决策引用面为空")):
        entry = docs[name]
        if entry["err"] is not None:
            warnings.append(v("UNPARSABLE_YAML", display_path(os.path.join(out, name), root),
                              "%s 不可解析：相关引用面降级" % name))
        elif not entry["present"]:
            warnings.append(missing_warning(out, name, note, root))

    if not passed:
        payload["warnings"] = warnings
        emit(payload, args.json, human_collect)
        return 1

    stories = story_map(docs[STORIES_FILE]["data"])
    acs = [ac for ac in items(story_entry, "acceptance_criteria") if isinstance(ac, dict)]
    ids = ac_ids(story_entry)
    tcs = read_tcs(docs, ids)
    prior = read_prior(docs, args.story, stories)
    decisions = read_decisions(docs)
    git, git_warnings = git_intel(root)
    warnings += git_warnings

    if not docs[TEST_PLAN_FILE]["present"]:
        tcs = []

    payload["ok"] = True
    payload["acs"] = acs
    payload["tcs"] = tcs
    payload["prior"] = prior
    payload["decisions"] = decisions
    payload["git"] = git
    payload["warnings"] = warnings
    payload["counts"] = {
        "acs": len(acs),
        "tcs": len(tcs),
        "decisions": len(decisions),
        "commits": len(git["commits"]),
        "files_recent": sum(len(c["files"]) for c in git["commits"]),
        "prior": 1 if prior else 0,
        "warnings": len(warnings),
    }
    emit(payload, args.json, human_collect)
    return 0


def human_collect(payload):
    if not payload["ok"]:
        print("拒绝：")
        for item in payload["violations"]:
            print("- %s %s: %s" % (item["code"], item["where"], item["msg"]))
        if payload.get("suggestions"):
            print("候选 story：%s" % "、".join(payload["suggestions"]))
        print("路由：%s" % payload["gate"]["route"])
        return
    counts = payload["counts"]
    print("目标 %s：AC %d · TC %d · 架构决策 %d · 前序 %s"
          % (payload["story"], counts["acs"], counts["tcs"], counts["decisions"],
             payload["prior"]["ref"] if payload["prior"] else "无"))
    if payload["git"]["available"]:
        print("git 情报：最近 %d 次提交（涉及文件 %d）"
              % (counts["commits"], counts["files_recent"]))
    else:
        print("git 情报：不可用（见 warnings）")
    for item in payload["warnings"]:
        print("警告 %s %s: %s" % (item["code"], item["where"], item["msg"]))


# ---------------------------------------------------------------- check

def check_identity(record, where):
    violations = []
    rid = record.get("id")
    if not nonempty(rid):
        violations.append(v("EMPTY_FIELD", where + ".id", "id 缺失"))
    elif not SC_RE.fullmatch(str(rid)):
        violations.append(v("ENUM_INVALID", where + ".id",
                            "id 须为 SC-0nn（三位零填充），实为 %s" % rid))
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
    return violations


def ref_list(record, key, where):
    """取引用列表键：(值列表, violations)。非列表 → 空列表 + 违规。"""
    value = record.get(key)
    if value is None:
        return [], []
    if not isinstance(value, list):
        return [], [v("EMPTY_FIELD", "%s.%s" % (where, key), "%s 不是列表" % key)]
    violations = []
    seen = set()
    result = []
    for i, item in enumerate(value):
        item_where = "%s.%s[%d]" % (where, key, i)
        if not nonempty(item):
            violations.append(v("EMPTY_FIELD", item_where, "%s 项为空" % key))
            continue
        text = str(item)
        if text in seen:
            violations.append(v("DUPLICATE_ID", item_where, "%s 项重复：%s" % (key, text)))
            continue
        seen.add(text)
        result.append(text)
    return result, violations


def check_story_binding(record, where, ctx):
    """story 解析 + epic 一致 + ac_refs ⊆ story AC。返回 (story_entry, acs, violations)。"""
    violations = []
    story = record.get("story")
    story_entry = None
    if not nonempty(story):
        violations.append(v("EMPTY_FIELD", where + ".story", "story 缺失（S-x 引用）"))
    elif not ctx["has_stories"]:
        violations.append(v("MISSING_FILE", "stories.yaml",
                            "stories.yaml 缺席：story 引用无法解析（先跑 %s 定稿）" % DIYC_ROUTE))
    elif str(story) not in ctx["stories"]:
        violations.append(v("UNKNOWN_ID", where + ".story",
                            "%s 在 stories.yaml 中不存在" % story))
    else:
        story_entry = ctx["stories"][str(story)]

    epic = record.get("epic")
    if not nonempty(epic):
        violations.append(v("EMPTY_FIELD", where + ".epic", "epic 缺失（E-x 引用）"))
    elif story_entry is not None and str(epic) != str(story_entry.get("epic")):
        violations.append(v("SET_MISMATCH", where + ".epic",
                            "epic 与 stories.yaml 不一致：声明 %s，实为 %s"
                            % (epic, story_entry.get("epic"))))

    acs = []
    refs, ref_violations = ref_list(record, "ac_refs", where)
    violations += ref_violations
    if not refs:
        violations.append(v("EMPTY_FIELD", where + ".ac_refs",
                            "ac_refs 为空（上下文包至少引用本 story 的一条 AC）"))
    if story_entry is not None:
        known = set(ac_ids(story_entry))
        acs = sorted(known)
        for i, ref in enumerate(refs):
            if ref not in known:
                violations.append(v("UNKNOWN_ID", "%s.ac_refs[%d]" % (where, i),
                                    "%s 不是 %s 的 AC（该 story 的 AC：%s）"
                                    % (ref, record.get("story"),
                                       "、".join(acs) if acs else "无")))
    return story_entry, acs, violations


def check_test_refs(record, where, ctx, acs):
    """tc_refs 解析（test-plan.yaml）+ 归属校验（tc.ac 须属本 story）。"""
    violations = []
    refs, ref_violations = ref_list(record, "tc_refs", where)
    violations += ref_violations
    if refs and not ctx["has_test_plan"]:
        violations.append(v("MISSING_FILE", "test-plan.yaml",
                            "test-plan.yaml 缺席：%d 条 tc_refs 无法解析（先跑 diy-test-design）"
                            % len(refs)))
        return violations
    known = set(acs)
    for i, ref in enumerate(refs):
        tc = ctx["tcs"].get(ref)
        if tc is None:
            violations.append(v("UNKNOWN_ID", "%s.tc_refs[%d]" % (where, i),
                                "%s 在 test-plan.yaml 中不存在" % ref))
        elif known and str(tc.get("ac")) not in known:
            violations.append(v("SET_MISMATCH", "%s.tc_refs[%d]" % (where, i),
                                "%s 归属 %s，不属于 %s" % (ref, tc.get("ac"), record.get("story"))))
    return violations


def check_decisions(record, where, ctx):
    violations = []
    refs, ref_violations = ref_list(record, "decisions", where)
    violations += ref_violations
    if refs and not ctx["has_arch"]:
        violations.append(v("MISSING_FILE", "architecture.yaml",
                            "architecture.yaml 缺席：%d 条 decisions 无法解析" % len(refs)))
        return violations
    for i, ref in enumerate(refs):
        if ref not in ctx["decisions"]:
            violations.append(v("UNKNOWN_ID", "%s.decisions[%d]" % (where, i),
                                "%s 在 architecture.yaml 中不存在" % ref))
    return violations


def check_files(record, where, ctx, final):
    """files[] 现场勘察义务：update 型必须存在且带 current_state；--final 另需 preserve。"""
    violations = []
    files = record.get("files")
    if files is None:
        return [v("EMPTY_FIELD", where + ".files",
                  "files 缺失（本故事将触碰的文件；无文件写空列表）")]
    if not isinstance(files, list):
        return [v("EMPTY_FIELD", where + ".files", "files 不是列表")]
    if final and not files:
        violations.append(v("EMPTY_FIELD", where + ".files",
                            "--final 要求 files 非空（至少一个将触碰的文件）"))
    for i, item in enumerate(files):
        fw = "%s.files[%d]" % (where, i)
        if not isinstance(item, dict):
            violations.append(v("EMPTY_FIELD", fw, "file 条目不是映射"))
            continue
        path = item.get("path")
        action = item.get("action")
        if not nonempty(path):
            violations.append(v("EMPTY_FIELD", fw + ".path", "path 缺失"))
        elif not is_safe_rel(path):
            violations.append(v("ENUM_INVALID", fw + ".path",
                                "path 须为相对 project-root 的正斜杠路径，实为 %s" % path))
        if not nonempty(action):
            violations.append(v("EMPTY_FIELD", fw + ".action", "action 缺失（new|update）"))
        elif str(action) not in FILE_ACTIONS:
            violations.append(v("ENUM_INVALID", fw + ".action",
                                "action 越界：%s（合法集 %s）"
                                % (action, "|".join(FILE_ACTIONS))))
        if not nonempty(item.get("why")):
            violations.append(v("EMPTY_FIELD", fw + ".why", "why 缺失（一行说明该文件为何被触碰）"))
        if str(action) != "update" or not nonempty(path) or not is_safe_rel(path):
            continue
        if not os.path.isfile(rel_to_root(ctx["root"], path)):
            violations.append(v("MISSING_FILE", fw + ".path",
                                "update 目标不存在：%s（new 型才会被创建）" % path))
        if not nonempty(item.get("current_state")):
            violations.append(v("EMPTY_FIELD", fw + ".current_state",
                                "update 型必填：先读该文件，写它今天的行为"))
        elif final and not nonempty(item.get("preserve")):
            violations.append(v("EMPTY_FIELD", fw + ".preserve",
                                "--final 要求 update 型写明须保持的既有行为"))
    return violations


def text_list(record, key, where):
    """字符串列表键的形状校验（可缺席；缺席视为空）。"""
    value = record.get(key)
    if value is None:
        return []
    if not isinstance(value, list):
        return [v("EMPTY_FIELD", "%s.%s" % (where, key), "%s 不是列表" % key)]
    violations = []
    for i, item in enumerate(value):
        if not nonempty(item):
            violations.append(v("EMPTY_FIELD", "%s.%s[%d]" % (where, key, i),
                                "%s 项不得为空" % key))
    return violations


def check_final_duties(record, where, status):
    """--final 附加义务：status 已落 final、verify 非空、open_questions 闭合、零假设。"""
    violations = []
    if str(status) != "final":
        violations.append(v("STATUS_MISMATCH", where + ".status",
                            "--final 要求 status 已落 final（实为 %s）" % status))
    if not items(record, "verify"):
        violations.append(v("EMPTY_FIELD", where + ".verify",
                            "--final 要求 verify 非空（命令级完成判据）"))
    for i, question in enumerate(items(record, "open_questions")):
        if not str(question).startswith(CLOSED_PREFIX):
            violations.append(v("PENDING_DECISION", "%s.open_questions[%d]" % (where, i),
                                "open_questions 须清零或逐条以 %s 标注处置" % CLOSED_PREFIX))
    if any("[ASSUMPTION]" in s for s in collect_strings(record)):
        violations.append(v("ASSUMPTION_PRESENT", where,
                            "--final 要求零 [ASSUMPTION]；未决推断须先落定"))
    return violations


def check_record(index, record, ctx, final, where_base):
    where = "%s.contexts[%d]" % (where_base, index)
    if not isinstance(record, dict):
        return [v("EMPTY_FIELD", where, "记录不是映射")]
    violations = check_identity(record, where)
    story_entry, acs, story_violations = check_story_binding(record, where, ctx)
    violations += story_violations
    if story_entry is not None:
        acs = ac_ids(story_entry)
    violations += check_test_refs(record, where, ctx, acs)
    violations += check_decisions(record, where, ctx)
    violations += check_files(record, where, ctx, final)
    violations += text_list(record, "risks", where)
    violations += text_list(record, "verify", where)
    violations += text_list(record, "open_questions", where)
    prior = record.get("prior_story")
    if prior is not None and not isinstance(prior, dict):
        violations.append(v("EMPTY_FIELD", where + ".prior_story", "prior_story 不是映射"))
    elif isinstance(prior, dict):
        if not nonempty(prior.get("ref")):
            violations.append(v("EMPTY_FIELD", where + ".prior_story.ref", "ref 缺失（S-y）"))
        elif ctx["has_stories"] and str(prior["ref"]) not in ctx["stories"]:
            violations.append(v("UNKNOWN_ID", where + ".prior_story.ref",
                                "%s 在 stories.yaml 中不存在" % prior["ref"]))
        carry = prior.get("carryover")
        if carry is not None and not isinstance(carry, list):
            violations.append(v("EMPTY_FIELD", where + ".prior_story.carryover",
                                "carryover 不是列表"))
    if final:
        violations += check_final_duties(record, where, record.get("status"))
    return violations


def build_ctx(docs, root):
    return {
        "root": root,
        "has_stories": docs[STORIES_FILE]["present"] and docs[STORIES_FILE]["err"] is None,
        "has_test_plan": docs[TEST_PLAN_FILE]["present"] and docs[TEST_PLAN_FILE]["err"] is None,
        "has_arch": docs[ARCH_FILE]["present"] and docs[ARCH_FILE]["err"] is None,
        "stories": story_map(docs[STORIES_FILE]["data"]),
        "tcs": {str(tc["id"]): tc for tc in items(docs[TEST_PLAN_FILE]["data"], "test_cases")
                if isinstance(tc, dict) and nonempty(tc.get("id"))},
        "decisions": {str(d["id"]): d for d in items(docs[ARCH_FILE]["data"], "decisions")
                      if isinstance(d, dict) and nonempty(d.get("id"))},
    }


def cmd_check(args):
    root = os.path.abspath(args.project_root)
    out = os.path.abspath(args.output_dir)
    docs = load_docs(out)
    ctx = build_ctx(docs, root)
    path = os.path.join(out, CONTEXT_FILE)
    show = display_path(path, root)
    violations = []
    warnings = []
    records = []

    for name in (STORIES_FILE, TEST_PLAN_FILE, ARCH_FILE):
        if not docs[name]["present"]:
            warnings.append(missing_warning(
                out, name, "%s 缺席：相关引用解析降级（记录内逐条给出违规）" % name, root))

    data, err = load_yaml_safe(path)
    if data is None and err is None:
        violations.append(v("MISSING_FILE", show,
                            "%s 不存在（先完成一次 story 上下文包起草）" % CONTEXT_FILE))
    elif err is not None:
        violations.append(v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err))
    elif not isinstance(data, dict):
        violations.append(v("EMPTY_FIELD", show, "顶层不是映射（须为 project + contexts）"))
    else:
        project = data.get("project")
        if project is not None and not isinstance(project, dict):
            violations.append(v("EMPTY_FIELD", show + " project", "project 不是映射"))
        revisions = data.get("revisions")
        if revisions is not None and not isinstance(revisions, list):
            violations.append(v("EMPTY_FIELD", show + " revisions", "revisions 不是列表"))
        raw_records = data.get("contexts")
        if raw_records is None:
            violations.append(v("EMPTY_FIELD", show + " contexts",
                                "contexts 缺失（集合形态；无记录写空列表）"))
        elif not isinstance(raw_records, list):
            violations.append(v("EMPTY_FIELD", show + " contexts", "contexts 不是列表"))
        else:
            records = [r for r in raw_records
                       if not (args.story and isinstance(r, dict)
                               and str(r.get("story")) != args.story)]
            if args.story and not records:
                violations.append(v("UNKNOWN_ID", show + " contexts",
                                    "--story %s 无对应记录" % args.story))
            for i, record in enumerate(records):
                violations += check_record(i, record, ctx, args.final, show)
            seen_ids = set()
            seen_stories = set()
            for i, record in enumerate(records):
                if not isinstance(record, dict):
                    continue
                rid = record.get("id")
                if nonempty(rid):
                    if str(rid) in seen_ids:
                        violations.append(v("DUPLICATE_ID", "%s.contexts[%d].id" % (show, i),
                                            "记录 ID %s 重复（SC ID 稳定不重用）" % rid))
                    seen_ids.add(str(rid))
                story = record.get("story")
                if nonempty(story):
                    if str(story) in seen_stories:
                        violations.append(v("DUPLICATE_ID", "%s.contexts[%d].story" % (show, i),
                                            "%s 已有一条记录；按 story 键原位更新，不新增记录" % story))
                    seen_stories.add(str(story))
            if args.final and not records:
                violations.append(v("EMPTY_FIELD", show + " contexts",
                                    "--final 要求至少 1 条记录"))

    counts = {
        "contexts": len(records),
        "by_status": count_by(records, "status"),
        "files": count_items(records, "files"),
        "acs": count_items(records, "ac_refs"),
        "tcs": count_items(records, "tc_refs"),
        "open_questions": count_items(records, "open_questions"),
    }
    ok = not violations
    payload = base_payload("check", args, out)
    payload["ok"] = ok
    payload["final"] = args.final
    payload["violations"] = violations
    payload["warnings"] = warnings
    payload["counts"] = counts
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


def human_check(payload):
    if payload["ok"]:
        print("PASS：%s 校验通过（contexts=%d）"
              % (payload["output_dir"] + "/" + CONTEXT_FILE, payload["counts"]["contexts"]))
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
        description="diy-create-story 确定性引擎：目标 story 情报采集（只读）+ "
                    "story-context.yaml 校验")
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("collect", help="门禁 + AC/TC/前序/决策/git 采集（只读，不写盘）")
    c.add_argument("--story", required=True, help="目标 story ID（S-x）")
    c.add_argument("--project-root", default=".", help="项目根（默认 .）")
    c.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    c.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    c.set_defaults(func=cmd_collect)

    k = sub.add_parser("check", help="校验 story-context.yaml（schema/引用/现场勘察；--final 附加定稿义务）")
    k.add_argument("--story", default=None, help="只校验该 story 的记录（可省 → 全量）")
    k.add_argument("--project-root", default=".", help="项目根（默认 .）")
    k.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    k.add_argument("--final", action="store_true",
                   help="定稿校验：status 已落 final + verify/files/preserve 义务 + 零假设 + 未决清零")
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
