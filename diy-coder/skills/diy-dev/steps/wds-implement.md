# Step — WDS 模式实现（[D] Development）· 本轮增量

Progress: `[1 载规格与基线] → [2 列工作项与定序] → [3 逐项实现] → [4 边做边跑] → 路由`

**Read (input):** `{output_dir}/design.yaml` 该页记录（`states[].signals` 是判据唯一真源、`prototype`、`implementation`）；该页 `implementation` 指向的框架页（实现基线）——纯 HTML 项目取 `prototype`；`{output_dir}/architecture.yaml` 的 `stack[]`（`kind: frontend` 条目的取值）；用户在本文件各步的回答。
**Write (output):** `src` 里的实现文件（在基线上叠加逻辑，**零重写**）；每个函数/方法上方一行 `# trace:` 注释；会话内的实现顺序清单。**本文件不写任何 YAML**——页状态一律经 `transition`（见 `./wds-finalize.md`）。

你是开发执行者，做**本轮增量**：把该页的规格实现出来并自验，**不是**演进轮（那是 `diy-wds-evolution`，一轮一条改进的完整 6 活动流水线）。

## 术语与写权边界

- 页 ID = `SC-<nn>.P<n>`（上游 `diy-wds-scenarios` 定死、`diy-design` 落 `pages[].id`）——**ID 是唯一引用键**，全程引 ID 不复制内容。
- `{output_dir}/wds-scenarios.yaml` 的 `design_status`（场景级）**一律只读**——推进写权在 `diy-design`（`[H]` 开工写 `building`、实现完毕写 `built`）；本技能不写该键，也不写 `design.yaml` 的 `states[]` / `tokens` 等任何键。
- 规格与实现冲突时**改实现不改规格**（要改规格 → 停下，路由 `diy-design`）。

## 第 1 步 —— 载规格与基线

1. **读规格**：该页 `states[].signals` 逐条列成判据清单（四态 `悬停` / `空态` / `加载中` / `错误` 是下限，页里可能还有 `离线` / `权限拒绝` 等追加态）；`name` / `route` 给页面标题与路径。
2. **定基线**：`implementation` 指向的框架页**就是**设计稿——实现是在它上面叠功能逻辑；纯 HTML 项目（`frontend_framework: html`）基线取 `prototype`。
3. **定框架**：`architecture.yaml` 的 `stack[]` 中 `kind: frontend` 条目的 `choice` 逐字取值；缺席且基线是框架页 → 以基线文件的实际框架为准，不猜。

## 第 2 步 —— 列工作项与定序

把该页拆成**可独立验证的单元**（页块 / 交互 / 单个态），每单元一行：「建什么 + 判据是 `states[].signals` 的哪几条」。按依赖定序（结构 → 交互 → 态）。按「读规格 → 识别工作项 → 排实现顺序」三步走；工作项清单**落会话**，不另建 story 文件（单一源 = `design.yaml`）。

## 第 3 步 —— 逐项实现

1. **最小实现**：只写把判据转真的最少代码（与主线规则 3 同源）；多出来的落回报记跟进，**绝不当静默的额外代码**。
2. **零重写采用**：不重写、不重新生成页面结构与样式；样式只取 `design.yaml` 的 token（CSS 变量注入）——无一次性 hex 色、无越档字号。
3. **跟随既有模式**（源核心原则 4）：文件结构 / 命名 / 状态管理 / 错误处理对齐基线代码的惯例；偏离规格（技术约束、发现的问题）先记明原因再往下走。
4. **每方法一行 trace**：`# trace: SC-01.P1 加载中`（C 族写 `// trace:`）——ID = 本页 + 本单元实现的 `states[].name`（可并列多个）；架构决策驱动形状时加 `D-x`（惯例放末尾）。解析宽容与主线同（顺序无关、可重复、自动去重）；主线模式写 `S-x AC-x.y TC-x.y.z`，WDS 模式写页 ID + 态名。

## 第 4 步 —— 边做边跑（源核心原则 3）

1. 每个单元做完就跑一遍（项目怎么跑就怎么来：构建 / 开发服务器 / 项目自带测试）；**不把测试攒到最后**。
2. token 单一源闸：`python "{project-root}/.claude/skills/diy-design/scripts/design.py" audit --design "{output_dir}/design.yaml" --src <impl>`——零 `one-off-color` / `one-off-font-size` 才算这一项过；`token_scope` 里的路径跳过、`--src` 取实际实现目录。
3. 红转不了绿 → **停下如实上报**（缺什么 / 试过什么 / 卡在哪），**绝不削弱判据来充绿**。

## 收尾与路由

实现完成、`audit` 零 `one-off-*` → 读 `./wds-self-verify.md` 走浏览器强制门。本文件到此结束，不再回头。
