# -*- coding: utf-8 -*-
"""diy-editorial-review 确定性引擎 e2e 测试（B4 批，任务书 §7 九用例逐条对应）。

覆盖（用例号 = 任务书 §7 测试节的九条，顺序一致）：
- 用例 1：target 缺席 → exit 1 + MISSING_FILE + 零产出
- 用例 2：target < 3 词 → exit 1 + EMPTY_FIELD（源 HALT 门槛）
- 用例 3：`--lens` 非法值 → exit 1 + ENUM_INVALID（`--reader-type` 同规；单透镜合法）
- 用例 4：`stats` 在合成分节 md 上给出节清单与词数（+ yaml 按顶层键切节 + 回执共同键）
- 用例 5：`check` 检出 lenses 与两槽不一致 → SET_MISMATCH（双向）
- 用例 6：`check` 检出 findings `no` 跳号 → SET_MISMATCH（重号 → DUPLICATE_ID）
- 用例 7：`check` 检出 reader_type 非法 → ENUM_INVALID（枚举中文化 人类|LLM）
- 用例 8：`--final` 对未定稿记录拒绝 → STATUS_MISMATCH（同稿非 --final 放行）
- 用例 9：契约冒烟（合法记录 check --final exit 0 + 回执键完整；SKILL.md 母本 §1 中文定稿
          逐字 + 四段中文标题 ≤90 行 + 终门句指向 editorial_review.py + `--previous` 判 no）
夹具全部落 tempdir 自建；不读写本仓库真实 diy-output。
运行：cd diy-coder && python -m unittest discover -s tests -p "test_editorial_review.py" -v
"""
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.join(HERE, "..", "skills", "diy-editorial-review")
ENGINE = os.path.join(SKILL_DIR, "scripts", "editorial_review.py")
SKILL_MD_PATH = os.path.join(SKILL_DIR, "SKILL.md")
NL = chr(10)

# 套件级句式母本（suite-texts.md §1 中文定稿，逐字）——2026-09-19 中文化轮
INSTANCE_ZH = ("实例解析（FR-4.5/D-9）由工具脚本执行：运行 "
               "`python \"{project-root}/.claude/skills/diy-tools/scripts/diyc.py\" "
               "resolve [--instance <name>] --json`，把回执里的 `output_dir` "
               "当作本次运行唯一的读写根目录。")
INSTANCE_EN_MARK = "Instance resolution (FR-4.5/D-9)"

# 3 节 md：甲 2 词（ab cd）、乙 4 词（中文四字）、丙 3 词（one two three）
DOC_MD = NL.join([
    "# 文档标题",
    "## 甲",
    "ab cd",
    "## 乙",
    "中文四字",
    "## 丙",
    "one two three",
]) + NL

SHORT_MD = NL.join(["## 标题", "ab"]) + NL
HEADING_ONLY_MD = NL.join(["# 只有标题"]) + NL

DOC_YAML = NL.join([
    "project:",
    "  name: mini",
    "brief:",
    "  problem: ab cd",
    "decisions: []",
]) + NL

REVIEW_YAML = NL.join([
    "project:",
    "  name: mini",
    "  created: '2026-09-13'",
    "  updated: '2026-09-20'",
    "reviews:",
    "- id: ER-001",
    "  target: docs/doc.yaml",
    "  date: '2026-09-20'",
    "  status: 已定稿",
    "  lenses: [结构, 文风]",
    "  reader_type: 人类",
    "  structure:",
    "    model: 教程线性",
    "    purpose: 帮新用户跑通一遍",
    "    audience: 新用户",
    "    findings:",
    "    - {no: 1, category: CUT, target: 附录, rationale: 没人看, impact_words: 30}",
    "    - {no: 2, category: PRESERVE, target: 背景, rationale: 保留理解, impact_words: -5}",
    "    estimated_reduction_words: 25",
    "    meets_length_target: 未设目标",
    "  prose:",
    "    findings:",
    "    - {no: 1, original: 我们把数据进行了处理, revised: 系统处理数据, changes: 去冗余动词, locations: ['第 2 节']}",
    "  open_questions: []",
    "revisions: []",
]) + NL


def run_engine(args, cwd=None):
    return subprocess.run([sys.executable, ENGINE] + args,
                          capture_output=True, text=True, encoding="utf-8", cwd=cwd)


