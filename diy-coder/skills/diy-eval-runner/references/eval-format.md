# 用例形态与四模式

一个 **case** 是一次评测的单位：`input + rubric + 可选 state_prefix + 可选 files`。四种模式共用同一套 case 形态，变的只是「跑哪些 config」与「怎么判」。

## case

```json
{
  "id": "create-1",
  "input": "给 InsuLens 写一份 brief——它是面向中型保险公司的理赔分诊工具，笔记在 evals/insulens/files/memo.md",
  "rubric": [
    "brief.md 存在且字数在 250-1500 之间",
    "brief.md 点名了 InsuLens 与中型保险公司这一细分市场",
    "brief.md 至少吸纳 memo.md 里的两个具体要点，且没有编造 memo.md 里没有的说法"
  ],
  "state_prefix": null,
  "files": ["evals/insulens/files/memo.md"]
}
```

- `id`：稳定标识，同时是 run 里该 case 的目录名。
- `input`：**真实、毛糙**的用户请求——用真路径、真公司名、错别字、口语。打磨过的输入测的是技能很少遇到的情形。引擎逐字发送（`state_prefix` 已前置）。
- `rubric`：具名 expectation 列表，逐条可判 `{text, passed, evidence}`。每条值不值得留，看下面的强/弱分类学。
- `state_prefix`：可选，方括号起手式，把技能「按到流程中段」（见下）。
- `files`：可选夹具，运行前 stage 进该 case 的清场目录。裸文件名落工作目录根、带目录则保留相对结构（input 才能逐字引用）。来源解析顺序：`--project-root` 相对 > 用例文件目录相对 > 绝对路径。

trigger 的 case 更轻：`{query, should_trigger}`——没有产物要判，只有「触发了没有」。

## state_prefix：单发模拟多轮

多数多轮技能，只要 case 设计得对，就能单发评测。`state_prefix` 就是那个把中段可达的关键发明——一段方括号起手式，告诉技能「这一轮落在你流程的哪一步、用户已经说了什么」：

```
[技能已走完发现阶段；第 4 轮用户被问及干系人，回答：] 用户说："就我和一个 PM"
```

引擎把它前置到 `input`、合成一条消息发出。于是任意中段时刻（澄清轮、纠错轮、打断后续跑）都能用一次输入考到。**对话弧线本身就是交付物**的 case 除外——那类仍需人类判断。

主观类技能（教练、头脑风暴、设计主持）可以不要 rubric 靠人判；`state_prefix` 在那类照样值钱，它让人类看到想判的正是中段那一刻。

## 强 vs 弱 expectation

expectation 有区分度（错输出过不了）时，grader 判得更准、结果更诚实。**弱 expectation 比没有更糟**——它亮起的绿灯读起来像证据，其实什么也没量。写进 rubric 前先照下表自查；grader 看到弱断言会标出来。

**弱（别写）**：

- 只查文件名存在——空文件也过。存在性必须配内容检查。
- 纯主观措辞——"brief 质量高"无法判。把性质写成具体的。
- 同义反复——凡是「理解了 prompt 就自动成立」的断言都证明不了什么。

**强（产物正确性）**：

- 必须出现的事实（"至少吸纳第 X 节的两个要点"）。
- 结构断言（"字数在 250-1500 之间"）——错输出会失败。
- **否定断言**（"没有引入无关章节的内容"）。
- frontmatter 检查（"含 title / status / created（ISO 8601）/ updated"）。
- 有界输出块（"最终消息含 `intent='create'` 的 JSON 对象"）。

**强（过程纪律）**：

- 边车产物 + 内容（".memlog.md 记下了定价决策及其被否掉的替代方案与理由"）。
- transcript 工具调用（"transcript 里有一次调 `diy-editorial-review` 的记录"）。
- 阶段顺序（"润色调用发生在 brief 落盘之后、最终 JSON 块之前"）。
- 只读不变量（"输入 brief.md 与夹具逐字节一致，且没有任何写操作指向它"）。
- **双向保真**（"memlog 里每条决策都反映在 brief 里，且 brief 里没有任何说法既不来自输入也不来自 memlog"）。

多数过程纪律检查其实是「确定性读 transcript 与文件系统」，grader 只需引证。

## 四模式细则

**baseline —— 技能 vs 裸模型。** 同一输入跑两遍：一遍把技能 stage 进清场目录，一遍什么都不 stage。裸模型是长期地板；技能只有做出裸模型做不到的东西才配存在。打不过就该退休，不是再打一个补丁。

**variant —— 全量 vs 精简最小版。** 用 `--variant-path` 指一个被剥到最小的同技能版本（或改动前的快照），同一输入对比。若是为了防护某维度而存在的那一节在两版之间打平 → 那节是装饰，裁掉；若精简版明显且稳定地更差 → 那一节挣到了自己的位置。这是「疑似仪式」变成可运行裁决的方式。

**quality —— 产物 vs rubric。** 单 config 的产物交给只读 grader 逐条判（契约见 `grader.md`）。

**trigger —— 描述在正确的问句上火、在其余问句上沉默。** 生成共享关键词的近邻正/反问句 → 分层切分 → 经 adapter 量真实触发 → 有界轮数内改描述（全流程见 `description-optimization.md`）。触发判定一律是「技能被拉进来了吗」，运行时差异在 adapter 缝后面。

## 让技能非交互地跑

单发模式需要技能**不停下来问**就把交付物做出来。多数多轮技能有 headless 旗标或关键词：从 input 里触发它——开头一句 `Run headless.`、技能自己 headless 段里的关键词、或者给足上下文让它没什么可澄清的。`state_prefix` 也在这帮忙：一轮里已经给出它要问的答案，跑就不会停。技能没有 headless 路径、input 又满足不了它的问题时，要么给技能加 headless 模式，要么承认这个 case 需要人在环里。
