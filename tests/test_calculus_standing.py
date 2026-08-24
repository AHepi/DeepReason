"""The standing view: Def 9.3, Prop 12.4 and Prop 12.5.

Implements R4, R8, R9, R12 (v2 calculus program, Rung 4). The claim these
tests exist to make falsifiable is Prop 12.5 -- **standing never adjudicates**.
Label computation reads `att` and `dep` only; standing is consumed by render
and schedule alone. Its strongest form is here: two runs over the same graph,
one carrying frame assertions and one carrying none, produce IDENTICAL labels.

Prop 12.4's two directions are the companion. If both held only in one
direction the axes would be coupled and nobody would notice, because the
single-direction test passes under coupling in the other.
"""

import json

from deepreason.calculus import operations
from deepreason.calculus.standing import (
    consulted,
    frames,
    standing_of,
    standing_view,
)
from deepreason.harness import Harness
from deepreason.ontology import (
    Commitment,
    Interface,
    Problem,
    ProblemProvenance,
    Provenance,
    Ref,
    SpawnTrigger,
    Status,
)
from deepreason.ontology.artifact import RefRole
from tests.conftest import attack


SCOPE = {
    "schema": "declarative-scope.v1",
    "predicate": {"op": "contains",
                  "args": [{"field": "description"}, {"text": "tides"}]},
}


def _art(harness, text, refs=()):
    return harness.create_artifact(
        text,
        interface=Interface(refs=list(refs)),
        provenance=Provenance(role="critic"),
    )


def _shared_graph(harness):
    """The graph the labels are computed over, identical in both roots.

    Deliberately non-trivial: a supported claim, a premise it depends on, and
    a refuted rival. A graph of isolated nodes would make Prop 12.5's test pass
    for the wrong reason -- there would be nothing for standing to perturb.
    """
    premise = _art(harness, "p: the moon exerts a tidal force")
    subject = _art(
        harness, "b: the lunar theory of tides",
        refs=[Ref(target=premise.id, role=RefRole.DEPENDENCE)],
    )
    rival = _art(harness, "r: the solar theory of tides")
    attack(harness, rival.id, "the-solar-theory-mispredicts-the-spring-tide")
    return premise, subject, rival


def _frame(harness, subject, *, description="why do tides follow the moon"):
    case = _art(harness, "reach record: three lineages cite this subject")
    problem = operations.ensure_promotion_problem(harness, subject.id, description)
    assertion = operations.file_frame_assertion(
        harness, problem=problem, subject_ref=subject.id, scope=SCOPE,
        reach_case_refs=(case.id,),
        departure_protocol="declare the departure in the pack and cite this id",
    )
    return case, problem, assertion


# --- R8: Prop 12.5, in its strongest form ------------------------------------

def test_frame_assertions_do_not_move_a_single_label(tmp_path):
    """R8, Prop 12.5. Two runs, the same graph, one WITH frame assertions and
    one WITHOUT. Every label, every attack edge and every support edge over the
    shared artifacts is identical.

    Restricting to the shared ids is not a weakening: the frame assertion, its
    reach case and its promotion problem are extra NODES, and the claim is that
    they perturb nothing already there. A comparison over all nodes would
    compare a node against its own absence and prove nothing.

    THE SUBJECT IS REFUTED IN BOTH ROOTS, deliberately, and this is the part
    the mutation proof forced. An earlier version framed an ACCEPTED subject,
    and a mutation that leaked standing into `compute_label0` -- setting every
    consulted subject to `accepted` -- passed it, because the subject was
    already accepted. A run where standing could only agree with the label
    cannot detect standing overriding it. "Refuted and still framing" is both
    the interesting case for the calculus and the only one with anything to
    catch.
    """
    plain = Harness(tmp_path / "plain")
    framed = Harness(tmp_path / "framed")

    plain_premise, plain_subject, plain_rival = _shared_graph(plain)
    attack(plain, plain_subject.id, "the-lunar-theory-mispredicts-the-neap-tide")
    plain_ids = {plain_premise.id, plain_subject.id, plain_rival.id}

    framed_premise, framed_subject, framed_rival = _shared_graph(framed)
    attack(framed, framed_subject.id, "the-lunar-theory-mispredicts-the-neap-tide")
    _frame(framed, framed_subject)
    assert framed.state.status[framed_subject.id] == Status.REFUTED

    common = plain_ids & {framed_premise.id, framed_subject.id, framed_rival.id}
    assert len(common) == 3, "both roots must build the same content-addressed graph"

    def restrict(harness):
        return (
            {a: harness.state.status[a] for a in sorted(common)},
            sorted(tuple(e) for e in harness.state.att
                   if set(e) <= set(harness.state.artifacts)),
            sorted(tuple(e) for e in harness.state.dep if e[0] in common),
        )

    assert consulted(framed) != ()
    assert consulted(plain) == ()
    assert restrict(plain) == restrict(framed)


