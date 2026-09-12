# -*- coding: utf-8 -*-
"""S-15 设计还原闭环 e2e 测试：绑定引用可解析 / token 单一源审计 / 视觉对比层。

夹具复用 test_design 的 GOOD_DESIGN/GOOD_HTML（合规基准），偏差实现页由其派生。
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
from test_design import GOOD_DESIGN, GOOD_HTML  # noqa: E402

NL = chr(10)

STORIES = NL.join([
    "project:", "  name: mini", "  status: final", "stories:",
    "- id: S-T1", "  title: 待办列表页", "  status: pending", "  acceptance_criteria:",
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

DEVIATED_IMPL = GOOD_HTML.replace(
    "--color-bg: #ffffff;", "--color-bg: #e8e8ff;").replace(
    "--color-text: #1a1a1a;", "--color-text: #444444;").replace(
    "button { background: var(--color-accent); }",
    "button { background: var(--color-accent); padding: 24px 60px; }")


def run_engine(args):
    return subprocess.run([sys.executable, DESIGN_PY] + args,
                          capture_output=True, text=True, encoding="utf-8")


class RestoreLoopTests(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = os.path.join(self.tmp.name, "diy-output")
        os.makedirs(os.path.join(self.out, "prototypes"))

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, rel, content):
        path = os.path.join(self.out, rel)
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

    # trace: S-15 AC-15.2 TC-15.2.1
    def test_one_off_values_fail_token_audit(self):
        dpath = self.write("design.yaml", GOOD_DESIGN)
        bad = self.write("impl_bad.html", ONE_OFF_IMPL)
        r = run_engine(["audit", "--design", dpath, "--src", bad, "--json"])
        self.assertEqual(r.returncode, 1, r.stdout)
        data = json.loads(r.stdout)
        self.assertFalse(data["pass"])
        kinds = {x["kind"] for x in data["violations"]}
        self.assertIn("one-off-color", kinds)
        self.assertIn("one-off-font-size", kinds)
        good = self.write("impl_good.html", GOOD_HTML)
        g = run_engine(["audit", "--design", dpath, "--src", good, "--json"])
        self.assertEqual(g.returncode, 0, g.stdout)
        self.assertTrue(json.loads(g.stdout)["pass"])

    # trace: S-15 AC-15.3 TC-15.3.1
    def test_visual_compare_scores_and_rejects_deviation(self):
        dpath = self.write("design.yaml", GOOD_DESIGN)
        self.write("prototypes/P-1.html", GOOD_HTML)
        deviated = self.write("impl_dev.html", DEVIATED_IMPL)
        r = run_engine(["compare", "--design", dpath, "--page", "P-1",
                        "--implementation", deviated, "--json"])
        self.assertEqual(r.returncode, 1, r.stdout)
        data = json.loads(r.stdout)
        self.assertLess(data["score"], data["threshold"])
        self.assertGreaterEqual(len(data["viewports"]), 2, "未做多视口对比")
        for v in data["viewports"]:
            self.assertIn("viewport", v)
            self.assertIn("score", v)
        same = self.write("impl_same.html", GOOD_HTML)
        g = run_engine(["compare", "--design", dpath, "--page", "P-1",
                        "--implementation", same, "--json"])
        self.assertEqual(g.returncode, 0, g.stdout)
        gd = json.loads(g.stdout)
        self.assertGreaterEqual(gd["score"], gd["threshold"])


if __name__ == "__main__":
    unittest.main()
