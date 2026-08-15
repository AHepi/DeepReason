# SPEC — Rung 2: the premise channel

Traces to REQUEST.md M1–M11. **Diff budget: 900 lines** — production 500,
tests 250, docs 150, budgeted as separate line items per the estimator
correction recorded in Rung 1b-i.

## The two design questions this rung had to settle

### Q1 — how does the harness find a problem's premises? **By lookup.**

The operator asked whether the attribution could be an edge in the existing
support wiring rather than a separate lookup. Answered, and not carried as a
live alternative:

1. **§9.8 requires LAZY materialisation; support propagation is EAGER.** "The
   fall is one event; its thousandfold consequence is paid as the frontier is
   touched, not all at once." Support propagation relabels every dependent on
   every recomputation; on the grounded-extension root — 2,894 problems — that
   is the whole frontier marked at once.
2. **The saving is small.** It would supply the marking only. The two grades,
   the three resolutions and the closure records are built either way.

### Q2 — what produces an attribution? **DECIDED: the critic seat, on a dumb rule, with signals for later.**

Amendment 3 puts the long-term answer in the allocation layer. Rung 2 ships the
hook and the evidence source, not the policy:

- **The producer:** the critic seat's pack gains an invitation to file a premise
  attribution against the problem it is working, alongside its ordinary attack
  on a candidate. No new seat, no new role (qualification digests do not move).
- **The trigger:** deliberately simple and deterministic — offered when a
  problem has ≥ `PREMISE_INVITE_AFTER` refuted candidates and carries no
  standing attribution. This redirects ATTENTION on failure; it mints no
  problem, so H1 is intact (M10).
- **The signals, declared through the Rung 1b-i contract** so Rung 1b-ii's
  policy has something to consume: problem thrash, attack-target entropy, and
  the independence-resolution rate — the calculus's own over-binding diagnostic
  (§9.8).
- **The anti-E28 gate:** a test proving the producer actually fires. The harness
  has twice shipped a mechanism no producer ever reached (the controller that
  never steered; the reach trigger that never fired). Not a third time.

## Changes

| # | Change | R |
|---|---|---|
| S1 | `presupposition-wf` — a program commitment parsing an artifact into ⟨problem-id, premise-id⟩, passing iff both resolve and the parsed premise is the artifact ρ `mention`s. Registered as an ordinary artifact (P6/Refl). | M1 |
| S2 | The mention-law check: an attribution carrying a `dependence` ref on its premise FAILS `presupposition-wf`. | M2 |
| S3 | The premise rent battery — a demarcation criterion requiring a SUBSTANTIVE commitment, reusing `measures/reach.py::_substantive`. Builds the `crit` half of `active()`, today an unimported stub. | M7 |
| S4 | `premise_orphaned(π)` as a derived predicate with both grades; lazy materialisation; scheduler deprioritisation (attention only). | M3, M5 |
| S5 | The three resolutions as registered artifacts: retire / translate / independence. Retirement removes π from selection, never deletes it, and is itself attackable. | M4, M11 |
| S6 | The producer: pack invitation + the deterministic offer rule + three declared signals. | M8 |
| S7 | The problem-layer lifecycle map document, in the same commit. | — |

## Acceptance checks

| # | Check |
|---|---|
| A1 | An attribution with a `dependence` ref on its premise fails `presupposition-wf` |
| A2 | Refuting a premise with no standing attribution marks nothing |
| A3 | Filing an attribution against an unrefuted premise marks nothing |
| A4 | Attribution unrefuted ∧ premise refuted ⇒ π marked, correct grade |
| A5 | **The operator's siren sequence, end to end, solo**: π posed, X and ρ registered, X refuted by the rent battery (a demonstrative verdict, status-changing under every authority mode), π marked, retired — with **no conjecture ever proposed on π** — then ν attacked, X reinstated, retirement attacked, π back on the frontier |
| A6 | Translate mints π₂ with lineage provenance; it is the ONLY path that mints a problem from a problem |
| A7 | Independence closes the orphan and the scheduler treats π as unmarked, computed from the resolution; π's own record is never mutated |
| A8 | Marks are lazy: a fall over N problems materialises no orphan until a problem is focused |
| A9 | An uncited/unattributed conjecture is neither refused nor down-ranked (M9) |
| A10 | **The producer fires** in an offline run of the loop, and the three signals are emitted and declared |
| A11 | A v2 run carrying attributions replays and re-derives identically (within-version integrity) |
| A12 | Full gate 0 failed; `docs_verify` full; `blast_radius` disclosed in advance |

