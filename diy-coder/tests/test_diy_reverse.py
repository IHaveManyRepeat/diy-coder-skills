# -*- coding: utf-8 -*-
"""diy-reverse 契约测试（B7b · W4）。

覆盖八类必备（承 B7a §2.6）+ 本技能特有边界：
  门禁（外部目标可访问）/ init（唯一写盘 + **不覆盖既有 design.yaml**）
  / ID 铸号（`P-<n>`：形态 / 顺序 / 原型同源）/ list / show / check
  / 跨技能门禁（design.yaml 是 diy-design 的产物 → 拒绝覆盖并路由）
  / 回执键完整性 / 契约冒烟
  另加：① `one-off-*` 判据（重复值可作 token、单次值禁）
        ② **交叉核对**——本引擎产出的 design.yaml 必须过既有 `design.py validate`
           与 `design.py check`（裁定 13 的三道检查，实测非纸面）

口径来源：taskbook-b7b §2.2/§2.3 + 裁定 11/13/20 + `diy-design/SKILL.md:52-78`
与 `design.py` 的 validate/check 判据（`REQUIRED_STATES` / `CONTRAST_PAIRS`）。
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
REVERSE_DIR = os.path.join(SKILLS, "diy-reverse")
SCRIPT = os.path.join(REVERSE_DIR, "scripts", "reverse.py")
DESIGN_PY = os.path.join(SKILLS, "diy-design", "scripts", "design.py")
STEPS = ("01-define.md", "02-explore.md", "03-specs.md", "04-extract-tokens.md")

COMMON_KEYS = {"ok", "command", "project_root", "output_dir", "instance",
               "violations", "warnings", "counts"}
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

HTML_OK = ("<!doctype html>\n<html lang=\"zh-CN\"><head><meta charset=\"utf-8\">"
           "<title>首页</title></head><body><h1>首页</h1>"
           "<form><label for=\"q\">搜索</label><input id=\"q\"></form>"
           "</body></html>\n")


def run_cli(*args, script=SCRIPT):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    proc = subprocess.run([sys.executable, script, *args], capture_output=True,
                          text=True, encoding="utf-8", env=env)
    doc = None
    if "--json" in args and proc.stdout.strip().startswith("{"):
        doc = json.loads(proc.stdout)
    return proc.returncode, doc, proc.stdout, proc.stderr


def tokens_doc(**over):
    doc = {
        "project": {"name": "example.com", "created": "2026-09-21",
                    "updated": "2026-09-21", "status": "草稿"},
        "direction": "克制的编辑风格\n- 不用大面积投影\n- 不用圆角卡片堆叠",
        "frontend_framework": "html",
        "tokens": {
            "color": {"bg": "#ffffff", "surface": "#f5f5f5", "text": "#111111",
                      "text_muted": "#595959", "accent": "#1a5fb4",
                      "accent_text": "#ffffff"},
            "spacing": {"unit": "8px", "scale": ["8px", "16px", "24px", "32px"]},
            "typography": {"family_base": "Inter", "family_heading": "Inter",
                           "scale": ["16px", "20px", "32px"]},
        },
        "pages": [
            {"id": "P-1", "name": "首页", "route": "/",
             "states": [{"name": "悬停", "signals": ["图标", "动效"]},
                        {"name": "空态", "signals": ["文字"]},
                        {"name": "加载中", "signals": ["图标", "动效"]},
                        {"name": "错误", "signals": ["图标", "文字"]}],
             "prototype": "prototypes/P-1.html"},
            {"id": "P-2", "name": "价格页", "route": "/pricing",
             "states": [{"name": "悬停", "signals": ["图标"]},
                        {"name": "空态", "signals": ["文字"]},
                        {"name": "加载中", "signals": ["动效"]},
                        {"name": "错误", "signals": ["文字"]}],
             "prototype": "prototypes/P-2.html"},
        ],
        "revisions": [],
    }
    doc.update(over)
    return doc


def write_design(tmp, doc, prototypes=("P-1", "P-2")):
    out = os.path.join(tmp, "diy-output")
    os.makedirs(os.path.join(out, "prototypes"), exist_ok=True)
    for pid in prototypes:
        with io.open(os.path.join(out, "prototypes", "%s.html" % pid), "w",
                     encoding="utf-8") as f:
            f.write(HTML_OK)
    path = os.path.join(out, "design.yaml")
    with io.open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(doc, f, allow_unicode=True, sort_keys=False)
    return path


class ReverseCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="diy-reverse-")
        self.out = os.path.join(self.tmp, "diy-output")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)


# ---- 1 门禁：外部目标可访问（裁定 11：只留 URL + 截图两轨） ------------------

class GateTests(ReverseCase):
    def test_bad_track_is_rejected(self):
        rc, doc, _, _ = run_cli("init", "--track", "source-code",
                                "--target", self.tmp, "--project-root",
                                self.tmp, "--output-dir", self.out, "--json")
        self.assertEqual(rc, 1)
        self.assertEqual(doc["violations"][0]["code"], "ENUM_INVALID")
        self.assertFalse(os.path.exists(os.path.join(self.out, "design.yaml")))

    def test_url_track_needs_http_url(self):
        for bad in ("example.com", "ftp://example.com", "/local/path"):
            rc, doc, _, _ = run_cli("init", "--track", "url", "--target", bad,
                                    "--project-root", self.tmp, "--output-dir",
                                    self.out, "--json")
            self.assertEqual(rc, 1, bad)
            self.assertEqual(doc["violations"][0]["code"], "TARGET_UNREACHABLE")
            self.assertFalse(os.path.exists(os.path.join(self.out, "design.yaml")))

    def test_screenshot_track_needs_existing_files(self):
        rc, doc, _, _ = run_cli("init", "--track", "screenshots", "--target",
                                os.path.join(self.tmp, "shot.png"),
                                "--project-root", self.tmp, "--output-dir",
                                self.out, "--json")
        self.assertEqual(rc, 1)
        self.assertEqual(doc["violations"][0]["code"], "TARGET_UNREACHABLE")
        shot = os.path.join(self.tmp, "shot.png")
        with io.open(shot, "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n")
        rc, doc, _, _ = run_cli("init", "--track", "screenshots", "--target", shot,
                                "--project-root", self.tmp, "--output-dir",
                                self.out, "--json")
        self.assertEqual(rc, 0, doc)
        self.assertTrue(os.path.exists(os.path.join(self.out, "design.yaml")))

    def test_output_dir_is_required_for_init(self):
        rc, _, _, _ = run_cli("init", "--track", "url", "--target",
                              "https://example.com", "--project-root", self.tmp,
                              "--json")
        self.assertEqual(rc, 2)


# ---- 2 写权边界：只在初始生成时写，已存在不覆盖（裁定 13） ------------------

class WriteBoundaryTests(ReverseCase):
    def test_init_writes_skeleton_in_existing_schema_form(self):
        rc, doc, _, _ = run_cli("init", "--track", "url", "--target",
                                "https://example.com", "--project-root",
                                self.tmp, "--output-dir", self.out, "--json")
        self.assertEqual(rc, 0, doc)
        got = yaml.safe_load(io.open(os.path.join(self.out, "design.yaml"),
                                     encoding="utf-8"))
        self.assertEqual(got["project"]["status"], "草稿")
        for key in ("direction", "frontend_framework", "tokens", "pages",
                    "revisions"):
            self.assertIn(key, got)
        self.assertEqual(set(got["tokens"]), {"color", "spacing", "typography"})
        self.assertEqual(got["pages"], [])

    def test_init_refuses_overwrite_existing_design_yaml(self):
        path = write_design(self.tmp, tokens_doc())
        before = io.open(path, encoding="utf-8").read()
        rc, doc, _, _ = run_cli("init", "--track", "url", "--target",
                                "https://example.com", "--project-root",
                                self.tmp, "--output-dir", self.out, "--json")
        self.assertEqual(rc, 1, doc)
        self.assertEqual(doc["violations"][0]["code"], "OVERWRITE_REFUSED")
        self.assertIn("diy-design", doc["violations"][0]["msg"])
        self.assertEqual(io.open(path, encoding="utf-8").read(), before)

    def test_init_refuses_when_existing_is_corrupt(self):
        os.makedirs(self.out, exist_ok=True)
        with io.open(os.path.join(self.out, "design.yaml"), "w",
                     encoding="utf-8") as f:
            f.write("pages: [oops\n")
        rc, doc, _, _ = run_cli("init", "--track", "url", "--target",
                                "https://example.com", "--project-root",
                                self.tmp, "--output-dir", self.out, "--json")
        self.assertEqual(rc, 1)
        self.assertEqual(doc["violations"][0]["code"], "OVERWRITE_REFUSED")


# ---- 3 check：既有 schema 三道（裁定 13） ----------------------------------

class SchemaCheckTests(ReverseCase):
    def test_clean_draft_passes(self):
        write_design(self.tmp, tokens_doc())
        rc, doc, _, _ = run_cli("check", "--project-root", self.tmp,
                                "--output-dir", self.out, "--json")
        self.assertEqual(rc, 0, doc)
        self.assertEqual(doc["violations"], [])
        self.assertEqual(doc["counts"]["pages"], 2)

    def test_direction_and_framework_required(self):
        write_design(self.tmp, tokens_doc(direction="", frontend_framework=""))
        rc, doc, _, _ = run_cli("check", "--project-root", self.tmp,
                                "--output-dir", self.out, "--json")
        self.assertEqual(rc, 1)
        self.assertEqual(
            [v["code"] for v in doc["violations"]].count("EMPTY_FIELD"), 2)

    def test_token_families_required(self):
        doc_in = tokens_doc()
        del doc_in["tokens"]["typography"]["family_base"]
        doc_in["tokens"]["spacing"]["scale"] = []
        write_design(self.tmp, doc_in)
        rc, doc, _, _ = run_cli("check", "--project-root", self.tmp,
                                "--output-dir", self.out, "--json")
        self.assertEqual(rc, 1)
        msgs = " ".join(v["where"] + v["msg"] for v in doc["violations"])
        self.assertIn("typography", msgs)
        self.assertIn("spacing", msgs)

    def test_pages_empty_and_four_states(self):
        doc_in = tokens_doc()
        doc_in["pages"][0]["states"] = [{"name": "悬停", "signals": ["图标"]}]
        write_design(self.tmp, doc_in)
        rc, doc, _, _ = run_cli("check", "--project-root", self.tmp,
                                "--output-dir", self.out, "--json")
        self.assertEqual(rc, 1)
        self.assertIn("空态", " ".join(v["msg"] for v in doc["violations"]))

        write_design(self.tmp, tokens_doc(pages=[]))
        rc, doc, _, _ = run_cli("check", "--project-root", self.tmp,
                                "--output-dir", self.out, "--json")
        self.assertEqual(rc, 1)

    def test_prototype_file_must_exist(self):
        write_design(self.tmp, tokens_doc(), prototypes=("P-1",))
        rc, doc, _, _ = run_cli("check", "--project-root", self.tmp,
                                "--output-dir", self.out, "--json")
        self.assertEqual(rc, 1)
        self.assertIn("MISSING_FILE", [v["code"] for v in doc["violations"]])

    def test_color_only_signal_refused(self):
        doc_in = tokens_doc()
        doc_in["pages"][0]["states"][0]["signals"] = ["色彩"]
        write_design(self.tmp, doc_in)
        rc, doc, _, _ = run_cli("check", "--project-root", self.tmp,
                                "--output-dir", self.out, "--json")
        self.assertEqual(rc, 1)
        self.assertIn("ENUM_INVALID", [v["code"] for v in doc["violations"]])


# ---- 4 ID 形态 / 顺序 / 原型同源（既有 schema 是 `P-<n>`，裁定 13） ---------

class PageIdTests(ReverseCase):
    def test_bad_form_sequence_and_prototype_name(self):
        doc_in = tokens_doc()
        doc_in["pages"][1]["id"] = "SC-01.P2"
        doc_in["pages"][1]["prototype"] = "prototypes/other.html"
        write_design(self.tmp, doc_in)
        rc, doc, _, _ = run_cli("check", "--project-root", self.tmp,
                                "--output-dir", self.out, "--json")
        self.assertEqual(rc, 1)
        codes = [v["code"] for v in doc["violations"]]
        self.assertIn("ENUM_INVALID", codes)
        self.assertIn("SET_MISMATCH", codes)

    def test_duplicate_page_id(self):
        doc_in = tokens_doc()
        doc_in["pages"][1]["id"] = "P-1"
        doc_in["pages"][1]["prototype"] = "prototypes/P-1.html"
        write_design(self.tmp, doc_in)
        rc, doc, _, _ = run_cli("check", "--project-root", self.tmp,
                                "--output-dir", self.out, "--json")
        self.assertEqual(rc, 1)
        self.assertIn("DUPLICATE_ID", [v["code"] for v in doc["violations"]])


# ---- 5 终门 + 假设清零 ------------------------------------------------------

class FinalGateTests(ReverseCase):
    def test_final_requires_status_and_no_assumption(self):
        write_design(self.tmp, tokens_doc())
        rc, doc, _, _ = run_cli("check", "--final", "--project-root", self.tmp,
                                "--output-dir", self.out, "--json")
        self.assertEqual(rc, 1)
        self.assertIn("STATUS_MISMATCH", [v["code"] for v in doc["violations"]])

        doc_in = tokens_doc()
        doc_in["project"]["status"] = "已定稿"
        doc_in["pages"][0]["name"] = "[假设] 首页"
        write_design(self.tmp, doc_in)
        rc, doc, _, _ = run_cli("check", "--final", "--project-root", self.tmp,
                                "--output-dir", self.out, "--json")
        self.assertEqual(rc, 1)
        self.assertIn("ASSUMPTION_PRESENT", [v["code"] for v in doc["violations"]])

        doc_ok = tokens_doc()
        doc_ok["project"]["status"] = "已定稿"
        write_design(self.tmp, doc_ok)
        rc, doc, _, _ = run_cli("check", "--final", "--project-root", self.tmp,
                                "--output-dir", self.out, "--json")
        self.assertEqual(rc, 0, doc)


# ---- 6 「不抄像素」判据：重复值可作 token、单次值禁（裁定 13 / census-5 新-2）-

class OneOffJudgementTests(ReverseCase):
    def test_repeat_values_become_tokens_single_values_dropped(self):
        rc, doc, _, _ = run_cli("tokens", "--values",
                                "#ffffff,#1a5fb4,#ffffff,#1a5fb4,#c9a227,16px,16px,20px",
                                "--project-root", self.tmp, "--json")
        self.assertEqual(rc, 0, doc)
        self.assertEqual(doc["counts"]["values"], 8)
        self.assertEqual(doc["counts"]["repeat"], 3)
        self.assertEqual(doc["counts"]["one_off"], 2)
        self.assertEqual(sorted(doc["counts"]["tokens"]),
                         sorted(["#ffffff", "#1a5fb4", "16px"]))
        self.assertEqual(sorted(doc["counts"]["dropped"]), sorted(["#c9a227", "20px"]))
        self.assertEqual([w["code"] for w in doc["warnings"]],
                         ["ONE_OFF_VALUE", "ONE_OFF_VALUE"])

    def test_min_threshold_is_two(self):
        rc, doc, _, _ = run_cli("tokens", "--values", "#111,#111,#222,#333,#333",
                                "--project-root", self.tmp, "--json")
        self.assertEqual(rc, 0)
        self.assertEqual(sorted(doc["counts"]["tokens"]), ["#111", "#333"])

    def test_empty_values_is_usage_error(self):
        rc, _, _, _ = run_cli("tokens", "--values", "  ", "--project-root",
                              self.tmp, "--json")
        self.assertEqual(rc, 1)
        rc, _, _, _ = run_cli("tokens", "--project-root", self.tmp, "--json")
        self.assertEqual(rc, 2)


# ---- 7 跨技能门禁 + 既有引擎交叉核对（裁定 13 的实测面） --------------------

class CrossSkillTests(ReverseCase):
    def test_read_commands_report_missing_product(self):
        rc, doc, _, _ = run_cli("check", "--project-root", self.tmp,
                                "--output-dir", self.out, "--json")
        self.assertEqual(rc, 1)
        self.assertEqual(doc["violations"][0]["code"], "MISSING_FILE")
        rc, doc, _, _ = run_cli("list", "--project-root", self.tmp,
                                "--output-dir", self.out, "--json")
        self.assertEqual(rc, 1)

    def test_product_satisfies_existing_design_engine(self):
        """本引擎的产物必须过既有 `design.py validate` / `check`（裁定 13 三道）。"""
        if not os.path.isfile(DESIGN_PY):
            self.skipTest("diy-design 引擎缺席")
        doc_ok = tokens_doc()
        doc_ok["project"]["status"] = "已定稿"
        path = write_design(self.tmp, doc_ok)
        rc, doc, _, _ = run_cli("check", "--final", "--project-root", self.tmp,
                                "--output-dir", self.out, "--json")
        self.assertEqual(rc, 0, doc)
        for sub in ("validate", "check"):
            proc = subprocess.run(
                [sys.executable, DESIGN_PY, sub, "--design", path, "--json"],
                capture_output=True, text=True, encoding="utf-8",
                env=dict(os.environ, PYTHONIOENCODING="utf-8"))
            self.assertEqual(proc.returncode, 0,
                             "design.py %s 判红：%s" % (sub, proc.stdout))

    def test_list_and_show_roundtrip(self):
        write_design(self.tmp, tokens_doc())
        rc, doc, _, _ = run_cli("list", "--project-root", self.tmp,
                                "--output-dir", self.out, "--json")
        self.assertEqual(rc, 0)
        self.assertEqual(set(doc["items"][0]),
                         {"id", "name", "route", "states", "prototype", "status"})
        rc, doc, _, _ = run_cli("show", "--id", "P-2", "--project-root", self.tmp,
                                "--output-dir", self.out, "--json")
        self.assertEqual(rc, 0)
        self.assertEqual(doc["page"]["route"], "/pricing")
        rc, doc, _, _ = run_cli("show", "--id", "P-9", "--project-root", self.tmp,
                                "--output-dir", self.out, "--json")
        self.assertEqual(rc, 1)
        self.assertEqual(doc["violations"][0]["code"], "UNKNOWN_ID")


# ---- 8 回执键完整性 + 契约冒烟 ---------------------------------------------

class ReceiptTests(ReverseCase):
    def test_all_receipts_carry_common_keys(self):
        write_design(self.tmp, tokens_doc())
        for args in (["list"], ["show"], ["check"]):
            rc, doc, _, _ = run_cli(*args, "--project-root", self.tmp,
                                    "--output-dir", self.out, "--json")
            self.assertTrue(COMMON_KEYS.issubset(set(doc)), args)
            self.assertIsNone(doc["instance"])
        rc, doc, _, _ = run_cli("tokens", "--values", "#111,#111",
                                "--project-root", self.tmp, "--json")
        self.assertTrue(COMMON_KEYS.issubset(set(doc)))


class SkillShapeTests(unittest.TestCase):
    def skill_text(self):
        return io.open(os.path.join(REVERSE_DIR, "SKILL.md"),
                       encoding="utf-8").read()

    def test_main_file_is_thin_four_section(self):
        lines = self.skill_text().splitlines()
        self.assertLessEqual(len(lines), 90, "SKILL.md 超 90 行硬阈值")
        for head in ("## 激活时", "## 工作流", "## 结构", "## 规则"):
            self.assertIn(head, lines)

    def test_frontmatter_five_fields(self):
        fm = yaml.safe_load(self.skill_text().split("---")[1])
        self.assertEqual(fm["phase"], "anytime")
        self.assertEqual(fm["precededBy"], [])
        self.assertEqual(fm["followedBy"], [])
        self.assertIs(fm["required"], False)
        self.assertEqual(fm["line"], "any")
        self.assertEqual(fm["outputs"], "design.yaml")

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

    def test_no_write_outside_design_yaml_and_prototypes(self):
        text = self.skill_text()
        self.assertIn("只在初始生成时写", text)
        self.assertIn("diy-design", text)
        self.assertIn("diy-analyze", text)

    def test_red_line_no_foreign_check_type(self):
        text = self.skill_text()
        self.assertNotIn("check --type", text)
        self.assertNotIn("diyc.py\" check --type", text)

    def test_intellectual_property_rules_present(self):
        text = self.skill_text()
        self.assertIn("不抄像素", text)
        self.assertIn("one-off", text)


class StepsShapeTests(unittest.TestCase):
    def test_frozen_file_names(self):
        got = sorted(f for f in os.listdir(os.path.join(REVERSE_DIR, "steps"))
                     if f.endswith(".md"))
        self.assertEqual(tuple(got), STEPS)

    def test_every_step_has_sections_and_five_elements(self):
        for name in STEPS:
            text = io.open(os.path.join(REVERSE_DIR, "steps", name),
                           encoding="utf-8").read()
            self.assertIn("# Step ", text)
            self.assertIn("Progress: ", text)
            self.assertGreaterEqual(text.count("## 第 "), 1, name)
            self.assertIn("**收尾与路由**：", text)

    def test_one_off_judgement_is_written_into_explore(self):
        text = io.open(os.path.join(REVERSE_DIR, "steps", "02-explore.md"),
                       encoding="utf-8").read()
        self.assertIn("one-off-color", text)
        self.assertIn("one-off-font-size", text)
        self.assertIn("单次值", text)

    def test_shared_skeleton_verbatim(self):
        for name in STEPS:
            text = io.open(os.path.join(REVERSE_DIR, "steps", name),
                           encoding="utf-8").read()
            for lit in SKELETON_LITERALS:
                self.assertIn(lit, text, "%s 缺骨架串：%s" % (name, lit[:20]))


if __name__ == "__main__":
    unittest.main()
