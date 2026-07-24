---
name: story-closeout
description: Verify and close out an implemented story with subagent audits and evidence-bearing LOGBOOK entries. Use IMMEDIATELY after finishing the implementation of any story from stories/ — whenever implementation work for a story appears complete, whenever the user says a story is done, or whenever they ask to verify, close out, or mark up a story. Never mark story checkboxes without this skill.
---

# Story Close-out

Read the `org-conventions` skill bundled in this plugin (`${CLAUDE_PLUGIN_ROOT}/skills/org-conventions/SKILL.md`) before writing any LOGBOOK entries — it defines the drawer format, timestamp capture, and checkbox semantics used below.

The user may pass the story file path when invoking (e.g. `/workflow-kit:story-closeout stories/story-03-chore-completion.org`); otherwise close out the story that was just implemented in this session.

This skill runs AFTER implementation (the TDD loop) is finished. It does not implement; it verifies, fixes, and records.

1. Dispatch the `story-verifier` subagent to verify the quality of the changes and completeness of each item in ==Acceptance Criteria== and report findings.
2. If the findings from step 1 indicate that any item in ==Acceptance Criteria== is not met, or that there is an issue with the quality of the changes, update the implementation accordingly, and repeat step 1. If the findings from step 1 indicate that all items in ==Acceptance Criteria== are met, and the quality is satisfactory, proceed to step 3.
3. In the story org file, mark each ==Acceptance Criteria== TODO as done (`[X]`), not done (`[ ]`), or deferred (`[-]`), with a LOGBOOK entry per the LOGBOOK convention in org-conventions.md. The entry describes _how_ the item was verified (for `[X]`), _what is missing_ (for `[ ]`), or _why it was deferred_ (for `[-]`). Run `date '+%Y-%m-%d %a %H:%M'` immediately before writing each entry to capture the actual verification time per item. Do NOT mark any item in ==Definition of Done== as done at this time.
4. Dispatch the `story-verifier` subagent to verify each item in ==Definition of Done== and report findings — the verification item is evidenced against the repo's declared `Verify command:` line (CLAUDE.md; defaults per weight class are named in user-stories' Definition of Done blocks).
5. If the findings in step 4 reveal any incomplete items, determine if those findings have merit within the context of this story and, if so, make the appropriate changes and then repeat step 4. Otherwise, if the findings in step 4 indicate that all items in ==Definition of Done== are met, proceed to step 6.
6. In the story org file, mark each Definition of Done TODO as done (`[X]`), not done (`[ ]`), or deferred (`[-]`), with a LOGBOOK entry per the LOGBOOK convention, capturing the actual time per item as in step 3.

A red verify run is never self-ticked. When the check backing an item — the declared `Verify command:`, a test run, or the check the item itself states — fails and the fix loop cannot make it green, do not mark the item `[X]`, and do not reinterpret, narrow, or substitute the item's bar so the failing result clears it. Surface the failure to the human, who may rule a documented deferral: a red-run item is marked `[-]` only on that ruling, and its LOGBOOK entry records the ruling alongside the failing evidence.

Out-of-scope discoveries made during the fix loops (steps 2 and 5) are NOT fixed inline and are NOT written to PLAN.org (this skill never touches it). Record each one in the story's Technical Notes as "Deferred discovery: ..." — the `/workflow-kit:update-design` pass carries them into the Plan's Deferred section afterward.

STOP. You are done when these instructions are complete. Do not modify PLAN.org or the DESIGN document. Suggest running `/workflow-kit:update-design` next.
