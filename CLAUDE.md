# CLAUDE.md

回复用户的要求（代码、文档、解释除外）：
- 精简：能用一个字，不能用两个字
- 准确：可查证的不猜测

复用纪律（详见 `diy-coder/docs/code-quality.md`）：
- 写工具函数前先查 `diy-tools/scripts/diyc_lib.py`，有则 import 使用
- 新通用函数提炼入 diyc_lib，随批走 sync
- 单文件 ≤400 行，超线即拆

