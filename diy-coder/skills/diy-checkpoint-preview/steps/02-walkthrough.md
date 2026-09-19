# Step 2 — Walkthrough（按关注点带看）

Progress: `Orientation → [Walkthrough] → Detail Pass → Testing → Wrap-Up`

**Read (input):** the `mode` and trail from step 1 (the spec's Suggested Review Order, or the trail generated in step 1's fallback); the diff; changed files in full where a hunk is not enough.
**Write (output):** the walkthrough message; the `concerns[]` section of the draft record.

## Rules for this step

- Organize by **concern**, not by file. A concern is a cohesive design intent — e.g. "input validation", "state management", "API contract". One file may appear under several concerns; one concern may span several files.
- The walkthrough activates **design judgment**, not correctness checking. Frame each concern as "here's what this change does and why" — the human judges whether it is the right approach for the system. Correctness hunting is step 3's re-review mode and diy-review's job.

## Build the walkthrough

**With a trail** (`mode: 全程轨迹` — the normal path, including a trail generated in step 1):

1. Read the trail's stops from the spec (or from the conversation when step 1 generated it).
2. Resolve each stop to a location in the current repo and output it as `path:line`.
3. Read the diff to understand what each stop actually does.
4. Group stops by concern — stops sharing a design intent belong together even in different files. A stop may appear under more than one concern when it serves more than one purpose.

**Without a trail** (fallback when trail generation failed, e.g. git unavailable):

1. Get the diff against the baseline established in step 1.
2. Identify concerns by reading the diff for cohesive design intents: functional groupings (what user-facing behavior does each cluster support?), architectural layers (does the change cross API → service → data?), design decisions (where did the author choose between alternatives?).
3. For each concern, pick the key locations as `path:line` stops.

## Order for comprehension

Sequence concerns top-down: the highest-level intent (the "what and why") first, then drill into supporting implementation. Within a concern, order stops so each builds on the previous — the reader should never meet a reference to something they have not seen yet. When the change has a natural entry point (a new public API, a config change, a UI entry point), lead with it.

## Write each concern

1. **Heading** — a short phrase naming the design intent (not a file name, not a module name).
2. **Why** — 1–2 sentences: what problem this concern addresses, why this approach over the alternatives. When the spec documents rejected alternatives, reference them here.
3. **Stops** — one per line: `path:line` followed by a brief phrase (not a sentence) describing what this location does for the concern; keep framing under 15 words per stop.

Target 2–5 concerns for a typical change. A single-concern change is fine — do not invent groupings. More than 7 concerns is a signal that scope may be too large, but present it anyway.

## Present

One message with the progress strip, then each concern group:

```
Orientation → [Walkthrough] → Detail Pass → Testing → Wrap-Up

### {Concern Heading}

{Why — 1–2 sentences}

- `path:line` — {brief framing}
- `path:line` — {brief framing}
```

End the message with:

```
---

Take your time — click through the stops, read the diff, trace the logic. While you are reviewing you can ask for anything, e.g. a deeper pass on one area.

When you're ready, say **next** and I'll surface the highest-risk spots.
```

## Write the record

Append the concerns to this run's record (keep the human's wording where they corrected you):

```yaml
    concerns:
      - name: {design intent, short phrase}
        why: {1–2 sentences in document_output_language}
        sites: [path:line, path:line]
```

## Next

Default: read fully and follow `./03-detail-pass.md`. Early exit: when the human signals a decision about this {change_type} ("let's ship it", "this needs a rethink", "I'm done reviewing"), confirm their intent and go to `./05-wrapup.md`; if you misread them, acknowledge and continue here.
