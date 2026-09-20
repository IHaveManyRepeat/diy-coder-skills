# -*- coding: utf-8 -*-
"""diyc check 规则引擎测试（契约 §4.2；批次 3 TDD 交付）。

覆盖：
- 8 类型各自至少一红一绿（prd/architecture/openapi/epics/stories/test-plan/sprint/review）
- PENDING_UNCOVERED 三态（无条目→违规；decision: 待办→违规；已豁免 / 接受缺口→豁免）
- 跨文件真值：已完成任务 vs stories/test-plan 不一致 → STATUS_MISMATCH；
  待审查任务 evidence 缺失 → EVIDENCE_MISSING
- --previous 稳定 ID 集合（ID_UNSTABLE）
- openapi 缺席 = ok + warning；openapi 3.1 轻量结构自检
- review verdict / route / kill_target 校验；UNPARSABLE_YAML

夹具 tests/diyc_fixture.py 为 W1 冻结 API（只读引用）；全部落临时目录。
运行：cd diy-coder && python -m unittest discover -s tests -v
"""
import argparse
import os
import sys
import unittest
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "skills" / "diy-tools" / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(HERE))

import diyc_check  # noqa: E402
import diyc_fixture as fx  # noqa: E402


def check(root, type_, **kw):
    args = argparse.Namespace(
        project_root=str(root), instance=None, output_dir=fx.out_dir(root),
        type=type_, final=kw.get("final", False), previous=kw.get("previous"),
        story=kw.get("story"), json=True)
    return diyc_check.run(args)


def codes(result):
    return {x["code"] for x in result["violations"]}


def msgs(result):
    return " | ".join(x["msg"] for x in result["violations"])


def other_drive_dir(root):
    """与 root 不同盘符的现存目录（Windows 多盘；无第二盘 / POSIX → None）。"""
    cur = os.path.splitdrive(os.path.abspath(str(root)))[0].upper()
    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        drive = "%s:" % letter
        if drive.upper() != cur and os.path.isdir(drive + os.sep):
            return drive + os.sep
    return None


def prd_doc(frs=None, nfrs=None, **over):
    doc = {
        "project": fx.project_meta(),
        "purpose": "夹具产品目的",
        "goals": [{"id": "G-1", "goal": "目标", "metric": "指标"}],
        "users": [{"id": "U-1", "name": "用户", "need": "需求"}],
        "features": [{"id": "F-1", "name": "组", "description": "说明",
                      "requirements": list(frs or [
                          {"id": "FR-1.1", "statement": "应当便于夹具", "priority": "必须"}])}],
        "nfrs": list(nfrs or [{"id": "NFR-1", "statement": "非功能"}]),
    }
    doc.update(over)
    return doc


def arch_doc(decisions=None, **over):
    doc = {
        "project": fx.project_meta(),
        "decisions": list(decisions or [{
            "id": "D-1", "title": "决策", "decision": "选了 A", "rationale": "理由",
            "alternatives": [{"option": "B", "why_not": "更差"}],
            "affects": ["FR-1.1"], "status": "已采纳"}]),
    }
    doc.update(over)
    return doc


def openapi_doc(paths=None, **over):
    doc = {
        "openapi": "3.1.0",
        "x-project": fx.project_meta(),
        "info": {"title": "夹具接口", "version": "0.1.0"},
        "paths": paths if paths is not None else {
            "/users": {"get": {"operationId": "listUsers",
                               "responses": {"200": {"description": "OK"}},
                               "x-fr": ["FR-1.1"]}}},
    }
    doc.update(over)
    return doc


def stories_doc(items, **over):
    return fx.doc_stories(items, **over)


def simple_story(sid="S-1", acs=None, status="待办"):
    return fx.story(sid, acs=acs if acs is not None else [
        fx.ac("AC-1.1", refs=["FR-1.1"])], status=status)


class CheckBase(unittest.TestCase):
    def setUp(self):
        self.root = fx.make_root()

    def tearDown(self):
        fx.cleanup(self.root)


# ---------------------------------------------------------------- prd

