"""diy-viewer 引用收集、悬空诊断与渲染状态。"""

import html
import json
import re
import sys
from pathlib import Path

from viewer_glossary import DOC_KEY_LABELS, GLOSSARY
from viewer_labels import ENUM_KEYS, FREE_TEXT_FIELDS, KEY_LABELS

ID_RE = re.compile(r"\b[A-Z]{1,4}-\d+(?:\.\d+)*\b")
ID_FULL_RE = re.compile(r"[A-Z]{1,4}-\d+(?:\.\d+)*")
# trace: S-15 AC-15.1 design_ref（AC 绑定 design.yaml 页面引用）入引用链，悬空即标红
# replaced_by（TC.retired 替代用例 ID）入引用链：悬空即标红（UNKNOWN_ID 对位可见）
REF_KEYS = {"affects", "refs", "depends_on", "feature_refs", "story", "test_refs", "ac", "epic", "x-fr", "design_ref", "replaced_by", "cm_refs",
            # brainstorm 五键由 no/索引改引 BI-###：命中即链到
            # 想法卡片、悬空即标红（UNKNOWN_ID 对位可见）。键仅 brainstorm 在用，全局加不误伤；
            # 迁移期整数引用不经 is_id_string / all-str 守卫，仍走纯文本路径
            "ideas", "idea", "top", "quick_wins", "breakthroughs"}
# 资产路径字段（doc, key）：diy-wds-assets 的 assets[].path 是 **output_dir 相对**路径
# （引擎核 `path.startswith("assets/<活动>/")`），渲染成相对链接。
# 同键 path 在 openapi 是 API 路由（/users）、在 spec-scan 是扫描目标——一律不从全局映射
ASSET_PATH_FIELDS = {("wds-assets", "path")}
ASSET_PATH_RE = re.compile(r"^assets/[A-Za-z0-9][A-Za-z0-9._/-]*$")
# design 族两键装 output_dir 相对文件路径（结构稿 HTML /
# 实现文件）。与 wds-assets 的 assets/<活动>/ 前缀不同，路径根不定型（prototypes/、src/），
# ASSET_PATH_RE 罩不住，故独立判定（判据见 doc_path_value）：文件确在 output_dir 下 → 直链；
# 其余纯文本。两分支一律跳过 ID linkify——cell() → linkify() 的 ID_RE 会在路径中段命中
# 页 ID 形态（P-1）把 prototypes/P-1.html 腰斩成指向页锚的错链
DOC_PATH_FIELDS = {("design", "prototype"), ("design", "implementation")}
# 过程性字段默认折叠（FR-4.1 可读性，D-10 后白话化纪律）：结论常驻、过程按需展开。
# revisions 依「修订历史留痕」：
# 「viewer 渲染为默认折叠的修订历史卡片（沿用 detail 折叠做法）」
FOLDED_KEYS = {"evidence", "findings", "revisions"}
FOLDED_NOTE_LEN = 80
PREVIEW_KEYS = ("statement", "then", "title", "question", "goal", "risk", "name",
                "decision", "description", "narrative")
ID_INDEX: dict = {}
# S-12 ID 链一致性（FR-4.4）：悬空引用按文档汇总，渲染时行内标红 + 顶部告警
DANGLING_BY_DOC: dict = {}
# S-12 孤儿 must FR（AC-12.2）：未被任何 AC/用例引用，条目行标红
ORPHAN_IDS: set = set()


# 当前渲染文档名（B1 文档级标签覆盖的查表上下文）；模板按节点归属文档逐条切换
_RENDER_DOC = ""
_UNMAPPED_SEEN: set = set()
# 资产相对链接前缀：页面落在 {output_dir}/<view_dir>/，故默认视图目录（一层）即
# `../`；main 按 view_dir 实际深度覆盖，view_dir 为空（页面与产物同目录）时为 ``
_ASSET_REL_PREFIX = "../"
# 当前解析根 output_dir：doc_path_value 的文件存在性判定基准，main 赋值
_OUT_DIR: Path = Path()


def _diag_unmapped(value) -> None:
    # trace: 未映射枚举诊断（只打 stderr，不改输出）：契约漂移一行可见
    s = str(value)
    if not s or s in _UNMAPPED_SEEN:
        return
    _UNMAPPED_SEEN.add(s)
    print(f"[diy-viewer] unmapped enum: {s}", file=sys.stderr)


