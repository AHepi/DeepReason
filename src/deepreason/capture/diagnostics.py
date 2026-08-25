"""§14's six capture diagnostics, over a fixed SEQUENCE-NUMBER window.

`docs/POIETIC_CALCULUS_FORMALIZED.md` §14.1-§14.6, adopted as THE diagnostic
definitions by the v2 calculus program's Rung 8 (RIDER 2 / R48).

Two properties are load-bearing and neither is decoration.

**The window is sequence numbers.** `W_m(n) = {max(1, n-m+1) .. n}`. Not
wall-clock -- §15.1 forbids it entering any verdict or serialization -- and not
an event count, which is what `harness.recent_semantic_events` and
`capture/detection.py` use. That difference is why these six are a DISTINCT
FAMILY from the Rung 2 detection signals and from `detection.adjudicator_
metrics`, rather than a re-implementation of either (V-6; `DR-INV-signal-
contract`).

**Canonical rounding at a declared precision is part of the policy (A10),** not
an implementation detail: the precision travels in the emitted payload, so a
reader re-derives the number from the record without knowing this module's
defaults. Absence renders as `none` and never as `0.0` -- a zero that means "no
data" is indistinguishable from a measured zero, which is the reading error
these six exist to prevent.

Every one of the six prices ATTENTION and none may reach a label: two states
with identical artifacts, attacks and dependencies but different diagnostic
values have identical labels (Theorem 14.1).
"""

from __future__ import annotations

import json
import math
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from deepreason.canonical import canonical_json, sha256_hex
from deepreason.ontology import Rule, Status

# Fixed order, and the emission order. The six are computed from ONE vector so
# they describe one window; six independent computations could straddle a cycle
# boundary and describe different ones.
CAPTURE14_SIGNALS: tuple[str, ...] = (
    "capture14.stream-contraction.v1",
    "capture14.attack-target-entropy.v1",
    "capture14.criticism-debt.v1",
    "capture14.reinstatement-rate.v1",
    "capture14.validity-attack-rate.v1",
    "capture14.exogenous-grounding-ratio.v1",
)


# --- the window ---------------------------------------------------------------


def window(harness, m: int):
    """`W_m(n)` as a range over sequence numbers, inclusive at both ends.

    `n` is the highest APPLIED seq. §14 writes `max(1, n-m+1)` because its
    sequence numbers are 1-based; this log's are 0-based, so the clamp is at 0.
    Keeping the literal 1 would silently drop the run's own first registration
    from every window, which is a difference in indexing convention masquerading
    as a definition.
    """
    n = harness._next_seq - 1
    if n < 0:
        return range(0, 0)
    return range(max(0, n - max(1, m) + 1), n + 1)


def _events(harness, w):
    """Events whose seq lies in `w`.

    `_events_since` is the tail-backed reader: the in-memory tail covers a
    default window, and only a window wider than the tail pays a log read. A
    from-scratch log walk per cycle was measured quadratic for `transitions()`
    and would be the same mistake here.
    """
    if not w:
        return []
    return [e for e in harness._events_since(w.start) if e.seq in w]


def conjectures(harness, w) -> tuple[str, ...]:
    """`C_{m,n}`: artifacts registered by a CONJ event inside the window.

    `Rule.CONJ` is what `rules/conj.py` uses for a candidate; the default
    `Rule.REGISTER` is the bookkeeping path. Reading every registration would
    count nu artifacts, critics and paperwork as conjectures and would make SC
    a measure of the harness's own bookkeeping.
    """
    return tuple(
        sorted(
            aid
            for event in _events(harness, w)
            if event.rule is Rule.CONJ
            for aid in event.state_diff.a_add
        )
    )


