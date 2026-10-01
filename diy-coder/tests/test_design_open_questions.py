# -*- coding: utf-8 -*-
"""W7 跨工位测试（C·3a 任务书 §6 断言面 4 / 5）。

文件名沿用 §6 的拆分建议；两面都以 `open_questions` / 终门为轴：

- 断言面 4「`transition` 改状态**后**重跑 `validate` 是否自洽」——引擎的两个命令归 W2，
  但**配合语义**（谁在哪一步写、写完该看到什么）由 W1 的工作流句与 W3 / W4 的写权声明
  定义；「每条边都有唯一写者」这一条只有把四份文档与引擎放在一起才可断言。
- 断言面 5「终门联动：`validate` 过 + `open_questions` 零 `待办` → 才可写 `已定稿`」——
  门是 W1 定的（`## 工作流` 第 6 步的「定稿走三道」）、命令是 W2 实现的。

面 1 / 2 / 3 / 6 / 7 / 8 在同批新增的 `test_design_wds.py`。
**去重纪律（§6 末段）**：与 W1/W2/W3/W4/W5/W6/W8/W9 的测试文件逐条比对过断言串
（`grep` 机械比对）；W2 已逐条覆盖的「单边回执形状 / 单点结构违规」不在此重复。
"""
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
SKILLS = os.path.join(HERE, "..", "skills")
DESIGN_SKILL_MD = os.path.join(SKILLS, "diy-design", "SKILL.md")
DESIGN_PY = os.path.join(SKILLS, "diy-design", "scripts", "design.py")
NL = chr(10)

# 页状态边的**写者归属**（文档面）：技能目录 → 该技能声明自己写的边；
# `user` = 文档点名「无技能代劳、由用户直接调 transition」的边。
DOCUMENTED_OWNERS = {
    "diy-design": {("未开始", "结构稿中"), ("结构稿中", "已移除")},
    "diy-dev": {("结构稿中", "待验收"), ("结构稿中", "已移除")},
    "diy-review": {("待验收", "结构稿中")},
    "user": {("待验收", "已批准"), ("待验收", "已移除"), ("已批准", "结构稿中"),
             ("已批准", "已移除"), ("已移除", "结构稿中")},
}
# 每个写者的文档证据（技能目录 → 逐字句所在文件与串）；diy-review 用「教了哪些边」的
# 机械提取（见 test_each_owner_claim_is_backed_by_verbatim_text），不引它的命令全文——
# 该命令面已由 W4 自己的断言钉死（去重纪律：不重复单工位已覆盖的断言串）。
OWNER_EVIDENCE = {
    "diy-design": ("steps/prototype-loop.md", "经 `transition` 推到 `结构稿中`"),
    "diy-dev": ("SKILL.md", "只写 `结构稿中 → 待验收` 与 `结构稿中 → 已移除`"),
}
# 四份技能主文件（写权声明面）
OWNER_SKILLS = ("diy-design", "diy-dev", "diy-review", "diy-wds-evolution")

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

GOOD_PROTOTYPE = NL.join([
    "<!DOCTYPE html>",
    '<html lang="zh-CN">',
    "<head>",
    '<meta charset="utf-8">',
    "<title>首页</title>",
    "<style>",
    ":root {",
    "  --color-bg: #ffffff;",
    "  --color-text: #1a1a1a;",
    "}",
    "body { background: var(--color-bg); color: var(--color-text); }",
    "</style>",
    "</head>",
    "<body>",
    "<h1>首页</h1>",
    '<button type="button">开始</button>',
    "</body>",
    "</html>",
])

IMPL_JS = NL.join([
    "// trace: SC-01.P1 加载中",
    "export function mount(root) {",
    "  root.style.background = 'var(--color-bg)';",
    "}",
])


def read(path):
    with io.open(path, encoding="utf-8") as fh:
        return fh.read()


def run(script, args):
    return subprocess.run([sys.executable, script] + args,
                          capture_output=True, text=True, encoding="utf-8")


def run_json(script, args):
    proc = run(script, args)
    try:
        return proc.returncode, json.loads(proc.stdout)
    except ValueError:
        raise AssertionError("回执不是单行 JSON：rc=%s%s%s"
                             % (proc.returncode, NL, proc.stdout + proc.stderr))


