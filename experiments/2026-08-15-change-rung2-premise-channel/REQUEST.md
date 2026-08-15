# REQUEST — Rung 2: the premise channel and the problem-layer lifecycle

Route: `dr-change-orchestrator`. **Rung 2 of the v2 calculus program**
(`experiments/2026-08-14-change-calculus-reconciliation-v2/LADDER.md`).
Date: 2026-08-15. Branch: `claude/calculus-reconciliation-v2-qqghvn`.

## 1. Authority

Operator, verbatim, on the delivered Rung 1b-i and the ladder revision:

> Cool. continue

Substantive authority, all previously ledgered:

- **H2** (pre-decided): the premise channel, generalised — a critic may register
  a problem's hidden presupposition as an ordinary artifact AND an adjudicated
  attribution artifact; when the attribution stands unrefuted and the premise is
  refuted, the §9.8 orphan cascade fires unchanged.
- **H1** (pre-decided): a failed conjecture mints nothing. Rung 2 must therefore
  ship *translate* — the only remaining way a problem is replaced — before
  Rung 3 deletes the successor trigger.
- **D-2** answered Road B: the operator's siren case, "what is the colour of a
  siren", refuted by argument alone with no conjecture ever proposed on π.
- **D-3** answered **A**: premises are derived, not stored.
- **Amendment 3** (R37–R42): the producer gap is filled from the allocation
  layer — multiple forms, purpose-built detection signals declared through the
  Rung 1b-i contract, config-routed depth-vs-breadth sensitivity, dials
  automatic by default and user-adjustable.
- **The 2026-08-14 law**: no cross-version obligation. A v2 run's own record
  stays typed, append-only, replayable by v2.

## 2. Requirements

| # | Requirement | Source |
|---|---|---|
| M1 | The **premise** (artifact X) and the **attribution** (artifact ρ, "π has premise X") are ordinary artifacts. No new node type; recognition by commitment, not by a `kind` field. | H2 |
| M2 | Law 9.4′ — an attribution `mention`s its premise and MUST NOT `dependence`-ref it, so refuting the premise cannot knock over the attribution. | H2 |
| M3 | `premise_orphaned(π)` is DERIVED from the log; both grades (premise refuted / premise unaccredited). | H2, D-3 |
| M4 | The three resolutions — retire / translate / independence — are registered artifacts, each attackable and therefore reversible. | H2, N1 |
| M5 | Marks are lazily materialised and deprioritise their problem in scheduling. **Attention only.** | §9.8, C5 |
| M6 | The operator's siren sequence runs end to end, solo, with **no conjecture ever proposed on π**. | D-2 |
| M7 | A premise carries a demarcation rent battery requiring a SUBSTANTIVE commitment, so a premise that forbids nothing is refuted by program. | R27 |
| M8 | **A producer exists and a test proves it fires.** A deliberately simple one, plus the detection signals declared through the signal contract. | Amendment 3, R37/R39 |
| M9 | Nothing may rank, admit or accept a conjecture differently for carrying or lacking an attribution. | formalism-optional |
| M10 | No problem is minted from any conjecture's failure. Failure may redirect ATTENTION only. | H1 |
| M11 | N3: no resolution asserts insolubility; retirement is reversible. | §9.8, N3 |

## 3. Map preflight

`DR-INV-frozen-surfaces` first. Then the seams before the subsystems:
`DR-SEAM-ontology-x-rules` (owns `ontology/problem.py` + `rules/spawn.py`),
`DR-SEAM-adjudication-x-rules` (the warrant→edge chain the attribution must
ride without adding an edge species), `DR-SEAM-scheduler-x-rules` (orphan marks
deprioritise; retirement removes from selection without deleting),
`DR-SEAM-evaluation-x-rules` (the rent battery runs on the existing evaluation
path). Then `DR-SUB-ontology`, `DR-SUB-rules`, `DR-SUB-scheduler`.
New document owed: the problem-layer lifecycle (pose → attribution → mark →
resolution), recorded as a map gap by the v2 preflight.

## 4. Amendments

### Amendment 1 (2026-08-15) — Rung 2 step 2: wire the channel

Operator, verbatim:

