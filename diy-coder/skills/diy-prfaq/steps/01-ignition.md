# Step 1 — Ignition（点火）

Progress: `[Ignition] → Press Release → Customer FAQ → Internal FAQ → Verdict`

**Read (input):** the `headless` receipt from On Activation (headless mode); the `prfaq.stage` anchor when resuming; whatever the user brings — an idea, notes, product intent, or paths to documents.
**Write (output):** the ignition message; the draft `{output_dir}/prfaq.yaml` (`project` block, `prfaq.stage: 1`, `prfaq.concept_type`, `prfaq.essentials`, empty stage containers, `distillate` skeleton, `revisions: []`).

## Set the tone, then ground the method

Open cold — this is not a warm exploratory greeting. Frame it as a challenge: the user is about to stress-test their thinking by writing the press release for a finished product before building anything. Surviving this process means the concept is ready; failing here saves wasted effort. Be direct and energizing.

Then ground the method in three sentences: Amazon's Working Backwards — write the finished-product press release first, then answer the hardest customer and stakeholder questions. The point is forcing clarity before committing resources.

## Customer-first enforcement

Where the user starts decides what you push on:

- **Leads with a solution** ("I want to build X") → redirect to the customer's problem. Don't let them skip the pain.
- **Leads with a technology** ("I want to use AI / blockchain / etc.") → challenge harder. Technology is a "how", not a "why" — push them to articulate the human problem. Strip away the buzzword and ask whether anyone still cares.
- **Leads with a customer problem** → dig deeper into specifics: how they cope today, what they've tried, why it hasn't been solved.

When the user is stuck, offer concrete suggestions built on what they have shared so far — draft a hypothesis for them to react to rather than repeating the question harder.

## Concept type detection

Early in the conversation, identify which of these this is and store it as `prfaq.concept_type`:

| The user is building | `concept_type` | Stage 3-4 framing |
| --- | --- | --- |
| a commercial product | `商业` | default commercial framing |
| an internal tool | `内部` | stakeholder value, adoption path, maintenance |
| an open-source project | `开源` | adoption strategy, contributors, sustainability |
| a community / nonprofit initiative | `社区` | stakeholder value, participation, sustainability |

Non-commercial concepts don't have "unit economics" or "first 100 customers" — Stages 3 and 4 adapt the framing to stakeholder value, adoption paths and sustainability instead.

## The four essentials

Stage 1 ends when you have enough clarity on these to draft a press release headline. Capture them in conversation, then write them into `prfaq.essentials`:

- **Who is the customer / user?** — a specific persona, not "everyone".
- **What is their problem?** — concrete and felt, not abstract.
- **Why does this matter to them?** — stakes and consequences.
- **What's the initial concept for a solution?** — even rough.

Specificity is your judgment; presence and non-emptiness are the engine's (`headless` gate, and every `check`).

**Fast-track:** the user provides all four essentials in the opening message (or via structured input) → acknowledge, confirm your understanding, create the document and go to Stage 2 without extended discovery.

**Graceful redirect:** if after 2-3 exchanges the user still can't articulate a customer or problem, don't force it. Say the idea needs more exploration first — a dedicated brainstorming pass — and stop there. A PRFAQ built on nothing produces only a hollow press release; the honest exit is a win too.

## Contextual gathering

