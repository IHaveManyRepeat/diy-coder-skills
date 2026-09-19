# Step 2 — Systematic Impact Analysis（影响面系统走查）

Progress: `Initialize → [Analysis] → Edits → Proposal → Route → Finish`

**Read (input):** the `collect` receipt (`docs` / `diyc.check.violations` / `chain` / `counts`); `prd.yaml` / `epics.yaml` / `stories.yaml` / `architecture.yaml` only to resolve the context behind a specific impact (by ID — never a full re-read).
**Write (output):** `impacts` in the record; the working notes behind them.

## The receipt is the mechanical half (diy 改造点)

The source workflow walked its checklist by hand over whole documents. Here the mechanical facts already arrived:

- `docs` — the ID-level inventory of all six artifacts (features/FR, epics, stories+ACs, decisions, operations, pages). Take every candidate target ID from here, never from a fresh manual scan.
- `diyc.check.violations` — the cross-document mechanical verdict from diyc (`type` = which artifact). A pre-existing violation inside the change's blast radius is impact evidence: it names an ID chain that is already broken where the change lands.
- `chain` — the upstream/downstream reference points of `--target <ID>`. Every point on the chain is a place the change may ripple into; the two-hop expansion (FR → AC → TC → sprint task) is the construction blast radius.

If On Activation ran without `--target`, rerun it now with the confirmed target (`FR-x.y` / `F-x` / `S-x` / `AC-x.y` / `D-x` / ...) — the analysis needs the chain. If the running session cannot re-invoke `collect` mid-step, the conversation's own knowledge of the ID chain may stand in, but say so and keep this skill's reference-never-copy rule.

## The perspective list is the judgment half (source checklist §1–§4)

Walk these sections with the human; each produces `impacts` entries — `{artifact, target, kind, why}` with `target` a product ID that exists in the receipt, or `path:<relative>` for an infra file:

**A. Trigger and context (source §1).** Why did this surface now? Classify the issue: technical limitation found during implementation / new requirement from stakeholders / a misunderstanding of the original requirement / strategic pivot / a failed approach needing a different solution. The classification steers the path evaluation in D.

**B. Epic impact (source §2).** Can the epic holding the trigger story still be completed as planned? Which epic-level change is needed — modify scope or acceptance criteria, add an epic, remove or defer one, redefine it? Do later epics depend on it (check `epics[].feature_refs` and story `epic` links in the receipt)? Does the epic order or priority need resequencing?

**C. Artifact conflicts (source §3).** Per artifact in the receipt:
- `prd` — do goals, requirements, or the MVP boundary conflict with the change? Which `F-*` / `FR-*` / `NFR-*` are affected, and is the MVP still achievable?
- `architecture` — which `D-*` decisions (components, patterns, stack, data model, API design, integration points) does it touch?
- `design` — which `P-*` pages' flows, states, or accessibility are impacted?
- `openapi` — which `operationId`s lose or need a contract change?
- `test-plan` — which `TC-*` cases bind the affected ACs, and do the `static_checks` gates still match? (source §3.4 "Testing strategies")
- `infra` — deployment scripts, CI/CD pipeline configs, IaC, monitoring: anything the change forces to add or edit. Target is the file (`path:<relative>`), never a product ID. (source §3.4 "other artifacts")

**D. Path forward (source §4).** Evaluate the three source options against the evidence:
- **`直接调整`** — modify or add within the existing plan; effort / risk / timeline?
- **`回滚`（潜在）** — would reverting completed work simplify the fix, and is that justified?
- **`MVP 复审`** — is the MVP still achievable, or must scope shrink or goals move?

Name the recommendation with its rationale here; `approach` is settled in step 4 and the reasoning carries there.

## Produce impacts

One entry per affected target — `kind` is `修改` / `新增` / `删除`. `why` states what the change does to it in one line (impact, not the edit itself — edits are step 3). Anything the perspective list raises that cannot be tied to an existing target becomes an `open_questions` entry instead — never a fabricated ID. Infra files keep the source §3.4 "other artifacts" sweep alive: a deployment script, a CI config, an IaC file is `{artifact: infra, target: path:<relative>}`, not an open question. An inference you cannot confirm with the human yet carries the `[假设]` prefix in the value while drafting; the final gate requires zero, so every one of them is resolved or landed as an `open_questions` entry before step 6.

## Report progress

After each major section (B, C, D) present the running impact list in one message; the source workflow reported progress per checklist section, and the human steers here.

## Next

Read fully and follow `./03-edits.md`.
