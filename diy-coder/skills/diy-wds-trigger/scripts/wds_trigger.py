# -*- coding: utf-8 -*-
"""diy-wds-trigger 确定性引擎：产物列举（list）/ 整份或单条详情（show）/ 顶层骨架铸造（init）
/ wds-trigger.yaml 校验（check [--final]）/ 计数体检（metrics）。

机制：本技能是 **WDS 线的第二环**（源 `wds-2-trigger-mapping`）——把业务目标映射到用户心理
（Effect Mapping，源侧方法出处 Balic & Domingues / inUse）。产物 `{output_dir}/wds-trigger.yaml`
是**单记录多段**的内容型产物：`business_goals[]` / `personas[]`（内嵌驱动因素）/
`driver_patterns` / `priority` / `feature_impact[]` / `effect_map`，各段由会话（LLM）逐步编辑
写回；本引擎只做确定性的两件事：**铸造顶层骨架**与**机械校验**。分工写死（任务书 §2.2）：
`project.name` / `created` 与 `mode` / `entry` 由 `init` 铸造后不再由 LLM 改；五个子命令里
**只有 `init` 写盘**。

单记录形态的直接后果（承任务书 §0.2 裁定 2）：母本 §8 的两值口径**直接适用**——顶层
`project.status: 草稿|已定稿`。`list` 至多回一条；`show` 不带 `--id` 时整份全文返回、
带 `--id` 时按键寻址单条记录。

  list     列产物摘要——只回 `name` / `status` / `stage` / `mode` / `entry` / `goals` /
           `personas` / `updated` 八字段（续接锚点是 `stage`）。产物缺席是新项目常态 →
           空列表 + `ok: true`，不报错；产物损坏 → 结构化违规。`--status S` 过滤顶层
           `project.status`（非法值 `ENUM_INVALID`）。

  show     整份全文（`document` 键）。`--id TG-<n>` → 该人物记录（`record` 键）；
           不存在 → `UNKNOWN_ID`。产物缺席 → `MISSING_FILE`。

  init     铸顶层骨架（`--mode` 必填）：`project.status: 草稿` + `stage: 模式` +
           `business_goals` 的**首条记录**（`BG-1` 愿景节点空位）+ 其余五段空位 +
           `revisions: []`。**跨技能门禁（§2.3.1 冻结）**：须先有 `{output_dir}/wds-brief.yaml`
           且其 `project.status: 已定稿`，否则**零写入**（缺席 → `MISSING_FILE`；未定稿 →
           `STATUS_MISMATCH`）——缺失时提示**路由到 `diy-wds-brief`**。
           **已有合法产物 → 不覆盖**（只刷 `project.updated` + warning）；`--mode` 与产物
           不符 → `SET_MISMATCH` 且**零写入**（模式决定整条管线的参与方式，不得被静默改写）；
           产物损坏 → `UNPARSABLE_YAML` 拒绝且零写入。

  check    schema / 枚举 / 必填键（下表）/ `status` 与 `stage` 同档 / ID 形态与唯一性与
           引用可解析 / 评分重算 / 构图纪律逐条。`--final` 附加：`project.status: 已定稿` +
           `stage: 收尾` + 上游简报仍在场且已定稿 + 各段按下列键表齐备 + 零 `[假设]`。
           exit 0 唯一放行。

  metrics  人物/驱动因素**机械体检**（不阻断，承源侧「展示端自适应」口径）：人物群 2–4、每人
           3–5 正 + 3–5 负、Effect Map 连接数 = 目标数 + 2×人物数；越界 → **warning**
           （exit 0）。`--id TG-<n>` 只窄化「每人驱动因素」那一族（群数与连接数是文档级，
           恒核）；不存在 → `UNKNOWN_ID`。

必填键表（`check --final`）：
- `project`: name / created / updated / status（`草稿|已定稿`）
- `stage` ∈ 模式/目标/驱动/优先级/特征/成品/收尾（**续接锚点**；`已定稿` ⟺ `收尾`）
- `mode` ∈ W/S/D（源侧硬规则：模式由用户显式选择，禁止代选）；`entry` ∈ 工作坊/既有产物
- `business_goals[]`: **恰 1 条 `kind: 愿景` 且为首条**（Effect Map 的 `BG0` 节点）+
  **3–5 条 `kind: 目标`**；每条 id（`BG-<n>`）+ statement 非空；目标条目另需 metric /
  target / timeline 三键
- `personas[]` **2–4 条**（裁定 6）：id（`TG-<n>`）/ name / role / priority（主|其他，
  **恰一条「主」**）/ summary / context / goals / frustrations / current_behavior；
  `priority: 主` 者另需 `transformation.{before, after}`
- `personas[].driving_forces`（**嵌在人物内，不设顶层并列段——裁定 16**）：
  `positive[]` **3–5 条**（每条 id `DF-<n>.<m>+` / statement / why / **promise**）+
  `negative[]` **3–5 条**（每条 id `DF-<n>.<m>-` / statement / why / **answer**）
- `driver_patterns`: shared / unique / tensions 三键（裁定 16 的共/独/张力）；
  shared 与 unique 非空，tensions 可空；引用的驱动因素 ID 必须可解析
- `priority`: ranked_personas（覆盖全部人物恰一次，每条带 why）/ ranked_drivers（非空，带 why）/
  focus_statement.{top_group（= 排名第一的人物）, must（非空）, should, could}
- `feature_impact[]`: 每条 id（`FI-<n>`）/ name / scores.{primary, others[]} / score /
  decision（必须|应该|可选）/ rationale；score 与评分表重算一致
  （主人物 高=5/中=3/低=1；其他人物 高=3/中=1/低=0），decision 与 Must-Have 判据一致
  （必须 ⟺ 主人物命中「高」或 score ≥ max−3，max = 5 + 3×(人物数−1)）
- `effect_map`: derived_from / format / direction / config / nodes / connections /
  class_defs（**恰 4 条逐字**）/ diagram；nodes 与 business_goals / personas 一一对应；
  connections **恰为** BG→PLATFORM ∪ PLATFORM→TG ∪ TG→DF（配对严格）
- `revisions`: 列表（无修订写空列表）

跨技能读契约（任务书 §2.3.1 冻结）：本技能是 **WDS 线第二环**——入口门禁 = 上游
`{output_dir}/wds-brief.yaml` 的 `project.status: 已定稿`（读 `brief.core` / `brief.content` /
`brief.visual` / `brief.platform` 四组键）；下游 `diy-wds-scenarios` 读本产物的
`business_goals[]` / `personas[]`（`TG-<n>` + 其驱动因素） / `priority`，门禁 = 本产物的
`project.status: 已定稿`。**驱动因素数组按优先级降序排列，前 3 条即下游读取的 Top 3**。

违规码（复用 batch3-contract §3 冻结集 + B6 已批码，**本批不新增码**；两处语义复用在此登记）：
① `SET_MISMATCH` 承载「`init` 的 `--mode` 与既有产物不符」「`feature_impact[].score` 与评分表
重算不符」「`scores.others` 条数与人物数不匹配」「驱动因素 ID 的序号与所属人物不符」——
最近义项是「取值/形状与来源不匹配」；② `STATUS_MISMATCH` 承载「`project.status` 与 `stage`
不同档」「上游简报未定稿」「`feature_impact[].decision` 与 Must-Have 判据不符（含主人物高影响
却被判「可选」）」「`project.status: 已定稿` 而骨架段仍空」——最近义项是「状态/结论不自洽」。

`--previous` 判 **no**（裁定 18）：本产物是**单记录多段**，段与记录只增不减（重跑即就地补段，
不收缩集合）——不存在「旧有新无」的 ID 集合可比对；改既有内容往 `revisions` 追加。

契约（承 batch3-contract §3 / 任务书 §2.2）：exit 0 唯一放行 / 1 = 违规或被拒绝 /
2 = 用法错误（argparse 默认）/ 本批无 exit 3；`--json` → 单行回执（`ensure_ascii=False`），
无 `--json` → 中文人读行（每违规一行 `CODE where: msg` + 汇总行）；回执共同键
`{ok, command, project_root, output_dir, instance, violations, warnings, counts}`
（`instance` 恒 `null` 但**键在位**，`warnings` 与 `violations` 同形），`where` 正斜杠、
相对 project-root；**写盘命令（`init`）回执另含 `updated`**，只读子命令不含。
`--project-root`（默认 `.`）全部子命令都收；`--output-dir` **写盘子命令必填**（不设默认、
**不得**私读 `diy-coder.yaml` 当默认），只读子命令可省（省了则回执为 `null`，需读产物的
子命令明确报缺而不静默按空处理）。**`--instance` 一律不做**：实例由 SKILL.md 委托
`diyc.py resolve` 解析后以 `--output-dir` 形式传入，签名表内不出现它。
写回纪律：全文 load → 就地改 → `yaml.safe_dump(allow_unicode=True, sort_keys=False,
default_flow_style=False)` → 同目录临时文件 + `os.replace`（注释不保留；复用
`diyc_lib.save_yaml_atomic` 的同款实现——不另造一份语义不同的）。

★ **红线**：本技能的终门是**本引擎的 `check --final`**。**不得**教模型调用
`diyc.py check --type <WDS 型> --previous`——`diyc.py` 的 `CHECK_TYPES` 是 8 型封闭集，
WDS 型不在其中（`test_suite_texts.py` 有守卫会直接判红）。
"""
# trace: 迁移计划 §二 验收 #1（薄主文件 + 厚 steps）/#2（产物 schema + TG-<n>）
#        /#3（前置门禁：读上游 wds-brief.yaml 的 project.status: 已定稿）/#4（ID 唯一性与顺序性）
#        /#8（frontmatter 六字段）/#12（领域引擎接线：b 终门 / c --previous 判 no / e 写权边界）
import argparse
import io
import json
import os
import re
import sys

