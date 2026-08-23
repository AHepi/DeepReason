# Validation for: the two-call seat protocol

## Acceptance checks

**S1 (R1, R9) — the protocol module**

    $ python -c "from deepreason.llm.split import plan_split, SplitPlan, deliberation_request, extraction_request, SPLIT_LEG_REASON, SPLIT_LEG_EXTRACT"
    exit 0
    $ python -m pytest tests/test_split_budget_protocol.py -q -k "plan or ceiling or auto_arms or envelope or minimal or frozen or empty_trace"
    11 passed, 11 deselected

PASS

**S2 (R1, R3) — per-request overrides at the endpoint**

    $ python -m pytest tests/test_split_budget_protocol.py tests/test_llm.py tests/test_providers.py tests/test_vision.py tests/test_adapter_attempt_logging.py tests/test_budget.py tests/test_seats_evidence_law.py tests/test_config.py -q
    103 passed in 11.35s

PASS

**S3 (R1, R3, R4, R6, R18) — the split dispatch**

    $ python -m pytest tests/test_split_budget_protocol.py -q
    22 passed

Covered end to end by the full gate below. PASS

**S4 (R1) — export surface / packaging**

    $ git diff --name-only e1ea05e82..HEAD -- pyproject.toml src/deepreason/mcp/ scripts/ src/deepreason/cli/
    (empty)

No console entry point, MCP tool set, schema sha or wheel-layout change. PASS

**S5 (R2) — the Config choice**

    $ python -c "from deepreason.config import Config; c=Config(); print(c.SPLIT_BUDGET_SEAT_PROTOCOL, c.SPLIT_BUDGET_EXTRACTION_TOKENS)"
    auto 512
    $ python -m pytest tests/test_config.py -q
    12 passed

PASS

**S6 (R6, R7) — the typed per-attempt fields** (four, per SPEC Amendment 1)

    $ python -c "from deepreason.ontology.event import LLMAttempt as A; a=A(prompt_ref='blob:p'); assert (a.natural_stop, a.split_leg, a.split_notice, a.split_max_tokens)==(None,'','',None); print('ok')"
    ok

PASS

**S7 (R10, R11) — the regressions**

    $ python -m pytest tests/test_split_budget_protocol.py -q
    22 passed in 0.35s

Twenty-two tests, up from the thirteen SPEC.md specified: R18's two were added
at Amendment 1, and three more were forced by defects the gate found (the
unconstrained deliberation leg, the sampler-enforced stand-down, and the real
glm-5.2 seat actually arming). PASS

**S8 (R7) — the no-consumer proof**

    $ python -m pytest tests/test_seats_evidence_law.py -q
    13 passed in 0.38s

PASS

**S9 (R14) — the map moves in the same commits**

    $ python tools/docs_verify.py
    docs_verify [full]: 62 documents, 982 checks, 4 workers
    docs_verify: 3 failed
      -- all three CON-run-identity.md git-history checks, identical to the
         C6 baseline of "3 pre-existing shallow-clone failures"
    $ python tools/docs_verify.py --audit
    docs_verify --audit: 0 finding(s)

PASS

**S10 (R13) — the requalification cost report**

    e1ea05e82  b9038b84efdea313c3f3f2a8862d8acf180d3938ab3d1bf3588c3585dfe07386
    this tree  b9038b84efdea313c3f3f2a8862d8acf180d3938ab3d1bf3588c3585dfe07386

Byte-identical over the committed fixture. No qualification subject digest
moves; requalification price zero per home. This SUPERSEDES the intermediate
finding of one battery per home, which measured a defective tree — see
RESULTS.md and ERRATA E44. PASS

**S11 (R16) — R-by-R delivery**: owned by `dr-deliver-change`. Pending.

## Full gate

    3857 passed, 6 skipped in 968.20s (0:16:08)

0 failed. The C6 baseline is 3829 passed; the +28 are this tranche's own tests.
Two earlier runs were RED and both failures were real, which is why the gate is
run and not assumed:

    run 1: 40 failed, 3814 passed
    run 2:  1 failed, 3853 passed
    run 3: 3857 passed, 0 failed

PASS

## Record-behavior preservation

Two committed roots, one valid and one not, replayed through
`verify_root_report` on the tranche base and on this tree, with `generated_at`
scrubbed, and diffed:

    IDENTICAL - prior verify_root verdicts unchanged
      run-6472629dbc5d408a733d472040671752 -> valid: True  | epistemic_checks_passed: False
      run-9a6be78e1e79184a0bd89923b957586c -> valid: False | epistemic_checks_passed: False

