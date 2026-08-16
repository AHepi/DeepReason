<!-- DR-SEAM-rules-x-workflow -->
Verified-at: 9fa394d9
Verify: python tools/docs_verify.py
Owns: src/deepreason/rules/conj.py, src/deepreason/rules/crit.py, src/deepreason/workflow/transaction_service.py, src/deepreason/workflow/conjecture_recovery.py, src/deepreason/workflow/nonconjecture_recovery.py, src/deepreason/workflow/atomic_recovery.py
Sides: DR-SUB-rules, DR-SUB-workflow

# rules x workflow

## The agreement

`rules/` decides what may be proposed and what may be attacked; `workflow/`
decides by what recorded authority a provider may be asked. Under RunManifest v6
every model-facing epistemic move is bracketed: the rule opens a durable,
unissued `WorkPreparationV1` before it renders a prompt, and settles that work
with exactly one `WorkTerminalV1` on every exit path, including the ones that
raise. What the rule supplies is the transaction's semantic identity — a
`contract_id`, a `route_lease`, `target_refs`, `input_refs`, a `trigger_ref`
that content-addresses the payload, and one state fence — and once prepared,
none of it may move: `finalize_dispatch` copies the contract and the lease out
of the preparation, so a rule cannot dispatch under authority it did not already
record. What the workflow plane promises in return is that it will never read
any of it. `transaction_service.py`, `transaction.py`, `replay.py`, `state.py`
and `reducer.py` touch no artifact, no commitment and no epistemic status;
`task_payload_value` is frozen JSON that only its author interprets.

That blindness has one exception, and it is the shape of this whole seam:
**recovery**. A crashed run must re-derive an epistemic effect from a stored blob
with no provider present, and that is not a control-plane question — so
`workflow/conjecture_recovery.py` and `workflow/nonconjecture_recovery.py`, and
only those two, import `deepreason.rules`. They do it in opposite directions.
The criticism effect is SHARED: `nonconjecture_recovery` calls `rules/crit.py`'s
own appliers with `restart_safe=True`. The conjecture effect is DUPLICATED:
`_materialize_formal` lives in `workflow/`, re-runs the anti-relapse gate itself
and calls `harness.register_batch(rule=Rule.CONJ)` itself, and `rules/conj.py`'s
`conj` imports it back on the branch that follows
`_v6_atomic_conjecture_fallback`. Two independent implementations
must build byte-identical artifact ids from one provider output, or a run
recovers into a different graph than it wrote.

A naive grep over-reports this seam and under-reports it at once. 37 files match
`deepreason.workflow`; three of them match only `deepreason.workflows`, a
different package (workload definitions, not the control plane). Two of the
fourteen modules below `deepreason.rules` name the control plane — `conj.py` and
`crit.py`; the other twelve never do — including D2 rev 2's own
`relatedness.py`/`encoding.py`, both v6-runtime-agnostic by construction (they
take a bare `harness`/`adapter`, never a `RunManifest`). And
`workflow/atomic_recovery.py` names no rule at all yet exists solely for those
two, which are its only callers in `src/`.
`check: test "$(grep -rl 'deepreason\.workflow' --include=*.py src/deepreason | wc -l)" -gt "$(grep -rlE 'deepreason\.workflow\b' --include=*.py src/deepreason | wc -l)" && grep -q "deepreason\.workflows\." src/deepreason/workflows/website.py && ! grep -qE "deepreason\.workflow\b" src/deepreason/workflows/website.py && test "$(grep -rlE 'deepreason\.workflow\b' --include=*.py src/deepreason/rules | sort | paste -sd,)" = "src/deepreason/rules/conj.py,src/deepreason/rules/crit.py" && test "$(grep -rln 'recover_atomic_child_output' --include=*.py src/deepreason | grep -vc '^src/deepreason/workflow/atomic_recovery.py')" -eq 2 && grep -q "^def recover_atomic_child_output(" src/deepreason/workflow/atomic_recovery.py`

The dependency arrow is asymmetric by construction. All 32 of the rules' imports
of the control plane are function-local — not one at module scope — so importing
every module under `rules/` loads no `deepreason.workflow.*` at all, and the
rules stay testable against a fake harness with no v6 runtime present. The
reverse arrow is three imports in two files, one of them at module scope
(`anti_relapse`), because recovery cannot defer the gate it re-runs.
`check: python -c "import importlib, pkgutil, sys, deepreason.rules as R; loaded=[importlib.import_module(m.name) for m in pkgutil.walk_packages(R.__path__, 'deepreason.rules.')]; assert len(loaded)==14, len(loaded); assert not [m for m in sys.modules if m.startswith('deepreason.workflow.')]" && test "$(grep -rhcE '^ +from deepreason\.workflow\b' src/deepreason/rules/conj.py src/deepreason/rules/crit.py | paste -sd+ | bc)" -eq 34 && ! grep -rqE '^from deepreason\.workflow\b' --include=*.py src/deepreason/rules && grep -q "^from deepreason.rules.guards import anti_relapse$" src/deepreason/workflow/conjecture_recovery.py && test "$(grep -rlE '^\s*from deepreason\.rules' --include=*.py src/deepreason/workflow | sort | paste -sd,)" = "src/deepreason/workflow/conjecture_recovery.py,src/deepreason/workflow/nonconjecture_recovery.py" && test "$(grep -rhcE '^\s*from deepreason\.rules' --include=*.py src/deepreason/workflow | paste -sd+ | bc)" -eq 3`

## Where it is expressed

