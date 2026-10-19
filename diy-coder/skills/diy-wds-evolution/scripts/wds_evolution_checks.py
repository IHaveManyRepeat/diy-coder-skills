"""diy-wds-evolution 常量表、工具与演进校验。"""

import json
import os
import re
import sys
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import v  # noqa: E402
from diyc_lib_base import load_yaml_text  # noqa: E402

PRODUCT = "wds-evolution.yaml"
# VA-09（.yml 扩面）连带（C·11 V-A E3）：自产物的两种拼写都不算门禁上游
PRODUCT_STEM = PRODUCT.rsplit(".", 1)[0]
ROUND_RE = re.compile(r"^EV-(\d{2})$")
ROUND_STATUS = ("草稿", "分析", "范围", "设计", "实现", "验证", "已交付")
ENTRIES = ("存量接入", "上线后持续")
FACTOR_LEVELS = ("high", "medium", "low")
FACTOR_WEIGHT = {"high": 5, "medium": 3, "low": 1}
FACTORS = ("impact", "effort", "learning")
PHASES = ("analysis", "scope", "design", "implement", "test", "delivery")
PHASE_LABEL = {"analysis": "A 分析", "scope": "S 范围", "design": "D 设计",
               "implement": "I 实现", "test": "T 验证", "delivery": "P 交付"}
INCREMENT_SCOPE = "本轮增量"
CRITERION_VERDICTS = ("通过", "未通过")
# 本轮的判据四类——源 `delivery-templates.md` 的 TS-XXX 测试场景族 HP-/REG-/EC-/A11Y- 逐字保留
CRITERION_KINDS = ("HP", "REG", "EC", "A11Y")
STATUS_VALUES = ("草稿", "已定稿")

# 入口门禁的扫描面：既有产物任一在场即放行（本技能自己的产物不算；`.yml` 与 `.yaml` 同态）
GATE_FILES = ("design.yaml", "design.yml", "sprint.yaml", "sprint.yml")
GATE_GLOB_PREFIX = "wds-"


# —— 基础工具 ——


def emit(result, as_json):
    """打印回执并返回 exit code（ok → 0，否则 1）。"""
    if as_json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=False))
    else:
        for item in result["violations"]:
            print("{} {}: {}".format(item["code"], item["where"], item["msg"]))
        for item in result["warnings"]:
            print("WARN {} {}: {}".format(item["code"], item["where"], item["msg"]))
        summary = "OK" if result["ok"] else "FAIL({})".format(len(result["violations"]))
        print("{} — {} {}".format(summary, result["command"], result["counts"]))
    return 0 if result["ok"] else 1


def load_yaml_soft(path):
    """(data, err)。缺失 → (None, "missing")；空文件 → ({}, None)；解析错 → (None, msg)。"""
    if not os.path.exists(path):
        return None, "missing"
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError as exc:
        return None, str(exc)
    if not text.strip():
        return {}, None
    try:
        return load_yaml_text(text), None
    except yaml.YAMLError as exc:
        return None, str(exc)


def product_path(output_dir):
    return os.path.join(output_dir, PRODUCT)


def norm(path):
    return os.path.normpath(path).replace("\\", "/")


def gate_present(output_dir):
    """既有产物任一在场？（本技能自己的产物不计）"""
    if not os.path.isdir(output_dir):
        return []
    hits = []
    for name in GATE_FILES:
        if os.path.exists(os.path.join(output_dir, name)):
            hits.append(name)
    for name in sorted(os.listdir(output_dir)):
        if (name.startswith(GATE_GLOB_PREFIX)
                and name.endswith((".yaml", ".yml"))
                and name.rsplit(".", 1)[0] != PRODUCT_STEM):
            hits.append(name)
    return hits


def load_product_or_report(output_dir, violations):
    """读产物；缺失/损坏 → 记违规并回 None。"""
    path = product_path(output_dir)
    data, err = load_yaml_soft(path)
    where = norm(path)
    if err == "missing":
        violations.append(v("MISSING_FILE", where, "产物不存在：{}".format(PRODUCT)))
        return None
    if err:
        violations.append(v("UNPARSABLE_YAML", where, "YAML 解析失败：{}".format(err)))
        return None
    if not isinstance(data, dict):
        violations.append(v("UNPARSABLE_YAML", where, "产物顶层不是映射"))
        return None
    return data


def rounds_of(data):
    rounds = data.get("rounds")
    return rounds if isinstance(rounds, list) else []


# —— 校验内核 ——


