# VALIDATION — verdict: PASS

Every acceptance check in `SPEC.md` §7, proven against the tree at
`bce018ae5` + Part B. Instruments run one at a time on an otherwise idle
box, per `dr-drive-harness` §5b.

## Instruments

| Instrument | Result | Baseline (`docs/AUDIT_BASELINES.md`) | Verdict |
|---|---|---|---|
| `python -m pytest tests/ -q -n 4` | **3737 passed, 6 skipped, 0 failed** (870.80s) | 0 failed | PASS |
| `python tools/docs_verify.py` (full) | **922 checks, 3 failed** — all `CON-run-identity.md:200/202/204` | 3 pre-existing shallow-clone `git log`/`git show` failures | PASS (baseline) |
| `python scripts/wheel_smoke.py` | **exit 0** — "isolated V6-only contents, clean imports, exact entry points, module parity, MCP registration, and exact MCP schemas" | exit 0 | PASS |
| `python -u scripts/wheel_operational_smoke.py` | see §Wheel-operational below | exit 0, with a KNOWN flake at the `reason` stage | see below |
| `census_probe.py` | 21/21 converted sites now `COMPILES+NOTICE` or clamped; the 2 non-converted rows unchanged | `census-before.txt` | PASS |

Test-count arithmetic, so the delta is auditable rather than asserted:
3703 (tranche base) → 3726 (Part A: +22 in
`test_all_configs_allowed_remainder.py`, +1 from splitting the scratch
fractions test) → 3737 (Part B: +11 in `test_seats_evidence_law.py`).

`docs_verify` check count 918 → 922: four new checks (one in
`SUB-manifest.md`'s new section, one in its new Traps entry, one in
`CON-criticism-source.md`, one in `CON-seats.md`), with three existing
checks in `SEAM-manifest-x-schools.md` rewritten in place from
raises-assertions to notice-assertions.

## Acceptance checks, per requirement

### Part A

**R1 — the remaining sites are converted.** 21 sites (census A1–A21). Proof:
`census-before.txt` vs `census-after.txt`, both committed, both produced by
the same committed probe.

**R2 — the worklist was re-derived fresh, with per-site proof.** `census_probe.py`
constructs each configuration and reports the OBSERVED outcome rather than
grepping for a `raise`. Two rows were re-classified by that re-derivation
and neither matched the park's own description:

- A21 did NOT refuse with the typed code the park predicted; it crashed with
  a bare `IndexError`.
- A22 (`_preflight_text_authority`) was `already-done` — converted by the
  2026-08-13 text-authority tranche — and was NOT re-converted.

**R3 — every conversion uses the pattern already on main.** No new
mechanism. `CompileNoticeV1` unchanged; `_emit_compile_notice` unchanged;
`_emit_deduped` widened by one optional keyword. The one NEW code,
`V6_CONTRACT_DECOMPOSITION_ROUTE_REQUIRED`, exists because that site had no
typed refusal to preserve.

**R4 — deterministic resolution, stated in SPEC.md.** Six conflicts resolve
rather than refuse, each with its rule in `SPEC.md` §4 and each with a test
asserting BOTH the winner and the `resolution` string:

| Conflict | Rule | Test |
|---|---|---|
| `allow_shared=False` vs shared bindings (school and criticism) | explicit bindings win | `test_route_bound_shared_seat_resolves_to_the_explicit_bindings`, `test_criticism_shared_seat_conflict_resolves_to_the_bindings` |
| `require_distinct_models` / `_families` vs bindings | explicit bindings win | `test_school_distinct_model_conflict_resolves_to_the_bindings`, `..._family_...` |
| inquiry vs control-plane `capability_profile` | control plane wins, policy rewritten | `test_capability_profile_mismatch_resolves_to_the_control_plane` |
| over-claimed scratch attention fractions | proportional clamp, ratio preserved | `test_reserved_attention_fractions_are_clamped_not_refused` |
| `cycles` over the ceiling | clamp to ceiling | `test_cycles_over_ceiling_clamps` |
| unresolved embedder model | fall back to hashing | `test_unresolved_embedder_model_falls_back_to_hashing` |

One conflict deliberately has NO resolution: `V4_CRITICISM_FOREIGN_COVERAGE_IMPOSSIBLE`.
The field is `ge=1`, so clamping to zero would invent a value the operator
did not ask for; the declared coverage stands and the point of use refuses
typed. `test_unsatisfiable_foreign_coverage_compiles_and_states_the_arithmetic`
asserts `notice.resolution is None` — the absence is pinned, not left to
chance.

