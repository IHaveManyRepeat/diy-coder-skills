# -*- coding: utf-8 -*-
"""diy-viewer 批 5a：distillate {text, src} 与 prd out_of_scope 两形态渲染测试。"""

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
VSCRIPTS = os.path.join(HERE, "..", "skills", "diy-viewer", "scripts")
sys.path.insert(0, VSCRIPTS)

import viewer_refs as _refs  # noqa: E402
from viewer_distillate import (_render_distillate_entries,  # noqa: E402
                               _render_out_of_scope)
from viewer_labels import KEY_LABELS  # noqa: E402


class SrcLabelTests(unittest.TestCase):
    def test_src_label_registered(self):
        self.assertEqual(KEY_LABELS.get("src"), "来源", "缺 src 中文标签（零裸键纪律）")

    def test_text_not_hijacked_for_distillate(self):
        # design token 的「文字」标签保持原义，不复用为 distillate 内容列
        self.assertEqual(KEY_LABELS.get("text"), "文字")


class DistillateRenderTests(unittest.TestCase):
    def setUp(self):
        _refs.ID_INDEX.clear()
        _refs.ID_INDEX["RF-001"] = {
            "doc": "research", "preview": "通勤焦虑下降",
            "node": {"id": "RF-001", "claim": "城市通勤用户对续航焦虑的敏感度逐年下降"},
        }
        _refs._RENDER_DOC = "research"

    def test_text_and_src_rendered(self):
        html = _render_distillate_entries(
            "target_users",
            [{"text": "整车厂", "src": "RF-001"}],
            {"research": {}},
        )
        self.assertIn("整车厂", html)
        self.assertIn("RF-001", html)
        self.assertIn("内容", html, "text 列须有文档级「内容」表头")
        self.assertIn("来源", html)

    def test_missing_src_badged(self):
        html = _render_distillate_entries(
            "value_props", [{"text": "机会"}], {})
        self.assertIn("缺来源", html)

    def test_dangling_src_red(self):
        html = _render_distillate_entries(
            "constraints", [{"text": "限", "src": "RF-999"}], {})
        self.assertIn("dangling", html)
        self.assertIn("RF-999", html)


class OutOfScopeRenderTests(unittest.TestCase):
    def setUp(self):
        _refs.ID_INDEX.clear()
        _refs.ID_INDEX["PQ-001"] = {
            "doc": "prfaq", "preview": "数据在哪",
            "node": {"id": "PQ-001", "q": "数据存在哪里？", "a": "全部落本地 YAML"},
        }
        _refs._RENDER_DOC = "prd"

    def test_inherit_expands_mother_text(self):
        html = _render_out_of_scope(
            [{"src": "PQ-001"}], {"prfaq": {}})
        self.assertIn("继承", html)
        self.assertIn("PQ-001", html)
        # 母体文本经 ID_INDEX.node 的可读字段展开
        self.assertIn("数据存在哪里", html)

    def test_self_produced_os_rendered(self):
        html = _render_out_of_scope(
            [{"id": "OS-001", "statement": "不做移动端"}], {})
        self.assertIn("自产", html)
        self.assertIn("不做移动端", html)
        self.assertIn("OS-001", html)

    def test_dotted_path_expands(self):
        prfaq = {"prfaq": {"press_release": {"headline": "三分钟出稿"}}}
        html = _render_out_of_scope(
            [{"src": "prfaq.press_release.headline"}],
            {"prfaq": prfaq})
        self.assertIn("三分钟出稿", html)

    def test_dangling_mother_marked(self):
        html = _render_out_of_scope([{"src": "PQ-999"}], {})
        self.assertIn("dangling", html)
        self.assertIn("PQ-999", html)


class ResolveSrcTextTests(unittest.TestCase):
    def setUp(self):
        _refs.ID_INDEX.clear()
        _refs.ID_INDEX["RK-001"] = {
            "doc": "research", "preview": "密度差",
            "node": {"id": "RK-001", "text": "充电网络密度差异大于价格差异"},
        }

    def test_id_node_text(self):
        text, err = _refs.resolve_src_text("RK-001", {})
        self.assertEqual(err, "")
        self.assertEqual(text, "充电网络密度差异大于价格差异")

    def test_missing_id(self):
        text, err = _refs.resolve_src_text("RK-999", {})
        self.assertTrue(err)

    def test_dotted_path_list_index(self):
        docs = {"brief": {"brief": {"extra_sections": [{"name": "范围", "content": "仅本批"}]}}}
        text, err = _refs.resolve_src_text("brief.extra_sections[0]", docs)
        self.assertEqual(err, "")
        self.assertIn("仅本批", text)


if __name__ == "__main__":
    unittest.main()
