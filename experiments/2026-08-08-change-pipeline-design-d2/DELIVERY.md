# Delivered: dual-mode conjecture — Rung D2 (design, then operator-authorized implementation, then Amendment 4's mechanical prose-required correction)

Branch: `claude/pipeline-design-d2` @ `56a6d7d7` (pushed, tree clean;
`git status --porcelain` empty; local HEAD == `origin/claude/pipeline-design-d2` HEAD)

## What changed

D2 started as a SPEC-ONLY design rung and grew, across four operator
amendments, into a shipped implementation. The delivered design is: a
conjecture stays ONE artifact whose content is always explanatory
prose (never full code) — the operator's own correction (Amendment 1)
replaced the original twin-artifact design seed entirely. On top of
that prose, a conjecturer may optionally attach an executable
**code-commitment** (`checker_spec`/`checker_specs`) on either
candidate contract (skeleton and the live reasoning path). A failing
code-commitment refutes the conjecture it lives on demonstratively,
the same way any other commitment failure does — there is no
faithfulness referee anywhere in the design; a defeated relatedness
challenge can strip a commitment's protection without touching the
conjecture's own accepted status. A new `"encoder"` seat role lets the
coder seat author that commitment code for already-admitted prose,
leaving `property_designer` untouched.

Amendment 4, raised by the operator after the tranche's first PASS,
found and closed one real gap: nothing previously stopped a
conjecture's prose fields from being bare code with zero explanation.
The fix (`src/deepreason/programs.py::is_pure_code`, an AST-based
mechanical test) is wired into the two commitment programs that were
already mandatory well-formedness checks — `reasoning_wf_program`
(unconditional on the live path) and `skeleton_wf_program` (the
pre-existing opt-in path) — so a pure-code submission is refuted the
same way any other commitment failure is, with no new admission gate
and no content-quality referee.

