# -*- coding: utf-8 -*-
"""diy-research 确定性引擎 e2e 测试（任务书 B1 §3 / §2.5）。

覆盖：
- 用例 1：拒绝路径零产出（缺 research.yaml → MISSING_FILE exit 1；产物目录保持为空）
- 用例 2：check --final 合法记录 exit 0（计数回执）
- 用例 3：违规码逐类（ENUM_INVALID / EMPTY_FIELD / DUPLICATE_ID /
          ASSUMPTION_PRESENT / STATUS_MISMATCH / UNKNOWN_ID）
- 用例 4：--previous 丢记录 → ID_UNSTABLE；--id 过滤单条记录
- 用例 5：steps/ 三维度覆盖（market|technical|domain 各 4 分析步 + 01-scope + 06-synthesis；
          每步结尾点名下一个文件）
- 用例 6：SKILL.md 契约冒烟（冻结实例句 md5 + 写作纪律块 md5 + 终门句指向 research.py）
夹具全部落 tempdir 自建；不读写本仓库真实 diy-output；不依赖本机 git 状态。
运行：cd diy-coder && python -m unittest discover -s tests -p "test_research.py" -v
"""
import copy
import hashlib
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

# 冻结文本校验值（batch4/frozen-texts.md：§1 实例句 233 字符；§2 写作纪律块 497 字符）
INSTANCE_MD5 = "5445f98bc4d4821e6888b89406a97eac"
DISCIPLINE_MD5 = "f1b3b6fbb528f0cfab31f3196b3547ae"
INSTANCE_ANCHOR = "Instance resolution (FR-4.5/D-9)"

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


def record(rid="RS-001", dimension="market", status="final"):
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
            "confidence": "medium",
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
        self.write_doc(doc(record("RS-001", "market"), record("RS-002", "technical")))
        r = self.check("--final")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertTrue(data["ok"])
        self.assertEqual(data["violations"], [])
        self.assertEqual(data["counts"]["researches"], 2)
        self.assertEqual(data["counts"]["by_dimension"], {"market": 1, "technical": 1})
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
        dup["researches"][1]["dimension"] = "domain"
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
        assumed["researches"][0]["scope"] = "[ASSUMPTION] 假定只做乘用车"
        draft_status = doc(record(status="draft"))
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
        draft = record(status="draft")
        draft["findings"] = []
        draft.pop("synthesis")
        self.write_doc(doc(draft))
        r = self.check()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(json.loads(r.stdout)["violations"], [])

    # trace: 任务书 §3（--id 过滤单条记录；未知 id → UNKNOWN_ID）
    def test_check_id_filter_and_unknown_id(self):
        broken = record("RS-001", "market")
        broken["findings"] = []
        self.write_doc(doc(broken, record("RS-002", "technical")))
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
        write_yaml(prev, doc(record("RS-001"), record("RS-002", "technical")))
        self.write_doc(doc(record("RS-002", "technical"), record("RS-003", "domain")))
        r = self.check("--previous", prev)
        self.assertEqual(r.returncode, 1, r.stdout)
        hits = [x for x in json.loads(r.stdout)["violations"] if x["code"] == "ID_UNSTABLE"]
        self.assertTrue(hits, r.stdout)
        self.assertIn("RS-001", hits[0]["msg"])

    # trace: 任务书 §2.2（追加式改名安全：旧集合是新集合子集 → exit 0）
    def test_previous_subset_passes(self):
        prev = os.path.join(self.root, "research.prev.yaml")
        write_yaml(prev, doc(record("RS-001"), record("RS-002", "technical")))
        self.write_doc(doc(record("RS-001"), record("RS-002", "technical"),
                           record("RS-003", "domain")))
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
        self.write_doc(doc(record(status="draft")))
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
            self.assertIn("## Next", text, "%s 缺 ## Next 段" % path)
            tail = text.split("## Next", 1)[1]
            self.assertTrue(("steps/" in tail) or ("01-scope.md" in tail) or
                            (".md" in tail),
                            "%s 的 Next 未点名下一个文件" % path)


class SkillContractTests(unittest.TestCase):
    """用例 6：SKILL.md 契约冒烟（任务书 §2.1）。"""

    def read_skill(self):
        self.assertTrue(os.path.isfile(SKILL_MD), "SKILL.md 尚未交付")
        with io.open(SKILL_MD, encoding="utf-8") as f:
            return f.read()

    # trace: 任务书 §2.1（冻结实例句逐字；md5 口径同 frozen-texts §3 复现命令）
    def test_instance_sentence_is_frozen_verbatim(self):
        raw = self.read_skill()
        m = re.search(r"Instance resolution \(FR-4\.5/D-9\)[^\r\n]*", raw)
        self.assertTrue(m, "SKILL.md 缺实例解析样板句")
        frag = m.group(0)
        self.assertEqual(len(frag), 233, "实例句字符数偏离冻结文本（233）")
        self.assertEqual(hashlib.md5((frag + NL).encode("utf-8")).hexdigest(),
                         INSTANCE_MD5, "实例句与冻结文本不一致：%s" % frag)

    # trace: 任务书 §2.1（写作纪律块整块逐字；md5 口径同 frozen-texts §3）
    def test_writing_discipline_block_is_frozen_verbatim(self):
        raw = self.read_skill()
        m = re.search(r"^- \*\*Writing discipline\..*$", raw, re.M)
        self.assertTrue(m, "SKILL.md 缺写作纪律块")
        block = m.group(0)
        self.assertEqual(len(block), 497, "写作纪律块字符数偏离冻结文本（497）")
        self.assertEqual(hashlib.md5((block + NL).encode("utf-8")).hexdigest(),
                         DISCIPLINE_MD5, "写作纪律块与冻结文本不一致")

    # trace: 任务书 §2.1（薄主文件 ≤90 行；厚内容在 steps/）
    def test_skill_md_is_thin(self):
        lines = self.read_skill().splitlines()
        self.assertLessEqual(len(lines), 90, "SKILL.md 超 90 行（%d）" % len(lines))
        for section in ("## On Activation", "## Workflow", "## Schema", "## Rules"):
            self.assertIn(section, self.read_skill(), "SKILL.md 缺 %s 段" % section)

    # trace: 任务书 §3（终门句指向本技能引擎 check --final；渲染静默；触发语逐字）
    def test_engine_hooks_and_triggers(self):
        skill = self.read_skill()
        self.assertIn("research.py", skill, "终门句未指向领域引擎")
        self.assertIn("check --final", skill, "终门句缺 check --final")
        self.assertIn("--json", skill, "终门句缺 --json 回执")
        self.assertIn("viewer.py", skill, "缺渲染静默调用命令")
        self.assertNotIn("--open", skill, "渲染静默：不得新增打开浏览器交互点")
        for trigger in SOURCE_TRIGGERS:
            self.assertIn(trigger, skill, "源描述触发语未逐字保留：%s" % trigger)

    # trace: 任务书 §3（门禁：联网检索硬前提句保留）
    def test_web_search_prerequisite_survives(self):
        skill = self.read_skill()
        self.assertRegex(skill, r"[Ww]eb search (is )?required",
                         "缺联网检索硬前提句（源技能 PREREQUISITE）")


if __name__ == "__main__":
    unittest.main()
