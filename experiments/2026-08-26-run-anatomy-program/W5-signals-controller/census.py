"""W5 / D7 — the signals and allocation-controller census.

Read-only over committed run roots. Emits SIGNAL_CENSUS.json,
CONTROLLER_CENSUS.json and LAW_CHECK.json; `render.py` turns those into the
committed tables. Nothing here opens a root writable, and nothing here
reads a number it did not derive from `log.jsonl`, `objects/`,
`progress.jsonl`, `run-status.json`, `run-manifest.json` or
`REPLAY_VALIDATION.json`.

Three hazards this instrument is built around (GOAL.md "Three hazards"):

H1  A controller DECISION is a `Refl` event whose output artifact carries
    `provenance.role == "controller"` — not a Measure event (ERRATA E43).
H2  Four of the five `allocation.POLICY_SIGNALS` are computed in-process and
    are never emitted as Measure values. Their silence is the expected
    state, and the census says so with the mechanism named.
H3  A log event carries no cycle. Cycles are re-derived from the `cycle`
    Measure tag and cross-checked against `progress.jsonl`; a disagreement
    is reported, never silently resolved.
"""

import json
import os
import sys
from collections import Counter, defaultdict
from types import SimpleNamespace

from deepreason import allocation, controller
from deepreason.signals import PREFIX_DECLARATIONS, SIGNAL_DECLARATIONS

HERE = os.path.dirname(os.path.abspath(__file__))
PROGRAM = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(PROGRAM))

# The Rung 1b-ii signal-consumption tranche landed 2026-08-21; the census
# population is every inventoried root whose first event is later than that.
POPULATION_CUTOFF = "2026-08-22"

# Signals a committed consumer actually READS, with the reader named. Derived
# from the source, not guessed: a signal nothing reads cannot have its
# staleness bound violated, because nothing believes it for any length of time.
# Signals a committed consumer actually READS, with the reader named and the
# reliance window stated. Read out of the source and verified by reading it,
# not inferred from the name: a signal nothing reads cannot have its staleness
# bound violated, because nothing believes it for any length of time.
# `signal_occurrences()` below re-derives the raw evidence for this table so a
# reader can check it rather than trust it.
CONSUMERS = {
    "dropped-call": {
        "reader": "controller.Controller._new_transport_drops "
                  "(TRANSPORT_DROP_TAG, matched on reason)",
        "reliance": "within the step that consumes it; the counter is "
                    "monotonic and never re-reads an old drop",
    },
    "controller-authority": {
        "reader": "controller.Controller._rehydrate_process_state "
                  "(episode dedupe on resume)",
        "reliance": "the whole run — rehydration reads the LAST record "
                    "whatever its age",
    },
    "capture14.hysteresis-mode.v1": {
        "reader": "capture.hysteresis.policies() -> mode() / "
                  "slice_budgets(), reached from calculus/render.py",
        "reliance": "the whole run — `reversed(policies(harness))` takes the "
                    "most recent receipt whatever its age",
    },
}

# Units whose value is a LEVEL that persists between emissions. For these a
# per-cycle hole means a consumer reading the level reads a stale one, so
# coverage is the right test. An `event` unit is an OCCURRENCE: its absence in
# a cycle is information, not staleness, and the question there is how old the
# last occurrence was when something believed it.
LEVEL_UNITS = ("ratio", "count", "tokens")


# --------------------------------------------------------------------------
# reading the record
# --------------------------------------------------------------------------

