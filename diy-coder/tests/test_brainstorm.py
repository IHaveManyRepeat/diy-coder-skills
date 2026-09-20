# -*- coding: utf-8 -*-
"""diy-brainstorm 确定性引擎 e2e 测试（B4 批 W1；任务书 §3 测试节 10 项逐条对应用例）。

覆盖：
- 用例 1：init 建记录且 BS 序号连续（骨架字段 + 回执键完整性 + 骨架即过 check）
- 用例 2：init 产物已有记录时续号不重号；损坏产物拒绝且零写入（门禁零产出）
- 用例 3：list 空产物返回空列表（ok: true，不报错）
- 用例 4：techniques 命令面——`--all` 条数 == brain-methods.csv 数据行数（61）且每条
          description 非空；`--category` 合法值只返该类、非法值 exit 1（ENUM_INVALID）；
          `--random N` 不重复
- 用例 5：check 检出 themes[].ideas / actions[].idea 引用越界 no（UNKNOWN_ID）
- 用例 6：check 检出想法 no 跳号（SET_MISMATCH）
- 用例 7：check 检出 status 非法（ENUM_INVALID）
- 用例 8：check 检出 current_step 与 status 不一致（STATUS_MISMATCH）
- 用例 9：check --final 对未完成记录拒绝；对完整记录放行
- 用例 10：SKILL.md 契约冒烟（母本 §1 中文定稿逐字 + 四段中文标题 + 终门句指向本技能引擎）

夹具全部落 tempdir 自建；不读写本仓库真实 diy-output；不依赖本机 git 状态。
运行：cd diy-coder && python -m unittest discover -s tests -p "test_brainstorm.py" -v
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
ENGINE = os.path.join(HERE, "..", "skills", "diy-brainstorm", "scripts", "brainstorm.py")
SKILL_MD = os.path.join(HERE, "..", "skills", "diy-brainstorm", "SKILL.md")
METHODS_CSV = os.path.join(HERE, "..", "skills", "diy-brainstorm", "brain-methods.csv")
NL = chr(10)

# 套件级句式母本（suite-texts.md §1 / §2 / §6 中文定稿，逐字）——B4 技能中文原生，直接写定稿
INSTANCE_ZH = ("实例解析（FR-4.5/D-9）由工具脚本执行：运行 "
               "`python \"{project-root}/.claude/skills/diy-tools/scripts/diyc.py\" "
               "resolve [--instance <name>] --json`，把回执里的 `output_dir` "
               "当作本次运行唯一的读写根目录。")
DISCIPLINE_ZH = ("- **写作纪律。** 主字段 = 大白话主句；数字/枚举内联；机器语法（命令/旗标/路径）"
                 "进括号；机器锚点逐字保留（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 "
                 "`diy-design` 的 detect 启发式。schema 若定义 `plain`：一行写清该条目为什么存在，"
                 "绝不写是什么（转述会漂移）；只写难懂的条目。若定义 `detail`：过程叙述——结论留在主字段。")
PRECISE_ZH = ("- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；"
              "不复述上游已写的信息（引用 ID）；不写没有信息量的套话。")

RECEIPT_KEYS = ("ok", "command", "project_root", "output_dir", "violations",
                "warnings", "counts")

# 完整会话记录夹具（已完成 / current_step: 5；各校验面自洽）
COMPLETE_YAML = NL.join([
    "project:",
    "  name: mini",
    "  created: '2026-01-01'",
    "  updated: '2026-09-20'",
    "sessions:",
    "- id: BS-001",
    "  topic: 会话续接体验",
    "  goals: 产出可执行的改进项",
    "  approach: AI 推荐",
    "  date: '2026-09-20'",
    "  status: 已完成",
    "  current_step: 5",
    "  techniques:",
    "  - {name: 连续五问, category: 深度分析}",
    "  ideas:",
    "  - no: 1",
    "    title: 会话卡片",
    "    concept: 一屏看完状态。续接点直达。",
    "    novelty: 免读全文",
    "    technique: 连续五问",
    "  - no: 2",
    "    title: 断点提示",
    "    concept: 回到会话即见下一步。",
    "    novelty: 免回忆",
    "    technique: 连续五问",
    "  themes:",
    "  - {name: 续接体验, focus: 回到会话的成本, ideas: [1, 2]}",
    "  priorities:",
    "    top: [1]",
    "    quick_wins: [2]",
    "    breakthroughs: []",
    "  actions:",
    "  - idea: 1",
    "    why: 续接成本最高",
    "    steps: [设计卡片字段, 实现 list 命令]",
    "    resources: 无",
    "    timeline: 一周",
    "    success: 续接步数减半",
    "  open_questions: []",
    "revisions: []",
]) + NL


def run_engine(args):
    return subprocess.run([sys.executable, ENGINE] + args,
                          capture_output=True, text=True, encoding="utf-8")


def csv_rows():
    """brain-methods.csv 数据行（CSV 解析器计数：含表头 61 行 / 数据 61 行不得用 wc -l 推断）。"""
    with io.open(METHODS_CSV, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


class EngineCase(unittest.TestCase):
    """tmp 项目根 + diy-output 目录的公共夹具。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="bsp-")
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

    def brainstorm_path(self):
        return os.path.join(self.out, "brainstorm.yaml")

    def engine(self, *args):
        return run_engine(list(args) + ["--project-root", self.root,
                                        "--output-dir", self.out, "--json"])

    def init(self, *extra):
        return self.engine("init", *extra)

    def check(self, *extra):
        return self.engine("check", *extra)

    def list_sessions(self):
        return self.engine("list")

    def read_text(self, rel):
        with io.open(os.path.join(self.root, rel), encoding="utf-8") as f:
            return f.read()


