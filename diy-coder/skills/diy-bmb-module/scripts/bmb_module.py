# -*- coding: utf-8 -*-
"""diy-bmb-module 确定性引擎：计划骨架铸造（new）+ 批次计划校验（check）。

机制：本技能是**批次规划器（只规划不造）**——把「这批要造哪些技能、各自解决什么、
按什么顺序造」写成 `{output_dir}/module-plan.yaml`（新产物类型，记录 ID 前缀 `MP-###`），
再拿计划的技能清单去核 diy 的真实注册面：每个技能 `SKILL.md` 的 frontmatter 六字段。
引擎只做机械可判的三件事——

  new      铸造一条计划记录：`{output_dir}/module-plan.yaml` 不存在则建
           （`project{name,created,updated}` + `plans: []` + `revisions: []`；project.name
           取自 `{project-root}/diy-coder.yaml` 的 `project.name`，缺配置回退项目目录名）；
           序号规则 = 既有最大号 + 1，三位零填充（MP-001 起），不重编不重用。
           同一 slug 已存在 → DUPLICATE_ID 拒绝并指认既有 MP-xxx（**同 slug 更新走记录
           就地编辑，不新建**——承源侧 anti-zombie 合并思想的记录级形态）。slug 缺失
           （无头常态）→ stderr 一行 `missing_slug` 语义说明 + EMPTY_FIELD 拒绝、零产出。
           骨架里除 id/slug/title/status/date 外全是空值（空串/空列表）——空值即「未写」，
           承源侧「先把骨架灌进文档、把写作纪律写进文档本身」的手法。

  check    校验 `{output_dir}/module-plan.yaml`（**零写面**：不写任何被校验技能的文件，
           frontmatter 亦然；本子命令只读、绝不落盘）。校验面四层：
           ① schema：顶层 project 三键 + plans/revisions 两列表（**顶层不设 status**——多记录
              产物的定稿态挂记录级；命中 → STATUS_MISMATCH）；记录必填 id/slug/title/status/
              date/vision 与集合键；`id` 形态 MP-### 且全局唯一（ENUM_INVALID / DUPLICATE_ID）；
              `status ∈ 草稿|已定稿`、`skills[].kind ∈ 工作流|工具`（ENUM_INVALID）；
              `skills[].name` hyphen-case 且 ≤64 字符（NAME_ILLEGAL）。
           ② 引用闭包三档：`skills[].name` / `depends_on` / `dependencies` / `build_order`
              指向**本记录内**名字 → 通过；指向**已装技能**（查找面命中）→ warning `UNKNOWN_ID`
              （合法的「依赖既有能力」）；两边都不是 → 违规 `UNKNOWN_ID`。
           ③ 注册面（frontmatter 六字段 = phase / precededBy / followedBy / required / line /
              outputs）：查找面 = 权威面 `--skills-root`（缺省 `{project-root}/.claude/skills`，
              安装面）+ 第二面 `{project-root}/diy-coder/skills`（套件源树），**两处都查不到
              才判缺失**（→ warning `MISSING_FILE`，计划先于建造是计划器常态，不阻断）；
              六字段齐备**仅对 `new: true`（本批新建）判**（缺 → 违规 `EMPTY_FIELD`）；
              **存量技能与计划外对端缺字段一律记 warning**（14 个存量技能零字段是既成事实，
              本技能零写面改不了——不得判红）。双向对称**只判「本计划内技能之间」**：
              A.followedBy ∋ B 要求 B.precededBy ∋ A（反之亦然），不对称 → `SET_MISMATCH`；
              两侧任一未声明该字段 → 不判（不判不可读数据）；对端在计划外 → warning。
              链接指向既不在计划内、又未装 → 违规 `UNKNOWN_ID`（补源侧「指向真实能力」等价面）。
           ④ `--previous`（**判 yes**：技能清单收缩 = 计划变更，须机械留痕）：配对键 = 记录
              `slug`（**记录重铸 MP-### 时仍能配对**）；旧稿有而新稿无的技能条目 → `ID_UNSTABLE`，
              除非该条目在新稿里保留并标 `dropped: true`（计划内移除的显式留痕）。旧稿不可读 →
              `MISSING_FILE` 拒绝。
           `--final` 附加义务（作用域随 `--id`，缺省 = 全部记录）：每条被检记录 `status: 已定稿`
           （否则 `STATUS_MISMATCH`）、记录内零 `[假设]` 字面量（`ASSUMPTION_PRESENT`）、
           `skills` 非空（空态 `EMPTY_FIELD`）。**空态**（`plans: []` / `skills: []`）：非 --final
           通过但记 warning `EMPTY_FIELD`；`--final` 一律拒绝。

  路径令牌（承纪律 2）：路径参数里的 `{project-root}` **由引擎按 `--project-root` 自解析**
  （唯一例外）；其余任何 `{...}` 令牌一律拒绝并报 `TOKEN_UNRESOLVED`、零写入。

规则来源：违规码复用 batch3-contract §3 冻结集（MISSING_FILE / UNPARSABLE_YAML /
DUPLICATE_ID / UNKNOWN_ID / ENUM_INVALID / EMPTY_FIELD / ASSUMPTION_PRESENT / STATUS_MISMATCH /
SET_MISMATCH 共 9 个）+ 本批点名的新增码 3 个：**`NAME_ILLEGAL`（技能名非法）/
`ID_UNSTABLE`（技能清单收缩）/ `TOKEN_UNRESOLVED`（未解析路径令牌）**。回执契约对齐既有先例：
exit 0 唯一放行 / --json 单行 JSON（ensure_ascii=False）/ 共同键 {ok, command, project_root,
output_dir, violations[{code,where,msg}], warnings（与 violations 同形，人读态渲染为 WARN）,
counts}；`new` 另含命令级附加键 {plan_id, slug, file, created}；where 一律正斜杠、相对
project-root；人读态每条违规一行 `CODE where: msg` + 末尾汇总行。

分工裁定：本引擎不做实例解析（由 SKILL.md 委托 `diyc.py resolve`）、不读 `diy-coder.yaml`
取 output_dir（必填、由调用方传入；读它只为产物 `project.name`）、不扩 diyc 类型集
（新产物类型不进 `diyc.py check` 的硬编码集）。写盘只发生在 `new`，且只写自己的产物
`{output_dir}/module-plan.yaml`；`check` 全程零写入。
"""
import argparse
import datetime
import io
import json
import os
import re
import sys

