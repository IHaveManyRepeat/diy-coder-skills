# Step 5 — Deep-Dive（单区域逐文件深挖）

Progress: `Scan → [Deep-Dive] → Finalize`

**Read (input):** the scan receipt and `structure` from step 1; then every file in the chosen area, in full.
**Write (output):** one `deep_dives[]` entry in `{output_dir}/project-context.yaml`; `revisions` when a rule changes.

## The rule that governs this whole step

Deep-dive mode requires **literal full-file review**. Sampling, guessing, or relying on tooling output alone is FORBIDDEN. Every file in scope is read line by line, and every claim in the entry traces to what was actually read.

## 5a — Choose the area

Offer what the scan already knows, then take a custom path. For each part, derive candidate areas from `structure.key_dirs` and the receipt's file counts:

```
What area should I deep-dive?

1. {part.name} / {dir} — {n} files
2. {part.name} / {dir} — {n} files
   ... or name a folder, a file, or a feature.

This reads EVERY file in the area.
```

HALT — wait for the choice. Confirm the scope back with the type (folder / file / feature), the path, and the file count, and let the human narrow it. A file-scoped dive also covers its direct imports one level deep and asks who imports it; a feature-scoped dive pulls in the UI, the endpoints, the models, the services and the tests that implement it.

## 5b — Read it all

Walk the area — `git ls-files`/`ls`, excluding `node_modules`, `.git`, `dist`, `build`, `coverage`, `*.min.js`, `*.map` — and for every remaining file read the complete contents, in batches per subfolder, writing conclusions down before opening the next batch. For each file capture:

- purpose in one or two plain sentences (behaviour, side effects, assumptions a modifier must know);
- exports with signatures, and imports (what it depends on);
- who imports it (its dependents);
- notable logic, state handling, side effects (I/O, network, database), error handling;
- TODOs / FIXMEs and the associated tests.

A file you could not read is named as unread in the entry — never silently dropped.

## 5c — Relationships and data flow

Build the picture across the files just read: the dependency edges between them, circular dependencies if any, entry points (nothing in scope imports them) and leaf nodes. Then trace the flow end to end — where data enters, how it is transformed, where it leaves — and name the integration points: external APIs consumed, internal services called, shared state touched, events published or subscribed, tables read or written.

## 5d — Related code outside the area

Search the rest of the codebase for the same shapes: similar naming, similar signatures, an established pattern this area should follow, utilities that already solve part of the problem. Name the reuse opportunities concretely (`path:line`), and say when an existing pattern is deliberately not followed.

## 5e — Write the entry

Append to `deep_dives[]`:

```yaml
- area: <the area, as the human named it>
  date: <today>
  files_scanned: <n>            # every file in scope; unread ones named in notes
  findings:                     # one line each, plain language, no code dumps
    - <what this area is and how it is entered>
    - <the dependency / data-flow facts that matter>
    - <reuse opportunities and the patterns to follow>
  notes: <risks, gotchas, verification steps before changing this area, tests to run>
```

`findings` carries conclusions, not process — the reading trail stays in the conversation. Aggregate the risks and the verification steps collected per file into `notes`; a deep dive that changes an existing rule amends that rule and appends to `revisions`.

## 5f — Update the index

The file itself is the index: the new entry is its own navigation. Bump `project.updated`, and when the dive covered a directory that was not yet in `structure.key_dirs`, add it with its purpose.

## 5g — Continue or finish

```
Deep dive complete: {area} — {files_scanned} files.

1. Deep-dive another area
2. Finish
```

HALT — wait. **1** returns to 5a with a fresh area. **2** goes to the finalize step below.

## Next

Read fully and follow `./04-finalize.md` — the final gate runs there and covers everything this step wrote.
