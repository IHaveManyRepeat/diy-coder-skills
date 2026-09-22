# -*- coding: utf-8 -*-
"""diy-wds-evolution 的领域引擎（B7b 工位 W3）。

机制与规则来源
--------------
- 契约：`batch3-contract.md` §2.2/§3/§5/§7（子命令面、回执 schema、违规码冻结集、
  原子写纪律、代码惯例）。本引擎是本技能终门的**唯一**执行者——WDS 型产物一律走本引擎的
  `check`，**不得**改用 `diyc.py check --type`（`CHECK_TYPES` 是主线 8 型封闭集）。
- 产物：`{output_dir}/wds-evolution.yaml`（B7b 任务书 §2.3；主体段 `rounds[]` + `kaizen_priority`，
  记录 ID `EV-<nn>`）。
- 门禁（任务书裁定 9）：本技能是**入口技能**（`precededBy: []`）——门禁 = **既有产物任一在场**
  （`design.yaml` / `sprint.yaml` / `wds-*.yaml`，**本技能自己的产物除外**——它是要被演进的对象之外的东西）。
- 裁定 10：[T] 只验**本轮增量**（全量验收归 C 阶段的 `diy-dev`）→ `rounds[].test.scope` 冻结值
  `本轮增量`，`check --final` 机械核对。
- Kaizen 优先级框架（本技能相对 `diy-dev` 的不可替代内容）：`Priority = Impact × Effort × Learning`，
  三因子各取 `high|medium|low`（权重 5/3/1），`score` 必须等于三因子权重之积——
  **源侧两处表述互斥在此归一**：`kaizen-principles.md` 把 Effort 的 High 记作「1–2 天」（省力最优）、
  `steps-a/step-01` 的表把 High 记作「1-2 days」——故三因子**一律「越大越好」**，
  `score` 高 = 优先；**不是**「工作量越大越优先」。

违规码：**零新增**，全部复用 `batch3-contract.md` §3 冻结集
（`MISSING_FILE` / `UNPARSABLE_YAML` / `DUPLICATE_ID` / `UNKNOWN_ID` / `ENUM_INVALID` /
`EMPTY_FIELD` / `STATUS_MISMATCH` / `SET_MISMATCH` / `ASSUMPTION_PRESENT`）。
模态语义复用两处（在此声明）：
  ① `MISSING_FILE` 在 `init` 上承载「**入口门禁**：无任何既有产物可演进」——源侧该情形
     由「口头接力」承担（census-5 §6.2），diy 侧升级为硬门；
  ② `STATUS_MISMATCH` 承载「`--final` 时 `project.status` 非 `已定稿`」「轮次未达 `已交付`」
     「本轮增量判据存在 `未通过`」三类。

写盘纪律：`init` 是**唯一写盘**命令；`list` / `show` / `check` 全程只读。
原子写 = 全文 load → 就地改 → 同目录临时文件 + `os.replace`（同 `diyc_lib.save_yaml_atomic`
的「同款」实现——本技能目录自带全部内容，不跨目录 import 共享库，见 NFR-4）。
"""

import argparse
import json
import os
import re
import sys
import tempfile

import yaml

# —— 冻结常量 ——

PRODUCT = "wds-evolution.yaml"
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

# 入口门禁的扫描面：既有产物任一在场即放行（本技能自己的产物不算）
GATE_FILES = ("design.yaml", "sprint.yaml")
GATE_GLOB_PREFIX = "wds-"


class UsageError(Exception):
    """用法/参数错误（exit 2）。"""


# —— 基础工具 ——


def today():
    from datetime import date
    return date.today().isoformat()


def v(code, where, msg):
    return {"code": code, "where": where, "msg": msg}


def receipt(command, ok, **fields):
    data = {
        "ok": ok,
        "command": command,
        "project_root": fields.pop("project_root", "."),
        "output_dir": fields.pop("output_dir", ""),
        "instance": None,
        "violations": fields.pop("violations", []),
        "warnings": fields.pop("warnings", []),
        "counts": fields.pop("counts", {}),
    }
    data.update(fields)
    return data


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
        return yaml.safe_load(text), None
    except yaml.YAMLError as exc:
        return None, str(exc)