def test_label_computation_names_no_standing_symbol():
    """R8, Prop 12.5, structurally. `Harness._adjudicate` is the sole writer of
    `state.status`; asserted on its AST rather than its text so a rename or a
    deletion fails instead of passing. The positive anchors are what stop this
    becoming a check that passes on an empty function.

    This is the companion to the behavioural test above: that one would still
    pass if standing were consulted in a way that happened not to move a label
    on this particular graph.
    """
    import ast
    import inspect
    import textwrap

    tree = ast.parse(textwrap.dedent(inspect.getsource(Harness._adjudicate)))
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)} | {
        n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)
    }
    assert "build_att" in names and "final_labels" in names
    assert not any("standing" in n.lower() or "consult" in n.lower()
                   or "frame" in n.lower() for n in names), sorted(names)


def test_no_adjudication_module_imports_the_standing_view():
    """R8, Prop 12.5. The seam whose content is the ABSENCE of traffic
    (DR-SEAM-adjudication-x-authority) now also holds for standing. Read from
    the AST so a relative or aliased import cannot slip past."""
    import ast
    import pathlib

    for path in sorted(pathlib.Path("src/deepreason/adjudication").glob("*.py")):
        tree = ast.parse(path.read_text())
        modules = [
            (n.module or "") for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)
        ] + [
            a.name for n in ast.walk(tree) if isinstance(n, ast.Import)
            for a in n.names
        ]
        assert not any("calculus" in m or "standing" in m for m in modules), (
            path.name, modules
        )


# --- R9: Prop 12.4, both directions ------------------------------------------

def test_status_changes_without_standing_changing(harness):
    """R9, Prop 12.4, first direction. Refuting the SUBJECT moves its status
    and leaves its standing exactly where it was -- refuted and still framing,
    which is the ordinary condition of mature knowledge and the whole reason
    the second axis exists. The assertion only MENTIONS b, so pass two never
    reaches it."""
    _premise, subject, _rival = _shared_graph(harness)
    _case, _problem, assertion = _frame(harness, subject)

    before = standing_of(harness, subject.id)
    assert {g.assertion_id for g in before} == {assertion.id}
    assert harness.state.status[subject.id] == Status.ACCEPTED

    attack(harness, subject.id, "the-lunar-theory-mispredicts-the-neap-tide")

    assert harness.state.status[subject.id] == Status.REFUTED
    assert standing_of(harness, subject.id) == before


def test_standing_changes_without_status_changing(harness):
    """R9, Prop 12.4, second direction, and R11's behavioural half. Attacking
    the REACH CASE -- "contaminated", "shallow", "not held-out" -- cuts the
    assertion's support, so it falls to suspended_unsupported and stops being
    consulted. The subject's own status never moves. Revocation says unearned,
    not wrong."""
    _premise, subject, _rival = _shared_graph(harness)
    case, _problem, assertion = _frame(harness, subject)

    assert standing_of(harness, subject.id) != ()
    status_before = harness.state.status[subject.id]

    attack(harness, case.id, "the-reach-record-is-not-held-out")

    assert harness.state.status[assertion.id] == Status.SUSPENDED_UNSUPPORTED
    assert standing_of(harness, subject.id) == ()
    assert harness.state.status[subject.id] == status_before == Status.ACCEPTED


