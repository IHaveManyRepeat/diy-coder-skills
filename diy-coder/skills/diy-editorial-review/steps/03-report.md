# Step 3 — 落盘与交付（Report）

Progress: `定位与定档 → 两透镜分析 → [落盘与交付]`

**Read (input):** 记录里的两槽 findings；引擎 `check` 的回执。
**Write (output):** `{output_dir}/editorial-review.yaml` 定稿（记录级 `status: 已定稿`）；渲染；交付摘要与路由。

## 定稿

1. `open_questions` 收尾：需作者拍板的（`QUESTION` 类建议的悬置项、拿不准的修订）写进这里。
2. 记录改 `status: 已定稿`，`project.updated` 改今天（记录级 `date` 不动——它记的是本次评审的日子）。
3. 全文零 `[假设]` 字面量（存疑走 `open_questions`）。
4. `estimated_reduction_words` 与 `findings` 的 `impact_words` 之和核对一致（都填时）。被 `diy-product-brief` 调用时，本步就是终门步——不回头问用户。

## 终门

```
python "{project-root}/.claude/skills/diy-editorial-review/scripts/editorial_review.py" check --final --project-root "{project-root}" --output-dir "{output_dir}" --json
```

`exit 0` 是唯一放行。违规 → 按回执的 `where` 就地修，重跑，直到 exit 0。不得跳过。

## 渲染

```
python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"
```

静默执行，不进浏览器、不等路径、不阻塞。

## 交付摘要

按源文固定格式给一份能直接决策的摘要（用 `document_output_language`）：

```
本文档摘要
- 目的：<一句话> ｜ 读者：<谁> / reader_type <人类|LLM>
- 结构模型：<五模型之一> ｜ 现状：<N 节 · M 词>

结构建议（按优先级）
#1 CUT <章节名> — <理由一句>（~X 词；理解力提示：<有则写>）
……

文风建议（三列）
| 原文 | 建议 | 改动说明 |
|---|---|---|
……

汇总
- 建议 N 条（结构 A / 文风 B）｜ 估计净削减 X 词（原稿 M 词的 Y%）
- 长度目标：<达标 / 未达标 / 未设目标>
- 理解力权衡：<哪些削减动了理解或参与感>
```

模型 / 读者档 / 建议计数以记录与回执为准，不凭记忆重打。两透镜都没挑出问题时照给摘要，明说「未发现需要改的地方」——这是合法完成，不是错误，也绝不编造发现凑数。

## 路由

- **施加者**：findings 是建议——目标文档由**它的持有者或用户**改；本技能不改 target，目标若是 diy 产物，改动与它的 `revisions` 条目都由持有者写。
- **被 `diy-product-brief` 调用**：施加归调用方（①结构 → ②语气与惯例 → ③文字机械层三遍顺序，先 `brief` 再 `addendum`）；本技能到此为止，不重复施加。
- 想再审另一份文档 → 从 step 1 开始（铸下一条 `ER-###` 记录）；同一文档改动后要复审 → 同样新起一条记录，旧记录留痕。

## 播报与下一步

这是最后一个步骤文件——终门 exit 0 后本轮到此结束。结论由记录的 `structure` / `prose` 两槽与 `open_questions` 承载；不再读任何 `steps/` 文件。
