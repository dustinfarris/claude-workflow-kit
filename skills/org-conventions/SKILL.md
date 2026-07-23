---
name: org-conventions
description: The single source of truth for org-mode formatting in the document chain — LOGBOOK drawers, timestamps, checkbox semantics, Decision Log entries, Advisories, batches and gates, and per-document mutability. ALWAYS read this before writing any LOGBOOK entry, Decision Log entry, Advisory, or checkbox state in PRD.org, DESIGN.org, PLAN.org, or stories/ files, and before creating any of those files.
---

# Org Conventions

This skill is the single source of truth for org-mode formatting used across the document chain (PRD.org, DESIGN.org, PLAN.org, stories/). Any skill writing a LOGBOOK entry, Decision Log entry, Advisory, or checkbox state MUST follow these conventions exactly. Do not improvise variants. Formatting conventions change here and nowhere else.

## Document chain format rule

All durable planning artifacts are org format, never markdown: PRD.org, DESIGN.org, PLAN.org, and every file under stories/. Ephemeral scratch output (brainstorm specs, subagent reports) may be any format. Do not hard-wrap lines in org documents; let lines flow naturally.

## Document chain location

The document chain for an initiative lives in a date-stamped initiative directory: `docs/YYYY-MM-DD-<initiative-slug>/` containing PRD.org, DESIGN.org, PLAN.org, and `stories/`. One initiative = one chain; phases of the same initiative share the directory (a new dated directory means a new PRD, not a new phase).

Path resolution, in order: (1) the `Active initiative:` line in the repo's CLAUDE.md, (2) the newest `docs/*/` dated initiative directory, (3) the repo root (legacy layout). Filenames inside the directory stay canonical uppercase (PRD.org, DESIGN.org, PLAN.org) — the prd-lock hook matches `*PRD.org` at any depth, and lowercase names escape the lock.

## Lessons file

Lessons live at the repo level, never inside an initiative directory: `docs/learnings.org` is a single cumulative file across initiatives (project-setup seeds it). One dated entry per learning, newest first; update rather than duplicate; delete entries that prove wrong. Wherever this skill or another names a "lesson candidate," this file is the destination.

## Document chain & version control

- Chain documents are committed in doc-only commits, never mixed with code changes. Code commits carry code; doc commits carry chain documents.
- Chain documents enter version control at their canonical moments only: the PRD at lock (the human rename is the approval act; the lock commit follows it), the DESIGN at canon approval, and thereafter each update-design pass (D-entry + body edit + Advisory) as its own doc commit. Working drafts and intermediates are never committed.
- The brainstorm spec is never committed. It is scratch material supporting PRD and DESIGN drafting; the DESIGN supersedes it. `docs/superpowers/specs/` is permanently gitignored. Nothing that survives to a document's first commit may reference the brainstorm spec by section number — rejected alternatives drawn from the brainstorm are restated in words so the entry is self-contained.

## Batches and gates

PLAN.org organizes stories under batch headings. A batch is the unit of work that ends at a gate; "Phase N" is an optional label on a batch heading — decoration, never load-bearing.

Orientation is structural, not nominal: the gate record (a LOGBOOK entry on the batch heading, written by phase-close) doubles as the closed-marker. The open batch is the batch heading without a gate record. At most one batch is open at a time. A legacy PLAN with no batch headings is one open batch.

The PRD may declare gate criteria (what must be verified at gates, e.g. on-device checks); the PLAN must carry the batch structure. A single-batch initiative satisfies this trivially and never thinks about phases.

Gate record format: a standard single-note LOGBOOK drawer on the batch heading — timestamp, checks run, verdict, advisories withdrawn/promoted counts.

## Story file naming

Stories live in a `stories/` subdirectory adjacent to the PRD, saved with a numbered filename for easy reference: `story-01-<slug>.org`, `story-02-<slug>.org`, ...

## Checkbox state semantics

- `[X]` — done, with evidence recorded in a LOGBOOK entry
- `[ ]` — not done, with what is missing recorded in a LOGBOOK entry
- `[-]` — deferred, with the reason recorded in a LOGBOOK entry

## Capturing timestamps

Timestamps reflect the ACTUAL time of the entry, never an invented or reused time. Run the `date` shell command immediately before writing each entry: every bracketed timestamp in chain documents (LOGBOOK notes, gate records, Advisory headings) is an org-native inactive timestamp, captured via `date '+%Y-%m-%d %a %H:%M'` and wrapped in brackets: `[2026-07-11 Sat 14:22]`.

D-entry dates like `(2026-07-10)` are inline notation, not org timestamps — this rule does not apply to them. Gate records are LOGBOOK notes and use the LOGBOOK entry format.

Run `date` per item, not once per session — entries written at different times carry different timestamps.

## Inline markup

Inline markup: ~code~ for anything a language would parse — identifiers, module/function names (~BearCub.Chores~, ~list_extras/2~), expressions, shell commands (~mix precommit~), file paths. =verbatim= only for literal non-code strings quoted exactly — stored values (=morning=), config keys, log output. When unsure, prefer ~code~.

## Line-initial asterisks

No line in body or LOGBOOK text may begin with an asterisk unless it is intentionally an org heading. Quoted code or error output that happens to start a line with `*` (e.g. Elixir error text) parses as an org level-2 heading and silently corrupts document structure — and LOGBOOK evidence quotes error text constantly. When quoting such text: reflow so the `*` lands mid-sentence, or wrap it in a `#+begin_src`/`#+begin_example` block. Self-check: run `grep '^\*\*'` on the file before finishing any org write.

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

