"""Bronze Flat v1 forensic reporting (repair plan phase F / phase G
report_census_matches_raw): the census parser is pinned to a hand-checked
fixture built from a retained v1 raw blob, census totals must reconcile
internally, and the offline nomic rescore artifact must carry per-item
values plus a complete embedder fingerprint."""

import hashlib
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from bronze_census import (  # noqa: E402
    RUNS_DIR,
    STREAMS,
    build_census,
    coerce_content,
    extract_candidates,
    lenient_json,
)

DEEPSEEK_ROOT = RUNS_DIR / "deepseek-v4-pro"
RESCORE_PATH = REPO / "experiments" / "results" / "bronze_flat_v1_nomic_rescore.json"

# Hand-checked fixture: the conjecturer call recorded as the conj-noregister
# Measure at seq 64 of the retained deepseek-v4-pro root. The raw blob was
# inspected by hand: it decodes to exactly three candidates whose content
# sha256 hashes and typicality values are pinned below. All three were
# gate-blocked (gate Measures at seq 59/61/63, problem pi-bronze).
FIXTURE_SEQ = 64
FIXTURE_RAW_REF = "1ba5ac52a9c9d83edc806dd0f1b837cf3203f4b44555dd607563287cc4fa2785"
FIXTURE_CANDIDATES = [
    ("a891e2c7fc0d388b650ad054ffd77b36ffe2402026eb711e52a113108dff3c7d", 0.7),
    ("22cd331be6e350709c099e90ed7557eb00de03b18c65240e13f73fb326fbd1a1", 0.8),
    ("f9d6a170ee4f3a80470f0ef50ce8153bd60ae496f8736e48b42ffab8ef547857", 0.3),
]

pytestmark = pytest.mark.skipif(
    not DEEPSEEK_ROOT.is_dir(), reason="retained bronze_flat_2026-07-13 roots absent"
)


@pytest.fixture(scope="module")
def census():
    return build_census()


def _fixture_event():
    for line in (DEEPSEEK_ROOT / "log.jsonl").open():
        event = json.loads(line)
        if event["seq"] == FIXTURE_SEQ:
            return event
    raise AssertionError(f"seq {FIXTURE_SEQ} not found in retained root")


def test_fixture_call_is_the_recorded_one():
    event = _fixture_event()
    assert event["rule"] == "Measure"
    assert event["inputs"] == ["conj-noregister"]
    assert event["llm"]["role"] == "conjecturer"
    assert event["llm"]["raw_ref"] == FIXTURE_RAW_REF


def test_census_parser_extracts_hand_verified_candidates():
    from deepreason.harness import Harness

    harness = Harness(str(DEEPSEEK_ROOT))
    raw = harness.blobs.get(FIXTURE_RAW_REF).decode("utf-8")
    parsed = lenient_json(raw)
    candidates, note = extract_candidates(parsed)
    assert note is None
    assert len(candidates) == len(FIXTURE_CANDIDATES)
    for cand, (sha, typicality) in zip(candidates, FIXTURE_CANDIDATES):
        content = coerce_content(cand["content"])
        assert isinstance(content, str)
        assert hashlib.sha256(content.encode("utf-8")).hexdigest() == sha
        assert cand["typicality"] == typicality


def test_census_rows_match_fixture(census):
    rows = [
        row
        for row in census["streams"]["deepseek-v4-pro"]["rows"]
        if row["seq"] == FIXTURE_SEQ and row["attempt"] is None
    ]
    assert [row["content_sha256"] for row in rows] == [
        sha for sha, _typ in FIXTURE_CANDIDATES
    ]
    for row in rows:
        assert row["disposition"] == "gate-blocked"
        assert row["schema_valid"] is True
        assert row["problem"] == "pi-bronze"


def test_census_totals_internally_consistent(census):
    for stream in STREAMS:
        counts = census["streams"][stream]["counts"]
        assert counts["emitted"] >= counts["registered"] + counts["gate_blocked"]
        assert counts["emitted"] == sum(
            value for key, value in counts.items() if key != "emitted"
        )
        coverage = census["streams"][stream]["coverage"]
        assert 0.0 <= coverage <= 1.0
        # Every gate Measure in the root must land on exactly one row.
        assert counts["gate_blocked"] == census["streams"][stream]["gate_measures"]
    assert 0.0 <= census["coverage"] <= 1.0
    assert census["totals"]["emitted"] == sum(
        census["streams"][s]["counts"]["emitted"] for s in STREAMS
    )


def test_census_rows_carry_required_fields(census):
    for stream in STREAMS:
        for row in census["streams"][stream]["rows"]:
            assert row["stream"] == stream
            assert isinstance(row["seq"], int)
            assert row["disposition"] is not None
            assert row["join_method"] is not None
            assert "content_sha256" in row and "typicality" in row
            assert isinstance(row["schema_valid"], bool)


def test_refuted_adjudication_paths_present(census):
    for stream in STREAMS:
        adjudication = census["streams"][stream]["refuted_adjudication"]
        conjecturer_paths = [
            entry["adjudication_path"]
            for entry in adjudication.values()
            if entry["role"] == "conjecturer"
        ]
        assert conjecturer_paths, f"no refuted conjectures classified in {stream}"
        for path in conjecturer_paths:
            assert path in ("direct-argumentative", "program") or path.startswith(
                "mixed:"
            )


@pytest.mark.skipif(
    not RESCORE_PATH.is_file(),
    reason="rescore artifact not generated (requires local nomic model files)",
)
def test_rescore_covers_registered_substantive_conjectures():
    from bronze_nomic_rescore import is_substantive, registered_conjectures

    rescore = json.loads(RESCORE_PATH.read_text())
    fingerprint = rescore["embedder_fingerprint"]
    for field in ("model", "version", "sentinel", "embedding_dim", "name"):
        assert fingerprint.get(field), f"fingerprint missing {field}"
    assert fingerprint["model"] == "nomic-ai/nomic-embed-text-v1.5"
    for stream in STREAMS:
        substantive = {
            aid
            for aid, content in registered_conjectures(stream).items()
            if is_substantive(content)
        }
        stream_data = rescore["streams"][stream]
        assert set(stream_data["registered_substantive"]) == substantive
        per_item = stream_data["registered_to_first_refuted"]
        assert set(per_item) == substantive
        for value in per_item.values():
            assert isinstance(value, float) and 0.0 <= value <= 2.0
        expected_pairs = len(substantive) * (len(substantive) - 1) // 2
        assert len(stream_data["registered_pairwise"]) == expected_pairs
    assert rescore["calibration_reference"]["paraphrase_margin"] == 0.19
    assert rescore["calibration_reference"]["unrelated"] == 0.60
