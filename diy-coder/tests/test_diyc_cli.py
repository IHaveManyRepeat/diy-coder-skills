# -*- coding: utf-8 -*-
"""diyc CLI 入口测试（批次 3，契约 §3/§4.1/§4.3/§4.4）。

覆盖：resolve（合法/实例/非法名/配置降级）、trace（解析/排除/--src/未解析 ID）、
static（阻断停链 / 记录不阻断 / 超时 / 无 static_checks）、
exit code 三态（0/1/2）、人类态渲染。真产物仅只读冒烟。
"""
import json
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)  # import diyc_fixture

import diyc_fixture as fx  # noqa: E402

DIYC = os.path.join(HERE, "..", "skills", "diy-tools", "scripts", "diyc.py")
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
REAL_OUTPUT = os.path.join(REPO_ROOT, "diy-output")
PY = '"%s"' % sys.executable  # 含空格的解释器路径加引号（shell=True 经 cmd/POSIX sh）

# trace 夹具行：拆分拼接，避免本文件源码出现连写的 "# trace:" 字面量
# （diyc trace 是文本扫描，否则测试夹具会被自己的审计扫成假引用）
TRACE_MARK_PY = "#"
TRACE_MARK_JS = "//"


def trace_line(mark, ids):
    return mark + " trace: " + ids + "\n"


def run_diyc(root, *args, timeout=120):
    return subprocess.run(
        [sys.executable, DIYC, *args, "--project-root", str(root)],
        capture_output=True, text=True, encoding="utf-8", timeout=timeout,
        stdin=subprocess.DEVNULL)


def jload(p):
    return json.loads(p.stdout)


def fwd(path):
    """回执表示层形态：一律正斜杠（V 验证 S5 裁定，机器消费面分隔符单形）。"""
    return str(path).replace("\\", "/")


class ResolveTests(unittest.TestCase):
    # trace: S-16 AC-16.1 实例解析委托（契约 §4.1）
    def setUp(self):
        self.root = fx.make_root()
        self.addCleanup(fx.cleanup, self.root)

    def test_resolve_mainline(self):
        p = run_diyc(self.root, "resolve", "--json")
        self.assertEqual(p.returncode, 0, p.stderr)
        r = jload(p)
        self.assertTrue(r["ok"])
        self.assertEqual(r["command"], "resolve")
        self.assertEqual(r["output_dir"], fwd(os.path.join(self.root, "diy-output")))
        self.assertNotIn("\\", r["output_dir"], "回执 output_dir 必须是正斜杠单形（S5）")
        self.assertIsNone(r["instance"])
        self.assertTrue(r["config_found"])
        self.assertEqual(r["warnings"], [])

    def test_resolve_instance_join(self):
        p = run_diyc(self.root, "resolve", "--instance", "v2.1_x", "--json")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(jload(p)["output_dir"],
                         fwd(os.path.join(self.root, "diy-output", "v2.1_x")))

    def test_resolve_illegal_instance_rejected(self):
        for bad in ("b.", "a/b", ".."):
            with self.subTest(instance=bad):
                p = run_diyc(self.root, "resolve", "--instance", bad, "--json")
                self.assertEqual(p.returncode, 1)
                self.assertIn("非法实例名", p.stderr)
                self.assertNotIn("Traceback", p.stderr)

    def test_resolve_empty_instance_rejected(self):
        # 契约 §3/§5 裁定：仅 None（旗标缺席）表示主线；显式空串按非法实例名拒绝
        p = run_diyc(self.root, "resolve", "--instance", "", "--json")
        self.assertEqual(p.returncode, 1)
        self.assertIn("非法实例名", p.stderr)
        self.assertNotIn("Traceback", p.stderr)

    def test_resolve_broken_config_downgrades_with_warning(self):
        with open(os.path.join(self.root, "diy-coder.yaml"), "w", encoding="utf-8") as f:
            f.write("paths: [unclosed\n")
        p = run_diyc(self.root, "resolve", "--json")
        self.assertEqual(p.returncode, 0, p.stderr)
        r = jload(p)
        self.assertEqual(r["output_dir"], fwd(os.path.join(self.root, "diy-output")))
        self.assertEqual(len(r["warnings"]), 1)

    def test_undecodable_config_reports_internal_error(self):
        # N-1/N-2（V 增量复验）：非 UTF-8 配置（中文 Windows 记事本按 ANSI 保存）不得
        # 空 stdout 裸崩——兜底窗口须覆盖 resolve_output_dir（配置读取在此发生）；
        # 人类态渲染器对兜底回执形状不得再崩（N-2）
        with open(os.path.join(self.root, "diy-coder.yaml"), "wb") as f:
            f.write(b"project:\n  name: \xd6\xd0\xce\xc4\n")  # GBK 字节：非 UTF-8
        p = run_diyc(self.root, "resolve", "--json")
        self.assertEqual(p.returncode, 1, p.stdout + p.stderr)
        self.assertTrue(p.stdout.strip(), "不得空 stdout 静默失败")
        r = jload(p)
        self.assertFalse(r["ok"])
        self.assertEqual([x["code"] for x in r["violations"]], ["INTERNAL_ERROR"])
        self.assertNotIn("Traceback", p.stderr)
        p2 = run_diyc(self.root, "resolve")
        self.assertEqual(p2.returncode, 1, p2.stdout + p2.stderr)
        self.assertIn("INTERNAL_ERROR", p2.stdout)
        self.assertNotIn("Traceback", p2.stderr)

    def test_resolve_missing_config(self):
        os.remove(os.path.join(self.root, "diy-coder.yaml"))
        p = run_diyc(self.root, "resolve", "--json")
        self.assertEqual(p.returncode, 0, p.stderr)
        r = jload(p)
        self.assertFalse(r["config_found"])
        self.assertEqual(r["output_dir"], fwd(os.path.join(self.root, "diy-output")))

    def test_resolve_human_mode_shows_output_dir(self):
        p = run_diyc(self.root, "resolve")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("output_dir", p.stdout)


