# Step 2 — 被测特性识别与 AC 绑定

Progress: `探测 → [目标] → 生成 API → 生成 E2E → 记录`

**Read (input):** 第 1 步确认的框架；`{output_dir}/stories.yaml`（按 ID 定位目标故事/AC）；实现面。
**Write (output):** 对话内的一份目标清单——特性、入口、绑定的 AC。本步不写产物。

## 识别被测特性

三条路径，按此优先序（BMAD step-1「Identify Features」）：

1. **点名** —— 用户点了某个特性、组件、端点或文件。就以此为准，不擅自扩大范围。
2. **目录扫描** —— 用户给了目录（如 `src/components/`）。读该面，枚举其中可测的特性。
3. **自动发现** —— 什么都没点。从已实现的面发现候选：API 测试取路由/处理器，E2E 取有用户可见流程的页面/组件。把候选摆出来，由用户确认要覆盖的子集。

结果以短编号列表给出：`特性 — 入口（路径或路由）— 拟走生成层（api | e2e）`。`api | e2e` 是本技能的**生成层轴**，只决定走第 3 步还是第 4 步、以及收尾摘要的分层计数，**不写进 `test-plan.yaml` 的 `type` 字段**（`type` 恒为 `端到端`）；层信息落用例 `title`。既无用户可见界面、也无 API 边界的特性不在范围内——明说，别为它编一条用例。

## 绑到故事 + AC——只引用，不复制

对每个目标，在 `stories.yaml` 里定位该特性所实现的故事与验收准则：

- 按 ID 读——在 AC 文本里搜该特性的行为；绝不把 AC 散文粘进用例标题或 `steps`。用例引用 `AC-x.y`；它的 `steps` 写具体验证动作，不是 AC 的复述。
- 追加的 TC 承载的是**那条绑定的 AC**——绝不发明 AC，也绝不写范围。

**无 AC 可绑** → 该特性要么没被规划、要么早于 AC。绝不静默挂到最像的那条 AC 上。**交互态**当场问用户裁定：绑到某条已存在的 AC、丢弃、还是把缺口退回 diy-epics-stories——拿到裁定即继续。**headless 或未获裁定** → 经 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" defer-add --entry '{"skill": "diy-e2e-tests", "action": "裁定未绑定 AC 的候选特性 <feature>：绑定到现有 AC / 丢弃 / 退回 diy-epics-stories", "reason": "仅人工可做"}' --project-root "{project-root}" --json`（resolved 实例时附 `--instance <name>`）入队，收尾摘要必列该 `DA-###`。绑定未决期间不得追加用例——`record` 会把整批 `ac` 对 `stories.yaml` 解析，有一条悬空即整批拒绝。写权归命令本体（单写者 ＝ `diyc.py defer-add`），本技能只调用。

## 只覆盖已在场的东西

目标锁定现状实现。用户期待、但尚未实现的特性不是这里的测试目标——那是故事范围问题；记一行、跳过。本技能绝不写实现代码。

## 播报与下一步

读全 `./03-generate-api.md` 并照做。
