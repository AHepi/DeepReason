<!-- DR-INV-signal-contract -->
Verified-at: 748c9ab61
Verify: python -m pytest tests/test_signal_contract.py tests/test_allocation_signal_consumption.py -q
Owns: src/deepreason/signals.py, src/deepreason/allocation.py, src/deepreason/wander.py
Seams: 
Seams-undocumented: scheduler x signal-contract

# The signal contract — three layers, and what may move in each

Operator design law, 2026-08-14 (CLAUDE.md, "Operator design laws"):

> The signal REGISTRY is a CONTRACT, not a wiring: a signal is anything
> declaring name, unit, producer-agnostic semantics, and a staleness bound; new
> setups add signals by declaration through this typed channel, never by
> teaching a consumer about a subsystem.

## What it is

A signal is a declaration, not a wire. `SignalDeclaration` carries the four
fields the law names; `SIGNAL_DECLARATIONS` and `PREFIX_DECLARATIONS` are the
registry; `SIGNALS` and `PREFIXES` are DERIVED views kept for every existing
consumer. The derivation is the point: two hand-maintained copies of one fact is
how a registry stops being a contract.

`check: python -c "from deepreason.signals import SIGNALS, SIGNAL_DECLARATIONS; assert SIGNALS == {n: d.semantics for n, d in SIGNAL_DECLARATIONS.items()}"`

## The three layers, which are not interchangeable

| Layer | What it holds | What it takes to change it |
|---|---|---|
| **FROZEN** | the change protocol itself — decisions typed and recorded, interface-only consumption, envelope bounds, and **allocation touches efficiency, never evidence** | an operator design law; nothing below may relax it |
| **VERSIONED** | the registry and the policy algorithm — policy as a recorded artifact, referee-reviewed | `REC-add-signal` / `REC-revise-allocation-policy`, with the decision recorded |
| **FREE** | parameter values inside declared envelopes | ordinary configuration; no ceremony |

The FROZEN layer's last clause is the one to guard hardest, because it is the
harness's own oldest invariant wearing allocation's clothes: **measures never
adjudicate** (spec §0, calculus C5). A signal may price attention, budget, or
throttling. It may never reach a label.

`check: ! grep -qE "^from deepreason\\.(rules|informal|capture|schools)" src/deepreason/controller.py`

## Interface-only consumption

The allocation controller consumes the signal interface and nothing else. Today
`controller.py`'s only `deepreason` import is `deepreason.ontology`, so the
boundary already holds; the test exists to fail the day it stops holding.

`check: python -m pytest tests/test_signal_contract.py::test_the_allocation_controller_consumes_only_the_interface -q`

## The migration debt, stated

Eighty-nine entries predated the contract. They carry their authors' prose as
`semantics` verbatim, and `unit`/`staleness` of `"unspecified"` — because
inventing a unit for a signal whose author never stated one would be fabrication
dressed as rigour. The census is pinned and may only shrink; a NEW signal
declared `unspecified` fails the gate.

**Eighty-four remain.** Rung 1b-ii paid down five — `controller-update`,
`controller-authority`, `controller-rehydration`, `controller-hold:` and
`dropped-call` — because that rung's consumption side is what establishes when
each is emitted and how long a consumer may believe it. Their SEMANTICS PROSE
was left byte-identical; only the two markers moved, through an explicit
`_PAID_DOWN` table so prose cannot drift while a unit is being stated. The
paydown rule is `REC-add-signal.md` §"paying down the debt": lower the census by
exactly the number fixed, and say in the commit what evidence fixed it.

`check: python -m pytest tests/test_signal_contract.py::test_the_migration_debt_can_only_shrink -q`

## Signals are keyed by SEAT INSTANCE, not role

The operator's clause (2), verbatim: one conjecturer may sit in "multiple
structurally asymmetric seats that may need throttling independently".

The unit of allocation is therefore the SEAT INSTANCE, and `allocation.py` owns
its spelling. A role bound to exactly ONE seat HAS one seat instance, and that
instance's canonical name is the bare role name; the `#<seat>` suffix appears
only where there is more than one seat to tell apart. That is not an exception
to seat keying — it is what seat keying spells for an ensemble of one, and it is
why no knob and no Measure input changes spelling for any topology in a
committed root.

