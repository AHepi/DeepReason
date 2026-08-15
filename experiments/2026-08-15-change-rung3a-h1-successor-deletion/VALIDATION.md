# VALIDATION — Rung 3a

Verdict: **PASS.**

| Instrument | Result |
|---|---|
| `python -m pytest tests/ -q -n 4` | **3644 passed, 7 skipped, 0 failed** (789 s) |
| `python tools/docs_verify.py` (full) | 901 checks, **3 failed — all `CON-run-identity`**, the recorded shallow-clone baseline |
| diff, measured | production **13**, tests **177**, docs + errata **62** — production and docs well inside their 40/80 line items; **tests 37 over the 140 ceiling** |

## Acceptance checks

| # | Check | Verdict | Evidence |
|---|---|---|---|
| B1 | Refuting an addressed candidate and re-running `scan_spawns` leaves the frontier unchanged | PASS | `test_refutation_alone_cannot_grow_the_problem_frontier` |
| B2 | The frontier still grows by every other structural route | PASS | `test_every_other_structural_trigger_still_fires`; `test_multi_cycle_spawns_and_persistence` still asserts `disc:` and `conn:` |
| B3 | **Mutation:** the old loop reinstated in-process makes B1 fail | PASS | `test_the_regression_would_catch_the_old_loop` — reinstates the branch verbatim in behaviour and asserts the frontier grows |
| B4 | No addressability lost | PASS | the deleted successor only ever copied its parent's criteria under a new id; no problem, criterion, lineage or provenance root is removed. Nothing in the gate's 3644 tests asserts a lost addressee |
| B5 | `SpawnTrigger.SUCCESSOR` still parses and `easy.py`'s repair path still mints its problem | PASS | `test_the_successor_trigger_survives_for_its_remaining_producer`; `tests/test_chunked.py` and `tests/test_website_state_machine.py` green |
| B6 | Full gate 0 failed; `docs_verify` at baseline; map moved in the same commit | PASS | above; `SUB-rules.md`, `SEAM-ontology-x-rules.md`, `SEAM-rules-x-scratch.md` all in this commit |

## Fallout, re-founded rather than weakened

Four tests asserted the deleted behaviour. None had its assertion dropped:

| Test | Was | Now |
|---|---|---|
| `test_multi_cycle_spawns_and_persistence` | `assert any(succ:)` | `assert NOT any(succ:)`, keeping the `disc:`/`conn:` assertions. The negative is what lets the test notice the loop returning |
| `test_focus_family_restricts_selection` | a successor joined the family | asserts no successor joins; the focus-lock property under test is unchanged |
| `test_focus_lock_works_only_the_focused_problem` | successors spawn but are never worked | the lock holds against a frontier that never grew — the same guarantee, a different population |
| `test_successor_descriptions_do_not_nest` | nesting defence via `scan_spawns` | now pins the STRONGER property (no depth of refutation produces a successor at all), and still exercises the description contract on a hand-built chain for the surviving producer |

## Re-derived counts (E27's rule: never increment, re-derive)

`scan_spawns` `_spawn` call sites **7 → 6**; triggers spawned there **7 → 6**;
`SpawnTrigger` enum size **9 → 9** (unchanged, deliberately). Three pinned map
checks moved with them.

## The diff budget, corrected

An earlier revision of this file quoted 17/151/63 — numbers written before the
measurement, not from it. The measured figures are **13 / 177 / 62** (`git diff
--cached --numstat` against `314d15c4f`), and tests are **37 lines over** their
ceiling, not 11. Corrected in the same tranche it was miswritten in. The overrun
is real and its cause is the mutation proof: reinstating the deleted loop in
test code costs about as many lines as the deletion saved, which is the price of
a regression that can actually fail.

## Residue

- **The `easy.py` question is open** and is the operator's (PARKED.md P1). Until
  it is answered, "H1 is applied" means "in the reasoning loop", and the map
  says so rather than leaving the surviving enum member to imply otherwise.
- **Old roots carrying `succ:` problems no longer describe a producible state.**
  Owed nothing under the 2026-08-14 law, and recorded here so nobody reads a
  historical root as evidence the loop still exists.
