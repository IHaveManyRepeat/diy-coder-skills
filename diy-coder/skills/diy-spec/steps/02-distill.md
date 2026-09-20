# Step 2 — 五字段蒸馏（Distill）

Progress: `输入与定位 → [蒸馏] → 两遍自校验 → 终门与交付`

**Read (input):** step 1 的输入清单与其材料；更新路径下该记录的现行五字段与 `capabilities`。
**Write (output):** 记录的 `why` / `capabilities` / `constraints` / `non_goals` / `success_signal` / `assumptions` / `open_questions` / `companions` / `sources` / `artifacts`。

## 走法

结构化且已分节的输入 → 尊重作者的分节，把合内核的抬进五字段、溢出的抬进 `artifacts`；混合输入 → 自己分拣：逐条声明走一遍 load-bearing 判定，路由到内核字段或 `artifacts`。

先按输入丰瘠选一条路（稀疏输入二选一，**选择记进 `verdict.coherence` 段末**）：

- **express**——尽力蒸馏，每个缺口都落 `open_questions[]`。**无头默认走这条**并记录。
- **guided**——逐字段与用户走一遍，一次一个字段。

输入丰富则直接抽取，不做 elicitation（本技能蒸馏，不引导）。

## 五字段

- **Why**——一段话，点名四类来源之一（或组合）：`pain`（要解决的痛）/ `opportunity`（新出现的机会）/ `vision`（想让它存在的愿景）/ `mandate`（法规、废弃、期限、合同义务）。写清谁受影响、为什么是现在。下游每一次取舍都回到这段话。
- **Capabilities**——每条 `{id: CAP-N, intent, success}`：`intent` 一句「用户或系统能做到 X 以达成 Y」（**WHAT，不是 HOW**）；`success` 一条可测或可演示的判据，测试或真演示能判定的那种。新能力的号取**下一个未用号**；退役的保留条目并标 `retired: true`。
- **Constraints**——非协商项，且**真能淘汰设计**：不淘汰任何东西的「约束」是装饰，不配进这一格。
- **Non-goals**——至少一条显式划出范围之外的东西；缺席等于让下游技能自行填补真空。
- **Success signal**——一到两句：**世界变化的时刻**，不是仪表盘读数；具体到能写一个测试或跑一次演示。

## Spec Law 8 条（自校对面，step 3 逐条走）

1. 每条 capability 同时有 `intent` 与 `success`——缺一不成能力。
2. `intent` 描述 WHAT 而非 HOW；实现处方归 `artifacts`。
3. constraint 真能淘汰设计决策。
4. non-goals 显式，至少一条。
5. success signal 具体到可测可演示（「用户会喜欢」不算）。
6. CAP ID 稳定唯一：永不重用、永不重编号。
7. **Preservation**——每条 load-bearing 源声明都落进产物（内核或 `artifacts`）；纯包装性内容不落。
8. Lean prose——每句都承载 load-bearing 内容；装饰、对冲、背景铺陈、清嗓子的话都砍。三处一视同仁：内核、`artifacts`、`revisions`。

## load-bearing 三透镜

一条声明是 load-bearing，当且仅当**任一消费方**少了它就会改变决策。三面各问一遍：

1. **下游技能**——少了它，下一个技能会不会做错事？
2. **实现者**——少了它，写代码的人会不会选错做法？
3. **验证者**——少了它，验收的人会不会放行错的东西？

三面都答「不会」→ 不落（或者它只是包装）。判不准时按「落」处理，但落进 `assumptions[]` 讲清依据。

## artifacts 开条判据（spec-authored 内容的内联承载位）

内核里一行装不下的 load-bearing 内容，开一条 `artifacts: [{name: <类型名>, body: <多行块字符串>}]`：

- 多条目目录（逐实体的矩阵：品类、模式、路线一类）
- 表格；**图表一律进 artifacts**（mermaid 块、ASCII 图、图像引用都写进 `body`）
- 编辑口径 / 声音规则；内核按名字引用的长参考（术语表、遗留系统说明、项目惯例）

**开条判据：「超过一行内核形状」。** 单行的决策翻转项留在 `constraints`；intent + success 配对留在 `capabilities`。某个内核字段开始套子条目时，内容已经长过内核，该开 artifacts 了。

`name` 取**内容类型名**（kebab-case 标识，读的人开条前就知道里面是什么）：`glossary` / `stack` / `conventions` / `state-machines` / `failure-modes` / `architecture-diagrams` / `compliance-references` / `<entity-class>`（如 `patron-archetypes`）。同一类型只开一条；拆多条时用更细的类型名。

## companions 双轨与 sources

- **spec-authored**（本技能所有）→ 内容**内联进 `artifacts[]`**，不另建文件——diy 侧单源纪律。
- **adopted**（上游技能所有、下游仍要读）→ 只记**路径引用**进 `companions: [<relative path>]`（相对 project-root、正斜杠），**不复制内容、不改它**；它在场性由终门校验。
- **`sources[]`**——已被完全吸收、下游不再需要读的源文档（如某份 PRD 的每条 load-bearing 声明都已进内核），只列路径供审计；**不列** decision log / README / 组织性文档 / 上游的过程元数据。
- 跨文档信息一律引用 ID 或路径（`CAP-N` / `path:<relative>`），禁止复制——复制会漂移。

## 播报与下一步

一句话：五字段各落了几条、开了几条 artifacts、引了几个 adopted companions、哪些缺口进了 `open_questions`。

读全并照做 `./03-validate.md`。
