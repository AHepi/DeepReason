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

**The model never engaged the question.** This is the finding, and it is
worth more than the capability tallies. All 70 standing positions are
evidence-*neighbourhood* conjectures: relation claims about a single
artifact (`0e26d6be54fd`) against the five attached sources — "depends on
SRC_004", "reduces to SRC_003", "contradicts SRC_005", "shares mechanism
with SRC_001", "abstracts", "integrates" — restated dozens of times with
varying refutation conditions, plus meta-criticisms of those relation
claims. The criticism is often good (it correctly convicts targets of
naming a relation kind while supplying no causal mechanism, and of
refutation conditions narrower than the claims they guard). But it is
criticism of the wrong target. Not one accepted position addresses how
schools generate rivals or how criticism retires them. The run spent
191k tokens becoming an example of the pathology it was asked to
diagnose.

This sharpens the parked defect. The record already showed criticism
retiring rivalry more slowly than conjecture grows it; segment 5 shows
something worse at the scheduling layer — with five attached sources the
neighbourhood machinery generates a combinatorial relation lattice
(sources x relation kinds x restatements) that displaces the operator's
question entirely. Conjecture did not merely outpace criticism; it
crowded out the problem. Any fix that only speeds up retirement leaves
this untouched: the question needs a budget floor the neighbourhood work
cannot consume.

**A new replay violation class, first fired here.** `verify_root` returns
`valid: false` with 6 violations. Four are the known
`foreign-criticism` coverage-debt class. Two are not: `conjecture-context`
at seqs 390 and 547, "render handles differ from the selected blocks" —
the check that the context actually rendered to the model matches the
attention selection the record commits to. That check has fired in no
previous run recorded here (segment 4's clean ladder returned zero
violations; earlier ladders showed only the coverage-debt class). It bears
directly on whether the record faithfully states what the model was shown,
so it should be characterized before it is explained away — specifically,
whether the mismatch is ordering-only or a genuine set difference. I could
not reach the receipts through the event blobs to settle that here; the
violations reproduce from the committed root via `verify_root`.

Honest status: the run is complete, terminal, and continuable. Nothing
here refutes the referee or the contained runner — both were simply never
reached. What the run does establish is that the attach path admits real
documents end to end, and that on this question the harness's own
neighbourhood stage is a budget sink severe enough to starve the
question, the citations, the research, the simulation, and the referee
all at once.
