# -*- coding: utf-8 -*-
"""diy-product-brief 确定性引擎 e2e 测试（B1 批，任务书 §2.5 / §4）。

覆盖：
- 用例 1：intent 门禁拒绝路径（更新/校验 无产物 → exit 1 + MISSING_FILE + 路由 + 零产出）
- 用例 2：intent 合法路径（「新建」空目录 → exit 0 + 路由 steps/01-discovery.md；产物已存在 → warning）
- 用例 3：check 合法（草稿宽松 exit 0 + counts；--final 定稿记录 exit 0）
- 用例 4：check 违规码（stakes 越界 ENUM_INVALID / BD 重复 DUPLICATE_ID / 缺文件 MISSING_FILE /
          损坏 UNPARSABLE_YAML / --final 义务 EMPTY_FIELD、ASSUMPTION_PRESENT、STATUS_MISMATCH）
- 用例 5：--previous 丢决策 → ID_UNSTABLE（更新模式防丢决策）
- 用例 6：SKILL.md 契约冒烟（冻结实例句 md5 + 写作纪律块 md5 + 终门句指向 brief.py check --final
          + 薄主文件行数上限 + steps/ 逐个点名下一文件 + 技能面零 bmad- 悬空引用）

夹具全部落 tempdir 自建；不读写本仓库真实 diy-output；不依赖本机 git 状态。
运行：cd diy-coder && python -m unittest discover -s tests -p "test_brief.py" -v
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
SKILL_DIR = os.path.join(HERE, "..", "skills", "diy-product-brief")
ENGINE = os.path.join(SKILL_DIR, "scripts", "brief.py")
SKILL_MD = os.path.join(SKILL_DIR, "SKILL.md")
STEPS_DIR = os.path.join(SKILL_DIR, "steps")
NL = chr(10)

# 冻结文本校验值（batch4/frozen-texts.md：§1 实例句 233 字符 / §2 写作纪律块 497 字符）
INSTANCE_MD5 = "5445f98bc4d4821e6888b89406a97eac"
DISCIPLINE_MD5 = "f1b3b6fbb528f0cfab31f3196b3547ae"

BRIEF_YAML = NL.join([
    "project:",
    "  name: mini",
    "  status: 草稿",
    "  created: '2026-09-14'",
    "  updated: '2026-09-14'",
    "brief:",
    "  title: 迷你简报",
    "  stakes: 内部",
    "  problem: 手工迁移逐字对照成本高",
    "  solution: 薄主文件 + 步骤文件 + 领域引擎",
    "  pitch: 把 BMAD 技能改造成 diy 形态。",
    "  users:",
    "  - who: 独立开发者",
    "    need: 一条命令拿回校验结论",
    "  value:",
    "  - point: 确定性下沉到引擎",
    "    evidence: 引擎测试通过",
    "  open_questions:",
    "  - 是否需要多实例支持",
    "  assumptions: []",
    "  extra_sections:",
    "  - name: 范围",
    "    content: 仅本批 5 技能",
    "decisions:",
    "- id: BD-001",
    "  date: '2026-09-14'",
    "  decision: 产物落 YAML 单一源",
    "  rationale: md 追加形态无法机械校验",
    "  status: 生效",
    "- id: BD-002",
    "  date: '2026-09-14'",
    "  decision: 外部交接裁剪",
    "  rationale: diy 无 MCP 对应物",
    "  status: 已反转",
    "addendum:",
    "- section: 被拒方案",
    "  content: 双写 md + yaml",
    "  why_separate: 属于下游文档层的取舍记录，不进简报正文",
    "revisions: []",
]) + NL

# 定稿态：project.status 落「已定稿」+ assumptions 清空（--final 义务的全部满足态）
BRIEF_FINAL_YAML = (BRIEF_YAML
                    .replace("  status: 草稿", "  status: 已定稿"))


def run_engine(args):
    return subprocess.run([sys.executable, ENGINE] + args,
                          capture_output=True, text=True, encoding="utf-8")


class EngineCase(unittest.TestCase):
    """tmp 项目根 + diy-output 目录的公共夹具。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="brief-")
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

    def intent(self, value, *extra):
        return run_engine(["intent", "--intent", value, "--project-root", self.root,
                           "--output-dir", self.out, "--json"] + list(extra))

    def check(self, *extra):
        return run_engine(["check", "--project-root", self.root,
                           "--output-dir", self.out, "--json"] + list(extra))

    def brief_path(self):
        return os.path.join(self.out, "brief.yaml")


