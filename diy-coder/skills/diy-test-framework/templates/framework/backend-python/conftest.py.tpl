# placeholders:
# -*- coding: utf-8 -*-
"""共享夹具（由 diy-test-framework 渲染；要改请改技能内模板，不要改本文件）。

新的夹具一律加在这里；测试文件不各自造连接/临时目录。
"""
import os
import tempfile

import pytest


@pytest.fixture()
def tmp_workdir():
    """每个用例一个临时目录（确定性隔离；用例之间不共享可变状态）。"""
    with tempfile.TemporaryDirectory(prefix="t-") as path:
        yield path


@pytest.fixture(scope="session")
def base_url():
    """被测服务地址（本地缺省，CI 由环境变量覆盖）。"""
    return os.environ.get("BASE_URL", "http://localhost:8000")
