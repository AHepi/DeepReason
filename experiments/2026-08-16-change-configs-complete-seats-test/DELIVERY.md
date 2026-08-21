# Delivered: the all-configurations law is complete, and the seats/evidence law now has a test that can go red

Branch: `claude/configs-complete-seats-test-7wg7fu`
Base: `5f648ebc9` (`origin/main` at session start)
Tranche: `experiments/2026-08-16-change-configs-complete-seats-test/`

## What changed

**Part A.** Every compile-time denial the 2026-08-12 tranche self-parked is
now a typed disclosure. 21 sites: the v4 school topology (5 codes), the v4
criticism topology (8 codes), the v5/v6 capability-profile mismatch (2), both
preflight functions (4), the scratch embedder fallback and the reserved
attention fractions (2), the intake cycles ceiling (1), and the two v6
route-seat plan passes (1, plus one new code for a site that had no typed
refusal to preserve). A configuration that parses now compiles; the retired
refusal survives as a `CompileNoticeV1` carrying its old code, message and
pointer, plus a `resolution` string wherever two parts of one configuration
contradicted each other and one had to be dropped.

Six conflicts resolve deterministically instead of refusing (SPEC §4, each
with a test asserting both the winner and the `resolution`). One deliberately
does NOT resolve — `V4_CRITICISM_FOREIGN_COVERAGE_IMPOSSIBLE`, whose field is
`ge=1` and therefore cannot be clamped to zero without inventing an intent —
and the test pins `resolution is None` so the absence is deliberate rather
than accidental.

Six families still refuse, and are pinned from the other side: shape/parse
errors, dangling references, frozen-record protections, not-yet-implemented
capabilities, version-completeness checks, and every runtime/dispatch
resolver.

**Part B.** `tests/test_seats_evidence_law.py` — 11 adversarial cases, no
pytest marks, in the ordinary gate. Each takes a configuration Part A now
admits, compiles it, and shows the seats/evidence law still holds at the
point of use. Every assertion reads a typed record object; none reads model
output. The mutation proof is in VALIDATION.md: guard 1 was disabled, the
file went RED with `DID NOT RAISE WellFormednessError`, the mutation was
reverted and verified byte-identical, and the file went GREEN.

## Two findings the census produced, both fixed here rather than parked

**The park's own prediction was wrong, and the truth was worse.** The parked
note (P2) said a grounded-bridge v6 configuration missing its stage routes
would hit a typed `V6_BEHAVIORAL_CONTRACT_ROUTE_REQUIRED`. It did not. On the
tranche base it died with a bare `IndexError` inside
`_compile_route_seat_contract_decomposition_plan` — neither a compile (which
the law requires) nor a typed refusal (which CLAUDE.md requires), and nothing
the record could carry. It was caused by the DELIVERING tranche's own
conversion: removing `BRIDGE_*_ROUTE_REQUIRED` let compilation walk past the
missing route into an unguarded index. Both plan passes now skip the unbound
grant and disclose it; the dispatch resolvers still refuse typed, because a
skipped grant is simply absent from the plan.

**Converting the criticism cluster newly exposed an untyped runtime crash.**
`scheduler.py:1320` raised a bare `RuntimeError` when a manifest declares
foreign criticism but the run has no critic seat. That line was unreachable
while the shape could not compile. It is now
`SchoolRouteResolutionError("SCHOOL_ROUTE_CRITIC_ROLE_MISSING", ...)` — still
a `RuntimeError` subclass, so every existing catcher still catches it. The
law itself demands this: an unsatisfiable ensemble "still fails typed at the
point of use".

## The precondition the delivering tranche refused to proceed without

It declined to convert the v4 school/criticism cluster until someone verified
the downstream fails TYPED rather than crashing. Discharged in SPEC §2 by
reading the dispatch code: `llm/firewall.py`'s nine
`SchoolRouteResolutionError` codes; `informal/trial.py`'s typed
`_block`/`_decline` on a missing critic, defender or judge role;
`require_cross_family_judge_ensemble`'s `JudgeEnsemblePolicyError` from the
immutable leases; `workflow/criticism.py`'s
`V4_CRITICISM_FOREIGN_COVERAGE_UNSATISFIED`; and — the one Part B leans on
hardest — `harness.py::_validate_warrant`'s frozen rule that a rubric-derived
warrant without a conforming trial transcript is refused outright.

