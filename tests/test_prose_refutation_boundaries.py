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
import json
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


def test_the_new_mode_is_config_only_and_refused_by_the_manifest_path():
    """Implements S11's reconciliation of the two authority vocabularies.

    `authority.py` `_ARGUMENTATIVE_VALUES` (Config) and `rules/crit.py`
    `_POLICY_AUTHORITIES` (manifest `CriticismPolicyV1.authority`) are separate
    closed sets, and the new value belongs to exactly one of them ON PURPOSE.

    Admitting it to the manifest set would change a frozen manifest Literal,
    and with it every qualification subject digest derived from the manifest --
    making roots that are replay-valid today read against a schema they were
    not written under. So the manifest-bound path REFUSES it, with a reason
    that says which vocabulary it belongs to rather than only that it is
    unknown.
    """

    import pytest
    from deepreason.authority import _ARGUMENTATIVE_VALUES
    from deepreason.rules import crit

    assert SINGLE_FAMILY_AUTHORITY in _ARGUMENTATIVE_VALUES
    assert SINGLE_FAMILY_AUTHORITY not in crit._POLICY_AUTHORITIES

    with pytest.raises(ValueError, match="ARGUMENTATIVE_AUTHORITY_NOT_MANIFEST_BOUND"):
        crit._resolve_authority(None, SINGLE_FAMILY_AUTHORITY, policy_call=True)

    # The manifest's own two values still resolve exactly as before.
    assert crit._resolve_authority(None, "defended_trial", policy_call=True) == (
        "trial_required"
    )
    assert crit._resolve_authority(None, "observe_only", policy_call=True) == (
        "observe_only"
    )


def test_the_new_mode_routes_to_the_same_defended_trial(harness):
    """Implements R15/A6: "mint criticisms" reuses the path, not a new one.

    The criticism rule decides only observe-or-try. WHICH judge ensemble the
    trial then demands is decided downstream by route topology, so this mode
    must reach the identical branch `trial_required` reaches -- a second,
    parallel trial call would be a second path to a warrant, which A6 rules out.
    """

    from deepreason.config import Config
    from deepreason.rules import crit

    assert crit._authority(Config(ARGUMENTATIVE_AUTHORITY=SINGLE_FAMILY_AUTHORITY)) == (
        SINGLE_FAMILY_AUTHORITY
    )
    assert SINGLE_FAMILY_AUTHORITY in crit._TRIAL_MODES
    assert "trial_required" in crit._TRIAL_MODES
    assert "observe_only" not in crit._TRIAL_MODES

    source = (_SOURCE_ROOT / "rules" / "crit.py").read_text(encoding="utf-8")
    assert 'if authority == "trial_required":' not in source
    assert source.count("if authority in _TRIAL_MODES:") == 2


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


def test_the_refuting_endpoint_is_given_the_whole_argument(harness):
    """Implements R3: "the endpoint that wants to refute just needs access to
    the full argument" -- and R5/R6, which say what "full" excludes.

    Four things at once, because they are one property: the target's complete
    text, no excerpt marker, every id the target declares it rests on, and no
    scratch object anywhere in the result.  The support chain belongs to the
    argument -- a case that a target is unsupported cannot be answered without
    it -- and the scratchpad does not, at any budget.
    """

    from deepreason.llm import packs
    from deepreason.ontology import Commitment, Interface, Provenance
    from deepreason.ontology.artifact import Ref, RefRole

    harness.register_commitment(
        Commitment(id="k-whole", eval="predicate:'DESIGN' in content")
    )
    ground = harness.create_artifact(
        "the supporting measurement, recorded elsewhere",
        provenance=Provenance(role="conjecturer"),
    )
    body = "component detail\n" * 600
    target = harness.create_artifact(
        "BEGIN-DESIGN\n" + body + "END-MANIFEST",
        interface=Interface(
            commitments=["k-whole"],
            refs=[Ref(target=ground.id, role=RefRole.EVIDENCE)],
        ),
        provenance=Provenance(role="conjecturer"),
    )

    # A budget far below the target's size: the point is that the transport
    # limit no longer decides how much of the argument is refutable.
    rendered = packs.render_crit_pack(
        target.id, harness.state, harness.commitments, harness.blobs, token_budget=1200
    )

    assert "BEGIN-DESIGN\n" + body + "END-MANIFEST" in rendered
    assert "HARNESS PACK EXCERPT" not in rendered
    assert ground.id in rendered
    assert "SCR_" not in rendered
    assert "scratch" not in rendered.lower()


