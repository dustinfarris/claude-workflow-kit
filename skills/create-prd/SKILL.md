---
name: create-prd
description: Turn an idea into PRD.org through a conversation held at outcome altitude — what hurts, for whom, what a user would observe if it worked, what is out of scope, and whether it should be built at all. Use whenever the user brings an idea for a new feature, capability, or initiative — "I have an idea", "I've been thinking about", "what if it could", "should we build" — BEFORE any brainstorming, even when the request sounds like a build request. Also use when the user asks to create the PRD, draft the PRD, or lock in success criteria, or when starting the document chain for any new project. Not for bugs, bounded changes to existing behavior, or refactors — those go straight to Superpowers.
model: opus
---

# Create PRD

Read the `org-conventions` skill bundled in this plugin (`${CLAUDE_PLUGIN_ROOT}/skills/org-conventions/SKILL.md`) for the document chain rules.

This skill is the conversation that turns an idea into PRD.org, and it runs before any brainstorm: do not invoke `superpowers:brainstorming` during this stage, whatever the request sounds like. Brainstorming is the design conversation, and it starts only once PRD.org exists. Input is the idea as the human brings it, in whatever state — a sentence, a paragraph, a half-formed thought. The user may pass it inline when invoking; otherwise ask for it. If the human arrives with an existing brainstorm document instead of an idea, treat the document as the idea: reflect it back and run the same conversation.

## The conversation

Open by reflecting the idea back in two or three sentences — what you heard, and what kind of thing it seems to be — then ask one question. Do not classify the request or announce a path; routing has already happened by the time this skill runs.

Altitude rule: before asking any question, apply one test — could the answer change the outcomes? Questions that pass: who hurts, why now, what a user would observe if it worked, what this deliberately is not, whether there is a cheaper way to reach the same outcome. A question whose answer can only change the mechanism is a design question; do not ask it. One question per message; offer multiple choice where it helps.

Parking: when either of you drifts into mechanism — schemas, module names, screens, test plans, library choices — write one line to SKETCH.org (below), say so in a clause, and return to the outcome question. Material the human volunteers "for the design" goes there the same way, without comment. Nothing parked is argued during this stage.

Ask the existence question out loud at least once; never leave it implicit: is the pain real enough to build for, could something that already exists cover it, could this be nothing.

Soft bound: there is no turn count. If the conversation circles, say so, state what is settled and what is not, and ask which unsettled item to take next.

## SKETCH.org

The initiative directory `docs/YYYY-MM-DD-<initiative-slug>/` (date = today, via `date '+%Y-%m-%d'`; slug from the working name of the idea) is created at the first parked line or the first PRD draft, whichever comes first; set or update the `Active initiative:` line in the repo's CLAUDE.md at the same moment, noting its previous value. Create `SKETCH.org` in the directory from the repo-local `templates/SKETCH.org` if present, otherwise `${CLAUDE_PLUGIN_ROOT}/templates/SKETCH.org`, and append parked thoughts as list items, one per line, in the order they came up. No LOGBOOK, no timestamps, no sections. SKETCH.org has no authority and is never cited by any chain document; DESIGN.org supersedes it on contact.

## Exit

When you believe you can state the problem, the success criteria, and the non-goals, say so and propose one of four verdicts. The human rules; never assume the verdict.

1. **Write the PRD.** Continue with Drafting the PRD below.
2. **Set aside.** Append a dated heading to `docs/backlog.org` (create the file with a `#+title:` line if absent): the idea in a sentence, the verdict, the reason in the human's words, and the parked lines from SKETCH.org if any. Then remove the initiative directory this conversation created — it holds only SKETCH.org — and restore the `Active initiative:` line to its previous value. A set-aside idea is reopened by starting a new conversation from its backlog entry. STOP.
3. **Different idea.** Write the same backlog entry for the original idea, with one line naming the idea that emerged, remove the initiative directory if one was created and restore the `Active initiative:` line (as in verdict 2), then restart the conversation on the new idea from the top of this skill.
4. **Bounded, no chain.** Too small for a document chain. State what was settled in a few lines so the brainstorm does not re-ask it, remove the initiative directory if one was created and restore the `Active initiative:` line (as in verdict 2), and hand the human to Superpowers directly. STOP.

