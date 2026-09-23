# -*- coding: utf-8 -*-
"""变异冒烟夹具：可被 mutmut 变异的最小被测面。

`add` 的 `+` 是唯一的变异靶点——mutmut 把它变成 `-` 后，check_add 必须转红。
本文件是被测对象，不是测试；夹具约定见 README.md。
"""


def add(a, b):
    return a + b
