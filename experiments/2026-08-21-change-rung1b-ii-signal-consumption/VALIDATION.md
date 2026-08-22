# Validation for: Rung 1b-ii — the consumption side of the signal contract

Round 1. **Verdict: FAIL** — one finding, narrow and specific, at the bottom.
Everything else passed, including all three of the operator's grant conditions.

## Acceptance checks

    S1 (R1,R2,C1)  $ pytest ... -k "seats_throttle_independently or bare_role_spelling"
                     2 passed, 15 deselected                              : PASS

    S2 (R1)        $ grep -c "attempt_trace" src/deepreason/controller.py
                     2
                   $ ! grep -q "V3_CANONICAL_ROLES" src/deepreason/allocation.py
                     no role table in allocation.py: ok
                   $ pytest ...::test_seat_identity_is_read_from_the_attempt_trace
                     1 passed                                             : PASS

    S3 (R3)        $ pytest ...::test_the_shipped_qualification_subject_digest_does_not_move
                     1 passed                                             : PASS

    S4 (R8)        $ grep -c "state\.status" src/deepreason/controller.py
                     0
                   $ pytest ...::test_the_controller_reads_no_graph_status
                     1 passed                                             : PASS

    S5 (R4)        $ pytest ... -k matrix
                     4 passed, 13 deselected                              : PASS

    S6 (R5,R6,R7)  $ pytest ... -k open_loop
                     2 passed, 15 deselected                              : PASS

    S7 (R9)        $ python -c "...unspecified_declarations..."
                     84
                   $ pytest tests/test_signal_contract.py -q
                     10 passed                                            : PASS

    S8 (R10,R11)   $ pytest ... -k "evidence or verdict"
                     3 passed, 14 deselected                              : PASS
                   mutation proof: proof/s8_mutation.txt — repo 3 passed;
                   mutation A 1 failed; mutation B 1 failed                : PASS

    S9 (R12)       docs_verify below                                      : PASS
    S10 (R13)      DELIVERY.md — owed at delivery, not here                : n/a

    S11 (R15)      $ diff proof/sweep_before.txt proof/sweep_after.txt
                     (no output)  rc=0
                   $ pytest ... -k "before_seat_keying or resolves_differently"
                     2 passed, 15 deselected                              : PASS

    S12 (R16)      proof/s12_red.txt   1 failed  (attempt-limits)
                   proof/s12_green.txt 2 passed                           : PASS

    S13 (R17-R19)  $ grep -c "_configured_role_cap" docs/map/INV-frozen-surfaces.md
                     1
                   $ git diff --name-only origin/main..HEAD | grep -c run_manifest.py
                     0                                                    : PASS

## Full gate

    $ python -m pytest tests/ -q -n 4
    3779 passed, 6 skipped in 1182.38s (0:19:42)                          : PASS

0 failed. No MCP-thread flake appeared, so nothing needed isolating (C8). The
count sits above the operator's stated 3755 baseline for two reasons, both
accounted for: that baseline was measured at `c8071fc34`, which `origin/main`
has since advanced 9 commits past (Rung 3b and others), and this tranche adds
27 collected tests across `tests/test_allocation_signal_consumption.py` and
`tests/test_signal_contract.py`.

## Record-behavior preservation

The change touched a READER of the append-only record (`invariants.py`), so the
full instrument was owed rather than a spot-check.

    107 committed roots, before and after, diff EMPTY, rc=0.
    Baseline composition: 87 valid=True, 9 valid=False, 11 unopenable — so the
    empty diff is not vacuous; a verdict moving in either direction would show.

Analytic half (`proof/s11_targeted_census.txt`), which is the stronger one:
both changed lines are reachable only from inside the loop over a controller
policy artifact's `knobs` map, and **0 of the 107 roots contain one**. The
targeted set — roots for which a verdict COULD move — is empty. This extends
ERRATA E28's measurement (104 logs) to 107 and to this change's exact input.

