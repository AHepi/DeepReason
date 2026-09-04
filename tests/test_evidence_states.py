"""The four evidence states, one test per state, on the record's own facts.

Implements R1/R2/R4/R10 of
`experiments/2026-09-04-change-evidence-states/REQUEST.md`.

The reading exists because the progress law (CLAUDE.md, 2026-09-03) makes
"survivors harder to vary, bolder conjectures that survived criticism" the
success criterion, and today an artifact nobody attacked and one that beat off
an attack both read ACCEPTED.

The committed roots used here are chosen for what they already contain, not
built for this test:

* `experiments/live_tri_2026-07-27/run-6dab80d615a437a8b3fa489a279df847` ran
  criticism 11 times and produced no attack at all (zero `att`, zero warrants —
  the fidelity guard in `tests/test_adjudication_blindness.py` pins that shape).
  It is the canonical OPEN case: criticism happened, nothing warranted landed,
  and nothing on the record says the pass ran in full.
* `experiments/2026-09-02-live-p-a2-corrected/run` is P-A2 at cycle 4, with 75
  accepted and 11 refuted, and does carry sustained attacks.

Both are opened READ-ONLY and never copied out, matching
`tests/test_adjudication_blindness.py`; a writable open of a committed root
repairs, i.e. destroys, the evidence.
"""

from __future__ import annotations

import pathlib
import subprocess

import pytest

from deepreason.harness import Harness
from deepreason.ontology import Artifact, Provenance, Status, Warrant, WarrantType
from deepreason.runtime.criticism_dispatch import (
    OUTCOME_COMPLETE,
    OUTCOME_CUT_BUDGET,
    declare_criticism_dispatch,
)
from deepreason.views.evidence_states import (
    PRE_CYCLE,
    EvidenceState,
    evidence_state_summary,
    evidence_states,
)
from tests.conftest import art, attack

REPO = pathlib.Path(__file__).resolve().parents[1]
BLIND_ROOT = REPO / "experiments/live_tri_2026-07-27/run-6dab80d615a437a8b3fa489a279df847"
PA2_ROOT = REPO / "experiments/2026-09-02-live-p-a2-corrected/run"


def _is_committed(path: pathlib.Path) -> bool:
    """Durable-evidence rule 1: a fixture must be something `git ls-files`
    knows, or it dies with the session and takes the test's meaning with it."""

    listed = subprocess.run(
        ["git", "ls-files", "--error-unmatch", str((path / "log.jsonl").relative_to(REPO))],
        cwd=REPO,
        capture_output=True,
    )
    return listed.returncode == 0


# --- the four states, on a harness built here ----------------------------- #


def test_open_when_nothing_warranted_was_brought(harness):
    """R1: OPEN is 'no warranted attack and no completed trial'."""

    a = art(harness, "an untested conjecture")
    assert harness.state.status[a.id] == Status.ACCEPTED
    assert evidence_states(harness)[a.id] is EvidenceState.OPEN


def test_supported_when_a_warranted_attack_was_itself_refuted(harness):
    """R1: SUPPORTED is 'survived at least one warranted attack'.

    The reinstatement shape of `tests/test_adjudication.py`: k attacks a, j
    attacks k, so a is ACCEPTED again — and this time the record can say WHY it
    is accepted, which is the whole point of the reading.
    """

    a = art(harness, "a conjecture that will be attacked")
    k, _ = attack(harness, a.id, "k")
    attack(harness, k.id, "j")

    assert harness.state.status[a.id] == Status.ACCEPTED
    assert harness.state.status[k.id] == Status.REFUTED
    assert evidence_states(harness)[a.id] is EvidenceState.SUPPORTED


def test_supported_when_a_trial_ruled_and_did_not_sustain(harness):
    """R1: 'or defended trial'. `trial-declined` is the typed non-sustained
    outcome `informal/trial.py::_decline` files."""

    a = art(harness, "a conjecture put on trial")
    harness.record_measure(inputs=["trial-declined", a.id, "guard_blocked_nothing"])
    assert evidence_states(harness)[a.id] is EvidenceState.SUPPORTED


def test_refuted_matches_the_status_label(harness):
    """R1: 'REFUTED (as today)' — the reading adds nothing to the label."""

    a = art(harness, "a conjecture that falls")
    attack(harness, a.id, "decisive")
    assert harness.state.status[a.id] == Status.REFUTED
    assert evidence_states(harness)[a.id] is EvidenceState.REFUTED


def test_contested_on_an_ensemble_split_trial(harness):
    """R1: CONTESTED is 'evidence both ways — an ensemble-split trial ...'."""

    a = art(harness, "a conjecture the judges split on")
    harness.record_measure(inputs=["trial-blocked:ensemble-split", a.id])
    assert evidence_states(harness)[a.id] is EvidenceState.CONTESTED


