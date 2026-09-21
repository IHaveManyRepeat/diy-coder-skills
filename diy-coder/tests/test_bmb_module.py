# -*- coding: utf-8 -*-
"""diy-bmb-module 确定性引擎 e2e 测试（批次规划器：只规划不造）。

覆盖 §2.5 W2 清单 ①–⑫（外加两条本面自加用例 ⑬/⑭）：
- 用例 1：`new` 建计划骨架且 MP-### 序号连续；同 slug 就地更新（不新建）
- 用例 2：`new` 重复 slug 拒绝（exit 1 + 指认既有 MP-xxx + 零写入）
- 用例 3：`check` 检出技能清单引用越界（UNKNOWN_ID——depends_on / build_order）
- 用例 4：`check` 检出六字段缺失（EMPTY_FIELD——限「本批新建」标记的技能）
- 用例 5：`--previous` 检出 skill 条目丢失（ID_UNSTABLE；**按 slug 配对**，MP-### 重铸仍能配对）
- 用例 6：`--previous` 对 `dropped: true` 放行
- 用例 7：`--final` 对未定稿拒绝 + `plans: []` / `skills: []` 空态拒绝（非 --final 只记 warning）
- 用例 8：契约冒烟（--json 单行 + 共同键齐全 + where 正斜杠相对；无 --json 时逐行 + 汇总行；
           `new` 的命令级附加键 plan_id/slug/file；--output-dir 必填 → 用法错误 exit 2）
- 用例 9：只读面断言（校验零写入——被校验技能与计划文件逐字节不变、无 .tmp 残骸）
- 用例 10：存量技能缺字段只记 warning 不判红
- 用例 11：`--previous` 坏路径 → MISSING_FILE 拒绝 + 零写入
- 用例 12：未解析 `{...}` 令牌 → TOKEN_UNRESOLVED（`{project-root}` 由引擎按 --project-root 自解析）
- 用例 13：双向对称（SET_MISMATCH：计划内单向链接）+ 悬空指向（UNKNOWN_ID）+ 相位双轨
           （`any` 与 `anytime` 等价，不判不对称）
- 用例 14：SKILL.md / steps 契约冒烟（母本 §1/§2/§3/§4/§5/§6/§7/§8 逐字 + 四段中文标题
           ≤90 行 + frontmatter 六字段 + 零写面声明 + steps 形态）
夹具全部落 tempdir 自建；不读写本仓库真实 diy-output；不依赖本机 git 状态。
运行：cd diy-coder && python -m unittest discover -s tests -p "test_bmb_module.py" -v
"""
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.join(HERE, "..", "skills", "diy-bmb-module")
ENGINE = os.path.join(SKILL_DIR, "scripts", "bmb_module.py")
SKILL_MD_PATH = os.path.join(SKILL_DIR, "SKILL.md")
STEPS_DIR = os.path.join(SKILL_DIR, "steps")
NL = chr(10)

FRONTMATTER_SIX = ("phase", "precededBy", "followedBy", "required", "line", "outputs")

# 六字段齐备的 SKILL.md（本批新建技能的合规形态）
FULL_SKILL = NL.join([
    "---",
    "name: {name}",
    "description: 'sample'",
    "phase: {phase}",
    "precededBy: [{preceded}]",
    "followedBy: [{followed}]",
    "required: false",
    "line: any",
    "outputs: 技能目录树",
    "---",
    "",
    "# {name}",
    "",
    "正文一句。",
]) + NL

BARE_SKILL = NL.join(["# {name}", "", "没有 frontmatter 的存量技能。"]) + NL

PLAN_HEAD = NL.join([
    "project:",
    "  name: mini",
    "  created: '2026-09-20'",
    "  updated: '2026-09-20'",
    "plans:",
]) + NL

# 两个成员：builder（followedBy → module）与 module（precededBy → builder），双向对称
PLAN_BODY = NL.join([
    "- id: MP-001",
    "  slug: b5-meta",
    "  title: B5 元能力批次",
    "  status: 草稿",
    "  date: '2026-09-20'",
    "  vision: 给 diy 套件补三个元能力技能",
    "  skills:",
    "  - {name: diy-bmb-builder, kind: 工作流, purpose: 造技能, brief: 见 SKILL.md 契约"
    ", depends_on: [diy-bmb-module], dropped: false, new: true}",
    "  - {name: diy-bmb-module, kind: 工具, purpose: 规划批次, brief: 见 SKILL.md 契约"
    ", depends_on: [], dropped: false, new: true}",
    "  dependencies: [diy-bmb-module]",
    "  build_order: [diy-bmb-module, diy-bmb-builder]",
    "  open_questions: []",
])
PLAN_YAML = PLAN_HEAD + PLAN_BODY + NL + "revisions: []" + NL


