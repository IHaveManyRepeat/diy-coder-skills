# -*- coding: utf-8 -*-
"""diyc 共享层产物索引：Docs 唯一入口（契约 §5）。"""

import os

from diyc_lib_base import id_sort, load_yaml_checked

# 文档名 → 文件名（契约 §6 形状以 diy-output 实物为准）
DOC_FILES = {
    "prd": "prd.yaml",
    "architecture": "architecture.yaml",
    "openapi": "openapi.yaml",
    "epics": "epics.yaml",
    "stories": "stories.yaml",
    "test-plan": "test-plan.yaml",
    "sprint": "sprint.yaml",
    "design": "design.yaml",
    "bug-log": "bug-log.yaml",
    # 裁定 22（C·3a · W9）：WDS 线场景大纲纳入注册表——`diyc_check_docs.py` 的
    # architecture `affects` 域要解析 `SC-<nn>` / `SC-<nn>.P<n>`，须经 `Docs` 唯一入口
    # 读（契约 §5 禁旁路读文件）。此前由消费方就地 `setdefault` 补登记（两处真相），
    # 2026-09-28 收口期归位到此处；全库无迭代消费方，加键为纯增量。
    "wds-scenarios": "wds-scenarios.yaml",
}

# ---------------------------------------------------------------- 产物索引

def items(doc, key, of_type=None) -> list:
    """取顶层列表键；缺失/非列表 → []；of_type 在场时仅保留该类型项。"""
    if not isinstance(doc, dict):
        return []
    value = doc.get(key)
    if not isinstance(value, list):
        return []
    if of_type is None:
        return value
    return [x for x in value if isinstance(x, of_type)]


def _ac_ids(tc_entry) -> list:
    """TC 条目的 ac 字段：str 或 list 均接受（形状以产物为准，容错读）。"""
    ac = tc_entry.get("ac")
    if isinstance(ac, str):
        return [ac]
    if isinstance(ac, list):
        return [a for a in ac if isinstance(a, str)]
    return []


