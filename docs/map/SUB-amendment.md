<!-- DR-SUB-amendment -->
Verified-at: 08dcdf3c
Verify: python -m pytest tests/test_amendment_epochs.py tests/test_amendment_chain_integrity.py -q
Owns: src/deepreason/amendment/
Seams: 
Seams-undocumented: amendment x application, amendment x harness, amendment x manifest, amendment x periphery, amendment x rules, amendment x run-identity, amendment x verification

# Amendment epochs — reshaping the question of a run that has already stopped

## What it is

A run root binds one question, one evidence dossier and one manifest for its
whole life, and nothing committed to it may ever be edited. Amendment epochs are
how a stopped run nevertheless acquires a reshaped question or more evidence
without minting a new root and throwing away the epistemic state that root
earned. Epoch 0 is the set of documents bound at the root itself; every later
epoch is a directory holding its own complete canonical copies, chained by an
append-only record file and separated from its parent by a declared ledger
sequence — the fence. Events below a fence answer to the parent epoch's
documents, events at or above it to the successor's, which is what keeps replay
validation piecewise and lets an unamended root read exactly as it always did.
The package refuses far more than it accepts, and every refusal is a typed,
durable code; a crash mid-amendment leaves a staged epoch that `continue`
declines to run past rather than a half-state it silently accepts.

Nothing here rewrites a byte. Documents are created through `mkstemp` +
`os.replace`, the chain is opened append-only, and a staged document that
already exists with different content is a refusal, not an overwrite.
`check: sh -c '! grep -nE "open\(\"w|write_text\(|write_bytes\(" src/deepreason/amendment/apply.py src/deepreason/amendment/state.py' && grep -q 'with path.open("ab") as stream:' src/deepreason/amendment/apply.py && grep -q "staged epoch already binds different" src/deepreason/amendment/apply.py`

## Entry points

- `amend_run(root, *, attach=(), reshape_question=None, supplied_by="operator",
  allow_partial=False)` — the package's only write operation. Takes the operator
  locks non-blockingly plus an amendment lock, appends one epoch, returns a
  `deepreason-amendment-result-v1` summary.
- `RunAmendmentV1` and `RunAmendmentV1.create(...)` — the typed epoch record;
  `create` computes `amendment_digest` over the canonical payload, and the model
  validator recomputes and compares it on every load.
- `load_amendments(root)` — the committed chain, structurally validated
  (contiguous `seq`, unbroken digest chain, strictly increasing fences, matching
  parent/successor document digests).
- `staged_amendment(root)` — the record of the one epoch that may be staged but
  uncommitted, or `None`.
- `require_no_partial_amendment(root, *, code)` — fail-closed guard that raises
  `AmendmentError` under the *caller's* code, so `continue` refuses with
  `CONTINUE_AMENDMENT_INCOMPLETE` rather than a generic amendment error.
- `current_epoch(root)` — count of committed epochs; `0` on an unamended root.
- `epoch_directory(root, seq)` and `epoch_workload_path(root, epoch)` — where an
  epoch's bound documents live.
- `load_epoch_manifest / load_epoch_run_input / load_epoch_dossier(root, epoch)`
  — per-epoch resolvers; epoch `0` short-circuits to the root's own documents.
- `verify_epoch_run_input(root, epoch)` — one epoch's run input and dossier
  against their own digests, with every source blob re-resolved in the root's
  shared store.
- `dossier_union(root)`, `union_citable_blocks(root)`, `epoch_problem_ids(root)`
  — the cumulative evidence and question views; these are what the conjecture
  rule reasons against once a root has been amended.
- `AmendmentError(code, message)` — the typed refusal carrying `.code`.
- `amendment_lock(root)` and `record_bytes(record)` — the per-root lock and the
  canonical serialization the chain line and the staged record share.
