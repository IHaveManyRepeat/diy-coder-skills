# -*- coding: utf-8 -*-
"""diy-spec 确定性引擎 e2e 测试（通用契约蒸馏技能）。

覆盖（任务书 §6 测试节 10 项逐条对应）：
- 用例 1：new 建记录且 SK 序号连续（空文件 001 → 002；有空洞的稿 005 → 取 006，不重号）
- 用例 2：new 同 slug 拒绝（`DUPLICATE_ID` + 指出既有 SK-001 + 零写入）
- 用例 3：check 检出 CAP intent 缺失（`EMPTY_FIELD`）
- 用例 4：check 检出 CAP ID 重复（`DUPLICATE_ID`）
- 用例 5：check 检出 companions 路径不在场（`MISSING_FILE`；在场时 exit 0）
- 用例 6：check 检出 non_goals 空（Spec Law 4）
- 用例 7：--previous 检出 CAP 丢失且未标 retired（`ID_UNSTABLE`）
- 用例 8：--previous 对标了 retired 的退役 CAP 放行（旧稿标 retired / 新稿留痕标 retired 两态）
- 用例 9：--final 对 `verdict` 缺失拒绝（同稿非 --final exit 0）
- 用例 10：契约冒烟（SKILL.md 四段中文标题 + 母本 §1/§2/§3/§4/§5/§6 逐字 + 终门句
          指向本技能引擎 + 边界声明 / steps 四文件形态）
- 用例 11（补充，§2.5 ④ + 用法错误）：回执共同键完整 + `--output-dir` / `--slug` 必填
          （argparse 用法错误 exit 2）+ 人读态「每违规一行 + 汇总行」

夹具全部落 tempdir 自建；不读写本仓库真实 diy-output。
运行：cd diy-coder && python -m unittest discover -s tests -p "test_spec_kernel.py" -v
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
SKILL_DIR = os.path.join(HERE, "..", "skills", "diy-spec")
ENGINE = os.path.join(SKILL_DIR, "scripts", "spec_kernel.py")
SKILL_MD_PATH = os.path.join(SKILL_DIR, "SKILL.md")
STEPS_DIR = os.path.join(SKILL_DIR, "steps")
NL = chr(10)

SPEC_FILE = "spec-kernel.yaml"

# 合法稿：五字段齐备 + CAP 结构完整 + companions/sources 在场 + verdict 两段非空
GOOD = NL.join([
    "project:",
    "  name: mini",
    "  created: '2026-09-20'",
    "  updated: '2026-09-20'",
    "specs:",
    "- id: SK-001",
    "  slug: quarter-drop",
    "  title: 季度上新",
    "  status: 已定稿",
    "  date: '2026-09-20'",
    "  why: 用户在下单前看不到上新批次，只能靠猜。",
    "  capabilities:",
    "  - {id: CAP-1, intent: 用户能按季度筛选商品。, success: 筛选后只出现该季度商品，空季度给空态。}",
    "  constraints:",
    "  - 结算页不得新增交互步骤",
    "  non_goals:",
    "  - 不做跨季度比价",
    "  success_signal: 上线一周内，季度筛选出现在真实下单路径上。",
    "  assumptions: []",
    "  open_questions: []",
    "  companions: [docs/ux-design.md]",
    "  sources: [docs/prd.md]",
    "  artifacts:",
    "  - name: glossary",
    "    body: '季度：自然季度。'",
    "  verdict:",
    "    coherence: 五字段齐备，Law 1-6/8 通过。",
    "    preservation:",
    "      dropped: []",
    "      note: 逐声明走查完成，无静默丢弃。",
    "revisions: []",
]) + NL
GOOD_FILE = "diy-output/" + SPEC_FILE

VERDICT_BLOCK = NL.join([
    "  verdict:",
    "    coherence: 五字段齐备，Law 1-6/8 通过。",
    "    preservation:",
    "      dropped: []",
    "      note: 逐声明走查完成，无静默丢弃。",
]) + NL


def run_engine(args, cwd=None):
    return subprocess.run([sys.executable, ENGINE] + args,
                          capture_output=True, text=True, encoding="utf-8", cwd=cwd)


class EngineCase(unittest.TestCase):
    """tmp 项目根 + diy-output 目录的公共夹具（伴生材料按需落地）。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="spec-kernel-")
        self.root = self.tmp.name
        self.out = os.path.join(self.root, "diy-output")
        os.makedirs(self.out, exist_ok=True)
        self.write("docs/ux-design.md", "# 体验设计" + NL)
        self.write("docs/prd.md", "# PRD" + NL)

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

    def read(self, rel):
        with io.open(os.path.join(self.root, rel), encoding="utf-8") as f:
            return f.read()

    def exists(self, rel):
        return os.path.exists(os.path.join(self.root, rel))

    def new(self, slug, *extra):
        return run_engine(["new", "--slug", slug, "--project-root", self.root,
                           "--output-dir", self.out, "--json"] + list(extra))

    def check(self, *extra):
        return run_engine(["check", "--project-root", self.root,
                           "--output-dir", self.out, "--json"] + list(extra))

    def payload(self, result):
        return json.loads(result.stdout)

    def codes(self, result):
        return [item["code"] for item in self.payload(result)["violations"]]

    def write_spec(self, text, rel=GOOD_FILE):
        return self.write(rel, text)