Seat identity was already in the record and no new role or field was added:
`LLMAttempt.seat` is on every attempt, and `LLMCall._school_route_matches_attempts`
already validates it against the school-route receipt. Adding a role would have
moved every qualification subject digest — a ~14-minute battery per home — which
is why the shipped digest is pinned rather than trusted.

`check: python -m pytest tests/test_allocation_signal_consumption.py -q -k "seats_throttle_independently or bare_role_spelling"`
`check: python -m pytest tests/test_allocation_signal_consumption.py::test_the_shipped_qualification_subject_digest_does_not_move -q`

One derivation, not two: `allocation.route_cap_for_knob` is the single rule for
"what cap did the run assign this seat", used by the controller when it writes a
barrier and by replay validation when it re-derives one. A steered cap survives
`verify_root` only if both sides agree, and two copies of that rule is how they
silently stop agreeing.

`check: grep -q "route_cap_for_knob" src/deepreason/invariants.py && grep -q "route_cap_for_knob" src/deepreason/allocation.py`

## Every configuration class compiles, attaches, and closes its loops

The operator's clause (4) is a COMPILED matrix, not an argument: solo,
no-schools, judges-off and legacy-on each compile; the controller attaches and
states an authority naming every bound seat; and every policy-referenced signal
has a producer. Topology-independence is the property — the controller must not
care which of these a run is, because it reads the interface and the interface
answers the same way in all four.

A role KEY with no routes is not a bound seat. The compiler emits all eleven
canonical keys, so a membership test against `manifest.roles` would report a
judge in a run that binds none.

`check: python -m pytest tests/test_allocation_signal_consumption.py -q -k matrix`

## A topology that cannot produce a signal COMPILES

Clause (5), and the all-configurations law applied to allocation: disclose,
never die. `allocation.POLICY_SIGNALS` names what the policy reads, and one
producer predicate per signal decides — from the BOUND ROLES alone, so the same
answer is available at compile time from `manifest.roles` and at attach time
from `adapter.endpoints` — whether this topology contains anything that could
emit it.

The live case: a topology binding no `argumentative_critic` has nothing that can
attack a controller policy, so `allocation.policy-contested.v1` has no producer
and fail-static can never fire. That run still compiles and still steers; it
carries a typed `ALLOCATION_OPEN_LOOP` notice — `CompileNoticeV1` reused
verbatim, never modified — and the `controller-authority` record gains an
`open_loop` list. Extending that record rather than inventing a channel is
deliberate: ERRATA E28's lesson was that a controller with authority over
nothing said nothing, and a controller whose fail-static branch can never fire
must not be silent either.

`check: python -m pytest tests/test_allocation_signal_consumption.py -q -k open_loop`

## Allocation touches EFFICIENCY, NEVER EVIDENCE — the strictest row

The FROZEN layer's last clause, and the row seat keying puts most at risk: a
seat key is PROVENANCE-shaped, and provenance reaching adjudication is what the
harness forbids by construction (spec §0, calculus C5; v0.1 Axiom 4.1, Genesis
Inertness). The guard is a differential, not an assurance: the same scripted
record is run with and without a controller whose two seats are deliberately
asymmetric, and every label, edge and warrant must be identical. Allocation's
OWN policy artifact has a status — that is the design (P6), not a leak — and is
excluded; nothing else may move.

Mutation-proven twice, in a scratch copy
(`experiments/2026-08-21-change-rung1b-ii-signal-consumption/proof/s8_mutation.txt`):
removing the tribunal guard turns the ledger test red, and minting a warrant
against a conjecture whenever a seat-keyed knob moves — the forbidden move in
its most plausible disguise — turns the differential red.

`check: python -m pytest tests/test_allocation_signal_consumption.py -q -k "evidence or verdict"`
`check: ! grep -qE "create_artifact|Warrant|att_add|dep_add" src/deepreason/allocation.py`

