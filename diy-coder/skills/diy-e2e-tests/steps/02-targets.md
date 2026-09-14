# Step 2 — Targets（被测特性识别与 AC 绑定）

Progress: `Detect → [Targets] → Generate API → Generate E2E → Record`

**Read (input):** the confirmed framework from step 1; `{output_dir}/stories.yaml` (locate the target story/AC by ID); the implementation surface.
**Write (output):** an in-conversation target list — feature, entry point, bound AC. No artifact write in this step.

## Identify the features

Three paths, in this order of preference (BMAD step-1 "Identify Features"):

1. **Explicit** — the user named a feature, component, endpoint or file. Take it as the scope; do not widen it.
2. **Directory scan** — the user gave a directory (e.g. `src/components/`). Read that surface and enumerate the testable features it contains.
3. **Auto-discovery** — nothing was named. Discover candidates from the implemented surface: routes/handlers for API tests, pages/components with user-visible flows for E2E. Present the candidates and let the user confirm the subset to cover.

Present the result as a short numbered list: `feature — entry point (path or route) — proposed test layer (api | e2e)`. A feature with no user-visible surface and no API boundary is out of scope — say so instead of inventing a test for it.

## Bind to story + AC — reference, never copy

For each target, locate the story and acceptance criterion in `stories.yaml` that the feature implements:

- Read by ID — search the AC text for the feature's behavior; do not paste AC prose into test titles or steps. The case references `AC-x.y`; its `steps` state concrete verification, not a restatement of the AC.
- The bound AC is what the appended TC carries — never an invented AC, never a range.

**No AC to bind** → the feature is either unplanned or pre-AC. Do not silently attach it to the nearest-looking AC. Record the candidate with the `[ASSUMPTION]` prefix in the conversation and ask the user to adjudicate: bind it to a named existing AC, drop it, or route the gap back to diy-epics-stories. Cases cannot be appended while the binding is unresolved — `record` resolves every `ac` against `stories.yaml` and refuses the whole batch otherwise.

## Cover only what exists

Target the implementation as it stands. A feature the user expects but that is not implemented yet is not a test target here — it is a story-scoping question; note it and move on. This skill never writes implementation code.

## Next

Read fully and follow `./03-generate-api.md`.