def carried(harness, w) -> tuple[tuple[str, str], ...]:
    """Attacks NEWLY CARRIED inside the window, as `(carrier, warrant id)`.

    §14.2's own primitive, and the one that separates this family from the
    shipped `criticism.attack-target-entropy.v1`: `carry_add` is the declared
    carriage, `att_add` is the materialized edge set after closure. The log
    records them separately, so they are two quantities rather than two
    readings of one.
    """
    return tuple(
        sorted(
            pair
            for event in _events(harness, w)
            for pair in event.state_diff.carry_add
        )
    )


# --- A10: canonical rounding at a declared precision ---------------------------


def canonical(value: float | None, precision: int) -> Decimal | None:
    """ROUND_HALF_EVEN at `precision` decimal places.

    HALF_EVEN rather than HALF_UP because a tie-break that always rounds away
    from zero drifts a series upward, and because it is the tie-break every
    machine agrees on. The precision is the POLICY's, never this module's.
    """
    if value is None:
        return None
    quantum = Decimal(1).scaleb(-precision)
    return Decimal(repr(float(value))).quantize(quantum, rounding=ROUND_HALF_EVEN)


def render(value: float | None, precision: int) -> str:
    """The emitted spelling. `none` for absence -- never `0.000000`."""
    rounded = canonical(value, precision)
    return "none" if rounded is None else format(rounded, "f")


# --- §14.1 stream contraction --------------------------------------------------


def _signature(harness, aid: str) -> str:
    """`phi_L(a)`: a deterministic BEHAVIOURAL signature.

    Three parts, per §14: the commitment-verdict vector, the declared
    relations, and the problem lineage.

    The relations enter as their ROLE COUNTS, never as their targets. Every
    artifact is content-addressed and therefore unique, so a signature carrying
    ref targets would be unique for every conjecture and SC would read 0 on
    every record ever made -- an instrument that cannot fire, which is what
    `docs_verify --audit` refuses for a doc check and what this module refuses
    for a diagnostic.
    """
    from deepreason.calculus.nomination import lineage_root

    artifact = harness.state.artifacts.get(aid)
    if artifact is None:
        return ""
    verdicts = sorted(
        (w.commitment, w.verdict or "")
        for w in harness.warrants.values()
        if w.target == aid and w.commitment
    )
    roles: dict[str, int] = {}
    for ref in artifact.interface.refs:
        role = ref.role.value if hasattr(ref.role, "value") else str(ref.role)
        roles[role] = roles.get(role, 0) + 1
    lineages = sorted(
        {
            lineage_root(harness, pid) or pid
            for candidate, pid in harness.state.addr
            if candidate == aid
        }
    )
    return sha256_hex(
        canonical_json(
            {
                "verdicts": [list(pair) for pair in verdicts],
                "relations": roles,
                "lineage": lineages,
            }
        )
    )


def stream_contraction(harness, w) -> float | None:
    """`SC = 1 - (N_eff - 1)/(N - 1)`, `N_eff = 1/sum(p_z^2)`.

    Absent below two conjectures: with `N = 1` the formula divides by zero, and
    "one conjecture" is not a contracted stream, it is no stream.
    """
    ids = conjectures(harness, w)
    n = len(ids)
    if n < 2:
        return None
    counts: dict[str, int] = {}
    for aid in ids:
        key = _signature(harness, aid)
        counts[key] = counts.get(key, 0) + 1
    n_eff = 1.0 / sum((c / n) ** 2 for c in counts.values())
    return 1.0 - (n_eff - 1.0) / (n - 1.0)


# --- §14.2 attack-target entropy ------------------------------------------------


def attack_target_entropy(harness, w) -> float | None:
    """Normalised Shannon entropy of newly carried attacks over their targets.

    0.0 covers both "one distinct target" and "log |T| = 0", which are the same
    state: a window whose criticism all landed in one place. Absent when the
    window carried no attack at all -- which is NOT the same state, and reading
    it as 0.0 would say criticism was maximally concentrated when none existed.
    """
    targets = [
        harness.warrants[wid].target
        for _, wid in carried(harness, w)
        if wid in harness.warrants
    ]
    if not targets:
        return None
    counts: dict[str, int] = {}
    for target in targets:
        counts[target] = counts.get(target, 0) + 1
    if len(counts) < 2:
        return 0.0
    total = len(targets)
    entropy = -sum((c / total) * math.log(c / total) for c in counts.values())
    return entropy / math.log(len(counts))


