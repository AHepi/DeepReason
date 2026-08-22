<!-- DR-INV-signal-contract -->
Verified-at: 5e0d5bab
Verify: python -m pytest tests/test_signal_contract.py tests/test_allocation_signal_consumption.py -q
Owns: src/deepreason/signals.py, src/deepreason/allocation.py
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

## Where to change what

| To do this | Read | Test |
|---|---|---|
| add a signal | `REC-add-signal.md` | `tests/test_signal_contract.py` |
| revise the allocation policy | `REC-revise-allocation-policy.md` | `tests/test_controller.py` |
| retire a signal's `unspecified` marker | `REC-add-signal.md` §"paying down the debt" | the pinned census |
| key signals by seat instance | `REC-revise-allocation-policy.md`; the seat-instance section above | `tests/test_allocation_signal_consumption.py` |
| add a signal the POLICY reads | `REC-add-signal.md`, then `allocation.POLICY_SIGNALS` **and its producer predicate** | `tests/test_signal_contract.py` |

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