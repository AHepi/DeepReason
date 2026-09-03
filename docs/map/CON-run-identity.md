<!-- DR-CON-run-identity -->
Verified-at: 0fd78a0c8
Verify: python tools/docs_verify.py
Owns: src/deepreason/preparation.py, src/deepreason/application/text_runs.py, src/deepreason/runtime/continuation.py, src/deepreason/runtime/progress.py, src/deepreason/amendment/apply.py, src/deepreason/amendment/models.py, src/deepreason/amendment/state.py, src/deepreason/ui/status.py
Seams: 
Seams-undocumented: amendment x run-identity, application x run-identity, harness x run-identity, manifest x run-identity, run-identity x verification

# Run identity and lifecycle — one question, one root, forever

## What it is

A run's identity is a content address, not a name someone chose. Preparation
digests the question, the budget, the provider profile, the frozen policy
preset and (when present) the attached-evidence dossier, and mints
`run-<digest[:32]>` — so the same question under the same configuration lands
on the same directory on any machine, at any hour. Everything the run will
ever produce accumulates inside that one directory as an append-only record,
and nothing in it is ever edited. The lifecycle that follows has exactly four
legal moves: **start** it, **continue** it, **amend** it, or **retire** it.
A fifth exists only for a root that ran and never wrote a terminal —
**finalize** it — and it is a repair, not a move the lifecycle plans for.
Determinism is what makes the fourth move necessary: a relaunch cannot pick a
fresh root by accident, so a leftover root must be deliberately renamed out of
the way. This concept is spread across `preparation.py`, `application/`,
`runtime/`, `amendment/` and `cli/` because identity is minted in one place,
enforced in another, extended in a third, and operated from a fourth.

## Where it lives

| Aspect | File | Symbol |
|---|---|---|
| Run id minted from question + config | `preparation.py` | `RunPreparationService.prepare`, `_request_digest` |
| Where the operator's `--config` is loaded, and the typed refusal for a file that is not a configuration at all | `preparation.py` | `_load_operator_config`, `RunPreparationRequestV1.config_path`, `CONFIG_PROFILE_INVALID` |
| What the identity digest covers | `preparation.py` | `_request_digest` payload, `_REQUEST_DOMAIN` |
| The question digest — a DIFFERENT digest, not part of run identity | `preparation.py` | `_question_digest`, `_QUESTION_DOMAIN` |
| The durable identity record in the root | `preparation.py` | `RunPreparationRecordV1`, `PREPARATION_RECORD_NAME` |
| A conditional sibling snapshot: which seat groups were bound at mint time (Rung S5) | `preparation.py` | `SEAT_BINDINGS_SNAPSHOT_NAME` — written into the prepared root only when at least one `--seat` group is bound; absent, not empty, for a default home |
| Re-opening an existing identity without rewriting it | `preparation.py` | `RunPreparationService._load_existing` |
| Id → root, resolved from the record and never from a path | `preparation.py` | `resolve_managed_run_root` |
| Legal id charset | `preparation.py` | `_RUN_ID` |
| Where managed roots live on disk | `provider_profile.py` + `preparation.py` | `provider_state_dir` resolves `DEEPREASON_HOME` alone; `preparation.py` joins `runs/` onto it |
| One-shot manifest binding | `run_manifest.py` | `bind_run_manifest`, `MANIFEST_NAME`, `MANIFEST_HASH_NAME` |
| Start vs. continue dispatch, and the started-root refusal | `application/text_runs.py` | `TextRunApplicationService.start`, `.continue_run`, `._launch` |
| The terminal file and its readers | `application/text_runs.py` | `TextRunApplicationService.result` (`run-result.json`) |
| Append-only log and content stores | `harness.py` | `Harness.log`, `Harness.objects`, `Harness.blobs` |
| Operational telemetry: the two progress files | `runtime/progress.py` | `ProgressSink`, `ProgressEvent` |
| Status must be derivable from the progress log | `ui/status.py` | `read_run_status` |
| Single-owner locks on a root | `locking.py` | `operator_locks`, `OPERATOR_LOCK_NAMES` |
| Resume preconditions and the stop archive | `runtime/continuation.py` | `prepare_continuation` (`run-stops/`) |
| Typed continuation history | `runtime/continuation.py` | `_continuation_history`, `_validate_typed_history` |
| The amendment record and its chaining rules | `amendment/models.py` | `RunAmendmentV1` |
| Epoch staging, chain commitment, crash recovery | `amendment/apply.py` | `amend_run`, `_amend_locked`, `_stage_epoch_documents`, `_commit_chain_line` |
| Epoch layout and epoch-aware readers | `amendment/state.py` | `AMENDMENT_EPOCH_DIR`, `AMENDMENT_CHAIN_NAME`, `load_amendments`, `current_epoch`, `staged_amendment` |
| Replay windowed by the epoch fence | `invariants.py` | `_amendment_epochs` |
| Whether a run stands at a stop that may be amended | `runtime/terminal_authority.py` | `derive_terminal_authority` |
| The one route to a terminal, for the one launch path | `application/text_runs.py` | `terminalize_text_run` (called by `_worker` and by `finalize_stopped_root`; `cli/` calls no scheduler and no terminalization since 2026-08-13) |
| Where a caller holding a compiled manifest enters | `application/text_runs.py` | `TextRunApplicationService.start_manifest_run` — resolves the manifest and the workload, then IS `start` |
| Bringing a root that stopped without a terminal to one, by appending | `application/text_runs.py` | `finalize_stopped_root` |
| Operator surface | `cli/main.py` | `_cmd_reason`, `_cmd_continue`, `_cmd_amend`, `_cmd_cancel`, `_cmd_finalize` |
| Same surface over MCP, by opaque id | `mcp_server.py` | `_resolve_managed_root` |

