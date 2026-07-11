---
name: promote-prd
description: Promote an approved brainstorm/spec into the immutable PRD.org contract. Use after a Superpowers brainstorming session produces an approved spec and before any stories are written — whenever the user asks to create the PRD, promote the spec, or lock in success criteria. Also use when starting the document chain for any new project.
---

# Promote PRD

Read the `org-conventions` skill bundled in this plugin (`${CLAUDE_PLUGIN_ROOT}/skills/org-conventions/SKILL.md`) for the document chain rules.

Input: the approved brainstorm spec. The user may pass its path when invoking; otherwise look for the newest spec under `docs/superpowers/specs/` or ask which document to promote.

1. Read the spec and extract exactly three things — nothing more:
   - **The problem**: what hurts, for whom, why off-the-shelf doesn't fit.
   - **Success Criteria**: the observable outcomes that define success. Keep these outcome-shaped ("a kid can see today's chores in one tap"), not mechanism-shaped ("the LiveView renders a chore list component"). Mechanisms belong in DESIGN.org.
   - **Out of Scope**: explicit non-goals for this version.
2. Create the initiative directory `docs/YYYY-MM-DD-<initiative-slug>/` (date = today, via `date '+%Y-%m-%d'`; slug from the initiative name), then set or update the `Active initiative:` line in the repo's CLAUDE.md to point at it. Write `PRD.org` inside it using the repo-local `templates/PRD.org` if present, otherwise `${CLAUDE_PLUGIN_ROOT}/templates/PRD.org`, filling those three sections and leaving the Amendments section with its protocol comment and "(no amendments)". Do NOT carry over personas, market context, competitive framing, or stakeholder matrices from the spec — for this document chain, those are ceremony.
3. For a personal-mvp weight class (check CLAUDE.md), the whole PRD should be around ten lines of content. For work-grade, be as complete as the spec supports, but every Success Criterion must still be an observable outcome.
4. Present the PRD to the user for approval. Ask explicitly: "Approve this as the invariant contract? After approval it is locked — agents cannot edit it, and changes require the human Amendment protocol."
5. After approval, remind the user that the `prd-lock` hook now enforces immutability, and suggest `/workflow-kit:promote-design` as the next step.

Never edit PRD.org after it has been approved, in this session or any other. If asked to change it, explain the Amendment protocol in the file's header instead.
