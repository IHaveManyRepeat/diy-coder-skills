# -*- coding: utf-8 -*-
"""套件级句式母本一致性测试。

母本：`diy-coder/.analysis/2026-09-16-skill-remediation/suite-texts.md`
用途：母本一处改 -> 机械复制 -> 本测试抓漂移（NFR-4 要求技能目录自带全部内容，不能运行时读共享文件）。

三组：
  A **冻结片段组**（母本 §1 / §2）—— 分两态：
      · 已转中文定稿的技能（`CONVERTED_*` 台账）-> 断言含中文定稿、且不再含英文原形；
      · 未转的技能 -> 断言英文原形逐字同 md5。
    每转一个技能就在台账里加一个；**漏登即红**（英文断言会失败）。
  B **待落地组**（母本 §3 / §4 / §5 / §6）—— 母本已定、技能未改；断言「缺锚串的技能集 == 台账」。
    每落地一个就从台账删一个；**漏删即红**。台账清空后转为「全部适用技能必须含锚串」。
  C **非成员组** —— 工具类技能不得出现 §1 / §2 的任一形态。

trace: 中文化轮前置（母本抽取 + 全中文正典），来源裁定见 dispositions.md 轮3 / C1 / B10；
       母本 §8 记录 spec-scan 处置（§1 补中文定稿、§2 保留自定短块）。
"""
import hashlib
import os
import re
import unittest

NL = "\n"
SKILLS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "skills")


def skills():
    """技能短名（去掉 `diy-` 前缀），与母本的成员清单同名。"""
    return sorted(d[len("diy-"):] for d in os.listdir(SKILLS_DIR) if d.startswith("diy-"))


def read(skill):
    """按短名读 SKILL.md；不存在返回 None。"""
    path = os.path.join(SKILLS_DIR, "diy-" + skill, "SKILL.md")
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def md5(text):
    return hashlib.md5((text + NL).encode("utf-8")).hexdigest()


# --------------------------------------------------------------- A 冻结片段

INSTANCE_EN_MD5 = "5445f98bc4d4821e6888b89406a97eac"
INSTANCE_EN_RE = re.compile(r"Instance resolution \(FR-4\.5/D-9\)[^\r\n]*")
INSTANCE_EN_MARK = "Instance resolution (FR-4.5/D-9)"

INSTANCE_ZH = ("实例解析（FR-4.5/D-9）由工具脚本执行：运行 "
               "`python \"{project-root}/.claude/skills/diy-tools/scripts/diyc.py\" "
               "resolve [--instance <name>] --json`，把回执里的 `output_dir` "
               "当作本次运行唯一的读写根目录。")

INSTANCE_MEMBERS = frozenset("""
architecture augment build-loop checkpoint-preview correct-course create-story
design dev e2e-tests epics-stories help investigate openapi prfaq
product-brief project-context quick-dev readiness-check research retrospective
review sprint test-design
""".split())
# 已转中文定稿的技能（中文化轮逐个加入；B3 批 5 技能为中文原生，落地即转）
CONVERTED_INSTANCE = frozenset(["spec-scan", "prd", "teach-me-testing", "test-author",
                                "test-framework", "test-gate", "test-review",
                                "product-brief", "prfaq", "openapi", "epics-stories",
                                "create-story", "checkpoint-preview", "sprint",
                                "build-loop", "readiness-check", "test-design",
                                "quick-dev", "help", "augment", "e2e-tests",
                                "correct-course", "project-context",
                                "investigate", "research", "retrospective"])
INSTANCE_NON_MEMBERS = frozenset(["tools", "viewer"])  # 不解析配置

DISCIPLINE_EN_MD5 = "f1b3b6fbb528f0cfab31f3196b3547ae"
DISCIPLINE_EN_RE = re.compile(r"^- \*\*Writing discipline[^\r\n]*", re.M)

DISCIPLINE_ZH = ("- **写作纪律。** 主字段 = 大白话主句；数字/枚举内联；"
                 "机器语法（命令/旗标/路径）进括号；机器锚点逐字保留"
                 "（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 "
                 "`diy-design` 的 detect 启发式。schema 若定义 `plain`："
                 "一行写清该条目为什么存在，绝不写是什么（转述会漂移）；"
                 "只写难懂的条目。若定义 `detail`：过程叙述——结论留在主字段。")

