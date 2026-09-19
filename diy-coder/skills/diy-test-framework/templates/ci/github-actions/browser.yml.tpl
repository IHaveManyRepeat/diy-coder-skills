# placeholders: RUNTIME_SETUP_CMD INSTALL_CMD LINT_CMD TEST_CMD BROWSER_INSTALL P0_GATE P1_GATE REPORT_PATH CACHE_PATH CACHE_KEY CACHE_RESTORE_KEYS BROWSER_CACHE_PATH BROWSER_CACHE_KEY BROWSER_CACHE_RESTORE_KEYS NOTIFY_SECRET
# GitHub Actions 测试流水线（diy-test-framework 渲染；要改请改技能内模板，不要改本文件）
# 质量门（事实源 = test-framework.yaml 的 ci.gates）：P0 覆盖 {{P0_GATE}} / P1 覆盖 {{P1_GATE}}
# 分片：matrix.shard 已注入 SHARD 环境变量；TEST_CMD 取值可带分片参数（如 `npx playwright test --shard=$SHARD/4`）
# 缓存：依赖与浏览器各一份，键含锁文件哈希；restore-keys 为回退前缀（失配可复用旧缓存）
# 失败通知：secret 名 = {{NOTIFY_SECRET}}（未配置则跳过，见 docs/ci-secrets-checklist.md）
name: Test Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]
  schedule:
    - cron: "0 2 * * 0"          # 每周 burn-in

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  lint:
    name: Lint
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v4
      - name: Set up runtime
        run: {{RUNTIME_SETUP_CMD}}
      - name: Cache dependencies
        uses: actions/cache@v4
        with:
          path: {{CACHE_PATH}}
          key: {{CACHE_KEY}}
          restore-keys: {{CACHE_RESTORE_KEYS}}
      - name: Install dependencies
        run: {{INSTALL_CMD}}
      - name: Run quality checks
        run: {{LINT_CMD}}

  test:
    name: Test (shard ${{ matrix.shard }}/4)
    runs-on: ubuntu-latest
    timeout-minutes: 30
    needs: lint
    strategy:
      fail-fast: false
      matrix:
        shard: [1, 2, 3, 4]
    env:
      SHARD: ${{ matrix.shard }}
    steps:
      - uses: actions/checkout@v4
      - name: Set up runtime
        run: {{RUNTIME_SETUP_CMD}}
      - name: Cache dependencies
        uses: actions/cache@v4
        with:
          path: {{CACHE_PATH}}
          key: {{CACHE_KEY}}
          restore-keys: {{CACHE_RESTORE_KEYS}}
      - name: Cache browsers
        uses: actions/cache@v4
        with:
          path: {{BROWSER_CACHE_PATH}}
          key: {{BROWSER_CACHE_KEY}}
          restore-keys: {{BROWSER_CACHE_RESTORE_KEYS}}
      - name: Install dependencies
        run: {{INSTALL_CMD}}
      - name: Install browsers
        run: {{BROWSER_INSTALL}}
      - name: Run tests
        run: {{TEST_CMD}}
      - name: Upload artifacts on failure
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: test-results-${{ matrix.shard }}
          path: |
            test-results/
            {{REPORT_PATH}}
          retention-days: 30

  burn-in:
    name: Burn-In (flaky detection)
    runs-on: ubuntu-latest
    timeout-minutes: 60
    needs: test
    if: github.event_name == 'pull_request' || github.event_name == 'schedule'
    steps:
      - uses: actions/checkout@v4
      - name: Set up runtime
        run: {{RUNTIME_SETUP_CMD}}
      - name: Cache dependencies
        uses: actions/cache@v4
        with:
          path: {{CACHE_PATH}}
          key: {{CACHE_KEY}}
          restore-keys: {{CACHE_RESTORE_KEYS}}
      - name: Cache browsers
        uses: actions/cache@v4
        with:
          path: {{BROWSER_CACHE_PATH}}
          key: {{BROWSER_CACHE_KEY}}
          restore-keys: {{BROWSER_CACHE_RESTORE_KEYS}}
      - name: Install dependencies
        run: {{INSTALL_CMD}}
      - name: Install browsers
        run: {{BROWSER_INSTALL}}
      - name: Burn-in loop (10 iterations)
        run: |
          for i in $(seq 1 10); do
            echo "burn-in iteration $i/10"
            {{TEST_CMD}} || exit 1
          done
      - name: Upload burn-in failures
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: burn-in-failures
          path: |
            test-results/
            {{REPORT_PATH}}
          retention-days: 30

  report:
    name: Report
    runs-on: ubuntu-latest
    needs: [test, burn-in]
    if: always()
    steps:
      - name: Download all artifacts
        uses: actions/download-artifact@v4
        with:
          path: artifacts
      - name: List collected artifacts
        run: find artifacts -maxdepth 2 -type d | sort
      - name: Summary
        run: |
          echo "## Test Summary" >> "$GITHUB_STEP_SUMMARY"
          echo "- gates: P0 {{P0_GATE}} / P1 {{P1_GATE}}" >> "$GITHUB_STEP_SUMMARY"
          echo "- test: ${{ needs.test.result }} / burn-in: ${{ needs.burn-in.result }}" >> "$GITHUB_STEP_SUMMARY"
          echo "- artifacts: 见本 job 的 artifacts/ 与失败 shard 的上传件" >> "$GITHUB_STEP_SUMMARY"
      - name: Notify on failure
        if: failure()
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.{{NOTIFY_SECRET}} }}
        run: |
          # Security: secret 经 env: 注入（DATA，不进脚本正文）
          case "${SLACK_WEBHOOK_URL:-}" in
            https://*) ;;
            *) echo "未配置 {{NOTIFY_SECRET}}：跳过失败通知（见 docs/ci-secrets-checklist.md）"; exit 0 ;;
          esac
          RUN_URL="$GITHUB_SERVER_URL/$GITHUB_REPOSITORY/actions/runs/$GITHUB_RUN_ID"
          printf '{"text":"%s 失败：%s"}\n' "$GITHUB_WORKFLOW" "$RUN_URL" \
            | curl -sS -X POST -H "Content-type: application/json" --data-binary @- "$SLACK_WEBHOOK_URL"

