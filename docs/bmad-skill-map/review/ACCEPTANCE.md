# 验收总结：BMAD 官方技能全景图

- 完成日期：2026-09-13
- 交付物：`BMAD技能全景图.md`（主文档）、`index.html`（可视化）、`raw/skill-map.json`（机器可读数据）
- 范围：BMAD 官方 7 个模块全部技能（含可选分支三类：技能内菜单、技能间依赖编排、模块级可选路径）

## 数据流

```
_bmad/_config/{bmad-help.csv, skill-manifest.csv}
        │  build_baseline.py（解析 86 条 + 定位实体目录）
        ▼
raw/catalog-baseline.json
        │  6 个提取子 agent（按模块分工，读实体 SKILL.md / customize.toml / steps）
        ▼
raw/module-*.json  ──assemble.py（归一化 + 去重 + 覆盖核对）──▶ raw/skill-map.json
        │                                                          │
        └──check_sources.py（321 处引用 0 失配）                    ├─ render_md.py ─▶ BMAD技能全景图.md
        └──check_divergence.py（双副本差异扫描）                    └─ render_html.py ─▶ index.html
```

## 两轮验证结果

| 轮次 | 执行 | 方法 | 发现 |
| --- | --- | --- | --- |
| 第一轮 `verify-round1.md` | w-bmm-b | 完整性与结构校验 | 阻断 3 项：合并脚本崩溃、3 技能漏提、2 组跨文件重复；结构漂移 3 类 |
| 第二轮 `verify-round2.md` | w-verify2 | 抽样溯源（23 条逐条打开源文件核对） | 阻断 3 项：13 条技能取自错误副本、产物滞后、新增 3 条重复 |

### 修复记录

| 问题 | 来源 | 处理 | 验证 |
| --- | --- | --- | --- |
| 3 技能漏提（agent-architect / agent-dev / investigate） | 一轮 | 派 w-bmm-fix 补提 → `module-bmm-missing.json` | 覆盖 86/86 |
| 2 组跨文件重复（document-project / tech-writer） | 一轮 | assemble.py 按信息量择优去重 | 重复清单已收敛 |
| `dependencies` dict / list 双形态、`steps` 三套键名、`kind` 两套枚举 | 一轮 + 二轮 | assemble.py 三个 normalize 函数统一 | 产物单一形态 |
| **13 条 BMad Method 技能误读全局副本** | 二轮 | 派 w-bmm-b-redo 基于项目副本重提 → `module-bmm-b-fixed.json` | 13/13 sourceFiles 通过 |
| 重复记账标签写反 | 二轮 | assemble.py 先比较后 append，记录真实 kept/dropped | 标签与产物一致 |
| retrospective 漏步骤 0.5 | 二轮 | 重提时补入（13 步） | 已确认存在 |
| prfaq / retrospective 的可选路径未显式标注 | 二轮 | 重提时写入 notes 与 summaryZh | 已确认 |

## 关键发现：同名技能存在双副本且内容不一致

- 项目本地：`F:/code2/bmad-tool/.claude/skills/<id>/` → 结构为 `SKILL.md` + `customize.toml`（+ 自定义 steps）
- 全局：`~/.claude/skills/<id>/` → 结构为 `SKILL.md` + `workflow.md` + `steps-*/`；部分技能另有 `bmad-skill-manifest.yaml`
- 差异规模：86 条中 76 条文件清单不同（完整清单见 `raw/copy-divergence.json`）
- 影响：若按全局副本理解流程，会与本机实际生效版本不符（如 dev-story 的 TDD 步骤在项目副本中是嵌在 step 5 内，而非独立 5 步）
- 本次口径：**以项目本地副本为唯一真值**，已在主文档「数据口径」章节声明

## 命名登记错位（已如实标注在产物中）

- **32 条技能有实体但未登记进 `bmad-help.csv`**：其中 14 条属命名错位（如 `wds-1-project-brief` ↔ 目录行 `bmad-wds-project-brief`、`bmad-create-prd/edit-prd/validate-prd` ↔ 单条 `bmad-prd`），18 条属真未登记（5 个 bmm agent、6 个 cis agent、`bmad-tea`、`bmad-eval-runner` 等）
- **18 条目录条目无同名实体**：17 条语义可落位（功能被 `wds-N-*` 实体吸收），1 条纯残留 `bmad-wds-idun`
- 这些差异不阻断交付，但意味着「用户在 `/bmad-help` 里能看到的」与「实际装了什么」并不一致

## 交付物清单

| 文件 | 说明 |
| --- | --- |
| `BMAD技能全景图.md` | 主文档，按模块分章，每技能展开菜单/步骤/依赖 |
| `index.html` | 自包含可视化，模块分区 + 阶段流程图 + 技能明细 |
| `raw/skill-map.json` | 机器可读全量数据（91 条 = 86 基线 + 8 目录独有） |
| `raw/catalog-baseline.json` | 从官方双 CSV 构建的规范化基线 |
| `raw/copy-divergence.json` | 双副本差异清单 |
| `review/verify-round1.md` | 第一轮验证报告 |
| `review/verify-round2.md` | 第二轮验证报告 |
| `scripts/*.py` | 可复跑的构建、校验、渲染脚本 |

## 已知遗留（不影响交付）

1. 一轮报告指出的 core 8 条 utility 技能有真实执行流但 `steps=null`——本次按"读不到即留空"的纪律未补，如需完整可再跑一轮补充。
2. `bmad-wds-platform-requirements` 等 8 条目录独有条目无独立实体，其内容以「被吸收到哪个实体技能」的形式记录在 notes。
3. 双副本差异只做了文件清单比对，未做逐文件内容 diff——如需确认某条技能的版本先后，需单独比对。