`check: python -c "import deepreason.amendment as a; [getattr(a, n) for n in ('amend_run','RunAmendmentV1','AmendmentError','current_epoch','dossier_union','epoch_problem_ids','epoch_directory','load_amendments','load_epoch_dossier','load_epoch_manifest','load_epoch_run_input','require_no_partial_amendment','staged_amendment','union_citable_blocks','verify_epoch_run_input')]; from deepreason.amendment.state import amendment_lock, epoch_workload_path, record_bytes"`

An unamended root pays one `exists` check for all of this: with no chain file,
every reader short-circuits and answers as though the package were absent.
`check: python -c "import tempfile; from deepreason.amendment.state import current_epoch, load_amendments, staged_amendment; d = tempfile.mkdtemp(); assert current_epoch(d) == 0 and load_amendments(d) == () and staged_amendment(d) is None"`

## State it owns

On disk, under the run root:

- `run-amendments.jsonl` — the append-only chain, one canonical JSON line per
  committed epoch, bounded at 4 MiB. Its *absence* is the unamended case.
- `run-epochs/NNN/` — one directory per epoch, `001` through `999`, each holding
  a complete document set: `evidence-dossier.json` and its `.sha256`,
  `run-input.json` and its `.sha256`, `run-manifest.json` and its `.sha256`,
  `text-workload.json`, and `run-amendment.json`.
- `.run-amendment.lock` — the amendment lock, held in addition to the operator
  locks.

`run-amendment.json` is staged **last** on purpose: its presence is exactly the
claim that the other seven documents are already durable. A reshaped question is
capped at `MAX_QUESTION_CHARS` (262 144) before any of this is touched.
`check: grep -q 'AMENDMENT_CHAIN_NAME = "run-amendments.jsonl"' src/deepreason/amendment/state.py && grep -q 'AMENDMENT_EPOCH_DIR = "run-epochs"' src/deepreason/amendment/state.py && grep -q 'AMENDMENT_RECORD_NAME = "run-amendment.json"' src/deepreason/amendment/state.py && grep -q 'AMENDMENT_LOCK_NAME = ".run-amendment.lock"' src/deepreason/amendment/state.py && grep -q "_MAX_EPOCHS = 999" src/deepreason/amendment/state.py && grep -q "_MAX_CHAIN_BYTES = 4 \* 1024 \* 1024" src/deepreason/amendment/state.py && grep -q "MAX_QUESTION_CHARS = 262_144" src/deepreason/amendment/apply.py && for s in EVIDENCE_DOSSIER_NAME EVIDENCE_DOSSIER_HASH_NAME RUN_INPUT_NAME RUN_INPUT_HASH_NAME MANIFEST_NAME MANIFEST_HASH_NAME WORKLOAD_NAME AMENDMENT_RECORD_NAME; do grep -q "directory / $s" src/deepreason/amendment/apply.py || exit 1; done; grep -q "Staged last: its presence is exactly the claim" src/deepreason/amendment/apply.py`

It owns no blob storage. Supplemental source bytes go into the **root's**
content-addressed store and are referenced by a second dossier; they are never
copied into the epoch directory, which is why a citation checked against
epoch 0's dossier still verifies after any number of amendments.

In the append-only ledger it appends exactly two kinds of thing, through the
ordinary `Harness` API: the reshaped question as a problem with a `seed` trigger
whose `from` names the id it supersedes, and import-role artifacts for each
source the supplemental dossier admits. Nothing else — no conjecture, no
criticism, no control, no status change — is authorized to cross a terminal
horizon this way. Both appends are content-addressed and therefore idempotent,
which is what lets a byte-identical re-run complete a partly applied epoch.
`check: grep -q "harness.register_problem(" src/deepreason/amendment/apply.py && grep -q "attach_bound_evidence(" src/deepreason/amendment/apply.py && grep -q '"trigger": "seed", "from": \[record.superseded_problem_id\]' src/deepreason/amendment/apply.py && grep -q 'return f"question-{_question_digest(question)\[:32\]}"' src/deepreason/amendment/apply.py`

