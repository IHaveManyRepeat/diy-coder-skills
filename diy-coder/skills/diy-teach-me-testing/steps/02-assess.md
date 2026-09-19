# Step 2 — 学员画像采集（Assess）

Progress: `Init → [Assess] → Hub → Session → Completion`

**Read (input):** `progress.py status` 回执里的 `dashboard.learner`（已有画像，避免重复问已知项）；技能内 `curriculum.yaml` 的 `roles:` 段（四角色的 `focus_areas`，用来解释「为什么问这个」）。
**Write (output):** `learner` 区块——只经 `update --learner`（本步骤不碰其他区块）。

## 四问（一次一条，等答）

**这一层是需求确认，不是副作用**：问题没问完不得替用户默认，也不得自己编画像。逐条给选项、逐条校验，答完一条再问下一条。

1. **角色**（必填）：`QA`（QA 工程师 / 测试工程师 / SDET）、`开发`（软件开发者）、`组长`（技术负责人 / 工程经理）、`负责人`（研发负责人 / 总监）。答别的 → 重申四值，重复问到达标。用来选 `curriculum.yaml` 的 `roles.<R>.teaching_adaptations`。
2. **测试经验**（必填）：`入门`（刚接触）、`进阶`（写过测试、想提高）、`资深`（底子扎实、想学进阶）。这三值是 `learning_paths` 的键——它决定推荐顺序。
3. **学习目标**（必填，非空）：想达成什么。用户说得含糊就追一句，拿到一句可记的话为止。
4. **当前痛点**（可省）：说「没有 / 跳过 / 无」→ 记空列表；不给空字符串占位。

## 落盘（唯一通道）

```
python "{project-root}/.claude/skills/diy-teach-me-testing/scripts/progress.py" update --learner --role <QA|开发|组长|负责人> --experience <入门|进阶|资深> --goals "<目标>" [--pain-points "<痛点>"] ... --project-root "{project-root}" --output-dir "{output_dir}" --json
```

- `--goals` / `--pain-points` 可重复给（一次一个）。
- 引擎置 `learner.assessed` = 当日，并在写盘前跑一遍与 `check` 同源的校验：**角色或经验缺一 → `EMPTY_FIELD` 拒绝**（画像没采完不得置 `assessed`），零写入。撞到这个拒回说明第 1、2 问没拿到值——回去问，不要绕过引擎手改 YAML。

## 播报

复述画像（角色 / 经验 / 目标 / 痛点），一句话说明它会怎么改变后面的讲解与推荐顺序，然后进 Hub。

## 播报与下一步

读 `./03-hub.md` 并照做。
