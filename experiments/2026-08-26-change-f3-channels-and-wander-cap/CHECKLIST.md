<!-- DR-TRANCHE-F3 -->
# Checklist for: "turning research and, simulation and coding permanently on" + the wander cap

State: next=1 blockers=none

Re-read REQUEST.md + SPEC.md before every step. Execute strictly in order.
One step per `dr-execute-step` invocation.

**Map ids this plan was scoped from** (resolved in REQUEST.md, read in the
prescribed order): `DR-INV-frozen-surfaces` → `DR-INV-signal-contract` →
`DR-REC-revise-allocation-policy` → `DR-SEAM-capabilities-x-rules` →
`DR-SEAM-scheduler-x-rules` → `DR-SUB-capabilities`, `DR-SUB-scheduler`,
`DR-CON-scheduler-ranking`, `DR-CON-capability-lifecycle`,
`DR-CON-problem-layer-lifecycle`, `DR-SEAM-llm-x-scheduler` (S19's own seam:
what refuses a knob at the point of use).

**Ceiling:** 1602 insertions (SPEC Budget). Checked with
`python tools/diff_budget.py 4760a32ef --ceiling 1602 --paths src tests docs` at every `[COMMIT]`.

---

## Phase A — the wire fix, first, so nothing else joins the 47

- [ ] 1. (S20) Write `tests/test_controller_reaches_the_wire.py` against the
      UNFIXED tree and prove it RED.
      done-when: `python -m pytest tests/test_controller_reaches_the_wire.py -q`
      reports failures, and the failure text names the ceiling being booked
      instead of the settled cap (paste it).

- [ ] 2. (S19) Change `Adapter._completion_cap`'s qualified branch to the
      settled cap bounded by the route ceiling.
      done-when: `python -m pytest tests/test_controller_reaches_the_wire.py -q`
      -> 0 failed.

- [ ] 3. (S19) Ring: the two suites that own the reservation bound and the
      lease ceiling.
      done-when: `python -m pytest tests/test_v6_reservation_bound_authority.py
      tests/test_route_lease_maxtokens_tuning.py tests/test_controller.py
      tests/test_allocation_signal_consumption.py -q` -> 0 failed.

- [ ] 4. (S19) Map: record the wiring in `docs/map/INV-signal-contract.md`
      (the last trap already owns "what refuses a knob at the point of use")
      and in `docs/map/SEAM-llm-x-scheduler.md`, each with a `check:` that
      would fail if the ceiling-only expression came back.
      done-when: `python tools/docs_verify.py --fast` -> 0 failed, and both
      new checks appear in the run.

- [ ] 5. (S19, S20) [COMMIT] Commit Phase A alone.
      done-when: `python tools/diff_budget.py 4760a32ef --ceiling 1602 --paths src tests docs`
      verdict is not EXCEEDED, and `git status --porcelain` is empty.

## Phase B — the channel registry (H1)

- [ ] 6. (S1, S18) Write `docs/map/INV-evidence-channels.md`: the three
      protected channels, their authority (the 2026-08-14 ruling), the one
      toggle, and the website's declared absence. The agreement gets written
      down BEFORE the code.
      done-when: file exists, contains `DR-INV-evidence-channels`, and
      `python tools/docs_verify.py --links` -> 0 unresolved.

- [ ] 7. (S1, S2, S5, S6) Write `tests/test_evidence_channels.py` — registry
      shape, default-on, per-channel toggle, unknown-id notice, website
      absence, code-testing's checked always-on-ness, and the compile matrix
      rows. Prove RED (no `channels` module yet).
      done-when: `python -m pytest tests/test_evidence_channels.py -q` fails
      on `ModuleNotFoundError: deepreason.channels` (paste it).

- [ ] 7b. (S23) Add the prose-standing guard to
      `tests/test_evidence_channels.py`: the channels-on/channels-off
      differential over every prose criticism in one scripted record, the
      structural check over `channels.py`/`wander.py`, and the kind-blindness
      census. Prose keeps its full standing, checked not promised.
      done-when: `python -m pytest tests/test_evidence_channels.py -q -k
      "prose or kind_blind"` -> 0 failed (after step 8 lands the module).

