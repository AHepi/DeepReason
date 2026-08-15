"""The premise channel — how a PROBLEM becomes criticisable (v2 Rung 2).

A problem is not an artifact and never enters ``att``/``dep``: nothing here can
attack a problem directly. What is criticised is what the problem takes for
granted, and the problem's consequence is a MARK, not a label.

Three ordinary artifacts and one derived predicate:

- the **premise** X — the claim the problem takes for granted. Ordinary
  artifact, ordinary commitments, refuted the ordinary way.
- the **attribution** rho — an ordinary artifact whose content says "problem pi
  has premise X". It ``mention``s X and MUST NOT ``dependence``-ref it (Law
  9.4', the mention law generalised): if it depended on X, refuting X would drag
  rho to suspended_unsupported and the cascade would disarm itself at exactly
  the moment it is needed.
- the **resolution** — retire / translate / independence, each a registered
  artifact and therefore attackable, which is what makes every step reversible
  (N1) and keeps retirement from being an insolubility verdict (N3).

Nothing is a type. An artifact is an attribution because it carries the
``program:presupposition_wf`` commitment (C3: dispatch on interface structure),
and both are ordinary registered artifacts, hence attackable (P6).

Two locks, deliberately: filing an attribution moves nothing on its own, and
refuting a premise moves nothing on its own. A problem is marked only when the
attribution stands AND the premise has fallen -- and even then the mark is not a
refutation of the problem, only an open question with three legal answers.
"""

from __future__ import annotations

import json

from deepreason.ontology import Status
from deepreason.programs import content_text

ATTRIBUTION_EVAL = "program:presupposition_wf"
RESOLUTION_EVAL = "program:premise_resolution_wf"

RESOLUTIONS = ("retire", "translate", "independence")

# Cascade grades (calculus 9.8). The distinction is inherited from the premise's
# own label and is never stored on the problem.
PREMISE_REFUTED = "premise-refuted"          # the premise was shown wrong
PREMISE_UNACCREDITED = "premise-unaccredited"  # the premise lost its support


def attribution_content(problem_id: str, premise_id: str) -> str:
    """Canonical content for an attribution artifact."""
    return json.dumps(
        {"problem": problem_id, "premise": premise_id}, sort_keys=True
    )


def resolution_content(
    resolution: str, problem_id: str, *, successor: str | None = None
) -> str:
    """Canonical content for one orphan resolution."""
    if resolution not in RESOLUTIONS:
        raise ValueError(f"unknown resolution: {resolution!r}")
    body: dict[str, str] = {"resolution": resolution, "problem": problem_id}
    if successor is not None:
        body["successor"] = successor
    return json.dumps(body, sort_keys=True)


def _refs(artifact, role: str) -> set[str]:
    return {r.target for r in artifact.interface.refs if r.role.value == role}


def presupposition_wf_program(text: str, budget, artifact=None) -> tuple[str, dict]:
    """PASS iff the artifact is a well-formed attribution.

    Checks the mention law itself, because the law is the whole separation: an
    attribution that DEPENDS on its premise would fall with it, and a cascade
    whose trigger falls with its own cause never fires.
    """
    try:
        body = json.loads(text)
    except Exception:  # noqa: BLE001 - unparseable content is a failed verdict
        return "fail", {"reason": "attribution content is not JSON"}
    if not isinstance(body, dict):
        return "fail", {"reason": "attribution content is not an object"}
    problem_id, premise_id = body.get("problem"), body.get("premise")
    if not isinstance(problem_id, str) or not problem_id:
        return "fail", {"reason": "attribution names no problem"}
    if not isinstance(premise_id, str) or not premise_id:
        return "fail", {"reason": "attribution names no premise"}
    if artifact is None:
        return "fail", {"reason": "attribution requires its own interface"}
    if premise_id in _refs(artifact, "dependence"):
        return "fail", {
            "reason": "mention law: an attribution must not depend on its premise",
            "premise": premise_id,
        }
    if premise_id not in _refs(artifact, "mention"):
        return "fail", {
            "reason": "attribution must mention the premise it names",
            "premise": premise_id,
        }
    return "pass", {"problem": problem_id, "premise": premise_id}


def premise_resolution_wf_program(text: str, budget, artifact=None) -> tuple[str, dict]:
    """PASS iff the artifact is a well-formed orphan resolution."""
    try:
        body = json.loads(text)
    except Exception:  # noqa: BLE001
        return "fail", {"reason": "resolution content is not JSON"}
    if not isinstance(body, dict):
        return "fail", {"reason": "resolution content is not an object"}
    resolution = body.get("resolution")
    if resolution not in RESOLUTIONS:
        return "fail", {"reason": f"unknown resolution: {resolution!r}"}
    if not isinstance(body.get("problem"), str) or not body["problem"]:
        return "fail", {"reason": "resolution names no problem"}
    if resolution == "translate" and not body.get("successor"):
        return "fail", {"reason": "translate must name its successor problem"}
    return "pass", dict(body)


