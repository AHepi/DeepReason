"""The stop report: the harness writes the first failure report itself.

Implements R1-R12 and R18-R20 of
`experiments/2026-09-03-change-stop-report/REQUEST.md`.

Motivating incident, in the operator's own words (2026-09-03): "One
window reported a crash happened because a conjecturer seat kept failing
to fill a form. When I said that particular model passed qualification
with ease, it double checked and realised it's config was off." The
harness already held the contradicting evidence on disk -- P-A1's
qualification record shows `conjecturer#0 conjecturer.turn.v6` passing
20/20 first-pass with 0 repairs -- and no instrument read it out. These
fixtures pin the classifier so that reading cannot drift back.

Each fixture asserts the CLAIM (this typed evidence => this box ranks
first), never an incidental string, so it fails only when the
classification stops being true.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from deepreason.application.stop_report import render_stop_report, stop_report

# --------------------------------------------------------------------------
# Minimal typed roots. Built from the record shapes measured on the committed
# roots (SPEC.md M1-M8), not invented: an event carries `llm.attempt_trace[]`,
# transport diagnostics are `Kind:detail` strings, and a qualification pair
# carries first_pass/eventual/repair counts against `representative_cases`.
# --------------------------------------------------------------------------

CONTRACT = "conjecturer.turn.v6"


def _seat(*, reasoning=None, max_tokens=4096, endpoint_id="ep-glm"):
    return {
        "api_key_env": "OLLAMA_API_KEY",
        "base_url": "https://example.invalid/v1",
        "context_window_tokens": 131072,
        "endpoint_id": endpoint_id,
        "family": "glm",
        "logprobs": False,
        "max_tokens": max_tokens,
        "model_id": "glm-5.3",
        "model_revision": "glm-5.3",
        "output_mechanism": "json_text",
        "output_mode": "json_object",
        "provider": "ollama",
        "reasoning": reasoning,
        "temperature": None,
        "timeout_s": 1800,
    }


def _attempt(*, valid=True, diagnostics=(), tokens=10, natural_stop=True,
             validation_path="", seat=0, endpoint_id="ep-glm"):
    return {
        "attempt": 0,
        "contract_id": CONTRACT,
        "diagnostic_ref": "d" * 64,
        "endpoint_id": endpoint_id,
        "max_tokens": 4096,
        "model_profile": "standard",
        "natural_stop": natural_stop,
        "prompt_ref": "p" * 64,
        "raw_ref": "r" * 64,
        "repair_scope": "",
        "route_sha256": "s" * 64,
        "seat": seat,
        "split_legs": [],
        "split_notice": "",
        "timeout_s": 1800,
        "tokens": tokens,
        "transport_attempts": 1,
        "transport_diagnostics": list(diagnostics),
        "transport_profile": "standard",
        "usage_unknown": False,
        "valid": valid,
        "validation_path": validation_path,
    }


def _event(seq, *, attempts=(), role="conjecturer"):
    llm = None
    if attempts:
        llm = {
            "role": role,
            "model": "glm-5.3",
            "endpoint": "https://example.invalid/v1",
            "prompt_ref": "p" * 64,
            "raw_ref": "r" * 64,
            "tokens": 10,
            "ms": 5,
            "attempts": len(attempts),
            "truncated": False,
            "mean_surprisal": None,
            "attempt_trace": list(attempts),
            "work_order_id": "w-1",
            "dispatch_authorization_ref": "a" * 64,
            "prompt_tokens": 5,
            "completion_tokens": 5,
        }
    return {
        "seq": seq,
        "ts": "2026-09-03T00:00:0%d+00:00" % (seq % 10),
        "rule": "Conj" if attempts else "Register",
        "inputs": [],
        "outputs": [],
        "llm": llm,
        "state_diff": {},
    }


def _qualification(*, first_pass=20, eventual=20, repairs=0, qualified=True,
                   failure_code=None, cases=20):
    case_rows = []
    for index in range(cases):
        ok = index < first_pass
        row = {
            "alias_failures": 0,
            "case_id": "case-%03d" % (index + 1),
            "eventual_valid": index < eventual,
            "first_pass_valid": ok,
            "repair_count": 0,
            "scope_violations": 0,
            "semantic_admission": index < eventual,
        }
        if not ok and failure_code:
            row["failure_code"] = failure_code
        case_rows.append(row)
    return {
        "schema": "deepreason-production-contract-doctor-v1",
        "eventual_valid_minimum_per_pair": 19,
        "pair_re_exercise_limit": 3,
        "production_contracts": True,
        "representative_cases_per_pair": cases,
        "run_manifest_schema_version": 6,
        "run_manifest_sha256": "m" * 64,
        "summary": {
            "case_count": cases,
            "eventual_valid_count": eventual,
            "first_pass_valid_count": first_pass,
            "pair_count": 1,
            "qualified": qualified,
            "qualified_pair_count": 1 if qualified else 0,
            "repair_count": repairs,
        },
        "pairs": [
            {
                "pair": {
                    "contract_id": CONTRACT,
                    "endpoint_id": "ep-glm",
                    "family": "glm",
                    "model_id": "glm-5.3",
                    "model_revision": "glm-5.3",
                    "output_mechanism": "json_text",
                    "pair_id": "sha256:" + "q" * 64,
                    "provider": "ollama",
                    "role": "conjecturer",
                    "route_sha256": "s" * 64,
                    "seat": 0,
                },
                "cases": case_rows,
                "eventual_valid_count": eventual,
                "first_pass_valid_count": first_pass,
                "repair_count": repairs,
                "qualified": qualified,
                "alias_failures": 0,
                "scope_violations": 0,
                "semantic_admission_count": eventual,
            }
        ],
    }


def _write_root(base: Path, *, message, events, qualification=None,
                notices=None, reasoning=None, stop_reason="operational_failure",
                state="failed", refusal="TERMINAL_LIFECYCLE_NOT_TAKEN_FAILURE_TERMINAL",
                embedder="nomic-ai/nomic-embed-text-v1.5") -> Path:
    root = base / "run"
    root.mkdir(parents=True, exist_ok=True)
    (root / "run-status.json").write_text(json.dumps({
        "state": state,
        "stop_reason": stop_reason,
        "message": message,
        "run_id": "f" * 64,
        "cycle": 3,
        "seq": len(events),
        "terminal_lifecycle_refusal": refusal,
        "token_limit": 1000,
        "token_spend": 100,
        "workload": "text",
    }))
    (root / "run-manifest.json").write_text(json.dumps({
        "schema_version": 6,
        "compiled_at": "2026-09-03T00:00:00",
        "compile_notices": list(notices or []),
        "engine_config_json": json.dumps({"EMBEDDER_MODEL": embedder}),
        "engine_profile": "full",
        "model_profile": "standard",
        "roles": {"conjecturer": [_seat(reasoning=reasoning)]},
        "concurrency": 1,
        "provider_fallback": False,
        "source_config_hash": "c" * 64,
        "run_input_digest": "i" * 64,
    }))
    with (root / "log.jsonl").open("w") as handle:
        for event in events:
            handle.write(json.dumps(event) + "\n")
    if qualification is not None:
        (root / "production-contract-qualification.json").write_text(
            json.dumps(qualification))
    return root


def _not_carried(pointer, value):
    return {
        "code": "ENGINE_CONFIG_FIELD_NOT_CARRIED",
        "message": "%s=%s is not carried by this manifest's engine config and "
                   "is restored at run time from this notice" % (pointer, value),
        "pointer": "/engine_config/%s" % pointer,
        "resolution": None,
        "value": value,
    }


def _ranked(report):
    return report["sections"]["classification"]["ranked"]


def _box(report, name):
    return report["sections"]["classification"]["boxes"][name]


# --------------------------------------------------------------------------
# One fixture per box (R20). Each pins the claim, not a string.
# --------------------------------------------------------------------------

def test_configuration_box_ranks_first_when_a_restored_gate_meets_a_qualified_seat(tmp_path):
    """R7: the run did not carry what was set, and the seat is vindicated.

    The seat passed its form 20/20, so the stop is not the model's; the
    manifest restored five gates from notices rather than carrying them.
    """
    root = _write_root(
        tmp_path,
        message="JUDGE_SEATS_ENABLED was restored at run time and the judge seat never dispatched",
        events=[_event(0), _event(1, attempts=[_attempt(valid=True)])],
        qualification=_qualification(first_pass=20, eventual=20, qualified=True),
        notices=[_not_carried("JUDGE_SEATS_ENABLED", "true"),
                 _not_carried("SCHOOL_SEATS_ENABLED", "true")],
    )
    report = stop_report(root)
    assert _ranked(report)[0] == "CONFIGURATION"
    assert _box(report, "CONFIGURATION")["verdict"] == "SUPPORTED"


def test_environment_box_ranks_first_on_a_429_streak(tmp_path):
    """R8: an account usage cap is the environment, not the model."""
    faults = ["HTTPError:HTTP-429:HTTP Error 429: Too Many Requests"] * 12
    root = _write_root(
        tmp_path,
        message="atomic child is terminally failed",
        events=[_event(0), _event(1, attempts=[_attempt(valid=False, diagnostics=faults)])],
        qualification=_qualification(first_pass=20, eventual=20, qualified=True),
    )
    report = stop_report(root)
    assert _ranked(report)[0] == "ENVIRONMENT"
    assert _box(report, "ENVIRONMENT")["verdict"] == "SUPPORTED"
    # R8: the provider's own message is quoted, not paraphrased.
    assert any("Too Many Requests" in str(item)
               for item in _box(report, "ENVIRONMENT")["supporting"])


def test_model_box_ranks_first_when_the_seat_failed_its_form_in_qualification(tmp_path):
    """R9: the attempt ladder set beside THAT seat's row for THAT form."""
    root = _write_root(
        tmp_path,
        message="route seat has terminally exhausted its smallest authorized contract",
        events=[_event(0), _event(1, attempts=[
            _attempt(valid=False, validation_path="/candidates/0/kind")])],
        qualification=_qualification(first_pass=5, eventual=5, repairs=0,
                                     qualified=False),
    )
    report = stop_report(root)
    assert _ranked(report)[0] == "MODEL"
    assert _box(report, "MODEL")["verdict"] == "SUPPORTED"


