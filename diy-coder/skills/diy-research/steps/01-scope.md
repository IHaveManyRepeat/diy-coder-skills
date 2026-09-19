# Step 1 — 主题范围与目标确认

Progress: `[Scope] → <dimension> 02–05 → Synthesis`

**Read (input):** 激活前的对话；用户点名的任何输入（简报、既有笔记、转录稿）。
**Write (output):** `{output_dir}/research.yaml` 里的草稿记录（`id` / `dimension` / `topic` / `goals` / `scope` / `date` / `status: 草稿` / `findings: []`）；范围播报。

## 找到主题

激活前的对话就是起点——不是白纸。找出用户想研究的主题、问题或领域，只问还缺的部分：

**你想研究哪个主题、问题或领域？** —— 例如「欧洲电动车市场」「大规模应用选 React 还是 Vue」「欧洲可持续包装法规」。

## 澄清（三个问题，一轮问完）

1. **核心关注** —— 「关于 {topic}，你最想弄清什么？」
2. **研究目标** —— 「你希望这项研究达成什么？」→ 落成 `goals`。
3. **范围与方法** —— 「是广撒网，还是深挖某几个方面？」——细分市场、地理区域、用途（市场进入 / 扩张 / 产品开发），以及用户点名要分析的竞争对手或细分 → 落成 `scope`。

此步不做任何检索，只确认理解与范围。

## 定维度

- **市场** —— 客户与竞争：行为与分层、痛点、决策过程、竞争格局。
- **技术** —— 技术与架构：技术栈、集成模式、架构模式、性能与扩展性、实现路径。
- **领域** —— 行业与生态：行业分析（规模、经济性、价值链）、竞争格局、监管环境、技术趋势。

一条记录 = 一个主题的一个维度。想要两个维度就得到两条记录（`RS-###`），各有自己的 `goals` 与 `scope`。两条记录**串行**：第二条在第一条第 6 步过终门并收尾（渲染 + 播报）之后才开（追加新 `RS-###`、重回本步）；不并行、不共用收尾播报（见 `./06-synthesis.md`）。选择确实含糊时，问——绝不悄悄选一个。

## 确认硬前提

**必须能联网检索。** 不可用即在此中止，告知用户，零写入。

## 写草稿记录

向 `{output_dir}/research.yaml` 追加一条记录（文件缺席时新建：`project: {name, created, updated}`——`name` 取 `diy-coder.yaml` 的 `project.name`——外加空的 `researches` 列表与 `revisions: []`）：

```yaml
  - id: RS-001                 # 下一个 = 既有最大值 + 1，三位零填充；永不重编号、永不复用
    dimension: 市场            # 市场 | 技术 | 领域
    topic: {用户的原话}
    goals: [{问题 2 的答案}]
    scope: {问题 3 的答案}
    date: YYYY-MM-DD
    status: 草稿
    findings: []               # 各分析步逐条追加，一次一条
```

日期口径：格式一律 `YYYY-MM-DD`；`project.created` 建文件时设、此后不改；`project.updated` 每次写回刷今天；记录的 `date` 是**本条动作的日子**（= 建这条记录那天），不随 `updated` 变。

源技能的命名规则按新载体承接：源技能写 `<dimension>-<slug>-research-<date>.md`、从主题派生路径安全 slug；diy 产物是一个固定文件，故 `dimension` + `topic` + `date` 即其身份，不派生路径、不派生 slug。

## 确认与继续

把理解摆回去——主题、目标、维度、范围，以及该维度将走的四个分析步——然后停下：

```
范围：{topic} — {dimension}

开始 {dimension} 维度的分析吗？

[C] Continue —— 确认范围，进入第一个分析步
[Modify] —— 改范围后再继续
```

HALT——等用户。选 `[Modify]` 时收齐改动、更新记录、重新展示；收到 `C` 答复后，读全并照做该维度的第 2 步。

## 播报与下一步

市场 → `steps/market/02-customer-behavior.md`；技术 → `steps/technical/02-stack.md`；领域 → `steps/domain/02-industry.md`。只读与记录 `dimension` 匹配的那一个。
