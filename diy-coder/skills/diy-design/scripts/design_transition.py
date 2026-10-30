# -*- coding: utf-8 -*-
"""diy-design transition 命令域：页状态迁移写回（9 条合法边）。."""

import io
import yaml

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import load_yaml, now, save_yaml_atomic, today, v  # noqa: E402

from design_a11y import page_gate_violations, required_states  # noqa: E402
from design_lib import PAGE_STATUSES, coerce_design, emit, load_design_doc, norm_path, page_id_violations, receipt  # noqa: E402
PAGE_STATUS_INITIAL = "未开始"
LEGAL_EDGES = frozenset({
    ("未开始", "结构稿中"),
    ("结构稿中", "待验收"),
    ("结构稿中", "已移除"),
    ("待验收", "已批准"),
    ("待验收", "结构稿中"),
    ("待验收", "已移除"),
    ("已批准", "结构稿中"),
    ("已批准", "已移除"),
    ("已移除", "结构稿中"),
})
# 页级门的落点边（不重跑 check）：→ 待验收 / 已批准 须先满足该页的 validate 判据
GATED_TARGETS = ("待验收", "已批准")

# ---------------------------------------------------------------- transition

def write_prev_snapshot(path):
    """重写既有产物前落 .prev 快照（逐字节复制 + 同目录 tmp + os.replace）。"""
    tmp = path + ".prev.tmp"
    with io.open(path, "rb") as f:
        data = f.read()
    try:
        with io.open(tmp, "wb") as f:
            f.write(data)
        os.replace(tmp, path + ".prev")
    except BaseException:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise

def dangling_design_refs(design_path, page_id):
    """stories.yaml 里 AC[].design_ref == page_id 的悬空 AC 清单（本技能只读，路由 diy-epics-stories）。"""
    stories_path = os.path.join(os.path.dirname(os.path.abspath(design_path)), "stories.yaml")
    if not os.path.isfile(stories_path):
        return []
    try:
        doc = load_yaml(stories_path)
    except yaml.YAMLError:
        return ["stories.yaml 解析失败——无法核对 AC[].design_ref 悬空项，请人工核对（路由 diy-epics-stories）"]
    out = []
    for story in doc.get("stories") or []:
        if not isinstance(story, dict):
            continue
        for ac in story.get("acceptance_criteria") or []:
            if isinstance(ac, dict) and ac.get("design_ref") == page_id:
                out.append("stories.yaml %s %s 的 design_ref=%s 已悬空——路由 diy-epics-stories 回写（本技能只读）"
                           % (story.get("id"), ac.get("id"), page_id))
    return out

def next_hint_for(src, dst, page_id):
    """迁移后点名下一步（状态闸 ≠ 质量闸：不重跑 check，改用回执点名）。"""
    if dst == "已移除":
        return "核对 AC[].design_ref 悬空项已路由 diy-epics-stories"
    table = {
        ("未开始", "结构稿中"): "写 prototypes/%s.html 结构稿（先出结构、经用户确认，再进详细规格）" % page_id,
        ("结构稿中", "待验收"): "跑 check / audit 自检全过，再请审查（diy-review 的 WDS 路径）",
        ("待验收", "已批准"): "用户批准（人裁，无自动后续步）——审查通过后页仍留 待验收，只报「待用户批准」",
        ("待验收", "结构稿中"): "按审查 findings 回修结构稿，改完重走 待验收",
        ("已批准", "结构稿中"): "重开：按变更信号改结构稿，改完重走 待验收",
        ("已移除", "结构稿中"): "恢复：重建结构稿并重走验收",
    }
    return table.get((src, dst), "继续设计工作流")

def _dup_page_ids(pages):
    seen, dups = set(), []
    for page in pages:
        if not isinstance(page, dict):
            continue
        pid = page.get("id")
        if not (isinstance(pid, str) and pid.strip()):
            continue  # 非字符串/空 ID 走 page_id_violations，不当重复键（列表不可哈希）
        if pid in seen and pid not in dups:
            dups.append(pid)
        seen.add(pid)
    return dups

def _transition_fail(args, violations, counts):
    return emit(receipt("transition", False, file=norm_path(args.design),
                        violations=violations, counts=counts, page=args.page), args.json)

