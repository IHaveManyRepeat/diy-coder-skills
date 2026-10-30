"""diy-wds-assets 常量表、Report 与 IO 工具。"""

import re
import sys
import yaml
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "diy-tools" / "scripts"))
from diyc_lib import display_path, now, project_name  # noqa: E402
from diyc_lib_base import DuplicateKeyError, load_yaml_text  # noqa: E402

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
PRESENTATION_ACTIVITY = "AS-08"     # 第 9 活动：presentation[] 的 ID 空间
# AS-07 文案条目的六段
CONTENT_ACTIVITY = "AS-07"
CONTENT_KEYS = (
    "content_purpose", "trigger_map_context", "awareness_strategy",
    "action_filter", "empowerment_frame", "structural_order",
)
ITEM_ID_RE = re.compile(r"^AS-(\d{2})\.(\d{1,3})$")
PAGE_ID_RE = re.compile(r"^SC-\d{2}\.P\d+$")
TOKEN_RE = re.compile(r"\{([^{}\n]+)\}")
SKILL_DIR = Path(__file__).resolve().parent.parent
# 模板位清单的提取口径：
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
        doc = load_yaml_text(path.read_text(encoding="utf-8"))
    except DuplicateKeyError as exc:
        report.add("DUPLICATE_KEY", display_path(path, report.project_root),
                   f"YAML 重复键：{exc}", bucket)
        return None
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


def skeleton(project_root: Path) -> dict:
    ts = now()
    pname, _w = project_name(project_root)
    return {
        "project": {"name": pname, "created": ts, "updated": ts, "status": "草稿"},
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
    """模板位清单：解析 `templates/` 下各模板「要填的位」`{...}`。

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
    """占位符残留核：`{...}` **∈ 模板位清单 → 违规**（说明该位没被填掉）。

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
