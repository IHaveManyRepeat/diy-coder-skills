# Step — [W] 出视觉（Visual）· 结构稿段

Progress: `[1 定稿面] → [2 生成结构稿] → [3 评审与回写] → 收尾路由`

**Read (input):** `{output_dir}/design.yaml` 的 `direction` / `tokens` / 该页 `pages[]` 记录；`[K]` 已确认的分区结构（若有）；同场景其它已出稿的 `{output_dir}/prototypes/*.html`（跨页一致性比对）；用户在本文件各步的回答。
**Write (output):** `{output_dir}/prototypes/<页 id>.html`（每页一份）；`design.yaml` 的 `pages[].prototype` 路径；复核后的规格增补（回写 `states[]` / `tokens`）与 `revisions`。

你是**设计总监**。W 段产出的是**结构稿**：布局、区块、landmark、四条交互状态，且它**从 `design.yaml` 再生**。

〔**工具面裁撤声明（X4–X8）**〕源 `steps-w/` 五文件 867 行里的**五选一工具菜单**（`[E] Excalidraw / [N] Nano Banana / [G] Google Stitch / [F] Figma / [H] HTML Prototype`，源 `step-01:65-71`）**整块裁**，连带：

| 裁撤项 | 源侧位置 | 理由 |
| --- | --- | --- |
| Nano Banana MCP + `GEMINI_API_KEY` + `.claude/mcp.json` 配置位（X1–X3） | `steps-w/step-00-nb-setup.md:60,80-84` | 平台耦合；diy 无该服务，且源侧「AI 生图做线框」在 `[C]` 的活动纪律里本就被列为 SYSTEM FAILURE |
| Figma（X4，48 处 / 19 文件） | `step-01:73`、`DESIGN-LOOP-GUIDE.md:52` | 平台耦合；diy 的结构稿是 HTML 且可 diff |
| Google Stitch / Pencil.io（X5 / X7） | `step-01:75` 等 | 同上 |
| 源侧 `step-02` 的无主菜单（普查 D2：菜单写 `[C] Continue` 但 frontmatter 无 `nextStepFile`） | `step-02:1-9,115` | 断链，不复制 |
| `step-02w` NB 提示词工厂（349 行，超 250 行硬限） | `steps-w/step-02w-*.md` | 随 NB 一并裁 |

**diy 侧只剩一条路**：`prototypes/<页 id>.html`（`[H] HTML Prototype` 那一路），这正是源侧五选一里唯一与「单一源再生」相容的一条。

## 第 1 步 —— 定稿面

出稿前把三件事摆在桌上（都是**读**，不是问）：`direction` 的具名方向与反模式禁令、`tokens.*` 的全部值、该页 `states[]` 的四态信号。**四态缺一不出稿**——结构稿要一次把四个态都画出来（源侧 `[P]` 的 4c 就要求每段带状态），少一个后面返工。

## 第 2 步 —— 生成结构稿

生成 `{output_dir}/prototypes/<页 id>.html`：

- **布局与区块**：按 `[K]` 确认的（或 `[P]` 第 2 步定的）分区顺序与相对位置；
- **landmark 与语义 HTML**：`h1` **恰好一个**、`img` 带 `alt`、`input` 带 `aria-label` 或被 `label[for]` 关联——这三条是 `check` 的 `semantic-html` 判定面，出稿时就满足，别留给收尾；
- **token 引用**：色值/字号一律走 CSS 变量（`var(--color-*)` / `var(--space-*)`），不写裸值——`audit` 只看真实色值位，`var()` 免检，裸值会被判 `one-off-*`；
- **四条交互状态**：每态都要在稿里**看得见**（不靠注释说明），且每态至少一条**非色彩**信号（图标 / 文字 / 形状 / 动效）。

**这一段的迭代成本最低**（源侧明写「在这一段便宜地迭代」）——布局不要等框架实现再改。

## 第 3 步 —— 评审与回写

源 `steps-w/step-03:65-67` 的两条自认局限**逐字直译**并保留：

> `AI-generated text in images is often garbled -- do NOT rely on the image for exact text content. The spec is the source of truth for all text.`
> `Focus review on: **layout correctness**, **color accuracy**, **mood/feeling**, **section presence and order**`

diy 侧口径：**规格（`design.yaml`）是所有文案的唯一真源**；评审只看四项——**布局正确 / 色彩准确 / 氛围 / 区块在场与顺序**。评审结论三选一（源 `step-03` 的回写动作，直译）：

| 结论 | 处置 |
| --- | --- |
| 规格没问题、稿有问题 | 改稿（改 `prototypes/<页 id>.html`） |
| 稿暴露了规格缺口 | **回写 `design.yaml`**（补 `states[]` / 补 token），再改稿——**不许只改稿不改规格**（那会造成两份源漂移） |
| 结构与分区都不对 | 回 `./k-sketch.md` 第 4 步重走结构确认硬门 |

**落盘**：`pages[].prototype` 指向本稿；有规格增补时往 `revisions` 追加一条 `{date, change, reason}`。

**检查点**：① 生成 ② 落盘稿 + `prototype` 路径 ③ 分隔 ④ 呈出该页四态摘要 ⑤ 给选项 ⑥ 等响应。

**收尾与路由**：结构稿已出 → 读 `./prototype-loop.md` 逐段循环，或（结构稿已确认、直接进生产）读 `./h-delivery.md`。

**裁撤登记（其余）**：源 `data/guides/HTML-VS-VISUAL-STYLES.md`(243) / `NANO-BANANA-PROMPT-GUIDE.md`(468) 随工具面一并裁（合计 711 行）；源 `step-00:93` 的 `01-Visual-Design/design-concepts/` 落点与 `step-03:86-88` 的三条视觉落点（含自称 legacy 的 `visuals/` 路径，普查 D13）**全裁**——diy 的视觉落点只有 `prototypes/`（结构稿）与 `src`（实现）。

本文件到此结束，不再回头。
