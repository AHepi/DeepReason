"""Directed web research: allowlisted, requests-budgeted, receipted.

The two owner decisions under test: fetches are confined to a frozen
per-run domain allowlist (https only, every redirect hop re-validated),
and the fetch budget is denominated in dispatched requests with typed
exhaustion carrying count and limit — the shape grounded by the
2026-07-27 campaign's ANSWERED resolution.
"""

from __future__ import annotations

import hashlib

import pytest

from deepreason.research.fetch import (
    FETCHED,
    RESEARCH_BUDGET_EXHAUSTED,
    RESEARCH_DOMAIN_NOT_ALLOWED,
    RESEARCH_FETCH_FAILED,
    RESEARCH_MEDIA_UNSUPPORTED,
    RESEARCH_RESPONSE_TOO_LARGE,
    RESEARCH_SCHEME_NOT_ALLOWED,
    ContainedFetcher,
    WebResearchConfigV1,
    html_to_text,
    load_web_config,
)


CONFIG = WebResearchConfigV1(
    domain_allowlist=("example.org", "data.example.net"),
    maximum_requests=3,
    maximum_response_bytes=4_096,
)

PAGE = b"<html><body><h1>Tides</h1><p>The moon pulls the sea.</p><script>x()</script></body></html>"


def _transport(script):
    """script: url -> (status, content_type, location, body) or Exception."""

    calls = []

    def transport(url, timeout, maximum_bytes):
        calls.append(url)
        entry = script[url]
        if isinstance(entry, Exception):
            raise entry
        return entry

    transport.calls = calls
    return transport


def test_allowlist_confines_fetches_without_spending_requests():
    fetcher = ContainedFetcher(CONFIG, transport=_transport({}))
    for url, refusal in (
        ("http://example.org/x", RESEARCH_SCHEME_NOT_ALLOWED),
        ("https://evil.example.com/x", RESEARCH_DOMAIN_NOT_ALLOWED),
        ("https://example.org.evil.com/x", RESEARCH_DOMAIN_NOT_ALLOWED),
    ):
        outcome = fetcher.fetch(url)
        assert outcome.receipt.outcome == refusal
        assert outcome.text is None
    # Validation refusals never touched the network and spent nothing.
    assert fetcher.requests_used == 0
    # Subdomains of an allowlisted domain are implied.
    assert CONFIG.allows("sub.example.org") and not CONFIG.allows("example.com")


def test_fetch_extracts_text_and_mints_a_content_addressed_receipt():
    transport = _transport(
        {"https://example.org/tides": (200, "text/html; charset=utf-8", None, PAGE)}
    )
    fetcher = ContainedFetcher(CONFIG, transport=transport)
    outcome = fetcher.fetch("https://example.org/tides")
    assert outcome.receipt.outcome == FETCHED
    assert outcome.text == "Tides\nThe moon pulls the sea."
    assert outcome.receipt.content_sha256 == hashlib.sha256(PAGE).hexdigest()
    assert outcome.receipt.requests_used == 1
    assert outcome.receipt.requests_limit == 3


def test_redirect_hops_are_revalidated_and_each_spends_one_request():
    transport = _transport(
        {
            "https://example.org/a": (302, "", "https://data.example.net/b", b""),
            "https://data.example.net/b": (200, "text/plain", None, b"payload"),
            "https://example.org/leak": (302, "", "https://evil.example.com/x", b""),
        }
    )
    fetcher = ContainedFetcher(CONFIG, transport=transport)
    outcome = fetcher.fetch("https://example.org/a")
    assert outcome.receipt.outcome == FETCHED and outcome.text == "payload"
    assert outcome.final_url == "https://data.example.net/b"
    assert fetcher.requests_used == 2  # both hops dispatched

    escape = fetcher.fetch("https://example.org/leak")
    # The redirect target is validated BEFORE dispatch: the off-allowlist
    # hop is refused, and only the first (allowlisted) round-trip spent.
    assert escape.receipt.outcome == RESEARCH_DOMAIN_NOT_ALLOWED
    assert fetcher.requests_used == 3
    assert "evil.example.com" not in transport.calls[-1]


def test_budget_exhaustion_is_typed_and_carries_count_and_limit():
    transport = _transport(
        {"https://example.org/x": (200, "text/plain", None, b"ok")}
    )
    fetcher = ContainedFetcher(CONFIG, transport=transport)
    for _ in range(3):
        assert fetcher.fetch("https://example.org/x").receipt.outcome == FETCHED
    refused = fetcher.fetch("https://example.org/x")
    assert refused.receipt.outcome == RESEARCH_BUDGET_EXHAUSTED
    assert refused.receipt.requests_used == 3
    assert refused.receipt.requests_limit == 3
    assert len(transport.calls) == 3  # nothing dispatched after exhaustion


