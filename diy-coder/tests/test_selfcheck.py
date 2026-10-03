# -*- coding: utf-8 -*-
"""diy-selfcheck 契约冒烟（零引擎、零 YAML 写面、编排型技能）。

技能定位：任务书/规格自检的**编排者**（B3 taskbook §13 底子 + B4/B6/B7/C·7/C·15 机制融合）——
冻结锚点 → 三机制派发（预演片调 diy-spec-scan / 引用核对 / 对抗三层）→ 合并去重 →
D 表处置 → 旧值复扫两轮 → B 部分机制评价。机械面全复用（md5/grep 走 shell，
SS-### 与终门走 diy-spec-scan 引擎）——不得为凑测试造无意义引擎（party-mode 判例）。

本文件不含子进程用例，只做 SKILL.md / steps 契约冒烟：

  1. frontmatter 六字段登记值 + description 形态（英文单引号单行 + # ↑ 中文注释）
  2. 四段中文结构 + 薄主文件行数预算
  3. steps 五文件形态（H1 中文步名 + 步号与文件序一致 + Read/Write 行 + 末段播报）
  4. 关键机制锚串（三机制边界 / 禁共写 / 报总数 / 交叉置信 / D 表闭环 / 复扫两轮 /
     B 部分必出 / 拍板贯通三问 / SS-### 永不复用 / 锚点冻结）
  5. 与 diy-spec-scan 的边界声明双向一致（selfcheck=编排者 / spec-scan=预演片，
     对侧 04-report 路由段有归位句）

夹具：无（纯文本断言，不落 tempfile、不读写本仓库 `diy-output/`）。
运行：cd diy-coder && python -m unittest discover -s tests -p "test_selfcheck.py" -v

trace: B3 §13 编排规格固化（用户 2026-10-03 裁定：B3 底子 + 各批机制融合为新技能）；
       零 YAML 写面承 diy-party-mode 判例；双向边界承 diy-party-mode ↔ diy-review 先例。
"""
import io
import os
import re
import unittest

NL = "\n"
HERE = os.path.dirname(os.path.abspath(__file__))
SKILLS_DIR = os.path.join(HERE, "..", "skills")
SKILL_DIR = os.path.join(SKILLS_DIR, "diy-selfcheck")
SKILL_MD = os.path.join(SKILL_DIR, "SKILL.md")
STEPS_DIR = os.path.join(SKILL_DIR, "steps")
SPEC_SCAN_ROUTE = os.path.join(SKILLS_DIR, "diy-spec-scan", "steps", "04-report.md")
SPEC_SCAN_MD = os.path.join(SKILLS_DIR, "diy-spec-scan", "SKILL.md")

H1_RE = re.compile(r"^# Step (\d+) — .*[一-鿿]")
STEP_FILES = ["01-freeze.md", "02-dispatch.md", "03-merge.md",
              "04-dispose.md", "05-close.md"]

SECTIONS_ZH = ("## 激活时", "## 工作流", "## 产物", "## 规则")


def read(path):
    with io.open(path, encoding="utf-8") as fh:
        return fh.read()


