# P1 样板保真度报告 —— diy-checkpoint-preview

- 日期：2026-09-13 ｜ 批次：迁移 P 阶段 P1（首个样板技能）
- 输入：BMAD `bmad-checkpoint-preview`（SKILL.md + step-01..05 + generate-trail.md）｜ 本仓 `.claude/skills/bmad-checkpoint-preview/`
- 产出：`diy-coder/skills/diy-checkpoint-preview/`（薄主文件 + steps/ + 领域引擎）｜ `diy-coder/tests/test_checkpoint.py`
- 执行：agent team（W1 引擎与测试 / W2 技能文件 / V 独立验证两阶段）｜ 任务书与验证档案：`diy-coder/.analysis/2026-09-13-migration-p1/`

## 结论

**样板全项通过；2 条范式裁定已于 2026-09-13 拍板（§5）。** V 独立验证：116 条能力清点**零丢失**、无阻断裂、**可发布 yes**；终审计发现的 3 处范式措辞摩擦（F1/F2/G-O1）已当场修复并经 V 复验关闭。验收 12 项 = 11 ✅ + 1 N/A（#10 非交汇技能）+ 2 条适配（#12 b/c，见 §5 R1）。

## 1. 差异报告（计划规定格式）

| 项 | 结果 |
| --- | --- |
| 技能名 | `diy-checkpoint-preview`（原 `bmad-checkpoint-preview`） |
| 工作流步数 | 原 5 步 → diy 5 步（语义一一对应；细节下沉 steps/，主文件只给路由） |
| 菜单/分支 | 原 3（Approve / Rework / Discuss）→ 3（+ discuss 循环回决策点） |
| 丢失能力清单 | **无**（2 项生态钩子按裁定裁剪：advanced elicitation / party mode 属 B4 未建，登记 C 阶段「B4 后回接」） |
| 门禁自检 | ✅ 零产出退出 + 路由（用例：空项目 exit 1、目录零写入） |
| ID 链自检 | ✅ story 引用解析（悬空 S-99 → UNKNOWN_ID exit 1）；CK-### 顺序/唯一/不重用（DUPLICATE_ID 实测） |
| viewer 自检 | ✅ 通用降级渲染 rc=0；⚠️ 2 条标签缺口登记 C 阶段（枚举值 approve/git 无中文映射、文档名 checkpoint 无中文标签） |

## 2. 交付物与指纹（定稿版）

| 文件 | 行数 | md5（前 8 位） |
| --- | --- | --- |
| `SKILL.md`（四段 + 两段冻结文本） | 77（≤90） | `9004e1b3` |
| `steps/01-orientation.md` | 114 | — |
| `steps/02-walkthrough.md` | 78 | — |
| `steps/03-detail-pass.md` | 101 | — |
| `steps/04-testing.md` | 74 | — |
| `steps/05-wrapup.md` | 41 | — |
| `scripts/checkpoint.py`（领域引擎：target / check） | 665 | `790ca4ca` |
| `tests/test_checkpoint.py` | 449 | `72f7bf35` |

冻结文本逐字校验（修复全程复跑 3 次均一致）：实例解析句 md5 `5445f98b…` ✅ ／ 写作纪律块 md5 `f1b3b6fb…` ✅。

## 3. 验收 12 项对照