- [ ] 8. (S1) Create `src/deepreason/channels.py` — `ChannelDeclaration`,
      `CHANNEL_DECLARATIONS`, `DECOMMISSIONED`,
      `DEFAULT_RESEARCH_ALLOWLIST`, `enabled`, `disabled_channels`,
      `unknown_channel_notices`.
      done-when: SPEC S1's accept command -> `ok`.

- [ ] 9. (S2, S8) Add `Config.CHANNELS_DISABLED` and BOTH H2 knobs
      (`SEED_LINEAGE_BUDGET_FLOOR`, `LINEAGE_ALLOCATION_POLICY`) in one
      edit, since all three share the frozen-surface obligation.
      done-when: SPEC S2's accept command -> `ok`.

- [ ] 10. (S8) Add the three unconditional `data.pop` lines to
      `run_manifest.py::_versioned_source_config_data` — the granted
      contact, and the step that makes it digest-preserving.
      done-when: SPEC S8's accept command -> `ok`.

- [ ] 11. (S8) Prove the grant's own claim: the shipped qualification subject
      digest does not move for the three new `Config` fields.
      done-when: `python -m pytest
      tests/test_allocation_signal_consumption.py::test_the_shipped_qualification_subject_digest_does_not_move
      tests/test_reusable_qualification.py -q` -> 0 failed.

- [ ] 12. (S3, S4) Make `engaged_research_policy`, `engaged_simulation_policy`
      and `engaged_inquiry_capability_policy` channel-aware, keeping every
      existing call working with `config=None`.
      done-when: SPEC S3's accept command -> `ok`.

- [ ] 13. (S3, S4, S5, S6, S15) Ring: the channel suite plus every suite the
      census marked EXPECTED TO MOVE or MUST NOT MOVE for H1.
      done-when: `python -m pytest tests/test_evidence_channels.py
      tests/test_v6_policy_preset.py tests/test_v6_engaged_public_defaults.py
      tests/test_contained_simulation_runner.py tests/test_single_run_path.py
      tests/test_decommissioned_pipeline_stays_out.py -q` -> 0 failed
      (goldens regenerated only where SPEC predicted the move).

- [ ] 14. (S7) Record the qualification-digest cost: the before/after subject
      digest pair and the count of goldens updated.
      done-when: `experiments/.../MEASUREMENTS.md` contains both digests and
      the golden count.

- [ ] 15. (S1, S18) Map: `SUB-capabilities.md` and `INDEX.md` gain the new
      invariant's row; `INV-evidence-channels.md`'s checks now run against
      real code.
      done-when: `python tools/docs_verify.py --fast` -> 0 failed.

- [ ] 16. (H1) [COMMIT] Commit Phase B.
      done-when: `python tools/diff_budget.py 4760a32ef --ceiling 1602 --paths src tests docs`
      verdict is not EXCEEDED, and `git status --porcelain` is empty.

## Phase C — the wander cap (H2)

- [ ] 17. (S9, S10, S11, S12, S16) Write `tests/test_wander_cap.py` — the
      policy's arithmetic, the floor holding on a stub run with an aggressive
      self-spawner, never-starves, the disclosure, the policy artifact, the
      label differential, and the phantom-emission assertions. Prove RED.
      done-when: `python -m pytest tests/test_wander_cap.py -q` fails on
      `ModuleNotFoundError: deepreason.wander` (paste it).

- [ ] 18. (S9) Create `src/deepreason/wander.py` — `LineageReading`,
      `LineageDecision`, `LINEAGE_POLICIES`, `decide`, `SIGNALS`.
      done-when: SPEC S9's accept command -> `ok`.

- [ ] 19. (S14) Declare the two new signals in `signals.py` with a real unit
      and staleness, and add both to `allocation.POLICY_SIGNALS` WITH their
      `_PRODUCERS` and `_RESOLUTIONS` entries — the pair, never half of it.
      done-when: SPEC S14's accept command -> `ok`.

- [ ] 20. (S10, S11) Wire `_select_problem`: the seed-cycle counter, the
      reading, `wander.decide`, candidacy gating, the per-cycle share signal,
      the transition disclosure and the policy artifact.
      done-when: `python -m pytest tests/test_wander_cap.py -q -k
      "floor_holds or never_starves or discloses or policy_artifact"` ->
      0 failed.

