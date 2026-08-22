# Diagnosis: the allocation controller wrote `endpoint.max_tokens = 20480` onto the leased conjecturer seat, and on a route declaring `context_window_tokens` the route firewall verifies that field for EQUALITY with the lease

Primary cause: `Controller._apply_cap`
(`src/deepreason/controller.py:552`, `bound[2].max_tokens = value`) writes the
tuned completion cap directly onto the live endpoint object that
`EndpointLease.verify` later inspects. At cycle 2 of run `40e713b3…` the
controller's efficiency branch fired — three spotless windows, zero truncation,
zero repairs — and narrowed the conjecturer seat's cap one envelope step, from
the leased 32768 to `round(32768 / 1.6) = 20480`. That write is lawful on every
axis the controller is bound by: the knob is a generator knob, the value sits
inside the anchored barrier `[800, 32768]`, the min-dwell was satisfied, and the
decision was emitted as a replayable policy artifact. `EndpointLease.verify`
(`src/deepreason/llm/firewall.py:270-273`) nonetheless adds `max_tokens` to its
frozen-equality set whenever the route declares `context_window_tokens`, which
this run's route does (`131072`). The next provider request re-verified the
lease immediately before dispatch (`llm/adapter.py:1146`), the equality failed,
and the raised `RouteFirewallError` became a dropped call and then a terminal
`operational_failure`. Six lines above that conditional, the same function's
comment states the opposite rule: `max_tokens` and `timeout_s` are
"intentionally absent" because they are "bounded process-health controls which
the deterministic controller may tune and log as Measure events". The contract
and the licence are both in force, and on this configuration they cannot both be
obeyed.

Evidence:
  - `experiments/2026-08-22-live-reach-rich-run/run/log.jsonl` seq **442**,
    `Refl` → artifact `492b41029fbd2b6f16eef2f520818a65c84e5f504ff59ab70d419fb334bf4003`
    (`run/objects/artifact/2e9009812fe9e3b6fd0b48ffd088d72d21bc09890ee21fd66f715bd8253cba52.json`),
    body verbatim:
    `{"cycle": 2, "evidence": {"argumentative_critic": {"n": 6, "repair_rate": 0.0, "truncation_rate": 0.0}, "conjecturer": {"n": 6, "repair_rate": 0.0, "truncation_rate": 0.0}}, "knobs": {"cap:argumentative_critic": 20480, "cap:conjecturer": 20480}}`
    → **this is the producer of 20480, named in the record, with its own
    evidence and provenance `role: "controller"`.** The value was never a
    transport artefact and never a literal.
  - `run/log.jsonl` seq **577**,
    `Measure ["dropped-call", "ROUTE_LEASE_MISMATCH role='conjecturer' seat=0 field=max_tokens expected=32768 actual=20480"]`,
    immediately followed by seq **578** `Measure ["run-stop", …]` with
    `{"cycle": 2, …}` → the first provider dispatch after the policy is the one
    that died; 135 events separate the tune from the refusal, with no successful
    provider call in between (`0` events carrying `llm` after seq 442).
  - `run/run-result.json` → `state: failed`, `stop_reason:
    operational_failure`, `error_type: "RouteFirewallError"`,
    `completion_status: "incomplete"`, `verification.operational_checks_passed:
    false`, `verification.integrity_valid: true` (the record itself is sound;
    only the operation failed).
  - `experiments/2026-08-22-live-reach-rich-run/run-config.yaml:27-28` →
    `context_window_tokens: 131072`, `max_tokens: 32768`. The first line is what
    selects the strict branch; the second is the value the equality demands.
  - Re-derivation of `20480` from committed code alone, one command:
    `python -c "from deepreason.controller import cap_envelope, clamp; e=cap_envelope('cap:conjecturer', 32768); print(e, clamp('cap:conjecturer', round(32768/e['step']), e))"`
    → `{'min': 800, 'max': 32768, 'step': 1.6, 'dwell': 2} 20480`. Exact.
  - The epoch-1 root
    (`failed-epoch1-run-40e713b3…/log.jsonl`) emitted the **byte-identical**
    policy artifact `492b4102…` at seq 352 — same content hash, same knobs.
    Epoch 1 died 76 events later of P7-reach seat exhaustion instead, because
    its already-terminal seat never issued another provider request for the
    firewall to refuse. The tune is deterministic; which of the two deaths
    arrives first is not.

