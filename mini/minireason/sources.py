"""Where a mini seat's brief CONTENT comes from -- a read-only projection of
mini's record into the request the seat-shell machinery already reads (S5:
R5, R6, R12), on `DR-INV-seat-section-sources`' pattern: a source READS the
state and the record and APPENDS NOTHING.

Measured, not assumed (proof/m3_seat_shell_reach.txt): the shipped walk runs
from a live mini session and fails on the first record-backed section because
mini's `State` hands out DICT projections while the plugins read ontology
objects. That one projection is the whole gap; mini gets no second renderer.

NO SOURCE HERE MAY READ AN ARTIFACT'S STATUS. The 2026-09-05 audit (row 3)
found the full harness's default critic brief printing status labels into a
seat's context; within mini a criticism overturns nothing, and no mini brief
renders a label of any kind. `mini/tests/test_mini_sources.py` walks the AST.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from pydantic import BaseModel, ConfigDict, Field

from deepreason.llm.layout import resolve_layout_policy
from deepreason.llm.seat_sections import (
    SectionRenderV1,
    SectionRequestV1,
    register_section_plugin,
)
from deepreason.ontology import Problem
from deepreason.programs import content_text
from minireason.records import MiniRecordV1, mini_records


class MiniSourceError(ValueError):
    """A typed refusal from mini's source layer: an unknown retention rule, a
    rule asked to run without the parameter it needs."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


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
        "everything": everything_so_far(session),
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


# ---------------------------------------------------------------------------
# The pool: everything a run has generated so far, in record order.
#
# Two things a mini seat can write, in one order. ARTIFACTS (conjectures) sit
# in the state's artifact map; RECORDS (commitment proposals, and from T5
# criticisms) are Measure events with a blob, deliberately outside that map so
# no authority path can read them (`minireason.records`). Both are ordered by
# the event that first wrote them, so "so far" means the record's own order.
# Computed by the SOURCE and handed to the plugin as a value, on the
# `DR-INV-seat-section-sources` pattern: the adapter reads the record, the
# plugin formats what it was given.
# ---------------------------------------------------------------------------

#: The kind an artifact is shown as, by the role its provenance carries. A
#: role not listed is shown as itself. A KIND label, never a status.
ARTIFACT_KINDS_BY_ROLE = {"conjecturer": "mini.conjecture.v1"}


def everything_so_far(session) -> tuple[MiniRecordV1, ...]:
    """Every artifact and every record this run has generated, oldest first."""

    state = session.harness.state
    # The event that first wrote each artifact, and its position among that
    # event's outputs: one batch registers several, in the order it was given.
    first_write: dict[str, tuple[int, int]] = {}
    for event in session.state.events:
        for position, output in enumerate(event.outputs):
            first_write.setdefault(output, (event.seq, position))
    keyed = []
    for artifact in state.artifacts.values():
        role = getattr(artifact.provenance.role, "value", artifact.provenance.role)
        seq, position = first_write.get(artifact.id, (artifact.provenance.event_seq, 0))
        keyed.append(
            (
                (seq, position),
                MiniRecordV1(
                    seq=seq,
                    kind=ARTIFACT_KINDS_BY_ROLE.get(role, role),
                    ref=artifact.id,
                    about=tuple(ref.target for ref in artifact.interface.refs),
                    content=content_text(artifact, session.blobs),
                ),
            )
        )
    keyed.extend(((record.seq, 0), record) for record in mini_records(session))
    return tuple(entry for _key, entry in sorted(keyed, key=lambda item: item[0]))


# ---------------------------------------------------------------------------
# Retention: what stays visible to "see everything" as the pool grows.
#
# A RULE, NEVER A VERDICT (monitor's recommendation, accepted by the operator
# 2026-09-05). What a seat is shown of the pool is decided by a declared,
# configurable rule -- recency, or a budget applied oldest-first -- and never
# by any judgement of merit, because a source that ranked would be the
# evidence side arriving in the brief by the back door. The default is
# EVERYTHING; a budget, when one is declared, withholds the OLDEST whole
# entries first and says so in the section itself, so the seat is never
# silently shown less than it was promised. A rule is registered, versioned
# and selected by id; a third rule -- novelty by the equivalence tiers, say --
# is a registration here, not an edit.
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class MiniRetentionRuleV1:
    """One registered rule. `select(ordered, sizes, budget_chars, keep_last)`
    returns `(shown, withheld)`, both in the pool's own order."""

    rule_id: str
    rule_version: str
    select: Callable[..., tuple[tuple[str, ...], tuple[str, ...]]]


