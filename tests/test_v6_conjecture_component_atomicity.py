"""V6 conjecture admits valid components without cross-component corruption."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from deepreason.canonical import canonical_json
from deepreason.capabilities.enums import CapabilityLifecycle
from deepreason.capabilities.policy import (
    InquiryCapabilityPolicyV1,
    SimulationInputBindingV1,
)
from deepreason.capabilities.simulation import SimulationCapabilityController
from deepreason.config import Config
from deepreason.rules.conj import conj
from deepreason.run_manifest import (
    ConjectureContextPolicyV1,
    ControlPlanePolicyV3,
    ScratchAuthoringPolicyV1,
    ToolchainEntry,
    compile_run_manifest,
)
from deepreason.scheduler.scheduler import Scheduler
from deepreason.scratch.service import ScratchService
from deepreason.workflow.transaction import ContextNamespace
from tests.test_v6_transaction_qualification import (
    _control,
    _route,
    _config,
    _live_adapter,
    _manifest,
    _seed_live_conjecture,
    _simulation_policy,
    _v6_simulation_turn,
)


def _component_diagnostics(harness, work) -> list[dict]:
    admission = next(iter(work.admissions.values()))
    return [json.loads(harness.blobs.get(ref)) for ref in admission.diagnostic_refs]


def test_valid_candidate_and_invalid_optional_scratch_complete_partially(tmp_path):
    policy = ScratchAuthoringPolicyV1(
        enabled=True,
        maximum_new_blocks_per_turn=1,
        maximum_revisions_per_turn=1,
        maximum_links_per_turn=0,
        maximum_unresolved_questions_per_turn=0,
        maximum_cluster_suggestions_per_turn=0,
        maximum_total_bytes=32_768,
    )
    config = _config()
    manifest = _manifest(scratch_authoring=policy)
    harness = ScratchService(tmp_path / "invalid-optional-scratch").harness
    _seed_live_conjecture(harness)
    response = {
        "candidates": [
            {
                "content": "A valid reversible formal mechanism.",
                "typicality": 0.23,
            }
        ],
        "scratch_proposal": {
            "revisions": [
                {
                    "target_alias": "SCR_999",
                    "body": {"content": "This optional revision names no visible scratch."},
                }
            ]
        },
    }
    adapter, _endpoint = _live_adapter(harness, manifest, [json.dumps(response)])

    registered = conj(
        harness,
        "pi-live-v6",
        adapter,
        config,
        workload_profile="text",
        run_manifest=manifest,
    )

    (artifact,) = registered
    (work,) = harness.workflow_state.transaction_work.values()
    (admission,) = work.admissions.values()
    assert artifact.id in harness.state.artifacts
    assert artifact.id in admission.admitted_refs
    assert not ScratchService(harness).state.blocks
    assert work.terminal.status == "completed"
    assert work.terminal.reason_code == "semantic_admission_partial"
    assert admission.outcome == "admitted"
    diagnostics = _component_diagnostics(harness, work)
    assert diagnostics == [
        {
            "component": "scratch",
            "disposition": "omitted",
            "error_code": "SCRATCH_ALIAS_UNKNOWN",
            "error_type": "ScratchAuthoringError",
            "message": ("SCRATCH_ALIAS_UNKNOWN: unknown scratch proposal reference(s): SCR_999"),
            "partial_refs": [],
            "phase": "semantic_validation",
            "schema": "conjecture-component-diagnostic.v1",
        }
    ]


def test_simulation_materialization_failure_admits_valid_partial_components(
    tmp_path,
    monkeypatch,
):
    config = _config()
    manifest = _manifest(simulation=_simulation_policy())
    harness = ScratchService(tmp_path / "simulation-materialization-failure").harness
    _seed_live_conjecture(harness)
    response = _v6_simulation_turn()
    response["candidates"] = [
        {
            "content": "A formal mechanism independent of simulation bookkeeping.",
            "typicality": 0.31,
        }
    ]
    second = json.loads(json.dumps(response["simulation_proposals"][0]))
    second["request_identifier"] = "v6-second-discriminator"
    second["hypothesis"] = "The second bounded rival remains below nine units."
    response["simulation_proposals"].append(second)
    adapter, _endpoint = _live_adapter(harness, manifest, [json.dumps(response)])

    def materialize_one_then_fail(
        controller,
        drafts,
        *,
        preparation,
        provider_attempt,
        source_call_seq,
    ):
        controller.propose_transactional(
            drafts[0],
            proposal_index=0,
            preparation=preparation,
            provider_attempt=provider_attempt,
            source_call_seq=source_call_seq,
        )
        raise RuntimeError("injected simulation materialization failure")

    monkeypatch.setattr(
        SimulationCapabilityController,
        "materialize_transactional_proposals",
        materialize_one_then_fail,
    )

    registered = conj(
        harness,
        "pi-live-v6",
        adapter,
        config,
        workload_profile="text",
        run_manifest=manifest,
    )

    (artifact,) = registered
    (proposal,) = harness.capability_state.proposals.values()
    (work,) = harness.workflow_state.transaction_work.values()
    (admission,) = work.admissions.values()
    assert work.terminal.status == "completed"
    assert work.terminal.reason_code == "semantic_admission_partial"
    assert admission.outcome == "admitted"
    assert artifact.id in admission.admitted_refs
    assert proposal.id in admission.admitted_refs
    assert len(harness.capability_state.proposals) == 1
    SimulationCapabilityController(harness, manifest).require_transactional_origin(proposal)
    (diagnostic,) = _component_diagnostics(harness, work)
    assert diagnostic["component"] == "simulation"
    assert diagnostic["phase"] == "materialization"
    assert diagnostic["disposition"] == "partial"
    assert diagnostic["partial_refs"] == [proposal.id]
    assert diagnostic["error_type"] == "RuntimeError"
    assert diagnostic["message"] == "injected simulation materialization failure"


def _scratch_simulation_manifest():
    scratch_authoring = ScratchAuthoringPolicyV1(
        enabled=True,
        maximum_new_blocks_per_turn=1,
        maximum_revisions_per_turn=1,
        maximum_links_per_turn=0,
        maximum_unresolved_questions_per_turn=0,
        maximum_cluster_suggestions_per_turn=0,
        maximum_total_bytes=32_768,
    )
    config = Config(
        N_SCHOOLS=0,
        roles={
            "conjecturer": [_route("conjecturer-route")],
            "synthesizer": [_route("synthesizer-route")],
            "summarizer": [_route("summarizer-route")],
        },
        scratchpad={
            "enabled": True,
            "max_blocks_per_pack": 4,
            "max_guides_per_pack": 0,
            "semantic_retrieval": False,
            "keyword_retrieval": True,
            "coverage_enabled": False,
            "exploratory_fraction": 0,
            "underexposed_fraction": 0,
        },
    )
    context_policy = ConjectureContextPolicyV1(
        mode="harness_only",
        initial_max_blocks=2,
        initial_max_guides=0,
        max_context_expansion_requests=0,
        max_extra_blocks=0,
        permitted_retrieval_channels=("keyword", "recent", "loose"),
        coverage_slot_mandatory=False,
        exploration_slot_mandatory=False,
    )
    control_values = _control(scratch_authoring=scratch_authoring).model_dump(mode="python")
    control_values["conjecture_context"] = context_policy.model_dump(mode="python")
    control = ControlPlanePolicyV3.model_validate(control_values)
    sealed_value = {"weight_bytes": 12}
    sealed_input = SimulationInputBindingV1(
        alias="WEIGHT_INPUT",
        description="Frozen weight input; never derived from scratch.",
        value=sealed_value,
        content_sha256=hashlib.sha256(canonical_json(sealed_value)).hexdigest(),
    )
    simulation = _simulation_policy(input_catalog=(sealed_input,))
    version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    manifest = compile_run_manifest(
        config,
        schema_version=6,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at="2026-07-17T00:00:00Z",
        control_plane_policy=control,
        inquiry_capability_policy=InquiryCapabilityPolicyV1(
            capability_profile="inquiry-capabilities.v2",
            simulation=simulation,
        ),
        run_input_digest="f" * 64,
        toolchains=(
            ToolchainEntry(
                id=simulation.python_toolchain_identity,
                runner="local",
                executable=str(Path(sys.executable).resolve()),
                version_output_sha256=hashlib.sha256(version.encode("utf-8")).hexdigest(),
                network=False,
            ),
        ),
    )
    return config, manifest, sealed_value


def test_real_scratch_retrieve_simulate_revise_then_fresh_formal(tmp_path):
    config, manifest, sealed_value = _scratch_simulation_manifest()
    harness = ScratchService(tmp_path / "scratch-simulation-lifecycle").harness
    _seed_live_conjecture(harness)
    prompts: list[str] = []

    simulation_turn = _v6_simulation_turn()
    simulation_turn["simulation_proposals"][0]["input_aliases"] = ["SIM_001"]
    simulation_turn["simulation_proposals"][0]["declared_assumptions"] = [
        (
            "Advisory provenance SCR_001 motivated this discriminating setup; "
            "SCR_001 is not a simulation input or formal premise."
        )
    ]

    def response(prompt: str) -> str:
        prompts.append(prompt)
        if len(prompts) == 1:
            return json.dumps(
                {
                    "scratch_proposal": {
                        "new_blocks": [
                            {
                                "local_key": "NEW_001",
                                "body": {
                                    "content": (
                                        "Invent one provisional mechanism in advisory "
                                        "scratch: delayed feedback may reverse the effect."
                                    ),
                                    "unfinished": (
                                        "Stretch this mechanism with a discriminating "
                                        "simulation before proposing it formally."
                                    ),
                                },
                            }
                        ]
                    }
                }
            )
        if len(prompts) == 2:
            assert "SCR_001" in prompt
            assert "SIM_001" in prompt
            return json.dumps(simulation_turn)
        if len(prompts) == 3:
            assert "SCR_001" in prompt
            assert "SIM_002: recorded simulation result" in prompt
            return json.dumps(
                {
                    "candidates": [
                        {
                            "content": (
                                "A fresh formal delayed-feedback proposal, independently "
                                "stated after the recorded simulation."
                            ),
                            "typicality": 0.19,
                        }
                    ],
                    "scratch_proposal": {
                        "revisions": [
                            {
                                "target_alias": "SCR_001",
                                "body": {
                                    "content": (
                                        "Revised advisory mechanism after the negative "
                                        "simulation: delayed feedback needs a threshold."
                                    ),
                                    "unfinished": (
                                        "Still imaginative scratch, not evidence or formal support."
                                    ),
                                },
                            }
                        ]
                    },
                }
            )
        raise AssertionError("unexpected extra provider dispatch")

    adapter, _endpoint = _live_adapter(harness, manifest, response)

    assert (
        conj(
            harness,
            "pi-live-v6",
            adapter,
            config,
            workload_profile="text",
            run_manifest=manifest,
        )
        == []
    )
    scratch_service = ScratchService(harness)
    (original,) = scratch_service.state.blocks.values()
    assert original.provenance.origin == "transactional-scratch-authoring.v1"

    assert (
        conj(
            harness,
            "pi-live-v6",
            adapter,
            config,
            workload_profile="text",
            run_manifest=manifest,
        )
        == []
    )
    (proposal,) = harness.capability_state.proposals.values()
    assert proposal.input_aliases == ("SIM_001",)
    assert "SCR_001" in proposal.declared_assumptions[0]
    origin = harness.workflow_state.transaction_work[proposal.originating_work_order_ref]
    (scratch_plan,) = (plan for plan in origin.plans.values() if plan.plan_kind == "scratch")
    (simulation_plan,) = (plan for plan in origin.plans.values() if plan.plan_kind == "simulation")
    (scratch_item,) = scratch_plan.items
    (simulation_item,) = simulation_plan.items
    assert scratch_item.namespace == ContextNamespace.SCRATCH
    assert scratch_item.alias == "SCR_001"
    assert scratch_item.object_ref == original.id
    assert simulation_item.namespace == ContextNamespace.SIMULATION
    assert simulation_item.alias == "SIM_001"
    assert simulation_item.object_ref == "WEIGHT_INPUT"
    assert simulation_item.object_ref != original.id

    scheduler = Scheduler(
        harness,
        adapter,
        config,
        workload_profile="text",
        run_manifest=manifest,
    )
    scheduler.step()
    (package,) = harness.capability_state.result_packages.values()
    package_event_seq = next(
        event.seq for event in harness.log.read() if package.id in event.outputs
    )
    transition = harness.capability_state.transitions[
        harness.capability_state.current_transition_by_request[proposal.id]
    ]
    assert transition.lifecycle == CapabilityLifecycle.RESULT_PACKAGED

    scheduler.step()
    transition = harness.capability_state.transitions[
        harness.capability_state.current_transition_by_request[proposal.id]
    ]
    assert transition.lifecycle == CapabilityLifecycle.CONSUMED
    (consumption,) = harness.capability_state.consumptions.values()
    assert consumption.follow_up_work_order_ref != origin.preparation.id

    blocks = tuple(scratch_service.state.blocks.values())
    revised = next(block for block in blocks if block.revision_of == original.id)
    (fresh_formal,) = harness.state.artifacts.values()
    assert fresh_formal.provenance.event_seq > package_event_seq
    assert revised.instance.seq > package_event_seq
    assert not fresh_formal.interface.refs

    (compiled,) = harness.capability_state.compiled.values()
    compiled_inputs = json.loads(harness.blobs.get(compiled.input_ref))
    assert compiled_inputs[0]["sealed_inputs"] == {"SIM_001": sealed_value}

    scratch_ids = set(scratch_service.state.blocks)
    encoded_inputs = canonical_json(compiled_inputs)
    assert all(scratch_id.encode("utf-8") not in encoded_inputs for scratch_id in scratch_ids)
    assert scratch_ids.isdisjoint(harness.state.artifacts)
    assert scratch_ids.isdisjoint(harness.commitments)
    assert scratch_ids.isdisjoint(harness.warrants)
    assert all(
        scratch_id not in edge
        for scratch_id in scratch_ids
        for edge in (*harness.state.att, *harness.state.dep)
    )
    assert len(prompts) == 3


def test_every_exactly_one_rule_is_carried_by_the_schema_universally():
    """Regression (thinking-off batteries, subject 97653fde...): a cross-field
    rule that lives only in a model_validator is invisible to a model reading
    the schema as its source of structural truth. One such rule
    (scratch.link's per-endpoint reference) cost glm-5.2 11/20 then 9/20
    first-pass valid with thinking off, and failed production qualification
    twice; encoding it in the schema restored 20/20 with zero repairs.

    The rule is universal, so this pins the ENCODER and every contract that
    uses it — a new exactly-one rule added in prose alone should fail here.
    """

    import pytest

    from deepreason.llm.wire import (
        AliasTable,
        AtomicConjectureWireContractV1,
        exclusive_fields_schema,
    )
    from deepreason.scratch.contracts import (
        ScratchLinkMinimalWireContract,
        ScratchLinkWireContract,
    )

    handles = {"SCR_001": "a", "SCR_002": "b"}
    expected = {
        "critic-free atomic conjecture": (
            AtomicConjectureWireContractV1(AliasTable({"SRC_001": "x"})),
            [{"oneOf": [{"required": ["candidate"]}, {"required": ["abstention"]}]}],
        ),
        "scratch link compact": (
            ScratchLinkWireContract(handles=handles),
            [
                {"oneOf": [{"required": ["from_index"]}, {"required": ["from_handle"]}]},
                {"oneOf": [{"required": ["to_index"]}, {"required": ["to_handle"]}]},
            ],
        ),
        "scratch link minimal": (
            ScratchLinkMinimalWireContract(handles=handles),
            [
                {"oneOf": [{"required": ["from_index"]}, {"required": ["from_handle"]}]},
                {"oneOf": [{"required": ["to_index"]}, {"required": ["to_handle"]}]},
            ],
        ),
    }
    for label, (contract, clauses) in expected.items():
        schema = contract.model_json_schema()
        assert schema["allOf"] == clauses, label
        # Branches must stay `required`-only: _strict_schema closes any
        # subschema carrying `properties`, which would turn a constraint
        # branch into an object that rejects its siblings.
        for clause in schema["allOf"]:
            for branch in clause["oneOf"]:
                assert set(branch) == {"required"}, (label, branch)
        # No null escape: `required` must mean present-and-usable.
        for clause in schema["allOf"]:
            for branch in clause["oneOf"]:
                (name,) = branch["required"]
                field = schema["properties"][name]
                assert "anyOf" not in field and "default" not in field, (label, name)

    # The encoder itself: groups are independent, so a mixed selection across
    # groups stays legal. Pairing them would forbid a form the validator
    # accepts.
    schema = {"properties": {n: {"anyOf": [{"type": "integer"}, {"type": "null"}], "default": None} for n in ("a", "b", "c", "d")}}
    exclusive_fields_schema(("a", "b"), ("c", "d"))(schema)
    assert schema["allOf"] == [
        {"oneOf": [{"required": ["a"]}, {"required": ["b"]}]},
        {"oneOf": [{"required": ["c"]}, {"required": ["d"]}]},
    ]
    assert schema["properties"]["a"] == {"type": "integer"}

    jsonschema = pytest.importorskip("jsonschema", reason="optional checker")
    atomic = AtomicConjectureWireContractV1(AliasTable({"SRC_001": "x"})).model_json_schema()
    candidate = {"content": "a candidate", "typicality": 0.5}

    def valid(document) -> bool:
        try:
            jsonschema.validate(document, atomic)
        except jsonschema.ValidationError:
            return False
        return True

    assert valid({"candidate": candidate})
    assert valid({"abstention": {"search_signal": "stuck"}})
    assert not valid({"candidate": candidate, "abstention": {"search_signal": "stuck"}})
    assert not valid({})
    assert not valid({"candidate": None, "abstention": {"search_signal": "stuck"}})


def test_the_turn_outcome_rules_are_carried_by_the_schema_and_agree_with_the_validator():
    """Regression (coin canonicity run-c5f901f38208e862f4ce2fe60a26e551):
    `conjecturer.turn.v6` was rejected 5 times and completed 0 times, so every
    surviving candidate came from the atomic fallback — which carries no
    capability channel at all. Its two outcome rules ("at least one meaningful
    outcome", "abstention cannot accompany semantic proposals") lived only in
    model_validators, so a model reading the schema could emit a structurally
    valid turn the harness then refused.

    The dangerous direction for an encoding like this is a FALSE REJECT, so
    this differential-tests the schema against the validator rather than
    merely asserting the schema's shape.
    """

    import itertools

    import pytest

    from deepreason.llm.wire import (
        AliasTable,
        ConjecturerTurnWireContractV6,
        ConjecturerTurnWireV6,
    )

    contract = ConjecturerTurnWireContractV6(
        reasoning=False,
        aliases=AliasTable({"SRC_001": "x"}),
        simulation_enabled=True,
        maximum_simulation_proposals=1,
    )
    schema = contract.model_json_schema()

    # Constraint branches must stay OPEN. _strict_schema closes objects; a
    # closed branch here would reject every sibling field of the turn.
    def closed_constraint_branches(node, constrains=False, hits=None):
        hits = [] if hits is None else hits
        if isinstance(node, dict):
            if constrains and node.get("additionalProperties") is False and "type" not in node:
                hits.append(node)
            for key, child in node.items():
                closed_constraint_branches(
                    child,
                    key in {"anyOf", "oneOf", "allOf", "not", "if", "then", "else"},
                    hits,
                )
        elif isinstance(node, list):
            for child in node:
                closed_constraint_branches(child, constrains, hits)
        return hits

    assert closed_constraint_branches(schema) == []
    # Constraints live under allOf so `_reject_unknown_fields`, which reads a
    # TOP-LEVEL anyOf/oneOf then properties, keeps its previous behaviour.
    assert "anyOf" not in schema and "oneOf" not in schema
    assert schema["allOf"]

    jsonschema = pytest.importorskip("jsonschema", reason="optional checker")

    candidate = {"content": "c", "typicality": 0.5}
    simulation = {
        "request_identifier": "r", "hypothesis": "h", "rival_predictions": ["a"],
        "discriminating_purpose": "p", "simulation_mode": "sandboxed_python_v1",
        "model_source": "def simulate(inputs, rng):\n    return {'v': 1}\n",
        "requested_observables": ["v"], "interpretation_conditions": ["c"],
    }
    options = {
        "candidates": ([], [candidate]),
        "context_request": (None, {"query": "q"}),
        "abstention": (None, {"search_signal": "stuck"}),
        "simulation_proposals": ([], [simulation]),
    }
    disagreements = []
    for combination in itertools.product(
        *[[(name, value) for value in values] for name, values in options.items()]
    ):
        full = dict(combination)
        for omit_empty in (False, True):
            document = {
                name: value
                for name, value in full.items()
                if not (omit_empty and (value == [] or value is None))
            }
            try:
                jsonschema.validate(document, schema)
                by_schema = True
            except jsonschema.ValidationError:
                by_schema = False
            try:
                ConjecturerTurnWireV6.model_validate(document)
                by_validator = True
            except Exception:
                by_validator = False
            if by_schema != by_validator:
                disagreements.append((document, by_schema, by_validator))

    assert disagreements == [], disagreements[:4]


def test_omitting_a_capability_property_also_removes_the_constraints_naming_it():
    """Regression (schema sweep, 2026-07-31): `ConjecturerTurnWireV6` carries
    its outcome rules in the schema, but the capability-gated properties are
    removed at render time. Omission that left the `allOf` alone advertised
    `simulation_proposals`, `scratch_proposal` and `research_proposals` as ways
    to satisfy the turn while `additionalProperties: false` forbade emitting
    them — a dead branch on every run with a channel switched off, which is
    the common case.

    The invariant is that a rendered schema after omission must be
    indistinguishable from one where the property was never declared, so the
    encoder and the omission cannot disagree.
    """

    import itertools

    from deepreason.llm.wire import (
        AliasTable,
        ConjecturerTurnWireContractV6,
        _names_mentioned,
    )

    for simulation, scratch, research in itertools.product((False, True), repeat=3):
        contract = ConjecturerTurnWireContractV6(
            reasoning=False,
            aliases=AliasTable({"SRC_001": "x"}),
            simulation_enabled=simulation,
            maximum_simulation_proposals=1 if simulation else 0,
            research_enabled=research,
            maximum_research_proposals=1 if research else 0,
        )
        schema = contract.model_json_schema()
        label = (simulation, scratch, research)
        declared = set(schema["properties"])
        constrained = _names_mentioned(schema.get("allOf", []))
        assert constrained <= declared, (label, sorted(constrained - declared))

        # An emptied branch must be DROPPED, never kept as `{}`: a vacuously
        # true branch satisfies the whole anyOf and silently deletes the rule.
        def branches(node):
            if isinstance(node, dict):
                for key, child in node.items():
                    if key in {"anyOf", "oneOf"} and isinstance(child, list):
                        assert child, (label, key)
                        assert all(branch for branch in child), (label, key)
                    yield from branches(child)
            elif isinstance(node, list):
                for child in node:
                    yield from branches(child)

        list(branches(schema))


def test_the_branch_builders_read_the_rendered_shape_not_the_annotation():
    """A nullable array renders as `{"anyOf": [{"type": "array"}, {"type":
    "null"}]}` with no top-level `type` and no `items`, which a naive array
    test misses — emitting `{"not": {"type": "null"}}`, a branch that admits
    `[]` and so drops the rule it was carrying. Every reference array on the
    claim ledger has exactly that shape.
    """

    import pytest

    from deepreason.llm.wire import absent_or_empty, present_and_nonempty

    properties = {
        "plain_array": {"type": "array", "items": {"type": "string"}},
        "nullable_array": {
            "anyOf": [{"type": "array", "items": {"type": "string"}}, {"type": "null"}],
            "default": None,
        },
        "alias": {"type": "string"},
        "nullable_object": {"anyOf": [{"type": "object"}, {"type": "null"}]},
        "required_text": {"type": "string", "minLength": 1},
    }

    assert present_and_nonempty("plain_array", properties) == {
        "required": ["plain_array"],
        "properties": {"plain_array": {"minItems": 1}},
    }
    assert present_and_nonempty("nullable_array", properties) == {
        "required": ["nullable_array"],
        "properties": {"nullable_array": {"minItems": 1, "type": "array"}},
    }
    assert present_and_nonempty("nullable_array", properties, minimum=2) == {
        "required": ["nullable_array"],
        "properties": {"nullable_array": {"minItems": 2, "type": "array"}},
    }
    assert present_and_nonempty("alias", properties) == {
        "required": ["alias"],
        "properties": {"alias": {"minLength": 1}},
    }
    assert present_and_nonempty("nullable_object", properties) == {
        "required": ["nullable_object"],
        "properties": {"nullable_object": {"not": {"type": "null"}}},
    }

    assert absent_or_empty("plain_array", properties) == {"maxItems": 0}
    assert absent_or_empty("nullable_array", properties) == {
        "anyOf": [{"type": "null"}, {"maxItems": 0}]
    }
    assert absent_or_empty("nullable_object", properties) == {"type": "null"}
    # A field with no empty representation must not be given an unsatisfiable
    # one; `maxLength: 0` against a rendered `minLength: 1` would forbid the
    # whole discriminator value rather than merely emptying the field.
    with pytest.raises(ValueError, match="require_absent"):
        absent_or_empty("required_text", properties)
