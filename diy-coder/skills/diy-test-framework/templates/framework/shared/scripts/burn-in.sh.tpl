#!/usr/bin/env bash
# placeholders: TEST_CMD BURN_IN_ITERATIONS
# 抖动检测：连跑 N 轮，任何一轮失败即退出（由 diy-test-framework 渲染；要改请改技能内模板）
# 用法：bash scripts/burn-in.sh（BURN_IN_ITERATIONS 可用环境变量覆盖，默认 {{BURN_IN_ITERATIONS}}）
set -euo pipefail

ITERATIONS="${BURN_IN_ITERATIONS:-{{BURN_IN_ITERATIONS}}}"
echo "burn-in：连跑 ${ITERATIONS} 轮（目标 = UI 抖动，后端面按需执行）"
for i in $(seq 1 "${ITERATIONS}"); do
  echo "burn-in iteration $i/${ITERATIONS}"
  {{TEST_CMD}} || exit 1
done
echo "burn-in 通过：${ITERATIONS} 轮无失败"