def _withhold_oldest_over_budget(
    ordered: tuple[str, ...], sizes: Mapping[str, int], budget_chars: int | None
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Oldest whole entries go first, and the newest is never withheld: a
    budget that emptied the section would be a silent cut wearing a notice."""

    shown = list(ordered)
    withheld: list[str] = []
    if budget_chars is not None:
        while len(shown) > 1 and sum(sizes[aid] for aid in shown) > budget_chars:
            withheld.append(shown.pop(0))
    return tuple(shown), tuple(withheld)


def _select_everything(ordered, sizes, budget_chars, keep_last):
    return _withhold_oldest_over_budget(ordered, sizes, budget_chars)


def _select_recency(ordered, sizes, budget_chars, keep_last):
    if keep_last is None:
        raise MiniSourceError(
            "MINI_RETENTION_PARAMETER_MISSING",
            "the recency rule needs keep_last; a rule that guessed a window "
            "would be a rule the operator did not configure",
        )
    kept = tuple(ordered[-keep_last:])
    withheld = tuple(aid for aid in ordered if aid not in set(kept))
    shown, over = _withhold_oldest_over_budget(kept, sizes, budget_chars)
    return shown, withheld + over


_RETENTION_REGISTRY: dict[str, MiniRetentionRuleV1] = {}
DEFAULT_RETENTION_RULE_ID = "mini.retention.everything.v1"


def register_mini_retention_rule(rule: MiniRetentionRuleV1) -> MiniRetentionRuleV1:
    existing = _RETENTION_REGISTRY.get(rule.rule_id)
    if existing is not None and existing != rule:
        raise MiniSourceError(
            "MINI_RETENTION_RULE_CONFLICT",
            f"rule id {rule.rule_id!r} is already registered with different values",
        )
    _RETENTION_REGISTRY[rule.rule_id] = rule
    return rule


def mini_retention_rule_ids() -> tuple[str, ...]:
    return tuple(sorted(_RETENTION_REGISTRY))


def resolve_mini_retention_rule(rule_id: str) -> MiniRetentionRuleV1:
    rule = _RETENTION_REGISTRY.get(rule_id)
    if rule is None:
        raise MiniSourceError(
            "MINI_RETENTION_RULE_UNKNOWN",
            f"no mini retention rule {rule_id!r}; registered: "
            + ", ".join(mini_retention_rule_ids()),
        )
    return rule


register_mini_retention_rule(
    MiniRetentionRuleV1(DEFAULT_RETENTION_RULE_ID, "1.0.0", _select_everything)
)
register_mini_retention_rule(
    MiniRetentionRuleV1("mini.retention.recency.v1", "1.0.0", _select_recency)
)


# ---------------------------------------------------------------------------
# The mini section plugins -- registered like any other, through the same
# protocol the shipped ones satisfy. None of them reads a status.
# ---------------------------------------------------------------------------


class NoParams(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class _MiniPlugin:
    plugin_id = ""
    plugin_version = "1.0.0"
    section_id = ""
    declared_handle_kinds: tuple[str, ...] = ()
    requires: tuple[str, ...] = ()
    parameters_model: type[BaseModel] = NoParams


class MiniProblem(_MiniPlugin):
    """The standard input's problem and, when the root was started from one,
    its frozen criteria (R12). Shown to every mini seat."""

    plugin_id = "mini.problem"
    section_id = "problem"
    requires = ("problem",)

    def render(self, request: SectionRequestV1, params: BaseModel):
        problem = request.problem
        lines = [f"PROBLEM {problem.id}", problem.description]
        criteria = tuple(request.supplied.get("criteria") or ())
        if criteria:
            lines.append(
                "CRITERIA (frozen with the standard input; shown, not compiled "
                "into commitments by the reduced engine):"
            )
            lines.extend(f"- {cid}: {spec}" for cid, spec in criteria)
        return SectionRenderV1(
            section_id=self.section_id,
            text="\n".join(lines),
            provenance_refs=(problem.id,),
        )


class EverythingParams(BaseModel):
    """The retention rule and its FREE parameters. `exclude_kinds` is a KIND
    filter, not a merit one: the reseed school-policy declarations are
    scaffolding the loop writes for itself, not content a seat generated."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    retention_rule: str = DEFAULT_RETENTION_RULE_ID
    budget_chars: int | None = Field(default=None, ge=1)
    keep_last: int | None = Field(default=None, ge=1)
    exclude_kinds: tuple[str, ...] = ("seed",)


def _entry_text(index: int, entry: MiniRecordV1) -> str:
    lines = [f"[{index}] {entry.kind} {entry.ref}"]
    for target in entry.about:
        lines.append(f"    about: {target}")
    lines.append(entry.content)
    return "\n".join(lines)


class MiniEverythingSoFar(_MiniPlugin):
    """EVERYTHING generated in this run so far -- artifacts and records, in
    full, oldest first, with NO status of any kind (R6). Which entries survive
    a declared budget is the registered retention rule's decision, recorded
    in the section."""

    plugin_id = "mini.everything-so-far"
    section_id = "everything-so-far"
    parameters_model = EverythingParams

    def render(self, request: SectionRequestV1, params: EverythingParams):
        excluded = set(params.exclude_kinds)
        pool = [
            entry
            for entry in request.supplied.get("everything") or ()
            if entry.kind not in excluded
        ]
        if not pool:
            return None
        entries = {
            entry.ref: _entry_text(index, entry)
            for index, entry in enumerate(pool, start=1)
        }
        ordered = tuple(entries)
        sizes = {aid: len(text) for aid, text in entries.items()}
        rule = resolve_mini_retention_rule(params.retention_rule)
        shown, withheld = rule.select(ordered, sizes, params.budget_chars, params.keep_last)
        lines = [
            "EVERYTHING GENERATED SO FAR IN THIS RUN (every artifact, in full, "
            "oldest first; no verdict of any kind is shown):"
        ]
        if withheld:
            lines.append(
                f"WITHHELD UNDER RULE {rule.rule_id}: {len(withheld)} earlier "
                f"entr{'y' if len(withheld) == 1 else 'ies'} exist in this run "
                "and are not shown here -- " + ", ".join(withheld) + ". Treat "
                "what follows as partial; do not conclude they do not exist."
            )
        lines.extend(entries[aid] for aid in shown)
        return SectionRenderV1(
            section_id=self.section_id,
            text="\n".join(lines),
            provenance_refs=shown,
        )


class MiniTargetConjecture(_MiniPlugin):
    """The one conjecture under scrutiny, in full (R5). The critic sees THIS
    and the problem, and nothing else the run generated."""

    plugin_id = "mini.target-conjecture"
    section_id = "target-conjecture"
    requires = ("target_id",)

    def render(self, request: SectionRequestV1, params: BaseModel):
        target_id = request.supplied["target_id"]
        target = request.state.artifacts[target_id]
        return SectionRenderV1(
            section_id=self.section_id,
            text=f"TARGET CONJECTURE {target_id}\n{content_text(target, request.blobs)}",
            provenance_refs=(target_id,),
        )


class DirectiveParams(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    text: str = Field(min_length=1)


class _Placeholders(dict):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


class MiniDirective(_MiniPlugin):
    """What the seat is asked to DO, as text the LAYOUT carries. The wording
    is data in the layout entry's params, so a file-declared layout can
    change it with no code; `{name}` placeholders take the request's
    supplied values (the conjecturer's `{vs_k}`)."""

    plugin_id = "mini.directive"
    section_id = "directive"
    parameters_model = DirectiveParams

    def render(self, request: SectionRequestV1, params: DirectiveParams):
        return SectionRenderV1(
            section_id=self.section_id,
            text=params.text.format_map(_Placeholders(request.supplied)),
        )


MINI_PLUGINS = (MiniProblem, MiniEverythingSoFar, MiniTargetConjecture, MiniDirective)
for _plugin in MINI_PLUGINS:
    register_section_plugin(_plugin())


__all__ = [
    "ARTIFACT_KINDS_BY_ROLE",
    "DEFAULT_RETENTION_RULE_ID",
    "EverythingParams",
    "MINI_PLUGINS",
    "MiniRetentionRuleV1",
    "MiniSourceError",
    "everything_so_far",
    "mini_retention_rule_ids",
    "mini_section_request",
    "register_mini_retention_rule",
    "resolve_mini_retention_rule",
]
