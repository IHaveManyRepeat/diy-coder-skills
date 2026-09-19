# -*- coding: utf-8 -*-
"""diy-test-gate 确定性引擎 e2e 测试（B3 批 W2，任务书 §4 / §2.5）。

覆盖：
- 用例 1：前置门禁拒绝（缺 stories.yaml / test-plan 非 已定稿 / 缺 prd.yaml /
          --story 未知）→ exit 1 + 结构化拒绝 + 路由 + 零产出
- 用例 2：collect 矩阵 join（合成四产物：priority 由 prd FR 推导 / TC 绑定 /
          证据台账归属 / totals + by_level）
- 用例 3：collect 覆盖判定表（失败胜、通过无台账 → 计已验证 + warning、待办不计）
- 用例 4：collect 软指标六项 + 缺口清单
- 用例 5：collect 委派 diyc（真跑子进程：上游违规进 diyc.violations 不当失败吞掉；
          diyc 缺席 → TOOL_MISSING 降级不崩）
- 用例 6：collect mutation 面（缺席 n/a + warning / 在场取全部 run 的 score 最小值）
- 用例 7：check 合法记录 --final exit 0 唯一放行（PASS 路径）
- 用例 8：check 门决策不自洽（硬判据 失败 而 decision PASS / 软判据 失败 而 PASS /
          NFR 域 CONCERNS 而 PASS / 判据 actual 陈旧）
- 用例 9：check UNKNOWN 阈值域 PASS / NFR critical FAIL 而门 PASS / 阈值 source 强制记出处
- 用例 10：check waiver 8 键契约 + 安全域不可豁免 + 豁免后 nfr_critical 重算
- 用例 11：check 引用解析（AC 悬空）+ totals 重算 + --final 义务 + 回执共同键
- 用例 12：SKILL.md 契约冒烟（母本 §1 / §2 中文定稿逐字 + 终门句指向 gate.py）
- 用例 13：G-1 证据时效（台账时间戳 / mutation run 日期 >7 天 → EVIDENCE_STALE）
- 用例 14：G-2 跨层重复覆盖候选（同一 technique + kill_target 跨 ≥2 层 → duplicates）
- 用例 15：G-3 合规五标准记账 + 聚合 FAIL>PARTIAL>PASS（第五个走查维度）
- 用例 16：G-4 跨域风险合成（候选命中 → 须落 recommendations / findings）
- 用例 17：G-1..G-4 的走查义务在 steps/ 的落点（源 checklist → diy 明文义务）
- 用例 18：G-3 / G-4 的输入面（合规五标准清单 + 跨域合成规则进 `nfr_inputs`）
夹具全部落 tempdir 自建；不读写本仓库真实 diy-output；不依赖本机 git 状态。
运行：cd diy-coder && python -m unittest discover -s tests -p "test_gate.py" -v
"""
import contextlib
import copy
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import date, timedelta

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.join(HERE, "..", "skills", "diy-test-gate")
ENGINE = os.path.join(SKILL_DIR, "scripts", "gate.py")
SKILL_MD = os.path.join(SKILL_DIR, "SKILL.md")

# 套件级句式母本中文定稿（suite-texts.md §1 / §2；逐字，禁改写）
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

PRD = {
    "project": {"name": "mini", "status": "已定稿", "created": "2026-01-01",
                "updated": "2026-01-02"},
    "features": [
        {"id": "F-1", "name": "能力一", "description": "描述",
         "requirements": [
             {"id": "FR-1.1", "statement": "必须能力一", "priority": "必须"},
             {"id": "FR-1.2", "statement": "应当能力二", "priority": "应该"},
             {"id": "FR-1.3", "statement": "可选能力三", "priority": "可选"},
         ]},
    ],
    "nfrs": [{"id": "NFR-1", "statement": "登录 P95 < 200ms"}],
}

STORIES = {
    "project": {"name": "mini", "status": "已定稿", "created": "2026-01-01",
                "updated": "2026-01-02"},
    "stories": [
        {"id": "S-1", "epic": "E-1", "title": "登录页面",
         "narrative": "作为用户我要登录", "status": "进行中",
         "acceptance_criteria": [
             {"id": "AC-1.1", "given": "已注册", "when": "提交",
              "then": "进入首页", "refs": ["FR-1.1"]},
             {"id": "AC-1.2", "given": "已注册", "when": "密码错",
              "then": "报错", "refs": ["FR-1.2"]},
             {"id": "AC-1.3", "given": "已注册", "when": "验证码",
              "then": "通过", "refs": []},
         ]},
        {"id": "S-2", "epic": "E-1", "title": "登出接口", "narrative": "退出",
         "status": "待办",
         "acceptance_criteria": [
             {"id": "AC-2.1", "given": "已登录", "when": "点登出",
              "then": "回登录页", "refs": ["FR-1.3"]},
         ]},
    ],
}

TEST_PLAN = {
    "project": {"name": "mini", "status": "已定稿", "created": "2026-01-01",
                "updated": "2026-01-02"},
    "test_cases": [
        {"id": "TC-1.1.1", "title": "边界值", "ac": "AC-1.1", "type": "单元",
         "priority": "P0", "technique": "边界", "kill_target": "off-by-one",
         "status": "通过", "steps": ["跑"]},
        {"id": "TC-1.1.2", "title": "负面", "ac": "AC-1.1",
         "type": "集成", "priority": "P0", "technique": "错误猜测",
         "kill_target": "吞异常", "status": "通过", "steps": ["跑"]},
        {"id": "TC-1.2.1", "title": "决策表", "ac": "AC-1.2", "type": "单元",
         "priority": "P1", "technique": "决策表",
         "kill_target": "漏分支", "status": "失败", "steps": ["跑"]},
        {"id": "TC-1.2.2", "title": "边界", "ac": "AC-1.2", "type": "单元",
         "priority": "P1", "technique": "边界", "kill_target": "边界错",
         "status": "通过", "steps": ["跑"]},
        {"id": "TC-1.3.1", "title": "等价类", "ac": "AC-1.3", "type": "单元",
         "priority": "P2", "technique": "等价类", "kill_target": "分类错",
         "status": "待办", "steps": ["跑"]},
    ],
    "static_checks": [{"order": 1, "tool": "python -m ruff check .",
                       "kills": "语法", "gate": "阻断"}],
    "coverage_gaps": [],
}

