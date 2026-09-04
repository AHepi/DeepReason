# Delivered: does a blind critic perform better?
Branch: `claude/blind-critic-experiment-synir6` (pushed, tree clean)

## What changed

Nothing in the harness. Zero bytes under `src/`, checked by hashing every
`.py` in the package before and after the whole experiment and again at
every commit.

What was built is an instrument and its evidence, all under
`experiments/2026-09-04-experiment-blind-critic/`. Four versions of the
critic's brief exist as registered configuration — today's shipped brief,
one that adds the school and author seat of the target, one that adds the
objections already raised against it, and one with both. Registering them
changes no source file, and the first renders byte-identical to what ships
today. 120 accepted conjectures drawn from five committed runs — 60
untouched and 60 each carrying one mechanically planted fault — went to
all four briefs against the live provider: 480 real criticism calls
through `rules/crit.py`, every one preserved.

The answer to the question is that neither blindness was shown to help or
hurt at the bar this tranche set for itself before any call. Hiding who
wrote the target is a flat null (0.508 against 0.500 over 240
observations). Hiding what has already been objected to points the way the
operator conjectured — 0.542 blind against 0.467 informed, matched pairs
14 to 5 — at 7.5 points against a 20-point threshold and p = 0.245. Both
verdicts are INCONCLUSIVE, recorded as such.

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "Census it and state, in the PREREG, exactly which provenance and which history the default critic brief carries" | done | PREREG §2, 13 rows, derived by rendering |
| R2 | "F1 provenance: labels OMITTED vs PRESENT (school id, origin, author seat)" | done-with-assumption A1 | cells.py; the record has no `origin` field, so origin is read off the author role — and every target here is conjecturer-authored, so only school and seat vary |
| R3 | "F2 history: rebuttal + discharge history OMITTED vs PRESENT" | done-with-assumption A10 | no rebuttal or discharge exists in ANY source root (zero events of every discharge kind). F2 tests prior-objection exposure; the gap is stated in PREREG §3 and RESULTS residue |
| R4 | "TWO BLINDNESSES, TWO FACTORS, never conflated" | done | four cells, two factors, each level pooling two cells; separate verdicts |
| R5 | "a registered layout per cell; no code edit — if a cell needs a source edit, PARK it and stop" | done | `src/` sha256 unchanged across the whole registration; the stop condition did not fire |
| R6 | "a fixed set of accepted artifacts… half UNTOUCHED, half with ONE planted defect" | done-with-assumption A9 | SELECTION.json, 60/60, reproducible digest. Eligibility gained a history clause or F2 would have been underpowered; P-A2's run drops out because its conjectures carry no recorded objections |
| R7 | "planted by the same method the judge study used" | done-with-assumption A2 | `plant.py`; three classes verbatim, three adapted because this pool carries none of the source pool's fields (measured, SPEC M2) |
| R8 | "ground-truth key committed BEFORE any call and sealed by digest" | done | commit `954d81846`, before any `raw/` commit; `sha256sum -c` passes |
| R9 | "MEASURES, fixed in PREREG before any call (no model self-reported number)" | done | PREREG §6, sealed; AST check that no self-report field is read |
| R10 | "M1 sensitivity: planted defects the critic's criticism names" | done | M1_PRIMARY.json (blind panel) and M1.json (lexical), agreement 0.887 |
| R11 | "M2 false attack: sound artifacts the critic attacks" | done | M2.json — 1.000 in every cell; the pre-registered saturation rule fired |
| R12 | "M3 warrant rate: criticisms that become attack edges" | done | M3.json — 0 in every cell, floor as predicted |
| R13 | "M4 spend per criticism, matched caps across cells" | done | M4.json plus a config-identity assertion |
| R14 | "M5 sharpness, BLIND-judged by the committed three-judge protocol, cell and provenance fields OMITTED ENTIRELY" | done | 1437 blind scorings; row key set asserted. The measure is reported as a FAILED INSTRUMENT — 4 of 5 criteria at ceiling |
| R15 | "'Performs better' … more real error found at no worse false attack, not 'more criticism'" | done | PREREG §8's rule; and it bit — a significant sub-threshold result was recorded inconclusive rather than promoted |
| R16 | "SAMPLE SIZE decided by the record… state the number and its arithmetic" | done-with-assumption A5 | PREREG §7. The saturated sustain rate carries no variance to power anything; the size comes from M1, which is what the request asks to be sensitive |
| R17 | "read EVERY criticism attempt from the typed attempt objects… not from attack edges alone" | done | forms recovered from each `attempt_trace`'s `raw_ref` blob; `attack_true >= att_edges` asserted per cell |
| R18 | "critic model as configured on main's launch config; at most 3 concurrent calls" | done-with-assumption A6 | glm-5.2, which CLAUDE.md's own header names as main's provider; `CONCURRENCY = 3` |
| R19 | "Green cycle_soak before any live launch; detached launch; snapshot loop armed" | done | SOAK.txt rc=0; `setsid nohup`; snapshot commits in the log |
| R20 | "PREREG (frozen, digest committed before calls), sealed key, raw records preserved, RESULTS with one verdict per factor and the residue" | done | all present; raw records as `raw/calls.jsonl` plus `raw/roots.tar.gz` |
| R21 | "An inconclusive result is recorded as one." | done | both factors INCONCLUSIVE; the 20-point bar was not moved after the numbers were visible |
| R22 | "The default critic exposure on main is NOT changed" | done | the shipped layout and shell are untouched; 37 tests pinning them pass |
| R23 | "Read CLAUDE.md IN FULL (the 2026-08-28 judge laws, and 2026-09-03)" | done | PREREG §9 states all three consequences |
| R24 | "Commit and push at every phase boundary." | done | one commit per step, plus snapshot commits during the run |

