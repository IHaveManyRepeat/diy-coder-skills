# -*- coding: utf-8 -*-
"""diy-prfaq 确定性引擎 e2e 测试（B1 批，任务书 §5 / §2.5）。

覆盖：
- 用例 1：headless 输入门禁——缺项 → exit 1 + 具名缺口 + 零产出；四项齐全 → exit 0
- 用例 2：check 合法草稿 / 合法定稿 exit 0 + counts（起草期宽松：空 verdict / 空 FAQ 合法）
- 用例 3：check 违规各带 violation code（ENUM_INVALID / STATUS_MISMATCH / EMPTY_FIELD /
          DUPLICATE_ID / ASSUMPTION_PRESENT / MISSING_FILE / UNPARSABLE_YAML）
- 用例 4：--previous 稳定 ID 比对（旧有新无 → ID_UNSTABLE；旧稿缺席 → MISSING_FILE）
- 用例 5：SKILL.md 契约冒烟（两段冻结文本逐字 md5 + 终门句指向 prfaq.py check --final）
- 附加：--output-dir 必填（argparse 用法错误 exit 2）

夹具全部落 tempdir 自建；不读写本仓库真实 diy-output。
运行：cd diy-coder && python -m unittest discover -s tests -p "test_prfaq.py" -v
"""
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.join(HERE, "..", "skills", "diy-prfaq", "scripts", "prfaq.py")
SKILL_MD = os.path.join(HERE, "..", "skills", "diy-prfaq", "SKILL.md")
STEP_01_MD = os.path.join(HERE, "..", "skills", "diy-prfaq", "steps", "01-ignition.md")
NL = chr(10)

# 冻结文本校验值（batch4/frozen-texts.md §1 §2：逐字复制，禁改写）
INSTANCE_MD5 = "5445f98bc4d4821e6888b89406a97eac"
DISCIPLINE_MD5 = "f1b3b6fbb528f0cfab31f3196b3547ae"
INSTANCE_ANCHOR = "Instance resolution (FR-4.5/D-9)"
DISCIPLINE_ANCHOR = "- **Writing discipline."

# 合法草稿：stage 2，press_release 部分填写（起草期宽松），一条客户 FAQ
PRFAQ_DRAFT = NL.join([
    "project:",
    "  name: mini",
    "  status: draft",
    "  created: '2026-09-14'",
    "  updated: '2026-09-14'",
    "prfaq:",
    "  stage: 2",
    "  concept_type: commercial",
    "  essentials:",
    "    customer: 独立开发者",
    "    problem: 手工整理需求耗时",
    "    stakes: 交付延期",
    "    solution: 自动生成 PRFAQ 草稿",
    "  press_release:",
    "    headline: 需求整理从三小时到三分钟",
    "    subheadline: 独立开发者当天拿到成型概念",
    "  customer_faq:",
    "  - id: PQ-001",
    "    q: 与现有工具有何不同？",
    "    a: 直接产出可交付的概念拷问稿",
    "  internal_faq: []",
    "  verdict: {}",
    "distillate:",
    "  problem: 需求整理耗时",
    "  target_users:",
    "  - 独立开发者",
    "  value_props:",
    "  - 三分钟出草稿",
    "  constraints: []",
    "  open_questions: []",
    "notes:",
    "- stage: 1",
    "  content: 概念类型判定为商业产品；被挑战的假设：需求整理其实不痛",
    "revisions: []",
]) + NL