**The same row, for the SECOND controller (Rung 8).** `capture/hysteresis.py`
implements §14.7 and Theorem 14.1 is the identical claim in the calculus's own
words: two states with identical artifacts, attacks and dependencies but
different diagnostic values or attention modes have identical labels. It gets
the identical guard — a differential on one scripted record, plus a structural
check — with one deliberate difference from allocation's: `create_artifact` IS
permitted, for the policy artifact and only for it, because a policy that could
not be attacked would be authority without exposure (P6).

Mutation-proven twice, in a scratch copy: teaching `_adjudicate` to read the
recorded mode turns the differential red, and minting a warrant when the mode
is entered — the forbidden move dressed as "so the diversification has teeth" —
turns both the differential AND the structural check red.

`check: python -m pytest tests/test_capture14_hysteresis.py -q -k "theorem_14_1 or constructs_no_edge"`
`check: ! grep -qE "att_add|dep_add|Warrant\(|register_fail_warrant|_adjudicate" src/deepreason/capture/hysteresis.py`

## The THIRD controller, and the row it takes (F3, 2026-08-26)

`wander.py` is a lineage-allocation policy: a FLOOR on the share of worked
cycles the operator-seeded lineage gets, with self-spawned lineages yielding
candidacy while the floor is unmet. It sits in the VERSIONED layer exactly as
the cap policy does — `LINEAGE_POLICIES` is a registry keyed by policy id,
`Config.ATTENTION_ALLOCATION_POLICY` selects from it, and
`Config.SEED_PROBLEM_BUDGET_FLOOR` is a FREE-layer parameter. An unknown policy
id falls back to the shipped default and discloses (`fallback_from`), never
refuses: the all-configurations law applied to a policy selector.

W6 measured why it exists. One run spent **41.2 % of 702 789 tokens** on
`audit:ritual`, a problem it invented about its own critic, while the
operator's question got 53.2 % — and 48.3 % after the spawn appeared at log seq
345 of 3 200
(`experiments/2026-08-26-run-anatomy-program/W6-token-flow/` TABLES.md T12).

`check: python -c "
from deepreason import wander
from deepreason.config import Config
r = wander.LineageReading(cycles=10, seed_worked=3, other_worked=7, floor=0.5)
assert wander.decide(Config(), r).engaged
assert wander.decide(Config(SEED_PROBLEM_BUDGET_FLOOR=0.1), wander.reading_from(Config(SEED_PROBLEM_BUDGET_FLOOR=0.1), cycles=10, seed_worked=3)).engaged is False
assert wander.decide(Config(ATTENTION_ALLOCATION_POLICY='open-lineage.v1'), r).engaged is False
assert wander.decide(Config(ATTENTION_ALLOCATION_POLICY='nope'), r).fallback_from == 'nope'
"`

**The same strictest row, for the THIRD controller.** Allocation touches
EFFICIENCY, NEVER EVIDENCE, and this policy gets the identical guard: a
differential on one scripted record, run with the cap throttling every cycle
and with the null policy never throttling, every status, edge, warrant and
dependency identical. The cap's OWN policy artifact is excluded — that is the
design (P6) — and nothing else may move. `wander.py` is stricter than
`allocation.py` in one respect: it may not even create that artifact, because
the scheduler does, so it imports no `deepreason` module at all.

Mutation-proven twice, in a scratch copy
(`experiments/2026-08-26-change-f3-channels-and-wander-cap/proof/s12_mutation.txt`):
minting a warrant against a conjecture whenever the cap engages — "so the
throttle has teeth" — turns the differential RED, and letting the policy module
reach the graph turns the structural check RED.

`check: python -m pytest tests/test_wander_cap.py -q -k "labels_are_identical or constructs_no_evidence"`
`check: ! grep -qE "create_artifact|att_add|dep_add|Warrant|Status|from deepreason|import deepreason" src/deepreason/wander.py`

**The consumer reads the interface and nothing else.** `scheduler.py` calls
`wander.decide` and `wander.reading_from`; it never names a policy function. A
scheduler that knew it was running `wander_cap_v1` would have to be edited to
run anything else, which is the coupling the registry exists to prevent.

