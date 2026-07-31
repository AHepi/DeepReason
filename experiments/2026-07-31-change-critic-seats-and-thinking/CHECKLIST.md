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

- [ ] S3 (R4, P2) — binding rule: refuse to launch when the provider
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

- [ ] S4 (R5) — thinking off for the live GLM 5.2 profile.
      Site: the ladder's `deepreason setup` invocation gains
      `--reasoning none`. No code change; the field already accepts it.
      Done-criterion: the written `provider.yaml` shows `reasoning: none`
      and a profile digest of `e800ce9c...` (predicted in SPEC F6).

- [ ] S5 — regression tests for S1-S3.
      Done-criterion: the new tests pass and each names what it guards.

- [ ] S6 (C2) — full gate.
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
