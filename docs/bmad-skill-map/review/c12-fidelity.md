# C·12 批保真度报告 —— 三裁定落地（form_factor/modes 承载 + viewer 渲染通道 + diy-review 拆 steps）

- 批次：C 阶段第 12 项（三合一小批）｜ 完成日期：2026-10-01 ｜ 编制：主 agent（team-lead）
- 任务书：`diy-coder/.analysis/2026-09-28-c12/taskbook-c12.md`（158 行修订版，2026-10-01 四项裁定 + §7-5 三裁定 + Layer 1 时间轴归入 + W2 交付 3 收严）
- 施工形态：**agent team（c12-batch）三工位并行**（w1-design / w2-viewer / w3-review）+ lead 回派 2 轮（W3-R1 / W1-R1）+ lead 收口面（A 案订正）
- 基线：HEAD `15d9401`（C·3a 收口，**1575 passed / 235 subtests**）→ 收口态 **1603 passed / 243 subtests**（净增 +28 用例 / +8 subtests，与三工位新增精确闭合：W1 10 + W2 12 + W3 6）
- 本批改动：**15 M（+947 / −58）＋ 2 未跟踪**（`skills/diy-review/steps/` 七件 44 行 · `tests/test_review_skill.py` 91 行）——工作树**未提交**（待用户授权）
- 收口链：① suite_texts 复跑 11 绿 → ② sync.sh 49 技能冒烟过 + 源↔镜 diy 面 md5 **0 不匹配**（568 = 559 基线 + 7 steps + 镜像特有 2，数字闭合）→ ③ 全量**停笔串行 367.64s 零红** → ④ viewer 标签（并入 W2 + A 案）→ ⑤ 本报告 → ⑥ `迁移计划.md` §二十九 → ⑦ registry.yaml 零改动（链不变）

## 一、三工位交付总览（行数为收口态现测）

| 工位 | 面 | 交付 | 行数变化 | 自测 |
|---|---|---|---|---:|
| W1 | design 面承载（裁定 C12-1 + §7-5） | 顶层两键 + validate 五专项码 + audit 双模联动（dark 六角色判据 validate/audit 同源）+ `collect_token_hexes` 展开 dark（修「audit 打自己」盲点）+ check 暗色同款 5 组（4.5:1）+ 移动端按压态（`REQUIRED_STATES` 按 form_factor 取值，非移动端逐字不动）+ SKILL.md 规则两句 + 值域双向守卫 | design.py 1162→**1257** · SKILL.md 104→**106**（锁 112）· test_design.py 523→**774** · test_design_skill.py 296→**350** | 面内 54 passed / 11 subtests |
| W2 | viewer 渲染通道（裁定 C12-2 + Layer 1 时间轴） | assets 清单页（按活动分组+直链，空/缺静默）· prototype/implementation 独立路径判定（修 §7.3-2 腰斩缺陷，存在即直链否则纯文本、两分支绕 linkify）· form_factor/modes 键值标签 + dark 子块**零裸键**（七键中文、裸英文断言零在场）· 时间轴页（聚合 revisions，单产物渲染只增不改）· 回归 12 用例 | viewer.py 1648→**1781**（含 A 案订正 +2）· test_viewer_labels.py 769→**1060** | 面内 34 passed；viewer 六文件 81 passed / 8 subtests |
| W3 | diy-review 拆 steps（裁定 C12-3） | steps/ 七件（l1/l2/l3/l4/lenses/wds-review/falsify，原文逐字下沉+文件头三件套）；主文件保留激活时/工作流骨架/schema/**路由表**/规则 1–8/写作纪律；契约改（≤93→≤95、`assertNotIn("Read (input)")`→`assertIn`）；`test_suite_texts` 留痕（旧裁定对 review 作废）+ 新 `test_review_skill.py` | SKILL.md 91→**79**（线 = 79×1.2 = **95**，裁定 3 口径）· steps 七件 **44** 行 · test_review_contract 171→**189** · test_diy_review_wds 415→**442** · test_suite_texts 468→**469** | 面内 59 passed（回派后 63） |
| 回派 | W3-R1（lead 裁定扩权） | `test_restore.py` 拆分连带红：两 assertIn 读源改指 l4 + 「截图对比」NotIn 扩「主文件+steps」面 | 118→**128** | 4 passed |
| 回派 | W1-R1（lead 裁定扩权） | 两键必填跨面波及 9 红：四文件五构造点补 `响应式 Web`+`亮`；`:177` 键集合断言授权**未动用**（assertIn 宽松循环）；EdgeOwnership 读源扩面（W3 漏项代修） | 跨面四文件（open_questions 392 · transition 478 · wds 677 · diy_reverse 500） | 73 passed / 49 subtests |
| 收口 | lead（用户裁定 A） | viewer.py:1690 C·11 诊断行「未渲染」假事实订正（清单页落地后部分失真）+ 两条断言锚同步（`已列入清单页`） | viewer.py +2 · test_viewer_labels +1 | 57 passed |

## 二、V 验证总账（§5 五项，lead 亲跑，报告 `.analysis/2026-09-28-c12/v-report.md`）

