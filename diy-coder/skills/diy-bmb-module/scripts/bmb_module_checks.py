# -*- coding: utf-8 -*-
"""bmb-module 校验面：schema/引用闭包/注册面/--previous（只读零写）。"""

from bmb_module_lib import (ASSUMPTION, FRONTMATTER_FIELDS, KINDS, NAME_MAX, NAME_RE,
                            PLAN_ID_RE, PROJECT_KEYS, STATUSES, as_links, find_skill,
                            normalize_phase, read_frontmatter)
from diyc_lib import items, load_yaml_safe, nonempty, v, walk_strings

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
                                    msg + "（新建技能须六字段齐备）"))
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
        for _p, text in walk_strings(plan, ""):
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
