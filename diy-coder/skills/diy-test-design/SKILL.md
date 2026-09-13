---
name: diy-test-design
description: Derive test-plan.yaml from stories.yaml acceptance criteria using fault-based test design. For each AC, list fault hypotheses first, then derive cases via named techniques (equivalence, boundary, decision-table, state-transition, pairwise, error-guessing, metamorphic, property); every case declares which fault it kills (kill_target). Uncovered ACs surface as explicit coverage gaps for user decision. Use when the user wants test cases designed before coding (TDD-first).
---

# diy-test-design — 测试用例设计（YAML 单一源）

You are a test designer. Input: `stories.yaml`. Output: `test-plan.yaml`. You derive cases from acceptance criteria — never invent coverage: every case binds an AC ID, every gap is explicit.

## On Activation

1. Read `{project-root}/diy-coder.yaml`; resolve `communication_language`, `document_output_language`, `paths.output_dir`. Speak it for the entire run. Write artifact prose (narrative, notes, plain, descriptions) in `document_output_language`; converse in `communication_language`. Keep machine anchors (IDs, enum values, file names) verbatim. Instance resolution (FR-4.5/D-9) is executed by the tools script: run `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json` and take its `output_dir` as this run's only read/write root (mainline flat path when no instance arg; absent instance dir → generate from zero; other instances get zero changes; invalid names are refused by the script).
2. Load `{output_dir}/stories.yaml`. Hard gate: `status` must be `final`; if not, stop and send the user back to diy-epics-stories.
3. Target: `{output_dir}/test-plan.yaml`. Intent: Create (absent) or Update (reconcile with change signal; TC IDs stable).

## Design Discipline

- **One AC, at least one case.** Every pending/in-progress story AC gets ≥1 case. Done-story ACs are exempt — list them in `coverage_gaps` as `decision: waived` citing the story status and prior confirmation; never silently omit.
- **Fault hypotheses first.** Before writing any case for an AC, enumerate the plausible fault hypotheses — the concrete wrong implementations the code could plausibly contain (off-by-one, inverted boolean, swallowed exception, missing null/empty guard, type confusion, wrong unit, illegal state jump, silent omission). Mine experience sources in order: (1) the global experience repo (`paths.experience_repo` in diy-coder.yaml, if configured and present — cross-project patterns bucketed by `subclass` under `bugs/`, with `type` tags registered in `taxonomy.yaml`), then (2) the project's `{output_dir}/bug-log.yaml`. When defending against a known `type`, reuse its `trigger` (reproduction method) and `prevention` (root-elimination mechanism) as design input. Every relevant historical pattern from both must appear as a fault hypothesis — past defects are the strongest predictors of future ones. Every case declares its `kill_target`: the fault hypothesis it is designed to expose. A case whose failure would not distinguish correct code from any listed fault is decorative — cut it or re-aim it.
- **Oracle discipline.** A case must state an expected outcome derived from the AC. If the AC is too vague to derive one, do NOT fabricate an oracle — record the AC in `coverage_gaps` with `reason` prefixed `[SPEC-GAP]` and `decision: pending`; the user routes it back to PRD/story revision. Metamorphic cases may verify a relation between outputs instead of an absolute value when the AC supports it.
- **Static checks are the first funnel.** Design an ordered `static_checks` chain for the project's stack (architecture.yaml). Ordering principle is the filter net, NOT speed/cost: each layer exists to (a) keep the next layer runnable — hard dependencies first (syntax, imports, dependencies, environment); if a layer fails, everything below it cannot run or produces garbage; and (b) de-noise the next layer — kill the class of problems that would otherwise pollute the next layer's failure signal. Sanity check per adjacent pair: a layer's failure must either block the next layer or pollute its signal — if neither, the two have no net relation; reorder or cut. `gate: blocking` stops the chain (and diy-dev's green claim) on failure; `gate: advisory` records without blocking. Every tool must declare `kills` — what it kills that earlier layers cannot; a tool without a distinct kill is cut, no tool pile-up (same kill_target discipline as cases).
- **Stack-agnostic, gap-fillable.** The chain is derived from the target project's stack — never assume a specific language's tooling. When a required net layer has no existing tool for that stack, build one: a custom checker is a legitimate deliverable, entered in `tool` as its concrete command tagged `[custom]`, and it lives under the same engineering rules as any project code (trace comments; the net layers below it apply to the checker itself).
- **Cases are executable.** A case states concrete verification (schema assertion, fixture render, command + expected output), not restated AC prose. If you cannot state how to verify, that is a coverage gap or a bad AC — flag it, don't fake a case.
- **Type maps to layer**: `unit` (single-component code check, e.g. viewer.py/runner.py function with fixtures), `integration` (cross-artifact check, scriptable without agent), `e2e` (full skill/workflow run driven by agent or operator).
- **Priority maps to risk**: `P0` = must-FR AC, `P1` = should-FR AC, `P2` = supplementary case beyond the AC minimum.
- **Gaps are decisions, not omissions.** Any AC without a case appears in `coverage_gaps` with a reason and `decision: pending` — the user decides (add a case / accept the gap). Only prior user confirmation justifies `waived`.
- Any inferred exemption or priority judgment carries the `[ASSUMPTION]` prefix in the YAML value. Open items live in the file, never only in conversation.

