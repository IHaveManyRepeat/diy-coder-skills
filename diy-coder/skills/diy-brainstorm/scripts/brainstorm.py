# -*- coding: utf-8 -*-
"""diy-brainstorm 确定性引擎：会话列举（list）/ 技术库加载与抽样（techniques）/
会话记录骨架铸造（init）/ brainstorm.yaml 校验（check [--final]）。

机制：会话记录是**内容型产物**（教练对话的结论落 `{output_dir}/brainstorm.yaml`），
内容面由会话（LLM）直接编辑 YAML；本引擎只做确定性的两件事——铸造骨架与机械校验。
技术库落技能目录根 `brain-methods.csv`（与 `scripts/` 平级，61 技术 / 10 类，中文原生），
路径按引擎自身位置推算（`Path(__file__).parent.parent`），两种安装布局（源码
`diy-coder/skills/` 与安装 `.claude/skills/`）下同构成立。

  list       列会话记录——只回 `id` / `topic` / `date` / `status` / `current_step` 五字段
             （源纪律：**只列名不读内容**，续接点由 `current_step` 承载）。产物缺席是新项目
             常态 → 空列表 + `ok: true`，不报错；产物损坏 → 结构化违规（列不出就列不出）。

  techniques 加载技术库：`--all` 全列 / `--category C` 按类筛选 / `--random N` 随机抽 N
             （跨类别优先，保证组合多样）/ 无参 = 随机 5 个候选。`--category` 合法值 =
             CSV 的 `category` 列（10 个中文类名，**取值语言随库**），非法值 → `ENUM_INVALID`
             + exit 1。四种技术选取模式（用户自选 / AI 推荐 / 随机 / 渐进流）都由这里取数。

  init       建会话记录骨架（`--topic` 必填 / `--goals` 可省）：铸造 `BS-###`（序号 = 现有
             最大 + 1，三位零填充，**不复用空号不重号**）、`status: 草稿` + `current_step: 1`，
             原子写（产物缺席则建文件；损坏 → 拒绝且零写入，绝不覆盖）。

  check      schema / `BS-###` 格式与唯一 / `status` 枚举 / `current_step` 枚举 1-5 且与
             `status` 同档（草稿→1；进行中→2-4；已完成→5，否则 `STATUS_MISMATCH`）/
             步骤锚点与内容一致（≥2 有 approach、≥3 有 techniques、=5 有 themes + priorities.top
             + actions——源纪律「无行动计划不得收尾」）/ 想法 `no` 连续不跳号（1..N）/
             `themes[].ideas`、`priorities` 三键与 `actions[].idea` 的引用必须落在本记录
             `ideas[].no` 内 / `techniques[].category` ∈ 库内类名。`--final` 附加：
             `status: 已完成` 且零 `[假设]`（定稿前清零，未决项落 `open_questions`）。
             `--id BS-xxx` 把记录级扫描收窄到一条（找不到 → `UNKNOWN_ID`）。
             exit 0 唯一放行。

分工裁定（任务书 §2.2 形 A）：brainstorm.yaml 属新产物类型，不进 diyc.py check 的硬编码
类型集；契约同构——exit 0 唯一放行 / `--json` 单行回执（`ensure_ascii=False`）/ 无 `--json`
走中文人读行（每违规一行 `CODE where: msg` + 汇总行）/ 回执共同键
{ok, command, project_root, output_dir, violations[{code, where, msg}], warnings, counts}，
写回命令（init）另含 `updated`；`where` 正斜杠、相对 project-root。`--output-dir` 必填、
无缺省；引擎不做实例解析 / 白名单 / 目录推导（实例解析由 SKILL.md 委托 `diyc.py resolve`）。
写回纪律：全文 load → 就地改 → 追加/合并 → `yaml.safe_dump(allow_unicode=True,
sort_keys=False, default_flow_style=False)` → 同目录临时文件 + `os.replace`（注释不保留）。

违规码：复用 batch3-contract §3 冻结集——本引擎用到 `MISSING_FILE` / `UNPARSABLE_YAML` /
`UNKNOWN_ID` / `ENUM_INVALID` / `EMPTY_FIELD` / `DUPLICATE_ID` / `SET_MISMATCH` /
`STATUS_MISMATCH` / `ASSUMPTION_PRESENT` 共 9 个，**零新增**。两处语义复用在此登记：
① `UNPARSABLE_YAML` 兼作技术库（CSV）解析失败码——冻结集里没有「非 YAML 文本不可解析」码，
   造新码不如复用最近义项（msg 内点名是 CSV）；
② `SET_MISMATCH` 承载「想法 `no` 非 1..N 连续」——该码的语义是集合与真值不符，正中此例。

`--previous` 不适用（任务书 §2.2 记账，W1 判 no）：本产物是追加式台账（`sessions[]` 只追加、
记录内序号 `no` 只在记录内递增），从无 ID 集合收缩面——不存在「旧有新无」可比对。
"""
# trace: 迁移计划 §二 验收 #2（产物 schema + BS-### 稳定 ID）/#3（门禁零产出退出）
#        /#4（ID 链接入：BS-### + 想法序号）/#12（领域引擎接线：a 实例委托 d/e 写权边界）
import argparse
import csv
import io
import json
import os
import random
import re
import sys

