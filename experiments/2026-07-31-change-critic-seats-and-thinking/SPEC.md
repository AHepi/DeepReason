# Spec: critic seats, simulation exposure, thinking off

Traces to REQUEST.md R1-R5, C1-C4. Every finding below is from source or
from a measurement run this session; none is recalled.

## Findings

### F1 (answers Q1, and contradicts R1's premise) — the criticising seat was never off

R1 says "all of the critic roles were switched off". The record says
otherwise, and the orchestrator requires the contradiction be reported
rather than silently resolved.

In `run-c5f901f38208e862f4ce2fe60a26e551`, `argumentative_critic` was
`qualified_exact_behavior` with `authorized_contract_ids:
['batch-critic.v2', 'config-referee.v1', 'critic.atomic-target.v1']`. It
made 6 `batch-critic.v2` calls and produced 9 recorded criticisms, two of
which are confirmed correct by independent enumeration. The seat that
criticises was ON and working.

The seats carrying `inactive_no_authorized_contract` were `defender`,
`judge`, `grounding_reviewer`, `property_designer`, `variator`,
`vision_critic` — the seats that ADJUDICATE, plus the ones that generate
alternative material. This is the D4 finding: criticism ran, and nothing
could convert it into a refutation.

### F2 (answers Q2) — they were not "switched off"; they were never wired

`doctor.py:1016`: `if not contract_ids: selected_class =
"inactive_no_authorized_contract"`. The class is a consequence of a seat
being granted zero contracts, not of a switch.

`run_manifest.py:1811-1932`, `_route_seat_behavioral_contract_assignments`,
is the closed inventory. It assigns contracts to exactly:

    conjecturer            <- conjecturer_turn_contract
    argumentative_critic   <- batch_critic_contract (+ config-referee.v1
                              when the referee is enabled)
    bridge.ledger_role     <- bridge_ledger_wire_contract      (grounded bridge)
    bridge.composer_role   <- bridge_composition_contract      (grounded bridge)
    bridge.reviewer_role   <- GroundingVerdictWireV1   ONLY IF grounding_review
    bridge.grounding_repair_role <- GroundingRepairWireV1 ONLY IF repairs > 0
    scratch block/link/guide roles <- scratch.*.compact.v1     (scratch on)

`variator`, `property_designer`, `vision_critic` and `defender` appear in
`manifest.roles` (so the plan emits an entry for them) and appear in NO
branch of that function. They cannot be granted a contract by
configuration, because the v6 control plane has none to grant:
`ControlPlanePolicyV3.contract_versions` (`run_manifest.py:648-660`)
lists bridge catalog/ledger/composition, conjecturer turn, batch critic,
simulation request/result — and nothing for those four roles.

They are v4-era features still gated by live config knobs whose comments
name the requirement: `PROP_PROPOSE_PERIOD` — *"Requires the
property_designer AND judge roles"*; `VISION_CRIT_PER_CYCLE` — *"Requires
the vision_critic role"*; the HV spot-checks that ask `variator` for
whole-content edits. The v6 control plane never grew contracts for them.

**So R1 splits into three pieces of very different size:**

  - **R1a — `judge` / `grounding_reviewer`.** Reachable today by
    configuration: set `bridge.grounding_review = True` (and
    `max_grounding_repair_attempts > 0` for the repair seat). No new
    contract. This is the seat whose absence produced D4.
  - **R1b — `variator`, `property_designer`, `vision_critic`,
    `defender`.** NOT reachable by configuration. Requires new v6 wire
    contracts, new `contract_versions` entries, new assignment branches,
    and new qualification pairs. `contract_versions` is part of the
    manifest schema, which CLAUDE.md freezes ("manifest schemas"). This
    is a stop condition, not a task.
  - **R1c — `argumentative_critic`.** Already on. Nothing to do.

### F3 (answers Q3) — the critic wire has no channel of any kind

`BatchCriticWireV2` (`wire.py:1527`) is exactly
`cases: list[{target_alias, attack, case, counterexample}]`. No
simulation channel, no evidence channel, no context request. Simulation
drafts are ingested only on the conjecture path (`rules/conj.py:1969`,
`output.simulation_proposals if active_v5 or active_v6`).

R2 therefore has two readings with materially different cost:

  - **R2-show** — the critic is SHOWN the simulation contract and the
    proposals the conjecturer filed, so it can criticise a candidate for
    not simulating, or criticise the program itself. Pack text plus a
    critic-side render. No new contract, no capability metering, no
    frozen surface.
  - **R2-file** — the critic may FILE simulation proposals itself. Needs
    a new critic contract version carrying `simulation_proposals`, an
    ingestion path off the conjecture boundary, and per-role capability
    budget metering. The capability-state maps pool all proposals and
    are a named frozen surface (`capabilities/state.py` digests).

### F4 (answers Q4) — "the form of the contract" already exists as text

