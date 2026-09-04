<!-- tranche: 2026-09-04-defect-dead-seat-retirement -->

# Results — a run now survives a dead seat

## 2026-09-04 — the defect, and what the record showed

P-A1 (`run 4565139800f5ca02`) stopped at cycle 5 of a 3 000 000-token budget
with 1 093 086 spent, `state: failed`, `stop_reason: operational_failure`,
message `V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY`. `deepreason stop-report` on
that root (`proof/stop_report.txt`) says why in three rows nobody had put side
by side:

- **§3.** Every one of the run's 41 `RemoteDisconnected` faults is on ONE
  endpoint. `conjecturer#1` (ollama-glm-5.3): 17 attempts, 6 zero-token, 23
  faults. `conjecturer#0` (ollama-deepseek-v4-pro-0813): **30 attempts, 0
  zero-token, faults `none`**. `argumentative_critic#0`, same healthy endpoint:
  12 attempts, faults `none`.
- **§4.** ENVIRONMENT SUPPORTED, CONFIGURATION RULED OUT, and the report's own
  note: "a seat that passed its form at full marks did not lose the ability
  between qualification and the run". Both conjecturer seats had passed 20/20
  first-pass with 0 repairs on every form.
- **§5.** `continue: REFUSED`, `amend: REFUSED`.

The manifest makes the loss concrete: `school-0` and `school-2` were bound to
the healthy seat, `school-1` and `school-3` to the dead one, and all four
criticism bindings pointed at the healthy seat. Half the conjecture capacity
and all of the criticism capacity was alive when the run stopped.

## What the diagnosis found, and where the first reading would have gone wrong

The exhaustion was ALREADY typed per seat. `RouteSeatInsufficientCapabilityV1`
is minted by the transaction service and lands in
`insufficient_capability_by_route_seat`, keyed `(role, seat, endpoint_id,
route_sha256)`, and four sites refuse further dispatch on that key. Those
refusals are correct and are untouched. What was missing was a CALLER that
could absorb one: `Scheduler.step`'s school loop has three exception arms and
`RunManifestError` matches none, so it reached the terminalizer
(`run-result.json`: `"error_type": "RunManifestError"`).

The obvious fix follows from that — add a fourth arm — **and the reproduction
refuted it.** With one problem in the run, the dead seat's next dispatch
carries the payload whose atomic decomposition the exhaustion left incomplete,
and `workflow/atomic_recovery.py` raises `ValueError("atomic child is
terminally failed")` BEFORE the guard is consulted at all. P-A1 took the guard
road only because it had many problems, so its next dispatch carried a payload
the seat had not seen. A one-problem run takes the other road on the very next
cycle.

That is the single most useful thing this tranche produced, and it changed the
design rather than decorating it: **retirement is decided where the seat is
CHOSEN, not where a dispatch is refused.** The school is dropped from the
cycle's allocation before `conj` is entered, and both roads close with one
change. Both are pinned in the committed suite, so a fix closing one and not
the other stays red.

## What shipped

`runtime/seat_retirement.py` is the one derivation and decides nothing the
record does not hold: the exhaustion trigger reads the seat's own record, the
transport trigger reuses `provider_health.dead_seats` from 2026-09-03. Each
stood-down seat gets one `seat.retired.v1` receipt, deduped against the record
rather than an in-memory flag, so a resumed run neither re-discloses nor falls
silent. `seats_bound` never shrinks — retiring a seat must not rename every
seat instance the run has already recorded.

When no conjecturer seat is left, the run stops `provider_unavailable`: a CLEAN
stop that `continue` accepts, per the 2026-08-29 law, and deliberately NOT
composable. The switch is `Config.SEAT_RETIREMENT_POLICY`, ON by default; `off`
reproduces the old death exactly and emits `seat.retirement-disabled.v1` with
the warning the ungated-seats law requires.

Seven consumers of a fixed seat set were enumerated and each handled or given a
typed disclosure. Three are disclosures rather than repairs, and the judge one
is the one worth stating: with a seat gone the cross-family ensemble is
unobtainable, so judge summons are SKIPPED and the predicate is not relaxed —
the measured 0-2.5% false-conviction regime is the cross-family one and every
looser configuration measured over-convicts at 47-60%.

## Frozen surfaces

The surface-2 contact the instruction forecast never happened, and
`tools/blast_radius.py`'s own output proves the avoidance rather than a
sentence claiming it: `harness.py` appears in neither contact list, because a
retirement needs no new record kind. One contact remains — a single
`data.pop("SEAT_RETIREMENT_POLICY", None)` line in `run_manifest.py`, whose
effect is to keep every manifest and qualification digest byte-identical. The
operator granted it on the record; it is ledgered in `INV-frozen-surfaces.md`.

## Two things found on the way, recorded rather than absorbed

**A claim I priced wrong, and the operator caught it.** Presenting the size
overrun I described 209 lines of comments and docstrings as "conventions the
repo requires". Only 31 of them were: CLAUDE.md's comment rule is a
RESTRICTION on what a comment may say, not a requirement to write one, and no
rule mandates a production docstring. Pricing a choice as an obligation is how
an over-budget diff gets waved through, so it is written into `FIX.md`
Amendment 3 rather than left in chat.

**Two tripwires that had outlived their tranches** — `docs/ERRATA.md` E74. Each
asserted something about "this tranche" with only one end of its range pinned,
so each turned red on the first granted contact after its own tranche merged —
barring exactly what `INV-frozen-surfaces.md` exists to permit. Both re-aimed,
neither relaxed, and the re-aimed map check's coarseness is stated beside it
rather than hidden.

## The honest residue

Accepted does not mean true. Six things this tranche does NOT show are listed
in `VERIFY.md`; the two that matter most:

1. **What causes a seat to exhaust is unchanged.** P-A1's seat was
   unreachable, not incapable, and the record still calls it incapable. Parked
   as `PARKED.md` P1 with a ready-to-send prompt.
2. **No live run.** This container has no credentials, so the proof is
   entirely offline. A live run would show the retirement firing against a real
   transport wall rather than a stub returning invalid output. The mechanism is
   the same either way, but "the same mechanism" is an argument, not a
   measurement.