## The rules it obeys

**The id is `run-` plus the first 32 hex of a domain-separated request digest.**

`check: grep -q 'f"run-{request_digest\[:32\]}"' src/deepreason/preparation.py`

**The digest covers question, budget, provider-profile digest, policy preset id
and policy preset digest — and nothing time-varying.** No clock, no uuid, no
path enters it, which is the whole reason identity is reproducible. The run
MANIFEST digest is the opposite: it carries `compiled_at`, so it moves between
preparations that the run id does not distinguish.

`check: python -c "import inspect,deepreason.preparation as p;from deepreason.run_manifest import RunManifest;s=inspect.getsource(p._request_digest);assert not any(t in s for t in ('compiled_at','uuid','clock','_QUESTION_DOMAIN')) and '_REQUEST_DOMAIN' in s and 'compiled_at' in RunManifest.model_fields"`

**The seat-bindings snapshot is conditional, never a bare empty file** (Rung
S5): absent when no `--seat` group is bound, so a default home's prepared
root is byte-for-byte unchanged from before this rung.

`check: python -c "import tempfile,pathlib;from deepreason.application.models import RunBudgetIntentV1;from deepreason.cli.doctor import ProductionContractCaseResultV1,run_production_contract_doctor;from deepreason.preparation import SEAT_BINDINGS_SNAPSHOT_NAME,RunPreparationRequestV1,RunPreparationService;from deepreason.provider_profile import ProviderProfileV1,write_provider_profile;d=pathlib.Path(tempfile.mkdtemp());profile=ProviderProfileV1.create(provider='openai',endpoint='https://api.example.com/v1',model_id='m',family='f',context_window_tokens=262144,maximum_completion_tokens=4096,credential_env='DEEPREASON_CRI_KEY');path=write_provider_profile(profile,d/'profile.yaml');executor=lambda manifest:run_production_contract_doctor(manifest,case_executor=lambda m,p,i:ProductionContractCaseResultV1(case_id=f'case-{i+1:03d}',first_pass_valid=True,eventual_valid=True,repair_count=0,semantic_admission=True));service=RunPreparationService(runs_dir=d/'runs',qualification_cache_dir=d/'qc',environ={'DEEPREASON_CRI_KEY':'x'},qualification_executor=executor);req=RunPreparationRequestV1(question='q',budget=RunBudgetIntentV1(cycles=1,token_budget=100),profile_path=str(path));prepared=service.prepare(req);assert not (pathlib.Path(prepared.root)/SEAT_BINDINGS_SNAPSHOT_NAME).exists()"`

**Budget is part of identity.** `--cycles` and `--token-budget` enter
`_request_digest` through `request.budget`, so the same question at a different
budget is a DIFFERENT root — not a relaunch of the old one.

**A dossier digest enters the payload only when evidence is attached**, so
question-only ids stay byte-identical to their historical values. Widening this
unconditionally would rename every existing question-only root.

