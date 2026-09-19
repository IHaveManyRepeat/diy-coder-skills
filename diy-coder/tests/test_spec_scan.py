# -*- coding: utf-8 -*-
"""diy-spec-scan 确定性引擎 e2e 测试（规格预演扫描技能）。

覆盖：
- 用例 1：collect 单文件目标 → 文件清单 + 行数 + 二级标题单元切分（`###` 不算；无二级标题
          时整文件一单元、单元名取文件名）
- 用例 2：collect 技能目录（SKILL.md + steps/）→ SKILL.md + steps/*.md 按文件名排序
          （相对 --target 按 project-root 解析）
- 用例 3：collect 普通目录 → 本层 *.md + 一层子目录 *.md（再深一层不算，不无限深挖）
- 用例 4：collect 空目录 / 不存在的目标 → exit 1 + MISSING_FILE
- 用例 5：collect 非 UTF-8 文件 → SCAN_TRUNCATED warning、仍列出、行数记 0、exit 0
- 用例 6：check 合法报告 → exit 0 唯一放行
- 用例 7：check 非法 type 枚举 → exit 1 + ENUM_INVALID
- 用例 8：check would_guess 为空 → exit 1 + EMPTY_FIELD（msg 指明哪条 finding 哪个字段）
- 用例 9：check summary 计数与 findings 真值不符 → exit 1 + SET_MISMATCH
- 用例 10：check --final 有单元未扫 → exit 1（非 --final 同稿 exit 0）
- 用例 11：check --final 的 [假设] 字面量禁令 —— `quote` 字段豁免（引文是证据，
           2026-09-16 裁定）；非 quote 字段仍判 exit 1 + ASSUMPTION_PRESENT
- 用例 12：check schema 违规表（id 形态 / 重复 ID / where 形态 / severity 越界 /
           缺 project 键 / 缺字段 / YAML 损坏）
- 用例 13：check 缺 spec-scan.yaml → exit 1 + MISSING_FILE、零 Traceback
- 用例 14：契约冒烟（--json 单行可解析 + 共同键齐全 + where 正斜杠相对；无 --json 时
           每条违规一行 `CODE where: msg` + 末尾汇总行）
- 用例 15：--output-dir 与 collect --target 必填（用法错误 exit 2）
夹具全部落 tempdir 自建；不读写本仓库真实 diy-output。
运行：cd diy-coder && python -m unittest discover -s tests -p "test_spec_scan.py" -v
"""
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.join(HERE, "..", "skills", "diy-spec-scan", "scripts", "spec_scan.py")
NL = chr(10)

# 11 行：一级标题不算单元，`### ` 不算二级标题
SKILL_MD = NL.join([
    "# 技能标题",
    "",
    "## 激活段",
    "",
    "内容一",
    "",
    "### 三级标题不算单元",
    "",
    "## 步骤一",
    "",
    "内容二",
]) + NL

# 3 行：无二级标题 → 整个文件一个单元，单元名取文件名
PLAIN_MD = NL.join([
    "# 只有一级标题",
    "",
    "正文一句。",
]) + NL

STEP_A = NL.join(["## 步骤甲", "", "甲内容。"]) + NL
STEP_B = NL.join(["## 步骤乙", "", "乙内容。"]) + NL

SPEC_SCAN_YAML = NL.join([
    "project:",
    "  name: mini",
    "  created: '2026-09-15'",
    "  updated: '2026-09-15'",
    "scans:",
    "- id: SS-001",
    "  target: {kind: dir, path: skills/diy-dev}",
    "  units:",
    "  - {unit: 激活段, path: skills/diy-dev/SKILL.md, scanned: true}",
    "  - {unit: 步骤一, path: skills/diy-dev/steps/01-init.md, scanned: true}",
    "  findings:",
    "  - id: SS-001-01",
    "    type: 分支无定义",
    "    where: 'skills/diy-dev/SKILL.md:42'",
    "    quote: 按需选择合适的方式处理",
    "    read_as: 作者默认实现者知道怎么选",
    "    stuck: 不知道何时走哪条分支",
    "    would_guess: 我会一律走默认路径，忽略另一分支",
    "    severity: 阻断",
    "  - id: SS-001-02",
    "    type: 术语冲突",
    "    where: skills/diy-dev/steps/01-init.md",
    "    quote: 优先级高的先做",
    "    read_as: 优先级排序规则未定义",
    "    stuck: 无法判断先后",
    "    would_guess: 我会按文件出现顺序执行",
    "    severity: 观察",
    "  summary: {total: 2, blocker: 1, major: 0, minor: 1, units_total: 2, units_scanned: 2}",
    "revisions: []",
]) + NL


