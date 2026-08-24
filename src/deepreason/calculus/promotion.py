"""§9.4's five pinned promotion criteria, as PROGRAMS over a frozen input.

Every criterion here is a pure function of two things: the CANDIDATE's own
bytes and interface, and ONE frozen, fence-stamped reach certificate fetched
from the blob store by digest. Neither reads live graph state, which is Rider 5
clause (4) and is what makes a promotion verdict reproducible: a candidate
evaluated twice on one record gets one answer, whatever the run did in between.

The programs are registered in `programs.PROGRAMS` with `class_="structural"`
AND in `programs.BLOB_PROGRAMS`. The dual registration is mechanical, not
decorative: `programs_by_class()` -- and therefore
`measures/reach._STRUCTURAL_PROGRAMS` -- reads `PROGRAMS` alone, so a criterion
living only in `BLOB_PROGRAMS` would count as SUBSTANTIVE by default and would
both ground reach and confer prose immunity. Both are wrong here. Grounding
reach would let promotion paperwork manufacture the signal that nominates;
conferring immunity would sell protection for a verdict that passes VACUOUSLY
whenever there is no incumbent to succeed. The class in this tree only ever
WITHHOLDS a measure or a protection, never grants one, so declaring these
structural withholds exactly what must be withheld.
"""

from __future__ import annotations

import json

from deepreason.canonical import sha256_hex
from deepreason.ontology import Commitment
from deepreason.ontology.commitment import Budget

PASS, FAIL, OVERRUN = "pass", "fail", "overrun"

SUBJECT_DEMARCATION = "promotion_subject_demarcation"
REACH_INTEGRITY = "promotion_reach_integrity"
SCOPE_DETERMINISM = "promotion_scope_determinism"
COMPATIBILITY = "promotion_compatibility"
ACCOUNTS_FOR = "promotion_accounts_for"

PROMOTION_PROGRAMS: tuple[str, ...] = (
    SUBJECT_DEMARCATION,
    REACH_INTEGRITY,
    SCOPE_DETERMINISM,
    COMPATIBILITY,
    ACCOUNTS_FOR,
)

# Prop 12.1: a criterion terminates inside a DECLARED bound, and `overrun` means
# unobtainable rather than slow. The bound is a step count over the frozen
# environment, so it is a property of content and never of the machine.
#
# It lives in `extra["spec"]["step_limit"]` and NOT in `Budget.steps`, which is
# the tree's own rule and not a preference: `DR-SEAM-evaluation-x-ontology`
# records that `Budget.steps` is read by nothing, because it is not part of any
# spec digest, while `extra["spec"]` is inside the commitment's content address.
# A bound outside the content address would let a verdict move without the
# commitment moving, which is exactly what §0 determinism forbids. The
# `dataset_oracle` adapter takes the same road for the same reason.
PROMOTION_STEPS = 4_000


def criteria_for(certificate_ref: str) -> tuple[Commitment, ...]:
    """The five criteria, bound to ONE certificate by content address.

    The certificate digest is in the commitment id as well as in its frozen
    spec, so a criterion cannot be re-pointed at a different certificate without
    becoming a different commitment -- and the problem that pinned it would then
    no longer name it.
    """
    spec = json.dumps(
        {"certificate_ref": certificate_ref, "step_limit": PROMOTION_STEPS},
        sort_keys=True, separators=(",", ":"),
    )
    return tuple(
        Commitment(
            id=f"promotion:{name}@{certificate_ref[:12]}",
            eval=f"program:{name}",
            budget=Budget(extra={"spec": spec}),
        )
        for name in PROMOTION_PROGRAMS
    )


# --- the shared frozen-input contract ----------------------------------------