| Site | File | Symbol | What it enforces |
|---|---|---|---|
| The bracket opens | `rules/conj.py`, `rules/crit.py` | `InquiryTransactionService(harness, manifest, meter)` — four constructions | the rule that makes the call owns the transaction; the scheduler owns none (`DR-SEAM-scheduler-x-workflow`) |
| The identity tuple | `rules/conj.py`, `rules/crit.py` | the four `service.prepare(...)` sites | ten keyword arguments, identical at every site, nothing positional |
| Contract authorization | `workflow/transaction_service.py` | `prepare` → `resolve_route_seat_behavioral_capability` | `V6_BEHAVIORAL_CONTRACT_NOT_AUTHORIZED` for a contract not frozen for that seat |
| Contract freeze | `workflow/transaction_service.py` | `finalize_dispatch` → `DispatchAuthorizationBundleV1.create(contract_id=preparation.contract_id, route_lease=preparation.route_lease)` | issue cannot dispatch under authority the preparation did not record |
| One state fence | `workflow/transaction.py` | `WorkPreparationV1._one_state_fence_and_payload` | `formal_fence_seq == scratch_fence_seq`; exactly one payload source |
| Reference hygiene | `workflow/transaction.py` | `WorkPreparationV1._unique_refs` | `target_refs` / `input_refs` are the rule's, and are unique |
| Route agreement | `rules/conj.py` | `resolve_conjecture_route` vs the rule's `RouteLeaseRefV1` | "v6 conjecture route differs from its manifest authority" |
| Decomposition agreement | `rules/conj.py`, `rules/crit.py` | the atomic child's lease and contract re-check | "atomic {conjecture,criticism} differs from decomposition authority" |
| Planning is not exposing | `workflow/transaction_service.py` | `context_plan` (a `staticmethod`) | a `ContextPackPlanV1` becomes durable only inside the `WORK_ISSUED` append |
| Open-preparation guard | `workflow/transaction_service.py` | `_require_open_preparation` | "work preparation is no longer open for dispatch": one bundle per preparation |
| Settle on every exit | `rules/crit.py` | the `abandon(*, issued, reason_code)` closure | pre-issue → `exact` and zero tokens; post-issue → `unknown` and no counts |
| Settle on every exit | `rules/conj.py` | `abandon_v6_context_preissue` | context planning that fails after preparation abandons before dispatch |
| Repair rebinding | `rules/conj.py`, `rules/crit.py` | the three sites that rebind from `repaired` — `conj` (`transaction_preparation`/`transaction_authorization`), `_v6_atomic_conjecture_fallback` and `_v6_transactional_batch_call` | the terminal lands on the repair work item, not on the already-terminated parent |
| Well-formedness | `workflow/replay.py` | `_apply_transaction` | prepared first, issued once, nothing after a terminal, transition is the final output |
| Well-formedness | `harness.py` | `record_transaction_transition` | the per-kind record inventory; every record names the same work and attempt |
| Effect ordering (conjecture) | `rules/conj.py` | `register_batch` → `record_semantic_admission(admitted_refs=…registered…)` → `terminate` | the admission NAMES the artifacts the effect produced |
| Effect ordering (criticism) | `rules/crit.py` | `_v6_transactional_batch_call` terminates, then `_crit_argumentative_batch_result` runs | the provider output is admitted before the caller-owned effect is applied |
| Recovery, criticism | `workflow/nonconjecture_recovery.py` | `_recover_criticism_effect` → `rules/crit.py` appliers | `preparation.target_refs` are the targets, `input_refs` the coverage assignments |
| Citable exposure | `rules/conj.py`, `rules/crit.py` | `context_plan(plan_kind="citable")` with `ContextNamespace.EVIDENCE` items | the admitted blocks a call was SHOWN are named in its exposure receipt, so a citation can be checked against what the model could read rather than against the whole dossier (P4, R62) |
| Recovery, conjecture | `workflow/conjecture_recovery.py` | `_materialize_formal` → `anti_relapse` → `register_batch(rule=Rule.CONJ)` | the gate is re-run, not replayed; an artifact already present admits as `recovered-existing` |
| Recovery, atomic child | `workflow/atomic_recovery.py` | `recover_atomic_child_output(harness, manifest, service, root_item, contract)` | the RULE hands its wire contract; the stored raw blob is re-validated with no adapter |
| Idempotent re-application | `rules/crit.py` | `restart_safe` + `effect_source_call_seq` | two identical critic outputs from two transactions stay two effects |

The four preparation sites are one fixed identity tuple. Every argument is passed
by keyword, none positionally, and no rule ever passes `task_payload_ref` or
`source_terminal_commitment_ref`: the payload is always inline — which is what
makes `trigger_ref`'s content address and recovery's payload-equality match work
— and post-terminal work belongs to the bridge, not to a rule. One fence value
goes into both fence fields at all four sites, and the record refuses the three
ways a rule could get the preparation wrong.
`check: python -c "import ast, pathlib; want={'attempt_index','contract_id','formal_fence_seq','input_refs','route_lease','scratch_fence_seq','target_refs','task_kind','task_payload_value','trigger_ref'}; calls=[(f,n) for f in ('src/deepreason/rules/conj.py','src/deepreason/rules/crit.py') for n in ast.walk(ast.parse(pathlib.Path(f).read_text())) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr=='prepare']; assert len(calls)==4, len(calls); bad=[(f,n.lineno) for f,n in calls if n.args or {k.arg for k in n.keywords}!=want]; assert not bad, bad; kws=[{k.arg: ast.unparse(k.value) for k in n.keywords} for f,n in calls]; assert all(kw['formal_fence_seq']==kw['scratch_fence_seq']=='fence' for kw in kws), kws; assert all('fence = max(0, harness._next_seq - 1)' in pathlib.Path(f).read_text() for f in ('src/deepreason/rules/conj.py','src/deepreason/rules/crit.py'))" && ! grep -rq "source_terminal_commitment_ref" --include=*.py src/deepreason/rules && grep -q "source_terminal_commitment_ref=source_terminal_commitment_ref," src/deepreason/bridge/harness.py && python -c "import unittest; from deepreason.workflow.transaction import WorkPreparationV1 as W; from deepreason.workflow.models import RouteLeaseRefV1, WorkflowTaskKind; T=unittest.TestCase(); base=dict(manifest_digest='a'*64, task_kind=WorkflowTaskKind.CONJECTURE, attempt_index=0, trigger_ref='t', contract_id='conjecturer.turn.v6', route_lease=RouteLeaseRefV1(role='conjecturer', seat=0, endpoint_id='e', route_sha256='0'*64), task_payload_value={'schema':'x'}); assert W.create(formal_fence_seq=7, scratch_fence_seq=7, **base).work_id; T.assertRaisesRegex(Exception, 'one immutable state fence', W.create, formal_fence_seq=7, scratch_fence_seq=8, **base); T.assertRaisesRegex(Exception, 'exactly one payload source', W.create, formal_fence_seq=7, scratch_fence_seq=7, task_payload_ref='r', **base); T.assertRaisesRegex(Exception, 'must be unique', W.create, formal_fence_seq=7, scratch_fence_seq=7, target_refs=('a','a'), **base)"`

