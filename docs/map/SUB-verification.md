<!-- DR-SUB-verification -->
Verified-at: e6badeead
Verify: python -m pytest tests/test_chaos_invariants.py tests/test_r0_terminal_verification.py tests/test_verifier_registry.py tests/test_cli_verifiers.py -q
Owns: src/deepreason/invariants.py, src/deepreason/verification/, src/deepreason/signals_read.py
Seams: DR-SEAM-harness-x-verification, DR-SEAM-periphery-x-verification
Seams-undocumented: adjudication x verification, amendment x verification, application x verification, capabilities x verification, llm x verification, manifest x verification, run-identity x verification, scratch x verification, verification x warrants-and-attacks, verification x workflow

# Verification — replay validation of a run root, and the pinned mechanical verifiers

## Seams

| Side | Status | What the agreement is (one line) |
|---|---|---|
| `DR-SEAM-harness-x-verification` | documented | the harness promises everything a run knows is reconstructible from `log.jsonl` and the two content-addressed stores, and that the live session and a replay agree |
| `DR-SEAM-periphery-x-verification` | documented | for every source bound into a run's identity, the writer's claim and the verifier's re-derivation must match |
| adjudication x verification | undocumented | real, confirmed from the adjudication side: `invariants.py` re-derives `dep` and reruns `toposort` rather than trusting the recorded graph, and `verification/report.py` hosts the adjudication-blindness detector adjudication cannot host itself |
| amendment x verification | undocumented, one-directional | real, confirmed from the amendment side: `invariants.py`'s `_amendment_epochs` decides whether the LEDGER honours the fences an amendment declares; `amendment/` imports nothing from `invariants.py` at all |
| capabilities x verification | undocumented | real, confirmed from the capabilities side: this document's own claim names "the replay validator" as machinery both capability types share |
| llm x verification | **deliberately absent** | confirmed from the llm side: `llm/`'s own check proves it never imports `verification` |
| verification x warrants-and-attacks | undocumented, likely real | plausible: `DR-SUB-adjudication`'s Traps section already names a `verify_root` failure mode (`carry-warrant`) tied directly to `DR-CON-warrants-and-attacks`'s "no warrant, no attack edge" chain |
| manifest x verification | undocumented | not evidenced here either way — candidate pair, not yet analyzed (consistent with `DR-SUB-manifest`'s own Seams table) |
| application x verification | undocumented | not evidenced here either way — candidate pair, not yet analyzed (consistent with `DR-SUB-application`'s own Seams table) |
| run-identity x verification | undocumented | not evidenced here either way — candidate pair, not yet analyzed |
| scratch x verification | undocumented | not evidenced here either way — candidate pair, not yet analyzed |
| verification x workflow | undocumented | not evidenced here either way — candidate pair, not yet analyzed |

## What it is

Two things share this document because they answer the same question from
opposite ends: is a claim admissible? `invariants.py` answers it about a whole
run root — it re-derives state from the append-only log twice, cross-checks
every durable projection against the log that produced it, and returns typed
findings. `verification/` answers it about one bounded computation — a Lean
kernel run, a sandboxed simulation, a declared test battery over a patched
workspace — and returns an immutable receipt. Neither writes to the run root and
neither touches the argument graph: replay validation is read-only, and a
verifier receipt is process evidence that some *other* subsystem must convert
into a warrant. `verification/report.py` bridges the two ends by re-channelling
`verify_root`'s flat finding list into five independent dimensions, of which
only two decide validity.
`check: sh -c '! grep -nE "write_text|write_bytes|open\(" src/deepreason/invariants.py'`

Both halves are a **frozen surface**: see `DR-INV-frozen-surfaces`. The finding
shape and the check names are compared across recorded roots and across time, so
a rename silently reinterprets every stored verdict.
`check: grep -q "def verify_root(root: Path, meter_total: int | None = None) -> dict:" src/deepreason/invariants.py`

## Entry points

- `verify_root(root, meter_total=None)` — the whole battery over a run root.
  Returns `{"violations": [{"check", "detail"}, ...], "stats": {...}}`. `check`
  is drawn from a fixed vocabulary of typed names, never free text; only
  `detail` varies.
- `verify_root_report(root, meter_total=None, allow_missing_terminal=False)` —
  the v2 adapter: runs `verify_root`, classifies each finding into
  integrity / security / completion / epistemic / operational, then adds
  terminal, authority, model-execution, transaction and blindness findings that
  the log alone cannot express.
- `verify_post_commit_report(root, meter_total=None)` — the same report with the
  root's own stored verification summary excluded, for projecting a terminal
  after its commitment exists.
- `VerificationReportV2.valid` / `.summary_payload()` — `valid` is
  authority-only (integrity and security empty); `summary_payload()` is the
  bounded `verification.summary.v2` block embedded in `run-result.json`.
`check: for s in verify_root_report verify_post_commit_report _legacy_channel _terminal_findings _terminal_authority_findings _model_execution_findings _transaction_findings _adjudication_blindness_findings valid summary_payload; do grep -q "def $s(" src/deepreason/verification/report.py || exit 1; done`
- `_amendment_epochs(root, manifest, fail, problems)` — validates the amendment
  chain and returns the `(fence_seq, next_fence_seq, dossier)` window per epoch,
  which is what makes the rest of validation piecewise. An unamended root yields
  exactly one window.
- `_controller_v3_history(root)` — correlates durable controller-v3 records
  *before* replay, so a corrupted history still names its exact failed boundary
  instead of collapsing to a generic open error.
`check: for s in verify_root _amendment_epochs _controller_v3_history _legacy_bridge_failure_call_seqs _expected_call_outcome _epoch_input_for_dossier; do grep -q "def $s(" src/deepreason/invariants.py || exit 1; done; grep -q "An unamended root yields exactly one window covering" src/deepreason/invariants.py`
- `VerifierRegistry` — the only route from a name to a backend; `register`,
  `get`/`resolve`, `fingerprint_is_pinned`, `verify`. Model output never selects
  a tool.
- `VerificationRequest` / `VerificationResult` — frozen pydantic request and
  receipt. `VerificationResult.fail_warrant_eligible` is `verdict == "fail"`.
- `LeanBackend` (alias `Lean4Backend`), `SimulationBackend`,
  `ContainedSimulationBackend` — the three `VerifierBackend` implementations;
  each exposes `fingerprint()` and `verify(request, blobs)`.
- `verify_code_patch(workload, snapshot, patch, runner=..., blobs=...)` — apply
  a patch in a throwaway tree, then run only the workload's predeclared checks.
- `TrustedCheckRunner.run(check, workspace, blobs)` — bounded subprocess
  execution of one declared check; `VerificationRunner` (alias `VerifierRunner`)
  wraps a registry.
- `LLMBroker` — a unix-socket broker that lets a contained simulation call a
  model without the sandbox holding a network namespace.
`check: python -c "import deepreason.verification as v; [getattr(v, n) for n in ('VerifierRegistry','VerificationRequest','VerificationResult','LeanBackend','Lean4Backend','SimulationBackend','TrustedCheckRunner','VerificationRunner','VerifierRunner','verify_code_patch','verify_root_report')]; from deepreason.verification.contained import ContainedSimulationBackend; from deepreason.verification.llm_broker import LLMBroker; from deepreason.verification.registry import VerifierRegistry as R; assert hasattr(R, 'fingerprint_is_pinned')"`

The package exports lazily through a `_EXPORTS` table in
`verification/__init__.py`; importing `deepreason.verification` pulls in no
backend, which is what keeps Lean and the sandbox off the harness startup path.
`check: grep -q "_EXPORTS = {" src/deepreason/verification/__init__.py && python -c "import sys, deepreason.verification as v; eager=[m for m in sys.modules if m.startswith('deepreason.verification.')]; assert not eager, eager; assert v.LeanBackend and any(m.startswith('deepreason.verification.lean') for m in sys.modules)"`

## State it owns

Nothing on disk. `verify_root` opens two independent read-only `Harness`
instances and reads `run-manifest.json`, the amendment chain, epoch documents
and the object/blob stores; it creates and repairs nothing — a torn log tail is
a finding, never something validation silently truncates.
`check: python -m pytest "tests/test_persistence_invariants.py::test_replay_verification_does_not_repair_a_torn_tail" "tests/test_persistence_invariants.py::test_time_travel_does_not_create_or_repair_storage" -q`

`REPLAY_VALIDATION.json` (schema `replay-validation.v1`) is written by
*callers* — `capabilities/audit.py` for tranche audits and
`runtime/terminal_authority.py` for the terminal binding — out of this
subsystem's return value, alongside the manifest and process digests that name
what was validated.
`check: grep -q "def _fresh_replay_validation" src/deepreason/runtime/terminal_authority.py && grep -q "replay-validation.v1" src/deepreason/capabilities/audit.py && sh -c '! grep -q REPLAY_VALIDATION src/deepreason/invariants.py'`

Verifier backends own no store either: diagnostics, output, stdout/stderr and
axiom listings go into the caller's content-addressed blob store as
`*_ref` digests on the receipt. The one piece of durable identity the package
does own is the pinned containment worker source — `CONTAINED_WORKER_SOURCE_V1`
and its `CONTAINED_WORKER_SHA256`, which appears in every contained execution
fingerprint, so changing the worker changes the recorded runtime identity.
`check: grep -q "CONTAINED_WORKER_SHA256 = sha256_hex(CONTAINED_WORKER_SOURCE_V1.encode(\"utf-8\"))" src/deepreason/verification/contained.py && grep -q "\"worker_sha256\": CONTAINED_WORKER_SHA256" src/deepreason/verification/contained.py`

In-memory `stats` (event/artifact/problem counts, `logged_tokens`, profile
totals, the workflow and capability process digests) ride out on the return
value and are the numbers experiment reports quote.

`stats["signal_snapshot"]` (Part F, R15, adjudication-judge-seats-optins
tranche, 2026-08-11) is `signals_read.read_signal_snapshot(root)`'s typed
output, added by `verify_root_report` alongside `stats["verification_v2"]`
above — a pure READ aggregation, not a new report shape or a new
`VerificationFindingV2`. It never fails closed to `{}` the way `stats`
itself does on an unopenable root (the earlier Traps entry below): each of
its three sub-reads (`latest_config_critique`, the per-phase deferral
counts, the summed token spend) independently tolerates a missing or
unreadable root and returns its own empty shape, so a caller can always
index `stats["signal_snapshot"]["token_spend"]` without a KeyError even
when `stats` was otherwise empty.
`check: grep -q 'stats\["signal_snapshot"\] = read_signal_snapshot' src/deepreason/verification/report.py && grep -q "class SignalSnapshotV1" src/deepreason/signals_read.py && grep -q "def read_signal_snapshot" src/deepreason/signals_read.py && python -c "from deepreason.verification.report import verify_root_report; r = verify_root_report('/nonexistent/path/for/docs-verify', allow_missing_terminal=True); assert r.stats['signal_snapshot']['token_spend'] == {'prompt_tokens': 0, 'completion_tokens': 0, 'total': 0, 'calls': 0}"`

## Where to change what

| To change... | Edit | Test |
|---|---|---|
| Add or tighten a replay invariant | a new `fail("<name>", ...)` inside `verify_root`, `src/deepreason/invariants.py` | `python -m pytest tests/test_chaos_invariants.py -q` |
| Which conjecturer-turn contract versions replay authorizes | two membership checks inside `verify_root` (the legacy `work_orders` walk; `validate_conjecture_turn`'s `event.conjecture_turn` check) — both widened for v7 (P-CEPP-1) though BOTH are unreachable for schema 6 in the current codebase: `harness.py`'s `record_conjecture_turn_event` (frozen) refuses any `attempt.contract_id` outside `{v4, v5}`, and `h.workflow_state.work_orders` stays empty for a transactional dispatch (`transaction_work` instead) | `python -m pytest tests/test_v6_transaction_qualification.py::test_live_v7_conjecture_dispatch_mints_a_v7_contracted_commitment tests/test_conjecturer_turn_v4.py::test_v7_configured_expansion_replay_validates -q` |
| Which dimension a finding lands in (and so whether it flips `valid`) | `_SECURITY_CHECKS` / `_OPERATIONAL_CHECKS` / `_EPISTEMIC_CHECKS` / `_legacy_channel`, `verification/report.py` | `python -m pytest "tests/test_r0_terminal_verification.py::test_verify_root_report_separates_completion_from_false_authority" -q` |
| Add a finding derived from the terminal projection, not the log | `_terminal_findings`, `_terminal_authority_findings`, `_model_execution_findings`, `_transaction_findings`, `verification/report.py` | `python -m pytest tests/test_r0_terminal_verification.py -q` |
| Amendment chain validation or the per-epoch fence windows | `_amendment_epochs`, `src/deepreason/invariants.py` | `python -m pytest "tests/test_amendment_chain_integrity.py::test_chain_anchored_to_another_manifest_is_reported" -q` |
| Add a mechanical verifier backend | implement the `VerifierBackend` protocol in `verification/models.py`, register on `VerifierRegistry`, add to `_EXPORTS` | `python -m pytest tests/test_verifier_registry.py -q` |
| Lean toolchain pinning, axiom or placeholder policy | `verification/lean.py` and `VerificationRequest._backend_shape` | `python -m pytest tests/test_lean_backend.py -q` |
| What a simulation program may contain | `_guard` in `verification/simulation.py` **and** `guard` inside `CONTAINED_WORKER_SOURCE_V1` | `python -m pytest tests/test_simulation_backend.py tests/test_contained_simulation_runner.py -q` |
| Sandbox resource limits or the containment shape | `_CPU_SECONDS` / `_MEMORY_LIMIT` / `_IPC_LIMIT` in `simulation.py`; `_containment_limits` and `containment_prefix` in `contained.py`; `_sandbox.py` for seccomp | `python -m pytest tests/test_contained_simulation_runner.py -q` |
| Let a sandboxed program call a model | `verification/llm_broker.py` and `_derive_v2` in `brokered.py` | `python -m pytest tests/test_brokered_simulation.py -q` |
| How a code patch is applied and which checks run | `verify_code_patch` in `code.py`, `TrustedCheckRunner.run` in `runner.py` | `python -m pytest tests/test_workload_code.py -q` |
| What `REPLAY_VALIDATION.json` binds | not here — `_fresh_replay_validation` in `runtime/terminal_authority.py`, `write_tranche_a_audits` in `capabilities/audit.py` | `python -m pytest tests/test_v6_terminal_commitment_authority.py -q` |
| Add a new already-live signal to the read-only snapshot | `signals_read.py` (a new `_<name>` helper, threaded into `read_signal_snapshot`) — never a new `Measure`/`LLMCall` field; that would need `DR-SUB-scheduler`'s `signals.py` registry instead | `python -m pytest tests/test_signals_read.py tests/test_v6_verification_transactions.py::test_report_includes_signal_snapshot -q` |
`check: grep -q "_SECURITY_CHECKS = frozenset(" src/deepreason/verification/report.py && grep -q "_OPERATIONAL_CHECKS = frozenset(" src/deepreason/verification/report.py && grep -q "_EPISTEMIC_CHECKS = frozenset(" src/deepreason/verification/report.py && grep -q "def write_tranche_a_audits(" src/deepreason/capabilities/audit.py`
`check: grep -q "def _guard(tree: ast.AST) -> None:" src/deepreason/verification/simulation.py && grep -q "imports are not allowed" src/deepreason/verification/simulation.py && grep -q "def guard(source, label):" src/deepreason/verification/contained.py && grep -q "may not import or mutate scope" src/deepreason/verification/contained.py && grep -q "def _containment_limits(" src/deepreason/verification/contained.py && grep -q "def containment_prefix(cls)" src/deepreason/verification/contained.py && grep -q "def seccomp_available()" src/deepreason/verification/_sandbox.py && grep -q "def _derive_v2(source: str) -> str:" src/deepreason/verification/brokered.py`

## Traps

- **`attempt-limits` must re-derive the SAME control barrier the controller
  wrote against, or every steered run verifies as invalid.** A per-attempt
  `max_tokens` differing from its route's is authorized only by a prior
  controller policy whose value sits inside that knob's barrier. That barrier is
  anchored per run to the cap the manifest assigned the role, so the check calls
  `cap_envelope(knob, _configured_role_cap(knob))`; reading the static
  `ENVELOPES` table instead restores the pre-2026-08-13 state where the widest
  ceiling was 5,000 and a production run that actually steered — every one of
  them pins 16,384 — would fail replay. The asymmetry to respect when touching
  this: the predicate may only ever ADD authorized values, never remove one, or
  a committed root changes meaning. The 2026-08-13 widening
  (`experiments/2026-08-13-defect-controller-steering-inert/`) was measurably a
  no-op on the past — zero of 104 committed logs contain a controller policy
  body, so `authorized_controller_limits` is empty in all of them — and the
  42-root sweep is the instrument that must confirm that before any future
  change here.
`check: grep -q "cap_envelope(knob, _configured_role_cap(knob))" src/deepreason/invariants.py && grep -q "def _configured_role_cap" src/deepreason/invariants.py && python -m pytest tests/test_controller_steering_parity.py::test_replay_authorizes_a_cap_the_controller_could_legitimately_set tests/test_controller_steering_parity.py::test_replay_still_rejects_a_cap_beyond_the_anchored_barrier tests/test_process_metadata.py::test_invariants_reject_unlogged_effective_transport_limit -q`
- **A new `fail()` name defaults to integrity, and integrity decides `valid`.**
  `_legacy_channel` routes anything it does not recognise to `integrity`, and
  `valid` is `integrity_valid and security_valid`. Adding a check without
  classifying it therefore flips `valid` on every recorded root that trips it.
  Every security-channel name is a name `verify_root` actually emits — that
  correspondence is the thing a rename breaks.
`check: python -c "import re,pathlib; inv=pathlib.Path('src/deepreason/invariants.py').read_text(); rep=pathlib.Path('src/deepreason/verification/report.py').read_text(); em=set(re.findall(r'fail\(\s*\"([a-z0-9-]+)\"', inv)); sec=set(re.findall(r'\"([a-z0-9-]+)\"', rep.split('_SECURITY_CHECKS = frozenset(')[1].split(')')[0])); raise SystemExit(0 if sec and sec <= em else 1)"`
- **`valid` does not mean good.** It means no integrity and no security finding.
  Completeness, epistemic adequacy and operational success are three separate
  booleans, and a run can be `valid` with all three false. The epistemic checks
  (`adjudication-blindness`, `bridge-epistemic`, `bridge-grounding`,
  `grounding-review`) are derived in `report.py` — they are not `verify_root`
  findings at all, so reading `verify_root` alone tells you nothing about them.
`check: sh -c 'grep -q "return self.integrity_valid and self.security_valid" src/deepreason/verification/report.py && ! grep -q "\"adjudication-blindness\"" src/deepreason/invariants.py && grep -q "\"adjudication-blindness\"" src/deepreason/verification/report.py'`
- **`completion_satisfied` is UNREACHABLE on the public `deepreason reason`
  path, so any instrument demanding it is asserting against the design.**
  `completion_satisfied` is `not self.completion`, and
  `_deferred_model_phase_findings` turns every `v6-model-phase-deferred.v1`
  marker into one completion finding.
  `Scheduler._premise_rent_step` runs on every cycle with no state gate in
  front of it, and a v6 manifest grants the `variator` a behavioral contract
  only under `criticism_policy.authority == "defended_trial"` — which the
  public path never sets — so cycle 0 of every such run declares a
  `premise-demarcation-variation` deferral and the flag can never come back
  true. Found 2026-08-21 by `scripts/wheel_operational_smoke.py`, whose
  `_assert_resumable_terminal` had demanded exactly that since before
  `a476c564f` (2026-08-15) added the deferral; the retained root
  `run-e9d4bb16796b8aa4b560c632b33d6500` converged, replay-valid, with that
  one marker at seq 34 and nothing else in any channel. FIXED in
  `experiments/2026-08-21-fix-wheel-smoke-reason-stage/` by making the
  instrument compare completion findings against the deferrals the run
  DECLARED, so undeclared debt still fails. The enduring rule: completion
  debt splits into declared and undeclared, and only the second is a defect.
`check: grep -q "def _declared_model_phase_deferrals(" scripts/wheel_operational_smoke.py && grep -q "terminal carries undeclared completion debt" scripts/wheel_operational_smoke.py && ! grep -q '"completion_satisfied",' scripts/wheel_operational_smoke.py && grep -q "def _deferred_model_phase_findings(" src/deepreason/verification/report.py && grep -q '"v6-model-phase-deferred.v1"' src/deepreason/scheduler/scheduler.py && python -m pytest tests/test_wheel_operational.py::test_a_converged_terminal_with_only_deferral_debt_is_resumable tests/test_wheel_operational.py::test_a_malformed_deferral_marker_is_not_declared_debt -q`
- **A missing coverage target is debt; a malformed coverage receipt is a
  violation.** `foreign-criticism` is the one check name that splits by detail
  text: `target ... policy requires ...` is re-routed to `completion`, every
  other `foreign-criticism` finding stays `integrity`. Changing that detail
  string changes the channel.
`check: grep -q 'check == "foreign-criticism"' src/deepreason/verification/report.py && grep -q 'detail.startswith("target ")' src/deepreason/verification/report.py && grep -q '"policy requires" in detail' src/deepreason/verification/report.py`
- **FIXED 2026-08-11 (adjudication-judge-seats-optins tranche, run
  `run-ee9696e2161374f6597f65963a645d8a`, found by
  `scripts/wheel_operational_smoke.py`): `_transaction_findings`'s
  `task == "criticism"` authority check assumed `manifest.criticism_policy`
  is always populated for real criticism work.** Road E (this tranche's
  Part A) built a genuinely school-free legacy criticism dispatch with NO
  `criticism_policy` binding at all, and Part B2 made that the DEFAULT
  (`LEGACY_CRITICISM_ENABLED=True`) — so every ordinary run's legacy
  criticism transactions were flagged `security`-invalid
  ("criticism work is not authorized by the manifest"), 17 findings on
  one ordinary `deepreason reason` call, confirmed live via an installed
  wheel. `nonconjecture_recovery.py::_criticism_contract`'s RECOVERY-side
  authority check already had the correct school-free branch (S13e, this
  same tranche) — this POST-HOC verification check was a second,
  independent site that needed the identical branch and was missed during
  Part A's own frozen-surface confirmation (Step 1 checked `harness.py`/
  `capabilities/state.py`/`invariants.py`/`run_manifest.py` contact, not
  `verification/report.py`). Fixed by mirroring `_criticism_contract`'s
  exact shape: `critic_school_id is None` is authorized whenever the
  `argumentative_critic` role has a manifest route and
  `payload["dispatch_authority"] == "observe_only"`.
`check: python -m pytest tests/test_v6_verification_transactions.py -k "school_free_criticism" -q`
- **An unopenable root returns empty `stats`.** `verify_root` short-circuits to
  a single `open` (or the controller-v3) finding with `"stats": {}`. Callers
  that index into `stats` unconditionally crash on exactly the roots most worth
  inspecting.
`check: grep -q 'return {"violations": \[{"check": "open", "detail": repr(e)\[:400\]}\], "stats": {}}' src/deepreason/invariants.py`
- **`overrun` is not `fail`.** Only `verdict == "fail"` is fail-warrant
  eligible; a timed-out or resource-exhausted verifier settles nothing. The same
  asymmetry runs through `verify_code_patch`: a patch-application error
  propagates as an operational error rather than becoming a `fail`.
`check: python -m pytest "tests/test_verifier_registry.py::test_overrun_is_never_fail_warrant_eligible" -q`
- **The registry re-checks pinning on every call, not just at registration.**
  `verify` refuses if the backend's live fingerprint has drifted, if the result
  names a different backend, or if the result's fingerprint is not the pinned
  one. A backend whose `fingerprint()` depends on mutable environment state will
  fail here, correctly.
`check: grep -q "verifier fingerprint changed after registration" src/deepreason/verification/registry.py && grep -q "verifier returned a different backend identifier" src/deepreason/verification/registry.py`
- **Lean requests refuse ambiguity at construction.** `toolchain_id` may not be
  `auto`, `latest`, `*.x` or any range; `lean4` additionally requires
  `source_ref` and at least one target theorem and forbids `allow_sorry`
  outright. These are model validators, not runtime checks — see the
  read-the-validator trap in `DR-INV-frozen-surfaces`.
`check: grep -q "toolchain_id must be an exact resolved coordinate" src/deepreason/verification/models.py && grep -q "Lean verification never permits sorry or admit" src/deepreason/verification/models.py`
- **The in-process and contained simulation runners must agree byte for byte.**
  `_resolve_observable` in `simulation.py` and `resolve_observable` in the
  pinned worker are deliberate duplicates; if they diverge, a result depends on
  which path executed it. Edit both or neither.
`check: grep -q "def _resolve_observable(output: dict, name: str) -> Any:" src/deepreason/verification/simulation.py && grep -q "def resolve_observable(output, name):" src/deepreason/verification/contained.py`
- **The verifier CLI commands are deliberately not public (G02).**
  `_cmd_check_proof`, `_cmd_code` and `_cmd_simulate` exist in `cli/main.py` but
  no `add_parser` registers them, so `deepreason ... simulate` exits 2 with
  `invalid choice`. Do not "fix" the missing subcommand; the workflows are
  unqualified.
`check: python -c "import subprocess,sys; r=[subprocess.run([sys.executable,'-m','deepreason.cli.main',c],capture_output=True,text=True) for c in ('check-proof','code','simulate')]; assert all(p.returncode==2 and 'invalid choice' in p.stderr for p in r)" && grep -q "def _cmd_check_proof" src/deepreason/cli/main.py && grep -q "def _cmd_code" src/deepreason/cli/main.py && grep -q "def _cmd_simulate" src/deepreason/cli/main.py && python -m pytest tests/test_cli_verifiers.py -q`
- **`report.py` imports `verify_root` inside the function body on purpose.** A
  module-level import reintroduces an import cycle during harness startup.
`check: grep -q "    from deepreason.invariants import verify_root" src/deepreason/verification/report.py && python -c "import sys, deepreason.verification.report; assert 'deepreason.invariants' not in sys.modules"`
- **A demand for "exactly one artifact shaped like X" must key on a
  discriminator the model cannot emit.** Until 2026-08-03 the
  `attached-evidence` check selected its candidate set by `mention` refs to
  the source record alone, so the first live conjecture that cited its own
  attached evidence (stress-triplet `run-0a3e93d6e8031e2e6d1d21dde2fa93cc`,
  completed rc=5) flipped its root to `valid=False`, with a detail string
  naming as missing an artifact that existed. Fixed in tranche
  `experiments/2026-08-03-fix-attached-evidence-integrity`: the predicate now
  also requires `import` provenance — the writer's stamp, unreachable from
  rule-driven creation — and the uniqueness and dependence demands are
  unchanged. The agreement is documented in `DR-SEAM-periphery-x-verification`.
`check: grep -q "artifact.provenance.role == \"import\"" src/deepreason/invariants.py && grep -q "Regression (stress-triplet run-0a3e93d6)" tests/test_attached_evidence_citation.py`
