# diy 技能审查底单

> 快照 2026-10-03，基数 49。事实源：各 SKILL.md frontmatter + `diy-help/registry.yaml`（守卫：test_help_registry.py）；本文档为派生快照，链序变更后作废重生成。
> 审 = 提示词审查，用 = 实际使用，勾选直接改本文件。★ = required 硬门禁（9）。[] = 链上可选节点。

## 链序

```
主线  prd ★ → architecture ★ → [openapi] → [design·双源] → epics-stories ★ → test-design ★
      → sprint ★ → create-story → test-author → dev → review → retrospective
分叉  dev → e2e-tests ｜ review → augment → test-review → test-gate
      ｜ sprint → build-loop（链后执行面）｜ epics-stories → readiness-check ★（链外挂）
WDS   wds-brief ★ → wds-trigger ★ → wds-scenarios ★ → [system] → [assets] → [evolution]
      → dev（WDS 模式）→ review（WDS 路径）
```

双模式三技：design（双源）/ dev / review——审查与使用各跑两遍。

## A 主线（22）

| 审 | 用 | 技能 | 行 | 依赖 |
| --- | --- | --- | --- | --- |
| ☐ | ☐ | diy-prd ★ | 121 | — |
| ☐ | ☐ | diy-architecture ★ | 94 | prd |
| ☐ | ☐ | diy-openapi | 77 | architecture |
| ☐ | ☐ | diy-design（双源） | 106 | prd |
| ☐ | ☐ | diy-epics-stories ★ | 99 | architecture |
| ☐ | ☐ | diy-readiness-check ★ | 79 | epics-stories |
| ☐ | ☐ | diy-test-design ★ | 102 | epics-stories |
| ☐ | ☐ | diy-test-framework | 87 | — |
| ☐ | ☐ | diy-sprint ★ | 97 | test-design |
| ☐ | ☐ | diy-create-story | 92 | sprint |
| ☐ | ☐ | diy-test-author | 59 | test-design |
| ☐ | ☐ | diy-dev（双模式） | 88 | create-story, test-author |
| ☐ | ☐ | diy-review（双模式） | 79 | dev |
| ☐ | ☐ | diy-e2e-tests | 75 | dev |
| ☐ | ☐ | diy-augment | 79 | — |
| ☐ | ☐ | diy-test-review | 88 | augment |
| ☐ | ☐ | diy-test-gate | 92 | augment |
| ☐ | ☐ | diy-build-loop | 91 | sprint |
| ☐ | ☐ | diy-retrospective | 93 | review |
| ☐ | ☐ | diy-research | 80 | — |
| ☐ | ☐ | diy-product-brief | 89 | — |
| ☐ | ☐ | diy-prfaq | 81 | — |

## B WDS 线（6）

| 审 | 用 | 技能 | 行 | 依赖 |
| --- | --- | --- | --- | --- |
| ☐ | ☐ | diy-wds-brief ★ | 86 | — |
| ☐ | ☐ | diy-wds-trigger ★ | 89 | wds-brief |
| ☐ | ☐ | diy-wds-scenarios ★ | 88 | wds-trigger |
| ☐ | ☐ | diy-wds-system | 89 | wds-scenarios |
| ☐ | ☐ | diy-wds-assets | 89 | wds-scenarios |
| ☐ | ☐ | diy-wds-evolution | 88 | — |

## C 横向（21，独立可用）

| 审 | 用 | 技能 | 行 | 备注 |
| --- | --- | --- | --- | --- |
| ☐ | ☐ | diy-help | 79 | 导航核心，先审 |
| ☐ | ☐ | diy-viewer | 42 | C·14 将动聚合树 |
| ☐ | ☐ | diy-tools | 66 | |
| ☐ | ☐ | diy-project-context | 76 | |
| ☐ | ☐ | diy-eval-runner | 67 | |
| ☐ | ☐ | diy-teach-me-testing | 92 | |
| ☐ | ☐ | diy-brainstorm | 88 | |
| ☐ | ☐ | diy-elicit | 73 | 横切入口，被多技能挂载 |
| ☐ | ☐ | diy-party-mode | 65 | 横切入口，被多技能挂载 |
| ☐ | ☐ | diy-cis-method | 81 | |
| ☐ | ☐ | diy-spec | 84 | |
| ☐ | ☐ | diy-spec-scan | 90 | |
| ☐ | ☐ | diy-editorial-review | 87 | |
| ☐ | ☐ | diy-quick-dev | 92 | |
| ☐ | ☐ | diy-investigate | 93 | |
| ☐ | ☐ | diy-checkpoint-preview | 86 | |
| ☐ | ☐ | diy-correct-course | 90 | |
| ☐ | ☐ | diy-analyze | 78 | 独立入口，不入链 |
| ☐ | ☐ | diy-reverse | 83 | 独立入口，不入链 |
| ☐ | ☐ | diy-bmb-builder | 65 | |
| ☐ | ☐ | diy-bmb-module | 81 | |

## 顺序

help 先行 → 主线按链序（审查与使用同场跑一个真实项目）→ WDS 同法 → 横向插空。
