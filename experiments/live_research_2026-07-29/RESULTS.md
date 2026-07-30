# Live in-run research: glm-5.2 under two frozen allowlists (2026-07-29)

One frontier model (glm-5.2 on Ollama Cloud), one question — what
distinguishes an idempotent operation from a safe one, and which does an
append-only event log require of its writers — asked twice, with the ONLY
difference between runs being the frozen research domain allowlist:

- **wide**: `en.wikipedia.org`, `www.rfc-editor.org`
- **narrow**: `docs.python.org`

Each allowlist is manifest behavior, so each ladder ran its own full
qualification battery (wide 484 s, narrow 443 s, both rc=0 at full tier —
the first qualifications ever run against a schema exposing
`research_proposals`). Every claim below is re-derived from append-only
logs; the audit JSONs beside this file carry the complete records.

## What the model did, live

**In all three runs glm-5.2 proposed directed research unprompted by any
example — three proposals per run, every URL on-topic.** It translated the
question into whatever its frozen list allowed: RFC 9110 §9.2 section URLs
under the wide list; Python `logging`/`sqlite3`/`queue` documentation —
retry semantics, append-mode handlers, delivery guarantees — under the
narrow list. No proposal ever targeted an off-list host: told the truth
about the frozen allowlist in the question text, the model stayed inside it.

## Three runs, three containment stories

**narrow (run-7d8723fb) — the full success path.** Three proposals →
granted → fetched (4/6 request budget; the two-URL proposal spent two) →
packaged → consumed into 100 citable admission blocks → run completed →
bridge composed at `partially_answered`. Replay valid.

**wide, first attempt (run-0c3ce902) — fetch success plus a live
byte-ceiling refusal, then a harness crash.** The model fetched RFC and
Wikipedia material successfully (consumed, citable), and one response
exceeded the frozen 4 MiB per-response ceiling — refused with a typed
`RESEARCH_RESPONSE_TOO_LARGE` attempt inside a `nothing_fetched` receipt,
request spent. The reasoning then crashed mid-run on a simulation-only
assumption in the scheduler (see "Harness fixes"). The root replays VALID
and is pinned as the regression fixture `tests/test_research_root_replay.py`.

**wide, second attempt (run-5a771259) — typed exhaustion end to end.** The
model proposed `rfc9110#section-9.2` URLs; the redirect chain landed on a
page exceeding the 4 MiB ceiling, so all three URLs were refused (typed,
one spent request per hop), exhausting the 6-request budget exactly
(receipt `nothing_fetched`, 6/6). The two follow-up proposals were DENIED
with typed `requests_budget_exhausted` transitions — the cumulative budget
working live. The run then completed and bridged at `partially_answered`
**with the fetch refusals surfacing in the final answer's epistemics**: the
composed output explicitly records that verbatim RFC definitions are
unavailable and downgrades exactly the claims that needed them, while still
answering the core question (writers cannot be "safe"; the log requires
idempotence — with a preserved live rivalry over whether RFC-sense
idempotence suffices or a stronger log-specific dedup property is needed).

## Harness fixes the live runs forced

The first live research-enabled run exposed three simulation-only
assumptions outside the capability layer, each now fixed and committed:

1. `write_tranche_a_audits` crashed on research proposals/consumptions;
   it now reports contained fetches (RESEARCH_SOURCE_AUDIT.md) and counts
   research requests in TOKEN_ACCOUNTING.json.
2. `verify_root` crashed on research grants/compiled/receipts/packages and
   checked all capability transitions against the simulation policy digest;
   it now validates the research chain against the frozen research policy
   (allowlist host membership, request/source budgets, per-turn caps).
3. The scheduler treated any unconsumed `RESULT_PACKAGED` package as a
   simulation follow-up — this crashed run-0c3ce902; research packages now
   stay inside their own conjecture cycle.

## Honest caveats

- The wide/narrow ladder questions contain a literal `'\''` artifact from a
  quoting bug in `run_research.sh`; run-5a771259 used the clean text. The
  question semantics were unaffected.
- Fetched material became citable blocks, but no candidate in these short
  (6-cycle) runs recorded an `evidence-citation` measure against them —
  citable blocks surface in packs for later turns, and the runs ended
  before any candidate cited one. Demonstrating a byte-checked citation of
  fetched text in a live run remains open.
- `bridge_trio.py` reports `FAIL bridge_result has resolution` on both
  completed runs; it reads a key the result payload does not carry. Both
  bridges completed with `process_status=success`,
  `resolution=partially_answered` (see bridge-status lines in the .txt).
- run-0c3ce902's reasoning is incomplete (crashed pre-fix); its value is
  the intact, replay-valid research record.

