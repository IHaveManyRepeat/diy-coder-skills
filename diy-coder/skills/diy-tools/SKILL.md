---
name: diy-tools
description: Internal deterministic CLI (diyc.py) for the diy-coder suite. Shared checker/writeback engine that host skills invoke for instance resolution, mechanical checks, TDD gates, static-check chains, and HALT writeback. Not user-facing - host skills call it, never the user for workflow decisions.
# ↑ 中文：diy-coder 套件的内部确定性 CLI（diyc.py）——宿主技能调用的共享检查器/写回器（实例解析、机械检查、TDD 门、静态检查链、HALT 写回）。非用户直调：宿主技能调它，用户不用它做工作流决策。
phase: anytime
precededBy: []
followedBy: []
required: false
line: any
outputs: —
---

# diy-tools — diyc 检查器/写回器（内部工具，非用户直调）

diy-coder 技能套件的内部引擎。宿主技能（diy-dev、diy-sprint、diy-review 等）调用它；用户绝不直接调用。全部规则与阈值都活在脚本里——本文件只声明命令面与调用路径。

## 调用

```bash
python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" <subcommand> [options]
```

通用选项（每个子命令都有）：`--project-root R`（缺省 `.`）、`--instance NAME`、`--json`（单行机器可读回执）。
退出码：`0` 正常 / `1` 违规或拒绝（非法状态迁移、未知 story、非法实例名）/ `2` 用法错误。

## 命令

| 命令 | 用途 |
| --- | --- |
| `resolve` | 解析 `output_dir`（配置 + 实例）。唯一的实例解析入口；宿主技能把回执里的 `output_dir` 当作自己唯一的读写根。 |
| `check --type T [--final] [--previous PA] [--story S-x] [--strict]` | T ∈ prd/architecture/openapi/epics/stories/test-plan/sprint/review 的机械检查。exit 0 是唯一放行；`--previous` 守护 ID 稳定；`--final` 跑终门义务清单。消费基线台账（见回执）。 |
| `trace [--src P]... [--strict]` | 拿 `# trace:` / `// trace:` 注释对账 stories/test-plan/architecture。未解析的 ID → exit 1。 |
| `static [--timeout 600] [--strict]` | 按序跑 test-plan 的 `static_checks`；出现阻断性失败即停链（后续层跳过）。 |
| `transition --story S-x --to STATE [--reason T] [--rounds N]` | HALT 状态迁移。`待审查→已完成` 在此被拒——走 `done`。 |
| `green --story S-x --tc TC-a --red "..." --green "..."` | 追加 red/green 证据；回填 test-plan 的 TC 状态。 |
| `done --story S-x [--rounds N]` | `待审查→已完成` 终态写回，含单一事实源回填。 |
| `bug-add --entry '<json>' \| --entry-file P` | 往 bug-log.yaml 铸造 BUG-0xx。 |
| `defer-add --entry '<json>' \| --entry-file P` | 把一个延迟动作排进 `deferred-actions.yaml`（铸造 `DA-0xx`；`reason` ∈ `用户配置`/`破坏性操作`/`越界改动`/`仅人工可做`）。凡是副作用纪律要求用户确认的动作：排队而非阻塞——用户稍后确认并自行执行。 |
| `defer-set --id DA-0xx --status 已完成\|已拒绝` | 翻转一条待确认动作的 `status`（`待办` → `已完成` = 用户已确认并自行执行 / `已拒绝` = 裁定不做）。单向：两个目标值是终态，再翻转判 `ILLEGAL_TRANSITION`。只动 `status`，动作本身永远由用户执行。 |
| `reconcile [--apply]` | sprint 任务对账 stories/test-plan（缺省 dry-run；`--apply` 才写）。 |
| `baseline-add --code C --where W --reason R` | 往 `{output_dir}/diyc-baseline.yaml` 追加一条已知遗留条目（落 `on`: 今天、`by`: 用户）。重复 `(code, where)` → `BASELINE_DUPLICATE`，台账损坏 → `BASELINE_INVALID`；两者均拒绝、零写入。只在用户明确批准后执行（规则 4）。 |