def is_enum_key(k: str) -> bool:
    # trace: 枚举判定带文档上下文：自由文本字段不做徽章尝试、不报漂移诊断
    return k in ENUM_KEYS and (_RENDER_DOC, k) not in FREE_TEXT_FIELDS


# retired 键族标签补充（全局表缺键在此收口，
# 零裸键纪律：replaced_by 直出英文＝显示缺陷）。retired/reason 全局表已收（已退休/原因），复用。
KEY_LABELS_EXT = {"replaced_by": "替代用例"}


def key_label(k: str) -> str:
    # trace: 文档级覆盖优先（bug-log type→小类），再回落全局表（type→类型）
    label = DOC_KEY_LABELS.get(_RENDER_DOC, {}).get(k)
    if label is None:
        label = KEY_LABELS.get(k)
    if label is None:
        label = KEY_LABELS_EXT.get(k)
    if label is None:
        if is_enum_key(k):
            _diag_unmapped(k)
        return k
    return label


def split_retired(items: list):
    """列表条目按 retired 键在场拆分（在场＝已裁废弃）——(活跃, 废弃)。"""
    active = [x for x in items if not (isinstance(x, dict) and "retired" in x)]
    retired = [x for x in items if isinstance(x, dict) and "retired" in x]
    return active, retired


def folded_section(inner: str, n: int) -> str:
    """废弃条目折叠区（默认收起；沿用 detail 折叠样式，标签走 key_label）。"""
    label = key_label("retired")
    return (f'<details class="detail"><summary>展开{gloss(esc(label))}（{n} 项）</summary>'
            f'<div class="d-body">{inner}</div></details>')


def gloss(text: str) -> str:
    """术语包装：已转义的展示文本命中术语表 → 悬浮解释（展示层增强，不改正文）。"""
    tip = GLOSSARY.get(text)
    if not tip:
        return text
    return f'<span class="term" data-tip="{esc(tip)}">{text}</span>'


def _collect_ids(node, doc: str, _seen=None) -> None:
    # trace: S-11 AC-11.1 TC-11.1.1 防环：自引用锚点（YAML 合法）结构只访问一次，不无限递归
    if _seen is None:
        _seen = set()
    if isinstance(node, dict):
        if id(node) in _seen:
            return
        _seen.add(id(node))
        i = node.get("id")
        if isinstance(i, str) and i not in ID_INDEX:
            preview = next(
                (str(node[k]) for k in PREVIEW_KEYS
                 if isinstance(node.get(k), str) and node[k].strip()),
                i,
            )
            ID_INDEX[i] = {"doc": doc, "preview": preview[:120], "node": node}
        for v in node.values():
            _collect_ids(v, doc, _seen)
    elif isinstance(node, list):
        if id(node) in _seen:
            return
        _seen.add(id(node))
        for x in node:
            _collect_ids(x, doc, _seen)


def is_id_string(v) -> bool:
    return isinstance(v, str) and ID_FULL_RE.fullmatch(v.strip()) is not None


def iter_ref_values(node, _seen=None):
    # trace: S-12 AC-12.1 AC-12.2 产出引用型字段的全部字符串值（悬空/孤儿共用遍历）；
    # S-11 AC-11.1 TC-11.1.1 防环：自引用结构只访问一次
    if _seen is None:
        _seen = set()
    if isinstance(node, dict):
        if id(node) in _seen:
            return
        _seen.add(id(node))
        for k, v in node.items():
            if k in REF_KEYS:
                vals = v if isinstance(v, list) else [v]
                for x in vals:
                    if isinstance(x, str):
                        yield x
            else:
                yield from iter_ref_values(v, _seen)
    elif isinstance(node, list):
        if id(node) in _seen:
            return
        _seen.add(id(node))
        for x in node:
            yield from iter_ref_values(x, _seen)


def collect_dangling(node, found: list) -> None:
    # trace: S-12 AC-12.1 TC-12.1.1 收集引用型字段中不可解析的 ID（悬空引用）
    found.extend(
        x.strip() for x in iter_ref_values(node)
        if is_id_string(x) and x.strip() not in ID_INDEX)


