"""diy-viewer openapi 页专属渲染（v4·批4b）：总览横表＋功能分组详情竖表＋行锚。

总览＝索引（一屏扫读、找接口，7 列横表）；详情＝说明书（按功能标签分组、每接口
一张两列竖表，能放的都放）。行锚挂详情接口标题 `id=operationId`（4a 引擎查重保证
唯一），总览行内链接跳转。分组序＝顶层 tags 声明序；未匹配/未挂 tags 落「未分组」
殿后（存量不丢行）；多 tag 取首个匹配归组（一行一锚）。竖表两列（字段｜内容）喂入
复用 render_table；总览含行内链接故自拼表格。选填行无值隐藏，核心行无值写「—」。
"""

from viewer_labels import HTTP_METHODS
from viewer_refs import esc, gloss
from viewer_render import cell, key_label, render_table

UNGROUPED = "未分组"

# 核心行（无值写「—」）；其余选填行无值隐藏（任务书 §1.4）
_CORE = ("method", "path", "operationId", "summary")

# 详情行键序（能放的都放——任务书 §1.4 列举序）
_DETAIL_ORDER = (
    "method", "path", "operationId", "summary", "description", "tags", "x-fr",
    "deprecated", "parameters", "requestBody", "responses", "security",
    "externalDocs", "servers", "callbacks",
)


def _join_fr(op: dict) -> str:
    fr = op.get("x-fr")
    if isinstance(fr, list):
        return ", ".join(str(x) for x in fr)
    return fr if isinstance(fr, str) and fr else ""


def _resolve_ref(node, data: dict):
    """局部 $ref（#/components/...）解析；解析不了原样返回。"""
    if isinstance(node, dict) and isinstance(node.get("$ref"), str):
        ref = node["$ref"]
        if ref.startswith("#/"):
            cur = data
            for part in ref[2:].split("/"):
                if isinstance(cur, dict) and part in cur:
                    cur = cur[part]
                else:
                    return node
            return cur
    return node


def _schema_brief(schema) -> str:
    if isinstance(schema, dict):
        if isinstance(schema.get("$ref"), str):
            return schema["$ref"]
        if schema.get("type") is not None:
            return str(schema.get("type"))
    return ""


def _param_brief(params, data: dict) -> str:
    """请求参数简略：`名(位置,必填)`，多个逗号隔开（总览列）。"""
    if not isinstance(params, list):
        return ""
    parts = []
    for p in params:
        r = _resolve_ref(p, data)
        if not isinstance(r, dict):
            continue
        parts.append("%s(%s,%s)" % (r.get("name") or "?", r.get("in") or "?",
                                    "必填" if r.get("required") else "选填"))
    return ", ".join(parts)


def _param_detail(params, data: dict) -> str:
    """请求参数详情：名/位置/必填/类型/说明 逐参数一行。"""
    if not isinstance(params, list):
        return ""
    lines = []
    for p in params:
        r = _resolve_ref(p, data)
        if not isinstance(r, dict):
            continue
        line = "%s｜%s｜%s" % (r.get("name") or "?", r.get("in") or "?",
                              "必填" if r.get("required") else "选填")
        typ = _schema_brief(r.get("schema"))
        if typ:
            line += "｜%s" % typ
        desc = r.get("description")
        if isinstance(desc, str) and desc.strip():
            line += "｜%s" % desc.strip()
        lines.append(line)
    return "\n".join(lines)


def _request_body_detail(rb) -> str:
    """请求体：内容类型→schema/必填/说明。"""
    if not isinstance(rb, dict):
        return ""
    req = "必填" if rb.get("required") else "选填"
    lines = []
    content = rb.get("content")
    if isinstance(content, dict):
        for media, m in content.items():
            brief = _schema_brief(m.get("schema")) if isinstance(m, dict) else ""
            lines.append("%s｜%s%s" % (media, req,
                                      "｜schema: %s" % brief if brief else ""))
    desc = rb.get("description")
    if isinstance(desc, str) and desc.strip():
        lines.append(desc.strip())
    return "\n".join(lines)