def run_engine(args, cwd=None):
    return subprocess.run([sys.executable, ENGINE] + args,
                          capture_output=True, text=True, encoding="utf-8", cwd=cwd)


class EngineCase(unittest.TestCase):
    """tmp 项目根 + diy-output + 安装面技能树的公共夹具。

    查找两面（权威 = `{project-root}/.claude/skills`、第二 = `{project-root}/diy-coder/skills`）
    都由 tempdir 承载，第二面默认不存在 → 用例结果不随本机真实技能树漂移。
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="bmb-module-")
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

    def skill(self, name, preceded=(), followed=(), full=True, phase="anytime"):
        text = (FULL_SKILL if full else BARE_SKILL).format(
            name=name, phase=phase, preceded=", ".join(preceded),
            followed=", ".join(followed))
        return self.write(os.path.join(".claude", "skills", name, "SKILL.md"), text)

    def snapshot(self, top):
        """目录快照（相对路径 → 内容），用于零写入断言。"""
        root = os.path.join(self.root, top)
        seen = {}
        for dirpath, _dirs, files in os.walk(root):
            for name in files:
                path = os.path.join(dirpath, name)
                with io.open(path, "rb") as f:
                    seen[os.path.relpath(path, self.root).replace(os.sep, "/")] = f.read()
        return seen

    def new(self, *extra):
        return run_engine(["new", "--project-root", self.root,
                           "--output-dir", self.out, "--json"] + list(extra))

    def check(self, *extra):
        return run_engine(["check", "--project-root", self.root,
                           "--output-dir", self.out, "--json"] + list(extra))

    def write_plan(self, text):
        return self.write("diy-output/module-plan.yaml", text)

    def codes(self, result):
        return [item["code"] for item in json.loads(result.stdout)["violations"]]

    def warn_codes(self, result):
        return [item["code"] for item in json.loads(result.stdout)["warnings"]]


class NewTests(EngineCase):

    # trace: 用例 1 · new（MP-### 序号连续；同 slug 更新走记录就地编辑，不新建）
    def test_new_mints_sequential_ids_and_rejects_repeat_slug(self):
        r1 = self.new("--slug", "b5-meta", "--title", "B5 元能力批次")
        self.assertEqual(r1.returncode, 0, r1.stdout + r1.stderr)
        data = json.loads(r1.stdout)
        self.assertEqual(data["plan_id"], "MP-001")
        self.assertEqual(data["slug"], "b5-meta")
        self.assertTrue(data["ok"])

        r2 = self.new("--slug", "b6-next", "--title", "B6 批量")
        self.assertEqual(r2.returncode, 0, r2.stdout + r2.stderr)
        self.assertEqual(json.loads(r2.stdout)["plan_id"], "MP-002")

        with io.open(os.path.join(self.out, "module-plan.yaml"), encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn("id: MP-001", text)
        self.assertIn("id: MP-002", text)
        self.assertIn("status: 草稿", text)

    # trace: 用例 2 · new（重复 slug → 拒绝 + 指认既有 MP-xxx + 零写入）
    def test_new_duplicate_slug_refused_with_zero_write(self):
        self.assertEqual(self.new("--slug", "b5-meta").returncode, 0)
        before = self.snapshot("diy-output")
        r = self.new("--slug", "b5-meta")
        self.assertEqual(r.returncode, 1, r.stdout)
        data = json.loads(r.stdout)
        self.assertFalse(data["ok"])
        self.assertEqual(self.codes(r), ["DUPLICATE_ID"])
        self.assertIn("MP-001", data["violations"][0]["msg"])
        self.assertEqual(self.snapshot("diy-output"), before, "拒绝路径不得落盘")

    # trace: 门禁 ③ · new（slug 缺失 → 一行 missing_slug 语义说明 + 零产出）
    def test_new_missing_slug_refused(self):
        r = self.new()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("missing_slug", r.stderr)
        self.assertEqual(self.codes(r), ["EMPTY_FIELD"])
        self.assertFalse(os.path.exists(os.path.join(self.out, "module-plan.yaml")))


class CheckTests(EngineCase):

    def setUp(self):
        super(CheckTests, self).setUp()
        self.skill("diy-bmb-builder", followed=["diy-bmb-module"])
        self.skill("diy-bmb-module", preceded=["diy-bmb-builder"])

    # trace: 契约 check（合法计划 → exit 0 唯一放行）
    def test_check_legal_plan_passes(self):
        self.write_plan(PLAN_YAML)
        r = self.check()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertTrue(data["ok"])
        self.assertEqual(data["violations"], [])
        self.assertEqual(data["warnings"], [])
        self.assertEqual(data["counts"]["plans"], 1)
        self.assertEqual(data["counts"]["skills"], 2)

    # trace: 用例 3 · check（引用越界 → UNKNOWN_ID：depends_on 与 build_order 两处）
    def test_check_reference_closure_unknown_id(self):
        self.write_plan(PLAN_YAML.replace("depends_on: [diy-bmb-module]", "depends_on: [diy-nope]"))
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertEqual(self.codes(r), ["UNKNOWN_ID"])
        self.assertIn("diy-nope", json.loads(r.stdout)["violations"][0]["msg"])

        self.write_plan(PLAN_YAML.replace("build_order: [diy-bmb-module, diy-bmb-builder]",
                                          "build_order: [diy-bmb-module, diy-ghost]"))
        r2 = self.check()
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertIn("UNKNOWN_ID", self.codes(r2))

    # trace: 用例 3b · check（指向已装技能 = 合法的「依赖既有能力」→ warning 不判红）
    def test_check_installed_reference_warns_not_red(self):
        self.skill("diy-elicit")
        self.write_plan(PLAN_YAML.replace("depends_on: [diy-bmb-module]",
                                          "depends_on: [diy-bmb-module, diy-elicit]"))
        r = self.check()
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertEqual(json.loads(r.stdout)["violations"], [])
        self.assertIn("对端在计划外", json.loads(r.stdout)["warnings"][0]["msg"])

    # trace: 用例 4 · check（六字段缺失 → EMPTY_FIELD，限「本批新建」标记的技能）
    def test_check_new_skill_missing_frontmatter_fields(self):
        self.skill("diy-bmb-builder", full=False)
        self.write_plan(PLAN_YAML)
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        data = json.loads(r.stdout)
        self.assertEqual(sorted(set(self.codes(r))), ["EMPTY_FIELD"])
        self.assertEqual(len(data["violations"]), 1, data["violations"])
        msg = data["violations"][0]["msg"]
        self.assertIn("diy-bmb-builder", msg)
        for field in FRONTMATTER_SIX:
            self.assertIn(field, msg, "六字段缺失须逐个点名：缺 %s" % field)

    # trace: 用例 10 · check（存量技能缺字段只记 warning 不判红——W2 零写面改不了）
    def test_check_legacy_skill_missing_fields_is_warning_only(self):
        self.skill("diy-bmb-builder", full=False)
        text = PLAN_YAML.replace(
            "{name: diy-bmb-builder, kind: 工作流, purpose: 造技能, brief: 见 SKILL.md 契约"
            ", depends_on: [diy-bmb-module], dropped: false, new: true}",
            "{name: diy-bmb-builder, kind: 工作流, purpose: 造技能, brief: 见 SKILL.md 契约"
            ", depends_on: [diy-bmb-module], dropped: false, new: false}")
        self.write_plan(text)
        r = self.check()
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertEqual(json.loads(r.stdout)["violations"], [])
        self.assertEqual(sorted(set(self.warn_codes(r))), ["EMPTY_FIELD"])
        self.assertIn("存量", json.loads(r.stdout)["warnings"][0]["msg"])

    # trace: 用例 10b · check（计划声明的技能尚未建造 → MISSING_FILE warning，不阻断）
    def test_check_missing_skill_is_warning_not_red(self):
        self.write_plan(PLAN_YAML.replace("{name: diy-bmb-module, kind: 工具",
                                          "{name: diy-not-yet-built-1, kind: 工具"))
        r = self.check()
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertEqual(json.loads(r.stdout)["violations"], [])
        self.assertIn("MISSING_FILE", self.warn_codes(r))

    # trace: 用例 13 · check（双向对称：计划内单向链接 → SET_MISMATCH；相位 any/anytime 等价）
    def test_check_bilateral_symmetry_and_phase_spelling(self):
        self.skill("diy-bmb-builder", followed=[])          # 单向：module 说 builder 在前，builder 不认
        self.write_plan(PLAN_YAML)
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertEqual(self.codes(r), ["SET_MISMATCH"])
        self.assertIn("双向对称", json.loads(r.stdout)["violations"][0]["msg"])

        # 两侧相位拼写不同（any / anytime）不构成不对称
        self.skill("diy-bmb-builder", followed=["diy-bmb-module"], phase="any")
        self.write_plan(PLAN_YAML)
        r2 = self.check()
        self.assertEqual(r2.returncode, 0, r2.stdout)
        self.assertEqual(json.loads(r2.stdout)["violations"], [])
        self.assertEqual(json.loads(r2.stdout)["counts"]["phases"], {"anytime": 2})

    # trace: 用例 13b · check（悬空指向 → UNKNOWN_ID——补源侧「指向真实能力」等价面）
    def test_check_dangling_link_is_unknown_id(self):
        self.skill("diy-bmb-builder", followed=["diy-bmb-module", "diy-nowhere"])
        self.write_plan(PLAN_YAML)
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("UNKNOWN_ID", self.codes(r))
        joined = " ".join(item["msg"] for item in json.loads(r.stdout)["violations"])
        self.assertIn("diy-nowhere", joined)

    # trace: 用例 7 · check --final（未定稿 / 空态一律拒绝；非 --final 只记 warning）
    def test_check_final_gates(self):
        self.write_plan(PLAN_YAML)
        r = self.check("--final")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertEqual(self.codes(r), ["STATUS_MISMATCH"])
        self.assertIn("已定稿", json.loads(r.stdout)["violations"][0]["msg"])

        # 定稿态 + 零 [假设] → 放行
        self.write_plan(PLAN_YAML.replace("status: 草稿", "status: 已定稿"))
        r2 = self.check("--final")
        self.assertEqual(r2.returncode, 0, r2.stdout)
        self.assertEqual(json.loads(r2.stdout)["violations"], [])

        # 零 [假设]：定稿稿含该字面量 → ASSUMPTION_PRESENT
        self.write_plan(PLAN_YAML.replace("status: 草稿", "status: 已定稿")
                        .replace("vision: 给 diy 套件补三个元能力技能",
                                 "vision: 给 diy 套件补三个元能力技能（[假设]）"))
        r3 = self.check("--final")
        self.assertEqual(r3.returncode, 1, r3.stdout)
        self.assertEqual(self.codes(r3), ["ASSUMPTION_PRESENT"])

    # trace: 用例 7b · check（plans: [] / skills: [] 空态：非 --final 过 + warning，--final 拒绝）
    def test_check_empty_states(self):
        self.write_plan(PLAN_HEAD.rstrip(NL) + " []" + NL + "revisions: []" + NL)
        r = self.check()
        self.assertEqual(r.returncode, 0, r.stdout)
        data = json.loads(r.stdout)
        self.assertEqual(data["violations"], [])
        self.assertEqual(self.warn_codes(r), ["EMPTY_FIELD"])
        self.assertEqual(data["counts"]["plans"], 0)
        r2 = self.check("--final")
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertEqual(self.codes(r2), ["EMPTY_FIELD"])

        empty_record = NL.join([
            "- id: MP-001",
            "  slug: b5-meta",
            "  title: B5 元能力批次",
            "  status: 草稿",
            "  date: '2026-09-20'",
            "  vision: 给 diy 套件补三个元能力技能",
            "  skills: []",
            "  dependencies: []",
            "  build_order: []",
            "  open_questions: []",
        ]) + NL
        self.write_plan(PLAN_HEAD + empty_record + "revisions: []" + NL)
        r3 = self.check()
        self.assertEqual(r3.returncode, 0, r3.stdout)
        self.assertEqual(json.loads(r3.stdout)["violations"], [])
        self.assertEqual(self.warn_codes(r3), ["EMPTY_FIELD"])
        self.assertEqual(json.loads(r3.stdout)["counts"]["skills"], 0)
        r4 = self.check("--final")
        self.assertEqual(r4.returncode, 1, r4.stdout)
        self.assertIn("EMPTY_FIELD", self.codes(r4), "空 skills 在 --final 下一律拒绝")
        self.assertIn("STATUS_MISMATCH", self.codes(r4), "草稿不得过终门")

    # trace: 契约 check（schema 违规表：id 形态 / 重复 ID / status 枚举 / kind 枚举 / 命名）
    def test_check_schema_violations(self):
        cases = [
            ("ENUM_INVALID", "id: MP-001", "id: MP-1", "id 须为 MP-###"),
            ("ENUM_INVALID", "status: 草稿", "status: draft", "status 枚举越界"),
            ("ENUM_INVALID", "kind: 工作流", "kind: agent", "kind 枚举越界"),
            ("NAME_ILLEGAL", "name: diy-bmb-builder", "name: Diy_bmb_builder", "非 hyphen-case"),
            ("EMPTY_FIELD", "  vision: 给 diy 套件补三个元能力技能" + NL, "", "vision 缺失"),
        ]
        for code, old, new, note in cases:
            self.write_plan(PLAN_YAML.replace(old, new))
            r = self.check()
            self.assertEqual(r.returncode, 1, "%s 未拒：%s" % (note, r.stdout))
            self.assertIn(code, self.codes(r), "%s 未报 %s：%s" % (note, code, r.stdout))

        # 顶层出现 status（多记录产物顶层不设 status → STATUS_MISMATCH）
        self.write_plan(PLAN_YAML.replace("plans:" + NL, "status: 草稿" + NL + "plans:" + NL))
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("STATUS_MISMATCH", self.codes(r))

        # 计划内技能名重复（名字即引用键，须唯一）
        self.write_plan(PLAN_YAML.replace("  - {name: diy-bmb-module, kind: 工具",
                                          "  - {name: diy-bmb-builder, kind: 工具"))
        r6 = self.check()
        self.assertEqual(r6.returncode, 1, r6.stdout)
        self.assertIn("DUPLICATE_ID", self.codes(r6))

        # 重复记录 ID
        block = PLAN_BODY + NL
        self.write_plan(PLAN_HEAD + block + block + "revisions: []" + NL)
        r2 = self.check()
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertIn("DUPLICATE_ID", self.codes(r2))

        # --id 指认不存在的记录 → UNKNOWN_ID
        self.write_plan(PLAN_YAML)
        r3 = self.check("--id", "MP-009")
        self.assertEqual(r3.returncode, 1, r3.stdout)
        self.assertEqual(self.codes(r3), ["UNKNOWN_ID"])

        # 缺文件 / YAML 损坏
        os.remove(os.path.join(self.out, "module-plan.yaml"))
        r4 = self.check()
        self.assertEqual(r4.returncode, 1, r4.stdout)
        self.assertEqual(self.codes(r4), ["MISSING_FILE"])
        self.write_plan("plans: [" + NL)
        r5 = self.check()
        self.assertEqual(r5.returncode, 1, r5.stdout)
        self.assertEqual(self.codes(r5), ["UNPARSABLE_YAML"])

    # trace: 用例 8 · 契约冒烟（--json 共同键 + where 正斜杠相对 + counts + 命令级附加键）
    def test_receipt_contract(self):
        common = {"ok", "command", "project_root", "output_dir", "violations",
                  "warnings", "counts"}
        self.write_plan(PLAN_YAML.replace("depends_on: [diy-bmb-module]", "depends_on: [diy-nope]"))
        r = self.check()
        self.assertEqual(len(r.stdout.strip().splitlines()), 1, "check --json 须单行")
        data = json.loads(r.stdout)
        self.assertTrue(common <= set(data), "check 回执缺共同键")
        self.assertEqual(data["command"], "check")
        self.assertEqual(data["project_root"], self.root)
        self.assertEqual(data["output_dir"], self.out.replace("\\", "/"))
        for item in data["violations"]:
            self.assertNotIn("\\", item["where"])
            self.assertFalse(item["where"].startswith("/"), item["where"])
        self.assertTrue(data["counts"])

        r2 = run_engine(["check", "--project-root", self.root, "--output-dir", self.out])
        self.assertEqual(r2.returncode, 1, r2.stdout)
        lines = [ln for ln in r2.stdout.strip().splitlines() if ln.strip()]
        self.assertTrue(lines[0].startswith("UNKNOWN_ID "), lines[0])
        self.assertTrue(lines[-1].startswith("汇总："), r2.stdout)

        r3 = self.new("--slug", "receipt-check")
        self.assertEqual(r3.returncode, 0, r3.stdout + r3.stderr)
        data3 = json.loads(r3.stdout)
        self.assertTrue(common <= set(data3), "new 回执缺共同键")
        for key in ("plan_id", "slug", "file"):
            self.assertIn(key, data3, "new 回执缺命令级附加键 %s" % key)

    # trace: 契约（用法错误 exit 2：--output-dir 必填 / 无子命令）
    def test_required_arguments(self):
        self.assertEqual(run_engine(["check", "--project-root", self.root]).returncode, 2)
        self.assertEqual(run_engine(["new", "--project-root", self.root, "--slug", "x"]).returncode, 2)
        self.assertEqual(run_engine(["--project-root", self.root]).returncode, 2)


class ReadOnlyFaceTests(EngineCase):

    # trace: 用例 9 · 只读面（校验零写入——被校验技能与计划文件逐字节不变、无 .tmp 残骸）
    def test_check_writes_nothing(self):
        self.skill("diy-bmb-builder", followed=["diy-bmb-module"])
        self.skill("diy-bmb-module", preceded=["diy-bmb-builder"])
        self.write_plan(PLAN_YAML)
        before_skills = self.snapshot(os.path.join(".claude", "skills"))
        before_plan = self.snapshot("diy-output")
        r = self.check("--final", "--previous", os.path.join(self.out, "module-plan.yaml"))
        self.assertIn(r.returncode, (0, 1), r.stdout + r.stderr)
        self.assertEqual(self.snapshot(os.path.join(".claude", "skills")), before_skills,
                         "check 不得写任何被校验技能的文件（frontmatter 亦然）")
        self.assertEqual(self.snapshot("diy-output"), before_plan,
                         "check 不得写计划文件，也不得留 .tmp 残骸")
        leftover = [p for p in self.snapshot(os.path.join(".claude", "skills")) if p.endswith(".tmp")]
        self.assertEqual(leftover, [])

    # trace: 用例 11 · check（--previous 坏路径 → MISSING_FILE 拒绝 + 零写入）
    def test_previous_bad_path_is_missing_file_with_zero_write(self):
        self.skill("diy-bmb-builder", followed=["diy-bmb-module"])
        self.skill("diy-bmb-module", preceded=["diy-bmb-builder"])
        self.write_plan(PLAN_YAML)
        before_skills = self.snapshot(os.path.join(".claude", "skills"))
        before_plan = self.snapshot("diy-output")
        r = self.check("--previous", os.path.join(self.root, "no-such-prev.yaml"))
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertNotIn("Traceback", r.stderr)
        self.assertEqual(self.codes(r), ["MISSING_FILE"])
        self.assertIn("no-such-prev.yaml", json.loads(r.stdout)["violations"][0]["where"])
        self.assertEqual(self.snapshot("diy-output"), before_plan)
        self.assertEqual(self.snapshot(os.path.join(".claude", "skills")), before_skills)

    # trace: 用例 12 · 令牌处置（{project-root} 自解析；其余 {...} → TOKEN_UNRESOLVED 零写入）
    def test_unresolved_token_rejected(self):
        self.skill("diy-bmb-builder", followed=["diy-bmb-module"])
        self.skill("diy-bmb-module", preceded=["diy-bmb-builder"])
        self.write_plan(PLAN_YAML)
        self.write(".claude/prev.yaml", PLAN_YAML)

        r = self.check("--previous", "{project-root}/.claude/prev.yaml")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertEqual(json.loads(r.stdout)["violations"], [])

        r2 = self.check("--previous", "{output_dir}/prev.yaml")
        self.assertEqual(r2.returncode, 1, r2.stdout)
        self.assertEqual(self.codes(r2), ["TOKEN_UNRESOLVED"])

        r3 = self.check("--skills-root", "{project-root}/.claude/skills")
        self.assertEqual(r3.returncode, 0, r3.stdout)

        r4 = self.check("--skills-root", "{instance}/skills")
        self.assertEqual(r4.returncode, 1, r4.stdout)
        self.assertEqual(self.codes(r4), ["TOKEN_UNRESOLVED"])

        r5 = run_engine(["new", "--project-root", self.root, "--output-dir", "{output_dir}",
                         "--slug", "t", "--json"])
        self.assertEqual(r5.returncode, 1, r5.stdout)
        self.assertEqual(self.codes(r5), ["TOKEN_UNRESOLVED"])

    # trace: 用例 12b · --skills-root 换第一面（第二面 = 套件源树，两面都查不到才判缺失）
    def test_skills_root_replaces_first_face(self):
        alt = tempfile.TemporaryDirectory(prefix="bmb-alt-")
        self.addCleanup(alt.cleanup)
        for name, preceded, followed in (("diy-bmb-builder", (), ("diy-bmb-module",)),
                                         ("diy-bmb-module", ("diy-bmb-builder",), ())):
            path = os.path.join(alt.name, name)
            os.makedirs(path, exist_ok=True)
            with io.open(os.path.join(path, "SKILL.md"), "w", encoding="utf-8") as f:
                f.write(FULL_SKILL.format(name=name, phase="anytime",
                                          preceded=", ".join(preceded),
                                          followed=", ".join(followed)))
        self.skill("diy-bmb-module", preceded=["diy-bmb-builder"])
        self.write_plan(PLAN_YAML)
        self.assertIn("MISSING_FILE", self.warn_codes(self.check()))
        r = self.check("--skills-root", alt.name)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertEqual(json.loads(r.stdout)["warnings"], [])


class PreviousTests(EngineCase):

    def setUp(self):
        super(PreviousTests, self).setUp()
        self.skill("diy-bmb-builder", followed=["diy-bmb-module"])
        self.skill("diy-bmb-module", preceded=["diy-bmb-builder"])

    def prev_text(self, extra_skill, plan_id="MP-007"):
        """旧稿：同 slug、**不同 MP-###**（配对键是 slug，不是 id）。"""
        entry = ("  - {name: %s, kind: 工具, purpose: 旧条目, brief: 见 SKILL.md 契约"
                 ", depends_on: [], dropped: false, new: false}" % extra_skill)
        return (PLAN_YAML.replace("  dependencies: [diy-bmb-module]",
                                  entry + NL + "  dependencies: [diy-bmb-module]")
                .replace("id: MP-001", "id: " + plan_id))

    # trace: 用例 5 · check --previous（旧稿有而新稿无的条目 → ID_UNSTABLE；按 slug 配对）
    def test_previous_detects_dropped_skill_by_slug(self):
        self.write(".claude/prev.yaml", self.prev_text("diy-gone"))
        self.write_plan(PLAN_YAML)
        r = self.check("--previous", os.path.join(self.root, ".claude", "prev.yaml"))
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertEqual(self.codes(r), ["ID_UNSTABLE"])
        self.assertIn("diy-gone", json.loads(r.stdout)["violations"][0]["msg"])
        self.assertIn("MP-007", json.loads(r.stdout)["violations"][0]["msg"])

        # 不同 slug 的旧记录不参与配对（不误报）
        self.write(".claude/prev.yaml", self.prev_text("diy-gone").replace("slug: b5-meta",
                                                                          "slug: other-batch"))
        r2 = self.check("--previous", os.path.join(self.root, ".claude", "prev.yaml"))
        self.assertEqual(r2.returncode, 0, r2.stdout)
        self.assertEqual(json.loads(r2.stdout)["violations"], [])

    # trace: 用例 6 · check --previous（新稿保留条目并标 dropped: true → 放行）
    def test_previous_allows_dropped_marker(self):
        self.write(".claude/prev.yaml", self.prev_text("diy-gone"))
        self.write_plan(PLAN_YAML.replace(
            "  dependencies: [diy-bmb-module]",
            "  - {name: diy-gone, kind: 工具, purpose: 已裁, brief: 见 SKILL.md 契约"
            ", depends_on: [], dropped: true, new: false}" + NL + "  dependencies: [diy-bmb-module]"))
        r = self.check("--previous", os.path.join(self.root, ".claude", "prev.yaml"))
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertEqual(json.loads(r.stdout)["violations"], [])

    # trace: 用例 5b · check --previous（--id 缩域：只校验被点名的记录）
    def test_previous_scoped_by_id(self):
        self.write(".claude/prev.yaml", self.prev_text("diy-gone"))
        self.write_plan(PLAN_YAML)
        r = self.check("--previous", os.path.join(self.root, ".claude", "prev.yaml"),
                       "--id", "MP-001")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertEqual(json.loads(r.stdout)["counts"]["checked"], 1)