class IntentGateTests(EngineCase):

    # trace: 任务书 §4 门禁（更新/校验 无产物 → 零产出退出 + 一行理由 + 路由）
    def test_intent_refuses_without_artifact_and_writes_nothing(self):
        for value in ("更新", "校验"):
            r = self.intent(value)
            self.assertEqual(r.returncode, 1, "%s: %s" % (value, r.stdout + r.stderr))
            self.assertNotIn("Traceback", r.stderr)
            data = json.loads(r.stdout)
            self.assertFalse(data["ok"])
            self.assertFalse(data["exists"])
            self.assertEqual([x["code"] for x in data["violations"]], ["MISSING_FILE"])
            self.assertTrue(data["reason"], data)
            self.assertIn("新建", data["reason"], "拒绝理由须给路由（先「新建」）")
            self.assertEqual(data["violations"][0]["where"], "diy-output/brief.yaml")
        self.assertFalse(os.path.exists(self.brief_path()),
                         "门禁拒绝路径不得产出 brief.yaml")
        self.assertEqual(os.listdir(self.out), [], "拒绝路径不得写任何文件")

    # trace: 任务书 §4（「新建」为唯一可在空目录运行的模式；路由指向 01-discovery）
    def test_intent_create_routes_to_discovery_with_zero_writes(self):
        r = self.intent("新建")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertTrue(data["ok"])
        self.assertFalse(data["exists"])
        self.assertEqual(data["route"], "steps/01-discovery.md")
        self.assertEqual(os.listdir(self.out), [], "intent 只读检测，绝不写产物")

    # trace: 任务书 §4（既有产物 → 更新/校验 模式；「新建」撞既有产物给 resume 语义 warning）
    def test_intent_reports_existing_artifact_state(self):
        self.write("diy-output/brief.yaml", BRIEF_FINAL_YAML)
        r = self.intent("更新")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertTrue(data["ok"])
        self.assertTrue(data["exists"])
        self.assertEqual(data["status"], "已定稿")
        self.assertEqual(data["route"], "steps/04-update.md")
        # 读取成本纪律：回执给出既有产物规模，模型不必读全文
        self.assertEqual(data["counts"]["decisions"], 2)
        self.assertEqual(data["counts"]["open_questions"], 1)
        r2 = self.intent("校验")
        self.assertEqual(json.loads(r2.stdout)["route"], "steps/05-validate.md")
        r3 = self.intent("新建")
        self.assertEqual(r3.returncode, 0, r3.stdout)
        self.assertTrue(json.loads(r3.stdout)["warnings"], "「新建」撞既有产物须告警（resume 语义）")

    # trace: 任务书 §4（损坏既有产物：不得静默按可用处理）
    def test_intent_flags_unparsable_artifact(self):
        self.write("diy-output/brief.yaml", "brief: [" + NL)
        r = self.intent("更新")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertNotIn("Traceback", r.stderr)
        self.assertEqual(json.loads(r.stdout)["violations"][0]["code"], "UNPARSABLE_YAML")

    # trace: 任务书 §2.2（引擎不做实例解析/目录推导：--output-dir 必填，intent 值收封闭集）
    def test_usage_errors_and_mandatory_output_dir(self):
        r = run_engine(["intent", "--intent", "新建", "--project-root", self.root, "--json"])
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        r2 = run_engine(["check", "--project-root", self.root, "--json"])
        self.assertEqual(r2.returncode, 2, r2.stdout + r2.stderr)
        r3 = self.intent("frobnicate")
        self.assertEqual(r3.returncode, 2, r3.stdout + r3.stderr)


