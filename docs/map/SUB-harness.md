<!-- DR-SUB-harness -->
Verified-at: 08dcdf3c
Verify: python -m pytest tests/test_replay.py tests/test_persistence_invariants.py -q
Owns: src/deepreason/harness.py
Seams: DR-SEAM-adjudication-x-harness, DR-SEAM-bridge-x-harness, DR-SEAM-capabilities-x-harness, DR-SEAM-harness-x-llm, DR-SEAM-harness-x-manifest, DR-SEAM-harness-x-ontology, DR-SEAM-harness-x-scratch, DR-SEAM-harness-x-verification, DR-SEAM-harness-x-workflow

# The harness — append-only record, event application, materialized state

## What it is

`Harness` is the only writer of a run root and the only code that turns an
intention into a durable event. It validates well-formedness, persists records
to the content-addressed object and blob stores, builds an `Event`, applies it
to the in-memory materialized view, and appends it to `log.jsonl` — in that
order, through one `_commit`/`_apply_event` path shared byte-for-byte with
replay. That sharing is the whole point: reopening a root reconstructs the same
state as the live session that wrote it, which is what makes the log admissible
evidence rather than a diary. The drivers of DeepReason — `rules`, `schools`,
`scheduler`, `llm` — are *callers*; the harness imports none of them, so that
dependency arrow never reverses. The four typed process subsystems are the
deliberate exception: replay cannot rebuild a state whose types it cannot name,
so the harness does import `bridge`, `capabilities`, `scratch` and `workflow`
— but only their event/model/state modules, never a controller or service that
would call back into it. `bridge`, `capabilities` and `scratch` come in at
module level; every `workflow` import (and `bridge.harness`) is deferred inside
a function, which is what keeps the import graph acyclic.
`check: grep -q "final_labels(compute_label0(nodes, att), dep)" src/deepreason/harness.py && ! grep -qE "deepreason\.(rules|schools|scheduler|llm)\b" src/deepreason/harness.py && grep -q "^from deepreason.capabilities.state import CapabilityReplayState" src/deepreason/harness.py && grep -q "from deepreason.workflow.replay import" src/deepreason/harness.py && ! grep -qE "^from deepreason\.(workflow|bridge\.harness)" src/deepreason/harness.py && ! grep -qE "deepreason\.(workflow\.(transaction_service|shadow)|capabilities\.(simulation|research))" src/deepreason/harness.py`

Event application and well-formedness here are a **frozen surface**: see
`DR-INV-frozen-surfaces`. A change that invalidates an existing replay-valid
root is wrong by definition — fix readers, not the record.
`check: grep -q "harness.py. event application / well-formedness" CLAUDE.md && grep -q "harness.py. — event application and well-formedness" docs/map/INV-frozen-surfaces.md`

## Entry points

- `Harness(root)` — open or create a run root; replays every logged event, then
  adjudicates **once** at the end.
- `Harness.at(root, seq)` — read-only time-travel view truncated at `seq`; its
  blob store is fenced to holdout bytes already revealed at that point.
- `register_commitment`, `register_problem` — the two non-artifact formal
  records; `register_problem` auto-pins the Popper battery onto `criteria`.
- `create_artifact` — store content, compute the content-addressed id, register.
- `register_batch` — the real registration path: artifacts *and* explicit
  `(artifact, warrant)` carriage pairs in one event. `register_artifact` is a
  one-entry wrapper; content dedupe still commits when carriage is new.
- `carried_warrant_ids`, `carrier_ids` — read the materialized carriage
  relation (includes carriage recovered from legacy `Artifact.warrants`).
`check: for s in register_commitment register_problem create_artifact register_artifact register_batch carried_warrant_ids carrier_ids recent_events recent_semantic_events semantic_event_clock transitions embed_artifact build_bridge write_workflow_checkpoint workflow_checkpoint_digest reload_durable_authority; do grep -q "def $s(" src/deepreason/harness.py || exit 1; done`
- `record_measure` — the untyped `Measure` vehicle: hv/reach estimates, the
  `addr` reach amendment, and signal-tagged side records.
