# Validation for: implement amendment epochs

Spec: `docs/proposals/AMENDMENT_EPOCHS.md` (operator-designated), sections
"Design", "Why nothing corrupts", "Implementation sketch", "Regression
fixtures". The doc's "As implemented" section is the implementer's own
report and is treated as the object under audit, never as authority.

Branch `claude/amendment-epochs-om0ztb`. **Second pass**, after the
operator's ruling on the first pass's FAIL (REQUEST.md R12a/R12b, R15a,
R1a) and the re-plan in `CHECKLIST.md` (C1..C6). Every acceptance check
was re-run against the amended spec and the amended code; the first
pass's verdict and its two failures are preserved below in
"First-pass verdict (superseded)".

Acceptance checks S1..S16 were derived from the designated spec.

## Acceptance checks

### S1 — R1: `deepreason amend [--attach FILE ...] [--reshape-question "TEXT"] [--root ROOT]`

    $ deepreason amend --help
    usage: deepreason amend [-h] [--attach FILE] [--reshape-question TEXT]
                            [--allow-partial] [--json]
      --attach FILE         file or directory to admit as a supplemental dossier
                            (repeatable)
      --reshape-question TEXT
                            the superseding question; the old one keeps its record
                            and status

R1a corrected the spec's usage line to this CLI's global `--root`
rather than shadowing it with a subcommand duplicate:

    $ sed -n '/^## Design/,/^`amend` refuses/p' docs/proposals/AMENDMENT_EPOCHS.md
        deepreason --root ROOT amend [--attach FILE ...] \
            [--reshape-question "TEXT"] [--allow-partial]
        deepreason --root ROOT continue --budget cycles=N \
            [--token-budget N|unlimited]

    $ deepreason --root <root> amend
    AMEND_EMPTY: an amendment must attach evidence, reshape the question, or both

The documented invocation reaches `amend` and refuses typed, which is
the flag surface working end to end.

: PASS (R1a)

### S2 — R2: `deepreason continue --tokens N` resumes afterwards

    $ deepreason continue --help
    usage: deepreason continue [-h] --budget BUDGET [--token-budget TOKEN_BUDGET]
                               [--expected-manifest-digest EXPECTED_MANIFEST_DIGEST]

R1a also corrected the spec's `continue` line to the real flags
(`--budget cycles=N [--token-budget N|unlimited]`), which is the
pre-existing surface this tranche did not touch. Resumption itself is
demonstrated by S11.

: PASS (R1a, R2)

### S3 — R3, R22: typed refusals

    $ deepreason --root <root> amend
    AMEND_EMPTY: an amendment must attach evidence, reshape the question, or both
    rc=1
    $ deepreason --root <root> amend --reshape-question "   "
    AMEND_QUESTION_EMPTY: a reshaped question must be nonblank

    empty:              AMEND_EMPTY
    blank question:     AMEND_QUESTION_EMPTY
    unchanged question: AMEND_QUESTION_UNCHANGED

Not-at-terminal (a bound v6 root with no terminal commitment):

    tests/test_amendment_epochs.py::test_amendment_refuses_a_run_that_is_not_at_a_terminal_stop PASSED

raising `AMEND_NOT_AT_TERMINAL` and leaving no `run-epochs/` directory.
Partial-chain recovery refusal: see S13.

: PASS

### S4 — R5, R21: supplemental admission as a NEW dossier

    === S4 supplemental dossier is a distinct digest ===
    {'dossier_1': 'b2d35057d5bdf28e', 'dossier_2': '43abd2f6b9195d53',
     'distinct': True, 'epoch_1_dir': 'run-epochs/001'}

    === S4 attached-source records for the new dossier ===
    [{'seq': 10, 'source_id': 'src-02949c9555200745731f54be20b53526e20672a3',
      'dossier_digest': '43abd2f6b9195d53', 'provenance_role': 'import'}]

    === S4 non-import survivors per problem ===
    {'question-3a9417651aaaf3d6bbf0180b9e45e0ef': 1}

The new dossier has its own digest, its own attached-source record, and
the record's artifact carries provenance role `import` — which the
survivor count confirms is excluded from survivors.

