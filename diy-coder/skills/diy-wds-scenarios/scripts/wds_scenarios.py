# -*- coding: utf-8 -*-
"""diy-wds-scenarios 确定性引擎：产物列举（list）/ 单条或整份详情（show）/ 骨架铸造（init）
/ wds-scenarios.yaml 校验（check [--final]，含**页面覆盖矩阵**的机械核对）。

机制：本技能是 **WDS 链的第三环**（源 `wds-3-scenarios`：把触发图翻成场景大纲与页面树）。
产物 `{output_dir}/wds-scenarios.yaml` 是**内容型产物**——`scope` / `page_inventory[]` /
`scenarios[].pages[]` 由会话（LLM）逐步编辑写回，本引擎只做确定性的两件事：**铸造骨架**
与**机械校验**（含覆盖矩阵）。四个子命令里**只有 `init` 写盘**。

**裁定 12 的落地（本引擎最要紧的一条）**：源侧 step-05 会为每个场景建目录树
（`C-UX-Scenarios/[NN-slug]/`）+ 每个页面建文件夹与样板 md + `Sketches/` 空目录。
diy 侧**只产本 YAML**：逐场景写 `scenarios[]` 记录、其下写 `pages[]` 记录——**不建任何目录树、
不建 `Sketches/`**（那是 C·3 `diy-design` 的产物位）。故 `check` 的页面类判据全部落在
**记录与引用**上，不落在文件系统上。

**裁定 8 的 ID 体系（机械核对）**：场景 `SC-<nn>`（两位数、顺序递增、不重编不复用）；
页面 `SC-<nn>.P<n>`（**废止独立的 `P-*` 前缀**）；人物 `TG-<n>`（引用上游，不复制内容）。
页面 `slug` 保留源侧 `NN.<p>-<page-slug>` 形态作**展示名**，但它必须与 ID **同源**——
这一条由 `check` 机械核对（展示名与引用键漂移是本设计最可能的坏味道）。

**裁定 17 的交接契约（必携三键）**：每条记录含 `design_intent`（`[K|C|S|D|L]`）+
`design_status`（初值 `not-started`；本技能**只设初值**，后续推进归 C·3 的 `diy-design`，
故 `--final` 要求它**恰为初值**）+ `trigger_map_context`（`target_group: TG-<n>` +
`drivers[]`：所消费的驱动因素 ID，形态取上游实值 `DF-<人物号>.<条号>+|-`，
见 `diy-wds-trigger/SKILL.md` 结构段 + `business_goal: BG-<n>`）。
**所消费的驱动必须属本记录的人物群**——引擎从驱动 ID 里认出人物号并与 `target_group` 比对，
跨群引用判 `SET_MISMATCH`（这条替代了源侧「人工看有没有抄错群」）。

**三条骨律的机械落点**（源 step-05）：
① **阳光路径零分支** —— 结构保证：`pages[]` 是有序列表、页号连续、无分支键；
② **场景名必须含人物名** —— 上游 `wds-trigger.yaml` 可解析时逐条核对（解不出则降级 warning，
   不猜、不判红）；
③ **每页恰属一条战略链** —— **页面覆盖矩阵**：每条 `page_inventory[]` 的页在全部
   `scenarios[].pages[]` 里**恰出现一次**；漏配 / 重复分配 / 清单外的页各判一条。

  list    列场景摘要——只回六字段（对照源 `00-ux-scenarios.md` 摘要表列：
          `id` / `name` / `persona` / `pages` / `priority` / `status`），**不读正文**。
          `persona` 列 = 记录的 `trigger_map_context.target_group`（单一源，不复制人物名）。
          产物缺席是新项目常态 → 空列表 + `ok: true`；`--status` 按记录级 `status` 过滤。

  show    整份全文 + 覆盖矩阵（无 `--id`）；`--id SC-<nn>` 回该场景记录，
          `--id SC-<nn>.P<n>` 回该页面记录（§2.3 登记的两级记录 ID）；不存在 → `UNKNOWN_ID`。

  init    铸骨架：`project.status: 草稿` + `scope`（`--site-type` 必填）+ `page_inventory: []`
          + **首条记录骨架**（`SC-01`，只带 `id` / 留空 `name` / `status: 草稿`）
          + `revisions: []`。**上游门禁**（§2.3.1）：读 `{output_dir}/wds-trigger.yaml`，缺失
          → `MISSING_FILE` 且**零写入**（路由 `diy-wds-trigger`）；`project.status ≠ 已定稿`
          → `STATUS_MISMATCH` 且零写入。已有合法产物 → **不覆盖**（只刷 `project.updated`
          + warning）；产物损坏 → `UNPARSABLE_YAML` 拒绝且零写入。
          ── 记录级 ID 的铸号：`init` 铸 `SC-01`，其后各条由会话按 `SC-<nn>` 规则**顺序追加**；
          `check` 判唯一（`DUPLICATE_ID`）与连续（跳号 / 重编 → `SET_MISMATCH`）。

  check   schema / 枚举 / 必填键（下表）/ ID 链 / 覆盖矩阵 / 令牌 / `[假设]`。`--final` 附加：
          `project.status: 已定稿` + 全部记录 `status: 已大纲` + 各记录键表齐备 + 覆盖 100%
          + `design_status` 为初值。exit 0 唯一放行。

必填键表（`check --final`；草稿期只核结构与枚举）：
- `project`: name / created / updated / status
- `scope`: site_type / scale / scenario_format / page_strategy（`approach` 选填）
- `page_inventory`: 列表（每条 `name` / `purpose`；`name` 是覆盖矩阵的连接键，须唯一）
- `scenarios[]`（每条）：id / name / priority / status / **design_intent** / **design_status** /
  **trigger_map_context**(target_group / drivers / business_goal) / transaction / situation /
  driving_forces(hope / worry) / device / entry / success(user / business) / pages[]
- `scenarios[].pages[]`（每条）：id / slug / name / purpose（非末页另需 exit_action）
- `revisions`: 列表（无修订写空列表）

跨技能读契约（§2.3.1 冻结）：读 `{output_dir}/wds-trigger.yaml` 的 `business_goals[]` /
`personas[]`（`TG-<n>` + 其驱动因素）/ `priority`，门禁 = 其 `project.status: 已定稿`；
**只读不写**（上游写权 100% 归 `diy-wds-trigger`）。

违规码：复用 batch3-contract §3 冻结集——本引擎用到 `MISSING_FILE` / `UNPARSABLE_YAML` /
`DUPLICATE_ID` / `UNKNOWN_ID` / `EMPTY_FIELD` / `ENUM_INVALID` / `STATUS_MISMATCH` /
`SET_MISMATCH` / `ASSUMPTION_PRESENT` 共 9 个；`TOKEN_UNRESOLVED` 沿用 B6 的已批新增码与判定
流程（**本批不新增任何码**）。三处语义复用在此登记：① `SET_MISMATCH` 承载「ID 跳号 / 页号
不连续 / slug 与 ID 不同源 / 覆盖矩阵违规」四类（最近义项 = 「集合或取值不匹配」）；
② `ENUM_INVALID` 兼作 `list --status` 非法取值码；③ `UNKNOWN_ID` 兼作「场景里出现页清单外的
页」与「`show --id` 不存在」两用。

`--previous` 判 **no**（裁定 18）：`scenarios[]` 与 `pages[]` **只增不减**（重跑即新增记录，
不收缩集合），不存在「旧有新无」的 ID 集合可比对；改既有记录往 `revisions` 追加。

契约（承 batch3-contract §3 / 任务书 §2.2）：exit 0 唯一放行 / 1 = 违规或被拒绝 /
2 = 用法错误（argparse 默认）；`--json` → 单行回执（`ensure_ascii=False`）；无 `--json`
→ 中文人读行。回执共同键 `{ok, command, project_root, output_dir, instance, violations,
warnings, counts}`（`instance` 恒 `null` 但**键在位**，`warnings` 与 `violations` 同形），
`where` 正斜杠、相对 project-root；**写盘命令（`init`）回执另含 `updated`**，只读子命令不含。
`--project-root`（默认 `.`）全部子命令都收；`--output-dir` **写盘子命令必填**（不设默认、
**不得**私读 `diy-coder.yaml` 当默认），只读子命令可省（省了则回执为 `null`，需读产物的
子命令明确报缺而不静默按空处理）。**`--instance` 一律不做**：实例由 SKILL.md 委托
`diyc.py resolve` 解析后以 `--output-dir` 形式传入。
写回纪律：全文 load → 就地改 → `yaml.safe_dump(allow_unicode=True, sort_keys=False,
default_flow_style=False)` → 同目录临时文件 + `os.replace`（复用 `diyc_lib.save_yaml_atomic`
的同款实现——不另造一份语义不同的）。

★ **红线**：本技能的终门是**本引擎的 `check --final`**。**不得**教模型调用
`diyc.py check --type <WDS 型> --previous`——`diyc.py` 的 `CHECK_TYPES` 是 8 型封闭集，
WDS 型不在其中（`test_suite_texts.py` 有守卫会直接判红）。
"""
# trace: 迁移计划 §二 验收 #1（薄主文件 + 厚 steps）/#2（产物 schema + SC-<nn>/SC-<nn>.P<n>）
#        /#3（前置门禁：读 wds-trigger.yaml 的 project.status: 已定稿）/#4（ID 唯一性与顺序性）
#        /#6（viewer 标签缺口登记）/#8（frontmatter 六字段）/#12（领域引擎接线：b 终门 / c --previous 判 no）
import argparse
import io
import json
import os
import re
import sys

