"""diy-wds-trigger 终检、评分与指标。"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import check_tokens, display_path, enum_check, nonempty, receipt_base, require, v, walk_strings  # noqa: E402

from wds_trigger_checks_base import (
    ASSUMPTION_MARK, CLASS_DEFS, DECISION_ENUM, DRIVER_EMOJI, EFFECT_MAP_KEYS,
    ENTRY_ENUM, FEATURE_KEYS, FEATURE_RE, FINAL_STAGE, LEVEL_ENUM, MODE_ENUM,
    MUST_HAVE_SLACK, PLATFORM_NODE, PRIORITY_KEYS, PRODUCT_FILE, SCORE_OTHER,
    SCORE_PRIMARY, STAGE_ENUM, STATUS_ENUM, TOP_KEYS, as_dict, as_list,
    check_goals, check_patterns, check_personas, count_findings,
    driver_index, emit, expected_connections, out_dir_or_violation, persona_ids,
    read_document, resolve_ids)


def check_priority(priority, known_personas, known_drivers, show, final, out):
    """优先级段：排名带 why；焦点声明三档。ID 解析恒核，键齐备只在 `--final`。"""
    if not isinstance(priority, dict):
        out.append(v("EMPTY_FIELD", show + ".priority",
                     "须为映射（ranked_personas / ranked_drivers / focus_statement）"))
        return
    ranked = as_list(priority.get("ranked_personas"))
    resolve_ids(ranked, known_personas, "%s.priority.ranked_personas" % show, "人物排序", out)
    resolve_ids(as_list(priority.get("ranked_drivers")),
                known_drivers, "%s.priority.ranked_drivers" % show, "驱动因素排序", out)
    focus = as_dict(priority.get("focus_statement"))
    for key, label in (("must", "Must"), ("should", "Should"), ("could", "Could")):
        resolve_ids(as_list(focus.get(key)), known_drivers,
                    "%s.priority.focus_statement.%s" % (show, key), label, out)
    if not final:
        return
    require(priority, PRIORITY_KEYS, show + ".priority", out)
    order = [str(as_dict(x).get("id") or "") for x in ranked if isinstance(x, dict)]
    if sorted(order) != sorted(known_personas):
        out.append(v("SET_MISMATCH", "%s.priority.ranked_personas" % show,
                     "排序须覆盖全部人物恰一次（人物 %s，实排 %s）"
                     % ("|".join(sorted(known_personas)), "|".join(order))))
    if not focus:
        out.append(v("EMPTY_FIELD", "%s.priority.focus_statement" % show,
                     "须为映射（top_group / must / should / could）"))
        return
    top = str(focus.get("top_group") or "").strip()
    if top not in known_personas:
        out.append(v("UNKNOWN_ID", "%s.priority.focus_statement.top_group" % show,
                     "top_group = %s 不是既有 TG-<n>" % (top or "空")))
    elif order and order[0] != top:
        out.append(v("SET_MISMATCH", "%s.priority.focus_statement.top_group" % show,
                     "top_group 须 = 人物排序的第一名（%s），实为 %s" % (order[0], top)))
    if not nonempty(focus.get("must")):
        out.append(v("EMPTY_FIELD", "%s.priority.focus_statement.must" % show,
                     "Must Address 为空——焦点声明必须给必办项"))


def max_score(persona_count):
    """评分满分（源 `06c:84`）：主人物 5 + 其他每人 3。"""
    return SCORE_PRIMARY["高"] + SCORE_OTHER["高"] * max(persona_count - 1, 0)


def recompute_score(scores):
    """按评分表重算总分；形状不合法 → None。"""
    if not isinstance(scores, dict):
        return None
    primary = scores.get("primary")
    if primary not in SCORE_PRIMARY:
        return None
    total = SCORE_PRIMARY[primary]
    for value in as_list(scores.get("others")):
        if value not in SCORE_OTHER:
            return None
        total += SCORE_OTHER[value]
    return total


def check_features(features, persona_count, show, final, out):
    """特征影响段（裁定 10）：Primary 5/3/1、其他 3/1/0、Must-Have 阈值。"""
    if not final:
        return
    if not nonempty(features):
        out.append(v("EMPTY_FIELD", show + ".feature_impact",
                     "为空——裁定 10 保留特征影响分析（先设计哪个功能由它回答）"))
        return
    ceiling = max_score(persona_count)
    for index, record in enumerate(features):
        where = "%s.feature_impact[%d]" % (show, index)
        if not isinstance(record, dict):
            out.append(v("EMPTY_FIELD", where, "须为映射（键表 %s）" % " / ".join(FEATURE_KEYS)))
            continue
        require(record, FEATURE_KEYS, where, out)
        ident = str(record.get("id") or "").strip()
        if not FEATURE_RE.match(ident):
            out.append(v("ENUM_INVALID", where + ".id",
                         "ID 形态越界：%s（须为 FI-<n>；`F-*` 归主线 prd.yaml，避让）"
                         % (ident or "空")))
        enum_check(record.get("decision"), DECISION_ENUM, where + ".decision",
                   "decision", out)
        scores = as_dict(record.get("scores"))
        others = as_list(scores.get("others"))
        if others and len(others) != max(persona_count - 1, 0):
            out.append(v("SET_MISMATCH", where + ".scores.others",
                         "其他人物评分 %d 条 ≠ 人物数 %d − 1" % (len(others), persona_count)))
        computed = recompute_score(scores)
        stored = record.get("score")
        if computed is None:
            out.append(v("ENUM_INVALID", where + ".scores" ,
                         "评分越界：primary=%s / others=%s（合法集 高|中|低）"
                         % (scores.get("primary"), "|".join(str(x) for x in others))  ))
        elif stored != computed:
            out.append(v("SET_MISMATCH", where + ".score",
                         "score = %s 与评分表重算 %d 不符（主人物 高=5/中=3/低=1；"
                         "其他 高=3/中=1/低=0）" % (stored, computed)))
            continue
        decision = str(record.get("decision") or "").strip()
        primary = scores.get("primary")
        must = primary == LEVEL_ENUM[0] or stored >= ceiling - MUST_HAVE_SLACK
        if decision == DECISION_ENUM[0] and not must:
            out.append(v("STATUS_MISMATCH", where + ".decision",
                         "判「必须」但既不满足主人物命中「高」、也不满足 score ≥ max−%d（= %d）"
                         % (MUST_HAVE_SLACK, ceiling - MUST_HAVE_SLACK)))
        if decision == DECISION_ENUM[2] and primary == LEVEL_ENUM[0]:
            out.append(v("STATUS_MISMATCH", where + ".decision",
                         "主人物命中「高」的功能不得判「可选」（源 steps-v 04 硬规则）"))


def check_effect_map(graph, goals, personas, show, final, out):
    """Effect Map 段（裁定 7 收编的构图纪律）。"""
    if not isinstance(graph, dict):
        if final:
            out.append(v("EMPTY_FIELD", show + ".effect_map",
                         "须为映射（derived_from / nodes / connections / class_defs / diagram）"))
        return
    if not final:
        return
    require(graph, EFFECT_MAP_KEYS, show + ".effect_map", out)
    nodes = as_dict(graph.get("nodes"))
    expect = {"business_goals": ["BG%d" % i for i in range(len(goals))],
              "platform": PLATFORM_NODE,
              "target_groups": ["TG%d" % i for i in range(len(personas))],
              "driving_forces": ["DF%d" % i for i in range(len(personas))]}
    for key, value in expect.items():
        actual = nodes.get(key)
        if key == "platform":
            if actual != value:
                out.append(v("SET_MISMATCH", "%s.effect_map.nodes.%s" % (show, key),
                             "平台节点恒为 %s，实为 %s" % (value, actual)))
            continue
        if as_list(actual) != value:
            out.append(v("SET_MISMATCH", "%s.effect_map.nodes.%s" % (show, key),
                         "节点序列越界：须为 %s，实为 %s"
                         % ("|".join(value) or "（空）",
                            "|".join(str(x) for x in as_list(actual)) or "（空）")))
    want = sorted(expected_connections(goals, personas))
    have = sorted(str(x) for x in as_list(graph.get("connections")))
    if have != want:
        out.append(v("SET_MISMATCH", "%s.effect_map.connections" % show,
                     "连接须恰为 BG→PLATFORM ∪ PLATFORM→TG ∪ TG→DF（配对严格，本文 %s 条 / "
                     "应为 %d 条 = 目标数 + 2×人物数）" % (len(have), len(want))))
    if sorted(str(x) for x in as_list(graph.get("class_defs"))) != sorted(CLASS_DEFS):
        out.append(v("SET_MISMATCH", "%s.effect_map.class_defs" % show,
                     "四类样式须逐字取自源 `08g:63-66`（businessGoal / platform / targetGroup / "
                     "drivingForces 四条）"))
    diagram = graph.get("diagram")
    if isinstance(diagram, str) and diagram.strip():
        for mark in ("flowchart LR", PLATFORM_NODE, "classDef"):
            if mark not in diagram:
                out.append(v("EMPTY_FIELD", "%s.effect_map.diagram" % show,
                             "图内缺 %s（构图纪律见 steps/05-documents.md）" % mark))
        for emoji in DRIVER_EMOJI:
            if emoji not in diagram:
                out.append(v("EMPTY_FIELD", "%s.effect_map.diagram" % show,
                             "驱动因素须带 %s（正/负两栏）" % emoji))


def check_document(data, show, args):
    """全量校验；返回 (violations, warnings, counts)。"""
    violations = []
    project = as_dict(data.get("project"))
    if not isinstance(data.get("project"), dict):
        violations.append(v("EMPTY_FIELD", show + " project", "project 不是映射"))
    for key in ("name", "created", "updated", "status"):
        if not nonempty(project.get(key)):
            violations.append(v("EMPTY_FIELD", "%s.project.%s" % (show, key), "%s 为空" % key))
    status = project.get("status")
    status_ok = False
    if isinstance(status, str) and status.strip() in STATUS_ENUM:
        status = status.strip()
        status_ok = True
    elif nonempty(status):
        violations.append(v("ENUM_INVALID", show + ".project.status",
                            "status 越界：%s（合法集 %s）" % (status, "|".join(STATUS_ENUM))))
    elif nonempty(project.get("name")):
        violations.append(v("EMPTY_FIELD", show + ".project.status", "status 为空"))

    for key, allowed, label in (("stage", STAGE_ENUM, "stage"),
                                ("mode", MODE_ENUM, "mode"),
                                ("entry", ENTRY_ENUM, "entry")):
        if not nonempty(data.get(key)):
            violations.append(v("EMPTY_FIELD", "%s.%s" % (show, key), "%s 为空" % label))
        else:
            enum_check(data.get(key), allowed, "%s.%s" % (show, key), label, violations)
    stage = str(data.get("stage") or "").strip()
    # 同档规则：`已定稿` ⟺ `stage: 收尾`（反向不成立——`收尾` 也是 06-finish 进行中的合法中间态）
    if status_ok and status == STATUS_ENUM[1] and stage != FINAL_STAGE:
        violations.append(v("STATUS_MISMATCH", "%s.stage" % show,
                            "status: 已定稿 要求 stage: %s，实为 %s"
                            % (FINAL_STAGE, stage or "空")))

    for key in TOP_KEYS:
        if key not in data:
            violations.append(v("EMPTY_FIELD", "%s.%s" % (show, key),
                                "缺主体段 %s（§2.3 冻结）" % key))
    goals = as_list(data.get("business_goals"))
    personas = as_list(data.get("personas"))
    features = as_list(data.get("feature_impact"))
    for key, value in (("business_goals", data.get("business_goals")),
                       ("personas", data.get("personas")),
                       ("feature_impact", data.get("feature_impact"))):
        if value is not None and not isinstance(value, list):
            violations.append(v("EMPTY_FIELD", "%s.%s" % (show, key), "%s 须为列表" % key))
    check_goals(goals, show, args.final, violations)
    known_drivers = driver_index(data, violations, show)
    check_personas(data, show, args.final, violations)
    check_patterns(data.get("driver_patterns"), known_drivers, show, args.final, violations)
    check_priority(as_dict(data.get("priority")), set(persona_ids(data)), known_drivers,
                   show, args.final, violations)
    check_features(features, len(personas), show, args.final, violations)
    check_effect_map(as_dict(data.get("effect_map")), goals, personas, show, args.final,
                     violations)
    # 越界情形（与 metrics 同一实现源；裁定 6 的三组口径）——`--final` 时升级为违规
    if args.final:
        for where, msg in count_findings(data, show, require_present=True)[0]:
            violations.append(v("EMPTY_FIELD", where, msg))

    revisions = data.get("revisions")
    if revisions is None:
        violations.append(v("EMPTY_FIELD", show + " revisions", "revisions 缺失（无修订写空列表）"))
    elif not isinstance(revisions, list):
        violations.append(v("EMPTY_FIELD", show + " revisions", "revisions 不是列表"))

    violations += check_tokens(data, show)

    if args.final:
        if status_ok and status != STATUS_ENUM[1]:
            violations.append(v("STATUS_MISMATCH", show + ".project.status",
                                "--final 要求 status: 已定稿，实为 %s（先走完六个步骤文件，"
                                "再按 §2.5 六拍落盘定稿）" % status))
        if any(ASSUMPTION_MARK in text for _p, text in walk_strings(data, "")):
            violations.append(v("ASSUMPTION_PRESENT", show,
                                "--final 要求零 [假设]；未决项写进 revisions 或就地补问"))
    counts = {"records": 1,
              "by_status": {status: 1} if status_ok else {},
              "by_stage": {stage: 1} if stage else {},
              "personas": len(personas), "goals": len(goals), "features": len(features)}
    # `check` 无独立 warning 通道（诊断全走 violations）——`warnings` 恒空但键在位
    return violations, [], counts


def cmd_metrics(args):
    """计数体检：人物群 2–4、每人 3–5 正 + 3–5 负、连接数 = 目标数 + 2×人物数。

    越界一律 **warning**（源侧「展示端自适应」口径），exit 0；缺产物 / 坏产物 / 未知 ID
    才是违规。
    """
    payload = receipt_base("metrics", args, args.output_dir)
    out, missing = out_dir_or_violation(args, "metrics")
    if missing is not None:
        payload["violations"] = [missing]
        return emit(payload, args.json)
    root = os.path.abspath(args.project_root)
    path = os.path.join(out, PRODUCT_FILE)
    show = display_path(path, root)
    data, err = read_document(path)
    if err is not None:
        payload["violations"] = [v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err)]
        return emit(payload, args.json)
    if data is None:
        payload["violations"] = [v("MISSING_FILE", show,
                                   "%s 不存在（先跑 init 铸骨架）" % PRODUCT_FILE)]
        return emit(payload, args.json)
    wanted = str(args.id).strip() if nonempty(args.id) else None
    if wanted is not None and wanted not in persona_ids(data):
        payload["violations"] = [v("UNKNOWN_ID", show + ".personas",
                                   "找不到记录 %s（本技能记录 ID 取 TG-<n>）" % wanted)]
        return emit(payload, args.json)
    findings, needed = count_findings(data, show, only_id=wanted)
    payload["warnings"] = [v("EMPTY_FIELD", where, msg) for where, msg in findings]
    payload["ok"] = True
    payload["counts"] = needed
    body = ["- 人物群 %d ｜ 目标 %d ｜ 连接 %d/%d"
            % (needed["personas"], needed["goals"], needed["connections_actual"],
               needed["connections_expected"])]
    return emit(payload, args.json,
                "PASS：%s 体检完成（越界 %d 条，warning 不阻断）" % (show, len(findings)),
                body)


# ---------------------------------------------------------------- CLI