1. **Ask about inputs.** Ask whether the user has existing documents, research, brainstorming material or other sources to inform the PRFAQ. Collect paths for the subagents — do not read user-provided files yourself; that is the artifact analyzer's job.
2. **Fan out both subagents in one message (parallel).** Each receives the product intent summary (customer, problem, solution direction, domain).

   **Artifact analyzer** — *Process:* scan the planning-artifact directory and the project knowledge folders for documents that could be relevant, by name pattern: brainstorming/ideation, research/analysis/findings, context/overview/background, brief/summary, plus any markdown, text or structured document that looks relevant; a sharded document (a folder with `index.md` plus parts) → read the index first, then only the relevant parts; a very large document (estimated >50 pages) → table of contents, executive summary and section headings first, read only the sections directly relevant to the intent, and note which sections were skimmed versus read fully; issue all reads in a single message, not one at a time; ignore documents that aren't relevant. *Extract:* insights bearing on the intent, market and competitive information, user research or personas, technical context and constraints, ideas **both accepted and rejected** (rejected ideas prevent re-proposing), metrics and data points. *Return ONLY this JSON*, no preamble, under 1,500 tokens, at most 5 bullets per section:
   ```json
   {"documents_found": [{"path": "...", "relevance": "one line"}],
    "key_insights": ["self-contained bullet"],
    "user_market_context": ["..."],
    "technical_context": ["..."],
    "ideas_and_decisions": [{"idea": "...", "status": "accepted|rejected|open",
                             "rationale": "brief why"}],
    "raw_detail_worth_preserving": ["details, data points, quotes"]}
   ```

   **Web researcher** — *Process:* identify search angles from the intent — direct competitors, adjacent solutions to the same pain, market size and trends, industry news creating opportunity or risk, user sentiment about existing solutions; run 3-5 targeted searches (quality over quantity), shaped like `"[problem domain] solutions comparison"`, `"[competitor] alternatives"`, `"[industry] market trends [current year]"`, `"[target user type] pain points [domain]"`; synthesize the signal, don't list links. *Return ONLY this JSON*, under 1,000 tokens, at most 5 bullets per section:
   ```json
   {"competitive_landscape": [{"name": "...", "approach": "...", "gaps": "..."}],
    "market_context": ["..."],
    "user_sentiment": ["..."],
    "timing_and_opportunity": ["..."],
    "risks_and_considerations": ["..."]}
   ```

3. **Graceful degradation:** subagents unavailable → scan the most relevant 1-2 documents inline and run targeted searches directly. Never block the workflow.
4. **Merge findings** with what the user shared; surface anything surprising that enriches or challenges their assumptions before drafting begins.

## Create the draft document

Write `{output_dir}/prfaq.yaml` — the single source every later stage updates:

```yaml
project: {name: <diy-coder.yaml project.name>, status: 草稿, created: <today>, updated: <today>}
prfaq:
  stage: 1
  concept_type: <detected>
  essentials: {customer: ..., problem: ..., stakes: ..., solution: ...}
  press_release: {}
  customer_faq: []
  internal_faq: []
  verdict: {}
distillate: {problem: ..., target_users: [<string>], value_props: [], constraints: [], open_questions: []}
notes: []
revisions: []
```

## Coaching notes capture → `notes` + the distillate

Two destinations, two jobs — keep them separate. **`notes` is the process narrative** (the diy form of the source's `<!-- coaching-notes-stage-1 -->` block, which must survive context compaction); **`distillate` is the machine contract** downstream `diy-prd` consumes, so it stays a clean summary with no process commentary.

Append one entry to `notes` for this stage:

```yaml
notes:
  - stage: 1
    content: <concept type and why; the assumptions you challenged; the coaching process behind the direction call; the subagent discovery process; user context that fits nowhere else>
```

Then route the downstream-relevant items into the five buckets (every later stage uses the same split):

- `distillate.problem` — the problem as sharpened, plus requirements signals it implies.
- `distillate.target_users` — who it serves: personas, market, adoption population.
- `distillate.value_props` — what survived: differentiators, the claims that held up.
- `distillate.constraints` — technical context, platform preferences, scope signals (in / out / maybe), resource and timeline estimates, hard limits, **anything rejected for a reason downstream must not re-propose, written as a constraint — `Not <X>: because <Y>`** (this is what stops the PRD from re-proposing a dropped option), and competitive intelligence that is settled and affects what gets adopted.
- `distillate.open_questions` — unknowns, unresolved items (including competitive intelligence still open), and later the verdict's "needs more heat" / "cracks" points as actionable entries.

A rejection is a constraint, not a story: the *why* travels with the *what* so the entry stands alone for a downstream reader. The coaching process around it — what was tried, what was explored and set aside, how the alternatives felt — stays in `notes`.

## Headless mode

The gate already passed at activation. Run this step non-interactively: skip the tone-setting and enforcement sections (they need a human), fan out the two subagents over whatever material the caller provided, create the draft document, and seed `distillate` from the subagent summaries. Beyond the four required essentials, optional inputs are welcome whenever the caller provides them: competitive context, technical constraints, team/org context, target market, existing research.

Record the source documents actually used (the artifact analyzer's `documents_found`) as one `distillate.constraints` bullet — diy has no frontmatter `inputs` field, and the trail must survive so downstream can trace where a claim came from.

Then route straight to Stage 2 and run Stages 2-5 without interaction; there, mark every low-confidence answer with the `[假设]` prefix so a human can review it later.

## Next

Enough clarity on customer, problem and solution to draft a press release headline (or headless mode reached document creation) → read fully and follow `./02-press-release.md`.