def _responses_detail(resp, data: dict) -> str:
    """响应：逐状态码——说明/响应体 schema/响应头。"""
    if not isinstance(resp, dict):
        return ""
    lines = []
    for code, r in resp.items():
        r = _resolve_ref(r, data)
        if not isinstance(r, dict):
            lines.append("%s｜—" % code)
            continue
        desc = r.get("description")
        parts = ["%s｜%s" % (code, desc.strip()
                            if isinstance(desc, str) and desc.strip() else "—")]
        content = r.get("content")
        if isinstance(content, dict):
            for media, m in content.items():
                brief = _schema_brief(m.get("schema")) if isinstance(m, dict) else ""
                if brief:
                    parts.append("  %s schema: %s" % (media, brief))
        headers = r.get("headers")
        if isinstance(headers, dict):
            for hn, hv in headers.items():
                hdesc = (hv.get("description") if isinstance(hv, dict)
                         and isinstance(hv.get("description"), str) else "")
                parts.append("  响应头 %s%s" % (hn, "：%s" % hdesc.strip()
                                               if hdesc.strip() else ""))
        lines.append("\n".join(parts))
    return "\n".join(lines)


def _security_detail(sec) -> str:
    if not isinstance(sec, list):
        return ""
    if not sec:
        return "显式无鉴权"
    parts = []
    for s in sec:
        if isinstance(s, dict):
            parts.append("; ".join(
                "%s(%s)" % (k, ", ".join(str(x) for x in v)) if isinstance(v, list)
                else str(k) for k, v in s.items()))
    return "; ".join(parts)


def _external_docs(ed) -> str:
    if not isinstance(ed, dict):
        return ""
    return "｜".join(str(x) for x in (ed.get("description") or "", ed.get("url") or "")
                     if x)


def _servers_detail(servers) -> str:
    if not isinstance(servers, list):
        return ""
    lines = []
    for s in servers:
        if isinstance(s, dict):
            lines.append(str(s.get("url") or "")
                         + ("｜%s" % s["description"] if isinstance(s.get("description"), str)
                            and s["description"].strip() else ""))
    return "\n".join(lines)


def _callbacks_detail(cbs) -> str:
    if not isinstance(cbs, dict):
        return ""
    lines = []
    for name, c in cbs.items():
        if isinstance(c, dict):
            methods = [m.upper() for m in c if str(m).lower() in HTTP_METHODS]
            lines.append("%s%s" % (name, "：%s" % ", ".join(methods) if methods else ""))
        else:
            lines.append(str(name))
    return "\n".join(lines)


def _detail_text(key: str, item: dict, data: dict, top_security) -> str | None:
    """详情单元格文本；选填空值返回 None（调用方隐藏行），核心行回「—」。"""
    op = item["op"]
    if key == "method":
        return item["method"]
    if key == "path":
        return item["path"]
    if key == "operationId":
        v = op.get("operationId")
        return str(v).strip() if isinstance(v, str) and v.strip() else "—"
    if key == "summary":
        v = op.get("summary")
        return v.strip() if isinstance(v, str) and v.strip() else "—"
    if key == "description":
        v = op.get("description")
        return v.strip() if isinstance(v, str) and v.strip() else None
    if key == "tags":
        v = op.get("tags")
        if isinstance(v, list) and v:
            return ", ".join(str(x) for x in v)
        return None
    if key == "x-fr":
        return _join_fr(op) or None
    if key == "deprecated":
        return "是" if op.get("deprecated") else None
    if key == "parameters":
        return _param_detail(op.get("parameters"), data) or None
    if key == "requestBody":
        return _request_body_detail(op.get("requestBody")) or None
    if key == "responses":
        return _responses_detail(op.get("responses"), data) or None
    if key == "security":
        sec = op.get("security")
        if sec is None or sec == top_security:
            return None  # 仅与顶层不同时展示（任务书 §1.4）
        return _security_detail(sec) or None
    if key == "externalDocs":
        return _external_docs(op.get("externalDocs")) or None
    if key == "servers":
        return _servers_detail(op.get("servers")) or None
    if key == "callbacks":
        return _callbacks_detail(op.get("callbacks")) or None
    return None


def collect_operations(data: dict) -> list:
    """paths 逐 path/method 展开为操作列表（保持文档序）。"""
    ops = []
    for path, item in (data.get("paths") or {}).items():
        if not isinstance(item, dict):
            continue
        for method, op in item.items():
            if method.lower() in HTTP_METHODS and isinstance(op, dict):
                ops.append({"path": path, "method": method.upper(), "op": op})
    return ops


