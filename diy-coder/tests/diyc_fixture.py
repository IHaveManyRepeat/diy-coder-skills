# -*- coding: utf-8 -*-
"""diyc 测试共享夹具：临时项目根 + 迷你产物 YAML 工厂。

冻结 API（W2/W3 只读引用，签名不得改）：
  make_project(root) -> Path                    建 <root>/diy-coder.yaml（paths.output_dir: diy-output）
  write_doc(project_root, name, data) -> Path   写 <root>/diy-output/<name>.yaml；data 为 dict（safe_dump）
                                                或 str（原样，供损坏 YAML 夹具）
  read_doc(project_root, name) -> dict          读回（文件缺失 raise FileNotFoundError，断言写回结果用）
- 全部写临时目录，绝不触碰真实 diy-output（契约 §9）。
- 迷你文档只含规则所需字段，字段形状对齐 diy-output 真产物（契约 §6）。
"""
import shutil
import tempfile
from pathlib import Path

import yaml

DEFAULT_OUTPUT_DIR = "diy-output"


def make_project(root) -> Path:
    """在给定 root 下建/覆盖 diy-coder.yaml，返回 Path(root)。"""
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    (root / "diy-coder.yaml").write_text(
        "paths:\n  output_dir: %s\n" % DEFAULT_OUTPUT_DIR, encoding="utf-8")
    return root


def make_root() -> Path:
    """临时项目根便捷构造（tempdir + make_project），返回 Path。"""
    return make_project(Path(tempfile.mkdtemp(prefix="diyc-fixture-")))


def cleanup(root):
    shutil.rmtree(str(root), ignore_errors=True)


def out_dir(root, instance=None) -> str:
    """产物目录路径（不创建）：<root>/<output_dir>[/<instance>]。"""
    p = Path(root) / DEFAULT_OUTPUT_DIR
    return str(p / instance) if instance else str(p)


def _doc_path(project_root, name) -> Path:
    filename = str(name) if str(name).endswith(".yaml") else "%s.yaml" % name
    return Path(project_root) / DEFAULT_OUTPUT_DIR / filename


def write_doc(project_root, name, data) -> Path:
    """落盘一份产物（第一参数为项目根；name 为文档名如 stories/test-plan，可带 .yaml）。

    data 为 dict（safe_dump）或 str（原样写入，供损坏 YAML 夹具）；返回文件路径。
    """
    path = _doc_path(project_root, name)
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, str):
        text = data
    else:
        text = yaml.safe_dump(data, allow_unicode=True, sort_keys=False,
                              default_flow_style=False)
    path.write_text(text, encoding="utf-8")
    return path


def read_doc(project_root, name) -> dict:
    """读回产物（空文件 → {}）；文件缺失 raise FileNotFoundError。"""
    return yaml.safe_load(_doc_path(project_root, name).read_text(encoding="utf-8")) or {}


