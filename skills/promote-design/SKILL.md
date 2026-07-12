---
name: promote-design
description: Promote an approved brainstorm document into DESIGN.org with Decision Log and Advisories scaffolding, running the skeptic design review for work-grade projects. Use after PRD.org exists and before user stories are written — whenever the user asks to create the design doc, promote the design, or run a design review. This is the boundary where the durable org document chain begins.
---

# Promote Design

Read the `org-conventions` skill bundled in this plugin (`${CLAUDE_PLUGIN_ROOT}/skills/org-conventions/SKILL.md`) for the document chain rules.

Input: the approved brainstorm document (same source `/workflow-kit:create-prd` used). The user may pass its path when invoking; otherwise use the newest one under `docs/superpowers/specs/`. The brainstorm document predates the PRD: if the human pivoted at PRD review, divergence between it and PRD.org is expected and healthy, not lineage breakage to repair — PRD.org and DESIGN.org supersede it on contact.

1. Resolve the active initiative directory (per org-conventions). If it contains `PRD-draft.org` but no `PRD.org`, STOP — the PRD has not been approved yet; approval is the human's own rename from `PRD-draft.org` to `PRD.org` (see `/workflow-kit:create-prd`). Do not read the draft as if it were the contract. Tell the human to finish approving the PRD first.
2. Read the brainstorm document, PRD.org, and the `## Weight class` section of CLAUDE.md.
3. Write `DESIGN.org` into the active initiative directory (per the org-conventions path resolution) using the repo-local `templates/DESIGN.org` if present, otherwise `${CLAUDE_PLUGIN_ROOT}/templates/DESIGN.org`. Convert the brainstorm document's content into the template's sections. Copy the brainstorm document's design content faithfully — this is format promotion, not a rewrite. The approved PRD.org outranks the brainstorm document: where they conflict, do not copy the conflicting material faithfully — surface the conflict, and where its resolution records a real judgment, mint a design-time Decision Log entry whose rejected alternative is the brainstorm document's superseded position. Faithful copying remains the rule for everything the PRD does not touch. Write the Key Behaviors sections to be excerptable: `#+begin_src` blocks for code, clear prose for constraints, since story excerpts are copied verbatim from here. Preserve both empty scaffolding headings, `* Decision Log` and `* Advisories`. If the brainstorm document recorded design decisions, seed `* Decision Log` with design-time entries (per org-conventions) rather than losing the rationale — entry and body are born together at this stage, with no Advisory.
4. **Skeptic review — work-grade weight class only.** If CLAUDE.md declares work-grade, dispatch the `skeptic-reviewer` subagent on DESIGN.org and PRD.org. Present its findings to the user verbatim and unsoftened. Apply only the changes the user accepts; accepted changes at this stage are body edits — mint design-time D-entries in `* Decision Log` where they record judgment calls, but no Advisories: the design is not yet canon and has no prior readers to protect. If CLAUDE.md declares personal-mvp, skip this step entirely — the upstream brainstorm review suffices at that weight class.
5. Present DESIGN.org for user approval. After approval, suggest `/workflow-kit:user-stories PRD.org DESIGN.org` as the next step.

Do not write stories, plans, or code. This skill ends when DESIGN.org is approved.
