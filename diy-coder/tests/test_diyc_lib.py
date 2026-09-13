# -*- coding: utf-8 -*-
"""diyc_lib 单元测试（批次 3，契约 §5）。

覆盖：配置容错（对齐 help.py 批次 1 加固语义）、实例白名单、原子写、
id_sort、receipt/render、emit 两态、Docs 索引与 story_covered 三态
（TDD 门唯一定义源）。真产物仅只读冒烟。
"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)  # import diyc_fixture
sys.path.insert(0, os.path.join(HERE, "..", "skills", "diy-tools", "scripts"))

import diyc_fixture as fx  # noqa: E402
import diyc_lib  # noqa: E402

REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
REAL_OUTPUT = os.path.join(REPO_ROOT, "diy-output")


class FixtureApiTests(unittest.TestCase):
    # trace: 冻结夹具 API（team-lead 2026-09-13 裁定）：make_project / write_doc / read_doc，W2/W3 只读引用
    def test_make_project_write_read_roundtrip(self):
        root = fx.make_project(Path(tempfile.mkdtemp(prefix="diyc-fx-")))
        self.addCleanup(fx.cleanup, root)
        self.assertTrue(os.path.isfile(os.path.join(root, "diy-coder.yaml")))
        p = fx.write_doc(root, "stories", {"stories": [{"id": "S-1"}]})
        self.assertTrue(str(p).replace("\\", "/").endswith("diy-output/stories.yaml"))
        self.assertEqual(fx.read_doc(root, "stories")["stories"][0]["id"], "S-1")

    def test_write_doc_accepts_yaml_suffix_and_raw_str(self):
        root = fx.make_project(Path(tempfile.mkdtemp(prefix="diyc-fx-")))
        self.addCleanup(fx.cleanup, root)
        fx.write_doc(root, "bug-log.yaml", "bugs:\n- id: BUG-001\n")
        self.assertEqual(fx.read_doc(root, "bug-log")["bugs"][0]["id"], "BUG-001")

    def test_read_doc_missing_raises(self):
        root = fx.make_project(Path(tempfile.mkdtemp(prefix="diyc-fx-")))
        self.addCleanup(fx.cleanup, root)
        with self.assertRaises(FileNotFoundError):
            fx.read_doc(root, "sprint")


class ConfigToleranceTests(unittest.TestCase):
    # trace: TC-16.1.1 实例解析容错（与 help.py resolve_output_dir 逐条一致）
    def setUp(self):
        self.root = fx.make_root()
        self.addCleanup(fx.cleanup, self.root)

    def cfg_path(self):
        return os.path.join(self.root, "diy-coder.yaml")

    def test_missing_config_returns_default(self):
        os.remove(self.cfg_path())
        cfg, warnings = diyc_lib.read_config(self.root)
        self.assertEqual(cfg, {})
        self.assertEqual(warnings, [])

    def test_broken_yaml_downgrades_with_warning(self):
        with open(self.cfg_path(), "w", encoding="utf-8") as f:
            f.write("paths: [unclosed\n")
        cfg, warnings = diyc_lib.read_config(self.root)
        self.assertEqual(cfg, {})
        self.assertEqual(len(warnings), 1)
        self.assertIn("diy-coder.yaml", warnings[0])

    def test_paths_not_mapping_downgrades(self):
        with open(self.cfg_path(), "w", encoding="utf-8") as f:
            f.write("paths: [1, 2]\n")
        cfg, warnings = diyc_lib.read_config(self.root)
        self.assertEqual(cfg, {"paths": [1, 2]})
        self.assertEqual(len(warnings), 1)
        self.assertIn("paths", warnings[0])

    def test_output_dir_not_string_downgrades(self):
        with open(self.cfg_path(), "w", encoding="utf-8") as f:
            f.write("paths:\n  output_dir: 3\n")
        cfg, warnings = diyc_lib.read_config(self.root)
        self.assertEqual(len(warnings), 1)
        self.assertIn("output_dir", warnings[0])
        resolved = diyc_lib.resolve_output_dir(self.root, None)
        self.assertEqual(resolved, os.path.join(self.root, "diy-output"))

    def test_resolve_mainline_flat(self):
        resolved = diyc_lib.resolve_output_dir(self.root, None)
        self.assertEqual(resolved, os.path.join(self.root, "diy-output"))

    def test_resolve_with_instance(self):
        resolved = diyc_lib.resolve_output_dir(self.root, "v2.1_x-9")
        self.assertEqual(resolved, os.path.join(self.root, "diy-output", "v2.1_x-9"))


class InstanceWhitelistTests(unittest.TestCase):
    # trace: 末字符禁点（Windows 尾点目录折叠）——非法实例名拒注入
    def setUp(self):
        self.root = fx.make_root()
        self.addCleanup(fx.cleanup, self.root)

    def test_illegal_names_rejected(self):
        # "" 显式空串不回落主线：仅 None 表示主线（契约 §3/§5 裁定，viewer R16-1 语义）
        for bad in ("", "b.", "b..", ".b", "a/b", "a\\b", "..", "a b", "-b"):
            with self.subTest(instance=bad):
                with self.assertRaises(SystemExit) as ctx:
                    diyc_lib.resolve_output_dir(self.root, bad)
                self.assertEqual(ctx.exception.code, 1)

    def test_legal_names_accepted(self):
        for good in ("a", "ab", "a.b", "a_b-c9", "9x", "A1"):
            with self.subTest(instance=good):
                diyc_lib.resolve_output_dir(self.root, good)


class YamlIOTests(unittest.TestCase):
    def setUp(self):
        self.root = fx.make_root()
        self.addCleanup(fx.cleanup, self.root)

    def test_load_yaml_missing_and_empty(self):
        p = os.path.join(self.root, "none.yaml")
        self.assertEqual(diyc_lib.load_yaml(p), {})
        empty = os.path.join(self.root, "empty.yaml")
        with open(empty, "w", encoding="utf-8") as f:
            f.write("")
        self.assertEqual(diyc_lib.load_yaml(empty), {})

    def test_load_yaml_broken_raises(self):
        bad = os.path.join(self.root, "bad.yaml")
        with open(bad, "w", encoding="utf-8") as f:
            f.write("a: [\n")
        with self.assertRaises(Exception):
            diyc_lib.load_yaml(bad)

    def test_safe_load_yaml_returns_tuple(self):
        data, err = diyc_lib.safe_load_yaml(os.path.join(self.root, "none.yaml"))
        self.assertEqual(data, {})
        self.assertIsNone(err)
        bad = os.path.join(self.root, "bad.yaml")
        with open(bad, "w", encoding="utf-8") as f:
            f.write("a: [\n")
        data, err = diyc_lib.safe_load_yaml(bad)
        self.assertIsNone(data)
        self.assertIsInstance(err, str)

    def test_save_yaml_atomic_roundtrip(self):
        p = os.path.join(self.root, "out.yaml")
        diyc_lib.save_yaml_atomic(p, {"项目": "中文", "n": [1, 2]})
        self.assertEqual(diyc_lib.load_yaml(p), {"项目": "中文", "n": [1, 2]})
        leftovers = [f for f in os.listdir(self.root) if f.endswith(".tmp")]
        self.assertEqual(leftovers, [], "原子写遗留临时文件")


class SmallHelpersTests(unittest.TestCase):
    def test_today_and_stamp_shapes(self):
        self.assertRegex(diyc_lib.today(), r"^\d{4}-\d{2}-\d{2}$")
        self.assertRegex(diyc_lib.stamp(), r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$")

    def test_id_sort_numeric_aware(self):
        got = diyc_lib.id_sort(["S-10", "S-2", "S-1", "S-21", "S-3"])
        self.assertEqual(got, ["S-1", "S-2", "S-3", "S-10", "S-21"])
        got = diyc_lib.id_sort(["TC-5.1.10", "TC-5.1.2", "TC-5.1.1"])
        self.assertEqual(got, ["TC-5.1.1", "TC-5.1.2", "TC-5.1.10"])

    def test_v_normalizes_where_slashes(self):
        viol = diyc_lib.v("UNKNOWN_ID", "diy-output\\sprint.yaml tasks[S-9]", "msg")
        self.assertEqual(viol["where"], "diy-output/sprint.yaml tasks[S-9]")
        self.assertEqual(set(viol), {"code", "where", "msg"})

    def test_receipt_shape(self):
        r = diyc_lib.receipt("resolve", True, output_dir="diy-output", instance=None,
                             config_found=False, warnings=[])
        self.assertTrue(r["ok"])
        self.assertEqual(r["command"], "resolve")
        self.assertEqual(r["config_found"], False)


class EmitTests(unittest.TestCase):
    # trace: 契约 §3——--json 单行回执；人类态违规行 + 汇总行；exit code 由 ok 决定
    def capture(self, result, as_json, human_lines_fn=None):
        import io
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            rc = diyc_lib.emit(result, as_json, human_lines_fn=human_lines_fn)
        finally:
            sys.stdout = old
        return rc, buf.getvalue()

    def test_json_mode_single_line(self):
        result = {"ok": False, "command": "check",
                  "violations": [diyc_lib.v("MISSING_FILE", "diy-output/prd.yaml", "文件缺失")],
                  "warnings": [], "counts": {}}
        rc, out = self.capture(result, True)
        self.assertEqual(rc, 1)
        self.assertEqual(out.strip().count("\n"), 0, "JSON 回执不是单行")
        self.assertEqual(json.loads(out)["violations"][0]["code"], "MISSING_FILE")

    def test_human_mode_violations_and_summary(self):
        result = {"ok": False, "command": "check",
                  "violations": [diyc_lib.v("MISSING_FILE", "diy-output/prd.yaml", "文件缺失")],
                  "warnings": ["测试警告"], "counts": {}}
        rc, out = self.capture(result, False)
        self.assertEqual(rc, 1)
        self.assertIn("MISSING_FILE diy-output/prd.yaml: 文件缺失", out)
        self.assertIn("WARN 测试警告", out)
        self.assertIn("check", out)

    def test_human_mode_ok_summary(self):
        result = {"ok": True, "command": "trace", "violations": [], "warnings": [], "counts": {}}
        rc, out = self.capture(result, False)
        self.assertEqual(rc, 0)
        self.assertIn("通过", out)

    def test_human_lines_fn_appends_and_violations_kept(self):
        result = {"ok": False, "command": "resolve",
                  "violations": [diyc_lib.v("MISSING_FILE", "diy-output/prd.yaml", "文件缺失")],
                  "warnings": [], "counts": {}}
        rc, out = self.capture(result, False, human_lines_fn=lambda r: ["output_dir: X"])
        self.assertEqual(rc, 1)
        self.assertIn("output_dir: X", out)
        self.assertIn("MISSING_FILE diy-output/prd.yaml: 文件缺失", out)


class DocsIndexTests(unittest.TestCase):
    # trace: 契约 §5/§6——Docs 为跨文档核对唯一入口
    def setUp(self):
        self.root = fx.make_root()
        self.addCleanup(fx.cleanup, self.root)
        self.out = fx.out_dir(self.root)
        fx.write_doc(self.root, "stories", fx.doc_stories([
            fx.story("S-1", [fx.ac("AC-1.1", refs=["FR-1.1"])], status="done"),
        ]))
        fx.write_doc(self.root, "test-plan", fx.doc_test_plan(
            [fx.tc("TC-1.1.1", "AC-1.1", status="pass")],
            gaps=[fx.gap("AC-1.2", "S-1", decision="waived")]))
        fx.write_doc(self.root, "sprint", fx.doc_sprint([
            fx.task("S-1", status="done", test_refs=["TC-1.1.1"])]))
        fx.write_doc(self.root, "architecture", {"project": fx.project_meta(),
                                                 "decisions": [{"id": "D-1", "status": "accepted"}]})
        fx.write_doc(self.root, "prd", {"project": fx.project_meta(),
                                        "features": [{"id": "F-1", "requirements": [
                                            {"id": "FR-1.1", "priority": "must"}]}],
                                        "nfrs": [{"id": "NFR-1", "statement": "s"}]})
        fx.write_doc(self.root, "epics", {"project": fx.project_meta(),
                                          "epics": [{"id": "E-1", "status": "in-progress"}]})
        self.docs = diyc_lib.Docs(self.root, self.out)

    def test_index_shapes(self):
        self.assertEqual(set(self.docs.stories()), {"S-1"})
        self.assertEqual(set(self.docs.acs()), {"AC-1.1"})
        self.assertEqual(self.docs.acs()["AC-1.1"]["_story"], "S-1")
        self.assertEqual(set(self.docs.tcs()), {"TC-1.1.1"})
        self.assertEqual(self.docs.tcs()["TC-1.1.1"]["_story"], "S-1")
        self.assertEqual(set(self.docs.frs()), {"FR-1.1"})
        self.assertEqual(self.docs.frs()["FR-1.1"]["_feature"], "F-1")
        self.assertEqual(set(self.docs.nfrs()), {"NFR-1"})
        self.assertEqual(set(self.docs.decisions()), {"D-1"})
        self.assertEqual(set(self.docs.epics()), {"E-1"})
        self.assertEqual(set(self.docs.tasks()), {"S-1"})
        self.assertEqual(set(self.docs.gaps()), {"AC-1.2"})

    def test_missing_doc_returns_none_and_yaml_err(self):
        self.assertIsNone(self.docs.doc("design"))
        self.assertIsNone(self.docs.doc("openapi"))
        self.assertIsNone(self.docs.yaml_err("stories"))

    def test_broken_doc_records_error(self):
        fx.write_doc(self.root, "bug-log", "bugs: [\n")
        docs = diyc_lib.Docs(self.root, self.out)
        self.assertIsNone(docs.doc("bug-log"))
        self.assertIsInstance(docs.yaml_err("bug-log"), str)

    def test_tcs_for_story(self):
        self.assertEqual(self.docs.tcs_for_story("S-1"), ["TC-1.1.1"])
        self.assertEqual(self.docs.tcs_for_story("S-99"), [])


class StoryCoveredTests(unittest.TestCase):
    # trace: 契约 §4.2 PENDING_UNCOVERED 唯一定义源——三态：有 TC 覆盖 / waived 豁免 / 缺覆盖
    def setUp(self):
        self.root = fx.make_root()
        self.addCleanup(fx.cleanup, self.root)
        self.out = fx.out_dir(self.root)
        fx.write_doc(self.root, "stories", fx.doc_stories([
            fx.story("S-20", [fx.ac("AC-20.1")]),                      # 无 TC 无 gap → 缺覆盖
            fx.story("S-21", [fx.ac("AC-21.1")]),                      # 无 TC gap=pending → 缺覆盖
            fx.story("S-22", [fx.ac("AC-22.1")]),                      # gap=waived → 豁免
            fx.story("S-23", [fx.ac("AC-23.1")]),                      # gap=accept-gap → 豁免
            fx.story("S-24", [fx.ac("AC-24.1")]),                      # 有 TC → 覆盖
            fx.story("S-25", [fx.ac("AC-25.1"), fx.ac("AC-25.2")]),    # 部分覆盖 → 缺 AC-25.2
        ]))
        fx.write_doc(self.root, "test-plan", fx.doc_test_plan(
            [fx.tc("TC-24.1.1", "AC-24.1"), fx.tc("TC-25.1.1", "AC-25.1")],
            gaps=[fx.gap("AC-21.1", "S-21", decision="pending"),
                  fx.gap("AC-22.1", "S-22", decision="waived"),
                  fx.gap("AC-23.1", "S-23", decision="accept-gap")]))
        self.docs = diyc_lib.Docs(self.root, self.out)

    def test_pending_or_missing_gap_is_uncovered(self):
        covered, missing = self.docs.story_covered("S-20")
        self.assertFalse(covered)
        self.assertEqual(missing, ["AC-20.1"])
        covered, missing = self.docs.story_covered("S-21")
        self.assertFalse(covered)
        self.assertEqual(missing, ["AC-21.1"])

    def test_waived_and_accept_gap_are_exempt(self):
        self.assertEqual(self.docs.story_covered("S-22"), (True, []))
        self.assertEqual(self.docs.story_covered("S-23"), (True, []))

    def test_tc_binding_covers(self):
        self.assertEqual(self.docs.story_covered("S-24"), (True, []))

    def test_partial_coverage_lists_only_missing(self):
        covered, missing = self.docs.story_covered("S-25")
        self.assertFalse(covered)
        self.assertEqual(missing, ["AC-25.2"])

    def test_unknown_story_is_trivially_covered(self):
        self.assertEqual(self.docs.story_covered("S-99"), (True, []))


@unittest.skipUnless(os.path.isdir(REAL_OUTPUT), "无真产物目录，跳过冒烟")
class RealArtifactSmokeTests(unittest.TestCase):
    # 只读冒烟：Docs 能解析本仓库全部产物（不改一个字节）
    def test_docs_read_real_artifacts(self):
        docs = diyc_lib.Docs(REPO_ROOT, REAL_OUTPUT)
        self.assertIsNotNone(docs.doc("stories"))
        self.assertTrue(docs.stories(), "stories.yaml 未解析出 story")
        self.assertTrue(docs.acs(), "acs 索引为空")
        self.assertTrue(docs.tcs(), "tcs 索引为空")
        self.assertTrue(docs.tasks(), "sprint 任务索引为空")
        self.assertTrue(docs.frs(), "frs 索引为空")
        self.assertTrue(docs.decisions(), "decisions 索引为空")

    def test_story_covered_on_real_artifact(self):
        docs = diyc_lib.Docs(REPO_ROOT, REAL_OUTPUT)
        # S-1：done story，全部 AC waived（coverage_gaps）→ 豁免覆盖
        covered, missing = docs.story_covered("S-1")
        self.assertTrue(covered, "S-1 应因 waived 豁免视为覆盖：%s" % missing)


if __name__ == "__main__":
    unittest.main()