import yaml

PRODUCT_FILE = "wds-trigger.yaml"
UPSTREAM_FILE = "wds-brief.yaml"
UPSTREAM_SKILL = "diy-wds-brief"

# 推进与模式（`stage` 是续接锚点；`mode` / `entry` 是参与方式，由 init 铸造）
STAGE_ENUM = ("模式", "目标", "驱动", "优先级", "特征", "成品", "收尾")
MODE_ENUM = ("W", "S", "D")
ENTRY_ENUM = ("工作坊", "既有产物")
FINAL_STAGE = STAGE_ENUM[-1]

# 母本 §8 两值口径：单记录产物 → 顶层 `project.status`（裁定 2，零偏离）
STATUS_ENUM = ("草稿", "已定稿")

# 裁定 6：三组互斥口径取「采集端」较宽侧——驱动因素 3–5/类、人物群 2–4
DRIVER_RANGE = (3, 5)
PERSONA_RANGE = (2, 4)
GOAL_RANGE = (3, 5)

GOAL_KIND_ENUM = ("愿景", "目标")
PERSONA_PRIORITY_ENUM = ("主", "其他")
LEVEL_ENUM = ("高", "中", "低")
# 裁定 10：Feature Impact 保留（Primary 5/3/1、其他 3/1/0、Must-Have 阈值）
DECISION_ENUM = ("必须", "应该", "可选")
SCORE_PRIMARY = {"高": 5, "中": 3, "低": 1}
SCORE_OTHER = {"高": 3, "中": 1, "低": 0}
MUST_HAVE_SLACK = 3

# §2.3 冻结的主体段（缺一不可）；`driver_patterns` 是跨群模式，**不与 `personas[]` 并列放
# `driving_forces[]`**（裁定 16）
TOP_KEYS = ("business_goals", "personas", "driver_patterns", "priority", "feature_impact",
            "effect_map")
GOAL_KEYS = ("id", "kind", "statement")
GOAL_TARGET_KEYS = ("metric", "target", "timeline")
PERSONA_KEYS = ("id", "name", "role", "priority", "summary", "context", "goals",
                "frustrations", "current_behavior", "driving_forces")
DRIVER_KEYS = ("id", "statement", "why")
DRIVER_POSITIVE_KEY = "promise"     # 源侧：正向驱动因素各带 `[Product] Promise`
DRIVER_NEGATIVE_KEY = "answer"      # 源侧：负向驱动因素各带 `[Product] Answer`
PATTERN_KEYS = ("shared", "unique", "tensions")
PRIORITY_KEYS = ("ranked_personas", "ranked_drivers", "focus_statement")
FEATURE_KEYS = ("id", "name", "scores", "score", "decision", "rationale")
EFFECT_MAP_KEYS = ("derived_from", "format", "direction", "config", "nodes", "connections",
                   "class_defs", "diagram")

# Effect Map 构图纪律（裁定 7：08a–08h 收编为唯一定义）——四类样式色值逐字取自源 `08g:63-66`
CLASS_DEFS = ("classDef businessGoal fill:#f3f4f6,color:#1f2937,stroke:#d1d5db,stroke-width:2px",
              "classDef platform fill:#e5e7eb,color:#111827,stroke:#9ca3af,stroke-width:3px",
              "classDef targetGroup fill:#f9fafb,color:#1f2937,stroke:#d1d5db,stroke-width:2px",
              "classDef drivingForces fill:#f3f4f6,color:#1f2937,stroke:#d1d5db,stroke-width:2px")
