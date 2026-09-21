# -*- coding: utf-8 -*-
"""diy-wds-brief 确定性引擎：产物列举（list）/ 整份详情（show）/ 顶层骨架铸造（init）
/ wds-brief.yaml 校验（check [--final]）。

机制：本技能是 **WDS 线的入口**（三源合一：wds-0-project-setup 分诊 + wds-0-alignment-signoff
对齐签核 + wds-1-project-brief 战略简报）。产物 `{output_dir}/wds-brief.yaml` 是**单记录、
多段**的内容型产物——各段由会话（LLM）逐步编辑写回，本引擎只做确定性的两件事：**铸造顶层
骨架**与**机械校验**。分工写死（任务书 §2.2）：`project.name` / `created` 与 `intake` 的分诊
结论由 `init` 铸造后不再由 LLM 改；四个子命令里**只有 `init` 写盘**，`check` 只校验不写。

单记录形态的两个直接后果（承任务书 §0.2 裁定 2 / §2.2 注）：
① **无记录级 ID**（不是 B6 那种「一个文件装 N 条记录」的集合）→ 母本 §8 的两值口径
   **直接适用**：顶层 `project.status: 草稿|已定稿`，零偏离；取数工具里的「ID 铸号递增」
   用例对本技能**不适用**，代之以「重复 `init` 不覆盖已有骨架」。
② `list` 至多回一条；`show` 不带 `--id`（无记录级 ID 可寻址），整份全文返回。

  list    列本产物摘要——只回 `name` / `status` / `stage` / `project_type` / `updated`
          五字段（续接锚点是 `stage`）。产物缺席是新项目常态 → 空列表 + `ok: true`，
          不报错；产物损坏 → 结构化违规。`--status S` 按 `S` 过滤顶层 `project.status`。

  show    整份全文返回（`document` 键）。产物缺席 → `MISSING_FILE`。

  init    铸顶层骨架（`--project-type` 必填）：`project.status: 草稿` + `intake` 分诊结论 +
          `client_profile` 四域空位 + `brief` 四段空位 + `alignment` / `signoff` 段骨架 +
          `revisions: []`。**已有合法产物 → 不覆盖**（只刷 `project.updated` + warning）；
          `--project-type` 与产物不符 → `SET_MISMATCH` 且**零写入**（分诊结论是整条 WDS 链
          路由的根，不得被静默改写；要改走 `revisions`）；产物损坏 → `UNPARSABLE_YAML`
          拒绝且零写入，绝不覆盖。

  check   schema / 枚举 / 必填键（下表）/ `status` 与 `stage` 同档 / 对齐十节 / 签核三型
          分列 / 未解析 `{...}` 令牌。`--final` 附加：`project.status: 已定稿` +
          `intake.stage: 收尾` + 简报四段按档位齐备 + 零 `[假设]`。exit 0 唯一放行。

必填键表（`check --final`，`brief_level: complete` 档；`simplified` 档各段收窄为括号内一组）：
- `project`: name / created / updated / status
- `intake`: project_type / complexity / brief_level / strategic_analysis / stage
- `client_profile` 四域: organization / key_people / internal_drivers / collaboration
- `brief.core` 9 键: vision / positioning / business_model / **business_customers（仅
  business_model 含 `B2B` 时）** / target_users / product_concept / success_metrics /
  competitive_landscape / constraints（简化档：vision / target_users / constraints）
- `brief.content.content_language` 5 键: personality / tone / languages / seo_keywords /
  content_structure（简化档：languages）
- `brief.visual.visual_direction` 6 键: inspiration / existing_brand / references /
  design_style / layout_effects / imagery（简化档：design_style）
- `brief.platform.platform_requirements` 4 键: tech_stack / integrations /
  contact_strategy / multilingual（简化档：tech_stack）
- `alignment`（`status ≠ 不需要` 时）十节: realization / why_it_matters /
  how_we_see_it_working / paths_we_explored / recommended_solution / path_forward /
  value_we_create / cost_of_inaction / our_commitment / summary
- `signoff`（`type ≠ 不签核` 时）分型齐备：对外合同 11 节（**其中 `availability` 是条件
  节**——仅 `pricing_model: 长期聘用` 时必填，其余模式接受缺省）/ 服务协议 12 节 / 内部审批
  7 节（三张节表与条件节表见下方常量）
- `revisions`: 列表（无修订写空列表）

跨技能读契约（任务书 §2.3.1 冻结，**本技能是链的起点**）：下游 `diy-wds-trigger` 读
`brief.core`（vision / positioning / target_users / product_concept）· `brief.content.
content_language` · `brief.visual.visual_direction`（6 维）· `brief.platform.
platform_requirements`，门禁 = 本产物的 `project.status: 已定稿`。**这四组键名是三方唯一
契约**，本引擎的必填键表与之一一对应——改键名必须同步 W2/W3。

违规码：复用 batch3-contract §3 冻结集——本引擎用到 `MISSING_FILE` / `UNPARSABLE_YAML` /
`EMPTY_FIELD` / `ENUM_INVALID` / `STATUS_MISMATCH` / `ASSUMPTION_PRESENT` / `SET_MISMATCH`
共 7 个；**`TOKEN_UNRESOLVED` 沿用 B6 的已批新增码与判定流程**（本批**不新增任何码**）。
两处语义复用在此登记：① `SET_MISMATCH` 承载「`init` 的 `--project-type` 与既有产物不符」
（最近义项是「集合/取值不匹配」，与 `bmb_module` 的同码用途同族）；② `ENUM_INVALID` 兼作
`list --status` 非法取值码（同族先例同款用法）。

`--previous` 判 **no**（裁定 18）：本产物是**单记录多段**，段只增不减（重跑即就地补段，
不收缩集合）——不存在「旧有新无」的 ID 集合可比对；改既有段往 `revisions` 追加。

契约（承 batch3-contract §3 / 任务书 §2.2）：exit 0 唯一放行 / 1 = 违规或被拒绝 /
2 = 用法错误（argparse 默认）/ 本批无 exit 3；`--json` → 单行回执（`ensure_ascii=False`），
无 `--json` → 中文人读行（每违规一行 `CODE where: msg` + 汇总行）；回执共同键
`{ok, command, project_root, output_dir, instance, violations, warnings, counts}`
（`instance` 恒 `null` 但**键在位**，`warnings` 与 `violations` 同形），`where` 正斜杠、
相对 project-root；**写盘命令（`init`）回执另含 `updated`**，只读子命令不含。
`--project-root`（默认 `.`）全部子命令都收；`--output-dir` **写盘子命令必填**（不设默认、
**不得**私读 `diy-coder.yaml` 当默认），只读子命令可省（省了则回执为 `null`，需读产物的
子命令明确报缺而不静默按空处理）。**`--instance` 一律不做**（裁定 9）：实例由 SKILL.md
委托 `diyc.py resolve` 解析后以 `--output-dir` 形式传入，签名表内不出现它。
写回纪律：全文 load → 就地改 → `yaml.safe_dump(allow_unicode=True, sort_keys=False,
default_flow_style=False)` → 同目录临时文件 + `os.replace`（注释不保留；复用
`diyc_lib.save_yaml_atomic` 的同款实现——不另造一份语义不同的）。

★ **红线**：本技能的终门是**本引擎的 `check --final`**。**不得**教模型调用
`diyc.py check --type <WDS 型> --previous`——`diyc.py` 的 `CHECK_TYPES` 是 8 型封闭集，
WDS 型不在其中（`test_suite_texts.py` 有守卫会直接判红）。
"""
# trace: 迁移计划 §二 验收 #1（薄主文件 + 厚 steps）/#2（产物 schema + 单记录无 ID）
#        /#3（前置门禁：入口技能 = 分诊完成）/#6（viewer 标签缺口登记）
#        /#8（frontmatter 六字段）/#12（领域引擎接线：b 终门 / c --previous 判 no / e 写权边界）
import argparse
import io
import json
import os
import re
import sys

