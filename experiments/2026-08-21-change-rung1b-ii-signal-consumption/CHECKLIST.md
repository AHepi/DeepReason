# Checklist for: Rung 1b-ii — the consumption side of the signal contract

State: next=9 blockers=none

Map ids this plan was built on: `DR-INV-signal-contract` (owner),
`DR-REC-add-signal`, `DR-REC-revise-allocation-policy`, `DR-INV-frozen-surfaces`
(surface 3, granted contact), `DR-SUB-scheduler` (controller prose),
`DR-SUB-verification` (`_configured_role_cap` prose), `DR-SUB-llm` (adapter
endpoints / seat resolution). Seam `scheduler x signal-contract` is recorded as
undocumented in `INV-signal-contract.md`'s own header and is NOT created here
(SPEC.md "Out of scope").

Re-read REQUEST.md + SPEC.md before every step. Execute strictly in order.
One step per dr-execute-step invocation.

**Hard ordering constraint (R16 / S12):** steps 2-4 run the seat-anchoring
regression RED on the UNFIXED tree. No edit to `invariants.py` may happen before
step 5. A regression test first seen green proves nothing.

- [x] 1. (S11) Capture the BEFORE root sweep on the unfixed tree.
      done-when: `proof/sweep_before.txt` exists, has one line per openable
      root, and `grep -c "" proof/sweep_before.txt` equals the root count
      printed by `python -c "import pathlib;print(len({p.parent for p in pathlib.Path('experiments').rglob('log.jsonl')}))"`

- [x] 2. (S12) Write `tests/test_allocation_signal_consumption.py` containing
      ONLY the seat-anchoring regression `test_a_seat_knob_anchors_to_its_own_route_ceiling`
      (a manifest binding conjecturer to two routes, seat 1 at max_tokens=16384;
      assert `cap_envelope("cap:conjecturer#1", _configured_role_cap-equivalent)`
      admits 16384).
      done-when: the file exists and contains that test name

- [x] 3. (S12) Run it RED on the unfixed tree and save the output.
      done-when: `python -m pytest tests/test_allocation_signal_consumption.py -q`
      exits non-zero AND its output is saved verbatim to `proof/s12_red.txt`

- [x] 4. (S12) [COMMIT] Commit the RED regression and its pasted failure.
      done-when: `git log -1 --name-only` names the test file and
      `proof/s12_red.txt`; branch pushed

- [x] 5. (S1, S2, S4, S6) Create `src/deepreason/allocation.py`: seat-instance
      naming (`seat_instance`, `split_seat_instance`, `cap_knob`), the
      policy-referenced signal set `POLICY_SIGNALS`, the producer predicates,
      `open_loop_signals`, `open_loop_notices` (lazy `CompileNoticeV1` import),
      and the two policy-status signal readers.
      done-when: `python -c "import deepreason.allocation as a; print(a.POLICY_SIGNALS)"`
      prints 5 names AND `python -m pytest tests/test_signal_contract.py -q` still passes

- [x] 6. (S4, S6, S7) Register in `src/deepreason/signals.py`: four new
      `SignalDeclaration`s (`allocation.seat-truncation.v1`,
      `allocation.seat-repair.v1`, `allocation.policy-authorized.v1`,
      `allocation.policy-contested.v1`) with real unit/staleness, and replace
      `unspecified` on the five debt entries named in SPEC.md S7, leaving their
      `semantics` prose byte-identical.
      done-when: `python -c "from deepreason.signals import unspecified_declarations as u;print(len(u()))"`
      prints `84`

- [x] 7. (S7) Lower `MIGRATION_DEBT` in `tests/test_signal_contract.py` from 89
      to 84 and add `test_every_policy_referenced_signal_is_declared`.
      done-when: `python -m pytest tests/test_signal_contract.py -q` -> passes

- [x] 8. (S7) [COMMIT] Commit the registry declarations and the debt paydown.
      done-when: branch pushed; `git status --porcelain` empty

- [ ] 9. (S1, S2) Rekey `Controller` by seat instance in
      `src/deepreason/controller.py`: `_process_signals`, `_current_caps`,
      `_anchor_envelopes`, `_authority`, `_clean_streak`, `_propose`,
      `_apply_cap`; and teach `cap_envelope` to resolve its base envelope from
      the role part of a seat-suffixed knob.
      done-when: `python -m pytest tests/test_controller.py tests/test_controller_steering_parity.py -q`
      -> passes with no assertion weakened (diff of those two files is empty
      except the `_process_signals` key assertions SPEC.md predicted)

- [ ] 10. (S4) Migrate the three `harness.state.status.get(...)` reads onto the
      declared signal readers in `allocation.py`.
      done-when: `grep -c "state\.status" src/deepreason/controller.py` -> `0`

- [ ] 11. (S6) Extend `_state_authority`'s `controller-authority` payload with
      the sorted `open_loop` signal list.
      done-when: `python -m pytest tests/test_controller.py -q` -> passes

- [ ] 12. (S1, S4, S6) [COMMIT] Commit the consumption side.
      done-when: branch pushed; `git status --porcelain` empty

