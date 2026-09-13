# V1 第一轮验证报告：完整性与结构校验

- 生成时间：2026-09-13
- 执行：w-bmm-b（验证子代理）
- 校验对象：`docs/bmad-skill-map/raw/` 下 6 份模块 JSON + `catalog-baseline.json`
- 基准口径：W3 任务简报中的产物规范（顶层键、技能 11 键、dependencies 字段、steps 条目 `{name,descZh,optional}`、menu 条目 `{code,labelEn,labelZh,descZh}`）+ `scripts/assemble.py` 的实际契约
- 方法：全量 `json.load` 解析 → 逐字段断言 → 跨文件去重/覆盖比对 → 实跑 `scripts/assemble.py`

## 总体结论

**不通过。** 存在 1 个阻断级集成缺陷（合成脚本无法运行）、1 个覆盖缺口（3 个技能未提取）、1 组跨文件重复（2 个技能各被提取两次且内容不一致）。其余结构项（JSON 可解析、技能必备键、ID 越界、menu 条目形状）通过。

| 维度 | 结果 |
|------|------|
| 文件存在性 | 6/6 ✓ |
| JSON 可解析 | 6/6 ✓ |
| 技能必备 11 键 | 85/85 行完整 ✓ |
| 无 baseline 之外 ID | 0 条越界 ✓ |
| baseline 覆盖 | 83/86 ✗（3 缺失） |
| 跨文件 canonicalId 去重 | ✗（2 组重复且内容不同） |
| dependencies 形状统一 | ✗（dict / list 两套） |
| steps 条目键统一 | ✗（三套） |
| kind 枚举统一 | ✗（两套 + 1 条自由文本） |
| `assemble.py` 可运行 | ✗（line 91 AttributeError） |

## A. 完整性

### A1. 覆盖矩阵（baseline 共 86 个技能）

| 模块 | baseline 数 | 已提取 | 文件 |
|------|------------|--------|------|
| core | 12 | 12 | module-core.json |
| bmm | 32 | 29（15 + 16，含 2 重复） | module-bmm-a.json + module-bmm-b.json |
| bmb | 5 | 5 | module-bmb-automator.json |
| automator | 2 | 2 | module-bmb-automator.json |
| tea | 10 | 10 | module-tea-cis.json |
| cis | 10 | 10 | module-tea-cis.json |
| wds | 15 | 15 | module-wds.json |

去重后共提取 83 个唯一 ID。

### A2. 未覆盖的 3 个技能（均为 bmm，需裁决归属）

| canonicalId | baseline phase | 说明 |
|-------------|----------------|------|
| bmad-agent-architect | 无（agent 型无 phase） | 架构师 agent，两组任务书均未包含 |
| bmad-agent-dev | 无（agent 型无 phase） | 开发 agent，同上 |
| bmad-investigate | 空串（menuCode IN） | 调查工作流，同上 |

事实观察：bmm-a 文件 `coveredIds` 自报 15，与其 skills 数一致（自洽）；但它含 2 个 "anytime" 技能（见 A3），而缺少上述 3 个。若按「anitime 阶段归 B 组」的划分，A 组应为 13（去重后）+ 3 = 16，与任务书「16 技能」吻合。归属由 team-lead 裁决。

### A3. 跨文件重复（2 组，且两份内容不一致）

| canonicalId | module-bmm-a.json | module-bmm-b.json |
|-------------|-------------------|-------------------|
| bmad-document-project | steps 14 条，sourceFiles 7 个 | steps 16 条，sourceFiles 5 个 |
| bmad-agent-tech-writer | steps 8 条（键名 titleZh/summaryZh），sourceFiles 6 个 | steps null（agent 型判定），sourceFiles 6 个 |

两者在 baseline 中 phase 均为 `anytime`，按阶段规则应属 B 组，但两份条目内容有实质差异，去重时不能简单丢弃任一份，需合并或裁决保留版本。

## B. 结构一致性（跨文件漂移）

