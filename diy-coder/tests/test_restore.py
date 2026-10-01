# -*- coding: utf-8 -*-
"""S-15 设计采用闭环测试：绑定引用可解析 / token 单一源审计 / 零重写采用条款。

2026-09-12 D-10 变更：视觉截图对比（compare）废弃删除，TC-15.3.1 改写为
设计稿零重写采用与结构对照审查。夹具复用 test_design 的 GOOD_DESIGN/GOOD_HTML。
"""
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
DESIGN_PY = os.path.join(HERE, "..", "skills", "diy-design", "scripts", "design.py")
VIEWER_PY = os.path.join(HERE, "..", "skills", "diy-viewer", "scripts", "viewer.py")
SKILL_EPICS = os.path.join(HERE, "..", "skills", "diy-epics-stories", "SKILL.md")
SKILL_DESIGN = os.path.join(HERE, "..", "skills", "diy-design", "SKILL.md")
SKILL_DEV = os.path.join(HERE, "..", "skills", "diy-dev", "SKILL.md")
SKILL_REVIEW = os.path.join(HERE, "..", "skills", "diy-review", "SKILL.md")
REVIEW_STEPS = os.path.join(HERE, "..", "skills", "diy-review", "steps")
from test_design import GOOD_DESIGN, GOOD_HTML  # noqa: E402

NL = chr(10)

STORIES = NL.join([
    "project:", "  name: mini", "  status: 已定稿", "stories:",
    "- id: S-T1", "  title: 待办列表页", "  status: 待办", "  acceptance_criteria:",
    "  - id: AC-T1.1",
    "    given: 待办列表页", "    when: 页面加载", "    then: 按设计稿渲染列表",
    "    refs: [F-1]", "    design_ref: P-1",
    "  - id: AC-T1.2",
    "    given: 悬空场景", "    when: 引用检查", "    then: 应标红",
    "    refs: [F-1]", "    design_ref: P-99",
])

ONE_OFF_IMPL = GOOD_HTML.replace(
    "body { background: var(--color-bg); color: var(--color-text); }",
    "body { background: var(--color-bg); color: var(--color-text); font-size: 17px; }").replace(
    "button { background: var(--color-accent); }",
    "button { background: #ff0000; }")


def run_engine(args):
    return subprocess.run([sys.executable, DESIGN_PY] + args,
                          capture_output=True, text=True, encoding="utf-8")


class RestoreLoopTests(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = os.path.join(self.tmp.name, "diy-output")

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, rel, content):
        path = os.path.join(self.out, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    # trace: S-15 AC-15.1 TC-15.1.1
    def test_design_ref_resolves_and_dangles(self):
        self.write("design.yaml", GOOD_DESIGN)
        self.write("stories.yaml", STORIES)
        v = subprocess.run([sys.executable, VIEWER_PY, "--project-root", self.tmp.name],
                           capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(v.returncode, 0, v.stderr)
        page = io.open(os.path.join(self.out, ".view", "stories.html"),
                       encoding="utf-8").read()
        body = page.split("</main>")[0]
        self.assertIn("P-99", body, "悬空引用未渲染")
        self.assertIn("引用不存在", body, "悬空 design_ref 未标红")
        self.assertIn('href="design.html#P-1"', body, "合法 design_ref 未成为可解析链接")
        skill = io.open(SKILL_EPICS, encoding="utf-8").read()
        self.assertIn("design_ref", skill, "diy-epics-stories 缺绑定条款")

    # trace: S-15 AC-15.1 B-6 SS-017-04（设计侧只读：删/改页面 id 前置扫 AC[].design_ref）
    def test_design_scans_design_ref_before_page_removal(self):
        design = io.open(SKILL_DESIGN, encoding="utf-8").read()
        self.assertIn("AC[].design_ref", design, "diy-design 不知道 AC 绑定面，删除页面即静默悬空")
        self.assertIn("diy-epics-stories", design, "悬空 design_ref 未路由回 diy-epics-stories")
        self.assertIn("只读", design, "design 侧未声明 stories.yaml 只读（写权在 epics-stories）")

    # trace: S-15 AC-15.2 TC-15.2.1
    def test_one_off_values_fail_token_audit(self):
        dpath = self.write("design.yaml", GOOD_DESIGN)
        bad = self.write("impl_bad.html", ONE_OFF_IMPL)
        r = run_engine(["audit", "--design", dpath, "--src", bad, "--json"])
        self.assertEqual(r.returncode, 1, r.stdout)
        data = json.loads(r.stdout)
        self.assertFalse(data["ok"])
        kinds = {x["code"] for x in data["violations"]}
        self.assertIn("one-off-color", kinds)
        self.assertIn("one-off-font-size", kinds)
        good = self.write("impl_good.html", GOOD_HTML)
        g = run_engine(["audit", "--design", dpath, "--src", good, "--json"])
        self.assertEqual(g.returncode, 0, g.stdout)
        self.assertTrue(json.loads(g.stdout)["ok"])

    # trace: S-15 AC-15.3 TC-15.3.1 D-10（2026-09-12 变更：截图对比废弃，改零重写采用）
    # trace: C·12 回派 W3-R1 读源改——「结构对照」/「线框」随 L4 段下沉
    #        steps/l4-design-adoption.md（assertIn 改读该文件）；「截图对比」的 NotIn
    #        面随拆分扩为「主文件 + steps 拼接」（文档面 = 教学面，与 test_diy_review_wds
    #        的 `--to 已批准` 同口径）。断言本体（锚串/失败消息）零改动。
    def test_adopt_zero_rewrite_terms_and_compare_removed(self):
        dev = io.open(SKILL_DEV, encoding="utf-8").read()
        self.assertIn("零重写", dev, "diy-dev 缺零重写采用条款")
        self.assertIn("设计稿代码", dev, "diy-dev 缺「在设计稿代码上叠加逻辑」条款")
        review = io.open(SKILL_REVIEW, encoding="utf-8").read()
        l4 = io.open(os.path.join(REVIEW_STEPS, "l4-design-adoption.md"),
                     encoding="utf-8").read()
        self.assertIn("结构对照", l4, "diy-review L4 缺结构对照条款")
        self.assertIn("线框", l4, "diy-review L4 缺线框对照对象")
        steps_all = NL.join(
            io.open(os.path.join(REVIEW_STEPS, name), encoding="utf-8").read()
            for name in sorted(os.listdir(REVIEW_STEPS)) if name.endswith(".md"))
        self.assertNotIn("截图对比", review + NL + steps_all, "废弃的截图对比条款仍残留")
        h = run_engine(["--help"])
        self.assertNotIn("compare", h.stdout, "design.py compare 子命令未删除")


if __name__ == "__main__":
    unittest.main()