class PrdCheckTest(CheckBase):
    def test_clean_prd_passes_with_counts(self):
        fx.write_doc(self.root, "prd", prd_doc())
        r = check(self.root, "prd")
        self.assertTrue(r["ok"], msgs(r))
        self.assertEqual(r["counts"]["frs"], 1)
        self.assertEqual(r["counts"]["goals"], 1)
        self.assertEqual(r["counts"]["features"], 1)

    def test_shape_violations(self):
        doc = prd_doc(frs=[
            {"id": "FR-1.1", "statement": "甲", "priority": "必须"},
            {"id": "FR-1.1", "statement": "重复 ID", "priority": "high"},
            {"id": "FR-1.2", "statement": "", "priority": "必须"},
        ])
        fx.write_doc(self.root, "prd", doc)
        r = check(self.root, "prd")
        self.assertFalse(r["ok"])
        self.assertIn("DUPLICATE_ID", codes(r))
        self.assertIn("ENUM_INVALID", codes(r))
        self.assertIn("EMPTY_FIELD", codes(r))

    def test_final_requires_zero_assumption_and_answered_questions(self):
        doc = prd_doc()
        doc["goals"][0]["goal"] = "[假设] 猜测的目标"
        doc["goals"][0]["metric"] = "正文提到 [假设] 一词不算标记"
        doc["open_questions"] = [{"id": "Q-1", "question": "待定问题", "answer": None}]
        fx.write_doc(self.root, "prd", doc)
        self.assertTrue(check(self.root, "prd")["ok"], "草稿级不应拦 [假设]")
        r = check(self.root, "prd", final=True)
        self.assertIn("ASSUMPTION_PRESENT", codes(r))
        self.assertIn("PENDING_DECISION", codes(r))
        # 判定与 viewer 同源：前缀才算标记，正文提及不误报
        assumption_hits = [x for x in r["violations"] if x["code"] == "ASSUMPTION_PRESENT"]
        self.assertEqual(len(assumption_hits), 1, msgs(r))
        self.assertIn("goals", assumption_hits[0]["where"])

    def test_missing_file(self):
        r = check(self.root, "prd")
        self.assertFalse(r["ok"])
        self.assertEqual(codes(r), {"MISSING_FILE"})

    def test_previous_id_unstable_and_stable(self):
        old = prd_doc(frs=[{"id": "FR-1.1", "statement": "甲", "priority": "必须"},
                           {"id": "FR-1.9", "statement": "旧需求", "priority": "必须"}])
        prev = self.root / "prd.prev.yaml"
        fx.write_text(prev, yaml.safe_dump(old, allow_unicode=True, sort_keys=False))
        fx.write_doc(self.root, "prd", prd_doc())
        r = check(self.root, "prd", previous=str(prev))
        self.assertIn("ID_UNSTABLE", codes(r))
        self.assertIn("FR-1.9", msgs(r))
        # 稳定：旧稿 = 新稿 ID 集合
        fx.write_text(prev, yaml.safe_dump(prd_doc(), allow_unicode=True, sort_keys=False))
        self.assertTrue(check(self.root, "prd", previous=str(prev))["ok"])

    def test_previous_architecture_dcr_ids(self):
        # 遗留小项（rulings §D5 第 5 项）：architecture 纳入 --previous 白名单。
        # 稳定 ID = decisions/D-* + components/C-* + risks/R-*——前缀不同，扁平并集不冲突。
        arch = {"project": {"name": "x", "status": "已定稿",
                            "created": "2026-01-01", "updated": "2026-01-01"},
                "decisions": [{"id": "D-1", "title": "选型", "decision": "选 A",
                               "rationale": "B 落败",
                               "alternatives": [{"option": "B", "why_not": "慢"}],
                               "affects": ["FR-1.1"], "status": "已采纳"}],
                "components": [{"id": "C-1", "name": "核心", "responsibility": "主流程"}],
                "risks": [{"id": "R-1", "risk": "风险", "mitigation": "缓解"}]}
        prev = fx.write_text(self.root / "architecture.prev.yaml",
                             yaml.safe_dump(arch, allow_unicode=True, sort_keys=False))

        fx.write_doc(self.root, "architecture", arch)
        self.assertTrue(check(self.root, "architecture", previous=str(prev))["ok"],
                        "ID 全保留应放行")

        fx.write_doc(self.root, "architecture", dict(arch, risks=[]))
        r = check(self.root, "architecture", previous=str(prev))
        self.assertIn("ID_UNSTABLE", codes(r))
        self.assertIn("R-1", msgs(r))

        # 三个命名空间互不遮蔽：只丢 D-1 须点名 D-1，且不误报 C-1
        fx.write_doc(self.root, "architecture", dict(arch, decisions=[]))
        r2 = check(self.root, "architecture", previous=str(prev))
        self.assertIn("D-1", msgs(r2))
        self.assertNotIn("C-1", msgs(r2))

    def test_previous_relative_resolves_against_project_root(self):
        # V 验证 B1：相对 --previous 按 project-root 解析（与 trace --src 同语义），不随 cwd
        fx.write_doc(self.root, "prd", prd_doc())
        prev_file = self.root / "prd.prev.yaml"
        old = prd_doc(frs=[{"id": "FR-1.1", "statement": "甲", "priority": "必须"},
                           {"id": "FR-1.9", "statement": "旧需求", "priority": "必须"}])
        fx.write_text(prev_file, yaml.safe_dump(old, allow_unicode=True, sort_keys=False))
        elsewhere = fx.make_root()
        cwd = os.getcwd()
        try:
            os.chdir(elsewhere)
            r = check(self.root, "prd", previous="prd.prev.yaml")
            self.assertIn("ID_UNSTABLE", codes(r))          # rc1 按内容，且无 traceback
            self.assertIn("FR-1.9", msgs(r))
            self.assertNotIn("MISSING_FILE", codes(r))
            fx.write_text(prev_file, yaml.safe_dump(prd_doc(), allow_unicode=True, sort_keys=False))
            r2 = check(self.root, "prd", previous="prd.prev.yaml")
            self.assertTrue(r2["ok"], msgs(r2))              # rc0
            r3 = check(self.root, "prd", previous="no-such.yaml")
            self.assertFalse(r3["ok"])                       # 不存在 → 优雅 MISSING_FILE
            self.assertEqual(codes(r3), {"MISSING_FILE"})
        finally:
            os.chdir(cwd)
            fx.cleanup(elsewhere)

    def test_previous_relative_across_drive_cwd_no_crash(self):
        # V 验证 B1 复现场景：cwd 与 project-root 跨盘，相对 --previous 曾抛未捕获 ValueError
        other = other_drive_dir(self.root)
        if not other:
            self.skipTest("无第二盘符可切（单盘 / POSIX）")
        fx.write_doc(self.root, "prd", prd_doc())
        fx.write_text(self.root / "prd.prev.yaml",
                      yaml.safe_dump(prd_doc(), allow_unicode=True, sort_keys=False))
        cwd = os.getcwd()
        try:
            try:
                os.chdir(other)                              # cwd 与 project-root 不同盘
            except OSError:
                self.skipTest("无法切换到 %s" % other)
            r = check(self.root, "prd", previous="prd.prev.yaml")
        finally:
            os.chdir(cwd)
        self.assertTrue(r["ok"], msgs(r))


