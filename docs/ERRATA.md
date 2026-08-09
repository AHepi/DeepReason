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
