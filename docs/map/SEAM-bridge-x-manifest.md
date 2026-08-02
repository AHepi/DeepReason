<!-- DR-SEAM-bridge-x-manifest -->
Verified-at: 08dcdf3c
Verify: python tools/docs_verify.py
Owns: src/deepreason/bridge/harness.py, src/deepreason/bridge/transactional_adapter.py, src/deepreason/bridge/derived.py, src/deepreason/run_manifest.py
Sides: DR-SUB-bridge, DR-SUB-manifest

# bridge x manifest

## The agreement

The manifest promises the bridge one immutable, already-validated authority
document: whether the run's final view is built in `grounded_two_stage` mode at
all, which roles carry the ledger, composition, review and repair seats, which
wire-contract versions those seats were qualified against, and a whole-workflow
retry ceiling — frozen before the first provider call and named by one digest.
The bridge promises in return that it **derives and never decides**. The
`BridgeWorkflowPolicy` a caller passes is treated as a claim to be checked
against the manifest's own historical v1 projection, not as authority; the
effective policy is computed purely from `bridge_policy` plus
`control_plane_policy.contract_versions`, and a disagreement is a typed refusal
rather than a default. The vocabulary is the manifest's to import, not the
bridge's to receive: `run_manifest.py` imports `WorkflowRetryPolicyV1` and
`BridgeWorkflowPolicy` so that a manifest can express itself in the bridge's
types, while the bridge holds exactly one `run_manifest` symbol at module
scope. The document is a plan, never evidence — the bridge reads eight of its
thirty-two fields, copies none of its content into the append-only record, and
stores only a 64-hex digest in the handful of records that name it. And the
bridge may not assume a manifest exists, is loadable, or is v6: three separate
fallbacks turn on `schema_version` and on the file's presence, because replaying
a stopped root must not depend on a document only today's loader can parse.

Three of the package's sixteen modules touch `run_manifest`, and only one of
those imports it at module scope; the reverse edge is the module-level one,
which is why every bridge-side manifest import is function-local. Eight manifest
attributes reach the bridge directly, out of thirty-two fields.
`check: test "$(grep -rl "deepreason\.run_manifest" --include=*.py src/deepreason/bridge | wc -l)" -eq 3 && test "$(grep -l "^from deepreason.run_manifest" src/deepreason/bridge/*.py | wc -l)" -eq 1 && grep -q "^from deepreason.run_manifest import resolve_route_seat_base_profile$" src/deepreason/bridge/transactional_adapter.py && grep -q "^from deepreason.bridge.retry import WorkflowRetryPolicyV1$" src/deepreason/run_manifest.py && ! grep -q "deepreason\.run_manifest" src/deepreason/bridge/retry.py && python -c "import re, pathlib; from deepreason.run_manifest import RunManifest; names=set(); [names.update(re.findall(r'(?<![a-z_])(?:bound_manifest|manifest)\.([a-z_0-9]+)', pathlib.Path('src/deepreason/bridge/%s.py' % f).read_text())) for f in ('harness','derived','transactional_adapter')]; expected={'bridge_policy','control_plane_policy','model_profile','roles','schema_version','scratch_policy','sha256','workload_profile'}; assert names == expected, sorted(names ^ expected); assert len(RunManifest.model_fields) == 32"`

## Where it is expressed