Exactly four contract ids can reach `prepare` from a rule — one spelled in the
source (`batch-critic.v2`), one read from the manifest's own configured value
(`conj.py`'s `configured_turn_contract`, captured once from
`control_plane_policy.contract_versions.conjecturer_turn_contract` and always
one of `conjecturer.turn.v6`/`conjecturer.turn.v7`, P-CEPP-1), two carried by
the atomic wire contracts — and `prepare` refuses any contract the manifest
has not frozen for that route seat. A route lease is minted
once per call from the live endpoint lease, re-checked against the manifest
before dispatch and against the decomposition transition for an atomic child, and
re-derived from the manifest again at recovery: four independent derivations of
the same four fields.
`check: grep -q "V6_BEHAVIORAL_CONTRACT_NOT_AUTHORIZED" src/deepreason/workflow/transaction_service.py && grep -q "behavioral = resolve_route_seat_behavioral_capability(" src/deepreason/workflow/transaction_service.py && grep -q "contract_id=preparation.contract_id," src/deepreason/workflow/transaction_service.py && grep -q "route_lease=preparation.route_lease," src/deepreason/workflow/transaction_service.py && python -c "import ast, pathlib; from deepreason.llm.packs import AliasTable; from deepreason.llm.wire import AtomicConjectureWireContractV1 as AC, AtomicCriticWireContractV1 as ACR; ids={(lambda v: v.value if isinstance(v, ast.Constant) else ast.unparse(v))([k.value for k in n.keywords if k.arg=='contract_id'][0]) for f in ('src/deepreason/rules/conj.py','src/deepreason/rules/crit.py') for n in ast.walk(ast.parse(pathlib.Path(f).read_text())) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr=='prepare'}; assert ids=={'configured_turn_contract','batch-critic.v2','contract.contract_id'}, ids; assert AC(AliasTable({}), reasoning=False).contract_id=='conjecturer.atomic-candidate.v1'; assert ACR(AliasTable({'SRC_001':'x'}), expected_target='x').contract_id=='critic.atomic-target.v1'" && test "$(grep -c 'route_sha256=route_fingerprint(endpoint_lease.route),' src/deepreason/rules/conj.py)" -eq 1 && test "$(grep -c 'route_sha256=route_fingerprint(endpoint_lease.route),' src/deepreason/rules/crit.py)" -eq 3 && grep -q 'raise ValueError("v6 conjecture route differs from its manifest authority")' src/deepreason/rules/conj.py && grep -q 'raise ValueError("atomic conjecture differs from decomposition authority")' src/deepreason/rules/conj.py && grep -q 'raise ValueError("atomic criticism differs from decomposition authority")' src/deepreason/rules/crit.py && grep -q '"route fingerprint differs from manifest"' src/deepreason/workflow/nonconjecture_recovery.py && grep -q "provider.route_lease != preparation.route_lease" src/deepreason/workflow/atomic_recovery.py`

`trigger_ref` is a namespaced content address over the payload, and the
namespaces partition by producer: the rules own `conjecture:`, `criticism:` and
`decomposition-child:`, and never emit `repair:`, `bridge:` or
`scratch-authoring:`. `target_refs` and `input_refs` are the seam's semantic
payload — the workflow plane validates only their uniqueness, and recovery is
the only place they are resolved, as criticism targets and as
coverage-assignment object ids.
`check: python -c "import ast, re, pathlib; pat=r'trigger_ref = .([a-z-]+):. [+] hashlib[.]sha256'; own=set(re.findall(pat, pathlib.Path('src/deepreason/rules/conj.py').read_text()+pathlib.Path('src/deepreason/rules/crit.py').read_text())); assert own=={'conjecture','criticism','decomposition-child'}, own; foreign=set(); [foreign.update(re.findall(pat, p.read_text())) for p in pathlib.Path('src/deepreason').rglob('*.py') if p.parts[2]!='rules']; assert foreign>={'repair','bridge','scratch-authoring'} and not (own & foreign), (own, foreign); got=sorted(ast.unparse([k.value for k in n.keywords if k.arg=='target_refs'][0]) for f in ('src/deepreason/rules/conj.py','src/deepreason/rules/crit.py') for n in ast.walk(ast.parse(pathlib.Path(f).read_text())) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr=='prepare'); assert got==['(problem.id,)','(problem.id,)','(target_id,)','targets'], got" && grep -q 'raise ValueError("preparation transition differs from prepared authority")' src/deepreason/workflow/replay.py && grep -q 'raise ValueError("transaction inputs differ from its transition")' src/deepreason/workflow/replay.py && grep -q "list(preparation.target_refs)," src/deepreason/workflow/nonconjecture_recovery.py && grep -q "for assignment_ref in preparation.input_refs:" src/deepreason/workflow/nonconjecture_recovery.py && grep -q "def _unique_refs" src/deepreason/workflow/transaction.py`

