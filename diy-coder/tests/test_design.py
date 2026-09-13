# -*- coding: utf-8 -*-
"""diy-design 确定性引擎 e2e 测试（S-14）。

夹具策略：TC-14.1.1/14.3.1 用合成 design.yaml + 原型 HTML（引擎契约验证）；
TC-14.2.1 用无前端词迷你 PRD + 本项目真实 prd.yaml（TC steps 指定）。
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
DESIGN_PY = os.path.join(HERE, "..", "skills", "diy-design", "scripts", "design.py")
REAL_PRD = os.path.join(HERE, "..", "..", "diy-output", "prd.yaml")
NL = chr(10)

GOOD_DESIGN = NL.join([
    "project:",
    "  name: mini",
    "  status: final",
    "direction: 瑞士编辑风——大字阶对比、留白节奏、单强调色；禁默认卡片网格与居中英雄区",
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
    "- id: P-1",
    "  name: 待办列表",
    "  route: /todos",
    "  states:",
    "  - name: hover",
    "    signals: [icon, motion]",
    "  - name: empty",
    "    signals: [text]",
    "  - name: loading",
    "    signals: [icon, motion]",
    "  - name: error",
    "    signals: [icon, text]",
    "  prototype: prototypes/P-1.html",
])

GOOD_HTML = NL.join([
    "<!DOCTYPE html>",
    '<html lang="zh-CN">',
    "<head>",
    '<meta charset="utf-8">',
    "<style>",
    ":root {",
    "  --color-bg: #ffffff;",
    "  --color-surface: #f5f5f2;",
    "  --color-text: #1a1a1a;",
    "  --color-accent: #0a5c8c;",
    "  --spacing-unit: 4px;",
    "}",
    "body { background: var(--color-bg); color: var(--color-text); }",
    "button { background: var(--color-accent); }",
    "</style>",
    "</head>",
    "<body>",
    "<h1>待办列表</h1>",
    "<ul><li>示例事项</li></ul>",
    '<button type="button">新增</button>',
    "</body>",
    "</html>",
])


def run_engine(args):
    return subprocess.run(
        [sys.executable, DESIGN_PY] + args,
        capture_output=True, text=True, encoding="utf-8",
    )


class DesignEngineTests(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, rel, content):
        path = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def write_prd(self, fr_texts):
        body = ["project:", "  name: mini", "  status: final", "features:",
                "- id: FG-1", "  name: mini", "  requirements:"]
        for i, txt in enumerate(fr_texts, 1):
            body += ["  - id: F-%d" % i, "    statement: %s" % txt]
        return self.write("diy-output/prd.yaml", NL.join(body))

    # trace: S-14 AC-14.1 TC-14.1.1
    def test_frontend_design_fixture_validates(self):
        dpath = self.write("diy-output/design.yaml", GOOD_DESIGN)
        ppath = self.write("diy-output/prototypes/P-1.html", GOOD_HTML)
        v = run_engine(["validate", "--design", dpath, "--json"])
        self.assertEqual(v.returncode, 0, v.stderr)
        self.assertTrue(json.loads(v.stdout)["valid"])
        html = open(ppath, encoding="utf-8").read()
        self.assertIn("--color-text", html)
        self.assertIn("var(--color-", html)
        c = run_engine(["check", "--design", dpath, "--json"])
        self.assertEqual(c.returncode, 0, c.stderr + c.stdout)
        self.assertTrue(json.loads(c.stdout)["pass"])

    # trace: S-14 AC-14.2 TC-14.2.1
    def test_no_frontend_prd_skips(self):
        self.write_prd(["系统按周期导出 CSV 报表并归档至指定目录"])
        d = run_engine(["detect", "--project-root", self.root, "--json"])
        self.assertEqual(d.returncode, 0, d.stderr)
        data = json.loads(d.stdout)
        self.assertFalse(data["has_frontend"])
        self.assertTrue(data["skip_reason"])
        self.assertFalse(os.path.exists(os.path.join(self.root, "diy-output", "design.yaml")))
        # 本项目真实 prd.yaml（无前端展示 FR）同样 skip
        d2 = run_engine(["detect", "--project-root",
                         os.path.dirname(os.path.dirname(REAL_PRD)), "--json"])
        self.assertFalse(json.loads(d2.stdout)["has_frontend"], d2.stdout)
        # 正面对照：含页面展示需求 → 不 skip（TC-14.1.1 前置）
        self.write_prd(["页面以列表展示待办事项，支持勾选完成"])
        d3 = run_engine(["detect", "--project-root", self.root, "--json"])
        self.assertTrue(json.loads(d3.stdout)["has_frontend"], d3.stdout)

    # trace: S-14 AC-14.3 TC-14.3.1
    def test_a11y_check_catches_faults(self):
        bad = GOOD_DESIGN.replace("text: '#1a1a1a'", "text: '#808080'")
        bad = bad.replace("    signals: [icon, motion]" + NL + "  - name: empty",
                          "    signals: [color]" + NL + "  - name: empty")
        dpath = self.write("diy-output/design.yaml", bad)
        self.write("diy-output/prototypes/P-1.html", GOOD_HTML)
        c = run_engine(["check", "--design", dpath, "--json"])
        self.assertEqual(c.returncode, 1, c.stdout)
        data = json.loads(c.stdout)
        self.assertFalse(data["pass"])
        kinds = {v["kind"] for v in data["violations"]}
        self.assertIn("contrast", kinds)
        self.assertIn("color-only-signal", kinds)
        # semantic-html fail 路径：h1 缺失同被拦截（AC-14.3 第三项）
        no_h1 = GOOD_HTML.replace("<h1>待办列表</h1>", "<h2>待办列表</h2>")
        self.write("diy-output/prototypes/P-1.html", no_h1)
        c3 = run_engine(["check", "--design", dpath, "--json"])
        self.assertIn("semantic-html",
                      {v["kind"] for v in json.loads(c3.stdout)["violations"]})
        # 修正后 pass（design 与原型都恢复合规）
        self.write("diy-output/design.yaml", GOOD_DESIGN)
        self.write("diy-output/prototypes/P-1.html", GOOD_HTML)
        c2 = run_engine(["check", "--design", dpath, "--json"])
        self.assertEqual(c2.returncode, 0, c2.stdout)
        self.assertTrue(json.loads(c2.stdout)["pass"])

    # trace: S-14 AC-14.3 TC-14.3.2
    def test_three_digit_hex_parity_across_check_and_audit(self):
        design = GOOD_DESIGN.replace("bg: '#ffffff'", "bg: '#fff'")
        design = design.replace("text: '#1a1a1a'", "text: '#000'")
        dpath = self.write("diy-output/design.yaml", design)
        self.write("diy-output/prototypes/P-1.html", GOOD_HTML)
        c = run_engine(["check", "--design", dpath, "--json"])
        self.assertEqual(c.returncode, 0, c.stdout + c.stderr)
        data = json.loads(c.stdout)
        self.assertTrue(data["pass"], data["violations"])
        # audit 同口径：token 三位 #fff/#000 vs 源码六位 #ffffff/#000000 → 命中不判 one-off
        src = self.write("diy-output/src/app.css",
                         "body { background: #ffffff; color: #000000; }" + NL)
        a = run_engine(["audit", "--design", dpath, "--src", src, "--json"])
        self.assertEqual(a.returncode, 0, a.stdout + a.stderr)
        self.assertTrue(json.loads(a.stdout)["pass"])

    # trace: S-14 AC-14.2 TC-14.2.1
    def test_detect_plain_verbs_do_not_veto_real_ui_fr(self):
        # determinism-1 回归：普通动词（生成/渲染）出现在真实 UI 需求句中不得否决命中
        self.write_prd(["系统应生成订单详情页，展示商品列表与状态标签"])
        d = run_engine(["detect", "--project-root", self.root, "--json"])
        self.assertEqual(d.returncode, 0, d.stderr)
        data = json.loads(d.stdout)
        self.assertTrue(data["has_frontend"], d.stdout)
        self.assertEqual(data["hits"][0]["fr"], "F-1")
        self.write_prd(["页面渲染完成后弹出登录弹窗"])
        d2 = run_engine(["detect", "--project-root", self.root, "--json"])
        self.assertTrue(json.loads(d2.stdout)["has_frontend"], d2.stdout)
        # 机器锚词（技能名/技术术语，词边界判定）仍构成否决：工具链自身描述不触发设计
        self.write_prd(["diy-viewer 把 HTML 产物渲染成页面"])
        d3 = run_engine(["detect", "--project-root", self.root, "--json"])
        self.assertFalse(json.loads(d3.stdout)["has_frontend"], d3.stdout)

    # trace: S-15 AC-15.2 TC-15.2.1
    def test_audit_judges_hex_at_value_positions_only(self):
        # determinism-2 回归：var() fallback / 选择器 / 注释不是色值位，不得误报
        dpath = self.write("diy-output/design.yaml", GOOD_DESIGN)
        src = self.write("diy-output/src/app.css", NL.join([
            ".card {",
            "  color: var(--color-text, #111827);",
            "  background: var(--color-bg);",
            "}",
            "#fade { opacity: 0; }",
            "/* legacy: #ccc */",
            "",
        ]))
        a = run_engine(["audit", "--design", dpath, "--src", src, "--json"])
        self.assertEqual(a.returncode, 0, a.stdout + a.stderr)
        self.assertTrue(json.loads(a.stdout)["pass"])
        # 对照：真实色值位的非 token 色值必须仍被报（收紧不得变松）
        bad = self.write("diy-output/src/bad.css", "button { background: #111827; }" + NL)
        a2 = run_engine(["audit", "--design", dpath, "--src", bad, "--json"])
        self.assertEqual(a2.returncode, 1, a2.stdout + a2.stderr)
        oneoffs = [v for v in json.loads(a2.stdout)["violations"]
                   if v["kind"] == "one-off-color"]
        self.assertTrue(oneoffs and "#111827" in oneoffs[0]["detail"], a2.stdout)
        # 内联 style 是色值位：style 属性中的非 token 色值同样被抓
        inline = self.write("diy-output/src/card.html",
                            '<div style="color: #111827">x</div>' + NL)
        a3 = run_engine(["audit", "--design", dpath, "--src", inline, "--json"])
        self.assertEqual(a3.returncode, 1, a3.stdout + a3.stderr)
        self.assertTrue(any(v["kind"] == "one-off-color"
                            for v in json.loads(a3.stdout)["violations"]), a3.stdout)

    # trace: S-14 AC-14.3 TC-14.3.3
    def test_malformed_shapes_degrade_without_traceback(self):
        # 夹具一：token 色值为整数 123（形状未知）
        bad = GOOD_DESIGN.replace("bg: '#ffffff'", "bg: 123")
        dpath = self.write("diy-output/design.yaml", bad)
        self.write("diy-output/prototypes/P-1.html", GOOD_HTML)
        c = run_engine(["check", "--design", dpath, "--json"])
        self.assertNotIn("Traceback", c.stderr)
        self.assertEqual(c.returncode, 1, c.stdout + c.stderr)
        self.assertFalse(json.loads(c.stdout)["pass"])
        # 夹具二：pages.states 混入裸字符串（半写条目）
        bad2 = GOOD_DESIGN.replace(
            "- name: hover" + NL + "    signals: [icon, motion]",
            "- 半写字符串" + NL + "  - name: hover" + NL + "    signals: [icon, motion]")
        self.write("diy-output/design.yaml", bad2)
        c2 = run_engine(["check", "--design", dpath, "--json"])
        self.assertNotIn("Traceback", c2.stderr)
        self.assertEqual(c2.returncode, 1, c2.stdout + c2.stderr)
        self.assertFalse(json.loads(c2.stdout)["pass"])


if __name__ == "__main__":
    unittest.main()
