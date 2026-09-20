# -*- coding: utf-8 -*-
"""diy-product-brief 确定性引擎：intent 门禁（前置条件 + 路由）+ brief.yaml 校验。

子命令：
  intent  解析 intent（新建/更新/校验）的前置条件并给路由，确定性部分不留给 LLM：
            新建 → 不要求产物在场；产物已存在 → warning（resume/更新 语义，不得静默覆盖）
            更新 → {output_dir}/brief.yaml 必须存在
            校验 → 同上
          缺席且 intent ∈ {更新, 校验} → 零产出 exit 1 + 一行理由 + 路由（先新建）。
          只读检测，绝不写文件；回执给出 status 与 counts（读取成本纪律：模型读回执不读全文）。
  check   校验 {output_dir}/brief.yaml（单文档 + 附属集合，顶层 project 载文档级 status）：
            形状：project / brief 映射；decisions / addendum / revisions 列表
            枚举：project.status(草稿|已定稿)、stakes(个人兴趣|内部|投资人|公开)、
                  decisions[].status(生效|已反转)
            ID：BD-### 三位零填充、集合内唯一（稳定不重用不重编号，铸造权在会话）
            日期：YYYY-MM-DD
            内容：decision 文本、users[].who/need、value[].point、addendum 三键（section/
                  content/why_separate）恒非空；起草期容许叙事字段半写（实时持久化的前提）
          --previous PATH：读旧稿快照，比对 BD-### 集合，旧有新无 → ID_UNSTABLE（update 模式防丢决策）
          --final 附加定稿义务：project.status 已落「已定稿」、零 [假设]（含 assumptions 清空）、
                  title/problem/solution/users 非空、每条 decision 有 rationale。exit 0 唯一放行。
          --final 附加评审证据链（任务书 §12.1 ①ⓒ 六条）：顶层 review_refs 非空（缺失或空 →
                  EVIDENCE_MISSING）；{output_dir}/editorial-review.yaml 在场（缺席 →
                  MISSING_FILE）；每个 ID 在该台账 reviews[] 内（否则 UNKNOWN_ID）；该记录
                  status: 已定稿（否则 STATUS_MISMATCH）；其 target 归一化后指向本 brief.yaml
                  （否则 EVIDENCE_MISSING）；其 lenses 同时含 结构 与 文风（否则 EVIDENCE_MISSING）。
                  target 归一化四步顺序不可换：normpath → 统一正斜杠 → 相对 project-root →
                  比较（指向别处的记录不构成本文档的证据）。派发不可用（环境缺本技能的同套件
                  兄弟 diy-editorial-review 引擎）→ TOOL_MISSING warning 降级：六条一并转
                  warning、--final 放行（环境问题；技能在场而记录缺失或不合格仍硬拒）。

分工裁定（任务书 §2.2/§2.3）：brief 属新产物类型，不进 diyc.py check 的硬编码类型集；
本引擎沿用领域引擎形态（同 checkpoint.py / design.py），契约同构：exit 0 唯一放行 /
--json 单行回执 / violations[{code, where, msg}] + warnings + counts。违规码全部复用
batch3-contract §3 冻结集（MISSING_FILE UNPARSABLE_YAML EMPTY_FIELD ENUM_INVALID
DUPLICATE_ID ID_UNSTABLE ASSUMPTION_PRESENT STATUS_MISMATCH EVIDENCE_MISSING
UNKNOWN_ID），无新增码；降级 warning 码 TOOL_MISSING（兄弟引擎缺席专用，同 readiness 先例）。

禁手写实例解析：引擎不做 --instance / 白名单 / 目录推导；--output-dir 必填，由调用方传入
（SKILL.md 从 diyc.py resolve 取）。产物与产物 ID 由 diy-product-brief 会话（LLM）创作——
BD-0nn 由 LLM 铸造、本引擎只校验格式与唯一性；引擎全程只读，不写任何文件。
"""
# trace: B1 diy-product-brief 验收 #3（前置门禁零产出退出）/#4（ID 链接入）/#12（领域引擎接线）
import argparse
import io
import json
import os
import re
import sys

import yaml