The conjecture side applies its epistemic effect BEFORE the admission, and the
admission names what the effect produced; the criticism side admits and
terminates BEFORE the caller-owned effect runs. Both orders are deliberate, and
they are why a crash lands in a different place for each seat — which is what the
scheduler's `admitted_effect_candidates` widening exists to cover
(`DR-SEAM-scheduler-x-workflow`).
`check: python -c "import inspect; from deepreason.rules import conj as C, crit as R; s=inspect.getsource(C.conj); i=s.index('registered = harness.register_batch('); j=s.index('outcome=\"admitted\",\n            admitted_refs=admitted_refs,'); k=s.index('status=\"completed\",\n            reason_code=('); assert i<j<k, (i,j,k); assert '*(artifact.id for artifact in registered),' in s; t=inspect.getsource(R._v6_transactional_batch_call); assert t.index('status=\"completed\",')<t.rindex('return output, llm_call'); assert '_crit_argumentative_batch_result' not in t; b=inspect.getsource(R.crit_argumentative_batch); assert b.index('_v6_transactional_batch_call(')<b.index('_crit_argumentative_batch_result(')"`

What replay and the harness refuse in a rule's transaction, and the exit paths
the rules must therefore close — the critic's `abandon` closure separates
pre-issue (`exact`, zero tokens) from post-issue (`unknown`, no counts), and the
conjecture side abandons a preparation whose context planning fails before any
dispatch:
`check: for s in "work_prepared must introduce exactly one preparation" "transaction must begin with durable work preparation" "transaction transition follows typed termination" "transactional work was already issued" "transaction transition must be the final output" "transaction inputs differ from its transition" "transaction outputs belong to another work attempt"; do grep -q "$s" src/deepreason/workflow/replay.py || exit 1; done; for s in "transaction record belongs to another work item" "transaction record belongs to another attempt" "work_issued requires plans, reservation, exposure, and bundle" "only provider_result may carry an LLM call"; do grep -q "$s" src/deepreason/harness.py || exit 1; done; grep -q 'raise ValueError("work preparation is no longer open for dispatch")' src/deepreason/workflow/transaction_service.py && grep -q 'raise ValueError("work preparation is not canonical in this root")' src/deepreason/workflow/transaction_service.py && python -c "import inspect, re; from deepreason.rules import crit as R, conj as C; t=inspect.getsource(R._v6_transactional_batch_call); assert 'def abandon(*, issued: bool, reason_code: str) -> None:' in t; assert re.search(r'except WorkBudgetDenied:\n\s+raise\n\s+except Exception:\n\s+abandon\(issued=False, reason_code=.critic_preissue_failure.\)', t); assert 'abandon(issued=True, reason_code=\"critic_transport_result_unknown\")' in t and 'abandon(issued=True, reason_code=\"critic_authority_failure\")' in t; assert all('status=\"%s\"' % s in t for s in ('abandoned','transport_failed','completed')); s=inspect.getsource(C.conj); assert 'def abandon_v6_context_preissue(' in s and 'reason_code=\"provider_predispatch_authority_failed\",' in s and 'reason_code=\"provider_transport_failure\",' in s" && python -m pytest tests/test_v6_controller3_replay_verification.py::test_provider_result_without_authorized_attempt_fails_closed tests/test_v6_conjecture_scratch_consumption.py::test_context_commit_failure_abandons_prepared_work_before_dispatch tests/test_v6_transaction_qualification.py::test_recovery_terminalizes_prepared_but_unissued_work tests/test_v6_transaction_qualification.py::test_issued_without_provider_result_recovers_as_unknown_abandonment -q`

Schema repair terminates the PARENT work item and mints a child inheriting its
contract, lease and targets, so all three rule call sites rebind `preparation`
and `authorized` before writing their own terminal.
`check: python -c "import inspect, re; from deepreason.rules import crit as R, conj as C; assert re.search(r'preparation = repaired\.preparation\n\s+authorized = repaired\.authorized', inspect.getsource(R._v6_transactional_batch_call)); assert 'preparation, authorized = repaired.preparation, repaired.authorized' in inspect.getsource(C._v6_atomic_conjecture_fallback); assert re.search(r'transaction_preparation = repaired\.preparation\n\s+transaction_authorization = repaired\.authorized', inspect.getsource(C.conj))" && grep -q "def _terminalize_invalid(" src/deepreason/workflow/repair_transaction.py && grep -q "work_id=authorized.preparation.id," src/deepreason/workflow/repair_transaction.py && for s in "contract_id=parent.contract_id," "route_lease=parent.route_lease," "target_refs=parent.target_refs,"; do grep -q "$s" src/deepreason/workflow/repair_transaction.py || exit 1; done`

The two recovery arrows, their exclusivity, and the fact that conjecture recovery
re-runs the gate rather than replaying its verdict — same `anti_relapse` calls,
same `compile_interface_draft`, same `Rule.CONJ` batch, on both sides:
`check: for s in "anti_relapse.relapse_domain(" "anti_relapse.check(" "anti_relapse.record_domain(" "anti_relapse.recorded_domains(" "rule=Rule.CONJ," "compile_interface_draft" '"recovered-existing"'; do grep -q "$s" src/deepreason/workflow/conjecture_recovery.py || exit 1; done; for s in "anti_relapse.relapse_domain(" "anti_relapse.check(" "anti_relapse.record_domain(" "rule=Rule.CONJ," "compile_interface_draft"; do grep -q "$s" src/deepreason/rules/conj.py || exit 1; done; grep -q "^def _materialize_formal(" src/deepreason/workflow/conjecture_recovery.py && grep -q "from deepreason.workflow.conjecture_recovery import _materialize_formal" src/deepreason/rules/conj.py && ! grep -q "_materialize_formal" src/deepreason/rules/crit.py && grep -q "^def _crit_argumentative_batch_result(" src/deepreason/rules/crit.py && grep -q "^def _apply_counterexample_retry_result(" src/deepreason/rules/crit.py && grep -q "    from deepreason.rules.crit import (" src/deepreason/workflow/nonconjecture_recovery.py && test "$(grep -rln '_crit_argumentative_batch_result\|_apply_counterexample_retry_result' --include=*.py src/deepreason | sort | paste -sd,)" = "src/deepreason/rules/crit.py,src/deepreason/workflow/nonconjecture_recovery.py" && grep -q "    from deepreason.rules.conj import root_problem_family" src/deepreason/workflow/conjecture_recovery.py`