D2b shipped `SIMULATION_MODEL_SOURCE_CONTRACT` and
`SIMULATION_REQUESTED_OBSERVABLES_CONTRACT` in `llm/wire.py`, and this
session confirmed the first appears verbatim in a live production pack at
char 11,117. R3 for the critic path is satisfiable by rendering those
same two constants — one source of truth, no second wording to drift.

### F5 (answers Q7, R5) — measured: only `reasoning_effort: "none"` turns thinking off

Three live calls to `https://ollama.com/v1/chat/completions`, model
glm-5.2, same prompt ("What is 17*23?"):

    reasoning_effort: "none"   content "391"   reasoning 0 chars    3 completion tokens
    think: false               content "391"   reasoning 296 chars  126 completion tokens
    reasoning_effort: "low"    content "391"   reasoning 321 chars  135 completion tokens

`think: false` is the native `/api/chat` parameter and is ignored by the
OpenAI-compatible endpoint. `"low"` still thinks. Only `"none"` produces a
zero-length reasoning field, and it cuts completion tokens from 135 to 3
on this trivial prompt.

The profile field already accepts it: `reasoning: str | StrictInt | None`
(`provider_profile.py:74`), and `_ollama_reasoning` emits
`{"reasoning_effort": str(value)}`. `deepreason setup --reasoning none`
writes it today with no code change. The house already uses this exact
value for capability probes (`cli/main.py:1456`, `reasoning="none"`, with
the comment "Freeze deterministic decoding").

The current profile's `reasoning: null` means the knob is UNSET, so no
field is sent and glm-5.2 thinks by default. Unset is not off. This is
the mechanism behind the coin run's first conjecture turn returning
`completion_tokens: 24576` — exactly the cap, all of it hidden reasoning.

### F6 (the cost of R5) — measured: it forces a full re-qualification

    reasoning=None    profile_digest bc6ec47224efdcf3236d6f37588bbb55...
    reasoning="none"  profile_digest e800ce9c13e48f6e37338bea69d0691b...
    endpoint_id       provider-profile-bc6ec472... -> provider-profile-e800ce9c...

`qualification_subject_payload` (`qualification.py:277`) closes over
`provider_profile_digest`, so the subject digest moves and the cached
battery no longer applies: the full ~14-minute, ~1160-call qualification
re-runs. CLAUDE.md names "Anything altering qualification subject
digests" a frozen surface requiring explicit operator approval. The same
is true of R1a: enabling `grounding_review` adds a route-seat pair, which
changes `manifest_behavior` and the pair inventory, so the subject digest
moves for that reason too.

R1a and R5 therefore share one re-qualification if done in the same
change, and cost two if split.

### F7 (answers Q5, Q6) — where a binding rule can actually bind

`REASONING_ADAPTERS` (`llm/providers.py:67`) already knows which
providers realise the knob: `deepseek`, `openai`, `ollama` have real
adapters; `generic` has `_no_reasoning_knob`. So "when it's available" is
decidable in-process from the provider string, with no probe.

Candidate enforcement points, cheapest first:

  - **P1 profile validator** — `ProviderProfileV1` rejects a profile
    whose provider has a real reasoning adapter and whose `reasoning` is
    not an off value. Binds at profile creation, so `setup` refuses to
    write a thinking-on profile. Strongest and smallest.
  - **P2 launch refusal** — `reason`/`qualify` refuse to start. Later,
    weaker, but does not invalidate existing committed profiles.
  - **P3 gate test only** — documents, does not bind. Insufficient for
    "binding".

P1 has a consequence to state plainly: every committed provider profile
in this repository has `reasoning: null` and would become invalid, which
would break the reopening of existing roots. P2 does not have that
problem. A P1 variant that binds only on WRITE (setup/create) and not on
READ (loading a committed profile) avoids it.

## Assumptions recorded (smallest reasonable reading, where the words are silent)

A1: "critic roles" is read as the seats that participate in criticism and
its adjudication, not as every unseated role in the manifest. R1c is
already satisfied; R1a is the live gap; R1b is out of reach without a
frozen-surface change.

A2: R4's "binding" is read as enforcement in code, not documentation.

A3: R4's "when it's available" is read as "the provider has a real
reasoning adapter", per F7.

## Decision points (batched to the operator; work is blocked on these)

D-1: R1 scope — R1a only, or R1a + a separate tranche opened for R1b?
D-2: R2 reading — R2-show, or R2-file (frozen surface)?
D-3: R5/R1a cost — is the full re-qualification authorised, and is P1 or
     P2 the binding point for R4?

## Budget (pending D-1..D-3)

R1a + R2-show + R4(P2) + R5 is estimated ~120 changed lines across
`config.py`/`v6_policy.py` (bridge flag), `llm/packs.py` (critic-side
render of the two contract constants), `provider_profile.py` or
`cli/main.py` (the binding rule), plus tests. Within one tranche.

R1b or R2-file each exceed a tranche on their own and touch frozen
surfaces; neither is costed here.
