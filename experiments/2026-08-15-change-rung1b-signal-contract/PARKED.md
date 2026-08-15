# Parked — Rung 1b-i

## P1 — Rung 1b-ii: the consumption side of the signal contract

**What.** Three of the operator's six clauses are not built yet: SC-2
(signals keyed by SEAT INSTANCE, not role — "multiple structurally asymmetric
seats that may need throttling independently"), SC-4 (the compiled topology
matrix: solo, no-schools, judges-off, legacy-on each compile, the controller
attaches, every policy-referenced signal has a producer), and SC-5 (a topology
that cannot produce a signal compiles with a typed `allocation open-loop for
signal X` notice — disclose, never die).

Also deferred with them: migrating `controller.py`'s three direct
`harness.state.status.get(...)` reads into declared signals. They are the last
place the controller reads graph state other than through the interface, and
they belong with the keying that makes the reads meaningful.

**Why parked.** Scope split argued in REQUEST.md §3: 1b-i is the declaration
side (what a signal IS and who may read it), 1b-ii is the consumption side
(what the allocation controller DOES with them). The declaration side is what
the rest of the v2 program depends on, so it went first.

### Ready-to-send prompt

```
Rung 1b-ii of the v2 calculus program: the consumption side of the signal
contract. Route through dr-change-orchestrator.

AUTHORITY: the operator's six-clause design, ledgered verbatim at
experiments/2026-08-14-change-calculus-reconciliation-v2/REQUEST.md
Amendment 2 (R29-R36), and now a standing law in CLAUDE.md. Clauses (1),
(3) and (6) landed in Rung 1b-i
(experiments/2026-08-15-change-rung1b-signal-contract/). This tranche is
clauses (2), (4), (5).

READ FIRST: docs/map/INV-signal-contract.md and both REC recipes; then
src/deepreason/controller.py (cap_envelope/clamp are the FREE layer,
_policy_payload already reads policy from a registered artifact);
docs/ERRATA.md E28 (the controller has never once steered a real run --
zero of 104 committed logs contain a policy body).

SCOPE:
(2) key signals by SEAT INSTANCE. Seat identity is already in the record:
    seat-bindings.v1 (spec v1.7 A) carries resolved group ->
    provider/model/profile-digest into the log. Do NOT add a role.
(4) a compiled matrix test over configuration classes: solo, no-schools,
    judges-off, legacy-on. Each compiles, the controller attaches, every
    policy-referenced signal has a producer.
(5) a topology that cannot produce a signal COMPILES, carrying a typed
    "allocation open-loop for signal X" notice. Extend the
    controller-authority record the E28 fix established.
Plus: migrate controller.py's three harness.state.status.get(...) reads
into declared signals, paying down part of the 89-entry unspecified debt
as you go (lower MIGRATION_DEBT by exactly what you fix).

HARD CONSTRAINTS: allocation touches EFFICIENCY, NEVER EVIDENCE -- no
signal and no allocation decision may reach a label. Adding no new LLM
role keeps qualification subject digests still. Disclose, never die: a
missing producer is a notice, not a refusal (the all-configurations law).

NOT OWED: any cross-version proof. The 2026-08-14 law retired
replay-byte-unchanged obligations and old-root sweeps as gate
obligations; within-version integrity is untouched.

GATE: full gate 0 failed, docs_verify full, map moves in the same commit.
Commit and push at every phase boundary.
```