import yaml

BRIEF_FILE = "wds-brief.yaml"

# 分诊与推进（`intake` 五键；前四键是分诊结论，`stage` 是续接锚点）
PROJECT_TYPE_ENUM = ("greenfield", "brownfield")
COMPLEXITY_ENUM = ("simple", "standard", "complex", "complex+mobile")
BRIEF_LEVEL_ENUM = ("complete", "simplified")
STRATEGIC_ENUM = ("full", "simplified", "skip")
STAGE_ENUM = ("分诊", "对齐", "签核", "核心", "内容", "视觉", "收尾")
INTAKE_KEYS = ("project_type", "complexity", "brief_level", "strategic_analysis", "stage")

# 母本 §8 两值口径：单记录产物 → 顶层 `project.status`（裁定 2，零偏离）
STATUS_ENUM = ("草稿", "已定稿")
FINAL_STAGE = STAGE_ENUM[-1]            # 已定稿 ⟺ stage: 收尾（反向不成立，见 check_document）

# 签核段（裁定 13：三型并列，全留）
SIGNOFF_TYPE_ENUM = ("不签核", "对外合同", "服务协议", "内部审批")
SIGNOFF_STATUS_ENUM = ("未开始", "构建中", "已定稿")
RETAINER_MODEL = "长期聘用"             # 唯一触发合同 `availability` 条件必填的定价模式
PRICING_ENUM = ("固定价", "计时", RETAINER_MODEL, "混合")
BRANCH_OF_TYPE = {"对外合同": "external_contract", "服务协议": "service_agreement",
                  "内部审批": "internal"}

