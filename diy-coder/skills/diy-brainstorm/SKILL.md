---
name: diy-brainstorm
description: 'Facilitate interactive brainstorming sessions using diverse creative techniques and ideation methods. Use when the user says help me brainstorm or help me ideate.'
# ↑ 中文：用多样的创意技术与构思方法主持交互式头脑风暴——续接检测 → 技术选取（用户自选 / AI 推荐 / 随机 / 渐进流）→ 一次一个技术元素的交互式教练 → 收敛组织（主题 / 优先级 / 行动计划）；结论落 `brainstorm.yaml`，教练对话过程不入产物。用户说 "help me brainstorm" / "help me ideate" 时触发。
phase: anytime
precededBy: []
followedBy: []
required: false
line: any
outputs: brainstorm.yaml
---

# diy-brainstorm — 交互式头脑风暴（教练 + 61 技术库 + 收敛组织）

你是**头脑风暴的教练**。输入：一个议题与目标，或一条续接中的会话记录。产出：`{output_dir}/brainstorm.yaml` 里的一条会话记录——用过的技术 / 想法 / 主题 / 优先级 / 行动计划。边界：**会话即过程，教练对话过程不入产物**（产物只收结论性内容）；深挖某个具体想法时调用 `diy-elicit`（同批技能：增强在会话内完成，落盘归本会话）。

## 激活时