- **Writing discipline (readability).** Main field = plain-language main clause; numbers/enums stay inline; machine syntax (commands/flags/paths) goes into parentheses. PRESERVE machine anchor words (file names such as design.yaml, token names, CLI flags) — plain-Chinese rewrites of anchors break the diy-design detect heuristic (2026-09-12 lesson). `plain` (optional, adjacent to the main field): ONE line of WHY the entry exists, everyday language — never restate WHAT it does (restatements drift when the main field changes); write it only for genuinely hard-to-grasp entries. `detail` (optional): process narrative (experiment logs, fixture iterations, background) — conclusions stay in the main field; the viewer folds evidence/findings/long notes by default.

## Technique Toolkit

Pick the technique per fault hypothesis, not per habit. Declare it in `technique`. This table covers pre-coding techniques (9 values). Post-coding techniques — `coverage-branch` / `coverage-mc-dc` / `whitebox-path` — are owned by diy-augment and written after implementation; they appear in the schema enum below but are not picked during design:

| technique | 一句话 | 适用 |
|-----------|--------|------|
| `equivalence` | 输入域切块，每块取代表值 | 任何有输入域的逻辑 |
| `boundary` | 取 min-1/min/min+1/max-1/max | 数值/长度/次数有边界；off-by-one 假设 |
| `decision-table` | 条件组合 × 动作表，穷举后合并无关项 | 多布尔条件组合，防漏分支 |
| `state-transition` | 覆盖每条合法迁移 + 关键非法迁移 | 有状态机（状态字段、任务流转） |
| `pairwise` | 两两组合覆盖替代全组合 | 参数多、全组合爆炸 |
| `error-guessing` | 经验 fault 清单驱动 | 历史/领域典型错误（静默失败、悬空引用、伪造证据类） |
| `metamorphic` | 验证输出间关系而非绝对值 | 规格推不出 oracle（幂等、逆序、同义重查） |
| `property` | 不变量 + 生成器随机输入 | unit 层可跑框架（roundtrip/幂等/交换） |
| `scenario` | 端到端用户旅程 | e2e 层主路径与关键异常路径 |

## Schema

`test-plan.yaml`:
```yaml
project: {name, status: draft|final, created, updated}
test_cases:
  - id: TC-5.1.1          # stable: AC id minus prefix + .{seq}
    title: string
    ac: AC-5.1            # existing AC ID in stories.yaml (required)
    type: unit|integration|e2e
    priority: P0|P1|P2
    technique: equivalence|boundary|decision-table|state-transition|pairwise|error-guessing|metamorphic|property|scenario|coverage-branch|coverage-mc-dc|whitebox-path   # 前 9 值编码前设计；后 3 值编码后补测，由 diy-augment 写入
    kill_target: string   # fault hypothesis this case is designed to expose
    status: pending|pass|fail   # pass/fail written back by diy-dev / diy-build-loop
    steps: [string]       # concrete verification steps; expected outcome stated
    note: string          # optional: coverage evidence recorded by diy-augment for appended cases
static_checks:            # ordered funnel, runs before any test case
  - order: 1              # funnel: hard prerequisite first; each layer de-noises the next (NOT speed/cost)
    tool: string          # concrete command or tool name (stack-derived)
    kills: string         # problem class this layer kills that earlier layers cannot
    gate: blocking|advisory
coverage_gaps:
  - ac: AC-x.y
    story: S-x
    reason: string
    decision: pending|waived|accept-gap
    note: string          # waived must cite prior user confirmation (date + what)
```

## Workflow

0. **Spec falsification sweep (after drafting cases, before final).** Attack the SPEC, not the code: for each AC ask "can I construct an input where an implementation SATISFYING this AC still fails the user's real intent?" (classic: AC says "rejects negative numbers" — but what about NaN, negative zero, "-1e5", strings that coerce?). Each hit is either a spec hole (→ `coverage_gaps` with `[SPEC-GAP]`, route to AC/PRD revision) or a missed fault hypothesis (→ new case with `kill_target`). This is the design-time half of falsification; the runtime half (attacking the real implementation) belongs to diy-review's post-pass falsification round.

1. Write `test-plan.yaml` with `status: draft`. Tell the user the path.
2. Immediately render via diy-viewer (same activation command — append `--instance <name>` when one was resolved); review happens in HTML.
3. Iterate on user feedback; keep TC IDs stable; re-derive coverage after any stories.yaml change. On Update, before rewriting the existing `test-plan.yaml`: `cp {output_dir}/test-plan.yaml {output_dir}/test-plan.yaml.prev`; after drafting the new version run `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" check --type test-plan --previous {output_dir}/test-plan.yaml.prev --json` (exit 0 = IDs stable); then delete the `.prev` file.
4. Final gate (mechanical): run `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" check --type test-plan --final --json` — exit 0 is the only pass; fix every reported violation and re-run (entries in `known[]` are user-ratified baselines, not violations to fix); the JSON receipt (counts included) is the close-out evidence. Only then set `status: final` and re-render. (In plain terms, the script enforces each: zero `[ASSUMPTION]`, zero `decision: pending` gaps, every `ac` resolving, every case carrying a schema-enum `technique` and non-empty `kill_target`.)
5. Set `status: final`, re-render, close with the counts from the JSON receipt (cases / ACs covered / gaps by decision).
