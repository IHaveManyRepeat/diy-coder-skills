# -*- coding: utf-8 -*-
"""bmb-module 通用小件：常量与骨架零件。"""

import io
import os
import re

import yaml

from diyc_lib import nonempty, today

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


# trace: diy-bmb-module 非空判定（None / 空白字符串均视为空）


# trace: diy-bmb-module 相位归一（`any` 与 `anytime` 双轨等价——套件内两种拼写并存，非差异）
def normalize_phase(value):
    text = str(value).strip()
    return "anytime" if text in ANY_PHASE_SPELLINGS else text


# trace: diy-bmb-module YAML 安全装载：(data, err)；缺失 (None, None)、空文件 ({}, None)、损坏 (None, 原因)


# trace: diy-bmb-module 原子写盘（同款 diyc_lib.save_yaml_atomic：同目录 tmp + os.replace；
# 失败清理 tmp 后原样抛出，不留残骸、不吞异常）


# trace: diy-bmb-module 链字段归一（列表原样；单值包一层；空/None → []）
def as_links(value):
    if isinstance(value, list):
        return [str(x) for x in value if nonempty(x)]
    return [str(value)] if nonempty(value) else []


# trace: diy-bmb-module 递归收集任意节点的字符串值（[假设] 扫描用，只看值不看键）


# trace: diy-bmb-module 今日日期（YYYY-MM-DD）


# trace: diy-bmb-module 路径令牌处置：{project-root} 按 --project-root 自解析，其余 {...} 一律拒绝
def resolve_path_arg(raw, project_root):
    text = str(raw)
    resolved = text.replace(ROOT_TOKEN, project_root)
    return resolved, sorted({token for token in TOKEN_RE.findall(resolved)})


# trace: diy-bmb-module 回执输出（--json 单行 / 人读行）


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