# ---------------------------------------------------------------- architecture

class ArchitectureCheckTest(CheckBase):
    def test_clean_architecture_passes(self):
        fx.write_doc(self.root, "prd", prd_doc())
        fx.write_doc(self.root, "architecture", arch_doc())
        r = check(self.root, "architecture")
        self.assertTrue(r["ok"], msgs(r))
        self.assertEqual(r["counts"], {"decisions": 1, "已采纳": 1, "待定": 0})

    def test_affects_dangling_unknown_id(self):
        fx.write_doc(self.root, "prd", prd_doc())
        fx.write_doc(self.root, "architecture", arch_doc(decisions=[{
            "id": "D-1", "title": "决策", "decision": "A", "rationale": "r",
            "alternatives": [{"option": "B", "why_not": "w"}],
            "affects": ["FR-9.9"], "status": "已采纳"}]))
        r = check(self.root, "architecture")
        self.assertIn("UNKNOWN_ID", codes(r))
        self.assertIn("FR-9.9", msgs(r))

    def test_no_alternative_and_final_forbids_proposed(self):
        fx.write_doc(self.root, "prd", prd_doc())
        fx.write_doc(self.root, "architecture", arch_doc(decisions=[{
            "id": "D-1", "title": "决策", "decision": "A", "rationale": "r",
            "alternatives": [], "affects": ["FR-1.1"], "status": "待定"}]))
        r = check(self.root, "architecture", final=True)
        self.assertIn("EMPTY_FIELD", codes(r))
        self.assertIn("PENDING_DECISION", codes(r))


