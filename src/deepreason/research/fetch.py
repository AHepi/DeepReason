"""The contained web fetcher for directed research (owner decisions realized).

Two long-parked decisions land here, one grounded by live campaign
evidence and one by the harness's own containment doctrine:

1. **Per-run domain allowlist over open web.** A fetch may target only a
   host on the frozen allowlist (exact match or subdomain), https only,
   with every redirect hop re-validated. Where the run may look is part
   of what the run *is*.
2. **Requests-denominated fetch budget with a typed exhaustion record.**
   The 2026-07-27 campaign's grounded ANSWERED resolution: budgets count
   dispatched requests (every network round-trip spends one, including
   redirect hops and failures); exhaustion is a typed, auditable record
   carrying both the count and the limit — never a silent degradation.
   A per-response byte ceiling is containment, not a budget: it bounds
   any single response without changing the budget's denomination.

Every fetch attempt — success, refusal, failure, exhaustion — mints a
receipt. Refusals that never touch the network (bad scheme, host off the
allowlist, exhausted budget) spend nothing; everything dispatched spends.
"""

from __future__ import annotations

import hashlib
from html.parser import HTMLParser
from pathlib import Path
from typing import Callable, Literal
from urllib.parse import urlparse

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

FETCHED = "FETCHED"
RESEARCH_SCHEME_NOT_ALLOWED = "RESEARCH_SCHEME_NOT_ALLOWED"
RESEARCH_DOMAIN_NOT_ALLOWED = "RESEARCH_DOMAIN_NOT_ALLOWED"
RESEARCH_BUDGET_EXHAUSTED = "RESEARCH_BUDGET_EXHAUSTED"
RESEARCH_FETCH_FAILED = "RESEARCH_FETCH_FAILED"
RESEARCH_RESPONSE_TOO_LARGE = "RESEARCH_RESPONSE_TOO_LARGE"
RESEARCH_MEDIA_UNSUPPORTED = "RESEARCH_MEDIA_UNSUPPORTED"
RESEARCH_REDIRECT_LIMIT = "RESEARCH_REDIRECT_LIMIT"

_MAX_REDIRECT_HOPS = 5


class WebResearchConfigV1(BaseModel):
    """Frozen containment authority for one web research backend."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    domain_allowlist: tuple[str, ...] = Field(min_length=1, max_length=64)
    maximum_requests: int = Field(ge=1, le=1_000)
    maximum_response_bytes: int = Field(
        default=2 * 1024 * 1024, ge=1_024, le=16 * 1024 * 1024
    )
    timeout_seconds: int = Field(default=30, ge=1, le=300)

    @field_validator("domain_allowlist")
    @classmethod
    def _plain_lowercase_hosts(cls, value):
        for domain in value:
            if (
                not domain
                or domain != domain.strip().lower()
                or domain.startswith(".")
                or "/" in domain
                or ":" in domain
                or "*" in domain
            ):
                raise ValueError(
                    "allowlist entries must be bare lowercase hostnames "
                    "(subdomains are implied; no schemes, ports, or wildcards)"
                )
        return tuple(value)

    def allows(self, host: str) -> bool:
        host = host.lower().rstrip(".")
        return any(
            host == domain or host.endswith("." + domain)
            for domain in self.domain_allowlist
        )


def load_web_config(path: str | Path) -> WebResearchConfigV1:
    """Load a web research config file (YAML/JSON). Fails loudly — a
    malformed containment authority must never silently widen."""

    target = Path(path)
    if not target.exists():
        raise ValueError(f"RESEARCH_BACKEND web config not found: {path}")
    try:
        return WebResearchConfigV1.model_validate(
            dict(yaml.safe_load(target.read_text()))
        )
    except (ValueError, TypeError, yaml.YAMLError) as error:
        raise ValueError(
            f"RESEARCH_BACKEND web config {path} is invalid: {error}"
        ) from error


class FetchReceiptV1(BaseModel):
    """One durable, sanitized record of one fetch attempt."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_: Literal["research-fetch-receipt.v1"] = Field(
        "research-fetch-receipt.v1", alias="schema"
    )
    seq: int = Field(ge=1)
    url: str = Field(min_length=1, max_length=4_096)
    host: str = Field(default="", max_length=1_024)
    outcome: Literal[
        "FETCHED",
        "RESEARCH_SCHEME_NOT_ALLOWED",
        "RESEARCH_DOMAIN_NOT_ALLOWED",
        "RESEARCH_BUDGET_EXHAUSTED",
        "RESEARCH_FETCH_FAILED",
        "RESEARCH_RESPONSE_TOO_LARGE",
        "RESEARCH_MEDIA_UNSUPPORTED",
        "RESEARCH_REDIRECT_LIMIT",
    ]
    http_status: int | None = Field(default=None, ge=100, le=599)
    byte_count: int = Field(default=0, ge=0)
    content_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    # The grounded exhaustion shape: the typed record carries both the
    # running count and the frozen limit, always.
    requests_used: int = Field(ge=0)
    requests_limit: int = Field(ge=1)


