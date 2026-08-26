# W3 — evidence and scratch: what was USED, versus carried

Run-anatomy program, measurement tranche W3. **READ-ONLY**: this tranche
changed nothing under `src/` or `tests/`, and every defect it found is a
parked prompt, not a fix.

    git diff --stat origin/main -- src/ tests/     # empty; the gate

## Read in this order

| file | what it is |
|---|---|
| `RESULTS.md` | the honest ledger — 11 findings, then the residue |
| `TABLES.md` | per-document and per-section usage; the scratch call-and-consequence table |
| `EXEMPLARS.md` | six verbatim excerpts from the record, nothing paraphrased |
| `PARKED.md` | six ready-to-send prompts for what W3 found and did not fix |
| `GOAL.md` | the bounded goal, its machine-decidable criteria, resolved map ids |

## Re-derive everything

    python experiments/2026-08-26-run-anatomy-w3-evidence-scratch/evidence_census.py
    python experiments/2026-08-26-run-anatomy-w3-evidence-scratch/scratch_census.py
    python experiments/2026-08-26-run-anatomy-w3-evidence-scratch/tables.py
    python experiments/2026-08-26-run-anatomy-w3-evidence-scratch/exemplars.py

The two censuses take ~1 and ~3 minutes over all 64 committed roots and open
every root READ-ONLY. `tables.py` and `exemplars.py` are presentation only —
they compute no number of their own, so neither document can drift from the
census JSONs or from the record.

Pass a root path to either census to run it on one root:

    python .../evidence_census.py experiments/2026-08-25-poietics-program/run

## The headline, in four lines

- P-R1's 212 verified citations are real. **591 of its 623 admitted blocks
  were never shown to any model** (the legend caps at 32), and every one of
  its 70 verified quotes ends inside the legend's 160-character excerpt.
- The critic seat was shown the evidence 21 times and cited it 3 times. What
  it referenced instead was the candidate it was attacking.
- A scratch note in a run that could read it back has its distinctive wording
  reappear in a later artifact at **18.1%**, against **4.3%** in runs that
  provably could not read theirs back (Fisher exact, p = 0.0004).
- Eight roots — the eight most recent — write scratch with retrieval switched
  off. P-R1 is one of them: 17 notes, nothing that could read them.

Only RECORD-LEVEL use is measurable. Whether a model attended to a section or
a note it was shown is in no record, and is never inferred here.