def test_oversize_media_and_failure_outcomes_are_typed_and_spent():
    transport = _transport(
        {
            "https://example.org/big": (200, "text/plain", None, b"x" * 5_000),
            "https://example.org/pdf": (200, "application/pdf", None, b"%PDF-"),
            "https://example.org/down": OSError("connection refused"),
        }
    )
    fetcher = ContainedFetcher(CONFIG, transport=transport)
    assert fetcher.fetch("https://example.org/big").receipt.outcome == (
        RESEARCH_RESPONSE_TOO_LARGE
    )
    assert fetcher.fetch("https://example.org/pdf").receipt.outcome == (
        RESEARCH_MEDIA_UNSUPPORTED
    )
    assert fetcher.fetch("https://example.org/down").receipt.outcome == (
        RESEARCH_FETCH_FAILED
    )
    assert fetcher.requests_used == 3  # every dispatched attempt spends


def test_web_config_loads_loudly_and_rejects_widening_shapes(tmp_path):
    good = tmp_path / "web.yaml"
    good.write_text(
        "domain_allowlist: [example.org]\nmaximum_requests: 10\n"
    )
    config = load_web_config(good)
    assert config.maximum_requests == 10

    with pytest.raises(ValueError, match="not found"):
        load_web_config(tmp_path / "missing.yaml")
    bad = tmp_path / "bad.yaml"
    bad.write_text("domain_allowlist: ['*.example.org']\nmaximum_requests: 10\n")
    with pytest.raises(ValueError, match="invalid"):
        load_web_config(bad)


def test_directed_backend_registers_receipted_evidence(tmp_path):
    from deepreason.harness import Harness
    from deepreason.ontology import Commitment, Problem, ProblemProvenance
    from deepreason.research.backends import WebBackend, run_research

    transport = _transport(
        {"https://example.org/tides": (200, "text/html", None, PAGE)}
    )
    backend = WebBackend(CONFIG, transport=transport)

    harness = Harness(tmp_path / "run")
    harness.register_commitment(
        Commitment(id="k-tide-tables", eval="predicate:True", observation_valued=True)
    )
    problem = harness.register_problem(
        Problem(
            id="research:tides",
            description=(
                "find the published tide mechanism at "
                "https://example.org/tides before concluding"
            ),
            criteria=["k-tide-tables"],
            provenance=ProblemProvenance.model_validate(
                {"trigger": "research", "from": []}
            ),
        )
    )
    evidence = run_research(harness, problem, backend)
    assert evidence is not None
    assert "moon pulls the sea" in str(
        harness.blobs.get(evidence.content_ref)
        if not evidence.content_ref.startswith("inline:")
        else evidence.content_ref
    )
    # The reliability node carries the fetch provenance claim — attackable.
    reliability_ref = next(
        ref.target for ref in evidence.interface.refs if ref.role == "dependence"
    )
    reliability = harness.state.artifacts[reliability_ref]
    assert "https://example.org/tides" in reliability.content_ref
    assert hashlib.sha256(PAGE).hexdigest()[:16] in reliability.content_ref

    # Every fetch attempt reached the append-only log as a measure.
    fetch_events = [
        event
        for event in harness.log.read()
        if event.inputs and str(event.inputs[0]).startswith("research-fetch:")
    ]
    assert [event.inputs[0] for event in fetch_events] == ["research-fetch:FETCHED"]
    assert fetch_events[0].inputs[2] == "requests:1/3"

    # A directed miss (no URL in the description) spends nothing and
    # registers nothing.
    plain = harness.register_problem(
        Problem(
            id="research:plain",
            description="find corroborating tide tables",
            criteria=["k-tide-tables"],
            provenance=ProblemProvenance.model_validate(
                {"trigger": "research", "from": []}
            ),
        )
    )
    assert run_research(harness, plain, backend) is None
    assert backend.fetcher.requests_used == 1


def test_web_mode_wires_through_build_service(tmp_path):
    from deepreason.config import Config
    from deepreason.research.backends import build_service

    config_path = tmp_path / "web.yaml"
    config_path.write_text(
        "domain_allowlist: [example.org]\nmaximum_requests: 5\n"
    )
    service = build_service(
        Config(RESEARCH_BACKEND=f"web:{config_path}")
    )
    assert service.mode == "web" and service.internal
    assert service.fetcher.fetcher.config.maximum_requests == 5


def test_html_extraction_is_deterministic_and_script_free():
    assert html_to_text(PAGE) == "Tides\nThe moon pulls the sea."
    assert html_to_text(b"<p>a</p><script>evil()</script><p>b</p>") == "a\nb"