## Reconciliation, requirement by requirement

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | convert the ~20 remaining denial sites | done — 21 | `CENSUS.md`; `census-before.txt` vs `census-after.txt` |
| R2 | re-derive fresh, pasted proof per site, `already-done` where converted | done | `census_probe.py` (committed); A22 rowed `already-done`, A21 re-classified from "typed refusal" to "untyped crash" |
| R3 | same `CompileNoticeV1` pattern, recorded alongside the result | done | no new mechanism; `_emit_deduped` widened by one optional keyword |
| R4 | deterministic resolution in SPEC.md, never a refusal | done | SPEC §4; VALIDATION's R4 table, six rules + one deliberate non-resolution |
| R5 | parse/shape errors stay refused | done | `test_dangling_school_references_still_refuse`, `test_unimplemented_capabilities_still_refuse`, `test_reserved_attention_limits_are_bounded`, `..._still_exits_nonzero_for_a_shape_error` |
| R6 | runtime unchanged | done, with one disclosure | no dispatch resolver weakened; `scheduler.py:1320` given a TYPE (argued in SPEC §2) |
| R7 | pinned tests enumerated in SPEC before touching any | done, **with a recorded method gap** | SPEC §5 table (T1–T7) + addendum (T8–T11): the code-grep missed substring/prose matches, and three of the four cost a full gate |
| R8 | census artifact, Part B's input | done | `CENSUS.md`, with the shape column and Part B's ✔ mapping |
| R9 | Part B only after Part A's gate is green | done | Part A committed at `bce018ae5` with 3726 passed / 0 failed before the Part B file existed |
| R10 | one new file, docstring names the law verbatim + tranche | done | `tests/test_seats_evidence_law.py` |
| R11 | attack list = census shapes + audit L2 shapes | done | 11 cases; B14/B15 cover `goal-L2.txt`'s two seat-binding levers |
| R12 | compile it, then prove the law at the point of use | done | every case asserts a successful compile + notice BEFORE attacking |
| R13 | assert the mechanism, never the prose | done | typed record objects only; no assertion reads generated text |
| R14 | mutation proof — watch it go red | done | CHECKLIST S11: diff, RED, byte-identical restore, GREEN, all pasted |
| R15 | joins the ordinary gate, no special marks | done | part of the 3737 |
| R16 | a real violation is a finding, xfail + park | **did not fire** | 0 `xfail`; PARKED.md says so explicitly |
| R17 | pre-granted surface 4 only | respected | `harness.py` byte-identical; `capabilities/state.py` untouched |
| R18 | if IntakeFormV1's schema moves, all four pins + FORM_DR1 | **not triggered** | schema sha identical before/after (`eaf1f49c…`, `6eec6554…`); `wheel_smoke.py` exit 0 confirms independently |
| R19 | cross-version replay proofs retired | respected | not attempted |
| R20 | report the qualification-digest cost, don't stop | done | **net cost zero** — see below |
| R21 | ring while iterating, full gate at the boundary | done | 3737 passed / 0 failed; `docs_verify` 3 baseline failures |
| R22 | map moves in the same commits | done | Part A: `SUB-manifest`, `CON-schools`, `CON-criticism-source`, `SEAM-manifest-x-schools`. Part B: `CON-seats`, `SUB-manifest`'s check extended |
| R23 | errata for any document claiming completion | done | `docs/ERRATA.md` **E33** |
| R24 | commit and push every phase boundary | done | four pushes |
| R25 | R-by-R with pasted proof; the two closing counts | this table; counts below | |
| R26 | no stops | respected | the one operator-only decision was re-parked, not blocked on |

## Qualification-digest cost (R20): zero

`compile_notices` is popped from both serializations when `schema_version < 6
or not compile_notices`, so any configuration that triggers no notice is
byte-identical to before and its subject digest does not move. A configuration
that DOES trigger a notice gets a different digest — but every such
configuration was previously REFUSED outright, so it has no cached
qualification to invalidate. Nothing needs requalifying.
`test_notice_free_compiles_record_nothing` pins the byte contract.

## What this tranche did NOT do

Four parked items, each with a ready-to-paste prompt in `PARKED.md`. The one
worth the operator's eye is **P1**: the v6 launch kill switch
(`V6_LAUNCH_DISABLED`) still refuses. Two tranches have now declined to
convert it on their own authority, for the same reason — an emergency valve
that no longer stops anything is not "compile-time denial abolished", it is
the removal of an operational safety valve, and it is not one of the denial
categories the operator's own law names. It needs one sentence from the
operator, not more implementation.

**P4** is the honest residue of Part A: preflight-time notices reach stderr
but not the typed run record, because the manifest is already frozen when
preflight runs. Under this repo's own epistemology, a disclosure that exists
only on stderr is not evidence about the run. This tranche made them visible;
it did not make them evidence.

## The wheel smokes

`python scripts/wheel_smoke.py` — **exit 0**. This is the one that pins what
this tranche could plausibly have moved: console entry points, the MCP tool
set and its exact schema shas, wheel layout. It passing is the independent
confirmation that `IntakeFormV1`'s schema did not move.

`python -u scripts/wheel_operational_smoke.py` — **exit 1, at the parked
defect**. Same assertion (`terminal verification is incomplete`), same line
(`_assert_resumable_terminal`, `:2061`), same `"stage":"reason"`, same
envelope fields as `experiments/2026-08-16-change-embedder-auto-install/PARKED.md`
P1, which proved it pre-existing on a clean worktree at `d52c739ff`. Full
reasoning in VALIDATION.md; short version: the assertion needs terminal
verification state from a completed run, and nothing here touches
terminalization, `verify_root`, or the stop policy.

## Close

**Notices vs sites:** 21 of 21 remaining denial sites now emit a typed
disclosure or resolve deterministically, out of 21 that still refused or
crashed on the tranche base — leaving 1 site (`V6_LAUNCH_DISABLED`) refusing
by recorded decision pending the operator's answer, and 1 (`_preflight_text_authority`)
already converted by an intervening tranche.

**Attack cases the law's test holds against:** 11 of 11, with zero `xfail`
and zero real violations found — and the file has been seen RED, so the
number means something.