_DOUBLE = [{"in": [1], "out": 2}, {"in": [5], "out": 10}]


def _target_with(harness, kappa, content, codec="utf8"):
    from deepreason.ontology import Interface, Provenance

    harness.register_commitment(kappa)
    return harness.create_artifact(
        content,
        codec=codec,
        interface=Interface(commitments=[kappa.id]),
        provenance=Provenance(role="conjecturer", school="school-0"),
    )


def test_formal_backing_covers_the_whole_formal_set_not_only_execution(harness):
    """Implements R21: "they are both formal".

    `predicate:` and substantive `program:` commitments are formal claims, so
    they require formal refutation.  `formally_backed` is a superset of
    `execution_backed`: anything execution protected it protects too.
    """

    from deepreason.ontology import Commitment
    from deepreason.oracle import exec_oracle_commitment
    from deepreason.rules.warrants import execution_backed, formally_backed

    predicate = _target_with(
        harness, Commitment(id="k-moon", eval="predicate:'moon' in content"),
        "the moon pulls the sea",
    )
    assert formally_backed(harness, predicate.id) is True
    assert execution_backed(harness, predicate.id) is False

    runnable = _target_with(
        harness, exec_oracle_commitment("solve", _DOUBLE),
        "def solve(x):\n    return x * 2", codec="code:python",
    )
    assert formally_backed(harness, runnable.id) is True
    assert execution_backed(harness, runnable.id) is True


def test_a_structural_program_confers_no_formal_backing(harness):
    """Implements R22: "a conjecture endpoint might not fill out the form
    properly for this distinction".

    This is the hole R21 would open if "formal" meant merely evaluable.
    `workloads/models.py:105` names safe skeleton compilation as the one route
    by which model-authored counterconditions add commitments, and
    `ForbiddenCase` allows `program:` there.  A candidate could therefore
    attach `program:json-wf` -- which passes for anything well-formed -- and
    immunise itself against criticism.  Structural well-formedness proves
    nothing about the subject, so it protects nothing about the subject.
    """

    from deepreason.ontology import Commitment
    from deepreason.rules.warrants import formally_backed

    structural = _target_with(
        harness, Commitment(id="k-wf", eval="program:json-wf"), '{"a": 1}'
    )

    assert formally_backed(harness, structural.id) is False


def test_a_failing_formal_commitment_earns_no_protection(harness):
    """Implements Q12's answer: the all-currently-pass clause survives.

    A formal claim that is already refuted mechanically has nothing left to
    protect; shielding it from prose would shield a defeated claim.
    """

    from deepreason.ontology import Commitment
    from deepreason.rules.warrants import formally_backed

    failing = _target_with(
        harness, Commitment(id="k-absent", eval="predicate:'moon' in content"),
        "no such word here",
    )

    assert formally_backed(harness, failing.id) is False


def test_a_passing_formal_commitment_now_resists_prose(harness):
    """Implements R21 and closes VALIDATION.md's FAIL on S4's first clause.

    Measured before this step: a target carrying `predicate:'chorale' in
    content` -- `programs.evaluable` True -- was refuted by prose, `att=1`.
    "They are both formal", so it must not be.
    """

    from deepreason.config import Config
    from deepreason.ontology import Commitment, Interface, Provenance, Status
    from deepreason.rules.crit import crit_argumentative

    harness.register_commitment(
        Commitment(id="k-formal", eval="predicate:'chorale' in content")
    )
    target = harness.create_artifact(
        "a chorale passage with parallel fifths in bar 3",
        interface=Interface(commitments=["k-formal"]),
        provenance=Provenance(role="conjecturer", school="school-0"),
    )

    crit_argumentative(
        harness,
        target.id,
        _single_family_trial_adapter(harness),
        Config(ARGUMENTATIVE_AUTHORITY=SINGLE_FAMILY_AUTHORITY),
    )

    assert not harness.state.att
    assert harness.state.status[target.id] == Status.ACCEPTED


def test_a_structural_only_target_is_still_refutable_by_prose(harness):
    """Implements R22 end to end, not just at the predicate.

    `program:json-wf` is the cheap formal commitment a conjecturer can reach
    through safe skeleton compilation. If attaching it bought immunity, an
    endpoint could take back R2 by filling in the form. It buys nothing: the
    target is still refuted.
    """

    from deepreason.config import Config
    from deepreason.ontology import Commitment, Interface, Provenance, Status
    from deepreason.rules.crit import crit_argumentative

    harness.register_commitment(Commitment(id="k-wf", eval="program:json-wf"))
    target = harness.create_artifact(
        "a chorale passage with parallel fifths in bar 3",
        interface=Interface(commitments=["k-wf"]),
        provenance=Provenance(role="conjecturer", school="school-0"),
    )

    _run_substitute_trial(
        harness, _single_family_trial_adapter(harness), target, "school-1"
    )

    assert len(harness.state.att) == 1
    assert harness.state.status[target.id] == Status.REFUTED


