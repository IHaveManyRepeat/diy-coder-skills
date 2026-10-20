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
- 用例 16：SKILL.md / steps 契约冒烟（中文化轮 2026-09-19——母本 §1/§3/§4/§6 逐字 +
          §2 自定短块（母本 §8 登记的非成员变体）+ 四段中文标题 ≤105 行 + B-24 语义条目）
- 用例 17：check source 数组 / schema 分层（元素越界 → ENUM_INVALID；schema≥2 缺 source
           或空数组 → EMPTY_FIELD；无 schema 存量缺 source 缺省 [卡点] 兼容不报错；
           顶层 schema: 2 写入面在场；counts.by_source 按元素各计与夹具分法一致）
夹具全部落 tempdir 自建；不读写本仓库真实 diy-output。
运行：cd diy-coder && python -m unittest discover -s tests -p "test_spec_scan.py" -v
"""
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.join(HERE, "..", "skills", "diy-spec-scan")
ENGINE = os.path.join(SKILL_DIR, "scripts", "spec_scan.py")
SKILL_MD_PATH = os.path.join(SKILL_DIR, "SKILL.md")
STEPS_DIR = os.path.join(SKILL_DIR, "steps")
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
    "schema: 2",
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
    "    source: [卡点]",
    "  - id: SS-001-02",
    "    type: 术语冲突",
    "    where: skills/diy-dev/steps/01-init.md",
    "    quote: 优先级高的先做",
    "    read_as: 优先级排序规则未定义",
    "    stuck: 无法判断先后",
    "    would_guess: 我会按文件出现顺序执行",
    "    severity: 观察",
    "    source: [卡点, 穷举, 交叉认证]",
    ("  summary: {total: 2, blocker: 1, major: 0, minor: 1, units_total: 2, "
     "by_source: {卡点: 2, 穷举: 1, 交叉认证: 1}, units_scanned: 2}"),
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

    # trace: 批 2a §5.4 ①——source 元素越界 → ENUM_INVALID（schema 分层不豁免枚举值域）
    def test_check_source_element_out_of_enum_rejected(self):
        self.write_spec_scan(SPEC_SCAN_YAML.replace("source: [卡点]", "source: [外部]"))
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertEqual(self.codes(r), ["ENUM_INVALID"])
        violation = json.loads(r.stdout)["violations"][0]
        self.assertIn("外部", violation["msg"])
        self.assertIn("卡点|穷举|交叉认证", violation["msg"])
        self.assertTrue(violation["where"].endswith("findings[0].source"),
                        violation["where"])

    # trace: 批 2a §5.4 ②——schema≥2 时 source 缺失 / 空数组 → EMPTY_FIELD
    def test_check_schema_v2_requires_nonempty_source(self):
        self.write_spec_scan(SPEC_SCAN_YAML.replace("    source: [卡点]" + NL, ""))
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertEqual(self.codes(r), ["EMPTY_FIELD"])
        violation = json.loads(r.stdout)["violations"][0]
        self.assertIn("source", violation["msg"])
        self.assertTrue(violation["where"].endswith("findings[0].source"),
                        violation["where"])

        self.write_spec_scan(SPEC_SCAN_YAML.replace("source: [卡点]", "source: []"))
        r2 = self.check()
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertEqual(self.codes(r2), ["EMPTY_FIELD"])
        self.assertIn("空数组", json.loads(r2.stdout)["violations"][0]["msg"])

    # trace: 批 2a §5.4 ③——无 schema 存量文件缺 source → 缺省 [卡点] 兼容不报错，计数同口径
    def test_check_legacy_without_schema_defaults_source_to_kadian(self):
        text = SPEC_SCAN_YAML.replace("schema: 2" + NL, "")
        text = text.replace("    source: [卡点]" + NL, "")
        text = text.replace("    source: [卡点, 穷举, 交叉认证]" + NL, "")
        # 真实存量文件连 summary.by_source 键都没有——schema 分层下缺省兼容不报，
        # 回执 counts.by_source 仍按缺省 [卡点] 口径产出
        text = text.replace(", by_source: {卡点: 2, 穷举: 1, 交叉认证: 1}", "")
        self.write_spec_scan(text)
        r = self.check("--final")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual(data["violations"], [])
        self.assertEqual(data["counts"]["by_source"],
                         {"卡点": 2, "穷举": 0, "交叉认证": 0})

    # trace: 批 2a §5.4 ④——顶层 schema: 2 写入面（SKILL.md 结构段登记）＋在场时 check 放行
    def test_check_schema_v2_stamp_declared_and_accepted(self):
        with io.open(SKILL_MD_PATH, encoding="utf-8") as f:
            skill = f.read()
        self.assertIn("schema: 2", skill, "SKILL.md 结构段缺顶层 schema: 2 版本戳")
        self.assertIn("顶层版本戳", skill, "schema: 2 缺版本戳语义注释")
        self.write_spec_scan(SPEC_SCAN_YAML)
        r = self.check()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.codes(r), [])

    # trace: 批 2a §5.4 ⑤——counts.by_source 按元素各计（多值 source 样例逐元素入账）
    def test_check_by_source_counts_each_element(self):
        self.write_spec_scan(SPEC_SCAN_YAML)
        r = self.check("--final")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual(data["counts"]["findings"], 2)
        # findings 两件：[卡点] + [卡点, 穷举, 交叉认证] → 元素四枚，卡点 2 各计
        self.assertEqual(data["counts"]["by_source"],
                         {"卡点": 2, "穷举": 1, "交叉认证": 1})


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


# 套件级句式母本（`suite-texts.md` 中文定稿，逐字）——2026-09-19 中文化轮
INSTANCE_ZH = ("实例解析（FR-4.5/D-9）由工具脚本执行：运行 "
               "`python \"{project-root}/.claude/skills/diy-tools/scripts/diyc.py\" "
               "resolve [--instance <name>] --json`，把回执里的 `output_dir` "
               "当作本次运行唯一的读写根目录。")
INSTANCE_EN_MARK = "Instance resolution (FR-4.5/D-9)"
RESOLVE_KEYS_ZH = ("解析 `project.communication_language` / "
                   "`project.document_output_language` / `paths.output_dir`")
DEFAULT_CHAIN_ZH = ("缺省链：`paths.output_dir` 一律取 `diyc.py resolve` 回执"
                    "（引擎缺省 `diy-output`，异常形状降级并 warning）；"
                    "缺 `document_output_language` 落 `project.communication_language`；"
                    "两者皆缺则跟随用户当前消息的语言，并在收尾一行说明。")
INSTANCE_FLAG_ZH = ("实例名只在本次激活参数出现 `--instance <name>` 时才传"
                    "（无头侧入口 `runner.py --instance`；交互侧由用户在发起消息里给出同一旗标）；"
                    "未传时回执的 `output_dir` 即主线平铺根。")
READ_DISCIPLINE_ZH = ("读取纪律：预载预算 = 本文件、上述配置与回执、`steps/` 下当前那一个文件"
                      "——绝不批量预载；执行期读取以每个步骤开头的 `Read (input)` 行为唯一权威，"
                      "**主文件不列举封闭清单**。")
PRECISE_ZH = ("- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；"
              "不复述上游已写的信息（引用 ID）；不写没有信息量的套话。")
# 本技能自定短块（母本 §8 登记的变体：§2 非成员，不参与套件级 §2 断言）
DISCIPLINE_OWN_ZH = ("- **写作纪律。** findings 散文用 `document_output_language`；"
                     "`quote` 里机器锚点（ID / 枚举值 / 命令 / 路径）逐字保留原文，不翻译。"
                     "引文里可能出现 `[假设]` 等被禁字面量——照抄，终门对 `quote` 豁免。")
DISCIPLINE_GENERIC_ZH = "- **写作纪律。** 主字段 = 大白话主句；"
H1_RE = re.compile(r"^# Step (\d+) — .*[一-鿿]")


class SkillContractTests(unittest.TestCase):
    """用例 16：SKILL.md / steps 契约冒烟（中文化轮 2026-09-19 + B-24）。"""

    def read(self, path):
        with io.open(path, encoding="utf-8") as f:
            return f.read()

    def read_skill(self):
        return self.read(SKILL_MD_PATH)

    # trace: 母本 §1（实例解析句中文定稿逐字；英文原形随中文化退役）
    def test_instance_sentence_is_mother_copy_verbatim(self):
        raw = self.read_skill()
        self.assertIn(INSTANCE_ZH, raw, "SKILL.md 缺母本 §1 中文定稿（逐字）")
        self.assertNotIn(INSTANCE_EN_MARK, raw, "已转中文定稿，仍残留英文原形")

    # trace: 母本 §3（A-3 键路径写全 project. 前缀 / A-2 缺省链 / A-1 实例触发条款）
    def test_resolve_keys_default_chain_and_instance_flag(self):
        raw = self.read_skill()
        self.assertIn(RESOLVE_KEYS_ZH, raw, "缺母本 §3 键路径锚串（A-3：project. 前缀）")
        self.assertIn(DEFAULT_CHAIN_ZH, raw, "缺母本 §3 缺省链（A-2）")
        self.assertIn(INSTANCE_FLAG_ZH, raw, "缺母本 §3 实例触发条款（A-1）")

    # trace: 母本 §4（A-5 C1 组：预载预算 + 执行期以 Read (input) 行为唯一权威）
    def test_read_discipline_verbatim(self):
        self.assertIn(READ_DISCIPLINE_ZH, self.read_skill(),
                      "SKILL.md 缺母本 §4 定稿（逐字）")

    # trace: 母本 §6（Rules 末尾、§2 之前）+ §8（自定短块，非通用 §2 块）
    def test_precise_and_own_writing_discipline(self):
        raw = self.read_skill()
        self.assertIn(PRECISE_ZH, raw, "缺母本 §6 中文定稿")
        self.assertIn(DISCIPLINE_OWN_ZH, raw, "缺本技能自定写作纪律短块（母本 §8）")
        self.assertNotIn(DISCIPLINE_GENERIC_ZH, raw,
                         "spec-scan 是 §2 非成员，不得改用通用 §2 写作纪律块")
        self.assertLess(raw.index(PRECISE_ZH), raw.index(DISCIPLINE_OWN_ZH),
                        "Rules 末尾顺序须为：§6 精准简练 → §2 自定短块")
        self.assertTrue(raw.rstrip(NL).endswith(DISCIPLINE_OWN_ZH),
                        "写作纪律块须置文件收尾行")

    # trace: 中文化政策（四段中文标题 ≤105 行 + 无英文段名 + §5 渲染静默命令全文）
    def test_four_chinese_sections_and_budget(self):
        raw = self.read_skill()
        self.assertLessEqual(len(raw.splitlines()), 105, "薄主文件超出 105 行预算")
        for section in ("## 激活时", "## 工作流", "## 结构", "## 规则"):
            self.assertIn(section, raw, "缺四段结构：%s" % section)
        for legacy in ("## On Activation", "## Workflow", "## Schema", "## Rules"):
            self.assertNotIn(legacy, raw, "英文段名残留：%s" % legacy)
        self.assertIn('diy-viewer/scripts/viewer.py" --project-root "{project-root}"', raw,
                      "缺渲染静默的 viewer 命令全文（母本 §5）")

    # trace: B-24 · SS-026-02（产物 = 卡点清单；执行计划留对话）
    def test_execution_plan_stays_in_conversation(self):
        raw = self.read_skill()
        self.assertIn("落盘的产物是卡点清单", raw, "SS-026-02 未收口到「产物 = 卡点清单」")
        self.assertNotIn("是**执行计划 + 卡点清单**", raw, "SS-026-02 的旧口径残留")

    # trace: B-24 · SS-026-04/05（单写者 + 号段规则：新增递增、删除/合并允许空缺、绝不重编号）
    def test_single_writer_and_id_segment_rules(self):
        step2 = self.read(os.path.join(STEPS_DIR, "02-dry-run.md"))
        self.assertIn("单写者", step2, "SS-026-04 缺单写者条款")
        self.assertIn("不带 `id`", step2, "SS-026-04 缺「回给调度者、不带 id」")
        self.assertIn("不引入分片文件", step2, "SS-026-04 缺「不引入分片文件」")
        self.assertIn("绝不重编号", step2, "SS-026-05 缺号段规则（绝不重编号）")
        self.assertNotIn("连续不跳号", step2, "SS-026-05 旧口径「连续不跳号」残留")
        step4 = self.read(os.path.join(STEPS_DIR, "04-cross-check.md"))
        self.assertIn("空缺号不回收、不重排", step4, "SS-026-05 ② 未在去误报处同口径")

    # trace: B-24 · SS-026-06（quote 豁免措辞补齐：SKILL.md 半句 + steps/05 扫描面收窄）
    def test_quote_exemption_wording(self):
        self.assertIn("终门对 `quote` 豁免", self.read_skill(),
                      "SS-026-06 SKILL.md 侧豁免半句缺失")
        step5 = self.read(os.path.join(STEPS_DIR, "05-report.md"))
        self.assertIn("**`quote` 豁免**", step5, "SS-026-06 steps/05 缺 quote 豁免")
        self.assertIn("非 `quote` 字段", step5, "SS-026-06 steps/05 未点名扫描面")
        self.assertIn("全角", step5, "SS-026-06 缺全角 ［假设］ 出口")
        self.assertNotIn("全文档", step5, "SS-026-06 旧口径「全文档」残留")

    # trace: B-24 · SS-026-07（复核回路：删「可进入建设批次」，修订后同目标可重扫一次）
    def test_recheck_loop_replaces_build_batch(self):
        step5 = self.read(os.path.join(STEPS_DIR, "05-report.md"))
        self.assertIn("重扫一次", step5, "SS-026-07 缺复核回路")
        self.assertIn("SS-002", step5, "SS-026-07 缺机器锚点 SS-002")
        self.assertIn("本技能不改规格", step5, "缺零改写纪律（本技能不改规格）")
        self.assertNotIn("可进入建设批次", step5, "SS-026-07 的「可进入建设批次」未删")

    # trace: v4 批 2b · 硬门放开——可读非空即入扫（:30 新文案 + :33 新退出句 + 边界两态；旧句零在场）
    def test_hard_gate_opened_to_readable_nonempty(self):
        raw = self.read_skill()
        self.assertIn("硬门：目标存在、可读、非空即入扫", raw, ":30 硬门新文案缺失")
        self.assertNotIn("要照做的事", raw, "旧硬门句「要照做的事」须零在场")
        lines = raw.splitlines()
        self.assertTrue(
            any("不可读 / 空" in ln and "零产出" in ln for ln in lines),
            ":33 缺「不可读 / 空 → 零产出」新退出句")
        self.assertTrue(
            any("纯参考资料" in ln and "不再退出" in ln for ln in lines),
            "缺「纯参考不再退出」反转句")
        boundary = next((ln for ln in lines if "边界两态" in ln), "")
        self.assertIn("解码失败", boundary, "边界两态缺非 UTF-8 解码失败警示问句")
        self.assertIn("入扫零单元 / 退出", boundary, "边界两态缺解码失败问句的两个选项")
        self.assertIn("无 `.md`", boundary, "边界两态缺「目录无 .md」")
        self.assertIn("零产出", boundary, "「目录无 .md」须归「空 → 零产出」")

    # trace: v4 批 2b · 裁①甲——kind 扩枚举「任务书|技能|规格|文档」两处均断（SKILL schema 行 + 01 四选一）
    #   Q-108 改：01 开放裁量「由你判定」作废，改断三阶判据链锚（模糊档先问一次/不代判）
    def test_kind_enum_includes_document_in_both_places(self):
        self.assertIn("任务书|技能|规格|文档", self.read_skill(),
                      "SKILL 结构段 kind 枚举缺「文档」")
        collect = self.read(os.path.join(STEPS_DIR, "01-collect.md"))
        self.assertIn("四选一", collect, "01-collect 缺 kind 四选一")
        self.assertIn("三阶判据链", collect, "01-collect 缺三阶判据链")
        self.assertIn("模糊档", collect, "01 缺模糊档（第三阶）")
        self.assertIn("先问一次", collect, "01 模糊档缺「先问一次」")
        self.assertIn("不代判", collect, "01 模糊档缺「AI 不代判」")
        self.assertNotIn("由你判定（引擎不给）", collect,
                         "01 旧开放裁量句「由你判定（引擎不给）」须零在场")

    # trace: Q-108 · 三阶链②体系产物对照表（封闭世界四类·规格从紧四行）＋文档轻扫口径（第二补块）
    def test_kind_lookup_table_and_doc_light_scan(self):
        collect = self.read(os.path.join(STEPS_DIR, "01-collect.md"))
        self.assertIn("体系产物→类型对照表", collect, "01 缺对照表标题")
        for token in ("prd", "brief", "prfaq", "epics", "stories", "architecture",
                      "openapi", "design", "test-plan", "spec", "story-context",
                      "change-proposal", "project-context",
                      "trigger", "scenarios", "system",
                      "SKILL.md", "steps", "taskbook",
                      "sprint", "review", "mutation-report", "selfcheck",
                      "spec-scan", "investigation", "research", "retrospective",
                      "checkpoint", "editorial-review", "readiness", "evolution"):
            self.assertIn(token, collect, "对照表缺产物真名：%s" % token)
        self.assertIn("从紧归规格", collect, "对照表缺四行从紧注记")
        self.assertIn("结构判兜底", collect, "01 缺体系外结构判兜底")
        self.assertIn("轻扫口径", collect, "01 文档路由缺轻扫口径")
        self.assertIn("规范性语句", collect, "轻扫口径缺①规范性语句")
        self.assertIn("指涉可解析性", collect, "轻扫口径缺②指涉可解析性")
        self.assertIn("谁以什么方式消费它", collect, "轻扫口径缺风险轴判据表述")
        self.assertIn("互补", collect, "轻扫口径缺与 editorial-review 深审互补区分")

    # trace: Q-108 · selfcheck 01 同批同文——三阶链＋对照表全文自包含（落文断言面登记在 spec-scan 侧）
    def test_selfcheck_freeze_same_kind_rule_table(self):
        freeze = self.read(os.path.join(
            HERE, "..", "skills", "diy-selfcheck", "steps", "01-freeze.md"))
        self.assertIn("三阶判据链", freeze, "selfcheck 01 缺三阶判据链")
        self.assertIn("体系产物→类型对照表", freeze, "selfcheck 01 缺对照表标题")
        self.assertIn("模糊档", freeze, "selfcheck 01 缺模糊档")
        self.assertIn("先问一次", freeze, "selfcheck 01 缺「先问一次」")
        self.assertIn("从紧归规格", freeze, "selfcheck 01 对照表缺从紧注记")
        self.assertIn("taskbook", freeze, "selfcheck 01 对照表缺任务书行")
        self.assertIn("WDS 四产物", freeze, "selfcheck 01 对照表缺 WDS 行")

    # trace: v4 批 2b · 裁①甲——01 分岔（文档→03／其余→02）+ 纠错通道 revisions 留痕 + 建文件 schema: 2 配方
    def test_collect_route_fork_and_schema_stamp(self):
        collect = self.read(os.path.join(STEPS_DIR, "01-collect.md"))
        self.assertIn("判为 `文档` → 读全并照做 `./03-exhaustive.md`", collect,
                      "01 缺纯文档分岔（kind=文档 → 03）")
        self.assertIn("读全并照做 `./02-dry-run.md`", collect,
                      "01 缺其余照旧 → 02 分岔")
        self.assertIn("HALT 重走本步", collect, "01 缺纠错通道（改判 → HALT 重走本步）")
        self.assertIn("`revisions` 留痕", collect, "纠错通道缺 revisions 留痕")
        self.assertIn("schema: 2", collect, "01 建文件配方缺顶层 schema: 2 版本戳")

    # trace: v4 批 2b · dispatch 写面（source 三值/schema: 2 ＋ 纯文档路由句 ＋ 执行计划互斥豁免）
    #   断言面登记在 spec-scan 侧；02-dispatch.md 落文由 selfcheck 施工线承担，同批同步重跑。
    def test_selfcheck_dispatch_source_schema_and_route(self):
        dispatch = self.read(os.path.join(
            HERE, "..", "skills", "diy-selfcheck", "steps", "02-dispatch.md"))
        self.assertIn("纯文档路由", dispatch, "dispatch 缺纯文档路由句")
        self.assertTrue(
            any("source" in ln and "卡点|穷举|交叉认证" in ln
                for ln in dispatch.splitlines()),
            "dispatch 缺 source 三值写面句（同句含 source）")
        self.assertIn("schema: 2", dispatch, "dispatch 缺 schema: 2 写面句")
        blocks = re.split(r"\n\s*\n", dispatch)
        self.assertTrue(
            any("纯文档" in b and "执行计划" in b for b in blocks),
            "dispatch 缺纯文档路由与「每个单元先写执行计划」强制句的互斥豁免（须同段共现）")

    # trace: v4 批 2b · 04 复扫优先项括注（纯文档路由下预演缺席——本优先项跳过）
    def test_cross_check_marks_pure_document_route(self):
        step4 = self.read(os.path.join(STEPS_DIR, "04-cross-check.md"))
        self.assertIn("纯文档", step4, "04 优先项缺纯文档路由跳过括注")

    # trace: steps 形态（H1 中文步名 + 步号与文件序一致 + Read/Write 行逐字英文 + 末段）
    def test_steps_shape(self):
        names = ["01-collect.md", "02-dry-run.md", "03-exhaustive.md",
                 "04-cross-check.md", "05-report.md"]
        for i, name in enumerate(names, start=1):
            text = self.read(os.path.join(STEPS_DIR, name))
            lines = text.replace("\r\n", NL).split(NL)
            match = H1_RE.match(lines[0])
            self.assertTrue(match, "%s 的 H1 须为 '# Step N — <中文步名>'，实为 %r"
                            % (name, lines[0]))
            self.assertEqual(int(match.group(1)), i, "%s 步号与文件序不符" % name)
            self.assertTrue(any(ln.startswith("**Read (input):**") for ln in lines),
                            "%s 缺 '**Read (input):**' 行" % name)
            self.assertTrue(any(ln.startswith("**Write (output):**") for ln in lines),
                            "%s 缺 '**Write (output):**' 行" % name)
            heads = [ln for ln in lines if ln.startswith("## ")]
            self.assertEqual(heads[-1], "## 播报与下一步",
                             "%s 末段须为 '## 播报与下一步'" % name)
            self.assertNotIn("**读入：**", text, "%s 旧形态「读入」残留" % name)
            self.assertNotIn("**写出：**", text, "%s 旧形态「写出」残留" % name)


if __name__ == "__main__":
    unittest.main()
