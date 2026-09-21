# -*- coding: utf-8 -*-
"""diy-cis-method 确定性引擎 e2e 测试（B6 批 W3；任务书 §2.6 十三类用例逐条对应）。

覆盖（任务书 §2.6 ①–⑬）：
- ① 门禁：`init` 无 `--method` → exit 2（argparse 用法错误）；`--method` 非法 → ENUM_INVALID
     exit 1；`--topic` 空串 → EMPTY_FIELD exit 1；`--output-dir` 缺席 → exit 2；`--instance` 不存在
- ② `init` 合法 exit 0 + 骨架结构（CM-001 / status: 草稿 / current_step: 1）且骨架即过 check
- ③ `init` 续号递增（CM-002）不重号；损坏产物拒绝且零写入
- ④ `list` 只回六字段、`--method` 过滤生效；`show` 单条全文；未知 ID → UNKNOWN_ID
- ⑤ `check --final` 检出：STATUS_MISMATCH / EMPTY_FIELD（where 含键名）/ ENUM_INVALID（method
     与 current_step 越界）
- ⑥ 问题求解分支 `current_step: 8` + `已完成` 放行（源侧 step 9 optional 例外）；该例外不推广
- ⑦ 可达集：创新策略默认 25 < `--all` 30；叙事默认 25 == `--all` 25；设计思维 15 < 30；
     问题求解 30 == 30（夹具 CSV 驱动 + 真实 CSV 在场时的交叉核对）
- ⑧ `methods --category` 非法类 → ENUM_INVALID；库缺列/列名不符 → UNPARSABLE_YAML；
     `--method` 缺席 → EMPTY_FIELD；`--random N` 超界 → 全给 + warning（不报错）
- ⑨ 回执键完整性（`instance` 键在位恒 null / `warnings` 与 `violations` 同形 / `where` 正斜杠）；
     只读子命令**不含** `updated`，`init` 含
- ⑩ SKILL.md 契约冒烟（母本 §1 中文定稿逐字 + 终门句指向本引擎 + 产物路径声明句在场）
- ⑪ 未解析 `{...}` 令牌 → TOKEN_UNRESOLVED（本批唯一新增码）；白名单令牌不报
- ⑫ 空态：`sessions: []` + `--final` → EMPTY_FIELD exit 1
- ⑬ ID 唯一性：手工构造重复 `CM-001` → DUPLICATE_ID

另含两条引擎内表核对（§5 回报必答 ②/③ 的机械证据）：把引擎模块直接导入，逐条比对
34 键必填表（含注入项排除）与可达集映射（23 个冻结中文类名逐字）。

夹具全部落 tempdir 自建；不读写本仓库真实 diy-output；不依赖本机 git 状态。
方法库夹具：把引擎复制进 temp 技能根（`scripts/cis_method.py` + `cis-methods.csv`），
使 `Path(__file__).parent.parent` 的自带库解析在夹具上生效（真库在场时另跑交叉核对）。
运行：cd diy-coder && python -m unittest discover -s tests -p "test_cis_method.py" -v
"""
import csv
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.join(HERE, "..", "skills", "diy-cis-method", "scripts", "cis_method.py")
SKILL_MD = os.path.join(HERE, "..", "skills", "diy-cis-method", "SKILL.md")
REAL_CSV = os.path.join(HERE, "..", "skills", "diy-cis-method", "cis-methods.csv")
NL = chr(10)

# ---------------------------------------------------------------- 独立内表（非实现拷贝）
# 源侧取数位置：`.claude/skills/bmad-cis-*/SKILL.md` 的 <step n="k"> 内首个非注入
# <template-output> 标签（多键形态按逗号切分后取首键）。此处**独立手录**，与引擎内表
# 双向核对——本批最易双实现漂移的一处（任务书 §5 回报必答 ②）。
INJECTION_KEYS = ("date", "user_name", "agent_role", "agent_name")
SOURCE_FIRST_KEYS = {
    "创新策略": ["company_name", "market_landscape", "current_business_model",
                 "disruption_vectors", "innovation_initiatives", "option_a_name",
                 "recommended_strategy", "phase_1", "leading_indicators"],
    "问题求解": ["problem_title", "problem_boundaries", "root_cause_analysis",
                 "driving_forces", "solution_methods", "evaluation_criteria",
                 "implementation_approach", "success_metrics", "key_learnings"],
    "设计思维": ["design_challenge", "user_insights", "pov_statement", "ideation_methods",
                 "prototype_approach", "testing_plan", "refinements"],
    "叙事": ["story_purpose", "story_type", "story_beats", "emotional_arc", "opening_hook",
             "complete_story", "short_version", "best_channels", "resolution"],
}
BRANCH_STEPS = {"创新策略": 9, "问题求解": 9, "设计思维": 7, "叙事": 10}
# §0 裁定 5(d) 的 23 个冻结中文类名（逐字）
FROZEN_CATEGORIES = {
    "创新策略": ["市场分析", "商业模式", "颠覆", "战略", "价值链", "技术"],
    "问题求解": ["诊断", "分析", "综合", "评估", "实施", "创意"],
    "设计思维": ["共情", "定义", "构思", "原型", "测试", "落地"],
    "叙事": ["转变", "战略", "说服", "分析", "情感"],
}
# §0 裁定 5(e)：默认可达集 = 源侧工作流实际引用的类（保真照搬；叙事为修后 = 全类）
REACHABLE_CATEGORIES = {
    "创新策略": ["市场分析", "商业模式", "颠覆", "战略", "价值链"],
    "问题求解": ["诊断", "分析", "综合", "评估", "实施", "创意"],
    "设计思维": ["共情", "构思", "原型"],
    "叙事": ["转变", "战略", "说服", "分析", "情感"],
}
REACHABLE_COUNTS = {"创新策略": 25, "问题求解": 30, "设计思维": 15, "叙事": 25}
ALL_COUNTS = {"创新策略": 30, "问题求解": 30, "设计思维": 30, "叙事": 25}
PER_CATEGORY = 5

