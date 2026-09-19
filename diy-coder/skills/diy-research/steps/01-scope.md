# Step 1 — Scope（主题范围与目标确认）

Progress: `[Scope] → <dimension> 02–05 → Synthesis`

**Read (input):** the conversation before activation; any input the user names (brief, prior notes, transcripts).
**Write (output):** the draft record in `{output_dir}/research.yaml` (`id` / `dimension` / `topic` / `goals` / `scope` / `date` / `status: 草稿` / `findings: []`); the scope message.

## Discover the topic

The conversation before activation IS the starting point — not a blank slate. Find the topic, problem or area the user wants researched. Ask only what is still missing:

**What topic, problem, or area do you want to research?** — e.g. "the electric vehicle market in Europe", "React vs Vue for large-scale applications", "sustainable packaging regulations in Europe".

## Clarify (three questions, one round)

1. **Core focus** — "What exactly about {topic} are you most interested in?"
2. **Research goals** — "What do you hope to achieve with this research?" → these become `goals`.
3. **Scope and approach** — "Should we focus broadly or dive deep into specific aspects?" — segments, geographic regions, purpose (market entry / expansion / product development), and any competitor or segment the user wants analysed by name → this becomes `scope`.

Do not research yet. This step confirms understanding and scope only.

## Settle the dimension

- **市场** — customers and competition: behavior and segments, pain points, decision processes, competitive landscape.
- **技术** — technologies and architecture: stack, integration patterns, architectural patterns, performance and scalability, implementation paths.
- **领域** — industry and ecosystem: industry analysis (size, economics, value chain), competitive landscape, regulatory environment, technology trends.

One record = one dimension of one topic. A user who wants two dimensions gets two records (`RS-###`), each with its own goals and scope. When the choice is genuinely ambiguous, ask — never silently pick one.

## Confirm the prerequisite

**Web search is required.** If it is unavailable, abort here, tell the user, and write nothing.

## Write the draft record

Append one record to `{output_dir}/research.yaml` (create the file when absent: `project: {name, created, updated}` — `name` taken from `diy-coder.yaml` `project.name` — plus an empty `researches` list and `revisions: []`):

```yaml
  - id: RS-001                 # next = highest existing + 1, 3 digits; never renumber, never reuse
    dimension: 市场          # 市场 | 技术 | 领域
    topic: {the user's own words}
    goals: [{from question 2}]
    scope: {from question 3}
    date: YYYY-MM-DD
    status: 草稿
    findings: []               # the analysis steps append here, one entry at a time
```

Source naming rule carried over: the source skills wrote `<dimension>-<slug>-research-<date>.md` and derived a path-safe slug from the topic. The diy artifact is one fixed file, so `dimension` + `topic` + `date` carry that identity and no path or slug is derived.

## Confirm and continue

Present the understanding back — topic, goals, dimension, scope, and the four analysis steps the dimension will cover — then halt:

```
Scope: {topic} — {dimension}

Ready to begin the {dimension} analysis?
[C] Continue - Confirm scope and proceed to the first analysis step
[Modify] Change the scope before proceeding
```

HALT — wait for the user. On 'Modify', gather the changes, update the record, and present again. On 'C', read fully and follow the dimension's step 2.

## Next

市场 → `steps/market/02-customer-behavior.md`; 技术 → `steps/technical/02-stack.md`; 领域 → `steps/domain/02-industry.md`. Read only the one that matches the record's `dimension`.