## Frozen-surface diff

    $ git diff --stat origin/main..HEAD -- capabilities/state.py harness.py \
        invariants.py run_manifest.py qualification.py
     src/deepreason/invariants.py | 29 +++++++++++++++++++----------
     1 file changed, 19 insertions(+), 10 deletions(-)

NON-EMPTY, and permitted: REQUEST.md Amendment 1b quotes the operator granting
this exact surface — "GRANTED: the 12-line reader fix in
src/deepreason/invariants.py (_configured_role_cap), on three conditions".
Measured content: 6 executable lines added, 7 removed, net -1 (docstring and
comment lines excluded), inside the granted 12. The four other frozen surfaces
are untouched. `run_manifest.py` in particular is untouched, and the gate's
alarm on it is a proven grep false positive (SPEC.md M3).

## Map

    docs_verify:            60 documents, 940 checks, 3 failed             : PASS
    docs_verify --audit:    0 finding(s)                                   : PASS
    docs_verify --links:    0 dangling reference(s), 60 document(s)        : PASS
    docs_verify --coverage: 6 seams swept, 16 without a Sweep: header,
                            2 finding(s)                                   : PASS (baseline)

The 3 `docs_verify` failures are exactly the pre-existing
`CON-run-identity.md:200/202/204` shallow-clone failures recorded in
`docs/AUDIT_BASELINES.md` line 25 and named verbatim in REQUEST.md C8. All
three fail on git history this container's shallow clone does not carry.

`--coverage`'s 2 findings and 16 header-less seams are pre-existing and name
seams this tranche did not touch (`SEAM-schools-x-scratch.md`'s unnamed
enforcement site; five seams awaiting a `Sweep:` header "when next touched").
None is a seam this change moved.

**new checks added by this change:** 7 in `docs/map/INV-signal-contract.md`
(seat-instance keying ×2, the shared route-cap derivation, the matrix, the
open-loop notice, efficiency-never-evidence ×2), 2 in
`docs/map/REC-add-signal.md`, 3 in `docs/map/INV-frozen-surfaces.md` (the
granted contact ×2, the false-alarm row). Each was run individually and
returned rc=0 before `Verified-at:` was advanced.

**record observables added vs sweep probes:** the `open_loop` key on the
`controller-authority` Measure payload is a new record observable. No sweep
probe is owed for it and the reason is not silence: `tools/root_sweep.py`
reports one row per root over verdicts and identity stamps, and this observable
cannot appear in any committed root — 0 of 107 contain a controller policy body
or authority record at all (`proof/s11_targeted_census.txt`). A probe would read
"-" on every row for the same reason the seat-bindings column does. It becomes
owed the first time a live run records one; PARKED.md P3 carries the prompt.

**wheel smoke:**

    $ python scripts/wheel_smoke.py
    wheel smoke passed: isolated V6-only contents, clean imports, exact entry
    points, module parity, MCP registration, and exact MCP schemas

Owed and run: the tranche adds `src/deepreason/allocation.py`, which moves the
wheel layout that `module parity` pins. No pin needed changing — the new module
is inside the package and adds no console entry point and no MCP tool, so the
entry-point set and the MCP schema shas are unmoved.
`wheel_operational_smoke.py` covers the operational provider-facing surface,
which this change does not move; it was started anyway as a stronger check and
its result is recorded in round 2.

## docs_verify --stale — every entry, judged

Two entries are this tranche's and are the FAIL below:

- **`SUB-scheduler.md`** — 3 commits since `e6badeead`, one of them mine
  (`f42429de1`, the consumption side, which touches `controller.py`).
- **`SUB-verification.md`** — 1 commit since `95814d9e9`, mine
  (`8c4e3e450`, the granted reader fix, which touches `invariants.py`).

Five entries are NOT this tranche's, and are dismissed with their reason:

- `CON-run-identity.md`, `CON-schools.md`, `SEAM-manifest-x-schools.md` — all
  three cite `bce018ae5` (all-configs-allowed, 2026-08-16). Pre-existing.
- `SUB-calculus.md` — cites `1da817eaa` (Rung 3b frame-separation). Pre-existing,
  and that rung's own tranche owns it.
