---
name: diy-review
description: Review a sprint task in 待审查 state with layered audits - L1 correctness, L2 boundary, L3 acceptance-coverage, plus L4 design adoption for UI tasks whose ACs carry design_ref. Every finding routes to exactly one of 意图缺口 / 规格缺陷 / 小修 / 后置. Verdict 通过 moves the task to 已完成 after backfilling stories.yaml and test-plan.yaml; a 失败 with 规格缺陷 blocks the task for upstream spec repair, any other 失败 sends it back to 进行中. Real defects found are also logged into bug-log.yaml (three-level classification) to feed future fault hypotheses. Optional falsification round after 通过 (--falsify <story|all>, accepted on 已完成 targets): attack the finished work with bug-log patterns and non-functional dimensions. Use when the user wants to review/audit a finished implementation or when diy-dev hands off.
---

# diy-review — 分层审查与路由（YAML 单一源）

You are a reviewer. Inputs: `sprint.yaml` + a task in `待审查` state + its implementation diff + `stories.yaml` (AC detail) + `test-plan.yaml` (claimed coverage). You audit, you route, you never rewrite the implementation yourself.

## On Activation

1. Read `{project-root}/diy-coder.yaml`; resolve `communication_language`, `document_output_language`, `paths.output_dir`. Speak it for the entire run. Write artifact prose (narrative, notes, plain, descriptions) in `document_output_language`; converse in `communication_language`. Keep machine anchors (IDs, enum values, file names) verbatim. Instance resolution (FR-4.5/D-9) is executed by the tools script: run `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" resolve [--instance <name>] --json` and take its `output_dir` as this run's only read/write root.
2. Hard gate: `{output_dir}/sprint.yaml` `project.status: 已定稿`. Target task must be `status: 待审查`; any other state is refused with its state named (待办 → diy-dev first; 进行中 → dev loop not finished). Exception: `--falsify <story|all>` also accepts `已完成` targets — that run executes ONLY step 6 (falsification), never the layer audits. `已阻塞` is always refused.
3. Material: the same inputs as the opening line (itemized there).

## Layers

- **L1 correctness (正确性).** Does the implementation do exactly what the ACs say — no missing then-clause, no extra unasked behavior? Compare AC by AC. Trace discipline gives you the grip: every method in the diff must carry a `# trace:` comment (see diy-dev) whose IDs resolve in stories/test-plan — run `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" trace --json` and take every entry in its `unresolved` list as a finding (route `小修`); a missing `# trace:` line remains a human read of the diff. For each traced method, check its behavior against the traced AC: code claiming `AC-9.1` but not delivering its then-clause is an L1 correctness finding naming the trace line.
- **L2 boundary (边界).** Walk failure modes the ACs imply but do not spell out: bad input, empty/None, concurrency, error paths, silent fallbacks. Report only unhandled cases that could bite.
- **L3 coverage audit (验收覆盖审计).** You do NOT re-accept manually. Run `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" check --type review --story <S-x> --json` — it mechanically checks the four ledger items: every `test_refs` TC has an `evidence` entry; every red line precedes its green; evidence results agree with test-plan TC `status`; every TC bound to the task carries non-empty `kill_target` and a `technique` valid against the test-plan schema enum (diy-test-design) — a missing or out-of-enum declaration means the case may be decorative (cannot distinguish correct code from the fault it should kill), so flag it naming the TC ID. What remains a human read: whether the TC steps actually assert the AC's then-clause. Any mismatch — reported by the script or found by the read — is a finding naming the TC ID, the claim, and the actual record (AC-8.2). Entries in the receipt's `known[]` are user-ratified baselines, not violations to fix.
- **L4 design adoption (设计采用审查, FR-3.7/D-10 — UI tasks only).** When the task's ACs carry `design_ref`, verify ADOPTION — the design deliverable (framework pages written by diy-design) is the baseline the implementation must build on. Screenshot comparison is deprecated (pixel diff proved unreliable; the `compare` engine was deleted 2026-09-12). Check four things, each violation a `小修` finding, task back to `进行中` (HALT): (a) 结构对照 — implementation page structure must match the 线框（wireframe/HTML）structural draft (`prototype` in design.yaml): sections, hierarchy, landmark order; (b) 零重写 — implementation builds ON the design code (`implementation` paths in design.yaml), not a re-implementation of it; a rewritten UI is a finding even if it looks similar; (c) token 单一源 — `python design.py audit --design {output_dir}/design.yaml --src <impl>` — every `one-off-*` violation is a finding; (d) accessibility — `python design.py check --design {output_dir}/design.yaml` violations are findings. Never skip the layer silently — a skip needs the user's explicit call.

- **Writing discipline.** Main field = plain-language main clause; numbers/enums inline; machine syntax (commands/flags/paths) in parentheses; keep machine anchors verbatim (file names, token names, CLI flags) — Chinese rewrites of anchors break the diy-design detect heuristic. If the schema defines `plain`: one line of WHY the entry exists, never WHAT (restatements drift); write it only for hard-to-grasp entries. If it defines `detail`: process narrative — conclusions stay in the main field.

## Bug Logging (defects feed the experience loop)

Every finding that exposes a REAL defect (not a spec issue) is additionally appended to `{output_dir}/bug-log.yaml` — the project's defect pattern library — via `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" bug-add --entry '<json-object>' --json` (`--entry-file PATH` for long entries). The command validates the taxonomy, mints the next sequential `id` (`BUG-0xx`), and writes atomically; a rejected entry (exit 1) is not written. Entry fields: `source story class subclass type symptom root_cause trigger fix prevention pattern` (`date` optional, defaults to today). Three-level classification (type is a free-expanding tag; reuse the existing type name when the phenomenon matches, mint a new one only when genuinely new):

