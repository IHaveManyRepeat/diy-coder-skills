---
name: diy-reverse
description: 'Reverse-engineer an EXTERNAL target (public website, or provided screenshots) into a first design.yaml — the committed design single source — plus one structural wireframe per page. Entry skill; the gate is "the external target is reachable". Own-codebase analysis is routed to diy-analyze. Writes design.yaml only at initial generation: if it already exists, refuse to overwrite and route to diy-design.'
# ↑ 中文：把**外部**目标（公开网站 / 截图）逆向成一份**初始 `design.yaml`**（设计单一源：方向 / 框架 / token 三段 / 逐页规格与四态）与逐页结构稿。**入口技能**——门禁 = 外部目标可访问；自有代码库改调 `diy-analyze`。**只在初始生成时写 `design.yaml`**：已存在则拒绝覆盖并路由 `diy-design`。
phase: anytime
precededBy: []
followedBy: []
required: false
line: any
outputs: design.yaml
---

# diy-reverse — 外部目标逆向（初始设计单源）

你是**逆向提取者**。输入：一个**外部**目标——公开网站（URL 轨）或已提供的截图（截图轨）。产出：`{output_dir}/design.yaml`（**既有 schema 的初始生成**）+ 逐页 `{output_dir}/prototypes/<页 id>.html` 结构稿。**边界。** 提取**模式与关系**，不搬像素与专有资产——纪律三条：**先观察后提取**（不看完不落笔）、**尊重知识产权**（不搬代码 / 字体 / 受版权内容）、**抓规则不抄像素**（收的是可复用的 token 与结构，不是逐像素值）。**自有代码库不归本技能**——那是 `diy-analyze` 的活（**路由**，不是技能间调用：diy 的「调用」先例只给零写面增强技能）。深挖某一页时调用 `diy-elicit`、要多视角审视时调用 `diy-party-mode`（零写面：结果并入本产物）。

## 激活时