| Site | File | Symbol | What it enforces |
|---|---|---|---|
| Policy compiler | `run_manifest.py` | `BridgePolicy.workflow_policy` | the sole translation from manifest authority into `BridgeWorkflowPolicy`; composition version is derived from the ledger version, never supplied |
| Admissibility | `run_manifest.py` | v3+ branch of `RunManifest._production_routes_are_concrete` | a grounded bridge without a route for its ledger, composer or reviewer role, or with fewer reviewer routes than `reviewer_seats`, is not a valid manifest |
| Wire vocabulary | `run_manifest.py` | `ContractVersionPolicyV1/V2/V3` | which `bridge.ledger.*` / `bridge.composition.*` contract a run may speak; v6 pins the v3/v2 pair by `Literal` default |
| Repair grants | `run_manifest.py` | `_compile_contract_schema_repair_policy` | `bridge_policy.max_schema_repair_attempts` clamped to 0..2 and expanded into per-contract-id grants — the compile-time seed, not the runtime ceiling |
| Decomposition edges | `run_manifest.py` | `_compile_route_seat_contract_decomposition_plan` | `bridge.ledger.v3 → bridge.ledger-batch.v1` and `bridge.composition.v2 → bridge.composition-batch.v1`, seat 0 only |
| Qualification inventory | `run_manifest.py` | `_route_seat_behavioral_contract_assignments` | which bridge contract/seat pairs the doctor battery must exercise before a run may launch |
| Digest binding | `bridge/harness.py` | `_bound_manifest_digest` | the supplied `run_manifest_digest` must equal the root's `run-manifest.sha256` sidecar |
| Scratch coverage | `bridge/harness.py` | `_bound_scratch_attention_policy` | an attention pack may be used only under a v3–v6 manifest whose `scratch_policy` is enabled; the coverage knob is the manifest's, not the caller's |
| Authority derivation | `bridge/harness.py` | `_bound_bridge_execution`, `_derive_bridge_execution_policy` | caller policy == historical v1 projection, effective contract version from the control plane, retry ceiling from `control.workflow_retry`, lease from `roles[ledger_role][0]` |
| Pure preflight | `bridge/harness.py` | `preflight_bound_bridge_policy` | the application layer can validate bridge authority against a manifest with no root, no adapter and no mutation |
| Lease agreement | `bridge/harness.py` | `_assert_adapter_matches_retry_lease` | runtime endpoint wiring must still be the manifest-derived lease, or `BRIDGE_WORKFLOW_RETRY_ROUTE_CHANGED` before dispatch |
| v6 exactness | `bridge/transactional_adapter.py` | `TransactionalBridgeAdapter.__init__` | `schema_version == 6`, the frozen v3/v2 contract pair, `model_profile` identity, `leases_from_manifest` equality, and one manifest digest across adapter, harness, replay state and every prior transaction |
| Per-call contract gate | `bridge/transactional_adapter.py` | `_EXACT_V6_CONTRACTS`, `.call` | each bridge template role may only present the contract ids the manifest qualified for it |
| Per-seat presentation | `bridge/transactional_adapter.py` | `resolve_route_seat_base_profile` | the model profile for a bridge stage is the manifest's frozen seat profile; an override raises `V6ModelProfileOverrideForbidden` |
| Version admission | `runtime/launch_policy.py` | `require_v6_launch_allowed`, `resolve_effective_run_manifest` | the bridge delegates "may this manifest launch at all" rather than re-deciding it |
| Derived destination | `bridge/derived.py` | `build_derived_bridge` | the destination root's own bound manifest must be grounded, text-profile, and digest-equal to the supplied one (see Traps — the version pin is unreachable) |
| Live qualification | `cli/doctor.py` | `_production_bridge_ledger_probe`, `_production_bridge_composition_probe`, `_production_grounding_probe`, `ProductionContractPairV1.contract_id` | the manifest's battery constructs the bridge's real wire contracts and closes the contract-id vocabulary |

The compiler pairs the two contract versions and cannot express a split, the
manifest's `BridgePolicy` is strictly narrower than the `BridgeWorkflowPolicy`
it compiles into, and a missing route is refused on the manifest side at
validation and again on the bridge side at derivation with two different typed
codes.
`check: python -c "from deepreason.run_manifest import BridgePolicy; from deepreason.bridge.workflow import BridgeWorkflowPolicy; p=BridgePolicy(mode='grounded_two_stage',allow_partial=True,allow_abstention=True,require_claim_ledger=True,require_claim_uses=True,grounding_review=True,max_schema_repair_attempts=0,max_grounding_repair_attempts=1,output_section_limit=8,target_profile='plain',ledger_role='summarizer',composer_role='thesis',reviewer_role='judge',grounding_repair_role='judge'); assert p.workflow_policy(ledger_contract_version='v3').composition_contract_version=='v2'; assert p.workflow_policy(ledger_contract_version='v2').composition_contract_version=='v1'; assert BridgeWorkflowPolicy.model_fields['max_ledger_amendments'].annotation.__args__==(0,1); assert BridgePolicy.model_fields['max_ledger_amendments'].annotation.__args__==(1,)" && grep -q 'f"BRIDGE_{task.upper()}_ROUTE_REQUIRED: "' src/deepreason/run_manifest.py && grep -q 'raise ValueError("BRIDGE_LEDGER_ROUTE_REQUIRED")' src/deepreason/bridge/harness.py && python -m pytest tests/test_run_manifest_scratch_bridge.py -q`

