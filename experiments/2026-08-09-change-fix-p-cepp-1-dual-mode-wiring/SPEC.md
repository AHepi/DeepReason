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

## Budget

Pending Q4's answer — see the three priced options above. No single
Budget line can be given honestly before the operator picks a scope;
committing one now would be exactly the "headline that contradicts its
own itemization" trap `dr-spec-change`'s own procedure warns against.

Rubric: 6/7 yes — the 7th ("nothing in the spec untraceable to an R/C
number") is the one item this STOP itself represents: the 22 EXTRA sites
beyond `PARKED.md`'s named one are not literally traceable to R1's
QUOTED words (which named only `run_manifest.py`), which is exactly why
this is reported as a material contradiction and a stop, not silently
folded into "R1, expanded."
