# Delivered: Rung 1b-ii — the consumption side of the signal contract

Branch: `claude/calculus-rung1b-ii-signal-consumption-n6mond` (pushed, tree clean)
VALIDATION.md round 2: **PASS**. Round 1's FAIL and its evidence are kept above
it rather than rewritten.

## What changed

The allocation controller now throttles **seat instances**, not roles. A new
module, `src/deepreason/allocation.py`, owns the whole interface the controller
is allowed to read: how a seat instance is named, the one derivation of "what
cap did this run assign this seat", the set of signals the policy reads with a
producer predicate for each, and the two policy-status readers. `controller.py`
keys every signal window, envelope, dwell counter and cap on the seat instance,
and `_apply_cap` writes one seat's endpoint rather than the role's whole
ensemble — which is exactly what used to make two structurally asymmetric seats
share a single throttle. Seat identity came from `LLMAttempt.seat`, already on
every attempt in the record; no role was added and no field was written, so no
qualification battery was disturbed.

A role bound to ONE seat keeps the bare role name. That is not an exception to
seat keying — it is what seat keying spells for an ensemble of one — and it is
why 26 existing controller tests passed unchanged, with no assertion weakened
and no fixture edited.

Four signals were declared under the contract with real units and staleness
bounds, and five entries of the pre-contract migration debt were paid down
(89 → 84) with their semantics prose left byte-identical. The controller's three
direct `harness.state.status.get(...)` reads are gone: `controller.py` no longer
names `Status` at all, so the spelling of contestation lives in exactly one
place.

A topology that cannot produce a policy-referenced signal now **compiles and
says so**. Binding no `argumentative_critic` means nothing can ever attack a
controller policy, so fail-static can never fire — that run still steers, and
carries a typed `ALLOCATION_OPEN_LOOP` notice plus an `open_loop` list on the
`controller-authority` record. Disclose, never die.

Finally, one granted 12-line reader fix in `src/deepreason/invariants.py`:
per-seat cap knobs now anchor to their own seat's route instead of missing the
role lookup and falling back to an unanchored `[500, 2500]` default that refused
limits the route itself authorised.

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "key signals by SEAT INSTANCE" | done | `f42429de1`; VALIDATION S1, S2 |
| R2 | "two structurally asymmetric seats ... must throttle independently" | done | `9d60e2ae3`; VALIDATION S1 — the two seats move in OPPOSITE directions in one cycle |
| R3 | "Do NOT add a role" | done | `9d60e2ae3`; VALIDATION S2, S3 — subject digest `d47cb2bf…88dc` unmoved, `compile_notices is None` |
| R4 | "a compiled matrix test over configuration classes" | done-with-assumption A3 | `9d60e2ae3`; VALIDATION S5 — 4 parametrised cases |
| R5 | "a topology that cannot produce a signal COMPILES, carrying a typed notice" | done-with-assumption A2 | `9d60e2ae3`; VALIDATION S6 |
| R6 | "Extend the controller-authority record the E28 fix established" | done | `f42429de1`; VALIDATION S6 — `open_loop` key asserted |
| R7 | "Disclose, never die ... CompileNoticeV1 ... reuse it" | done | `aa4e60202`; type imported unmodified, `run_manifest.py` untouched |
| R8 | "migrate controller.py's three harness.state.status.get(...) reads" | done-with-assumption A4 | `f42429de1`; VALIDATION S4 — `grep -c` → 0 |
| R9 | "lower MIGRATION_DEBT by exactly what you fix" | done-with-assumption A5 | `aa4e60202`; VALIDATION S7 — 89→84, `proof/s7_registry_diff.txt` |
| R10 | "allocation touches EFFICIENCY, NEVER EVIDENCE ... a test proves it" | done | `9d60e2ae3`; VALIDATION S8 — differential + ledger + architecture |
| R11 | "MUTATION PROOF ... paste both runs" | done | `proof/s8_mutation.txt` — repo 3 passed; mutation A 1 failed; mutation B 1 failed |
| R12 | "Map moves in the same commits" | done | `8c4e3e450` (reader fix + `INV-frozen-surfaces.md`), `2ba885078`, `1c2ea7289` |
| R13 | "Deliver R-by-R with pasted PROOF" | done | this document |
| R14 | "GRANTED: the 12-line reader fix" | done | `8c4e3e450`; 6 executable lines added, 7 removed, net −1 |
| R15 | "READER-ONLY, PROVEN NOT ASSERTED ... Paste the before/after" | done | 107-root diff EMPTY, rc=0 (`proof/sweep_proof.txt`) + `proof/s11_targeted_census.txt` |
| R16 | "MUTATION-PROVEN REGRESSION ... Run it RED on the unfixed tree first" | done | `proof/s12_red.txt` (1 failed, `attempt-limits`), `proof/s12_green.txt` (2 passed) |
| R17 | "the grant lives in SPEC.md ... note it granted with this date" | done | SPEC.md, "GRANTED 2026-08-21" |
| R18 | "the map ... gains a line naming this contact" | done | `8c4e3e450` — `INV-frozen-surfaces.md`, same commit as the fix |
| R19 | "the run_manifest.py false alarm is rowed ... with that file untouched" | done | `git diff --name-only origin/main..HEAD \| grep -c run_manifest.py` → 0 |
| R20 | "grep is not semantic proof ... proceed on the same standard" | done | SPEC.md M3; `proof/s11_targeted_census.txt`; ERRATA E38 |
| R21 | "root sweep needs removal" | **PARTIAL, by design — see below** | REQUEST.md Amendment 2; PARKED.md P4 |
| C1 | "No existing signal name changes spelling" | held | `proof/s7_registry_diff.txt` — 0 removed, 0 prose moved; 26 controller tests unchanged |
| C5 | "if you find yourself editing a file that rung owns, STOP" | held | Rung 3b merged at `5780a9298` before this branch began; its delivery touched no `src/` file |