import yaml

BRAINSTORM_FILE = "brainstorm.yaml"
METHODS_FILE = "brain-methods.csv"
LIB_COLUMNS = ("category", "technique_name", "description")

STATUS_ENUM = ("草稿", "进行中", "已完成")
APPROACH_ENUM = ("用户自选", "AI 推荐", "随机", "渐进流")
# 记录级状态机与续接锚点同档（裁定 1：current_step 是续接点，不是进度装饰）
STEP_BY_STATUS = {"草稿": (1,), "进行中": (2, 3, 4), "已完成": (5,)}
STEP_MIN, STEP_MAX = 1, 5
DEFAULT_CANDIDATES = 5
ASSUMPTION_MARK = "[假设]"
PROJECT_FIELDS = ("name", "created", "updated")

BS_RE = re.compile(r"BS-(\d{3})\Z")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}\Z")


def v(code, where, msg):
    """违规项构造；where 统一正斜杠（契约 §3）。"""
    return {"code": code, "where": str(where).replace("\\", "/"), "msg": msg}


def nonempty(value):
    """非空判定：None / 空白字符串均视为空。"""
    return value is not None and str(value).strip() != ""


def is_int(value):
    """整数判定（布尔不得充当整数：true 不是 1）。"""
    return isinstance(value, int) and not isinstance(value, bool)


def normalize_keys(node):
    """布尔键归一回字符串：PyYAML 按 YAML 1.1 把裸键 `no` 解析成布尔 False
    （`yes/no/on/off` 都是隐式布尔）。schema 冻结用 `no` 当想法序号键——若不归一，
    ① check 读不到 `no`（`idea.get("no")` 恒 None）；② init 的全文重写会把既有
    `no: 1` 落成 `false: 1`（产物被静默污染）。归一后写回为 `'no': 1`（合法且可往返）。
    """
    if isinstance(node, dict):
        out = {}
        for key, value in node.items():
            if isinstance(key, bool):
                key = "no" if key is False else "yes"
            out[key] = normalize_keys(value)
        return out
    if isinstance(node, list):
        return [normalize_keys(item) for item in node]
    return node


def load_yaml_safe(path):
    """读 YAML：(data, err)。缺席 → (None, None)；空文件 → ({}, None)；损坏 → (None, 原因)。
    载入即做布尔键归一（见 `normalize_keys`）。"""
    if not os.path.isfile(path):
        return None, None
    try:
        with io.open(path, "r", encoding="utf-8") as handle:
            return normalize_keys(yaml.safe_load(handle) or {}), None
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


def today():
    """"YYYY-MM-DD（本地时区）。"""
    import datetime
    return datetime.date.today().isoformat()


def save_yaml_atomic(path, data):
    """同目录 tmp + os.replace 原子替换（契约 §3 写回纪律；注释不保留，失败不吞异常）。"""
    tmp = path + ".tmp"
    try:
        with io.open(tmp, "w", encoding="utf-8") as handle:
            yaml.safe_dump(data, handle, allow_unicode=True, sort_keys=False,
                           default_flow_style=False)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise


def project_name(project_root):
    """产物 `project.name`：diy-coder.yaml 的 `project.name`；不可用 → 项目目录名 + warning。"""
    cfg, err = load_yaml_safe(os.path.join(project_root, "diy-coder.yaml"))
    if isinstance(cfg, dict):
        project = cfg.get("project")
        if isinstance(project, dict) and nonempty(project.get("name")):
            return str(project["name"]), None
    note = "diy-coder.yaml project.name 不可用（%s），回落项目目录名" % (err or "缺该键")
    return os.path.basename(os.path.abspath(project_root)), v(
        "MISSING_FILE", "diy-coder.yaml", note)


# ---------------------------------------------------------------- 技术库

def methods_path():
    """技术库路径：技能目录根（`scripts/` 的上一级），两种安装布局同构。"""
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        METHODS_FILE)


