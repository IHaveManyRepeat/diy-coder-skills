# -*- coding: utf-8 -*-
"""diy-spec 确定性引擎：spec-kernel.yaml 的骨架铸造（new）与校验（check）。

子命令：
  new    --slug S [--title T]：建一条记录骨架并 **铸造 `SK-###`**（三位零填充、取既有
         最大值 + 1，不重号不重用）；同 slug 已存在 → 拒绝并指出既有 `SK-xxx`（更新走
         记录就地编辑，不新建——「同一 slug = 同一记录」）。原子写。
  check  [--final] [--previous PATH] [--id SK-xxx]：五字段非空 / CAP 结构（intent +
         success 双非空、`CAP-N` 格式）/ CAP ID 记录内唯一 / slug 唯一 / companions 与
         sources 路径在场性（相对 project-root）/ artifacts 条目结构 / verdict 形状；
         **`--previous`**：按 slug 配对旧稿，旧稿 CAP 集合中「旧有新无且未标
         `retired: true`」→ `ID_UNSTABLE`（退役豁免同看两稿：旧稿该 CAP 标 retired，
         或新稿仍留该 id 且标 retired）；`--final` 附加：`status: 已定稿` + 零 `[假设]`
         + `verdict` 两段非空（自校验义务已履行）。exit 0 唯一放行。

分工裁定（任务书 §2.3）：spec-kernel 是新产物类型，不进 diyc.py check 的硬编码类型集；
本引擎沿用领域引擎形态，契约同构：exit 0 唯一放行 / `--json` 单行回执 /
`violations[{code, where, msg}]` + `counts`；写回命令回执另含 `updated`。违规码全部复用
batch3-contract §3 冻结集（**未新增码**）：`MISSING_FILE` / `UNPARSABLE_YAML` /
`DUPLICATE_ID` / `UNKNOWN_ID` / `ENUM_INVALID` / `EMPTY_FIELD` / `ASSUMPTION_PRESENT` /
`STATUS_MISMATCH` / `ID_UNSTABLE`。

事实裁定（B4 建议档归 W 项，回报第 5 项）：
  · #42「五字段非空」的判据 = `why` / `capabilities`（≥1 条且 intent + success 双非空）/
    `non_goals`（≥1 条，Spec Law 4）/ `success_signal` 逐字非空；`constraints` **键在场
    且为列表**，空列表放行——Spec Law 3 是品质判据（凑一条不淘汰设计的约束 = decoration，
    比空列表更坏），条数不设门。
  · #41 `retired` 条目的字段义务 = 退役条目的 `id` / `intent` / `success` **不失义务**
    （痕迹的价值在于「退役的是什么」）；`retired` 出现时须为布尔；退役条目仍计入 CAP ID
    唯一性与 `--previous` 在场判定。
  · #21 `--id` 缺席 → 校验全部记录（文件级：project / revisions / 记录 ID 唯一 / slug 唯一
    照查）；给出 → 记录内容面只门该条，ID 不在稿内报 `UNKNOWN_ID`。
  · #40 `--previous` 的比对范围与匹配键 = **按 `slug` 配对**（CAP-N 是记录内命名空间，
    跨记录并集比对无意义），逐记录比 CAP 集合；旧稿有、新稿整条 slug 消失 → 同判
    `ID_UNSTABLE`（整条记录的 CAP 一并丢失）。

禁手写实例解析：引擎不做 `--instance` / 白名单 / 目录推导；`--output-dir` 必填（每个子命令
各自接收），由调用方传入（SKILL.md 从 `diyc.py resolve` 取）。内容面（五字段 / CAP /
artifacts / verdict）由 LLM 直编 YAML；引擎只做骨架与校验——**`CAP-N` 由 LLM 铸造**、
引擎校验格式与唯一性（任务书 §2.4 铸造权分派）。
"""
# trace: B4 diy-spec 验收 #2（产物 schema + SK-### 稳定前缀）/#3（门禁零产出）/#4（CAP-N + retired + --previous）/12b（终门指向自带引擎）
import argparse
import datetime
import io
import json
import os
import re
import sys

import yaml

