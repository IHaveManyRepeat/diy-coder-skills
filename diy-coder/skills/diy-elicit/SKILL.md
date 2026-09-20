---
name: diy-elicit
description: 'Push the LLM to reconsider, refine, and improve its recent output: pick 5 methods from the 69-method library that fit the current section, apply them one at a time, and hand the enhanced version back to the invoking skill. It has no write surface — the enhanced content stays in the conversation and the artifact owner persists what it accepts. Use when user asks for deeper critique or mentions a known deeper critique method, e.g. socratic, first principles, pre-mortem, red team.'
# ↑ 中文：对当前内容做深挖增强——从 69 方法库选 5 个贴合当前 section 的方法、一次一个地套用，把增强版就地交还调用方。零写面：增强结果留在会话里，落盘归产物持有者。用户要做更深批判、或点名某个方法（socratic / first principles / pre-mortem / red team）时触发。
phase: anytime
precededBy: []
followedBy: []
required: false
line: any
outputs: —
---

# diy-elicit — 内容深挖增强（零产物）

你是**内容深挖增强器**：输入当前 section（调用方在会话里给出的内容，或 `--target <path>` 指向的文档段），按上下文从 `methods.csv`（69 方法 / 12 类）选 5 个方法、一次一个地套用，把增强版就地呈现并交还调用方。增强对象即内容本身，不涉跨文档引用。**本技能不改任何文件**——被调用时增强版即该 section 的最终版本，落盘由调用方（产物持有者）或用户自己做，改动记入该产物 `revisions` 段；独立使用时增强结果只在会话中呈现。

## 激活时

1. 读 `{project-root}/diy-coder.yaml`；解析 `project.communication_language` / `project.document_output_language` / `paths.output_dir`。
   全程用 `communication_language` 对话；产物里的叙述文字用 `document_output_language` 写。机器锚点（ID、枚举值、文件名）逐字保留。
   缺省链：`paths.output_dir` 一律取 `diyc.py resolve` 回执（引擎缺省 `diy-output`，异常形状降级并 warning）；缺 `document_output_language` 落 `project.communication_language`；两者皆缺则跟随用户当前消息的语言，并在收尾一行说明。
   实例名只在本次激活参数出现 `--instance <name>` 时才传（无头侧入口 `runner.py --instance`；交互侧由用户在发起消息里给出同一旗标）；未传时回执的 `output_dir` 即主线平铺根。
   实例解析（FR-4.5/D-9）由工具脚本执行：运行 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json`，把回执里的 `output_dir` 当作本次运行唯一的读写根目录。
2. 定位增强对象，三档：
   - 激活参数有 `--target <path>` → 只读该文档（project-root 相对路径），按用户点名的段增强。
   - 被别的技能调用 → 用调用方在会话里给出的当前 section 内容。
   - 独立使用且无对象 → 问一次：贴内容 / 给路径 / 取消；等用户回话。
3. 硬门：增强对象在场且 ≥1 句。
   - 满足 → 继续第 4 步。
   - 空对象 / <1 句 → 一行说明 + **零产出**停（不代拟内容）。
4. 本技能无 `steps/`（源即单文件短流程），母本 §4 读取纪律按「无 steps 永久不适用」分支：材料面 = 本文件 + 方法库（经引擎读，不预读 CSV 全文）。
5. 读 `## 工作流` 并照做。

## 工作流

全局步骤纪律：一次只套用一个方法、输出整块给出；方法始终贴合当前 section；机器锚点（命令 / 旗标 / 方法名）逐字保留；对话用 `communication_language`。

1. **智能选 5**（主体是你，不是引擎）：看内容类型 / 复杂度 / 利益相关方 / 风险 / 创意潜力，从方法库描述里匹配 5 个，基础与专门技法搭配；`methods --random 5` 是抽样兜底面。
2. **呈现菜单**（每次执行后重现同一菜单）：
   - `1-5` → 执行第 3 条。
   - `r` → `methods --random 5` 换新 5 个（尽量跨类别）。
   - `a` → `methods --all` 全列 69 个，按名称或编号选。
   - `x` → 交还（第 5 条）。
   - 直接给改动意见 / 给多个编号（如 `1,3`）→ 就地改或按序执行，再重现菜单。
3. **执行方法**：以 CSV 的 `description` 为理解源、`output_pattern` 为弹性流程引导；复杂度随内容伸缩；多视角方法**明确各视角立场**（与 `diy-party-mode` 的视角制同源）。执行后先展示增强版（这个方法揭示了什么、改进了什么），再必问「是否应用（y/n）」——仅 y 视为接受（改动点进交还块），否则丢弃，其他回复照用户指示办。
4. **回到菜单**（迭代循环）：每次套用都建立在上一版增强之上，直到用户选 `x`。
5. **交还**（`x`）：按 `## 结构` 的交还块交出增强版与建议改动点。

## 结构

**零产物、零写面**——没有 YAML 单一源（本段不写 schema）：增强在会话内完成，交还块是唯一交付形态，落盘归产物持有者。

```
【交还】增强对象：<section 名 或 --target 路径>
增强版：见上文（本技能不落盘）
建议的改动点：
- <一句一条，供持有者落盘并写进该产物 `revisions` 段>
```

方法库 `methods.csv`（69 方法 / 12 类）与 `scripts/` 平级；路径由引擎自身位置推算，两种安装布局同构。

## 规则

1. **零写面**：本技能不改任何文件——不写 `{output_dir}`、不改被增强对象、不建 md；`revisions` 由持有者记。被调用时，交还即职责完成。
2. **门禁与终门**：空对象 / <1 句 → 一行说明 + 零产出停；独立使用先问一次。**无终门**——引擎是只读工具（无 `check`），本技能无产物可校验。
3. **引擎**（只读）：`python "{project-root}/.claude/skills/diy-elicit/scripts/elicit.py" methods [--random N | --category C | --all] [--json]`——库加载 / 随机抽 N / 按类筛选 / 全列；`--category` 取库内中文类名，非法值 exit 1 + `ENUM_INVALID`；exit 0 = 回执可用。
4. **无渲染**：零产物 → 无渲染步骤（母本 §5 不适用），不调用 viewer、不新增「打开浏览器 / 报告路径等待查看 / 阻塞等待」交互点。
5. **边界**：`diy-editorial-review` 只出建议、不代改 target；本技能就地增强当前内容并交还——两者都不把改动落盘。要多视角碰撞走 `diy-party-mode`；`diy-brainstorm` 的深挖入口调用本技能。
6. **一次一个对象**：换增强对象先交还，再重开菜单。

- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；不复述上游已写的信息（引用 ID）；不写没有信息量的套话。

- **写作纪律。** 主字段 = 大白话主句；数字/枚举内联；机器语法（命令/旗标/路径）进括号；机器锚点逐字保留（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 `diy-design` 的 detect 启发式。schema 若定义 `plain`：一行写清该条目为什么存在，绝不写是什么（转述会漂移）；只写难懂的条目。若定义 `detail`：过程叙述——结论留在主字段。