def validate(data, violations, warnings, final):
    """全量校验。`final=True` 时叠加定稿级判据。"""
    # 1. project 四键
    project = data.get("project")
    if not isinstance(project, dict):
        violations.append(v("EMPTY_FIELD", "project", "project 段缺失或不是映射"))
        project = {}
    for key in ("name", "created", "updated", "status"):
        if project.get(key) in (None, ""):
            violations.append(v("EMPTY_FIELD", "project.{}".format(key), "必填键缺失"))
    status = project.get("status")
    if status not in (None, "") and status not in STATUS_VALUES:
        violations.append(v("ENUM_INVALID", "project.status",
                            "取值 {} 不在 {}".format(status, "|".join(STATUS_VALUES))))

    # 2. revisions
    if not isinstance(data.get("revisions"), list):
        violations.append(v("EMPTY_FIELD", "revisions", "revisions 必须是在场列表"))

    # 3. rounds
    rounds = data.get("rounds")
    if not isinstance(rounds, list) or not rounds:
        violations.append(v("EMPTY_FIELD", "rounds", "rounds 必须是非空列表"))
        rounds = []

    seen = {}
    for idx, rnd in enumerate(rounds):
        where = "rounds[{}]".format(idx)
        if not isinstance(rnd, dict):
            violations.append(v("EMPTY_FIELD", where, "轮次记录不是映射"))
            continue
        rid = rnd.get("id")
        if rid in (None, ""):
            violations.append(v("EMPTY_FIELD", where + ".id", "必填键缺失"))
        elif not ROUND_RE.match(str(rid)):
            violations.append(v("ENUM_INVALID", where + ".id",
                                "ID 形态应形如 EV-<nn>：{}".format(rid)))
        if rid in seen:
            violations.append(v("DUPLICATE_ID", where + ".id",
                                "{} 与 rounds[{}] 重复".format(rid, seen[rid])))
        else:
            seen[rid] = idx

        if str(rnd.get("target", "")).strip() == "":
            violations.append(v("EMPTY_FIELD", where + ".target", "必填键缺失"))
        rstatus = rnd.get("status")
        if rstatus not in ROUND_STATUS:
            violations.append(v("ENUM_INVALID", where + ".status",
                                "取值 {} 不在 {}".format(rstatus, "|".join(ROUND_STATUS))))
        entry = rnd.get("entry")
        if entry not in ENTRIES:
            violations.append(v("ENUM_INVALID", where + ".entry",
                                "取值 {} 不在 {}".format(entry, "|".join(ENTRIES))))

    # 4. ID 序号连续（EV-01 … EV-nn，不跳号不乱序）
    ids = [str(r.get("id", "")) for r in rounds if isinstance(r, dict)]
    if ids and all(ROUND_RE.match(i) for i in ids):
        expect = ["EV-{:02d}".format(n) for n in range(1, len(ids) + 1)]
        if ids != expect:
            violations.append(v("SET_MISMATCH", "rounds[].id",
                                "序号应为 {}，实为 {}".format(expect, ids)))

    # 5. Kaizen 优先级框架
    kp = data.get("kaizen_priority")
    if not isinstance(kp, dict):
        violations.append(v("EMPTY_FIELD", "kaizen_priority", "Kaizen 优先级段缺失"))
        kp = {}
    # formula / scale 由 init 铸出，永远在场；candidates 由会话追加（定稿时必须非空）
    for key in ("formula", "scale"):
        if kp.get(key) in (None, "", [], {}):
            violations.append(v("EMPTY_FIELD", "kaizen_priority." + key, "必填键缺失"))
    candidates = kp.get("candidates")
    if candidates is None:
        violations.append(v("EMPTY_FIELD", "kaizen_priority.candidates", "必填键缺失"))
        candidates = []
    elif not isinstance(candidates, list):
        violations.append(v("EMPTY_FIELD", "kaizen_priority.candidates", "必须是列表"))
        candidates = []
    elif final and not candidates:
        violations.append(v("EMPTY_FIELD", "kaizen_priority.candidates",
                            "定稿前必须至少有一条候选（Impact×Effort×Learning 排序）"))
    scale = kp.get("scale")
    if isinstance(scale, dict):
        for factor in FACTORS:
            block = scale.get(factor)
            if not isinstance(block, dict):
                violations.append(v("EMPTY_FIELD",
                                    "kaizen_priority.scale." + factor, "三档量表缺失"))
                continue
            for level in FACTOR_LEVELS:
                if block.get(level) != FACTOR_WEIGHT[level]:
                    violations.append(v("SET_MISMATCH",
                                        "kaizen_priority.scale.{}.{}".format(factor, level),
                                        "权重应为 {}，实为 {}".format(
                                            FACTOR_WEIGHT[level], block.get(level))))
    candidate_targets = []
    for idx, cand in enumerate(candidates):
        where = "kaizen_priority.candidates[{}]".format(idx)
        if not isinstance(cand, dict):
            violations.append(v("EMPTY_FIELD", where, "候选记录不是映射"))
            continue
        if str(cand.get("target", "")).strip() == "":
            violations.append(v("EMPTY_FIELD", where + ".target", "必填键缺失"))
        else:
            candidate_targets.append(cand["target"])
        product_score = 1
        ok_factors = True
        for factor in FACTORS:
            level = cand.get(factor)
            if level not in FACTOR_LEVELS:
                violations.append(v("ENUM_INVALID", where + "." + factor,
                                    "取值 {} 不在 high|medium|low".format(level)))
                ok_factors = False
            else:
                product_score *= FACTOR_WEIGHT[level]
        if ok_factors and cand.get("score") != product_score:
            violations.append(v("SET_MISMATCH", where + ".score",
                                "重算应为 {}，实为 {}".format(
                                    product_score, cand.get("score"))))

    # 6. 每轮目标必须来自候选清单
    for idx, rnd in enumerate(rounds):
        if not isinstance(rnd, dict):
            continue
        target = rnd.get("target")
        if target and candidate_targets and target not in candidate_targets:
            violations.append(v("SET_MISMATCH", "rounds[{}].target".format(idx),
                                "目标不在 kaizen_priority.candidates 内：{}".format(target)))

    # 7. 定稿级判据
    if final:
        if project.get("status") != "已定稿":
            violations.append(v("STATUS_MISMATCH", "project.status",
                                "--final 要求 已定稿，实为 {}".format(project.get("status"))))
        for idx, rnd in enumerate(rounds):
            where = "rounds[{}]".format(idx)
            if not isinstance(rnd, dict):
                continue
            if rnd.get("status") != "已交付":
                violations.append(v("STATUS_MISMATCH", where + ".status",
                                    "--final 要求 已交付，实为 {}".format(rnd.get("status"))))
            for phase in PHASES:
                block = rnd.get(phase)
                if block in (None, "", [], {}):
                    violations.append(v("EMPTY_FIELD", where + "." + phase,
                                        "六相 {} 段缺失".format(PHASE_LABEL[phase])))
            test = rnd.get("test")
            if isinstance(test, dict):
                if test.get("scope") != INCREMENT_SCOPE:
                    violations.append(v("ENUM_INVALID", where + ".test.scope",
                                        "裁定 10：只验本轮增量，取值应为 {}".format(
                                            INCREMENT_SCOPE)))
                criteria = test.get("criteria")
                if not isinstance(criteria, list) or not criteria:
                    violations.append(v("EMPTY_FIELD", where + ".test.criteria",
                                        "本轮增量判据清单缺失"))
                else:
                    for ci, crit in enumerate(criteria):
                        if not isinstance(crit, dict):
                            violations.append(v("EMPTY_FIELD",
                                                "{}.test.criteria[{}]".format(where, ci),
                                                "判据不是映射"))
                            continue
                        if str(crit.get("criterion", "")).strip() == "":
                            violations.append(v("EMPTY_FIELD",
                                                "{}.test.criteria[{}].criterion".format(where, ci),
                                                "判据描述缺失"))
                        kind = crit.get("kind")
                        if kind in (None, ""):
                            violations.append(v("EMPTY_FIELD",
                                                "{}.test.criteria[{}].kind".format(where, ci),
                                                "判据类别缺失（HP|REG|EC|A11Y）"))
                        elif kind not in CRITERION_KINDS:
                            violations.append(v("ENUM_INVALID",
                                                "{}.test.criteria[{}].kind".format(where, ci),
                                                "取值 {} 不在 {}".format(
                                                    kind, "|".join(CRITERION_KINDS))))
                        verdict = crit.get("verdict")
                        if verdict not in CRITERION_VERDICTS:
                            violations.append(v("ENUM_INVALID",
                                                "{}.test.criteria[{}].verdict".format(where, ci),
                                                "取值 {} 不在 通过|未通过".format(verdict)))
                        elif verdict != "通过":
                            violations.append(v("STATUS_MISMATCH",
                                                "{}.test.criteria[{}].verdict".format(where, ci),
                                                "定稿要求全部判据 通过，实为 {}".format(verdict)))
        marker = _find_assumption(data)
        if marker:
            violations.append(v("ASSUMPTION_PRESENT", marker, "--final 要求零 [假设] 标记"))
    else:
        for idx, rnd in enumerate(rounds):
            if isinstance(rnd, dict) and rnd.get("status") not in (None, "已交付"):
                filled = [p for p in PHASES if rnd.get(p) not in (None, "", [], {})]
                if len(filled) < len(PHASES):
                    warnings.append(v("SET_MISMATCH", "rounds[{}]".format(idx),
                                      "六相仅 {} / 6 齐备，定稿前必须补齐".format(len(filled))))


def _find_assumption(node, where=""):
    if isinstance(node, str):
        return where if "[假设]" in node else None
    if isinstance(node, dict):
        for key, value in node.items():
            hit = _find_assumption(value, "{}.{}".format(where, key) if where else str(key))
            if hit:
                return hit
    elif isinstance(node, list):
        for idx, value in enumerate(node):
            hit = _find_assumption(value, "{}[{}]".format(where, idx))
            if hit:
                return hit
    return None


def build_counts(data):
    rounds = rounds_of(data)
    by_status = {}
    for rnd in rounds:
        if isinstance(rnd, dict):
            key = str(rnd.get("status", "?"))
            by_status[key] = by_status.get(key, 0) + 1
    kp = data.get("kaizen_priority") if isinstance(data.get("kaizen_priority"), dict) else {}
    candidates = kp.get("candidates")
    return {
        "rounds": len(rounds),
        "by_status": by_status,
        "candidates": len(candidates) if isinstance(candidates, list) else 0,
        "delivered": by_status.get("已交付", 0),
    }


# —— 子命令 ——