DRIVER_EMOJI = ("✅", "❌")         # 正向 / 负向驱动因素（源 `08e`）
PLATFORM_NODE = "PLATFORM"          # 恒单个（源 `08a`）

GOAL_RE = re.compile(r"^BG-\d+$")
PERSONA_RE = re.compile(r"^TG-\d+$")
DRIVER_RE = re.compile(r"^DF-(\d+)\.(\d+)([+-])$")
FEATURE_RE = re.compile(r"^FI-\d+$")

# 令牌白名单：`{project-root}` 由引擎按 --project-root 自解析（唯一例外）；
# `{output_dir}` 是源 `{output_folder}` 的 diy 替换。其余任何 `{...}` 一律拒绝。
TOKEN_WHITELIST = ("{project-root}", "{output_dir}")
TOKEN_RE = re.compile(r"\{[A-Za-z0-9_\-]+\}")

ASSUMPTION_MARK = "[假设]"


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


def as_list(value):
    return value if isinstance(value, list) else []


def as_dict(value):
    return value if isinstance(value, dict) else {}


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
                   "引擎不设默认、不私读 diy-coder.yaml）" % (command, PRODUCT_FILE))


def read_document(path):
    """读产物 → (data | None, err)。None + err None = 缺席。"""
    data, err = load_yaml_safe(path)
    if data is not None and not isinstance(data, dict):
        return None, "顶层不是映射（须为 project + 六个主体段 + revisions）"
    return data, err


def upstream_gate(output_dir, root):
    """跨技能门禁（§2.3.1 冻结）：读 {output_dir}/wds-brief.yaml 且 project.status: 已定稿。

    返回违规列表——空列表 = 放行。缺失/未定稿一律**零写入**。
    """
    path = os.path.join(output_dir, UPSTREAM_FILE)
    show = display_path(path, root)
    data, err = load_yaml_safe(path)
    if err is not None:
        return [v("UNPARSABLE_YAML", show, "上游产物解析失败：%s（先修好简报再跑本技能）" % err)]
    if data is None:
        return [v("MISSING_FILE", show,
                  "缺上游产物——本技能的门禁 = %s 的 `project.status: 已定稿`；"
                  "请先跑 `%s`，本技能零产出停止" % (UPSTREAM_FILE, UPSTREAM_SKILL))]
    status = as_dict(data.get("project")).get("status")
    if str(status or "").strip() != STATUS_ENUM[1]:
        return [v("STATUS_MISMATCH", "%s.project.status" % show,
                  "上游简报 status = %s，门禁要求 %s（先跑 `%s` 定稿，本技能零产出停止）"
                  % (status if nonempty(status) else "空", STATUS_ENUM[1], UPSTREAM_SKILL))]
    return []


def brief_summary(data):
    """`list` 只回约定字段（不读正文）。"""
    project = as_dict(data.get("project"))
    return {"name": project.get("name"), "status": project.get("status"),
            "stage": data.get("stage"), "mode": data.get("mode"),
            "entry": data.get("entry"),
            "goals": len(as_list(data.get("business_goals"))),
            "personas": len(as_list(data.get("personas"))),
            "updated": project.get("updated")}


# ---------------------------------------------------------------- 计数体检（单一定义源）

def _range_finding(seq, low, high, where, label, require_present):
    """区间核对：越界 → (where, msg)；require_present=False 时空集合不报（草稿态常态）。"""
    count = len(seq)
    if count == 0 and not require_present:
        return None
    if low <= count <= high:
        return None
    return (where, "%s %d 条，越出 %d–%d" % (label, count, low, high))


def connection_shape(goals, personas):
    """Effect Map 连接数口径（源 `08f:70-77`）：目标数 + 2×人物数。"""
    return len(goals) + 2 * len(personas)


def expected_connections(goals, personas):
    """Effect Map 的连接（源 `08f`）：BG→PLATFORM ∪ PLATFORM→TG ∪ TG→DF（配对严格）。"""
    return (["BG%d --> PLATFORM" % i for i in range(len(goals))]
            + ["PLATFORM --> TG%d" % i for i in range(len(personas))]
            + ["TG%d --> DF%d" % (i, i) for i in range(len(personas))])


def count_findings(data, show, only_id=None, require_present=False):
    """四条越界情形的**单一定义源**：metrics 取 warning、check --final 取违规。

    四条：① 人物群 2–4；② 每人正向驱动 3–5；③ 每人负向驱动 3–5；④ 连接数 = 目标数 + 2×人物数。
    返回 (findings, needed) —— findings 为 (where, msg) 列表；needed 为连接数的实况字典。
    """
    findings = []
    personas = [x for x in as_list(data.get("personas")) if isinstance(x, dict)]
    goals = [x for x in as_list(data.get("business_goals")) if isinstance(x, dict)]
    # 群数与连接数是**文档级**——`--id` 只窄化「每人驱动因素」那一族
    label = "人物群（%s）" % "|".join(str(x.get("id") or "?") for x in personas)
    item = _range_finding(personas, PERSONA_RANGE[0], PERSONA_RANGE[1],
                          "%s.counts.personas" % show, label, require_present)
    if item is not None:
        findings.append(item)
    for index, record in enumerate(personas):
        pid = str(record.get("id") or "TG-?")
        if only_id is not None and pid != only_id:
            continue
        forces = as_dict(record.get("driving_forces"))
        for key, label in (("positive", "正向驱动因素"), ("negative", "负向驱动因素")):
            item = _range_finding(as_list(forces.get(key)),
                                  DRIVER_RANGE[0], DRIVER_RANGE[1],
                                  "%s.personas[%d].driving_forces.%s" % (show, index, key),
                                  "%s（%s）的%s" % (pid, key, label), require_present)
            if item is not None:
                findings.append(item)
    graph = as_dict(data.get("effect_map"))
    connections = as_list(graph.get("connections"))
    expected = connection_shape(goals, personas)
    needed = {"personas": len(personas), "goals": len(goals),
              "connections_expected": expected, "connections_actual": len(connections)}
    if len(connections) != expected:
        findings.append(("%s.effect_map.connections" % show,
                         "Effect Map 连接数 %d ≠ 目标数 %d + 2×人物数 %d = %d"
                         % (len(connections), len(goals), len(personas), expected)))
    return findings, needed


# ---------------------------------------------------------------- 校验

