---
name: promote-design
description: Promote an approved brainstorm document into DESIGN.org with Decision Log and Advisories scaffolding, running the skeptic design review for work-grade projects. Use after PRD.org exists and before user stories are written — whenever the user asks to create the design doc, promote the design, or run a design review. This is the boundary where the durable org document chain begins.
---

# Promote Design

Read the `org-conventions` skill bundled in this plugin (`${CLAUDE_PLUGIN_ROOT}/skills/org-conventions/SKILL.md`) for the document chain rules.

Input: the approved brainstorm document (same source `/workflow-kit:create-prd` used). The user may pass its path when invoking; otherwise list candidates under `docs/superpowers/specs/` and ask which document to promote — never guess. The brainstorm document predates the PRD: if the human pivoted at PRD review, divergence between it and PRD.org is expected and healthy, not lineage breakage to repair — PRD.org and DESIGN.org supersede it on contact.

Per org-conventions, only a D-entry carries decision authority: body prose beyond what a D-entry settles is session-authored implementation guidance, not contract, and yields to owner preference without ceremony. This governs how a session defends its own choices — including under skeptic-review pushback in step 4 — with an honest-attribution discipline: canon is defended as canon, with the citation actually checked; a session-authored choice is defended as a choice, on the merits of the specific proposal at hand, not the category it resembles. This is not license to go quiet — un-ruled positions are not thereby indefensible, and pushback that keeps work on track is valued; the discipline governs what the defense is made of, not whether to defend.

1. Resolve the active initiative directory (per org-conventions). If it contains `PRD-draft.org` but no `PRD.org`, STOP — the PRD has not been approved yet; approval is the human's own rename from `PRD-draft.org` to `PRD.org` (see `/workflow-kit:create-prd`). Do not read the draft as if it were the contract. Tell the human to finish approving the PRD first.
2. Read the brainstorm document, PRD.org, and the `## Weight class` section of CLAUDE.md.
3. Write `DESIGN.org` into the active initiative directory (per the org-conventions path resolution) using the repo-local `templates/DESIGN.org` if present, otherwise `${CLAUDE_PLUGIN_ROOT}/templates/DESIGN.org`. Convert the brainstorm document's content into the template's sections. Copy the brainstorm document's design content faithfully — this is format promotion, not a rewrite. The approved PRD.org outranks the brainstorm document: where they conflict, do not copy the conflicting material faithfully — surface the conflict, and where its resolution records a real judgment, mint a design-time Decision Log entry whose rejected alternative is the brainstorm document's superseded position. Faithful copying remains the rule for everything the PRD does not touch. Write the Key Behaviors sections to be excerptable: `#+begin_src` blocks for code, clear prose for constraints, since story excerpts are copied verbatim from here. Preserve both scaffolding headings, `* Decision Log` (which holds no entries — only the pointer to the repo-level shared log `docs/decisions.org`, per org-conventions) and `* Advisories`. If the brainstorm document recorded design decisions, mint design-time entries in the shared log (per org-conventions — heading + CUSTOM_ID, continuing the repo-wide sequence) rather than losing the rationale — entry and body are born together at this stage, with no Advisory.
4. **Skeptic review — work-grade weight class only.** If CLAUDE.md declares work-grade, dispatch the `skeptic-reviewer` subagent on DESIGN.org and PRD.org. Present its findings to the user verbatim and unsoftened. Apply only the changes the user accepts; accepted changes at this stage are body edits — mint design-time D-entries in the shared decision log where they record judgment calls, but no Advisories: the design is not yet canon and has no prior readers to protect. If CLAUDE.md declares personal-mvp, skip this step entirely — the upstream brainstorm review suffices at that weight class.
5. Before presenting DESIGN.org for approval, scrub its body and this promotion's new shared-log entries for brainstorm-spec references: grep for "spec §", "brainstorm", and the spec filename pattern. Report every hit, then rewrite each to self-contained wording per org-conventions' Document chain & version control section (the rule lives there, not here). This is a report-then-fix step — list what was found and how each was reworded, never a silent rewrite.
6. Then produce the alignment trace before presenting DESIGN.org for approval — the demonstration, not the claim:
   (a) a criterion-by-criterion trace: for each PRD Success Criterion (SC-n), cite the DESIGN.org section(s) that satisfy it.
   (b) a disposition line for every brainstorm document position the PRD overrode: faithful copy / rejected-alternative (cite the D-number) / dropped.
   An alignment claim without this trace — e.g. "the PRD was created from the brainstorm document, so no divergence" — does not satisfy this step; absence of the trace is treated as the check not having happened, the same posture story-verifier takes toward unevidenced Acceptance Criteria. This applies at every weight class — at personal-mvp scale the trace is around six lines, so there is no ceremony to exempt. Present the trace together with DESIGN.org for user approval. After approval, suggest `/workflow-kit:user-stories PRD.org DESIGN.org` as the next step.

   Example trace:

   ```
   SC-1 → §Key Behaviors / Chore reset
   SC-2 → §Data Model, §Key Behaviors / Recurrence
   SC-3 → §Screens / Interfaces / Kiosk view

   Brainstorm dispositions:
   - Notification batching: faithful copy (§Key Behaviors)
   - Multi-tenant accounts: dropped (PRD Out of Scope)
   - Sync engine choice: rejected-alternative, D3
   ```

Do not write stories, plans, or code. This skill ends when DESIGN.org is approved.
