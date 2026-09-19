# placeholders: TEST_DIR
# pytest 配置（由 diy-test-framework 渲染；要改请改技能内模板，不要改本文件）
[pytest]
testpaths = {{TEST_DIR}}
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*
addopts = -ra --strict-markers
markers =
    unit: 单组件行为
    integration: 跨组件/产物协作