# 对齐段（源 10 节；`status: 不需要` 时十节全免）
ALIGNMENT_STATUS_ENUM = ("不需要", "未开始", "进行中", "已定稿")
ALIGNMENT_SECTIONS = ("realization", "why_it_matters", "how_we_see_it_working",
                      "paths_we_explored", "recommended_solution", "path_forward",
                      "value_we_create", "cost_of_inaction", "our_commitment", "summary")

# 客户画像四域（census-1 真能力 F；源模板把「决策文化/协作风格」并进 collaboration）
CLIENT_PROFILE_KEYS = ("organization", "key_people", "internal_drivers", "collaboration")

# 简报四段（§2.3）：本四段的键名同时是**跨技能读契约**（§2.3.1，三方逐键核对）
BRIEF_KEYS = ("core", "content", "visual", "platform")

CORE_REQUIRED = ("vision", "positioning", "business_model", "target_users",
                 "product_concept", "success_metrics", "competitive_landscape",
                 "constraints")
CORE_B2B_KEY = "business_customers"     # 仅 `business_model` 含 `B2B` 时必填（源 step-06 条件性）
CORE_SIMPLIFIED = ("vision", "target_users", "constraints")

CONTENT_KEYS = ("content_language",)    # 下游读键（§2.3.1，冻结）
CONTENT_LANGUAGE_KEYS = ("personality", "tone", "languages", "seo_keywords",
                         "content_structure")
CONTENT_LANGUAGE_SIMPLIFIED = ("languages",)

VISUAL_KEYS = ("visual_direction",)     # 下游读键（§2.3.1，冻结）
VISUAL_DIRECTION_KEYS = ("inspiration", "existing_brand", "references", "design_style",
                         "layout_effects", "imagery")   # 六维（源 19/21/22/23/24/25）
VISUAL_DIRECTION_SIMPLIFIED = ("design_style",)

PLATFORM_KEYS = ("platform_requirements",)              # 下游读键（§2.3.1，冻结）
PLATFORM_REQUIREMENTS_KEYS = ("tech_stack", "integrations", "contact_strategy",
                             "multilingual")
PLATFORM_REQUIREMENTS_SIMPLIFIED = ("tech_stack",)

# 签核三型节表（源侧实值；三张表合计 30 节）
# 对外合同 11 节 = `wds-0-alignment-signoff/workflow.md:98-111` 的 05a-05k 正文节
# （`availability` 源 05f 写的节在合同模板中**不存在**——本批补齐并登记为源侧缺陷修复；
#  其中 `availability` 是条件节，见下方 `CONTRACT_CONDITIONAL`）
CONTRACT_SECTIONS = ("project_overview", "business_model", "scope_of_work", "payment_terms",
                     "timeline", "availability", "confidentiality", "not_to_exceed",
                     "work_initiation", "terms_and_conditions", "approval")
# 服务协议 12 节 = `templates/service-agreement.template.md` 的节（源侧**无构建步**，
# 05* 只按合同模板建节、`service-agreement.md` 仅在 05l 收尾处被提及——本批补齐构建步）
SERVICE_SECTIONS = ("project_overview", "scope_of_services", "our_commitment", "timeline",
                    "why_it_matters", "expected_outcomes", "service_terms",
                    "risks_and_considerations", "confidentiality", "not_to_exceed",
                    "terms_and_conditions", "approval")