## Scope boundary — D-8

Rung 2 ships the channel for premises that fall **by demarcation or by a failing
formal commitment**. A premise that is contentful and wrong **by argument alone**
needs argumentative status authority, which no solo configuration has today
(drift row W-1). That is D-8, unanswered, and Rung 2's SPEC must not let a green
gate imply the channel is complete.

## Step 2 — the wiring (REQUEST.md Amendment 1, M12–M20)

Step 1 shipped the channel. Nothing calls it. This section specifies the
connection and is the authority for CHECKLIST.md steps 8–15.

### Map preflight (resolved ids)

`DR-INV-frozen-surfaces` (read first; the design below avoids all five),
`DR-INV-signal-contract` + `DR-REC-add-signal` (M14),
`DR-SEAM-scheduler-x-rules` (the pinned import set, the pinned `Config`
partition, the pinned rank tuple — all three are touched or deliberately
not touched), `DR-CON-scheduler-ranking` (the rank tuple again, second
copy of the pin), `DR-CON-packs-and-token-economy` (the crit pack's
section table), `DR-CON-problem-layer-lifecycle` (this tranche's own
document), `DR-SUB-scheduler`, `DR-SUB-rules`, `DR-SUB-evaluation`.

### D1 — the rent battery's commitment is deliberately NOT evaluable

`programs.evaluate` hands a program `(text, budget, artifact)` and no
commitment registry, so no `program:` commitment can see whether the
artifact's OTHER commitments are substantive — demarcation is a property of
the interface, not of the content. The rent battery is therefore a
harness-owned commitment with its own eval kind:

    PREMISE_RENT = Commitment(id="demarcation:premise-rent",
                              eval="demarcation:crit")

Consequences, all of them load-bearing:

- `programs.evaluable()` is False for it, so `crit_program`, `reach_sweep`,
  `hv`, `formally_backed` and the anti-relapse battery all skip it. Every
  `programs.evaluate` call site in `src/` either guards on `evaluable()`
  first or catches `NotEvaluable`; verified call site by call site.
- `measures/reach.py::_substantive` is False for it, so **carrying the rent
  battery can never satisfy the rent battery**. The self-immunisation trap
  (`rules/warrants.py::formally_backed`) is closed by construction, not by
  adding a name to `_STRUCTURAL_PROGRAMS`.
- `harness.py` is untouched: warrant well-formedness requires the commitment
  to be REGISTERED, never that its eval be of a particular kind (the
  `rubric:` branch is the only kind-sensitive line and does not match).

### D2 — how a premise falls

`measures/demarcation.py::crit(artifact, commitments)` is the §6 predicate:
at least one commitment that is evaluable AND substantive. `mod` stays
unimplemented — the operator scoped the `crit` half only.

`premises.py::premise_rent_sweep(harness)` walks the artifacts carrying
`PREMISE_RENT`, and for each one whose `crit()` is False registers a
DEMONSTRATIVE fail warrant through the shared package
(`rules/warrants.py::register_fail_warrant`, `skip_if_on_record=True`).
Demonstrative, so it is status-changing under every authority mode (A5),
and its validity node ν is an ordinary registered artifact, so the verdict
is itself attackable (N1).

### D3 — the filing channel: one optional field, no new role

