# -*- coding: utf-8 -*-
"""baseline 已知遗留台账测试（批次 3.5，D1-D4 用户裁定 2026-09-13）。

覆盖：命中降级 known + exit 0 / 部分命中（STALE 反噬）/ 条目非法（缺 reason）不吞违规 /
坏 YAML 不吞违规 / 无文件行为不变 / 实例隔离 / 写回命令不消费（审计面限定）。
baseline-add（P2，用户裁定后补）：创建并闭环消费 / 追加保留既有条目 / 重复拒绝零写入 /
坏文件拒绝不覆盖 / where 规范化 / 实例隔离 / 缺目录拒绝 / 空 reason 拒绝 / 必填旗标 rc2。
"""
import json
import os
import subprocess
import sys
import unittest
from datetime import date

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)  # import diyc_fixture

import diyc_fixture as fx  # noqa: E402

DIYC = os.path.join(HERE, "..", "skills", "diy-tools", "scripts", "diyc.py")

REVIEW_WHERE = "diy-output/sprint.yaml tasks[S-1].review"


def run_diyc(root, *args, timeout=120):
    return subprocess.run(
        [sys.executable, DIYC, *args, "--project-root", str(root)],
        capture_output=True, text=True, encoding="utf-8", timeout=timeout,
        stdin=subprocess.DEVNULL)


def jload(p):
    return json.loads(p.stdout)


def chk(root, *extra):
    return run_diyc(root, "check", "--type", "review", *extra, "--json")


def review_sprint():
    """恰好 1 条 ROUTE_INVALID 的最小 sprint 夹具（实测 shape）。"""
    return fx.doc_sprint([
        fx.task("S-1", status="review", test_refs=[],
                review={"verdict": "pass", "findings": [
                    {"layer": "correctness", "route": "patch", "detail": "夹具"}]}),
    ])


def baseline_entry(code="ROUTE_INVALID", where=REVIEW_WHERE,
                   reason="夹具裁定：2026-09-13 用户批准豁免"):
    return {"code": code, "where": where, "reason": reason}