BRIEF_FILE = "brief.yaml"
REVIEW_FILE = "editorial-review.yaml"
REVIEW_SCRIPT_REL = ("diy-editorial-review", "scripts", "editorial_review.py")
REVIEW_STATUS = "已定稿"
REVIEW_LENSES = ("结构", "文风")
INTENTS = ("新建", "更新", "校验")
ROUTES = {
    "新建": "steps/01-discovery.md",
    "更新": "steps/04-update.md",
    "校验": "steps/05-validate.md",
}
DOC_STATUSES = ("草稿", "已定稿")
STAKES = ("个人兴趣", "内部", "投资人", "公开")
DECISION_STATUSES = ("生效", "已反转")

BD_RE = re.compile(r"BD-\d{3}")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


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


def normalize_rel(value, project_root):
    """target 归一化（任务书 §12.1 ①ⓒ(5)，**四步顺序不可换**）：① `os.path.normpath`
    → ② `replace("\\", "/")` 统一正斜杠（Windows 下 ① 产反斜杠）→ ③ 转为相对
    `project_root` 的形式 → ④ 返回比较用串。两侧——ER 记录的 `target` 与本
    `brief.yaml`——各跑一次再一次比较；指向别处的记录不构成本文档的证据。"""
    step = os.path.normpath(str(value)).replace("\\", "/")           # ① ②
    absolute = step if os.path.isabs(step) else os.path.join(project_root, step)
    try:
        rel = os.path.relpath(absolute, project_root)                # ③
    except ValueError:                                               # 跨盘（Windows）不可相对化
        return os.path.abspath(absolute).replace("\\", "/")
    if rel.startswith(".."):                                         # 越界（对齐 display_path）
        return os.path.abspath(absolute).replace("\\", "/")
    return rel.replace("\\", "/")


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


def emit(payload, as_json, human_lines):
    """打印回执并返回 exit code（ok=true → 0，否则 1）。"""
    if as_json:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        for line in human_lines:
            print(line)
    return 0 if payload["ok"] else 1


# ---- intent（前置门禁 + 路由） ----

def cmd_intent(args):
    root = os.path.abspath(args.project_root)
    out = args.output_dir
    intent = args.intent
    path = os.path.join(out, BRIEF_FILE)
    show = display_path(path, root)
    exists = os.path.isfile(path)
    violations = []
    warnings = []
    counts = {}
    status = None

    if intent in ("更新", "校验") and not exists:
        violations.append(v("MISSING_FILE", show,
                            "%s 不存在：%s 需要既有产物；先跑「新建」（%s）"
                            % (BRIEF_FILE, intent, ROUTES["新建"])))
    if exists:
        data, err = load_yaml_safe(path)
        if err is not None:
            violations.append(v("UNPARSABLE_YAML", show,
                                "既有产物不可解析，无法确认可用：%s" % err))
        elif isinstance(data, dict):
            project = data.get("project")
            if isinstance(project, dict):
                status = project.get("status")
            brief = data.get("brief") if isinstance(data.get("brief"), dict) else {}
            decisions = data.get("decisions") if isinstance(data.get("decisions"), list) else []
            counts = {
                "decisions": sum(1 for d in decisions if isinstance(d, dict)),
                "decisions_by_status": count_by(decisions, "status"),
                "open_questions": list_len(brief.get("open_questions")),
                "addendum": list_len(data.get("addendum")),
                "revisions": list_len(data.get("revisions")),
            }
        if intent == "新建":
            warnings.append(v("STATUS_MISMATCH", show,
                              "已存在 brief.yaml（status=%s）：「新建」须先与用户确认 resume"
                              "或改走「更新」，禁止静默覆盖" % (status or "未知")))

    ok = not violations
    reason = None
    if not ok:
        reason = "；".join(x["msg"] for x in violations)
    payload = {
        "ok": ok,
        "command": "intent",
        "project_root": args.project_root,
        "output_dir": os.path.normpath(out).replace("\\", "/"),
        "intent": intent,
        "file": show,
        "exists": exists,
        "status": status,
        "route": ROUTES[intent],
        "violations": violations,
        "warnings": warnings,
        "reason": reason,
        "counts": counts,
    }
    if ok:
        human = ["intent=%s：%s（%s）→ 读 %s"
                 % (intent, show, status if exists else "不存在", ROUTES[intent])]
        human += ["WARNING %s" % w["msg"] for w in warnings]
    else:
        human = ["拒绝：%s" % reason]
    return emit(payload, args.json, human)


def list_len(value):
    return len(value) if isinstance(value, list) else 0


