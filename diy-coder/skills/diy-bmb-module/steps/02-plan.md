# Step 2 — 落计划（Plan）

Progress: `构思会话 → [落计划] → 校验 → 终门与交付`

**Read (input):** step 1 铸的骨架记录；对话里的探索结论与评审结论。
**Write (output):** `{output_dir}/module-plan.yaml` 里该记录的 `title` / `vision` / `skills[]` / `dependencies` / `build_order` / `open_questions`。

## 就地编辑，不新建

改的是 step 1 铸的那条骨架记录（按 `slug` 认人）。**不要再跑一次 `new`**——重复 slug 会被拒。编辑直接用文件工具改 YAML（内容面归你，机械面归引擎）：

```yaml
  - id: MP-001
    slug: <不变>
    title: <计划标题>
    status: 草稿                     # 终门通过前一直是草稿
    date: YYYY-MM-DD
    vision: <一段：这批技能要解决什么、给谁解决>
    skills:
      - {name: diy-<name>, kind: 工作流|工具, purpose: <一句：它做什么>, brief: <自足 brief>, depends_on: [diy-<name>], dropped: false, new: true}
    dependencies: [diy-<name>]
    build_order: [diy-<name>]
    open_questions: [<未决问题>]
```

- `name` 写**完整技能名（含 `diy-` 前缀）**，hyphen-case、≤64 字符；`kind` 只能是 `工作流` 或 `工具`。
- `new: true` = **本批新建**（这批要造的）——它是六字段齐备判定的唯一入口，别对存量技能乱标；存量/对端写 `false`。
- `dropped: true` 只在「计划内移除、要留痕」时用（见 step 3 的 `--previous`）。默认 `false`。
- 依赖字段无内容写 `[]`，**不要省键**——缺键会被判缺字段。

落盘前先把**该记录的完整内容**（身份 + vision + 逐技能 brief + 路线图）在对话里整块过一遍给用户确认——理由同源侧纪律：写错的成本远高于看一眼的成本。

## 逐技能自足 brief

`brief` 的唯一判据：**不靠对话上下文，直接交棒给 `diy-bmb-builder` 也能造**。逐技能写满这六行（一行一事）：

- **目的** — 它给谁解决什么问题（不是「做什么」的清单）。
- **入口** — 用户说什么话触发它、给什么输入。
- **产物** — 落哪个文件 / 目录、什么形态（YAML / 项目文件 / 零产物）。
- **边界** — 它**不做**什么、和哪个已装技能容易混。
- **设计取舍** — step 1 架构建模时定下的取舍与理由。
- **依赖** — 依赖哪个技能（本批的写进 `depends_on`，已装的也写）。

一句话能说清就不写两句；`purpose` 是索引行，`brief` 是交棒行，不要把 `brief` 写成 `purpose` 的复述。

## 构建路线图

`build_order` 列**本记录声明的技能名**，按「先造谁」排。判据：被依赖的先造；无依赖关系时按能力闭环排（先造能立刻验证的那条链）。**只列计划内的技能名**——引用既有能力归 `depends_on`，不进 `build_order`。

## 播报与下一步

给用户一句话：计划落在哪、几个技能、造的第一件事是什么。

读全并照做 `./03-validate.md`。