# --- §14.3 criticism debt --------------------------------------------------------


def _live_attackers(harness, aid: str) -> tuple[str, ...]:
    """Attackers that are themselves unrefuted. A refuted critic is not live
    criticism -- counting it would report an artifact as under criticism by an
    argument the tree has already defeated."""
    return tuple(
        sorted(
            attacker
            for attacker, target in harness.state.att
            if target == aid and harness.state.status.get(attacker) is not Status.REFUTED
        )
    )


def younger_than(harness, h: int) -> frozenset[str]:
    """Artifacts registered within the last `h` sequence numbers.

    Computed as the COMPLEMENT of what §14.3 wants, and deliberately: asking
    "which artifacts are old" needs every artifact's registration seq, which is
    a whole-log read per cycle. Asking "which are young" needs only the events
    inside the age floor, which the in-memory tail already holds. Everything
    not named here is, by definition, at least `h` old.

    `Provenance.event_seq` is NOT the source. It defaults to 0 and almost no
    caller sets it, so reading it would make every artifact maximally old and
    the age floor would discriminate nothing -- a diagnostic that cannot fire.
    """
    n = harness._next_seq - 1
    if h <= 0 or n < 0:
        return frozenset()
    return frozenset(
        aid
        for event in harness._events_since(max(0, n - h + 1))
        for aid in event.state_diff.a_add
    )


def criticism_debt(harness, w, h: int) -> float | None:
    """Of the unrefuted artifacts at least `h` seqs old, the fraction with no
    live attacker.

    Absent when nothing is old enough. Returning 0.0 there would say "no old
    artifact lacks criticism" on a record that has no old artifacts, which
    reads as health and is really youth.
    """
    young = younger_than(harness, h)
    old = [
        aid
        for aid, status in harness.state.status.items()
        if status is not Status.REFUTED and aid not in young
    ]
    if not old:
        return None
    return sum(1 for aid in old if not _live_attackers(harness, aid)) / len(old)


# --- §14.4 reinstatement rate ------------------------------------------------------


def reinstatement_rate(harness, w) -> float | None:
    """`R->U` label changes in the window, per criticism registered in it.

    `N_crit` is newly carried attacks -- the same primitive §14.2 uses -- so the
    two rates are commensurable readings of one window rather than two windows
    that happen to share a name.
    """
    n_crit = len(carried(harness, w))
    if not n_crit:
        return None
    reinstated = sum(
        1
        for seq, _, old, new in harness.transitions()
        if seq in w and old == Status.REFUTED.value and new != Status.REFUTED.value
    )
    return reinstated / n_crit


# --- §14.5 validity-node attack rate -------------------------------------------------


def validity_attack_rate(harness, w) -> float | None:
    """Of the attacks newly carried in the window, the share whose target is a
    warrant-validity artifact. Absent when the window carried no attack."""
    pairs = carried(harness, w)
    if not pairs:
        return None
    nodes = {w_.validity_node for w_ in harness.warrants.values()}
    on_nodes = sum(
        1
        for _, wid in pairs
        if wid in harness.warrants and harness.warrants[wid].target in nodes
    )
    return on_nodes / len(pairs)


# --- §14.6 exogenous grounding ratio ---------------------------------------------------


