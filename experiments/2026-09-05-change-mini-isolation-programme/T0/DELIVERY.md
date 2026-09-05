# Delivered: T0 — the prerequisites (S0a, S0b)
Sub-tranche T0 of the mini isolation programme.
Branch: `claude/mini-isolation-t0-t2-upwc47` @ `16787862b` (pushed, tree clean).
Base: `1f8108c00a`. Validation: `T0/VALIDATION.md`, verdict PASS.

## What changed

Two roads that the design measured as DEAD now exist, and both are proven by
tests rather than asserted.

**A plugin the operator writes is read by a run.** `load_operator_plugins`
had no call site anywhere under `src/`, so `<DEEPREASON_HOME>/seat_plugins/`
was a documented place to put a file that nothing ever opened. The managed
shallow entry (`src/deepreason/shallow.py`) now calls it once during setup,
before the first call — a plugin registered after a brief was rendered would
be a section the run claims it had and did not. Both of the loader's lists
reach the run's record: what loaded, and why the rest did not. They are
written to `seat-plugins.json` in the run root under a schema id and returned
in the result payload. Dropping the second list would leave the operator
looking at a brief missing a section with no reason given, which is the
failure the loader exists to prevent.

**A brief's composition can be declared in a file.**
`register_seat_pack_layout` was reachable only from Python, so step 3 of the
add-a-section recipe — "register a layout that includes it" — had no road that
did not edit the tree. `register_seat_pack_layout_file` in
`src/deepreason/llm/seat_sections.py` reads a `<name>.layout.json` from the
same operator directory, carrying the layout's own `layout_id`, its
`entries`, and an optional `default_for_seat`. Every failure raises one coded
refusal naming the file and registers nothing; read by a run's loader, that
refusal becomes a typed notice carrying its own code and the run continues on
what did load. The third possibility — a brief silently composed from the
seat's default while the operator's file sits unread — is the one this forbids.

Nothing in the full harness changes behaviour. The two existing seats' briefs
are byte-identical (`tests/test_conj_pack_legacy_golden.py`,
`tests/test_crit_pack_legacy_golden.py`: 15 passed), no frozen surface is
touched (the diff over all five is empty, and `blast_radius.py` returned
`CLEAR` at every commit), and the full gate is 5077 passed, 0 failed.

## Reconciliation

T0 is the first of eight sub-tranches; most requirements are owned by later
ones and say so. Nothing is marked done that is not proven.

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "mini needs to be tested in isolation" | owned by T1 (S1) | — |
| R2 | "not limit prose length at all" | owned by T2 (S2) | — |
| R3 | "cycles with commitments disabled" | owned by T2 (S3) | — |
| R4 | "a new kind of artifact that generates commitments" | owned by T4 (S4) | — |
| R5 | "critics see the conjecture artifact, not the proposed commitments" | owned by T3 (S5) | — |
| R6 | "conjecturers see everything generated so far" | owned by T3 (S5) | — |
| R7 | "all three seats … the same pluggable interface with relaxed forms" | prerequisites **done**; the shells are T3 (S6) | commits `3276a70ff`, `db5cc16ff`; VALIDATION S0a/S0b |
| R8 | "Don't change the controller just yet" | **honoured** | no hook declared, no controller called anywhere in T0 |
| R9 | "the mini flow … adjustable in a pluggable way" | file-declared half **done**; the flow is T5 (S8) | commit `db5cc16ff`; VALIDATION S0b |
| R10 | "add new artifact types on the fly" | file-declared half **done**; the rest is T5 (S8) | commit `db5cc16ff`; VALIDATION S0b |
| R11 | "test this new config in isolation" | owned by T1 (S1) | — |
| R12 | "starting input should be standard" | owned by T1 (S1) | — |
| R13 (Amendment 1) | "within mini, criticism can't overturn anything" | **honoured** | T0 builds no elimination road of any kind |
| R14 (Amendment 1) | "the point is content generation for now" | **honoured** | T0 changes no authority path |
| R-stored | "the current default conjecture form needs stored but not deleted" | owned by T2 (S2) | nothing in T0 touches any form |
| R-again | "the episodes … need to be tested again" | deferred | window: "episodes (R-again, later)" |
| R-history | "One more history conjecture experiment" | deferred | operator: "But before that:" |

## Assumptions the operator may override

None is decided by T0; all are carried from SPEC.md and listed in
`T0/VALIDATION.md`. One is worth flagging early:

**A6 — "the larger harness" is the eleven modules SPEC.md §S1 names.** While
preparing T1 this was measured and found to need amending: four of those
eleven packages are already loaded by modules S1 explicitly ALLOWS (the event
ontology imports `bridge.events` and `capabilities.enums`; the harness
imports `adjudication.edges`). The fence T1 builds will therefore say what it
can honestly say — that mini adds nothing beyond that — and the measurement
will be recorded there. T0 does not depend on it.

## Map delta

changed: `docs/map/REC-add-a-section-plugin.md` (steps 2, 3 and 4 are now
true end to end, each with its own check), `docs/map/SUB-application.md`
(the shallow path's plugin loading), `docs/map/SUB-llm.md` (the
file-declared layout road).
created: none — `SUB-minireason.md` is T1's (step 12).
new checks: 5, each mutation-proven before being written down.
left stale: 23 documents, none of them this tranche's — every one names
commits that pre-date the base and belongs to a subsystem T0 did not touch.
Advancing a stamp whose checks this tranche did not re-run would be a false
stamp, so they are left honest.

## Errata

errata: none. No committed document was found to state something false. The
two subsystem documents this tranche updated were INCOMPLETE about new
behaviour, not wrong about old, which the map's own `--stale` channel covers.

## Parked (not done, not promised)

No NEW parked item was found in T0. The programme's `PARKED.md` already
carries six from the design phase (P1–P6), unchanged. Two of them were
touched by T0's evidence and are worth restating:

- **P1 — mini's 95 tests are outside the gate every tranche runs.** Confirmed
  again here: `pytest tests/ -q -n 4` reported 5077 passed while mini's 95
  ran only because this tranche ran them by hand. Its ready-to-send prompt is
  in `PARKED.md`.
- **P6 — nothing says where `mini/` is documented.** T1 step 12 closes it by
  creating `SUB-minireason.md`.

**recommended next: T1 (steps 10–15).** It is the next sub-tranche in the
programme's own order, it closes P6, and its first step has already surfaced
a measurement that will amend SPEC.md's assumption A6 — better done inside T1,
where the fence is built, than carried further.
