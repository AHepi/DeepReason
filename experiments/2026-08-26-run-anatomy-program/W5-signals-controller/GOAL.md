# GOAL — W5, the signals and allocation-controller census

Tranche directory:
`experiments/2026-08-26-run-anatomy-program/W5-signals-controller/`
Route: `deepreason-orchestrator`. Window: W5 of the RUN ANATOMY PROGRAM
(registered in `../PROGRAM.md`), answering dimension **D7 — Signals**:
the operator's phrase *"were signals working"*.

## The one goal

**Measure, from the typed record alone, whether the declared signals were
produced, whether any consumed signal violated its declared staleness
bound, what the allocation controller read and did, what observably
changed downstream of each decision, and whether the
efficiency-never-evidence boundary held on live data.**

This is a MEASUREMENT tranche, not a defect tranche. Nothing under `src/`
or `tests/` is touched. Every defect the census surfaces is PARKED with a
ready-to-send prompt; none is fixed here.

## The census population, and why it is these roots

The operator's scope: *"every root that ran after the signal-consumption
tranche landed (attempt-4, P-R1, P-C1 ARM H at minimum; the
controller-tuning history includes the E43 incident root — include it as
the known-positive control)"*.

The signal-consumption tranche is
`experiments/2026-08-21-change-rung1b-ii-signal-consumption/` (Rung 1b-ii,
delivered 2026-08-21: seat-instance keying, the compiled topology matrix,
and the `allocation open-loop for signal X` notice). Selecting inventory
rows with `first_ts >= 2026-08-22` yields exactly **nine roots**, and the
four the operator named by hand are all inside it:

| # | root | run id | first_ts | state | cycles | operator's name |
|---|---|---|---|---|---|---|
| 1 | `experiments/2026-08-22-live-reach-rich-run/failed-epoch1-run-40e713b3…` | `40e713b30a147dfc` | 2026-08-22T14:01 | failed | 2 | — |
| 2 | `experiments/2026-08-22-live-reach-rich-run/run` | `40e713b30a147dfc` | 2026-08-22T14:18 | failed | 2 | **E43 incident root** (known-positive control) |
| 3 | `experiments/2026-08-22-change-epoch3-second-lineage/failed-attempt2-run-bb045538…` | `bb0455384ea09b5b` | 2026-08-23T10:23 | failed | 0 | — |
| 4 | `experiments/2026-08-22-change-epoch3-second-lineage/failed-attempt3-run-bb045538…` | `bb0455384ea09b5b` | 2026-08-23T18:37 | failed | 2 | — |
| 5 | `experiments/2026-08-22-change-epoch3-second-lineage/run` | `bb0455384ea09b5b` | 2026-08-24T04:02 | completed | 8 | **attempt-4** |
| 6 | `experiments/2026-08-24-change-rung7-wounds-falls-succession/run` | `40e713b30a147dfc` | 2026-08-25T01:53 | failed | 0 | — |
| 7 | `experiments/2026-08-25-poietics-program/run` | `1b31f0065687bd24` | 2026-08-25T09:55 | completed | 12 | **P-R1** |
| 8 | `experiments/2026-08-25-change-constructive-frontier/void-inert-battery-run-6913328037a61ca6` | `6913328037a61ca6` | 2026-08-25T19:07 | failed | 11 | — |
| 9 | `experiments/2026-08-25-change-constructive-frontier/run` | `1950b3d0ee228113` | 2026-08-25T19:46 | failed | 15 | **P-C1 ARM H** |

**One deliberate widening, stated so it can be overruled.** The
declared-but-silent question is asked as *"which registered signals
emitted NOTHING **anywhere** … how many have **ever** carried a value in a
live run?"*. "Ever" and "anywhere" are not satisfied by nine roots, so the
SILENCE census runs over **all 54 inventoried roots**, while production,
staleness, consumption, effect and open-loop are measured on the nine.
Both populations are stated on every table that reports a number.

## Falsifiable success criterion

The tranche succeeds if and only if all seven hold, and every number is
re-derivable by running the committed instrument against the committed
roots:

1. **Declared-vs-emitted table.** Every name in `SIGNAL_DECLARATIONS` and
   every family in `PREFIX_DECLARATIONS` appears exactly once, marked
   EMITTED or SILENT, with per-root and per-cycle emission counts for the
   nine-root population and an ever-emitted verdict over all 54.
2. **Staleness verdicts.** For every signal a consumer actually reads, the
   declared staleness bound is stated and a PASS/FAIL/NOT-DECIDABLE verdict
   is recorded, with the reason for any NOT-DECIDABLE given in the record's
   own terms rather than as a shrug.
3. **Decision-and-effect table.** Every controller policy artifact in the
   nine roots is listed with: cycle, the evidence it read, the knobs it
   moved, the envelope it moved inside, the anchor the envelope was
   computed from, whether the E43 lease ceiling clamped it, and the event
   that logged it.
4. **Effect rows, including null ones.** For each decision, what the record
   shows changed downstream — per-seat completion caps and per-seat token
   spend before and after, candidates per cycle. "Tuned and nothing
   changed" is recorded as a row, never omitted.
