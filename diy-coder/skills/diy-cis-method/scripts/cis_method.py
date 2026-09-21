# -*- coding: utf-8 -*-
"""diy-cis-method 确定性引擎：会话列举（list）/ 单条详情（show）/ 方法库加载（methods）/
会话记录骨架铸造（init）/ cis-method.yaml 校验（check [--final]）。

机制：本技能是**四分支创意方法引导器**（创新策略 / 问题求解 / 设计思维 / 叙事），
四条分支各有固定的源步骤序列（9 / 9 / 7 / 10 步）。产物 `{output_dir}/cis-method.yaml`
是**单 YAML 集合、内容型产物**——每步的成品内容由会话（LLM）直接编辑 YAML 写回
（`deliverable.<键>` + `open_questions`，并推进 `current_step` / `status`），本引擎只做
确定性的两件事——**铸造骨架**与**机械校验**。分工写死（任务书 §2.2）：`id` / `method` /
`date` 由 `init` 铸造后不再由 LLM 改；五个子命令里**只有 `init` 写盘**，`check` 只校验不写。

方法库落技能目录根 `cis-methods.csv`（与 `scripts/` 平级，四源合一的 115 条 / 23 类，
中文原生），路径按引擎自身位置推算（`Path(__file__).parent.parent`），两种安装布局
（源码 `diy-coder/skills/` 与安装 `.claude/skills/`）下同构成立。

  list    列会话记录——只回 `id` / `method` / `topic` / `date` / `status` / `current_step`
          六字段（源纪律：**只列不读正文**，续接锚点是 `current_step`）。产物缺席是新项目
          常态 → 空列表 + `ok: true`，不报错；产物损坏 → 结构化违规。

  show    单条记录全文（`--id CM-###`）；不在集合内 → `UNKNOWN_ID`。

  methods 加载方法库（对应 `diy-brainstorm` 的 `techniques` 命令）：默认只给**该分支工作流
          实际接入的类别**（可达集，裁定 5(e) 保真照搬源侧），`--all` 给该 `method` 的
          全部条目（**不跨分支**——语义是「含源侧未接入工作流的条目」，不是「全库 115 条」），
          `--category C` 在结果集上按类过滤（`C` 须是该 `method` 的合法类名，否则
          `ENUM_INVALID`），`--random N` 从**默认结果集**抽 N 条、`N` 超界 → 全给 + warning
          （不报错）。`--method` 必填（缺席 → `EMPTY_FIELD`；`init` 侧的缺席另由 argparse
          `required` 判为用法错误 exit 2——两处口径不同，见任务书 §2.6 ①/⑧）。

  init    建会话记录骨架（`--method` / `--topic` 必填）：铸造 `CM-###`（序号 = 现有最大 + 1，
          三位零填充，**不复用空号不重号**）、`status: 草稿` + `current_step: 1`，
          全文 load → 就地改 → 原子写（产物缺席则建文件；损坏 → 拒绝且零写入，绝不覆盖）。

  check   schema / `CM-###` 格式与唯一 / `method` 枚举 / `topic` / `date` /
          `current_step` 越界与同档（`草稿`=1；`进行中`=2..末步-1；`已完成`=末步）/
          `deliverable` 空而 `status ≠ 草稿` / **分支必填键**（下表）/ 多余键（warning）/
          `open_questions` / 未解析 `{...}` 令牌。`--final` 附加：`status: 已完成` 且零 `[假设]`。
          `--id CM-xxx` 把记录级扫描收窄到一条（找不到 → `UNKNOWN_ID`）。exit 0 唯一放行。

分支必填键表（内表 `STEP_KEYS`，共 **34 键**）：每分支 = 该分支**每个源 step 的第一个
「非注入」`<template-output>` 键**（源侧两形态：一键一标签 / 逗号分隔多键，多键按逗号切分后
取首键）。**注入项 = `date` / `user_name` / `agent_role` / `agent_name` 四项，一律不入表**。
创新策略 9 + 问题求解 9 + 设计思维 7 + 叙事 9 = 34——叙事第 10 步的唯一标签是
`agent_role, agent_name, user_name, date`（四个全是注入项）→ **该步无实键**。
`check` 按**进度**校验（`current_step` 已走到的步其首键必须已落），`--final` 时
`status: 已完成` 已把 `current_step` 顶到末步 → 等价于「分支必填键集齐全」。
**不校验全部 122 个模板键**（源侧模板键表是建议结构，非封闭集）：多余键只给 warning。
问题求解分支的源侧第 9 步 `optional="true"` → `已完成` 时 `current_step ∈ {8, 9}`
**显式放行**（本批唯一的分支内例外，不得推广到其他分支）。

可达集映射（内表 `REACHABLE_CATEGORIES`，裁定 5(e)）：默认集 = 源侧工作流实际引用的类
（保真照搬）——创新策略 25 / 问题求解 30 / 设计思维 15；**叙事分支为源侧缺陷修复后**
（Step 2 改由引擎按类呈现全部条目）默认集 = `--all` = **25**。类名逐字取 §0 裁定 5(d)
的 23 个冻结中文名（`CATEGORY_ENUM`），与 `cis-methods.csv` 的 `category` 值同词
（库行校验会逐行核对，跨工位漂移在此暴露）。

违规码：复用 batch3-contract §3 冻结集——本引擎用到 `MISSING_FILE` / `UNPARSABLE_YAML` /
`EMPTY_FIELD` / `ENUM_INVALID` / `UNKNOWN_ID` / `DUPLICATE_ID` / `STATUS_MISMATCH` /
`ASSUMPTION_PRESENT` 共 8 个；**唯一新增码 = `TOKEN_UNRESOLVED`**（**不在**冻结集内，
也不在「已批扩展」两项内）——承载 §0 裁定 8 的「白名单外的任何 `{...}` 令牌一律拒绝」
（白名单仅 `{project-root}`（唯一例外）与 `{output_dir}`（源 `{output_folder}` 的 diy 替换））。
两处语义复用在此登记：
① `UNPARSABLE_YAML` 兼作方法库（CSV）解析失败码——冻结集里没有「非 YAML 文本不可解析」码，
   造新码不如复用最近义项（msg 内点名是 CSV；承 `diy-brainstorm/scripts/brainstorm.py` 先例）；
② `ENUM_INVALID` 兼作 `--random` 超界与非可达类名的 warning 码（同族先例同款用法）。

`--previous` 判 **no**（裁定 10）：`sessions[]` 只追加、`CM-###` 顺序递增，从无 ID 集合
收缩面——不存在「旧有新无」可比对；改既有记录往 `revisions` 追加而不重编号。

契约（承 batch3-contract §3 / 任务书 §2.2）：exit 0 唯一放行 / 1 = 违规或被拒绝 /
2 = 用法错误（argparse 默认）/ **本批无 exit 3**；`--json` → 单行回执（`ensure_ascii=False`），
无 `--json` → 中文人读行（每违规一行 `CODE where: msg` + 汇总行）；回执共同键
`{ok, command, project_root, output_dir, instance, violations, warnings, counts}`
（`instance` 恒 `null` 但**键在位**，`warnings` 与 `violations` 同形），`where` 正斜杠、
相对 project-root；**写盘命令（`init`）回执另含 `updated`**，只读子命令不含。
`--project-root`（默认 `.`）全部子命令都收；`--output-dir` **写盘子命令必填**（不设默认、
**不得**私读 `diy-coder.yaml` 当默认），只读子命令可省（其 `output_dir` 回执取值 = 调用方
从 `diyc.py resolve` 回执拿到的值；省了则回执为 `null`，需读产物的子命令明确报缺而不静默按空处理）。
**`--instance` 一律不做**（裁定 9）：实例由 SKILL.md 委托 `diyc.py resolve` 解析后以
`--output-dir` 形式传入，签名表内不出现它。
写回纪律：全文 load → 就地改 → `yaml.safe_dump(allow_unicode=True, sort_keys=False,
default_flow_style=False)` → 同目录临时文件 + `os.replace`（注释不保留；复用
`diyc_lib.save_yaml_atomic` 的同款实现——不另造一份语义不同的）。
"""
# trace: 迁移计划 §二 验收 #2（产物 schema + CM-### 稳定 ID）/#3（议题非空门禁）
#        /#4（ID 链：唯一性 + 顺序性 + 不进主链）/#12（领域引擎接线：b 终门 / e 写权边界）
import argparse
import csv
import io
import json
import os
import random
import re
import sys