# --- R4: derived, never stored -----------------------------------------------

def test_standing_is_recomputed_from_the_log_and_never_stored(tmp_path):
    """R4, C4. Reopening the root read-only rebuilds the identical view from
    the log alone, and READING it writes nothing -- no repair, no new event.
    A view that were stored would survive this test while being a second
    record able to fall out of step with the first."""
    root = tmp_path / "run"
    harness = Harness(root)
    _premise, subject, _rival = _shared_graph(harness)
    _frame(harness, subject)
    first = standing_view(harness)
    lines = len((root / "log.jsonl").read_text().splitlines())

    reopened = Harness(root, read_only=True)
    second = standing_view(reopened)

    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    assert first["subjects"] == [subject.id]
    assert len((root / "log.jsonl").read_text().splitlines()) == lines


def test_no_field_was_added_to_problem_state_or_event():
    """R4. The standing axis added no stored field anywhere. A relation table
    would be a second graph whose interactions with att, dep, replay and status
    would all need re-proving."""
    from deepreason.ontology import Event, EpistemicState

    for model in (Problem, EpistemicState, Event):
        assert not any(
            "standing" in f or "frame" in f or "consult" in f
            for f in model.model_fields
        ), (model.__name__, sorted(model.model_fields))


def test_the_scope_predicate_selects_which_problems_are_framed(harness):
    """R4/R5. sigma is what makes standing SCOPED rather than global: the same
    consulted assertion frames the problems its predicate admits and no
    others."""
    _premise, subject, _rival = _shared_graph(harness)
    _frame(harness, subject)
    in_scope = harness.register_problem(Problem(
        id="pi-in", description="what sets the tides at the equinox",
        provenance=ProblemProvenance.model_validate(
            {"trigger": SpawnTrigger.SEED, "from": []}),
    ))
    out_of_scope = harness.register_problem(Problem(
        id="pi-out", description="why is the sky blue",
        provenance=ProblemProvenance.model_validate(
            {"trigger": SpawnTrigger.SEED, "from": []}),
    ))
    assert frames(harness, subject.id, in_scope.id) is True
    assert frames(harness, subject.id, out_of_scope.id) is False
    # The promotion problem is itself in scope, and correctly so: its
    # description states the question the subject frames. Naming it here rather
    # than filtering it out keeps the test honest about what sigma admits.
    framed_problems = standing_view(harness)["grants"][0]["framed_problems"]
    assert "pi-in" in framed_problems and "pi-out" not in framed_problems
    assert framed_problems == sorted(framed_problems)


# --- a manifest-bound root that carries a frame assertion --------------------