def _load_certificate(budget, blobs):
    """Fetch and FENCE-STAMP the frozen input, or say why it is unobtainable.

    Every failure here is `overrun`, never `fail`. A missing or corrupt frozen
    input means the verdict could not be obtained; refusing a candidate for the
    state of its own problem's paperwork would be adjudication by accident.
    """
    from deepreason.calculus.claims import ClaimDecodeError, ReachCertificateV1, decode

    ref = _spec(budget).get("certificate_ref")
    if not ref:
        return None, {"reason": "promotion-criterion-has-no-certificate"}
    try:
        data = blobs.get(ref)
    except (KeyError, AttributeError):
        return None, {"reason": "promotion-certificate-unavailable"}
    if sha256_hex(data) != ref:
        return None, {"reason": "promotion-certificate-bytes-do-not-match-digest"}
    try:
        body = decode(data.decode("utf-8"))
    except (ClaimDecodeError, UnicodeDecodeError):
        return None, {"reason": "promotion-certificate-unreadable"}
    if not isinstance(body, ReachCertificateV1):
        return None, {"reason": "promotion-certificate-is-not-one"}
    return body, {}


def _frame_claim(text):
    """The candidate's frame claim, or None if it makes none."""
    from deepreason.calculus.claims import ClaimDecodeError, FrameAssertionV1, decode

    try:
        body = decode(text)
    except ClaimDecodeError:
        return None
    return body if isinstance(body, FrameAssertionV1) else None


def _spec(budget) -> dict:
    """The frozen commitment spec, or an empty one. Reads `extra["spec"]` and
    NEVER `Budget.steps` — see `PROMOTION_STEPS` above for why the distinction
    is load-bearing rather than stylistic."""
    if budget is None or not getattr(budget, "extra", None):
        return {}
    try:
        return json.loads(budget.extra.get("spec", "{}"))
    except ValueError:
        return {}


def _steps(budget) -> int:
    declared = _spec(budget).get("step_limit")
    return PROMOTION_STEPS if declared is None else int(declared)


def _open(text, budget, blobs, cost: int):
    """The three questions every criterion asks before it can answer its own.

    Returns `(certificate, claim, refusal)` with `refusal` set when the
    criterion cannot proceed. `cost` is the criterion's declared step price:
    charged BEFORE any work, so a starved budget is reported as unobtainable
    rather than discovered halfway through (Prop 12.1).
    """
    if _steps(budget) < cost:
        return None, None, (OVERRUN, {"reason": "budget-exhausted"})
    certificate, why = _load_certificate(budget, blobs)
    if certificate is None:
        return None, None, (OVERRUN, why)
    claim = _frame_claim(text)
    if claim is None:
        # Remark 9.5 from the criteria's side: an ordinary artifact addressed to
        # a promotion problem -- the problem's own companion subject, the
        # certificate itself -- makes no frame claim, so the promotion relation
        # is UNOBTAINABLE for it rather than false. `fail` here would mint a
        # warrant against the promotion problem's own paperwork.
        return None, None, (OVERRUN, {"reason": "not-a-frame-claim"})
    return certificate, claim, None


def _subject_of(certificate, artifact_id):
    for subject in certificate.subjects:
        if subject.artifact_id == artifact_id:
            return subject
    return None


def _commitment_of(certificate, cid):
    for commitment in certificate.commitments:
        if commitment.id == cid:
            return commitment
    return None


def _admitted(document, problems):
    """The frozen problems a scope document admits, or None if it cannot judge."""
    from deepreason.calculus.scope import ScopeError, compile_scope, scope_admits
    from deepreason.ontology import Problem, ProblemProvenance

    try:
        compiled = compile_scope(document)
    except ScopeError:
        return None
    admitted = []
    for frozen in problems:
        record = Problem(
            id=frozen.id,
            description=frozen.description,
            criteria=list(frozen.criteria),
            provenance=ProblemProvenance.model_validate(
                {"trigger": frozen.trigger, "from": list(frozen.sources)}
            ),
        )
        if scope_admits(compiled, record):
            admitted.append(frozen)
    return admitted


# --- criterion 1: subject-demarcation (§12.2, including its closing clause) ---


