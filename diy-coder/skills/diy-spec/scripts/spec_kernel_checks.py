# -*- coding: utf-8 -*-
"""diy-spec 校验域：SK/CAP/日期常量、路径与记录定位助手、记录/CAP/verdict/前稿比对校验族。."""

import os
import re

import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import display_path, load_yaml_safe, nonempty, v, walk_strings  # noqa: E402

SPEC_FILE = "spec-kernel.yaml"
SK_RE = re.compile(r"SK-\d{3}")
CAP_RE = re.compile(r"CAP-\d+")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
RECORD_STATUSES = ("草稿", "已定稿")
ASSUMPTION = "[假设]"

def resolve_path(value, project_root):
    """产物内路径按 project-root 解析（绝对路径原样）。"""
    text = str(value)
    return text if os.path.isabs(text) else os.path.join(project_root, text)

def record_where(show, index, record):
    """记录定位串：有合法 id 用 id、否则用下标（where 稳定可读）。"""
    rid = record.get("id") if isinstance(record, dict) else None
    if nonempty(rid) and SK_RE.fullmatch(str(rid)):
        return "%s specs[%s]" % (show, rid)
    return "%s specs[%d]" % (show, index)

# trace: B4 diy-spec 验收 #2/#4（CAP 结构 + intent/success 双非空 + 记录内唯一 + retired 布尔）
def check_capabilities(items, where, violations):
    """CAP 结构：intent / success 双非空、CAP-N 格式、记录内唯一、retired 布尔（Spec Law 1/6）。"""
    if not isinstance(items, list):
        violations.append(v("EMPTY_FIELD", where + ".capabilities",
                            "capabilities 缺失或不是列表（五字段之一，须为 CAP 条目列表）"))
        return 0
    if not items:
        violations.append(v("EMPTY_FIELD", where + ".capabilities",
                            "capabilities 为空（Spec Law 1：内核至少 1 条能力）"))
        return 0
    seen = set()
    retired = 0
    for i, item in enumerate(items):
        cap_where = "%s.capabilities[%d]" % (where, i)
        if not isinstance(item, dict):
            violations.append(v("EMPTY_FIELD", cap_where,
                                "CAP 条目不是映射（须含 id / intent / success）"))
            continue
        cid = item.get("id")
        if not nonempty(cid):
            violations.append(v("EMPTY_FIELD", cap_where + ".id", "CAP id 缺失"))
        elif not CAP_RE.fullmatch(str(cid)):
            violations.append(v("ENUM_INVALID", cap_where + ".id",
                                "CAP id 须为 CAP-N（N 为自然数），实为 %s" % cid))
        elif str(cid) in seen:
            violations.append(v("DUPLICATE_ID", cap_where + ".id",
                                "CAP id %s 在记录内重复（Spec Law 6：稳定、唯一、"
                                "永不重编号；退役用 retired: true 留痕，不删条目）" % cid))
        else:
            seen.add(str(cid))
        for key in ("intent", "success"):
            if not nonempty(item.get(key)):
                violations.append(v("EMPTY_FIELD", cap_where + "." + key,
                                    "%s 为空（Spec Law 1：intent 与 success 缺一不可；"
                                    "intent 说 WHAT、success 可测可演示）" % key))
        if "retired" in item and not isinstance(item.get("retired"), bool):
            violations.append(v("ENUM_INVALID", cap_where + ".retired",
                                "retired 若给出须为布尔（true|false）"))
        if item.get("retired") is True:
            retired += 1
    return retired