SPEC_FILE = "spec-kernel.yaml"
SK_RE = re.compile(r"SK-\d{3}")
CAP_RE = re.compile(r"CAP-\d+")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
RECORD_STATUSES = ("草稿", "已定稿")
ASSUMPTION = "[假设]"


def v(code, where, msg):
    return {"code": code, "where": where, "msg": msg}


def nonempty(value):
    return value is not None and str(value).strip() != ""


def today():
    return datetime.date.today().isoformat()


def display_path(path, project_root):
    """where 显示口径（对齐 diyc）：正斜杠 + 相对 project-root；越界回退绝对路径。"""
    try:
        rel = os.path.relpath(path, project_root)
    except ValueError:
        rel = os.path.abspath(path)
    if rel.startswith(".."):
        return os.path.abspath(path).replace("\\", "/")
    return rel.replace("\\", "/")


def load_yaml_safe(path):
    """读 YAML：(data, err)。缺失 → (None, None)；空 → ({}, None)；损坏 → (None, 原因)。"""
    if not os.path.isfile(path):
        return None, None
    try:
        with io.open(path, "r", encoding="utf-8") as f:
            return (yaml.safe_load(f) or {}), None
    except yaml.YAMLError as e:
        return None, str(e)
    except OSError as e:
        return None, str(e)


def save_yaml_atomic(path, data):
    """全文 load → 就地改 → dump → 同目录临时文件 + os.replace（契约 §3 写回纪律）。

    对齐 diyc_lib.save_yaml_atomic 先例：注释不保留；失败清理 tmp 后原样抛出。
    """
    tmp = path + ".tmp"
    try:
        with io.open(tmp, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False,
                           default_flow_style=False)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise


def collect_strings(node):
    """递归收集任意节点的字符串值（`[假设]` 扫描用，只看值不看键）。"""
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for value in node.values():
            for item in collect_strings(value):
                yield item
    elif isinstance(node, list):
        for value in node:
            for item in collect_strings(value):
                yield item


def resolve_path(value, project_root):
    """产物内路径按 project-root 解析（绝对路径原样）。"""
    text = str(value)
    return text if os.path.isabs(text) else os.path.join(project_root, text)


def project_name(root, warnings):
    """project.name 取自 diy-coder.yaml；不可用 → 回落项目目录名 + warning（零静默降级）。"""
    cfg, err = load_yaml_safe(os.path.join(root, "diy-coder.yaml"))
    if isinstance(cfg, dict):
        project = cfg.get("project")
        if isinstance(project, dict) and nonempty(project.get("name")):
            return str(project["name"])
    warnings.append(v("MISSING_FILE", "diy-coder.yaml",
                      "diy-coder.yaml 的 project.name 不可用（%s），回落项目目录名"
                      % (err or "缺该键")))
    return os.path.basename(os.path.abspath(root))


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
        if any(ASSUMPTION in s for s in collect_strings(record)):
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