def check_goals(goals, show, final, out):
    """业务目标段：恰一条愿景（首条）+ 3–5 条目标；由 `init` 铸 `BG-<n>`。"""
    seen = set()
    vision_at = []
    targets = 0
    for index, record in enumerate(goals):
        where = "%s.business_goals[%d]" % (show, index)
        if not isinstance(record, dict):
            out.append(v("EMPTY_FIELD", where, "须为映射（id / kind / statement）"))
            continue
        ident = record.get("id")
        text = str(ident).strip() if isinstance(ident, str) else ""
        if not GOAL_RE.match(text):
            out.append(v("ENUM_INVALID", where + ".id",
                         "ID 形态越界：%s（须为 BG-<n>，裁定 8）" % (text or "空")))
        if text in seen:
            out.append(v("DUPLICATE_ID", where + ".id", "ID 重复：%s" % text))
        seen.add(text)
        kind = enum_check(record.get("kind"), GOAL_KIND_ENUM, where + ".kind",
                          "kind", out)
        if kind == GOAL_KIND_ENUM[0]:
            vision_at.append(index)
            if final:
                require(record, ("id", "statement"), where, out)
        elif kind == GOAL_KIND_ENUM[1]:
            targets += 1
            if final:
                require(record, GOAL_KEYS + GOAL_TARGET_KEYS, where, out)
    if final:
        if vision_at != [0]:
            out.append(v("STATUS_MISMATCH", "%s.business_goals" % show,
                         "须恰 1 条 `kind: 愿景` 且为首条（Effect Map 的 BG0 节点），"
                         "实为第 %s 条" % (", ".join(str(i) for i in vision_at) or "无")))
        low, high = GOAL_RANGE
        if not (low <= targets <= high):
            out.append(v("EMPTY_FIELD", "%s.business_goals" % show,
                         "业务目标须 %d–%d 条（源侧 SMART 目标口径），实为 %d"
                         % (low, high, targets)))


def persona_ids(data):
    return [str(as_dict(x).get("id") or "") for x in as_list(data.get("personas"))
            if isinstance(x, dict)]


def driver_index(data, out, show):
    """驱动因素 ID → 归属人物序号；顺带做形态 / 唯一性 / 归属核对。"""
    index = {}
    for pindex, record in enumerate(as_list(data.get("personas"))):
        if not isinstance(record, dict):
            continue
        pid = str(record.get("id") or "").strip()
        where = "%s.personas[%d]" % (show, pindex)
        if not PERSONA_RE.match(pid):
            out.append(v("ENUM_INVALID", where + ".id",
                         "ID 形态越界：%s（须为 TG-<n>，裁定 8）" % (pid or "空")))
        forces = as_dict(record.get("driving_forces"))
        for key in ("positive", "negative"):
            direction = "+" if key == "positive" else "-"
            for dindex, driver in enumerate(as_list(forces.get(key))):
                dw = "%s.driving_forces.%s[%d]" % (where, key, dindex)
                if not isinstance(driver, dict):
                    out.append(v("EMPTY_FIELD", dw, "须为映射（id / statement / why …）"))
                    continue
                ident = str(driver.get("id") or "").strip()
                match = DRIVER_RE.match(ident)
                if match is None:
                    out.append(v("ENUM_INVALID", dw + ".id",
                                 "ID 形态越界：%s（须为 DF-<n>.<m>+ / DF-<n>.<m>-，裁定 8）"
                                 % (ident or "空")))
                    continue
                if match.group(3) != direction:
                    out.append(v("SET_MISMATCH", dw + ".id",
                                 "%s 与所属数组 %s 方向不符" % (ident, key)))
                number = int(match.group(1))
                if pid and PERSONA_RE.match(pid) and number != pindex + 1:
                    out.append(v("SET_MISMATCH", dw + ".id",
                                 "%s 的序号 %d 与所属人物 %s 不符（序号 = 人物序号）"
                                 % (ident, number, pid)))
                if ident in index:
                    out.append(v("DUPLICATE_ID", dw + ".id", "驱动因素 ID 重复：%s" % ident))
                index[ident] = pid
    return index


def resolve_ids(values, known, where, label, out):
    """引用可解析核对（`id` / `ids` 两形态）。"""
    for item in as_list(values):
        if isinstance(item, str):
            ident = item
        elif isinstance(item, dict):
            ident = str(item.get("id") or "").strip()
            if not nonempty(item.get("why")):
                out.append(v("EMPTY_FIELD", where, "%s 的排序必须给 why（源侧硬要求）" % label))
        else:
            continue
        if ident and ident not in known:
            out.append(v("UNKNOWN_ID", where, "%s 引用的 ID %s 不存在" % (label, ident)))


def check_personas(data, show, final, out):
    """人物段：2–4 条、必填键、恰一条「主」、驱动因素嵌在人物内（裁定 16）。"""
    personas = as_list(data.get("personas"))
    seen = set()
    mains = 0
    for index, record in enumerate(personas):
        where = "%s.personas[%d]" % (show, index)
        if not isinstance(record, dict):
            out.append(v("EMPTY_FIELD", where, "须为映射（键表 %s）" % " / ".join(PERSONA_KEYS)))
            continue
        ident = str(record.get("id") or "").strip()
        if ident in seen:
            out.append(v("DUPLICATE_ID", where + ".id", "人物 ID 重复：%s" % ident))
        seen.add(ident)
        priority = enum_check(record.get("priority"), PERSONA_PRIORITY_ENUM,
                              where + ".priority", "priority", out)
        if priority == PERSONA_PRIORITY_ENUM[0]:
            mains += 1
        forces = as_dict(record.get("driving_forces"))
        if not final:
            continue
        require(record, PERSONA_KEYS, where, out)
        for key in ("positive", "negative"):
            mark = DRIVER_POSITIVE_KEY if key == "positive" else DRIVER_NEGATIVE_KEY
            for dindex, driver in enumerate(as_list(forces.get(key))):
                if not isinstance(driver, dict):
                    continue
                dw = "%s.driving_forces.%s[%d]" % (where, key, dindex)
                require(driver, DRIVER_KEYS + (mark,), dw, out)
        if priority == PERSONA_PRIORITY_ENUM[0]:
            require(as_dict(record.get("transformation")), ("before", "after"),
                    where + ".transformation", out)
    if final and mains != 1:
        out.append(v("STATUS_MISMATCH", "%s.personas" % show,
                     "须恰 1 条 `priority: 主`（Feature Impact 的加权基准），实为 %d 条" % mains))