# ---------------------------------------------------------------- openapi

class OpenapiCheckTest(CheckBase):
    def test_absent_is_ok_with_warning(self):
        r = check(self.root, "openapi")
        self.assertTrue(r["ok"], msgs(r))
        self.assertTrue(r["warnings"])
        self.assertEqual(r["counts"], {})
        self.assertTrue(check(self.root, "openapi", final=True)["ok"],
                        "缺席 + --final 仍应合法跳过")

    def test_structure_self_check_and_clean_pass(self):
        bad = openapi_doc(paths={"/users": {
            "fetch": {"operationId": "listUsers", "responses": {}},
            "get": {"operationId": "listUsers", "responses": {}},
            "post": {"operationId": "createUser", "x-fr": ["FR-1.1"]}}})
        bad["openapi"] = "3.0.0"
        bad["paths"]["users"] = {"get": {"operationId": "listUsers",
                                         "responses": {"200": {"description": "OK"}},
                                         "x-fr": ["FR-1.1"]}}
        fx.write_doc(self.root, "prd", prd_doc())
        fx.write_doc(self.root, "openapi", bad)
        r = check(self.root, "openapi", final=True)
        got = codes(r)
        self.assertIn("ENUM_INVALID", got, "版本前缀/paths 键/method 越界未拦")
        self.assertIn("DUPLICATE_ID", got, "operationId 未查重")
        self.assertIn("EMPTY_FIELD", got, "responses 缺失未拦")
        # 修正版通过
        fx.write_doc(self.root, "openapi", openapi_doc())
        r2 = check(self.root, "openapi", final=True)
        self.assertTrue(r2["ok"], msgs(r2))
        self.assertEqual(r2["counts"], {"paths": 1, "operations": 1})

    def test_xfr_dangling_unknown_id(self):
        fx.write_doc(self.root, "prd", prd_doc())
        fx.write_doc(self.root, "openapi", openapi_doc(paths={
            "/users": {"get": {"operationId": "listUsers",
                               "responses": {"200": {"description": "OK"}},
                               "x-fr": ["FR-9.9"]}}}))
        r = check(self.root, "openapi")
        self.assertIn("UNKNOWN_ID", codes(r))


# ---------------------------------------------------------------- epics

class EpicsCheckTest(CheckBase):
    def _doc(self, **over):
        doc = {"project": fx.project_meta(), "epics": [
            {"id": "E-1", "title": "史诗", "goal": "目标",
             "feature_refs": ["F-1"], "status": "待办"}]}
        doc.update(over)
        return doc

    def test_clean_epics_passes(self):
        fx.write_doc(self.root, "epics", self._doc())
        r = check(self.root, "epics")
        self.assertTrue(r["ok"], msgs(r))
        self.assertEqual(r["counts"], {"epics": 1})

    def test_duplicate_and_enum(self):
        fx.write_doc(self.root, "epics", self._doc(epics=[
            {"id": "E-1", "title": "甲", "goal": "g", "feature_refs": ["F-1"],
             "status": "待办"},
            {"id": "E-1", "title": "乙", "goal": "g", "feature_refs": ["F-2"],
             "status": "finished"}]))
        r = check(self.root, "epics")
        self.assertIn("DUPLICATE_ID", codes(r))
        self.assertIn("ENUM_INVALID", codes(r))


# ---------------------------------------------------------------- stories

