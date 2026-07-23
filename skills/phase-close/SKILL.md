---
name: phase-close
description: Closes the open batch in PLAN.org — verification, document reconciliation, advisory pass, and the gate record. Use when a batch or phase is done, when the user says they are ready to gate, or as a pre-milestone check before starting the next batch.
---

# Phase Close

Read the `org-conventions` skill bundled in this plugin (`${CLAUDE_PLUGIN_ROOT}/skills/org-conventions/SKILL.md`) for LOGBOOK, Advisory, and gate-record formats, and for what marks a batch open.

This is the gate skill: it closes the open batch, and it audits rather than maintains. The per-story passes (story-closeout, update-design) already did the maintenance; the gate verifies that work landed and records the crossing.

**Orientation.** Resolve the active initiative directory per org-conventions. The open batch is the batch heading without a gate record (a legacy PLAN with no batch headings is one open batch — the whole story list). If there are zero open batches, or more than one, stop and ask — orientation is ambiguous and closing the wrong batch corrupts the gate structure.

**Precondition.** Every story in the open batch is done or deferred, and update-design has run after the final story. Otherwise say so and stop — a gate closes a finished batch, it does not finish one.

1. Run the repo's declared `Verify command:` (CLAUDE.md); if the line is absent, default per weight class: work-grade runs `mix check`, personal-mvp runs `mix format --check-formatted` and `mix test`. All must pass; fix failures before continuing (test or format fixes only — behavior changes at this stage go through a story). If the PRD declares gate criteria (e.g. an on-device checklist), run them too — where a criterion is a manual check, present it to the human for sign-off; never fake a result.

2. Diff actual behavior against DESIGN.org: walk each Key Behaviors section and confirm the implementation matches. List any divergences. A deliberate divergence with no record means a per-story update-design pass was missed — run update-design retroactively for the affected story so the pivot lands its D-entry, body edit, and Advisory the normal way, rather than patching DESIGN directly here. An accidental divergence is surfaced to the human — that is a bug or an unrecorded pivot, and the human decides which.

3. PLAN reconciliation — audit, don't update. Read the whole open batch cold and verify the per-story record holds: every story's status is truthful and its LOGBOOK captures what was carried forward. A discrepancy means an update-design pass was skipped or failed; run it retroactively for that story so the repair leaves the normal evidence trail. The gate itself writes no PLAN content except the gate record in step 5.

4. Advisory pass: read `* Advisories` in DESIGN.org and withdraw — delete, not annotate — any advisory that no longer protects anything, because no reader could plausibly reintroduce the superseded position now. A withdrawn advisory that generalizes beyond this project is a lesson candidate: note it in the report for later promotion to the repo-level `docs/learnings.org` (see org-conventions' Lessons file section). Git remains the permanent archive.

5. Shared decision log pass: read the repo-level `docs/decisions.org`. This is where lazy repair lands — reconciliation with other chains happens here, at this chain's own gate, never earlier. For any supersession entry minted by another chain that overrules a decision this chain relies on, treat the affected DESIGN text as a divergence per step 2: route the repair through a retroactive update-design pass, never a direct patch. Then audit the sequence: a duplicate D-number (two concurrent sessions minting the same next number — the accepted risk) is repaired here by renumbering the later-committed entry and fixing its citations; a numbering repair is not a decision and mints nothing.

6. Write the gate record on the batch heading per org-conventions: a single-note LOGBOOK drawer with the timestamp, checks run, verdict, and the count of advisories withdrawn/promoted. Its presence is what marks the batch closed.

7. Report a short summary to the user: what shipped, notable pivots (from the Decision Log), and the advisories withdrawn/promoted.

STOP. Do not modify PRD.org. Do not open the next batch — the next user-stories run opens it.
