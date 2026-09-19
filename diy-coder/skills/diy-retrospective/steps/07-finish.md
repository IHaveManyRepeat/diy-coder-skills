# Step 7 — 终门与路由

Progress: `epic 发现 → 深度分析 → 连续性 → 回顾讨论 → 行动 → 就绪度 → [收尾]`

**Read (input):** 完整的记录；引擎的 `check` 回执。
**Write (output):** 记录上的 `status: 已定稿`；收尾摘要。

## 终门（机械）

先写 `status: 已定稿`——`已定稿` 是门检查的对象，不是门的产物——再跑：

```
python "{project-root}/.claude/skills/diy-retrospective/scripts/retrospective.py" check --final --project-root "{project-root}" --output-dir "{output_dir}" --json
```

exit 0 是唯一放行。逐条修完上报的违规再重跑。门要求的说白了就是：零 `[假设]`；`metrics` 与产物实际一致（`SET_MISMATCH` ＝ 数字被手工改过、或产物已前进——用新一次 `collect` 重取）；`readiness` 五键非空；至少一条带责任人的行动项；每个 `epic` / `evidence` / `next_epic.id` 引用可解析。JSON 回执（含计数）即收口证据。

渲染与收尾都等 exit 0。经 diy-viewer 渲染（静默旁路——只写命令，不新增浏览器交互点、不报路径阻塞等待、不等待）：

```
python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"
```

resolved 实例时附 `--instance <name>`。

## 保存并标记 epic 已回顾（源技能 step-11）

diy 里没有 `sprint-status.yaml`，也没有可翻的 retro 键：这条记录**就是**完成标记。`retros` 条目上的 `status: 已定稿`——加上它记下的这段过程——就是告诉下一个会话「此 epic 已回顾」的东西。绝不把状态写到别处（本技能对 `sprint.yaml` 零写入）。

## 收尾摘要

用用户的语言、照回执说清：

- epic 与其完成度（`stories_done / stories_total`，设了 `partial` 时一并给出）——绝不手工点数；
- 关键指标：轮数合计、阻塞数、augment 失败数、按类别分的缺陷；
- 找到的 pattern（含计数）与值得重复的亮点；
- 承诺：按类别分的行动项、按档分的准备项、关键路径项数；
- 就绪度结论一行，以及任何未解的阻塞；
- 重大变更检测的结论：零命中就明说下一 epic 的计划仍然成立；
- 记录落在哪。

开场先讲 epic 交付了什么——源技能在承诺之前先致意，本步照做：行动清单之前，`wins` 先得一句认可。庆祝不是装饰；它让同一份记录里的挑战可信。

## 路由（源技能 step-8 / step-10 / step-12 的交接）

- **`significant_changes` 非空** → 下一 epic 的计划可疑：路由 **diy-correct-course**，且交接形态是**一条 proposal 承载整批条目**——N 条 change 进同一条记录的 `impacts[]`（必要时加 `edits`），`mode: 批量`，绝不拆成 N 份提案。该 proposal 落定前，不动下一 epic 的工作。
- **`critical_path` 非空** → 那些项在先；它们是下一 epic 首个故事的前置条件。
- **缺用例**（某条阻塞点名某 AC 没有用例）→ 按该故事的 sprint 任务状态分：任务尚未 `已完成` 归 **diy-test-design**（Update 模式重推导覆盖）；任务已 `已完成` 归 **diy-augment**（augment 的硬门只收 `已完成` 任务——这条判据本身就是分界线）。
- **账本不对**（evidence、红绿先后、TC 状态回填有缺口）→ 先跑 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" check --type review --story <S-x> --json`（或 `--type sprint`）定位违规项，再按归属路由：evidence 红绿 / 齐备问题 → diy-review 的正常入口（任务在 `待审查` 态），任务已 `已完成` 则走 `--falsify`（唯一入口）；TC `status` 未回填 → 回该任务自己的绿线 / 定稿回填。
- **其余情况** → epic 循环继续：下一 epic 的故事走 diy-create-story → diy-dev，队列需刷时走 diy-sprint。
- **绝不**编辑本 retro 分析的产物——需要改它们的结论一律写成 `significant_changes` 条目、一律路由 diy-correct-course，owning skill 名写进该条目的 `recommended_action`。

若配置了 `paths.experience_repo` 且在场，一行提醒用户 `bug-log.yaml` 会喂养跨项目经验库即可（推送由他们决定）——本技能不同步任何东西。

## 播报与下一步

这是最后一个步骤文件——终门 exit 0 后本轮到此结束；去处按上面的路由清单交给对应技能，不再读任何 `steps/` 文件。