`check: grep -q 'payload\["dossier_digest"\] = request.dossier_digest' src/deepreason/preparation.py`

**A configuration digest enters the payload on exactly the same terms**
(2026-08-29): only when the operator named a `--config`, so a question-only id
is unchanged, and over the configuration's VALUES rather than the file's bytes,
so reformatting a YAML profile does not mint a second run of one question. Two
different configurations of one question are two roots -- without this, the
second is refused `RUN_ALREADY_STARTED` against the first's root, which is a
launch verb refusing a configuration that compiled.

`check: python -m pytest tests/test_managed_path_config_read.py::test_run_identity_covers_the_configuration -q`

**Preparing the same request twice mutates nothing.** The second call re-opens
the root, re-validates every bound document against `run-preparation.json`, and
leaves file mtimes untouched.

`check: python -m pytest tests/test_run_preparation_service.py::test_preparation_is_idempotent_without_requalification_or_rewrites -q`

**An identity may never be re-pointed at different input.** A conflicting
question, profile or request under the same `managed_run_id` raises
`PREPARATION_INPUT_CONFLICT` before any filesystem write.

`check: python -m pytest tests/test_run_preparation_service.py::test_explicit_managed_identity_rejects_conflicting_input_without_mutation -q`

**A root that has already run may never be started again.** `_launch` refuses
when `progress.jsonl` or `run-result.json` exists, inside the registry lock and
with the operator locks already held, BEFORE `bind_run_manifest` is reached.

`check: python -c "import inspect;from deepreason.application.text_runs import TextRunApplicationService as S;s=inspect.getsource(S._launch);assert s.index('operator_locks(root') < s.index('RUN_ALREADY_STARTED: choose a fresh root or continue_run') < s.index('bind_run_manifest(manifest, root)')"`

**A root binds exactly one manifest for life.** `bind_run_manifest` is
idempotent only for byte-identical canonical bytes; anything else is
`RUN_MANIFEST_CONFLICT`. A surviving `.sha256` sidecar with no manifest file is
itself a binding record and still refuses a different digest.

`check: grep -q 'run root is already bound to a different manifest' src/deepreason/run_manifest.py && grep -q 'run root already records a different manifest digest' src/deepreason/run_manifest.py`

**The root's files divide into evidence and telemetry.** `log.jsonl`,
`objects/` and `blobs/` are the harness's append-only record; `progress.jsonl`
and `run-status.json` are the progress sink's, and are never evidence.

`check: python -c "import inspect;from deepreason.harness import Harness;from deepreason.runtime.progress import ProgressSink;h=inspect.getsource(Harness.__init__);g=inspect.getsource(ProgressSink.__init__);assert all(n in h for n in ('log.jsonl','objects','blobs'));assert all(n in g for n in ('progress.jsonl','run-status.json'));assert not any(n in h for n in ('progress.jsonl','run-status.json'))"`

**`run-status.json` is a projection, not an independent record.** A status file
that is not the last line of `progress.jsonl` is refused rather than believed.

`check: grep -q "run-status.json is not derived from the progress log" src/deepreason/ui/status.py`

**A run is addressed by opaque id, never by operator-chosen path.** `deepreason
reason` refuses any `--root` other than the default; managed run paths are
host-owned, and `resolve_managed_run_root` resolves an id through its record.

`check: grep -q "PUBLIC_REASON_ROOT_FORBIDDEN: managed run paths are host-owned" src/deepreason/cli/main.py`

**The `runs/` segment is not part of `DEEPREASON_HOME`.** `provider_state_dir`
returns the home itself; `preparation.py` is the only place that joins `runs/`
onto it, for both `resolve_managed_run_root` and the service's own `_runs_dir`.
A reader who greps `provider_profile.py` for the layout will not find it.

`check: python -c "import inspect,deepreason.preparation as p;from deepreason.provider_profile import provider_state_dir;assert 'state / \"runs\"' in inspect.getsource(p.resolve_managed_run_root) and 'runs' not in inspect.getsource(provider_state_dir)"`

