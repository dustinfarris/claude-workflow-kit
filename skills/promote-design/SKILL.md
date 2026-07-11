---
name: promote-design
description: Promote an approved brainstorm/spec into DESIGN.org with Changelog scaffolding, running the skeptic design review for work-grade projects. Use after PRD.org exists and before user stories are written — whenever the user asks to create the design doc, promote the design, or run a design review. This is the boundary where the durable org document chain begins.
---

# Promote Design

Read the `org-conventions` skill bundled in this plugin (`${CLAUDE_PLUGIN_ROOT}/skills/org-conventions/SKILL.md`) for the document chain rules.

Input: the approved brainstorm spec (same source `/promote-prd` used). The user may pass its path when invoking; otherwise use the newest spec under `docs/superpowers/specs/`.

1. Read the spec, PRD.org, and the `## Weight class` section of CLAUDE.md.
2. Write `DESIGN.org` at the repo root using the repo-local `templates/DESIGN.org` if present, otherwise `${CLAUDE_PLUGIN_ROOT}/templates/DESIGN.org`. Convert the spec's content into the template's sections. Copy the spec's design content faithfully — this is format promotion, not a rewrite. Write the Key Behaviors sections to be excerptable: `#+begin_src` blocks for code, clear prose for constraints, since story excerpts are copied verbatim from here. Preserve the empty `* Changelog` heading; initial promotion needs no Changelog entry.
3. **Skeptic review — work-grade weight class only.** If CLAUDE.md declares work-grade, dispatch the `skeptic-reviewer` subagent on DESIGN.org and PRD.org. Present its findings to the user verbatim and unsoftened. Apply only the changes the user accepts; accepted changes at this stage are body edits without Changelog entries (the design is not yet canon). If CLAUDE.md declares personal-mvp, skip this step entirely — the upstream brainstorm review suffices at that weight class.
4. Present DESIGN.org for user approval. After approval, suggest `/workflow-kit:user-stories PRD.org DESIGN.org` as the next step.

Do not write stories, plans, or code. This skill ends when DESIGN.org is approved.
