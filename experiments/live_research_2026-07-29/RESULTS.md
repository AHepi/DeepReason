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
