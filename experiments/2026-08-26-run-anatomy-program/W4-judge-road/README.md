# W4 — the judge-road autopsy

RUN ANATOMY PROGRAM, Round 1 census, window W4. Dimensions **D5** (judge
activity), **D6** (judge form filling — bounded here to what judges DID,
see PARKED W4-P4), and the adjudication end of **D8** (were commitments
attacked correctly).

Read `RESULTS.md` first. It leads with the finding that matters: the
standing "no defended trial has ever run in this repository" is false, and
the corrected fact is sharper than the one it replaces.

| file | what it is |
|---|---|
| `GOAL.md` | the bounded question, map preflight, scope contract |
| `RESULTS.md` | the honest ledger, five segments, residue in segment 5 |
| `FUNNEL.md` | **generated** — the road walked gate by gate, both roots |
| `ADJUDICATION_SAMPLE.md` | **generated** — the 60 hand-ruled verdicts |
| `EXEMPLARS.md` | **generated** — six rows quoted verbatim |
| `PARKED.md` | four findings, three with ready-to-send prompts |

Instruments, all re-runnable from the committed roots:

    python3 trial_sweep.py            # all 54 roots, _adjudication re-derived
    python3 road_census.py            # both legs, gate by gate, 2 roots
    python3 disclosure_probe.py       # P-R1's terminator, offline, from its config
    python3 verdict_sample.py         # the stratified 60 rows + artifact bytes
    python3 handcheck.py              # independent re-derivation, no deepreason import
    python3 criterion_proxy_probe.py  # criterion quality, measured separately
    python3 tables.py                 # writes FUNNEL.md + ADJUDICATION_SAMPLE.md
    python3 exemplars.py              # writes EXEMPLARS.md

Read-only tranche. `git diff --stat origin/main` names no path under `src/`
or `tests/`, and no committed run root was modified.