def _declared_groups(data: dict) -> list:
    names = []
    for t in data.get("tags") or []:
        if isinstance(t, dict) and isinstance(t.get("name"), str) and t["name"].strip():
            names.append(t["name"].strip())
    return names


def _op_group(op: dict, declared: list) -> str:
    """多 tag 取首个精确匹配组名的归组（裁定②）；无匹配/未挂 → 未分组。"""
    tags = op.get("tags")
    if isinstance(tags, list):
        for t in tags:
            s = str(t).strip()
            if s in declared:
                return s
    return UNGROUPED


def group_operations(data: dict, ops: list) -> list:
    """[(组名, [ops...])]：顶层 tags 声明序为组序（裁定①），未分组殿后。"""
    declared = _declared_groups(data)
    buckets = {g: [] for g in declared}
    ungrouped = []
    for item in ops:
        g = _op_group(item["op"], declared)
        (buckets[g] if g in buckets else ungrouped).append(item)
    out = [(g, buckets[g]) for g in declared if buckets[g]]
    if ungrouped:
        out.append((UNGROUPED, ungrouped))
    return out


def _render_overview(ops: list, groups: list, data: dict) -> str:
    """总览横表 7 列：方法/路径/操作 ID/摘要/功能组/x-fr/请求参数（简略）。
    操作 ID 单元格行内链接跳详情锚；无 operationId 出纯文本。"""
    group_of = {id(o): g for g, items in groups for o in items}
    th = "".join("<th>%s</th>" % gloss(esc(h)) for h in
                 ("方法", "路径", "操作 ID", "摘要", "功能组", "关联需求", "请求参数"))
    rows = []
    for item in ops:
        op = item["op"]
        oid = str(op.get("operationId") or "").strip()
        oid_html = ('<a href="#%s">%s</a>' % (esc(oid), esc(oid))
                    if oid else cell(op.get("operationId")))
        rows.append(
            "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td>"
            "<td>%s</td><td>%s</td></tr>" % (
                cell(item["method"]), cell(item["path"]), oid_html,
                cell(op.get("summary")), cell(group_of[id(item)]),
                cell(_join_fr(op)), cell(_param_brief(op.get("parameters"), data))))
    return ('<h2 id="api-overview">接口总览</h2><div class="table-scroll">'
            '<table class="data"><thead><tr>%s</tr></thead><tbody>%s</tbody>'
            "</table></div>" % (th, "".join(rows)))


def _render_one(item: dict, data: dict, top_security) -> str:
    """详情区单接口：标题挂 id=operationId 行锚 ＋ 两列竖表（字段｜内容）。"""
    op = item["op"]
    oid = str(op.get("operationId") or "").strip()
    anchor = ' id="%s"' % esc(oid) if oid else ""
    title = "<h4%s>%s</h4>" % (anchor, esc(oid or op.get("summary") or item["path"]))
    rows = []
    for key in _DETAIL_ORDER:
        text = _detail_text(key, item, data, top_security)
        if key in _CORE:
            if text is None:  # 核心行空值兜底
                text = "—"
        elif not text:  # 选填行无值隐藏
            continue
        rows.append({"字段": key_label(key), "内容": text})
    return title + render_table(rows)


def _render_details(groups: list, data: dict) -> str:
    top_security = data.get("security")
    parts = ['<h2 id="api-detail">接口详情</h2>']
    for gname, items in groups:
        parts.append("<h3>%s（%d 个接口）</h3>" % (esc(gname), len(items)))
        for item in items:
            parts.append(_render_one(item, data, top_security))
    return "".join(parts)


def render_openapi_section(data: dict) -> str:
    """openapi 页两层主体：3.1 告警＋总览横表＋分组详情竖表（行锚挂详情标题）。"""
    alerts = []
    version = data.get("openapi")
    if not isinstance(version, str) or not version.startswith("3.1"):
        alerts.append(f"⚠ openapi 字段缺失或非 3.1（当前：{version}）——不符合 OpenAPI 3.1 语法")
    out = "".join(f'<div class="alert">{a}</div>' for a in alerts)
    ops = collect_operations(data)
    if not ops:
        return out
    groups = group_operations(data, ops)
    return out + _render_overview(ops, groups, data) + _render_details(groups, data)