def check_patterns(patterns, known, show, final, out):
    """跨群模式段（裁定 16）：共 / 独 / 张力。ID 解析恒核，键齐备只在 `--final`。"""
    if not isinstance(patterns, dict):
        out.append(v("EMPTY_FIELD", show + ".driver_patterns",
                     "须为映射（shared / unique / tensions）"))
        return
    for key in PATTERN_KEYS:
        for index, item in enumerate(as_list(patterns.get(key))):
            where = "%s.driver_patterns.%s[%d]" % (show, key, index)
            if not isinstance(item, dict):
                if final:
                    out.append(v("EMPTY_FIELD", where, "须为映射（ids / id + note）"))
                continue
            resolve_ids(item.get("ids") if key != "unique" else [item.get("id")],
                        known, where, key, out)
            if final and not nonempty(item.get("note")):
                out.append(v("EMPTY_FIELD", where + ".note", "note 为空"))
    if not final:
        return
    for key in PATTERN_KEYS:
        if key not in patterns:
            out.append(v("EMPTY_FIELD", "%s.driver_patterns.%s" % (show, key),
                         "缺跨群模式键 %s（共 / 独 / 张力）" % key))
    for key in ("shared", "unique"):
        if not nonempty(patterns.get(key)):
            out.append(v("EMPTY_FIELD", "%s.driver_patterns.%s" % (show, key),
                         "%s 为空——跨群共性与独有必须在场（张力允许为空）" % key))


def check_priority(priority, known_personas, known_drivers, show, final, out):
    """优先级段：排名带 why；焦点声明三档。ID 解析恒核，键齐备只在 `--final`。"""
    if not isinstance(priority, dict):
        out.append(v("EMPTY_FIELD", show + ".priority",
                     "须为映射（ranked_personas / ranked_drivers / focus_statement）"))
        return
    ranked = as_list(priority.get("ranked_personas"))
    resolve_ids(ranked, known_personas, "%s.priority.ranked_personas" % show, "人物排序", out)
    resolve_ids(as_list(priority.get("ranked_drivers")),
                known_drivers, "%s.priority.ranked_drivers" % show, "驱动因素排序", out)
    focus = as_dict(priority.get("focus_statement"))
    for key, label in (("must", "Must"), ("should", "Should"), ("could", "Could")):
        resolve_ids(as_list(focus.get(key)), known_drivers,
                    "%s.priority.focus_statement.%s" % (show, key), label, out)
    if not final:
        return
    require(priority, PRIORITY_KEYS, show + ".priority", out)
    order = [str(as_dict(x).get("id") or "") for x in ranked if isinstance(x, dict)]
    if sorted(order) != sorted(known_personas):
        out.append(v("SET_MISMATCH", "%s.priority.ranked_personas" % show,
                     "排序须覆盖全部人物恰一次（人物 %s，实排 %s）"
                     % ("|".join(sorted(known_personas)), "|".join(order))))
    if not focus:
        out.append(v("EMPTY_FIELD", "%s.priority.focus_statement" % show,
                     "须为映射（top_group / must / should / could）"))
        return
    top = str(focus.get("top_group") or "").strip()
    if top not in known_personas:
        out.append(v("UNKNOWN_ID", "%s.priority.focus_statement.top_group" % show,
                     "top_group = %s 不是既有 TG-<n>" % (top or "空")))
    elif order and order[0] != top:
        out.append(v("SET_MISMATCH", "%s.priority.focus_statement.top_group" % show,
                     "top_group 须 = 人物排序的第一名（%s），实为 %s" % (order[0], top)))
    if not nonempty(focus.get("must")):
        out.append(v("EMPTY_FIELD", "%s.priority.focus_statement.must" % show,
                     "Must Address 为空——焦点声明必须给必办项"))


def max_score(persona_count):
    """评分满分（源 `06c:84`）：主人物 5 + 其他每人 3。"""
    return SCORE_PRIMARY["高"] + SCORE_OTHER["高"] * max(persona_count - 1, 0)


def recompute_score(scores):
    """按评分表重算总分；形状不合法 → None。"""
    if not isinstance(scores, dict):
        return None
    primary = scores.get("primary")
    if primary not in SCORE_PRIMARY:
        return None
    total = SCORE_PRIMARY[primary]
    for value in as_list(scores.get("others")):
        if value not in SCORE_OTHER:
            return None
        total += SCORE_OTHER[value]
    return total


def check_features(features, persona_count, show, final, out):
    """特征影响段（裁定 10）：Primary 5/3/1、其他 3/1/0、Must-Have 阈值。"""
    if not final:
        return
    if not nonempty(features):
        out.append(v("EMPTY_FIELD", show + ".feature_impact",
                     "为空——裁定 10 保留特征影响分析（先设计哪个功能由它回答）"))
        return
    ceiling = max_score(persona_count)
    for index, record in enumerate(features):
        where = "%s.feature_impact[%d]" % (show, index)
        if not isinstance(record, dict):
            out.append(v("EMPTY_FIELD", where, "须为映射（键表 %s）" % " / ".join(FEATURE_KEYS)))
            continue
        require(record, FEATURE_KEYS, where, out)
        ident = str(record.get("id") or "").strip()
        if not FEATURE_RE.match(ident):
            out.append(v("ENUM_INVALID", where + ".id",
                         "ID 形态越界：%s（须为 FI-<n>；`F-*` 归主线 prd.yaml，避让）"
                         % (ident or "空")))
        enum_check(record.get("decision"), DECISION_ENUM, where + ".decision",
                   "decision", out)
        scores = as_dict(record.get("scores"))
        others = as_list(scores.get("others"))
        if others and len(others) != max(persona_count - 1, 0):
            out.append(v("SET_MISMATCH", where + ".scores.others",
                         "其他人物评分 %d 条 ≠ 人物数 %d − 1" % (len(others), persona_count)))
        computed = recompute_score(scores)
        stored = record.get("score")
        if computed is None:
            out.append(v("ENUM_INVALID", where + ".scores" ,
                         "评分越界：primary=%s / others=%s（合法集 高|中|低）"
                         % (scores.get("primary"), "|".join(str(x) for x in others))  ))
        elif stored != computed:
            out.append(v("SET_MISMATCH", where + ".score",
                         "score = %s 与评分表重算 %d 不符（主人物 高=5/中=3/低=1；"
                         "其他 高=3/中=1/低=0）" % (stored, computed)))
            continue
        decision = str(record.get("decision") or "").strip()
        primary = scores.get("primary")
        must = primary == LEVEL_ENUM[0] or stored >= ceiling - MUST_HAVE_SLACK
        if decision == DECISION_ENUM[0] and not must:
            out.append(v("STATUS_MISMATCH", where + ".decision",
                         "判「必须」但既不满足主人物命中「高」、也不满足 score ≥ max−%d（= %d）"
                         % (MUST_HAVE_SLACK, ceiling - MUST_HAVE_SLACK)))
        if decision == DECISION_ENUM[2] and primary == LEVEL_ENUM[0]:
            out.append(v("STATUS_MISMATCH", where + ".decision",
                         "主人物命中「高」的功能不得判「可选」（源 steps-v 04 硬规则）"))


