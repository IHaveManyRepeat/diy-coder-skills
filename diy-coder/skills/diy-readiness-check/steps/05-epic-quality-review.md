# Step 5 — 史诗质量评审

Progress: `文档发现 → 需求清点 → 覆盖校验 → UX 对齐 → [史诗质量评审] → 总评与定稿`

**Read (input):** 回执（`epics` / `stories` 的 `diyc.check.violations`、`counts`）；`epics.yaml` 与 `stories.yaml`——每条史诗与故事；脚手架检查用 `architecture.yaml`。
**Write (output):** 质量类 finding（`area: epics` / `area: stories`）及其 severity。

这次评审自主跑——质疑一切、一处不让（源 step-5 §8）。机械形状检查（ID、枚举、AC 引用可解析）已经随 `diyc.check.violations` 到场；下面是你判而 diyc 判不了的那一层。

## A. 史诗的用户价值

逐条史诗问：标题是不是用户能做的一件事（而不是一个系统组件）？目标描述的是不是用户结果？单靠这条史诗，有没有人能受益？

红旗 → finding（源 step-5 §2.A）：

- "Setup Database" / "Create Models" —— 没有用户价值；
- "API Development" / "Infrastructure Setup" —— 技术里程碑；
- "Authentication System" —— 边界情形：判它交付的是用户可见的价值（登录 / 登出 / 账户）还是只有管道。

技术型史诗是**错误**，不是风格问题：`severity: 严重`。源规则是字面意思——去把它们找出来。

## B. 史诗的独立性

- 史诗 1 独立成立；史诗 2 只能使用史诗 1 的产出；史诗 N 绝不依赖史诗 N+1。
  「第 N 个」＝文件里的列表序（`epics[]` 的顺序；一条 epic 内按 `stories[]` 顺序）；ID 号只是稳定标识，**不是排序信号**。
- 要抓的：「史诗 2 需要史诗 3 的功能」、同一 epic 里的 story 引用了更晚 epic 的组件、史诗之间的循环依赖。
- 破坏独立性的前向依赖 → `严重`。

## C. 故事质量

**粒度。** 用户价值清晰；不靠将来某条 story 就能做完。"Setup all models" 不是用户故事；"Create login UI (depends on Story 1.3)" 是前向依赖——破坏独立性时 `严重`，只是粒度问题时 `高`。

**验收标准。** Given/When/Then 结构；每条 AC 可独立测试；错误条件被覆盖；结果具体。含糊的判据（"user can login"）、缺错误路径、happy path 不完整、结果不可度量 → `高`（源 "major"）；纯格式噪音 → `中` / `低`。

## D. 依赖

- 史诗内：故事 1.1 可单独完成；1.2 可用 1.1 的产出；没有任何东西等更晚的 story。
- 数据库/实体时机：每条 story 创建自己需要的东西；"create all tables in Story 1.1" → `高`。
- 跨史诗：某 story 依赖另一史诗尚未实现的功能 → `高`；颠倒史诗次序时 → `严重`。

## E. 实现相关的专项检查

- **脚手架（Starter template）**（源 step-5 §5.A）：取值路径 = 从 `architecture.yaml` 的 `stack[].choice` 里找脚手架/生成器/模板类的那一项。找到 → 史诗 1 的故事 1 必须是基于它的初始项目搭建（clone、依赖、初始配置），缺失 → `高`。找不到（`stack[]` 里没有任何脚手架类选择）→ 该检查不成立：一行说明后跳过，**不落 finding**——绝不为凑检查去猜一个脚手架。
- **绿地 vs 棕地**（源 step-5 §5.B）：绿地期望有初始搭建 story、开发环境配置与早期 CI/CD；棕地期望与既有系统的集成点、迁移/兼容 story。该有而缺 → `中`，并点名缺的是什么。

## F. 合规清单（逐史诗过）

- [ ] 交付用户价值
- [ ] 独立成立
- [ ] 故事粒度合适
- [ ] 无前向依赖
- [ ] 数据库表在需要时才建
- [ ] 验收标准清晰
- [ ] 与 FR 的可追溯性成立（diyc 的 AC `refs`）

每个没勾上的框都落成一条带具体例子与一行整改建议的 finding——绝不是泛泛的抱怨。

## Severity 对照表（源 step-5 §7）

| 源档位 | diy `severity` |
| --- | --- |
| critical violations —— 技术型史诗、前向依赖、史诗级大小的故事 | `严重` |
| major issues —— 含糊的验收标准、依赖将来 story、数据库时机 | `高` |
| minor concerns —— 格式、结构偏差、文档缺口 | `中` / `低` |

## 播报与下一步

读全 `./06-final-assessment.md` 并照做。