- [ ] 21. (S13) Emit the four phantom allocation signals at the four points
      where `controller.py` acts on them.
      done-when: SPEC S13's accept commands -> `ok` and 0 failed.

- [ ] 22. (S12) Mutation-prove the efficiency-never-evidence boundary in a
      SCRATCH COPY: (a) teach the adjudicator to read the throttle; (b) mint
      a warrant when the throttle engages. Both must turn the differential
      RED; (b) must also turn the structural check RED.
      done-when: `experiments/.../proof/s12_mutation.txt` exists and shows
      RED for both mutations and GREEN on the unmutated tree.

- [ ] 23. (S10, S11, S13) Ring: every suite the census marked for H2.
      done-when: `python -m pytest tests/test_wander_cap.py
      tests/test_controller.py tests/test_signal_contract.py
      tests/test_allocation_signal_consumption.py
      tests/test_scheduler_promotion_rank.py tests/test_capture14_hysteresis.py
      tests/test_premise_channel_loop.py tests/test_import_role_survivors.py
      tests/test_amendment_epochs.py -q` -> 0 failed.

- [ ] 24. (S18) Map: `INV-signal-contract.md` (the lineage layer, the new
      `POLICY_SIGNALS` census, the wander policy's own
      efficiency-never-evidence row), `REC-revise-allocation-policy.md` and
      `CON-scheduler-ranking.md` (the throttle as a CANDIDACY gate beside
      `INTEGRATION_BUDGET_SHARE`, never in the rank key).
      done-when: `python tools/docs_verify.py --fast` -> 0 failed.

- [ ] 25. (H2) [COMMIT] Commit Phase C.
      done-when: `python tools/diff_budget.py 4760a32ef --ceiling 1602 --paths src tests docs`
      verdict is not EXCEEDED, and `git status --porcelain` is empty.

## Phase D — modularity, and the gates

- [ ] 26. (S17) Write `tests/test_channel_and_wander_modularity.py` — the five
      architecture checks, each written to go RED on the bypass it names.
      done-when: `python -m pytest
      tests/test_channel_and_wander_modularity.py -q` -> 0 failed.

- [ ] 26b. (S21, S22) Add the sixth architecture check — the ROAD exists in
      every launch path (compiled policy bounds, non-empty allowlist, the
      simulation controller constructs, the code-testing road evaluates).
      done-when: `python -m pytest
      tests/test_channel_and_wander_modularity.py -q -k "road"` -> 0 failed.

- [ ] 27. (S17) Prove the architecture test FAILS on a bypass: in a scratch
      copy, make `scheduler.py` call the policy function directly.
      done-when: `experiments/.../proof/s17_bypass.txt` shows the test RED
      under the bypass and GREEN without it.

- [ ] 28. (S18) Add the granted-contact row to
      `docs/map/INV-frozen-surfaces.md` — the three `data.pop` lines, the
      forecast quoted, and the digest-preservation check.
      done-when: `python tools/docs_verify.py --fast` -> 0 failed.

- [ ] 29. (all) Map gate, FULL (not `--fast`), on an otherwise idle box.
      done-when: `python tools/docs_verify.py` -> 0 failed, then
      `python tools/docs_verify.py --audit` -> 0 refused, then
      `python tools/docs_verify.py --links` -> 0 unresolved (paste all three).

- [ ] 30. (all) Full gate, alone, nothing else running.
      done-when: `python -m pytest tests/ -q -n 4` ends "N passed, 0 failed"
      (paste it).

- [ ] 31. (all) Wheel smokes — the public surface may have moved (a new
      module, new Config fields).
      done-when: `python scripts/wheel_smoke.py` and `python -u
      scripts/wheel_operational_smoke.py` both exit 0, with pins updated in
      THIS commit if the surface moved.

- [ ] 32. (all) [COMMIT] Push and confirm a clean tree.
      done-when: `git status --porcelain` is empty AND the branch head is on
      `origin/claude/deepreason-f3-rebuild-9tf39b`.
