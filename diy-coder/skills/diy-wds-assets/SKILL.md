---
name: diy-wds-assets
description: 'WDS line fifth ring — the asset factory: turn page specs plus the design system into wireframes, page designs, UI elements, icons, images, motion, copy and presentation decks. No external service: prompts are exported for the user to generate elsewhere, output is HTML-first, artifacts land under assets/<activity>/. Use when the user says "generate the assets" / "make the wireframes" / "build the deck".'
# ↑ 中文：WDS 线第五环（资产工厂）——页面规格 + 设计系统 → 线框 / 页面稿 / UI 件 / 图标 / 图片 / 动效 / 文案 / 演示；**不接任何外部服务**（裁定 6），
# 唯一生成通道 = 导出提示词（用户在外生成后回填），产物 HTML 优先、落 `{output_dir}/assets/<活动>/`（裁定 12），YAML 只存路径引用；门禁 = 读 `wds-scenarios.yaml` 的 `project.status: 已定稿`（`wds-design-system.yaml` 可选读，缺则降级：不校验令牌一致性）。用户说 "generate the assets" / "make the wireframes" / "build the deck" 时触发。
phase: 2-wds-design
precededBy: [diy-wds-scenarios]
followedBy: []
required: false
line: wds
outputs: wds-assets.yaml
---

# diy-wds-assets — WDS 线第五环（资产工厂：8 活动 + 提示词导出）

你是**资产生产的主持人**（源 Freya 线的 `[GA]` 活动）。输入：一份已定稿的 `{output_dir}/wds-scenarios.yaml`（页面清单 = 每个资产的锚）与可选的 `{output_dir}/wds-design-system.yaml`（令牌一致性）。产出：`{output_dir}/wds-assets.yaml`——8 个活动的资产清单，每条带**可粘贴的提示词**与 `assets/<活动>/` 路径引用。边界：**本技能不接任何外部服务**（用户 2026-09-21 拍板：「我直接出 html 就行了」）——提示词导出是唯一的生成通道、HTML 是首选产物形态；**WDS 线与 diy 主线（prd → design → dev）并行不交汇**，只写自己的产物；深挖某步调用 `diy-elicit`、要多视角审视调用 `diy-party-mode`（零写面：增强结果在会话内呈现，落盘归本记录）。

## 激活时

