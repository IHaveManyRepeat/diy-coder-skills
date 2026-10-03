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
    "  status: 已定稿",
    "direction: 瑞士编辑风——大字阶对比、留白节奏、单强调色；禁默认卡片网格与居中英雄区",
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
    "- id: P-1",
    "  name: 待办列表",
    "  route: /todos",
    "  states:",
    "  - name: 悬停",
    "    signals: [图标, 动效]",
    "  - name: 空态",
    "    signals: [文字]",
    "  - name: 加载中",
    "    signals: [图标, 动效]",
    "  - name: 错误",
    "    signals: [图标, 文字]",
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
        body = ["project:", "  name: mini", "  status: 已定稿", "features:",
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
        self.assertTrue(json.loads(v.stdout)["ok"])
        html = open(ppath, encoding="utf-8").read()
        self.assertIn("--color-text", html)
        self.assertIn("var(--color-", html)
        c = run_engine(["check", "--design", dpath, "--json"])
        self.assertEqual(c.returncode, 0, c.stderr + c.stdout)
        self.assertTrue(json.loads(c.stdout)["ok"])

    # trace: C·3a §2.4（回执归一：单行 {ok,command,violations[],warnings,counts,file}；
    #                    命令专有键一个不少）
    def test_receipt_family_shape_across_all_four_commands(self):
        dpath = self.write("diy-output/design.yaml", GOOD_DESIGN)
        self.write("diy-output/prototypes/P-1.html", GOOD_HTML)
        self.write_prd(["页面以列表展示待办事项，支持勾选完成"])
        src = self.write("diy-output/src/app.css", "body { color: var(--color-text); }" + NL)
        runs = {
            "detect": ["detect", "--project-root", self.root],
            "validate": ["validate", "--design", dpath],
            "check": ["check", "--design", dpath],
            "audit": ["audit", "--design", dpath, "--src", src],
        }
        common = {"ok", "command", "violations", "warnings", "counts", "file"}
        for cmd, args in runs.items():
            with self.subTest(command=cmd):
                proc = run_engine(list(args) + ["--json"])
                self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
                self.assertEqual(len(proc.stdout.strip().splitlines()), 1,
                                 "%s 回执必须是单行 JSON" % cmd)
                data = json.loads(proc.stdout)
                self.assertEqual(data["command"], cmd)
                self.assertTrue(common <= set(data), "%s 缺公共键" % cmd)
                self.assertIsInstance(data["ok"], bool)
                self.assertIsInstance(data["violations"], list)
                self.assertIsInstance(data["warnings"], list)
                self.assertIsInstance(data["counts"], dict)
                self.assertTrue(data["file"])
        # 命令专有键保留（SKILL.md:31-33 / :84 的消费面）
        detect = json.loads(run_engine(runs["detect"] + ["--json"]).stdout)
        self.assertTrue(detect["has_frontend"])
        self.assertIsNone(detect["skip_reason"])
        self.assertEqual(detect["hits"][0]["fr"], "F-1")
        check = json.loads(run_engine(runs["check"] + ["--json"]).stdout)
        self.assertEqual([list(p) for p in check["checked"]["contrast_pairs"]],
                         [["text", "bg"], ["text", "surface"], ["text_muted", "bg"],
                          ["text_muted", "surface"], ["accent_text", "accent"]])
        audit = json.loads(run_engine(runs["audit"] + ["--json"]).stdout)
        self.assertEqual(audit["audited"], 1)

    # trace: C·3a §2.4（退出码 0 成功 / 1 拒绝 / 2 用法错误）
    def test_exit_codes_and_rejection_receipts(self):
        dpath = self.write("diy-output/design.yaml", GOOD_DESIGN)
        self.write("diy-output/prototypes/P-1.html", GOOD_HTML)
        # 1 拒绝：缺 --design 的文件
        proc = run_engine(["validate", "--design", dpath + ".nope", "--json"])
        self.assertEqual(proc.returncode, 1, proc.stdout)
        data = json.loads(proc.stdout)
        self.assertFalse(data["ok"])
        self.assertEqual(data["violations"][0]["code"], "MISSING_FILE")
        self.assertNotIn("Traceback", proc.stderr)
        # 1 拒绝：detect 的 prd.yaml 缺席
        d = run_engine(["detect", "--project-root", os.path.join(self.root, "no-such"),
                        "--json"])
        self.assertEqual(d.returncode, 1, d.stdout)
        self.assertEqual(json.loads(d.stdout)["violations"][0]["code"], "MISSING_FILE")
        # 2 用法错误：缺必填旗标
        u = run_engine(["validate", "--json"])
        self.assertEqual(u.returncode, 2, u.stdout + u.stderr)

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
        bad = bad.replace("    signals: [图标, 动效]" + NL + "  - name: 空态",
                          "    signals: [色彩]" + NL + "  - name: 空态")
        dpath = self.write("diy-output/design.yaml", bad)
        self.write("diy-output/prototypes/P-1.html", GOOD_HTML)
        c = run_engine(["check", "--design", dpath, "--json"])
        self.assertEqual(c.returncode, 1, c.stdout)
        data = json.loads(c.stdout)
        self.assertFalse(data["ok"])
        kinds = {v["code"] for v in data["violations"]}
        self.assertIn("contrast", kinds)
        self.assertIn("color-only-signal", kinds)
        # semantic-html fail 路径：h1 缺失同被拦截（AC-14.3 第三项）
        no_h1 = GOOD_HTML.replace("<h1>待办列表</h1>", "<h2>待办列表</h2>")
        self.write("diy-output/prototypes/P-1.html", no_h1)
        c3 = run_engine(["check", "--design", dpath, "--json"])
        self.assertIn("semantic-html",
                      {v["code"] for v in json.loads(c3.stdout)["violations"]})
        # 修正后 pass（design 与原型都恢复合规）
        self.write("diy-output/design.yaml", GOOD_DESIGN)
        self.write("diy-output/prototypes/P-1.html", GOOD_HTML)
        c2 = run_engine(["check", "--design", dpath, "--json"])
        self.assertEqual(c2.returncode, 0, c2.stdout)
        self.assertTrue(json.loads(c2.stdout)["ok"])

    # trace: C·3a §4.6（check 维度集扩充：无障碍 a11y-* + 设计系统 ds-token-*，
    #                    既有 contrast / color-only-signal / semantic-html 不删改）
    def test_check_extra_dimensions_hit_and_keep_legacy_codes(self):
        bad_html = GOOD_HTML.replace(
            "button { background: var(--color-accent); }",
            "button { height: 32px; padding: 12px; font-size: 13px;"
            " background: #123456; }").replace(
            '<button type="button">新增</button>',
            '<button type="button" tabindex="-1">新增</button>'
            '<div onclick="go()">跳过</div>')
        dpath = self.write("diy-output/design.yaml", GOOD_DESIGN)
        self.write("diy-output/prototypes/P-1.html", bad_html)
        c = run_engine(["check", "--design", dpath, "--json"])
        self.assertEqual(c.returncode, 1, c.stdout)
        data = json.loads(c.stdout)
        codes = [x["code"] for x in data["violations"]]
        for code in ("a11y-touch-target", "a11y-keyboard", "ds-token-color",
                     "ds-token-font-size", "ds-token-spacing"):
            self.assertIn(code, codes, "新维度未判：%s" % code)
        # 既有判据的 code 名一字不改（保真面：contrast / color-only-signal / semantic-html）
        legacy = GOOD_DESIGN.replace("text: '#1a1a1a'", "text: '#808080'")
        self.write("diy-output/design.yaml", legacy)
        self.write("diy-output/prototypes/P-1.html",
                   GOOD_HTML.replace("<h1>待办列表</h1>", ""))
        c2 = run_engine(["check", "--design", dpath, "--json"])
        legacy_codes = {x["code"] for x in json.loads(c2.stdout)["violations"]}
        self.assertIn("contrast", legacy_codes)
        self.assertIn("semantic-html", legacy_codes)
        self.assertEqual(json.loads(c2.stdout)["checked"]["contrast_pairs"],
                         [list(p) for p in (("text", "bg"), ("text", "surface"),
                                            ("text_muted", "bg"), ("text_muted", "surface"),
                                            ("accent_text", "accent"))])

    # trace: C·13 §2 W1（form_factor↔触控下限联动分档：桌面 24；移动端/响应式 Web/多端/
    #                    缺键/表外值 44；边界口径 = 现行 < 判据下恰值通过）
    def test_touch_target_min_by_form_factor(self):
        def touch_violations(design_text, html):
            dpath = self.write("diy-output/design.yaml", design_text)
            self.write("diy-output/prototypes/P-1.html", html)
            data = json.loads(run_engine(
                ["check", "--design", dpath, "--json"]).stdout)
            return (data,
                    [x for x in data["violations"] if x["code"] == "a11y-touch-target"])

        def html_button(height):
            return GOOD_HTML.replace(
                "button { background: var(--color-accent); }",
                "button { background: var(--color-accent); height: %dpx; }" % height)

        # 边界六枚（恰值通过 / −1 违规 / +1 通过）：移动端 44 档、桌面 24 档
        for form_factor, edge in (("移动端", 44), ("桌面", 24)):
            design = GOOD_DESIGN.replace("form_factor: 响应式 Web",
                                         "form_factor: " + form_factor)
            for height, should_violate in ((edge, False), (edge - 1, True),
                                           (edge + 1, False)):
                data, touches = touch_violations(design, html_button(height))
                self.assertEqual(bool(touches), should_violate,
                                 "%s %dpx 触控判定不符：%s" % (form_factor, height,
                                                              data["violations"]))
                self.assertEqual(data["checked"]["a11y_extras"][0],
                                 "触控目标 ≥%dpx" % edge)
                if should_violate:
                    self.assertIn("< %dpx——触控目标最小 %d×%dpx"
                                  % (edge, edge, edge), touches[0]["msg"])
                else:
                    self.assertTrue(data["ok"], data["violations"])
        # 桌面档变宽行为锚：43px 于 44 档违规、于 24 档通过（红转绿方向仅此通道）
        _, desktop_touches = touch_violations(
            GOOD_DESIGN.replace("form_factor: 响应式 Web", "form_factor: 桌面"),
            html_button(43))
        self.assertEqual(desktop_touches, [])
        # 内联 style 通道同分档：桌面 23px 违规且渲染值随档（24）
        inline = GOOD_HTML.replace(
            '<button type="button">新增</button>',
            '<button type="button" style="height: 23px">新增</button>')
        data, touches = touch_violations(
            GOOD_DESIGN.replace("form_factor: 响应式 Web", "form_factor: 桌面"),
            inline)
        self.assertEqual(len(touches), 1)
        self.assertIn("23px < 24px", touches[0]["msg"])
        # 响应式 Web/多端 = 44 最严端（呈核 3 改判）；缺键/表外值 = 44 缺省档（呈核 8）
        missing_key = GOOD_DESIGN.replace("form_factor: 响应式 Web" + NL, "")
        for design in (GOOD_DESIGN,
                       GOOD_DESIGN.replace("form_factor: 响应式 Web",
                                           "form_factor: 多端"),
                       missing_key,
                       GOOD_DESIGN.replace("form_factor: 响应式 Web",
                                           "form_factor: 平板")):
            data, touches = touch_violations(design, html_button(43))
            self.assertEqual(len(touches), 1,
                             "43px 须按 44 档违规：%s" % data["violations"])
            self.assertIn("< 44px", touches[0]["msg"])
            self.assertEqual(data["checked"]["a11y_extras"][0], "触控目标 ≥44px")
        # 缺省档恰 44 通过（44 档双向闭环）
        data, touches = touch_violations(missing_key, html_button(44))
        self.assertEqual(touches, [])
        self.assertTrue(data["ok"], data["violations"])

    # trace: C·13 §2 W1（floor 余项两新码 a11y-reduced-motion / a11y-focus-order；
    #                    承上例先例形态——新码必判 + 修正路径转绿）
    def test_check_reduced_motion_and_focus_order_codes(self):
        bad_html = GOOD_HTML.replace(
            "button { background: var(--color-accent); }",
            "button { background: var(--color-accent);"
            " transition: background .2s ease; }").replace(
            '<button type="button">新增</button>',
            '<button type="button" tabindex="2">新增</button>')
        dpath = self.write("diy-output/design.yaml", GOOD_DESIGN)
        self.write("diy-output/prototypes/P-1.html", bad_html)
        c = run_engine(["check", "--design", dpath, "--json"])
        self.assertEqual(c.returncode, 1, c.stdout)
        violations = json.loads(c.stdout)["violations"]
        codes = [x["code"] for x in violations]
        for code in ("a11y-reduced-motion", "a11y-focus-order"):
            self.assertIn(code, codes, "新码未判：%s" % code)
        self.assertIn("prefers-reduced-motion",
                      [x for x in violations
                       if x["code"] == "a11y-reduced-motion"][0]["msg"])
        self.assertIn("阅读顺序",
                      [x for x in violations
                       if x["code"] == "a11y-focus-order"][0]["msg"])
        # 修正路径（判据可满足）：补 prefers-reduced-motion 降级块 + tabindex 归 0 → 全绿
        fixed = bad_html.replace(
            "</style>",
            "@media (prefers-reduced-motion: reduce)"
            " { button { transition: none; } }</style>").replace(
            'tabindex="2"', 'tabindex="0"')
        self.write("diy-output/prototypes/P-1.html", fixed)
        c2 = run_engine(["check", "--design", dpath, "--json"])
        data = json.loads(c2.stdout)
        self.assertEqual(c2.returncode, 0, c2.stdout)
        self.assertTrue(data["ok"])
        self.assertEqual(data["violations"], [])

    # trace: S-14 AC-14.3 TC-14.3.2
    def test_three_digit_hex_parity_across_check_and_audit(self):
        # token 侧写成三位 #000、源码侧写成六位 #000000（反向：bg 写六位、原型写三位）。
        # 两侧字面形都只在本对里出现——任一侧退化成逐字比较，check 立刻命中 ds-token-color。
        design = GOOD_DESIGN.replace("text: '#1a1a1a'", "text: '#000'")
        dpath = self.write("diy-output/design.yaml", design)
        self.write("diy-output/prototypes/P-1.html",
                   GOOD_HTML.replace("--color-bg: #ffffff;", "--color-bg: #fff;")
                            .replace("--color-text: #1a1a1a;", "--color-text: #000000;"))
        c = run_engine(["check", "--design", dpath, "--json"])
        self.assertEqual(c.returncode, 0, c.stdout + c.stderr)
        data = json.loads(c.stdout)
        self.assertTrue(data["ok"], data["violations"])
        # audit 同口径：token 三位 #000 vs 源码六位 #000000 → 归一后命中，不判 one-off
        src = self.write("diy-output/src/app.css",
                         "body { background: #ffffff; color: #000000; }" + NL)
        a = run_engine(["audit", "--design", dpath, "--src", src, "--json"])
        self.assertEqual(a.returncode, 0, a.stdout + a.stderr)
        self.assertTrue(json.loads(a.stdout)["ok"])

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
        self.assertTrue(json.loads(a.stdout)["ok"])
        # 对照：真实色值位的非 token 色值必须仍被报（收紧不得变松）
        bad = self.write("diy-output/src/bad.css", "button { background: #111827; }" + NL)
        a2 = run_engine(["audit", "--design", dpath, "--src", bad, "--json"])
        self.assertEqual(a2.returncode, 1, a2.stdout + a2.stderr)
        oneoffs = [v for v in json.loads(a2.stdout)["violations"]
                   if v["code"] == "one-off-color"]
        self.assertTrue(oneoffs and "#111827" in oneoffs[0]["msg"], a2.stdout)
        # 内联 style 是色值位：style 属性中的非 token 色值同样被抓
        inline = self.write("diy-output/src/card.html",
                            '<div style="color: #111827">x</div>' + NL)
        a3 = run_engine(["audit", "--design", dpath, "--src", inline, "--json"])
        self.assertEqual(a3.returncode, 1, a3.stdout + a3.stderr)
        self.assertTrue(any(v["code"] == "one-off-color"
                            for v in json.loads(a3.stdout)["violations"]), a3.stdout)

    # trace: C·3a §4.4（token_scope：audit 的 os.walk 跳过这些路径，--src 语义不变；
    #                    相对项按 --src 解析）
    def test_audit_skips_token_scope_paths(self):
        design = GOOD_DESIGN + NL + NL.join([
            "token_scope:",
            "- vendor",
        ]) + NL
        dpath = self.write("diy-output/design.yaml", design)
        self.write("diy-output/src/vendor/lib.css", "body { color: #123456; }" + NL)
        self.write("diy-output/src/app.css", "body { color: #123456; }" + NL)
        a = run_engine(["audit", "--design", dpath, "--src",
                        os.path.join(self.root, "diy-output", "src"), "--json"])
        self.assertEqual(a.returncode, 1, a.stdout + a.stderr)
        data = json.loads(a.stdout)
        self.assertEqual([x["where"] for x in data["violations"]], ["src/app.css"],
                         "vendor 未跳过或误报面漂移")
        self.assertEqual(data["counts"]["skipped_dirs"], 1)
        self.assertTrue(any("token_scope" in w for w in data["warnings"]), data)
        # 无 token_scope 时同一棵树两个文件都判（跳过是增量，不改 --src 整体语义）
        plain = self.write("diy-output/design_plain.yaml", GOOD_DESIGN)
        a2 = run_engine(["audit", "--design", plain, "--src",
                         os.path.join(self.root, "diy-output", "src"), "--json"])
        self.assertEqual(len(json.loads(a2.stdout)["violations"]), 2, a2.stdout)

    # trace: C·3a §4.5（open_questions 结构校验 + 终门零 待办）
    def test_validate_open_questions_and_final_gate(self):
        base = GOOD_DESIGN + NL + NL.join([
            "open_questions:",
            "- id: Q-1",
            "  question: 首页要不要放 FAQ？",
            "  status: 待办",
            "- id: Q-2",
            "  question: 空态文案谁来定？",
            "  status: 已解决",
            "  answer: 产品经理已定稿",
        ]) + NL
        dpath = self.write("diy-output/design.yaml", base)
        self.write("diy-output/prototypes/P-1.html", GOOD_HTML)
        # 已定稿 + 零 待办：Q-2 合规、Q-1 待办 → 终门拦截
        v = run_engine(["validate", "--design", dpath, "--json"])
        self.assertEqual(v.returncode, 1, v.stdout)
        codes = [x["code"] for x in json.loads(v.stdout)["violations"]]
        self.assertEqual(codes, ["OPEN_QUESTION_PENDING"], v.stdout)
        # 草稿态：同一份不拦（终门只管 已定稿）
        self.write("diy-output/design.yaml", base.replace("status: 已定稿", "status: 草稿"))
        v2 = run_engine(["validate", "--design", dpath, "--json"])
        self.assertEqual(v2.returncode, 0, v2.stdout)
        self.assertTrue(json.loads(v2.stdout)["ok"])
        # 结构违规：重复 id / 已解决缺 answer / status 枚举外
        broken = base.replace("id: Q-2", "id: Q-1").replace(
            "  status: 已解决" + NL + "  answer: 产品经理已定稿", "  status: 已解决").replace(
            "status: 草稿", "status: 草稿")
        broken = broken.replace("  status: 待办", "  status: 悬而未决")
        self.write("diy-output/design.yaml", broken)
        v3 = run_engine(["validate", "--design", dpath, "--json"])
        codes3 = [x["code"] for x in json.loads(v3.stdout)["violations"]]
        self.assertIn("DUPLICATE_ID", codes3)
        self.assertIn("EMPTY_FIELD", codes3)
        self.assertIn("ENUM_INVALID", codes3)

    # trace: C·3a §2.3（pages[].status 枚举与 removed_reason 从属字段）
    def test_validate_page_status_enum_and_removed_reason(self):
        dpath = self.write("diy-output/design.yaml",
                           GOOD_DESIGN.replace("  route: /todos",
                                               "  route: /todos" + NL + "  status: 已移除"))
        self.write("diy-output/prototypes/P-1.html", GOOD_HTML)
        v = run_engine(["validate", "--design", dpath, "--json"])
        self.assertEqual([x["code"] for x in json.loads(v.stdout)["violations"]],
                         ["EMPTY_FIELD"], v.stdout)
        self.assertIn("removed_reason", json.loads(v.stdout)["violations"][0]["where"])
        self.write("diy-output/design.yaml",
                   GOOD_DESIGN.replace("  route: /todos",
                                       "  route: /todos" + NL + "  status: 草稿"))
        v2 = run_engine(["validate", "--design", dpath, "--json"])
        self.assertEqual([x["code"] for x in json.loads(v2.stdout)["violations"]],
                         ["ENUM_INVALID"], v2.stdout)

    # trace: C·3a §2.3（states[].name 契约：有交互状态缺 name → EMPTY_FIELD，where 须定位到 states 序号）
    def test_validate_flags_state_missing_name_with_index(self):
        self.write("diy-output/prototypes/P-1.html", GOOD_HTML)
        design = GOOD_DESIGN.replace("  - name: 加载中",
                                     "  - signals: [图标, 动效]" + NL + "  - name: 加载中")
        dpath = self.write("diy-output/design.yaml", design)
        v = run_engine(["validate", "--design", dpath, "--json"])
        self.assertEqual(v.returncode, 1, v.stdout)
        data = json.loads(v.stdout)
        self.assertEqual([x["code"] for x in data["violations"]], ["EMPTY_FIELD"], v.stdout)
        self.assertEqual(data["violations"][0]["where"], "design.yaml pages[P-1].states[2]",
                         "缺 name 的定位未带 states 序号")
        self.assertIn("缺 name", data["violations"][0]["msg"])

    # trace: C·3a §2.2（保真面：四态缺一的既有报错文本逐字不变——不得再挂后缀或改写）
    def test_missing_state_message_kept_verbatim(self):
        self.write("diy-output/prototypes/P-1.html", GOOD_HTML)
        design = GOOD_DESIGN.replace("  - name: 加载中" + NL + "    signals: [图标, 动效]" + NL, "")
        dpath = self.write("diy-output/design.yaml", design)
        v = run_engine(["validate", "--design", dpath, "--json"])
        self.assertEqual(v.returncode, 1, v.stdout)
        self.assertIn("P-1 缺交互状态 加载中",
                      [x["msg"] for x in json.loads(v.stdout)["violations"]],
                      "四态缺一的既有报错文本被改写（须与改前引擎逐字一致）")

    # trace: C·3a §2.4（UNPARSABLE_YAML 单码两语义：YAML 语法坏 vs 半写形状，msg 须可区分）
    def test_unparsable_yaml_msg_distinguishes_syntax_from_shape(self):
        dpath = self.write("diy-output/design.yaml", "pages: [1," + NL)
        self.write("diy-output/prototypes/P-1.html", GOOD_HTML)
        syn = json.loads(run_engine(["check", "--design", dpath, "--json"]).stdout)
        self.assertEqual(syn["violations"][0]["code"], "UNPARSABLE_YAML")
        self.assertIn("解析失败", syn["violations"][0]["msg"])
        shape = GOOD_DESIGN.replace(
            "- name: 悬停" + NL + "    signals: [图标, 动效]",
            "- 半写字符串" + NL + "  - name: 悬停" + NL + "    signals: [图标, 动效]")
        self.write("diy-output/design.yaml", shape)
        sh = json.loads(run_engine(["check", "--design", dpath, "--json"]).stdout)
        self.assertEqual(sh["violations"][0]["code"], "UNPARSABLE_YAML")
        self.assertIn("不是映射", sh["violations"][0]["msg"])
        self.assertNotEqual(syn["violations"][0]["msg"], sh["violations"][0]["msg"],
                            "同码两语义必须在 msg 上可辨（语法错 vs 形状问题）")

    # trace: C·3a §2.3（pages[].id 契约：非空字符串；缺失 → EMPTY_FIELD，非字符串 → UNPARSABLE_YAML）
    def test_validate_pages_id_must_be_nonempty_string(self):
        self.write("diy-output/prototypes/P-1.html", GOOD_HTML)
        no_id = GOOD_DESIGN.replace("- id: P-1" + NL + "  name: 待办列表", "- name: 待办列表")
        dpath = self.write("diy-output/design.yaml", no_id)
        v = run_engine(["validate", "--design", dpath, "--json"])
        self.assertEqual(v.returncode, 1, v.stdout)
        data = json.loads(v.stdout)
        self.assertEqual([x["code"] for x in data["violations"]], ["EMPTY_FIELD"], v.stdout)
        self.assertEqual(data["violations"][0]["where"], "design.yaml pages[0].id")
        # 非字符串 ID（不可哈希的列表）：形状异常码，不得落到 INTERNAL_ERROR
        bad_id = GOOD_DESIGN.replace("- id: P-1", "- id: [P-1]")
        self.write("diy-output/design.yaml", bad_id)
        v2 = run_engine(["validate", "--design", dpath, "--json"])
        self.assertNotIn("Traceback", v2.stderr)
        self.assertEqual([x["code"] for x in json.loads(v2.stdout)["violations"]],
                         ["UNPARSABLE_YAML"], v2.stdout)

    # trace: C·3a §4.4（token_scope 单文件 --src：解析基 = src 所在目录，命中仍按前缀包含）
    def test_audit_token_scope_with_single_file_src(self):
        app = self.write("diy-output/src/app.css", "body { color: #123456; }" + NL)
        vend = self.write("diy-output/src/vendor/lib.css", "body { color: #123456; }" + NL)
        # 情形一：相对项解析后恰好指向该文件 → 跳过（旧实现拼成 <文件>/<相对项>，永不命中）
        dpath = self.write("diy-output/design.yaml",
                           GOOD_DESIGN + NL + NL.join(["token_scope:", "- app.css"]) + NL)
        a = run_engine(["audit", "--design", dpath, "--src", app, "--json"])
        self.assertEqual(a.returncode, 0, a.stdout + a.stderr)
        data = json.loads(a.stdout)
        self.assertEqual(data["violations"], [])
        self.assertEqual((data["counts"]["files"], data["counts"]["skipped"]), (0, 1))
        self.assertTrue(any("token_scope" in w for w in data["warnings"]), data)
        # 情形二：相对项指祖先子树（V2 的 [vendor]+vendor/lib.css 例）在单文件 src 下
        # 不命中——解析基是 src 所在目录，命中仍按前缀包含；单文件要跳过就写绝对项（情形三）
        # 或把 --src 给成目录（文档口径）。方向是「少跳不误跳」：宁可多判不静默漏判。
        dpath2 = self.write("diy-output/design.yaml",
                            GOOD_DESIGN + NL + NL.join(["token_scope:", "- vendor"]) + NL)
        a2 = run_engine(["audit", "--design", dpath2, "--src", vend, "--json"])
        self.assertEqual(a2.returncode, 1, a2.stdout)
        self.assertEqual([x["code"] for x in json.loads(a2.stdout)["violations"]],
                         ["one-off-color"])
        # 情形三：绝对项豁免出口仍可用（绝对项原样解析）
        dpath3 = self.write("diy-output/design.yaml",
                            GOOD_DESIGN + NL + NL.join(["token_scope:", "- " + vend]) + NL)
        a3 = run_engine(["audit", "--design", dpath3, "--src", vend, "--json"])
        self.assertEqual(a3.returncode, 0, a3.stdout + a3.stderr)
        self.assertEqual(json.loads(a3.stdout)["counts"]["skipped"], 1)

    # trace: S-14 AC-14.3 TC-14.3.3
    def test_malformed_shapes_degrade_without_traceback(self):
        # 夹具一：token 色值为整数 123（形状未知）
        bad = GOOD_DESIGN.replace("bg: '#ffffff'", "bg: 123")
        dpath = self.write("diy-output/design.yaml", bad)
        self.write("diy-output/prototypes/P-1.html", GOOD_HTML)
        c = run_engine(["check", "--design", dpath, "--json"])
        self.assertNotIn("Traceback", c.stderr)
        self.assertEqual(c.returncode, 1, c.stdout + c.stderr)
        self.assertFalse(json.loads(c.stdout)["ok"])
        # 夹具二：pages.states 混入裸字符串（半写条目）
        bad2 = GOOD_DESIGN.replace(
            "- name: 悬停" + NL + "    signals: [图标, 动效]",
            "- 半写字符串" + NL + "  - name: 悬停" + NL + "    signals: [图标, 动效]")
        self.write("diy-output/design.yaml", bad2)
        c2 = run_engine(["check", "--design", dpath, "--json"])
        self.assertNotIn("Traceback", c2.stderr)
        self.assertEqual(c2.returncode, 1, c2.stdout + c2.stderr)
        self.assertFalse(json.loads(c2.stdout)["ok"])
        self.assertIn("UNPARSABLE_YAML",
                      [x["code"] for x in json.loads(c2.stdout)["violations"]],
                      "形状问题须以 UNPARSABLE_YAML 上报")


    # ------------------------------------------------------- C·12 裁定 C12-1（W1 新增）

    # trace: C·12 §0 裁定 C12-1 / §7 裁定 2（五专项码首例：顶层键错误与条目字段错误不同层级）
    def test_top_level_two_keys_missing_invalid_and_legacy_ok(self):
        import re
        self.write("diy-output/prototypes/P-1.html", GOOD_HTML)
        stripped = re.sub(r"^form_factor: .*" + NL, "", GOOD_DESIGN, flags=re.MULTILINE)
        stripped = re.sub(r"^modes: .*" + NL, "", stripped, flags=re.MULTILINE)
        dpath = self.write("diy-output/design.yaml", stripped)
        v = run_engine(["validate", "--design", dpath, "--json"])
        codes = [x["code"] for x in json.loads(v.stdout)["violations"]]
        self.assertEqual(codes, ["FORM_FACTOR_MISSING", "MODES_MISSING"], v.stdout)
        # 表外值 → *_INVALID；msg 值域逐字按裁定 C12-1 §0 表
        bad = stripped.replace("frontend_framework: html", NL.join([
            "frontend_framework: html", "form_factor: 平板", "modes: 夜间"]))
        self.write("diy-output/design.yaml", bad)
        v2 = run_engine(["validate", "--design", dpath, "--json"])
        data2 = json.loads(v2.stdout)
        self.assertEqual([x["code"] for x in data2["violations"]],
                         ["FORM_FACTOR_INVALID", "MODES_INVALID"], v2.stdout)
        msgs = " ".join(x["msg"] for x in data2["violations"])
        self.assertIn("响应式 Web/移动端/桌面/多端", msgs, "form_factor 值域未按 §0 表逐字")
        self.assertIn("亮/暗/双模", msgs, "modes 值域未按 §0 表逐字")
        # 合法旧稿（补两键后）rc=0（§4 验收 #1）
        fixed = stripped.replace("frontend_framework: html", NL.join([
            "frontend_framework: html", "form_factor: 响应式 Web", "modes: 亮"]))
        self.write("diy-output/design.yaml", fixed)
        v3 = run_engine(["validate", "--design", dpath, "--json"])
        self.assertEqual(v3.returncode, 0, v3.stdout)
        self.assertTrue(json.loads(v3.stdout)["ok"])

    # ------------------------------------------------------- C·7 W4（meta 可选键）

    # trace: C·7 任务书 §2 W4 交付 1/4（meta 三态：缺失/合法 rc=0；空串与非字符串 →
    #        EMPTY_FIELD 且 msg 区分两态；SS-030-06：不用 UNPARSABLE_YAML——那是解析层）
    def test_pages_meta_optional_three_states(self):
        self.write("diy-output/prototypes/P-1.html", GOOD_HTML)
        # 态一：缺失（GOOD_DESIGN 无 meta）→ rc=0
        dpath = self.write("diy-output/design.yaml", GOOD_DESIGN)
        v0 = run_engine(["validate", "--design", dpath, "--json"])
        self.assertEqual(v0.returncode, 0, v0.stdout)
        # 态二：三子键合法 → rc=0；部分子键在场（description 缺席）同样 rc=0（各自可选）
        for extra in ("    title: 待办列表\n    description: 一句价值主张\n    og_image: assets/og-todos.png",
                      "    title: 待办列表"):
            legal = GOOD_DESIGN.replace(
                "  prototype: prototypes/P-1.html",
                "  prototype: prototypes/P-1.html\n  meta:\n" + extra)
            self.write("diy-output/design.yaml", legal)
            v1 = run_engine(["validate", "--design", dpath, "--json"])
            self.assertEqual(v1.returncode, 0, v1.stdout)
            self.assertTrue(json.loads(v1.stdout)["ok"], v1.stdout)
        # 态三：空串与非字符串 → EMPTY_FIELD 两枚、msg 区分两态
        bad = GOOD_DESIGN.replace(
            "  prototype: prototypes/P-1.html",
            "  prototype: prototypes/P-1.html\n  meta:\n    title: ''\n    og_image: 42")
        self.write("diy-output/design.yaml", bad)
        v2 = run_engine(["validate", "--design", dpath, "--json"])
        vios = [x for x in json.loads(v2.stdout)["violations"] if ".meta." in x["where"]]
        self.assertEqual([x["code"] for x in vios], ["EMPTY_FIELD", "EMPTY_FIELD"], v2.stdout)
        msgs = " | ".join(x["msg"] for x in vios)
        self.assertIn("为空", msgs, "空串态 msg 未区分：%s" % msgs)
        self.assertIn("不是字符串", msgs, "非字符串态 msg 未区分：%s" % msgs)
        # meta 整体非映射 → EMPTY_FIELD（非 UNPARSABLE_YAML）
        worse = GOOD_DESIGN.replace(
            "  prototype: prototypes/P-1.html",
            "  prototype: prototypes/P-1.html\n  meta: 首页标题")
        self.write("diy-output/design.yaml", worse)
        v3 = run_engine(["validate", "--design", dpath, "--json"])
        vios3 = [x for x in json.loads(v3.stdout)["violations"] if x["where"].endswith(".meta")]
        self.assertEqual([x["code"] for x in vios3], ["EMPTY_FIELD"], v3.stdout)
        self.assertIn("不是映射", vios3[0]["msg"], v3.stdout)
        # check 对带合法 meta 的夹具零扰动（验收 #8：新增键不扰动既有面）
        legal_full = GOOD_DESIGN.replace(
            "  prototype: prototypes/P-1.html",
            "  prototype: prototypes/P-1.html\n  meta:\n    title: 待办列表")
        self.write("diy-output/design.yaml", legal_full)
        c1 = run_engine(["check", "--design", dpath, "--json"])
        self.assertEqual(c1.returncode, 0, c1.stdout)

    # trace: C·12 §7-5① / §4 验收 #12（dark 子块形状：仅双模合法且必填，六角色全合法 hex）
    def test_dual_mode_dark_pair_shape(self):
        import re
        self.write("diy-output/prototypes/P-1.html", GOOD_HTML)
        stripped = re.sub(r"^form_factor: .*" + NL, "", GOOD_DESIGN, flags=re.MULTILINE)
        stripped = re.sub(r"^modes: .*" + NL, "", stripped, flags=re.MULTILINE)
        base = stripped.replace("frontend_framework: html", NL.join([
            "frontend_framework: html", "form_factor: 响应式 Web"]))
        dark_full = NL.join([
            "    dark:", "      bg: '#0f1115'", "      surface: '#1a1d24'",
            "      text: '#f2f4f8'", "      text_muted: '#a8b0bd'",
            "      accent: '#7cc4ff'", "      accent_text: '#0f1115'",
        ])
        with_dark = base.replace("    accent_text: '#ffffff'",
                                 "    accent_text: '#ffffff'" + NL + dark_full)
        dpath = self.write("diy-output/design.yaml",
                           base.replace("frontend_framework: html",
                                        "frontend_framework: html" + NL + "modes: 双模"))
        for label, body in (
                ("缺 dark", base + NL + "modes: 双模"),
                ("角色残（缺 text_muted）",
                 base.replace("    accent_text: '#ffffff'",
                              "    accent_text: '#ffffff'" + NL + dark_full)
                     .replace("      text_muted: '#a8b0bd'" + NL, "")
                     + NL + "modes: 双模" + NL),
                ("值非 hex",
                 base.replace("frontend_framework: html",
                              "frontend_framework: html" + NL + "modes: 双模")
                     .replace("    accent_text: '#ffffff'",
                              "    accent_text: '#ffffff'" + NL +
                              dark_full.replace("'#f2f4f8'", "雾白")))):
            with self.subTest(shape=label):
                self.write("diy-output/design.yaml", body)
                v = run_engine(["validate", "--design", dpath, "--json"])
                self.assertEqual([x["code"] for x in json.loads(v.stdout)["violations"]],
                                 ["MODES_TOKEN_PAIR_MISSING"], v.stdout)
                a = run_engine(["audit", "--design", dpath, "--json",
                                "--src", os.path.join(self.root, "diy-output", "prototypes")])
                self.assertIn("MODES_TOKEN_PAIR_MISSING",
                              [x["code"] for x in json.loads(a.stdout)["violations"]],
                              "audit 未联动：%s" % label)
        # 双模 + 六角色全合法 hex → validate 与 audit 双过
        ok_doc = with_dark.replace("frontend_framework: html",
                                   "frontend_framework: html" + NL + "modes: 双模")
        self.write("diy-output/design.yaml", ok_doc)
        v2 = run_engine(["validate", "--design", dpath, "--json"])
        self.assertEqual(v2.returncode, 0, v2.stdout)
        a2 = run_engine(["audit", "--design", dpath, "--json",
                         "--src", os.path.join(self.root, "diy-output", "prototypes")])
        self.assertEqual(a2.returncode, 0, a2.stdout)

    # trace: C·12 §7-5①（亮/暗 单模携 dark → MODES_INVALID，msg 注明「dark 仅 双模 可有」）
    def test_single_mode_with_dark_rejected(self):
        import re
        self.write("diy-output/prototypes/P-1.html", GOOD_HTML)
        stripped = re.sub(r"^form_factor: .*" + NL, "", GOOD_DESIGN, flags=re.MULTILINE)
        stripped = re.sub(r"^modes: .*" + NL, "", stripped, flags=re.MULTILINE)
        dark_full = NL.join([
            "    dark:", "      bg: '#0f1115'", "      surface: '#1a1d24'",
            "      text: '#f2f4f8'", "      text_muted: '#a8b0bd'",
            "      accent: '#7cc4ff'", "      accent_text: '#0f1115'",
        ])
        with_dark = stripped.replace(
            "frontend_framework: html",
            "frontend_framework: html" + NL + "form_factor: 响应式 Web").replace(
            "    accent_text: '#ffffff'",
            "    accent_text: '#ffffff'" + NL + dark_full)
        dpath = self.write("diy-output/design.yaml", with_dark + NL + "modes: 亮" + NL)
        v = run_engine(["validate", "--design", dpath, "--json"])
        data = json.loads(v.stdout)
        self.assertEqual([x["code"] for x in data["violations"]], ["MODES_INVALID"], v.stdout)
        self.assertIn("dark 仅 双模 可有", data["violations"][0]["msg"])
        self.assertEqual(data["violations"][0]["where"], "design.yaml tokens.color.dark")
        # 暗单模同判
        self.write("diy-output/design.yaml", with_dark + NL + "modes: 暗" + NL)
        v2 = run_engine(["validate", "--design", dpath, "--json"])
        self.assertEqual([x["code"] for x in json.loads(v2.stdout)["violations"]],
                         ["MODES_INVALID"], v2.stdout)

    # trace: C·12 §7-5② / §4 验收 #13（双模暗色同款 5 组配对；单模零暗色对）
    def test_check_dual_mode_dark_contrast_pairs(self):
        import re
        self.write("diy-output/prototypes/P-1.html", GOOD_HTML)
        stripped = re.sub(r"^form_factor: .*" + NL, "", GOOD_DESIGN, flags=re.MULTILINE)
        stripped = re.sub(r"^modes: .*" + NL, "", stripped, flags=re.MULTILINE)
        dark_full = NL.join([
            "    dark:", "      bg: '#0f1115'", "      surface: '#1a1d24'",
            "      text: '#f2f4f8'", "      text_muted: '#a8b0bd'",
            "      accent: '#7cc4ff'", "      accent_text: '#0f1115'",
        ])
        with_dark = stripped.replace(
            "    accent_text: '#ffffff'",
            "    accent_text: '#ffffff'" + NL + dark_full)
        dpath = self.write("diy-output/design.yaml",
                           with_dark + NL + "modes: 双模" + NL)
        c = run_engine(["check", "--design", dpath, "--json"])
        data = json.loads(c.stdout)
        self.assertEqual(c.returncode, 0, c.stdout)
        pairs = [list(p) for p in data["checked"]["contrast_pairs"]]
        self.assertEqual(pairs, [["text", "bg"], ["text", "surface"],
                                 ["text_muted", "bg"], ["text_muted", "surface"],
                                 ["accent_text", "accent"],
                                 ["dark.text", "dark.bg"], ["dark.text", "dark.surface"],
                                 ["dark.text_muted", "dark.bg"],
                                 ["dark.text_muted", "dark.surface"],
                                 ["dark.accent_text", "dark.accent"]],
                         "暗色对未以 dark.<role> 形态原样枚举")
        self.assertEqual(data["counts"]["contrast_pairs"], 10)
        # 暗色对 <4.5:1 → contrast 违规（where 带 dark. 前缀）
        broken = self.write("diy-output/design.yaml",
                            with_dark.replace("      text: '#f2f4f8'", "      text: '#666666'")
                                     + NL + "modes: 双模" + NL)
        c2 = run_engine(["check", "--design", broken, "--json"])
        dark_vs = [x for x in json.loads(c2.stdout)["violations"]
                   if x["code"] == "contrast" and "dark." in x["where"]]
        self.assertTrue(dark_vs, "暗色对比度违规未被守（audit 只判存在性）")
        self.assertIn("dark.text(#666666) on dark.bg(#0f1115)", dark_vs[0]["msg"])
        # 单模（亮，即使误携 dark）→ 零暗色对（对拍：仍 5 组）
        single = self.write("diy-output/design.yaml", with_dark + NL + "modes: 亮" + NL)
        c3 = run_engine(["check", "--design", single, "--json"])
        data3 = json.loads(c3.stdout)
        self.assertEqual(len(data3["checked"]["contrast_pairs"]), 5, c3.stdout)
        self.assertEqual(data3["counts"]["contrast_pairs"], 5)

    # trace: C·12 §7-5①（collect_token_hexes 展开 dark——「audit 打自己」盲点回归）
    def test_audit_dark_hexes_whitelisted(self):
        import re
        self.write("diy-output/prototypes/P-1.html", GOOD_HTML)
        stripped = re.sub(r"^form_factor: .*" + NL, "", GOOD_DESIGN, flags=re.MULTILINE)
        stripped = re.sub(r"^modes: .*" + NL, "", stripped, flags=re.MULTILINE)
        dark_full = NL.join([
            "    dark:", "      bg: '#0f1115'", "      surface: '#1a1d24'",
            "      text: '#f2f4f8'", "      text_muted: '#a8b0bd'",
            "      accent: '#7cc4ff'", "      accent_text: '#0f1115'",
        ])
        doc = stripped.replace(
            "    accent_text: '#ffffff'",
            "    accent_text: '#ffffff'" + NL + dark_full) + NL + "modes: 双模" + NL
        dpath = self.write("diy-output/design.yaml", doc)
        # 暗色 token 在实现源码的真实色值位使用 → 不得自判 one-off-color
        src = self.write("diy-output/src/dark.css",
                         "body.dark { background: #0f1115; color: #f2f4f8; }" + NL)
        a = run_engine(["audit", "--design", dpath, "--src", src, "--json"])
        self.assertEqual(a.returncode, 0, a.stdout)
        self.assertEqual(json.loads(a.stdout)["violations"], [], a.stdout)
        # 对照：非 token 色仍报（展开是增量，白名单没放松）
        src2 = self.write("diy-output/src/bad.css", "a { color: #123456; }" + NL)
        a2 = run_engine(["audit", "--design", dpath, "--src", src2, "--json"])
        self.assertEqual([x["code"] for x in json.loads(a2.stdout)["violations"]],
                         ["one-off-color"], a2.stdout)

    # trace: C·12 §7-5③ / §4 验收 #14（移动端按压态；非移动端四态逐字不动）
    def test_mobile_press_state_required(self):
        import re
        self.write("diy-output/prototypes/P-1.html", GOOD_HTML)
        stripped = re.sub(r"^form_factor: .*" + NL, "", GOOD_DESIGN, flags=re.MULTILINE)
        stripped = re.sub(r"^modes: .*" + NL, "", stripped, flags=re.MULTILINE)
        with_ff = lambda ff: stripped.replace(
            "frontend_framework: html",
            "frontend_framework: html" + NL + "form_factor: " + ff + NL + "modes: 亮")
        dpath = self.write("diy-output/design.yaml", with_ff("移动端"))
        v = run_engine(["validate", "--design", dpath, "--json"])
        data = json.loads(v.stdout)
        self.assertEqual([x["code"] for x in data["violations"]], ["EMPTY_FIELD"], v.stdout)
        self.assertIn("P-1 缺交互状态 按压",
                      [x["msg"] for x in data["violations"]], v.stdout)
        # 按压在而悬停缺 → rc=0（移动端不要求悬停）
        pressed = stripped.replace("  - name: 悬停", "  - name: 按压").replace(
            "frontend_framework: html",
            "frontend_framework: html" + NL + "form_factor: 移动端" + NL + "modes: 亮")
        self.write("diy-output/design.yaml", pressed)
        v2 = run_engine(["validate", "--design", dpath, "--json"])
        self.assertEqual(v2.returncode, 0, v2.stdout)
        self.assertTrue(json.loads(v2.stdout)["ok"])
        # 非移动端四态逐字不动：悬停缺 → 报「悬停」（报错文本与 HEAD 逐字一致）
        for ff in ("响应式 Web", "桌面", "多端", None):
            with self.subTest(form_factor=ff or "（缺键）"):
                body = with_ff(ff) if ff else stripped + NL + "modes: 亮" + NL
                hoverless = body.replace(
                    "  - name: 悬停" + NL + "    signals: [图标, 动效]" + NL, "")
                self.write("diy-output/design.yaml", hoverless)
                v3 = run_engine(["validate", "--design", dpath, "--json"])
                msgs = [x["msg"] for x in json.loads(v3.stdout)["violations"]]
                self.assertIn("P-1 缺交互状态 悬停", msgs,
                              "非移动端四态判据漂移（form_factor=%r）" % ff)
                self.assertNotIn("P-1 缺交互状态 按压", msgs)

    # trace: C·12 §7-5③（transition 页级门同口径：移动端按按压判，非移动端按悬停判）
    def test_transition_gate_uses_press_state_on_mobile(self):
        import re
        self.write("diy-output/prototypes/P-1.html", GOOD_HTML)
        stripped = re.sub(r"^form_factor: .*" + NL, "", GOOD_DESIGN, flags=re.MULTILINE)
        stripped = re.sub(r"^modes: .*" + NL, "", stripped, flags=re.MULTILINE)
        staged = stripped.replace("  route: /todos",
                                  "  route: /todos" + NL + "  status: 结构稿中")
        dpath = self.write("diy-output/design.yaml", staged.replace(
            "frontend_framework: html",
            "frontend_framework: html" + NL +
            "form_factor: 移动端" + NL + "modes: 亮"))
        # 悬停在、按压缺 → 结构稿中 → 待验收 被页级门拦（GATE_FAILED）
        t = run_engine(["transition", "--design", dpath, "--page", "P-1",
                        "--to", "待验收", "--json"])
        self.assertEqual(t.returncode, 1, t.stdout)
        self.assertIn("GATE_FAILED", [x["code"] for x in json.loads(t.stdout)["violations"]])
        self.assertIn("P-1 缺交互状态 按压",
                      [x["msg"] for x in json.loads(t.stdout)["violations"]])
        # 按压在、悬停缺 → 门过
        self.write("diy-output/design.yaml", staged.replace(
            "  - name: 悬停", "  - name: 按压").replace(
            "frontend_framework: html",
            "frontend_framework: html" + NL +
            "form_factor: 移动端" + NL + "modes: 亮"))
        t2 = run_engine(["transition", "--design", dpath, "--page", "P-1",
                         "--to", "待验收", "--json"])
        self.assertEqual(t2.returncode, 0, t2.stdout)
        self.assertTrue(json.loads(t2.stdout)["ok"])


if __name__ == "__main__":
    unittest.main()
