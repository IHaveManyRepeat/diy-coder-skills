# -*- coding: utf-8 -*-
"""diy-research 确定性引擎 e2e 测试（任务书 B1 §3 / §2.5）。

覆盖：
- 用例 1：拒绝路径零产出（缺 research.yaml → MISSING_FILE exit 1；产物目录保持为空）
- 用例 2：check --final 合法记录 exit 0（计数回执）
- 用例 3：违规码逐类（ENUM_INVALID / EMPTY_FIELD / DUPLICATE_ID /
          ASSUMPTION_PRESENT / STATUS_MISMATCH / UNKNOWN_ID）
- 用例 4：--previous 丢记录 → ID_UNSTABLE；--id 过滤单条记录
- 用例 5：steps/ 三维度覆盖（market|technical|domain 目录各 4 分析步 + 01-scope + 06-synthesis；
          每步结尾点名下一个文件）+ 形态（H1 中文步名 + Read/Write 两行英文锚）
- 用例 6：SKILL.md 契约冒烟（母本 §1–§6 中文定稿逐字 + 四段中文标题 + ≤93 行 +
          终门句指向 research.py）
- 用例 7：B-19 落点锁（SS-009-02/04/05/06/07/08/09/10/11/12/16/17/18/19 + B1 + A-6）
夹具全部落 tempdir 自建；不读写本仓库真实 diy-output；不依赖本机 git 状态。
运行：cd diy-coder && python -m unittest discover -s tests -p "test_research.py" -v
"""
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.join(HERE, "..", "skills", "diy-research")
ENGINE = os.path.join(SKILL_DIR, "scripts", "research.py")
SKILL_MD = os.path.join(SKILL_DIR, "SKILL.md")
NL = chr(10)

# 套件级句式母本（suite-texts.md §1 / §2 / §3 / §4 / §5 / §6 中文定稿，逐字）
INSTANCE_ZH = ("实例解析（FR-4.5/D-9）由工具脚本执行：运行 "
               "`python \"{project-root}/.claude/skills/diy-tools/scripts/diyc.py\" "
               "resolve [--instance <name>] --json`，把回执里的 `output_dir` "
               "当作本次运行唯一的读写根目录。")
DISCIPLINE_ZH = ("- **写作纪律。** 主字段 = 大白话主句；数字/枚举内联；"
                 "机器语法（命令/旗标/路径）进括号；机器锚点逐字保留"
                 "（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 "
                 "`diy-design` 的 detect 启发式。schema 若定义 `plain`："
                 "一行写清该条目为什么存在，绝不写是什么（转述会漂移）；"
                 "只写难懂的条目。若定义 `detail`：过程叙述——结论留在主字段。")
RESOLVE_KEYS_ZH = ("解析 `project.communication_language` / "
                   "`project.document_output_language` / `paths.output_dir`")
READ_DISCIPLINE_ZH = ("读取纪律：预载预算 = 本文件、上述配置与回执、`steps/` 下当前那一个文件"
                      "——绝不批量预载；执行期读取以每个步骤开头的 `Read (input)` 行为唯一权威，"
                      "**主文件不列举封闭清单**。")
RENDER_SILENT_ZH = "渲染是静默旁路——只写调用命令"
PRECISE_ZH = ("- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；"
              "不复述上游已写的信息（引用 ID）；不写没有信息量的套话。")
# 英文原形（历史，批 4 冻结）——中文化后不得残留
INSTANCE_EN_MARK = "Instance resolution (FR-4.5/D-9)"
DISCIPLINE_EN_MARK = "- **Writing discipline."

# steps/ 全量清单（相对 SKILL_DIR/steps；H1 步号 = 文件名的数字前缀）
STEPS = [
    "01-scope.md", "06-synthesis.md",
    "market/02-customer-behavior.md", "market/03-pain-points.md",
    "market/04-decisions.md", "market/05-competitive.md",
    "technical/02-stack.md", "technical/03-integration.md",
    "technical/04-architecture.md", "technical/05-implementation.md",
    "domain/02-industry.md", "domain/03-competitive-landscape.md",
    "domain/04-regulatory.md", "domain/05-trends.md",
]
# SS-009-18：`Searches` 标题须带并行标记的四个文件（其余 8 个已带）
PARALLEL_MARK = "（并行跑）"
PARALLEL_FILES = ["technical/04-architecture.md", "technical/05-implementation.md",
                  "domain/04-regulatory.md", "domain/05-trends.md"]

