# Kaizen 优先级框架（Impact × Effort × Learning）

`data/kaizen-principles.md` 第三节的展开。**唯一权威**——步骤文件与产物键都回到这里。

源 = `.claude/skills/wds-8-product-evolution/data/kaizen-principles.md` 的「Kaizen Prioritization Framework」节（276 行文件的主体段之一）+ 同技能 `steps-a/step-01-identify.md:92–104` 的同名三档表。

---

## 一、公式

```
Priority = Impact × Effort × Learning
```

三因子各取三档之一，**权重 5 / 3 / 1**，`score` = 三档权重之积（十个可能取值：{1, 3, 5, 9, 15, 25, 27, 45, 75, 125}）。

**三因子一律「越大越好」**——见第三节的口径归一。

---

## 二、三档量表

| 因子 | `high`（5） | `medium`（3） | `low`（1） |
| --- | --- | --- | --- |
| **Impact** | 解掉主流用户的痛点、动到关键指标 | 改善体验、指标小幅动 | 有更好、没有也行 |
| **Effort**（**省力度**） | 1–2 天能做 | 3–5 天 | 1–2 周 |
| **Learning** | 验一个重要假设 | 核一个既有假定 | 只是增量式改善 |

**读法**：`high` 的 Effort = **省力**（1–2 天）。把 `effort` 读成「工作量」会把公式读反。

---

## 三、口径归一（源侧两处表述互斥）

- 源 `kaizen-principles.md` 的表头写 `High / Medium / Low`，而正文把 Effort 的 `Low` 记作「1-2 days」、`High` 记作「1-2 weeks」；
- 源 `steps-a/step-01-identify.md:96–100` 的同名表把 Effort 的 `High` 记作「1-2 days」、`Low` 记作「1-2 weeks」。

**两处对 High/Low 的指向相反**，且公式是**乘法**——若按前一处读法（Effort 越大越优先），`score` 高就成了「最贵的先做」，与 Kaizen「小步快跑」自相矛盾。

**diy 归一**：**三因子统一为收益向**——`effort` 的取值语义是**省力度**，`high` = 最省（1–2 天，取 `steps-a` 那一处的口径，它才是 [A] 活动实际可加载路径上的表）。**公式名与乘法形态逐字保留**（它是本技能的方法签名）。

---

## 四、可机械的部分与不可机械的部分

**可机械（`check` 会判红）**：

| 判据 | 违规码 |
| --- | --- |
| `scale` 三因子的 5 / 3 / 1 权重逐格在场且取值正确 | `SET_MISMATCH` |
| 每条候选的三个因子取值 ∈ `high\|medium\|low` | `ENUM_INVALID` |
| `score` == 三因子权重之积（**重算，不信手填值**） | `SET_MISMATCH` |
| 每轮 `rounds[].target` 必须能在 `candidates[]` 里找到 | `SET_MISMATCH` |
| 定稿前 `candidates[]` 至少一条 | `EMPTY_FIELD` |

**不可机械（人工判定，本框架不假装能算）**：

- **某一因子该判 `high` 还是 `medium`**——这是人的判断：Impact 靠业务语境、Effort 靠对代码的熟悉度、Learning 靠「这个假设此前验过没有」。**本框架只保证排序的内部一致，不保证三档判定本身正确。**
- 落笔纪律：每个因子的判定**在会话里说一句理由**（写进候选的 `rationale`，不进机械判据）；说不出的，说明这个因子还没想清，先别填。

---

## 五、用法（步骤里的落点）

1. `steps/01-analyze.md` 第 2 步：五源列出候选，每条给三因子的**初判**。
2. `steps/01-analyze.md` 第 3 步：逐条定档 → 算 `score` → 按 `score` 降序呈批（**用户关卡 1**，一次只做一条）。
3. `init` 铸出 `kaizen_priority.formula` 与 `.scale`（机械骨架）；候选由会话写进 `.candidates[]`。
4. `steps/05-test.md` 第 5 步：测试中冒出的新需求**作为新候选追加**（`score` 照算），本轮不做。
5. `steps/06-finish.md` 第 2 步：下轮建议读候选清单，**逐条念 score** 再让用户点头。