SPRINT = {
    "project": {"name": "mini", "status": "已定稿", "created": "2026-01-01",
                "updated": "2026-01-02"},
    "tasks": [
        {"story": "S-1", "status": "进行中",
         "test_refs": ["TC-1.1.1", "TC-1.1.2", "TC-1.2.1", "TC-1.2.2"],
         "evidence": [
             {"tc": "TC-1.1.1", "red": "1 failed", "green": "1 passed"},
             {"tc": "TC-1.1.2", "red": "1 failed", "green": "1 passed"},
             {"tc": "TC-1.2.1", "red": "1 failed", "green": "1 passed"},
         ]},
        {"story": "S-2", "status": "待办", "test_refs": [], "evidence": []},
    ],
}


def hard(name, target, actual, result):
    return {"name": name, "target": target, "actual": actual, "result": result}


def soft(name, target, actual, result):
    return {"name": name, "target": target, "actual": actual, "result": result}


def check_stories():
    """check 侧引用解析夹具：两 AC，TC 全 通过。"""
    return {
        "project": {"name": "mini", "status": "已定稿", "created": "2026-01-01",
                    "updated": "2026-01-02"},
        "stories": [
            {"id": "S-1", "epic": "E-1", "title": "登录",
             "narrative": "作为用户我要登录", "status": "进行中",
             "acceptance_criteria": [
                 {"id": "AC-1.1", "given": "g", "when": "w", "then": "t",
                  "refs": ["FR-1.1"]},
                 {"id": "AC-1.2", "given": "g", "when": "w", "then": "t",
                  "refs": ["FR-1.2"]},
             ]},
        ],
    }


def check_plan():
    return {
        "project": {"name": "mini", "status": "已定稿", "created": "2026-01-01",
                    "updated": "2026-01-02"},
        "test_cases": [
            {"id": "TC-1.1.1", "title": "a", "ac": "AC-1.1", "type": "单元",
             "priority": "P0", "technique": "边界", "kill_target": "x",
             "status": "通过", "steps": ["跑"]},
            {"id": "TC-1.1.2", "title": "b", "ac": "AC-1.1",
             "type": "集成", "priority": "P0",
             "technique": "错误猜测", "kill_target": "y",
             "status": "通过", "steps": ["跑"]},
            {"id": "TC-1.2.1", "title": "c", "ac": "AC-1.2", "type": "单元",
             "priority": "P0", "technique": "边界", "kill_target": "z",
             "status": "通过", "steps": ["跑"]},
        ],
        "static_checks": [],
        "coverage_gaps": [],
    }


def check_domains():
    """check 侧四域夹具（G-3：合规五标准行落在最相关的域 `findings`）。"""
    return [
        {"name": name, "status": "PASS",
         "thresholds": [{"name": name + "-t", "target": "1000ms",
                         "measured": "120ms",
                         "source": "用户会话 2026-09-15"}],
         "findings": list(COMPLIANCE_FINDINGS) if name == "安全" else []}
        for name in ("安全", "性能", "可靠性", "可维护性")
    ]


# G-3 第五个走查维度：五标准逐条记账（本夹具全 N/A）
COMPLIANCE_FINDINGS = [
    "SOC2: N/A — 非上市主体，无审计要求",
    "GDPR: N/A — 不处理欧盟个人数据",
    "HIPAA: N/A — 非医疗行业",
    "PCI-DSS: N/A — 不落支付卡特数据",
    "ISO27001: N/A — 未建 ISMS",
]


def check_gate():
    """check 侧 PASS 路径夹具：两 AC 全 FULL、四域 PASS、两组判据自洽。"""
    return {
        "project": {"name": "mini", "created": "2026-01-01",
                    "updated": "2026-09-16"},
        "gates": [
            {"id": "TG-001", "date": "2026-09-16", "status": "已定稿",
             "scope": "story", "story": "S-1",
             "oracle": {"source": "stories", "confidence": "高", "items": 2,
                        "inferred": [], "unresolved": []},
             "coverage": {
                 "items": [
                     {"ref": "AC-1.1", "story": "S-1", "priority": "P0",
                      "coverage": "FULL", "tests": ["TC-1.1.1", "TC-1.1.2"]},
                     {"ref": "AC-1.2", "story": "S-1", "priority": "P0",
                      "coverage": "FULL", "tests": ["TC-1.2.1"]},
                 ],
                 "totals": {"covered": 2, "total": 2, "pct": 100},
                 "by_level": {"单元": 2, "集成": 1, "端到端": 0},
                 "heuristics": [],
             },
             "nfr": {
                 "domains": check_domains(),
                 "overall_risk": "NONE",
                 "adr": {"rows": 29, "passed": 27},
                 "gaps": [],
             },
             "gate": {
                 "decision": "PASS",
                 "hard_criteria": [
                     hard("p0_coverage", "100%", "100%", "通过"),
                     hard("overall_coverage", "100%", "100%", "通过"),
                     hard("p1_coverage", "100%", "100%", "通过"),
                     hard("mutation_score", ">=90%", "n/a", "n/a"),
                     hard("nfr_critical", 0, 0, "通过"),
                     hard("p0_uncovered", 0, 0, "通过"),
                 ],
                 "soft_criteria": [
                     soft("business_rule_coverage", "100%", "100%", "通过"),
                     soft("boundary_coverage", "100%", "100%", "通过"),
                     soft("negative_scenario_coverage", ">=90%", "100%", "通过"),
                     soft("p0_depth_full", "100%", "100%", "通过"),
                     soft("effective_case_ratio", ">=95%", "100%", "通过"),
                     soft("id_chain_resolvable", "100%", "100%", "通过"),
                 ],
                 "blockers": [],
                 "waivers": [],
                 "basis": "三线覆盖全 100%，四域无 FAIL/CONCERNS，无 overlay 命中。",
                 "recommendations": ["补 boundary 用例"],
             },
             "open_questions": []},
        ],
        "revisions": [],
    }