class InitTests(EngineCase):

    # trace: 任务书 §3 测试节用例 1（BS 序号连续 + 骨架字段 + 回执键完整性 + 骨架即过 check）
    def test_init_creates_record_with_sequential_id(self):
        r = self.init("--topic", "会话续接体验", "--goals", "产出可执行的改进项")
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        data = json.loads(r.stdout)
        for key in RECEIPT_KEYS:
            self.assertIn(key, data, "回执缺公共键 %s" % key)
        self.assertIn("updated", data, "写回命令回执须含 updated")
        self.assertEqual(data["counts"]["sessions"], 1)
        text = self.read_text("diy-output/brainstorm.yaml")
        self.assertIn("id: BS-001", text)
        self.assertIn("status: 草稿", text)
        self.assertIn("current_step: 1", text)
        # 序号连续：第二条为 BS-002
        r2 = self.init("--topic", "第二个议题", "--goals", "第二个目标")
        self.assertEqual(r2.returncode, 0, r2.stderr + r2.stdout)
        self.assertEqual(json.loads(r2.stdout)["counts"]["sessions"], 2)
        self.assertIn("id: BS-002", self.read_text("diy-output/brainstorm.yaml"))
        # 骨架即过 check（草稿期宽松：approach / techniques / ideas 可空）
        c = self.check()
        self.assertEqual(c.returncode, 0, c.stdout + c.stderr)
        self.assertEqual(json.loads(c.stdout)["counts"]["sessions"], 2)

    # trace: 任务书 §3 测试节用例 2（续号不重号 + 损坏产物拒绝且零写入）
    def test_init_appends_without_reusing_ids_and_refuses_damaged(self):
        # 既有记录序号有缺口（BS-002）：新记录取 max + 1 = BS-003，不复用 BS-001 空号
        self.write("diy-output/brainstorm.yaml", COMPLETE_YAML.replace("BS-001", "BS-002"))
        r = self.init("--topic", "续号", "--goals", "不重号")
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        text = self.read_text("diy-output/brainstorm.yaml")
        self.assertIn("id: BS-003", text)
        self.assertEqual(text.count("id: BS-003"), 1)
        # 损坏产物：拒绝 + 零写入（原文件逐字节不动）
        self.write("diy-output/brainstorm.yaml", "sessions: [" + NL)
        before = self.read_text("diy-output/brainstorm.yaml")
        r2 = self.init("--topic", "写不进去", "--goals", "拒绝")
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertNotIn("Traceback", r2.stderr)
        data = json.loads(r2.stdout)
        self.assertFalse(data["ok"])
        self.assertEqual(data["violations"][0]["code"], "UNPARSABLE_YAML")
        self.assertEqual(self.read_text("diy-output/brainstorm.yaml"), before,
                         "拒绝路径不得改动产物一个字节")

    # trace: 任务书 §3 测试节用例 3（产物缺席 → 空列表 + ok: true，不报错）
    def test_list_empty_product_returns_empty_list(self):
        r = self.list_sessions()
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        data = json.loads(r.stdout)
        for key in RECEIPT_KEYS:
            self.assertIn(key, data)
        self.assertTrue(data["ok"])
        self.assertEqual(data["sessions"], [])
        self.assertEqual(data["counts"]["sessions"], 0)
        # 有记录时只回五字段（源纪律：只列不读内容）
        self.write("diy-output/brainstorm.yaml", COMPLETE_YAML)
        data2 = json.loads(self.list_sessions().stdout)
        self.assertEqual(len(data2["sessions"]), 1)
        self.assertEqual(sorted(data2["sessions"][0]),
                         ["current_step", "date", "id", "status", "topic"])