## The Popper loop, closed live (2026-07-29, second session)

The narrow run now demonstrates the full fallibilist cycle in one
append-only root: typed stop → bridge (fence 430) → continuation (6 more
live cycles, 6 new artifacts, second typed budget_exhausted stop) →
superseding bridge at fence 676. Both bridge terminals stand in the log
(seqs 473 and 691); terminal authority, integrity, and security all
verify. No answer was final: the first bridge became history the moment
the record grew past its fence.

Getting there surfaced six no-drift assumptions, each fixed and tested:
the continuation fence, the resume-lifecycle builder, the resume-decision
model, the checkpoint cross-check (a bridged run was silently
un-continuable), the staged bridge's unwhitelisted decomposition-effect
measure (a staged successful bridge invalidated its own root's terminal
authority), stale prior-epoch status/result views served as the new
launch's outcome, and epoch-blind crash recovery refusing every
superseding compose.

Calibration findings for the allowance signal suite:

- **The citation loop engages under continuation — and fails
  informatively.** The continued model attempted 11 evidence citations;
  every one was typed `EVIDENCE_REF_UNKNOWN_BLOCK` because it cited its
  own accepted-artifact hashes instead of the fetched-document block ids.
  Zero verified citations of fetched material. The §4 checker held; the
  gap is presentation — packs do not make citable research block ids
  discoverable enough for the model to use them. The waste signal
  therefore correctly still reads 3/3 uncited sources.
- **No new research proposals in the continuation** (still 3, budget
  4/6): the model spent its continuation consolidating, not fetching, so
  the allowance controller recorded no live grant decisions. Its denial
  and widening behavior is pinned offline in
  tests/test_research_capability.py.
- **The 18-way rivalry survived both segments**, so the superseding
  bridge is again truthful observation-mode rather than prose. The next
  lever is the reader-facing findings report (established / contested /
  unverified, rendered from the record), which remains the top
  presentation gap for end users.

## Segment 3 (2026-07-29): the legend ships, and a new defect surfaces

Segment 3 continued the narrow root past BOTH bridge epochs (the
two-bridge tail validated cleanly), ran 6 more live cycles to a third
typed budget_exhausted stop at cycle 18, and composed a third-epoch
bridge at fence 1131. Honest scorecard:

- **Citation conversion: not yet exercised.** Segment 3's candidates
  carried no evidence_refs at all — the 11 typed UNKNOWN_BLOCK failures
  from segment 2 remain the only citation attempts. The citable-block
  legend entered packs this segment, but the model chose consolidation
  over citation, and proposed no new research either (no allowance
  decisions recorded). Converting the legend into verified groundings
  still awaits a run whose candidates actually cite.
- **A resolution-semantics defect at scale.** The third bridge reports
  resolution=answered — yet the record holds 70 accepted artifacts, zero
  refuted, an unresolved rivalry now ~60 positions wide. The bounded
  evidence-pack window surfaced only 4 survivors and no rivalry
  observation, so the composer truthfully mapped everything it was shown
  and upgraded the resolution. The overclaim lives in the bounded
  window, not the classifier: at rivalry scales beyond the pack budget,
  the rivalry observation must survive windowing (or the resolution must
  be capped at partially_answered when the window is known-truncated).
  Filed as the next defect; FINDINGS.md still tells the full story (60
  rival positions, preserved).

## Segment 4 (2026-07-29): the config referee goes live

The referee — an observe-only critic that reviews whether the dynamic
token-steering configuration is doing its job — shipped in three stages
(deterministic view/verdict core, manifest-frozen authority, transactional
dispatch on the frozen critic seat) and was proven across three fresh
ladders (glm-5.2, docs.python.org allowlist, DEEPREASON_CONFIG_REFEREE=2,
each a distinct requalified subject):

- **Attempt 1 (run-e542c3c1): first grounded critique, then a real bug.**
  The cycle-2 review completed as a live config-referee.v1 transaction:
  verdict config_effective / no_change, citing three recorded observation
  seqs. The cycle-4 review was token-budget-denied inside issue — and the
  dispatch code followed the typed budget_denied terminal with an abandon
  transition, which the harness correctly refused (WellFormednessError),
  failing the run. Fail-closed did its job; fixed in 03758d61 with
  regression tests at both the transaction and scheduler layers.
- **Attempt 2 (run-d17935a4): typed denial, graceful cycle.** With the
  fix, both cadence firings terminated as typed budget_denied work items
  (default token budget too tight for reviews); the run completed with a
  typed stop and replay violations limited to the pre-existing
  foreign-criticism coverage-debt class (same class as the accepted
  three-epoch narrow root).
