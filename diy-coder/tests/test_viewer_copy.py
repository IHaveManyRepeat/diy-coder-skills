# -*- coding: utf-8 -*-
"""diy-viewer 表格 ID 复制按钮契约测试（夜队列 Q-003）。

夹具：dict 数据直接调 render_doc_page（features 为纯 flat dict 列表 → 走 render_table），
断言
  ① 只有带 ID 的行出复制按钮（无 ID 行不得出）
  ② 按钮紧跟该行 ID 单元格文本
  ③ data-file 取 <source_disp>/<doc>.yaml，data-id 取行 ID；实例路径含实例名
  ④ 页面含 navigator.clipboard 与 execCommand 兜底
  ⑤ 复制文案 A 的固定片段在场
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
VIEWER_SCRIPTS = os.path.join(HERE, "..", "skills", "diy-viewer", "scripts")
sys.path.insert(0, os.path.abspath(VIEWER_SCRIPTS))
import viewer_pages  # noqa: E402  直接调渲染函数，取 HTML 断言

DATA = {
    "project": {"name": "fx", "status": "草稿"},
    "features": [
        {"id": "FR-001", "title": "甲"},
        {"id": "FR-002", "title": "乙"},
        {"title": "无ID行"},
    ],
}


class ViewerCopyButtonTests(unittest.TestCase):
    def render(self, source="diy-output"):
        return viewer_pages.render_doc_page("prd", DATA, [("prd", DATA)], source)

    def test_copy_buttons_count_matches_rows_with_id(self):
        html = self.render()
        self.assertEqual(html.count('class="copy-id"'), 2,
                         "复制按钮数应等于有 ID 的行数（无 ID 行不得出按钮）")

    def test_button_follows_id_in_same_cell(self):
        html = self.render()
        self.assertRegex(html, r'FR-001<button class="copy-id"',
                         "FR-001 单元格内 ID 后未紧跟复制按钮")
        self.assertRegex(html, r'FR-002<button class="copy-id"',
                         "FR-002 单元格内 ID 后未紧跟复制按钮")

    def test_data_file_and_data_id_attributes(self):
        html = self.render()
        self.assertIn('data-file="diy-output/prd.yaml"', html, "data-file 未取来源路径")
        self.assertIn('data-id="FR-001"', html, "FR-001 缺 data-id")
        self.assertIn('data-id="FR-002"', html, "FR-002 缺 data-id")

    def test_instance_source_path_in_data_file(self):
        html = self.render("diy-output/inst")
        self.assertIn('data-file="diy-output/inst/prd.yaml"', html,
                      "实例路径未含实例名")

    def test_clipboard_api_and_exec_command_fallback_present(self):
        html = self.render()
        self.assertIn("navigator.clipboard", html, "缺 clipboard API 复制路径")
        self.assertIn("execCommand", html, "缺 execCommand 兜底")

    def test_copy_text_fragments_present(self):
        html = self.render()
        self.assertIn("请打开产物文件", html, "复制文案缺「请打开产物文件」")
        self.assertIn("定位条目", html, "复制文案缺「定位条目」")


if __name__ == "__main__":
    unittest.main()
