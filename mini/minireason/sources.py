"""Where a mini seat's brief CONTENT comes from -- a read-only projection of
mini's record into the request the seat-shell machinery already reads.

Implements S5 (R5, R6, R12) of the mini isolation programme, on the pattern
`DR-INV-seat-section-sources` states for the full harness: a source READS the
state and the record, computes what a seat is shown, and APPENDS NOTHING. The
run's next event sequence, the bytes of `log.jsonl` and the state digest are
the same after any function here has run as before it.

WHY THIS MODULE EXISTS, measured rather than assumed
(`experiments/2026-09-05-change-mini-isolation-programme/proof/
m3_seat_shell_reach.txt`): the shipped walk runs from a live mini session with
no scheduler, no V6 transaction and no manifest policy, and fails on the first
record-backed section because mini's `State` hands out DICT projections while
the plugins read ontology objects. So the whole gap between mini and the seat
shell is one projection, and it lives here. Mini gets no second renderer.

WHAT A SOURCE HERE MAY NOT READ: an artifact's STATUS. The audit of
2026-09-05 (`experiments/2026-09-05-audit-ois-1-1-spec-drift/`, row 3) found
the full harness's default critic brief printing adjudicated status labels
into a seat's context. Within mini a criticism overturns nothing (operator,
2026-09-05), and no mini brief renders a label of any kind --
`mini/tests/test_mini_exposure.py` goes red if a source or plugin in this
module names one.
"""

from __future__ import annotations

from typing import Any, Mapping

from deepreason.llm.layout import resolve_layout_policy
from deepreason.llm.seat_sections import SectionRequestV1
from deepreason.ontology import Problem


def _frozen_criteria(root, problem_id: str) -> tuple[tuple[str, str], ...]:
    """The standard input's criteria, when the root was started from one.

    Read from the frozen record the root binds (`run-input.json`), never from
    the manifest: the criteria are bound to the root's identity but the
    reduced engine does not compile them into commitments (T1's own notice),
    so the brief is the one place a seat can be shown them at all. A root
    started from a bare question carries mini's constant process root, whose
    problem id never matches, and gets none. Absence is a legal answer here,
    not an error: a root with no readable frozen input is a root that has
    no criteria to show.
    """

    from deepreason.evidence import RunInputManifestV2, load_run_input

    try:
        frozen = load_run_input(root)
    except Exception:  # noqa: BLE001 - absence of a frozen record is legal
        return ()
    if not isinstance(frozen, RunInputManifestV2):
        return ()
    if frozen.problem.id != problem_id:
        return ()
    # Each criterion is a complete commitment record; the brief needs its id
    # and what it evaluates, as plain pairs a plugin can format without the
    # evidence package's models.
    return tuple((criterion.id, criterion.eval) for criterion in frozen.problem.criteria)


def mini_section_request(
    session,
    problem_id: str,
    *,
    target_id: str | None = None,
    supplied: Mapping[str, Any] | None = None,
    layout=None,
) -> SectionRequestV1:
    """The one read-only projection from a mini `Session` to the request the
    shipped plugins expect.

    `problem` is projected from mini's dict view into the ontology `Problem`.
    The STATE is the canonical `EpistemicState` the dict view is itself
    projected from -- the very objects the harness holds -- because the
    plugins read `Artifact` fields off it and re-validating every artifact
    from its dict would be a second copy of the record for no reason. Nothing
    is written: the request is frozen by construction, and the session is
    not touched beyond reads.

    `supplied` is the caller's: what a seat's request carries that no plugin
    can compute from the state alone (`DR-INV-seat-section-plugins`), keyed
    by the names the plugins read. A `target_id` is put there for the seats
    that scrutinise one artifact; the frozen criteria are put there for
    `mini.problem`. The caller's own mapping wins on any key it names.
    """

    problems = session.state.problems
    raw = problems.get(problem_id)
    problem = Problem.model_validate(raw) if raw is not None else None
    values: dict[str, Any] = {
        "target_id": target_id,
        "criteria": _frozen_criteria(session.root, problem_id),
    }
    if supplied:
        values.update(supplied)
    return SectionRequestV1(
        problem=problem,
        state=session.harness.state,
        commitments=dict(session.harness.commitments),
        blobs=session.blobs,
        layout=layout or resolve_layout_policy(),
        supplied=values,
    )


__all__ = ["mini_section_request"]
