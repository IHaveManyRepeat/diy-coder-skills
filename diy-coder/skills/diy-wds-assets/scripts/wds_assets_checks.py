"""diy-wds-assets 活动、提示词与呈现校验。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "diy-tools" / "scripts"))
from diyc_lib import display_path, nonempty  # noqa: E402
from wds_assets_lib import (
    ACTIVITIES, ACTIVITY_STATUS, CONTENT_ACTIVITY, CONTENT_KEYS, DIR_OF,
    FRAME_JOBS, ITEM_ID_RE, PAGE_ID_RE, PRESENTATION_ACTIVITY, PRINCIPLE_COUNT,
    PRODUCT, PROJECT_STATUS, RECIPES, Report, SCOPES, STAGES, STATES,
    TERMINAL_STATUS, VERDICTS, coverage_report, gate_upstream, load_yaml,
    page_ids, path_in, read_design_system, scan_raw_tokens)

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
                # 只收形态合法且与父活动同源的 id：非法形态已判过，不级联刷屏
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
                    # VA-03c：`steps/07-content.md:10` 声称「引擎核六段在场与键齐」
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