The digest gate compares against the sidecar and refuses a mismatch, but a
missing sidecar is a silent pass-through, and the file name is a bridge-side
literal rather than the manifest's exported constant.
`check: python -c "import pathlib, tempfile, pytest; from deepreason.bridge.harness import _bound_manifest_digest as B, _bound_scratch_attention_policy as S; from deepreason.run_manifest import MANIFEST_HASH_NAME as H; r=pathlib.Path(tempfile.mkdtemp()); d='a'*64; assert B(r,d)==d and S(r,d,None) is None; (r/H).write_text('b'*64); pytest.raises(ValueError, B, r, d).match('BRIDGE_MANIFEST_MISMATCH'); assert H=='run-manifest.sha256'" && grep -q 'path = root / "run-manifest.sha256"' src/deepreason/bridge/harness.py`

The four bridge contract ids are defined in the bridge and re-declared as bare
literals on the manifest side, in the compilers and in the doctor's closed
`Literal`; nothing derives one from the other.
`check: python -c "import typing; from deepreason.cli.doctor import ProductionContractPairV1, _production_bridge_ledger_probe, _production_bridge_composition_probe; ids=set(typing.get_args(ProductionContractPairV1.model_fields['contract_id'].annotation)); assert {'bridge.ledger.v3','bridge.ledger-batch.v1','bridge.composition.v2','bridge.composition-batch.v1'} <= ids; assert _production_bridge_ledger_probe()[0].contract_id=='bridge.ledger.v3'; assert _production_bridge_composition_probe()[0].contract_id=='bridge.composition.v2'" && for c in bridge.ledger.v3 bridge.ledger-batch.v1; do grep -q "self.contract_id = \"$c\"" src/deepreason/bridge/ledger.py || exit 1; done && for c in bridge.composition.v2 bridge.composition-batch.v1; do grep -q "self.contract_id = \"$c\"" src/deepreason/bridge/compose.py || exit 1; done && for c in bridge.ledger.v3 bridge.ledger-batch.v1 bridge.composition.v2 bridge.composition-batch.v1; do grep -q "\"$c\"" src/deepreason/run_manifest.py || exit 1; done`

Six of the ten qualification pairs a v6 manifest projects are bridge contracts,
and every one of them is seat 0.
`check: python -m pytest "tests/test_cli_production_doctor_v6.py::test_matrix_preserves_core_pairs_and_adds_enabled_grounding_pairs" -q && grep -q "seat, route = next(iter(enumerate(routes)))" src/deepreason/bridge/harness.py && grep -q "    reviewer_seat: Literal\[0\] = 0" src/deepreason/run_manifest.py && grep -q "(contracts.bridge_ledger_wire_contract, bridge.ledger_role, 0)" src/deepreason/run_manifest.py`

A pre-v4 manifest gets the caller's policy back verbatim with retries disabled
and no lease, and an absent manifest keeps the same fallback — unless a
transactional adapter is present, in which case both are
`BRIDGE_MANIFEST_MISMATCH`, because the v6 path is exact in both directions: the
adapter refuses anything but schema 6 and the frozen contract pair, and the real
application build resolves v3/v2 from the manifest rather than from what it
passed down.
`check: python -c "import types; from deepreason.bridge.harness import _derive_bridge_execution_policy as D; from deepreason.bridge.workflow import BridgeWorkflowPolicy; from deepreason.bridge.retry import WorkflowRetryPolicyV1; s=BridgeWorkflowPolicy(grounding_review=False, composer_role='summarizer'); e,r,l=D(types.SimpleNamespace(schema_version=3), s); assert e==s and l is None and r==WorkflowRetryPolicyV1() and r.max_workflow_retries==0" && grep -q "if manifest.schema_version != 6:" src/deepreason/bridge/transactional_adapter.py && grep -q "v6 bridge adapter requires the frozen v3/v2 contract pair" src/deepreason/bridge/transactional_adapter.py && python -m pytest tests/test_v6_bridge_transactions.py::test_nontransactional_manifest_absent_bridge_retains_legacy_fallback tests/test_v6_bridge_transactions.py::test_transactional_bridge_missing_manifest_fails_before_any_mutation tests/test_v6_bridge_transactions.py::test_real_application_bridge_uses_harness_derived_v3_v2_policy tests/test_v6_bridge_transactions.py::test_transactional_bridge_replaced_manifest_fails_before_any_mutation -q`