Every epoch-0 document keeps its exact canonical bytes across an amendment, the
log only grows, and `verify_root` stays clean on both sides of the fence.
`check: python -m pytest "tests/test_amendment_epochs.py::test_amendment_appends_an_epoch_and_edits_nothing" "tests/test_amendment_epochs.py::test_verify_root_stays_valid_across_the_amendment_fence" "tests/test_amendment_epochs.py::test_question_only_amendment_keeps_its_parent_dossier" -q`

## Where to change what

| To change... | Edit | Test |
|---|---|---|
| What an amendment is allowed to carry (a third kind of supersession) | `RunAmendmentV1._identity_and_shape` in `models.py`, then the record construction in `_amend_locked`, `apply.py` | `python -m pytest "tests/test_amendment_chain_integrity.py::test_the_record_model_refuses_incoherent_amendments" -q` |
| Which documents an epoch directory binds, or their staging order | `_stage_epoch_documents`, `apply.py` | `python -m pytest "tests/test_amendment_epochs.py::test_staged_epoch_record_is_canonical_and_matches_the_chain_line" -q` |
| Chain structural validation — sequence contiguity, digest chaining, fence monotonicity | `load_amendments` and `_decode_record`, `state.py` | `python -m pytest tests/test_amendment_chain_integrity.py -q` |
| Whether the *ledger* honours a fence, and the per-epoch replay windows | not here — `_amendment_epochs` in `invariants.py`; see `DR-SUB-verification` | `python -m pytest "tests/test_amendment_chain_integrity.py::test_three_chained_epochs_validate_and_window_correctly" -q` |
| Which post-horizon ledger events an amendment may append | `_apply_ledger_chain` in `apply.py` **and** `_is_amendment_application_event` in `runtime/terminal_authority.py` — both, or the two disagree | `python -m pytest "tests/test_amendment_chain_integrity.py::test_a_stray_post_horizon_event_is_still_refused_after_an_amendment" -q` |
| How a reshaped question's problem id is derived | `_reshaped_problem_id` in `apply.py`, which delegates to `_question_digest` in `preparation.py` (`DR-CON-run-identity`) | `python -m pytest "tests/test_amendment_epochs.py::test_amendment_appends_an_epoch_and_edits_nothing" -q` |
| Whether a continuation actually runs the reshaped question | the epoch-workload branch of the fixed run request in `application/text_runs.py` | `python -m pytest "tests/test_amendment_epochs.py::test_continuation_runs_the_reshaped_question_under_the_same_root" -q` |
| Which dossiers and questions a conjecture may cite after an amendment | `dossier_union` / `union_citable_blocks` / `epoch_problem_ids` in `state.py`, consumed in `rules/conj.py` | `python -m pytest "tests/test_amendment_epochs.py::test_old_citations_verify_identically_after_the_amendment" -q` |
| The attached-evidence budget an amendment must respect | `_check_evidence_budget`, `apply.py` | `python -m pytest "tests/test_amendment_chain_integrity.py::test_amend_refuses_evidence_beyond_the_frozen_budget" "tests/test_amendment_chain_integrity.py::test_amend_refuses_when_the_manifest_does_not_enable_evidence" -q` |
| Which run states may be amended at all | `_require_terminal_stop`, plus the v6/`RunInputManifestV2` guards in `_amend_locked`, `apply.py` | `python -m pytest "tests/test_amendment_epochs.py::test_amendment_refuses_a_run_that_is_not_at_a_terminal_stop" -q` |
| The operator surface — flags, MCP arguments, refusal text | `_cmd_amend` and its `add_parser("amend")` in `cli/main.py`; the `amend_run` branch in `mcp_server.py` | `python -m pytest "tests/test_amendment_epochs.py::test_cli_amend_reports_the_epoch_and_refuses_typed" "tests/test_amendment_epochs.py::test_mcp_amend_run_is_exposed_and_hides_host_paths" -q` |
| The epoch ceiling, chain size bound, or question size bound | `_MAX_EPOCHS` / `_MAX_CHAIN_BYTES` in `state.py`; `MAX_QUESTION_CHARS` in `apply.py` | `python -m pytest "tests/test_amendment_chain_integrity.py::test_epoch_directory_refuses_an_out_of_range_epoch" "tests/test_amendment_chain_integrity.py::test_an_oversized_chain_file_is_refused" -q` |
`check: python -m pytest "tests/test_amendment_chain_integrity.py::test_the_record_model_refuses_incoherent_amendments" "tests/test_amendment_chain_integrity.py::test_a_record_whose_digest_does_not_cover_its_payload_is_refused" "tests/test_amendment_chain_integrity.py::test_epoch_directory_refuses_an_out_of_range_epoch" -q`
`check: grep -q "from deepreason.amendment.state import dossier_union, epoch_problem_ids" src/deepreason/rules/conj.py && grep -q "from deepreason.amendment.state import current_epoch, epoch_workload_path" src/deepreason/application/text_runs.py && grep -q "def _assert_amendment_committed(root: Path) -> None:" src/deepreason/runtime/continuation.py && grep -q "def _is_amendment_application_event(harness, event, problem_ids)" src/deepreason/runtime/terminal_authority.py && grep -q "def _cmd_amend(args) -> int:" src/deepreason/cli/main.py && grep -q 'if name == "amend_run":' src/deepreason/mcp_server.py`