def load_methods(project_root):
    """加载技术库 → (rows | None, violations)。行结构 {category, technique_name, description}。"""
    path = methods_path()
    show = display_path(path, project_root)
    if not os.path.isfile(path):
        return None, [v("MISSING_FILE", show, "%s 不存在（技能自带技术库）" % METHODS_FILE)]
    violations = []
    rows = []
    try:
        with io.open(path, "r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            missing = [c for c in LIB_COLUMNS if c not in (reader.fieldnames or [])]
            if missing:
                return None, [v("EMPTY_FIELD", show,
                                "技术库缺列：%s（须为 %s）" % ("|".join(missing),
                                                              "|".join(LIB_COLUMNS)))]
            for i, row in enumerate(reader):
                item = {key: (row.get(key) or "").strip() for key in LIB_COLUMNS}
                where = "%s 第 %d 行" % (show, i + 2)
                empty = [key for key in LIB_COLUMNS if not item[key]]
                if empty:
                    violations.append(v("EMPTY_FIELD", where,
                                        "技术条目缺 %s" % "|".join(empty)))
                    continue
                rows.append(item)
    except (csv.Error, OSError, UnicodeDecodeError) as e:
        return None, [v("UNPARSABLE_YAML", show, "技术库解析失败：%s" % e)]
    if violations:
        return None, violations
    if not rows:
        return None, [v("EMPTY_FIELD", show, "技术库无数据行")]
    return rows, []


def library_categories(rows):
    """库内类名（CSV 出现序去重）——`--category` 的合法集与 check 的枚举来源。"""
    seen = []
    for row in rows:
        if row["category"] not in seen:
            seen.append(row["category"])
    return seen


def sample_cross_category(rows, count):
    """跨类别优先抽样：按类分桶后轮转取，各类耗尽再补齐——保证组合多样（源 02c 语义）。"""
    buckets = {}
    for row in rows:
        buckets.setdefault(row["category"], []).append(row)
    order = list(buckets)
    random.shuffle(order)
    for bucket in buckets.values():
        random.shuffle(bucket)
    picked = []
    while len(picked) < count:
        before = len(picked)
        for category in order:
            if len(picked) >= count:
                break
            if buckets[category]:
                picked.append(buckets[category].pop())
        if len(picked) == before:
            break
    return picked


def count_by_category(rows, key):
    counts = {}
    for row in rows:
        counts[row[key]] = counts.get(row[key], 0) + 1
    return counts


# ---------------------------------------------------------------- 命令面

def receipt_base(command, args, output_dir):
    return {"ok": False, "command": command, "project_root": args.project_root,
            "output_dir": os.path.normpath(output_dir).replace("\\", "/"),
            "violations": [], "warnings": [], "counts": {}}


def emit(payload, as_json, summary_line=None):
    """打印回执并返回 exit code：0 = 放行，1 = 有违规（契约 §3）。"""
    if as_json:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        if payload.get("ok"):
            print(summary_line or "PASS：%s 完成" % payload["command"])
        else:
            for item in payload.get("violations") or []:
                print("%s %s: %s" % (item["code"], item["where"], item["msg"]))
        for item in payload.get("warnings") or []:
            print("WARN %s %s: %s" % (item["code"], item["where"], item["msg"]))
        if payload.get("violations"):
            print("FAIL：%d 条违规（exit 1）" % len(payload["violations"]))
    return 0 if payload.get("ok") else 1


def read_sessions(path, show):
    """读产物并取 sessions 列表 → (records | None, violations, warnings)。"""
    data, err = load_yaml_safe(path)
    if data is None and err is None:
        return None, [], []
    if err is not None:
        return None, [v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err)], []
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


# ---- list ----

def cmd_list(args):
    root = os.path.abspath(args.project_root)
    out = os.path.abspath(args.output_dir)
    path = os.path.join(out, BRAINSTORM_FILE)
    show = display_path(path, root)
    payload = receipt_base("list", args, out)
    records, violations, warnings = read_sessions(path, show)
    payload["violations"] = violations
    payload["warnings"] = warnings
    sessions = []
    for rec in records or []:
        if not isinstance(rec, dict):
            continue
        sessions.append({"id": rec.get("id"), "topic": rec.get("topic"),
                         "date": rec.get("date"), "status": rec.get("status"),
                         "current_step": rec.get("current_step")})
    payload["ok"] = not violations
    payload["sessions"] = sessions
    payload["counts"] = {"sessions": len(sessions),
                         "by_status": count_by_category(
                             [{"k": s["status"]} for s in sessions if nonempty(s["status"])],
                             "k")}
    return emit(payload, args.json,
                "PASS：%s 记录 %d 条%s" % (show, len(sessions),
                                          "（产物缺席，按空列表处理）" if records is None else ""))