import yaml

SCENARIOS_FILE = "wds-scenarios.yaml"
TRIGGER_FILE = "wds-trigger.yaml"

# 上游读契约（§2.3.1 冻结的三组键）+ 门禁判据
UPSTREAM_KEYS = ("business_goals", "personas", "priority")
FINAL_UPSTREAM_STATUS = "已定稿"

# 母本 §8 两值口径：单记录产品形态 → 顶层 `project.status`（裁定 2，零偏离）
STATUS_ENUM = ("草稿", "已定稿")
# 记录级子状态（裁定 2 的可选记录级域）：本技能定义为本条大纲的推进锚点
RECORD_STATUS_ENUM = ("草稿", "已大纲")

# 规模分析（源 step-02）四件
SITE_TYPE_ENUM = ("presentation", "dynamic", "mixed")
SCALE_ENUM = ("small", "medium", "large")
SCENARIO_FORMAT_ENUM = ("screen-flow", "storyboard", "mixed")
# 大纲模式（源 step-02 推荐 → 源 step-05 实际实现的两态；`approach` 选填）
APPROACH_ENUM = ("对话", "建议")

# 交接契约（裁定 17）：设计意图五值 + 设计状态九值（初值 not-started）
DESIGN_INTENT_ENUM = ("K", "C", "S", "D", "L")
DESIGN_STATUS_INITIAL = "not-started"
DESIGN_STATUS_ENUM = ("not-started", "discussed", "wireframed", "specified", "explored",
                      "building", "built", "approved", "removed")

# ID 形态（裁定 8）
SCENARIO_ID_RE = re.compile(r"^SC-\d{2}$")
PAGE_ID_RE = re.compile(r"^SC-(\d{2})\.P(\d+)$")
PAGE_SLUG_RE = re.compile(r"^(\d{2})\.(\d+)-")
# 上游驱动因素 ID（`DF-<人物号>.<条号>+|-`，见 `diy-wds-trigger/SKILL.md` 结构段）
# 与早期草案的 `TG-<n>.…` 兼容写法——两种都用于「所消费驱动须属本记录人物」的核对。
DRIVER_ID_RE = re.compile(r"\bDF-(\d+)\.")
TG_ID_RE = re.compile(r"\bTG-(\d+)\b")

SCOPE_REQUIRED = ("site_type", "scale", "scenario_format", "page_strategy")
SCOPE_ENUMS = (("site_type", SITE_TYPE_ENUM), ("scale", SCALE_ENUM),
               ("scenario_format", SCENARIO_FORMAT_ENUM), ("approach", APPROACH_ENUM))
