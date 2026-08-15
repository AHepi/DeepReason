# SPEC — Rung 1b-i: the signal contract, declaration side

Traces to REQUEST.md L1–L7. **Diff budget: 400 lines** across `src/`, `tests/`,
`docs/` (LADDER estimated 450–650 for all six clauses; this is three of them).

## S1 — the typed declaration (L1, L2)

`src/deepreason/signals.py` gains `SignalDeclaration`, a frozen record with the
operator's four fields:

| field | meaning |
|---|---|
| `name` | the measure tag as it appears in `event.inputs[0]` |
| `unit` | what one occurrence counts as, from a closed vocabulary |
| `semantics` | producer-agnostic meaning — what it means, never who emits it |
| `staleness` | how long an observation of it remains usable |

`unit` and `staleness` are closed `Literal`s including an explicit
`"unspecified"` member. **No unit or staleness is invented for an existing
signal.** The 74 `SIGNALS` and 15 `PREFIXES` entries migrate with their prose
becoming `semantics` verbatim and both new fields set to `"unspecified"` — an
honest debt marker, not a fabrication.

`SIGNALS` and `PREFIXES` keep their names, types and contents, DERIVED from the
declarations (`{name: d.semantics}`), so every existing consumer
(`report.py`, `cli/main.py`, `tests/test_signals.py`) is untouched and one
source of truth replaces two.

## S2 — the contract is enforced, and the debt can only shrink (L1)

New tests:

1. every declaration carries all four fields, non-empty;
2. `SIGNALS`/`PREFIXES` are exactly the declarations' semantics — the derived
   view cannot drift from its source;
3. **the unspecified census is pinned at its current value and may only go
   down.** A NEW signal declared `unspecified` fails the gate: that is what makes
   this a contract for new setups (the operator's clause 1) while leaving the
   migrated ones honestly marked;
4. the closed vocabularies reject an unknown unit or staleness.

## S3 — interface-only consumption (L3)

An architecture test asserting `controller.py` imports no schools / rules /
criticism internals. It **passes on the tree as it stands** —
`controller.py`'s only `deepreason` import is `deepreason.ontology` — so its
value is that it fails the day the boundary is breached. Recorded as such in
the INV document rather than presented as a fix.

**Not in this tranche:** migrating the controller's three direct
`harness.state.status.get(...)` reads into declared signals. That is
consumption-side work and belongs with SC-2's seat keying in 1b-ii; doing it
here would change what the controller reads without the keying that makes the
reads meaningful. Recorded in PARKED.md.

## S4 — the governing documents (L4, L5, L6)

- `docs/map/INV-signal-contract.md` (`DR-INV-signal-contract`): the three
  layers — FROZEN change protocol, VERSIONED registry and policy algorithm,
  FREE parameter values within envelopes — each with checks that can fail.
- `docs/map/REC-add-signal.md`: the recipe for adding a signal by declaration.
- `docs/map/REC-revise-allocation-policy.md`: the recipe for revising the policy
  algorithm, including that policy is a recorded artifact and referee-reviewed.
- **No skill, no workflow** (L5).

## Acceptance checks

| # | L | Check |
|---|---|---|
| A1 | L1 | every declaration has four non-empty fields |
| A2 | L2 | `SIGNALS`/`PREFIXES` unchanged in content; existing consumers untouched |
| A3 | L1 | the unspecified census is pinned; a new unspecified signal fails |
| A4 | L3 | the architecture test exists and passes |
| A5 | L4 | `docs_verify` full — no new failure beyond the recorded baseline; `--links` resolves the three new ids |
| A6 | L5 | `.claude/` untouched |
| A7 | L7 | `blast_radius` CLEAR; root sweep unchanged |
| A8 | all | full gate, 0 failed |

## Predicted fixture updates

**None.** `SIGNALS` and `PREFIXES` keep identical content, so
`tests/test_signals.py` should pass unmodified. If any assertion there moves,
that is a stop, not a fixture update — it would mean the derived view drifted.