import yaml

PLAN_FILE = "module-plan.yaml"
SKILL_FILE = "SKILL.md"
SKILLS_FACE_REL = os.path.join(".claude", "skills")
SUITE_SKILLS_REL = os.path.join("diy-coder", "skills")
PROJECT_KEYS = ("name", "created", "updated")
FRONTMATTER_FIELDS = ("phase", "precededBy", "followedBy", "required", "line", "outputs")
PLAN_ID_RE = re.compile(r"MP-\d{3}\Z")
NAME_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
NAME_MAX = 64
KINDS = ("工作流", "工具")
STATUSES = ("草稿", "已定稿")
ASSUMPTION = "[假设]"
TOKEN_RE = re.compile(r"\{[^{}]*\}")
ROOT_TOKEN = "{project-root}"
ANY_PHASE_SPELLINGS = ("any", "anytime")


# trace: diy-bmb-module 违规构造（统一 {code, where, msg} 形态；where 正斜杠）
def v(code, where, msg):
    return {"code": code, "where": str(where).replace("\\", "/"), "msg": msg}


# trace: diy-bmb-module 非空判定（None / 空白字符串均视为空）
def nonempty(value):
    return value is not None and str(value).strip() != ""


# trace: diy-bmb-module where 显示口径（正斜杠 + 相对 project-root；越界回退绝对路径）
def display_path(path, project_root):
    try:
        rel = os.path.relpath(path, project_root)
    except ValueError:
        rel = os.path.abspath(path)
    if rel.startswith(".."):
        return os.path.abspath(path).replace("\\", "/")
    return rel.replace("\\", "/")


# trace: diy-bmb-module 相位归一（`any` 与 `anytime` 双轨等价——套件内两种拼写并存，非差异）
def normalize_phase(value):
    text = str(value).strip()
    return "anytime" if text in ANY_PHASE_SPELLINGS else text


# trace: diy-bmb-module YAML 安全装载：(data, err)；缺失 (None, None)、空文件 ({}, None)、损坏 (None, 原因)
def load_yaml_safe(path):
    if not os.path.isfile(path):
        return None, None
    try:
        with io.open(path, "r", encoding="utf-8") as handle:
            return (yaml.safe_load(handle) or {}), None
    except yaml.YAMLError as e:
        return None, str(e)
    except OSError as e:
        return None, str(e)


# trace: diy-bmb-module 原子写盘（同款 diyc_lib.save_yaml_atomic：同目录 tmp + os.replace；
# 失败清理 tmp 后原样抛出，不留残骸、不吞异常）
def save_yaml_atomic(path, data):
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


# trace: diy-bmb-module 集合字段取列表（缺失/非列表 → []，缺项由 check 层单独报）
def items(doc, key):
    if not isinstance(doc, dict):
        return []
    value = doc.get(key)
    return value if isinstance(value, list) else []


