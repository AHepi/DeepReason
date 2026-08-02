"""Boundaries the prose-refutation work must not cross.

Implements R5/R6 of `experiments/2026-08-01-change-prose-can-refute/REQUEST.md`,
the operator's verbatim instruction:

    "The scratchpad authority chain needs to be completely separate from
     conjecture/criticism adjudication. They shouldn't exist together."

The scratchpad is an imaginative workshop declared `advisory_non_grounding`:
storage alone never makes a note a fact, evidence, or support for one.  These
tests pin the stronger property the operator asked for -- separation of the
AUTHORITY chain, not merely of grounding.  Nothing a criticism can act on, and
nothing that decides what stands, may carry a scratch object.

They pass today.  They exist so that the prose-refutation work, which widens
what a criticism is given and what it may do, cannot quietly couple the two.
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

from deepreason.llm import packs
from deepreason.rules import crit

_SOURCE_ROOT = Path(__file__).resolve().parents[1] / "src" / "deepreason"


def _imported_modules(path: Path) -> set[str]:
    """Every module named by an import anywhere in the file, nested included."""

    tree = ast.parse(path.read_text(encoding="utf-8"))
    seen: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            seen.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            seen.add(node.module)
    return seen


def test_the_criticism_rule_imports_no_scratch_module():
    """R5/R6: the criticism side must not reach the scratchpad at all.

    A function-local import would satisfy a top-of-file grep and still couple
    the two, so the whole module is walked rather than its header.
    """

    imported = _imported_modules(_SOURCE_ROOT / "rules" / "crit.py")

    assert not [name for name in imported if name.startswith("deepreason.scratch")], (
        sorted(imported)
    )


def test_the_criticism_rule_touches_scratch_only_as_an_ordering_fence():
    """R5/R6: `scratch_fence_seq` is transactional ordering, not content.

    The fence is the one legitimate appearance of the word on this side -- it
    sequences a transaction against the scratch log without reading it.  If any
    other scratch name appears here, the separation has been breached.
    """

    source = (_SOURCE_ROOT / "rules" / "crit.py").read_text(encoding="utf-8")
    mentions = [
        line.strip()
        for line in source.splitlines()
        if "scratch" in line.lower() and not line.strip().startswith("#")
    ]

    assert mentions, "expected the fence assignments; the test is stale otherwise"
    assert all("scratch_fence_seq" in line for line in mentions), mentions


def test_the_criticism_pack_cannot_be_given_scratch():
    """R5/R6: separation enforced by the signature, not by call-site habit.

    `render_conj_pack` accepts `scratch_context` because conjecture is where
    the workshop belongs.  The criticism pack must have no such parameter, so
    no future caller can pass one without changing this contract.
    """

    assert "scratch_context" in inspect.signature(packs.render_conj_pack).parameters

    for name in ("render_crit_pack", "render_batch_crit_pack"):
        parameters = inspect.signature(getattr(packs, name)).parameters
        assert "scratch_context" not in parameters, (name, sorted(parameters))


def test_the_defended_trial_imports_no_scratch_module():
    """R5/R6: the trial decides what stands, so it is authority chain proper.

    `crit_argumentative` routes a sustained case here, so this module is the
    last link before a prose case can change a status.  It must be as separate
    from the workshop as the criticism rule is.
    """

    imported = _imported_modules(_SOURCE_ROOT / "informal" / "trial.py")

    assert not [name for name in imported if name.startswith("deepreason.scratch")], (
        sorted(imported)
    )


def test_no_scratch_identifier_reaches_a_warrant_or_an_attack_edge():
    """R5/R6: what a warrant may name is the narrowest part of the chain.

    A warrant's referents are an artifact, a commitment, a validity node and a
    trace blob.  None of them is a scratch object, and nothing in the warrant
    module may import one.
    """

    imported = _imported_modules(_SOURCE_ROOT / "rules" / "warrants.py")
    assert not [name for name in imported if name.startswith("deepreason.scratch")], (
        sorted(imported)
    )

    imported = _imported_modules(_SOURCE_ROOT / "adjudication" / "edges.py")
    assert not [name for name in imported if name.startswith("deepreason.scratch")], (
        sorted(imported)
    )


SINGLE_FAMILY_AUTHORITY = "single_family_trial"
"""The value S11 adds to ``ARGUMENTATIVE_AUTHORITY``.