def count_by(items, key):
    counts = {}
    for item in items:
        if isinstance(item, dict) and nonempty(item.get(key)):
            value = str(item[key])
            counts[value] = counts.get(value, 0) + 1
    return counts


# ---- check ----

def check_text_list(value, where, label, violations):
    """字符串列表：非列表 → EMPTY_FIELD；元素空或非标量 → EMPTY_FIELD。"""
    if value is None or (isinstance(value, list) and not value):
        return []
    if not isinstance(value, list):
        violations.append(v("EMPTY_FIELD", where, "%s 不是列表" % label))
        return []
    for i, item in enumerate(value):
        if isinstance(item, (dict, list)) or not nonempty(item):
            violations.append(v("EMPTY_FIELD", "%s[%d]" % (where, i), "%s 条目为空" % label))
    return value


def check_pairs(value, where, keys, label, violations, optional=()):
    """映射列表：每项须为映射；keys 恒非空；optional 键出现时不得为空。"""
    if value is None:
        return
    if not isinstance(value, list):
        violations.append(v("EMPTY_FIELD", where, "%s 不是列表" % label))
        return
    for i, item in enumerate(value):
        iw = "%s[%d]" % (where, i)
        if not isinstance(item, dict):
            violations.append(v("EMPTY_FIELD", iw, "%s 条目不是映射" % label))
            continue
        for key in list(keys) + [k for k in optional if k in item]:
            if not nonempty(item.get(key)):
                violations.append(v("EMPTY_FIELD", "%s.%s" % (iw, key), "%s 为空" % key))


def check_brief_section(brief, where, final, violations):
    if brief is None:
        violations.append(v("EMPTY_FIELD", where, "brief 缺失（单文档主体）"))
        return {}
    if not isinstance(brief, dict):
        violations.append(v("EMPTY_FIELD", where, "brief 不是映射"))
        return {}

    stakes = brief.get("stakes")
    if nonempty(stakes) and str(stakes) not in STAKES:
        violations.append(v("ENUM_INVALID", where + ".stakes",
                            "stakes 越界：%s（合法集 %s）" % (stakes, "|".join(STAKES))))

    check_pairs(brief.get("users"), where + ".users", ("who", "need"), "users", violations)
    check_pairs(brief.get("value"), where + ".value", ("point",), "value", violations,
                optional=("evidence",))
    check_pairs(brief.get("extra_sections"), where + ".extra_sections",
                ("name", "content"), "extra_sections", violations)
    check_text_list(brief.get("open_questions"), where + ".open_questions",
                    "open_questions", violations)
    check_text_list(brief.get("assumptions"), where + ".assumptions",
                    "assumptions", violations)

    if final:
        for key in ("title", "problem", "solution"):
            if not nonempty(brief.get(key)):
                violations.append(v("EMPTY_FIELD", "%s.%s" % (where, key),
                                    "--final 要求 %s 非空" % key))
        users = brief.get("users")
        if not isinstance(users, list) or not users:
            violations.append(v("EMPTY_FIELD", where + ".users",
                                "--final 要求 users 非空"))
        if isinstance(brief.get("assumptions"), list) and brief["assumptions"]:
            violations.append(v("ASSUMPTION_PRESENT", where + ".assumptions",
                                "--final 要求 assumptions 清空（未决假设先落定或转 open_questions）"))
    return brief


def check_decisions(decisions, where, final, violations):
    if decisions is None:
        return []
    if not isinstance(decisions, list):
        violations.append(v("EMPTY_FIELD", where, "decisions 不是列表"))
        return []
    seen = set()
    for i, item in enumerate(decisions):
        iw = "%s[%d]" % (where, i)
        if not isinstance(item, dict):
            violations.append(v("EMPTY_FIELD", iw, "decision 条目不是映射"))
            continue
        rid = item.get("id")
        if not nonempty(rid):
            violations.append(v("EMPTY_FIELD", iw + ".id", "id 缺失"))
        elif not BD_RE.fullmatch(str(rid)):
            violations.append(v("ENUM_INVALID", iw + ".id",
                                "id 须为 BD-0nn（三位零填充），实为 %s" % rid))
        elif str(rid) in seen:
            violations.append(v("DUPLICATE_ID", iw + ".id",
                                "决策 ID %s 重复（BD ID 稳定不重用）" % rid))
        else:
            seen.add(str(rid))
        date = item.get("date")
        if not nonempty(date):
            violations.append(v("EMPTY_FIELD", iw + ".date", "date 缺失"))
        elif not DATE_RE.fullmatch(str(date)):
            violations.append(v("ENUM_INVALID", iw + ".date",
                                "date 须为 YYYY-MM-DD，实为 %s" % date))
        if not nonempty(item.get("decision")):
            violations.append(v("EMPTY_FIELD", iw + ".decision", "decision 为空"))
        status = item.get("status")
        if not nonempty(status):
            violations.append(v("EMPTY_FIELD", iw + ".status", "status 缺失"))
        elif str(status) not in DECISION_STATUSES:
            violations.append(v("ENUM_INVALID", iw + ".status",
                                "status 越界：%s（合法集 %s）"
                                % (status, "|".join(DECISION_STATUSES))))
        if final and not nonempty(item.get("rationale")):
            violations.append(v("EMPTY_FIELD", iw + ".rationale",
                                "--final 要求每条决策有 rationale（规范记忆的判据）"))
    return decisions


