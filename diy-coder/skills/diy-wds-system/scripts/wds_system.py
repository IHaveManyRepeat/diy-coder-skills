# -*- coding: utf-8 -*-
"""diy-wds-system 领域引擎（形 A，承 B7a §2.2）——五子命令 init / list / show / check / similarity。

子命令签名（`--json` 一律适用；`--project-root` 默认 `.`；`--instance` 一律不做）：
    init        --mode <on|off> --prefix <p> [--name <n>] [--complexity <c>] [--output-dir D]  写盘
    list        [--prefix P] [--category C] [--status S] [--output-dir D]                     只读
    show        [--id ID] [--output-dir D]                                                    只读
    check       [--final] [--output-dir D]                                                    只读
    similarity  --visual <high|medium|low> --functional <…> --behavioral <…> --contextual <…> 只读零写盘

★ **第五子命令 `similarity` 是本批对 §2.2「四子命令」的一处登记性偏离**（回报 §8 ⑥ 已列）：
  任务书 §3 W1 卡「额外负担」第 5 条要求「**实现聚合段**」（重复检测的四维等级 → 百分比 →
  等级 → 推荐），而 §2.2 冻结「四子命令」——两条并存的最小满足 = 加一个**只读、零写盘**的
  第五子命令。先例：B7a 的 `diy-wds-trigger` 亦在四子命令之外加了 `metrics`。**不写盘**。

机制与规则来源（逐条）：
  · 组件 ID `[prefix]-[NNN]`、26 前缀表、6 分类表 —— 源 `wds-7/steps-c/step-08b:56–122`
  · 相似度聚合（四维权重 30/30/25/15、High/Medium/Low = 1.0/0.6/0.2、6 级阈值）
    —— 源 `wds-7/steps-c/step-03:56–167`（**只实现聚合段**；输入段不可机械，归人工判定，见步骤文件）
  · 上游门禁（`wds-scenarios.yaml` 的 `project.status: 已定稿`）—— 任务书 §2.3.1 冻结
  · `tokens` 派生自 `design.yaml.tokens`（引用不复述）—— 裁定 5（用户 2026-09-21 拍板）
  · `design_system_mode` 默认 `on` —— 裁定 17（计划 §四 :232 的反转口径）

违规码：**复用 batch3-contract §3 冻结集**（`MISSING_FILE` / `UNPARSABLE_YAML` /
`DUPLICATE_ID` / `UNKNOWN_ID` / `EMPTY_FIELD` / `ENUM_INVALID` / `STATUS_MISMATCH` /
`SET_MISMATCH` / `ASSUMPTION_PRESENT`）+ B6 已批码 `TOKEN_UNRESOLVED`。**本批零新增码。**
  ★ 两处**语义复用**（登记）：
    · `SET_MISMATCH` 承载三类：① 同前缀编号跳号 / 不连续；② 组件 `category` 与
      前缀表里同前缀那一行的 `category` 不一致；③ `init` 见到既有产物（**约定：不覆盖，
      只刷 `project.updated`，并出 warning** —— 与 B7a `diy-wds-brief` 的
      `init --project-type 与既有产物不符` 同款用法）。
    · `TOKEN_UNRESOLVED` 承载：组件 `token_refs` 的 `命名空间.名` 在本产物声明的
      命名空间表（`tokens.namespaces`）里解析不到，**或** `派生` 模式下本产物的名字
      超出了 `design.yaml.tokens` 的键集（引用漂移）。

副作用面：唯一写盘 = `{output_dir}/wds-design-system.yaml`（`init`）；三个只读子命令零写盘。
返回：exit 0 放行 / 1 违规 / 2 用法错误（argparse 默认）。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

try:
    import yaml
except ModuleNotFoundError:                                    # pragma: no cover
    sys.stderr.write("本引擎依赖 PyYAML：pip install pyyaml\n")
    raise

SKILL_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = SKILL_DIR / "data"

PRODUCT = "wds-design-system.yaml"
UPSTREAM = "wds-scenarios.yaml"
DESIGN = "design.yaml"

DOC_STATUSES = ("草稿", "已定稿")
MODES = ("on", "off")
COMPONENT_STATUSES = ("在用", "已废弃")
COMPLEXITIES = ("simple", "moderate", "complex")

ID_RE = re.compile(r"^([a-z]{3})-(\d{3})$")
PAGE_ID_RE = re.compile(r"^SC-\d{2}\.P\d+$")
TOKEN_REF_RE = re.compile(r"^([a-z_]+)\.([a-z0-9_\-]+)$")
NAMESPACES = ("color", "spacing", "typography")
ASSUMPTION = "[假设]"

# 组件记录必填键（11 段组件模板的 diy 形态；`related` / `notes` 为选填，故不入集）
COMPONENT_REQUIRED = (
    "id", "name", "prefix", "category", "complexity", "status", "variants", "states",
    "styling", "behavior", "accessibility", "usage", "used_in", "token_refs", "version",
)
DOC_REQUIRED = ("project", "design_system_mode", "tokens", "categories", "prefixes",
                "components", "revisions")


# ───────────────────────────── 基础设施 ─────────────────────────────

def today() -> str:
    import datetime
    return datetime.date.today().isoformat()


def load_yaml(path: Path):
    """→ (data, error)。error 为 None 表示解析成功。"""
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")), None
    except Exception as exc:                                   # noqa: BLE001 - 一律转违规码
        return None, str(exc)


def save_yaml_atomic(path: Path, data) -> None:
    """全文组装 → 同目录临时文件 → os.replace 原子替换（对齐 diyc 写回纪律；注释不保留）。"""
    text = yaml.safe_dump(data, allow_unicode=True, sort_keys=False,
                          default_flow_style=False)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def display_path(path: Path, project_root: Path) -> str:
    """相对 project-root、正斜杠；越界则绝对路径。"""
    try:
        return path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def v(code: str, where: str, msg: str) -> dict:
    return {"code": code, "where": where, "msg": msg}


def table_prefixes() -> list:
    data, err = load_yaml(DATA_DIR / "component-prefixes.yaml")
    if err:
        raise SystemExit("前缀表不可读：%s" % err)
    return data["table"]


def table_categories() -> list:
    data, err = load_yaml(DATA_DIR / "component-categories.yaml")
    if err:
        raise SystemExit("分类表不可读：%s" % err)
    return [c["name"] for c in data["categories"]]


def table_spacing_names() -> list:
    data, err = load_yaml(DATA_DIR / "token-vocabulary.yaml")
    if err:
        raise SystemExit("令牌词汇表不可读：%s" % err)
    return [s["name"] for s in data["spacing"]]


# ───────────────────────────── 上游与产物读取 ─────────────────────────────

def read_upstream(output_dir: Path, project_root: Path):
    """→ (page_ids, violations)。门禁：wds-scenarios.yaml 必须在场且已定稿。"""
    path = output_dir / UPSTREAM
    where = display_path(path, project_root)
    if not path.exists():
        return None, [v("MISSING_FILE", where,
                        "上游产物不在场——零产出停止，路由 `diy-wds-scenarios`")]
    doc, err = load_yaml(path)
    if err:
        return None, [v("UNPARSABLE_YAML", where, "上游产物不可解析：%s" % err)]
    status = (doc.get("project") or {}).get("status")
    if status != "已定稿":
        return None, [v("STATUS_MISMATCH", where + " project.status",
                        "上游未定稿（实测 %r）——零产出停止，路由 `diy-wds-scenarios`" % status)]
    pages = []
    for sc in doc.get("scenarios") or []:
        for pg in (sc or {}).get("pages") or []:
            if isinstance(pg, dict) and pg.get("id"):
                pages.append(pg["id"])
    return {"pages": pages, "name": (doc.get("project") or {}).get("name")}, None


def read_product(output_dir: Path, project_root: Path):
    """→ (data, violations)。产物必须在场且可解析。"""
    path = output_dir / PRODUCT
    where = display_path(path, project_root)
    if not path.exists():
        return None, [v("MISSING_FILE", where, "产物不在场——先跑 `init`")]
    doc, err = load_yaml(path)
    if err:
        return None, [v("UNPARSABLE_YAML", where, "产物不可解析：%s" % err)]
    return doc, None


def read_design(output_dir: Path):
    """可选读 `design.yaml`（裁定 5 的派生源头）→ (tokens, present)。"""
    path = output_dir / DESIGN
    if not path.exists():
        return None, False
    doc, err = load_yaml(path)
    if err or not isinstance(doc, dict):
        return None, False
    tokens = doc.get("tokens")
    return (tokens if isinstance(tokens, dict) else None), True


# ───────────────────────────── 组件记录 ─────────────────────────────

def new_component(cid: str, prefix: str, type_name: str, category: str,
                  complexity: str, day: str) -> dict:
    return {
        "id": cid,
        "name": type_name,
        "prefix": prefix,
        "category": category,
        "complexity": complexity,
        "status": "在用",
        "variants": [],
        "states": [{"name": "默认", "signals": []}],
        "styling": {"visual_properties": {}, "layout": {}, "library_component": None},
        "behavior": {"interactions": [], "animations": [], "rules": []},
        "accessibility": {"aria": None, "keyboard": [], "screen_reader": None},
        "usage": {"when_to_use": None, "when_not_to_use": [], "best_practices": []},
        "used_in": [],
        "token_refs": [],
        "related": [],
        "version": {"created": day, "updated": day, "changes": 1},
        "notes": None,
    }


def check_component(rec, idx, prefix_map, categories, page_ids, where_base,
                    namespaces, final):
    """单条组件记录的全部机械判据 → violations。"""
    bad = []
    if not isinstance(rec, dict):
        return [v("UNPARSABLE_YAML", "%s[%d]" % (where_base, idx), "组件记录不是映射")]
    cid = rec.get("id")
    m = ID_RE.match(cid) if isinstance(cid, str) else None
    if not cid:
        bad.append(v("EMPTY_FIELD", "%s[%d].id" % (where_base, idx), "组件缺 id"))
    elif not m:
        bad.append(v("SET_MISMATCH", "%s[%d].id" % (where_base, idx),
                     "id 形态须为 `[prefix]-[NNN]`（三位补零），实测 %r" % cid))
    elif m.group(1) not in prefix_map:
        bad.append(v("ENUM_INVALID", "%s[%d].id" % (where_base, idx),
                     "前缀 %r 不在 26 条冻结前缀表内" % m.group(1)))

    prefix = rec.get("prefix")
    if prefix not in prefix_map:
        bad.append(v("ENUM_INVALID", "%s[%d].prefix" % (where_base, idx),
                     "prefix %r 不在冻结前缀表内" % prefix))
    elif m and m.group(1) != prefix:
        bad.append(v("SET_MISMATCH", "%s[%d].prefix" % (where_base, idx),
                     "prefix %r 与 id 前缀 %r 不一致" % (prefix, m.group(1))))

    category = rec.get("category")
    if category not in categories:
        bad.append(v("ENUM_INVALID", "%s[%d].category" % (where_base, idx),
                     "category %r 不在 6 条冻结分类表内" % category))
    elif prefix in prefix_map and prefix_map[prefix] != category:
        bad.append(v("SET_MISMATCH", "%s[%d].category" % (where_base, idx),
                     "category %r 与前缀表里 %s 那一行的 %r 不一致"
                     % (category, prefix, prefix_map[prefix])))

    if rec.get("complexity") not in COMPLEXITIES:
        bad.append(v("ENUM_INVALID", "%s[%d].complexity" % (where_base, idx),
                     "complexity %r 不在 %s 内" % (rec.get("complexity"), list(COMPLEXITIES))))
    if rec.get("status") not in COMPONENT_STATUSES:
        bad.append(v("ENUM_INVALID", "%s[%d].status" % (where_base, idx),
                     "status %r 不在 %s 内" % (rec.get("status"), list(COMPONENT_STATUSES))))

    # used_in → 上游页面 ID（跨技能 ID 链接入）
    for j, pid in enumerate(rec.get("used_in") or []):
        if not (isinstance(pid, str) and PAGE_ID_RE.match(pid)):
            bad.append(v("SET_MISMATCH", "%s[%d].used_in[%d]" % (where_base, idx, j),
                         "页面引用须为 `SC-<nn>.P<n>` 形态，实测 %r" % pid))
        elif pid not in page_ids:
            bad.append(v("UNKNOWN_ID", "%s[%d].used_in[%d]" % (where_base, idx, j),
                         "%s 不在 wds-scenarios.yaml 的页面清单里" % pid))

    # token_refs → 命名空间解析（裁定 5 的机械兑现面）
    for j, ref in enumerate(rec.get("token_refs") or []):
        token_where = "%s[%d].token_refs[%d]" % (where_base, idx, j)
        m2 = TOKEN_REF_RE.match(ref) if isinstance(ref, str) else None
        if not m2:
            bad.append(v("TOKEN_UNRESOLVED", token_where,
                         "引用须为 `命名空间.名` 形态，实测 %r" % ref))
            continue
        ns, name = m2.group(1), m2.group(2)
        if ns not in NAMESPACES:
            bad.append(v("TOKEN_UNRESOLVED", token_where,
                         "命名空间 %r 不在 %s 内" % (ns, list(NAMESPACES))))
        elif name not in namespaces.get(ns, []):
            bad.append(v("TOKEN_UNRESOLVED", token_where,
                         "%s.%s 不在本产物声明的 %s 命名空间表内" % (ns, name, ns)))

    if final:
        for key in COMPONENT_REQUIRED:
            if key not in rec:
                bad.append(v("EMPTY_FIELD", "%s[%d]" % (where_base, idx),
                             "组件缺必填键 %r" % key))
        if not rec.get("name"):
            bad.append(v("EMPTY_FIELD", "%s[%d].name" % (where_base, idx), "组件缺 name"))
        for key in ("usage", "styling", "behavior", "accessibility"):
            if isinstance(rec.get(key), dict) and not rec.get(key):
                bad.append(v("EMPTY_FIELD", "%s[%d].%s" % (where_base, idx, key),
                             "定稿态不许留空段 %r" % key))
    return bad


def check_document(doc, project_root, output_dir, page_ids, prefix_table, categories,
                   namespaces, final) -> list:
    where = display_path(output_dir / PRODUCT, project_root)
    bad = []
    for key in DOC_REQUIRED:
        if key not in doc:
            bad.append(v("EMPTY_FIELD", where, "产物缺顶层键 %r" % key))
    if bad:
        return bad

    status = (doc.get("project") or {}).get("status")
    if status not in DOC_STATUSES:
        bad.append(v("ENUM_INVALID", where + " project.status",
                     "project.status %r 不在 %s 内" % (status, list(DOC_STATUSES))))
    if final and status != "已定稿":
        bad.append(v("STATUS_MISMATCH", where + " project.status",
                     "终门要求 project.status: 已定稿，实测 %r" % status))
    if doc.get("design_system_mode") not in MODES:
        bad.append(v("ENUM_INVALID", where + " design_system_mode",
                     "design_system_mode %r 不在 %s 内" % (doc.get("design_system_mode"),
                                                         list(MODES))))

    # 冻结表逐条对账
    want_p = [r["prefix"] for r in prefix_table]
    got_p = [r.get("prefix") for r in (doc.get("prefixes") or []) if isinstance(r, dict)]
    if got_p != want_p:
        bad.append(v("SET_MISMATCH", where + " prefixes",
                     "前缀表与冻结资产不一致（实测 %d 条，应为 %d 条）" % (len(got_p), len(want_p))))
    if list(doc.get("categories") or []) != list(categories):
        bad.append(v("SET_MISMATCH", where + " categories",
                     "分类表与冻结资产不一致（实测 %r）" % (doc.get("categories"),)))

    # token 段：派生模式下名字不得超出 design.yaml 的键集
    source = (doc.get("tokens") or {}).get("source") or {}
    if source.get("mode") == "派生":
        design, present = read_design(output_dir)
        if present and design is not None:
            for ns in ("color", "typography"):
                keys = sorted((design.get(ns) or {}).keys())
                got = list((doc.get("tokens") or {}).get("namespaces", {}).get(ns) or [])
                for name in got:
                    if keys and name not in keys:
                        bad.append(v("TOKEN_UNRESOLVED",
                                     "%s tokens.namespaces.%s" % (where, ns),
                                     "%s.%s 在 design.yaml.tokens.%s 里解析不到（引用漂移）"
                                     % (ns, name, ns)))

    # 组件集：唯一性 / 编号连续性 / 逐条判据
    comps = doc.get("components")
    if not isinstance(comps, list):
        bad.append(v("UNPARSABLE_YAML", where + " components", "components 不是列表"))
        return bad

    seen = {}
    prefix_map = {r["prefix"]: r["category"] for r in prefix_table}
    for i, rec in enumerate(comps):
        bad += check_component(rec, i, prefix_map, categories, page_ids,
                               where + " components", namespaces, final)
        cid = (rec or {}).get("id") if isinstance(rec, dict) else None
        if cid:
            seen.setdefault(cid, []).append(i)
    for cid, idxs in seen.items():
        if len(idxs) > 1:
            bad.append(v("DUPLICATE_ID", where + " components",
                         "%s 出现 %d 次（下标 %s）" % (cid, len(idxs), idxs)))

    per_prefix = {}
    for cid in seen:
        m = ID_RE.match(cid)
        if m:
            per_prefix.setdefault(m.group(1), []).append(int(m.group(2)))
    for prefix, nums in sorted(per_prefix.items()):
        if sorted(nums) != list(range(1, len(nums) + 1)):
            bad.append(v("SET_MISMATCH", where + " components",
                         "前缀 %s 的编号不连续（实测 %s，应自 001 起逐 1 递增）"
                         % (prefix, sorted(nums))))

    if final and not comps:
        bad.append(v("EMPTY_FIELD", where + " components", "定稿态不许零组件"))

    # 零 [假设]
    dumped = json.dumps(doc, ensure_ascii=False)
    if ASSUMPTION in dumped:
        bad.append(v("ASSUMPTION_PRESENT", where,
                     "产物含 %s 标记——未决项须写进 revisions 或就地补问" % ASSUMPTION))
    return bad


# ───────────────────────────── 子命令 ─────────────────────────────

def cmd_init(args, project_root: Path) -> dict:
    output_dir = Path(args.output_dir)
    violations, warnings = [], []
    prefix_table = table_prefixes()
    categories = table_categories()
    prefix_map = {r["prefix"]: r for r in prefix_table}

    prefix = args.prefix
    if prefix is None or prefix == "":
        violations.append(v("EMPTY_FIELD", "init --prefix", "`--prefix` 不得为空"))
    elif prefix not in prefix_map:
        violations.append(v("ENUM_INVALID", "init --prefix",
                            "%r 不在 26 条冻结前缀表内" % prefix))
    if args.mode not in MODES:
        violations.append(v("ENUM_INVALID", "init --mode",
                            "%r 不在 %s 内" % (args.mode, list(MODES))))
    if args.complexity not in COMPLEXITIES:
        violations.append(v("ENUM_INVALID", "init --complexity",
                            "%r 不在 %s 内" % (args.complexity, list(COMPLEXITIES))))
    if violations:
        return {"violations": violations, "warnings": warnings, "counts": {}}

    upstream, bad = read_upstream(output_dir, project_root)
    if bad:
        return {"violations": bad, "warnings": warnings, "counts": {}}

    day = today()
    product_path = output_dir / PRODUCT
    where = display_path(product_path, project_root)
    if product_path.exists():
        existing, err = load_yaml(product_path)
        if err:
            return {"violations": [v("UNPARSABLE_YAML", where, "产物不可解析：%s" % err)],
                    "warnings": warnings, "counts": {}}
        existing.setdefault("project", {})["updated"] = day
        save_yaml_atomic(product_path, existing)
        warnings.append(v("SET_MISMATCH", where,
                          "既有产物在场——约定不覆盖，只刷 project.updated（本次未铸新号）"))
        return {"violations": violations, "warnings": warnings,
                "counts": {"components": len(existing.get("components") or []),
                           "created": False},
                "updated": day}

    design, design_present = read_design(output_dir)
    if design_present and design is not None:
        mode, color_names = "派生", sorted((design.get("color") or {}).keys())
        typo_names = sorted((design.get("typography") or {}).keys())
    else:
        mode = "独立"
        color_names = ["accent", "accent_text", "bg", "surface", "text", "text_muted"]
        typo_names = ["family_base", "family_heading", "scale"]
        warnings.append(v("MISSING_FILE", display_path(output_dir / DESIGN, project_root),
                          "`design.yaml` 不在场——token 降级为独立定义（裁定 5 的可选读降级）"))

    doc = {
        "project": {"name": upstream.get("name") or output_dir.name,
                    "created": day, "updated": day, "status": "草稿"},
        "design_system_mode": args.mode,
        "tokens": {
            "source": {"file": DESIGN, "path": "tokens", "mode": mode},
            "namespaces": {
                "color": color_names,
                "spacing": table_spacing_names(),
                "typography": typo_names,
            },
        },
        "categories": categories,
        "prefixes": [{"type": r["type"], "prefix": r["prefix"], "category": r["category"]}
                     for r in prefix_table],
        "components": [new_component(
            "%s-001" % prefix, prefix,
            args.name or prefix_map[prefix]["type"],
            prefix_map[prefix]["category"], args.complexity, day)],
        "revisions": [],
    }
    save_yaml_atomic(product_path, doc)
    return {"violations": violations, "warnings": warnings,
            "counts": {"components": 1, "prefixes": len(prefix_table),
                       "categories": len(categories), "created": True},
            "updated": day}


def cmd_list(args, project_root: Path) -> dict:
    output_dir = Path(args.output_dir)
    if args.status is not None and args.status not in COMPONENT_STATUSES:
        return {"violations": [v("ENUM_INVALID", "list --status",
                                 "%r 不在 %s 内" % (args.status, list(COMPONENT_STATUSES)))],
                "warnings": [], "counts": {}}
    if args.category is not None and args.category not in table_categories():
        return {"violations": [v("ENUM_INVALID", "list --category",
                                 "%r 不在 6 条冻结分类表内" % args.category)],
                "warnings": [], "counts": {}}
    doc, bad = read_product(output_dir, project_root)
    if bad:
        return {"violations": bad, "warnings": [], "counts": {}}

    items = []
    for rec in doc.get("components") or []:
        if not isinstance(rec, dict):
            continue
        if args.prefix is not None and rec.get("prefix") != args.prefix:
            continue
        if args.category is not None and rec.get("category") != args.category:
            continue
        if args.status is not None and rec.get("status") != args.status:
            continue
        items.append({"id": rec.get("id"), "name": rec.get("name"),
                      "category": rec.get("category"), "prefix": rec.get("prefix"),
                      "complexity": rec.get("complexity"), "status": rec.get("status")})
    return {"violations": [], "warnings": [], "items": items,
            "counts": {"items": len(items),
                       "components": len(doc.get("components") or [])}}


def cmd_show(args, project_root: Path) -> dict:
    output_dir = Path(args.output_dir)
    doc, bad = read_product(output_dir, project_root)
    if bad:
        return {"violations": bad, "warnings": [], "counts": {}}
    comps = [r for r in (doc.get("components") or []) if isinstance(r, dict)]
    if args.id is None:
        return {"violations": [], "warnings": [], "document": doc,
                "counts": {"components": len(comps), "returned": len(comps)}}
    hit = [r for r in comps if r.get("id") == args.id]
    if not hit:
        return {"violations": [v("UNKNOWN_ID", "show --id",
                                 "%s 不在 components[] 里" % args.id)],
                "warnings": [], "counts": {"components": len(comps)}}
    return {"violations": [], "warnings": [], "document": hit[0],
            "counts": {"components": len(comps), "returned": 1}}


# 四维权重与等级→数值映射（源 step-03:152–160 的 action 块，逐字）
DIM_WEIGHTS = {"visual": 0.30, "functional": 0.30, "behavioral": 0.25, "contextual": 0.15}
GRADE_VALUES = {"high": 1.0, "medium": 0.6, "low": 0.2}
# 6 级阈值（源 step-03:56–144；左闭右闭，逐级递减）
SIM_LEVELS = (
    (95, 100, 1, "Identical", "复用既有组件引用"),
    (80, 94, 2, "Very High Similarity", "考虑给既有组件加变体"),
    (65, 79, 3, "High Similarity", "设计师定：加变体还是新建"),
    (45, 64, 4, "Medium Similarity", "倾向新建，请设计师确认"),
    (20, 44, 5, "Low Similarity", "新建组件"),
    (0, 19, 6, "No Similarity", "必新建组件"),
)


def cmd_similarity(args, project_root: Path) -> dict:
    """重复检测的**聚合段**（可机械段）：四维等级 → 百分比 → 等级 → 推荐。

    ★ 只此一段可机械。**输入段（规格 + 候选 → 四维 High/Medium/Low）不可机械**——
      源侧只有散文示例、无字段级比对规则（源 step-02:94–199 全是 `Example`），
      故「四维等级」由会话按四维属性表逐维判定并经用户确认后传入本命令。
    """
    where = "similarity --visual/--functional/--behavioral/--contextual"
    grades = {"visual": args.visual, "functional": args.functional,
              "behavioral": args.behavioral, "contextual": args.contextual}
    violations = []
    for dim, g in grades.items():
        if g is None or g == "":
            violations.append(v("EMPTY_FIELD", where, "维度 %s 不得为空" % dim))
        elif g not in GRADE_VALUES:
            violations.append(v("ENUM_INVALID", where,
                                "维度 %s 取值 %r 不在 %s 内" % (dim, g, list(GRADE_VALUES))))
    if violations:
        return {"violations": violations, "warnings": [], "counts": {}}

    overall = sum(GRADE_VALUES[grades[d]] * DIM_WEIGHTS[d] for d in DIM_WEIGHTS)
    pct = int(round(overall * 100))
    level = next((row for row in SIM_LEVELS if row[0] <= pct <= row[1]), SIM_LEVELS[-1])
    _, _, number, level_name, recommendation = level
    key_factors = ["%s=%s(%.1f)×%.2f" % (d, grades[d], GRADE_VALUES[grades[d]], DIM_WEIGHTS[d])
                   for d in ("visual", "functional", "behavioral", "contextual")]
    result = {
        "violations": [], "warnings": [],
        "similarity": {"percentage": pct, "level": level_name, "level_number": number,
                       "recommendation": recommendation, "key_factors": key_factors,
                       "grades": grades, "weights": DIM_WEIGHTS, "overall": round(overall, 4)},
        "counts": {"percentage": pct, "level_number": number},
    }
    return result


def cmd_check(args, project_root: Path) -> dict:
    output_dir = Path(args.output_dir)
    doc, bad = read_product(output_dir, project_root)
    if bad:
        return {"violations": bad, "warnings": [], "counts": {}}
    upstream, bad = read_upstream(output_dir, project_root)
    if bad:
        return {"violations": bad, "warnings": [], "counts": {}}

    warnings = []
    if not (output_dir / DESIGN).exists():
        warnings.append(v("MISSING_FILE", display_path(output_dir / DESIGN, project_root),
                          "`design.yaml` 不在场——token 按独立定义核（裁定 5 的可选读降级）"))
    namespaces = ((doc.get("tokens") or {}).get("namespaces") or {})
    violations = check_document(doc, project_root, output_dir, set(upstream["pages"]),
                               table_prefixes(), table_categories(), namespaces, args.final)
    return {"violations": violations, "warnings": warnings,
            "counts": {"components": len(doc.get("components") or []),
                       "violations": len(violations), "warnings": len(warnings)}}


# ───────────────────────────── CLI ─────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="wds_system.py",
        description="diy-wds-system 领域引擎：设计系统组件库与令牌（token 派生自 design.yaml）")
    ap.add_argument("--json", action="store_true", help="输出单行 JSON 回执")
    sub = ap.add_subparsers(dest="command")

    def common(p, write):
        # `--json` 在子命令后也要能写：default=SUPPRESS 保证不覆盖根解析器的取值
        p.add_argument("--json", action="store_true", default=argparse.SUPPRESS,
                       help="输出单行 JSON 回执")
        p.add_argument("--project-root", default=".")
        p.add_argument("--output-dir", required=write, default=None,
                       help="读写根（写盘子命令必填）")

    p = sub.add_parser("init", help="铸产物骨架 + 首条组件记录（唯一写盘）")
    p.add_argument("--mode", default="on", help="design_system_mode：on|off（默认 on）")
    p.add_argument("--prefix", required=True, help="首条组件的类型前缀（26 条冻结表内）")
    p.add_argument("--name", default=None, help="首条组件名（缺省取前缀表里的 type）")
    p.add_argument("--complexity", default="simple", help="simple|moderate|complex")
    common(p, True)

    p = sub.add_parser("list", help="只回六字段（不读正文）")
    p.add_argument("--prefix", default=None)
    p.add_argument("--category", default=None)
    p.add_argument("--status", default=None)
    common(p, False)

    p = sub.add_parser("show", help="单条或整份全文")
    p.add_argument("--id", default=None)
    common(p, False)

    p = sub.add_parser("check", help="机械核对（--final 为终门）")
    p.add_argument("--final", action="store_true")
    common(p, False)

    p = sub.add_parser("similarity", help="重复检测聚合段：四维等级 → 百分比 → 等级 → 推荐")
    for dim in ("visual", "functional", "behavioral", "contextual"):
        p.add_argument("--" + dim, default=None, help="high|medium|low")
    common(p, False)
    return ap


def main(argv=None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = build_parser()
    args = ap.parse_args(argv)
    if not args.command:
        ap.print_usage(sys.stderr)
        return 2

    project_root = Path(args.project_root)
    if getattr(args, "output_dir", None):
        output_dir = Path(args.output_dir)
    else:
        output_dir = project_root / "diy-output"
    args.output_dir = os.path.normpath(str(output_dir))

    handlers = {"init": cmd_init, "list": cmd_list, "show": cmd_show, "check": cmd_check,
                "similarity": cmd_similarity}
    result = handlers[args.command](args, project_root)
    violations = result["violations"]
    warnings = result["warnings"]
    receipt = {
        "ok": not violations,
        "command": args.command,
        "project_root": str(args.project_root),
        "output_dir": args.output_dir,
        "instance": None,
        "violations": violations,
        "warnings": warnings,
        "counts": result.get("counts", {}),
    }
    if args.command == "init":
        receipt["updated"] = result.get("updated")
    for extra in ("items", "document", "similarity"):
        if extra in result:
            receipt[extra] = result[extra]

    if args.json:
        sys.stdout.write(json.dumps(receipt, ensure_ascii=False) + "\n")
    else:
        for item in violations:
            sys.stdout.write("%s %s: %s\n" % (item["code"], item["where"], item["msg"]))
        for item in warnings:
            sys.stdout.write("WARN %s %s: %s\n" % (item["code"], item["where"], item["msg"]))
        sys.stdout.write("ok=%s violations=%d warnings=%d\n"
                         % (receipt["ok"], len(violations), len(warnings)))
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