class StoriesCheckTest(CheckBase):
    def test_clean_stories_passes_with_counts(self):
        fx.write_doc(self.root, "prd", prd_doc())
        fx.write_doc(self.root, "stories", stories_doc([simple_story()]))
        r = check(self.root, "stories")
        self.assertTrue(r["ok"], msgs(r))
        self.assertEqual(r["counts"]["stories"], 1)
        self.assertEqual(r["counts"]["acs"], 1)
        self.assertEqual(r["counts"]["must_frs"], 1)

    def test_shape_and_dangling_refs(self):
        fx.write_doc(self.root, "prd", prd_doc())
        bad_ac = {"id": "AC-1.1", "given": "g", "when": "w", "then": "",
                  "refs": ["FR-9.9"]}
        fx.write_doc(self.root, "stories", stories_doc([simple_story(acs=[bad_ac])]))
        r = check(self.root, "stories")
        self.assertIn("UNKNOWN_ID", codes(r), "refs 悬空未拦")
        self.assertIn("EMPTY_FIELD", codes(r), "then 为空未拦")
        # AC 重复
        fx.write_doc(self.root, "stories", stories_doc([simple_story(acs=[
            fx.ac("AC-1.1", refs=["FR-1.1"]), fx.ac("AC-1.1", refs=["FR-1.1"])])]))
        self.assertIn("DUPLICATE_ID", codes(check(self.root, "stories")))

    def test_final_requires_must_fr_coverage(self):
        fx.write_doc(self.root, "prd", prd_doc(frs=[
            {"id": "FR-1.1", "statement": "甲", "priority": "必须"},
            {"id": "FR-1.2", "statement": "乙", "priority": "必须"},
            {"id": "FR-1.3", "statement": "丙", "priority": "应该"}]))
        fx.write_doc(self.root, "stories", stories_doc([simple_story()]))
        r = check(self.root, "stories", final=True)
        self.assertIn("SET_MISMATCH", codes(r))
        self.assertIn("FR-1.2", msgs(r))
        self.assertNotIn("FR-1.3", msgs(r), "应该级 FR 不在必须覆盖范围")

    def test_design_ref_must_resolve(self):
        fx.write_doc(self.root, "prd", prd_doc())
        ac = {"id": "AC-1.1", "given": "g", "when": "w", "then": "t",
              "refs": ["FR-1.1"], "design_ref": "P-1"}
        fx.write_doc(self.root, "stories", stories_doc([simple_story(acs=[ac])]))
        r = check(self.root, "stories")
        self.assertIn("UNKNOWN_ID", codes(r), "design.yaml 缺席时 design_ref 未拦")


# ---------------------------------------------------------------- test-plan

class TestPlanCheckTest(CheckBase):
    def _env(self, cases=None, gaps=None):
        fx.write_doc(self.root, "prd", prd_doc())
        fx.write_doc(self.root, "stories", stories_doc([simple_story()]))
        fx.write_doc(self.root, "test-plan", fx.doc_test_plan(
            cases if cases is not None else [
                fx.tc("TC-1.1.1", "AC-1.1", technique="边界")],
            gaps=gaps))

    def test_clean_test_plan_passes_with_counts(self):
        self._env()
        r = check(self.root, "test-plan")
        self.assertTrue(r["ok"], msgs(r))
        self.assertEqual(r["counts"]["cases"], 1)
        self.assertEqual(r["counts"]["by_type"], {"单元": 1})
        self.assertEqual(r["counts"]["by_priority"], {"P0": 1})
        self.assertEqual(r["counts"]["acs_covered"], 1)

    def test_technique_and_kill_target_and_dangling_ac(self):
        self._env(cases=[fx.tc("TC-1.1.1", "AC-9.9", technique="example",
                               kill_target="")])
        r = check(self.root, "test-plan")
        got = codes(r)
        self.assertIn("ENUM_INVALID", got, "technique 越界未拦")
        self.assertIn("EMPTY_FIELD", got, "kill_target 为空未拦")
        self.assertIn("UNKNOWN_ID", got, "ac 悬空未拦")

    def test_final_forbids_pending_gap(self):
        self._env(cases=[fx.tc("TC-1.1.1", "AC-1.1", technique="边界")],
                  gaps=[fx.gap("AC-1.2", "S-1", decision="待办")])
        # 补齐 AC-1.2（缺口绑定的 AC 须存在于 stories）
        fx.write_doc(self.root, "stories", stories_doc([simple_story(acs=[
            fx.ac("AC-1.1", refs=["FR-1.1"]), fx.ac("AC-1.2", refs=["FR-1.1"])])]))
        draft = check(self.root, "test-plan")
        self.assertTrue(draft["ok"], "草稿级不应拦 decision: 待办 缺口：%s" % msgs(draft))
        r = check(self.root, "test-plan", final=True)
        self.assertIn("PENDING_DECISION", codes(r))
        # 已豁免缺口不拦定稿
        self._env(cases=[fx.tc("TC-1.1.1", "AC-1.1", technique="边界")],
                  gaps=[fx.gap("AC-1.2", "S-1", decision="已豁免", note="2026-01-01 用户确认")])
        fx.write_doc(self.root, "stories", stories_doc([simple_story(acs=[
            fx.ac("AC-1.1", refs=["FR-1.1"]), fx.ac("AC-1.2", refs=["FR-1.1"])])]))
        self.assertTrue(check(self.root, "test-plan", final=True)["ok"])

    def test_waived_gap_requires_note(self):
        self._env(cases=[fx.tc("TC-1.1.1", "AC-1.1", technique="边界")],
                  gaps=[fx.gap("AC-1.2", "S-1", decision="已豁免")])
        fx.write_doc(self.root, "stories", stories_doc([simple_story(acs=[
            fx.ac("AC-1.1", refs=["FR-1.1"]), fx.ac("AC-1.2", refs=["FR-1.1"])])]))
        self.assertIn("EMPTY_FIELD", codes(check(self.root, "test-plan")))