def test_the_forbidden_case_form_still_refuses_a_predicate():
    """Implements R22's other half: the trustworthy class stays un-authorable.

    `predicate:` commitments confer immunity, so it matters that a model
    cannot write one. The bar is an RCE guard rather than an epistemic one,
    which is exactly why it needs a test on this side too -- a future
    relaxation for security reasons would silently hand endpoints the immunity
    key.
    """

    import pytest
    from deepreason.informal.skeleton import ForbiddenCase

    assert ForbiddenCase(case="c", eval="rubric:std-1")
    assert ForbiddenCase(case="c", eval="program:json-wf")

    with pytest.raises(ValueError):
        ForbiddenCase(case="c", eval="predicate:True")


def test_the_criticism_rule_still_records_scrutiny_for_a_formal_target(harness):
    """Implements R21 WITHOUT deleting evidence -- the correction made at
    step 18.

    Widening the criticism rule's own guard would have suppressed the scrutiny
    record for every target carrying a passing problem criterion, because
    problem criteria are instantiated into every candidate's interface. That
    loses the case entirely rather than declining to act on it, which moves
    toward adjudication blindness, not away from it. So only the trial -- the
    one place prose can mint a warrant -- consults the widened guard.
    """

    from deepreason.config import Config
    from deepreason.ontology import Commitment, Interface, Provenance, Status
    from deepreason.rules.crit import crit_argumentative

    harness.register_commitment(
        Commitment(id="k-formal", eval="predicate:'chorale' in content")
    )
    target = harness.create_artifact(
        "a chorale passage with parallel fifths in bar 3",
        interface=Interface(commitments=["k-formal"]),
        provenance=Provenance(role="conjecturer", school="school-0"),
    )

    critic = crit_argumentative(
        harness, target.id, _single_family_trial_adapter(harness), Config()
    )

    assert critic is not None
    assert any(
        event.inputs[:2] == ["scrutiny", target.id] for event in harness.log.read()
    )
    assert harness.state.status[target.id] == Status.ACCEPTED


def test_the_formal_boundary_is_execution_backing_and_not_evaluability(harness):
    """Implements R4: "only formal claims in formal prose require formal
    refutation" -- and CORRECTS SPEC.md's A1 about where that line sits.

    A1 read R4 as `programs.evaluable`. The implemented line is narrower:
    `rules/warrants.py:24` `execution_backed` protects a target only when it
    carries at least one EXEC-ORACLE commitment (`oracle.EXEC_PROGRAMS` --
    exec, property, dataset_oracle) and every one of them currently passes.

    A `predicate:` commitment is `evaluable` and is NOT execution-backed, so a
    target carrying only predicates is open to prose. Asserted rather than
    described, because the two readings differ in what is protected and the
    difference is invisible from either function alone.
    """

    from deepreason import programs
    from deepreason.ontology import Commitment, Interface, Provenance
    from deepreason.rules.warrants import execution_backed
    from tests.test_oracle import _oracle_candidate

    predicate = Commitment(id="k-prose", eval="predicate:'moon' in content")
    assert programs.evaluable(predicate) is True

    harness.register_commitment(predicate)
    only_predicate = harness.create_artifact(
        "the moon is not made of cheese",
        interface=Interface(commitments=[predicate.id]),
        provenance=Provenance(role="conjecturer"),
    )
    assert execution_backed(harness, only_predicate.id) is False

    _, executable = _oracle_candidate(harness, "def solve(x):\n    return x * 2")
    assert execution_backed(harness, executable.id) is True


def test_the_execution_guard_is_consulted_before_the_authority_branch():
    """Implements S4: the boundary needs no code change under any mode.

    Proved by ORDER rather than by running every mode: in both the criticism
    rule and the trial, `execution_backed` is consulted strictly before the
    authority value is branched on, so no authority -- including one that does
    not exist yet -- can reach past it.  A future mode added below the guard
    would still be caught; a guard moved below the branch fails here.
    """

    source = (_SOURCE_ROOT / "rules" / "crit.py").read_text(encoding="utf-8")
    guard = source.index("if execution_backed(harness, target_id):")
    branch = source.index('if authority == "observe_only":')
    assert guard < branch, (guard, branch)

    trial = (_SOURCE_ROOT / "informal" / "trial.py").read_text(encoding="utf-8")
    assert '_decline(harness, target_id, "execution-backed", diagnostics)' in trial


