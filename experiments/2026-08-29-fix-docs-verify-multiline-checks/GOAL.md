# GOAL — docs_verify runs every check the map carries

Tranche: `experiments/2026-08-29-fix-docs-verify-multiline-checks/`
Route: DEFECT (`deepreason-orchestrator`)
Branch: `claude/docs-verify-multiline-checks-n9m4si`
Base: main `ae490e26b`

## Map preflight (ids resolved before design)

| id | document | why it is in scope |
|---|---|---|
| `DR-SCHEMA` | `docs/map/SCHEMA.md` | owns the check grammar; §Checks states the column-0 rule the parser implements |
| `DR-INV-frozen-surfaces` | `docs/map/INV-frozen-surfaces.md` | read before design; **no contact** — the five frozen surfaces are `capabilities/state.py`, `harness.py`, `invariants.py` + `verification/`, `run_manifest.py`, `qualification.py`, plus frozen-adjacent `route_fingerprint`. This tranche touches none of them and no `src/` file at all. |
| `DR-INDEX` | `docs/map/INDEX.md` | `Verify:` header runs `docs_verify --links`; no seam document covers `tools/`, so there is no seam to read before the subsystems |

No `SEAM-` document exists for the pair (tooling × map), because
`tools/` has no `SUB-` document. That is the documented meaning of an
absent seam only for SUB/CON pairs; here it means the instrument is
governed by `SCHEMA.md` alone.

## The defect, cited not re-derived

Operator, 2026-08-29, verbatim:

> Found something important: docs_verify only parses single-line
> check: blocks — multi-line ones are silently never run. what now?

Monitor verification, cited: the parser is `tools/docs_verify.py:47`
(`_CHECK`), which requires the opening and closing backtick on ONE
line; the census counts 72 column-0 `check:` openers with no same-line
closing backtick across 27 `docs/map/` documents.

## Success criterion (falsifiable)

1. **R1** — a column-0 `` `check: `` opener the grammar cannot parse
   makes `python tools/docs_verify.py` print an ERROR and exit 1. It is
   never skipped and never silent. Proven by a mutation: an unclosed
   opener planted in a scratch map document turns the run RED.
2. **R2** — the 72 committed multi-line checks are parsed AS WRITTEN
   and executed. Proven by the parsed-check count rising from 1141 to
   1141 + (the multi-line checks that parse), with no committed check
   text rewritten. `--self-test` and `--audit` cover the multi-line
   form, including a multi-line vacuous check shown flagged.
3. **R3** — the full `python tools/docs_verify.py` is run and every
   failure among the newly-executed checks is tabled as a FINDING
   (document:line, the claim it defends, verbatim output), classed
   (a) pass / (b) claim rotted / (c) check malformed beyond the
   grammar. Nothing in `src/` and no committed check text is repaired.
4. **R4** — `docs/AUDIT_BASELINES.md` carries the new authoritative
   totals, with the superseded "3 shallow-clone" baseline kept visible
   as history and the reason it undercounted.

## Out of scope (PARKED, not fixed)

- Any map document other than `SCHEMA.md`.
- Any `src/` file.
- Repairing class-(c) malformed checks or rotted claims found by R3.
- The four in-flight parallel windows' files and tranche directories.