1. **验收 14 项实跑**：C·12 全触面 12 测试文件一次 **224 passed / 60 subtests**
2. **保真对拍**：`git show HEAD` 基线引擎 vs 新引擎双跑两稿（干净稿/畸形稿）——**剔除新增码（FORM_FACTOR_MISSING/MODES_MISSING）后回执逐字 SAME**，既有 EMPTY_FIELD msg 保留；非移动端四态行为逐字同 HEAD（W1 七场景对拍 + lead 两场景复核）
3. **例外通道逐条复核**：申报 vs 实改 vs git diff 全吻合（见 §三）
4. **行数/计数**：16 文件 wc -l 现测全部与工位底稿一致
5. **变异验证 10 条**：三工位自证 10 条（W1 4 + W2 3 + W3 4）+ **lead 亲验 4 条**（l3 EVIDENCE_MISSING · FORM_FACTORS 去「多端」· 删 dark 标签 · page_targets 扩面回退）全 RED→md5 逐字节还原→GREEN

事故留痕（无残留）：lead 首次跑 W1 变异时 pytest 失败输出 GBK 解码崩溃致 design.py 短暂滞留变异态——即时发现、精确还原、复绿核对；后续改 bytes 捕获。

## 三、既有测试改动面全登记（任务书 §3-5 例外通道，本批共 5 类）

| # | 改动 | 授权 | 实况 |
|---|---|---|---|
| 1 | W3 读源调整：test_review_contract 9 锚（改指 steps 对应件）+ test_diy_review_wds 12 用例（`review_steps_text()` 拼接 + raw/docs 扩面） | §3-5 唯一例外通道（任务书预判 9 条内 + ★风险条款首查 12 例） | 断言本体零删改；NotIn 面扩到全部文档面（教学面=扫描面） |
| 2 | W3-R1：test_restore.py 读源（2 assertIn 改指 l4 + 1 NotIn 扩面） | lead 裁定 W3-R1（任务书预判漏项，lead 全库 grep 兜底后扩权） | 4 passed |
| 3 | W1-B1：test_design.py `GOOD_DESIGN` 夹具 +2 行（`form_factor: 响应式 Web`/`modes: 亮`） | lead 裁定（验收 #1「补两键后 rc=0」∩ 验收 #9「零删改绿」联立 → 唯一调和路径 = 夹具随 schema 演进；断言弱化除外） | 6 用例恢复绿；test 函数与断言零改动 |
| 4 | W1-R1：四文件五构造点补两键 + EdgeOwnership 读源扩面 | lead 裁定（两键必填的跨面连带；`:177` 授权未动用） | 73 passed / 49 subtests |
| 5 | 收口 A 案：viewer.py 诊断行文案 + test_viewer_labels 3 处断言锚（`未渲染`→`已列入清单页`，`点开查看` 保留） | **用户裁定 A（2026-10-01）**——C·11 诊断行在清单页落地后「未渲染」成部分假事实，不留假事实先例（同裁定 C12-3 注释改写） | 57 passed |

## 四、任务书预判面漏项 2 处（经验登记）

§2.3「已知必红断言 9 条」清单漏了两个**扫描 diy-review 主文件内容**型断言（预判时只列了 assertIn 锚型）：

1. `test_restore.py::RestoreLoopTests`（「结构对照」「线框」）→ W3-R1 处置
2. `test_design_open_questions.py::EdgeOwnershipTests`（`page_targets()` 扫 design.py 调用行 `--to`）→ W1-R1③ 代修（单写面优先）

**教训**：拆分类批次开工首查的 grep 面应覆盖**全部引用该技能文档的测试**（含按路径硬读与内容扫描两类），不止任务书点名的文件。

## 五、欠账登记（1 条）

- **diy-reverse 引擎 `init` 产物不含两键**（W1-R1 申报）：现无用例对 init 产物跑 design.py validate（不红）；后续批把两键接进 diy-reverse 产物面时须同步引擎。

## 六、裁定与口径留痕（本批新增）

1. 五专项码逐字：`FORM_FACTOR_MISSING`/`FORM_FACTOR_INVALID`/`MODES_MISSING`/`MODES_INVALID`/`MODES_TOKEN_PAIR_MISSING`（案 A，开顶层 schema 键专项码首例）
2. `diy-review` 拆后行数线口径 = **拆后实测 ×1.2 取 ceil**（79→95，C·3a 同口径）
3. 2026-09-19「12 个单文件技能不拆 steps」旧裁定对 `review` 作废（`test_suite_texts` docstring 留痕）
4. §3-2 部分解冻留痕：check 对比度维双模暗色扩展放行，余 7 维仍冻
5. 欠账两条归宿（任务书 §7-4）：dev/review 消费句 → C·7；form_factor↔touch-target 联动 → census #9 批（C·13）

**下一步**：**C·7**（读取成本纪律 + Layer 1 微处置 5 项 + 消费句 + dev 88 线放宽；任务书已立待审，节号 §三十）→ census #9 / C·13 立项 → **C·10**（版本发布，须最后）。基数仍 **49 技能**（本批零新增）。