def test_a_prose_case_against_a_formally_backed_target_is_refused_by_type():
    """Implements S4's acceptance: refused WITH A TYPED REASON, not silently.

    The trial declines before any seat spends, so the refusal is attributable
    in the record rather than appearing as a case that simply failed to
    persuade.

    Step 18 widened this guard from `execution_backed` to `formally_backed`
    per R21. The decline REASON deliberately keeps its historical spelling
    `execution-backed`: it is compared against recorded roots, and renaming it
    would change what those roots' diagnostics mean.
    """

    import inspect
    from deepreason.informal import trial

    body = inspect.getsource(trial)
    guard_at = body.index("if formally_backed(harness, target_id):")
    decline = body.index('"execution-backed"', guard_at)
    assert decline - guard_at < 800, body[guard_at:decline]


class _StubEndpoint:
    """The minimum surface `EndpointLease.verify` reads off a live endpoint."""

    def __init__(self, lease):
        self.name = lease.route.base_url
        self.model = lease.route.model_id


def _adapter(leases, bindings):
    """An adapter carrying leases and school bindings and nothing else live."""

    from deepreason.llm.adapter import LLMAdapter

    endpoints = {
        role: tuple(_StubEndpoint(lease) for lease in seats)
        for role, seats in leases.items()
    }
    return LLMAdapter(
        endpoints, blob_store=None, leases=leases, school_judge_bindings=bindings
    )


def test_configuring_school_bindings_does_not_reach_the_gate_with_two_families():
    """Implements R15: "only make it active if a single model is running the
    entire harness".

    This is the assertion the whole extension turns on. Two families are
    present AND school bindings are configured -- the configuration is
    satisfiable, and it still must not be consulted, because a substitute
    guarantee is admissible only where the guarantee it substitutes for is
    unobtainable. The proof is the TYPE of the stop: the run fails on the
    cross-FAMILY code, so cross-school was never selected.

    The two judge seats here share no family, so the cross-school gate would
    have ACCEPTED them (both schools are bound). Selection by configuration
    would therefore be silent, not loud -- which is why it is asserted.
    """

    import pytest
    from deepreason.llm.firewall import JudgeEnsemblePolicyError

    two_families = (_lease("glm", seat=0), _lease("qwen", seat=1))
    bindings = (
        _judge_binding("school-0", two_families[0]),
        _judge_binding("school-1", two_families[1]),
    )
    adapter = _adapter({"judge": two_families}, bindings)

    assert adapter.school_judge_bindings == bindings
    assert adapter._select_judge_ensemble() == two_families

    one_family_only = (_lease("glm", seat=0), _lease("glm", seat=1))
    mixed = _adapter(
        {"judge": one_family_only, "conjecturer": (_lease("qwen", role="conjecturer"),)},
        (
            _judge_binding("school-0", one_family_only[0]),
            _judge_binding("school-1", one_family_only[1]),
        ),
    )
    with pytest.raises(JudgeEnsemblePolicyError, match="SECOND_JUDGE_FAMILY_REQUIRED"):
        mixed._select_judge_ensemble()


def test_the_cross_school_gate_governs_only_a_single_family_run():
    """Implements R15's positive half: the path is reachable when it should be.

    One family across the whole run, two schools bound to the two judge seats:
    this is the configuration `require_cross_family_judge_ensemble` refuses by
    construction, and the only one in which cross-school stands in for it.
    """

    import pytest
    from deepreason.llm.firewall import (
        JudgeEnsemblePolicyError,
        JudgeSchoolEnsemblePolicyError,
    )

    seats = (_lease("glm", seat=0), _lease("glm", seat=1))
    bindings = (_judge_binding("school-0", seats[0]), _judge_binding("school-1", seats[1]))

    assert _adapter({"judge": seats}, bindings)._select_judge_ensemble() == seats

    # Same topology, bindings withheld: the run falls back to the gate it
    # cannot satisfy rather than to no gate at all.
    with pytest.raises(JudgeEnsemblePolicyError):
        _adapter({"judge": seats}, ())._select_judge_ensemble()

    # Same topology, one school holding both seats: selected, and refused.
    one_school = (_judge_binding("school-0", seats[0]), _judge_binding("school-0", seats[1]))
    with pytest.raises(JudgeSchoolEnsemblePolicyError):
        _adapter({"judge": seats}, one_school)._select_judge_ensemble()


