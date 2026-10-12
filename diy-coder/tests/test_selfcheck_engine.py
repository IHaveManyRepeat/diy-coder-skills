# -*- coding: utf-8 -*-
"""diy-selfcheck 确定性引擎测试（selfcheck.yaml check 基础校验 + --final 六义务）。

覆盖：
- 用例 1：完整夹具 --final 全绿——三源 findings（多元素 source＋layer＋confidence）、
        disposals 全覆盖、rescans 双轮、b_review、summary ref_checked/ref_false、
        同目录 spec-scan.yaml 配对（ss_ref 可解析）；回执共同键齐全、counts 与真值一致
- 用例 2：六义务逐条缺一即红（① b_review 空 ② summary 缺 ref 键 ③ disposals 缺口/孤儿
        ④ rescans 缺轮 ⑤ [假设] ⑥ ss_ref 解析不到）——同稿非 --final 均绿（义务只在
        --final 生效）；quote 字段 [假设] 豁免（--final 绿）
- 用例 3：ss_ref 正反例——spec-scan.yaml 可解析绿／无 spec-scan.yaml 红／id 解析不到红／
        不带 ss_ref 且无 spec-scan.yaml 绿
- 用例 4：schema 基础违规——缺键（顶层 checks／date／anchor.md5／target.path）／枚举越界
        （status／source 元素／kind／layer）／SC 号段重复 ID_DUP／SC 形态 ID_FMT／
        缺文件 MISSING_FILE／YAML 损坏 UNPARSABLE_YAML
- 用例 5：anchor.commit 缺省不红（单锚降级）；status 草稿不挡 --final（裁④：status 门不加）
- 用例 6：CLI 面——违规码冻结集 VIOLATION_CODES 12 码／违规 where 带检查 ID／人读态非 JSON／
        未知子命令与缺路径参数 exit 2
夹具全部落 tempdir 自建；不读写本仓库真实 diy-output。
运行：cd diy-coder && python -m pytest tests/test_selfcheck_engine.py -q
"""
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.join(HERE, "..", "skills", "diy-selfcheck", "scripts", "selfcheck.py")

COMMON_KEYS = {"ok", "command", "project_root", "output_dir", "final",
               "violations", "warnings", "counts"}
SS_IDS = ("SS-001-01", "SS-001-02")

FROZEN_CODES = {"EMPTY_FIELD", "ENUM_INVALID", "ID_FMT", "ID_DUP", "MISSING_FILE",
                "UNPARSABLE_YAML", "DUTY_B_REVIEW_MISSING", "DUTY_SUMMARY_REF_MISSING",
                "DUTY_DISPOSAL_GAP", "DUTY_RESCAN_MISSING", "HYPOTHESIS_FOUND",
                "SS_REF_UNRESOLVED"}


def run_cli(*args):
    """跑真 CLI，回 (rc, 回执 or None, stdout, stderr)。"""
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    proc = subprocess.run([sys.executable, ENGINE, *args], capture_output=True,
                          text=True, encoding="utf-8", env=env)
    doc = None
    if "--json" in args and proc.stdout.strip().startswith("{"):
        doc = json.loads(proc.stdout)
    return proc.returncode, doc, proc.stdout, proc.stderr


def full_check(**over):
    """完整合法 check（三源 findings＋多元素 source＋layer＋confidence＋全区块）。"""
    check = {
        "id": "SC-001",
        "date": "2026-10-11",
        "status": "已定稿",
        "anchor": {"md5": "d41d8cd98f00b204e9800998ecf8427e", "commit": "03b4e35",
                   "exec_form": "编排者合并", "shards": 3},
        "target": {"kind": "任务书",
                   "path": ".analysis/2026-10-07-execution-plan/taskbook-batch2c.md"},
        "findings": [
            {"n": 1, "source": ["预演"], "ss_ref": "SS-001-01", "severity": "阻断"},
            {"n": 2, "source": ["引用核对"], "claim": "文中称三片合并 28 条",
             "actual": "spec-scan.yaml 实为 28 条", "severity": "建议"},
            {"n": 3, "source": ["对抗"], "layer": "盲猎", "issue": "B 部分缺收口出口",
             "severity": "观察"},
            {"n": 4, "source": ["预演", "对抗"], "layer": "边界猎手",
             "ss_ref": "SS-001-02", "confidence": 2, "issue": "交叉命中同一条歧义",
             "severity": "建议"},
        ],
        "disposals": [
            {"finding": 1, "level": "阻断", "action": "修入", "landing": "SKILL.md:23"},
            {"finding": 2, "level": "建议", "action": "采纳", "landing": "03-merge.md:6"},
            {"finding": 3, "level": "观察", "action": "留痕", "landing": "revisions"},
            {"finding": 4, "level": "建议", "action": "合并", "landing": "05-close.md:13"},
        ],
        "rescans": {"round1": "复扫一轮：旧值全清", "round2": "复扫二轮：零回归",
                    "cleared": []},
        "b_review": "B 部分：三机制评价，编排闭环成立。",
        "revisions": [],
        "summary": {"total": 4, "by_source": {"预演": 2, "引用核对": 1, "对抗": 2},
                    "ref_checked": 12, "ref_false": 1},
    }
    check.update(over)
    return check