: PASS

### S5 — R6, R18: dossier-1 never touched; its citations still verify

    === S5 epoch-0 documents byte-identical after amendment ===
    {'run-manifest.json': True, 'run-input.json': True,
     'evidence-dossier.json': True}

    === S5 old citation verdict before -> after ===
    {'before': ['EVIDENCE_CITATION_VERIFIED'],
     'after':  ['EVIDENCE_CITATION_VERIFIED'],
     'identical_records': True}

Not merely the same code — the full `EvidenceCitationCheckV1` records
compare equal.

: PASS

### S6 — R7: the citation checker consults the UNION of dossiers

    === S6 union: a dossier-2 block resolves through the checker ===
    {'block': 'a751a21234299ead', 'codes': ['EVIDENCE_CITATION_VERIFIED'],
     'union_block_count': 4, 'dossier_1_blocks': 2, 'dossier_2_blocks': 2}

Each dossier is loaded through `load_evidence_dossier`, which validates
it against its own recorded digest before its blocks enter the union.

: PASS

### S7 — R8, R9, R17: question supersession is strictly additive

    === S7 reshaped problem provenance ===
    {'trigger': 'seed', 'from': ['question-3a9417651aaaf3d6bbf0180b9e45e0ef']}

    === S7 old problem record unchanged ===
    {'still_present': True, 'description_unchanged': True}

    === S7 status flips on pre-existing artifacts (must be empty) ===
    {}

    === S7 additive only ===
    {'new_problems': ['question-4b4cac18dffda96a67ae5c61ac392d11'],
     'att_edges_removed': [], 'dep_edges_removed': []}

Provenance is exactly `{trigger: seed, from: [old-question-id]}`. Zero
status flips; no attack or dependence edge removed.

: PASS

### S8 — R10, R24c: the reshaped question wins cycle 0

    === S8 scheduler selection at cycle 0 of the continuation ===
    {'selected': 'question-4b4cac18dffda96a67ae5c61ac392d11',
     'reshaped': 'question-4b4cac18dffda96a67ae5c61ac392d11',
     'wins': True, 'trigger': 'seed'}

: PASS

### S9 — R11: the `run-amendment.v1` record and its five named fields

    {
      "amendment_digest": "5a950ea42b591b65a970d185a95a9a684785e1827673249dff3def66fcfd4da2",
      "created_at": "2026-07-30T10:29:24Z",
      "fence_seq": 9,
      "parent_dossier_digest": "b2d35057d5bdf28e...",
      "parent_manifest_digest": "bc6a5b208e698ca6...",
      "problem_id": "question-4b4cac18dffda96a67ae5c61ac392d11",
      "schema": "run-amendment.v1",
      "seq": 1,
      "successor_dossier_digest": "43abd2f6b9195d53...",
      "successor_manifest_digest": "bc6a5b208e698ca6...",
      "successor_run_input_digest": "f49577f23ea87875...",
      "superseded_problem_id": "question-3a9417651aaaf3d6bbf0180b9e45e0ef",
      "supplemental_dossier_digests": ["43abd2f6b9195d53..."]
    }

All five spec-named fields present: `parent_manifest_digest`,
`successor_manifest_digest`, `supplemental_dossier_digests`,
`problem_id`, `fence_seq`.

: PASS

### S10 — R12a: the successor manifest and run input

    === S10 qualification subject untouched (no requalify) ===
    {'report_bytes_unchanged': True,
     'validate_production_contract_qualification': 'accepted',
     'epoch1_manifest_equals_parent': True,
     'successor_manifest_digest_equals_parent': True}

    === S10 probe: where the superseding run-input lives ===
    {'parent_manifest.run_input_digest':    'ffcc8f6e3f533ebd',
     'successor_manifest.run_input_digest': 'ffcc8f6e3f533ebd',
     'extended_in_manifest': False,
     'successor_run_input_document_digest': 'f49577f23ea87875',
     'successor_run_input_named_by_record': True,
     'epoch1_run_input_problem': 'question-4b4cac18dffda96a67ae5c61ac392d11'}

