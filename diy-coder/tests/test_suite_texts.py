# -*- coding: utf-8 -*-
"""套件级句式母本一致性测试。

母本：`diy-coder/.analysis/2026-09-16-skill-remediation/suite-texts.md`
用途：母本一处改 -> 机械复制 -> 本测试抓漂移（NFR-4 要求技能目录自带全部内容，不能运行时读共享文件）。

两组：
  A **强制组**（母本 §1 / §2，历史冻结、英文原形 + md5）—— 成员必须逐字同 md5，本组现在就绿。
  B **待落地组**（母本 §3 / §4 / §5，母本已定、技能尚未改）—— 断言「缺该锚串的技能集 == 台账」。
    中文化轮每落地一个技能，台账就要减一个；漏减则本测试红。台账清空后本组自动转为
    「全部适用技能必须逐字含锚串」的强制断言。

trace: 中文化轮前置（母本抽取），来源裁定见 dispositions.md 轮3 / C1；母本 §8 记录 spec-scan 缺口。
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


# --------------------------------------------------------------- A 强制组

INSTANCE_MD5 = "5445f98bc4d4821e6888b89406a97eac"
INSTANCE_RE = re.compile(r"Instance resolution \(FR-4\.5/D-9\)[^\r\n]*")
INSTANCE_MEMBERS = frozenset("""
architecture augment build-loop checkpoint-preview correct-course create-story
design dev e2e-tests epics-stories help investigate openapi prd prfaq
product-brief project-context quick-dev readiness-check research retrospective
review sprint test-design
""".split())
INSTANCE_NON_MEMBERS = frozenset(["tools", "viewer"])  # 不解析配置

DISCIPLINE_MD5 = "f1b3b6fbb528f0cfab31f3196b3547ae"
DISCIPLINE_RE = re.compile(r"^- \*\*Writing discipline[^\r\n]*", re.M)
DISCIPLINE_MEMBERS = frozenset("""
architecture checkpoint-preview correct-course create-story e2e-tests
epics-stories investigate prd prfaq product-brief project-context quick-dev
readiness-check research retrospective review sprint test-design
""".split())
# spec-scan 带同前缀（`- **Writing discipline.**`）的技能自定短块——非 §2 成员，不参与 md5 断言
DISCIPLINE_NON_MEMBERS = frozenset(["spec-scan"])


class FrozenTextsConsistencyTests(unittest.TestCase):
    """母本 §1 / §2：成员逐字同 md5；非成员不得出现。"""

    def _members_hitting(self, pattern, digest, non_members=()):
        hit, miss = set(), set()
        for s in skills():
            if s in non_members:
                continue
            text = read(s)
            if text is None:
                continue
            found = pattern.findall(text)
            if not found:
                continue
            for frag in found:
                if md5(frag.strip()) == digest:
                    hit.add(s)
                else:
                    miss.add(s)
        return hit, miss

    # trace: 母本 §1（实例解析句）—— 24 份逐字同 md5
    def test_instance_resolution_sentence_is_verbatim(self):
        hit, miss = self._members_hitting(INSTANCE_RE, INSTANCE_MD5)
        self.assertEqual(miss, set(), "以下技能的实例解析句与母本 §1 不符：%s" % sorted(miss))
        self.assertEqual(hit, set(INSTANCE_MEMBERS),
                         "§1 成员集与母本不符（多：%s；少：%s）"
                         % (sorted(hit - set(INSTANCE_MEMBERS)),
                            sorted(set(INSTANCE_MEMBERS) - hit)))
        for s in INSTANCE_NON_MEMBERS:
            text = read(s)
            if text is not None:
                self.assertNotIn("Instance resolution (FR-4.5/D-9)", text,
                                 "%s 不在 §1 成员内，不应出现该句" % s)

    # trace: 母本 §2（写作纪律块）—— 18 份逐字同 md5
    def test_writing_discipline_block_is_verbatim(self):
        hit, miss = self._members_hitting(DISCIPLINE_RE, DISCIPLINE_MD5,
                                          non_members=DISCIPLINE_NON_MEMBERS)
        self.assertEqual(miss, set(), "以下技能的写作纪律块与母本 §2 不符：%s" % sorted(miss))
        self.assertEqual(hit, set(DISCIPLINE_MEMBERS),
                         "§2 成员集与母本不符（多：%s；少：%s）"
                         % (sorted(hit - set(DISCIPLINE_MEMBERS)),
                            sorted(set(DISCIPLINE_MEMBERS) - hit)))


# --------------------------------------------------------------- B 待落地组

# 母本 §3 / §4 / §5 的关键锚串（落地后须逐字出现在技能 SKILL.md）
ANCHOR_RESOLVE_KEYS = ("解析 `project.communication_language` / "
                       "`project.document_output_language` / `paths.output_dir`")
ANCHOR_READ_DISCIPLINE = ("读取纪律：`steps/` 下的步骤文件一次只读一个，绝不批量预载；"
                          "每个步骤开头的 `Read (input)` 行是该步读什么的唯一权威。")
ANCHOR_RENDER_SILENT = "渲染是静默旁路——只写调用命令"

_CONFIG_SKILLS = sorted(set(INSTANCE_MEMBERS))
_READ_SKILLS = sorted(set(INSTANCE_MEMBERS))  # 不读 steps/ 的技能见母本 §4 例外


def _lacking(anchor, candidates):
    return {s for s in candidates if read(s) is not None and anchor not in read(s)}


class PendingLandingTests(unittest.TestCase):
    """母本 §3 / §4 / §5：母本已定、技能未改。台账 = 尚未落地的技能集。

    中文化轮每落地一个技能就把它从对应台账删掉；漏删 -> 本测试红（这是刻意设计的强制点）。
    台账清空后，同一测试转为「全部适用技能必须含锚串」。
    """

    # 中文化轮落地后，逐个从下列集合删除
    PENDING_RESOLVE_KEYS = frozenset(_CONFIG_SKILLS)
    PENDING_READ_DISCIPLINE = frozenset(_READ_SKILLS)
    PENDING_RENDER_SILENT = frozenset("""
