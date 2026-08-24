"""`cascade-integrity` -- the replay check for Prop 9.7's totality.

Implements the granted surface-3 contact (v2 calculus program, Rung 7), which
was requested in that tranche's SPEC.md §1 before a line of it was written, per
`DR-INV-frozen-surfaces`'s own discipline: "a STOP already written in prose is
not a STOP that was obeyed."

Three limbs, all facts about the ROOT rather than about one artifact, because a
well-formedness program already refuses a malformed artifact and it is the
reader of a FINISHED run who needs telling that the record contains a broken
cascade at all:

    1. a consulted resolution whose problem carries no mark -- a question taken
       off the frontier with no premise-criticism behind it;
    2. a problem carried by a fallen frame and NOT marked -- Prop 9.7's
       totality, re-derived independently of the marking function;
    3. a fallen frame that marks nothing because it is not separated -- a
       disclosure, since components only ever grow and a separation held at
       consultation can be lost afterwards.

Limb 2's independence is the design point. A limb that called
`premise_orphaned` on both sides would agree with itself on every possible
record and could never fire -- a check that cannot fail is what
`docs_verify --audit` exists to refuse, and the same standard applies here.
"""

import inspect
from pathlib import Path

from deepreason.calculus import operations
from deepreason.harness import Harness
from deepreason.invariants import verify_root
from deepreason.ontology import (
    Commitment,
    Interface,
    Problem,
    ProblemProvenance,
    Provenance,
    Ref,
)
from deepreason.ontology.artifact import RefRole
from deepreason.premises import RESOLUTION_EVAL, resolution_content
from tests.conftest import attack


TIDES = {
    "schema": "declarative-scope.v1",
    "predicate": {"op": "contains",
                  "args": [{"field": "description"}, {"text": "tides"}]},
}


def _art(harness, text, refs=()):
    return harness.create_artifact(
        text, interface=Interface(refs=list(refs)),
        provenance=Provenance(role="critic"),
    )


def _problem(harness, pid, description):
    return harness.register_problem(
        Problem(
            id=pid, description=description, criteria=[],
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": []}
            ),
        )
    ).id


def _findings(root):
    return [
        v for v in verify_root(root)["violations"]
        if v["check"] == "cascade-integrity"
    ]


def _frame(harness, *, unseparated=False):
    subject = _art(harness, "b: the lunar theory of tides")
    case = _art(
        harness, "reach record: three lineages cite the lunar theory",
        refs=([Ref(target=subject.id, role=RefRole.DEPENDENCE)]
              if unseparated else ()),
    )
    promotion = operations.ensure_promotion_problem(
        harness, subject.id, "promote or refuse the lunar theory"
    )
    assertion = operations.file_frame_assertion(
        harness, problem=promotion, subject_ref=subject.id, scope=TIDES,
        reach_case_refs=(case.id,), departure_protocol="declare it",
    )
    return subject, assertion


# --- limb 1: a resolution with no mark ---------------------------------------

def test_a_resolution_with_no_mark_is_reported(tmp_path):
    """A `retire` takes a problem off the frontier and a `translate` replaces
    it. Doing either to a problem nothing orphaned removes a question with no
    premise-criticism behind it -- the silent path N3 forbids."""
    root = tmp_path / "no-mark"
    harness = Harness(root)
    problem = _problem(harness, "tides-0", "what governs the tides")
    kappa = Commitment(id=f"{RESOLUTION_EVAL}@v2", eval=RESOLUTION_EVAL,
                       budget={"steps": 1000})
    harness.register_commitment(kappa)
    harness.create_artifact(
        resolution_content("retire", problem), codec="json",
        interface=Interface(commitments=[kappa.id]),
    )
    del harness

    findings = _findings(root)
    assert len(findings) == 1, findings
    assert "tides-0" in findings[0]["detail"]
    assert "retire" in findings[0]["detail"]


def test_a_resolution_with_a_mark_is_not_reported(tmp_path):
    """The control. Without it the limb above would pass on a check that fired
    on every resolution, which is a louder way of saying nothing."""
    from deepreason.premises import file_premise

    root = tmp_path / "with-mark"
    harness = Harness(root)
    problem = _problem(harness, "tides-0", "what governs the tides")
    premise, _ = file_premise(harness, problem, "X: the tides are lunar")
    attack(harness, premise.id, "the-tides-are-not-purely-lunar")
    kappa = Commitment(id=f"{RESOLUTION_EVAL}@v2", eval=RESOLUTION_EVAL,
                       budget={"steps": 1000})
    harness.register_commitment(kappa)
    harness.create_artifact(
        resolution_content("retire", problem), codec="json",
        interface=Interface(commitments=[kappa.id]),
    )
    del harness

    assert _findings(root) == []


