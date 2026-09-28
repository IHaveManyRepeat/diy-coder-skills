# -*- coding: utf-8 -*-
"""diy-design 技能文档契约（C·3a 段1 · W1）。

本文件自 `test_design.py` 迁出 `SkillContractTests` 整段（含其专用常量）。
迁出理由（任务书 §3 首步必做）：`SKILL.md` 是 W1 的独占文件面，而 `test_design.py`
的 `DesignEngineTests` 归 W2（`design.py` 引擎改造）——两类断言同处一文件会让
两个工位抢同一文件。迁出后 W1 独占本文件，可自由增补改造后的新断言。

保真面：原 `SkillContractTests` 的断言一条不删（行数预算 93 → 112 除外，见下）。
"""
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILLS = os.path.join(HERE, "..", "skills")
SKILL_MD = os.path.join(SKILLS, "diy-design", "SKILL.md")
STEPS_DIR = os.path.join(SKILLS, "diy-design", "steps")

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

# 母本 §4 读取纪律锚串（值同 `test_suite_texts.py` 的 `ANCHOR_READ_DISCIPLINE`）。
# 本技能本批长出 `steps/`，进 `_steppers()` 适用面 → 必补；此处另作本技能的显式在场断言。
READ_DISCIPLINE = ("读取纪律：预载预算 = 本文件、上述配置与回执、`steps/` 下当前那一个文件"
                   "——绝不批量预载；执行期读取以每个步骤开头的 `Read (input)` 行为唯一权威，"
                   "**主文件不列举封闭清单**。")


