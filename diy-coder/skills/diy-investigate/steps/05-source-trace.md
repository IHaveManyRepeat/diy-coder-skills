# Step 5 — 源码追踪

Progress: `确认输入 → 据点 → 边界 → 推理 → [源码追踪] → 结案`

**Read (input):** 记录的假设 + 证据；`collect` 回执的 `candidates` / `vcs.commits` / `files`；源码文件本身。
**Write (output):** 记录的 `evidence`（「已确证」的 `path:line` 条目）与 `conclusion` 骨架（`fix_direction` = 错误发源地 / 触发器 / 条件）。

## 首扫（并发——一条消息多个工具调用）

- 用精确错误串 grep——搜索面就是回执的 `files` 清单；
- glob 受影响目录找并行实现——回执的 `candidates` 里 `kind: parallel` 已点名（确认即可，不要重新发现）；
- `git log` 看近期变更——回执的 `vcs.commits` 已带来。

## 然后顺序做

读周边代码；顺调用链走；留意语言与进程的边界穿越（编译产物→脚本、IPC、宿主→设备、配置流）。每条「已确证」的观察落成一条 `evidence` 条目，`ref` 带 `path:line`。

## 按案件类型收窄

- **`探索` 模式** —— I/O 映射（触发器、输出、依赖）；高频词扫描；控制流过滤（分支、循环、错误处理、状态机转移）。交付物是区域模型，不是缺陷。
- **`症状驱动` 模式** —— 深度评估：根因在本地上下文里可达，还是需要更广的区域模型？浮出升级信号就上报；绝不静默扩大范围。trivial-fix 评估：off-by-one、缺一个空值检查、参数次序颠倒 → 一行建议或草稿 diff，写进 `conclusion.fix_direction`；比这更大的 → 停在根因面。

`fix_direction` 是**诊断产出**（指出缺陷位置与改法），不是 fix——草稿 diff 只作为该字段的**文本内容**，**绝不写入源码目录**；workaround / 缓解措施仍只在显式请求时生成（step 6），实施一律走 step 6 的路由（`diy-quick-dev` 等）。

**调查止于诊断——实现不在范围内。** 没有单独的 trace 章节：分级过的 `evidence` 列表本身就是追踪，错误发源地 / 触发器 / 条件各占 `conclusion.fix_direction` 的一行。

## 播报与下一步

完整读 `./06-report.md` 并照做。
