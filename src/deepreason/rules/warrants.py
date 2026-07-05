"""Shared demonstrative fail-warrant package (spec §2/§3).

Six sites used to hand-build the same triple — attackable validity node ν,
DEMONSTRATIVE fail warrant (`w:<commitment>:<target>`), critic artifact
carrying it — with the duplicate-verdict guard present at only some of
them. The id scheme, the ν/critic wiring, and the guard predicate are
load-bearing for adjudication and the audit machinery, so they live here
exactly once. Every site passes its own ν wording, critic wording, and
trace payload unchanged — the helper is plumbing, not policy.
"""

from deepreason.ontology import Artifact, Interface, Provenance, Rule, Warrant, WarrantType


def verdict_on_record(harness, commitment_id: str, target_id: str) -> bool:
    """The §3 duplicate-verdict guard: one (κ, target) fail verdict on the
    graph at a time — re-registration would double-register critics."""
    return any(
        w.commitment == commitment_id and w.target == target_id
        for w in harness.warrants.values()
    )


def register_fail_warrant(
    harness,
    *,
    commitment_id: str,
    target_id: str,
    nu_content: str,
    critic_content: str,
    trace_ref: str,
    nu_interface: Interface | None = None,
    warrant_id: str | None = None,
    llm=None,
    skip_if_on_record: bool = False,
) -> Artifact | None:
    """Register ν + DEMONSTRATIVE fail warrant + critic; returns the critic
    (None when skip_if_on_record and the verdict is already on the graph)."""
    if skip_if_on_record and verdict_on_record(harness, commitment_id, target_id):
        return None
    nu = harness.create_artifact(
        nu_content,
        interface=nu_interface,
        provenance=Provenance(role="critic"),
    )
    warrant = Warrant(
        id=warrant_id or f"w:{commitment_id}:{target_id}",
        target=target_id,
        type=WarrantType.DEMONSTRATIVE,
        commitment=commitment_id,
        verdict="fail",
        trace_ref=trace_ref,
        validity_node=nu.id,
    )
    return harness.create_artifact(
        critic_content,
        provenance=Provenance(role="critic"),
        warrants=[warrant],
        rule=Rule.CRIT,
        llm=llm,
    )
