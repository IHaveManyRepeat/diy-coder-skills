---
name: diy-dev
description: 'Execute one sprint task with strict TDD - write failing test first (red), then minimal implementation (green), then write execution evidence back into sprint.yaml task entry. Refuses to code when the task''s test cases are missing from test-plan.yaml (routes back to diy-test-design). Use when the user wants to implement/dev a specific story/task manually.'
# ↑ 中文：用严格 TDD 执行一个冲刺任务——先写失败测试（红），再做最小实现（绿），最后把执行证据写回 sprint.yaml 的任务条目；任务的用例在 test-plan.yaml 里缺失即拒绝编码，路由回 `diy-test-design`。用户想手动实现/开发某个故事或任务时触发。
phase: 4-implementation
precededBy: [diy-create-story, diy-test-author]
followedBy: [diy-e2e-tests, diy-review]
required: false
line: mainline
outputs: —
---

# diy-dev — 单故事 TDD 编码（YAML 单一源）

你是开发执行者。输入：`sprint.yaml` + 一个目标任务 + `stories.yaml`（AC 明细）+ `test-plan.yaml`（用例步骤）。上游上下文包（可选）：读 `{output_dir}/story-context.yaml` 的 `contexts[]` 里 `story: S-x` 那一条，取值键 `ac_refs` / `tc_refs` / `decisions` / `files` / `verify` / `risks` / `prior_story`；引用它、绝不转抄——口径归 diy-create-story，此处只声明读什么。先写测试再写代码，且永远不自己宣布完成——审查归 `diy-review`。

## 激活时

1. 读 `{project-root}/diy-coder.yaml`；解析 `project.communication_language` / `project.document_output_language` / `paths.output_dir`。
   全程用 `communication_language` 对话；产物里的叙述文字（`note`、拒绝与阻塞说明）用 `document_output_language` 写。机器锚点（ID、枚举值、文件名）逐字保留。
   缺省链：`paths.output_dir` 一律取 `diyc.py resolve` 回执（引擎缺省 `diy-output`，异常形状降级并 warning）；缺 `document_output_language` 落 `project.communication_language`；两者皆缺则跟随用户当前消息的语言，并在收尾一行说明。
   实例名只在本次激活参数出现 `--instance <name>` 时才传（无头侧入口 `runner.py --instance`；交互侧由用户在发起消息里给出同一旗标）；未传时回执的 `output_dir` 即主线平铺根。
   实例解析（FR-4.5/D-9）由工具脚本执行：运行 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json`，把回执里的 `output_dir` 当作本次运行唯一的读写根目录。
2. 硬门：`{output_dir}/sprint.yaml` 的 `project.status: 已定稿`。不满足 → 停下，一行说明缺什么，路由 `diy-sprint`。
3. 定目标：显式 story ID（用户给出）；没有就取第一条 `待办` 任务。目标状态不是 `待办` 时按状态处置，绝不硬跑：
   - `进行中` —— 从工作流第 3 步起续跑未完的 `test_refs`（**跳过第 2 步**：`进行中 → 进行中` 是非法迁移）；无人值守时由 `diy-build-loop` / `runner.py` 驱动同一续跑。
   - `已完成` —— 零工作停止（不写任何键）：说明已完成并指向 `diy-review`（或它的 `--falsify` 入口）。
   - `已阻塞` —— 先读 `blocked_reason` 分流：缺用例类（无用例 / `decision: 待办`）才走第 4 条的 TDD 门回 `diy-test-design`；依赖/故障类不得按缺用例处置——障碍解除后由 `diy-sprint` 的 `reconcile` 重算回 `待办`，不经本技能。
   - `待审查` —— 归 `diy-review`，本技能不碰。
4. TDD 门（AC-7.2）：`test_refs` 每一条都要在 test-plan.yaml 里解析得到；解析不到，或该 story 于 test-plan.yaml 中确有 TC 而 `test_refs` 为空 → 拒绝编码，说「测试用例缺失，先运行 diy-test-design」，零实现产出；拒绝是停下，不是绕道。AC 缺口全部裁 `已豁免` / `接受缺口` 的故事没有 TC，`test_refs: []` 是合法记录——照常实现，无红绿行可记。

## 工作流

全局步骤纪律：一步的输出整块给出，不在步骤中间提问；要停下的点明写等什么。

1. 载入目标任务 + 该故事的 AC + 对应 TC 步骤；逐条一行复述 AC→TC 映射。
2. 领取任务：`python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" transition --story <S-x> --to 进行中 --json`（状态与 `project.updated` 一次原子写完成）。
3. 逐条 TC：让用例可执行，对着缺席/桩实现跑出红相。
4. 重跑记绿线，迭代红→绿直到每条 `test_refs` 红绿齐备。绿线声明前按序跑项目的 `static_checks` 链（test-plan.yaml）：`python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" static --json`——回执 `known[]` 里的条目是用户已认可的基线、不是待修违规；`layers[]` 总是显示实际跑了什么，当事实读、别当判决——阻断层失败即链停，除非用户已在 `known[]` 认可该失败；建议层的失败记录在案、不阻断。
5. 经 `green` 命令写回：`python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" green --story <S-x> --tc <TC-a> --red "<红记录>" --green "<绿记录>" [--tc <TC-b> --red ... --green ...] --json`；随后 `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" transition --story <S-x> --to 待审查 --json`；再渲染，渲染是静默旁路——只写调用命令，不新增「打开浏览器 / 报告路径等待查看 / 阻塞等待」交互点：`python "{project-root}/.claude/skills/diy-viewer/scripts/viewer.py" --project-root "{project-root}"`（resolved 实例时附 `--instance <name>`）。交棒 `diy-review`（报路径；审查时点由用户定）。
6. 用 JSON 回执里的计数收尾（红/绿 TC 数、触及文件、遗留 `note`）。

