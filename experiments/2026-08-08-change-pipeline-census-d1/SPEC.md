# Spec for: pipeline census — Rung D1 of the dual-mode conjecture program
Traces: every item cites R/C numbers. Untraceable items are bugs.

## Map preflight (CLAUDE.md's map-preflight rule, R5)

Resolved ids from `docs/map/INDEX.md` before designing:

- `DR-SUB-capabilities` — simulation/research proposal lifecycles (R6).
- `DR-SUB-evaluation` — programs, oracles, measures, informal trials;
  names `experiments/lambda_run.py` and the property-oracle path (R6).
- `DR-SUB-rules` — `rules/conj.py`, `rules/crit.py`, `rules/warrants.py`
  (R7, R8).
- `DR-SUB-scheduler` — `Scheduler._select_problem` ranking (R9).
- `DR-CON-criticism-source` — the criticism socket (`rules/crit.py`) (R7).
- `DR-CON-warrants-and-attacks` — warrant → attack edge → status chain
  (R8).
- `DR-CON-capability-lifecycle` — typed proposal → admission → work
  order → result (R6, R11).
- `DR-CON-packs-and-token-economy` — prompt construction, section
  allocation, budgets (R9, R10).
- `DR-INV-frozen-surfaces` — checked; this tranche touches none of the
  five surfaces (measure-only).
- No `DR-SEAM-*` document names `docs/map/CON-conjecture-kinds.md`
  (it does not exist yet — this tranche creates it, an isolated new
  CON- document per `SCHEMA.md`'s triage rule: it is not named in any
  existing SEAM "Where it is expressed" table, and no two existing
  SUB-/CON- documents currently claim its content in their `Owns:`
  headers, since it does not exist).

`check: grep -q "CON-conjecture-source.md" docs/map/INDEX.md && grep -q "CON-capability-lifecycle.md" docs/map/INDEX.md`

## Items

S1 (R1, C1): no target files — this is the standing boundary for the
whole tranche.
    accept: `git diff --stat origin/claude/monitor-session-handover-63ajqv...HEAD -- src/ tests/ tools/` -> empty output at delivery time.

S2 (R2, R3, R17): setup already performed this session (branch head
verify, editable install, `dr-explain-to-operator` loaded).
    accept: already satisfied — see this tranche's opening transcript;
    `git log --oneline -1 origin/claude/monitor-session-handover-63ajqv` -> `371e84d7 ...`.

S3 (R4): REQUEST.md written and committed.
    accept: `test -f experiments/2026-08-08-change-pipeline-census-d1/REQUEST.md` -> exit 0 (already committed, commit `fbb5608c`).

S4 (R5): this SPEC.md's map-preflight section, above.
    accept: this section exists in the committed SPEC.md.

S5 (R6): CENSUS.md section "Executable-commitment paths" — enumerate
every path by which an artifact acquires an executable commitment:
`simulation.py::propose`/`propose_transactional` (`SimulationProposalV1`),
`research.py::propose`/`propose_transactional`
(`ResearchFetchProposalV1`), `experiments/lambda_run.py` (the
lambda-calculus evaluation arm), the property-oracle path
(`oracle.py::property_oracle_commitment`/`admit_counterexample`,
the dead-path per S6 PARKED P1), and safe-skeleton forbidden-case
compilation (`workloads/models.py:105`'s call into
`informal/skeleton.py::draft_forbidden_commitments`). Bounded search
for "any path these miss" (Q2): grep `src/deepreason/` for
`exec(`, `eval(`, `compile(`, `subprocess`, `ast.parse`, and
`Commitment(` construction sites with a non-`None` `eval=` field;
classify each hit as a known path (above) or a new one; a hit that is
dead code (unreachable from any public entry point, same shape as
PARKED P1) is reported as such, not silently folded into "a path".
    accept: every named path has a pasted `grep -n` or `sed -n` command
    in CENSUS.md; the bounded search's own command is pasted with its
    full hit count.

