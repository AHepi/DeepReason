# Errata — corrections to committed documents

Started 2026-08-03 at the operator's request. One entry per discovered error
in a COMMITTED document: what the document said, what the record shows, where
it was corrected (or why it stands uncorrected). Entries are appended, never
rewritten — if a correction itself proves wrong, that is a new entry. Evidence
pointers only; no narrative.

Scope note: this ledger is for documents (handovers, map, RESULTS, specs).
Code defects have tranches; run roots are never edited at all. Findings
about the less-capable-executor infrastructure (the cross-cutting skills,
calibration blocks, and the 2026-08-03 handover program) have their own
ledger: `docs/ERRATA_EXECUTOR.md`.

---

## 2026-08-03

**E1 — handover line pointer, cosmetic.** `docs/HANDOVER_2026-08-02.md` cites
the rc=5 exit contract as `application/models.py:1258`; the stress-triplet
RESULTS.md cites `:1269`. Both point inside `run_result_exit_code` — 1258 is
the `def`, 1269 the `return 5` branch. No correction needed; recorded because
the two documents disagree and a reader diffing them should not go looking
for a third function. Evidence: `src/deepreason/application/models.py`
(`def run_result_exit_code`).

**E2 — the map declared periphery × verification a non-interaction.**
`INDEX.md`'s seam matrix had no periphery row (which INDEX itself defines as
"no measured import traffic at all"), and neither `SUB-periphery.md` nor
`SUB-verification.md` listed the other in `Seams-undocumented:`. The traffic
is real — `invariants.py` re-derives the attached-evidence triple that
`evidence/render.py` writes — but every import between the sides is
function-local, invisible to the coupling metric. Plausibly contributory to
the attached-evidence defect (tranche
`experiments/2026-08-03-fix-attached-evidence-integrity`): no document told
the reader's author what the writer guaranteed. Corrected 2026-08-03:
`SEAM-periphery-x-verification.md` created, matrix row added, both `Seams:`
lines fixed.

**E3 — the pre-v6 census check went stale-false the day it mattered.**
`SEAM-harness-x-verification.md` pinned the root census at
`len(R)==42, 25 v6 / 14 raising / 3 no-manifest` (Verified-at 9fa394d9).
Commit `3062454e` (2026-08-02) added the three stress-triplet roots, making
the true tracked census 45 / 28 / 14 / 3 — and nobody re-ran the document's
checks, so the map carried a failing check for a day while its stamp claimed
otherwise. Corrected 2026-08-03 (numbers updated, and the check now names
this incident). The general lesson is already SCHEMA.md law: a stamp advanced
without a re-run is the one dishonest state the system has.

**E4 — `INV-frozen-surfaces.md` census numeral.** Same staleness as E3 on the
prose side: "25 v6" → 28 after the triplet commit. Corrected 2026-08-03. Its
companion claim — that `verify_root_report` surfaces three of the 14 raising
roots as verdict rows rather than ERROR rows (the 11-vs-14 sweep delta) —
is NOT adjudicated here; that is the handover's open item 2, still parked in
`experiments/2026-08-03-fix-attached-evidence-integrity/PARKED.md`.

**E5 — the "45-root baseline" is not reproducible from the committed tree.**
`experiments/2026-08-02-stress-triplet/RESULTS.md` (sweep appendix) reports
"45 roots" from `tools/root_sweep.py`, and `docs/HANDOVER_2026-08-02.md`
says that baseline is "reproducible from it". On a clean checkout of the
same tree the instrument yields **42 rows**: it scans `experiments/` only,
and 42 = 39 prior + 3 triplet. The three no-manifest calibration roots under
`runs/jolt_positive_headroom_v3_1/` are outside its glob, so the appendix's
45 must have included three roots that existed only in that session's
working tree and did not survive the container rollback; they cannot now be
identified. What IS reproducible and was reproduced 2026-08-03: 11 ERROR
rows, and the three triplet rows byte-matching the appendix
(`triage valid=False epistemic_passed=True att=1 blind=0`, orbit and
workshop `valid=True epistemic_passed=False att=0 blind=1`). The per-root
claims stand; the headline count does not.

