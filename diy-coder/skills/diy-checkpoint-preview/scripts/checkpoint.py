# -*- coding: utf-8 -*-
"""diy-checkpoint-preview 确定性引擎：变更候选定位（前置门禁）+ checkpoint.yaml 校验。

子命令：
  target  4 层级联定位被审变更，确定性部分不留给 LLM：
            1 显式 --ref（commit / range / 分支；PR 引用须先解析为本地 ref）
            2 {output_dir}/sprint.yaml 中 status: 待审查 的任务
            3 git 工作区改动 → HEAD 提交
            4 四者皆无 → 零产出 exit 1 + 结构化拒绝回执（含路由）
          只读检测，绝不写文件。环境健壮性：目录非 git 仓库 / 无提交 / 无 diff
          一律返回空候选 + 结构化原因，不崩溃。
          裸提交候选附意图判定（BMAD step-01:54）：提交信息 subject < 10 词 →
          inferred: true + 原因；工作区改动 / range 无单一提交信息 → null + 原因。
  check   校验 {output_dir}/checkpoint.yaml（顶层 project + checkpoints 集合，形状对齐
          bug-log.yaml）：schema / 枚举 / story 引用可解析 / change_type 出现时非空；
          --final 附加定稿义务（checkpoints 非空、concern 非空、decision 已定且非 讨论、
          status 已落 已定稿、next 非空、零 [假设]）。exit 0 唯一放行。

分工裁定（任务书 §2.3）：checkpoint 属新产物类型，不进 diyc.py check 的硬编码类型集；
本引擎沿用领域引擎形态（同 design.py 分工），契约同构：exit 0 唯一放行 / --json 单行回执 /
violations[{code, where, msg}] + counts。违规码复用 batch3-contract §3 冻结集，
新增 NO_TARGET（门禁拒绝专用）。

禁手写实例解析：引擎不做 --instance / 白名单 / 目录推导；--output-dir 必填，
由调用方传入（SKILL.md 从 diyc.py resolve 取）。产物与产物 ID 由 diy-checkpoint-preview
会话（LLM）创作——CK-0nn 由 LLM 铸造、本引擎只校验格式与唯一性。
"""
# trace: 迁移计划 §二 验收 #3（前置门禁零产出退出）/#4（ID 链接入）/#12（领域引擎接线）
import argparse
import io
import json
import os
import re
import subprocess
import sys

import yaml

CK_FILE = "checkpoint.yaml"
SPRINT_FILE = "sprint.yaml"
STORIES_FILE = "stories.yaml"

TARGET_SOURCES = ("显式指定", "冲刺任务", "Git 提交")
MODES = ("全程轨迹", "仅规格", "裸提交")
DECISIONS = ("批准", "返工", "讨论")
RECORD_STATUSES = ("草稿", "已定稿")
RISK_LABELS = ("认证", "公开 API", "数据模型", "计费", "基础设施", "安全",
               "配置", "其他")
WORKTREE_REF = "WORKTREE"

CK_RE = re.compile(r"CK-\d{3}")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
# BMAD step-01-orientation.md:54 —— "commit message is terse (under 10 words)" → 标 [inferred]
TERSE_WORDS = 10


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


# ---- git 层（只读；任何失败都降级为结构化原因，不抛异常） ----

