# W5 — signals and the allocation controller

Window W5 of the RUN ANATOMY PROGRAM (`../PROGRAM.md`), dimension **D7 —
Signals**: the operator's *"were signals working"*. Read-only; fixes
nothing.

## Read in this order

| file | what it is |
|---|---|
| `GOAL.md` | the one goal, the nine-root population and why it is those, the success criterion, the map ids, and the three join hazards this census was built around |
| `RESULTS.md` | the honest ledger — the four headline answers, the causal chain for the inert steering, and the residue |
| `DECLARED_VS_EMITTED.md` | every declared signal name, marked emitted or silent, over both populations; the structural silences; and the eight tags the registry does not declare |
| `DECISIONS_AND_EFFECT.md` | all 47 controller knob-moves with envelope, anchor, lease ceiling and downstream effect; the E43 known-positive control; the "tuned and nothing changed" rows |
| `STALENESS.md` | a verdict per signal that declares a bound, and how each verdict is decided |
| `LAW_CHECK.md` | efficiency-never-evidence, on live data, with every exemption listed |
| `PARKED.md` | six findings, each a ready-to-send prompt |

## Re-deriving every number

    python3 census.py     # -> SIGNAL_CENSUS.json, CONTROLLER_CENSUS.json,
                          #    STALENESS.json, LAW_CHECK.json
    python3 render.py     # -> the four .md tables

`census.py` reads `../ROOT_INVENTORY.json` (W1's, read-only here) and the
committed roots. It opens nothing writable and imports `deepreason.signals`,
`deepreason.allocation` and `deepreason.controller` only to re-derive
envelopes and seat-instance names through the shipped functions rather than
through a second copy of their rules.

## The answer in four lines

- 32 of 111 declared signal names have ever carried a value in a live run.
- 47 allocation-controller decisions, all in-envelope; **0 reached the wire**.
- 1 declared staleness bound is exceeded; 84 names declare no bound at all.
- 0 efficiency-never-evidence violations.
