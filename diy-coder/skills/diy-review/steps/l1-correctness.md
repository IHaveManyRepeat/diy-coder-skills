# Step — L1 正确性（Correctness）

**Read (input):** 本任务实现面（取数口径 = 主文件规则第 2 条）；`stories.yaml` 的 AC 明细；`test-plan.yaml`；`trace` 回执。
**Write (output):** L1 findings（`layer: 正确性`）——`unresolved` 每条路由 `小修`；未兑现 then 子句的逐条点名。

- **L1 正确性。** 实现是否恰好做到了 AC 说的——没有漏掉的 then 子句、没有没被要求的多余行为？逐条 AC 对照。trace 纪律是抓手：diff 里每个方法都要带 `# trace:` 注释（见 diy-dev），其 ID 必须能在 stories / test-plan 里解析——跑 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" trace --src <本任务实现文件/目录> --json`（`--src` 可重复、相对 project-root；不给则扫全项目），把回执 `unresolved` 里的每一条当 finding（路由 `小修`）——该列表是**该扫描面**上的结果；`# trace:` 整行缺席仍属人对 diff 的目读。对被追踪的方法逐条核行为：声明 `AC-9.1` 却没兑现其 then 子句的代码，是一条点名该 trace 行的 L1 finding。