# 内部审批 7 节 = `steps-c/step-06a-build-internal-signoff.md:68-104` 的 Section 1-7
# （源侧把「风险/保密/路径」并成第 7 节 Optional Sections）
INTERNAL_SECTIONS = ("project_overview", "goals_and_metrics", "budget_and_resources",
                     "ownership", "approval_and_signoff", "timeline_and_milestones",
                     "optional_sections")
# 合同**条件节**表：节 → 触发它必填的定价模式。源 05f 的 `Step-Specific Rules` 原文
# 「Only applies to retainer model - skip for other models」——故 `availability` 只在
# `pricing_model: 长期聘用` 时计入必填集，其余模式接受缺省（键在场则照常校验）。
# 本表与 `steps/03-signoff.md` 第 3 步第 6 行的「条件节：仅 `pricing_model: 长期聘用` 时
# 必填——其余模式整节可缺省」逐字一致（V-01 修复）。
CONTRACT_CONDITIONAL = {"availability": RETAINER_MODEL}

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


def require(node, keys, where, out, missing_ok=True):
    """必填键非空检查。node 不是映射时只报一条。"""
    if not isinstance(node, dict):
        if missing_ok:
            out.append(v("EMPTY_FIELD", where, "须为映射（键表 %s）" % " / ".join(keys)))
        return
    for key in keys:
        if not nonempty(node.get(key)):
            out.append(v("EMPTY_FIELD", "%s.%s" % (where, key), "必填键 %s 为空" % key))


def enum_check(value, allowed, where, label, out, warnings=None, soft=False):
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
                   "引擎不设默认、不私读 diy-coder.yaml）" % (command, BRIEF_FILE))


def read_document(path, show):
    """读产物 → (data | None, err)。None + err None = 缺席。"""
    data, err = load_yaml_safe(path)
    if data is not None and not isinstance(data, dict):
        return None, "顶层不是映射（须为 project + intake + client_profile + brief）"
    return data, err


def brief_summary(data):
    """`list` 只回五字段（不读正文）。"""
    project = data.get("project") if isinstance(data.get("project"), dict) else {}
    intake = data.get("intake") if isinstance(data.get("intake"), dict) else {}
    return {"name": project.get("name"), "status": project.get("status"),
            "stage": intake.get("stage"), "project_type": intake.get("project_type"),
            "updated": project.get("updated")}


# ---------------------------------------------------------------- list / show

def cmd_list(args):
    payload = receipt_base("list", args, args.output_dir)
    out, missing = out_dir_or_violation(args, "list")
    if missing is not None:
        payload["violations"] = [missing]
        return emit(payload, args.json)
    root = os.path.abspath(args.project_root)
    path = os.path.join(out, BRIEF_FILE)
    show = display_path(path, root)
    status = str(args.status).strip() if nonempty(args.status) else None
    violations = []
    if status is not None and status not in STATUS_ENUM:
        violations.append(v("ENUM_INVALID", "list --status",
                            "status 越界：%s（合法集 %s）" % (status, "|".join(STATUS_ENUM))))
    data, err = read_document(path, show)
    warnings = []
    if err is not None:
        violations.append(v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err))
    elif data is None:
        warnings.append(v("MISSING_FILE", show,
                          "%s 尚未建立（先跑 init 铸骨架）——按空列表处理" % BRIEF_FILE))
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
    body = ["- %s ｜ %s ｜ %s ｜ %s ｜ %s"
            % (r["name"], r["status"], r["stage"], r["project_type"], r["updated"])
            for r in records]
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
    path = os.path.join(out, BRIEF_FILE)
    show = display_path(path, root)
    data, err = read_document(path, show)
    violations = []
    if err is not None:
        violations.append(v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err))
    elif data is None:
        violations.append(v("MISSING_FILE", show, "产物不存在（先跑 init 铸骨架）"))
    payload["violations"] = violations
    payload["ok"] = not violations
    payload["document"] = data if not violations else None
    payload["counts"] = {"records": 1 if not violations else 0}
    summary = None
    if not violations:
        item = brief_summary(data)
        summary = "PASS：%s（%s / stage: %s / %s）" % (show, item["status"], item["stage"],
                                                     item["project_type"])
    return emit(payload, args.json, summary)


# ---------------------------------------------------------------- init