# ---- techniques ----

def cmd_techniques(args):
    root = os.path.abspath(args.project_root)
    out = os.path.abspath(args.output_dir)
    payload = receipt_base("techniques", args, out)
    rows, violations = load_methods(root)
    if violations:
        payload["violations"] = violations
        payload["counts"] = {"techniques": 0, "library": 0}
        return emit(payload, args.json)
    categories = library_categories(rows)
    picked = []
    if args.all:
        picked = list(rows)
    elif args.category is not None:
        if str(args.category) not in categories:
            payload["violations"] = [v("ENUM_INVALID", "techniques --category",
                                       "category 越界：%s（合法集 %s）"
                                       % (args.category, "|".join(categories)))]
            payload["counts"] = {"techniques": 0, "library": len(rows)}
            return emit(payload, args.json)
        picked = [row for row in rows if row["category"] == str(args.category)]
    else:
        count = args.random if args.random is not None else DEFAULT_CANDIDATES
        if not is_int(count) or count < 1:
            payload["violations"] = [v("ENUM_INVALID", "techniques --random",
                                       "抽样条数须为正整数，实为 %s" % args.random)]
            payload["counts"] = {"techniques": 0, "library": len(rows)}
            return emit(payload, args.json)
        if count > len(rows):
            payload["warnings"] = [v("ENUM_INVALID", "techniques --random",
                                     "请求 %d 条超出库容量 %d，按全库返回" % (count, len(rows)))]
            picked = list(rows)
        else:
            picked = sample_cross_category(rows, count)
    payload["ok"] = True
    payload["techniques"] = picked
    payload["counts"] = {"techniques": len(picked), "library": len(rows),
                         "by_category": count_by_category(picked, "category"),
                         "categories": len(categories)}
    return emit(payload, args.json,
                "PASS：技术库 %d 条 / %d 类，本次返回 %d 条"
                % (len(rows), len(categories), len(picked)))


# ---- init ----

def next_record_id(records):
    """下一个 `BS-###`：现有最大序号 + 1（三位零填充）。空号不复用、不重号。"""
    max_no = 0
    for rec in records:
        if isinstance(rec, dict) and nonempty(rec.get("id")):
            m = BS_RE.fullmatch(str(rec["id"]).strip())
            if m:
                max_no = max(max_no, int(m.group(1)))
    return "BS-%03d" % (max_no + 1)


def blank_document(project_root, stamp):
    """新建产物骨架：project 三键 + 空集合 + 空 revisions。"""
    name, warning = project_name(project_root)
    doc = {"project": {"name": name, "created": stamp, "updated": stamp},
           "sessions": [], "revisions": []}
    return doc, ([warning] if warning else [])


def new_record(record_id, topic, goals, stamp):
    """会话记录骨架：结论性字段全给空位，内容面由会话（LLM）直接编辑。"""
    return {"id": record_id, "topic": topic, "goals": goals or "", "approach": "",
            "date": stamp, "status": "草稿", "current_step": 1,
            "techniques": [], "ideas": [], "themes": [],
            "priorities": {"top": [], "quick_wins": [], "breakthroughs": []},
            "actions": [], "open_questions": []}


def cmd_init(args):
    root = os.path.abspath(args.project_root)
    out = os.path.abspath(args.output_dir)
    path = os.path.join(out, BRAINSTORM_FILE)
    show = display_path(path, root)
    payload = receipt_base("init", args, out)
    stamp = today()
    data, err = load_yaml_safe(path)
    if err is not None:
        payload["violations"] = [v("UNPARSABLE_YAML", show,
                                   "YAML 解析失败：%s（拒绝且零写入——修好或另行归档后再 init）" % err)]
        return emit(payload, args.json)
    if data is None:
        doc, warnings = blank_document(root, stamp)
        payload["warnings"] = warnings
    elif not isinstance(data, dict):
        payload["violations"] = [v("EMPTY_FIELD", show, "顶层不是映射（须为 project + sessions）")]
        return emit(payload, args.json)
    else:
        sessions = data.get("sessions")
        if sessions is None:
            sessions = []
        if not isinstance(sessions, list):
            payload["violations"] = [v("EMPTY_FIELD", show + " sessions",
                                       "sessions 不是列表（拒绝且零写入）")]
            return emit(payload, args.json)
        doc = data
        project = doc.get("project")
        if not isinstance(project, dict):
            project = {}
        name = project.get("name")
        warnings = []
        if not nonempty(name):
            name, warning = project_name(root)
            if warning is not None:
                warnings.append(warning)
        doc["project"] = {"name": name,
                          "created": project.get("created") if nonempty(project.get("created"))
                          else stamp,
                          "updated": stamp}
        doc["sessions"] = sessions
        doc.setdefault("revisions", [])
        payload["warnings"] = warnings
    record_id = next_record_id(doc.get("sessions") or [])
    record = new_record(record_id, args.topic, args.goals, stamp)
    doc["sessions"] = list(doc.get("sessions") or []) + [record]
    try:
        if out:
            os.makedirs(out, exist_ok=True)
        save_yaml_atomic(path, doc)
    except OSError as e:
        payload["violations"] = [v("TOOL_ERROR", show, "写盘失败：%s" % e)]
        return emit(payload, args.json)
    payload["ok"] = True
    payload["updated"] = stamp
    payload["id"] = record_id
    payload["counts"] = {"sessions": len(doc["sessions"]), "next_id": record_id}
    return emit(payload, args.json,
                "PASS：已建会话记录 %s（status: 草稿 / current_step: 1），"
                "产物共 %d 条记录" % (record_id, len(doc["sessions"])))