# trace: diy-bmb-module 链字段归一（列表原样；单值包一层；空/None → []）
def as_links(value):
    if isinstance(value, list):
        return [str(x) for x in value if nonempty(x)]
    return [str(value)] if nonempty(value) else []


# trace: diy-bmb-module 递归收集任意节点的字符串值（[假设] 扫描用，只看值不看键）
def collect_strings(node):
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for value in node.values():
            for text in collect_strings(value):
                yield text
    elif isinstance(node, list):
        for entry in node:
            for text in collect_strings(entry):
                yield text


# trace: diy-bmb-module 今日日期（YYYY-MM-DD）
def today():
    return datetime.date.today().isoformat()


# trace: diy-bmb-module 路径令牌处置：{project-root} 按 --project-root 自解析，其余 {...} 一律拒绝
def resolve_path_arg(raw, project_root):
    text = str(raw)
    resolved = text.replace(ROOT_TOKEN, project_root)
    return resolved, sorted({token for token in TOKEN_RE.findall(resolved)})


# trace: diy-bmb-module 回执输出（--json 单行 / 人读行）
def emit(payload, as_json, human_lines):
    if as_json:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        human_lines(payload)


# trace: diy-bmb-module 人读态末尾汇总行（三处回执共用）
def summary_line(payload):
    print("汇总：违规 %d 条 · 警告 %d 条（exit %d）"
          % (len(payload["violations"]), len(payload["warnings"]),
             0 if payload["ok"] else 1))


# trace: diy-bmb-module 人读态逐行渲染（违规 `CODE where: msg`、警告 `WARN CODE where: msg`）
def human_lines(payload):
    for item in payload["violations"]:
        print("%s %s: %s" % (item["code"], item["where"], item["msg"]))
    for item in payload["warnings"]:
        print("WARN %s %s: %s" % (item["code"], item["where"], item["msg"]))
    summary_line(payload)


# trace: diy-bmb-module 计划骨架（空值即「未写」——把写作纪律写进文档本身）
def skeleton_record(plan_id, slug, title):
    return {
        "id": plan_id,
        "slug": slug,
        "title": title,
        "status": "草稿",
        "date": today(),
        "vision": "",
        "skills": [],
        "dependencies": [],
        "build_order": [],
        "open_questions": [],
    }


# trace: diy-bmb-module 产物 project.name（配置优先，缺配置回退项目目录名）
def project_name(project_root):
    cfg, _err = load_yaml_safe(os.path.join(project_root, "diy-coder.yaml"))
    if isinstance(cfg, dict) and isinstance(cfg.get("project"), dict):
        name = cfg["project"].get("name")
        if nonempty(name):
            return str(name)
    return os.path.basename(os.path.abspath(project_root))


# trace: diy-bmb-module 下一个计划号（既有最大号 + 1，三位零填充；不重编不重用）
def next_plan_id(plans):
    top = 0
    for plan in plans:
        if not isinstance(plan, dict):
            continue
        match = re.fullmatch(r"MP-(\d{3})", str(plan.get("id") or ""))
        if match:
            top = max(top, int(match.group(1)))
    return "MP-%03d" % (top + 1)


# trace: diy-bmb-module 技能查找两面（权威面 = --skills-root 或安装面；第二面 = 套件源树）
def skill_faces(skills_root, project_root):
    return [os.path.abspath(skills_root),
            os.path.join(os.path.abspath(project_root), SUITE_SKILLS_REL)]


# trace: diy-bmb-module 技能定位（两面依次查 <face>/<name>/SKILL.md；两处都没有 → None）
def find_skill(name, faces):
    for face in faces:
        path = os.path.join(face, str(name), SKILL_FILE)
        if os.path.isfile(path):
            return path
    return None


# trace: diy-bmb-module frontmatter 读取（首行 --- 到下一个 --- 之间；返回 (映射|None, 失败原因|None)）
def read_frontmatter(path):
    try:
        with io.open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
    except OSError as e:
        return None, "读取失败：%s" % e
    lines = text.replace("\r\n", "\n").split("\n")
    if not lines or lines[0].strip() != "---":
        return None, "缺 frontmatter 段（首行须为 ---）"
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return None, "frontmatter 段未闭合"
    try:
        data = yaml.safe_load("\n".join(lines[1:end]))
    except yaml.YAMLError as e:
        return None, "frontmatter 解析失败：%s" % e
    if data is None:
        return {}, None
    if not isinstance(data, dict):
        return None, "frontmatter 不是映射"
    return data, None