def test_harness_box_ranks_first_only_when_the_other_three_are_ruled_out(tmp_path):
    """R10: claimable only when the three boxes above are ruled out.

    Regression (P-A2 epoch 3, run 1b89ed64e050c354): the last provider
    call was valid, no transport fault was recorded, qualification passed
    23/23, and the stop message names an internal ordering invariant.
    """
    root = _write_root(
        tmp_path,
        message="v6 conjecture context must be planned after durable work preparation",
        events=[_event(0), _event(1, attempts=[_attempt(valid=True)])],
        qualification=_qualification(first_pass=20, eventual=20, qualified=True),
        notices=[],
    )
    report = stop_report(root)
    assert _ranked(report)[0] == "HARNESS"
    assert _box(report, "HARNESS")["verdict"] == "SUPPORTED"
    for other in ("CONFIGURATION", "ENVIRONMENT", "MODEL"):
        assert _box(report, other)["verdict"] == "RULED OUT"
        assert _box(report, other)["ruling_out"], (
            "a RULED OUT box must cite the evidence that ruled it out")


def test_harness_box_is_not_claimable_while_another_box_holds_evidence(tmp_path):
    """R10, the negative half: transport faults forbid a harness verdict."""
    faults = ["HTTPError:HTTP-429:HTTP Error 429: Too Many Requests"] * 12
    root = _write_root(
        tmp_path,
        message="v6 conjecture context must be planned after durable work preparation",
        events=[_event(0), _event(1, attempts=[_attempt(valid=True, diagnostics=faults)])],
        qualification=_qualification(first_pass=20, eventual=20, qualified=True),
    )
    report = stop_report(root)
    assert _box(report, "HARNESS")["verdict"] != "SUPPORTED"