import yaml

CIS_FILE = "cis-method.yaml"
METHODS_FILE = "cis-methods.csv"
# 表头冻结（§0 裁定 5(a)：6 列，保英文；多出的 `method` 判别列是四库归并的新增列）
LIB_COLUMNS = ("method", "category", "name", "slug", "description", "prompts")

METHOD_ENUM = ("创新策略", "问题求解", "设计思维", "叙事")
STATUS_ENUM = ("草稿", "进行中", "已完成")
ASSUMPTION_MARK = "[假设]"

# 分支步数（源侧 workflow 的 step 数）与 `已完成` 的 current_step 域
BRANCH_STEPS = {"创新策略": 9, "问题求解": 9, "设计思维": 7, "叙事": 10}
# 问题求解源侧第 9 步 `optional="true"`：跳过时第 8 步收尾（源侧「optional 缺省则终结指令前移」）
COMPLETED_STEPS = {"创新策略": (9,), "问题求解": (8, 9), "设计思维": (7,), "叙事": (10,)}

# 注入项：不由任何 step 产出、而由模板首部或运行环境注入的占位符（四项，一律不入必填表）
INJECTION_KEYS = ("date", "user_name", "agent_role", "agent_name")

# 分支必填键表：每分支 = 每个源 step 的第一个「非注入」<template-output> 键（9+9+7+9 = 34）
STEP_KEYS = {
    "创新策略": ("company_name", "market_landscape", "current_business_model",
                 "disruption_vectors", "innovation_initiatives", "option_a_name",
                 "recommended_strategy", "phase_1", "leading_indicators"),
    "问题求解": ("problem_title", "problem_boundaries", "root_cause_analysis",
                 "driving_forces", "solution_methods", "evaluation_criteria",
                 "implementation_approach", "success_metrics", "key_learnings"),
    "设计思维": ("design_challenge", "user_insights", "pov_statement", "ideation_methods",
                 "prototype_approach", "testing_plan", "refinements"),
    # 第 10 步的唯一标签 `agent_role, agent_name, user_name, date` 全是注入项 → 该步无实键
    "叙事": ("story_purpose", "story_type", "story_beats", "emotional_arc", "opening_hook",
             "complete_story", "short_version", "best_channels", "resolution"),
}

