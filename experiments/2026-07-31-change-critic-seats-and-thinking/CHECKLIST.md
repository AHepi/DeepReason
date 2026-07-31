# Checklist

Each step has ONE done-criterion whose output is pasted when checked.
Traces to REQUEST.md. R6 applies throughout: commit locally, never push.

- [x] S1 (R1a) — enable grounding review in the engaged v6 preset so the
      `judge` seat receives a contract.
      Site: `src/deepreason/v6_policy.py:176` `"grounding_review": False`.
      Done-criterion: compile an engaged v6 manifest and show
      `_route_seat_behavioral_contract_assignments` now contains an entry
      whose role is the bridge `reviewer_role`, where before it had none.

- [x] S2 (R2-show, R3) — expose the simulation option AND the form of the
      contract to the critic pack.
      Site: `src/deepreason/llm/packs.py` — a new note constant built from
      the two existing D2b constants (single source of truth, no second
      wording), plus a rendered list of the simulation proposals already
      filed for the targets in this call; `src/deepreason/rules/crit.py`
      passes them from `harness.capability_state`.
      MUST be gated so a run without simulation enabled renders a
      byte-identical critic pack (the D1 lesson: unconditional pack text
      moves committed baselines).
      Done-criterion: rendered critic pack with simulation enabled
      contains `def simulate(inputs, rng)` and the filed proposal's
      request identifier; with simulation disabled it is byte-identical
      to the pre-change render.

- [x] S3 (R4, P2) — binding rule: refuse to launch when the provider
      realises a reasoning knob and thinking is not off.
      Sites: `src/deepreason/llm/providers.py` (availability predicate +
      the off token, beside `REASONING_ADAPTERS` which already knows which
      providers realise the knob), and the `reason`/`qualify` launch path
      in `src/deepreason/cli/main.py`.
      Binds on LAUNCH only — never on loading a committed profile, so
      every existing run root still reopens (SPEC F7).
      Done-criterion: launching with `reasoning: null` on an ollama
      profile exits non-zero with a typed code naming the rule; the same
      launch with `reasoning: "none"` proceeds; a `generic`-provider
      profile with `reasoning: null` is unaffected.

- [x] S4 (R5) — thinking off for the live GLM 5.2 profile.
      Site: the ladder's `deepreason setup` invocation gains
      `--reasoning none`. No code change; the field already accepts it.
      Done-criterion: the written `provider.yaml` shows `reasoning: none`
      and a profile digest of `e800ce9c...` (predicted in SPEC F6).

- [x] S5 — regression tests for S1-S3.
      Done-criterion: the new tests pass and each names what it guards.

- [x] S6 (C2) — full gate.
      Done-criterion: `pytest tests/ -q -n 4` reports 0 failed. Any
      baseline that moves must have been predicted in this checklist
      before it moved; an unpredicted move is a stop.

- [ ] S7 (R7, R8) — the live GLM 5.2 run with thinking off, and the
      report. BLOCKED on the R7 conflict recorded in REQUEST.md: with
      thinking off and R1a on, the qualification subject moves and the
      cached battery cannot apply. Put to the operator before spending
      any provider calls.

## Predicted baseline moves (declared BEFORE any step runs)

