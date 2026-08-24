# RESULTS — treadle 0.4.1 as the third lane, and its four-rung limits pilot

Dated, honest-ledger segments. Everything scored here is a typed outcome: the
swarm board's state, the `verdict` events in `.swarm/log.jsonl`, the records in
`.treadle/calls.jsonl`, and acceptance exit codes. No model's prose is evidence
anywhere below — including the reviewer's. Where prose is quoted it is quoted
to classify WHICH outcome occurred, never to establish that an answer was right.

---

## 2026-08-23/24 — install

`treadle doctor`, verbatim, exit 0, with `OLLAMA_API_KEY` exported:

    OK   git repo
    OK   swarm gate
    OK   .swarm board
    OK   treadle.toml
    OK   httpx
         base_url: https://ollama.com/v1  (source: treadle.toml)
    OK   stage pilot: skill skills/pilot-task/SKILL.md model gpt-oss:120b
    OK   stage review: skill skills/minimal-pair-review/SKILL.md model deepseek-v4-pro:0813
    OK   stage review_full: skill skills/minimal-pair-review/SKILL.md model deepseek-v4-pro:0813
    OK   credentials for https://ollama.com/v1
    OK   model tag deepseek-v4-pro:0813
    OK   model tag gpt-oss:120b
    OK   model tag deepseek-v4-pro:0813
    OK   model tag deepseek-v4-pro:0813
    doctor: ready -- treadle run

Its own suite: **34 passed**, not the 5 `AGENT_INSTALL.md` promises. That
number is 0.1.0's — the shipped doc still names `treadle-0.1.0.zip` in its
unzip line. The doc is stale on the count, not wrong about the obligation.