# --------------------------------------------------------------------------
# The operator's own case (R9's second sentence).
# --------------------------------------------------------------------------

def test_model_box_says_so_when_the_seat_passed_qualification_at_full_marks(tmp_path):
    """R9: 'If the seat passed qualification 20/20 on that form, the report
    must SAY SO in the model box and point at configuration or environment
    instead.'

    Regression (P-A1 run 4565139800f5ca02): conjecturer#0 on
    conjecturer.turn.v6 passed 20/20 first-pass with 0 repairs while a
    window reported the seat could not fill the form.
    """
    faults = ["RemoteDisconnected:Remote end closed connection without response"] * 20
    root = _write_root(
        tmp_path,
        message="route seat has terminally exhausted its smallest authorized contract",
        events=[_event(0), _event(1, attempts=[_attempt(valid=False, diagnostics=faults)])],
        qualification=_qualification(first_pass=20, eventual=20, qualified=True),
    )
    report = stop_report(root)
    model = _box(report, "MODEL")
    assert "passed qualification 20/20" in json.dumps(model), (
        "the model box must state the qualification result explicitly")
    ranked = _ranked(report)
    assert ranked.index("MODEL") > ranked.index("ENVIRONMENT"), (
        "a vindicated seat ranks below environment")
    assert ranked.index("MODEL") > ranked.index("CONFIGURATION"), (
        "a vindicated seat ranks below configuration")


