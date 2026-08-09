# Judge-evidence review: what do committed runs prove about LLM-judge discrimination?

**The question**, in the operator's words: what do the committed runs and
experiments actually prove about LLM-judge discrimination? The operator's
own hypothesis — "they prosecute without any discernable discrimination" —
is what this document tests, not what it assumes. Every claim below carries
its source (`path:line` or a JSON field inside a named file) so the number
can be re-derived, not just trusted.

*(Executive summary is written last, after §2-§8 are evidenced — filling it
in before the sweep would decorate a conclusion instead of testing one.)*

## Contents

- §2 Judge audit machinery and its outputs (R5a)
- §3 Trial-protocol experiments (R5b)
- §4 Adjudication-blindness fix tranche, 2026-08-01 (R5c)
- §5 Stress-triplet and lambda/experiment-module runs (R5d)
- §6 EXPERIMENT_PROGRAM_2026-07.md's judge items (R5e)
- §7 Three-way scoring: incorrect / undiscriminating / over-prosecuting
- §8 Design consequence: a judge-free or judge-minimal road for solo runs

## §2. Judge audit machinery and its outputs (R5a)

### 2.0 A terminology trap this whole review has to avoid

The committed record uses two different actors that are easy to conflate
under the word "judge":

- **The argumentative CRITIC** (`argumentative_critic` role, `rules/crit.py`)
  proposes an objection. Whether that objection can change `Status` at all
  is gated by `ARGUMENTATIVE_AUTHORITY` (`docs/map/CON-authority.md`),
  which **defaults to `observe_only`** — a critic with no authority granted
  files scrutiny and mints no warrant.
- **The JUDGE** (`judge` role) is the seat that rules inside a rubric trial,
  a defended court, or one of `informal/audits.py`'s audit functions.
  Judges are what `informal/trial.py`'s order-swap/paraphrase guards
  actually govern (§3), and what `require_cross_family_judges()` gates.

Several committed reports below measure the CRITIC's raw objection rate
(near-100% on everything, clean or flawed alike) separately from the
JUDGE-mediated COURT's conviction rate (the opposite problem — very rarely
convicts). Both numbers are real and both are relevant to the operator's
worry, but they are evidence about two different mechanisms and this
section keeps them labeled separately. Collapsing them would make the
record say something it does not.

### 2.1 The audit functions themselves

`src/deepreason/informal/audits.py` (confirmed by direct read):

- `planted_flaw_calibration` (`audits.py:228`) — constructed flaws (known
  ground truth) plus clean controls scored by the judge ensemble; logs
  `judge-error-rate:<rate>` (`audits.py:267`); `rate > config.JUDGE_ERR_MAX`
  spawns an audit-the-critic problem (`audits.py:268-269`).
- `bias_probes` (`audits.py:273`) — self-preference (own-family vs foreign
  content, authorship masked) and verbosity (terse vs padded, same content)
  pairs, scored over BOTH presentation orders; logs
  `judge-self-preference:<rate>` / `judge-verbosity-bias:<rate>`
  (`audits.py:332,334`).
- `paraphrase_invariance_audit` (`audits.py:116`) — re-runs a logged rubric
  ruling on paraphrases of the same exchange; a verdict flip is a hit,
  registered as a demonstrative warrant against the ruling's validity node.
- `premise_deletion_audit` (`audits.py:184`) — deletes the ruling's own
  cited `decisive_point`; a verdict that still says `fail` after its stated
  grounds are removed is a hit.
- All four preflight `adapter.require_cross_family_judges()` before any
  other endpoint spends, and a split ensemble logs
  `audit-blocked:ensemble-split` and returns no hit (`audits.py:151-155,
  200-204, 263-264, 313-317`) — disagreement is never resolved by picking
  seat zero.