**`continue` resumes; it never re-specifies.** Its only arguments are
`--budget`, `--token-budget` and `--expected-manifest-digest`. Before resuming
it demands: no staged amendment (`CONTINUE_AMENDMENT_INCOMPLETE`), a
`run-stop.json` whose digest matches (`CONTINUE_STOP_REQUIRED`,
`CONTINUE_STOP_DIGEST_MISMATCH`), a `checkpoint.json` fenced on the manifest
and stop digests (`CONTINUE_CHECKPOINT_REQUIRED`,
`CONTINUE_CHECKPOINT_MISMATCH`), and no live operator lock
(`CONTINUE_RUN_ACTIVE`). The prior stop is archived under
`run-stops/<event_seq>-<digest>.json` before the latest pointer can move.

`check: python -c "import pathlib;s=pathlib.Path('src/deepreason/runtime/continuation.py').read_text();assert all(c in s for c in ('CONTINUE_AMENDMENT_INCOMPLETE','CONTINUE_STOP_REQUIRED','CONTINUE_STOP_DIGEST_MISMATCH','CONTINUE_CHECKPOINT_REQUIRED','CONTINUE_CHECKPOINT_MISMATCH','CONTINUE_RUN_ACTIVE'))"`

**An amendment supersedes the question and the evidence, never the authority.**
The successor epoch's manifest is the parent's copied verbatim — the two
digests are equal by construction — so routing, policy and budget authority
cannot move across a fence.

`check: grep -q 'successor_manifest_digest=parent_manifest.sha256' src/deepreason/amendment/apply.py`

**An amendment appends and edits nothing.** Epoch N lands as a complete
document set under `run-epochs/NNN/` plus one canonical line in
`run-amendments.jsonl`; epoch 0's manifest, run input and dossier keep their
exact bytes forever. Order is fail-closed: stage documents → apply the ledger
chain → commit the chain line.

`check: python -m pytest tests/test_amendment_epochs.py::test_amendment_appends_an_epoch_and_edits_nothing -q`

**Replay stays valid across the fence.** `verify_root` windows the log by
`fence_seq`, validating events below it against the parent epoch's documents
and events at or above it against the successor's.

`check: python -m pytest tests/test_amendment_epochs.py::test_verify_root_stays_valid_across_the_amendment_fence -q`

**A reshaped question is registered as a `seed` problem** carrying
`from: [superseded_problem_id]`, so the scheduler's seed-priority guarantee
gives it first claim on the continuation budget — and a half-committed epoch
blocks the resume outright.

`check: python -m pytest tests/test_amendment_epochs.py::test_reshaped_question_wins_the_continuation_first_cycle tests/test_amendment_epochs.py::test_partial_amendment_refuses_continuation_and_completes_on_rerun -q`

**Retirement is a git rename of a committed root, not a code path.** Nothing in
`src/` renames or deletes a run root. The recorded instance is the self-study
ladder: five directories, all carrying the same `managed_run_id`, exactly one
of which still matches its own directory name.

`check: python -c "import json,glob,os;ps=sorted(glob.glob('experiments/live_research_2026-07-29/selfstudy/runs/*/run-preparation.json'));ids={json.load(open(p))['managed_run_id'] for p in ps};assert len(ps)==5 and len(ids)==1 and sum(os.path.basename(os.path.dirname(p))==json.load(open(p))['managed_run_id'] for p in ps)==1"`

**Only two of those four retirements are recorded as git renames.** Whole-commit
rename detection over the ladder's `runs/` directory finds exactly two:
`a7cb7dfb` → `failed-epoch1` (buried inside an unrelated commit) and `1637e808`
→ `failed-epoch2` (the only rename commit whose subject announces what it is
doing). `completed-epoch3` and `failed-epoch4` entered the tree as fresh adds
whose old `run-<id>` path was removed in a *later* commit — for epoch3 the copy
landed in `6a8758a5` and the delete followed in `f304fec1`, so a commit whose
subject reads "retire ... as epoch3" contains no rename at all. That is the
operation CLAUDE.md warns against, preserved here as evidence. Do not use
`git log --follow` to audit this: `--follow` traces every one of the four back
through the shared `run-<id>` ancestor path and reports a rename for all of
them, including the two that were never renamed.

`check: git log -M --diff-filter=R --name-status --format= -- experiments/live_research_2026-07-29/selfstudy/runs/ | grep -o 'runs/[a-z0-9-]*run-9175f0ecb055e57455af3c50df153c5a/run-manifest.json' | sort -u | tr '\n' ' ' | grep -qx 'runs/failed-epoch1-run-9175f0ecb055e57455af3c50df153c5a/run-manifest.json runs/failed-epoch2-run-9175f0ecb055e57455af3c50df153c5a/run-manifest.json runs/run-9175f0ecb055e57455af3c50df153c5a/run-manifest.json '`