class BaselineTests(unittest.TestCase):
    def setUp(self):
        self.root = fx.make_root()
        self.addCleanup(fx.cleanup, self.root)

    def write_baseline(self, entries, instance=None):
        doc = {"baseline": entries}
        if instance:
            path = os.path.join(str(self.root), "diy-output", instance, "diyc-baseline.yaml")
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                yaml.safe_dump(doc, f, allow_unicode=True, sort_keys=False)
        else:
            fx.write_doc(self.root, "diyc-baseline", doc)

    def write_instance_sprint(self, instance, doc):
        path = os.path.join(str(self.root), "diy-output", instance, "sprint.yaml")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(doc, f, allow_unicode=True, sort_keys=False)

    def test_hit_downgrades_to_known_exit0(self):
        fx.write_doc(self.root, "sprint", review_sprint())
        self.write_baseline([baseline_entry()])
        p = chk(self.root)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        r = jload(p)
        self.assertTrue(r["ok"])
        self.assertEqual(r["violations"], [])
        self.assertEqual(len(r["known"]), 1)
        self.assertEqual(r["known"][0]["code"], "ROUTE_INVALID")
        self.assertEqual(r["known"][0]["where"], REVIEW_WHERE)
        self.assertEqual(r["known"][0]["reason"], "夹具裁定：2026-09-13 用户批准豁免")
        self.assertEqual(r["counts"]["known"], 1)

    def test_human_mode_renders_known(self):
        fx.write_doc(self.root, "sprint", review_sprint())
        self.write_baseline([baseline_entry()])
        p = run_diyc(self.root, "check", "--type", "review")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("KNOWN", p.stdout)

    def test_partial_hit_stale_fails(self):
        # 一条命中（吸收）+ 一条悬空（STALE）→ exit 1；被吸收的不再出现在 violations
        fx.write_doc(self.root, "sprint", review_sprint())
        self.write_baseline([
            baseline_entry(),
            baseline_entry(where="diy-output/sprint.yaml tasks[S-9].review"),
        ])
        p = chk(self.root)
        self.assertEqual(p.returncode, 1)
        r = jload(p)
        self.assertEqual([x["code"] for x in r["violations"]], ["BASELINE_STALE"])
        self.assertEqual(r["violations"][0]["where"],
                         "diy-output/diyc-baseline.yaml baseline[1]")
        self.assertEqual(len(r["known"]), 1)
        self.assertEqual(r["counts"]["known"], 1)

    def test_story_scope_no_false_stale(self):
        # --story 任务级单点校验：缩域不构成完整审计，同域其他条目不得被误判悬空
        # （diy-review L3 官方流程用 --story，误报会诱导删真实豁免条目——V 验证发现）
        fx.write_doc(self.root, "sprint", review_sprint())
        self.write_baseline([
            baseline_entry(),
            baseline_entry(where="diy-output/sprint.yaml tasks[S-9].review"),
        ])
        p = run_diyc(self.root, "check", "--type", "review", "--story", "S-1", "--json")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        r = jload(p)
        self.assertEqual(r["violations"], [])
        self.assertEqual(len(r["known"]), 1)

    def test_missing_reason_does_not_absorb(self):
        # 条目非法 → BASELINE_INVALID 且原违规不被吞（安全方向：绝不静默吞违规）
        fx.write_doc(self.root, "sprint", review_sprint())
        self.write_baseline([{"code": "ROUTE_INVALID", "where": REVIEW_WHERE}])
        p = chk(self.root)
        self.assertEqual(p.returncode, 1)
        r = jload(p)
        codes = [x["code"] for x in r["violations"]]
        self.assertIn("BASELINE_INVALID", codes)
        self.assertIn("ROUTE_INVALID", codes)
        self.assertNotIn("known", r)

    def test_broken_yaml_does_not_absorb(self):
        fx.write_doc(self.root, "sprint", review_sprint())
        fx.write_doc(self.root, "diyc-baseline", "baseline: [unclosed\n")
        p = chk(self.root)
        self.assertEqual(p.returncode, 1)
        codes = [x["code"] for x in jload(p)["violations"]]
        self.assertIn("BASELINE_INVALID", codes)
        self.assertIn("ROUTE_INVALID", codes)

    def test_no_baseline_file_behaves_unchanged(self):
        fx.write_doc(self.root, "sprint", review_sprint())
        p = chk(self.root)
        self.assertEqual(p.returncode, 1)
        r = jload(p)
        self.assertNotIn("known", r)
        self.assertNotIn("known", r["counts"])

    def test_instance_isolation(self):
        # 主线 baseline 命中；同一 root 的实例目录无 baseline → 实例检查不豁免
        fx.write_doc(self.root, "sprint", review_sprint())
        self.write_baseline([baseline_entry()])
        self.write_instance_sprint("v2", review_sprint())
        p = run_diyc(self.root, "check", "--type", "review", "--instance", "v2", "--json")
        self.assertEqual(p.returncode, 1)
        self.assertNotIn("known", jload(p))
        p2 = chk(self.root)
        self.assertEqual(p2.returncode, 0)

    def test_unrelated_command_no_false_stale(self):
        # 域匹配：trace 不产 ROUTE_INVALID，review 台账条目不得被当悬空误报
        fx.write_doc(self.root, "sprint", review_sprint())
        self.write_baseline([baseline_entry()])
        p = run_diyc(self.root, "trace", "--json")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        r = jload(p)
        self.assertEqual(r["violations"], [])
        self.assertEqual(r.get("known"), [])

    def test_strict_flag_ignores_baseline(self):
        # 发布/CI 复核：--strict 完全忽略 baseline（known 不生效，STALE 不报）
        fx.write_doc(self.root, "sprint", review_sprint())
        self.write_baseline([baseline_entry()])
        p = chk(self.root, "--strict")
        self.assertEqual(p.returncode, 1)
        r = jload(p)
        self.assertEqual([x["code"] for x in r["violations"]], ["ROUTE_INVALID"])
        self.assertNotIn("known", r)

    def test_writeback_commands_do_not_consume_baseline(self):
        # 审计面限定：写回命令的拒绝不因 baseline 条目而静默放行
        fx.write_doc(self.root, "sprint", fx.doc_sprint([fx.task("S-1", status="pending")]))
        self.write_baseline([baseline_entry(
            code="ILLEGAL_TRANSITION",
            where="diy-output/sprint.yaml tasks[S-1].status")])
        p = run_diyc(self.root, "transition", "--story", "S-1", "--to", "done", "--json")
        self.assertEqual(p.returncode, 1)
        r = jload(p)
        self.assertFalse(r["ok"])
        self.assertNotIn("known", r)
        self.assertIn("ILLEGAL_TRANSITION", [x["code"] for x in r["violations"]])


