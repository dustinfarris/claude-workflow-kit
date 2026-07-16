---
name: create-prd
description: Draft a PRD from an approved brainstorm document into PRD-draft.org, then hand the human the rename that locks it in as the invariant contract. Use after a Superpowers brainstorming session produces an approved brainstorm document and before any stories are written — whenever the user asks to create the PRD, draft the PRD, or lock in success criteria. Also use when starting the document chain for any new project.
---

# Create PRD

Read the `org-conventions` skill bundled in this plugin (`${CLAUDE_PLUGIN_ROOT}/skills/org-conventions/SKILL.md`) for the document chain rules.

Input: the approved brainstorm document. The user may pass its path when invoking; otherwise list candidates under `docs/superpowers/specs/` and ask which document to promote — never guess. The brainstorm document predates the PRD: if the human pivoted at PRD review, divergence between it and PRD.org is expected and healthy, not lineage breakage to repair — PRD.org and DESIGN.org supersede it on contact.

1. Read the brainstorm document and extract exactly three things — nothing more:
   - **The problem**: what hurts, for whom, why off-the-shelf doesn't fit.
   - **Success Criteria**: the observable outcomes that define success. Number them (1, 2, 3, ...) — the numbers are stable handles, never renumbered, and downstream artifacts (DESIGN.org's alignment trace, story Acceptance Criteria) cite them as SC-n. Keep these outcome-shaped ("a kid can see today's chores in one tap"), not mechanism-shaped ("the LiveView renders a chore list component"). Mechanisms belong in DESIGN.org.
   - **Out of Scope**: explicit non-goals for this version.

   A brainstorm document may carry a "for the design doc" section (mechanism material parked there per the README's brainstorm kickoff fence) — leave it alone. It is ordinary design feedstock for `/workflow-kit:promote-design`, not something this skill extracts.
2. Create the initiative directory `docs/YYYY-MM-DD-<initiative-slug>/` (date = today, via `date '+%Y-%m-%d'`; slug from the initiative name), then set or update the `Active initiative:` line in the repo's CLAUDE.md to point at it. Write `PRD-draft.org` inside it using the repo-local `templates/PRD.org` if present, otherwise `${CLAUDE_PLUGIN_ROOT}/templates/PRD.org`, filling those three sections and leaving the Amendments section with its protocol comment and "(no amendments)". Do NOT carry over personas, market context, competitive framing, or stakeholder matrices from the brainstorm document — for this document chain, those are ceremony.

   Write to `PRD-draft.org`, never `PRD.org`. The prd-lock hook blocks Write/Edit/MultiEdit on any path ending `PRD.org`, and blocks write-shaped Bash (redirects, `sed -i`, `tee`, `mv`/`cp` onto, `rm`, `truncate`) that targets `PRD.org` — writing `PRD.org` directly at this stage would be blocked by the kit's own hook before a human had approved anything. `PRD-draft.org` matches neither the hook's filename glob nor its Bash regex, so drafting and revision stay unrestricted.
3. For a personal-mvp weight class (check CLAUDE.md), the whole PRD should be around ten lines of content. For work-grade, be as complete as the brainstorm document supports, but every Success Criterion must still be an observable outcome.
4. Iterate on `PRD-draft.org` with the human without restriction — it is a draft, not yet a contract, so edit it as many times as the conversation needs.
5. Before presenting the draft for approval, scrub it for brainstorm-spec references: grep `PRD-draft.org` for "spec §", "brainstorm", and the spec filename pattern. Report every hit, then rewrite each to self-contained wording per org-conventions' Document chain & version control section (the rule lives there, not here). This is a report-then-fix step — list what was found and how each was reworded, never a silent rewrite.
6. When the human is satisfied, present the draft and ask explicitly: "Approve this as the invariant contract? If so, perform the rename yourself: `mv docs/<initiative-dir>/PRD-draft.org docs/<initiative-dir>/PRD.org`. That rename is the approval — after it, agents cannot edit the file, and changes require the human Amendment protocol."
7. After giving that instruction, suggest `/workflow-kit:promote-design` as the next step, noting it will refuse to run until `PRD.org` exists.

Never write, edit, rename, or copy anything onto `PRD.org` — the prd-lock hook blocks every such path by design, and that is not a workaround problem to solve; it is the point. The human's own rename, run in their own shell, is the only approval act. If asked to change an already-approved PRD.org, explain the Amendment protocol in the file's header instead.
