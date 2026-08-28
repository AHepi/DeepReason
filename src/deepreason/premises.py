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

from deepreason.canonical import canonical_json
from deepreason.ontology import Commitment, Interface, Provenance, Ref, Status
from deepreason.ontology.artifact import RefRole
from deepreason.programs import content_text

ATTRIBUTION_EVAL = "program:presupposition_wf"
RESOLUTION_EVAL = "program:premise_resolution_wf"

RESOLUTIONS = ("retire", "translate", "independence")

# The premise rent battery (Formalization §12.2 demarcation). Its eval kind is
# NOT ``program:``, and that is the design rather than an omission:
# ``programs.evaluate`` hands a program (text, budget, artifact) and no
# commitment registry, and demarcation is a property of the INTERFACE plus its
# behaviour under variation, which no content-only program can see. Two
# properties follow, both load-bearing. Every generic sweep skips it, because
# ``programs.evaluable`` is False for an unknown eval kind. And for the same
# reason it never enters ``B^-HV``, so CARRYING THE RENT BATTERY CONTRIBUTES
# NOTHING TO SATISFYING IT: no role variant can differ on a commitment nobody
# can evaluate. §12.2 closes the self-immunisation hole in ``load`` rather than
# in ``crit`` -- an artifact that attaches ``json-wf`` to buy demarcation has a
# nonempty attack surface and still fails, because its variants pass that check
# too. Substantiveness is what the battery EXHIBITS under variation, not what
# the interface asserts.
PREMISE_RENT_EVAL = "demarcation:demarcated"
PREMISE_RENT = Commitment(id="demarcation:premise-rent", eval=PREMISE_RENT_EVAL)

ATTRIBUTION_COMMITMENT = Commitment(id="presupposition-wf@v1", eval=ATTRIBUTION_EVAL)

# How many refuted candidates a problem accumulates before the critic is asked
# what the problem itself assumes. A module constant, not a Config field: a new
# top-level Config field needs an explicit line in run_manifest.py's
# _versioned_source_config_data (frozen surface 4) and moves the scheduler x
# rules Config-partition count. Rung 1b-ii owns dials; this rung owns the hook.
PREMISE_INVITE_AFTER = 2

# Cascade grades (calculus 9.8). The distinction is inherited from the premise's
# own label and is never stored on the problem.
PREMISE_REFUTED = "premise-refuted"          # the premise was shown wrong
PREMISE_UNACCREDITED = "premise-unaccredited"  # the premise lost its support


PREMISE_CITATION_SCHEMA = "premise-citation-record.v1"

# The sampled role variants a rent verdict's second reading rests on, promoted
# from a trace-blob payload to a registered artifact so the sample is
# ATTACKABLE (Rung D / E-1, R58).
PREMISE_SAMPLE_SCHEMA = "premise-rent-sample.v1"


def attribution_content(
    problem_id: str, premise_id: str, *, citation_ref: str | None = None
) -> str:
    """Canonical content for an attribution artifact.

    The citation key appears only when there IS one, so an attribution filed
    without citations keeps the content address it had before P4 and a repeated
    filing stays idempotent across the change.
    """
    body = {"problem": problem_id, "premise": premise_id}
    if citation_ref is not None:
        body["citation"] = citation_ref
    return json.dumps(body, sort_keys=True)


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


