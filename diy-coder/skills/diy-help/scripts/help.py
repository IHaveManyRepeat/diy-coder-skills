# -*- coding: utf-8 -*-
"""diy-help 状态机引擎：读登记表 → 扫产物链 → 计算当前位置 → 推荐下一步 skill。

产物链（D-2 单一源；**链序与提示文案读 registry.yaml，节点的产物与必做性读该技能
SKILL.md 的 frontmatter 六字段**——两处不重复任何一条事实）：
  mainline：prd → architecture → openapi(可选) → design(可选) → epics+stories
            → test-plan → sprint → <exec>
  wds     ：wds-brief → wds-trigger → wds-scenarios →（余下节点随 B7 批次登记）

规则：
- 第一个非「已定稿」节点即当前位置：文件缺失=未开始（推荐该节点 skill）；
  文件存在但 status != 已定稿 = 阻塞（指明 file + status + action）。
- 可选节点（frontmatter `required: false`）：文件缺失=合法跳过（notes 提示），
  仅当存在且非「已定稿」才阻塞；多文件节点须全部文件存在才算完成。
- 链走完后看 sprint 任务状态：有「已阻塞」任务 → 指明人工解除；
  其余非终态 → 该线的 exec 技能；全「已完成」→ 工作流完成。
- 多线：无任何产物 → 零起点，回执给 branches 供按用途分叉；两条线产物并存 →
  提示由用户选定（本脚本不自动合并），线由 --line 指定。
- 登记表或技能 frontmatter 异常一律硬失败——本脚本是导航的唯一权威，
  宁可停手报错，也不给错的位置。
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

# 实例名白名单（与 viewer/runner/exp-sync 同源）：字母数字开头和结尾，中间可含 . _ -。
# 末字符禁点：Windows 目录名尾点被静默折叠（b. ≡ b），会破坏实例隔离；fullmatch 避免 $ 放行尾换行
INSTANCE_RE = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9_-])?")

DEFAULT_STATUS_PATH = ("project", "status")

# 技能根 = 本脚本所在技能目录的上一级。仓内 = diy-coder/skills/；
# 安装后 = {project-root}/.claude/skills/ —— 两种布局同式，故不依赖 --project-root。
_HERE = os.path.dirname(os.path.abspath(__file__))
SKILLS_DIR = os.path.dirname(os.path.dirname(_HERE))
REGISTRY_PATH = os.path.join(os.path.dirname(_HERE), "registry.yaml")

# 链节点的 outputs 形状：`+` 分隔的裸文件名（无空格/括号/破折号）。
# 非链技能可写自由文本（`—` / `技能目录树（…）`），但链节点必须可被机械解析。
_OUTPUT_TOKEN_RE = re.compile(r"^[A-Za-z0-9_.\-]+$")


def load_yaml(path):
    with io.open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _fail(msg):  # 登记表/技能声明异常一律硬失败（本脚本是导航唯一权威，不给错的位置）
    sys.stderr.write("FATAL %s\n" % msg)
    sys.exit(1)


def load_registry(path=REGISTRY_PATH):  # trace: C·1 登记表驱动——链序与提示文案的唯一来源
    """读登记表并校验形状；任何异常一律硬失败（不降级）。"""
    if not os.path.isfile(path):
        _fail("找不到登记表 %s（技能安装不完整？）" % path)
    try:
        reg = load_yaml(path)
    except yaml.YAMLError as e:
        _fail("登记表 %s 解析失败：%s" % (path, e))
    lines = reg.get("lines") if isinstance(reg, dict) else None
    if not isinstance(lines, dict) or not lines:
        _fail("登记表 %s 形状非法：缺 lines 映射" % path)
    for name, line in lines.items():
        if not isinstance(line, dict):
            _fail("登记表 lines.%s 形状非法：应为映射" % name)
        chain = line.get("chain")
        if not isinstance(chain, list) or not chain or \
                not all(isinstance(x, str) and x for x in chain):
            _fail("登记表 lines.%s.chain 非法：须为非空技能名列表" % name)
        if not isinstance(line.get("label"), str) or not line["label"].strip():
            _fail("登记表 lines.%s 缺 label" % name)
        if line.get("entry") != chain[0]:
            _fail("登记表 lines.%s.entry(%r) 必须是 chain 的第一个(%r)"
                  % (name, line.get("entry"), chain[0]))
        if "exec" not in line:
            _fail("登记表 lines.%s 缺 exec（无下游须显式写 null）" % name)
        if line["exec"] is None and \
                not (isinstance(line.get("exec_note"), str) and line["exec_note"].strip()):
            _fail("登记表 lines.%s 的 exec 为 null 时必须给 exec_note" % name)
        notes = line.get("notes", {}) or {}
        if not isinstance(notes, dict):
            _fail("登记表 lines.%s.notes 应为映射" % name)
        for k, v in notes.items():
            if not (isinstance(v, str) and v.strip()):
                _fail("登记表 lines.%s.notes.%s 须为非空字符串" % (name, k))
        paths = line.get("status_paths", {}) or {}
        if not isinstance(paths, dict):
            _fail("登记表 lines.%s.status_paths 应为映射" % name)
        for k, v in paths.items():
            if not (isinstance(v, list) and v and all(isinstance(x, str) and x for x in v)):
                _fail("登记表 lines.%s.status_paths.%s 须为非空字符串列表（如 [x-project, status]）"
                      % (name, k))
    return reg


def read_frontmatter(skill):  # trace: C·1 节点事实来自技能自声明（六字段封闭集）
    """读某技能 SKILL.md 的 frontmatter；help 只用其中两项：outputs / required。"""
    path = os.path.join(SKILLS_DIR, skill, "SKILL.md")
    if not os.path.isfile(path):
        _fail("技能 %s 未安装（缺 %s）" % (skill, path))
    try:
        with io.open(path, "r", encoding="utf-8") as f:
            raw = f.read()
    except (UnicodeDecodeError, OSError) as e:  # 声明面不可读即硬失败，不裸栈
        _fail("技能 %s 的 SKILL.md 不可读：%s" % (skill, e))
    m = re.match(r"^---[ \t]*\r?\n(.*?)\r?\n---[ \t]*\r?\n", raw, re.S)
    if not m:
        _fail("技能 %s 的 SKILL.md 无 frontmatter" % skill)
    try:
        fm = yaml.safe_load(m.group(1))
    except yaml.YAMLError as e:
        _fail("技能 %s 的 frontmatter 解析失败：%s" % (skill, e))
    if not isinstance(fm, dict):
        _fail("技能 %s 的 frontmatter 非映射" % skill)
    return fm


def chain_nodes(reg, line):  # trace: C·1 表（链序）+ frontmatter（产物/必做性）→ 扫描节点
    """组装某条线的扫描节点。节点只取引擎需要的三项，其余登记字段引擎不读。"""
    notes = reg["lines"][line].get("notes") or {}
    status_paths = reg["lines"][line].get("status_paths") or {}
    nodes = []
    for skill in reg["lines"][line]["chain"]:
        fm = read_frontmatter(skill)
        required = fm.get("required")
        if not isinstance(required, bool):
            _fail("技能 %s 的 frontmatter.required 须为布尔（六字段封闭集）" % skill)
        files = []
        for tok in str(fm.get("outputs") or "").split("+"):
            tok = tok.strip()
            if not tok:
                continue
            if not _OUTPUT_TOKEN_RE.match(tok):
                _fail("技能 %s 的 outputs 含非文件名片段 %r（链节点须为 `+` 分隔的裸文件名）"
                      % (skill, tok))
            files.append(tok)
        if not files:
            _fail("技能 %s 的 outputs 为空（链节点必须声明产物）" % skill)
        nodes.append({
            "skill": skill,
            "files": files,
            # 声明读不到时的回落顺序由 read_status 兜底；此处给的是**权威位置**
            # （如 openapi.yaml 的元数据在 x-project，见 diy-openapi/SKILL.md:19）
            "status_path": tuple(status_paths.get(skill, DEFAULT_STATUS_PATH)),
            "optional": not required,
            "note": notes.get(skill, ""),
        })
    return nodes


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
        # trace: F-A3b paths 为真值标量时 isinstance 守卫降级默认值（对齐 read_status 范式）
        paths = cfg.get("paths")
        if isinstance(paths, dict):
            output_dir = paths.get("output_dir", output_dir)
            if not isinstance(output_dir, str):  # trace: 对抗审查修复——output_dir 值非字符串降级
                sys.stderr.write("WARN diy-coder.yaml: output_dir 不是字符串，降级默认 diy-output\n")
                output_dir = "diy-output"
        elif paths is not None:
            sys.stderr.write("WARN diy-coder.yaml: paths 形状异常（应为映射），降级默认 %s\n"
                             % output_dir)
    if instance:
        if not INSTANCE_RE.fullmatch(instance):
            sys.stderr.write("非法实例名: %s（字母数字开头和结尾，中间可含 . _ -）\n" % instance)
            sys.exit(1)
        output_dir = os.path.join(output_dir, instance)
    return os.path.join(project_root, output_dir)


def read_status(path, status_path=DEFAULT_STATUS_PATH):  # trace: S-13 AC-13.1 TC-13.1.6 按节点声明路径读 status；语法/形状/半写降级 unparsable/unknown 而非崩溃
    """读产物 status；按声明路径读取，读不到时回落另一 meta 位置（project / x-project）。

    文件损坏或顶层非映射 → 'unparsable'；无有效 status → 'unknown'（None/空值归一）。
    """
    try:
        doc = load_yaml(path)
    except yaml.YAMLError as e:
        sys.stderr.write("WARN %s: %s\n" % (os.path.basename(path), e))
        return "unparsable"
    if not isinstance(doc, dict):
        sys.stderr.write("WARN %s: 顶层不是映射，按 unparsable 处理\n"
                         % os.path.basename(path))
        return "unparsable"
    probes = [tuple(status_path)]
    for alt in (("project", "status"), ("x-project", "status")):
        if alt not in probes:
            probes.append(alt)
    malformed = False
    for probe in probes:  # trace: F-A1 声明路径读不到 → 回落姊妹 meta 位置
        node = doc
        broken = False
        for i, key in enumerate(probe):
            if not isinstance(node, dict):
                # trace: 对抗审查修复——中段键值是标量（如 project: 3）判形状异常，
                # 不再静默回落 unknown（真 shape 错应可见为 unparsable）
                broken = i > 0 and node is not None and node != ""
                node = None
                break
            node = node.get(key)
        if broken:
            malformed = True
            continue
        if isinstance(node, (dict, list)):  # trace: F-A3c status 值形状异常（容器）
            malformed = True
            continue
        if node is not None and node != "":
            return node
    if malformed:
        sys.stderr.write("WARN %s: status 值形状异常，按 unparsable 处理\n"
                         % os.path.basename(path))
        return "unparsable"
    return "unknown"


def scan_chain(output_dir, chain):  # trace: S-13 AC-13.1 TC-13.1.1 TC-13.1.2 存在性+status 扫链定位置/推荐
    """返回 (completed_skills, next_skill, blocked, notes)。chain = 该线的扫描节点列表。"""
    completed, notes = [], []
    for node in chain:
        skill, files = node["skill"], node["files"]
        exists = [f for f in files if os.path.isfile(os.path.join(output_dir, f))]
        if not exists:
            if node.get("optional"):
                notes.append(node["note"])
                continue
            return completed, skill, None, notes
        if len(exists) != len(files):  # trace: F-A3a 多文件节点半写（声明文件只落一部分）按未开始处理
            return completed, skill, None, notes
        status_path = node.get("status_path", DEFAULT_STATUS_PATH)
        statuses = {f: read_status(os.path.join(output_dir, f), status_path) for f in exists}
        unfinal = {f: s for f, s in statuses.items() if s != "已定稿"}
        if unfinal:
            f, s = sorted(unfinal.items())[0]
            if s in ("unparsable", "unknown"):  # trace: F-A3c 半写/损坏与写作中分流，动作按 status 值分支
                action = "修复 %s 后重跑（半写或损坏，无法读出有效 status）" % f
            else:
                action = "继续 %s 直至 %s 定稿（status: 已定稿）" % (skill, f)
            return completed, None, {"file": f, "status": s, "action": action}, notes
        completed.append(skill)
    return completed, None, None, notes


def scan_sprint(output_dir, exec_skill, queue_file):  # trace: S-13 AC-13.1 TC-13.1.6 链后读 sprint 任务；tasks 形状异常降级阻断
    """链走完后读任务队列。返回 (next_skill, blocked, workflow_done)。

    `queue_file` 由链末节点的 `outputs` 给出（不硬编码产物名）。
    """
    path = os.path.join(output_dir, queue_file)
    if not os.path.isfile(path):  # 链扫已判其「已定稿」，此刻不在=声明与实物不一致
        _fail("任务队列 %s 不在（链已判其已定稿）——登记表与产物不一致" % queue_file)
    sprint = load_yaml(path)
    tasks = sprint.get("tasks")
    # trace: F-A3d tasks 为空列表与 null 同判阻断（空 sprint 不是可执行链）
    if not isinstance(tasks, list) or not tasks or not all(isinstance(t, dict) for t in tasks):
        blocked = {
            "file": queue_file,
            "status": "unparsable",
            "action": "%s 的 tasks 为空或损坏（半写），修复后重跑" % queue_file,
        }
        return None, blocked, False
    blocked_tasks = [t for t in tasks if t.get("status") == "已阻塞"]
    if blocked_tasks:
        names = ", ".join(str(t.get("story", "?")) for t in blocked_tasks)
        blocked = {
            "file": queue_file,
            "status": "已阻塞",
            "action": "人工解除阻塞任务（%s）的 blocked_reason 后重跑" % names,
        }
        return None, blocked, False
    if all(t.get("status") == "已完成" for t in tasks):
        return None, None, True
    return exec_skill, None, False  # 该线登记表声明的执行技能（主线 = diy-build-loop）


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
            lines.append("下一步：工作流已全部完成。可选收尾：证伪轮（diy-review --falsify all）、bug-log 经验入库。")
        if result.get("branches"):
            lines.append("分叉：%s" % "；".join(
                "%s → %s" % (b["label"], b["entry"]) for b in result["branches"]))
        for n in result["notes"]:
            lines.append("提示：%s" % n)
    return "\n".join(lines)


def main():  # trace: S-13 AC-13.1 TC-13.1.1 组装位置/推荐/阻塞（零起点→该线入口 + 分叉候选）
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="diy-coder 工作流状态机导航")
    ap.add_argument("--project-root", default=".", help="项目根目录")
    ap.add_argument("--instance", default=None, help="实例名（FR-4.5/D-9）")
    ap.add_argument("--line", default=None, help="强制指定当前线（登记表 lines 的键）")
    ap.add_argument("--json", action="store_true", help="机器可读 JSON 输出")
    args = ap.parse_args()

    reg = load_registry()
    lines_meta = reg["lines"]
    if args.line is not None and args.line not in lines_meta:
        _fail("未知的线 %r（登记表只有：%s）" % (args.line, "、".join(sorted(lines_meta))))
    chains = {name: chain_nodes(reg, name) for name in lines_meta}
    branches = [{"line": n, "label": lines_meta[n]["label"], "entry": lines_meta[n]["entry"]}
                for n in lines_meta]

    output_dir = resolve_output_dir(args.project_root, args.instance)
    started = [n for n in lines_meta if any(
        os.path.isfile(os.path.join(output_dir, f))
        for node in chains[n] for f in node["files"])]

    if not started:  # 零起点：无任何产物 → 给各线入口供按用途分叉
        line_name = args.line or ("mainline" if "mainline" in lines_meta else sorted(lines_meta)[0])
        result = {
            "position": "零起点",
            "line": None,
            "branches": branches,
            "output_dir": output_dir,
            "completed_steps": [],
            "next_skill": lines_meta[line_name]["entry"],
            "blocked": None,
            "notes": [],
            "workflow_done": False,
        }
    else:
        extra_notes = []
        if args.line:
            line_name = args.line
        elif len(started) == 1:
            line_name = started[0]
        else:  # 双线并存：本技能不自动合并，由用户选定（--line）
            line_name = "mainline" if "mainline" in started else sorted(started)[0]
            extra_notes.append(
                "两条线的产物并存（%s）——本技能不自动合并；请用户选定当前工作线后"
                "用 --line <线名> 重跑" % "、".join(lines_meta[n]["label"] for n in started))
        meta, chain = lines_meta[line_name], chains[line_name]
        completed, next_skill, blocked, notes = scan_chain(output_dir, chain)
        notes = notes + extra_notes
        workflow_done = False
        if not next_skill and not blocked:
            if meta["exec"]:
                # 任务队列名取链末节点的 outputs（不硬编码产物名）
                next_skill, blocked, workflow_done = scan_sprint(
                    output_dir, meta["exec"], chain[-1]["files"][0])
            else:  # 本线下游未登记（exec: null）——如实说明，不假报完成
                next_skill = None
                notes.append(meta["exec_note"])
        if blocked:
            position = "阻塞于 %s" % blocked["file"]
        elif workflow_done:
            position = "工作流完成"
        elif meta["exec"] and next_skill == meta["exec"]:
            position = "执行阶段"
        elif next_skill:
            step = next(i + 1 for i, n in enumerate(chain) if n["skill"] == next_skill)
            position = ("第 %d/%d 步：%s" % (step, len(chain), next_skill)
                        if line_name == "mainline" else
                        "%s 第 %d/%d 步：%s" % (meta["label"], step, len(chain), next_skill))
        else:  # 链已走完且本线下游未登记
            position = ("%s——下游待登记" % meta["label"] if line_name != "mainline"
                        else "下游待登记")
        result = {
            "position": position,
            "line": line_name,
            "branches": branches if len(started) > 1 else None,
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