_DEMO_CASE = "clause 2 forbids parallel fifths and bar 3 has them"
_DEMO_DEFENCE = "the fifths echo the cantus firmus deliberately"
_DEMO_RULING = json.dumps(
    {"verdict": "fail", "decisive_point": "bar 3 has them"}
)


def _single_family_trial_adapter(harness):
    """critic + defender + two judge seats, ONE family, TWO schools bound.

    Both judge endpoints share a model id, so `infer_model_family` gives them
    one family and the cross-family gate is unsatisfiable by construction --
    the situation R13/R15 scope the new path to.
    """

    from deepreason.llm.adapter import LLMAdapter
    from deepreason.llm.endpoints import MockEndpoint
    from deepreason.llm.firewall import leases_from_endpoints

    # Every seat carries the same model id: R15 is "a single model is running
    # the ENTIRE harness", so a mock-family critic beside a glm-family judge
    # would be a multi-family run and correctly disqualified.
    endpoints = {
        "argumentative_critic": MockEndpoint(
            [json.dumps({"attack": True, "case": _DEMO_CASE})],
            name="mock://critic",
            model="glm-test",
        ),
        "defender": MockEndpoint(
            [json.dumps({"answer": _DEMO_DEFENCE})],
            name="mock://defender",
            model="glm-test",
        ),
        "judge": [
            MockEndpoint([_DEMO_RULING], name="mock://judge-a", model="glm-test"),
            MockEndpoint([_DEMO_RULING], name="mock://judge-b", model="glm-test"),
        ],
    }
    leases = leases_from_endpoints(endpoints)
    bindings = (
        _judge_binding("school-0", leases["judge"][0]),
        _judge_binding("school-1", leases["judge"][1]),
    )
    return LLMAdapter(
        endpoints,
        harness.blobs,
        retry_max=2,
        leases=leases,
        school_judge_bindings=bindings,
    )


def test_a_single_model_run_refutes_by_prose_end_to_end(harness):
    """Implements S2/R2 ("Prose can refute") in a single-model run.

    The whole extension, exercised rather than described: one model family
    across both judge seats, two schools bound to those seats, the new
    authority mode, and a target carrying no evaluable commitment. The
    outcome asserted is the typed record -- an attack edge and a REFUTED
    status -- not the model's prose.

    The refutation must come from PROSE, not from the mechanical channel that
    already mints defeats (FEASIBILITY.md risk 6, A7). The target here carries
    a `rubric:` commitment, which `programs.evaluable` rejects and no oracle
    can run, and the warrant is asserted to be ARGUMENTATIVE rather than
    DEMONSTRATIVE. That is what makes this evidence for S2.
    """

    from deepreason import programs
    from deepreason.config import Config
    from deepreason.ontology import Commitment, Interface, Provenance, Status, WarrantType
    from deepreason.rules.crit import crit_argumentative
    from deepreason.informal.standards import register_standard

    register_standard(harness, "std-fifths", "clause 2: no parallel fifths")
    kappa = Commitment(id="kappa-fifths", eval="rubric:std-fifths")
    harness.register_commitment(kappa)
    assert programs.evaluable(kappa) is False

    target = harness.create_artifact(
        "a chorale passage with parallel fifths in bar 3",
        interface=Interface(commitments=[kappa.id]),
        provenance=Provenance(role="conjecturer", school="school-0"),
    )

    adapter = _single_family_trial_adapter(harness)
    from deepreason.llm.firewall import is_single_family_run

    assert is_single_family_run(adapter.leases) is True

    critic, _ = _run_substitute_trial(harness, adapter, target, "school-1")

    assert critic is not None
    assert len(harness.state.att) >= 1
    assert harness.state.status[target.id] == Status.REFUTED

    warrant = next(w for w in harness.warrants.values() if w.target == target.id)
    assert warrant.type == WarrantType.ARGUMENTATIVE, warrant.type