# ---- check ----

def collect_strings(node):
    """递归收集映射/列表内的全部字符串（键与值）——[假设] 扫描用。"""
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for key, value in node.items():
            yield str(key)
            for text in collect_strings(value):
                yield text
    elif isinstance(node, list):
        for item in node:
            for text in collect_strings(item):
                yield text


def check_idea_refs(refs, where, numbers):
    """引用检查：`no` 必须落在本记录的 `ideas[].no` 集合内（否则 UNKNOWN_ID）。"""
    violations = []
    if not isinstance(refs, list):
        return [v("EMPTY_FIELD", where, "缺失或不是列表（无引用写空列表）")]
    for i, ref in enumerate(refs):
        if is_int(ref) and ref in numbers:
            continue
        violations.append(v("UNKNOWN_ID", "%s[%d]" % (where, i),
                            "%s 不在本记录 ideas[].no 内（可引用集 %s）"
                            % (ref, sorted(numbers) or "空")))
    return violations


def check_ideas(record, where):
    violations = []
    ideas = record.get("ideas")
    numbers = []
    if ideas is None:
        return [v("EMPTY_FIELD", where + ".ideas", "ideas 缺失（无内容写空列表）")], numbers
    if not isinstance(ideas, list):
        return [v("EMPTY_FIELD", where + ".ideas", "ideas 不是列表")], numbers
    for i, idea in enumerate(ideas):
        iw = "%s.ideas[%d]" % (where, i)
        if not isinstance(idea, dict):
            violations.append(v("EMPTY_FIELD", iw, "想法不是映射"))
            continue
        no = idea.get("no")
        if not is_int(no) or no < 1:
            violations.append(v("ENUM_INVALID", iw + ".no",
                                "no 须为正整数（会话内序号，从 1 起），实为 %r" % (no,)))
        else:
            numbers.append(no)
        for key in ("title", "concept", "novelty", "technique"):
            if not nonempty(idea.get(key)):
                violations.append(v("EMPTY_FIELD", iw + "." + key, "%s 为空" % key))
    if numbers and sorted(numbers) != list(range(1, len(numbers) + 1)):
        violations.append(v("SET_MISMATCH", where + ".ideas",
                            "想法 no 须为 1..N 连续不跳号，实为 %s" % sorted(numbers)))
    return violations, numbers


def check_themes(record, where, numbers):
    violations = []
    themes = record.get("themes")
    if themes is None:
        return [v("EMPTY_FIELD", where + ".themes", "themes 缺失（无内容写空列表）")]
    if not isinstance(themes, list):
        return [v("EMPTY_FIELD", where + ".themes", "themes 不是列表")]
    for i, theme in enumerate(themes):
        tw = "%s.themes[%d]" % (where, i)
        if not isinstance(theme, dict):
            violations.append(v("EMPTY_FIELD", tw, "主题不是映射"))
            continue
        for key in ("name", "focus"):
            if not nonempty(theme.get(key)):
                violations.append(v("EMPTY_FIELD", tw + "." + key, "%s 为空" % key))
        refs = theme.get("ideas")
        if refs is None:
            violations.append(v("EMPTY_FIELD", tw + ".ideas",
                                "ideas 缺失（无引用写空列表）"))
            continue
        violations += check_idea_refs(refs, tw + ".ideas", numbers)
    return violations