class NewTests(EngineCase):

    # trace: B4 diy-spec 用例 1（new 建记录且 SK 序号连续；有空洞取最大值 + 1）
    def test_new_mints_records_with_continuous_ids(self):
        r1 = self.new("alpha")
        self.assertEqual(r1.returncode, 0, r1.stdout + r1.stderr)
        r2 = self.new("beta", "--title", "乙")
        self.assertEqual(r2.returncode, 0, r2.stdout + r2.stderr)
        data = self.payload(r2)
        self.assertTrue(data["ok"])
        self.assertEqual(data["counts"]["id"], "SK-002")
        records = self._records()
        self.assertEqual([x["id"] for x in records], ["SK-001", "SK-002"])
        self.assertEqual([x["slug"] for x in records], ["alpha", "beta"])
        self.assertEqual(records[0]["status"], "草稿")
        self.assertEqual(records[0]["date"], self.payload(r1)["updated"])
        self.assertEqual(data["updated"], self.payload(r1)["updated"])
        # 有空洞的稿：最大序号 + 1，绝不重号
        self.write_spec(NL.join([
            "project: {name: mini, created: '2026-09-20', updated: '2026-09-20'}",
            "specs:",
            "- id: SK-005",
            "  slug: gamma",
            "  status: 草稿",
            "revisions: []",
        ]) + NL)
        r3 = self.new("delta")
        self.assertEqual(r3.returncode, 0, r3.stdout + r3.stderr)
        self.assertEqual(self.payload(r3)["counts"]["id"], "SK-006")

    def _records(self):
        import yaml
        with io.open(os.path.join(self.out, SPEC_FILE), encoding="utf-8") as f:
            return yaml.safe_load(f)["specs"]

    # trace: B4 diy-spec 用例 2 + 验收 #3（同 slug 拒绝：零写入、指出既有记录）
    def test_new_rejects_duplicate_slug_with_zero_write(self):
        self.assertEqual(self.new("alpha").returncode, 0)
        before = self.read(GOOD_FILE)
        r = self.new("alpha")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        data = self.payload(r)
        self.assertFalse(data["ok"])
        self.assertEqual(self.codes(r), ["DUPLICATE_ID"])
        self.assertIn("SK-001", data["violations"][0]["msg"])
        self.assertEqual(self.read(GOOD_FILE), before, "拒绝路径必须零写入")