## What is deliberately absent

**Replay never opens the manifest.** `bridge/state.py` rebuilds the entire
advisory bridge state from the log and compares manifest *digests* carried
inside typed records — the retry attempt fence against the failure's
`run_manifest_digest` — but imports nothing from `run_manifest`. This is
load-bearing rather than incidental: `load_run_manifest` accepts only schema 6,
so a replay path that needed the document would make every pre-v6 root
unverifiable, and a change that invalidates existing replay-valid roots is wrong
by definition (`DR-INV-frozen-surfaces`).
`check: ! grep -q "deepreason\.run_manifest" src/deepreason/bridge/state.py && grep -q "^def rebuild_bridge_state(" src/deepreason/bridge/state.py && grep -q "run_manifest_digest" src/deepreason/bridge/state.py && python -c "from deepreason.run_manifest import LATEST_SCHEMA_VERSION; assert LATEST_SCHEMA_VERSION == 6"`

**Thirteen of the sixteen bridge modules have no notion of a manifest at all.**
The stage machine, the ledger, the composer, the validators, the evidence pack,
review and repair receive contract selection as a plain
`Literal["v1","v2","v3"]` string. `ledger.py` and `compose.py` define the very
contract ids the manifest names and still never read the manifest that names
them. Widening any of them to take a `RunManifest` would put document parsing on
the path that must run during replay.
`check: for f in ledger compose workflow validate evidence_pack review repair state models events operations retry; do grep -q "deepreason\.run_manifest" src/deepreason/bridge/$f.py && exit 1; done; grep -q 'contract_version: Literal\["v1", "v2", "v3"\] = "v1",' src/deepreason/bridge/ledger.py && grep -q 'ledger_contract_version: Literal\["v1", "v2", "v3"\] = "v1"' src/deepreason/bridge/workflow.py && grep -q "^def assemble_evidence_pack(" src/deepreason/bridge/evidence_pack.py`

**No manifest content ever enters the record.** Across every Pydantic model in
the package, exactly five fields mention a manifest and all five are strings —
`run_manifest_digest` on the terminal result and the failure, `manifest_digest`
on the retry attempt fence, `manifest_sha256` on the two operation markers. A
role name, a contract version or a policy object stored in a bridge record would
give a replay two sources of truth about authority.
`check: python -c "import importlib, inspect; from pydantic import BaseModel; mods=[importlib.import_module('deepreason.bridge.'+n) for n in ('models','retry','harness','operations','state','workflow','ledger','compose','validate','review','repair','evidence_pack','events','derived','transactional_adapter')]; found={(o.__name__,f):i.annotation for m in mods for o in vars(m).values() if inspect.isclass(o) and issubclass(o,BaseModel) for f,i in o.model_fields.items() if 'manifest' in f}; assert len(found)==5, sorted(found); assert all(a in (str, str|None) for a in found.values()), sorted(found)"`

**The bridge never writes, binds or exports a manifest.** Binding one document
to one root is `application/bridge.py`'s job; the bridge only ever compares.
`check: ! grep -rq "bind_run_manifest\|persist_run_manifest\|write_run_manifest" --include=*.py src/deepreason/bridge && grep -q "from deepreason.run_manifest import bind_run_manifest" src/deepreason/application/bridge.py && grep -q "^def bind_run_manifest(" src/deepreason/run_manifest.py`