| # | 验收项 | 结果 | 证据 |
| --- | --- | --- | --- |
| 1 | 薄主文件 + 厚子文件（steps/ 首次落地） | ✅ | 77 行主文件只给路由；5 个步骤文件承载细节；读取纪律「一次只加载一个」入 Rules |
| 2 | 产物 YAML schema（`diy-output/` + 稳定 ID） | ✅ | `checkpoint.yaml`，`CK-###` 三位序号；单一源 + revisions 段 |
| 3 | 前置门禁（零产出退出 + 路由） | ✅ | 用例断言 exit 1 + 目录零写入 |
| 4 | ID 链接入 | ✅ | story 引用可解析校验；CK ID 唯一/不复用（DUPLICATE_ID） |
| 5 | 注册 | ✅ | `sync.sh` 安装 15 技能；源/副本 7 文件 md5 全一致（修复后重同步复验） |
| 6 | viewer 渲染 | ✅⚠️ | 通用降级 rc=0（3 文档）；标签/枚举映射缺口登记 C 阶段（§8） |
| 7 | 冒烟 TC | ✅ | 20 用例全过（含门禁拒绝、契约冒烟、阈值边界 9/10 词、WORKTREE null、空仓库、损坏 YAML） |
| 8 | 登记元数据 | ✅ | frontmatter：phase/precededBy/followedBy/required 与 skill-map.json 逐字一致；line/outputs 见 §5 R2 |
| 9 | 读取成本纪律 | ✅ | On Activation 明确读取清单；checkpoint.yaml 仅铸造 CK-### / 按 `id:` 定位改单条；校验结论走引擎回执 |
| 10 | 双源输入声明 | N/A | 本技能为通用入口型（主线/WDS 线均可挂），非主线×WDS 交汇点 |
| 11 | 渲染静默 | ✅ | 渲染只写命令；零新增浏览器/路径等待交互点（非 TTY `--no-open` 静默已验证） |
| 12 | diyc 接线 | ✅（2 条适配） | a 实例句委托 diyc resolve（冻结文本逐字）；d 语言绑定套件模板；e Rules 写权边界；**b/c 适配见 §5 R1**（V 终审计曾发现 b 项时序自指措辞 F2 → 已修复经复验） |

## 4. 能力保真（V 独立清点对照）

**结论：116 条能力清点零丢失**（V 独立复现：307 全量 / 20 专项 / 双 md5 / sync 一致 / 真实仓库冒烟 / 夹具四态校验 / 渲染 / 边界零裸栈 / 引擎零写操作）。

- **分组核对**（A 全局 13 / B SKILL 9 / C step-01 27 / D step-02 13 / E step-03 22 / F step-04 11 / G step-05 7 / H generate-trail 11 / I customize 3）：必须保留项全部存活；裁剪/合并均属已裁定适配（customize 机制按 §8.7 整体不迁；生态钩子按 §7.6；generate-trail 按 §8.6 并入 step-01）。
- **§J 十条差异观察**：全部「保留」或「已裁定适配」，未发现与 §7/§8 裁定不符项。样例：级联三分支双处存活（恰好一个→确认／多个→编号选项／无→fall through）；交互能力（dig into / EARLY EXIT / Discuss 循环）以 steps 文本承载、未误移入引擎；risk 标签 8 项**逐字**保留；零悬空技能引用。
- **终审计发现与关闭**：F1（`inferred: null` 写入冲突）、F2（终门时序自指）、G-O1（`inferred: false` 措辞张力）——3 处均为**文本级范式措辞**（引擎/测试零改动），已修复并经 V 增量复验 **G1/G2 通过 + G-O1 关闭**（档案：`v-verdict.md` §3/§6）。
- **遗留观察 5 条**（O1/O2/O4/O5/O6，均无功能影响，记录不修）。其中 O6 说明：Machine Hardening 的 `## Spec Change Log` 数据源在 diy 侧等价物是 stories.yaml（结构化 YAML 无该 markdown 段）——该分支**保留但不激活**，范式完整，待后续批次出现 markdown spec 场景自然启用。
- **W1 收口附注**（引擎侧未决项裁定）：`mode`↔`target.source` 一致性不做硬约束（LLM 可在有 story 锚点时修正引擎建议）；`inferred` 词数阈值照原文英文口径（`<10` 空白分词），中文提交标题通常 1 词 → 恒判 `true`——**保守方向**（仅提示人工核对、不产生错值）；精确化需自造 CJK 折算规则（偏离原文），登记为后续批次可选项。

## 5. 范式裁定项（已拍板 2026-09-13，2 条）