INVENTORY_KEYS = ("name", "purpose")
SCENARIO_REQUIRED = ("name", "priority", "status", "design_intent", "design_status",
                     "transaction", "situation", "device", "entry")
SCENARIO_NESTED = (("trigger_map_context", "target_group"),
                   ("trigger_map_context", "drivers"),
                   ("trigger_map_context", "business_goal"),
                   ("driving_forces", "hope"), ("driving_forces", "worry"),
                   ("success", "user"), ("success", "business"))
PAGE_REQUIRED = ("id", "slug", "name", "purpose")

# 令牌白名单：`{project-root}` 由引擎按 --project-root 自解析（唯一例外）；
# `{output_dir}` 是源 `{output_folder}` 的 diy 替换。其余任何 `{...}` 一律拒绝。
TOKEN_WHITELIST = ("{project-root}", "{output_dir}")
TOKEN_RE = re.compile(r"\{[A-Za-z0-9_\-]+\}")

ASSUMPTION_MARK = "[假设]"
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}\Z")


def v(code, where, msg):
    """违规/警告项构造；where 统一正斜杠（契约 §3）。"""
    return {"code": code, "where": str(where).replace("\\", "/"), "msg": msg}


def nonempty(value):
    """非空判定：None / 空白串 / 空容器均视为空。"""
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() != ""
    if isinstance(value, (list, dict, tuple)):
        return len(value) > 0
    return True


def text_of(value):
    """取字符串值并去空白；非字符串给空串（供比较用）。"""
    return value.strip() if isinstance(value, str) else ""


def load_yaml_safe(path):
    """读 YAML：(data, err)。缺席 → (None, None)；空文件 → ({}, None)；损坏 → (None, 原因)。"""
    if not os.path.isfile(path):
        return None, None
    try:
        with io.open(path, "r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}, None
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
    """同目录 tmp + os.replace 原子替换（同款实现 = `diyc_lib.save_yaml_atomic`）。"""
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
    return os.path.basename(os.path.abspath(project_root)), v("MISSING_FILE", "diy-coder.yaml", note)


def walk_strings(node, path):
    """递归产出 (路径, 字符串值)——令牌扫描用（只扫值：键不可能承载令牌）。"""
    if isinstance(node, str):
        yield path, node
    elif isinstance(node, dict):
        for key, value in node.items():
            for item in walk_strings(value, "%s.%s" % (path, key)):
                yield item
    elif isinstance(node, list):
        for index, value in enumerate(node):
            for item in walk_strings(value, "%s[%d]" % (path, index)):
                yield item


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


def check_tokens(node, where):
    """未解析 `{...}` 令牌：白名单外一律 TOKEN_UNRESOLVED（沿用 B6 已批码）。"""
    violations = []
    for path, text in walk_strings(node, where):
        for token in TOKEN_RE.findall(text):
            if token in TOKEN_WHITELIST:
                continue
            violations.append(v("TOKEN_UNRESOLVED", path,
                                "未解析令牌 %s（白名单仅 %s）"
                                % (token, " / ".join(TOKEN_WHITELIST))))
    return violations


def require(node, keys, where, out):
    """必填键非空检查。node 不是映射时只报一条。"""
    if not isinstance(node, dict):
        out.append(v("EMPTY_FIELD", where, "须为映射（键表 %s）" % " / ".join(keys)))
        return
    for key in keys:
        if not nonempty(node.get(key)):
            out.append(v("EMPTY_FIELD", "%s.%s" % (where, key), "必填键 %s 为空" % key))


def enum_check(value, allowed, where, label, out, soft=False, warnings=None):
    """枚举检查：非法 → ENUM_INVALID（soft=True 时落 warnings）。"""
    if isinstance(value, str) and value.strip() in allowed:
        return value.strip()
    item = v("ENUM_INVALID", where, "%s 越界：%s（合法集 %s）"
             % (label, value if nonempty(value) else "空", "|".join(allowed)))
    (warnings if soft and warnings is not None else out).append(item)
    return None


# ---------------------------------------------------------------- 回执与产物读取

def receipt_base(command, args, output_dir):
    """回执公共骨架（契约 §3）：`instance` 恒 null 但键在位。"""
    return {"ok": False,
            "command": command,
            "project_root": args.project_root,
            "output_dir": (os.path.normpath(output_dir).replace("\\", "/")
                           if nonempty(output_dir) else None),
            "instance": None,
            "violations": [],
            "warnings": [],
            "counts": {}}


def emit(payload, as_json, summary_line=None, body_lines=None):
    """打印回执并返回 exit code：0 = 放行，1 = 有违规/被拒绝（契约 §3）。"""
    if as_json:
        print(json.dumps(payload, ensure_ascii=False))
        return 0 if payload.get("ok") else 1
    if not payload.get("ok"):
        for item in payload.get("violations") or []:
            print("%s %s: %s" % (item["code"], item["where"], item["msg"]))
    else:
        for line in body_lines or []:
            print(line)
        print(summary_line or "PASS：%s 完成" % payload["command"])
    for item in payload.get("warnings") or []:
        print("WARN %s %s: %s" % (item["code"], item["where"], item["msg"]))
    if payload.get("violations"):
        print("FAIL：%d 条违规（exit 1）" % len(payload["violations"]))
    return 0 if payload.get("ok") else 1


def out_dir_or_violation(args, command):
    """只读子命令的 --output-dir：可省（§2.2），读产物的子命令省了须明确报缺。"""
    if nonempty(args.output_dir):
        return os.path.abspath(args.output_dir), None
    return None, v("EMPTY_FIELD", "--output-dir",
                   "%s 需读 %s，须给 --output-dir（取值由 `diyc.py resolve` 回执给；"
                   "引擎不设默认、不私读 diy-coder.yaml）" % (command, SCENARIOS_FILE))


def read_document(path):
    """读产物 → (data | None, err)。None + err None = 缺席。"""
    data, err = load_yaml_safe(path)
    if data is not None and not isinstance(data, dict):
        return None, "顶层不是映射（须为 project + scope + page_inventory + scenarios）"
    return data, err


def upstream_personas(output_dir):
    """上游读契约（§2.3.1）：(TG-n → 人物记录, 上游路径, err)。缺席 → ({}, path, None)。"""
    path = os.path.join(output_dir, TRIGGER_FILE)
    data, err = load_yaml_safe(path)
    if not isinstance(data, dict):
        return {}, path, err
    people = {}
    for item in data.get("personas") or []:
        if isinstance(item, dict) and nonempty(item.get("id")):
            people[text_of(item.get("id"))] = item
    return people, path, None


def coverage_of(data):
    """页面覆盖矩阵（★ 本引擎的核心机械核对）。

    返回 (inventory_names, rows)：`rows` 逐行 = 场景内的每一页（含它在哪条链上）。
    连接键 = 页面的**展示名**（`page_inventory[].name` ↔ `pages[].name`）；
    引用键 = `SC-<nn>.P<n>`（父子引用）——两者都核（前者核覆盖，后者核同源）。
    """
    names = []
    for item in data.get("page_inventory") or []:
        if isinstance(item, dict) and nonempty(item.get("name")):
            names.append(text_of(item.get("name")))
    rows = []
    for record in data.get("scenarios") or []:
        if not isinstance(record, dict):
            continue
        for node in record.get("pages") or []:
            if not isinstance(node, dict):
                continue
            rows.append({"page": text_of(node.get("name")) or None,
                         "scenario": text_of(record.get("id")) or None,
                         "purpose_in_flow": node.get("purpose")})
    return names, rows


def coverage_report(data):
    """覆盖矩阵回执（`check` / `show` 共用）：counts + 行 + 三条差集。"""
    names, rows = coverage_of(data)
    assigned = [row["page"] for row in rows if row["page"]]
    seen = {}
    for name in assigned:
        seen[name] = seen.get(name, 0) + 1
    inventory_closed = set(names)
    covered = [name for name in names if seen.get(name)]
    return {"total": len(names), "covered": len(covered),
            "rate": "%d/%d" % (len(covered), len(names)),
            "matrix": rows,
            "unassigned": [name for name in names if not seen.get(name)],
            "repeated": [name for name, count in seen.items() if count > 1],
            "unknown": [name for name in seen if name not in inventory_closed],
            "duplicated": [name for name in inventory_closed
                           if names.count(name) > 1]}


# ---------------------------------------------------------------- list / show

def scenario_summary(record):
    """`list` 只回六字段（对照源 `00-ux-scenarios.md` 摘要表列；不读正文）。"""
    context = record.get("trigger_map_context")
    context = context if isinstance(context, dict) else {}
    pages = record.get("pages")
    return {"id": record.get("id"),
            "name": record.get("name"),
            "persona": context.get("target_group"),
            "pages": len(pages) if isinstance(pages, list) else 0,
            "priority": record.get("priority"),
            "status": record.get("status")}


def cmd_list(args):
    payload = receipt_base("list", args, args.output_dir)
    out, missing = out_dir_or_violation(args, "list")
    if missing is not None:
        payload["violations"] = [missing]
        return emit(payload, args.json)
    root = os.path.abspath(args.project_root)
    path = os.path.join(out, SCENARIOS_FILE)
    show = display_path(path, root)
    status = text_of(args.status) or None
    violations = []
    if status is not None and status not in RECORD_STATUS_ENUM:
        violations.append(v("ENUM_INVALID", "list --status",
                            "status 越界：%s（合法集 %s）" % (status, "|".join(RECORD_STATUS_ENUM))))
    data, err = read_document(path)
    warnings = []
    if err is not None:
        violations.append(v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err))
    elif data is None:
        warnings.append(v("MISSING_FILE", show,
                          "%s 尚未建立（先跑 init 铸骨架）——按空列表处理" % SCENARIOS_FILE))
    records = []
    if not violations and data is not None:
        for record in data.get("scenarios") or []:
            if not isinstance(record, dict):
                continue
            item = scenario_summary(record)
            if status is None or text_of(item.get("status")) == status:
                records.append(item)
    payload["violations"] = violations
    payload["warnings"] = warnings
    payload["ok"] = not violations
    payload["records"] = records
    payload["counts"] = {"records": len(records),
                         "by_status": {r["status"]: sum(
                             1 for x in records if x["status"] == r["status"])
                             for r in records if nonempty(r["status"])}}
    body = ["- %s ｜ %s ｜ %s ｜ %s 页 ｜ P%s ｜ %s"
            % (r["id"], r["name"], r["persona"], r["pages"], r["priority"], r["status"])
            for r in records]
    return emit(payload, args.json,
                "PASS：%s 记录 %d 条%s" % (show, len(records),
                                          "（产物缺席，按空列表处理）" if data is None else ""),
                body)


