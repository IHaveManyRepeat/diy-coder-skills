# Step 1 — Discovery（脑爆倾倒 + 风险校准 + 工作模式）

Progress: `[Discovery] → Draft → Finalize`（create 路径；update 从 step 4 进入，validate 从 step 5 进入）

**Read (input):** the activation receipt (`intent` / `route` / `counts`); any source material the user points to; `{output_dir}/project-context.yaml` when it exists.
**Write (output):** the discovery message; `{output_dir}/brief.yaml` created with `project` (`status: draft`) and the skeleton the dump has already filled.

## Open the room

The opening move is space for the full picture, not a questionnaire.

1. Invite a brain dump, and ask up front for source material the user already has — memo, deck, transcript, prior brief, chat thread. Paths or paste; big inputs are fine.
2. Read what exists first; ask only what is missing. After the dump, "anything else?" often surfaces what they almost forgot.
3. Drill into specifics only once the broad shape is on the table — premature granular questions interrupt the dump and miss the room.
4. Echo back the domain and the form factor (mobile / web / desktop / multi-surface / hardware / API — what *is* this thing) and how each shapes the approach.

## Ground the picture

- Web-research subagents during the dump: landscape, comparables, current state — AI especially, where training data ages by the week. The subagent searches and the parent gets a digest; extract, don't ingest.
- Persisted project context (optional): when `{output_dir}/project-context.yaml` exists, read its `rules` as background awareness — tech, domain, constraints — so the user is not asked what is already written down.
- Deep work (full market sizing, exhaustive teardowns) → suggest `diy-research`; it is the research skill of this suite, do not attempt it inline here.

## Read the stakes

Early, and in the user's own terms: passion project (**hobby**), internal pitch (**internal**), investor input (**investor**), public launch (**public**). This is `stakes` in brief.yaml and it calibrates how hard you push for the rest of the run.

## Offer the working mode

Once the dump is captured and the stakes are read, in the user's language:

- **Fast path** — batch the remaining gaps into one or two consolidated questions, then draft the full brief with `[ASSUMPTION]` tags where you inferred. The user reviews and we iterate. Best for "I'm pitching tomorrow."
- **Coaching path** — walk through together: pull the picture out, push back where assumptions are thin, draft section by section. Best for "I want a brief I'm proud of and time isn't the constraint."

The coaching posture below shapes the coaching path; the fast path swaps pushback for `[ASSUMPTION]` tags the user can correct in review. The workspace persists — stop and resume freely.

## Put the workspace on disk

Create `{output_dir}/brief.yaml` (create intent only) and tell the user the path:

```yaml
project: {name: <diy-coder.yaml project.name>, status: draft, created: <today>, updated: <today>}
brief: {title: '', stakes: <as read>, problem: '', solution: '', pitch: '',
        users: [], value: [], open_questions: [], assumptions: [], extra_sections: []}
decisions: []
addendum: []
revisions: []
```

From here persistence is real-time: a decision goes into `decisions` with its `rationale` the moment it is made; volunteered depth goes into `addendum` with its `why_separate`; an inference awaiting confirmation is tagged `[ASSUMPTION]` in place and echoed in `brief.assumptions`.

If `brief.yaml` already existed — the `intent` receipt said so, and it warned on create — never silently overwrite: offer to resume the in-progress draft or to run a deliberate update; any rewrite goes through step 4's snapshot discipline.

## Next

Read fully and follow `./02-draft.md`. If the ask turns out to be a change to an existing complete brief, go to `./04-update.md` instead.
