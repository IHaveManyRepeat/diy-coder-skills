# Step 4 — Compose（风险、判据、人工确认）

Progress: `Target → Artifacts → Code Survey → [Compose] → Finish`

**Read (input):** 草稿记录、`collect` 回执，以及 `{output_dir}/test-plan.yaml` 的 `static_checks` 段（判据的取材面；test-plan 其余部分不读）。
**Write (output):** 记录里的 `risks` / `verify` / `open_questions`。

## 风险

实现里可能出什么错，取自现场勘察、决策与前序遗留：一条仍未批准的 `待定` 决策、一个行为容易被弄坏的文件、一条本故事即将开工却仍 `待办` 的 TC、一段历史上耗掉过一轮评审的遗留。每行都要可行动——盯什么、为什么——绝不复述 AC，绝不写严重度打分。没找到风险：列表留空，并在交付消息里说明；绝不为了填字段而编一条。

## 判据

命令级完成判据：diy-dev 实际会跑的命令，从 TC refs 的既有字段（`type`（`单元|集成|端到端`）/ `steps` / `technique`）与 `{output_dir}/test-plan.yaml` 的 `static_checks` 链推导（链的语义由 diy-test-design 定义，此处只引用、不重定义）。每条是一个命令，或命令加它的预期结果（`python -m unittest discover -s tests -v` — 全绿），绝不写「工作正常」。没人能跑的判据不是判据。

## 未决问题

起草当刻一切未决的事：空的 `tcs`（路由 diy-test-design）、一条按写法无法验证的 AC、一条仍在判断中的文件边界。它们在 final **之前**与用户关上——要么解决（删行），要么带 `[CLOSED]` 与当时所采取的决定记下处置。绝不留下悬空的问题，绝不把问题只留在对话里：未决项住在文件里。

## 可选：外部检索

源工作流的第 4 步（为最新库细节做联网检索）在此收敛。项目的技术栈事实住在 `architecture.yaml` 与 `project-context.yaml`，而无出处的「最新版本」说法烂得很快。若某条故事确实依赖这两份文档都没钉住的库行为，把它放进 `open_questions`，等 diy-dev 真正需要时去查该库自己的文档——绝不发明版本号、端点或 API 形状，绝不把发明的东西当既定事实写进上下文包。

## 人工确认

把整包作为一条消息铺开：故事与 epic、AC 与 TC 的引用、决策、各文件及其 `why`、风险、判据命令、未决问题。明说整包**不**包含什么——AC 正文、决策正文、故事叙述——因为那些离这里只有一个引用的距离，期待此处有副本的读者会去错地方找。

先请用户改文件清单（它是杠杆最大、也最容易勘察错的一项），再请改风险。用户的答复是任何改动的证据；改了文件集的修正会把你送回第 3 步重走，而不是静默就地改。

然后渲染（静默旁路——只写命令，不新增「打开浏览器 / 报告路径等待查看 / 阻塞等待」交互点）：

```
python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"
```

（解析出实例时附 `--instance <name>`）。

## 播报与下一步

读 `./05-finish.md` 并照做。