S6 (R7): CENSUS.md section "Criticism dispatch per kind" —
`crit_program` (`rules/crit.py:895`) vs `crit_argumentative`
(`rules/crit.py:1175`)/`crit_argumentative_batch` (`rules/crit.py:1336`)
selection logic (the caller that chooses between them); what the
rendered pack shows about a target's kind (grep pack-rendering code for
any kind-conditional section); where `ARGUMENTATIVE_AUTHORITY`
(`observe_only`/`trial_required`) is read (`config.py`) and enforced
(the call site(s) branching on it); the exact semantics of
`execution_backed`/`formally_backed` prose-immunity in
`rules/warrants.py`.
    accept: every claim has a pasted `grep -n`/`sed -n` command; the
    selection-logic claim traces to the actual caller function name and
    line.

S7 (R8): CENSUS.md section "Refutation semantics per kind" — the
DEMONSTRATIVE path at `rules/crit.py:805` (what dies: artifact vs
claim); what a trial-guarded prose refutation
(`ARGUMENTATIVE_AUTHORITY=trial_required`) can and cannot do
mechanically to a target; the `suspended_unsupported` mechanics for
dependents (where it is set, what it means for a dependent's own
eligibility).
    accept: every claim has a pasted command; the dependents claim
    traces to the actual field/function that propagates
    `suspended_unsupported`.

S8 (R9): CENSUS.md section "R-g audit" — bounded search (Q3):
    (a) `grep -n "typicality\|rank\|_select_problem" src/deepreason/scheduler/scheduler.py`
        and read the ranking formula's terms; check none reads a
        conjecture's kind (execution_backed/formally_backed/eval field).
    (b) `grep -n "execution_backed\|formally_backed\|kind" src/deepreason/rules/crit.py`
        and read every pack-rendering branch; check any kind-conditional
        rendering is criticism-FORM matching (R-d), not an admission/
        exposure gate.
    (c) `grep -rn "execution_backed\|formally_backed" src/deepreason/workflow/ src/deepreason/scheduler/`
        and read every acceptance-path branch for a kind-conditional
        accept/reject.
    Each of (a)-(c) reports its finding as CONFIRMS (no penalty found,
    protection-only) or REFUTES (a penalty found, cited with file:line
    and the mechanism), per R-g's instruction to attempt refutation,
    not confirmation.
    accept: (a), (b), (c) each have a pasted command and an explicit
    CONFIRMS/REFUTES verdict with evidence.