def test_contested_when_a_failed_attack_stands_beside_a_standing_one(harness):
    """R1: '... or a sustained attack alongside a failed one'.

    Built on the dangling-ref road `tests/test_adjudication.py` uses for mutual
    attack: A and B attack each other and both suspend, so B's attack on the
    target is neither eliminated nor decisive while a second attacker has been
    refuted outright.
    """

    target = art(harness, "the contested conjecture")
    nu1, nu2 = art(harness, "nu 1"), art(harness, "nu 2")

    # A dangling target is legal and takes effect when the target registers,
    # which is the only way to build a genuine attack cycle on content-addressed
    # ids (CON-warrants-and-attacks, "Dangling refs are legal").
    w1 = Warrant(id="w1", target="B", type=WarrantType.ARGUMENTATIVE, validity_node=nu1.id)
    a = Artifact(
        id="A", content_ref="inline:critic A", warrants=["w1"],
        provenance=Provenance(role="critic"),
    )
    harness.register_artifact(a, warrants=[w1])
    w2 = Warrant(id="w2", target="A", type=WarrantType.ARGUMENTATIVE, validity_node=nu2.id)
    w3 = Warrant(
        id="w3", target=target.id, type=WarrantType.ARGUMENTATIVE, validity_node=nu2.id
    )
    b = Artifact(
        id="B", content_ref="inline:critic B", warrants=["w2", "w3"],
        provenance=Provenance(role="critic"),
    )
    harness.register_artifact(b, warrants=[w2, w3])

    failed, _ = attack(harness, target.id, "an attack that is itself refuted")
    attack(harness, failed.id, "refuting the first attacker")

    assert harness.state.status["B"] == Status.SUSPENDED
    assert harness.state.status[failed.id] == Status.REFUTED
    assert evidence_states(harness)[target.id] is EvidenceState.CONTESTED


# --- the blind-critic constraint (C2) ------------------------------------- #


def test_a_critic_call_alone_never_moves_an_artifact_off_open(harness):
    """C2, from `experiments/2026-09-04-experiment-blind-critic/RESULTS.md`:
    the critic attacked every target it was shown, rate 1.000 in all four
    cells. So 'was criticised' may never mean 'a critic call happened' — an
    objection that mints no warrant is not evidence of survival."""

    a = art(harness, "a conjecture every critic complains about")
    for n in range(12):
        harness.create_artifact(
            f"critic: objection {n} against the conjecture",
            provenance=Provenance(role="critic"),
        )
        harness.record_measure(inputs=["trial-blocked:guard", a.id])

    assert harness.state.att == []
    assert evidence_states(harness)[a.id] is EvidenceState.OPEN


# --- the completeness rule (R4) ------------------------------------------- #


def test_absence_needs_the_declaration(harness):
    """R4: the absence of any warranted attack counts toward OPEN only; it may
    read as SUPPORTED only when the cycle declares criticism ran in full.

    This is the test SPEC.md S8's M5 mutant must turn red: drop the licence
    check and the first assertion below fails.
    """

    a = art(harness, "a conjecture nobody attacked")
    assert evidence_states(harness)[a.id] is EvidenceState.OPEN

    declare_criticism_dispatch(
        harness, cycle=0, outcome=OUTCOME_CUT_BUDGET, planned=4, dispatched=1,
        targets=[a.id],
    )
    assert evidence_states(harness)[a.id] is EvidenceState.OPEN, (
        "a pass cut by budget licenses nothing"
    )

    declare_criticism_dispatch(
        harness, cycle=1, outcome=OUTCOME_COMPLETE, planned=1, dispatched=1,
        targets=[a.id],
    )
    assert evidence_states(harness)[a.id] is EvidenceState.SUPPORTED


def test_a_complete_pass_licenses_only_the_targets_it_names(harness):
    """R4's licence is per artifact, not per cycle: a pass that ran in full says
    nothing about a conjecture it never looked at."""

    looked_at = art(harness, "a conjecture the pass dispatched on")
    never_visited = art(harness, "a conjecture the pass never saw")
    declare_criticism_dispatch(
        harness, cycle=0, outcome=OUTCOME_COMPLETE, planned=1, dispatched=1,
        targets=[looked_at.id],
    )
    readings = evidence_states(harness)
    assert readings[looked_at.id] is EvidenceState.SUPPORTED
    assert readings[never_visited.id] is EvidenceState.OPEN


