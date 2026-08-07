# Spec for: qualification per seat — Rung S4 of role-seat separation
Traces: every item cites R/C numbers. Untraceable items are bugs.
Revision 2 — supersedes the first commit's "Option 2 recommended"
STOP per REQUEST.md's R11 amendment (operator's Q4 answer): the
required measurement (below, M5) has been RUN, PASSES, and the
delivered scope is **Option 2b**, per the operator's own branching
rule.

Map preflight: resolves to `DR-SUB-manifest` (qualification subject
digests — frozen surface 5), `DR-SUB-application` (`cli/main.py`,
`readiness.py`, `preparation.py`), `DR-CON-seats`. `docs/map/
INV-frozen-surfaces.md` re-read before writing this document.

## The finding this rung's design actually rests on (M1-M4, unchanged from revision 1 — S3's defect analysis stands per R12)

M1-M4 (revision 1's evidence, re-cited, not re-pasted — see git
history of this file for the full pasted commands): `deepreason
qualify` (as S3 shipped it) already qualifies the heterogeneous
manifest as ONE combination subject, not per-profile; this is what S2
originally called an SM9-forbidden combination. `RunPreparationService.prepare`
checks the SAME combination subject, which is why heterogeneous runs
were never actually broken by S3 — they work TODAY, exactly by virtue
of the thing S2 called untested. Revision 1 read this as a defect to
revert; R11's amendment reframes it correctly: **it was never proven
safe, not that it was wrong.** R12 keeps the M1-M4 record standing —
S3 shipped combination-subject qualification without the measurement
that makes it legitimate; this rung supplies that measurement, not a
revert.

## M5 — the required measurement (R11): does a heterogeneous manifest's battery dispatch each case to its OWN role's bound endpoint?

Executed live, not inferred from reading `production_contract_pairs`'
source (which revision 1 already cited statically — R11 explicitly
asked for a RUN, not a re-read). Script (preserved verbatim in this
tranche as `measure_dispatch.py`, promoted to a committed regression
test at Item S1 below):

```python
manifest = build_preparation_manifest(
    default_profile,  # model_id="model-default"
    question="Why is the sky blue?",
    compiled_at=...,
    seat_bindings={"conjecturer": profile_a, "judge": profile_b},
    # profile_a.model_id="model-a", profile_b.model_id="model-b"
)
pairs = production_contract_pairs(manifest)
# monkeypatch deepreason.llm.adapter._endpoint_from_spec to return a
# FakeEndpoint per (model_id, endpoint_id) that RECORDS every
# .complete() call's model_id into dispatch_log, returns a stub "{}"
# (deliberately schema-invalid, to force repair retries and prove
# purity survives retries too, not just the first attempt)
for role in ("conjecturer", "judge"):
    dispatch_log.clear()
    exercise_production_contract_case(manifest, by_role[role][0], 0)
    print(role, "expected", by_role[role][0].model_id, "got", dispatch_log)
```

Output:
```
roles model_ids: {'conjecturer': ['model-a'], 'argumentative_critic': ['model-default'], 'defender': ['model-default'], 'variator': ['model-default'], 'judge': ['model-b'], 'summarizer': ['model-default'], 'synthesizer': ['model-default'], 'vision_critic': ['model-default'], 'property_designer': ['model-default'], 'thesis': ['model-default'], 'grounding_reviewer': ['model-default']}
total pairs: 15
roles with pairs: ['argumentative_critic', 'conjecturer', 'judge', 'summarizer', 'synthesizer', 'thesis']
target roles found: ['conjecturer', 'judge']
role=conjecturer expected_model=model-a calls=['model-a', 'model-a', 'model-a', 'model-a', 'model-a'] PURE=True
role=judge expected_model=model-b calls=['model-b', 'model-b'] PURE=True
ALL ROLES DISPATCH-PURE (zero cross-contamination): True

role=summarizer expected_model=model-default calls=['model-default']
PURE: True
```