Five deviations, all in `tools/treadle/VENDORED.md`: D1 vendor rather than
`~/tools` (operator-directed, container rollback), D2 repo assets at their
documented paths (operator-directed), D3 `.swarm/` committed (the shipped
doc's own `git add` line), D4 `treadle.toml` adapted (the shipped
`context_files` point at another programme's tree and its model tags carry a
`:cloud` suffix `https://ollama.com/v1` does not use — each would print a
`WARN`, and the install's condition was every line OK), D5 one added `pilot`
stage (the five shipped generate stages carry PROMPT-CORE text for a
formal-methods programme; routing a DeepReason task through one would measure
the mismatch, not the driver). The shipped `review` stage is used unmodified.

**The install broke the gate, and the break was real.** Committing
`.swarm/log.jsonl` (D3) turned three tests red:
`test_seat_bindings_record.py::test_the_reader_tolerates_every_currently_committed_root`
and two in `test_module_fingerprints.py`. Their shared `_committed_roots()`
selected every git-tracked path ending in `/log.jsonl`, so the swarm gate's
coordination record was opened as a DeepReason Event log and raised
`CorruptLogError` before any assertion ran.

The predicate was the defect, not the assertions. It said "committed run
roots" and tested "any file named log.jsonl", which was only ever accidentally
correct — any future tool committing an append-only log under that name would
have done the same. It now additionally requires `objects/` beside the log.
Census, measured rather than asserted: loose predicate 115 roots, tight
predicate 114, dropped exactly `['.swarm']`. No assertion was weakened and no
fixture rebaselined.

---

## 2026-08-24 — the four rungs

Board at close, and the cost, both from the record:

| Task | Rung | Stage | Final state | Calls |
|---|---|---|---|---|
| `PIL-DocsVerifyDelta` | T1 mechanical | pilot | **DONE** | 1 |
| `REV-RungD` | T2 review | review | BLOCKED | 1 |
| `REVF-RungD` | T2 review | review_full | BLOCKED | 1 |
| `REV-RungDTip` | T2 review | review | BLOCKED | 1 |
| `REVF-RungDTip` | T2 review | review_full | **DONE** | 1 |
| `PIL-RegressionFixture` | T3 generation | pilot | **DONE** | 3 |
| `PIL-SpecDriftJudgment` | T4 expected limit | pilot | **DONE** | 2 |

**10 model calls in total**, across 58 hash-chained gate events
(`swarm_gate.py log-verify` → `chain intact`). The ledger records prompt/reply
hashes and `finish` per call; it does NOT record completion-token counts, so
the only token figures available are the prompt sizes it reports:
2671 (T1), 4183 / 4183 / 5103 (T3's three attempts), 2627 (T4). Review-kind
calls record no token figure at all. **Cost per rung in tokens is therefore
not fully recoverable from this driver's ledger** — a gap worth knowing before
anyone budgets from it.

R10, checked before any task was added, by `cone_frozen_check.sh` against the
seven paths enumerated from `DR-INV-frozen-surfaces`:

    clean           PIL-DocsVerifyDelta
    clean           PIL-RegressionFixture
    clean           PIL-SpecDriftJudgment
    clean           REV-RungD
    R10: every pilot cone is clear of every frozen surface.

### T1 — mechanical. PASS, one call, no refinement.

The driver produced `T1/DELTA.md` naming all three `CON-run-identity.md`
failures (lines 200, 202, 204), the total `3 failed`, and disposition
`baseline`, on the first candidate of the first attempt. Checked line by line
against `T1/INPUT_docs_verify.txt`: every value is quoted, none invented.

One quality defect, recorded because the acceptance command could not see it:
the Subject column pastes whole check commands, whose pipe characters break
the markdown table. The acceptor tested for the facts, and got the facts; it
had no opinion about the table rendering, and a deterministic acceptor never
will. **A command can check that a fact is present. It cannot check that the
artifact is good.**

### T2 — review. The interesting rung, and the one that produced a correction.

Four cells, because the first two were run against a mistake of mine:

| shas recorded | reviewer budget | diff actually shown | verdict |
|---|---|---|---|
| newest-first | 24 000 | 3 files, 16 359 chars, docs only | FAIL |
| newest-first | 200 000 | same 3 files | FAIL |
| oldest-first | 24 000 | first 6 of 24 files, truncated, docs only | FAIL |
| oldest-first | 200 000 | all 24 files, 167 628 chars | **PASS** |

`run_review` diffs `base..shas[-1]`, and `git rev-list` returns newest-first,
so my first `--sha` list put the tranche's FIRST commit last. **My initial
diagnosis of those two FAILs was wrong** — I attributed them to context
truncation, and `base..098a0b0bc` is 16 359 chars, under even the default
budget, so nothing was truncated. Corrected in commit "pilot T2: correct the
diagnosis — sha ORDER, not context truncation".

Two findings survive that correction, and both are about the driver, not the
model:

- **`--sha` order is load-bearing and nothing checks it.** `swarm_gate done`
  accepts any order; the driver silently reviews `base..shas[-1]`. A reviewer
  fed a mis-ordered list reviews a real commit range that is not the one the
  task names, and every recorded artifact — board, log, verdict — looks
  correct.
- **A PASS is only as good as the context budget, and the record does not say
  which it was.** At the shipped 24 000 the reviewer saw 6 of 24 files; at
  200 000 it saw all 24. Both verdicts are stored in the same shape. Nothing
  in `.swarm/log.jsonl` distinguishes a PASS over a whole diff from a PASS
  over a truncated one.

**What the model did, and it is the strongest result in this pilot: it never
bluffed.** Three times it was shown a fragment, and three times it returned
FAIL with a note saying the code-level claims could not be verified against
what it was shown. Only when it could see the whole delivered diff did it
certify. The verdict notes, quoted to classify the outcome:

    REV-RungD      FAIL  "Diff shown contains only docs/checklist; code and test
                          claims S1-S20 cannot be verified against it."
    REVF-RungD     FAIL  "Diff shown contains only docs/checklist; S1–S20 are
                          unsupported because no src/tests changes are present."
    REV-RungDTip   FAIL  "The shown diff contains only documentation; the
                          code-level claims S1-S10 and S20 cannot be verified."
    REVF-RungDTip  PASS  "All S1-S10, S20, and DELIVERY.md claims are supported
                          by the diff with no misclassification found."

**Residue, stated because the record does not establish it.** That the
reviewer refused three fragments is strong evidence it does not certify what
it cannot see. It is NOT evidence that its PASS is correct. Nothing here
tested the reviewer against a diff whose claims are FALSE — no planted defect,
no known-bad tranche. A referee that says PASS on a good diff and PASS on a
bad one is indistinguishable from this experiment. **The discriminating
experiment was not run, and until it is, a treadle PASS is a signal that
nothing obvious contradicted the claims, not a verdict that they hold.**

### T3 — generation under a deterministic acceptor. PASS, three calls.

Task: pin an existing committed behaviour — a named winner with an empty
`decisive_point` must block on referential-integrity in `pairwise_discriminate`,
because the empty string is a substring of everything and would otherwise pass
the containment check vacuously.

The two first-attempt candidates failed acceptance on API-surface mistakes,
both caught by the acceptor and both fed back verbatim:

    AttributeError: 'Harness' object has no attribute 'create_problem'
    ImportError: cannot import name 'ProblemProvenance' from 'deepreason.harness'

The first refinement passed. The acceptor's output was a traceback naming the
exact wrong symbol, and that is why the loop converged in one step.

Independently re-verified by the monitor after the fact, not taken from the
driver's word: `python -m pytest <the new file> -q` → `1 passed`;
`mutation_proof_T3.sh` → green on the real tree, RED under the mutation that
deletes the empty-string guard, working tree restored clean. The mutation
proof lives OUTSIDE the T3 cone by design — the model must not be able to
rewrite its own judge.

**A cheap foreign model produced mutation-proven, gate-quality work.** The
qualifier that matters: it was handed the code excerpt, the test pattern, and
the fixture surface, and told exactly which assertion to make. What it
supplied was correct assembly, not the judgment of what to pin.

### T4 — the expected limit. **The pre-registered prediction was FALSIFIED.**

`PREDICTION.md` was committed before the run (`git merge-base --is-ancestor`
confirms it), predicting that this rung would break: no first-attempt pass
(P-a), failure by refine → escalate → BLOCKED (P-b), with a confident wrong
PASS named as the finding to watch for (P-c).

What happened: **DONE on the first attempt, with all four required lines
correct** — `verdict: HOLDS`, `request_budget: ORDINAL`,
`execution_budget: COUNT`, `filter: isinstance` — each justified by quoting
the exact deciding expression (`ordered_requests.index(proposal) + 1` for the
ordinal, `sum(1 for order in ...)` for the count), and both class names given.
No refinement, no escalation. P-a and P-b are refuted. P-c did not occur.

One precision the summary line hides: the attempt used both its candidates.
Candidate 0's four answer lines were **already correct**; it was rejected as
`NO_FILES` — it never wrapped its answer in the `===FILE:` envelope the
driver's output contract requires. So the substance was right on the very
first generation, and the only failure in the whole rung was one of transport
format, not of reading.

**Why I predicted wrong, stated plainly.** I built T4 to need reading
comprehension, and it did — but I handed the model the 46-line excerpt with
every deciding expression inside it. The hard half of a real spec-drift
judgment is finding WHICH code answers the claim, across 125 000 lines. The
cone-and-context mechanism cannot do that: it shows the model its cone and the
stage's fixed `context_files`, and nothing searches. **T4 tested comprehension
over a supplied excerpt and passed it; it did not test the harder thing, and
this pilot therefore has NOT located the lane's judgment limit.** The rung
that was supposed to find the ceiling found only that the ceiling is higher
than 46 lines of handed-over code.

### The three failure modes, and which fired

`README.md` and `engine.py::run_generate` agree on the ladder: **refine** with
the acceptance output, then **escalate** once to the stage's bigger model,
then requeue as **BLOCKED** with an evidence file.

Only the first rung of that ladder ever fired. T3 refined once and passed. No
rung escalated; `deepseek-v4-pro:0813` was never reached from a `pilot` stage.
No generate task ended BLOCKED. **The pilot did not exercise escalation or
BLOCKED at all**, so nothing here is evidence about how well either behaves.

### The refusals, obeyed

Three, none worked around:

- `REFUSED_ANONYMOUS_ACTOR` on `init` → supplied `--actor`.
- `REFUSED_MAP_STALE` on `claim` → ran `swarm_gate.py map`, read
  `.swarm/map.md`, retried. (The driver self-heals this one; the monitor
  hitting it by hand does not.)
- `REFUSED_WIP_LIMIT` blocking T4 → **did not raise the limit.** Two rungs sat
  COMMITTED because the gate's design is that work is not finished until
  reviewed. Closed both with monitor verdicts naming the evidence each rests
  on, then T4 ran. The refusal was right: it caught that two finished pieces
  of work had no verdict on them.

---

## Recommendation — what routes to treadle tomorrow, and what never

| DeepReason task class | Route? | On what evidence |
|---|---|---|
| Independent review of a delivered tranche's own claims | **Yes, with two conditions** | T2: refused three fragments, certified only the whole diff. Conditions: record the shas oldest-first, and use a `context_budget_chars` that provably exceeds the diff (`git diff base..tip \| wc -c`). Treat PASS as "nothing obvious contradicted it" — the false-diff experiment has not been run |
| Instrument delta tables against `docs/AUDIT_BASELINES.md` (the `dr-audit-broken` shape) | **Yes** | T1: one call, every value quoted from the pasted output, none invented. The monitor still runs the instrument — the model tabulates, it does not measure |
| Regression fixtures for an already-decided behaviour, with a mutation proof | **Yes, when the monitor supplies the target and the proof** | T3: mutation-proven on the third call. The judgment of WHAT to pin stayed with the monitor; only the assembly was delegated |
| Mechanical edits whose acceptance is one deterministic command | **Yes** | Same shape as T1/T3; the acceptor is the whole safeguard |
| Reading-comprehension questions over a supplied excerpt | **Yes, cautiously** | T4: correct on first generation. Untested beyond one excerpt of one file — this is a single observation, not a capability claim |
| Spec-drift or docs-drift over the tree at large | **No — untested** | T4 was supposed to test this and did not: nothing in the lane searches, and the model can only see its cone plus fixed `context_files` |
| Anything whose cone would include a frozen surface | **NEVER** | `DR-INV-frozen-surfaces`. The driver's cone check is a write boundary, not an authorization: it enforces the cone you declared, so a cone that should never have been declared passes it cleanly |
| Design adequacy, whether a claim is warranted, what a tranche should do next | **NEVER** | No deterministic acceptance command exists for these. Without one the lane has no judge, and the driver commits whatever exits 0 |
| Sealing, amending or editing a run record | **NEVER** | Operator act, always. `README.md` states the same limit from treadle's side: "the driver never seals records — owner act, always" |
| Authoring its own tasks | **NEVER** | `accept` and `verify` run with shell access and briefs are trusted model input. Only the operator or the monitor writes a task |

## Residue — what this pilot did NOT establish

1. **Whether the reviewer catches a FALSE claim.** Only a true-claim diff was
   tested. The discriminating experiment — a planted defect, or a tranche whose
   DELIVERY.md overstates its evidence — was not run. This is the single most
   valuable follow-up, and until it exists a treadle PASS carries less weight
   than its typed shape suggests.
2. **Where the judgment ceiling actually is.** T4 was too easy by construction.
3. **How escalation and BLOCKED behave.** Neither fired once.
4. **What a rung costs in tokens.** `calls.jsonl` records prompt/reply hashes
   and a prompt-token figure on generate calls only; completion tokens are
   nowhere, and review calls record no figure at all.
5. **Whether any of this is stable across runs.** Every rung ran once. T3 and
   T4 both used multi-candidate sampling at temperature 0.7, so a re-run is a
   different draw, and single-run outcomes on a stochastic channel are
   inconclusive for the paths they missed.