class CheckValidationTests(EngineCase):

    # trace: 任务书 §2.5 用例 3（draft 起草期宽松：exit 0 唯一放行 + counts）
    def test_check_draft_is_lenient_and_counts(self):
        self.write("diy-output/brief.yaml", BRIEF_YAML)
        r = self.check()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertTrue(data["ok"])
        self.assertEqual(data["violations"], [])
        self.assertEqual(data["counts"]["decisions"], 2)
        self.assertEqual(data["counts"]["decisions_by_status"], {"生效": 1, "已反转": 1})
        self.assertEqual(data["counts"]["users"], 1)
        self.assertEqual(data["counts"]["addendum"], 1)

    # trace: 任务书 §2.5 用例 3（--final 定稿记录 exit 0）
    def test_check_final_legal_record_passes(self):
        self.write("diy-output/brief.yaml", BRIEF_FINAL_YAML)
        r = self.check("--final")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertTrue(data["ok"])
        self.assertTrue(data["final"])
        self.assertEqual(data["violations"], [])

    # trace: 任务书 §4（--final 附加：status 已落「已定稿」/ title-problem-solution-users 非空 /
    #        assumptions 清空 / 每条 decision 有 rationale）
    def test_check_final_duties_report_codes(self):
        cases = [
            ("STATUS_MISMATCH", BRIEF_FINAL_YAML.replace("  status: 已定稿", "  status: 草稿")),
            ("EMPTY_FIELD", BRIEF_FINAL_YAML.replace("  title: 迷你简报" + NL, "")),
            ("EMPTY_FIELD", BRIEF_FINAL_YAML.replace("  rationale: diy 无 MCP 对应物" + NL, "")),
            ("ASSUMPTION_PRESENT",
             BRIEF_FINAL_YAML.replace("  assumptions: []",
                                      NL.join(["  assumptions:", "  - '[假设] 用户未定'"]))),
        ]
        for code, text in cases:
            self.write("diy-output/brief.yaml", text)
            r = self.check("--final")
            self.assertEqual(r.returncode, 1, "%s: %s" % (code, r.stdout + r.stderr))
            data = json.loads(r.stdout)
            self.assertFalse(data["ok"])
            self.assertIn(code, {x["code"] for x in data["violations"]},
                          "%s 未报出：%s" % (code, r.stdout))
            self.assertTrue(all(x.get("where") and x.get("msg")
                                for x in data["violations"]), r.stdout)

    # trace: 任务书 §2.4（[假设] 扫描覆盖全文任意字段，不止 assumptions 列表）
    def test_final_scans_assumption_tag_anywhere(self):
        text = BRIEF_FINAL_YAML.replace(
            "  problem: 手工迁移逐字对照成本高",
            "  problem: '[假设] 手工迁移逐字对照成本高'")
        self.write("diy-output/brief.yaml", text)
        r = self.check("--final")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ASSUMPTION_PRESENT", {x["code"] for x in json.loads(r.stdout)["violations"]})

    # trace: 任务书 §4（schema / stakes 枚举 / decision id 唯一）
    def test_check_enum_id_dates_and_codes(self):
        cases = [
            ("ENUM_INVALID", BRIEF_YAML.replace("stakes: 内部", "stakes: masochistic")),
            ("ENUM_INVALID", BRIEF_YAML.replace("id: BD-001", "id: BD-1")),
            ("ENUM_INVALID", BRIEF_YAML.replace("  status: 生效", "  status: superseded")),
            ("EMPTY_FIELD", BRIEF_YAML.replace("  why_separate: 属于下游文档层的取舍记录，不进简报正文" + NL, "")),
            ("DUPLICATE_ID", BRIEF_YAML.replace("id: BD-002", "id: BD-001")),
        ]
        for code, text in cases:
            self.write("diy-output/brief.yaml", text)
            r = self.check()
            self.assertEqual(r.returncode, 1, "%s: %s" % (code, r.stdout + r.stderr))
            self.assertIn(code, {x["code"] for x in json.loads(r.stdout)["violations"]},
                          "%s 未报出：%s" % (code, r.stdout))

    # trace: 任务书 §2.3（缺文件/损坏 → 结构化违规，不 Traceback）
    def test_check_missing_and_unparsable_are_structured(self):
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertNotIn("Traceback", r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual(data["violations"][0]["code"], "MISSING_FILE")
        self.assertEqual(data["counts"]["decisions"], 0)
        self.write("diy-output/brief.yaml", "brief: [" + NL)
        r2 = self.check()
        self.assertEqual(r2.returncode, 1)
        self.assertNotIn("Traceback", r2.stderr)
        self.assertEqual(json.loads(r2.stdout)["violations"][0]["code"], "UNPARSABLE_YAML")

    # trace: 任务书 §2.2（--previous 适用范围含本技能：update 模式防丢决策）
    def test_previous_detects_lost_decision(self):
        prev = self.write("diy-output/brief.prev.yaml", BRIEF_YAML)
        self.write("diy-output/brief.yaml", BRIEF_FINAL_YAML)
        r = self.check("--previous", prev)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(json.loads(r.stdout)["violations"], [])
        # 新稿丢掉 BD-002 → ID_UNSTABLE（msg 注明旧 ID）
        without = BRIEF_FINAL_YAML.replace(NL.join([
            "- id: BD-002",
            "  date: '2026-09-14'",
            "  decision: 外部交接裁剪",
            "  rationale: diy 无 MCP 对应物",
            "  status: 已反转",
        ]) + NL, "")
        self.write("diy-output/brief.yaml", without)
        r2 = self.check("--previous", prev)
        self.assertEqual(r2.returncode, 1, r2.stdout)
        data = json.loads(r2.stdout)
        self.assertIn("ID_UNSTABLE", {x["code"] for x in data["violations"]})
        self.assertTrue(any("BD-002" in x["msg"] for x in data["violations"]), r2.stdout)
        # 旧稿缺席 → 结构化 MISSING_FILE（快照流程未执行）
        r3 = self.check("--previous", os.path.join(self.out, "nope.yaml"))
        self.assertEqual(r3.returncode, 1, r3.stdout)
        self.assertIn("MISSING_FILE", {x["code"] for x in json.loads(r3.stdout)["violations"]})


class SkillContractTests(unittest.TestCase):
    """用例 6：SKILL.md / steps 契约冒烟（冻结文本逐字 + 结构与路由纪律）。"""

    def read(self, path):
        if not os.path.isfile(path):
            self.skipTest("%s 尚未交付——契约用例待补" % os.path.basename(path))
        with io.open(path, encoding="utf-8") as f:
            return f.read()

    # trace: 任务书 §2.1（冻结实例句逐字；md5 口径同 frozen-texts §3 复现命令）
    def test_instance_sentence_is_frozen_verbatim(self):
        raw = self.read(SKILL_MD)
        m = re.search(r"Instance resolution \(FR-4\.5/D-9\)[^\r\n]*", raw)
        self.assertTrue(m, "SKILL.md 缺实例解析样板句")
        frag = m.group(0)
        self.assertEqual(len(frag), 233, "实例句字符数偏离冻结文本（233）")
        self.assertEqual(hashlib.md5((frag + NL).encode("utf-8")).hexdigest(), INSTANCE_MD5,
                         "实例句与冻结文本不一致：%s" % frag)

    # trace: 任务书 §2.1（写作纪律块逐字，置 Rules 段末尾）
    def test_writing_discipline_block_is_frozen_verbatim(self):
        raw = self.read(SKILL_MD)
        m = re.search(r"^- \*\*Writing discipline\..*$", raw, re.MULTILINE)
        self.assertTrue(m, "SKILL.md 缺写作纪律块")
        block = m.group(0)
        self.assertEqual(len(block), 497, "纪律块字符数偏离冻结文本（497）")
        self.assertEqual(hashlib.md5((block + NL).encode("utf-8")).hexdigest(), DISCIPLINE_MD5,
                         "纪律块与冻结文本不一致")
        self.assertEqual(raw.rindex("- **Writing discipline."), len(raw) - len(block) - 1,
                         "纪律块须置 Rules 段末尾（文件收尾行）")

    # trace: 任务书 §2.2/§4（终门句指向本技能领域引擎 check --final；--output-dir 必填有记载）
    def test_final_gate_points_to_engine(self):
        skill = self.read(SKILL_MD)
        self.assertIn("brief.py", skill, "终门句未指向领域引擎")
        self.assertIn("check --final", skill, "终门句缺 check --final")
        self.assertIn("--json", skill, "终门句缺 --json 回执")
        self.assertIn("--output-dir", skill, "激活句/终门句须声明 --output-dir 必填")
        self.assertIn("diyc.py", skill, "激活句须委托 diyc.py resolve 做实例解析")

    # trace: 任务书 §2.1（薄主文件 ≤ 90 行）+ 读取纪律（never batch-load）
    def test_thin_main_file_and_read_discipline(self):
        skill = self.read(SKILL_MD)
        self.assertLessEqual(len(skill.split(NL)), 90, "主文件超 90 行上限")
        self.assertIn("never batch-load", skill, "缺读取成本纪律句")
        for section in ("## On Activation", "## Workflow", "## Schema", "## Rules"):
            self.assertIn(section, skill, "缺四段结构：%s" % section)

    # trace: 任务书 §2.1（steps/ 读一条加载一条，每步结尾点名下一个文件）
    def test_steps_chain_names_next_file(self):
        chain = [("01-discovery.md", "02-draft.md"), ("02-draft.md", "03-finalize.md"),
                 ("03-finalize.md", "04-update.md"), ("04-update.md", "05-validate.md")]
        for name, nxt in chain:
            text = self.read(os.path.join(STEPS_DIR, name))
            self.assertIn("## Next", text, "%s 缺 Next 段" % name)
            self.assertIn(nxt, text, "%s 未点名下一个文件 %s" % (name, nxt))
        last = self.read(os.path.join(STEPS_DIR, "05-validate.md"))
        self.assertIn("04-update.md", last, "validate 须提供转 update 的回接")

    # trace: 任务书 §0.3（未建技能引用一律裁剪——技能面不得留悬空 bmad- 引用）
    def test_no_dangling_bmad_references(self):
        targets = [SKILL_MD]
        if os.path.isdir(STEPS_DIR):
            targets += [os.path.join(STEPS_DIR, n)
                        for n in sorted(os.listdir(STEPS_DIR)) if n.endswith(".md")]
        for path in targets:
            text = self.read(path)
            hits = re.findall(r"bmad-[a-z0-9-]+", text)
            self.assertEqual(hits, [], "%s 含悬空 bmad- 引用：%s" % (path, hits))


if __name__ == "__main__":
    unittest.main()