**R5 — parse/shape errors still refuse.** Pinned from the other side:
`test_dangling_school_references_still_refuse`,
`test_unimplemented_capabilities_still_refuse`,
`test_reserved_attention_limits_are_bounded`,
`test_cli_validate_intake_still_exits_nonzero_for_a_shape_error`, and the
`SEAT_OUT_OF_RANGE` branch of
`test_policy_discloses_incomplete_or_impossible_topology`. `CENSUS.md`'s
"What deliberately still refuses" enumerates all six families.

**R6 — runtime unchanged.** No dispatch resolver was weakened. One runtime
line changed, and it gives an EXISTING failure a type rather than changing
behavior: `scheduler.py:1320`'s bare `RuntimeError` became
`SchoolRouteResolutionError("SCHOOL_ROUTE_CRITIC_ROLE_MISSING", ...)`, which
is a `RouteFirewallError`, which is a `RuntimeError` — every existing
`except RuntimeError` still catches it. The argument for doing this at all
is in `SPEC.md` §2: converting `V4_CRITICISM_BINDING_INCOMPLETE` makes that
line newly reachable, and shipping a newly-reachable UNTYPED crash is
exactly what §2.2 forbids converting into.

**R7 — pinned tests enumerated before being touched.** `SPEC.md` §5's table
(T1–T7), plus an ADDENDUM recording that the enumeration method was
incomplete: it grepped full codes, and four more tests (T8–T11) matched by
substring or prose. Three of those cost a full 17-minute gate to find. The
gap is in the method, and the method fix is written down.

**R8 — census artifact.** `CENSUS.md`, with the "configuration shape now
admitted" column and a ✔ marking each shape Part B attacks.

### Part B

**R9 — Part B started only after Part A's gate was green.** Part A's gate
(3726 passed, 0 failed) and `docs_verify` (3 baseline failures) ran and were
committed as `bce018ae5` before `tests/test_seats_evidence_law.py` existed.

**R10 — one new file, docstring names the law verbatim and this tranche.**
`tests/test_seats_evidence_law.py`. The docstring quotes both the law and
its binding clause word for word from CLAUDE.md, and names the tranche
directory.

**R11 — the attack list.** 11 cases covering every census shape that
touches seat binding, school routing, criticism policy, judge roles or
scratch (B1, B2, B3, B6, B7, B9, B10, B12, B13), plus the two
previously-constructible shapes named in
`experiments/2026-08-13-audit/proof/goal-L2.txt` (B14/B15: the distinct
`seat-bindings.yaml` and `criticism-seat-bindings.yaml` levers and
`resolve_criticism_seats`). B4/B5/B8/B11 are covered by
`test_all_configs_allowed_remainder.py`'s own compile-and-notice pins plus
B10's ensemble guard; SPEC §6's numbering is retained in the file's section
comments so the mapping is traceable.

**R12 — each case compiles, then the law is proven at the point of use.**
Every case calls `compile_run_manifest` (or `preflight_payload`) and
asserts it SUCCEEDS with a notice, before attacking. The typed refusals
that come back: `WellFormednessError` (B9), `JudgeEnsemblePolicyError`
(B10), typed trial decline recorded in the log (B7),
`SchoolRouteResolutionError` ×3 codes (B1/B2/B6), `RunManifestError` (B13).

**R13 — mechanism, not prose.** Assertions read `harness.warrants`,
`harness.state.status`, `harness.log.read()`, `manifest.compile_notices`,
`EndpointLease.route`, `ScratchAuthoringPolicyV1`'s Literal, and the typed
exception classes. `grep -n` over the file finds no assertion on generated
text.

