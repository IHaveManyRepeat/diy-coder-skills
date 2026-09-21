# Step 3 — 校验（Validate）

Progress: `构思会话 → 落计划 → [校验] → 终门与交付`

**Read (input):** 计划文件；计划声明的每个技能 `SKILL.md` 的 frontmatter；改稿前的旧计划（若本次是改既有计划）。
**Write (output):** 计划文件的修正（**只改计划自己**）；给用户的三档处置清单。

## 跑引擎

```
python "{project-root}/.claude/skills/diy-bmb-module/scripts/bmb_module.py" check --project-root "{project-root}" --output-dir "{output_dir}" --json
```

`check` **全程只读**：它不写任何被校验技能的文件（frontmatter 亦然），也不动计划文件。回执给出 `violations[]` / `warnings[]` / `counts`。

改既有计划时先留痕再校验（顺序不能反）：

1. `cp {output_dir}/module-plan.yaml {output_dir}/module-plan.yaml.prev`
2. 改计划 → 跑 `check --previous {output_dir}/module-plan.yaml.prev --json`（退出 0 = 技能清单无收缩）
3. 删 `.prev`

旧稿有而新稿无的技能条目 → `ID_UNSTABLE`。**收缩不是错，没留痕才是**：条目保留在新稿里并标 `dropped: true`，再跑一次即放行。

## 三档处置

| 档 | 落点 | 怎么处置 |
| --- | --- | --- |
| **违规**（退出 1） | 计划自身写错：schema 缺项 / 引用越界 / 新建技能六字段缺失 / 双向不对称 | 改**计划**（或由用户改技能），重跑 |
| **warning** | 计划声明的技能尚未建造（`MISSING_FILE`）；存量技能或计划外对端缺字段；引用已装技能 | 转述给用户即可，**不阻断**；不要为了消 warning 去改任何技能文件 |
| **过** | — | 进 step 4 |

两条不许碰的线：

- **不碰存量。** 存量技能缺 frontmatter 六字段是既成事实（14 个既有技能零字段），本技能零写面改不了——引擎只记 warning。
- **不为消 warning 而新建空技能目录。** 「计划先于建造」是计划器的常态；技能由 `diy-bmb-builder` 按 `build_order` 造。

## 读回执的三个面

- **引用闭包**：`depends_on` / `dependencies` / `build_order` 里的名字要么在本计划内，要么是已装技能；两样都不是 → `UNKNOWN_ID`，是拼写错还是漏登记，当场判。
- **注册面**：计划内技能两两之间的 `precededBy` / `followedBy` 必须双向对称（A 的 followedBy 指向 B ⟺ B 的 precededBy 回指 A）；不对称 → `SET_MISMATCH`，改计划或提给用户改技能。相位 `any` 与 `anytime` 是同一档，不是差异。
- **计数**：`counts.checked` 是本次实际校验的记录数（`--id` 可缩域；缺省逐条全查、不取最新）。

## 播报与下一步

给用户一句话：违规几条、warning 几条、还差什么才能定稿。

读全并照做 `./04-finish.md`。