def subject_demarcation(text, budget, artifact=None, blobs=None):
    certificate, claim, refusal = _open(text, budget, blobs, cost=1)
    if refusal is not None:
        return refusal
    subject = _subject_of(certificate, claim.subject_ref)
    if subject is None:
        return OVERRUN, {"reason": "subject-not-in-environment",
                         "detail": claim.subject_ref}

    # The EMPIRICAL clause first, and the order is the point. It is fully
    # decidable from the frozen record with no seat, so letting the variator
    # abstention below short-circuit it would hide a real refusal behind an
    # honest "could not check".
    admitted = _admitted(claim.scope, certificate.problems)
    if admitted is None:
        return OVERRUN, {"reason": "scope-does-not-compile"}
    empirical = any(
        (spec := _commitment_of(certificate, cid)) is not None
        and spec.observation_valued
        for frozen in admitted
        for cid in frozen.criteria
    )
    if empirical and not any(
        (spec := _commitment_of(certificate, cid)) is not None
        and spec.observation_valued
        for cid in subject.commitments
    ):
        return FAIL, {
            "reason": "empirical-scope-without-observation-valued-commitment",
            "subject": subject.artifact_id,
        }

    if subject.demarcation == "no-attack-surface":
        # `crit` settles this alone and no sample could rescue it: an interface
        # declaring nothing forbids nothing, so there is no surface to be
        # load-bearing on.
        return FAIL, {"reason": "subject-declares-nothing",
                      "subject": subject.artifact_id}
    if subject.demarcation == "declared-only":
        return OVERRUN, {"reason": "demarcation-undecided-no-variator",
                         "subject": subject.artifact_id}
    return PASS, {"subject": subject.artifact_id, "demarcation": "load-bearing"}


# --- criterion 2: reach-integrity (I-6, §10.5) --------------------------------


def ordering_holds(records) -> bool:
    """The log's own ordering, and it is the whole of novel-fact evidence here.

    `subject_seq < measure_seq`: the artifact existed before the sweep that
    credited it, so the credit is not a record of something written to match.
    `reveal_seq > subject_seq` where sealed evidence was revealed: the artifact
    predates the evidence, which is the strongest provenance the informal side
    can produce (§10.5, Lakatos's criterion mechanized). Reading a mapping
    rather than the model so a reader can exercise the rule directly.
    """
    for record in records:
        subject_seq = int(record["subject_seq"])
        if subject_seq >= int(record["measure_seq"]):
            return False
        reveal = record.get("reveal_seq")
        if reveal is not None and int(reveal) <= subject_seq:
            return False
    return True


def reach_integrity(text, budget, artifact=None, blobs=None):
    certificate, claim, refusal = _open(text, budget, blobs, cost=1)
    if refusal is not None:
        return refusal
    if not claim.reach_case_refs:
        return FAIL, {"reason": "no-reach-case"}
    from deepreason.calculus.compiler import compile_interface
    from deepreason.ontology import Artifact

    # The certificate's own artifact id, RE-DERIVED rather than carried: an id
    # written inside the document it names could not be part of that document's
    # content address without a fixed point.
    certificate_id = Artifact.compute_id(
        _spec(budget)["certificate_ref"], "json", compile_interface(certificate)
    )
    known = {certificate_id} | {s.artifact_id for s in certificate.subjects}
    unknown = [ref for ref in claim.reach_case_refs if ref not in known]
    if unknown:
        # A case nomination did not freeze cannot have its provenance checked,
        # so it is refused rather than taken on trust.
        return FAIL, {"reason": "reach-case-not-in-the-record", "cases": unknown}
    records = [
        {
            "subject_seq": r.subject_seq,
            "measure_seq": r.measure_seq,
            "reveal_seq": r.reveal_seq,
        }
        for r in certificate.reach_records
    ]
    if not ordering_holds(records):
        return FAIL, {"reason": "reach-recorded-before-its-subject",
                      "records": records}
    return PASS, {"cases": list(claim.reach_case_refs)}


# --- criterion 3: scope-determinism (C1) --------------------------------------