def check_priorities(record, where, numbers):
    violations = []
    priorities = record.get("priorities")
    if priorities is None:
        return [v("EMPTY_FIELD", where + ".priorities",
                  "priorities 缺失（三键 top / quick_wins / breakthroughs，无内容写空列表）")]
    if not isinstance(priorities, dict):
        return [v("EMPTY_FIELD", where + ".priorities", "priorities 不是映射")]
    for key in ("top", "quick_wins", "breakthroughs"):
        refs = priorities.get(key)
        if refs is None:
            violations.append(v("EMPTY_FIELD", "%s.priorities.%s" % (where, key),
                                "%s 缺失（无引用写空列表）" % key))
            continue
        violations += check_idea_refs(refs, "%s.priorities.%s" % (where, key), numbers)
    return violations


def check_actions(record, where, numbers):
    violations = []
    actions = record.get("actions")
    if actions is None:
        return [v("EMPTY_FIELD", where + ".actions", "actions 缺失（无内容写空列表）")]
    if not isinstance(actions, list):
        return [v("EMPTY_FIELD", where + ".actions", "actions 不是列表")]
    for i, action in enumerate(actions):
        aw = "%s.actions[%d]" % (where, i)
        if not isinstance(action, dict):
            violations.append(v("EMPTY_FIELD", aw, "行动计划不是映射"))
            continue
        if action.get("idea") is None:
            violations.append(v("EMPTY_FIELD", aw + ".idea",
                                "idea 缺失（须指向 ideas[].no）"))
        else:
            violations += check_idea_refs([action.get("idea")], aw + ".idea", numbers)
        for key in ("why", "resources", "timeline", "success"):
            if not nonempty(action.get(key)):
                violations.append(v("EMPTY_FIELD", aw + "." + key, "%s 为空" % key))
        steps = action.get("steps")
        if steps is None:
            violations.append(v("EMPTY_FIELD", aw + ".steps", "steps 缺失（至少一步）"))
        elif not isinstance(steps, list):
            violations.append(v("EMPTY_FIELD", aw + ".steps", "steps 不是列表"))
        else:
            if not steps:
                violations.append(v("EMPTY_FIELD", aw + ".steps", "steps 为空（至少一步）"))
            for j, step in enumerate(steps):
                if not nonempty(step):
                    violations.append(v("EMPTY_FIELD", "%s.steps[%d]" % (aw, j),
                                        "step 为空"))
    return violations


