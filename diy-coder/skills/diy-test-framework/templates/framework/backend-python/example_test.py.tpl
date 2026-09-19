# placeholders:
# -*- coding: utf-8 -*-
"""示例测试（由 diy-test-framework 渲染）——证明 runner 能收集并执行；
真实用例由 diy-test-author 生成（消费 test-plan.yaml 的 TC），生成后可由用户裁决移除本示例。
"""


def test_scaffold_is_ready():
    assert sum([1, 2, 3]) == 6
