---
name: phase-close
description: Close out a completed phase — verify the suite, reconcile documents against actual behavior, and promote deferrals to v2 candidates. Use when all stories in PLAN.org are closed out, when the user says the phase or MVP is done, or when they ask to wrap up, ship, or review what was built before starting the next phase.
---

# Phase Close

Read the `org-conventions` skill bundled in this plugin (`${CLAUDE_PLUGIN_ROOT}/skills/org-conventions/SKILL.md`) for LOGBOOK and Changelog formats.

Preconditions: every story in PLAN.org is marked done or deferred, and `/update-design` has run after the final story. If either is false, say so and stop — this gate closes a finished phase, it does not finish one.

1. Run the full verification appropriate to the weight class in CLAUDE.md: work-grade runs `mix check`; personal-mvp runs `mix format --check-formatted` and `mix test`. All must pass; fix failures before continuing (test or format fixes only — behavior changes at this stage go through a story).
2. Diff actual behavior against DESIGN.org: walk each Key Behaviors section and confirm the implementation matches. List any divergences found. For each deliberate divergence not yet recorded, make the DESIGN body edit and paired Changelog entry now (per the invariant in org-conventions.md). For each accidental divergence, surface it to the user — that is a bug or an unrecorded pivot, and the human decides which.
3. Confirm PLAN.org reads as an accurate record of what was actually built: every story's status is truthful, and LOGBOOK entries capture the decisions worth carrying forward. Fill gaps with dated LOGBOOK entries.
4. Promote the Plan's `* Deferred` section into a `* v2 Candidates` section: for each item, one line on what it is and why it was deferred. Do not design them.
5. Report a short phase summary to the user: what shipped, notable pivots (from the Changelog), and the v2 candidate list. Note which workflow stages earned their keep at this weight class and which felt like ceremony — that feedback tunes the toggles.

STOP. Do not modify PRD.org. Do not begin v2.
