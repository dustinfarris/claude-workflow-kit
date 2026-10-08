---
name: story-closeout
description: Verify and close out an implemented story with subagent audits and evidence-bearing LOGBOOK entries. Use IMMEDIATELY after finishing the implementation of any story from stories/ — whenever implementation work for a story appears complete, whenever the user says a story is done, or whenever they ask to verify, close out, or mark up a story. Never mark story checkboxes without this skill.
model: sonnet
---

# Story Close-out

Read the `org-conventions` skill bundled in this plugin (`${CLAUDE_PLUGIN_ROOT}/skills/org-conventions/SKILL.md`) before writing any LOGBOOK entries — it defines the drawer format, timestamp capture, and checkbox semantics used below.

The user may pass the story file path when invoking (e.g. `/workflow-kit:story-closeout stories/story-03-chore-completion.org`); otherwise close out the story that was just implemented in this session.

This skill runs AFTER implementation (the TDD loop) is finished. It does not implement; it verifies, fixes, and records.

1. Dispatch the `story-verifier` subagent once to verify the quality of the changes and the completeness of each item in ==Acceptance Criteria== and ==Definition of Done== together, and report findings in checklist order: Acceptance Criteria items first, then Definition of Done items. The Definition of Done items are evidenced against the repo's declared `Verify command:` line (CLAUDE.md; defaults per weight class are named in user-stories' Definition of Done blocks), which the verifier runs once for the whole pass.
2. If the findings from step 1 indicate that any item in either section is not met, or that there is an issue with the quality of the changes, determine whether those findings have merit within the context of this story and, if so, make the appropriate changes. Any change after a pass re-runs the full step 1 check before anything is ticked: a fix to the code for an Acceptance Criteria finding, a fix for a Definition of Done finding, and a human ruling that changes an item's state (a deferral, a retirement) even when no code changes. Repeat until a pass finds every item in both sections met or ruled deferred by the human and the quality satisfactory, then proceed to step 3.
3. On the findings of the last step 1 pass, mark each ==Acceptance Criteria== and ==Definition of Done== TODO in the story org file as done (`[X]`), not done (`[ ]`), or deferred (`[-]`), with a LOGBOOK entry per the LOGBOOK convention in org-conventions.md. The entry describes _how_ the item was verified (for `[X]`), _what is missing_ (for `[ ]`), or _why it was deferred_ (for `[-]`). An item that a step 2 fix touched also names the finding the fix answered (the missing assertion, the over-long comment), so the story file shows the fix loop and not only its result. Run `date '+%Y-%m-%d %a %H:%M'` immediately before writing each entry to capture the actual verification time per item.

Every story gets this one verifier dispatch, covering Acceptance Criteria and Definition of Done together, whatever its size and at every weight class; a restyle or fix-up story is no exception. No checkbox, Acceptance Criteria or Definition of Done, is ever ticked without this close-out's own verifier pass over the final code behind it: a fresh test run, a green `Verify command:`, or an earlier pass is evidence for the verifier to cite, not a substitute for its pass. If the last step 1 pass predates the last change, step 3 does not happen.

A red verify run is never self-ticked. When the check backing an item — the declared `Verify command:`, a test run, or the check the item itself states — fails and the fix loop cannot make it green, do not mark the item `[X]`, and do not reinterpret, narrow, or substitute the item's bar so the failing result clears it. Surface the failure to the human, who may rule a documented deferral: a red-run item is marked `[-]` only on that ruling, and its LOGBOOK entry records the ruling alongside the failing evidence.

Out-of-scope discoveries made during the fix loop (step 2) are NOT fixed inline and are NOT written to PLAN.org (this skill never touches it). Record each one in the story's Technical Notes as "Deferred discovery: ..." — the `/workflow-kit:update-design` pass carries them into the Plan's Deferred section afterward.

STOP. You are done when these instructions are complete. Do not modify PLAN.org or the DESIGN document. Suggest running `/workflow-kit:update-design` next.