def find_record(data, target):
    """按记录 ID 找场景或页面：`SC-<nn>` / `SC-<nn>.P<n>`；找不到 → None。"""
    for record in data.get("scenarios") or []:
        if not isinstance(record, dict):
            continue
        if text_of(record.get("id")) == target:
            return record
        for node in record.get("pages") or []:
            if isinstance(node, dict) and text_of(node.get("id")) == target:
                return node
    return None


def cmd_show(args):
    payload = receipt_base("show", args, args.output_dir)
    out, missing = out_dir_or_violation(args, "show")
    if missing is not None:
        payload["violations"] = [missing]
        return emit(payload, args.json)
    root = os.path.abspath(args.project_root)
    path = os.path.join(out, SCENARIOS_FILE)
    show = display_path(path, root)
    data, err = read_document(path)
    violations = []
    if err is not None:
        violations.append(v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err))
    elif data is None:
        violations.append(v("MISSING_FILE", show, "产物不存在（先跑 init 铸骨架）"))
    target = text_of(args.id) or None
    body = None
    if not violations and target is not None:
        body = find_record(data, target)
        if body is None:
            violations.append(v("UNKNOWN_ID", "%s %s" % (show, target),
                                "记录 ID 不存在（场景取 SC-<nn>，页面取 SC-<nn>.P<n>）"))
    payload["violations"] = violations
    payload["ok"] = not violations
    payload["document"] = (data if target is None else body) if not violations else None
    report = coverage_report(data) if not violations else None
    if report is not None:
        payload["coverage"] = report
    payload["counts"] = {"records": 1 if not violations else 0,
                         "scenarios": len([x for x in (data or {}).get("scenarios") or []
                                           if isinstance(x, dict)]) if not violations else 0,
                         "inventory": report["total"] if report else 0,
                         "assigned": report["covered"] if report else 0}
    summary = None
    if not violations:
        if target is None:
            summary = "PASS：%s（%d 条场景 ｜ 覆盖 %s）" % (show, payload["counts"]["scenarios"],
                                                          report["rate"])
        else:
            summary = "PASS：%s %s（%s）" % (show, target, text_of(body.get("name")) or "—")
    return emit(payload, args.json, summary)


