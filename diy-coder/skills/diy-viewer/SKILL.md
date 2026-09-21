---
name: diy-viewer
description: Render diy-coder YAML artifacts (prd.yaml, architecture.yaml, etc.) into human-friendly HTML (browser auto-opens in interactive terminals only; AI/automated runs render silently). Use when the user asks to view/see/preview any diy-output document, or after any diy-* skill produces or updates a YAML artifact.
# ↑ 中文：把 diy-coder 的 YAML 产物（prd.yaml、architecture.yaml 等）渲染成人类友好的 HTML（浏览器只在交互终端自动打开；AI/自动化运行静默渲染）。用户想查看/预览任何 diy-output 文档，或任何 diy-* 技能产出/更新了 YAML 产物之后，触发本技能。
phase: anytime
precededBy: []
followedBy: []
required: false
line: any
outputs: —
---

# diy-viewer — YAML 单一源 → HTML 人类友好投影

你是一个薄启动器。YAML 文件是唯一事实源；本技能绝不编辑它们——只渲染一个视图。

## 运行

不改工作目录、恰好执行一次（把 `{project-root}` 换成项目根的绝对路径）。缺省形态是主线；激活时解析过实例名就用实例形态——同一命令行加 `--instance <name>`（绝不退回主线路径）：

```bash
# 主线
python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"

# 实例（同一命令行 + --instance <name>）
python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}" --instance <name>
```

行为：

- `--instance <name>`：把该实例的产物从 `<output_dir>/<name>/` 渲染到 `<output_dir>/<name>/.view/`（FR-4.5/D-9）。不带它：渲染主线平铺的 `output_dir`。
- 调用方义务：激活时解析出实例名的 diy-* 技能，必须在自己的渲染调用上追加同一个 `--instance <name>`——绝不静默回落主线。实例目录解析与实例名校验是 viewer.py 的职责。
- 可选显式文件：在命令后追加它们的路径，即只渲染这些文件。

## 规则

- 渲染命令要求宿主 Python 装有 PyYAML。若因 `ModuleNotFoundError` 失败，报出该错误并建议 `pip install pyyaml`。不得静默回落。
- 若 `paths.output_dir` 缺失或其下没有 YAML 文件，告诉用户扫描的是哪个目录，并建议先跑一个 diy-* 工作流；不得编造内容。
- 只在用户明确要求打开浏览器时才传 `--open`；`--no-open` 一票否决（即使同时给了 `--open`）。
- 渲染完，用 `project.communication_language`（取自 `diy-coder.yaml`）回一行摘要：渲染了哪些文档、HTML 落在哪里。例外——自动化/无头渲染（另一个技能流程里的渲染步骤、runner 驱动的会话）保持静默：不报路径，直接继续；渲染只是旁路一步，绝不阻塞流程。
- 本技能不写任何 YAML 散文；HTML 投影的外壳标签按设计固定为中文（展示层的选择——`document_output_language` 管的是源产物里的散文，不是 viewer 外壳）。
- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；不复述上游已写的信息（引用 ID）；不写没有信息量的套话。
