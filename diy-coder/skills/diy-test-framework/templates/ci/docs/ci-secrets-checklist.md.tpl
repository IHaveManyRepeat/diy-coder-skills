# placeholders: CI_PLATFORM CI_FILE CI_PLATFORM_SECRETS_UI NOTIFY_SECRET BASE_URL API_URL
# CI 秘密清单（由 diy-test-framework 渲染；要改请改技能内模板，不要改本文件）

平台：**{{CI_PLATFORM}}**。**本技能不代配秘密**：下列条目是人工处置项——配置入口
{{CI_PLATFORM_SECRETS_UI}}，配完在 `{output_dir}/test-framework.yaml` 的 `open_questions` 勾掉。
流水线文件 `{{CI_FILE}}` 里只出现**变量名**，不出现值。

## 必配（缺了流水线仍能跑，但功能降级）

| 变量名 | 用途 | 缺省行为 | 状态 |
| --- | --- | --- | --- |
| `{{NOTIFY_SECRET}}` | 失败通知（Slack 传入 webhook 地址 / 邮件网关地址） | 通知步骤打印一行提示并跳过 | ☐ |
| `BASE_URL` | 被测环境地址（{{BASE_URL}}） | 用流水线内默认值 | ☐ |
| `API_URL` | 接口地址（{{API_URL}}） | 用流水线内默认值 | ☐ |

## 配置纪律

- **只配进平台秘密库**（{{CI_PLATFORM_SECRETS_UI}}），不写进流水线文件、不写进仓库里的任何文件。
- 秘密名与流水线里的引用名**逐字一致**（上面表格左列就是引用名）。
- 通知用的 webhook 地址按可轮换对待：泄露即换，换完同步秘密库。
- 秘密一旦进过日志或产物就等于泄露：产物保留 30 天，排查完记得清理。
- 需要登录态（账号 / OAuth token）的用例：账号归测试环境自备，**不要**把凭据写进测试代码或夹具。

## 与台账的关系

配完秘密后重跑本技能的 `check`：秘密名出现在生成物里、但不属任何 YAML 字段，因此台账只记
`open_questions` 一行结论（如「{{NOTIFY_SECRET}} 已配 / 待配」），不记值。