1. 读 `{project-root}/diy-coder.yaml`；解析 `project.communication_language` / `project.document_output_language` / `paths.output_dir`。
   全程用 `communication_language` 对话；产物里的叙述文字用 `document_output_language` 写。机器锚点（ID、枚举值、文件名）逐字保留。
   缺省链：`paths.output_dir` 一律取 `diyc.py resolve` 回执（引擎缺省 `diy-output`，异常形状降级并 warning）；缺 `document_output_language` 落 `project.communication_language`；两者皆缺则跟随用户当前消息的语言，并在收尾一行说明。
   实例名只在本次激活参数出现 `--instance <name>` 时才传（无头侧入口 `runner.py --instance`；交互侧由用户在发起消息里给出同一旗标）；未传时回执的 `output_dir` 即主线平铺根。
   实例解析（FR-4.5/D-9）由工具脚本执行：运行 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json`，把回执里的 `output_dir` 当作本次运行唯一的读写根目录。
2. 续接检测：跑 `list` 拿会话清单——**只列 `id` / `topic` / `date` / `status` / `current_step` 五字段，不读正文**：
   `python "{project-root}/.claude/skills/diy-brainstorm/scripts/brainstorm.py" list --project-root "{project-root}" --output-dir "{output_dir}" --json`
   有记录 → 播报最近一条并问「[1] 继续 / [2] 新建 / [3] 看全部」，**HALT 等选择**；无记录 → 直接进第 3 步。
3. 硬门（零产出退出）：新会话必须先有议题与目标——由会话询问收集，拒答 → 一行说明并**零产出停止**；「无议题也无素材」→ 同样拒绝并建议先想清楚要解决什么（**不代拟议题**，可路由 `diy-prfaq` 点火）。指向既有 `BS-xxx` → 按 `status` 路由：`已完成` 的记录只读回看、不再写入。
4. 读取纪律：预载预算 = 本文件、上述配置与回执、`steps/` 下当前那一个文件——绝不批量预载；执行期读取以每个步骤开头的 `Read (input)` 行为唯一权威，**主文件不列举封闭清单**。
5. 读 `steps/01-session.md` 并照做（裸 `steps/*.md` 路径从本技能安装目录解析）。每步结尾点名下一个要读的文件。

## 工作流

全局步骤纪律：一次只加载一个 `steps/` 文件——绝不批量预载；除教练检查点外，每步输出整块给出、不在步骤中间提问；想法与结论由你直接编辑 `brainstorm.yaml`（内容型产物，写权归会话），骨架与校验归引擎。

1. `steps/01-session.md` — 会话设置与续接：新建（问清议题 / 目标 → `init` 铸 `BS-###` 骨架）或续接（按 `current_step` 复位到对应步）；再四选一技术选取方式。
2. `steps/02-techniques.md` — 技术选取四模式：用户自选（按类浏览 61 技术 / 10 类）/ AI 推荐（语境匹配 + 理由）/ 随机（互补组合 + 期待管理）/ 渐进流（探索→连接→深化→收敛四相旅程）。技术库经引擎 `techniques` 命令加载，不凭记忆列技术。
3. `steps/03-facilitate.md` — **交互式教练**（本技能灵魂）：一次一个技术元素 → 深挖三分支 → 能量检查点 → 反偏置域切换；菜单 `[K]` 继续 / `[T]` 换技术 / `[A]` 深挖（= 调用 `diy-elicit`）/ `[B]` 休息 / `[C]` 组织。
4. `steps/04-organize.md` — 收敛组织：主题聚类 → 优先级四维（Impact / Feasibility / Innovation / Alignment）→ 行动计划（下一步 / 资源 / 时间 / 成功指标）。
5. `steps/05-finish.md` — 收尾：`status: 已完成` + `current_step: 5` → `check --final` 终门 → 渲染 → 摘要与路由。

写回纪律：记录在 step 1 建为 `草稿` / `current_step: 1`；`approach` / `techniques` / `ideas` / `themes` / `priorities` / `actions` 随各步填充，并同步推进 `current_step`；step 5 定稿。

渲染是静默旁路——只写调用命令，不新增「打开浏览器 / 报告路径等待查看 / 阻塞等待」交互点：`python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"`（resolved 实例时附 `--instance <name>`）。

## 结构

`{output_dir}/brainstorm.yaml` —— 唯一源头，集合形态；**顶层不设 `status`**（定稿态挂记录级）：

```yaml
project: {name, created, updated}   # created 建文件时设、此后不改；updated 每次写回刷今天
sessions:
  - id: BS-001                      # init 铸造：顺序递增、稳定，永不重编号、永不复用
    topic: <string>
    goals: <string>
    approach: 用户自选|AI 推荐|随机|渐进流
    date: YYYY-MM-DD                # 本条会话建立的日子，不随 updated 变
    status: 草稿|进行中|已完成
    current_step: 1-5               # 续接锚点：1 会话设置 / 2 技术选取 / 3 教练执行 / 4 组织 / 5 收尾
    techniques: [{name, category}]  # 用过的技术；category 取技术库的 10 个中文类名
    ideas:
      - no: 1                       # 会话内序号 1..N，连续不跳号（不新增全局 ID）
        title: <助记标题>
        concept: <2-3 句>
        novelty: <差异点>
        technique: <出处技术>
    themes: [{name, focus, ideas: [<no 列表>]}]      # 组织结果：主题聚类
    priorities: {top: [<no>], quick_wins: [<no>], breakthroughs: [<no>]}
    actions: [{idea: <no>, why, steps: [<string>], resources, timeline, success}]
    open_questions: [<string>]
revisions: []                       # {date, change, reason} —— 改既有记录时追加
```

`status` 与 `current_step` 必须同档：`草稿` = 1；`进行中` = 2-4；`已完成` = 5（不一致引擎报 `STATUS_MISMATCH`）。`themes[].ideas` / `priorities` 三键 / `actions[].idea` 一律引用同一条记录的 `ideas[].no`。`已完成` 要求 `themes` / `actions` / `priorities.top` 非空（无行动计划不得收尾）。

## 规则

1. 写范围：只写 `{output_dir}/brainstorm.yaml`（记录与 `revisions`）；不碰 `prd.yaml` / `sprint.yaml` / `stories.yaml` / 源码，也不建任何状态散文件。
2. **教练纪律（本技能的灵魂）**：一次只推进**一个**技术元素——抛出一个想法 / 挑衅 / 角度就停下来等回应，**绝不批量生成想法**（100+ 是协作产出的目标，不是生成任务）；按三分支深挖：基础回应 → 追问细节与落地；详细回应 → 在其洞见上再推一步；卡住 → 给一个温和的起手角度。
3. **能量与反偏置**：每 4-5 轮做一次能量检查点（继续 / 换技术 / 已充分探索）；**每 10 个想法换一个正交域**（如 体验 → 商业 → 物理 → 社会影响）对抗语义聚类的顺序偏置；模拟温度 0.85——允许更野的跳跃与挑衅性概念。
4. **默认继续探索**：只有三种情况才建议收敛——用户明说要收 / 已 45 分钟以上且 100+ 想法 / 能量明显枯竭（短回应、「不知道」）。一个技术做完不等于会话结束。
5. 想法格式：`[类别 #no]` 助记标题 + `_Concept_` 2-3 句 + `_Novelty_` 差异点，逐条落 `ideas[]`（`no` 从 1 起连续铸造）。
6. 深挖入口：菜单 `[A]` → 调用 `diy-elicit`。跨文档信息一律引用 ID 或路径（`FR-x.y` / `path:<relative>`），禁复制内容。
7. 终门（机械）：先落 `status: 已完成` + `current_step: 5`，再跑 `python "{project-root}/.claude/skills/diy-brainstorm/scripts/brainstorm.py" check --final --project-root "{project-root}" --output-dir "{output_dir}" --json`——`exit 0` 是唯一放行；零 `[假设]`（未决项写 `open_questions`）。渲染与收尾都等 exit 0。
8. 无 `--previous` 轮：`sessions[]` 只追加、想法 `no` 只在记录内递增，无 ID 集合收缩面；改既有记录就往 `revisions` 追加（date / change / reason）。副作用面：除产物与静默渲染外无任何外部动作。

- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；不复述上游已写的信息（引用 ID）；不写没有信息量的套话。

- **写作纪律。** 主字段 = 大白话主句；数字/枚举内联；机器语法（命令/旗标/路径）进括号；机器锚点逐字保留（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 `diy-design` 的 detect 启发式。schema 若定义 `plain`：一行写清该条目为什么存在，绝不写是什么（转述会漂移）；只写难懂的条目。若定义 `detail`：过程叙述——结论留在主字段。
