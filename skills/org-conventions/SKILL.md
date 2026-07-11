---
name: org-conventions
description: The single source of truth for org-mode formatting in the document chain — LOGBOOK drawers, timestamps, checkbox semantics, Changelog entries, and per-document mutability. ALWAYS read this before writing any LOGBOOK entry, Changelog entry, or checkbox state in PRD.org, DESIGN.org, PLAN.org, or stories/ files, and before creating any of those files.
---

# Org Conventions

This skill is the single source of truth for org-mode formatting used across the document chain (PRD.org, DESIGN.org, PLAN.org, stories/). Any skill writing a LOGBOOK entry, Changelog entry, or checkbox state MUST follow these conventions exactly. Do not improvise variants. Formatting conventions change here and nowhere else.

## Document chain format rule

All durable planning artifacts are org format, never markdown: PRD.org, DESIGN.org, PLAN.org, and every file under stories/. Ephemeral scratch output (brainstorm specs, subagent reports) may be any format. Do not hard-wrap lines in org documents; let lines flow naturally.

## Story file naming

Stories live in a `stories/` subdirectory adjacent to the PRD, saved with a numbered filename for easy reference: `story-01-<slug>.org`, `story-02-<slug>.org`, ...

## Checkbox state semantics

- `[X]` — done, with evidence recorded in a LOGBOOK entry
- `[ ]` — not done, with what is missing recorded in a LOGBOOK entry
- `[-]` — deferred, with the reason recorded in a LOGBOOK entry

## Capturing timestamps

Timestamps reflect the ACTUAL time of the entry, never an invented or reused time. Run the `date` shell command immediately before writing each entry:

- For LOGBOOK inactive timestamps: `date '+%Y-%m-%d %a %H:%M'` — wrap the result in square brackets to form `[YYYY-MM-DD Day HH:MM]`
- For Changelog timestamps: `date '+%Y-%m-%d %H:%M %Z'` — wrap the result in square brackets

Run `date` per item, not once per session — entries written at different times carry different timestamps.

## LOGBOOK entry format

LOGBOOK entries follow org-mode's native LOGBOOK drawer convention. Each item gets a single drawer with a single timestamped note. The entry describes _how_ the item was verified (for `[X]`), _what is missing_ (for `[ ]`), or _why it was deferred_ (for `[-]`).

For met items:

```org
** [X] <criterion text>
:LOGBOOK:
- Note taken on [2026-05-06 Wed 14:32] \\
  <verification description, naming concrete evidence: test name, command run, file path and line, etc.>
:END:
```

For deferred items:

```org
** [-] <criterion text>
:LOGBOOK:
- Note taken on [2026-05-06 Wed 14:32] \\
  Deferred — <reason; e.g., "not applicable to documentation-only stories" or "no context functions in this story">
:END:
```

For not-met items:

```org
** [ ] <criterion text>
:LOGBOOK:
- Note taken on [2026-05-06 Wed 14:32] \\
  Not met — <description of what's missing or why it could not be verified>
:END:
```

The LOGBOOK contains a single entry per item. Multi-line detail goes inside that single entry's body, separated by line breaks (use `\\` at end of a line for org-mode's hard line break, or write as a single paragraph). Do not create multiple LOGBOOK entries per item.

Plan-level LOGBOOK entries (status updates, implementation observations, decisions, deferrals) use the same single-drawer, single-note format:

```org
:LOGBOOK:
- Note taken on [2026-05-06 Wed 14:32] \\
  <description of status update, decision, observation, or deferral>
:END:
```

## DESIGN Changelog entry format

```org
** [YYYY-MM-DD HH:MM TZ] <terse heading naming the change>

/Sections affected: <Workstream N — <Workstream name>, "<subsection>"; ...>/

<prose describing the correction; use a numbered list if multiple corrections, prose if single>
```

The "Sections affected" line uses italic markup (forward slashes) per org convention. Entries are appended under the `* Changelog` heading, newest last.

**Invariant: a Changelog entry without a corresponding DESIGN body edit is never correct.** If an implementation decision clarifies something the design already says correctly, it belongs in the Plan LOGBOOK, not the Changelog.

## Mutability policy per document

- **PRD.org** — invariant contract. Human-only edits via the Amendment protocol (see the template). Agents NEVER edit this file; a PreToolUse hook enforces the lock. If work appears to conflict with PRD Success Criteria, stop and surface for a human decision.
- **DESIGN.org** — adaptive mechanism. Body edits allowed when new information surfaces, always paired with a Changelog entry.
- **PLAN.org and stories/** — execution state. Updated freely per the skills that own them, with LOGBOOK evidence.