def _fallen_frame_entries(harness):
    """The SECOND entry condition (v2 Rung 7): (problem id, label) for every
    problem a fallen frame carried.

    Reads `calculus.standing.fallen_frames`; it does not re-derive which frames
    fell. Two readings of "a frame that left unrefuted standing" would leave no
    way to tell which one a mark on the record meant -- the same reason
    `consultability_of` calls Rung 3b's separation predicate rather than
    re-deriving the graph condition.

    "Carrying" is sigma-admission, computed from each immutable `Problem`
    record (A7: nothing stores which assertions a problem was posed under), so
    the cascade's set and the renderer's set are the same set. Imported inside
    the function: this module is Rung 2's machinery and holds no calculus
    import at module scope.
    """
    from deepreason.calculus.standing import fallen_frames, framed_problem_ids

    for fallen in fallen_frames(harness):
        for problem_id in framed_problem_ids(harness, fallen.scope):
            if problem_id == fallen.problem_id:
                # The assertion's OWN promotion problem is the problem it
                # ANSWERS, never one posed under it, and sigma can admit it by
                # accident because the two are about the same subject. Marking
                # it would deprioritize in scheduling the one problem D-1
                # requires to stay on the frontier when a frame falls -- "the
                # incumbent's promotion problem stays on the frontier, ranked
                # by wound count". The exclusion is the answer to D-1 read
                # back into the cascade, not a convenience.
                continue
            yield problem_id, fallen.label


def premise_orphaned(harness) -> dict[str, str]:
    """problem id -> grade, for every problem whose premise has fallen.

    ONE MARKING FUNCTION, BOTH ENTRY CONDITIONS (Prop 9.7, complete at Rung 7).
    A problem is marked when a consulted ATTRIBUTION names a premise that has
    fallen (§9.8's premise entry, Rung 2), or when a consulted FRAME ASSERTION
    it was posed under has left unrefuted standing (§9.7's frame entry, Rung
    7). The two entries differ in what they READ and in nothing else: they
    produce the same pairs and pass through the same grading step below, so
    there is no second mechanism to keep in step with this one.

    §9.7's two grades are distinguished by the TWO-PASS LABELS and by nothing
    else -- `refuted` from pass one is a fall, `suspended_unsupported` from
    pass two is a revocation -- which is why neither entry needs machinery of
    its own to tell them apart. `suspended` marks NOTHING: an unresolved attack
    is nobody's win, and a problem posed under a contested frame is not
    orphaned.

    A problem reached by BOTH grades carries the fall, because a refuted
    premise is a stronger fact about the problem than an unaccredited one.

    DERIVED, never stored (C4): a pure function of replayed state, recomputed on
    demand. That is also what makes the cascade LAZY -- a fall over a thousand
    problems costs nothing until someone asks about a given problem, which is
    what 9.8 requires ("its thousandfold consequence is paid as the frontier is
    touched, not all at once").
    """
    entries = [
        (problem_id, harness.state.status.get(premise_id))
        for _, problem_id, premise_id in standing_attributions(harness)
    ]
    entries += list(_fallen_frame_entries(harness))
    marks: dict[str, str] = {}
    for problem_id, status in entries:
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


def orphan_causes(harness) -> dict[str, tuple[str, str]]:
    """problem id -> (cause id, grade), for every marked problem.

    The CAUSE is what fell: the premise for the premise entry, the assertion for
    the frame entry. Kept beside `premise_orphaned` rather than folded into it
    because the mark is what the scheduler and the resolutions read, and a mark
    that carried its cause would tempt a consumer to act on the cause instead of
    on the problem -- which is how a mark becomes a verdict.

    Grades agree with `premise_orphaned` by construction: both read the same
    labels through the same two-line mapping, and the test that pins them
    compares the two dictionaries key for key.
    """
    causes: dict[str, tuple[str, str]] = {}
    marks = premise_orphaned(harness)
    pairs: list[tuple[str, str]] = [
        (problem_id, premise_id)
        for _, problem_id, premise_id in standing_attributions(harness)
    ]
    from deepreason.calculus.standing import fallen_frames, framed_problem_ids

    for fallen in fallen_frames(harness):
        pairs += [
            (problem_id, fallen.assertion_id)
            for problem_id in framed_problem_ids(harness, fallen.scope)
            if problem_id != fallen.problem_id
        ]
    for problem_id, cause_id in pairs:
        if problem_id not in marks:
            continue
        # Precedence is expressed on the LABEL, exactly as the marking function
        # expresses it, and the grade is READ from the mark rather than decided
        # here. Two functions deciding a grade would be the second mechanism
        # Prop 9.7's completion exists to forbid -- so this one names neither
        # grade constant, and a reader can see that it cannot disagree.
        fell = harness.state.status.get(cause_id) == Status.REFUTED
        if problem_id in causes and not fell:
            continue
        causes[problem_id] = (cause_id, marks[problem_id])
    return causes


