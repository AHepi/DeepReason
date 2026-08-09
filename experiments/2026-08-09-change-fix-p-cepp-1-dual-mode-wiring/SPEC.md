# Spec for: fix dual seat wiring and test with a short live run
Traces: every item cites R/C numbers. Untraceable items are bugs.

## Map preflight (recorded, per REQUEST.md's own note)

- `DR-INV-frozen-surfaces` — read in full this phase. Surface 3
  (replay-validation formats, `invariants.py`), surface 4 (manifest
  schemas AND validators, `run_manifest.py`), surface 5 (qualification
  subject digests, `qualification.py`/`cli/doctor.py`'s pair inventory)
  are ALL plausibly in contact — see census below. Only surface 4 has
  the operator's approval on record (REQUEST.md C1); surfaces 3 and 5
  do not yet.
- `DR-SEAM-llm-x-manifest` — read in full previously (CP1M tranche);
  re-consulted here. Its own "How to change it" step 1 predicts exactly
  what was found: "A new route/contract field... moves every
  behavioural and decomposition grant that stores one... a cache miss
  costing the whole [qualification] battery."

## The material contradiction (found before any Item below could be written)

R1 quotes `PARKED.md`'s ready-to-send prompt verbatim: fix
`_compile_contract_schema_repair_policy` in `run_manifest.py`. Per
`dr-spec-change`'s own procedure ("a mechanism the request NAMES... is a
suggestion, not a requirement... verify it actually reaches the code
this change touches... If it cannot, that is a material contradiction"),
I traced whether that ONE fix actually gets a v7-configured manifest to
"validate and dispatch a `program:candidate_checker` eval-kind
commitment" (R1's own success condition, also quoted from the
operator's authority chain). It does not. Tracing the full call path
from "manifest requests v7" to "conjecturer turn actually mints under
v7" found **23 hardcoded `"conjecturer.turn.v6"` literals across 8
files**, not the 1 file `PARKED.md` named:

| File | Hits | What breaks for v7 without a fix here |
|---|---|---|
| `run_manifest.py` | 5 (lines 658-659, 2005, 2020, 2491) | the repair-grant gap R1 names (2491); ALSO: `is_conjecture` (2005) and `scratch_write` (2020) checks only recognize v6, so v7 turns lose scratch (imaginative-workshop) read/write authority even once the repair grant is fixed |
| `rules/conj.py` | 5 (lines 736, 946, 1018, 1874, 2215) | `expected_contract` (736) HARD-REJECTS any schema_version=6 manifest whose `conjecturer_turn_contract != "conjecturer.turn.v6"` with `ValueError("controlled conjecture turns require their exact active manifest contract")` — this fires BEFORE any turn is minted, independent of the repair-grant fix; `effective_contract` (2215) then hardcodes the MINTED commitment's own contract id to `"conjecturer.turn.v6"` regardless of what the manifest configured, so even a turn that got past line 736 would still mint a v6-labeled commitment, never exposing v7's vocabulary |
| `workflow/profiles.py` | 4 (lines 78, 112, 157, 182) | `WorkflowControlProfileV1.conjecturer_contract_id`'s own `Literal` type (line 74-79) **does not include `"conjecturer.turn.v7"` at all** — a v7 value fails Pydantic validation outright, and line 246 constructs this profile directly from the manifest's configured value, so this fires on every v7-configured run regardless of anything else |
| `invariants.py` | 2 (lines 1192, 2987) | **replay validation** (frozen surface 3): two membership checks (`{"conjecturer.turn.v4", "v5", "v6"}`) reject v7 as an unauthorized contract when re-deriving state from a committed root's log — a v7 root would FAIL `verify_root` even if everything upstream worked |
| `cli/doctor.py` | 2 (lines 62, 794) | `ProductionContractPairV1.contract_id`'s `Literal` (qualification battery's pair inventory, frozen surface 5) does not include v7; the qualification-subject digest is built from this inventory |
| `capabilities/simulation.py`, `capabilities/research.py` | 4 (2 each) | capability-proposal admission gates reject any preparation whose `contract_id != "conjecturer.turn.v6"` — affects the simulation/research capability channels specifically, NOT candidate_checker directly, but a v7-authored conjecture could not admit a simulation/research proposal either |
| `workflow/conjecture_recovery.py` | 2 (lines 166, 428) | resume/recovery after a crash mid-turn hardcodes v6; a v7 turn interrupted mid-flight could not resume |
| `llm/wire.py` | 1 (line 81) | a named constant, `CONJECTURER_TURN_CONTRACT_V6` — used elsewhere as a literal reference, lower risk on its own but marks the pattern repeats even in shared constants |

