# Validation — every SPEC acceptance check, against the tree

Verdict: **PASS**, with two spec items amended before the freeze line and
one acceptance criterion corrected mid-run because as written it could
not be satisfied on this container. Both are named below rather than
quietly met.

| S | acceptance check | result |
|---|---|---|
| S0 | no byte under `src/` changes | PASS — `git diff --stat 0f6bf2c854 -- src/ \| wc -l` = 0, checked at every commit; `git status --porcelain src/` empty throughout |
| S1 | 13-row census of the shipped critic brief in PREREG | PASS — PREREG §2; derived by rendering (`cells.py --census`), not by reading |
| S2 | F1 renders in C10, not in C00 | PASS — step 3: `C10 provenance=True`, `C00 provenance=False` |
| S3 | F2 renders in C01, not in C00 | PASS — step 3: `C01 history=True`, `C00 history=False` |
| S4 | C00 byte-identical to default; four cells distinct; one env assignment | PASS — `default == C00: True`, `all four distinct: True`, `src/ bytes unchanged: True` |
| S5 | 120 targets, reproducible selection | PASS (amended by A9) — `SELECTION.sha256 b07661e3…` identical on re-run; eligibility now requires recorded history |
| S6 | 60 pairs, 10 per class, single-difference assertion | PASS — `60 pairs, 10 per class`; `DEFECT_KEY.sha256 b1813c10…` identical on re-run |
| S7 | key and PREREG sealed BEFORE the first call | PASS — commit `954d81846` "step 5: the freeze line" precedes every commit adding `raw/`; `sha256sum -c` passes both files |
| S8 | measures from the record; no self-reported number | PASS — AST check over `measure.py`: no banned field is read (the criterion was corrected mid-step; see below) |
| S9 | M1 two detectors, blind, agreement reported | PASS — `M1_PRIMARY.json` and `M1.json`; grader row key-set assertion passes; agreement 0.887 |
| S10 | M2 per cell + saturation rule | PASS — 1.000 in all four cells; `saturated: true`; the rule fired and is carried into both verdicts |
| S11 | M3 over every attempt, `attack_true >= att_edges` | PASS — asserted and holds in all four cells |
| S12 | M4 per cell, matched caps | PASS — `M4.json`; one model, one `max_tokens`, one `timeout_s`, one pack budget across cells |
| S13 | M5 blind, keymap with scores | PASS — row key set `{bid, target, criticism}` asserted; keymap written in the same act as the scores. The measure itself is recorded as a FAILED INSTRUMENT (4 of 5 criteria at ceiling), which is a result about the instrument, not a failed check |
| S14 | one of three verdict words per factor, with numbers | PASS — RESULTS.md: F1 INCONCLUSIVE, F2 INCONCLUSIVE |
| S15 | sample-size arithmetic in PREREG | PASS — PREREG §7, `98.11` pasted with its expression |
| S16 | green soak, ≤3 concurrent, key from the gitignored file, detached, snapshot armed | PASS — `SOAK.txt` rc=0; `CONCURRENCY = 3`; `git check-ignore` on the env file exits 0; no committed file contains the key; `raw/driver.log` from a `setsid nohup` launch; snapshot commits in the log |
| S17 | all deliverables exist | PASS — PREREG.md + .sha256, DEFECT_KEY.json + .sha256, SELECTION.json, raw/, RESULTS.md with a Residue section, PARKED.md |
| S18 | no default changed; targeted ring green | PASS — 37 passed, 0 failed on the four files that pin the shipped brief and the seat-section interface |
| S19 | the three law consequences stated in PREREG | PASS — PREREG §9 |
| S20 | a commit per step, clean tree | PASS — see the log; final check in DELIVERY |

## The one acceptance criterion that had to be corrected

**S8's check, as written, could not pass.** It said `measure.py` "contains
no read of any field named `score|confidence|rating|self`", checked by
text search. The rule stated in the file's own docstring contains those
words, so the file could never satisfy a grep for them. Corrected inside
the step to check FIELD READS by parsing the file's syntax tree, which is
what the criterion meant. Recorded because a criterion silently loosened
to fit is worth more suspicion than one that failed.

**CHECKLIST step 15's criterion was unreachable as written too.** It said
"0 failed" for `docs_verify`. `docs/AUDIT_BASELINES.md` records 5 or 6
expected failures on a shallow clone, so 0 was never available here. The
criterion actually applied is ZERO DELTA against the base commit's own
run of the same command, measured in a clean worktree at `0f6bf2c854`:
6 failed on base, 6 on this branch, failure lists identical.

## Amendments folded in before the freeze line

- **A9** — eligibility gained a history clause, or factor F2 would have
  run at 70 observations per level against the 99 its own arithmetic
  demands.
- **A10** — F2 is prior-objection exposure, not rebuttal history: zero
  discharges of any kind exist in any source root.
- **A11** — the selector was renamed off the standard library's `select`.

## Drift found during validation, and how it was disposed

Two map checks went red on a branch that had changed nothing under
`src/`. Traced to a test fixture that picks the smallest committed run
root and assumes it made no provider calls; this tranche's 480
four-event bench roots each made one. The claim those tests guard was
never falsified. The tranche changed how it stores its OWN evidence —
480 loose roots became `raw/roots.tar.gz`, inside its own declared area
— and left the fixture alone. Parked as P6. No assertion was weakened.

## Gate

    python -m pytest tests/ -q -n 4
    4956 passed, 6 skipped in 1187.25s (0:19:47)      0 failed