augment checkpoint-preview correct-course create-story e2e-tests investigate
prfaq product-brief project-context quick-dev readiness-check research
retrospective spec-scan viewer
""".split())

    def _check(self, anchor, candidates, pending):
        lacking = _lacking(anchor, candidates)
        if pending:
            self.assertEqual(lacking, set(pending),
                             "§锚串 %r 的未落地集与台账不符（实测多：%s；台账多：%s）——"
                             "已落地的技能请从 PENDING 台账删除"
                             % (anchor[:24],
                                sorted(lacking - set(pending)),
                                sorted(set(pending) - lacking)))
        else:
            self.assertEqual(lacking, set(),
                             "台账已清空，以下技能仍缺锚串 %r：%s" % (anchor[:24], sorted(lacking)))

    # trace: 母本 §3（配置解析键路径 + 缺省链）
    def test_pending_resolve_keys(self):
        self._check(ANCHOR_RESOLVE_KEYS, _CONFIG_SKILLS, self.PENDING_RESOLVE_KEYS)

    # trace: 母本 §4（读取纪律）
    def test_pending_read_discipline(self):
        self._check(ANCHOR_READ_DISCIPLINE, _READ_SKILLS, self.PENDING_READ_DISCIPLINE)

    # trace: 母本 §5（渲染静默）
    def test_pending_render_silent(self):
        renderers = [s for s in skills()
                     if (read(s) or "").find("diy-viewer/scripts/viewer.py") >= 0]
        self._check(ANCHOR_RENDER_SILENT, renderers, self.PENDING_RENDER_SILENT)


if __name__ == "__main__":
    unittest.main()