def run_engine(args):
    return subprocess.run([sys.executable, ENGINE] + args,
                          capture_output=True, text=True, encoding="utf-8")


class EngineCase(unittest.TestCase):
    """tmp 项目根 + diy-output 目录的公共夹具。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="gate-")
        self.root = self.tmp.name
        self.out = os.path.join(self.root, "diy-output")
        os.makedirs(self.out, exist_ok=True)

    def tearDown(self):
        self.tmp.cleanup()

    def write_doc(self, name, data):
        path = os.path.join(self.out, name)
        with io.open(path, "w", encoding="utf-8") as fh:
            yaml.safe_dump(data, fh, allow_unicode=True, sort_keys=False)
        return path

    def write_trio(self, prd=PRD, stories=STORIES, plan=TEST_PLAN, sprint=SPRINT):
        self.write_doc("prd.yaml", prd)
        self.write_doc("stories.yaml", stories)
        self.write_doc("test-plan.yaml", plan)
        if sprint is not None:
            self.write_doc("sprint.yaml", sprint)

    def write_check_fixtures(self):
        self.write_doc("prd.yaml", PRD)
        self.write_doc("stories.yaml", check_stories())
        self.write_doc("test-plan.yaml", check_plan())
        self.write_doc("test-gate.yaml", check_gate())

    def mutate_gate(self, mutate):
        data = copy.deepcopy(check_gate())
        mutate(data)
        self.write_doc("test-gate.yaml", data)

    def collect(self, *extra):
        return run_engine(["collect", "--project-root", self.root,
                           "--output-dir", self.out, "--json"] + list(extra))

    def check(self, *extra):
        return run_engine(["check", "--project-root", self.root,
                           "--output-dir", self.out, "--json"] + list(extra))

    def out_files(self):
        return sorted(os.listdir(self.out))

    def codes(self, data, key="violations"):
        return [item["code"] for item in data[key]]

    def criterion(self, data, name, group="hard_criteria"):
        gate = data["gates"][0]["gate"]
        return [c for c in gate[group] if c["name"] == name][0]


class GateTests(EngineCase):

    # trace: 任务书 §4 门禁（stories 缺席 → 零产出退出 + 路由 diy-epics-stories）
    def test_gate_refuses_missing_stories(self):
        self.write_doc("prd.yaml", PRD)
        self.write_doc("test-plan.yaml", TEST_PLAN)
        r = self.collect()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertNotIn("Traceback", r.stderr)
        data = json.loads(r.stdout)
        self.assertFalse(data["ok"])
        self.assertFalse(data["gate"]["passed"])
        self.assertEqual(self.codes(data), ["MISSING_FILE"])
        self.assertIn("stories.yaml", data["violations"][0]["where"])
        self.assertIn("diy-epics-stories", data["gate"]["route"])
        self.assertEqual(self.out_files(), ["prd.yaml", "test-plan.yaml"],
                         "拒绝路径不得产出任何文件")

    # trace: 任务书 §4 门禁（test-plan 须 已定稿 → 路由 diy-test-design）
    def test_gate_refuses_non_final_test_plan(self):
        plan = copy.deepcopy(TEST_PLAN)
        plan["project"]["status"] = "草稿"
        self.write_trio(plan=plan)
        r = self.collect()
        self.assertEqual(r.returncode, 1, r.stdout)
        data = json.loads(r.stdout)
        self.assertEqual(self.codes(data), ["STATUS_MISMATCH"])
        self.assertIn("diy-test-design", data["gate"]["route"])

    # trace: 任务书 §4 门禁（prd.yaml 为 priority 前提，缺席 → HALT + 路由 diy-prd）
    def test_gate_refuses_missing_prd(self):
        self.write_doc("stories.yaml", STORIES)
        self.write_doc("test-plan.yaml", TEST_PLAN)
        r = self.collect()
        self.assertEqual(r.returncode, 1, r.stdout)
        data = json.loads(r.stdout)
        self.assertEqual(self.codes(data), ["MISSING_FILE"])
        self.assertIn("prd.yaml", data["violations"][0]["where"])
        self.assertIn("diy-prd", data["gate"]["route"])

    # trace: 验收 #4（ID 链接入：--story 未知 → UNKNOWN_ID 拒绝）
    def test_gate_refuses_unknown_story(self):
        self.write_trio()
        r = self.collect("--story", "S-9")
        self.assertEqual(r.returncode, 1, r.stdout)
        data = json.loads(r.stdout)
        self.assertEqual(self.codes(data), ["UNKNOWN_ID"])
        self.assertIn("S-9", data["violations"][0]["msg"])


class CollectTests(EngineCase):

    # trace: 任务书 §4 collect（矩阵 join：AC × TC × 证据台账 + priority 推导 + 统计）
    def test_collect_matrix_join(self):
        self.write_trio()
        r = self.collect()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertTrue(data["ok"], data)
        items = {it["ref"]: it for it in data["items"]}
        self.assertEqual(sorted(items), ["AC-1.1", "AC-1.2", "AC-1.3", "AC-2.1"])
        self.assertEqual(items["AC-1.1"]["story"], "S-1")
        self.assertEqual(items["AC-1.1"]["priority"], "P0", "必须 FR → P0")
        self.assertEqual(items["AC-1.2"]["priority"], "P1", "应该 FR → P1")
        self.assertEqual(items["AC-1.3"]["priority"], "P2", "无 FR refs → P2")
        self.assertEqual(items["AC-2.1"]["priority"], "P2", "可选 FR → P2")
        self.assertEqual(items["AC-1.1"]["coverage"], "FULL",
                         "≥2 类 type 全验证 → FULL")
        self.assertEqual(items["AC-1.1"]["tests"], ["TC-1.1.1", "TC-1.1.2"])
        self.assertEqual(items["AC-1.2"]["coverage"], "PARTIAL",
                         "失败 的 TC 不计，剩下已验证一条 → PARTIAL")
        self.assertEqual(items["AC-1.2"]["tests"], ["TC-1.2.2"])
        self.assertEqual(items["AC-1.3"]["coverage"], "NONE", "待办不计 → NONE")
        self.assertEqual(items["AC-2.1"]["coverage"], "NONE", "无 TC → NONE")
        self.assertEqual(data["coverage"]["totals"],
                         {"covered": 1, "total": 4, "pct": 25})
        self.assertEqual(data["coverage"]["by_level"],
                         {"单元": 2, "集成": 1, "端到端": 0})
        self.assertEqual(data["coverage"]["p0"]["pct"], 100)
        self.assertEqual(data["coverage"]["p1"]["pct"], 0)
        self.assertEqual(data["scope"], "story")
        self.assertEqual(data["stories"], ["S-1", "S-2"])

    # trace: 任务书 §4 覆盖判定表（① 失败胜；③ 通过无台账 → 已验证 + warning）
    def test_collect_coverage_table(self):
        self.write_trio()
        data = json.loads(self.collect().stdout)
        warns = self.codes(data, "warnings")
        self.assertIn("EVIDENCE_MISSING", warns,
                      "通过但无红绿台账须出 warning：%s" % data["warnings"])
        self.assertIn("TC-1.2.2", data["coverage"]["by_tc"]["missing_evidence"])
        self.assertNotIn("TC-1.2.1", data["coverage"]["by_tc"]["verified"],
                         "失败胜：即使留有 green 记录也不计已验证")
        self.assertIn("TC-1.2.1", data["coverage"]["by_tc"]["blocked"])
        self.assertIn("TC-1.3.1", data["coverage"]["by_tc"]["pending"])
        self.assertIn("EMPTY_FIELD", warns, "无 FR refs 的 AC 须 warning")

    # trace: 任务书 §4 collect（软指标六项口径：分子/分母/actual/estimated）
    def test_collect_soft_metrics(self):
        self.write_trio()
        data = json.loads(self.collect().stdout)
        m = data["soft_metrics"]
        self.assertEqual(sorted(m), ["boundary_coverage", "business_rule_coverage",
                                     "effective_case_ratio", "id_chain_resolvable",
                                     "negative_scenario_coverage", "p0_depth_full"])
        self.assertEqual(m["boundary_coverage"]["numerator"], 2,
                         "判定表 ③（通过无台账）计入已验证：AC-1.1 与 AC-1.2")
        self.assertEqual(m["boundary_coverage"]["denominator"], 4)
        self.assertEqual(m["business_rule_coverage"]["actual"], "0%",
                         "决策表 的 TC 失败 → 不计覆盖")
        self.assertEqual(m["negative_scenario_coverage"]["actual"], "25%")
        self.assertEqual(m["negative_scenario_coverage"]["target"], ">=90%")
        self.assertEqual(m["p0_depth_full"]["actual"], "100%",
                         "P0 唯一 AC：≥2 类 type + 含 错误猜测")
        self.assertEqual(m["effective_case_ratio"]["actual"], "100%")
        self.assertEqual(m["id_chain_resolvable"]["actual"], "100%")
        self.assertEqual(m["id_chain_resolvable"]["target"], "100%")
        for value in m.values():
            self.assertFalse(value.get("estimated"), value)

    # trace: 任务书 §4 collect（缺口清单：none / partial / blocker / heuristic）
    def test_collect_gap_inventory(self):
        self.write_trio()
        data = json.loads(self.collect().stdout)
        kinds = {}
        for gap in data["gaps"]:
            kinds.setdefault(gap["ref"], set()).add(gap["kind"])
        self.assertIn("none", kinds["AC-1.3"])
        self.assertIn("none", kinds["AC-2.1"])
        self.assertIn("partial", kinds["AC-1.2"])
        self.assertIn("blocker", kinds["TC-1.2.1"])
        self.assertTrue(any("heuristic" in v for v in kinds.values()),
                        "盲区候选须进缺口清单：%s" % data["gaps"])

    # trace: 任务书 §2.3（委派 diyc：上游违规进 diyc.violations，不当失败吞掉）
    def test_collect_delegates_diyc_violations(self):
        plan = copy.deepcopy(TEST_PLAN)
        plan["test_cases"][0]["kill_target"] = ""
        self.write_trio(plan=plan)
        r = self.collect()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertTrue(data["ok"], "diyc 上游违规不是本引擎的失败")
        self.assertTrue(data["diyc"]["available"])
        self.assertEqual(data["diyc"]["checked"], ["test-plan"])
        self.assertIn("EMPTY_FIELD", self.codes(data["diyc"], "violations"))

    # trace: 任务书 §2.3（diyc 缺席 → TOOL_MISSING 结构化降级，不崩）
    def test_collect_degrades_when_diyc_missing(self):
        self.write_trio()
        sys.path.insert(0, os.path.join(SKILL_DIR, "scripts"))
        old_bytecode = sys.dont_write_bytecode
        sys.dont_write_bytecode = True
        try:
            import gate
            import gate_lib
        finally:
            sys.dont_write_bytecode = old_bytecode
            sys.path.pop(0)
        original = gate_lib.diyc_script_path
        gate_lib.diyc_script_path = lambda: os.path.join(self.root, "no-such-diyc.py")
        try:
            args = gate.build_parser().parse_args(
                ["collect", "--project-root", self.root,
                 "--output-dir", self.out, "--json"])
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = args.func(args)
        finally:
            gate_lib.diyc_script_path = original
        self.assertEqual(rc, 0, buf.getvalue())
        data = json.loads(buf.getvalue())
        self.assertTrue(data["ok"])
        self.assertFalse(data["diyc"]["available"])
        self.assertIn("TOOL_MISSING", self.codes(data, "warnings"))

    # trace: 任务书 §4 mutation 面（缺席 n/a + warning；在场取全部 run 的最小 score）
    def test_collect_mutation_surface(self):
        self.write_trio()
        data = json.loads(self.collect().stdout)
        self.assertFalse(data["mutation"]["present"])
        self.assertIsNone(data["mutation"]["score"])
        self.assertIn("MISSING_FILE", self.codes(data, "warnings"))
        self.write_doc("mutation-report.yaml", {
            "project": {"name": "mini", "created": "2026-01-01",
                        "updated": "2026-01-02"},
            "runs": [{"date": "2026-01-02", "task": "S-1", "scope": "x",
                      "killed": 9, "total": 10, "score": 90,
                      "survivors": [], "equivalents": []},
                     {"date": "2026-01-02", "task": "S-2", "scope": "y",
                      "killed": 7, "total": 10, "score": 70,
                      "survivors": [], "equivalents": []}],
            "revisions": [],
        })
        data = json.loads(self.collect().stdout)
        self.assertTrue(data["mutation"]["present"])
        self.assertEqual(data["mutation"]["runs"], 2)
        self.assertEqual(data["mutation"]["score"], 70, "多 run 聚合取最小值")
        self.assertEqual(data["mutation"]["target"], ">=90%")

    # trace: G-1 证据时效（台账 red/green 时间戳 >7 天 → EVIDENCE_STALE；run 日期同口径）
    def test_collect_evidence_staleness(self):
        today = date.today()
        fresh = today.isoformat()
        old = (today - timedelta(days=30)).isoformat()
        sprint = copy.deepcopy(SPRINT)
        sprint["tasks"][0]["evidence"] = [
            {"tc": "TC-1.1.1", "red": "%s 22:10 pytest: 1 failed" % old,
             "green": "%s 22:18 pytest: 3 passed" % old},
            {"tc": "TC-1.1.2", "red": "%s 22:10 pytest: 1 failed" % fresh,
             "green": "%s 22:18 pytest: 3 passed" % fresh},
        ]
        self.write_trio(sprint=sprint)
        data = json.loads(self.collect().stdout)
        stale = [item for item in data["warnings"]
                 if item["code"] == "EVIDENCE_STALE"]
        self.assertEqual(len(stale), 1, stale)
        self.assertIn("TC-1.1.1", stale[0]["msg"])
        self.assertIn("30 天前", stale[0]["msg"])
        self.assertEqual(data["counts"]["stale_evidence"], 1)
        self.write_doc("mutation-report.yaml", {
            "project": {"name": "mini", "created": "2026-01-01",
                        "updated": "2026-01-02"},
            "runs": [{"date": old, "task": "S-1", "score": 95,
                      "survivors": [], "equivalents": []}],
            "revisions": [],
        })
        data = json.loads(self.collect().stdout)
        runs = [item for item in data["warnings"]
                if item["code"] == "EVIDENCE_STALE"
                and "mutation-report.yaml" in item["where"]]
        self.assertEqual(len(runs), 1, data["warnings"])
        self.assertEqual(data["counts"]["stale_evidence"], 2)

    # trace: G-3 / G-4 输入面（合规五标准清单 + 跨域合成规则进 `nfr_inputs`，供 steps/04 走查）
    def test_collect_nfr_inputs_surfaces(self):
        self.write_trio()
        data = json.loads(self.collect().stdout)
        nfr = data["nfr_inputs"]
        self.assertEqual(nfr["compliance_standards"],
                         ["SOC2", "GDPR", "HIPAA", "PCI-DSS", "ISO27001"])
        self.assertEqual([rule["pair"] for rule in nfr["cross_domain_rules"]],
                         [["可靠性", "可维护性"],
                          ["安全", "可靠性"]])
        self.assertEqual(nfr["cross_domain_rules"][1]["impact"], "HIGH")
        self.assertEqual(nfr["cross_domain_rules"][1]["trigger"]["安全"],
                         ["FAIL"])

    # trace: G-2 跨层重复覆盖候选（同一 technique + 同一 kill_target 跨 ≥2 层）
    def test_collect_duplicate_coverage(self):
        self.write_trio()
        data = json.loads(self.collect().stdout)
        self.assertEqual(data["coverage"]["duplicates"], [],
                         "基线夹具两 TC 技法不同，无候选")
        self.assertEqual(data["counts"]["duplicates"], 0)
        plan = copy.deepcopy(TEST_PLAN)
        plan["test_cases"].append(
            {"id": "TC-1.1.3", "title": "同目标跨层", "ac": "AC-1.1",
             "type": "集成", "priority": "P0", "technique": "边界",
             "kill_target": "off-by-one", "status": "通过", "steps": ["跑"]})
        self.write_trio(plan=plan)
        data = json.loads(self.collect().stdout)
        rows = data["coverage"]["duplicates"]
        self.assertEqual(len(rows), 1, rows)
        self.assertEqual(rows[0]["ref"], "AC-1.1")
        self.assertEqual(rows[0]["priority"], "P0")
        self.assertEqual(rows[0]["levels"], ["单元", "集成"], "层级按码点排序")
        self.assertEqual(rows[0]["tests"], ["TC-1.1.1", "TC-1.1.3"])
        self.assertEqual(data["counts"]["duplicates"], 1)


class CheckTests(EngineCase):

    # trace: 任务书 §4 / §2.5（合法记录 --final exit 0 唯一放行）
    def test_check_final_legal_record_passes(self):
        self.write_check_fixtures()
        r = self.check("--final")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertTrue(data["ok"], data["violations"])
        self.assertEqual(data["counts"]["gates"], 1)
        self.assertEqual(data["counts"]["by_decision"], {"PASS": 1})
        self.assertIn("MISSING_FILE", self.codes(data, "warnings"),
                      "mutation-report 缺席走过渡期口径（warning，不拒绝）")

    # trace: 任务书 §4 check（硬判据 失败 而 decision PASS → 不自洽 + actual 陈旧）
    def test_check_decision_inconsistent(self):
        self.write_check_fixtures()
        self.mutate_gate(lambda d: self._flip_hard(d, "p0_coverage",
                                                   actual="0%", result="失败"))
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        codes = self.codes(json.loads(r.stdout))
        self.assertIn("DECISION_INCONSISTENT", codes)
        self.assertIn("CRITERION_STALE", codes)

    # trace: 任务书 §4 check（软判据 失败 → 门至少 CONCERNS）
    def test_check_soft_fail_but_gate_pass(self):
        self.write_check_fixtures()
        self.mutate_gate(lambda d: self._flip_soft(d, "boundary_coverage",
                                                   actual="50%", result="失败"))
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("DECISION_INCONSISTENT", self.codes(json.loads(r.stdout)))

    # trace: 任务书 §4 check（NFR 域 CONCERNS 而门 PASS → 违例）
    def test_check_domain_concerns_but_gate_pass(self):
        self.write_check_fixtures()
        self.mutate_gate(lambda d: self._set_domain(d, "安全", "CONCERNS",
                                                    risk="MEDIUM"))
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("DECISION_INCONSISTENT", self.codes(json.loads(r.stdout)))

    # trace: 任务书 §4 check（overlay：合成 且 confidence≠高 → 至少 CONCERNS）
    def test_check_synthetic_overlay(self):
        self.write_check_fixtures()
        self.mutate_gate(lambda d: d["gates"][0]["oracle"].update(
            {"source": "合成", "confidence": "中",
             "inferred": ["登录旅程"]}))
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("DECISION_INCONSISTENT", self.codes(json.loads(r.stdout)))

    # trace: 任务书 §4 check（NFR critical FAIL 而门 PASS → 违例且不可豁免）
    def test_check_nfr_critical_fail_but_gate_pass(self):
        self.write_check_fixtures()

        def mutate(d):
            self._set_domain(d, "性能", "FAIL", risk="HIGH")
            self._flip_hard(d, "nfr_critical", actual=1, result="失败")
        self.mutate_gate(mutate)
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("DECISION_INCONSISTENT", self.codes(json.loads(r.stdout)))

    # trace: 任务书 §4 check（判据 actual 与重算不符 → CRITERION_STALE）
    def test_check_criterion_stale(self):
        self.write_check_fixtures()
        self.mutate_gate(lambda d: self._flip_hard(d, "nfr_critical",
                                                   actual=2, result="通过"))
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("CRITERION_STALE", self.codes(json.loads(r.stdout)))

    # trace: 任务书 §4 / nfr-status-definitions（UNKNOWN 阈值域 PASS → 违例）
    def test_check_unknown_threshold_pass(self):
        self.write_check_fixtures()

        def mutate(d):
            d["gates"][0]["nfr"]["domains"][0]["thresholds"][0].update(
                {"target": "UNKNOWN", "measured": ""})
        self.mutate_gate(mutate)
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("UNKNOWN_THRESHOLD_PASS", self.codes(json.loads(r.stdout)))

    # trace: 任务书 §4 check（阈值 source 强制记出处 → 猜的阈值拒收）
    def test_check_unsourced_threshold_refused(self):
        self.write_check_fixtures()

        def mutate(d):
            d["gates"][0]["nfr"]["domains"][0]["thresholds"][0]["source"] = "行业惯例"
        self.mutate_gate(mutate)
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("THRESHOLD_UNSOURCED", self.codes(json.loads(r.stdout)))

    # trace: 任务书 §4 check（waiver 8 键契约；安全域不可豁免）
    def test_check_waiver_contract(self):
        self.write_check_fixtures()
        base = {"ref": "AC-1.2", "approved_by": "张三", "date": "2026-09-16",
                "reason": "已知", "expires": "2026-12-31", "monitoring": "周报",
                "fix_owner": "李四", "fix_target": "S-2"}
        incomplete = dict(base)
        del incomplete["expires"]
        del incomplete["fix_owner"]
        self.mutate_gate(lambda d: d["gates"][0]["gate"]["waivers"].append(incomplete))
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("WAIVER_INCOMPLETE", self.codes(json.loads(r.stdout)))
        security = dict(base, ref="安全")
        self.mutate_gate(lambda d: d["gates"][0]["gate"]["waivers"].append(security))
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("WAIVER_INAPPLICABLE", self.codes(json.loads(r.stdout)))

    # trace: 任务书 §4 check（豁免后 nfr_critical 重算：FAIL 域数 − 已豁免域数）
    def test_check_waiver_reduces_nfr_critical(self):
        self.write_check_fixtures()

        def mutate(d):
            self._set_domain(d, "性能", "FAIL", risk="HIGH")
            waiver = {"ref": "性能", "approved_by": "张三",
                      "date": "2026-09-16", "reason": "已知",
                      "expires": "2026-12-31", "monitoring": "周报",
                      "fix_owner": "李四", "fix_target": "S-2"}
            d["gates"][0]["gate"]["waivers"].append(waiver)
            d["gates"][0]["gate"]["basis"] = "性能域 FAIL 经用户豁免。"
        self.mutate_gate(mutate)
        r = self.check("--final")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    # trace: 任务书 §4 check（引用解析 + totals / by_level 重算）
    def test_check_reference_and_totals(self):
        self.write_check_fixtures()
        self.mutate_gate(lambda d: d["gates"][0]["coverage"]["items"][1].update(
            {"ref": "AC-9.9"}))
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("UNKNOWN_ID", self.codes(json.loads(r.stdout)))
        self.write_check_fixtures()
        self.mutate_gate(lambda d: d["gates"][0]["coverage"].update(
            {"totals": {"covered": 1, "total": 2, "pct": 50}}))
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("SET_MISMATCH", self.codes(json.loads(r.stdout)))
        self.write_check_fixtures()
        self.mutate_gate(lambda d: d["gates"][0]["coverage"].update(
            {"by_level": {"单元": 9, "集成": 9, "端到端": 9}}))
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("SET_MISMATCH", self.codes(json.loads(r.stdout)))

    # trace: 任务书 §4 check（--final 附加：零假设 / basis 非空 / 两组判据齐）
    def test_check_final_duties(self):
        self.write_check_fixtures()

        def mutate(d):
            gate = d["gates"][0]["gate"]
            gate["basis"] = ""
            gate["hard_criteria"] = [c for c in gate["hard_criteria"]
                                     if c["name"] != "p0_uncovered"]
            d["gates"][0]["note"] = "[假设] 待确认"
        self.mutate_gate(mutate)
        r = self.check("--final")
        self.assertEqual(r.returncode, 1, r.stdout)
        codes = self.codes(json.loads(r.stdout))
        self.assertIn("ASSUMPTION_PRESENT", codes)
        self.assertIn("EMPTY_FIELD", codes)

    # trace: 任务书 §4（草稿记录：decision 未定不判不自洽，落 warning）
    def test_check_draft_record_is_tolerated(self):
        self.write_check_fixtures()

        def mutate(d):
            record = d["gates"][0]
            record["status"] = "草稿"
            record["gate"]["decision"] = ""
            record["gate"]["basis"] = ""
        self.mutate_gate(mutate)
        r = self.check()
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("PENDING_DECISION", self.codes(json.loads(r.stdout), "warnings"))

    # trace: 任务书 §4 check（estimated 项无 algorithm → 违例）
    def test_check_estimated_requires_algorithm(self):
        self.write_check_fixtures()

        def mutate(d):
            for c in d["gates"][0]["gate"]["soft_criteria"]:
                if c["name"] == "boundary_coverage":
                    c["estimated"] = True
        self.mutate_gate(mutate)
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("EMPTY_FIELD", self.codes(json.loads(r.stdout)))

    # trace: 任务书 §4 check（枚举越界 / 记录 ID 重复）
    def test_check_enum_and_duplicate(self):
        self.write_check_fixtures()
        self.mutate_gate(lambda d: d["gates"][0].update({"scope": "epic"}))
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ENUM_INVALID", self.codes(json.loads(r.stdout)))
        self.write_check_fixtures()
        self.mutate_gate(lambda d: d["gates"].append(copy.deepcopy(d["gates"][0])))
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("DUPLICATE_ID", self.codes(json.loads(r.stdout)))

    # trace: 任务书 §2.5（缺文件 → 结构化 MISSING_FILE，不崩）
    def test_check_missing_file_is_structured(self):
        r = self.check("--final")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertNotIn("Traceback", r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual(self.codes(data), ["MISSING_FILE"])
        self.assertEqual(data["counts"]["gates"], 0)

    # trace: 任务书 §2.2（--output-dir 必填 → 缺省即用法错误 rc=2）
    def test_output_dir_is_mandatory(self):
        r = run_engine(["collect", "--project-root", self.root, "--json"])
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        r2 = run_engine(["check", "--project-root", self.root, "--json"])
        self.assertEqual(r2.returncode, 2, r2.stdout + r2.stderr)

    # trace: 任务书 §2.2（回执共同键；本批无 instance 键）
    def test_receipt_common_keys(self):
        self.write_trio()
        for r in (self.collect(), self.check()):
            data = json.loads(r.stdout)
            for key in ("ok", "command", "project_root", "output_dir",
                        "violations", "warnings", "counts"):
                self.assertIn(key, data, key)
            self.assertNotIn("instance", data, "本批回执无 instance 键")
            self.assertNotIn("\\", data["output_dir"], "output_dir 正斜杠")

    # trace: G-3 合规五标准（第五个走查维度）：记账完整 + 聚合 FAIL>PARTIAL>PASS
    def test_check_compliance_recording(self):
        self.write_check_fixtures()
        r = self.check("--final")
        self.assertEqual(r.returncode, 0, "五标准齐 → 放行：%s" % r.stdout)

        def drop_hipaa(data):
            domain = data["gates"][0]["nfr"]["domains"][0]
            domain["findings"] = [line for line in domain["findings"]
                                  if not line.startswith("HIPAA")]

        self.mutate_gate(drop_hipaa)
        r = self.check("--final")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("COMPLIANCE_UNRECORDED", self.codes(json.loads(r.stdout)))

        def conflicting(data):
            domain = data["gates"][0]["nfr"]["domains"][0]
            domain["findings"] = (
                [line for line in domain["findings"]
                 if not line.startswith("GDPR")]
                + ["GDPR: PASS — 无个人数据", "GDPR@安全: PARTIAL — 缺删除路径"])

        self.mutate_gate(conflicting)
        r = self.check("--final")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("COMPLIANCE_AGGREGATE_MISMATCH",
                      self.codes(json.loads(r.stdout)))

        def malformed(data):
            domain = data["gates"][0]["nfr"]["domains"][0]
            domain["findings"] = ([line for line in domain["findings"]
                                   if not line.startswith("SOC2")]
                                  + ["SOC2 未评估"])

        self.mutate_gate(malformed)
        r = self.check("--final")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("COMPLIANCE_UNRECORDED", self.codes(json.loads(r.stdout)))

        # 记账义务是 --final 义务：草稿记录不催
        self.write_check_fixtures()
        self.mutate_gate(lambda d: d["gates"][0]["nfr"]["domains"][0].update(
            {"findings": []}))
        r = self.check()
        self.assertNotIn("COMPLIANCE_UNRECORDED", self.codes(json.loads(r.stdout)))

    # trace: G-4 跨域风险合成（候选命中 → 须落 recommendations / findings；不成立也要写明）
    def test_check_cross_domain_synthesis(self):
        self.write_check_fixtures()

        def concerns(data):
            record = data["gates"][0]
            for domain in record["nfr"]["domains"]:
                if domain["name"] in ("可靠性", "可维护性"):
                    domain["status"] = "CONCERNS"
            record["nfr"]["overall_risk"] = "MEDIUM"
            record["gate"]["decision"] = "CONCERNS"

        self.mutate_gate(concerns)
        r = self.check("--final")
        self.assertEqual(r.returncode, 1, r.stdout)
        messages = [item["msg"] for item in json.loads(r.stdout)["violations"]
                    if item["code"] == "CROSS_DOMAIN_UNRECORDED"]
        self.assertTrue(any("可靠性×可维护性" in msg
                            for msg in messages), messages)

        def with_note(data):
            concerns(data)
            data["gates"][0]["gate"]["recommendations"].append(
                "可靠性×可维护性: 成立——低覆盖会掩盖可靠性回归，先补观测")

        self.mutate_gate(with_note)
        r = self.check("--final")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

        # 另一组：安全 = FAIL 且 可靠性 ≠ PASS
        def security_pair(data):
            record = data["gates"][0]
            for domain in record["nfr"]["domains"]:
                if domain["name"] == "安全":
                    domain["status"] = "FAIL"
                elif domain["name"] == "可靠性":
                    domain["status"] = "CONCERNS"
            record["nfr"]["overall_risk"] = "HIGH"
            record["gate"]["decision"] = "FAIL"
            self._flip_hard(data, "nfr_critical", actual=1, result="失败")

        self.mutate_gate(security_pair)
        r = self.check("--final")
        self.assertEqual(r.returncode, 1, r.stdout)
        messages = [item["msg"] for item in json.loads(r.stdout)["violations"]
                    if item["code"] == "CROSS_DOMAIN_UNRECORDED"]
        self.assertTrue(any("安全×可靠性" in msg for msg in messages),
                        messages)

    # 夹具微操作（结构性改动，不靠字符串补丁）
    def _flip_hard(self, data, name, actual, result):
        for c in data["gates"][0]["gate"]["hard_criteria"]:
            if c["name"] == name:
                c["actual"] = actual
                c["result"] = result

    def _flip_soft(self, data, name, actual, result):
        for c in data["gates"][0]["gate"]["soft_criteria"]:
            if c["name"] == name:
                c["actual"] = actual
                c["result"] = result

    def _set_domain(self, data, name, status, risk):
        for domain in data["gates"][0]["nfr"]["domains"]:
            if domain["name"] == name:
                domain["status"] = status
                data["gates"][0]["nfr"]["overall_risk"] = risk


class StepObligationTests(unittest.TestCase):
    """G-1..G-4 的走查义务在 `steps/` 的落点（源 checklist 条目 → diy 明文义务）。"""

    def read_step(self, name):
        path = os.path.join(SKILL_DIR, "steps", name)
        if not os.path.isfile(path):
            self.fail("steps/%s 缺失" % name)
        with io.open(path, encoding="utf-8") as fh:
            return fh.read()

    # trace: G-1（源 trace checklist「Evidence freshness validated」（>7 days））
    def test_g1_freshness_obligation(self):
        text = self.read_step("03-matrix-gaps.md")
        self.assertIn("EVIDENCE_STALE", text)
        self.assertIn("EVIDENCE_TTL_DAYS", text)
        self.assertIn("gate.basis", text, "陈旧证据的处置须落 basis（源：Decision document "
                                          "notes any stale evidence used）")

    # trace: G-2（源 trace checklist「Duplicate Coverage Detection」）
    def test_g2_duplicate_obligation(self):
        text = self.read_step("03-matrix-gaps.md")
        self.assertIn("coverage.duplicates", text)
        self.assertIn("重复覆盖", text)
        self.assertIn("gate.recommendations", text, "合并建议须落 recommendations")

    # trace: G-3（源 nfr step-04a「Common compliance standards」+ step-04e 聚合）
    def test_g3_compliance_obligation(self):
        text = self.read_step("04-nfr.md")
        for standard in ("SOC2", "GDPR", "HIPAA", "PCI-DSS", "ISO27001"):
            self.assertIn(standard, text)
        self.assertIn("FAIL > PARTIAL > PASS", text)
        self.assertIn("COMPLIANCE_AGGREGATE_MISMATCH", text)

    # trace: G-4（源 nfr step-04e「Identify Cross-Domain Risks」两条规则）
    def test_g4_cross_domain_obligation(self):
        text = self.read_step("04-nfr.md")
        self.assertIn("可靠性×可维护性", text)
        self.assertIn("安全×可靠性", text)
        self.assertIn("CROSS_DOMAIN_UNRECORDED", text)


class SkillContractTests(unittest.TestCase):
    """用例：SKILL.md 契约冒烟（母本中文定稿逐字 + 终门句指向本技能引擎）。"""

    def read_skill(self):
        if not os.path.isfile(SKILL_MD):
            self.skipTest("SKILL.md 尚未交付")
        with io.open(SKILL_MD, encoding="utf-8") as fh:
            return fh.read()

    # trace: 任务书 §2.1 / 母本 §1（实例解析句中文定稿逐字）
    def test_instance_sentence_is_mother_text_verbatim(self):
        self.assertIn(INSTANCE_ZH, self.read_skill(),
                      "SKILL.md 缺母本 §1 中文定稿（或未逐字复制）")

    # trace: 任务书 §2.1 / 母本 §2（写作纪律块中文定稿逐字）
    def test_writing_discipline_block_is_mother_text_verbatim(self):
        self.assertIn(DISCIPLINE_ZH, self.read_skill(), "缺母本 §2 中文定稿")

    # trace: 验收 #12（b 终门 / a 实例委托 / d 语言绑定 / e 写权边界）
    def test_engine_wiring(self):
        skill = self.read_skill()
        self.assertIn("gate.py", skill)
        self.assertIn("check --final", skill)
        self.assertIn("--json", skill)
        self.assertIn("collect", skill)
        self.assertIn("diyc.py", skill)
        self.assertIn("test-gate.yaml", skill)
        self.assertIn("TG-", skill, "Schema 段缺稳定 ID 前缀")
        for peer in ("diy-test-design", "diy-epics-stories", "diy-prd",
                     "diy-augment", "diy-sprint", "diy-correct-course"):
            self.assertIn(peer, skill, "缺路由/证据面引用：%s" % peer)
        for banned in ("bmad-testarch", "bmad-help", "Master Test Architect"):
            self.assertNotIn(banned, skill, "不得残留 BMAD 引用：%s" % banned)

    # trace: 验收 #9 / #11（读取纪律 + 渲染静默锚串）
    def test_read_discipline_and_render_silence(self):
        skill = self.read_skill()
        self.assertIn("读取纪律：预载预算 = 本文件", skill)
        self.assertIn("渲染是静默旁路——只写调用命令", skill)
        self.assertIn("viewer.py", skill)


if __name__ == "__main__":
    unittest.main()
