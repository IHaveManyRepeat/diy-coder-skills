# -*- coding: utf-8 -*-
"""diy-analyze 契约测试（B7b · W4）。

覆盖八类必备（承 B7a §2.6）+ 本技能特有边界：
  门禁（代码库可读）/ init（唯一写盘）/ ID 铸号（AN-<nn> 顺序与唯一）
  / list / show / check / 跨技能门禁（入口技能：无上游 diy 产物）
  / 回执键完整性 / 契约冒烟（CLI 真跑）
  共享骨架一致性（裁定 1：与 diy-reverse 逐字共用的写作块）

口径来源：taskbook-b7b §2.2（引擎契约）· batch3-contract §3/§4 · 裁定 14/15/20。
"""
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SKILLS = os.path.join(ROOT, "skills")
ANALYZE_DIR = os.path.join(SKILLS, "diy-analyze")
REVERSE_DIR = os.path.join(SKILLS, "diy-reverse")
SCRIPT = os.path.join(ANALYZE_DIR, "scripts", "analyze.py")

COMMON_KEYS = {"ok", "command", "project_root", "output_dir", "instance",
               "violations", "warnings", "counts"}
STEPS = ("01-define.md", "02-scan.md", "03-map.md", "04-document.md")

# 裁定 1 的「分析/提取骨架」写作块——八份步骤文件逐字共用（与 diy-reverse 同款）。
SKELETON_LITERALS = (
    "**Read (input):**",
    "**Write (output):**",
    "**本段纪律**：",
    "**先说清为什么**：",
    "**检查点（六拍）**：① 生成 → ② 落盘 → ③ 分隔 → ④ 呈出 → ⑤ 出四选项 → ⑥ 等响应。",
    "`[a]` 高级引导 → 调 `diy-elicit`（零写面）｜ `[c]` 继续 → 进下一步 ｜ "
    "`[p]` 多方模式 → 调 `diy-party-mode`（零写面）｜ `[y]` YOLO → 跳过后续检查点连续推进（首次选中时一行明示）。",
    "**收尾与路由**：",
    "**不跳读**：本步只读它点名的那一份产物，绝不批量预载 `steps/`；前一步的产物没落盘，本步不许开工。",
    "**不编造**：读不出来的值留空并记 gap；绝不用印象补。",
    "**不代决**：检查点呈出后 HALT 等响应，绝不替用户拍板。",
)

GOOD_COMPONENTS = [
    {"id": "AN-01", "name": "AuthModule", "layer": "应用层",
     "responsibility": "登录、注册与会话管理", "location": "src/auth/"},
    {"id": "AN-02", "name": "UserService", "layer": "领域层",
     "responsibility": "用户资料 CRUD", "location": "src/users/"},
]


def run_cli(*args):
    """跑真 CLI（契约冒烟），回 (rc, 回执 or None, stdout, stderr)。"""
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    proc = subprocess.run([sys.executable, SCRIPT, *args], capture_output=True,
                          text=True, encoding="utf-8", env=env)
    doc = None
    if "--json" in args and proc.stdout.strip().startswith("{"):
        doc = json.loads(proc.stdout)
    return proc.returncode, doc, proc.stdout, proc.stderr


def write_analysis(tmp, doc):
    out = os.path.join(tmp, "diy-output")
    os.makedirs(out, exist_ok=True)
    path = os.path.join(out, "analysis.yaml")
    with io.open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(doc, f, allow_unicode=True, sort_keys=False)
    return path