# --------------------------------------------------------------------------
# Properties of the report itself (R1, R2, R11).
# --------------------------------------------------------------------------

def _digest_tree(root: Path) -> tuple[list[str], str]:
    paths = sorted(str(p.relative_to(root)) for p in root.rglob("*") if p.is_file())
    digest = hashlib.sha256()
    for rel in paths:
        digest.update(rel.encode())
        digest.update((root / rel).read_bytes())
    return paths, digest.hexdigest()


def test_report_writes_nothing_into_the_root(tmp_path):
    """R1: read-only, never writing into the root."""
    root = _write_root(
        tmp_path, message="atomic child is terminally failed",
        events=[_event(0), _event(1, attempts=[_attempt()])],
        qualification=_qualification())
    before = _digest_tree(root)
    stop_report(root)
    render_stop_report(stop_report(root))
    assert _digest_tree(root) == before


def test_report_is_deterministic_byte_for_byte(tmp_path):
    """R1: deterministic. Same root and flags => identical output."""
    root = _write_root(
        tmp_path, message="atomic child is terminally failed",
        events=[_event(0), _event(1, attempts=[_attempt()])],
        qualification=_qualification())
    first = render_stop_report(stop_report(root))
    second = render_stop_report(stop_report(root))
    assert first == second
    assert json.dumps(stop_report(root), sort_keys=True) == \
        json.dumps(stop_report(root), sort_keys=True)


def test_report_never_asserts_a_defect(tmp_path):
    """R11: 'The report never asserts a defect; it ranks the boxes by
    evidence and says which are ruled out and why.'"""
    root = _write_root(
        tmp_path,
        message="v6 conjecture context must be planned after durable work preparation",
        events=[_event(0), _event(1, attempts=[_attempt(valid=True)])],
        qualification=_qualification())
    rendered = render_stop_report(stop_report(root)).lower()
    for claim in ("is a bug", "is a defect", "caused by a defect",
                  "this is broken", "the harness is at fault"):
        assert claim not in rendered


def test_markdown_and_json_carry_the_same_sections(tmp_path):
    """R1: emits Markdown and JSON -- neither a partial view of the other."""
    root = _write_root(
        tmp_path, message="atomic child is terminally failed",
        events=[_event(0), _event(1, attempts=[_attempt()])],
        qualification=_qualification())
    report = stop_report(root)
    rendered = render_stop_report(report)
    assert set(report["sections"]) == {
        "what_actually_ran", "pre_run_check", "provider_health",
        "classification", "continuability", "evidence_states",
    }
    for title in ("WHAT ACTUALLY RAN", "PRE-RUN CHECK", "PROVIDER HEALTH",
                  "THE STOP", "CONTINUABILITY", "EVIDENCE STATES"):
        assert title in rendered


