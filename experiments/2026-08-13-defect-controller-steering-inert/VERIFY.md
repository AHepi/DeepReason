# Verify: the steering loop fires on a compiled-config run

GOAL.md's success criterion, checked line by line. Live section is filled
in at the bottom from the guarded run; the offline sections stand on their
own and are the proof of record if the live run is inconclusive.

## 1. Regression suite — PASS

    python -m pytest tests/test_controller_steering_parity.py -q
    -> 12 passed

The four assertions GOAL.md named, mapped to their tests:

| GOAL criterion | Test |
|---|---|
| (1) compiled-manifest run through the one door records controller attachment | `test_the_one_door_attaches_a_controller_with_real_authority` — drives `ops.run_scheduler` (what `start_manifest_run` calls) with a bound, qualified v6 manifest and asserts the controller reaching the scheduler already covers every role the adapter bound |
| (2) at least one policy evaluation, or the typed nothing-to-steer record | `test_the_grounded_configuration_steers_instead_of_sitting_inert` (policies emitted) and `test_a_controller_with_nothing_to_steer_records_that_it_has_nothing` (typed `controller-authority` scope=`none`) |
| (3) envelope coverage for every manifest-bound role | `test_every_manifest_bound_role_gets_a_barrier_containing_its_cap` — all eleven grounded roles, asserting the assigned 16384 is INSIDE each barrier, not merely that a barrier exists |
| (4) managed-path fixture byte-unchanged | The managed path and the compiled path are one path since `experiments/2026-08-13-change-single-run-path-unification`; `tests/test_lifecycle_operation_parity.py` (12 tests) passes unchanged, and the whole gate is green with no fixture regenerated |

## 2. Mutation proof — the suite is pinned to the mechanism

A passing test proves nothing until it can fail. Both halves of the fix
were reverted in place and the right tests died:

    # neuter the anchoring only (API intact, behaviour reverted)
    configured = self._current_caps()   ->   configured = {}
    -> 3 failed, 9 passed
       FAILED test_every_manifest_bound_role_gets_a_barrier_containing_its_cap
       FAILED test_the_grounded_configuration_steers_instead_of_sitting_inert
       FAILED test_partial_authority_names_which_roles_are_out_of_reach

    # drift the replay reader back to the static table
    cap_envelope(knob, _configured_role_cap(knob)) -> cap_envelope(knob, None)
    -> 1 failed, 11 passed
       FAILED test_replay_authorizes_a_cap_the_controller_could_legitimately_set
       (AssertionError: {'attempt-limits'})

## 3. The reproduction inverted — PASS

`repro_controller_inert.py`, unmodified since the diagnosis phase, now
exits 1 ("NOT REPRODUCED"), which is the passing state for a fixed defect.
Pre-fix vs post-fix on the identical artifact:

| | pre-fix | post-fix |
|---|---|---|
| `step()` over 8 cycles | 8x `None` | 4 proposals over 5 roles, alternating with `dwell=2` |
| policy artifacts | 0 | 4 |
| `controller-*` records | `[]` | 1 `controller-authority`, scope `full`, all 11 roles steerable |
| judge cap trajectory | 16384 (frozen) | 16384 -> 10240 -> 6400 -> 4000 -> 2500 |

Full output in REPRO.md's post-fix section.

## 4. The existing guarantee survived — PASS, byte-unchanged

`tests/test_controller.py::test_controller_does_not_normalize_an_explicit_cap_outside_its_envelope`
passes with NO edit to the test. A 7,000 baseline yields a `[800, 7000]`
barrier; a truncation signal proposes `clamp(round(7000*1.6)) = 7000`,
equal to the current value, so no delta, `step()` returns `None`, the cap
stays 7,000 and no `controller-update` record appears. The rule "the
controller has no authority to normalize an explicit compiled setting" is
now preserved BY CONSTRUCTION rather than by a guard that also disabled
the whole mechanism. No fixture in the repo was updated for this fix.

## 5. Full gate — PASS

    python -m pytest tests/ -q -n 4
    -> 3591 passed, 0 failed, 7 skipped   (854s)

Zero permitted failures: the one long-standing carve-out
(`test_bronze_report.py::test_census_totals_internally_consistent`,
`assert 159 == 165`) was reproduced on a clean `origin/main` worktree,
confirmed pre-existing and NOT caused by this fix, and then deleted on the
operator's instruction ("Forget bronze baseline. It's irrelevant and
should be deleted", 2026-08-13) rather than re-baselined.
`docs/AUDIT_BASELINES.md` now records the gate at 0 failed.

## 6. Map gate — PASS against baseline

    python tools/docs_verify.py          -> 3 failed
    python tools/docs_verify.py --audit  -> 0 findings
    python tools/docs_verify.py --links  -> 0 dangling, 53 documents