def save_yaml_atomic(path, data):
    """全文重写 + 同目录临时文件 + os.replace（对齐 save_yaml_atomic 的同款实现）。"""
    directory = os.path.dirname(os.path.abspath(path)) or "."
    fd, tmp = tempfile.mkstemp(dir=directory, prefix=".wds-evolution-", suffix=".tmp")
    os.close(fd)
    try:
        with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
            yaml.safe_dump(data, fh, allow_unicode=True, sort_keys=False,
                           default_flow_style=False)
        os.replace(tmp, path)
    except Exception:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


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
        if name.startswith(GATE_GLOB_PREFIX) and name.endswith(".yaml") and name != PRODUCT:
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


def cmd_init(args):
    violations, warnings = [], []
    where = norm(product_path(args.output_dir))
    if not args.target or not str(args.target).strip():
        violations.append(v("EMPTY_FIELD", where, "--target 必填，不得为空"))
    if args.entry not in ENTRIES:
        violations.append(v("ENUM_INVALID", "--entry",
                            "取值 {} 不在 {}".format(args.entry, "|".join(ENTRIES))))
    counts = {"rounds": 0, "by_status": {}, "candidates": 0, "delivered": 0}
    if violations:
        return receipt("init", False, project_root=args.project_root,
                       output_dir=norm(args.output_dir), violations=violations,
                       warnings=warnings, counts=counts)

    # 入口门禁（裁定 9）：既有产物任一在场
    hits = gate_present(args.output_dir)
    if not hits:
        violations.append(v("MISSING_FILE", where,
                            "入口门禁：{} 下无任何既有产物（design.yaml / sprint.yaml / "
                            "wds-*.yaml）可演进——本技能不产零起点项目".format(
                                norm(args.output_dir))))
        return receipt("init", False, project_root=args.project_root,
                       output_dir=norm(args.output_dir), violations=violations,
                       warnings=warnings, counts=counts)

    # 已有产物 → 不覆盖（只刷 updated + warning）
    if os.path.exists(product_path(args.output_dir)):
        data, err = load_yaml_soft(product_path(args.output_dir))
        if err and err != "missing":
            violations.append(v("UNPARSABLE_YAML", where,
                                "产物损坏，拒绝写入：{}".format(err)))
            return receipt("init", False, project_root=args.project_root,
                           output_dir=norm(args.output_dir), violations=violations,
                           warnings=warnings, counts=counts)
        if not isinstance(data, dict):
            violations.append(v("UNPARSABLE_YAML", where, "产物顶层不是映射，拒绝写入"))
            return receipt("init", False, project_root=args.project_root,
                           output_dir=norm(args.output_dir), violations=violations,
                           warnings=warnings, counts=counts)
        data.setdefault("project", {})["updated"] = today()
        save_yaml_atomic(product_path(args.output_dir), data)
        warnings.append(v("SET_MISMATCH", where,
                          "产物已存在：骨架与 EV-01 未重建，只刷 project.updated"))
        return receipt("init", True, project_root=args.project_root,
                       output_dir=norm(args.output_dir), violations=violations,
                       warnings=warnings, counts=build_counts(data), updated=today())

    # 铸骨架 + 首轮铸号
    name = os.path.basename(os.path.abspath(args.project_root)) or "project"
    data = {
        "project": {"name": name, "created": today(), "updated": today(),
                    "status": "草稿"},
        "kaizen_priority": {
            "formula": "Priority = Impact × Effort × Learning",
            "scale": {factor: dict(FACTOR_WEIGHT) for factor in FACTORS},
            "candidates": [],
        },
        "rounds": [{
            "id": "EV-01",
            "target": str(args.target).strip(),
            "status": "草稿",
            "entry": args.entry,
            "analysis": {},
            "scope": {},
            "design": {},
            "implement": {},
            "test": {"scope": INCREMENT_SCOPE, "criteria": []},
            "delivery": {},
        }],
        "revisions": [],
    }
    save_yaml_atomic(product_path(args.output_dir), data)
    return receipt("init", True, project_root=args.project_root,
                   output_dir=norm(args.output_dir), violations=violations,
                   warnings=warnings, counts=build_counts(data), updated=today())