def base_doc(**over):
    doc = {
        "project": {"name": "demo", "created": "2026-09-21",
                    "updated": "2026-09-21", "status": "草稿"},
        "question": {"text": "这个应用的鉴权是怎么组织的？", "scope": "跨切面：认证",
                     "output_format": "架构图 + 组件地图", "time_box": "30 分钟",
                     "codebase": "."},
        "architecture": {"summary": "单块 Node 应用，四层结构。",
                         "tech_stack": ["TypeScript 5.x", "Next.js 14"],
                         "overview": "页面层经应用层调用领域层，基础设施层垫底。",
                         "mermaid": "graph TD\n    Client --> API\n    API --> DB",
                         "patterns": ["分层"], "layers": ["展示层", "应用层"]},
        "components": [dict(c) for c in GOOD_COMPONENTS],
        "data_flow": [{"name": "登录", "steps": ["表单提交", "API 校验", "写会话"],
                       "components": ["AN-01", "AN-02"]}],
        "dependencies": [{"from": "AN-02", "to": "AN-01", "note": "取会话"}],
        "risks": [{"risk": "管理端路由无输入校验", "severity": "高",
                   "location": "src/routes/admin.ts", "impact": "安全漏洞"}],
        "recommendations": [{"action": "给管理端补 Zod 校验", "priority": "高",
                             "effort": "2–3 小时", "target": "src/routes/admin.ts"}],
        "revisions": [],
    }
    doc.update(over)
    return doc


class AnalyzerCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="diy-analyze-")
        self.out = os.path.join(self.tmp, "diy-output")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def init_ok(self, **over):
        args = ["init", "--question", "这个应用的鉴权是怎么组织的？",
                "--scope", "跨切面：认证", "--output-format", "架构图 + 组件地图",
                "--time-box", "30 分钟", "--project-root", self.tmp,
                "--output-dir", self.out, "--json"]
        rc, doc, _, err = run_cli(*args)
        self.assertEqual(rc, 0, err)
        return doc


# ---- 1 门禁：代码库可读（入口技能；缺失即零产出） ----------------------------

class GateTests(AnalyzerCase):
    def test_missing_codebase_zero_write(self):
        missing = os.path.join(self.tmp, "nope")
        rc, doc, _, _ = run_cli("init", "--question", "Q", "--codebase", missing,
                                "--project-root", self.tmp, "--output-dir",
                                self.out, "--json")
        self.assertEqual(rc, 1)
        self.assertFalse(doc["ok"])
        self.assertEqual(doc["violations"][0]["code"], "MISSING_FILE")
        self.assertFalse(os.path.exists(os.path.join(self.out, "analysis.yaml")))

    def test_empty_question_refused(self):
        rc, doc, _, _ = run_cli("init", "--question", "   ",
                                "--project-root", self.tmp, "--output-dir",
                                self.out, "--json")
        self.assertEqual(rc, 1)
        self.assertEqual(doc["violations"][0]["code"], "EMPTY_FIELD")
        self.assertFalse(os.path.exists(os.path.join(self.out, "analysis.yaml")))

    def test_output_dir_is_required_for_init(self):
        rc, _, _, err = run_cli("init", "--question", "Q",
                                "--project-root", self.tmp, "--json")
        self.assertEqual(rc, 2, err)  # argparse 用法错误

    def test_reader_on_absent_product_is_violation_not_crash(self):
        rc, doc, _, _ = run_cli("check", "--project-root", self.tmp,
                                "--output-dir", self.out, "--json")
        self.assertEqual(rc, 1)
        self.assertEqual(doc["violations"][0]["code"], "MISSING_FILE")


# ---- 2 init：唯一写盘 + 骨架形态 -------------------------------------------