def _framed_manifest_root(tmp_path, monkeypatch, *, name):
    """A real v6 root, launched through `deepreason run --run-manifest`, whose
    record contains a frame assertion filed DURING the run.

    Filed during the run rather than bolted on after, because writing to a
    terminalized root would be exercising a state no operator can reach.
    """
    from tests.test_amendment_epochs import _problem_id
    from tests.test_lifecycle_operation_parity import (
        ORIGINAL_QUESTION,
        _bind_v6_root,
        _no_provider_scheduler,
    )
    from deepreason.cli.main import main
    from deepreason.run_manifest import MANIFEST_NAME

    filed = {}

    def scheduler_that_files_a_frame_assertion(harness, config, cycles, budget, **kw):
        subject = harness.create_artifact(
            "b: loop gain above unity sustains the oscillation",
            provenance=Provenance(role="conjecturer"),
            problem_id=_problem_id(ORIGINAL_QUESTION),
        )
        case = harness.create_artifact(
            "reach record: three lineages cite this subject",
            provenance=Provenance(role="conjecturer"),
        )
        problem = operations.ensure_promotion_problem(
            harness, subject.id, "what sets the tides at the equinox"
        )
        assertion = operations.file_frame_assertion(
            harness, problem=problem, subject_ref=subject.id, scope=SCOPE,
            reach_case_refs=(case.id,), departure_protocol="cite this id",
        )
        filed.update(subject=subject.id, assertion=assertion.id)
        return _no_provider_scheduler()(harness, config, cycles, budget, **kw)

    root, _manifest, _spec, problem_file = _bind_v6_root(tmp_path, name=name)
    monkeypatch.setattr(
        "deepreason.ops.run_scheduler", scheduler_that_files_a_frame_assertion
    )
    assert main([
        "--root", str(root), "run", "--budget", "1",
        "--problem", str(problem_file),
        "--run-manifest", str(root / MANIFEST_NAME),
    ]) == 0
    return root, filed


# --- R12 / L-2: operations parity over a root carrying a frame assertion -----

def test_amend_then_continue_over_a_root_carrying_a_frame_assertion(
    tmp_path, monkeypatch
):
    """R12, L-2. The operator's standing law: "The flags and operations
    available to the newer reason runs should be available to all
    configurations." A run whose record contains a frame assertion reaches the
    same typed terminal and accepts the same operations as one that does not --
    amend appends an epoch, continue prepares, and the log is appended to and
    never edited.

    The assertion is filed DURING the run rather than bolted on afterwards,
    because writing to a terminalized root would be testing a state no
    operator can reach.
    """
    from deepreason.runtime.continuation import prepare_continuation
    from tests.test_lifecycle_operation_parity import _supplement

    root, filed = _framed_manifest_root(tmp_path, monkeypatch, name="frame-parity-root")

    stopped = Harness(root, read_only=True)
    assert {g.assertion_id for g in consulted(stopped)} == {filed["assertion"]}

    from deepreason.amendment import amend_run, load_amendments
    from deepreason.invariants import verify_root

    log_before = (root / "log.jsonl").read_bytes()
    result = amend_run(root, attach=(str(_supplement(tmp_path)),))
    assert result["epoch"] == 1
    assert len(load_amendments(root)) == 1
    # Appended, never edited -- the amendment epoch does not rewrite the frame
    # assertion's own registration.
    assert (root / "log.jsonl").read_bytes().startswith(log_before)

    amended = Harness(root, read_only=True)
    assert {g.assertion_id for g in consulted(amended)} == {filed["assertion"]}
    # Checked HERE, before the continuation is prepared. Preparing one moves the
    # root off its committed terminal by design, so `verify_root` then reports
    # TERMINAL_COMMITMENT_REQUIRED on any root, framed or not -- asserting an
    # empty violation list after that point would be asserting a property no
    # continued run has.
    assert verify_root(root)["violations"] == []

    record = prepare_continuation(
        root, cycles="2", tokens="unlimited", check_operator_lock=False
    )
    assert record["schema"] == "deepreason-continuation-v1"
    continued = Harness(root, read_only=True)
    assert {g.assertion_id for g in consulted(continued)} == {filed["assertion"]}


# --- R6: the read-only surface -----------------------------------------------

