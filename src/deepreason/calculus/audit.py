"""§9.9's authority audit, as an EXECUTABLE REPLAY PROGRAM.

    Standing is render authority and nothing else. It is derived, never stored
    (C4); it is content and edge-structure, never a type (C3); it appears in
    packs and schedules, never in label computation (C5, §6); every object
    realizing it — the frame assertion, its reach case, its subject's
    commitments, the succession rulings — is attackable and reinstateable
    (N1, P6).

Five clauses, one per sentence, each a program over a replayed root. Two of
them (C5, P6) are DIFFERENTIALS: they build a counterfactual labelling on a
COPY of the relations and compare, because the only way to show standing does
not reach a label is to compute the labels without it and find them unchanged.

It lives here rather than in `invariants.py` deliberately. `verify_root` asks
whether a record is well-formed and replayable; this asks whether the
CALCULUS's authority story holds on it, and it needs counterfactual relation
sets to ask that — a validator with a simulator inside it is a different thing
from a validator. Keeping it in `calculus/` also keeps a frozen surface at
zero, which is Rung 8's own forecast.

IT MUST BE ABLE TO FAIL. Every clause has a seeded-violation test.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

CLAUSES: tuple[str, ...] = (
    "C4-derived",
    "C3-content-not-type",
    "C5-absent-from-labels",
    "N1-attackable",
    "P6-reinstateable",
)

# The one body schema that realizes standing. Instrument standing is a
# `bounded` VALUE of that body's `validity` field, never a second record type
# (C3: the distinction is content, not type).
STANDING_SCHEMA = "poietic.frame-assertion.v1"

# The four kinds §9.9 names as realizing standing. Declared here so the audit
# reports coverage against the CALCULUS's list rather than against whatever the
# record happened to contain.
REALIZER_KINDS: tuple[str, ...] = (
    "assertion",
    "commitment",
    "reach-case",
    "succession-ruling",
)


class ClauseResultV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    ok: bool
    checked: int = 0
    detail: dict = Field(default_factory=dict)


class AuthorityAuditV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_: Literal["poietic.authority-audit.v1"] = Field(
        default="poietic.authority-audit.v1", alias="schema"
    )
    ok: bool
    grants: int
    clauses: tuple[ClauseResultV1, ...]
    violations: tuple[str, ...]


# --- the pieces each clause reads, exposed so a seed can replace one ------------


def stored_standing_fields(harness) -> tuple[str, ...]:
    """Any field on the applied state that looks like STORED standing.

    C4 is a claim about the shape of the state, so it is checked against the
    state's own attributes rather than against a promise. Anything named for
    standing or framing that is not a method is a candidate store.
    """
    state = harness.state
    names = set(getattr(state, "__dict__", {})) | set(
        getattr(type(state), "model_fields", {})
    )
    return tuple(
        sorted(
            name
            for name in names
            if ("standing" in name or "framing" in name)
            and not callable(getattr(state, name, None))
        )
    )


def grant_schemas(harness) -> tuple[str, ...]:
    """The body schemas realizing the consulted grants, deduplicated."""
    from deepreason.calculus.standing import declared_frame_assertions

    return tuple(
        sorted({body.schema_ for _, body in declared_frame_assertions(harness)})
    )


def realizing_objects(harness, grants) -> dict[str, str]:
    """`{object id: kind}` for everything §9.9 names as realizing standing.

    Built from every DECLARED frame assertion, not only the currently consulted
    ones. A refuted assertion still realizes standing -- it is the thing whose
    defeat took the standing away, and P6 is exactly the claim that the defeat
    can be undone. Auditing only live grants would let authority escape
    scrutiny by losing, which is the opposite of what N1 and P6 ask.
    """
    from deepreason.calculus.standing import (
        _promotion_problem_of,
        declared_frame_assertions,
    )
    from deepreason.calculus.succession import succession_trial_of

    found: dict[str, str] = {}
    for assertion_id, body in declared_frame_assertions(harness):
        found[assertion_id] = "assertion"
        for case in body.reach_case_refs:
            found[case] = "reach-case"
        subject = harness.state.artifacts.get(body.subject_ref)
        for cid in subject.interface.commitments if subject is not None else ():
            found[cid] = "commitment"
        promotion_problem = _promotion_problem_of(harness, assertion_id)
        # A succession ruling realizes standing when one exists: the rivals a
        # trial compared are the artifacts whose contest decided who frames.
        # They are ordinary registered artifacts, which is exactly what N1
        # needs -- a ruling that were not one could not be appealed.
        for pid in sorted(harness.state.problems):
            trial = succession_trial_of(harness, pid)
            if trial is not None and trial.promotion_problem == promotion_problem:
                for rival in trial.rival_ids:
                    found[rival] = "succession-ruling"
    found.pop("", None)
    return found


def _labels(nodes, att, dep) -> dict[str, str]:
    from deepreason.adjudication.grounded import label0
    from deepreason.adjudication.support import final_labels

    return {
        aid: status.value
        for aid, status in final_labels(label0(set(nodes), set(att)), set(dep)).items()
    }


def labels_without_standing(harness, grants) -> dict[str, str]:
    """The labelling with every grant's realizing edges WITHHELD.

    Built on a COPY of the relations. If standing never enters label
    computation, removing every artifact that realizes it from the attack and
    dependence relations cannot change any surviving label — and the labels of
    the removed artifacts themselves are excluded from the comparison, since
    an artifact that is not there has no label to compare.
    """
    # NAMED `withheld`, not `revoked`, and the rename is not cosmetic:
    # `test_revocation_has_no_rule_of_its_own` scans every NAME under
    # `calculus/` for one, because revocation is a derived grade and giving it
    # a rule is the mistake that guard exists to catch. This is a
    # counterfactual, not a grade.
    withheld = {grant.assertion_id for grant in grants}
    nodes = set(harness.state.artifacts) - withheld
    att = {(a, b) for a, b in harness.state.att
           if a not in withheld and b not in withheld}
    dep = {(a, b) for a, b in harness.state.dep
           if a not in withheld and b not in withheld}
    return _labels(nodes, att, dep)


def labels_without_attacks_on(harness, targets) -> dict[str, str]:
    """The labelling with every attack ON `targets` removed, on a COPY."""
    kept = {(a, b) for a, b in harness.state.att if b not in set(targets)}
    return _labels(set(harness.state.artifacts), kept, set(harness.state.dep))


# --- the program ------------------------------------------------------------------


def authority_audit(harness) -> AuthorityAuditV1:
    """Run all five clauses. A PURE READ: nothing here writes to the record."""
    from deepreason.calculus.standing import consulted

    grants = consulted(harness)
    violations: list[str] = []
    clauses: list[ClauseResultV1] = []

    def clause(name, ok, checked=0, **detail):
        clauses.append(
            ClauseResultV1(name=name, ok=ok, checked=checked, detail=detail)
        )

    # C4 -- derived, never stored.
    stored = stored_standing_fields(harness)
    if stored:
        violations.append(
            f"C4: standing is stored on the applied state: {list(stored)}"
        )
    derived = {
        grant.assertion_id: tuple(sorted(g.subject_id for g in consulted(harness)))
        for grant in grants
    }
    clause("C4-derived", not stored, len(grants), stored=list(stored),
           re_derived=len(derived))

    # C3 -- content and edge structure, never a type.
    schemas = list(grant_schemas(harness))
    extra = [s for s in schemas if s != STANDING_SCHEMA]
    if extra:
        violations.append(f"C3: standing is realized by a second record type: {extra}")
    clause("C3-content-not-type", not extra, len(schemas), schemas=schemas)

    # C5 -- absent from label computation. A DIFFERENTIAL.
    real = _labels(
        set(harness.state.artifacts), set(harness.state.att), set(harness.state.dep)
    )
    counterfactual = labels_without_standing(harness, grants)
    moved = sorted(
        aid for aid, label in counterfactual.items() if real.get(aid) != label
    )
    if moved:
        violations.append(
            f"C5: revoking standing moved {len(moved)} label(s): {moved[:5]}"
        )
    clause("C5-absent-from-labels", not moved, len(counterfactual),
           compared=len(real), moved=moved[:5])

    # N1 -- every realizing object is attackable.
    realizers = realizing_objects(harness, grants)
    unattackable = sorted(
        oid
        for oid, kind in realizers.items()
        if kind != "commitment" and oid not in harness.state.artifacts
    ) + sorted(
        oid
        for oid, kind in realizers.items()
        if kind == "commitment" and oid not in harness.commitments
    )
    if unattackable:
        violations.append(
            f"N1: {len(unattackable)} realizing object(s) are not on the record "
            f"and so could never be attacked: {unattackable[:5]}"
        )
    # §9.9 names FOUR kinds. A record with no succession has three, and the
    # clause says which it found rather than which it hoped for -- a kinds list
    # that silently shrank to what happened to be present would report full
    # coverage of a record that had none.
    clause("N1-attackable", not unattackable, len(realizers),
           realizers=sorted(realizers), kinds_declared=list(REALIZER_KINDS),
           kinds_found=sorted(set(realizers.values())),
           unattackable=unattackable[:5])

    # P6 -- reinstateable. A DIFFERENTIAL: removing every attack on a realizer
    # must restore it, or its status absorbs (Thm 12.3).
    attacked = sorted(
        oid for oid in realizers
        if oid in harness.state.artifacts
        and any(target == oid for _, target in harness.state.att)
    )
    reinstated = labels_without_attacks_on(harness, attacked) if attacked else {}
    absorbing = sorted(
        oid for oid in attacked if reinstated.get(oid) == "refuted"
    )
    if absorbing:
        violations.append(
            f"P6: {len(absorbing)} realizing object(s) stay refuted with every "
            f"attack on them removed: {absorbing[:5]}"
        )
    clause("P6-reinstateable", not absorbing, len(attacked),
           absorbing=absorbing, attacked=attacked[:5])

    return AuthorityAuditV1(
        ok=not violations,
        grants=len(grants),
        clauses=tuple(clauses),
        violations=tuple(violations),
    )
