#!/usr/bin/env python3
"""diy-wds-assets 领域引擎（B7b / W2）。

子命令：init（唯一写盘）/ list / show / check / prompts。
- 全部子命令收 `--project-root`（默认 `.`）；写盘子命令 `init` 必填 `--output-dir`。
- **`--instance` 一律不做**（键恒 `null` 在位）。
- 回执共同键：{ok, command, project_root, output_dir, instance, violations, warnings, counts}
  —— `warnings` 与 `violations` 同形；`init` 另含 `updated`，只读子命令不含。
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
CODES = [row[1] for row in ACTIVITIES]
DIR_OF = {row[0]: row[3] for row in ACTIVITIES}
DIR_OF_CODE = {row[1]: row[3] for row in ACTIVITIES}

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
ITEM_ID_RE = re.compile(r"^AS-(\d{2})\.(\d{1,3})$")
PAGE_ID_RE = re.compile(r"^SC-\d{2}\.P\d+$")
TOKEN_RE = re.compile(r"\{([^{}\n]+)\}")
TOKEN_WHITELIST = {"project-root", "output_dir"}


class Report:
    """违规 / 警告的收集器（两者同形）。"""

    def __init__(self, command: str, project_root: Path, output_dir: Path):
        self.command = command
        self.project_root = project_root
        self.output_dir = output_dir
        self.violations: list[dict] = []
        self.warnings: list[dict] = []
        self.counts: dict = {}
        self.extra: dict = {}

    def add(self, code, where, message, bucket="violations"):
        getattr(self, bucket).append({"code": code, "where": where, "message": message})

    def bad(self, code, where, message):
        self.add(code, where, message)

    def warn(self, code, where, message):
        self.add(code, where, message, bucket="warnings")

    def receipt(self, ok=None):
        if ok is None:
            ok = not self.violations
        payload = {
            "ok": ok,
            "command": self.command,
            "project_root": str(self.project_root),
            "output_dir": str(self.output_dir),
            "instance": None,
            "violations": self.violations,
            "warnings": self.warnings,
            "counts": self.counts,
        }
        payload.update(self.extra)
        return payload

    def exit_code(self):
        return 0 if not self.violations else 1


def load_yaml(path: Path, report: Report, bucket="violations", label=None):
    if not path.exists():
        report.add("MISSING_FILE", str(path), f"{label or path.name} 不存在", bucket)
        return None
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        report.add("UNPARSABLE_YAML", str(path), f"YAML 解析失败：{exc}", bucket)
        return None
    if not isinstance(doc, dict):
        report.add("UNPARSABLE_YAML", str(path), "顶层不是映射", bucket)
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
        report.bad("STATUS_MISMATCH", str(output_dir / UPSTREAM), "上游 project.status 不是 已定稿")
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


def read_design_system(report: Report, output_dir: Path):
    path = output_dir / DESIGN_SYSTEM
    if not path.exists():
        report.warn("MISSING_FILE", str(path), "可选上游 wds-design-system.yaml 缺席：降级为不校验令牌一致性")
        return None
    doc = load_yaml(path, report, bucket="warnings", label="可选上游 wds-design-system.yaml")
    return doc


def scan_raw_tokens(text: str, report: Report):
    for line_no, line in enumerate(text.splitlines(), start=1):
        for token in TOKEN_RE.findall(line):
            if token not in TOKEN_WHITELIST:
                report.bad("TOKEN_UNRESOLVED", f"line {line_no}", f"未解析令牌 {{{token}}}")


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
    for act in doc.get("activities") or []:
        if act.get("id") == ident:
            report.extra["record"] = act
            report.counts = summarize(doc)
            return report.exit_code()
        for item in act.get("items") or []:
            if item.get("id") == ident:
                report.extra["record"] = item
                report.counts = summarize(doc)
                return report.exit_code()
    report.bad("UNKNOWN_ID", ident, f"产物里没有 {ident}")
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
        for j, item in enumerate(items):
            iwhere = f"{where}.items[{j}]"
            ident = str(item.get("id") or "")
            match = ITEM_ID_RE.match(ident)
            if not match:
                report.bad("SET_MISMATCH", iwhere, f"条目 ID 形态不合 AS-<nn>.<m>：{ident!r}")
            elif f"AS-{match.group(1)}" != act.get("id"):
                report.bad("SET_MISMATCH", iwhere, f"条目 ID {ident} 与父活动 {act.get('id')} 不同源")
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
                if not path.startswith(prefix):
                    report.bad("SET_MISMATCH", aw, f"资产路径须落 {prefix} 内，实为 {path}")
            verdict = ((item.get("review") or {}).get("verdict"))
            if verdict is not None and verdict not in VERDICTS:
                report.bad("ENUM_INVALID", iwhere, f"非法评审结论：{verdict}")
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
        if not path.startswith(prefix):
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
    for i, rec in enumerate(records):
        where = f"presentation[{i}]"
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
            if not path.startswith("assets/presentation/"):
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
        report.bad("ASSUMPTION_PRESENT", str(path), "产物含未决标记 [假设]")
    scan_raw_tokens(text, report)

    project = doc.get("project") or {}
    if project.get("status") not in PROJECT_STATUS:
        report.bad("ENUM_INVALID", "project.status", f"非法状态：{project.get('status')}")
    if doc.get("stage") not in STAGES:
        report.bad("ENUM_INVALID", "stage", f"非法阶段：{doc.get('stage')}")

    item_ids = check_activities(doc, report, page_ids(upstream))
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
                verdict = (item.get("review") or {}).get("verdict")
                if verdict != "通过":
                    report.bad(
                        "SET_MISMATCH",
                        f"activities[{index}].items[{j}]",
                        f"已定稿要求评审结论为 通过，实为 {verdict}",
                    )

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
    return report.exit_code()


# ---------------------------------------------------------------------- CLI


def _common_flags(parser):
    """共同旗标：`--project-root` 全部子命令都收；`--output-dir` 由 main 逐命令校验。"""
    parser.add_argument("--project-root", default=argparse.SUPPRESS, help="项目根（默认 .）")
    parser.add_argument("--output-dir", default=argparse.SUPPRESS, help="产物目录（写盘 / 读产物必填）")
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
    parser = build_parser()
    args = parser.parse_args(argv)
    project_root = Path(getattr(args, "project_root", ".")).resolve()
    raw_output = getattr(args, "output_dir", None)
    output_dir = Path(raw_output).resolve() if raw_output else project_root
    as_json = bool(getattr(args, "json", False))

    if not args.command:
        report = Report("", project_root, output_dir)
        report.bad("ENUM_INVALID", "command", "缺少子命令：init / list / show / check / prompts")
        emit(report, as_json, exit_code=2)
        return 2
    if not raw_output:
        report = Report(args.command, project_root, output_dir)
        report.bad("ENUM_INVALID", "--output-dir", "本子命令必填 --output-dir")
        emit(report, as_json, exit_code=2)
        return 2

    report = Report(args.command, project_root, output_dir)
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
    payload = report.receipt(ok=(exit_code == 0))
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    else:
        state = "OK" if exit_code == 0 else "FAIL"
        print(f"[{state}] {report.command or '(no command)'} → {report.output_dir}")
        for item in report.violations:
            print(f"  违规 {item['code']} @ {item['where']}: {item['message']}")
        for item in report.warnings:
            print(f"  警告 {item['code']} @ {item['where']}: {item['message']}")


if __name__ == "__main__":
    raise SystemExit(main())
