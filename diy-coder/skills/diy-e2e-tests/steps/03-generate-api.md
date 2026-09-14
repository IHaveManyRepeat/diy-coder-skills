# Step 3 — Generate API（接口层用例生成）

Progress: `Detect → Targets → [Generate API] → Generate E2E → Record`

**Read (input):** the target list from step 2; the confirmed framework + existing patterns from step 1; the API implementation (routes, handlers, schemas).
**Write (output):** API test files in the project's test directory — never in `{output_dir}`, never a new artifact.

## What an API case must contain

For each API target (BMAD step-2):

- **Status codes** — the declared success code, plus the plausible failure codes for that endpoint (e.g. 200 happy path; 400 malformed input; 404 unknown resource; 500 only when a real fault path exists — never assert a 500 you cannot trigger deterministically).
- **Response structure** — assert the shape the contract promises (required fields present, types as declared), not the entire payload verbatim.
- **Happy path first**, then 1–2 critical error cases. Two error cases that exercise the same guard are one case written twice — pick the ones that fail differently.
- **Existing patterns** — the runner, assertion style, fixture conventions and file naming come from `existing_patterns`. Imitating the project beats importing a habit from another stack.

## Discipline

- One behavior per case, named so a failure reads as a sentence (`rejects a missing auth header with 401`).
- No sleeps, no ordering dependence between cases: each case sets up what it needs and asserts a visible result.
- A case that cannot state its expected outcome is not a case — drop it and say why; a vague oracle is worse than a missing case.
- Follow the project's existing API-test conventions when they conflict with generic advice above — readability of the suite wins over doctrine.

## Keep the target list honest

If generating an API case exposes that the endpoint's contract is unclear (no schema, no documented error codes), report it and skip that target rather than guessing the oracle. Note the gap for the closing summary — that is a finding about the implementation surface, not a test to fake.

## Next

Read fully and follow `./04-generate-e2e.md`.