def check_effect_map(graph, goals, personas, show, final, out):
    """Effect Map 段（裁定 7 收编的构图纪律）。"""
    if not isinstance(graph, dict):
        if final:
            out.append(v("EMPTY_FIELD", show + ".effect_map",
                         "须为映射（derived_from / nodes / connections / class_defs / diagram）"))
        return
    if not final:
        return
    require(graph, EFFECT_MAP_KEYS, show + ".effect_map", out)
    nodes = as_dict(graph.get("nodes"))
    expect = {"business_goals": ["BG%d" % i for i in range(len(goals))],
              "platform": PLATFORM_NODE,
              "target_groups": ["TG%d" % i for i in range(len(personas))],
              "driving_forces": ["DF%d" % i for i in range(len(personas))]}
    for key, value in expect.items():
        actual = nodes.get(key)
        if key == "platform":
            if actual != value:
                out.append(v("SET_MISMATCH", "%s.effect_map.nodes.%s" % (show, key),
                             "平台节点恒为 %s，实为 %s" % (value, actual)))
            continue
        if as_list(actual) != value:
            out.append(v("SET_MISMATCH", "%s.effect_map.nodes.%s" % (show, key),
                         "节点序列越界：须为 %s，实为 %s"
                         % ("|".join(value) or "（空）",
                            "|".join(str(x) for x in as_list(actual)) or "（空）")))
    want = sorted(expected_connections(goals, personas))
    have = sorted(str(x) for x in as_list(graph.get("connections")))
    if have != want:
        out.append(v("SET_MISMATCH", "%s.effect_map.connections" % show,
                     "连接须恰为 BG→PLATFORM ∪ PLATFORM→TG ∪ TG→DF（配对严格，本文 %s 条 / "
                     "应为 %d 条 = 目标数 + 2×人物数）" % (len(have), len(want))))
    if sorted(str(x) for x in as_list(graph.get("class_defs"))) != sorted(CLASS_DEFS):
        out.append(v("SET_MISMATCH", "%s.effect_map.class_defs" % show,
                     "四类样式须逐字取自源 `08g:63-66`（businessGoal / platform / targetGroup / "
                     "drivingForces 四条）"))
    diagram = graph.get("diagram")
    if isinstance(diagram, str) and diagram.strip():
        for mark in ("flowchart LR", PLATFORM_NODE, "classDef"):
            if mark not in diagram:
                out.append(v("EMPTY_FIELD", "%s.effect_map.diagram" % show,
                             "图内缺 %s（构图纪律见 steps/05-documents.md）" % mark))
        for emoji in DRIVER_EMOJI:
            if emoji not in diagram:
                out.append(v("EMPTY_FIELD", "%s.effect_map.diagram" % show,
                             "驱动因素须带 %s（正/负两栏）" % emoji))


def check_document(data, show, args):
    """全量校验；返回 (violations, warnings, counts)。"""
    violations = []
    project = as_dict(data.get("project"))
    if not isinstance(data.get("project"), dict):
        violations.append(v("EMPTY_FIELD", show + " project", "project 不是映射"))
    for key in ("name", "created", "updated", "status"):
        if not nonempty(project.get(key)):
            violations.append(v("EMPTY_FIELD", "%s.project.%s" % (show, key), "%s 为空" % key))
    status = project.get("status")
    status_ok = False
    if isinstance(status, str) and status.strip() in STATUS_ENUM:
        status = status.strip()
        status_ok = True
    elif nonempty(status):
        violations.append(v("ENUM_INVALID", show + ".project.status",
                            "status 越界：%s（合法集 %s）" % (status, "|".join(STATUS_ENUM))))
    elif nonempty(project.get("name")):
        violations.append(v("EMPTY_FIELD", show + ".project.status", "status 为空"))

    for key, allowed, label in (("stage", STAGE_ENUM, "stage"),
                                ("mode", MODE_ENUM, "mode"),
                                ("entry", ENTRY_ENUM, "entry")):
        if not nonempty(data.get(key)):
            violations.append(v("EMPTY_FIELD", "%s.%s" % (show, key), "%s 为空" % label))
        else:
            enum_check(data.get(key), allowed, "%s.%s" % (show, key), label, violations)
    stage = str(data.get("stage") or "").strip()
    # 同档规则：`已定稿` ⟺ `stage: 收尾`（反向不成立——`收尾` 也是 06-finish 进行中的合法中间态）
    if status_ok and status == STATUS_ENUM[1] and stage != FINAL_STAGE:
        violations.append(v("STATUS_MISMATCH", "%s.stage" % show,
                            "status: 已定稿 要求 stage: %s，实为 %s"
                            % (FINAL_STAGE, stage or "空")))

    for key in TOP_KEYS:
        if key not in data:
            violations.append(v("EMPTY_FIELD", "%s.%s" % (show, key),
                                "缺主体段 %s（§2.3 冻结）" % key))
    goals = as_list(data.get("business_goals"))
    personas = as_list(data.get("personas"))
    features = as_list(data.get("feature_impact"))
    for key, value in (("business_goals", data.get("business_goals")),
                       ("personas", data.get("personas")),
                       ("feature_impact", data.get("feature_impact"))):
        if value is not None and not isinstance(value, list):
            violations.append(v("EMPTY_FIELD", "%s.%s" % (show, key), "%s 须为列表" % key))
    check_goals(goals, show, args.final, violations)
    known_drivers = driver_index(data, violations, show)
    check_personas(data, show, args.final, violations)
    check_patterns(data.get("driver_patterns"), known_drivers, show, args.final, violations)
    check_priority(as_dict(data.get("priority")), set(persona_ids(data)), known_drivers,
                   show, args.final, violations)
    check_features(features, len(personas), show, args.final, violations)
    check_effect_map(as_dict(data.get("effect_map")), goals, personas, show, args.final,
                     violations)
    # 越界情形（与 metrics 同一实现源；裁定 6 的三组口径）——`--final` 时升级为违规
    if args.final:
        for where, msg in count_findings(data, show, require_present=True)[0]:
            violations.append(v("EMPTY_FIELD", where, msg))

    revisions = data.get("revisions")
    if revisions is None:
        violations.append(v("EMPTY_FIELD", show + " revisions", "revisions 缺失（无修订写空列表）"))
    elif not isinstance(revisions, list):
        violations.append(v("EMPTY_FIELD", show + " revisions", "revisions 不是列表"))

    violations += check_tokens(data, show)

    if args.final:
        if status_ok and status != STATUS_ENUM[1]:
            violations.append(v("STATUS_MISMATCH", show + ".project.status",
                                "--final 要求 status: 已定稿，实为 %s（先走完六个步骤文件，"
                                "再按 §2.5 六拍落盘定稿）" % status))
        if any(ASSUMPTION_MARK in text for text in collect_strings(data)):
            violations.append(v("ASSUMPTION_PRESENT", show,
                                "--final 要求零 [假设]；未决项写进 revisions 或就地补问"))
    counts = {"records": 1,
              "by_status": {status: 1} if status_ok else {},
              "by_stage": {stage: 1} if stage else {},
              "personas": len(personas), "goals": len(goals), "features": len(features)}
    # `check` 无独立 warning 通道（诊断全走 violations）——`warnings` 恒空但键在位
    return violations, [], counts