# trace: B4 diy-spec 验收 #2/#3（SK-### 由引擎铸造；同 slug 拒绝 = 零写入门禁）
def cmd_new(args):
    root = os.path.abspath(args.project_root)
    out = args.output_dir
    path = os.path.join(out, SPEC_FILE)
    show = display_path(path, root)
    violations, warnings, counts = [], [], {}
    if not nonempty(args.slug):
        violations.append(v("EMPTY_FIELD", "new --slug",
                            "slug 缺失（无头不可推 → 拒绝；交互式应先在会话里问一次）"))
    data, err = load_yaml_safe(path)
    if err is not None:
        violations.append(v("UNPARSABLE_YAML", show,
                            "YAML 解析失败，拒绝写入以免覆盖：%s" % err))
    elif data is not None and not isinstance(data, dict):
        violations.append(v("EMPTY_FIELD", show,
                            "顶层不是映射（须为 project + specs + revisions），拒绝写入"))
    elif nonempty(args.slug):
        if data is None:
            name = project_name(root, warnings)
            stamp = today()
            data = {"project": {"name": name, "created": stamp, "updated": stamp},
                    "specs": [], "revisions": []}
        existing = [r for r in (data.get("specs") or []) if isinstance(r, dict)]
        hit = [r for r in existing if str(r.get("slug")) == str(args.slug)]
        if hit:
            violations.append(v("DUPLICATE_ID", show + " specs[%s]" % args.slug,
                                "slug %s 已存在（%s）：同一 slug = 同一记录——更新走就地"
                                "编辑（保持该 id、CAP 保留、新 CAP 取下一个未用号），"
                                "或用另一个 slug 新建" % (args.slug, hit[0].get("id"))))
        else:
            numbers = [int(str(r["id"])[3:]) for r in existing
                       if nonempty(r.get("id")) and SK_RE.fullmatch(str(r["id"]))]
            sid = "SK-%03d" % (max(numbers) + 1 if numbers else 1)
            record = {"id": sid, "slug": str(args.slug),
                      "title": args.title if nonempty(args.title) else "",
                      "status": "草稿", "date": today(), "why": "",
                      "capabilities": [], "constraints": [], "non_goals": [],
                      "success_signal": "", "assumptions": [], "open_questions": [],
                      "companions": [], "sources": [], "artifacts": [],
                      "verdict": {"coherence": "",
                                  "preservation": {"dropped": [], "note": ""}}}
            data["specs"] = list(data.get("specs") or []) + [record]
            data["project"] = dict(data.get("project") or {})
            data["project"]["updated"] = today()
            if not nonempty(data["project"].get("created")):
                data["project"]["created"] = today()
            try:
                os.makedirs(out, exist_ok=True)
                save_yaml_atomic(path, data)
            except OSError as e:
                violations.append(v("MISSING_FILE", show, "写盘失败（零写入）：%s" % e))
            else:
                counts = {"specs": len(data["specs"]),
                          "capabilities": 0, "id": sid}
                counts["updated"] = data["project"]["updated"]
    payload = receipt("new", args, out, not violations, violations, warnings)
    payload["counts"] = counts
    if not violations:
        payload["updated"] = counts.pop("updated")
    emit(payload, args.json, human_new)
    return 0 if not violations else 1


def cmd_check(args):
    root = os.path.abspath(args.project_root)
    out = args.output_dir
    path = os.path.join(out, SPEC_FILE)
    show = display_path(path, root)
    violations, warnings = [], []
    counts = {"records": 0, "capabilities": 0, "retired": 0, "companions": 0,
              "sources": 0, "artifacts": 0}
    data, err = load_yaml_safe(path)
    if data is None and err is None:
        violations.append(v("MISSING_FILE", show,
                            "%s 不存在（先跑 new 建记录骨架）" % SPEC_FILE))
    elif err is not None:
        violations.append(v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err))
    elif not isinstance(data, dict):
        violations.append(v("EMPTY_FIELD", show,
                            "顶层不是映射（须为 project + specs + revisions）"))
    else:
        project = data.get("project")
        if project is not None and not isinstance(project, dict):
            violations.append(v("EMPTY_FIELD", show + " project", "project 不是映射"))
        revisions = data.get("revisions")
        if revisions is not None and not isinstance(revisions, list):
            violations.append(v("EMPTY_FIELD", show + " revisions", "revisions 不是列表"))
        raw_records = data.get("specs")
        scope_slugs = None
        if raw_records is None:
            violations.append(v("EMPTY_FIELD", show + " specs",
                                "specs 缺失（集合形态；无记录写空列表）"))
        elif not isinstance(raw_records, list):
            violations.append(v("EMPTY_FIELD", show + " specs", "specs 不是列表"))
        else:
            counts["records"] = len(raw_records)
            seen_ids, seen_slugs = {}, {}
            for i, record in enumerate(raw_records):
                if not isinstance(record, dict):
                    continue
                rid, slug = record.get("id"), record.get("slug")
                if nonempty(rid):
                    if str(rid) in seen_ids:
                        violations.append(v("DUPLICATE_ID", "%s specs[%d].id" % (show, i),
                                            "记录 ID %s 重复（SK ID 稳定不重用）" % rid))
                    seen_ids[str(rid)] = i
                if nonempty(slug):
                    if str(slug) in seen_slugs:
                        violations.append(v("DUPLICATE_ID", "%s specs[%d].slug" % (show, i),
                                            "slug %s 重复（同一 slug = 同一记录，"
                                            "更新走就地编辑）" % slug))
                    seen_slugs[str(slug)] = i
            if args.id and str(args.id) not in seen_ids:
                violations.append(v("UNKNOWN_ID", show + " specs",
                                    "--id %s 在稿内不存在" % args.id))
            else:
                if args.id:
                    target = raw_records[seen_ids[str(args.id)]]
                    scope_slugs = {str(target.get("slug"))} \
                        if nonempty(target.get("slug")) else set()
                for i, record in enumerate(raw_records):
                    if args.id and (not isinstance(record, dict)
                                    or str(record.get("id")) != str(args.id)):
                        continue
                    part = check_record(i, record, args.final, root, show, violations)
                    for key, value in part.items():
                        counts[key] += value
            if args.final and not raw_records:
                violations.append(v("EMPTY_FIELD", show + " specs",
                                    "--final 要求至少 1 条记录"))
            if args.previous:
                check_previous(data, args.previous, root, show, violations, scope_slugs)
    payload = receipt("check", args, out, not violations, violations, warnings)
    payload["counts"] = counts
    emit(payload, args.json, human_check)
    return 0 if not violations else 1


