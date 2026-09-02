# Coverage charged a conjecture for every falsifiable claim it made

## 2026-09-02 — what the record showed, what was fixed, what remains unproven

**The finding.** The Pareto frontier — the shortlist of surviving artifacts a
run publishes as its best — was inverted on three independent live roots, and
inverted totally. Not skewed: inverted.

    root                        survivors  frontier  frontier composition  dominated
    P-S1 9e48a36b1dec91ee            98        58    58/58 harness-minted  40/40 seed
    P-A1 4565139800f5ca02            11         7     7/7 harness-minted    4/4 seed
    P-R1 poietics-program            58        40    40/40 harness-minted  18/18 seed

Not one artifact answering the operator's question reached a frontier on any of
the three roots, and not one harness-minted `connection` artifact was dominated.

**Why the axis could not have been measuring quality.** Across all 156
survivors on all three roots, **zero commitments FAILED**. Every artifact passed
everything that was actually decided about it. So `coverage` had no quality
signal to carry: its entire variance was the number of falsifiable
counterconditions each artifact had declared. The artifacts answering the
operator's question each passed FOUR commitments; the harness-minted artifacts
that dominated them each passed TWO.

    root   group        n    pass/artifact  fail  overrun/artifact
    P-S1   connection   58   2.00           0     0.00
    P-S1   seed         40   4.00           0     3.23
    P-A1   connection    7   2.00           0     0.00
    P-A1   seed          4   4.00           0     2.50
    P-R1   connection   40   2.00           0     0.00
    P-R1   seed         18   4.00           0     3.61

**The mechanism.** `scheduler.pareto_scores` computed `coverage` as passes over
every EVALUABLE commitment. A commitment can be evaluable, be evaluated, and
still yield no verdict: `programs.OVERRUN`. An observation-valued
countercondition returns it unconditionally, so it counted as a non-pass and
lowered its own artifact's score. Every other consumer of `programs.evaluate`
already read OVERRUN as "no verdict obtained" — `rules/act.py` ("a spec defect,
not the candidate's fault"), `rules/crit.py` twice, `_lean_external_check`'s
docstring ("never a failed proof or a warrant"). The ranking arithmetic was the
sole dissenter. `SUB-evaluation.md` had even STATED the governing rule — *no
`fail` warrant may be minted from an `overrun`* — but stated it about warrants,
and the violator was a consumer that only counts.

The frontier sorted on `coverage` alone because `hv` was structurally
unmeasurable on every v6 run until `5f34e4d00` and `reach` is empirically zero:
`len(state.hv) == 0` and `len(state.reach) == 0` on all three roots.

**Two things the brief did not predict.**

1. *It is five program families wide.* The four `lean_*` programs also return
   OVERRUN while awaiting the pinned external verifier — so a FORMALLY BACKED
   conjecture was penalised for being formally backed. The formalism-optional
   law (R-g: "formal backing may confer protection; its absence confers no
   disadvantage") was being violated in both directions by one division.
2. *Why the guard never fired.* `tests/test_formalism_optional_rank.py` has
   guarded this exact axis since 2026-08-30 and was green throughout. It builds
   its pending commitment as `eval="observation"`, which `programs.evaluable`
   screens out before the battery. No live artifact carries that spelling:
   `workloads/text.py:222-226` rewrites every declared `eval: "observation"`
   into `program:reasoning_observation_pending`, which IS evaluable. **A
   regression test that constructs its own fixture can pin a shape the harness
   normalises away before any artifact carries it**, and no amount of re-running
   it will say so.

**One correction to the tranche's own brief.** The P-A1 write-up's D1 finding
("14 frontier members, 1 seed") came from `deepreason --root … frontier`, whose
handler prints EVERY REGISTERED PROBLEM (`cli/main.py:998-1004`), not the Pareto
frontier. D1 measured the problem population. Measured properly the P-A1 artifact
frontier is 7 of 11 with 0% seed — a sharper result, not a softer one. Recorded
because the number will otherwise be carried forward.

**The fix.** One rule, reader-only: a verdict of OVERRUN leaves the coverage
denominator, exactly as an unmeasured axis leaves `capture.pareto.frontier`'s
pairwise comparison; the axis is omitted when nothing was decided, which
SUBSUMES the 2026-08-30 empty-battery rule rather than replacing it. A
commitment that FAILED was decided and still lowers coverage. Nothing written to
the record changes; no committed root was touched; no frozen surface is
involved. 40 insertions across two files.

**What the record now shows.** Re-scored offline on copies, both formulas
computed in one run and the shipped code asserted against the new one:

    root                     frontier BEFORE      frontier AFTER
    P-S1 9e48a36b1dec91ee    58 (0% seed)         98 — all 40 seed answers on it
    P-A1 4565139800f5ca02     7 (0% seed)         11 — all  4 seed answers on it
    P-R1 poietics-program    40 (0% seed)         58 — all 18 seed answers on it
    known-good 2026-08-12   233                  233 — IDENTICAL, a complete no-op

`verify_root` returns 0 violations on all four roots, before and after.

**Residue — what remains unproven.** Accepted does not mean true.

- On these three roots the frontier becomes the WHOLE survivor set. That is not
  the repair over-reaching — the mutation controls show a real FAIL still
  dominates, and the known-good root does not move at all. It is what happens
  when the only axis carrying variance was a spurious penalty: with `hv` and
  `reach` at zero entries and no commitment failing anywhere, nothing is left to
  discriminate on. **Whether a frontier is usefully narrow under the new rule
  depends on `hv`, and no run has yet been observed with a measured `hv` and
  this coverage rule together.** Not measured here.
- All 204 OVERRUN verdicts on the three roots are the observation program. The
  other four families are covered by the same rule and by unit tests, but **no
  committed root demonstrates them**; the claim about `lean_*` penalising formal
  backing is derived from code, not from a live root.
- `frontier_delta` feeds `StopMetrics`, so a longer frontier can move a
  `converged` stop. Disclosed and pinned status-neutral by test; **unmeasured
  live**, because no run was launched.
- A `predicate:` whose body RAISES is still recorded FAIL, so an author's typo
  is arithmetically indistinguishable from a refutation — and unlike OVERRUN it
  can reach a real warrant. A different shape (it WAS evaluated), deliberately
  not touched, parked as P1 with a ready-to-send prompt.