# ---------------------------------------------------------------- init

def blank_document(project_root, stamp, site_type, scale, scenario_format):
    """新建产物骨架：分诊后段（scope）空位 + 页清单空表 + 首条记录铸号（`SC-01`）。

    首条记录只有 `id` / 留空 `name` / `status: 草稿`——场景名与人物引用要到 03-plan
    「用户关卡 2」之后才存在；此处铸号保证 **ID 顺序递增且不重编不复用**。
    """
    name, warning = project_name(project_root)
    scope = {"site_type": site_type}
    if nonempty(scale):
        scope["scale"] = scale
    if nonempty(scenario_format):
        scope["scenario_format"] = scenario_format
    doc = {
        "project": {"name": name, "created": stamp, "updated": stamp,
                    "status": STATUS_ENUM[0]},
        "scope": scope,
        "page_inventory": [],
        "scenarios": [{"id": "SC-01", "name": "", "status": RECORD_STATUS_ENUM[0]}],
        "revisions": [],
    }
    return doc, ([warning] if warning else [])


def cmd_init(args):
    payload = receipt_base("init", args, args.output_dir)
    out = os.path.abspath(args.output_dir)
    root = os.path.abspath(args.project_root)
    path = os.path.join(out, SCENARIOS_FILE)
    show = display_path(path, root)
    violations = []
    site_type = text_of(args.site_type)
    if not nonempty(site_type):
        violations.append(v("EMPTY_FIELD", "init --site-type",
                            "规模分析未完成：站点类型为空（用户关卡 1 未获点头 → 零产出停止，不代拟）"))
    else:
        enum_check(site_type, SITE_TYPE_ENUM, "init --site-type", "site_type", violations)
    for value, allowed, flag, label in (
            (args.scale, SCALE_ENUM, "init --scale", "scale"),
            (args.scenario_format, SCENARIO_FORMAT_ENUM, "init --scenario-format",
             "scenario_format")):
        if nonempty(value):
            enum_check(value, allowed, flag, label, violations)
    if violations:
        payload["violations"] = violations
        return emit(payload, args.json)
    # 上游门禁（§2.3.1）：读 wds-trigger.yaml 且 project.status: 已定稿；否则零产出停止
    upstream_path = os.path.join(out, TRIGGER_FILE)
    upstream, upstream_err = load_yaml_safe(upstream_path)
    upstream_show = display_path(upstream_path, root)
    if upstream is None:
        payload["violations"] = [v(
            "MISSING_FILE", upstream_show,
            "上游产物缺失或不可解析（%s）→ 零产出停止：先跑 `diy-wds-trigger` 把触发图定稿"
            "（本技能按 project.status: 已定稿 门禁只读它的 %s）"
            % (upstream_err or "文件不存在", " / ".join(UPSTREAM_KEYS)))]
        return emit(payload, args.json)
    stored_status = text_of((upstream.get("project") or {}).get("status")) \
        if isinstance(upstream.get("project"), dict) else ""
    if stored_status != FINAL_UPSTREAM_STATUS:
        payload["violations"] = [v(
            "STATUS_MISMATCH", "%s project.status" % upstream_show,
            "上游未定稿（实为 %s，要求 %s）→ 零产出停止：回 `diy-wds-trigger` 收尾"
            % (stored_status or "空", FINAL_UPSTREAM_STATUS))]
        return emit(payload, args.json)
    stamp = today()
    data, err = read_document(path)
    if err is not None:
        payload["violations"] = [v("UNPARSABLE_YAML", show,
                                   "%s（拒绝且零写入——修好或另行归档后再 init）" % err)]
        return emit(payload, args.json)
    if data is None:
        doc, warnings = blank_document(
            root, stamp, site_type,
            text_of(args.scale) or None, text_of(args.scenario_format) or None)
        payload["warnings"] = warnings
    else:
        # 已有骨架：**不覆盖**。记录与页清单是会话逐步长出来的——重跑只刷 updated。
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
                          "updated": stamp,
                          "status": project.get("status") if nonempty(project.get("status"))
                          else STATUS_ENUM[0]}
        doc.setdefault("scope", {"site_type": site_type})
        doc.setdefault("page_inventory", [])
        doc.setdefault("scenarios", [{"id": "SC-01", "name": "",
                                      "status": RECORD_STATUS_ENUM[0]}])
        doc.setdefault("revisions", [])
        warnings.append(v("SET_MISMATCH", show,
                          "产物已存在——本次 init 未覆盖任何内容，只刷 project.updated；"
                          "续接请按记录级 status 定位（已大纲/草稿）"))
        payload["warnings"] = warnings
    try:
        if out:
            os.makedirs(out, exist_ok=True)
        save_yaml_atomic(path, doc)
    except OSError as e:
        payload["violations"] = [v("MISSING_FILE", show, "写盘失败：%s" % e)]
        return emit(payload, args.json)
    payload["ok"] = True
    payload["updated"] = stamp
    payload["counts"] = {"records": len(doc.get("scenarios") or []),
                         "inventory": len(doc.get("page_inventory") or [])}
    return emit(payload, args.json,
                "PASS：已建 %s 骨架（%s / status: 草稿 / 首条记录 SC-01 铸号）"
                % (show, site_type))


# ---------------------------------------------------------------- check

