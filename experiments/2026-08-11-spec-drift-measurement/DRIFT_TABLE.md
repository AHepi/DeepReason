# Spec drift table — harness-spec v1.3 + v1.4/v1.5/v1.6 amendments vs. main's current surface

Measured 2026-08-11. Read-only grep across the four spec files; each term
cross-checked against src/deepreason/ and docs/map/ to confirm it is a
real, current concept (not a typo) and whether it lives on main today or
only on the unmerged `claude/adjudication-judge-seats-optins-4nb7ov`
branch (confirmed NOT merged: `git merge-base --is-ancestor
<branch-tip> HEAD` fails against current main-derived HEAD).

| Term | v1.3 | v1.4 | v1.5 | v1.6 | Real on main today? | Where it lives |
|---|---|---|---|---|---|---|
| `seats` (the architecture, not the English word) | 0 | 0 | 3 hits, all incidental ("manifest seat", "critic seats", "shared seats" — never defines the seat-binding system) | 0 | Yes, extensively | `seat_events.py`, `seat_bindings.py`, `docs/map/CON-seats.md` |
| `seat-bindings.v1` (the typed schema) | 0 | 0 | 0 | 0 | Yes | `seat_events.py:66` (`schema_: Literal["seat-bindings.v1"]`), `docs/map/CON-seats.md` |
| `conjecturer.turn.v7` (wire contract) | 0 | 0 | 0 | 0 | Yes | `llm/wire.py`, `run_manifest.py`, `docs/map/SUB-manifest.md` |
| `candidate_checker` | 0 | 0 | 0 | 0 | Yes | `llm/wire.py`, `oracle.py`, `informal/skeleton.py`, `signals.py` |
| `LEGACY_CRITICISM_ENABLED` | 0 | 0 | 0 | 0 | **No — unmerged only.** Referenced as "pending delivery" in `docs/FORM_DR1_RUN_APPLICATION.md:80` (committed on main), but the flag itself (`config.py`, `preparation.py`, `cli/main.py`) exists only on `claude/adjudication-judge-seats-optins-4nb7ov`. | n/a on main; will need documenting when that branch merges |
| `school seat` / `SCHOOL_SEATS_ENABLED` | 0 | 0 | 0 | 0 | **Partially.** Seat routing/leasing for schools (`resolve_school_role_lease`, `llm/firewall.py`, `docs/map/SEAM-llm-x-manifest.md`) is real on main; the `SCHOOL_SEATS_ENABLED` opt-in flag itself is unmerged-branch-only. | mixed — routing on main, the toggle is not |
| `blind same-model judges` / adjudication-blindness | 0 | 0 | 0 | 0 | Yes | `verification/report.py`, `docs/map/SUB-adjudication.md`, `docs/map/INV-frozen-surfaces.md` |
| `config referee` | 0 | 0 | 0 | 0 | Yes | `verification/report.py:833-852`, `llm/roles.py:51,313` |

## Reading the table

Seven of eight terms are 100% undocumented in the spec series, and the
eighth ("seats") appears only as an ordinary English word three times,
never as the name of the typed system it now is. Two of the eight
(`LEGACY_CRITICISM_ENABLED`, `SCHOOL_SEATS_ENABLED`) are not yet real on
main at all — they exist only on the unmerged adjudication branch, so
their drift will WIDEN, not narrow, once that branch lands (main will
gain the surface; the spec will still not mention it). The other six are
real, shipped, exercised-by-tests concepts on main today with zero spec
coverage.

This is not evidence the spec is wrong — v1.3-v1.6 make no claim these
terms contradict. It is evidence the spec has not been extended to cover
four rungs' worth of shipped work (seats, schools' seat-routing, the v7
wire contract, config-referee review) that postdates v1.6. Per
CLAUDE.md's map convention, this is exactly what an append-only amendment
is for — v1.4/v1.5/v1.6 already established the pattern (each "amends...
does not replace or modify" the prior file).

## Recommendation

Draft a new **v1.7 amendment** (`docs/harness-spec-v1.7-amendment.md`)
documenting the six real, on-main, undocumented surfaces (seats/
seat-bindings.v1, conjecturer.turn.v7, candidate_checker, school-seat
routing, adjudication-blindness/blind-judge structure, config referee),
in the same "amends, does not rewrite" style as v1.4-v1.6. Defer
LEGACY_CRITICISM_ENABLED/SCHOOL_SEATS_ENABLED documentation to a
follow-on v1.8 (or a v1.7 revision) once the adjudication branch's merge
status is known — documenting an unmerged flag now risks the amendment
describing something main doesn't yet do, the exact inverse of today's
drift.

Alternative considered and NOT recommended: editing v1.3-v1.6 in place.
CLAUDE.md is explicit ("never edit existing spec text") and the amendment
chain's own self-description forbids it structurally.

## STOP — question for the operator

**Scope of the careful spec update: should this program draft a v1.7
amendment now covering the six surfaces already real on main (seats,
conjecturer.turn.v7, candidate_checker, school-seat routing,
adjudication-blindness, config referee), deferring the two
adjudication-branch-only flags to a later amendment once that branch's
merge status resolves — or should the whole update wait for the
adjudication branch to land first, so ONE v1.7 amendment can cover all
eight terms at once?**

Recommendation: draft v1.7 now for the six on-main surfaces. Waiting
means real, already-shipped, already-tested surfaces (seats, the v7
wire contract) stay undocumented for however long the adjudication
branch takes to merge, for no benefit — nothing about documenting them
depends on that branch. A v1.8 (or v1.7 revision) can cover the
remaining two once they land, in the same append-only style.

## STOP — second question (Item 6, docs/ organization)

A separate investigation this session inventoried `docs/` (100 files,
~22,000 lines, several coexisting naming conventions, one self-declared
superseded file) and researched accepted standards (Diátaxis,
Architecture Decision Records, docs-as-code). Full inventory,
standards primer, and a concrete proposal are in this tranche's
`DOCS_REORG_PROPOSAL.md`. Summary: the repo's own map system
(`docs/map/`) already IS a strong reference layer; the spec-amendment
series is structurally closest to an ADR chain; per-experiment
RESULTS.md and five standalone top-level technical reports are
"explanation" documents sitting at the top level rather than under
`experiments/`; `docs/ERRATA.md`/`ERRATA_EXECUTOR.md` fit no standard
cleanly and should stay their own genre rather than be force-fit.

**Should this program add a single `docs/INDEX.md` navigation page now
(zero renames, zero risk to the 854 automated checks or the code/test
citations into `docs/map/`, `docs/ERRATA*.md`, and the spec series),
and treat any actual file MOVES (the five standalone reports, an
ADR-style rename for `docs/proposals/`) as a separate, smaller,
opt-in follow-on tranche?**

Recommendation: yes to the index now, defer moves. The index delivers
the "messy repo, make it easier to navigate" complaint immediately and
at zero risk; moves are real but bounded cost that should not block on
or be bundled with either this v1.7 spec question or the index itself.

## Combined answer format

One message answering both questions is enough: (1) draft v1.7 now /
wait for the adjudication branch / other; (2) add the index now, defer
moves / do both now / neither yet.

