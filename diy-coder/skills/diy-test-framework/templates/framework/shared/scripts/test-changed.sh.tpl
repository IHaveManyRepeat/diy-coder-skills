#!/usr/bin/env bash
# placeholders: TEST_CMD TEST_GLOB BASE_BRANCH
# 只跑与本次改动相关的测试（由 diy-test-framework 渲染；要改请改技能内模板，不要改本文件）
# 用法：bash scripts/test-changed.sh（BASE_BRANCH 可用环境变量覆盖，默认 {{BASE_BRANCH}}）
set -euo pipefail

BASE_BRANCH="${BASE_BRANCH:-{{BASE_BRANCH}}}"
if ! git rev-parse --verify --quiet "origin/${BASE_BRANCH}" >/dev/null; then
  echo "缺少 origin/${BASE_BRANCH}：先 git fetch origin ${BASE_BRANCH}，或改 BASE_BRANCH 后重试" >&2
  exit 2
fi

CHANGED="$(git diff --name-only "origin/${BASE_BRANCH}...HEAD" -- '{{TEST_GLOB}}')"
if [ -z "${CHANGED}" ]; then
  echo "无改动测试文件（对比 origin/${BASE_BRANCH}）——跳过"
  exit 0
fi

echo "改动测试文件："
printf '%s\n' "${CHANGED}"
# 选测 = 在完整测试命令后追加改动文件路径；框架若不接受文件参数，请改用其自带的筛选旗标
# shellcheck disable=SC2086
{{TEST_CMD}} ${CHANGED}