# 套件级句式母本（`suite-texts.md` 中文定稿，逐字）——B5 批施工期比对
INSTANCE_ZH = ("实例解析（FR-4.5/D-9）由工具脚本执行：运行 "
               "`python \"{project-root}/.claude/skills/diy-tools/scripts/diyc.py\" "
               "resolve [--instance <name>] --json`，把回执里的 `output_dir` "
               "当作本次运行唯一的读写根目录。")
RESOLVE_KEYS_ZH = ("解析 `project.communication_language` / "
                   "`project.document_output_language` / `paths.output_dir`")
DEFAULT_CHAIN_ZH = ("缺省链：`paths.output_dir` 一律取 `diyc.py resolve` 回执"
                    "（引擎缺省 `diy-output`，异常形状降级并 warning）；"
                    "缺 `document_output_language` 落 `project.communication_language`；"
                    "两者皆缺则跟随用户当前消息的语言，并在收尾一行说明。")
INSTANCE_FLAG_ZH = ("实例名只在本次激活参数出现 `--instance <name>` 时才传"
                    "（无头侧入口 `runner.py --instance`；交互侧由用户在发起消息里给出同一旗标）；"
                    "未传时回执的 `output_dir` 即主线平铺根。")
READ_DISCIPLINE_ZH = ("读取纪律：预载预算 = 本文件、上述配置与回执、`steps/` 下当前那一个文件"
                      "——绝不批量预载；执行期读取以每个步骤开头的 `Read (input)` 行为唯一权威，"
                      "**主文件不列举封闭清单**。")