def test_the_standing_surface_is_read_only_and_calls_no_model(
    tmp_path, monkeypatch, capsys
):
    """R6, and C4's condition on frozen surface 5. The `standing` CLI command
    and the `run_standing` MCP tool render a derived view and nothing else.

    Three properties, and the third is the one that keeps qualification digests
    still: neither path opens its root writably (a writable open REPAIRS a root,
    which would alter the evidence a reader asked to see), neither writes a byte
    to the log, and neither reaches an LLM seat. A new role would change the
    pair inventory and cost a ~14-minute qualification battery per home.
    """
    import ast
    import pathlib

    from deepreason.cli.main import main

    root, filed = _framed_manifest_root(tmp_path, monkeypatch, name="surface-root")
    before = (root / "log.jsonl").read_bytes()
    capsys.readouterr()

    assert main(["--root", str(root), "standing"]) == 0
    text = capsys.readouterr().out
    assert filed["subject"] in text and "frames" in text
    assert filed["assertion"] in text

    assert main(["--root", str(root), "standing", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["view"] == "standing.v1"
    assert payload["subjects"] == [filed["subject"]]

    # Reading wrote nothing.
    assert (root / "log.jsonl").read_bytes() == before

    # Both handlers open read-only, asserted on the source rather than trusted.
    # Read from the AST: a keyword argument is the meaning, and a text search
    # would also match `read_only=True` belonging to some neighbouring call.
    #
    # WIDENED at Rung 5, and widened rather than relaxed. The CLI handler now
    # binds its harness to a local so the knowledge section can share the one
    # open, so the argument to `standing_view` may be a Name rather than an
    # inline call. The assertion follows the binding and then requires the SAME
    # thing of it: the nearest binding of that name above the call, which is
    # the one the handler actually passes.
    for path in ("src/deepreason/cli/main.py", "src/deepreason/mcp_server.py"):
        tree = ast.parse(pathlib.Path(path).read_text())

        def _is_read_only_harness(node):
            return (
                isinstance(node, ast.Call)
                and ast.unparse(node.func) == "Harness"
                and any(
                    k.arg == "read_only" and getattr(k.value, "value", None) is True
                    for k in node.keywords
                )
            )

        # Every `<name> = Harness(...)` in the file, with its line. Keyed by
        # (name, lineno) and NOT by name alone: this file binds the name
        # `harness` twenty-six times, and a name-keyed map would silently
        # check one of them and pass whatever the other twenty-five did.
        bindings = [
            (target.id, assign.lineno, assign.value)
            for assign in ast.walk(tree)
            if isinstance(assign, ast.Assign)
            for target in assign.targets
            if isinstance(target, ast.Name)
            and isinstance(assign.value, ast.Call)
            and ast.unparse(assign.value.func) == "Harness"
        ]
        opens = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and ast.unparse(node.func) == "standing_view"
        ]
        assert opens, path
        for call in opens:
            inner = call.args[0]
            if isinstance(inner, ast.Name):
                # The nearest binding of that name ABOVE the call is the one
                # it receives, which is what the reader of this handler sees.
                candidates = [
                    (lineno, value) for name, lineno, value in bindings
                    if name == inner.id and lineno < call.lineno
                ]
                assert candidates, (path, ast.unparse(call))
                inner = max(candidates)[1]
            assert _is_read_only_harness(inner), (path, ast.unparse(call))

    # No LLM seat: the module graph the view depends on reaches no adapter,
    # route or seat. Read from the AST so an aliased import cannot slip past.
    tree = ast.parse(pathlib.Path("src/deepreason/calculus/standing.py").read_text())
    modules = [
        (n.module or "") for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)
    ] + [
        a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names
    ]
    assert not any(
        part in m for m in modules
        for part in ("llm", "adapter", "seat", "provider", "qualification")
    ), modules


# --- R15: the standing-integrity epistemic check ------------------------------