def _carrying(harness, eval_name: str):
    """Artifacts carrying a commitment with this eval, with their parsed body.

    Recognition is by INTERFACE STRUCTURE, never by a kind field (C3).
    """
    out = []
    for artifact in harness.state.artifacts.values():
        for cid in artifact.interface.commitments:
            kappa = harness.commitments.get(cid)
            if kappa is None or kappa.eval != eval_name:
                continue
            try:
                body = json.loads(content_text(artifact, harness.blobs))
            except Exception:  # noqa: BLE001
                break
            if isinstance(body, dict):
                out.append((artifact, body))
            break
    return out


def standing_attributions(harness) -> list[tuple[str, str, str]]:
    """(attribution id, problem id, premise id) for every CONSULTED attribution.

    Consulted means unrefuted: an attribution someone has successfully attacked
    ("the problem never assumed that") stops counting, which is how a problem is
    released without anyone having to rescue the premise.
    """
    consulted = []
    for artifact, body in _carrying(harness, ATTRIBUTION_EVAL):
        if harness.state.status.get(artifact.id) != Status.ACCEPTED:
            continue
        problem_id, premise_id = body.get("problem"), body.get("premise")
        if isinstance(problem_id, str) and isinstance(premise_id, str):
            consulted.append((artifact.id, problem_id, premise_id))
    return sorted(consulted)


def standing_resolutions(harness) -> dict[str, dict]:
    """problem id -> the parsed body of its CONSULTED resolution, if any.

    A resolution that has itself been refuted stops counting, so attacking a
    retirement returns its problem to the frontier (N1). Nothing is deleted:
    the refuted resolution stays in the record (P8).
    """
    out: dict[str, dict] = {}
    for artifact, body in _carrying(harness, RESOLUTION_EVAL):
        if harness.state.status.get(artifact.id) != Status.ACCEPTED:
            continue
        problem_id = body.get("problem")
        if isinstance(problem_id, str):
            out.setdefault(problem_id, dict(body))
    return out


def premise_orphaned(harness) -> dict[str, str]:
    """problem id -> grade, for every problem whose premise has fallen.

    DERIVED, never stored (C4): a pure function of replayed state, recomputed on
    demand. That is also what makes the cascade LAZY -- a fall over a thousand
    problems costs nothing until someone asks about a given problem, which is
    what 9.8 requires ("its thousandfold consequence is paid as the frontier is
    touched, not all at once").
    """
    marks: dict[str, str] = {}
    for _, problem_id, premise_id in standing_attributions(harness):
        status = harness.state.status.get(premise_id)
        if status == Status.REFUTED:
            marks[problem_id] = PREMISE_REFUTED
        elif status == Status.SUSPENDED_UNSUPPORTED:
            marks.setdefault(problem_id, PREMISE_UNACCREDITED)
    return marks


def open_orphans(harness) -> dict[str, str]:
    """Marked problems that have no consulted resolution yet — the work."""
    resolved = standing_resolutions(harness)
    return {
        pid: grade
        for pid, grade in premise_orphaned(harness).items()
        if pid not in resolved
    }


def retired_problems(harness) -> set[str]:
    """Problems whose consulted resolution is `retire`.

    The scheduler stops selecting these. They are not deleted and the retirement
    is attackable, so this is never an insolubility verdict (N3).
    """
    return {
        pid
        for pid, body in standing_resolutions(harness).items()
        if body.get("resolution") == "retire"
    }


def premise_work_invited(harness, problem_id: str, *, after: int) -> bool:
    """Should the critic be asked what this problem assumes?

    The deliberately dumb producer (Rung 2). Attention only: it invites a
    question, mints no problem, and carries no penalty for a critic who declines
    -- so H1 is intact (a failure redirects attention, it does not spawn) and
    nothing is ranked on whether an attribution exists.

    Fires when a problem has accumulated refuted candidates and nobody has yet
    questioned the problem itself.
    """
    if any(pid == problem_id for _, pid, _ in standing_attributions(harness)):
        return False
    refuted = sum(
        1
        for aid, pid in harness.state.addr
        if pid == problem_id and harness.state.status.get(aid) == Status.REFUTED
    )
    return refuted >= after