No requirement is `not-done` and none is deferred.

## Assumptions the operator may override

- **A1** — "origin" is read off the author role; every target here is
  conjecturer-authored, so F1 is in practice a school-and-seat label test.
- **A2** — three of six defect classes are adapted; four of six now mutate
  the prose field, where the source had two of six.
- **A3** — the false-attack saturation rule, fixed before any call.
- **A4** — the judging protocol's machinery transfers; its criteria were
  re-written for criticism. (They still failed — see P3.)
- **A5** — sample size comes from the objection volumes, not the saturated
  rate.
- **A6** — a controlled bench rather than a managed run, and glm-5.2 as the
  critic seat.
- **A7** — the single-target criticism path, never the batch renderer.
- **A8** — observe-only criticism authority in all four cells, so no judge
  sits between the critic and any measure.
- **A9, A10, A11** — the three amendments folded in before the freeze line.

## Map delta

No map document changed or was created. This tranche changed no behaviour,
so no `Verified-at:` stamp may advance and no `Traps` entry is earned;
advancing one would be a false stamp. `docs_verify` reports the same six
failures on this branch as on the base commit, with an identical failure
list — measured, not assumed, in a clean worktree at `0f6bf2c854`.
Left stale: none by this tranche.

## Errata

**E74** added to `docs/ERRATA.md`: `AUDIT_BASELINES.md`'s shallow-clone
delta is four git-availability rows, not the three it lists — the fourth,
`INV-frozen-surfaces.md:736`, fails on a missing branch ref exactly as the
listed rows do. It matters here rather than as bookkeeping: two checks
really did regress on this branch, and only a base-commit diff separated
them from an under-specified baseline. Left uncorrected in
`AUDIT_BASELINES.md` itself, which may only move in a tranche that moves
the value.

## Parked (not done, not promised)

Six entries, each with a ready-to-send prompt in `PARKED.md`:

- **P1** two committed soak cases (`pc1`, `pc2`) cannot compile a manifest
  at all — the gate in front of every live launch has a hole in it.
- **P2** the provider now rejects the reasoning value the newest committed
  launch config sends; a relaunch from it would fail at the first seat call.
- **P3** nothing applies to an experiment's own measures the standard the
  map checks already have — that a check which cannot fail is refused. This
  tranche's sharpness rubric is the fixture that proves it is needed.
- **P4** the critic may never read two of the structured fields it is
  shown: a fault planted in the counterconditions was named in 0 of 240
  blind judgements across all four briefs.
- **P5** no conjecturer in any committed root has ever discharged an open
  criticism — hundreds of undischarged submissions, not one answer.
- **P6** a committed test picks a run root by size and assumes it made no
  provider calls, so any tranche committing small roots turns two map
  checks red without touching `src/`.

**Recommended next: P2.** It is the only one that blocks work rather than
describing it — the newest committed launch config cannot currently make a
provider call, so the next live tranche hits it at cycle 0. P1 is its close
second for the same reason.