PRECISE_ZH = ("- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；"
              "不复述上游已写的信息（引用 ID）；不写没有信息量的套话。")
DISCIPLINE_ZH = ("- **写作纪律。** 主字段 = 大白话主句；数字/枚举内联；"
                 "机器语法（命令/旗标/路径）进括号；机器锚点逐字保留"
                 "（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 "
                 "`diy-design` 的 detect 启发式。schema 若定义 `plain`："
                 "一行写清该条目为什么存在，绝不写是什么（转述会漂移）；"
                 "只写难懂的条目。若定义 `detail`：过程叙述——结论留在主字段。")
RENDER_SILENT_ZH = ("渲染是静默旁路——只写调用命令，不新增「打开浏览器 / 报告路径等待查看 / "
                    "阻塞等待」交互点：`python \"{project-root}/.claude/skills/diy-viewer/"
                    "scripts/viewer.py\" --project-root \"{project-root}\"`"
                    "（resolved 实例时附 `--instance <name>`）。")
PATH_BASE_ZH = ("所有代码引用一律 project-root 相对 `path:line`（基准 = `{project-root}`，"
                "不随会话 CWD 变化；正斜杠；越界的文件用绝对路径）。")
STATUS_ZH = ("单记录产物（`sprint.yaml` 等）写 `project.status`；多记录产物（一份文件装 N 条记录）"
             "顶层不设 status，定稿态挂记录级 `status: 草稿|已定稿`。")
