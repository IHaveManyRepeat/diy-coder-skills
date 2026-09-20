# -*- coding: utf-8 -*-
"""diy-elicit 只读方法库引擎测试（形 B：无 check、无写回、无写面）。

覆盖（任务书 §4 的 6 项，各至少一条用例；第 6 项的契约冒烟按断言面拆 4 条）：
- 用例 1：`methods --random 5` 返 5 条且不重复
- 用例 2：`--category` 非法值 → exit 1 + ENUM_INVALID（argparse 级用法错误仍为 exit 2）
- 用例 3：`--category` 合法值（中文化后的中文类名）只返该类
- 用例 4：`--all` 条数 == methods.csv 数据行数 == 69（中文化后仍须 69）
- 用例 5：方法库每条 description 与 output_pattern 非空（12 类不减）
- 用例 6：契约冒烟（母本 §1 实例句逐字 + 零写面声明句在场；另加母本 §2 / §3 / §6 逐字、
          四段中文标题、≤90 行、§5 非成员、引擎零写盘的行为证据）

形 B 回执面（任务书 §2.2 形态分派表）：只收 `[--json]`（免 `--project-root` / `--output-dir`）、
共同键豁免 `project_root` / `output_dir` / `violations` 三键改 `{ok, command, counts}`；
载荷键 `methods:[...]` 与失败键 `msg` 按 SS-028-04「归 W」自定。

夹具全部落 tempdir 自建；不读写本仓库真实 diy-output、不写本仓库任何目录。
运行：cd diy-coder && python -m unittest discover -s tests -p "test_elicit.py" -v
"""
import csv
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.join(HERE, "..", "skills", "diy-elicit")
ENGINE = os.path.join(SKILL_DIR, "scripts", "elicit.py")
SKILL_MD_PATH = os.path.join(SKILL_DIR, "SKILL.md")
LIBRARY = os.path.join(SKILL_DIR, "methods.csv")


def run_engine(args, cwd):
    """cwd 一律指向 tempdir：任何写盘都会落在可检视的临时目录里。"""
    return subprocess.run([sys.executable, ENGINE] + args,
                          capture_output=True, text=True, encoding="utf-8", cwd=cwd)


def read_text(path):
    with io.open(path, encoding="utf-8") as fh:
        return fh.read()