# 母本 §1 中文定稿（suite-texts.md，逐字）
INSTANCE_ZH = ("实例解析（FR-4.5/D-9）由工具脚本执行：运行 "
               "`python \"{project-root}/.claude/skills/diy-tools/scripts/diyc.py\" "
               "resolve [--instance <name>] --json`，把回执里的 `output_dir` "
               "当作本次运行唯一的读写根目录。")

RECEIPT_KEYS = ("ok", "command", "project_root", "output_dir", "instance",
                "violations", "warnings", "counts")
V_SHAPE = ("code", "where", "msg")


def run_engine(engine_path, args):
    return subprocess.run([sys.executable, engine_path] + args,
                          capture_output=True, text=True, encoding="utf-8")


def fixture_csv():
    """夹具方法库：四分支 115 行（30/30/30/25），类名照 §0 裁定 5(d) 冻结表逐字。"""
    lines = ["method,category,name,slug,description,prompts"]
    for method in ("创新策略", "问题求解", "设计思维", "叙事"):
        for category in FROZEN_CATEGORIES[method]:
            for i in range(1, PER_CATEGORY + 1):
                slug = "%s-%d" % (category, i) if method == "叙事" else ""
                name = "%s方法%d" % (category, i)
                lines.append(",".join([method, category, name, slug,
                                       "%s 的描述" % name, "引导问句1|引导问句2"]))
    return NL.join(lines) + NL


def branch_keys(method):
    """该分支 `deliverable` 合法键全集（源 template 占位符去注入项）——取测试侧独立表。"""
    return list(TEMPLATE_KEYS[method])


# 源 `template.md` 占位符（去注入项 date / user_name；叙事另去 agent_role / agent_name）
TEMPLATE_KEYS = {
    "创新策略": [
        "company_name", "strategic_focus", "current_situation", "strategic_challenge",
        "market_landscape", "competitive_dynamics", "market_opportunities", "market_insights",
        "current_business_model", "value_proposition", "revenue_cost_structure",
        "model_weaknesses", "disruption_vectors", "unmet_jobs", "technology_enablers",
        "strategic_whitespace", "innovation_initiatives", "business_model_innovation",
        "value_chain_opportunities", "partnership_opportunities",
        "option_a_name", "option_a_description", "option_a_pros", "option_a_cons",
        "option_b_name", "option_b_description", "option_b_pros", "option_b_cons",
        "option_c_name", "option_c_description", "option_c_pros", "option_c_cons",
        "recommended_strategy", "key_hypotheses", "success_factors",
        "phase_1", "phase_2", "phase_3",
        "leading_indicators", "lagging_indicators", "decision_gates",
        "key_risks", "risk_mitigation"],
    "问题求解": [
        "problem_title", "problem_category", "initial_problem", "refined_problem_statement",
        "problem_context", "success_criteria", "problem_boundaries", "root_cause_analysis",
        "contributing_factors", "system_dynamics", "driving_forces", "restraining_forces",
        "constraints", "key_insights", "solution_methods", "generated_solutions",
        "creative_alternatives", "evaluation_criteria", "solution_analysis",
        "recommended_solution", "solution_rationale", "implementation_approach",
        "action_steps", "timeline", "resources_needed", "responsible_parties",
        "success_metrics", "validation_plan", "risk_mitigation", "adjustment_triggers",
        "key_learnings", "what_worked", "what_to_avoid"],
    "设计思维": [
        "project_name", "design_challenge", "challenge_statement", "user_insights",
        "key_observations", "empathy_map", "pov_statement", "hmw_questions",
        "problem_insights", "ideation_methods", "generated_ideas", "top_concepts",
        "prototype_approach", "prototype_description", "features_to_test", "testing_plan",
        "user_feedback", "key_learnings", "refinements", "action_items", "success_metrics"],
    "叙事": [
        "story_type", "framework_name", "story_purpose", "target_audience", "opening_hook",
        "core_narrative", "story_beats", "emotional_arc", "resolution", "complete_story",
        "character_voice", "conflict_tension", "transformation", "emotional_touchpoints",
        "key_messages", "short_version", "medium_version", "extended_version",
        "best_channels", "audience_considerations", "tone_notes", "adaptation_suggestions",
        "refinement_opportunities", "additional_versions", "feedback_plan"],
}


def record_yaml(rid, method, status, step, deliverable_keys, extra_keys=(),
                open_questions="[]", topic="增长瓶颈"):
    """手搓单条记录产物（`deliverable` 键逐条给出，值非空且无 [假设] / 无花括号令牌）。"""
    lines = ["project:",
             "  name: mini",
             "  created: '2026-09-18'",
             "  updated: '2026-09-20'",
             "sessions:",
             "- id: %s" % rid,
             "  method: %s" % method,
             "  topic: %s" % topic,
             "  date: '2026-09-20'",
             "  status: %s" % status,
             "  current_step: %d" % step]
    keys = list(deliverable_keys) + list(extra_keys)
    if keys:
        lines.append("  deliverable:")
        for key in keys:
            lines.append("    %s: %s 的内容" % (key, key))
    else:
        lines.append("  deliverable: {}")
    lines.append("  open_questions: %s" % open_questions)
    lines.append("revisions: []")
    return NL.join(lines) + NL


