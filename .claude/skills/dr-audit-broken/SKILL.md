---
name: dr-audit-broken
description: Audit dimension - find broken code by running every committed verification instrument and tabling deltas against the recorded baselines. Invoked by dr-audit-orchestrator when broken.md is missing.
---

# Audit: broken code

Entry: `LEDGER.md` exists, `broken.md` missing. Exit: `broken.md`
written, LEDGER rows added, proofs in `proof/`.

Broken means: an instrument's output moved from
`docs/AUDIT_BASELINES.md` §Instruments. The instruments define
broken; this worker adds no judgment of its own (G3).

## Operations

1. `pip install -e . --break-system-packages -q` and
   `pip install pytest pytest-xdist jsonschema --break-system-packages -q`.
   Run every command below with `python -m` where applicable; save
   each full output to `proof/broken-<n>.txt`.
2. `python -m pytest tests/ -q -n 4` — compare failures to the
   baseline failure list. Re-run any non-baseline failure serially
   (`python -m pytest <nodeid> -q`) before rowing it: still red →
   verdict `broken`; green serially → verdict `flaky` (row it; flaky
   is a finding unless baseline-listed).
3. `python tools/docs_verify.py` — compare failing checks to the
   baseline list. Non-baseline failure → verdict `broken` (the check
   or the code it pins moved; the fix tranche decides which).
4. `python scripts/wheel_smoke.py` then
   `python -u scripts/wheel_operational_smoke.py` — any non-zero exit
   → verdict `broken`, target = the pin named in the output.
5. RETIRED (operator ruling 2026-08-22, CLAUDE.md §Build and test):
   the root sweep is no longer an audit instrument. Do NOT run
   `tools/root_sweep.py`. Write `proof/broken-sweep.txt` containing
   the single line `retired 2026-08-22 — see CLAUDE.md` so the proof
   count stays auditable.
6. Write `broken.md`: the table of every non-baseline delta, one row
   per finding, columns as the LEDGER. Matches baseline exactly →
   the table plus one line: `all instruments at baseline`, with the
   five proof files as the required proof of looking (G2).

## GATE

Pass: every instrument ran (four live instruments + the retirement
marker file = five proof files) AND every non-baseline delta has a
LEDGER row with disposition `parked`.
Verdict labels: `broken` | `flaky` | `baseline`.

## Activation plant (first run)

Edit one assert in a copy of a passing test to a false constant, run
step 2 scoped to that file, paste the red output, `git checkout --`
the file, paste the clean status.

## Outlets

| Situation | Outlet |
|---|---|
| Any fix impulse | PARK — prompt in PARKED.md, route deepreason-orchestrator |
| Instrument itself crashes | row verdict `broken`, target = instrument, PARK |
| Baseline looks wrong | row it, PARK a baseline-correction prompt (PRECEDENCE 2) |