Re-applying a criticism effect is idempotent by construction: the scrutiny
`Measure` carries `source:<seq>`, so two identical critic outputs from two
authorized attempts stay two effects, and `restart_safe` suppresses only the
exact repeat.
`check: python -c "import inspect; from deepreason.rules import crit as R; from deepreason.workflow import nonconjecture_recovery as N; o=inspect.getsource(R._observe_case); assert 'inputs.append(f\"source:{effect_source_call_seq}\")' in o; assert 'raise RuntimeError(\"criticism scrutiny effect is duplicated\")' in o; assert 'if not restart_safe or not existing:' in o; s=inspect.getsource(N._recover_criticism_effect); assert all(kw in s for kw in ('llm_already_recorded=True,','restart_safe=True,','effect_source_call_seq=source_call_seq,'))" && python -m pytest tests/test_v6_nonconjecture_recovery.py::test_identical_critic_effects_remain_isolated_by_source_transaction tests/test_v6_nonconjecture_recovery.py::test_recovered_criticism_applies_canonical_effect_exactly_once tests/test_v6_nonconjecture_recovery.py::test_grounded_counterexample_recovery_does_not_invent_override_on_repeat -q`

## What is deliberately absent

**The transaction plane cannot make an epistemic move, and the rules cannot write
a transaction record.** `transaction_service.py`, `transaction.py`, `replay.py`,
`state.py` and `reducer.py` contain not one reference to `harness.state`,
`harness.commitments`, `register_batch`, `register_commitment`,
`create_artifact` or `record_measure`; symmetrically `rules/` never calls
`harness.record_transaction_transition`, never calls `recover_incomplete`, and
constructs no transaction record type at all — the only workflow record types a
rule builds are `RouteLeaseRefV1`, `VisibleContextItemV1`, `GuardFindingV1` and
`ConjectureWorkAssignmentV1`, none of them a transaction record. Each
side can refuse the other; neither can forge the other's record. The same
boundary explains why rules name two of the eight
`WorkflowTaskKind` values and why `CONJECTURE` is excluded from
`_RECOVERABLE_TASKS`: conjecture recovery needs the embedder and the
anti-relapse gate that the generic recovery path deliberately does not carry.
Adding `CONJECTURE` to that set to "unify" recovery routes conjecture through a
path with no gate at all.
`check: grep -q "^class WorkPreparationV1(" src/deepreason/workflow/transaction.py && grep -q "    def _apply_transaction(" src/deepreason/workflow/replay.py && grep -q "^def state_after_transition(" src/deepreason/workflow/state.py && grep -q "^def reduce_conjecture(" src/deepreason/workflow/reducer.py && ! grep -qE "harness\.state|harness\.commitments|register_batch|register_commitment|create_artifact|record_measure" src/deepreason/workflow/transaction_service.py src/deepreason/workflow/transaction.py src/deepreason/workflow/replay.py src/deepreason/workflow/state.py src/deepreason/workflow/reducer.py && ! grep -rqE "record_transaction_transition|recover_incomplete|WorkPreparationV1\(|WorkTerminalV1\(|DispatchAuthorizationBundleV1\(|TokenReservationV2\(|ContextExposureReceiptV2\(|ContextPackPlanV1\(|WorkLifecycleTransitionV1\(|ProviderAttemptV1\(|SemanticAdmissionV1\(|CompactRecoveryTransitionV1\(|RouteSeatInsufficientCapabilityV1\(|ContractDecompositionTransitionV1\(|ContractDecompositionCompletionV1\(" --include=*.py src/deepreason/rules && grep -q "harness.register_batch(" src/deepreason/workflow/conjecture_recovery.py && grep -q "harness.state.artifacts.get(target_id)" src/deepreason/workflow/nonconjecture_recovery.py && test "$(grep -c "self.harness.record_transaction_transition(" src/deepreason/workflow/transaction_service.py)" -eq 6 && test "$(grep -rlE "RouteLeaseRefV1\(|VisibleContextItemV1\(" --include=*.py src/deepreason/rules | sort | paste -sd,)" = "src/deepreason/rules/conj.py,src/deepreason/rules/crit.py" && python -c "import ast, re, pathlib; T={p: ast.parse(p.read_text()) for p in pathlib.Path('src/deepreason/rules').rglob('*.py')}; W={p: {a.asname or a.name for n in ast.walk(t) if isinstance(n, ast.ImportFrom) and n.module and (n.module=='deepreason.workflow' or n.module.startswith('deepreason.workflow.')) for a in n.names} for p, t in T.items()}; built={n.func.id for p, t in T.items() for n in ast.walk(t) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in W[p] and re.search(r'V\d+$', n.func.id)}; assert built=={'RouteLeaseRefV1','VisibleContextItemV1','GuardFindingV1','ConjectureWorkAssignmentV1'}, sorted(built)" && python -c "import re, pathlib; from deepreason.workflow.nonconjecture_recovery import _RECOVERABLE_TASKS; from deepreason.workflow.models import WorkflowTaskKind as K; s=pathlib.Path('src/deepreason/rules/conj.py').read_text()+pathlib.Path('src/deepreason/rules/crit.py').read_text(); assert set(re.findall(r'WorkflowTaskKind\.([A-Z_]+)', s))=={'CONJECTURE','CRITICISM'}; assert K.CONJECTURE not in _RECOVERABLE_TASKS and K.CRITICISM in _RECOVERABLE_TASKS; assert len(_RECOVERABLE_TASKS)==6 and len(list(K))==8"`