`check: git log -1 --format=%s 1637e808 | grep -qi retire`

`check: test -z "$(git show -M --diff-filter=R --name-status --format= f304fec1)" && git log -1 --format=%s f304fec1 | grep -qi "retire.*epoch3" && git show --name-status --format= 6a8758a5 -- experiments/live_research_2026-07-29/selfstudy/runs/completed-epoch3-run-9175f0ecb055e57455af3c50df153c5a/run-manifest.json | grep -q "^A"`

## Where to change what

| To change... | Edit | Test |
|---|---|---|
| what enters the deterministic run id | `preparation.py` `_request_digest` (see Traps — this renames roots) | `tests/test_run_preparation_service.py` |
| what a re-prepared identity re-validates | `preparation.py` `RunPreparationService._load_existing` | `tests/test_run_preparation_service.py::test_preparation_is_idempotent_without_requalification_or_rewrites` |
| the refusal when a root has already run | `application/text_runs.py` `TextRunApplicationService._launch` | `tests/test_application_text_runs_d0.py` |
| what `continue` demands before resuming | `runtime/continuation.py` `prepare_continuation` | `tests/test_continuation.py` |
| the amendment record's shape or chaining rules | `amendment/models.py` `RunAmendmentV1` | `tests/test_amendment_chain_integrity.py` |
| what an amendment may supersede, and its staging order | `amendment/apply.py` `_amend_locked`, `_stage_epoch_documents` | `tests/test_amendment_epochs.py` |
| the progress/status file contract | `runtime/progress.py` `ProgressSink` | `tests/test_progress.py` |
| how replay windows events by epoch fence | `invariants.py` `_amendment_epochs` — FROZEN, see `DR-INV-frozen-surfaces` | `tests/test_amendment_chain_integrity.py` |

## Traps

- **`finalize` reached a terminal and `run-status.json` went on saying
  `running`.** `run-status.json` is `progress.jsonl`'s last line, and
  terminalization writes the LOG; `finalize_stopped_root` called
  `terminalize_text_run` without emitting a progress record, so a root it
  successfully finalized kept whatever state the killed process had left — which
  is `running` on every root `finalize` exists for. Every reader over that file
  then described a finished run as in flight, `deepreason stop-report`'s
  continuability section included, which answered `continue: UNKNOWN — the run
  is in state 'running'` about a root standing at a valid terminal. Observed on
  P-A2 epoch 4 (`63e48f57415d05323b608a84f138ee5c22c274d7d8ebccc2e219b613d7c3a722`,
  `finalize` rc=0, status still `running`) and reproduced on the stub. FIXED
  2026-09-03 (`experiments/2026-09-03-defect-stopped-run-resumption/`). The
  emission is best-effort by design: the terminal is already durable in the log
  when it runs, so a progress-write failure must not un-finalize the root.
`check: grep -q "ProgressSink" src/deepreason/application/text_runs.py && python -c "import inspect; from deepreason.application.text_runs import finalize_stopped_root as f; s = inspect.getsource(f); assert 'ProgressSink(' in s and 'activity=\"finalized\"' in s, 'finalize no longer emits a progress record: run-status.json will keep the killed process state'"`
- **Two different things are called `run_id`.** `progress.jsonl` and
  `run-status.json` carry `run_id = manifest.sha256`; the CLI's `reason` payload
  and every MCP handle carry `run_id = managed_run_id`. They are never equal.
  The manifest digest embeds `compiled_at`, so two preparations of the same
  question in two `DEEPREASON_HOME`s share a managed id and differ in manifest
  digest. Monitoring that greps `run_id` out of `progress.jsonl` and compares it
  to the directory name will never match.
- **Reading `RUN_ALREADY_STARTED` as "the run is still running".** It is not a
  liveness error. Liveness is `RUN_ALREADY_RUNNING` (a live thread in the
  registry, or a busy operator lock). `RUN_ALREADY_STARTED` says only that
  `progress.jsonl` or `run-result.json` already exists in the root — which is
  the normal state of a finished or crashed run, and the signal to retire,
  continue, or amend.