def check_addendum(addendum, where, violations):
    if addendum is None:
        return []
    if not isinstance(addendum, list):
        violations.append(v("EMPTY_FIELD", where, "addendum 不是列表"))
        return []
    for i, item in enumerate(addendum):
        iw = "%s[%d]" % (where, i)
        if not isinstance(item, dict):
            violations.append(v("EMPTY_FIELD", iw, "addendum 条目不是映射"))
            continue
        for key in ("section", "content", "why_separate"):
            if not nonempty(item.get(key)):
                violations.append(v("EMPTY_FIELD", "%s.%s" % (iw, key),
                                    "%s 为空（why_separate 记录为何不进简报正文）" % key))
    return addendum


def check_revisions(revisions, where, violations):
    if revisions is None:
        return []
    if not isinstance(revisions, list):
        violations.append(v("EMPTY_FIELD", where, "revisions 不是列表"))
        return []
    for i, item in enumerate(revisions):
        iw = "%s[%d]" % (where, i)
        if not isinstance(item, dict):
            violations.append(v("EMPTY_FIELD", iw, "revision 条目不是映射"))
            continue
        for key in ("date", "change", "reason"):
            if not nonempty(item.get(key)):
                violations.append(v("EMPTY_FIELD", "%s.%s" % (iw, key), "%s 为空" % key))
        date = item.get("date")
        if nonempty(date) and not DATE_RE.fullmatch(str(date)):
            violations.append(v("ENUM_INVALID", iw + ".date",
                                "date 须为 YYYY-MM-DD，实为 %s" % date))
    return revisions


def check_project(project, where, violations, final):
    if not isinstance(project, dict):
        violations.append(v("EMPTY_FIELD", where, "project 缺失或不是映射"))
        return
    status = project.get("status")
    if not nonempty(status):
        violations.append(v("EMPTY_FIELD", where + ".status", "status 缺失（草稿|已定稿）"))
    elif str(status) not in DOC_STATUSES:
        violations.append(v("ENUM_INVALID", where + ".status",
                            "status 越界：%s（合法集 %s）"
                            % (status, "|".join(DOC_STATUSES))))
    elif final and str(status) != "已定稿":
        violations.append(v("STATUS_MISMATCH", where + ".status",
                            "--final 要求 project.status 为「已定稿」（先落定稿，再跑门禁）"))
    for key in ("created", "updated"):
        value = project.get(key)
        if nonempty(value) and not DATE_RE.fullmatch(str(value)):
            violations.append(v("ENUM_INVALID", "%s.%s" % (where, key),
                                "%s 须为 YYYY-MM-DD，实为 %s" % (key, value)))


def previous_ids(previous, project_root, violations):
    """读旧稿快照的 BD-### 集合；读失败记违规并返回 None。"""
    show = display_path(previous, project_root)
    data, err = load_yaml_safe(previous)
    if data is None and err is None:
        violations.append(v("MISSING_FILE", show,
                            "旧稿快照不存在（更新重写前先 cp brief.yaml brief.yaml.prev）"))
        return None
    if err is not None:
        violations.append(v("UNPARSABLE_YAML", show, "旧稿快照不可解析：%s" % err))
        return None
    if not isinstance(data, dict):
        violations.append(v("EMPTY_FIELD", show, "旧稿快照顶层不是映射"))
        return None
    items = data.get("decisions")
    if not isinstance(items, list):
        return set()
    return {str(d["id"]) for d in items
            if isinstance(d, dict) and nonempty(d.get("id"))}