- `record_llm_calls` — durable accounting for provider calls that registered
  nothing (blocked trials, extra ensemble seats, dropped calls).
- `record_scratch_event`, `record_bridge_event`, `record_capability_transition`
  — the typed process seams for advisory scratch, grounded bridge, and
  capability lifecycles; each revalidates its records before any write.
- `record_control_transition`, `record_transaction_transition`,
  `record_lifecycle_transition`, `record_resume_transition`,
  `record_terminal_commitment` — `Control`-rule seams for the workflow
  controller v2/v3 transaction and v4 stop/resume/terminal authority.
`check: for s in record_measure record_llm_calls record_scratch_event record_bridge_event record_control_transition record_transaction_transition record_capability_transition record_lifecycle_transition record_resume_transition record_terminal_commitment; do grep -q "def $s(" src/deepreason/harness.py || exit 1; done`
- `recent_events`, `recent_semantic_events`, `semantic_event_clock` — bounded
  event windows and the behaviour-visible action clock policy ages on.
- `transitions` — incremental `(seq, artifact, old_status, new_status)` replay
  program over the log, driven by capture detection every cycle.
- `embed_artifact` — content-addressed embedding with a per-process cache.
- `write_workflow_checkpoint`, `workflow_checkpoint_digest` — seal and digest
  the complete authority prefix so a lost log tail is detectable.
- `reload_durable_authority` — discard a pre-lock view and re-replay the root
  inside a process lock's critical section.
- `build_bridge` — delegates to `deepreason.bridge.harness.build_grounded_bridge`.

## State it owns

**On disk, under the run root** (the harness owns the *placement and lifecycle*;
the store implementations live in `deepreason/log/` and `deepreason/storage/`,
which this document does not own):

- `log.jsonl` — the append-only `Event` stream, the only source of truth.
- `objects/` — content-addressed, schema-namespaced immutable records
  (commitments, problems, artifacts, warrants, and every typed workflow,
  bridge, capability and criticism record).
- `blobs/` — opaque content bytes: artifact content, prompts, raw provider
  output, diagnostics, canonical evidence JSON.
- `holdout/` — sealed bytes moved into `blobs/` idempotently by a `Reveal`
  event, so replay reproduces the reveal.
- `workflow-checkpoint.json` — written by `write_workflow_checkpoint`,
  re-verified against a fresh prefix replay on every writable open.
- It *reads* `run-manifest.json` (transaction authority, via
  `run_manifest.MANIFEST_NAME`) and `checkpoint.json` (the generic run
  checkpoint, on resume); it does not write either. `workflow-checkpoint.json`
  is the ONLY durable file the harness itself writes outside the three stores —
  one atomic `os.replace`, and no `write_text`/`write_bytes` anywhere in it.
`check: grep -q 'BlobStore(self.root / "blobs"' src/deepreason/harness.py && grep -q 'ObjectStore(self.root / "objects"' src/deepreason/harness.py && grep -q 'EventLog(self.root / "log.jsonl"' src/deepreason/harness.py && grep -q 'self.root / "workflow-checkpoint.json"' src/deepreason/harness.py && grep -q 'self.root / "holdout"' src/deepreason/harness.py`
`check: grep -q "from deepreason.run_manifest import MANIFEST_NAME, load_run_manifest" src/deepreason/harness.py && grep -q 'run_checkpoint_path = self.root / "checkpoint.json"' src/deepreason/harness.py && grep -q "run_checkpoint_path.read_bytes()" src/deepreason/harness.py && ! grep -qE "(write_text|write_bytes|run_checkpoint_path\.(write|open))" src/deepreason/harness.py`

