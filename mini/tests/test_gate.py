"""M1 — shared anti-relapse admission plus process-only orbit analytics."""

from deepreason.ontology import Commitment, Provenance, Warrant, WarrantType
from deepreason.rules.guards import anti_relapse
from minireason import gate
from minireason.checks import compile_checks
from minireason.compat import MINI_NEAR_DUP_EPS
from minireason.loop import Session

BAD = '{"claim": "c", "mechanism": "m", "forbidden": []}'  # refuted on arrival


def _relapse_receipts(session, kind):
    import json as _json
    path = session.root / "relapse.log.jsonl"
    if not path.exists():
        return []
    return [
        record
        for line in path.read_text().splitlines()
        if (record := _json.loads(line)).get("type") == kind
    ]


def _register(session, content, stance="mechanist", pid="pi-0"):
    cks = compile_checks(content)
    commitment_ids = session.register_commitments(cks)
    artifact = session.build_candidate(content, commitment_ids, stance)
    session.register_candidates([(artifact, [])], pid, None)
    return artifact, cks


def _refuted_session(tmp_path):
    s = Session(tmp_path / "run")
    s.spawn_problem("pi-0", "d")
    artifact, cks = _register(s, BAD)
    s.refute(artifact.id, [{"commitment": "skeleton-wf", "eval": "program:skeleton_wf",
                            "verdict": "fail"}])
    assert s.state.refuted == {artifact.id}
    return s, artifact, cks


def test_hash_relapse_blocked(tmp_path):
    s, artifact, _ = _refuted_session(tmp_path)
    ok, reason = s.admit_candidate(artifact)
    assert not ok and reason.startswith("hash:") and artifact.id[:12] in reason


def test_structural_battery_alone_admits_paraphrase_with_receipt(tmp_path):
    """Contract change (bronze flat v1 repair): a battery whose evaluable
    members are all structural well-formedness checks cannot establish
    relapse equivalence. The paraphrase is admitted and the skip is
    receipted, never silent."""
    s, prior, cks = _refuted_session(tmp_path)
    shuffled = '{"mechanism": "m", "claim": "c", "forbidden": []}'
    candidate = s.build_candidate(shuffled, [c["id"] for c in cks], "mechanist")
    ok, reason = s.admit_candidate(candidate)
    assert ok and reason == "admitted"
    receipts = _relapse_receipts(s, "relapse-structural-only")
    assert any(
        r["candidate_id"] == candidate.id and r["prior_id"] == prior.id
        for r in receipts
    )


def test_substantive_battery_still_blocks_paraphrase(tmp_path):
    """With at least one substantive commitment in the shared battery,
    verdict-vector equivalence blocks exactly as before."""
    s = Session(tmp_path / "run")
    s.spawn_problem("pi-0", "d")
    base = Commitment(id="base-sub", eval="predicate:len(content) > 3")
    s.harness.register_commitment(base)
    prior = s.build_candidate('{"claim": "c", "mechanism": "m"}', [base.id], "mechanist")
    s.register_candidates([(prior, [])], "pi-0", None)
    s.refute(prior.id, [{"commitment": base.id, "eval": base.eval, "verdict": "fail"}])
    shuffled = '{"mechanism": "m", "claim": "c"}'
    candidate = s.build_candidate(shuffled, [base.id], "mechanist")
    ok, reason = s.admit_candidate(candidate)
    assert not ok and "to refuted" in reason and prior.id[:12] in reason


def test_genuinely_new_content_admitted(tmp_path):
    s, _, _ = _refuted_session(tmp_path)
    content = (
        '{"claim": "entirely new", "mechanism": "different", '
        '"forbidden": [{"case": "valid json", "eval": "program:json-wf"}]}'
    )
    cks = compile_checks(content)
    ids = s.register_commitments(cks)
    candidate = s.build_candidate(content, ids, "mechanist")
    ok, reason = s.admit_candidate(candidate)
    assert ok and reason == "admitted"


def test_candidate_commitments_are_visible_only_in_temporary_guard_overlay(tmp_path):
    session = Session(tmp_path / "run")
    session.spawn_problem("pi-0", "d")
    base = Commitment(id="base", eval="predicate:len(content) > 0")
    session.harness.register_commitment(base)
    prior = session.build_candidate("old idea", [base.id], "mechanist")
    session.register_candidates([(prior, [])], "pi-0", None)
    session.refute(
        prior.id,
        [{"commitment": base.id, "eval": base.eval, "verdict": "fail"}],
    )

    candidate_only = Commitment(
        id="candidate-only",
        eval="predicate:'new' in content",
    )
    # A near-paraphrase of the prior: the semantic stage keeps the prior in
    # range, so the battery comparison is what decides.
    candidate = session.build_candidate(
        "old idea new",
        [base.id, candidate_only.id],
        "mechanist",
    )

    # Without the candidate-only predicate, the active battery sees the same
    # verdict and blocks. The temporary overlay makes the differing verdict
    # visible, but does not mutate canonical commitments during admission.
    assert session.admit_candidate(candidate)[0] is False
    assert session.admit_candidate(
        candidate,
        candidate_commitments=[candidate_only],
    ) == (True, "admitted")
    assert candidate_only.id not in session.harness.commitments