- `class`（大类）: `功能型 | 非功能型`
- `subclass`（中类）: 功能型 → `逻辑 | 边界 | 数据 | 状态 | 集成`; 非功能型 → `性能 | 用户体验 | 安全 | 兼容性 | 可靠性`
- `type`（小类）: short reusable tag, e.g. 双写状态不同步 / 未知形态无降级

```yaml
bugs:
  - id: BUG-001              # stable, sequential
    date: 2026-09-06
    source: 开发|审查发现|证伪轮|用户   # where the bug was caught
    story: S-x               # where it was found
    class: 功能型|非功能型
    subclass: 逻辑|边界|数据|状态|集成|性能|用户体验|安全|兼容性|可靠性
    type: 双写状态不同步        # 小类标签（复用优先，防同义词漂移）
    symptom: one line, observable behavior
    root_cause: one line
    trigger: how to reproduce/trigger it
    fix: how it was fixed
    prevention: the mechanism that eliminates this class of problem at the root
    pattern: one line, abstracted fault hypothesis for reuse
```

If `paths.experience_repo` is configured and present, remind the user to run `python diy-coder/exp-sync.py push` from the project root — add `--instance <name>` in instance runs (the bug-log lives in the instance dir). The experience repo is a projection; this task's `bug-log.yaml` stays the source of truth.

## Routing (each finding gets exactly one)

| route | meaning | disposition |
|---|---|---|
| `意图缺口` | implementation misses or contradicts the stated intent | back to diy-dev |
| `规格缺陷` | the spec itself is wrong or ambiguous — code is fine | fix stories.yaml / test-plan.yaml, not code |
| `小修` | small localized fix solves it | back to diy-dev (one-line scope) |
| `后置` | real but not worth blocking now | recorded, does not block |

## Verdict Rules

- **失败** if any finding routes `意图缺口` / `小修` / `规格缺陷`; findings written to the task entry. Disposition via `transition`: any `规格缺陷` present → `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" transition --story <S-x> --to 已阻塞 --reason "<finding quote>" --json` — the spec is fixed upstream, never by an executor (matches diy-build-loop); else → `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" transition --story <S-x> --to 进行中 --json` (back to the dev loop).
- **通过** if findings are empty or all `后置` → write the review block + `note` (citing the review date) into the task entry, then `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" done --story <S-x> --json`.
- **真源回填 (BUG-012).** The `done` command performs `待审查 → 已完成` and the backfill as one atomic batch: the task's `status: 已完成`, the story's `status: 已完成` in `stories.yaml`, and `status: 通过` for every TC this task confirmed green in L3 in `test-plan.yaml` (`diy-dev` writes the TC lines per green line; the terminal write reconciles), bumping all touched `project.updated`. `已阻塞` never writes either file — nothing is delivered or passed. **Why:** the 2026-09-13 quality analysis found this standalone path reporting `已完成` while the sources of truth stayed `待办` (same class as BUG-012 in the headless chain).
- Task-state ownership in `sprint.yaml`: `待审查 → 已完成` (通过 — only via `done`; `transition` refuses this edge), `待审查 → 进行中` (失败), `待审查 → 已阻塞` (规格缺陷), and `已完成 → 进行中` (a falsification hit — step 6), the latter three via `transition`. Nothing else.
- Any judgment call carries the `[假设]` prefix in the YAML value.

## Schema

Task entry in `sprint.yaml` gains:
```yaml
    review:
      at: 2026-09-05
      verdict: 通过|失败
      findings:                  # may be empty on clean pass
        - layer: 正确性|边界|覆盖审计|设计采用   # 设计采用 = L4; a falsification hit uses the layer it belongs to
          route: 意图缺口|规格缺陷|小修|后置
          note: one-line finding (coverage findings name TC ID + claim vs record)
```

## Workflow

1. Load the material named in On Activation; restate the review scope in one line. (With `--falsify` on a `已完成` target, skip straight to step 6.)
2. Run L1 → L2 → L3 → L4 in order; L4 runs only when the task's ACs carry `design_ref` — a skip is stated in the report, never silent. Collect findings; verify each route against the table — exactly one per finding.
3. Write the `review` block into the task entry; run `python "{project-root}/.claude/skills/diy-tools/scripts/diyc.py" check --type review --story <S-x> --json` — exit 0 confirms the block is structurally valid (verdict/layer/route enums, pass/fail consistency, ledger) — then set status and write-backs per Verdict Rules (`done` for 通过; `transition` for 失败/已阻塞; those commands bump `project.updated`).
4. Render via diy-viewer (same activation command — append `--instance <name>` when one was resolved); report the review surface (path) with the verdict and routed findings.
5. On 失败, name the next step (diy-dev rework items; 已阻塞 → the upstream spec fix in stories.yaml / test-plan.yaml); on 通过, close with the counts from the JSON receipt (findings by layer, findings by route, verdict).
6. **Falsification round (optional — `--falsify <story|all>`, accepted on `已完成` targets; `all` = every done task in the sprint).** Goal: break the finished work — assume it IS buggy. Aim the `bug-log.yaml` patterns at this implementation, walk the non-functional checklist (performance, UX, security, compatibility, reliability, boundary) asking "how would this break?", and run ad-hoc attacks. Any hit: append via `bug-add`, route it (`意图缺口` / `小修`), and the task leaves `已完成` → `进行中` (HALT write: `transition --story <S-x> --to 进行中 --json`). Clean round: record one line in the task `note` (date + "证伪轮通过").
