# -*- coding: utf-8 -*-
"""变异冒烟夹具的测试面：文件名不带 `test_` 前缀，故主项目 pytest 不收集它。

它只在副本沙箱里、由 mutmut 调起的 pytest 执行（该 pytest 的 rootdir 是本目录，
读本目录的 pytest.ini 拿到 `python_files = check_*.py`）。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from calc import add  # noqa: E402


def test_add():
    assert add(1, 2) == 3