def test_live_duplicates_are_never_gated(tmp_path):
    s = Session(tmp_path / "run")
    s.spawn_problem("pi-0", "d")
    good = (
        '{"claim": "c", "mechanism": "m", "forbidden": '
        '[{"case": "x", "eval": "program:json-wf"}]}'
    )
    artifact, _ = _register(s, good)
    ok, _ = s.admit_candidate(artifact)
    assert ok  # dedupe is the caller's job; the gate only blocks relapse


def test_orbit_healthy_never_fires(tmp_path):
    s = Session(tmp_path / "run")
    s.spawn_problem("pi-0", "d")
    for i in range(30):
        _register(s, f'{{"claim": "c{i}", "mechanism": "m{i}"}}')
    assert gate.gate_blocks(s.state.events, 20) == []
    assert gate.orbit(s.state.events, s.state.artifacts) is None


def test_orbit_fires_at_floor_and_names_the_school(tmp_path):
    s, artifact, _ = _refuted_session(tmp_path)
    for _ in range(5):  # the measured orbiting arms logged 7-14 per window
        ok, reason = s.admit_candidate(artifact)
        assert not ok
        s.measure([f"gate:{reason}"])
    assert len(gate.gate_blocks(s.state.events, 20)) == 5
    assert gate.orbit(s.state.events, s.state.artifacts, window=20, floor=5) == "mechanist"
    # One block below the floor: silent.
    assert gate.orbit(s.state.events, s.state.artifacts, window=20, floor=6) is None
    # Outside the window: silent again (rate, not lifetime count).
    for _ in range(25):
        s.measure(["padding"])
    assert gate.orbit(s.state.events, s.state.artifacts, window=20, floor=5) is None


def test_mini_admission_matches_full_guard_for_all_outcomes(tmp_path):
    """The reduced engine is a facade over the full normative guard."""
    s, prior, cks = _refuted_session(tmp_path)
    shuffled = '{"mechanism": "m", "claim": "c", "forbidden": []}'
    equivalent = s.build_candidate(shuffled, [c["id"] for c in cks], "mechanist")
    novel_text = (
        '{"claim": "novel", "mechanism": "different", '
        '"forbidden": [{"case": "valid json", "eval": "program:json-wf"}]}'
    )
    novel_checks = compile_checks(novel_text)
    novel_ids = s.register_commitments(novel_checks)
    novel = s.build_candidate(novel_text, novel_ids, "mechanist")

    for candidate in (prior, equivalent, novel):
        assert s.admit_candidate(candidate) == anti_relapse.check(
            candidate,
            [],
            s.harness,
            **s.guard_scope(candidate),
        )


def test_counter_warrant_exception_is_identical_to_full_guard(tmp_path):
    """The counter-warrant exemption is reachable only through a substantive
    battery (structural-only batteries never block, so there is nothing to
    exempt); mini and the full guard agree on the whole path."""
    s = Session(tmp_path / "run")
    s.spawn_problem("pi-0", "d")
    base = Commitment(id="base-cw", eval="predicate:len(content) > 3")
    s.harness.register_commitment(base)
    prior = s.build_candidate('{"claim": "c", "mechanism": "m"}', [base.id], "mechanist")
    s.register_candidates([(prior, [])], "pi-0", None)
    s.refute(prior.id, [{"commitment": base.id, "eval": base.eval, "verdict": "fail"}])
    refuter = next(
        attacker
        for attacker, target in s.harness.state.att
        if target in s.state.refuted and attacker in s.state.accepted
    )
    nu = s.harness.create_artifact(
        "nu: the refuter is unsound", provenance=Provenance(role="critic")
    )
    counter = Warrant(
        id="w-mini-counter",
        target=refuter,
        type=WarrantType.ARGUMENTATIVE,
        validity_node=nu.id,
    )
    shuffled = '{"mechanism": "m", "claim": "c"}'
    candidate = s.build_candidate(shuffled, [base.id], "mechanist", [counter])

    # Blocked without the counter-warrant, admitted with it; the full guard
    # under identical scope returns the identical pair.
    assert s.admit_candidate(candidate)[0] is False
    mini_result = s.admit_candidate(candidate, [counter])
    full_result = anti_relapse.check(
        candidate,
        [counter],
        s.harness,
        **s.guard_scope(candidate),
    )
    assert mini_result == full_result == (True, "admitted")