H1_RE = re.compile(r"^# Step (\d+) — .*[一-鿿]")


class SkillContractTests(unittest.TestCase):
    """用例 14：SKILL.md / steps 契约冒烟（母本逐字 + 四段 + 六字段 + 零写面）。"""

    def read(self, path):
        with io.open(path, encoding="utf-8") as f:
            return f.read()

    def read_skill(self):
        return self.read(SKILL_MD_PATH)

    # trace: 母本 §1/§3/§4/§5/§6/§7/§8（逐字复制，禁改写）
    def test_mother_texts_verbatim(self):
        raw = self.read_skill()
        for label, anchor in (("§1 实例解析句", INSTANCE_ZH),
                              ("§3 键路径", RESOLVE_KEYS_ZH),
                              ("§3 缺省链", DEFAULT_CHAIN_ZH),
                              ("§3 实例触发", INSTANCE_FLAG_ZH),
                              ("§4 读取纪律", READ_DISCIPLINE_ZH),
                              ("§5 渲染静默", RENDER_SILENT_ZH),
                              ("§6 精准简练", PRECISE_ZH),
                              ("§2 写作纪律块", DISCIPLINE_ZH),
                              ("§7 路径基准", PATH_BASE_ZH),
                              ("§8 产物状态口径", STATUS_ZH)):
            self.assertIn(anchor, raw, "SKILL.md 缺母本 %s（逐字）" % label)
        self.assertNotIn("Instance resolution (FR-4.5/D-9)", raw, "已转中文定稿，仍残留英文原形")

    # trace: 四段结构 + 行数预算（验收 #1）+ 标题含技能名
    def test_four_chinese_sections_and_budget(self):
        raw = self.read_skill()
        self.assertLessEqual(len(raw.splitlines()), 90, "薄主文件超出 90 行预算")
        for section in ("## 激活时", "## 工作流", "## 结构", "## 规则"):
            self.assertIn(section, raw, "缺四段结构：%s" % section)
        for legacy in ("## On Activation", "## Workflow", "## Schema", "## Rules"):
            self.assertNotIn(legacy, raw, "英文段名残留：%s" % legacy)
        self.assertIn("# diy-bmb-module", raw, "标题须含技能名")

    # trace: 登记元数据（§2.1 表：phase/anytime · precededBy/followedBy 空 · required false · line any）
    def test_frontmatter_registration(self):
        raw = self.read_skill()
        head = raw.split("---", 2)[1]
        self.assertIn("name: diy-bmb-module", head)
        for line in ("phase: anytime", "precededBy: []", "followedBy: []",
                     "required: false", "line: any", "outputs: module-plan.yaml"):
            self.assertIn(line, head, "frontmatter 缺登记行：%s" % line)
        self.assertIn("# ↑ 中文：", head, "frontmatter 缺中文注释行")
        self.assertRegex(head, r"Use when the user requests to")

    # trace: 零写面（§4 改造 5 / §2.6——不写任何被校验技能的文件，frontmatter 亦然）
    def test_zero_write_surface_declared(self):
        raw = self.read_skill()
        self.assertIn("零写面", raw, "规则段须声明零写面")
        self.assertIn("不写任何被校验技能的文件", raw, "缺只读面纪律句")
        self.assertIn("--previous", raw, "须写明 --previous 判 yes 的用法")

    # trace: steps 形态（4 文件 · H1 中文步名 · Read/Write 行逐字英文 · 结尾点名下一个文件）
    def test_steps_shape(self):
        names = ["01-ideate.md", "02-plan.md", "03-validate.md", "04-finish.md"]
        self.assertEqual(sorted(n for n in os.listdir(STEPS_DIR) if n.endswith(".md")), names,
                         "steps 文件集须与 §4 卡冻结的 4 文件一致")
        for i, name in enumerate(names, start=1):
            text = self.read(os.path.join(STEPS_DIR, name))
            lines = text.replace("\r\n", NL).split(NL)
            match = H1_RE.match(lines[0])
            self.assertTrue(match, "%s 的 H1 须为 '# Step N — <中文步名>'，实为 %r" % (name, lines[0]))
            self.assertEqual(int(match.group(1)), i, "%s 步号与文件序不符" % name)
            self.assertTrue(any(ln.startswith("**Read (input):**") for ln in lines),
                            "%s 缺 '**Read (input):**' 行" % name)
            self.assertTrue(any(ln.startswith("**Write (output):**") for ln in lines),
                            "%s 缺 '**Write (output):**' 行" % name)
            heads = [ln for ln in lines if ln.startswith("## ")]
            self.assertEqual(heads[-1], "## 播报与下一步", "%s 末段须为 '## 播报与下一步'" % name)
        last = self.read(os.path.join(STEPS_DIR, "04-finish.md"))
        self.assertIn("diy-bmb-builder", last, "末步须点名交棒对象 diy-bmb-builder")


if __name__ == "__main__":
    unittest.main()
