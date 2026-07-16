"""Post-run invariant checker — the chaos battery's measuring instrument.

Every check is a hard property the spec promises regardless of how badly
the engine LLM behaves: replay determinism (§0), accounting totality
(every token on the log exactly once), graph well-formedness (§2), and
detection totality. ``verify_root`` returns named violations so a report
can say WHICH promise broke; the chaos battery treats every entry as a
bug candidate.
"""

import json
from enum import Enum
from pathlib import Path

from deepreason.adjudication.edges import DependenceCycleError, build_dep, toposort
from deepreason.bridge.events import BridgeAction
from deepreason.controller import ENVELOPES, GENERATOR_LEDGER
from deepreason.harness import Harness
from deepreason.llm.firewall import route_fingerprint
from deepreason.ontology.state import Status
from deepreason.run_manifest import (
    MANIFEST_HASH_NAME,
    MANIFEST_NAME,
    load_run_manifest,
)


class ExpectedCallOutcome(str, Enum):
    """Attempt-validity shape authorized by one typed process event."""

    SUCCESS_REQUIRED = "success_required"
    FAILURE_REQUIRED = "failure_required"
    LEGACY_DROPPED = "legacy_dropped"


def _is_typed_bridge_failure(event) -> bool:
    payload = event.bridge
    return bool(
        event.rule.value == "Bridge"
        and payload is not None
        and payload.action == BridgeAction.FAILED
        and payload.error_code
        and event.llm is not None
    )


def _legacy_bridge_failure_call_seqs(events, bridge_state) -> set[int]:
    """Correlate only the historical Stage-A three-event failure shape.

    Older bridge workflows put exhausted Stage-A spend on LEDGER_CREATED,
    followed immediately by LEDGER_VALIDATED and a typed FAILED event.  This
    resolver recognizes that exact canonical chain; near misses remain normal
    successful-call candidates and therefore fail attempt validity.
    """

    correlated: set[int] = set()
    for index in range(len(events) - 2):
        created, validated, failed = events[index : index + 3]
        if not (
            created.rule.value == validated.rule.value == failed.rule.value == "Bridge"
            and created.bridge is not None
            and created.bridge.action == BridgeAction.LEDGER_CREATED
            and created.llm is not None
            and validated.bridge is not None
            and validated.bridge.action == BridgeAction.LEDGER_VALIDATED
            and validated.llm is None
            and failed.bridge is not None
            and failed.bridge.action == BridgeAction.FAILED
            and failed.llm is None
            and failed.bridge.error_code == "BRIDGE_LEDGER_REPAIR_EXHAUSTED"
        ):
            continue
        failures = [
            bridge_state.failures[output]
            for output in failed.outputs
            if output in bridge_state.failures
        ]
        if len(failures) != 1:
            continue
        failure = failures[0]
        ledger_id = failure.claim_ledger_id
        report_id = failure.validation_report_id
        if not (
            failure.phase == "stage_a"
            and failure.error_code == failed.bridge.error_code
            and ledger_id is not None
            and report_id is not None
            and any(
                diagnostic.code == "BRIDGE_LEDGER_REPAIR_EXHAUSTED"
                for diagnostic in failure.diagnostics
            )
            and {
                failure.evidence_pack_id,
                failure.catalog_id,
                ledger_id,
            }.issubset(set(created.outputs))
            and list(validated.inputs) == [ledger_id]
            and validated.bridge.finding_ref == report_id
            and report_id in validated.outputs
            and list(failed.inputs) == [ledger_id, report_id]
            and list(failure.terminal_inputs) == [ledger_id, report_id]
        ):
            continue
        correlated.add(created.seq)
    return correlated


def _expected_call_outcome(
    event,
    legacy_failure_call_seqs: set[int],
) -> ExpectedCallOutcome:
    if event.seq in legacy_failure_call_seqs or _is_typed_bridge_failure(event):
        return ExpectedCallOutcome.FAILURE_REQUIRED
    if any(
        value == "dropped-call"
        or value.endswith("-dropped")
        or value in {"budget-exhausted", "terminal-route-firewall"}
        for value in event.inputs
    ):
        return ExpectedCallOutcome.LEGACY_DROPPED
    return ExpectedCallOutcome.SUCCESS_REQUIRED


