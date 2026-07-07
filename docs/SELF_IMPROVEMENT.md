# Driver Instructions: Improving the Harness From Its Own Record

*How an operating agent (driver) uses the experiment logs to improve
DeepReason itself. `docs/AGENT.md` tells you how to drive the harness on a
problem; this file tells you how to drive it on the harness. The same
discipline applies: nothing changes on vibes, every claim cites a committed
log, and refuted predictions get recorded, not buried.*

---

## 0. The reading rule (start here, budget your attention)

**Read the latest `experiments/results/INDEX_*.md` and nothing else first.**
The index is one line per experiment with its result file; it is the map of
what is already known. Do not re-read the whole corpus — it is large, and
the index exists precisely so you don't have to.

Drill down in this order, only as far as your task requires:

1. Latest `INDEX_*.md` — always.
2. The specific `experiments/results/<report>.json` files your hypothesis
   touches — only those.
3. The narrative doc behind them (`docs/BASIN_REPORT.md`,
   `docs/OPERATOR_DIAGNOSIS.md`, `docs/MINI_STRESS_REPORT.md`, ...) — only
   if the report file leaves the method unclear.
4. Raw run roots (`runs/`, gitignored — regenerate via the scripts) — only
   to re-derive a number you intend to dispute.

If an older index exists, consult it only when the latest one explicitly
points backward.

## 1. Where improvement ideas come from

In priority order:

1. **Caveats recorded in the latest index.** Every honest caveat is a
   pre-scoped experiment (e.g. "not budget-matched", "n=1 per condition",
   "single-seed", "regime unreachable on this family"). These are the
   cheapest wins: the method already exists, only the missing arm needs
   running.
2. **Accounting anomalies.** Any reconciliation divergence, invisible
   spend, or truncation pattern from a live run. These have historically
   produced the highest-value fixes (the 8.4% retry-spend finding, the
   delta=833 mid-retry leak) — and they start as **zero-token log
   forensics** (the T0 pattern), not as new runs.
3. **Refuted or dead machinery.** Components the record shows are placebo
   or inert are candidates for removal — removal is an improvement, and
   MiniReason's cut list shows the precedent.
4. **New failure modes observed while driving.** If you hit one during a
   normal problem run, log it as a candidate hypothesis here rather than
   patching it ad hoc.
5. **The harness's own output.** Pointing the harness (or MiniReason) at a
   question about its own behavior is a legitimate source of hypotheses —
   the creativity and criticism-design runs did exactly this. Treat the
   surviving conjectures as *hypotheses to test*, never as findings.

## 2. The improvement loop (one iteration)

Follow all six steps in order. Skipping step 2 (pre-registration) is the
failure mode this file exists to prevent.

**Step 1 — Hypothesize.** One sentence, falsifiable, with the number that
would refute it. Cite the index line(s) that motivate it.

**Step 2 — Pre-register.** Write `experiments/<name>_prereg.yaml` *before*
running anything: the prediction as literally written, the decision rules
and thresholds, the arms, the budget, and what result would count as
refutation. Follow the shape of the existing preregs
(`basin_study_prereg.yaml`, `criticism_decisive_prereg.yaml`). Commit it
before the run so the prediction is timestamped ahead of the data.

**Step 3 — Run cheap first.**
- Zero-token analyses (log forensics over existing committed roots) before
  any spend.
- MiniReason arms before full-harness arms — a mini root is a valid parent
  root, so nothing is thrown away if the result warrants escalation.
- Budget every arm explicitly; match budgets across arms you intend to
  compare (the unmatched-budget caveat in the record exists because this
  rule was once skipped).
- Re-certify any judge seat on a new provider before trusting its scores.

**Step 4 — Report honestly.** Write
`experiments/results/<name>_report.json` with the measured numbers, and
record the verdict *against the prereg as written*. A prediction that
failed in its literal form is reported as refuted even if the underlying
causal claim survived — the record's credibility is the asset being
protected. Never delete or amend an old report; supersede it.

**Step 5 — Only now change code.** A harness change must cite the report
that justifies it (in the commit message). Then verify:
- `python -m pytest mini/tests` (includes the graduation contract),
- the parent test suite,
- `deepreason.invariants.verify_root` on a fresh smoke root,
- byte-equal replay of at least one existing committed root, to prove the
  change didn't alter the meaning of the historical record.

**Step 6 — Update the map.** Add one line per experiment to the latest
`INDEX_*.md` (or start a new dated index for a new session), pointing at
the report file. If the finding changes operating guidance, update
`docs/AGENT.md` or the relevant narrative doc in the same commit. An
experiment that isn't in an index does not exist.

## 3. Rules of engagement (harness-improvement edition)

1. **The record outranks you.** If your intuition disagrees with a
   committed report, the move is a new pre-registered experiment, not an
   edit to code or to the report.
2. **Nothing is deleted.** Reports, preregs, and indexes are append-only,
   exactly like run logs. Superseding is allowed; silent replacement is
   not.
3. **One hypothesis per prereg.** Bundled predictions make refutation
   ambiguous.
4. **Prefer removal to addition.** Every component must earn its keep by
   measurement; when in doubt, the burden of proof is on the machinery,
   not on its absence.
5. **Don't tune on the test.** If you iterate a design against a
   measurement, that measurement is spent — confirm on a fresh problem or
   seed before claiming the improvement.
6. **Respect the determinism contract.** Any change that would make an
   existing committed root replay differently is a breaking change to the
   evidence base — flag it to the human before merging, never slip it in.
7. **Stop conditions apply here too.** If two pre-registered attempts at
   the same improvement come back refuted or inconclusive, write up why
   and return the question to the human rather than burning a third
   budget.

## 4. Bootstrapping a session

A minimal self-improvement session, end to end:

```
1. Read the latest experiments/results/INDEX_*.md.
2. Pick the highest-priority item per Section 1 (state why in one line).
3. Write and commit the prereg.
4. Run the cheapest arm that can refute the prediction.
5. Commit report + index line (+ code change with its verification,
   if the result justified one).
6. Report to the human: hypothesis, verdict as written, what changed,
   what it cost, and the next candidate from the index.
```