Validation in this package is deliberately **local**: `load_amendments` proves
the chain is well shaped, and whether the ledger obeys the fences it declares is
`verify_root`'s question. The package imports nothing from `invariants.py`.
`check: grep -q "Whether the ledger honours those" src/deepreason/amendment/state.py && grep -q "def _amendment_epochs(" src/deepreason/invariants.py && sh -c '! grep -q "deepreason.invariants" src/deepreason/amendment/apply.py src/deepreason/amendment/state.py src/deepreason/amendment/models.py'`

## Traps

- **A staged epoch forks recovery on one question: did it reach the ledger?**
  Nothing applied means nothing to orphan, so a *different* amendment supersedes
  the staged one outright and its abandoned question never enters the record.
  Once events HAVE applied they belong to that epoch: it is completed by a
  byte-identical re-run, never replaced, and a different amendment becomes the
  NEXT epoch (`AMEND_PENDING_CONFLICT`). The discriminator is whether the staged
  `fence_seq` still equals the live head sequence — not a flag, not a timestamp.
  Reusing the pending record's `created_at` is what makes the completing re-run
  produce the identical digest.
`check: python -m pytest "tests/test_amendment_epochs.py::test_staged_epoch_that_never_reached_the_ledger_is_superseded" "tests/test_amendment_epochs.py::test_staged_epoch_that_applied_events_refuses_and_names_the_route" "tests/test_amendment_epochs.py::test_partial_amendment_refuses_continuation_and_completes_on_rerun" -q`
- **Re-attaching already-admitted content used to be accepted here and then
  rejected by `verify_root`** (regression, PARKED P2). It is now refused up
  front — before any parse, blob write, or staging — as
  `AMEND_SOURCE_ALREADY_ADMITTED`, and the *whole* invocation fails rather than
  a subset being admitted, because silently dropping part of what the operator
  pointed at misrepresents the evidence base. The duplicate test is content
  digest against every dossier in `dossier_union`, so an earlier amendment's
  sources count too.