def check_artifacts(items, where, violations):
    """artifacts 条目结构：{name, body}，name 记录内唯一（spec-authored 内容内联承载）。"""
    if not isinstance(items, list):
        violations.append(v("EMPTY_FIELD", where + ".artifacts",
                            "artifacts 缺失或不是列表（无 spec-authored 内容写空列表）"))
        return 0
    seen = set()
    for i, item in enumerate(items):
        art_where = "%s.artifacts[%d]" % (where, i)
        if not isinstance(item, dict):
            violations.append(v("EMPTY_FIELD", art_where,
                                "artifacts 条目不是映射（须含 name / body）"))
            continue
        name = item.get("name")
        if not nonempty(name):
            violations.append(v("EMPTY_FIELD", art_where + ".name",
                                "name 为空（内容类型名，如 glossary / architecture-diagrams）"))
        elif str(name) in seen:
            violations.append(v("DUPLICATE_ID", art_where + ".name",
                                "artifacts name %s 重复（同一内容类型只开一条）" % name))
        else:
            seen.add(str(name))
        if not nonempty(item.get("body")):
            violations.append(v("EMPTY_FIELD", art_where + ".body",
                                "body 为空（多行块字符串承载内容；图表一律进 artifacts）"))
    return len(items)

def check_paths(items, where, key, root, violations):
    """companions / sources：相对 project-root 的在场性。"""
    if not isinstance(items, list):
        violations.append(v("EMPTY_FIELD", "%s.%s" % (where, key),
                            "%s 缺失或不是列表（无条目写空列表）" % key))
        return 0
    for i, item in enumerate(items):
        item_where = "%s.%s[%d]" % (where, key, i)
        if not nonempty(item):
            violations.append(v("EMPTY_FIELD", item_where, "%s 条目为空" % key))
            continue
        if not os.path.exists(resolve_path(item, root)):
            hint = ("adopted companions 只记路径引用、不复制内容——路径须相对 project-root "
                    "且文件在场" if key == "companions" else
                    "sources 记录被完全吸收的源文档，路径须相对 project-root 且文件在场")
            violations.append(v("MISSING_FILE", item_where,
                                "%s 指向的 %s 不在场（%s）" % (key, item, hint)))
    return len(items)

def check_str_list(items, where, key, violations):
    """字符串列表字段（constraints / non_goals / assumptions / open_questions）。"""
    if not isinstance(items, list):
        violations.append(v("EMPTY_FIELD", "%s.%s" % (where, key),
                            "%s 缺失或不是列表（无条目写空列表）" % key))
        return 0
    for i, item in enumerate(items):
        if not nonempty(item):
            violations.append(v("EMPTY_FIELD", "%s.%s[%d]" % (where, key, i),
                                "%s 条目为空" % key))
    return len(items)

def check_verdict(verdict, where, violations, final):
    """verdict：Pass 1（coherence）+ Pass 2（preservation）两段；`--final` 要求均非空。"""
    if verdict is None:
        if final:
            violations.append(v("EMPTY_FIELD", where + ".verdict",
                                "--final 要求 verdict 两段非空：coherence 写 Pass 1 判决、"
                                "preservation.note 写 Pass 2 走查结论"))
        return
    if not isinstance(verdict, dict):
        violations.append(v("EMPTY_FIELD", where + ".verdict", "verdict 不是映射"))
        return
    coherence = verdict.get("coherence")
    if coherence is not None and not isinstance(coherence, str):
        violations.append(v("EMPTY_FIELD", where + ".verdict.coherence",
                            "coherence 须为字符串（Pass 1 coherence 判决段）"))
    elif final and not nonempty(coherence):
        violations.append(v("EMPTY_FIELD", where + ".verdict.coherence",
                            "--final 要求 coherence 非空（Pass 1：Spec Law 1-6/8 判决）"))
    preservation = verdict.get("preservation")
    if preservation is None:
        if final:
            violations.append(v("EMPTY_FIELD", where + ".verdict.preservation",
                                "--final 要求 preservation 在场（dropped + note）"))
        return
    if not isinstance(preservation, dict):
        violations.append(v("EMPTY_FIELD", where + ".verdict.preservation",
                            "preservation 不是映射（须含 dropped / note）"))
        return
    dropped = preservation.get("dropped")
    if dropped is not None and not isinstance(dropped, list):
        violations.append(v("EMPTY_FIELD", where + ".verdict.preservation.dropped",
                            "dropped 须为列表（wrapper-only 内容的留痕位；无丢弃写空列表）"))
    if final and not nonempty(preservation.get("note")):
        violations.append(v("EMPTY_FIELD", where + ".verdict.preservation.note",
                            "--final 要求 preservation.note 非空（Pass 2：逐声明走查结论）"))