基准为 W3 简报口径。以下为各文件与基准的偏离，偏离项是否属可接受差异由 team-lead 判定。

### B1【阻断】dependencies 形状两套

- **dict 型**（符合基准）：module-core / module-bmm-b / module-tea-cis / module-wds
- **list 型**（每条 helpEntry 一项，字段含 code/phase/...）：module-bmm-a（15 行中 9 行非空）、module-bmb-automator（7 行中 6 行非空）

后果：`scripts/assemble.py:91` 排序时对 list 调用 `.get()`，实跑崩溃，`skill-map.json` 未生成：

```
File "scripts/assemble.py", line 91, in <lambda>
    lst.sort(key=lambda x: ((x.get("dependencies") or {}).get("phase") or "zz", x["canonicalId"]))
AttributeError: 'list' object has no attribute 'get'
```

### B2. steps 条目键三套

| 形状 | 文件 | 条目总数 |
|------|------|---------|
| `{name, descZh, optional}`（符合基准） | bmb-automator / bmm-b / tea-cis / wds | 58 + 111 + 77 + 113 |
| `{id, titleZh, summaryZh, optional, source}` | bmm-a | 110 |
| `{name, file, descZh}`（缺 optional） | core 仅 bmad-brainstorming | 8 |

bmm-a 的步骤名/描述以 `titleZh/summaryZh` 承载，内容非空（抽样可见），但键名与基准不一致。

### B3. kind 枚举两套 + 1 条自由文本

- `"agent 型" / "workflow 型" / "utility 型"`：core、tea-cis；其中 `bmad-party-mode` 为自由文本 `"utility 型（多 agent 编排）"`
- `"agent" / "workflow" / "utility"`（裸值）：bmm-a / bmm-b / bmb-automator / wds
- `null`：core 的 2 个 catalog-only 技能（bmad-customize、bmad-spec）

### B4. sourceFiles 路径约定两套

- 相对技能目录（如 `SKILL.md`、`steps/step-01-*.md`）：bmb-automator / bmm-b / tea-cis
- `.claude/skills/<canonicalId>/...` 前缀：bmm-a / core / wds

### B5. 顶层元数据键

| 文件 | module 载体 | group/groupScope | coveredIds | sourceRoot | 备注 |
|------|------------|------------------|-----------|------------|------|
| module-core.json | module | 缺 | 缺 | 缺 | 另有 catalogOnly？否，2 条 catalog-only 在 skills 内 |
| module-bmm-a.json | module | 有 | 有(15) | 有 | 另有 schemaNotes |
| module-bmm-b.json | module | 有 | 有(16) | 有 | |
| module-bmb-automator.json | modules/moduleNames | 缺 | 缺 | 有 | 跨 bmb+automator 两模块 |
| module-tea-cis.json | modules/moduleNames | 缺 | 缺 | 缺 | 跨 tea+cis 两模块，另有 moduleVersions |
| module-wds.json | module | 缺 | 缺 | 缺 | 另有 catalogOnlySkills(8)/idMappingSummary |

跨模块文件用 `modules` 承载属合理设计；`coveredIds` 仅 2 份文件具备，为与基准的主要口径差异。`catalogOnlySkills` 仅 wds 使用，assemble.py 已显式支持该键。

### B6. 通过项

- `menu` 条目键全部为 `{code, labelEn, labelZh, descZh}`（6 文件一致）
- 技能行必备 11 键（canonicalId/module/kind/evidenceLevel/sourceFiles/summaryZh/entry/menu/dependencies/steps/notes）85 行全覆盖
- 每文件 `skillCount` = skills 实际条数；`baselineSkillCount` = coveredIds 数（有该键者）
- 无 baseline 之外的多余 ID（extra = 0）

## C. 数据质量观察（不阻断，供 V2 抽样与合成注意）

