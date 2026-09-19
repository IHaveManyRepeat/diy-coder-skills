# Step 5 — 追加 TC、机械门与摘要

Progress: `探测 → 目标 → 生成 API → 生成 E2E → [记录]`

**Read (input):** 已执行的用例及其实测状态；第 2 步的 AC 绑定；`test-plan.yaml` 既有的 TC ID。
**Write (output):** 用例 JSON 文件；`{output_dir}/test-plan.yaml` 里追加的 `test_cases` 条目；收尾会话摘要。

## 铸 TC ID——续号，永不复用

每条用例 `id = TC-{ac}.{seq}`：取 AC ID，去掉 `AC-` 前缀，保留点分编号，再接该 AC 的下一个序号。`AC-5.1` 已有 `TC-5.1.1` → `TC-5.1.2`。在 `{output_dir}/test-plan.yaml` 里按 AC ID 查既有最大号（按 ID 定位——不整篇重导）。永不重编号、永不复用、绝不回填被删用例留下的空档。

## 写用例文件

一个 JSON 文件，落在临时路径（绝不写进 `{output_dir}`）：

```json
[
  {
    "id": "TC-5.1.2",
    "title": "登录流程端到端",
    "ac": "AC-5.1",
    "type": "端到端",
    "priority": "P0",
    "technique": "场景",
    "kill_target": "用户旅程在中途静默中断（页面已跳转但状态未持久化）",
    "status": "通过",
    "steps": ["打开 /login", "填写表单并提交", "断言跳转且会话可复用"]
  }
]
```

顶层对象带一个 `test_cases` 键同样接受。本技能追加的每条用例，`type` 恒为 `端到端`、`technique` 恒为 `场景`；`status` 是实测结果，不是预期。`api | e2e` 生成层轴只落 `title`，不进 `type`（见 `./02-targets.md`）；`priority` 按 diy-test-design 的「priority 映射到风险」取值——唯一权威出处就是它，本技能只引用。

## 追加——机械门

```
python "{project-root}/.claude/skills/diy-e2e-tests/scripts/e2e.py" record --tc-file <cases.json> --project-root "{project-root}" --output-dir "{output_dir}" --json
```

exit 0 是唯一放行。引擎校验 id 规则与续号、`ac` 在 `stories.yaml` 的解析、`端到端`/`场景`/`kill_target`/`title`/`steps` 的必填与实测 `status`——每条用例都过才写；有任何违规 → exit 1、零写入、既有计划分毫不动。逐条修完上报的违规再重跑。

成功时回执带 `appended`、`counts.cases_total`，以及一个 `diyc` 块：引擎会经 `diyc.py check --type test-plan` 重查整条 `test-plan.yaml`。那里的违规是**要转述的 warning**（可能早于本次运行）——它们不推翻这次追加，但必须出现在收尾摘要里，绝不吞掉。

## 收尾

渲染（静默旁路——不报路径等待、不阻塞；headless 静默渲染）：`python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"`（resolved 实例时附 `--instance <name>`）。

摘要（就在对话里——本技能不另写摘要产物；BMAD 的 `test-summary.md` 由这份收尾报告加追加的用例取代）：

- 按 id 列出追加的用例，及其落地的文件（项目测试目录）。
- 执行结果：跑了几条 / 过了几条 / 红了几条，每条仍红的写明已做的修复或观察值 vs 预期值。
- 覆盖：确认过的目标清单里覆盖了几个特性，API 与 E2E 分列。
- 缺口与假设：跳过的目标及其原因，未决绑定的 `DA-###` 与用户的裁定，`diyc` 的 warning。
- 下一步（三步可达路径）：① 逐条报 `TC-x.y.z` 与它所属的 `S-x`，日常回归交给项目自己的 CI；② 故事仍在 `待审查` / `进行中` → 红用例本就是 diy-review L3 台账的材料，交给当前审查轮；③ 故事已 `已完成` → 入口是 `diy-review --falsify <S-x>`（唯一的 `已完成` 入口：命中即 `bug-add`，并把任务转回 `进行中`）。本技能零写 `sprint.yaml`。

## 播报与下一步

无——本轮到此结束。摘要期间若浮出新的目标，用户在 `./02-targets.md` 重新进入，而不是从探测步重来。