# trace: diy-bmb-module 顶层结构校验（project 三键 + plans/revisions 两列表 + 顶层不设 status）
def check_top_level(data, show):
    violations = []
    project = data.get("project")
    if not isinstance(project, dict):
        violations.append(v("EMPTY_FIELD", show + " project",
                            "project 缺失或不是映射（须含 name/created/updated）"))
    else:
        for key in PROJECT_KEYS:
            if not nonempty(project.get(key)):
                violations.append(v("EMPTY_FIELD", "%s project.%s" % (show, key),
                                    "project.%s 缺失" % key))
    for key in ("plans", "revisions"):
        if key not in data:
            violations.append(v("EMPTY_FIELD", "%s %s" % (show, key),
                                "%s 缺失（无内容写空列表）" % key))
        elif not isinstance(data.get(key), list):
            violations.append(v("EMPTY_FIELD", "%s %s" % (show, key), "%s 不是列表" % key))
    if "status" in data:
        violations.append(v("STATUS_MISMATCH", show + " status",
                            "多记录产物顶层不设 status（定稿态挂记录级 `status: 草稿|已定稿`）"))
    return violations


# trace: diy-bmb-module 字段齐备判定（键在且值非 None——空列表是合法值，缺键才是缺失）
def missing_fields(mapping):
    return [key for key in FRONTMATTER_FIELDS if key not in mapping or mapping.get(key) is None]


# trace: diy-bmb-module 引用三档（计划内 → None / 已装 → "installed" / 两边都不是 → "unknown"）
def reference_tier(name, plan_names, faces):
    if name in plan_names:
        return None
    if find_skill(name, faces):
        return "installed"
    return "unknown"


# trace: diy-bmb-module 技能条目字段面（name 命名 / kind 枚举 / purpose / brief / 布尔与列表）
def check_skill_entry(index, entry, where, violations, stats):
    ewhere = "%s.skills[%d]" % (where, index)
    if not isinstance(entry, dict):
        violations.append(v("EMPTY_FIELD", ewhere, "技能条目不是映射（须含 name/kind/purpose/brief）"))
        return "", {}
    name = entry.get("name")
    if not nonempty(name):
        violations.append(v("EMPTY_FIELD", ewhere + ".name",
                            "技能名缺失（写完整技能名，含 `diy-` 前缀）"))
        return "", entry
    name = str(name)
    if len(name) > NAME_MAX or not NAME_RE.fullmatch(name):
        violations.append(v("NAME_ILLEGAL", ewhere + ".name",
                            "技能名须为 hyphen-case（小写字母/数字、单连字符分隔）且不超过 64 字符，"
                            "实为 %s" % name))
    kind = entry.get("kind")
    if not nonempty(kind):
        violations.append(v("EMPTY_FIELD", ewhere + ".kind", "%s 的 kind 缺失（工作流|工具）" % name))
    elif str(kind) not in KINDS:
        violations.append(v("ENUM_INVALID", ewhere + ".kind",
                            "%s 的 kind 越界：%s（合法集 %s）" % (name, kind, "|".join(KINDS))))
    for key in ("purpose", "brief"):
        if not nonempty(entry.get(key)):
            violations.append(v("EMPTY_FIELD", "%s.%s" % (ewhere, key),
                                "%s 的 %s 缺失（brief 须自足到不靠对话上下文即可交棒给"
                                " diy-bmb-builder）" % (name, key)))
    for key in ("dropped", "new"):
        value = entry.get(key)
        if value is not None and not isinstance(value, bool):
            violations.append(v("ENUM_INVALID", "%s.%s" % (ewhere, key),
                                "%s 的 %s 须为布尔（true/false），实为 %s" % (name, key, value)))
    depends = entry.get("depends_on")
    if depends is not None and not isinstance(depends, list):
        violations.append(v("EMPTY_FIELD", ewhere + ".depends_on",
                            "%s 的 depends_on 不是列表（批次内依赖，无依赖写 []）" % name))
    stats["skills"] += 1
    if entry.get("new") is True:
        stats["new_skills"] += 1
    return name, entry