def batch_translation_offers(harness) -> tuple[dict, ...]:
    """§9.8's batch offers: OPEN orphans grouped by what fell.

    "The fall is one event; its thousandfold consequence is paid as the
    frontier is touched, not all at once" -- and one translation into a better
    vocabulary answers for a whole group at once, because the group shares a
    cause. Grouping by cause is therefore not a convenience: a group with two
    causes is two translations wearing one name.

    ATTENTION ONLY (C5, A9). This registers nothing, spawns nothing, moves no
    label and confers no protection. It offers; a critic who declines pays
    nothing, and the three resolutions remain ordinary registered artifacts
    authored one at a time. An offer is not a resolution and materializing a
    group still means adjudicating each closure.

    Sorted by cause id, then by problem id, so two readers of one root see the
    same offers in the same order.
    """
    open_ = open_orphans(harness)
    causes = orphan_causes(harness)
    grouped: dict[tuple[str, str], list[str]] = {}
    for problem_id in open_:
        cause = causes.get(problem_id)
        if cause is None:
            continue
        grouped.setdefault(cause, []).append(problem_id)
    return tuple(
        {
            "cause": cause_id,
            "grade": grade,
            "problems": sorted(problem_ids),
            "size": len(problem_ids),
        }
        for (cause_id, grade), problem_ids in sorted(grouped.items())
    )


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


def citation_record_content(problem_id: str, checks) -> str:
    """Canonical content for one verified-citation record."""
    return json.dumps(
        {
            "schema": PREMISE_CITATION_SCHEMA,
            "problem": problem_id,
            "citations": sorted(
                {(check.block_id, check.block_ref) for check in checks}
            ),
        },
        sort_keys=True,
    )


def file_premise_citations(harness, problem_id: str, checks, *, provenance=None):
    """Register the admitted-evidence record a premise attribution rests on.

    Only VERIFIED checks reach here, and the artifact records the blocks rather
    than the model's prose about them: what the attribution comes to depend on
    is the byte-checked citation, not the sentence that claimed it.
    """
    verified = [check for check in checks if check.verified]
    if not verified:
        return None
    return harness.create_artifact(
        citation_record_content(problem_id, verified),
        codec="json",
        provenance=provenance,
    )


def file_premise(
    harness, problem_id: str, premise_text: str, *, provenance=None, citation_ref=None
):
    """Register the premise X and the attribution rho. Returns (X, rho).

    Both are ordinary artifacts, so both are attackable (P6), and X carries the
    rent battery so demarcation adjudicates it without anyone writing an attack.
    Content-addressed ids make a repeated filing idempotent rather than a
    duplicate.

    `citation_ref` names an admitted-citation record, and the attribution
    DEPENDS on it (R62's fourth layer): if the citation record falls, the
    attribution loses its support. That is the one role the premise itself may
    never have — depending on the premise would suspend the attribution the
    moment the premise fell, erasing the relation that identifies the orphan.
    """
    harness.register_commitment(PREMISE_RENT)
    harness.register_commitment(ATTRIBUTION_COMMITMENT)
    premise = harness.create_artifact(
        premise_text,
        interface=Interface(commitments=[PREMISE_RENT.id]),
        provenance=provenance,
    )
    refs = [
        # MENTION, never DEPENDENCE: law 9.4'. presupposition_wf refuses the
        # other role, so this is guarded rather than merely intended.
        Ref(target=premise.id, role=RefRole.MENTION)
    ]
    if citation_ref is not None:
        refs.append(Ref(target=citation_ref, role=RefRole.DEPENDENCE))
    attribution = harness.create_artifact(
        attribution_content(problem_id, premise.id, citation_ref=citation_ref),
        codec="json",
        interface=Interface(
            commitments=[ATTRIBUTION_COMMITMENT.id],
            refs=refs,
        ),
        provenance=provenance,
    )
    return premise, attribution