def receipt(command, args, out, ok, violations, warnings):
    return {"ok": ok, "command": command, "project_root": args.project_root,
            "output_dir": os.path.normpath(out).replace("\\", "/"),
            "violations": violations, "warnings": warnings, "counts": {}}


def emit(payload, as_json, human_lines):
    if as_json:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        human_lines(payload)


def human_new(payload):
    if payload["ok"]:
        print("OK new：铸造 %s（记录 %d 条 · 文件 %s）"
              % (payload["counts"]["id"], payload["counts"]["specs"],
                 payload["output_dir"] + "/" + SPEC_FILE))
    else:
        for item in payload["violations"]:
            print("%s %s: %s" % (item["code"], item["where"], item["msg"]))
    for item in payload["warnings"]:
        print("警告 %s %s: %s" % (item["code"], item["where"], item["msg"]))
    print("汇总：违规 %d 条 · 警告 %d 条（exit %d）"
          % (len(payload["violations"]), len(payload["warnings"]),
             0 if payload["ok"] else 1))


def human_check(payload):
    counts = payload["counts"]
    if payload["ok"]:
        print("PASS：%s/%s 校验通过（记录 %d 条 · CAP %d 个 · 退役 %d 个）"
              % (payload["output_dir"], SPEC_FILE, counts["records"],
                 counts["capabilities"], counts["retired"]))
    else:
        for item in payload["violations"]:
            print("%s %s: %s" % (item["code"], item["where"], item["msg"]))
    for item in payload["warnings"]:
        print("警告 %s %s: %s" % (item["code"], item["where"], item["msg"]))
    print("汇总：违规 %d 条 · 警告 %d 条（exit %d）"
          % (len(payload["violations"]), len(payload["warnings"]),
             0 if payload["ok"] else 1))


def build_parser():
    ap = argparse.ArgumentParser(
        description="diy-spec 确定性引擎：spec-kernel.yaml 骨架铸造（new）与校验（check）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    n = sub.add_parser("new", help="建记录骨架并铸造 SK-###（同 slug 已存在 → 拒绝）")
    n.add_argument("--project-root", default=".", help="项目根（默认 .）")
    n.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    n.add_argument("--slug", required=True,
                   help="记录唯一键（同一 slug = 同一记录；源带 slug 则继承）")
    n.add_argument("--title", default=None, help="标题（可后补）")
    n.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    n.set_defaults(func=cmd_new)

    c = sub.add_parser("check", help="校验 spec-kernel.yaml（五字段/CAP/路径；--final 附加定稿义务）")
    c.add_argument("--project-root", default=".", help="项目根（默认 .）")
    c.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    c.add_argument("--final", action="store_true",
                   help="定稿校验：status: 已定稿 + 零 [假设] + verdict 两段非空")
    c.add_argument("--previous", default=None,
                   help="旧稿路径（改写既有记录前留档；按 slug 比对 CAP 集合）")
    c.add_argument("--id", default=None, help="只门一条记录（SK-xxx；文件级校验照查）")
    c.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    c.set_defaults(func=cmd_check)
    return ap


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = build_parser().parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
