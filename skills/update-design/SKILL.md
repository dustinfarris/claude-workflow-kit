---
name: update-design
description: Propagate a completed story's outcomes through the document chain — Plan LOGBOOK, DESIGN body + Changelog, and embedded excerpts in unimplemented stories. Use after every story close-out, whenever the user asks to update the plan or design from implementation, sync documents, or record implementation decisions. This is the document-truthfulness pass; without it the chain rots.
---

# Update Design and Plan after Implementation

Read the `org-conventions` skill bundled in this plugin (`${CLAUDE_PLUGIN_ROOT}/skills/org-conventions/SKILL.md`) before writing any LOGBOOK or Changelog entries — it defines the entry formats, timestamp capture, and the Changelog invariant referenced below.

The user may pass paths when invoking (e.g. `/workflow-kit:update-design PLAN.org DESIGN.org`); otherwise resolve the active initiative directory per org-conventions and use its `PLAN.org` and `DESIGN.org`. The story in scope is the one most recently closed out.

1. Open PLAN.org and update it to reflect current progress based on the story file's checkbox states and LOGBOOK entries from the just-completed implementation. Add a Plan LOGBOOK entry per the LOGBOOK convention for any status updates and implementation notes — observations, decisions made during implementation, deferrals, or context that doesn't change the design but is worth carrying forward. Carry any "Deferred discovery" items from the story's Technical Notes into the Plan's `* Deferred` section.

2. Review the story just closed out in step 1 — its LOGBOOK and its actual implementation — for design changes or pivots, defined as text that needs to be added, removed, or reworded in the body of DESIGN.org. Previously-completed stories are assumed to have landed their own DESIGN updates at completion and are out of scope here. If a design change is warranted, make the body edit first, then add a timestamped Changelog entry that cites the section(s) reworded and characterises the before/after, per the Changelog format in org-conventions.md. **A Changelog entry without a corresponding body edit is never correct** — if an implementation decision clarifies something the design doc already says correctly, record it in the Plan LOGBOOK (step 1) instead, not here. **PRD doorbell:** if a pivot appears to conflict with the Success Criteria in PRD.org — the design is being bent to serve an outcome that no longer holds, rather than merely reworded — STOP and surface the conflict for the human. That is an Amendment question, not a Changelog entry; PRD.org is never edited by this skill or any agent.

3. If step 2 produced any DESIGN body edits, review all unimplemented stories to ensure their embedded Design excerpt sections match the reworded DESIGN body text. If a story's excerpt has drifted from the updated design, revise the excerpt to match. If step 2 made no edits, skip this step.

4. If step 3 produced any story edits, reassess the Plan to verify its accuracy in light of any updates to the design and story set. If step 3 made no edits, skip this step.

5. Final consistency check: confirm Plan, DESIGN, and stories are mutually consistent before stopping. The Plan reflects current implementation status; DESIGN body and Changelog reflect any pivots from this story's implementation; unimplemented stories' embedded excerpts match DESIGN's current text. If any of these is out of sync, return to the appropriate step.

STOP. You are done when these instructions are complete. Do not modify any other files.