def test_reasoning_null_renders_as_provider_default_never_as_off(tmp_path):
    """R3: 'reasoning knob value as sent (or "omitted -> provider default")'.

    An omitted knob is the provider's DEFAULT, not "off" -- the trap R17
    requires stated flatly, pinned here so the renderer cannot drift into
    the wrong word.
    """
    root = _write_root(
        tmp_path, message="atomic child is terminally failed",
        events=[_event(0), _event(1, attempts=[_attempt()])],
        qualification=_qualification(), reasoning=None)
    rendered = render_stop_report(stop_report(root))
    assert "omitted → provider default" in rendered
    seats = stop_report(root)["sections"]["what_actually_ran"]["seats"]
    assert seats[0]["reasoning"] == "omitted → provider default"


def test_embedder_null_says_hashing_and_does_not_guess(tmp_path):
    """R3: 'embedder as compiled (EMBEDDER_MODEL null -> say "hashing",
    do not guess)'."""
    root = _write_root(
        tmp_path, message="atomic child is terminally failed",
        events=[_event(0), _event(1, attempts=[_attempt()])],
        qualification=_qualification(), embedder=None)
    assert stop_report(root)["sections"]["what_actually_ran"]["embedder"] == "hashing"


# --------------------------------------------------------------------------
# Rootless mode (R27) and absence tolerance.
# --------------------------------------------------------------------------

def test_a_home_with_no_run_root_reports_from_qualification_alone(tmp_path):
    """R27: the failure class the operator described -- a config error that
    fails qualification and never mints a run root.

    Regression (P-A2 epoch 1; Phase-1 M3-C0, PARKED.md P3: "producing no
    run root at all").
    """
    home = tmp_path / "home"
    (home / "qualification-cache").mkdir(parents=True)
    digest = "4b0c48889a00b48c37ea90f1470cb29e8c3426182972882ff7f83867df822f08"
    payload = _qualification(first_pass=5, eventual=5, qualified=False,
                             failure_code="ENDPOINT_HTTP_429")
    payload["schema"] = "deepreason-reusable-qualification.v1"
    payload["subject_digest"] = digest
    (home / "qualification-cache" / (digest + ".json")).write_text(json.dumps(payload))
    (home / "runs").mkdir()

    report = stop_report(home)
    assert report["source"]["kind"] == "home-no-root"
    assert report["sections"]["pre_run_check"]["rows"], (
        "qualification rows must survive the absence of a run root")
    assert _ranked(report)[0] == "ENVIRONMENT"
    rendered = render_stop_report(report)
    assert digest in rendered, "the subject digest the cache was read from (R4)"
    assert "no run root" in rendered.lower()


def test_evidence_states_are_a_typed_absence_where_nothing_could_have_survived(tmp_path):
    """R6 of the 2026-09-04 evidence-states tranche: the section is present on
    every kind, as a typed absence where the record cannot carry it.

    A home with no run root and a root whose run died before its first call
    both admitted nothing, so "0 survivors" would be a claim about criticism
    that never happened. The section says which of the two it is instead.
    """

    home = tmp_path / "home"
    (home / "qualification-cache").mkdir(parents=True)
    (home / "runs").mkdir()
    digest = "5" * 64
    payload = _qualification()
    payload["schema"] = "deepreason-reusable-qualification.v1"
    payload["subject_digest"] = digest
    (home / "qualification-cache" / (digest + ".json")).write_text(json.dumps(payload))
    report = stop_report(home)
    assert report["source"]["kind"] == "home-no-root"
    reading = report["sections"]["evidence_states"]
    assert reading["absent"] is True
    assert "never started" in reading["reason"]
    assert "EVIDENCE STATES" in render_stop_report(report)

    root = tmp_path / "compiled-but-never-ran"
    root.mkdir()
    (root / "run-manifest.json").write_text("{}")
    report = stop_report(root)
    assert report["source"]["kind"] == "root-no-log"
    reading = report["sections"]["evidence_states"]
    assert reading["absent"] is True
    assert "no log.jsonl" in reading["reason"]
    assert "EVIDENCE STATES" in render_stop_report(report)