def full_doc(**over):
    check = full_check()
    check.update(over)
    return {"project": {"name": "demo", "created": "2026-10-11",
                        "updated": "2026-10-11"},
            "schema": 2,
            "checks": [check]}


def spec_scan_doc(ids=SS_IDS):
    findings = [{"id": fid, "type": "分支无定义", "where": "SKILL.md:1",
                 "quote": "原文", "read_as": "读作", "stuck": "卡在", "would_guess": "会猜",
                 "severity": "阻断", "source": ["卡点"]} for fid in ids]
    return {"project": {"name": "demo", "created": "2026-10-11",
                        "updated": "2026-10-11"},
            "schema": 2,
            "scans": [{"id": "SS-001", "target": {"kind": "file", "path": "SKILL.md"},
                       "units": [], "findings": findings,
                       "summary": {"total": len(findings), "blocker": len(findings),
                                   "major": 0, "minor": 0, "units_total": 0,
                                   "by_source": {"卡点": len(findings), "穷举": 0,
                                                 "交叉认证": 0},
                                   "units_scanned": 0}}],
            "revisions": []}


def codes_of(doc):
    return [item["code"] for item in doc["violations"]]


class EngineCase(unittest.TestCase):
    """tmp 目录夹具 + 跑真 CLI 的公共骨架。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="selfcheck-engine-")
        self.addCleanup(self.tmp.cleanup)
        self.path = os.path.join(self.tmp.name, "selfcheck.yaml")

    def write(self, doc, name="selfcheck.yaml"):
        target = os.path.join(self.tmp.name, name)
        with io.open(target, "w", encoding="utf-8") as handle:
            yaml.safe_dump(doc, handle, allow_unicode=True, sort_keys=False)
        return target

    def run_check(self, *flags, doc=None, spec=None, path=None, as_json=True):
        if doc is not None:
            self.write(doc)
        if spec is not None:
            self.write(spec, "spec-scan.yaml")
        target = path or self.path
        args = ["check", target, "--project-root", self.tmp.name]
        if as_json:
            args.append("--json")
        return run_cli(*args, *flags)

    def codes(self, *flags, **kw):
        rc, doc, _, _ = self.run_check(*flags, **kw)
        self.assertIn(rc, (0, 1), doc)
        return rc, codes_of(doc)


# ---- 1 完整夹具：--final 全绿 + 回执契约 -------------------------------------

class HappyPathTests(EngineCase):
    def test_full_fixture_green_final(self):
        rc, doc, _, _ = self.run_check("--final", doc=full_doc(),
                                       spec=spec_scan_doc())
        self.assertEqual(rc, 0, doc)
        self.assertTrue(doc["ok"])
        self.assertEqual(doc["violations"], [])
        self.assertTrue(doc["final"])

    def test_receipt_common_keys(self):
        _, doc, _, _ = self.run_check("--final", doc=full_doc(),
                                      spec=spec_scan_doc())
        self.assertTrue(COMMON_KEYS.issubset(set(doc)), doc)
        self.assertIsInstance(doc["violations"], list)
        self.assertIsInstance(doc["warnings"], list)
        self.assertTrue(doc["output_dir"].endswith("selfcheck-engine-") or
                        os.path.isdir(doc["output_dir"]))

    def test_counts_match_fixture(self):
        _, doc, _, _ = self.run_check("--final", doc=full_doc(),
                                      spec=spec_scan_doc())
        self.assertEqual(doc["counts"],
                         {"checks": 1, "findings": 4, "disposals": 4})

    def test_draft_status_not_final_gate(self):
        """裁④：status 门不加——草稿也能过 --final（status 只做基础枚举校验）。"""
        rc, doc, _, _ = self.run_check("--final", doc=full_doc(status="草稿"),
                                       spec=spec_scan_doc())
        self.assertEqual(rc, 0, doc)

    def test_human_mode_is_not_json(self):
        rc, _, out, _ = self.run_check(doc=full_doc(), spec=spec_scan_doc(),
                                       as_json=False)
        self.assertEqual(rc, 0, out)
        self.assertFalse(out.strip().startswith("{"))
        self.assertIn("PASS：", out)
        self.assertIn("汇总：", out)


# ---- 2 六义务逐条：缺一即红（同稿非 --final 均绿） ---------------------------

class DutyTests(EngineCase):
    def assert_duty_red(self, doc, code, spec=None):
        """基础（非 --final）绿 → --final 单码红。"""
        rc, _, _, _ = self.run_check(doc=doc, spec=spec)
        self.assertEqual(rc, 0, "基础校验应绿：%s" % doc)
        rc, got, _, _ = self.run_check("--final", doc=doc, spec=spec)
        self.assertEqual(rc, 1, got)
        self.assertIn(code, codes_of(got))
        return got

    def test_duty1_b_review_empty(self):
        got = self.assert_duty_red(full_doc(b_review=""),
                                   "DUTY_B_REVIEW_MISSING")
        self.assertIn("SC-001", got["violations"][0]["where"])

    def test_duty2_summary_ref_missing(self):
        doc = full_doc()
        del doc["checks"][0]["summary"]["ref_checked"]
        self.assert_duty_red(doc, "DUTY_SUMMARY_REF_MISSING")

    def test_duty3_disposal_gap(self):
        doc = full_doc()
        doc["checks"][0]["disposals"].pop()   # finding n=4 无处置
        self.assert_duty_red(doc, "DUTY_DISPOSAL_GAP")

    def test_duty3_orphan_disposal(self):
        doc = full_doc()
        doc["checks"][0]["disposals"].append({"finding": 9, "action": "落空"})
        self.assert_duty_red(doc, "DUTY_DISPOSAL_GAP")

    def test_duty4_rescan_round_missing(self):
        doc = full_doc()
        del doc["checks"][0]["rescans"]["round2"]
        self.assert_duty_red(doc, "DUTY_RESCAN_MISSING")

    def test_duty5_assumption_red(self):
        doc = full_doc()
        doc["checks"][0]["findings"][2]["issue"] = "[假设] 这里可能缺 B 出口"
        got = self.assert_duty_red(doc, "HYPOTHESIS_FOUND")
        hit = [item for item in got["violations"]
               if item["code"] == "HYPOTHESIS_FOUND"]
        self.assertEqual(len(hit), 1)
        self.assertIn("findings[2]", hit[0]["where"])

    def test_duty5_quote_exempt(self):
        doc = full_doc()
        doc["checks"][0]["findings"][1]["quote"] = "引文含 [假设] 字样——豁免"
        rc, got, _, _ = self.run_check("--final", doc=doc, spec=spec_scan_doc())
        self.assertEqual(rc, 0, got)

    def test_duty6_ss_ref_resolves(self):
        rc, doc, _, _ = self.run_check("--final", doc=full_doc(),
                                       spec=spec_scan_doc())
        self.assertEqual(rc, 0, doc)

    def test_duty6_no_spec_scan_red(self):
        rc, doc, _, _ = self.run_check("--final", doc=full_doc())
        self.assertEqual(rc, 1, doc)
        self.assertIn("SS_REF_UNRESOLVED", codes_of(doc))

    def test_duty6_unresolved_id_red(self):
        rc, doc, _, _ = self.run_check("--final", doc=full_doc(),
                                       spec=spec_scan_doc(ids=("SS-001-01",)))
        self.assertEqual(rc, 1, doc)
        unresolved = [item for item in doc["violations"]
                      if item["code"] == "SS_REF_UNRESOLVED"]
        self.assertEqual(len(unresolved), 1)   # 只有 SS-001-02 解析不到
        self.assertIn("SS-001-02", unresolved[0]["msg"])

    def test_duty6_no_ss_ref_green_without_spec_scan(self):
        doc = full_doc()
        for finding in doc["checks"][0]["findings"]:
            finding.pop("ss_ref", None)
        rc, got, _, _ = self.run_check("--final", doc=doc)
        self.assertEqual(rc, 0, got)


# ---- 3 schema 基础校验（每次 check 都跑） ------------------------------------

class SchemaBasicTests(EngineCase):
    def assert_single(self, doc, code):
        rc, got, _, _ = self.run_check(doc=doc)
        self.assertEqual(rc, 1, got)
        self.assertEqual(codes_of(got), [code], got)
        return got

    def test_missing_top_checks(self):
        doc = full_doc()
        del doc["checks"]
        self.assert_single(doc, "EMPTY_FIELD")

    def test_missing_check_date(self):
        doc = full_doc()
        del doc["checks"][0]["date"]
        self.assert_single(doc, "EMPTY_FIELD")

    def test_missing_anchor_md5(self):
        doc = full_doc()
        del doc["checks"][0]["anchor"]["md5"]
        self.assert_single(doc, "EMPTY_FIELD")

    def test_missing_target_path(self):
        doc = full_doc()
        del doc["checks"][0]["target"]["path"]
        self.assert_single(doc, "EMPTY_FIELD")

    def test_status_enum_invalid(self):
        self.assert_single(full_doc(status="定稿"), "ENUM_INVALID")

    def test_source_element_enum_invalid(self):
        doc = full_doc()
        doc["checks"][0]["findings"][0]["source"] = ["卡点"]   # spec-scan 值域越界
        self.assert_single(doc, "ENUM_INVALID")

    def test_source_empty_array(self):
        doc = full_doc()
        doc["checks"][0]["findings"][0]["source"] = []
        self.assert_single(doc, "EMPTY_FIELD")

    def test_kind_enum_invalid(self):
        doc = full_doc()
        doc["checks"][0]["target"]["kind"] = "prd"
        self.assert_single(doc, "ENUM_INVALID")

    def test_layer_enum_invalid(self):
        doc = full_doc()
        doc["checks"][0]["findings"][2]["layer"] = "盲点"
        self.assert_single(doc, "ENUM_INVALID")

    def test_duplicate_sc_id(self):
        doc = full_doc()
        doc["checks"].append(full_check())
        self.assert_single(doc, "ID_DUP")

    def test_bad_sc_format(self):
        self.assert_single(full_doc(id="SC-01"), "ID_FMT")

    def test_missing_file(self):
        rc, doc, _, _ = self.run_check(path=os.path.join(self.tmp.name, "absent.yaml"))
        self.assertEqual(rc, 1)
        self.assertEqual(codes_of(doc), ["MISSING_FILE"])

    def test_unparsable_yaml(self):
        with io.open(self.path, "w", encoding="utf-8") as handle:
            handle.write("project: [unclosed\n")
        rc, doc, _, _ = self.run_check()
        self.assertEqual(rc, 1)
        self.assertEqual(codes_of(doc), ["UNPARSABLE_YAML"])

    def test_empty_checks_list_passes(self):
        doc = full_doc()
        doc["checks"] = []
        rc, got, _, _ = self.run_check(doc=doc)
        self.assertEqual(rc, 0, got)

    def test_anchor_commit_optional_green_final(self):
        """单锚降级：anchor.commit 缺省不红（基础与 --final 同绿）。"""
        doc = full_doc()
        del doc["checks"][0]["anchor"]["commit"]
        rc, got, _, _ = self.run_check("--final", doc=doc, spec=spec_scan_doc())
        self.assertEqual(rc, 0, got)


# ---- 4 CLI 面：冻结集 / where 定位 / 用法错误 -------------------------------

class CliTests(EngineCase):
    def test_violation_codes_frozen(self):
        spec = importlib.util.spec_from_file_location("selfcheck_engine", ENGINE)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(set(module.VIOLATION_CODES), FROZEN_CODES)

    def test_check_scoped_violation_carries_check_id(self):
        doc = full_doc()
        doc["checks"][0]["findings"][2]["layer"] = "盲点"
        rc, got, _, _ = self.run_check(doc=doc)
        self.assertEqual(rc, 1)
        self.assertTrue(all("SC-001" in item["where"]
                            for item in got["violations"]), got)

    def test_unknown_subcommand_exit2(self):
        rc, _, _, _ = run_cli("frobnicate")
        self.assertEqual(rc, 2)

    def test_output_dir_form_used_by_05_close(self):
        """05-close 终门命令形态：check --final --project-root … --output-dir … --json（无位置参数）。"""
        self.write(full_doc())
        self.write(spec_scan_doc(), "spec-scan.yaml")
        rc, doc, _, _ = run_cli("check", "--final", "--project-root", self.tmp.name,
                                "--output-dir", self.tmp.name, "--json")
        self.assertEqual(rc, 0, doc)
        self.assertTrue(doc["ok"])

    def test_missing_path_arg_exit2(self):
        rc, _, _, _ = run_cli("check")
        self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()
