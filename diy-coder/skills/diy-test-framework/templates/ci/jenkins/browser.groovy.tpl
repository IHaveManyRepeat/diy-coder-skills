// placeholders: RUNTIME_SETUP_CMD INSTALL_CMD LINT_CMD TEST_CMD BROWSER_INSTALL P0_GATE P1_GATE REPORT_PATH CACHE_PATH CACHE_KEY BROWSER_CACHE_PATH NOTIFY_SECRET
// Jenkinsfile 测试流水线（diy-test-framework 渲染；要改请改技能内模板，不要改本文件）
// 质量门（事实源 = test-framework.yaml 的 ci.gates）：P0 覆盖 {{P0_GATE}} / P1 覆盖 {{P1_GATE}}
// 分片：failFast false 的四路并行分支，各自注入 SHARD；TEST_CMD 取值可带分片参数
// 缓存：Jenkins 无声明式缓存原语——依赖与浏览器缓存由 agent 工作区保留 + 工具自动安装覆盖；
//       约定的缓存键 = {{CACHE_KEY}}（锁文件哈希口径，与其他平台一致），依赖缓存路径 = {{CACHE_PATH}}，
//       浏览器缓存路径 = {{BROWSER_CACHE_PATH}}。换 agent 或清理工作区后首轮为冷缓存。
// 产物：post 段发布 JUnit 与失败产物；聚合面 = 构建页的 Test Result 与 Artifacts
// 失败通知：秘密名 = {{NOTIFY_SECRET}}（在 Manage Jenkins → Credentials 配成 Secret text 并注入
//       为同名环境变量；未配置则跳过，见 docs/ci-secrets-checklist.md）
pipeline {
    agent any

    environment {
        CI = 'true'
        P0_GATE = '{{P0_GATE}}'
        P1_GATE = '{{P1_GATE}}'
    }

    options {
        timeout(time: 60, unit: 'MINUTES')
        disableConcurrentBuilds()
    }

    stages {
        stage('Lint') {
            steps {
                sh '''
                    {{RUNTIME_SETUP_CMD}}
                    {{INSTALL_CMD}}
                    {{LINT_CMD}}
                '''
            }
        }
        stage('Test') {
            failFast false
            parallel {
                stage('shard-1') {
                    environment { SHARD = '1' }
                    steps {
                        sh '''
                            {{RUNTIME_SETUP_CMD}}
                            {{INSTALL_CMD}}
                            {{BROWSER_INSTALL}}
                            {{TEST_CMD}}
                        '''
                    }
                }
                stage('shard-2') {
                    environment { SHARD = '2' }
                    steps {
                        sh '''
                            {{RUNTIME_SETUP_CMD}}
                            {{INSTALL_CMD}}
                            {{BROWSER_INSTALL}}
                            {{TEST_CMD}}
                        '''
                    }
                }
                stage('shard-3') {
                    environment { SHARD = '3' }
                    steps {
                        sh '''
                            {{RUNTIME_SETUP_CMD}}
                            {{INSTALL_CMD}}
                            {{BROWSER_INSTALL}}
                            {{TEST_CMD}}
                        '''
                    }
                }
                stage('shard-4') {
                    environment { SHARD = '4' }
                    steps {
                        sh '''
                            {{RUNTIME_SETUP_CMD}}
                            {{INSTALL_CMD}}
                            {{BROWSER_INSTALL}}
                            {{TEST_CMD}}
                        '''
                    }
                }
            }
        }
        stage('Burn-In') {
            when { anyOf { branch 'PR-*'; triggeredBy 'TimerTrigger' } }
            steps {
                sh '''
                    {{RUNTIME_SETUP_CMD}}
                    {{INSTALL_CMD}}
                    {{BROWSER_INSTALL}}
                    for i in $(seq 1 10); do
                      echo "burn-in iteration $i/10"
                      {{TEST_CMD}} || exit 1
                    done
                '''
            }
        }
        stage('Report') {
            steps {
                echo "gates: P0 ${P0_GATE} / P1 ${P1_GATE}"
            }
        }
    }

    post {
        always {
            junit testResults: 'test-results/**/*.xml', allowEmptyResults: true
            archiveArtifacts artifacts: 'test-results/**,{{REPORT_PATH}}**', allowEmptyArchive: true
        }
        failure {
            sh '''
                case "${SLACK_WEBHOOK_URL:-}" in
                  https://*) ;;
                  *) echo "未配置 {{NOTIFY_SECRET}}：跳过失败通知（见 docs/ci-secrets-checklist.md）"; exit 0 ;;
                esac
                printf '{"text":"%s 失败：%s"}\n' "$JOB_NAME" "$BUILD_URL" \
                  | curl -sS -X POST -H "Content-type: application/json" --data-binary @- "$SLACK_WEBHOOK_URL"
            '''
        }
    }
}

// ============================================================================
// 注入防护（逐字复制面：渲染不得删改）
// 把本流水线扩展为参数化构建（parameters）/ 共享库 / 多分支触发时：
//   · 构建参数（params.* / env.*）一律按不可信处理，严禁拼进 sh 命令名或脚本路径；
//   · 必须作为参数传入固定命令并加双引号，或经 environment 块中转；
//   · 输入只能是 DATA，不能是 COMMAND——不接受 install-command / test-command 这类
//     命令形状的参数：`sh "$CMD"` / `eval` 一律禁止。
// check 会对本文件做脚本块扫描（违规码 UNSAFE_INJECTION），注释里的示例不算违规。
// ✅ SAFE —— 参数作为参数进入固定命令
//   sh 'npx playwright test --grep "$TEST_GREP"'
// ❌ NEVER
//   sh 'npx playwright test --grep "' + params.TEST_GREP + '"'
//   sh "${params.INSTALL_COMMAND}"
// ============================================================================