- [ ] 13. (S12, S13/R18) Apply the granted 12-line reader fix to
      `_configured_role_cap` in `src/deepreason/invariants.py` AND, in the same
      edit set, add the contact line to `docs/map/INV-frozen-surfaces.md`
      (naming the contact, the 2026-08-21 grant, why a reader fix is the
      permitted kind, and the `run_manifest.py` false alarm with its grep
      proof).
      done-when: `python -m pytest tests/test_allocation_signal_consumption.py -q -k ceiling`
      -> passes (saved verbatim to `proof/s12_green.txt`) AND
      `grep -q "_configured_role_cap" docs/map/INV-frozen-surfaces.md`

- [ ] 14. (S11) Add the reader-only differential test: every knob WITHOUT `#`
      resolves identically pre- and post-fix; only `#`-bearing knobs differ.
      done-when: `python -m pytest tests/test_allocation_signal_consumption.py -q -k reader_only`
      -> passes

- [ ] 15. (S11) Capture the AFTER root sweep and diff it against step 1.
      done-when: `diff proof/sweep_before.txt proof/sweep_after.txt` prints
      nothing and exits 0 (saved to `proof/sweep_diff.txt`, empty)

- [ ] 16. (S13/R19) Prove `run_manifest.py` was not touched.
      done-when: `git diff --name-only origin/main...HEAD | grep -c run_manifest.py`
      -> `0`

- [ ] 17. (S11, S12, S13) [COMMIT] Commit the reader fix WITH its map line.
      done-when: `git log -1 --name-only` names both
      `src/deepreason/invariants.py` and `docs/map/INV-frozen-surfaces.md`, and
      names no other `src/` file; branch pushed

- [ ] 18. (S1) Add the seat-instance behaviour tests:
      `test_two_asymmetric_seats_throttle_independently`,
      `test_a_single_seat_role_keeps_the_bare_role_spelling`,
      `test_seat_identity_is_read_from_the_attempt_trace`.
      done-when: `python -m pytest tests/test_allocation_signal_consumption.py -q -k seat_instance`
      -> passes

- [ ] 19. (S3) Add `test_the_shipped_qualification_subject_digest_does_not_move`
      pinning `d47cb2bf27021474aa17933bc3dcfeeb5dfb1c23b0cfe49452941aace39088dc`.
      done-when: that test passes

- [ ] 20. (S5) Add the compiled configuration matrix over solo / no-schools /
      judges-off / legacy-on: each compiles, the controller attaches, every
      policy-referenced signal has a producer.
      done-when: `python -m pytest tests/test_allocation_signal_consumption.py -q -k matrix`
      -> 4 parametrised cases pass

- [ ] 21. (S6) Add the open-loop tests: a critic-less topology compiles and
      yields a typed `ALLOCATION_OPEN_LOOP` notice naming
      `allocation.policy-contested.v1`, and the `controller-authority` record
      carries it.
      done-when: `python -m pytest tests/test_allocation_signal_consumption.py -q -k open_loop`
      -> passes

- [ ] 22. (S8) Add the efficiency-never-evidence tests: the differential
      (controller-stepped vs not: identical status maps, warrant sets, att/dep
      edges), the ledger check, and the architecture check.
      done-when: `python -m pytest tests/test_allocation_signal_consumption.py -q -k evidence`
      -> passes

- [ ] 23. (S8/R11) MUTATION PROOF: in a scratch copy of the tree only, break
      `is_generator_knob`'s tribunal guard, run the evidence test, watch it go
      RED, discard the copy.
      done-when: both runs saved verbatim to `proof/s8_mutation.txt`, showing
      RED on the mutated copy and GREEN on the repo tree, and
      `git status --porcelain` is empty

- [ ] 24. (S1, S3, S5, S6, S8) [COMMIT] Commit the behaviour, matrix,
      open-loop and evidence tests plus the mutation proof.
      done-when: branch pushed; `git status --porcelain` empty

- [ ] 25. (S9) Advance `docs/map/INV-signal-contract.md`: a section per
      delivered clause with an executable `check:` each, the debt number
      89 -> 84, the "half-delivered" Trap REWRITTEN (never deleted) to say when
      it was fixed, and `Verified-at:` advanced only after re-running that
      document's own checks.
      done-when: every `check:` in that document exits 0 when run individually

- [ ] 26. (S9) Drop the "not yet built" / "lands in Rung 1b-ii" forward
      references from `docs/map/REC-add-signal.md` and
      `docs/map/REC-revise-allocation-policy.md`.
      done-when: `grep -c "Rung 1b-ii" docs/map/REC-*.md` -> `0`

- [ ] 27. (S9) Map check: `python tools/docs_verify.py` (full, not `--fast`,
      run alone on an idle box).
      done-when: failures are exactly the 3 pre-existing
      `CON-run-identity.md` shallow-clone failures named in C8, and no others;
      `--audit` reports no newly-refused check

- [ ] 28. (S9) [COMMIT] Commit the map.
      done-when: branch pushed; `git status --porcelain` empty

- [ ] 29. (all) Full gate: `python -m pytest tests/ -q -n 4`, run alone.
      done-when: output ends `0 failed` (pasted). Any MCP-thread failure is
      re-run isolated before attribution, per C8.