def check_scope(scope, where, final, out):
    """规模分析段（源 step-02 四件）。"""
    if not isinstance(scope, dict):
        out.append(v("EMPTY_FIELD", where, "scope 须为映射（site_type / scale / "
                                           "scenario_format / page_strategy）"))
        return
    for key, allowed in SCOPE_ENUMS:
        if nonempty(scope.get(key)):
            enum_check(scope.get(key), allowed, "%s.%s" % (where, key), key, out)
    if final:
        require(scope, SCOPE_REQUIRED, where, out)
    if final and isinstance(scope.get("page_strategy"), dict):
        strategy = scope["page_strategy"]
        if not nonempty(strategy.get("individual")) and not nonempty(strategy.get("templated")):
            out.append(v("EMPTY_FIELD", "%s.page_strategy" % where,
                         "逐页/模板化两类至少要落到一类（源 step-02 的页面文档化策略）"))


def check_inventory(inventory, where, final, out):
    """页清单（源 step-02 第 2 指令）：每条 `name` / `purpose`。"""
    if not isinstance(inventory, list):
        out.append(v("EMPTY_FIELD", where, "page_inventory 须为列表"))
        return
    if final and not inventory:
        out.append(v("EMPTY_FIELD", where, "页清单为空——覆盖矩阵无从核起"))
    for index, item in enumerate(inventory):
        ref = "%s[%d]" % (where, index)
        if not isinstance(item, dict):
            out.append(v("EMPTY_FIELD", ref, "页清单每条须为映射（name / purpose）"))
            continue
        require(item, INVENTORY_KEYS, ref, out)


def check_pages(record, ref, ctx):
    """`pages[]`：父子引用完整性 + 页号连续 + slug 与 ID 同源 + 非末页 exit_action。"""
    pages = record.get("pages")
    if pages is None:
        # 铸骨架时首条记录只带 id/name/status——页要到 04-outline 的循环里才长出来
        if ctx["final"]:
            ctx["out"].append(v("EMPTY_FIELD", "%s pages" % ref,
                                "场景至少要有一条页面记录（Q8 的最短路径）"))
        return
    if not isinstance(pages, list):
        ctx["out"].append(v("EMPTY_FIELD", "%s pages" % ref, "pages 须为列表（8 问的 Q8 路径）"))
        return
    if ctx["final"] and not pages:
        ctx["out"].append(v("EMPTY_FIELD", "%s pages" % ref, "场景至少要有一条页面记录"))
    sid = text_of(record.get("id"))
    for index, node in enumerate(pages):
        ref_p = "%s.pages[%d]" % (ref, index)
        if not isinstance(node, dict):
            ctx["out"].append(v("EMPTY_FIELD", ref_p, "页面记录须为映射"))
            continue
        pid = text_of(node.get("id"))
        if not nonempty(pid):
            ctx["out"].append(v("EMPTY_FIELD", "%s.id" % ref_p, "页面 ID 为空（须 SC-<nn>.P<n>）"))
        else:
            ctx["page_ids"].append(pid)
            match = PAGE_ID_RE.match(pid)
            if match is None:
                ctx["out"].append(v("ENUM_INVALID", "%s.id" % ref_p,
                                    "页面 ID 越界：%s（须 SC-<nn>.P<n> 两位场景号）" % pid))
            else:
                if nonempty(sid) and pid != "%s.P%s" % (sid, match.group(2)):
                    ctx["out"].append(v(
                        "SET_MISMATCH", "%s.id" % ref_p,
                        "页面 ID 前缀与所属场景不同源：页 %s 挂在 %s 下（父子引用完整性）"
                        % (pid, sid or "—")))
                if int(match.group(2)) != index + 1:
                    ctx["out"].append(v(
                        "SET_MISMATCH", "%s.id" % ref_p,
                        "页号不连续：第 %d 条记录的 ID 是 %s（阳光路径要求有序、连续、零分支）"
                        % (index + 1, pid)))
                slug = text_of(node.get("slug"))
                slug_match = PAGE_SLUG_RE.match(slug)
                if nonempty(slug) and slug_match is not None:
                    if (slug_match.group(1) != match.group(1)
                            or int(slug_match.group(2)) != int(match.group(2))):
                        ctx["out"].append(v(
                            "SET_MISMATCH", "%s.slug" % ref_p,
                            "展示名 %s 与引用键 %s 不同源（slug 的 NN.<p> 必须与 ID 一致）"
                            % (slug, pid)))
        require(node, PAGE_REQUIRED, ref_p, ctx["out"])
        if index < len(pages) - 1 and not nonempty(node.get("exit_action")):
            ctx["out"].append(v("EMPTY_FIELD", "%s.exit_action" % ref_p,
                                "非末页必须写清「什么动作带去下一步」（末页收在成功态）"))


