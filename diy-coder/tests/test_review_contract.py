# -*- coding: utf-8 -*-
"""diy-review 分层审查契约测试（2026-09-13 skill 质量分析发现固化）。

契约来源：diy-review/.analysis/2026-09-13-1117（19 项发现，rank1-4 修复轮）——
- architecture-1：L4 设计采用必须接进可执行路径（Workflow + schema 枚举 + 命名一致）
- architecture-2：schema layer 枚举须能记录 L4 命中
- architecture-3：证伪轮命中须授权 done → in-progress 回退
- architecture-4：bad_spec 分流与 Routing 表 / diy-build-loop 冲突
- enhancement-1：旧「三层」回述导致 L4 被默认漏掉
- enhancement-3：全部任务完成后证伪轮无可达入口

2026-09-19 中文化轮（B-14）：正文转中文，分节锚随之改为 `## 激活时` / `## 工作流` / `## 结构` /
`## 规则`；同时把 B-14 的 8 条裁定固化成断言（实现面口径 / `trace --src` / `design.py` 全路径 /
L3 时点差 / `后置` 唯一落点 / 重开入口不变 / `EVIDENCE_MISSING` 不当豁免 / exp-sync 安装形态路径）。
"""
import io
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_REVIEW = os.path.join(HERE, "..", "skills", "diy-review", "SKILL.md")
SKILL_LOOP = os.path.join(HERE, "..", "skills", "diy-build-loop", "SKILL.md")
VIEWER = os.path.join(HERE, "..", "skills", "diy-viewer", "scripts", "viewer.py")
HELP = os.path.join(HERE, "..", "skills", "diy-help", "scripts", "help.py")


def read(path):
    with io.open(path, encoding="utf-8") as f:
        return f.read()


class ReviewL4WiringTests(unittest.TestCase):

    # trace: F-architecture-1（L4 只写在 Layers 节，Workflow 不执行）
    def test_l4_runs_inside_workflow(self):
        workflow = read(SKILL_REVIEW).split("## 工作流", 1)[1]
        self.assertIn("L4", workflow, "工作流未接 L4 设计采用")
        self.assertIn("design_ref", workflow, "工作流缺 design_ref 触发条件")

    # trace: F-architecture-2（layer 枚举缺 design）
    def test_schema_layer_enum_has_design(self):
        self.assertIn("正确性|边界|覆盖审计|设计采用", read(SKILL_REVIEW),
                      "schema layer 枚举缺 设计采用（L4 命中无法记录）")

    # trace: F-enhancement-1（description 仍称三层）
    def test_description_covers_l4(self):
        self.assertIn("design adoption", read(SKILL_REVIEW), "description 未覆盖 L4")


class StaleNamingTests(unittest.TestCase):

    # trace: F-enhancement-1（回述旧「三层」模式使 L4 默认漏掉）
    def test_review_skill_drops_three_layer_naming(self):
        review = read(SKILL_REVIEW)
        self.assertNotIn("## Three Layers", review, "仍用 Three Layers 标题")
        self.assertNotIn("three layers", review.lower(), "仍称 three layers")

    # trace: F-enhancement-1（build-loop 回述三层）
    def test_build_loop_names_l1_l4(self):
        loop = read(SKILL_LOOP)
        self.assertNotIn("three layers", loop.lower(), "build-loop 仍称 three layers")
        self.assertIn("L1-L4", loop, "build-loop 未按 L1-L4 描述审查阶段")

    # trace: F-enhancement-1（viewer 术语仍称三层审查 / 缺 design 层映射）
    def test_viewer_terms_updated(self):
        viewer = read(VIEWER)
        self.assertNotIn("三层审查（正确性/边界/覆盖审计）", viewer, "审查记录术语未更新")
        self.assertNotIn("等待三层审查", viewer, "待审查术语未更新")
        self.assertIn('"设计采用": "设计采用"', viewer, "viewer 缺 设计采用 层展示映射（英文值直出）")


class FalsificationEntryTests(unittest.TestCase):

    # trace: F-enhancement-3（硬门禁只开 review 态，done 后无入口）
    def test_falsify_accepted_for_done_targets(self):
        act = read(SKILL_REVIEW).split("## 激活时", 1)[1].split("## 工作流", 1)[0]
        self.assertIn("--falsify", act, "硬门禁未给 --falsify 开 done 例外")

    # trace: F-architecture-3（状态写入权「Nothing else」与证伪回退冲突）
    def test_falsification_reopen_is_authorized(self):
        self.assertIn("已完成 → 进行中", read(SKILL_REVIEW), "缺证伪回退的授权条款")

    # trace: F-enhancement-3（help 收尾提示未给命令入口）
    def test_help_points_to_falsify(self):
        self.assertIn("--falsify", read(HELP), "help 收尾未给证伪轮命令入口")


class VerdictRoutingTests(unittest.TestCase):

    # trace: F-architecture-4（bad_spec 原分流到 in-progress，与 Routing 表 / loop 冲突）
    def test_bad_spec_disposition_is_blocked(self):
        verdict = read(SKILL_REVIEW).split("## 规则", 1)[1]
        self.assertIn("规格缺陷", verdict)
        self.assertIn("已阻塞", verdict, "规格缺陷 未分流到 已阻塞")


