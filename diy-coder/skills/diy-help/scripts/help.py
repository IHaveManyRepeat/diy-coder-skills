# -*- coding: utf-8 -*-
"""diy-help 状态机引擎：扫产物链 → 计算当前位置 → 推荐下一步 skill。

产物链（D-2 单一源，status 读 project.status）：
  prd → architecture → openapi(可选) → epics+stories → test-plan → sprint → build-loop

规则：
- 第一个非 final 节点即当前位置：文件缺失=未开始（推荐该节点 skill）；
  文件存在但 status != final = 阻塞（指明 file + status + action）。
- openapi.yaml 可选（D-6：无 API 面项目优雅终止）：全缺失=合法跳过，
  仅当存在且非 final 才阻塞。
- sprint.yaml final 后看任务状态：有 blocked 任务 → 指明人工解除；
  其余非终态 → diy-build-loop；全 done → 工作流完成。
- 只读导航，零写回。实例解析对齐 FR-4.5/D-9。
"""
# trace: S-13 AC-13.1 AC-13.2 TC-13.1.1 TC-13.1.2 TC-13.2.1
import argparse
import io
import json
import os
import re
import sys

import yaml

INSTANCE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")

CHAIN = [
    {"skill": "diy-prd", "files": ["prd.yaml"]},
    {"skill": "diy-architecture", "files": ["architecture.yaml"]},
    {"skill": "diy-openapi", "files": ["openapi.yaml"], "optional": True},
    {"skill": "diy-epics-stories", "files": ["epics.yaml", "stories.yaml"]},
    {"skill": "diy-test-design", "files": ["test-plan.yaml"]},
    {"skill": "diy-sprint", "files": ["sprint.yaml"]},
]


def load_yaml(path):
    with io.open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def resolve_output_dir(project_root, instance):  # trace: S-16 AC-16.1 D-9 实例目录解析（白名单拒注入，主线平铺兼容）
    cfg_path = os.path.join(project_root, "diy-coder.yaml")
    output_dir = "diy-output"
    if os.path.isfile(cfg_path):
        # trace: S-13 AC-13.1 TC-13.1.6 配置损坏/半写（paths 为 null 等）降级默认值，不崩
        try:
            cfg = load_yaml(cfg_path)
        except yaml.YAMLError as e:
            sys.stderr.write("WARN diy-coder.yaml: %s\n" % e)
            cfg = {}
        if not isinstance(cfg, dict):
            cfg = {}
        output_dir = (cfg.get("paths") or {}).get("output_dir", output_dir)
    if instance:
        if not INSTANCE_RE.match(instance):
            sys.stderr.write("invalid instance name: %s\n" % instance)
            sys.exit(1)
        output_dir = os.path.join(output_dir, instance)
    return os.path.join(project_root, output_dir)


def read_status(path):  # trace: S-13 AC-13.1 TC-13.1.6 读产物 project.status；语法/形状/半写降级 unparsable 而非崩溃
    """读产物 project.status；文件损坏或形状异常时返回 'unparsable' 并在 stderr 报告。"""
    try:
        doc = load_yaml(path)
    except yaml.YAMLError as e:
        sys.stderr.write("WARN %s: %s\n" % (os.path.basename(path), e))
        return "unparsable"
    if not isinstance(doc, dict):
        sys.stderr.write("WARN %s: 顶层不是映射，按 unparsable 处理\n"
                         % os.path.basename(path))
        return "unparsable"
    proj = doc.get("project") or {}
    if not isinstance(proj, dict):
        sys.stderr.write("WARN %s: project 节点形状异常，按 unparsable 处理\n"
                         % os.path.basename(path))
        return "unparsable"
    return proj.get("status", "unknown")


def scan_chain(output_dir):  # trace: S-13 AC-13.1 TC-13.1.1 TC-13.1.2 存在性+status 扫链定位置/推荐
    """返回 (completed_skills, next_skill, blocked, notes)。"""
    completed, notes = [], []
    for node in CHAIN:
        skill, files = node["skill"], node["files"]
        exists = [f for f in files if os.path.isfile(os.path.join(output_dir, f))]
        if not exists:
            if node.get("optional"):
                notes.append("openapi.yaml 不存在——若本项目有 API 面，可随时运行 diy-openapi 生成契约")
                continue
            return completed, skill, None, notes
        statuses = {f: read_status(os.path.join(output_dir, f)) for f in exists}
        unfinal = {f: s for f, s in statuses.items() if s != "final"}
        if unfinal:
            f, s = sorted(unfinal.items())[0]
            action = "继续 %s 直至 %s 定稿（status: final）" % (skill, f)
            return completed, None, {"file": f, "status": s, "action": action}, notes
        completed.append(skill)
    return completed, None, None, notes