def read_log(root):
    with open(os.path.join(root, "log.jsonl"), encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def read_json(path, default=None):
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return default


_ARTIFACT_INDEX = {}


def artifact_index(root):
    """ARTIFACT id -> stored object, for one root.

    The filename under `objects/artifact/` is the OBJECT digest, not the
    artifact id — the artifact's own id lives at `data.id` inside. Looking a
    policy artifact up by the id the `Refl` event names therefore needs this
    index; joining on the filename silently finds nothing, which reads as "the
    controller never ran".
    """
    if root in _ARTIFACT_INDEX:
        return _ARTIFACT_INDEX[root]
    index = {}
    directory = os.path.join(root, "objects", "artifact")
    try:
        names = os.listdir(directory)
    except OSError:
        names = []
    for name in names:
        if not name.endswith(".json"):
            continue
        obj = read_json(os.path.join(directory, name))
        if not isinstance(obj, dict):
            continue
        data = obj.get("data") or {}
        key = data.get("id") or obj.get("id")
        if key:
            index[key] = obj
    _ARTIFACT_INDEX[root] = index
    return index


def artifact_body(root, artifact_id):
    """One artifact object by ARTIFACT id, or None."""
    return artifact_index(root).get(artifact_id)


def classify_signal(name):
    """EXACT / PREFIX:<family> / UNDECLARED for one Measure inputs[0]."""
    if name in SIGNAL_DECLARATIONS:
        return "exact", name
    for prefix in PREFIX_DECLARATIONS:
        if name.startswith(prefix):
            return "prefix", prefix
    return "undeclared", name


def declaration_for(kind, key):
    table = SIGNAL_DECLARATIONS if kind == "exact" else PREFIX_DECLARATIONS
    decl = table.get(key)
    if decl is None:
        return {"unit": None, "staleness": None}
    return {"unit": decl.unit, "staleness": decl.staleness}


# --------------------------------------------------------------------------
# the manifest side: routes, seat instances, envelopes
# --------------------------------------------------------------------------

def manifest_routes(root):
    """role -> tuple of route objects, from run-manifest.json.

    Rendered as SimpleNamespace so `allocation.route_cap_for_knob` — the ONE
    derivation the writer and replay validation share — can be called on it
    unmodified. Re-deriving the rule here instead would be the second copy
    INV-signal-contract exists to forbid.
    """
    manifest = read_json(os.path.join(root, "run-manifest.json"), {}) or {}
    roles = manifest.get("roles") or {}
    out = {}
    for role, routes in roles.items():
        out[role] = tuple(SimpleNamespace(**route) for route in (routes or ()))
    return out


def bound_roles(routes):
    """Roles with at least one route. `manifest.roles` membership is NOT
    seat-boundness — the compiler emits all canonical keys and an
    unconfigured role's value is an empty tuple (INV-signal-contract Traps)."""
    return tuple(role for role, seats in routes.items() if seats)


def seat_instances(routes):
    """seat-instance name -> (role, seat index, route), the unit of allocation."""
    out = {}
    for role, seats in routes.items():
        for index, route in enumerate(seats):
            out[allocation.seat_instance(role, index, len(seats))] = (
                role, index, route,
            )
    return out


def lease_ceiling(routes, instance):
    """The E43 bound: the largest cap the route firewall will admit.

    Mirrors `Controller._lease_ceiling` — a route declaring
    `context_window_tokens` has its leased `max_tokens` as a hard ceiling; a
    route declaring none has no ceiling.
    """
    bound = seat_instances(routes).get(instance)
    if bound is None:
        return None
    route = bound[2]
    if getattr(route, "context_window_tokens", None) is None:
        return None
    return getattr(route, "max_tokens", None)


# --------------------------------------------------------------------------
# per-root census
# --------------------------------------------------------------------------

def census_root(root_path):
    root = os.path.join(REPO, root_path)
    routes = manifest_routes(root)
    instances = seat_instances(routes)

    cycle = -1                     # -1 = before the first `cycle` tag (setup)
    cycles_seen = set()
    heartbeats = []                # (seq, cycle) — the scheduler's own segmentation
    emissions = Counter()          # signal key -> count
    per_cycle = defaultdict(Counter)   # signal key -> {cycle: count}
    undeclared = Counter()
    payload_families = Counter()   # hv / reach Measure events (no signal tag)
    first_seq = {}                 # signal key -> first seq it appeared at

    decisions = []                 # ALLOCATION controller policies, in log order
    hysteresis = []                # capture/hysteresis.py §14.7 policies
    authority = []                 # controller-authority records
    rehydrations = []
    holds = []
    drops = []                     # dropped-call events

    # effect substrate: every dispatch's own max_tokens / timeout, by seat
    dispatches = []                # {seq, cycle, instance, max_tokens, ...}

    status_events = []             # every event carrying a status_changed
    signal_event_seqs = set()      # Measure events carrying a declared signal
    controller_event_seqs = set()  # controller Measure + Refl events

    conj_per_cycle = Counter()
    crit_per_cycle = Counter()

    for event in read_log(root):
        seq = event["seq"]
        rule = event.get("rule")
        inputs = event.get("inputs") or []
        diff = event.get("state_diff") or {}

        if rule == "Measure" and inputs and inputs[0] == "cycle":
            try:
                cycle = int(inputs[1])
                cycles_seen.add(cycle)
                heartbeats.append((seq, cycle))
            except (IndexError, ValueError):
                pass

        if rule == "Conj":
            conj_per_cycle[cycle] += 1
        if rule == "Crit":
            crit_per_cycle[cycle] += 1

        if diff.get("status_changed"):
            status_events.append({
                "seq": seq, "rule": rule, "cycle": cycle,
                "signal": inputs[0] if (rule == "Measure" and inputs) else None,
                "changed": diff["status_changed"],
            })

        # --- signal production ------------------------------------------- #
        if rule == "Measure":
            if not inputs:
                payload_families["measure-without-inputs"] += 1
            elif diff.get("hv_set"):
                payload_families["hv-estimate"] += 1
            elif diff.get("reach_set"):
                payload_families["reach-sweep"] += 1
            else:
                kind, key = classify_signal(inputs[0])
                if kind == "undeclared":
                    undeclared[inputs[0]] += 1
                else:
                    emissions[key] += 1
                    per_cycle[key][cycle] += 1
                    first_seq.setdefault(key, seq)
                    signal_event_seqs.add(seq)

                if inputs[0] == controller.TRANSPORT_DROP_TAG:
                    drops.append({
                        "seq": seq, "cycle": cycle,
                        "reason": inputs[1] if len(inputs) > 1 else "",
                        "transport_match": any(
                            m in (inputs[1] if len(inputs) > 1 else "")
                            for m in controller.TRANSPORT_REASONS
                        ),
                    })
                if inputs[0] == "controller-authority":
                    # `Controller._state_authority` writes exactly
                    # ["controller-authority", scope, payload].
                    payload = read_json_str(
                        inputs[2] if len(inputs) > 2 else "")
                    authority.append({
                        "seq": seq, "cycle": cycle,
                        "scope": inputs[1] if len(inputs) > 1 else None,
                        "steerable": (payload or {}).get("steerable"),
                        "unsteerable": (payload or {}).get("unsteerable"),
                        "open_loop": (payload or {}).get("open_loop"),
                        "payload_present": payload is not None,
                    })
                    controller_event_seqs.add(seq)
                if inputs[0] == "controller-rehydration":
                    rehydrations.append({
                        "seq": seq, "cycle": cycle,
                        "policy": inputs[1] if len(inputs) > 1 else None,
                        "changed": read_json_str(
                            inputs[2] if len(inputs) > 2 else ""),
                    })
                    controller_event_seqs.add(seq)
                if inputs[0].startswith("controller-hold:"):
                    holds.append({
                        "seq": seq, "cycle": cycle, "tag": inputs[0],
                        "policy": inputs[1] if len(inputs) > 1 else None,
                    })
                    controller_event_seqs.add(seq)

        # --- controller decisions (H1: Refl, not Measure) ------------------ #
        if rule == "Refl":
            for artifact_id in event.get("outputs") or []:
                obj = artifact_body(root, artifact_id)
                if obj is None:
                    continue
                data = obj.get("data") or {}
                provenance = data.get("provenance") or {}
                if provenance.get("role") != "controller":
                    continue
                ref = data.get("content_ref") or ""
                body = None
                if ref.startswith("inline:"):
                    body = read_json_str(ref[len("inline:"):])
                # TWO controllers share `provenance.role == "controller"`.
                # The allocation controller's policy is the one carrying a
                # `knobs` mapping — the same discriminator
                # `Controller._policy_payload` uses; `capture/hysteresis.py`'s
                # §14.7 policy carries `mode`/`bands` instead. Counting the
                # second as an allocation decision inflates every table here.
                family = (
                    "allocation-policy"
                    if isinstance((body or {}).get("knobs"), dict)
                    else "capture14-hysteresis-policy"
                )
                record = {
                    "seq": seq, "log_cycle": cycle, "artifact": artifact_id,
                    "family": family,
                    "policy_cycle": (body or {}).get("cycle"),
                    "knobs": (body or {}).get("knobs") or {},
                    "evidence": (body or {}).get("evidence") or {},
                    "parsed": body is not None,
                }
                if family == "allocation-policy":
                    decisions.append(record)
                else:
                    hysteresis.append(record)
                controller_event_seqs.add(seq)

        # --- dispatch substrate for the effect table ----------------------- #
        call = event.get("llm")
        if call:
            trace = call.get("attempt_trace") or []
            for attempt in trace:
                seat = attempt.get("seat", 0)
                role = call.get("role")
                seats_bound = len(routes.get(role) or ()) or 1
                dispatches.append({
                    "seq": seq, "cycle": cycle, "role": role,
                    "instance": allocation.seat_instance(role, seat, seats_bound),
                    "max_tokens": attempt.get("max_tokens"),
                    "timeout_s": attempt.get("timeout_s"),
                    # `attempt.tokens` is prompt+completion for that leg;
                    # `completion_tokens` is the call's completion side alone.
                    # Only the second can be compared against a completion cap.
                    "tokens": attempt.get("tokens"),
                    "completion_tokens": call.get("completion_tokens"),
                    "truncated": bool(call.get("truncated")),
                    "attempts": call.get("attempts"),
                })
            if not trace:
                role = call.get("role")
                seats_bound = len(routes.get(role) or ()) or 1
                dispatches.append({
                    "seq": seq, "cycle": cycle, "role": role,
                    "instance": allocation.seat_instance(role, 0, seats_bound),
                    "max_tokens": None, "timeout_s": None,
                    "tokens": call.get("tokens"),
                    "completion_tokens": call.get("completion_tokens"),
                    "truncated": bool(call.get("truncated")),
                    "attempts": call.get("attempts"),
                })

    status_json = read_json(os.path.join(root, "run-status.json"), {}) or {}
    replay = read_json(os.path.join(root, "REPLAY_VALIDATION.json"), {}) or {}

    return {
        "root": root_path,
        "run_id": status_json.get("run_id"),
        "state": status_json.get("state"),
        "stop_reason": status_json.get("stop_reason"),
        "cycles_seen": sorted(cycles_seen),
        "heartbeats": heartbeats,
        "hysteresis_policies": hysteresis,
        "progress_cycle_max": progress_cycle_max(root),
        "replay_ok": replay.get("ok", replay.get("valid")),
        "bound_roles": sorted(bound_roles(routes)),
        "seat_instances": sorted(instances),
        "emissions": dict(emissions),
        "per_cycle": {k: dict(v) for k, v in per_cycle.items()},
        "first_seq": first_seq,
        "undeclared": dict(undeclared),
        "payload_families": dict(payload_families),
        "decisions": decisions,
        "authority": authority,
        "rehydrations": rehydrations,
        "holds": holds,
        "drops": drops,
        "status_events": status_events,
        "signal_event_seqs": sorted(signal_event_seqs),
        "controller_event_seqs": sorted(controller_event_seqs),
        "conj_per_cycle": dict(conj_per_cycle),
        "crit_per_cycle": dict(crit_per_cycle),
        "dispatches": dispatches,
        "routes": {
            role: [
                {
                    "max_tokens": getattr(r, "max_tokens", None),
                    "context_window_tokens": getattr(
                        r, "context_window_tokens", None),
                    "timeout_s": getattr(r, "timeout_s", None),
                    "model_id": getattr(r, "model_id", None),
                }
                for r in seats
            ]
            for role, seats in routes.items()
        },
        "expected_open_loop": list(
            allocation.open_loop_signals(bound_roles(routes))
        ),
    }


def read_json_str(text):
    try:
        value = json.loads(text)
    except (TypeError, ValueError):
        return None
    return value if isinstance(value, dict) else None


def progress_cycle_max(root):
    """H3 cross-check: the highest cycle progress.jsonl claims."""
    path = os.path.join(root, "progress.jsonl")
    best = None
    try:
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                value = row.get("cycle")
                if isinstance(value, int):
                    best = value if best is None else max(best, value)
    except OSError:
        return None
    return best


# --------------------------------------------------------------------------
# decision analysis: envelope, anchor, lease ceiling, effect
# --------------------------------------------------------------------------

def scheduler_cycle_for(heartbeats, seq):
    """The scheduler cycle a controller decision belongs to.

    `Scheduler.step` calls `controller.step()` BEFORE it writes the
    `["cycle", n, problem]` heartbeat, so a policy artifact lands in the log
    ahead of the heartbeat for its own cycle. Attributing it to the LAST
    heartbeat seen would put every decision one cycle early. The NEXT
    heartbeat is the decision's cycle; None means the run ended before one
    was written.
    """
    return next((cycle for hb_seq, cycle in heartbeats if hb_seq > seq), None)


def analyse_decisions(root_census):
    root = os.path.join(REPO, root_census["root"])
    routes = manifest_routes(root)
    dispatches = root_census["dispatches"]
    heartbeats = [tuple(h) for h in root_census["heartbeats"]]
    drops = root_census["drops"]
    route_caps = {
        cap
        for seats in root_census["routes"].values()
        for route in seats
        if (cap := route.get("max_tokens")) is not None
    }
    rows = []

    for decision in root_census["decisions"]:
        seq = decision["seq"]
        for knob, value in sorted(decision["knobs"].items()):
            instance = knob.split(":", 1)[1] if knob.startswith("cap:") else None
            anchor = allocation.route_cap_for_knob(routes, knob)
            envelope = controller.cap_envelope(knob, anchor)
            ceiling = lease_ceiling(routes, instance) if instance else None

            before = [
                d for d in dispatches
                if d["seq"] < seq and (instance is None or d["instance"] == instance)
            ]
            after = [
                d for d in dispatches
                if d["seq"] > seq and (instance is None or d["instance"] == instance)
            ]
            field = "timeout_s" if knob == "timeout:transport" else "max_tokens"

            rows.append({
                "root": root_census["root"],
                "seq": seq,
                "artifact": decision["artifact"],
                "policy_cycle": decision["policy_cycle"],
                "log_cycle": decision["log_cycle"],
                "knob": knob,
                "instance": instance,
                "applied_value": value,
                "anchor_cap": anchor,
                "envelope": envelope,
                "in_envelope": (
                    envelope is not None
                    and envelope["min"] <= value <= envelope["max"]
                ),
                "lease_ceiling": ceiling,
                "clamped_by_lease": (
                    ceiling is not None and value == ceiling
                ),
                "evidence_for_seat": decision["evidence"].get(instance),
                "evidence_transport": decision["evidence"].get("transport"),
                "scheduler_cycle": scheduler_cycle_for(heartbeats, seq),
                "preceding_heartbeat_cycle": decision["log_cycle"],
                "effect": {
                    "field": field,
                    "before_last": last_value(before, field),
                    "after_first": first_value(after, field),
                    "before_distinct": distinct_values(before, field),
                    "after_distinct": distinct_values(after, field),
                    "dispatches_after": len(after),
                    "mean_total_tokens_before": mean_of(before[-12:], "tokens"),
                    "mean_total_tokens_after": mean_of(after[:12], "tokens"),
                    "mean_completion_tokens_before": mean_of(
                        before[-12:], "completion_tokens"),
                    "mean_completion_tokens_after": mean_of(
                        after[:12], "completion_tokens"),
                    # The record-only test that needs no code reading: a cap
                    # in force cannot be exceeded. Zero breaches is NOT proof
                    # the cap was in force — it also happens when no call
                    # wanted more than the cap allowed — so it is reported as
                    # what it is, an untested cap.
                    "completions_above_the_applied_cap": sum(
                        1 for d in after
                        if knob != "timeout:transport"
                        and isinstance(d.get("completion_tokens"), int)
                        and d["completion_tokens"] > value
                    ),
                    "truncations_before": sum(
                        1 for d in before[-12:] if d["truncated"]),
                    "truncations_after": sum(
                        1 for d in after[:12] if d["truncated"]),
                    # The falsifiable question: did the value the policy
                    # states ever appear on a dispatch this seat actually
                    # made afterwards?
                    "reached_the_wire": value in distinct_values(after, field),
                    "value_is_a_route_cap": value in route_caps,
                    # The E43 signature: a transport drop whose reason names
                    # the applied value is the decision's typed downstream
                    # effect, even when no dispatch followed.
                    "refusals_naming_value": [
                        {"seq": d["seq"], "reason": d["reason"]}
                        for d in drops
                        if d["seq"] > seq and str(value) in d["reason"]
                    ],
                },
            })
    return rows


def last_value(rows, field):
    for row in reversed(rows):
        if row.get(field) is not None:
            return row[field]
    return None


def first_value(rows, field):
    for row in rows:
        if row.get(field) is not None:
            return row[field]
    return None


def distinct_values(rows, field):
    return sorted({row[field] for row in rows if row.get(field) is not None})


def mean_of(rows, field):
    values = [row[field] for row in rows if isinstance(row.get(field), int)]
    return round(sum(values) / len(values), 1) if values else None


# --------------------------------------------------------------------------
# the law check: allocation touches EFFICIENCY, never EVIDENCE
# --------------------------------------------------------------------------

def law_check(root_census):
    """Structural, on live data: no event that emits a declared signal or
    applies an allocation decision may carry a label change for anything
    except a controller policy artifact — whose own status IS allowed to move
    (INV-signal-contract, design point P6).
    """
    # BOTH controller policy families are exempt, and only they. A controller
    # policy's own status IS allowed to move — a policy that could not be
    # attacked would be authority without exposure (INV-signal-contract, P6).
    # The exemption is by exact artifact id, and it names the family, so it
    # stays auditable instead of being a blanket over anything a Refl touched.
    policy_family = {
        d["artifact"]: d["family"] for d in root_census["decisions"]
    }
    policy_family.update({
        h["artifact"]: h["family"] for h in root_census["hysteresis_policies"]
    })
    signal_seqs = set(root_census["signal_event_seqs"])
    controller_seqs = set(root_census["controller_event_seqs"])
    violations = []
    exempt = []
    for event in root_census["status_events"]:
        if event["seq"] not in signal_seqs and event["seq"] not in controller_seqs:
            continue
        foreign = [
            entry for entry in event["changed"] if entry not in policy_family
        ]
        row = {
            "seq": event["seq"], "rule": event["rule"], "cycle": event["cycle"],
            "signal": event["signal"], "changed": event["changed"],
            "families": sorted({
                policy_family[entry]
                for entry in event["changed"] if entry in policy_family
            }),
        }
        if foreign:
            row["foreign"] = foreign
            violations.append(row)
        else:
            exempt.append(row)

    decision_cycles = sorted({
        d["log_cycle"] for d in root_census["decisions"]
    })
    label_cycles = Counter(
        event["cycle"] for event in root_census["status_events"]
    )
    return {
        "root": root_census["root"],
        "signal_or_decision_events": len(signal_seqs | controller_seqs),
        "label_changing_events_total": len(root_census["status_events"]),
        "label_changes_inside_signal_or_decision_events": (
            len(violations) + len(exempt)
        ),
        "policy_status_moves_exempt": exempt,
        "violations": violations,
        "decision_cycles": decision_cycles,
        "label_changes_per_cycle": {str(k): v for k, v in sorted(
            label_cycles.items())},
        "verdict": "CONFIRMED" if not violations else "VIOLATED",
    }


# --------------------------------------------------------------------------
# open-loop adjudication
# --------------------------------------------------------------------------

def open_loop_verdicts(root_census):
    """Each `allocation open-loop for signal X` notice, adjudicated REAL or
    SPURIOUS against what the root's own record shows was emitted."""
    emitted = root_census["emissions"]
    out = []
    for record in root_census["authority"]:
        for signal in record.get("open_loop") or []:
            count = emitted.get(signal, 0)
            out.append({
                "root": root_census["root"],
                "seq": record["seq"],
                "signal": signal,
                "emitted_in_this_root": count,
                "verdict": "SPURIOUS" if count else "REAL",
            })
    return out


# --------------------------------------------------------------------------
# staleness: the contract's one falsifiable promise per signal
# --------------------------------------------------------------------------

def staleness_verdicts(per_root):
    """A staleness bound can only be violated where one was DECLARED.

    84 of the 111 declared names carry the `unspecified` debt marker, which
    records that nobody stated a bound — those cannot be violated, and saying
    so is the honest verdict, not a pass. For the rest the decidable question
    the record can answer is COVERAGE: a `cycle`-bounded signal is "usable
    until the next cycle boundary", so a consumer reading it in a cycle where
    it was not re-emitted is reading a value past its bound. A gap in the
    per-cycle series is therefore the falsifiable form, and the scheduler
    states the promise itself — `_record_detection_signals` says the three v2
    detection signals are "emitted every cycle so the series is complete
    rather than sampled".
    """
    rows = []
    declarations = [
        (name, decl.unit, decl.staleness, "exact")
        for name, decl in SIGNAL_DECLARATIONS.items()
    ] + [
        (name, decl.unit, decl.staleness, "prefix")
        for name, decl in PREFIX_DECLARATIONS.items()
    ]
    for name, unit, bound, kind in sorted(declarations):
        emitted_total = sum(r["emissions"].get(name, 0) for r in per_root)
        row = {
            "signal": name, "kind": kind, "unit": unit, "staleness": bound,
            "emitted_in_population": emitted_total,
            "reader": (CONSUMERS.get(name) or {}).get("reader"),
            "per_root": [],
        }
        if bound == "unspecified":
            row["verdict"] = "NO-BOUND-DECLARED"
            row["reason"] = (
                "migration debt marker: the author stated no staleness bound, "
                "so there is no promise here to keep or break"
            )
            rows.append(row)
            continue
        if not emitted_total:
            row["verdict"] = "NOT-APPLICABLE"
            row["reason"] = (
                "never emitted in the population, so no value exists that "
                "could be believed past its bound"
            )
            rows.append(row)
            continue
        if bound in ("run", "permanent"):
            row["verdict"] = "PASS"
            row["reason"] = (
                "bound is `" + bound + "`; every read of a logged value "
                "happens inside the run that logged it, so the bound cannot "
                "be exceeded by construction"
            )
            rows.append(row)
            continue

        if unit not in LEVEL_UNITS:
            # An OCCURRENCE with a `cycle` bound. Coverage says nothing here;
            # the falsifiable question is how old the last occurrence was when
            # a consumer believed it.
            consumer = CONSUMERS.get(name)
            if consumer is None:
                row["verdict"] = "NO-CONSUMER"
                row["reason"] = (
                    "an `" + unit + "` signal with a `" + bound + "` bound "
                    "that no committed reader consumes: the bound is a "
                    "promise nothing relies on, so nothing can break it"
                )
                rows.append(row)
                continue
            row["reliance"] = consumer["reliance"]
            ages = []
            for root in per_root:
                cycles = [c for c in root["cycles_seen"] if c >= 0]
                emitted_cycles = sorted(
                    int(c) for c, n in root["per_cycle"].get(name, {}).items()
                    if n
                )
                if not emitted_cycles or not cycles:
                    continue
                age = max(cycles) - max(emitted_cycles)
                ages.append(age)
                row["per_root"].append({
                    "root": root["root"],
                    "emitted_in_cycles": emitted_cycles,
                    "last_cycle_of_the_run": max(cycles),
                    "age_of_the_last_occurrence_at_run_end_in_cycles": age,
                })
            if not ages:
                row["verdict"] = "NOT-DECIDABLE"
                row["reason"] = (
                    "emitted, but no cycle could be attributed to any "
                    "emission, so no age can be computed"
                )
            elif max(ages) <= 1:
                row["verdict"] = "PASS"
                row["reason"] = (
                    "the last occurrence was never more than one cycle old "
                    "while its reader could still consult it"
                )
            else:
                row["verdict"] = "EXCEEDED"
                row["reason"] = (
                    "declared bound is `" + bound + "`, but its reader ("
                    + consumer["reader"] + ") relies on it for "
                    + consumer["reliance"] + "; the last occurrence was up to "
                    + str(max(ages)) + " cycles old and still in force. The "
                    "reliance is deliberate, so the mismatch is in the "
                    "DECLARATION, not in the reader."
                )
            rows.append(row)
            continue

        worst = 0
        for root in per_root:
            cycles = [c for c in root["cycles_seen"] if c >= 0]
            if not cycles or not root["emissions"].get(name):
                continue
            emitted_cycles = {
                int(c) for c, n in root["per_cycle"].get(name, {}).items()
                if n and int(c) >= 0
            }
            missing = sorted(set(cycles) - emitted_cycles)
            worst = max(worst, len(missing))
            row["per_root"].append({
                "root": root["root"],
                "cycles_with_a_heartbeat": len(cycles),
                "cycles_carrying_the_signal": len(emitted_cycles & set(cycles)),
                "cycles_missing_it": missing,
            })
        if worst == 0:
            row["verdict"] = "PASS"
            row["reason"] = (
                "bound is `" + bound + "` and the series is complete: every "
                "cycle that has a heartbeat also carries this signal, so no "
                "consumer can read a value from a previous cycle"
            )
        else:
            row["verdict"] = "GAP"
            row["reason"] = (
                "bound is `" + bound + "` but the per-cycle series has holes; "
                "a consumer reading the last emitted value inside a hole "
                "would be reading past the bound. Whether one does is a "
                "question about consumers, recorded separately."
            )
        rows.append(row)

    return {
        "schema": "run-anatomy.w5.staleness.v1",
        "population_roots": [r["root"] for r in per_root],
        "declared_total": len(SIGNAL_DECLARATIONS) + len(PREFIX_DECLARATIONS),
        "with_a_declared_bound": sum(
            1 for r in rows if r["staleness"] != "unspecified"),
        "verdict_counts": dict(Counter(r["verdict"] for r in rows)),
        "rows": rows,
    }


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def main():
    inventory = read_json(os.path.join(PROGRAM, "ROOT_INVENTORY.json"))
    roots = inventory["roots"]
    population = sorted(
        (r for r in roots if r["first_ts"] >= POPULATION_CUTOFF),
        key=lambda r: r["first_ts"],
    )

    per_root = [census_root(r["root"]) for r in population]

    # The silence census asks "ever", so it runs over ALL inventoried roots.
    ever = Counter()
    ever_roots = defaultdict(set)
    undeclared_ever = Counter()
    for row in roots:
        root = os.path.join(REPO, row["root"])
        for event in read_log(root):
            if event.get("rule") != "Measure":
                continue
            inputs = event.get("inputs") or []
            diff = event.get("state_diff") or {}
            if not inputs or diff.get("hv_set") or diff.get("reach_set"):
                continue
            kind, key = classify_signal(inputs[0])
            if kind == "undeclared":
                undeclared_ever[inputs[0]] += 1
            else:
                ever[key] += 1
                ever_roots[key].add(row["root"])

    declared = []
    for name, decl in sorted(SIGNAL_DECLARATIONS.items()):
        declared.append({
            "name": name, "kind": "exact", "unit": decl.unit,
            "staleness": decl.staleness,
            "ever_emitted": ever.get(name, 0),
            "roots_ever": len(ever_roots.get(name, ())),
            "population_emitted": sum(
                r["emissions"].get(name, 0) for r in per_root),
            "population_roots": sum(
                1 for r in per_root if r["emissions"].get(name)),
        })
    for name, decl in sorted(PREFIX_DECLARATIONS.items()):
        declared.append({
            "name": name, "kind": "prefix", "unit": decl.unit,
            "staleness": decl.staleness,
            "ever_emitted": ever.get(name, 0),
            "roots_ever": len(ever_roots.get(name, ())),
            "population_emitted": sum(
                r["emissions"].get(name, 0) for r in per_root),
            "population_roots": sum(
                1 for r in per_root if r["emissions"].get(name)),
        })

    signal_census = {
        "schema": "run-anatomy.w5.signal-census.v1",
        "population_cutoff": POPULATION_CUTOFF,
        "population_roots": [r["root"] for r in per_root],
        "silence_population_roots": len(roots),
        "declared_total": len(SIGNAL_DECLARATIONS) + len(PREFIX_DECLARATIONS),
        "declared_exact": len(SIGNAL_DECLARATIONS),
        "declared_prefix": len(PREFIX_DECLARATIONS),
        "declared": declared,
        "undeclared_tags_ever": dict(undeclared_ever),
        "per_root": [
            {
                key: value for key, value in root.items()
                if key not in ("dispatches", "status_events")
            }
            for root in per_root
        ],
    }

    decision_rows = []
    for root in per_root:
        decision_rows.extend(analyse_decisions(root))

    controller_census = {
        "schema": "run-anatomy.w5.controller-census.v1",
        "population_roots": [r["root"] for r in per_root],
        "decisions": decision_rows,
        "authority_records": [
            dict(record, root=root["root"])
            for root in per_root for record in root["authority"]
        ],
        "rehydrations": [
            dict(record, root=root["root"])
            for root in per_root for record in root["rehydrations"]
        ],
        "holds": [
            dict(record, root=root["root"])
            for root in per_root for record in root["holds"]
        ],
        "drops": [
            dict(record, root=root["root"])
            for root in per_root for record in root["drops"]
        ],
        "open_loop": [
            verdict for root in per_root for verdict in open_loop_verdicts(root)
        ],
        "expected_open_loop_by_root": {
            root["root"]: root["expected_open_loop"] for root in per_root
        },
        "consumers": CONSUMERS,
    }

    staleness = staleness_verdicts(per_root)
    with open(os.path.join(HERE, "STALENESS.json"), "w", encoding="utf-8") as h:
        json.dump(staleness, h, indent=1, sort_keys=True)
        h.write("\n")
    print("wrote STALENESS.json")

    law = {
        "schema": "run-anatomy.w5.law-check.v1",
        "population_roots": [r["root"] for r in per_root],
        "per_root": [law_check(root) for root in per_root],
    }
    law["verdict"] = (
        "CONFIRMED" if all(r["verdict"] == "CONFIRMED" for r in law["per_root"])
        else "VIOLATED"
    )

    for name, payload in (
        ("SIGNAL_CENSUS.json", signal_census),
        ("CONTROLLER_CENSUS.json", controller_census),
        ("LAW_CHECK.json", law),
    ):
        with open(os.path.join(HERE, name), "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=1, sort_keys=True)
            handle.write("\n")
        print(f"wrote {name}")

    emitted_names = sum(1 for d in declared if d["ever_emitted"])
    print(f"declared names: {signal_census['declared_total']}; "
          f"ever emitted in any of {len(roots)} roots: {emitted_names}")
    print(f"controller decisions in the population: {len(decision_rows)} "
          f"knob-moves across {len(per_root)} roots")
    print(f"law check: {law['verdict']}")


if __name__ == "__main__":
    sys.exit(main())