**The manifest fields a reader expects the bridge to consult, it does not.**
`route_seat_presentation_plan` is reached only through
`resolve_route_seat_base_profile`, and the route leases only through
`leases_from_manifest`, which reads `roles`. The behavioural capability plan and
`contract_schema_repair_policy` are never opened here: the doctor projects the
pair inventory from the former, and `llm/adapter.py` and `workflow/` resolve the
repair grant through `resolve_route_seat_behavioral_capability`. `budget_policy`,
`stop_policy`, `memory_policy`, `criticism_policy`, `inquiry_capability_policy`
and `run_input_digest` are not read at all — in particular the question does not
come from the manifest, because the evidence pack is assembled from the log at a
pinned fence, so what the answer is about comes from the record, not the plan.
`check: ! grep -rq "run_input_digest\|budget_policy\|stop_policy\|memory_policy\|criticism_policy\|inquiry_capability_policy\|route_seat_presentation_plan\|route_seat_behavioral_capability_plan\|contract_schema_repair_policy\|resolve_route_seat_behavioral_capability" --include=*.py src/deepreason/bridge && grep -q "^def resolve_route_seat_base_profile(" src/deepreason/run_manifest.py && grep -q "^    route_seat_presentation_plan" src/deepreason/run_manifest.py && grep -q "^    contract_schema_repair_policy" src/deepreason/run_manifest.py && grep -q "    resolve_route_seat_behavioral_capability," src/deepreason/llm/adapter.py`

**`bridge_policy.max_schema_repair_attempts` is NOT the runtime repair ceiling.**
It is a compile-time seed: `_compile_contract_schema_repair_policy` clamps it to
0..2 and writes per-contract grants, and the runtime honours the *grant*. A
manifest whose `bridge_policy` says zero can still repair a bridge contract once
if that contract's grant says one. Reading the bridge policy to predict runtime
repair behaviour is reading the wrong field.
`check: grep -q "bridge_ceiling = min(2, max(0, bridge_policy.max_schema_repair_attempts))" src/deepreason/run_manifest.py && python -m pytest "tests/test_v6_bridge_transactions.py::test_bridge_runtime_uses_contract_grant_not_bridge_policy_ceiling" "tests/test_v6_bridge_transactions.py::test_grounding_direct_contracts_use_their_canonical_zero_grants" -q`

**A bridge wire-schema change does not move the qualification subject digest.**
The subject's pair inventory is route and contract *identity* — contract id,
role, seat, endpoint, route fingerprint, model, provider, family, output
mechanism — and carries no fingerprint of the contract's JSON schema. So editing
`ClaimLedgerWireV2`'s fields leaves every cached "qualified" verdict in place for
a shape the provider was never probed against. That is the exact failure mode
`DR-SUB-manifest` records from the `live_jolt_2026-07-31` epoch boundary, where
a contract field — not qualification code — dropped a subject to `shallow`.
Clear the cache by hand when you change a bridge contract's wire shape.
`check: python -c "from deepreason.cli.doctor import ProductionContractPairV1; assert set(ProductionContractPairV1.model_fields) == {'pair_id','contract_id','role','seat','endpoint_id','route_sha256','model_id','model_revision','provider','family','output_mechanism'}" && grep -q 'return pair.model_dump(mode="json", exclude={"pair_id"})' src/deepreason/qualification.py && grep -q '"pair_inventory": pairs' src/deepreason/qualification.py`

**`bridge/retry.py` has no manifest activation of its own, and cannot acquire
one.** It is the module `run_manifest.py` imports at module scope, so the edge
is one-way by construction: the retry ceiling arrives as a
`WorkflowRetryPolicyV1` the manifest already froze, and a default-constructed
policy permits no retry. Adding a manifest lookup inside `retry.py` closes the
import cycle rather than adding a feature. Covered by the surface check above.

**No seat selection anywhere.** The ledger lease is `roles[ledger_role][0]`, the
manifest pins `reviewer_seat` to `Literal[0]`, and the qualification pairs are
projected at seat 0. A multi-seat bridge is not a knob that is off; it is a
concept neither side has.

## How to change it

1. **Read `DR-INV-frozen-surfaces` first.** The manifest side is surface 4
   (schemas *and* validators) and surface 5 (anything entering a qualification
   subject digest). Every field you add to `BridgePolicy` or
   `ContractVersionPolicyV3` is permanent, and it moves every subject digest —
   a cache miss costing the whole battery (~14 min, ~1160 calls). A per-run knob
   belongs on `Config`, never here.