def scope_determinism(text, budget, artifact=None, blobs=None):
    certificate, claim, refusal = _open(text, budget, blobs, cost=1)
    if refusal is not None:
        return refusal
    from deepreason.calculus.scope import ScopeError, compile_scope

    try:
        compile_scope(claim.scope)
    except ScopeError as error:
        if error.code in {"scope-too-deep", "scope-too-large"}:
            # A declared bound that could not be met. Refusing here would refuse
            # a candidate for being big rather than for being wrong (C2).
            return OVERRUN, {"reason": "scope-exceeds-its-bound",
                             "detail": error.code}
        return FAIL, {"reason": "scope-does-not-compile", "detail": error.code}
    if _steps(budget) < len(certificate.problems):
        return OVERRUN, {"reason": "budget-exhausted"}
    first = _admitted(claim.scope, certificate.problems)
    second = _admitted(claim.scope, certificate.problems)
    if first is None or second is None:
        return FAIL, {"reason": "scope-not-total"}
    if [p.id for p in first] != [p.id for p in second]:
        # Determinism PROVEN by re-evaluation rather than promised. The DSL's
        # leaves reach nothing but the five fields of a `Problem`, so this
        # cannot fail today -- and a future leaf that could would fail here
        # rather than in a live run.
        return FAIL, {"reason": "scope-is-not-deterministic"}
    return PASS, {"admits": [p.id for p in first]}


# --- criterion 4: compatibility -- rivals never co-frame ----------------------


def _declared_incumbents(certificate, claim):
    """The consulted subjects a candidate DECLARES succession over.

    Declared through Rung 4's existing `succeeded_wound_refs` intersecting the
    incumbent's machine-derived wound list (D-6 answer A), so no new claim body
    is invented and no candidate can choose its own wounds.
    """
    declared = set(claim.succeeded_wound_refs)
    out = []
    for grant in certificate.consulted:
        if grant.subject_ref == claim.subject_ref:
            continue
        subject = _subject_of(certificate, grant.subject_ref)
        if subject is not None and declared & set(subject.wound_refs):
            out.append(grant)
    return out


def compatibility(text, budget, artifact=None, blobs=None):
    certificate, claim, refusal = _open(text, budget, blobs, cost=1)
    if refusal is not None:
        return refusal
    mine = _admitted(claim.scope, certificate.problems)
    if mine is None:
        return OVERRUN, {"reason": "scope-does-not-compile"}
    succeeded = {g.assertion_id for g in _declared_incumbents(certificate, claim)}
    for grant in certificate.consulted:
        if grant.subject_ref == claim.subject_ref or grant.assertion_id in succeeded:
            continue
        theirs = _admitted(grant.scope, certificate.problems)
        if theirs is None:
            # A consulted assertion whose scope no longer compiles admits
            # nothing, exactly as `standing.frames` treats it. It cannot be
            # co-framed with.
            continue
        overlap = sorted({p.id for p in mine} & {p.id for p in theirs})
        if overlap:
            return FAIL, {
                "reason": "rivals-co-frame",
                "incumbent": grant.assertion_id,
                "overlap": overlap,
                # An overlapping consulted assertion routes to DISCRIMINATION.
                # Two subjects never frame one problem: the calculus resolves
                # that by comparing them, not by letting both stand.
                "route": f"disc:{overlap[0]}",
            }
    return PASS, {"admits": [p.id for p in mine]}


# --- criterion 5: accounts-for -- the STRONG succession relation ---------------


def succeeds(certificate, claim):
    """Formalization §3.5 / R57, all four parts, none of them optional.

    Exposed as a plain function over a frozen certificate and a frame claim
    because that is what it IS -- a relation over two frozen readings. The
    registry program below is a thin wrapper, so the relation can be exercised
    directly rather than only through a run.
    """
    incumbents = _declared_incumbents(certificate, claim)
    if not incumbents:
        # Nothing to succeed. Labelled so a reader never mistakes "nobody to
        # beat" for "beat somebody".
        return PASS, {"reason": "no-incumbent"}
    rival = _subject_of(certificate, claim.subject_ref)
    if rival is None:
        return OVERRUN, {"reason": "subject-not-in-environment",
                         "detail": claim.subject_ref}
    for grant in incumbents:
        incumbent = _subject_of(certificate, grant.subject_ref)
        if incumbent is None:
            return OVERRUN, {"reason": "incumbent-not-in-environment",
                             "detail": grant.subject_ref}
        verdict, detail = _succeeds_one(certificate, claim, incumbent, rival)
        if verdict != PASS:
            return verdict, detail
        witness = detail
    return PASS, witness