S9 (R10): CENSUS.md section "Load-knob inventory" — table of every
budget/period/ceiling/share knob across `config.py` (e.g.
`PROP_PROPOSE_PERIOD`, `FUZZ_N`, `PACK_TOKEN_BUDGET`), `v6_policy.py`,
`capabilities/policy.py` (capability controller budgets), criticism
policy fields (`run_manifest.py`'s `CriticismPolicyV1`), and scratch
attention budgets (`scratch/` package). Columns: name, location
(file:line), unit, default, frozen-at-mint-time vs read-live-at-label-
time (determined by checking whether the value is read from
`RunManifest`/`policy_preset` at proposal-mint time or from live
`Config`/`harness.state` at labeling/dispatch time).
    accept: every row has a pasted command locating the knob's
    definition; the mint-time-vs-live column has a pasted command
    showing the actual read site, not an inference.

S10 (R11): CENSUS.md section "Historical encoding-failure evidence" —
corpus (Q4): every committed root under `experiments/**/log.jsonl`
(same corpus root_sweep.py already walks) plus the turmite/jolt roots
CLAUDE.md names by name. Method: for every `LLMAttempt` in every
capability-channel-role call's `attempt_trace` with `valid=False`,
read its `validation_path`/`diagnostic_ref` blob; classify as ENCODING
(schema/structural violation — JSON Schema, "not expressible",
malformed identifier, self-link, observable-key pattern) or CONTENT
(a judgment the model made was substantively wrong, not a structural
violation). Report the fraction ENCODING/(ENCODING+CONTENT) with the
denominator and the per-root breakdown; report the turmite/jolt cycle-0
blobs by name as the two canonical, previously-diagnosed cases (per
CLAUDE.md's own "Hard-won invariants" section) rather than re-deriving
them from scratch.
    accept: the classification script/command is pasted; the fraction
    is pasted with its numerator/denominator; turmite and jolt's own
    diagnostic blobs are quoted verbatim with their root path.

S11 (R12): `docs/map/CON-conjecture-kinds.md`, per `SCHEMA.md`'s
anatomy (Verified-at, Verify, Owns, Seams/Seams-undocumented, What it
is, Entry points, State it owns, Invariants, Where to change what,
Traps), naming the kind signal (R-c's answer: structural, not a typed
field yet — `ConjectureCandidate` has no commitment channel per the
preplan's own "what exists today"), the dispatch/refutation/R-g
findings from S6-S8 as its body, and a `check:` line per load-bearing
claim that would fail if the behavior regressed.
    accept: `python tools/docs_verify.py` reports the new document's
    checks passing; `python tools/docs_verify.py --audit` finds none of
    its checks unfalsifiable; `python tools/docs_verify.py --links`
    passes (no dangling `DR-` reference).

S12 (R13): full acceptance gate.
    accept: every CENSUS.md row has a pasted command (grep for the
    census's own M-number rows without a following fenced command
    block — none found); `python tools/docs_verify.py` -> "0 failed";
    `python tools/docs_verify.py --audit` -> "0 findings" (exact wording
    to be confirmed against the tool's actual output format);
    `python -m pytest tests/ -q -n 4` run once at the boundary -> 0
    failed, net of any pre-existing failures found and named (S6's P1/P3
    are LIVE-RUN defects, not pytest failures per this tranche's own
    reading of PARKED.md — see Assumption A5; if the gate is fully green
    this reconciles to "0 failed, no pre-existing failures to net out").

S13 (R14): PARKED.md — any defect noticed during the census (e.g. any
new dead path found in S5, any inconsistency found in S8) recorded
with a ready-to-send `deepreason-orchestrator`/`dr-set-goal` prompt,
same shape as S1/S6's PARKED.md.
    accept: `test -f experiments/2026-08-08-change-pipeline-census-d1/PARKED.md` -> exit 0 (created only if a defect is actually found; if none is found, this item is marked "no defects found this tranche" rather than an empty file, per S1/S6's own convention of only writing PARKED.md when there is something to park).

S14 (R15): commit and push at every phase boundary (REQUEST.md done;
SPEC.md next; CHECKLIST.md; each executed step; VALIDATION.md;
DELIVERY.md).
    accept: `git log --oneline origin/claude/pipeline-census-d1-c9h41d..HEAD` at delivery time -> empty (nothing unpushed).

S15 (R16): deliver through `dr-validate-change` then `dr-deliver-change`,
then stop.
    accept: VALIDATION.md and DELIVERY.md both exist and are committed.

S16 (C3, R-g): every S6/S8 finding is written so it could be wrong —
S8 explicitly instructs REFUTE-don't-confirm; this item is the rubric
check that S8's three sub-searches were actually run adversarially
(i.e., the CENSUS.md prose does not merely restate the preplan's
"expected finding" without having grepped for the counter-case).
    accept: S8's CENSUS.md section shows the pasted grep for each of
    (a)/(c) even though the expected answer is "no hits" — a "no hits"
    result IS the evidence, not an assumed one.

## Assumptions (operator may override)

A1 (Q1): S6 PARKED P1 (`experiments/2026-08-08-live-two-seat-ab-s6/PARKED.md`)
is the anchor for the "dead property-oracle path" — its own diagnosis
chain (call graph: `property_designer` → `propose_properties` →
`checker_wf_commitment` → requires an existing `program:property_oracle`
commitment → only minted by `admit_counterexample`, which itself
requires one as precondition → circular, no public bootstrap) is reused
verbatim in CENSUS.md rather than re-derived, per the operator's own
"diagnosis chain" phrasing in the task pointing at this file.

A2 (Q2): the bounded search for "any path these miss" is the grep list
in S5 (`exec(`, `eval(`, `compile(`, `subprocess`, `ast.parse`,
`Commitment(...eval=`) — smallest reasonable set that would catch any
executable-authoring mechanism the four named paths miss, since all
four named paths use one of these primitives internally. Assumed,
operator may override with a broader or narrower list.

A3 (Q3): the R-g audit's bounded search is the three-part grep in S8
(scheduler ranking terms, crit.py kind-conditional rendering, workflow/
scheduler acceptance branches) — chosen because these are exactly the
three surfaces R-g's own text names ("scheduler ranking terms, pack
rendering differences, acceptance criteria"). Assumed, operator may
override.

A4 (Q4): the corpus for the encoding-failure fraction is every root
under `experiments/**/log.jsonl` (root_sweep.py's own corpus) plus the
turmite/jolt roots CLAUDE.md names — not `runs/` (no `runs/` directory
holds committed roots in this repo per a preflight `find`), and not
every LLM call ever made (only capability-channel-role calls, since R11
asks about "executable-authoring attempts by the conjecturer"
specifically). Assumed, operator may override.

A5 (Q5), CORRECTED post-gate-run (was wrong; corrected plainly rather
than silently): "P1/P3" in the task's acceptance line does NOT refer to
S6's `PARKED.md` P1/P3 as first assumed. Running the full gate found
`tests/test_module_fingerprints.py::test_absence_is_valid_before_the_feature_and_presence_valid_after`
failing with `ValueError: too many values to unpack (expected 1)` — and
`experiments/2026-08-07-change-seats-in-record-s5/PARKED.md` line 17
names this EXACT failure "tracked as P1/P3 in every one of Rungs
S1-S4's own `PARKED.md` files" (`experiments/2026-08-06-change-seat-census-s1/PARKED.md`,
`...-seat-binding-wired-s3/PARKED.md`, `...-qualification-per-seat-s4/PARKED.md`).
That is the actual referent: a long-standing harness/continuation-record
defect (a continued root can carry 2 `module_fingerprints` payloads
where this test assumes exactly 1), already queued for
`deepreason-orchestrator`, unrelated to this tranche's own zero code
changes. The gate also surfaced a SECOND failure,
`tests/test_continuation.py::test_a_stop_with_no_typed_receipt_refuses_continuation`,
traced to S6's own `PARKED.md` P3 (the `continue`-resume crash) leaving
behind committed root `failed-epoch1-run-8c77c6588485304d1f73416318c62949`
with an unexpected stop reason this test's witness scan does not
expect — pre-existing (S6 committed that root before this session
started; this tranche changed no code that could cause it), but NOT
previously connected to a gate-level test failure in any prior PARKED.md.
Recorded as a fresh PARKED entry (below) rather than folded silently
into "the named P1/P3", since it is a distinct defect with its own cause.

## Questions for operator (STOP if non-empty)

(empty — every open question resolved to a smallest-reasonable-reading
assumption above; none differ materially enough in files/effort/
behavior to warrant a stop, per dr-ask-the-right-question's dominance
test: the record itself (S6's PARKED.md, CLAUDE.md's own text,
root_sweep.py's existing corpus convention) answers each one.)

## Out of scope (explicit)

- Rung D2 (dual-mode design) — not started; D1 is measurement only.
- Fixing PARKED P1/P2/P3 from the S6 tranche, or any new defect found
  here — parked per R14, never fixed (this tranche's own R1 forbids
  `src/` edits regardless).
- Any change to `experiments/2026-08-06-change-seat-census-s1/` or any
  other prior tranche's artifacts.
- Deciding D4's load-mix policy — D1 only inventories the knobs; it
  does not design the dial.

## Frozen-surface contact forecast

none expected — checked against `docs/map/INV-frozen-surfaces.md`'s
five surfaces (`capabilities/state.py`, `harness.py`, `invariants.py`/
`verification/`, `run_manifest.py`, `qualification.py`'s subject
digest) and the frozen-adjacent `route_fingerprint`. This tranche reads
all of these but writes to none — R1's own boundary (`src/`, `tests/`,
`tools/` byte-untouched) makes contact structurally impossible. The
sole write target, `docs/map/CON-conjecture-kinds.md`, is a new file
outside every frozen surface's `Owns:` header.

`check: git diff --stat origin/claude/monitor-session-handover-63ajqv...HEAD -- src/deepreason/capabilities/state.py src/deepreason/harness.py src/deepreason/invariants.py src/deepreason/run_manifest.py src/deepreason/qualification.py` -> empty at delivery time.

## Blast-radius census

`grep -rn "CON-conjecture-kinds" tests/ docs/map/` -> no hits (verified
2026-08-08; the only existing reference to this filename anywhere in
the tree is `docs/proposals/DUAL_MODE_CONJECTURE_PREPLAN.md:139`, the
naming source, outside both searched trees). Classification: MUST NOT
MOVE (nothing currently asserts on this not-yet-existing document, so
nothing can be broken by adding it; `docs_verify.py --links` will
start checking its internal references once it exists, which is the
intended new coverage, not drift).

`grep -rn "property_oracle_commitment\|admit_counterexample\|checker_wf_commitment" tests/ docs/map/`
-> to be pasted in CENSUS.md/CHECKLIST execution (S5); classified there
as MUST NOT MOVE (this tranche only reads these functions, never edits
them).

No other symbol is targeted for change by this spec (measure-only), so
no further blast-radius rows apply beyond the new document's own
non-existence today.

## Budget

~600-900 lines across CENSUS.md + CON-conjecture-kinds.md + this
skill-chain's own artifacts (REQUEST/SPEC/CHECKLIST/VALIDATION/
DELIVERY/PARKED). Estimated 6-10 commits (one per phase boundary plus
incremental CENSUS.md commits per CHECKLIST step). Frozen surfaces
touched: none.

**Revised 2026-08-08, mid-execution:** actual tranche size reached
~1921 lines after CENSUS.md's six measurement sections (step 15),
roughly double the original estimate — driven entirely by pasted
command+output evidence per claim (the task's own "no claim without
evidence" requirement), not scope creep; `src/`, `tests/`, `tools/`
remained byte-untouched throughout. Per `dr-execute-step`'s ceiling
rule, this was raised as a STOP (options: continue vs. trim already-
committed evidence) rather than absorbed silently. Operator decision:
continue as planned — no code risk either way, and trimming would
weaken the evidence trail for no safety benefit. Revised budget: no
new ceiling set; the remaining two sections (map document, gates) are
expected to add a few hundred more lines, accepted explicitly.

Rubric: 6/6 yes
- every R has a spec item with a machine-decidable accept: yes (S1-S16
  cover R1-R17; R17 covered by S2).
- blast-radius census pasted (or pasted-empty) and every hit
  classified: yes.
- frozen-surface contact forecast recorded: yes (none expected, with a
  check).
- every mechanism the request names traced to code it actually
  reaches: yes (S1 PARKED P1's diagnosis chain confirmed still live in
  `oracle.py`; `workloads/models.py:105` confirmed to be the skeleton
  compilation call the task names; `lambda_run` confirmed to exist at
  `src/deepreason/experiments/lambda_run.py`).
- DESIGN-AND-STOP sections: n/a — this is MEASURE ONLY, not
  DESIGN-AND-STOP; Measurements/Options sections are not required by
  the template's own gating ("DESIGN-AND-STOP only") and are instead
  the entire content of CENSUS.md, produced during `dr-execute-step`.
- nothing in the spec untraceable to an R/C number: yes (re-read pass
  performed; every S-item's parenthetical cites R/C numbers).