def write_text(path, text) -> Path:
    """写任意文本文件（源码等非产物夹具用）。"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def project_meta(name="diy-coder-skill", status="已定稿"):
    return {"name": name, "status": status, "created": "2026-01-01", "updated": "2026-01-01"}


def ac(ac_id, refs=None, given="夹具 Given", when="夹具 When", then="夹具 Then"):
    return {"id": ac_id, "given": given, "when": when, "then": then,
            "refs": list(refs or [])}


def story(sid, acs=None, status="待办", epic="E-1"):
    return {"id": sid, "epic": epic, "title": "夹具故事 %s" % sid,
            "narrative": "夹具 narrative", "acceptance_criteria": list(acs or []),
            "status": status}


def doc_stories(items, name="diy-coder-skill", status="已定稿"):
    return {"project": project_meta(name, status), "stories": list(items)}


def tc(tc_id, ac_id, status="待办", type_="单元", priority="P0",
       technique="example", kill_target="夹具 kill target", steps=None,
       dimension=None, api_refs=None, radius=None):
    entry = {"id": tc_id, "title": "夹具用例 %s" % tc_id, "ac": ac_id, "type": type_,
             "priority": priority, "technique": technique, "kill_target": kill_target,
             "status": status, "steps": list(steps or ["夹具步骤"])}
    if dimension is not None:
        entry["dimension"] = dimension
    if api_refs is not None:
        entry["api_refs"] = list(api_refs)
    if radius is not None:
        entry["radius"] = radius
    return entry


def gap(ac_id, sid, decision="待办", reason="夹具缺口", note=None):
    g = {"ac": ac_id, "story": sid, "reason": reason, "decision": decision}
    if note is not None:
        g["note"] = note
    return g


def static_check(order, tool, gate="阻断", kills="夹具层"):
    return {"order": order, "tool": tool, "kills": kills, "gate": gate}


def _is_fh_id(value):
    """FH-x.y.z 形态判定（归一化只对自由文本 kill_target 铸 FH）。"""
    if not isinstance(value, str) or not value.startswith("FH-"):
        return False
    parts = value[3:].split(".")
    return len(parts) == 3 and all(p.isdigit() for p in parts)


DIMENSION_AXES = ("正向", "边界", "异常", "安全", "性能")


def doc_test_plan(cases, gaps=None, static_checks=None, name="diy-coder-skill",
                  status="已定稿", fault_hypotheses=None, dimension_audit=None,
                  mutation=None, normalize=True):
    """normalize=True（缺省）＝把旧式夹具升到新 schema：自由文本 kill_target 逐条
    转 FH 条目并回填引用、缺 dimension 的 TC 补「正向」、自动铸五轴 audit——
    存量测试零改动即绿。显式传段或 normalize=False 时原样落盘（红案例用）。"""
    entries = []
    for c in cases:
        entries.append(dict(c))
    if normalize:
        fhs = []
        seq = {}
        for c in entries:
            kt = c.get("kill_target")
            if isinstance(kt, str) and kt.strip() and not _is_fh_id(kt):
                ac_id = c.get("ac")
                ac_key = ac_id if isinstance(ac_id, str) else str(ac_id)
                ac_num = ac_key.split("-", 1)[-1] if "-" in ac_key else ac_key
                z = seq.get(ac_num, 0) + 1
                seq[ac_num] = z
                fh_id = "FH-%s.%d" % (ac_num, z)
                fhs.append({"id": fh_id, "ac": ac_key, "text": kt})
                c["kill_target"] = fh_id
            c.setdefault("dimension", "正向")
        if fault_hypotheses is None and fhs:
            fault_hypotheses = fhs
        if dimension_audit is None:
            ac_order = []
            for c in entries:
                for a in (c["ac"] if isinstance(c.get("ac"), list) else [c.get("ac")]):
                    if a not in ac_order:
                        ac_order.append(a)
            for g in (gaps or []):
                if isinstance(g, dict) and g.get("ac") not in ac_order:
                    ac_order.append(g.get("ac"))
            dimension_audit = []
            for a in ac_order:
                for axis in DIMENSION_AXES:
                    if axis == "正向":
                        ids = [c["id"] for c in entries
                               if a in (c["ac"] if isinstance(c.get("ac"), list)
                                        else [c.get("ac")])]
                        if ids:
                            dimension_audit.append({"ac": a, "axis": axis, "tcs": ids})
                        else:
                            dimension_audit.append(
                                {"ac": a, "axis": axis,
                                 "not_applicable": "夹具缺口轴（无 TC）"})
                    else:
                        dimension_audit.append(
                            {"ac": a, "axis": axis, "not_applicable": "夹具不适用"})
    doc = {"project": project_meta(name, status), "test_cases": entries}
    if static_checks is not None:
        doc["static_checks"] = list(static_checks)
    if gaps is not None:
        doc["coverage_gaps"] = list(gaps)
    if fault_hypotheses is not None:
        doc["fault_hypotheses"] = list(fault_hypotheses)
    if dimension_audit is not None:
        doc["dimension_audit"] = list(dimension_audit)
    if mutation is not None:
        doc["mutation"] = dict(mutation)
    return doc


def task(sid, status="待办", test_refs=None, **extra):
    t = {"story": sid, "status": status, "test_refs": list(test_refs or [])}
    t.update(extra)
    return t


def doc_sprint(tasks, name="diy-coder-skill", status="已定稿"):
    return {"project": project_meta(name, status), "tasks": list(tasks)}