# ============================================================================
# 注入防护（逐字复制面：渲染不得删改）
# 把本流水线扩展为可复用工作流（on: workflow_call）/ 手动触发 / 复合动作时：
#   · `${{ inputs.* }}` 与整个 `${{ github.event.* }}` 命名空间一律按不可信处理；
#   · 必须经 `env:` 中转，并在 `run:` 里以双引号 `"$ENV_VAR"` 引用；严禁直接插值；
#   · inputs 只能是 DATA，不能是 COMMAND——不接受 install-command / test-command 这类
#     命令形状的输入：即使经 env:，`run: $CMD` 仍是命令注入。
# check 会对本文件做脚本块扫描（违规码 UNSAFE_INJECTION），注释里的示例不算违规。
# ✅ SAFE —— 输入作为参数进入固定命令
#   - name: Run selected tests
#     env:
#       TEST_GREP: ${{ inputs.test-grep }}
#     run: |
#       # Security: inputs passed through env: to prevent script injection
#       npx playwright test --grep "$TEST_GREP"
# ❌ NEVER —— 直接表达式注入 / 把输入当命令执行
#   - run: npx playwright test --grep "${{ inputs.test-grep }}"
#   - env: { CMD: ${{ inputs.test-command }} }
#     run: $CMD
# 安全上下文（无需 env: 中转）：${{ steps.*.outputs.* }} / ${{ matrix.* }} / ${{ runner.os }}
#   / ${{ github.sha }} / ${{ github.ref }} / ${{ secrets.* }} / ${{ env.* }}
# ============================================================================