class InitTests(AnalyzerCase):
    def test_init_writes_skeleton_and_receipt(self):
        doc = self.init_ok()
        self.assertTrue(doc["ok"])
        self.assertIsNone(doc["instance"])
        self.assertIn("updated", doc)
        self.assertTrue(os.path.exists(os.path.join(self.out, "analysis.yaml")))
        got = yaml.safe_load(io.open(os.path.join(self.out, "analysis.yaml"),
                                     encoding="utf-8"))
        self.assertEqual(got["project"]["status"], "草稿")
        self.assertEqual(got["question"]["text"], "这个应用的鉴权是怎么组织的？")
        self.assertEqual(got["components"], [])
        self.assertEqual(got["revisions"], [])

    def test_init_does_not_overwrite_existing(self):
        self.init_ok()
        rc, doc, _, _ = run_cli("init", "--question", "改了问题",
                                "--project-root", self.tmp, "--output-dir",
                                self.out, "--json")
        self.assertEqual(rc, 0)
        self.assertEqual(doc["violations"], [])
        self.assertTrue(doc["warnings"])
        got = yaml.safe_load(io.open(os.path.join(self.out, "analysis.yaml"),
                                     encoding="utf-8"))
        self.assertEqual(got["question"]["text"], "这个应用的鉴权是怎么组织的？")

    def test_init_refuses_corrupt_product(self):
        os.makedirs(self.out, exist_ok=True)
        with io.open(os.path.join(self.out, "analysis.yaml"), "w",
                     encoding="utf-8") as f:
            f.write("project: [unclosed\n")
        rc, doc, _, _ = run_cli("init", "--question", "Q",
                                "--project-root", self.tmp, "--output-dir",
                                self.out, "--json")
        self.assertEqual(rc, 1)
        self.assertEqual(doc["violations"][0]["code"], "UNPARSABLE_YAML")


# ---- 3 ID 铸号：AN-<nn> 唯一 / 顺序 / 形态 ---------------------------------

class IdTests(AnalyzerCase):
    def check_doc(self, **over):
        write_analysis(self.tmp, base_doc(**over))
        return run_cli("check", "--project-root", self.tmp, "--output-dir",
                       self.out, "--json")

    def test_duplicate_id(self):
        rc, doc, _, _ = self.check_doc(components=[GOOD_COMPONENTS[0],
                                                  dict(GOOD_COMPONENTS[0])])
        self.assertEqual(rc, 1)
        self.assertIn("DUPLICATE_ID", [v["code"] for v in doc["violations"]])

    def test_sequence_gap(self):
        rc, doc, _, _ = self.check_doc(
            components=[GOOD_COMPONENTS[0], dict(GOOD_COMPONENTS[1], id="AN-04")])
        self.assertEqual(rc, 1)
        self.assertIn("SET_MISMATCH", [v["code"] for v in doc["violations"]])

    def test_bad_id_shape(self):
        rc, doc, _, _ = self.check_doc(
            components=[dict(GOOD_COMPONENTS[0], id="AN-1"), GOOD_COMPONENTS[1]])
        self.assertEqual(rc, 1)
        self.assertIn("ENUM_INVALID", [v["code"] for v in doc["violations"]])


# ---- 4 list / show ---------------------------------------------------------

class ReadCommandTests(AnalyzerCase):
    def setUp(self):
        super().setUp()
        write_analysis(self.tmp, base_doc())

    def test_list_returns_six_fields_only(self):
        rc, doc, _, _ = run_cli("list", "--project-root", self.tmp,
                                "--output-dir", self.out, "--json")
        self.assertEqual(rc, 0)
        item = doc["items"][0]
        self.assertEqual(set(item), {"id", "name", "layer", "responsibility",
                                     "location", "status"})
        self.assertEqual(doc["counts"]["components"], 2)

    def test_show_by_id_and_unknown(self):
        rc, doc, _, _ = run_cli("show", "--id", "AN-02", "--project-root",
                                self.tmp, "--output-dir", self.out, "--json")
        self.assertEqual(rc, 0)
        self.assertEqual(doc["component"]["name"], "UserService")
        rc, doc, _, _ = run_cli("show", "--id", "AN-99", "--project-root",
                                self.tmp, "--output-dir", self.out, "--json")
        self.assertEqual(rc, 1)
        self.assertEqual(doc["violations"][0]["code"], "UNKNOWN_ID")


# ---- 5 check：常态与 --final ----------------------------------------------