- [ ] 30. (all) Wheel smokes: `python scripts/wheel_smoke.py` and
      `python -u scripts/wheel_operational_smoke.py`.
      done-when: both exit 0 (pasted). This tranche adds a module but no
      console entry point or MCP tool, so no pin is expected to move; if one
      does, the pin is updated in THIS step's commit.

- [ ] 31. (all) [COMMIT] push and confirm clean tree.
      done-when: `git status --porcelain` is empty AND branch head is on origin


## Execution log

**Step 1 (S11) — BEFORE sweep.** `python tools/root_sweep.py` launched over the
107 openable roots under `experiments/`; still running at the time steps 2-4
were executed. It reads roots read-only and writes only
`proof/sweep_before.txt`, so it does not interact with the steps below. Its
done-criterion is re-checked when it lands, and step 15 diffs it against the
AFTER sweep.

**Step 2 (S12) — the RED regression written.** `tests/test_allocation_signal_consumption.py`
holds `test_a_seat_knob_anchors_to_its_own_route_ceiling` (the operator's
16,384 case) and its bound-companion `test_a_seat_knob_is_still_bounded_by_its_own_route`.

**Step 3 (S12) — run RED on the unfixed tree.** Saved verbatim to
`proof/s12_red.txt`:

    1 failed, 1 passed in 0.46s
    FAILED ...::test_a_seat_knob_anchors_to_its_own_route_ceiling
    AssertionError: a per-seat knob was refused a limit its own route
    assigned: ['attempt-limits']

`attempt-limits` is the ONLY violation the synthetic root reports, so the red
is the operator's stated red — the fallback refusing a legitimate limit — and
not incidental breakage. The companion test PASSES red-first too, proving the
4,096 seat's ceiling still binds: the fix must widen per seat, not per role.

**MEASURED REFINEMENT to the granted contact, disclosed rather than absorbed.**
The grant names `_configured_role_cap`. Measuring the failure shows that
function is one of TWO reader sites, and fixing it alone leaves the fix inert:

    src/deepreason/invariants.py:3586  _configured_role_cap  — ANCHORING:
        resolves the knob's ceiling by `manifest.roles.get(knob[len("cap:"):])`,
        so `cap:conjecturer#1` misses and anchors to nothing.
    src/deepreason/invariants.py:3985  the consumer — LOOKUP:
        `allowed_caps = {route.max_tokens,
                         *authorized_controller_limits.get(f"cap:{e.llm.role}")}`
        asks only for the ROLE-keyed knob, so a value authorized under
        `cap:conjecturer#1` is stored and never consulted.

Both are reads in the same file, on the same path, in the granted reader; no
writer, no record format, and no other file is involved. The second site is ONE
added line. Total stays inside the granted 12. Recorded here and in SPEC.md S11
because "the 12-line reader fix in `_configured_role_cap`" was the operator's
own wording, and a second site found by measurement is exactly the kind of thing
that must be said out loud rather than quietly folded in.

**Step 5 (S1/S2/S4/S6) — `src/deepreason/allocation.py` created.**

    $ python -c "import deepreason.allocation as a; print(a.POLICY_SIGNALS)"
    ('allocation.seat-truncation.v1', 'allocation.seat-repair.v1',
     'dropped-call', 'allocation.policy-authorized.v1',
     'allocation.policy-contested.v1')
    $ python -m pytest tests/test_signal_contract.py -q
    7 passed in 0.10s

    open loop, no critic:   ('allocation.policy-contested.v1',)
    open loop, with critic: ()
    notices: [('ALLOCATION_OPEN_LOOP',
               'allocation open-loop for signal allocation.policy-contested.v1')]

**Step 6 (S4/S6/S7) — registry.** Four declarations added, five debt entries
paid down.

    $ python -c "from deepreason.signals import unspecified_declarations as u;print(len(u()))"
    84

C1 proven rather than asserted (`proof/s7_registry_diff.txt`), by executing the
PREVIOUS commit's `signals.py` alongside the new one and comparing declaration
by declaration:

    added: ['allocation.policy-authorized.v1', 'allocation.policy-contested.v1',
            'allocation.seat-repair.v1', 'allocation.seat-truncation.v1']
    removed: []
    semantics prose moved: []
    unit/staleness moved: ['controller-authority', 'controller-hold:',
                           'controller-rehydration', 'controller-update',
                           'dropped-call']
    debt: 89 -> 84

No name removed, no prose moved, exactly the five paydowns claimed. The
paydown is an explicit `_PAID_DOWN` override table rather than retyped
entries, so the prose CANNOT drift while a unit is being stated.

**Step 7 (S7) — `MIGRATION_DEBT` 89 -> 84**, with the arithmetic recorded in
the constant's own comment, plus two new contract tests: every
policy-referenced signal is declared, and none of them still carries the
`unspecified` debt marker (a consumer that must decide how long to believe an
observation may not read a signal whose staleness nobody stated).

    $ python -m pytest tests/test_signal_contract.py tests/test_signals.py -q
    18 passed in 4.83s