def premise_rent_sweep(harness, variator=None, *, decided=None) -> list:
    """Refute every premise that fails DEMARCATION (Formalization §12.2).

    `demarcated(a) = crit(a) and load(a)`. `crit` asks whether the interface
    declares anything at all that could count against the premise; `load` asks
    whether the claim does any work — whether a role variant of it gets a
    different verdict from the battery. Both readings are needed and neither
    substitutes for the other, which is the point for PROSE: a prose premise
    declares almost nothing, so a criterion resting on `crit` alone fells every
    premise a critic can file and its verdict carries no information (operator,
    2026-08-15: "a second check needs to be added for prose").

    Without a variator the second reading cannot be taken, so NOTHING falls on
    it. That is a typed abstention rather than a silent pass: the run records
    `premise.rent-undecided.v1` once per premise and leaves the premise
    accepted, because "we could not check" must never look like "we checked and
    it was fine". A premise whose interface declares nothing at all still falls,
    because `crit` needs no sample.

    The verdict is DEMONSTRATIVE and therefore status-changing under every
    authority mode. It is also a SAMPLE through `load`, so ν says so and the
    sampled variants are on the record (§12.1's determinism road: log the
    variants rather than seed the kernel). Attacking ν reinstates the premise
    and un-marks the problem by the same computed predicate (N1).

    `decided` is a caller-owned cache of premises already settled by the second
    reading, exactly like the scheduler's `_fuzz_clean`: the sample costs a
    provider call and is a spot-check rather than a fixed point.
    """
    from deepreason.measures.demarcation import crit, load
    from deepreason.proof_debt import KernelCheckV1, file_derivation_manifest
    from deepreason.rules.warrants import register_fail_warrant

    settled = decided if decided is not None else set()
    critics = []
    for artifact in list(harness.state.artifacts.values()):
        if PREMISE_RENT.id not in artifact.interface.commitments:
            continue
        if artifact.id in settled:
            continue
        declares = crit(artifact, harness.commitments)
        sampled: list[str] = []
        if declares:
            if variator is None:
                settled.add(artifact.id)
                harness.record_measure(
                    inputs=["premise.rent-undecided.v1", artifact.id, "no-variator"]
                )
                continue
            if load(artifact, variator):
                settled.add(artifact.id)
                harness.record_measure(
                    inputs=["premise.rent-undecided.v1", artifact.id, "load-bearing"]
                )
                continue
            sampled = list(getattr(variator, "sampled", ()))
        # The bill this verdict rests on (Rung D / E-1). Only the SAMPLED path
        # files one, because only it has an open certificate: a premise felled
        # for an empty attack surface rests on `crit` alone, which is
        # re-derivable and owes no certificate. The sample is registered as an
        # ORDINARY artifact so "your sample was unrepresentative" finally has
        # somewhere to land -- before this it lived only in the trace blob,
        # which is readable and inert.
        manifest_ref = None
        if declares:
            certificate = harness.create_artifact(
                canonical_json(
                    {
                        "schema": PREMISE_SAMPLE_SCHEMA,
                        "premise": artifact.id,
                        "variants": sampled,
                    }
                ),
                codec="json",
                provenance=Provenance(role="variator"),
            )
            manifest = file_derivation_manifest(
                harness,
                artifact.id,
                kernel_checks=[
                    KernelCheckV1(
                        name="demarcation.crit",
                        program="",  # crit reads the interface, not the bytes
                        recorded_verdict="pass" if declares else "fail",
                    )
                ],
                open_certificate_refs=[certificate.id],
                # A2: the verdict is a finite-budget deterministic result.
                # A10: the sample is canonically ordered and serialized. Both
                # are ASSUMED here rather than proved, which is exactly what
                # axiom debt is for.
                axiom_debt=["A2", "A10"],
                provenance=Provenance(role="critic"),
            )
            manifest_ref = manifest.id
        critic = register_fail_warrant(
            harness,
            commitment_id=PREMISE_RENT.id,
            target_id=artifact.id,
            manifest_ref=manifest_ref,
            nu_content=(
                f"nu: the demarcation verdict on {artifact.id} is sound and "
                "relevant -- it fails demarcation: "
                + (
                    "its interface declares nothing that could count against it"
                    if not declares
                    else "no sampled role variant of it draws a different verdict "
                    "from its battery, so its mechanism is not load-bearing. That "
                    "half rests on a SAMPLE, not a proof, and the sampled variants "
                    "are on the record"
                )
            ),
            critic_content=(
                f"critic: premise {artifact.id[:12]} fails demarcation -- "
                "nothing it says could have been otherwise in any way its own "
                "battery can see"
            ),
            trace_ref=harness.blobs.put(
                canonical_json(
                    {
                        "commitment": PREMISE_RENT.id,
                        "eval": PREMISE_RENT_EVAL,
                        "verdict": "fail",
                        "crit": declares,
                        "load": False,
                        "reason": (
                            "empty attack surface"
                            if not declares
                            else "no sampled role variant differs over B^-HV"
                        ),
                        "commitments": list(artifact.interface.commitments),
                        "sampled_variants": [text[:120] for text in sampled],
                    }
                )
            ),
            skip_if_on_record=True,
        )
        if critic is not None:
            critics.append(critic)
    return critics


