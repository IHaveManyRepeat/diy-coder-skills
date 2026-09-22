# -*- coding: utf-8 -*-
"""diy-wds-evolution 冒烟测试（B7b 工位 W3）。

覆盖 B7b 任务书 §0.2 裁定 20 的八类必备用例 + 本技能特有边界：
  ① 门禁（无参 exit 2 / 非法值 ENUM_INVALID / 空值 EMPTY_FIELD / 入口门禁零产出）
  ② init 合法 + 骨架断言
  ③ ID 铸号（EV-<nn> 递增、不重复、不跳号）
  ④ list 只回约定字段 + 过滤
  ⑤ check 各类违规
  ⑥ 跨技能门禁（既有产物任一在场 → 放行；全缺 → 零产出）
  ⑦ 回执键完整性
  ⑧ 契约冒烟（SKILL.md 四段 + 母本六节逐字 + 终门句 + 红线）
  ⑨ 本技能特有边界：Kaizen 优先级框架（Impact×Effort×Learning 重算）+ 本轮增量校验

夹具全落 tempfile；不读写仓库真实 diy-output/；不依赖 git 状态。
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

import yaml

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
DIy_CODER = os.path.dirname(TESTS_DIR)                      # diy-coder/
SKILL_DIR = os.path.join(DIy_CODER, "skills", "diy-wds-evolution")
SCRIPT = os.path.join(SKILL_DIR, "scripts", "wds_evolution.py")
SKILL_MD = os.path.join(SKILL_DIR, "SKILL.md")
STEPS_DIR = os.path.join(SKILL_DIR, "steps")
DATA_DIR = os.path.join(SKILL_DIR, "data")

PRODUCT = "wds-evolution.yaml"

# —— 母本（diy-coder/.analysis/2026-09-16-skill-remediation/suite-texts.md）逐字片段 ——
MOTHER_1 = (
    '实例解析（FR-4.5/D-9）由工具脚本执行：运行 `python "{project-root}/.claude/skills/'
    'diy-tools/scripts/diyc.py" resolve [--instance <name>] --json`，把回执里的 `output_dir` '
    '当作本次运行唯一的读写根目录。'
)
MOTHER_2 = (
    '- **写作纪律。** 主字段 = 大白话主句；数字/枚举内联；机器语法（命令/旗标/路径）进括号；'
    '机器锚点逐字保留（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 `diy-design` 的 '
    'detect 启发式。schema 若定义 `plain`：一行写清该条目为什么存在，绝不写是什么（转述会漂移）；'
    '只写难懂的条目。若定义 `detail`：过程叙述——结论留在主字段。'
)
MOTHER_3A = '读 `{project-root}/diy-coder.yaml`；解析 `project.communication_language` / `project.document_output_language` / `paths.output_dir`。'
MOTHER_3B = '全程用 `communication_language` 对话；产物里的叙述文字用 `document_output_language` 写。机器锚点（ID、枚举值、文件名）逐字保留。'
MOTHER_3C = (
    '缺省链：`paths.output_dir` 一律取 `diyc.py resolve` 回执（引擎缺省 `diy-output`，异常形状降级并 warning）；'
    '缺 `document_output_language` 落 `project.communication_language`；两者皆缺则跟随用户当前消息的语言，并在收尾一行说明。'
)
MOTHER_3D = (
    '实例名只在本次激活参数出现 `--instance <name>` 时才传（无头侧入口 `runner.py --instance`；'
    '交互侧由用户在发起消息里给出同一旗标）；未传时回执的 `output_dir` 即主线平铺根。'
)
MOTHER_4 = (
    '读取纪律：预载预算 = 本文件、上述配置与回执、`steps/` 下当前那一个文件——绝不批量预载；'
    '执行期读取以每个步骤开头的 `Read (input)` 行为唯一权威，**主文件不列举封闭清单**。'
)
MOTHER_5 = (
    '渲染是静默旁路——只写调用命令，不新增「打开浏览器 / 报告路径等待查看 / 阻塞等待」交互点：'
    '`python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"`'
    '（resolved 实例时附 `--instance <name>`）。'
)
MOTHER_6 = '- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；不复述上游已写的信息（引用 ID）；不写没有信息量的套话。'


def run_cli(*args, cwd=None):
    """跑引擎 CLI，回 (rc, receipt|None, stdout, stderr)。"""
    cmd = [sys.executable, SCRIPT] + list(args)
    proc = subprocess.run(
        cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8"
    )
    receipt = None
    out = (proc.stdout or "").strip()
    if out:
        try:
            receipt = json.loads(out.splitlines()[-1])
        except json.JSONDecodeError:
            receipt = None
    return proc.returncode, receipt, proc.stdout, proc.stderr


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = self._tmp.name
        self.out = os.path.join(self.root, "diy-output")
        os.makedirs(self.out, exist_ok=True)

    def tearDown(self):
        self._tmp.cleanup()

    # ---- 夹具 ----
    def write_artifact(self, name, payload=None):
        path = os.path.join(self.out, name)
        with open(path, "w", encoding="utf-8") as fh:
            yaml.safe_dump(payload or {"project": {"name": "x"}}, fh, allow_unicode=True)
        return path

    def product_path(self):
        return os.path.join(self.out, PRODUCT)

    def load_product(self):
        with open(self.product_path(), encoding="utf-8") as fh:
            return yaml.safe_load(fh)

    def dump_product(self, data):
        with open(self.product_path(), "w", encoding="utf-8") as fh:
            yaml.safe_dump(data, fh, allow_unicode=True, sort_keys=False)

    def init_ok(self, **kw):
        args = ["init", "--entry", kw.get("entry", "上线后持续"),
                "--target", kw.get("target", "功能 X 首次使用引导"),
                "--project-root", self.root, "--output-dir", self.out, "--json"]
        return run_cli(*args)

    def full_product(self):
        """一份可过 --final 的完整产物。"""
        return {
            "project": {"name": "evo", "created": "2026-09-21",
                        "updated": "2026-09-21", "status": "已定稿"},
            "kaizen_priority": {
                "formula": "Priority = Impact × Effort × Learning",
                "scale": {
                    "impact": {"high": 5, "medium": 3, "low": 1},
                    "effort": {"high": 5, "medium": 3, "low": 1},
                    "learning": {"high": 5, "medium": 3, "low": 1},
                },
                "candidates": [
                    {"target": "功能 X 首次使用引导", "impact": "high",
                     "effort": "high", "learning": "medium", "score": 75},
                ],
            },
            "rounds": [{
                "id": "EV-01", "target": "功能 X 首次使用引导",
                "status": "已交付", "entry": "上线后持续",
                "analysis": {"snapshot": "4 页 / 3 条主流程"},
                "scope": {"page": "功能 X 主屏", "risk": "low"},
                "design": {"summary": "加内联引导"},
                "implement": {"branch": "evolution/feature-x-onboarding",
                              "files": ["src/x.tsx"]},
                "test": {"scope": "本轮增量",
                         "criteria": [{"kind": "HP", "criterion": "首次使用有引导气泡",
                                       "how": "新账号首登", "expected": "出现气泡",
                                       "actual": "出现气泡", "verdict": "通过"}]},
                "delivery": {"summary": "已交付 1 项增量", "pr": None},
            }],
            "revisions": [],
        }


class GateTests(Base):
    """① 门禁 + ⑥ 跨技能门禁。"""

    def test_no_subcommand_is_usage_error(self):
        rc, _, _, _ = run_cli()
        self.assertEqual(rc, 2)

    def test_init_without_output_dir_is_usage_error(self):
        rc, _, _, _ = run_cli("init", "--entry", "上线后持续",
                              "--target", "t", "--project-root", self.root)
        self.assertEqual(rc, 2)

    def test_init_empty_target_is_empty_field_and_no_write(self):
        self.write_artifact("design.yaml")
        rc, rec, _, _ = run_cli("init", "--entry", "上线后持续", "--target", "",
                                "--project-root", self.root, "--output-dir", self.out,
                                "--json")
        self.assertEqual(rc, 1)
        self.assertEqual(rec["violations"][0]["code"], "EMPTY_FIELD")
        self.assertFalse(os.path.exists(self.product_path()))

    def test_init_missing_target_is_empty_field(self):
        self.write_artifact("design.yaml")
        rc, rec, _, _ = run_cli("init", "--entry", "上线后持续",
                                "--project-root", self.root, "--output-dir", self.out,
                                "--json")
        self.assertEqual(rc, 1)
        self.assertEqual(rec["violations"][0]["code"], "EMPTY_FIELD")
        self.assertFalse(os.path.exists(self.product_path()))

    def test_init_bad_entry_is_enum_invalid_and_no_write(self):
        self.write_artifact("design.yaml")
        rc, rec, _, _ = run_cli("init", "--entry", "第三种", "--target", "t",
                                "--project-root", self.root, "--output-dir", self.out,
                                "--json")
        self.assertEqual(rc, 1)
        self.assertEqual(rec["violations"][0]["code"], "ENUM_INVALID")
        self.assertFalse(os.path.exists(self.product_path()))

    def test_entry_gate_zero_output_when_no_existing_artifact(self):
        rc, rec, _, _ = self.init_ok()
        self.assertEqual(rc, 1)
        self.assertEqual(rec["violations"][0]["code"], "MISSING_FILE")
        self.assertFalse(os.path.exists(self.product_path()))

    def test_gate_opens_on_any_single_existing_artifact(self):
        for name in ("design.yaml", "sprint.yaml", "wds-scenarios.yaml",
                     "wds-brief.yaml", "wds-assets.yaml"):
            with self.subTest(name=name):
                with tempfile.TemporaryDirectory() as tmp:
                    out = os.path.join(tmp, "diy-output")
                    os.makedirs(out)
                    self.write_artifact_at(out, name)
                    rc, rec, _, _ = run_cli(
                        "init", "--entry", "存量接入", "--target", "目标甲",
                        "--project-root", tmp, "--output-dir", out, "--json")
                    self.assertEqual(rc, 0, rec)
                    self.assertTrue(os.path.exists(os.path.join(out, PRODUCT)))

    def write_artifact_at(self, out, name):
        with open(os.path.join(out, name), "w", encoding="utf-8") as fh:
            yaml.safe_dump({"project": {"name": "x"}}, fh, allow_unicode=True)

    def test_own_product_does_not_satisfy_gate(self):
        """本技能自己的产物不算「既有产物」——否则真门禁会被自己的产物绕开。"""
        self.write_artifact(PRODUCT, {"project": {"name": "x"}})
        rc, rec, _, _ = self.init_ok()
        self.assertEqual(rc, 1)
        self.assertEqual(rec["violations"][0]["code"], "MISSING_FILE")


class InitTests(Base):
    """② init 骨架。"""

    def test_init_mints_skeleton_and_first_round(self):
        self.write_artifact("design.yaml")
        rc, rec, _, _ = self.init_ok()
        self.assertEqual(rc, 0, rec)
        self.assertIn("updated", rec)
        data = self.load_product()
        self.assertEqual(data["project"]["status"], "草稿")
        self.assertTrue(data["project"]["name"])
        self.assertTrue(data["project"]["created"])
        self.assertEqual(data["rounds"][0]["id"], "EV-01")
        self.assertEqual(data["rounds"][0]["status"], "草稿")
        self.assertEqual(data["rounds"][0]["entry"], "上线后持续")
        self.assertEqual(data["rounds"][0]["target"], "功能 X 首次使用引导")
        self.assertEqual(data["revisions"], [])
        self.assertIn("kaizen_priority", data)

    def test_init_does_not_overwrite_existing_product(self):
        self.write_artifact("design.yaml")
        run_cli("init", "--entry", "上线后持续", "--target", "目标甲",
                "--project-root", self.root, "--output-dir", self.out, "--json")
        before = self.load_product()
        rc, rec, _, _ = run_cli("init", "--entry", "存量接入", "--target", "目标乙",
                                "--project-root", self.root, "--output-dir", self.out,
                                "--json")
        self.assertEqual(rc, 0, rec)
        self.assertTrue(rec["warnings"])
        after = self.load_product()
        self.assertEqual(after["project"]["created"], before["project"]["created"])
        self.assertEqual(after["rounds"][0]["target"], "目标甲")
        self.assertEqual(len(after["rounds"]), 1)

    def test_init_on_corrupt_product_refuses_without_write(self):
        self.write_artifact("design.yaml")
        with open(self.product_path(), "w", encoding="utf-8") as fh:
            fh.write("project: [\n")
        rc, rec, _, _ = self.init_ok()
        self.assertEqual(rc, 1)
        self.assertEqual(rec["violations"][0]["code"], "UNPARSABLE_YAML")
        with open(self.product_path(), encoding="utf-8") as fh:
            self.assertEqual(fh.read(), "project: [\n")


class ListShowTests(Base):
    """③④ list / show。"""

    def setUp(self):
        super().setUp()
        self.write_artifact("design.yaml")
        self.init_ok()

    def test_list_returns_only_contract_fields(self):
        rc, rec, _, _ = run_cli("list", "--project-root", self.root,
                                "--output-dir", self.out, "--json")
        self.assertEqual(rc, 0, rec)
        self.assertEqual(rec["counts"]["rounds"], 1)
        item = rec["rounds"][0]
        self.assertEqual(set(item.keys()),
                         {"id", "target", "status", "entry"})

    def test_list_filter_and_bad_value(self):
        data = self.load_product()
        data["rounds"].append({"id": "EV-02", "target": "目标乙",
                               "status": "验证", "entry": "存量接入"})
        self.dump_product(data)
        rc, rec, _, _ = run_cli("list", "--status", "验证", "--project-root", self.root,
                                "--output-dir", self.out, "--json")
        self.assertEqual(rc, 0, rec)
        self.assertEqual([r["id"] for r in rec["rounds"]], ["EV-02"])
        rc, rec, _, _ = run_cli("list", "--status", "不存在", "--project-root", self.root,
                                "--output-dir", self.out, "--json")
        self.assertEqual(rc, 1)
        self.assertEqual(rec["violations"][0]["code"], "ENUM_INVALID")

    def test_show_whole_and_by_id(self):
        rc, rec, _, _ = run_cli("show", "--project-root", self.root,
                                "--output-dir", self.out, "--json")
        self.assertEqual(rc, 0, rec)
        rc, rec, _, _ = run_cli("show", "--id", "EV-01", "--project-root", self.root,
                                "--output-dir", self.out, "--json")
        self.assertEqual(rc, 0, rec)
        self.assertEqual(rec["round"]["id"], "EV-01")
        rc, rec, _, _ = run_cli("show", "--id", "EV-99", "--project-root", self.root,
                                "--output-dir", self.out, "--json")
        self.assertEqual(rc, 1)
        self.assertEqual(rec["violations"][0]["code"], "UNKNOWN_ID")


class CheckTests(Base):
    """⑤ check 各类违规 + ⑨ 本技能特有边界。"""

    def setUp(self):
        super().setUp()
        self.write_artifact("design.yaml")
        self.init_ok()

    def codes(self, rec):
        return [x["code"] for x in rec["violations"]]

    def check(self, *extra):
        return run_cli("check", *extra, "--project-root", self.root,
                       "--output-dir", self.out, "--json")

    def test_check_missing_file(self):
        os.remove(self.product_path())
        rc, rec, _, _ = self.check()
        self.assertEqual(rc, 1)
        self.assertIn("MISSING_FILE", self.codes(rec))

    def test_check_unparsable_yaml(self):
        with open(self.product_path(), "w", encoding="utf-8") as fh:
            fh.write("project: [\n")
        rc, rec, _, _ = self.check()
        self.assertEqual(rc, 1)
        self.assertIn("UNPARSABLE_YAML", self.codes(rec))

    def test_check_round_status_and_entry_enums(self):
        data = self.load_product()
        data["rounds"][0]["status"] = "在做"
        data["rounds"][0]["entry"] = "第三轨"
        self.dump_product(data)
        rc, rec, _, _ = self.check()
        self.assertEqual(rc, 1)
        self.assertEqual(self.codes(rec).count("ENUM_INVALID"), 2)

    def test_check_duplicate_and_gap_round_ids(self):
        data = self.load_product()
        data["rounds"].append(dict(data["rounds"][0]))
        self.dump_product(data)
        rc, rec, _, _ = self.check()
        self.assertEqual(rc, 1)
        self.assertIn("DUPLICATE_ID", self.codes(rec))

        data = self.load_product()
        data["rounds"] = [data["rounds"][0],
                          {"id": "EV-03", "target": "乙", "status": "草稿",
                           "entry": "存量接入"}]
        self.dump_product(data)
        rc, rec, _, _ = self.check()
        self.assertEqual(rc, 1)
        self.assertIn("SET_MISMATCH", self.codes(rec))

    def test_check_bad_round_id_shape(self):
        data = self.load_product()
        data["rounds"][0]["id"] = "EV-1"
        self.dump_product(data)
        rc, rec, _, _ = self.check()
        self.assertEqual(rc, 1)
        self.assertIn("ENUM_INVALID", self.codes(rec))

    def test_check_empty_round_target(self):
        data = self.load_product()
        data["rounds"][0]["target"] = "  "
        self.dump_product(data)
        rc, rec, _, _ = self.check()
        self.assertEqual(rc, 1)
        self.assertIn("EMPTY_FIELD", self.codes(rec))

    def test_check_final_requires_finalized_status(self):
        rc, rec, _, _ = self.check("--final")
        self.assertEqual(rc, 1)
        self.assertIn("STATUS_MISMATCH", self.codes(rec))

    def test_check_final_requires_six_phases(self):
        data = self.full_product()
        del data["rounds"][0]["delivery"]
        self.dump_product(data)
        rc, rec, _, _ = self.check("--final")
        self.assertEqual(rc, 1)
        self.assertIn("EMPTY_FIELD", self.codes(rec))

    def test_check_final_requires_increment_scope(self):
        """裁定 10：[T] 只验本轮增量。"""
        data = self.full_product()
        data["rounds"][0]["test"]["scope"] = "全量验收"
        self.dump_product(data)
        rc, rec, _, _ = self.check("--final")
        self.assertEqual(rc, 1)
        self.assertIn("ENUM_INVALID", self.codes(rec))

    def test_check_final_requires_all_criteria_passed(self):
        data = self.full_product()
        data["rounds"][0]["test"]["criteria"][0]["verdict"] = "未通过"
        self.dump_product(data)
        rc, rec, _, _ = self.check("--final")
        self.assertEqual(rc, 1)
        self.assertIn("STATUS_MISMATCH", self.codes(rec))

    def test_check_final_requires_criterion_kind(self):
        """判据四类（源 TS-XXX 的 HP-/REG-/EC-/A11Y- 族）逐条在场。"""
        data = self.full_product()
        del data["rounds"][0]["test"]["criteria"][0]["kind"]
        self.dump_product(data)
        rc, rec, _, _ = self.check("--final")
        self.assertEqual(rc, 1)
        self.assertIn("EMPTY_FIELD", self.codes(rec))

        data = self.full_product()
        data["rounds"][0]["test"]["criteria"][0]["kind"] = "SMOKE"
        self.dump_product(data)
        rc, rec, _, _ = self.check("--final")
        self.assertEqual(rc, 1)
        self.assertIn("ENUM_INVALID", self.codes(rec))

    def test_check_kaizen_score_recompute(self):
        data = self.full_product()
        data["kaizen_priority"]["candidates"][0]["score"] = 15
        self.dump_product(data)
        rc, rec, _, _ = self.check("--final")
        self.assertEqual(rc, 1)
        self.assertIn("SET_MISMATCH", self.codes(rec))

    def test_check_kaizen_factor_level_enum(self):
        data = self.full_product()
        data["kaizen_priority"]["candidates"][0]["impact"] = "very-high"
        self.dump_product(data)
        rc, rec, _, _ = self.check("--final")
        self.assertEqual(rc, 1)
        self.assertIn("ENUM_INVALID", self.codes(rec))

    def test_check_round_target_must_be_a_candidate(self):
        data = self.full_product()
        data["rounds"][0]["target"] = "清单外的目标"
        self.dump_product(data)
        rc, rec, _, _ = self.check("--final")
        self.assertEqual(rc, 1)
        self.assertIn("SET_MISMATCH", self.codes(rec))

    def test_check_kaizen_framework_present(self):
        data = self.full_product()
        del data["kaizen_priority"]["scale"]
        self.dump_product(data)
        rc, rec, _, _ = self.check("--final")
        self.assertEqual(rc, 1)
        self.assertIn("EMPTY_FIELD", self.codes(rec))

    def test_check_assumption_marker(self):
        data = self.full_product()
        data["rounds"][0]["analysis"]["snapshot"] = "4 页 [假设] 未核"
        self.dump_product(data)
        rc, rec, _, _ = self.check("--final")
        self.assertEqual(rc, 1)
        self.assertIn("ASSUMPTION_PRESENT", self.codes(rec))

    def test_full_fixture_passes_final(self):
        self.dump_product(self.full_product())
        rc, rec, _, _ = self.check("--final")
        self.assertEqual(rc, 0, rec)
        self.assertEqual(rec["counts"]["rounds"], 1)

    def test_draft_check_tolerates_unfinished_round(self):
        rc, rec, _, _ = self.check()
        self.assertEqual(rc, 0, rec)


class OutputDirFallbackTests(Base):
    """⑩ 回归 V3-01：省略 `--output-dir` 时缺省须回落 `{project-root}/diy-output`。

    触发面：runner / 无头编排按 `--project-root X` 调用且不带 `--output-dir`。
    缺陷形态是**静默**的——CWD 相对回落会读到另一个项目的产物、且 rc=0。
    """

    def _dump_product(self, out_dir, target):
        os.makedirs(out_dir, exist_ok=True)
        doc = {
            "project": {"name": target, "created": "2026-09-21",
                        "updated": "2026-09-21", "status": "草稿"},
            "rounds": [{"id": "EV-01", "target": target, "status": "草稿",
                        "entry": "上线后持续"}],
            "revisions": [],
        }
        with open(os.path.join(out_dir, PRODUCT), "w", encoding="utf-8") as fh:
            yaml.safe_dump(doc, fh, allow_unicode=True, sort_keys=False)

    def test_default_output_dir_follows_project_root_not_cwd(self):
        # CWD 指向另一个临时项目 B（B 有自己的 diy-output 与本技能产物）
        with tempfile.TemporaryDirectory() as elsewhere:
            cwd_b = os.path.join(elsewhere, "proj-b")
            self._dump_product(os.path.join(cwd_b, "diy-output"), "FROM-CWD-B")
            # project-root 指向 A（A 有自己的 diy-output 与本技能产物）
            self._dump_product(self.out, "FROM-PROJ-A")

            rc, rec, _, err = run_cli("list", "--project-root", self.root,
                                      "--json", cwd=cwd_b)
            self.assertEqual(rc, 0, (rec, err))
            self.assertEqual(rec["rounds"][0]["target"], "FROM-PROJ-A")
            self.assertNotEqual(rec["rounds"][0]["target"], "FROM-CWD-B")
            self.assertEqual(rec["output_dir"],
                             os.path.join(self.root, "diy-output").replace("\\", "/"))


class ReceiptTests(Base):
    """⑦ 回执键完整性。"""

    KEYS = {"ok", "command", "project_root", "output_dir", "instance",
            "violations", "warnings", "counts"}

    def test_common_receipt_keys(self):
        self.write_artifact("design.yaml")
        for args in (("init", "--entry", "上线后持续", "--target", "t"),
                     ("list",), ("show",), ("check",)):
            with self.subTest(cmd=args[0]):
                rc, rec, _, _ = run_cli(*args, "--project-root", self.root,
                                        "--output-dir", self.out, "--json")
                self.assertTrue(self.KEYS.issubset(set(rec.keys())), rec)
                self.assertIn("instance", rec)
                self.assertIsNone(rec["instance"])
                self.assertIsInstance(rec["violations"], list)
                self.assertIsInstance(rec["warnings"], list)
                if args[0] == "init":
                    self.assertIn("updated", rec)
                else:
                    self.assertNotIn("updated", rec)

    def test_human_output_without_json(self):
        self.write_artifact("design.yaml")
        self.init_ok()
        rc, _, out, _ = run_cli("check", "--project-root", self.root,
                                "--output-dir", self.out)
        self.assertEqual(rc, 0)
        self.assertTrue(out.strip())


class ContractSmokeTests(unittest.TestCase):
    """⑧ 契约冒烟。"""

    def skill_text(self):
        with open(SKILL_MD, encoding="utf-8") as fh:
            return fh.read()

    def test_skill_md_line_budget(self):
        text = self.skill_text()
        lines = text.splitlines()
        self.assertLessEqual(len(lines), 90, "SKILL.md 超 90 行硬阈值")

    def test_skill_md_four_sections(self):
        text = self.skill_text()
        for head in ("## 激活时", "## 工作流", "## 结构", "## 规则"):
            self.assertIn(head, text)

    def test_mother_texts_verbatim(self):
        text = self.skill_text()
        for anchor in (MOTHER_1, MOTHER_2, MOTHER_3A, MOTHER_3B, MOTHER_3C,
                       MOTHER_3D, MOTHER_4, MOTHER_5, MOTHER_6):
            with self.subTest(anchor=anchor[:24]):
                self.assertIn(anchor, text)

    def test_final_gate_points_at_own_engine(self):
        text = self.skill_text()
        self.assertIn("wds_evolution.py", text)
        self.assertIn("check --final", text)
        self.assertIn("diyc.py check --type", text)     # 只以否定句出现

    def test_no_previous_teaching(self):
        """红线：不得教 diyc.py check --type <WDS 型> --previous。"""
        text = self.skill_text()
        self.assertNotIn("check --type wds", text)
        self.assertNotIn("--type evolution", text)
        self.assertNotIn("--previous", text.replace("无 `--previous` 轮", ""))

    def test_frontmatter_contract(self):
        text = self.skill_text()
        self.assertTrue(text.startswith("---\n"))
        head = text.split("---")[1]
        self.assertIn("name: diy-wds-evolution", head)
        self.assertIn("phase: 3-wds-build", head)
        self.assertIn("precededBy: []", head)
        self.assertIn("followedBy: []", head)
        self.assertIn("required: false", head)
        self.assertIn("line: wds", head)
        self.assertIn("outputs: wds-evolution.yaml", head)

    def test_product_path_declared(self):
        self.assertIn("wds-evolution.yaml", self.skill_text())

    def test_steps_files_and_section_counts(self):
        expect = {"01-analyze.md": 4, "02-scope.md": 5, "03-design.md": 5,
                  "04-implement.md": 5, "05-test.md": 5, "06-finish.md": 3}
        present = sorted(f for f in os.listdir(STEPS_DIR) if f.endswith(".md"))
        self.assertEqual(present, sorted(expect))
        for name, count in expect.items():
            with self.subTest(step=name):
                with open(os.path.join(STEPS_DIR, name), encoding="utf-8") as fh:
                    text = fh.read()
                self.assertEqual(text.count("\n## 第 "), count)
                self.assertIn("**Read (input):**", text)
                self.assertIn("**Write (output):**", text)
                self.assertIn("检查点（六拍）", text)
                self.assertIn("diy-elicit", text)
                self.assertIn("diy-party-mode", text)

    def test_data_files_carry_kaizen_core(self):
        with open(os.path.join(DATA_DIR, "kaizen-principles.md"), encoding="utf-8") as fh:
            kp = fh.read()
        for anchor in ("Kaizen", "Kaikaku", "改善", "改革", "無駄",
                       "Impact", "Effort", "Learning", "何时暂停"):
            self.assertIn(anchor, kp, anchor)
        with open(os.path.join(DATA_DIR, "priority-framework.md"), encoding="utf-8") as fh:
            pf = fh.read()
        for anchor in ("Impact", "Effort", "Learning", "high", "medium", "low"):
            self.assertIn(anchor, pf, anchor)


if __name__ == "__main__":
    unittest.main()
