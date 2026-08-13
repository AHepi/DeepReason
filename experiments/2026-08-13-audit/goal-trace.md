# goal-trace.md — 2026-08-13 audit

Traces every STANDING operator design law in CLAUDE.md § "Operator
design laws" against code/test enforcement. Per-tranche law tracing
(REQUEST.md) is `dr-validate-change`'s job, not this one.

**No prior audit tranche under this skill family exists to diff
`proof/goal-laws.txt` against, so "laws added since the last audit" is
the full list below — this is the first census.**

| id | law | verdict | mechanism | test | proof file | disposition |
|---|---|---|---|---|---|---|
| L1 | Formalism is an option, never an obligation | enforced | `formally_backed` (`rules/warrants.py`, used by `oracle.py`, `rules/relatedness.py`, `informal/trial.py`) | `tests/test_oracle.py`, `tests/test_prose_refutation_boundaries.py` | proof/goal-L1.txt | baseline |
| L2 | Seats change GENERATED, never EVIDENCE | partially-enforced | generation/criticism seat-binding separation (`seat_bindings.py`) | `tests/test_seat_bindings.py` + 4 more | proof/goal-L2.txt | parked |
| L3 | A solo run with everything on must be an option | enforced | `single_model` handling (`run_manifest.py`, `cli/main.py`, `compat_eval.py`) | `tests/test_prose_refutation_boundaries.py` (explicit "solo-law compliance" test), `tests/test_model_firewall.py` + 4 more | proof/goal-L3.txt | baseline |
| L4 | Tokens are cheap; the agent is not | process-law | n/a (agent working-style rule) | n/a | proof/goal-L4.txt | baseline (enforced by CLAUDE.md's own "Build and test" section + the `dr-drive-harness` skill) |
| L5 | All configurations should be allowed | partially-enforced | `CompileNoticeV1`/`compile_notices` (`run_manifest.py` + 4 more sites) | many (`test_run_manifest.py`, `test_seat_bindings.py`, `test_config_scratch_bridge.py`, `test_manifest_integration.py`, `test_intake_form.py`, `test_run_manifest_scratch_bridge.py`) | proof/goal-L5.txt | parked |

**Count: 5 laws traced — 2 enforced, 2 partially-enforced, 1
process-law. 0 unenforced.**

## Detail

**L1 — Formalism is an option, never an obligation.** Mechanism scan
for `prose.immunity` hits `rules/warrants.py`'s `formally_backed()`
("Prose-immunity guard: True iff the target carries at least one
EVALUABLE AND SUBSTANTIVE commitment and EVERY such commitment
currently passes"), consumed by `oracle.py`, `rules/relatedness.py`,
`informal/trial.py`. Test scan finds it exercised in
`tests/test_oracle.py` and (by name) `tests/
test_prose_refutation_boundaries.py`. Both halves of X3's `enforced`
bar (mechanism file + a test that would go red on violation) are met.
**Verdict: enforced.**

**L2 — Seats change GENERATED, never EVIDENCE.** `seat_bindings.py`
does structurally separate generation-side and criticism-side seat
bindings (a distinct `CRITICISM_SEAT_BINDINGS_FILENAME`, a distinct
`resolve_criticism_seats`, tested across `test_seat_bindings.py` and
four more files) — real infrastructure, not prose. But the *specific*
invariant the law states — "no seat, mode, or package may let a
generation seat's prose skip criticism" — has no dedicated adversarial
test proving that invariant itself (as opposed to testing that seat
*bindings* resolve correctly). And the law's own citation,
`ROLE_SEAT_SEPARATION_PLAN.md`'s "S7 — packages" rung ("A package =
named preset bundling seat bindings + mode settings... joins
BEHAVIOR_MODES_PREPLAN"), is explicitly sequenced *after* S3–S6 and is
not yet built — the "package" concept this law's own citation names as
the guardrail's home is still a preplan. **Verdict:
partially-enforced** — mechanism (seat separation) exists, no test
pins the exact "cannot skip criticism" claim, and the plan's own
"packages" rung is unbuilt. Park: propose either (a) an adversarial
regression test that tries to construct a seat/mode/package
configuration and asserts criticism cannot be skipped, or (b) if S7
lands first, a test at that boundary instead.

**L3 — A solo run with everything on must be an option.**
`tests/test_prose_refutation_boundaries.py:1018` contains a test
docstring that names this exact law verbatim: *"Part C (S2a, R1)
solo-law compliance: the master reachability gate ... solo run — the
exact accommodation the operator's standing solo law requires (C3, 'no
configuration may strand solo runs')."* This is about as direct as
`enforced` evidence gets — a test that names the law by name. The
underlying `single_model` mechanism is broad (`run_manifest.py`,
`cli/main.py`, `compat_eval.py`) and tested across six more files
(`test_model_firewall.py`, `test_small_model_end_to_end.py`,
`test_run_manifest.py`, `test_continuation.py`,
`test_verify_workload_roots.py`,
`test_v6_contract_schema_repair_policy.py`). **Verdict: enforced.**

**L4 — Tokens are cheap; the agent is not.** This governs
agent/operator working style during a session (prefer live-run
evidence, run the targeted test ring instead of repeated full gates)
— there is no runtime code path a test can catch a "violation" of.
**Verdict: process-law.** Per the worker's own requirement to name WHO
enforces it: CLAUDE.md's own "Build and test" section states the rule
directly and records the 44-minute four-full-gate-runs mistake as its
standing cautionary example; the `dr-drive-harness` skill (loaded at
the start of every harness session, including this audit's own
ACTIVATION per-worker sequencing) carries it forward as the driving
manual every session — including `dr-audit-broken`'s own
`--lf`/targeted-ring guidance — is required to follow.

**L5 — All configurations should be allowed.** The
`experiments/2026-08-12-change-all-configs-allowed/` tranche shipped
`CompileNoticeV1`/`compile_notices`, converting roughly 13 compile-time
denial sites across `run_manifest.py`, `config.py`, `seat_bindings.py`
to typed disclosures, with tests across six files
(`test_run_manifest.py`, `test_seat_bindings.py`,
`test_config_scratch_bridge.py`, `test_manifest_integration.py`,
`test_intake_form.py`, `test_run_manifest_scratch_bridge.py`). But that
same tranche's own `DELIVERY.md` records R3 as `done-with-assumption
A5`: "~20 more sites census-complete, not code-complete," and its
`PARKED.md` P1 explicitly routes "convert the remaining CONVERT-SPEC'D
denials" to a follow-on `dr-change-orchestrator` tranche. The law as
stated ("**all** configurations should be allowed") is therefore not
yet fully realized — roughly 20 compile-time denial sites identified
by that tranche's own census still refuse rather than disclose.
**Verdict: partially-enforced.** Park: this is already self-parked by
the delivering tranche (P1) — this audit confirms P1 is still open (no
later tranche has closed it) rather than re-parking a duplicate.

## Laws added since the last audit

None to diff against — first audit tranche under this skill family
(see header note). All 5 laws above are the complete current census of
CLAUDE.md § "Operator design laws".

## Outlet note

Neither L2 nor L5's "impulse to build the missing enforcement" was
acted on now — both are parked (L5 pointing at the pre-existing P1
rather than duplicating it), per this worker's own Outlets table:
"Impulse to build the missing enforcement now → PARK — mechanism
prompt, route dr-change-orchestrator."