def test_the_same_run_under_the_old_mode_refutes_nothing(harness):
    """Implements S2's contrast: the mode is what changed, not the fixture.

    Identical target and identical adapter under `observe_only` must leave the
    graph unmoved. Without this the previous test could be passing because of
    the fixture rather than because of the authority value.
    """

    from deepreason.config import Config
    from deepreason.ontology import Commitment, Interface, Provenance, Status
    from deepreason.rules.crit import crit_argumentative
    from deepreason.informal.standards import register_standard

    register_standard(harness, "std-fifths", "clause 2: no parallel fifths")
    kappa = Commitment(id="kappa-fifths", eval="rubric:std-fifths")
    harness.register_commitment(kappa)
    target = harness.create_artifact(
        "a chorale passage with parallel fifths in bar 3",
        interface=Interface(commitments=[kappa.id]),
        provenance=Provenance(role="conjecturer", school="school-0"),
    )

    critic = crit_argumentative(
        harness, target.id, _single_family_trial_adapter(harness), Config()
    )

    assert critic is not None  # the case is still recorded as scrutiny
    assert not harness.state.att
    assert harness.state.status[target.id] == Status.ACCEPTED
    assert not harness.warrants


def test_the_minting_critic_carries_a_school_other_than_the_targets(harness):
    """Implements R14 at the point a warrant is actually minted.

    The trial stamps the critic and its validity node with the critic's school.
    Asserted here on the artifact the warrant hangs from, so "a critic isn't
    from the same school" is checked where the status change happens rather
    than only where the assignment was planned (step 4).
    """

    from deepreason.config import Config
    from deepreason.informal.trial import run_argument_trial_from_case
    from deepreason.ontology import Commitment, Interface, Provenance, Status
    from deepreason.informal.standards import register_standard

    register_standard(harness, "std-fifths", "clause 2: no parallel fifths")
    kappa = Commitment(id="kappa-fifths", eval="rubric:std-fifths")
    harness.register_commitment(kappa)
    target = harness.create_artifact(
        "a chorale passage with parallel fifths in bar 3",
        interface=Interface(commitments=[kappa.id]),
        provenance=Provenance(role="conjecturer", school="school-0"),
    )

    critic = run_argument_trial_from_case(
        harness,
        _single_family_trial_adapter(harness),
        Config(),
        target.id,
        _DEMO_CASE,
        None,
        authority="status",
        critic_school_id="school-1",
    )

    assert critic is not None
    assert harness.state.status[target.id] == Status.REFUTED
    assert target.provenance.school == "school-0"
    assert critic.provenance.school == "school-1"
    assert critic.provenance.school != target.provenance.school


def test_the_config_only_path_cannot_satisfy_the_cross_school_guarantee(harness):
    """A limit of the assembled whole, asserted so it cannot be forgotten.

    R18 makes cross-school criticism the guarantee, so a case with no school
    is not a complete case.  `crit_argumentative`'s direct-helper path -- the
    one a bare `Config` drives -- passes `critic_school_id=None`, and a school
    can only be supplied through the v4 envelope, which requires an endpoint
    lease and a school context together and then demands a MANIFEST-bound
    authority value.

    So in a single-model run a Config-driven prose trial always declines
    `no-critic-school`.  The reachable path is the school-routed one, where
    the scheduler supplies the critic's school and the manifest supplies
    `defended_trial`.  This is a real narrowing of where the substitute
    applies, and it is asserted rather than described.
    """

    from deepreason.config import Config
    from deepreason.ontology import Status
    from deepreason.rules.crit import crit_argumentative

    target = _rubric_target(harness)

    critic = crit_argumentative(
        harness,
        target.id,
        _substitute_adapter(harness),
        Config(ARGUMENTATIVE_AUTHORITY=SINGLE_FAMILY_AUTHORITY),
    )

    assert critic is None
    assert not harness.state.att
    assert harness.state.status[target.id] == Status.ACCEPTED
    declines = [
        event.inputs[2]
        for event in harness.log.read()
        if event.inputs and event.inputs[0] == "trial-declined"
    ]
    assert declines == ["no-critic-school"], declines


def _role_spec(model: str) -> dict:
    """One §15 role-table entry — the same shape a ladder's config carries."""

    return {
        "endpoint_id": f"route-{model}",
        "endpoint": "https://models.invalid/v1",
        "model": model,
        "provider": "fixture",
        "family": "glm",
    }