def _bad_mention_law_root(tmp_path, name="integrity-root"):
    """A root whose log contains a frame assertion with a DEPENDENCE on its own
    subject — Law 9.4 violated on the record.

    Hand-registered on purpose. The compiler cannot emit this interface and the
    authoring operation cannot produce it, so the only way such a record exists
    is a path that bypassed the controller — which is exactly the case a
    replay-time check has to catch, because by then nobody is around to refuse
    it at authoring time.
    """
    from deepreason.calculus.claims import FrameAssertionV1, encode
    from deepreason.calculus.programs import FRAME_ASSERTION_COMMITMENT

    root = tmp_path / name
    harness = Harness(root)
    subject = _art(harness, "b: the lunar theory of tides")
    case = _art(harness, "reach record: three lineages cite this subject")
    body = FrameAssertionV1(
        subject_ref=subject.id, scope=SCOPE, departure_protocol="cite this id",
        reach_case_refs=[case.id],
    )
    harness.register_commitment(FRAME_ASSERTION_COMMITMENT)
    problem = operations.ensure_promotion_problem(harness, subject.id, "tides")
    bad = harness.create_artifact(
        encode(body), codec="json",
        interface=Interface(
            commitments=[FRAME_ASSERTION_COMMITMENT.id],
            refs=[
                # The violation: DEPENDENCE where Law 9.4 requires MENTION.
                Ref(target=subject.id, role=RefRole.DEPENDENCE),
                Ref(target=case.id, role=RefRole.DEPENDENCE),
            ],
        ),
        problem_id=problem.id,
        provenance=Provenance(role="import"),
    )
    return root, subject.id, bad.id


def test_standing_integrity_fires_on_a_violated_mention_law(tmp_path):
    """R15. The epistemic check reports a frame assertion whose recorded
    interface DEPENDS on its own subject.

    Why a replay-time check when a well-formedness program already refuses it:
    the program's verdict refutes the artifact, which is a fact about that
    artifact. This check is a fact about the ROOT — that its record contains a
    violated separation at all — and it is the reader of a finished run, not
    the author of a live one, who needs to be told.
    """
    from deepreason.invariants import verify_root

    root, subject_id, bad_id = _bad_mention_law_root(tmp_path)
    findings = [
        v for v in verify_root(root)["violations"]
        if v["check"] == "standing-integrity"
    ]
    assert len(findings) == 1, verify_root(root)["violations"]
    assert bad_id in findings[0]["detail"]
    assert "mention law" in findings[0]["detail"]


def test_standing_integrity_is_silent_on_a_clean_root(tmp_path, monkeypatch):
    """R15. The positive half. Without it the test above would pass on a check
    that fired on every root, which would be a louder way of saying nothing."""
    from deepreason.invariants import verify_root

    root, _filed = _framed_manifest_root(tmp_path, monkeypatch, name="clean-root")
    assert [
        v for v in verify_root(root)["violations"]
        if v["check"] == "standing-integrity"
    ] == []


def test_standing_integrity_reports_nothing_on_a_root_that_predates_it():
    """R15, and the reader-before-writer guardrail. Every committed root
    predates the frame layer entirely, so the check must be SILENT on them —
    absence of frame assertions is valid, never a finding.

    Pinned to a committed root (`git ls-files` knows it) rather than a fixture,
    per the durable-probe rule: a session-local root would die with the session
    and take this claim's meaning with it.
    """
    from pathlib import Path

    from deepreason.invariants import verify_root

    root = Path(
        "experiments/live_engaged_2026-07-27/"
        "run-f4fa6663e5412d64df943a5a22342baf"
    )
    assert root.exists(), "the pinned committed root moved; repoint this probe"
    assert [
        v for v in verify_root(root)["violations"]
        if v["check"] == "standing-integrity"
    ] == []


# --- Prop 12.6 / D-4 answered A: the knowledge view, definition always inline --