# 合法定稿：stage 5，九键齐全，PQ 序列文档级连续，verdict 与 distillate 非空
PRFAQ_FINAL = NL.join([
    "project:",
    "  name: mini",
    "  status: final",
    "  created: '2026-09-14'",
    "  updated: '2026-09-14'",
    "prfaq:",
    "  stage: 5",
    "  concept_type: open-source",
    "  essentials:",
    "    customer: 独立开发者",
    "    problem: 手工整理需求耗时",
    "    stakes: 交付延期",
    "    solution: 自动生成 PRFAQ 草稿",
    "  press_release:",
    "    headline: 需求整理从三小时到三分钟",
    "    subheadline: 独立开发者当天拿到成型概念",
    "    opening: 今天发布 X，把需求整理压到三分钟",
    "    problem: 手工整理把周末吃掉",
    "    solution: 一份 YAML 承载全部拷问结论",
    "    leader_quote: 概念不该靠会议纪要存活",
    "    how_it_works: 给出四要素，逐步回答客户与内部问题",
    "    customer_quote: 我终于敢在周五立项了",
    "    getting_started: 安装后运行一次即可拿到草稿",
    "  customer_faq:",
    "  - id: PQ-001",
    "    q: 与现有工具有何不同？",
    "    a: 直接产出可交付的概念拷问稿",
    "  - id: PQ-002",
    "    q: 数据存在哪里？",
    "    a: 全部落本地 YAML，不上传",
    "  internal_faq:",
    "  - id: PQ-003",
    "    q: 最难的技术问题是什么？",
    "    a: 问题生成的领域校准",
    "  verdict:",
    "    strength: forged",
    "    narrative: 客户问题经得起追问，成本模型仍缺实证",
    "distillate:",
    "  problem: 需求整理耗时",
    "  target_users:",
    "  - 独立开发者",
    "  value_props:",
    "  - 三分钟出草稿",
    "  constraints:",
    "  - 仅本地文件，不做云端同步",
    "  open_questions:",
    "  - 成本模型缺实测数据",
    "notes:",
    "- stage: 1",
    "  content: 概念类型判定为开源项目；被挑战的假设：维护者会用云端",
    "- stage: 3",
    "  content: 客户问题暴露数据归属缺口，裁为 accepted trade-off",
    "revisions: []",
]) + NL


def run_engine(args):
    return subprocess.run([sys.executable, ENGINE] + args,
                          capture_output=True, text=True, encoding="utf-8")


def swap(text, old, new):
    """夹具改写：锚点必须命中，否则夹具静默不生效（假绿）。"""
    assert old in text, "夹具锚点未命中：%r" % old
    return text.replace(old, new)


