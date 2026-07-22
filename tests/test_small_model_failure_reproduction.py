"""The prior small-model failure stays a local invalid value, not control."""

import pytest

from deepreason.workflows.manifest_compiler import ManifestCompiler
from deepreason.workflows.website import WebsiteStage, WebsiteStateMachine


def test_operator_fields_cannot_enter_a_component_contract_or_build():
    outline = {"components": [{"alias": "C1", "purpose": "DNA hero"}]}
    confused_response = {
        "alias": "C1",
        "slots": ["root"],
        "exports": [],
        "owned_dom_ids": ["dna-hero"],
        "depends_on": [],
        "content_requirements": ["animated helix"],
        "motion_requirement": "static",
        "model": "deepseek-v4",
        "delegate": True,
        "bypass_guards": True,
        "command": "spawn another model",
    }
    result = ManifestCompiler().compile(outline, [confused_response])
    assert result.manifest is None
    assert {item.code for item in result.diagnostics} == {
        "INVALID_COMPONENT_CONTRACT",
        "MISSING_COMPONENT_CONTRACT",
    }
    assert all(item.repair_scope == "/component_contracts/C1" for item in result.diagnostics)


def test_model_text_cannot_choose_next_state_or_bypass_repair():
    machine = WebsiteStateMachine()
    model_value = {
        "next_state": "EXPORT",
        "bypass_guards": True,
        "delegate": "C2",
    }
    # The only state-machine input is the harness's typed fact.  Arbitrary
    # model text can be retained in a diagnostic, but it has no transition
    # authority and the machine remains at PLAN.
    result = machine.retryable_failure([
        {"code": "INVALID_COMPONENT_CONTRACT", "received": model_value}
    ])
    assert result.stage == WebsiteStage.PLAN
    assert machine.stage == WebsiteStage.PLAN
    assert not machine.complete


def test_invalid_skeleton_never_produces_a_canonical_manifest():
    outline = {
        "components": [
            {"alias": "C1", "purpose": "hero"},
            {"alias": "C2", "purpose": "detail"},
        ]
    }
    contracts = [
        {
            "alias": "C1", "slots": ["root"], "exports": [],
            "owned_dom_ids": ["hero"], "depends_on": ["C2"],
            "content_requirements": [], "motion_requirement": "static",
        },
        {
            "alias": "C2", "slots": ["root"], "exports": [],
            "owned_dom_ids": ["detail"], "depends_on": ["C1"],
            "content_requirements": [], "motion_requirement": "static",
        },
    ]
    result = ManifestCompiler().compile(outline, contracts)
    assert result.manifest is None
    assert {item.code for item in result.diagnostics} == {"DEPENDENCY_CYCLE"}


def test_compact_easy_execution_is_fail_closed_before_model_or_scheduler(
    tmp_path, monkeypatch,
):
    """The retired Easy facade cannot launch the compact website path."""
    from deepreason import easy

    calls = []
    monkeypatch.setattr(
        "deepreason.llm.adapter.build_adapter",
        lambda *_args, **_kwargs: calls.append("adapter"),
    )
    monkeypatch.setattr(
        "deepreason.ops.run_scheduler",
        lambda *_args, **_kwargs: calls.append("scheduler"),
    )
    root = tmp_path / "run"
    output = tmp_path / "site"

    with pytest.raises(easy.EasyV6PreparationRequired) as caught:
        easy.make(
            "the wonders of DNA",
            out=str(output),
            config=str(tmp_path / "must-not-be-read.yaml"),
            root=str(root),
        )

    assert caught.value.code == "V6_PREPARATION_REQUIRED"
    assert calls == []
    assert not root.exists()
    assert not output.exists()