R12a (operator ruling) replaced R12's mechanism clause. The spec now
reads, at `docs/proposals/AMENDMENT_EPOCHS.md` "Manifest epoch record":

> The manifest itself is copied VERBATIM across the epoch — capability
> policies, allowlists, budgets, and provider profile included — so the
> qualification subject is unchanged and the cached qualification remains
> valid (no requalify). What supersedes is the RUN INPUT and the DOSSIER,
> and the amendment record is what names them: the successor run-input is
> its own canonical, digest-bound document, chained to its parent by this
> record rather than by a re-pointed manifest.

Measured against R12a, every clause holds:

- manifest copied verbatim — `epoch1_manifest_equals_parent: True`,
  `successor_manifest_digest_equals_parent: True`;
- qualification subject unchanged, no requalify —
  `report_bytes_unchanged: True` and
  `validate_production_contract_qualification` accepts the cached report;
- the superseding run-input is its own digest-bound document named by the
  record — `successor_run_input_document_digest: f49577f23ea87875`,
  distinct from the parent's `ffcc8f6e3f533ebd`, carrying the reshaped
  question `epoch1_run_input_problem: question-4b4cac18...`.

`extended_in_manifest: False` is now the specified behavior, not a
deviation. Materializing a distinct successor manifest digest is parked
(R12b) in `PARKED.md` P1.

: PASS (R12a)

### S11 — R13, R2: `continue` resumes the same root on the reshaped question

    tests/test_amendment_epochs.py::test_continuation_runs_the_reshaped_question_under_the_same_root PASSED

which asserts the scheduler worked exactly `[reshaped_id]`, the run
reached `state == "completed"`, `continued.manifest_digest ==
manifest.sha256`, both problems remain in state, and
`verify_root(root)["violations"] == []`.

: PASS

### S12 — R14, R19: append-only ledger, unchanged run identity

    === S12 ledger is append-only (old log is an exact prefix) ===
    True

    === S12 root directory name and manifest digest unchanged ===
    {'root_name': 'amend-root', 'bound_manifest_digest': 'bc6a5b208e698ca6',
     'still_bound': True}

: PASS

### S13 — R4, R15, R22, R24d: one atomic chain; crash recovery

    === S13 the one atomic chain of typed events at/after the fence ===
    {'seq': 9,  'rule': 'Spawn',    'outputs': ['question-4b4cac18dffda96:problem']}
    {'seq': 10, 'rule': 'Register', 'outputs': ['8de3ce0ce6:import']}
    {'seq': 11, 'rule': 'Register', 'outputs': ['6054f02771:import']}
    {'seq': 12, 'rule': 'Register', 'outputs': ['a1c7141d32:import']}

    === S13 fence_seq vs first amendment event ===
    {'fence_seq': 9, 'first_event_at_or_after_fence': 9,
     'events_below_fence_unchanged_count': 9}

Crash simulation:

    S13 staged-then-crashed: crash before the chain line landed
    S13 staged record present: True
    S13 committed chain empty: True
    S13 continue refusal: CONTINUE_AMENDMENT_INCOMPLETE

R15a implemented the bounded supersession. Both recovery shapes are now
covered by regression:

    tests/test_amendment_epochs.py::test_staged_epoch_that_never_reached_the_ledger_is_superseded PASSED
    tests/test_amendment_epochs.py::test_staged_epoch_that_applied_events_refuses_and_names_the_route PASSED
    tests/test_amendment_epochs.py::test_partial_amendment_refuses_continuation_and_completes_on_rerun PASSED

**Nothing applied** (crash before `_apply_ledger_chain`): the first test
asserts the log is byte-identical to before the attempt, the staged
fence still equals the live head, and a *different* amendment supersedes
it outright — the committed chain holds only the new record, the
abandoned question never enters `state.problems`, `verify_root` returns
`[]`, and `prepare_continuation` proceeds.