def baseline_file_text(root, instance=None):
    parts = [str(root), "diy-output"] + ([instance] if instance else [])
    parts.append("diyc-baseline.yaml")
    with open(os.path.join(*parts), encoding="utf-8") as f:
        return f.read()


def write_instance_doc(root, instance, name, doc):
    path = os.path.join(str(root), "diy-output", instance, name + ".yaml")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(doc, f, allow_unicode=True, sort_keys=False)


class BaselineAddTests(unittest.TestCase):
    """P2：baseline-add 写入口（仅用户裁定后调用；重复/损坏拒绝零半写）。"""

    def setUp(self):
        self.root = fx.make_root()
        self.addCleanup(fx.cleanup, self.root)

    def add(self, *extra, code="ROUTE_INVALID", where=REVIEW_WHERE,
            reason="2026-09-13 用户裁定豁免"):
        return run_diyc(self.root, "baseline-add", "--code", code, "--where", where,
                        "--reason", reason, *extra, "--json")

    def test_add_creates_file_then_check_consumes(self):
        # 闭环：新写入的条目随即被 check 消费（known，exit 0）
        fx.write_doc(self.root, "sprint", review_sprint())
        p = self.add()
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        r = jload(p)
        self.assertTrue(r["ok"])
        self.assertEqual(r["entry"], {"code": "ROUTE_INVALID", "where": REVIEW_WHERE,
                                      "reason": "2026-09-13 用户裁定豁免",
                                      "on": date.today().isoformat(), "by": "user"})
        self.assertEqual(r["counts"]["entries"], 1)
        self.assertEqual(r["updated"], date.today().isoformat())
        p2 = chk(self.root)
        self.assertEqual(p2.returncode, 0, p2.stdout + p2.stderr)
        self.assertEqual(len(jload(p2)["known"]), 1)

    def test_add_appends_and_preserves_existing(self):
        fx.write_doc(self.root, "diyc-baseline", {"baseline": [
            dict(baseline_entry(where="diy-output/sprint.yaml tasks[S-7].review"),
                 on="2026-09-01", by="user")]})
        p = self.add()
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        doc = fx.read_doc(self.root, "diyc-baseline")
        self.assertEqual(len(doc["baseline"]), 2)
        self.assertEqual(doc["baseline"][0]["reason"], "夹具裁定：2026-09-13 用户批准豁免")
        self.assertEqual(doc["baseline"][0]["on"], "2026-09-01")  # 既有字段原样保留
        self.assertEqual(doc["baseline"][1]["where"], REVIEW_WHERE)
        self.assertEqual(doc["baseline"][1]["on"], date.today().isoformat())
        self.assertEqual(doc["baseline"][1]["by"], "user")

    def test_add_duplicate_rejected_zero_write(self):
        fx.write_doc(self.root, "diyc-baseline", {"baseline": [baseline_entry()]})
        before = baseline_file_text(self.root)
        p = self.add()
        self.assertEqual(p.returncode, 1)
        self.assertEqual([x["code"] for x in jload(p)["violations"]],
                         ["BASELINE_DUPLICATE"])
        self.assertEqual(baseline_file_text(self.root), before)

    def test_add_duplicate_detects_unnormalized_existing_entry(self):
        # 手工条目的 code 带空白 / where 反斜杠（手工编辑常见形态）——重复判定按规范化语义
        fx.write_doc(self.root, "diyc-baseline", {"baseline": [
            {"code": "ROUTE_INVALID ", "where": REVIEW_WHERE.replace("/", "\\"),
             "reason": "手工条目"}]})
        p = self.add()
        self.assertEqual(p.returncode, 1)
        self.assertEqual([x["code"] for x in jload(p)["violations"]],
                         ["BASELINE_DUPLICATE"])

    def test_add_broken_file_rejected_not_overwritten(self):
        fx.write_doc(self.root, "diyc-baseline", "baseline: [unclosed\n")
        p = self.add()
        self.assertEqual(p.returncode, 1)
        self.assertIn("BASELINE_INVALID", [x["code"] for x in jload(p)["violations"]])
        self.assertEqual(baseline_file_text(self.root), "baseline: [unclosed\n")

    def test_add_normalizes_where_backslash(self):
        fx.write_doc(self.root, "sprint", review_sprint())
        p = self.add(where="diy-output\\sprint.yaml tasks[S-7].review")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        normalized = "diy-output/sprint.yaml tasks[S-7].review"
        self.assertEqual(jload(p)["entry"]["where"], normalized)
        self.assertIn(normalized, baseline_file_text(self.root))

    def test_add_instance_isolation(self):
        write_instance_doc(self.root, "v2", "sprint", review_sprint())
        p = self.add("--instance", "v2")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertTrue(os.path.isfile(os.path.join(
            str(self.root), "diy-output", "v2", "diyc-baseline.yaml")))
        self.assertFalse(os.path.isfile(os.path.join(
            str(self.root), "diy-output", "diyc-baseline.yaml")))

    def test_add_missing_output_dir_rejected(self):
        # 不代建目录（project-root/instance 指错时防呆）
        p = self.add()
        self.assertEqual(p.returncode, 1)
        self.assertEqual([x["code"] for x in jload(p)["violations"]], ["MISSING_FILE"])

    def test_add_blank_reason_rejected(self):
        fx.write_doc(self.root, "sprint", review_sprint())
        p = self.add(reason="  ")
        self.assertEqual(p.returncode, 1)
        self.assertIn("BASELINE_INVALID", [x["code"] for x in jload(p)["violations"]])

    def test_add_requires_all_flags(self):
        p = run_diyc(self.root, "baseline-add", "--code", "X", "--where", "Y", "--json")
        self.assertEqual(p.returncode, 2)

    def test_add_write_failure_reports_internal_error(self):
        # V 复验 F-1（High）：写路径异常不得静默（空 stdout + tmp 残骸）——
        # 台账路径被同名目录占用（os.replace 必败，跨平台）→ INTERNAL_ERROR 回执 rc1；
        # 失败后现场原样保留（目录仍在）、无 .tmp 残骸
        fx.write_doc(self.root, "sprint", review_sprint())
        occupy = os.path.join(str(self.root), "diy-output", "diyc-baseline.yaml")
        os.makedirs(occupy)
        p = self.add()
        self.assertEqual(p.returncode, 1, p.stdout + p.stderr)
        self.assertTrue(p.stdout.strip(), "不得空 stdout 静默失败")
        r = jload(p)
        self.assertFalse(r["ok"])
        self.assertEqual([x["code"] for x in r["violations"]], ["INTERNAL_ERROR"])
        self.assertTrue(os.path.isdir(occupy), "失败不得破坏现场")
        self.assertFalse(os.path.isfile(occupy + ".tmp"), "失败不得留 .tmp 残骸")


if __name__ == "__main__":
    unittest.main()