def check_scenario(record, index, show, ctx):
    """单条 `scenarios[]` 记录（含裁定 17 的三条交接契约键）。"""
    ref = "scenarios[%d]" % index
    if not isinstance(record, dict):
        ctx["out"].append(v("EMPTY_FIELD", "%s %s" % (show, ref), "记录须为映射"))
        return
    sid = text_of(record.get("id"))
    if not nonempty(sid):
        ctx["out"].append(v("EMPTY_FIELD", "%s %s.id" % (show, ref), "场景 ID 为空（须 SC-<nn>）"))
    elif SCENARIO_ID_RE.match(sid) is None:
        ctx["out"].append(v("ENUM_INVALID", "%s %s.id" % (show, ref),
                            "场景 ID 越界：%s（须 SC-<nn> 两位序号）" % sid))
    else:
        ctx["ids"].append(sid)
    if nonempty(record.get("status")):
        enum_check(record.get("status"), RECORD_STATUS_ENUM, "%s %s.status" % (show, ref),
                   "status", ctx["out"])
    priority = record.get("priority")
    if nonempty(priority) and str(priority).strip() not in ("1", "2", "3"):
        ctx["out"].append(v("ENUM_INVALID", "%s %s.priority" % (show, ref),
                            "priority 越界：%s（合法集 1|2|3）" % priority))
    intent = record.get("design_intent")
    if nonempty(intent):
        enum_check(intent, DESIGN_INTENT_ENUM, "%s %s.design_intent" % (show, ref),
                   "design_intent", ctx["out"])
    design_status = record.get("design_status")
    if nonempty(design_status):
        enum_check(design_status, DESIGN_STATUS_ENUM, "%s %s.design_status" % (show, ref),
                   "design_status", ctx["out"])
        if ctx["final"] and text_of(design_status) != DESIGN_STATUS_INITIAL:
            ctx["out"].append(v(
                "STATUS_MISMATCH", "%s %s.design_status" % (show, ref),
                "本技能只设初值 %s（实为 %s）——设计期的推进归 C·3 的 `diy-design`"
                % (DESIGN_STATUS_INITIAL, design_status)))
    if ctx["final"]:
        require(record, SCENARIO_REQUIRED, "%s %s" % (show, ref), ctx["out"])
        for head, leaf in SCENARIO_NESTED:
            node = record.get(head)
            if not isinstance(node, dict):
                ctx["out"].append(v("EMPTY_FIELD", "%s %s.%s" % (show, ref, head),
                                    "%s 须为映射（缺 %s）" % (head, leaf)))
            elif not nonempty(node.get(leaf)):
                ctx["out"].append(v("EMPTY_FIELD", "%s %s.%s.%s" % (show, ref, head, leaf),
                                    "必填键 %s 为空" % leaf))
        if text_of(record.get("status")) != RECORD_STATUS_ENUM[1]:
            ctx["out"].append(v("STATUS_MISMATCH", "%s %s.status" % (show, ref),
                                "--final 要求每条记录 status: %s，实为 %s"
                                % (RECORD_STATUS_ENUM[1], text_of(record.get("status")) or "空")))
    context = record.get("trigger_map_context")
    context = context if isinstance(context, dict) else {}
    target = text_of(context.get("target_group"))
    drivers = context.get("drivers")
    if isinstance(drivers, list):
        for index_d, driver in enumerate(drivers):
            text = text_of(driver)
            # 驱动因素 ID 形态（上游 `wds-trigger` 的方案）：`DF-<人物号>.<条号>+|-`
            # 兼容写法：`TG-<n>.…`（早期草案）。两种都从字符串里认出人物号再比。
            match = DRIVER_ID_RE.search(text) or TG_ID_RE.search(text)
            if match is not None and nonempty(target) and ("TG-%s" % match.group(1)) != target:
                ctx["out"].append(v(
                    "SET_MISMATCH", "%s %s.trigger_map_context.drivers[%d]" % (show, ref, index_d),
                    "所消费的驱动因素 %s 属另一人物群（本记录的人物是 %s）——"
                    "场景只消费自己那条链上的驱动" % (text, target)))
    if nonempty(target) and nonempty(record.get("name")) and ctx["people"]:
        person = ctx["people"].get(target)
        person_name = text_of((person or {}).get("name")) if isinstance(person, dict) else ""
        if nonempty(person_name) and person_name not in text_of(record.get("name")):
            ctx["out"].append(v("SET_MISMATCH", "%s %s.name" % (show, ref),
                                "场景名必须含人物名（骨律）：%s 里找不到 %s"
                                % (text_of(record.get("name")), person_name)))
    check_pages(record, "%s %s" % (show, ref), ctx)


def check_ids(ids, page_ids, show, out):
    """ID 链：唯一（重复 → DUPLICATE_ID）+ 顺序连续（跳号/重编 → SET_MISMATCH）。"""
    seen = set()
    for value in ids:
        if value in seen:
            out.append(v("DUPLICATE_ID", "%s scenarios[%s]" % (show, value),
                         "场景 ID 重复：%s（稳定 ID 不得复用）" % value))
        seen.add(value)
    for index, value in enumerate(ids):
        if SCENARIO_ID_RE.match(value) is not None and value != "SC-%02d" % (index + 1):
            out.append(v("SET_MISMATCH", "%s scenarios[%d].id" % (show, index),
                         "场景 ID 须顺序递增且不重编：第 %d 条应为 SC-%02d，实为 %s"
                         % (index + 1, index + 1, value)))
    counts = {}
    for value in page_ids:
        counts[value] = counts.get(value, 0) + 1
    for value, count in counts.items():
        if count > 1:
            out.append(v("DUPLICATE_ID", "%s %s" % (show, value),
                         "页面 ID 重复 %d 次（稳定 ID 不得复用）" % count))


def check_coverage(data, show, final, out):
    """★ 页面覆盖矩阵的机械核对（三条骨律之三：每页恰属一条战略链）。"""
    report = coverage_report(data)
    for name in report["duplicated"]:
        out.append(v("DUPLICATE_ID", "%s page_inventory[%s]" % (show, name),
                     "页清单里出现了两次同名页（展示名是覆盖矩阵的连接键，须唯一）"))
    for name in report["unassigned"]:
        out.append(v("SET_MISMATCH", "%s page_inventory[%s]" % (show, name),
                     "这一页没有分给任何场景——每页必须恰属一条战略链（漏配）"))
    for name in report["repeated"]:
        out.append(v("SET_MISMATCH", "%s page_inventory[%s]" % (show, name),
                     "这一页被分给了多于一条战略链（重复分配）——每页恰属一条"))
    for name in report["unknown"]:
        out.append(v("UNKNOWN_ID", "%s page_inventory[%s]" % (show, name),
                     "场景里出现了页清单之外的页——先回 page_inventory 补条再分配"))
    if final and report["total"] and report["covered"] != report["total"]:
        out.append(v("SET_MISMATCH", "%s page_inventory" % show,
                     "--final 要求覆盖率 100%%，实为 %s" % report["rate"]))
    return report