def independence_resolution_rate(harness) -> float:
    """Fraction of consulted resolutions settled as INDEPENDENCE.

    The calculus's own over-binding diagnostic (9.8): a high rate says problems
    are being marked as resting on premises they turn out not to need.
    """
    bodies = list(standing_resolutions(harness).values())
    if not bodies:
        return 0.0
    independent = sum(1 for body in bodies if body.get("resolution") == "independence")
    return independent / len(bodies)


def premise_work_invited(
    harness, problem_id: str, *, after: int = PREMISE_INVITE_AFTER
) -> bool:
    """Should the critic be asked what this problem assumes?

    The deliberately dumb producer (Rung 2). Attention only: it invites a
    question, mints no problem, and carries no penalty for a critic who declines
    -- so H1 is intact (a failure redirects attention, it does not spawn) and
    nothing is ranked on whether an attribution exists.

    THE LADDER. Every invitation costs `after` refuted candidates: the first is
    bought by the first `after`, and a problem already standing N attributions
    must accumulate `after * (N + 1)` before it may ask again. So a problem can
    be asked more than once, and the number of times is bounded by
    `floor(refuted / after)` -- bought by refutations the run had to produce
    anyway, never by a free re-ask.

    A latch was the alternative and the record refuted it. Until 2026-08-28 any
    standing attribution closed a problem to further invitations for the rest of
    the run; the technique run then established at seq 779, in a surviving
    conjecture, that its own question was malformed -- 593 events after the only
    channel for saying so had closed (AUDIT_REPORT.md section F-B, and the
    per-dispatch counterfactual in
    experiments/2026-08-28-change-premise-invitation-reachability/probes/).
    Criticism that arrives late is exactly the criticism this channel exists
    for, so the gate that shuts before it arrives is the defect.

    With no attribution standing this is byte-for-byte the rule it replaces, so
    a run that never files a premise sees no difference at all. An attribution
    that is itself refuted stops standing (`standing_attributions` counts only
    unrefuted ones), which LOWERS the rung rather than deleting it -- N1
    reversibility, unchanged.
    """
    standing = sum(1 for _, pid, _ in standing_attributions(harness) if pid == problem_id)
    refuted = sum(
        1
        for aid, pid in harness.state.addr
        if pid == problem_id and harness.state.status.get(aid) == Status.REFUTED
    )
    return refuted >= after * (standing + 1)