# ---------------------------------------------------------------- list / show

def cmd_list(args):
    payload = receipt_base("list", args, args.output_dir)
    out, missing = out_dir_or_violation(args, "list")
    if missing is not None:
        payload["violations"] = [missing]
        return emit(payload, args.json)
    root = os.path.abspath(args.project_root)
    path = os.path.join(out, PRODUCT_FILE)
    show = display_path(path, root)
    status = str(args.status).strip() if nonempty(args.status) else None
    violations = []
    if status is not None and status not in STATUS_ENUM:
        violations.append(v("ENUM_INVALID", "list --status",
                            "status 越界：%s（合法集 %s）" % (status, "|".join(STATUS_ENUM))))
    data, err = read_document(path)
    warnings = []
    if err is not None:
        violations.append(v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err))
    elif data is None:
        warnings.append(v("MISSING_FILE", show,
                          "%s 尚未建立（先跑 init 铸骨架）——按空列表处理" % PRODUCT_FILE))
    records = []
    if not violations and data is not None:
        item = brief_summary(data)
        if status is None or str(item.get("status") or "").strip() == status:
            records.append(item)
    payload["violations"] = violations
    payload["warnings"] = warnings
    payload["ok"] = not violations
    payload["records"] = records
    payload["counts"] = {"records": len(records),
                         "by_status": {r["status"]: 1 for r in records if nonempty(r["status"])}}
    body = ["- %s ｜ %s ｜ %s ｜ %s ｜ 目标 %s ｜ 人物 %s ｜ %s"
            % (r["name"], r["status"], r["stage"], r["mode"], r["goals"], r["personas"],
               r["updated"]) for r in records]
    return emit(payload, args.json,
                "PASS：%s 记录 %d 条%s" % (show, len(records),
                                          "（产物缺席，按空列表处理）" if data is None else ""),
                body)


def cmd_show(args):
    payload = receipt_base("show", args, args.output_dir)
    out, missing = out_dir_or_violation(args, "show")
    if missing is not None:
        payload["violations"] = [missing]
        return emit(payload, args.json)
    root = os.path.abspath(args.project_root)
    path = os.path.join(out, PRODUCT_FILE)
    show = display_path(path, root)
    data, err = read_document(path)
    violations = []
    if err is not None:
        violations.append(v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err))
    elif data is None:
        violations.append(v("MISSING_FILE", show, "产物不存在（先跑 init 铸骨架）"))
    record = None
    wanted = str(args.id).strip() if nonempty(args.id) else None
    if not violations and wanted is not None:
        record = next((x for x in as_list(data.get("personas"))
                       if isinstance(x, dict) and str(x.get("id") or "").strip() == wanted),
                      None)
        if record is None:
            violations.append(v("UNKNOWN_ID", show + ".personas",
                                "找不到记录 %s（本技能记录 ID 取 TG-<n>）" % wanted))
    payload["violations"] = violations
    payload["ok"] = not violations
    payload["document"] = data if not violations and wanted is None else None
    payload["record"] = record
    payload["counts"] = {"records": 1 if not violations else 0}
    summary = None
    if not violations:
        item = brief_summary(data)
        summary = ("PASS：%s（%s / stage: %s / %s）"
                   % (show, item["status"], item["stage"], item["mode"])
                   if wanted is None else "PASS：%s 的 %s" % (show, wanted))
    return emit(payload, args.json, summary)


# ---------------------------------------------------------------- init

def blank_document(project_root, stamp, mode, entry):
    """新建产物骨架：模式结论 + 首条记录（`BG-1` 愿景节点空位）+ 五段空位。"""
    name, warning = project_name(project_root)
    doc = {
        "project": {"name": name, "created": stamp, "updated": stamp,
                    "status": STATUS_ENUM[0]},
        "stage": STAGE_ENUM[0],
        "mode": mode,
        "entry": entry,
        "business_goals": [{"id": "BG-1", "kind": GOAL_KIND_ENUM[0]}],
        "personas": [],
        "driver_patterns": {key: [] for key in PATTERN_KEYS},
        "priority": {},
        "feature_impact": [],
        "effect_map": {},
        "revisions": [],
    }
    return doc, ([warning] if warning else [])


def cmd_init(args):
    payload = receipt_base("init", args, args.output_dir)
    out = os.path.abspath(args.output_dir)
    root = os.path.abspath(args.project_root)
    path = os.path.join(out, PRODUCT_FILE)
    show = display_path(path, root)
    violations = []
    mode = str(args.mode).strip() if args.mode is not None else ""
    if not nonempty(mode):
        violations.append(v("EMPTY_FIELD", "init --mode",
                            "模式未选：源侧硬规则——模式必须由用户显式选择（W 工作坊 / "
                            "S 建议降级 / D 代做降级），不得代选"))
    else:
        enum_check(mode, MODE_ENUM, "init --mode", "mode", violations)
    entry = str(args.entry).strip() if nonempty(args.entry) else ENTRY_ENUM[0]
    enum_check(entry, ENTRY_ENUM, "init --entry", "entry", violations)
    if violations:
        payload["violations"] = violations
        return emit(payload, args.json)
    # 跨技能门禁（§2.3.1）：上游简报必须在场且已定稿——不满足则零写入
    gate = upstream_gate(out, root)
    if gate:
        payload["violations"] = gate
        return emit(payload, args.json)
    stamp = today()
    data, err = read_document(path)
    if err is not None:
        payload["violations"] = [v("UNPARSABLE_YAML", show,
                                   "%s（拒绝且零写入——修好或另行归档后再 init）" % err)]
        return emit(payload, args.json)
    if data is None:
        doc, warnings = blank_document(root, stamp, mode, entry)
        payload["warnings"] = warnings
    else:
        # 已有骨架：**不覆盖**。模式决定整条管线的参与方式——改判走 revisions + 重跑。
        stored = str(data.get("mode") or "").strip()
        if nonempty(stored) and stored != mode:
            payload["violations"] = [v("SET_MISMATCH", "%s.mode" % show,
                                       "既有产物记录的是 %s，--mode 给的是 %s——不覆盖"
                                       "（模式决定参与方式；要改走 revisions 并经用户确认后"
                                       "再手工改，不改判则按既有值继续）" % (stored, mode))]
            return emit(payload, args.json)
        doc = data
        project = as_dict(doc.get("project"))
        warnings = []
        name = project.get("name")
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
        doc.setdefault("stage", STAGE_ENUM[0])
        doc.setdefault("mode", mode)
        doc.setdefault("entry", entry)
        doc.setdefault("business_goals",
                       [{"id": "BG-1", "kind": GOAL_KIND_ENUM[0]}])
        doc.setdefault("personas", [])
        doc.setdefault("driver_patterns", {key: [] for key in PATTERN_KEYS})
        doc.setdefault("priority", {})
        doc.setdefault("feature_impact", [])
        doc.setdefault("effect_map", {})
        doc.setdefault("revisions", [])
        warnings.append(v("SET_MISMATCH", show,
                          "产物已存在骨架——本次 init 未覆盖任何内容，只刷 project.updated；"
                          "续接请按 stage 定位"))
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
    payload["counts"] = {"records": 1, "stage": doc.get("stage")}
    return emit(payload, args.json,
                "PASS：已建 %s 骨架（%s / status: 草稿 / stage: 模式）" % (show, mode))


