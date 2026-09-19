# Step 2 — Artifacts（工件分析：读结构化产物，引用不复制）

Progress: `Target → [Artifacts] → Code Survey → Compose → Finish`

**Read (input):** 回执的 `acs` / `tcs` / `decisions` / `prior` / `git` 块。
**Write (output):** 记录里的 `ac_refs` / `tc_refs` / `design_ref` / `decisions` / `prior_story`。

## 这次转换（先读它，再看各块）

源工作流加载规划 markdown（epics / PRD / architecture / UX），把与故事相关的上下文抄进故事文件——一份上游一改就漂的二手副本。diy 不抄：上游是结构化的单一源，所以上下文包按 ID **引用**它们，并证明这条故事知道自己的义务。

你的任务不是复述一条验收标准，而是把四件事说清：本故事必须满足哪些 AC、哪些测试验证它们、哪些决策约束它、前一条故事留下了什么。

绝不把 AC 的 `given/when/then` 粘进记录，绝不转述决策正文，绝不抄故事叙述。`ac_refs` 里的 `AC-3.1` **就是**那条验收标准——diy-dev 去 `stories.yaml` 读它。

## AC 引用

本故事的 AC，只取 ID，全部取（回执的 `acs` 块就是这份清单）。当某条 AC 带 `design_ref` 时，记录的 `design_ref` 指向服务本故事主界面的那个页面——多条 AC 绑了不同页面时取绑定最密的那一个。完整绑定集留在 `stories.yaml` 的 AC 上；此处不复制。

## TC 引用

`tc_refs` = 回执 `tcs` 的 ID：`ac` 属于本故事 AC 集的每个用例。diy-dev 跑之前 `status: 待办` 是正常的——不是要上报的问题。`tcs` 为空**才是**：没有测试验证本故事的 AC，sprint 的 TDD 门会扣住该任务。记进 `open_questions`（**不是** `risks`）——它必须在 final 前关上：解决后删行，或带 `[CLOSED]` 与所采取的决定；并把用户路由去 diy-test-design。

## 决策

`decisions` = 回执里适用的 `D-x`——适用性的判据是决策的 `affects` 与本故事 AC 的 `refs` 所指向的 FR/NFR 相交（两者都在回执里可见）。不是每条决策都归此处；不相干的决策是噪音，dev agent 反正会读到它。仍 `status: 待定` 的决策未经批准：它进 `risks`（第 4 步），绝不混进护栏里装作已定。

## 前序故事

回执的 `prior.ref` 是编号小于目标故事的里最高的那条。它的 `carryover` 行从回执里**在场且有值**的字段各起一行（`prior.task` 的既有键 `status` / `note` / `evidence`（红绿记录）/ `loop`（轮次与结果）/ `blocked_reason`；缺席或空值的字段跳过该行，`prior.task` 本身可能为 `null`）。每行点名其来源字段，例如 `sprint S-2 note：既有实现复用 src/app.py`，让 dev agent 去读证据而不是信一句摘要。没有值得带走的 → 省 `prior_story`；绝不写空壳。

## git 情报

`git.commits`（最近 5 次：subject + 文件）是模式证据，不是叙述：近期工作碰了哪些文件、用了哪些惯例、这类改动通常还会带上什么（测试、夹具、文档）。要紧的折进第 4 步的 `risks` / `verify`。绝不把提交信息粘进记录，绝不把提交信息当需求。

## 播报与下一步

读 `./03-code-survey.md` 并照做。