# 各分支 `deliverable` 合法键全集（源 `template.md` 占位符去注入项）——**只用于「多余键」
# 的 warning**（非封闭集，不阻断）；键名逐字取自源模板，与 W2 分支文件的「本分支结构」节同源。
BRANCH_KEYS = {
    "创新策略": (
        "company_name", "strategic_focus", "current_situation", "strategic_challenge",
        "market_landscape", "competitive_dynamics", "market_opportunities", "market_insights",
        "current_business_model", "value_proposition", "revenue_cost_structure",
        "model_weaknesses", "disruption_vectors", "unmet_jobs", "technology_enablers",
        "strategic_whitespace", "innovation_initiatives", "business_model_innovation",
        "value_chain_opportunities", "partnership_opportunities",
        "option_a_name", "option_a_description", "option_a_pros", "option_a_cons",
        "option_b_name", "option_b_description", "option_b_pros", "option_b_cons",
        "option_c_name", "option_c_description", "option_c_pros", "option_c_cons",
        "recommended_strategy", "key_hypotheses", "success_factors",
        "phase_1", "phase_2", "phase_3",
        "leading_indicators", "lagging_indicators", "decision_gates",
        "key_risks", "risk_mitigation"),
    "问题求解": (
        "problem_title", "problem_category", "initial_problem", "refined_problem_statement",
        "problem_context", "success_criteria", "problem_boundaries", "root_cause_analysis",
        "contributing_factors", "system_dynamics", "driving_forces", "restraining_forces",
        "constraints", "key_insights", "solution_methods", "generated_solutions",
        "creative_alternatives", "evaluation_criteria", "solution_analysis",
        "recommended_solution", "solution_rationale", "implementation_approach",
        "action_steps", "timeline", "resources_needed", "responsible_parties",
        "success_metrics", "validation_plan", "risk_mitigation", "adjustment_triggers",
        "key_learnings", "what_worked", "what_to_avoid"),
    "设计思维": (
        "project_name", "design_challenge", "challenge_statement", "user_insights",
        "key_observations", "empathy_map", "pov_statement", "hmw_questions",
        "problem_insights", "ideation_methods", "generated_ideas", "top_concepts",
        "prototype_approach", "prototype_description", "features_to_test", "testing_plan",
        "user_feedback", "key_learnings", "refinements", "action_items", "success_metrics"),
    "叙事": (
        "story_type", "framework_name", "story_purpose", "target_audience", "opening_hook",
        "core_narrative", "story_beats", "emotional_arc", "resolution", "complete_story",
        "character_voice", "conflict_tension", "transformation", "emotional_touchpoints",
        "key_messages", "short_version", "medium_version", "extended_version",
        "best_channels", "audience_considerations", "tone_notes", "adaptation_suggestions",
        "refinement_opportunities", "additional_versions", "feedback_plan"),
}

# 23 个冻结中文类名（§0 裁定 5(d)：三工位逐字一致；同名跨分支由 method 列消歧）
CATEGORY_ENUM = {
    "创新策略": ("市场分析", "商业模式", "颠覆", "战略", "价值链", "技术"),
    "问题求解": ("诊断", "分析", "综合", "评估", "实施", "创意"),
    "设计思维": ("共情", "定义", "构思", "原型", "测试", "落地"),
    "叙事": ("转变", "战略", "说服", "分析", "情感"),
}

# 可达集：源侧工作流实际接入的类别（保真照搬；叙事 = 源侧缺陷修复后按类呈现全部 25 条）
REACHABLE_CATEGORIES = {
    "创新策略": ("市场分析", "商业模式", "颠覆", "战略", "价值链"),
    "问题求解": ("诊断", "分析", "综合", "评估", "实施", "创意"),
    "设计思维": ("共情", "构思", "原型"),
    "叙事": ("转变", "战略", "说服", "分析", "情感"),
}

# §0 裁定 8 令牌白名单：`{project-root}` 由引擎按 --project-root 自解析（唯一例外）；
# `{output_dir}` 是源 `{output_folder}` 的 diy 替换。其余任何 `{...}` 一律拒绝。
TOKEN_WHITELIST = ("{project-root}", "{output_dir}")
TOKEN_RE = re.compile(r"\{[A-Za-z0-9_\-]+\}")

CM_RE = re.compile(r"CM-(\d{3})\Z")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}\Z")


def v(code, where, msg):
    """违规/警告项构造；where 统一正斜杠（契约 §3）。"""
    return {"code": code, "where": str(where).replace("\\", "/"), "msg": msg}


def nonempty(value):
    """非空判定：None / 空白字符串均视为空。"""
    return value is not None and str(value).strip() != ""


