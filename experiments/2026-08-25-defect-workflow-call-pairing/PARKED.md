# PARKED — noticed by this tranche, deliberately not done here

One tranche, one goal (CLAUDE.md). Each entry is written for its future runner: what, then a
ready-to-send prompt.

---

## P3 — the schema-repair ladder still has no offline witness

**What.** `scripts/cycle_soak.py --induce-repairs N` reaches the repair ladder by making the
stub's transport fail (four HTTP 500s), so what it exercises end-to-end is the
`outcome="transport_failure"` path — the one this tranche fixed. The soak does report
`attempts.repairs == 1`, so a repair transaction is prepared and terminalized; but the SEMANTIC
repair shape — the provider answers, the body is well-formed at the transport level and invalid
against the wire schema, `SchemaRepairError` is raised, and `repair_schema_failure` dispatches a
separately authorized patch turn that succeeds — is never driven to a recorded provider result
offline. The `attempt != 0` clamp, the `repair.semantic-task.v1` payload and the
`diagnostic_ref`-points-at-the-NEXT-turn trap (`DR-SEAM-llm-x-workflow` Traps) are all on that
path, and all of them are held today by unit fixtures that pin `retry_max=0`, which the seam
document itself records as hiding the clamp.

**Why it is a gap rather than a defect.** Nothing is known to be broken here. The point is that
if something were, the soak would not show it — exactly the situation that made P1 invisible
until `--induce-repairs` existed. Live roots do exercise it (the reach-rich epoch-1 root has 13
on-target repair turns), so this is about cheap offline coverage, not about correctness.

### Ready-to-send prompt

```
Route: dr-change-orchestrator (capability gap, not a defect).
One goal: give scripts/cycle_soak.py a SEMANTIC repair inducer, so the schema-repair
ladder is driven to a recorded provider result offline the way --induce-repairs
already drives the transport-failure ladder.

Today --induce-repairs makes the stub fail TRANSPORT (four HTTP 500s), which reaches
outcome="transport_failure".  What is missing is the shape where the provider ANSWERS
and the body is invalid against the wire schema: SchemaRepairError ->
workflow/repair_transaction.py::repair_schema_failure -> a separately authorized patch
turn that succeeds.

Read first, in order:
  - experiments/2026-08-25-defect-workflow-call-pairing/VERIFY.md (Residue) — why the
    existing inducer does not cover this
  - docs/map/SEAM-llm-x-workflow.md Traps — three traps live on this path, and one of
    them records that every v6 repair fixture pins retry_max=0, so deleting the
    one-bundle-one-request clamp "leaves the whole repair suite green"
  - scripts/cycle_soak.py, install_repair_inducer
  - experiments/2026-08-22-fix-repair-patch-transport/repair_turn_census.py — the
    census that reads a repair turn's real authority (join provider_attempt.work_id ->
    preparation.id), because a repair attempt's own diagnostic_ref points at the NEXT
    turn's diagnostic and reading it naively scores every converging repair as off-target

End state: a soak flag that reaches a recorded semantic repair, a named assertion for
it beside the four already in S1, and a docs/AUDIT_BASELINES.md row saying what it
exits.  If it turns out the ladder cannot be reached offline without teaching the stub
something a real provider would not do, that is a recorded negative result, not a
failure — say so and stop.
```

---

## Not parked, recorded so nobody re-opens them

- **P1 and P2 of `experiments/2026-08-23-change-cycle-soak-instrument/PARKED.md` are both
  CLOSED.** P1 is this tranche (with its framing corrected at `docs/ERRATA.md` E53). P2's fix
  landed as `experiments/2026-08-23-fix-reservation-bound-authority/` and its outstanding
  `EXPECTED_RED` deletion was carried out here (`docs/ERRATA.md` E54). Both files carry a
  resolution line.
- **The adapter's `attempt != 0` repair clamp was investigated and is SOUND.** GOAL.md put it
  out of scope and the record then exonerated it: the failing event was `attempt: 0`. It has no
  hole. Do not re-open it on the strength of P1's original wording.
- **21 `foreign-criticism` and 1 `attempt-validity` violations stand on committed roots.** They
  predate this tranche, are unchanged by it, and belong to whoever owns those checks.
