"""thesis view (§8): the record argued as one committed position —
pack fidelity, deterministic trimming, program-checked citations with one
repair pass, and read-only discipline over the run root."""

import hashlib
import json

import pytest

from deepreason.harness import Harness
from deepreason.informal.trial import transcript_blob
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.budget import TokenMeter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.ontology import (
    Problem,
    ProblemProvenance,
    Provenance,
    Warrant,
    WarrantType,
)
from deepreason.storage.blobs import BlobStore
from deepreason.views.thesis import (
    check_citations,
    evidence_pack,
    render_thesis,
    thesis,
)


def _skel(claim: str, mechanism: str = "a concrete mechanism") -> str:
    return json.dumps({"claim": claim, "mechanism": mechanism,
                       "forbidden": [{"case": f"evidence against {claim[:20]}",
                                      "eval": "rubric:std"}]})


def _seed_root(tmp_path) -> tuple[Harness, dict]:
    """Two survivors (one HV-ranked), one argued refutation with a trial
    transcript, one pairwise ruling — the shapes a real root carries."""
    h = Harness(tmp_path / "run")
    h.register_problem(Problem(
        id="pi-x", description="why did X happen?",
        provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []})))
    a = h.create_artifact(_skel("mechanism alpha explains X"),
                          provenance=Provenance(role="conjecturer", school="s0"),
                          problem_id="pi-x")
    b = h.create_artifact(_skel("mechanism beta explains X"),
                          provenance=Provenance(role="conjecturer", school="s1"),
                          problem_id="pi-x")
    h.record_measure(hv={a.id: 0.9, b.id: 0.2})
    doomed = h.create_artifact(_skel("moods explain X"),
                               provenance=Provenance(role="conjecturer"),
                               problem_id="pi-x")
    nu = h.create_artifact("nu: the case against moods is sound",
                           provenance=Provenance(role="critic"))
    trace = transcript_blob(h, case="names no mechanism, only a mood",
                            answer="the mood is load-bearing",
                            decisive_point="names no mechanism, only a mood")
    h.create_artifact(
        "critic: moods name no mechanism and forbid nothing checkable",
        provenance=Provenance(role="critic"),
        warrants=[Warrant(id="w-moods", target=doomed.id,
                          type=WarrantType.ARGUMENTATIVE, trace_ref=trace,
                          validity_node=nu.id)])
    # Pairwise ruling artifact (the shape pairwise_discriminate writes).
    h.create_artifact(
        json.dumps({"pairwise": {"problem": "pi-x", "winner": a.id,
                                 "loser": b.id,
                                 "decisive_point": "alpha names the carrier"}},
                   sort_keys=True),
        codec="json", provenance=Provenance(role="critic"))
    return h, {"a": a.id, "b": b.id, "doomed": doomed.id}


def _valid_output(ids, citations=None):
    return json.dumps({
        "thesis": "Mechanism alpha is the best-supported account of X.",
        "argument": [{"heading": "The surviving mechanism",
                      "body": "alpha survived criticism and won pairwise.",
                      "citations": citations or [ids["a"][:12]]}],
        "rebuttals": [{"heading": "Against moods",
                       "body": "the record felled it: no mechanism named.",
                       "citations": [ids["doomed"][:12]]}],
        "rivals": [{"artifact": ids["b"][:12], "position": "mechanism beta",
                    "discriminator": "a test separating alpha from beta"}],
        "overturn": ["evidence that alpha's carrier does not exist"],
    })


def _adapter(h, responses):
    return LLMAdapter({"thesis": MockEndpoint(responses)},
                      BlobStore(h.root.parent / "scratch-blobs"),
                      retry_max=2, meter=TokenMeter(budget=10**9))


def test_pack_carries_the_record(tmp_path):
    h, ids = _seed_root(tmp_path)
    pack = evidence_pack(h)
    assert "mechanism alpha explains X" in pack
    assert f"[{ids['a'][:12]}]" in pack and "hv 0.90" in pack
    assert "REFUTED: moods explain X" in pack
    assert "names no mechanism, only a mood" in pack       # case + decisive
    assert f"[{ids['a'][:12]}] beat [{ids['b'][:12]}]" in pack  # pairwise
    assert "UNRESOLVED RIVALRIES" in pack and "pi-x:" in pack


