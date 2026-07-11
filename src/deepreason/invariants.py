"""Post-run invariant checker — the chaos battery's measuring instrument.

Every check is a hard property the spec promises regardless of how badly
the engine LLM behaves: replay determinism (§0), accounting totality
(every token on the log exactly once), graph well-formedness (§2), and
detection totality. ``verify_root`` returns named violations so a report
can say WHICH promise broke; the chaos battery treats every entry as a
bug candidate.
"""

import json
from pathlib import Path

from deepreason.adjudication.edges import DependenceCycleError, build_dep, toposort
from deepreason.controller import ENVELOPES, GENERATOR_LEDGER
from deepreason.harness import Harness
from deepreason.llm.firewall import route_fingerprint
from deepreason.ontology.state import Status
from deepreason.run_manifest import (
    MANIFEST_HASH_NAME,
    MANIFEST_NAME,
    load_run_manifest,
)


def verify_root(root: Path, meter_total: int | None = None) -> dict:
    """Run every invariant over the session at ``root``. Returns
    {"violations": [{"check", "detail"}, ...], "stats": {...}}."""
    violations: list[dict] = []

    def fail(check: str, detail: str) -> None:
        violations.append({"check": check, "detail": detail[:400]})

    # 1. Replay determinism: two independent materializations agree.
    try:
        h = Harness(root)
        if Harness(root).state.model_dump_json() != h.state.model_dump_json():
            fail("replay", "two replays of the same log produced different state")
    except Exception as e:  # noqa: BLE001 - an unopenable root is the finding
        return {"violations": [{"check": "open", "detail": repr(e)[:400]}], "stats": {}}

    events = list(h.log.read())

    # Process metadata is replay/audit input only.  Its checks never inspect
    # or alter att, dep, status, warrants, guards, or acceptance.
    manifest = None
    manifest_path = Path(root) / MANIFEST_NAME
    if manifest_path.exists():
        hash_path = Path(root) / MANIFEST_HASH_NAME
        if not hash_path.exists():
            fail("run-manifest-hash", f"missing {MANIFEST_HASH_NAME}")
        try:
            manifest = load_run_manifest(manifest_path)
            if manifest_path.read_bytes() != manifest.canonical_bytes():
                fail("run-manifest-canonical", "manifest bytes are not canonical JSON")
            if manifest.pack_profile != manifest.model_profile:
                fail(
                    "profile-metadata",
                    f"pack_profile={manifest.pack_profile!r} differs from "
                    f"model_profile={manifest.model_profile!r}",
                )
            if manifest.output_profile != manifest.model_profile:
                fail(
                    "profile-metadata",
                    f"output_profile={manifest.output_profile!r} differs from "
                    f"model_profile={manifest.model_profile!r}",
                )
        except Exception as e:  # noqa: BLE001 - invalid metadata is the finding
            fail("run-manifest", repr(e))

    # 2. Incremental transitions == from-scratch walk.
    try:
        if h.transitions() != Harness(root).transitions():
            fail("transitions", "incremental transitions diverge from a fresh walk")
    except Exception as e:  # noqa: BLE001
        fail("transitions", repr(e))

    # 3. Time-travel at sampled seqs must not crash.
    seqs = [e.seq for e in events]
    for seq in sorted({seqs[i * (len(seqs) - 1) // 4] for i in range(5)} if seqs else []):
        try:
            Harness.at(root, seq)
        except Exception as e:  # noqa: BLE001
            fail("time-travel", f"Harness.at(seq={seq}): {e!r}")

    # 4. Accounting: meter total == sum of logged call tokens; every
    #    llm-bearing event's prompt/raw blobs exist.
    logged = 0
    llm_calls = 0
    llm_attempts = 0
    repair_attempts = 0
    traced_calls = 0
    first_pass_valid = 0
    eventual_valid = 0
    schema_exhausted = 0
    transport_dropped = 0
    usage_unknown_attempts = 0
    provider_transport_attempts = 0
    authorized_controller_limits: dict[str, set[int]] = {}
    for e in events:
        # Controller policies are harness-authored, attackable artifacts. A
        # value is transport-authorized only after its policy is appended;
        # later refutation may cause a revert but cannot erase that historical
        # request setting from the replay trace.
        for output in e.outputs if e.rule.value == "Refl" else ():
            artifact = h.state.artifacts.get(output)
            if (
                artifact is None
                or artifact.provenance.role.value != "controller"
                or not artifact.content_ref.startswith("inline:")
            ):
                continue
            try:
                body = json.loads(artifact.content_ref[len("inline:"):])
            except (TypeError, ValueError):
                continue
            knobs = body.get("knobs") if isinstance(body, dict) else None
            if not isinstance(knobs, dict):
                continue
            for knob, value in knobs.items():
                envelope = ENVELOPES.get(knob)
                if (
                    knob in GENERATOR_LEDGER
                    and type(value) is int
                    and envelope is not None
                    and envelope["min"] <= value <= envelope["max"]
                ):
                    authorized_controller_limits.setdefault(knob, set()).add(
                        value
                    )
        if e.llm is None:
            continue
        llm_calls += 1
        llm_attempts += e.llm.attempts
        repair_attempts += max(0, e.llm.attempts - 1)
        logged += e.llm.tokens
        trace = list(e.llm.attempt_trace)
        dropped = any(
            value == "dropped-call"
            or value.endswith("-dropped")
            or value in {"budget-exhausted", "terminal-route-firewall"}
            for value in e.inputs
        )
        if trace:
            traced_calls += 1
            first_pass_valid += int(trace[0].valid)
            eventual_valid += int(any(attempt.valid for attempt in trace))
            usage_unknown_attempts += sum(
                int(attempt.usage_unknown) for attempt in trace
            )
            provider_transport_attempts += sum(
                attempt.transport_attempts for attempt in trace
            )
            if not any(attempt.valid for attempt in trace):
                if any(attempt.usage_unknown for attempt in trace):
                    transport_dropped += 1
                else:
                    schema_exhausted += 1

            if len(trace) != e.llm.attempts:
                fail(
                    "attempt-trace",
                    f"event seq={e.seq}: trace has {len(trace)} entries but "
                    f"attempts={e.llm.attempts}",
                )
            trace_tokens = sum(attempt.tokens for attempt in trace)
            if trace_tokens != e.llm.tokens:
                fail(
                    "attempt-accounting",
                    f"event seq={e.seq}: trace tokens={trace_tokens} but "
                    f"call tokens={e.llm.tokens}",
                )
            valid_indexes = [
                index for index, attempt in enumerate(trace) if attempt.valid
            ]
            if dropped and valid_indexes:
                fail(
                    "attempt-validity",
                    f"event seq={e.seq}: dropped call contains a valid attempt",
                )
            if not dropped and valid_indexes != [len(trace) - 1]:
                fail(
                    "attempt-validity",
                    f"event seq={e.seq}: successful call must have one final valid "
                    f"attempt, got {valid_indexes}",
                )
        elif manifest is not None:
            # Historical records remain readable because attempt_trace has a
            # default, but a manifest-bound run without total attempt evidence
            # cannot substantiate replay/accounting claims.
            fail(
                "attempt-trace",
                f"event seq={e.seq}: manifest-bound LLM call has no attempt trace",
            )

        prompt_payload = None
        empty_raw_allowed = bool(trace and trace[-1].usage_unknown)
        for ref, kind in ((e.llm.prompt_ref, "prompt"), (e.llm.raw_ref, "raw")):
            if not ref:
                if kind == "raw" and empty_raw_allowed:
                    continue
                fail("blobs", f"event seq={e.seq}: {kind} blob reference is empty")
                continue
            try:
                payload = h.blobs.get(ref)
                if kind == "prompt":
                    prompt_payload = payload
            except KeyError:
                fail("blobs", f"event seq={e.seq}: {kind} blob {ref[:12]} missing")

        if manifest is not None:
            routes = manifest.roles.get(e.llm.role, ())
            if not routes:
                fail(
                    "frozen-route",
                    f"event seq={e.seq}: role {e.llm.role!r} has no active manifest route",
                )
            elif not any(
                route.model_id == e.llm.model and route.base_url == e.llm.endpoint
                for route in routes
            ):
                fail(
                    "frozen-route",
                    f"event seq={e.seq}: {e.llm.role} used "
                    f"endpoint={e.llm.endpoint!r} model={e.llm.model!r} outside manifest",
                )

            for index, attempt in enumerate(trace):
                prefix = f"event seq={e.seq} attempt={index}"
                if attempt.attempt != index:
                    fail(
                        "attempt-order",
                        f"{prefix}: recorded attempt index={attempt.attempt}",
                    )
                for ref, kind in (
                    (attempt.prompt_ref, "prompt"),
                    (attempt.raw_ref, "raw"),
                    (attempt.diagnostic_ref, "diagnostic"),
                ):
                    required = (
                        kind == "prompt"
                        or (kind == "raw" and not attempt.usage_unknown)
                        or (kind == "diagnostic" and not attempt.valid)
                    )
                    if not ref:
                        if required:
                            fail("attempt-blobs", f"{prefix}: missing {kind} ref")
                        continue
                    try:
                        h.blobs.get(ref)
                    except KeyError:
                        fail(
                            "attempt-blobs",
                            f"{prefix}: {kind} blob {ref[:12]} missing",
                        )

                if not attempt.contract_id:
                    fail("attempt-contract", f"{prefix}: contract_id is empty")
                if attempt.model_profile != manifest.model_profile:
                    fail(
                        "attempt-profile",
                        f"{prefix}: model_profile={attempt.model_profile!r}, "
                        f"manifest={manifest.model_profile!r}",
                    )
                if attempt.seat < 0 or attempt.seat >= len(routes):
                    fail(
                        "attempt-route",
                        f"{prefix}: seat {attempt.seat} outside role route table",
                    )
                    continue
                route = routes[attempt.seat]
                if (
                    e.llm.model != route.model_id
                    or e.llm.endpoint != route.base_url
                ):
                    fail(
                        "attempt-route",
                        f"{prefix}: top-level call does not match recorded seat",
                    )
                if attempt.endpoint_id != route.endpoint_id:
                    fail(
                        "attempt-route",
                        f"{prefix}: endpoint_id={attempt.endpoint_id!r}, "
                        f"manifest={route.endpoint_id!r}",
                    )
                expected_route_hash = route_fingerprint(route)
                if attempt.route_sha256 != expected_route_hash:
                    fail(
                        "attempt-route",
                        f"{prefix}: route hash does not match manifest seat",
                    )
                if attempt.output_mechanism != route.output_mechanism:
                    fail(
                        "attempt-route",
                        f"{prefix}: output mechanism={attempt.output_mechanism!r}, "
                        f"manifest={route.output_mechanism!r}",
                    )
                # timeout_s is the marker for the extended trace. Historical
                # attempts default it to None and remain replayable; every new
                # adapter attempt records both limits. Values may differ from
                # the base route only after an earlier logged controller
                # policy authorized that exact process setting.
                if attempt.timeout_s is not None:
                    allowed_timeouts = {
                        route.timeout_s,
                        *authorized_controller_limits.get(
                            "timeout:transport", set()
                        ),
                    }
                    if attempt.timeout_s not in allowed_timeouts:
                        fail(
                            "attempt-limits",
                            f"{prefix}: timeout_s={attempt.timeout_s!r} was not "
                            "authorized by the route or a prior controller policy",
                        )
                    allowed_caps = {
                        route.max_tokens,
                        *authorized_controller_limits.get(
                            f"cap:{e.llm.role}", set()
                        ),
                    }
                    if attempt.max_tokens not in allowed_caps:
                        fail(
                            "attempt-limits",
                            f"{prefix}: max_tokens={attempt.max_tokens!r} was not "
                            "authorized by the route or a prior controller policy",
                        )

            # W4 has one initial generation and at most two repairs.  Attempts
            # and the final repair pack are operational evidence, not verdicts.
            if e.llm.attempts < 1 or e.llm.attempts > 3:
                fail(
                    "repair-metadata",
                    f"event seq={e.seq}: attempts={e.llm.attempts}, expected 1..3",
                )
            if e.llm.attempts > 1 and prompt_payload is not None:
                prompt_text = prompt_payload.decode("utf-8", errors="replace")
                if "DIAGNOSTIC:" not in prompt_text:
                    fail(
                        "repair-metadata",
                        f"event seq={e.seq}: repaired call lacks field diagnostic in final prompt",
                    )
                expected = (
                    "replacement JSON value"
                    if e.llm.attempts == 3
                    else "complete corrected JSON value"
                )
                if expected not in prompt_text:
                    fail(
                        "repair-metadata",
                        f"event seq={e.seq}: final repair prompt does not match attempts",
                    )
    if meter_total is not None and logged != meter_total:
        fail("accounting",
             f"meter says {meter_total} tokens, log accounts for {logged} "
             f"(delta {meter_total - logged})")

    # 5. Graph well-formedness.
    for wid, w in h.warrants.items():
        if w.validity_node not in h.state.artifacts:
            fail("warrant-validity", f"{wid}: validity node not registered")
        if w.target not in h.state.artifacts:
            fail("warrant-target", f"{wid}: target not registered")
    for carrier, wid in h.state.carries:
        if carrier not in h.state.artifacts:
            fail("carry-carrier", f"{carrier}: carrier artifact not registered")
        if wid not in h.warrants:
            fail("carry-warrant", f"{wid}: carried warrant not registered")
    for x, t in h.state.att:
        if x not in h.state.artifacts or t not in h.state.artifacts:
            fail("att-endpoints", f"dangling attack edge ({x[:12]}, {t[:12]})")
    try:
        toposort(set(h.state.artifacts), build_dep(h.state.artifacts))
    except DependenceCycleError as e:
        fail("dep-dag", str(e))
    # Any Status enum member is legal — SUSPENDED/SUSPENDED_UNSUPPORTED
    # are the spec §4 support-cascade labels (dependent of a refuted
    # premise; orphaned != false), first produced live on runs/ab_needham.
    # The check guards against values outside the enum domain entirely.
    for aid, status in h.state.status.items():
        if not isinstance(status, Status):
            fail("status-domain", f"{aid[:12]}: {status}")
    for aid, pid in h.state.addr:
        if aid not in h.state.artifacts or pid not in h.state.problems:
            fail("addr", f"dangling addr pair ({aid[:12]}, {pid})")

    # 6. Event stream: seqs strictly consecutive from 0.
    if seqs != list(range(len(seqs))):
        fail("seq-stream", "event seqs are not consecutive from 0")

    # 7. Detection stays a total function over a messy log.
    try:
        from deepreason.capture.detection import raw_flags
        from deepreason.config import Config
        from deepreason.llm.embedder import HashingEmbedder

        raw_flags(h, HashingEmbedder(), Config())
    except Exception as e:  # noqa: BLE001
        fail("detection-total", repr(e))

    stats = {
        "events": len(events),
        "artifacts": len(h.state.artifacts),
        "problems": len(h.state.problems),
        "warrants": len(h.warrants),
        "accepted": sum(1 for s in h.state.status.values() if s == Status.ACCEPTED),
        "refuted": sum(1 for s in h.state.status.values() if s == Status.REFUTED),
        "logged_tokens": logged,
        "process": {
            "manifest_present": manifest_path.exists(),
            "manifest_sha256": manifest.sha256 if manifest is not None else None,
            "engine_profile": manifest.engine_profile if manifest is not None else None,
            "model_profile": manifest.model_profile if manifest is not None else None,
            "profile_totals": {
                (manifest.model_profile if manifest is not None else "unprofiled"): {
                    "calls": llm_calls,
                    "attempts": llm_attempts,
                    "repair_attempts": repair_attempts,
                    "tokens": logged,
                    "traced_calls": traced_calls,
                    "first_pass_valid": first_pass_valid,
                    "eventual_valid": eventual_valid,
                    "schema_exhausted": schema_exhausted,
                    "transport_dropped": transport_dropped,
                    "usage_unknown_attempts": usage_unknown_attempts,
                    "provider_transport_attempts": provider_transport_attempts,
                }
            },
        },
        "gate_blocks": sum(1 for e in events for i in e.inputs if i.startswith("gate:")),
        "trial_blocks": sum(1 for e in events for i in e.inputs
                            if i.startswith("trial-blocked:")),
        "dropped_calls": sum(1 for e in events if "dropped-call" in e.inputs),
        "interventions": sum(1 for e in events for i in e.inputs
                             if i.startswith("intervention:")),
        "reseeds": sum(1 for e in events if e.rule.value == "Reseed"),
        "max_problem_desc_len": max(
            (len(p.description) for p in h.state.problems.values()), default=0),
    }
    return {"violations": violations, "stats": stats}
