"""Standards as case law (spec §10.3).

Every rubric:<spec-id> resolves to a registered STANDARD artifact: rubric
text, evaluation mode (absolute | anchored | pairwise), and mention refs to
exemplars/anchors. Standards are ordinary artifacts — attackable,
reinstateable, succeedable. Precedents accrete by reference: no mutation.
The closure extension (§1) is the teeth: the productive attack in informal
domains usually lands on the standard, not the work — and when it lands,
every verdict issued under it falls and every target reinstates, computed
in pass 1 (parallel fifths, as a theorem of the graph).
"""

import json

from deepreason.ontology import Artifact, Interface, Provenance, Ref, Rule, Status
from deepreason.programs import content_text


def register_standard(
    harness,
    spec_id: str,
    rubric: str,
    mode: str = "absolute",
    exemplars: list[str] = (),
    anchors: list[str] = (),
) -> Artifact:
    """mode: absolute | anchored | pairwise. anchors = known-bad exemplar
    artifact ids for anchored mode (§10.2)."""
    assert mode in ("absolute", "anchored", "pairwise")
    body = {"standard": {"spec": spec_id, "mode": mode, "rubric": rubric}}
    if anchors:
        body["standard"]["anchors"] = list(anchors)
    refs = [
        Ref(target=e, role="mention")
        for e in [*exemplars, *anchors]
        if e in harness.state.artifacts
    ]
    return harness.create_artifact(
        json.dumps(body, sort_keys=True),
        codec="json",
        interface=Interface(refs=refs),
        provenance=Provenance(role="seed"),
        rule=Rule.REFL,
    )


def _body(artifact: Artifact, harness) -> dict | None:
    if artifact.codec != "json":
        return None
    try:
        data = json.loads(content_text(artifact, harness.blobs))
    except ValueError:
        return None
    body = data.get("standard") if isinstance(data, dict) else None
    return body if isinstance(body, dict) and "spec" in body else None


def resolve_standard(harness, spec_id: str) -> Artifact | None:
    """Latest registered standard declaring spec_id (event order)."""
    found = None
    for artifact in harness.state.artifacts.values():
        body = _body(artifact, harness)
        if body is not None and body["spec"] == spec_id:
            found = artifact
    return found


def standard_body(harness, artifact: Artifact) -> dict:
    body = _body(artifact, harness)
    if body is None:
        raise ValueError(f"{artifact.id[:12]} is not a standard artifact")
    return body


def precedent_slice(harness, standard_id: str, k: int) -> list[dict]:
    """Top-k ACCEPTED precedents citing the standard, user rulings ranked
    first (§10.6) — a deterministic query; pack ordering is the only
    authority a user ruling has (N1: never status privilege)."""
    hits: list[tuple[int, int, dict]] = []
    for order, (aid, artifact) in enumerate(harness.state.artifacts.items()):
        if harness.state.status.get(aid) != Status.ACCEPTED:
            continue
        if not any(
            r.target == standard_id and r.role.value == "mention"
            for r in artifact.interface.refs
        ):
            continue
        try:
            data = json.loads(content_text(artifact, harness.blobs))
        except ValueError:
            continue
        precedent = data.get("precedent") if isinstance(data, dict) else None
        if not isinstance(precedent, dict):
            continue
        is_user = artifact.provenance.role.value == "user"
        hits.append(
            (0 if is_user else 1, order,
             {"id": aid, "holding": precedent.get("holding", ""), "user": is_user})
        )
    return [item for _, _, item in sorted(hits, key=lambda t: (t[0], t[1]))][:k]