Every dispatched call (including all schema-repair retries — the
stub response is deliberately invalid, so `V6PatchRepairSession`
retries several times per case) targeted EXACTLY the model its OWN
`ProductionContractPairV1.model_id` named, for all three roles tested
(two explicitly bound to different profiles, one left on the default)
— **zero cross-contamination between roles bound to different
profiles in one heterogeneous manifest.** Traced to why: `cli/doctor.py`'s
`exercise_production_contract_case` resolves `route =
manifest.roles[pair.role][pair.seat]` then `_endpoint_from_spec(route.endpoint_spec())`
freshly, per call, from THIS pair's own route — there is no shared,
cacheable, or otherwise leakable endpoint state across roles.

**Measurement verdict: PASSES.** Per R11's branching rule, this
authorizes **Option 2b**.

## M6 — does `prepare()` already refuse typed for an unqualified combination, with ZERO new code? (measured, not assumed)

```python
service = RunPreparationService(..., qualification_executor=None)
# two-profile home, seat bound to a DIFFERENT, never-qualified profile
service.prepare(request)
```
Output:
```
REFUSED TYPED: QualificationError QUALIFICATION_NOT_CONFIGURED: no completed reusable qualification exists for this exact subject
```
This is the EXISTING `resolve_completed_qualification`/
`RunPreparationService.prepare` code path (S3, unmodified) — it
already raises a typed refusal for a heterogeneous manifest whose
combination has never been qualified, with **zero lines changed**.
Combined with M5, R4's literal acceptance ("refuses typed when the
combination's battery is absent") is **already satisfied by S3's
existing, unmodified code**, now that M5 proves the combination it
checks is dispatch-correct.

## Option 2b — what actually needs building (much smaller than either revision-1 option)

Given M5+M6, the delta this rung needs to add is:

