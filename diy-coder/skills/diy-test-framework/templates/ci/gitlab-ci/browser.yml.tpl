# placeholders: RUNTIME_SETUP_CMD INSTALL_CMD LINT_CMD TEST_CMD BROWSER_INSTALL P0_GATE P1_GATE REPORT_PATH CACHE_LOCKFILE CACHE_PATH BROWSER_CACHE_LOCKFILE BROWSER_CACHE_PATH NOTIFY_SECRET
# GitLab CI 测试流水线（diy-test-framework 渲染；要改请改技能内模板，不要改本文件）
# 质量门（事实源 = test-framework.yaml 的 ci.gates）：P0 覆盖 {{P0_GATE}} / P1 覆盖 {{P1_GATE}}
# 分片：test 作业 parallel: 4，分片序号用内置变量 $CI_NODE_INDEX（TEST_CMD 取值可带分片参数，
#       如 `npx playwright test --shard=$CI_NODE_INDEX/4`）
# 缓存：依赖与浏览器各一条 cache 条目（至多四条）；key.files 由锁文件内容派生
# 失败通知：秘密变量名 = {{NOTIFY_SECRET}}（在 Settings → CI/CD → Variables 配置；未配置则跳过）
stages: [lint, test, burn-in, report]

variables:
  GIT_DEPTH: 0
  P0_GATE: "{{P0_GATE}}"
  P1_GATE: "{{P1_GATE}}"

lint:
  stage: lint
  cache:
    key:
      files: [{{CACHE_LOCKFILE}}]
    paths: [{{CACHE_PATH}}]
  script:
    - {{RUNTIME_SETUP_CMD}}
    - {{INSTALL_CMD}}
    - {{LINT_CMD}}
  timeout: 10 minutes

test:
  stage: test
  parallel: 4
  needs: [lint]
  cache:
    - key:
        files: [{{CACHE_LOCKFILE}}]
      paths: [{{CACHE_PATH}}]
    - key:
        files: [{{BROWSER_CACHE_LOCKFILE}}]
      paths: [{{BROWSER_CACHE_PATH}}]
  script:
    - {{RUNTIME_SETUP_CMD}}
    - {{INSTALL_CMD}}
    - {{BROWSER_INSTALL}}
    - {{TEST_CMD}}
  artifacts:
    when: on_failure
    paths: [test-results/, {{REPORT_PATH}}]
    expire_in: 30 days
  timeout: 30 minutes

burn-in:
  stage: burn-in
  needs: [test]
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
    - if: '$CI_PIPELINE_SOURCE == "schedule"'
  cache:
    - key:
        files: [{{CACHE_LOCKFILE}}]
      paths: [{{CACHE_PATH}}]
    - key:
        files: [{{BROWSER_CACHE_LOCKFILE}}]
      paths: [{{BROWSER_CACHE_PATH}}]
  script:
    - {{RUNTIME_SETUP_CMD}}
    - {{INSTALL_CMD}}
    - {{BROWSER_INSTALL}}
    - |
      for i in $(seq 1 10); do
        echo "burn-in iteration $i/10"
        {{TEST_CMD}} || exit 1
      done
  artifacts:
    when: on_failure
    paths: [test-results/, {{REPORT_PATH}}]
    expire_in: 30 days
  timeout: 60 minutes

report:
  stage: report
  needs: [test, burn-in]
  when: always
  script:
    # needs 的 artifacts 由 GitLab 自动取回本作业工作区——聚合面就在这里
    - ls -R test-results/ 2>/dev/null || echo "无 test-results/ 产物（本次未失败）"
    - echo "gates: P0 $P0_GATE / P1 $P1_GATE"
    - echo "pipeline: $CI_PIPELINE_ID  branch: $CI_COMMIT_REF_NAME"

notify-failure:
  stage: report
  needs: [test, burn-in]
  when: on_failure
  script:
    - |
      if [ -z "${SLACK_WEBHOOK_URL:-}" ]; then
        echo "未配置 {{NOTIFY_SECRET}}：跳过失败通知（见 docs/ci-secrets-checklist.md）"
      else
        printf '{"text":"%s 失败：%s"}\n' "$CI_PROJECT_PATH" "$CI_PIPELINE_URL" \
          | curl -sS -X POST -H "Content-type: application/json" --data-binary @- "$SLACK_WEBHOOK_URL"
      fi

# ============================================================================
# 注入防护（逐字复制面：渲染不得删改）
# 把本流水线扩展为 downstream / 手动触发 / 可复用流水线时：
#   · 外部输入（trigger 变量、pipeline 变量、MR 标题等）一律按不可信处理；
#   · 必须经 `variables:` 或 `script` 内的双引号变量引用，严禁把输入拼进命令名或脚本路径；
#   · 输入只能是 DATA，不能是 COMMAND——不接受 install-command / test-command 这类
#     命令形状的输入：`eval $CMD` / `$CMD` 一律禁止。
# check 会对本文件做脚本块扫描（违规码 UNSAFE_INJECTION），注释里的示例不算违规。
# ✅ SAFE —— 输入作为参数进入固定命令
#   script:
#     - npx playwright test --grep "$TEST_GREP"
# ❌ NEVER
#   script:
#     - npx playwright test --grep "$CI_TRIGGER_GREP"
#     - eval "$INSTALL_CMD_FROM_INPUT"
# ============================================================================
