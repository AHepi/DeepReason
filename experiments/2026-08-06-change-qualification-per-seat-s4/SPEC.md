# Spec for: qualification per seat — Rung S4 of role-seat separation
Traces: every item cites R/C numbers. Untraceable items are bugs.

Map preflight: resolves to `DR-SUB-manifest` (qualification subject
digests — frozen surface 5), `DR-SUB-application` (`cli/main.py`,
`readiness.py`, `preparation.py`), `DR-CON-seats`. `docs/map/
INV-frozen-surfaces.md` re-read before writing this document; surface
5 ("Anything altering qualification subject digests — qualification.py")
is the surface this spec's central finding lives right up against.

## The central finding (read this before the items below)

**Honoring R5 (this tranche's own non-goal, inherited from S2) breaks
an EXISTING, unrelated invariant that Rung S3 depends on — not a
hypothetical, a measured fact.**

M1 — `deepreason qualify`'s CURRENT body (as S3 left it) already
qualifies the MIXED/heterogeneous manifest, not a uniform one:
```
$ sed -n '1562,1566p' src/deepreason/cli/main.py
        manifest = qualification_subject_manifest(
            profile,
            attached_evidence=bool(getattr(args, "attached_evidence", False)),
            seat_bindings=resolve_seat_bindings() or None,
        )
```
This is the EXACT SM9-forbidden combination S2's SPEC.md named as a
non-goal ("never qualify a profile inside a manifest that mixes it
with other seats' different bindings") — S3 shipped it anyway,
because S3's own acceptance criteria (a MockEndpoint routing unit
test, sweep byte-identical for the NO-bindings case) never exercised
`deepreason qualify` with actual bindings present. This is a genuine
defect in S3's delivery, not a new decision — R5 is the operator
asking for it to be corrected.

M2 — `RunPreparationService.prepare` qualifies/validates against the
SAME (currently mixed) manifest, and this consistency is WHY
heterogeneous runs currently launch at all:
```
$ sed -n '613,626p' src/deepreason/preparation.py
        else:
            dossier, run_input, workload = _records_for_question(request.question)
        seat_bindings = resolve_seat_bindings(environ=self._environ, home=self._home)
        manifest = build_preparation_manifest(
            profile,
            question=request.question,
            compiled_at=_compiled_at(self._clock),
            run_input_digest=run_input.run_input_digest,
            attached_evidence=request.dossier_digest is not None,
            seat_bindings=seat_bindings or None,
        )
        try:
            bundle = resolve_completed_qualification(
                manifest,
```
Both `_cmd_qualify` and `prepare()` build the SAME heterogeneous
manifest and compute the SAME (mixed) subject digest from it — so
today, a two-seat home's single mixed-manifest qualification, once
run, satisfies BOTH `qualify` and `prepare`'s checks. Fixing R5 (M1)
removes the ONLY thing that made M2 self-consistent.

M3 — `project_qualification_report` (which `prepare()` calls
immediately after `resolve_completed_qualification`, to build the
report it persists into the run root) INTERNALLY re-derives the
subject digest from whatever manifest it is given and REQUIRES it to
equal `bundle.subject_digest`, or refuses typed:
```
$ sed -n '728,741p' src/deepreason/qualification.py
def project_qualification_report(
    bundle: ReusableQualificationBundleV1,
    manifest: RunManifest,
    profile: ProviderProfileV1,
) -> ProductionContractDoctorReportV1:
    """Bind reusable sanitized cases to one exact manifest and validate it."""

    subject_digest = qualification_subject_digest(manifest, profile)
    if bundle.subject_digest != subject_digest:
        raise QualificationError(
            "QUALIFICATION_SUBJECT_MISMATCH",
            "completed qualification evidence does not cover this exact behavior subject",
        )
```
Once R5 is honored (M1's fix), `bundle` can ONLY ever come from a
UNIFORM per-profile qualification pass (that is what "one profile,
uniformly bound, per qualification pass" means). Passing the RUN's
own heterogeneous `manifest` here will ALWAYS raise
`QUALIFICATION_SUBJECT_MISMATCH`, because a heterogeneous manifest's
`manifest_behavior` (which includes `roles`) differs from the uniform
one `bundle` was built against. **There is no manifest object that
satisfies both "is the run's real, dispatch-correct, heterogeneous
shape" and "digest-matches a bundle that SM9 forbids ever producing."**

M4 — this is not a local, one-call problem: the same equality
(`report.run_manifest_sha256 == manifest.sha256`, a DIFFERENT,
whole-manifest hash check, layered on top of M3's subject-digest
check) is re-enforced by `validate_production_contract_qualification`
(`cli/doctor.py:1378-1401`), invoked via `require_v6_production_qualification`
(`runtime/launch_policy.py:176-241`) from **5 separate call sites**,
not just `prepare()`:
```
$ grep -rn "require_v6_production_qualification(" src/deepreason --include="*.py" | grep -v "def require_v6"
src/deepreason/cli/main.py:2421:            require_v6_production_qualification(
src/deepreason/application/text_runs.py:794:        require_v6_production_qualification(
src/deepreason/ops.py:360:            qualification = require_v6_production_qualification(
src/deepreason/bridge/transactional_adapter.py:251:        qualification = require_v6_production_qualification(
src/deepreason/scratch/authoring.py:238:        self._classification_report = require_v6_production_qualification(
```
`ops.py`'s call site is inside `run_scheduler` — checked on ordinary
cycle dispatch, not only at prepare-time. Even if `prepare()` could
somehow be made to succeed for a heterogeneous manifest, the SAME
equality would be re-enforced on the FIRST reasoning cycle, and on
every `continue`.

**Conclusion: making R5 true (which R4's own acceptance depends on,
since a stale mixed-subject cache is not a real fix) makes any
genuinely heterogeneous run (2+ DIFFERENT bound profiles) refuse
`QUALIFICATION_SUBJECT_MISMATCH` at prepare time under the CURRENT
validation chain — regardless of whether every individual seat is
qualified.** Making a heterogeneous run actually LAUNCH and RUN
successfully requires changing what "this manifest is qualified"
MEANS — from "one whole-manifest digest match" to "every role's
route is separately provenanced to its own seat's qualification" —
and that is a real change to `qualification.py::project_qualification_report`
and `cli/doctor.py::validate_production_contract_qualification`,
exercised at all 5 call sites above. This is frozen-surface-5
territory (`INV-frozen-surfaces.md`: "Anything altering qualification
subject digests... qualification.py") by the map's own definition,
not a stretch of it.

## Re-reading R7's actual acceptance text (this narrows, not widens, the stop)

R7, quoted exactly: **"a two-profile home qualifies both and refuses
typed when one battery is absent."** This is two claims: (a)
`deepreason qualify` handles two profiles (R1 — clean, no frozen
contact, M1's own fix is entirely inside `_cmd_qualify`); (b) refusal
happens when a battery is missing (R4 — also achievable cleanly, see
Item S3 below). **R7 does not assert that a run SUCCEEDS once both
batteries are present** — that stronger claim (successful
heterogeneous LAUNCH) is the one M3/M4 show requires frozen-surface-5
contact, and it is not literally what any R number asks for. This
spec delivers R1-R3, R5, R6, R8-R10 in full, delivers R4 as a
CLEAN, always-correct preflight refusal, and treats "a run with all
its seats qualified successfully launches and reasons" as the ONE
open question requiring operator words before any code touching
`qualification.py`/`cli/doctor.py`'s validators is written.

## Options for closing the gap (priced; none chosen without operator words)

**Option 1 — extend the validation chain to per-role provenance.**
`project_qualification_report`/`validate_production_contract_qualification`
change from "one bundle, one whole-manifest digest" to "every
`(role, seat)` in the manifest has its own bound profile's cached
qualification, verified independently." Likely needs a new wrapper
report type (or a restructured `ProductionContractDoctorReportV1`)
carrying per-role provenance instead of one flat subject digest, and
every one of the 5 `require_v6_production_qualification` call sites
re-verified against both the unchanged single-profile shape AND the
new heterogeneous shape. Frozen-surface-5 contact: real, deliberate.
Estimated 400-700+ lines — larger than this rung's own budget so far,
arguably its own rung. Risk: high (correctness-sensitive, touches
code re-checked on every cycle dispatch, 5 call sites, replay-adjacent
via `ops.py`'s per-cycle check).

**Option 2 (recommended for THIS rung) — deliver R1-R3, R5, R6,
R8-R10 in full; R4 becomes an always-typed, always-correct preflight:
`deepreason reason` refuses (a) if any bound seat's OWN profile lacks
a completed qualification (the useful, literal part of R4), AND (b)
unconditionally, with a distinct typed reason, if 2+ DISTINCT profiles
are bound at all — naming this a scoped program limit, not a bug:
"heterogeneous seat launch is not yet wired past qualification;
`deepreason qualify`/`deepreason status` fully support per-seat
operation, `deepreason reason` does not yet dispatch a run whose seats
differ — tracked for a follow-on rung."** Zero frozen-surface contact.
Every part of R1-R10's literal text is satisfied; the residual gap
(successful heterogeneous launch) is named, not hidden, and parked
with Option 1's pricing as its ready-to-run follow-on. Estimated
250-400 lines for THIS rung.

**Option 3 — revert S3's `_cmd_qualify` mixing (M1) is left AS-IS
(do not honor R5), so heterogeneous runs keep "working" exactly as
today by continuing to qualify the mixed manifest as one unit.**
Rejected outright — this is the operator's own R5, quoted verbatim,
and directly contradicts S2's SM9 non-goal this program has already
committed to; keeping a known-forbidden combination working by NOT
fixing it is not a real option, only priced here for completeness.

Recommendation: **Option 2.** It is the only one that fits inside
"one rung only," delivers everything R1-R10 literally asks for, and
turns M3/M4's finding into an honest, typed, zero-frozen-surface
refusal rather than either an obscure crash or unauthorized
frozen-surface contact.

## Items (Option 2's scope — pending operator confirmation)

S1 (R1, R5, M1): Fix `_cmd_qualify` to stop the SM9-forbidden mixing:
remove `seat_bindings=resolve_seat_bindings() or None` from its
`qualification_subject_manifest` call (the base/default profile is
ALWAYS qualified uniformly, exactly as before S3's regression); walk
`("default", base_profile)` plus every DISTINCT profile named by
`load_seat_bindings()`'s raw `{group: path}` entries (each resolved
via `resolve_provider_profile`, deduped by `profile_digest` for
EXECUTION — one battery per distinct profile, not per group label),
each qualified via the EXISTING single-profile logic (extracted into
a reusable per-profile body), each with NO `seat_bindings` passed to
`qualification_subject_manifest` (R5).
accept: single-profile home (no `--seat` bindings, or all bindings
resolve to the default's own digest) — `payload` shape byte-identical
to pre-S4 output (no new keys, no wrapping); two-distinct-profile home
— both battery-qualified (or cache-reused), aggregate JSON/text output
names both.

S2 (R2): No new digest logic — reuse `qualification_subject_payload`/
`qualification_subject_digest` exactly as they exist (S2's SM7); S1's
fix only changes WHICH manifests get built and passed in, never the
digest FUNCTION itself.
accept: `git diff` shows zero lines changed in
`qualification_subject_payload`/`qualification_subject_digest`.

S3 (R4, clean preflight half): new `require_all_seats_qualified(default_profile,
seat_bindings, *, cache_dir) -> None` in `qualification.py` — for
every profile in `seat_bindings.values()` whose `profile_digest`
differs from `default_profile.profile_digest`, build ITS OWN uniform
`qualification_subject_manifest(profile)`, check
`load_completed_qualification`, raise a new typed
`QualificationError("QUALIFICATION_SEAT_UNQUALIFIED", ...)` naming the
unqualified profile's provider/model on the first miss. Called from
`RunPreparationService.prepare` right after `seat_bindings` is
resolved, only when `seat_bindings` is non-empty.
accept: unit test — two bound profiles, one battery cached, one
missing, `prepare()` raises `QUALIFICATION_SEAT_UNQUALIFIED` naming
the missing one; both cached, this check passes (does not itself
raise — S4 below still refuses for a different, honestly-scoped
reason).

S4 (R4, the honest scope boundary, Option 2): `RunPreparationService.prepare`
refuses typed (`RunPreparationError("QUALIFICATION_HETEROGENEOUS_LAUNCH_NOT_SUPPORTED",
...)`) whenever 2+ DISTINCT profiles are bound (checked AFTER S3's
per-seat completeness check, so the error message is maximally
specific: "all N seats are individually qualified; heterogeneous
launch itself is not yet wired — see PARKED.md" vs. "seat X is
unqualified"). Single-profile homes (R6) never reach this branch —
`len(distinct profiles) <= 1` is the untouched, existing code path.
accept: two-profile home, both qualified — `prepare()` raises
`QUALIFICATION_HETEROGENEOUS_LAUNCH_NOT_SUPPORTED`, NOT
`QUALIFICATION_SUBJECT_MISMATCH` (the honest, typed, chosen refusal,
not an accidental one); single-profile home — `prepare()` behavior
unchanged (S1 gate test + existing test suite, byte-identical).

S5 (R3): `readiness.py` gains `get_seat_readiness(*, environ=None,
home=None) -> tuple[SeatReadinessV1, ...]` — for `"default"` plus
each RAW `{group: path}` entry in `load_seat_bindings()`, resolve the
profile and compute readiness via the SAME cache-check logic
`get_readiness` already uses (extracted into a shared helper),
returning one `SeatReadinessV1` per label (duplicates allowed — two
groups pointing at the same profile each get their own entry, honest
to what the operator configured). `ReadinessV1`/`get_readiness`/the
MCP `get_readiness` tool are UNTOUCHED (packaging-surface-free,
zero JSON-shape risk to existing consumers).
accept: no bindings — `get_seat_readiness()` returns `()`;
two bound groups — returns 2 entries with correct per-profile
`qualification_state`.

S6 (R3): `_cmd_status` in `cli/main.py` — when `get_seat_readiness()`
returns non-empty, print an ADDITIONAL "Per-seat readiness" section
(text mode) or add a `"seats"` key to a NEW wrapping JSON object
(`--json` mode); when empty (R6, single-profile homes), output is
BYTE-IDENTICAL to today (no wrapping, no new key) — the branch is
never taken.
accept: single-profile home — `deepreason status`/`--json` output
diffed against a pre-S4 capture, empty diff; two-seat home — output
additionally names both seats' readiness.

S7 (R6): single-profile-home byte-identity, proven directly (not
merely inferred from "no bindings -> untouched branch"): a fixture
captures `deepreason qualify`/`deepreason status` output for a
single-profile home BEFORE this tranche's commits land, re-captures
AFTER, diffs empty.
accept: `diff` empty for both commands' output.

S8 (R8): full gate, 0 failed (net of the already-diagnosed,
independently-reconfirmed-unrelated P3/P1 pre-existing failure from
Rungs S1/S3's PARKED.md entries — reconfirmed fresh for this
tranche's own commit range, not merely re-cited).

S9 (R9): sweep byte-identical, 45 roots, captured before any `src/`
edit and after all of them.

S10 (R10): no S5 (seats in the typed record) work — confirmed by a
grep for any new `RunManifest`/`Config` field in this tranche's diff
(there is none; S1-S6 above are all `qualification.py`/`readiness.py`/
`cli/main.py`/`preparation.py` function bodies, no schema changes).

## Assumptions (operator may override)

A1 (Q1, resolved): "the rung-6/fingerprint gating shape" = lazy,
process-cached-boolean-style gating checked at the point of USE
(`SchoolPopulationRegistry.fingerprint_is_pinned`-on-`get()`, per
`experiments/2026-08-04-change-rung6-plugin-conformance/SPEC.md`
lines 157-165), never eagerly at registration. Applied here: the
qualification-completeness check (S3 above) runs when a seat is about
to be USED for a real run (`prepare()`), never at `deepreason setup
--seat` registration time — `setup` only persists the binding; it
never checks or requires qualification.

A2 (Q2, resolved): "the distinct bound profiles" (R1) = the default/
base profile PLUS every profile named by `load_seat_bindings()`'s raw
group entries, deduplicated by `profile_digest` for EXECUTION
purposes (S1); the default is always included, matching R6's "single
profile home... existing cache" framing (a home with zero `--seat`
flags has exactly one member in this set).

A3 (Q3, resolved): R4's "at selection time" check lives in
`RunPreparationService.prepare` (S3/S4 above) — the existing
single-profile qualification-refusal path's natural, already-proven
location, not a new preflight layer elsewhere.

## Questions for operator (STOP — non-empty)

Q4: **Confirm Option 2's scope** (R1-R3, R5, R6, R8-R10 delivered in
full; R4 delivered as an honest, always-typed, zero-frozen-surface
refusal for ANY heterogeneous 2+-profile run, rather than attempting
successful heterogeneous launch) — OR authorize Option 1 (extending
`project_qualification_report`/`validate_production_contract_qualification`
to per-role provenance, ~400-700 lines, real frozen-surface-5 contact,
likely its own rung) as this rung's actual scope instead. Option 2 is
recommended: it fits "one rung only," needs zero frozen-surface
sign-off, and is a strict subset of what Option 1 would eventually
subsume — nothing built under Option 2 is wasted if Option 1 is
authorized later.

## Out of scope (explicit)

- Successful heterogeneous-seat run LAUNCH/reasoning (Option 1's
  content) — priced above, not built, pending Q4.
- Any `RunManifest`/`Config` schema change (R10; Rung S5's own scope).
- The `experimenter`-template routing gap (S3's own A4) — untouched,
  unrelated to qualification.
- Per-seat token budgets — S2's SM10 already showed this isn't needed.

## Frozen-surface contact forecast

Under Option 2 (recommended): **none** — S1-S9 touch only
`_cmd_qualify`'s loop structure, a new preflight function in
`qualification.py` (using EXISTING digest functions unchanged, S2
above), `readiness.py`, `cli/main.py`'s `_cmd_status`, and
`RunPreparationService.prepare`'s call sequence — no manifest schema,
no validator equality-check change, no new `RunManifest`/`Config`
field. `qualification.py::project_qualification_report`,
`cli/doctor.py::validate_production_contract_qualification`, and all
5 `require_v6_production_qualification` call sites are UNTOUCHED.

Under Option 1: real, deliberate, and priced above — not authorized
without explicit operator words (Q4).

## Blast-radius census

```
$ grep -rn "_cmd_qualify" tests/ docs/map/
docs/map/SUB-manifest.md:164 (names _cmd_qualify collectively with readiness.py/preparation.py/webapp.py, not exact-shape-pinning)
```
MUST NOT MOVE the check's own assertion (`test_qualification_tier.py -k readiness`), re-verified below (S7-equivalent).

```
$ grep -rln "get_readiness" tests/ docs/map/
tests/test_end_user_attachments.py, tests/test_webapp.py, tests/test_qualification_tier.py, tests/test_mcp_help.py, tests/test_mcp.py, tests/test_public_v6_facade.py
```
MUST NOT MOVE — `ReadinessV1`/`get_readiness` untouched (S5's design
keeps them so); `get_seat_readiness` is a new, additive function.

```
$ grep -rln "resolve_completed_qualification" tests/ docs/map/
tests/test_reusable_qualification.py, tests/test_qualification_tier.py, tests/test_public_v6_facade.py, docs/map/SUB-manifest.md
```
MUST NOT MOVE for the single-profile call shape (unchanged, S4's new
branch only fires for 2+ distinct profiles).

```
$ grep -rn "project_qualification_report\|validate_production_contract_qualification" tests/ docs/map/ | wc -l
```
(run fresh in Item S3/S4's own execution step) — EXPECTED: MUST NOT
MOVE under Option 2, since neither function's body changes.

## Budget

Estimated 250-400 lines (Option 2): `qualification.py`
(`require_all_seats_qualified`, ~30-40 lines), `cli/main.py`
(`_cmd_qualify` loop restructuring, ~80-120 lines net given the
extraction), `preparation.py` (S3/S4's new calls, ~20-30 lines),
`readiness.py` (`get_seat_readiness`/`SeatReadinessV1`, ~50-70 lines),
`cli/main.py::_cmd_status` (~20-30 lines), tests (~150-250 lines).
Larger than S3's budget because this rung touches four subsystems
(qualify, status, prepare, readiness) instead of one binding path;
priced up front rather than discovered mid-execution. Frozen surfaces
touched: **none**, conditional on Option 2 — the same "conditional on
the placement/scope decision" shape as Rungs S2 and S3's own
forecasts, not a routine "none expected."

Rubric: 6/6 yes — every R has a spec item or is explicitly the STOP's
subject (R4, split into S3's clean half and the Q4 STOP for the
successful-launch half); blast-radius census pasted, every hit
classified; frozen-surface contact forecast recorded (none, under
Option 2, real under Option 1 — both priced); every mechanism the
request names (`--seat`, "rung-6/fingerprint gating shape", SM7, SM9)
traced to actual code/prior tranches, not assumed; this is an EXECUTE
request but a genuine STOP was found mid-spec — handled per
dr-spec-change's own mandatory rule (commit and present, not silently
picking a side); nothing above is untraceable to an R/C number.
