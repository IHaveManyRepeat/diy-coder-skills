#!/usr/bin/env bash
# 兼容壳：转发到 install.py（D-8 后统一安装入口，保留既有命令习惯）
# 用法不变: ./sync.sh [目标项目根]
DIR="$(cd "$(dirname "$0")" && pwd)"
if [ $# -eq 0 ]; then
  python "$DIR/install.py"
else
  python "$DIR/install.py" "$1"
fi
