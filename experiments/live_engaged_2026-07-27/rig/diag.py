"""Capture the full production doctor report and one failing case's real error.

Runs inside the live venv with DEEPREASON_HOME/OLLAMA_API_KEY set. Output is
diagnostic-only and stays in the scratchpad; it never enters the repository.
"""

import json
import sys
import traceback

from deepreason.cli.doctor import (
    PRODUCTION_CASES_PER_PAIR,
    _contract_schema_repair_grant,
    _production_probe_contract,
    _admit_production_probe_output,
    _validate_production_contract_request_envelopes,
    exercise_production_contract_case,
    production_contract_pairs,
)
from deepreason.preparation import qualification_subject_manifest
from deepreason.provider_profile import resolve_provider_profile


def deep_case(manifest, pair, case_index):
    """Reproduce one case, returning the true failure chain per attempt."""

    from deepreason.llm.adapter import _endpoint_from_spec, _enforce_request_envelope
    from deepreason.llm.firewall import EndpointLease
    from deepreason.llm.repair import OutputMechanism, V6PatchRepairSession

    grant = _contract_schema_repair_grant(manifest, pair)
    contract, request = _production_probe_contract(manifest, pair, case_index)
    route = manifest.roles[pair.role][pair.seat]
    endpoint = _endpoint_from_spec(route.endpoint_spec())
    schema = contract.model_json_schema()
    session = V6PatchRepairSession(
        contract=pair.contract_id,
        schema=schema,
        initial_request=request,
        retry_max=grant.maximum_schema_repairs,
        # Mirror the production battery exactly: without explicit root
        # authority a cross-field violation is unrepairable at zero
        # attempts here while the real battery grants field patches,
        # and the diagnosis diverges from production behavior.
        root_authorized_pointers=tuple(
            sorted("/" + name for name in (schema.get("properties") or {}))
        ),
    )
    lease = EndpointLease(role=pair.role, seat=pair.seat, route=route)
    attempts = []
    for attempt in range(session.attempt_count):
        turn = session.turn(attempt)
        record = {"attempt": attempt}
        try:
            _enforce_request_envelope(pair.role, turn.request, lease)
            kwargs = {}
            mechanism = OutputMechanism(route.output_mechanism)
            if mechanism is not OutputMechanism.JSON_TEXT:
                kwargs = {
                    "response_schema": turn.response_schema,
                    "output_mechanism": mechanism,
                }
            raw = endpoint.complete(turn.request, **kwargs)
            record["raw_head"] = str(raw)[:600]
            candidate = session.candidate_from_raw(turn, raw)
            wire = contract.validate_value(candidate)
            compiled = contract.compile(wire)
            _admit_production_probe_output(pair, compiled)
            record["outcome"] = "valid"
            attempts.append(record)
            return attempts
        except Exception as error:  # noqa: BLE001 - diagnostic capture
            record["error_type"] = type(error).__name__
            record["error"] = str(error)[:1500]
            record["trace_tail"] = traceback.format_exc().splitlines()[-4:]
            attempts.append(record)
            try:
                session.note_invalid(turn, locals().get("raw"), error)
            except Exception as diag_error:  # noqa: BLE001
                record["note_invalid_error"] = f"{type(diag_error).__name__}: {diag_error}"[:400]
                break
    return attempts


def main() -> int:
    resolved = resolve_provider_profile(None)
    manifest = qualification_subject_manifest(resolved.profile)
    pairs = production_contract_pairs(manifest)
    print(json.dumps({"pair_count": len(pairs), "cases_per_pair": PRODUCTION_CASES_PER_PAIR,
                      "pairs": [{"pair_id": p.pair_id, "role": p.role, "seat": p.seat,
                                 "contract_id": p.contract_id} for p in pairs]}, indent=2))
    failing = None
    for pair in pairs:
        summary = {"pair_id": pair.pair_id, "contract_id": pair.contract_id, "cases": []}
        unqualified = False
        for index in range(PRODUCTION_CASES_PER_PAIR):
            _validate_production_contract_request_envelopes(manifest, pair, index)
            case = exercise_production_contract_case(manifest, pair, index)
            summary["cases"].append(json.loads(case.model_dump_json()))
            if not (case.eventual_valid and case.semantic_admission):
                unqualified = True
                if failing is None:
                    failing = (pair, index)
                break  # stop this pair at its first failing case
        print(json.dumps({"pair_summary": summary}, indent=2))
        sys.stdout.flush()
        if unqualified and failing is not None:
            break  # first failing pair is enough for diagnosis
    if failing is None:
        print(json.dumps({"diagnosis": "all pairs qualified in diagnostic pass"}))
        return 0
    pair, index = failing
    print(json.dumps({
        "deep_case": {"pair_id": pair.pair_id, "contract_id": pair.contract_id,
                      "case_index": index, "attempts": deep_case(manifest, pair, index)}
    }, indent=2))
    return 1


if __name__ == "__main__":
    sys.exit(main())
