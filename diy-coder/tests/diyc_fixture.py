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


def project_meta(name="diy-coder-skill", status="final"):
    return {"name": name, "status": status, "created": "2026-01-01", "updated": "2026-01-01"}


def ac(ac_id, refs=None, given="夹具 Given", when="夹具 When", then="夹具 Then"):
    return {"id": ac_id, "given": given, "when": when, "then": then,
            "refs": list(refs or [])}


def story(sid, acs=None, status="pending", epic="E-1"):
    return {"id": sid, "epic": epic, "title": "夹具故事 %s" % sid,
            "narrative": "夹具 narrative", "acceptance_criteria": list(acs or []),
            "status": status}


def doc_stories(items, name="diy-coder-skill", status="final"):
    return {"project": project_meta(name, status), "stories": list(items)}


def tc(tc_id, ac_id, status="pending", type_="unit", priority="P0",
       technique="example", kill_target="夹具 kill target", steps=None):
    return {"id": tc_id, "title": "夹具用例 %s" % tc_id, "ac": ac_id, "type": type_,
            "priority": priority, "technique": technique, "kill_target": kill_target,
            "status": status, "steps": list(steps or ["夹具步骤"])}


def gap(ac_id, sid, decision="pending", reason="夹具缺口", note=None):
    g = {"ac": ac_id, "story": sid, "reason": reason, "decision": decision}
    if note is not None:
        g["note"] = note
    return g


def static_check(order, tool, gate="blocking", kills="夹具层"):
    return {"order": order, "tool": tool, "kills": kills, "gate": gate}


def doc_test_plan(cases, gaps=None, static_checks=None, name="diy-coder-skill", status="final"):
    doc = {"project": project_meta(name, status), "test_cases": list(cases)}
    if static_checks is not None:
        doc["static_checks"] = list(static_checks)
    if gaps is not None:
        doc["coverage_gaps"] = list(gaps)
    return doc


def task(sid, status="pending", test_refs=None, **extra):
    t = {"story": sid, "status": status, "test_refs": list(test_refs or [])}
    t.update(extra)
    return t


def doc_sprint(tasks, name="diy-coder-skill", status="final"):
    return {"project": project_meta(name, status), "tasks": list(tasks)}
