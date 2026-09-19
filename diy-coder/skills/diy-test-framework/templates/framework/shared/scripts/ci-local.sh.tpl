#!/usr/bin/env bash
# placeholders: INSTALL_CMD LINT_CMD TEST_CMD
# 本地复现 CI（由 diy-test-framework 渲染；要改请改技能内模板，不要改本文件）
# 与流水线同一条命令、同一个 CI=true —— 本地绿了再推，CI 才算数
set -euo pipefail
export CI=true

echo "== 安装依赖 =="
{{INSTALL_CMD}}

echo "== 静态检查（与 CI lint 阶段同一条命令）=="
{{LINT_CMD}}

echo "== 跑测试（与 CI test 阶段同一条命令）=="
{{TEST_CMD}}

echo "== CI 本地复现通过 =="