class TechniquesTests(EngineCase):

    # trace: 任务书 §3 测试节用例 4（--all 条数 == CSV 数据行数 61 + description 非空；
    # 附：--category 合法/非法、--random 不重复——同一条命令面的边界断言）
    def test_techniques_all_matches_csv_data_rows(self):
        rows = csv_rows()
        self.assertEqual(len(rows), 61, "brain-methods.csv 数据行数须为 61（CSV 解析器计数）")
        r = self.engine("techniques", "--all")
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        data = json.loads(r.stdout)
        self.assertEqual(data["counts"]["techniques"], len(rows))
        for item in data["techniques"]:
            self.assertTrue(item["description"].strip(), "技术 %s 缺 description" % item)
            self.assertTrue(item["category"].strip())
            self.assertTrue(item["technique_name"].strip())
        categories = sorted({x["category"] for x in rows})
        self.assertEqual(len(categories), 10, "技术库须为 10 类")
        # --category 合法值只返该类（取值语言随库：中文类名）
        one = categories[0]
        rc = self.engine("techniques", "--category", one)
        self.assertEqual(rc.returncode, 0, rc.stderr + rc.stdout)
        got = json.loads(rc.stdout)["techniques"]
        self.assertTrue(got)
        self.assertEqual({x["category"] for x in got}, {one})
        # --category 非法值 → exit 1 + ENUM_INVALID
        bad = self.engine("techniques", "--category", "不存在的类")
        self.assertEqual(bad.returncode, 1, bad.stdout)
        self.assertEqual(json.loads(bad.stdout)["violations"][0]["code"], "ENUM_INVALID")
        # --random N：不重复
        rr = self.engine("techniques", "--random", "6")
        self.assertEqual(rr.returncode, 0, rr.stderr + rr.stdout)
        names = [x["technique_name"] for x in json.loads(rr.stdout)["techniques"]]
        self.assertEqual(len(names), 6)
        self.assertEqual(len(set(names)), 6, "--random 抽样不得重复")