def review_script_path():
    """diy-editorial-review 的引擎路径：由本引擎自身位置推算 skills 根
    （源码与安装两种布局同构，对齐 readiness 的 diyc_script_path 先例）。"""
    skills_root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    return os.path.join(skills_root, *REVIEW_SCRIPT_REL)


# trace: B4 任务书 §12.1 ①ⓒ（--final 评审证据链：review_refs → editorial-review.yaml 的 ER-###）
def check_review_evidence(data, root, out, path, show, violations, warnings):
    """--final 的六条证据校验：`review_refs` 非空 → 台账在场 → ID 在 `reviews[]` 内 →
    该记录 `status: 已定稿` → `target` 归一化后指向本 `brief.yaml` → `lenses` 两透镜齐全
    （忠实源 `doc_standards` 的两条 append-only 标准提供者语义）。派发不可用（环境缺兄弟
    引擎）→ `TOOL_MISSING` 降级：六条一并转 warning、放行；与「技能在场而记录缺失或不合格
    → 硬拒」分工不重叠——前者是环境问题、后者是产物问题。"""
    script = review_script_path()
    if not os.path.isfile(script):
        warnings.append(v("TOOL_MISSING", display_path(script, root),
                          "diy-editorial-review 引擎缺席：评审证据校验（六条）降级为 warning、"
                          "--final 放行；请从会话侧人工确认本稿已过结构 + 文风两透镜评审"))
        return
    raw_refs = data.get("review_refs")
    refs = [str(r) for r in raw_refs if nonempty(r)] if isinstance(raw_refs, list) else []
    if not refs:
        violations.append(v("EVIDENCE_MISSING", show + " review_refs",
                            "--final 要求 review_refs 非空（存量的已定稿记录同样要补，"
                            "不静默放行）：调 diy-editorial-review 评审本稿，"
                            "把 ER-### 写进 review_refs 再定稿"))
        return
    review_path = os.path.join(out, REVIEW_FILE)
    review_show = display_path(review_path, root)
    review, err = load_yaml_safe(review_path)
    if review is None and err is None:
        violations.append(v("MISSING_FILE", review_show,
                            "%s 不存在：review_refs 指向的记录无处可查"
                            "（先调 diy-editorial-review 产出 ER-###）" % REVIEW_FILE))
        return
    if err is not None:
        violations.append(v("UNPARSABLE_YAML", review_show, "评审台账不可解析：%s" % err))
        return
    if not isinstance(review, dict):
        violations.append(v("EMPTY_FIELD", review_show, "评审台账顶层不是映射"))
        return
    raw_records = review.get("reviews")
    records = raw_records if isinstance(raw_records, list) else []
    by_id = {}
    for item in records:
        if isinstance(item, dict) and nonempty(item.get("id")):
            by_id.setdefault(str(item["id"]), item)
    brief_rel = normalize_rel(path, root)
    for rid in refs:
        record = by_id.get(rid)
        if record is None:
            violations.append(v("UNKNOWN_ID", show + " review_refs",
                                "%s 不在 %s 的 reviews[] 内" % (rid, review_show)))
            continue
        rw = "%s reviews[%s]" % (review_show, rid)
        status = record.get("status")
        if str(status) != REVIEW_STATUS:
            violations.append(v("STATUS_MISMATCH", rw + ".status",
                                "--final 要求证据记录 status: 已定稿，实为 %s"
                                % (status if nonempty(status) else "缺失")))
        target = record.get("target")
        if not nonempty(target) or normalize_rel(target, root) != brief_rel:
            violations.append(v("EVIDENCE_MISSING", rw + ".target",
                                "该记录评审的是 %s，不是本 brief.yaml"
                                "——指向别处的记录不构成本文档的证据"
                                % (target if nonempty(target) else "（target 缺失）")))
        lenses = record.get("lenses")
        seen = {str(x) for x in lenses} if isinstance(lenses, list) else set()
        if set(REVIEW_LENSES) - seen:
            violations.append(v("EVIDENCE_MISSING", rw + ".lenses",
                                "该记录 lenses=%s 未同时含 结构 与 文风"
                                "（定稿路径要求两透镜齐全）" % (lenses,)))