5. **Open-loop census.** Every `controller-authority` record's `open_loop`
   list is extracted, and each named signal is adjudicated REAL (no
   producer ever emitted it in that root) or SPURIOUS (a producer did).
6. **The law check on live data.** No signal value and no allocation
   decision correlates with any label change: the `status_changed` stream
   of the nine roots is joined against controller decision cycles, and
   either the boundary is confirmed or the violation is named with its
   event sequence numbers.
7. **Honest ledger.** `RESULTS.md` records the residue plainly, including
   what a record cannot show about counterfactuals.

The tranche FAILS if any reported number cannot be re-derived by the
committed instrument, or if a gap is reported as a finding.

## Scope contract

- READ-ONLY on `src/` and `tests/`. Proven at the gate by
  `git diff --stat origin/main -- src tests` being empty.
- No committed run root is opened writable, and none is modified. The
  instrument reads `log.jsonl`, `objects/`, `progress.jsonl`,
  `run-status.json` and `run-manifest.json` as bytes; it never constructs a
  writable `Harness` over a committed root.
- W4 and W6 run concurrently. W5 writes ONLY this subdirectory. In
  particular it does NOT touch `../PROGRAM.md`, `../inventory.py` or
  `../ROOT_INVENTORY.json`, which are W1's under the program's concurrency
  contract; `ROOT_INVENTORY.json` is READ as the shared substrate.
- Defects become entries in `PARKED.md`, each with a ready-to-send prompt.

## Map ids resolved (map preflight)

Read before designing, per CLAUDE.md and `dr-drive-harness` §4:

| id | why it is in scope |
|---|---|
| `DR-INV-signal-contract` | read FIRST: the owning authority for D7 — the three layers, seat-instance keying, the open-loop notice, and the efficiency-never-evidence row this census must re-check on live data |
| `DR-INV-frozen-surfaces` | read before designing: `harness.py` event application and the replay-validation formats this census reads are frozen, which is why the tranche only reads them |
| `DR-CON-seats` | seat instance vs role — the unit of allocation, and the key every table in this census joins on |
| `DR-SUB-scheduler` | owns `Controller.step()`'s call site, the transport-drop site that tags `dropped-call`, and the cycle boundary a `cycle`-staleness signal is measured against |
| `DR-SUB-llm` | the route firewall and `EndpointLease.verify` — the downstream consumer that refused a lawful controller narrowing in the E43 incident |
| `DR-SEAM-llm-x-scheduler` | the seam `INV-signal-contract` names as the worked case for "what refuses this knob downstream" — read before either side |
| `DR-SUB-harness` | `log.jsonl`, `objects/artifact/`, and `record_measure` — the substrate. **Frozen**; read-only here |
| `DR-SUB-verification` | `verify_root` re-derives `route_cap_for_knob` to decide what a logged policy authorized; the census reports the stored verdict, never a re-run that repairs |
| `DR-CON-run-identity` | which directories are roots, and what a retirement prefix means for the population above |

No map document is modified: nothing in this tranche changes code, so
nothing here may advance a `Verified-at:` stamp.

## Three hazards recorded before they can be walked into

**H1 — the controller's decisions are NOT Measure events.** `docs/ERRATA.md`
E43 records this exact mistake in a shipped comment: the controller's
applied decision is a **`Refl` event carrying an artifact with
`provenance.role == "controller"`**, whose `content_ref` is
`inline:{"cycle":…,"evidence":…,"knobs":…}`. Only its *authority*,
*rehydration*, *hold* and *transport-drop* signals are Measure events. A
census that looks for controller tuning under `Measure` finds nothing and
would report "the controller never ran" — the false negative this tranche
exists to avoid.

**H2 — `POLICY_SIGNALS` names five signals the controller does not read as
recorded values.** `allocation.POLICY_SIGNALS` declares
`allocation.seat-truncation.v1`, `allocation.seat-repair.v1`,
`dropped-call`, `allocation.policy-authorized.v1` and
`allocation.policy-contested.v1`. Of these, only `dropped-call` is a logged
Measure tag; the other four are computed in-process
(`Controller._process_signals` reads `event.llm.truncated`/`.attempts`
directly, and `allocation.policy_is_authorized`/`policy_is_contested` read
`harness.state.status`). "Declared but never emitted" is therefore the
EXPECTED state for four of the five, and the census must report it as a
measured fact with its mechanism named, not as a bug it discovered.

**H3 — a per-cycle count needs a cycle, and Measure events carry none.**
The log event has `seq` and `ts` but no cycle field. Cycle boundaries are
re-derived from the `cycle` Measure tag (emitted once per cycle) and
cross-checked against `progress.jsonl`; where the two disagree the
disagreement is reported rather than silently resolved.

## What this tranche will not do

- It will not fix anything, in `src/`, `tests/`, or any map document.
- It will not re-run `verify_root` in a way that opens a root writable; the
  STORED `REPLAY_VALIDATION.json` verdict is what it reports.
- It will not treat model prose, or its own prose, as evidence.
- It will not launch a live run. Every number here comes from committed
  roots.
