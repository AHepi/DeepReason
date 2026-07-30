# Validation for: implement amendment epochs

Spec: `docs/proposals/AMENDMENT_EPOCHS.md` (operator-designated), sections
"Design", "Why nothing corrupts", "Implementation sketch", "Regression
fixtures". The doc's "As implemented" section is the implementer's own
report and is treated as the object under audit, never as authority.

Branch `claude/amendment-epochs-om0ztb` at `0a946726`. No `SPEC.md` /
`CHECKLIST.md` exist (see REQUEST.md's provenance note); acceptance
checks S1..S16 below were derived from the designated spec for this
phase.

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

    $ deepreason amend --root /tmp/nope
    deepreason: error: unrecognized arguments: --root /tmp/nope

`--attach` (repeatable) and `--reshape-question`: PASS.
`--root` after the subcommand: **FAIL (surface)** — this CLI carries
`--root` as a global option (`deepreason --root ROOT amend`), which every
other root-taking subcommand uses. Substantively amend takes a root; the
spec's literal placement is rejected. Recorded, not silently reconciled.

: PASS (flags) / FAIL (literal `--root` placement)

### S2 — R2: `deepreason continue --tokens N` resumes afterwards

    $ deepreason continue --help
    usage: deepreason continue [-h] --budget BUDGET [--token-budget TOKEN_BUDGET]
                               [--expected-manifest-digest EXPECTED_MANIFEST_DIGEST]

The token flag is spelled `--token-budget`, not `--tokens`. This is the
pre-existing `continue` surface, untouched by this tranche; the spec line
describes it loosely. Resumption itself is demonstrated by S11.

: PASS (behavior) / note (spec spells the pre-existing flag `--tokens`)

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

### S10 — R12: the successor manifest

    === S10 qualification subject untouched (no requalify) ===
    {'report_bytes_unchanged': True,
     'validate_production_contract_qualification': 'accepted',
     'epoch1_manifest_equals_parent': True,
     'successor_manifest_digest_equals_parent': True}

    === S10 DEPARTURE probe: does the successor manifest extend run-input? ===
    {'parent_manifest.run_input_digest':    'ffcc8f6e3f533ebd',
     'successor_manifest.run_input_digest': 'ffcc8f6e3f533ebd',
     'extended_in_manifest': False,
     'successor_run_input_document_digest': 'f49577f23ea87875',
     'successor_run_input_named_by_record': True,
     'epoch1_run_input_problem': 'question-4b4cac18dffda96a67ae5c61ac392d11'}

R12 has two clauses and they split:

- **Outcome clause** — "capability policies, allowlists, budgets, and
  provider profile copied verbatim, qualification subject unchanged,
  cached qualification remains valid (no requalify)": **PASS.** The
  epoch-1 manifest is byte-identical to the parent and
  `validate_production_contract_qualification` accepts the unchanged
  cached report.
- **Mechanism clause** — "the successor manifest is the parent manifest
  with ... the run-input reference and dossier list extended":
  **FAIL.** `extended_in_manifest: False`. The successor run-input is a
  real canonical digest-bound document named by the amendment record,
  but the manifest document does not point at it.

No operator words defer the mechanism clause.

: FAIL (mechanism clause)

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

    --- R15 probe: can the operator amend to something DIFFERENT after the crash? ---
      refused: AMEND_PENDING_CONFLICT
      escape hatch in CLI/API to abandon the staged epoch: False

    --- and the identical re-run still completes ---
      completed epoch: 1 staged cleared: True

R15 splits the same way R12 does:

- **Fail-closed clause** — "leaves a typed partial chain that recovery
  refuses to continue past ... nothing is rewritten": **PASS.**
- **Supersession clause** — "a re-run of `amend` supersedes it with a
  fresh chain": **FAIL.** An identical re-run *completes* the staged
  epoch; a *different* one is refused `AMEND_PENDING_CONFLICT` and there
  is no typed way to abandon a staged epoch. The operator is left with
  no route except hand-deleting `run-epochs/NNN/` inside a run root,
  which this project's own rule ("Never edit a committed root's
  contents") forbids. This is an operator dead-end, not a wording
  difference.

: PASS (fail-closed) / FAIL (supersession clause)

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

    3126 passed, 7 skipped in 485.76s (0:08:05)

Baseline at `531a7154` was `3110 passed, 7 skipped`; the change adds 16.
: PASS

## Record-behavior preservation

`verify_root` over all 15 committed run roots under
`experiments/live_research_2026-07-29/`, at `531a7154` (pre-change
worktree) and at `0a946726`:

    $ diff pre.json post.json
    IDENTICAL: verify_root verdicts unchanged on all 15 committed roots

Both known-good roots (0 violations) and defect-era roots keep their
exact verdicts — `foreign-criticism` x5 roots (3, 7, 4, 4, 5 findings),
`run-input` on `failed-epoch1-run-9175f0ec`, `terminal-authority` on
`failed-epoch2-run-9175f0ec`. No existing replay-valid root was
invalidated and no defect-era finding was masked.

: unchanged

## Requirement sweep

| R | Verdict | Evidence |
|---|---|---|
| R1 | PARTIAL | S1 — `--attach`/`--reshape-question` exact; `--root` accepted only as the CLI's global option, not after the subcommand |
| R2 | PASS (note) | S2, S11 — resumption works; spec spells the pre-existing flag `--tokens`, actual is `--token-budget` |
| R3 | PASS | S3 |
| R4 | PASS | S13 — one chain, seq 9..12, all at/above the declared fence |
| R5 | PASS | S4 |
| R6 | PASS | S5 |
| R7 | PASS | S6 |
| R8 | PASS | S7 |
| R9 | PASS | S7 |
| R10 | PASS | S8 |
| R11 | PASS | S9 |
| **R12** | **FAIL** | S10 — outcome clause holds (no requalify); mechanism clause "successor manifest with the run-input reference extended" is not implemented, and no operator words defer it |
| R13 | PASS | S11 |
| R14 | PASS | S12 |
| **R15** | **FAIL** | S13 — fail-closed clause holds; "a re-run supersedes it with a fresh chain" is not implemented and there is no typed way to abandon a staged epoch |
| R16 | PASS | S14 |
| R17 | PASS | S7 |
| R18 | PASS | S5, S6 |
| R19 | PASS | S12 |
| R20 | PASS (see R12) | S9, S14 — record and piecewise validation land; the manifest-superseding half is the R12 failure |
| R21 | PASS | S4, S6 |
| R22 | PASS | S1, S3, S13 |
| R23 | PASS | S15 |
| R24 | PASS | S16 |

## Assumptions carried

No `SPEC.md` existed, so these were assumptions taken during
implementation rather than recorded and approved beforehand. They are
surfaced here for the delivery:

- **A1** — "the run manifest freezes the question (run-input digest)"
  (spec, blocker 1) was read as removable per-epoch. It is not: the
  controller process state, the capability transition chain, work
  orders, terminal commitments, and replay-validation bindings all bind
  one `(manifest digest, run_input_digest)` pair for a root's life. This
  assumption is what R12 fails on.
- **A2** — "supersedes it with a fresh chain" was read as unsound
  whenever the staged epoch had already applied ledger events, because a
  fresh fence would orphan them. The implementation chose fail-closed
  refusal over supersession for every case, including the case where
  nothing was applied yet and supersession would in fact be sound.
- **A3** — the manifest's frozen attached-evidence budget was read as
  binding the *union* of bound dossiers, not the newest alone. The spec
  is silent.
- **A4** — a dossier's `problem_ref` was read as belonging permanently to
  the question that admitted it, so a question-only amendment inherits
  its parent's dossier rather than minting one. The spec is silent.
- **A5** — the reshaped problem's criteria were read as the parent's
  criteria carried verbatim. The spec is silent.

## Verdict: FAIL

FAIL detail:

1. **R12 mechanism clause** (check S10). The successor manifest does not
   extend the run-input reference; `extended_in_manifest: False`.
   Implementing it as specified means making the manifest digest and the
   run-input digest epoch-varying across `workflow/state.py`
   (`apply_decision`), `capabilities/state.py` (transition chain — a
   CLAUDE.md frozen surface), `runtime/terminal_authority.py`,
   `runtime/continuation.py`, and ~20 identity checks in
   `invariants.py`. That is the change workflow's declared stop
   condition ("the spec turns out to require touching frozen-record
   semantics ... qualification subjects") and the spec's own tranche-1
   note ("frozen-surface adjacent: operator approval required").
   **This one needs an operator ruling; it is not a re-plannable step.**

2. **R15 supersession clause** (check S13). No typed route out of a
   staged-but-uncommitted epoch when the operator wants a *different*
   amendment. This one *is* re-plannable without touching any frozen
   surface: allow supersession exactly when the staged epoch has applied
   no ledger events yet (`fence_seq == harness._next_seq`), which is
   sound because nothing would be orphaned, and keep the fail-closed
   refusal when events exist.

3. **R1 `--root` placement** (check S1). Re-plannable, but the smallest
   correct fix may be to amend the spec's usage line rather than shadow
   the CLI's global `--root` with a subcommand duplicate.

Routing: `dr-plan-steps` for (2) and (3); operator decision required for
(1). Not eligible for `dr-deliver-change`.
