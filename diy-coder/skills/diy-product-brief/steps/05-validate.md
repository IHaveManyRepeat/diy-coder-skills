# Step 5 — Validate（对照简报自身目的的诚实点评）

Progress: `Discovery → Draft → Finalize`（validate 从本步进入；结论回对话，不写产物）

**Read (input):** `{output_dir}/brief.yaml` — brief, `decisions`, `addendum`; the original inputs the user supplied.
**Write (output):** nothing on disk. The critique returns inline in the conversation, `communication_language` — no separate file unless the user asks for one.

## Ground the critique

Judge the brief against its own purpose, not a generic template: as a **hobby** brief, as an **internal** pitch, as **investor** input, as a **public** launch. A validation that ignores prior decisions, reversed ideas, or the context the user supplied is shallow — read `decisions` and `addendum` first, then hold the brief to what it set out to do at its own `stakes`.

## What to examine

- **Problem → solution fit:** does `solution` actually answer the `problem` as stated, at the stated stakes?
- **Evidence:** do the `value[].point` claims carry `evidence`, or are they assertions? A fabricated moat is the exact failure this brief exists to prevent — name it if you see it.
- **Users:** are `users` specific enough to design for, or a demographic?
- **Unknowns:** are the real unknowns in `open_questions`, or are unexamined assumptions hiding as prose? Thin answers get pushback here exactly as in drafting.
- **Coherence:** does the whole read as one product's story within 1-2 pages, with overflow living in `addendum`?

## Cite specific lines

Quote the sentence being judged — from `problem`, `pitch`, a `value` entry, a decision `rationale` — and say what it does and does not establish. Caveat what cannot be evaluated from the file alone (market facts, internal constraints, the user's unstated intent). Confirm what is strong as plainly as what is weak: a validation that only faults is not honest either.

## Return inline and offer the route

Deliver the critique in the conversation, ordered by what matters most. Always close by offering to roll the findings into an update — never end without that offer; in headless mode set `"offer_to_update": true` in the JSON status block.

## Next

Read fully and follow `./04-update.md` when the user takes the offer. Otherwise the run ends here — the critique stays in the conversation and nothing is written.