## Drafting the PRD

1. From the conversation, extract exactly three things — nothing more:
   - **The problem**: what hurts, for whom, why off-the-shelf doesn't fit.
   - **Success Criteria**: the observable outcomes that define success. Number them (1, 2, 3, ...) — the numbers are stable handles, never renumbered, and downstream artifacts (DESIGN.org's alignment trace, story Acceptance Criteria) cite them as SC-n. Keep these outcome-shaped ("a kid can see today's chores in one tap"), not mechanism-shaped ("the LiveView renders a chore list component"). Mechanisms belong in SKETCH.org now and DESIGN.org later.
   - **Out of Scope**: explicit non-goals for this version.
2. Create the initiative directory if the conversation has not already (see SKETCH.org above), then write `PRD-draft.org` inside it using the repo-local `templates/PRD.org` if present, otherwise `${CLAUDE_PLUGIN_ROOT}/templates/PRD.org`, filling those three sections and leaving the Amendments section with its protocol comment and "(no amendments)". Do NOT carry over personas, market context, competitive framing, or stakeholder matrices — for this document chain, those are ceremony.

   Write to `PRD-draft.org`, never `PRD.org`. The prd-lock hook blocks Write/Edit/MultiEdit/NotebookEdit on any path ending `PRD.org`, and blocks write-shaped Bash (redirects, `sed -i`, `tee`, `mv`/`cp` onto, `rm`, `truncate`) that targets `PRD.org` — writing `PRD.org` directly at this stage would be blocked by the kit's own hook before a human had approved anything. `PRD-draft.org` matches neither the hook's filename glob nor its Bash regex, so drafting and revision stay unrestricted.
3. For a personal-mvp weight class (check CLAUDE.md), the whole PRD should be around ten lines of content. For work-grade, be as complete as the conversation supports, but every Success Criterion must still be an observable outcome.
4. Iterate on `PRD-draft.org` with the human without restriction — it is a draft, not yet a contract, so edit it as many times as the conversation needs.
5. Before presenting the draft for approval, scrub it for references to scratch material: grep `PRD-draft.org` for "SKETCH", "spec §", and "brainstorm". Report every hit, then rewrite each to self-contained wording per org-conventions' Document chain & version control section (the rule lives there, not here). This is a report-then-fix step — list what was found and how each was reworded, never a silent rewrite.
6. When the human is satisfied, present the draft and ask explicitly: "Approve this as the invariant contract? If so, perform the rename yourself: `mv docs/<initiative-dir>/PRD-draft.org docs/<initiative-dir>/PRD.org`. That rename is the approval — after it, agents cannot edit the file, and changes require the human Amendment protocol."
7. After giving that instruction, name the next step: the design brainstorm. State the hand-off as one sentence — PRD.org is the fixed contract, SKETCH.org is the starting material — and remind the human to run `/model opus` and open a fresh session with "let's design <initiative>". `/workflow-kit:promote-design` follows the brainstorm, and refuses to run until `PRD.org` exists.

Never write, edit, rename, or copy anything onto `PRD.org` — the prd-lock hook blocks every such path by design, and that is not a workaround problem to solve; it is the point. The human's own rename, run in their own shell, is the only approval act. If asked to change an already-approved PRD.org, explain the Amendment protocol in the file's header instead. Never write DESIGN.org.

STOP. You are done when the rename instruction and the hand-off have been given, or when a set-aside or bounded verdict has been recorded as described above. A different-idea verdict does not end the skill: it restarts the conversation, which ends at whichever of the other three verdicts the restart reaches.