**R1 —— 新产物类型的终门载体：技能自带领域引擎（同构契约），而非扩展 diyc。**
`diyc.py check --type T` 类型集硬编码 7 类（prd/architecture/openapi/epics/stories/test-plan/sprint/review）；`checkpoint` 属新类型。按批次 3 已立分工裁定（「diyc = 跨文档机械核对、X.py = 领域引擎」，design 即出此例），本技能终门 = `scripts/checkpoint.py check --final`（exit 0 唯一放行 / `--json` 单行回执 / violations+counts 同构）。同时适配验收 #12(c)：本技能记录只追加、CK ID 不重用，无需 `--previous`（Rules 8 显式声明）。
**若你裁定「必须扩展 diyc 类型集」**：需改动冻结的 diyc 三文件并增量复核，且 34 个新技能将各自触发一次 diyc 改动——建议维持引擎形态。

**R2 —— 登记元数据落 SKILL.md frontmatter。**
样本已落 6 字段（`phase / precededBy / followedBy / required / line / outputs`；前四项值取自 skill-map.json 逐字一致）。`line: any` 为扩展值（skill-map 无此字段；本技能跨两条线通用）——需确认 `any` 进登记表枚举（C 阶段缺口 1 落地时 diy-help 读取该字段）。

## 6. P2 缺口定论（P1 实证）

| 缺口 | 定论 |
| --- | --- |
| 缺口 1（diy-help 承载力） | 载体选定 = 各技能 frontmatter 声明（样本已示范）；现状 help.py 硬编码 `CHAIN` 未受影响；C 阶段按 48 技能重写为登记表驱动，`line` 枚举需含 `any` |
| 缺口 2（viewer 产物类型） | **通用降级已存在且可用**（未知类型递归渲染，不崩不空——本批实测）；剩余 = 展示层映射缺口（checkpoint 文档标签 + 枚举值中文映射），小而明确，C 阶段一次补齐 |
| 缺口 3（人设类） | 已定（方案 B），本批无涉 |

## 7. 集成证据（全部亲跑，修复后复验过）

| 项 | 命令/值 | 结果 |
| --- | --- | --- |
| 全量回归 | `cd diy-coder && python -m unittest discover -s tests -v` | **307 passed**（287 基线 + 20 新增，零回归；修复后专项复跑 20/20 仍绿） |
| 分发同步 | `bash diy-coder/sync.sh` | 15 技能安装 + 冒烟全过；源/副本 md5 全一致（修复后重同步复验） |
| 夹具终门 | `checkpoint.py check --final` | exit 0；counts：checkpoints 1 / approve 1 / concerns 2 / risks 2 / observations 2 |
| 真实仓库冒烟 | `checkpoint.py target`（只读） | exit 0；级联轨迹：explicit 未命中 → sprint 无 review 任务 → git 命中（WORKTREE） |
| 渲染 | `viewer.py`（夹具，非 TTY 静默） | rc=0，3 文档；2 条未映射枚举警示（已登记 C 阶段） |
| 冻结文本 | md5 双校验（修复全程 3 次复跑） | `5445f98b…` / `f1b3b6fb…` 逐字节一致 |

## 8. 遗留项与下一步

**C 阶段增补清单（本批新增 3 项）**：
1. viewer 展示层：`DOC_LABELS["checkpoint"]` 中文标签 + 枚举值映射（approve/rework/discuss、source 值、risk label 值、inferred 布尔显示）
2. 横切入口回接：本技能步骤内的深化/多角色邀请语，在 B4 批 `diy-elicit` / `diy-party-mode` 落地后按原挂载位置接回
3. 登记表（缺口 1）读取 frontmatter 六字段；`line` 枚举含 `any`

**下一步（B1 批，已具备启动条件）**：5 个新技能 —— `diy-research`(3合1) / `diy-product-brief` / `diy-prfaq` / `diy-readiness-check` / `diy-project-context`(2合1)；`diy-checkpoint-preview` 已在本批建成。

**本会话暂停点**：P1 全交付（文件落盘、`.claude` 已同步、测试全绿）；工作区未提交（等你指令）；B1 未启动（P 强制人工审通过后才铺开）。