- **Attempt 3 (run-e6c07aec, --token-budget 200000): the full loop,
  replay-clean.** Two completed referee transactions, two grounded
  critiques (seqs 436 and 452), and verify_root returns ZERO violations.
  The criticism is substantively right: the referee independently spotted
  the sustained EVIDENCE_REFS_UNBOUND run at seqs 342–356 ("the
  consumed-source/uncited condition the dynamic steering should react to
  by tightening"), observed no tightening response followed, judged the
  config mistuned, and recommended research_allowance_step_tighten — the
  exact intervention that condition calls for, derived from the signals
  alone. The second critique cites the first (seq 436): earlier advice is
  itself a citable observation, so the referee can see whether its advice
  corresponded to any change.

Containment held everywhere: citations outside the shown window are
rejected as unfounded (offline-tested), recommendations came only from
the frozen menu, and no budget, status, or policy byte moved because the
referee spoke — the critiques are attention on the record, available to
the operator and to any criticism-weighted continuation.

## Segment 5 (2026-07-29): the self-study run completes, and answers nothing

The self-study ladder — glm-5.2 asked to criticize DeepReason's own school
and criticism mechanism, with five mechanism documents attached and all
three opt-in capabilities on — finally ran to a typed terminal after five
earlier attempts died to container resets, a rig typo, and four
now-fixed defects. Attempt 6 (`run-9175f0ec`, launched after retiring the
attempt-4 root as `failed-epoch2-`) reached a typed `budget_exhausted`
stop at cycle 6: 42 provider calls, 191,232 of 200,000 tokens, 754
events, 79 accepted artifacts.

**The attached-evidence envelope is proven; everything it was meant to
feed is empty.** Admission worked exactly as designed — 5 sources, 331
blocks (255 paragraph, 68 section, 8 table), 112,749 dossier bytes, zero
admission refusals, and the dossier KeyError that killed attempt 4 never
recurred. Past that point every capability the run was configured to
exercise returned nothing:

- **Research: 0 requests, 0 fetch attempts.** The frozen
  `en.wikipedia.org` allowlist was never consulted. The model proposed no
  directed fetch despite the question naming three in-scope topics.
- **Simulation: 0 formal tool executions.** No `sandboxed_python_v1`
  proposal was ever made, so the contained runner — the segment's
  headline capability — was not exercised at all by this run.
- **Referee: 2 transactions, both typed `budget_denied`
  (`token_budget_denied`), 0 critiques.** The same 200k budget that let
  the referee complete twice in segment 4 could not seat a single review
  here, because the budget was gone before the cadence fired.
- **Citations: 33 attempts, 33 `EVIDENCE_REFS_UNBOUND`, 0 verified.** The
  question explicitly instructed the model to cite block ids. Every
  attempt failed its deterministic check, so no claim about the mechanism
  is grounded. Citation conversion remains unexercised across all five
  segments.

**The question was never dispatched — a scheduling defect, not model
behavior.** The work-preparation chronology settles culpability
precisely. Every provider call from the first (formal fence 32) to the
last (fence 605) served one problem: `conn:0e26d6be54fd`, the
auto-spawned neighbourhood-connection problem for the attached-source
record of STATE_OF_THE_THEORY.md. The full 191,232-token spend decomposes
as: 73,285 tokens / 8 calls on its conjecturer turns, 23,032 / 6 on its
atomic candidates, 39,007 / 12 on repair turns of those outputs, and
55,908 / 16 on batch criticism of them. The operator's question
(`question-98a0e3…`) was first *prepared* at fence 722 — after the budget
was already spent — and all 8 of its conjecturer turns terminated typed
`budget_denied` without one provider call. The referee's two cadence
firings (fences 720, 740) and a second connection problem
(`conn:0f99efbab8a4`, fences 742–748) were denied the same way. So the
70 standing relation conjectures ("depends on SRC_004", "reduces to
SRC_003", …) are not the model failing to engage the question — glm-5.2
answered exactly what it was dispatched, every time. The harness spent
the entire budget asking how one attached document relates to the other
four, and never once asked its operator's question.

This reframes the parked defect at a harsher altitude. It is not that
conjecture outpaces criticism, or even that neighbourhood work
outcompetes the question — there was no competition. Attach-spawned
connection problems were scheduled strictly ahead of the operator's
question with no budget reservation whatsoever, so at any attach scale
where connection work can exhaust the budget, the question's allocation
is exactly zero. The fix is a scheduling guarantee, not an economy tweak:
the operator's question must hold a budget floor (or scheduling priority)
that auto-spawned housekeeping problems cannot consume.

**A new replay violation class: ordering-only, root-caused to
re-render.** `verify_root` returns `valid: false` with 6 violations. Four
are the known `foreign-criticism` coverage-debt class. Two are new:
`conjecture-context` at event seqs 390 and 547 — "render handles differ
from the selected blocks", the check that the context rendered to the
model matches the attention selection the record commits to. Direct
comparison of the render receipts (state_seqs 386 and 543) against the
replayed attention receipts shows the mismatch is **ordering-only**: the
handle sets are identical (10 and 13 blocks; nothing shown that was not
selected, nothing selected that was not shown), but the render's
`block_handles` order is a permutation of the selection's `final_order` —
in the seq-386 case a single block sits at its *old* position 2 while
`final_order` moved it to the end. Both violations sit inside
repair-turn clusters (fences 385→393 and 542→550), and both failing
windows follow earlier renders that shared blocks — consistent with the
renderer maintaining `block_handles` as a persistent dict across
re-renders, where updating an existing key preserves its original
insertion position while `final_order` reorders freely. Content
faithfulness held; the ordering commitment is what broke. Filed as a
defect: either the renderer must rebuild `block_handles` in `final_order`
on every render, or the invariant must compare as ordered sets only if
ordering is genuinely not part of the containment claim.

Honest status: the run is complete, terminal, and continuable. Nothing
here refutes the referee or the contained runner — both were starved
before dispatch, along with the question itself. What the run
establishes: the attach path admits real documents end to end; the typed
budget-denial path holds under total exhaustion (16 denials, no crash);
and the scheduler's treatment of auto-spawned connection problems is the
binding defect — severe enough that a 200k-token run completed without
its question ever reaching the model.

## Segment 6 (2026-07-30): the question answers, first verified citations, replay-valid

Segment 5's diagnosis produced two harness fixes, and the second one
took two rounds — the first round was refuted live, which is worth
recording as much as the success.

**The fixes.** (1) Render receipts persist as canonical JSON with sorted
keys, so a reloaded handle map iterates B1, B10, B2, ... and every
consumer comparing `.values()` against a selection's `final_order` broke
at ten-plus blocks — the "render handles differ" replay violations were
spurious convictions of faithful renders. `ordered_refs()` recovers
handle-index order; the replay validator, the live canonical-order check,
and both wire-contract sites now use it, and re-verifying the attempt-6
root drops exactly the two conjecture-context violations. (2) Scheduling:
making reflexive problems lose rank ties was not enough — attempt 7
(cycle 0 `disc:question`, cycle 1 `conn:0e26d6be54fd` again, stopped at
~0 tokens) showed that evidence admission auto-accepts import-role
records ADDRESSING the question, so the question counted as "solved" and
took the 0.3 aging discount before a single provider call; no tie was
ever reached. The complete fix: import-role artifacts never count as
survivors for scheduling, and seed problems win rank ties outright (the
question must also beat its own spawned `disc:question-<digest>`, which
wins the bare id tie). Both fixes regression-tested against the exact
live conditions; full gate 3106/0 twice.

**Attempt 8 (run-9175f0ec, epoch-5 of the identity): the run the ladder
was designed for.** Clean `reason_rc=0`, typed `budget_exhausted` at
cycle 6, 189,909/200,000 tokens over 35 provider calls, 486 events —
and `verify_root` returns **valid: true, zero violations**, the first
fully replay-valid attached-evidence run on record. The cycle heartbeats
read: question, disc:question, conn, question, conn, disc:question —
the operator's question took cycle 0 and ~63% of all tokens (119,768
across 3 turns + 17 atomic candidates), with its own discrimination and
the connection housekeeping rotating in on age exactly as designed.

**First verified citations in the record: 28.** After five segments of
typed citation failures (UNKNOWN_BLOCK, EVIDENCE_REFS_UNBOUND), 28
citations byte-verified against the admitted dossier, with 9
EVIDENCE_QUOTE_MISMATCH refusals showing the deterministic checker still
rejecting bad quotes. Citation conversion — the capability the
attach envelope exists for — is now exercised end to end.

**The model's actual answer.** 34 positions stand accepted, and this
time they are ABOUT the mechanism. The record preserves a genuine
rivalry of diagnoses for why criticism retires almost nothing while
rivalry grows: incomplete closure enforcement in the grounded-extension
attack pass (defeated warrants never transitively invalidate their
carriers); batch criticism diluting per-target warrants below the
retirement threshold; absence of any enforced coverage-debt retirement
threshold; per-target warrant requirements compounding combinatorially
with batching. The proposed optimisations are specific and criticizable:
enforce the closure rule; winner-takes-all tournaments per criticism
batch; a coverage-debt amortization queue forcing attention proportional
to accumulated debt; criterion-level forced choice to bound rivalry;
ensemble-pruning that collapses semantically redundant rivals rather
than criticizing each independently; throttling school generative
capacity by unretired debt. And the record's own criticism is doing real
work against them: it convicts the mutual-information pruning proposal
of contradicting its own disanalogy ("warrants are strictly logical, not
probabilistic"), catches an internal O(N^2)-vs-O(N) inconsistency in a
proposed simulation's coverage-debt formula, and identifies that
debt-coupled throttling freezes a high-debt plateau instead of retiring
anything.

**The honest residue.** Simulation and research remain unexercised — but
the failure moved somewhere more interesting: candidates PROPOSED
simulations and named Wikipedia targets in prose while leaving the typed
`simulation_refs` channel empty, and the in-record critics repeatedly
convicted them for exactly that. The mechanism is self-policing the gap;
the model is not yet using the typed proposal channel. The config
referee's two cadence firings were again typed budget_denied — the
question's atomic-candidate appetite left the referee's reservation
unfunded at both firings; the reservation sizing is the next tuning
knob. Rivalry discipline improved without new machinery: 34 accepted
positions against attempt 6's 70, on the same budget, with the
disagreement preserved as unresolved rivals rather than merged.

## Segment 7 (2026-07-30): a genuinely open problem, and what four attempts proved

A new all-capability ladder (`openchallenge_run.sh`, fresh home, fresh
full qualification battery) put glm-5.2 on an unsolved programming
problem: the minimal 13-input sorting network. S(13) is unknown — proven
optimal only through n=12, best known 45 comparators, Batcher's
construction 48 (verified during dossier compilation) — and every
candidate is exactly decidable in the contained sandbox by the 0-1
principle (8192 binary vectors, ~60 ms). Two dossier documents were
attached: the problem statement and a capability contract that
explicitly mandates the TYPED simulation and research channels, citing
the previous segment's prose-only failure mode. Four attempts, all
preserved as epochs of the run identity:

- **Attempt 1 (failed-epoch1, typed failure).** glm-5.2 spent its entire
  8192-token completion cap on hidden reasoning about the combinatorial
  problem and emitted nothing — three attempts at completion=8192 with
  empty output, repairs returning empty objects, and the route seat
  failing closed with V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY at cycle 0.
  A genuinely hard question needs a deep completion budget: the ladder
  now sets 24576.
- **Attempt 2 (completed-epoch2): every typed channel fired — and a new
  defect.** Typed budget_exhausted, 178,642/200,000. The model filed TWO
  typed sandboxed_python_v1 simulation proposals, each a genuinely
  discriminating experiment (simulated annealing vs uninformed random
  search at n=7; pruned-exhaustive vs evolutionary search at n=9), and
  TWO typed research proposals; the research chain ran END TO END —
  proposed, granted, compiled, dispatched, fetched
  (en.wikipedia.org/wiki/Sorting_network, ~197 KB), packaged, consumed
  as citable evidence. But both simulation proposals were denied
  (request_budget_exhausted / execution_budget_exhausted) with ZERO
  simulations run: the capability state pools every capability's
  proposals and work orders, and the simulation budget gate counted the
  pooled totals, so the two research fetches had silently exhausted the
  simulation budgets. Fixed (gate and accounting now count only
  simulation records) with a regression test that drives two full
  research chains and then requires the first simulation proposal to
  clear untouched budgets; full gate 3107/0.
- **Attempts 3 and 4 (completed-epoch3, and the standing root): clean,
  cited, and typed-channel-silent.** Both completed with typed
  budget_exhausted (174,513 and 176,638 tokens), healthy
  question-first rotation, zero replay violations, and verified
  citations (21 and 8) — but neither filed a single typed capability
  proposal, so the budget fix could not be exercised live. The filing
  behavior is stochastic across identically-configured runs: the same
  model, question, and contract that produced four typed proposals in
  attempt 2 produced none in attempts 3 and 4.

**What the model said about the problem.** The accepted positions form a
real rivalry about where S(13) lives and why search stalls at 45:
extension arguments (an optimal 12-input prefix plus a 5-comparator
insertion tail would give 44 — rivaled by the claim that integrating a
13th channel needs at least 6 comparators, and criticized correctly for
assuming a 44-network must embed an optimal 12-prefix at all);
landscape arguments (no single-comparator removal from a 45-network
preserves sorting, so 45-to-44 needs simultaneous structural changes;
44-networks may be disconnected from 45-networks under local search
moves); and strategy claims (symmetry-pruned local search from Batcher
beats naive synthesis; SAT symmetry-breaking may over-prune asymmetric
optima). The record's criticism enforced the capability contract
relentlessly — candidate after candidate convicted for describing a
discriminating simulation while leaving the typed channel empty — and
caught real mathematical errors, including an inversion-count pruning
bound that is invalid because non-adjacent comparators resolve multiple
inversions at once. No 44-comparator network was produced; no candidate
network was sandbox-verified, because no simulation was ever granted.

**The campaign's honest ledger.** Across the four attempts every
DeepReason capability was exercised live except one: attach admission
and byte-checked citation (three runs), contained research fetch to
consumption (attempt 2), typed simulation proposal and typed denial
(attempt 2), typed run failure fail-closed (attempt 1), typed
budget_exhausted stops and clean replay (attempts 2-4). The one part
never exercised live remains contained simulation EXECUTION — blocked
first by the pooling defect, then by the model simply not filing. The
lever is no longer harness correctness (the offline regression proves
the full grant-execute-consume chain); it is turn-contract affordance:
the typed proposal channel needs to be un-ignorable in the conjecturer
contract — for example a required field forcing each candidate to
either reference a filed simulation or state why none discriminates —
before a live granted execution can be counted on rather than hoped
for. The referee also stayed starved in all three completed attempts
(six typed budget_denied transactions) under the question's
atomic-candidate appetite; its reservation sizing is the other standing
knob.

## Segment 8 (2026-07-30): amendment epochs land, and are unexercised live

Segment 7 closed with the campaign's ledger and a standing constraint
that had nothing to do with the model: a run's question was frozen at
mint time. Changing it, or admitting evidence discovered mid-campaign,
meant a new root and a lost epistemic state — every accepted position,
rivalry, and criticism debt from the old question thrown away in order
to ask a better one. `deepreason amend` removes that constraint. After a
typed terminal stop it appends one epoch to the SAME root: supplemental
sources admitted as their own dossier with their own digest, the
question superseded by a seed problem whose provenance names the
question it replaces, and a `run-amendment.v1` line chaining the two
behind a declared event fence. `continue` then resumes, and the reshaped
question takes cycle 0 on the existing seed-priority guarantee.

**What the record shows.** Offline, on a converged v6 root: epoch 0's
manifest, run input, and dossier keep their exact canonical bytes; the
log grows only by suffix; a citation verified against the first dossier
returns a byte-identical `EvidenceCitationCheckV1` after the amendment;
no pre-existing artifact changes status and no attack or dependence edge
is removed; `verify_root` returns clean across the fence, and again
after a real continuation. `verify_root` over all fifteen committed run
roots in this experiment is byte-identical to the pre-change commit —
the defect-era findings on `failed-epoch1`, `failed-epoch2`, and the
five `foreign-criticism` roots all still report exactly what they
reported before, none masked. Full gate 3128 passed, 0 failed.

**The residue, stated plainly.** None of this has been exercised live.
Every claim above rests on offline regression against a fixture root; no
amendment has been applied to any root in this campaign, and no live
model has yet reasoned across an amendment fence. What the record
therefore does NOT show: whether a reshaped question actually produces
better conjectures than a fresh root would, whether glm-5.2 uses the
older dossier's blocks once new ones are visible alongside them, or
whether the seed-priority win at cycle 0 survives a frontier with real
discrimination and connection spawns on it rather than a fixture's two
problems. Accepted does not mean true, and implemented does not mean
useful: the capability is proven correct, not proven valuable.

**One thing the tranche's own validation caught.** The first validation
pass returned FAIL, not PASS, on two counts — and the more instructive
one was not the design deviation but a plain usability dead-end: a run
that crashed mid-amendment could be *completed*, but if the operator
then wanted a different amendment there was no typed way out, only a
hand-deletion inside a run root that this project's own rules forbid.
Recovery now splits on whether the staged epoch ever reached the ledger:
nothing applied, it is superseded outright; events applied, they belong
to that epoch and it is completed, with the refusal naming that route.
The gap was invisible to the implementation's own tests and visible
immediately to a validation that asked what an operator would actually
try next.

## 2026-07-30 — tensor rank live run: the record blocked every quoted citation, and the sandbox never ran

Run root `run-27b80f26bd398c718360e97e2a403593` (home `openchallenge`,
glm-5.2, qualification cache hit). Typed outcome: state `completed`,
`stop_reason` `budget_exhausted` at cycle 6, 176,730 of 200,000 tokens
over 26 provider calls, `verify_root` clean, terminal commitment bound at
event 498. What follows is what the record shows about the two channels
that failed, both diagnosed from the record and neither re-run.

### The 42 blocked citations are a line-wrapping artifact, not dishonesty

`log.jsonl` carries 42 `EVIDENCE_QUOTE_MISMATCH` events and 4
`EVIDENCE_CITATION_VERIFIED`. Every one of the 46 names a block of the
attached dossier; none names an unknown or ambiguous block.

The 42 mismatches reduce to 15 distinct (block, quote) pairs, recovered
from the run's blob store and re-checked against each block's canonical
text — the exact byte slice `span_start:span_end` of the admitted source,
digest-verified against `text_sha256`:

    exact              0
    present after whitespace normalisation   15
    absent from the block                     0
    block unresolvable                        0

Every quote the model offered is really in the block it cited. Nine
differ from the admitted bytes only where the dossier has a hard line
break and the model wrote a space:

    model  '...despite: decades of hand construction; numerical alternating-least-squares s'
    source '...despite: decades of hand construction; numerical\nalternating-least-squares s'

The other six differ by a break plus list indentation (`\n   `) or by
runs of spaces inside an indented code block collapsing to one.

`check_candidate_citations` tests `ref.quote.encode() in canonical.encode()`
(`src/deepreason/evidence/citations.py:192`) — raw byte containment against
text that still carries the source's newlines. `TENSOR_RANK_CHALLENGE.md`
is hard-wrapped at ~72 columns, so a quote long enough to be worth making
almost always spans a wrap and almost always fails. The dossier's own
authoring, not the model, is what made the channel unusable.

The 4 that verified prove the same point from the other side. All four
cite one block, `70df46c005c3`, and all four carry no quote at all: the
checker records `EVIDENCE_CITATION_VERIFIED` for a bare block reference
without ever comparing text. So the run's byte-checked citation score is
0 of 50 quoted citations and 4 of 5 unquoted ones — and the 7 quoted
citations of that same block `70df46c005c3` failed while its bare
references passed. Nothing was verified by quotation in this run.

Residue: this says nothing about whether the model would quote honestly
against an unwrapped source. It says only that the check as written
cannot distinguish an honest quote of wrapped text from a fabricated one,
because both fail identically. Whether the right repair is a normalising
comparison, an unwrapped admission form, or leaving the check strict and
telling the model the constraint is a design question, not settled here.

### The sandbox denial: the model was never told the program's shape

One simulation proposal, `sim_2x2_diagonal_W_refutation`, lifecycle
`proposed → validated → denied`, `reason_code` `invalid_model_program`,
zero budget consumed. Replaying `validate_sandboxed_python_source` over
the proposal's stored `model_source` reproduces the denial exactly:

    ValueError: sandboxed Python must define exactly one simulate function

The program is a script: a `verify_decomposition` helper, then ten
top-level statements — assignments, asserts, prints. The validator's
first structural rule (`src/deepreason/simulation/compiler.py:212`) requires
the module body to be exactly one `FunctionDef` named `simulate` with
signature `(inputs, rng)`. The submission fails on statement count before
anything else is examined.

The program is not otherwise bad. It contains no import, no forbidden
name, no private attribute traversal; at 2,255 bytes it is far inside the
size cap; the runner profile matched and the toolchain was available. Its
mathematics is sound — the diagonal-W argument it encodes is correct.
It was refused for its shape alone.

The reason it had the wrong shape is in the prompt. The pack that carried
this turn (blob `9705881e`, 23,570 bytes) describes `model_source` to the
model as exactly `{"maxLength": 262144, "minLength": 1, "title": "Model
Source", "type": "string"}`. The words `simulate`, `inputs`, and `rng`
appear nowhere in the pack, nowhere in the ladder's question, and nowhere
in `CAPABILITY_CONTRACT.md` — which I wrote, and which describes what the
sandbox is FOR at length while never stating what a program must look
like. The requirement exists only in the validator. A second, latent
failure sits behind the first: the proposal declares `requested_observables:
["stdout"]`, but observables are keys of the mapping `simulate` returns
(`verification/contained.py:202`), and stdout is not one — a correctly
shaped program with these observables would still have failed, one stage
later, as `declared observable missing`.

So `invalid_model_program` with an empty detail is accurate and useless.
The typed record says the program was invalid; it does not say the module
body had eleven statements where one was allowed, and the operator cannot
learn that from the run root — only by replaying the validator by hand,
which is what produced this paragraph.

Residue: capability-channel use is stochastic across identical runs, and
this is one attempt. What is NOT stochastic is the prompt: no run of this
ladder can tell the model the contract, because the contract is not in the
pack. That part is a defect, not a sampling outcome.

### Found while diagnosing: TOKEN_ACCOUNTING.json miscounts research as simulation

`TOKEN_ACCOUNTING.json` for this root reports `simulation_compilations: 1`,
`simulation_executions: 1`, `simulation_backend_attempts: 1`. No
simulation compiled, executed, or reached a backend in this run — the
single proposal was denied at validation and `objects/` contains no
simulation work order, compiled simulation, or execution receipt. All
three counters are the Wikipedia research fetch, mislabelled.

The cause is the documented invariant, violated in the reporter:
`capabilities/audit.py:435-438` reads `len(state.compiled)`,
`state.execution_count`, and `sum(len(receipt.attempts) for receipt in
state.receipts.values())` without filtering by type, and
`capabilities/state.py` puts `CompiledResearchFetchV1` into the same
`compiled` map (line 307) and the research receipt into the same
`receipts` map (line 340). The budget meter beside it
(`capabilities/simulation.py:1134`) filters by `isinstance` and is correct
— which is why `run-result.json`'s `capability_accounting` truthfully
reports `simulation_executions: 0` while `TOKEN_ACCOUNTING.json` reports 1
for the same run. Parked, not fixed: see PARKED.md P4.

## 2026-07-30 — fixed: a quoted citation is now checked against the block's words, not its line layout

Tranche `experiments/2026-07-30-fix-citation-quote-check/`. Defect class,
offline proof, no live run.

**What the record showed.** `check_candidate_citations` decided a quoted
citation by raw byte containment against the admitted source's own bytes,
which carry the author's hard wrapping and alignment. A model writes
running text. So the verdict tracked line layout, and an exact quote
spanning a wrap returned the same `EVIDENCE_QUOTE_MISMATCH` as a
fabricated one — the check could not discriminate between the two things
it exists to separate.

**What is fixed.** The strict byte test runs first; on failure both sides
are whitespace-folded and the comparison is retried. Every non-whitespace
character must still appear, contiguously and in order. Folding never
inserts whitespace where the source had none, so `"foobar"` still fails
against `"foo bar"`, and an all-whitespace quote is refused rather than
matching every block. The admitted bytes were not touched: normalising at
admission would move `text_sha256`, block ids and dossier digests, and
invalidate every committed root.

**What the record now shows.** Full gate 3168 passed, 0 failed.
`verify_root` over all sixteen committed roots is byte-identical to the
pre-change sweep — 23 foreign-criticism, 1 run-input, 1 terminal-authority
violations, the same counts on the same roots, none masked and none
introduced. The tensor-rank run's own 15 recorded quotes, replayed through
the fixed checker against its own dossier, return 15
`EVIDENCE_CITATION_VERIFIED`. That is a counterfactual, not a repair: the
root still carries its 42 `EVIDENCE_QUOTE_MISMATCH` events, because the
log is append-only and was not edited.

**One decision worth recording.** A reflowed quote records
`EVIDENCE_CITATION_VERIFIED` rather than a new typed code. The
alternative was considered and rejected: the check exists to establish
whether the model reproduced the source's words, and layout is not part
of that question, so a reflowed quote is a verified citation and not a
lesser kind. The distinction is not lost — both the quote and the
admitted bytes stay in the record, which is exactly how this tranche
re-derived all 15 field cases after the fact.

**The residue.** No live model has been through this path. Whether
glm-5.2 now produces verified groundings against a wrapped dossier is
unproven; what is proven is that the 15 claims the run rejected would be
accepted, and that the check now separates an honest reflow from a
fabrication. Accepted does not mean true, and fixed does not mean
exercised.

**What the tranche got wrong, and how it was caught.** FIX.md was amended
mid-implementation to also correct `EvidenceRefClaimV1`'s docstring,
which tells the model a quote must reproduce a byte span "exactly" — now
stricter than the harness enforces. Before making that change the
qualification subject digest was checked and found not to carry contract
schema text, which is true. Generalising from that one digest to "the
prompt is free to change" was not. Pydantic promotes the docstring into
the JSON schema `description`, the schema is serialised into the context
pack, and the pack's bytes sit inside committed provenance digests: the
gate came back `4 failed, 3164 passed`, on a token baseline (842.0 vs
784.5) and a `generated_root_sha256`. Isolated by stashing — all four
pass on a clean tree and again with only that file reverted — and the
amendment was retracted rather than the digests regenerated, since
rewriting committed provenance is frozen-record semantics. The contract
text is parked as D1a for the D2 tranche, which is about pack text
anyway and can pay that cost once.

**Still open from the 2026-07-30 diagnosis:** D2 (the sandboxed_python_v1
program contract never reaches the model) and P4 (TOKEN_ACCOUNTING.json
counting research records as simulation records).