class ZhConversionTests(unittest.TestCase):
    """2026-09-19 中文化轮（B-14）：四段中文标题 + 母本锚串 + B-14 八条落点。"""

    # trace: 中文化政策（四段中文标题 + description 中文注释 + ≤93 行预算）
    def test_four_chinese_sections_and_budget(self):
        raw = read(SKILL_REVIEW)
        self.assertLessEqual(len(raw.splitlines()), 93, "薄主文件超出 93 行预算")
        for section in ("## 激活时", "## 工作流", "## 结构", "## 规则"):
            self.assertIn(section, raw, "缺四段结构：%s" % section)
        self.assertIn("# ↑ 中文：", raw, "description 缺中文注释")
        # 无 steps/ —— 母本 §4 读取纪律永久不适用（2026-09-19 裁定），不得写成假事实
        self.assertNotIn("Read (input)", raw, "无 steps/ 的技能不得出现 §4 的步骤锚串")

    # trace: 母本 §1 / §2 / §3 / §5 / §6（逐字定稿由 test_suite_texts.py 强校，此处只锚存在性）
    def test_mother_texts_landed(self):
        raw = read(SKILL_REVIEW)
        self.assertIn("实例解析（FR-4.5/D-9）由工具脚本执行", raw, "缺母本 §1 实例解析句")
        self.assertNotIn("Instance resolution (FR-4.5/D-9)", raw, "已转中文定稿，仍残留 §1 英文原形")
        self.assertIn("解析 `project.communication_language` / "
                      "`project.document_output_language` / `paths.output_dir`", raw,
                      "缺母本 §3 配置解析键（A-3：project. 前缀）")
        self.assertIn("渲染是静默旁路——只写调用命令", raw, "缺母本 §5 渲染静默句")
        self.assertIn("- **精准简练。**", raw, "缺母本 §6 精准简练条款")
        self.assertIn("- **写作纪律。**", raw, "缺母本 §2 写作纪律块")

    # trace: B-14 SS-012-01 / SS-019-03（实现面与 diy-augment 同句复用）
    def test_implementation_surface_same_sentence_as_augment(self):
        raw = read(SKILL_REVIEW)
        self.assertIn("`references[].file` 里引用了本任务 `S-x` 的文件集合", raw,
                      "实现面未写死 trace 回执口径")
        self.assertIn("`git status --porcelain` 里本任务的未跟踪实现文件", raw,
                      "实现面缺未跟踪文件半边")
        self.assertIn("开场一行声明本次采样的实现面", raw, "实现面采样未要求声明")

    # trace: B-14 SS-012-02（trace --src 指向本任务实现面，unresolved 限该扫描面）
    def test_trace_src_points_at_task_surface(self):
        raw = read(SKILL_REVIEW)
        self.assertIn('diyc.py" trace --src <本任务实现文件/目录> --json', raw,
                      "trace 未用 --src 收窄到本任务实现面")
        self.assertIn("该扫描面", raw, "unresolved 未声明为扫描面内结果")

    # trace: B-14 SS-012-07 / A-11（design.py 全路径）
    def test_design_py_full_paths(self):
        raw = read(SKILL_REVIEW)
        self.assertIn('.claude/skills/diy-design/scripts/design.py" audit --design "{output_dir}/design.yaml" --src',
                      raw, "L4 audit 未写 design.py 全路径")
        self.assertIn('.claude/skills/diy-design/scripts/design.py" check --design "{output_dir}/design.yaml"',
                      raw, "L4 check 未写 design.py 全路径")

    # trace: B-14 SS-012-03（L3 时点差：块缺席非违规）+ SS-019-09 侧（追加件无 evidence 不当豁免）
    def test_l3_time_point_and_evidence_missing_signal(self):
        raw = read(SKILL_REVIEW)
        self.assertIn("其缺席不是违规", raw, "L3 未写 review 块缺席不是违规")
        self.assertIn("同一条命令", raw, "L3 未写与第 3 步块校验是同一条命令")
        self.assertIn("`EVIDENCE_MISSING`", raw, "缺台账违规码")
        self.assertIn("不当豁免", raw, "追加件无 evidence 未声明不当豁免")

    # trace: B-14 SS-012-05（后置唯一落点）+ SS-012-04（重开入口不变）
    def test_defer_landing_and_reopen_entry(self):
        raw = read(SKILL_REVIEW)
        self.assertIn("`deferred-actions.yaml`", raw, "未切断与 deferred-actions.yaml 的错误联想")
        self.assertIn("review.findings[]", raw, "后置未写唯一落点")
        self.assertIn("重开入口不变", raw, "重开未声明入口不变")
        self.assertIn('pop("augment")', raw, "重开未写清旧判定")

    # trace: B-14 SS-012-06 / A-9（exp-sync 安装形态路径，由人手动执行）
    def test_exp_sync_installed_path(self):
        raw = read(SKILL_REVIEW)
        self.assertIn('.claude/skills/diy-tools/scripts/exp-sync.py" push', raw,
                      "exp-sync 未写安装形态路径")
        self.assertIn("由人手动执行", raw, "exp-sync 未注明由人手动执行")


if __name__ == "__main__":
    unittest.main()