def verify_root(root: Path, meter_total: int | None = None) -> dict:
    """Run every invariant over the session at ``root``. Returns
    {"violations": [{"check", "detail"}, ...], "stats": {...}}."""
    violations: list[dict] = []

    def fail(check: str, detail: str) -> None:
        violations.append({"check": check, "detail": detail[:400]})

    # 1. Replay determinism: two independent materializations agree.
    try:
        h = Harness(root)
        second = Harness(root)
        if second.state.model_dump_json() != h.state.model_dump_json():
            fail("replay", "two replays of the same log produced different state")
        if second.scratch_state != h.scratch_state:
            fail("scratch-replay", "two replays produced different advisory scratch state")
        if second.bridge_state != h.bridge_state:
            fail("bridge-replay", "two replays produced different advisory bridge state")
    except Exception as e:  # noqa: BLE001 - an unopenable root is the finding
        return {"violations": [{"check": "open", "detail": repr(e)[:400]}], "stats": {}}

    events = list(h.log.read())
    legacy_failure_call_seqs = _legacy_bridge_failure_call_seqs(
        events, h.bridge_state
    )

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
            # V1 froze one shared compatibility profile.  V2 deliberately
            # separates workload pack shape, transport model capacity, and
            # output wire shape (e.g. reasoning.text.v1 / compact /
            # compact.v2); equality would reject every legal v2 root.
            if (
                manifest.schema_version == 1
                and manifest.pack_profile != manifest.model_profile
            ):
                fail(
                    "profile-metadata",
                    f"pack_profile={manifest.pack_profile!r} differs from "
                    f"model_profile={manifest.model_profile!r}",
                )
            if (
                manifest.schema_version == 1
                and manifest.output_profile != manifest.model_profile
            ):
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

    def validate_school_route(event) -> None:
        call = event.llm
        receipt = getattr(call, "school_route", None) if call is not None else None
        output_schools = (
            {
                artifact.provenance.school
                for output in event.outputs
                if (artifact := h.state.artifacts.get(output)) is not None
                and artifact.provenance.school is not None
            }
            if event.rule.value == "Conj"
            else set()
        )
        tagged_schools = (
            {
                value.removeprefix("school:")
                for value in event.inputs
                if value.startswith("school:")
            }
            if event.inputs and event.inputs[0] == "conj-noregister"
            else set()
        )
        expected_school = output_schools | tagged_schools

        if manifest is not None and manifest.schema_version == 4 and expected_school:
            if len(expected_school) != 1:
                fail(
                    "school-route",
                    f"event seq={event.seq}: one call records multiple schools "
                    f"{sorted(expected_school)!r}",
                )
            if receipt is None:
                fail(
                    "school-route",
                    f"event seq={event.seq}: school-conditioned call has no route receipt",
                )
            elif receipt.school_id not in expected_school:
                fail(
                    "school-route",
                    f"event seq={event.seq}: receipt school={receipt.school_id!r}, "
                    f"event schools={sorted(expected_school)!r}",
                )

        if receipt is None:
            return
        if manifest is None or manifest.schema_version != 4:
            fail(
                "school-route",
                f"event seq={event.seq}: school route receipt requires a v4 manifest",
            )
            return
        control = manifest.control_plane_policy
        if control is None:
            fail("school-route", f"event seq={event.seq}: v4 control policy is missing")
            return
        engine_data = json.loads(manifest.engine_config_json)
        roster = {
            f"school-{index}"
            for index in range(int(engine_data.get("N_SCHOOLS", 0)))
        }
        if receipt.school_id not in roster:
            fail(
                "school-route",
                f"event seq={event.seq}: receipt school is outside manifest roster",
            )
            return
        if receipt.role != "conjecturer":
            fail(
                "school-route",
                f"event seq={event.seq}: unsupported school role {receipt.role!r}",
            )
            return
        routes = manifest.roles.get(receipt.role, ())
        school_policy = control.school_execution
        expected_seat = 0
        expected_endpoint = None
        if school_policy.mode == "route_bound":
            matches = [
                binding
                for binding in school_policy.bindings
                if binding.school_id == receipt.school_id
                and binding.role == receipt.role
            ]
            if len(matches) != 1:
                fail(
                    "school-route",
                    f"event seq={event.seq}: receipt has no unique manifest binding",
                )
                return
            expected_seat = matches[0].seat
            expected_endpoint = matches[0].endpoint_id
        if receipt.seat != expected_seat:
            fail(
                "school-route",
                f"event seq={event.seq}: receipt seat={receipt.seat}, "
                f"policy seat={expected_seat}",
            )
            return
        if receipt.seat >= len(routes):
            fail(
                "school-route",
                f"event seq={event.seq}: receipt seat is outside manifest routes",
            )
            return
        route = routes[receipt.seat]
        if expected_endpoint is not None and receipt.endpoint_id != expected_endpoint:
            fail(
                "school-route",
                f"event seq={event.seq}: receipt endpoint differs from binding",
            )
        if receipt.endpoint_id != route.endpoint_id:
            fail(
                "school-route",
                f"event seq={event.seq}: receipt endpoint differs from manifest route",
            )
        if receipt.route_sha256 != route_fingerprint(route):
            fail(
                "school-route",
                f"event seq={event.seq}: receipt route hash differs from manifest route",
            )

    def validate_conjecture_context(event) -> None:
        """Prove the exact advisory bytes and their append-only provenance."""

        call = event.llm
        receipt = (
            getattr(call, "conjecture_context", None) if call is not None else None
        )
        if receipt is None:
            return
        prefix = f"event seq={event.seq}"
        if manifest is None or manifest.schema_version != 4:
            fail(
                "conjecture-context",
                f"{prefix}: advisory context receipt requires a v4 manifest",
            )
        else:
            control = manifest.control_plane_policy
            if (
                control is None
                or control.mode != "active_conjecture"
                or control.conjecture_context.mode == "disabled"
            ):
                fail(
                    "conjecture-context",
                    f"{prefix}: manifest does not authorize conjecture context",
                )
            if receipt.manifest_digest != manifest.sha256:
                fail(
                    "conjecture-context",
                    f"{prefix}: receipt manifest digest does not match the run",
                )

        if receipt.formal_fence_seq >= event.seq:
            fail(
                "conjecture-context",
                f"{prefix}: context fence does not precede the call event",
            )
        route_receipt = getattr(call, "school_route", None)
        if receipt.school_id is not None and route_receipt is None:
            fail(
                "conjecture-context",
                f"{prefix}: school context has no matching route receipt",
            )
        try:
            fenced = Harness.at(root, receipt.formal_fence_seq)
            if receipt.problem_id not in fenced.state.problems:
                fail(
                    "conjecture-context",
                    f"{prefix}: problem was absent at the formal fence",
                )
        except Exception as error:  # noqa: BLE001 - malformed evidence is a finding
            fail(
                "conjecture-context",
                f"{prefix}: cannot reconstruct formal fence: {error!r}",
            )

        selection = h.scratch_state.attention_receipts.get(
            receipt.selection_receipt_ref
        )
        context = h.scratch_state.advisory_contexts.get(
            receipt.advisory_context_ref
        )
        if selection is None:
            fail(
                "conjecture-context",
                f"{prefix}: selection receipt is absent from scratch replay",
            )
        elif selection.state_seq != receipt.scratch_fence_seq:
            fail(
                "conjecture-context",
                f"{prefix}: selection receipt names another scratch fence",
            )
        if context is None:
            fail(
                "conjecture-context",
                f"{prefix}: advisory context is absent from scratch replay",
            )
        elif context.retrieval_receipt != receipt.selection_receipt_ref:
            fail(
                "conjecture-context",
                f"{prefix}: advisory context names another selection receipt",
            )
        elif selection is not None and [block.id for block in context.blocks] != list(
            selection.final_order
        ):
            fail(
                "conjecture-context",
                f"{prefix}: advisory blocks differ from the selected order",
            )

        selection_events = [
            candidate
            for candidate in events
            if candidate.scratch is not None
            and receipt.selection_receipt_ref in candidate.outputs
        ]
        context_events = [
            candidate
            for candidate in events
            if candidate.scratch is not None
            and receipt.advisory_context_ref in candidate.outputs
        ]
        if len(selection_events) != 1 or selection_events[0].seq >= event.seq:
            fail(
                "conjecture-context",
                f"{prefix}: selection must have one preceding scratch event",
            )
        elif selection_events[0].scratch.context_ref != receipt.render_receipt_ref:
            fail(
                "conjecture-context",
                f"{prefix}: selection event does not bind the render receipt blob",
            )
        if len(context_events) != 1 or context_events[0].seq >= event.seq:
            fail(
                "conjecture-context",
                f"{prefix}: advisory context must have one preceding scratch event",
            )

        try:
            from deepreason.scratch.render import ScratchRenderReceiptV1

            render = ScratchRenderReceiptV1.model_validate_json(
                h.blobs.get(receipt.render_receipt_ref)
            )
            if render.state_seq != receipt.scratch_fence_seq:
                fail(
                    "conjecture-context",
                    f"{prefix}: render receipt names another scratch fence",
                )
            if render.attention_receipt != receipt.selection_receipt_ref:
                fail(
                    "conjecture-context",
                    f"{prefix}: render receipt names another selection",
                )
            if selection is not None and list(render.block_handles.values()) != list(
                selection.final_order
            ):
                fail(
                    "conjecture-context",
                    f"{prefix}: render handles differ from the selected blocks",
                )
        except (KeyError, TypeError, ValueError) as error:
            fail(
                "conjecture-context",
                f"{prefix}: invalid render receipt blob: {error!r}",
            )

        try:
            rendered = h.blobs.get(receipt.rendered_context_ref)
            initial_prompt = h.blobs.get(call.attempt_trace[0].prompt_ref)
            if initial_prompt.count(rendered) != 1:
                fail(
                    "conjecture-context",
                    f"{prefix}: initial prompt does not contain exact context once",
                )
            marker, separator, payload_bytes = rendered.partition(b"\n")
            payload = json.loads(payload_bytes) if separator else None
            from deepreason.scratch.contracts import SCRATCH_CONTRACT_INSTRUCTIONS

            if (
                marker != b"SCRATCH_ADVISORY_CONTEXT_V1"
                or not isinstance(payload, dict)
                or payload.get("warning") != SCRATCH_CONTRACT_INSTRUCTIONS
                or context is None
                or context.warning != SCRATCH_CONTRACT_INSTRUCTIONS
            ):
                fail(
                    "conjecture-context",
                    f"{prefix}: rendered advisory warning or envelope differs",
                )
        except (IndexError, KeyError, TypeError, UnicodeError, ValueError) as error:
            fail(
                "conjecture-context",
                f"{prefix}: rendered context evidence is incomplete: {error!r}",
            )

    for e in events:
        validate_school_route(e)
        validate_conjecture_context(e)
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
        expected_outcome = _expected_call_outcome(e, legacy_failure_call_seqs)
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
            if (
                expected_outcome == ExpectedCallOutcome.LEGACY_DROPPED
                and valid_indexes
            ):
                fail(
                    "attempt-validity",
                    f"event seq={e.seq}: dropped call contains a valid attempt",
                )
            elif (
                expected_outcome == ExpectedCallOutcome.FAILURE_REQUIRED
                and valid_indexes
            ):
                fail(
                    "attempt-validity",
                    f"event seq={e.seq}: failed call must contain no valid "
                    f"attempt, got {valid_indexes}",
                )
            elif (
                expected_outcome == ExpectedCallOutcome.SUCCESS_REQUIRED
                and valid_indexes != [len(trace) - 1]
            ):
                fail(
                    "attempt-validity",
                    f"event seq={e.seq}: successful call must have one final valid "
                    f"attempt, got {valid_indexes}",
                )
        elif expected_outcome == ExpectedCallOutcome.FAILURE_REQUIRED:
            fail(
                "attempt-trace",
                f"event seq={e.seq}: typed failed LLM call has no attempt trace",
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

        inspect_attempts = (
            manifest is not None
            or expected_outcome == ExpectedCallOutcome.FAILURE_REQUIRED
        )
        if inspect_attempts:
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
        "scratch_events": sum(1 for e in events if e.scratch is not None),
        "bridge_events": sum(1 for e in events if e.bridge is not None),
        "max_problem_desc_len": max(
            (len(p.description) for p in h.state.problems.values()), default=0),
    }
    return {"violations": violations, "stats": stats}