def git(root, *args):
    """执行 git 子命令 → (rc, stdout, stderr)；git 可执行文件不可用 → (None, "", 原因)。"""
    try:
        p = subprocess.run(["git", "-C", root] + list(args),
                           capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
    except OSError as e:
        return None, "", str(e)
    return p.returncode, p.stdout, p.stderr


def is_git_repo(root):
    rc, out, _ = git(root, "rev-parse", "--is-inside-work-tree")
    return rc == 0 and out.strip() == "true"


def numstat_totals(root, *git_args):
    """git --numstat 输出聚合 → (files, insertions, deletions)；失败 → 全 0。"""
    rc, out, _ = git(root, *git_args)
    if rc != 0:
        return 0, 0, 0
    files = ins = dele = 0
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        files += 1
        ins += int(parts[0]) if parts[0].isdigit() else 0
        dele += int(parts[1]) if parts[1].isdigit() else 0
    return files, ins, dele


def commit_subject(root, ref):
    """单一提交的 subject 行；取不到（未知 ref / 非提交对象）→ None。"""
    rc, out, _ = git(root, "log", "-1", "--format=%s", ref)
    if rc != 0:
        return None
    return out.strip() or None


def intent_flag(root, commit_ref):
    """BMAD step-01 bare-commit 语义：意图源 = 提交信息；terse（< 10 词）→ 标 [inferred]。

    返回 (inferred, reason)：True/False = 已判定；None = 无单一提交信息可判定
    （工作区未提交改动 / range），交由人从 diff 核对。
    """
    subject = commit_subject(root, commit_ref)
    if subject is None:
        return None, "无单一提交信息可判定，意图从 diff 推断，请人工核对"
    words = len(subject.split())
    if words < TERSE_WORDS:
        return True, ("提交信息过短（%d 词 < %d），意图从 diff 推断，请人工核对"
                      % (words, TERSE_WORDS))
    return False, None


def candidate(ref, source, story=None, spec=None, mode="裸提交", diff_stat=None,
              inferred=None, inferred_reason=None):
    return {"ref": ref, "source": source, "story": story, "spec": spec,
            "mode": mode, "diff_stat": diff_stat,
            "inferred": inferred, "inferred_reason": inferred_reason}


def stat_dict(files, ins, dele):
    return {"files": files, "insertions": ins, "deletions": dele}


def explicit_candidate(root, ref):
    """层 1：显式 ref。返回 (候选 | None, 原因)。PR 引用无法本地解析 → 拒绝并给路由。"""
    if not is_git_repo(root):
        return None, "--ref %s 无法解析：项目不是 git 仓库" % ref
    if ".." in ref:
        rc, out, _ = git(root, "rev-list", "--count", ref)
        if rc != 0 or not out.strip():
            return None, "--ref %s 无法解析为 git range" % ref
        files, ins, dele = numstat_totals(root, "diff", "--numstat", ref)
        return candidate(ref, "显式指定", diff_stat=stat_dict(files, ins, dele),
                         inferred=None,
                         inferred_reason="range 无单一提交信息，意图从 diff 推断，请人工核对"), None
    rc, out, _ = git(root, "rev-parse", "--verify", "--quiet", ref + "^{commit}")
    if rc != 0 or not out.strip():
        return None, ("--ref %s 无法解析（PR 引用请先用 gh 解析为本地 commit/分支）" % ref)
    files, ins, dele = numstat_totals(root, "show", "--numstat", "--format=", ref)
    inferred, reason = intent_flag(root, ref)
    return candidate(ref, "显式指定", diff_stat=stat_dict(files, ins, dele),
                     inferred=inferred, inferred_reason=reason), None


def load_story_index(output_dir):
    """story 索引：{story_id: stories.yaml 条目 | None}。上游文件损坏 → warnings（不静默）。"""
    index = {}
    warnings = []
    sources = ((STORIES_FILE, "stories", None), (SPRINT_FILE, "tasks", "story"))
    for filename, key, sub in sources:
        path = os.path.join(output_dir, filename)
        data, err = load_yaml_safe(path)
        if err is not None:
            warnings.append(v("UNPARSABLE_YAML", filename,
                              "上游文档不可解析，story 引用无法核验：%s" % err))
            continue
        items = data.get(key) if isinstance(data, dict) else None
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            sid = item.get(sub) if sub else item.get("id")
            if nonempty(sid):
                index.setdefault(str(sid), None if sub else item)
    return index, warnings


def sprint_candidates(output_dir, project_root):
    """层 2：sprint.yaml 中 status: 待审查 的任务（取其 story 与 spec 锚点）。"""
    path = os.path.join(output_dir, SPRINT_FILE)
    data, err = load_yaml_safe(path)
    if data is None and err is None:
        return [], [], "%s 不存在" % display_path(path, project_root)
    if err is not None:
        return [], [], "%s 不可解析" % display_path(path, project_root)
    tasks = data.get("tasks") if isinstance(data, dict) else None
    if not isinstance(tasks, list):
        return [], [], "%s 无 tasks 列表" % display_path(path, project_root)
    reviews = [t for t in tasks if isinstance(t, dict) and t.get("status") == "待审查"]
    if not reviews:
        return [], [], "%s 中无 status: 待审查 的任务" % display_path(path, project_root)
    index, warnings = load_story_index(output_dir)
    stories_path = os.path.join(output_dir, STORIES_FILE)
    cands = []
    for task in reviews:
        sid = task.get("story")
        entry = index.get(str(sid)) if nonempty(sid) else None
        if entry is not None:
            spec = display_path(stories_path, project_root)
            # 全程轨迹仅在 spec 携带审查顺序（suggested_review_order 非空）时成立
            mode = "全程轨迹" if entry.get("suggested_review_order") else "仅规格"
        else:
            spec, mode = None, "裸提交"
        # 冲刺任务候选的意图锚点是 story/spec，不走提交信息判定（[inferred] 属裸提交路径）
        cands.append(candidate(None, "冲刺任务", story=str(sid) if nonempty(sid) else None,
                               spec=spec, mode=mode))
    return cands, warnings, "命中 %d 个 status: 待审查 的任务" % len(cands)


def git_candidates(root):
    """层 3：git 工作区改动 → HEAD 提交。返回 (候选列表, 原因)。"""
    if not is_git_repo(root):
        return [], "非 git 仓库（或 git 不可用）"
    rc, out, _ = git(root, "status", "--porcelain")
    if rc != 0:
        return [], "git status 执行失败"
    changed = [line for line in out.splitlines() if line.strip()]
    if changed:
        head_ok = git(root, "rev-parse", "--verify", "--quiet", "HEAD")[0] == 0
        args = ["diff", "--numstat", "HEAD"] if head_ok else ["diff", "--numstat"]
        _, ins, dele = numstat_totals(root, *args)
        return [candidate(WORKTREE_REF, "Git 提交",
                          diff_stat=stat_dict(len(changed), ins, dele),
                          inferred=None,
                          inferred_reason="工作区未提交改动无提交信息，意图从 diff 推断，请人工核对"
                          )], None
    rc, out, _ = git(root, "rev-parse", "--short", "HEAD")
    if rc == 0 and out.strip():
        sha = out.strip()
        files, ins, dele = numstat_totals(root, "show", "--numstat", "--format=", "HEAD")
        inferred, reason = intent_flag(root, "HEAD")
        return [candidate(sha, "Git 提交", diff_stat=stat_dict(files, ins, dele),
                          inferred=inferred, inferred_reason=reason)], None
    return [], "git 仓库无提交且工作区干净（无 diff）"


# ---- target 收口 ----

def cmd_target(args):
    root = os.path.abspath(args.project_root)
    out = args.output_dir
    checked = []
    warnings = []
    candidates = []

    if nonempty(args.ref):
        cand, why = explicit_candidate(root, args.ref)
        checked.append({"source": "显式指定", "hit": cand is not None, "reason": why})
        if cand is not None:
            candidates.append(cand)
    else:
        checked.append({"source": "显式指定", "hit": False, "reason": "未提供 --ref"})

    if not candidates:
        cands, warns, why = sprint_candidates(out, root)
        warnings += warns
        checked.append({"source": "冲刺任务", "hit": bool(cands), "reason": why})
        candidates += cands

    if not candidates:
        cands, why = git_candidates(root)
        checked.append({"source": "Git 提交", "hit": bool(cands), "reason": why})
        candidates += cands

    ok = bool(candidates)
    first = candidates[0] if candidates else {}
    reason = None
    violations = []
    if not ok:
        reason = ("未定位到被审变更：%s。请显式传 --ref（commit / range / 分支），"
                  "或先跑 diy-dev / diy-review 使任务进入 待审查 后重试。"
                  % "；".join(c["reason"] for c in checked))
        violations = [v("NO_TARGET", display_path(os.path.join(out, CK_FILE), root), reason)]
    payload = {
        "ok": ok,
        "command": "target",
        "project_root": args.project_root,
        "output_dir": os.path.normpath(out).replace("\\", "/"),
        "ref": first.get("ref"),
        "source": first.get("source"),
        "mode": first.get("mode"),
        "story": first.get("story"),
        "spec": first.get("spec"),
        "diff_stat": first.get("diff_stat"),
        "inferred": first.get("inferred"),
        "inferred_reason": first.get("inferred_reason"),
        "candidates": candidates,
        "checked": checked,
        "violations": violations,
        "warnings": warnings,
        "reason": reason,
        "counts": {"candidates": len(candidates)},
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        if ok:
            print("已定位被审变更候选 %d 个（首选项 source=%s）：" % (len(candidates),
                                                              first.get("source")))
            for c in candidates:
                detail = c.get("story") or c.get("ref") or "-"
                flag = " [inferred]" if c.get("inferred") else ""
                print("- [%s] %s spec=%s mode=%s%s" % (c["source"], detail,
                                                       c.get("spec"), c["mode"], flag))
        else:
            print("拒绝：%s" % reason)
    return 0 if ok else 1


# ---- check ----

def collect_strings(node):
    """递归收集映射/列表内的全部字符串（键与值）——[假设] 扫描用。"""
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


def check_concerns(record, where):
    violations = []
    concerns = record.get("concerns")
    if concerns is None:
        return [v("EMPTY_FIELD", where + ".concerns", "concerns 缺失")]
    if not isinstance(concerns, list):
        return [v("EMPTY_FIELD", where + ".concerns", "concerns 不是列表")]
    for i, concern in enumerate(concerns):
        cw = "%s.concerns[%d]" % (where, i)
        if not isinstance(concern, dict):
            violations.append(v("EMPTY_FIELD", cw, "concern 不是映射"))
            continue
        for key in ("name", "why"):
            if not nonempty(concern.get(key)):
                violations.append(v("EMPTY_FIELD", cw + "." + key, "%s 为空" % key))
        sites = concern.get("sites")
        if not isinstance(sites, list):
            violations.append(v("EMPTY_FIELD", cw + ".sites", "sites 缺失或不是列表"))
            continue
        for j, site in enumerate(sites):
            if not nonempty(site):
                violations.append(v("EMPTY_FIELD", "%s.sites[%d]" % (cw, j),
                                    "site 为空（须为 path:line）"))
    return violations


def check_risks(record, where):
    violations = []
    risks = record.get("risks")
    if risks is None:
        return [v("EMPTY_FIELD", where + ".risks", "risks 缺失（无高风险点写空列表）")]
    if not isinstance(risks, list):
        return [v("EMPTY_FIELD", where + ".risks", "risks 不是列表")]
    for i, risk in enumerate(risks):
        rw = "%s.risks[%d]" % (where, i)
        if not isinstance(risk, dict):
            violations.append(v("EMPTY_FIELD", rw, "risk 不是映射"))
            continue
        label = risk.get("label")
        if not nonempty(label):
            violations.append(v("EMPTY_FIELD", rw + ".label", "label 为空"))
        elif str(label) not in RISK_LABELS:
            violations.append(v("ENUM_INVALID", rw + ".label",
                                "label 越界：%s（合法集 %s）" % (label, "|".join(RISK_LABELS))))
        for key in ("where", "why"):
            if not nonempty(risk.get(key)):
                violations.append(v("EMPTY_FIELD", rw + "." + key, "%s 为空" % key))
    return violations


def check_observations(record, where):
    violations = []
    items = record.get("observations")
    if items is None:
        return [v("EMPTY_FIELD", where + ".observations",
                  "observations 缺失（无观察点写空列表）")]
    if not isinstance(items, list):
        return [v("EMPTY_FIELD", where + ".observations", "observations 不是列表")]
    for i, obs in enumerate(items):
        ow = "%s.observations[%d]" % (where, i)
        if not isinstance(obs, dict):
            violations.append(v("EMPTY_FIELD", ow, "observation 不是映射"))
            continue
        for key in ("do", "watch"):
            if not nonempty(obs.get(key)):
                violations.append(v("EMPTY_FIELD", ow + "." + key, "%s 为空" % key))
    return violations


def check_record(index, record, final, story_ids, where_base):
    violations = []
    where = "%s.checkpoints[%d]" % (where_base, index)
    if not isinstance(record, dict):
        return [v("EMPTY_FIELD", where, "记录不是映射")]

    rid = record.get("id")
    if not nonempty(rid):
        violations.append(v("EMPTY_FIELD", where + ".id", "id 缺失"))
    elif not CK_RE.fullmatch(str(rid)):
        violations.append(v("ENUM_INVALID", where + ".id",
                            "id 须为 CK-0nn（三位零填充），实为 %s" % rid))

    date = record.get("date")
    if not nonempty(date):
        violations.append(v("EMPTY_FIELD", where + ".date", "date 缺失"))
    elif not DATE_RE.fullmatch(str(date)):
        violations.append(v("ENUM_INVALID", where + ".date",
                            "date 须为 YYYY-MM-DD，实为 %s" % date))

    # §8.3 裁定：change_type 为开放字符串（commit|branch|PR|<自由文本>，默认 change）——
    # 可选、出现时非空即可；禁封闭枚举（用户自然语言命名不得被误判）
    change_type = record.get("change_type")
    if change_type is not None and not nonempty(change_type):
        violations.append(v("EMPTY_FIELD", where + ".change_type",
                            "change_type 出现时不得为空（开放字符串，默认 change）"))

    target = record.get("target")
    if not isinstance(target, dict):
        violations.append(v("EMPTY_FIELD", where + ".target", "target 缺失或不是映射"))
    else:
        source = target.get("source")
        if not nonempty(source):
            violations.append(v("EMPTY_FIELD", where + ".target.source", "source 缺失"))
        elif str(source) not in TARGET_SOURCES:
            violations.append(v("ENUM_INVALID", where + ".target.source",
                                "source 越界：%s（合法集 %s）"
                                % (source, "|".join(TARGET_SOURCES))))
        elif str(source) == "显式指定" and not nonempty(target.get("ref")):
            violations.append(v("EMPTY_FIELD", where + ".target.ref",
                                "source=显式指定 时 ref 必填"))
        elif str(source) == "冲刺任务" and not nonempty(target.get("story")):
            violations.append(v("EMPTY_FIELD", where + ".target.story",
                                "source=冲刺任务 时 story 必填"))
        story = target.get("story")
        if nonempty(story) and str(story) not in story_ids:
            violations.append(v("UNKNOWN_ID", where + ".target.story",
                                "story %s 在 %s / %s 中均不可解析"
                                % (story, STORIES_FILE, SPRINT_FILE)))
        if "inferred" in target and not isinstance(target.get("inferred"), bool):
            violations.append(v("ENUM_INVALID", where + ".target.inferred",
                                "inferred 若给出须为布尔（true|false）"))

    mode = record.get("mode")
    if not nonempty(mode):
        violations.append(v("EMPTY_FIELD", where + ".mode", "mode 缺失"))
    elif str(mode) not in MODES:
        violations.append(v("ENUM_INVALID", where + ".mode",
                            "mode 越界：%s（合法集 %s）" % (mode, "|".join(MODES))))

    decision = record.get("decision")
    if nonempty(decision) and str(decision) not in DECISIONS:
        violations.append(v("ENUM_INVALID", where + ".decision",
                            "decision 越界：%s（合法集 %s）"
                            % (decision, "|".join(DECISIONS))))

    status = record.get("status")
    if not nonempty(status):
        violations.append(v("EMPTY_FIELD", where + ".status", "status 缺失"))
    elif str(status) not in RECORD_STATUSES:
        violations.append(v("ENUM_INVALID", where + ".status",
                            "status 越界：%s（合法集 %s）"
                            % (status, "|".join(RECORD_STATUSES))))

    violations += check_concerns(record, where)
    violations += check_risks(record, where)
    violations += check_observations(record, where)

    if final:
        violations += check_final_duties(record, where, decision, status)
    return violations


def check_final_duties(record, where, decision, status):
    """--final 附加义务：decision 已定（非 讨论）、status 已落 已定稿、next 非空、零假设。"""
    violations = []
    if not nonempty(decision):
        violations.append(v("PENDING_DECISION", where + ".decision",
                            "--final 要求 decision 已定（批准|返工）；讨论后回到决策"))
    elif str(decision) == "讨论":
        if str(status) == "已定稿":
            violations.append(v("STATUS_MISMATCH", where + ".status",
                                "讨论决策不得落 status: 已定稿"))
        else:
            violations.append(v("PENDING_DECISION", where + ".decision",
                                "讨论未收敛：讨论后须回到 批准|返工 再定稿"))
    elif str(status) != "已定稿":
        violations.append(v("STATUS_MISMATCH", where + ".status",
                            "decision 已定（%s），须落 status: 已定稿" % decision))
    if not nonempty(record.get("next")):
        violations.append(v("EMPTY_FIELD", where + ".next", "--final 要求 next 路由行非空"))
    concerns = record.get("concerns")
    if isinstance(concerns, list) and not concerns:
        violations.append(v("EMPTY_FIELD", where + ".concerns",
                            "--final 要求至少 1 个 concern"))
    if any("[假设]" in s for s in collect_strings(record)):
        violations.append(v("ASSUMPTION_PRESENT", where,
                            "--final 要求零 [假设]；未决假设须先落定"))
    return violations


def count_by(records, key):
    """按记录顶层字段值计数（空值跳过）；key='target' 时取 target.source。"""
    counts = {}
    for record in records:
        if not isinstance(record, dict):
            continue
        value = record.get(key)
        if key == "target" and isinstance(value, dict):
            value = value.get("source")
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


def cmd_check(args):
    root = os.path.abspath(args.project_root)
    out = args.output_dir
    path = os.path.join(out, CK_FILE)
    show = display_path(path, root)
    violations = []
    warnings = []
    records = []

    data, err = load_yaml_safe(path)
    if data is None and err is None:
        violations.append(v("MISSING_FILE", show,
                            "%s 不存在（先完成一次 checkpoint 起草）" % CK_FILE))
    elif err is not None:
        violations.append(v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err))
    elif not isinstance(data, dict):
        violations.append(v("EMPTY_FIELD", show, "顶层不是映射（须为 project + checkpoints）"))
    else:
        # §8.2 裁定：project 形状为 {name, created, updated}，状态挂记录级（不要求 project.status）
        project = data.get("project")
        if project is not None and not isinstance(project, dict):
            violations.append(v("EMPTY_FIELD", show + " project", "project 不是映射"))
        revisions = data.get("revisions")
        if revisions is not None and not isinstance(revisions, list):
            violations.append(v("EMPTY_FIELD", show + " revisions", "revisions 不是列表"))
        raw_records = data.get("checkpoints")
        if raw_records is None:
            violations.append(v("EMPTY_FIELD", show + " checkpoints",
                                "checkpoints 缺失（集合形态；无记录写空列表）"))
        elif not isinstance(raw_records, list):
            violations.append(v("EMPTY_FIELD", show + " checkpoints", "checkpoints 不是列表"))
        else:
            records = raw_records
            story_ids, index_warnings = load_story_index(out)
            warnings += index_warnings
            seen = set()
            for i, record in enumerate(records):
                violations += check_record(i, record, args.final, story_ids, show)
                if isinstance(record, dict) and nonempty(record.get("id")):
                    rid = str(record["id"])
                    if rid in seen:
                        violations.append(v("DUPLICATE_ID", "%s.checkpoints[%d].id" % (show, i),
                                            "记录 ID %s 重复（CK ID 稳定不重用）" % rid))
                    seen.add(rid)
            if args.final and not records:
                violations.append(v("EMPTY_FIELD", show + " checkpoints",
                                    "--final 要求至少 1 条记录"))

    counts = {
        "checkpoints": len(records),
        "by_decision": count_by(records, "decision"),
        "by_status": count_by(records, "status"),
        "by_source": count_by(records, "target"),
        "concerns": count_items(records, "concerns"),
        "risks": count_items(records, "risks"),
        "observations": count_items(records, "observations"),
    }
    ok = not violations
    payload = {
        "ok": ok,
        "command": "check",
        "project_root": args.project_root,
        "output_dir": os.path.normpath(out).replace("\\", "/"),
        "final": args.final,
        "violations": violations,
        "warnings": warnings,
        "counts": counts,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        if ok:
            print("PASS：%s 校验通过（checkpoints=%d）" % (show, len(records)))
        else:
            print("FAIL：")
            for item in violations:
                print("- %s %s: %s" % (item["code"], item["where"], item["msg"]))
    return 0 if ok else 1


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(
        description="diy-checkpoint-preview 确定性引擎：变更候选定位（门禁）+ checkpoint.yaml 校验")
    sub = ap.add_subparsers(dest="cmd", required=True)

    t = sub.add_parser("target", help="4 层级联定位被审变更（显式 ref → 冲刺任务待审查态 → Git 提交）")
    t.add_argument("--project-root", default=".", help="项目根（默认 .）")
    t.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    t.add_argument("--ref", default=None, help="显式变更锚点（commit / range / 分支）")
    t.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    t.set_defaults(func=cmd_target)

    c = sub.add_parser("check", help="校验 checkpoint.yaml（schema/枚举/引用；--final 附加定稿义务）")
    c.add_argument("--project-root", default=".", help="项目根（默认 .）")
    c.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    c.add_argument("--final", action="store_true", help="定稿校验：decision 已定 + status 已落 已定稿 + 零假设")
    c.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    c.set_defaults(func=cmd_check)

    args = ap.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