1. module-bmm-a.json 的 `bmad-agent-tech-writer` 与 B 版重复且内容不同（A 版 steps 8 条，B 版 null）——见 A3。
2. module-core.json 仅 `bmad-brainstorming` 提供 steps（8 条）；其余 9 个 local-source 的 utility 型技能 steps 均为 null（core 提取者的约定：utility 型不展开步骤）。
3. module-wds.json 的 `wds-5-agentic-development` 为 workflow 型但 steps = null（该文件其余 14 个 workflow 均有 steps）。
4. core 2 个 catalog-only（bmad-customize、bmad-spec）steps = null，符合基准要求。
5. 各文件 discrepancies 数：core 0、bmb-automator 4、bmm-a 5、tea-cis 5、bmm-b 7、wds 8，合计 29 条（内容准确性属 V2 抽样范围）。

## D. 修复建议（优先级排序）

1. 【阻断】dependencies 形状二选一：将 bmm-a / bmb-automator 归一为 dict，或在 `assemble.py` 兼容 list（`deps[0].get("phase")` 之类）。不定则任务 7 无法合成。
2. 【阻断】补齐或裁决 3 个未覆盖技能（bmad-agent-architect / bmad-agent-dev / bmad-investigate）。
3. 【阻断】裁决 2 个重复技能的保留版本（建议按 phase 规则留 B 组版本，并合并 A 组多出的信息）。
4. 【建议】统一 steps 条目键（bmm-a 的 titleZh/summaryZh → name/descZh；core 补 optional 或明确 core 单列口径）。
5. 【建议】统一 kind 枚举为裸值 `agent/workflow/utility`，`bmad-party-mode` 的附加说明移入 notes。
6. 【建议】统一 sourceFiles 路径前缀约定，并在各文件顶层统一补充 `group/groupScope/coveredIds`。

## E. 逐文件统计

| 文件 | 技能数 | evidence | dependencies | steps 条目 | 顶层 coveredIds | 重复 | discrepancies |
|------|-------|----------|--------------|-----------|----------------|------|---------------|
| module-core.json | 12 | 10 local + 2 catalog-only | dict | 8 | 缺 | 0 | 0 |
| module-bmm-a.json | 15 | 15 local | list（9 非空） | 110 | 有(15) | 2 | 5 |
| module-bmm-b.json | 16 | 16 local | dict | 111 | 有(16) | 2 | 7 |
| module-bmb-automator.json | 7 | 7 local | list（6 非空） | 58 | 缺 | 0 | 4 |
| module-tea-cis.json | 20 | 20 local | dict | 77 | 缺 | 0 | 5 |
| module-wds.json | 15 | 15 local | dict | 113 | 缺 | 0 | 8 |

合计 85 行（83 唯一 ID）、477 条步骤、29 条 discrepancies。全部校验均为脚本化断言，修复后可直接复跑。

## 补记（发布后变更，2026-09-13）

> 本节为快照后的状态更新，不改动以上任何结论；与上文冲突处（如 E 表 module-bmm-b 的 16 条）以本节为准。

- D1（dependencies 形状阻断）已由 lead 在 `scripts/assemble.py` 增加 `normalize_deps()` 修复，line 91 traceback 已不复现；`module-bmm-b.json` 17 行 dependencies 均为 dict。
- D2/D3（3 缺口 + 2 重复）已在 `module-bmm-b.json` 按「`_bmad/bmm` 目录归属」口径解决：`bmad-document-project`、`bmad-agent-tech-writer`（manifestPath 在 1-analysis）移交 A 组；补入 `bmad-agent-architect`、`bmad-agent-dev`、`bmad-investigate`。该文件现为 17 条、全部 local-source、全部带 `skillDir`。
- 新增待裁决项（已裁决）：该文件既有 14 条源自主全局副本（含本机定制的版本），与 baseline 指认的项目副本存在实质差异（详见 `module-bmm-b.json` 的 discrepancies 第 3 条）。team-lead 裁决按项目副本重核：w-bmm-b-redo 重提取为 `raw/module-bmm-b-fixed.json`（13 条，`bmad-checkpoint-preview` 经核无需修改）与 `raw/module-bmm-missing.json`（3 条缺口技能），最终验收见 `review/ACCEPTANCE.md`。