`check: python -c "
import inspect
from deepreason.scheduler.scheduler import Scheduler
src = inspect.getsource(Scheduler)
assert 'wander.decide(' in src and 'wander.reading_from(' in src
for fn in ('wander_cap_v1', 'open_lineage_v1', 'LINEAGE_POLICIES'):
    assert fn not in src, fn
"`

**Selection STAYS read-only.** The decision is computed and STASHED inside
`_select_problem`; the cycle body emits it. `DR-CON-scheduler-ranking` says
selection may not write, and a time-travel harness opened for replay refuses
every write — the first implementation here emitted from the ranking function
and turned two committed suites red, one of them on a read-only harness.

`check: python -c "
import inspect
from deepreason.scheduler.scheduler import Scheduler
src = inspect.getsource(Scheduler._select_problem)
assert 'self._pending_wander = decision' in src
assert 'record_measure' not in src and 'create_artifact' not in src
"`

## Every declared policy signal now has an EMIT SITE

W5's census (2026-08-26) found four of the five `POLICY_SIGNALS` declared,
consumed IN-PROCESS, and emitted nowhere in `src/`: a reader of any committed
root could see the cap a controller applied but not the numbers that moved it.
None was struck — all four are genuinely consumed, and striking a consumed
signal makes the registry LESS true — so all four gained an emit site at the
point where the controller ACTS on the reading, and the two lineage signals
ship with theirs.

The census is now a test rather than an audit, so a sixth silent name fails the
gate the day it is added.

`check: python -m pytest tests/test_wander_cap.py -q -k "phantom or emit_site"`

## Two families read attack-target entropy, and they are not the same quantity

The v2 program's V-6 row, decided at Rung 8
(`experiments/2026-08-25-change-rung8-rent-audit-diagnostics/SPEC.md` §3 D1):
**declare a distinct family; re-found neither Rung 2 signal.** Three populations
carry these names on this tree, and each reads something different.

| population | what it reads | declared? |
|---|---|---|
| `criticism.attack-target-entropy.v1` (Rung 2) | the WHOLE standing attack relation as it stands now — `state.att`, after closure | yes, registry |
| `capture14.attack-target-entropy.v1` (§14.2, Rung 8) | only attacks NEWLY CARRIED inside a fixed sequence-number window `W_m(n)` — `state_diff.carry_add`, before closure | yes, registry |
| `capture/detection.py::adjudicator_metrics` | four same-named quantities over an EVENT window, feeding `raw_flags` and nothing else | **no** — never emitted as a measure |

The decision is not a preference. `problem.thrash.v1` has no §14 counterpart at
all, so "re-found them" was only ever available for one of the two; the log
records `att_add` and `carry_add` as separate relations, so the two registry
entries are two quantities rather than two implementations of one; and changing
what a declared name means while the name and its `.v1` stay put is exactly the
drift the registry exists to prevent.

Each registry entry names the other in its own `semantics`, from its own side.
That is what the first check below holds in place — a future author who deletes
one cross-reference has silently recreated the ambiguity.

`check: python -c "from deepreason.signals import declaration as d; a=d('criticism.attack-target-entropy.v1'); b=d('capture14.attack-target-entropy.v1'); assert a and b and a.semantics != b.semantics and 'capture14.attack-target-entropy.v1' in a.semantics and 'criticism.attack-target-entropy.v1' in b.semantics"`

The third population stays undeclared BECAUSE it is never emitted. That is a
fact about `detection.py`, not a promise about it, so it is checked as one: the
day someone wires `adjudicator_metrics` to `record_measure` without declaring
it, this fails.

`check: ! grep -q "record_measure" src/deepreason/capture/detection.py`

All six §14 diagnostics are declared with a real unit and a real staleness — no
new signal may carry the migration debt marker.

`check: python -c "from deepreason.signals import declaration as d; ns=('stream-contraction','attack-target-entropy','criticism-debt','reinstatement-rate','validity-attack-rate','exogenous-grounding-ratio'); ds=[d('capture14.%s.v1' % n) for n in ns]; assert len(ds)==6 and all(x and x.unit=='ratio' and x.staleness=='cycle' for x in ds)"`

## Where to change what