class CheckTests(AnalyzerCase):
    def test_clean_draft_passes_common_gate(self):
        write_analysis(self.tmp, base_doc())
        rc, doc, _, _ = run_cli("check", "--project-root", self.tmp,
                                "--output-dir", self.out, "--json")
        self.assertEqual(rc, 0, doc)
        self.assertEqual(doc["violations"], [])
        self.assertEqual(doc["counts"]["components"], 2)

    def test_final_needs_status_and_clean_assumptions(self):
        write_analysis(self.tmp, base_doc())
        rc, doc, _, _ = run_cli("check", "--final", "--project-root", self.tmp,
                                "--output-dir", self.out, "--json")
        self.assertEqual(rc, 1)
        self.assertIn("STATUS_MISMATCH", [v["code"] for v in doc["violations"]])

        doc_in = base_doc()
        doc_in["project"]["status"] = "已定稿"
        doc_in["architecture"]["summary"] = "[假设] 大概是单块"
        write_analysis(self.tmp, doc_in)
        rc, doc, _, _ = run_cli("check", "--final", "--project-root", self.tmp,
                                "--output-dir", self.out, "--json")
        self.assertEqual(rc, 1)
        self.assertIn("ASSUMPTION_PRESENT", [v["code"] for v in doc["violations"]])

        doc_ok = base_doc()
        doc_ok["project"]["status"] = "已定稿"
        write_analysis(self.tmp, doc_ok)
        rc, doc, _, _ = run_cli("check", "--final", "--project-root", self.tmp,
                                "--output-dir", self.out, "--json")
        self.assertEqual(rc, 0, doc)

    def test_layer_and_severity_enums(self):
        write_analysis(self.tmp, base_doc(
            components=[dict(GOOD_COMPONENTS[0], layer="随便写的层")],
            risks=[{"risk": "x", "severity": "致命", "location": "a", "impact": "b"}]))
        rc, doc, _, _ = run_cli("check", "--project-root", self.tmp,
                                "--output-dir", self.out, "--json")
        self.assertEqual(rc, 1)
        self.assertGreaterEqual(len([v for v in doc["violations"]
                                     if v["code"] == "ENUM_INVALID"]), 2)


# ---- 6 回执键完整性 --------------------------------------------------------

class ReceiptTests(AnalyzerCase):
    def test_all_receipts_carry_common_keys(self):
        self.init_ok()
        for args in (["list"], ["show"], ["check"]):
            rc, doc, _, _ = run_cli(*args, "--project-root", self.tmp,
                                    "--output-dir", self.out, "--json")
            self.assertLessEqual(rc, 1)
            self.assertTrue(COMMON_KEYS.issubset(set(doc)),
                            "%s 缺共同键" % args)
            self.assertIn("instance", doc)
            self.assertIsNone(doc["instance"])
            self.assertIsInstance(doc["violations"], list)
            self.assertIsInstance(doc["warnings"], list)

    def test_human_mode_is_chinese_not_json(self):
        rc, _, out, _ = run_cli("list", "--project-root", self.tmp,
                                "--output-dir", self.out)
        self.assertLessEqual(rc, 1)
        self.assertFalse(out.strip().startswith("{"))


# ---- 7 契约冒烟 + 母本逐字 + frontmatter -----------------------------------

