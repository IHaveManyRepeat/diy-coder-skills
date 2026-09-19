# Step 4 — 单节执行（Session）

Progress: `Init → Assess → Hub → [Session] → Completion`

**Read (input):** `curriculum.yaml` 里该节的 `objective` / `outline` / `prerequisites`；`quiz-questions.yaml` 里该节的 3 题（session 7 无题）；`templates/session-notes.md`；`status` 回执里的 `dashboard.learner`（决定讲解口吻）。
**Write (output):** `{output_dir}/notes/session-<NN>.md`（课堂笔记正文，本步骤唯一的散文落点）；进度文件里该节的行——只经 `update --session`。

## 开场与标记进行中

先播报：本节第 N 节、名称、时长、目标（取自 `curriculum.yaml`），以及本节先修是否已完成的提示（只提示、不拦）。

```
python "{project-root}/.claude/skills/diy-teach-me-testing/scripts/progress.py" update --session N --status in-progress --project-root "{project-root}" --output-dir "{output_dir}" --json
```

## 讲解（按角色适配）

- 从 `curriculum.yaml` 该节 `outline` 的每一条展开成一段讲解；`roles.<role>.teaching_adaptations.<N>` 是这一节对这个角色的讲法（视角、举例重心），照它调整，不要加戏。
- 教学资源引用对象是 **diy 技能与产物**：例如讲到用例就指 `diy-test-design` 与 `test-plan.yaml`，讲到红相脚手架就指 `diy-test-author`，讲到门就指 `diy-test-gate` 与 `test-gate.yaml`。**不出现源平台品牌字样，不给任何外部 URL**。
- 跨产物信息一律**引用 ID**（`AC-x.y` / `TC-x.y.z` / `FR-x.y` / `S-x` / `path:<相对路径>`），**禁止复制内容**——复述会漂移，引用才可校验。
- 讲完停一下问用户有没有疑问（有就答完再进测验），这一步不要跳过。

## 测验（第 1-6 节）

从 `quiz-questions.yaml` 取该节 3 题，**逐题问、逐题等答**（HALT）：给 A-D 选项，答完立刻反馈，再问下一题。

**每题最多 3 次作答机会**（源口径保留）：第 1、2 次答错只回一句「不对，再试一次」——**不公布正确答案、不给提示**；第 3 次仍错 → 公布正确答案与解析，该题记答错。3 次内答对（无论第几次）即记该题答对。答满 3 次仍错也要给答案再进下一题，不许卡在一题上无限重试。

- 计分：`score = round(答对数 × 100 / 3)`，典型值 0 / 33 / 67 / 100。**分数由答对数算出（答对 = 该题在 3 次机会内答对），不要手编。**
- 判线：通过 = `score >= 70`。**2/3 = 67 未达线**——3 题须全对（源文自述的 "2 of 3 correct" 与其算式矛盾，以算式为准）。
- 未达线 → **停下让用户选**，不自动通过、也不替用户决定：
  - **[R] 复习**：重讲本节要点（换个说法、换本角色的例子）→ 重测 3 题 → 用新分数继续。
  - **[C] 带分继续**：分数照记（写回时就是它），照常完成本节。
- 用户答完最后一题前，不得先写笔记或写回进度。

## 课堂笔记（先笔记、后写回）

按 `templates/session-notes.md` 的七段结构（本节目标 / 覆盖的关键概念 / 本节引用的教学资源 / 测验结果 / 实例 / 关键收获 / 下一个推荐课次）写 `{output_dir}/notes/session-<NN>.md`（NN = 两位零填充 session id；**固定命名，无 slug 变体**）。

- 模板里的占位符逐个填实：分数、日期用当次真实值；「下一个推荐课次」用 `status` 回执的 `next_recommended` 口径。
- **重做已完成的节 → 覆盖同名 md**（旧稿不留档）；变更痕迹由进度文件的 `revisions` 承担，不由 md 承担。
- 目录由 `init` 建好，**不要自建目录**，也不要改文件名。

## 写回（唯一通道）

```
python "{project-root}/.claude/skills/diy-teach-me-testing/scripts/progress.py" update --session N --status completed --score <0-100> --notes notes/session-NN.md --project-root "{project-root}" --output-dir "{output_dir}" --json
```

- `--score` 只在 `--status completed` 时接受；`--notes` 指向的文件须先在盘上（引擎会验在场），所以**先落笔记再写回**。
- 引擎自己重算 `sessions_completed` / `completion_percentage` / `next_recommended` 并追加重做修订——**这三值你一个字都不要写**。
- 回执 `ok: true` → 播报本节完成（分数 / 笔记路径 / 总进度 / 下一个推荐），然后回 Hub。

## 第 7 节的分支（无 quiz，主题探索）

第 7 节没有测验，也**不接受 `--score`**（`score` 恒 null，不参与平均分）：

- 从 `curriculum.yaml` 第 7 节 `outline` 的主题菜单里逐次挑一个主题展开，用户说停就停；**每展开一个主题计 1**，边数边记。
- 收尾时写 `notes/session-07.md`（同七段结构，「测验结果」段写「本节无 quiz，探索主题 N 个」），然后：

```
python "{project-root}/.claude/skills/diy-teach-me-testing/scripts/progress.py" update --session 7 --status completed --topics <N> --notes notes/session-07.md --project-root "{project-root}" --output-dir "{output_dir}" --json
```

- 完成判据 = `topics_explored >= curriculum.yaml` 的 `sessions[7].min_topics`（引擎在 `check` 里强制）。探索数不够就继续挖，或先把这一节留在 `in-progress`。

## Next

读 `./03-hub.md` 并照做（Hub-and-spoke：任何一节走完都先回 Hub）。