def check_record(index, record, final, root, show, violations):
    """单条记录校验；返回 counts 片段。"""
    where = record_where(show, index, record)
    counts = {"capabilities": 0, "retired": 0, "companions": 0, "sources": 0,
              "artifacts": 0}
    if not isinstance(record, dict):
        violations.append(v("EMPTY_FIELD", where, "记录不是映射"))
        return counts
    rid = record.get("id")
    if not nonempty(rid):
        violations.append(v("EMPTY_FIELD", where + ".id", "id 缺失（SK-### 由 new 铸造）"))
    elif not SK_RE.fullmatch(str(rid)):
        violations.append(v("ENUM_INVALID", where + ".id",
                            "id 须为 SK-0nn（三位零填充），实为 %s" % rid))
    if not nonempty(record.get("slug")):
        violations.append(v("EMPTY_FIELD", where + ".slug",
                            "slug 缺失（slug 是记录的唯一键：同一 slug = 同一记录）"))
    title = record.get("title")
    if title is not None and not isinstance(title, str):
        violations.append(v("EMPTY_FIELD", where + ".title", "title 须为字符串"))
    status = record.get("status")
    if not nonempty(status):
        violations.append(v("EMPTY_FIELD", where + ".status", "status 缺失"))
    elif str(status) not in RECORD_STATUSES:
        violations.append(v("ENUM_INVALID", where + ".status",
                            "status 越界：%s（合法集 %s）"
                            % (status, "|".join(RECORD_STATUSES))))
    date = record.get("date")
    if not nonempty(date):
        violations.append(v("EMPTY_FIELD", where + ".date", "date 缺失"))
    elif not DATE_RE.fullmatch(str(date)):
        violations.append(v("ENUM_INVALID", where + ".date",
                            "date 须为 YYYY-MM-DD，实为 %s" % date))
    # 五字段内核（Why / Capabilities / Constraints / Non-goals / Success signal）
    if not nonempty(record.get("why")):
        violations.append(v("EMPTY_FIELD", where + ".why",
                            "why 为空（五字段之一：一段话点名 pain / opportunity / vision / "
                            "mandate 四类来源之一）"))
    counts["retired"] = check_capabilities(record.get("capabilities"), where, violations)
    counts["capabilities"] = len(record.get("capabilities")) \
        if isinstance(record.get("capabilities"), list) else 0
    check_str_list(record.get("constraints"), where, "constraints", violations)
    non_goals = record.get("non_goals")
    if not isinstance(non_goals, list):
        violations.append(v("EMPTY_FIELD", where + ".non_goals",
                            "non_goals 缺失或不是列表（Spec Law 4：至少 1 条非目标——"
                            "缺席会让下游自行填补真空）"))
    elif not non_goals:
        violations.append(v("EMPTY_FIELD", where + ".non_goals",
                            "non_goals 为空（Spec Law 4：至少 1 条非目标——缺席会让下游"
                            "自行填补真空）"))
    else:
        check_str_list(non_goals, where, "non_goals", violations)
    if not nonempty(record.get("success_signal")):
        violations.append(v("EMPTY_FIELD", where + ".success_signal",
                            "success_signal 为空（五字段之一：世界变化时刻、可测可演示，"
                            "不是仪表盘）"))
    # 可选段与承载面
    check_str_list(record.get("assumptions"), where, "assumptions", violations)
    check_str_list(record.get("open_questions"), where, "open_questions", violations)
    counts["companions"] = check_paths(record.get("companions"), where, "companions",
                                      root, violations)
    counts["sources"] = check_paths(record.get("sources"), where, "sources",
                                    root, violations)
    counts["artifacts"] = check_artifacts(record.get("artifacts"), where, violations)
    check_verdict(record.get("verdict"), where, violations, final)
    if final:
        if nonempty(status) and str(status) != "已定稿":
            violations.append(v("STATUS_MISMATCH", where + ".status",
                                "--final 要求 status: 已定稿，实为 %s" % status))
        if any(ASSUMPTION in s for _p, s in walk_strings(record, "")):
            violations.append(v("ASSUMPTION_PRESENT", where,
                                "--final 要求零 %s；未决推断须先落定（或清空标记、"
                                "把缺口写进 open_questions）" % ASSUMPTION))
    return counts

