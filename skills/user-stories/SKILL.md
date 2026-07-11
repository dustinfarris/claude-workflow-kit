---
name: user-stories
description: Break an approved design into implementation-ready user stories with embedded design excerpts, then emit PLAN.org. Use whenever the user asks to create stories, break down a design, generate a story set, or plan implementation from PRD.org and DESIGN.org — and use this INSTEAD of any generic plan-writing skill when the repo has a PRD.org/DESIGN.org document chain.
---

# User Stories from PRD + Design

Read the `org-conventions` skill bundled in this plugin (`${CLAUDE_PLUGIN_ROOT}/skills/org-conventions/SKILL.md`) before writing any files.

The user may pass paths when invoking (e.g. `/workflow-kit:user-stories PRD.org DESIGN.org`); otherwise resolve the active initiative directory per org-conventions (CLAUDE.md `Active initiative:` line, else newest `docs/*/` dated directory, else repo root) and use its `PRD.org` and `DESIGN.org`. Read both fully before writing anything. Also read the `## Weight class` section of CLAUDE.md — it selects the Definition of Done variant below.

Create user stories to implement the design in a `stories/` sub-directory adjacent to the PRD. The stories are written in org format and saved with numbered filenames for easy reference (e.g. `story-01-<slug>.org`).

User stories should be small and focused — each completable in one focused session ending in a demoable, test-passing state. Stories may bundle adjacent edits when they share an insertion point or are reviewed together (co-located AGENTS.md edits, for example). Order the set so the app is runnable (even if ugly) as early as possible. Target 6–10 stories for an MVP-class project; if you're producing many more, the stories are too small or the design is too big.

The Acceptance Criteria should be clear, verifiable, and center around the user experience, without delving into system internals or implementation details.

## AC drift guard

Acceptance Criteria must be consistent with both the embedded Design excerpt (see below) and the PRD's Success Criteria section in PRD.org. The intent of an AC should trace back to something the PRD's Success Criteria establish, even if the AC's wording is more specific than the PRD's. If you find yourself wanting to write an AC that goes beyond either the embedded Design excerpt or the PRD's intent — asking for more examples, more file scope, or behavior the spec does not cover — stop. Either narrow the AC to match what the spec says, or surface the gap as a comment for the human to resolve before the story is finalized. Acceptance criteria that drift past the embedded spec create the same problem the embedding was meant to prevent.

Tracing runs both directions. Outward: no AC may exceed the excerpt or the PRD's intent. Inward: every requirement the embedded excerpt explicitly enumerates for this story's scope must be either covered by an AC or surfaced as uncovered — quoting a requirement in the excerpt and then omitting it from the ACs is the same drift in reverse.

Where the design is silent on a detail an AC would need to state (a location, a threshold, a behavior), do not resolve the silence — write the AC at the design's level of specificity, or surface the gap as a "# GAP:" comment in the story for human adjudication. "# GAP:" is the greppable convention for surfaced gaps.

Example Acceptance Criteria for documentation work:

```org
* Acceptance Criteria

** [ ] The integration document INTEGRATION.md lists the five subsections as a nested numbered list.
```

Example Acceptance Criteria for code work:

```org
* Acceptance Criteria

** [ ] The Build Plan Verifier's prior-art check rules list contains the four new category-choice rule identifiers.
** [ ] The artifact validation requires the `category_choice_rationale` field on every artifact.
```

## Story structure

Each user story includes, at a minimum:

1. A "Design" section containing a link to DESIGN.org and the verbatim relevant content from it for that story's scope (see DESIGN EXCERPT SCOPE below).
2. The User Story in standard "As a / I need / so that" form.
3. Acceptance Criteria as checkbox TODOs.
4. The Definition of Done for the declared weight class, copied verbatim from the matching block below.
5. A "Technical Notes" section for implementation details relevant to the story but not part of the acceptance criteria. The Technical Notes reference the Design excerpt as the source of truth for the spec, with DESIGN.org as broader context only. Dependencies on previous stories are noted here ("This story depends on Story N because ...").

## Definition of Done — work-grade weight class (verbatim)

```org
* Definition of Done

** [ ] All acceptance criteria have been either met or have had a documented removal or deferral
** [ ] Unit tests written and passing for all context functions
** [ ] Integration tests written and passing for all user flows in this story
** [ ] moduledocs have been reviewed and updated if appropriate
** [ ] Code follows style guidelines in CLAUDE.md
** [ ] ~mix check~ passes without errors
```

## Definition of Done — personal-mvp weight class (verbatim)

```org
* Definition of Done

** [ ] All acceptance criteria have been either met or have had a documented removal or deferral
** [ ] Tests written and passing for the acceptance criteria in this story
** [ ] Code follows style guidelines in CLAUDE.md
** [ ] ~mix format --check-formatted~ and ~mix test~ pass without errors
```

## DESIGN EXCERPT SCOPE

The Design excerpt section contains the verbatim relevant content from DESIGN.org for that story's scope:

- For documentation-only stories (AGENTS.md / INTEGRATION.md / README.md prose edits): copy the entire `#+begin_src markdown ... #+end_src` block(s) from DESIGN.org. Include surrounding sentences that name the insertion point in the target file ("after the existing first paragraph of Step 7", "at the start of the X subsection"). Do not paraphrase — copy the design's prose exactly.

- For code stories (verifier internals, mix tasks, test files): copy the relevant `#+begin_src elixir` / `#+begin_src json` blocks plus the surrounding prose that explains behavior, integration points, and constraints. Include "What stays the same" or equivalent constraint paragraphs where they apply.

- For test stories (shape tests, coverage tests, seeded fixtures): copy the assertion shape, helper definitions, fixture file contents, and the verification criteria.

Scope each excerpt tightly to what the story implements. If a story covers two adjacent design subsections, include both. Do not include unrelated parts of the same workstream. Do not modify the design's prose during extraction; if something looks wrong, flag it but copy the existing version.

## Emit the plan

After the story set is written, review the stories and observe any dependencies they may have on each other. PLAN.org lives alongside the PRD in the initiative directory; each story is listed in the order you determine as an org TODO linking to its story file, under a batch heading, and the plan links to DESIGN.org.

If PLAN.org is absent, create it from the repo-local `templates/PLAN.org` if present, otherwise `${CLAUDE_PLUGIN_ROOT}/templates/PLAN.org`, and place this run's stories as the first batch — label the batch from the given phase scope if any was passed, else "Batch 1".

If PLAN.org already exists, first verify no batch is open — an open batch is a batch heading without a gate record (see org-conventions). If a batch is open, STOP and surface it: generating a new batch over an open one breaks gate orientation, and the open batch must be closed at a gate first. Otherwise append this run's stories as a new batch heading after the existing batches. Never modify prior batches or their gate records.

STOP. You are done when the stories and PLAN.org exist. Do not begin implementing.