def check_document(data, show, args, output_dir):
    """全量校验；返回 (violations, warnings, counts, coverage)。"""
    violations = []
    warnings = []
    project = data.get("project")
    if not isinstance(project, dict):
        violations.append(v("EMPTY_FIELD", show + " project", "project 不是映射"))
        project = {}
    for key in ("name", "created", "updated", "status"):
        if not nonempty(project.get(key)):
            violations.append(v("EMPTY_FIELD", "%s.project.%s" % (show, key), "%s 为空" % key))
    status = text_of(project.get("status"))
    status_ok = status in STATUS_ENUM
    if nonempty(project.get("status")) and not status_ok:
        violations.append(v("ENUM_INVALID", show + ".project.status",
                            "status 越界：%s（合法集 %s）"
                            % (project.get("status"), "|".join(STATUS_ENUM))))

    check_scope(data.get("scope"), show + ".scope", args.final, violations)
    check_inventory(data.get("page_inventory"), show + ".page_inventory", args.final, violations)

    scenarios = data.get("scenarios")
    if not isinstance(scenarios, list):
        violations.append(v("EMPTY_FIELD", show + " scenarios", "scenarios 须为列表"))
        scenarios = []
    people, upstream_path, upstream_err = upstream_personas(output_dir)
    if not people:
        warnings.append(v("MISSING_FILE",
                          display_path(upstream_path, os.path.abspath(args.project_root)),
                          "上游 %s 不可读（%s）——「场景名含人物名」的机械核对跳过"
                          "（人工在 04-outline 第 2 步的闸清单里判）"
                          % (TRIGGER_FILE, upstream_err or "文件不存在")))
    ctx = {"out": violations, "ids": [], "page_ids": [], "people": people, "final": args.final}
    for index, record in enumerate(scenarios):
        check_scenario(record, index, show, ctx)
    check_ids(ctx["ids"], ctx["page_ids"], show, violations)

    report = check_coverage(data, show, args.final, violations)

    revisions = data.get("revisions")
    if revisions is None:
        violations.append(v("EMPTY_FIELD", show + " revisions", "revisions 缺失（无修订写空列表）"))
    elif not isinstance(revisions, list):
        violations.append(v("EMPTY_FIELD", show + " revisions", "revisions 不是列表"))

    violations += check_tokens(data, show)

    if args.final:
        if status_ok and status != STATUS_ENUM[1]:
            violations.append(v("STATUS_MISMATCH", show + ".project.status",
                                "--final 要求 status: 已定稿，实为 %s（先走完 wds-scenarios 的"
                                "六个步骤文件，再按 §2.5 六拍落盘定稿）" % status))
        if not scenarios:
            violations.append(v("EMPTY_FIELD", show + " scenarios",
                                "--final 要求至少一条场景记录"))
        if any(ASSUMPTION_MARK in text for text in collect_strings(data)):
            violations.append(v("ASSUMPTION_PRESENT", show,
                                "--final 要求零 [假设]；未决项写进 revisions 或就地补问"))
    counts = {"records": len([x for x in scenarios if isinstance(x, dict)]),
              "by_status": {name: sum(1 for x in scenarios if isinstance(x, dict)
                                      and text_of(x.get("status")) == name)
                            for name in RECORD_STATUS_ENUM},
              "inventory": report["total"], "assigned": report["covered"],
              "pages": len(report["matrix"]), "coverage": report["rate"]}
    return violations, warnings, counts, report


def cmd_check(args):
    payload = receipt_base("check", args, args.output_dir)
    out, missing = out_dir_or_violation(args, "check")
    if missing is not None:
        payload["violations"] = [missing]
        return emit(payload, args.json)
    root = os.path.abspath(args.project_root)
    path = os.path.join(out, SCENARIOS_FILE)
    show = display_path(path, root)
    data, err = read_document(path)
    if err is not None:
        payload["violations"] = [v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err)]
        return emit(payload, args.json)
    if data is None:
        payload["violations"] = [v("MISSING_FILE", show,
                                   "%s 不存在（先跑 init 铸骨架）" % SCENARIOS_FILE)]
        return emit(payload, args.json)
    violations, warnings, counts, report = check_document(data, show, args, out)
    payload["violations"] = violations
    payload["warnings"] = warnings
    payload["ok"] = not violations
    payload["final"] = bool(args.final)
    payload["coverage"] = report
    payload["counts"] = counts
    return emit(payload, args.json,
                "PASS：%s 校验通过（%s；%d 条场景 ｜ 覆盖 %s）"
                % (show, "已定稿" if args.final else "草稿可用",
                   counts["records"], counts["coverage"]))


# ---------------------------------------------------------------- CLI

def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(
        description="diy-wds-scenarios 确定性引擎：产物列举（list）/ 单条或整份详情（show）/ "
                    "骨架铸造（init）/ wds-scenarios.yaml 校验（check，含页面覆盖矩阵）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(parser, output_required=False):
        parser.add_argument("--project-root", default=".",
                            help="项目根（默认 .）")
        parser.add_argument("--output-dir", required=output_required, default=None,
                            help="产物目录（写盘子命令必填；只读子命令可省，取值由 "
                                 "`diyc.py resolve` 回执给）")
        parser.add_argument("--json", action="store_true", help="输出单行 JSON 回执")

    ls = sub.add_parser("list", help="列场景摘要（只回 id/name/persona/pages/priority/status）")
    common(ls)
    ls.add_argument("--status", default=None, help="按记录级 status 过滤（草稿|已大纲）")
    ls.set_defaults(func=cmd_list)

    sh = sub.add_parser("show", help="整份全文 + 覆盖矩阵（--id 取 SC-<nn> / SC-<nn>.P<n>）")
    common(sh)
    sh.add_argument("--id", default=None, help="记录 ID（场景 SC-<nn> 或页面 SC-<nn>.P<n>）")
    sh.set_defaults(func=cmd_show)

    ini = sub.add_parser("init", help="铸骨架（--site-type 必填；上游须已定稿；不覆盖已有产物）")
    common(ini, output_required=True)
    ini.add_argument("--site-type", required=True,
                     help="站点类型（必填：presentation|dynamic|mixed；空值 → EMPTY_FIELD 零产出）")
    ini.add_argument("--scale", default=None, help="规模带（small|medium|large）")
    ini.add_argument("--scenario-format", default=None, dest="scenario_format",
                     help="场景格式（screen-flow|storyboard|mixed）")
    ini.set_defaults(func=cmd_init)

    ck = sub.add_parser("check", help="校验 wds-scenarios.yaml（schema/ID 链/覆盖矩阵/令牌；"
                                      "--final 附加定稿义务）")
    common(ck)
    ck.add_argument("--final", action="store_true",
                    help="定稿校验：status: 已定稿 + 全部记录已大纲 + 键表齐备 + 覆盖 100% + 零 [假设]")
    ck.set_defaults(func=cmd_check)

    args = ap.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
