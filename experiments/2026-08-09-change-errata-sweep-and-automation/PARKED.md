# Parked — not done, not promised

## P1 — `test_bronze_report.py`'s gate_measures/gate_blocked mismatch
still fails the full gate (already known: D2's PARKED P-D2-3)

WHAT: `pytest tests/ -q -n 4` fails
`test_bronze_report.py::test_census_totals_internally_consistent`
(`assert counts["gate_blocked"] == census["streams"][stream]
["gate_measures"]` -> `159 == 165`). This tranche independently
reconfirmed the failure is pre-existing (byte-identical on a fresh
`origin/main` checkout, isolated venv) and out of this docs-only
tranche's scope (no `src/`/`tests/` file touched). It is the SAME
defect already found and parked by
`experiments/2026-08-08-change-pipeline-design-d2/PARKED.md` item
P-D2-3, dated 2026-08-08 — not a new discovery, a re-confirmation that
it is still unresolved five tranches later.

Not fixed here, on purpose: this tranche's `REQUEST.md` scopes it to
`docs/ERRATA.md` and two `.claude/skills/` files; a bronze-census
arithmetic defect is a `src/`/`tests/` code fix, not a committed
document's claim shown wrong, so it belongs to
`deepreason-orchestrator`, never this ledger's or this workflow's own
change track.

Ready-to-send prompt: "`tests/test_bronze_report.py::
test_census_totals_internally_consistent` fails with `assert 159 ==
165` (gate_blocked vs gate_measures) on a clean `origin/main` checkout
— confirmed pre-existing and unrelated to any recent docs-only tranche.
Diagnose starting from `dr-set-goal`, using
`experiments/2026-08-08-change-pipeline-design-d2/PARKED.md`'s P-D2-3
entry as the prior investigation record (it already narrows the
mismatch to the bronze census's gate-Measure counting) and this
tranche's `VALIDATION.md` Full-gate section as the reconfirmation
evidence (byte-identical failure on `origin/main`, isolated venv,
2026-08-09)."