def test_absent_records_are_typed_absences_not_crashes(tmp_path):
    """Durability rule 5: every existing committed root predates this
    feature, so absence is valid and never a failure."""
    root = tmp_path / "bare"
    root.mkdir()
    (root / "log.jsonl").write_text("")
    report = stop_report(root)
    assert report["sections"]["pre_run_check"]["absent"], (
        "a root with no qualification record reports a typed absence")
    render_stop_report(report)


def test_stop_report_refuses_a_path_that_is_neither_root_nor_home(tmp_path):
    """A refusal is typed, not a traceback."""
    with pytest.raises(Exception) as caught:
        stop_report(tmp_path / "nowhere")
    assert "nowhere" in str(caught.value)


def test_a_run_config_yaml_is_read_only_when_one_is_passed():
    """R2: 'NEVER from a run-config YAML unless one is passed explicitly
    for a DIFF section.'

    Structural, not textual: the yaml import must live inside the single
    function that builds the diff, so no other code path can reach it.
    A report derived from the settings file cannot contradict the
    settings file, which is the whole failure this instrument removes.
    """
    import ast
    import inspect

    from deepreason.application import stop_report as module

    tree = ast.parse(inspect.getsource(module))
    holders = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        names = [alias.name for alias in node.names]
        if not any(name.split(".")[0] == "yaml" for name in names):
            continue
        enclosing = [f.name for f in ast.walk(tree)
                     if isinstance(f, ast.FunctionDef)
                     and any(child is node for child in ast.walk(f))]
        holders.update(enclosing)
    assert holders == {"_config_diff"}, (
        "yaml may be read only by the run-config diff, not by any other "
        f"path; found it reachable from {sorted(holders)}")


def test_a_clean_terminal_attributes_no_box(tmp_path):
    """The operator's 2026-08-29 law: exhaustion is a clean stop.

    Regression (Phase-1 M1-H0, run-fe00609058e1...): a run that reached
    its budget and finished with 47 admitted conjectures must not have
    blame manufactured for it out of ordinary in-run schema repairs.
    """
    root = _write_root(
        tmp_path, message="", state="completed", stop_reason="budget_exhausted",
        refusal="STOPPED_REFUSES_UNFINISHED_WORKFLOW_AUTHORITY",
        events=[_event(0), _event(1, attempts=[
            _attempt(valid=False, validation_path="/candidates/0/evidence_refs/1/block")])],
        qualification=_qualification())
    report = stop_report(root)
    boxes = report["sections"]["classification"]["boxes"]
    assert all(box["verdict"] == "RULED OUT" for box in boxes.values())
    # The clean stop still has a continuability story, and that is the
    # part the operator needs.
    assert report["sections"]["continuability"]["continue"] == "REFUSED"


def test_one_seats_pass_never_vindicates_a_different_seats_failure(tmp_path):
    """Regression (P-A2 epoch 1): 22 of 23 pairs passed and ONE failed.

    Reading the 22 as vindication of the 1 would repeat, in the opposite
    direction, the misreading this report exists to prevent.
    """
    payload = _qualification(first_pass=20, eventual=20, qualified=True)
    failing = json.loads(json.dumps(payload["pairs"][0]))
    failing["pair"]["role"] = "grounding_reviewer"
    failing["pair"]["contract_id"] = "groundingrepairwirev1.direct.v1"
    failing["first_pass_valid_count"] = 4
    failing["eventual_valid_count"] = 5
    failing["qualified"] = False
    for index, case in enumerate(failing["cases"]):
        ok = index < 4
        case["first_pass_valid"] = ok
        case["eventual_valid"] = index < 5
    payload["pairs"].append(failing)
    root = _write_root(
        tmp_path, message="qualification refused one pair",
        events=[_event(0), _event(1, attempts=[_attempt(valid=True)])],
        qualification=payload)
    report = stop_report(root)
    assert _ranked(report)[0] == "MODEL"
    assert _box(report, "MODEL")["verdict"] == "SUPPORTED"
    supporting = json.dumps(_box(report, "MODEL")["supporting"])
    assert "grounding_reviewer" in supporting
    assert "conjecturer" not in supporting, (
        "the passing seat must not be dragged into the failing seat's box")
