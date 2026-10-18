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
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from bmb_module_checks import check_plan_record, check_previous, check_top_level  # noqa: E402
from bmb_module_lib import (PLAN_FILE, SKILLS_FACE_REL, human_lines, next_plan_id,
                            resolve_path_arg, skeleton_record, skill_faces)  # noqa: E402
from diyc_lib import display_path, emit_via, load_yaml_safe, now, project_name, save_yaml_atomic, v  # noqa: E402


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
        emit_via(payload, args.json, human_lines)
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
    emit_via(payload, args.json, human_lines)
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
        "created": now(),
    }
    if out_tokens:
        for token in out_tokens:
            violations.append(v("TOKEN_UNRESOLVED", token,
                                "未解析的路径令牌：{...} 一律拒绝；唯一例外 {project-root} "
                                "由引擎按 --project-root 自解析"))
        emit_via(payload, args.json, human_new)
        return 1
    slug = str(args.slug or "").strip()
    if not slug:
        sys.stderr.write("missing_slug: 未给 --slug——同一 slug 更新既有计划、不新建；"
                         "无头下缺 slug 直接拒绝、零产出。\n")
        violations.append(v("EMPTY_FIELD", "--slug", "slug 缺失：计划的身份键，缺它无法判定"
                                                     "「新建」还是「更新」"))
        emit_via(payload, args.json, human_new)
        return 1
    data, err = load_yaml_safe(path)
    if data is None and err is None:
        pname, _w = project_name(root)
        data = {"project": {"name": pname, "created": now(), "updated": now()},
                "plans": [], "revisions": []}
    elif err is not None:
        violations.append(v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err))
    elif not isinstance(data, dict):
        violations.append(v("EMPTY_FIELD", show, "顶层不是映射（须为 project + plans + revisions）"))
    elif not isinstance(data.get("project"), dict) or not isinstance(data.get("revisions"), list):
        violations.append(v("EMPTY_FIELD", show,
                            "既有文件缺 project 或 revisions（先跑 check 修好骨架，再 new）"))
    if violations:
        emit_via(payload, args.json, human_new)
        return 1
    plans = data.get("plans")
    if not isinstance(plans, list):
        violations.append(v("EMPTY_FIELD", show + " plans", "plans 缺失或不是列表"))
        emit_via(payload, args.json, human_new)
        return 1
    for plan in plans:
        if isinstance(plan, dict) and str(plan.get("slug") or "") == slug:
            violations.append(v("DUPLICATE_ID", show,
                                "slug %s 已存在于记录 %s——同一 slug 更新走记录就地编辑，不新建"
                                % (slug, plan.get("id"))))
            emit_via(payload, args.json, human_new)
            return 1
    plan_id = next_plan_id(plans)
    plans.append(skeleton_record(plan_id, slug, str(args.title or "").strip()))
    data["project"]["updated"] = now()
    if not os.path.isdir(out):
        os.makedirs(out, exist_ok=True)
    save_yaml_atomic(path, data)
    payload["ok"] = True
    payload["plan_id"] = plan_id
    payload["counts"] = {"plans": len(plans)}
    emit_via(payload, args.json, human_new)
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