def _is_external_anchor(harness, aid: str) -> bool:
    """A terminal leaf that is contact with something outside the judgment loop.

    Three kinds, and the order is cheapest-first. A budgeted program check: an
    interface commitment the evaluator can actually run, and not a rubric --
    `grounding_lambda` already draws that exact line. A recorded evidence item:
    an import-role artifact, which is this tree's own marker for material that
    entered from outside (`research/backends`). An appellate ruling: recognised
    by CONTENT (a `precedent` object) rather than by who wrote it, so a ruling
    stays a ruling however it was entered.
    """
    from deepreason import programs

    artifact = harness.state.artifacts.get(aid)
    if artifact is None:
        return False
    for cid in artifact.interface.commitments:
        kappa = harness.commitments.get(cid)
        if (
            kappa is not None
            and programs.evaluable(kappa)
            and not kappa.eval.startswith("rubric:")
        ):
            return True
    role = getattr(getattr(artifact, "provenance", None), "role", None)
    if role == "import":
        return True
    try:
        body = json.loads(programs.content_text(artifact, harness.blobs))
    except (ValueError, TypeError, UnicodeDecodeError, KeyError):
        return False
    return isinstance(body, dict) and "precedent" in body


def _externally_grounded(harness, warrant_id: str) -> bool:
    """Every terminal leaf of the warrant's validity lineage is an anchor.

    The lineage is `w -> nu(w) -> the validity nodes of the warrants nu itself
    carries -> ...`. A node already visited is a CLOSED LOOP -- mutually
    dependent judgments -- and is never an anchor, which is exactly the state
    §14.6 measures the absence of.
    """
    warrant = harness.warrants.get(warrant_id)
    if warrant is None:
        return False
    seen: set[str] = set()
    frontier = [warrant.validity_node]
    grounded = True
    while frontier:
        aid = frontier.pop()
        if aid in seen:
            return False
        seen.add(aid)
        if _is_external_anchor(harness, aid):
            continue
        artifact = harness.state.artifacts.get(aid)
        onward = [
            harness.warrants[wid].validity_node
            for wid in (artifact.warrants if artifact is not None else ())
            if wid in harness.warrants
        ]
        if not onward:
            grounded = False
            continue
        frontier.extend(onward)
    return grounded


def exogenous_grounding_ratio(harness, w) -> float | None:
    """Of the live warrants registered in the window, the share externally
    grounded. A warrant is live when its carrier is not refuted -- a warrant
    carried only by a defeated critic is not doing any grounding."""
    live = sorted(
        {
            wid
            for carrier, wid in carried(harness, w)
            if harness.state.status.get(carrier) is not Status.REFUTED
        }
    )
    if not live:
        return None
    return sum(1 for wid in live if _externally_grounded(harness, wid)) / len(live)


# --- the vector -------------------------------------------------------------------------


