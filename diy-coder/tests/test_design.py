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


if __name__ == "__main__":
    unittest.main()
