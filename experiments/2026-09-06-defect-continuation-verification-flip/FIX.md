# Fix proposal: give a semantically-rejected wire-valid reply the category the record already has

**STOPPED FOR AN OPERATOR GRANT.** The cause is inside
`src/deepreason/invariants.py`, which is frozen surface 3
(`docs/map/INV-frozen-surfaces.md`). Nothing is implemented. This document
prices the roads, pastes the disclosure gate's own computed contact list, and
asks for the grant.

## What the fix would change, in one sentence

`_controller_v3_history` routes EVERY non-admitted semantic admission to
`FAILURE_REQUIRED`, whose rule forbids a wire-valid attempt, except for one
narrow patch-repair case; the fix widens that exception to what the record
actually distinguishes — a reply that PARSED and was then refused on its
semantics is a `SEMANTIC_REJECTION`, which already permits "at most one final
wire-valid attempt", whoever produced it.

## Frozen-surface contact forecast — `tools/blast_radius.py`, pasted verbatim

    frozen_surface_verdict: CONTACT
    frozen_surface_contacts: [
     {"surface": "replay-validation record formats (invariants.py)",
      "tier": "DIRECT", "target": "src/deepreason/invariants.py",
      "detail": "target file is surface path src/deepreason/invariants.py"},
     {"surface": "replay-validation record formats (invariants.py)",
      "tier": "SYMBOL_INDIRECT", "target": "_controller_v3_history",
      "detail": "'_controller_v3_history' referenced in src/deepreason/invariants.py (grep-based; not proof of semantic contact)"},
     {"surface": "replay-validation record formats (invariants.py)",
      "tier": "SYMBOL_INDIRECT", "target": "_expected_call_outcome",
      "detail": "'_expected_call_outcome' referenced in src/deepreason/invariants.py (grep-based; not proof of semantic contact)"}
    ]
    frozen_adjacent_contacts: []
    reachability: _controller_v3_history REACHABLE; _expected_call_outcome REACHABLE

Disposed row by row: the DIRECT row is the grant being asked for. Both
SYMBOL_INDIRECT rows are the same file's own functions and are the site of the
change, not separate contacts. `frozen_adjacent_contacts` is empty —
`route_fingerprint` is untouched, no `Route` field moves. No record FORMAT
changes: no new field, no new check name, no `_EPISTEMIC_CHECKS` entry, no
`report.py` channel. `verification/` is not touched at all.

## The impact, measured across every committed root