class SkillShapeTests(unittest.TestCase):
    def skill_text(self):
        return io.open(os.path.join(ANALYZE_DIR, "SKILL.md"),
                       encoding="utf-8").read()

    def test_main_file_is_thin_four_section(self):
        lines = self.skill_text().splitlines()
        self.assertLessEqual(len(lines), 90, "SKILL.md 超 90 行硬阈值")
        for head in ("## 激活时", "## 工作流", "## 结构", "## 规则"):
            self.assertIn(head, lines)

    def test_frontmatter_five_fields(self):
        head = self.skill_text().split("---")[1]
        fm = yaml.safe_load(head)
        self.assertEqual(fm["phase"], "anytime")
        self.assertEqual(fm["precededBy"], [])
        self.assertEqual(fm["followedBy"], [])
        self.assertIs(fm["required"], False)
        self.assertEqual(fm["line"], "any")
        self.assertEqual(fm["outputs"], "analysis.yaml")

    def test_mother_text_blocks_verbatim(self):
        text = self.skill_text()
        for anchor in (
            '实例解析（FR-4.5/D-9）由工具脚本执行：运行 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json`，把回执里的 `output_dir` 当作本次运行唯一的读写根目录。',
            "缺省链：`paths.output_dir` 一律取 `diyc.py resolve` 回执（引擎缺省 `diy-output`，异常形状降级并 warning）；缺 `document_output_language` 落 `project.communication_language`；两者皆缺则跟随用户当前消息的语言，并在收尾一行说明。",
            "读取纪律：预载预算 = 本文件、上述配置与回执、`steps/` 下当前那一个文件——绝不批量预载；执行期读取以每个步骤开头的 `Read (input)` 行为唯一权威，**主文件不列举封闭清单**。",
            "渲染是静默旁路——只写调用命令，不新增「打开浏览器 / 报告路径等待查看 / 阻塞等待」交互点：",
            "- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；不复述上游已写的信息（引用 ID）；不写没有信息量的套话。",
            "- **写作纪律。** 主字段 = 大白话主句；数字/枚举内联；机器语法（命令/旗标/路径）进括号；机器锚点逐字保留（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 `diy-design` 的 detect 启发式。",
        ):
            self.assertIn(anchor, text, "母本锚串缺席：%s" % anchor[:24])

    def test_red_line_no_foreign_check_type(self):
        """红线：不得教 `diyc.py check --type <WDS 型>`；`--previous` 只准出现在否定的声明里。"""
        text = self.skill_text()
        self.assertNotIn("check --type", text)
        self.assertNotIn("diyc.py\" check", text)
        for line in text.splitlines():
            if "--previous" in line:
                self.assertIn("无 `--previous`", line, "非声明的 --previous 引用：%s" % line)

    def test_boundary_sentences(self):
        text = self.skill_text()
        self.assertIn("arch-analyze", text)
        self.assertIn("只记既有事实", text)


class StepsShapeTests(unittest.TestCase):
    def steps(self, folder):
        return sorted(f for f in os.listdir(folder) if f.endswith(".md"))

    def test_frozen_file_names(self):
        self.assertEqual(tuple(self.steps(os.path.join(ANALYZE_DIR, "steps"))),
                         STEPS)

    def test_every_step_has_sections_and_five_elements(self):
        for name in STEPS:
            text = io.open(os.path.join(ANALYZE_DIR, "steps", name),
                           encoding="utf-8").read()
            self.assertIn("# Step ", text)
            self.assertIn("Progress: ", text)
            self.assertGreaterEqual(text.count("## 第 "), 1, name)
            self.assertIn("**收尾与路由**：", text)

    def test_shared_skeleton_verbatim_in_all_eight_files(self):
        """裁定 1：分析/提取骨架逐字共用——两技能八份步骤文件全覆盖。"""
        files = ([os.path.join(ANALYZE_DIR, "steps", n) for n in STEPS] +
                 [os.path.join(REVERSE_DIR, "steps", n)
                  for n in ("01-define.md", "02-explore.md", "03-specs.md",
                            "04-extract-tokens.md")])
        for path in files:
            text = io.open(path, encoding="utf-8").read()
            for lit in SKELETON_LITERALS:
                self.assertIn(lit, text, "%s 缺骨架串：%s"
                              % (os.path.basename(path), lit[:20]))


class EngineCliTests(unittest.TestCase):
    def test_unknown_subcommand_is_usage_error(self):
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        proc = subprocess.run([sys.executable, SCRIPT, "frobnicate"],
                              capture_output=True, text=True, encoding="utf-8",
                              env=env)
        self.assertEqual(proc.returncode, 2)


if __name__ == "__main__":
    unittest.main()
