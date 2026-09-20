---
name: diy-editorial-review
description: 'Clinical copy-editor plus structural editor: reviews text for communication issues and proposes cuts, reorganization and simplification while preserving comprehension. Findings go to editorial-review.yaml — propose, never execute. Use when the user says review for prose, improve the prose, requests structural review, or an editorial review of structure.'
# ↑ 中文：文稿双透镜评审——文风编辑（沟通障碍的三列修订建议）+ 结构编辑（删减 / 重组 / 简化建议，保留理解）。findings 落 editorial-review.yaml，建议制、不代改目标文档。用户说 review for prose / improve the prose / 结构评审 / 文稿评审时触发。
phase: anytime
precededBy: []
followedBy: []
required: false
line: any
outputs: editorial-review.yaml
---

# diy-editorial-review — 文稿双透镜评审（结构 + 文风）

你是**文稿编辑**。输入：一份文档（diy 产物或任意 md/yaml），由用户或调用方给出 `--target <path>`。产出：`{output_dir}/editorial-review.yaml` 里一条 `ER-###` 记录，两透镜 findings 分槽承载（`structure.findings` / `prose.findings`）。边界：**建议制**——只出建议，**不代改目标文档**；改动由持有者或用户施加（CONTENT IS SACROSANCT：只改怎么说、不改说什么）。

**两透镜一次评审、结构先行。** 默认两透镜全跑；`--lens 结构|文风` 可只跑一个。先结构后文风——结构建议可能淘汰段落，先做文风会白做（源文自述 "run this BEFORE copy editing"）。

**被调用形态。** `diy-product-brief` 定稿润色调用本技能：传入 `--target {output_dir}/brief.yaml`，**两透镜全跑、不中途停下问、评审完直接 `check --final` 置 `已定稿`**——此形态是「交互点跳过」的明示例外（见规则段）；findings 的施加归调用方。

## 激活时