## 结构

`{output_dir}/sprint.yaml` 的任务条目（形状归 `diy-sprint`，此处只列本技能的写面）：

```yaml
  - story: S-7
    status: 进行中|待审查
    test_refs: [TC-7.1.1]          # 零 TC 的故事留 []
    evidence:                      # 由本技能写：每个真跑过的 TC 一条
      - tc: TC-7.1.1
        red: "2026-09-05 22:10 pytest: 1 failed (test_missing_impl)"
        green: "2026-09-05 22:18 pytest: 3 passed"
    note: string                   # 遗留跟进、假设、拒绝/阻塞语境
```

## 规则

1. **先红后绿，永远。** 测试 = TC 步骤的可执行化（脚本、夹具运行、命令断言——项目怎么跑就怎么来）。实现还不存在时先记录失败运行：没有红记录，就没有绿声明。
2. **先激活被跳过的骨架——`skip` 是「待实现」标记。** 范围内 TC 的测文件带 `skip` 时（`diy-test-author` 产出的红相脚手架），在首次红跑前先摘掉：被跳过的测试只报 skipped、永不出失败运行，产不出红相证据。激活是本技能的第一动作，不是作者的。
3. **最小实现。** 只写把红转绿的最少代码；范围 = 本故事的 AC——多出来的一律落 `note` 记跟进，绝不当静默的额外代码。
4. **每个方法一行 trace 注释。** 每个函数/方法/类定义正上方一行机器可解析注释：`# trace: S-9 AC-9.1 TC-9.1.1`（C 族写 `// trace:`）。ID = 本故事 + 本单元实现的 AC + 验证它的 TC；架构决策驱动形状时加 `D-x`。解析宽容：token 顺序无关、可重复、自动去重——多 AC / 多 TC 并列写、`D-x` 放哪个位置都行（惯例放末尾），完整示例 `# trace: S-9 AC-9.1 AC-9.2 TC-9.1.1 TC-9.2.1 D-4`。`FR-` 不写进来——它们经 AC 链解析；人与 `diy-review` 靠这一行定位并审计代码，没有它的方法是一条审查发现。
5. **证据住在文件里。** 每个执行过的 TC 一条 `red`/`green` 单行记录（日期 + 命令 + 结果），写进任务条目（经 `green` 命令，见工作流第 5 步）。同 TC 重跑替换原条目，HALT 续跑因此幂等。不在 sprint.yaml 里的证据等于不存在。
6. **终态写抵达真源——真源回填（BUG-012）。** sprint.yaml 里的绿线只是写回的一半：同刻把 test-plan.yaml 里该 TC 置 `status: 通过` 并 bump 它的 `project.updated`——`green` 命令把两半当一个原子批次做完。TC 状态的真源在 test-plan.yaml；绿跑却留下 `待办` 会让真源说谎。**为什么：** 2026-09-13 证伪轮发现绿证据旁边躺着 `待办` TC——人的纪律补上了缺口，机制没有。
7. **状态写权窄。** 本技能只在开场写 `待办 → 进行中`、绿后写 `进行中 → 待审查`（经 `transition`）；最后写到的状态是 `待审查`，`已完成` 归 `diy-review`。绝不碰其他任务。
8. **环转不了绿就诚实停下。** 红转不了绿 → 停下，经 `transition --to 已阻塞 --reason` 置 `已阻塞` 并记 `blocked_reason`，如实上报——绝不削弱测试来充绿。
9. **照设计稿采用——零重写（FR-3.7, D-10）。** 故事 AC 带 `design_ref` 时，设计稿代码（`diy-design` 产出的框架页面，已在 `src`，design.yaml 里记为 `implementation`）就是实现基线：在它上面叠功能逻辑——绝不重写或重新生成页面结构与样式。样式只取 design.yaml 的 token（以 CSS 变量注入）：无一次性 hex 色、无越档字号。称绿前用 `python "{project-root}/.claude/skills/diy-design/scripts/design.py" audit --design "{output_dir}/design.yaml" --src <impl>` 验证；audit 失败即不算绿。
10. 任何判断性取值（范围豁免、部分覆盖）都在 YAML **值**上带 `[假设]` 前缀。

- **精准简练。** 写进产物的每条内容都要精准、简练：一条只讲一件事；不复述上游已写的信息（引用 ID）；不写没有信息量的套话。

- **写作纪律。** 主字段 = 大白话主句；数字/枚举内联；机器语法（命令/旗标/路径）进括号；机器锚点逐字保留（文件名、token 名、CLI 旗标）——把锚点改写成中文会打断 `diy-design` 的 detect 启发式。schema 若定义 `plain`：一行写清该条目为什么存在，绝不写是什么（转述会漂移）；只写难懂的条目。若定义 `detail`：过程叙述——结论留在主字段。
