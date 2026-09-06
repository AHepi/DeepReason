"""`tools/record_claims.py`: universal statements tested against a run record.

Every root here is SYNTHETIC and built from the shapes the real record uses
(`log.jsonl` events carrying `seq`/`rule`/`inputs`/`control`, `objects/<kind>/
<sha>.json` carrying `data`, `run-status.json` carrying `state`/`stop_reason`).
Nothing copies a committed root, so a retired or renamed root cannot break
these tests; the two that DO read committed evidence say so and select it by
property.

Each refutation carries a mutation proof: the same root with the one field the
claim reads changed flips the verdict. A test that passes for a reason other
than the field it names is a test that will keep passing after the behaviour
it guards is gone.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
TOOL = REPO / "tools" / "record_claims.py"


def _load_tool():
    spec = importlib.util.spec_from_file_location("record_claims_under_test", TOOL)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


rc = _load_tool()


# ---------------------------------------------------------------------------
# synthetic roots
# ---------------------------------------------------------------------------


def make_root(
    directory: Path,
    *,
    status: dict | None = None,
    events: list[dict] | None = None,
    objects: dict[str, list[dict]] | None = None,
) -> Path:
    """One run root with exactly the record content a test needs."""

    directory.mkdir(parents=True, exist_ok=True)
    payload = {
        "run_id": "run" + hashlib.sha256(str(directory).encode()).hexdigest()[:16],
        "state": "completed",
        "stop_reason": "max_cycles",
        "workload": "text",
        "cycle": 4,
    }
    payload.update(status or {})
    (directory / "run-status.json").write_text(json.dumps(payload))
    lines = []
    for index, event in enumerate(events or []):
        row = {"seq": index, "rule": "Register", "inputs": [], "outputs": []}
        row.update(event)
        lines.append(json.dumps(row))
    (directory / "log.jsonl").write_text("\n".join(lines) + ("\n" if lines else ""))
    for kind, records in (objects or {}).items():
        folder = directory / "objects" / kind
        folder.mkdir(parents=True, exist_ok=True)
        for record in records:
            blob = json.dumps(record, sort_keys=True)
            stem = hashlib.sha256(blob.encode()).hexdigest()
            (folder / f"{stem}.json").write_text(
                json.dumps({"data": record, "id": stem, "schema": kind})
            )
    return directory


def measure(code: str, *rest: str) -> dict:
    return {"rule": "Measure", "inputs": [code, *rest]}


def control(action: str) -> dict:
    return {"rule": "Control", "control": {"schema": "control.event.v3", "action": action}}


def claims_file(path: Path, *claims: dict) -> Path:
    path.write_text(
        json.dumps(
            {
                "schema_version": rc.SCHEMA_VERSION,
                "title": "synthetic",
                "claims": list(claims),
            }
        )
    )
    return path


def verdicts(claims_path: Path, *roots: Path) -> dict[str, tuple[str, str]]:
    title, claims = rc.load_claims(claims_path)
    records = [rc.RunRecord(root) for root in roots]
    return {
        result.claim.claim_id: (result.status, result.standing)
        for result in rc.evaluate(claims, records)
    }


# ---------------------------------------------------------------------------
# one refutation per primitive kind, each with its mutation proof
# ---------------------------------------------------------------------------


def test_a_status_field_refutes_a_never_claim(tmp_path):
    claim = {
        "claim_id": "S1",
        "statement": "A run never stops operational_failure.",
        "kind": "never",
        "condition": {"status": {"field": "stop_reason", "in": ["operational_failure"]}},
    }
    path = claims_file(tmp_path / "c.json", claim)

    bad = make_root(tmp_path / "bad", status={"state": "failed", "stop_reason": "operational_failure"})
    assert verdicts(path, bad)["S1"][0] == rc.STATUS_REFUTED

    # Mutation: the one field the claim reads, and nothing else.
    good = make_root(tmp_path / "good", status={"state": "failed", "stop_reason": "budget_exhausted"})
    assert verdicts(path, good)["S1"][0] == rc.STATUS_UNREFUTED


def test_an_event_rule_refutes_a_never_claim(tmp_path):
    claim = {
        "claim_id": "S2",
        "statement": "A run never records a criticism.",
        "kind": "never",
        "condition": {"event": {"rule": "Crit", "min_count": 1}},
    }
    path = claims_file(tmp_path / "c.json", claim)

    bad = make_root(tmp_path / "bad", events=[{"rule": "Crit"}])
    assert verdicts(path, bad)["S2"][0] == rc.STATUS_REFUTED

    good = make_root(tmp_path / "good", events=[{"rule": "Conj"}])
    assert verdicts(path, good)["S2"][0] == rc.STATUS_UNREFUTED


def test_a_measure_code_refutes_a_never_claim(tmp_path):
    claim = {
        "claim_id": "S3",
        "statement": "The seat never cites an id the dossier does not hold.",
        "kind": "never",
        "condition": {"measure": {"code": "evidence-citation:EVIDENCE_REF_UNKNOWN_BLOCK"}},
    }
    path = claims_file(tmp_path / "c.json", claim)

    bad = make_root(
        tmp_path / "bad",
        events=[measure("evidence-citation:EVIDENCE_REF_UNKNOWN_BLOCK", "abc", "art", "q")],
    )
    assert verdicts(path, bad)["S3"][0] == rc.STATUS_REFUTED

    good = make_root(
        tmp_path / "good",
        events=[measure("evidence-citation:EVIDENCE_CITATION_VERIFIED", "abc", "art", "q")],
    )
    assert verdicts(path, good)["S3"][0] == rc.STATUS_UNREFUTED


def test_a_measure_code_prefix_matches_a_family_of_codes(tmp_path):
    claim = {
        "claim_id": "S3b",
        "statement": "A run never checks a citation.",
        "kind": "never",
        "condition": {"measure": {"code_prefix": "evidence-citation:"}},
    }
    path = claims_file(tmp_path / "c.json", claim)

    bad = make_root(tmp_path / "bad", events=[measure("evidence-citation:EVIDENCE_QUOTE_MISMATCH")])
    assert verdicts(path, bad)["S3b"][0] == rc.STATUS_REFUTED

    good = make_root(tmp_path / "good", events=[measure("evidence-citations-elsewhere")])
    assert verdicts(path, good)["S3b"][0] == rc.STATUS_UNREFUTED


def test_a_control_action_refutes_a_never_claim(tmp_path):
    claim = {
        "claim_id": "S4",
        "statement": "A run never records a lifecycle stop.",
        "kind": "never",
        "condition": {"control": {"action": "lifecycle_stopped"}},
    }
    path = claims_file(tmp_path / "c.json", claim)

    bad = make_root(tmp_path / "bad", events=[control("lifecycle_stopped")])
    assert verdicts(path, bad)["S4"][0] == rc.STATUS_REFUTED

    good = make_root(tmp_path / "good", events=[control("work_transition")])
    assert verdicts(path, good)["S4"][0] == rc.STATUS_UNREFUTED


def test_an_object_field_refutes_a_never_claim(tmp_path):
    claim = {
        "claim_id": "S5",
        "statement": "The critic never exhausts its smallest authorized contract.",
        "kind": "never",
        "condition": {
            "object": {
                "kind": "workflow-route-seat-insufficient-capability-v1",
                "where": [
                    ["route_lease.role", "eq", "argumentative_critic"],
                    ["reason", "eq", "smallest_authorized_contract_schema_exhausted"],
                ],
            }
        },
    }
    path = claims_file(tmp_path / "c.json", claim)

    def root(name, role):
        return make_root(
            tmp_path / name,
            objects={
                "workflow-route-seat-insufficient-capability-v1": [
                    {
                        "route_lease": {"role": role, "seat": 0},
                        "reason": "smallest_authorized_contract_schema_exhausted",
                    }
                ]
            },
        )

    assert verdicts(path, root("bad", "argumentative_critic"))["S5"][0] == rc.STATUS_REFUTED

    # Mutation: the same exhaustion, a different seat. This is exactly the real
    # ARM R case, and the claim must survive it.
    survived = verdicts(path, root("good", "conjecturer"))["S5"]
    assert survived == (rc.STATUS_UNREFUTED, rc.STANDING_NOT_SHOWN)


def test_an_always_claim_is_refuted_by_a_root_where_it_does_not_hold(tmp_path):
    claim = {
        "claim_id": "A1",
        "statement": "A run reaches a completed terminal.",
        "kind": "always",
        "condition": {"status": {"field": "state", "eq": "completed"}},
    }
    path = claims_file(tmp_path / "c.json", claim)

    bad = make_root(tmp_path / "bad", status={"state": "failed"})
    assert verdicts(path, bad)["A1"][0] == rc.STATUS_REFUTED

    good = make_root(tmp_path / "good", status={"state": "completed"})
    assert verdicts(path, good)["A1"][0] == rc.STATUS_UNREFUTED


def test_a_root_where_every_claim_survives(tmp_path):
    path = claims_file(
        tmp_path / "c.json",
        {
            "claim_id": "S1",
            "statement": "never stops operational_failure",
            "kind": "never",
            "condition": {"status": {"field": "stop_reason", "eq": "operational_failure"}},
        },
        {
            "claim_id": "S2",
            "statement": "never records a criticism",
            "kind": "never",
            "condition": {"event": {"rule": "Crit"}},
        },
        {
            "claim_id": "A1",
            "statement": "always reaches a completed terminal",
            "kind": "always",
            "condition": {"status": {"field": "state", "eq": "completed"}},
        },
    )
    clean = make_root(
        tmp_path / "clean",
        status={"state": "completed", "stop_reason": "max_cycles"},
        events=[{"rule": "Conj"}, measure("cycle", "4")],
    )
    for status, _ in verdicts(path, clean).values():
        assert status == rc.STATUS_UNREFUTED


# ---------------------------------------------------------------------------
# the standing
# ---------------------------------------------------------------------------


def test_standing_fires_when_the_condition_held_nowhere(tmp_path):
    claim = {
        "claim_id": "N1",
        "statement": "The seat never cites a block admitted but withheld from the legend.",
        "kind": "never",
        "condition": {"measure": {"code": "evidence-citation:EVIDENCE_REF_NOT_EXPOSED"}},
    }
    path = claims_file(tmp_path / "c.json", claim)
    root = make_root(
        tmp_path / "r",
        events=[measure("evidence-citation:EVIDENCE_CITATION_VERIFIED")],
    )
    assert verdicts(path, root)["N1"] == (rc.STATUS_UNREFUTED, rc.STANDING_NOT_SHOWN)


def test_standing_is_shown_when_the_condition_held_outside_the_scope(tmp_path):
    """A survival whose predicate DID hold somewhere is a different animal."""

    claim = {
        "claim_id": "N2",
        "statement": "A completed run never stops operational_failure.",
        "kind": "never",
        "scope": {"states": ["completed"]},
        "condition": {"status": {"field": "stop_reason", "eq": "operational_failure"}},
    }
    path = claims_file(tmp_path / "c.json", claim)
    in_scope = make_root(tmp_path / "ok", status={"state": "completed", "stop_reason": "max_cycles"})
    out_of_scope = make_root(
        tmp_path / "dead", status={"state": "failed", "stop_reason": "operational_failure"}
    )
    result = verdicts(path, in_scope, out_of_scope)["N2"]
    assert result == (rc.STATUS_UNREFUTED, rc.STANDING_SHOWN)

    # Without the out-of-scope root the same survival reads differently, and
    # that difference is the whole point of the standing.
    assert verdicts(path, in_scope)["N2"] == (rc.STATUS_UNREFUTED, rc.STANDING_NOT_SHOWN)


def test_the_not_shown_sentence_is_printed_not_left_to_the_reader(tmp_path):
    claim = {
        "claim_id": "N1",
        "statement": "never cites an unexposed block",
        "kind": "never",
        "condition": {"measure": {"code": "evidence-citation:EVIDENCE_REF_NOT_EXPOSED"}},
    }
    path = claims_file(tmp_path / "c.json", claim)
    root = make_root(tmp_path / "r")
    title, claims = rc.load_claims(path)
    records = [rc.RunRecord(root)]
    report = rc.render(rc.evaluate(claims, records), records, title)
    assert rc.NOT_SHOWN_SENTENCE in report
    assert rc.STANDING_NOT_SHOWN in report


def test_not_tested_when_the_scope_admits_no_supplied_root(tmp_path):
    claim = {
        "claim_id": "T1",
        "statement": "The deferred arm never stops operational_failure.",
        "kind": "never",
        "scope": {"root_names": ["run-armh"]},
        "condition": {"status": {"field": "stop_reason", "eq": "operational_failure"}},
    }
    path = claims_file(tmp_path / "c.json", claim)
    other = make_root(tmp_path / "run-armr", status={"stop_reason": "operational_failure"})
    assert verdicts(path, other)["T1"][0] == rc.STATUS_NOT_TESTED


def test_every_scope_key_selects(tmp_path):
    root = make_root(
        tmp_path / "run-one",
        status={"state": "failed", "stop_reason": "operational_failure", "workload": "text"},
    )
    record = rc.RunRecord(root)
    for key, value in (
        ("run_ids", record.run_id),
        ("root_names", "run-one"),
        ("states", "failed"),
        ("stop_reasons", "operational_failure"),
        ("workloads", "text"),
    ):
        assert rc.Scope({key: [value]}, "scope").admits(record), key
        assert not rc.Scope({key: ["something-else"]}, "scope").admits(record), key


# ---------------------------------------------------------------------------
# the vocabulary fails closed
# ---------------------------------------------------------------------------


def test_vocabulary_refuses_an_unknown_condition_key():
    with pytest.raises(rc.ClaimsError) as excinfo:
        rc.compile_condition({"stop_resaon": {"eq": "x"}})
    assert "unknown condition key" in str(excinfo.value)


def test_vocabulary_refuses_a_condition_with_more_than_one_key():
    with pytest.raises(rc.ClaimsError):
        rc.compile_condition({"event": {"rule": "Crit"}, "control": {"action": "x"}})


def test_vocabulary_refuses_an_unknown_event_rule():
    with pytest.raises(rc.ClaimsError) as excinfo:
        rc.compile_condition({"event": {"rule": "Criticise"}})
    assert "not a record rule name" in str(excinfo.value)


def test_vocabulary_refuses_an_unknown_operator():
    with pytest.raises(rc.ClaimsError):
        rc.compile_condition({"object": {"kind": "artifact", "where": [["id", "matches", "x"]]}})


def test_vocabulary_refuses_an_unknown_claim_key():
    with pytest.raises(rc.ClaimsError):
        rc.Claim(
            {
                "claim_id": "X",
                "statement": "s",
                "kind": "never",
                "condition": {"event": {"rule": "Crit"}},
                "readiness": "PASS",
            },
            "claims[0]",
        )


def test_vocabulary_refuses_an_unknown_scope_key():
    with pytest.raises(rc.ClaimsError):
        rc.Scope({"models": ["glm"]}, "scope")


def test_vocabulary_refuses_a_measure_naming_both_code_and_prefix():
    with pytest.raises(rc.ClaimsError):
        rc.compile_condition({"measure": {"code": "a", "code_prefix": "a"}})


def test_a_claims_file_with_the_wrong_schema_version_is_refused(tmp_path):
    path = tmp_path / "c.json"
    path.write_text(json.dumps({"schema_version": "creib.conformance-pilot.claims.v1", "claims": []}))
    with pytest.raises(rc.ClaimsError) as excinfo:
        rc.load_claims(path)
    assert "schema_version" in str(excinfo.value)


def test_a_repeated_claim_id_is_refused():
    entry = {
        "claim_id": "D1",
        "statement": "s",
        "kind": "never",
        "condition": {"event": {"rule": "Crit"}},
    }
    with pytest.raises(rc.ClaimsError) as excinfo:
        rc.claims_from_dict(
            {"schema_version": rc.SCHEMA_VERSION, "claims": [dict(entry), dict(entry)]}
        )
    assert "repeats" in str(excinfo.value)


def test_the_rule_names_agree_with_the_record_s_own_enum():
    """The tool copies the rule names rather than importing the harness.

    The copy is what keeps this instrument read-only; this test is what keeps
    the copy true. A rule added to the record fails here rather than silently
    making a claim about it unwritable.
    """

    from deepreason.ontology.event import Rule

    assert set(rc.EVENT_RULES) == {member.value for member in Rule}


# ---------------------------------------------------------------------------
# paths and quantifiers
# ---------------------------------------------------------------------------


def test_every_quantifier_holds_of_all_elements_and_any_of_one(tmp_path):
    sections = {"sections": [{"plugin_id": "dr.problem"}, {"plugin_id": "dr.output-contract.organiser"}]}
    root = make_root(tmp_path / "r", objects={"plan": [sections]})
    path = claims_file(
        tmp_path / "c.json",
        {
            "claim_id": "ANY",
            "statement": "a plan never names the organiser contract",
            "kind": "never",
            "condition": {
                "object": {
                    "kind": "plan",
                    "where": [["any:sections[].plugin_id", "eq", "dr.output-contract.organiser"]],
                }
            },
        },
        {
            "claim_id": "EVERY",
            "statement": "a plan never omits the organiser contract entirely",
            "kind": "never",
            "condition": {
                "object": {
                    "kind": "plan",
                    "where": [["every:sections[].plugin_id", "ne", "dr.output-contract.organiser"]],
                }
            },
        },
    )
    result = verdicts(path, root)
    assert result["ANY"][0] == rc.STATUS_REFUTED
    assert result["EVERY"][0] == rc.STATUS_UNREFUTED


def test_every_quantifier_is_vacuously_true_on_an_empty_list(tmp_path):
    """Documented in docs/CLAIMS_SCHEMA.md, and pinned here so it stays known."""

    root = make_root(tmp_path / "r", objects={"plan": [{"sections": []}]})
    path = claims_file(
        tmp_path / "c.json",
        {
            "claim_id": "EMPTY",
            "statement": "a plan never omits the contract",
            "kind": "never",
            "condition": {
                "object": {
                    "kind": "plan",
                    "where": [["every:sections[].plugin_id", "ne", "dr.output-contract.organiser"]],
                }
            },
        },
    )
    assert verdicts(path, root)["EMPTY"][0] == rc.STATUS_REFUTED


def test_a_kind_the_root_does_not_carry_counts_zero(tmp_path):
    root = make_root(tmp_path / "r")
    path = claims_file(
        tmp_path / "c.json",
        {
            "claim_id": "K",
            "statement": "never carries that kind",
            "kind": "never",
            "condition": {"object": {"kind": "workflow-never-written-v1"}},
        },
    )
    assert verdicts(path, root)["K"] == (rc.STATUS_UNREFUTED, rc.STANDING_NOT_SHOWN)


def test_nesting_combines_conditions(tmp_path):
    root = make_root(
        tmp_path / "r",
        status={"state": "failed"},
        events=[measure("cycle", "3")],
    )
    path = claims_file(
        tmp_path / "c.json",
        {
            "claim_id": "AND",
            "statement": "never fails while recording a cycle",
            "kind": "never",
            "condition": {
                "all_of": [
                    {"status": {"field": "state", "eq": "failed"}},
                    {"measure": {"code": "cycle"}},
                ]
            },
        },
        {
            "claim_id": "NOT",
            "statement": "never avoids failing",
            "kind": "never",
            "condition": {"not": {"status": {"field": "state", "eq": "failed"}}},
        },
    )
    result = verdicts(path, root)
    assert result["AND"][0] == rc.STATUS_REFUTED
    assert result["NOT"][0] == rc.STATUS_UNREFUTED


def test_min_count_needs_that_many(tmp_path):
    root = make_root(tmp_path / "r", events=[{"rule": "Crit"}, {"rule": "Crit"}])
    path = claims_file(
        tmp_path / "c.json",
        {
            "claim_id": "TWO",
            "statement": "never records two criticisms",
            "kind": "never",
            "condition": {"event": {"rule": "Crit", "min_count": 2}},
        },
        {
            "claim_id": "THREE",
            "statement": "never records three criticisms",
            "kind": "never",
            "condition": {"event": {"rule": "Crit", "min_count": 3}},
        },
    )
    result = verdicts(path, root)
    assert result["TWO"][0] == rc.STATUS_REFUTED
    assert result["THREE"][0] == rc.STATUS_UNREFUTED


# ---------------------------------------------------------------------------
# reporting
# ---------------------------------------------------------------------------


def test_refuting_record_ids_are_capped_at_five_and_the_rest_are_counted(tmp_path):
    path = claims_file(
        tmp_path / "c.json",
        {
            "claim_id": "CAP",
            "statement": "never fails",
            "kind": "never",
            "condition": {"status": {"field": "state", "eq": "failed"}},
        },
    )
    roots = [
        make_root(tmp_path / f"r{n}", status={"state": "failed"}) for n in range(7)
    ]
    title, claims = rc.load_claims(path)
    records = [rc.RunRecord(root) for root in roots]
    result = rc.evaluate(claims, records)[0]
    payload = result.to_dict()
    assert payload["refuting"] == 7
    assert len(payload["refuting_record_ids"]) == rc.MAX_REFUTING_SHOWN == 5
    assert payload["refuting_record_ids_omitted"] == 2
    assert "+2 further refuting record id(s) not shown" in rc.render([result], records, title)


def test_a_refutation_names_a_locator_into_the_record(tmp_path):
    root = make_root(
        tmp_path / "r",
        events=[{"rule": "Register"}, measure("evidence-citation:EVIDENCE_QUOTE_MISMATCH")],
        objects={"warrant": [{"id": "w"}]},
    )
    path = claims_file(
        tmp_path / "c.json",
        {
            "claim_id": "L1",
            "statement": "never mismatches a quote",
            "kind": "never",
            "condition": {"measure": {"code": "evidence-citation:EVIDENCE_QUOTE_MISMATCH"}},
        },
        {
            "claim_id": "L2",
            "statement": "never records a warrant",
            "kind": "never",
            "condition": {"object": {"kind": "warrant"}},
        },
    )
    title, claims = rc.load_claims(path)
    records = [rc.RunRecord(root)]
    report = rc.render(rc.evaluate(claims, records), records, title)
    assert "log.jsonl:seq=1" in report
    assert "objects/warrant/" in report


def test_the_report_states_the_non_inductive_limit_and_that_it_is_not_a_gate(tmp_path):
    root = make_root(tmp_path / "r")
    path = claims_file(
        tmp_path / "c.json",
        {
            "claim_id": "Z",
            "statement": "never fails",
            "kind": "never",
            "condition": {"status": {"field": "state", "eq": "failed"}},
        },
    )
    title, claims = rc.load_claims(path)
    records = [rc.RunRecord(root)]
    report = rc.render(rc.evaluate(claims, records), records, title)
    assert "Survival is not confirmation" in report
    assert "not a gate, a status, or a score" in report


# ---------------------------------------------------------------------------
# read-only
# ---------------------------------------------------------------------------


def _digest_tree(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _committed_arm_r_root() -> Path:
    """The committed root this tranche's claims file was written against.

    Selected by PROPERTY, not by path alone: the one root under the
    writers-room tranche whose run-status reports `operational_failure`. A
    rename that retires it must not fail this test.
    """

    base = REPO / "experiments" / "2026-09-06-change-writers-room-organiser-testing" / "runs"
    for status_path in sorted(base.rglob("run-status.json")):
        try:
            status = json.loads(status_path.read_text())
        except ValueError:  # pragma: no cover - a malformed root is not this test's subject
            continue
        if status.get("stop_reason") == "operational_failure":
            return status_path.parent
    pytest.skip("no committed operational_failure root under the writers-room tranche")


def test_read_only_the_root_is_byte_identical_after_a_full_run(tmp_path):
    root = _committed_arm_r_root()
    before = _digest_tree(root)
    claims = REPO / "experiments" / "2026-09-06-change-writers-room-organiser-testing" / "claims.json"
    out = tmp_path / "report.md"
    exit_code = rc.main(
        ["--claims", str(claims), "--root", str(root), "--markdown", str(out)]
    )
    assert exit_code == 0
    assert _digest_tree(root) == before
    assert out.is_file()


def test_read_only_the_tool_imports_nothing_from_the_harness():
    source = TOOL.read_text()
    assert "import deepreason" not in source
    assert "from deepreason" not in source


def test_read_only_a_markdown_destination_inside_a_root_is_refused(tmp_path):
    root = make_root(tmp_path / "r")
    path = claims_file(
        tmp_path / "c.json",
        {
            "claim_id": "Z",
            "statement": "never fails",
            "kind": "never",
            "condition": {"status": {"field": "state", "eq": "failed"}},
        },
    )
    inside = root / "objects" / "claims.md"
    assert rc.main(["--claims", str(path), "--root", str(root), "--markdown", str(inside)]) == 2
    assert not inside.exists()


# ---------------------------------------------------------------------------
# the CLI
# ---------------------------------------------------------------------------


def test_the_cli_exits_zero_even_when_every_claim_is_refuted(tmp_path):
    """It is not a gate: refutations are the output, never the exit code."""

    root = make_root(tmp_path / "r", status={"state": "failed"})
    path = claims_file(
        tmp_path / "c.json",
        {
            "claim_id": "R",
            "statement": "never fails",
            "kind": "never",
            "condition": {"status": {"field": "state", "eq": "failed"}},
        },
    )
    completed = subprocess.run(
        [sys.executable, str(TOOL), "--claims", str(path), "--root", str(root)],
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    assert "R: REFUTED" in completed.stdout


def test_the_cli_exits_two_on_a_claims_file_it_cannot_read(tmp_path):
    root = make_root(tmp_path / "r")
    broken = tmp_path / "broken.json"
    broken.write_text("{not json")
    completed = subprocess.run(
        [sys.executable, str(TOOL), "--claims", str(broken), "--root", str(root)],
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 2


def test_the_cli_exits_two_on_a_directory_that_is_not_a_run_root(tmp_path):
    path = claims_file(
        tmp_path / "c.json",
        {
            "claim_id": "Z",
            "statement": "never fails",
            "kind": "never",
            "condition": {"status": {"field": "state", "eq": "failed"}},
        },
    )
    completed = subprocess.run(
        [sys.executable, str(TOOL), "--claims", str(path), "--root", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 2
    assert "not a run root" in completed.stderr


def test_the_json_report_carries_every_field_the_text_report_shows(tmp_path):
    root = make_root(tmp_path / "r", status={"state": "failed"})
    path = claims_file(
        tmp_path / "c.json",
        {
            "claim_id": "J",
            "statement": "never fails",
            "kind": "never",
            "condition": {"status": {"field": "state", "eq": "failed"}},
            "note": "a note",
        },
    )
    completed = subprocess.run(
        [sys.executable, str(TOOL), "--claims", str(path), "--root", str(root), "--json"],
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert payload["result_type"] == "RECORD_CLAIMS_RESULT_V1"
    row = payload["claims"][0]
    assert row["status"] == rc.STATUS_REFUTED
    assert row["standing"] == rc.STANDING_SHOWN
    assert row["note"] == "a note"
    assert row["refuting_record_ids"]
    assert row["epistemic_limit"]


# ---------------------------------------------------------------------------
# the tranche's own claims file, against the committed root
# ---------------------------------------------------------------------------


def test_the_tranche_claims_file_reports_what_the_committed_record_shows():
    """Regression (ARM R run-36d9a22c, `state: failed`): the nine claims and
    the three statuses the record decides. Selected by property (the root's own
    `operational_failure`), so retiring or renaming the root cannot break it.
    """

    root = _committed_arm_r_root()
    claims_path = (
        REPO / "experiments" / "2026-09-06-change-writers-room-organiser-testing" / "claims.json"
    )
    title, claims = rc.load_claims(claims_path)
    records = [rc.RunRecord(root)]
    got = {r.claim.claim_id: (r.status, r.standing) for r in rc.evaluate(claims, records)}
    assert got == {
        "ORG-CITE-01": (rc.STATUS_REFUTED, rc.STANDING_SHOWN),
        "ORG-PLAN-01": (rc.STATUS_UNREFUTED, rc.STANDING_NOT_SHOWN),
        "ORG-PLAN-02": (rc.STATUS_UNREFUTED, rc.STANDING_NOT_SHOWN),
        "RUN-STOP-01": (rc.STATUS_REFUTED, rc.STANDING_SHOWN),
        "CRIT-CAP-01": (rc.STATUS_UNREFUTED, rc.STANDING_NOT_SHOWN),
        "ORG-COND-01": (rc.STATUS_REFUTED, rc.STANDING_SHOWN),
        "RUN-TERM-01": (rc.STATUS_REFUTED, rc.STANDING_SHOWN),
        "EVID-EXPOSED-01": (rc.STATUS_UNREFUTED, rc.STANDING_NOT_SHOWN),
        "ARMH-STOP-01": (rc.STATUS_NOT_TESTED, rc.STANDING_SHOWN),
    }


def test_every_proxy_claim_in_the_tranche_file_says_so_in_its_note():
    """A proxy that does not announce itself is read as the thing it stands for."""

    claims_path = (
        REPO / "experiments" / "2026-09-06-change-writers-room-organiser-testing" / "claims.json"
    )
    raw = json.loads(claims_path.read_text())
    notes = {c["claim_id"]: (c.get("note") or "") for c in raw["claims"]}
    assert "PROXY" in notes["ORG-COND-01"], "the countercondition claim must declare itself a proxy"


def test_the_tranche_claims_file_carries_no_readiness_field():
    """DeepReason reads readiness from the record, never from a person.

    h-EPI's appraisal takes each argument's readiness from a person who marked
    it; that rule is not adopted here (the operator: 'no the rule from the
    other harness'). Nothing in this schema has a place to put one, and this
    test says so where a future edit would see it.
    """

    claims_path = (
        REPO / "experiments" / "2026-09-06-change-writers-room-organiser-testing" / "claims.json"
    )
    text = claims_path.read_text().lower()
    assert '"readiness"' not in text
    assert '"appraisal"' not in text
    source = TOOL.read_text().lower()
    assert "readiness" not in source.replace("readiness in deepreason", "")
