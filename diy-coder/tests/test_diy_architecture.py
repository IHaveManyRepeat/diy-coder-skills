# -*- coding: utf-8 -*-
"""diy-architecture 技能契约（C·3a 段2 · W9；原 C·3b 并入）。

覆盖四交付：① 双源输入判定（四情形 + 零产出路由）② `affects` 开放 SC/P 域
（含引擎侧 `known` 域接入的端到端冒烟，裁定 22）③ 可测性评审维度 ④ 运维维度；
外加 §2.2 保真面的机械抓手（四段结构 / 行数控制线 / 母本锚串 / `.prev` 对账句 /
终门句 / ID 纪律 / FR-NFR 域）。

引擎侧规则级用例在 `tests/test_diyc_check.py`（W9 增补）；本文件只做
「SKILL.md 承诺 ↔ 上下游产物 ↔ 引擎行为」的跨面核对与文档契约断言。
"""
import argparse
import os
import subprocess
import sys
import tempfile
import unittest

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
SKILLS = os.path.join(HERE, "..", "skills")
SKILL_MD = os.path.join(SKILLS, "diy-architecture", "SKILL.md")
SCRIPTS = os.path.join(SKILLS, "diy-tools", "scripts")
UPSTREAM_MD = os.path.join(SKILLS, "diy-wds-scenarios", "SKILL.md")
CHECK_DOCS_PY = os.path.join(SCRIPTS, "diyc_check_docs.py")

sys.path.insert(0, SCRIPTS)
import diyc_check  # noqa: E402

INSTANCE_ZH = ("实例解析（FR-4.5/D-9）由工具脚本执行：运行 "
               "`python \"{project-root}/.claude/skills/diy-tools/scripts/diyc.py\" "
               "resolve [--instance <name>] --json`，把回执里的 `output_dir` "
               "当作本次运行唯一的读写根目录。")
INSTANCE_EN_MARK = "Instance resolution (FR-4.5/D-9)"
RESOLVE_KEYS = ("解析 `project.communication_language` / "
                "`project.document_output_language` / `paths.output_dir`")
RENDER_SILENT = "渲染是静默旁路——只写调用命令"
PRECISE_ZH = ("- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；"
              "不复述上游已写的信息（引用 ID）；不写没有信息量的套话。")
DISCIPLINE_ZH = ("- **写作纪律。** 主字段 = 大白话主句；数字/枚举内联；"
                 "机器语法（命令/旗标/路径）进括号；机器锚点逐字保留"
                 "（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 "
                 "`diy-design` 的 detect 启发式。schema 若定义 `plain`："
                 "一行写清该条目为什么存在，绝不写是什么（转述会漂移）；"
                 "只写难懂的条目。若定义 `detail`：过程叙述——结论留在主字段。")


def check(root, **kw):
    """以 CLI 等价参数直调引擎（与 tests/test_diyc_check.py 同口径）。"""
    args = argparse.Namespace(
        project_root=str(root), instance=None,
        output_dir=os.path.join(str(root), "diy-output"),
        type="architecture", final=kw.get("final", False), previous=kw.get("previous"),
        story=None, json=True)
    return diyc_check.run(args)