**The deterministic rules have no transaction because they have no provider.**
`crit_program`, `crit_fuzz`, `try_counterexample`, `spawn`, `scan_spawns`,
`register_fail_warrant` and the anti-relapse gate reach no model, so bracketing
them would be process authority over nothing. Four of the six modules that call
a provider unbracketed are a generational fact rather than a designed absence —
`rules/experiment.py` (three sites), `rules/synth.py`, `rules/vision.py`, and
`crit.py`'s pre-v6 paths, all of which v4/v5 roots still need. Under v6 they are
unreachable rather than authorized:
`synthesize` is excluded by an explicit `schema_version == 6` branch in the
scheduler, and vision, experiment authoring and property design become typed
completion debt through `_defer_untransactional_v6_phase`. Local argumentative
criticism used to join them; FIXED 2026-08-10
(adjudication-judge-seats-optins tranche, S13i): it is now bracketed and
dispatches live under v6 too — `crit_argumentative_batch` self-detects the
v6-bound adapter and resolves its own manifest and route, so
`"argumentative-criticism"` no longer appears as a deferred phase anywhere in
the scheduler. It remains a `crit.py` site, just no longer an unbracketed one.
The other two, D2 rev 2's
`rules/relatedness.py::relatedness_trial` and
`rules/encoding.py::draft_encoded_commitment`, are unbracketed for a DIFFERENT
reason — not deferred, DORMANT: neither has any caller anywhere in `src/`
yet (step 17/21 of that tranche's own CHECKLIST.md recorded this as reactive-
only / no wiring, deliberately), so both are unreachable from every scheduler
path, v6 or not, until a future tranche wires a call site — at which point that
tranche must decide bracketing the same way `conj.py`/`crit.py` already did.
Re-enabling any of the four generational sites under v6 without a transaction
does not degrade — the adapter's global guard fails the whole root
(`DR-SEAM-llm-x-workflow`). `conj.py` is already clean: it has no `adapter.call`
that omits the bundle argument.
`check: python -c "import ast, pathlib; sites=[(p.name, n, any(k.arg=='dispatch_authorization' for k in n.keywords)) for p in sorted(pathlib.Path('src/deepreason/rules').rglob('*.py')) for n in ast.walk(ast.parse(p.read_text())) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr=='call' and isinstance(n.func.value, ast.Name) and n.func.value.id=='adapter']; bound=[s for s in sites if s[2]]; unbound=[s for s in sites if not s[2]]; assert len(bound)==4 and {f for f,_n,_b in bound}=={'conj.py','crit.py'}, bound; assert {f for f,_n,_b in unbound}=={'crit.py','experiment.py','synth.py','vision.py','encoding.py','relatedness.py'}, sorted(f for f,_n,_b in unbound)" && ! grep -rq "draft_encoded_commitment\|relatedness_trial" --include=*.py src/deepreason/scheduler src/deepreason/rules/conj.py && python -c "import ast, inspect, textwrap; from deepreason.scheduler.scheduler import Scheduler as S; T=ast.parse(textwrap.dedent(inspect.getsource(S.step))); g=[n for n in ast.walk(T) if isinstance(n, ast.If) and any('relation = synthesize(' in ast.unparse(s) for s in n.body)]; assert len(g)==1, len(g); t=ast.unparse(g[0].test); assert 'not (self.run_manifest is not None and self.run_manifest.schema_version == 6)' in t, t; W=ast.parse(textwrap.dedent(inspect.getsource(S))); phases={(c.args[0].value if c.args else [k.value for k in c.keywords if k.arg=='phase'][0].value) for c in ast.walk(W) if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute) and c.func.attr=='_defer_untransactional_v6_phase'}; assert {'vision-criticism','experiment-generator-authoring','property-design'} <= phases and 'argumentative-criticism' not in phases, sorted(phases)" && grep -q "def _defer_untransactional_v6_phase(" src/deepreason/scheduler/scheduler.py`

**Planning context is not exposing context, and recovery has no adapter.**
`InquiryTransactionService.context_plan` is a `staticmethod` that appends
nothing: a `ContextPackPlanV1` is a pure packing plan and becomes durable only
inside the `WORK_ISSUED` append, alongside the reservation, the exposure receipt
and the bundle — so a rule may build, discard and rebuild plans freely before
issue, and a plan that never reached an issue asserts nothing about what a model
saw. Making `context_plan` append would give every abandoned pre-issue path a
context receipt for a prompt nobody sent. The mirror absence is in
`atomic_recovery`: `recover_atomic_child_output` takes the RULE's live wire
contract as an argument and calls `contract.compile(contract.validate_value(...))`
on the stored raw blob, so the rule supplies the semantics, the workflow module
supplies the authority checks, and no adapter is present in either. That is how
the module can sit in `workflow/` while being called only from `rules/` — it
never names a rule symbol, it receives one.
`check: python -c "import inspect; from deepreason.workflow.transaction_service import InquiryTransactionService as I; from deepreason.workflow.atomic_recovery import recover_atomic_child_output as f; assert isinstance(inspect.getattr_static(I, 'context_plan'), staticmethod); src=inspect.getsource(I.context_plan); assert 'record_transaction_transition' not in src and 'return ContextPackPlanV1.create(' in src; p=inspect.signature(f).parameters; assert 'adapter' not in p and 'contract' in p; assert 'contract.compile(contract.validate_value(candidate))' in inspect.getsource(f)" && grep -q "Pure packing plan; it is not evidence that context was exposed." src/deepreason/workflow/transaction.py && grep -q "records=(\*plans, reservation_record, exposure, bundle)," src/deepreason/workflow/transaction_service.py && ! grep -q "deepreason\.rules" src/deepreason/workflow/atomic_recovery.py && grep -q "^def _materialize_formal(" src/deepreason/workflow/conjecture_recovery.py && grep -q "^def _recover_criticism_effect(" src/deepreason/workflow/nonconjecture_recovery.py && ! grep -rqE "LLMAdapter|build_adapter|\.complete\(" --include=*.py src/deepreason/workflow/atomic_recovery.py src/deepreason/workflow/conjecture_recovery.py src/deepreason/workflow/nonconjecture_recovery.py`