- `SUB-evidence.md` — cites `1a32fb193` (three-layer citable evidence).
  Pre-existing.

None of the five names a file this tranche touched.

## Requirement sweep

    R1  seat-instance keying                  : S1 + S2 outputs
    R2  asymmetric seats throttle independently: S1 (opposite directions, one cycle)
    R3  no role added                          : S2 + S3 (digest pinned, unmoved)
    R4  compiled matrix, four classes          : S5 (4 parametrised cases)
    R5  open-loop topology compiles            : S6
    R6  controller-authority record extended   : S6 (open_loop key asserted)
    R7  disclose never die, CompileNoticeV1    : S6 (type reused, unmodified)
    R8  three status reads migrated            : S4 (grep -c -> 0)
    R9  MIGRATION_DEBT lowered by exactly 5    : S7 (89 -> 84) + proof/s7_registry_diff.txt
    R10 efficiency never evidence, a test      : S8 (differential + ledger + architecture)
    R11 mutation proof, both runs pasted       : proof/s8_mutation.txt
    R12 map moves in the same commits          : Map section; INV-frozen-surfaces.md
                                                 landed in 8c4e3e450 WITH the reader fix
    R13 R-by-R delivery with pasted proof      : owed at dr-deliver-change
    R14 the reader fix is granted              : frozen-surface diff, quoted grant
    R15 reader-only, proven not asserted       : S11 (sweep diff empty) + census
    R16 mutation-proven regression, RED first  : S12 (both runs pasted)
    R17 the grant lives in SPEC.md, dated      : SPEC.md "GRANTED 2026-08-21"
    R18 the map names the contact              : INV-frozen-surfaces.md, same commit
    R19 run_manifest.py false alarm rowed,
        file untouched                         : S13 (grep -c -> 0) + the map row
    R20 measurement, not grep, settles contact : SPEC.md M3 + proof/s11_targeted_census.txt

    C1  no signal name or prose changes spelling: proof/s7_registry_diff.txt
                                                  (0 removed, 0 prose moved) and
                                                  26 controller tests passing UNCHANGED
    C5  no file the Rung 3b window owns         : Rung 3b merged at 5780a9298 before
                                                  this branch started; its delivery
                                                  commit touched no src/ file

## Assumptions carried

    A1  knob names are not registry signal names, so C1 does not bind their
        spelling — but the design leaves every single-seat topology unchanged anyway
    A2  "producer" is decided from the bound roles alone
    A3  the four configuration classes resolve to the four compiled shapes in S5
    A4  the controller stops reading harness.state for status entirely
    A5  five debt entries fixed — the four controller signals plus dropped-call
    A6  R37-R41 (attribution-priority policy) are NOT delivered here; parked

## Verdict: FAIL

**FAIL detail — one finding.** `docs_verify --stale` names two map documents
this tranche's commits made stale, and re-reading them by hand confirms their
PROSE now under-describes the mechanism, even though every one of their `check:`
lines still passes:

- `docs/map/SUB-verification.md`, Traps: "That barrier is anchored per run to
  the cap the manifest assigned **the role**". It is now anchored to the SEAT
  INSTANCE. The same trap also says "the 42-root sweep is the instrument that
  must confirm that before any future change here" — this change ran it, at 107
  roots, and that fact belongs in the trap.
- `docs/map/SUB-scheduler.md`, Traps: "a **role's** assigned cap may only WIDEN
  the barrier" and the authority record described as "the steerable **roles**".
  Both are seat instances now.