class SkillContractTests(unittest.TestCase):
    """SKILL.md 契约：母本逐字 + 四段结构 + C·3a 四项交付 + 保真面。"""

    def setUp(self):
        with open(SKILL_MD, encoding="utf-8") as fh:
            self.raw = fh.read()

    # trace: 中文化轮（母本 §1 / §2 / §3 / §5 / §6 逐字）；§2.8 冻结要求
    def test_mother_texts_verbatim(self):
        self.assertIn(INSTANCE_ZH, self.raw, "缺母本 §1 中文定稿实例解析句")
        self.assertNotIn(INSTANCE_EN_MARK, self.raw, "已转中文定稿，仍残留 §1 英文原形")
        self.assertIn(RESOLVE_KEYS, self.raw, "缺母本 §3 配置解析键")
        self.assertIn(RENDER_SILENT, self.raw, "缺母本 §5 渲染静默锚串")
        self.assertIn("viewer.py\" --project-root", self.raw, "缺 viewer 命令全文")
        self.assertIn(PRECISE_ZH, self.raw, "缺母本 §6 精准简练条款")
        self.assertIn(DISCIPLINE_ZH, self.raw, "缺母本 §2 写作纪律块")
        self.assertIn("# ↑ 中文：", self.raw, "description 缺中文注释")

    # trace: C·3a §2.1 / §9 #1（四段结构不变；软控制线 = 现状 87 + 20% = ≤104，无硬阈值）
    def test_four_chinese_sections_and_budget(self):
        self.assertLessEqual(len(self.raw.splitlines()), 104, "薄主文件超出 104 行控制线")
        for section in ("## 激活时", "## 工作流", "## 结构", "## 规则"):
            self.assertIn(section, self.raw, "缺四段结构：%s" % section)

    # trace: C·3a §2.8（单文件形态：无 steps/ → 母本 §4 读取纪律不适用，不动 LANDED 台账）
    def test_single_file_skill_has_no_steps_dir(self):
        self.assertFalse(os.path.isdir(os.path.join(SKILLS, "diy-architecture", "steps")),
                         "本技能是单文件技能（2026-09-19 裁定）；长出 steps/ 须同步补 "
                         "§4 锚串并登记 LANDED_READ_DISCIPLINE")

    # ---------------------------------------------------------- 保真面（§2.2）

    # trace: C·3a §5.9 保真面——决策式 YAML 单一源 + 写范围恰好一份产物
    def test_single_source_and_write_scope(self):
        self.assertIn("决策式 YAML 单一源", self.raw, "缺决策式单一源形态声明")
        self.assertIn("写范围恰好一份产物", self.raw, "缺写范围纪律")
        self.assertIn("architecture.yaml.prev", self.raw, "缺 .prev 快照件")

    # trace: C·3a §5.9 保真面——ID 纪律（D-* / C-* / R-* 永不重编号、永不复用）
    def test_id_chain_discipline(self):
        self.assertIn("`D-*` / `C-*` / `R-*`", self.raw, "缺三类 ID 的列举")
        self.assertIn("永不重编号、永不复用", self.raw, "缺 ID 稳定纪律句")
        self.assertIn("check --type architecture --previous", self.raw, "缺 .prev 对账命令")
        for branch in ("ID_UNSTABLE", "MISSING_FILE", "UNPARSABLE_YAML"):
            self.assertIn(branch, self.raw, "缺 .prev 对账的失败分支：%s" % branch)

    # trace: C·3a §5.9 保真面——终门句（check --type architecture --final）
    def test_final_gate_sentence(self):
        self.assertIn("check --type architecture --final", self.raw, "缺终门命令句")
        self.assertIn("exit 0 是唯一放行", self.raw, "缺终门唯一放行语义")

    # trace: C·3a §5.9 保真面——affects 的 FR/NFR 域是**扩展**不是替换
    def test_fr_nfr_domain_preserved(self):
        self.assertIn("FR-x.y | NFR-x", self.raw, "结构段 affects 值域丢掉了 FR/NFR 域")

    # trace: B9/C·3a §5.9——棕地例外照旧（不改硬门的既有授权面）
    def test_brownfield_exception_kept(self):
        self.assertIn("棕地例外", self.raw, "缺棕地例外句")
        self.assertIn("不留悬空豁免", self.raw, "缺豁免留痕纪律")
        self.assertIn("R-###", self.raw, "未指明豁免留痕的落点（risks[] 的 R-###）")

    # ---------------------------------------------------------- 交付 1：双源输入

    # trace: C·3a §5.9 #1 / 验收 #10（四情形：主线有/无 × WDS 有/无，各有产出行为）
    def test_dual_source_four_cases(self):
        self.assertIn("四情形", self.raw, "缺「四情形」声明")
        self.assertIn("wds-scenarios.yaml", self.raw, "未声明 WDS 线输入源")
        self.assertIn("`project.status: 已定稿`", self.raw, "未声明门禁判据")
        self.assertIn("问用户一次走哪条", self.raw, "两源俱在时未交用户裁决（不得静默选边）")
        self.assertIn("零产出", self.raw, "两源俱缺时未声明零产出")
        self.assertIn("不写空 `architecture.yaml`", self.raw, "零产出未点名不写空产物")
        self.assertIn("不得把 WDS 线硬塞进 `prd.yaml` 门禁的例外", self.raw,
                      "缺「WDS 线走等价门禁、不是 prd 门禁的例外」禁令")

    # trace: C·3a §5.9 #1（零产出 + 三分支路由；路由目标技能须实装）
    def test_zero_output_routing_targets(self):
        for target in ("diy-prd", "diy-wds-brief", "diy-wds-scenarios"):
            self.assertIn(target, self.raw, "缺路由目标：%s" % target)
            self.assertTrue(os.path.isfile(os.path.join(SKILLS, target, "SKILL.md")),
                            "路由目标技能不在场：%s" % target)

    # trace: C·3a §5.9 #1（WDS 线的读面：wds-brief 可选读，wds-scenarios 只读）
    def test_wds_read_surface(self):
        self.assertIn("wds-brief.yaml", self.raw, "缺 wds-brief.yaml 可选读声明")
        self.assertIn("只读", self.raw, "缺 WDS 上游只读边界")

    # ---------------------------------------------------------- 交付 2：SC/P 域

    # trace: C·3a §5.9 #2 / 裁定 22（ID 形态以段1 W1 定义为准——只消费、不重定义）
    def test_scp_id_domain_consumed_not_redefined(self):
        self.assertIn("SC-<nn>", self.raw, "affects 值域未开放 SC-<nn>")
        self.assertIn("SC-<nn>.P<n>", self.raw, "affects 值域未开放 SC-<nn>.P<n>")
        self.assertIn("只消费、不重定义", self.raw, "未声明「只消费上游定义」的边界")
        with open(UPSTREAM_MD, encoding="utf-8") as fh:
            upstream = fh.read()
        for token in ("SC-<nn>", "SC-<nn>.P<n>", "废止独立的 `P-*` 前缀"):
            self.assertIn(token, upstream,
                          "上游 diy-wds-scenarios 不再声明 %r（ID 契约已漂移）" % token)

    # trace: C·3a 裁定 22（引擎侧接入是同一交付；SKILL 的「终门两域都认」须为真）
    def test_engine_known_domain_wired(self):
        with open(CHECK_DOCS_PY, encoding="utf-8") as fh:
            engine = fh.read()
        self.assertIn("wds-scenarios", engine, "引擎 known 域未接 WDS 侧产物")
        self.assertIn("SC-<nn>", engine, "引擎侧未点名 SC/P 域形态")

    # trace: C·3a §9 #20 —— 终门实跑：WDS 线（无 prd.yaml）architecture.yaml 真过
    def test_final_gate_accepts_scp_on_wds_line(self):
        with tempfile.TemporaryDirectory(prefix="w9-arch-") as root:
            self._seed(root, prd=False)
            r = check(root)
            self.assertTrue(r["ok"], r["violations"])

    # trace: C·3a §5.9 #1 情形四（两源俱缺 → 零产出）的机械面：无源即无产物，
    #        终门以 MISSING_FILE 判知「零产出」这一终态（不是「写空稿再报违规」）
    def test_zero_output_end_state_is_gate_visible(self):
        with tempfile.TemporaryDirectory(prefix="w9-arch-") as root:
            os.makedirs(os.path.join(root, "diy-output"), exist_ok=True)
            with open(os.path.join(root, "diy-coder.yaml"), "w", encoding="utf-8") as fh:
                fh.write("paths:\n  output_dir: diy-output\n")
            r = check(root)
            self.assertFalse(r["ok"])
            self.assertEqual(["MISSING_FILE"], [x["code"] for x in r["violations"]])

    # trace: C·3a 裁定 22 边界 —— 源产物缺席时 SC/P 仍真拒（新域只增数据源，不增通配）
    def test_final_gate_rejects_scp_without_source(self):
        with tempfile.TemporaryDirectory(prefix="w9-arch-") as root:
            self._seed(root, prd=True, wds=False)
            r = check(root)
            codes = {x["code"] for x in r["violations"]}
            self.assertIn("UNKNOWN_ID", codes, r["violations"])

    def _seed(self, root, prd=True, wds=True):
        os.makedirs(os.path.join(root, "diy-output"), exist_ok=True)
        with open(os.path.join(root, "diy-coder.yaml"), "w", encoding="utf-8") as fh:
            fh.write("paths:\n  output_dir: diy-output\n")
        out = os.path.join(root, "diy-output")
        if prd:
            self._dump(os.path.join(out, "prd.yaml"), {
                "project": {"name": "demo", "status": "已定稿",
                            "created": "2026-01-01", "updated": "2026-01-01"},
                "purpose": "夹具", "goals": [{"id": "G-1", "goal": "目标", "metric": "指标"}],
                "users": [{"id": "U-1", "name": "用户", "need": "需求"}],
                "features": [{"id": "F-1", "name": "组", "description": "说明",
                              "requirements": [{"id": "FR-1.1", "statement": "应当便于夹具",
                                                "priority": "必须"}]}],
                "nfrs": [{"id": "NFR-1", "statement": "非功能"}]})
        if wds:
            self._dump(os.path.join(out, "wds-scenarios.yaml"), {
                "project": {"name": "demo", "created": "2026-01-01",
                            "updated": "2026-01-01", "status": "已定稿"},
                "scenarios": [{"id": "SC-01", "name": "张伟的订购", "priority": 1,
                               "status": "已大纲",
                               "pages": [{"id": "SC-01.P1", "slug": "01.1-首页", "name": "首页"}]}]})
        self._dump(os.path.join(out, "architecture.yaml"), {
            "project": {"name": "demo", "status": "已定稿",
                        "created": "2026-01-01", "updated": "2026-01-01"},
            "stack": [{"choice": "html", "why": "静态站"}],
            "decisions": [{"id": "D-1", "title": "页面结构", "decision": "每场景一页",
                           "rationale": "理由", "alternatives": [{"option": "单页", "why_not": "更差"}],
                           "affects": ["SC-01", "SC-01.P1"], "status": "已采纳"}],
            "components": [{"id": "C-1", "name": "页面", "responsibility": "承接"}],
            "risks": [{"id": "R-1", "risk": "风险", "mitigation": "缓解"}],
            "revisions": []})

    @staticmethod
    def _dump(path, data):
        with open(path, "w", encoding="utf-8") as fh:
            yaml.safe_dump(data, fh, allow_unicode=True, sort_keys=False)

    # trace: C·3a §9 #7（冒烟 TC）——终点是人的技能列表：CLI 面自检可跑通
    def test_cli_smoke(self):
        with tempfile.TemporaryDirectory(prefix="w9-arch-") as root:
            self._seed(root, prd=False)
            proc = subprocess.run(
                [sys.executable, os.path.join(SCRIPTS, "diyc.py"), "check",
                 "--type", "architecture", "--project-root", root, "--json"],
                capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
            self.assertIn('"ok": true', proc.stdout)

    # ---------------------------------------------------------- 交付 3 / 4：两维评审

    # trace: C·3a §5.9 #3（可测性评审维度：承接 bmad-testarch-test-design 系统级模式）
    def test_testability_review_dimension(self):
        for axis in ("可控", "可观测", "可靠"):
            self.assertIn(axis, self.raw, "可测性维度缺轴：%s" % axis)
        for probe in ("可播种", "可 mock", "追踪"):
            self.assertIn(probe, self.raw, "可测性维度缺判据：%s" % probe)
        self.assertIn("bmad-testarch-test-design", self.raw, "未点名维度来源（系统级模式）")
        self.assertIn("整维沉默", self.raw, "缺「沉默即 finding」的判据")
        self.assertIn("不新增产物键", self.raw, "两维未守 §2.3「不新建产物键」")

    # trace: C·3a §5.9 #4 / 迁移计划 §十二 c（运维维度：operational / environmental envelope）
    def test_operational_envelope_dimension(self):
        for token in ("部署与环境", "基础设施选型", "运维"):
            self.assertIn(token, self.raw, "运维维度缺子面：%s" % token)
        self.assertIn("operational / environmental envelope", self.raw, "缺源侧维度名（可追溯）")

    # trace: C·3a §5.9 #3/#4（缺席处置机械化：落 risks[]，定稿前逐条处置）
    def test_missing_dimension_disposition(self):
        self.assertIn("缺席处置", self.raw, "缺缺席处置纪律")
        self.assertIn("`risks[]`", self.raw, "缺席未落到既有的 risks[] 键")


if __name__ == "__main__":
    unittest.main()
