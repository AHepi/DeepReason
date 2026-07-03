"""Shared builders for P0 acceptance tests (spec §16)."""

import pytest

from deepreason.harness import Harness
from deepreason.ontology import Interface, Provenance, Warrant, WarrantType


@pytest.fixture
def harness(tmp_path) -> Harness:
    return Harness(tmp_path / "run")


def art(harness: Harness, text: str, *, interface: Interface | None = None, **kwargs):
    return harness.create_artifact(
        text,
        interface=interface,
        provenance=kwargs.pop("provenance", Provenance(role="seed")),
        **kwargs,
    )


def attack(harness: Harness, target_id: str, note: str, *, warrant_kwargs: dict | None = None):
    """Register nu + a critic artifact carrying a warrant against target."""
    nu = art(harness, f"nu: the attack '{note}' is sound and relevant")
    warrant = Warrant(
        id=f"w-{note}",
        target=target_id,
        type=WarrantType.ARGUMENTATIVE,
        validity_node=nu.id,
        **(warrant_kwargs or {}),
    )
    critic = harness.create_artifact(
        f"critic: {note}",
        provenance=Provenance(role="critic"),
        warrants=[warrant],
    )
    return critic, nu