Code: `src/deepreason/rules/encoding.py`, `rules/relatedness.py`,
`programs.py` (`candidate_checker` dispatch, `is_pure_code`),
`ontology/skeleton.py`-adjacent `ForbiddenCase.checker_spec`,
`ontology/reasoning.py`-adjacent `Countercondition.checker_spec` /
`ReasoningCandidateProposal.checker_specs`, `rules/warrants.py`
(`formally_backed`'s relatedness-gated exclusion),
`workloads/text.py::reasoning_wf_program`,
`informal/skeleton.py::skeleton_wf_program`, one scoped
`run_manifest.py` contract-version registration (operator-granted,
Amendment 3). Tests: 16 files touched/added (1031 insertions), full
gate 3415 passed. Map: 8 `docs/map/` documents updated in the same
commits as the behavior they describe, 6 new `check:` lines added, 0
created.

## Reconciliation

Original scope (R1–R18) and Amendment 1 (R19–R40) below; Amendment 2
(R41–R48), Amendment 3 (R49–R52), and Amendment 4 (R53–R58) follow.
"Historical" proof = a documented fact about how this tranche ran its
own process, not a runtime behavior check.

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "No code, no checklist, no execution this window" | superseded | Amendment 3 (R49-52) explicitly re-opened execution in this same tranche |
| R2 | setup/preflight on the named base commit | done | historical, session start |
| R3 | route capture→spec→STOP | done | commits `258718ab`, `7e8995d4`; superseded onward by amendments |
| R4 | authority = PREPLAN R-a..R-g + census | done | SPEC.md cites D1's M-numbers throughout |
| R5 | R-g gate on every design decision | done | SPEC.md rev 2 Items 1,2,5,6 each carry an explicit R-g argument |
| R6 | D1 census as measurement base | done | SPEC.md M1-M20 cited/derived |
| R7 | twin-artifact shape decision | superseded | Amendment 1 rejects it; kept marked-superseded in SPEC.md per house convention (R31) |
| R8 | optional formal channel, absence byte-identical | done | `test_R_g_informal_only_run_replays_byte_identical`; VALIDATION.md Item 2 |
| R9 | verifiable kind signal | done | unchanged design — zero `ontology/artifact.py` diff |
| R10 | kind-matched criticism forms | done | unchanged design — zero `llm/packs.py` diff |
| R11 | coder-seat delegation as encoder | done-with-assumption A1 | superseded in shape by R38; `rules/encoding.py`, `test_encoding.py`, commit `1055c584` |
| R12 | R-g acceptance checks D3 must pass | done | 7 named claims, commit `f0f526f2`, VALIDATION.md Item 6 |
| R13 | frozen-surface forecast named | done | SPEC.md rev 1 & 2 both carry full 5-surface forecasts |
| R14 | operator decision sheet in SPEC.md | done | present in both revisions |
| R15 | budget headline = computed sum | done | rev 2: "1150" itemized; actual 824 lines delivered |
| R16 | commit/push REQUEST+SPEC, STOP | done | historical |
| R17 | anything broken: PARKED, never fixed | done | PARKED.md P-D2-1/2/3, none touched in-tree |
| R18 | read CLAUDE.md/skills first | done | historical, session start |
| R19 | re-anchor R-g: guarded direction is prose only | done | SPEC.md rev 2 Item 6, "corrected, one-directional guardrail" |
| R20 | conjecture artifacts can never be full code (original half) | done | Item 1 rev 2's prose-required design; fully closed by Amendment 4 below (R54) |
| R21 | code not explanatory, prose is | done | same design; commitment code lives in `budget.extra`, never as artifact content |
| R22 | neither prose nor code critiqued directly, only commitments | done | `crit_program` runs the commitment, never inspects artifact text |
| R23 | commitments get criticized | done | Item 2 design + tests, commit `59496d8f` |
| R24 | code as commitment, if related & sole criticizable surface | done | Item 2 + Item 5 together |
| R25/R26 | referee irrelevant; redesign if one is needed | done | `relatedness_trial` reuses existing judge-ensemble shape, no new referee |
| R27 | all code criticizable through commitment attack surface | done | `checker_spec`/`checker_specs` IS the commitment; no other code surface |
| R28 | F2 Road B: formal channel on both candidate contracts | done | `ForbiddenCase.checker_spec` + `Countercondition.checker_spec`/`ReasoningCandidateProposal.checker_specs`, commits `f0c741d7`, `5560aa2e` |
| R29 | F3 Road A: new encoder role, property_designer untouched | done | `seat_bindings.py` diff shows byte-unchanged `property_designer`, `"encoder"` added alongside |
| R30 | F4 moot, forecast re-derived assuming no grant | done | surfaces 2/3 needed zero contact (`harness.py`/`invariants.py` byte-identical) |
| R31 | SPEC rev 2 supersedes rev 1 in place, reasoning kept | done | SPEC.md structure, commit `af4d17ce` |
| R32 | one artifact, prose required, enforcement measured | done | M22 finding; fully closed by Amendment 4 (R54) |
| R33 | optional code-commitment channel on both contracts | done | see R28 |
| R34 | commitments sole attack surface; formally_backed = incentive | done | protection-semantics section + tests, commit `c66eb78d` |
| R35 | relatedness without referee, reuse relevance_trial | done | `relatedness_trial` docstring/shape, commits `56154daf`, `0c877b10` |
| R36 | R-g re-derived incl. _standing_recrit_pool decision | done | Item 6 "STAYS AS-IS" re-confirmation; `test_R_g_no_scheduling_term_reads_the_candidate_checker_kind` |
| R37 | test implications specified plainly | done-with-assumption | VALIDATION.md notes one stale cross-reference in SPEC's own "Test implications" prose (never propagated after Item 2's redesign) — surfaced plainly, not silently carried; the actual test files added match the real design |
| R38 | encoder authors commitment code for admitted prose | done | `draft_encoded_commitment` docstring + no-op fallback, `test_encoding.py` |
| R39 | re-run decision sheet, forks priced | done | rev 2's decision sheet, F5-F7 resolved by Amendment 2 |
| R40 | commit/push SPEC rev 2, STOP | done | historical |
| R41 | F5 Road B: reuse oracle.py's compile engine | done | `run_from_full_spec` reuses `run()`/`_compile` unchanged |
| R42 | F6 Road B: relatedness purely reactive | done | zero callers of `relatedness_trial` anywhere in `src/` |
| R43 | prose-immunity minus relatedness; sustained challenge strips shield | done | `test_a_challenged_relatedness_claim_strips_only_its_own_commitment` |
| R44 | kind's checks mechanically re-executed every cycle | done | `crit_program` confirmed unchanged |
| R45 | execution-supremacy earned by attack surface, not shield | done | `EXEC_PROGRAMS` confirmed still exactly 3 members |
| R46 | SPEC update encoding the three couplings, measured | done | SPEC.md rev 2 "Protection semantics (CORRECTED by Amendment 2)" |
| R47 | plan-steps per the stated discipline | done | CHECKLIST.md's 31 steps, diff-budget at every [COMMIT], step 28's digest measurement |
| R48 | commit/push spec+checklist, STOP for review | done | historical |
| R49 | begin execute-step from 1, one step per invocation | done | 24 commits, one/few steps each, per established convention |
| R50 | surface-4 grant, scoped to step 27 only | done | frozen-surface diff = exactly the one authorized `run_manifest.py` hunk |
| R51 | step 27 done-when satisfied; step 28 digest evidence mandatory | done | CHECKLIST.md step 28's pre/post digest comparison, byte-identical |
| R52 | continue through 31, validate, STOP before delivery | done | commit `3dfbe36c`; honored until this message's explicit authorization |
| R53 | verify Amendment 4's four claims before moving on | done | independent verification, ledgered in REQUEST.md's C13 |
| R54 | pure code shouldn't be available at all | done | `is_pure_code` wired into both mandatory wf programs, commits `69cb6c26`, `d9085106`, `fd2ee0fb` |
| R55 | code in explanation uncriticizable; code in commitments can be | done | already true pre-amendment (C13); no code change needed |
| R56 | code commitments must refute their own carrying artifact | done | already true pre-amendment (C13); no code change needed |
| R57 | prose+code need not commit the code; attack-edge addable | done-with-assumption A6 | (a) half already true; (b) half's existing narrower mechanism confirmed unchanged, not widened |
| R58 | operator's chosen enforcement shape (mechanical commitment, not admission gate) | done | `is_pure_code` refuted via existing `crit_program` path; rejected alternative (admission-time gate) never built |

