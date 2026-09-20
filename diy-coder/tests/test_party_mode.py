# -*- coding: utf-8 -*-
"""diy-party-mode 契约冒烟（单文件技能、零引擎、零产物）。

任务书 §5 / §2.5：W3 无引擎（零产物 + 名册已裁 → 无确定性面），**不得为凑测试造无意义引擎**
——本文件因此不含任何子进程 / 引擎用例，只做 SKILL.md 契约冒烟（下列九项各一条用例）：

  1. 四段中文标题在场 + 薄主文件行数预算 + 标题含技能名
  2. 母本 §1 实例解析句中文定稿逐字（英文原形不得残留）
  3. 母本 §3 配置键全路径锚串 + 缺省链 + 实例触发条款
  4. 母本 §2 写作纪律块逐字且置文件末尾；母本 §6 精准简练在场且在其前
  5. 关键纪律句在场（真子代理 / 逐字呈现 / 不合成 / 视角动态派生 / 零写面声明）
  6. 无渲染理由句在场（零 YAML 产物 → 母本 §5 不适用；不得出现 viewer 调用）
  7. 无 `steps/` → 母本 §4 不适用理由句在场；无 `scripts/` 引擎（禁造无意义引擎）
  8. frontmatter 登记元数据 + `--model` / `--solo` 参数面 + 源触发语
  9. 与 `diy-review` 的边界声明双向一致（两侧文本互不矛盾）

夹具：无（纯文本断言，不落 tempfile、不读写本仓库 `diy-output/`）。
运行：cd diy-coder && python -m unittest discover -s tests -p "test_party_mode.py" -v

trace: B4 W3 diy-party-mode（任务书 §5）；母本 = suite-texts.md §1/§2/§3/§6；
       零产物判例承 diy-test-author，单文件形态承 2026-09-19「无 steps 技能 §4 永久不适用」裁定。
"""
import io
import os
import re
import unittest

NL = "\n"
HERE = os.path.dirname(os.path.abspath(__file__))
SKILLS_DIR = os.path.join(HERE, "..", "skills")
SKILL_DIR = os.path.join(SKILLS_DIR, "diy-party-mode")
SKILL_MD = os.path.join(SKILL_DIR, "SKILL.md")
REVIEW_MD = os.path.join(SKILLS_DIR, "diy-review", "SKILL.md")

# 母本 §1 中文定稿（suite-texts.md；test_suite_texts.py 的 INSTANCE_ZH 同文）
INSTANCE_ZH = ("实例解析（FR-4.5/D-9）由工具脚本执行：运行 "
               "`python \"{project-root}/.claude/skills/diy-tools/scripts/diyc.py\" "
               "resolve [--instance <name>] --json`，把回执里的 `output_dir` "
               "当作本次运行唯一的读写根目录。")
INSTANCE_EN_MARK = "Instance resolution (FR-4.5/D-9)"

# 母本 §3 锚串（键路径带 project. 前缀 / 缺省链 / 实例触发）
RESOLVE_KEYS_ZH = ("解析 `project.communication_language` / "
                   "`project.document_output_language` / `paths.output_dir`")
DEFAULT_CHAIN_ZH = ("缺省链：`paths.output_dir` 一律取 `diyc.py resolve` 回执"
                    "（引擎缺省 `diy-output`，异常形状降级并 warning）；"
                    "缺 `document_output_language` 落 `project.communication_language`；"
                    "两者皆缺则跟随用户当前消息的语言，并在收尾一行说明。")
INSTANCE_FLAG_ZH = ("实例名只在本次激活参数出现 `--instance <name>` 时才传"
                    "（无头侧入口 `runner.py --instance`；交互侧由用户在发起消息里给出同一旗标）；"
                    "未传时回执的 `output_dir` 即主线平铺根。")

# 母本 §6 精准简练（Rules 末尾、§2 之前）
PRECISE_ZH = ("- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；"
              "不复述上游已写的信息（引用 ID）；不写没有信息量的套话。")

# 母本 §2 写作纪律块（Rules 段末尾）
DISCIPLINE_ZH = ("- **写作纪律。** 主字段 = 大白话主句；数字/枚举内联；"
                 "机器语法（命令/旗标/路径）进括号；机器锚点逐字保留"
                 "（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 "
                 "`diy-design` 的 detect 启发式。schema 若定义 `plain`："
                 "一行写清该条目为什么存在，绝不写是什么（转述会漂移）；"
                 "只写难懂的条目。若定义 `detail`：过程叙述——结论留在主字段。")

SECTIONS_ZH = ("## 激活时", "## 工作流", "## 结构", "## 规则")
SECTIONS_EN_LEGACY = ("## On Activation", "## Workflow", "## Schema", "## Rules")
SRC_TRIGGER = ("Use when user requests party mode, wants multiple agent perspectives, "
               "group discussion, roundtable, or multi-agent conversation about their project.")


def read(path):
    with io.open(path, encoding="utf-8") as fh:
        return fh.read()