Named here so the assertion below fails on its ABSENCE until step 10 lands it,
rather than silently testing nothing.
"""


def test_the_single_family_authority_value_exists():
    """Implements R13/R15: the switch that makes the path reachable.

    RED until step 10.  Every other assertion in this section is structural and
    would pass vacuously without it, so this is what proves they are testing a
    mode that exists.
    """

    from deepreason.config import Config

    assert Config(ARGUMENTATIVE_AUTHORITY=SINGLE_FAMILY_AUTHORITY)


def test_the_criticism_prompt_cannot_vary_with_the_authority_mode():
    """Implements R9: nothing new is shown at the model boundary.

    The operator chose to dispatch an author-side critic WITHOUT telling the
    model who wrote the target.  Byte-identity across modes is proved
    STRUCTURALLY rather than by rendering twice: the criticism packs take no
    config and no authority argument, so no mode can reach them.  A future
    parameter that let one through fails this.
    """

    for name in ("render_crit_pack", "render_batch_crit_pack"):
        parameters = set(inspect.signature(getattr(packs, name)).parameters)
        assert not parameters & {"config", "authority", "mode", "trial_authority"}, (
            name,
            sorted(parameters),
        )


def test_the_criticism_prompt_never_names_an_author_or_a_school(tmp_path):
    """Implements R9: the model boundary carries no authorship.

    Targets reach the critic under call-local aliases.  If a school id or an
    author label ever appeared in the rendered text, that label would become an
    input to deciding what stands.
    """

    from deepreason.harness import Harness
    from tests.test_v6_engaged_repair_verification import _engaged_root

    harness = Harness(_engaged_root(tmp_path / "authorship"), read_only=True)
    target_id = sorted(harness.state.artifacts)[0]
    rendered = packs.render_crit_pack(
        target_id,
        harness.state,
        harness.commitments,
        harness.blobs,
        token_budget=2048,
    )

    schools = {
        artifact.provenance.school
        for artifact in harness.state.artifacts.values()
        if artifact.provenance.school
    }
    for school in schools:
        assert school not in rendered, school
    for label in ("school", "author", "provenance"):
        assert label not in rendered.lower(), label


def test_a_school_can_never_be_scheduled_to_criticise_its_own_work():
    """Implements R14: "as long as a critic isn't from the same school, it's fine".

    This is a PRESERVATION test, not a new rule.  The exclusion already holds
    three times over, and the single-family path must not weaken any of them:

      1. the planner subtracts the owner from the eligible set;
      2. a target record refuses to list the owner among completed critics;
      3. an assignment refuses to be constructed with the owner eligible.

    R14 is the operator's answer to the deepest risk in the feasibility
    survey -- a point of view criticising its own work is close to marking its
    own homework, and this repository's own pre-registered study found that
    withholding shared context does not buy independence.  The exclusion is
    what makes that risk not arise, so it is asserted rather than assumed.
    """

    import pytest
    from deepreason.workflow import criticism

    source = inspect.getsource(criticism.plan_foreign_criticism)
    assert "- {target.owner_school_id}" in source, source

    with pytest.raises(ValueError, match="owner school cannot be a completed"):
        criticism.ForeignCriticismTargetV1(
            target_id="a" * 64,
            owner_school_id="school-0",
            completed_critic_school_ids=("school-0",),
        )


def test_the_planner_leaves_a_single_school_run_with_no_eligible_critic():
    """Implements R14 at the boundary that matters for R15.

    One school and one family is the degenerate case the single-family path
    must NOT paper over: with nobody but the author available, the correct
    outcome is no criticism, not self-criticism.
    """

    from deepreason.workflow import criticism

    source = inspect.getsource(criticism.plan_foreign_criticism)
    assert "foreign_schools = sorted(set(bindings) - {target.owner_school_id})" in source


def _lease(family: str, role: str = "judge", seat: int = 0):
    """One frozen lease carrying only what the ensemble gates read.

    The endpoint identity varies with the seat, so a binding that names the
    wrong seat's endpoint is distinguishable from one that names the right one.
    """

    from deepreason.llm.firewall import EndpointLease, Route

    return EndpointLease(
        role=role,
        seat=seat,
        route=Route(
            endpoint_id=f"{role}-{family}-{seat}",
            base_url=f"mock://{family}",
            model_id=f"model-{family}",
            provider="mock",
            family=family,
            max_tokens=64,
            context_window_tokens=1024,
        ),
    )


def _judge_binding(school_id: str, lease):
    """One manifest-owned judge binding naming exactly the seat it is given."""

    from deepreason.run_manifest import SchoolRoleBindingV1

    return SchoolRoleBindingV1(
        school_id=school_id,
        role="judge",
        seat=lease.seat,
        endpoint_id=lease.route.endpoint_id,
    )


def test_the_cross_school_ensemble_accepts_one_family_with_two_schools():
    """Implements R14/R15: cross-SCHOOL stands in for cross-FAMILY.

    One family across both judge seats is exactly the case
    `require_cross_family_judge_ensemble` refuses, and exactly the case R15
    scopes the new path to.  Two schools bound to those two seats is what the
    substitute guarantee requires.
    """

    from deepreason.llm.firewall import require_cross_school_judge_ensemble

    seats = (_lease("glm", seat=0), _lease("glm", seat=1))
    accepted = require_cross_school_judge_ensemble(
        {"judge": seats},
        (_judge_binding("school-0", seats[0]), _judge_binding("school-1", seats[1])),
    )

    assert accepted == seats


def test_the_cross_school_ensemble_raises_on_one_family_and_one_school():
    """Implements R14: one point of view is not an ensemble.

    A single school holding both judge seats is the degenerate case -- the same
    objection R14 rules out on the criticism side, arriving instead at the seat
    that decides whether a case is sustained.  Two seats are present, so what
    is asserted is that seat count alone does not satisfy the gate.
    """

    import pytest
    from deepreason.llm.firewall import (
        JudgeSchoolEnsemblePolicyError,
        require_cross_school_judge_ensemble,
    )

    seats = (_lease("glm", seat=0), _lease("glm", seat=1))

    with pytest.raises(
        JudgeSchoolEnsemblePolicyError, match="SECOND_JUDGE_SCHOOL_REQUIRED"
    ):
        require_cross_school_judge_ensemble(
            {"judge": seats},
            (_judge_binding("school-0", seats[0]), _judge_binding("school-0", seats[1])),
        )


def test_the_cross_school_ensemble_does_not_count_an_unverifiable_binding():
    """Implements R15's fail-closed sense at the binding.

    A binding naming an endpoint the leased seat does not carry cannot be shown
    to describe that seat.  Coverage that cannot be verified is absence, so the
    gate must refuse rather than accept two nominal schools.
    """

    import pytest
    from deepreason.llm.firewall import (
        JudgeSchoolEnsemblePolicyError,
        require_cross_school_judge_ensemble,
    )
    from deepreason.run_manifest import SchoolRoleBindingV1

    seats = (_lease("glm", seat=0), _lease("glm", seat=1))
    elsewhere = SchoolRoleBindingV1(
        school_id="school-1", role="judge", seat=1, endpoint_id="some-other-endpoint"
    )

    with pytest.raises(JudgeSchoolEnsemblePolicyError):
        require_cross_school_judge_ensemble(
            {"judge": seats}, (_judge_binding("school-0", seats[0]), elsewhere)
        )


def test_the_cross_family_gate_is_untouched_by_the_cross_school_sibling():
    """Implements R15/S8: the new gate is a sibling, never a relaxation.

    Byte-level proof that the existing gate did not move lives in `git diff`;
    this pins the behaviour that diff is protecting, so a future edit to the
    cross-family gate fails here even if the diff is never inspected again.
    """

    import pytest
    from deepreason.llm.firewall import (
        JudgeEnsemblePolicyError,
        require_cross_family_judge_ensemble,
    )

    one_family = (_lease("glm"), _lease("glm"))
    with pytest.raises(JudgeEnsemblePolicyError, match="SECOND_JUDGE_FAMILY_REQUIRED"):
        require_cross_family_judge_ensemble({"judge": one_family})

    two_families = (_lease("glm"), _lease("qwen"))
    assert require_cross_family_judge_ensemble({"judge": two_families}) == two_families


def test_the_single_family_predicate_fails_closed_on_no_leases():
    """Implements R15: "only make it active if a single model is running the
    entire harness".

    No family is not one family.  An empty lease set must not unlock the
    substitute guarantee, because "we could not tell" is not "we checked".
    """

    from deepreason.llm.firewall import is_single_family_run

    assert is_single_family_run({}) is False
    assert is_single_family_run({"judge": ()}) is False


def test_the_single_family_predicate_reads_every_role_not_just_judges():
    """Implements R15: "a single model is running the ENTIRE harness".

    A run whose judges share a family while its conjecturer does not is a
    multi-family run, and must not qualify.
    """

    from deepreason.llm.firewall import is_single_family_run

    assert is_single_family_run({"judge": (_lease("glm"), _lease("glm"))}) is True
    assert (
        is_single_family_run(
            {"judge": (_lease("glm"),), "conjecturer": (_lease("qwen", role="conjecturer"),)}
        )
        is False
    )