> Rung 2 step 2 of the v2 calculus program: wire the premise channel, and
> prove it fires on a live run. Route through dr-change-orchestrator.
>
> SCOPE, three parts:
> (1) The premise rent battery: a demarcation criterion pinned onto premise
>     artifacts requiring a SUBSTANTIVE commitment -- reuse
>     measures/reach.py::_substantive; structural checks must NOT satisfy it
>     (the self-immunisation trap documented in rules/warrants.py::
>     formally_backed). This needs the crit half of active();
>     measures/demarcation.py holds two stubs that raise NotImplementedError
>     and nothing imports them (drift row M-1, corrected).
> (2) The wiring: the critic pack gains the premise invitation; the scheduler
>     consults premises.premise_work_invited, deprioritises marked problems
>     (premise_orphaned) and skips retired ones (retired_problems).
>     ATTENTION ONLY -- no label may move.
> (3) Declare the three detection signals through the Rung 1b-i contract
>     (src/deepreason/signals.py, SignalDeclaration): problem thrash,
>     attack-target entropy, independence-resolution rate. New signals may
>     NOT use unit/staleness "unspecified" -- the census test forbids it.
>
> HARD CONSTRAINTS: no problem is minted from a conjecture's failure (H1 --
> failure may redirect attention only); nothing ranks, admits or accepts a
> conjecture differently for carrying or lacking an attribution; NO new LLM
> role (it would move every qualification subject digest and cost a ~14
> minute battery per home). Allocation touches efficiency, never evidence.
> NOT OWED: any cross-version proof -- the 2026-08-14 law retired
> replay-byte-unchanged obligations and old-root sweeps as gate obligations.
>
> TESTS THAT MATTER: the producer fires in an offline run of the ACTUAL loop,
> not just in a unit test of the rule; a premise falls by DEMARCATION with no
> hand-written refutation (this is what the offline siren test does not
> prove); a marked problem is deprioritised and a retired one is not
> selected. Then ONE guarded live run judged on typed outcomes only --
> verify_root, run state, the record -- to see whether a real critic ever
> files an attribution. A live miss is inconclusive, not a failure; record it
> either way.
>
> GATE: full gate 0 failed; docs_verify full (3 pre-existing CON-run-identity
> failures are the recorded baseline on a shallow clone); map moves in the
> same commit. Commit and push at every phase boundary.

Requirements added by this amendment:

| # | Requirement | Source |
|---|---|---|
| M12 | The premise rent battery: a demarcation criterion PINNED ONTO premise artifacts requiring a SUBSTANTIVE commitment, reusing `measures/reach.py::_substantive`. Structural checks must NOT satisfy it. Builds the `crit` half of `active()` in `measures/demarcation.py` (today two unimported `NotImplementedError` stubs — drift row M-1). | Amendment 1 (1); supersedes nothing, REFINES M7 |
| M13 | The wiring: the critic pack gains the premise invitation; the scheduler consults `premise_work_invited`, deprioritises `premise_orphaned` problems and skips `retired_problems`. ATTENTION ONLY — no label may move. | Amendment 1 (2); REFINES M5/M8 |
| M14 | The three detection signals — problem thrash, attack-target entropy, independence-resolution rate — declared through the Rung 1b-i contract (`signals.py`, `SignalDeclaration`). Neither `unit` nor `staleness` may be `unspecified`. | Amendment 1 (3); REFINES M8 |
| M15 | NO new LLM role. (It would move every qualification subject digest and cost a ~14-minute battery per home.) | Amendment 1, hard constraints |
| M16 | The producer fires in an offline run of the ACTUAL loop, not only in a unit test of the rule. | Amendment 1, tests |
| M17 | A premise falls by DEMARCATION with no hand-written refutation. | Amendment 1, tests |
| M18 | A marked problem is deprioritised and a retired one is not selected. | Amendment 1, tests |
| M19 | ONE guarded live run, judged on typed outcomes only (`verify_root`, run state, the record), asking whether a real critic ever files an attribution. A live MISS is inconclusive, not a failure; recorded either way. | Amendment 1, tests |
| M20 | NOT OWED: any cross-version proof. No replay-byte-unchanged obligation, no old-root sweep as a gate obligation (2026-08-14 law). | Amendment 1 |

### Amendment 2 (2026-08-15) — a second check for prose

Operator, verbatim, in reply to the step-2 status report that disclosed the
residue ("a premise a critic writes is bare prose, so it never pays rent —
filing an attribution is effectively the accusation, and the rent battery is
its mechanical adjudication rather than an independent second test"):

> Ok. A second check needs to be added for prose.

| # | Requirement | Source |
|---|---|---|
| M21 | A PROSE premise — one carrying no substantive commitment — must face a SECOND check before it falls. The rent battery alone may not fell it. | Amendment 2 |

**Status: the second check's IDENTITY is underdetermined by the message and is
the subject of one batched question to the operator** (three readings differ
materially in behaviour and effort; see DELIVERY/the session report). Nothing
is implemented against M21 until it is answered — writing the wrong second
check is more expensive than asking.
