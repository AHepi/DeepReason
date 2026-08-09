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
