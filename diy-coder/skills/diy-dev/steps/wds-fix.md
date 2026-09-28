# Step — 回修环（[F] Bugfixing）· 一次一条缺陷

Progress: `[1 复现] → [2 根因] → [3 最小修] → [4 验证与回归] → 回门/收尾`

**Read (input):** 缺陷来源之一——`diy-review` 的 WDS 审查结论（会话内审查报告、无 YAML 载体）里路由为「小修」的条目 / 用户在呈报里的「问题」分支 / 本页浏览器门逐条核对里的未过项；该页 `design.yaml` 记录（判据唯一真源）；`{output_dir}/prototypes/<页 id>.html` 或 `implementation` 基线现值。
**Write (output):** `src` 里的修复改动（最小改动面）；会话内的复现记录 / 根因 / 回归面。**本文件不写任何 YAML**——页状态由 `diy-review` 的回修边（`待验收 → 结构稿中`，经 `transition`）落定，修完仍走 `./wds-finalize.md`。

源侧 `steps-f/`（5 文件 / 671 行）的三条核心原则全保，五步压成四步——**一次只修一条**，不夹带重构。

## 第 1 步 —— 先复现（源硬规矩：`ALWAYS reproduce the bug before investigating`）

1. 用最小步骤把缺陷**再跑出来**：现象 / 触发条件 / 期望 vs 实际；
2. **修不了复现的缺陷不修**——不能复现的修复是猜测；复现不出来 → 停下如实上报（补信息：截图 / 控制台 / 步骤），不硬改。

## 第 2 步 —— 定位根因（源 `ALWAYS identify root cause before writing a fix`）

1. 沿调用链读代码，读到**根因**再动手——**绝不修症状**（症状修完会换个地方再冒出来）；
2. 根因在**规格**（判据本身不成立 / 缺态）→ 停下，路由 `diy-design`（`design.yaml` 写权不在本技能）；根因在页面树（缺页 / 偏题）→ 路由 `diy-wds-scenarios`。

## 第 3 步 —— 最小修（源 `Minimal fix` + 硬禁令）

1. 只改根因所需的最小面；**绝不在同一次修复里重构周边代码**（源 `NEVER refactor surrounding code in the same fix`）；
2. 仍守零重写采用：不动页面结构与样式基线，样式只取 token；`# trace:` 行随改动单元补；
3. 发现别的缺陷 → 另行记录（另起一条），**不夹带**（一次一条，与演进轮的「一次一条改进」同理）。

## 第 4 步 —— 验证与回归检查（源 `Regression check`）

1. **原缺陷**：第 1 步的复现步骤重跑，实际 == 期望；
2. **回归面**：改动触及的共享件（token / 组件 / 路由）与相邻页裸跑一遍，确认只发生预期改动（改既有功能时与第 1 步前捕的基线对比）；
3. **重走浏览器门**（`./wds-self-verify.md`）——门过才可再呈；未过继续自环，页状态不变；
4. 修完 → `./wds-finalize.md` 走状态写回（审查打回的页此时在 `结构稿中`，写回 `待验收`）与交棒。

## 裁撤与归位（源侧台账）

| 源侧 | 处置 |
| --- | --- |
| `steps-f/step-05-document.md` 的修复文档与故事文件 `Problem / Root cause / Solution / Code change / Learned` 记录 | **裁**——diy 侧不建第二份源：复现 / 根因 / 回归面留会话回报；产物真源 = `design.yaml` + `src` |
| 源侧 `## Progress` 章节与设计日志报点 | **裁**——全流水线缺陷（5 技能 11 处）；进度真源 = `pages[].status` |
| 源侧「重跑 [T] 验收测试」的建议 | **归位**为 `./wds-accept.md`（场景级全量验收；本节只跑本次修复的判据与回归面） |

## 收尾与路由

修完验证通过 → `./wds-finalize.md`。本文件到此结束，不再回头。