class Capture14VectorV1(BaseModel):
    """One window's six diagnostics, already canonically rounded.

    The values are STRINGS, not floats, and that is the A10 requirement rather
    than a serialization taste: a float's repr is the machine's, a
    fixed-precision decimal string is the policy's. The window and precision
    travel with them so the record states what was measured and how.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_: Literal["capture14-vector.v1"] = Field(
        default="capture14-vector.v1", alias="schema"
    )
    n: int
    m: int
    h: int
    precision: int
    sc: str
    ath: str
    debt: str
    rr: str
    var: str
    egr: str

    def values(self) -> tuple[str, ...]:
        """The six, in `CAPTURE14_SIGNALS` order."""
        return (self.sc, self.ath, self.debt, self.rr, self.var, self.egr)


def diagnostics(harness, config) -> Capture14VectorV1:
    """All six over one window, computed once."""
    m = int(config.CAPTURE14_WINDOW)
    h = int(config.CAPTURE14_AGE_FLOOR)
    precision = int(config.CAPTURE14_PRECISION)
    w = window(harness, m)
    return Capture14VectorV1(
        n=harness._next_seq - 1,
        m=m,
        h=h,
        precision=precision,
        sc=render(stream_contraction(harness, w), precision),
        ath=render(attack_target_entropy(harness, w), precision),
        debt=render(criticism_debt(harness, w, h), precision),
        rr=render(reinstatement_rate(harness, w), precision),
        var=render(validity_attack_rate(harness, w), precision),
        egr=render(exogenous_grounding_ratio(harness, w), precision),
    )


# --- G-4/G-5: the capture cost of elevation ------------------------------------------------

CONDITIONING_SIGNAL = "capture14.promotion-conditioning.v1"


def _conditioning_records(harness) -> tuple[tuple[str, str, str], ...]:
    """`(phase, assertion id, payload digest)` for every conditioning record."""
    return tuple(
        (event.inputs[1], event.inputs[2], event.inputs[3])
        for event in harness.log.read()
        if event.rule is Rule.MEASURE
        and len(event.inputs) >= 4
        and event.inputs[0] == CONDITIONING_SIGNAL
    )


def conditioning_payload(harness, digest: str) -> dict:
    return json.loads(harness.blobs.get(digest))


def owed_after(harness) -> tuple[str, ...]:
    """Elevations with a `before` and no `after`, in elevation order.

    Derived from the LOG rather than from scheduler state: a resumed run owes
    exactly what the record says it owes, and no in-process variable can
    disagree with it.
    """
    records = _conditioning_records(harness)
    paid = {aid for phase, aid, _ in records if phase == "after"}
    return tuple(
        aid for phase, aid, _ in records if phase == "before" and aid not in paid
    )


def _emit_conditioning(harness, config, assertion_id: str, phase: str, scope) -> None:
    from deepreason.calculus.standing import framed_problem_ids

    payload = {
        "phase": phase,
        "assertion": assertion_id,
        "conditioned_problems": len(framed_problem_ids(harness, scope)) if scope else 0,
        "vector": json.loads(diagnostics(harness, config).model_dump_json(by_alias=True)),
    }
    digest = harness.blobs.put(canonical_json(payload))
    harness.record_measure(inputs=[CONDITIONING_SIGNAL, phase, assertion_id, digest])


def promotion_conditioning(harness, config) -> None:
    """G-5's pair: pay any owed `after`, then record a `before` per new
    elevation.

    The order matters and is not arbitrary. Paying first means an elevation
    that happens in this same cycle does not have its own `before` mistaken for
    an owed `after`; recording second means the `before` is taken with the new
    grant already on the record, which is what makes `conditioned_problems`
    the size of the surface the elevation actually created.
    """
    from deepreason.calculus.standing import consulted

    grants = {grant.assertion_id: grant for grant in consulted(harness)}
    for assertion_id in owed_after(harness):
        grant = grants.get(assertion_id)
        _emit_conditioning(
            harness, config, assertion_id, "after", grant.scope if grant else None
        )
    seen = {aid for _, aid, _ in _conditioning_records(harness)}
    for assertion_id, grant in sorted(grants.items()):
        if assertion_id not in seen:
            _emit_conditioning(harness, config, assertion_id, "before", grant.scope)


def emit(harness, config) -> None:
    """One cycle's §14 emission: the six, then G-5's pair, then the controller.

    The vector is computed ONCE and emitted six times. Six independent
    computations could straddle a registration and describe different windows,
    and six numbers describing different states of the record are not a vector.
    """
    from deepreason.capture import hysteresis

    vector = diagnostics(harness, config)
    for signal, value in zip(CAPTURE14_SIGNALS, vector.values()):
        # The window SIZE travels in the inputs; the window's END does not.
        # `n` is the log's length INCLUDING bookkeeping, so two runs with equal
        # authoritative surfaces and different event counts would emit
        # different bytes for one epistemic state -- which is what the v6
        # shadow comparison caught. The record already says `n`: it is the seq
        # of the measure event carrying the value.
        harness.record_measure(inputs=[signal, value, str(vector.m)])
    promotion_conditioning(harness, config)
    hysteresis.step(harness, config)