def test_pack_trims_deterministically(tmp_path):
    h, ids = _seed_root(tmp_path)
    for i in range(30):
        h.create_artifact(_skel(f"filler mechanism {i}", "m" * 400),
                          provenance=Provenance(role="conjecturer"),
                          problem_id="pi-x")
    small = evidence_pack(h, budget_chars=3000)
    assert small == evidence_pack(h, budget_chars=3000)  # deterministic
    assert len(small) <= 3000 + 400  # footer + section-header slack
    assert "omitted for budget" in small
    # The top-HV survivor is never trimmed (registration-priority within HV).
    assert ids["a"][:12] in small


def test_default_problem_is_the_seed(tmp_path):
    h, _ = _seed_root(tmp_path)
    # A spawned successor exists too; the seed must be chosen by default.
    h.register_problem(Problem(
        id="pi-child", description="a successor",
        provenance=ProblemProvenance.model_validate(
            {"trigger": "successor", "from": ["pi-x"]})))
    assert evidence_pack(h).startswith("PROBLEM pi-x:")


def test_citation_check_flags_fabricated_ids(tmp_path):
    h, ids = _seed_root(tmp_path)
    pack = evidence_pack(h)
    _, pack_ids = __import__("deepreason.views.thesis", fromlist=["_pack"])._pack(
        h, "pi-x", 24_000)
    from deepreason.llm.contracts import ThesisOutput
    good = ThesisOutput.model_validate_json(_valid_output(ids))
    assert check_citations(good, pack_ids) == []
    bad = ThesisOutput.model_validate_json(
        _valid_output(ids, citations=["deadbeefcafe"]))
    assert check_citations(bad, pack_ids) == ["deadbeefcafe"]
    assert pack  # pack is what the ids were drawn from


def test_thesis_retries_on_bad_citation_then_passes(tmp_path):
    h, ids = _seed_root(tmp_path)
    seen = []

    def fn(prompt):
        seen.append(prompt)
        # First call fabricates an id; the repair call cites a real one.
        return (_valid_output(ids, citations=["deadbeefcafe"]) if len(seen) == 1
                else _valid_output(ids))

    result = thesis(h, _adapter(h, fn))
    assert result["citation_check"] == {"ok": True, "unresolved": [], "retried": True}
    assert "CITATION VIOLATION" in seen[1]
    assert "deadbeefcafe" in seen[1]
    assert result["spend"]["calls"] == 2


def test_thesis_annotates_when_retry_also_bad(tmp_path):
    h, ids = _seed_root(tmp_path)
    result = thesis(h, _adapter(
        h, lambda p: _valid_output(ids, citations=["deadbeefcafe"])))
    assert not result["citation_check"]["ok"]
    assert result["citation_check"]["unresolved"] == ["deadbeefcafe"]
    assert result["citation_check"]["retried"] is True
    assert result["output"].thesis  # output still returned, never raised


def test_read_only_over_the_root(tmp_path):
    h, ids = _seed_root(tmp_path)
    log = h.root / "log.jsonl"
    before_log = hashlib.sha256(log.read_bytes()).hexdigest()
    before_blobs = sorted(p.name for p in (h.root / "blobs").rglob("*") if p.is_file())
    result = thesis(h, _adapter(h, lambda p: _valid_output(ids)))
    assert result["citation_check"]["ok"]
    assert hashlib.sha256(log.read_bytes()).hexdigest() == before_log
    assert sorted(p.name for p in (h.root / "blobs").rglob("*")
                  if p.is_file()) == before_blobs


def test_adapter_sharing_run_blobs_is_rejected(tmp_path):
    h, ids = _seed_root(tmp_path)
    shared = LLMAdapter({"thesis": MockEndpoint([_valid_output(ids)])},
                        h.blobs, retry_max=2, meter=TokenMeter(budget=10**9))
    with pytest.raises(ValueError, match="read-only"):
        thesis(h, shared)


def test_spend_reported_in_result_and_render(tmp_path):
    h, ids = _seed_root(tmp_path)
    result = thesis(h, _adapter(h, lambda p: _valid_output(ids)))
    assert result["spend"]["tokens"] > 0
    assert result["spend"]["meter"]["total"] > 0
    prose = render_thesis(result)
    assert prose.startswith("# Thesis: pi-x")
    assert "spend:" in prose and "tokens" in prose
    assert "## Thesis" in prose and "## Rebuttals" in prose
    assert "## Live rivals" in prose and "## What would overturn this" in prose