# --- limb 2: Prop 9.7's totality, re-derived ---------------------------------

def test_a_healthy_cascade_reports_nothing(tmp_path):
    """The positive control for limb 2: a fall, its marks, and silence."""
    root = tmp_path / "healthy"
    harness = Harness(root)
    _, assertion = _frame(harness)
    _problem(harness, "tides-0", "what governs the tides")
    attack(harness, assertion.id, "the-lunar-frame-overreaches-its-scope")
    del harness

    assert _findings(root) == []


def test_limb_two_re_derives_rather_than_asking_the_marking_function(tmp_path):
    """The design point, asserted structurally because it cannot be shown on a
    healthy record. `verify_root` computes what SHOULD be marked from the exits
    and σ, and compares -- so a mutation to either derivation breaks it. A limb
    that called `premise_orphaned` on both sides would agree with itself on
    every possible record and could never fail."""
    source = inspect.getsource(verify_root)
    block = source[source.index("Cascade integrity"):]
    assert "_framed_problem_ids(h, fallen.scope)" in block
    assert "_fallen_frames(h)" in block
    # the marks are read ONCE, as the thing being compared against
    assert block.count("_orphan_marks(h)") == 1


# --- limb 3: the disclosure ---------------------------------------------------

def test_an_unseparated_fallen_frame_is_disclosed(tmp_path):
    """Not an accusation. An assertion that was never consultable never framed
    anything, so its fall orphans nothing -- and the record should say so,
    because components only ever GROW and a separation held at consultation can
    be lost afterwards. Silence a reader cannot see is the thing worth
    reporting."""
    root = tmp_path / "unseparated"
    harness = Harness(root)
    _, assertion = _frame(harness, unseparated=True)
    _problem(harness, "tides-0", "what governs the tides")
    attack(harness, assertion.id, "the-lunar-frame-overreaches-its-scope")
    del harness

    findings = _findings(root)
    assert len(findings) == 1, findings
    assert assertion.id in findings[0]["detail"]
    assert "not separated" in findings[0]["detail"]
    assert "never consultable" in findings[0]["detail"]


# --- additive, and the channel it lands in ------------------------------------

def test_the_check_reports_nothing_on_a_root_that_predates_it():
    """The reader-before-writer guardrail, and the proof that the contact is
    ADDITIVE rather than the assertion that it is.

    Pinned to a COMMITTED root that `git ls-files` knows, per the durable-probe
    rule: a session-local root would die with the session and take this claim's
    meaning with it. Every committed root predates the cascade entirely, so the
    check must be silent on them -- absence is valid, never a finding.
    """
    root = Path(
        "experiments/live_engaged_2026-07-27/"
        "run-f4fa6663e5412d64df943a5a22342baf"
    )
    assert root.exists(), "the pinned committed root moved; repoint this probe"
    assert _findings(root) == []


def test_the_check_is_epistemic_not_integrity():
    """It reports what the record SAYS about its own cascade, not that the
    record is malformed -- so it lands in the epistemic channel beside
    `standing-integrity`, where a reader looking for adjudication problems will
    find it."""
    from deepreason.verification.report import _EPISTEMIC_CHECKS, _legacy_channel

    assert "cascade-integrity" in _EPISTEMIC_CHECKS
    assert _legacy_channel("cascade-integrity", "any detail") == "epistemic"


def test_no_existing_finding_moved(tmp_path):
    """Additive means INSERTIONS ONLY: a root with no frame assertions and no
    resolutions produces exactly what it produced before, and a root that DOES
    carry them gains cascade findings without losing any other."""
    root = tmp_path / "mixed"
    harness = Harness(root)
    _, assertion = _frame(harness, unseparated=True)
    _problem(harness, "tides-0", "what governs the tides")
    attack(harness, assertion.id, "the-lunar-frame-overreaches-its-scope")
    del harness

    violations = verify_root(root)["violations"]
    checks = [v["check"] for v in violations]
    assert "cascade-integrity" in checks
    # the Rung 4 check is untouched and still reports on its own terms
    assert [v for v in violations if v["check"] == "standing-integrity"] == []
