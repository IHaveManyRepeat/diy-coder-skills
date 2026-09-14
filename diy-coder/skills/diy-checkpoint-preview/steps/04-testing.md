# Step 4 — Testing（亲手验证）

Progress: `Orientation → Walkthrough → Detail Pass → [Testing] → Wrap-Up`

**Read (input):** the diff and the spec; the concerns and risk spots already presented in steps 2–3.
**Write (output):** the observation suggestions message; the `observations[]` section of the draft record.

## Rules for this step

- This is **experiential**, not analytical. The detail pass asked "did you think about X?" — this says "you could see X with your own eyes."
- Do not prescribe. The human decides whether observing a behavior is worth their time: frame suggestions as options, not obligations.
- Do not duplicate CI, test suites or automated checks — assume they exist and work. This is about manual observation, the kind of confidence no automated test provides.
- If the change has no user-visible behavior, say so explicitly. Do not invent observations.

## Identify observable behavior

Scan the diff and the spec for changes that produce behavior a human could directly observe:

- **UI changes** — new screens, modified layouts, changed interactions, error states
- **CLI/terminal output** — new commands, changed output, new flags or options
- **API responses** — new endpoints, changed payloads, different status codes
- **State changes** — database records, file system artifacts, config effects
- **Error paths** — bad input, missing dependencies, edge conditions

For each observable behavior, determine:

1. **What to do** — the specific action (command to run, button to click, request to send)
2. **What to expect** — the observable result that confirms the change works
3. **Why bother** — one phrase connecting this observation to the change's intent (omit when obvious from context)

Target 2–5 suggestions for a typical change. More than 5 qualifying → prioritize by how much confidence the observation buys relative to effort. Zero observable behavior is fine — do not pad with trivia.

## Present

One message:

```
Orientation → Walkthrough → Detail Pass → [Testing] → Wrap-Up

### How to See It Working

**{Brief description}**
Do: {specific action}
Expect: {observable result}
```

Use code blocks for commands or requests. When there is no observable behavior, replace the suggestions with:

```
### How to See It Working

This change is internal — no user-visible behavior to observe. The diff and tests tell the full story.
```

End with:

```
---

You've seen the change and how to verify it. When you're ready to make a call, just say so.
```

## Write the record

Append to this run's record (empty list is a valid outcome — say so in the message):

```yaml
    observations:
      - {do: specific action, watch: observable result, why: one phrase}
```

## Next

When the human signals they are ready to decide about this {change_type}, read fully and follow `./05-wrapup.md`.