class EngineCase(unittest.TestCase):
    """tmp 项目根 + diy-output 目录的公共夹具。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="prfaq-")
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

    def check(self, *extra):
        return run_engine(["check", "--project-root", self.root,
                           "--output-dir", self.out, "--json"] + list(extra))

    def headless(self, *extra):
        return run_engine(["headless", "--project-root", self.root,
                           "--output-dir", self.out, "--json"] + list(extra))

    def prfaq_path(self):
        return os.path.join(self.out, "prfaq.yaml")


class HeadlessGateTests(EngineCase):

    # trace: B1 diy-prfaq 验收 #3（headless 输入门禁：零产出 + 具名缺口 + 指引）
    def test_headless_gate_refuses_with_named_gaps_and_zero_output(self):
        r = self.headless("--problem", "手工整理需求耗时")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertNotIn("Traceback", r.stderr)
        data = json.loads(r.stdout)
        self.assertFalse(data["ok"])
        self.assertEqual(sorted(data["gaps"]), ["customer", "solution", "stakes"])
        self.assertTrue(data["reason"], data)
        codes = {x["code"] for x in data["violations"]}
        self.assertIn("EMPTY_FIELD", codes)
        self.assertTrue(all(x.get("where") and x.get("msg") for x in data["violations"]),
                        r.stdout)
        self.assertEqual(data["counts"]["essential_fields"], 1)
        self.assertEqual(os.listdir(self.out), [], "门禁拒绝路径不得写任何文件")

    # trace: B1 diy-prfaq §5（headless：四项在场且非空 → 放行）
    def test_headless_gate_passes_with_four_essentials(self):
        r = self.headless("--customer", "独立开发者", "--problem", "手工整理需求耗时",
                          "--stakes", "交付延期", "--solution", "自动生成 PRFAQ 草稿")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertTrue(data["ok"])
        self.assertEqual(data["gaps"], [])
        self.assertEqual(data["counts"]["essential_fields"], 4)
        self.assertEqual(os.listdir(self.out), [], "headless 校验是只读门禁，不写文件")
        # 空白串视同缺项（确定性只查在场/非空）
        r2 = self.headless("--customer", "   ", "--problem", "p", "--stakes", "s",
                           "--solution", "x")
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertEqual(json.loads(r2.stdout)["gaps"], ["customer"])


class CheckValidationTests(EngineCase):

    # trace: B1 diy-prfaq 验收 #2（合法草稿 exit 0 唯一放行；起草期宽松）
    def test_check_draft_legal_record_passes(self):
        self.write("diy-output/prfaq.yaml", PRFAQ_DRAFT)
        r = self.check()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertTrue(data["ok"])
        self.assertEqual(data["violations"], [])
        self.assertEqual(data["counts"]["stage"], 2)
        self.assertEqual(data["counts"]["customer_faq"], 1)
        self.assertEqual(data["counts"]["faqs"], 1)
        self.assertEqual(data["counts"]["notes"], 1)

    # trace: B1 diy-prfaq 验收 #2（--final 定稿义务：stage=5 + 九键非空 + distillate 非空）
    def test_check_final_legal_record_passes(self):
        self.write("diy-output/prfaq.yaml", PRFAQ_FINAL)
        r = self.check("--final")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertTrue(data["ok"], r.stdout)
        self.assertEqual(data["counts"]["internal_faq"], 1)
        self.assertEqual(data["counts"]["open_questions"], 1)
        self.assertEqual(data["counts"]["notes"], 2)

    # trace: B1 diy-prfaq 验收 #2（三类违规各带 code：枚举 / 阶段 / 空字段）
    def test_check_final_reports_violation_codes(self):
        cases = [
            ("ENUM_INVALID",
             swap(PRFAQ_FINAL, "    strength: forged", "    strength: great")),
            ("STATUS_MISMATCH",
             swap(PRFAQ_FINAL, "  stage: 5", "  stage: 4")),
            ("EMPTY_FIELD",
             swap(PRFAQ_FINAL, "    headline: 需求整理从三小时到三分钟" + NL, "")),
        ]
        for code, text in cases:
            self.write("diy-output/prfaq.yaml", text)
            r = self.check("--final")
            self.assertEqual(r.returncode, 1, "%s: %s" % (code, r.stdout + r.stderr))
            data = json.loads(r.stdout)
            self.assertFalse(data["ok"])
            self.assertIn(code, {x["code"] for x in data["violations"]},
                          "%s 未报出：%s" % (code, r.stdout))
            self.assertTrue(all(x.get("where") and x.get("msg")
                                for x in data["violations"]), r.stdout)

    # trace: B1 diy-prfaq 验收 #2/#4（essentials 四键非空；FAQ ID 唯一与格式）
    def test_check_essentials_and_faq_ids(self):
        missing = swap(PRFAQ_DRAFT, "    stakes: 交付延期" + NL, "")
        self.write("diy-output/prfaq.yaml", missing)
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("EMPTY_FIELD", {x["code"] for x in json.loads(r.stdout)["violations"]})
        # 重复 ID：内部 FAQ 复用客户 FAQ 的 PQ-001（文档级单一序列）
        dup = swap(PRFAQ_FINAL, "  - id: PQ-003", "  - id: PQ-001")
        self.write("diy-output/prfaq.yaml", dup)
        r2 = self.check()
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertIn("DUPLICATE_ID", {x["code"] for x in json.loads(r2.stdout)["violations"]})
        # 格式越界：PQ-1 非三位零填充
        bad = swap(PRFAQ_FINAL, "  - id: PQ-002", "  - id: PQ-2")
        self.write("diy-output/prfaq.yaml", bad)
        r3 = self.check()
        self.assertEqual(r3.returncode, 1, r3.stdout)
        self.assertIn("ENUM_INVALID", {x["code"] for x in json.loads(r3.stdout)["violations"]})

    # trace: B1 diy-prfaq 验收 #2（--final 零 [ASSUMPTION]）
    def test_check_final_rejects_assumption_marker(self):
        # YAML 块序列项以 `[` 开头须引号包裹（未引号会破坏解析）——SKILL.md 同款纪律
        text = swap(PRFAQ_FINAL, "  - 成本模型缺实测数据",
                    "  - '[ASSUMPTION] 成本模型缺实测数据'")
        self.write("diy-output/prfaq.yaml", text)
        r = self.check("--final")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ASSUMPTION_PRESENT",
                      {x["code"] for x in json.loads(r.stdout)["violations"]})
        # 起草期允许（草稿清单一并回归）
        self.write("diy-output/prfaq.yaml", PRFAQ_DRAFT)
        self.assertEqual(self.check().returncode, 0)

    # trace: B1 diy-prfaq 验收 #2（notes 键：过程叙事承载，逐条校验 stage/content）
    def test_check_notes_entries(self):
        # 出现时校验：stage 越界 → ENUM_INVALID；content 空 → EMPTY_FIELD
        bad_stage = swap(PRFAQ_FINAL, "  content: 客户问题暴露数据归属缺口，裁为 accepted trade-off",
                         "  content: 客户问题暴露数据归属缺口")
        bad_stage = swap(bad_stage, "- stage: 3", "- stage: 6")
        self.write("diy-output/prfaq.yaml", bad_stage)
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ENUM_INVALID", {x["code"] for x in json.loads(r.stdout)["violations"]})
        blank = swap(PRFAQ_FINAL, "  content: 概念类型判定为开源项目；被挑战的假设：维护者会用云端",
                     "  content: ''")
        self.write("diy-output/prfaq.yaml", blank)
        r2 = self.check()
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertIn("EMPTY_FIELD", {x["code"] for x in json.loads(r2.stdout)["violations"]})
        # 形状：notes 非列表 → EMPTY_FIELD；缺席合法（§2.4 起草期宽松）
        absent = swap(PRFAQ_FINAL, "notes:" + NL + "- stage: 1" + NL
                      + "  content: 概念类型判定为开源项目；被挑战的假设：维护者会用云端" + NL
                      + "- stage: 3" + NL
                      + "  content: 客户问题暴露数据归属缺口，裁为 accepted trade-off" + NL, "")
        not_list = swap(absent, "revisions: []", "notes: {}" + NL + "revisions: []")
        self.write("diy-output/prfaq.yaml", not_list)
        r3 = self.check()
        self.assertEqual(r3.returncode, 1, r3.stdout)
        self.assertIn("EMPTY_FIELD", {x["code"] for x in json.loads(r3.stdout)["violations"]})
        self.write("diy-output/prfaq.yaml", absent)
        r4 = self.check("--final")
        self.assertEqual(r4.returncode, 0, r4.stdout + r4.stderr)  # 缺席合法
        self.assertEqual(json.loads(r4.stdout)["counts"]["notes"], 0)

    # trace: B1 diy-prfaq 验收 #2（缺文件 / 损坏 YAML → 结构化违规，不 Traceback）
    def test_check_missing_file_and_unparsable_are_structured(self):
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertNotIn("Traceback", r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual(data["violations"][0]["code"], "MISSING_FILE")
        self.assertEqual(data["counts"]["faqs"], 0)
        self.write("diy-output/prfaq.yaml", "prfaq: [" + NL)
        r2 = self.check()
        self.assertEqual(r2.returncode, 1)
        self.assertNotIn("Traceback", r2.stderr)
        self.assertEqual(json.loads(r2.stdout)["violations"][0]["code"], "UNPARSABLE_YAML")


class PreviousTests(EngineCase):

    # trace: B1 diy-prfaq 验收 #4（--previous：稳定 PQ ID 集合比对，旧有新无 → ID_UNSTABLE）
    def test_previous_reports_id_unstable(self):
        dropped = swap(PRFAQ_FINAL, "  - id: PQ-002" + NL + "    q: 数据存在哪里？" + NL
                       + "    a: 全部落本地 YAML，不上传" + NL, "")
        self.write("diy-output/prfaq.yaml.prev", PRFAQ_FINAL)  # 旧稿含 PQ-002
        self.write("diy-output/prfaq.yaml", dropped)           # 新稿丢失 PQ-002
        r = self.check("--previous", os.path.join(self.out, "prfaq.yaml.prev"))
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertIn("ID_UNSTABLE", {x["code"] for x in data["violations"]})
        msg = [x for x in data["violations"] if x["code"] == "ID_UNSTABLE"][0]
        self.assertIn("PQ-002", msg["msg"])
        # 新旧一致 → exit 0
        self.write("diy-output/prfaq.yaml", PRFAQ_FINAL)
        r2 = self.check("--previous", os.path.join(self.out, "prfaq.yaml.prev"))
        self.assertEqual(r2.returncode, 0, r2.stdout + r2.stderr)

    # trace: B1 diy-prfaq 验收 #4（--previous 路径无效 → 结构化 MISSING_FILE）
    def test_previous_missing_file_is_structured(self):
        self.write("diy-output/prfaq.yaml", PRFAQ_FINAL)
        r = self.check("--previous", os.path.join(self.out, "nope.yaml"))
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertNotIn("Traceback", r.stderr)
        self.assertIn("MISSING_FILE", {x["code"] for x in json.loads(r.stdout)["violations"]})


class CliContractTests(EngineCase):

    # trace: B1 diy-prfaq 验收 #12（引擎不做实例解析/目录推导：--output-dir 必填）
    def test_output_dir_is_mandatory(self):
        for cmd in ("check", "headless"):
            r = run_engine([cmd, "--project-root", self.root, "--json"])
            self.assertEqual(r.returncode, 2, "%s: %s" % (cmd, r.stdout + r.stderr))

    # trace: B1 diy-prfaq §2.2（无 --json → 中文人读行：每违规一行 + 汇总）
    def test_human_readable_refusal(self):
        r = run_engine(["headless", "--project-root", self.root,
                        "--output-dir", self.out])
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("EMPTY_FIELD", r.stdout)
        self.assertIn("customer", r.stdout)


class SkillContractTests(unittest.TestCase):
    """用例 5：SKILL.md 契约冒烟（B1 批冻结文本 + 终门接线）。"""

    def read_skill(self):
        with io.open(SKILL_MD, encoding="utf-8") as f:
            return f.read()

    # trace: B1 diy-prfaq §2.1（实例解析句逐字；md5 口径同 frozen-texts §3 复现命令）
    def test_instance_sentence_is_frozen_verbatim(self):
        raw = self.read_skill()
        m = re.search(r"Instance resolution \(FR-4\.5/D-9\)[^\r\n]*", raw)
        self.assertTrue(m, "SKILL.md 缺实例解析样板句")
        frag = m.group(0)
        self.assertEqual(len(frag), 233, "实例句字符数偏离冻结文本（233）")
        self.assertEqual(hashlib.md5((frag + NL).encode("utf-8")).hexdigest(),
                         INSTANCE_MD5, "实例句与冻结文本不一致：%s" % frag)

    # trace: B1 diy-prfaq §2.1（写作纪律块逐字，置 Rules 段末尾）
    def test_writing_discipline_block_is_frozen_verbatim(self):
        raw = self.read_skill().replace(chr(13), "")
        lines = [line for line in raw.split(NL) if line.startswith(DISCIPLINE_ANCHOR)]
        self.assertEqual(len(lines), 1, "SKILL.md 写作纪律块数量异常：%d" % len(lines))
        self.assertEqual(len(lines[0]), 497, "纪律块字符数偏离冻结文本（497）")
        self.assertEqual(hashlib.md5((lines[0] + NL).encode("utf-8")).hexdigest(),
                         DISCIPLINE_MD5, "纪律块与冻结文本不一致")
        rules_at = raw.index("## Rules")
        self.assertGreater(raw.index(lines[0]), rules_at, "纪律块未落在 Rules 段内")

    # trace: B1 diy-prfaq §2.1（终门句指向 prfaq.py check --final）
    def test_final_gate_points_to_engine(self):
        skill = self.read_skill()
        self.assertIn("prfaq.py", skill, "终门句未指向领域引擎")
        self.assertIn("check --final", skill, "终门句缺 check --final")
        self.assertIn("--json", skill, "终门句缺 --json 回执")

    # trace: B1 diy-prfaq §12.5 收敛（被拒方案回流 distillate.constraints 的权威路由句在 01）
    def test_rejection_routing_is_declared_in_step_01(self):
        with io.open(STEP_01_MD, encoding="utf-8") as f:
            step = f.read()
        self.assertIn("`Not <X>: because <Y>`", step,
                      "01 缺被拒方案的约束式路由句（防下游重提）")
        self.assertIn("`distillate.constraints`", step, "01 缺 constraints 落点")
        self.assertIn("`distillate.open_questions`", step, "01 缺 open_questions 落点")


if __name__ == "__main__":
    unittest.main()