class CheckTests(EngineCase):

    # trace: B4 diy-spec 用例 3（CAP intent 双非空 —— Spec Law 1 的机械面）
    def test_check_flags_empty_capability_intent(self):
        self.write_spec(GOOD.replace("intent: 用户能按季度筛选商品。", "intent: ''"))
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        data = self.payload(r)
        self.assertEqual(self.codes(r), ["EMPTY_FIELD"])
        self.assertIn("capabilities[0].intent", data["violations"][0]["where"])
        self.assertEqual(data["counts"]["capabilities"], 1)

    # trace: B4 diy-spec 用例 4（CAP ID 记录内唯一 —— Spec Law 6）
    def test_check_flags_duplicate_capability_id(self):
        dup = GOOD.replace(
            "  constraints:",
            "  - {id: CAP-1, intent: 用户能按品牌筛选。 , success: 品牌筛选生效。}"
            + NL + "  constraints:")
        self.write_spec(dup)
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("DUPLICATE_ID", self.codes(r))
        self.assertIn("capabilities[1].id", self.payload(r)["violations"][0]["where"])

    # trace: B4 diy-spec 用例 5（companions 路径在场性，相对 project-root 解析）
    def test_check_flags_missing_companion_path(self):
        self.write_spec(GOOD)
        r = self.check()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(self.payload(r)["ok"])
        self.write_spec(GOOD.replace("[docs/ux-design.md]", "[docs/nope.md]"))
        r2 = self.check()
        self.assertEqual(r2.returncode, 1, r2.stdout + r2.stderr)
        data = self.payload(r2)
        self.assertEqual(self.codes(r2), ["MISSING_FILE"])
        self.assertIn("companions[0]", data["violations"][0]["where"])
        self.assertIn("docs/nope.md", data["violations"][0]["msg"])

    # trace: B4 diy-spec 用例 6（non_goals 至少一条 —— Spec Law 4）
    def test_check_flags_empty_non_goals(self):
        self.write_spec(GOOD.replace("  - 不做跨季度比价" + NL, ""))
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        data = self.payload(r)
        self.assertEqual(self.codes(r), ["EMPTY_FIELD"])
        self.assertIn("non_goals", data["violations"][0]["where"])
        self.assertIn("Spec Law 4", data["violations"][0]["msg"])

    # trace: B4 diy-spec 用例 9（--final 要求 verdict 两段非空；同稿非 --final 放行）
    def test_final_rejects_record_without_verdict(self):
        self.write_spec(GOOD.replace(VERDICT_BLOCK, ""))
        r = self.check()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        rf = self.check("--final")
        self.assertEqual(rf.returncode, 1, rf.stdout + rf.stderr)
        data = self.payload(rf)
        self.assertEqual(self.codes(rf), ["EMPTY_FIELD"])
        self.assertIn("verdict", data["violations"][0]["where"])
        self.assertEqual(data["counts"]["records"], 1)


