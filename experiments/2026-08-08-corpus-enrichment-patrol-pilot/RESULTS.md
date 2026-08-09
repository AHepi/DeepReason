# Corpus-enrichment + consistency-patrol pilot — RESULTS (living document)

Dated, honest-ledger segments per house convention. This file is updated
incrementally as each phase boundary lands; earlier segments are never
rewritten, only appended to or corrected with a new dated note.

## 2026-08-08 — Pre-registration and setup

Frozen `prereg.yaml` and `PARKED.md` committed before any Phase 1/2/3
call (`b4859d48`). One deviation from the task's own instructions was
found and recorded before spending any budget on it: **the "dual-mode"
opt-in (`conjecturer.turn.v7`) the task asked to switch on for Phase 1
does not work for any live run today.** `ContractVersionPolicyV3`
accepts the label, but the code that would grant a v7 manifest the
authority to actually validate (`_compile_contract_schema_repair_policy`,
`src/deepreason/run_manifest.py:2473-2545`) hardcodes that authority for
`conjecturer.turn.v6` only — a manifest asking for v7 is refused with a
typed error, `V6_BEHAVIORAL_REPAIR_GRANT_REQUIRED`, before any run can
even start. Confirmed by direct construction, not assumed. A second,
independent gap was found alongside it: the `encoder` role's own dispatch
function (`rules/encoding.py::draft_encoded_commitment`) has zero
callers anywhere in `src/` — it would not fire even if v7 worked. Both
are parked as **P-CEPP-1** (`PARKED.md`) rather than fixed — this
tranche's scope keeps `src/`/`tests/`/`tools/` byte-untouched. Phase 1
therefore runs on the harness's current default (v6); **zero
candidate-checker commitments across every Phase 1 root is the
EXPECTED, reported outcome, not a live-run miss.**

A second correction, made before launch: the task referred to an
"encoder seat," but `seat_bindings.py`'s `GROUP_ROLES` shows `"encoder"`
is a ROLE, not a seat GROUP — the only CLI-addressable group reaching it
is `--seat coder=PATH` (which also covers `property_designer`). The
prereg and ladder scripts were corrected to use `coder` before any run,
recorded in commit `2aa317d1`.