**E6 — run-0a3e93d6's recorded verdict was a reader artifact.**
`REPLAY_VALIDATION.json` in the committed triage root says `valid: false`
with one `attached-evidence` violation whose detail names a missing artifact
that exists (seq 4 of the root's own log). The root is evidence and is not
edited; the READER was wrong and was fixed in tranche
`experiments/2026-08-03-fix-attached-evidence-integrity` (verdict R;
DIAGNOSIS.md has the four-artifact proof). Post-fix, `verify_root` on the
unchanged bytes returns zero violations — the stored file remains as the
honest record of what the verifier believed on 2026-08-02, which is exactly
why callers assemble `REPLAY_VALIDATION.json` rather than the verifier
writing it: the verdict is a function of root bytes AND reader code, and
only the first is frozen.

**E7 — four map checks pinned claims to run roots that were never committed
(supersedes E5's "cannot now be identified").** The turmite and jolt ladders
gitignore their `home/` by design ("the typed outcome and the audit are
committed instead"), so `run-bc3e8797` (turmite) and `run-b4d6dfda` (jolt)
only ever existed in the session that ran them — and they are two of the
three extra rows in E5's 45-vs-42 sweep discrepancy. Four checks opened those
roots directly: `SEAM-harness-x-verification.md` (the read-only probe and the
521-file no-write pin), `SUB-adjudication.md` (the blindness trap), and
`SEAM-adjudication-x-rules.md` (whose prose called jolt "committed"). All
four could pass only on the machine that ran the ladders; every fresh clone
fails them. Corrected 2026-08-03: repointed at committed roots (orbit
`run-6472629d`, and the run ids kept in prose as history). The blindness trap
gained better evidence in the exchange — orbit is a post-detector root, so
the check now asserts the blindness finding FIRING rather than the defect era
it could no longer reproduce. Rule for the future, already implicit in
SCHEMA.md: a check may only open a root that `git ls-files` knows.

**E8 — FIX.md predicted the wrong instrument for the verdict flip.** The
attached-evidence tranche's FIX.md (committed `df0fd0fd`) predicted
run-0a3e93d6's sweep row would flip `valid` False → True. It does not, and
correctly not: the sweep reads `verify_root_report`, which also binds the
root's own STORED terminal summary — frozen evidence, written 2026-08-02 by
the then-defective reader — and refuses to call a root valid whose own
record says invalid (`run-result-verification`). The fixed reader's verdict
is visible in `verify_root` (0 violations, pinned by the regression test)
and in `verify_post_commit_report` (`valid: True`, the stored-summary-
excluded projection). Net effect: the before/after sweeps compare
byte-identical — the strongest possible frozen-surface outcome — and the
prediction error was about which instrument shows the flip, not whether the
defect is fixed. Same lesson as E4/E5: cite the instrument with the number.

## 2026-08-03 (continued — rung 1 of the modularisation ladder)

**E9 — seven seam documents existed but `INDEX.md`'s matrix and six owning
`SUB-`/`CON-` headers still said "not yet written" or omitted them
entirely.** `SEAM-bridge-x-llm.md`, `SEAM-harness-x-workflow.md`,
`SEAM-llm-x-workflow.md`, `SEAM-bridge-x-manifest.md`,
`SEAM-ontology-x-rules.md`, `SEAM-scheduler-x-workflow.md` and
`SEAM-evaluation-x-ontology.md` are all full, substantial documents (not
stubs) — `INDEX.md`'s seam matrix marked all seven "— not yet written".
Independently, cross-referencing every seam document's `Sides:` line
against its two owning documents' `Seams:` headers found eight further
misses across six files: `SUB-ontology.md` (missing
`DR-SEAM-evaluation-x-ontology`), `SUB-manifest.md` (missing
`DR-SEAM-llm-x-manifest` and `DR-SEAM-manifest-x-schools`),
`SUB-bridge.md` and `SUB-llm.md` (both missing `DR-SEAM-bridge-x-llm`),
`CON-schools.md` (missing `DR-SEAM-manifest-x-schools`), and
`SUB-harness.md` (missing BOTH `DR-SEAM-harness-x-workflow` and
`DR-SEAM-harness-x-verification` — its `Seams:` header was entirely empty
despite two real seam documents). No mechanism in `tools/docs_verify.py`
checks a `Sides:` line against both parties' `Seams:` headers, so nothing
would have caught this short of the cross-reference done here. Corrected
2026-08-03 in `experiments/2026-08-03-change-rung1-sockets-on-paper/`:
`INDEX.md`'s seven matrix rows repointed at their real documents, and all
eight missing `Seams:` entries added (each document's `Seams-undocumented:`
line correspondingly shortened). Discovered while executing R2 of rung 1
(every `SUB-*.md` surfaces its seams in prose) — the header had to be
accurate before it could be honestly surfaced.

## 2026-08-04

**E10 — the handover prescribed a fixture that cannot reach the code it
was meant to test.** `docs/HANDOVER_2026-08-03.md`, Rung 3's accept
line: "a determinism test proving a run's outputs are byte-identical
before/after the registry (reuse the offline no-provider fixture pattern
from `tests/test_attached_evidence_citation.py`)." That fixture replaces
`deepreason.ops.run_scheduler` — the function that constructs the
`Scheduler` — so `init_schools` and `allocate`, the exact functions rung
3 migrates, are never executed under it; a test built on it would pass
while proving nothing. Found at spec time by the rung-3 executor
(`experiments/2026-08-03-change-rung3b-registry-call-site-migration/
SPEC.md` Q3), which delivered the property R7 wanted via a mock-endpoint
`Scheduler` plus a mutation test instead. Corrected 2026-08-04: the
handover's rung-3 accept line now carries the correction note, and the
lesson generalized — rung/spec text should state acceptance PROPERTIES;
a concretely named mechanism is a suggestion the spec phase must verify
for reachability, never a requirement. Companion tooling fact, same
tranche (`55b16ce9`): `docs_verify --fast` reuses cached results and so
cannot catch documents newly affected by a `src/` change — the full mode
can and did; recorded in the handover's environment facts.

## 2026-08-09 (sweep of tranches since 2026-08-04)

**E11 — rung 4's fingerprint-timing prose contradicted its own check.**
`docs/map/SEAM-schools-x-scheduler.md`'s fingerprint row said the
module-fingerprint stamp "fires at construction" while a check two
lines below it asserted the opposite. Rung 4
(`experiments/2026-08-04-change-rung4-module-fingerprints/`) moved the
stamp to `run(cycles > 0)` and added the corrective check but left the
stale sentence in place. Found and corrected in passing by rung 5 the
same day (`experiments/2026-08-04-change-rung5-dumb-alternative-backend/
DELIVERY.md:113-116`: "Corrected in passing: `SEAM-schools-x-scheduler`'s
fingerprint row said the stamp fires 'at construction' while its own
check two lines below asserted it does not... `docs_verify` validates
checks, not the prose around them."). The map document's current text
is correct ("outside the `N_SCHOOLS > 0` gate... and NOT at
construction, which must append nothing") but the correction itself was
never ledgered until now.

**E12 — this ledger's own E5 misidentified the three no-manifest
roots.** E5 (above) states "The three no-manifest calibration roots
under `runs/jolt_positive_headroom_v3_1/` are outside its glob."
Measured directly at commit `8122b0e3`, by manifest load over every
git-tracked root
(`experiments/2026-08-05-fix-expired-census-readers/PARKED.md` P1a):
the three `runs/jolt_positive_headroom_v3_1/calibration/2026070{1,2,3}`
roots actually RAISE — they are not the no-manifest three. The real
no-manifest three are `experiments/bronze_flat_2026-07-13/
{deepseek-v4-pro,kimi-k2_6,qwen3_5_397b}`, which are INSIDE
`root_sweep.py`'s `experiments/` glob, not outside it. E5's headline
finding (the 45-root baseline is not reproducible from the committed
tree) is unaffected — only this supporting sentence is wrong. Flagged
and explicitly deferred by the fix-expired-census-readers tranche
itself ("Not done here because `docs/ERRATA.md` is outside this
tranche's declared scope... suggested disposition: a one-entry append
to `docs/ERRATA.md`"), and carried forward unfixed through
`experiments/2026-08-05-fix-loopback-fixture-daemon/PARKED.md:105`. Per
this ledger's own rule ("if a correction itself proves wrong, that is a
new entry"), E5 is not edited.

**E13 — CLAUDE.md's directory map named only the v1.5 spec amendment.**
The `docs/` row under "Directory map" read "specs (harness v1.3 + v1.5
amendment, ... BASIN_REPORT)", omitting v1.4 and v1.6, which exist on
disk and are part of the current spec. Surfaced by the operator
questioning the O2 reading list; the stale line had already propagated
into one executor instruction. Corrected 2026-08-08, commit `1f6c24ab`
("CLAUDE.md: correct stale spec listing (v1.4/v1.5/v1.6 amendments
exist)"): now reads "specs (harness v1.3 + v1.4/v1.5/v1.6 amendments —
read ALL amendments; note 'V6' elsewhere names the RunManifest/policy
generation and the wire-contract series, NOT this spec document
series), ... BASIN_REPORT". Already fixed in place; never ledgered
until now.

**E14 — CLAUDE.md's turmite/jolt cycle-0 paragraph read as a current
blocker after both were fixed.** The "Hard-won invariants" section's
turmite (`_not_a_self_link`) and jolt (observable-naming) cycle-0
failures carried no dating clause, so the paragraph read as describing
live/current blockers though both were fixed 2026-08-01 (SWEEP.md/
REPAIR_OSCILLATION.md). Flagged by the overnight-omnibus tranche's own
preflight ("stale as of this tranche, per PREREG.yaml's own note" —
`experiments/2026-08-09-overnight-omnibus/RESULTS.md:205-212,719-722`).
Corrected 2026-08-09, commit `7e8f42402` ("CLAUDE.md: date the cycle-0
examples (fixed 2026-08-01; live SUCCEEDED 2026-08-09)"): the paragraph
now ends "(Both specific encodings were FIXED 2026-08-01 — SWEEP.md/
REPAIR_OSCILLATION.md; live simulation SUCCEEDED events recorded
2026-08-09, overnight-omnibus Block B — the examples are historical,
the blob-first discipline is the enduring rule.)" Already fixed in
place; never ledgered until now.

**E15 — S6's pre-registration called `property_designer`'s non-firing a
"stochastic miss"; the record shows a structural dead path.**
`experiments/2026-08-08-live-two-seat-ab-s6/PLAN.md:83-89`
(pre-registered before the live run) invoked CLAUDE.md's
capability-channel stochasticity doctrine to excuse `property_designer`
never firing live as "an accepted, typed, non-failure outcome," and the
tranche's first `RESULTS.md` segment (lines 98-111) repeated this as
"the accepted, PRE-REGISTERED stochastic miss." A dated correction
segment in the same `RESULTS.md` (lines 168-227, "correction:
'stochastic miss' was wrong; the path is structurally dead") shows the
probability was 0, not low: `oracle.py::property_oracle_commitment`
(the only minter of the triggering property-oracle commitment) has
exactly one caller, `admit_counterexample`, which itself requires that
commitment to already exist — a bootstrap circularity, structurally
dead regardless of question, cycle budget, or bound model, not a case
CLAUDE.md's stochasticity doctrine covers. Corrected 2026-08-08 by
`RESULTS.md`'s own dated, non-destructive segment (the original segment
is not edited) and cross-referenced in `PARKED.md` P1; `PLAN.md` itself
stands uncorrected, per the tranche's own pre-registration convention.
Downstream documents already cite the corrected framing
(`docs/proposals/RECORD_LIFECYCLE_DEFECT_PLAN.md:152-153`;
`docs/proposals/CODER_AS_TOOL_PREPLAN.md:39-41`); only this ledger
lacked the pointer until now.

**E16 — S6's `PARKED.md` misattributed the `continue`-crash to a
pending atomic child; L1 found it fires regardless.**
`experiments/2026-08-08-live-two-seat-ab-s6/PARKED.md` P3 described the
crash fixture as having "one of these decompositions still in flight
(some atomic children completed, others not yet attempted)" and "the
pending item at resume time was an ATOMIC child... two sibling children
already `terminal_status: 'completed'`" — read as requiring an
incomplete child for the crash to fire.
`experiments/2026-08-08-fix-l1-continue-resumable-crash/
DIAGNOSIS.md:117-124` checked this directly against the fixture's own
record and refuted it: the one recorded decomposition is FULLY
resolved (`contract_decomposition_completed` at seq 64, both children
`terminal_status: 'completed'`), and the crash mechanism fires anyway,
on ANY criticism atomic child ever admitted, pending or not — a
broader, different mechanism than P3 described. Corrected 2026-08-08 by
the L1 tranche's diagnosis; S6's own `PARKED.md` stands as written (a
closed tranche's parked item, not edited).

**E17 — O1's "14 genuine multi-node floating chains" superseded by
O2's spec-true re-run showing zero.**
`experiments/2026-08-08-change-grounded-overlay-o1/
RESULTS.md:47-53,182-183` and `DELIVERY.md:29-32` reported "14 genuine
multi-node floating chains across 12 roots" as the rung's one positive
catch, computed against an operationally-proxied "ground" definition
(`Provenance.role ∈ {SEED, IMPORT, USER}`).
`experiments/2026-08-08-change-grounded-overlay-o2/
SPEC.md:195-255`, re-running against the spec-DERIVED ground definition
the operator's Amendment 1 required instead (adding a §11.3
program-check anchor the proxy structurally could not see), found the
count collapses to zero across all 48 roots and all 14 of O1's flagged
chains: "spec_floating=2586(chains=0) ... EVERY one of O1's own 14
flagged 'self-supporting clusters' turns out to already rest on a
program-check-verified member once that anchor type is honored." O2
states the consequence explicitly: "R5's premise does not survive the
spec-true audit... that catch is zero multi-node chains, corpus-wide."
O1's own `RESULTS.md`/`DELIVERY.md`/`CHECKLIST.md`/`VALIDATION.md`/
`REPORT.md` remain unmodified and still assert the 14-chain catch; O2
itself is a DESIGN-AND-STOP tranche per its own preplan and stopped at
`SPEC.md`, never delivering a closing note back into O1's documents.
The correction stands only in O2's `SPEC.md` prose until this entry.

## 2026-08-11

**E18 — `docs/map/INV-frozen-surfaces.md`'s "Fields compared" list
undercounted what the root sweep actually needed to compare, and
`tools/root_sweep.py` matched that undercount.** Found during Item 1 of
the operator's seven-item sweep/smoke currency audit
(`experiments/2026-08-11-sweep-smoke-currency/`). The sweep's `modules=`
and `seats=` columns reported only the IDENTITY keys of the two typed
record families (`ModuleFingerprintV1.module_id`, `SeatBindingV1.group`
— both sets of names), never their CONTENT digests
(`ModuleFingerprintsEventPayloadV1.digest`,
`SeatBindingsEventPayloadV1.digest`). Two roots sharing the same
module/group names but differing in actual fingerprinted content or
bound profile would have swept as identical — a real gap in an
instrument whose stated job (`INV-frozen-surfaces.md`, "The root
sweep") is exactly to catch a reader change silently reinterpreting a
stored verdict.

**Correction to this entry's own first draft (same-day, per the
append-only rule — a claim proved wrong is a new correction, not a
silent edit): the gap was NOT hypothetical.** The first draft of this
entry claimed "no committed root under `experiments/` carries either
stamp yet," inherited unverified from `tools/root_sweep.py`'s own
comment ("no committed root under `experiments/` carries this stamp
yet") without independently checking. The completed full-tree re-sweep
(103 roots, `sweep-after-item1.txt`) shows this was WRONG: several
committed roots already carry both stamps — e.g.
`experiments/2026-08-04-change-rung5-dumb-alternative-backend/*` and
`experiments/2026-08-05-testphase-live-validation/*` carry
`modules=default`/`round-robin`;
`experiments/2026-08-08-corpus-enrichment-patrol-pilot/*` carries
`seats=coder`/`conjecture`. The gap was live on real record data, not
merely possible in principle. What the correction does NOT change: no
actual divergence was hiding behind the gap — every distinct identity
key (`modules=default`, `modules=round-robin`, `seats=coder`,
`seats=conjecture`) maps to exactly ONE digest across every root that
uses it, so no committed root's verdict actually changes with this
fix; only the instrument's ABILITY to have caught a divergence, had one
existed, was missing. `docs/map/INV-frozen-surfaces.md`'s own "Fields
compared" prose listed only the four original fields and never named
the digests as missing, so a reader of that document had no way to
know the coverage gap existed. Fixed mechanically, same tranche:
`tools/root_sweep.py` now also reports `module_digests=`/
`seat_digests=` (commit in
`experiments/2026-08-11-sweep-smoke-currency/`), and `INV-frozen-
surfaces.md`'s "Fields compared" list and `Verify` prose were updated
in the SAME commit per the map's own convention, and corrected again
in this same-day follow-up for the stale-premise finding above. Zero
`src/` lines changed. The full detached re-sweep (`sweep-after-item1.txt`,
103 roots, 11 ERROR lines — matching the documented baseline exactly,
all `UnsupportedRunManifestVersionError`) confirms no committed root's
verdict moved on any field that existed before this fix.

Recorded per the operator's standing directive: an out-of-date
verification instrument is a debugging error, and belongs here whether
or not it had yet produced a wrong verdict. The self-correction above
is recorded per this ledger's own rule: a correction to a correction is
a new addition within the entry, never a silent rewrite of the claim
it replaces.

**E19 — `GATES_AND_PACKAGES_PREPLAN.md` cites a tranche as authority
that was never opened.** `docs/proposals/GATES_AND_PACKAGES_PREPLAN.md:4-5`
reads: "Extends BEHAVIOR_MODES_PREPLAN and the adjudication/judge/schools
opt-in spec (`experiments/2026-08-09-change-adjudication-judge-seats-
optins/`)." That directory does not exist in the committed tree
(`ls experiments/ | grep -i adjudication-judge-seats` -> no hits) — the
cited tranche was planned but never opened, so the document's own
"Existing gates-in-fragments this unifies" census (the paragraph
immediately following the citation) rests in part on a source that
cannot be read to verify it. Found by
`experiments/2026-08-10-change-blast-radius-analysis/CENSUS.md` Part B
while tracing the operator's own "Road E" shorthand (which itself
resolves to no literal document anywhere in the repo — the operator's
compressed reference to the substance now written up as CENSUS.md B2/B3,
not to this preplan or its dangling citation). Not corrected here — the
preplan's own status line reads "PROPOSED," so no live rung depends on
this citation resolving today; recorded so a future session picking up
`GATES_AND_PACKAGES_PREPLAN.md` does not spend time looking for a
directory that was never created.
(Renumbering note, added at merge: this entry was minted as "E18" on
its delivery branch, and
`experiments/2026-08-10-change-blast-radius-analysis/DELIVERY.md`
§Errata cites it under that number. Three branches delivered the same
day each minted an "E18" against a ledger ending at E17; this ledger
serializes them in merge order, and the closed tranche's DELIVERY.md
stays as delivered per this ledger's own convention. One factual update
known at merge time: the cited tranche directory
`experiments/2026-08-09-change-adjudication-judge-seats-optins/` was
not "never opened" — it exists and is actively executing on the
then-unmerged `claude/adjudication-judge-seats-optins-4nb7ov` branch,
invisible from the tree this entry's check ran against. The dangling
citation resolves the moment that branch merges; what stands is only
that the preplan cited it before it was readable from main.)

**E20 — `docs/RESEARCH_BACKEND.md`'s header Status line says v6 in-run
research is gated; the code and the rest of the same document say it
shipped.** Line 6 reads "V6 in-run enablement remains gated
(`V6_RESEARCH_UNAVAILABLE`) and is tranche 2," written before tranche 2
landed and never re-synced. `run_manifest.py:2869-2874` shows the gate is
conditional — `V6_RESEARCH_UNAVAILABLE` fires only when research is
enabled with a backend other than `web.contained.v1`, the one implemented
backend — and the document's own later sections say tranche 2 (A, B, C1,
C2) is complete and live-proven (lines 149-189). Confirmed live against
the committed record, not just prose:
`experiments/live_research_2026-07-29/wide/runs/run-0c3ce902cc5bca75a709b04e2473d100`
replays with `verify_root` reporting zero violations, three model-proposed
research proposals, three grants, three receipts, and one consumption of
research fetches into citable evidence, and a sibling root in the same
campaign (`run-5a771259557378224bd68591483817be`) shows two of three
proposals live-denied with the typed reason `requests_budget_exhausted`.
Not corrected in `docs/RESEARCH_BACKEND.md` itself by this entry — that is
Phase A's finding, recorded here per the errata checkpoint rule; the fix
(updating the header Status line) is deferred to whoever next touches
that document, since this tranche's own scope is the probe-apparatus
SPEC, not a `RESEARCH_BACKEND.md` edit. Evidence:
`experiments/2026-08-09-change-llm-probe-apparatus/AUDIT.md` §1-2.
(Renumbering note, added at merge: minted as "E18" on its delivery
branch — the third same-day "E18" against a ledger ending at E17; see
E19's note. This ledger serializes them in merge order; the probe
tranche's own artifacts stay as delivered.)
## 2026-08-11 (adjudication-judge-seats-optins tranche — corrective amendments)

(Renumbering note, added at merge: the two entries below were minted as
"E18"/"E19" on their delivery branch, the fourth and fifth same-day
collisions against a ledger that ended at E17 when the branches forked;
this ledger serializes them in merge order as E21/E22, and the tranche's
own DELIVERY.md stays as delivered citing the branch-time numbers.)

**E21 — Amendment 10's "and" reading of the schools opt-in was recorded
as confirmed, then found too coupled and corrected by Amendment 11.**
`experiments/2026-08-09-change-adjudication-judge-seats-optins/
REQUEST.md` R26 ("Amendment 10... operator's own words: 'Yes. School
opt in. But for both criticism and conjecture.'") reads `SCHOOL_SEATS_
ENABLED` as covering BOTH the conjecture-side route-binding mechanism
(`SchoolExecutionPolicyV1.mode='route_bound'`) AND the criticism-side
route-binding mechanism (`CriticismPolicyV1.bindings`'s per-school
distinct endpoint) TOGETHER — "the operator's words resolve the
'and/or' toward 'and'... No CHECKLIST.md step needs renumbering." This
reading was written into `src/deepreason/config.py`'s
`SCHOOL_SEATS_ENABLED` field comment at Step 43 ("Gates whether a
school seat may be bound to a distinct route for BOTH conjecture-side
routing... and criticism-side routing... together, not either in
isolation") and into SPEC.md's original §2(d) design prose. The
operator's next message (Amendment 11, same REQUEST.md, R27) corrected
this directly: "School and criticism should be separate... conjecture-
side school seats and criticism's attachment-to-a-school are two
INDEPENDENTLY toggleable things, not one flag driving both. R26's
reading... was too coupled." Corrected 2026-08-10/11 by rewriting Part
E into two fully independent CLI levers (`--school-seat`, Step 44;
`--criticism-seat`, Step 44b) and rewriting `config.py`'s
`SCHOOL_SEATS_ENABLED` comment to name them as independent (commit
`a8307d69b` for Step 44's config comment fix). REQUEST.md's own R26
entry stands unedited, verbatim, per its append-only ledger rule — a
reader stopping at Amendment 10 without reaching Amendment 11 would be
misled about the delivered design; this entry is that pointer.

**E22 — CHECKLIST.md's step-3 STOP priced Road A/Road B for Road E;
neither shipped.** The same tranche's `CHECKLIST.md` step 3 recorded a
STOP: `crit_argumentative_batch`'s `active_v6` branch hard-requires
`critic_school_id`, and the step's own design note had assumed this
guard could be widened with a bypass flag (Road A) or duplicated into a
parallel dispatch function (Road B). Neither road was built. The
operator's Amendment 7 ("No I need a clean separation between school
and criticism. Although they still need to interact.") directed a
THIRD shape — removing the coupling at its root via self-detection
(`crit_argumentative_batch` resolves its own v6 authority, no new
scheduler keyword) — which is what steps 4-15 actually built.
`CHECKLIST.md` step 3 already self-corrects in place ("**STOP,
resolved.**... Resolved by REQUEST.md Amendment 7... supersedes both
originally-priced roads... Steps 4-14 below replace the original steps
4-8, which are deleted"), so no committed document currently asserts
the wrong roads as delivered; recorded here only so a reader scanning
ERRATA for this tranche's shape of correction finds the pointer without
having to read all of `CHECKLIST.md` to discover it was already fixed
in place.

**E23 — E19's subject citation now resolves: the adjudication tranche
directory exists on main as of this merge.** E19 recorded
`GATES_AND_PACKAGES_PREPLAN.md:4-5` citing
`experiments/2026-08-09-change-adjudication-judge-seats-optins/` when no
such directory was readable from main, with a merge-time note that the
directory was executing on the then-unmerged branch. That branch merged
to main 2026-08-11 (this commit); the directory and its
REQUEST/SPEC/CHECKLIST/VALIDATION/DELIVERY artifacts are now in the
committed tree, so the preplan's citation is no longer dangling. What
stands from E19: the preplan cited the tranche before it was readable
from main, and E19's own "planned but never opened" inference was wrong
when written. No document edit needed; recorded per the operator's
instruction to update this ledger at the adjudication merge.

**E24 — `dr-drive-harness/SKILL.md`'s "never generalize instruction
scope" rule is an accepted, permanent exception to `authoring-skills`'s
own W3 ("each surviving 'never' must be enforced by a GATE").** The
2026-08-12 skills-overhaul census (`experiments/2026-08-12-change-
skills-overhaul/CENSUS.md`, `dr-drive-harness-36`) flagged this rule —
"Never generalize an instruction beyond its stated scope; if a spec
seems silent about your case, that is a question... not an invitation
to infer" — as the one negation in the whole `.claude/skills/` set with
no mechanical trigger. `DESIGN.md`'s gate table recorded the gap
honestly rather than building an unproven check to close it, and parked
the choice (`PARKED.md` P1): a new lint-style checker comparing an
agent's stated scope against files touched, or an operator-accepted
judgment-only status. The operator's answer, 2026-08-12: "judgement
only and approved to continue." Reason recorded in
`experiments/2026-08-12-change-skills-parked-followups/SPEC.md`
(Q1): a mechanical scope-checker would need the same judgment it is
meant to replace, and would likely have flagged the skills-overhaul
tranche's own DELTA edits as false positives (each touched more files
than the single one named in its own CHECKLIST step, for good reason).
No document is wrong here — this entry exists so a future reader
auditing the set against `authoring-skills`'s W3 finds the accepted
exception on record, rather than re-discovering and re-litigating it.

**E25 — README's "`deepreason amend` adds to a stopped run" was true of
managed runs only; a run stopped by `deepreason run --run-manifest` could
not be amended at all.** The claim (`README.md`, "Changing the question,
or adding evidence, after a run has stopped") described the operation
correctly and the precondition correctly two paragraphs later — "`amend`
refuses, with a typed reason, unless the run is standing at a real
terminal stop" — but nothing said that whether a stopped run *had* such a
stop depended on which launch path started it. It did. The managed
`TEXT_RUN_SERVICE` path wrote the terminal records at stop; the bare
`deepreason run --run-manifest` path called the scheduler and printed.
Grounded-extension run `8e22d0431fd2b98d`
(`experiments/2026-08-12-live-grounded-extension-expansion`) completed 24
real cycles that way and refused `AMEND_NOT_AT_TERMINAL`,
`CONTINUE_STOP_REQUIRED` and `RUN_RESULT_NOT_READY` — terminal authority
never left `current_open_uncommitted`. The census behind this entry
(`experiments/2026-08-13-change-lifecycle-operation-parity`, CHECKLIST
step 16) found no committed document that stated the launch-path
dependency and none that denied it: the gap was silence, not a false
sentence, which is why it survived. **The claim is now true as written**
— both launch paths call one shared
`application/text_runs.py::terminalize_text_run`, and `deepreason
finalize` repairs a root stopped before the fix by appending. This entry
exists so a reader auditing that README sentence against the pre-2026-08-13
record finds the discrepancy explained rather than re-deriving it, and so
the newly-true state is on the ledger with the run that paid for it.
**E26 — two committed statements describe `terminalize_text_run` as the
sequence "both paths" call; after 2026-08-13 there is one path.** Neither
was false when written, which is exactly why an entry is owed rather than
a silent edit: a reader auditing them afterwards finds two launch paths
described where one exists, and has no way to tell whether the document
or the code moved. The two statements are `CLAUDE.md`'s operations-parity
law — "The mechanism is therefore ONE shared implementation both paths
call — `application/text_runs.py::terminalize_text_run` — never a copy,
because a copy is how the paths drifted in the first place" — and
`docs/map/CON-run-identity.md`'s row "`terminalize_text_run` (called by
`_worker` AND by `cli.main._execute_bound_run`)". Both were written by
`experiments/2026-08-13-change-lifecycle-operation-parity`, which fixed
the drift by making the two paths share the sequence. The SAME DAY,
`experiments/2026-08-13-change-single-run-path-unification` removed the
second path outright on the operator's instruction ("Why not retrofit the
newer reason path? Get rid of the old one. The new one has a lot of
machinery that needs to work every run."): `deepreason run --run-manifest`
keeps its exact parser surface and became a rendering shell over
`TextRunApplicationService.start_manifest_run`, and
`cli.main._execute_bound_run` was deleted with its bare-path retrofit
`attach_bound_evidence_once`. **What stands unchanged is the LAW** —
"The flags and operations available to the newer reason runs should be
available to all configurations" — and its reason; only its stated
mechanism moved, from parity-by-agreement to parity-by-construction. Both
documents were updated in the deleting commit, and both of their
`check:` lines were inverted to negations (`cli/main.py` must NOT name a
scheduler) so a reappearing second path fails the map gate rather than
merely contradicting its prose. Recorded per that tranche's R18: any
committed document describing the two-path split as permanent design, or
the bare path as lifecycle-complete, earns an entry.
**E27 — `docs/map/SEAM-harness-x-workflow.md`'s "Fifty-seven files
under `src/deepreason` name both sides" was already one behind its own
`check:` before this correction touched it.** The prose said 57 while
the executable check on the very next line pinned 58, so one of the two
had been stale since some earlier commit and nothing forced them to
agree — a `check:` authenticates the CLAIM it guards, not the sentence
beside it, and here the sentence and the check were two different
claims. Found 2026-08-13 by the results-retrieval tranche
(`experiments/2026-08-13-change-results-retrieval-surface/`), whose new
reader `src/deepreason/application/results.py` legitimately names both
sides (it imports `deepreason.harness` for a read-only open and
`deepreason.workflow.lifecycle` for `RESUMABLE_STOP_REASONS`) and so
moved the true count to 59. Both prose and check now read 59, and the
count was re-derived rather than incremented. Nothing about the seam's
AGREEMENT changed; only its population census did. The general lesson,
recorded because it will recur: a prose number beside a pinned number
is a second, unguarded copy — when you move one, re-derive the other
rather than trusting it.
(Renumbering note, added at merge: minted as "E25" on its delivery
branch, colliding with the unification tranche's E25; serialized in
merge order per this ledger's convention.)
**E28 — `docs/CONTROLLER_SPEC.md`'s "Does it work? Yes, on what it
controls" was proven only on a cap that happened to lie INSIDE the
static envelope, and has been read ever since as evidence that the
controller steers real runs.** The 2026-07-05 live A/B starved
`cap:conjecturer` to **1200** — comfortably inside that knob's static
barrier of `[800, 5000]` — and the controller duly widened it 1200 →
1920 → 3072. That result is real and the spec's report of it is
accurate. What it does not license is the belief the sentence invites:
that the mechanism runs "automatically, with no human" on the runs the
harness actually launches. A compiled v6 manifest pins
`max_tokens=16384` on every role it binds, which was outside every
static ceiling in the table, so `_propose` skipped every knob in
silence and the controller had authority over nothing. Measured on the
committed record, not inferred: grounded-extension run
`8e22d0431fd2b98d` carries 12,991 events with zero steering artifacts,
and **zero of the 104 committed logs in `experiments/` contain a
controller policy body at all** — in the whole recorded history of this
repo the controller has never once steered a real run. Two further
sentences in the same section are corrected by the same finding: "the
savings direction (narrowing wasteful caps...) lives in the deferred
half" is wrong about the code — the narrowing branch IS implemented
(`_clean_streak` + `CLEAN_WINDOWS`) and simply never reached a knob it
was allowed to move; and the A/B's framing of the controller as "not
yet a token saver" was measured on a starved 1200-token cap, the one
configuration where saving is impossible. The savings were sitting in
plain sight in the other direction: that same grounded root pinned
`judge` at 16,384 for 342 calls whose largest completion was **141
tokens**. Found and fixed 2026-08-13 by
`experiments/2026-08-13-defect-controller-steering-inert/`; the barrier
is now derived per run from the cap the manifest assigned each role,
and a controller that cannot steer something says so in a typed
`controller-authority` record instead of returning `None`. The general
lesson, recorded because it is the reusable half: an A/B that fixes the
one parameter which gates the mechanism proves the mechanism works
*where it was already allowed to act*, and says nothing about whether
it is ever allowed to act. State the configuration a live result was
measured under, in the sentence that reports the result.
**E29 — `docs/harness-spec-v1.3.md` §3's spawn-trigger list ("failed
verdict ⇒ successor problem (P2)") and §7's dependent sentence are both
FALSE as of the v2 program's Rung 3a.** The trigger is deleted: no failed
verdict mints a problem, and `rules/spawn.py::scan_spawns` no longer
contains the branch. §7's sentence is the load-bearing casualty — "No
bespoke sharpen-or-drop: the failed verdict already Spawns a successor
problem (P2) — sharpening is the successor's job" JUSTIFIED the absence
of a sharpen-or-drop rule by pointing at the very trigger H1 removes, so
deleting the trigger without re-founding that justification would leave
a gap the spec still claims is filled. It is re-founded on two things
that do exist: the premise channel (a problem's presupposition is
criticisable, and a marked problem's three resolutions include
*translate*, which is now the only path from one problem to another),
and discrimination (two surviving rivals still spawn the comparison).
Neither fires on a refutation, which is the whole content of H1: failure
redirects ATTENTION, it does not spawn. Found and fixed 2026-08-15 by
`experiments/2026-08-15-change-rung3a-h1-successor-deletion/`. The
general lesson, recorded because it is the reusable half: when deleting
a mechanism, grep for the sentences that CITE it as a reason for
something else's absence — those are the claims that quietly become
unsupported, and they are never in the same section as the deletion.
**E30 — `docs/COMPUTABLE_CALCULUS.md` §5's trigger list, stated as
"exhaustive", and §9.6's "The failed verdict spawns a successor problem
as always" are deliberately NOT implemented.** Not contradicted by
another document but by the operator's own H1 decision, which predates
this program and was pre-decided rather than derived. The calculus is
committed theory authority in this repository, so a reader must be told
that two of its sentences are knowingly unimplemented and why: a
successor minted from a failure is a problem nobody posed, carrying its
parent's criteria under a new id, and one recorded run reached 2,894
problems that way. §9.6's clause also had a second life — it minted the
CRISIS problem under a consulted frame assertion — and that half is
answered separately by `DECISIONS.md` D-1 (crisis is a render state
only, no standing-layer trigger). Minted 2026-08-15 by the same tranche.
The `SpawnTrigger.SUCCESSOR` enum member survives the deletion and is
not evidence against this entry: a live producer outside the reasoning
loop still stamps it (`easy.py::seed_component`, staged-pipeline
component repair), and whether H1 reaches that site is an open operator
question.

## 2026-08-16 (website-remnant close-out)

**E31 — E30's own closing paragraph is FALSE as of Rung 3d, and two code
comments carried the same claim.** E30 recorded that `SpawnTrigger.SUCCESSOR`
survives H1's deletion because "a live producer outside the reasoning loop
still stamps it (`easy.py::seed_component`, staged-pipeline component repair),
and whether H1 reaches that site is an open operator question". The operator
closed that question in ADDENDUM v2 (v2 program `REQUEST.md` Amendment 9, R66):
the staged pipeline was already decommissioned, so the producer was a remnant,
and Rung 3d removed it. `seed_component` now stamps `{"trigger": "seed"}` on
both branches (`src/deepreason/easy.py:753-756`), and no source file mints a
successor problem — asserted by
`tests/test_decommissioned_pipeline_stays_out.py::test_no_source_file_produces_a_successor_problem`.
The enum member is retained as INERT VOCABULARY so pre-v2 roots still parse on
replay; retention is not a producer claim. E30's substance stands — the
calculus's successor sentences remain deliberately unimplemented — only its
rationale for the member's survival is superseded. The same stale claim was
carried in two comments and is corrected in this tranche's commit:
`src/deepreason/ontology/problem.py`'s `SUCCESSOR` block ("the member stays
because a LIVE producer still uses it") and `easy.py::seed_component`'s
docstring ("A repair problem ... is a SUCCESSOR spawned from the implicated
component artifact"). `docs/map/SUB-rules.md:193-194` was already corrected at
Rung 3d and is not affected. The general lesson, recorded because it is the
reusable half: an entry that explains why something SURVIVED a deletion is
dated by the survival, not by the deletion — when the surviving reason is later
removed, the entry becomes the last place the dead reason is still asserted,
and nothing about the removing tranche points at it.

**E31b — the manifest-sha attribution scan (the tranche's stated errata
checkpoint) found nothing to correct.** `04da6c65f`'s report attributed two
`test_single_run_path.py` failures to the container ("why the grounded-manifest
builder returns a different sha in this container now"); `395668544` self-
corrected that in its own commit message and in `VALIDATION.md`/`PARKED.md`,
which name the real cause — the builder's evidence dossier digests
`docs/map/SUB-adjudication.md`, so editing it moved a content address. No
committed DOCUMENT carries the superseded attribution; it survives only in
immutable commit messages that the correcting commit answers directly. The
correction is confirmed by construction on a fresh container: see
`experiments/2026-08-15-change-rung3d-website-remnant/VALIDATION.md`, close-out
section.

## 2026-08-16 (manifest-sha / doc-coupling close-out)

**E32 — "the manifest digest is a pure function of the compiled
configuration" was false, and a committed parked prompt recommended a road
built on it.** `tests/test_single_run_path.py`'s
`test_run_identity_is_deterministic_through_the_one_road` docstring stated
that the manifest digest is a pure function of the compiled configuration.
It is a function of the compiled configuration AND the evidence that
configuration binds: dossier bytes → `evidence_dossier_digest` →
`run_input_digest` → `manifest.sha256`, and the grounded-extension
configuration binds six local documents, two of them under `docs/map/`.
That sentence is why the same failure was diagnosed twice as something
else — a deleted `SpawnTrigger.SUCCESSOR` enum, then a container/build
cache — since a digest believed to depend on code alone cannot move when
only a document moves, so something else always had to be blamed. Both
prior readings were already falsified on record (`d52c739ff`; E31b);
`experiments/2026-08-16-defect-manifest-sha-doc-coupling` settles the
positive claim with an A/B probe — editing a bound dossier document moves
all three digests together, editing a map document outside the dossier
moves none — and corrects the docstring in the same commit.

Also corrected: `experiments/2026-08-15-change-rung3d-website-remnant/PARKED.md`'s
ready-to-send prompt offered as its preferred road (a) "freeze the dossier
by copying those bytes into the tranche directory", which would edit
`experiments/2026-08-12-live-grounded-extension-expansion/build_manifest.py`
— a committed live tranche's own compile script — and leave it disagreeing
with the `evidence-dossier.json` it produced. Superseded by an APPENDED
addendum in that file (the prompt itself is left verbatim, per the
append-don't-rewrite rule); the freeze belongs in the test's `tmp_path`.
That prompt's cache framing is NOT among the corrections: it already said
the cache hypothesis was refuted, and it was right.

The general lesson: a digest's docstring must name every input class the
digest covers, because the omitted class is the one a future reader will
rule out first. "Pure function of X" invites exactly one diagnosis when the
digest moves and X did not — look for corruption — and forbids the correct
one, which is that some Y is also an input.

## 2026-08-16 (all-configs completion)

**E33 — "compile-time denial abolished" was a title claiming a completion
its own body denies.** `experiments/2026-08-12-change-all-configs-allowed/
DELIVERY.md`'s heading reads "Delivered: all configurations are allowed —
compile-time denial abolished". That document's own "What changed" section
states the opposite three paragraphs later: "roughly 60 sites total: the
~13 converted above, and ~20 more fully designed but intentionally left for
a follow-on tranche (SPEC.md §3, PARKED.md P1)". The body is accurate; the
heading is not, and a reader scanning tranche titles — which is how the
tranche index is read — would conclude the law was fully delivered on
2026-08-12 and that the parked remainder did not exist.

The claim is TRUE as of 2026-08-16, not 2026-08-12. The remaining sites
were converted in `experiments/2026-08-16-change-configs-complete-seats-
test/`, whose CENSUS.md holds the before/after evidence per site
(`census-before.txt`: 20 sites still refusing and 1 crashing untyped on
main at `5f648ebc9`; `census-after.txt`: all 21 compiling).

Not corrected in place: the 2026-08-12 DELIVERY.md is a delivered tranche
artifact and is left verbatim, per the append-don't-rewrite rule. This
entry is the correction.

The general lesson: a tranche heading is a claim, and it is the claim most
readers will act on. When a tranche knowingly ships a subset, the heading
says so — "a tier-1 subset of" costs four words and saves the next reader
from believing a park does not exist.

## 2026-08-21 (wheel-smoke reason-stage tranche)

**E34 — the wheel operational smoke's `reason`-stage failure was recorded as
FLAKY; it was deterministic, and the "pass" observation never evaluated the
assertion.** `experiments/2026-08-16-change-embedder-auto-install/
CHECKLIST.md` step 21 concludes "Across three observations of this stage on
this container — my run 1 (passed), my run 2 (failed), base (failed) — the
`reason` stage is FLAKY here", and `PARKED.md` P1 carries the same claim
("Observed 3 times on this container at that stage — passed once, failed
twice"), as does `experiments/2026-08-16-change-configs-complete-seats-test/`
CHECKLIST S13 / REQUEST.md §3, which call it "the parked pre-existing flake".

Run 1 did not pass `_assert_resumable_terminal`. It aborted at
`scripts/wheel_operational_smoke.py:3447` (`AssertionError: durable CLI
result changed when retrieved through MCP`), and that line lies inside
`STAGE_MCP_REQUEST` — `stage = STAGE_MCP_REQUEST` at line 3435, next
transition at line 3461 — which the smoke reaches BEFORE
`_assert_resumable_terminal` at line 3565. Run 1 is silent about the
assertion, not a pass. Step 21's own text records the two failures were "at
the same stage", which is true of the STAGE LABEL and false of the
assertions: four separate sub-stages of the smoke all set `stage =
STAGE_REASON`, so the failure envelope's `"stage":"reason"` does not identify
which one ran.

The failure was deterministic from `a476c564f` (2026-08-15), which added
`Scheduler._premise_rent_step` and its unconditional per-cycle deferral.
Every evaluation of the assertion on a tree at or after that commit has
failed: the prior tranche's run 2, its clean-worktree base run at
`d52c739ff`, and two runs on `c7e605553` in this tranche. Diagnosis and
mechanism: `experiments/2026-08-21-fix-wheel-smoke-reason-stage/DIAGNOSIS.md`;
evidence root `run-e9d4bb16796b8aa4b560c632b33d6500`.

Not corrected in place: both 2026-08-16 tranches are delivered artifacts and
are left verbatim, per the append-don't-rewrite rule. Nothing those tranches
CONCLUDED changes — the failure was pre-existing and correctly parked, and
the embedder tranche's own ONNX-non-determinism hypothesis was already
refuted in its own record. Only the word "flaky" is wrong.

The general lesson, and the reason this is worth an entry rather than a
shrug: a stage NAME in a failure envelope is not an assertion identity. When
one label covers several assertions, "it failed at stage X twice and passed
once" is not evidence of non-determinism until you have checked that the
passing run reached the same assertion. Reading it as flakiness turns a
one-line deterministic bug into a race hunt.

## 2026-08-21 (Rung 3b, frame-separation)

**E35 — `docs/COMPUTABLE_CALCULUS.md` Proposition 9.6's proof is incomplete,
and Law 9.4's "this single interface constraint is the whole separation of
the axes" is false as stated.** Prop 9.6 reads: "the attack targets b; fa
carries no dependence on b (Law 9.4), so Pass 2 leaves fa's label untouched;
the renderer keys on final(fa). ∎". The proof discharges PASS 2 only. Pass 1
— the grounded attack pass — can move `fa`'s label with no dependence on `b`
whatever, whenever `fa` and `b` sit in the same connected component of
`att ∪ dep`: a new attack on `b` then reaches `fa` through pre-existing
paths. `docs/POIETIC_CALCULUS_FORMALIZED.md` §7 already says so in prose
("The source document's mention law is necessary but not sufficient for this
theorem") and supplies the missing hypothesis as Definition 7.2, the
frame-separation invariant. This entry exists because a reader of
`COMPUTABLE_CALCULUS.md` §9 has no pointer from the wrong proof to the
correction, and §9 is the section a frame-layer implementer reads.

The gap is now EXECUTABLE rather than only argued:
`tests/test_calculus_frame_separation.py::test_a_reach_case_that_depends_on_the_subject_is_unconsultable`
builds a graph in which Law 9.4 is fully obeyed — the assertion `mention`s
its subject and carries no dependence on it — and separation fails anyway,
because a record the assertion depends on depends on the subject. Mention and
separation are independent conditions; the first does not imply the second.
Found and demonstrated 2026-08-21 by
`experiments/2026-08-21-change-rung3b-frame-separation/`.

Not corrected in place: `COMPUTABLE_CALCULUS.md` is committed theory
authority and is left verbatim per the append-don't-rewrite rule. What Prop
9.6 CONCLUDES survives — a wound really does leave standing untouched — but
only under the added hypothesis, which is why Rung 3b ships the hypothesis
before Rung 4 ships the frame layer that would otherwise violate it.

The general lesson: a proof that discharges one of two passes reads exactly
like a proof that discharges both. When a status semantics has more than one
pass, a persistence argument names every pass or it is incomplete — and the
missing one will be the pass that needs a GRAPH condition rather than an
interface constraint, because interface constraints are the ones authors
think to write down.

**E36 — `docs/map/INV-frozen-surfaces.md`'s "The governing principle" still
states the law CLAUDE.md retired on 2026-08-14.** The document opens with:

> The append-only record itself: fix READERS so old roots stay valid; a change
> that invalidates existing replay-valid roots is wrong by definition.

CLAUDE.md's operator law "Old runs owe the future nothing; new versions
optimise for new functions" quotes that exact sentence and marks it
**SUPERSEDED**: "new versions owe old roots neither validity nor readability,
and no tranche owes a replay-byte-unchanged proof over historical roots
anymore." The same section of `INV-frozen-surfaces.md` also still calls the
42-root sweep "the instrument" for measuring the difference, while
`experiments/2026-08-14-change-calculus-reconciliation-v2/LADDER.md` §2
removed it as a gate obligation and §4 reclassifies replay-validation formats
as "free to change shape".

Two committed documents therefore give opposite answers to "may I change this
format?", and the one a reader is told to open FIRST (`dr-drive-harness` §4,
"`INV-frozen-surfaces.md` — **first, always**") is the one carrying the
retired law. CLAUDE.md wins: it is where operator law lives.

The scope boundary the retired law did NOT touch, restated so this entry is
not over-read: a CURRENT-version run's record stays typed, append-only, and
replayable by the code that wrote it. Within-version integrity is the
epistemology and is untouched.

Found while reading `INV-frozen-surfaces.md` at the map preflight of
`experiments/2026-08-21-change-rung3b-frame-separation/`. Not corrected in
place — that rung's scope is one invariant and a defect found mid-change is
parked, not fixed (`PARKED.md` P3 carries the ready-to-send prompt).

## 2026-08-22 (Rung 1b-ii, signal consumption)

**E37 — "the 42-root sweep" names a root count that has been wrong for
weeks; the sweep covers 107.** `CLAUDE.md` ("The 42-root sweep obeys the
same rule for the same reason"), `docs/map/INV-frozen-surfaces.md`,
`SEAM-evaluation-x-rules.md`, `SEAM-harness-x-verification.md` and
`SEAM-harness-x-workflow.md` all name the instrument by a fixed count of
42. `tools/root_sweep.py` takes no such number: it sweeps
`{p.parent for p in pathlib.Path("experiments").rglob("log.jsonl")}`,
which is **107** as of this commit, and grows every time a tranche
commits a root. Measured, not inferred — this tranche ran the sweep twice
and both passes wrote 107 rows
(`experiments/2026-08-21-change-rung1b-ii-signal-consumption/proof/`).
The number matters because it is quoted to price the instrument: a reader
budgeting for "42 roots" budgets for well under half the real cost, which
in this tranche was about 100 minutes per pass. This is the same failure
mode E27 recorded in its own general lesson — "a prose number beside a
pinned number is a second, unguarded copy" — except here the second copy
is beside a value nothing pins at all, so nothing could catch it drifting.
Not corrected in place: the operator retired the instrument itself on
2026-08-22 ("root sweep needs removal. It doesn't matter whether old
records still verify"), so every sentence carrying the wrong number is due
for deletion rather than repair. Recorded here so that nobody re-trusts
"42" in the interval, and so the removal tranche has the census
(`experiments/2026-08-21-change-rung1b-ii-signal-consumption/PARKED.md`
P4 lists all 50 live references).

**E38 — `tools/blast_radius.py` reports `frozen_surface_verdict: CONTACT`
for changes that touch no frozen surface, and will do so for every future
controller tranche.** Its `SYMBOL_INDIRECT` tier is decided by grep, so a
declared target symbol contacts a frozen surface whenever its NAME appears
in that surface's file. `Controller`, `cap_envelope` and
`is_generator_knob` all appear inside `src/deepreason/invariants.py`, so
any tranche declaring one of them stops at `dr-spec-change`'s mandatory
operator STOP whether or not it intends to touch that file. Worse, the
match is on substrings of unrelated identifiers: this tranche's gate run
reported `manifest schemas and validators (run_manifest.py)` contact for
the symbol `clamp`, where every `clamp` in that file is
`clamp_reserved_attention_fractions` / `_reserved_fractions_are_clamped`,
imported from `deepreason.config` and unrelated to `controller.clamp`. The
tool is not lying — each detail string says "grep-based; not proof of
semantic contact" — and the disclosure is deliberately over-wide by
design. But the cost is real and lands on every controller tranche, and an
alarm that always fires informs nobody. Whether to resolve the symbol
before claiming contact is an operator decision about disclosure, not an
implementation detail, so nothing was changed:
`experiments/2026-08-21-change-rung1b-ii-signal-consumption/PARKED.md` P2
carries the ready-to-send prompt and the measured evidence.

**E39 — `LADDER.md`'s per-rung line estimates are systematically low, and
Rungs 5–8 carry estimates produced the same way.** Rung 4 estimated
500–700 lines; the delivered tranche is 2 290 insertions over `src`,
`tests`, `docs/map` and `scripts`, and needed its ceiling raised twice
mid-flight (963 → 1 850 → still exceeded at 2 290). The work did not
grow — every line traces to a numbered requirement and no later rung's
machinery is present — so the error is in the estimating method, and it
has a measurable shape worth stating because it will recur:

1. **New modules were priced at about half what existing modules in the
   same package already run at.** `calculus/scope.py` was estimated at 85
   and landed at 190; `calculus/standing.py` at 110 and landed at 248. The
   existing `calculus/` modules average ~93 lines for far less behaviour,
   at the docstring density CLAUDE.md's Conventions ask for. The line
   count of the neighbouring modules is measurable before writing
   anything, and was not measured.
2. **A mandated multi-proof gate was priced at the size of a smaller
   one.** Rung 4's gate carries seven named propositions across 34 tests
   (983 lines); the estimate of 290 was scaled from Rung 3b's two-proof
   gate (82 lines) without scaling for the proof count.
3. **New map documents were priced from a guess.** Rung 3b's own SPEC
   estimated the axiom document at "~60 extra lines" and Rung 4's at ~95;
   `INV-axiom-basis.md` landed at 259, because eleven axioms each need a
   statement, a proving rung, a preservation list and a check that can
   fail — plus an explanation for each row that must NOT yet carry one.

Not corrected in place: revising Rungs 5–8's numbers now would be
replacing one guess with another. What is recorded instead is the method
that would produce a defensible figure — measure the neighbouring
modules, scale the gate by proof count, and price a map document per row
— so the next rung's SPEC can be checked against something. Evidence:
`experiments/2026-08-22-change-rung4-frame-assertions/` REQUEST.md
Amendments 1 and 3 and VALIDATION.md's ceiling section.

**E40 — E38's grep-based frozen-surface false positive recurred, on a
second symbol, in the next tranche that ran the gate.** E38 recorded
`clamp` matching `clamp_reserved_attention_fractions` inside
`run_manifest.py`. Rung 4's boundary run reproduced the same shape with
`consulted`: `tools/blast_radius.py` reported `manifest schemas and
validators (run_manifest.py)` contact and a `PLAUSIBLE`
qualification-digest consumer, where all three hits are English prose in
comments predating the tranche ("consulted at mint sites", "consulted at
scheduler dispatch sites", "is consulted"), the file has a zero-line
diff, and it imports nothing from `deepreason.calculus`. Recorded as a
SECOND measured instance rather than a repeat complaint, because E38's
open question is whether the cost justifies resolving the symbol before
claiming contact, and one instance is an anecdote while two on unrelated
symbols in consecutive tranches is a rate. Disposal method is unchanged
and is the one `INV-frozen-surfaces` already models for `clamp`: measure
the diff, grep the hits, scan the imports, and record the disposal — never
wave it away. The prompt remains
`experiments/2026-08-21-change-rung1b-ii-signal-consumption/PARKED.md` P2.

## 2026-08-22 (reach structural-set fix)

**E41 — a map Traps entry named one consumer of a defect that had two, and
called "not an observed live failure" the one thing that was blocking every
text run.** `docs/map/SEAM-evaluation-x-rules.md` Traps recorded the
`_STRUCTURAL_PROGRAMS`-vs-`ProgramSpec.class_` divergence correctly and even
carried a check that would fail when it was closed. But it scoped the
consequence to ONE consumer — "structural to the anti-relapse gate … and
SUBSTANTIVE to `formally_backed` (a passing one confers prose immunity)" —
and `measures/reach.py::reach_sweep` reads the same `_substantive` predicate.
The entry's recorded residue then read: "this is a code-reading finding at the
predicate level, not an observed live failure." On the `formally_backed` side
that was right and stayed right —
`experiments/2026-08-21-measure-reach-firing/probe_immunity.json` measures
`backed_only_by_declared_structural` at 0 over 3 528 candidate artifacts,
re-measured unchanged at 903 `formally_backed` per root before and after the
fix. On the REACH side it was wrong, and wrong in the opposite direction from
the one the entry anticipated: a qualifying criterion must PASS for a hit, and
`reasoning-envelope-wf` fails on prose by construction, so counting it
substantive VETOED hits rather than manufacturing them. It was the single
reason no current-version root ever recorded a reach event
(`experiments/2026-08-21-measure-reach-firing/census.json`: 0 `reach_set`
events on 96 roots; `experiments/2026-08-22-live-reach-rich-run/rehearsal.json`
S8a/S8b). A permissive-looking misclassification had a restrictive effect
because the same predicate gates two directions.

Corrected 2026-08-22 by tranche
`experiments/2026-08-22-reach-structural-programs-fix` (commit `7b82206dc`):
the Traps entry is rewritten to name both consumers and both discharged
residues, and its check is inverted from asserting the divergence to asserting
the agreement. Recorded here rather than only in the map because the mistake
is reusable: when a shared predicate has more than one consumer, the blast
radius is the union of them, and a Traps entry that lists one reads as if it
listed all.

## 2026-08-22 (repair patch transport tranche)

**E42 — a parked finding read every converging repair as an off-target patch,
because the census asked the wrong record for the authority.**
`experiments/2026-08-22-live-reach-rich-run/PARKED.md` P7-reach recorded that
the reach-rich epoch-1 conjecturer seat "returned a well-formed patch addressed
to a pointer OUTSIDE the authorized set, and both are the SIBLING INDEX of the
authorized one", citing the diagnostic envelope `blobs/11/11659d8c…`
(`authorized_pointers ["/candidate/checker_specs/1/id"]`) against the raw
provider output `blobs/9b/9b29d126…`
(`{"op":"remove","path":"/candidate/checker_specs/0/terms"}`).

Both blobs are quoted correctly. The pairing is not. `blobs/11/11659d8c…` is
not the envelope that turn was dispatched under; it is the diagnostic derived
AFTER the patch was applied. `workflow/repair_transaction.py::_terminalize_invalid`
writes a repair attempt's `diagnostic_ref` as `trace_ref or next_diagnostic_ref`,
so a census keyed on that field compares attempt N's response with attempt N+1's
authority. A convergent repair moves the pointer on by construction, so every
convergent repair scores off-target.

The authority frozen before issue is the work preparation's
`repair.semantic-task.v1` payload. Read from there, the dispatched envelope for
that turn (`blobs/43/433c086d…`) authorizes exactly
`/candidate/checker_specs/0/terms` — the pointer the seat patched. Two
independent confirmations that `11659d8c…` is post-patch: its `baseline_sha256`
differs from the payload's (`1a478807191f3af7…`), and its `frozen_subtree_hashes`
no longer list `/candidate/checker_specs/0/terms`, the subtree just removed.

**Corrected reading:** all 13 repair turns of `run-40e713b30a147dfc` patched a
pointer inside their own authorized set; the run recorded ZERO off-target
patches (`experiments/2026-08-22-fix-repair-patch-transport/repair-turn-census.json`,
re-derivable by `repair_turn_census.py`). The seat exhausted because six
responses were unreadable at the wire on transport SPELLING, and a discarded
response still consumes a grant. P7-reach's remaining content stands: it is not
the ledgered glm-5.2 cap-burn (0 of 41 attempts had zero completion tokens),
and raising the completion cap remains the wrong remedy.

Fixed 2026-08-22 by tranche `experiments/2026-08-22-fix-repair-patch-transport`
(commit `97a964583`). Recorded here rather than only in the map because the
mistake is reusable: a record field named for a diagnostic does not say WHEN
that diagnostic was derived, and in an append-only log the cheapest way to be
wrong about causation is to join on the convenient key instead of the frozen
one.

---

## 2026-08-22 (route lease vs controller-tuned max_tokens)

**E43 — the map promised a bound the controller did not have.**
`docs/map/SUB-scheduler.md`'s controller Traps entry, recording the
2026-08-13 steering-inert fix, said barriers are "anchored so a SEAT
INSTANCE's assigned cap may only WIDEN the barrier and the controller can
never move a cap past the operator's own setting." The first clause is true;
the second does not follow from it and was false. Because the anchor only
ever widens — `cap_envelope` computes `envelope["max"] = max(static_max,
configured_cap)` — a seat assigned a cap BELOW the static ceiling keeps a
barrier wider than its own route, and a truncation signal moves it past the
assigned limit. Measured, not reasoned: a seat leased at 3000 against
`cap:conjecturer`'s static 5000 is widened to `round(3000 * 1.6) = 4800`
(`experiments/2026-08-22-fix-route-lease-maxtokens/repro.json`, case B).
The claim carried a check
(`test_every_manifest_bound_role_gets_a_barrier_containing_its_cap`) which
pins that the barrier CONTAINS the cap — a different assertion from the one
the prose made, which is how the sentence survived.

The mirror case is what surfaced it. Reach-rich epoch 2 (run
`40e713b30a147dfc1a0f73feb91fa67a493454f6103a452888b8e08713368c4c`,
`log.jsonl` seq 442 then 577) died on the NARROWING side: the controller
settled the conjecturer seat from its leased 32768 to 20480 — lawful under
every rule the controller answers to — and `EndpointLease.verify`, which
bound `max_tokens` for equality on any route declaring
`context_window_tokens`, refused the next dispatch and ended the run at cycle
2 of 24 with `stop_reason=operational_failure`.

Corrected 2026-08-22 by tranche
`experiments/2026-08-22-fix-route-lease-maxtokens` (commit `8469d0669`): the
Traps entry is rewritten in place — never deleted, per `SCHEMA.md` — to state
which clause was false, why, and that the promise holds from 2026-08-22 and
only for seats whose route declares `context_window_tokens`, where
`Controller._lease_ceiling` bounds the proposal at the lease.

Recorded here rather than only in the map because the mistake is reusable in
two ways. First: a claim can carry a passing check and still be false, when
the check pins a neighbouring assertion — "the barrier contains the cap" was
verified; "the controller cannot exceed the cap" was not, and only the second
was written down as the guarantee. Second: the same commit corrected a
comment in `src/deepreason/llm/firewall.py` that asserted the opposite of the
code six lines below it, and additionally described the controller's logging
as "Measure events" when the record shows a `Refl` policy artifact
(`objects/artifact/2e9009812fe9e3b6fd0b48ffd088d72d21bc09890ee21fd66f715bd8253cba52.json`).
Two documents and one comment each described this controller's authority, and
all three were wrong in a different direction.

**E44 — "a Config value costs nothing to add" omitted the step that makes it
true, and a signature is not a subject.** `docs/map/INV-frozen-surfaces.md`,
under "Where authority is allowed to live instead", said: "A `Config` value
costs nothing to add and is invisible to replay." Invisible to replay, yes.
Costs nothing, only if you also drop the key in
`run_manifest.py::_versioned_source_config_data` — because `Config` is
serialized into every manifest's `engine_config_json` and hashed into its
`source_config_hash`, both of which the qualification subject embeds. Eight
prior knobs are already in that drop list for exactly this reason
(`ENGAGED_CRITICISM_AUTHORITY`, `LEGACY_CRITICISM_ENABLED`,
`ADJUDICATION_STATUS_AUTHORITY_ENABLED`, `JUDGE_SEATS_ENABLED` and its two
throttles, `SCHOOL_SEATS_ENABLED`); the sentence never mentioned them, so a
reader who took it at face value would skip the step. Measured 2026-08-22 by
`experiments/2026-08-22-change-two-call-seat-protocol/`: without the drop, the
subject digest over a committed fixture moved from `b9038b84efdea313...` to
`a5d81e5d34f51635...` and the full gate went red in 40 places, 22 of them
frozen manifest goldens; with it, byte-identical and green. Corrected in place
per `SCHEMA.md`, with a check that fails if a `SPLIT_BUDGET_` key reaches
`engine_config_json`.

Recorded here rather than only in the map because the WAY it was got wrong
recurs, and because the first correction written for it was ALSO wrong. That
tranche's SPEC.md M9 ran `inspect.signature(qualification_subject_payload)`, saw
`(manifest, profile)` with no `Config` parameter, and inferred the price was
zero; the measurement was accurate and the inference was not, since the manifest
the signature DOES name is what carries `Config` in. Then, on measuring the
digest actually move, the same window wrote up "the price is one battery per
home" as an inherent cost — which was a description of a DEFECTIVE
implementation, not of the design. The full gate is what separated the two: a
before/after digest over a committed fixture told it something had moved, and
only the gate's 40 red goldens told it the move was avoidable. When the question
is "does X enter this digest", the admissible answer is a before/after digest
plus a payload diff plus the full gate — never a signature, a grep, or a digest
comparison alone.

---

**E45 — a blast-radius census classified per FILE, and two per-CHECK hits moved
under a wholesale "MUST NOT MOVE".**
`experiments/2026-08-22-change-rungd-proof-debt-localization/SPEC.md`'s
"Blast-radius census" table declared `src/deepreason/programs.py` as a target
and then classified every map document that references it in one row — "they
assert on `register_fail_warrant`'s existing behaviour, which S8 leaves
default-unchanged". Two of those documents assert nothing of the kind. They
carry EXACT-SET pins over `programs.evaluate`, and Rung D adds a member to each:
`SEAM-evaluation-x-ontology.md:54` pins every callee inside `evaluate`
(`derivation_manifest_wf` joins it), and `SUB-evaluation.md:85` pins every file
that CALLS `evaluate` (`proof_debt.py` joins it, because `receipt()` re-runs
kernel checks). Both went red at step 6 and were correctly updated in the same
commit as the code; the error is the classification, not the tree.

Recorded because the SHAPE recurs and this is its third instance in one program.
Rung 4's census predicted too narrowly; Rung 5's predicted nothing and missed a
test pinning "exactly one backend" — the exact state that rung existed to change
(`experiments/2026-08-14-change-calculus-reconciliation-v2/` PARKED P6). Both
times the full gate caught it three commits later than the census would have.
Here the map caught it one commit later.

The correctable lesson is narrower than "be more careful". `blast_radius.py`
reports consumers per TARGET — a file or a symbol — and a reader naturally
writes one classification per row it returns. But a map document can hold many
independent checks over the same file, and the ones that bite are exact-set pins
(`assert found == {...}`, `assert D[0] == [...]`), which move whenever a set
gains a member for any reason. **A census row that names a FILE must be expanded
to the CHECKS in that file before it is classified**, and any check containing
`==` against a literal set or list is EXPECTED TO MOVE by default unless the
change demonstrably adds no member. The same tranche also found two
architectural pins the census never looked at at all — `premises.py` must not
import the calculus substrate (`SUB-calculus.md:163`) and `rules/warrants.py`'s
top-level imports are pinned to `{deepreason.ontology}`
(`SEAM-evaluation-x-rules.md:39`) — both of which caught real first-draft
violations. Neither was weakened; both fixes are better code. But a census that
had enumerated checks rather than files would have predicted all four.

**E46 — three committed statements said this refusal meant the prompt changed;
it cannot mean that.** `WorkflowAuthorizationError("transactional reservation
bound differs from rendered request")` names the request, and two documents
glossed it the same way: `docs/map/SEAM-llm-x-workflow.md`'s "What breaks first"
list read *"(the prompt changed after issue)"*, and
`experiments/2026-08-22-change-epoch3-second-lineage/PARKED.md` P6-epoch3
described "the prompt-bound term computed over two different strings". None was
careless — the message invites exactly that reading — but the guard cannot fire
on the prompt. `DispatchAuthorizationBundleV1.verify_dispatch` compares the
bundle's `prompt_sha256` against the adapter's freshly rendered prompt at
`llm/adapter.py`, ahead of the reservation block, and raises `"dispatch differs
from its authorization bundle"` on any difference; equal digests are equal
bytes, equal bytes are an equal `conservative_prompt_bound`. Any run reaching
the bound guard has already proven its two prompt bounds equal. The divergence
was always the COMPLETION CAP: `preview_request` booked a route's ceiling while
`call` recomputed the cap from the endpoint's settled value. Corrected
2026-08-23 by `experiments/2026-08-23-fix-reservation-bound-authority/`, which
makes the cap a single consumed number, rewrites the seam's gloss and its
Traps entry, and widens the message itself to print both bounds and both
prompt bounds — so the next reader is told what disagreed instead of inferring
it. Recorded because the mistake is reusable: **an error message is not
evidence about its own cause**, and this one misdirected a map document and a
parked finding for a day.

**E47 — a parked finding's elimination was false, and the search that produced
it could not have succeeded.** `PARKED.md` P6-epoch3 ruled out a controller cap
re-tune as the cause of epoch-3 attempt 3's death — "no policy artifact
carrying a `knobs`/`cap:` entry exists in `log.jsonl`, and `max_tokens` appears
as `32768` and no other value across every object in the root", with a pasted
one-liner regexing `"max_tokens"\s*:\s*([0-9]+)` over the root. The policy
artifact exists. It is a content-addressed artifact under
`objects/artifact/` with `provenance.role: "controller"`, its body is an
`inline:` JSON **string** rather than a nested object, and it spells the value
`"cap:conjecturer": 20480` — never as a `max_tokens` field. So the regex was
looking for a shape the record does not use, and "32768 everywhere" was the
true answer to a question that could not have returned anything else. The
settled cap is what killed the run: booked `8333 + 32768 = 41101` against a
dispatched `8333 + 20480 = 28813`, a gap of 12288 that is exactly the
narrowing. Found 2026-08-23 by
`experiments/2026-08-23-fix-reservation-bound-authority/`, whose
`repro/attempt3_census.py` re-derives it from the committed root; P6-epoch3's
other elimination — no prompt drift between reserve and authorize, 50 of 50
`prompt_sha256` agreeing — stands, and E46 explains why it had to. Recorded because the failure mode generalises and
has now cost two tranches (see E42, where a census joined on the convenient key
rather than the frozen one): **a negative result from a search is only as
strong as the proof that the search could have found the thing.** A census over
typed records must enumerate the record types it means to cover and say which
it read, not pattern-match a field name across a directory tree.


**E48 — the ladder and the operator's brief both cite drift row S-5 for §12.2's
empirical-scope clause; S-5 is a different row.**
`experiments/2026-08-14-change-calculus-reconciliation-v2/LADDER.md`'s Rung 5
work list ends its demarcation paragraph with "for empirical scopes, at least
one commitment must be observation-valued (drift row S-5)", and the operator's
Rung 5 brief repeats the citation verbatim. `RECONCILIATION.md`'s **S-5** row
says something else entirely: "Def 9.3 standing is derived, never stored;
instrument standing is not a third value but a `bounded` validity". No row in
that table carries the observation-valued clause; it comes from the
Formalization's §12.2 closing sentence, which the same paragraph also names.
The OBLIGATION was never ambiguous and was implemented as stated — only the
pointer is wrong, which matters because a reader who follows it lands on a
requirement Rung 3 already discharged and may conclude the clause was already
done. Found 2026-08-24 by `experiments/2026-08-24-change-rung5-promotion-criteria/`
(SPEC.md A9), which reported the mismatch rather than resolving it, and shipped
against §12.2 directly:
`tests/test_promotion_criteria.py::test_an_empirical_scope_needs_an_observation_valued_commitment`.

**E49 — E45's census lesson recurred, one tranche later, in its own shape.**
E45 recorded a blast-radius census that classified per FILE where the hits were
per CHECK. `experiments/2026-08-24-change-rung5-promotion-criteria/SPEC.md`
repeated the family error from the other side: it declared the FILES it planned
to edit and not the SYMBOL its own spec item named as the mechanism.
`tools/blast_radius.py` reports `consumers` only for declared targets, so
`register_fail_warrant` — named in SPEC.md S9 as the one warrant constructor the
promotion sweep would mint through — never entered `--symbols`, and the three
call-site count pins in `SUB-rules.md`, `SEAM-adjudication-x-rules.md` and
`SEAM-evaluation-x-rules.md` went unpredicted. The full `docs_verify` at the
boundary caught all three, four commits later than the census would have. The
rule the two entries jointly support, stated so the third occurrence has
somewhere to have been prevented: **a census must enumerate every symbol a spec
item names as its mechanism, not only the files it plans to edit, and must
classify per CHECK rather than per file.** Recorded 2026-08-24 by the same
tranche, against itself.

**E50 — `DR-SUB-calculus` said "five of the nine names are DECLARED AND
UNBUILT" three paragraphs below its own check asserting there are four.**
`docs/map/SUB-calculus.md`'s "Why closed" section gave the unbuilt count as
five while the check in its "What it owns" section asserted
`len(missing) == 4`, and both were on the same page. With five implemented
of nine declared, four is right and five is wrong. The error was inert —
nothing branches on the prose — but it is the shape a reader is least
likely to catch, because the contradicting check is above the fold and
passes. Found 2026-08-24 by
`experiments/2026-08-24-change-rung6-frame-render-departures/` while
moving the same counts for the departure-declaration body, and fixed in
the same commit; the counts now read four of ten. The general rule, which
the same document's own `SCHEMA.md` already implies: **a count stated in
prose is a load-bearing claim and needs the check that would fail with
it** — an unchecked number beside a checked one decays silently and reads
as verified.

**E51 — `DR-SUB-verification` said the epistemic checks "are not `verify_root`
findings at all", and two of them are.** The row read: "the epistemic checks
(`adjudication-blindness`, `bridge-epistemic`, `bridge-grounding`,
`grounding-review`) are derived in `report.py` — they are not `verify_root`
findings at all, so reading `verify_root` alone tells you nothing about them."
It was true when written and stopped being true at Rung 4 (2026-08-22), which
emitted `standing-integrity` from `verify_root` INTO the epistemic channel;
Rung 7's `cascade-integrity` (2026-08-24) is the second. A reader who trusted
the row would have skipped `verify_root` while looking for exactly the finding
it carries.

The row's own check did not catch it, and the reason generalises: it pinned
`adjudication-blindness` by name — one member of a four-member set — and **a
check that names one member cannot notice the set growing.** The four names in
the prose were never checked against the four in the code at all. Found
2026-08-24 by `experiments/2026-08-24-change-rung7-wounds-falls-succession/`
while adding the second counterexample, and fixed in the same commit: the row
now states the split both ways and its new check asserts BOTH partitions of
`_EPISTEMIC_CHECKS` — those `verify_root` emits and those `report.py` derives —
so a third member cannot join either side unnoticed. Sibling of E50: a
membership claim in prose is load-bearing and needs the check that would fail
with it, and for a SET that check must be over the whole set.

---

## 2026-08-25 (Rung 8 — rent, the authority audit, the §14 diagnostics)

**E52 — `RECONCILIATION.md` routes five drift rows to "Rung 7"; four of them
are Rung 8's, and one of them really did land at Rung 7.** The v2 program's
drift table gives its dispositions as
`experiments/2026-08-14-change-calculus-reconciliation-v2/RECONCILIATION.md`
rows **S-7** ("adopt — Rung 7"), **S-17** ("adopt — Rung 7"), **S-21**
("adopt — Rung 7, as a replay program over the log"), **G-4** ("adapt — Rung 7
must extend the existing capture instruments"), **G-5** ("adopt — Rung 7") and
**P-10** ("Rung 7 adds the calculus's specific new instrument"). The same
program's `LADDER.md` opens its **Rung 8** section with "Discharges: S-7, S-17
(residual-domain authorship), S-21, G-4, G-5, T-7, P-10."

The record settles it. `experiments/2026-08-24-change-rung7-wounds-falls-
succession/DELIVERY.md` reconciles ten requirements — wounds, the second
cascade entry, batch translation offers, succession, anomaly conservation, and
Q2a–Q2d — and none of them is rent, the authority audit, or capture
integration. Those four (S-7, S-21, G-4, G-5, with P-10's new instrument) were
delivered 2026-08-25 by Rung 8. **S-17 is the exception and cuts the other
way:** anomaly conservation DID land at Rung 7 (that DELIVERY's R5), so the
`LADDER.md` Rung 8 header over-claims it.

Cause, and it is structural rather than careless: `RECONCILIATION.md`'s
disposition column was written when the program had SEVEN rungs.
`LADDER.md`'s own Correction 2 then split the spawn-trigger deletion into its
own rung and Amendment 2 inserted Rung 1b, shifting every later number by one.
The drift table was never re-numbered. Every row after the split reads one
rung early.

**Uncorrected in place, deliberately.** `RECONCILIATION.md` is a delivered
tranche's committed artifact and rewriting its disposition column would edit
the record of what was decided when. This entry is the correction, and the
authority for "which rung owes which row" is `LADDER.md` plus the delivering
tranche's own DELIVERY.md — never the drift table's rung numbers.

---

## 2026-08-25 (the workflow-call-pairing defect tranche)

**E53 — PARKED.md P1 framed the defect as a REPAIR defect and named two
suspects; the failing event is not a repair, and neither suspect was the
cause.** `experiments/2026-08-23-change-cycle-soak-instrument/PARKED.md` titles
P1 "a repair under transactional authorization leaves a record `verify_root`
rejects" and reasons: "`llm/adapter.py` already knows a repair cannot reuse an
authorization bundle — the branch immediately above the reservation-bound check
raises `WorkflowAuthorizationError("transactional repair requires a new
authorization bundle")` when `attempt != 0` under a dispatch authorization. In
the observed run that guard did not fire; the repair dispatched and the
resulting attempt record did not pair with its authorization. So either the
guard has a hole, or the pairing check and the guard disagree about what a
repaired attempt should look like."

Both disjuncts are false, and the record says so directly. The failing event's
attempt trace records `attempt: 0` with `transport_attempts: 4` — one authorized
semantic attempt whose TRANSPORT was retried inside the endpoint, never a second
authorized attempt. The clamp had nothing to fire at and has no hole. Nor do the
guard and the check disagree about repairs: the check's sixth agreement compared
`attempt.raw_ref` against `call.raw_ref` across two types that spell absence
differently (`None` vs `""`), which is false by construction for the whole
`outcome="transport_failure"` class whether a repair is anywhere in sight or not.
`--induce-repairs` was simply the shortest reachable route to a transport
failure, because the inducer makes the stub answer HTTP 500.

Cause, and it is worth keeping: the parking note reasoned from the FEATURE THAT
PRODUCED the witness (the repair inducer) rather than from the failing event's
own attempt trace. The trace was one field away — `attempt: 0` — and settles it.
This is the blob-first discipline (CLAUDE.md's cycle-0 invariant) applied to a
parked finding rather than to a run death: read the event before naming the
subsystem. The park itself was right to refuse a diagnosis it had not earned;
what drifted was the hypothesis it volunteered alongside.

Uncorrected in place: P1 is a delivered tranche's committed artifact. Its
disposition is recorded at that file's own P1 resolution line and in
`experiments/2026-08-25-defect-workflow-call-pairing/DIAGNOSIS.md`.

**E54 — `scripts/cycle_soak.py`'s `EXPECTED_RED` claimed a fix was still in
flight nine days after it landed.** The entry read: "A parallel window is fixing
the reservation-bound seam in `llm/adapter.py:1400`. This soak DRIVES that code;
it does not modify it." That window delivered as
`experiments/2026-08-23-fix-reservation-bound-authority/`, and the soak has been
reporting `[PASS] D4-reservation-bound` since; PARKED.md P2's own ready-to-send
prompt instructed whoever cleared it to "delete the D4-reservation-bound entry
from EXPECTED_RED in the same commit — an expected-red seam nobody clears is
indistinguishable from a seam nobody fixed, and the soak's exit 3 stops meaning
anything." It was not deleted. Removed 2026-08-25 by the tranche above; the map
is now empty, which makes exit 3 unreachable rather than merely unearned. The
general lesson is the one P2 already wrote down and that nothing enforced: an
expected-red carve-out needs an owner AND a deletion step in the fixing
tranche's own checklist, because the carve-out silently outlives its reason.

## 2026-08-26 (F3 — channels on by default, and the wander cap)

**E57 (renumbered at merge from E54; that number was taken same-day) — `DR-SEAM-llm-x-scheduler` documented the allocation seam as a
two-party agreement and left out the party that CONSUMES it; the omission is
what let 47 controller decisions reach nothing while the document read as
complete.** That seam was written after run `40e713b30a147dfc` died, and it
was written around the failure in front of it: the controller PROPOSES a
completion cap, the route firewall REFUSES an inadmissible one, and the
document's "Where it is expressed" table names both sides plus the envelope,
the licence, the ceiling and the barrier. Every row is accurate. None of them
is the row that decides whether a decision reaches a dispatch at all, which is
`Adapter._completion_cap` — the one reader of the field `Controller._apply_cap`
writes.

Between 2026-08-23 and 2026-08-26 that reader returned the ROUTE CEILING on
every route declaring qualified capacity, so the settled cap was unreachable.
The two components went on agreeing perfectly about a field neither end
consumed. W7's anatomy measured the result across the whole committed
population: **47 tuning decisions, 0 becoming the `max_tokens` of any later
call**, with one run's conjecturer cap driven 32768 → 800 across sixteen cycles
while every dispatch went out at 32768
(`docs/RUN_ANATOMY_SYNTHESIS_2026-08-26.md` row 9;
`experiments/2026-08-26-run-anatomy-program/W5-signals-controller/`).

The generalizable correction, and the reason this is an erratum rather than an
ordinary fix: **a seam document that lists only the parties who can REFUSE each
other will miss this failure class every time.** Refusal is loud and therefore
gets documented; consumption is silent and therefore does not. The seam's own
Traps section now carries "a field both ends agree about, and neither end
reads", and its expression table carries the consuming link with a check that
goes red if the ceiling-only expression returns
(`experiments/2026-08-26-change-f3-channels-and-wander-cap/`, SPEC.md §S0/S19).

Two further points the record supports and this entry should not overstate.
First, no fix in the chain was wrong: E43's relaxation and the epoch-3
reservation fix were each correct for the run that motivated them, and only
their COMPOSITION severed the link. Second, the direction of travel is the part
worth remembering — before E43 an ineffective steering decision killed the run
and named itself in a typed drop; after it, the same decision was recorded as a
successful policy and disappeared. **The failure mode changed from loud to
silent**, which is the worse of the two.

**E55 — `DR-CON-scheduler-ranking`'s "Must never do" named disk and labels and
omitted the LOG, and an implementer who obeyed it exactly still broke two
committed suites.** The socket contract read: "write to disk or assign a
`Status`/`hv`/`reach` value — attention and ranking only". A `record_measure`
call is neither of those, and it is still forbidden here: `_select_problem` is
called on a TIME-TRAVEL harness opened read-only for replay, which refuses
every write, and on callers that want the ranking and nothing else.

Found by doing it. The wander cap's first implementation emitted its typed
disclosure from inside the ranking function — a Measure, not a status, not a
file — and turned `tests/test_scheduler_promotion_rank.py::test_the_rank_term_moves_no_label`
and `tests/test_amendment_epochs.py::test_reshaped_question_wins_the_continuation_first_cycle`
red, the second with `ReadOnlyHarnessError: time-travel harness is read-only`.
The shipped code stashes the decision on `_pending_wander` and the cycle body
emits it.

The document now states the log prohibition explicitly, with its own check, and
says why it is not obvious. Recorded rather than silently fixed because the
original sentence was not wrong — it was INCOMPLETE in a way that reads as
exhaustive, which is the more dangerous shape for a "must never do" list.

---

## 2026-08-26 (F2 — the reference menu)

**E56 — `SEAM-llm-x-rules.md`'s crossing-name count was already wrong, and
its own check structurally could not see it.** The document read "Thirty-nine
names cross the boundary, and every one of them is data or a refusal". At the
tranche base `4760a32ef`, before this tranche touched anything, the tree
carried FORTY:

    $ python -c "import ast,pathlib; T=[ast.parse(p.read_text()) for p in
      pathlib.Path('src/deepreason/rules').rglob('*.py')]; n=[x for t in T
      for x in ast.walk(t) if isinstance(x, ast.ImportFrom) and
      (x.module or '').startswith('deepreason.llm')];
      print(len({a.name for x in n for a in x.names}))"
    40

The cause is the interesting part, and it generalizes past this document.
The check beneath that sentence asserts `seen >= {...}` and `mods >= {...}`
— SUPERSET tests. They are the right shape for the claim they were written
for ("these names must cross"), and they are structurally blind to the claim
the prose actually makes ("thirty-nine names cross"). A superset test can
never fail on an addition, so the number could drift upward indefinitely
while every check stayed green.

`SCHEMA.md` already states the rule this violated — "**Counts are claims.**
`-ge N` floors hid a 6-file error and a 28-vs-29 mismatch; when the prose
states a number, the check pins it with `-eq`" — which is why this is an
erratum rather than a discovery: the governing rule existed and the document
predated or ignored it.

Corrected in place 2026-08-26 (commit `2a4b8edd6`): the prose now reads
forty-one, reflecting this tranche's own addition of `reference_menu` to the
names `rules/` imports from `llm/`, and a new `-eq` check pins the count so
it fails in BOTH directions. The generalizable action for the next reader:
where a map document states a number in prose, check whether the check under
it is a floor or an equality, because a floor beside a number is a claim
nothing is guarding.

---

## 2026-08-26 (REBUILD F1 — the discharge-required criticism channel)

**E58 (renumbered at merge from E55; that number was taken same-day) — CLAUDE.md's full-gate expectation understates the suite by ~36% and
its duration by half.** "Build and test" reads:

    pytest tests/ -q -n 4                       # full gate, ~8 min
                                                # expect ~3100 passed, 0 failed

Measured twice on `4760a32ef` + this tranche, on an otherwise idle box:
**4225 passed, 6 skipped in 962.12s (16:02)** mid-tranche, and **4231 passed,
6 skipped in 958.70s (15:58)** at its close. The count is 36% above the stated
figure and the wall clock is twice it.

Both halves mislead in a way that costs something. The COUNT is the number a
reader compares against to decide whether their run collected everything; a
reader seeing 4231 against an expected ~3100 has no way to tell drift from a
duplicated collection. The DURATION is worse: `~8 min` invites killing a gate
at ten minutes in the belief that it has hung, which on this container is
exactly when it is halfway through.

Uncorrected in place, deliberately. The number drifts every time a tranche
adds tests — this one added 56 — so a figure baked into CLAUDE.md is a
claim that decays by design, and replacing 3100 with 4231 would only reset
the clock on the same error. What a reader needs is the SHAPE (`0 failed` is
the only acceptable result) and a way to get the current number, which
`.pytest_cache` already holds. Recorded here so the next reader who measures
16 minutes knows the document is behind rather than the box.

Evidence: `experiments/2026-08-26-change-f1-discharge-criticism-channel/`
CHECKLIST.md steps 18 and 29 (both runs pasted), VALIDATION.md "Full gate".

---

## 2026-08-27 (the split-budget leg recording defect)

**E59 — `docs/RUN_ANATOMY_SYNTHESIS_2026-08-26.md` filed the two-call split
leg under "Unexercised — nothing here is broken", and it was broken.** That
document's §3.2 opens "Nothing here is broken. Each is a path that exists, is
believed sound, and has never been driven far enough by a committed run to be
tested", and item 1 is the two-call split leg, correctly counted as 0 of 3 155
attempts carrying a non-empty `split_leg`.

The census is right and the verdict is wrong. Driven one day later, the path
produced a REPLAY-INVALID record every time: 260 `verify_root` violations
across four checks on a run that CONVERGED, plus an
`LLMAttempt.prompt_ref=None` operational failure on its stand-down path. The
protocol wrote its two legs into `attempt_trace`, which `verify_root` reads as
a repair ladder.

The correction is to the INFERENCE, not the count, and it generalises: **"never
exercised" licenses no verdict about soundness in either direction.** §3.2's
own framing ("believed sound") is doing the work of a measurement it explicitly
says was never taken, and a reader scanning that section for risk would have
skipped the one item that was about to stop a launch. The neighbouring §3.3
item 4 cross-reference makes the same path visible twice under the same
verdict.

Corrected by the tranche rather than in place: the mechanism is fixed, so the
item is no longer unexercised. Recorded here because the SHAPE of the error —
a confident "nothing here is broken" over a set defined by not having been
tested — is the part that will recur in the next such synthesis.

Evidence: `experiments/2026-08-27-defect-split-leg-recording/` (REPRO.md for
the 260 violations and the byte-identical crash; RESULTS.md for the before/after
table), `experiments/2026-08-27-pc2b-symmetric-reasoning/BLOCKER.md` at
`ee0563cf1` for the independent first sighting, and
`docs/RUN_ANATOMY_SYNTHESIS_2026-08-26.md` §3.2 item 1 for the claim.
