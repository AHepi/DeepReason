"""thesis view (§8): the record argued as one committed position —
pack fidelity, deterministic trimming, program-checked citations with one
repair pass, and read-only discipline over the run root."""

import hashlib
import json
import os
import stat
from types import SimpleNamespace

import pytest

from scripts import thesis as thesis_script
from deepreason.harness import Harness
from deepreason.informal import holdout
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


def _tree_snapshot(root):
    """Capture paths, types, modes, mtimes, and bytes without following links."""

    root = root.resolve()
    paths = [root, *sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix())]
    snapshot = []
    for path in paths:
        observed = path.lstat()
        if stat.S_ISREG(observed.st_mode):
            payload = path.read_bytes()
        elif stat.S_ISLNK(observed.st_mode):
            payload = os.fsencode(os.readlink(path))
        else:
            payload = b""
        snapshot.append(
            (
                "." if path == root else path.relative_to(root).as_posix(),
                stat.S_IFMT(observed.st_mode),
                stat.S_IMODE(observed.st_mode),
                observed.st_mtime_ns,
                payload,
            )
        )
    return tuple(snapshot)


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


@pytest.mark.parametrize("at_seq", [None, 0])
def test_thesis_script_current_and_historical_reads_are_physically_read_only(
    tmp_path, monkeypatch, capsys, at_seq
):
    h, _ids = _seed_root(tmp_path)
    before = _tree_snapshot(h.root)
    opened = []

    monkeypatch.setattr(
        thesis_script,
        "load_config",
        lambda _path: SimpleNamespace(roles={"thesis": {}}),
    )
    monkeypatch.setattr(
        thesis_script, "apply_overrides", lambda config, _overrides: config
    )
    monkeypatch.setattr(
        thesis_script, "role_api_key_envs", lambda _config, _roles: set()
    )
    monkeypatch.setattr(thesis_script, "build_adapter", lambda *_args, **_kwargs: object())

    def fake_thesis(harness, _adapter, *, problem_id, budget_chars):
        opened.append(harness)
        assert evidence_pack(
            harness, problem_id=problem_id, budget_chars=budget_chars
        ).startswith("PROBLEM pi-x:")
        return {"view": "read-only"}

    monkeypatch.setattr(thesis_script, "thesis", fake_thesis)
    monkeypatch.setattr(thesis_script, "render_thesis", lambda _result: "rendered")

    argv = [
        "--root",
        str(h.root),
        "--problem",
        "pi-x",
        "--config",
        str(tmp_path / "unused.yaml"),
    ]
    if at_seq is not None:
        argv.extend(["--at-seq", str(at_seq)])

    assert thesis_script.main(argv) == 0
    assert capsys.readouterr().out == "rendered\n"
    assert len(opened) == 1 and opened[0]._read_only
    assert opened[0]._next_seq == (h._next_seq if at_seq is None else at_seq + 1)
    assert _tree_snapshot(h.root) == before


def test_thesis_script_rejects_negative_historical_sequence_before_opening(
    tmp_path, capsys
):
    root = tmp_path / "absent"
    assert thesis_script.main(["--root", str(root), "--at-seq", "-1"]) == 1
    assert "--at-seq must be non-negative" in capsys.readouterr().err
    assert not root.exists()


def test_historical_thesis_never_reads_future_revealed_holdout(tmp_path):
    root = tmp_path / "holdout-history"
    harness = Harness(root)
    problem_id = "pi-holdout-history"
    harness.register_problem(
        Problem(
            id=problem_id,
            description="What does the fixed record establish?",
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": []}
            ),
        )
    )
    secret = "FUTURE SECRET MEASUREMENT"
    pairwise = json.dumps(
        {
            "pairwise": {
                "problem": problem_id,
                "winner": "candidate-a",
                "loser": "candidate-b",
                "decisive_point": secret,
            }
        },
        separators=(",", ":"),
    ).encode()
    sealed = holdout.seal(harness, pairwise, problem_id=problem_id)
    pre_reveal_seq = harness._next_seq - 1

    before_reveal = evidence_pack(
        Harness.at(root, pre_reveal_seq), problem_id=problem_id
    )
    assert secret not in before_reveal

    holdout.reveal(harness, sealed.id)
    reveal_seq = harness._next_seq - 1
    historical_after_reveal = evidence_pack(
        Harness.at(root, pre_reveal_seq), problem_id=problem_id
    )
    assert historical_after_reveal == before_reveal
    assert secret not in historical_after_reveal

    revealed = evidence_pack(Harness.at(root, reveal_seq), problem_id=problem_id)
    assert secret in revealed


@pytest.mark.parametrize("at_seq", [None, 0])
@pytest.mark.parametrize("output_kind", ["root", "nested", "symlink"])
def test_thesis_script_rejects_output_inside_read_only_run_before_adapter_call(
    tmp_path, monkeypatch, capsys, at_seq, output_kind
):
    h, _ids = _seed_root(tmp_path)
    before = _tree_snapshot(h.root)
    alias = tmp_path / "run-alias"
    if output_kind == "root":
        output = h.root
    elif output_kind == "nested":
        output = h.root / "uncreated" / "thesis.md"
    else:
        try:
            alias.symlink_to(h.root, target_is_directory=True)
        except OSError as error:
            pytest.skip(f"directory symlinks unavailable: {error}")
        output = alias / "thesis.md"

    monkeypatch.setattr(
        thesis_script,
        "load_config",
        lambda _path: SimpleNamespace(roles={"thesis": {}}),
    )
    monkeypatch.setattr(
        thesis_script, "apply_overrides", lambda config, _overrides: config
    )
    monkeypatch.setattr(
        thesis_script, "role_api_key_envs", lambda _config, _roles: set()
    )

    def adapter_must_not_run(*_args, **_kwargs):
        raise AssertionError("adapter construction must follow output validation")

    def model_must_not_run(*_args, **_kwargs):
        raise AssertionError("model call must follow output validation")

    monkeypatch.setattr(thesis_script, "build_adapter", adapter_must_not_run)
    monkeypatch.setattr(thesis_script, "thesis", model_must_not_run)

    argv = [
        "--root",
        str(h.root),
        "--problem",
        "pi-x",
        "--config",
        str(tmp_path / "unused.yaml"),
        "--out",
        str(output),
    ]
    if at_seq is not None:
        argv.extend(["--at-seq", str(at_seq)])

    assert thesis_script.main(argv) == 1
    assert "--out must be outside the read-only run root" in capsys.readouterr().err
    assert _tree_snapshot(h.root) == before


def test_adapter_sharing_run_blobs_is_rejected(tmp_path):
    h, ids = _seed_root(tmp_path)
    shared = LLMAdapter({"thesis": MockEndpoint([_valid_output(ids)])},
                        h.blobs, retry_max=2, meter=TokenMeter(budget=10**9))
    with pytest.raises(ValueError, match="read-only"):
        thesis(h, shared)
    with pytest.raises(ValueError, match="read-only"):
        thesis(Harness.at(h.root, h._next_seq - 1), shared)


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