class SkillContractTests(unittest.TestCase):
    """diy-party-mode 契约冒烟（任务书 §5 测试节五项 + 形态 / 登记面扩展）。"""

    def skill(self):
        self.assertTrue(os.path.isfile(SKILL_MD), "缺 diy-party-mode/SKILL.md")
        return read(SKILL_MD)

    # trace: 任务书 §5（四段中文标题 + 薄主文件 ≤90 行 + 标题含技能名）；母本 §2.1
    def test_four_chinese_sections_and_thin_main_file(self):
        raw = self.skill()
        for section in SECTIONS_ZH:
            self.assertIn(section, raw, "缺四段结构：%s" % section)
        for legacy in SECTIONS_EN_LEGACY:
            self.assertNotIn(legacy, raw, "英文段名残留：%s" % legacy)
        self.assertLessEqual(len(raw.splitlines()), 90, "薄主文件超出 90 行预算")
        self.assertTrue(re.search(r"^# diy-party-mode — ", raw, re.M),
                        "缺 H1 标题（须为 '# diy-party-mode — <中文名>'）")

    # trace: 任务书 §5（母本 §1 中文定稿逐字）
    def test_instance_sentence_verbatim(self):
        raw = self.skill()
        self.assertIn(INSTANCE_ZH, raw, "SKILL.md 缺母本 §1 中文定稿（逐字）")
        self.assertNotIn(INSTANCE_EN_MARK, raw, "已转中文定稿，仍残留英文原形")

    # trace: 任务书 §2.1（母本 §3：键路径 project. 前缀 / 缺省链 / 实例触发语义）
    def test_resolve_keys_default_chain_and_instance_flag(self):
        raw = self.skill()
        self.assertIn(RESOLVE_KEYS_ZH, raw, "缺母本 §3 键路径锚串（project. 前缀）")
        self.assertIn(DEFAULT_CHAIN_ZH, raw, "缺母本 §3 缺省链")
        self.assertIn(INSTANCE_FLAG_ZH, raw, "缺母本 §3 实例触发条款")

    # trace: 任务书 §2.1（母本 §2 置 Rules 末尾、母本 §6 在其前）
    def test_precise_brief_then_writing_discipline_at_end(self):
        raw = self.skill()
        self.assertIn(PRECISE_ZH, raw, "缺母本 §6 精准简练")
        self.assertIn(DISCIPLINE_ZH, raw, "缺母本 §2 写作纪律块（逐字）")
        self.assertLess(raw.index(PRECISE_ZH), raw.index(DISCIPLINE_ZH),
                        "Rules 末尾顺序须为：§6 精准简练 → §2 写作纪律块")
        self.assertTrue(raw.rstrip(NL).endswith(DISCIPLINE_ZH),
                        "写作纪律块须置文件收尾行")

    # trace: 任务书 §5 裁定 1–3（本批最大改造：真子代理 / 逐字呈现 / 视角动态派生 / 零写面）
    def test_key_discipline_sentences(self):
        raw = self.skill()
        for phrase in ("真子代理", "逐字呈现", "不合成", "视角动态派生",
                       "零写面", "不写任何文件"):
            self.assertIn(phrase, raw, "缺关键纪律句：%s" % phrase)
        self.assertIn("绝不自己生成视角发言", raw, "缺「禁自扮视角」的硬禁令")
        self.assertIn("--solo", raw, "缺 `--solo` 例外与明示义务的落点")

    # trace: 任务书 §2.1 / §5（W2/W3 零产物 → 无渲染步骤，须在 Rules 写明理由）
    def test_no_render_step_with_reason(self):
        raw = self.skill()
        self.assertNotIn("viewer.py", raw, "零产物技能不得出现渲染调用")
        self.assertIn("无渲染", raw, "Rules 未写明无渲染步骤的理由")
        self.assertIn("母本 §5", raw, "无渲染理由未点名母本 §5")

    # trace: 任务书 §5 形态裁定（单文件技能、无 steps）；§2.5「不得为 W3 造无意义的引擎」
    def test_single_file_form_no_steps_no_engine(self):
        raw = self.skill()
        self.assertFalse(os.path.isdir(os.path.join(SKILL_DIR, "steps")),
                         "单文件形态：不得建 steps/")
        self.assertFalse(os.path.isdir(os.path.join(SKILL_DIR, "scripts")),
                         "零确定性面：不得为凑测试造引擎")
        self.assertIn("母本 §4", raw, "缺「无 steps → 母本 §4 不适用」的理由句")

    # trace: 任务书 §2.1 登记元数据表（anytime / false / 空链 / outputs —）+ §5 回报必答（参数面）
    def test_registration_metadata_and_arguments(self):
        raw = self.skill()
        head = raw.split("## 激活时")[0]
        for line in ("name: diy-party-mode", "phase: anytime", "precededBy: []",
                     "followedBy: []", "required: false", "line: any", "outputs: —"):
            self.assertIn(line, head, "frontmatter 缺登记项：%s" % line)
        self.assertIn("# ↑ 中文：", head, "缺 description 下方的中文注释行")
        self.assertIn(SRC_TRIGGER, head, "description 未逐字保留源技能触发语")
        self.assertRegex(head, r"description: '[^']+'",
                         "description 须为英文单引号单行")
        for flag in ("--model <model>", "--solo"):
            self.assertIn(flag, raw, "缺参数面机器锚点：%s" % flag)

    # trace: 任务书 §5 裁定 5（与 diy-review 的边界声明；V 终审计项②的施工面）
    def test_boundary_with_diy_review_is_two_way(self):
        raw = self.skill()
        self.assertIn("diy-review", raw, "缺与 diy-review 的边界声明")
        for phrase in ("结构化缺陷检出", "findings 台账", "讨论形态", "不互替"):
            self.assertIn(phrase, raw, "边界声明缺要素：%s" % phrase)
        # 双向：声明里对 diy-review 的定性必须与它自己的文本一致（facts，不涉它的措辞）
        review = read(REVIEW_MD)
        for fact in ("findings", "L1", "路由", "意图缺口"):
            self.assertIn(fact, review, "边界声明所引 diy-review 事实不成立：%s" % fact)
        self.assertNotIn("圆桌", review, "diy-review 不得自称讨论形态（边界互斥）")
        self.assertNotIn("多视角", review, "diy-review 不得自称多视角会审（边界互斥）")


if __name__ == "__main__":
    unittest.main()