Single-root replays rather than a sweep, per the operator's 2026-08-22 ruling
retiring the sweep as an instrument. PASS

## Frozen-surface diff

    $ git diff --stat e1ea05e82..HEAD -- src/deepreason/capabilities/state.py \
        src/deepreason/harness.py src/deepreason/invariants.py \
        src/deepreason/run_manifest.py src/deepreason/qualification.py
     src/deepreason/run_manifest.py | 11 +++++++++++
     1 file changed, 11 insertions(+)

NON-EMPTY, and covered by the operator's words. REQUEST.md Amendment 2 quotes
the grant verbatim ("Insertions only, 11 and 0, into the function that exists
for exactly this ... Its effect is to PRESERVE digests, not move them"), minted
as R19. Insertions only, 11 and 0; no schema, no validator, no Pydantic model.
The four other frozen surfaces are untouched. PASS

## Map

    docs_verify:            62 documents, 982 checks, 3 failed : PASS
                            (all three the C6-baseline CON-run-identity
                            git-history checks a shallow clone cannot satisfy)
    docs_verify --audit:    0 finding(s)                       : PASS
    docs_verify --links:    0 dangling reference(s), 62 docs   : PASS
    docs_verify --coverage: 7 seams swept, 16 without a Sweep:
                            header, 2 finding(s)               : PASS (dismissed)

`--coverage`'s two findings name `SEAM-periphery-x-verification.md`
(`amendment/apply.py`) and `SEAM-schools-x-scratch.md` (`informal/trial.py`).
Neither seam, and neither named file, is touched by this tranche; both
pre-date it. Dismissed as pre-existing, not created here.

    docs_verify --stale: 11 -> 5 documents.

Eight were made stale by this tranche and are advanced at step 17 to
`23bb8bf66` — four it edited (`SUB-llm`, `SUB-ontology`, `CON-seats`,
`INV-frozen-surfaces`) and four whose owned files it moved without editing
(`SEAM-llm-x-workflow`, `CON-schools` via `llm/adapter.py` and
`ontology/event.py`; `SUB-manifest`, `SEAM-manifest-x-schools` via
`run_manifest.py`). Stamps advanced only because the FULL run above re-ran all
982 checks green. The five remaining each name a commit from another tranche
and are dismissed as not this tranche's to clear:

    CON-run-identity.md         bce018ae5  all-configs-allowed
    SEAM-evaluation-x-rules.md  1fbf071af, e732d3141  reach rulings
    SEAM-llm-x-scheduler.md     8469d0669  route-lease max_tokens fix
    SUB-evaluation.md           1fbf071af  reach rulings
    SUB-scheduler.md            8469d0669  route-lease max_tokens fix

**New checks added by this change:** three, each mutation-proven before being
written down.
  - `SUB-ontology.md` — the four `LLMAttempt` fields exist with replay-safe
    defaults, AND `natural_stop` occurs nowhere in `src/` outside
    `ontology/event.py` and `llm/`.
  - `CON-seats.md` — a split seat call is still one seat, one lease and one
    authorization; `B_r + B_a == ceiling` with the skew never inverted; the
    two stand-down notices exist.
  - `INV-frozen-surfaces.md` — no `SPLIT_BUDGET_` key reaches
    `engine_config_json`, and both `data.pop` lines are present.

**Record observables added vs sweep probes:** four observables
(`natural_stop`, `split_leg`, `split_notice`, `split_max_tokens`), and NO
sweep probe — justified rather than omitted. The root sweep is RETIRED as an
instrument by operator ruling 2026-08-22 ("it just wastes time"), and CLAUDE.md
states that no tranche may be required to sweep committed roots. The
replacement the same ruling names is what this tranche did: targeted,
mutation-proven regression tests plus single-root replays committed alongside
the change (see Record-behavior preservation above, and the twenty-two tests of
S7).

**Wheel smoke:** packaging surface untouched — smoke not owed. Proven by S4's
empty `git diff --name-only` over `pyproject.toml`, `src/deepreason/mcp/`,
`scripts/` and `src/deepreason/cli/`.

## Requirement sweep

| R | Demonstrated by |
|---|---|
| R1 — reason at B_r, then a non-thinking extraction pass at B_a fed the possibly-truncated trace | S1, S2, S3. `test_the_split_path_extracts_an_answer_from_a_truncated_trace`, `test_the_extraction_leg_is_not_a_thinking_call`, `test_the_deliberation_leg_is_genuinely_unconstrained` |
| R2 — per-profile Config choice, default ON for reasoning-model profiles (glm-5.2), OFF where non-thinking | S5. `test_auto_arms_for_a_reasoning_route_and_not_for_a_non_thinking_one`, and `test_the_shipped_glm_seat_actually_arms` on a REAL compiled setup profile |
| R3 — all configurations compile; typed notice, never refusal | S7. `test_a_provider_that_cannot_disable_thinking_still_compiles`, `test_a_seat_that_cannot_split_records_a_notice_and_behaves_as_before`, `test_a_route_enforced_at_the_sampler_stands_down` |
| R4 — a truncated trace yields an answer instead of an empty seat failure | S7. `test_the_split_path_survives_a_null_completion_on_the_reasoning_leg`, and the before/after pair in `test_the_split_path_extracts_an_answer_from_a_truncated_trace` |
| R5 — read and ledger both research consumption points IN FULL | REQUEST.md's AUTHORITY block; SPEC.md cites Q7's `B_a ~ 512`, the coupling tax, the natural-stop PPV, and the coercion note's light-emission-schema dose-response at the items they govern |
| R6 — natural stop becomes a typed per-attempt field | S6, and `_natural_stop_field` records it on every attempt, split or not |
| R7 — recorded, not acted on; no gate or label may consume it | S8. A reference census plus a mutation test that flips the field and shows no status, label, guard or replay verdict moves. Three mutations shown red |
| R8 — the extraction call's schema is the minimal envelope | S7. `test_the_extraction_request_is_the_minimal_envelope`, asserted as an explicit ABSENCE because the failure mode is accretion |
| R9 — both budgets sit inside the route lease ceiling | S1. `B_a = min(extraction_tokens, ceiling // 2)`, `B_r = ceiling - B_a`, so the sum IS the ceiling by construction |
| R10 — add the regression that the split never exceeds it | S7. `test_neither_leg_nor_their_sum_exceeds_the_route_lease_ceiling` over six ceilings, plus `test_the_wire_budgets_obey_the_same_three_bounds` against what the endpoint really received |
| R11 — offline regression with a synthetic truncated trace, mutation-proven | S7. The same model, undivided, burns all three allowed completions and produces nothing; split, it answers in two |
| R12 — wheel smokes only if the public surface moves | S4. Untouched; smoke not owed, recorded as a decision |
| R13 — state which profiles moved and the requalification price | S10. None moved; zero per home. The intermediate wrong answer is recorded and superseded in RESULTS.md and ERRATA E44 |
| R14 — ring while iterating, full gate at the boundary, docs_verify full, map in the same commits | Full gate 3857/0; docs_verify at the C6 baseline; every map edit rode the commit that changed the behaviour |
| R15 — commit and push every phase boundary | Fourteen commits, each pushed with retry |
| R16 — deliver R-by-R with pasted PROOF | Owned by `dr-deliver-change`. Pending |
| R17 — the eight rowed frozen-surface contacts; no writes to the five surfaces | Superseded in one place by R19; otherwise honored — the frozen-surface diff shows `run_manifest.py` alone |
| R18 — the extraction leg rides the bundle, refused on any repair bundle | S3. `test_the_extraction_leg_is_refused_on_a_repair_bundle`, and `test_a_split_call_under_one_bundle_never_exceeds_its_booked_completion` |
| R19 — the granted `run_manifest.py` contact, two `data.pop` lines and nothing else | Frozen-surface diff: 11 insertions, 0 deletions, that function only |

Every R is demonstrated. None deferred.

## Assumptions carried

- **A1** — "reasoning-model profile" is read as the seat's ROUTE, not
  `ModelProfile`, because the presentation profile carries no statement about
  whether a model thinks. VALIDATED beyond the assumption by
  `test_the_shipped_glm_seat_actually_arms`.
- **A2** — a per-call reasoning override is admissible because it never mutates
  the endpoint, so the frozen lease still verifies. Extended during execution to
  the `json_mode` override, on the same reasoning and for the same
  frozen-lease reason.
- **A3** — the split applies to attempt 0 only; repair turns are
  extraction-shaped by construction.
- **A4** — R7's negative is proved twice: a reference census and a behavioural
  mutation test.
- **A5** — `B_a` defaults to 512, and is a Config value so a home can move it
  without code. Refined during execution: `B_a = min(512, ceiling // 2)` with a
  256 floor, because the flat rule handed a 513-token ceiling's reasoning leg
  one token.

## Verdict: PASS
