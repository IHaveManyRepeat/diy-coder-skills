# Step 4 — Generate E2E（端到端用例生成与实跑）

Progress: `Detect → Targets → Generate API → [Generate E2E] → Record`

**Read (input):** the target list from step 2; the confirmed framework + existing patterns from step 1; the UI implementation and its routes.
**Write (output):** E2E test files in the project's test directory, and the run results (pass/fail per case) carried into step 5.

## What an E2E case must contain

For each UI target (BMAD step-3):

- **Semantic locators** — role, label, text, placeholder. Never CSS/XPath paths that break on a class rename; a locator tied to an element's meaning survives refactors.
- **A user workflow** — the journey as the user performs it: navigate, interact (click / fill / submit), observe. One linear flow per case; branches that need their own setup become their own case.
- **Visible-outcome assertions** — assert what the user can see (text appears, URL changed, list gained the item), not internal state.
- **Linear and simple** — no fixture composition frameworks, no page-object abstractions, no helper layers invented for a handful of cases (BMAD "Keep It Simple"). Readable beats DRY at this scale.

## Quality gate before running (BMAD checklist, kept as discipline)

Walk each generated case against these before executing:

- Uses the framework's standard APIs and the project's existing test patterns.
- Locators are semantic/accessible; no hardcoded waits or sleeps.
- Cases are independent — no order dependency, no shared mutable state.
- Descriptions say what behavior is verified.
- The test directory layout matches `existing_patterns`.

Fix the case here, not after a flaky run.

## Run them for real (BMAD step-4)

Execute using the project's own test command (from step 1). **A case that has not been executed is not appended** — `record` accepts only `status: 通过|失败`, and the point of this skill is that the appended cases actually ran.

- Failure → fix the test immediately when the test is wrong; when the *implementation* is wrong, do not patch the test to hide it — leave the case red (`status: 失败`) and record the observed-vs-expected evidence for step 5.
- Flakiness → make the wait deterministic (wait on the condition, not the clock) and re-run. Never leave a retry loop in the test.
- Runner unavailable or environment cannot start the system → that is a first-class result: report it, set the affected cases to `失败` only if they actually ran red, and otherwise append nothing for them. Never append an unexecuted case.

## Next

Read fully and follow `./05-record.md`.
