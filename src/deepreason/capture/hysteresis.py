"""§14.7's deterministic hysteresis controller.

    The mode may alter lineage quotas, render slices, retrieval balance, critic
    budgets, and variation budgets. It may not add or remove attack edges,
    dependency edges, or labels directly.  (§14.7)

Three constraints shape this module and none is stylistic.

**It writes no knob.** It decides a MODE and records a POLICY ARTIFACT; the
render reads the policy. That is what keeps Theorem 14.1 structural rather than
promised, and it is the shape `Controller._emit_policy` already uses.

**It has one lever, and says so about the other four.** §14.7 names five; this
tree has render slices. `lineage_quotas`, `retrieval_balance` and
`variation_budgets` do not exist, and `critic_budgets` exists but belongs to the
allocation controller under its own envelope law -- two controllers writing one
cap is a defect this declines to create. Each absent lever is disclosed with a
resolution, reusing `allocation.open_loop_signals`'s disclose-never-die shape.

**Entry and exit are asymmetric by construction.** `Config` refuses a symmetric
or inverted pair, so no configuration turns the hysteresis into a toggle.
"""

from __future__ import annotations

import json

from deepreason.capture.diagnostics import diagnostics
from deepreason.ontology import Provenance, Rule

POLICY_SCHEMA = "capture14-hysteresis.v1"
MODES = ("normal", "diversify")

# One band per diagnostic, in `CAPTURE14_SIGNALS` order. A band is the side of a
# threshold that counts as ALARM; the thresholds themselves are reused from
# `detection.raw_flags` wherever one already exists, so a calibration lands once
# for both instrument families (G-4).
BAND_NAMES = ("sc", "ath", "debt", "rr", "var", "egr")

# What the diversify mode multiplies the slice budgets by. Widening shows MORE
# of a frame's own standing attackers and more of the departures already
# declared against it -- the frame's own crisis, which is what diversifies a
# pack posed inside its vocabulary. UNMEASURED.
SLICE_WIDENING = 2

_NO_LEVER = {
    "lineage_quotas": "no lineage quota exists on this tree; a scheduler that "
                      "capped work per lineage root would be one",
    "retrieval_balance": "retrieval balance lives on the evidence policy, not "
                         "on a knob this controller may reach",
    "critic_budgets": "the lever exists but belongs to the ALLOCATION "
                      "controller under its own envelope law; two controllers "
                      "writing one seat cap is a defect, not a feature",
    "variation_budgets": "no variation budget exists on this tree; a per-cycle "
                         "variator call cap would be one",
}


def _bands(vector, config) -> dict[str, bool]:
    """Which diagnostics are in their alarm band. `none` is never an alarm: a
    diagnostic with no data has not reported anything to be alarmed about."""

    def value(raw):
        return None if raw == "none" else float(raw)

    sc, ath, debt, rr, var, egr = (value(v) for v in vector.values())
    floor = config.LAMBDA_FLOOR
    return {
        "sc": sc is not None and sc > config.CAPTURE14_SC_CEILING,
        "ath": ath is not None and ath < config.ATTACK_ENTROPY_FLOOR,
        "debt": debt is not None and debt > config.CRIT_DEBT_CEILING,
        "rr": rr is not None and rr == 0.0,
        "var": var is not None and var == 0.0,
        "egr": egr is not None and floor is not None and egr < floor,
    }


MODE_SIGNAL = "capture14.hysteresis-mode.v1"


def policies(harness) -> tuple[str, ...]:
    """Every recorded policy artifact id, in emission order.

    Read from the mode RECEIPTS, not by sniffing artifact content: the receipt
    is the record's own statement that an artifact is a policy, and a content
    scan would also match a critic that quoted one.
    """
    return tuple(
        event.inputs[2]
        for event in harness.log.read()
        if event.rule is Rule.MEASURE
        and len(event.inputs) >= 3
        and event.inputs[0] == MODE_SIGNAL
    )


def policy_body(harness, artifact_id: str) -> dict | None:
    from deepreason import programs

    artifact = harness.state.artifacts.get(artifact_id)
    if artifact is None:
        return None
    try:
        body = json.loads(programs.content_text(artifact, harness.blobs))
    except (ValueError, UnicodeDecodeError, KeyError):
        return None
    return body if isinstance(body, dict) and body.get("schema") == POLICY_SCHEMA else None


def mode(harness) -> str:
    """The mode in force, derived from the record and stored nowhere.

    A record with no policy reads `normal`, which is what every root written
    before this rung must read -- the absence-tolerant reader lands before the
    writer emits.
    """
    for aid in reversed(policies(harness)):
        body = policy_body(harness, aid)
        if body is not None:
            return str(body.get("mode", "normal"))
    return "normal"


def slice_budgets(harness, config) -> tuple[int, int]:
    """`(attackers, departures)` for the frame slice.

    Read from the AUTHORISING policy rather than re-derived, so a replay shows
    the render the record says happened. Falls back to the configured defaults
    whenever no policy is on the record.
    """
    default = (int(config.FRAME_SLICE_ATTACKERS), int(config.FRAME_SLICE_DEPARTURES))
    for aid in reversed(policies(harness)):
        body = policy_body(harness, aid)
        if body is None:
            continue
        authorised = body.get("adjustments", {}).get("render_slices")
        if not authorised:
            return default
        return int(authorised["attackers"]), int(authorised["departures"])
    return default


def step(harness, config) -> dict | None:
    """One cycle's decision. Returns `None` when the mode does not change.

    T_enter: at least `CAPTURE14_ENTER_K` diagnostics in band.
    T_exit:  at most `CAPTURE14_EXIT_K` in band -- strictly stricter.
    """
    vector = diagnostics(harness, config)
    bands = _bands(vector, config)
    alarmed = sum(bands.values())
    current = mode(harness)
    if current == "normal":
        if alarmed < int(config.CAPTURE14_ENTER_K):
            return None
        chosen = "diversify"
    else:
        if alarmed > int(config.CAPTURE14_EXIT_K):
            return None
        chosen = "normal"
    return _emit(harness, config, vector, bands, chosen)


def _emit(harness, config, vector, bands, chosen: str) -> dict:
    adjustments: dict = {}
    if chosen == "diversify":
        adjustments["render_slices"] = {
            "attackers": int(config.FRAME_SLICE_ATTACKERS) * SLICE_WIDENING,
            "departures": int(config.FRAME_SLICE_DEPARTURES) * SLICE_WIDENING,
        }
    body = {
        "schema": POLICY_SCHEMA,
        "mode": chosen,
        "vector": json.loads(vector.model_dump_json(by_alias=True)),
        "precision": int(config.CAPTURE14_PRECISION),
        "bands": bands,
        "enter_k": int(config.CAPTURE14_ENTER_K),
        "exit_k": int(config.CAPTURE14_EXIT_K),
        "adjustments": adjustments,
        "no_lever": dict(_NO_LEVER),
    }
    policy = harness.create_artifact(
        json.dumps(body, sort_keys=True),
        codec="json",
        provenance=Provenance(role="controller"),
        rule=Rule.REFL,
    )
    harness.record_measure(inputs=[MODE_SIGNAL, chosen, policy.id])
    return {"mode": chosen, "policy": policy.id, "alarmed": sum(bands.values())}