- **Assuming a root that ran real cycles can be continued or amended.** It can
  only if its launch path wrote a terminal. `deepreason run --run-manifest`
  did not, until 2026-08-13: grounded-extension run `8e22d0431fd2b98d`
  completed 24 cycles and then refused `AMEND_NOT_AT_TERMINAL`,
  `CONTINUE_STOP_REQUIRED` and `RUN_RESULT_NOT_READY`, because terminal
  authority never left `current_open_uncommitted`. Fixed that morning by
  making both launch paths call the same `terminalize_text_run`, and the
  same day by removing the second launch path altogether
  (`experiments/2026-08-13-change-single-run-path-unification`): `deepreason
  run --run-manifest` is a rendering shell over
  `TEXT_RUN_SERVICE.start_manifest_run`, so there is no longer a path that
  COULD skip the sequence. `deepreason finalize` still repairs a root
  stopped before the fix — by appending, never by editing. The check is a
  negation for that reason: a scheduler call reappearing in `cli/main.py`
  is the defect returning.
`check: ! grep -q "run_scheduler" src/deepreason/cli/main.py && grep -q "start_manifest_run" src/deepreason/cli/main.py && grep -q "^def finalize_stopped_root(" src/deepreason/application/text_runs.py && grep -q '"finalize"' src/deepreason/cli/main.py && python -m pytest tests/test_lifecycle_operation_parity.py -q`
- **Assuming terminal authority notices a forged record. It does not, and
  neither verb consults the replay verdict at all.** Measured 2026-08-30 on
  committed root
  `experiments/2026-08-13-defect-controller-steering-inert/failed-epoch1-run-8e22d0431fd2b98d`:
  flipping ONE byte of the provider endpoint recorded in `log.jsonl` leaves
  `derive_terminal_authority` reporting `current_valid_committed` and `amend`
  PASSING, while `verify_root` reports `frozen-route` and `attempt-route` —
  both SECURITY-channel findings. The same one-byte forgery of an
  `amend_ready` root (`experiments/2026-08-27-pc2b-symmetric-reasoning/run`)
  buys the WHOLE sequence: `amend` accepts and commits epoch 1, and `continue`
  then accepts `seq=0` — measured 2026-08-30, re-runnable as that tranche's
  `proof/forge_amend_ready.py`. Census of the same day: 16 of 59 committed
  roots pass amend's entire precondition while their own
  `REPLAY_VALIDATION.json` publishes `valid: false` (`proof/census.json`). The
  stored verdict is not a sound fallback either: on four of those sixteen a
  canonical forge of `valid: true` is UNDETECTED, because
  `derive_terminal_authority` skips `_validate_result_projection_binding`
  whenever the published result equals the fail-closed pending projection.
  FIXED 2026-08-31 (`experiments/2026-08-31-defect-jailbreak-gate-closure`):
  both verbs now RE-DERIVE the record and refuse typed —
  `CONTINUE_RECORD_NOT_VERIFIED` and `AMEND_RECORD_NOT_VERIFIED`, each naming
  the failed checks — placed last among their preconditions and before their
  first write, so nothing lands in a tampered root. The same probe now reads
  `jailbreak_open: False` while its intact arm still accepts both verbs.
  The gate asks a NARROWER question than the 2026-08-30 attempt, which is why
  that attempt was reverted and this one is not: it refuses on the SECURITY
  channel only. That was the difference between eight red lifecycle tests and
  zero. The states the product supports on purpose — a partially applied
  amendment mid-recovery (`amendment-chain`), a bound but unintroduced source
  that `amend` exists to admit (`attached-evidence`), and any root that is
  merely incomplete or not a v6 record (`run-input`, `run-manifest-hash`,
  `terminal-authority`, `open`) — are all `integrity`, and all still continue
  and amend. What is NOT gated, and is the honest residue: security findings
  the report DERIVES rather than replays. On the largest committed root those
  number 494 and are version skew, not tampering, which is why gating on them
  was rejected (`experiments/2026-08-31-defect-jailbreak-gate-closure/proof/
  big_root_channels.json`).