**Separately, and independent of all of the above**: CP1M's `PARKED.md`
entry already noted `rules/encoding.py::draft_encoded_commitment` (the
function that would delegate checker-authoring to a literal "encoder"
role/seat) has ZERO callers anywhere in `src/` — re-confirmed on this
tree, unchanged. Its own docstring clarifies why this is LESS blocking
than it sounds: it is a FALLBACK ("the caller's own Item 2 inline
mechanism — the conjecturer embeds `checker_spec` itself — is untouched,
a no-op from here"). The PRIMARY dispatch path does not need the encoder
role to fire at all: a `conjecturer.turn.v7` output can carry a
`checker_spec` inline (the same field shape `ForbiddenCase`/
`Countercondition` already use, per D2's own design). So R1's phrase
"through the encoder seat" is satisfiable via the INLINE mechanism
without needing to also fix the separate dead-code gap — but this
softens the encoder-specific wording, it does not shrink the 23-site
census above.

## Items (Option C, operator-confirmed scope)

S1 (R1, C1): `run_manifest.py`, 5 sites.
- `_compile_contract_schema_repair_policy` (~line 2491): before — the
  `ceilings` dict key is the literal `"conjecturer.turn.v6"`; a
  v7-configured manifest's `assignments` (built dynamically in
  `_route_seat_behavioral_contract_assignments`, already reads
  `contracts.conjecturer_turn_contract` correctly) contains
  `"conjecturer.turn.v7"`, which has no matching grant. After — the key
  is `control_plane_policy.contract_versions.conjecturer_turn_contract`
  (whatever the manifest actually configured), so v6 and v7 both get an
  identical `conjecture_ceiling` grant.
- `_compile_route_seat_behavioral_capability_plan`'s `is_conjecture` set
  (~line 2004-2007) and `scratch_write` check (~line 2020): before —
  both hardcode `"conjecturer.turn.v6"` only. After — both recognize
  `"conjecturer.turn.v7"` as an equal member (a small shared
  membership set, not two independently-maintained literals).
  accept: `python -m pytest tests/test_v6_contract_schema_repair_policy.py tests/test_v6_contract_schema_repair_runtime.py tests/test_v6_route_seat_behavioral_capability_plan.py tests/test_v6_route_seat_behavioral_capability_runtime.py -q` (all four verified to exist) stays green
  AND a new regression test constructs a v7-configured
  `ControlPlanePolicyV3`, compiles a full v6-schema manifest, and
  asserts: the compiled `contract_schema_repair_policy` has a
  `"conjecturer.turn.v7"` grant with `maximum_schema_repairs ==` the
  same value a v6-configured manifest gets; `_compile_route_seat_behavioral_capability_plan`'s
  output for that seat has `scratch_read="advisory"` and
  `scratch_write="contract_governed"`, matching the v6 case exactly.

S2 (R1): `rules/conj.py`, 5 sites (all under the SAME function/module,
grouped as one item since they must move together or the module is left
internally inconsistent).
- `expected_contract` dict (~line 730-742): before — schema_version 6
  hardcodes the literal `"conjecturer.turn.v6"` as the ONLY accepted
  value, raising `ValueError` otherwise. After — for schema_version 6,
  the accepted value is whichever of `{"conjecturer.turn.v6",
  "conjecturer.turn.v7"}` the manifest's own `RunManifest`-validated
  `Literal` field carries (the manifest's own Pydantic validation
  already restricts it to exactly these two; this check need only
  confirm schema_version 6 implies an ACTIVE-mode manifest, not
  re-pin the literal value). v4/v5 branches unchanged.
- `effective_contract` (~line 2210-2218): before — hardcodes
  `"conjecturer.turn.v6"` whenever `active_v6` and not
  `atomic_fallback_completed`, regardless of what the manifest
  configured. After — uses the manifest's configured
  `conjecturer_turn_contract` value in that branch (captured once,
  where `control`/`active_v6` are already set, into a new local
  variable) instead of a hardcoded literal; the
  `"conjecturer.atomic-candidate.v1"` fallback branch is UNCHANGED
  (atomic decomposition always uses its own dedicated contract,
  independent of v6/v7 — confirmed by S1's own `is_conjecture` set,
  which already lists `conjecturer.atomic-candidate.v1` as a SEPARATE
  member, not derived from the turn contract).
- Lines 946, 1018, 1874 (atomic-decomposition source-contract
  bookkeeping): before — all three hardcode `"conjecturer.turn.v6"` as
  the SOURCE contract id when preparing, matching, or resolving an
  atomic-decomposition transition. After — all three use the same
  captured configured-contract local variable as `effective_contract`'s
  fix, so a v7 turn's decomposition bookkeeping stays internally
  consistent with its own contract id rather than silently mislabeling
  itself as v6.
  accept: `python -m pytest tests/test_v6_conjecture_component_atomicity.py tests/test_v6_conjecture_scratch_consumption.py tests/test_v6_context_continuation.py tests/test_v6_controller3_replay_verification.py tests/test_v6_engaged_public_defaults.py tests/test_v6_engaged_repair_verification.py tests/test_v6_transaction_qualification.py -q`
  (all verified to exist and import `rules.conj`) stays green AND a new
  regression test drives a v7-configured manifest's conjecture turn
  through `Conj(...)` (the narrowest existing v6-exercising test's
  fixture, adapted) and asserts the resulting admitted commitment's
  contract id is `"conjecturer.turn.v7"`, not `"conjecturer.turn.v6"`.

S3 (R1, C1 — same class of frozen-surface concern as C1, not literally
named): `workflow/profiles.py`, 4 sites.
- `WorkflowControlProfileV1.conjecturer_contract_id`'s `Literal` type
  (~line 74-79): before — `Literal["conjecturer.legacy.v1",
  "conjecturer.turn.v4", "conjecturer.turn.v5", "conjecturer.turn.v6"]`;
  a v7 value raises `pydantic.ValidationError` outright. After — the
  Literal additionally admits `"conjecturer.turn.v7"`. This is the SAME
  additive-Literal pattern `run_manifest.py`'s own
  `ContractVersionPolicyV3.conjecturer_turn_contract` already uses
  (line 658) — the exact precedent this fix mirrors, not a new pattern.
- The two membership-set checks (~line 109-113, ~154-158) gating
  `CONTEXT_REQUEST`/`ABSTENTION` outcomes and the "active conjecture
  profile requires a controlled turn contract" validator: before — both
  check membership in `{"conjecturer.turn.v4", "v5", "v6"}` literally.
  After — both include `"conjecturer.turn.v7"`.
  accept: `python -m pytest tests/test_workflow_reducer_c0.py tests/test_workflow_control_replay_c1.py -q` (both verified to exist, both cited in the blast-radius census) stays green AND a new regression
  test constructs `WorkflowControlProfileV1(conjecturer_contract_id="conjecturer.turn.v7", ...)`
  with `workflow_profile="inquiry.active.v2"` and confirms it validates
  (no `ValidationError`) and its `available_capability_outcomes()`
  (or equivalent) includes `CONTEXT_REQUEST`/`ABSTENTION` exactly as a
  v6-configured profile would.

S4 (R1, frozen surface 3 — operator-approved via the Option C choice):
`invariants.py`, 2 sites.
- Lines ~1192 and ~2987: before — both membership checks are
  `{"conjecturer.turn.v4", "conjecturer.turn.v5", "conjecturer.turn.v6"}`
  literally; replaying a v7-authored root's log would `fail("conjecture-turn",
  "manifest does not authorize v4 conjecture turns")` even though the
  manifest legitimately authorized v7. After — both sets additionally
  admit `"conjecturer.turn.v7"`.
  accept: `python -m pytest tests/test_scratch_provenance_refs.py tests/test_v6_transaction_qualification.py tests/test_chaos_invariants.py tests/test_invariant_call_outcomes.py tests/test_persistence_invariants.py tests/test_replay.py tests/test_replay_code.py tests/test_replay_formal.py tests/test_replay_reasoning.py -q`
  (all nine verified to exist; the first two are the only files
  currently asserting on the `"conjecture-turn"` fail reason this item
  touches) stays green (existing v4/v5/v6 root replay assertions MUST
  NOT MOVE — blast-radius census) AND a new regression test builds a
  minimal
  v7-configured root (fixture, no live call), runs `verify_root`, and
  asserts no `"conjecture-turn"` violation is raised for the v7 contract
  specifically (mirroring whatever existing fixture proves the same for
  v6, adapted).

## Assumptions (operator may override)

A1 (Q1, REQUEST.md): reuse CP1M's existing verified operator keys
(`experiments/2026-08-09-cp1m-stratification-retrodiction/env`) for the
live-run test rather than requesting new ones — assumed, operator may
override.

A2 (Q2, REQUEST.md): the v7 repair grant mirrors v6's exactly (same
`conjecture_ceiling` value, same `maximum_provider_calls` arithmetic) —
the smallest reasonable reading of "a real `ContractSchemaRepairGrantV1`"
given D2's own framing of v7 as additive-not-different — assumed,
operator may override.

A3 (Q3, REQUEST.md): "test with a short live run" is read as satisfied
by confirming a `program:candidate_checker` commitment actually gets
minted, compiles, and executes through the live path (the INLINE
mechanism, A1 above) — not a full run to a CONFIRMED/REFUTED verdict on
a specific claim. A single cycle reaching that dispatch is the bar —
assumed, operator may override.

## Operator decision (resolves Q4, recorded before continuing)

Presented as a batched question (AskUserQuestion) with the three priced
options above plus their preview detail. **Operator chose Option C
(critical-path fix, recommended)**: `run_manifest.py`, `rules/conj.py`,
`workflow/profiles.py`, `invariants.py` — 4 files, all 16 hardcoded
sites within them (the full per-file counts from the census: 5 + 5 + 4
+ 2). This selection is also the operator's explicit approval to touch
`invariants.py` (frozen surface 3) for this specific, named change — the
option's own preview text said so plainly ("touches replay-validation, a
protected surface") before it was chosen. `cli/doctor.py`,
`capabilities/simulation.py`, `capabilities/research.py`, and
`workflow/conjecture_recovery.py` remain OUT OF SCOPE (moved from
"Questions for operator" to "Out of scope", confirmed, not just
deferred pending an answer).

## Questions for operator (STOP — this is the material contradiction case)

**Q4 (material, blocks `dr-plan-steps`): which scope should this tranche
deliver?**

- **Option A — literal `PARKED.md` scope only** (`run_manifest.py`'s
  repair-grant dict, ~1 line). Cheapest (~1 line, 1 file, touches only
  frozen surface 4, already approved). **Does NOT satisfy R1's own
  success condition**: a v7-configured manifest would still be rejected
  by `workflow/profiles.py`'s Literal type before a run could even
  start, so "test with a short live run" (R2) would fail at the very
  first step, not prove anything new beyond what CP1M already proved
  offline.
- **Option B — the full 23-site wiring**, all 8 files, so a v7-configured
  live run can actually reach a `program:candidate_checker` dispatch AND
  survive `verify_root` afterward. Satisfies R1 and R2 as literally
  read. Touches THREE frozen/near-frozen surfaces (run_manifest.py:
  approved; invariants.py and cli/doctor.py's qualification pair
  inventory: NOT yet approved — C1 only names run_manifest.py). Estimated
  ~60-100 changed lines across 8 files (each site is a 1-3 line
  membership-set widen, not a redesign — see census; no file needs new
  logic, only wider Literals/sets) plus regression tests per file plus
  one qualification-battery cache miss (~14 min, ~1160 calls, CLAUDE.md's
  own documented cost of any manifest/pair-inventory change) plus a
  root_sweep before/after (frozen-surface instrument, ~10 min).
- **Option C — critical-path-only subset of B**: fix only what blocks a
  LIVE RUN from reaching dispatch and surviving replay
  (`run_manifest.py`, `rules/conj.py`, `workflow/profiles.py`,
  `invariants.py` — 4 files, ~16 sites), explicitly PARKING
  `cli/doctor.py` (qualification pair inventory — needed only if the
  qualification battery itself must exercise v7, which R2's "short live
  run" does not require if the run's manifest is hand-built for the test
  rather than going through the doctor's battery), `capabilities/
  simulation.py`/`research.py` (unrelated to candidate_checker), and
  `workflow/conjecture_recovery.py` (only matters if the test run
  crashes mid-turn, which a short deliberate test run is not expected
  to). Still touches invariants.py (frozen surface 3) — still needs
  explicit approval for that one surface, narrower than B otherwise.
  Estimated ~30-45 changed lines across 4 files.

**Recommendation: Option C.** It is the smallest change that makes R1's
own success condition true (a v7 manifest can be built, a conjecture
turn can mint under it, and the resulting root replay-validates), defers
the qualification-battery cost (a real ~14-minute, ~1160-call expense
CLAUDE.md flags explicitly) to a later tranche if the operator later
wants v7 reachable through the NORMAL `deepreason doctor`/qualification
path rather than a hand-built test manifest, and leaves the
capability-channel and crash-recovery files untouched since nothing in
R1/R2 needs them. It still requires the operator's explicit words for
touching `invariants.py` (frozen surface 3) specifically, since C1 only
named `run_manifest.py`.

Stopping here per `dr-spec-change`'s own rule: "Never start
implementation with a material ambiguity open."

## Frozen-surface contact forecast

| Surface | Contact | Approval on record? |
|---|---|---|
| 1. `capabilities/state.py` digests | none — not touched by any option | n/a |
| 2. `harness.py` event application | none — not touched by any option | n/a |
| 3. Replay-validation formats (`invariants.py`) | **YES**, Options B and C (widening two membership sets so a v7 root replay-validates) | **NOT YET** — REQUEST.md C1 names only `run_manifest.py` |
| 4. Manifest schemas AND validators (`run_manifest.py`, and arguably `workflow/profiles.py`'s `WorkflowControlProfileV1` — a workflow-side schema, not literally `run_manifest.py`, but the same class of "admitting a value a validator previously rejected" concern) | YES, all options touch `run_manifest.py`; B and C also touch `workflow/profiles.py` | `run_manifest.py`: YES (C1). `workflow/profiles.py`: not literally named, same concern class — flagging rather than assuming covered |
| 5. Qualification subject digests (`cli/doctor.py`'s pair inventory) | Option B only | NOT YET |

## Blast-radius census

Every symbol/file the spec's candidate options change, grepped against
`tests/` and `docs/map/`:

- `_compile_contract_schema_repair_policy`: `grep -rn` → no test file
  names this function directly by name (tests exercise it indirectly
  through manifest compilation). MUST NOT MOVE: existing v6-only
  ceilings/grants for every OTHER contract id in the function (untouched
  by any option).
- `"conjecturer.turn.v6"` (all 23 sites): tests referencing the
  surrounding symbols — `tests/test_workflow_control_replay_c1.py`,
  `tests/test_workflow_reducer_c0.py`,
  `tests/test_workflow_control_event_storage_c1.py`,
  `tests/test_workflow_control_recovery_mutation_c1.py`,
  `tests/test_workflow_resume_lifecycle_c4.py`, `tests/test_properties.py`
  (6 files). EXPECTED TO MOVE: none of these currently test v7 at all
  (v7 has no reachable path today), so existing v6-path assertions in
  these files are MUST NOT MOVE — a widened Literal/membership-set must
  not change any v6 behavior or v6 test outcome. New v7-specific
  assertions are ADDITIVE (new test functions), not modifications to
  existing ones.
- `docs/map/` — `grep -rn "conjecturer.turn.v6\|conjecturer_turn_contract"
  docs/map/` → `SEAM-llm-x-manifest.md` does not name this contract
  directly (it documents `Route`/lease machinery, a different layer).
  No map document currently describes the conjecture-contract-version
  dispatch path in `rules/conj.py` at all — **this is itself a map gap**:
  neither `SUB-rules.md` (owns `rules/conj.py`) nor `SUB-manifest.md`
  documents the v6/v7 contract-version dispatch mechanism this tranche
  would touch. Per `docs/map/INDEX.md`'s own rule, closing this gap is
  ordinary work that moves with the code change (whichever option the
  operator picks) — not optional, not deferred.

## Out of scope (explicit)

- Fixing `rules/encoding.py::draft_encoded_commitment`'s zero-callers
  gap (a SEPARATE defect from P-CEPP-1, not named in R1, softened by the
  inline-mechanism finding above but not itself requested).
- `capabilities/simulation.py`/`research.py`'s v6-only admission gates
  (Option C explicitly defers these — not requested, unrelated to
  candidate_checker).
- `workflow/conjecture_recovery.py`'s crash-resume v6 hardcoding
  (Option C explicitly defers — R2's "short live run" is not expected
  to crash mid-turn).
- Any change to the qualification battery's normal `deepreason doctor`
  path (Option C's hand-built test manifest avoids exercising it,
  deferring the ~14-minute cache-miss cost).

## Budget (Option C, operator-confirmed)

Itemized by spec item, source-line changes only (not counting new
regression tests, which are additive and estimated separately):

- S1 (`run_manifest.py`): 3 sites, ~2-4 lines each (dict key /
  membership-set widen) = ~9 lines
- S2 (`rules/conj.py`): 5 sites, ~2-5 lines each (one new captured
  local variable + 4 call-site substitutions) = ~18 lines
- S3 (`workflow/profiles.py`): 4 sites, ~1-3 lines each (Literal widen +
  3 membership-set widens) = ~9 lines
- S4 (`invariants.py`): 2 sites, ~1-2 lines each = ~3 lines

Headline arithmetic: `python3 -c "print(9 + 18 + 9 + 3)"` → **39 lines**
(source only). Regression tests: 4 new test functions (one per item),
estimated ~15-30 lines each = ~60-120 lines. Map update (the gap named
in the blast-radius census — `SUB-rules.md`/`SUB-manifest.md` do not
document the v6/v7 contract-version dispatch path) in the SAME commit(s)
as the code, per CLAUDE.md's own rule: ~20-40 lines of new map prose +
checks.

**Total estimated diff: ~120-190 lines across 4 source files + 4 test
files + 1-2 map documents.** Under the `dr-drive-harness` default
~300-line guideline; no sub-tranche split needed.

### Amendment (post-step-4, operator-confirmed): ceiling raised

After S1 and S2's regression test landed, `tools/diff_budget.py` read
228/190 (EXCEEDED) — driven by a mid-step discovery in S2 (CHECKLIST.md
step 4): the realistic dispatch path needs a durable model-classification
binding that would otherwise require touching `cli/doctor.py` (explicitly
out of scope), so a ~50-line doctor-bypassing test helper was added
instead, legitimate and necessary, not scope creep. Presented to the
operator via `AskUserQuestion` with three priced options (raise the
ceiling / trim the test / split into sub-tranches); **operator chose
"raise the ceiling and continue."** New ceiling: **320 lines** (the
estimated final total from the stop report, with headroom), still under
the `dr-drive-harness` ~300-line guideline's *intent* (a genuinely
coherent one-fix change, not sprawl) even though the raw number now sits
just over that soft default — recorded plainly rather than quietly
redefining "guideline." No functional scope changed; only the ceiling
`dr-execute-step`'s diff-budget gate checks against.

Commits: one per spec item (S1-S4), so a failure in one item's gate run
does not block committing the others — 4 commits, each running the
affected-file ring (CLAUDE.md's own iterate-on-the-ring rule) plus one
final full-gate commit closing the CHECKLIST.

Frozen surfaces touched: `run_manifest.py` (surface 4, approved — C1)
and `invariants.py` (surface 3, approved via the Option C choice,
above). `workflow/profiles.py` is the same class of concern as surface
4 (a validator being widened) though not literally named by that
surface's file list — flagged, not assumed silently covered.

Rubric (re-read as reviewer, after the operator's answer resolved Q4):
- every R has a spec item with a machine-decidable accept? **yes** — R1
  → S1-S4, each with a pasted `pytest` command over verified-to-exist
  files; R2 → the live-run test (next phase, after CHECKLIST); R3 →
  satisfied by this session's own CLAUDE.md re-read at dr-change-orchestrator's
  environment preflight.
- blast-radius census pasted (or pasted-empty) and every hit classified?
  **yes** — full 23-site census above, all classified by file/impact;
  the 6-file test census for the v6-literal symbol also pasted and
  classified MUST NOT MOVE.
- frozen-surface contact forecast recorded? **yes** — table above,
  3 surfaces, 2 approved, 1 flagged-as-same-class.
- every mechanism the request names traced to code it actually reaches?
  **yes** — this IS the material-contradiction finding: `PARKED.md`'s
  named mechanism (the repair-policy dict) does NOT alone reach R1's
  success condition; traced exhaustively, not assumed.
- nothing in the spec untraceable to an R/C number? **yes** — every
  Item cites R1 (+C1 where the frozen-surface approval matters); the
  Option C scope itself traces to the operator's own AskUserQuestion
  answer, recorded above as its own citable decision.

Rubric: 5/5 yes.