**Events applied** (crash before `_commit_chain_line`): the second test
asserts `pending.fence_seq < harness._next_seq`, that a different
amendment is refused `AMEND_PENDING_CONFLICT`, and that the refusal names
the route:

    epoch 1 is staged, has already applied ledger events, and cannot be
    replaced; re-run `deepreason amend` with its original inputs to
    complete it, then amend again to open the next epoch

and that the named route works end to end — completing epoch 1, then
opening epoch 2 with the different amendment, chained
(`latest.parent_amendment_digest == first.amendment_digest`) and
`verify_root` clean. The operator dead-end the first pass found is gone.

Nothing is rewritten in either shape: the discarded epoch directory is
pre-commitment staging that no chain line names and no ledger event
refers to.

: PASS (R15, R15a)

### S14 — R16, R20, R24a: piecewise replay validation across the fence

    === S14a verify_root BEFORE amendment ===
    []
    === S14b verify_root immediately after amend (no continuation yet) ===
    []

    === S14 epoch windows and current epoch ===
    {'current_epoch': 1, 'fence_seq': 9, 'events_total': 14}

`_amendment_epochs` yields one `(fence, next_fence, dossier)` window per
epoch and the attached-evidence checks run per window; the chain's
anchoring to the bound manifest, each epoch's document digests, and each
epoch's source blobs are validated.

Note: a `verify_root` taken *mid-continuation* (after `prepare_continuation`
opened epoch 1 but before it committed a terminal) reports
`terminal-authority: TERMINAL_COMMITMENT_REQUIRED`. That is the ordinary
open-epoch state of any resumed run, not an amendment finding; S11's
completed continuation returns `[]`.

: PASS

