# Docs reorganization proposal (Item 6) — propose only, do not execute

## Inventory (measured 2026-08-11)

`docs/` holds **100 files, all Markdown**: 36 at top level, 53 under
`docs/map/`, 11 under `docs/proposals/`. Roughly 22,000 lines / 220,000
words combined. Coexisting naming conventions, no single scheme:

- `SCREAMING_SNAKE_CASE.md` — most top-level docs and all of
  `docs/proposals/`.
- `kebab-versioned` — the harness spec series only
  (`harness-spec-v1.3.md`, `-v1.4-amendment.md`, etc.), a genuine
  append-only amendment chain (each explicitly "amends... does not
  replace or modify" the prior file — not drift, working as designed).
- Dated snapshots — four `HANDOVER_YYYY-MM-DD.md` files, one-off
  session handoffs, not living references.
- `PREFIX-slug.md` — `docs/map/` only (`SUB-`, `CON-`, `SEAM-`, `INV-`,
  `REC-`), its own documented ID grammar (`docs/map/SCHEMA.md`).
- `*_PREPLAN`/`*_PLAN` — `docs/proposals/`, marking proposed-not-yet-
  accepted design status.

**Superseded content found:** exactly one document-level
self-declared supersession —
`docs/proposals/RECORD_LIFECYCLE_DEFECT_PLAN.md` ("Status: PARTIALLY
SUPERSEDED... by the operator's own reframe — see
CODER_AS_TOOL_PREPLAN.md"). No `*OLD*`/`*DEPRECATED*`/`*_v[0-9]*`
files exist — version identity lives only in the harness-spec
filenames. Likely low-reuse, archived-report content sitting at top
level rather than under `experiments/`: the four `HANDOVER_*.md` files
and five single-experiment technical reports (`BASIN_REPORT.md`,
`CAN_LLMS_EXPLORE.md`, `PATROL_DETERMINISM_REPORT.md`,
`MINI_STRESS_REPORT.md`, `AUTONOMICS_REPORT.md`).

**Load-bearing paths — must never move:**
1. `docs/map/*.md` — 53 files, 854 inline `check:` commands executed by
   `tools/docs_verify.py`.
2. `docs/ERRATA.md` / `docs/ERRATA_EXECUTOR.md` — named directly in
   CLAUDE.md's session-start instruction.
3. `docs/harness-spec-v1.3.md` — cited in production code and tests
   (`verification/report.py:1033`, `cli/main.py:1097`,
   `tests/test_adjudication_blindness.py:8`,
   `scripts/e31_benchmark/sealed.py:88`).
4. Numerous other top-level docs cited as rationale comments in
   `src/`/`tests/` (`TOKEN_ECONOMY.md`, `BASIN_REPORT.md`,
   `CONTROLLER_SPEC.md`, `AMENDMENT_EPOCHS.md`,
   `ROLE_SEAT_SEPARATION_PLAN.md`) — prose citations, not
   machine-checked, but a rename strands the comment.
5. `README.md` names `docs/map/INDEX.md` and
   `docs/map/INV-frozen-surfaces.md` as required reading.

## Standards researched

- **Diátaxis** (diataxis.fr) — four documentation modes: tutorials
  (learning by doing), how-to guides (task-oriented), reference
  (information lookup), explanation (understanding why). Organizes by
  READER NEED rather than by subject.
- **Architecture Decision Records (ADR)** (adr.github.io, Nygard 2011)
  — short, numbered, immutable files, one per significant decision:
  context, decision, consequences.
- **Docs-as-code** (writethedocs.org) — a PROCESS standard (docs live
  in the repo, same review/CI pipeline as code), orthogonal to the
  content taxonomies above.

## Fit assessment

`docs/map/` is already a docs-as-code reference layer, stronger than
typical (its checks EXECUTE against the live codebase, not just lint).
It is Diátaxis **Reference** by its own self-description
(`SCHEMA.md`: "This is a map, not a spec... When the two disagree, the
code is what the map must describe").

The harness-spec + amendment series is Reference-as-contract, but its
append-only layering behavior is structurally closer to an **ADR
chain** than a single reference document — each amendment is a
large-grained decision record with consequences, just not filed
one-decision-per-file. `docs/proposals/*_PREPLAN.md`/`*_PLAN.md` are
pre-ADR: proposed decisions awaiting acceptance, with an ad hoc
free-text "Status:" header doing the job ADR's discrete, immutable
format would do more cleanly.

Per-experiment `RESULTS.md` and the standalone top-level technical
reports are Diátaxis **Explanation** ("why," discursive) — their
placement at `docs/` top level rather than under
`experiments/<name>/RESULTS.md` is a location mismatch already implicit
in CLAUDE.md's own directory map, which lists `experiments/` as where
"RESULTS.md = narrative" belongs.

`docs/ERRATA.md`/`ERRATA_EXECUTOR.md` fit **none of the three
standards cleanly** — not reference, not explanation, not ADR (an ADR
amends a decision going forward; ERRATA retroactively flags a document
as wrong without editing it), not how-to. This is a real, named gap:
the reorg should NOT force-fit these into a taxonomy that doesn't model
them; they stay their own genre.

**How-to guides are the thinnest category** in the whole tree —
CLAUDE.md and `.claude/skills/` (outside `docs/`) currently carry that
load. No file under `docs/` is task-oriented in the Diátaxis sense.

## Proposed reorganization (index-first, move-nothing-load-bearing)

1. **Add `docs/INDEX.md`** (new, top-level, distinct from
   `docs/map/INDEX.md`) as a single navigation entry point, organized
   by Diátaxis-inspired sections: Reference (→ `docs/map/`, the spec
   series), Explanation (→ per-experiment RESULTS.md, pointing OUT of
   `docs/` to `experiments/*/RESULTS.md` rather than duplicating it),
   Decisions (→ `docs/proposals/`, reframed as a pre-ADR queue),
   Corrections (→ `docs/ERRATA.md`/`ERRATA_EXECUTOR.md`, named as its
   own genre, not force-fit).
2. **Do NOT move** any of: `docs/map/*`, `docs/harness-spec-*.md`,
   `docs/ERRATA.md`, `docs/ERRATA_EXECUTOR.md`, or anything cited by a
   `check:` line or a `src/`/`tests/` comment (see Load-bearing list
   above) — moving any of these breaks an automated check or strands a
   prose citation, for zero organizational benefit an index page
   doesn't already provide.
3. **Consider relocating** (lower priority, real but bounded cost) the
   five standalone top-level technical reports
   (`BASIN_REPORT.md`, etc.) toward `experiments/<their-origin-date>/`
   alongside the tranche that produced them, IF each can be traced to
   one experiment directory without ambiguity — otherwise leave in
   place and only add the index pointer.
4. **Consider a light rename pass** on `docs/proposals/*_PREPLAN.md`
   toward an ADR-numbered scheme (`docs/proposals/ADR-0001-<slug>.md`)
   ONLY as a NEW-file-forward convention (new proposals only) — do not
   rename existing files (breaks their own internal cross-references
   and any prose citation elsewhere).

## Migration cost

Step 1 (index): ~1 new file, 0 renames, 0 risk to load-bearing paths —
cheap, immediate value. Steps 3-4: bounded but nonzero — each rename
needs its own grep-and-fix pass for prose citations (not machine-
checked, so a missed one silently strands a reference); recommend
doing steps 3-4 only if the operator wants them, as their own small
follow-on tranche, not bundled with step 1.

## What must never move (repeated for the decision sheet)

`docs/map/*.md` (854 checks), `docs/ERRATA.md`, `docs/ERRATA_EXECUTOR.md`,
`docs/harness-spec-v1.3.md` (code/test-cited). These four are the hard
constraint on any reorg, regardless of which standard or index shape
the operator chooses.