def test_the_knowledge_view_never_prints_the_bare_word(tmp_path, monkeypatch, capsys):
    """D-4's H3 discipline, made structural rather than remembered.

    The recorded precedent this forestalls is not hypothetical: readers of
    `positions.accepted` treated acceptance as ADJUDICATED, and v1.7 §E had to
    add the `adjudication-blindness` check afterwards. "Knowledge" carries more
    weight than "accepted", so the definition travels with every row, and the
    row and its label come out of one function -- a caller cannot print one
    without the other without writing the bare word itself.
    """
    from deepreason.cli.main import main
    from deepreason.views.knowledge import KNOWLEDGE_LABEL, knowledge_view

    assert KNOWLEDGE_LABEL == "knowledge (unrefuted ∧ active ∧ reach > 0)"

    root, filed = _framed_manifest_root(tmp_path, monkeypatch, name="knowledge-root")
    capsys.readouterr()
    assert main(["--root", str(root), "standing"]) == 0
    text = capsys.readouterr().out
    for line in text.splitlines():
        if "knowledge" in line:
            assert KNOWLEDGE_LABEL in line, line


def test_the_knowledge_view_is_derived_and_writes_nothing(harness):
    """A view steers attention and never adjudicates (Def 8.1). It is
    recomputed from replayed state on every call, and no label anywhere is
    computed from it."""
    from deepreason.views.knowledge import KNOWLEDGE_LABEL, knowledge_view

    kappa = Commitment(id="k-mechanism", eval="predicate:len(content) > 0")
    harness.register_commitment(kappa)
    problem = harness.register_problem(
        Problem(
            id="question-seed", description="why do tides follow the moon",
            provenance=ProblemProvenance.model_validate(
                {"trigger": SpawnTrigger.SEED, "from": []}
            ),
        )
    )
    declaring = harness.create_artifact(
        "b: the lunar theory",
        interface=Interface(commitments=[kappa.id]),
        provenance=Provenance(role="conjecturer"), problem_id=problem.id,
    )
    bare = harness.create_artifact(
        "c: a claim that forbids nothing",
        provenance=Provenance(role="conjecturer"), problem_id=problem.id,
    )
    harness.record_measure(reach={declaring.id: 1.0, bare.id: 1.0})

    before = (harness.root / "log.jsonl").read_bytes()
    view = knowledge_view(harness)
    assert (harness.root / "log.jsonl").read_bytes() == before

    assert view["label"] == KNOWLEDGE_LABEL
    ids = [row["artifact"] for row in view["rows"]]
    # `crit` false settles §12.2 on its own: an interface declaring nothing
    # forbids nothing, so no sample could rescue it and the view excludes it.
    assert ids == [declaring.id]
    assert all(row["label"] == KNOWLEDGE_LABEL for row in view["rows"])
    # Every row says WHICH half of §12.2 it rests on. A row implying the full
    # reading it never took would be the misreading this view exists to avoid.
    assert view["rows"][0]["active_reading"] == "declared-only"


def test_a_refuted_or_unreaching_artifact_is_not_knowledge(harness):
    """The two other conjuncts, each on its own. Without them the view could
    pass by reporting everything with a nonempty interface."""
    from deepreason.views.knowledge import knowledge_view

    kappa = Commitment(id="k-mechanism", eval="predicate:len(content) > 0")
    harness.register_commitment(kappa)
    problem = harness.register_problem(
        Problem(
            id="question-seed", description="why do tides follow the moon",
            provenance=ProblemProvenance.model_validate(
                {"trigger": SpawnTrigger.SEED, "from": []}
            ),
        )
    )
    unreaching = harness.create_artifact(
        "b: never travelled", interface=Interface(commitments=[kappa.id]),
        provenance=Provenance(role="conjecturer"), problem_id=problem.id,
    )
    reaching = harness.create_artifact(
        "c: travelled and then fell", interface=Interface(commitments=[kappa.id]),
        provenance=Provenance(role="conjecturer"), problem_id=problem.id,
    )
    harness.record_measure(reach={reaching.id: 1.0})
    assert [r["artifact"] for r in knowledge_view(harness)["rows"]] == [reaching.id]

    attack(harness, reaching.id, "the account fails on its own criteria")
    assert harness.state.status[reaching.id] is Status.REFUTED
    assert knowledge_view(harness)["rows"] == []
    assert unreaching.id not in {
        r["artifact"] for r in knowledge_view(harness)["rows"]
    }