def check_record(index, record, final, categories, show):
    """单条记录的 schema / 枚举 / 引用 / 锚点一致性检查。"""
    violations = []
    where = "%s.sessions[%d]" % (show, index)
    if not isinstance(record, dict):
        return [v("EMPTY_FIELD", where, "记录不是映射")]

    rid = record.get("id")
    if not nonempty(rid):
        violations.append(v("EMPTY_FIELD", where + ".id", "id 缺失"))
    elif not BS_RE.fullmatch(str(rid).strip()):
        violations.append(v("ENUM_INVALID", where + ".id",
                            "id 须为 BS-0nn（三位零填充），实为 %s" % rid))

    for key in ("topic", "goals"):
        if not nonempty(record.get(key)):
            violations.append(v("EMPTY_FIELD", where + "." + key,
                                "%s 为空（会话门禁要求议题与目标在场）" % key))

    date = record.get("date")
    if not nonempty(date):
        violations.append(v("EMPTY_FIELD", where + ".date", "date 缺失"))
    elif not DATE_RE.fullmatch(str(date).strip()):
        violations.append(v("ENUM_INVALID", where + ".date",
                            "date 须为 YYYY-MM-DD，实为 %s" % date))

    approach = record.get("approach")
    if nonempty(approach) and str(approach) not in APPROACH_ENUM:
        violations.append(v("ENUM_INVALID", where + ".approach",
                            "approach 越界：%s（合法集 %s）"
                            % (approach, "|".join(APPROACH_ENUM))))

    status = record.get("status")
    status_ok = False
    if not nonempty(status):
        violations.append(v("EMPTY_FIELD", where + ".status", "status 缺失"))
    elif str(status) not in STATUS_ENUM:
        violations.append(v("ENUM_INVALID", where + ".status",
                            "status 越界：%s（合法集 %s）"
                            % (status, "|".join(STATUS_ENUM))))
    else:
        status_ok = True

    step = record.get("current_step")
    step_ok = False
    if not is_int(step):
        violations.append(v("ENUM_INVALID", where + ".current_step",
                            "current_step 须为 1-5 整数，实为 %r" % (step,)))
    elif not (STEP_MIN <= step <= STEP_MAX):
        violations.append(v("ENUM_INVALID", where + ".current_step",
                            "current_step 越界：%s（合法集 1-5）" % step))
    else:
        step_ok = True

    if status_ok and step_ok:
        legal = STEP_BY_STATUS[str(status)]
        if step not in legal:
            violations.append(v("STATUS_MISMATCH", where + ".current_step",
                                "status: %s 要求 current_step ∈ %s，实为 %s（续接锚点必须与"
                                "会话阶段同档）"
                                % (status, "|".join(str(x) for x in legal), step)))
        if step >= 2 and not nonempty(approach):
            violations.append(v("EMPTY_FIELD", where + ".approach",
                                "current_step: %s 要求 approach 已选（%s）"
                                % (step, "|".join(APPROACH_ENUM))))

    techniques = record.get("techniques")
    if techniques is None:
        violations.append(v("EMPTY_FIELD", where + ".techniques",
                            "techniques 缺失（无内容写空列表）"))
    elif not isinstance(techniques, list):
        violations.append(v("EMPTY_FIELD", where + ".techniques", "techniques 不是列表"))
    else:
        for i, technique in enumerate(techniques):
            tw = "%s.techniques[%d]" % (where, i)
            if not isinstance(technique, dict):
                violations.append(v("EMPTY_FIELD", tw, "技术条目不是映射"))
                continue
            for key in ("name", "category"):
                if not nonempty(technique.get(key)):
                    violations.append(v("EMPTY_FIELD", tw + "." + key, "%s 为空" % key))
            category = technique.get("category")
            if nonempty(category) and categories and str(category) not in categories:
                violations.append(v("ENUM_INVALID", tw + ".category",
                                    "category 越界：%s（合法集 = 技术库类名 %s）"
                                    % (category, "|".join(categories))))
        if step_ok and step >= 3 and not techniques:
            violations.append(v("EMPTY_FIELD", where + ".techniques",
                                "current_step: %s 要求已选技术（step 2 的产出）" % step))

    idea_violations, numbers = check_ideas(record, where)
    violations += idea_violations
    violations += check_themes(record, where, numbers)
    violations += check_priorities(record, where, numbers)
    violations += check_actions(record, where, numbers)

    questions = record.get("open_questions")
    if questions is None:
        violations.append(v("EMPTY_FIELD", where + ".open_questions",
                            "open_questions 缺失（无内容写空列表）"))
    elif not isinstance(questions, list):
        violations.append(v("EMPTY_FIELD", where + ".open_questions",
                            "open_questions 不是列表"))
    else:
        for i, question in enumerate(questions):
            if not nonempty(question):
                violations.append(v("EMPTY_FIELD", "%s.open_questions[%d]" % (where, i),
                                    "条目为空"))

    if step_ok and step == STEP_MAX:
        # 源纪律「无行动计划不得收尾」：收尾态必须有组织结论与行动计划
        for key, msg in (("themes", "至少 1 个主题"),
                         ("actions", "至少 1 条行动计划")):
            if isinstance(record.get(key), list) and not record[key]:
                violations.append(v("EMPTY_FIELD", where + "." + key,
                                    "current_step: 5 要求%s（组织步的产出）" % msg))
        priorities = record.get("priorities")
        if isinstance(priorities, dict) and not priorities.get("top"):
            violations.append(v("EMPTY_FIELD", where + ".priorities.top",
                                "current_step: 5 要求 top 非空（优先级四维的收敛结果）"))

    if final:
        violations += check_final_duties(record, where, status)
    return violations


def check_final_duties(record, where, status):
    """`--final` 附加义务：`status: 已完成` + 零 `[假设]`（定稿前清零）。"""
    violations = []
    if str(status) != "已完成":
        violations.append(v("STATUS_MISMATCH", where + ".status",
                            "--final 要求 status: 已完成，实为 %s（先走完 5 步收尾）" % status))
    if any(ASSUMPTION_MARK in text for text in collect_strings(record)):
        violations.append(v("ASSUMPTION_PRESENT", where,
                            "--final 要求零 [假设]；未决项写进 open_questions 再定稿"))
    return violations