## 独立脚本

两个仓库根脚本与 `diyc.py` 一同分发（安装进 `scripts/`；**由人工手动运行**——宿主技能绝不自动调用）：

| 脚本 | 用途 |
| --- | --- |
| `runner.py` | 无头循环编排器：逐个把 sprint 任务推到终态（`已完成`/`已阻塞`）。可从 HALT 写回的 `sprint.yaml` 状态断点续跑；每任务重试次数有界。 |
| `exp-sync.py` | 经验库同步：把项目的 `bug-log.yaml` 条目推送进 `paths.experience_repo` 指向的共享仓库（按 subclass 分桶；`taxonomy.yaml` 自动扩展）。 |

## 回执

带 `--json` 时，每个命令输出一行 JSON：`{ok, command, project_root, output_dir, instance, violations[], warnings[], counts{}, ...}`。违规形如 `{code, where, msg}`，`where` 用正斜杠、相对 project-root。不带 `--json` 时：一条违规一行（`CODE where: msg`），最后一行摘要。

审计类命令（`check`、`trace`、`static`）还会消费基线台账 `{output_dir}/diyc-baseline.yaml`——用户批准过的已知遗留条目（`code`、`where`、`reason`、`on`、`by`）。某条违规的 `(code, where)` 命中台账条目即降级进 `known[]`（携带该条目的 `reason`）并计入 `counts.known`——那里的条目是已批准的欠债、不是待修违规，永不影响退出码。一条台账条目未被命中、而本次运行在该条目所在的文件范围内仍报同一个 code，它就成了 `BASELINE_STALE`（exit 1）：删掉它，台账只减不增（范围匹配让 `trace` 这类命令不会误判无关条目；`check --story S-x` 是任务级抽查、完全跳过 STALE——收窄的运行证明不了某条目已悬空）。台账损坏或条目缺必填字段 → `BASELINE_INVALID`（exit 1）、整本台账失效——违规绝不被静默吞掉。降级只发生在判定层——明细数组与计数（`unresolved`、`layers`、`counts.unresolved` 等）照旧呈现本次运行观察到的东西；把它们读作事实，而非判决。写回类命令（`transition`、`green`、`done`、`bug-add`、`defer-add`、`reconcile`）不消费基线。`--strict` 完全忽略台账（不降级、不报 STALE），供发布/CI 复检。`baseline-add` 是台账唯一的写入者，且自身从不消费台账：只追加一条；重复 `(code, where)`（`BASELINE_DUPLICATE`）或台账损坏/非法（`BASELINE_INVALID`）一律拒绝、零写入；`output_dir` 缺失时拒绝（`MISSING_FILE`）而非代为创建。任何意外内部故障（权限、路径被目录占用、磁盘写满）都表现为一条 `INTERNAL_ERROR` 违规、exit 1、回执形状完好——绝不静默留空 stdout，绝不残留 `.tmp`。

## 规则

1. 零新增依赖——只用 stdlib + PyYAML；Python 3.10+。
2. 写回类命令只改动解析出的 `output_dir`；YAML 原子重写（`tmp` + 替换；写入失败时 tmp 文件会被清理）。注释不保留——产物不得依赖注释。
3. `scripts/` 下的文件是各道门的唯一定义源（例如 `Docs.story_covered` 同时驱动 TDD 门与 reconcile）。绝不在提示词里内联重新实现规则——调命令、读回执。
4. 基线条目只在用户明确批准后才写进台账——宿主技能提 `(code, where, reason)`、用户拍板、`baseline-add` 是唯一写入者；绝不为了过门把违规自行入册。

- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；不复述上游已写的信息（引用 ID）；不写没有信息量的套话。
