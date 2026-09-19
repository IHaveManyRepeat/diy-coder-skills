# Step 1 — Orientation（定向）

Progress: `[Orientation] → Walkthrough → Detail Pass → Testing → Wrap-Up`

**Read (input):** the `target` receipt from On Activation; the spec named in its `spec` field (when present); the diff and the changed files.
**Write (output):** the orientation message; the draft record in `{output_dir}/checkpoint.yaml` (`id` / `date` / `change_type` / `target` / `mode`).

## Locate the change

The conversation before activation IS the starting point — not a blank slate. Locating happens in two layers.

**Your layer — the recent conversation.** Scan the last few messages for a PR, commit, range, branch, spec path, or a description of the change. Turn a commit / range / branch / PR clue into an explicit `--ref` and pass it to the engine (a PR resolves via `gh pr view` when `gh` is available; if that fails, ask for a SHA or branch). A spec path alone is not an engine ref — carry it into Enrich below instead. Run:

```
python "{project-root}/.claude/skills/diy-checkpoint-preview/scripts/checkpoint.py" target --project-root "{project-root}" --output-dir "{output_dir}" [--ref <commit|range|branch|PR>] --json
```

**The engine's layer — 3 mechanical levels plus the refusal:**

1. explicit `--ref` → `source: 显式指定`
2. a `sprint.yaml` task with `status: 待审查` → `source: 冲刺任务` (its `story` and `spec` when resolvable). Branch on the candidate count: exactly one → suggest it and confirm with the human; several → present them as numbered options; none → fall through to git.
3. git worktree / HEAD diff → `source: Git 提交`
4. none of the three → exit 1 + a refusal line

Take `candidates`, `source`, `story`, `spec`, `mode`, `diff_stat` from the receipt. Do not ask questions beyond this cascade.

On exit 1 the run is over: relay the refusal's one-line reason and its route (give an explicit ref, or run diy-dev / diy-review first), stop, and write nothing — the refusal is a zero-output exit, not a record.

## Enrich (pair spec and commit)

The engine pairs them mechanically: a spec whose `baseline_commit` is an ancestor of the reviewed commit/branch is the spec for that change.

- Spec alone → its `baseline_commit` frontmatter is the diff baseline.
- Commit/branch alone → take the spec found by the engine when there is one.
- Both → use both.

## Settle review_mode

`mode` comes from the receipt; confirm it here and let it drive steps 2–4:

1. **`全程轨迹`** — a spec exists with a `## Suggested Review Order` section. Intent source: the spec's Intent section.
2. **`仅规格`** — a spec exists, no Suggested Review Order. Intent source: the spec's Intent section.
3. **`裸提交`** — no spec. Intent source: the commit message. If the message is terse (under 10 words), scan the diff for the primary change pattern and draft a one-sentence intent. The receipt reports which case you are in: `target.inferred: true` — the intent was inferred from the diff; `false` — the message itself carries the intent (≥10 words, or an explicit commit ref), nothing to infer; `null` — undeterminable (a WORKTREE or range target, say), paired with an `inferred_reason` string. Flag an inferred intent `[inferred]` in the output so the human can correct it; in the `null` case relay the `inferred_reason` in plain words — the intent came from the diff and needs a human check.

Set `change_type` — the record field that carries how the human names the change: `PR`, `commit`, `branch`, or their own words (e.g. `auth refactor`); default to `change` when ambiguous. Steps 2–5 close their prompts with "this {change_type}", reading it from the record so the phrase survives the whole run.

## Produce the orientation

**Intent.** From a spec's Intent section: display verbatim regardless of length — it is already written to be concise. From other sources (commit message, bug report, the human's own words): ≤200 tokens → verbatim; longer → distill to ≤200 tokens and link the full source (file path or URL). Format: `> **Intent:** {summary}`.

**Surface-area stats.** Derive from the receipt's `diff_stat` plus the diff content:

- **Files changed** — count from `git diff --stat`.
- **Modules touched** — distinct top-level directories among the changed paths.
- **Lines of logic** — added/modified lines excluding blanks, imports and formatting; `~` because approximate.
- **Boundary crossings** — changes spanning more than one top-level module; `0` if single-module.
- **New public interfaces** — new exports, endpoints, public methods in the diff; `0` if none.

Omit any metric you cannot compute rather than guessing.

Present as one message:

```
[Orientation] → Walkthrough → Detail Pass → Testing → Wrap-Up

> **Intent:** {intent_summary}

N files changed · M modules touched · ~L lines of logic · B boundary crossings · P new public interfaces
```

## Fallback trail generation (only when mode is not `全程轨迹`)

A generated trail is lower quality than an author-produced one, but far better than none. Build it from the diff:

1. Read the changed files in full — hunks alone miss the intent around them. If the total exceeds ~50k tokens, read in full the files with the largest hunks and use hunks for the rest.
2. Identify 2–5 concerns: cohesive design intents that explain the *why* behind a cluster of changes. Prefer functional groupings and architectural boundaries over file-level splits. When a spec exists, anchor concern identification in its Intent section. A single concern is fine — do not invent groupings.
3. Give each concern 1–4 `path:line` stops — entry points, decision points and boundary crossings over mechanical changes. Lead with the entry point (the highest-leverage stop); inside a concern, order stops so each builds on the previous; end with peripherals (tests, config, types).
4. Format each stop:

```
**{Concern name}**

- {one-line framing, ≤15 words}
  `src/path/to/file.ts:42`
```

With only one concern, omit the bold label and list the stops directly.

Announce it — "I built a review trail for this {change_type} (no author-produced trail was found):" — then present the trail. It now serves as the Suggested Review Order: downstream steps treat `mode` as `全程轨迹`. If the diff cannot be retrieved, say "Could not generate trail — git unavailable." and keep the original mode — step 2 carries the non-trail path.

## Write the draft record

Append one record to `{output_dir}/checkpoint.yaml` (create the file when absent: `project: {name, created, updated}` — `name` taken from `diy-coder.yaml` `project.name` — plus an empty `checkpoints` list and `revisions: []`):

```yaml
  - id: CK-001                 # next = highest existing + 1, 3 digits; never renumber, never reuse
    date: YYYY-MM-DD           # today
    change_type: {how the human names it, e.g. commit|branch|PR|auth refactor}
    target: {ref, source, story?, spec?, inferred?}   # copied from the receipt, never retyped from memory
    mode: 全程轨迹|仅规格|裸提交
    concerns: []
    risks: []
    observations: []
    decision: ''               # undecided while drafting
    reason: ''
    next: ''
    status: 草稿
```

`inferred` mirrors the receipt's three values: `true` → write `inferred: true`; `false` → omit the key (a marker is only ever written for `true` — absence is the default, never mint one); `null` (undeterminable — a WORKTREE or range target, say) → omit the key too, and relay the receipt's `inferred_reason` in plain words when one is present — the intent was inferred from the diff and needs a human check.

## Next

Read fully and follow `./02-walkthrough.md`. If the human signals a verdict at any point (in this step or any later one), confirm their intent and go to `./05-wrapup.md` instead.