**R21 is the one row that is not `done`, and the reason is routing, not
reluctance.** "Root sweep needs removal" arrived mid-tranche and is a different
goal: measured blast radius is **50 live references** across `tools/root_sweep.py`,
`CLAUDE.md`, four skills, nine map documents, `docs/AUDIT_BASELINES.md`, the
v1.7 amendment, three proposals and one test. One tranche, one goal, is repo
law. What this tranche did do is handle the single place R21 collided with work
in flight: `SUB-verification.md`'s anchoring trap MANDATED the sweep, and step
32 was editing that exact trap — writing the mandate forward would have shipped
a document contradicting a standing instruction. It is replaced by the census.
Everything else is P4, one paste away.

## Assumptions the operator may override

- **A1** — knob names are not registry signal names, so C1 does not bind their
  spelling; the design leaves every single-seat topology spelled as today anyway.
- **A2** — "producer" is decided from the bound roles alone. Override by naming
  further topology inputs (engine profile, control-plane mode) as conditions.
- **A3** — the four configuration classes resolve to `single_model`,
  `SCHOOL_SEATS_ENABLED=False`, `JUDGE_SEATS_ENABLED=False`,
  `LEGACY_CRITICISM_ENABLED=True`.
- **A4** — the controller stops reading `harness.state` for status entirely,
  rather than keeping the read behind a named accessor.
- **A5** — five debt entries fixed: the four controller signals plus
  `dropped-call`. Override by naming more.
- **A6** — R37–R41 (attribution-priority policy) are NOT delivered here despite
  the program's Amendment 3 table landing them "at Rung 1b-ii"; this tranche's
  message scoped the window to clauses (2), (4), (5) plus the debt.

## Map delta

    changed: INV-signal-contract.md (+125), INV-frozen-surfaces.md,
             REC-add-signal.md, REC-revise-allocation-policy.md,
             SUB-scheduler.md, SUB-verification.md
    created: none
    new checks: 12 — 7 in INV-signal-contract.md, 2 in REC-add-signal.md,
             3 in INV-frozen-surfaces.md; each run individually, rc=0,
             before any Verified-at: was advanced
    left stale: CON-run-identity.md, CON-schools.md, SEAM-manifest-x-schools.md
             (all → bce018ae5, all-configs-allowed), SUB-calculus.md
             (→ Rung 3b), SUB-evidence.md (→ three-layer citable evidence).
             All five pre-existing; none names a file this tranche touched.

`INV-signal-contract.md`'s "Rung 1b is only half-delivered" Trap was REWRITTEN
to say when it closed, never deleted, and two new Traps record what this rung
actually tripped over: a `POLICY_SIGNALS` entry without its producer predicate,
and `manifest.roles` membership not being seat-boundness.

## Errata

Two entries, landed in this commit:

- **E37** — "the 42-root sweep" is a wrong count in `CLAUDE.md` and four map
  documents. `tools/root_sweep.py` takes no fixed number; it sweeps every
  openable root, which is **107** and grows. Measured twice this tranche. Not
  corrected in place, because R21 retires the instrument and those sentences are
  due for deletion rather than repair.
- **E38** — `tools/blast_radius.py` reports `CONTACT` for changes that touch no
  frozen surface, and will for every future controller tranche: `Controller`,
  `cap_envelope` and `is_generator_knob` all appear inside `invariants.py`, and
  the match is grep-based — this run reported `run_manifest.py` contact for
  `clamp`, which is `clamp_reserved_attention_fractions` there. Nothing changed:
  how wide that disclosure should be is an operator decision.

## Parked (not done, not promised)

- **P1** — R37–R41, attribution-priority allocation forms (multiple forms, the
  detection signals, the depth-vs-breadth sensitivity dial). Ready-to-send
  prompt in PARKED.md.
- **P2** — the blast-radius gate's grep-wide `SYMBOL_INDIRECT` tier (ERRATA
  E38). Ready-to-send prompt in PARKED.md.
- **P3** — a sweep probe for the `open_loop` observable. May be discharged by
  P4 instead.
- **P4** — **remove the root sweep (R21)**, with the measured 50-reference
  census and a ready-to-send prompt that also states what must NOT be edited
  (`experiments/*` are immutable records) and what must replace it (the census).

**Recommended next: P4.** It is the operator's own standing instruction, already
ledgered verbatim, its census is measured and pasted so the next window starts
from evidence rather than a grep, and it discharges P3 along the way. It also
removes the instrument that cost this tranche about 3.5 hours of wall clock for
an answer the census gave in seconds.