# 源技能 description 触发语（逐字保留，任务书 §0 合并口径）
SOURCE_TRIGGERS = (
    "Use when the user says they need market research",
    "Use when the user says they would like to do or produce a technical research report",
    "Use when the user says wants to do domain research for a topic or industry",
)

# steps/ 覆盖清单（任务书 §3：01-scope + <dimension>/02..05 + 06-synthesis）
DIMENSIONS = {
    "market": ["02-customer-behavior.md", "03-pain-points.md",
               "04-decisions.md", "05-competitive.md"],
    "technical": ["02-stack.md", "03-integration.md",
                  "04-architecture.md", "05-implementation.md"],
    "domain": ["02-industry.md", "03-competitive-landscape.md",
               "04-regulatory.md", "05-trends.md"],
}


def read_step(rel):
    """按相对路径读 SKILL_DIR/steps 下的步骤文件。"""
    with io.open(os.path.join(SKILL_DIR, "steps", rel), encoding="utf-8") as f:
        return f.read()


def record(rid="RS-001", dimension="市场", status="已定稿"):
    """合法研究记录夹具（--final 全义务满足）。"""
    return {
        "id": rid,
        "dimension": dimension,
        "topic": "欧洲电动车市场",
        "goals": ["判断是否值得进入"],
        "scope": "德法英三国乘用车，2024-2026 公开数据",
        "date": "2026-09-14",
        "status": status,
        "findings": [{
            "area": "customer-behavior",
            "claim": "城市通勤用户对续航焦虑的敏感度逐年下降",
            "sources": [{
                "title": "IEA Global EV Outlook 2026",
                "url": "https://www.iea.org/reports/global-ev-outlook-2026",
                "accessed": "2026-09-10",
            }],
            "confidence": "中",
        }],
        "synthesis": {
            "executive_summary": "市场增速放缓但渗透率仍上行，需以细分场景切入。",
            "key_points": ["德法英的充电网络密度差异大于价格差异"],
            "open_questions": ["商用车细分未覆盖，需单独研究"],
        },
    }


def write_yaml(path, payload):
    with io.open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(payload, f, allow_unicode=True, sort_keys=False,
                       default_flow_style=False)


def doc(*records):
    return {
        "project": {"name": "mini", "created": "2026-01-01", "updated": "2026-09-14"},
        "researches": list(records),
        "revisions": [],
    }


def run_engine(args):
    return subprocess.run([sys.executable, ENGINE] + args,
                          capture_output=True, text=True, encoding="utf-8")