class TraceTests(unittest.TestCase):
    # trace: S-8 AC-8.1 分层审查预览——trace 引用解析（契约 §4.3）
    def setUp(self):
        self.root = fx.make_root()
        self.addCleanup(fx.cleanup, self.root)
        fx.write_doc(self.root, "stories", fx.doc_stories(
            [fx.story("S-1", [fx.ac("AC-1.1")])]))
        fx.write_doc(self.root, "test-plan", fx.doc_test_plan(
            [fx.tc("TC-1.1.1", "AC-1.1")]))

    def test_trace_all_resolved(self):
        fx.write_text(os.path.join(self.root, "src", "a.py"),
                      trace_line(TRACE_MARK_PY, "S-1 AC-1.1 TC-1.1.1") + "x = 1\n")
        p = run_diyc(self.root, "trace", "--json")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        r = jload(p)
        self.assertTrue(r["ok"])
        self.assertEqual(r["counts"]["refs"], 3)
        self.assertEqual(r["counts"]["files_with_trace"], 1)
        self.assertEqual(r["unresolved"], [])

    def test_trace_unresolved_id_fails(self):
        fx.write_text(os.path.join(self.root, "src", "b.js"),
                      trace_line(TRACE_MARK_JS, "TC-9.9.9"))
        p = run_diyc(self.root, "trace", "--json")
        self.assertEqual(p.returncode, 1)
        r = jload(p)
        self.assertFalse(r["ok"])
        self.assertEqual(len(r["unresolved"]), 1)
        u = r["unresolved"][0]
        self.assertEqual(u["id"], "TC-9.9.9")
        self.assertEqual(u["file"], "src/b.js")
        self.assertEqual(u["line"], 1)
        codes = [x["code"] for x in r["violations"]]
        self.assertIn("TRACE_UNRESOLVED", codes)

    def test_trace_excludes_output_dir_and_vcs(self):
        for rel in (("diy-output", "fake.py"), (".git", "h.py"), ("node_modules", "n.py")):
            fx.write_text(os.path.join(self.root, *rel), trace_line(TRACE_MARK_PY, "S-99"))
        p = run_diyc(self.root, "trace", "--json")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertEqual(jload(p)["counts"]["refs"], 0)

    def test_trace_src_scopes_scan(self):
        fx.write_text(os.path.join(self.root, "src", "a.py"), trace_line(TRACE_MARK_PY, "S-1"))
        fx.write_text(os.path.join(self.root, "src", "b.js"), trace_line(TRACE_MARK_JS, "TC-9.9.9"))
        p = run_diyc(self.root, "trace", "--src", "src/a.py", "--json")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        r = jload(p)
        self.assertEqual(r["counts"]["refs"], 1)
        self.assertEqual(r["references"][0]["file"], "src/a.py")

    def test_trace_human_mode_lists_violations(self):
        fx.write_text(os.path.join(self.root, "src", "b.js"), trace_line(TRACE_MARK_JS, "TC-9.9.9"))
        p = run_diyc(self.root, "trace")
        self.assertEqual(p.returncode, 1)
        self.assertIn("TRACE_UNRESOLVED", p.stdout)
        self.assertIn("src/b.js", p.stdout)