class PreviousTests(EngineCase):

    # trace: B4 diy-spec 用例 7 + 验收 #4（--previous：CAP 旧有新无且未标 retired → ID_UNSTABLE）
    def test_previous_flags_lost_capability(self):
        prev = GOOD.replace(
            "  constraints:",
            "  - {id: CAP-2, intent: 用户能看上新日历。, success: 日历显示未来四批。}"
            + NL + "  constraints:")
        self.write_spec(prev, "old/spec-kernel.prev.yaml")
        self.write_spec(GOOD)
        r = self.check("--previous", "old/spec-kernel.prev.yaml")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        data = self.payload(r)
        self.assertEqual(self.codes(r), ["ID_UNSTABLE"])
        self.assertIn("CAP-2", data["violations"][0]["msg"])
        self.assertIn("SK-001", data["violations"][0]["where"])
        # 旧稿路径无效 → 结构化违规，不崩
        r2 = self.check("--previous", "old/nope.yaml")
        self.assertEqual(r2.returncode, 1, r2.stdout + r2.stderr)
        self.assertIn("MISSING_FILE", self.codes(r2))

    # trace: B4 diy-spec 用例 8（retired 豁免两态：旧稿标退役 / 新稿留痕标退役）
    def test_previous_exempts_retired_capability(self):
        prev_retired = GOOD.replace(
            "  constraints:",
            "  - {id: CAP-2, intent: 用户能看上新日历。, success: 日历显示未来四批。,"
            " retired: true}" + NL + "  constraints:")
        self.write_spec(prev_retired, "old/spec-kernel.prev.yaml")
        self.write_spec(GOOD)
        r = self.check("--previous", "old/spec-kernel.prev.yaml")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(self.payload(r)["ok"])
        # 新稿留痕：CAP-2 仍在 capabilities 里标 retired: true（退役保痕的常态路径）
        self.write_spec(GOOD.replace(
            "  constraints:",
            "  - {id: CAP-2, intent: 用户能看上新日历。, success: 日历显示未来四批。,"
            " retired: true}" + NL + "  constraints:"))
        r2 = self.check("--previous", "old/spec-kernel.prev.yaml")
        self.assertEqual(r2.returncode, 0, r2.stdout + r2.stderr)
        self.assertEqual(self.payload(r2)["counts"]["retired"], 1)