def cmd_transition(args):  # trace: S-14 AC-14.1 页状态迁移写回（9 条合法边；破坏性边追加 revisions）
    path = args.design
    rel = norm_path(path)
    base_name = os.path.basename(path)
    doc, violations = load_design_doc(path)
    if doc is None:
        return _transition_fail(args, violations, {"pages": 0})
    problems = coerce_design(doc)[1]  # 只取形状问题清单（写回一律用原样文档，不用归一结果）
    if problems:
        return _transition_fail(args, [v("UNPARSABLE_YAML", rel, p) for p in problems],
                                {"pages": 0})
    raw_pages = doc.get("pages") if doc.get("pages") is not None else []
    if not isinstance(raw_pages, list):
        return _transition_fail(args, [v("UNPARSABLE_YAML", rel,
                                         "%s 的 pages 不是列表（形状异常）——拒绝写回" % rel)],
                                {"pages": 0})
    pages = raw_pages
    counts = {"pages": len(pages)}
    id_problems = page_id_violations(pages, base_name)
    if id_problems:
        return _transition_fail(args, id_problems, counts)
    dups = _dup_page_ids(pages)
    if dups:
        return _transition_fail(args, [v("DUPLICATE_ID", "%s pages[].id" % base_name,
                                         "页 ID 重复：%s——ID 是唯一引用键，先去重"
                                         % "/".join(str(d) for d in dups))], counts)
    page = next((p for p in pages if isinstance(p, dict) and p.get("id") == args.page), None)
    if page is None:
        return _transition_fail(args, [v("UNKNOWN_ID", "%s pages[%s]" % (base_name, args.page),
                                         "页 %s 不在 design.yaml 的 pages[] 中（ID 是唯一引用键）"
                                         % args.page)], counts)
    src = page.get("status") or PAGE_STATUS_INITIAL
    dst = args.to
    if src not in PAGE_STATUSES:
        return _transition_fail(args, [v("ENUM_INVALID",
                                         "%s pages[%s].status" % (base_name, args.page),
                                         "%s 的 status=%r 不在 %s——先修状态值再迁移"
                                         % (args.page, src, "/".join(PAGE_STATUSES)))], counts)
    if (src, dst) not in LEGAL_EDGES:
        legal = sorted({d for (s, d) in LEGAL_EDGES if s == src})
        return _transition_fail(args, [v("ILLEGAL_TRANSITION",
                                         "%s pages[%s].status" % (base_name, args.page),
                                         "非法迁移 %s → %s；从 %s 只能去 %s（合法边见 design.py "
                                         "transition 契约；跨态跳转须逐边走）"
                                         % (src, dst, src, "/".join(legal) or "（无出口）"))], counts)
    reason = (args.reason or "").strip()
    if dst == "已移除" and not reason:
        return _transition_fail(args, [v("EMPTY_FIELD",
                                         "%s pages[%s].removed_reason" % (base_name, args.page),
                                         "--to 已移除 必须给 --reason（移除原因，写进 removed_reason）")],
                                counts)
    if dst in GATED_TARGETS:
        gate = page_gate_violations(os.path.dirname(os.path.abspath(path)), page, base_name,
                                    "GATE_FAILED", "GATE_FAILED",
                                    required_states(doc.get("form_factor")))
        if gate:
            return _transition_fail(args, gate, counts)
    project = doc.get("project")
    if not isinstance(project, dict):
        return _transition_fail(args, [v("EMPTY_FIELD", base_name + " project",
                                         "project 缺失或不是映射——形状异常，拒绝写回")], counts)
    stamp = now()
    new_page = dict(page)
    new_page["status"] = dst
    if dst == "已移除":
        new_page["removed_reason"] = reason
    elif src == "已移除":
        new_page.pop("removed_reason", None)  # 恢复：清陈旧 reason（removed_reason 仅 已移除 时写）
    new_doc = {**doc, "pages": [new_page if p is page else p for p in pages],
               "project": {**project, "updated": stamp}}
    if dst == "已移除" or (src, dst) == ("已批准", "结构稿中"):
        # 破坏性边才追加 revisions：纯推进不记
        new_doc["revisions"] = list(doc.get("revisions") or []) + [
            {"date": today(), "change": args.page, "reason": reason or ("%s → %s" % (src, dst))}]
    warnings = dangling_design_refs(path, args.page) if dst == "已移除" else []
    write_prev_snapshot(path)  # 重写前落 .prev 快照
    save_yaml_atomic(path, new_doc)
    result = receipt("transition", True, file=rel, page=args.page, violations=[], warnings=warnings,
                     counts={"pages": len(new_doc["pages"]),
                             "revisions": len(new_doc.get("revisions") or [])},
                     **{"from": src, "to": dst, "updated": stamp,
                        "next_hint": next_hint_for(src, dst, args.page)})
    return emit(result, args.json,
                ["transition：%s %s → %s" % (args.page, src, dst),
                 "下一步：%s" % result["next_hint"]])