class SkillContractTests(unittest.TestCase):

    def skill(self):
        return read(SKILL_MD)

    # trace: 六字段守卫先导自查 + 登记值（anytime 编排技能、无链序依赖、无 diy-output 产物）
    def test_registration_metadata(self):
        raw = self.skill()
        head = raw.split("## 激活时")[0]
        for line in ("name: diy-selfcheck", "phase: anytime", "precededBy: []",
                     "followedBy: []", "required: false", "line: any", "outputs: —"):
            self.assertIn(line, head, "frontmatter 缺登记项：%s" % line)
        self.assertIn("# ↑ 中文：", head, "缺 description 下方的中文注释行")
        self.assertRegex(head, r"description: '[^']+'",
                         "description 须为英文单引号单行")

    # trace: 四段中文结构 + 薄主文件预算（编排技能以步骤文件承载细节，主文件防膨胀）
    def test_four_chinese_sections_and_budget(self):
        raw = self.skill()
        for section in SECTIONS_ZH:
            self.assertIn(section, raw, "缺四段结构：%s" % section)
        for legacy in ("## On Activation", "## Workflow", "## Schema", "## Rules"):
            self.assertNotIn(legacy, raw, "英文段名残留：%s" % legacy)
        self.assertLessEqual(len(raw.splitlines()), 80, "薄主文件超出 80 行预算")

    # trace: steps 形态（H1 中文步名 + 步号与文件序一致 + Read/Write 行逐字 + 末段播报）
    def test_steps_shape(self):
        for i, name in enumerate(STEP_FILES, start=1):
            text = read(os.path.join(STEPS_DIR, name))
            lines = text.replace("\r\n", NL).split(NL)
            match = H1_RE.match(lines[0])
            self.assertTrue(match, "%s 的 H1 须为 '# Step N — <中文步名>'，实为 %r"
                            % (name, lines[0]))
            self.assertEqual(int(match.group(1)), i, "%s 步号与文件序不符" % name)
            self.assertTrue(any(ln.startswith("**Read (input):**") for ln in lines),
                            "%s 缺 '**Read (input):**' 行" % name)
            self.assertTrue(any(ln.startswith("**Write (output):**") for ln in lines),
                            "%s 缺 '**Write (output):**' 行" % name)
            heads = [ln for ln in lines if ln.startswith("## ")]
            self.assertEqual(heads[-1], "## 播报与下一步",
                             "%s 末段须为 '## 播报与下一步'" % name)
            self.assertNotIn("**读入：**", text, "%s 旧形态「读入」残留" % name)
            self.assertNotIn("**写出：**", text, "%s 旧形态「写出」残留" % name)

    # trace: 编排时序五步齐全且首尾相接（工作流点名五文件）
    def test_workflow_names_five_steps(self):
        raw = self.skill()
        for step in STEP_FILES:
            self.assertIn("`steps/%s`" % step, raw, "工作流未点名 %s" % step)

    # trace: B3 §13 三机制 + 读取边界各异（不按最严纪律自我设限）
    def test_three_mechanisms_and_read_boundaries(self):
        raw = self.skill()
        for phrase in ("三机制", "预演", "引用核对", "对抗",
                       "不按最严纪律自我设限", "禁读实现", "必读实现"):
            self.assertIn(phrase, raw, "缺三机制/读取边界要素：%s" % phrase)

    # trace: B3 §13 四保障（版本冻结 / 分片禁共写 / 报总数 / B 部分双输出）
    def test_guarantees(self):
        raw = self.skill()
        for phrase in ("冻结", "禁多 agent 写同一产物", "必报总数",
                       "出 B 才算 dogfood", "B 部分必出"):
            self.assertIn(phrase, raw, "缺四保障要素：%s" % phrase)
        step2 = read(os.path.join(STEPS_DIR, "02-dispatch.md"))
        self.assertIn("不复用任务书写作侧", step2,
                      "片指令缺 self-preference 隔离句")
        self.assertIn("锚一变全废", step2, "片指令缺锚点失效句")
        self.assertIn("禁写长 JSON", step2, "缺 B7b 长 JSON 截断教训句")

    # trace: B6/B7 闭环道（D 表无空行 / 增量补扫 / 旧值复扫两轮）
    def test_dispose_loop(self):
        step4 = read(os.path.join(STEPS_DIR, "04-dispose.md"))
        self.assertIn("无处置记录 = 扫描未闭环", step4, "缺 D 表闭环判据")
        self.assertIn("逐条处置 ≠ 逐处改透", step4, "缺 B6 教训原句")
        self.assertIn("复扫两轮", step4, "缺旧值复扫两轮强制道")
        self.assertIn("增量补扫", step4, "缺按改动落点增量补扫")
        raw = self.skill()
        self.assertIn("复扫两轮", raw, "SKILL.md 规则区缺复扫两轮锚")

    # trace: B7a 交叉命中置信度 + B7b 拍板贯通三问
    def test_cross_hit_confidence_and_ruling_questions(self):
        step3 = read(os.path.join(STEPS_DIR, "03-merge.md"))
        self.assertIn("置信度最高", step3, "缺交叉命中置信度判据")
        step2 = read(os.path.join(STEPS_DIR, "02-dispatch.md"))
        self.assertIn("贯通三问", step2, "缺用户拍板贯通三问专项")

    # trace: 机器台账归属（SS-### 永不复用 + check --final 终门由预演片走）
    def test_machine_ledger_belongs_to_spec_scan(self):
        raw = self.skill()
        self.assertIn("SS-###", raw, "缺 SS-### 台账锚")
        self.assertIn("永不复用", raw, "缺「永不复用」纪律")
        step5 = read(os.path.join(STEPS_DIR, "05-close.md"))
        self.assertIn("spec_scan.py", step5, "缺终门命令机器锚点")
        self.assertIn("check --final", step5, "缺 --final 终门旗标")

    # trace: 与 diy-spec-scan 的边界声明双向一致
    def test_boundary_with_spec_scan_is_two_way(self):
        raw = self.skill()
        self.assertIn("diy-spec-scan", raw, "缺与 diy-spec-scan 的边界声明")
        for phrase in ("编排者", "预演扫描片"):
            self.assertIn(phrase, raw, "边界声明缺要素：%s" % phrase)
        route = read(SPEC_SCAN_ROUTE)
        self.assertIn("diy-selfcheck", route,
                      "diy-spec-scan 04-report 路由段缺 diy-selfcheck 归位句")
        spec_scan = read(SPEC_SCAN_MD)
        self.assertNotIn("编排者", spec_scan,
                          "diy-spec-scan 不得自称编排者（边界互斥）")
        self.assertNotIn("dogfood", spec_scan.lower(),
                         "diy-spec-scan 不得自称 dogfood 编排（归 diy-selfcheck）")


if __name__ == "__main__":
    unittest.main()