class StaticTests(unittest.TestCase):
    # trace: S-7 AC-7.1 static_checks 链（契约 §4.4）
    def setUp(self):
        self.root = fx.make_root()
        self.addCleanup(fx.cleanup, self.root)

    def write_plan(self, checks):
        fx.write_doc(self.root, "test-plan", fx.doc_test_plan([], static_checks=checks))

    def test_blocking_failure_stops_chain(self):
        self.write_plan([
            fx.static_check(1, PY + ' -c "print(1)"', gate="阻断"),
            fx.static_check(2, PY + ' -c "import sys; sys.exit(3)"', gate="阻断"),
            fx.static_check(3, PY + ' -c "print(3)"', gate="阻断"),
        ])
        p = run_diyc(self.root, "static", "--json")
        self.assertEqual(p.returncode, 1)
        r = jload(p)
        self.assertFalse(r["ok"])
        verdicts = [x["verdict"] for x in r["layers"]]
        self.assertEqual(verdicts, ["通过", "失败", "已跳过"])
        self.assertEqual(r["counts"]["failed"], 1)
        self.assertEqual(r["counts"]["skipped"], 1)
        self.assertFalse(any(x["code"] == "MISSING_FILE" for x in r["violations"]))

    def test_advisory_failure_does_not_block(self):
        self.write_plan([
            fx.static_check(1, PY + ' -c "import sys; sys.exit(1)"', gate="记录不阻断"),
            fx.static_check(2, PY + ' -c "print(2)"', gate="阻断"),
        ])
        p = run_diyc(self.root, "static", "--json")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        r = jload(p)
        self.assertTrue(r["ok"])
        verdicts = [x["verdict"] for x in r["layers"]]
        self.assertEqual(verdicts, ["失败", "通过"])

    def test_timeout_counts_as_failure(self):
        self.write_plan([
            fx.static_check(1, PY + ' -c "import time; time.sleep(10)"', gate="阻断"),
        ])
        p = run_diyc(self.root, "static", "--timeout", "1", "--json")
        self.assertEqual(p.returncode, 1)
        r = jload(p)
        self.assertEqual(r["layers"][0]["verdict"], "失败")

    def test_no_static_checks_warns_ok(self):
        fx.write_doc(self.root, "test-plan", fx.doc_test_plan([]))
        p = run_diyc(self.root, "static", "--json")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        r = jload(p)
        self.assertTrue(r["ok"])
        self.assertEqual(r["counts"]["run"], 0)
        self.assertTrue(r["warnings"])

    def test_missing_test_plan_is_violation(self):
        p = run_diyc(self.root, "static", "--json")
        self.assertEqual(p.returncode, 1)
        codes = [x["code"] for x in jload(p)["violations"]]
        self.assertIn("MISSING_FILE", codes)

    def test_human_mode_lists_layers(self):
        self.write_plan([fx.static_check(1, PY + ' -c "print(1)"')])
        p = run_diyc(self.root, "static")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("通过", p.stdout)


class UsageTests(unittest.TestCase):
    def setUp(self):
        self.root = fx.make_root()
        self.addCleanup(fx.cleanup, self.root)

    def test_unknown_subcommand_is_usage_error(self):
        p = run_diyc(self.root, "no-such-command")
        self.assertEqual(p.returncode, 2)

    def test_missing_subcommand_is_usage_error(self):
        p = run_diyc(self.root)
        self.assertEqual(p.returncode, 2)

    def test_bug_add_requires_exactly_one_entry_source(self):
        # 互斥组 required=True（契约 §4.8）：缺失与同时给出都是用法错误，argv 层拦截
        p = run_diyc(self.root, "bug-add")
        self.assertEqual(p.returncode, 2)
        p = run_diyc(self.root, "bug-add", "--entry", "{}", "--entry-file", "x.json")
        self.assertEqual(p.returncode, 2)

    def test_check_final_rejected_for_review(self):
        # 契约 §4.2：--final 对 review 为用法错误(2)，在 argparse 收口层拦截
        p = run_diyc(self.root, "check", "--type", "review", "--final", "--json")
        self.assertEqual(p.returncode, 2)
        self.assertIn("review", p.stderr)

    def test_check_previous_type_whitelist(self):
        # 契约 §4.2：--previous 仅 prd/openapi/epics/stories/test-plan
        p = run_diyc(self.root, "check", "--type", "sprint", "--previous", "x.yaml", "--json")
        self.assertEqual(p.returncode, 2)
        self.assertIn("--previous", p.stderr)


@unittest.skipUnless(os.path.isdir(REAL_OUTPUT), "无真产物目录，跳过冒烟")
class RealArtifactSmokeTests(unittest.TestCase):
    # 只读冒烟：resolve 对真仓库根 rc=0
    def test_resolve_real_root(self):
        p = run_diyc(REPO_ROOT, "resolve", "--json")
        self.assertEqual(p.returncode, 0, p.stderr)
        r = jload(p)
        self.assertTrue(r["output_dir"].endswith("diy-output"))


if __name__ == "__main__":
    unittest.main()
