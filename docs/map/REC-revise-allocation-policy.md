<!-- DR-REC-revise-allocation-policy -->
Verified-at: 9d60e2ae
Verify: python -m pytest tests/test_controller.py -q
Owns: 
Seams: 
Seams-undocumented: 

# Recipe — revise the allocation policy

The policy algorithm is the VERSIONED layer (`DR-INV-signal-contract`). It may
change; the protocol for changing it may not.

## Before you start

Read `docs/ERRATA.md` E28 first. The controller was believed to steer real runs
for months on the strength of an A/B that fixed the one parameter gating the
mechanism: **zero of the 104 committed logs in `experiments/` contain a
controller policy body at all.** Any claim that a policy revision improves
anything must state the configuration it was measured under, in the sentence
that reports the result.

## The steps

1. **State the signals the new policy reads**, by name, before writing it. If a
   signal you need does not exist, `REC-add-signal.md` first — do not read
   around the interface. Name them by SEAT INSTANCE where the policy throttles
   per seat: `allocation.seat_instance` spells a single-seat role as the bare
   role name and a multi-seat one as `role#seat`, and
   `allocation.route_cap_for_knob` is the ONE derivation of a seat's assigned
   ceiling that the writer and replay validation must share.
2. **Write the policy as a recorded artifact.** `controller.py::_policy_payload`
   already reads the policy from a registered artifact; a policy that lives only
   in code is a policy nobody can attack, which is a status privilege by another
   name (calculus P6).
3. **Keep every parameter inside its envelope.** `cap_envelope`/`clamp` are the
   FREE layer's bounds. Moving a value inside its envelope needs no ceremony;
   moving the envelope is a VERSIONED change.
4. **Have the referee review it.** `config_referee` (spec v1.7 §F) is the
   argumentative critic whose only target is run configuration. It is opt-in and
   suspect-by-default like any judge seat — consult the judge-audit evidence in
   the committed record before leaning on its verdict.
5. **Record the decision**, typed: what changed, which signals it reads, what it
   was measured under.
6. **Run** `python -m pytest tests/test_controller.py tests/test_signal_contract.py -q`.

`check: grep -q "def cap_envelope" src/deepreason/controller.py && grep -q "def clamp" src/deepreason/controller.py`
`check: grep -q "_policy_payload" src/deepreason/controller.py`

## Two policy families now, and the recipe covers both

`controller.py` steers per-seat COMPLETION CAPS from process signals.
`wander.py` steers ATTENTION between problem lineages from the scheduler's own
selection counts. They share this recipe, the three layers, and the
efficiency-never-evidence row; they share no code.

The second family adds one step to step 1: a lineage policy is REGISTERED in
`wander.LINEAGE_POLICIES` under its own versioned id and selected by
`Config.ATTENTION_ALLOCATION_POLICY`. A new throttle is a registry entry, never
an edit to the scheduler — and the check that this stays true is in
`DR-INV-signal-contract` ("the consumer reads the interface and nothing else").

`check: python -c "
from deepreason import wander
assert set(wander.LINEAGE_POLICIES) >= {'wander-cap.v1', 'open-lineage.v1'}
assert wander.DEFAULT_POLICY_ID in wander.LINEAGE_POLICIES
from deepreason.config import Config
assert Config().ATTENTION_ALLOCATION_POLICY in wander.LINEAGE_POLICIES
"`

**Step 5 has teeth now.** "Record the decision, typed" used to be the weakest
step here, because E28's warning — the controller was believed to steer for
months and zero committed logs contained a policy body — had no counterpart
check. It does now: every name in `allocation.POLICY_SIGNALS` must appear at an
emit site in `src/`, tested rather than audited, so a policy that reads a
reading the record never carries fails the gate.

`check: python -m pytest tests/test_wander_cap.py -q -k emit_site`

## What this recipe may NOT do

- It may not let allocation touch a status. Efficiency, never evidence.
- It may not make a topology's missing signal fatal: a topology that cannot
  produce a signal COMPILES, carrying a typed open-loop notice (the operator's
  clause 5). Landed 2026-08-21 — `allocation.open_loop_signals` /
  `open_loop_notices`, and the `open_loop` list on the `controller-authority`
  record. A new policy that reads a signal must add it to
  `allocation.POLICY_SIGNALS` **together with its producer predicate**, or the
  census cannot answer for it.
- It may not import a subsystem into `controller.py` to obtain a number.

## If this recipe fails you

Record it in PARKED.md naming this file. Two recorded failures, then a workflow.