## Assumptions the operator may override

A1: coder-seat delegation adds a new `"encoder"` role rather than
reusing/retiring `property_designer`.
A2: SPEC.md rev 1 named the acceptance checks; Amendment 3 then had
them written as code in this same tranche.
A3: budget itemization is by decision item, summing to the stated
headline (held for both revisions).
A4: M15-M20 were the load-bearing re-measurements; D1's M1-M14 cited
without re-running.
A5: the STOP after SPEC.md rev 1 was the frozen-surface-contact STOP
the spec template itself requires.
A6: `is_pure_code`'s scope is deliberately narrow — only
function/class/import-only submissions trip it; bare assignment
sequences do not.

## Map delta

changed: `docs/map/CON-conjecture-kinds.md`, `CON-seats.md`,
`SEAM-adjudication-x-rules.md`, `SEAM-evaluation-x-ontology.md`,
`SEAM-evaluation-x-rules.md`, `SEAM-llm-x-rules.md`,
`SEAM-ontology-x-rules.md`, `SEAM-rules-x-workflow.md` (8 files, 208
insertions / 41 deletions)
created: none
new checks: 6 (`CON-conjecture-kinds.md`'s new dual-mode section, 5
checks; plus 1 combined check added for Amendment 4's pure-code test)

left stale (advisory, `docs_verify --stale`, all 31 entries classified
in VALIDATION.md, none silent):
- 11 documents: pre-existing staleness entirely predating D2 —
  dismissed, backlog from earlier tranches, every check still passes.
- 8 documents: staleness mixed with D2 as a contributing but not sole
  cause — dismissed, D2's one `run_manifest.py` hunk touches nothing
  these documents claim.
- 8 documents: D2 is the sole cause but the `Verified-at:` stamp was
  never advanced — a bookkeeping gap, not a false claim (every check
  in each already passes); left for a future touch to re-stamp.
- 1 document (`CON-warrants-and-attacks.md`): a genuine minor prose
  gap — its exhaustive-looking list of exclusion paths doesn't
  mention the new third path (a defeated relatedness challenge); not
  a false claim, and the new nuance is documented in the more specific
  home (`CON-conjecture-kinds.md`) per file-ownership discipline.
- 2 documents: edited but with no additional owned-file staleness —
  no action needed.

## Parked (not done, not promised)

**P-D2-1** — `tests/test_continuation.py::test_a_stop_with_no_typed_receipt_refuses_continuation`
fails on a pre-existing continuation/recovery-reason typing defect,
confirmed byte-identical on a fresh worktree at this tranche's own
base commit. Ready-to-send prompt: "Diagnose and fix
`test_continuation.py`'s `test_a_stop_with_no_typed_receipt_refuses_continuation`
— a committed root stopped on `operational_failure` is being refused
with `CONTINUE_RESUME_RECOVERY_MISMATCH` instead of the expected
`CONTINUE_TYPED_STOP_REQUIRED`; also fixes `SUB-application.md:208`/`:239`'s
matching map-check failures."

**P-D2-2** — `tests/test_module_fingerprints.py::test_absence_is_valid_before_the_feature_and_presence_valid_after`
fails with `ValueError: too many values to unpack` on
`recorded_module_fingerprints`, confirmed pre-existing. Ready-to-send
prompt: "Diagnose and fix `test_module_fingerprints.py`'s double-stamp
defect — `recorded_module_fingerprints` returns more than one value for
some stamped committed roots, breaking the test's single-value unpack."

**P-D2-3** — `tests/test_bronze_report.py::test_census_totals_internally_consistent`
fails with a `gate_blocked` (159) vs `gate_measures` (165) mismatch
over the retained bronze-flat historical roots, confirmed pre-existing
and unrelated to any code this tranche touched. Ready-to-send prompt:
"Reconcile `scripts/bronze_census.py`'s `gate_blocked`/`gate_measures`
counts for `experiments/bronze_flat_2026-07-13/` — the census fixture
reports 159 blocked but 165 gate Measures, so some gate Measure isn't
landing on exactly one counted row."

recommended next: P-D2-1 — it also fails two live `docs_verify.py`
checks (`SUB-application.md:208`/`:239`), so fixing it clears both a
test and a documentation-accuracy gap in one tranche.