# ---------------------------------------------------------------- sprint

class SprintCheckTest(CheckBase):
    def _env(self, tasks, story_status="待办", tc_status="待办",
             acs=None, gaps=None, tc_kw=None):
        fx.write_doc(self.root, "prd", prd_doc())
        fx.write_doc(self.root, "stories", stories_doc(
            [simple_story(status=story_status, acs=acs)]))
        kwargs = {"technique": "边界"}
        kwargs.update(tc_kw or {})
        fx.write_doc(self.root, "test-plan", fx.doc_test_plan(
            [fx.tc("TC-1.1.1", "AC-1.1", status=tc_status, **kwargs)], gaps=gaps))
        fx.write_doc(self.root, "sprint", fx.doc_sprint(tasks))

    def test_clean_sprint_passes_with_counts(self):
        self._env([fx.task("S-1", status="待办", test_refs=["TC-1.1.1"])])
        r = check(self.root, "sprint")
        self.assertTrue(r["ok"], msgs(r))
        self.assertEqual(r["counts"]["tasks_by_status"], {"待办": 1})
        self.assertEqual(r["counts"]["blocked"], 0)
        self.assertEqual(r["counts"]["gated"], 1)

    def test_blocked_without_reason_and_dangling_refs(self):
        self._env([fx.task("S-1", status="已阻塞", test_refs=["TC-9.9.9"])])
        r = check(self.root, "sprint")
        got = codes(r)
        self.assertIn("BLOCKED_NO_REASON", got)
        self.assertIn("UNKNOWN_ID", got)
        # 重复任务（story 键重复）
        self._env([fx.task("S-1"), fx.task("S-1")])
        self.assertIn("DUPLICATE_ID", codes(check(self.root, "sprint")))
        # evidence 条目形状异常（非映射）
        self._env([fx.task("S-1", status="待审查", evidence=["裸字符串"])])
        self.assertIn("EMPTY_FIELD", codes(check(self.root, "sprint")))

    def test_pending_uncovered_three_states(self):
        # 夹具 story 的 AC-1.2 无任何 TC 绑定（TC-1.1.1 绑的是 AC-1.1）
        uncovered_acs = [fx.ac("AC-1.2", refs=["FR-1.1"])]
        # 1) 无 TC 且无 gap 条目 → 违规
        self._env([fx.task("S-1", status="待办")], acs=uncovered_acs)
        r = check(self.root, "sprint")
        self.assertIn("PENDING_UNCOVERED", codes(r))
        self.assertIn("AC-1.2", msgs(r))
        # 2) gap decision: 待办 → 违规
        self._env([fx.task("S-1", status="待办")], acs=uncovered_acs,
                  gaps=[fx.gap("AC-1.2", "S-1", decision="待办")])
        self.assertIn("PENDING_UNCOVERED", codes(check(self.root, "sprint")))
        # 3) 已豁免 → 豁免；接受缺口 → 豁免
        for decision in ("已豁免", "接受缺口"):
            self._env([fx.task("S-1", status="待办")], acs=uncovered_acs,
                      gaps=[fx.gap("AC-1.2", "S-1", decision=decision,
                                   note="2026-01-01 用户确认")])
            r = check(self.root, "sprint")
            self.assertTrue(r["ok"], "%s 缺口应豁免：%s" % (decision, msgs(r)))
        # 4) 已绑 TC → 覆盖
        self._env([fx.task("S-1", status="待办", test_refs=["TC-1.1.1"])])
        self.assertTrue(check(self.root, "sprint")["ok"])
        # 5) 已完成任务不适用 TDD 门（已完成 story 豁免）
        self._env([fx.task("S-1", status="已完成")], story_status="已完成")
        self.assertNotIn("PENDING_UNCOVERED", codes(check(self.root, "sprint")))

    def test_cross_file_truth_done_task(self):
        self._env([fx.task("S-1", status="已完成", test_refs=["TC-1.1.1"])])
        r = check(self.root, "sprint")
        got = codes(r)
        self.assertIn("STATUS_MISMATCH", got, "已完成任务 vs 未完成 story / 未通过 TC")
        # 修正两个真源 → 通过
        self._env([fx.task("S-1", status="已完成", test_refs=["TC-1.1.1"])],
                  story_status="已完成", tc_status="通过")
        r2 = check(self.root, "sprint")
        self.assertTrue(r2["ok"], msgs(r2))

    def test_final_set_equality_and_assumption(self):
        fx.write_doc(self.root, "prd", prd_doc())
        fx.write_doc(self.root, "stories", stories_doc(
            [simple_story("S-1"), simple_story("S-2", acs=[fx.ac("AC-2.1", refs=["FR-1.1"])])]))
        fx.write_doc(self.root, "test-plan", fx.doc_test_plan(
            [fx.tc("TC-1.1.1", "AC-1.1", technique="边界"),
             fx.tc("TC-2.1.1", "AC-2.1", technique="边界")]))
        fx.write_doc(self.root, "sprint", fx.doc_sprint(
            [fx.task("S-1", status="已阻塞", blocked_reason="[假设] 待确认")]))
        r = check(self.root, "sprint", final=True)
        got = codes(r)
        self.assertIn("SET_MISMATCH", got, "任务集与 story 集不等未拦")
        self.assertIn("ASSUMPTION_PRESENT", got)

    def test_story_scope_narrows(self):
        fx.write_doc(self.root, "prd", prd_doc())
        fx.write_doc(self.root, "stories", stories_doc(
            [simple_story("S-1"), simple_story("S-2", acs=[fx.ac("AC-2.1", refs=["FR-1.1"])])]))
        fx.write_doc(self.root, "test-plan", fx.doc_test_plan([]))
        fx.write_doc(self.root, "sprint", fx.doc_sprint([
            fx.task("S-1", status="待办", test_refs=["TC-1.1.1"]),
            fx.task("S-2", status="待办")]))
        r = check(self.root, "sprint", story="S-2")
        self.assertIn("PENDING_UNCOVERED", codes(r))
        self.assertNotIn("S-1", msgs(r), "--story 未收窄检查面")
        r2 = check(self.root, "sprint", story="S-9")
        self.assertIn("UNKNOWN_ID", codes(r2))