`check: python -c "import pathlib; c=pathlib.Path('src/deepreason/runtime/continuation.py').read_text(); a=pathlib.Path('src/deepreason/amendment/apply.py').read_text(); assert 'CONTINUE_RECORD_NOT_VERIFIED' in c and 'record_verification_refusal' in c and 'AMEND_RECORD_NOT_VERIFIED' in a, 'the integrity gate was removed from a verb: it is the 2026-08-29 security clause, not a convenience'" && python -m pytest tests/test_jailbreak_gate.py -q`
- **Changing the budget to "re-run the same question".** Budget is inside the
  identity digest, so a different `--cycles` mints a different root and a fresh
  qualification-cached preparation. That is often what an operator wanted, and
  never what they expected.
- **Expecting `--config` to be free of the identity.** Since 2026-08-29
  (tranche `experiments/2026-08-29-defect-managed-path-config-read/`, defect
  P14) the configuration is part of the run id, so changing one switch and
  re-asking the same question mints a DIFFERENT root rather than reopening the
  old one -- the same surprise budget has always carried. Before that tranche
  the file was never read, so this could not bite; the reason it must bite now
  is the alternative, which is two differently-configured runs colliding on one
  id and the second being refused against the first's root.
- **Retiring a root without committing the rename first.** CLAUDE.md's rule —
  `git mv run-<id> failed-epochN-run-<id>`, COMMIT THE RENAME FIRST — exists
  because the cloud container can roll back to a stale checkout, restoring the
  old directory name while the relaunch is already in flight. The self-study
  ladder retired four roots; only `1637e808` ("retire attempt-4 failed root as
  epoch2 to free run identity") did it the prescribed way, as a single
  rename-and-commit. See the retirement rule above for what the other three
  actually look like in the history.
- **Expecting a retired root to still resolve by id.** The rename does not touch
  `run-preparation.json`, so the record still names the original
  `managed_run_id` while the directory does not. `resolve_managed_run_root`
  refuses it with `MANAGED_RUN_IDENTITY_MISMATCH`. That is the intent: a retired
  root is evidence, openable by path for `verify_root` and replay, not a run.
- **Expecting `amend` to hand back a fresh identity.** It does not. The root,
  the bound manifest digest and the managed id are all unchanged; only
  `current_epoch` advances. A ladder that keys on the root name observes nothing.
- **Pinning a manifest digest compiled from live repository paths.** Identity
  covers the attached-evidence dossier, so a configuration that binds local
  documents has those documents' BYTES inside its digest, through exactly one
  channel: dossier bytes → `evidence_dossier_digest` → `run_input_digest` →
  `manifest.sha256`. The grounded-extension configuration
  (`experiments/2026-08-12-live-grounded-extension-expansion/build_manifest.py`,
  `DOSSIER_PATHS`) binds six local files, two of them map documents —
  `docs/map/CON-warrants-and-attacks.md` and `docs/map/SUB-adjudication.md`. Two
  tests in `tests/test_single_run_path.py` compared a fresh compile of that
  configuration against a hard-coded `8e22d0431fd2b98d…`, which made every
  SCHEMA.md-mandated edit to either document look like a run-identity
  regression, and the digest mismatch named no cause. It was misdiagnosed twice
  — once as a deleted enum, once as a container cache — before
  `experiments/2026-08-16-defect-manifest-sha-doc-coupling` settled it with an
  A/B probe: editing a document inside `DOSSIER_PATHS` moves all three digests
  together, editing a map document outside it moves none of them. Fixed
  2026-08-16, in the tests alone: the configuration half is compared field by
  field against the live run's committed `run-manifest.json` (everything except
  `run_input_digest`), the evidence half is compared against bytes the test
  freezes in its own `tmp_path`, and the sensitivity is asserted as CORRECT so
  it is not re-diagnosed a third time. The rule: a digest may be pinned only
  against inputs the pinning test owns.
`check: test "$(grep -c 'GROUNDED_MANIFEST_SHA256' tests/test_single_run_path.py)" = 2 && grep -q 'run-manifest.sha256' tests/test_single_run_path.py && python -m pytest tests/test_single_run_path.py -q -k sensitivity`
- **Deleting `run-epochs/NNN/` to clear a half-committed amendment.** Recovery
  depends on whether the staged epoch reached the ledger. If it applied events,
  `amend` refuses a different amendment with `AMEND_PENDING_CONFLICT` and only a
  byte-identical re-run completes it; if it applied none, a different amendment
  discards the staging itself. Hand-deleting the directory in the first case
  orphans committed events.