### S15 — R23: MCP `amend_run` beside `continue_run`

    run tools in order: ['get_readiness', 'start_run', 'run_status',
      'run_result', 'run_findings', 'amend_run', 'continue_run', 'cancel_run']
    amend_run present: True
    adjacent to continue_run: True
    capability areas: ['readiness', 'reasoning_runs', 'continuation',
      'amendment', 'run_information', 'cancellation', 'scratchpad_browsing',
      'grounded_bridge', 'help']
    amendment area: [{'id': 'amendment', 'summary': 'Add evidence or reshape
      the question of a stopped request without discarding what it already
      established.', 'operations': ['amend_run']}]

    tests/test_amendment_epochs.py::test_mcp_amend_run_is_exposed_and_hides_host_paths PASSED

: PASS

### S16 — R24: the four named regression fixtures

    tests/test_amendment_epochs.py::test_amendment_appends_an_epoch_and_edits_nothing PASSED
    tests/test_amendment_epochs.py::test_verify_root_stays_valid_across_the_amendment_fence PASSED        (a)
    tests/test_amendment_epochs.py::test_old_citations_verify_identically_after_the_amendment PASSED      (b)
    tests/test_amendment_epochs.py::test_reshaped_question_wins_the_continuation_first_cycle PASSED       (c)
    tests/test_amendment_epochs.py::test_partial_amendment_refuses_continuation_and_completes_on_rerun PASSED (d)
    tests/test_amendment_epochs.py::test_amendment_refuses_an_empty_or_unchanged_request PASSED
    tests/test_amendment_epochs.py::test_amendment_refuses_a_run_that_is_not_at_a_terminal_stop PASSED
    tests/test_amendment_epochs.py::test_question_only_amendment_keeps_its_parent_dossier PASSED
    tests/test_amendment_epochs.py::test_second_amendment_chains_onto_the_first PASSED
    tests/test_amendment_epochs.py::test_continuation_runs_the_reshaped_question_under_the_same_root PASSED
    tests/test_amendment_epochs.py::test_staged_epoch_record_is_canonical_and_matches_the_chain_line PASSED
    tests/test_amendment_epochs.py::test_cli_amend_reports_the_epoch_and_refuses_typed PASSED
    tests/test_amendment_epochs.py::test_mcp_amend_run_is_exposed_and_hides_host_paths PASSED
    ============================= 13 passed in 50.95s ==============================

Fixture (d) covers the typed refusal and the intact parent epoch; it does
not cover the spec's "fresh chain" supersession, because that is not
implemented (S13).

: PASS

## Full gate

    3128 passed, 7 skipped in 488.53s (0:08:08)

Baseline at `531a7154` was `3110 passed, 7 skipped`; this tranche adds 18
(16 in the first pass, 2 for R15a).
: PASS

## Record-behavior preservation

`verify_root` over all 15 committed run roots under
`experiments/live_research_2026-07-29/`, at `531a7154` (pre-change
worktree) and at the tranche head, re-run after the R15a code change:

    $ diff pre.json post2.json
    IDENTICAL to 531a7154 across all 15 committed roots

Both known-good roots (0 violations) and defect-era roots keep their
exact verdicts — `foreign-criticism` on 5 roots (3, 7, 4, 4, 5
findings), `run-input` on `failed-epoch1-run-9175f0ec`,
`terminal-authority` on `failed-epoch2-run-9175f0ec`. No existing
replay-valid root was invalidated and no defect-era finding was masked.

: unchanged

## Requirement sweep

| R | Verdict | Evidence |
|---|---|---|
| R1 | superseded-by R1a | — |
| R1a | PASS | S1 — spec usage line corrected to the CLI's global `--root`; documented invocation works |
| R2 | PASS | S2, S11 |
| R3 | PASS | S3 |
| R4 | PASS | S13 — one chain, seq 9..12, all at/above the declared fence |
| R5 | PASS | S4 |
| R6 | PASS | S5 |
| R7 | PASS | S6 |
| R8 | PASS | S7 |
| R9 | PASS | S7 |
| R10 | PASS | S8 |
| R11 | PASS | S9 |
| R12 | superseded-by R12a | — |
| R12a | PASS | S10 — manifest verbatim, qualification unchanged, superseding run-input its own digest-bound document named by the record |
| R12b | PASS | C1 — `PARKED.md` P1, successor-manifest digest materialization parked with its structural reason and unpark criteria |
| R13 | PASS | S11 |
| R14 | PASS | S12 |
| R15 | PASS | S13 — fail-closed clause |
| R15a | PASS | S13 — supersession when nothing applied; typed refusal naming the route when events exist; both under regression |
| R16 | PASS | S14 |
| R17 | PASS | S7 |
| R18 | PASS | S5, S6 |
| R19 | PASS | S12 |
| R20 | PASS | S9, S14 |
| R21 | PASS | S4, S6 |
| R22 | PASS | S1, S3, S13 |
| R23 | PASS | S15 |
| R24 | PASS | S16 |

Every requirement is either demonstrated by a pasted acceptance output or
explicitly superseded by an operator-ruled amendment. None is deferred.

## Assumptions carried

Taken during implementation rather than approved beforehand (no `SPEC.md`
existed), surfaced for the delivery:

- **A1** — "the run manifest freezes the question (run-input digest)"
  (spec, blocker 1) was read as removable per-epoch. It is not: the
  controller process state, the capability transition chain, work
  orders, terminal commitments, and replay-validation bindings all bind
  one `(manifest digest, run_input_digest)` pair for a root's life.
  **Resolved** by the operator's R12a ruling; the residue is parked as
  `PARKED.md` P1.
- **A2** — "supersedes it with a fresh chain" was read as unsound
  whenever the staged epoch had already applied ledger events.
  **Resolved** by R15a: unsound only in that case, and supersession is
  now implemented for the case where nothing was applied.
- **A3** — the manifest's frozen attached-evidence budget binds the
  *union* of bound dossiers, not the newest alone. The spec is silent.
  **Still carried.**
- **A4** — a dossier's `problem_ref` belongs permanently to the question
  that admitted it, so a question-only amendment inherits its parent's
  dossier rather than minting one. The spec is silent. **Still carried.**
- **A5** — the reshaped problem's criteria are the parent's criteria
  carried verbatim. The spec is silent. **Still carried.**

A3, A4 and A5 remain assumptions, not requirements. They are behavior the
operator has not ruled on; if any is wrong, it is a change tranche, not a
defect in this one.

## Verdict: PASS

All 16 acceptance checks pass with pasted output. Full gate 3128 passed /
0 failed. `verify_root` verdicts on all 15 committed roots identical to
the pre-change commit. Every requirement demonstrated or
operator-superseded; none deferred.

Routing: `dr-deliver-change`.

## First-pass verdict (superseded)

The first pass returned **FAIL** on two requirements. Kept here because a
validation that quietly rewrites its own history is not a record.

1. **R12 mechanism clause** — the successor manifest did not extend the
   run-input reference (`extended_in_manifest: False`). Implementing it
   as literally specified meant making the manifest and run-input digests
   epoch-varying across `workflow/state.py`, `capabilities/state.py` (a
   frozen surface), `runtime/terminal_authority.py`,
   `runtime/continuation.py`, and ~20 identity checks in
   `invariants.py` — the change workflow's declared stop condition.
   Operator ruled: amend the spec to the record-carried design (R12a) and
   park the digest materialization (R12b).

2. **R15 supersession clause** — no typed route out of a
   staged-but-uncommitted epoch when the operator wanted a *different*
   amendment; `AMEND_PENDING_CONFLICT` with no escape but hand-deleting
   a directory inside a run root. Operator ruled: fix it (R15a). Fixed
   in C4 and under regression.

3. **R1 `--root` placement** — the spec's usage line put `--root` after
   the subcommand; this CLI carries it globally. Operator ruled: correct
   the spec (R1a). Corrected in C3.

## Third pass — post-delivery coverage gaps (R26) and the live attempt (R27)

### S17 — gap 1: the chain and epoch detectors actually fire

`tests/test_amendment_chain_integrity.py`, 36 cases. Every `verify_root`
amendment failure branch now has a test that corrupts exactly one thing
and asserts the specific finding, rather than asserting a clean root:

    unreadable chain                -> amendment-chain, "unreadable"
    non-canonical chain bytes       -> amendment-chain
    forged amendment digest         -> AMENDMENT_RECORD_INVALID + amendment-chain
    chain anchored to another manifest -> amendment-chain, "anchored to another manifest"
    broken parent link              -> AMENDMENT_CHAIN_BROKEN
    non-advancing fence             -> AMENDMENT_CHAIN_BROKEN
    out-of-order sequence           -> AMENDMENT_CHAIN_INVALID
    staged but uncommitted          -> amendment-chain, "staged but never committed"
    missing epoch document          -> amendment-epoch, "documents are unavailable"
    deleted epoch directory         -> amendment-epoch, "documents are unavailable"
    record naming a dossier the epoch lacks -> amendment-epoch, "differ from the record"
    record naming an unregistered question  -> amendment-epoch, "names a question absent"
    swapped epoch dossier           -> amendment-epoch
    foreign epoch manifest          -> amendment-epoch, "differ from the record"
    tampered source blob            -> amendment-epoch / attached-evidence
    tampered staged record          -> AMEND_NOT_AT_TERMINAL naming the staged epoch

All ten `RunAmendmentV1` rejection rules are covered by parametrized
cases. Coverage of `amendment/models.py` moved 84% -> **100%**; the
module total 86% -> **95%**.

Two of these were written expecting one behavior and found another,
which is the point of writing them:

- forging the staged record does not reach `AMEND_PENDING_CONFLICT`; it
  breaks the very authority that let the staged epoch's events cross the
  terminal horizon, so `amend` fails closed at `AMEND_NOT_AT_TERMINAL`
  instead. Correct, but the message pointed at the stop rather than the
  staged epoch, so `_require_terminal_stop` now names the staged epoch
  and the terminal authority's detail code.
- a root that binds evidence its manifest does not authorize is already
  non-conforming before any amendment. The useful property, now pinned:
  amending an already-flawed root reports exactly the flaws it had and
  invents none.

: PASS

### S18 — gap 2: an amendment beside a commitment-bound bridge episode

    test_amendment_and_a_bridge_episode_coexist_past_one_horizon PASSED
    test_a_stray_post_horizon_event_is_still_refused_after_an_amendment PASSED

Built on the bridge suite's own proven root: run a grounded bridge to
`process_status == "success"` with real dispatches, confirm its events
sit past the terminal horizon, then amend the same root. Both post-
terminal authorizations hold together — `derive_terminal_authority` stays
valid, `verify_root_report` stays integrity- and security-valid,
`verify_root` returns `[]`, the `BridgeAction.COMPLETED` episode still
stands, and both questions remain in state.

The negative case matters as much: planting an ordinary conjecturer
artifact past the horizon on an amended root collapses authority with
`TERMINAL_POST_HORIZON_EVENT_UNAUTHORIZED`. Widening the rule to admit
amendments did not turn it into a general licence.

: PASS

### S19 — gap 3: three chained epochs

    test_three_chained_epochs_validate_and_window_correctly PASSED

Three amendments, each attaching and reshaping: sequence `[1, 2, 3]`,
each record's `parent_amendment_digest` naming its predecessor, fences
strictly increasing, each epoch's parent run-input and dossier digests
matching the previous epoch's successor. Four dossiers bound, four
unique sources, four questions on the frontier, `verify_root` clean.
Then the MIDDLE epoch's run-input is deleted and the finding still
comes back — it is not masked by its well-formed neighbours.

: PASS

### S20 — the operator-facing refusal surface

    AMEND_ROOT_UNAVAILABLE            (root is not a directory)
    ADMISSION_PATH_UNAVAILABLE        (attachment path unreadable)
    AMEND_EVIDENCE_NOT_AUTHORIZED     (manifest disables attached evidence)
    AMEND_EVIDENCE_BUDGET_EXCEEDED    (union exceeds the frozen budget)
    AMEND_RUN_ACTIVE                  (operator lock live; released -> lands)
    AMENDMENT_EPOCH_OUT_OF_RANGE      (epoch 0 and epoch 1000)
    AMENDMENT_CHAIN_INVALID           (chain exceeds its size bound)

Each asserts the typed code and that nothing was staged or committed.

: PASS

### S21 — dead exports removed

`epoch_fences`, `epoch_for_event_seq`, `current_manifest`,
`current_run_input`, `current_dossier` deleted (no production caller, no
test); `epoch_manifest_path` made private, since only
`load_epoch_manifest` used it. Public surface 23 -> 18 names, every one
with a caller or a test.

: PASS

### Live run attempt (R27): BLOCKED on the credential

A live amendment run is the right next evidence and I judged it worth
doing. It cannot run: the supplied key does not authenticate for
inference.

    $ curl .../v1/chat/completions -H "Authorization: Bearer $OLLAMA_API_KEY" ...
    HTTP/2 401
    {"error":"Unauthorized"}

Ruled out, in order:

- **Not the proxy.** `$HTTPS_PROXY/__agentproxy/status` reports
  `enabled: true`, `recentRelayFailures: []`; an echo probe confirms the
  `Authorization` header reaches the origin byte-identical
  (`Bearer SENTINEL-VALUE-12345` echoed intact). The 401 comes from
  Ollama's own server (`server: Google Frontend`,
  `x-request-id: 997f81e2-42ad-4242-acda-0da9a53a861b`), not the relay.
- **Not the endpoint or model name.** `glm-5.2` and `glm-5.1` are both
  listed by `/v1/models`.
- **Not a misread of a healthy key.** `/v1/models` returns HTTP 200 for a
  deliberately bogus key too, so that 200 proves nothing; the bogus key
  and the supplied key return the identical `{"error":"Unauthorized"}` on
  `/v1/chat/completions`.

So the key reads as valid-shaped but is not entitled to inference —
expired, revoked, or without inference credit. Nothing in the harness or
this container can work around that, and I will not fake a live result.

The ladder is otherwise ready: setup -> qualify -> reason -> amend ->
continue -> audit, modelled on `selfstudy_run.sh`. It needs one working
credential and roughly 30-40 minutes (qualification against a fresh
subject is ~14 min, ~1160 calls).

: BLOCKED — no live evidence produced, and none claimed

### Third-pass verdict: PASS (offline), live evidence still outstanding

Gaps 1, 2 and 3 are closed with pasted evidence; the dead exports are
gone. The standing live gap from RESULTS segment 8 is unchanged and
remains honestly open.