class FetchOutcome(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    receipt: FetchReceiptV1
    text: str | None = None
    final_url: str | None = None


class _TextCollector(HTMLParser):
    """Deterministic text extraction (same discipline as the EPUB adapter)."""

    _BREAK = frozenset(
        {"p", "div", "li", "br", "tr", "section", "article", "blockquote",
         "h1", "h2", "h3", "h4", "h5", "h6"}
    )

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.pieces: list[str] = []
        self._suppressed = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self._suppressed += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style"} and self._suppressed:
            self._suppressed -= 1
        if tag in self._BREAK:
            self.pieces.append("\n")

    def handle_data(self, data):
        if not self._suppressed:
            self.pieces.append(data)

    def text(self) -> str:
        lines = "".join(self.pieces).splitlines()
        collapsed = [" ".join(line.split()) for line in lines]
        return "\n".join(line for line in collapsed if line)


def html_to_text(body: bytes) -> str:
    collector = _TextCollector()
    collector.feed(body.decode("utf-8", errors="replace"))
    return collector.text().strip()


# transport(url, timeout, maximum_bytes) -> (status, content_type, location, body)
Transport = Callable[[str, int, int], tuple[int, str, str | None, bytes]]


def _urllib_transport(
    url: str, timeout: int, maximum_bytes: int
) -> tuple[int, str, str | None, bytes]:
    import urllib.request

    request = urllib.request.Request(
        url,
        headers={"User-Agent": "deepreason-research/0.1"},
    )

    class _NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None  # redirects are validated hop-by-hop by the fetcher

    opener = urllib.request.build_opener(_NoRedirect)
    try:
        with opener.open(request, timeout=timeout) as response:
            body = response.read(maximum_bytes + 1)
            return (
                response.status,
                response.headers.get("Content-Type", ""),
                None,
                body,
            )
    except urllib.error.HTTPError as error:
        if error.code in (301, 302, 303, 307, 308):
            return (
                error.code,
                error.headers.get("Content-Type", ""),
                error.headers.get("Location"),
                b"",
            )
        raise


class ContainedFetcher:
    """Allowlisted, budgeted, receipted fetch execution."""

    def __init__(
        self,
        config: WebResearchConfigV1,
        *,
        transport: Transport | None = None,
    ) -> None:
        self.config = config
        self.transport = transport or _urllib_transport
        self.requests_used = 0
        self.receipts: list[FetchReceiptV1] = []

    def _receipt(self, url: str, host: str, outcome: str, **fields) -> FetchReceiptV1:
        receipt = FetchReceiptV1(
            seq=len(self.receipts) + 1,
            url=url[:4_096],
            host=host[:1_024],
            outcome=outcome,
            requests_used=self.requests_used,
            requests_limit=self.config.maximum_requests,
            **fields,
        )
        self.receipts.append(receipt)
        return receipt

    def drain_receipts(self) -> tuple[FetchReceiptV1, ...]:
        drained = tuple(self.receipts)
        self.receipts = []
        return drained

    @property
    def exhausted(self) -> bool:
        return self.requests_used >= self.config.maximum_requests

    def _validate(self, url: str) -> tuple[str, str | None]:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        if parsed.scheme != "https":
            return host, RESEARCH_SCHEME_NOT_ALLOWED
        if not host or not self.config.allows(host):
            return host, RESEARCH_DOMAIN_NOT_ALLOWED
        return host, None

    def fetch(self, url: str) -> FetchOutcome:
        """Fetch one allowlisted https URL, following bounded validated
        redirects. Validation refusals spend nothing; every dispatched
        round-trip (including each redirect hop and every failure that
        reached the network) spends exactly one request."""

        current = url
        for _hop in range(_MAX_REDIRECT_HOPS + 1):
            host, refusal = self._validate(current)
            if refusal is not None:
                return FetchOutcome(receipt=self._receipt(current, host, refusal))
            if self.exhausted:
                # The grounded shape: typed, auditable, carries count+limit.
                return FetchOutcome(
                    receipt=self._receipt(current, host, RESEARCH_BUDGET_EXHAUSTED)
                )
            self.requests_used += 1
            try:
                status, content_type, location, body = self.transport(
                    current,
                    self.config.timeout_seconds,
                    self.config.maximum_response_bytes,
                )
            except Exception:  # noqa: BLE001 - sanitized typed failure
                return FetchOutcome(
                    receipt=self._receipt(current, host, RESEARCH_FETCH_FAILED)
                )
            if location is not None:
                current = location
                continue
            if status != 200:
                return FetchOutcome(
                    receipt=self._receipt(
                        current, host, RESEARCH_FETCH_FAILED, http_status=status
                    )
                )
            if len(body) > self.config.maximum_response_bytes:
                return FetchOutcome(
                    receipt=self._receipt(
                        current,
                        host,
                        RESEARCH_RESPONSE_TOO_LARGE,
                        http_status=status,
                        byte_count=len(body),
                    )
                )
            media = content_type.split(";")[0].strip().lower()
            if media in ("text/html", "application/xhtml+xml"):
                text = html_to_text(body)
            elif media.startswith("text/") or media in (
                "application/json",
                "",
            ):
                text = body.decode("utf-8", errors="replace").strip()
            else:
                return FetchOutcome(
                    receipt=self._receipt(
                        current,
                        host,
                        RESEARCH_MEDIA_UNSUPPORTED,
                        http_status=status,
                        byte_count=len(body),
                    )
                )
            return FetchOutcome(
                receipt=self._receipt(
                    current,
                    host,
                    FETCHED,
                    http_status=status,
                    byte_count=len(body),
                    content_sha256=hashlib.sha256(body).hexdigest(),
                ),
                text=text,
                final_url=current,
            )
        return FetchOutcome(
            receipt=self._receipt(current, host, RESEARCH_REDIRECT_LIMIT)
        )


__all__ = [
    "FETCHED",
    "RESEARCH_BUDGET_EXHAUSTED",
    "RESEARCH_DOMAIN_NOT_ALLOWED",
    "RESEARCH_FETCH_FAILED",
    "RESEARCH_MEDIA_UNSUPPORTED",
    "RESEARCH_REDIRECT_LIMIT",
    "RESEARCH_RESPONSE_TOO_LARGE",
    "RESEARCH_SCHEME_NOT_ALLOWED",
    "ContainedFetcher",
    "FetchOutcome",
    "FetchReceiptV1",
    "WebResearchConfigV1",
    "html_to_text",
    "load_web_config",
]
