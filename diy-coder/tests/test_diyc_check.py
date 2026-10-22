# -*- coding: utf-8 -*-
"""diyc check 规则引擎测试（契约 §4.2；批次 3 TDD 交付）。

覆盖：
- 8 类型各自至少一红一绿（prd/architecture/openapi/epics/stories/test-plan/sprint/review）
- PENDING_UNCOVERED 三态（无条目→违规；decision: 待办→违规；已豁免 / 接受缺口→豁免）
- 跨文件真值：已完成任务 vs stories/test-plan 不一致 → STATUS_MISMATCH；
  待审查任务 evidence 缺失 → EVIDENCE_MISSING
- --previous 稳定 ID 集合（ID_UNSTABLE）
- openapi 缺席 = ok + warning；openapi 3.1 轻量结构自检（批 4a：通用错误 $ref /
  功能 tags F-x 解析 / securitySchemes+security 在场；prd 缺席损坏硬 violation）
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


def tc_case(*args, **kwargs):
    """Q-114：夹具 TC 统一带 producer（前向必填，缺失即 EMPTY_FIELD）。

    共享夹具 diyc_fixture.tc 是 W1 冻结面（只读引用），本文件经此包装落默认
    test-design——需要其它生产方值的用例在调用点覆写 case["producer"]。
    """
    case = fx.tc(*args, **kwargs)
    case["producer"] = "test-design"
    return case


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
        "tags": [{"name": "F-1 组"}],
        "security": [],
        "paths": paths if paths is not None else {
            "/users": {"get": {"operationId": "listUsers",
                               "tags": ["F-1 组"],
                               "responses": {
                                   "200": {"description": "OK"},
                                   "404": {"$ref": "#/components/responses/NotFound"}},
                               "x-fr": ["FR-1.1"]}}},
        "components": {
            "responses": {"NotFound": {"description": "资源不存在"}},
            "securitySchemes": {"noop": {"type": "apiKey", "name": "Authorization",
                                         "in": "header", "x-decision": "D-1"}},
        },
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

    # trace: Q-107（stack 铸 ST-### + kind 封闭七类；存量缺 id/kind → warning 不阻塞）
    def test_stack_legacy_missing_id_kind_warns_not_blocks(self):
        fx.write_doc(self.root, "prd", prd_doc())
        fx.write_doc(self.root, "architecture",
                     arch_doc(stack=[{"choice": "html", "why": "静态站"}]))
        r = check(self.root, "architecture")
        self.assertTrue(r["ok"], msgs(r))
        self.assertTrue(any("缺 id" in w for w in r["warnings"]), r["warnings"])
        self.assertTrue(any("缺 kind" in w for w in r["warnings"]), r["warnings"])

    def test_stack_new_shape_passes_without_warnings(self):
        fx.write_doc(self.root, "prd", prd_doc())
        fx.write_doc(self.root, "architecture", arch_doc(stack=[
            {"id": "ST-001", "kind": "frontend", "choice": "html", "why": "静态站"},
            {"id": "ST-002", "kind": "language", "choice": "python", "why": "引擎同栈"}]))
        r = check(self.root, "architecture")
        self.assertTrue(r["ok"], msgs(r))
        stack_warns = [w for w in r["warnings"] if "stack" in w]
        self.assertEqual([], stack_warns, stack_warns)

    def test_stack_invalid_kind_is_violation(self):
        fx.write_doc(self.root, "prd", prd_doc())
        fx.write_doc(self.root, "architecture", arch_doc(stack=[
            {"id": "ST-001", "kind": "database", "choice": "postgres", "why": "存储"}]))
        r = check(self.root, "architecture")
        self.assertIn("ENUM_INVALID", codes(r))
        self.assertIn("database", msgs(r))

    def test_stack_bad_id_format_and_duplicate(self):
        fx.write_doc(self.root, "prd", prd_doc())
        fx.write_doc(self.root, "architecture", arch_doc(stack=[
            {"id": "STACK-1", "kind": "language", "choice": "python", "why": "a"},
            {"id": "ST-002", "kind": "test", "choice": "pytest", "why": "b"},
            {"id": "ST-002", "kind": "lint", "choice": "ruff", "why": "c"}]))
        r = check(self.root, "architecture")
        self.assertIn("ENUM_INVALID", codes(r))
        self.assertIn("DUPLICATE_ID", codes(r))
        self.assertIn("STACK-1", msgs(r))

    def test_stack_frontend_scaffold_at_most_one(self):
        fx.write_doc(self.root, "prd", prd_doc())
        fx.write_doc(self.root, "architecture", arch_doc(stack=[
            {"id": "ST-001", "kind": "frontend", "choice": "react", "why": "a"},
            {"id": "ST-002", "kind": "frontend", "choice": "vue", "why": "b"}]))
        r = check(self.root, "architecture")
        self.assertIn("DUPLICATE_ID", codes(r))
        self.assertIn("frontend", msgs(r))


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

    # trace: v4 批 4a §7-4——五类新用例（通用错误 $ref / tags / F-x / prd 硬门 / 安全面）

    def test_generic_error_ref_missing_red(self):
        fx.write_doc(self.root, "prd", prd_doc())
        fx.write_doc(self.root, "openapi", openapi_doc(paths={
            "/users": {"get": {"operationId": "listUsers", "tags": ["F-1 组"],
                               "responses": {"200": {"description": "OK"}},
                               "x-fr": ["FR-1.1"]}}}))
        r = check(self.root, "openapi")
        self.assertIn("EMPTY_FIELD", codes(r), "通用错误 $ref 缺失未拦")
        self.assertIn("通用错误", msgs(r))

    def test_tags_missing_red(self):
        fx.write_doc(self.root, "prd", prd_doc())
        fx.write_doc(self.root, "openapi", openapi_doc(paths={
            "/users": {"get": {
                "operationId": "listUsers",
                "responses": {"404": {"$ref": "#/components/responses/NotFound"}},
                "x-fr": ["FR-1.1"]}}}))
        r = check(self.root, "openapi")
        self.assertIn("EMPTY_FIELD", codes(r), "tags 缺失未拦")
        self.assertIn("tags", msgs(r))

    def test_tag_feature_anchor_dangling(self):
        fx.write_doc(self.root, "prd", prd_doc())
        fx.write_doc(self.root, "openapi", openapi_doc(paths={
            "/users": {"get": {"operationId": "listUsers", "tags": ["F-9 幽灵功能"],
                               "responses": {"404": {"$ref": "#/components/responses/NotFound"}},
                               "x-fr": ["FR-1.1"]}}}))
        r = check(self.root, "openapi")
        self.assertIn("UNKNOWN_ID", codes(r), "F-x 功能锚悬空未拦")
        self.assertIn("F-9", msgs(r))

    def test_prd_absent_or_corrupt_is_hard_violation(self):
        # 三档总则一档（§7-1 ⑪）：prd 缺席/损坏 → 硬 violation exit 1（废 warning 跳过）
        fx.write_doc(self.root, "openapi", openapi_doc())
        r = check(self.root, "openapi")
        self.assertFalse(r["ok"], "prd 缺席须硬 violation exit 1")
        self.assertIn("UNKNOWN_ID", codes(r))
        self.assertIn("prd.yaml", msgs(r))
        fx.write_doc(self.root, "prd", "foo: [unclosed")
        r2 = check(self.root, "openapi")
        self.assertFalse(r2["ok"], "prd 损坏须硬 violation exit 1")
        self.assertIn("UNKNOWN_ID", codes(r2))

    def test_security_schemes_and_security_absent_red(self):
        fx.write_doc(self.root, "prd", prd_doc())
        doc = openapi_doc()
        del doc["components"]["securitySchemes"]
        del doc["security"]
        fx.write_doc(self.root, "openapi", doc)
        r = check(self.root, "openapi")
        self.assertIn("EMPTY_FIELD", codes(r), "securitySchemes/security 缺席未拦")
        self.assertIn("securitySchemes", msgs(r))
        self.assertIn("security", msgs(r))


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
                tc_case("TC-1.1.1", "AC-1.1", technique="边界")],
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
        self._env(cases=[tc_case("TC-1.1.1", "AC-9.9", technique="example",
                               kill_target="")])
        r = check(self.root, "test-plan")
        got = codes(r)
        self.assertIn("ENUM_INVALID", got, "technique 越界未拦")
        self.assertIn("EMPTY_FIELD", got, "kill_target 为空未拦")
        self.assertIn("UNKNOWN_ID", got, "ac 悬空未拦")

    def test_final_forbids_pending_gap(self):
        self._env(cases=[tc_case("TC-1.1.1", "AC-1.1", technique="边界")],
                  gaps=[fx.gap("AC-1.2", "S-1", decision="待办")])
        # 补齐 AC-1.2（缺口绑定的 AC 须存在于 stories）
        fx.write_doc(self.root, "stories", stories_doc([simple_story(acs=[
            fx.ac("AC-1.1", refs=["FR-1.1"]), fx.ac("AC-1.2", refs=["FR-1.1"])])]))
        draft = check(self.root, "test-plan")
        self.assertTrue(draft["ok"], "草稿级不应拦 decision: 待办 缺口：%s" % msgs(draft))
        r = check(self.root, "test-plan", final=True)
        self.assertIn("PENDING_DECISION", codes(r))
        # 已豁免缺口不拦定稿
        self._env(cases=[tc_case("TC-1.1.1", "AC-1.1", technique="边界")],
                  gaps=[fx.gap("AC-1.2", "S-1", decision="已豁免", note="2026-01-01 用户确认")])
        fx.write_doc(self.root, "stories", stories_doc([simple_story(acs=[
            fx.ac("AC-1.1", refs=["FR-1.1"]), fx.ac("AC-1.2", refs=["FR-1.1"])])]))
        self.assertTrue(check(self.root, "test-plan", final=True)["ok"])

    def test_waived_gap_requires_note(self):
        self._env(cases=[tc_case("TC-1.1.1", "AC-1.1", technique="边界")],
                  gaps=[fx.gap("AC-1.2", "S-1", decision="已豁免")])
        fx.write_doc(self.root, "stories", stories_doc([simple_story(acs=[
            fx.ac("AC-1.1", refs=["FR-1.1"]), fx.ac("AC-1.2", refs=["FR-1.1"])])]))
        self.assertIn("EMPTY_FIELD", codes(check(self.root, "test-plan")))


class FiveAxisCheckTest(CheckBase):
    """五轴矩阵＋FH 落盘＋audit 双向一致（底单五轴批裁定）。"""

    def _env(self, cases, fhs=None, audit=None, mutation=None, **kw):
        fx.write_doc(self.root, "prd", prd_doc())
        fx.write_doc(self.root, "stories", stories_doc([simple_story()]))
        fx.write_doc(self.root, "test-plan", fx.doc_test_plan(
            cases, fault_hypotheses=fhs, dimension_audit=audit,
            mutation=mutation, normalize=False, **kw))

    def _clean_env(self):
        anchor = {"operationId": "opA", "path": "/a", "method": "get"}
        tc = tc_case("TC-1.1.1", "AC-1.1", technique="边界", dimension="正向",
                   kill_target="FH-1.1.1")
        fhs = [{"id": "FH-1.1.1", "ac": "AC-1.1", "text": "夹具故障假设"}]
        audit = [{"ac": "AC-1.1", "axis": "正向", "tcs": ["TC-1.1.1"]}] + [
            {"ac": "AC-1.1", "axis": ax, "not_applicable": "夹具不适用"}
            for ax in ("边界", "异常", "安全", "性能")]
        return tc, fhs, audit, anchor

    def test_missing_fh_section_and_dimension(self):
        self._env([tc_case("TC-1.1.1", "AC-1.1", technique="边界",
                         kill_target="自由文本")])
        r = check(self.root, "test-plan")
        got = codes(r)
        self.assertIn("EMPTY_FIELD", got, "FH 段缺失未拦")
        self.assertIn("ENUM_INVALID", got, "dimension 缺失未拦")

    def test_kill_target_must_reference_fh(self):
        tc, fhs, audit, _ = self._clean_env()
        bad = dict(tc)
        bad["kill_target"] = "FH-9.9.9"
        self._env([bad], fhs=fhs, audit=audit)
        self.assertIn("UNKNOWN_ID", codes(check(self.root, "test-plan")))

    def test_fh_id_must_match_ac(self):
        tc, fhs, audit, _ = self._clean_env()
        bad_fhs = [{"id": "FH-2.1.1", "ac": "AC-1.1", "text": "数字段错位"}]
        self._env([tc], fhs=bad_fhs, audit=audit)
        r = check(self.root, "test-plan")
        self.assertIn("ENUM_INVALID", codes(r), "FH id 与 ac 数字段不对应未拦")

    def test_fh_shape_and_radius(self):
        _, _, audit, _ = self._clean_env()
        self._env([], fhs=[{"id": "FH-1.1.1", "ac": "AC-9.9", "text": "",
                            "radius": "超大"}], audit=audit)
        r = check(self.root, "test-plan")
        got = codes(r)
        self.assertIn("UNKNOWN_ID", got)
        self.assertIn("EMPTY_FIELD", got)
        self.assertIn("ENUM_INVALID", got, "radius 越界未拦")

    def test_audit_missing_cell(self):
        tc, fhs, audit, _ = self._clean_env()
        holey = [e for e in audit if e.get("axis") != "边界"]
        self._env([tc], fhs=fhs, audit=holey)
        r = check(self.root, "test-plan")
        self.assertIn("SET_MISMATCH", codes(r), "缺审计格未拦")
        self.assertIn("AC-1.1/边界", msgs(r))

    def test_audit_tc_not_on_axis(self):
        tc, fhs, _, _ = self._clean_env()
        wrong_dim = dict(tc)
        wrong_dim["dimension"] = "边界"
        audit = [{"ac": "AC-1.1", "axis": "正向", "tcs": ["TC-1.1.1"]}] + [
            {"ac": "AC-1.1", "axis": ax, "not_applicable": "夹具不适用"}
            for ax in ("边界", "异常", "安全", "性能")]
        self._env([wrong_dim], fhs=fhs, audit=audit)
        r = check(self.root, "test-plan")
        self.assertIn("SET_MISMATCH", codes(r), "TC.dimension 与轴不对应未拦")

    def test_audit_reverse_tc_absent_from_axis(self):
        tc, fhs, _, _ = self._clean_env()
        audit = [{"ac": "AC-1.1", "axis": ax, "not_applicable": "夹具不适用"}
                 for ax in ("正向", "边界", "异常", "安全", "性能")]
        self._env([tc], fhs=fhs, audit=audit)
        r = check(self.root, "test-plan")
        self.assertIn("SET_MISMATCH", codes(r), "TC 未被其轴收录未拦")

    def test_done_story_exempts_audit(self):
        tc, fhs, _, _ = self._clean_env()
        fx.write_doc(self.root, "prd", prd_doc())
        fx.write_doc(self.root, "stories", stories_doc(
            [simple_story(status="已完成")]))
        fx.write_doc(self.root, "test-plan", fx.doc_test_plan(
            [tc], fault_hypotheses=fhs, dimension_audit=[], normalize=False))
        r = check(self.root, "test-plan", final=True)
        self.assertTrue(r["ok"], msgs(r))

    def test_final_requires_every_fh_killed(self):
        tc, fhs, _, _ = self._clean_env()
        fhs = fhs + [{"id": "FH-1.1.2", "ac": "AC-1.1", "text": "无人杀我"}]
        audit = [{"ac": "AC-1.1", "axis": "正向", "tcs": ["TC-1.1.1"]}] + [
            {"ac": "AC-1.1", "axis": ax, "not_applicable": "夹具不适用"}
            for ax in ("边界", "异常", "安全", "性能")]
        self._env([tc], fhs=fhs, audit=audit)
        r = check(self.root, "test-plan", final=True)
        self.assertIn("SET_MISMATCH", codes(r), "FH 未被杀未拦")
        self.assertIn("FH-1.1.2", msgs(r))

    def test_final_fh_dual_design_phase_reference_only(self):
        """设计期（全待办）＝引用口径：待办 TC 引用即算被杀。"""
        tc, fhs, audit, _ = self._clean_env()
        tc["status"] = "待办"
        self._env([tc], fhs=fhs, audit=audit)
        r = check(self.root, "test-plan", final=True)
        self.assertTrue(r["ok"], msgs(r))

    def test_final_fh_dual_coding_phase_requires_passed(self):
        """编码期（出现通过/失败）＝收紧：仅 status: 通过 的引用计数。"""
        tc, fhs, audit, _ = self._clean_env()
        tc["status"] = "失败"  # 失败触发编码期，但失败引用不计数
        self._env([tc], fhs=fhs, audit=audit)
        r = check(self.root, "test-plan", final=True)
        self.assertIn("SET_MISMATCH", codes(r), "编码期失败引用未收紧未拦")
        self.assertIn("FH-1.1.1", msgs(r))
        tc["status"] = "通过"
        self._env([tc], fhs=fhs, audit=audit)
        self.assertTrue(check(self.root, "test-plan", final=True)["ok"],
                        "编码期通过引用未放行")

    def test_final_fh_dual_mixed_status(self):
        """混合状态：通过计数、待办不计数——仅被待办引用的 FH 仍红。"""
        tc1, fhs, audit, _ = self._clean_env()
        tc2 = dict(tc1, id="TC-1.1.2", status="待办",
                   kill_target="FH-1.1.2", dimension="正向")
        tc1["status"] = "通过"
        fhs = fhs + [{"id": "FH-1.1.2", "ac": "AC-1.1", "text": "仅待办引用"}]
        audit = [{"ac": "AC-1.1", "axis": "正向",
                  "tcs": ["TC-1.1.1", "TC-1.1.2"]}] + [
            {"ac": "AC-1.1", "axis": ax, "not_applicable": "夹具不适用"}
            for ax in ("边界", "异常", "安全", "性能")]
        self._env([tc1, tc2], fhs=fhs, audit=audit)
        r = check(self.root, "test-plan", final=True)
        self.assertIn("SET_MISMATCH", codes(r), "混合状态待办引用未拦")
        self.assertIn("FH-1.1.2", msgs(r))
        self.assertNotIn("FH-1.1.1", msgs(r))

    def test_mutation_section_shape(self):
        tc, fhs, audit, _ = self._clean_env()
        self._env([tc], fhs=fhs, audit=audit, mutation={"enabled": "yes"})
        self.assertIn("ENUM_INVALID", codes(check(self.root, "test-plan")))
        self._env([tc], fhs=fhs, audit=audit, mutation={"enabled": True, "tool": " "})
        self.assertIn("EMPTY_FIELD", codes(check(self.root, "test-plan")))
        self._env([tc], fhs=fhs, audit=audit,
                  mutation={"enabled": True, "tool": "cosmic-ray"})
        self.assertTrue(check(self.root, "test-plan")["ok"], "合法 mutation 段被拦")


class ApiRefCheckTest(CheckBase):
    """AC/TC api_refs 复合锚＋接口门＋悬空 operation 登记（底单五轴批·e2e 认 ID 裁定）。"""

    ANCHOR = {"operationId": "listUsers", "path": "/users", "method": "get"}

    def _stories_with_anchor(self):
        ac = {"id": "AC-1.1", "given": "g", "when": "w", "then": "t",
              "refs": ["FR-1.1"], "api_refs": [self.ANCHOR]}
        return stories_doc([simple_story(acs=[ac])])

    def _plan_covering_anchor(self):
        tc = tc_case("TC-1.1.1", "AC-1.1", technique="决策表", type_="集成",
                   dimension="正向", kill_target="FH-1.1.1",
                   api_refs=[self.ANCHOR])
        fhs = [{"id": "FH-1.1.1", "ac": "AC-1.1", "text": "夹具故障假设"}]
        audit = [{"ac": "AC-1.1", "axis": "正向", "tcs": ["TC-1.1.1"]}] + [
            {"ac": "AC-1.1", "axis": ax, "not_applicable": "夹具不适用"}
            for ax in ("边界", "异常", "安全", "性能")]
        return tc, fhs, audit

    def test_ac_anchor_shape_and_resolution(self):
        fx.write_doc(self.root, "prd", prd_doc())
        bad = {"operationId": "ghost", "path": "/x", "method": "get"}
        ac = {"id": "AC-1.1", "given": "g", "when": "w", "then": "t",
              "refs": ["FR-1.1"], "api_refs": [bad, {"path": "/users"}]}
        fx.write_doc(self.root, "stories", stories_doc([simple_story(acs=[ac])]))
        fx.write_doc(self.root, "openapi", openapi_doc())
        r = check(self.root, "stories")
        got = codes(r)
        self.assertIn("UNKNOWN_ID", got, "悬空 operationId 未拦")
        self.assertIn("EMPTY_FIELD", got, "复合锚缺键未拦")

    def test_ac_anchor_resolves_when_openapi_present(self):
        fx.write_doc(self.root, "prd", prd_doc())
        fx.write_doc(self.root, "stories", self._stories_with_anchor())
        fx.write_doc(self.root, "openapi", openapi_doc())
        self.assertTrue(check(self.root, "stories")["ok"])

    def test_dangling_operation_requires_skip_line(self):
        fx.write_doc(self.root, "prd", prd_doc())
        fx.write_doc(self.root, "stories", stories_doc([simple_story()]))  # 无锚
        doc = openapi_doc(paths={
            "/users": {"get": {"operationId": "listUsers",
                               "responses": {"200": {"description": "OK"}}}},
            "/health": {"get": {"operationId": "health",
                                "responses": {"200": {"description": "OK"}}}}})
        fx.write_doc(self.root, "openapi", doc)
        r = check(self.root, "stories", final=True)
        self.assertIn("SET_MISMATCH", codes(r), "悬空 operation 未拦")
        self.assertIn("health", msgs(r))
        # notes 登记后放行
        fixed = stories_doc([simple_story()])
        fixed["notes"] = "listUsers: 既有覆盖\nhealth: 无对应需求"
        fx.write_doc(self.root, "stories", fixed)
        self.assertTrue(check(self.root, "stories", final=True)["ok"])

    def test_final_requires_integration_tc_for_anchored_ac(self):
        fx.write_doc(self.root, "prd", prd_doc())
        fx.write_doc(self.root, "stories", self._stories_with_anchor())
        fx.write_doc(self.root, "openapi", openapi_doc())
        tc, fhs, audit = self._plan_covering_anchor()
        # 门红：无任何 TC 点名该锚
        bare = {k: x for k, x in tc.items() if k != "api_refs"}
        fx.write_doc(self.root, "test-plan", fx.doc_test_plan(
            [bare], fault_hypotheses=fhs, dimension_audit=audit, normalize=False))
        r = check(self.root, "test-plan", final=True)
        self.assertIn("SET_MISMATCH", codes(r), "接口用例缺席未拦")
        # 门绿：type 集成＋点名锚
        fx.write_doc(self.root, "test-plan", fx.doc_test_plan(
            [tc], fault_hypotheses=fhs, dimension_audit=audit, normalize=False))
        self.assertTrue(check(self.root, "test-plan", final=True)["ok"])
        # 门红：点名锚但 type 非集成
        wrong = dict(tc)
        wrong["type"] = "单元"
        fx.write_doc(self.root, "test-plan", fx.doc_test_plan(
            [wrong], fault_hypotheses=fhs, dimension_audit=audit, normalize=False))
        self.assertIn("SET_MISMATCH", codes(check(self.root, "test-plan", final=True)))


class RetiredTcCheckTest(CheckBase):
    """Q-111：TC.retired 废弃键（底单 :902-904 三裁）——双键必填/replaced_by 校验/覆盖三层剔除。"""

    FHS = [{"id": "FH-1.1.1", "ac": "AC-1.1", "text": "夹具故障假设"}]
    ANCHOR = {"operationId": "listUsers", "path": "/users", "method": "get"}

    def _env(self, cases, fhs=None, audit=None, final=False):
        fx.write_doc(self.root, "prd", prd_doc())
        fx.write_doc(self.root, "stories", stories_doc([simple_story()]))
        fx.write_doc(self.root, "test-plan", fx.doc_test_plan(
            cases, fault_hypotheses=fhs if fhs is not None else self.FHS,
            dimension_audit=audit, normalize=False))
        return check(self.root, "test-plan", final=final)

    def _base(self, tc_id="TC-1.1.1", **over):
        t = tc_case(tc_id, "AC-1.1", technique="边界", dimension="正向",
                  kill_target="FH-1.1.1")
        t.update(over)
        return t

    def _audit(self, ids):
        return ([{"ac": "AC-1.1", "axis": "正向", "tcs": list(ids)}] +
                [{"ac": "AC-1.1", "axis": ax, "not_applicable": "夹具不适用"}
                 for ax in ("边界", "异常", "安全", "性能")])

    def test_retired_both_keys_required(self):
        # 键在场则双键必填：缺一即 EMPTY_FIELD；形状非映射同样 EMPTY_FIELD
        dead = self._base(retired={"reason": "被取代"})
        r = self._env([dead], audit=self._audit(["TC-1.1.1"]))
        self.assertIn("EMPTY_FIELD", codes(r), "缺 replaced_by 未拦")
        self.assertIn("retired.replaced_by", " | ".join(x["where"] for x in r["violations"]))
        dead = self._base(retired={"replaced_by": "TC-1.1.2"})
        r = self._env([dead], audit=self._audit(["TC-1.1.1"]))
        self.assertIn("EMPTY_FIELD", codes(r), "缺 reason 未拦")
        dead = self._base(retired="已废弃")
        r = self._env([dead], audit=self._audit(["TC-1.1.1"]))
        self.assertIn("EMPTY_FIELD", codes(r), "retired 形状非映射未拦")

    def test_retired_replaced_by_unknown_and_self(self):
        dead = self._base(retired={"reason": "r", "replaced_by": "TC-9.9.9"})
        r = self._env([dead], audit=self._audit(["TC-1.1.1"]))
        self.assertIn("UNKNOWN_ID", codes(r), "replaced_by 悬空未拦")
        dead = self._base(retired={"reason": "r", "replaced_by": "TC-1.1.1"})
        r = self._env([dead], audit=self._audit(["TC-1.1.1"]))
        self.assertIn("SET_MISMATCH", codes(r), "replaced_by 自指未拦")

    def test_retired_excluded_from_counts(self):
        active = self._base()
        dead = self._base("TC-1.1.2",
                          retired={"reason": "重复设计", "replaced_by": "TC-1.1.1"})
        r = self._env([active, dead], audit=self._audit(["TC-1.1.1", "TC-1.1.2"]))
        self.assertTrue(r["ok"], msgs(r))
        self.assertEqual(r["counts"]["cases"], 1, "cases 未剔除 retired")
        self.assertEqual(r["counts"]["by_type"], {"单元": 1})
        self.assertEqual(r["counts"]["by_priority"], {"P0": 1})
        self.assertEqual(r["counts"]["by_dimension"], {"正向": 1})
        self.assertEqual(r["counts"]["acs_covered"], 1, "acs_covered 未剔除 retired")

    def test_retired_excluded_from_fh_killed(self):
        # 替代品不继承 kill_target（KISS）：仅被废弃 TC 杀掉的 FH → 红
        dead = self._base(retired={"reason": "r", "replaced_by": "TC-1.1.2"})
        alive = self._base("TC-1.1.2", kill_target="FH-1.1.2")
        fhs = self.FHS + [{"id": "FH-1.1.2", "ac": "AC-1.1", "text": "替代瞄准"}]
        r = self._env([dead, alive], fhs=fhs,
                      audit=self._audit(["TC-1.1.1", "TC-1.1.2"]), final=True)
        self.assertIn("SET_MISMATCH", codes(r), "retired 杀伤未从 killed 剔除")
        self.assertIn("FH-1.1.1", msgs(r))
        # 替代品重新瞄准后放行（kill_target 自带，不继承）
        alive2 = self._base("TC-1.1.2", kill_target=["FH-1.1.1", "FH-1.1.2"])
        r = self._env([dead, alive2], fhs=fhs,
                      audit=self._audit(["TC-1.1.1", "TC-1.1.2"]), final=True)
        self.assertTrue(r["ok"], msgs(r))

    def test_retired_status_not_flip_coding_phase(self):
        # 废弃条目的历史 通过 不得触发编码期口径：活跃面全待办 → 设计期引用口径放行
        dead = self._base("TC-1.1.2", status="通过",
                          retired={"reason": "r", "replaced_by": "TC-1.1.1"})
        r = self._env([self._base(), dead],
                      audit=self._audit(["TC-1.1.1", "TC-1.1.2"]), final=True)
        self.assertTrue(r["ok"], msgs(r))

    def test_retired_excluded_from_anchor_gate(self):
        # 接口锚门：唯一点名锚的集成 TC 已废弃 → 门红；替代在场 → 门绿
        fx.write_doc(self.root, "prd", prd_doc())
        ac = {"id": "AC-1.1", "given": "g", "when": "w", "then": "t",
              "refs": ["FR-1.1"], "api_refs": [self.ANCHOR]}
        fx.write_doc(self.root, "stories", stories_doc([simple_story(acs=[ac])]))
        fx.write_doc(self.root, "openapi", openapi_doc())
        dead = tc_case("TC-1.1.1", "AC-1.1", technique="决策表", type_="集成",
                     dimension="正向", kill_target="FH-1.1.1",
                     api_refs=[self.ANCHOR])
        dead["retired"] = {"reason": "锚迁移", "replaced_by": "TC-1.1.2"}
        fhs = [{"id": "FH-1.1.1", "ac": "AC-1.1", "text": "夹具故障假设"}]
        fx.write_doc(self.root, "test-plan", fx.doc_test_plan(
            [dead], fault_hypotheses=fhs, dimension_audit=self._audit(["TC-1.1.1"]),
            normalize=False))
        r = check(self.root, "test-plan", final=True)
        self.assertIn("SET_MISMATCH", codes(r), "retired 集成 TC 仍计入锚覆盖")
        alive = tc_case("TC-1.1.2", "AC-1.1", technique="决策表", type_="集成",
                      dimension="正向", kill_target="FH-1.1.1",
                      api_refs=[self.ANCHOR])
        fx.write_doc(self.root, "test-plan", fx.doc_test_plan(
            [dead, alive], fault_hypotheses=fhs,
            dimension_audit=self._audit(["TC-1.1.1", "TC-1.1.2"]), normalize=False))
        self.assertTrue(check(self.root, "test-plan", final=True)["ok"])


class ProducerTcCheckTest(CheckBase):
    """Q-114：TC.producer 生产者字段（底单 :884/:889 + 2026-10-20/21 裁）——
    必填（缺失 EMPTY_FIELD）+ 三值枚举 test-design|augment|e2e（非法值 ENUM_INVALID），
    前向强制、存量零回填（当前无存量用例）。"""

    FHS = [{"id": "FH-1.1.1", "ac": "AC-1.1", "text": "夹具故障假设"}]

    def _env(self, cases):
        fx.write_doc(self.root, "prd", prd_doc())
        fx.write_doc(self.root, "stories", stories_doc([simple_story()]))
        fx.write_doc(self.root, "test-plan", fx.doc_test_plan(
            cases, fault_hypotheses=self.FHS))
        return check(self.root, "test-plan")

    def _case(self, producer="test-design", **over):
        t = tc_case("TC-1.1.1", "AC-1.1", technique="边界", dimension="正向",
                    kill_target="FH-1.1.1")
        if producer is None:
            t.pop("producer", None)
        else:
            t["producer"] = producer
        t.update(over)
        return t

    def test_producer_missing_is_empty_field(self):
        r = self._env([self._case(producer=None)])
        self.assertIn("EMPTY_FIELD", codes(r), "producer 缺失未拦")
        self.assertIn(".producer", " | ".join(x["where"] for x in r["violations"]))

    def test_producer_illegal_value_is_enum_invalid(self):
        r = self._env([self._case(producer="test-design-v2")])
        got = codes(r)
        self.assertIn("ENUM_INVALID", got, "producer 非法值未按枚举拦")
        self.assertNotIn("EMPTY_FIELD", {x["code"] for x in r["violations"]
                                         if x["where"].endswith(".producer")},
                         "非空非法值不应报缺失")

    def test_producer_three_legal_values_pass(self):
        cases = []
        for i, producer in enumerate(("test-design", "augment", "e2e"), start=1):
            t = self._case(producer=producer)
            t["id"] = "TC-1.1.%d" % i
            cases.append(t)
        r = self._env(cases)
        self.assertNotIn("EMPTY_FIELD", codes(r), codes(r))
        self.assertNotIn("ENUM_INVALID", codes(r), codes(r))


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
            [tc_case("TC-1.1.1", "AC-1.1", status=tc_status, **kwargs)], gaps=gaps))
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
            [tc_case("TC-1.1.1", "AC-1.1", technique="边界"),
             tc_case("TC-2.1.1", "AC-2.1", technique="边界")]))
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
            [tc_case("TC-1.1.1", "AC-1.1", status=tc_status, **kwargs)]))
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

    def test_finding_radius_enum(self):
        # 爆炸半径标注（底单爆炸半径批 1b）：合法枚举过、越界拦
        base = fx.task("S-1", status="待审查", test_refs=["TC-1.1.1"], evidence=[
            {"tc": "TC-1.1.1", "red": "r", "green": "g"}])
        base["review"] = {"at": "2026-01-01", "verdict": "失败", "findings": [
            {"layer": "正确性", "route": "小修", "radius": "系统", "note": "x"}]}
        self._env(base, tc_status="通过")
        self.assertTrue(check(self.root, "review")["ok"], msgs(check(self.root, "review")))
        base["review"] = {"at": "2026-01-01", "verdict": "失败", "findings": [
            {"layer": "正确性", "route": "小修", "radius": "致命", "note": "x"}]}
        self._env(base, tc_status="通过")
        self.assertIn("ENUM_INVALID", codes(check(self.root, "review")))

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

    # Q-104（底单 :364 ⑤）：重复键 ≠ 解析失败——新码 DUPLICATE_KEY，与 UNPARSABLE_YAML 区分
    def test_duplicate_key_yaml(self):
        fx.write_doc(self.root, "prd",
                     "project:\n  name: a\n  name: b\n")
        r = check(self.root, "prd")
        self.assertFalse(r["ok"])
        self.assertEqual(codes(r), {"DUPLICATE_KEY"})
        self.assertIn("重复键", msgs(r))
        self.assertNotIn("UNPARSABLE_YAML", codes(r))

    def test_duplicate_key_nested_and_distinct_from_unparsable(self):
        doc = prd_doc()
        text = yaml.safe_dump(doc, allow_unicode=True, sort_keys=False)
        # 嵌套层重复键同样拦截（不在顶层也能抓）
        text += "extra:\n  k: 1\n  k: 2\n"
        fx.write_doc(self.root, "prd", text)
        r = check(self.root, "prd")
        self.assertFalse(r["ok"])
        self.assertEqual(codes(r), {"DUPLICATE_KEY"})
        # 对照：真解析失败仍是 UNPARSABLE_YAML（两码分界不漂移）
        fx.write_doc(self.root, "prd", "project: [unclosed\n")
        r2 = check(self.root, "prd")
        self.assertEqual(codes(r2), {"UNPARSABLE_YAML"})

    def test_receipt_shape(self):
        fx.write_doc(self.root, "prd", prd_doc())
        r = check(self.root, "prd")
        self.assertEqual(r["command"], "check")
        self.assertIsInstance(r["violations"], list)
        self.assertIsInstance(r["warnings"], list)
        self.assertIsInstance(r["counts"], dict)

    # v4 批 3（§7-3b）：全类型 project 时间键格式断言——两格式兼容（存量纯日期 |
    # 秒级真值）；空串（留空＝未盖章）与乱写红
    def test_project_times_accept_both_formats(self):
        doc = prd_doc()
        doc["project"]["created"] = "2026-10-13 09:00:00"
        doc["project"]["updated"] = "2026-10-13 09:30:15"
        fx.write_doc(self.root, "prd", doc)
        r = check(self.root, "prd")
        self.assertTrue(r["ok"], msgs(r))

    def test_project_times_reject_empty_and_garbage(self):
        doc = prd_doc()
        doc["project"]["created"] = ""
        doc["project"]["updated"] = "手写"
        fx.write_doc(self.root, "prd", doc)
        r = check(self.root, "prd")
        self.assertFalse(r["ok"])
        self.assertEqual(codes(r), {"ENUM_INVALID"})
        wheres = " ".join(x["where"] for x in r["violations"])
        self.assertIn("project.created", wheres)
        self.assertIn("project.updated", wheres)


# ---------------------------------------------------------------- mutation-report

def mutation_doc(**over):
    """合法的最小 mutation-report：10 变异体 9 被杀（保守分 90），1 条候选等价体。"""
    run = {"date": "2026-09-22", "task": "S-1", "killed": 9, "total": 10, "score": 90,
           "survivors": [{"mutant": "core/Add_Sub", "file": "a.py", "line": 1}],
           "equivalents": [{"mutant": "core/Add_Sub", "reason": "不可区分"}]}
    run.update(over)
    return {"project": {"name": "mini", "status": "已定稿"}, "runs": [run],
            "revisions": []}


class MutationReportTest(CheckBase):
    """C·9 缺口⑦：mutation-report 此前是唯一无校验器的产物（schema 漂移无人拦）。"""

    def test_clean_report_passes_with_counts(self):
        fx.write_doc(self.root, "mutation-report", mutation_doc())
        r = check(self.root, "mutation-report")
        self.assertTrue(r["ok"], msgs(r))
        self.assertEqual({"runs": 1, "survivors": 1, "equivalents": 1,
                          "critical_runs": 0}, r["counts"])

    def test_score_must_match_conservative_formula(self):
        """裁定前的分是保守值——候选等价体仍留在分母。"""
        fx.write_doc(self.root, "mutation-report", mutation_doc(score=100))
        r = check(self.root, "mutation-report")
        self.assertFalse(r["ok"])
        self.assertIn("SET_MISMATCH", codes(r))
        self.assertIn("按 killed/total 重算 90", msgs(r))

    def test_critical_tally_checked_too(self):
        fx.write_doc(self.root, "mutation-report",
                     mutation_doc(critical={"killed": 1, "total": 2, "score": 90}))
        r = check(self.root, "mutation-report")
        self.assertIn("SET_MISMATCH", codes(r))
        self.assertEqual(1, r["counts"]["critical_runs"])

    def test_critical_must_be_mapping_when_present(self):
        fx.write_doc(self.root, "mutation-report", mutation_doc(critical=50))
        r = check(self.root, "mutation-report")
        self.assertIn("TYPE_INVALID", codes(r))
        self.assertIn("省略该键", msgs(r))

    def test_missing_runs_rejected(self):
        fx.write_doc(self.root, "mutation-report", {"project": {"status": "草稿"}})
        r = check(self.root, "mutation-report")
        self.assertIn("EMPTY_FIELD", codes(r))

    def test_equivalent_requires_mutant_and_reason(self):
        doc = mutation_doc()
        doc["runs"][0]["equivalents"] = [{"mutant": "core/Add_Sub"}]
        fx.write_doc(self.root, "mutation-report", doc)
        r = check(self.root, "mutation-report")
        self.assertIn("EMPTY_FIELD", codes(r))
        self.assertIn("reason", msgs(r))

    def test_zero_total_rejected(self):
        fx.write_doc(self.root, "mutation-report",
                     mutation_doc(killed=0, total=0, score=0))
        r = check(self.root, "mutation-report")
        self.assertIn("ENUM_INVALID", codes(r))


# ------------------------------------------- architecture.affects 的 SC/P 域（C·3a 裁定 22）

def scenarios_doc(scenarios=None, **over):
    """wds-scenarios.yaml 迷你夹具（ID 形态照 diy-wds-scenarios 规则 6）。"""
    doc = {
        "project": {"name": "demo", "created": "2026-09-21",
                    "updated": "2026-09-21", "status": "已定稿"},
        "scenarios": list(scenarios or [{
            "id": "SC-01", "name": "张伟的订购", "priority": 1, "status": "已大纲",
            "pages": [{"id": "SC-01.P1", "slug": "01.1-首页", "name": "首页"}]}]),
    }
    doc.update(over)
    return doc


class WdsAffectsDomainTest(CheckBase):
    """裁定 22：architecture.affects 的解析域并入 WDS 线 SC-<nn> / SC-<nn>.P<n>。

    第四条真链路（同 architecture.affects / openapi x-fr / stories refs / design_ref
    三条既有链路）——接入前 SC/P 一律 UNKNOWN_ID 真拒，接入后真解析。
    """

    # trace: C·3a 裁定 22 —— 接入后真过：纯 WDS 线（无 prd.yaml）不再走「跳过子检查」
    def test_wds_line_ids_resolve_without_prd(self):
        fx.write_doc(self.root, "wds-scenarios", scenarios_doc())
        fx.write_doc(self.root, "architecture", arch_doc(decisions=[{
            "id": "D-1", "title": "决策", "decision": "A", "rationale": "r",
            "alternatives": [{"option": "B", "why_not": "w"}],
            "affects": ["SC-01", "SC-01.P1"], "status": "已采纳"}]))
        r = check(self.root, "architecture")
        self.assertTrue(r["ok"], msgs(r))
        self.assertEqual([], r["warnings"], "SC/P 域在场时不应再报「无法解析，跳过子检查」")

    # trace: C·3a 裁定 22 —— 两域共存（双源俱在时用户选 WDS 线，而 prd 也在场）
    def test_prd_and_wds_domains_coexist(self):
        fx.write_doc(self.root, "prd", prd_doc())
        fx.write_doc(self.root, "wds-scenarios", scenarios_doc())
        fx.write_doc(self.root, "architecture", arch_doc(decisions=[{
            "id": "D-1", "title": "决策", "decision": "A", "rationale": "r",
            "alternatives": [{"option": "B", "why_not": "w"}],
            "affects": ["FR-1.1", "NFR-1", "SC-01", "SC-01.P1"], "status": "已采纳"}]))
        r = check(self.root, "architecture")
        self.assertTrue(r["ok"], msgs(r))

    # trace: C·3a 裁定 22 —— 反证：新域是真解析，不是橡皮章（域内不存在的 ID 仍真拒）
    def test_dangling_wds_id_still_rejected(self):
        fx.write_doc(self.root, "wds-scenarios", scenarios_doc())
        fx.write_doc(self.root, "architecture", arch_doc(decisions=[{
            "id": "D-1", "title": "决策", "decision": "A", "rationale": "r",
            "alternatives": [{"option": "B", "why_not": "w"}],
            "affects": ["SC-99.P9"], "status": "已采纳"}]))
        r = check(self.root, "architecture")
        self.assertFalse(r["ok"])
        self.assertIn("UNKNOWN_ID", codes(r))
        self.assertIn("SC-99.P9", msgs(r))

    # trace: C·3a 裁定 22 —— 域不静默放宽：wds-scenarios.yaml 缺席时 SC/P 仍判 UNKNOWN_ID
    #        （即接入前的真拒行为，作为新域的边界守卫：只增数据源，不增通配）
    def test_wds_domain_absent_keeps_rejection(self):
        fx.write_doc(self.root, "prd", prd_doc())
        fx.write_doc(self.root, "architecture", arch_doc(decisions=[{
            "id": "D-1", "title": "决策", "decision": "A", "rationale": "r",
            "alternatives": [{"option": "B", "why_not": "w"}],
            "affects": ["SC-01.P1"], "status": "已采纳"}]))
        r = check(self.root, "architecture")
        self.assertIn("UNKNOWN_ID", codes(r))

    # trace: C·3a 裁定 22 —— wds-scenarios.yaml 损坏 → 告警可见（不静默吞），子检查不虚报通过
    def test_broken_wds_scenarios_warns(self):
        fx.write_doc(self.root, "prd", prd_doc())
        fx.write_doc(self.root, "wds-scenarios", "scenarios: [未闭合\n")
        fx.write_doc(self.root, "architecture", arch_doc(decisions=[{
            "id": "D-1", "title": "决策", "decision": "A", "rationale": "r",
            "alternatives": [{"option": "B", "why_not": "w"}],
            "affects": ["SC-01.P1"], "status": "已采纳"}]))
        r = check(self.root, "architecture")
        self.assertIn("UNKNOWN_ID", codes(r))
        self.assertTrue(any("wds-scenarios.yaml 损坏" in w for w in r["warnings"]),
                        "损坏输入未告警：%s" % r["warnings"])


class EnumFacesTest(CheckBase):
    """Q-115 枚举面一致性：面清单＋extract＋集合相等断言（封闭世界）。"""

    def _mini(self, files):
        import shutil
        import tempfile
        root = tempfile.mkdtemp(prefix="enum_faces_")
        self.addCleanup(shutil.rmtree, root, True)
        for rel, text in files.items():
            path = os.path.join(root, rel.replace("/", os.sep))
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(text)
        return root

    def _check(self, root, registry, sweep=None):
        from diyc_check_docs import check_enum_faces
        from diyc_check_docs_lib import Report
        r = Report()
        check_enum_faces(r, skills_root=root, registry=registry, sweep_keys=sweep)
        return r

    def test_installation_faces_green(self):
        """仓库安装面自查：当前全部面与常量对齐（面清单零违规）。"""
        from diyc_check_docs import check_enum_faces
        from diyc_check_docs_lib import Report
        r = Report()
        check_enum_faces(r)
        self.assertEqual([v["where"] for v in r.violations], [], msgs({"violations": r.violations, "warnings": []}))

    def test_check_run_carries_faces_gate(self):
        """通用门挂载：正常 check 运行不引入 skills/ 面违规。"""
        fx.write_doc(self.root, "prd", prd_doc())
        r = check(self.root, "prd")
        self.assertTrue(r["ok"], msgs(r))
        self.assertFalse([v for v in r["violations"] if v["where"].startswith("skills/")])

    def test_pipe_drift_red(self):
        files = {"demo/SKILL.md": "  k: A|B|C\n"}
        reg = (("FAKE", ("A", "B"), (("demo/SKILL.md", ("pipe", "k")),)),)
        r = self._check(self._mini(files), reg, {"k": ("FAKE",)})
        self.assertEqual([v["code"] for v in r.violations], ["SET_MISMATCH"])
        self.assertIn("不一致", r.violations[0]["msg"])

    def test_pipe_missing_value_red(self):
        files = {"demo/SKILL.md": "  k: A\n"}
        reg = (("FAKE", ("A", "B"), (("demo/SKILL.md", ("pipe", "k")),)),)
        r = self._check(self._mini(files), reg, {"k": ("FAKE",)})
        self.assertEqual([v["code"] for v in r.violations], ["SET_MISMATCH"])

    def test_new_face_private_add_red(self):
        files = {"demo/SKILL.md": "  k: A|B\n",
                 "intruder/SKILL.md": "  k: A|B\n"}
        reg = (("FAKE", ("A", "B"), (("demo/SKILL.md", ("pipe", "k")),)),)
        r = self._check(self._mini(files), reg, {"k": ("FAKE",)})
        self.assertEqual([v["code"] for v in r.violations], ["SET_MISMATCH"])
        self.assertIn("清单外", r.violations[0]["msg"])
        self.assertIn("intruder", r.violations[0]["where"])

    def test_disjoint_foreign_enum_not_flagged(self):
        """同名键异义（如 research 的 dimension）值域不相交 → 扫掠不误报。"""
        files = {"demo/SKILL.md": "  k: A|B\n",
                 "other/SKILL.md": "  k: X|Y\n"}
        reg = (("FAKE", ("A", "B"), (("demo/SKILL.md", ("pipe", "k")),)),)
        r = self._check(self._mini(files), reg, {"k": ("FAKE",)})
        self.assertEqual(r.violations, [])

    def test_text_face_drift_red(self):
        files = {"demo/SKILL.md": "枚举：A / C\n"}
        reg = (("FAKE", ("A", "B"), (("demo/SKILL.md", ("text", "A / B")),)),)
        r = self._check(self._mini(files), reg, {})
        self.assertEqual([v["code"] for v in r.violations], ["SET_MISMATCH"])
        self.assertIn("缺枚举句", r.violations[0]["msg"])

    def test_membership_sweep_producer_red(self):
        files = {"demo/SKILL.md": "    producer: alpha\n",
                 "intruder/SKILL.md": "    producer: alpha\n"}
        reg = (("FAKE", ("alpha", "beta"), (
            ("demo/SKILL.md", ("text", "producer: alpha")),)),)
        r = self._check(self._mini(files), reg, {"producer": ("FAKE",)})
        self.assertEqual([v["code"] for v in r.violations], ["SET_MISMATCH"])
        self.assertIn("清单外", r.violations[0]["msg"])

    def test_pipe_after_context_disambiguates(self):
        files = {"demo/SKILL.md": "  status: 草稿|已定稿\n"
                                  "  - id: D-1\n"
                                  "    status: 待定|已采纳\n"}
        reg = (("FAKE", ("待定", "已采纳"),
                (("demo/SKILL.md", ("pipe_after", "- id: D-1", "status")),)),)
        r = self._check(self._mini(files), reg, {})
        self.assertEqual(r.violations, [])


if __name__ == "__main__":
    unittest.main()
