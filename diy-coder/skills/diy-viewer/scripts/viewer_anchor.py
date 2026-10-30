"""卡内子键标题 id 全名制铸造（Q-130）：祖先上下文前缀防跨卡撞号。

ctx 为祖先段元组 ((is_id, segment), ...)：is_id=True 段来自卡片 id 锚——
铸造时截断键链只取最近 id 作前缀（如 D-01-alternatives）；无 id 祖先时
取全键路径链兜底（如 scope-page_strategy）。同页撞号（同卡同键/无 id
兄弟卡）追加 -N 计数后缀保证唯一。slugify 由此单源，viewer_render 再导出。
"""
from viewer_labels import KEY_RE


def slugify(s: str) -> str:
    return KEY_RE.sub("-", str(s).strip().lower()).strip("-") or "x"


_HEADING_SEEN: dict = {}


def reset_heading_ids() -> None:
    """新节渲染入口（depth=0）与详情模板批量入口清空页内去重登记。"""
    _HEADING_SEEN.clear()


def mint_heading_id(key: str, ctx) -> str:
    """全名制标题 id：最近 id 祖先（父卡）为前缀；无 id 祖先→全键路径链；撞号→-N 后缀。"""
    chain = []
    id_prefix = None
    for is_id, seg in reversed(ctx):
        if is_id:
            id_prefix = seg
            break
        chain.append(seg)
    if id_prefix is not None:
        parts = [id_prefix, key]  # 父卡 id 值 + 本键（拟例 D-01-alternatives），中间键不入链
    else:
        chain.reverse()
        parts = chain + [key]  # 无 id 祖先：祖先键路径链兜底（拟例 scope-page_strategy）
    base = slugify("-".join(parts))
    cand, n = base, 1
    while cand in _HEADING_SEEN:
        n += 1
        cand = f"{base}-{n}"
    _HEADING_SEEN[cand] = 1
    return cand
