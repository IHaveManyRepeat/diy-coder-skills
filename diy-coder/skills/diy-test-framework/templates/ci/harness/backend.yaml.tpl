# placeholders: RUNTIME_SETUP_CMD INSTALL_CMD LINT_CMD TEST_CMD P0_GATE P1_GATE CACHE_PATH CACHE_KEY NOTIFY_SECRET
# Harness CI 测试流水线（后端面：无浏览器安装步骤；diy-test-framework 渲染）
# 质量门（事实源 = test-framework.yaml 的 ci.gates）：P0 覆盖 {{P0_GATE}} / P1 覆盖 {{P1_GATE}}
# 分片：repeat.strategy 并行四份，SHARD 由 <+strategy.iteration> 给出
# 缓存：Cache Intelligence（stage.spec.caching）——依赖缓存路径须落在 /harness 下
# 失败通知：秘密名 = {{NOTIFY_SECRET}}（Harness 秘密，经 <+secrets.getValue> 注入；未配置则跳过）
pipeline:
  name: Test Pipeline
  identifier: test_pipeline
  stages:
    - stage:
        name: Lint
        identifier: lint
        type: CI
        spec:
          cloneCodebase: true
          caching:
            enabled: true
            key: {{CACHE_KEY}}
            paths:
              - {{CACHE_PATH}}
          execution:
            steps:
              - step:
                  type: Run
                  name: Set up runtime
                  identifier: runtime
                  spec:
                    shell: Sh
                    command: {{RUNTIME_SETUP_CMD}}
              - step:
                  type: Run
                  name: Install dependencies
                  identifier: install
                  spec:
                    shell: Sh
                    command: {{INSTALL_CMD}}
              - step:
                  type: Run
                  name: Run quality checks
                  identifier: lint
                  spec:
                    shell: Sh
                    command: {{LINT_CMD}}
    - stage:
        name: Test
        identifier: test
        type: CI
        spec:
          cloneCodebase: true
          caching:
            enabled: true
            key: {{CACHE_KEY}}
            paths:
              - {{CACHE_PATH}}
          execution:
            steps:
              - step:
                  type: Run
                  name: Test shard
                  identifier: test_shard
                  spec:
                    shell: Sh
                    envVariables:
                      SHARD: <+strategy.iteration>
                    command: |
                      {{RUNTIME_SETUP_CMD}}
                      {{INSTALL_CMD}}
                      {{TEST_CMD}}
              - step:
                  type: Run
                  name: Upload artifacts on failure
                  identifier: artifacts
                  spec:
                    shell: Sh
                    command: echo "test-results/ 上传为失败产物（retention 30 天）"
          rollbackSteps: []
          repeat:
            strategy: Parallel
            items:
              - 1
              - 2
              - 3
              - 4
    - stage:
        name: BurnIn
        identifier: burn_in
        type: CI
        spec:
          cloneCodebase: true
          caching:
            enabled: true
            key: {{CACHE_KEY}}
            paths:
              - {{CACHE_PATH}}
          execution:
            steps:
              - step:
                  type: Run
                  name: Burn-in loop (10 iterations)
                  identifier: burn_in
                  spec:
                    shell: Sh
                    command: |
                      {{RUNTIME_SETUP_CMD}}
                      {{INSTALL_CMD}}
                      for i in $(seq 1 10); do
                        echo "burn-in iteration $i/10"
                        {{TEST_CMD}} || exit 1
                      done
    - stage:
        name: Report
        identifier: report
        type: CI
        spec:
          cloneCodebase: true
          execution:
            steps:
              - step:
                  type: Run
                  name: Quality gates
                  identifier: gates
                  spec:
                    shell: Sh
                    command: echo "gates: P0 {{P0_GATE}} / P1 {{P1_GATE}}"
    - stage:
        name: Notify on failure
        identifier: notify_on_failure
        type: CI
        when:
          pipelineStatus: Failure
        spec:
          cloneCodebase: false
          execution:
            steps:
              - step:
                  type: Run
                  name: Notify on failure
                  identifier: notify
                  spec:
                    shell: Sh
                    envVariables:
                      SLACK_WEBHOOK_URL: <+secrets.getValue("{{NOTIFY_SECRET}}")>
                    command: |
                      case "${SLACK_WEBHOOK_URL:-}" in
                        https://*) ;;
                        *) echo "未配置 {{NOTIFY_SECRET}}：跳过失败通知（见 docs/ci-secrets-checklist.md）"; exit 0 ;;
                      esac
                      printf '{"text":"%s 失败：见流水线执行页"}\n' "<+pipeline.name>" \
                        | curl -sS -X POST -H "Content-type: application/json" --data-binary @- "$SLACK_WEBHOOK_URL"

# ============================================================================
# 注入防护（逐字复制面：渲染不得删改）
# 把本流水线扩展为带输入（pipeline inputs / runtime inputs）/ 触发式流水线时：
#   · `<+input>`、`<+trigger.*>`、`<+pipeline.variables.*>` 一律按不可信处理；
#   · 必须经 envVariables 映射后以双引号 `"$ENV_VAR"` 引用，严禁直接插值进 command；
#   · 输入只能是 DATA，不能是 COMMAND——不接受 install-command / test-command 这类
#     命令形状的输入：`command: <+input>.cmd` 一律禁止。
# check 会对本文件做脚本块扫描（违规码 UNSAFE_INJECTION），注释里的示例不算违规。
# ✅ SAFE —— 输入作为参数进入固定命令
#   command: python -m pytest -k "$TEST_FILTER"
#   envVariables: { TEST_FILTER: <+input>.testFilter }
# ❌ NEVER
#   command: <+input>.installCommand
# ============================================================================
