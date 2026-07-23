# claude-workflow-kit — Claude Guidelines

## Weight class

tooling. This repo IS the workflow: skills, agents, hooks, and templates consumed by my project repos. There is no PRD/DESIGN chain here — the design rationale lives in docs/workflow-alignment-plan.org, and this file protects its invariants during iteration. The failure mode in this repo is not bugs; it is well-intentioned edits that sand off load-bearing constraints.

## Invariants — never weaken these while editing

- **Verbatim crown jewels.** The following blocks survived real projects and are preserved word-for-word unless I explicitly say otherwise: the DESIGN EXCERPT SCOPE rules and AC drift guard in skills/user-stories, the LOGBOOK format and the Decision Log and Advisories specs in skills/org-conventions/SKILL.md (including the payload litmus and the paired invariants), the Advisory-requires-body-edit paired invariants and five-step flow in skills/update-design, and every STOP boundary. Rewording for "clarity" is how these die.
- **Single source of truth.** LOGBOOK, timestamp, checkbox, Decision Log, and Advisory conventions change in skills/org-conventions/SKILL.md and nowhere else. If a skill needs a format tweak, the conventions file changes and the skills keep pointing at it.
- **Conversation-born terms don't ship.** A coined term may appear in spec text only after the spec states the rule it compresses, as a parenthetical mnemonic — a term may summarize an explanation, never replace one. This applies to verbatim blocks supplied in prompts as much as to session-drafted text — provided wording gets the same term audit before it ships.
- **Skills stop.** Every skill ends with an explicit stopping condition and stays inside its file scope. A skill that starts doing the next stage's job is a regression, not an improvement.
- **PRD lock is sacred.** prd-lock.sh may gain block patterns, never lose them. Its block message must keep teaching the Amendment protocol, not just refuse.
- **Weight class stays the amplitude knob.** Any new ceremony added to a skill must either apply to all weight classes or be gated on the CLAUDE.md weight-class declaration. No ceremony that personal-mvp cannot opt out of.
- **Reviews check different things.** skeptic-reviewer critiques the design against reality (bites, one-way doors, cuts); it never becomes an editorial/completeness reviewer — Superpowers already owns that. Keep the no-additions rule and the "say Nothing" rule.

## Testing

Hook changes require `test/hooks_test.sh` green before commit — both the existing cases and a new case for any new block/allow pattern. Skill changes get at least a dry read-through in a consuming repo before a version bump; friction found there gets fixed here directly, with the rationale captured in the CHANGELOG entry.

## Iteration loop

kit edit (from real project use) → CHANGELOG.org entry → version bump. Edits without an explicit rationale in the CHANGELOG are suspect — this kit should shrink over time, not grow. If a stage or rule has not been consulted to make a decision across two or three projects, propose cutting it rather than polishing it.

## Conventions for this repo

Org format for docs (README.org, CHANGELOG.org, docs/); markdown for SKILL.md, agents, and references (Claude Code's native format). Do not hard-wrap lines. Skill descriptions stay "pushy" per skill-writing best practice — trigger conditions live in the description, not the body.