def run_engine(args, cwd=None):
    return subprocess.run([sys.executable, ENGINE] + args,
                          capture_output=True, text=True, encoding="utf-8", cwd=cwd)


class EngineCase(unittest.TestCase):
    """tmp 项目根 + diy-output 目录的公共夹具。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="spec-scan-")
        self.root = self.tmp.name
        self.out = os.path.join(self.root, "diy-output")
        os.makedirs(self.out, exist_ok=True)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, rel, content, binary=False):
        path = os.path.join(self.root, rel)
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        if binary:
            with io.open(path, "wb") as f:
                f.write(content)
        else:
            with io.open(path, "w", encoding="utf-8") as f:
                f.write(content)
        return path

    def collect(self, *extra):
        return run_engine(["collect", "--project-root", self.root,
                           "--output-dir", self.out, "--json"] + list(extra))

    def check(self, *extra):
        return run_engine(["check", "--project-root", self.root,
                           "--output-dir", self.out, "--json"] + list(extra))

    def write_spec_scan(self, text):
        self.write("diy-output/spec-scan.yaml", text)

    def codes(self, result):
        return [item["code"] for item in json.loads(result.stdout)["violations"]]


class CollectTests(EngineCase):

    # trace: 契约 collect（单文件目标 → 文件清单 + 行数 + 二级标题单元切分）
    def test_collect_single_file_target(self):
        self.write("docs/spec.md", SKILL_MD)
        r = self.collect("--target", os.path.join(self.root, "docs", "spec.md"))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertTrue(data["ok"])
        self.assertEqual(data["target"]["kind"], "file")
        self.assertEqual(data["target"]["path"], "docs/spec.md")
        self.assertEqual(data["target"]["files"],
                         [{"path": "docs/spec.md", "lines": 11,
                           "units": ["激活段", "步骤一"]}])
        self.assertEqual(data["target"]["total_lines"], 11)
        self.assertEqual(data["counts"], {"files": 1, "lines": 11, "units": 2})

    # trace: 契约 collect（无二级标题 → 整个文件一个单元，单元名取文件名）
    def test_collect_file_without_heading_uses_filename(self):
        self.write("docs/plain.md", PLAIN_MD)
        r = self.collect("--target", os.path.join(self.root, "docs", "plain.md"))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        entry = json.loads(r.stdout)["target"]["files"][0]
        self.assertEqual(entry["lines"], 3)
        self.assertEqual(entry["units"], ["plain.md"])

    # trace: 契约 collect（技能目录 → SKILL.md + steps/*.md 按文件名排序；相对 target 按 project-root 解析）
    def test_collect_skill_directory(self):
        self.write("skill/SKILL.md", SKILL_MD)
        self.write("skill/steps/02-b.md", STEP_B)
        self.write("skill/steps/01-a.md", STEP_A)
        self.write("skill/notes.md", "不该入选：含 SKILL.md 时只枚举 SKILL.md + steps/")
        r = self.collect("--target", "skill")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual(data["target"]["kind"], "dir")
        self.assertEqual([f["path"] for f in data["target"]["files"]],
                         ["skill/SKILL.md", "skill/steps/01-a.md", "skill/steps/02-b.md"])
        self.assertEqual(data["counts"]["files"], 3)
        self.assertNotIn("notes.md", r.stdout)

    # trace: 契约 collect（普通目录 → 本层 *.md + 一层子目录 *.md，不再深挖）
    def test_collect_plain_directory_one_level(self):
        self.write("area/a.md", PLAIN_MD)
        self.write("area/sub/b.md", STEP_A)
        self.write("area/sub/deep/c.md", STEP_B)
        r = self.collect("--target", os.path.join(self.root, "area"))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual([f["path"] for f in data["target"]["files"]],
                         ["area/a.md", "area/sub/b.md"])
        self.assertNotIn("deep", r.stdout)
        self.assertEqual(data["counts"]["units"], 2)

    # trace: 契约 collect（空目录 / 不存在目标 → exit 1 + MISSING_FILE，零产出）
    def test_collect_empty_and_missing_target_refused(self):
        os.makedirs(os.path.join(self.root, "empty"), exist_ok=True)
        r = self.collect("--target", os.path.join(self.root, "empty"))
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertEqual(self.codes(r), ["MISSING_FILE"])
        data = json.loads(r.stdout)
        self.assertEqual(data["target"]["files"], [])
        self.assertEqual(data["target"]["kind"], "dir")
        self.assertEqual(data["counts"], {"files": 0, "lines": 0, "units": 0})

        r2 = self.collect("--target", os.path.join(self.root, "no-such-dir"))
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertEqual(self.codes(r2), ["MISSING_FILE"])
        self.assertEqual(json.loads(r2.stdout)["target"]["kind"], "file")

    # trace: 契约 collect（非 UTF-8 → SCAN_TRUNCATED warning，文件仍列出、行数记 0、不阻断）
    def test_collect_truncated_file_warns_and_passes(self):
        self.write("docs/bad.md", b"## \xff\xfe not utf8\n", binary=True)
        r = self.collect("--target", os.path.join(self.root, "docs", "bad.md"))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertTrue(data["ok"])
        self.assertEqual(data["target"]["files"],
                         [{"path": "docs/bad.md", "lines": 0, "units": []}])
        self.assertEqual([w["code"] for w in data["warnings"]], ["SCAN_TRUNCATED"])
        self.assertEqual(data["violations"], [])


class CheckTests(EngineCase):

    # trace: 契约 check（合法报告 → exit 0 唯一放行）
    def test_check_legal_report_passes(self):
        self.write_spec_scan(SPEC_SCAN_YAML)
        r = self.check("--final")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertTrue(data["ok"])
        self.assertEqual(data["violations"], [])
        self.assertEqual(data["counts"]["scans"], 1)
        self.assertEqual(data["counts"]["findings"], 2)
        self.assertEqual(data["counts"]["by_severity"], {"阻断": 1, "观察": 1})

    # trace: 契约 check（type 不在八值枚举 → ENUM_INVALID）
    def test_check_type_enum_rejected(self):
        self.write_spec_scan(SPEC_SCAN_YAML.replace("type: 术语冲突", "type: MAYBE_WRONG"))
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertEqual(self.codes(r), ["ENUM_INVALID"])
        self.assertIn("MAYBE_WRONG", json.loads(r.stdout)["violations"][0]["msg"])

    # trace: 契约 check（would_guess 为空 → EMPTY_FIELD；msg 指明哪条 finding 哪个字段）
    def test_check_empty_would_guess_rejected(self):
        self.write_spec_scan(SPEC_SCAN_YAML.replace(
            "would_guess: 我会一律走默认路径，忽略另一分支", 'would_guess: ""'))
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        data = json.loads(r.stdout)
        self.assertEqual(self.codes(r), ["EMPTY_FIELD"])
        violation = data["violations"][0]
        self.assertIn("would_guess", violation["msg"])
        self.assertIn("SS-001-01", violation["msg"])
        self.assertTrue(violation["where"].endswith("scans[0].findings[0].would_guess"))

    # trace: 契约 check（summary 计数与 findings 真值不符 → SET_MISMATCH）
    def test_check_summary_mismatch_rejected(self):
        self.write_spec_scan(SPEC_SCAN_YAML.replace("summary: {total: 2", "summary: {total: 3"))
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertEqual(self.codes(r), ["SET_MISMATCH"])
        self.assertIn("total", json.loads(r.stdout)["violations"][0]["msg"])

        self.write_spec_scan(SPEC_SCAN_YAML.replace("units_scanned: 2}", "units_scanned: 1}"))
        r2 = self.check()
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertEqual(self.codes(r2), ["SET_MISMATCH"])

    # trace: 契约 check --final（有单元未扫 → SET_MISMATCH；同稿非 --final 放行）
    def test_check_final_requires_all_units_scanned(self):
        text = (SPEC_SCAN_YAML
                .replace("path: skills/diy-dev/SKILL.md, scanned: true",
                         "path: skills/diy-dev/SKILL.md, scanned: false")
                .replace("units_scanned: 2}", "units_scanned: 1}"))
        self.write_spec_scan(text)
        r = self.check()
        self.assertEqual(r.returncode, 0, r.stdout)  # 非 --final：未扫是合法中间态
        r2 = self.check("--final")
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertEqual(self.codes(r2), ["SET_MISMATCH"])
        self.assertIn("scanned", json.loads(r2.stdout)["violations"][0]["msg"])

    # trace: 契约 check --final（零 [假设] 字面量；quote 豁免——2026-09-16 裁定）
    def test_check_final_quote_is_exempt_from_assumption_literal(self):
        # 引文是证据：被扫规格本身可能含该标记，逐字引用不得被判违规
        text = SPEC_SCAN_YAML.replace(
            "quote: 按需选择合适的方式处理",
            "quote: 此处须带 [假设] 前缀（引被扫规格原文）")
        self.write_spec_scan(text)
        r = self.check("--final")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertEqual(self.codes(r), [])

    # trace: 契约 check --final（非 quote 字段仍禁该字面量——扫描器自己的推断须先落定）
    def test_check_final_rejects_assumption_literal_outside_quote(self):
        text = SPEC_SCAN_YAML.replace(
            "stuck: 不知道何时走哪条分支", "stuck: 不知道何时走哪条分支（[假设]）")
        self.write_spec_scan(text)
        r = self.check()
        self.assertEqual(r.returncode, 0, r.stdout)  # 非 --final 不触发
        r2 = self.check("--final")
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertEqual(self.codes(r2), ["ASSUMPTION_PRESENT"])

    # trace: 契约 check（schema 违规表：id 形态 / 重复 ID / where 形态 / severity / 缺项 / 损坏）
    def test_check_schema_violations(self):
        cases = [
            ("ENUM_INVALID", "id: SS-001", "id: SS-1", "scan id 须为 SS-0nn"),
            ("ENUM_INVALID", "id: SS-001-01", "id: SS-001-1", "finding id 须为 SS-0nn-nn"),
            ("ENUM_INVALID", "where: 'skills/diy-dev/SKILL.md:42'",
             "where: 'skills/diy-dev/SKILL.md:四二'", "where 行号须为数字"),
            ("ENUM_INVALID", "severity: 观察", "severity: trivial", "severity 越界"),
            ("EMPTY_FIELD", "would_guess: 我会一律走默认路径，忽略另一分支", None, "四件套缺一"),
            ("EMPTY_FIELD", "    quote: 优先级高的先做" + NL, "", "quote 为空"),
            ("EMPTY_FIELD", "  created: '2026-09-15'" + NL, "", "project.created 缺失"),
            ("EMPTY_FIELD", "revisions: []" + NL, "", "revisions 缺失"),
            ("UNPARSABLE_YAML", None, None, "YAML 损坏"),
        ]
        for code, old, new, note in cases:
            text = "scans: [" if old is None else (
                SPEC_SCAN_YAML.replace(old, new) if new is not None
                else SPEC_SCAN_YAML.replace(old, ""))
            self.write_spec_scan(text)
            r = self.check()
            self.assertEqual(r.returncode, 1, "%s 未拒：%s" % (note, r.stdout))
            self.assertIn(code, self.codes(r), "%s 未报 %s：%s" % (note, code, r.stdout))
        # 重复 ID：整条 scan 复制一份（target path 保持原样，只放大 ID 面）
        block = SPEC_SCAN_YAML.split("scans:" + NL, 1)[1].replace("revisions: []" + NL, "")
        self.write_spec_scan(SPEC_SCAN_YAML.replace("revisions: []" + NL, "") + block)
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("DUPLICATE_ID", self.codes(r), r.stdout)

    # trace: 契约 check（缺 spec-scan.yaml → 结构化 MISSING_FILE，非 Traceback）
    def test_check_missing_file_is_structured(self):
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertNotIn("Traceback", r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual([x["code"] for x in data["violations"]], ["MISSING_FILE"])
        self.assertIn("spec-scan.yaml", data["violations"][0]["where"])
        self.assertEqual(data["counts"]["scans"], 0)


class ContractTests(EngineCase):

    # trace: 引擎契约冒烟（--json 单行 + 可解析 + 共同键齐全 + where 正斜杠相对）
    def test_json_receipt_single_line_and_common_keys(self):
        self.write("docs/spec.md", SKILL_MD)
        common = {"ok", "command", "project_root", "output_dir", "violations",
                  "warnings", "counts"}
        r = self.collect("--target", os.path.join(self.root, "docs", "spec.md"))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(len(r.stdout.strip().splitlines()), 1, "collect --json 须单行")
        data = json.loads(r.stdout)
        self.assertTrue(common <= set(data), "collect 回执缺共同键")
        self.assertEqual(data["command"], "collect")
        self.assertEqual(data["project_root"], self.root)
        self.assertIn("target", data)
        self.assertNotIn("\\", data["target"]["path"])

        self.write_spec_scan(SPEC_SCAN_YAML.replace("severity: 观察", "severity: trivial"))
        r2 = self.check()
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertEqual(len(r2.stdout.strip().splitlines()), 1, "check --json 须单行")
        data2 = json.loads(r2.stdout)
        self.assertTrue(common <= set(data2), "check 回执缺共同键")
        self.assertEqual(data2["command"], "check")
        self.assertEqual(data2["output_dir"], self.out.replace("\\", "/"))
        for item in data2["violations"]:
            self.assertNotIn("\\", item["where"])
            self.assertFalse(item["where"].startswith("/"), item["where"])

    # trace: 引擎契约冒烟（无 --json：每条违规一行 `CODE where: msg` + 末尾汇总行）
    def test_human_output_has_summary_line(self):
        self.write("docs/spec.md", SKILL_MD)
        r = run_engine(["collect", "--project-root", self.root,
                        "--output-dir", self.out,
                        "--target", os.path.join(self.root, "docs", "spec.md")])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("docs/spec.md", r.stdout)
        self.assertTrue(r.stdout.strip().splitlines()[-1].startswith("汇总："), r.stdout)

        self.write_spec_scan(SPEC_SCAN_YAML.replace("type: 术语冲突", "type: MAYBE_WRONG"))
        r2 = run_engine(["check", "--project-root", self.root, "--output-dir", self.out])
        self.assertEqual(r2.returncode, 1, r2.stdout)
        lines = [line for line in r2.stdout.strip().splitlines() if line.strip()]
        self.assertTrue(lines[-1].startswith("汇总："), r2.stdout)
        self.assertTrue(lines[0].startswith("ENUM_INVALID diy-output/spec-scan.yaml.scans[0]"
                                            ".findings[1].type: "), lines[0])
        self.assertNotIn("{", r2.stdout)  # 人读态不是 JSON

    # trace: 引擎契约（--output-dir 必填、collect --target 必填 → argparse 用法错误 exit 2）
    def test_required_arguments(self):
        self.assertEqual(run_engine(["check", "--project-root", self.root]).returncode, 2)
        self.assertEqual(run_engine(["collect", "--project-root", self.root,
                                     "--target", "x"]).returncode, 2)
        self.assertEqual(run_engine(["collect", "--project-root", self.root,
                                     "--output-dir", self.out]).returncode, 2)


if __name__ == "__main__":
    unittest.main()