def is_int(value):
    """整数判定（布尔不得充当整数：true 不是 1）。"""
    return isinstance(value, int) and not isinstance(value, bool)


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
    """同目录 tmp + os.replace 原子替换（契约 §3 写回纪律；同款实现 = `diyc_lib.save_yaml_atomic`，
    语义一致：注释不保留、失败清理 tmp 后原样抛出，不吞异常、不留残骸）。"""
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


def check_tokens(record, where):
    """未解析 `{...}` 令牌（裁定 8）：白名单外一律 TOKEN_UNRESOLVED。"""
    violations = []
    for path, text in walk_strings(record, where):
        for token in TOKEN_RE.findall(text):
            if token in TOKEN_WHITELIST:
                continue
            violations.append(v("TOKEN_UNRESOLVED", path,
                                "未解析令牌 %s（白名单仅 %s）"
                                % (token, " / ".join(TOKEN_WHITELIST))))
    return violations


# ---------------------------------------------------------------- 方法库

def methods_path():
    """方法库路径：技能目录根（`scripts/` 的上一级），两种安装布局同构。"""
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        METHODS_FILE)


def load_methods(project_root):
    """加载方法库 → (rows | None, violations)。行结构 = LIB_COLUMNS 六列。

    表头须逐字等于冻结表头（缺列 / 列名不符 / 改序 → `UNPARSABLE_YAML`，msg 点名）；
    每行的 `method` 与 `category` 逐行核对冻结枚举（跨工位漂移在此暴露）；
    `slug` 仅叙事分支填（源 `story-types.csv` 的 `story_type` 无他处可落，单列承载）。
    """
    path = methods_path()
    show = display_path(path, project_root)
    if not os.path.isfile(path):
        return None, [v("MISSING_FILE", show, "%s 不存在（技能自带方法库）" % METHODS_FILE)]
    violations = []
    rows = []
    try:
        # utf-8-sig：容忍 Windows 编辑器写入的 BOM（表头冻结不受 BOM 干扰）
        with io.open(path, "r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            header = tuple((name or "").strip() for name in (reader.fieldnames or []))
            if header != LIB_COLUMNS:
                return None, [v("UNPARSABLE_YAML", show,
                                "方法库表头不符：实为 %s（须逐字为 %s）"
                                % ("|".join(header) or "空", "|".join(LIB_COLUMNS)))]
            for index, raw in enumerate(reader):
                item = {key: (raw.get(key) or "").strip() for key in LIB_COLUMNS}
                where = "%s 第 %d 行" % (show, index + 2)
                method = item["method"]
                if method not in METHOD_ENUM:
                    violations.append(v("ENUM_INVALID", where + " method",
                                        "method 越界：%s（合法集 %s）"
                                        % (method or "空", "|".join(METHOD_ENUM))))
                    continue
                if item["category"] not in CATEGORY_ENUM[method]:
                    violations.append(v("ENUM_INVALID", where + " category",
                                        "category 越界：%s（%s 的冻结类名 %s）"
                                        % (item["category"] or "空", method,
                                           "|".join(CATEGORY_ENUM[method]))))
                    continue
                empty = [key for key in LIB_COLUMNS if key != "slug" and not item[key]]
                if empty:
                    violations.append(v("EMPTY_FIELD", where,
                                        "方法条目缺 %s" % "|".join(empty)))
                    continue
                if method == "叙事" and not item["slug"]:
                    violations.append(v("EMPTY_FIELD", where + " slug",
                                        "叙事分支的 slug（源 story_type）不得为空"))
                    continue
                rows.append(item)
    except (csv.Error, OSError, UnicodeDecodeError) as e:
        return None, [v("UNPARSABLE_YAML", show, "方法库解析失败：%s" % e)]
    if violations:
        return None, violations
    if not rows:
        return None, [v("EMPTY_FIELD", show, "方法库无数据行")]
    return rows, []


def count_by(rows, key):
    counts = {}
    for row in rows:
        counts[row[key]] = counts.get(row[key], 0) + 1
    return counts


# ---------------------------------------------------------------- 回执与产物读取

def receipt_base(command, args, output_dir):
    """回执公共骨架（契约 §3 schema）：`instance` 恒 null 但键在位。"""
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


def read_sessions(path, show):
    """读产物并取 sessions 列表 → (records | None, violations, warnings)。None = 产物缺席。"""
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


def out_dir_or_violation(payload, args, command):
    """只读子命令的 --output-dir：可省（§2.2），读产物的子命令省了须明确报缺。"""
    if nonempty(args.output_dir):
        return os.path.abspath(args.output_dir), None
    return None, v("EMPTY_FIELD", "--output-dir",
                   "%s 需读 %s，须给 --output-dir（取值由 `diyc.py resolve` 回执给；"
                   "引擎不设默认、不私读 diy-coder.yaml）" % (command, CIS_FILE))


# ---------------------------------------------------------------- list / show

def cmd_list(args):
    payload = receipt_base("list", args, args.output_dir)
    out, missing = out_dir_or_violation(payload, args, "list")
    if missing is not None:
        payload["violations"] = [missing]
        return emit(payload, args.json)
    root = os.path.abspath(args.project_root)
    path = os.path.join(out, CIS_FILE)
    show = display_path(path, root)
    records, violations, warnings = read_sessions(path, show)
    payload["violations"] = violations
    payload["warnings"] = warnings
    method = str(args.method).strip() if nonempty(args.method) else None
    if method is not None and method not in METHOD_ENUM:
        payload["violations"] = violations + [
            v("ENUM_INVALID", "list --method", "method 越界：%s（合法集 %s）"
              % (method, "|".join(METHOD_ENUM)))]
    sessions = []
    for rec in records or []:
        if not isinstance(rec, dict):
            continue
        if method is not None and str(rec.get("method") or "").strip() != method:
            continue
        sessions.append({"id": rec.get("id"), "method": rec.get("method"),
                         "topic": rec.get("topic"), "date": rec.get("date"),
                         "status": rec.get("status"), "current_step": rec.get("current_step")})
    payload["ok"] = not payload["violations"]
    payload["sessions"] = sessions
    payload["counts"] = {"sessions": len(sessions),
                         "by_status": count_by([{"k": s["status"]} for s in sessions
                                                if nonempty(s["status"])], "k")}
    body = ["- %s ｜ %s ｜ %s ｜ %s ｜ %s ｜ 第 %s 步"
            % (s["id"], s["method"], s["topic"], s["date"], s["status"], s["current_step"])
            for s in sessions]
    return emit(payload, args.json,
                "PASS：%s 记录 %d 条%s" % (show, len(sessions),
                                          "（产物缺席，按空列表处理）" if records is None else ""),
                body)


def cmd_show(args):
    payload = receipt_base("show", args, args.output_dir)
    out, missing = out_dir_or_violation(payload, args, "show")
    if missing is not None:
        payload["violations"] = [missing]
        return emit(payload, args.json)
    root = os.path.abspath(args.project_root)
    path = os.path.join(out, CIS_FILE)
    show = display_path(path, root)
    records, violations, warnings = read_sessions(path, show)
    payload["warnings"] = warnings
    target = str(args.id).strip()
    if not CM_RE.fullmatch(target):
        violations.append(v("ENUM_INVALID", "show --id",
                            "id 须为 CM-###（三位零填充），实为 %s" % target))
    found = None
    for rec in records or []:
        if isinstance(rec, dict) and str(rec.get("id") or "").strip() == target:
            found = rec
            break
    if found is None and not violations:
        violations.append(v("UNKNOWN_ID", "show --id",
                            "%s 不在 %s 的 sessions[] 内" % (target, show)))
    payload["violations"] = violations
    payload["ok"] = not violations
    payload["session"] = found
    payload["counts"] = {"sessions": len(records or [])}
    return emit(payload, args.json,
                "PASS：%s 记录 %s（%s / %s）" % (show, target, (found or {}).get("method"),
                                               (found or {}).get("status")))


# ---------------------------------------------------------------- methods

def cmd_methods(args):
    payload = receipt_base("methods", args, args.output_dir)
    root = os.path.abspath(args.project_root)
    method = str(args.method).strip() if nonempty(args.method) else ""
    if not method:
        payload["violations"] = [v("EMPTY_FIELD", "methods --method",
                                   "--method 必填（四条分支：%s）" % "|".join(METHOD_ENUM))]
        payload["counts"] = {"methods": 0, "library": 0}
        return emit(payload, args.json)
    if method not in METHOD_ENUM:
        payload["violations"] = [v("ENUM_INVALID", "methods --method",
                                   "method 越界：%s（合法集 %s）"
                                   % (method, "|".join(METHOD_ENUM)))]
        payload["counts"] = {"methods": 0, "library": 0}
        return emit(payload, args.json)
    rows, violations = load_methods(root)
    if violations:
        payload["violations"] = violations
        payload["counts"] = {"methods": 0, "library": 0}
        return emit(payload, args.json)
    method_rows = [row for row in rows if row["method"] == method]
    if not method_rows:
        payload["violations"] = [v("EMPTY_FIELD", METHODS_FILE,
                                   "库内无 %s 分支的条目" % method)]
        payload["counts"] = {"methods": 0, "library": len(rows)}
        return emit(payload, args.json)
    warnings = []
    # 默认集 = 该分支工作流实际接入的类（可达集）；--all = 该 method 全部条目（不跨分支）
    picked = list(method_rows) if args.all else [
        row for row in method_rows if row["category"] in REACHABLE_CATEGORIES[method]]
    if args.category is not None:
        category = str(args.category).strip()
        if category not in CATEGORY_ENUM[method]:
            payload["violations"] = [v("ENUM_INVALID", "methods --category",
                                       "category 越界：%s（%s 的合法类名 %s）"
                                       % (category, method, "|".join(CATEGORY_ENUM[method])))]
            payload["counts"] = {"methods": 0, "library": len(rows)}
            return emit(payload, args.json)
        picked = [row for row in picked if row["category"] == category]
        if not picked and category not in REACHABLE_CATEGORIES[method] and not args.all:
            warnings.append(v("ENUM_INVALID", "methods --category",
                              "「%s」类不在 %s 的默认可达集（源侧工作流未接入该类）；"
                              "加 --all 可见其全部条目" % (category, method)))
    if args.random is not None:
        if not is_int(args.random) or args.random < 1:
            payload["violations"] = [v("ENUM_INVALID", "methods --random",
                                       "抽样条数须为正整数，实为 %s" % args.random)]
            payload["counts"] = {"methods": 0, "library": len(rows)}
            return emit(payload, args.json)
        if args.random > len(picked):
            warnings.append(v("ENUM_INVALID", "methods --random",
                              "请求 %d 条超出结果集 %d 条，按全部返回"
                              % (args.random, len(picked))))
        else:
            picked = random.sample(picked, args.random)
    payload["ok"] = True
    payload["warnings"] = warnings
    payload["methods"] = picked
    payload["counts"] = {"methods": len(picked), "library": len(rows),
                         "branch": len(method_rows),
                         "by_category": count_by(picked, "category")}
    return emit(payload, args.json,
                "PASS：方法库 %d 条；%s 本次返回 %d 条（%s）"
                % (len(rows), method, len(picked), "--all 全分支" if args.all else "默认可达集"),
                ["- [%s] %s：%s" % (row["category"], row["name"], row["description"])
                 for row in picked])


# ---------------------------------------------------------------- init

def next_record_id(records):
    """下一个 `CM-###`：现有最大序号 + 1（三位零填充）。空号不复用、不重号。"""
    max_no = 0
    for rec in records:
        if isinstance(rec, dict) and nonempty(rec.get("id")):
            m = CM_RE.fullmatch(str(rec["id"]).strip())
            if m:
                max_no = max(max_no, int(m.group(1)))
    return "CM-%03d" % (max_no + 1)


def blank_document(project_root, stamp):
    """新建产物骨架：project 三键 + 空集合 + 空 revisions。"""
    name, warning = project_name(project_root)
    doc = {"project": {"name": name, "created": stamp, "updated": stamp},
           "sessions": [], "revisions": []}
    return doc, ([warning] if warning else [])


def new_record(record_id, method, topic, stamp):
    """记录骨架：内容型字段全给空位（`deliverable` / `open_questions` 由会话逐步编辑）。"""
    return {"id": record_id, "method": method, "topic": topic, "date": stamp,
            "status": "草稿", "current_step": 1, "deliverable": {}, "open_questions": []}


def cmd_init(args):
    payload = receipt_base("init", args, args.output_dir)
    out = os.path.abspath(args.output_dir)
    root = os.path.abspath(args.project_root)
    path = os.path.join(out, CIS_FILE)
    show = display_path(path, root)
    method = str(args.method).strip()
    topic = str(args.topic).strip()
    violations = []
    if method not in METHOD_ENUM:
        violations.append(v("ENUM_INVALID", "init --method",
                            "method 越界：%s（合法集 %s）" % (method, "|".join(METHOD_ENUM))))
    if not nonempty(topic):
        violations.append(v("EMPTY_FIELD", "init --topic",
                            "议题为空（门禁：无议题零产出停止，不代拟议题）"))
    if violations:
        payload["violations"] = violations
        return emit(payload, args.json)
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
        warnings = []
        name = project.get("name")
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
    record = new_record(record_id, method, topic, stamp)
    doc["sessions"] = list(doc.get("sessions") or []) + [record]
    try:
        if out:
            os.makedirs(out, exist_ok=True)
        save_yaml_atomic(path, doc)
    except OSError as e:
        payload["violations"] = [v("MISSING_FILE", show, "写盘失败：%s" % e)]
        return emit(payload, args.json)
    payload["ok"] = True
    payload["updated"] = stamp
    payload["id"] = record_id
    payload["counts"] = {"sessions": len(doc["sessions"]), "next_id": record_id}
    return emit(payload, args.json,
                "PASS：已建会话记录 %s（%s / status: 草稿 / current_step: 1），产物共 %d 条记录"
                % (record_id, method, len(doc["sessions"])))


# ---------------------------------------------------------------- check

def check_deliverable(record, where, method, status, step):
    """`deliverable` 面：空态 / 分支必填键（按进度）/ 多余键（warning）。"""
    violations = []
    warnings = []
    deliverable = record.get("deliverable")
    if deliverable is None:
        deliverable = {}
    if not isinstance(deliverable, dict):
        return [v("EMPTY_FIELD", where + ".deliverable", "deliverable 不是映射")], warnings
    draft = str(status) == "草稿"
    if not deliverable and not draft:
        violations.append(v("EMPTY_FIELD", where + ".deliverable",
                            "deliverable 为空而 status: %s（草稿以外的记录须有内容键）" % status))
    if method not in STEP_KEYS:
        return violations, warnings
    if not draft:
        for index, key in enumerate(STEP_KEYS[method]):
            if index + 1 > (step if is_int(step) else 0):
                break
            if not nonempty(deliverable.get(key)):
                violations.append(v("EMPTY_FIELD", "%s.deliverable.%s" % (where, key),
                                    "缺 %s 第 %d 步的必填键（该步 <template-output> 首键）"
                                    % (method, index + 1)))
    for key in deliverable:
        if key in INJECTION_KEYS:
            # 注入项由模板首部/运行环境注入，不是任何 step 的产出（叙事分支的 agent_role /
            # agent_name 是 agent 线残留，diy 侧整裁）——落进 deliverable 即无源字段。
            warnings.append(v("ENUM_INVALID", "%s.deliverable.%s" % (where, key),
                              "%s 是注入项（非步骤产出，源侧由模板首部/运行环境注入），"
                              "不得写进 deliverable" % key))
        elif key not in BRANCH_KEYS[method]:
            warnings.append(v("ENUM_INVALID", "%s.deliverable.%s" % (where, key),
                              "不在 %s 分支的模板键表内（源侧键表为建议结构，非封闭集；"
                              "放行但请确认不是串分支）" % method))
    return violations, warnings


def check_record(index, record, final, show):
    """单条记录的 schema / 枚举 / 同档 / 键表 / 令牌检查。"""
    violations = []
    warnings = []
    where = "%s.sessions[%d]" % (show, index)
    if not isinstance(record, dict):
        return [v("EMPTY_FIELD", where, "记录不是映射")], warnings

    rid = record.get("id")
    if not nonempty(rid):
        violations.append(v("EMPTY_FIELD", where + ".id", "id 缺失"))
    elif not CM_RE.fullmatch(str(rid).strip()):
        violations.append(v("ENUM_INVALID", where + ".id",
                            "id 须为 CM-###（三位零填充），实为 %s" % rid))

    topic = record.get("topic")
    if not nonempty(topic):
        violations.append(v("EMPTY_FIELD", where + ".topic", "topic 为空（会话门禁要求议题在场）"))

    date = record.get("date")
    if not nonempty(date):
        violations.append(v("EMPTY_FIELD", where + ".date", "date 缺失"))
    elif not DATE_RE.fullmatch(str(date).strip()):
        violations.append(v("ENUM_INVALID", where + ".date",
                            "date 须为 YYYY-MM-DD，实为 %s" % date))

    method = record.get("method")
    method_ok = False
    if not nonempty(method):
        violations.append(v("EMPTY_FIELD", where + ".method", "method 缺失"))
    elif str(method).strip() not in METHOD_ENUM:
        violations.append(v("ENUM_INVALID", where + ".method",
                            "method 越界：%s（合法集 %s）" % (method, "|".join(METHOD_ENUM))))
    else:
        method = str(method).strip()
        method_ok = True

    status = record.get("status")
    status_ok = False
    if not nonempty(status):
        violations.append(v("EMPTY_FIELD", where + ".status", "status 缺失"))
    elif str(status).strip() not in STATUS_ENUM:
        violations.append(v("ENUM_INVALID", where + ".status",
                            "status 越界：%s（合法集 %s）"
                            % (status, "|".join(STATUS_ENUM))))
    else:
        status = str(status).strip()
        status_ok = True

    step = record.get("current_step")
    step_max = BRANCH_STEPS[method] if method_ok else max(BRANCH_STEPS.values())
    step_ok = False
    if not is_int(step):
        violations.append(v("ENUM_INVALID", where + ".current_step",
                            "current_step 须为整数，实为 %r" % (step,)))
    elif not (1 <= step <= step_max):
        violations.append(v("ENUM_INVALID", where + ".current_step",
                            "current_step 越界：%s（%s 合法集 1-%d）"
                            % (step, method if method_ok else "四分支并集", step_max)))
    else:
        step_ok = True

    if status_ok and step_ok and method_ok:
        if status == "草稿":
            legal = (1,)
        elif status == "进行中":
            legal = tuple(range(2, step_max))
        else:
            legal = COMPLETED_STEPS[method]
        if step not in legal:
            note = "（问题求解第 9 步源侧 optional，跳过时第 8 步收尾）" if method == "问题求解" else ""
            violations.append(v("STATUS_MISMATCH", where + ".current_step",
                                "status: %s 要求 current_step ∈ %s，实为 %s%s（续接锚点必须"
                                "与会话阶段同档）"
                                % (status, "|".join(str(x) for x in legal), step, note)))

    deliverable_violations, deliverable_warnings = check_deliverable(
        record, where, method if method_ok else "", status, step)
    violations += deliverable_violations
    warnings += deliverable_warnings

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

    violations += check_tokens(record, where)

    if final:
        if str(status) != "已完成":
            violations.append(v("STATUS_MISMATCH", where + ".status",
                                "--final 要求 status: 已完成，实为 %s（先走完本分支的步骤序列）"
                                % status))
        if any(ASSUMPTION_MARK in text for text in collect_strings(record)):
            violations.append(v("ASSUMPTION_PRESENT", where,
                                "--final 要求零 [假设]；未决项写进 open_questions 再定稿"))
    return violations, warnings


def cmd_check(args):
    payload = receipt_base("check", args, args.output_dir)
    out, missing = out_dir_or_violation(payload, args, "check")
    if missing is not None:
        payload["violations"] = [missing]
        return emit(payload, args.json)
    root = os.path.abspath(args.project_root)
    path = os.path.join(out, CIS_FILE)
    show = display_path(path, root)
    violations = []
    warnings = []
    records = []
    data, err = load_yaml_safe(path)
    if data is None and err is None:
        violations.append(v("MISSING_FILE", show,
                            "%s 不存在（先跑 init 建会话记录）" % CIS_FILE))
    elif err is not None:
        violations.append(v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err))
    elif not isinstance(data, dict):
        violations.append(v("EMPTY_FIELD", show, "顶层不是映射（须为 project + sessions）"))
    else:
        project = data.get("project")
        if project is not None and not isinstance(project, dict):
            violations.append(v("EMPTY_FIELD", show + " project", "project 不是映射"))
        for key in ("name", "created", "updated"):
            if isinstance(project, dict) and not nonempty(project.get(key)):
                violations.append(v("EMPTY_FIELD", "%s.project.%s" % (show, key), "%s 为空" % key))
        revisions = data.get("revisions")
        if revisions is None:
            violations.append(v("EMPTY_FIELD", show + " revisions",
                                "revisions 缺失（无修订写空列表）"))
        elif not isinstance(revisions, list):
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
                                            "记录 ID %s 重复（CM ID 稳定不重用）" % rid))
                    seen.add(rid)
            target = str(args.id).strip() if nonempty(args.id) else None
            if target is not None and target not in seen:
                violations.append(v("UNKNOWN_ID", "check --id",
                                    "%s 不在 %s 的 sessions[] 内" % (target, show)))
            for i, record in enumerate(records):
                if target is not None and (not isinstance(record, dict)
                                           or str(record.get("id") or "").strip() != target):
                    continue
                record_violations, record_warnings = check_record(i, record, args.final, show)
                violations += record_violations
                warnings += record_warnings
            if args.final and not records:
                violations.append(v("EMPTY_FIELD", show + " sessions",
                                    "--final 要求至少 1 条会话记录（空集合不得冒充全部定稿）"))
    payload["ok"] = not violations
    payload["violations"] = violations
    payload["warnings"] = warnings
    payload["final"] = bool(args.final)
    payload["counts"] = {"sessions": len(records),
                         "by_method": count_by([r for r in records if isinstance(r, dict)
                                                and nonempty(r.get("method"))], "method"),
                         "by_status": count_by([r for r in records if isinstance(r, dict)
                                                and nonempty(r.get("status"))], "status")}
    return emit(payload, args.json,
                "PASS：%s 校验通过（sessions=%d；%s 必填键表 %d 键）"
                % (show, len(records), "四分支", sum(len(k) for k in STEP_KEYS.values())))