def blank_document(project_root, stamp, project_type, complexity, brief_level, strategic):
    """新建产物骨架：分诊结论 + 各段空位（内容型字段由会话逐步编辑）。"""
    name, warning = project_name(project_root)
    doc = {
        "project": {"name": name, "created": stamp, "updated": stamp,
                    "status": STATUS_ENUM[0]},
        "intake": {"project_type": project_type, "complexity": complexity,
                   "brief_level": brief_level, "strategic_analysis": strategic,
                   "stage": STAGE_ENUM[0]},
        "client_profile": {key: {} for key in CLIENT_PROFILE_KEYS},
        "brief": {key: {} for key in BRIEF_KEYS},
        "alignment": {"status": "未开始"},
        "signoff": {"type": SIGNOFF_TYPE_ENUM[0], "status": SIGNOFF_STATUS_ENUM[0],
                    "external_contract": {}, "service_agreement": {}, "internal": {}},
        "revisions": [],
    }
    return doc, ([warning] if warning else [])


def cmd_init(args):
    payload = receipt_base("init", args, args.output_dir)
    out = os.path.abspath(args.output_dir)
    root = os.path.abspath(args.project_root)
    path = os.path.join(out, BRIEF_FILE)
    show = display_path(path, root)
    violations = []
    project_type = str(args.project_type).strip() if args.project_type is not None else ""
    if not nonempty(project_type):
        violations.append(v("EMPTY_FIELD", "init --project-type",
                            "分诊未完成：项目类型为空（入口技能的门禁 = 分诊问答完成；"
                            "拒答则零产出停止，不代拟）"))
    else:
        enum_check(project_type, PROJECT_TYPE_ENUM, "init --project-type",
                   "project_type", violations)
    for value, allowed, flag, label in (
            (args.complexity, COMPLEXITY_ENUM, "init --complexity", "complexity"),
            (args.brief_level, BRIEF_LEVEL_ENUM, "init --brief-level", "brief_level"),
            (args.strategic_analysis, STRATEGIC_ENUM, "init --strategic-analysis",
             "strategic_analysis")):
        if value is not None and nonempty(value):
            enum_check(value, allowed, flag, label, violations)
    if violations:
        payload["violations"] = violations
        return emit(payload, args.json)
    stamp = today()
    data, err = read_document(path, show)
    if err is not None:
        payload["violations"] = [v("UNPARSABLE_YAML", show,
                                   "%s（拒绝且零写入——修好或另行归档后再 init）" % err)]
        return emit(payload, args.json)
    if data is None:
        doc, warnings = blank_document(
            root, stamp, project_type,
            str(args.complexity).strip() if nonempty(args.complexity) else COMPLEXITY_ENUM[1],
            str(args.brief_level).strip() if nonempty(args.brief_level) else BRIEF_LEVEL_ENUM[0],
            str(args.strategic_analysis).strip() if nonempty(args.strategic_analysis)
            else STRATEGIC_ENUM[0])
        payload["warnings"] = warnings
    else:
        # 已有骨架：**不覆盖**。分诊结论是整条 WDS 链路由的根——改判走 revisions + 重跑。
        stored = data.get("intake") if isinstance(data.get("intake"), dict) else {}
        existing = str(stored.get("project_type") or "").strip()
        if nonempty(existing) and existing != project_type:
            payload["violations"] = [v("SET_MISMATCH", "%s.intake.project_type" % show,
                                       "既有产物记录的是 %s，--project-type 给的是 %s——"
                                       "不覆盖（分诊结论决定整链路由；要改走 revisions 并经"
                                       "用户确认后再手工改，不改判则按既有值继续）"
                                       % (existing, project_type))]
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
                          "updated": stamp,
                          "status": project.get("status") if nonempty(project.get("status"))
                          else STATUS_ENUM[0]}
        doc.setdefault("intake", {"project_type": project_type})
        doc.setdefault("client_profile", {key: {} for key in CLIENT_PROFILE_KEYS})
        doc.setdefault("brief", {key: {} for key in BRIEF_KEYS})
        doc.setdefault("alignment", {"status": "未开始"})
        doc.setdefault("signoff", {"type": SIGNOFF_TYPE_ENUM[0],
                                   "status": SIGNOFF_STATUS_ENUM[0],
                                   "external_contract": {}, "service_agreement": {},
                                   "internal": {}})
        doc.setdefault("revisions", [])
        warnings.append(v("SET_MISMATCH", show,
                          "产物已存在骨架——本次 init 未覆盖任何内容，只刷 project.updated；"
                          "续接请按 intake.stage 定位"))
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
    payload["counts"] = {"records": 1, "stage": doc["intake"].get("stage")}
    return emit(payload, args.json,
                "PASS：已建 %s 骨架（%s / status: 草稿 / stage: 分诊）"
                % (show, project_type))