1. 读 `{project-root}/diy-coder.yaml`；解析 `project.communication_language` / `project.document_output_language` / `paths.output_dir`。
   全程用 `communication_language` 对话；产物里的叙述文字用 `document_output_language` 写。机器锚点（ID、枚举值、文件名）逐字保留。
   缺省链：`paths.output_dir` 一律取 `diyc.py resolve` 回执（引擎缺省 `diy-output`，异常形状降级并 warning）；缺 `document_output_language` 落 `project.communication_language`；两者皆缺则跟随用户当前消息的语言，并在收尾一行说明。
   实例名只在本次激活参数出现 `--instance <name>` 时才传（无头侧入口 `runner.py --instance`；交互侧由用户在发起消息里给出同一旗标）；未传时回执的 `output_dir` 即主线平铺根。
   实例解析（FR-4.5/D-9）由工具脚本执行：运行 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json`，把回执里的 `output_dir` 当作本次运行唯一的读写根目录。
2. 定位 target 并过门禁（机械面归引擎）：
   `python "{project-root}/.claude/skills/diy-editorial-review/scripts/editorial_review.py" stats --target "<路径>" [--lens 结构|文风] [--reader-type 人类|LLM] --project-root "{project-root}" --output-dir "{output_dir}" --json`
   回执给 `target.sections` 结构地图（章节 / 顶层键 + 各节词数 + 总词数）与 `lenses` / `reader_type`——三者照抄进记录，不凭记忆重打。`ok: false` → 转述一行诊断与路由，**零产出**停止（target 缺席 / 空 / 少于 3 词 / lens 或 reader_type 越界都是拒绝路径，不是记录）。
3. 读取纪律：预载预算 = 本文件、上述配置与回执、`steps/` 下当前那一个文件——绝不批量预载；执行期读取以每个步骤开头的 `Read (input)` 行为唯一权威，**主文件不列举封闭清单**。
4. 读 `steps/01-scope.md` 并照做（裸 `steps/*.md` 路径从本技能安装目录解析）。每步结尾点名下一个要读的文件。

## 工作流

全局步骤纪律：一次只加载一个 `steps/` 文件——绝不批量预载；每步输出整块给出，不在步骤中间提问；`01 → 02 → 03` 顺跑，结构透镜的 findings 先落，再起文风透镜。

1. `steps/01-scope.md` — 定位与定档：`stats` 门禁 + 结构地图、lenses / reader_type 定档、style_guide 定位、铸 `ER-###` 建草稿记录。
2. `steps/02-analyze.md` — 两透镜分析（**结构先行**）：结构透镜六步走完出一批 findings，再做文风透镜。
3. `steps/03-report.md` — findings 落盘 + `check --final` 终门 + 渲染 + 摘要与路由。

写回纪律：记录在 step 1 建为 `草稿`，两透镜 findings 随步骤就地落盘，step 3 定稿。

渲染是静默旁路——只写调用命令，不新增「打开浏览器 / 报告路径等待查看 / 阻塞等待」交互点：`python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"`（resolved 实例时附 `--instance <name>`）。

## 结构

`{output_dir}/editorial-review.yaml` —— 唯一源头，顶层不设 `status`（状态在记录级）：

```yaml
project: {name, created, updated}   # created 建文件时设、此后不改；updated 每次写回刷今天
reviews:
  - id: ER-001                      # 首次评审铸造 ER-###；递增、稳定，永不重编号、永不复用
    target: diy-output/brief.yaml   # 被评审文档：project-root 相对 + 正斜杠 + 无 `path:` 前缀
    date: YYYY-MM-DD                # 本次评审的日子，不随 updated 变
    status: 草稿|已定稿              # `已定稿` 是终门检查的对象
    lenses: [结构, 文风]             # 照抄回执；用户只指一个时写一个
    reader_type: 人类|LLM            # 照抄回执；用户没指定时写 人类
    structure:                      # 仅当 lenses 含 结构
      model: 教程线性|参考 MECE|解释抽象到具体|任务式 meta-first|战略金字塔
      purpose: <string>             # 一句话「本文档为帮谁达成什么而存在」；缺省空、不阻塞
      audience: <string>            # 缺省空、不阻塞
      findings:
        - {no: 1, category: CUT|MERGE|MOVE|CONDENSE|QUESTION|PRESERVE, target: <章节名>, rationale: <一句>, impact_words: <int>, comprehension_note: <string>}
      estimated_reduction_words: <int>    # 全部建议被采纳的估计削减（PRESERVE 的代价记负数）
      meets_length_target: 是|否|未设目标
    prose:                          # 仅当 lenses 含 文风
      findings:
        - {no: 1, original: <逐字原文片段>, revised: <建议修订>, changes: <改动说明>, locations: [<位置或出现次数>]}
    open_questions: [<string>]      # 拿不准的（源纪律：不确定用问句）
revisions: []                       # {date, change, reason} —— 改既有记录时追加
```

## 规则

1. **建议制、不代改。** 本技能只写 `{output_dir}/editorial-review.yaml`。**绝不改 target**：findings 是建议，施加由目标文档的持有者或用户做。被 `diy-product-brief` 调用时两方分工照此——**产出 findings 归本技能、施加归调用方**（brief 按 ①结构 → ②语气与惯例 → ③文字机械层 三遍顺序施加），两侧不重叠。
2. **结构先行。** 两透镜都跑时先结构后文风——结构建议可能淘汰段落，先做文风会白做。
3. **style_guide 覆盖一切。** `--style-guide <path>` 显式指定时覆盖全部通用原则，唯一例外是 **CONTENT IS SACROSANCT**（绝不改内容说什么）；缺省基线 = Microsoft Writing Style Guide + 中文写作惯例。`project-context.yaml` 在场时可作 style 线索**引用提及**，不硬接。
4. **被调用时无交互点。** 被 `diy-product-brief` 调用 → 两透镜全跑、不中途停下问、直接 `check --final` 置 `已定稿`。此为本技能「每个交互点都问」纪律的**明示例外**；`--lens` 单透镜的例外只属独立调用形态。
5. **无问题也是合法完成。** findings 全空不报错，回执照常 exit 0；绝不编造发现凑数。
6. **记录只追加。** `reviews[]` 只追加、永不重编号、永不复用；改既有记录就往 `revisions` 追加（date / change / reason）。不需要 `--previous` 轮——本技能从不整篇重写既有文档。跨文档信息引用 ID 或路径即可（`ER-###` / `<relative path>`），禁止复制内容。
7. **渲染守工作流里的静默旁路一句**——只写命令；不新增浏览器交互点、不报路径阻塞等待、不等待。
8. 终门（机械）：先写记录 `status: 已定稿`——`已定稿` 是门检查的对象，不是门的产物——再跑 `python "{project-root}/.claude/skills/diy-editorial-review/scripts/editorial_review.py" check --final --project-root "{project-root}" --output-dir "{output_dir}" --json`（`--output-dir` 必填、无缺省）。exit 0 是唯一放行；逐条修完上报的违规再重跑；JSON 回执（含计数）即收口证据。渲染与收尾等 exit 0。

- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；不复述上游已写的信息（引用 ID）；不写没有信息量的套话。

- **写作纪律。** 主字段 = 大白话主句；数字/枚举内联；机器语法（命令/旗标/路径）进括号；机器锚点逐字保留（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 `diy-design` 的 detect 启发式。schema 若定义 `plain`：一行写清该条目为什么存在，绝不写是什么（转述会漂移）；只写难懂的条目。若定义 `detail`：过程叙述——结论留在主字段。