def compute_orphans(prd_data, referenced: set) -> set:
    # trace: S-12 AC-12.2 TC-12.2.1 must FR 未被任何 AC/用例引用 → 孤儿
    orphans = set()
    for feat in prd_data.get("features") or []:
        if not isinstance(feat, dict):
            continue
        for req in feat.get("requirements") or []:
            if (isinstance(req, dict) and is_id_string(req.get("id"))
                    and str(req.get("priority", "")).strip().lower() == "必须"
                    and req["id"].strip() not in referenced):
                orphans.add(req["id"].strip())
    return orphans


def dangling_ref(i: str) -> str:
    # trace: S-12 AC-12.1 TC-12.1.1 悬空引用：红字 + 错误徽章，断裂显式可见
    return (f'<span class="dangling">{esc(i)}</span>'
            f'<span class="badge b-bad">{gloss("引用不存在")}</span>')


def resolve_src_text(src, docs_by_name: dict):
    """按 src 锚取母体文本——ID 走 ID_INDEX.node 的可读文本；结构键走点路径。

    返回 (text, err)：text 为找到的字符串（可空串）；err 非空表示悬空/不可解析。
    docs_by_name: {doc_name: data} 由 viewer_pages 传入（点路径解析用）。
    结构键点路径以产物根为起点（如 prfaq.press_release.headline）；带 [n] 下标。
    """
    if src is None:
        return "", "src 缺失"
    s = str(src).strip()
    if not s:
        return "", "src 为空"
    hit = ID_INDEX.get(s)
    if hit is not None:
        node = hit.get("node")
        if isinstance(node, dict):
            for k in ("claim", "text", "statement", "need", "point", "question",
                      "goal", "rule", "choice"):
                v = node.get(k)
                if isinstance(v, str) and v.strip():
                    return v, ""
            # 回落：拼接短标量
            bits = [str(v) for v in node.values()
                    if isinstance(v, str) and len(v) < 200]
            return " · ".join(bits[:3]), ""
        return str(node) if node is not None else "", ""
    # 点路径：以产物根为起点（如 prfaq.press_release.headline / brief.extra_sections[0]）；
    # 首段通常同时是文档名与顶层键——在全部候选文档根上走完整路径，首个命中即返回
    parts = s.split(".")
    if not docs_by_name:
        return "", "点路径无候选文档：%s" % s

    def _walk(root, parts):
        cur = root
        for part in parts:
            if cur is None:
                return None
            if part.endswith("]") and "[" in part:
                key, _, idx = part[:-1].partition("[")
                try:
                    cur = cur.get(key) if isinstance(cur, dict) else None
                    if not isinstance(cur, list):
                        return None
                    cur = cur[int(idx)]
                except (ValueError, IndexError, AttributeError):
                    return None
            else:
                cur = cur.get(part) if isinstance(cur, dict) else None
        return cur

    for _doc, root in (docs_by_name or {}).items():
        if not isinstance(root, dict):
            continue
        cur = _walk(root, parts)
        if cur is None:
            continue
        if isinstance(cur, str):
            return cur, ""
        if isinstance(cur, dict):
            for k in ("statement", "text", "claim", "need", "point", "question",
                      "content", "choice", "rule", "goal"):
                v = cur.get(k)
                if isinstance(v, str) and v.strip():
                    return v, ""
            bits = [str(v) for v in cur.values() if isinstance(v, str) and v.strip()]
            if bits:
                return bits[0], ""
    return "", "点路径悬空：%s" % s


def id_link(i: str, hit: dict) -> str:
    return (f'<a class="idl" href="{esc(hit["doc"])}.html#{esc(i)}"'
            f' title="{esc(hit["preview"])}">{esc(i)}</a>')


def render_ref_item(i: str) -> str:
    """单个 ID 引用：仅编号链接，详情点击后在右侧面板查看。"""
    hit = ID_INDEX.get(i.strip())
    if not hit:
        return dangling_ref(i)  # trace: S-12 AC-12.1 悬空引用标红
    return id_link(i, hit)


def ref_cell(i: str) -> str:
    """正文引用字段：编号链接 + 目标摘要，审阅无需跳页。"""
    s = i.strip()
    hit = ID_INDEX.get(s)
    if not hit:
        return dangling_ref(i)  # trace: S-12 AC-12.1 悬空引用标红
    out = id_link(i, hit)
    if hit["preview"] and hit["preview"] != s:
        out += f'<span class="refsum">{esc(hit["preview"])}</span>'
    return out


