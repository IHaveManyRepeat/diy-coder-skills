# placeholders: RUNTIME_SETUP_CMD INSTALL_CMD LINT_CMD TEST_CMD P0_GATE P1_GATE CACHE_PATH CACHE_KEY CACHE_RESTORE_KEYS NOTIFY_SECRET
# Azure DevOps 测试流水线（后端面：无浏览器安装步骤；diy-test-framework 渲染）
# 质量门（事实源 = test-framework.yaml 的 ci.gates）：P0 覆盖 {{P0_GATE}} / P1 覆盖 {{P1_GATE}}
# 分片：matrix 注入 SHARD_INDEX
# 缓存：Cache@2 依赖一份，键含锁文件哈希，restoreKeys 为回退前缀
# 失败通知：变量组里的秘密变量名 = {{NOTIFY_SECRET}}（未配置则跳过，见 docs/ci-secrets-checklist.md）
trigger:
  branches:
    include: [main, develop]

pr:
  branches:
    include: [main, develop]

schedules:
  - cron: "0 2 * * 0"
    displayName: Weekly burn-in
    branches:
      include: [main]
    always: true

variables:
  P0_GATE: "{{P0_GATE}}"
  P1_GATE: "{{P1_GATE}}"

stages:
  - stage: Lint
    displayName: "Lint"
    jobs:
      - job: LintJob
        pool: { vmImage: "ubuntu-latest" }
        timeoutInMinutes: 10
        steps:
          - script: {{RUNTIME_SETUP_CMD}}
            displayName: "Set up runtime"
          - task: Cache@2
            displayName: "Cache dependencies"
            inputs:
              key: {{CACHE_KEY}}
              path: {{CACHE_PATH}}
              restoreKeys: {{CACHE_RESTORE_KEYS}}
          - script: {{INSTALL_CMD}}
            displayName: "Install dependencies"
          - script: {{LINT_CMD}}
            displayName: "Run quality checks"

  - stage: Test
    displayName: "Test"
    dependsOn: Lint
    jobs:
      - job: TestShard
        pool: { vmImage: "ubuntu-latest" }
        timeoutInMinutes: 30
        strategy:
          matrix:
            Shard1: { SHARD_INDEX: 1 }
            Shard2: { SHARD_INDEX: 2 }
            Shard3: { SHARD_INDEX: 3 }
            Shard4: { SHARD_INDEX: 4 }
        steps:
          - script: {{RUNTIME_SETUP_CMD}}
            displayName: "Set up runtime"
          - task: Cache@2
            displayName: "Cache dependencies"
            inputs:
              key: {{CACHE_KEY}}
              path: {{CACHE_PATH}}
              restoreKeys: {{CACHE_RESTORE_KEYS}}
          - script: {{INSTALL_CMD}}
            displayName: "Install dependencies"
          - script: {{TEST_CMD}}
            displayName: "Run tests"
          - task: PublishTestResults@2
            condition: always()
            inputs:
              testResultsFormat: "JUnit"
              testResultsFiles: "test-results/**/*.xml"
              mergeTestResults: true
          - publish: test-results/
            artifact: test-results-$(SHARD_INDEX)
            condition: failed()

  - stage: BurnIn
    displayName: "Burn-In (flaky detection)"
    dependsOn: Test
    condition: succeededOrFailed()
    jobs:
      - job: BurnInJob
        pool: { vmImage: "ubuntu-latest" }
        timeoutInMinutes: 60
        steps:
          - script: {{RUNTIME_SETUP_CMD}}
            displayName: "Set up runtime"
          - task: Cache@2
            displayName: "Cache dependencies"
            inputs:
              key: {{CACHE_KEY}}
              path: {{CACHE_PATH}}
              restoreKeys: {{CACHE_RESTORE_KEYS}}
          - script: {{INSTALL_CMD}}
            displayName: "Install dependencies"
          - script: |
              for i in $(seq 1 10); do
                echo "burn-in iteration $i/10"
                {{TEST_CMD}} || exit 1
              done
            displayName: "Burn-in loop (10 iterations)"

  - stage: Report
    displayName: "Report"
    dependsOn: [Test, BurnIn]
    condition: always()
    jobs:
      - job: ReportJob
        pool: { vmImage: "ubuntu-latest" }
        steps:
          - download: current
            displayName: "Download all artifacts"
          - script: find "$(Pipeline.Workspace)" -maxdepth 2 -type d | sort
            displayName: "List collected artifacts"
          - script: echo "gates: P0 $(P0_GATE) / P1 $(P1_GATE)"
            displayName: "Quality gates"
          - script: |
              case "${SLACK_WEBHOOK_URL:-}" in
                https://*) ;;
                *) echo "未配置 {{NOTIFY_SECRET}}：跳过失败通知（见 docs/ci-secrets-checklist.md）"; exit 0 ;;
              esac
              RUN_URL="$(System.TeamFoundationCollectionUri)$(System.TeamProject)/_build/results?buildId=$(Build.BuildId)"
              printf '{"text":"%s 失败：%s"}\n' "$(Build.DefinitionName)" "$RUN_URL" \
                | curl -sS -X POST -H "Content-type: application/json" --data-binary @- "$SLACK_WEBHOOK_URL"
            displayName: "Notify on failure"
            condition: failed()
            env:
              SLACK_WEBHOOK_URL: $({{NOTIFY_SECRET}})

# ============================================================================
# 注入防护（逐字复制面：渲染不得删改）
# 把本流水线扩展为模板化流水线（parameters）/ 运行时参数（runtime parameters）/ 变量组时：
#   · `$(...)` 变量与 `${{ parameters.* }}` 一律按不可信处理；
#   · 必须经 env: 映射后以双引号 `"$ENV_VAR"` 引用，严禁直接拼进 script 命令行；
#   · 输入只能是 DATA，不能是 COMMAND——不接受 install-command / test-command 这类
#     命令形状的输入：`script: $(CMD)` 一律禁止。
# check 会对本文件做脚本块扫描（违规码 UNSAFE_INJECTION），注释里的示例不算违规。
# ✅ SAFE —— 输入作为参数进入固定命令
#   - script: python -m pytest -k "$TEST_FILTER"
#     env: { TEST_FILTER: $(TEST_FILTER_PARAM) }
# ❌ NEVER
#   - script: python -m pytest -k "${{ parameters.testFilter }}"
#   - script: $(INSTALL_COMMAND)
# ============================================================================