def test_a_licence_never_overrides_a_real_attack(harness):
    """The licence road is guarded by 'no warranted attack'. A refuted artifact
    stays refuted however complete the pass declared itself."""

    a = art(harness, "a conjecture that falls")
    attack(harness, a.id, "decisive")
    declare_criticism_dispatch(
        harness, cycle=0, outcome=OUTCOME_COMPLETE, planned=1, dispatched=1,
        targets=[a.id],
    )
    assert evidence_states(harness)[a.id] is EvidenceState.REFUTED


# --- the population (a standing invariant) -------------------------------- #


def test_import_role_admission_records_are_excluded(harness):
    """CLAUDE.md's standing invariant: import-role admission records never count
    as survivors. They are bookkeeping, so they get no reading at all — and the
    exclusion is counted rather than silent."""

    position = art(harness, "a real conjecture")
    record = harness.create_artifact(
        "attached source: a dossier block",
        provenance=Provenance(role="import"),
    )
    readings = evidence_states(harness)
    assert position.id in readings
    assert record.id not in readings
    assert evidence_state_summary(harness)["excluded_import_admissions"] == 1


# --- the summary shape ---------------------------------------------------- #


def test_summary_counts_every_reading_once(harness):
    a = art(harness, "one")
    b = art(harness, "two")
    attack(harness, b.id, "fells b")
    summary = evidence_state_summary(harness)
    assert summary["counts"]["open"] >= 1
    assert summary["counts"]["refuted"] == 1
    assert sum(summary["counts"].values()) == len(evidence_states(harness))
    assert set(summary["counts"]) == {"open", "supported", "refuted", "contested"}
    assert a.id in evidence_states(harness)


def test_per_cycle_buckets_artifacts_by_the_heartbeat_that_preceded_them(harness):
    """R6's 'per cycle' rides the heartbeat the scheduler already stamps
    (`["cycle", n, problem]`). Anything registered before the first heartbeat
    goes to its own bucket rather than silently into cycle 0."""

    before = art(harness, "registered before any cycle opened")
    harness.record_measure(inputs=["cycle", "0", "p-seed"])
    during = art(harness, "registered inside cycle 0")

    per_cycle = evidence_state_summary(harness)["per_cycle"]
    assert list(per_cycle)[0] == PRE_CYCLE
    assert per_cycle[PRE_CYCLE]["open"] >= 1
    assert per_cycle["0"]["open"] >= 1
    assert before.id and during.id


# --- committed roots: the reading over a record that predates it (R10) ----- #


@pytest.mark.parametrize("root", [BLIND_ROOT, PA2_ROOT])
def test_committed_roots_are_git_tracked_fixtures(root):
    assert _is_committed(root), root


def test_a_root_that_predates_the_declaration_says_so(tmp_path):
    """R10: the reading over a root with no declarations names the absence and
    reads no artifact as SUPPORTED merely because nothing attacked it."""

    harness = Harness(BLIND_ROOT, read_only=True)
    summary = evidence_state_summary(harness)

    assert summary["completeness"]["absent"] is True
    assert summary["completeness"]["reason"] == "NO_CRITICISM_DISPATCH_DECLARATION"
    assert "ran in full" in summary["completeness"]["detail"]


def test_the_blind_root_is_the_canonical_open_case():
    """Fidelity guard plus the claim: a root whose criticism produced no attack
    at all reads OPEN throughout, never SUPPORTED. Without the first two
    assertions the third proves nothing."""

    harness = Harness(BLIND_ROOT, read_only=True)
    assert harness.state.artifacts
    assert len(harness.state.att) == 0
    assert len(harness.warrants) == 0

    readings = evidence_states(harness)
    assert readings
    assert set(readings.values()) == {EvidenceState.OPEN}


def test_the_pa2_root_separates_survivors_from_untested_conjectures():
    """The reading's whole purpose, on a committed root: P-A2 at cycle 4 carries
    artifacts in three different states, where today all the non-refuted ones
    read ACCEPTED alike."""

    harness = Harness(PA2_ROOT, read_only=True)
    counts = evidence_state_summary(harness)["counts"]

    assert counts["open"] > 0
    assert counts["supported"] > 0
    assert counts["refuted"] > 0
    assert counts["open"] + counts["supported"] > counts["refuted"]


def test_reading_a_committed_root_leaves_it_byte_unchanged():
    """A writable open of a committed root repairs, i.e. destroys, the evidence
    (dr-drive-harness §5). The reading may only ever be a read."""

    before = subprocess.run(
        ["git", "status", "--porcelain", str(PA2_ROOT.relative_to(REPO))],
        cwd=REPO, capture_output=True, text=True,
    ).stdout
    evidence_state_summary(Harness(PA2_ROOT, read_only=True))
    after = subprocess.run(
        ["git", "status", "--porcelain", str(PA2_ROOT.relative_to(REPO))],
        cwd=REPO, capture_output=True, text=True,
    ).stdout
    assert before == after == ""