`check: python -m pytest "tests/test_amendment_epochs.py::test_amend_refuses_a_source_already_admitted_to_this_run" "tests/test_amendment_epochs.py::test_amend_refuses_content_admitted_by_an_earlier_amendment" -q`
- **`successor_manifest_digest` always equals `parent_manifest_digest`.** An
  amendment supersedes the question and the evidence, never routing, policy or
  budget authority — the controller's process state is bound to one manifest
  digest for the life of a root, so the successor manifest is the parent copied
  verbatim. The two fields stay distinct anyway: the fence, not the equality, is
  what makes replay piecewise, and collapsing them would silently authorize a
  manifest swap. The evidence budget is likewise metered over the *union* of all
  bound dossiers plus the supplement, not over the supplement alone.
  A `_require_terminal_stop` failure on a root that also carries a staged epoch
  appends a note pointing at the staged epoch, because the honest diagnosis is
  usually that record and not the stop.
`check: grep -q "parent_manifest_digest=parent_manifest.sha256," src/deepreason/amendment/apply.py && grep -q "successor_manifest_digest=parent_manifest.sha256," src/deepreason/amendment/apply.py && grep -q "the parent copied verbatim and the two digests are equal" src/deepreason/amendment/models.py && grep -q "_check_evidence_budget(parent_manifest, (\*bound, supplement))" src/deepreason/amendment/apply.py && grep -q "may no longer describe the events it applied" src/deepreason/amendment/apply.py`
- **`dossier_union` and `epoch_problem_ids` swallow a missing or unreadable
  epoch and keep going.** They are reader-side unions used during reasoning, so
  a truncated union narrows what a conjecture may cite rather than crashing a
  live run; the finding belongs to `verify_root`, which reports the same missing
  epoch as `amendment-epoch`. Do not add a raise here to "fail loudly" — that
  moves a validation finding into the reasoning path.
- **Chain-line bytes are canonical with `exclude_none=True`.** `_decode_record`
  re-serializes and compares against the stored line, so adding a field with a
  `None` default changes the bytes of every future line while leaving old lines
  decodable — and a field that is sometimes `None` and sometimes not changes
  them conditionally. Both the staged `run-amendment.json` and the chain line
  come from the same `record_bytes`.
`check: python -c "import inspect; from deepreason.amendment import state; s = inspect.getsource(state.dossier_union) + inspect.getsource(state.epoch_problem_ids); assert s.count('except (RunInputError, OSError):') == 2" && grep -q "exclude_none=True" src/deepreason/amendment/state.py && grep -q "amendment record bytes are not canonical" src/deepreason/amendment/state.py`
- **Coherence is enforced by model validators, not by the call site.** A
  question-only amendment must cite its parent's dossier unchanged; a supplement
  must be the successor dossier; `problem_id` and `superseded_problem_id` are
  set together or not at all; the successor run input must be a distinct
  document. A construction that violates any of these never becomes a record.
  On the *load* path that surfaces typed, as `AMENDMENT_RECORD_INVALID`; on the
  *construction* path inside `_amend_locked` it escapes as a raw pydantic
  `ValueError`, which the CLI prints verbatim — so a validator change here can
  replace a typed refusal with a pydantic traceback string. `AMEND_NO_EFFECT` is
  the call-site twin of the distinct-run-input rule and the only one of the four
  with a typed code of its own.
`check: grep -q "an amendment without new evidence keeps its parent's dossier" src/deepreason/amendment/models.py && grep -q "the successor epoch cites its newest supplemental dossier" src/deepreason/amendment/models.py && grep -q "question supersession names both the old and the new problem" src/deepreason/amendment/models.py && grep -q "a successor run input is a distinct document" src/deepreason/amendment/models.py && grep -q '"AMEND_NO_EFFECT"' src/deepreason/amendment/apply.py && python -c "import pydantic, deepreason.amendment as a; k=dict(seq=1,parent_manifest_digest='0'*64,successor_manifest_digest='0'*64,parent_run_input_digest='1'*64,successor_run_input_digest='1'*64,parent_dossier_digest='2'*64,successor_dossier_digest='2'*64,fence_seq=0,created_at='x'); e=None; exec('try:\n a.RunAmendmentV1.create(**k)\nexcept BaseException as x:\n e=x'); assert isinstance(e, pydantic.ValidationError) and not isinstance(e, a.AmendmentError)"`