The critic's existing contracts gain ONE optional field, `premise: str |
None`, meaning **"a presupposition this problem makes that forbids
nothing"** — not "a presupposition". It rides:

| Contract | Model |
|---|---|
| canonical single-target | `llm/contracts.py::ArgumentativeCriticOutput` |
| compact single-target wire | `llm/wire.py::CompactCritic` |
| canonical batch | `llm/contracts.py::BatchCase` |
| v6 batch wire (`batch-critic.v2`) | `llm/wire.py::BatchCriticCaseWireV2` |

No new role and no new `contract_id`, so no qualification subject digest
moves (M15): `qualification.py::qualification_subject_payload` digests the
manifest behaviour and the pair inventory, and a pair carries `contract_id`
as a closed literal — never the contract's rendered JSON schema.

When the field is present AND the invitation was standing for that
problem, `rules/crit.py` registers two ordinary artifacts: the premise X
(carrying `PREMISE_RENT`) and the attribution ρ (carrying
`program:presupposition_wf`, `mention`-ref'd to X, never `dependence`).
Absent or uninvited, nothing is registered and the critic's ordinary
behaviour is byte-identical.

### D4 — `PREMISE_INVITE_AFTER` is a module constant, not a `Config` field

A new top-level `Config` field is not free: `DR-INV-frozen-surfaces`'s own
trap requires an explicit line in `run_manifest.py::_versioned_source_
config_data` (frozen surface 4), and `DR-SEAM-scheduler-x-rules` pins the
`Config` partition counts exactly. The threshold lives in `premises.py`.
Rung 1b-ii owns dials; this rung owns the hook.

### D5 — the scheduler's three consults, all attention

1. `_select_problem` drops `retired_problems(harness)` from the candidate
   pool (the retirement is a consulted resolution, and attacking it puts
   the problem straight back — nothing is deleted).
2. `_select_problem`'s rank gains ONE term, inserted AFTER the `SEED` term
   so the operator's seed question still wins every tie outright, and
   before the reflexive tie-break: a `premise_orphaned` problem yields.
   Both selection modes, matching the existing SEED/reflexive pattern.
3. `step()` consults `premise_work_invited` for the selected problem and
   records the standing invitation as a typed Measure — the anti-E28
   evidence that the producer actually fires.

The pinned rank-tuple checks in `DR-SEAM-scheduler-x-rules` and
`DR-CON-scheduler-ranking` move in the same commit. No `deepreason.rules`
import is added to the scheduler (`premises` is a top-level module) and no
new `config.` read is added on either side, so the seam's import-set and
`Config`-partition pins are untouched.

### D6 — the three signals (M14)

Declared explicitly (never through `_migrated`), emitted once per cycle
from `step()` so the census is deterministic:

| Name | unit | staleness |
|---|---|---|
| `problem.thrash.v1` | ratio | cycle |
| `criticism.attack-target-entropy.v1` | ratio | cycle |
| `problem.independence-resolution-rate.v1` | ratio | run |

Producer-agnostic semantics, each saying what it is NOT evidence of.
`MIGRATION_DEBT` is unchanged: these are new declarations, not migrations.

### Step-2 acceptance checks

| # | Check | R |
|---|---|---|
| A13 | `crit()` is False for an artifact whose only commitments are structural (`json-wf`, `skeleton_wf`, `presupposition_wf`) and False for one carrying only the rent battery itself | M12 |
| A14 | A premise filed with no substantive commitment is REFUTED by the rent sweep, with no hand-written attack anywhere in the test | M17 |
| A15 | The producer fires in an offline run of the ACTUAL `Scheduler` loop: the invitation Measure is on the record and a stub critic's `premise` becomes a registered premise + attribution, and the problem is marked | M16 |
| A16 | A `premise_orphaned` problem is deprioritised and a `retired_problems` problem is never selected, in both selection modes | M18, M13 |
| A17 | The three signals are emitted by the real loop and every one resolves through `signals.declaration()` with a non-`unspecified` unit and staleness | M14 |
| A18 | An uninvited critic response carrying `premise` registers nothing; a conjecture's rank/admission is unchanged by the presence or absence of an attribution | M9, M13 |
| A19 | ONE guarded live run: `verify_root` green, typed terminal state, and the record searched for an attribution — outcome recorded either way | M19 |

### Diff budget — step 2

Step 1's actual spend, measured with `git diff --numstat` (not estimated):
**261 production, 295 tests, 78 map-doc lines** against the headline
500/250/150. Tests were already 45 over their line item at the end of step
1; that overage is recorded here rather than discovered later. Step 2's
ceiling, ledgered now: **production 320, tests 300, map docs 120** (the
tranche's own REQUEST/SPEC/CHECKLIST/RESULTS ledger is not budgeted — it is
the record, not the change). Enforced at every `[COMMIT]` step with
`tools/diff_budget.py`; EXCEEDED is a stop.

### Residue — stated so a green gate cannot imply more than it shows

A premise filed by a critic is bare prose and therefore carries no
substantive commitment, so under this rung **every filed premise falls by
demarcation**. That is why D3's field means "a presupposition that forbids
nothing" and not "a presupposition": the harness can see an artifact's
attack surface and nothing else, so filing IS the accusation and the rent
battery is its mechanical adjudication. The two locks stay distinct in the
channel itself (`premises.py` marks nothing until an attribution stands AND
the premise has fallen), and the recourse is unchanged and threefold —
attack ρ ("the problem never assumed that"), attack ν (the demarcation
verdict), or attach a substantive commitment to X. What this rung does NOT
give is discrimination between a vacuous premise and a true one nobody has
formalised. That is D-8, still unanswered.

## Out of scope

The allocation policy and its forms (Rung 1b-ii + its own experiment program);
frame assertions and standing (Rung 4); the successor-trigger deletion (Rung 3,
which depends on this rung's *translate*).