**In memory, rebuilt from the log on every open:** `state` (an
`EpistemicState`: `artifacts`, `problems`, `carries`, `att`, `dep`, `addr`,
`status`, `hv`, `reach`, `conn`), the `commitments` and `warrants` registries,
and four replay states applied *beside* the formal ontology and never inside it
— `scratch_state`, `bridge_state`, `workflow_state`, `capability_state`. None
of the four participates in `att`, `dep`, warrant carriage, or adjudication.
`check: python -c "import sys; from deepreason.ontology.state import EpistemicState as E; from deepreason.harness import Harness; f=set(E.model_fields); sys.exit(f != {'artifacts','problems','carries','att','dep','addr','status','hv','reach','conn'} or not {'scratch_state','bridge_state','workflow_state','capability_state','commitments','warrants'} <= set(Harness._reset.__code__.co_names))"`

**Derived caches**, pure functions of the append-only history and therefore
extended, never invalidated: `_tail` (bounded at 512 events), `_embed_cache`,
`_verdict_cache`, `_trans_shadow`, and the semantic-clock exclusion set. Live
open replay reproduces state byte-for-byte against the session that wrote it.
`check: python -m pytest tests/test_replay.py::test_replay_reproduces_state_byte_for_byte -q`
`check: grep -q "_TAIL_CAP = 512" src/deepreason/harness.py && grep -q 'key = (getattr(embedder, "model", type(embedder).__name__), aid)' src/deepreason/harness.py`

## Where to change what

| To change... | Edit | Test |
|---|---|---|
| Add a new typed event channel | `Rule` + the payload field in `ontology/event.py`, a `record_*` seam, the matching `_commit` keyword, and the `_apply_event` branch | `tests/test_replay.py::test_replay_reproduces_state_byte_for_byte` |
| What a `Measure` tag means, or add one | the emitting call site **and** `src/deepreason/signals.py` (AST-scanned registry) | `tests/test_signals.py` |
| Warrant admissibility at registration | `Harness._validate_warrant` | `tests/test_trial.py::test_rubric_warrant_without_transcript_rejected` |
| Which status labels come out | `Harness._adjudicate` wiring only; the logic is in `adjudication/` (frozen — `DR-INV-frozen-surfaces`) | `tests/test_replay.py::test_replay_reproduces_state_byte_for_byte` |
| The event window scheduler code sees | `Harness._TAIL_CAP`, `recent_events` | `tests/test_review_fixes.py::test_incremental_transitions_and_event_tail` |
| What counts as a semantic action (age/stop policy) | `_advance_semantic_event_clock`, `semantic_event_clock`, `recent_semantic_events` | `tests/test_workflow_shadow_c0.py::test_semantic_clock_collapses_split_conjecture_call_carrier` |
| Add or rename a durable per-root file | the `self.root / ...` constructions in `__init__`, `_workflow_checkpoint_path`, and the `Rule.REVEAL` branch | `tests/test_persistence_invariants.py::test_time_travel_does_not_create_or_repair_storage` |
| Read-only / time-travel enforcement | `_ensure_writable`, `Harness.at`, the `FencedBlobStore` wiring in `__init__` | `tests/test_persistence_invariants.py::test_time_travel_harness_rejects_every_write_and_changes_no_bytes` |
| Crash behaviour on a failed append | the `except` branch of `Harness._commit` | `tests/test_persistence_invariants.py::test_failed_append_rolls_live_state_back_to_durable_log` |
| Sequence/torn-tail fencing | `deepreason/log/event_log.py` (not owned here); the harness only consumes it | `tests/test_persistence_invariants.py::test_replay_rejects_duplicate_or_gapped_event_sequence` |
| Embedding cache identity | the key expression in `Harness.embed_artifact` | `tests/test_embedder.py::test_embed_cache_is_keyed_by_model` (skips without the neural extra — the grep under *State it owns* is the always-live guard) |

`check: grep -q "^class Rule" src/deepreason/ontology/event.py && grep -q "^class Event" src/deepreason/ontology/event.py && grep -q "^class StateDiff" src/deepreason/ontology/event.py`
`check: python -m pytest tests/test_signals.py -q`
`check: python -m pytest tests/test_trial.py::test_rubric_warrant_without_transcript_rejected -q`
`check: python -m pytest tests/test_review_fixes.py::test_incremental_transitions_and_event_tail -q`
`check: python -m pytest tests/test_workflow_shadow_c0.py::test_semantic_clock_collapses_split_conjecture_call_carrier -q`
`check: python -m pytest tests/test_persistence_invariants.py::test_time_travel_harness_rejects_every_write_and_changes_no_bytes tests/test_persistence_invariants.py::test_time_travel_does_not_create_or_repair_storage tests/test_persistence_invariants.py::test_replay_rejects_duplicate_or_gapped_event_sequence -q`
`check: grep -q "def test_embed_cache_is_keyed_by_model" tests/test_embedder.py`