class EngineCase(unittest.TestCase):
    """tmp 项目根 + diy-output 目录的公共夹具。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="research-")
        self.root = self.tmp.name
        self.out = os.path.join(self.root, "diy-output")
        os.makedirs(self.out, exist_ok=True)

    def tearDown(self):
        self.tmp.cleanup()

    def write_doc(self, payload, name="research.yaml"):
        path = os.path.join(self.out, name)
        write_yaml(path, payload)
        return path

    def check(self, *extra):
        return run_engine(["check", "--project-root", self.root,
                           "--output-dir", self.out, "--json"] + list(extra))

    def doc_path(self):
        return os.path.join(self.out, "research.yaml")


class RefusalTests(EngineCase):

    # trace: 任务书 §2.5 用例 1 / §3（拒绝路径零产出）
    def test_check_missing_file_refuses_with_zero_output(self):
        r = self.check("--final")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertNotIn("Traceback", r.stderr)
        data = json.loads(r.stdout)
        self.assertFalse(data["ok"])
        self.assertEqual([x["code"] for x in data["violations"]], ["MISSING_FILE"])
        self.assertTrue(data["violations"][0]["where"].endswith("research.yaml"))
        self.assertFalse(os.listdir(self.out), "拒绝路径不得写任何文件")

    # trace: 任务书 §2.5 用例 1（损坏 YAML 同样结构化，不崩溃）
    def test_unparsable_doc_is_structured(self):
        with io.open(self.doc_path(), "w", encoding="utf-8") as f:
            f.write("researches: [" + NL)
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertNotIn("Traceback", r.stderr)
        self.assertEqual(json.loads(r.stdout)["violations"][0]["code"], "UNPARSABLE_YAML")

    # trace: 任务书 §2.2（引擎不做实例解析/目录推导：--output-dir 必填）
    def test_output_dir_is_mandatory(self):
        r = run_engine(["check", "--project-root", self.root, "--json"])
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)


class CheckValidationTests(EngineCase):

    # trace: 任务书 §3（合法记录 exit 0 唯一放行 + 计数回执）
    def test_check_final_legal_doc_passes(self):
        self.write_doc(doc(record("RS-001", "市场"), record("RS-002", "技术")))
        r = self.check("--final")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertTrue(data["ok"])
        self.assertEqual(data["violations"], [])
        self.assertEqual(data["counts"]["researches"], 2)
        self.assertEqual(data["counts"]["by_dimension"], {"市场": 1, "技术": 1})
        self.assertEqual(data["counts"]["findings"], 2)
        self.assertEqual(data["counts"]["sources"], 2)

    # trace: 任务书 §3（枚举 / 来源 / 重复 ID 各带违规码）
    def test_check_reports_violation_codes(self):
        bad_dimension = doc(record())
        bad_dimension["researches"][0]["dimension"] = "sales"
        no_source = doc(record())
        no_source["researches"][0]["findings"][0]["sources"] = []
        bad_url = doc(record())
        bad_url["researches"][0]["findings"][0]["sources"][0]["url"] = "ftp://x/y"
        bad_accessed = doc(record())
        bad_accessed["researches"][0]["findings"][0]["sources"][0]["accessed"] = "昨天"
        bad_confidence = doc(record())
        bad_confidence["researches"][0]["findings"][0]["confidence"] = "certain"
        blank_claim = doc(record())
        blank_claim["researches"][0]["findings"][0]["claim"] = "  "
        cases = [
            ("ENUM_INVALID", bad_dimension, ".dimension"),
            ("EMPTY_FIELD", no_source, ".findings[0].sources"),
            ("ENUM_INVALID", bad_url, ".findings[0].sources[0].url"),
            ("ENUM_INVALID", bad_accessed, ".findings[0].sources[0].accessed"),
            ("ENUM_INVALID", bad_confidence, ".findings[0].confidence"),
            ("EMPTY_FIELD", blank_claim, ".findings[0].claim"),
        ]
        for code, payload, where_tail in cases:
            self.write_doc(payload)
            r = self.check("--final")
            self.assertEqual(r.returncode, 1, "%s: %s" % (code, r.stdout + r.stderr))
            data = json.loads(r.stdout)
            hits = [x for x in data["violations"] if x["code"] == code]
            self.assertTrue(hits, "%s 未报出：%s" % (code, r.stdout))
            self.assertTrue(all(x.get("where") and x.get("msg") for x in data["violations"]),
                            r.stdout)
            self.assertTrue(any(where_tail in x["where"] for x in hits),
                            "%s where 未指向 %s：%s" % (code, where_tail, r.stdout))

    # trace: 任务书 §2.4（RS-### 稳定不重用；ID 格式与唯一性）
    def test_check_reports_id_shape_and_duplicates(self):
        bad_id = doc(record())
        bad_id["researches"][0]["id"] = "RS-1"
        self.write_doc(bad_id)
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ENUM_INVALID", {x["code"] for x in json.loads(r.stdout)["violations"]})
        dup = doc(record("RS-001"), record("RS-001"))
        dup["researches"][1]["dimension"] = "领域"
        self.write_doc(dup)
        r2 = self.check()
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertIn("DUPLICATE_ID", {x["code"] for x in json.loads(r2.stdout)["violations"]})

    # trace: 任务书 §3（--final 附加义务：synthesis 三键 / findings / 零假设 / status）
    def test_check_final_duties(self):
        no_synthesis = doc(record())
        no_synthesis["researches"][0]["synthesis"] = {"executive_summary": "只有一句"}
        no_findings = doc(record())
        no_findings["researches"][0]["findings"] = []
        assumed = doc(record())
        assumed["researches"][0]["scope"] = "[假设] 假定只做乘用车"
        draft_status = doc(record(status="草稿"))
        cases = [
            ("EMPTY_FIELD", no_synthesis, ".synthesis"),
            ("EMPTY_FIELD", no_findings, ".findings"),
            ("ASSUMPTION_PRESENT", assumed, ""),
            ("STATUS_MISMATCH", draft_status, ".status"),
        ]
        for code, payload, where_tail in cases:
            self.write_doc(payload)
            r = self.check("--final")
            self.assertEqual(r.returncode, 1, "%s: %s" % (code, r.stdout + r.stderr))
            hits = [x for x in json.loads(r.stdout)["violations"] if x["code"] == code]
            self.assertTrue(hits, "%s 未报出：%s" % (code, r.stdout))
            if where_tail:
                self.assertTrue(any(where_tail in x["where"] for x in hits),
                                "%s where 未指向 %s：%s" % (code, where_tail, r.stdout))

    # trace: 任务书 §2.1（起草期宽松：draft 记录无 synthesis / 无 findings 合法）
    def test_check_draft_record_is_lenient(self):
        draft = record(status="草稿")
        draft["findings"] = []
        draft.pop("synthesis")
        self.write_doc(doc(draft))
        r = self.check()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(json.loads(r.stdout)["violations"], [])

    # trace: 任务书 §3（--id 过滤单条记录；未知 id → UNKNOWN_ID）
    def test_check_id_filter_and_unknown_id(self):
        broken = record("RS-001", "市场")
        broken["findings"] = []
        self.write_doc(doc(broken, record("RS-002", "技术")))
        r = self.check("--final", "--id", "RS-002")
        self.assertEqual(r.returncode, 0, "--id 应只校验指定记录：%s" % (r.stdout + r.stderr))
        self.assertEqual(json.loads(r.stdout)["counts"]["researches"], 1)
        r2 = self.check("--id", "RS-099")
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertIn("UNKNOWN_ID", {x["code"] for x in json.loads(r2.stdout)["violations"]})


class PreviousRoundTests(EngineCase):

    # trace: 任务书 §2.2 / §3（--previous 比对 RS-### 集合；旧有新无 → ID_UNSTABLE）
    def test_previous_dropped_id_is_unstable(self):
        prev = os.path.join(self.root, "research.prev.yaml")
        write_yaml(prev, doc(record("RS-001"), record("RS-002", "技术")))
        self.write_doc(doc(record("RS-002", "技术"), record("RS-003", "领域")))
        r = self.check("--previous", prev)
        self.assertEqual(r.returncode, 1, r.stdout)
        hits = [x for x in json.loads(r.stdout)["violations"] if x["code"] == "ID_UNSTABLE"]
        self.assertTrue(hits, r.stdout)
        self.assertIn("RS-001", hits[0]["msg"])

    # trace: 任务书 §2.2（追加式改名安全：旧集合是新集合子集 → exit 0）
    def test_previous_subset_passes(self):
        prev = os.path.join(self.root, "research.prev.yaml")
        write_yaml(prev, doc(record("RS-001"), record("RS-002", "技术")))
        self.write_doc(doc(record("RS-001"), record("RS-002", "技术"),
                           record("RS-003", "领域")))
        r = self.check("--previous", prev)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    # trace: 任务书 §2.2（--previous 指向缺席文件 → MISSING_FILE，不崩）
    def test_previous_missing_file_is_structured(self):
        self.write_doc(doc(record()))
        r = self.check("--previous", os.path.join(self.root, "nope.yaml"))
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertNotIn("Traceback", r.stderr)
        self.assertEqual(json.loads(r.stdout)["violations"][0]["code"], "MISSING_FILE")

    # trace: 任务书 §2.2（当前稿缺席时只报 MISSING_FILE，不叠加 ID_UNSTABLE 噪音）
    def test_previous_skipped_when_current_file_missing(self):
        prev = os.path.join(self.root, "research.prev.yaml")
        write_yaml(prev, doc(record("RS-001")))
        r = self.check("--previous", prev)
        self.assertEqual(r.returncode, 1, r.stdout)
        codes = [x["code"] for x in json.loads(r.stdout)["violations"]]
        self.assertEqual(codes, ["MISSING_FILE"])


class HumanReadableTests(EngineCase):

    # trace: 任务书 §2.2（无 --json → 中文人读行：每违规一行 CODE where: msg + 汇总行）
    def test_human_readable_output(self):
        self.write_doc(doc(record(status="草稿")))
        r = run_engine(["check", "--final", "--project-root", self.root,
                        "--output-dir", self.out])
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("STATUS_MISMATCH", r.stdout)
        self.assertIn("research.yaml", r.stdout)
        self.assertNotIn("{", r.stdout.split(NL)[0], "人读模式不得输出 JSON")
        self.write_doc(doc(record()))
        r2 = run_engine(["check", "--final", "--project-root", self.root,
                         "--output-dir", self.out])
        self.assertEqual(r2.returncode, 0, r2.stdout + r2.stderr)
        self.assertIn("通过", r2.stdout)


class StepFilesTests(unittest.TestCase):
    """用例 5：steps/ 三维度覆盖（任务书 §3 路由形态）。"""

    def step_files(self):
        return [os.path.join(dirpath, name)
                for dirpath, _dirs, files in os.walk(os.path.join(SKILL_DIR, "steps"))
                for name in files if name.endswith(".md")]

    # trace: 任务书 §3（01-scope + <dimension>/02..05 + 06-synthesis）
    def test_three_dimensions_covered(self):
        path = os.path.join(SKILL_DIR, "steps")
        self.assertTrue(os.path.isfile(os.path.join(path, "01-scope.md")),
                        "缺 01-scope.md")
        self.assertTrue(os.path.isfile(os.path.join(path, "06-synthesis.md")),
                        "缺 06-synthesis.md")
        for dimension, names in DIMENSIONS.items():
            for name in names:
                self.assertTrue(os.path.isfile(os.path.join(path, dimension, name)),
                                "缺 steps/%s/%s" % (dimension, name))

    # trace: 任务书 §2.1（读取纪律：每步文件结尾点名下一个要读的文件）
    def test_every_step_names_the_next_file(self):
        files = self.step_files()
        self.assertGreaterEqual(len(files), 14, "steps/ 文件数不足：%s" % files)
        for path in files:
            with io.open(path, encoding="utf-8") as f:
                text = f.read()
            self.assertIn("## 播报与下一步", text, "%s 缺「播报与下一步」段" % path)
            tail = text.split("## 播报与下一步", 1)[1]
            self.assertTrue(("steps/" in tail) or ("01-scope.md" in tail) or
                            (".md" in tail),
                            "%s 的末段未点名下一个文件" % path)

    # trace: 范本 §三（steps 形态：H1 中文步名 + Read/Write 两行英文锚）
    def test_steps_shape(self):
        for rel in STEPS:
            path = os.path.join(SKILL_DIR, "steps", rel)
            self.assertTrue(os.path.isfile(path), "缺步骤文件 %s" % rel)
            with io.open(path, encoding="utf-8") as f:
                lines = f.read().replace("\r\n", "\n").split("\n")
            m = re.match(r"^# Step (\d+) — .*[一-鿿]", lines[0])
            self.assertTrue(m, "%s 的 H1 须为 '# Step N — <中文步名>'，实为 %r"
                            % (rel, lines[0]))
            self.assertEqual(int(m.group(1)), int(os.path.basename(rel)[:2]),
                             "%s 的步号与文件序不符" % rel)
            self.assertTrue(any(ln.startswith("**Read (input):**") for ln in lines),
                            "%s 缺 '**Read (input):**' 行" % rel)
            self.assertTrue(any(ln.startswith("**Write (output):**") for ln in lines),
                            "%s 缺 '**Write (output):**' 行" % rel)


class SkillContractTests(unittest.TestCase):
    """用例 6：SKILL.md 契约冒烟（任务书 §2.1）。"""

    def read_skill(self):
        self.assertTrue(os.path.isfile(SKILL_MD), "SKILL.md 尚未交付")
        with io.open(SKILL_MD, encoding="utf-8") as f:
            return f.read()

    # trace: 母本 §1（实例解析句中文定稿逐字）
    def test_instance_sentence_zh(self):
        skill = self.read_skill()
        self.assertIn(INSTANCE_ZH, skill, "SKILL.md 缺母本 §1 中文定稿（逐字）")
        self.assertNotIn(INSTANCE_EN_MARK, skill, "已转中文定稿，不得残留英文原形")

    # trace: 母本 §2（写作纪律块中文定稿逐字，置 Rules 段末尾）
    def test_writing_discipline_block_zh(self):
        skill = self.read_skill()
        self.assertIn(DISCIPLINE_ZH, skill, "SKILL.md 缺母本 §2 中文定稿")
        self.assertNotIn(DISCIPLINE_EN_MARK, skill, "已转中文定稿，不得残留英文原形")
        self.assertEqual(DISCIPLINE_ZH, skill.rstrip(NL).splitlines()[-1],
                         "写作纪律块须置 Rules 段末尾")

    # trace: 母本 §3 / §4 / §5 / §6（中文化轮落地锚串逐字）
    def test_mother_text_anchors(self):
        skill = self.read_skill()
        for label, frag in (("§3 配置解析键", RESOLVE_KEYS_ZH),
                            ("§4 读取纪律", READ_DISCIPLINE_ZH),
                            ("§5 渲染静默", RENDER_SILENT_ZH),
                            ("§6 精准简练", PRECISE_ZH)):
            self.assertIn(frag, skill, "SKILL.md 缺母本 %s 逐字文本" % label)

    # trace: 任务书 §2.1 / 2026-09-19 中文化政策（薄主文件 ≤93 行 + 四段中文标题 + 步名点名）
    def test_skill_md_is_thin(self):
        skill = self.read_skill()
        self.assertLessEqual(len(skill.splitlines()), 93, "SKILL.md 超 93 行")
        for section in ("## 激活时", "## 工作流", "## 结构", "## 规则"):
            self.assertIn(section, skill, "SKILL.md 缺四段：%s" % section)
        self.assertIn("# ↑ 中文：", skill, "description 缺中文注释")
        for rel in STEPS:
            self.assertIn(os.path.basename(rel), skill, "工作流未点名 %s" % rel)

    # trace: 任务书 §3（终门句指向本技能引擎 check --final；渲染静默；触发语逐字）
    def test_engine_hooks_and_triggers(self):
        skill = self.read_skill()
        self.assertIn("research.py", skill, "终门句未指向领域引擎")
        self.assertIn("check --final", skill, "终门句缺 check --final")
        self.assertIn("--json", skill, "终门句缺 --json 回执")
        self.assertIn("--output-dir", skill, "激活句/终门句须声明 --output-dir 必填")
        self.assertIn("viewer.py", skill, "缺渲染静默调用命令")
        self.assertNotIn("--open", skill, "渲染静默：不得新增打开浏览器交互点")
        for trigger in SOURCE_TRIGGERS:
            self.assertIn(trigger, skill, "源描述触发语未逐字保留：%s" % trigger)

    # trace: 任务书 §3（门禁：联网检索硬前提句保留；中文化后为中文定稿）
    def test_web_search_prerequisite_survives(self):
        skill = self.read_skill()
        self.assertIn("硬前提", skill, "缺联网检索硬前提（源技能 PREREQUISITE）")
        self.assertIn("联网检索", skill, "硬前提句须点名联网检索")

    # trace: B-19 落点锁（landing-plan §二 十八条 + A-5 / A-6 / B1）
    def test_b19_landings(self):
        skill = self.read_skill()
        # SS-009-04：确认口径改为「检索一落地即写」，不得残留 as it is confirmed
        self.assertNotIn("as it is confirmed", skill, "SS-009-04 未落：残留旧口径")
        self.assertIn("检索一落地时就写进 YAML", skill, "SS-009-04 未落：逐次落笔口径")
        # SS-009-05：非 C 答复按 [Modify] 惯例
        self.assertIn("非 `C` 答复按", skill, "SS-009-05 未落：非 C 答复处置")
        self.assertIn("[Modify]", skill, "SS-009-05 未落：[Modify] 惯例")
        # SS-009-06：单查询零结果 → 重试一次、不写弱证据
        self.assertIn("换检索词重试一次", skill, "SS-009-06 未落：零结果重试")
        self.assertIn("不得拿弱证据凑数", skill, "SS-009-06 未落：不写弱证据")
        # SS-009-07：无出处观察落 synthesis.open_questions
        self.assertIn("无出处的说法不进 `findings[]`", skill, "SS-009-07 未落")
        self.assertIn("synthesis.open_questions", skill, "SS-009-07 未落：缺口载体")
        # SS-009-09：非 0 不删 .prev + 三码分支
        self.assertIn("非 0 一律不删 `.prev`", skill, "SS-009-09 未落：非 0 处置")
        for code in ("ID_UNSTABLE", "MISSING_FILE", "UNPARSABLE_YAML"):
            self.assertIn(code, skill, "SS-009-09 未落：缺 %s 分支" % code)
        # SS-009-08：.prev 触发条件 = 既有记录字段被改写
        self.assertIn("既有 `RS-###` 记录的字段被改写", skill, "SS-009-08 未落：触发条件")
        self.assertIn("新增记录不触发", skill, "SS-009-08 未落：追加不触发")
        # SS-009-02（B5 组）：amend 前回退草稿、改完重跑终门
        self.assertIn("回退 `草稿`", skill, "SS-009-02 未落：amend 前回退")
        self.assertIn("check --final --id RS-xxx", skill, "SS-009-02 未落：单条重跑终门")
        # SS-009-16：Searches 最小集定义
        self.assertIn("最小集", skill, "SS-009-16 未落：Searches 最小集")
        self.assertIn("锚定查询", skill, "SS-009-16 未落：追加锚定查询")
        # SS-009-17：critical claim 五类
        self.assertIn("五类", skill, "SS-009-17 未落：critical claim 五类")
        self.assertIn("市场规模/增速", skill, "SS-009-17 未落：五类点名")
        # B1 组：distillate 交出面（上游只写交出什么）
        self.assertIn("交出面", skill, "B1 未落：distillate 交出面")
        self.assertIn("diy-prd", skill, "B1 未落：映射出处指 diy-prd")
        # A-6（C7 三条约定）
        self.assertIn("不删不猜", skill, "A-6 未落：headless 转 open_questions")
        self.assertIn("不新增独立键", skill, "A-6 未落：前缀只写在值上")
        self.assertIn("ASSUMPTION_PRESENT", skill, "A-6 未落：终门扫的字段集")

        # SS-009-11（A-7 日期口径）落 steps/01-scope.md
        scope = read_step("01-scope.md")
        self.assertIn("本条动作的日子", scope, "SS-009-11 未落：记录级 date 口径")
        self.assertIn("`project.created` 建文件时设、此后不改", scope, "A-7 未落：created")
        self.assertIn("`project.updated` 每次写回刷今天", scope, "A-7 未落：updated")
        # SS-009-10：两条记录串行 + 指路 06-synthesis
        self.assertIn("串行", scope, "SS-009-10 未落：两条记录串行")
        self.assertIn("06-synthesis.md", scope, "SS-009-10 未落：指路收尾步")

        # SS-009-12 / SS-009-14 落 steps/06-synthesis.md
        synth = read_step("06-synthesis.md")
        self.assertIn("复用本维度 02–05 步已定义的 `area` 句柄", synth,
                      "SS-009-12 未落：收尾新条目复用 area 句柄")
        self.assertIn("检索轨迹本身不落盘", synth, "SS-009-14 未落：轨迹不落盘")
        self.assertIn("方法学 = `scope`", synth, "SS-009-14 未落：方法学 = scope")
        self.assertIn("回退 `草稿`", synth, "SS-009-02 未落：收尾步 amend 回退")

        # SS-009-18：6 条查询补 {topic}；4 文件补并行标记
        for rel in ("technical/04-architecture.md", "technical/05-implementation.md"):
            text = read_step(rel)
            queries = [ln for ln in text.splitlines() if ln.strip().startswith('- `"')]
            self.assertEqual(len(queries), 3, "%s 查询条数异常：%s" % (rel, queries))
            for ln in queries:
                self.assertIn('"{topic}', ln, "%s 查询缺 {topic} 锚点：%s" % (rel, ln))
        for rel in PARALLEL_FILES:
            self.assertIn(PARALLEL_MARK, read_step(rel),
                          "%s 的 Searches 标题缺并行标记" % rel)
        # SS-009-19：04 句柄改 deployment-architecture；05 保留 deployment-ops
        self.assertIn("`deployment-architecture`", read_step("technical/04-architecture.md"),
                      "SS-009-19 未落：04 句柄未改名")
        self.assertNotIn("`deployment-ops`", read_step("technical/04-architecture.md"),
                         "SS-009-19 未落：04 旧句柄残留")
        self.assertIn("`deployment-ops`", read_step("technical/05-implementation.md"),
                      "SS-009-19 未落：05 句柄应保留")


if __name__ == "__main__":
    unittest.main()