# ---------------------------------------------------------------- CLI

def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(
        description="diy-cis-method 确定性引擎：会话列举（list）/ 单条详情（show）/ 方法库加载"
                    "（methods）/ 记录骨架（init）/ cis-method.yaml 校验（check）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(parser, output_required=False):
        parser.add_argument("--project-root", default=".",
                            help="项目根（默认 .）")
        parser.add_argument("--output-dir", required=output_required, default=None,
                            help="产物目录（写盘子命令必填；只读子命令可省，取值由 "
                                 "`diyc.py resolve` 回执给）")
        parser.add_argument("--json", action="store_true", help="输出单行 JSON 回执")

    ls = sub.add_parser("list", help="列会话记录（只回 id/method/topic/date/status/current_step）")
    common(ls)
    ls.add_argument("--method", default=None, help="按分支过滤（四条分支之一）")
    ls.set_defaults(func=cmd_list)

    sh = sub.add_parser("show", help="单条记录全文（--id CM-###）")
    common(sh)
    sh.add_argument("--id", required=True, help="记录 ID（CM-###）")
    sh.set_defaults(func=cmd_show)

    mt = sub.add_parser("methods", help="方法库加载：默认分支可达集 / --all / --category C "
                                        "/ --random N")
    common(mt)
    mt.add_argument("--method", default=None, help="分支（必填：创新策略|问题求解|设计思维|叙事）")
    mt.add_argument("--category", default=None, help="按类过滤（类名取库内冻结中文类名）")
    group = mt.add_mutually_exclusive_group()
    group.add_argument("--all", action="store_true",
                       help="该分支全部条目（不跨分支；含源侧未接入工作流的条目）")
    group.add_argument("--random", type=int, default=None, help="从默认结果集随机抽 N 条")
    mt.set_defaults(func=cmd_methods)

    ini = sub.add_parser("init", help="建会话记录骨架（铸 CM-###，status: 草稿 + current_step: 1）")
    common(ini, output_required=True)
    ini.add_argument("--method", required=True,
                     help="分支（必填：创新策略|问题求解|设计思维|叙事）")
    ini.add_argument("--topic", required=True, help="议题（门禁：由会话询问收集，不代拟）")
    ini.set_defaults(func=cmd_init)

    ck = sub.add_parser("check", help="校验 cis-method.yaml（schema/枚举/键表/令牌；"
                                      "--final 附加定稿义务）")
    common(ck)
    ck.add_argument("--final", action="store_true",
                    help="定稿校验：status: 已完成 + 分支必填键齐全 + 零 [假设]")
    ck.add_argument("--id", default=None, help="只校验指定记录（CM-###）")
    ck.set_defaults(func=cmd_check)

    args = ap.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