class ContractTests(EngineCase):

    # trace: B4 diy-spec 用例 11（回执共同键 + 用法错误 exit 2 + 人读态）
    def test_receipt_keys_and_usage_errors(self):
        self.write_spec(GOOD)
        data = self.payload(self.check())
        for key in ("ok", "command", "project_root", "output_dir",
                    "violations", "warnings", "counts"):
            self.assertIn(key, data, "回执缺共同键 %s" % key)
        self.assertNotIn("instance", data, "领域引擎回执不含 instance 键")
        self.assertEqual(data["command"], "check")
        self.assertEqual(data["project_root"], self.root, "project_root 记 as-given")
        self.assertEqual(data["output_dir"], self.out.replace("\\", "/"))
        self.assertIn("records", data["counts"])
        # 用法错误（argparse 默认 exit 2）
        r = run_engine(["check", "--project-root", self.root])
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        r2 = run_engine(["new", "--project-root", self.root, "--output-dir", self.out])
        self.assertEqual(r2.returncode, 2, r2.stdout + r2.stderr)
        # 人读态：每违规一行 `CODE where: msg` + 汇总行
        self.write_spec(GOOD.replace("  - 不做跨季度比价" + NL, ""))
        h = run_engine(["check", "--project-root", self.root, "--output-dir", self.out])
        self.assertEqual(h.returncode, 1, h.stdout + h.stderr)
        self.assertIn("EMPTY_FIELD " + GOOD_FILE, h.stdout)
        self.assertIn("汇总：", h.stdout)

    def read_text(self, path):
        with io.open(path, encoding="utf-8") as f:
            return f.read()

    # trace: B4 diy-spec 用例 10 + 母本 §1/§2/§3/§4/§5/§6（逐字）+ 终门句 + 边界声明
    def test_skill_contract_smoke(self):
        self.assertTrue(os.path.isfile(SKILL_MD_PATH), "缺 SKILL.md")
        raw = self.read_text(SKILL_MD_PATH)
        # 薄主文件 ≤90 行 + 四段中文标题（任务书 §2.1）
        self.assertLessEqual(len(raw.splitlines()), 90, "薄主文件超出 90 行预算")
        for section in ("## 激活时", "## 工作流", "## 结构", "## 规则"):
            self.assertIn(section, raw, "缺四段结构：%s" % section)
        for legacy in ("## On Activation", "## Workflow", "## Schema", "## Rules"):
            self.assertNotIn(legacy, raw, "英文段名残留：%s" % legacy)
        self.assertTrue(any(ln.startswith("# diy-spec") for ln in raw.splitlines()),
                        "一级标题须含技能名")
        # frontmatter 登记元数据（任务书 §2.1 表）
        for line in ("name: diy-spec", "phase: anytime", "required: false",
                     "outputs: spec-kernel.yaml"):
            self.assertIn(line, raw, "frontmatter 缺 %s" % line)
        # 母本 §1 中文定稿逐字
        self.assertIn(
            "实例解析（FR-4.5/D-9）由工具脚本执行：运行 "
            "`python \"{project-root}/.claude/skills/diy-tools/scripts/diyc.py\" "
            "resolve [--instance <name>] --json`，把回执里的 `output_dir` "
            "当作本次运行唯一的读写根目录。", raw, "缺母本 §1 中文定稿（逐字）")
        # 母本 §2 写作纪律块逐字
        self.assertIn(
            "- **写作纪律。** 主字段 = 大白话主句；数字/枚举内联；"
            "机器语法（命令/旗标/路径）进括号；机器锚点逐字保留"
            "（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 "
            "`diy-design` 的 detect 启发式。schema 若定义 `plain`："
            "一行写清该条目为什么存在，绝不写是什么（转述会漂移）；"
            "只写难懂的条目。若定义 `detail`：过程叙述——结论留在主字段。",
            raw, "缺母本 §2 写作纪律块（逐字）")
        # 母本 §3 / §4 / §5 / §6 锚串
        self.assertIn("解析 `project.communication_language` / "
                      "`project.document_output_language` / `paths.output_dir`", raw)
        self.assertIn("读取纪律：预载预算 = 本文件、上述配置与回执、`steps/` 下当前那一个文件"
                      "——绝不批量预载；执行期读取以每个步骤开头的 `Read (input)` 行为唯一权威，"
                      "**主文件不列举封闭清单**。", raw)
        self.assertIn("渲染是静默旁路——只写调用命令", raw)
        self.assertIn('diy-viewer/scripts/viewer.py" --project-root "{project-root}"', raw)
        self.assertIn("- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；"
                      "不复述上游已写的信息（引用 ID）；不写没有信息量的套话。", raw)
        # 终门句指向本技能引擎（验收 #12b）
        self.assertIn("scripts/spec_kernel.py", raw, "终门须指向自带引擎")
        # 边界声明两句（§0 裁定 4 双方 SKILL.md）+ diy-prd 区别句（§6 裁定 6）
        self.assertIn("spec.yaml", raw, "缺与 diy-quick-dev 的边界声明")
        self.assertIn("diy-quick-dev", raw)
        self.assertIn("diy-prd", raw, "缺与 diy-prd 的区别句")
        # steps 四文件（冻结步数 = 4）+ 形态（H1 中文步名 + Read/Write 行 + 末段点名下一步）
        names = ["01-input.md", "02-distill.md", "03-validate.md", "04-finish.md"]
        self.assertEqual(sorted(os.listdir(STEPS_DIR)), names, "steps 冻结为 4 文件")
        h1_re = re.compile(r"^# Step (\d+) — .*[一-鿿]")
        for i, name in enumerate(names, start=1):
            text = self.read_text(os.path.join(STEPS_DIR, name))
            lines = text.replace("\r\n", NL).split(NL)
            match = h1_re.match(lines[0])
            self.assertTrue(match, "%s 的 H1 须为 '# Step N — <中文步名>'，实为 %r"
                            % (name, lines[0]))
            self.assertEqual(int(match.group(1)), i, "%s 步号与文件序不符" % name)
            self.assertTrue(any(ln.startswith("**Read (input):**") for ln in lines),
                            "%s 缺 '**Read (input):**' 行" % name)
            self.assertTrue(any(ln.startswith("**Write (output):**") for ln in lines),
                            "%s 缺 '**Write (output):**' 行" % name)
            if i < len(names):
                self.assertIn(names[i], text, "%s 未点名下一个步骤文件" % name)


if __name__ == "__main__":
    unittest.main()