def render_ref_list(items: list) -> str:
    """ID 引用列表：已登记 ID 出链接；未登记但形如 ID 的标红；其余回落纯文本。"""
    # 判序**先查索引，再判形态**：
    # ① 索引命中即链——覆盖 `SS-001-01` 这类三段短横 ID（is_id_string 的
    #    `[A-Z]{1,4}-\\d+` 不认它，若先判形态会把它降级成文本、再被 linkify 半匹配成
    #    指向 `SS-001` 的错链）
    # ② 未命中且形如 ID → 悬空标红，与 collect_dangling 的守卫对称
    # ③ 两者皆否（module-plan 的 depends_on 装技能名 diy-* 等）→ 纯文本，且不经 linkify
    lis = []
    for x in items:
        s = str(x).strip()
        hit = ID_INDEX.get(s)
        if hit is not None:
            lis.append(f"<li>{id_link(s, hit)}</li>")
        elif is_id_string(s):
            lis.append(f"<li>{dangling_ref(s)}</li>")  # trace: S-12 AC-12.1
        else:
            lis.append(f"<li>{esc(x)}</li>")
    return f'<ul class="reflist">{"".join(lis)}</ul>'


def build_id_index(docs: list) -> None:
    ID_INDEX.clear()
    for name, data in docs:
        _collect_ids(data, name)


def linkify(text: str) -> str:
    def sub(m):
        i = m.group(0)
        hit = ID_INDEX.get(i)
        if not hit:
            return i
        return (f'<a class="idl" href="{esc(hit["doc"])}.html#{esc(i)}"'
                f' title="{esc(hit["preview"])}">{i}</a>')

    return ID_RE.sub(sub, text)


def is_asset_path(k: str) -> bool:
    # 资产路径按 (文档, 键) 定位，不做全局映射
    return (_RENDER_DOC, k) in ASSET_PATH_FIELDS


def asset_link(v) -> str:
    """资产路径 → 相对链接（`../` + output_dir 相对路径）。
    只在值确为 `assets/` 下的相对路径时出链接：绝对路径、越级路径与自由文本一律回落纯文本。"""
    s = str(v).strip()
    if ASSET_PATH_RE.match(s) and ".." not in s:
        return f'<a class="asset" href="{esc(_ASSET_REL_PREFIX + s)}">{esc(s)}</a>'
    return cell(v)


def is_doc_path(k: str) -> bool:
    # design 族路径键按 (文档, 键) 定位，同 ASSET_PATH_FIELDS
    return (_RENDER_DOC, k) in DOC_PATH_FIELDS


def doc_path_value(v) -> str:
    """design 族路径值（裁定 C12-2 ②）：output_dir 下真实存在的文件 → 相对直链；
    其余 → 纯文本。两条路径都**不经 linkify**（见 DOC_PATH_FIELDS 注释的截断缺陷）；
    绝对路径 / URL / 越级显式回落纯文本（Path 的 / 拼接对 Windows 绝对路径会整体替换，
    必须先拒，否则 output_dir 外的文件也会被链出去）。"""
    if v is None or isinstance(v, (dict, list)):
        return cell(v)
    s = str(v).strip()
    looks_rel = (s and ".." not in s
                 and not s.startswith(("/", "\\", "http:", "https:", "file:"))
                 and re.match(r"^[A-Za-z]:[\\/]", s) is None)
    if looks_rel and (_OUT_DIR / s).is_file():
        return f'<a class="asset" href="{esc(_ASSET_REL_PREFIX + s)}">{esc(s)}</a>'
    return esc(s).replace("\n", "<br>")


def esc(v) -> str:
    return html.escape(str(v), quote=True)


def cell(v) -> str:
    """Render a scalar value; keeps line breaks, highlights [假设]."""
    if v is None:
        return '<span class="dim">—</span>'
    if isinstance(v, (dict, list)):
        return f'<code class="dim">{esc(json.dumps(v, ensure_ascii=False, default=str))}</code>'
    text = esc(v)
    if text.startswith("[假设]"):
        return f'<span class="assume" title="assumption, needs confirmation">{linkify(text)}</span>'
    return linkify(text).replace("\n", "<br>")