DISCIPLINE_MEMBERS = frozenset("""
architecture checkpoint-preview correct-course create-story e2e-tests
epics-stories investigate prfaq product-brief project-context quick-dev
readiness-check research retrospective review sprint test-design
""".split())
# 中文化轮逐个加入；B3 批 5 技能为中文原生，落地即转
CONVERTED_DISCIPLINE = frozenset(["prd", "teach-me-testing", "test-author",
                                  "test-framework", "test-gate", "test-review",
                                  "product-brief", "prfaq", "epics-stories",
                                  "create-story", "checkpoint-preview", "sprint",
                                  "readiness-check", "test-design", "quick-dev",
                                  "augment", "e2e-tests", "correct-course",
                                  "project-context", "investigate", "research",
                                  "retrospective"])
# spec-scan 带同前缀的技能自定短块——非 §2 成员，不参与断言
DISCIPLINE_NON_MEMBERS = frozenset(["spec-scan"])


class FrozenTextsConsistencyTests(unittest.TestCase):
    """母本 §1 / §2：已转者断言中文定稿，未转者断言英文原形 md5。"""

    def _check(self, label, zh_text, en_re, en_md5, en_mark, members,
               converted, non_members):
        for s in skills():
            if s in non_members:
                continue
            text = read(s)
            if text is None:
                continue
            if s in converted:
                self.assertIn(zh_text, text,
                              "%s：%s 已登记为中文定稿，但正文未含母本 %s 定稿" % (label, s, label))
                if en_mark:
                    self.assertNotIn(en_mark, text,
                                     "%s：%s 已转中文定稿，仍残留英文原形" % (label, s))
                continue
            if s not in members:
                continue
            frags = en_re.findall(text)
            self.assertTrue(frags, "%s：%s 是母本成员却缺该片段" % (label, s))
            for frag in frags:
                self.assertEqual(md5(frag.strip()), en_md5,
                                 "%s：%s 的片段既非英文原形 md5、也未登记为已转中文——"
                                 "转了就请加入 CONVERTED 台账" % (label, s))

    # trace: 母本 §1（实例解析句）
    def test_instance_resolution_sentence(self):
        self._check("§1", INSTANCE_ZH, INSTANCE_EN_RE, INSTANCE_EN_MD5,
                    INSTANCE_EN_MARK,
                    set(INSTANCE_MEMBERS) | set(CONVERTED_INSTANCE),
                    CONVERTED_INSTANCE, INSTANCE_NON_MEMBERS)
        for s in INSTANCE_NON_MEMBERS:
            text = read(s)
            if text is not None:
                self.assertNotIn(INSTANCE_EN_MARK, text, "%s 不应出现 §1 英文原形" % s)
                self.assertNotIn(INSTANCE_ZH, text, "%s 不应出现 §1 中文定稿" % s)

    # trace: 母本 §2（写作纪律块）
    def test_writing_discipline_block(self):
        self._check("§2", DISCIPLINE_ZH, DISCIPLINE_EN_RE, DISCIPLINE_EN_MD5, None,
                    set(DISCIPLINE_MEMBERS) | set(CONVERTED_DISCIPLINE),
                    CONVERTED_DISCIPLINE, DISCIPLINE_NON_MEMBERS)


# --------------------------------------------------------------- B 待落地

ANCHOR_RESOLVE_KEYS = ("解析 `project.communication_language` / "
                       "`project.document_output_language` / `paths.output_dir`")
ANCHOR_READ_DISCIPLINE = ("读取纪律：预载预算 = 本文件、上述配置与回执、`steps/` 下当前那一个文件"
                          "——绝不批量预载；执行期读取以每个步骤开头的 `Read (input)` 行为唯一权威，"
                          "**主文件不列举封闭清单**。")
ANCHOR_RENDER_SILENT = "渲染是静默旁路——只写调用命令"

_CONFIG_SKILLS = sorted(set(INSTANCE_MEMBERS) | set(CONVERTED_INSTANCE))

# 已落 §3 锚串的技能（中文化轮逐个加入；落地即从 PENDING_RESOLVE_KEYS 移除）
LANDED_RESOLVE_KEYS = frozenset(["prd", "product-brief", "prfaq", "openapi",
                                 "epics-stories", "create-story", "checkpoint-preview",
                                 "sprint", "build-loop", "readiness-check", "test-design",
                                 "quick-dev", "help", "augment", "e2e-tests",
                                 "correct-course", "spec-scan", "project-context",
                                 "investigate", "research", "retrospective"])

# 已落 §4 读取纪律的技能（仅对有 `steps/` 的适用面生效；落地即从 PENDING_READ_DISCIPLINE 移除）
LANDED_READ_DISCIPLINE = frozenset(["product-brief", "prfaq",
                                    "create-story", "checkpoint-preview",
                                    "readiness-check", "quick-dev",
                                    "e2e-tests", "correct-course", "spec-scan",
                                    "project-context", "investigate", "research",
                                    "retrospective"])