## Decision Log

A decision entry is the permanent record of a judgment call: a fork where a competent person could have gone the other way, which way was chosen, and why — including the rejected alternative when one was seriously considered. Creation threshold: would a plausible future reader choose otherwise if the reasoning weren't recorded? If yes, record it. Renaming a variable is not a decision entry; choosing emoji icons over an asset pipeline is.

Its referent is the system being built, never the document describing it.

Format:

```org
- *Dn (YYYY-MM-DD) — terse title:* what was decided; compressed rationale; rejected alternative if one was live; what it settles (FR-x, PRD deferrals); → § pointers to where the body reflects it.
```

- → § pointers target PRD or DESIGN sections only. Pre-chain working documents (the brainstorm spec) are never pointer targets: a rejected alternative that originated in the brainstorm is restated in words within the entry, never cited by spec section.

One monotonic sequence per initiative. The growing end is `* Decision Log` in DESIGN.org. In adopted repos where earlier entries live elsewhere (e.g. a PRD decision-log section), the next number is the highest existing number anywhere in the chain, plus one.

Created at three moments:

- design-time (through canon approval) — minted freely, entry and body born together, no pairing machinery;
- implementation-time (post-canon, via update-design) — the full three-step applies: mint the D-entry, make the body edit, issue the Advisory citing the D-number;
- amendment-time — the design consequences a PRD Amendment forces get D-entries like any other pivot.

Append-only, forever. A decision entry cannot become wrong; it records that a judgment happened. A reversed decision gets a new entry citing the old (`Dn — supersedes Dm: ...`); the old entry stays.

Referenced by: document bodies inline as `(Dx)`; Advisories (the why behind a notice); CLAUDE.md invariants (curated distillations); fresh sessions and design reviews (rejected alternatives fence off relitigation); Amendment analysis (the → § trail shows what an amendment invalidates); initiative-close extraction (survived decisions become confirmed-approach lessons).

Only what a D-entry records carries decision authority. Body prose that goes beyond what a D-entry settles is session-authored implementation guidance, not contract — it yields to owner preference without ceremony.

## Advisories

Purpose: active notices to future sessions reading this document cold — positions the document previously took that no longer hold. The primary consumer is the next agent session; git holds the permanent history, but a stateless reader will not run `git log`, so the working set of protective deltas lives in the document.

Payload rule: Each advisory's payload is the SUPERSEDED position, stated explicitly — what this document used to say, and why it still looks attractive. The current position is already in the body; do not restate it as the entry's substance. Test before writing: could a reader reconstruct the old position from this entry alone? "§5 tap target adjusted" fails. "§5 tap target raised from 72 px to 88 px" passes. An entry that fails this test is a commit message, not an advisory, and protects no one.

Issuance rule: an Advisory is issued only where a superseded position could trap a future reader — never as a mutation record. The test is the payload litmus itself: if there is no superseded position worth stating, there is no advisory. Additive or neutral body edits get no entry; git and the gate's reconciliation pass own mutation completeness. An advisory's "Sections affected" line may name a section only if that section's superseded position is stated in the payload — naming an affected section without stating what it used to say is the litmus failure in disguise.

Format: `** [YYYY-MM-DD Day HH:MM] <heading naming what no longer holds>`, then an italic `/Sections affected: .../` line, then prose. Timestamp via `date '+%Y-%m-%d %a %H:%M'`, wrapped in brackets. Appended under `* Advisories`, newest last.

```org
** [2026-07-10 Fri 16:40] §11 no longer permits async DB tests (D24)

/Sections affected: §11 Testing strategy/

Earlier versions of this document specified ~async: true~ on the ConnCase LiveView tests. Do not reintroduce it, even though it looks like an easy win: ~ecto_sqlite3~'s SQL.Sandbox collides under concurrent per-test write transactions ("Database busy"), and ~busy_timeout~/WAL are not the fix — they're already adapter defaults. Rationale: D24.

** [2026-07-13 Mon 09:12] §5 chore-row tap target raised from 72 px to 88 px

/Sections affected: §5 Kiosk layout/

This document previously specified ~72 px minimum tap height; on-device QA showed misses. If you're reading old excerpts, story fixtures, or CSS referencing 72, they're stale — 88 px is the floor. No D-entry: this is a corrected value, not a decision.
```

**An Advisory without a corresponding DESIGN body edit is never correct.** If an implementation decision clarifies something the design already says correctly, it belongs in the Plan LOGBOOK, not here. Decision-driven advisories cite their D-number; repair-class advisories (corrected errors, not judgments) mint no D-entry. Reciprocally: **a post-canon D-entry claiming a → § effect without a paired Advisory is equally suspect** — drift is detectable from both directions.

Lifecycle: issued post-canon only (pre-canon edits have no prior readers to protect). Withdrawn — deleted, not annotated — at a gate, once no reader could plausibly reintroduce the superseded position. Withdrawal is also promotion review: a withdrawn advisory that generalizes beyond this project is a lesson candidate, reported at the gate. Git remains the permanent archive.

## Mutability policy per document

- **PRD.org** — invariant contract. Human-only edits via the Amendment protocol (see the template). Agents NEVER edit this file; a PreToolUse hook enforces the lock. If work appears to conflict with PRD Success Criteria, stop and surface for a human decision.
- **DESIGN.org** — adaptive mechanism. Body edits allowed when new information surfaces, always paired per the Decision Log / Advisories rules above.
- **PLAN.org and stories/** — execution state. Updated freely per the skills that own them, with LOGBOOK evidence.
