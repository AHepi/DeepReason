# Validation for: the writer's room — limits, forms, and a census
Phase `dr-validate-change`, 2026-09-06. Base `6b59c2849` (the capture commit;
the predecessor's delivery head d9170e433 beneath it). Branch
`claude/mini-isolation-t3-t5-7tsc6d`.

## Acceptance checks

**S1 (R1, R-fix) — no mandatory section is ever cut; the limit is configurable.**

    $ python -m pytest mini/tests/test_mini_brief_limits.py -q     -> 4 passed
      (red on the old allocation: 'mini:brief-clipped' x2, CHECKLIST step 1)
    live: room run shallow-0b47bc7b090854078ddf7559 -- briefs 27, directive intact 27, clipped 0
      (the D8 root through the same instrument: 19 / 9 / 10)
    $ python -m pytest tests/test_shallow_reason.py -q              -> 14 passed
      (model_profile standard / frontier / compact each reach the engine)

: **PASS**.

**S2 (R2, R5) — the room forms.**

    $ python -m pytest mini/tests/test_mini_room_forms.py -q        -> 3 passed
    mini_form_ids(): 7 (stored + relaxed x3 + room x3); mini.flow.room.v1 binds the room shells,
      both commitment channels OFF, brief limit 12 000; the enumeration test (test_mini_shape_buys_nothing
      limb 2) iterates every registered form -> no score/rank/weight/confidence/priority/authority/severity
    goldens: tests/test_conj_pack_legacy_golden.py + test_crit_pack_legacy_golden.py -> 15 passed

: **PASS**. No status changes anywhere (refuted 0 live and offline).

**S3 (R4) — commitments outside conjecture artifacts, enforced.**

    $ python -m pytest mini/tests/test_mini_room_separation.py -q  -> 1 passed
    $ python proof/mutation_separation.py -> MUTATION CAUGHT (red as required): record text found inside
      a conjecture artifact
    live: assert_separated holds on the room root (RESULTS.md §6)

: **PASS**.

**S4 (R3) — the census.**

    PREREG_CENSUS.md sealed at 482b5f4b5 (sha 40ff8f8e...); census.py unchanged since (sha 0d871946...)
    RESULTS.md: table after/before, the rule clause by clause (3 of 4 hold; exact-dup fails), predictions
      scored, all 46 proposals quoted. No re-run.

: **PASS** as a measure (the rule's own verdict is recorded as it fired).

## Full gate

<<GATE>>

## Record-behavior preservation

No reader, writer or validator changed. Both live roots (D8's and the
room's) verify (0 violations) and replay (digest equal) under the same code.
The one recorded-format-adjacent change is the everything section's notice
wording, which is brief text, not record format.

## Frozen-surface diff

    $ git diff --stat 6b59c2849..HEAD -- src/deepreason/capabilities/state.py src/deepreason/harness.py \
        src/deepreason/invariants.py src/deepreason/run_manifest.py src/deepreason/qualification.py \
        src/deepreason/verification/ src/deepreason/llm/firewall.py
    (no output)

: **PASS**. blast_radius CLEAR at every [COMMIT] (steps 4, 7; T3/T4 moved
no source file but `loop.py`'s three-line fallback, CLEAR below).

## Packaging surface

`src/` changed in one file, `shallow.py` (the profile forwarding); no console
entry point, MCP tool, schema or wheel layout moved. Smokes not re-run;
the predecessor's T6 ran both green on the tree beneath this one.

## Map

    docs_verify FULL at 391d5bb31 (T1's tree): 82 documents, 1419 checks, 6 failed -- the six known rows
    --fast after T2 and after the Traps entry below: the same six; --audit: the one known finding
    new checks: T1 3 (the limits test; the reserve rule's constants; the flow field + refusal),
      T2 1 (the room forms test), T4 1 (the candidate-count fallback, Traps)
    Verified-at: SUB-minireason, SEAM-llm-x-minireason -> 391d5bb31

## Requirement sweep

| R | disposition |
|---|---|
| R1 limits | done (S1) |
| R2 forms | done (S2), stored and relaxed forms untouched |
| R3 census | done (S4), answer recorded as the sealed rule reads it |
| R4 condition | verified before any change; enforced by test (S3) |
| R5 writer's room | honoured: no authority, no status change, refuted 0 |
| R-fix | read as R1 (message 4 names "the limits"); P10 and the storage grant stay parked |

## Assumptions carried

A1–A3 (SPEC). New: the compact count (4) is the fallback for profiles that
declare none.

## Budget

Code 305 + 5 (T4's fallback) against 260; tests 273 + 79 (T3) + 17 (T4)
against 220. EXCEEDED, disclosed and re-baselined at step 7 (SPEC §Budget).

## Verdict: PASS