1. **`deepreason qualify` gains a per-profile loop (R1) ALONGSIDE its
   existing combination-qualify (unchanged, M1/M6).** When seat
   bindings exist: qualify the COMBINATION exactly as S3 already does
   (unmodified code path — this is what launch depends on, per M6),
   AND additionally loop over each DISTINCT bound profile (deduped by
   `profile_digest`) qualifying each UNIFORMLY (`qualification_subject_manifest(profile)`,
   no seat_bindings) — for `status`/readiness granularity (R3), not
   because launch needs it (M6 already shows it doesn't).
2. **`deepreason status` gains per-seat readiness (R3)**, reading the
   per-profile uniform subjects the loop above caches.
3. **No changes to `preparation.py`, `qualification.py`'s digest/
   report functions, or `cli/doctor.py`'s validators** — M6 proves
   `prepare()`'s existing refusal already does R4's job correctly.
4. **Rung S4b parked** (Option 1 from revision 1: per-role provenance,
   so N models mix freely without a fresh full battery per NEW
   combination) — real future value (cost), not required for
   correctness (M5/M6 already prove correctness), real frozen-surface-5
   contact when it is eventually built, gated at its own future spec.

## Items

S1 (R11, M5): Promote the dispatch-purity measurement to a committed
regression test — `tests/test_qualification_per_seat.py`, asserting
`ALL ROLES DISPATCH-PURE` for a 3-role heterogeneous manifest
(2 explicitly bound + 1 default), mutation-proven (a companion test
temporarily makes `exercise_production_contract_case` share one fake
endpoint across roles and confirms the purity assertion WOULD catch
that — proving the test can fail, not only that it currently passes).
accept: `python -m pytest tests/test_qualification_per_seat.py -q -k dispatch_purity`
passes; the mutation-companion test passes (proving the main test is
not vacuous).

S2 (R1, R2): `_cmd_qualify`'s per-profile loop. Walk `("default",
base_profile)` plus every DISTINCT profile named by
`load_seat_bindings()`'s raw `{group: path}` entries (deduped by
`profile_digest`, EXCLUDING any equal to the default's own digest —
no redundant re-qualification), each via the EXISTING single-profile
logic (extracted into a reusable per-profile body, called with NO
`seat_bindings`, R5's "one profile, uniformly bound, per pass" now
satisfied for THIS loop specifically) — reusing `qualification_subject_digest`/
`qualification_subject_payload` unchanged (S2's own SM7, R2).
**The EXISTING combination-qualify call (S3's, unmodified) still runs
too**, when seat bindings exist — this loop is additive, not a
replacement.
accept: single-profile home — loop has exactly one iteration whose
payload/output is byte-identical to pre-S4 (R6); two-distinct-profile
home — per-profile loop qualifies both PLUS the existing combination
call still qualifies the combination; output names all three
outcomes (2 profiles + 1 combination) without conflating them.

S3 (R3): `readiness.py` gains `get_seat_readiness(*, environ=None,
home=None) -> tuple[SeatReadinessV1, ...]` — for `"default"` plus
each RAW `{group: path}` entry, resolve the profile and compute
readiness via the per-profile uniform subject (the SAME logic
`get_readiness` uses, extracted into a shared helper). `ReadinessV1`/
`get_readiness`/the MCP `get_readiness` tool are UNTOUCHED
(packaging-surface-free — confirmed unchanged, unlike revision 1
this is not newly re-derived, same reasoning holds).
accept: no bindings — `()`; two bound groups — 2 entries with correct
per-profile `qualification_state`, independent of whether the
COMBINATION itself has been qualified (per-seat readiness answers
"is THIS seat's own profile provably capable," not "can a run launch
right now").

S4 (R3): `_cmd_status` — when `get_seat_readiness()` is non-empty,
print an ADDITIONAL "Per-seat readiness" section (text) / a `"seats"`
key on a new wrapping JSON object (`--json`); empty (R6) — byte-
identical to today, branch never taken.
accept: single-profile home output diffed against a pre-S4 capture,
empty; two-seat home additionally names both seats.

S5 (R4): confirmed NO code change needed (M6) — but ADD one
regression test proving it, since "already works" is exactly the kind
of claim that silently rots without a pinned assertion: a two-profile
home where the COMBINATION is unqualified refuses typed
(`QUALIFICATION_NOT_CONFIGURED`, or whichever code the existing path
raises — pinned exactly, not paraphrased); once the combination IS
qualified (via an injected test executor), `prepare()` succeeds and
the committed run manifest's roles reflect both profiles correctly.
accept: `python -m pytest tests/test_run_preparation_service.py -q -k combination`
— both the refusal and the success halves pass.

S6 (R6): single-profile-home byte-identity for `deepreason qualify`/
`deepreason status`, proven directly: capture output before this
tranche's commits land, recapture after, diff empty.
accept: both diffs empty.

S7 (R8): full gate, 0 failed (net of the already-diagnosed,
independently-reconfirmed pre-existing P1/P3 failure from Rungs
S1/S3's `PARKED.md`, reconfirmed fresh for this tranche's own commit
range).

S8 (R9): sweep byte-identical, 45 roots, before/after this tranche's
edits.

S9 (R10, R11): no `RunManifest`/`Config` schema change anywhere in
this tranche's diff (confirmed: S1-S6 above are all `qualification.py`/
`cli/main.py`/`readiness.py`/`preparation.py`-adjacent function
bodies and one new test file — no schema touched); Rung S4b (Option 1)
recorded in `PARKED.md` as a real, future, frozen-surface-5-gated
tranche, not built here.

## Assumptions (operator may override)

A1 (from revision 1, unchanged): "the rung-6/fingerprint gating
shape" = lazy, checked-at-use gating (confirmed against
`experiments/2026-08-04-change-rung6-plugin-conformance/SPEC.md`) —
moot for THIS revision's actual delta (M6 shows the check already
exists and already fires at the right time), kept for the record.
A2 (from revision 1, unchanged): "distinct bound profiles" = default
+ every profile named by `load_seat_bindings()`'s raw entries, deduped
by `profile_digest`.
A3 (from revision 1, unchanged): the qualification-completeness check
lives in `RunPreparationService.prepare` — confirmed, and now shown
to require ZERO new code there (M6), only a pinning test (S5).
A4: the per-profile loop (S2) EXCLUDES a bound profile whose digest
equals the default's own — assumed to avoid literally re-running the
same battery under two labels; operator may override toward always
listing it (harmless, only affects a "which seats does this cover"
display nuance, not a materially different behavior).

## Questions for operator

(none — R11's amendment resolved revision 1's Q4; the measurement it
required has been run and its outcome determines this revision's
scope per the operator's own branching rule, with no further fork.)

## Out of scope (explicit)

- Rung S4b (Option 1: per-role provenance, so N models mix freely
  without a fresh combination battery) — parked, not built, its own
  future frozen-surface-5 gate stands per R11.
- Any `RunManifest`/`Config` schema change (R10; Rung S5's scope).
- The `experimenter`-template routing gap (S3's own A4) — unrelated.

## Frozen-surface contact forecast

**None.** `qualification.py::project_qualification_report`,
`cli/doctor.py::validate_production_contract_qualification`, and all
5 `require_v6_production_qualification` call sites are untouched —
M6 proves they already do the right thing for combination-subject
qualification once M5 proves that subject is dispatch-correct. This
is a measured "none," not an assumed one: M5+M6 are the measurement
this forecast rests on, not a repetition of S2/S3's forecasts.

## Blast-radius census

```
$ grep -rn "_cmd_qualify" tests/ docs/map/
docs/map/SUB-manifest.md:164 (names _cmd_qualify collectively, not exact-shape-pinning)
```
```
$ grep -rln "get_readiness" tests/ docs/map/
tests/test_end_user_attachments.py, tests/test_webapp.py, tests/test_qualification_tier.py, tests/test_mcp_help.py, tests/test_mcp.py, tests/test_public_v6_facade.py
```
MUST NOT MOVE — `ReadinessV1`/`get_readiness` untouched; `get_seat_readiness` additive.
```
$ grep -rln "resolve_completed_qualification" tests/ docs/map/
tests/test_reusable_qualification.py, tests/test_qualification_tier.py, tests/test_public_v6_facade.py, docs/map/SUB-manifest.md
```
MUST NOT MOVE — unchanged function, unchanged call shape for the
single-profile case; the heterogeneous case already worked (M6),
newly pinned (S5), not newly built.
```
$ grep -rn "project_qualification_report\|validate_production_contract_qualification" tests/ docs/map/ | wc -l
```
(re-verified at Item S7's execution) — expected unchanged, since
neither function's body is touched under Option 2b.

## Budget

Estimated 150-250 lines (Option 2b) — smaller than revision 1's
Option 2 estimate (250-400), because M6 removed the need for any
`preparation.py`/`qualification.py` refusal-path changes entirely:
`cli/main.py` (`_cmd_qualify`'s additive per-profile loop, ~60-90
lines), `readiness.py` (`get_seat_readiness`/`SeatReadinessV1`,
~50-70 lines), `cli/main.py::_cmd_status` (~20-30 lines), tests
(~100-150 lines: dispatch-purity regression + mutation companion,
combination-refusal/success pinning, single-profile byte-identity).
Frozen surfaces touched: **none** — measured (M5, M6), not forecast.

Rubric: 6/6 yes — every R has a spec item (R4 via S5's pinning test,
not new production code — a legitimate "done" per M6's measurement);
blast-radius census pasted, every hit classified; frozen-surface
contact forecast recorded as measured none; every mechanism named
(the measurement itself, SM7, SM9, rung-6 shape) traced to real
executed evidence, not re-assumed from revision 1; EXECUTE request
with a genuine mid-spec measurement gate, handled per R11's own
branching rule, not invented; nothing above is untraceable to an
R/C number.
