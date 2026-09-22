# Step 4 — token 提取、定稿与收尾（Extract Tokens）

Progress: `[1 token 三段成形（重复值入 token）] → [2 组件编目与 token→组件映射] → [3 定稿、终门与渲染]`

**Read (input):** `{output_dir}/design.yaml` 的 `pages[]`（第 3 步已落）与 `tokens` 空壳；`steps/02-explore.md` 的色板 / 字阶 / 间距三张清单与 `reverse.py tokens` 的分流回执；`check` 回执。
**Write (output):** `direction`（具名方向 + 反模式禁令）/ `frontend_framework` / `tokens` 三段；`project.status: 已定稿` + `project.updated` 刷今天；`revisions`（未决项与来源登记）；给用户的交付摘要与路由。

你是**设计系统的提取者**（源 step-04 Extract Design System）。这一段把散开的原始值收成**有结构、可复用**的 token 三段，再走终门。

**本段纪律**：① **不跳读**：本步只读它点名的那一份产物，绝不批量预载 `steps/`；前一步的产物没落盘，本步不许开工。② **不编造**：读不出来的值留空并记 gap；绝不用印象补。③ **不代决**：检查点呈出后 HALT 等响应，绝不替用户拍板。④ **不改页规格**：源 `FORBIDDEN to modify page specifications — they are final from Step 03`——页规格在 `03-specs` 已定稿，本步只动 token 段。

## 第 1 步 —— token 三段成形（源 step-04 第 1 指令）

**先说清为什么**：讲清「为什么 token 要按用途分组、不按位置罗列」——按位置罗列的是这几次观察的流水账，按用途分组才是下一份设计能用的规则。用你自己的话讲。

### 1.1 四组值 → 三段 token（源 step-04 第 1 指令全保）

| 源分组 | diy 落点 |
| --- | --- |
| **颜色**（按用途：品牌 / 文本 / 背景 / 边框 / 反馈） | `tokens.color` 六键：`bg` / `surface` / `text` / `text_muted` / `accent` / `accent_text` |
| **字体**（族 + 从 h1 到 caption 的字阶：字号 / 字重 / 行高） | `tokens.typography.family_base` / `family_heading` / `scale[]`（阶逐条写成 `字号` 短句） |
| **间距**（基准单位 + 阶，含区块内距 / 卡片内距 / 元素间距三类模式） | `tokens.spacing.unit` + `scale[]` |
| **其他 token**（圆角、阴影、断点） | 会话呈出并记 gap——既有 schema **无这三类的承载位**（登记为 C·3 的 schema 扩充项，本批不新增字段） |

**取值纪律**：**只收 `02-explore` 3.3 判为「重复值」的**（单次值一律不收）；色值写 `#rrggbb` 形态，非法 hex 判 `ENUM_INVALID`。三键 `bg` / `text` / `accent` 为 `validate` 的必填（引擎同判 `EMPTY_FIELD`）。

### 1.2 方向与框架（既有 schema 的另两项必填）

- `direction`：**第一行**一句话具名方向，换行后 **2–3 行反模式禁令**（每行以 `- ` 起头）——逆向出来的方向同样要**具名**，不许写「干净极简」。
- `frontend_framework`：逆向一个网站时写 `html`（纯 HTML 项目止于结构稿，省略 `implementation`）。

**落盘**：`direction` / `frontend_framework` / `tokens` 三段。

**检查点（六拍）**：① 生成 → ② 落盘 → ③ 分隔 → ④ 呈出 → ⑤ 出四选项 → ⑥ 等响应。本步：② 落盘（`direction` / `frontend_framework` / `tokens`）；④ 呈出 token 三段与分流清单。
`[a]` 高级引导 → 调 `diy-elicit`（零写面）｜ `[c]` 继续 → 进下一步 ｜ `[p]` 多方模式 → 调 `diy-party-mode`（零写面）｜ `[y]` YOLO → 跳过后续检查点连续推进（首次选中时一行明示）。

读全并照做本文件 `## 第 2 步 —— 组件编目与 token→组件映射（源 step-04 第 2–4 指令）`。

## 第 2 步 —— 组件编目与 token→组件映射（源 step-04 第 2–4 指令）

**先说清为什么**：讲清「为什么这一节落不进产物也要做」——token 与组件的对应关系是设计系统能不能被复用的判据；它今天没有承载位，但**不给它一个去处，收出来的 token 就是一堆没有意义的色号**。用你自己的话讲。

### 2.1 组件编目（源 step-04 第 2–3 指令）