## How to change it

The order is forced by which side can refuse. Start at the record, end at the
rule; the other direction produces an epistemic move whose authority does not
exist, and you will not see it until the root is reopened.

1. **Read `DR-INV-frozen-surfaces` first.** The route-seat behavioral capability
   plan and the contract-decomposition plan are manifest surfaces: adding a
   contract id a rule may prepare with moves every qualification subject digest
   and costs a ~14-minute requalification. A per-run mode goes on `Config`.
2. **Change the durable record before the rule that produces it.** A new field on
   `WorkPreparationV1` means, in this order: `workflow/transaction.py` (the model
   and its validators), `transaction_service.prepare` (which fills it),
   `workflow/replay.py`'s `WORK_PREPARED` branch (which re-checks it), and only
   then the four `service.prepare(...)` sites in `rules/`. Writing the rule half
   first produces an event replay refuses to load, and the failure surfaces on
   reopen rather than at the append.
3. **A new rule that touches a provider is a transaction question first.** Under
   v6 the choices are exactly two: open a real transaction inside the rule, or
   route the phase through `_defer_untransactional_v6_phase` at its scheduler
   call site. There is no third option, and adding a fifth unbracketed
   `adapter.call` to `rules/` is how you find that out at dispatch.
4. **Move the recovery half with the dispatch half.** Every field a rule newly
   puts in `task_payload_value` must be interpreted identically in
   `nonconjecture_recovery` (criticism) or `_materialize_formal` (conjecture): a
   field the live path reads and recovery ignores makes a resumed run diverge
   from the run it resumed. If the change alters what artifact a candidate
   becomes, the duplicate implementation in `_materialize_formal` moves in the
   same commit or the recovered artifact ids stop matching.
5. **Decide where the effect sits relative to the admission, explicitly.** Before
   the admission (conjecture) means a crash leaves the effect applied and the work
   unadmitted, and recovery must tolerate already-present output. After it
   (criticism) means a crash leaves the record claiming an effect that never
   happened, and the seat must join the scheduler's `admitted_effect_candidates`
   set (`DR-SEAM-scheduler-x-workflow`). Not choosing is how a seat silently
   loses an effect.

What breaks first, in the order you will see it:
`RunManifestError("V6_BEHAVIORAL_CONTRACT_NOT_AUTHORIZED")` at `prepare`, before
any prompt is rendered; then `ValueError("work preparation is no longer open for
dispatch")` at issue; then `"dispatch differs from its authorization bundle"` —
raised from `llm/adapter.py` but defined on
`DispatchAuthorizationBundleV1.verify_dispatch` in `workflow/transaction.py`, so
grepping the adapter for it finds nothing (`DR-SEAM-llm-x-workflow`); then, on
reopen, `"transaction must begin with durable work preparation"` or
`"transaction transition follows typed termination"` from `replay.py`; and
finally `verify_root`'s
`workflow-replay` failure, which is the expensive one because the root is already
committed.

The tests that catch you, cheapest first:
`tests/test_v6_conjecture_scratch_consumption.py` and
`tests/test_v6_transaction_qualification.py` (preparation, abandonment, restart;
1–6 s), `tests/test_v6_nonconjecture_recovery.py` (the criticism effect and its
idempotence), `tests/test_v6_atomic_decomposition_authority.py` and
`tests/test_v6_engaged_repair_verification.py` (decomposition and repair
lineage), `tests/test_v6_live_repair_transactions.py` (one bundle, one call),
then `tests/test_v6_controller3_replay_verification.py` (~30 s; the full replay
of a canonical controller-v3 history).

## Traps

- **The seam's own name is a grep trap.** `src/deepreason/workflows/` (workload
  definitions) and `src/deepreason/workflow/` (the control plane) are different
  packages, and `grep -r "deepreason.workflow"` matches both. It reports 37 files
  where 34 name the control plane, and `workflows/website.py` — which imports
  `rules/crit.py` and `rules/guards/anti_relapse` — looks like a rules × workflow
  carrier while naming no control-plane module at all. Use
  `deepreason\.workflow\b`. The check is in "The agreement" above.
- **A repaired atomic child is a DIFFERENT work item, and the rule's fallback
  must name it.** In jolt `run-b4d6dfda0c20676a864a051fbc97bda4` two of three
  decomposition merges (Conj seqs 245 and 386) were reported non-replay-valid:
  when an atomic child is rejected, the admitted candidate comes from a
  `repair.semantic-task.v1` work item whose decomposition authority is its
  `parent_work_id`, and the per-slot identity match in
  `_v6_atomic_conjecture_fallback` must resolve to that repair, because
  `replay.py` refuses a completion whose per-slot inventory differs. The reader
  was fixed at `17d9049d`; the root is `integrity_valid: False` forever, because
  a written record cannot be made to claim it was valid. `DR-SUB-workflow` holds
  the reader half.