def library_rows():
    """解析方法库 CSV（条数对账以文件为准，不复制常量）。"""
    with io.open(LIBRARY, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


class EngineCase(unittest.TestCase):
    """tmp 工作目录夹具（引擎只读，工作目录仅用于验零写盘）。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="elicit-")
        self.cwd = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def methods(self, *extra):
        return run_engine(["methods"] + list(extra), self.cwd)


class MethodsRandomTests(EngineCase):

    # trace: B4 diy-elicit 用例 1（--random 5 返 5 条且不重复）
    def test_random_five_distinct(self):
        r = self.methods("--random", "5", "--json")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(len(r.stdout.strip().splitlines()), 1, "--json 须单行回执")
        data = json.loads(r.stdout)
        self.assertTrue(data["ok"], r.stdout)
        self.assertEqual(data["command"], "methods")
        picked = data["methods"]
        self.assertEqual(len(picked), 5, r.stdout)
        self.assertEqual(len({m["num"] for m in picked}), 5, "随机抽 5 条不得重复")
        self.assertEqual(len({m["method_name"] for m in picked}), 5)
        self.assertEqual(data["counts"]["returned"], 5)
        self.assertEqual(data["counts"]["total"], 69, "方法库总条数（中文化后仍须 69）")
        self.assertEqual(data["counts"]["categories"], 12, "方法库类别数（12 类不减）")


class CategoryTests(EngineCase):

    # trace: B4 diy-elicit 用例 2（--category 非法值 exit 1 + ENUM_INVALID；用法错误 exit 2）
    def test_category_invalid_rejected(self):
        r = self.methods("--category", "不存在的类", "--json")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertFalse(data["ok"])
        self.assertIn("ENUM_INVALID", data["msg"], "失败回执须点名 ENUM_INVALID")
        self.assertIn("ENUM_INVALID", r.stderr, "诊断行（stderr）须点名 ENUM_INVALID")

        human = self.methods("--category", "不存在的类")
        self.assertEqual(human.returncode, 1, human.stdout + human.stderr)
        self.assertIn("ENUM_INVALID", human.stderr)

        # argparse 级用法错误仍为 exit 2（非正数 N / 互斥旗标同给）
        self.assertEqual(self.methods("--random", "0").returncode, 2)
        self.assertEqual(self.methods("--random", "x").returncode, 2)
        self.assertEqual(self.methods("--random", "5", "--all").returncode, 2)

    # trace: B4 diy-elicit 用例 3（--category 合法值只返该类）
    def test_category_valid_filters_one_class(self):
        expected = sorted(int(row["num"]) for row in library_rows()
                          if row["category"] == "技术")
        self.assertTrue(expected, "方法库里应有「技术」类")
        r = self.methods("--category", "技术", "--json")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertTrue(data["ok"], r.stdout)
        self.assertEqual(sorted(m["num"] for m in data["methods"]), expected)
        for item in data["methods"]:
            self.assertEqual(item["category"], "技术")
            self.assertTrue(item["description"])
            self.assertTrue(item["output_pattern"])
        self.assertEqual(data["counts"]["returned"], len(expected))


class LibraryTests(EngineCase):

    # trace: B4 diy-elicit 用例 4（--all 条数 == CSV 数据行数 == 69）
    def test_all_lists_every_csv_row(self):
        rows = library_rows()
        self.assertEqual(len(rows), 69, "方法库条数中文化后仍须 69")
        r = self.methods("--all", "--json")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual(len(data["methods"]), 69)
        self.assertEqual([m["num"] for m in data["methods"]],
                         [int(row["num"]) for row in rows], "全列须与库内顺序一致")
        self.assertEqual(data["counts"]["returned"], 69)

    # trace: B4 diy-elicit 用例 5（库内每条 description 与 output_pattern 非空；12 类不减）
    def test_library_rows_are_complete(self):
        rows = library_rows()
        for row in rows:
            self.assertTrue(row["category"].strip(), row)
            self.assertTrue(row["method_name"].strip(), row)
            self.assertTrue(row["description"].strip(), row)
            self.assertTrue(row["output_pattern"].strip(), row)
        self.assertEqual(len({row["category"] for row in rows}), 12, "类别数不得减少")


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
PRECISE_ZH = ("- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；"
              "不复述上游已写的信息（引用 ID）；不写没有信息量的套话。")
DISCIPLINE_ZH = ("- **写作纪律。** 主字段 = 大白话主句；数字/枚举内联；"
                 "机器语法（命令/旗标/路径）进括号；机器锚点逐字保留"
                 "（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 "
                 "`diy-design` 的 detect 启发式。schema 若定义 `plain`："
                 "一行写清该条目为什么存在，绝不写是什么（转述会漂移）；"
                 "只写难懂的条目。若定义 `detail`：过程叙述——结论留在主字段。")
ZERO_WRITE_ZH = "本技能不改任何文件"
RENDER_ANCHOR_ZH = "渲染是静默旁路——只写调用命令"
VIEWER_ENGINE = "diy-viewer/scripts/viewer.py"
SECTIONS_ZH = ("## 激活时", "## 工作流", "## 结构", "## 规则")


class SkillContractTests(unittest.TestCase):
    """用例 6：SKILL.md 契约冒烟（§1 母本句 + 零写面声明句，另加母本 §2/§3/§6 与形态项）。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="elicit-smoke-")
        self.workdir = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def skill(self):
        return read_text(SKILL_MD_PATH)

    # trace: 母本 §1（实例解析句中文定稿逐字）
    def test_instance_sentence_verbatim(self):
        raw = self.skill()
        self.assertIn(INSTANCE_ZH, raw, "SKILL.md 缺母本 §1 中文定稿（逐字）")
        self.assertNotIn(INSTANCE_EN_MARK, raw)

    # trace: 母本 §3（键路径 project. 前缀 / 缺省链 / 实例触发三段）
    def test_resolve_keys_default_chain_and_instance_flag(self):
        raw = self.skill()
        self.assertIn(RESOLVE_KEYS_ZH, raw, "缺母本 §3 键路径锚串")
        self.assertIn(DEFAULT_CHAIN_ZH, raw, "缺母本 §3 缺省链")
        self.assertIn(INSTANCE_FLAG_ZH, raw, "缺母本 §3 实例触发条款")

    # trace: 母本 §6 + §2（Rules 末尾，§6 在前）+ 四段中文标题 + ≤90 行 + §5/§4 非成员
    def test_skill_shape_and_discipline_blocks(self):
        raw = self.skill()
        self.assertIn(PRECISE_ZH, raw, "缺母本 §6 中文定稿")
        self.assertIn(DISCIPLINE_ZH, raw, "缺母本 §2 中文定稿")
        self.assertLess(raw.index(PRECISE_ZH), raw.index(DISCIPLINE_ZH),
                        "Rules 末尾顺序须为：§6 精准简练 → §2 写作纪律块")
        self.assertTrue(raw.rstrip("\n").endswith(DISCIPLINE_ZH), "写作纪律块须置文件收尾行")
        self.assertLessEqual(len(raw.splitlines()), 90, "薄主文件超出 90 行预算")
        for section in SECTIONS_ZH:
            self.assertIn(section, raw, "SKILL.md 缺四段中文标题：%s" % section)
        self.assertNotIn(RENDER_ANCHOR_ZH, raw, "零产物技能无渲染步骤（母本 §5 非成员）")
        self.assertNotIn(VIEWER_ENGINE, raw, "零产物技能不得接 viewer")

    # trace: 任务书 §4（零写面声明句在场）+ §2.5 W2 例外（无终门句，引擎无 check）
    def test_zero_write_declaration_and_engine_is_read_only(self):
        raw = self.skill()
        self.assertIn(ZERO_WRITE_ZH, raw, "SKILL.md 缺零写面声明句")
        # 零写面可核证据（SS-027-31 / E-16：声明句之外给一条行为断言）——
        # 在空 tempdir 里跑一轮主命令，目录内容不变即引擎无写盘。
        before = sorted(os.listdir(self.workdir))
        r = run_engine(["methods", "--random", "5", "--json"], self.workdir)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(sorted(os.listdir(self.workdir)), before, "引擎在 cwd 留下了文件")


if __name__ == "__main__":
    unittest.main()
