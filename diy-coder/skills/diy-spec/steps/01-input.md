# Step 1 — 输入判定与 slug 解析（Input）

Progress: `[输入与定位] → 蒸馏 → 两遍自校验 → 终门与交付`

**Read (input):** 用户输入（路径 / 粘贴内容 / 口述想法）与其点名要读的参考材料；`{output_dir}/spec-kernel.yaml` 的既有记录——**只读 `id` / `slug` / `status` 三字段**，不读全稿；`{output_dir}/project-context.yaml`（若有，背景线索，**只读**）。
**Write (output):** 新记录骨架（`new` 的 `SK-###`）或点名既有的 `SK-xxx`；更新路径的旧稿副本 `spec-kernel.yaml.prev`。

## 门禁（拒绝 = 一行诊断 + 零产出；不建记录、不写文件、不改任何东西）

| 情形 | 处置 |
| --- | --- |
| 无输入 | 交互式：问一次——贴路径 / 贴内容 / 口述想法，三选一；无头：拒绝，一行说明「输入不足以蒸馏成内核」（源 `insufficient_intent` 的人读形态） |
| 输入过薄（如「一个给徒步者的 app」，四周没有可蒸馏的语境） | 拒绝：本技能蒸馏，不引导——路由 `diy-prd` 先把愿景问出来 |
| slug 无头缺失且不可推 | 拒绝，一行说明「缺 slug」（源 `missing_slug` 的人读形态）——无头调用方须在输入里给出 |

## slug 纪律

`slug` 描述**被规格化的东西**，不是输入形态：

- 源文档已带 slug（如 `prd-foo-bar-2026-05-23/`）→ 继承（`foo-bar`）。
- 稀疏 / 会话内 / 多源输入 → 交互式问一次；无头由调用方在输入里给出。
- **同一 slug = 同一记录**：命中既有记录 → 就地更新（保持其 `id`、CAP 保留）；未命中 → 新建。

## 建 / 更判定

1. 找既有记录：跑 `check` 或直接读 YAML 的 `id` / `slug` / `status` 三字段（读到记录级即止）。产物不在场 = 本次是新建。
2. 命中既有 `slug`：
   - **更新路径**——改写那一条之前先留旧稿副本，供终门 `--previous` 比对 CAP 集合：
     `cp "{output_dir}/spec-kernel.yaml" "{output_dir}/spec-kernel.yaml.prev"`
     然后读该记录全文（`capabilities` 的 id 与 `retired` 标记是本次必须保留的资产）。
   - 记录已是 `已定稿` 且用户没给变更信号 → 先问要做什么（复核 `assumptions` / `open_questions`，还是改哪一段），不擅自重写。
3. 未命中 → 跑骨架命令铸号（**`SK-###` 由引擎铸造，不手搓**）：

```
python "{project-root}/.claude/skills/diy-spec/scripts/spec_kernel.py" new --slug "<slug>" [--title "<标题>"] --project-root "{project-root}" --output-dir "{output_dir}" --json
```

回执 `counts.id` = 本次铸造的 `SK-###`；同 slug 已存在 → 引擎拒绝（`DUPLICATE_ID`）并指出既有 `SK-xxx`——照它走回更新路径，别换 slug 硬建。

## 输入整理

把输入按来源列成一张清单，逐条标注它是什么（PRD / brief / 邮件 / 会议记录 / 会话口述 / 多源混合）——清单是 step 2 蒸馏的走查底稿，也是 `sources[]` 的候选。结构化且已分节的输入（上游技能产出的 PRD、brief）尊重作者的分节；混合输入（脑暴、纪要）由你在 step 2 自行分拣。

**可选素材（只读，缺席不阻塞）**：`{output_dir}/project-context.yaml` 在场时，作为 distillate 的**背景线索**可引用提及——引用它的 ID / 路径，不转抄内容；缺席不追问、不报错。同理 `{output_dir}/prd.yaml` / `{output_dir}/brief.yaml` 在场时可作为 distillate 源（只读）——它们仍是**源**，是否落 `sources[]` 按 step 2 的判据（已完全吸收才列）。

## 播报与下一步

一句话：本次是新建（`SK-###`）还是更新（`SK-xxx`）、slug 是什么、输入来自几处。

读全并照做 `./02-distill.md`。
