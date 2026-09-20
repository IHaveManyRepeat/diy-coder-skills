# Step 1 — 定位与定档（Scope）

Progress: `[定位与定档] → 两透镜分析 → 落盘与交付`

**Read (input):** 用户或调用方给的 target（`--target <path>`；对话里已点名的文档同效）；引擎 `stats` 的回执；`--style-guide` 指向的文档（若有）。
**Write (output):** `{output_dir}/editorial-review.yaml` 的草稿记录（`id` / `target` / `date` / `status` / `lenses` / `reader_type` / `open_questions`）；给用户的进度播报。

## 跑引擎

```
python "{project-root}/.claude/skills/diy-editorial-review/scripts/editorial_review.py" stats --target "<路径>" [--lens 结构|文风] [--reader-type 人类|LLM] --project-root "{project-root}" --output-dir "{output_dir}" --json
```

回执给出：结构地图（md 按 `#` / `##` / `###` 切节、yaml 按顶层键切节；每节词数 + 总词数）、本次 `lenses`、`reader_type`——三者照抄进记录，不凭记忆重打。

`ok: false` → 把违规码与消息转述给用户，零产出停止（这是拒绝路径，不是记录）。target 缺席 / 内容少于 3 词 / `--lens` 或 `--reader-type` 越界，都在这一步挡住。

## 定档

- **lenses**：默认两个全跑。用户说「只看结构」→ `--lens 结构`；说「只润文字」→ `--lens 文风`。被 `diy-product-brief` 调用时两透镜全跑、不问。
- **reader_type**：`人类`（缺省）= 清晰 / 流畅 / 可读优先，理解辅助要保留；`LLM` = 精确与无歧义优先（依赖优先、术语一致、去 hedging、显式结构）。判据 = 这份文档主要给谁读；答不上来 → 人类。
- **style_guide**：`--style-guide <path>` 给了就通读一遍，记下关键要求——它在本次评审里覆盖一切通用原则，唯独不覆盖 CONTENT IS SACROSANCT。没给 → 基线 = Microsoft Writing Style Guide + 中文写作惯例。
- **purpose / audience**：能问就问（结构透镜靠它判「这一节是否直接服务目的」）；被 brief 调用或用户跳过 → 留空，从内容推断，并在 `rationale` 里点明依据。

## 落草稿记录

文件不存在时建：`project: {name, created, updated}`（`name` 取自 `diy-coder.yaml` 的 `project.name`）+ 空 `reviews: []` + `revisions: []`。追加一条：

```yaml
  - id: ER-001            # 下一个 = 已有序号最大值 + 1，三位零填充；不重编不重用
    target: <project-root 相对路径，正斜杠，无 `path:` 前缀>
    date: YYYY-MM-DD        # 本次评审的日子，不随 project.updated 变
    status: 草稿
    lenses: [结构, 文风]     # 照抄回执
    reader_type: 人类        # 照抄回执
    open_questions: []
```

结构槽 / 文风槽随 step 2 落盘——槽在场本身就是「这个透镜跑过了」的凭证（终门核对 lenses 与槽一致）。

## 播报与下一步

给用户一句话：评审哪份文档、几个章节多少词、跑哪个（些）透镜、reader_type 定在哪档、下一步先做结构分析。

读全并照做 `./02-analyze.md`。