def scan_sprint(output_dir):  # trace: S-13 AC-13.1 TC-13.1.6 链后读 sprint 任务；tasks 形状异常降级阻断
    """链走完后读 sprint 任务状态。返回 (next_skill, blocked, workflow_done)。"""
    sprint = load_yaml(os.path.join(output_dir, "sprint.yaml"))
    tasks = sprint.get("tasks")
    if not isinstance(tasks, list) or not all(isinstance(t, dict) for t in tasks):
        blocked = {
            "file": "sprint.yaml",
            "status": "unparsable",
            "action": "sprint.yaml 的 tasks 形状异常（半写/损坏），修复后重跑",
        }
        return None, blocked, False
    blocked_tasks = [t for t in tasks if t.get("status") == "blocked"]
    if blocked_tasks:
        names = ", ".join(str(t.get("story", "?")) for t in blocked_tasks)
        blocked = {
            "file": "sprint.yaml",
            "status": "blocked",
            "action": "人工解除阻塞任务（%s）的 blocked_reason 后重跑" % names,
        }
        return None, blocked, False
    if all(t.get("status") == "done" for t in tasks) and tasks:
        return None, None, True
    return "diy-build-loop", None, False


def render_human(result):  # trace: S-13 AC-13.2 TC-13.2.1 阻塞优先聚焦；blocked 时抑制可选提示
    lines = []
    lines.append("当前位置：%s" % result["position"])
    if result["completed_steps"]:
        lines.append("已完成：%s" % "、".join(result["completed_steps"]))
    if result["blocked"]:
        b = result["blocked"]
        lines.append("阻塞项：%s（当前状态 %s）" % (b["file"], b["status"]))
        lines.append("需要的动作：%s" % b["action"])
    else:
        if result["next_skill"]:
            lines.append("下一步：运行 %s" % result["next_skill"])
        elif result["workflow_done"]:
            lines.append("下一步：工作流已全部完成。可选收尾：证伪轮、bug-log 经验入库。")
        for n in result["notes"]:
            lines.append("提示：%s" % n)
    return "\n".join(lines)


def main():  # trace: S-13 AC-13.1 TC-13.1.1 组装位置/推荐/阻塞（含零起点→diy-prd）
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="diy-coder 工作流状态机导航")
    ap.add_argument("--project-root", default=".", help="项目根目录")
    ap.add_argument("--instance", default=None, help="实例名（FR-4.5/D-9）")
    ap.add_argument("--json", action="store_true", help="机器可读 JSON 输出")
    args = ap.parse_args()

    output_dir = resolve_output_dir(args.project_root, args.instance)
    if not os.path.isdir(output_dir):
        position = "零起点"
        result = {
            "position": position,
            "output_dir": output_dir,
            "completed_steps": [],
            "next_skill": "diy-prd",
            "blocked": None,
            "notes": [],
            "workflow_done": False,
        }
    else:
        completed, next_skill, blocked, notes = scan_chain(output_dir)
        workflow_done = False
        if not next_skill and not blocked:
            next_skill, blocked, workflow_done = scan_sprint(output_dir)
        if blocked:
            position = "阻塞于 %s" % blocked["file"]
        elif workflow_done:
            position = "工作流完成"
        elif next_skill == "diy-build-loop":
            position = "执行阶段"
        else:
            step = next(i + 1 for i, n in enumerate(CHAIN) if n["skill"] == next_skill)
            position = "第 %d/%d 步：%s" % (step, len(CHAIN), next_skill)
        result = {
            "position": position,
            "output_dir": output_dir,
            "completed_steps": completed,
            "next_skill": next_skill,
            "blocked": blocked,
            "notes": notes,
            "workflow_done": workflow_done,
        }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render_human(result))


if __name__ == "__main__":
    main()
