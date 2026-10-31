"""diy-viewer 产物页章节目录（TOC）：取数采集＋侧栏渲染＋样式。

深度按层数表（3级=h2/h3/h4、2级=h2/h3、其余=仅 h2）；取数＝section 标题
（带 id 且不在 .card 卡内——卡内标题属条目细节，照裁定排除）。
"""

from html.parser import HTMLParser

from viewer_render import esc

# 章节目录深度表：未列名的产物默认 2 级（仅 h2）
_TOC_DEPTH = {"brief": 4, "prfaq": 4, "analysis": 4, "wds-brief": 4, "wds-trigger": 4,
              "design": 3, "project-context": 3, "learning-progress": 3,
              "wds-scenarios": 3, "wds-design-system": 3, "wds-evolution": 3}


class _TocCollector(HTMLParser):
    """收集带 id、不在 .card 卡内的 h2~h4 标题，按 max_level 截断。"""
    _HLVLS = {"h2": 2, "h3": 3, "h4": 4}

    def __init__(self, max_level: int):
        super().__init__()
        self.max_level, self.entries, self._card = max_level, [], 0  # entries=[(lvl,id,text)]
        self._hlvl = self._hid = None
        self._buf = []

    def handle_starttag(self, tag, attrs):
        if tag == "div":
            self._card += "card" in dict(attrs).get("class", "").split()
        elif tag in self._HLVLS and self._card == 0:
            lvl, aid = self._HLVLS[tag], dict(attrs).get("id")
            if aid and 2 <= lvl <= self.max_level:
                self._hlvl, self._hid, self._buf = lvl, aid, []

    def handle_endtag(self, tag):
        if tag == "div":
            self._card = max(0, self._card - 1)
        elif self._hlvl is not None and tag == "h%d" % self._hlvl:
            self.entries.append((self._hlvl, self._hid, "".join(self._buf).strip()))
            self._hlvl = None

    def handle_data(self, data):
        if self._hlvl is not None:
            self._buf.append(data)


def build_toc(body: str, name: str) -> str:
    """按层数表深度收集 section 标题（排除卡内）→ nav 内容；0 条 → ""（不渲染容器）。"""
    p = _TocCollector(_TOC_DEPTH.get(name, 2))
    p.feed(body)
    if not p.entries:
        return ""
    return '<span class="toc-title">章节目录</span><ul>' + "".join(
        f'<li><a class="lvl{l}" href="#{esc(i)}">{esc(t)}</a></li>' for l, i, t in p.entries) + "</ul>"


TOC_CSS = """
.with-toc{display:flex;max-width:1340px;margin:0 auto;align-items:flex-start}
.with-toc>.toc{position:sticky;top:0;flex:0 0 232px;width:232px;align-self:flex-start;max-height:100vh;overflow-y:auto;border-right:1px solid var(--line);background:#fff;padding:20px 14px;box-sizing:border-box}
.with-toc>main{flex:1 1 auto;min-width:0;margin:0;max-width:1080px}
.toc .toc-title{font-weight:700;color:var(--mut);font-size:.75em;letter-spacing:.08em;margin:0 0 8px}
.toc ul{list-style:none;margin:0;padding:0}.toc li{margin:1px 0}
.toc a{display:block;color:var(--ink);text-decoration:none;padding:3px 8px;border-radius:5px;font-size:.9em;line-height:1.45;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.toc a:hover{background:#eef2f7;color:var(--accent)}.toc a.lvl2{font-weight:600}.toc a.lvl3{padding-left:20px}.toc a.lvl4{padding-left:32px;color:var(--mut)}
@media(max-width:1023px){.with-toc>.toc{display:none}}
"""
