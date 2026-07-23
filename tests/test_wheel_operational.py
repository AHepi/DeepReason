from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import threading

import pytest

from deepreason.cli.doctor import (
    _admit_production_probe_output,
    _production_probe_contract,
    production_contract_pairs,
)
from deepreason.llm.endpoints import OpenAICompatEndpoint
from deepreason.llm.wire import ReasoningConjecturerTurnWireV6
from deepreason.preparation import qualification_subject_manifest
from deepreason.provider_profile import ProviderProfileV1


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "scripts" / "wheel_loopback_sitecustomize.py"
SPEC = importlib.util.spec_from_file_location(
    "wheel_loopback_sitecustomize", FIXTURE_PATH
)
assert SPEC is not None and SPEC.loader is not None
FIXTURE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FIXTURE)
OPERATIONAL_SPEC = importlib.util.spec_from_file_location(
    "wheel_operational_smoke", ROOT / "scripts" / "wheel_operational_smoke.py"
)
assert OPERATIONAL_SPEC is not None and OPERATIONAL_SPEC.loader is not None
OPERATIONAL = importlib.util.module_from_spec(OPERATIONAL_SPEC)
OPERATIONAL_SPEC.loader.exec_module(OPERATIONAL)


def _profile(endpoint: str = "http://127.0.0.1:1/v1"):
    return ProviderProfileV1.create(
        provider="generic",
        endpoint=endpoint,
        model_id="deepreason-loopback-v6",
        model_revision="fixture-1",
        family="deterministic-loopback",
        context_window_tokens=1_000_000,
        maximum_completion_tokens=4_096,
        credential_env=FIXTURE.CREDENTIAL_ENV,
        output_mechanism="native_json_schema",
    )


def test_external_provider_satisfies_every_production_qualification_contract():
    manifest = qualification_subject_manifest(_profile())
    pairs = production_contract_pairs(manifest)
    assert len(pairs) == 4
    for pair in pairs:
        for case_index in range(20):
            contract, prompt = _production_probe_contract(
                manifest, pair, case_index
            )
            candidate = FIXTURE.response_for_schema(
                contract.model_json_schema(), prompt
            )
            wire = contract.validate_value(candidate)
            compiled = contract.compile(wire)
            _admit_production_probe_output(pair, compiled)


def test_external_provider_implements_real_openai_compatible_transport(tmp_path):
    state_path = tmp_path / "provider-counts.json"
    server = FIXTURE._ReusableLoopbackServer(
        ("127.0.0.1", 0), FIXTURE._handler(state_path)
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        endpoint = OpenAICompatEndpoint(
            f"http://127.0.0.1:{server.server_port}/v1",
            "deepreason-loopback-v6",
            api_key=FIXTURE.CREDENTIAL,
            max_tokens=1_024,
            output_mechanism="json_text",
        )
        schema = {
            "title": "SimpleInstalledProbe",
            "type": "object",
            "properties": {"message": {"type": "string", "minLength": 1}},
            "required": ["message"],
            "additionalProperties": False,
        }
        prompt = (
            "ordinary production adapter request\n\n"
            "Respond with ONLY a JSON object conforming to this JSON Schema:\n"
            + json.dumps(schema)
        )
        raw = endpoint.complete(prompt)
        assert json.loads(raw) == {"message": "deterministic fixture value"}
        state = json.loads(state_path.read_text(encoding="utf-8"))
        assert state == {
            "errors": [],
            "qualification_calls": 0,
            "schema_titles": {"SimpleInstalledProbe": 1},
            "total_calls": 1,
        }
        assert endpoint.last_usage["prompt_tokens"] > 0
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_external_provider_honours_runtime_reasoning_candidate_count():
    schema = ReasoningConjecturerTurnWireV6.model_json_schema()
    value = FIXTURE.response_for_schema(
        schema,
        "DIRECTIVE: return exactly 6 diverse candidates with typicality estimates.",
    )
    parsed = ReasoningConjecturerTurnWireV6.model_validate(value)
    assert len(parsed.candidates) == 6
    assert len({candidate.claim for candidate in parsed.candidates}) == 6


def test_external_provider_can_drive_a_genuine_resumable_stop():
    schema = ReasoningConjecturerTurnWireV6.model_json_schema()
    value = FIXTURE.response_for_schema(
        schema,
        OPERATIONAL.RESUMABLE_STOP_QUESTION,
    )
    parsed = ReasoningConjecturerTurnWireV6.model_validate(value)
    assert parsed.candidates == []
    assert parsed.abstention is not None
    assert parsed.abstention.search_signal == "stuck"


def test_operational_smoke_requires_exact_non_resumable_rejection():
    OPERATIONAL._assert_non_resumable_rejection(
        "ValueError: CONTINUE_TYPED_STOP_REQUIRED"
    )
    with pytest.raises(AssertionError, match="non-resumable"):
        OPERATIONAL._assert_non_resumable_rejection(
            "ValueError: CONTINUE_NOT_AUTHORIZED"
        )


def test_operational_poll_waits_for_a_new_terminal_commitment():
    class FakeClient:
        def __init__(self):
            self.result_calls = 0

        def tool(self, name, _arguments):
            if name == "run_status":
                return {"state": "completed"}
            self.result_calls += 1
            return {
                "state": "completed",
                "terminal_commitment_ref": (
                    "sha256:old" if self.result_calls == 1 else "sha256:new"
                ),
            }

    client = FakeClient()
    _status, result = OPERATIONAL._poll_terminal(
        client,
        "run-id",
        prior_terminal_commitment_ref="sha256:old",
    )
    assert result["terminal_commitment_ref"] == "sha256:new"
    assert client.result_calls == 2


def test_package_layout_excludes_mini_and_external_smoke_fixture():
    project = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'packages = ["src/deepreason"]' in project
    assert "mini/minireason" not in project
    assert not (ROOT / "src" / "deepreason" / "deterministic_provider.py").exists()