Only `paraphrase_invariance_audit` has a production call site
(`scheduler.py`, per `docs/map/SUB-evaluation.md` line 124); the other
three run only from tests and operator-invoked scripts. This matters for
§7: the record below is overwhelmingly from **stand-alone script-run
experiments** (`scripts/judge_battery.py`-style harnesses under
`experiments/`), not from `paraphrase_invariance_audit`/
`premise_deletion_audit`/`planted_flaw_calibration`/`bias_probes` firing
inside a normal scheduled run's log.

### 2.2 Offline/test-fixture numbers (label: SYNTHETIC, not live evidence)

- `tests/test_audits.py:131` — `planted_flaw_calibration` on a 4-item
  synthetic calibration set with one seeded judge error: `rate == 0.25`.
  This proves the CODE computes the ratio correctly; it says nothing about
  a real model's error rate (the "judge" in this test is a scripted mock
  that returns fixed responses).
- `tests/test_audits.py:154` — `bias_probes` with a mock judge scripted to
  always prefer the "own-family" probe: `result["self_preference"] == 1.0`.
  Same caveat: proves the mechanism can detect total, synthetic bias; it is
  not a live self-preference measurement.
- No committed root's `log.jsonl` contains a `judge-self-preference:` or
  `judge-verbosity-bias:` tag (confirmed by the background inventory
  sweep's grep across `experiments/`). **`bias_probes` has never produced a
  live number in the committed record.** This is a real gap, not a null
  result — see §7's INSUFFICIENT EVIDENCE call.

### 2.3 Live numbers: planted-flaw / unknown-flaw error rates (bears on R7a)

`experiments/results/e02_judge_redteam_t1_report.json` (prereg
`experiments/e02_judge_redteam_prereg.yaml`, tranche 1, 2026-07-13,
629674 live tokens) — this is the closest committed analogue of
`planted_flaw_calibration` run at scale with two judge-pair configurations
(same-family: two `gpt-oss:120b` seats; cross-family: `gpt-oss:120b` +
`qwen3-coder:480b`), 40 items per battery:

| battery | same-family catch rate | cross-family catch rate |
|---|---|---|
| known_flaw (seeded, judge has seen the taxonomy) | 0.975 (39/40) | 0.925 (37/40) |
| unknown_flaw (novel construction) | 0.55 (22/40) | 0.175 (7/40) |
| toothless_envelope (worthless, should never convict) | 0.70 (28/40) | 0.25 (10/40) |

`M1`/verdict `P1`: `ratio_unknown_over_known` = **0.1892** for cross-family
(known catch 0.925 vs unknown catch 0.175) — verdict **REFUTED** against
the prereg's own confirm line (≥0.8x) and even below its refute line
(<0.5x). Judges certify the memorized flaw taxonomy far better than they
catch a genuinely novel flaw of the same underlying kind.

`experiments/results/e02_t3_judge_zoo_report.json` (11-model judge zoo +
3 reasoning-arm re-judges, 120 frozen items, 1,501,657 live tokens,
2026-07-13) generalizes this beyond one model pair:

- `verdicts.P1`: median `unknown/known` catch ratio across all 11 seats =
  **0.475** (threshold 0.8) — **CONFIRMED** (poor generalization is
  systematic, not a property of one model pair).
- Per-seat `unknown_catch` ranges from 0.15 (`minimax-m2.7`) to 0.90
  (`kimi-k2.6`); `known_catch` stays in a tight 0.925-1.0 band for every
  seat. The judges agree almost perfectly on what they were trained/tuned
  to recognize and disagree enormously on what they were not.
- `verdicts.P3`: **REFUTED** — zero of the 11 seats reach both
  `unknown_catch >= 0.5` AND `clean_fp <= 0.15` simultaneously; no judge
  model threads catching novel flaws without also convicting clean work.

`experiments/results/judge_liability_index_report.json` (0 LLM tokens —
pure replay over `e02_t1_items/judgments.jsonl`, 2026-07-13): a
zero-cost liability index computed from cross-instrument contradiction and
exposure, without ground truth. `verdicts.P2`: weakest/strongest seat
liability-score ratio = **4.3468**, CONFIRMED — seats differ enormously in
measured liability. `verdicts.P1` (does the blind index rank seats in the
same order as their true unknown-flaw false-negative rate) is REFUTED —
the index's own author flags this as expected: n=3 exact-rank agreement is
weak evidence (1-in-6 chance), and `P2`'s separation is the stronger
finding.

### 2.4 Live numbers: false-positive / clean-item conviction rates (bears on R7b and R7c)

The single most direct number against "judges rule without discrimination"
in the strict sense of "cannot tell good from bad" is the **spread**
across judge identities on the SAME clean (sound, non-flawed) corpus:

`experiments/results/e02_t3_judge_zoo_report.json` `verdicts.P2`:
`clean_fp_min = 0.0` (mistral-large-3:675b), `clean_fp_max = 0.8`
(kimi-k2.6), `span_pp = 80.0` — CONFIRMED against an already-generous
30pp threshold. Two real, frozen judge models, given the SAME 40
genuinely clean items, disagree by 80 percentage points on how many of
them are flawed. That is real discrimination FAILURE, but it is
model-identity-dependent, not universal — it directly complicates a flat
"judges never discriminate" reading (some models barely ever false-convict;
others convict most sound work).

`experiments/results/e02_t2_voting_report.json` (vote-aggregation-rule
study, cross-family judge pair, 2026-07-13) — same underlying seats, two
aggregation rules:

| rule | cross-family unknown catch | cross-family clean FP | same-family clean FP |
|---|---|---|---|
| require_both (unanimous) | 0.175 | **0.025** | **0.475** |
| either_suffices (any one convicts) | 0.75 | **0.60** | 0.725 |

`verdicts.P3`: net catch-gain vs FP-rise moving from unanimous to
either-suffices = **0.0 percentage points exactly** (catch gain +57.5pp,
FP rise +57.5pp) — REFUTED. There is no aggregation rule in this data that
buys more true catches than it costs in false convictions; the two move
in lockstep. `experiments/results/e02_t2b_readjudication_report.json`
independently re-examined the 11 most-flagged "clean" items with two more
instruments (a different-family critic AND a different judge model) under
a conservative AND rule and reclassified **zero** of them as actually
defective (`verdicts.P1`, REFUTED against a ≥3-of-11 bar) — the 60% FP
rate under either-suffices is not hidden contamination in the "clean"
corpus, it is the judges convicting sound work.

Also notable: same-family unanimous agreement flags **47.5%** of clean
items as flawed (`require_both.same_family.clean.rate = 0.475`) — nearly
half of genuinely sound work rejected by two same-family judges agreeing
with each other. This is the sharpest single number in the whole record
against "judges are well-calibrated," and it is a live, non-synthetic
result.

### 2.5 Live numbers: the CRITIC's raw objection rate vs the JUDGE-mediated court's conviction rate (bears on R7b and R7c — read after §2.0)

`experiments/results/court_calibration_v1_report.json` (2026-07-14, the
authority-gate calibration run, 529 calls, 42 planted-defect pairs with
construction-time ground truth):

- `measured.critic_objection_rate`: **clean 1.0, corrupted 1.0** — the
  argumentative CRITIC objects to essentially 100% of everything it is
  shown, sound or defective alike. Read alone, this line is the single
  strongest piece of evidence FOR "prosecutes without discernible
  discrimination" in the whole record — but it is evidence about the
  CRITIC, not the judge-mediated court (§2.0).
- `measured.sensitivity`: **0.119** (5 of 42 planted defects actually
  convicted by the defended court) at `false_conviction: 0.0`.
  `verdicts.P1_the_gate`: **REFUTED — the gate FAILS** (sensitivity 0.119
  vs an 0.80 bound). Per-class: only `causal-non-sequitur` is ever caught
  (5/7); the other five planted-defect classes (chronology-error,
  evidence-misquotation, scope-contradiction, unsupported-comparison,
  vacuous-forbidden-case) are caught **0/7** each.
- `consequence` (quoted verbatim from the report): *"the defended court's
  mercy is now quantified with known labels: perfect specificity, 11.9
  percent sensitivity — it almost never convicts, including when a
  provable defect is planted in front of it."* Per the record's own
  narrative index (`experiments/results/INDEX_2026-07-13.md` line 213):
  *"the bare critic convicts 67.5 percent of the innocent; the defended
  court convicts 12 percent of the guilty."*

This is the record's clearest statement of a **bimodal** miscalibration:
the pre-court CRITIC over-flags almost everything (indiscriminate in the
"too trigger-happy" direction), while the JUDGE-gated court that reviews
those flags is almost never willing to convict, even on a genuine,
constructed defect (indiscriminate in the "too lenient" direction, not
"too harsh"). `experiments/results/critic_specificity_report.json`
confirms the critic-side half in isolation: `verdicts.P1` sensitivity on
flawed items **1.0** (40/40 caught — CONFIRMED), `verdicts.P2` acquittal
rate on verified-sound items **0.325** (13/40 acquitted, i.e. the bare
critic convicts **67.5%** of sound work) — REFUTED, **falsifier
triggered** ("indiscriminate prosecutor" was the report's own falsifier
condition, and it fired).

`experiments/results/defended_trial_v1_report.json` tested whether adding
a defense step to the court restores discrimination: `verdicts.P2`
(REFUTED, no falsifier) — arm-C (defended) sound-acquittal rate rises to
**0.95** but flawed-conviction rate falls to **0.375** (bar 0.60); the
report's own reading: *"Defense restores specificity but destroys
sensitivity."* `verdicts.P3` CONFIRMED: flawed-item abstention only 0.15,
so the court still renders a decision most of the time — it just decides
"acquit" far more than "convict."

`experiments/results/schema_comparator_v1_report.json` (representation
study, 2026-07-14): `verdicts.P2` CONFIRMED — critic objection rate is
**1.0 in every representation × critic-family cell** ("prosecution is
representation-invariant" — quoted). Changing HOW the case is presented to
the critic (structured case-list vs pure prose) does not change the
100%-objection behavior; `verdicts.P1` REFUTED-without-falsifier — a
comparator-aware form does cut the dominant "scope-formalism" objection
pattern by ~18.8 percentage points in both critic families, a real but
partial effect, well under the 30pp adoption bar.

`experiments/results/bronze_court_cross_v1_report.json` (three critic
families — deepseek-flash, kimi, mistral — run against real harness
output, not a curated corpus, 1746 calls): `verdicts.P1` REFUTED
(`P1_measured_spread_pp = 1.18` — the three critic families objected at
statistically indistinguishable rates, all ≈0.99-1.0, to real generated
content); `verdicts.P2` CONFIRMED (`scope_formalism_share` 0.738-0.929 —
the dominant objection ground is format-shaped, not content-specific);
`verdicts.P3` CONFIRMED (seat-plus-order disagreement 9.4-13.1%). Sustain
rate (actual conviction) stayed at 0/85, 3/85, 0/85 across the three
families — corroborating court_calibration's finding that objection is
near-universal but conviction is rare.

### 2.6 A mechanical (non-judge) counter-example, for contrast with §8

`experiments/results/circularity_verifier_report.json` (0 LLM tokens — a
deterministic program screen, not a judge) catches 8/10 constructed
circular arguments (`verdicts.P1` CONFIRMED, catch_rate 0.8) but ALSO
flags 24/40 clean items (`verdicts.P2` REFUTED, fp_rate **0.6** — the same
order of false-positive rate as the worst LLM judges in §2.4). This is
relevant to §8: a program-only screen is not automatically well-calibrated
either; the FP problem in this record is not obviously solved by removing
the LLM.

### 2.7 Bronze run family — a caution about attribution, not judge evidence per se

`experiments/results/bronze_flat_v1_report.json`'s original headline ("the
court convicted 10/10 substantive conjectures with zero survivors") is
**withdrawn** by its own forensic addendum
(`bronze_flat_v1_forensic_addendum.json`,
`claim_status.unsupported_by_retained_record_withdrawn`, quoted): *"'the
court convicted everything' - the decisive kills were direct argumentative
warrants from one batch critic; the defended cross-family rubric court did
not authorize them."* `bronze_flat_v1_correction1.json` confirms:
`conviction_path_confirmed` — the kills were `crit_argumentative_batch`
registering ARGUMENTATIVE warrants with **self-authored validity nodes**,
"with no defender or judge participation." **This tranche is evidence
about the direct-argumentative-critic path, not judge-mediated
adjudication**, despite its own original write-up conflating the two
(exactly the §2.0 trap). It is included here, labeled correctly, because
it is one of the record's largest live demonstrations of unchecked
criticism converting every proposal to REFUTED (10/10), and because that
same failure mode is what the JOINT trial/court machinery (§2.5) exists to
gate — it is background for §8, not §7a-c evidence about judges.
`experiments/results/bronze_repertoire_v2_report.json` and
`bronze_pilot_v1_report.json` are the same family's later, repaired-gate
runs; neither reports a judge-specific number beyond what §2.4/2.5 already
cover (bronze_pilot: `trial_blocked_referential_integrity: 1`,
`trial_blocked_ensemble_split: 3`, `warrants: 0`, `accepted: 12`,
`refuted: 0` — a run with no judge-authored conviction at all).

### 2.8 GLM flat run — the court convicting selectively, on crisp claims

`experiments/results/glm_judge_v1_report.json` (glm-5.2 all roles, 2026-07-14,
998,291 tokens): of 32 refuted designs, 30 fell to deterministic program
checks and **2** to "sustained defended trials" — i.e. the judge-mediated
court did convict, on 2 of 46 admitted designs (`calls.judge: 184` vs
`calls.conjecturer: 13` — the court consumed by far the largest share of
the budget for a small number of actual convictions). Its own forensic
addendum (`glm_judge_v1_forensic_addendum.json`,
`statement_classification.overstated_corrected`, quoted) narrows the
claim: *"two sustained LLM-court rulings are LLM-judge rulings, not formal
proofs; they show the court sustained two objections, nothing more."* This
is consistent with §2.5's pattern (the court convicts rarely, and what
convictions occur skew toward crisp, checkable claims) rather than
contradicting it.

`experiments/results/bronze_flat_v1_counterfactual_forensics.json`
(2026-07-13, 0 tokens, zero-cost replay) computed what would happen to the
19 artifacts refuted in the original bronze_flat run (§2.7) under
`observe_only` authority: `authority_replay.summary` shows **19 of 22**
refuted non-malformed artifacts (all 10 substantive conjectures, 8 stance
seeds, 1 standard) `would_return_to_accepted` — only the 3 conjecturer
outputs killed by a genuine `demonstrative` (program) warrant
`remains_refuted`. This is the record's own quantified illustration of
`observe_only`'s effect: the direct-argumentative-critic conviction path
(not judge-mediated, per §2.7) accounts for nearly the entire refutation
count on this run, and none of it would have happened under the harness's
actual default authority setting.

### 2.9 Runs with zero judge involvement (negative finding, not silence)

`experiments/results/gemma4_dna_unattended_report.json` and
`experiments/results/gemma4_dna_unattended_3_report.json` both report
`audits: {hits: 0, planted_flaw_error_rate:
null, self_preference: null, verbosity_bias: null}` and `trial_guard:
{rubric_warrants: 0, survival_rate: null}` — these two retained runs
(explicitly kept in-tree by `experiments/results/INDEX_2026-07-13.md` as
live small-model evidence for a different experiment, E1.2) have **no**
judge activity to report. Listed for completeness per R5a's "find every
committed root or results file carrying their numbers" — these two carry
none.

## §3. Trial-protocol experiments (R5b)

### 3.1 The guard design, read from `informal/trial.py` directly

`run_trial`'s decisive path (`_trial_steps`, confirmed by direct read) runs
five checks in this fixed order after a `fail` ruling, each capable of
blocking (or, under `observe_only`, filing an advisory outcome instead of a
warrant):

1. **Referential integrity** (`trial.py:362-381`, a PROGRAM check, no
   extra judge call) — every `decisive_point` the judge cited must be a
   real substring of the actual case+answer exchange. `outcome=
   "blocked:referential-integrity"`.
2. **Order-swap consistency** (`trial.py:383-431`, anchored/pairwise modes
   only) — re-runs the SAME ruling with the exchange presented in swapped
   order; if the verdict flips, or the swapped ruling cites a decisive
   point outside the exchange, the trial blocks
   (`outcome="blocked:order-swap"` or `"blocked:referential-integrity"`).
   This requires one extra judge call — it catches the judge disagreeing
   with itself, it does not remove the judge from the loop (relevant to
   §8).
3. **Paraphrase spot-check** (`_paraphrase_screen`, `trial.py:513`,
   called at `trial.py:440`) — re-rules on paraphrases of the same
   exchange through the SAME preflighted cross-family ensemble; a split or
   a unanimous non-fail blocks (`outcome="blocked:<reason>"`).
4. Every check runs on the ALREADY-cross-family-preflighted ensemble
   (`adapter.require_cross_family_judges()`, `trial.py:360`) — a run with
   only one model family available cannot reach this code path at all
   (§2.0's authority-gate distinction; `pairwise_discriminate`,
   `trial.py:810`, carries its own order-swap block at `trial.py:874-897`,
   docstring quoted: *"Under the swap, candidate a is labelled B: the same
   real winner is required (order-swap consistency, §3)"*).

None of these three checks is itself a second, independent adjudicator —
they are consistency screens ON the same judge ensemble's own output.
Referential integrity is the one true exception: it needs no additional
provider call at all, just a string-containment check against the ruling
the judge already gave (relevant to §8).

### 3.2 The prose-can-refute tranche's own evidence (`experiments/2026-08-01-change-prose-can-refute/`) — TEST-FIXTURE, not live

This tranche made prose criticism able to refute a target for the first
time in the codebase (`DELIVERY.md`, quoted: *"Before this tranche, no text
run in DeepReason could ever refute anything by argument... 26 of 42
[recorded] roots had executed criticism and produced zero attacks, every
artifact vacuously accepted."*). Its own proof of the mechanism working is
explicit about what it is:

    VALIDATION.md:36-51 (S2, R2):
    test_a_single_family_run_can_refute_by_prose_end_to_end PASSED
    single_family_run: True      len(state.att)   : 1
    judge families   : {'mock:glm'}   target status: refuted
    bound schools    : ('school-0', 'school-1')   warrant type: argumentative

`judge families: {'mock:glm'}` (also `CHECKLIST.md:569`) is a **scripted
mock adapter**, not a live model — this tranche's decisive proof is an
offline test fixture demonstrating the WIRING works (a prose case CAN mint
an attack edge and flip `Status` to `REFUTED`), not a live judge ruling.
`DELIVERY.md`'s own gate line — *"Proof: full gate 3287 passed, 7 skipped,
0 failed"* — confirms the tranche's evidence standard was the test suite,
consistent with `docs/map/INV-frozen-surfaces.md`'s Traps entry citing
this same tranche's `CHECKLIST.md` step 11 for the manifest-vocabulary
decision. This tranche is evidence about GUARD DESIGN (real, in the
committed code) and about WIRING CORRECTNESS (real, proven by test), not
live-run evidence of judge discrimination.

### 3.3 Live-run counts: order-swap and referential-integrity actually firing

Grepped directly against every committed harness root's `log.jsonl`
(`grep -rl "blocked:order-swap" experiments/ --include=log.jsonl` and the
same for `blocked:referential-integrity`, `audit-hit:`,
`audit-blocked:ensemble-split`, `pairwise-observation`,
`blocked:paraphrase`, 2026-08-09):

| tag | roots with ≥1 hit | total live hits |
|---|---|---|
| `"trial-llm"` (any judge call inside a rubric trial) | 11 roots | **1801** |
| `blocked:order-swap` | 5 roots (`glm_judge_2026-07-14`, `bronze_repertoire_v2_2026-07-14/{gpt-oss_120b,qwen3_5_397b}`, `bronze_feedback_v1_superseded_2026-07-14/{observe_only,trial_required}`) | **8** |
| `blocked:referential-integrity` | 7 roots (adds `bronze_repertoire_v2_2026-07-14/{deepseek-v4-pro,kimi-k2_6}`, `bronze_pilot_2026-07-14`) | **31** |
| `blocked:paraphrase` | 0 | **0** |
| `audit-hit:` (paraphrase/premise-deletion audit landed a warrant) | 0 | **0** |
| `audit-blocked:ensemble-split` (inside the harness log format, distinct from the e02/bronze script-run reports in §2 which use a different logging convention) | 0 | **0** |
| `pairwise-observation` | 0 | **0** |

Reading this table plainly: the order-swap and referential-integrity
screens are REAL and DO fire on live traffic (8 and 31 times respectively,
against 1801 total judge calls inside trials — roughly 2% combined block
rate on calls that reach a trial at all, a small but non-zero fraction of
judge output the guards themselves catch as inconsistent or ungrounded).
The paraphrase screen and the two audit functions wired to fire mid-run
(`paraphrase_invariance_audit`, `premise_deletion_audit`) have **never
fired in any committed root** — despite `paraphrase_invariance_audit`
having a live call site in `scheduler.py` (§2.1). This is a genuine gap:
the paraphrase-flip and ensemble-agreement questions R5b explicitly asks
about are answered by the STANDALONE e02 experiments in §2 (which measure
paraphrase-adjacent phenomena via a different, script-based harness, not
via `informal/audits.py`'s in-run functions), not by any in-run audit
event.

`docs/AUTONOMICS_REPORT.md:17` reports a much larger historical count —
*"117 invalid conviction attempts blocked (88 referential-integrity, 27
ensemble-split) vs 36 valid rubric convictions admitted"* — but this is
from the 2026-07-05 pre-rebuild harness run, whose result files were
retired from the working tree by `experiments/results/INDEX_2026-07-13.md`
(recoverable at commit `3d839b3`, per that index) after "the harness has
been substantially rebuilt on this branch." The narrative document itself
remains committed and its claim stands per the index's own citation
policy, but its underlying root is not among the 11 `log.jsonl` roots
grepped above — it predates the rebuild that produced them.

## §4. Adjudication-blindness fix tranche, 2026-08-01 (R5c)

`experiments/2026-08-01-fix-adjudication-blindness/` (`GOAL.md`,
`DIAGNOSIS.md`, `REPRO.md`, `FIX.md`, `VERIFY.md`) diagnosed and fixed:
`run-b4d6dfda0c20676a864a051fbc97bda4` (jolt epoch 3, 851 events, 72
artifacts) had `len(state.att) == 0`, `len(harness.warrants) == 0` — not
one attack was ever attempted anywhere in the run, all 72 artifacts sat
ACCEPTED, and `run-result.json` still reported `epistemic_checks_passed:
true`. `DIAGNOSIS.md` traces the cause to `invariants.py:4040-4048`
invoking the capture detector purely as a totality check and discarding
its return value — the blindness-detection flags were computed but never
reached the epistemic-findings channel, and even once wired up,
`MIN_ATTACKS_FOR_RITUAL=5` made two of the four ritual conditions
mathematically unreachable exactly when blindness was total.

**This tranche is NOT judge-discrimination evidence.** The zero-attack
root's own attack count is zero because `ARGUMENTATIVE_AUTHORITY` defaults
to `observe_only` (`docs/map/CON-authority.md` §"Everything defaults to
observe_only") — under that default, prose criticism records scrutiny and
mints no warrant AT ALL, so no judge (or critic) ruling was ever asked to
adjudicate anything in this root; there is no judge verdict to be right,
wrong, discriminating, or biased. `GOAL.md` says this explicitly: fixing
`authority.py` so text runs CAN mint warrants "is a design decision the
operator has not made" and was ruled **out of scope** for that tranche.
The defect this tranche fixed is a **reporting honesty** problem
(a run that attacked nothing must not claim to be epistemically clean),
not a judge-calibration problem — the two are adjacent (both concern
whether the harness's criticism layer is trustworthy) but distinct.
`GOAL.md`'s own blast-radius measurement is useful background for §2/§7,
though: of 31 openable roots, only 5 ever had ANY attacks/warrants at all
(`bronze_flat_2026-07-13/{deepseek-v4-pro: att=11, qwen3_5_397b: att=8,
kimi-k2_6: att=4}`, `live_compare_2026-07-28/.../shallow-dc6fe3f9: att=1`,
`live_engaged_2026-07-27/run-f4fa6663e5412d64: att=1`) — 26 of 31 roots
never attacked anything, consistent with `observe_only` being the actual
operating default across most of the committed record, which is itself a
relevant fact for §8 (a solo run today, run with defaults, already spends
no judge tokens on status-changing text adjudication).

## §5. Stress-triplet and lambda/experiment-module runs (R5d)

### 5.1 Stress-triplet: zero judge involvement (negative finding)

    grep -c '"trial-llm"\|"judge"' experiments/2026-08-02-stress-triplet/home-{orbit,triage,workshop}/runs/run-*/log.jsonl

    home-orbit/runs/run-6472629dbc5d408a733d472040671752/log.jsonl:0
    home-triage/runs/run-0a3e93d6e8031e2e6d1d21dde2fa93cc/log.jsonl:0
    home-workshop/runs/run-1a0d4168a446f052bc7ccc9aa20b9829/log.jsonl:0

All three roots are rule-engine event traces (`Register`, `Spawn`,
`Control`, `Refl`), consistent with `docs/map/SUB-adjudication.md`'s Traps
entry naming `run-6472629d` (orbit) as the committed demonstration of a
run with `att` empty and every artifact vacuously `ACCEPTED` (the
adjudication-blindness detector's positive-control fixture, §4 — a
different but related failure mode: zero warrants, not bad judge
verdicts). The tranche's own `{orbit,triage,workshop}-audit.json` files
were also checked directly (traversed for any key containing "judge" or
"trial") and contain none. **The stress-triplet contributes nothing to
the judge-discrimination question** — there is no judge ruling anywhere
in it to evaluate.

### 5.2 Lambda: pre-registered, never run to a committed result

    experiments/lambda_preregistration.yaml, lambda_preregistration_v2.yaml
    (both present, both prereg-only — no matching result file under
    experiments/results/, no committed run root under experiments/)

`src/deepreason/experiments/lambda_run.py` and `scripts/lambda_live.py`
exist as tooling but were never executed to a committed artifact. The one
"judge"-adjacent line in `lambda_run.py` (a comment: *"Post-hoc oracle
scoring: the withheld verifier judges every conjecture"*) refers to a
withheld PROGRAM oracle, not an LLM judge — even conceptually, lambda's
design does not route through `informal/audits.py` or `informal/trial.py`.
**Lambda contributes nothing to the judge-discrimination question either;
its absence from the record is a real gap (untested), not a null
result** — see §7's INSUFFICIENT EVIDENCE handling.