# trace: diy-bmb-module 注册面：存在性 + 六字段 + 双向对称 + 悬空指向（三档处置，见模块 docstring ③）
def check_registration(entries, names, faces, where, violations, warnings, stats):
    found = {}
    plan_names = set(names)
    for index, entry in enumerate(entries):
        name = names[index]
        ewhere = "%s.skills[%d]" % (where, index)
        if not name:
            continue
        path = find_skill(name, faces)
        if path is None:
            stats["missing"] += 1
            warnings.append(v("MISSING_FILE", ewhere,
                              "计划声明的技能 %s 尚未建造（计划先于建造是计划器常态，不阻断）" % name))
            continue
        stats["installed"] += 1
        fm, reason = read_frontmatter(path)
        if reason is not None:
            fm = {}
        missing = missing_fields(fm)
        if missing:
            msg = ("%s 的 SKILL.md frontmatter 缺字段：%s" % (name, " / ".join(missing)))
            if reason is not None:
                msg += "（%s）" % reason
            if entry.get("new") is True:
                violations.append(v("EMPTY_FIELD", ewhere + ".name",
                                    msg + "（本批新建技能须六字段齐备）"))
            else:
                warnings.append(v("EMPTY_FIELD", ewhere + ".name",
                                  msg + "（存量技能零字段是既成事实，本技能零写面改不了——记 warning 不判红）"))
        phase = fm.get("phase")
        key = normalize_phase(phase) if nonempty(phase) else "未声明"
        stats["phases"][key] = stats["phases"].get(key, 0) + 1
        found[name] = fm
    # 链接面：双向对称（仅计划内）+ 悬空指向 + 计划外对端
    partners = {}
    for index, entry in enumerate(entries):
        name = names[index]
        if not name or name not in found:
            continue
        ewhere = "%s.skills[%d]" % (where, index)
        fm = found[name]
        for field, mirror in (("followedBy", "precededBy"), ("precededBy", "followedBy")):
            if field not in fm:
                continue
            for linked in as_links(fm.get(field)):
                tier = reference_tier(linked, plan_names, faces)
                if tier == "unknown":
                    violations.append(v("UNKNOWN_ID", "%s.%s" % (ewhere, field),
                                        "%s 的 %s 指向 %s：既不在本计划内、也不是已装技能"
                                        "（悬空指向）" % (name, field, linked)))
                    continue
                if tier == "installed":
                    if linked not in partners:
                        partners[linked] = (ewhere, field, name)
                    continue
                if linked not in found or mirror not in found[linked]:
                    continue
                if name not in as_links(found[linked].get(mirror)):
                    violations.append(v("SET_MISMATCH", "%s.%s" % (ewhere, field),
                                        "双向对称：%s 的 %s 指向 %s，但 %s 的 %s 未回指 %s"
                                        % (name, field, linked, linked, mirror, name)))
    for linked, (ewhere, field, name) in sorted(partners.items()):
        warnings.append(v("UNKNOWN_ID", "%s.%s" % (ewhere, field),
                          "对端在计划外（已装技能，允许——依赖既有能力）：%s 引用 %s"
                          % (name, linked)))
        path = find_skill(linked, faces)
        fm, reason = read_frontmatter(path) if path else (None, "不可读")
        missing = missing_fields(fm) if reason is None else list(FRONTMATTER_FIELDS)
        if missing:
            warnings.append(v("EMPTY_FIELD", "%s.%s" % (ewhere, field),
                              "计划外对端 %s 的 frontmatter 缺字段：%s（不碰存量，记 warning）"
                              % (linked, " / ".join(missing))))