# ---------------------------------------------------------------- review

class ReviewCheckTest(CheckBase):
    def _env(self, task, tc_status="待办", tc_kw=None):
        fx.write_doc(self.root, "prd", prd_doc())
        fx.write_doc(self.root, "stories", stories_doc([simple_story()]))
        kwargs = {"technique": "边界"}
        kwargs.update(tc_kw or {})
        fx.write_doc(self.root, "test-plan", fx.doc_test_plan(
            [fx.tc("TC-1.1.1", "AC-1.1", status=tc_status, **kwargs)]))
        fx.write_doc(self.root, "sprint", fx.doc_sprint([task]))

    def test_evidence_missing_and_status_mismatch(self):
        # 待审查任务无 evidence 条目 → EVIDENCE_MISSING
        self._env(fx.task("S-1", status="待审查", test_refs=["TC-1.1.1"]))
        r = check(self.root, "review")
        self.assertIn("EVIDENCE_MISSING", codes(r))
        # 有 green 记录但 test-plan status 仍待办 → STATUS_MISMATCH
        self._env(fx.task("S-1", status="待审查", test_refs=["TC-1.1.1"], evidence=[
            {"tc": "TC-1.1.1", "red": "2026-01-01 失败", "green": "2026-01-01 通过"}]))
        r2 = check(self.root, "review")
        self.assertEqual(codes(r2), {"STATUS_MISMATCH"}, msgs(r2))
        # 台账完整且 TC 通过 → 通过
        self._env(fx.task("S-1", status="待审查", test_refs=["TC-1.1.1"], evidence=[
            {"tc": "TC-1.1.1", "red": "2026-01-01 失败", "green": "2026-01-01 通过"}]),
            tc_status="通过")
        self.assertTrue(check(self.root, "review")["ok"], msgs(check(self.root, "review")))

    def test_verdict_and_route_rules(self):
        base = fx.task("S-1", status="待审查", test_refs=["TC-1.1.1"], evidence=[
            {"tc": "TC-1.1.1", "red": "r", "green": "g"}])
        # verdict 非法 → ENUM_INVALID
        base["review"] = {"at": "2026-01-01", "verdict": "maybe", "findings": []}
        self._env(dict(base), tc_status="通过")
        self.assertIn("ENUM_INVALID", codes(check(self.root, "review")))
        # route 非法 → ROUTE_INVALID
        base["review"] = {"at": "2026-01-01", "verdict": "失败", "findings": [
            {"layer": "正确性", "route": "later", "note": "x"}]}
        self._env(dict(base), tc_status="通过")
        self.assertIn("ROUTE_INVALID", codes(check(self.root, "review")))
        # 通过 但含非后置发现 → ROUTE_INVALID
        base["review"] = {"at": "2026-01-01", "verdict": "通过", "findings": [
            {"layer": "正确性", "route": "小修", "note": "x"}]}
        self._env(dict(base), tc_status="通过")
        self.assertIn("ROUTE_INVALID", codes(check(self.root, "review")))
        # 失败 但全部后置 → ROUTE_INVALID
        base["review"] = {"at": "2026-01-01", "verdict": "失败", "findings": [
            {"layer": "覆盖审计", "route": "后置", "note": "x"}]}
        self._env(dict(base), tc_status="通过")
        self.assertIn("ROUTE_INVALID", codes(check(self.root, "review")))
        # 干净通过（空 findings）；层非法 → ENUM_INVALID
        base["review"] = {"at": "2026-01-01", "verdict": "通过", "findings": []}
        self._env(dict(base), tc_status="通过")
        r = check(self.root, "review")
        self.assertTrue(r["ok"], msgs(r))
        self.assertEqual(r["counts"]["findings_by_route"], {})
        # kill_target / technique 越界（L3 纪律）
        self._env(fx.task("S-1", status="待审查", test_refs=["TC-1.1.1"], evidence=[
            {"tc": "TC-1.1.1", "red": "r", "green": "g"}]),
            tc_status="通过", tc_kw={"technique": "example", "kill_target": ""})
        got = codes(check(self.root, "review"))
        self.assertIn("ENUM_INVALID", got)
        self.assertIn("EMPTY_FIELD", got)

    def test_story_scope_and_counts(self):
        self._env(fx.task("S-1", status="已完成", test_refs=["TC-1.1.1"], evidence=[
            {"tc": "TC-1.1.1", "red": "r", "green": "g"}],
            review={"at": "2026-01-01", "verdict": "通过", "findings": []}),
            tc_status="通过")
        r = check(self.root, "review")
        self.assertTrue(r["ok"], msgs(r))
        self.assertEqual(r["counts"]["findings_by_layer"], {})
        r2 = check(self.root, "review", story="S-9")
        self.assertIn("UNKNOWN_ID", codes(r2))


# ---------------------------------------------------------------- 通用

class CommonTest(CheckBase):
    def test_unparsable_yaml(self):
        fx.write_doc(self.root, "prd", "project: [unclosed\n")
        r = check(self.root, "prd")
        self.assertFalse(r["ok"])
        self.assertEqual(codes(r), {"UNPARSABLE_YAML"})

    def test_receipt_shape(self):
        fx.write_doc(self.root, "prd", prd_doc())
        r = check(self.root, "prd")
        self.assertEqual(r["command"], "check")
        self.assertIsInstance(r["violations"], list)
        self.assertIsInstance(r["warnings"], list)
        self.assertIsInstance(r["counts"], dict)


if __name__ == "__main__":
    unittest.main()
