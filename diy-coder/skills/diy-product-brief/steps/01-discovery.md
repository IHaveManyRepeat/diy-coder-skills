# Step 1 — Discovery（脑爆倾倒 + 风险校准 + 工作模式）

Progress: `[Discovery] → Draft → Finalize`（新建路径；更新从 step 4 进入，校验从 step 5 进入）

**Read (input):** 激活回执（`intent` / `route` / `counts`）；用户点名的任何源材料；`{output_dir}/project-context.yaml`（存在时）。
**Write (output):** discovery 消息；建 `{output_dir}/brief.yaml`，含 `project`（`status: 草稿`）与倾倒已填好的骨架。

## 开场

开场是给全貌留出空间，不是发问卷。

1. 请用户脑爆倾倒，一上来就问有没有现成材料——备忘、演示稿、转录稿、旧简报、聊天记录。给路径或直接粘贴都行，长文无妨。
2. 先读已有的，只问缺的。倾倒之后再问一句「还有别的吗？」——常能捞出差点被忘掉的东西。
3. 全貌上了桌再钻细节——过早问细颗粒的问题会打断倾倒，也会看漏整个房间。
4. 回声确认领域与形态（mobile / web / desktop / multi-surface / hardware / API——这东西**到底是**什么），以及各自如何影响打法。

## 给画面打底

- 倾倒期间用 web-research 子代理：竞品面貌、可比对象、现状——AI 尤其，训练数据一周就过时。子代理检索，母代理拿摘要；抽取，不吞入。
  子代理不可用 → 父代理内联跑同一批定向检索（竞品面貌 / 可比对象 / 现状），绝不阻塞流程；连内联检索也未跑时，在本步的 discovery 消息里**显式写明「本次未做外部核对」**，不静默。更新路径按第 4 步的 Discovery 姿态同理。
- 已落盘的项目上下文（可选）：`{output_dir}/project-context.yaml` 在场时读它的 `rules` 作背景意识——技术、领域、约束——不再问用户已经写下来的事。
- 深活（完整市场规模测算、穷尽式拆解）→ 建议走 `diy-research`；它是本套件的研究技能，不要在本步内联硬做。

## 读利害档位

趁早，用用户自己的话问：个人兴趣的项目（**个人兴趣**）、内部提案（**内部**）、投资人输入（**投资人**）、公开发布（**公开**）。这就是 brief.yaml 的 `stakes`，它校准余下全程顶得多狠。

## 给工作模式

倾倒记下、档位读出后，用用户的语言给两条路：

- **快速路径**——把剩余空档并成一两个问题，然后直接起草完整简报，推断处带 `[假设]`；用户审阅、再迭代。适合「我明天就要路演」。
- **陪跑路径**——一起走：把画面拉出来、假设单薄处顶回去、逐节成文。适合「我想要一份拿得出手的简报，时间不是约束」。

下面的陪跑姿态管陪跑路径；快速路径把顶回去换成 `[假设]` 前缀，让用户在审阅时纠正。工作区持久——随时停下、随时续上。

## 工作区落盘

建 `{output_dir}/brief.yaml`（仅新建意图）并告知用户路径：

```yaml
project: {name: <diy-coder.yaml project.name>, status: 草稿, created: <today>, updated: <today>}
brief: {title: '', stakes: <已读出的档位>, problem: '', solution: '', pitch: '',
        users: [], value: [], open_questions: [], assumptions: [], extra_sections: []}
decisions: []
addendum: []
revisions: []
```

从这一刻起持久化是实时的：决策做出即带 `rationale` 进 `decisions`；用户主动多说的纵深带 `why_separate` 进 `addendum`；等确认的推断就地标 `[假设]`，并回声到 `brief.assumptions`。

若 `brief.yaml` 本来就在——`intent` 回执会说明，且对 `新建` 给过 warning——绝不静默覆盖：给两个去处，续上在写的草稿，或走一次刻意更新；任何重写都过第 4 步的快照纪律。

## 播报与下一步

读全 `./02-draft.md` 并照做。若请求其实是对一份已完成的简报做变更，改走 `./04-update.md`。