1. 读 `{project-root}/diy-coder.yaml`；解析 `project.communication_language` / `project.document_output_language` / `paths.output_dir`。
   全程用 `communication_language` 对话；产物里的叙述文字用 `document_output_language` 写。机器锚点（ID、枚举值、文件名）逐字保留。
   缺省链：`paths.output_dir` 一律取 `diyc.py resolve` 回执（引擎缺省 `diy-output`，异常形状降级并 warning）；缺 `document_output_language` 落 `project.communication_language`；两者皆缺则跟随用户当前消息的语言，并在收尾一行说明。
   实例名只在本次激活参数出现 `--instance <name>` 时才传（无头侧入口 `runner.py --instance`；交互侧由用户在发起消息里给出同一旗标）；未传时回执的 `output_dir` 即主线平铺根。
   实例解析（FR-4.5/D-9）由工具脚本执行：运行 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json`，把回执里的 `output_dir` 当作本次运行唯一的读写根目录。
2. 续接检测：跑 `list` 看有没有已在做的活动——**只回 `id` / `code` / `name` / `status` / `items` / `exported` 六字段，不读正文**：
   `python "{project-root}/.claude/skills/diy-wds-assets/scripts/wds_assets.py" list --project-root "{project-root}" --output-dir "{output_dir}" --json` ｜ 有记录 → 播报六字段并问「① 接着做 / ② 复审调整 / ③ 推倒重来」，**HALT 等选择**；无记录 → 进第 3 步。
3. 门禁（零产出退出）：读 `{output_dir}/wds-scenarios.yaml`——**缺失 → 一行说明并零产出停止，路由 `diy-wds-scenarios`**；其 `project.status: 已定稿` 不成立 → 同样零产出停止（`init` / `check` 会把两者机械兜住：`MISSING_FILE` / `STATUS_MISMATCH`）。门禁过 → 按它只读取 `scenarios[].pages[]` 的 `id`（`SC-<nn>.P<n>`）/ `name` / `purpose`；`{output_dir}/wds-design-system.yaml` **可选读**（缺 → 降级：`token_ref` 留空、不校验令牌一致性，并在收尾记 gap）。
4. 读取纪律：预载预算 = 本文件、上述配置与回执、`steps/` 下当前那一个文件——绝不批量预载；执行期读取以每个步骤开头的 `Read (input)` 行为唯一权威，**主文件不列举封闭清单**。
5. 读 `steps/01-wireframes.md` 并照做（裸 `steps/*.md` 路径从本技能安装目录解析）。每步结尾点名下一个要读的文件。

## 工作流

全局步骤纪律：一次只加载一个 `steps/` 文件——绝不批量预载；除检查点外每步产出整块给出；`activities[]` / `prompts[]` / `presentation[]` 由你直接编辑 `wds-assets.yaml`（内容型产物，写权归会话），骨架与校验归引擎。

1. `steps/01-wireframes.md` — 线框（W）：载上下文 → 盘点 → 保真度三档 + 设计风格 → 提示词 → 成套评审。
2. `steps/02-page-designs.md` — 页面稿（P）：四源上下文 + **就绪度评估与依赖阻断** → 双风格库合并令牌 → 桌面先行 → 合规五查。
3. `steps/03-ui-elements.md` — UI 件（U）：组件定义 + **5 态 × 变体矩阵** → 渲染方式 → 按组件组顺序 → **WCAG AA**。
4. `steps/04-icons.md` — 图标（I）：6 类图标引用 → **去重** → 4 档尺寸 + 4 风格 → 5 组顺序 + SVG 后处理 → **隐喻清晰度**。
5. `steps/05-images.md` — 图片（M）：图位需求 → 按类分批 → content-styles 按批分配 → **参考链** → 批量生成 → 批内一致。
6. `steps/06-motion.md` — 动效（V）：动效需求 → **复杂度四级路由** → 动效人格 → 按复杂度分支 → **性能 + 无障碍**。
7. `steps/07-content.md` — 文案（C）：五模型框架 **7 步**，六段 YAML（目的 / 触发图 / 认知 / 行动 / 赋能 / 结构）→ **2–3 版**成稿。
8. `steps/08-presentation.md` — **演示/视觉传达（第 9 活动，裁定 7）**：6 步共享骨架 × 7 配方子模式 + **8 原则评审门**。
9. `steps/09-finish.md` — 全活动质检 + **提示词导出包** + 3 轮迭代精修与 4 条红旗 + 定稿终门。

写回纪律：骨架在 step 1 的 `init` 铸为 `project.status: 草稿` / `stage: 线框`（8 个活动壳一次铸出 + `AS-01` 起号）；逐活动把该活动的 `status` 从 `未开始` 推到 `进行中` → `已评审`；定稿 = `project.status: 已定稿` + `stage: 收尾` + 全部活动 `已评审`（未做的活动记 `已跳过` 并给理由）。`project.name` / `created` 与铸出的 `id` 由 `init` 铸造后**不再由你改**。

渲染是静默旁路——只写调用命令，不新增「打开浏览器 / 报告路径等待查看 / 阻塞等待」交互点：`python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"`（resolved 实例时附 `--instance <name>`）。

## 结构

`{output_dir}/wds-assets.yaml` —— 唯一源头；顶层设 `project.status`（母本 §8 两值口径）：

```yaml
project: {name, created, updated, status}   # status: 草稿|已定稿；created 建文件时设、此后不改
stage: 线框|页面稿|UI件|图标|图片|动效|文案|演示|收尾   # **续接锚点**；已定稿要求 stage: 收尾
activities:                                 # **8 条**（W P U I M V C S）——每活动一组 items[]
  - id: AS-01 ｜ code: W|P|U|I|M|V|C|S ｜ name: 线框   # 序号按 code 顺序固定、不重编不复用；S = 演示（第 9 活动）；源 8 码去掉已裁的 [E]
    status: 未开始|进行中|已评审|已跳过 ｜ scope: all|select|missing|priority|category|batch   # 记录级推进锚点 ｜ 源侧范围选择原话
    style: {design: <design-styles 卡名>, content: <content-styles 卡名>, format: <presentation-formats 卡名>}
    items:                                  # 每条 = 一个可粘贴的提示词 + 它的产出位
      - {id: AS-01.1, name, pages: [SC-01.P1], spec: <一句话用途>, variant, state: [default, hover], size: "1440x900", token_ref: <设计系统令牌键，可空>,
         prompt: <整段可粘贴提示词>, prompt_lang: en|zh, content: <仅 AS-07：五模型六段块>, assets: [{path: assets/wireframes/home-desktop.html, format: html|svg|css|json|md}], review: {checks: [...], verdict: 通过|重生|待定}}
prompts:                                    # 派生索引（不复制正文）：每条 = 一个可粘贴提示词包，ID 复用来源条目
  - {id: AS-01.1, activity: AS-01, target: <外部服务的提示词目标>, file: assets/wireframes/prompts/home-desktop.md, exported: true|false}
presentation:                               # 第 9 活动（AS-08）的成品记录；recipe 取 7 配方之一
  - {id: AS-08.1, recipe: SD|EX|PD|CT|IN|VM|CV, audience, format_card: data/presentation-formats/sd-slides.md, frames: [{n, job, headline, notes}], assets: [{path, format}], review: {principles: [...8], verdict}}
revisions: []                               # {date, change, reason}
```

**资产落位（裁定 12）**：**二进制与 HTML 产物落 `{output_dir}/assets/<活动>/` 子目录、不入库**；YAML 里**只存路径引用**（`assets[].path`，project-root 相对），不嵌二进制。**已知缺口**：`viewer.py` 只扫 `output_dir` 顶层 `*.yaml` → **`assets/<活动>/` 下的产物渲染不到**（登记为 C2 面缺口）。活动子目录名 = 源侧活动名：`wireframes` / `page-designs` / `ui-elements` / `icons` / `images` / `motion` / `content` / `presentation`。

## 规则

1. 写范围：只写 `{output_dir}/wds-assets.yaml`（各段与 `revisions`）与 `{output_dir}/assets/<活动>/` 下的产物文件；不碰 `wds-scenarios.yaml` / `wds-design-system.yaml`（**上游只读**——要修正走 `revisions` 建议或路由回上游技能重跑）、不碰 `design.yaml` / `prd.yaml` / 源码，也不建任何状态散文件。
2. **不接任何外部服务（裁定 6，用户拍板）**：不调 MCP、不调 Figma / Stitch / 任何生成服务。**每条资产的唯一生成通道 = `prompt` 字段 + 提示词导出包**（`steps/09-finish.md` 第 2 步）；用户在外生成后回填到 `assets/<活动>/`。产物**HTML 优先**；**不产二进制资产**（用户自行产出后回填的除外）。
3. **检查点四选项**（每步产出后，六拍不得省）：① 生成本步产出 → ② 落盘（编辑对应键/记录 + 推进活动级 `status`）→ ③ 显示检查点分隔 → ④ 呈出本步产出 → ⑤ 出四选项 → ⑥ 等响应。
4. **选项落点**：`[a] Advanced Elicitation` → 调用 `diy-elicit`；`[p] Party-Mode` → 调用 `diy-party-mode`（两者**零写面**：增强 / 多视角产出的内容并入对应记录，调用返回后回到第 ② 拍重落盘）；`[c] Continue` → 直接进下一步；`[y] YOLO` → 后续步骤跳过 ⑤⑥（不停等），**②③④ 照旧**。无头 / 非交互 = 全程 `[y]`（摘要一行明示），**不入 `deferred-actions` 队列**。
5. **ID 体系**：活动 `AS-<nn>`（`01`–`08`，按 code 顺序固定）；条目 `AS-<nn>.<m>`（活动内递增序号，**父 ID 必须存在**）；`prompts[]` 的条目 **复用其来源条目的 ID**（派生索引，不另铸号）；`presentation[]` 用 `AS-08.<m>`。**ID 是唯一引用键**，记录之间一律引 ID 不复制内容。
6. **可机械 vs 不可机械（不得假装全自动）**：引擎可机械核的 = 活动码齐备 / ID 唯一性与父子关系 / 枚举合法 / `assets[].path` 落在 `assets/<活动>/` 内 / 提示词非空 / 7 配方码合法；**不可机械、必须由人判定的** = 提示词的**语义质量**（是否真把规格翻译成风格参数）、评审表里「隐喻清晰度」「品牌对齐」「文化敏感度」三项、以及 `data/stop-red-flags.md` 的四条红旗（何时该停手）。
7. **终门（机械）**：先落 `project.status: 已定稿` + `stage: 收尾`，再跑 `python "{project-root}/.claude/skills/diy-wds-assets/scripts/wds_assets.py" check --final --project-root "{project-root}" --output-dir "{output_dir}" --json`——`exit 0` 是唯一放行；零 `[假设]`（未决项写 `revisions` 或就地补问）。渲染与收尾都等 exit 0。**WDS 型产物一律走本引擎终门**，不得改用 `diyc.py check --type`（那是主线 8 型封闭集）。
8. **违规码**：复用冻结集（`MISSING_FILE` / `UNPARSABLE_YAML` / `DUPLICATE_ID` / `UNKNOWN_ID` / `EMPTY_FIELD` / `ENUM_INVALID` / `STATUS_MISMATCH` / `SET_MISMATCH` / `ASSUMPTION_PRESENT`）+ B6 的已批码 `TOKEN_UNRESOLVED`（**本批不新增码**）；`SET_MISMATCH` 承载「活动码缺项 / 父子 ID 不同源 / 资产路径越出 `assets/<活动>/` / 提示词条目无来源」四类。
9. **无 `--previous` 轮**：`activities[].items[]` 与 `prompts[]` 只增不减，无 ID 集合收缩面；改既有记录往 `revisions` 追加（date / change / reason，`change` 点名 `AS-<nn>.<m>` 而不复制内容）。副作用面：除产物、`assets/<活动>/` 下的自产文件与静默渲染外无任何外部动作；产物内引用一律 project-root 相对 `path:line`。
10. **不可机械的三处纪律要在场（裁定 6/16 的摘留）**：`data/iteration-refinement.md` 的**3 轮迭代精修**、`data/stop-red-flags.md` 的**4 条红旗**（过早优化 / 过度工程 / 分析瘫痪 / 工具崇拜）、`templates/prompt-export.template.md` 的**通用生成提示词骨架**——三条都不是外部服务资产，**逐条保留**，落点见 `steps/09-finish.md`。
11. **边界（对方侧随 C 阶段补；本技能产 WDS 线产物——不进 diy 主链 CHAIN、不被主线任何门禁引用）**：vs `diy-design`——它产**结构稿与框架实现**（`design.yaml` + `prototypes/` + `src`，可跑、被 dev 采用），本技能产**视觉件与文案**；**本技能反向回填 `design.yaml` 的口在 diy 侧不存在**（源侧 `E-Assets` 的消费者为零，普查实测）——本技能是**链条终点**，下游接线随 C·3。vs `diy-wds-system`——它是**上游**（令牌与组件定义的来源，本技能可选读其产物）。vs `diy-elicit` / `diy-party-mode`——不是竞争是调用（见规则 4）。
12. **本线风格与 HARM/HELP（源 Freya 线 + Mimir 线的归位）**：**规格必须完整**（不完整的规格到生产阶段一定要返工）、**先原型后生产**、**设计系统从实际使用中长出**；**「UI 每次改动都要在浏览器里验证」**（源 mimir 的行为规格句）——凡产出 HTML 的活动，评审时**用浏览器实际打开核对**（本机 `playwright` 在 C·8 命令白名单内），不是只看提示词。**HARM**：产出一套看着齐、但每条提示词都缺规格锚（页面 / 尺寸 / 令牌）的资产清单——用户导出后生成的回不来，比不做更糟；**HELP**：每条资产先落「服务哪一页、哪个尺寸、哪些令牌」，再写提示词，交付一份不改一个字就能粘贴出去的清单。

- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；不复述上游已写的信息（引用 ID）；不写没有信息量的套话。

- **写作纪律。** 主字段 = 大白话主句；数字/枚举内联；机器语法（命令/旗标/路径）进括号；机器锚点逐字保留（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 `diy-design` 的 detect 启发式。schema 若定义 `plain`：一行写清该条目为什么存在，绝不写是什么（转述会漂移）；只写难懂的条目。若定义 `detail`：过程叙述——结论留在主字段。
