# Diagnosis: the `workflow-call-pairing` exact-pair comparison omits the empty-string→None normalization every writer and every other reader applies

Primary cause: **(b) the checker over-specifies.** `ProviderAttemptV1.raw_ref` is typed
`str | None` — absence is `None`. `LLMCall.raw_ref` is typed plain `str` — absence is `""`.
The two record types therefore spell "the provider returned no usable body" differently, and
the codebase translates between them at every boundary with the idiom `call.raw_ref or None`.
`invariants.py:398` is the one site that does not: it compares `attempt.raw_ref == call.raw_ref`
raw. Because the WRITER (`transaction_service.py:529`) applies `or None` unconditionally, an
attempt built from a call with an empty `raw_ref` ALWAYS has `raw_ref is None`, so line 398's
`None == ""` is False by construction. The sixth of the six pairing agreements is therefore
UNSATISFIABLE for the entire class of attempts whose provider was reached but returned no body
— `outcome="transport_failure"` — no matter what the run did. The other five agreements
(work id, bundle ref, contract id, route lease, prompt digest) all held in the observed event.
The repair ladder is not the cause; it is only the shortest reachable route to that class,
because the soak's inducer makes the stub answer with HTTP 500.

Evidence:
  - `scripts/cycle_soak.py --case epoch3 --induce-repairs 2` → soak-report.json:
    `A1-typed-terminal` PASS (`state='completed'`, `stop_reason='budget_exhausted'`),
    `A4-cycles-reached` PASS (cycle 8 of 8), `attempts.repairs == 1`, and
    `A3-verify-root-clean` FAIL with the single violation
    `{'check': 'workflow-call-pairing', 'detail': 'event seq=31: provider result differs from
    its authorized attempt'}`. The run is operationally clean; only the checker objects.
  - `log.jsonl` seq=31, read read-only through `Harness(root, read_only=True)`:
    `event.llm.raw_ref == ''`, `tokens == 0`, and the attempt trace carries
    `usage_unknown: true`, `valid: false`, `transport_attempts: 4`, four
    `HTTPError:HTTP-500` diagnostics. The paired `workflow-provider-attempt-v1` output has
    `raw_ref = None`, `outcome = 'transport_failure'`, and its
    `authorization_bundle_ref`/`prompt_sha256` MATCH the event's
    `dispatch_authorization_ref`/`prompt_ref`. Exactly one of the six agreements differs, and
    it differs only as `None` vs `''`.
  - `invariants.py:3775-3779`, the `blobs` check — **the same file already rules the opposite
    way on the same fact**: `empty_raw_allowed = bool(trace and trace[-1].usage_unknown)`, and
    an empty `e.llm.raw_ref` is skipped rather than failed when that holds. Line 398 rejects
    the record shape that line 3778 explicitly permits. `verify_root` contradicts itself.
  - Witness-class census over every committed run root (14 roots carrying
    `objects/workflow-provider-attempt-v1/`, 459 attempts total): `transport_failure` = 0,
    `raw_ref: null` = 0. **No committed root exercises this class at all** — which is why the
    defect has never been seen in the wild, and why the induced witness is the only one
    available. Recomputable:
    `find experiments runs -path '*workflow-provider-attempt-v1/*.json' -exec grep -l 'transport_failure' {} + | wc -l`
  - Three further sites encode the same normalization the checker omits, so the writer's
    spelling is the codebase's settled one, not an accident:
    `workflow/transaction_service.py:529` (`raw_ref=call.raw_ref or None`),
    `workflow/replay.py:2499` (`attempt.raw_ref != (call.raw_ref or None)` — the SAME six
    agreements, in replay's `workflow-replay` check, which PASSED on this very root),
    `workflow/replay.py:1464` (`(getattr(call, "raw_ref", None) or None) != proposal.raw_ref`).
  - `workflow/transaction.py:394` — the model's own validator: `raw_ref is None` is refused
    only when `outcome == "provider_result"`. A `None` raw_ref on a `transport_failure`
    attempt is not merely tolerated, it is the shape the type demands.

Implicated code: `src/deepreason/invariants.py:398` (the single comparison); read-only
corroboration at `src/deepreason/workflow/transaction_service.py:529` and
`src/deepreason/workflow/replay.py:2499`.

Falsifiable prediction: if this diagnosis is right, then a `ProviderAttemptV1` with
`outcome="transport_failure"`, `raw_ref=None` and all five other agreements intact, paired with
its `LLMCall` carrying `raw_ref=""`, must be the MINIMAL record that reproduces the finding —
and changing nothing but the checker's sixth agreement to `attempt.raw_ref == (call.raw_ref or
None)` must clear it while every other agreement still fires when broken. Command:
`python -m pytest tests/test_v6_transport_failure_pairing.py -q` RED on the unfixed tree, GREEN
after, with each of the five surviving agreements individually mutated to prove the check did
not simply go blind.

Ruled out: **(a) the repair transaction's WRITER emits an ill-paired call record.** PARKED.md P1
nominated the adapter's `attempt != 0` clamp
(`WorkflowAuthorizationError("transactional repair requires a new authorization bundle")`) as a
suspect with a hole. It has none, and the record shows why: the failing event's attempt trace
records `attempt: 0` with FOUR `transport_attempts`, i.e. one authorized semantic attempt whose
transport was retried inside the endpoint — never a second authorized attempt. The clamp had
nothing to fire at. The writer's output is correct and internally consistent: every one of the
six values it wrote agrees with the bundle, and the sixth agrees under the same translation the
writer itself performed one line earlier. Fixing the writer instead would mean widening
`LLMCall.raw_ref` to `str | None`, which is a LOG FORMAT change on a frozen-adjacent surface to
work around a reader — the exact inversion of `INV-frozen-surfaces`'s governing asymmetry
("readers may be fixed freely, writers and formats may not").

Note for the fix phase: contact with FROZEN surface 3 (`invariants.py`, replay-validation
formats) is unavoidable — the defect IS in that file. The grant must be requested in FIX.md
before implementation, per the tranche instruction. `DR-SUB-verification`'s own Traps section
states the sanctioned direction for exactly this file: "the predicate may only ever ADD
authorized values, never remove one, or a committed root changes meaning." This fix adds one
authorized value (`None` where the call side is `""`) and removes none.