def cmd_list(args):
    violations, warnings = [], []
    if args.status and args.status not in ROUND_STATUS:
        violations.append(v("ENUM_INVALID", "--status",
                            "取值 {} 不在 {}".format(args.status, "|".join(ROUND_STATUS))))
        return receipt("list", False, project_root=args.project_root,
                       output_dir=norm(args.output_dir), violations=violations,
                       warnings=warnings, counts={})
    data = load_product_or_report(args.output_dir, violations)
    if data is None:
        return receipt("list", False, project_root=args.project_root,
                       output_dir=norm(args.output_dir), violations=violations,
                       warnings=warnings, counts={})
    rows = []
    for rnd in rounds_of(data):
        if not isinstance(rnd, dict):
            continue
        if args.status and rnd.get("status") != args.status:
            continue
        rows.append({"id": rnd.get("id"), "target": rnd.get("target"),
                     "status": rnd.get("status"), "entry": rnd.get("entry")})
    return receipt("list", True, project_root=args.project_root,
                   output_dir=norm(args.output_dir), violations=violations,
                   warnings=warnings, counts=build_counts(data), rounds=rows)


def cmd_show(args):
    violations, warnings = [], []
    data = load_product_or_report(args.output_dir, violations)
    if data is None:
        return receipt("show", False, project_root=args.project_root,
                       output_dir=norm(args.output_dir), violations=violations,
                       warnings=warnings, counts={})
    if args.id:
        hit = None
        for rnd in rounds_of(data):
            if isinstance(rnd, dict) and rnd.get("id") == args.id:
                hit = rnd
                break
        if hit is None:
            violations.append(v("UNKNOWN_ID", "rounds[].id",
                                "{} 在 {} 中不存在".format(args.id, PRODUCT)))
            return receipt("show", False, project_root=args.project_root,
                           output_dir=norm(args.output_dir), violations=violations,
                           warnings=warnings, counts=build_counts(data))
        return receipt("show", True, project_root=args.project_root,
                       output_dir=norm(args.output_dir), violations=violations,
                       warnings=warnings, counts=build_counts(data), round=hit)
    return receipt("show", True, project_root=args.project_root,
                   output_dir=norm(args.output_dir), violations=violations,
                   warnings=warnings, counts=build_counts(data), document=data)


def cmd_check(args):
    violations, warnings = [], []
    data = load_product_or_report(args.output_dir, violations)
    if data is None:
        return receipt("check", False, project_root=args.project_root,
                       output_dir=norm(args.output_dir), violations=violations,
                       warnings=warnings, counts={})
    validate(data, violations, warnings, bool(args.final))
    return receipt("check", not violations, project_root=args.project_root,
                   output_dir=norm(args.output_dir), violations=violations,
                   warnings=warnings, counts=build_counts(data))


# —— CLI ——


def build_parser():
    ap = argparse.ArgumentParser(
        prog="wds_evolution.py",
        description="diy-wds-evolution 领域引擎：init 铸骨架 / list 续接 / show 取件 / check 终门",
    )
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--project-root", default=".", help="项目根（默认 .）")
    common.add_argument("--output-dir", default=None,
                        help="产物目录（相对 project-root；init 必填）")
    common.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    sub = ap.add_subparsers(dest="command")

    p_init = sub.add_parser("init", parents=[common], help="铸骨架与首轮 EV-01（唯一写盘）")
    p_init.add_argument("--entry", help="双轨入口：存量接入|上线后持续")
    p_init.add_argument("--target", help="本轮选定目标（必填）")
    p_init.set_defaults(func=cmd_init, requires_output=True)

    p_list = sub.add_parser("list", parents=[common], help="只回约定字段，不读正文")
    p_list.add_argument("--status", help="按记录级 status 过滤")
    p_list.set_defaults(func=cmd_list, requires_output=False)

    p_show = sub.add_parser("show", parents=[common], help="整份或单轮全文")
    p_show.add_argument("--id", help="EV-<nn>")
    p_show.set_defaults(func=cmd_show, requires_output=False)

    p_check = sub.add_parser("check", parents=[common], help="终门：--final 为定稿级")
    p_check.add_argument("--final", action="store_true", help="定稿级校验")
    p_check.set_defaults(func=cmd_check, requires_output=False)
    return ap


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = build_parser()
    args = ap.parse_args(argv)
    if not getattr(args, "func", None):
        ap.print_usage(sys.stderr)
        return 2
    if args.requires_output and not args.output_dir:
        ap.error("--output-dir 必填于写盘子命令")
    # 缺省回落 `{project_root}/diy-output`（**不是** CWD 相对——否则 `--project-root X`
    # 的调用方会静默读到另一个项目的产物）。同 wds_system.py / analyze.py / reverse.py。
    args.output_dir = args.output_dir or os.path.join(args.project_root, "diy-output")
    result = args.func(args)
    return emit(result, args.json)


if __name__ == "__main__":
    sys.exit(main())