| To do this | Read | Test |
|---|---|---|
| add a signal | `REC-add-signal.md` | `tests/test_signal_contract.py` |
| revise the allocation policy | `REC-revise-allocation-policy.md` | `tests/test_controller.py` |
| retire a signal's `unspecified` marker | `REC-add-signal.md` §"paying down the debt" | the pinned census |
| key signals by seat instance | `REC-revise-allocation-policy.md`; the seat-instance section above | `tests/test_allocation_signal_consumption.py` |
| add a signal the POLICY reads | `REC-add-signal.md`, then `allocation.POLICY_SIGNALS` **and its producer predicate** | `tests/test_signal_contract.py` |
| change how a run's attention splits between lineages | `REC-revise-allocation-policy.md`; register a policy in `wander.LINEAGE_POLICIES` | `tests/test_wander_cap.py` |

## Traps

- **A consumer that needs to know the producer has left the contract.**
  `semantics` is producer-agnostic on purpose. The moment a consumer branches on
  which subsystem emitted a signal, the registry is a wiring again and the next
  setup will have to teach that consumer about itself.
- **`unspecified` is a marker, not a default.** It records that nobody stated a
  unit. Using it for a new signal converts an honest debt into a licence.
- **Rung 1b was only half-delivered by 1b-i, and was completed by 1b-ii on
  2026-08-21.** Seat-instance keying, the compiled topology matrix, and the
  `allocation open-loop for signal X` notice were parked at
  `experiments/2026-08-15-change-rung1b-signal-contract/` PARKED.md P1 and
  landed at `experiments/2026-08-21-change-rung1b-ii-signal-consumption/`.
  Kept rather than deleted, per SCHEMA.md: a reader who finds this document at
  an older commit needs to know the gap was real and when it closed.
- **A producer predicate is easy to forget when adding a signal.** Adding a name
  to `POLICY_SIGNALS` without adding its `_PRODUCERS` entry raises `KeyError`
  inside `open_loop_signals` — loudly, on purpose. The pair is the declaration;
  half of it is not.
- **`manifest.roles` membership is not seat-boundness.** The compiler emits all
  eleven canonical role keys, and an unconfigured role's value is an EMPTY route
  tuple. Every producer predicate and every matrix assertion must read the
  routes, not the keys.
- **A dedicated workflow is deliberately absent.** The operator's tripwire: two
  recorded recipe failures first (the `authoring-skills` E1 rule). Two recipes,
  no skill.
`check: test -f docs/map/REC-add-signal.md && test -f docs/map/REC-revise-allocation-policy.md`
`check: ! test -d .claude/skills/dr-signals`
- **An in-envelope, in-dwell, fully logged allocation decision can still be
  illegal at the point of use.** The envelope bounds what the controller may
  PROPOSE; it says nothing about what the consumer of that knob will ACCEPT.
  `cap_envelope` anchors a seat's ceiling to `max(static_max, configured_cap)`,
  so a seat leased below the static maximum keeps a barrier wider than its own
  route — and its docstring's promise that the controller "can never move a cap
  past" the operator's setting was false for exactly those seats. Reach-rich
  epoch 2 (run `40e713b3…`) died on the mirror case: a lawful narrowing the
  route firewall refused. FIXED 2026-08-22
  (`experiments/2026-08-22-fix-route-lease-maxtokens/`) by bounding the
  controller at the seat's lease in `Controller._lease_ceiling`, applied in
  both `_propose` and `_apply_cap`. Deliberately NOT folded into
  `cap_envelope`: `invariants.py` re-derives that function to decide what a
  logged policy authorized, which is frozen surface 3, and the bound applied
  beside it is a subset of the envelope the validator re-derives, so no steered
  run can fail to verify. When adding a knob, ask what refuses it downstream —
  `DR-SEAM-llm-x-scheduler` is the worked case.
`check: grep -q "def _lease_ceiling" src/deepreason/controller.py && python -m pytest tests/test_route_lease_maxtokens_tuning.py::test_the_controller_never_calibrates_above_a_qualified_lease tests/test_route_lease_maxtokens_tuning.py::test_an_applied_policy_states_the_cap_the_seat_actually_got -q`