class SkillContractTests(unittest.TestCase):
    """SKILL.md 契约冒烟：母本逐字 + 中文化政策 + B-6 七条落点 + C·3a 改造面。"""

    def setUp(self):
        with open(SKILL_MD, encoding="utf-8") as fh:
            self.raw = fh.read()

    # trace: 中文化轮（母本 §1 / §2 / §3 / §5 / §6 中文定稿逐字）
    def test_mother_texts_verbatim(self):
        self.assertIn(INSTANCE_ZH, self.raw, "缺母本 §1 中文定稿实例解析句")
        self.assertNotIn(INSTANCE_EN_MARK, self.raw, "已转中文定稿，仍残留 §1 英文原形")
        self.assertIn(RESOLVE_KEYS, self.raw, "缺母本 §3 配置解析键（A-3：project. 前缀）")
        self.assertIn(RENDER_SILENT, self.raw, "缺母本 §5 渲染静默锚串")
        self.assertIn("viewer.py\" --project-root", self.raw, "缺 viewer 命令全文（A-12）")
        self.assertIn(PRECISE_ZH, self.raw, "缺母本 §6 精准简练条款")
        self.assertIn(DISCIPLINE_ZH, self.raw, "缺母本 §2 写作纪律块")

    # trace: 2026-09-19 中文化政策（四段中文标题 + description 中文注释）
    # trace: C·3a §2.1 行数口径订正——软控制线 = 现状 93 + 20% = ≤112（**不是** ≤90 硬阈值，
    #        也非旧断言的 93）；超线须在回报说明理由，本断言即该控制线的机械抓手。
    def test_four_chinese_sections_and_budget(self):
        self.assertLessEqual(len(self.raw.splitlines()), 112, "薄主文件超出 112 行控制线")
        for section in ("## 激活时", "## 工作流", "## 结构", "## 规则"):
            self.assertIn(section, self.raw, "缺四段结构：%s" % section)
        self.assertIn("# ↑ 中文：", self.raw, "description 缺中文注释")

    # trace: B-6 SS-017-05（description 对齐引擎真子命令；a11y 取自 check）
    def test_description_matches_engine_subcommands(self):
        self.assertNotIn("a11y-check", self.raw, "description 仍写引擎没有的 a11y-check")
        self.assertIn("detect / validate / check / audit", self.raw,
                      "description 未列引擎真子命令")
        self.assertIn("来自 `check` 回执", self.raw, "未注明 a11y 判定取自 check")

    # trace: B-6 SS-017-02（配对集合指引擎回执，不自拟子集）
    def test_contrast_pairs_point_to_engine_receipt(self):
        self.assertIn("checked.contrast_pairs", self.raw, "配对集合未指向引擎回执")
        self.assertIn("不自拟子集", self.raw, "未禁自拟配对子集")

    # trace: B-6 SS-017-06（direction 钉死字符串形状，结构与创作纪律同款）
    def test_direction_pinned_to_string(self):
        self.assertIn("direction: <string>", self.raw, "结构未钉死 direction 为字符串")
        self.assertIn("不是列表/映射", self.raw, "结构缺形状禁令")
        self.assertIn("**字符串**", self.raw, "创作纪律缺同款括注")

    # trace: B-6 SS-017-03（终门 = validate + check + audit + 假设清零点名字段集）
    def test_final_gate_expands_three_commands(self):
        for cmd in ("validate --design", "check --design", "audit --design"):
            self.assertIn(cmd, self.raw, "终门缺命令：%s" % cmd)
        self.assertIn("[假设]` 清零", self.raw, "终门缺假设清零")
        for field in ("direction", "pages[].name", "states[].signals"):
            self.assertIn(field, self.raw, "假设清零未点名字段：%s" % field)

    # trace: B-6 SS-017-07（四态不许省 + 最小真实信号 + 收尾点名占位）
    def test_four_states_never_omitted(self):
        self.assertIn("四态不许省", self.raw, "缺四态不许省条款")
        self.assertIn("最小真实信号", self.raw, "缺不适用态的最小真实信号写法")
        self.assertIn("哪些态是占位", self.raw, "收尾未点名占位态")

    # trace: B-6 SS-017-04（删/改页面 id 前置扫 design_ref + 路由；只读扩展）
    def test_page_removal_scans_design_ref(self):
        self.assertIn("AC[].design_ref", self.raw, "缺前置扫 AC[].design_ref")
        self.assertIn("diy-epics-stories", self.raw, "悬空 design_ref 未路由回写权技能")
        self.assertIn("只读", self.raw, "未声明只读边界")

    # trace: B-9（消费口径：从 stack[].choice 取值 + 找不到时的明确处置）
    def test_b9_frontend_framework_value_path(self):
        self.assertIn("stack[].choice", self.raw, "缺 B9 取值路径")
        self.assertIn("停下问用户一次", self.raw, "缺找不到时的明确处置")

    # ------------------------------------------------------- C·3a 改造面（W1 新增）

    # trace: C·3a §2.8（长出 steps/ → 必补母本 §4 读取纪律锚串）
    def test_read_discipline_anchor_landed(self):
        self.assertIn(READ_DISCIPLINE, self.raw, "缺母本 §4 读取纪律锚串（steps/ 已落地）")

    # trace: C·3a §3.1（双源判定 + WDS 线门禁 + 缺源零产出）
    def test_dual_source_input_declared(self):
        self.assertIn("wds-scenarios.yaml", self.raw, "激活时未声明 WDS 线输入源")
        self.assertIn("prd.yaml", self.raw, "激活时未声明主线输入源")
        self.assertIn("零产出", self.raw, "缺源未声明零产出")
        self.assertIn("diy-wds-brief", self.raw, "非产品站未路由到 diy-wds-brief")

    # trace: C·3a §3.1 ★ 裁定 7 订正（pages[].id 值域按来源线定）
    def test_page_id_domain_per_line(self):
        self.assertIn("SC-<nn>.P<n>", self.raw, "WDS 线页 ID 域未落")
        self.assertIn("P-n", self.raw, "主线页 ID 域未落")

    # trace: C·3a §3.1（design_intent → 预选活动；design_status 推进写权）
    def test_wds_handover_contract(self):
        self.assertIn("design_intent", self.raw, "未接上游 design_intent 交接契约")
        self.assertIn("design_status", self.raw, "未声明 design_status 推进写权")

    # trace: C·3a 收尾补漏（W7 发现）——值域 5 值里 `L` 在设计侧无落点：上游
    #        `DESIGN_INTENT_ENUM` 的 `K`/`C`/`S`/`D` 各有活动文件（k-sketch / c-discuss /
    #        s-suggest / d-dream），`L`（上游 `steps/06-finish.md`：Later——到设计阶段再定）
    #        谁都不认。失效模式 = 主文件列了值域（`K|C|S|D|L`）却没给 `L` 的处置。
    #        判据（同 design_status 守卫的行定位口径，**不**扫全文）：`## 工作流` 段里
    #        含 `design_intent` 的那一行（= 九活动预选句）须同时含机器锚 `L` 与处置
    #        锚串「问用户一次」——删掉 `L` 的处置句即红。
    def test_design_intent_l_has_disposition(self):
        import re
        upstream = os.path.join(SKILLS, "diy-wds-scenarios", "scripts", "wds_scenarios.py")
        with open(upstream, encoding="utf-8") as fh:
            source = fh.read()
        enum_match = re.search(r"DESIGN_INTENT_ENUM\s*=\s*\(([^)]*)\)", source)
        self.assertIsNotNone(enum_match, "上游 diy-wds-scenarios 不再定义 DESIGN_INTENT_ENUM")
        self.assertIn('"L"', enum_match.group(1),
                      "上游 DESIGN_INTENT_ENUM 已无 `L`——本守卫的前提消失，须重裁")
        flow = self.raw.split("## 工作流")
        self.assertEqual(len(flow), 2, "主文件 `## 工作流` 段定位失败（缺段或重复）")
        preselect = [ln for ln in flow[1].splitlines() if "`design_intent`" in ln]
        self.assertEqual(
            len(preselect), 1,
            "工作流段 `design_intent` 预选句定位失败（命中 %d 行）" % len(preselect))
        self.assertIn("`L`", preselect[0],
                      "预选句列了值域却没给 `L` 的处置（K/C/S/D 有活动文件，L 无落点）")
        self.assertIn("问用户一次", preselect[0], "`L` 的处置未写「问用户一次」")

    # trace: C·3a §3.1（design_status 值域落地——上游 9 值机械枚举；写表外值即上游 ENUM_INVALID）
    # trace: V4-L-1 双向化——原守卫只断言「枚举 9 值在场」，查不出「主文件写了枚举外值」
    #        （缺口原失效模式 = 映射里自造「进行中值」类枚举外值）；补反向 ⊆ 断言。
    def test_design_status_value_domain_matches_upstream_enum(self):
        import re
        upstream = os.path.join(SKILLS, "diy-wds-scenarios", "scripts", "wds_scenarios.py")
        with open(upstream, encoding="utf-8") as fh:
            source = fh.read()
        match = re.search(r"DESIGN_STATUS_ENUM\s*=\s*\(([^)]*)\)", source)
        self.assertIsNotNone(match, "上游 diy-wds-scenarios 不再定义 DESIGN_STATUS_ENUM")
        enum_values = re.findall(r'"([a-z-]+)"', match.group(1))
        self.assertEqual(
            len(enum_values), 9,
            "上游 DESIGN_STATUS_ENUM 值数变了（%s）——本技能的值域映射须同步" % enum_values)
        for value in enum_values:
            self.assertIn("`%s`" % value, self.raw,
                          "主文件未给出 design_status 的值：%s" % value)
        # 反向：映射范围 = `## 规则` 段内同时提 `design_status` 与枚举名的那一行
        # （= 规则 1 的「阶段 → 值」映射句；**不**扫全文反引号串）。
        rules = self.raw.split("## 规则")
        self.assertEqual(len(rules), 2, "主文件 `## 规则` 段定位失败（缺段或重复）")
        mapped_lines = [ln for ln in rules[1].splitlines()
                        if "`design_status`" in ln and "DESIGN_STATUS_ENUM" in ln]
        self.assertEqual(
            len(mapped_lines), 1,
            "规则 1 的 design_status 值域映射句定位失败（命中 %d 行）" % len(mapped_lines))
        mapped = set(re.findall(r"`([a-z-]+)`", mapped_lines[0]))
        self.assertTrue(mapped, "映射句未提取到任何反引号状态值——提取规则已与主文件写法脱钩")
        self.assertEqual(
            mapped - set(enum_values), set(),
            "主文件映射句写了 DESIGN_STATUS_ENUM 之外的值：%s"
            % sorted(mapped - set(enum_values)))

    # trace: 段2 V-C 高-2（返工轮 R-B）——「声明有、落点无」失效模式：
    #        权威表（SKILL.md 规则 1）承诺 8 个推进档位，而 specified / building /
    #        built / approved / removed 在 steps/ 层命中 0（进度实际停在 explored）。
    #        本断言把「档位 → 步骤文件写点」机械化：上游 DESIGN_STATUS_ENUM 里除初值
    #        （`DESIGN_STATUS_INITIAL`，本技能不写）外的每个值，都须至少在一个 step
    #        文件中以反引号机器锚形式在场。
    def test_design_status_advance_stages_landed_in_steps(self):
        import re
        upstream = os.path.join(SKILLS, "diy-wds-scenarios", "scripts", "wds_scenarios.py")
        with open(upstream, encoding="utf-8") as fh:
            source = fh.read()
        enum_match = re.search(r"DESIGN_STATUS_ENUM\s*=\s*\(([^)]*)\)", source)
        self.assertIsNotNone(enum_match, "上游 diy-wds-scenarios 不再定义 DESIGN_STATUS_ENUM")
        enum_values = re.findall(r'"([a-z-]+)"', enum_match.group(1))
        initial_match = re.search(r'DESIGN_STATUS_INITIAL\s*=\s*"([a-z-]+)"', source)
        self.assertIsNotNone(initial_match, "上游不再定义 DESIGN_STATUS_INITIAL")
        initial = initial_match.group(1)
        self.assertIn(initial, enum_values, "上游初值不在枚举内")
        advance = [v for v in enum_values if v != initial]
        self.assertEqual(len(advance), 8, "推进档位数变了：%s" % advance)
        bodies = {}
        names = sorted(n for n in os.listdir(STEPS_DIR) if n.endswith(".md"))
        self.assertTrue(names, "steps/ 为空——推进档位无落点面")
        for name in names:
            with open(os.path.join(STEPS_DIR, name), encoding="utf-8") as fh:
                bodies[name] = fh.read()
        for value in advance:
            hits = sorted(n for n, body in bodies.items() if "`%s`" % value in body)
            self.assertTrue(
                hits, "推进档位 `%s` 在 steps/ 层无落点（权威表声明有、步骤层写不出）" % value)

    # trace: C·3a §3.2（九活动路由下沉 steps/，主文件只给路由）
    def test_nine_activities_routed_to_steps(self):
        self.assertIn("steps/", self.raw, "主文件未给 steps/ 路由")
        for activity in ("[C]", "[K]", "[S]", "[D]", "[P]", "[V]", "[W]", "[M]", "[H]"):
            self.assertIn(activity, self.raw, "九活动路由缺 %s" % activity)

    # trace: C·3a §3.3（原型循环：循环单元称「段」，不叫「页规格」）
    def test_prototype_loop_naming(self):
        self.assertIn("原型循环", self.raw, "缺原型循环路由")
        self.assertIn("段（section）", self.raw, "未钉死循环单元名（段）")

    # trace: C·3a §3.5 / §2.3（状态扩展零 schema 改动，只需授权表述）
    def test_extra_states_authorized(self):
        for state in ("离线", "权限拒绝", "冷启动"):
            self.assertIn(state, self.raw, "未授权四态之外的额外状态：%s" % state)

    # trace: C·3a §2.5（transition 命令的调用句；主文件只给命令不给实现）
    def test_transition_command_referenced(self):
        self.assertIn("transition --design", self.raw, "缺 transition 调用句")

    # trace: C·3a §2.3 / §3.2（open_questions 键 + 场景桥 + 复杂度启发式）
    def test_schema_extensions_declared(self):
        self.assertIn("open_questions", self.raw, "结构段未声明 open_questions 键")
        self.assertIn("token_scope", self.raw, "结构段未声明 token_scope 键")
        self.assertIn("场景桥", self.raw, "缺场景桥路由")

    # trace: C·3a 裁定 17（术语陷阱：wds-5[P] 不叫「页规格」）
    def test_no_prototyping_page_spec_confusion(self):
        self.assertNotIn("建页规格", self.raw, "残留裁定 17 的术语陷阱措辞")

    # trace: C·3a §3.7 ③（双源判定的机械面）——两个路由目标技能在场
    def test_routing_targets_installed(self):
        for skill in ("diy-prd", "diy-wds-brief"):
            path = os.path.join(SKILLS, skill, "SKILL.md")
            self.assertTrue(os.path.isfile(path), "缺源时的路由目标技能不在场：%s" % skill)

    # trace: C·3a §3.1（WDS 输入字段契约须与上游 `diy-wds-scenarios` 的声明逐字一致）
    def test_wds_upstream_contract_matches(self):
        upstream_path = os.path.join(SKILLS, "diy-wds-scenarios", "SKILL.md")
        with open(upstream_path, encoding="utf-8") as fh:
            upstream = fh.read()
        for token in ("design_intent", "design_status", "SC-01.P1"):
            self.assertIn(token, upstream, "上游 diy-wds-scenarios 不再声明 %r（交接契约已漂移）" % token)
        # `design_status` 初值与写权归属：上游设初值、本技能推进
        self.assertIn("design_status` 只设初值", upstream, "上游未声明 design_status 初值归属")
        for token in ("design_intent", "design_status", "SC-<nn>.P<n>"):
            self.assertIn(token, self.raw, "本技能未接上游契约键 %r" % token)

    # trace: C·3a 母本 §4 锚串（「以每个步骤开头的 `Read (input)` 行为唯一权威」）——
    #        锚串承诺了 steps/ 的形态，此处把它机械化：每个步骤文件都须有 `Read (input)` 行。
    def test_every_step_file_declares_read_input(self):
        names = sorted(n for n in os.listdir(STEPS_DIR) if n.endswith(".md"))
        self.assertTrue(names, "steps/ 为空")
        for name in names:
            with open(os.path.join(STEPS_DIR, name), encoding="utf-8") as fh:
                body = fh.read()
            self.assertIn("**Read (input):**", body, "%s 缺 `Read (input)` 行" % name)
            self.assertIn("**Write (output):**", body, "%s 缺 `Write (output)` 行" % name)

    # trace: C·3a §3.6（主文件只给路由）——主文件点名的每个 steps 文件都必须在场
    def test_routed_step_files_exist(self):
        import re
        routed = set(re.findall(r"steps/([a-z0-9-]+\.md)", self.raw))
        self.assertEqual(len(routed), 10, "主文件点名的 steps 文件数变了：%s" % sorted(routed))
        on_disk = set(n for n in os.listdir(STEPS_DIR) if n.endswith(".md"))
        self.assertEqual(routed, on_disk,
                         "主文件路由与 steps/ 实况不符——缺文件 %s；未路由 %s"
                         % (sorted(routed - on_disk), sorted(on_disk - routed)))


if __name__ == "__main__":
    unittest.main()