# trace: diy-bmb-module 单条记录校验（schema + 引用闭包 + 注册面 + --final 义务）
def check_plan_record(index, plan, show, final, faces, violations, warnings, stats):
    where = "%s.plans[%d]" % (show, index)
    pid = plan.get("id")
    if not nonempty(pid):
        violations.append(v("EMPTY_FIELD", where + ".id", "id 缺失（须为 MP-###）"))
    elif not PLAN_ID_RE.fullmatch(str(pid)):
        violations.append(v("ENUM_INVALID", where + ".id",
                            "id 须为 MP-###（三位零填充），实为 %s" % pid))
    label = "记录 %s" % pid if nonempty(pid) else "记录 plans[%d]" % index
    for key, why in (("slug", "同一 slug 更新既有计划、不新建"),
                     ("title", "计划标题"),
                     ("vision", "这批技能要解决什么——一段话")):
        if not nonempty(plan.get(key)):
            violations.append(v("EMPTY_FIELD", "%s.%s" % (where, key),
                                "%s 的 %s 缺失（%s）" % (label, key, why)))
    if not nonempty(plan.get("date")):
        violations.append(v("EMPTY_FIELD", where + ".date", "%s 的 date 缺失（YYYY-MM-DD）" % label))
    status = plan.get("status")
    if not nonempty(status):
        violations.append(v("EMPTY_FIELD", where + ".status", "%s 的 status 缺失（草稿|已定稿）" % label))
    elif str(status) not in STATUSES:
        violations.append(v("ENUM_INVALID", where + ".status",
                            "%s 的 status 越界：%s（合法集 %s）" % (label, status, "|".join(STATUSES))))
    for key, note in (("dependencies", "批次内依赖关系"),
                      ("build_order", "构建路线图（builder 按序消费）"),
                      ("open_questions", "未决问题")):
        if not isinstance(plan.get(key), list):
            violations.append(v("EMPTY_FIELD", "%s.%s" % (where, key),
                                "%s 的 %s 缺失或不是列表（无内容写 []；%s）" % (label, key, note)))
    raw_skills = plan.get("skills")
    if not isinstance(raw_skills, list):
        violations.append(v("EMPTY_FIELD", where + ".skills",
                            "%s 的 skills 缺失或不是列表" % label))
        raw_skills = []
    elif not raw_skills:
        msg = ("%s 的 skills 为空（计划先于建造的常态，不阻断；--final 一律拒绝）" % label)
        (violations if final else warnings).append(v("EMPTY_FIELD", where + ".skills", msg))
    names = []
    entries = []
    for i, entry in enumerate(raw_skills):
        name, kept = check_skill_entry(i, entry, where, violations, stats)
        if name and name in names:
            violations.append(v("DUPLICATE_ID", "%s.skills[%d].name" % (where, i),
                                "%s 的技能名 %s 在本记录内重复（计划内名字即引用键，须唯一）"
                                % (label, name)))
        names.append(name)
        entries.append(kept)
    plan_names = {name for name in names if name}
    for i, (name, entry) in enumerate(zip(names, entries)):
        if not name or not isinstance(entry, dict):
            continue
        ewhere = "%s.skills[%d]" % (where, i)
        refs = [(str(x), ewhere + ".depends_on") for x in as_links(entry.get("depends_on"))]
        for key in ("dependencies", "build_order"):
            refs += [(str(x), "%s.%s" % (where, key)) for x in as_links(plan.get(key))]
        for ref, refwhere in refs:
            tier = reference_tier(ref, plan_names, faces)
            if tier == "unknown":
                violations.append(v("UNKNOWN_ID", refwhere,
                                    "引用越界：%s 既不在本计划内、也不是已装技能" % ref))
            elif tier == "installed":
                warnings.append(v("UNKNOWN_ID", refwhere,
                                  "对端在计划外（已装技能，允许——依赖既有能力）：%s" % ref))
    check_registration(entries, names, faces, where, violations, warnings, stats)
    if final:
        if str(status) != "已定稿":
            violations.append(v("STATUS_MISMATCH", where + ".status",
                                "--final 要求 status: 已定稿，实为 %s" % (status if nonempty(status) else "未声明")))
        for text in collect_strings(plan):
            if ASSUMPTION in text:
                violations.append(v("ASSUMPTION_PRESENT", where,
                                    "--final 要求零 [假设]；未决推断须先落定再交"))
                break
    stats["checked"] += 1


# trace: diy-bmb-module --previous 配对（键 = slug；旧有新无的条目且未标 dropped → ID_UNSTABLE）
def check_previous(prev_path, prev_show, selected, show, violations):
    data, err = load_yaml_safe(prev_path)
    if data is None and err is None:
        violations.append(v("MISSING_FILE", prev_show,
                            "--previous 旧稿不存在或不可读：%s" % prev_show))
        return
    if err is not None:
        violations.append(v("UNPARSABLE_YAML", prev_show, "旧稿 YAML 解析失败：%s" % err))
        return
    if not isinstance(data, dict):
        violations.append(v("EMPTY_FIELD", prev_show, "旧稿顶层不是映射（须含 plans）"))
        return
    by_slug = {}
    for plan in items(data, "plans"):
        if isinstance(plan, dict) and nonempty(plan.get("slug")):
            by_slug.setdefault(str(plan["slug"]), plan)
    for index, plan in selected:
        slug = str(plan.get("slug") or "")
        old = by_slug.get(slug)
        if old is None:
            continue
        new_names = {str(entry.get("name")) for entry in items(plan, "skills")
                     if isinstance(entry, dict) and nonempty(entry.get("name"))}
        for entry in items(old, "skills"):
            if not isinstance(entry, dict):
                continue
            name = entry.get("name")
            if not nonempty(name) or str(name) in new_names:
                continue
            violations.append(v("ID_UNSTABLE", "%s.plans[%d].skills" % (show, index),
                                "旧稿 %s（slug: %s）有而新稿无的技能条目 %s，且未标 dropped: true"
                                "——技能清单收缩 = 计划变更，须机械留痕"
                                % (old.get("id"), slug, name)))