## Traps

- **Object/blob writes precede the log append, deliberately.** If validation or
  the append fails, those immutable bytes stay orphaned and unreachable — but
  the in-memory view must never outrun the durable log, so `_commit` catches,
  `_reset()`s, and re-replays the durable log before re-raising. Anything you
  add to `_reset` must therefore be reconstructible from the log alone.
`check: python -m pytest tests/test_persistence_invariants.py::test_failed_append_rolls_live_state_back_to_durable_log -q`
- **Replay does not adjudicate per event** (`_apply_event(event,
  adjudicate=False)`); the grounded-extension fixpoint is a pure function of the
  final graph, and per-event adjudication made reopening an N-event log
  superlinear. New state that genuinely needs per-event recomputation cannot
  ride on `_adjudicate`.
`check: grep -q "self._apply_event(event, adjudicate=False)" src/deepreason/harness.py`
- **`_apply_event` sees a provisional event.** `_commit` recomputes
  `state_diff` afterwards and overwrites `self._tail[-1]`; drop that fix-up and
  the in-memory tail carries an empty diff while the log carries the real one.
`check: grep -q "event = event.model_copy(update={.state_diff.: state_diff})" src/deepreason/harness.py && grep -q "self._tail\[-1\] = event" src/deepreason/harness.py`
- **A carriage-only re-registration must not re-bill its LLM call.** In
  `register_batch`, an event that adds only `(artifact, warrant)` pairs leaves
  `llm` unset, because the caller already attached that call to the original
  registration. Symmetrically, a call that registered nothing at all must reach
  the log exactly once via `record_llm_calls`, or replay and `eval_report`
  silently under-count real spend.
- **`Measure` tags are enforced.** A new `record_measure`/`record_llm_calls`
  signal literal that is not registered in `src/deepreason/signals.py` fails
  `tests/test_signals.py`, which AST-scans the tree.
- **Semantic age is not log length.** `Control` receipts do not advance
  `semantic_event_clock`, and a split conjecturer-call `Measure` referenced by a
  later `Conj` event is *replaced by* it rather than counted beside it — using
  raw seq as age would let C1 instrumentation accelerate stop policy.
- **Two live harnesses on one root corrupt it silently.** `EventLog` fences on
  file size and raises `ConcurrentWriterError`; `reload_durable_authority`
  exists so a harness opened before its contender took the process lock discards
  every stale pre-lock assumption inside the critical section.
`check: grep -q "class ConcurrentWriterError" src/deepreason/log/event_log.py && grep -q "concurrent writer" src/deepreason/log/event_log.py && grep -q "st_size" src/deepreason/log/event_log.py && grep -q "def reload_durable_authority" src/deepreason/harness.py`
- **A torn final log line is repaired only on a writable open.** Time-travel
  views and `verify_root` must observe the damage without rewriting bytes;
  `Harness.at` on a missing root raises rather than creating storage.
- **Legacy roots embedded carriage on the artifact.** Replay materializes
  `Artifact.warrants` into `state.carries`, so readers must go through
  `carried_warrant_ids`/`carrier_ids`; reading the artifact field directly
  splits old and new roots into two code paths.
`check: python -m pytest tests/test_replay.py::test_legacy_embedded_warrants_materialize_explicit_carriage -q`
- **The embed cache is keyed by embedder *model*, not class.** It was once keyed
  by class name, which aliased two `NeuralEmbedder`s loading different models
  into one cache entry. (`tests/test_embedder.py` pins this but is module-skipped
  without the neural extra, so the grep check above is the live guard.)
