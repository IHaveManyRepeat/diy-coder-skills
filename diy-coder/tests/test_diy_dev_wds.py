# -*- coding: utf-8 -*-
"""diy-dev 双模式（主线 + WDS 线）文档契约与引擎实跑（C·3a 段2 · W3）。

两半：
  1. **文档契约**（`SkillContractTests`）——§5.1 双模式分支 / §5.2 浏览器强制门 /
     §5.3 与 `diy-wds-evolution` 的边界 / §2.8 母本 §4 锚串 / §2.2 主线保真面。
  2. **引擎实跑**（`WdsModeRunTests`）——技能教的 WDS 命令真跑：`design.py transition`
     （结构稿中 → 待验收）、页级门真拦（`GATE_FAILED`）、旧稿缺 `status` 键读作 `未开始`、
     token 闸 `audit`；主线侧对照跑 `diyc.py transition`（两模式各一次，§5.5 ①）。

判据与设计侧同源：门的判据 `states[].signals` / 三要素句 / 定性四项与
`diy-design/steps/prototype-loop.md` 逐字对齐（同一条门两端互引，不各说一套）。
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
SKILLS = os.path.join(HERE, "..", "skills")
SKILL_MD = os.path.join(SKILLS, "diy-dev", "SKILL.md")
STEPS_DIR = os.path.join(SKILLS, "diy-dev", "steps")
DESIGN_PY = os.path.join(SKILLS, "diy-design", "scripts", "design.py")
DESIGN_SRC = os.path.join(SKILLS, "diy-design", "scripts", "design.py")
DESIGN_SKILL_MD = os.path.join(SKILLS, "diy-design", "SKILL.md")
PROTOTYPE_LOOP_MD = os.path.join(SKILLS, "diy-design", "steps", "prototype-loop.md")
DIYC_PY = os.path.join(SKILLS, "diy-tools", "scripts", "diyc.py")
NL = chr(10)

# 母本锚串（值同 `test_suite_texts.py` 的 ANCHOR_* 常量；本文件另作显式在场断言）
INSTANCE_ZH = ("实例解析（FR-4.5/D-9）由工具脚本执行：运行 "
               "`python \"{project-root}/.claude/skills/diy-tools/scripts/diyc.py\" "
               "resolve [--instance <name>] --json`，把回执里的 `output_dir` "
               "当作本次运行唯一的读写根目录。")
INSTANCE_EN_MARK = "Instance resolution (FR-4.5/D-9)"
RESOLVE_KEYS = ("解析 `project.communication_language` / "
                "`project.document_output_language` / `paths.output_dir`")
READ_DISCIPLINE = ("读取纪律：预载预算 = 本文件、上述配置与回执、`steps/` 下当前那一个文件"
                   "——绝不批量预载；执行期读取以每个步骤开头的 `Read (input)` 行为唯一权威，"
                   "**主文件不列举封闭清单**。")
RENDER_SILENT = "渲染是静默旁路——只写调用命令"
PRECISE_ZH = ("- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；"
              "不复述上游已写的信息（引用 ID）；不写没有信息量的套话。")
DISCIPLINE_ZH = ("- **写作纪律。** 主字段 = 大白话主句；数字/枚举内联；"
                 "机器语法（命令/旗标/路径）进括号；机器锚点逐字保留"
                 "（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 "
                 "`diy-design` 的 detect 启发式。schema 若定义 `plain`："
                 "一行写清该条目为什么存在，绝不写是什么（转述会漂移）；"
                 "只写难懂的条目。若定义 `detail`：过程叙述——结论留在主字段。")

# 主线保真面（§2.2 diy-dev 行）逐条的机械抓手：条款关键词
MAINLINE_TERMS = ("TDD 门（AC-7.2）", "test_refs", "先红后绿", "`skip` 是「待实现」标记",
                  "最小实现", "# trace: S-9 AC-9.1 TC-9.1.1", "真源回填", "状态写权窄",
                  "环转不了绿就诚实停下", "照设计稿采用——零重写", "设计稿代码",
                  "`[假设]` 前缀")

FOUR_STATES = NL.join([
    "  states:",
    "  - name: 悬停",
    "    signals: [图标, 动效]",
    "  - name: 空态",
    "    signals: [文字]",
    "  - name: 加载中",
    "    signals: [图标, 动效]",
    "  - name: 错误",
    "    signals: [图标, 文字]",
])

GOOD_HTML = NL.join([
    "<!DOCTYPE html>",
    '<html lang="zh-CN">',
    "<head>",
    '<meta charset="utf-8">',
    "<style>",
    ":root {",
    "  --color-bg: #ffffff;",
    "  --color-text: #1a1a1a;",
    "  --color-accent: #0a5c8c;",
    "}",
    "body { background: var(--color-bg); color: var(--color-text); }",
    "button { background: var(--color-accent); }",
    "</style>",
    "</head>",
    "<body>",
    "<h1>首页</h1>",
    "<button>开始</button>",
    "</body>",
    "</html>",
])


def dev_docs():
    """本技能全部 .md（SKILL.md + steps/*.md）：(相对名, 正文)。"""
    out = []
    with io.open(SKILL_MD, encoding="utf-8") as fh:
        out.append(("SKILL.md", fh.read()))
    for name in sorted(n for n in os.listdir(STEPS_DIR) if n.endswith(".md")):
        with io.open(os.path.join(STEPS_DIR, name), encoding="utf-8") as fh:
            out.append(("steps/" + name, fh.read()))
    return out


def design_text(project_status="已定稿", page_status="结构稿中", page_id="SC-01.P1",
                with_prototype=True, with_states=True):
    """合成 WDS 侧 design.yaml；page_status=None 表示不写该键（旧稿形态）。"""
    lines = [
        "project:",
        "  name: wds-mini",
        "  status: %s" % project_status,
        "  updated: 2026-01-01",
        "direction: 瑞士编辑风——大字阶对比、留白节奏、单强调色",
        "frontend_framework: html",
        "tokens:",
        "  color:",
        "    bg: '#ffffff'",
        "    surface: '#f5f5f2'",
        "    text: '#1a1a1a'",
        "    text_muted: '#5a5a5a'",
        "    accent: '#0a5c8c'",
        "    accent_text: '#ffffff'",
        "  spacing:",
        "    unit: 4px",
        "    scale: [4px, 8px, 16px, 24px, 48px]",
        "  typography:",
        "    family_base: \"'Source Han Sans', sans-serif\"",
        "    family_heading: \"'Source Han Serif', serif\"",
        "    scale: [0.875rem, 1rem, 1.25rem, 2rem, 3rem]",
        "pages:",
        "- id: %s" % page_id,
        "  name: 首页",
        "  route: /",
    ]
    if page_status is not None:
        lines.append("  status: %s" % page_status)
    if with_states:
        lines.append(FOUR_STATES)
    if with_prototype:
        lines.append("  prototype: prototypes/%s.html" % page_id)
    return NL.join(lines) + NL


def run_engine(args, cwd=None):
    return subprocess.run([sys.executable, DESIGN_PY] + args,
                          capture_output=True, text=True, encoding="utf-8", cwd=cwd)


def engine_statuses():
    """从 design.py 源码取页状态词表与合法边（读源码，不复制常量）。"""
    with io.open(DESIGN_SRC, encoding="utf-8") as fh:
        src = fh.read()
    statuses = re.search(r"PAGE_STATUSES\s*=\s*\(([^)]*)\)", src)
    edges = re.search(r"LEGAL_EDGES\s*=\s*frozenset\(\{(.*?)\}\)", src, re.S)
    return (re.findall(r'"([^"]+)"', statuses.group(1)),
            set(re.findall(r'\("([^"]+)", "([^"]+)"\)', edges.group(1))))


class SkillContractTests(unittest.TestCase):
    """SKILL.md 契约冒烟：母本逐字 + 四段结构 + 双模式分支 + 保真面。"""

    def setUp(self):
        with io.open(SKILL_MD, encoding="utf-8") as fh:
            self.raw = fh.read()

    # trace: 中文化轮（母本 §1 / §2 / §3 / §5 / §6 中文定稿逐字）
    def test_mother_texts_verbatim(self):
        self.assertIn(INSTANCE_ZH, self.raw, "缺母本 §1 中文定稿实例解析句")
        self.assertNotIn(INSTANCE_EN_MARK, self.raw, "已转中文定稿，仍残留 §1 英文原形")
        self.assertIn(RESOLVE_KEYS, self.raw, "缺母本 §3 配置解析键")
        self.assertIn(RENDER_SILENT, self.raw, "缺母本 §5 渲染静默锚串")
        self.assertIn("viewer.py\" --project-root", self.raw, "缺 viewer 命令全文")
        self.assertIn(PRECISE_ZH, self.raw, "缺母本 §6 精准简练条款")
        self.assertIn(DISCIPLINE_ZH, self.raw, "缺母本 §2 写作纪律块")

    # trace: C·3a §2.8（本技能本批长出 `steps/` → 母本 §4 锚串必补）
    def test_read_discipline_anchor_landed(self):
        self.assertIn(READ_DISCIPLINE, self.raw, "缺母本 §4 读取纪律锚串（steps/ 已落地）")

    # trace: C·3a §2.1（四段结构不变 + 软控制线 = 现状 73 + 20% = ≤88；超线须回报理由）
    def test_four_sections_and_line_budget(self):
        self.assertLessEqual(len(self.raw.splitlines()), 88, "薄主文件超出 88 行控制线")
        for section in ("## 激活时", "## 工作流", "## 结构", "## 规则"):
            self.assertIn(section, self.raw, "缺四段结构：%s" % section)
        self.assertIn("# ↑ 中文：", self.raw, "description 缺中文注释")

    # trace: C·3a §2.2（diy-dev 保真面：主线模式一条不丢）
    def test_mainline_contract_preserved(self):
        for term in MAINLINE_TERMS:
            self.assertIn(term, self.raw, "主线保真面缺条款：%s" % term)
        self.assertEqual(self.raw.count("真源回填"), 1, "真源回填条款重复插入")

    # trace: C·3a §5.1（双模式分支：门禁单一判据 + 零产出 + 路由）
    def test_dual_mode_branch_declared(self):
        self.assertIn("`{output_dir}/design.yaml` 的 `project.status: 已定稿`", self.raw,
                      "未声明 WDS 模式门禁（design.yaml 的 project.status）")
        self.assertIn("`{output_dir}/sprint.yaml` 的 `project.status: 已定稿`", self.raw,
                      "未声明主线模式门禁（sprint.yaml 的 project.status）")
        self.assertIn("两源俱在 → 问用户一次走哪条", self.raw, "缺两源俱在的处置")
        self.assertIn("**零产出**", self.raw, "缺零产出声明")
        for route in ("`diy-sprint`", "`diy-design`", "`diy-wds-brief`"):
            self.assertIn(route, self.raw, "缺源时的路由目标：%s" % route)

    # trace: C·3a §5.1（WDS 侧三件：目标 = 结构稿中页 / 测试源 = states[].signals / 回填经 transition）
    def test_wds_target_test_source_and_writeback(self):
        self.assertIn("`pages[].status: 结构稿中` 的页", self.raw, "未声明 WDS 目标页判据")
        self.assertIn("键缺失 = `未开始`", self.raw, "未声明旧稿缺 status 键的读法")
        self.assertIn("`states[].signals`", self.raw, "未声明 WDS 测试源")
        self.assertIn("`design.py transition`", self.raw, "未声明 WDS 回填经引擎")
        self.assertIn("不手改", self.raw, "未禁止手改 pages[].status")

    # trace: C·3a §5.2 / §2.6（浏览器强制门三要素 + 裁定 21 三情形 + 责任分割）
    def test_browser_gate_frozen_terms(self):
        self.assertIn("浏览器强制门", self.raw, "缺浏览器强制门条款")
        self.assertIn("Playwright", self.raw, "验手段未点名 Playwright")
        self.assertIn("不得呈给用户", self.raw, "缺「未过不得呈人」的强制语义")
        self.assertIn("Flow 感觉 / 视觉层级 / 清晰度 / 一致性", self.raw, "缺定性四项")
        for term in ("不得静默降级", "不得无条件硬停", "留名"):
            self.assertIn(term, self.raw, "裁定 21 缺边界句：%s" % term)
        self.assertIn("先捕基线", self.raw, "改既有功能未要求捕基线")

    # trace: C·3a §9 #13（副作用分层：浏览器自验证属①档，②档只给 viewer 这类 GUI 展示）
    def test_side_effect_tier_layering(self):
        self.assertIn("①档", self.raw, "缺①档归属")
        self.assertIn("②档", self.raw, "缺②档边界")
        self.assertIn("打开浏览器", self.raw, "未点名②档的 GUI 展示动作")

    # trace: C·3a §5.3 / 裁定 20（与 diy-wds-evolution 的边界：两端互引，本技能写自己这端）
    def test_boundary_with_wds_evolution(self):
        self.assertIn("`diy-wds-evolution`", self.raw, "未声明演进轮归 diy-wds-evolution")
        self.assertIn("演进轮", self.raw, "缺演进轮边界句")
        self.assertIn("全量验收归本技能", self.raw, "未声明全量验收归属（B7b 裁定 10）")
        self.assertIn("`design_status` 一律只读", self.raw, "未声明 design_status 只读边界")

    # trace: C·3a §5.1（主文件只给路由：WDS 四步全下沉 steps/）
    def test_wds_steps_routed_and_files_exist(self):
        routed = set(re.findall(r"steps/([a-z0-9-]+\.md)", self.raw))
        on_disk = set(n for n in os.listdir(STEPS_DIR) if n.endswith(".md"))
        self.assertEqual(routed, on_disk,
                         "主文件路由与 steps/ 实况不符——缺文件 %s；未路由 %s"
                         % (sorted(routed - on_disk), sorted(on_disk - routed)))
        self.assertEqual(len(routed), 5, "WDS 路由文件数变了：%s" % sorted(routed))
        for name in sorted(on_disk):
            with io.open(os.path.join(STEPS_DIR, name), encoding="utf-8") as fh:
                body = fh.read()
            self.assertIn("**Read (input):**", body, "%s 缺 `Read (input)` 行" % name)
            self.assertIn("**Write (output):**", body, "%s 缺 `Write (output)` 行" % name)

    # trace: C·3a §5.1（WDS 侧写面只有一个通道：design.py transition；不碰主线命令）
    def test_wds_steps_have_single_write_channel(self):
        for rel, body in dev_docs():
            if not rel.startswith("steps/"):
                continue
            for banned in ("diyc.py transition", "diyc.py green"):
                self.assertNotIn(banned, body, "%s 混入主线写回命令 %s" % (rel, banned))
        with io.open(os.path.join(STEPS_DIR, "wds-finalize.md"), encoding="utf-8") as fh:
            finalize = fh.read()
        self.assertIn("design.py\" transition", finalize, "wds-finalize 未给 transition 调用句")
        for code in ("GATE_FAILED", "ILLEGAL_TRANSITION", "UNKNOWN_ID"):
            self.assertIn(code, finalize, "wds-finalize 未给回执码读法：%s" % code)

    # trace: C·3a §5.6 引用句核对（同一条门两端互引）——diy-design 侧的执行面在场
    def test_gate_matches_design_side(self):
        with io.open(PROTOTYPE_LOOP_MD, encoding="utf-8") as fh:
            design_side = fh.read()
        for term in ("states[].signals", "Playwright", "不得呈给用户",
                     "Flow 感觉 / 视觉层级 / 清晰度 / 一致性"):
            self.assertIn(term, design_side, "设计侧原型循环缺同一判据：%s" % term)
        with io.open(os.path.join(STEPS_DIR, "wds-self-verify.md"), encoding="utf-8") as fh:
            dev_side = fh.read()
        for term in ("states[].signals", "Playwright", "不得呈给用户",
                     "Flow 感觉 / 视觉层级 / 清晰度 / 一致性"):
            self.assertIn(term, dev_side, "实现侧自验证缺同一判据：%s" % term)

    # trace: C·3a 裁定 22 §圈定面（WDS 页 ID 域以段1 W1 定义为准：SC-<nn>.P<n>）
    def test_wds_page_id_domain_from_upstream(self):
        self.assertIn("SC-<nn>.P<n>", self.raw, "未接 WDS 线页 ID 域")
        with io.open(DESIGN_SKILL_MD, encoding="utf-8") as fh:
            design_skill = fh.read()
        self.assertIn("SC-<nn>.P<n>", design_skill, "设计侧页 ID 域声明漂移")

    # trace: C·3a §5.5 ①（双模式的路由目标技能在场，否则零产出路由落空）
    def test_routing_targets_installed(self):
        for skill in ("diy-sprint", "diy-design", "diy-review", "diy-wds-evolution",
                      "diy-epics-stories"):
            path = os.path.join(SKILLS, skill, "SKILL.md")
            self.assertTrue(os.path.isfile(path), "路由目标技能不在场：%s" % skill)


class WdsModeRunTests(unittest.TestCase):
    """引擎实跑：技能教的 WDS 命令真跑一遍（不采信文档自述）。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = os.path.join(self.tmp.name, "diy-output")

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, rel, content):
        path = os.path.join(self.out, rel)
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with io.open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
        return path

    # trace: C·3a §5.1（WDS 回填目标）——结构稿中 → 待验收 走通，回执键与教学句对齐
    def test_transition_walks_page_to_pending_acceptance(self):
        dpath = self.write("design.yaml", design_text(page_status="结构稿中"))
        self.write("prototypes/SC-01.P1.html", GOOD_HTML)
        r = run_engine(["transition", "--design", dpath, "--page", "SC-01.P1",
                        "--to", "待验收", "--json"])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads(r.stdout)
        self.assertTrue(data["ok"])
        self.assertEqual((data["command"], data["from"], data["to"]),
                         ("transition", "结构稿中", "待验收"))
        for key in ("ok", "command", "violations", "warnings", "counts", "file",
                    "page", "from", "to", "updated", "next_hint"):
            self.assertIn(key, data, "回执缺键：%s" % key)
        self.assertTrue(os.path.isfile(dpath + ".prev"), "写回前未落 .prev 快照")
        with io.open(dpath, encoding="utf-8") as fh:
            after = fh.read()
        self.assertIn("status: 待验收", after, "页状态未写回")

    # trace: C·3a §5.2 门不过不许写——结构稿缺失时引擎判 GATE_FAILED 且零写入
    def test_page_gate_blocks_writeback(self):
        dpath = self.write("design.yaml", design_text(page_status="结构稿中",
                                                     with_prototype=False))
        before = io.open(dpath, encoding="utf-8").read()
        r = run_engine(["transition", "--design", dpath, "--page", "SC-01.P1",
                        "--to", "待验收", "--json"])
        self.assertEqual(r.returncode, 1, r.stdout)
        data = json.loads(r.stdout)
        self.assertFalse(data["ok"])
        self.assertEqual({x["code"] for x in data["violations"]}, {"GATE_FAILED"})
        self.assertEqual(io.open(dpath, encoding="utf-8").read(), before, "拒绝路径仍写了盘")

    # trace: C·3a §5.1（键缺失 = 未开始：旧稿兼容，W2 转交口径）
    def test_missing_status_key_reads_as_not_started(self):
        dpath = self.write("design.yaml", design_text(page_status=None, with_prototype=False))
        r = run_engine(["transition", "--design", dpath, "--page", "SC-01.P1",
                        "--to", "结构稿中", "--json"])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(json.loads(r.stdout)["from"], "未开始")

    # trace: C·3a §5.1 红线（token 单一源闸：称绿前 audit 零 one-off-*）
    def test_token_audit_is_clean_on_baseline(self):
        dpath = self.write("design.yaml", design_text())
        impl = self.write("src/index.html", GOOD_HTML)
        r = run_engine(["audit", "--design", dpath, "--src", impl, "--json"])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(json.loads(r.stdout)["ok"])
        with io.open(os.path.join(STEPS_DIR, "wds-implement.md"), encoding="utf-8") as fh:
            self.assertIn("one-off-color", fh.read(), "实现步未教 token 闸")

    # trace: C·3a §9 #4（ID 是唯一引用键：表外页 ID 走 UNKNOWN_ID 而非静默新建）
    def test_unknown_page_id_is_rejected(self):
        dpath = self.write("design.yaml", design_text())
        r = run_engine(["transition", "--design", dpath, "--page", "SC-09.P9",
                        "--to", "待验收", "--json"])
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertEqual({x["code"] for x in json.loads(r.stdout)["violations"]},
                         {"UNKNOWN_ID"})

    # trace: C·3a §9 #3（WDS 门禁：上游未定稿 → 停下零产出）——门的判据从主文件句子里取，
    #        「句可机械解析 + 对两种 fixture 有分辨力」两项一起查（防文档漂移成不可核的散文）
    def test_wds_gate_expression_is_parseable_and_discriminating(self):
        with io.open(SKILL_MD, encoding="utf-8") as fh:
            doc = fh.read()
        m = re.search(r"`\{output_dir\}/(design\.yaml)` 的 `(project\.status): ([^`]+)`", doc)
        self.assertIsNotNone(m, "主文件未给出可机械解析的 WDS 门禁句")
        self.assertEqual(m.group(3), "已定稿", "WDS 门禁的目标值变了：%s" % m.group(3))
        verdict = {}
        for status in ("草稿", "已定稿"):
            path = self.write("gate-%s/design.yaml" % status, design_text(project_status=status))
            with io.open(path, encoding="utf-8") as fh:
                actual = re.search(r"^  status: (\S+)$", fh.read(), re.M).group(1)
            verdict[status] = (actual == m.group(3))
        self.assertEqual(verdict, {"草稿": False, "已定稿": True},
                         "门禁判据不可判别：%s" % verdict)

    # trace: C·3a §5.5 ①（两模式各一次实跑：主线侧走 diyc.py，WDS 侧走 design.py）
    def test_mainline_command_still_runs(self):
        sprint = NL.join([
            "project:",
            "  name: mini",
            "  status: 已定稿",
            "  created: '2026-01-01'",
            "  updated: '2026-01-02'",
            "tasks:",
            "- story: S-1",
            "  status: 待办",
            "  test_refs: [TC-1.1.1]",
        ]) + NL
        self.write("sprint.yaml", sprint)
        r = subprocess.run([sys.executable, DIYC_PY, "transition",
                            "--project-root", self.tmp.name,
                            "--story", "S-1", "--to", "进行中", "--json"],
                           capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(json.loads(r.stdout)["ok"])
        with io.open(os.path.join(self.out, "sprint.yaml"), encoding="utf-8") as fh:
            self.assertIn("status: 进行中", fh.read())

    # trace: C·3a §5.1（状态词表与合法边以段1 引擎为准——文档引用漂移即红）
    def test_statuses_and_edges_are_engine_legal(self):
        statuses, edges = engine_statuses()
        self.assertEqual(len(statuses), 5, "引擎页状态词表变了：%s" % statuses)
        self.assertIn(("结构稿中", "待验收"), edges, "引擎不再允许 结构稿中 → 待验收")
        with io.open(SKILL_MD, encoding="utf-8") as fh:
            raw = fh.read()
        for status in ("未开始", "结构稿中", "待验收", "已批准"):
            self.assertIn(status, raw, "主文件未引用引擎页状态：%s" % status)
        self.assertNotIn("已阻塞", statuses, "引擎页状态词表混入编排层状态（裁定 6）")
        for rel, body in dev_docs():
            if rel.startswith("steps/"):
                self.assertNotIn("已阻塞", body, "%s 引入了引擎表外的页状态" % rel)


if __name__ == "__main__":
    unittest.main()