# ---------------------------------------------------------------- check

def check_signoff(signoff, where, final, out):
    """签核段（裁定 13）：type 枚举 + 分型齐备（三型节表）。"""
    if not isinstance(signoff, dict):
        out.append(v("EMPTY_FIELD", where, "signoff 不是映射（三型并列：external_contract / "
                                           "service_agreement / internal）"))
        return
    stype = enum_check(signoff.get("type"), SIGNOFF_TYPE_ENUM, where + ".type",
                       "signoff.type", out)
    enum_check(signoff.get("status"), SIGNOFF_STATUS_ENUM, where + ".status",
               "signoff.status", out)
    for key in ("external_contract", "service_agreement", "internal"):
        if key in signoff and not isinstance(signoff.get(key), dict):
            out.append(v("EMPTY_FIELD", "%s.%s" % (where, key), "须为映射（三型并列）"))
    if stype in (None, SIGNOFF_TYPE_ENUM[0]):
        return
    branch = BRANCH_OF_TYPE.get(stype)
    payload = signoff.get(branch)
    if not isinstance(payload, dict):
        payload = {}
    if not payload:
        out.append(v("EMPTY_FIELD", "%s.%s" % (where, branch),
                     "signoff.type: %s 要求 %s 段齐备（分型与已填段必须一致）"
                     % (stype, branch)))
        return
    sections = {t: s for t, s in ((SIGNOFF_TYPE_ENUM[1], CONTRACT_SECTIONS),
                                  (SIGNOFF_TYPE_ENUM[2], SERVICE_SECTIONS),
                                  (SIGNOFF_TYPE_ENUM[3], INTERNAL_SECTIONS))}[stype]
    if branch != "internal":
        enum_check(payload.get("pricing_model"), PRICING_ENUM,
                   "%s.%s.pricing_model" % (where, branch), "pricing_model", out)
    if not final:
        return
    if payload.get("finalized") is not True:
        out.append(v("STATUS_MISMATCH", "%s.%s.finalized" % (where, branch),
                     "--final 要求该型已定稿（finalized: true）"))
    body = payload.get("sections")
    if not isinstance(body, dict):
        out.append(v("EMPTY_FIELD", "%s.%s.sections" % (where, branch),
                     "sections 须为映射（%s 共 %d 节）" % (stype, len(sections))))
        return
    # 条件节（源 05f）：「长期聘用才谈可用性」——非该模式时 `availability` 不入必填集，
    # 但**键在场则照常校验**（留空仍报 EMPTY_FIELD）。其余模式与其余 10 节不变。
    required = sections
    if stype == SIGNOFF_TYPE_ENUM[1]:
        mode = str(payload.get("pricing_model") or "").strip()
        for key, trigger in CONTRACT_CONDITIONAL.items():
            if mode != trigger and key not in body:
                required = tuple(item for item in required if item != key)
    require(body, required, "%s.%s.sections" % (where, branch), out)


def check_alignment(alignment, where, final, out):
    """对齐段：四态枚举 + 十节（`status: 不需要` 时全免）。"""
    if not isinstance(alignment, dict):
        out.append(v("EMPTY_FIELD", where, "alignment 不是映射"))
        return
    status = enum_check(alignment.get("status"), ALIGNMENT_STATUS_ENUM, where + ".status",
                        "alignment.status", out)
    if status in (None, "不需要"):
        return
    if final and status != "已定稿":
        out.append(v("STATUS_MISMATCH", where + ".status",
                     "--final 要求 alignment.status ∈ {不需要, 已定稿}，实为 %s"
                     "（走了一半的对齐要么补完，要么经用户确认改判为「不需要」）" % status))
        return
    if final:
        require(alignment, ALIGNMENT_SECTIONS, where, out)