def test_the_substitute_is_exposed_by_build_adapter_with_nothing_configured(harness):
    """Implements R20: "it should be EXPOSED whenever a single model is
    occupying all positions".

    The adapter is built by the production factory from a role table, exactly
    as a ladder builds one -- no constructor argument, no Config value, no
    manifest field, and nothing hand-fed. This is the assertion the previous
    round failed: the cross-school ensemble was an opt-in kwarg that
    `build_adapter` never passed, so no live run could reach it.
    """

    from deepreason.config import Config
    from deepreason.llm.adapter import build_adapter

    one_model = build_adapter(
        Config(
            roles={
                "argumentative_critic": _role_spec("glm-5"),
                "defender": _role_spec("glm-5"),
                "judge": [_role_spec("glm-5"), _role_spec("glm-5")],
            }
        ),
        harness.blobs,
    )
    assert one_model.is_single_model() is True
    assert len(one_model.judge_seats()) == 2

    two_models = build_adapter(
        Config(
            roles={
                "argumentative_critic": _role_spec("glm-5"),
                "defender": _role_spec("glm-5"),
                "judge": [_role_spec("glm-5"), _role_spec("glm-4")],
            }
        ),
        harness.blobs,
    )
    assert two_models.is_single_model() is False


def test_nothing_the_operator_configures_can_turn_the_substitute_on(harness):
    """Implements R20's other edge: route topology decides, not configuration.

    "Exposed whenever" is a fact about the run, not a preference. A two-model
    run cannot opt in, and a single-model run cannot opt out -- the predicate
    reads immutable leases and there is no knob in the path at all.
    """

    from deepreason.config import Config
    from deepreason.llm.adapter import LLMAdapter
    from deepreason.llm.endpoints import MockEndpoint
    from deepreason.llm.firewall import leases_from_endpoints

    endpoints = {
        "judge": [
            MockEndpoint(["{}"], name="mock://j0", model="glm-5"),
            MockEndpoint(["{}"], name="mock://j1", model="glm-4"),
        ]
    }
    # Every opt-in the previous design offered, supplied at once.
    adapter = LLMAdapter(
        endpoints,
        harness.blobs,
        leases=leases_from_endpoints(endpoints),
        school_judge_bindings=(),
    )
    assert adapter.is_single_model() is False

    source = inspect.getsource(
        __import__("deepreason.informal.trial", fromlist=["trial"])
    )
    guard = source.index("if adapter.is_single_model():")
    assert "config" not in source[guard : guard + 200], source[guard : guard + 200]


def _substitute_adapter(harness, second_judge_model: str = "glm-test"):
    """critic + defender + two judge seats, all one model unless told otherwise.

    `second_judge_model` is the only knob: setting it to another model of the
    SAME family makes the run multi-model without making it multi-family, which
    is the case the substitute guarantee must not fire on.
    """

    from deepreason.llm.adapter import LLMAdapter
    from deepreason.llm.endpoints import MockEndpoint
    from deepreason.llm.firewall import leases_from_endpoints

    endpoints = {
        "argumentative_critic": MockEndpoint(
            [json.dumps({"attack": True, "case": _DEMO_CASE})],
            name="mock://critic", model="glm-test",
        ),
        "defender": MockEndpoint(
            [json.dumps({"answer": _DEMO_DEFENCE})],
            name="mock://defender", model="glm-test",
        ),
        "judge": [
            MockEndpoint([_DEMO_RULING], name="mock://j0", model="glm-test"),
            MockEndpoint([_DEMO_RULING], name="mock://j1", model=second_judge_model),
        ],
    }
    return LLMAdapter(
        endpoints, harness.blobs, retry_max=2, leases=leases_from_endpoints(endpoints)
    )


def _rubric_target(harness):
    from deepreason.informal.standards import register_standard
    from deepreason.ontology import Commitment, Interface, Provenance

    register_standard(harness, "std-fifths", "clause 2: no parallel fifths")
    kappa = Commitment(id="k-rubric", eval="rubric:std-fifths")
    harness.register_commitment(kappa)
    return harness.create_artifact(
        "a chorale passage with parallel fifths in bar 3",
        interface=Interface(commitments=[kappa.id]),
        provenance=Provenance(role="conjecturer", school="school-0"),
    )


def _run_substitute_trial(harness, adapter, target, critic_school):
    from deepreason.config import Config
    from deepreason.informal.trial import run_argument_trial_from_case

    diagnostics: list = []
    critic = run_argument_trial_from_case(
        harness, adapter, Config(), target.id, _DEMO_CASE, None,
        authority="status", critic_school_id=critic_school,
        diagnostics=diagnostics,
    )
    return critic, diagnostics


def test_a_single_model_run_mints_a_warrant_on_cross_school_criticism(harness):
    """Implements R18/R20: "It should be cross school criticism", exposed
    "whenever a single model is occupying all positions".

    One model in every position cannot supply cross-FAMILY independence, so the
    trial was unreachable rather than strict. The substitute is that the case
    comes from a school other than the one that authored the target.
    """

    from deepreason.ontology import Status, WarrantType

    target = _rubric_target(harness)
    critic, _ = _run_substitute_trial(
        harness, _substitute_adapter(harness), target, "school-1"
    )

    assert critic is not None
    assert len(harness.state.att) == 1
    assert harness.state.status[target.id] == Status.REFUTED
    warrant = next(w for w in harness.warrants.values() if w.target == target.id)
    assert warrant.type == WarrantType.ARGUMENTATIVE