def first_keys(method, count):
    """该分支前 count 个源步的必填首键（问题求解可选项例外时也用它）。"""
    return SOURCE_FIRST_KEYS[method][:count]


class EngineCase(unittest.TestCase):
    """tmp 项目根 + diy-output 目录的公共夹具。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="cis-")
        self.root = self.tmp.name
        self.out = os.path.join(self.root, "diy-output")
        os.makedirs(self.out, exist_ok=True)
        self.engine_path = ENGINE

    def tearDown(self):
        self.tmp.cleanup()

    # ---- 夹具与调用 helper ----

    def write(self, rel, content):
        path = os.path.join(self.root, rel)
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with io.open(path, "w", encoding="utf-8", newline="") as f:
            f.write(content)
        return path

    def read_text(self, rel):
        with io.open(os.path.join(self.root, rel), encoding="utf-8") as f:
            return f.read()

    def product(self, content):
        return self.write("diy-output/cis-method.yaml", content)

    def stage_engine(self, csv_text):
        """把引擎复制进 temp 技能根并落夹具方法库 → 返回该副本路径。"""
        scripts = os.path.join(self.root, "_skill", "diy-cis-method", "scripts")
        os.makedirs(scripts, exist_ok=True)
        shutil.copy2(ENGINE, os.path.join(scripts, "cis_method.py"))
        with io.open(os.path.join(self.root, "_skill", "diy-cis-method", "cis-methods.csv"),
                     "w", encoding="utf-8", newline="") as f:
            f.write(csv_text)
        self.engine_path = os.path.join(scripts, "cis_method.py")
        return self.engine_path

    def engine(self, *args):
        return run_engine(self.engine_path,
                          list(args) + ["--project-root", self.root,
                                        "--output-dir", self.out, "--json"])

    def raw(self, *args):
        """不带默认旗标的裸调用（门禁/签名用例）。"""
        return run_engine(self.engine_path, list(args))

    def init(self, *extra):
        return self.engine("init", *extra)

    def check(self, *extra):
        return self.engine("check", *extra)

    def results(self, proc):
        payload = json.loads(proc.stdout)
        return payload

    def codes(self, proc):
        return {x["code"] for x in self.results(proc)["violations"]}


class GateTests(EngineCase):
    """§2.6 ① 门禁（口径已订正：用法错误 exit 2 ≠ 枚举违规 exit 1）。"""

    # trace: 任务书 §2.6 ①（init 无 --method → exit 2；非法值 → ENUM_INVALID；空 topic → EMPTY_FIELD）
    def test_gate_missing_method_is_usage_error(self):
        r = self.raw("init", "--topic", "议题", "--project-root", self.root,
                     "--output-dir", self.out, "--json")
        self.assertEqual(r.returncode, 2, "缺 --method 须为 argparse 用法错误 exit 2：%s"
                         % (r.stdout + r.stderr))

    def test_gate_invalid_method_is_enum_invalid(self):
        r = self.init("--method", "设计思考", "--topic", "议题")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertEqual(self.codes(r), {"ENUM_INVALID"})

    def test_gate_empty_topic_is_empty_field(self):
        r = self.init("--method", "创新策略", "--topic", "  ")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertEqual(self.codes(r), {"EMPTY_FIELD"})

    def test_gate_output_dir_mandatory_and_no_instance_flag(self):
        # --output-dir 必填于写盘子命令（不设默认、不私读 diy-coder.yaml）
        r = self.raw("init", "--method", "创新策略", "--topic", "议题",
                     "--project-root", self.root, "--json")
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        # --instance 一律不做（裁定 9）：签名表内不得出现它
        r2 = self.engine("list", "--instance", "demo")
        self.assertEqual(r2.returncode, 2, "--instance 不得进签名表：%s" % (r2.stdout + r2.stderr))


class InitTests(EngineCase):
    """§2.6 ②③ init 铸号、骨架、拒绝损坏。"""

    # trace: 任务书 §2.6 ②（exit 0 + 骨架结构断言）
    def test_init_creates_record_and_skeleton_passes_check(self):
        r = self.init("--method", "创新策略", "--topic", "增长瓶颈")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = self.results(r)
        self.assertEqual(data["instance"], None)
        self.assertEqual(data["id"], "CM-001")
        self.assertIn("updated", data)
        text = self.read_text("diy-output/cis-method.yaml")
        self.assertIn("id: CM-001", text)
        self.assertIn("method: 创新策略", text)
        self.assertIn("status: 草稿", text)
        self.assertIn("current_step: 1", text)
        self.assertIn("deliverable: {}", text)
        self.assertIn("open_questions: []", text)
        self.assertIn("revisions: []", text)
        # 骨架即过 check（草稿期宽松：deliverable 可空）
        c = self.check()
        self.assertEqual(c.returncode, 0, c.stdout + c.stderr)
        self.assertEqual(self.results(c)["counts"]["sessions"], 1)
        # 产物顶层不设 status（定稿态挂记录级，裁定 3）
        self.assertNotIn(NL + "status:", text)

    # trace: 任务书 §2.6 ③（续号递增不重号 + 损坏产物拒绝且零写入）
    def test_init_increments_id_and_refuses_damaged_product(self):
        self.assertEqual(self.init("--method", "设计思维", "--topic", "A").returncode, 0)
        r2 = self.init("--method", "叙事", "--topic", "B")
        self.assertEqual(r2.returncode, 0, r2.stdout + r2.stderr)
        self.assertEqual(self.results(r2)["id"], "CM-002")
        text = self.read_text("diy-output/cis-method.yaml")
        self.assertEqual(text.count("id: CM-002"), 1)
        self.assertEqual(text.count("id: CM-001"), 1)
        # 损坏产物：拒绝 + 零写入
        self.product("sessions: [" + NL)
        before = self.read_text("diy-output/cis-method.yaml")
        bad = self.init("--method", "创新策略", "--topic", "C")
        self.assertEqual(bad.returncode, 1, bad.stdout)
        self.assertNotIn("Traceback", bad.stderr)
        self.assertEqual(self.codes(bad), {"UNPARSABLE_YAML"})
        self.assertEqual(self.read_text("diy-output/cis-method.yaml"), before,
                         "拒绝路径不得改动产物一个字节")


class ListShowTests(EngineCase):
    """§2.6 ④ list / show。"""

    # trace: 任务书 §2.6 ④（只回六字段 + --method 过滤生效）
    def test_list_returns_six_fields_and_filters_by_method(self):
        self.init("--method", "创新策略", "--topic", "增长瓶颈")
        self.init("--method", "叙事", "--topic", "品牌故事")
        r = self.engine("list")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = self.results(r)
        self.assertEqual(len(data["sessions"]), 2)
        for item in data["sessions"]:
            self.assertEqual(sorted(item),
                             ["current_step", "date", "id", "method", "status", "topic"])
        one = self.engine("list", "--method", "叙事")
        got = self.results(one)["sessions"]
        self.assertEqual([x["id"] for x in got], ["CM-002"])
        # 非法 --method → ENUM_INVALID（'--method' 必填由 init 面覆盖）
        bad = self.engine("list", "--method", "叙事法")
        self.assertEqual(bad.returncode, 1, bad.stdout)
        self.assertEqual(self.codes(bad), {"ENUM_INVALID"})
        # 产物缺席：按空列表处理，不报错
        os.remove(os.path.join(self.out, "cis-method.yaml"))
        empty = self.engine("list")
        self.assertEqual(empty.returncode, 0, empty.stdout + empty.stderr)
        self.assertEqual(self.results(empty)["sessions"], [])

    # trace: 任务书 §2.6 ④（show 单条全文 / 未知 ID → UNKNOWN_ID）
    def test_show_returns_single_record_and_unknown_id(self):
        self.init("--method", "问题求解", "--topic", "交付延期")
        r = self.engine("show", "--id", "CM-001")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        rec = self.results(r)["session"]
        self.assertEqual(rec["id"], "CM-001")
        self.assertEqual(rec["method"], "问题求解")
        self.assertIn("deliverable", rec)
        miss = self.engine("show", "--id", "CM-009")
        self.assertEqual(miss.returncode, 1, miss.stdout)
        self.assertEqual(self.codes(miss), {"UNKNOWN_ID"})


class CheckFinalTests(EngineCase):
    """§2.6 ⑤ check --final 的四类检出。"""

    def complete(self, method="创新策略", step=None, drop_last=False, status="已完成"):
        if step is None:
            step = BRANCH_STEPS[method]
        keys = first_keys(method, step)
        if drop_last:
            keys = keys[:-1]
        self.product(record_yaml("CM-001", method, status, step, keys))
        return os.path.join(self.out, "cis-method.yaml")

    # trace: 任务书 §2.6 ⑤（status/current_step 不同档 → STATUS_MISMATCH）
    def test_final_detects_status_step_mismatch(self):
        self.complete(status="进行中")
        r = self.check("--final")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("STATUS_MISMATCH", self.codes(r))

    # trace: 任务书 §2.6 ⑤（缺分支必填键 → EMPTY_FIELD，where 含键名）
    def test_final_detects_missing_branch_key_with_name_in_where(self):
        self.complete(drop_last=True)
        r = self.check("--final")
        self.assertEqual(r.returncode, 1, r.stdout)
        data = self.results(r)
        miss = [x for x in data["violations"] if x["code"] == "EMPTY_FIELD"]
        self.assertTrue(miss, data["violations"])
        missing_key = SOURCE_FIRST_KEYS["创新策略"][-1]
        self.assertTrue(any(x["where"].endswith(missing_key) for x in miss),
                        "where 须点名具体键名 %s：%s" % (missing_key, [x["where"] for x in miss]))

    # trace: 任务书 §2.6 ⑤（method 非法 / current_step 越界 → ENUM_INVALID）
    def test_final_detects_enum_invalid_method_and_step(self):
        self.product(record_yaml("CM-001", "创新策略", "已完成", 9,
                                 first_keys("创新策略", 9)).replace("method: 创新策略",
                                                                    "method: 创意策略"))
        r = self.check("--final")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ENUM_INVALID", self.codes(r))
        self.complete()
        self.product(self.read_text("diy-output/cis-method.yaml")
                     .replace("current_step: 9", "current_step: 11"))
        r2 = self.check("--final")
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertIn("ENUM_INVALID", self.codes(r2))

    # trace: 任务书 §2.3（必填键按进度校验：已走到的步其首键须已落）
    def test_in_progress_record_requires_keys_of_steps_walked(self):
        walked = first_keys("问题求解", 3)
        self.product(record_yaml("CM-001", "问题求解", "进行中", 3, walked))
        r = self.check()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        # 抽掉第 2 步的首键 → EMPTY_FIELD 且 where 点名该键
        self.product(record_yaml("CM-001", "问题求解", "进行中", 3,
                                 walked[:1] + walked[2:]))
        r2 = self.check()
        self.assertEqual(r2.returncode, 1, r2.stdout)
        places = [x["where"] for x in self.results(r2)["violations"]]
        self.assertTrue(any(x.endswith(walked[1]) for x in places), places)

    # trace: 任务书 §2.3 边界表（deliverable 缺失/空而 status ≠ 草稿 → EMPTY_FIELD；多余键 → warning）
    def test_deliverable_empty_when_not_draft_and_extra_key_warns(self):
        self.product(record_yaml("CM-001", "设计思维", "进行中", 3, []))
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("EMPTY_FIELD", self.codes(r))
        # 多余键：warning 同形、不阻断（源侧模板键表是建议结构，非封闭集）
        self.product(record_yaml("CM-001", "设计思维", "已完成", 7,
                                 first_keys("设计思维", 7), extra_keys=["外来键"]))
        r2 = self.check("--final")
        self.assertEqual(r2.returncode, 0, r2.stdout + r2.stderr)
        warns = self.results(r2)["warnings"]
        self.assertTrue(any(x["where"].endswith("外来键") for x in warns), warns)
        self.assertEqual(sorted(warns[0]), sorted(V_SHAPE))
        # 注入项落进 deliverable（agent 线残留）→ warning 点名，不阻断
        self.product(record_yaml("CM-002", "叙事", "已完成", 10,
                                 first_keys("叙事", 9), extra_keys=["agent_role", "date"]))
        r3 = self.check("--final")
        self.assertEqual(r3.returncode, 0, r3.stdout + r3.stderr)
        places = [x["where"] for x in self.results(r3)["warnings"]]
        self.assertIn("diy-output/cis-method.yaml.sessions[0].deliverable.agent_role", places)
        self.assertIn("diy-output/cis-method.yaml.sessions[0].deliverable.date", places)

    # trace: 任务书 §2.3（method 与 deliverable 键表不匹配 → 缺键 EMPTY_FIELD + 多余键 warning）
    def test_method_key_table_mismatch(self):
        self.product(record_yaml("CM-001", "叙事", "已完成", 10,
                                 first_keys("创新策略", 9)))
        r = self.check("--final")
        self.assertEqual(r.returncode, 1, r.stdout)
        codes = self.codes(r)
        self.assertIn("EMPTY_FIELD", codes)
        self.assertTrue(self.results(r)["warnings"], "应同时 warning 点名多余键")

    # trace: 任务书 §2.6 ⑨（check 只读：无 updated；--id 收窄）
    def test_check_is_readonly_and_narrowable(self):
        self.complete(method="设计思维")
        r = self.check("--final")
        self.assertNotIn("updated", self.results(r))
        one = self.check("--id", "CM-001")
        self.assertEqual(one.returncode, 0, one.stdout + one.stderr)
        miss = self.check("--id", "CM-007")
        self.assertEqual(miss.returncode, 1, miss.stdout)
        self.assertEqual(self.codes(miss), {"UNKNOWN_ID"})


class OptionalStepTests(EngineCase):
    """§2.6 ⑥ 问题求解分支的 optional 例外（不得推广）。"""

    # trace: 任务书 §2.3 表 / §10 项 8（问题求解 已完成 时 current_step ∈ {8, 9}）
    def test_problem_solving_allows_step_8_when_completed(self):
        self.product(record_yaml("CM-001", "问题求解", "已完成", 8,
                                 first_keys("问题求解", 8)))
        r = self.check("--final")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        # step 9 亦可（跑完可选步）
        self.product(record_yaml("CM-001", "问题求解", "已完成", 9,
                                 first_keys("问题求解", 9)))
        r2 = self.check("--final")
        self.assertEqual(r2.returncode, 0, r2.stdout + r2.stderr)
        # 例外不得推广：创新策略 已完成 + step 8 → STATUS_MISMATCH
        self.product(record_yaml("CM-001", "创新策略", "已完成", 8,
                                 first_keys("创新策略", 8)))
        r3 = self.check("--final")
        self.assertEqual(r3.returncode, 1, r3.stdout)
        self.assertIn("STATUS_MISMATCH", self.codes(r3))
        # 问题求解 进行中 上限仍为 8（末步-1），已完成 才放行 8/9
        self.product(record_yaml("CM-001", "问题求解", "已完成", 7,
                                 first_keys("问题求解", 7)))
        r4 = self.check("--final")
        self.assertEqual(r4.returncode, 1, r4.stdout)


class ReachabilityTests(EngineCase):
    """§2.6 ⑦ 可达集映射（夹具 CSV 驱动）。"""

    def setUp(self):
        super().setUp()
        self.stage_engine(fixture_csv())

    # trace: 任务书 §2.6 ⑦ / §0 裁定 5(e)（默认集 vs --all 的四分支数字）
    def test_default_reachable_set_versus_all(self):
        for method, expected_default in REACHABLE_COUNTS.items():
            base = self.engine("methods", "--method", method)
            self.assertEqual(base.returncode, 0, base.stdout + base.stderr)
            got = self.results(base)["methods"]
            self.assertEqual(len(got), expected_default,
                             "%s 默认可达集应为 %d" % (method, expected_default))
            self.assertEqual({x["method"] for x in got}, {method},
                             "--all 与默认集均不得跨分支")
            self.assertEqual({x["category"] for x in got},
                             set(REACHABLE_CATEGORIES[method]))
            all_r = self.engine("methods", "--method", method, "--all")
            self.assertEqual(len(self.results(all_r)["methods"]), ALL_COUNTS[method],
                             "%s --all 应为全库该分支条数 %d" % (method, ALL_COUNTS[method]))
        # 两值相等的只有叙事（修后：默认集 == --all == 25）
        for method in ("创新策略", "设计思维"):
            base = len(self.results(self.engine("methods", "--method", method))["methods"])
            full = len(self.results(self.engine("methods", "--method", method,
                                                "--all"))["methods"])
            self.assertLess(base, full, "%s 默认集须小于 --all（源侧未接入项）" % method)
        story_base = len(self.results(self.engine("methods", "--method", "叙事"))["methods"])
        story_all = len(self.results(self.engine("methods", "--method", "叙事",
                                                 "--all"))["methods"])
        self.assertEqual(story_base, story_all, "叙事分支默认集 = --all（修后 25）")

    # trace: 任务书 §5 回报必答 ③（真实 cis-methods.csv 在场时逐分支对账）
    def test_real_library_cross_check(self):
        if not os.path.isfile(REAL_CSV):
            self.skipTest("cis-methods.csv 尚未交付（W1 施工中）——交叉核对待补")
        self.engine_path = ENGINE
        for method, expected_default in REACHABLE_COUNTS.items():
            base = self.engine("methods", "--method", method)
            self.assertEqual(base.returncode, 0, base.stdout + base.stderr)
            self.assertEqual(len(self.results(base)["methods"]), expected_default,
                             "真库 %s 默认可达集应为 %d" % (method, expected_default))
            full = self.engine("methods", "--method", method, "--all")
            self.assertEqual(len(self.results(full)["methods"]), ALL_COUNTS[method],
                             "真库 %s --all 应为 %d" % (method, ALL_COUNTS[method]))
        with io.open(REAL_CSV, encoding="utf-8-sig", newline="") as fh:
            rows = list(csv.DictReader(fh))
        self.assertEqual(len(rows), 115, "方法库须为 115 条（四源 30/30/30/25）")


class MethodsContractTests(EngineCase):
    """§2.6 ⑧ methods 的类名校验 / 库解析失败 / --method 缺席 / --random 超界。"""

    def setUp(self):
        super().setUp()
        self.stage_engine(fixture_csv())

    # trace: 任务书 §2.6 ⑧ / §0 裁定 5(e)（非法类 → ENUM_INVALID；缺席 --method → EMPTY_FIELD）
    def test_category_and_missing_method(self):
        bad = self.engine("methods", "--method", "创新策略", "--category", "不存在类")
        self.assertEqual(bad.returncode, 1, bad.stdout)
        self.assertEqual(self.codes(bad), {"ENUM_INVALID"})
        # 跨分支类名：创新策略 无「共情」类 → ENUM_INVALID（同名类由 method 列消歧）
        cross = self.engine("methods", "--method", "创新策略", "--category", "共情")
        self.assertEqual(cross.returncode, 1, cross.stdout)
        self.assertEqual(self.codes(cross), {"ENUM_INVALID"})
        # 同名类不跨分支：战略 在创新策略与叙事各自 5 条
        for method in ("创新策略", "叙事"):
            one = self.engine("methods", "--method", method, "--category", "战略")
            got = self.results(one)["methods"]
            self.assertEqual(len(got), PER_CATEGORY)
            self.assertEqual({x["method"] for x in got}, {method})
        # --method 缺席 → EMPTY_FIELD exit 1（非 argparse exit 2）
        miss = self.engine("methods")
        self.assertEqual(miss.returncode, 1, miss.stdout)
        self.assertEqual(self.codes(miss), {"EMPTY_FIELD"})

    # trace: 任务书 §2.6 ⑧（库缺列 / 列名不符 → UNPARSABLE_YAML）
    def test_library_header_defects(self):
        self.stage_engine("method,category,name,description,prompts" + NL + "创新策略,战略,甲,,描述,问" + NL)
        r = self.engine("methods", "--method", "创新策略")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertEqual(self.codes(r), {"UNPARSABLE_YAML"})
        self.stage_engine("method,category,title,slug,description,prompts" + NL
                          + "创新策略,战略,甲,,描述,问" + NL)
        r2 = self.engine("methods", "--method", "创新策略")
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertEqual(self.codes(r2), {"UNPARSABLE_YAML"})
        # 库文件缺席 → MISSING_FILE
        os.remove(os.path.join(self.root, "_skill", "diy-cis-method", "cis-methods.csv"))
        r3 = self.engine("methods", "--method", "创新策略")
        self.assertEqual(r3.returncode, 1, r3.stdout)
        self.assertEqual(self.codes(r3), {"MISSING_FILE"})

    # trace: 任务书 §0 裁定 5(e)（--random 从默认结果集抽；超界 → 全给 + warning 不报错）
    def test_random_draws_from_default_set(self):
        r = self.engine("methods", "--method", "创新策略", "--random", "3")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        got = self.results(r)["methods"]
        self.assertEqual(len(got), 3)
        self.assertEqual(len({x["name"] for x in got}), 3, "--random 抽样不得重复")
        self.assertTrue({x["category"] for x in got}
                        <= set(REACHABLE_CATEGORIES["创新策略"]),
                        "--random 须从默认可达集抽")
        over = self.engine("methods", "--method", "设计思维", "--random", "99")
        self.assertEqual(over.returncode, 0, over.stdout + over.stderr)
        p = self.results(over)
        self.assertEqual(len(p["methods"]), REACHABLE_COUNTS["设计思维"])
        self.assertTrue(p["warnings"], "超界须给 warning 而非报错")
        self.assertEqual(sorted(p["warnings"][0]), sorted(V_SHAPE))
        zero = self.engine("methods", "--method", "创新策略", "--random", "0")
        self.assertEqual(zero.returncode, 1, zero.stdout)
        self.assertEqual(self.codes(zero), {"ENUM_INVALID"})


class ReceiptTests(EngineCase):
    """§2.6 ⑨ 回执 schema。"""

    def setUp(self):
        super().setUp()
        self.stage_engine(fixture_csv())

    # trace: 任务书 §2.2 / §2.6 ⑨（公共键 + instance 恒 null + warnings 同形 + 单行 JSON）
    def test_receipt_keys_and_json_single_line(self):
        # 只读子命令不写盘：产物目录在调用前后均无产物
        self.assertFalse(os.path.exists(os.path.join(self.out, "cis-method.yaml")))
        r = self.engine("list")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse(os.path.exists(os.path.join(self.out, "cis-method.yaml")),
                         "只读子命令不得写盘")
        self.assertEqual(r.stdout.strip().count(NL), 0, "须为单行 JSON")
        data = self.results(r)
        for key in RECEIPT_KEYS:
            self.assertIn(key, data, "回执缺公共键 %s" % key)
        self.assertIsNone(data["instance"], "本批不做实例，但键在位恒 null")
        self.assertEqual(data["command"], "list")
        self.assertEqual(data["project_root"], self.root)
        self.assertNotIn("updated", data, "只读子命令回执不含 updated")
        init = self.results(self.init("--method", "创新策略", "--topic", "议题"))
        self.assertIn("updated", init, "init 写盘回执须含 updated")
        for code_key in ("violations", "warnings"):
            self.assertIsInstance(data[code_key], list)
        # 违规项 where 正斜杠
        bad = self.init("--method", "创新策略", "--topic", "")
        for item in self.results(bad)["violations"]:
            self.assertEqual(sorted(item), sorted(V_SHAPE))
            self.assertNotIn("\\\\", item["where"])

    # trace: 任务书 §2.2（--output-dir 必填于写盘子命令；只读子命令可省 → output_dir 取 resolve 值）
    def test_output_dir_optional_for_readonly_commands(self):
        # 方法库加载不依赖产物目录：省 --output-dir 照常工作，回执 output_dir 为 null
        r = self.raw("methods", "--method", "创新策略", "--project-root", self.root, "--json")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertIsNone(data["output_dir"])
        self.assertTrue(data["methods"])
        # 需读产物的只读子命令省 --output-dir：明确报缺，不静默按空处理
        r2 = self.raw("list", "--project-root", self.root, "--json")
        self.assertEqual(r2.returncode, 1, r2.stdout)
        data2 = json.loads(r2.stdout)
        self.assertEqual({x["code"] for x in data2["violations"]}, {"EMPTY_FIELD"})
        self.assertIsNone(data2["output_dir"])


class SkillContractTests(unittest.TestCase):
    """§2.6 ⑩ SKILL.md 契约冒烟（W1 并行交付；缺席则跳过）。"""

    def read_skill(self):
        if not os.path.isfile(SKILL_MD):
            self.skipTest("SKILL.md 尚未交付（W1 施工中）——契约冒烟待补")
        with io.open(SKILL_MD, encoding="utf-8") as f:
            return f.read()

    # trace: 任务书 §2.6 ⑩（母本 §1 逐字 + 终门句指向本引擎 + 产物路径声明句）
    def test_skill_contract_smoke(self):
        raw = self.read_skill()
        self.assertIn(INSTANCE_ZH, raw, "缺母本 §1 实例解析中文定稿（逐字）")
        for section in ("## 激活时", "## 工作流", "## 结构", "## 规则"):
            self.assertIn(section, raw, "缺段 %s" % section)
        self.assertIn("cis_method.py", raw, "终门句未指向本技能领域引擎")
        self.assertIn("check --final", raw, "终门句缺 check --final")
        self.assertIn("cis-method.yaml", raw, "产物路径声明句不在场")
        self.assertIn("diy-cis-method", raw)
        self.assertIn("TOKEN_UNRESOLVED", raw, "规则段须声明唯一新增违规码")
        self.assertLessEqual(len(raw.replace(NL + "\r", NL).replace("\r\n", NL)
                                 .rstrip(NL).split(NL)), 90,
                             "SKILL.md 超 90 行（薄主文件硬阈值）")


class TokenTests(EngineCase):
    """§2.6 ⑪ 未解析 `{...}` 令牌 → TOKEN_UNRESOLVED（唯一新增码）。"""

    # trace: 任务书 §0 裁定 8 / §10 项 7（白名单外令牌一律拒绝）
    def test_unresolved_token_is_rejected(self):
        self.product(record_yaml("CM-001", "设计思维", "已完成", 7,
                                 first_keys("设计思维", 7)))
        good = self.check("--final")
        self.assertEqual(good.returncode, 0, good.stdout + good.stderr)
        text = self.read_text("diy-output/cis-method.yaml")
        for token in ("{skill-name}", "{output_folder}", "{some_token}"):
            self.product(text.replace("design_challenge 的内容",
                                      '"内容 %s 在场"' % token))
            r = self.check()
            self.assertEqual(r.returncode, 1, r.stdout)
            self.assertIn("TOKEN_UNRESOLVED", self.codes(r))
            self.assertIn(token, r.stdout, "回执须点名未解析令牌")
        # 白名单两项不报（{project-root} 唯一例外 + {output_dir} 为 output_folder 的 diy 替换）
        self.product(text.replace("design_challenge 的内容",
                                  '"{project-root}/diy-output 与 {output_dir}"'))
        ok = self.check("--final")
        self.assertEqual(ok.returncode, 0, ok.stdout + ok.stderr)


class EmptyStateTests(EngineCase):
    """§2.6 ⑫ 空态拒绝。"""

    # trace: 任务书 §2.3 边界表（sessions: [] + --final → EMPTY_FIELD exit 1）
    def test_empty_sessions_rejected_only_under_final(self):
        self.product(NL.join(["project:",
                              "  name: mini",
                              "  created: '2026-09-18'",
                              "  updated: '2026-09-18'",
                              "sessions: []",
                              "revisions: []"]) + NL)
        r = self.check()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        final = self.check("--final")
        self.assertEqual(final.returncode, 1, final.stdout)
        self.assertEqual(self.codes(final), {"EMPTY_FIELD"})
        # 产物缺席：check 报 MISSING_FILE
        os.remove(os.path.join(self.out, "cis-method.yaml"))
        miss = self.check()
        self.assertEqual(miss.returncode, 1, miss.stdout)
        self.assertEqual(self.codes(miss), {"MISSING_FILE"})


class DuplicateIdTests(EngineCase):
    """§2.6 ⑬ ID 唯一性。"""

    # trace: 任务书 §8 验收 #4（重复 CM-001 → DUPLICATE_ID）
    def test_duplicate_id_is_reported(self):
        text = record_yaml("CM-001", "创新策略", "草稿", 1, [])
        head, tail = text.split("sessions:" + NL)
        body = tail.replace("revisions: []" + NL, "")
        self.product(head + "sessions:" + NL + body + body + "revisions: []" + NL)
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("DUPLICATE_ID", self.codes(r))


class InternalTableTests(unittest.TestCase):
    """引擎内表核对（§5 回报必答 ②/③ 的机械证据；直接导入引擎模块）。"""

    def load_module(self):
        if not os.path.isfile(ENGINE):
            self.skipTest("cis_method.py 尚未交付（W3 施工中）")
        spec = importlib.util.spec_from_file_location("cis_method_under_test", ENGINE)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    # trace: 任务书 §2.3（34 键 = 9+9+7+9，注入项不入表）
    def test_required_key_table_is_34_and_injection_free(self):
        mod = self.load_module()
        table = getattr(mod, "STEP_KEYS", None)
        self.assertIsNotNone(table, "引擎须持有分支必填键表 STEP_KEYS")
        total = 0
        for method, keys in table.items():
            self.assertEqual(list(keys), SOURCE_FIRST_KEYS[method],
                             "%s 必填键表与源侧首键不符" % method)
            total += len(keys)
        self.assertEqual(total, 34, "34 键（9+9+7+9）")
        self.assertEqual(set(table) , set(BRANCH_STEPS))
        flat = [k for keys in table.values() for k in keys]
        self.assertFalse(set(flat) & set(INJECTION_KEYS), "注入项不得入表")
        self.assertEqual(len(table["叙事"]), 9, "叙事第 10 步唯一标签全是注入项 → 该步无实键")

    # trace: 任务书 §0 裁定 5(e)（可达集映射：23 类名逐字 + 25/30/15/25）
    def test_reachability_map_matches_frozen_names(self):
        mod = self.load_module()
        reach = getattr(mod, "REACHABLE_CATEGORIES", None)
        frozen = getattr(mod, "CATEGORY_ENUM", None)
        self.assertIsNotNone(reach, "引擎须持有可达类别映射")
        self.assertIsNotNone(frozen, "引擎须持有 23 个冻结类名表")
        for method in BRANCH_STEPS:
            self.assertEqual(list(reach[method]), REACHABLE_CATEGORIES[method])
            self.assertEqual(list(frozen[method]), FROZEN_CATEGORIES[method])
            self.assertEqual(len(reach[method]) * PER_CATEGORY, REACHABLE_COUNTS[method])
            self.assertEqual(len(frozen[method]) * PER_CATEGORY, ALL_COUNTS[method])
        names = {name for group in frozen.values() for name in group}
        self.assertEqual(len(names), 21, "23 个类名去重后 21 个（战略、分析各跨两分支）")

    # trace: 任务书 §0 裁定 8（令牌白名单）
    def test_token_whitelist(self):
        mod = self.load_module()
        whitelist = getattr(mod, "TOKEN_WHITELIST", None)
        self.assertIsNotNone(whitelist)
        self.assertEqual(tuple(whitelist), ("{project-root}", "{output_dir}"))


if __name__ == "__main__":
    unittest.main()