def _succeeds_one(certificate, claim, incumbent, rival):
    x_e, x_rival = set(incumbent.accounted), set(rival.accounted)
    residue = sorted(x_e - x_rival)

    # 1. RECOVERY. X(e) subset-of X(e'), or an unrefuted account of why e worked
    #    over its restricted domain. The tree already has the shape for that
    #    account -- a `bounded` validity naming the residue as its domain -- so
    #    nothing new is invented, and the account is an ordinary attackable
    #    claim: refute the assertion and the successor falls with it.
    accounted_for_residue = claim.validity == "bounded" and all(
        pid in (claim.validity_domain or "") for pid in residue
    )
    if residue and not accounted_for_residue:
        return FAIL, {"reason": "recovery-fails", "residue": residue,
                      "incumbent": incumbent.artifact_id}

    # 2. RIGIDITY. No easier to vary over the shared explicanda. An unmeasured
    #    reading is unobtainable, never a refusal: HV is a sampled spot-check
    #    that may never have been taken, and a missing number is not evidence.
    if incumbent.hv is None or rival.hv is None:
        return OVERRUN, {"reason": "rigidity-unmeasured",
                         "incumbent": incumbent.artifact_id}
    if rival.hv < incumbent.hv:
        return FAIL, {"reason": "rival-is-easier-to-vary",
                      "incumbent_hv": incumbent.hv, "rival_hv": rival.hv}

    # 3. NON-IMMUNIZATION. No PROPER functional component of e' is removable
    #    while preserving every registered accounting and criticism outcome.
    #    This is what rejects ad-hoc riders mechanically rather than by taste.
    if len(rival.commitments) >= 2:
        frozen_ids = {frozen.id for frozen in certificate.problems}
        if not x_rival <= frozen_ids:
            # Which components are idle depends on what the rival's accounted
            # problems ASK FOR, and an accounting the environment never froze
            # cannot answer that. Unobtainable, never a refusal: an empty
            # `needed` set would make every uncriticised component look idle
            # and fell a rival for the environment's gaps.
            return OVERRUN, {"reason": "accounting-not-in-environment",
                             "detail": sorted(x_rival - frozen_ids)}
        needed = {
            cid
            for frozen in certificate.problems
            if frozen.id in x_rival
            for cid in frozen.criteria
        }
        for component in sorted(rival.commitments):
            if component in rival.criticised_commitments:
                continue          # registered criticism cites it
            if component in needed:
                continue          # an accounted problem asks for it
            spec = _commitment_of(certificate, component)
            if spec is not None and spec.observation_valued:
                # A commitment exposing the rival to evidence does work by
                # existing, whether or not anything has attacked it yet.
                continue
            return FAIL, {"reason": "excisable-idle-component",
                          "component": component}

    # 4. STRICTNESS WITNESS. At least one of recovery, criticism survival or
    #    rigidity is STRICT. Without it a rival that merely matches the
    #    incumbent would displace it, which is theory choice by coin flip --
    #    and it is precisely the case the WEAK reading admits.
    if x_e < x_rival:
        return PASS, {"strictness": "recovery", "incumbent": incumbent.artifact_id}
    shared = {
        cid
        for frozen in certificate.problems
        if frozen.id in (x_e & x_rival)
        for cid in frozen.criteria
    }
    survived = sorted(
        cid for cid in shared
        if cid in incumbent.criticised_commitments
        and cid not in rival.criticised_commitments
    )
    if survived:
        return PASS, {"strictness": "criticism-survival", "commitments": survived}
    if rival.hv > incumbent.hv:
        return PASS, {"strictness": "rigidity"}
    return FAIL, {"reason": "no-strictness-witness",
                  "incumbent": incumbent.artifact_id}