S1 changes `engaged_policy_digest()` (the engaged preset's bytes) and adds
a reviewer pair to the inventory. Anything committed that pins either
will move. S2 is gated to simulation-enabled packs, so it should move
nothing that S1 does not already move. S3 and S4 change no rendered
bytes. Exact fixtures are named as S6 discovers them, and any move not
predicted here stops the tranche.

## S1 done-criterion output

    BEFORE
      grounding_reviewer     <<< NONE -> inactive_no_authorized_contract >>>
      judge                  <<< NONE -> inactive_no_authorized_contract >>>
    AFTER
      grounding_reviewer     <<< NONE -> inactive_no_authorized_contract >>>
      judge                  ['groundingverdictwirev1.direct.v1']

    engaged_policy_digest  94bc16e4ef6ff0e4... -> 401f92b72f6b498d...

The `judge` seat now carries behavioral authority; it is the
`reviewer_role` the bridge policy names, so this is the seat whose
absence produced D4. `grounding_reviewer` stays dark because
`reviewer_role` defaults to `judge`; only one of the two is ever seated,
and switching which one is a config choice, not a second seat.

## S2 done-criterion output

    simulation DISABLED           -> 845 bytes, no contract text
    simulation ENABLED, none filed -> 2645 bytes
      contains "def simulate(inputs, rng)"      True
      contains "declared observable missing"    True
      "SIMULATIONS ALREADY FILED ON THIS PROBLEM: none."  True
    simulation ENABLED, one filed  -> 2713 bytes, names sim_bound_sweep/denied

    diff pack_before.txt pack_after.txt  (simulation disabled, pre- vs
    post-change code) -> BYTE-IDENTICAL

The contract text is not re-worded for the critic: the note is built from
`SIMULATION_MODEL_SOURCE_CONTRACT` and
`SIMULATION_REQUESTED_OBSERVABLES_CONTRACT`, the same two constants the
conjecturer's JSON schema carries, so the rule the critic is told and the
rule the harness enforces cannot drift into two wordings (R3).

## S3 done-criterion output

    availability (provider -> knob realized)
      ollama True | openai True | deepseek True | generic False | vllm False
    off-detection
      None False | "none" True | "None" True | " NONE " True
      "low" False | "high" False | 0 False | 2000 False

    ollama profile, reasoning: null
      $ deepreason reason --token-budget 1000 "test"
      REASONING_MUST_BE_DISABLED: provider 'ollama' realizes the reasoning
      knob and this profile has reasoning=None, which does not switch
      thinking off (unset sends no reasoning field, so the model thinks by
      default). Re-run setup with --reasoning none.
      exit 1

    same profile rewritten with reasoning: none  (digest e800ce9c13e48f6e,
    exactly as SPEC F6 predicted)
      $ deepreason reason --token-budget 1000 "test"
      QUALIFICATION_NOT_CONFIGURED: no completed reusable qualification
      exists for this exact subject

The rule stops firing and the launch proceeds to the next check. That
second message is also the empirical confirmation of the R7 conflict: with
thinking off, this subject has no completed qualification.

`generic` and any unlisted provider are unaffected, so the rule binds only
where the knob is real. It binds on LAUNCH (`reason`, `qualify`) and never
on profile load, so every committed run root still reopens.

## S5 done-criterion output

    tests/test_providers.py                                   9 passed
    tests/test_v6_engaged_public_defaults.py::test_the_reviewer_seat_carries_behavioral_authority
      + tests/test_v6_policy_preset.py                       14 passed
    tests/test_crit_batch.py                                 10 passed

Three regression tests, each naming run-c5f901f38208e862f4ce2fe60a26e551:

  - `test_the_reviewer_seat_carries_behavioral_authority` pins the SEAT,
    not the flag: it asserts the role the bridge policy names holds at
    least one contract, and that `argumentative_critic` stays authorized
    (it was never the problem).
  - `test_critic_pack_states_the_simulation_option_and_its_contract`
    asserts the pack carries the same two constant OBJECTS the
    conjecturer's schema carries, so the disclosed rule cannot drift from
    the enforced one, and that a simulation-disabled pack says nothing.
  - `test_thinking_off_rule_knows_where_the_knob_is_real_and_what_off_means`
    pins unset != off and the provider availability table.

One predicted fixture update, minimal:
`test_engaged_bridge_source_enables_the_review_free_grounded_bridge`
pinned `grounding_review: False`. Renamed to `..._the_reviewed_grounded_bridge`
and repointed, because the old NAME asserted the very property the change
removes; leaving the name would have made the test lie.

## S4 done-criterion output

`experiments/live_coin_thinkingoff_2026-07-31/coin_run.sh` sets up with
`--reasoning none`. Predicted profile digest `e800ce9c...` (SPEC F6),
confirmed already by the S3 rewrite test which produced exactly
`e800ce9c13e48f6e`. The ladder reuses the coin run's QUESTION.txt and
dossier byte-for-byte, so the only differences from
`run-c5f901f38208e862f4ce2fe60a26e551` are the three changes in this
tranche.

Checked while wiring it: `application/bridge.py:774/832/929` already pass
`review_adapter` conditioned on `policy.grounding_review`, so turning
review on is wired end to end on the production path and needs no
further change.

## S6 done-criterion output

    first run  : 18 failed, 3154 passed, 7 skipped in 755.10s
    after fixes: 3172 passed, 7 skipped in 698.04s   <- 0 failed

Every one of the 18 fell into a category CHECKLIST predicted, and none
required weakening an assertion. Two families:

**A — the binding rule refused test launches (12).** `test_public_v6_facade`
(5), `test_qualification_tier` (6), `test_shallow_reason` (1) all resolve
through one shared `_profile()` helper whose provider is `openai` with
`reasoning=None`. Fixed in ONE place by giving the fixture
`reasoning="none"`: a fixture that launches must satisfy the same
invariant a real profile does. No assertion changed.

**B — seating the reviewer moved the inventory and the behavior (6).**
Each is a real consequence, recorded rather than papered over:

    grounding_review pin False -> True            (1 test)
    qualification pairs        14 -> 15           (the reviewer pair)
    announced call ceiling   1100 -> 1140         (+40 = 20 cases x 2 calls)
    base battery              840 -> 880
    bridge provider calls        2 -> 3           (review is a call, not free)
    a test-local roles config had to seat `judge`, because a grounded
      bridge with review on refuses to compile without an explicit
      reviewer route (BRIDGE_REVIEWER_ROUTE_REQUIRED)

The production path was checked and is unaffected by that last one:
`preparation._config_for_profile` seats every `V3_CANONICAL_ROLES`, so
only hand-written configs that omit `judge` are affected.

**The measured price of R1a, stated plainly:** +1 qualification pair, +40
qualification calls, +1 provider call per bridge build.