**Pre-enrichment Phase 3 baseline**, captured before Phase 1 could add
any roots (`0ad1cefb`): 48 committed roots, `attack_edge_density =
0.013354` (sum of attack edges / sum of nodes across the corpus),
`mean_cycle_count = 6.212` (over the 33/48 roots whose `run-status.json`
carries a `cycle` field — the rest predate that field). 11/48 roots
predate the RunManifest v6 schema and are unopenable by any script using
`Harness(root, read_only=True)` — same treatment O1's own `overlay_common
.open_root` already gives them (confirmed: they error the same way in a
byte-for-byte comparison against O1's own committed
`overlay_results.jsonl`). A secondary methodology note: a fresh
`run_all_overlays.py` re-run is **not byte-reproducible** against O1's
committed file — 37/48 rows differ, but only in JSON list ORDER (Python's
hash-randomized `set()` iteration order across separate processes),
never in content. Confirmed by hand on one root: identical counts, edges,
and SCC membership once compared as sets rather than as raw list order.
Comparisons in this pilot are always done on canonicalized summaries,
never raw diffs, for exactly this reason.

**Phase 2 sizing.** A dry run of `phase2_patrol.py` against the
pre-enrichment corpus (49 roots — Phase 1's first run had already landed
one root by the time this ran) found 6426 candidate pairs (6065
historical, 361 already-enriched), with 938 accepted artifacts excluded
as unaddressed (no `state.addr` problem entry, so no locality signal).
11 roots were unopenable, matching Phase 3's own count exactly. The
patrol mechanism was smoke-tested on one real pair before committing to
the full run: a genuine-sounding candidate contradiction was found on
the very first pair tried (Rule 90 width-8/10 pass/fail claims from two
different problems in the same root) — auth, endpoint, and JSON parsing
all confirmed working end to end.

## 2026-08-08 — Phase 1 failure ledger (budget: 10)

The cloud container has rolled back or reaped detached background
processes **three times** in this tranche's Phase 1 window so far, each
inside a 15-30 minute span — a documented risk (CLAUDE.md's
"Environment" section) that turned out to recur far more often than a
single-incident read would suggest. Recovery method each time: read the
record before touching anything (`run-status.json`, `progress.jsonl`,
`log.jsonl`'s tail, `verify_root`, and — critically — whether the dead
process's PID is actually gone via `ps -p`) before deciding whether a
root is salvageable or must be discarded.

- **Failure #1** — `base-q01`'s `continue --budget cycles=2` step was
  killed mid-flight. Diagnosis: `run-status.json`/`progress.jsonl` were
  stale (`state: "running"`), but `log.jsonl` (1369 events) ended in the
  standard clean-stop signature (`lifecycle_stopped` then
  `terminal_committed`, seq 1367-1368, timestamped 22:21:05Z — exactly
  matching the requested 10+2=12 cycle budget). `verify_root`:
  replay_valid=true, before AND after removing six stale lock files
  whose owning PID (26937) was confirmed dead. **Outcome: root is real
  and complete** — committed as-is (`9e05622a`), run-status.json's
  staleness left uncorrected (never hand-edited a cache file to make it
  agree with my own reading; the log is what I cite as evidence, not my
  patched version of the summary).
- **Failure #2** — the first retry of `base-q13` was killed at cycle 3.
  Diagnosis: `verify_root` came back **replay_valid=false** (6
  foreign-criticism violations — a genuinely invalid mid-state, not a
  stale-cache illusion), and the log's tail sat inside an active
  `contract_decomposition_activated`/`work_transition` sequence — the
  EXACT shape CLAUDE.md already names as a known crash risk for
  `continue` (S6's P3: "continue can crash resuming a mid-decomposition
  stop"). Given that specific documented risk plus this tranche's own
  rule against touching `src/` to fix anything, the root was confirmed
  never-committed (`git log --all`: no history) and discarded rather
  than resumed.
- **Failure #3** — the SECOND retry of `base-q13` was also killed, at
  cycle 3, again `replay_valid=false`, again never committed, again
  discarded. Same diagnosis, same disposition.

**Root cause identified after failure #3, not just patched around**: a
raw OS-level detached process (`setsid nohup ... & disown`) is not
surviving in this container between tool-call turns, independent of
whether any run-level event triggers it — the pattern held even with no
visible container-rollback signal in between. Strategy changed
accordingly: Phase 1's remaining questions now run one at a time as a
harness-TRACKED background Bash call (`run_in_background: true`) inside
this session, rather than a raw detached shell driver. This is watched
directly by the tool layer (a completion notification arrives
automatically) instead of relying on a Unix process surviving on its
own, which is the mechanism that kept failing. `base-q13` is retrying
under this new mechanism now; further progress is appended below.

## 2026-08-09 — first non-crash finding: budget_exhausted stops can land replay_valid=false

`hard-h01`'s first `reason` call completed cleanly (`reason_rc=0`, state
`completed`, `stop_reason: budget_exhausted`, no process interruption
involved at all) — but `verify_root` still returned `replay_valid:
false`, citing two accepted artifacts with `foreign-criticism: 0 foreign
schools; policy requires 1`. Checked whether this was somehow caused by
this tranche's own coder-seat binding before treating it as a general
harness fact: `llm_calls_by_role` on this root shows ONLY
`argumentative_critic`/`conjecturer` on `glm-5.2` — `gemma4:31b` never
fired (consistent with the coder/encoder dead-seat finding), so the
seat binding is not the cause. This matches a pattern already named in
CLAUDE.md/S6's own RESULTS.md ("foreign-criticism verify violations
...  at natural stop points") for a different root cause (there,
gemma4:31b-as-conjecturer outpacing the critic) — here the same
SYMPTOM shows up for the mundane reason CLAUDE.md's own Live-runs
section predicts: a budget ceiling can be hit before every accepted
claim has accumulated its required cross-school criticism. This is not
evidence corruption and not a crash; it is the intended trigger for the
prereg's own resume policy (`continue --budget cycles=2` on any
`budget_exhausted`/`converged` stop) — applied here exactly as
pre-registered, not as an improvised workaround.

**Update 2026-08-09**: by hard2-h2-15 (the 8th of 10 questions), 5 of the
8 completed first-`reason`-call stops hit this same `replay_valid=false`
foreign-criticism gap (base-q13, hard-h05, hard-h10 stayed clean on the
first stop; hard-h01, hard-h15, hard2-h2-01, hard2-h2-08, hard2-h2-15 did
not). This is the NORM for this cycles=10/token-budget=180000
configuration, not an edge case — every instance closed cleanly with one
`continue --budget cycles=2` top-up, consistent with the prereg's own
resume policy, applied identically each time.

## 2026-08-09 — Phase 2 patrol underway

Post-enrichment pairing plan: 58 corpus roots (47 openable, 11
unopenable — same pre-v6-schema roots Phase 3's baseline already
excluded), **9277 pairs** (6065 historical, 3212 enriched — Phase 1's
10 new roots contributed disproportionately more pairs per root than
the historical average, since every enriched root has a single
locked-in problem with many accepted claims, while historical roots
often address several problems each with fewer claims per group).
1275 accepted artifacts excluded as unaddressed.

Running in bounded, resumable chunks (`--max-calls=N`, resume-by-scan
of already-answered pairs) rather than one continuous call — the same
adaptation Phase 1 needed, since a single ~5-hour call is a much larger
target for the container's demonstrated instability than a chunk of a
few thousand. **Chunk 1** (300 calls, ~13 minutes including one-time
corpus-opening overhead): 109 hits, 1 parse failure. **This is a much
higher candidate-hit rate than expected (36%)** — sanity-checked before
trusting it and continuing: the first several hits are all from one
root (`2026-08-02-stress-triplet/home-orbit`, a Wolfram-rule cellular-
automaton problem) where two accepted claims make literally opposite
factual assertions about the same rule/width pair ("Rule 184 fails the
criterion and is nonlinear" vs "Rule 184 passes and is linear," same
problem, same root). These read as genuine candidate contradictions,
not classifier noise — the mechanism is doing what it was built to do.
Whether the 36% rate holds corpus-wide or is concentrated in a few
noisy roots is exactly what the per-root/per-half breakdown in the
final decision table will show; not assumed here.

## 2026-08-09 — Phase 2 patrol complete: decision numbers

All 9277 pre-registered pairs checked (zero skipped, zero silently
dropped; 0 API transport errors; the resumable-chunk mechanism survived
two more container interruptions cleanly — every chunk's partial output
was a valid prefix, since `patrol_results.jsonl` is written one
complete, flushed JSON line at a time, never a torn write).

| | pairs | hits | rate | parse failures |
|---|---|---|---|---|
| **Overall** | 9277 | 1941 | **20.9%** | 143 (1.5%) |
| Historical half | 6065 | 1133 | 18.7% | 113 |
| Enriched half | 3212 | 808 | **25.2%** | 30 |

The enriched half's candidate-contradiction rate is meaningfully higher
than the historical half's (25.2% vs 18.7%). This pilot cannot say
WHY on its own — plausible readings include: the hard/hard2 questions
chosen for Phase 1 genuinely produce messier claim sets than the older
corpus's average question, OR the newer roots simply have larger
per-problem accepted-claim groups (more claims addressing the exact
same problem gives the pairing rule more same-topic material to find
tension in), OR both. Distinguishing these needs a follow-up pilot with
matched question difficulty across old and new roots — out of this
pilot's scope, named here as residue, not resolved.

Hits are spread across the corpus, not concentrated in one degenerate
root: 43 of 47 openable roots contributed at least one hit. The top 5
roots by hit count account for 620/1941 (32%) — real concentration, but
not a single-root artifact. Full hit list (root, problem, both artifact
ids, confidence, one-line reason) committed verbatim at
`patrol_hits.jsonl` (1941 rows) — not pasted here per the "hits are
candidate measurements, never edges" framing; nothing in this file was
or will be written into any root.

**Framing, restated as bound**: every one of these 1941 rows is a
CANDIDATE — a same-problem pair the model itself flagged as mutually
inconsistent when asked directly, nothing more. No adjudication ran. No
root was touched. Turning any of these into an actual attack edge would
require running them back through the harness's own criticism machinery
— that is exactly the "future criticism" this pilot's own framing
reserves them for, not something this tranche did or should do.

## 2026-08-09 — Phase 3 complete: overlay comparison, old vs new

Ran O1's `run_all_overlays.py` unmodified, same method as the
pre-enrichment baseline (copy output aside, restore O1's committed file
byte-for-byte — verified clean via `git status` both times).

| | pre-enrichment (48 roots) | post-enrichment (58 roots) | delta |
|---|---|---|---|
| Total claims (nodes) | 1947 | 2932 | +985 |
| Total attack edges | 26 | 37 | +11 |
| **Attack-edge density** (edges/nodes) | 0.013354 | 0.012619 | **-5.5% relative** |
| **Mean reasoning-cycle count** per root | 6.212 (33/48 roots) | 7.186 (43/58 roots) | **+15.7%** |
| Genuine unresolved controversy (SCCs) | 0 | 0 | unchanged |
| Floating (disconnected) claim components | 2690 | 3965 | +1275 |
| Roots with a resolvable warrant-sensitivity read (O1d) | 37 | 47 | +10 (all new roots resolved) |

**Reading these plainly.** Adding 10 harder questions grew the claim
pile by about half (1947→2932) but did NOT make the argument structure
proportionally more contentious — attack-edge density went slightly
DOWN, not up, and the count of claims genuinely stuck in unresolved
back-and-forth stayed at exactly zero in both the old and new corpus.
What DID change: the new runs took noticeably more reasoning cycles on
average (7.186 vs 6.212) — expected, since 6 of the 10 needed the
prereg's own `continue` top-up, and the older corpus's average run
predates some of those same policy checks. The floating-claims count
grew by exactly 1275 — the SAME number as Phase 2's own
"unaddressed-accepted-artifacts-excluded" count from its dry run. This
is a striking coincidence WORTH FLAGGING but NOT claimed as the same
fact: O1c's "floating" measure is about missing `dep`/`att` graph edges
(a claim that neither supports nor attacks anything), while Phase 2's
"unaddressed" count is about a missing `addr` (problem) link — two
different relations in the same record that COULD correlate (a claim
disconnected from the argument graph is plausibly also less likely to
carry a problem address) without being identical. Confirming or
refuting that correlation is residue, not resolved here.

## 2026-08-08 — Phase 1 progress (running table, updated per root)

| run id | question tier | status | cycles | accepted | candidate_checker_count | notes |
|---|---|---|---|---|---|---|
| base-q01 | base | committed | 12 (10+2 continue) | 110/113 | 0 (expected, P-CEPP-1) | recovered from failure #1, see above |
| base-q13 | base | committed | 10 | 93/94 | 0 (expected) | 3rd attempt succeeded under tracked-background strategy (task beb9axlw2) |
| hard-h01 | hard | committed | 12 (10+2 continue) | 95/97 | 0 (expected) | continue closed the foreign-criticism gap, see note above |
| hard-h05 | hard | committed | 10 | 91/91 | 0 (expected) | clean on first stop |
| hard-h10 | hard | committed | 10 | 83/85 | 0 (expected) | clean on first stop |
| hard-h15 | hard | committed | 12 (10+2 continue) | 99/100 | 0 (expected) | second foreign-criticism-gap case, closed by continue same as hard-h01 |
| hard2-h2-01 | hard2 | committed | 12 (10+2 continue) | 95/95 | 0 (expected) | third foreign-criticism gap case, closed by continue |
| hard2-h2-08 | hard2 | committed | 12 (10+2 continue) | 100/100 | 0 (expected) | fourth foreign-criticism gap case, closed by continue |
| hard2-h2-15 | hard2 | committed | 12 (10+2 continue) | 115/116 | 0 (expected) | fifth foreign-criticism gap case, closed by continue |
| hard2-h2-22 | hard2 | committed | 12 (10+2 continue) | 93/94 | 0 (expected) | sixth foreign-criticism gap case (final question), closed by continue |

**Phase 1 complete: 10/10 questions committed.** All zero on
`candidate_checker_commitment_count` and on `encoder_calls`/
`property_designer_calls` (P-CEPP-1, expected throughout). Failure
ledger: 3 spent (container/process deaths; see above). 6 of 10 first
stops needed one `continue --budget cycles=2` top-up for a
foreign-criticism gap; all 6 closed cleanly on the first try, 0 needed a
second.

## 2026-08-09 — DELIVERY: decision table, prereg conformance, residue

### Decision table

| Metric | Value |
|---|---|
| Phase 1 questions run | 10/10 committed (2 base, 4 hard, 4 hard2) |
| Phase 1 failure budget spent | 3/10 (all container/process deaths, none data-losing) |
| Dual-mode (`conjecturer.turn.v7`) commitments | 0/10 roots — expected, P-CEPP-1 (v7 has no live opt-in; encoder role has zero callers regardless) |
| Phase 2 pairs checked | 9277/9277 (100%, 0 API errors, 143 parse failures = 1.5%) |
| Phase 2 candidate-contradiction rate, overall | **20.9%** (1941/9277) |
| Phase 2 candidate-contradiction rate, historical half | 18.7% (1133/6065) |
| Phase 2 candidate-contradiction rate, enriched half | **25.2%** (808/3212) |
| Roots contributing at least one hit | 43/47 openable (91%) |
| Phase 3 attack-edge density, old → new | 0.013354 → 0.012619 (-5.5% relative) |
| Phase 3 mean cycle count, old → new | 6.212 → 7.186 (+15.7%) |
| Phase 3 unresolved-controversy count, old → new | 0 → 0 (unchanged) |
| Phase 3 floating-claim components, old → new | 2690 → 3965 (+1275) |

### Prereg conformance, deviation-by-deviation

1. **Dual-mode ("Dual-mode ON")** — NOT honored as literally instructed.
   `conjecturer.turn.v7` has no working opt-in for any live run
   (`V6_BEHAVIORAL_REPAIR_GRANT_REQUIRED`, confirmed by direct
   construction). Recorded BEFORE Phase 1 launch, parked as P-CEPP-1,
   Phase 1 ran on the harness default (v6) instead. This was the single
   largest deviation from the task's own instructions and was reported
   to the operator before any Phase 1 compute was spent, not discovered
   after the fact.
2. **"Encoder seat"** — the task named a seat group that does not exist
   (`--seat encoder=...`); corrected before launch to the real group
   (`--seat coder=...`, which covers both `property_designer` and
   `encoder` roles). Recorded in the prereg and the launch commit.
3. **Topical-neighborhood rule** — used problem-address locality
   (`state.addr`) only, not refs-based locality. A deliberate
   simplification named in the prereg BEFORE Phase 2 launch, parked as
   P-CEPP-2, not a discovered gap.
4. **Resume policy** — applied exactly as pre-registered
   (`continue --budget cycles=2` once per `budget_exhausted`/`converged`
   stop); 6/10 Phase 1 roots needed it, all 6 closed cleanly on the
   first application, 0 needed a second.
5. **Chunked Phase 2 execution** — the prereg did not anticipate
   splitting the patrol into resumable chunks; this was an operational
   adaptation forced by repeated container/process interruptions (see
   the failure ledger), not a change to the patrol's own rules (sampling
   rule, narrow question, output contract, and hit threshold were never
   touched mid-run).
6. **O1 overlay re-run's methodology note** — a fresh
   `run_all_overlays.py` invocation is not byte-reproducible against a
   prior run (Python's hash-randomized list ordering); comparisons here
   were always made on canonicalized counts, confirmed identical-content
   on a hand-checked sample before trusting the pattern for the rest.

Nothing else in `prereg.yaml` was deviated from: the run matrix, budgets
per run, narrow pair-contradiction question (verbatim, frozen before
Phase 2's first call), output contract, and candidate-hit threshold
(confidence >= 0.6) were all used exactly as registered.

### What this pilot proves, and what it cannot claim (the residue)

**Proven, by the typed record:**
- The consistency-patrol MECHANISM works end to end: a bounded,
  single-call, strict-JSON-contract question reliably surfaces
  plausible same-problem contradictions between claims a harness run
  separately accepted, at meaningful volume (1941 candidates from 9277
  checks) and at acceptable parse-failure cost (1.5%).
- Harder/newer material (this tranche's enriched half) shows a
  measurably higher candidate-contradiction rate than the historical
  average (25.2% vs 18.7%), without a corresponding increase in the
  harness's own structural "attack density" or genuine unresolved-
  controversy count — the patrol is catching something the harness's
  existing machinery does not already flag on its own.
- Dual-mode/candidate-checker delegation is confirmed, not assumed,
  unreachable in the current codebase for any live run — a concrete,
  reproducible defect handed off as P-CEPP-1 with the exact file/line
  and the exact fix shape needed.

**What a pilot this size cannot claim:**
- WHY the enriched half's rate is higher (question difficulty vs.
  claim-group size vs. both) — residue, needs a matched-difficulty
  follow-up, not resolved here.
- Whether the 1941 candidate hits are TRUE contradictions in any
  stronger sense than "the model, asked once, said so" — no adjudication
  ran, no root was touched, and the task's own framing forbids treating
  a hit as anything but a candidate for FUTURE criticism. Confirming any
  individual hit would require running it back through the harness's own
  criticism cycle, which this tranche deliberately did not do.
- Whether the floating-components/unaddressed-artifacts correlation
  (both +1275) is a real relationship or coincidence — flagged, not
  chased.
- Generalization beyond these specific 10 questions and this specific
  47-root corpus slice — a pilot decision-number set, not a claim about
  the harness's behavior in general.

All roots, raw patrol responses (`patrol_results.jsonl`, `patrol_hits.jsonl`),
and both overlay sweeps (`phase3/overlay_results_pre_enrichment.jsonl`,
`phase3/overlay_results_post_enrichment.jsonl`) are committed verbatim
under this tranche's directory. Stop condition met: decision table
complete, pushed.

## 2026-08-09 — Correction: the patrol's judgment step is not deterministic

Raised by the operator, and worth stating plainly rather than leaving
implicit: **this pilot's infrastructure is deterministic; its finding
mechanism is not**, and the delivery above did not say so clearly
enough.

What IS deterministic: the claim PAIRS fed into Phase 2. Every accepted
claim comes from an append-only, replay-verifiable record — re-opening
any committed root reproduces byte-identical claim text every time
(`verify_root`'s whole job). So the INPUT to every one of the 9277
patrol calls is fixed and reproducible, permanently.

What is NOT deterministic: the JUDGMENT that a given pair contradicts.
Each judgment came from one AI model call at temperature 0 (the setting
that minimizes response variance) — but temperature 0 reduces
variability, it does not guarantee bit-for-bit reproducibility; large-
model inference is not generally guaranteed deterministic even at
temperature 0. This was never tested directly: no pair in this pilot
was asked twice to check whether the model gave the same verdict both
times.

**Correct framing of the 1941 hits**: they are what ONE non-deterministic
pass of judgment found over a fixed, reproducible set of claim pairs —
not a provably complete or stable set of contradictions. A second pass
under identical settings could plausibly find a somewhat different set;
probably heavily overlapping for the clear-cut cases (opposite numbers,
direct negations) shown in the family typology above, but not
guaranteed identical. This is the same caveat this codebase's own
documentation already states for capability-channel use generally
("stochastic across identical runs; one live attempt is inconclusive on
its own") — it was true of Phase 2 from the start and should have been
stated here explicitly rather than left for the operator to surface.

## 2026-08-09 — Addendum: semantic-similarity cross-check (operator-requested)

Not part of the original pre-registration; added after delivery to give
the non-deterministic Phase 2 judgment an independent, fully
deterministic cross-check, using DeepReason's own embedding machinery
(`deepreason.llm.embedder`) rather than another LLM call. Two embedders
run over all 9277 pairs Phase 2 already scored: `HashingEmbedder`
(lexical, zero-dependency, exactly deterministic) and
`NeuralEmbedder(BAAI/bge-small-en-v1.5)` (semantic, ONNX/fastembed,
CPU-only, no API calls, deterministic within this environment — the
module's own documented caveat is cross-environment reproducibility,
not this-run reproducibility). Completed in ~3 minutes, 0 errors.

| | hits (n=1941) | non-hits (n=7336) |
|---|---|---|
| Lexical similarity (hashing), mean | 0.546 | 0.478 |
| **Semantic similarity (neural), mean** | **0.895** | **0.845** |
| Semantic similarity, stdev | 0.043 (tight) | 0.080 (wider) |

**Reading this plainly.** Every pair in this pilot was already
constrained to share a problem (Phase 2's own sampling rule), so
baseline similarity is elevated everywhere — this was never a test of
"are these about the same thing at all." The real signal is that
LLM-flagged hits cluster measurably tighter and higher (mean 0.895,
narrow spread) than non-hits (mean 0.845, wider spread) on the fully
deterministic semantic measure, and the lowest similarity found among
ALL 1941 hits was still 0.706 — no hit was a weakly-related, likely-
spurious pairing by this independent measure. There's also a moderate
positive correlation (r=0.399) between the LLM's own stated confidence
and this deterministic similarity score AMONG the hits themselves — the
more confident the (non-deterministic) judge was, the more topically
tight the (deterministic) embedding says the pair is. That correlation
would not be expected to exist if the LLM's contradiction calls were
close to random noise with respect to the actual claim content.

**What this does and does not prove.** This corroborates that Phase 2's
hits are, as a population, sitting where genuine same-topic
disagreements should sit — not scattered randomly across the similarity
range the way arbitrary/hallucinated pairings would be expected to.
It does NOT independently verify any single hit's TRUTH (an embedder
measures relatedness, not truth-value polarity — two claims that
straightforwardly AGREE would also show high similarity; similarity
alone cannot distinguish "same topic, agree" from "same topic,
disagree"). It also does not test the non-determinism question directly
— no pair was asked twice — it tests a different, complementary
question: is the population of hits topically coherent, or the mechanism
finding noise. Raw output: `semantic_crosscheck.jsonl` (9277 rows, both
similarity scores per pair, committed verbatim).