# trace: diy-bmb-module check 子命令（批次计划校验；只读、零写面；exit 0 唯一放行）
def cmd_check(args):
    root = os.path.abspath(args.project_root)
    out_value, out_tokens = resolve_path_arg(args.output_dir, root)
    prev_value, prev_tokens = resolve_path_arg(args.previous, root) if args.previous else ("", [])
    skills_value, skills_tokens = (resolve_path_arg(args.skills_root, root)
                                   if args.skills_root else ("", []))
    out = os.path.abspath(out_value)
    plan_path = os.path.join(out, PLAN_FILE)
    show = display_path(plan_path, root)
    prev_path = os.path.abspath(prev_value) if prev_value else ""
    violations = []
    warnings = []
    stats = {"plans": 0, "checked": 0, "skills": 0, "new_skills": 0,
             "installed": 0, "missing": 0, "phases": {}}
    payload = {
        "ok": False,
        "command": "check",
        "project_root": args.project_root,
        "output_dir": os.path.normpath(out).replace("\\", "/"),
        "final": bool(args.final),
        "violations": violations,
        "warnings": warnings,
        "counts": stats,
    }
    tokens = out_tokens + prev_tokens + skills_tokens
    if tokens:
        for token in tokens:
            violations.append(v("TOKEN_UNRESOLVED", token,
                                "未解析的路径令牌：{...} 一律拒绝；唯一例外 {project-root} "
                                "由引擎按 --project-root 自解析"))
        emit(payload, args.json, human_lines)
        return 1
    faces = skill_faces(skills_value or os.path.join(root, SKILLS_FACE_REL), root)
    data, err = load_yaml_safe(plan_path)
    selected = []
    if data is None and err is None:
        violations.append(v("MISSING_FILE", show,
                            "%s 不存在（先跑 new 铸计划骨架、再填内容）" % PLAN_FILE))
    elif err is not None:
        violations.append(v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err))
    elif not isinstance(data, dict):
        violations.append(v("EMPTY_FIELD", show, "顶层不是映射（须为 project + plans + revisions）"))
    else:
        violations += check_top_level(data, show)
        raw_plans = data.get("plans")
        plans = raw_plans if isinstance(raw_plans, list) else []
        stats["plans"] = len(plans)
        if isinstance(raw_plans, list) and not raw_plans:
            msg = "plans 为空（计划先于建造的常态，不阻断；--final 一律拒绝）"
            (violations if args.final else warnings).append(v("EMPTY_FIELD", show + " plans", msg))
        seen = set()
        for i, plan in enumerate(plans):
            if not isinstance(plan, dict):
                violations.append(v("EMPTY_FIELD", "%s.plans[%d]" % (show, i), "记录不是映射"))
                continue
            pid = str(plan.get("id") or "")
            if pid and pid in seen:
                violations.append(v("DUPLICATE_ID", "%s.plans[%d].id" % (show, i),
                                    "记录 ID %s 重复（ID 稳定不重用）" % pid))
            seen.add(pid)
            if args.id and pid != args.id:
                continue
            selected.append((i, plan))
        if args.id and not selected:
            violations.append(v("UNKNOWN_ID", "%s.plans" % show,
                                "--id %s 在本文件不存在" % args.id))
        for i, plan in selected:
            check_plan_record(i, plan, show, bool(args.final), faces, violations, warnings, stats)
    if prev_path:
        check_previous(prev_path, display_path(prev_path, root), selected, show, violations)
    payload["ok"] = not violations
    emit(payload, args.json, human_lines)
    return 0 if payload["ok"] else 1


# trace: diy-bmb-module check 人读态（PASS 行 + 逐违规/警告行 + 汇总行）
def human_check(payload):
    if payload["ok"]:
        counts = payload["counts"]
        print("PASS：%s 校验通过（计划 %d 条 · 技能 %d 个 · 本批新建 %d 个）"
              % (payload["output_dir"] + "/" + PLAN_FILE, counts["plans"],
                 counts["skills"], counts["new_skills"]))
    human_lines(payload)


# trace: diy-bmb-module new 人读态（铸造行 + 空值即未写提示 + 汇总行）
def human_new(payload):
    if payload["ok"]:
        print("新建计划 %s（slug: %s）→ %s"
              % (payload["plan_id"], payload["slug"], payload["file"]))
        print("骨架里除 id/slug/title/status/date 外都是空值——空值即「未写」，step 2 逐项填。")
    human_lines(payload)