def accounts_for(text, budget, artifact=None, blobs=None):
    certificate, claim, refusal = _open(text, budget, blobs, cost=1)
    if refusal is not None:
        return refusal
    return succeeds(certificate, claim)


# --- Remark 9.5's default-consult closure -------------------------------------


def promotion_criteria_sweep(harness, config) -> list:
    """Fire the promotion criteria BEFORE the renderer's next consultation.

    The hole this shuts is silent rather than loud: a frame assertion nobody
    happened to attack is ACCEPTED, and an accepted assertion addressed to a
    promotion problem is CONSULTED -- so an unexamined claim would frame every
    problem in its scope simply by having been registered first. The closure is
    not a new rule but an ORDER: the criteria fire, a `fail` mints a
    demonstrative warrant through `rules/warrants.register_fail_warrant` -- the
    tree's ONE warrant constructor -- the assertion stops being unrefuted, and
    `standing.consultability_of` declines it.

    Only a `fail` mints. An `overrun` is pending, never a refutation
    (`DR-SEAM-evaluation-x-rules`'s own agreement), so a criterion that could
    not be evaluated never refuses a candidate by default -- otherwise "we could
    not check" would become the strongest criticism in the calculus.

    Artifacts that make no frame claim are skipped ENTIRELY rather than
    evaluated and excused. The promotion problem's own paperwork is addressed to
    it -- its companion subject, its reach certificate -- and a sweep that ran
    the criteria over those would be evaluating a problem's evidence against the
    problem's own demands.
    """
    from deepreason import programs
    from deepreason.calculus.programs import FRAME_ASSERTION_COMMITMENT
    from deepreason.canonical import canonical_json
    from deepreason.ontology import SpawnTrigger
    from deepreason.rules.warrants import register_fail_warrant

    addressed: dict[str, set[str]] = {}
    for aid, pid in harness.state.addr:
        addressed.setdefault(pid, set()).add(aid)

    minted = []
    for pid, problem in sorted(harness.state.problems.items()):
        if problem.provenance.trigger is not SpawnTrigger.PROMOTION:
            continue
        criteria = [
            cid for cid in problem.criteria
            if cid in harness.commitments
            and harness.commitments[cid].eval.partition(":")[2] in PROMOTION_PROGRAMS
        ]
        for aid in sorted(addressed.get(pid, ())):
            artifact = harness.state.artifacts.get(aid)
            if artifact is None:
                continue
            if FRAME_ASSERTION_COMMITMENT.id not in artifact.interface.commitments:
                continue
            for cid in criteria:
                kappa = harness.commitments[cid]
                verdict, trace = programs.evaluate(kappa, artifact, harness.blobs)
                if verdict != FAIL:
                    continue
                critic = register_fail_warrant(
                    harness,
                    commitment_id=cid,
                    target_id=aid,
                    nu_content=(
                        f"nu: the promotion verdict on {aid} is sound and "
                        f"relevant -- it fails {kappa.eval.partition(':')[2]}: "
                        f"{trace.get('reason', 'refused')}"
                    ),
                    critic_content=(
                        f"critic: frame assertion {aid[:12]} does not earn its "
                        f"standing -- {trace.get('reason', 'refused')}"
                    ),
                    trace_ref=harness.blobs.put(
                        canonical_json(
                            {
                                "commitment": cid,
                                "eval": kappa.eval,
                                "verdict": verdict,
                                "promotion_problem": pid,
                                **{
                                    k: v for k, v in trace.items()
                                    if k not in {"commitment", "eval", "verdict"}
                                },
                            }
                        )
                    ),
                    skip_if_on_record=True,
                )
                if critic is not None:
                    minted.append(critic)
    return minted
