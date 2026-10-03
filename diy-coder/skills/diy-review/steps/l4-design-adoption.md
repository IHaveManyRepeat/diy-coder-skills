# Step — L4 设计采用（Design Adoption，FR-3.7/D-10 —— 仅 UI 任务）

**Read (input):** `design.yaml`（`prototype` 结构稿、`implementation` 路径、`tokens`）；任务 AC 的 `design_ref`；实现稿。
**Write (output):** L4 findings（`layer: 设计采用`，每项违规一条 `小修`）；任务打回 `进行中`（HALT）。

- **L4 设计采用（FR-3.7/D-10 —— 仅 UI 任务）。** 任务 AC 带 `design_ref` 时核验**采用**——设计交付（diy-design 写出的框架页）是实现必须在其上生长的基线。像素比对已弃用（不可靠；`compare` 引擎 2026-09-12 已删）。核四件事，每项违规一条 `小修` finding、任务打回 `进行中`（HALT）：(a) 结构对照——实现页面结构须与线框（wireframe/HTML）结构稿（design.yaml 的 `prototype`）一致：小节、层级、landmark 次序；(b) 零重写——实现长在设计稿代码（design.yaml 的 `implementation` 路径）**之上**，不是它的再实现；重写 UI 即使看着像也是一条 finding；(c) token 单一源——`python "{project-root}/.claude/skills/diy-design/scripts/design.py" audit --design "{output_dir}/design.yaml" --src <impl>` 的每条 `one-off-*` 违规即 finding；(d) 无障碍——`python "{project-root}/.claude/skills/diy-design/scripts/design.py" check --design "{output_dir}/design.yaml"` 的违规即 finding——**含设计系统三维 `ds-token-color` / `ds-token-font-size` / `ds-token-spacing`**（实现稿照抄字面值即违规）；引用回执**按 code 点名、不写维度计数**。绝不静默跳层——跳过要用户的明确裁断。
- **顶层两键消费（C·7）**：审查面同时看 `design.yaml` 顶层 `form_factor` 与 `modes`——`form_factor` 与实现形态的一致性（如 `移动端` 产物不应出现响应式断点依赖）；`双模` 时暗色对在产物中的体现（`tokens.color.dark` 六角色是否真被用上而非只留在设计稿）。两键语义以 `diy-design` 键表为唯一权威（`form_factor` = 目标表面「写在什么上」、`modes` = 默认主题），不另立解释。
- **触控分档消费（C·13）**：`check` 的 `a11y-touch-target` 下限按 `form_factor` 分档（移动端 44 / 桌面 24 / 响应式 Web 与多端 44 / 缺省 44）——审查面核产物形态与分档值的一致性（如 `桌面` 产物触控目标 24px 边界、`移动端` 44px）；分档口径以 `diy-design` 引擎为唯一权威，不另立解释。