Implicated code:
  - `src/deepreason/llm/firewall.py:270-273` — the conditional that adds
    `max_tokens` to the equality-checked set on a qualified route.
  - `src/deepreason/llm/firewall.py:251-256` — the comment asserting the
    contrary rule, in the same function.
  - `src/deepreason/controller.py:552` (`_apply_cap`), with
    `controller.py:114-142` (`cap_envelope`) and `controller.py:429-440`
    (`_propose`'s efficiency branch) as the deciding arithmetic.

Falsifiable prediction (what `dr-reproduce` must show): construct a
`Route(max_tokens=32768, context_window_tokens=131072)`, an endpoint matching it,
and a `Controller` over an adapter binding that endpoint to `conjecturer`; drive
three spotless conjecturer calls and step the controller past its dwell. Then

    python -m pytest tests/test_route_lease_maxtokens_tuning.py -q

on the UNFIXED tree must fail with
`RouteFirewallError: ROUTE_LEASE_MISMATCH role='conjecturer' seat=0
field=max_tokens expected=32768 actual=20480` — the recorded string, produced
offline, with no provider and no network.

Ruled out:
  - **The transport clamp at `llm/adapter.py:1193`**, the candidate PARKED.md
    P9-reach named but could not verify. It is a READER, not a producer:
    `transport_limits["max_tokens"] = getattr(endpoint, "max_tokens",
    lease.route.max_tokens)` copies whatever is already on the endpoint into the
    attempt trace, and it runs *after* `lease.verify(endpoint)` at
    `adapter.py:1146` — on this run it never executed at all, which is exactly
    why `20480` appears in no `workflow-token-reservation-v2` record in the
    root. The negative result P9-reach recorded is confirmed and now explained.
  - **A recurrence of a known trap.** `SUB-llm.md`, `CON-seats.md` and
    `INV-signal-contract.md` were all read before the record. None carries this
    failure; `CON-seats.md`'s "a clean compile says nothing about what its seats
    may do" is adjacent but concerns compile-time notices, not a mid-run
    mutation of a leased field. This is a NEW failure mode and earns a new
    `Traps` entry naming run `40e713b3…`.
  - **A glm-5.2 completion-cap burn.** The ledgered signature is zero completion
    tokens; `epoch1-repair-census.json` records
    `attempts_with_zero_completion_tokens: 0`, and the epoch-2 death carries no
    provider attempt at all. Raising `--maximum-completion-tokens` addresses a
    failure that did not occur, and would change the qualification subject digest
    and the run identity for nothing.

## The unrecorded sibling: the same mechanism kills in the other direction too

Stated here because the tranche's binding constraint is that a configuration
which compiles and qualifies must not be terminable mid-run by its own
components' lawful behavior — and closing only the narrowing direction leaves
that constraint unmet.

`cap_envelope` anchors a knob's ceiling as `max(static_max, configured_cap)`.
For `cap:conjecturer` the static maximum is 5000, so a QUALIFIED route whose
`max_tokens` is below 5000 — say 3000 — gets the barrier `[800, 5000]`. A
truncation rate above `TRUNC_HI` then licenses a widening to
`round(3000 * 1.6) = 4800`, above the leased 3000, and the very next dispatch
dies with the same `ROUTE_LEASE_MISMATCH`. No committed root shows this; it is a
prediction of the same mechanism, and `dr-reproduce` must demonstrate it
alongside the recorded one so that whichever direction the fix takes is proven
against both.

Note also, without weight on the diagnosis: the firewall's own refusal is
recorded under the tag `dropped-call`, which is `controller.TRANSPORT_DROP_TAG`
— the signal the controller reads to WIDEN the transport timeout. On a run that
survived one such refusal, the controller would answer a lease violation by
lengthening a wait. The run terminates first, so nothing acted on it here.
