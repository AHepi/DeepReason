# Reproduction

Form: offline unit reproduction (no provider, no network, no live run)

Artifact: `experiments/2026-08-22-fix-route-lease-maxtokens/repro.py`,
output preserved at `repro.json`. One command:

    python experiments/2026-08-22-fix-route-lease-maxtokens/repro.py

Fidelity: the lease is frozen from the endpoint object at adapter
construction — `LLMAdapter.__init__` → `leases_from_endpoints` →
`route_from_endpoint` — which is the same freeze every run performs; the
controller then mutates that SAME object mid-run, exactly as
`_apply_cap` does live; and the check is `lease.verify(endpoint)`, the call
`llm/adapter.py:1146` makes immediately before every provider request. The
route carries `max_tokens=32768` and `context_window_tokens=131072`, the two
values `run-config.yaml:27-28` declares.

## Current output (unfixed tree, verbatim)

    A/recorded: qualified route, efficiency narrowing
      leased_max_tokens                 32768
      context_window_tokens             131072
      controller_applied                {"cap:conjecturer": 20480}
      endpoint_max_tokens_after_tune    20480
      next_dispatch_refused             true
      error   ROUTE_LEASE_MISMATCH role='conjecturer' seat=0 field=max_tokens expected=32768 actual=20480

    B/predicted: qualified route, truncation widening
      leased_max_tokens                 3000
      controller_applied                {"cap:conjecturer": 4800}
      next_dispatch_refused             true
      error   ROUTE_LEASE_MISMATCH role='conjecturer' seat=0 field=max_tokens expected=3000 actual=4800

    C/control: unqualified route, same narrowing
      context_window_tokens             null
      controller_applied                {"cap:conjecturer": 20480}
      next_dispatch_refused             false
      error                             null

Case A's `error` string is **byte-identical** to the one in
`run/run-status.json` and at `run/log.jsonl` seq 577 of run
`40e713b30a147dfc1a0f73feb91fa67a493454f6103a452888b8e08713368c4c`.

Confirms diagnosis: yes — the controller alone produces `20480` from a leased
`32768`, and the refusal appears only when `context_window_tokens` is declared
(A refused, C identical but admitted). The single declared field is the
discriminator, which is precisely the conditional at
`llm/firewall.py:270-273`.

Case B additionally realises the unrecorded sibling the diagnosis predicted:
on a qualified route whose leased cap sits below the static envelope maximum,
a truncation signal licenses a widening ABOVE the lease and the same refusal
follows. No committed root shows this; it is now demonstrated offline. A fix
that closes only the narrowing direction leaves the tranche's binding
constraint — a configuration that compiles and qualifies must not be
terminable mid-run by its own components' lawful behavior — unmet.

## Post-fix expectation

`next_dispatch_refused` is `false` for **all three** cases, with case C
unchanged, and no assertion anywhere weakened to get there: an endpoint whose
`max_tokens` was NOT set by a logged controller policy — and every
non-`max_tokens` field, `context_window_tokens` above all — must still be
refused. The existing gate test
`tests/test_v6_request_envelope.py::test_runtime_endpoint_cannot_widen_frozen_capacity`
and `tests/test_model_firewall.py::test_endpoint_lease_allows_logged_process_tuning_only`
must both still pass unmodified; they are the two halves of the contradiction
and the fix has to satisfy both, not choose one.
