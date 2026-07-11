"""The prior small-model failure stays a local invalid value, not control."""

import json

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


def test_compact_workflow_builds_without_a_model_authored_nested_manifest(
    tmp_path, monkeypatch,
):
    """Gemma-like flat replies drive the actual skeleton-first make path."""
    import yaml

    from deepreason import easy, ops
    from deepreason.harness import Harness
    from deepreason.llm.adapter import LLMAdapter
    from deepreason.llm.endpoints import MockEndpoint
    from deepreason.manifest import parse_manifest
    from deepreason.ontology import Interface, Provenance, Ref, Rule

    monkeypatch.setenv("DEEPREASON_HOME", str(tmp_path / "dot"))
    monkeypatch.setenv("FAKE_MAKE_KEY", "k")
    config_path = tmp_path / "engine.yaml"
    config_path.write_text(yaml.safe_dump({
        "model_profile": "compact",
        "BROWSER_PER_CYCLE": 0,
        "roles": {"conjecturer": {
            "endpoint": "https://gemma.invalid/v1",
            "model": "gemma4:31b",
            "api_key_env": "FAKE_MAKE_KEY",
        }},
    }))

    prompts = []

    def gemma_like(prompt):
        prompts.append(prompt)
        if "WEBSITE DESIGN OUTLINE" in prompt:
            return json.dumps({"components": [
                {"alias": "C1", "purpose": "animated DNA hero"},
                {"alias": "C2", "purpose": "replication explanation"},
            ]})
        if "WEBSITE ART DIRECTION" in prompt:
            return json.dumps({
                "palette": "deep navy with cyan highlights",
                "typography": "geometric headings and readable body text",
                "spacing_strategy": "fluid grid spacing",
                "responsive_strategy": "single column on narrow screens",
                "interaction_state_model": "local controls plus global motion state",
                "motion_language": "slow orbital strand motion",
                "scroll_narrative": "hero gives way to replication",
                "depth_structure": "helix above quiet cellular layers",
                "transition_grammar": "opacity and transform",
                "texture_language": "luminous grain",
                "reduced_motion_version": "all content remains visible and still",
                "static_fallback": "complete readable still composition",
            })
        if "Target: C1" in prompt:
            return json.dumps({
                "alias": "C1", "slots": ["root"], "exports": ["mount"],
                "owned_dom_ids": ["dna-hero"], "depends_on": [],
                "content_requirements": ["title", "helix illustration"],
                "motion_requirement": "static",
            })
        if "Target: C2" in prompt:
            attempt = sum("Target: C2" in item for item in prompts)
            return json.dumps({
                "alias": "C2", "slots": ["root"], "exports": [],
                "owned_dom_ids": ["dna-copy"],
                # First reply reproduces a common small-model alias slip.
                # The runtime must re-ask C2 only, not regenerate C1.
                "depends_on": ["C9" if attempt == 1 else "C1"],
                "content_requirements": ["replication steps"],
                "motion_requirement": "static",
            })
        raise AssertionError("unexpected compact prompt")

    endpoint = MockEndpoint(
        gemma_like, name="https://gemma.invalid/v1", model="gemma4:31b"
    )

    def fake_build_adapter(config, blob_store, meter=None, only_roles=None,
                           run_manifest=None):
        return LLMAdapter(
            {"conjecturer": endpoint},
            blob_store,
            retry_max=config.RETRY_MAX,
            meter=meter,
            model_profile="compact",
        )

    monkeypatch.setattr("deepreason.llm.adapter.build_adapter", fake_build_adapter)
    scheduler_calls = []

    def fake_run(harness, config, cycles, token_budget=None, on_cycle=None,
                 run_manifest=None):
        pid = config.FOCUS_FAMILY
        problem = harness.state.problems[pid]
        refs = []
        for commitment_id in problem.criteria:
            commitment = harness.commitments.get(commitment_id)
            if commitment is not None and commitment.eval == "program:lineage_ref":
                refs = [
                    Ref(target=target, role="dependence")
                    for target in commitment.budget.extra["endpoints"].split(",")
                ]
        if pid == "pi-plan":
            content = "PLAN: pages, content, interactions, acceptance criteria. " * 15
        elif pid.startswith("pi-comp-"):
            contract_commitment = next(
                harness.commitments[item]
                for item in problem.criteria
                if harness.commitments[item].eval == "program:component_wf"
            )
            spec = json.loads(contract_commitment.budget.extra["spec"])["component"]
            exports = "\n".join(
                f"window.{name} = function () {{}};"
                for name in spec["js_exports"]
            )
            script = f"<script>{exports}</script>" if exports else ""
            root = spec["element_id"]
            content = (
                f'<section id="{root}"><h2>{spec["purpose"]}</h2>'
                f"<style>#{root} {{ display: block; }}</style>{script}</section>"
            )
        else:
            raise AssertionError(f"compact mode must not schedule {pid}")
        harness.create_artifact(
            content,
            interface=Interface(commitments=list(problem.criteria), refs=refs),
            provenance=Provenance(role="conjecturer"),
            problem_id=pid,
        )
        scheduler_calls.append(pid)
        if on_cycle is not None:
            from types import SimpleNamespace

            on_cycle(SimpleNamespace(harness=harness))
        return ({"survivors": 1}, None, {
            "logged_tokens_this_run": 100,
            "metered_tokens": 100,
        })

    monkeypatch.setattr(ops, "run_scheduler", fake_run)
    paths = easy.make(
        "the wonders of DNA",
        out=str(tmp_path / "site"),
        config=str(config_path),
        root=str(tmp_path / "run"),
        echo=lambda _message: None,
    )

    assert scheduler_calls == ["pi-plan", "pi-comp-c1", "pi-comp-c2"]
    assert len(prompts) == 5  # outline + art + C1 + C2 + localized C2 repair
    assert sum("Target: C1" in prompt for prompt in prompts) == 1
    assert sum("Target: C2" in prompt for prompt in prompts) == 2
    assert not any("```manifest" in prompt for prompt in prompts)
    assert any(path.suffix == ".html" for path in paths)

    harness = Harness(tmp_path / "run")
    design_pick = next(
        event.inputs[2]
        for event in harness.log.read()
        if event.rule == Rule.MEASURE and event.inputs[:2] == ["stage-pick", "design"]
    )
    manifest, error = parse_manifest(
        harness.blobs.get(harness.state.artifacts[design_pick].content_ref).decode()
        if not harness.state.artifacts[design_pick].content_ref.startswith("inline:")
        else harness.state.artifacts[design_pick].content_ref.removeprefix("inline:")
    )
    assert error == "" and manifest is not None
    assert [component.name for component in manifest.ordered()] == ["c1", "c2"]
    assert any(
        harness.commitments[item].eval == "program:manifest_wf"
        for item in harness.state.artifacts[design_pick].interface.commitments
    )
    llm_models = [event.llm.model for event in harness.log.read() if event.llm]
    assert llm_models and set(llm_models) == {"gemma4:31b"}