Census over the 90 committed roots carrying a run manifest (77 readable by
this classifier; the root sweep is retired, so this is the targeted instrument
the 2026-08-25 grant's precedent calls for):

**Exactly four calls, in two roots, are classified `FAILURE` while carrying a
wire-valid attempt** — the whole population the fix can move:

| root | seq | admission | terminal reason | today |
|---|---|---|---|---|
| `…organiser-testing/runs/home-r/runs/run-c3f3bf10bc57d63e224a9f1c68bf1057` | 142, 215, 295 | `schema_exhausted` | `recovered_schema_exhausted` | 3 violations |
| `…2026-08-04-change-rung5-dumb-alternative-backend/rr-home/runs/run-9a6be78e1e79184a0bd89923b957586c` | 17 | `rejected` | `simulation_semantic_rejected` | 1 violation, **stored invalid since 2026-08-04** |

Two facts this census settles. First, **the defect predates the continuation
by a month**: a committed root from 2026-08-04 carries the same violation over
a simulation proposal that was wire-valid and semantically rejected, and its
stored `REPLAY_VALIDATION.json` has said `valid: false` ever since. ARM R did
not create this; it produced a second instance in a way that made two verdicts
collide visibly. Second, **no currently-clean root can become dirty**:
`SEMANTIC_REJECTION` accepts `valid_indexes in ([], [len(trace)-1])` while
`FAILURE_REQUIRED` accepts only `[]`, so the widened route is a strict superset
— every record accepted today is accepted after.

## The roads

**A — widen the semantic-rejection route to any wire-valid non-admission (RECOMMENDED).**
In `_controller_v3_history`, when the admission exists and is not `admitted`,
route to `semantic_rejection_call_seqs` if the call's attempt trace ends in a
wire-valid attempt; otherwise `failure_call_seqs`. The existing
`_is_patch_repair_semantic_rejection` becomes a subset of the new predicate
and is removed or folded in. Transport failures are untouched (they are
tested first and carry no valid attempt anyway), and the existing precedence
— a seq required to fail by a proposal receipt or the legacy chain stays
`FAILURE_REQUIRED` — is preserved, because that filter runs afterwards.
~10 changed lines in one file. Fixes all four calls. Both roots go clean.

**Its cost, stated plainly:** the check loses one tripwire. Today, a record
claiming that a wire-valid reply was semantically rejected is refused; after,
it is accepted as an ordinary semantic rejection. That is a real weakening,
and it is the price of the check agreeing with the writer: the harness itself
produces exactly that record on two legitimate paths (a recovered closure, a
rejected simulation proposal). A forger able to append admission records can
already do worse, and `attempt-validity`'s stated job is that the attempt
trace agrees with the call's outcome — not that non-admissions are rare.

**B — recognise only the RECOVERED closure.** Route to the permissive shape
only when the work terminal's `reason_code` starts with `recovered_`. ~8 lines,
same file, same grant. Fixes ARM R's three and keeps the tripwire everywhere
else — but leaves the 2026-08-04 root condemned for a call of the same class,
which means the check would still be wrong about a legitimate record, and this
tranche would have decided that the second instance does not count. Cheaper to
argue, harder to defend.

**C — change nothing in the check; declare the pre-continuation verdict
authoritative.** Rejected on the record: it makes an honestly-completed record
verify WORSE than an abandoned one, and it would leave both committed roots
invalid over legitimate content.

**D — change the writer instead.** Rejected: the writer is right. The closure
references an existing recovery authority, uses the canonical record shape,
and passes every other replay rule. There is nothing to fix there.

## What the fix does NOT address, and why it is parked rather than folded in

**An open work order does not affect the verdict.** The before-root reports
`valid: true` while its own stats list three outstanding work orders. That is
the second half of P9's question and it is a POLICY question, not a defect
against a documented guarantee: making an unterminated work order invalidate a
record would condemn every operationally-failed root ever committed, and the
operator's 2026-08-29 law is about integrity-gating CONTINUATION, not about
what `valid` means. Parked as P1 with its own prompt; the continuation gate's
thin integrity half (it reads lifecycle decisions only, and `continue` refuses
on SECURITY findings while `attempt-validity` is INTEGRITY) is parked with it.

## What implementation would deliver, if the grant is given

1. `tests/test_attempt_validity_semantic_rejection.py` — the stub of REPRO.md
   promoted to a regression: three states of one canonical root (admitted,
   abandoned, closed), asserting the closed root verifies clean AFTER the fix
   and that the abandoned and closed verdicts AGREE. Red on the unfixed tree.
2. The mutation proof, in the same file: a call whose trace has NO valid
   attempt and a non-admitted admission must still fail `attempt-validity`
   (the check must not go blind); and a call whose valid attempt is not final
   must still fail.
3. A probe against the two committed roots above, pinning the verdicts the
   fix predicts and no others.
4. The map moves in the same commit: `DR-SEAM-llm-x-verification` gains the
   agreement this defect broke (what a non-admitted admission means about the
   attempt trace) with a `check:`, and a `Traps` entry naming
   `run-c3f3bf10bc57d63e224a9f1c68bf1057`; `INV-frozen-surfaces.md` records the
   granted contact.
5. The full gate once at the boundary.

## The grant being asked for

Contact with frozen surface 3, `src/deepreason/invariants.py` only:
`_controller_v3_history`'s classification branch (and the removal or folding of
`_is_patch_repair_semantic_rejection`). No record format, no check name, no new
finding, no `verification/` file, no digest input. Insertions and one modified
branch, ~10 lines. The safety argument is the census above: four calls in two
roots, both already reporting violations, and a strictly-more-permissive
predicate so nothing currently clean can move.

## Grant — given 2026-09-09

The monitor put road A to the operator with its price stated. The sentence the
operator answered, verbatim:

> Road A is recommended … This is your decision.

The operator's answer, verbatim, 2026-09-09:

> do it

Scope of what was granted, as this document asked for it above: contact with
frozen surface 3, `src/deepreason/invariants.py` ONLY — the classification
branch inside `_controller_v3_history`, and the folding of
`_is_patch_repair_semantic_rejection` into the widened predicate. No record
format, no new field, no new check name, no `_EPISTEMIC_CHECKS` entry, no
`verification/` file, no digest input. Transport failures and the
proposal-receipt / legacy-chain precedence stay exactly as they are.

Ledgered in `docs/map/INV-frozen-surfaces.md` under surface 3 as
**Granted contact, 2026-09-09**, in the same commit as the code, per the
documented recipe.