def cmd_check(args):
    root = os.path.abspath(args.project_root)
    out = os.path.abspath(args.output_dir)
    path = os.path.join(out, BRAINSTORM_FILE)
    show = display_path(path, root)
    payload = receipt_base("check", args, out)
    violations = []
    warnings = []
    records = []
    categories = None

    rows, lib_violations = load_methods(root)
    if lib_violations:
        warnings += lib_violations  # 库缺席 → 类名枚举降级（不阻断产物校验）
    else:
        categories = library_categories(rows)

    data, err = load_yaml_safe(path)
    if data is None and err is None:
        violations.append(v("MISSING_FILE", show,
                            "%s 不存在（先跑 init 建会话记录）" % BRAINSTORM_FILE))
    elif err is not None:
        violations.append(v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err))
    elif not isinstance(data, dict):
        violations.append(v("EMPTY_FIELD", show, "顶层不是映射（须为 project + sessions）"))
    else:
        project = data.get("project")
        if project is not None and not isinstance(project, dict):
            violations.append(v("EMPTY_FIELD", show + " project", "project 不是映射"))
        revisions = data.get("revisions")
        if revisions is not None and not isinstance(revisions, list):
            violations.append(v("EMPTY_FIELD", show + " revisions", "revisions 不是列表"))
        raw = data.get("sessions")
        if raw is None:
            violations.append(v("EMPTY_FIELD", show + " sessions",
                                "sessions 缺失（集合形态；无记录写空列表）"))
        elif not isinstance(raw, list):
            violations.append(v("EMPTY_FIELD", show + " sessions", "sessions 不是列表"))
        else:
            records = raw
            seen = set()
            for i, record in enumerate(records):
                if isinstance(record, dict) and nonempty(record.get("id")):
                    rid = str(record["id"]).strip()
                    if rid in seen:
                        violations.append(v("DUPLICATE_ID", "%s.sessions[%d].id" % (show, i),
                                            "记录 ID %s 重复（BS ID 稳定不重用）" % rid))
                    seen.add(rid)
            target_id = str(args.id).strip() if nonempty(args.id) else None
            if target_id is not None and target_id not in seen:
                violations.append(v("UNKNOWN_ID", "check --id",
                                    "%s 不在 %s 的 sessions[] 内" % (target_id, show)))
            for i, record in enumerate(records):
                if target_id is not None and (
                        not isinstance(record, dict)
                        or str(record.get("id") or "").strip() != target_id):
                    continue
                violations += check_record(i, record, args.final, categories, show)
            if args.final and not records:
                violations.append(v("EMPTY_FIELD", show + " sessions",
                                    "--final 要求至少 1 条会话记录"))

    statuses = {}
    ideas = 0
    for record in records:
        if not isinstance(record, dict):
            continue
        if nonempty(record.get("status")):
            statuses[str(record["status"])] = statuses.get(str(record["status"]), 0) + 1
        if isinstance(record.get("ideas"), list):
            ideas += len(record["ideas"])
    payload["ok"] = not violations
    payload["violations"] = violations
    payload["warnings"] = warnings
    payload["final"] = bool(args.final)
    payload["counts"] = {"sessions": len(records), "by_status": statuses, "ideas": ideas}
    return emit(payload, args.json,
                "PASS：%s 校验通过（sessions=%d / ideas=%d%s）"
                % (show, len(records), ideas, " / --final" if args.final else ""))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(
        description="diy-brainstorm 确定性引擎：会话列举（list）/ 技术库加载（techniques）"
                    "/ 记录骨架（init）/ brainstorm.yaml 校验（check）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(parser):
        parser.add_argument("--project-root", default=".",
                            help="项目根（默认 .）")
        parser.add_argument("--output-dir", required=True,
                            help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
        parser.add_argument("--json", action="store_true", help="输出单行 JSON 回执")

    ls = sub.add_parser("list", help="列会话记录（只回 id/topic/date/status/current_step 五字段）")
    common(ls)
    ls.set_defaults(func=cmd_list)

    tp = sub.add_parser("techniques", help="技术库加载：--all / --category C / --random N（默认随机 5 个）")
    common(tp)
    group = tp.add_mutually_exclusive_group()
    group.add_argument("--all", action="store_true", help="全列技术库")
    group.add_argument("--category", default=None, help="按类筛选（类名取技术库的中文类名）")
    group.add_argument("--random", type=int, default=None, help="随机抽 N 条（跨类别优先）")
    tp.set_defaults(func=cmd_techniques)

    ini = sub.add_parser("init", help="建会话记录骨架（铸 BS-###，status: 草稿 + current_step: 1）")
    common(ini)
    ini.add_argument("--topic", required=True, help="会话议题（门禁：由会话询问收集，不代拟）")
    ini.add_argument("--goals", default=None, help="会话目标（可省，内容面可后补）")
    ini.set_defaults(func=cmd_init)

    ck = sub.add_parser("check", help="校验 brainstorm.yaml（schema/枚举/引用/锚点；--final 附加定稿义务）")
    common(ck)
    ck.add_argument("--final", action="store_true",
                    help="定稿校验：status: 已完成 + 零 [假设]")
    ck.add_argument("--id", default=None, help="只校验指定记录（BS-###）")
    ck.set_defaults(func=cmd_check)

    args = ap.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