def engine_module():
    """把 `design.py` 当模块加载，直接取引擎常量（不复制、不解析源码文本）。"""
    spec = importlib.util.spec_from_file_location("design_engine_for_w7", DESIGN_PY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def design_text(project_status="草稿", page_status="待验收",
                open_questions=None, with_questions=True):
    """WDS 线 design.yaml：一页四态齐 + 结构稿在场（页级门可过）。"""
    lines = [
        "project:",
        "  name: wds-mini",
        "  status: %s" % project_status,
        "  created: 2026-01-01",
        "  updated: 2026-01-01",
        "direction: 瑞士编辑风——大字阶对比、留白节奏、单强调色",
        "frontend_framework: html",
        "form_factor: 响应式 Web",
        "modes: 亮",
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
        "- id: SC-01.P1",
        "  name: 首页",
        "  route: /",
    ]
    if page_status is not None:
        lines.append("  status: %s" % page_status)
    lines.append(FOUR_STATES)
    lines.append("  prototype: prototypes/SC-01.P1.html")
    if with_questions:
        lines.append("open_questions:")
        lines.append("- id: Q-1")
        lines.append("  question: 首页空态的文案由谁定稿？")
        if open_questions == "resolved":
            lines.append("  status: 已解决")
            lines.append("  answer: 产品经理已定稿")
        else:
            lines.append("  status: 待办")
    return NL.join(lines) + NL


class W7Harness(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="w7-")
        self.root = self.tmp
        self.out = os.path.join(self.root, "diy-output")
        os.makedirs(self.out, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write(self, rel, content):
        path = os.path.join(self.out, rel)
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        text = content if isinstance(content, str) else yaml.safe_dump(
            content, allow_unicode=True, sort_keys=False, default_flow_style=False)
        with io.open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
        return path

    def doc(self, rel="design.yaml"):
        with io.open(os.path.join(self.out, rel), encoding="utf-8") as fh:
            return yaml.safe_load(fh)

    def validate(self, path):
        return run_json(DESIGN_PY, ["validate", "--design", path, "--json"])

    def transition(self, path, to, reason=None):
        args = ["transition", "--design", path, "--page", "SC-01.P1", "--to", to]
        if reason is not None:
            args += ["--reason", reason]
        return run_json(DESIGN_PY, args + ["--json"])


# ---------------------------------------------------------------- 面 4

class EdgeOwnershipTests(unittest.TestCase):
    """断言面 4（前半）：9 条合法边各有**唯一**文档写者，且并集恰等于引擎边集。

    写者声明散在 W1（design）/ W3（dev）/ W4（review）三份文档里，引擎常量归 W2——
    只有三份文档与引擎放在一起，才可断言「无主边」与「多头边」都不存在。
    **与既有测试的分工**：W3 的 `test_statuses_and_edges_are_engine_legal` 只看两条边
    是否在引擎表内；W4 的 `test_taught_design_edges_are_engine_legal` 只看 review 一份
    文档的 `--to` 目标；本类断言**九条边的归属并集**。
    """

    # trace: C·3a §6 面 4（写者并集 == 引擎 9 条合法边；无主边与多头边都判红）
    def test_owner_union_equals_engine_legal_edges(self):
        edges = set(engine_module().LEGAL_EDGES)
        self.assertEqual(len(edges), 9, "引擎合法边数变了：%s" % sorted(edges))
        union = set()
        for owner, claimed in DOCUMENTED_OWNERS.items():
            union |= claimed
        self.assertEqual(union - edges, set(),
                         "文档声明了引擎表外的边：%s" % sorted(union - edges))
        self.assertEqual(edges - union, set(),
                         "引擎有边却无文档写者（无主边）：%s" % sorted(edges - union))
        claimed_by = {}
        for owner, claimed in DOCUMENTED_OWNERS.items():
            for edge in claimed:
                claimed_by.setdefault(edge, []).append(owner)
        shared = {edge: owners for edge, owners in claimed_by.items() if len(owners) > 1}
        self.assertEqual(shared, {("结构稿中", "已移除"): ["diy-design", "diy-dev"]},
                         "多头边不在预期集合内：%s" % shared)
        self.assertIn("同一边、阶段不同", read(os.path.join(SKILLS, "diy-dev", "SKILL.md")),
                      "设计期/实现期分工的理由句缺失——多头边失去解释")

    # trace: C·3a §6 面 4（每条归属都有文档证据；用户边不得被任何技能代写）
    def test_each_owner_claim_is_backed_by_verbatim_text(self):
        for owner, (rel, quote) in sorted(OWNER_EVIDENCE.items()):
            with self.subTest(owner=owner):
                doc = read(os.path.join(SKILLS, owner, rel))
                self.assertIn(quote, doc, "%s 的写权声明缺逐字句：%s" % (owner, quote))
        # review 侧：从它自己教的**页级**命令里机械提取边目标（不引命令全文——
        # W4 已钉死那一句）；只取 design.py 调用行，避免混入主线任务态
        # trace: C·12 W1-R1 读源扩面（lead 裁定 2026-10-01，W3-R1 同款）——diy-review 拆
        #        steps 后 design.py 调用行下沉，读源从主文件扩为「主文件 + steps/ 拼接」
        #        （文档面 = 教学面，与 test_diy_review_wds 同口径）；断言本体零改动
        def page_targets(skill):
            body = read(os.path.join(SKILLS, skill, "SKILL.md"))
            steps_dir = os.path.join(SKILLS, skill, "steps")
            if os.path.isdir(steps_dir):
                body += NL + NL.join(
                    read(os.path.join(steps_dir, name))
                    for name in sorted(os.listdir(steps_dir)) if name.endswith(".md"))
            return set(target for line in body.splitlines() if "design.py" in line
                       for target in re.findall(r"--to\s+([^\s\"`]+)", line))

        taught = page_targets("diy-review")
        self.assertTrue(taught, "未从 diy-review 扫到任何页级 --to 目标——取数规则脱钩")
        self.assertEqual(taught, {"结构稿中"}, "review 教的回修边目标变了：%s" % sorted(taught))
        # 用户边（待验收 → 已批准）与四条无技能代劳的边：四份主文件一律不得教成自己的动作
        for skill in OWNER_SKILLS:
            with self.subTest(skill=skill):
                targets = page_targets(skill)
                self.assertNotIn("已批准", targets,
                                 "%s 把用户批准边教成自己的动作" % skill)
        design = read(DESIGN_SKILL_MD)
        self.assertIn("本技能不写这四条边", design, "设计侧未声明四条无技能代劳的边")


class StateChainConvergenceTests(W7Harness):
    """断言面 4（后半）：链式改状态后重跑 `validate` 是否自洽。

    从 `待验收` 起把**其余**七条边依次走一遍（面 8 已覆盖 未开始 → 结构稿中 → 待验收）：
    回修 → 重提 → 用户批准 → 重开 → 重提 → 废弃 → 恢复；每一步写回后 `validate` 必须
    仍绿，链尾的 ID 集与起点一致。**与既有测试的分工**：W2 逐边独立跑（每次新夹具）；
    本类只跑**链**——查的是「多次写回后引擎仍自洽」。
    """

    def setUp(self):
        super().setUp()
        self.path = self.write("design.yaml", design_text(page_status="待验收"))
        self.write("prototypes/SC-01.P1.html", GOOD_PROTOTYPE)

    def step(self, to, reason=None):
        rc, data = self.transition(self.path, to, reason)
        self.assertEqual(rc, 0, json.dumps(data, ensure_ascii=False))
        self.assertEqual(data["to"], to)
        rc2, data2 = self.validate(self.path)
        self.assertEqual(rc2, 0, "写回 %s 后 validate 不再自洽：%s"
                         % (to, json.dumps(data2, ensure_ascii=False)))

    # trace: C·3a §6 面 4（七条边的链式往返：每步写回后 validate 绿 + ID 集稳定）
    def test_documented_chain_keeps_validate_green_and_ids_stable(self):
        ids_before = [p["id"] for p in self.doc()["pages"]]
        self.step("结构稿中")                       # diy-review 的回修边
        self.step("待验收")                         # diy-dev 的重提
        self.step("已批准")                         # 用户批准（人裁）
        self.step("结构稿中")                       # 重开（破坏性边）
        self.step("待验收")
        self.step("已移除", reason="被 v2 首页取代")   # 验收期废弃
        self.step("结构稿中")                       # 恢复
        final = self.doc()
        self.assertEqual([p["id"] for p in final["pages"]], ids_before,
                         "链上发生了 ID 重编号（稳定 ID 契约被破）")
        self.assertEqual(final["pages"][0]["status"], "结构稿中")
        self.assertEqual(len(final["revisions"]), 2,
                         "破坏性边未各追加一条 revisions（重开 + 废弃）")
        rc, data = run_json(DESIGN_PY, ["validate", "--design", self.path,
                                        "--previous", self.path + ".prev", "--json"])
        self.assertEqual(rc, 0, "链尾的 ID 对账不自洽：%s" % json.dumps(data, ensure_ascii=False))


# ---------------------------------------------------------------- 面 5

class FinalGateTests(W7Harness):
    """断言面 5：终门联动——`validate` 过 + `open_questions` 零 `待办` → 才可写 `已定稿`。

    门的文案（定稿三道）归 W1，闸的实现归 W2。**与既有测试的分工**：W2 的顺序是
    「已定稿 + 待办 → 拦 / 草稿 → 放」两格；本类补成**真值表四格**（含「已定稿 + 零待办
    → 放行」这一格），并把「才可写」的前置（三命令全过）一起跑通。
    """

    def setUp(self):
        super().setUp()
        self.write("prototypes/SC-01.P1.html", GOOD_PROTOTYPE)
        self.write("src/impl.js", IMPL_JS)

    # trace: C·3a §6 面 5（定稿三道的文档面 + 引擎面：一道有闸、一道无闸的分工）
    def test_final_gate_conjunction_is_documented_and_engine_backed(self):
        gate = [ln for ln in read(DESIGN_SKILL_MD).splitlines() if "定稿走三道" in ln]
        self.assertEqual(len(gate), 1, "主文件未给出唯一的「定稿走三道」句")
        for term in ("`validate` exit 0", "`check` PASS", "`audit` 零 `one-off-*`",
                     "`[假设]` 清零", "零 `待办`", "才写 `status: 已定稿`"):
            self.assertIn(term, gate[0], "定稿三道的合取项缺失：%s" % term)
        engine_src = read(DESIGN_PY)
        self.assertIn("OPEN_QUESTION_PENDING", engine_src,
                      "「零 待办」这一道在引擎里没有闸")
        self.assertNotIn("[假设]", engine_src,
                         "「[假设] 清零」在引擎里无闸（会话纪律）——若新增该闸，"
                         "须同步改写主文件的定稿三道句与本断言")

    # trace: C·3a §6 面 5（真值表：状态 × 待办 四格；被拦格须点名是哪条问题）
    def test_final_gate_truth_table(self):
        verdict = {}
        for status, questions, key in (("草稿", "pending", "草稿/待办"),
                                       ("草稿", "resolved", "草稿/零待办"),
                                       ("已定稿", "pending", "已定稿/待办"),
                                       ("已定稿", "resolved", "已定稿/零待办")):
            path = self.write("gate-%s-%s/design.yaml" % (status, questions),
                              design_text(project_status=status, open_questions=questions))
            write_dir = os.path.dirname(path)
            os.makedirs(os.path.join(write_dir, "prototypes"), exist_ok=True)
            with io.open(os.path.join(write_dir, "prototypes", "SC-01.P1.html"),
                         "w", encoding="utf-8") as fh:
                fh.write(GOOD_PROTOTYPE)
            rc, data = self.validate(path)
            verdict[key] = rc
            if key == "已定稿/待办":
                # 只断言「被哪条问题拦住」（码名由 W2 的用例钉死，此处不重复）
                self.assertFalse(data["ok"], json.dumps(data, ensure_ascii=False))
                self.assertTrue(data["violations"][0]["where"].endswith("open_questions[0].status"),
                                "被拦格未点名是哪条问题：%s" % data["violations"][0])
                self.assertIn("Q-1", data["violations"][0]["msg"])
        self.assertEqual(verdict, {"草稿/待办": 0, "草稿/零待办": 0,
                                   "已定稿/待办": 1, "已定稿/零待办": 0},
                         "终门真值表变了：%s" % verdict)

    # trace: C·3a §6 面 5（「才可写」的前置：三命令全过 → 清零 → 才写 已定稿）
    def test_three_commands_pass_before_final_status_is_written(self):
        path = self.write("design.yaml", design_text(project_status="草稿",
                                                     open_questions="pending"))
        for args in (["validate", "--design", path],
                     ["check", "--design", path],
                     ["audit", "--design", path, "--src", os.path.join(self.out, "src")]):
            with self.subTest(command=args[0]):
                rc, data = run_json(DESIGN_PY, args + ["--json"])
                self.assertEqual(rc, 0, json.dumps(data, ensure_ascii=False))
        doc = self.doc()
        self.assertEqual(doc["project"]["status"], "草稿", "定稿前状态已提前写死")
        doc["open_questions"][0] = {"id": "Q-1", "question": "首页空态的文案由谁定稿？",
                                    "status": "已解决", "answer": "产品经理已定稿"}
        doc["project"]["status"] = "已定稿"
        self.write("design.yaml", doc)
        rc, data = self.validate(path)
        self.assertEqual(rc, 0, "清零待办后仍不可定稿：%s" % json.dumps(data, ensure_ascii=False))


if __name__ == "__main__":
    unittest.main()
