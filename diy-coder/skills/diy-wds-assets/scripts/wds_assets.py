#!/usr/bin/env python3
"""diy-wds-assets 领域引擎（B7b / W2）。

子命令：init（唯一写盘）/ list / show / check / prompts。
- 全部子命令收 `--project-root`（默认 `.`）；`--output-dir` 缺省回落 `{project_root}/diy-output`
  （写盘子命令 `init` 必填）；只读子命令四个（list / show / check / prompts）零写盘。
- **`--instance` 一律不做**（键恒 `null` 在位）。
- 回执共同键：{ok, command, project_root, output_dir, instance, violations, warnings, counts}
  —— `warnings` 与 `violations` 同形；`init` 另含 `updated`，只读子命令不含。
  `project_root` 按 as-given 回显（不 resolve），`output_dir` 为 resolved + 正斜杠；
  违规项 schema = `{code, where, msg}`（`where` 正斜杠、路径型相对 project-root）。

★ **第五子命令 `prompts` 是对 §2.2「四子命令」的一处登记性偏离**（V3-12）：
  任务书 §3 要求「提示词导出索引」独立成面——`prompts[]` 的 `exported` 翻转与导出文件是
  本技能**照片类资产通道 + 用户可选项**（裁定 6：不接任何外部服务；其余产物由各活动直出），
  而 §2.2 冻结「四子命令」（init / list / show / check）——两条并存的最小满足 = 加一个
  **只读、零写盘**的第五子命令。
  先例：B7a 的 `diy-wds-trigger` 亦在四子命令之外加了 `metrics`；本批 `diy-wds-system`
  同款加 `similarity`。**不写盘**。
- 退出码：0 放行 / 1 违规 / 2 用法错误。
- 违规码：**复用冻结集**（MISSING_FILE / UNPARSABLE_YAML / DUPLICATE_ID / UNKNOWN_ID /
  EMPTY_FIELD / ENUM_INVALID / STATUS_MISMATCH / SET_MISMATCH / ASSUMPTION_PRESENT）
  + B6 已批码 TOKEN_UNRESOLVED。**本批不新增码**。
- 写范围：`{output_dir}/wds-assets.yaml`（唯一写盘面）；
  `{output_dir}/assets/<活动>/` 下的产物由会话写（裁定 12），本引擎只校验其路径引用。
- 跨技能机械核（任务书 §2.3.1 的**必读键** `scenarios[].pages[].id`）：`items[].pages[]` 逐条
  核形态 `SC-<nn>.P<n>`（不合 → `SET_MISMATCH`）并解析到上游 `wds-scenarios.yaml` 的页面清单
  （解析不到 → `UNKNOWN_ID`）；`check` 与 `init` **同门禁**（上游缺席 / 未定稿 → 停止）。
- 文档化陷阱：产物是 WDS 型，**不得**改用 `diyc.py check --type`（主线 8 型封闭集）。
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    print("需要 PyYAML：pip install pyyaml", file=sys.stderr)
    raise SystemExit(2)

PRODUCT = "wds-assets.yaml"
UPSTREAM = "wds-scenarios.yaml"
DESIGN_SYSTEM = "wds-design-system.yaml"

# (活动 ID, 码, 中文名, 资产子目录)
ACTIVITIES = [
    ("AS-01", "W", "线框", "wireframes"),
    ("AS-02", "P", "页面稿", "page-designs"),
    ("AS-03", "U", "UI 件", "ui-elements"),
    ("AS-04", "I", "图标", "icons"),
    ("AS-05", "M", "图片", "images"),
    ("AS-06", "V", "动效", "motion"),
    ("AS-07", "C", "文案", "content"),
    ("AS-08", "S", "演示", "presentation"),
]
DIR_OF = {row[0]: row[3] for row in ACTIVITIES}

STAGES = ["线框", "页面稿", "UI件", "图标", "图片", "动效", "文案", "演示", "收尾"]
ACTIVITY_STATUS = ["未开始", "进行中", "已评审", "已跳过"]
TERMINAL_STATUS = ["已评审", "已跳过"]
VERDICTS = ["通过", "重生", "待定"]
SCOPES = ["all", "select", "missing", "priority", "category", "batch", "type"]
PROJECT_STATUS = ["草稿", "已定稿"]
STATES = ["default", "hover", "focus", "active", "disabled"]
RECIPES = {
    "SD": "sd-slides.md",
    "EX": "ex-explainer.md",
    "PD": "pd-pitch.md",
    "CT": "ct-talk.md",
    "IN": "in-infographic.md",
    "VM": "vm-concept-illustration.md",
    "CV": "cv-concept-visual.md",
}
FRAME_JOBS = ["inform", "persuade", "transition"]
PRINCIPLE_COUNT = 8
PRESENTATION_ACTIVITY = "AS-08"     # 第 9 活动：presentation[] 的 ID 空间（裁定 10）
# AS-07 文案条目的六段（键名逐字取 `steps/07-content.md:10` 自己的声明，裁定 17 c）
CONTENT_ACTIVITY = "AS-07"
CONTENT_KEYS = (
    "content_purpose", "trigger_map_context", "awareness_strategy",
    "action_filter", "empowerment_frame", "structural_order",
)
ITEM_ID_RE = re.compile(r"^AS-(\d{2})\.(\d{1,3})$")
PAGE_ID_RE = re.compile(r"^SC-\d{2}\.P\d+$")
TOKEN_RE = re.compile(r"\{([^{}\n]+)\}")
SKILL_DIR = Path(__file__).resolve().parent.parent
# 模板位清单的提取口径（裁定 16 ③；C·11 V-A F-1 扩面到全部模板）：
# 逐模板按各自结构取「要填的位」——两模板的骨架与注记结构不同：
# · prompt-export：骨架在围栏代码块内；围栏外说明段含 `{output_dir}` 路径写法（:92），非模板位
# · content-output：文件本身即骨架（活文档），正文位在围栏外；`>` 引用注记（含 `{output_dir}` / `{…}`）非模板位
TEMPLATE_SPECS = (
    ("prompt-export.template.md", "fenced"),
    ("content-output.template.md", "noquote"),
)


class Report:
    """违规 / 警告的收集器（两者同形）。

    `root_given` = `--project-root` 的 as-given 原值（契约 §3：回执按原样回显，**不 resolve**）；
    内部文件操作用 `project_root`（resolved），两者分工见 `main()`。
    """

    def __init__(self, command: str, project_root: Path, output_dir: Path, root_given=None):
        self.command = command
        self.project_root = project_root
        self.output_dir = output_dir
        self.root_given = str(project_root) if root_given is None else str(root_given)
        self.violations: list[dict] = []
        self.warnings: list[dict] = []
        self.counts: dict = {}
        self.extra: dict = {}

    def add(self, code, where, msg, bucket="violations"):
        # `where` 在此再归一一次反斜杠（契约 §3：统一正斜杠）——双保险，构造点不必各写一遍
        getattr(self, bucket).append(
            {"code": code, "where": str(where).replace("\\", "/"), "msg": msg}
        )

    def bad(self, code, where, msg):
        self.add(code, where, msg)

    def warn(self, code, where, msg):
        self.add(code, where, msg, bucket="warnings")

    def receipt(self, ok=None):
        if ok is None:
            ok = not self.violations
        payload = {
            "ok": ok,
            "command": self.command,
            "project_root": self.root_given,
            "output_dir": self.output_dir.as_posix(),
            "instance": None,
            "violations": self.violations,
            "warnings": self.warnings,
            "counts": self.counts,
        }
        payload.update(self.extra)
        return payload

    def exit_code(self):
        return 0 if not self.violations else 1


def display_path(path: Path, project_root: Path) -> str:
    """相对 project-root、正斜杠（契约 §3 的 `where` 口径）；越界则绝对路径。"""
    try:
        return path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def nonempty(value) -> bool:
    """非空判定（对齐 `wds_brief.nonempty`）：None / 空白串 / 空容器均视为空。"""
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() != ""
    if isinstance(value, (list, dict, tuple)):
        return len(value) > 0
    return True


def path_in(path: str, prefix: str) -> bool:
    """路径包含性判据（VA-07）：**拒绝含 `..` 段的形态**。

    裸 `startswith` 可被 `assets/wireframes/../../outside.html` 逃逸（实测 rc=0）；
    拒绝比 normpath 更严，且与回执文案「须落 <prefix> 内」的声明一致。
    """
    if ".." in path.replace("\\", "/").split("/"):
        return False
    return path.startswith(prefix)


def load_yaml(path: Path, report: Report, bucket="violations", label=None):
    if not path.exists():
        report.add("MISSING_FILE", display_path(path, report.project_root),
                   f"{label or path.name} 不存在", bucket)
        return None
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        report.add("UNPARSABLE_YAML", display_path(path, report.project_root),
                   f"YAML 解析失败：{exc}", bucket)
        return None
    if not isinstance(doc, dict):
        report.add("UNPARSABLE_YAML", display_path(path, report.project_root),
                   "顶层不是映射", bucket)
        return None
    return doc


def save_yaml_atomic(path: Path, doc):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        yaml.safe_dump(doc, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    tmp.replace(path)


def project_name(project_root: Path) -> str:
    cfg = project_root / "diy-coder.yaml"
    if cfg.exists():
        try:
            doc = yaml.safe_load(cfg.read_text(encoding="utf-8")) or {}
            name = (doc.get("project") or {}).get("name")
            if name:
                return str(name)
        except yaml.YAMLError:
            pass
    return project_root.resolve().name


def today() -> str:
    return _dt.date.today().isoformat()


def skeleton(project_root: Path) -> dict:
    now = today()
    return {
        "project": {"name": project_name(project_root), "created": now, "updated": now, "status": "草稿"},
        "stage": STAGES[0],
        "activities": [
            {
                "id": aid,
                "code": code,
                "name": name,
                "status": "未开始",
                "scope": None,
                "style": {"design": None, "content": None, "format": None},
                "items": [],
            }
            for aid, code, name, _dir in ACTIVITIES
        ],
        "prompts": [],
        "presentation": [],
        "revisions": [],
    }


def gate_upstream(report: Report, output_dir: Path):
    """跨技能门禁：wds-scenarios.yaml 存在且 `project.status: 已定稿`。"""
    upstream = load_yaml(output_dir / UPSTREAM, report, label="上游 wds-scenarios.yaml")
    if upstream is None:
        return None
    if (upstream.get("project") or {}).get("status") != "已定稿":
        report.bad("STATUS_MISMATCH", display_path(output_dir / UPSTREAM, report.project_root),
                   "上游 project.status 不是 已定稿")
        return None
    return upstream


def page_ids(upstream: dict) -> set:
    """上游 `scenarios[].pages[].id` 的页面 ID 全集（§2.3.1 的必读键）。"""
    ids = set()
    for scenario in upstream.get("scenarios") or []:
        if not isinstance(scenario, dict):
            continue
        for page in scenario.get("pages") or []:
            if isinstance(page, dict) and page.get("id"):
                ids.add(page["id"])
    return ids


def coverage_report(doc: dict, pages: set) -> dict:
    """覆盖差集（V2-02，形状逐字取 `steps/09-finish.md:23-25`）。

    `unassigned` = 上游页清单里未被任何 `items[].pages[]` 引用的页；
    `orphan` = 引用到上游不存在的页（**与 V2-01 的 `UNKNOWN_ID` 同源判定**：形态合法才入门）。
    两列都为空也须在场（否则模型取不到键）。
    """
    refs = []
    for act in doc.get("activities") or []:
        for item in (act or {}).get("items") or []:
            refs.extend(pid for pid in (item or {}).get("pages") or [] if isinstance(pid, str))
    used = set(refs)
    return {
        "unassigned": sorted(pages - used),
        "orphan": sorted(pid for pid in used - pages if PAGE_ID_RE.match(pid)),
    }


def read_design_system(report: Report, output_dir: Path):
    path = output_dir / DESIGN_SYSTEM
    if not path.exists():
        report.warn("MISSING_FILE", display_path(path, report.project_root),
                    "可选上游 wds-design-system.yaml 缺席（引擎不做令牌一致性校验——"
                    "在场时由会话按 steps/09-finish.md 第 1 步「令牌同源」逐条对表）")
        return None
    doc = load_yaml(path, report, bucket="warnings", label="可选上游 wds-design-system.yaml")
    return doc


def template_slots(report: Report) -> set:
    """模板位清单（裁定 16 ③；C·11 V-A F-1 扩面）：解析 `templates/` 下各模板「要填的位」`{...}`。

    **解析提取、不硬编码**——模板改动后违规判据随之变（这层耦合约已登记，见回报）。
    逐模板按结构取口径（见 `TEMPLATE_SPECS` 注释）：`prompt-export` 只取**围栏代码块**内；
    `content-output` 取全文、排除 `>` 引用注记。两处排除都为了「`{output_dir}` 天然放行」成立。
    """
    slots: set[str] = set()
    for name, mode in TEMPLATE_SPECS:
        path = SKILL_DIR / "templates" / name
        if not path.exists():
            report.warn("MISSING_FILE", display_path(path, report.project_root),
                        f"模板 {name} 缺席：其模板位不计入清单，占位符残留核对其停用")
            continue
        fenced = False
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.lstrip().startswith("```"):
                fenced = not fenced
                continue
            if mode == "fenced" and not fenced:
                continue
            if mode == "noquote" and line.lstrip().startswith(">"):
                continue
            slots.update(TOKEN_RE.findall(line))
    return slots


def scan_raw_tokens(text: str, report: Report, path: Path):
    """占位符残留核（裁定 16 ③）：`{...}` **∈ 模板位清单 → 违规**（说明该位没被填掉）。

    判据方向与旧版相反：旧的「∉ 白名单（2 token）→ 违规」把无差别正则当成了「模板位填没填」
    的判据，于是 prompt 里合法的 JSON 示例（`{"breakpoint": "1440"}`）被误杀。改判后
    模型自创的模板外占位符抓不到（已知漏检面，用户已知悉并接受）。
    """
    slots = template_slots(report)
    shown = display_path(path, report.project_root)
    for line_no, line in enumerate(text.splitlines(), start=1):
        for token in TOKEN_RE.findall(line):
            if token in slots:
                report.bad("TOKEN_UNRESOLVED", f"{shown} line {line_no}",
                           f"占位符未填：{{{token}}} 是模板骨架的模板位，原样残留（填掉或删除该行）")


# --------------------------------------------------------------------- init


def cmd_init(args, report: Report):
    output_dir = Path(args.output_dir).resolve()
    if gate_upstream(report, output_dir) is None:
        report.counts = {"activities": 0, "items": 0, "written": False, "has_design_system": False}
        report.extra["updated"] = False
        return report.exit_code()
    ds = read_design_system(report, output_dir)

    path = output_dir / PRODUCT
    if path.exists():
        existing = load_yaml(path, report)
        if existing is None:
            report.extra["updated"] = False
            return report.exit_code()
        report.counts = summarize(existing)
        report.counts["written"] = False
        report.counts["has_design_system"] = ds is not None
        report.extra["updated"] = False
        return report.exit_code()

    doc = skeleton(Path(args.project_root).resolve())
    save_yaml_atomic(path, doc)
    report.counts = summarize(doc)
    report.counts["written"] = True
    report.counts["has_design_system"] = ds is not None
    report.extra["updated"] = True
    return report.exit_code()


# --------------------------------------------------------------- summarize


def summarize(doc: dict) -> dict:
    activities = doc.get("activities") or []
    items = [it for act in activities for it in (act.get("items") or [])]
    prompts = doc.get("prompts") or []
    return {
        "activities": len(activities),
        "items": len(items),
        "prompts": len(prompts),
        "exported": len([p for p in prompts if p.get("exported")]),
        "presentation": len(doc.get("presentation") or []),
        "skipped": len([a for a in activities if a.get("status") == "已跳过"]),
    }


# --------------------------------------------------------------------- list


def cmd_list(args, report: Report):
    output_dir = Path(args.output_dir).resolve()
    doc = load_yaml(output_dir / PRODUCT, report)
    if doc is None:
        return report.exit_code()
    wanted = getattr(args, "status", None)
    if wanted and wanted not in ACTIVITY_STATUS:
        report.bad("ENUM_INVALID", "--status", f"非法活动状态：{wanted}")
        return report.exit_code()
    rows = []
    for act in doc.get("activities") or []:
        if wanted and act.get("status") != wanted:
            continue
        exported = len(
            [
                p
                for p in (doc.get("prompts") or [])
                if p.get("activity") == act.get("id") and p.get("exported")
            ]
        )
        rows.append(
            {
                "id": act.get("id"),
                "code": act.get("code"),
                "name": act.get("name"),
                "status": act.get("status"),
                "items": len(act.get("items") or []),
                "exported": exported,
            }
        )
    report.extra["activities"] = rows
    report.counts = summarize(doc)
    report.counts["listed"] = len(rows)
    return report.exit_code()


# --------------------------------------------------------------------- show


def find_record(doc: dict, ident: str):
    """按 ID 找记录：活动 / 条目 / 演示记录 / 提示词条目——**与 `check` 同一 ID 空间**（裁定 9）。"""
    for act in doc.get("activities") or []:
        if act.get("id") == ident:
            return act
        for item in act.get("items") or []:
            if item.get("id") == ident:
                return item
    for key in ("presentation", "prompts"):
        for entry in doc.get(key) or []:
            if (entry or {}).get("id") == ident:
                return entry
    return None


def cmd_show(args, report: Report):
    output_dir = Path(args.output_dir).resolve()
    doc = load_yaml(output_dir / PRODUCT, report)
    if doc is None:
        return report.exit_code()
    ident = getattr(args, "id", None)
    if not ident:
        report.extra["doc"] = doc
        report.counts = summarize(doc)
        return report.exit_code()
    record = find_record(doc, ident)
    if record is None:
        report.bad("UNKNOWN_ID", ident, f"产物里没有 {ident}")
        return report.exit_code()
    report.extra["record"] = record
    report.counts = summarize(doc)
    return report.exit_code()


# ------------------------------------------------------------------- prompts


def cmd_prompts(args, report: Report):
    output_dir = Path(args.output_dir).resolve()
    doc = load_yaml(output_dir / PRODUCT, report)
    if doc is None:
        return report.exit_code()
    wanted = getattr(args, "activity", None)
    if wanted and wanted not in DIR_OF:
        report.bad("ENUM_INVALID", "--activity", f"非法活动 ID：{wanted}")
        return report.exit_code()
    rows = [p for p in (doc.get("prompts") or []) if not wanted or p.get("activity") == wanted]
    report.extra["prompts"] = rows
    report.counts = summarize(doc)
    report.counts["listed"] = len(rows)
    return report.exit_code()


# --------------------------------------------------------------------- check


def check_activities(doc, report: Report, pages: set):
    activities = doc.get("activities")
    if not isinstance(activities, list) or len(activities) != len(ACTIVITIES):
        report.bad(
            "SET_MISMATCH",
            "activities",
            f"活动数应为 {len(ACTIVITIES)}（源 8 活动去掉已裁的 [E] + 第 9 活动），实为 "
            f"{len(activities) if isinstance(activities, list) else '非列表'}",
        )
        activities = activities if isinstance(activities, list) else []
    seen_ids: set[str] = set()
    for index, act in enumerate(activities):
        where = f"activities[{index}]"
        want = ACTIVITIES[index] if index < len(ACTIVITIES) else None
        if want and act.get("id") != want[0]:
            report.bad("SET_MISMATCH", where, f"活动 ID 应为 {want[0]}，实为 {act.get('id')}")
        if want and act.get("code") != want[1]:
            report.bad("SET_MISMATCH", where, f"活动码应为 {want[1]}，实为 {act.get('code')}")
        if act.get("status") not in ACTIVITY_STATUS:
            report.bad("ENUM_INVALID", where, f"非法活动状态：{act.get('status')}")
        scope = act.get("scope")
        if scope is not None and scope not in SCOPES:
            report.bad("ENUM_INVALID", where, f"非法范围取值：{scope}")
        items = act.get("items")
        if items is None:
            items = []
        if not isinstance(items, list):
            report.bad("EMPTY_FIELD", where, "items 不是列表")
            continue
        sequence: list[tuple[str, int]] = []
        for j, item in enumerate(items):
            iwhere = f"{where}.items[{j}]"
            ident = str(item.get("id") or "")
            match = ITEM_ID_RE.match(ident)
            if not match:
                report.bad("SET_MISMATCH", iwhere, f"条目 ID 形态不合 AS-<nn>.<m>：{ident!r}")
            elif f"AS-{match.group(1)}" != act.get("id"):
                report.bad("SET_MISMATCH", iwhere, f"条目 ID {ident} 与父活动 {act.get('id')} 不同源")
            else:
                # 只收形态合法且与父活动同源的 id（裁定 1）：非法形态已判过，不级联刷屏
                sequence.append((ident, int(match.group(2))))
            if ident in seen_ids:
                report.bad("DUPLICATE_ID", iwhere, f"条目 ID 重复：{ident}")
            seen_ids.add(ident)
            for key in ("name", "spec", "prompt"):
                value = item.get(key)
                if value is None or (isinstance(value, str) and not value.strip()):
                    report.bad("EMPTY_FIELD", iwhere, f"{key} 不可空")
            item_pages = item.get("pages")
            if not item_pages:
                report.bad("EMPTY_FIELD", iwhere, "pages 不可空")
            elif not isinstance(item_pages, list):
                report.bad("SET_MISMATCH", iwhere, "pages 不是列表")
            else:
                # 上游硬契约，不许编造：形态 + 解析到 wds-scenarios.yaml 的页面清单
                for k, pid in enumerate(item_pages):
                    pwhere = f"{iwhere}.pages[{k}]"
                    if not (isinstance(pid, str) and PAGE_ID_RE.match(pid)):
                        report.bad("SET_MISMATCH", pwhere,
                                   f"页面引用须为 SC-<nn>.P<n> 形态，实测 {pid!r}")
                    elif pid not in pages:
                        report.bad("UNKNOWN_ID", pwhere,
                                   f"{pid} 不在 wds-scenarios.yaml 的页面清单里")
            if item.get("prompt_lang") not in (None, "en", "zh"):
                report.bad("ENUM_INVALID", iwhere, f"非法 prompt_lang：{item.get('prompt_lang')}")
            if act.get("code") == "U" and item.get("state"):
                for state in item["state"]:
                    if state not in STATES:
                        report.bad("ENUM_INVALID", iwhere, f"非法态：{state}")
            for k, asset in enumerate(item.get("assets") or []):
                aw = f"{iwhere}.assets[{k}]"
                path = str((asset or {}).get("path") or "")
                if not path:
                    report.bad("EMPTY_FIELD", aw, "path 不可空")
                    continue
                prefix = f"assets/{DIR_OF[act.get('id')]}/" if act.get("id") in DIR_OF else "assets/"
                if not path_in(path, prefix):
                    report.bad("SET_MISMATCH", aw, f"资产路径须落 {prefix} 内，实为 {path}")
            verdict = ((item.get("review") or {}).get("verdict"))
            if verdict is not None and verdict not in VERDICTS:
                report.bad("ENUM_INVALID", iwhere, f"非法评审结论：{verdict}")
        numbers = [n for _ident, n in sequence]
        if numbers != list(range(1, len(numbers) + 1)):
            report.bad(
                "SET_MISMATCH",
                where,
                "活动内条目序号须从 1 起连续递增（" + f"{act.get('id')}.1 / {act.get('id')}.2 …），实为 "
                + " / ".join(ident for ident, _n in sequence),
            )
    return seen_ids


def check_prompts(doc, report: Report, item_ids: set[str], final: bool):
    prompts = doc.get("prompts")
    if prompts is None:
        prompts = []
    if not isinstance(prompts, list):
        report.bad("EMPTY_FIELD", "prompts", "prompts 不是列表")
        return
    for i, entry in enumerate(prompts):
        where = f"prompts[{i}]"
        ident = str((entry or {}).get("id") or "")
        if ident not in item_ids:
            report.bad("SET_MISMATCH", where, f"提示词条目 {ident!r} 无来源条目")
        activity = (entry or {}).get("activity")
        if activity not in DIR_OF:
            report.bad("ENUM_INVALID", where, f"非法活动 ID：{activity}")
            continue
        path = str((entry or {}).get("file") or "")
        prefix = f"assets/{DIR_OF[activity]}/prompts/"
        if not path_in(path, prefix):
            report.bad("SET_MISMATCH", where, f"提示词文件须落 {prefix} 内，实为 {path}")
        if not (entry or {}).get("target"):
            report.bad("EMPTY_FIELD", where, "target 不可空（导出通道要写清收件人）")
        if final and not (entry or {}).get("exported"):
            report.bad("SET_MISMATCH", where, "已定稿要求全部提示词已导出（exported: true）")


def check_presentation(doc, report: Report, final: bool):
    records = doc.get("presentation")
    if records is None:
        records = []
    if not isinstance(records, list):
        report.bad("EMPTY_FIELD", "presentation", "presentation 不是列表")
        return
    seen_ids: set[str] = set()
    for i, rec in enumerate(records):
        where = f"presentation[{i}]"
        ident = str((rec or {}).get("id") or "")
        match = ITEM_ID_RE.match(ident)
        if not match or f"AS-{match.group(1)}" != PRESENTATION_ACTIVITY:
            report.bad("SET_MISMATCH", where,
                       f"演示记录 ID 须为 {PRESENTATION_ACTIVITY}.<m>，实为 {ident!r}")
        elif ident in seen_ids:
            report.bad("SET_MISMATCH", where, f"演示记录 ID 重复：{ident}")
        else:
            seen_ids.add(ident)
        recipe = (rec or {}).get("recipe")
        if recipe not in RECIPES:
            report.bad("ENUM_INVALID", where, f"非法 recipe：{recipe}（七值封闭集）")
        card = str((rec or {}).get("format_card") or "")
        if not card.startswith("data/presentation-formats/"):
            report.bad("SET_MISMATCH", where, f"format_card 须指到配方卡目录，实为 {card}")
        frames = (rec or {}).get("frames")
        if not frames:
            report.bad("EMPTY_FIELD", where, "frames 不可空（共享骨架的产物形态）")
        else:
            for k, frame in enumerate(frames):
                fw = f"{where}.frames[{k}]"
                for key in ("n", "job", "headline"):
                    if (frame or {}).get(key) in (None, ""):
                        report.bad("EMPTY_FIELD", fw, f"{key} 不可空")
                if (frame or {}).get("job") not in FRAME_JOBS:
                    report.bad("ENUM_INVALID", fw, f"非法帧职责：{(frame or {}).get('job')}")
        for k, asset in enumerate((rec or {}).get("assets") or []):
            aw = f"{where}.assets[{k}]"
            path = str((asset or {}).get("path") or "")
            if not path_in(path, "assets/presentation/"):
                report.bad("SET_MISMATCH", aw, f"演示产物须落 assets/presentation/ 内，实为 {path}")
        principles = ((rec or {}).get("review") or {}).get("principles")
        if not principles or len(principles) != PRINCIPLE_COUNT:
            report.bad(
                "SET_MISMATCH",
                where,
                f"8 原则须逐条给结论（实为 {len(principles) if principles else 0} 条）",
            )
        verdict = ((rec or {}).get("review") or {}).get("verdict")
        if verdict is not None and verdict not in VERDICTS:
            report.bad("ENUM_INVALID", where, f"非法评审结论：{verdict}")


def cmd_check(args, report: Report):
    output_dir = Path(args.output_dir).resolve()
    path = output_dir / PRODUCT
    doc = load_yaml(path, report)
    if doc is None:
        return report.exit_code()
    # 与 init 同门禁（§2.3.1）：上游缺席 / 未定稿 → 停止（页面 ID 无从解析）
    upstream = gate_upstream(report, output_dir)
    if upstream is None:
        return report.exit_code()
    final = bool(getattr(args, "final", False))

    text = path.read_text(encoding="utf-8")
    if "[假设]" in text:
        report.bad("ASSUMPTION_PRESENT", display_path(path, report.project_root), "产物含未决标记 [假设]")
    scan_raw_tokens(text, report, path)

    project = doc.get("project") or {}
    if project.get("status") not in PROJECT_STATUS:
        report.bad("ENUM_INVALID", "project.status", f"非法状态：{project.get('status')}")
    if doc.get("stage") not in STAGES:
        report.bad("ENUM_INVALID", "stage", f"非法阶段：{doc.get('stage')}")

    pages = page_ids(upstream)
    item_ids = check_activities(doc, report, pages)
    # 覆盖差集（V2-02）：形状逐字取 `steps/09-finish.md:23-25`，与 V2-01 的页面解析同源
    report.extra["coverage"] = coverage_report(doc, pages)
    check_prompts(doc, report, item_ids, final)
    check_presentation(doc, report, final)

    activities = doc.get("activities") or []
    for index, act in enumerate(activities):
        status = act.get("status")
        if final:
            if status not in TERMINAL_STATUS:
                report.bad(
                    "STATUS_MISMATCH",
                    f"activities[{index}]",
                    f"已定稿要求活动为 已评审 或 已跳过，实为 {status}",
                )
                continue
            if status == "已跳过":
                continue
            items = act.get("items") or []
            if not items:
                report.bad("EMPTY_FIELD", f"activities[{index}]", "非跳过的活动必须至少有一条资产")
            for j, item in enumerate(items):
                iwhere = f"activities[{index}].items[{j}]"
                verdict = (item.get("review") or {}).get("verdict")
                if verdict != "通过":
                    report.bad(
                        "SET_MISMATCH",
                        iwhere,
                        f"已定稿要求评审结论为 通过，实为 {verdict}",
                    )
                if act.get("id") == CONTENT_ACTIVITY:
                    # VA-03c（裁定 17 c）：`steps/07-content.md:10` 声称「引擎核六段在场与键齐」
                    content = item.get("content") if isinstance(item.get("content"), dict) else {}
                    missing = [key for key in CONTENT_KEYS if not nonempty(content.get(key))]
                    if missing:
                        report.bad("EMPTY_FIELD", f"{iwhere}.content",
                                   f"AS-07 文案条目须落六段，缺：{' / '.join(missing)}")

    if final:
        if project.get("status") != "已定稿":
            report.bad("STATUS_MISMATCH", "project.status", "未落 已定稿")
        if doc.get("stage") != STAGES[-1]:
            report.bad("STATUS_MISMATCH", "stage", f"已定稿要求 stage: {STAGES[-1]}")
        eighth = activities[7] if len(activities) > 7 else {}
        if eighth.get("status") == "已评审" and not (doc.get("presentation") or []):
            report.bad(
                "MISSING_FILE",
                "presentation",
                "第 9 活动已评审却没有 presentation[] 记录",
            )
    else:
        done = [a for a in activities if a.get("status") in TERMINAL_STATUS]
        if len(done) == len(ACTIVITIES) and len(ACTIVITIES) and project.get("status") != "已定稿":
            report.bad(
                "STATUS_MISMATCH",
                "project.status",
                "全部活动已收口却没落 已定稿（忘了定稿，或漏了终门）",
            )

    report.counts = summarize(doc)
    # §4.1 连带：终门同回「设计系统在场」态（与 init 同语义 = 存在且可解析）
    report.counts["has_design_system"] = read_design_system(report, output_dir) is not None
    return report.exit_code()


# ---------------------------------------------------------------------- CLI


def _common_flags(parser):
    """共同旗标：`--project-root` 全部子命令都收；`--output-dir` 由 main 兜底（仅 init 必填）。"""
    parser.add_argument("--project-root", default=argparse.SUPPRESS, help="项目根（默认 .）")
    parser.add_argument("--output-dir", default=argparse.SUPPRESS,
                        help="产物目录（缺省 {project-root}/diy-output；写盘子命令 init 必填）")
    parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help="以 JSON 回执输出")
    return parser


def build_parser():
    common = _common_flags(argparse.ArgumentParser(add_help=False))
    parser = _common_flags(
        argparse.ArgumentParser(prog="wds_assets.py", description="diy-wds-assets 领域引擎")
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("init", parents=[common], help="铸骨架（唯一写盘）")
    p_list = sub.add_parser("list", parents=[common], help="只回约定字段")
    p_list.add_argument("--status")
    p_show = sub.add_parser("show", parents=[common], help="单条 / 整份")
    p_show.add_argument("--id")
    p_check = sub.add_parser("check", parents=[common], help="终门（--final 唯一放行）")
    p_check.add_argument("--final", action="store_true")
    p_prompts = sub.add_parser("prompts", parents=[common], help="提示词导出索引（只读）")
    p_prompts.add_argument("--activity")
    return parser


def main(argv=None):
    # 回执是机器读面：stdout/stderr 一律 UTF-8（VA-01；与其余四引擎逐字同款两行）
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    parser = build_parser()
    args = parser.parse_args(argv)
    root_given = str(getattr(args, "project_root", "."))
    project_root = Path(root_given).resolve()
    raw_output = getattr(args, "output_dir", None)
    # 只读子命令缺省回落 `{project_root}/diy-output`（V3-03；对齐 wds_system / evolution / analyze / reverse）
    output_dir = Path(raw_output).resolve() if raw_output else project_root / "diy-output"
    args.output_dir = str(output_dir)          # 各 handler 统一从 args 取（含回落值）
    as_json = bool(getattr(args, "json", False))

    if not args.command:
        report = Report("", project_root, output_dir, root_given)
        report.bad("ENUM_INVALID", "command", "缺少子命令：init / list / show / check / prompts")
        emit(report, as_json, exit_code=2)
        return 2
    if args.command == "init" and not raw_output:
        report = Report(args.command, project_root, output_dir, root_given)
        report.bad("ENUM_INVALID", "--output-dir", "写盘子命令 init 必填 --output-dir")
        emit(report, as_json, exit_code=2)
        return 2

    report = Report(args.command, project_root, output_dir, root_given)
    handler = {
        "init": cmd_init,
        "list": cmd_list,
        "show": cmd_show,
        "check": cmd_check,
        "prompts": cmd_prompts,
    }[args.command]
    code = handler(args, report)
    emit(report, as_json, code)
    return code


def emit(report: Report, as_json: bool, exit_code: int):
    """回执输出：`--json` = 单行 JSON（契约 §3）；无 `--json` = 每违规一行 `CODE where: msg` + 汇总行。"""
    payload = report.receipt(ok=(exit_code == 0))
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, default=str))
    else:
        for item in report.violations:
            print(f"{item['code']} {item['where']}: {item['msg']}")
        for item in report.warnings:
            print(f"WARN {item['code']} {item['where']}: {item['msg']}")
        print(f"ok={payload['ok']} violations={len(report.violations)} warnings={len(report.warnings)}")


if __name__ == "__main__":
    raise SystemExit(main())
