# Results — the defended trial's task kind, and the census that did not know it

## 2026-09-10 — what the record showed

Every defended trial wrote a record that the run's own security check called
invalid. `verification/report.py::_transaction_findings` decides a v6 work
transaction's authority by an `if/elif` chain over `task_kind`, ending in
`else: unknown v6 task kind`. `WorkflowTaskKind` has eight members; the chain
had arms for seven. `DEFENDED_TRIAL_STEP` was added by the 2026-08-13
defended-trial wiring — in `workflow/models.py`, three packages away — and no
arm came with it.

Because `VerificationReportV2.valid` is integrity AND security, one trial step
was enough. Measured, not argued:

| root | trial steps | `verify_root` violations | security findings | `valid` |
|---|---|---|---|---|
| `run-02818acc38961781e2e820d0d6b591fb` (live solo, 22 trials) | 75 | **0** | 76 | false |
| `2026-08-12-live-grounded-extension-expansion/run` | 494 | 0 | 495 | false |
| `2026-09-02-live-p-a2-corrected/run` | 116 | 1 (pre-existing) | 117 | false |
| `2026-09-02-…/failed-epoch3-run-1b89ed64e050c354` | 26 | 0 | 27 | false |
| `2026-09-01-live-all-modules-p-a1/run` | 10 | 0 | 11 | false |

721 trial steps across five committed roots; 721 findings, plus one
`run-result-verification` echo each. The records REPLAY correctly on all but
one, and that one was already dirty. It was never the runs that were wrong.

The gap predates the 2026-09-09 solo tranche, and that was shown rather than
asserted: an offline stub on the older `ENGAGED_CRITICISM_AUTHORITY=defended_trial`
road, with none of that tranche's switches, produces the identical finding at 3.

## What was fixed

One `elif` arm, inserted before the closing `else` and never in place of it,
under a frozen-surface grant recorded verbatim in `FIX.md` §10 and in
`docs/map/INV-frozen-surfaces.md`. The arm reads
`criticism_policy.authority == "defended_trial"` — the SAME condition
`run_manifest.py::_route_seat_behavioral_contract_assignments` uses to grant
the defender/judge/variator seats their trial contracts, so the census and the
compiler cannot drift on what "authorized" means — and re-derives the
authorised contract through the same `wire_contract_for` that grant uses,
resolved against the route seat's own presentation profile.

Two things were measured BEFORE the code was written, and both are what made
the road safe to take: the derivation reproduces the recorded `contract_id` on
**721 of 721** committed trial steps with zero mismatches, and the payload's
declared role equals the route lease's role on every one.

## What the record now shows

A run that carries defended trials and reaches its terminal on the fixed code
stores `security_valid: true` about itself and reports `valid: true` — the
whole chain, in one artifact (`proof/VERIFY_stub_terminalized_after.txt`
against `proof/REPRO_stub_terminalized_before.txt`). Four forgery shapes stay
reported, each mutation-proved; a task kind outside the enum reports exactly as
before.

The five committed roots keep `valid: false`, and that is correct rather than a
shortfall. `terminalize_text_run` asked this same reader for a summary at each
run's terminal and froze `security_valid: false` into its `run-result.json`.
That is now those runs' own testimony about what the instrument told them, and
a committed root is not editable — evidence that changes when the code changes
is not evidence. What moved on them is the noise: `transaction-authority`
findings go from 26/10/75/116/494 to **zero**, leaving exactly one security
finding apiece.

## Residue — what remains unproven

- **The continuation gate and the report still disagree**, now by one finding
  instead of seventy-six. Whether the gate is meant to consult the report's
  security channel at all is a decision about which runs may be continued, not
  a defect fix. PARKED P1.
- **`tools/blast_radius.py` reports CLEAR for every path under
  `src/deepreason/verification/`**, which is half of frozen surface 3, while
  its own source comment claims the list is "verbatim from" the map. Found
  mid-tranche, disclosed in the grant request the operator read before
  granting, recorded as `docs/ERRATA.md` E88, PARKED P2, not fixed here.
- **verification × workflow still has no seam document.** The `Traps` entry and
  its enum check are a tripwire — they fail when the NEXT kind is added without
  an arm — not a seam.
- **No live run.** The defect is in a reader; a live run would add cost and no
  evidence. So no defended trial has yet been driven end to end against a real
  provider on the fixed tree.
- **The `hv-variation-step.v1` payload rides the trial's task kind** (48 of the
  721 steps). The arm accepts it because the manifest grants the variator seat
  under the same condition; whether the demarcation sampler deserves its own
  kind was not opened.

Accepted does not mean true: what is shown is that the instrument now measures
trial work against the authority the manifest froze for it, and that four ways
of faking such work are still caught. It is not shown that the authority the
manifest freezes is the right authority — that is `CON-authority`'s question,
not this tranche's.