1. 读 `{project-root}/diy-coder.yaml`；解析 `project.communication_language` / `project.document_output_language` / `paths.output_dir`。
   全程用 `communication_language` 对话；产物里的叙述文字用 `document_output_language` 写。机器锚点（ID、枚举值、文件名）逐字保留。
   缺省链：`paths.output_dir` 一律取 `diyc.py resolve` 回执（引擎缺省 `diy-output`，异常形状降级并 warning）；缺 `document_output_language` 落 `project.communication_language`；两者皆缺则跟随用户当前消息的语言，并在收尾一行说明。
   实例名只在本次激活参数出现 `--instance <name>` 时才传（无头侧入口 `runner.py --instance`；交互侧由用户在发起消息里给出同一旗标）；未传时回执的 `output_dir` 即主线平铺根。
   实例解析（FR-4.5/D-9）由工具脚本执行：运行 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json`，把回执里的 `output_dir` 当作本次运行唯一的读写根目录。
2. 续接检测：跑 `list` 看页面清单——**只回 `id` / `name` / `route` / `states` / `prototype` / `status` 六字段，不读正文**：
   `python "{project-root}/.claude/skills/diy-reverse/scripts/reverse.py" list --project-root "{project-root}" --output-dir "{output_dir}" --json`
   有记录 → **禁止重跑**：`design.yaml` 在场即已是别人的演进面，转第 3 步的写权分支；无记录 → 进第 3 步。
3. 门禁（零产出退出）：**外部目标可访问**——两轨（裁定 11：源侧 Internal 模式已裁）：**`url` 轨** = 一个 http(s) 公开目标；**`screenshots` 轨** = 已提供的截图文件（可读）。不可访问 / 截图不在场 → 一行说明并**零产出停止**；**目标是你自己的代码库 → 路由 `diy-analyze`**（`init` 会把门机械兜住：`TARGET_UNREACHABLE`）。
4. **写权边界**：`{output_dir}/design.yaml` **只在初始生成时写**（`init` 铸骨架）。已存在 → `init` 判 `OVERWRITE_REFUSED` 且**零写入**：把差异整理成 `revisions` **建议**在会话里呈出，**路由 `diy-design`**（生成权归本技能、演进权归 `diy-design` / `diy-dev`）。
5. 读取纪律：预载预算 = 本文件、上述配置与回执、`steps/` 下当前那一个文件——绝不批量预载；执行期读取以每个步骤开头的 `Read (input)` 行为唯一权威，**主文件不列举封闭清单**。
6. 读 `steps/01-define.md` 并照做（裸 `steps/*.md` 路径从本技能安装目录解析）。每步结尾点名下一个要读的文件。

## 工作流

全局步骤纪律：一次只加载一个 `steps/` 文件——绝不批量预载；除检查点外每步产出整块给出；`direction` / `tokens` / `pages[]` 与结构稿由你直接写（内容归会话），骨架与校验归引擎。

1. `steps/01-define.md` — 定目标与访问轨（**用户关卡**）→ 定提取目标 → 门禁与 `init` 铸骨架。
2. `steps/02-explore.md` — 广度侦察（两轨）→ 结构与交互 → 四张清单（页 / 组件 / 色板 / 字阶与间距）。
3. `steps/03-specs.md` — 页排序与六段规格 → 场景大纲 → 落 `pages[]`（四态 + 结构稿）。
4. `steps/04-extract-tokens.md` — token 三段（**重复值入 token**）→ 组件编目与映射（交接 `diy-wds-system`）→ 定稿、终门、渲染。

写回纪律：`init` 铸 `project.status: 草稿` 与既有 schema 的空壳；`project.name` / `created` 由 `init` 铸造后**不再由你改**；`pages[]` 的 `P-<n>` 由你**顺序铸号**；定稿 = `project.status: 已定稿`。

渲染是静默旁路——只写调用命令，不新增「打开浏览器 / 报告路径等待查看 / 阻塞等待」交互点：`python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"`（resolved 实例时附 `--instance <name>`）。

## 结构

`{output_dir}/design.yaml` —— **既有 schema，逐字沿用**（`diy-design/SKILL.md:52–78`；不新增字段、不自造 ID 形态）：

```yaml
project: {name, created, updated, status}   # status: 草稿|已定稿
direction: <string>       # 第一行一句话方向，换行后 2–3 行反模式禁令（每行以 "- " 起头）
frontend_framework: react|vue|svelte|…|html   # 逆向一个网站时写 html（纯 HTML 止于结构稿）
tokens:
  color: {bg, surface, text, text_muted, accent, accent_text}
  spacing: {unit, scale: [...]}
  typography: {family_base, family_heading, scale: [...]}
pages:
  - id: P-1                # 稳定 ID：**本技能顺序铸号**（P-1、P-2 …，不重编不复用）
    name / route
    states:                # 四态不许省，每态至少一条非色彩信号
      - {name: 悬停, signals: [图标, 动效]}      # 空态 / 加载中 / 错误 同构
    prototype: prototypes/P-1.html   # 结构稿：**你画的**线框，原型名与 id 同源
revisions: []              # {date, change, reason}
```

**「提取来源」无承载位**：既有 schema 没有来源字段（`source: {url, captured_at}` 之类），本批**不新增字段**——来源写进结构稿的头部注释 `<!-- 提取来源: <url> / <截图名> · 采集日 YYYY-MM-DD -->` 与会话呈出，**并登记为 C·3 的 schema 扩充项**（`diy.py` 不动）。

## 规则

1. **写范围**：只写 `{output_dir}/design.yaml`（**仅初始生成**）与 `{output_dir}/prototypes/<页 id>.html`；其余一律只读——不碰 `prd.yaml` / `wds-*.yaml` / `stories.yaml`，不搬目标站点的代码与资产进仓。
2. **检查点四选项**（每步产出后，六拍不得省）：① 生成本步产出 → ② 落盘 → ③ 显示检查点分隔 → ④ 呈出本步产出 → ⑤ 出四选项 → ⑥ 等响应。
3. **选项落点**：`[a]` → 调 `diy-elicit`；`[p]` → 调 `diy-party-mode`（两者**零写面**，返回后回第 ② 拍重落盘）；`[c]` → 进下一步；`[y]` → 后续跳过 ⑤⑥，**②③④ 照旧**。无头 / 非交互 = 全程 `[y]`（摘要一行明示），**不入 `deferred-actions` 队列**。
4. **写权边界（裁定 13）**：`design.yaml` 的初始生成权归本技能、演进权归 `diy-design` / `diy-dev`。已存在即**不覆盖**——`revisions` 建议 + 路由 `diy-design`；本技能**不改** `design.py`、不扩 schema。
5. **ID 形态**：页 ID 沿用既有 schema 的 `P-<n>`（**不得用 WDS 线的记录 ID 形态**），顺序铸号、不重编不复用；结构稿名与 `id` 同源（引擎核 `SET_MISMATCH`）。
6. **「不抄像素」判据（复用 `one-off-*` 口径）**：候选值先过 `reverse.py tokens --values …`——**同一值出现 ≥2 次才可作 token，单次值一律不收**（它与 `design.py audit` 的 `one-off-color` / `one-off-font-size` 同判据）。**计数可机械、分组与命名是人工判定**；`status: 待核实` 的推断不写成事实。
7. **终门（机械）**：先落 `project.status: 已定稿`，再跑 `python "{project-root}/.claude/skills/diy-reverse/scripts/reverse.py" check --final --project-root "{project-root}" --output-dir "{output_dir}" --json`——`exit 0` 是唯一放行；零 `[假设]`。随后**交叉核对一次既有设计域引擎**（schema 与易用性权威，只读）：`design.py validate` 与 `design.py check` 都必须 `exit 0`；两者不一致时以它为准修产物。渲染与收尾都等 `exit 0`。
8. **违规码**：复用冻结集（`MISSING_FILE` / `UNPARSABLE_YAML` / `EMPTY_FIELD` / `ENUM_INVALID` / `DUPLICATE_ID` / `UNKNOWN_ID` / `SET_MISMATCH` / `STATUS_MISMATCH` / `ASSUMPTION_PRESENT`）+ **本技能新增两码**（`init` 的门与写权边界，docstring 已标注）：`TARGET_UNREACHABLE`（外部目标不可访问）、`OVERWRITE_REFUSED`（既有 `design.yaml` 拒绝覆盖）。warning 码 `ONE_OFF_VALUE`（单次值）不属违规集。
9. **无 `--previous` 轮**：本产物是**初始生成 + 只增**，无 ID 集合收缩面；改既有内容往 `revisions` 追加（date / change / reason）。副作用面：读外部目标属**只读外访**（联网不可用即中止，不排队不阻塞）；除 `design.yaml` / `prototypes/` 与静默渲染外无任何写面。
10. **边界（对方侧随 C·3 补）**：vs `diy-analyze`——它扫**你自己的**代码库产 `analysis.yaml`（现状事实），本技能扫**外部**目标产设计契约；自有代码库路由它。vs `diy-design`——**生成权与演进权分离**（规则 4）。vs `diy-openapi` / `diy-project-context`——同属「既有物 → 体系产物」的入口先例，但产物域不同（接口契约 / AI 语境档）。vs `diy-wds-system`——组件编目与 token→组件映射**不在本产物**（schema 无 `components[]`），会话内呈出后由它承接。vs `diy-elicit` / `diy-party-mode`——不是竞争是调用（见规则 3）。

- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；不复述上游已写的信息（引用 ID）；不写没有信息量的套话。

- **写作纪律。** 主字段 = 大白话主句；数字/枚举内联；机器语法（命令/旗标/路径）进括号；机器锚点逐字保留（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 `diy-design` 的 detect 启发式。schema 若定义 `plain`：一行写清该条目为什么存在，绝不写是什么（转述会漂移）；只写难懂的条目。若定义 `detail`：过程叙述——结论留在主字段。