The 3 are exactly the recorded baseline (`docs/AUDIT_BASELINES.md`): all
`CON-run-identity.md` git-history checks that need an unshallowed clone.
Every check added by this tranche passes, and `--audit` — which refuses a
check that cannot fail — reports nothing, so the new checks are falsifiable.

## 7. Diff budget — WITHIN

    python tools/diff_budget.py origin/main --ceiling 150 \
      --paths src/deepreason/controller.py src/deepreason/invariants.py \
              src/deepreason/signals.py
    -> {"areas": {"controller.py": 122, "invariants.py": 21, "signals.py": 6},
        "total_insertions": 149, "ceiling": 150, "verdict": "WITHIN"}

It read `EXCEEDED` twice before this (165, then 152) and both were fixed by
removing narration and one duplicated derivation, never by raising the
ceiling.

## 8. Root sweep — the frozen-surface proof obligation

(filled in below)

## 9. Live run — PARTIAL PASS, and the honest split

Three epochs, each a fresh root compiled from byte-copies of the grounded
tranche's `build_manifest.py` and `run-config.yaml`. All three compiled to
`manifest_sha256 = 8e22d0431fd2b98dc915c66f2f3ccc6dc43184b4c326ff5d388a7c013a80989d`
— identical to the grounded run's id — so the configuration is provably
the one that recorded zero steering, and the code was the only variable.

| epoch | budget | events | provider results | outcome |
|---|---|---|---|---|
| 1 | 6 cy / 150k | 64 | 4 | failed cycle 0, `operational_failure` |
| 2 | 6 cy / 150k | 89 | 9 | failed cycle 0, `operational_failure` |
| 3 | 12 cy / 500k | 114 | 14 | failed cycle 0, `operational_failure` |

### PASS — the controller attaches with real authority, live

Recorded at seq 28 of EVERY epoch, identically:

    controller-authority  full
    {"steerable":["argumentative_critic","conjecturer","defender",
    "grounding_reviewer","judge","property_designer","summarizer",
    "synthesizer","thesis","variator","vision_critic"],"unsteerable":{}}

All ELEVEN bound roles inside a barrier the controller may move within,
including the five that appear in no static envelope table. Against the
same configuration, the grounded root's 12,991 events contain no such
record and no steerable role at all. GOAL criteria (1) and (3) are met on
live evidence, reproduced three times.

`verify_root` returns `[]` on all three roots: the new record does not
disturb replay validation on a real root.

### INCONCLUSIVE — the cap trajectory

No epoch emitted a policy artifact, because none reached cycle 1. A
narrowing decision needs `CLEAN_WINDOWS=3` spotless calls for a role and
the runs died before any role accumulated them. Per CLAUDE.md, one live
attempt that misses a path is inconclusive for that path and the offline
regression remains the proof — here the offline proof is
`repro_controller_inert.py` (judge 16384 -> 10240 -> 6400 -> 4000 -> 2500,
four policy artifacts) and
`test_the_grounded_configuration_steers_instead_of_sitting_inert`.

Recorded as an honest negative: the trajectory is proven offline and NOT
proven live.

### The failures are not this tranche's change

Settled on committed evidence after the live control was blocked twice by
provider noise (its qualification failed `REPAIR_SCOPE_VIOLATION`, then
`alias_failures=1`, both on UNMODIFIED `origin/main` code).

Comparing the first conjecturer prompt in the grounded root against
epoch 3's:

    grounded (ran 24 cycles):  criteria block EMPTY          25,544 bytes
    epoch 3  (died cycle 0):   - reasoning-envelope-wf:      27,655 bytes
                                 program:reasoning-envelope-wf

Every candidate must now carry a pinned program commitment the grounded
run never imposed. It lives on `origin/main`
(`workloads/text.py:296-297`, `programs.py:296`), arrived in commit
`20f50bbfc` from a different tranche, and:

    git diff origin/main -- src/ | grep -c "reasoning-envelope-wf"   # 0

Three record-level facts exonerate the controller independently of that:
every `attempt_trace` in all three epochs records `max_tokens=16384`, the
unmodified manifest value; zero policy artifacts exist, so `_apply_cap`
never ran; and `verify_root` is clean on all three roots.

Parked as P3 with a ready prompt carrying both the leading hypothesis and
the rival it must kill (provider drift), and the experiment that
separates them.

### A limit worth stating, surfaced by epoch 1

The conjecturer truncated at its full 16,384 cap. The controller cannot
help there: anchoring means it may never widen past the cap the operator
assigned, so a seat already at its ceiling and still truncating has no
headroom. That is the safety property working as designed, not a defect —
but it means this fix's value on the grounded configuration is the
NARROWING direction (judge pinned at 16,384 while never exceeding 141
completion tokens), not truncation recovery.