Neither is FALSE for a single-seat run, which is why no check caught it — and
that is exactly the drift the map exists to prevent: a reader following either
document would not learn that a role bound to several seats now throttles them
independently. SPEC.md's own blast-radius census predicted this row
("`SUB-verification.md:163,174` ... its prose gets the seat sentence if its
check turns out to describe the anchor"); it does describe the anchor.

Per `dr-validate-change`'s exit criteria, validation does not fix the thing it
validates. Routed back to `dr-plan-steps` as steps 32-34: update both Traps,
re-run their checks, re-validate. Nothing in the code changes.

---

# Validation round 2 — after the map fix

Re-run scope: the round-1 finding was confined to two map documents' PROSE. No
`src/` file changed between rounds, so the acceptance checks, the gate and the
sweep are re-affirmed rather than re-derived, and the map section is re-run in
full. `git diff --stat a3c45a268..HEAD -- src/` is empty, which is the evidence
for that claim:

    $ git diff --stat a3c45a268..HEAD -- src/
    (no output)

## Map — re-run

    docs_verify:            60 documents, 940 checks, 3 failed             : PASS
    docs_verify --stale:    5 document(s) worth re-reading                 : PASS

The 3 failures are the baseline `CON-run-identity.md:200/202/204` shallow-clone
failures (`docs/AUDIT_BASELINES.md` line 25, REQUEST.md C8).

`--stale`'s 5 entries are the same 5 dismissed in round 1, all pre-existing and
none naming a file this tranche touched:

    CON-run-identity.md, CON-schools.md, SEAM-manifest-x-schools.md
        -> bce018ae5 (all-configs-allowed, 2026-08-16)
    SUB-calculus.md      -> 1da817eaa (Rung 3b frame-separation)
    SUB-evidence.md      -> 1a32fb193 (three-layer citable evidence)

**`SUB-verification.md` and `SUB-scheduler.md` no longer appear.** That is the
round-1 FAIL discharged. Both documents' own checks were re-run individually
before `Verified-at:` advanced to `c29785aa`:

    SUB-scheduler.md, controller-barrier trap   3 passed
    SUB-scheduler.md, authority-record trap     3 passed
    SUB-verification.md, anchoring trap         rc=0 (now also pins the
                                                delegation to route_cap_for_knob)

## Packaging surface

    $ python scripts/wheel_smoke.py
    wheel smoke passed: isolated V6-only contents, clean imports, exact entry
    points, module parity, MCP registration, and exact MCP schemas

    $ python -u scripts/wheel_operational_smoke.py
    wheel operational smoke passed: installed setup, explicit qualification
    (80 qualification calls; 418 total calls), readiness, question-only
    reasoning, replay-verified terminal retrieval, cache reuse, opaque MCP
    restart, budget ceiling, and pre-V6 fail-closed admission

Both owed and both run. `wheel_smoke` because the tranche adds
`src/deepreason/allocation.py`, which moves the wheel layout that `module
parity` pins; no pin needed changing, since the new module adds no console entry
point and no MCP tool. The operational smoke was not strictly owed — the
provider-facing surface did not move — and was run anyway as the stronger check.

## R21 — the mid-tranche amendment

    R21  the root sweep is removed  : PARTIAL, by design, and recorded

REQUEST.md Amendment 2 argues the routing from a measured 50-reference census:
R21 is a different goal with its own blast radius across `CLAUDE.md`, four
skills, nine map documents and a test, and one tranche one goal is repo law. It
is parked as P4 with a ready-to-send prompt.

What this tranche DID do about it: `SUB-verification.md`'s anchoring trap
mandated the sweep, and this tranche was editing that exact trap in step 32.
The mandate is removed and replaced by the census. Nothing else was touched for
R21, and `tools/root_sweep.py` still stands.

What R21 does NOT retract: the sweep evidence already taken discharged grant
condition 1 (R15) on the day it was asked for. Retiring an obligation going
forward does not unmake a measurement already made — and the census, which is
the half that survives R21 entirely, independently answers the same question.

## Verdict: PASS

Every acceptance check S1-S13 passed with pasted output. Full gate 0 failed.
All three of the operator's grant conditions discharged: reader-only proven by
an empty 107-root diff AND by the census that says why none could move
(condition 1); the regression run RED on the unfixed tree and GREEN after, both
pasted (condition 2); the grant dated in SPEC.md, the map moved in the same
commit as the reader fix, and `run_manifest.py` rowed as a false alarm and left
untouched (condition 3). The round-1 FAIL is discharged and its evidence is kept
above rather than rewritten.

Routed to `dr-deliver-change`.
