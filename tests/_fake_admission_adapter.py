"""A minimal third-party-shaped adapter used by the §3a contract tests."""

from deepreason.admission.adapters import (
    AdapterBlockWireV1,
    AdapterManifestV1,
    AdapterResultWireV1,
)

MANIFEST = AdapterManifestV1(
    adapter_id="fake-binary",
    adapter_version="fake-adapter.v1",
    content_signatures=("46414b45",),  # b"FAKE"
    media_type="application/x-fake",
    span_fidelity="approximate",
    requires=None,
    extra_hint="tests only",
    entry="tests._fake_admission_adapter:extract",
)


def extract(data: bytes) -> AdapterResultWireV1:
    body = data[4:].decode("utf-8", errors="replace") or "empty payload"
    return AdapterResultWireV1(
        adapter_id="fake-binary",
        adapter_version="fake-adapter.v1",
        blocks=(
            AdapterBlockWireV1(text=body, title="decoded"),
            AdapterBlockWireV1(text=f"{len(data)} bytes total", title="size"),
        ),
    )


def phone_home(data: bytes):
    """A hostile adapter: tries the network; the sandbox must refuse it."""

    import socket

    socket.create_connection(("203.0.113.1", 80), timeout=5)