`check: python -m pytest tests/test_v6_engaged_repair_verification.py::test_merge_whose_child_was_repaired_verifies_clean tests/test_v6_engaged_repair_verification.py::test_the_repaired_child_slot_really_names_repair_work -q`
- **A budget denial arrives already terminalized, and it travels through the
  rule.** `reserve_dispatch` appends the `budget_denied` terminal and then raises
  `WorkBudgetDenied`; the critic helper therefore re-raises it ahead of its own
  `except Exception: abandon(...)`, which would otherwise write a second terminal
  after termination and fail the run with `WellFormednessError` (live regression
  `run-e542c3c1`). `recover_atomic_child_output` carries the mirror case: a
  `budget_denied` child terminal re-raises as `WorkBudgetDenied` rather than as a
  hard recovery error, because the typed stop path owns it (selfstudy
  `run-9175f0ec`). Any new terminal status needs the same judgement made
  explicitly on both sides.
`check: grep -q "raise WorkBudgetDenied(terminal) from error" src/deepreason/workflow/transaction_service.py && grep -q "raise WorkBudgetDenied(selected.terminal)" src/deepreason/workflow/atomic_recovery.py && grep -q 'raise ValueError("atomic child is terminally failed")' src/deepreason/workflow/atomic_recovery.py && python -m pytest tests/test_config_referee.py::test_budget_denied_referee_terminates_typed_without_second_transition -q`
- **Two identical critic outputs are two effects, not one.** Epistemic
  identifiers are content addresses, so the same prose from two authorized
  attempts produces the same critic artifact id — and without `source:<call seq>`
  in the scrutiny `Measure` inputs the second attempt would silently dedupe into
  the first, making a coverage obligation look satisfied by an effect belonging to
  a different transaction. The structural check is in "Where it is expressed";
  `test_identical_critic_effects_remain_isolated_by_source_transaction` is the
  behavioural half.
- **Recovery downgraded prose authority to `observe_only` unconditionally —
  FIXED (defended-trial-wiring tranche, 2026-08-13).** `_recover_criticism_
  effect` used to pass `authority="observe_only"` unconditionally while the
  live path passed the resolved authority, so a manifest with `criticism_
  policy.authority == "defended_trial"` that crashed mid-criticism would have
  recovered the case as scrutiny evidence rather than as a trial-worthy case
  — exactly the operator's own diagnosed defect. Fixed by
  `_recovered_criticism_authority`, which resolves the run's real authority
  (`"defended_trial"` -> `"trial_required"`, mirroring `crit.py`'s own
  `_resolve_authority` mapping) instead of hardcoding. Recovery still cannot
  DISPATCH the trial itself (no provider boundary — see this document's own
  seam agreement and `DR-SUB-workflow`'s Traps entry on `DEFENDED_TRIAL_
  STEP`), so `rules/crit.py::_crit_argumentative_batch_result` defers a
  trial-worthy case (a typed, restart-safe `"defended-trial-deferred"`
  Measure) rather than either downgrading it to observed or crashing.
  Regression: `tests/test_v6_nonconjecture_recovery.py::
  test_recovered_observe_only_criticism_resumes_observe_only` and
  `::test_recovered_defended_trial_criticism_defers_an_attacking_case_
  instead_of_downgrading_to_observe_only`.
`check: python -c "import inspect; from deepreason.workflow import nonconjecture_recovery as N; from deepreason.rules import crit as R; assert 'authority=_recovered_criticism_authority(manifest, payload),' in inspect.getsource(N._recover_criticism_effect); assert 'authority=authority,' in inspect.getsource(R.crit_argumentative_batch); assert 'trial_required' in inspect.getsource(R._resolve_authority); assert 'defended_trial' in inspect.getsource(N._recovered_criticism_authority)" && grep -q "defended_trial" src/deepreason/run_manifest.py && grep -q "def test_recovered_observe_only_criticism_resumes_observe_only" tests/test_v6_nonconjecture_recovery.py && grep -q "def test_recovered_defended_trial_criticism_defers_an_attacking_case_instead_of_downgrading_to_observe_only" tests/test_v6_nonconjecture_recovery.py && python -m pytest tests/test_v6_nonconjecture_recovery.py::test_recovered_observe_only_criticism_resumes_observe_only tests/test_v6_nonconjecture_recovery.py::test_recovered_defended_trial_criticism_defers_an_attacking_case_instead_of_downgrading_to_observe_only -q`
- **Residue: hoisting a rule's workflow import to module scope is not an
  `ImportError`.** Re-measured at `9fa394d9`: adding
  `from deepreason.workflow.transaction_service import InquiryTransactionService`
  at the top of `conj.py` imports cleanly in both directions. The 32
  function-local imports are therefore held by the structural check in "The
  agreement" and by nothing else — the property they buy, every `rules/` module
  importable with no control plane loaded, has no behavioural test of its own.
  The generalisation is the one `DR-SEAM-llm-x-workflow` records about
  `retry_max`: a constraint whose violating case no fixture produces is tested by
  nothing.

- **A new exposure namespace is a RECOVERY change before it is a dispatch
  change.** P4 added `ContextNamespace.EVIDENCE` and `plan_kind="citable"` so a
  call's citable blocks appear in its exposure receipt. The criticism recovery
  path asserted that EVERY exposed entry was in the source namespace and that
  the alias map equalled the target catalog exactly — both true until a critic
  was shown evidence, and both would have refused the first resumed call that
  had been. The assertions now scope to source-namespace entries, and the
  namespace whitelist is explicit rather than implied.
  (`experiments/2026-08-16-change-p4-citable-evidence/`)
`check: python -m pytest tests/test_p4_citable_evidence.py::test_a_resumed_critic_tolerates_an_evidence_exposure_entry tests/test_v6_nonconjecture_recovery.py -q`