def check_document(data, show, args):
    """全量校验；返回 (violations, warnings, counts)。"""
    violations = []
    warnings = []
    project = data.get("project")
    if not isinstance(project, dict):
        violations.append(v("EMPTY_FIELD", show + " project", "project 不是映射"))
        project = {}
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
                            "status 越界：%s（合法集 %s）"
                            % (status, "|".join(STATUS_ENUM))))
    elif not nonempty(status) and nonempty(project.get("name")):
        violations.append(v("EMPTY_FIELD", show + ".project.status", "status 为空"))

    intake = data.get("intake")
    if not isinstance(intake, dict):
        violations.append(v("EMPTY_FIELD", show + " intake", "intake 不是映射"))
        intake = {}
    for key in INTAKE_KEYS:
        if not nonempty(intake.get(key)):
            violations.append(v("EMPTY_FIELD", "%s.intake.%s" % (show, key), "必填键 %s 为空" % key))
    for key, allowed in (("project_type", PROJECT_TYPE_ENUM), ("complexity", COMPLEXITY_ENUM),
                         ("brief_level", BRIEF_LEVEL_ENUM),
                         ("strategic_analysis", STRATEGIC_ENUM), ("stage", STAGE_ENUM)):
        if nonempty(intake.get(key)):
            enum_check(intake.get(key), allowed, "%s.intake.%s" % (show, key), key, violations)
    stage = str(intake.get("stage") or "").strip()
    # 同档规则：`已定稿` ⟺ `stage: 收尾`；反向不成立——`收尾` 也是 07-finish 进行中的合法中间态
    if status_ok and status == STATUS_ENUM[1] and stage != FINAL_STAGE:
        violations.append(v("STATUS_MISMATCH", "%s.intake.stage" % show,
                            "status: 已定稿 要求 stage: %s，实为 %s"
                            % (FINAL_STAGE, stage or "空")))

    profile = data.get("client_profile")
    if not isinstance(profile, dict):
        profile = {}
    for key in CLIENT_PROFILE_KEYS:
        if key not in profile:
            violations.append(v("EMPTY_FIELD", "%s.client_profile.%s" % (show, key),
                                "客户画像四域缺 %s（organization / key_people / "
                                "internal_drivers / collaboration）" % key))

    brief = data.get("brief")
    if not isinstance(brief, dict):
        violations.append(v("EMPTY_FIELD", show + " brief", "brief 不是映射"))
        brief = {}
    for key in BRIEF_KEYS:
        if key not in brief:
            violations.append(v("EMPTY_FIELD", "%s.brief.%s" % (show, key),
                                "简报四段缺 %s（core / content / visual / platform）" % key))

    level = str(intake.get("brief_level") or "").strip()
    simplified = level == BRIEF_LEVEL_ENUM[1]
    if args.final:
        core = brief.get("core")
        if not isinstance(core, dict):
            violations.append(v("EMPTY_FIELD", show + ".brief.core", "core 不是映射"))
            core = {}
        require(core, CORE_SIMPLIFIED if simplified else CORE_REQUIRED,
                show + ".brief.core", violations)
        business_model = str(core.get("business_model") or "")
        if (not simplified) and "B2B" in business_model and not nonempty(core.get(CORE_B2B_KEY)):
            violations.append(v("EMPTY_FIELD", "%s.brief.core.%s" % (show, CORE_B2B_KEY),
                                "business_model 含 B2B → 必须给 B2B 客户画像"
                                "（源 step-06 条件性步骤）"))
        content = brief.get("content")
        if not isinstance(content, dict):
            content = {}
        language = content.get("content_language")
        if not isinstance(language, dict):
            language = {}
        require(language, CONTENT_LANGUAGE_SIMPLIFIED if simplified
                else CONTENT_LANGUAGE_KEYS, show + ".brief.content.content_language",
                violations)
        visual = brief.get("visual")
        if not isinstance(visual, dict):
            visual = {}
        direction = visual.get("visual_direction")
        if not isinstance(direction, dict):
            direction = {}
        require(direction, VISUAL_DIRECTION_SIMPLIFIED if simplified
                else VISUAL_DIRECTION_KEYS, show + ".brief.visual.visual_direction",
                violations)
        platform = brief.get("platform")
        if not isinstance(platform, dict):
            platform = {}
        requirements = platform.get("platform_requirements")
        if not isinstance(requirements, dict):
            requirements = {}
        require(requirements, PLATFORM_REQUIREMENTS_SIMPLIFIED if simplified
                else PLATFORM_REQUIREMENTS_KEYS,
                show + ".brief.platform.platform_requirements", violations)

    check_alignment(data.get("alignment"), show + ".alignment", args.final, violations)
    check_signoff(data.get("signoff"), show + ".signoff", args.final, violations)

    revisions = data.get("revisions")
    if revisions is None:
        violations.append(v("EMPTY_FIELD", show + " revisions", "revisions 缺失（无修订写空列表）"))
    elif not isinstance(revisions, list):
        violations.append(v("EMPTY_FIELD", show + " revisions", "revisions 不是列表"))

    violations += check_tokens(data, show)

    if args.final:
        if status_ok and status != STATUS_ENUM[1]:
            violations.append(v("STATUS_MISMATCH", show + ".project.status",
                                "--final 要求 status: 已定稿，实为 %s（先走完 wds-brief 的七个"
                                "步骤文件，再按 §2.5 六拍落盘定稿）" % status))
        if any(ASSUMPTION_MARK in text for text in collect_strings(data)):
            violations.append(v("ASSUMPTION_PRESENT", show,
                                "--final 要求零 [假设]；未决项写进 revisions 或就地补问"))
    counts = {"records": 1,
              "by_status": {status: 1} if status_ok else {},
              "by_stage": {stage: 1} if stage else {}}
    return violations, warnings, counts


