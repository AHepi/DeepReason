<!-- DR-INV-signal-contract -->
Verified-at: f39ff839
Verify: python -m pytest tests/test_signal_contract.py -q
Owns: src/deepreason/signals.py
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

Eighty-nine entries predate the contract. They carry their authors' prose as
`semantics` verbatim, and `unit`/`staleness` of `"unspecified"` — because
inventing a unit for a signal whose author never stated one would be fabrication
dressed as rigour. The census is pinned and may only shrink; a NEW signal
declared `unspecified` fails the gate.

`check: python -m pytest tests/test_signal_contract.py::test_the_migration_debt_can_only_shrink -q`

## Where to change what

| To do this | Read | Test |
|---|---|---|
| add a signal | `REC-add-signal.md` | `tests/test_signal_contract.py` |
| revise the allocation policy | `REC-revise-allocation-policy.md` | `tests/test_controller.py` |
| retire a signal's `unspecified` marker | `REC-add-signal.md` §"paying down the debt" | the pinned census |
| key signals by seat instance | **not yet built** — Rung 1b-ii | — |

## Traps

- **A consumer that needs to know the producer has left the contract.**
  `semantics` is producer-agnostic on purpose. The moment a consumer branches on
  which subsystem emitted a signal, the registry is a wiring again and the next
  setup will have to teach that consumer about itself.
- **`unspecified` is a marker, not a default.** It records that nobody stated a
  unit. Using it for a new signal converts an honest debt into a licence.
- **Rung 1b is only half-delivered by 1b-i.** Seat-instance keying, the compiled
  topology matrix, and the `allocation open-loop for signal X` notice are 1b-ii
  (`experiments/2026-08-15-change-rung1b-signal-contract/`). A reader who finds
  the contract without them should not conclude they were dropped.
- **A dedicated workflow is deliberately absent.** The operator's tripwire: two
  recorded recipe failures first (the `authoring-skills` E1 rule). Two recipes,
  no skill.
`check: test -f docs/map/REC-add-signal.md && test -f docs/map/REC-revise-allocation-policy.md`
`check: ! test -d .claude/skills/dr-signals`