def test_the_substitute_refuses_a_critic_from_the_targets_own_school(harness):
    """Implements R14/R18: the guarantee IS the cross-school property.

    Same run, same model, same case -- only the critic's school changes. If
    this minted a warrant, the substitute would be guaranteeing nothing.
    """

    from deepreason.ontology import Status

    target = _rubric_target(harness)
    critic, diagnostics = _run_substitute_trial(
        harness, _substitute_adapter(harness), target, "school-0"
    )

    assert critic is None
    assert not harness.state.att
    assert harness.state.status[target.id] == Status.ACCEPTED
    assert diagnostics[-1]["declined"] == "same-school-critic"


def test_the_substitute_refuses_a_case_with_no_school_at_all(harness):
    """Implements R20's fail-closed sense at the guarantee itself.

    An absent school is not a different school. Without this the substitute
    would silently degrade to no guarantee whenever a caller omitted it.
    """

    target = _rubric_target(harness)
    critic, diagnostics = _run_substitute_trial(
        harness, _substitute_adapter(harness), target, None
    )

    assert critic is None
    assert not harness.state.att
    assert diagnostics[-1]["declined"] == "no-critic-school"


def test_two_models_of_one_family_still_face_the_cross_family_gate(harness):
    """Implements R19: this is why the predicate keys on MODEL, not family.

    Both judge seats are family `glm`; the seats differ only by model id. The
    run is therefore NOT single-model, the substitute is not offered, and the
    cross-family gate applies and raises -- which is correct, because a run
    with two models has more independence available than the substitute
    assumes.
    """

    import pytest
    from deepreason.llm.firewall import JudgeEnsemblePolicyError

    target = _rubric_target(harness)

    with pytest.raises(JudgeEnsemblePolicyError, match="SECOND_JUDGE_FAMILY_REQUIRED"):
        _run_substitute_trial(
            harness,
            _substitute_adapter(harness, second_judge_model="glm-4"),
            target,
            "school-1",
        )


def _lease_model(model: str, role: str = "judge", seat: int = 0):
    """A lease whose MODEL identity is what varies, family held constant."""

    from deepreason.llm.firewall import EndpointLease, Route

    return EndpointLease(
        role=role,
        seat=seat,
        route=Route(
            endpoint_id=f"{role}-{model}-{seat}",
            base_url=f"mock://{model}",
            model_id=model,
            provider="mock",
            family="glm",
            max_tokens=64,
            context_window_tokens=1024,
        ),
    )


def test_the_single_model_predicate_is_narrower_than_the_family_one():
    """Implements R19/R20: "single model runs", "a single model is occupying
    all positions".

    The distinguishing case: two models that SHARE a family. The family
    predicate says yes -- one family -- and the model predicate must say no.
    Narrower is the safe direction, because this unlocks a substitute for an
    independence guarantee and must not fire on a run that has more
    independence available than it thinks.
    """

    from deepreason.llm.firewall import is_single_family_run, is_single_model_run

    two_models_one_family = {
        "judge": (_lease_model("glm-4", seat=0), _lease_model("glm-5", seat=1))
    }
    assert is_single_family_run(two_models_one_family) is True
    assert is_single_model_run(two_models_one_family) is False


def test_the_single_model_predicate_reads_every_position(harness=None):
    """Implements R20: "occupying ALL positions" -- roles, not just judges."""

    from deepreason.llm.firewall import is_single_model_run

    assert is_single_model_run(
        {
            "judge": (_lease_model("glm-5", seat=0), _lease_model("glm-5", seat=1)),
            "defender": (_lease_model("glm-5", role="defender"),),
        }
    ) is True

    assert is_single_model_run(
        {
            "judge": (_lease_model("glm-5", seat=0), _lease_model("glm-5", seat=1)),
            "defender": (_lease_model("glm-4", role="defender"),),
        }
    ) is False


def test_the_single_model_predicate_fails_closed_on_no_leases():
    """Implements R20's fail-closed sense. No model is not one model."""

    from deepreason.llm.firewall import is_single_model_run

    assert is_single_model_run({}) is False
    assert is_single_model_run({"judge": ()}) is False


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