def cmd_check(args):
    root = os.path.abspath(args.project_root)
    out = args.output_dir
    path = os.path.join(out, BRIEF_FILE)
    show = display_path(path, root)
    violations = []
    warnings = []
    decisions = []
    brief = {}
    addendum = []
    revisions = []

    data, err = load_yaml_safe(path)
    if data is None and err is None:
        violations.append(v("MISSING_FILE", show,
                            "%s 不存在（先完成一次「新建」起草）" % BRIEF_FILE))
    elif err is not None:
        violations.append(v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err))
    elif not isinstance(data, dict):
        violations.append(v("EMPTY_FIELD", show, "顶层不是映射（须为 project + brief）"))
    else:
        check_project(data.get("project"), show + " project", violations, args.final)
        brief = check_brief_section(data.get("brief"), show + " brief", args.final, violations)
        decisions = check_decisions(data.get("decisions"), show + " decisions",
                                    args.final, violations)
        addendum = check_addendum(data.get("addendum"), show + " addendum", violations)
        revisions = check_revisions(data.get("revisions"), show + " revisions", violations)
        if args.final and any("[假设]" in s for s in collect_strings(data)):
            violations.append(v("ASSUMPTION_PRESENT", show,
                                "--final 要求零 [假设]；未决假设须先落定"))
        if args.final:
            check_review_evidence(data, root, out, path, show, violations, warnings)

    if args.previous:
        old = previous_ids(args.previous, root, violations)
        if old is not None:
            current = {str(d["id"]) for d in decisions
                       if isinstance(d, dict) and nonempty(d.get("id"))}
            for rid in sorted(old - current):
                violations.append(v("ID_UNSTABLE", show + " decisions",
                                    "旧 ID %s 在新稿中消失（BD ID 稳定：不重编号、不重用）"
                                    % rid))

    counts = {
        "decisions": list_len(decisions),
        "decisions_by_status": count_by(decisions if isinstance(decisions, list) else [], "status"),
        "users": list_len(brief.get("users") if isinstance(brief, dict) else None),
        "value": list_len(brief.get("value") if isinstance(brief, dict) else None),
        "open_questions": list_len(brief.get("open_questions") if isinstance(brief, dict) else None),
        "assumptions": list_len(brief.get("assumptions") if isinstance(brief, dict) else None),
        "extra_sections": list_len(brief.get("extra_sections") if isinstance(brief, dict) else None),
        "addendum": list_len(addendum),
        "revisions": list_len(revisions),
    }
    ok = not violations
    payload = {
        "ok": ok,
        "command": "check",
        "project_root": args.project_root,
        "output_dir": os.path.normpath(out).replace("\\", "/"),
        "final": args.final,
        "previous": display_path(args.previous, root) if args.previous else None,
        "violations": violations,
        "warnings": warnings,
        "counts": counts,
    }
    if ok:
        human = ["PASS：%s 校验通过（decisions=%d%s）"
                 % (show, counts["decisions"], "，final" if args.final else "")]
        human += ["WARNING %s %s: %s" % (w["code"], w["where"], w["msg"])
                  for w in warnings]
    else:
        human = ["FAIL："] + ["- %s %s: %s" % (x["code"], x["where"], x["msg"])
                              for x in violations]
    return emit(payload, args.json, human)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(
        description="diy-product-brief 确定性引擎：intent 门禁（零产出拒绝 + 路由）+ brief.yaml 校验")
    sub = ap.add_subparsers(dest="cmd", required=True)

    i = sub.add_parser("intent", help="解析 intent 前置条件并给路由（更新/校验 无产物 → 零产出拒绝）")
    i.add_argument("--intent", required=True, choices=INTENTS,
                   help="会话判定的意图：新建 / 更新 / 校验")
    i.add_argument("--project-root", default=".", help="项目根（默认 .）")
    i.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    i.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    i.set_defaults(func=cmd_intent)

    c = sub.add_parser("check", help="校验 brief.yaml（schema/枚举/ID；--final 附加定稿义务）")
    c.add_argument("--project-root", default=".", help="项目根（默认 .）")
    c.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    c.add_argument("--final", action="store_true",
                   help="定稿校验：status 已落「已定稿」+ 零假设 + 主体非空 + 每条决策有 "
                        "rationale + review_refs 评审证据链（六条）")
    c.add_argument("--previous", default=None,
                   help="旧稿快照路径：比对 BD-### 集合，旧有新无 → ID_UNSTABLE")
    c.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    c.set_defaults(func=cmd_check)

    args = ap.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