# ---------------------------------------------------------------- check / metrics

def cmd_check(args):
    payload = receipt_base("check", args, args.output_dir)
    out, missing = out_dir_or_violation(args, "check")
    if missing is not None:
        payload["violations"] = [missing]
        return emit(payload, args.json)
    root = os.path.abspath(args.project_root)
    path = os.path.join(out, PRODUCT_FILE)
    show = display_path(path, root)
    data, err = read_document(path)
    if err is not None:
        payload["violations"] = [v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err)]
        return emit(payload, args.json)
    if data is None:
        payload["violations"] = [v("MISSING_FILE", show,
                                   "%s 不存在（先跑 init 铸骨架）" % PRODUCT_FILE)]
        return emit(payload, args.json)
    violations, warnings, counts = check_document(data, show, args)
    if args.final:
        # 定稿时复验跨技能门禁：上游简报须仍在场且已定稿（§2.3.1）
        violations = upstream_gate(out, root) + violations
    payload["violations"] = violations
    payload["warnings"] = warnings
    payload["ok"] = not violations
    payload["final"] = bool(args.final)
    payload["counts"] = counts
    return emit(payload, args.json,
                "PASS：%s 校验通过（%s；目标 %d / 人物 %d / 特征 %d）"
                % (show, "已定稿" if args.final else "草稿可用",
                   counts["goals"], counts["personas"], counts["features"]))


def cmd_metrics(args):
    """计数体检：人物群 2–4、每人 3–5 正 + 3–5 负、连接数 = 目标数 + 2×人物数。

    越界一律 **warning**（源侧「展示端自适应」口径），exit 0；缺产物 / 坏产物 / 未知 ID
    才是违规。
    """
    payload = receipt_base("metrics", args, args.output_dir)
    out, missing = out_dir_or_violation(args, "metrics")
    if missing is not None:
        payload["violations"] = [missing]
        return emit(payload, args.json)
    root = os.path.abspath(args.project_root)
    path = os.path.join(out, PRODUCT_FILE)
    show = display_path(path, root)
    data, err = read_document(path)
    if err is not None:
        payload["violations"] = [v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err)]
        return emit(payload, args.json)
    if data is None:
        payload["violations"] = [v("MISSING_FILE", show,
                                   "%s 不存在（先跑 init 铸骨架）" % PRODUCT_FILE)]
        return emit(payload, args.json)
    wanted = str(args.id).strip() if nonempty(args.id) else None
    if wanted is not None and wanted not in persona_ids(data):
        payload["violations"] = [v("UNKNOWN_ID", show + ".personas",
                                   "找不到记录 %s（本技能记录 ID 取 TG-<n>）" % wanted)]
        return emit(payload, args.json)
    findings, needed = count_findings(data, show, only_id=wanted)
    payload["warnings"] = [v("EMPTY_FIELD", where, msg) for where, msg in findings]
    payload["ok"] = True
    payload["counts"] = needed
    body = ["- 人物群 %d ｜ 目标 %d ｜ 连接 %d/%d"
            % (needed["personas"], needed["goals"], needed["connections_actual"],
               needed["connections_expected"])]
    return emit(payload, args.json,
                "PASS：%s 体检完成（越界 %d 条，warning 不阻断）" % (show, len(findings)),
                body)


# ---------------------------------------------------------------- CLI

def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(
        description="diy-wds-trigger 确定性引擎：产物列举（list）/ 详情（show）/ 骨架铸造"
                    "（init）/ wds-trigger.yaml 校验（check）/ 计数体检（metrics）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(parser, output_required=False):
        parser.add_argument("--project-root", default=".",
                            help="项目根（默认 .）")
        parser.add_argument("--output-dir", required=output_required, default=None,
                            help="产物目录（写盘子命令必填；只读子命令可省，取值由 "
                                 "`diyc.py resolve` 回执给）")
        parser.add_argument("--json", action="store_true", help="输出单行 JSON 回执")

    ls = sub.add_parser("list", help="列产物摘要（只回 name/status/stage/mode/entry/goals/"
                                     "personas/updated）")
    common(ls)
    ls.add_argument("--status", default=None, help="按 project.status 过滤（草稿|已定稿）")
    ls.set_defaults(func=cmd_list)

    sh = sub.add_parser("show", help="整份全文；--id TG-<n> 取单个人物记录")
    common(sh)
    sh.add_argument("--id", default=None, help="记录 ID（TG-<n>）；不存在 → UNKNOWN_ID")
    sh.set_defaults(func=cmd_show)

    ini = sub.add_parser("init", help="铸顶层骨架（--mode 必填；上游简报须已定稿）")
    common(ini, output_required=True)
    ini.add_argument("--mode", required=True,
                     help="参与模式（必填：W|S|D；空值 → EMPTY_FIELD 零产出，"
                          "源侧禁止代选）")
    ini.add_argument("--entry", default=None,
                     help="入口（工作坊|既有产物，默认 工作坊）")
    ini.set_defaults(func=cmd_init)

    ck = sub.add_parser("check", help="校验 wds-trigger.yaml（schema/枚举/必填键/ID/评分/构图；"
                                      "--final 附加定稿义务）")
    common(ck)
    ck.add_argument("--final", action="store_true",
                    help="定稿校验：status: 已定稿 + stage: 收尾 + 上游已定稿 + 各段齐备 + "
                         "零 [假设]")
    ck.set_defaults(func=cmd_check)

    mt = sub.add_parser("metrics", help="计数体检（人物群 2–4 / 每人 3–5 正 + 3–5 负 / "
                                        "连接数 = 目标数 + 2×人物数；越界只给 warning）")
    common(mt)
    mt.add_argument("--id", default=None, help="窄化到单个人物（TG-<n>）")
    mt.set_defaults(func=cmd_metrics)

    args = ap.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