class EngineCase(unittest.TestCase):
    """tmp 项目根 + diy-output 目录的公共夹具。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="editorial-")
        self.root = self.tmp.name
        self.out = os.path.join(self.root, "diy-output")
        os.makedirs(self.out, exist_ok=True)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, rel, content):
        path = os.path.join(self.root, rel)
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with io.open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def stats(self, *extra):
        return run_engine(["stats", "--project-root", self.root,
                           "--output-dir", self.out, "--json"] + list(extra))

    def check(self, *extra):
        return run_engine(["check", "--project-root", self.root,
                           "--output-dir", self.out, "--json"] + list(extra))

    def write_review(self, text):
        self.write("diy-output/editorial-review.yaml", text)

    def codes(self, result):
        return [item["code"] for item in json.loads(result.stdout)["violations"]]

    def assert_zero_output(self):
        self.assertEqual(os.listdir(self.out), [], "拒绝路径必须零产出")


class StatsGateTests(EngineCase):
    """用例 1-4：门禁与结构地图。"""

    # trace: B4 diy-editorial-review 用例 1（target 缺席 → MISSING_FILE + 零产出）
    def test_target_missing_refused(self):
        r = self.stats("--target", "docs/no-such.md")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertNotIn("Traceback", r.stderr)
        self.assertEqual(self.codes(r), ["MISSING_FILE"])
        self.assertFalse(json.loads(r.stdout)["ok"])
        self.assert_zero_output()

    # trace: B4 diy-editorial-review 用例 2（< 3 词 → EMPTY_FIELD；空标题文档同拒）
    def test_target_too_short_refused(self):
        self.write("docs/short.md", SHORT_MD)
        r = self.stats("--target", "docs/short.md")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertEqual(self.codes(r), ["EMPTY_FIELD"])
        self.assertIn("3 词", json.loads(r.stdout)["violations"][0]["msg"])
        self.write("docs/heading-only.md", HEADING_ONLY_MD)
        r2 = self.stats("--target", "docs/heading-only.md")
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertEqual(self.codes(r2), ["EMPTY_FIELD"])
        self.assert_zero_output()

    # trace: B4 diy-editorial-review 用例 3（--lens / --reader-type 越界 → ENUM_INVALID；单透镜合法）
    def test_invalid_lens_refused(self):
        self.write("docs/doc.md", DOC_MD)
        r = self.stats("--target", "docs/doc.md", "--lens", "拼写")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertEqual(self.codes(r), ["ENUM_INVALID"])
        self.assertIn("拼写", json.loads(r.stdout)["violations"][0]["msg"])
        r2 = self.stats("--target", "docs/doc.md", "--reader-type", "humans")
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertEqual(self.codes(r2), ["ENUM_INVALID"])
        self.assertIn("人类|LLM", json.loads(r2.stdout)["violations"][0]["msg"])
        self.assert_zero_output()
        r3 = self.stats("--target", "docs/doc.md", "--lens", "结构")
        self.assertEqual(r3.returncode, 0, r3.stdout + r3.stderr)
        data = json.loads(r3.stdout)
        self.assertEqual(data["lenses"], ["结构"], "单透镜自由：只跑一个透镜合法")
        self.assertEqual(data["reader_type"], "人类", "reader_type 缺省 人类")

    # trace: B4 diy-editorial-review 用例 4（分节清单与词数；yaml 按顶层键切节；回执共同键）
    def test_stats_section_map_on_md(self):
        self.write("docs/doc.md", DOC_MD)
        r = self.stats("--target", os.path.join(self.root, "docs", "doc.md"))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        common = {"ok", "command", "project_root", "output_dir", "violations",
                  "warnings", "counts"}
        self.assertTrue(common <= set(data), "stats 回执缺共同键")
        self.assertEqual(data["command"], "stats")
        self.assertEqual(data["counts"], {"sections": 3, "words": 9, "lines": 7})
        self.assertEqual([s["name"] for s in data["target"]["sections"]],
                         ["甲", "乙", "丙"])
        self.assertEqual([s["words"] for s in data["target"]["sections"]], [2, 4, 3])
        self.assertEqual(data["target"]["total_words"], 9)
        self.assertEqual(data["target"]["kind"], "md")
        self.assertEqual(data["target"]["path"], "docs/doc.md")
        self.assertNotIn("\\", data["target"]["path"])

        self.write("docs/doc.yaml", DOC_YAML)
        r2 = self.stats("--target", "docs/doc.yaml")
        self.assertEqual(r2.returncode, 0, r2.stdout + r2.stderr)
        data2 = json.loads(r2.stdout)
        self.assertEqual(data2["target"]["kind"], "yaml")
        self.assertEqual([s["name"] for s in data2["target"]["sections"]],
                         ["project", "brief", "decisions"])
        self.assertEqual(data2["target"]["sections"][1]["words"], 2)


class CheckTests(EngineCase):
    """用例 5-8：台账校验。"""

    # trace: B4 diy-editorial-review 用例 5（lenses ↔ 两槽 双向对账 → SET_MISMATCH）
    def test_lens_slot_mismatch(self):
        self.write("docs/doc.yaml", DOC_YAML)
        drop_prose = REVIEW_YAML.replace(
            "  prose:" + NL + "    findings:" + NL
            + "    - {no: 1, original: 我们把数据进行了处理, revised: 系统处理数据,"
              " changes: 去冗余动词, locations: ['第 2 节']}" + NL, "")
        self.write_review(drop_prose)
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertEqual(self.codes(r), ["SET_MISMATCH"])
        self.assertIn("prose", json.loads(r.stdout)["violations"][0]["msg"])

        self.write_review(REVIEW_YAML.replace("lenses: [结构, 文风]", "lenses: [结构]"))
        r2 = self.check()
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertEqual(self.codes(r2), ["SET_MISMATCH"],
                         "槽在场而 lenses 未声明同判：%s" % r2.stdout)
        self.assertIn("文风", json.loads(r2.stdout)["violations"][0]["msg"])

    # trace: B4 diy-editorial-review 用例 6（findings no 跳号 → SET_MISMATCH；重号 → DUPLICATE_ID）
    def test_finding_no_gap(self):
        self.write("docs/doc.yaml", DOC_YAML)
        self.write_review(REVIEW_YAML.replace(
            "- {no: 2, category: PRESERVE", "- {no: 3, category: PRESERVE"))
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertEqual(self.codes(r), ["SET_MISMATCH"])
        self.assertIn("不连续", json.loads(r.stdout)["violations"][0]["msg"])

        self.write_review(REVIEW_YAML.replace(
            "- {no: 2, category: PRESERVE", "- {no: 1, category: PRESERVE"))
        r2 = self.check()
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertIn("DUPLICATE_ID", self.codes(r2), r2.stdout)

    # trace: B4 diy-editorial-review 用例 7（reader_type 枚举中文化：人类|LLM）
    def test_reader_type_invalid(self):
        self.write("docs/doc.yaml", DOC_YAML)
        self.write_review(REVIEW_YAML.replace("reader_type: 人类", "reader_type: humans"))
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertEqual(self.codes(r), ["ENUM_INVALID"])
        self.assertIn("人类|LLM", json.loads(r.stdout)["violations"][0]["msg"])

        self.write_review(REVIEW_YAML.replace("reader_type: 人类", "reader_type: LLM"))
        r2 = self.check()
        self.assertEqual(r2.returncode, 0, r2.stdout + r2.stderr)

    # trace: B4 diy-editorial-review 用例 8（--final 对未定稿记录拒绝；同稿非 --final 放行）
    def test_final_requires_final_status(self):
        self.write("docs/doc.yaml", DOC_YAML)
        self.write_review(REVIEW_YAML.replace("status: 已定稿", "status: 草稿"))
        r = self.check()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r2 = self.check("--final")
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertEqual(self.codes(r2), ["STATUS_MISMATCH"])
        self.assertIn("已定稿", json.loads(r2.stdout)["violations"][0]["msg"])


class ContractSmokeTests(EngineCase):
    """用例 9：引擎回执契约 + SKILL.md 契约冒烟。"""

    # trace: B4 diy-editorial-review 用例 9（合规记录 exit 0 + 回执键 + SKILL.md 母本/四段/终门句）
    def test_contract_smoke(self):
        self.write("docs/doc.yaml", DOC_YAML)
        self.write_review(REVIEW_YAML)
        r = self.check("--final")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(len(r.stdout.strip().splitlines()), 1, "--json 回执须单行")
        data = json.loads(r.stdout)
        common = {"ok", "command", "project_root", "output_dir", "violations",
                  "warnings", "counts"}
        self.assertTrue(common <= set(data), "check 回执缺共同键")
        self.assertEqual(data["output_dir"], self.out.replace("\\", "/"))
        self.assertEqual(data["counts"]["reviews"], 1)
        self.assertEqual(data["counts"]["structure_findings"], 2)
        self.assertEqual(data["counts"]["prose_findings"], 1)

        # target 基准（§7 钉死；与 brief.py check --final 的归一化口径同源）：正斜杠 +
        # project-root 相对 + 无 `path:` 前缀——写成反斜杠形式即拒
        self.write_review(REVIEW_YAML.replace("target: docs/doc.yaml",
                                              "target: 'docs" + chr(92) + "doc.yaml'"))
        r_basis = self.check()
        self.assertEqual(r_basis.returncode, 1, r_basis.stdout)
        self.assertEqual(self.codes(r_basis), ["ENUM_INVALID"])
        self.assertIn("正斜杠", json.loads(r_basis.stdout)["violations"][0]["msg"])

        # `--previous` 判 no（追加式台账，无 ID 集合收缩面）→ argparse 用法错误
        self.assertEqual(self.check("--previous", "x.yaml").returncode, 2)

        with io.open(SKILL_MD_PATH, encoding="utf-8") as fh:
            raw = fh.read()
        self.assertIn(INSTANCE_ZH, raw, "SKILL.md 缺母本 §1 中文定稿（逐字）")
        self.assertNotIn(INSTANCE_EN_MARK, raw, "已转中文定稿，仍残留英文原形")
        self.assertLessEqual(len(raw.splitlines()), 90, "薄主文件超出 90 行预算")
        for section in ("## 激活时", "## 工作流", "## 结构", "## 规则"):
            self.assertIn(section, raw, "缺四段结构：%s" % section)
        self.assertIn("editorial_review.py", raw, "终门句未指向本技能引擎")
        self.assertIn("check --final", raw, "终门句缺 check --final")
        self.assertIn("--json", raw, "终门句缺 --json 回执")
        self.assertIn('diy-viewer/scripts/viewer.py" --project-root "{project-root}"', raw,
                      "缺渲染静默的 viewer 命令全文（母本 §5）")


if __name__ == "__main__":
    unittest.main()