逐条写：**变体**（主 / 次、小 / 中 / 大）、**状态**（默认 / 悬停 / 聚焦 / 激活 / 禁用 / 加载 / 错误 / 成功）、**内容槽**（图标 / 标签 / 描述 / 图像各放哪）、**响应式行为**。表头：组件 / 变体 / 状态 / 内容槽 / 响应式。

### 2.2 token → 组件映射（源 step-04 第 4 指令）

逐组件填一张表：**组件 / 用到的颜色 / 字体 / 间距 / 圆角**。**映射必须显式**（源 `Token-to-component mapping must be explicit`）——它是「这页为什么用这个色」的答案。

### 2.3 落点：**不落进 `design.yaml`**（裁定 13）

既有 schema **没有 `components[]` 段**，两份表**不新增字段、不落散文件**：

- **会话内呈出**两张表（这是它们在本批的正式交付形态）；
- **交接 `diy-wds-system`**——它的产物 `wds-design-system.yaml` 带 `components[]` 与 token 引用，**组件编目的 diy 落点是它**；一句话把交接面说清（组件清单 + 映射表 + `design.yaml.tokens` 的引用关系）；
- **登记为 C·3 项**：`design.yaml` 是否增设组件/映射段，与「提取来源」字段一并排期。

**检查点（六拍）**：① 生成 → ② 落盘 → ③ 分隔 → ④ 呈出 → ⑤ 出四选项 → ⑥ 等响应。本步：② 落盘（本步无写盘：两张表在会话内，`revisions` 记一条交接项）；④ 呈出编目表与映射表。 四选项同第 1 步。

读全并照做本文件 `## 第 3 步 —— 定稿、终门与渲染`。

## 第 3 步 —— 定稿、终门与渲染

### 3.1 定稿落盘

`project.status: 已定稿` + `project.updated` 刷今天；`revisions` 追加一条初始生成记录（`change` 写「初始生成：逆向自 <url / 截图名>」、`reason` 写用途），以及本轮未决项与 gap（一条一句）。

### 3.2 终门（机械；`exit 0` 是唯一放行）

```
python "{project-root}/.claude/skills/diy-reverse/scripts/reverse.py" check --final --project-root "{project-root}" --output-dir "{output_dir}" --json
```

`--final` 核：`project.status: 已定稿` + `direction` / `frontend_framework` 非空 + `tokens` 三段必填键齐（色值合法 hex）+ `pages[]` 非空 + 每页四态齐且各有非色彩信号 + 每页结构稿在场且与 `id` 同源 + `P-<n>` 唯一且顺序 + **零 `[假设]`**。**按回执 `where` 就地修、重跑，不得跳过**。

### 3.3 交叉核对既有设计域引擎（**裁定 13 的实测面**）

本引擎的判据是既有 schema 的复述；**权威仍是 `diy-design` 的两个只读命令**，各跑一次，**都必须 `exit 0`**：

```
python "{project-root}/.claude/skills/diy-design/scripts/design.py" validate --design "{output_dir}/design.yaml" --json
python "{project-root}/.claude/skills/diy-design/scripts/design.py" check --design "{output_dir}/design.yaml" --json
```

两者不一致时**以它为准修产物**（`check` 另核 WCAG 对比度配对、语义 HTML 三项）；修完重跑 3.2 —— 渲染与收尾都等全部 `exit 0`。

### 3.4 渲染（静默旁路）

`python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"`（resolved 实例时附 `--instance <name>`）。

### 3.5 交付摘要与路由

呈出一页摘要（会话内，不落盘）：**来源**（URL / 截图名 + 采集日）/ 页数与页 ID 清单 / token 三段计数 / 被剔除的单次值条数 / 组件编目条数 / 未决项。随后给路由三句：

- **产物归属**：`design.yaml` 的**生成权在本技能、演进权在 `diy-design` / `diy-dev`**——后续改动走它们的 Update，不要重跑本技能（会撞 `OVERWRITE_REFUSED`）。
- **能力交接**：组件编目与 token→组件映射 → `diy-wds-system`（`components[]`）；多页流程大纲 → 会话时仅供参考，进主线走 `diy-wds-scenarios` 的场景链。
- **登记项**：提取来源字段与组件/映射段**无承载位**，已登记为 C·3 的 schema 扩充项。

**收尾与路由**：三个引擎都回 `exit 0` 后，本文件到此结束——不再读任何 `steps/` 文件。

本文件到此结束，不再回头。
