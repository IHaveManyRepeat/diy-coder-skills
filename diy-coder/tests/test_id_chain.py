# trace: S-12 AC-12.1 AC-12.2 TC-12.1.1 TC-12.2.1
"""ID 链一致性校验测试（FR-4.4：悬空/孤儿引用渲染时标红，断裂一眼可见）。

- TC-12.1.1 悬空引用：stories 副本某 AC refs 指向不存在的 FR ID → 渲染后
  该引用行内带错误标记，且页面顶部告警区列出该项
- TC-12.2.1 孤儿 must FR：prd 副本某 must FR 无任何 AC/用例引用 → 渲染后
  该 FR 条目带孤儿标红提示
"""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIEWER = HERE.parent / "skills" / "diy-viewer" / "scripts" / "viewer.py"

PRD = """project:
  name: fixture
  status: 已定稿
  created: '2026-09-09'
  updated: '2026-09-09'
features:
- id: F-1
  name: 组
  description: 夹具功能组
  requirements:
  - id: FR-1.1
    statement: 被引用的需求
    priority: 必须
  - id: FR-1.2
    statement: 无任何引用的必须级需求（孤儿）
    priority: 必须
  - id: FR-1.3
    statement: 无引用的应该级需求（不在孤儿判定范围）
    priority: 应该
"""


def make_root():
    root = Path(tempfile.mkdtemp(prefix="tmp-tc12-"))
    (root / "diy-coder.yaml").write_text(
        "paths:\n  output_dir: diy-output\nviewer:\n  auto_open: false\n",
        encoding="utf-8")
    out = root / "diy-output"
    out.mkdir(parents=True)
    return root, out


def run_viewer(root):
    return subprocess.run(
        [sys.executable, str(VIEWER), "--project-root", str(root), "--no-open"],
        capture_output=True, text=True, timeout=60,
        stdin=subprocess.DEVNULL)


class TC_12_1_1_DanglingRefMarked(unittest.TestCase):
    # trace: S-12 AC-12.1 TC-12.1.1
    def setUp(self):
        self.root, self.out = make_root()
        (self.out / "prd.yaml").write_text(PRD, encoding="utf-8")
        (self.out / "stories.yaml").write_text(
            "project:\n"
            "  name: fixture\n"
            "  status: 已定稿\n"
            "  created: '2026-09-09'\n"
            "  updated: '2026-09-09'\n"
            "stories:\n"
            "- id: S-1\n"
            "  title: 夹具故事\n"
            "  narrative: n\n"
            "  acceptance_criteria:\n"
            "  - id: AC-1.1\n"
            "    given: g\n"
            "    when: w\n"
            "    then: t\n"
            "    refs:\n"
            "    - FR-1.1\n"
            "    - FR-99.9\n"
            "  status: 已完成\n", encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_dangling_ref_marked_and_alerted(self):
        result = run_viewer(self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        h = (self.out / ".view" / "stories.html").read_text(encoding="utf-8")
        # 引用处带错误标记（正文 refs + 详情面板模板合法重复渲染，≥1 即非静默）
        self.assertGreaterEqual(h.count("引用不存在"), 1,
                                "悬空引用渲染为正常内容（静默）")
        # 顶部告警区列出该项（告警 1 次 + 行内标记，FR-99.9 至少 2 处可见）
        self.assertIn("悬空引用", h, "页面顶部无悬空引用告警")
        self.assertGreaterEqual(h.count("FR-99.9"), 2,
                                "悬空 ID 应在行内标记与顶部告警同时可见")
        # 对照：无悬空的 prd 页面零误报（正文区；页面尾部全量 ID 详情
        # 模板含 stories 的悬空标记属面板链式查看的合法跨文档内容）
        p = (self.out / ".view" / "prd.html").read_text(encoding="utf-8")
        main_part = p.split("</main>")[0]
        self.assertNotIn("引用不存在", main_part, "正常引用被误标悬空")
        self.assertNotIn("悬空引用", p, "无悬空的页面出现告警")


class TC_12_2_1_OrphanMustFR(unittest.TestCase):
    # trace: S-12 AC-12.2 TC-12.2.1
    def setUp(self):
        self.root, self.out = make_root()
        (self.out / "prd.yaml").write_text(PRD, encoding="utf-8")
        (self.out / "stories.yaml").write_text(
            "project:\n"
            "  name: fixture\n"
            "  status: 已定稿\n"
            "  created: '2026-09-09'\n"
            "  updated: '2026-09-09'\n"
            "stories:\n"
            "- id: S-1\n"
            "  title: 夹具故事\n"
            "  narrative: n\n"
            "  acceptance_criteria:\n"
            "  - id: AC-1.1\n"
            "    given: g\n"
            "    when: w\n"
            "    then: t\n"
            "    refs:\n"
            "    - FR-1.1\n"
            "  status: 已完成\n", encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_orphan_must_fr_marked(self):
        result = run_viewer(self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        h = (self.out / ".view" / "prd.html").read_text(encoding="utf-8")
        # 孤儿 must FR 条目行标红 + 孤儿徽章
        self.assertIn('<tr class="orphan" id="FR-1.2">', h,
                      "孤儿 must FR 条目未标红")
        self.assertIn("孤儿", h, "孤儿条目无标红提示徽章")
        # 对照：被引用的 FR-1.1 与 should 级 FR-1.3 均不标
        self.assertNotIn('<tr class="orphan" id="FR-1.1">', h,
                         "被引用的 FR 被误标孤儿")
        self.assertNotIn('<tr class="orphan" id="FR-1.3">', h,
                         "should 级无引用 FR 不在孤儿判定范围")


if __name__ == "__main__":
    unittest.main()
