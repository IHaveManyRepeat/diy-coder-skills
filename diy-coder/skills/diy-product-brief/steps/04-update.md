# Step 4 — Update（变更信号对齐）

Progress: `Discovery → Draft → Finalize`（更新从本步进入；收口回到 Finalize）

**Read (input):** `{output_dir}/brief.yaml` in full — brief, `decisions`, `addendum`; the original inputs it cites; the change signal.
**Write (output):** the reconciled `brief.yaml`; new and flipped `decisions`; appended `revisions`.

## Reconcile before patching

Read the brief, the addendum, the decisions and the original inputs, then run the Discovery posture against the change signal itself — what changed, why now, which stakes it touches. A patch applied without context becomes drift; the signal is interrogated, not obeyed.

## Surface conflicts first

Before proposing any change, list every existing decision the signal touches, with its `rationale`, and ask the user to confirm the reversal. A conflict raised before the edit is a decision; the same conflict discovered after the edit is drift. Then make the change together, in the user's language, section by section.

## Snapshot and check (mechanical)

1. `cp {output_dir}/brief.yaml {output_dir}/brief.yaml.prev`
2. Draft the reconciled brief. Flip each superseded decision to `status: 已反转` and append the replacement as the next `BD-###` — never renumber, never reuse, never rewrite the earlier history.
3. Run, with the same `--project-root "{project-root}"` and `--output-dir "{output_dir}"` arguments as activation:
   `python "{project-root}/.claude/skills/diy-product-brief/scripts/brief.py" check --previous {output_dir}/brief.yaml.prev --json`
   Exit 0 = no decision was lost. `ID_UNSTABLE` means the rewrite dropped an id — restore it, do not proceed until the check clears.
4. Delete the `.prev` file. Bump `project.updated` and append `{date, change, reason}` to `revisions` for each amended record.

## Fundamental change

When the signal is fundamental — the problem, the users, or the stakes moved — offer **新建** instead of patching: a brief rebuilt around a new premise is a different brief. Replacing the old file still goes through the snapshot above; nothing is overwritten silently.

## Headless

Do not ask. Log the reversal to `decisions`, then apply. If the intent is still ambiguous after inference, halt `blocked` — zero writes, one-line reason, route.

## Next

Read fully and follow `./03-finalize.md` when the reconciled draft is ready to settle. Read `./05-validate.md` first only when the user wants the change read back critically.