def prev_index(data):
    """旧稿索引：slug → {cap_id: retired_bool}。"""
    index = {}
    records = data.get("specs") if isinstance(data, dict) else None
    if not isinstance(records, list):
        return index
    for record in records:
        if not isinstance(record, dict) or not nonempty(record.get("slug")):
            continue
        caps = {}
        items = record.get("capabilities")
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict) and nonempty(item.get("id")):
                    caps[str(item["id"])] = item.get("retired") is True
        index.setdefault(str(record["slug"]), {"id": record.get("id"), "caps": caps})
    return index

# trace: B4 diy-spec 验收 #12c（--previous：本批唯一判 yes —— CAP 稳定不重用的机械保障）
def check_previous(data, previous, root, show, violations, scope_slugs=None):
    """--previous：按 slug 配对，旧稿 CAP 旧有新无且未标 retired → ID_UNSTABLE。

    退役豁免同看两稿：旧稿该 CAP 标 retired: true，或新稿仍留该 id 且标 retired: true。
    旧稿整条 slug 在新稿消失 → 该记录的全部 CAP 一并判丢失。
    """
    prev_path = resolve_path(previous, root)
    prev_rel = display_path(prev_path, root)
    prev_data, err = load_yaml_safe(prev_path)
    if prev_data is None and err is None:
        violations.append(v("MISSING_FILE", prev_rel, "旧稿不存在（--previous 路径无效）"))
        return
    if err is not None:
        violations.append(v("UNPARSABLE_YAML", prev_rel, "旧稿 YAML 解析失败：%s" % err))
        return
    new_index = new_index_of(data, show)
    for slug, old in prev_index(prev_data).items():
        if scope_slugs is not None and slug not in scope_slugs:
            continue
        new = new_index.get(slug)
        if new is None:
            if old["caps"]:
                violations.append(v("ID_UNSTABLE", prev_rel + " specs[%s]" % slug,
                                    "旧稿 slug %s（%s）在新稿中整条消失，其 CAP %s 一并丢失"
                                    "（CAP ID 稳定不重用：退役要标 retired: true 留痕，"
                                    "记录不删除）" % (slug, old["id"], sorted(old["caps"]))))
            continue
        for cid in sorted(old["caps"], key=cap_sort):
            if cid in new["caps"]:
                continue
            if old["caps"][cid] or new.get("retired_ids", {}).get(cid):
                continue
            violations.append(v("ID_UNSTABLE", new["where"],
                                "稳定 ID %s 在旧稿存在、新稿中缺失且未标 retired: true"
                                "（Spec Law 6：永不重编号、永不重用；退役须保留条目并标 "
                                "retired: true）——对照 --previous %s" % (cid, prev_rel)))

def cap_sort(cid):
    """CAP-N 按数字排序（CAP-2 < CAP-10）。"""
    match = re.search(r"(\d+)$", str(cid))
    return (int(match.group(1)) if match else 0, str(cid))

def new_index_of(data, show):
    """新稿索引：slug → {id, caps, retired_ids, where}。"""
    index = {}
    records = data.get("specs") if isinstance(data, dict) else None
    if not isinstance(records, list):
        return index
    for i, record in enumerate(records):
        if not isinstance(record, dict) or not nonempty(record.get("slug")):
            continue
        caps, retired_ids = {}, {}
        items = record.get("capabilities")
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict) and nonempty(item.get("id")):
                    caps[str(item["id"])] = True
                    retired_ids[str(item["id"])] = item.get("retired") is True
        index.setdefault(str(record["slug"]),
                         {"id": record.get("id"), "caps": caps,
                          "retired_ids": retired_ids,
                          "where": record_where(show, i, record)})
    return index