2. **Decide whether you are changing authority or contract.** Authority (what a
   run may do: review on/off, ceilings, roles) is `BridgePolicy` plus
   `workflow_policy`, and stops there. A contract (which wire version a seat
   speaks) is a seven-site change: `ContractVersionPolicyV3`, the mapping in
   `_derive_bridge_execution_policy`, `BridgeWorkflowPolicy`'s literals,
   `_EXACT_V6_CONTRACTS`, `ProductionContractPairV1.contract_id`,
   `_compile_contract_schema_repair_policy`, and
   `_compile_route_seat_contract_decomposition_plan`.
3. **Keep the mapping total.** Every `bridge_ledger_wire_contract` literal any
   `ContractVersionPolicy*` can carry must be a key of the dict in
   `_derive_bridge_execution_policy`, or authority derivation dies on a bare
   `KeyError` (see Traps).
4. **Know who the v1-projection comparison is actually for.** Both sides call
   the same function — `application/bridge.py`'s `_historical_bridge_caller_policy`
   is literally `manifest.bridge_policy.workflow_policy(ledger_contract_version="v1")`,
   and that is exactly what `_derive_bridge_execution_policy` compares against —
   so the in-repo path can never trip `BRIDGE_WORKFLOW_POLICY_MISMATCH`. It fires
   only for a caller that hand-builds a `BridgeWorkflowPolicy`, which every
   fixture and every out-of-tree client does. Adding a field to
   `BridgeWorkflowPolicy` therefore breaks hand-built callers and leaves the
   application path green — the worst signal shape. See `DR-SUB-bridge`'s first
   trap for why the projection says `"v1"` at all.
`check: python -c "import inspect, typing; from deepreason import run_manifest as rm; from deepreason.bridge import harness as bh; src = inspect.getsource(bh._derive_bridge_execution_policy); declared = set(); [declared.update(typing.get_args(c.model_fields['bridge_ledger_wire_contract'].annotation)) for c in (rm.ContractVersionPolicyV1, rm.ContractVersionPolicyV2, rm.ContractVersionPolicyV3)]; missing = sorted(v for v in declared if '\"%s\"' % v not in src); assert declared and not missing, missing" && grep -q 'return manifest.bridge_policy.workflow_policy(ledger_contract_version="v1")' src/deepreason/application/bridge.py && grep -q 'historical_projection = bridge.workflow_policy(ledger_contract_version="v1")' src/deepreason/bridge/harness.py && python -m pytest tests/test_v6_bridge_transactions.py::test_v6_application_supplies_only_historical_bridge_caller_projection -q`
5. **Move the ledger and composition versions together.** Both sides refuse a
   split pair: `BridgePolicy.workflow_policy` derives the composition version
   from the ledger version, and `BridgeWorkflowPolicy`'s validator rejects the
   mismatch outright.
6. **Never give the replay path a manifest.** If a new agreement needs manifest
   data at replay time, put the value in the typed record at write time instead.
7. **Re-run the battery, and clear the cache first, if a bridge wire schema
   moved.** The subject digest will not notice for you.

What breaks first, in the order you will see it:
`BRIDGE_WORKFLOW_POLICY_MISMATCH` at build time before any model call, in every
fixture and hand-built caller but never on the application path; then a
bare `KeyError` from the contract mapping; then
`"v6 bridge adapter requires the frozen v3/v2 contract pair"` at adapter
construction; then `BRIDGE_LEDGER_ROUTE_REQUIRED`; then
`"bridge.ledger.v3 and bridge.composition.v2 must be selected together"`. The
expensive one arrives last and only live: a doctor tier drop to `shallow`, which
refuses `reason` at preparation with `QUALIFICATION_TIER_SHALLOW`.

The tests that catch you, cheapest first:
`tests/test_run_manifest_scratch_bridge.py` (0.2 s, manifest-side admissibility),
`tests/test_cli_production_doctor_v6.py -k "pairs or matrix"` (2 s, the pair
projection), `tests/test_bridge_workflow_retry.py` (policy freezing), then
`tests/test_v6_bridge_transactions.py` (minutes; the whole v6 authority chain).

## Traps