class Docs:
    """产物索引层：全部跨文档核对的唯一入口（契约 §5）。解析失败经 yaml_err 可见。"""

    def __init__(self, project_root, output_dir):
        self.project_root = project_root
        self.output_dir = output_dir
        self._cache = {}
        self._errs = {}
        self._err_codes = {}

    # -- 原始文档 ----------------------------------------------------------

    def doc(self, name):
        """name: prd/architecture/openapi/epics/stories/test-plan/sprint/design/bug-log。

        缺失 → None；解析失败/重复键/顶层非映射 → None（错误见 yaml_err）；空文件 → {}。
        """
        if name in self._cache:
            return self._cache[name]
        fname = DOC_FILES[name]
        path = os.path.join(self.output_dir, fname)
        data, code, err = load_yaml_checked(path)
        if err:
            # DUPLICATE_KEY 与 UNPARSABLE_YAML 区分（底单 :364 ⑤：重复键≠解析失败）
            label = "重复键" if code == "DUPLICATE_KEY" else "解析失败"
            self._errs[name] = "YAML %s: %s" % (label, err)
            self._err_codes[name] = code
            data = None
        elif data is not None and not isinstance(data, dict):
            self._errs[name] = "顶层不是映射（实际 %s）" % type(data).__name__
            self._err_codes[name] = "UNPARSABLE_YAML"
            data = None
        self._cache[name] = data
        return data

    def yaml_err(self, name):
        """该文档的解析错误一行中文；无错 → None。"""
        self.doc(name)
        return self._errs.get(name)

    def yaml_err_code(self, name):
        """该文档解析错误的违规码（DUPLICATE_KEY/UNPARSABLE_YAML）；无错 → None。"""
        self.doc(name)
        return self._err_codes.get(name)

    # -- 索引 --------------------------------------------------------------

    def stories(self) -> dict:
        """S-x → story 条目。"""
        d = self.doc("stories") or {}
        return {s["id"]: s for s in items(d, "stories", of_type=dict)
                if isinstance(s.get("id"), str)}

    def acs(self) -> dict:
        """AC-x.y → ac 条目（注入 _story）。"""
        out = {}
        for sid, s in self.stories().items():
            for a in items(s, "acceptance_criteria", of_type=dict):
                if isinstance(a.get("id"), str):
                    entry = dict(a)
                    entry["_story"] = sid
                    out[a["id"]] = entry
        return out

    def tcs(self) -> dict:
        """TC-x.y.z → tc 条目（注入 _story，经 ac 反查；解析不到为 None）。"""
        d = self.doc("test-plan") or {}
        acs = self.acs()
        out = {}
        for t in items(d, "test_cases", of_type=dict):
            if not isinstance(t.get("id"), str):
                continue
            entry = dict(t)
            story = None
            for ac_id in _ac_ids(t):
                hit = acs.get(ac_id)
                if hit is not None:
                    story = hit.get("_story")
                    break
            entry["_story"] = story
            out[t["id"]] = entry
        return out

    def gaps(self) -> dict:
        """AC → coverage_gaps 条目（同一 AC 多条取首条）。"""
        d = self.doc("test-plan") or {}
        out = {}
        for g in items(d, "coverage_gaps", of_type=dict):
            ac = g.get("ac")
            if isinstance(ac, list):
                ac = ac[0] if ac else None
            if isinstance(ac, str) and ac not in out:
                out[ac] = g
        return out

    def frs(self) -> dict:
        """FR-x.y → requirement（注入 _feature）。"""
        d = self.doc("prd") or {}
        out = {}
        for f in items(d, "features", of_type=dict):
            for r in items(f, "requirements", of_type=dict):
                if isinstance(r.get("id"), str):
                    entry = dict(r)
                    entry["_feature"] = f.get("id")
                    out[r["id"]] = entry
        return out

    def nfrs(self) -> dict:
        """NFR-x → 条目。"""
        d = self.doc("prd") or {}
        return {n["id"]: n for n in items(d, "nfrs", of_type=dict)
                if isinstance(n.get("id"), str)}

    def decisions(self) -> dict:
        """D-x → 架构决策条目。"""
        d = self.doc("architecture") or {}
        return {x["id"]: x for x in items(d, "decisions", of_type=dict)
                if isinstance(x.get("id"), str)}

    def epics(self) -> dict:
        """E-x → epic 条目。"""
        d = self.doc("epics") or {}
        return {x["id"]: x for x in items(d, "epics", of_type=dict)
                if isinstance(x.get("id"), str)}

    def tasks(self) -> dict:
        """S-x → sprint 任务条目。"""
        d = self.doc("sprint") or {}
        return {t["story"]: t for t in items(d, "tasks", of_type=dict)
                if isinstance(t.get("story"), str)}

    # -- 派生（TDD 门唯一入口） --------------------------------------------

    def tcs_for_story(self, story) -> list:
        """该 story 全部 AC 绑定的 TC id（数字感知排序）。"""
        acs = self.acs()
        wanted = {a_id for a_id, a in acs.items() if a.get("_story") == story}
        bound = [t_id for t_id, t in self.tcs().items()
                 if wanted.intersection(_ac_ids(t))]
        return id_sort(bound)

    def story_covered(self, story) -> tuple:
        """(covered, 缺覆盖 AC 列表)——TDD 门（PENDING_UNCOVERED）与 reconcile 唯一定义源。

        缺覆盖 AC = 无任何 TC 绑定，且（无 coverage_gaps 条目 或 decision == 待办）；
        gap decision 为 已豁免 / 接受缺口 → 豁免。story 不存在视为无缺覆盖
        （存在性由调用方单独校验）。
        """
        entry = self.stories().get(story)
        if not entry:
            return True, []
        tcs = self.tcs()
        bound_acs = set()
        for t in tcs.values():
            bound_acs.update(_ac_ids(t))
        gaps = self.gaps()
        missing = []
        for a in items(entry, "acceptance_criteria", of_type=dict):
            ac_id = a.get("id")
            if not isinstance(ac_id, str):
                continue
            if ac_id in bound_acs:
                continue
            g = gaps.get(ac_id)
            if isinstance(g, dict) and g.get("decision") in ("已豁免", "接受缺口"):
                continue
            missing.append(ac_id)
        return (not missing), missing