ANCHOR_PRECISE = ("- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；"
                  "不复述上游已写的信息（引用 ID）；不写没有信息量的套话。")

# 已落 §6 条款的技能（中文化轮逐个加入；落地即从 PENDING_PRECISE 移除）
LANDED_PRECISE = frozenset(["prd", "teach-me-testing", "test-author",
                            "test-framework", "test-gate", "test-review",
                            "product-brief", "prfaq", "openapi", "epics-stories",
                            "create-story", "checkpoint-preview", "sprint",
                            "build-loop", "readiness-check", "test-design",
                            "quick-dev", "help", "augment", "e2e-tests",
                            "correct-course", "spec-scan", "project-context",
                            "investigate", "research", "retrospective"])


def _steppers():
    """§4 读取纪律的适用面 = 有 `steps/` 的技能。

    2026-09-19 用户裁定：12 个单文件技能（architecture / augment / build-loop /
    design / dev / epics-stories / help / openapi / prd / review / sprint /
    test-design）**不拆 steps**，§4 对它永久不适用——§4 的两个成分（「读 `steps/` 下
    当前那一个文件」「以各 step 的 `Read (input)` 为准」）都预设 steps 存在，硬落即写入
    假事实。将来某技能若拆出 `steps/`，自动进入本适用面（缺锚串且未登记即判红）。
    """
    return [s for s in skills()
            if os.path.isdir(os.path.join(SKILLS_DIR, "diy-" + s, "steps"))]

# B3 批新建技能（**落地时在此登记**）：它们**中文原生**——§1/§3/§4/§5 一次写到位，
# 故只进 `CONVERTED_*` 与这里，**不进 `INSTANCE_MEMBERS` / `DISCIPLINE_MEMBERS` / 任何 `PENDING_*`**
# （进 PENDING 会因它们已含锚串而判红；RS4-01/04/05）。
NEW_SKILLS = frozenset(["teach-me-testing", "test-author",
                        "test-framework", "test-gate", "test-review"])


def _lacking(anchor, candidates):
    return {s for s in candidates if read(s) is not None and anchor not in read(s)}


class PendingLandingTests(unittest.TestCase):
    """母本 §3 / §4 / §5：断言「缺锚串的技能集 == 台账」；漏删即红。"""

    PENDING_RESOLVE_KEYS = frozenset(set(_CONFIG_SKILLS) - NEW_SKILLS - LANDED_RESOLVE_KEYS)
    PENDING_READ_DISCIPLINE = frozenset(set(_steppers()) - NEW_SKILLS - LANDED_READ_DISCIPLINE)
    # §6 适用面 = 全部技能（母本明示「不设非成员」）
    PENDING_PRECISE = frozenset(set(skills()) - NEW_SKILLS - LANDED_PRECISE)
    PENDING_RENDER_SILENT = frozenset("""
viewer
""".split())

    def _check(self, anchor, candidates, pending):
        lacking = _lacking(anchor, candidates)
        if pending:
            self.assertEqual(lacking, set(pending),
                             "锚串 %r 的未落地集与台账不符（缺锚串但未登记：%s ← 落地时漏登；"
                             "已含锚串但仍在台账：%s ← 请从 PENDING 台账删除）"
                             % (anchor[:24],
                                sorted(lacking - set(pending)),
                                sorted(set(pending) - lacking)))
        else:
            self.assertEqual(lacking, set(),
                             "台账已清空，以下技能仍缺锚串 %r：%s"
                             % (anchor[:24], sorted(lacking)))

    # trace: 母本 §3（配置解析键路径 + 缺省链）
    def test_pending_resolve_keys(self):
        self._check(ANCHOR_RESOLVE_KEYS, _CONFIG_SKILLS, self.PENDING_RESOLVE_KEYS)

    # trace: 母本 §4（读取纪律）——适用面 = 有 `steps/` 的技能（见 `_steppers`）
    def test_pending_read_discipline(self):
        self._check(ANCHOR_READ_DISCIPLINE, _steppers(), self.PENDING_READ_DISCIPLINE)

    # trace: 母本 §5（渲染静默）
    def test_pending_render_silent(self):
        renderers = [s for s in skills()
                     if (read(s) or "").find("diy-viewer/scripts/viewer.py") >= 0]
        self._check(ANCHOR_RENDER_SILENT, renderers, self.PENDING_RENDER_SILENT)

    # trace: 母本 §6（精准简练）——2026-09-19 用户立为母本；适用面 = 全部技能，不设非成员
    def test_pending_precise_brief(self):
        self._check(ANCHOR_PRECISE, skills(), self.PENDING_PRECISE)


if __name__ == "__main__":
    unittest.main()
