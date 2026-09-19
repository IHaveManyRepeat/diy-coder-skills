# Step 2 — Context（扫描事实落 YAML）

Progress: `Scan → [Context] → Rules → Finalize`

**Read (input):** the scan receipt from step 1; the source files of a part only when a conditional scan below says so.
**Write (output):** `stack` / `structure` / `architecture` / `integration` in `{output_dir}/project-context.yaml`.

## Read the receipt, do not re-scan

Every mechanical fact this step needs was already computed: parts, types, manifests, stack rows, docs, tree, file/LOC counts. Copy them from the receipt. Re-running the scan by hand is forbidden — a second derivation is a second truth.

One field group per message. Present it, then move on — no mid-group questions.

## stack

Copy the receipt's `stack` rows verbatim: `{part, language, framework, version, notes}`. A row the engine left empty (an unparsed manifest, an unknown language) is closed with the human now, in their words — the empty string stays only until they answer.

## structure

- `tree` — the receipt's `tree` string, annotated as the source workflow annotates it: mark each part's root, the entry points, and the interface paths between parts. An annotated excerpt beats the whole string: keep what a reader needs to navigate.
- `key_dirs` — one entry per critical directory: `{path, purpose}`. Seed it from the receipt's `tree` and `stats`, then add the focus areas the human named in step 1. Purposes are plain language, not restatements of the folder name.

## architecture

One entry per part: `{part, summary, key_points}`.

- `summary` — what this part is, in one or two sentences.
- `key_points` — what an implementer must know: entry points, layers, the conditional scans below.

The **conditional scans** come from the part's `type` (the documentation-requirements judgement, folded here): run only the rows that apply, and put their conclusions into `key_points` as bullets.

| part type | scan | where the conclusion goes |
| --- | --- | --- |
| 网页, 扩展, 桌面端, 移动端 | API contracts · data models · state management · UI components | `key_points` (endpoints / tables / stores / component families) |
| 后端, 数据 | API contracts · data models | `key_points` |
| 命令行, 库, 基础设施 | entry points · public surface | `key_points` |
| 嵌入式 | hardware/pin interfaces when found | `key_points` |
| 游戏, 桌面端, 移动端, 网页, 扩展 | assets (formats, sizes, where they live) | `key_points` |

Respect the level chosen in step 1: **快速** reads no source files — list the directories and patterns only, and say so; **深入** reads the critical directories of the type above; **穷尽** reads all source files, excluding `.git`, `node_modules`, `dist`, `build`, `coverage` — one subfolder at a time, writing each conclusion down before starting the next, and never letting a reading list accumulate in context.

## integration

Multi-part projects only — a monolith omits the key (the engine accepts its absence). One entry per coupling: `{between: [<partA>, <partB>], contract, notes}`. `contract` names the mechanism and its shape (REST `/api/v1`, gRPC service, queue topic, shared database). `notes` carries the data flow and the authentication path in one line. Never invent a coupling to fill the section: a part pair that does not talk simply has no entry.

## What this step does not write

Development and operations facts — prerequisites, install/build/run/test commands, environment setup, deployment and CI, contribution rules — are implementation rules, not scan facts. They land in step 3 as `工作流` and `质量` rules, with commands and paths kept verbatim. The document map is:

| source document (per-project-type in the CSV) | lands in |
| --- | --- |
| index.md | nothing — `project-context.yaml` itself is the retrieval entry point |
| project-overview.md | `architecture[].summary`, `stack` |
| source-tree-analysis.md | `structure.tree`, `structure.key_dirs` |
| architecture-{part}.md | `architecture[]` |
| api-contracts-{part}.md, data-models-{part}.md, component-inventory-{part}.md | `architecture[].key_points` |
| development-guide.md, deployment-guide.md, contribution-guide.md | `rules[]` (categories `工作流`, `质量`) |
| integration-architecture.md, project-parts.json | `integration[]`, `scan.parts` |
| project-scan-report.json | the `scan` block (no state scatter file) |

## Next

Read fully and follow `./03-rules.md`.
