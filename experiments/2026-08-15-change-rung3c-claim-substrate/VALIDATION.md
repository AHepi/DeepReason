# VALIDATION — Rung 3c

Verdict: **PASS.**

| Instrument | Result |
|---|---|
| `python -m pytest tests/ -q -n 4` | **3662 passed, 7 skipped, 0 failed** (825 s) |
| `python tools/docs_verify.py` (full) | 59 documents, 910 checks, **3 failed — all `CON-run-identity`**, the recorded shallow-clone baseline |
| diff, measured against `ee9a4439c` | production **448** / 380, tests **253** / 250, docs **100** / 70 |

## Acceptance checks

| # | Check | Verdict | Evidence |
|---|---|---|---|
| D-a | An open predicate cannot enter | PASS | `test_an_open_predicate_cannot_enter`, `test_a_declared_but_unbuilt_schema_is_refused_with_its_reason` — two DIFFERENT typed codes, so "unknown" and "not yet built" are never confused |
| D-b | Each of the six recognition conditions is required | PASS | `test_each_recognition_condition_is_required`, parametrised over all six |
| D-c | `ensure_problem_subject` is idempotent | PASS | `test_ensure_problem_subject_is_idempotent` — one artifact, and the log length is unchanged on the second call |
| D-d | The controller chooses every ref role | PASS | `test_no_body_field_names_a_ref_role`, `test_the_compiler_is_the_only_authority_on_ref_roles` — an AST walk asserting every `RefRole` site in the package is in `compiler.py` |
| D-e | An attribution MENTIONS its premise | PASS | `test_an_attribution_mentions_its_premise_and_never_depends_on_it` — the mention law now enforced at COMPILE time rather than checked afterwards |
| D-f | Attacking a companion moves `problem_status` and nothing else | PASS | `test_criticising_the_companion_moves_the_problems_standing` — the `Problem` record compares equal before and after |
| D-g | The missing-companion diagnostic names the gap and clears | PASS | `test_the_missing_companion_diagnostic_names_the_gap_and_clears` |
| D-h | No field added to `Problem`/`EpistemicState`/`Event` | PASS | `test_no_field_was_added_to_problem_state_or_event` — `Problem.model_fields` pinned exactly |
| D-i | Gate, docs, map in the same commit | PASS | above; `SUB-calculus.md` + `INDEX.md` in this commit |

## Diff budget: EXCEEDED on all three line items

Production **448/380**, tests **253/250**, docs **100/70**. Disclosed, not
re-baselined. The production overrun is the five-file package boundary the
advice specified — `claims`/`compiler`/`programs`/`operations`/`views` — where a
single module would have been smaller and would have put ref-role decisions
next to body definitions, which is the one thing C2 forbids. The docs overrun is
a new map document, which a new package owes.

## Residue

- **The premise channel is NOT on this substrate.** `premises.py` works exactly
  as delivered at Rung 2; the union carries a compatible
  `poietic.premise-attribution.v1` body and nothing produces it yet. Moving the
  channel across is a later step with its own regression obligations, and until
  then there are two attribution shapes in the tree — one live, one declared.
- **No scheduler integration** (C8), so nothing yet selects on `problem_status`.
  When it does, it must schedule accepted unresolved subjects and must not drop
  refuted or orphaned problems from history.
- **Seven of nine schemas are declared and unbuilt.** That is the honest state,
  refused with its own code, and the map says so.