- **The derived-bridge manifest gate cannot be satisfied in production.**
  `build_derived_bridge` requires the destination's bound manifest to be
  `schema_version == 3`, but `load_run_manifest` admits only schema 6 — so a v6
  destination raises `BRIDGE_DERIVED_MANIFEST_V3_REQUIRED` and a genuine v3 file
  raises `UnsupportedRunManifestVersionError`, caught and re-raised as
  `BRIDGE_DERIVED_MANIFEST_INVALID`. The path's only coverage,
  `tests/test_bridge_derived.py`, passes because an autouse fixture monkeypatches
  `load_run_manifest` to a raw `model_validate_json` that skips version
  discrimination. **Residue: this is a code-reading finding plus the check below,
  not an observed live failure** — no recorded root has attempted a derived build
  since the v6-only loader landed. Read this before concluding that a derived
  build "should just work".
`check: python -c "import inspect, json, pathlib, tempfile, pytest; from deepreason.run_manifest import LATEST_SCHEMA_VERSION as L, load_run_manifest as LR, UnsupportedRunManifestVersionError as U; from deepreason.bridge import derived; src=inspect.getsource(derived.build_derived_bridge); assert 'manifest.schema_version != 3' in src and 'BRIDGE_DERIVED_MANIFEST_V3_REQUIRED' in src and L==6; p=pathlib.Path(tempfile.mkdtemp())/'run-manifest.json'; p.write_bytes(json.dumps({'schema_version':3,'roles':{}}).encode()); pytest.raises(U, LR, p, verify_hash=False)" && grep -q "deepreason.run_manifest.load_run_manifest" tests/test_bridge_derived.py`
- **An unmapped ledger contract dies untyped, and it dies late.** The
  `{bridge.ledger.v1|v2|v3} -> {v1|v2|v3}` lookup in
  `_derive_bridge_execution_policy` is a bare dict subscript, and it runs *after*
  the caller-policy comparison. Add a literal to `ContractVersionPolicyV3`
  without adding the key and the failure is a `KeyError` naming only the string —
  no `BRIDGE_*` code, nothing that says which of the two sides is behind.
`check: python -c "import types, pytest; from deepreason.run_manifest import BridgePolicy; from deepreason.bridge.harness import _derive_bridge_execution_policy as D; b=BridgePolicy(mode='grounded_two_stage', allow_partial=True, allow_abstention=True, require_claim_ledger=True, require_claim_uses=True, grounding_review=True, max_schema_repair_attempts=0, max_grounding_repair_attempts=1, output_section_limit=8, target_profile='plain', ledger_role='summarizer', composer_role='thesis', reviewer_role='judge', grounding_repair_role='judge'); c=types.SimpleNamespace(contract_versions=types.SimpleNamespace(bridge_ledger_wire_contract='bridge.ledger.v4'), workflow_retry=None); m=types.SimpleNamespace(schema_version=6, control_plane_policy=c, bridge_policy=b, roles={'summarizer':()}); pytest.raises(KeyError, D, m, b.workflow_policy(ledger_contract_version='v1')).match('bridge.ledger.v4')"`
- **Renaming the digest sidecar turns the digest check off instead of breaking
  it.** `_bound_manifest_digest` hardcodes `"run-manifest.sha256"` while the same
  function's neighbours import `MANIFEST_NAME` from `run_manifest`. A missing
  sidecar is not an error — the supplied digest is returned unverified — so
  changing `MANIFEST_HASH_NAME` on the manifest side leaves the bridge looking
  for a file that no longer exists and silently accepting any digest a caller
  passes. Covered by the sidecar check above; the fix if you rename it is to
  import the constant, not to add a second literal.
- **Reading `bridge_policy` to predict runtime behaviour.** Two of its fields are
  seeds rather than settings: `max_schema_repair_attempts` seeds the contract
  grants (above) and `ledger_role`/`composer_role` seed a lease that
  `_assert_adapter_matches_retry_lease` will re-check against live wiring. The
  contract *version* is not on `bridge_policy` at all — it is on the control
  plane, which is why the caller's policy legitimately says `"v1"` while the run
  executes v3/v2.
- **Assuming the guard is on the side you are editing.** "Which bridge contracts
  must be qualified" is decided in `run_manifest.py` and `cli/doctor.py`, not in
  `bridge/`; "how many schema repairs a bridge call gets" is decided in
  `llm/adapter.py`, not in either side's bridge code. Searching `bridge/` for
  those enforcements and finding nothing is the expected result.