**R14 — mutation proof.** Recorded in full in `CHECKLIST.md` S11: guard 1
(`Harness._validate_warrant`'s rubric branch) replaced with `if False:`,
the file went RED with `Failed: DID NOT RAISE WellFormednessError`, the
mutation was reverted with `git checkout --` and verified byte-identical to
a pre-mutation copy, and the file went GREEN again. Both runs pasted.

**R15 — the test joins the ordinary gate.** No pytest marks; it is part of
the 3737.

**R16 — no real violation surfaced.** All 11 cases pass; `grep -c xfail` on
the file returns 0. `PARKED.md` states this explicitly so the absence of a
finding reads as a result rather than an omission.

### Cross-cutting

**R17 — pre-granted scope respected.** `run_manifest.py`'s model AND
validators were changed together, as granted. No other frozen surface was
touched: `harness.py` is byte-identical to its pre-tranche state (proven by
the mutation-restore diff), `capabilities/state.py` is untouched, and
replay-validation record formats are untouched.

**R18 — the four pins did not need to move.** `IntakeFormV1`'s JSON Schema
sha is identical before and after (`eaf1f49c…` full, `6eec6554…` MCP-safe),
because the cycles ceiling lives only in a validator, never in a `Field`
constraint. `wheel_smoke.py` passes with its existing MCP schema pins, which
is the independent confirmation. FORM_DR1 not regenerated.

**R19 — cross-version replay proofs retired.** Not attempted, per CLAUDE.md's
2026-08-14 law. Current-version record integrity is covered by the gate.

**R20 — qualification-digest cost, reported not stopped.** `compile_notices`
is popped from BOTH serializations when `schema_version < 6 or not
compile_notices`, so a configuration that triggers NO notice is byte-identical
to before and its subject digest does not move — no requalification for any
previously-compilable configuration. A configuration that DOES trigger a
notice gets a different digest than an otherwise-identical notice-free
compile, and would cost one full battery (~14 min, ~1160 calls) — but every
such configuration was previously REFUSED, so it has no cached qualification
to invalidate. Net requalification cost of this tranche: **zero**.
`test_notice_free_compiles_record_nothing` pins the byte contract.

**R21 — gate discipline.** Ring while iterating, full gate at each boundary.
Baselines from `docs/AUDIT_BASELINES.md`. 0 failed at both boundaries; no
MCP-thread flake fired, so none needed isolating.

**R22 — the map moved in the same commits as the code.** Part A's commit
carried `SUB-manifest.md` (new section + Traps entry), `CON-schools.md`,
`CON-criticism-source.md` and `SEAM-manifest-x-schools.md` (three executable
checks rewritten). Part B's commit carries `CON-seats.md` and extends
`SUB-manifest.md`'s check to include the new test file.

**R23 — errata.** `docs/ERRATA.md` **E33**: the delivering tranche's HEADING
("compile-time denial abolished") claimed a completion its own body denied
three paragraphs later. The scan found exactly one such document; it is
recorded rather than rewritten, per the append-don't-rewrite rule.

**R24 — commit and push at every phase boundary.** Four pushes: capture,
spec+checklist, Part A, Part B/delivery.

**R25 — R-by-R reconciliation with pasted proof.** `DELIVERY.md`.

**R26 — no stops.** None taken. The one decision that genuinely needed the
operator (the v6 launch kill switch) was re-parked with a one-sentence
question rather than blocking the window.

## Wheel-operational smoke — the parked defect, not this tranche's

`python -u scripts/wheel_operational_smoke.py` exits 1. The failure matches
the parked signature REQUEST.md §3 named, on every field the park records:

```
--- assertion failed (reason) ---
terminal verification is incomplete
  File ".../scripts/wheel_operational_smoke.py", line 3565, in main
    _assert_resumable_terminal(resumable_result)
  File ".../scripts/wheel_operational_smoke.py", line 2061, in _assert_resumable_terminal
    raise AssertionError("terminal verification is incomplete")
```
failure envelope: `"stage":"reason"`, `"failure_kind":"assertion_failed"`,
`"mcp_liveness":"exited"`, and every `terminalization_phase_entry_counts`
counter at 0.

`experiments/2026-08-16-change-embedder-auto-install/PARKED.md` P1 records
the identical assertion at the identical line, at the identical stage, with
the identical envelope fields — and proves it PRE-EXISTING by running a
clean `git worktree` at `d52c739ff`, carrying none of that tranche's
changes, to the same failure. Observed there 3 times: passed once, failed
twice including the base, i.e. FLAKY rather than uniformly red.

Not attributed to this tranche, and the reasoning is checkable rather than
asserted: this tranche's diff cannot reach that assertion's inputs. It
requires `verification.completion_satisfied`,
`verification.epistemic_checks_passed`,
`verification.operational_checks_passed`, `completion_status == "satisfied"`
and `stop.reason == "converged"` — terminal-verification state produced by a
completed run. Nothing here touches terminalization, `verify_root`, or the
stop policy; the sole runtime line changed is a scheduler error's TYPE. The
companion `wheel_smoke.py`, which pins the public surface this tranche could
plausibly have moved (entry points, MCP tool set, schema shas, wheel
layout), exits **0**.

Per `docs/AUDIT_BASELINES.md` this remains a FINDING owned by that park, not
a baseline — it is not re-parked here, because P1 is already open and adding
a second entry for one defect makes the ledger worse.

## Known gaps this tranche did not close

Stated as gaps, not as work: `PARKED.md` P1 (the v6 launch kill switch —
needs the operator's word), P2 (seat-binding notice threading — blast radius
still unmeasured), P3 (`_cmd_validate_intake`'s now-unreachable advisory
branch), P4 (preflight notices reach stderr but not the typed run record).

P4 is the one a reader should weigh: under CLAUDE.md's own epistemology, a
disclosure that exists only on stderr is not evidence about the run.
Compile-time notices ARE in the record (`compile_notices` on the frozen
manifest); preflight-time notices are not, because the manifest is already
frozen when preflight runs. This tranche made them visible; it did not make
them evidence.

**Verdict: PASS.**