def cmd_check(args):
    payload = receipt_base("check", args, args.output_dir)
    out, missing = out_dir_or_violation(args, "check")
    if missing is not None:
        payload["violations"] = [missing]
        return emit(payload, args.json)
    root = os.path.abspath(args.project_root)
    path = os.path.join(out, BRIEF_FILE)
    show = display_path(path, root)
    data, err = read_document(path, show)
    if err is not None:
        payload["violations"] = [v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err)]
        return emit(payload, args.json)
    if data is None:
        payload["violations"] = [v("MISSING_FILE", show,
                                   "%s 不存在（先跑 init 铸骨架）" % BRIEF_FILE)]
        return emit(payload, args.json)
    violations, warnings, counts = check_document(data, show, args)
    payload["violations"] = violations
    payload["warnings"] = warnings
    payload["ok"] = not violations
    payload["final"] = bool(args.final)
    payload["counts"] = counts
    return emit(payload, args.json,
                "PASS：%s 校验通过（%s；签核三型节表 11/12/7，简报四段按 %s 档）"
                % (show, "已定稿" if args.final else "草稿可用",
                   "simplified" if str((data.get("intake") or {}).get("brief_level") or "")
                   .strip() == BRIEF_LEVEL_ENUM[1] else "complete"))


# ---------------------------------------------------------------- CLI

def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(
        description="diy-wds-brief 确定性引擎：产物列举（list）/ 整份详情（show）/ "
                    "顶层骨架铸造（init）/ wds-brief.yaml 校验（check）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(parser, output_required=False):
        parser.add_argument("--project-root", default=".",
                            help="项目根（默认 .）")
        parser.add_argument("--output-dir", required=output_required, default=None,
                            help="产物目录（写盘子命令必填；只读子命令可省，取值由 "
                                 "`diyc.py resolve` 回执给）")
        parser.add_argument("--json", action="store_true", help="输出单行 JSON 回执")

    ls = sub.add_parser("list", help="列产物摘要（只回 name/status/stage/project_type/updated）")
    common(ls)
    ls.add_argument("--status", default=None, help="按 project.status 过滤（草稿|已定稿）")
    ls.set_defaults(func=cmd_list)

    sh = sub.add_parser("show", help="整份全文（单记录产物，无记录级 ID）")
    common(sh)
    sh.set_defaults(func=cmd_show)

    ini = sub.add_parser("init", help="铸顶层骨架（--project-type 必填；已有骨架不覆盖）")
    common(ini, output_required=True)
    ini.add_argument("--project-type", required=True,
                     help="分诊结论（必填：greenfield|brownfield；空值 → EMPTY_FIELD 零产出）")
    ini.add_argument("--complexity", default=None,
                     help="产品复杂度（simple|standard|complex|complex+mobile，默认 standard）")
    ini.add_argument("--brief-level", default=None, help="简报档位（complete|simplified）")
    ini.add_argument("--strategic-analysis", default=None,
                     help="战略分析深度（full|simplified|skip）")
    ini.set_defaults(func=cmd_init)

    ck = sub.add_parser("check", help="校验 wds-brief.yaml（schema/枚举/必填键/令牌；"
                                      "--final 附加定稿义务）")
    common(ck)
    ck.add_argument("--final", action="store_true",
                    help="定稿校验：status: 已定稿 + stage: 收尾 + 简报四段齐备 + 零 [假设]")
    ck.set_defaults(func=cmd_check)

    args = ap.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
