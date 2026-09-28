# Step — [D] 自主成稿（Dream Up）· mode 声明

Progress: `[0 mode 声明] → [1 整条做完] → [2 终局复审] → [3 收尾路由]`

**Read (input):** `./s-suggest.md`（**本活动复用它，不复制第二套文件**——见第 0 步）；`{output_dir}/design.yaml` 的 `pages[]` 与 `direction` / `tokens`；`{output_dir}/wds-scenarios.yaml` 该 `SC-<nn>` 下**全部页**（WDS 线）；`{output_dir}/prd.yaml` 的全部前端面 FR（主线）。
**Write (output):** 该场景**全部页**的记录（`pages[]`：`name` / `route` / `states[]` 雏形）；该场景 `design_status` 推进到 `discussed`（WDS 线：**场景级键**，不逐页写，值域见主文件规则 1）；`revisions`（终局复审里的用户改动）。

你是**设计总监**。`[D]` **不是缺失的活动**——源侧它是**刻意的模式复用**：`workflow-dream.md:44-45` 明写 `The Dream workflow uses the same steps as Suggest (./steps-s/) but with autonomous execution`，靠 `:57-67` 的 `Mode Override Rule` 把 halt 纪律**整批反转**。

## 第 0 步 —— mode 声明（本文件就是声明本体）

**`steps/` 下不复制第二套文件**：本活动走 `./s-suggest.md` 的**同一批八步**，只是把下面四条**反转**（源 `workflow-dream.md:57-67` 逐条直译）：

| 源侧 Override 原文 | diy 侧口径（`[D]` 模式生效时） |
| --- | --- |
| `OVERRIDE all "halt and wait" rules — auto-proceed after completing each step` | 八步**连续跑完**，不在步间 halt；检查点的 ⑤⑥ 两拍**跳过**（①②③④ 照旧） |
| `OVERRIDE "NEVER generate content without user input" — generate based on context and WDS patterns` | 允许**基于上下文先成稿**：页名/目的/入口一律从上游记录**推导**，不反问；推导不出来的项**不编造**，记进 `open_questions`（`待办`） |
| `DO NOT display menus or wait for menu selections between steps` | 全程不出菜单，只在**终局复审**（第 2 步）出一次 |
| `DO still save outputs and update the design log at each step` | **落盘不许省**：每页跑完即写 `pages[]`（该场景全部页跑完后才写场景级 `design_status: discussed`）（源 `:83` `even in autonomous mode, the design log must be updated per page`），**不许攒到最后一次性写** |

**反转是模式条件，不是永久授权**：这四条**只在 `[D]` 生效**（`design_intent: D` 或用户当场点名）。回到 `[S]` 即恢复 halt 纪律——源侧 `workflow-dream.md:59` 原文 `These rules apply ONLY in Suggest mode` 的反面同义。**逃生口照收**（源 `:67`）：会话中用户随时可打 `stop` / `pause`，立刻切回 `[S]` 的逐步确认。

## 第 1 步 —— 整条做完

按 `./s-suggest.md` 第 1–7 步**连续**把该场景的**全部页**做完（不是一页一停）。每页工序同 `[S]`，区别只在「不停等」与「先成稿后复审」。

**自动组件提取**（源 `:132-138`，diy 侧改写）：每页完成后扫一遍共享元素，命中就**记一条候选并转 `diy-wds-system`**——〔**改写理由**〕源侧是「自动提为共享组件、后续页引用而非复制」；diy 侧组件身份与 token 单一源归 `diy-wds-system`（`components[]` 的「二次使用才提取」阈值），本技能**只报候选，不自行铸组件**。

## 第 2 步 —— 终局复审（唯一的用户交互点）

呈出**逐页决策摘要表**（源 `:89-106` 的复审表，直译）：页 ID / 页名 / 目的 / 承接 FR 或 `SC-<nn>.P<n>` / 主行动 / 变体数。

用户逐页可：**接受** / **打回重做该页** / **改结构**（增删页）。打回或改动 → 落 `revisions` 并回第 1 步重跑该页，**重跑后重呈整表**（不增量呈）。若改动是**整条 `SC-<nn>` 废弃** → 该场景 `scenarios[].design_status` 写 `removed`（场景级键；口径见 `./c-discuss.md` 第 4 步「场景级废弃」）。

**门禁不自弃**：`[D]` 的自主性**不降低终门**——四态不许省、`[假设]` 清零、三命令全过、`open_questions` 零 `待办` 一条不松（`./p-specify.md` / 主文件「工作流」第 6 步照走）。

## 第 3 步 —— 收尾路由

复审通过 → 读 `./prototype-loop.md` 逐段建结构稿。

**裁撤/保真登记**：源 `workflow-dream.md` 的自有部分只有 144 行，其中 `:14-41` 四节与 `workflow-suggest.md` **几乎逐字相同**（27 行中仅 1 词之差：`:27` 的 `Page Creation` vs `Process`；普查 R10 原文称「逐字相同」，实测按此收窄，**裁到单一源** = `./s-suggest.md` 第 1 步）；`:108-130` 的「Per-Page Mode」两问过渡与 `workflow-suggest.md:77-111` 内容一致（普查 R9，**裁到一处** = 检查点四选项）。**本文件只承载 mode 语义**——这正是裁定 3 的口径：读取纪律本体由主文件 §4 锚串承担，diy 侧**只引入母本没有的那部分**（模式整批反转的条件语义）。

本文件到此结束，不再回头。