# trace: diy-bmb-module new 子命令（铸造 MP-### 骨架；同 slug 拒绝；写盘仅本产物）
def cmd_new(args):
    root = os.path.abspath(args.project_root)
    out_value, out_tokens = resolve_path_arg(args.output_dir, root)
    out = os.path.abspath(out_value)
    path = os.path.join(out, PLAN_FILE)
    show = display_path(path, root)
    violations = []
    payload = {
        "ok": False,
        "command": "new",
        "project_root": args.project_root,
        "output_dir": os.path.normpath(out).replace("\\", "/"),
        "violations": violations,
        "warnings": [],
        "counts": {"plans": 0},
        "plan_id": "",
        "slug": str(args.slug or ""),
        "file": show,
        "created": today(),
    }
    if out_tokens:
        for token in out_tokens:
            violations.append(v("TOKEN_UNRESOLVED", token,
                                "未解析的路径令牌：{...} 一律拒绝；唯一例外 {project-root} "
                                "由引擎按 --project-root 自解析"))
        emit(payload, args.json, human_new)
        return 1
    slug = str(args.slug or "").strip()
    if not slug:
        sys.stderr.write("missing_slug: 未给 --slug——同一 slug 更新既有计划、不新建；"
                         "无头下缺 slug 直接拒绝、零产出。\n")
        violations.append(v("EMPTY_FIELD", "--slug", "slug 缺失：计划的身份键，缺它无法判定"
                                                     "「新建」还是「更新」"))
        emit(payload, args.json, human_new)
        return 1
    data, err = load_yaml_safe(path)
    if data is None and err is None:
        data = {"project": {"name": project_name(root), "created": today(), "updated": today()},
                "plans": [], "revisions": []}
    elif err is not None:
        violations.append(v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err))
    elif not isinstance(data, dict):
        violations.append(v("EMPTY_FIELD", show, "顶层不是映射（须为 project + plans + revisions）"))
    elif not isinstance(data.get("project"), dict) or not isinstance(data.get("revisions"), list):
        violations.append(v("EMPTY_FIELD", show,
                            "既有文件缺 project 或 revisions（先跑 check 修好骨架，再 new）"))
    if violations:
        emit(payload, args.json, human_new)
        return 1
    plans = data.get("plans")
    if not isinstance(plans, list):
        violations.append(v("EMPTY_FIELD", show + " plans", "plans 缺失或不是列表"))
        emit(payload, args.json, human_new)
        return 1
    for plan in plans:
        if isinstance(plan, dict) and str(plan.get("slug") or "") == slug:
            violations.append(v("DUPLICATE_ID", show,
                                "slug %s 已存在于记录 %s——同一 slug 更新走记录就地编辑，不新建"
                                % (slug, plan.get("id"))))
            emit(payload, args.json, human_new)
            return 1
    plan_id = next_plan_id(plans)
    plans.append(skeleton_record(plan_id, slug, str(args.title or "").strip()))
    data["project"]["updated"] = today()
    if not os.path.isdir(out):
        os.makedirs(out, exist_ok=True)
    save_yaml_atomic(path, data)
    payload["ok"] = True
    payload["plan_id"] = plan_id
    payload["counts"] = {"plans": len(plans)}
    emit(payload, args.json, human_new)
    return 0


# trace: diy-bmb-module 命令行面（--output-dir 必填；引擎不做实例解析）
def build_parser():
    ap = argparse.ArgumentParser(
        description="diy-bmb-module 确定性引擎：计划骨架铸造（new）+ 批次计划校验（check，只读）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    n = sub.add_parser("new", help="铸计划骨架（MP-### 递增；同 slug 更新走记录就地编辑）")
    n.add_argument("--slug", default="", help="计划 slug（必给；是「新建还是更新」的判定键）")
    n.add_argument("--title", default="", help="计划标题（可省，内容面随后补）")
    n.add_argument("--project-root", default=".", help="项目根（默认 .）")
    n.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    n.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    n.set_defaults(func=cmd_new)

    k = sub.add_parser("check", help="校验 module-plan.yaml（schema/引用闭包/注册面六字段；"
                                     "只读、零写入）")
    k.add_argument("--final", action="store_true",
                   help="终门校验：全部被检记录 status: 已定稿 + 零 [假设] + skills 非空")
    k.add_argument("--previous", default="",
                   help="旧稿路径（配对键 = slug；旧有新无的技能条目且未标 dropped → ID_UNSTABLE）")
    k.add_argument("--id", default="", help="只校验该记录（缺省 = 全部记录，逐条报）")
    k.add_argument("--skills-root", default="",
                   help="技能查找的权威面（缺省 {project-root}/.claude/skills；第二面固定为套件源树）")
    k.add_argument("--project-root", default=".", help="项目根（默认 .）")
    k.add_argument("--output-dir", required=True,
                   help="产物目录（必填；由调用方传入，引擎不做实例解析/目录推导）")
    k.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    k.set_defaults(func=cmd_check)
    return ap


# trace: diy-bmb-module 入口（stdout/stderr 固定 UTF-8；退出码由子命令返回）
def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = build_parser().parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