class CheckTests(EngineCase):

    # trace: 任务书 §3 测试节用例 5（themes[].ideas 与 actions[].idea 引用越界 → UNKNOWN_ID）
    def test_check_reports_dangling_idea_references(self):
        self.write("diy-output/brainstorm.yaml",
                   COMPLETE_YAML.replace("ideas: [1, 2]", "ideas: [1, 99]"))
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("UNKNOWN_ID", {x["code"] for x in json.loads(r.stdout)["violations"]})
        self.write("diy-output/brainstorm.yaml",
                   COMPLETE_YAML.replace("  - idea: 1" + NL, "  - idea: 9" + NL))
        r2 = self.check()
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertIn("UNKNOWN_ID", {x["code"] for x in json.loads(r2.stdout)["violations"]})

    # trace: 任务书 §3 测试节用例 6（想法 no 跳号 → SET_MISMATCH）
    def test_check_reports_non_consecutive_idea_numbers(self):
        text = (COMPLETE_YAML
                .replace("  - no: 2" + NL, "  - no: 3" + NL)
                .replace("ideas: [1, 2]", "ideas: [1, 3]")
                .replace("quick_wins: [2]", "quick_wins: [3]"))
        self.write("diy-output/brainstorm.yaml", text)
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("SET_MISMATCH", {x["code"] for x in json.loads(r.stdout)["violations"]})

    # trace: 任务书 §3 测试节用例 7（status 非法 → ENUM_INVALID）
    def test_check_reports_invalid_status(self):
        self.write("diy-output/brainstorm.yaml",
                   COMPLETE_YAML.replace("status: 已完成", "status: 归档"))
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ENUM_INVALID", {x["code"] for x in json.loads(r.stdout)["violations"]})

    # trace: 任务书 §3 测试节用例 8（current_step 与 status 不一致 → STATUS_MISMATCH）
    def test_check_reports_step_status_mismatch(self):
        self.write("diy-output/brainstorm.yaml",
                   COMPLETE_YAML.replace("status: 已完成", "status: 进行中"))
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        data = json.loads(r.stdout)
        self.assertIn("STATUS_MISMATCH", {x["code"] for x in data["violations"]})
        self.assertTrue(all(x.get("where") and x.get("msg") for x in data["violations"]))

    # trace: 任务书 §3 测试节用例 9（--final 对未完成记录拒绝；完整记录放行）
    def test_check_final_rejects_unfinished_record(self):
        self.write("diy-output/brainstorm.yaml",
                   COMPLETE_YAML.replace("status: 已完成", "status: 进行中")
                   .replace("current_step: 5", "current_step: 4"))
        r = self.check("--final")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("STATUS_MISMATCH", {x["code"] for x in json.loads(r.stdout)["violations"]})
        # 完整记录：--final 放行（exit 0 唯一放行）
        self.write("diy-output/brainstorm.yaml", COMPLETE_YAML)
        ok = self.check("--final")
        self.assertEqual(ok.returncode, 0, ok.stdout + ok.stderr)
        self.assertTrue(json.loads(ok.stdout)["ok"])
        # 零 [假设]：定稿义务
        self.write("diy-output/brainstorm.yaml",
                   COMPLETE_YAML.replace("免读全文", "免读全文 [假设]待验证"))
        bad = self.check("--final")
        self.assertEqual(bad.returncode, 1, bad.stdout)
        self.assertIn("ASSUMPTION_PRESENT",
                      {x["code"] for x in json.loads(bad.stdout)["violations"]})

    # trace: 任务书 §2.2（--project-root / --output-dir 每个子命令必收；--output-dir 必填）
    def test_output_dir_is_mandatory_on_every_subcommand(self):
        for cmd in ("list", "techniques", "check"):
            r = run_engine([cmd, "--project-root", self.root, "--json"])
            self.assertEqual(r.returncode, 2, "%s: %s" % (cmd, r.stdout + r.stderr))
        r = run_engine(["init", "--topic", "T", "--project-root", self.root, "--json"])
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)


class SkillContractTests(unittest.TestCase):
    """用例 10：SKILL.md 契约冒烟（§2.5 ⑤）。"""

    def read_skill(self):
        if not os.path.isfile(SKILL_MD):
            self.skipTest("SKILL.md 尚未交付（W1 施工中）——用例 10 待补")
        with io.open(SKILL_MD, encoding="utf-8") as f:
            return f.read()

    # trace: 任务书 §2.5 ⑤ / 母本 §1（实例解析句中文定稿逐字）
    def test_skill_contract_smoke(self):
        raw = self.read_skill()
        self.assertIn(INSTANCE_ZH, raw, "SKILL.md 缺母本 §1 中文定稿（逐字）")
        self.assertNotIn("Instance resolution (FR-4.5/D-9)", raw,
                         "已转中文定稿，仍残留英文原形")
        # 四段中文标题（验收 #1/#8/#9/#11/#12）
        for section in ("## 激活时", "## 工作流", "## 结构", "## 规则"):
            self.assertIn(section, raw, "缺段 %s" % section)
        # 母本 §6 / §2（规则段末尾；逐字）
        self.assertIn(PRECISE_ZH, raw, "缺母本 §6 精准简练（逐字）")
        self.assertIn(DISCIPLINE_ZH, raw, "缺母本 §2 写作纪律块（逐字）")
        # 母本 §3 键路径 / §4 读取纪律 / §5 渲染静默
        self.assertIn("解析 `project.communication_language` / "
                      "`project.document_output_language` / `paths.output_dir`", raw)
        self.assertIn("读取纪律：预载预算 = 本文件", raw)
        self.assertIn("渲染是静默旁路——只写调用命令", raw)
        # 终门句指向本技能引擎（b：不产主链产物，无 diyc 类型集终门）
        self.assertIn("brainstorm.py", raw, "终门句未指向领域引擎")
        self.assertIn("check --final", raw, "终门句缺 check --final")
        self.assertIn("--json", raw, "终门句缺 --json 回执")
        # 技能名与产物名在场
        self.assertIn("diy-brainstorm", raw)
        self.assertIn("brainstorm.yaml", raw)
        # 输出体量：薄主文件 ≤ 90 行（验收 #1）
        self.assertLessEqual(len(raw.replace("\r\n", "\n").rstrip("\n").split("\n")), 90,
                             "SKILL.md 超 90 行（薄主文件硬约束）")


if __name__ == "__main__":
    unittest.main()
