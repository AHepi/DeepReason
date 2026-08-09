# Judge-evidence review: what do committed runs prove about LLM-judge discrimination?

**The question**, in the operator's words: what do the committed runs and
experiments actually prove about LLM-judge discrimination? The operator's
own hypothesis — "they prosecute without any discernable discrimination" —
is what this document tests, not what it assumes. Every claim below carries
its source (`path:line` or a JSON field inside a named file) so the number
can be re-derived, not just trusted.

**Executive summary** (written last, after §2-§8 below; full reasoning and
every number is in those sections):

The flat hypothesis — judges prosecute with no discernible discrimination
— is **not what the committed record shows**, but a real, narrower version
of it survives, and it lands on a DIFFERENT part of the pipeline than
"judge" naturally suggests. Splitting the pipeline in two matters more
than any single number here: the pre-court argumentative CRITIC objects to
essentially 100% of everything it sees, clean or flawed alike, across
three independent live studies (§2.5, §7b) — genuinely, repeatedly,
content-blind. But the JUDGE-gated conviction step that actually changes
an artifact's status is the opposite problem: it rarely convicts anything
(11.9% sensitivity against 42 planted, ground-truth defects, §2.5), misses
most novel flaws outside its certified taxonomy (§2.3, §7a), and — in the
harness's actual frozen configuration (cross-family, unanimous judges) —
almost never falsely convicts sound work (0-2.5% false-positive rate,
§2.4, §7c). Loosen that configuration (same-family pairing, or any
either-suffices vote rule) and false conviction of sound work jumps to
47-60% (§2.4) — so the operator's worry is FALSE of what the harness
actually runs today and a real, quantified risk of what it would become
under a weaker configuration. One strand — self-preference/verbosity bias
specifically — has never been measured live at all (§2.2, §7c): a genuine
gap, not a negative result. §8 lays out what already exists in the tree
for a judge-free or judge-minimal road, and what it cannot do: no
mechanism in the record adjudicates open-ended prose without an LLM in
some role, so eliminating judges as a category would mean giving up on
prose ever being able to refute anything — which is the exact state 26 of
31 measured roots are already in, by default (§4, §8.1).

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

## §6. EXPERIMENT_PROGRAM_2026-07.md's judge items (R5e)

### 6.1 The judge items, quoted

`docs/EXPERIMENT_PROGRAM_2026-07.md:52-55` (rule 4 of the program's six
standing rules): *"**Certified judges.** Judge seats are certified per run
against the planted-flaw, self-preference, and verbosity audits in
`deepreason report`. The cross-family rule (two seats, two route
families) is enforced."*

`:63-67` (a precondition, not an experiment, flagged before any Tier 2/3
run could proceed): *"`config/deepseek.yaml` currently seats both judges
from the same family, violating the cross-family rule."*

`:153-200` — **E0.2 "Judge and skeleton red-team"** in full. Question:
*"Can an adversarial generator get worthless artifacts past the judges and
the skeleton machinery, and does the planted-flaw battery detect flaw
classes it was not built from?"* Three sub-batteries: (a) unknown-flaw
battery via `scripts/judge_battery.py`, (b) skeleton gaming (toothless
forbidden cases), (c) bias-at-scale (self-preference/verbosity extended to
500 matched pairs). Predictions, quoted verbatim:

- P1: "unknown-flaw catch rate >= 0.8x the known-flaw catch rate.
  Falsifier: < 0.5x, and planted-flaw certification only certifies
  memorized flaw classes; judge audit numbers get demoted in every
  report."
- P2: "toothless-forbidden-case admission <= 10%. Falsifier: > 30%,
  skeletons are gameable."
- P3: "cross-family seats catch >= 5 percentage points MORE adversarial
  flaws than same-family seats. Falsifier: no difference, the cross-family
  rule is superstition."

`:257-320`, `:415-528`, `:747-789` — Tier 2/3 run designs repeatedly
specify cross-family judge pairs (e.g. `:259-261`: frontier profile
"judges `deepseek-v4-pro` + `qwen3-coder:480b`"; mid profile "cross-family
judges") and a per-stage survival funnel ("candidates generated ->
schema-valid -> gate-passed -> judge-survived", `:318`) citing
`experiments/results/gemma4_dna_unattended_report.json`/`_3_report.json`
(§2.9 — both report zero judge activity, so this funnel's "judge-survived"
stage was never exercised on those two specific roots).

`:789` — dependency graph line: *"E0.2 (judges) --> every Tier 2/3 run
(seat certification + satisfiability gate)"* — Tier 2/3 runs were
explicitly gated on E0.2 landing first.

`:810-826` — action items, quoted in part: item 2 *"Countercondition-
satisfiability checker + adversary harness on `scripts/judge_battery.py`
(E0.2)"*; item 7 *"Config fix: cross-family judge seats in
`config/deepseek.yaml` (precondition, not an experiment)."*

### 6.2 Were P1 and P2 confirmed, falsified, or left untested?

Both were RUN, and both have a directly matching result:

- **P1 (unknown-flaw catch >= 0.8x known-flaw catch): FALSIFIED.**
  `experiments/results/e02_judge_redteam_t1_report.json` `verdicts.P1`
  measured `ratio: 0.1892` for the cross-family pair — below even the
  falsifier line (< 0.5x), not just short of the confirm line. Per the
  plan's own falsifier clause, judge audit numbers are to be treated as
  demoted for memorized-vs-novel flaw detection claims wherever they
  appear. Cross-checked independently at larger scale by
  `e02_t3_judge_zoo_report.json` `verdicts.P1` (median ratio 0.475 across
  11 models, same conclusion).
- **P2 (toothless admission <= 10%): CONFIRMED, with a caveat the plan did
  not anticipate.** `e02_judge_redteam_t1_report.json` `verdicts.P2`
  measured `admission_rate: 0.0` (0/40) — well inside the confirm line.
  But `M2.admission_funnel` shows `not_flagged_by_cross_family_judge: 30`
  of 40 — the JUDGE stage alone would have let 30/40 toothless items
  through; the argumentative CRITIC stage (§2.0's distinction) is what
  actually caught them (`survived_criticism: 0`). The plan's P2 asked
  about the funnel's overall admission rate, which is genuinely 0% — but
  attributing that 0% to "the judges" would overstate what the judge
  stage itself contributed.
- **The E0.2 config precondition (`:63-67`) was fixed.** `config/
  deepseek.yaml`'s current committed text (checked directly) says: *"This
  profile's two DeepSeek judge seats are useful for non-normative probes
  but do NOT satisfy the rubric trial requirement... rubric workloads must
  supply and freeze a second judge family or preflight fails."* The
  precondition action item is done.
- **One number in `config/deepseek.yaml` could not be independently
  verified.** Its judge-role comment cites *"pro scores 0.0 error / 0.0
  bias with reasoning OFF... flash NEEDS reasoning (0.125 error, 0.375
  verbosity bias without it)"* sourced to
  `experiments/results/judge_battery_report.json` — **this file does not
  exist in the committed tree** (checked directly, `ls` fails). It may be
  one of the 61 pre-rebuild files retired by
  `experiments/results/INDEX_2026-07-13.md` (recoverable at `3d839b3`) or
  simply never committed. Either way, this specific claim is asserted in
  a committed file but not independently checkable from the current
  record — flagged here rather than silently repeated as verified.

## §7. Three-way scoring: incorrect / undiscriminating / over-prosecuting

This section introduces no new numbers — every figure below already
appears in §2-§6 and is referenced back to its source, not re-cited in
full.

### 7a. Judges rule INCORRECTLY (planted-flaw / unknown-flaw error rates)

Every measurement of a judge (or judge-gated court) against constructed
ground truth shows real, substantial error, and the errors are lopsided
toward MISSING genuine defects rather than inventing them:

- Known-flaw catch stays high and stable (0.925-1.0) across every model in
  the 11-seat zoo (§2.3); the certified planted-flaw taxonomy IS caught
  reliably.
- Unknown/novel-flaw catch collapses: 0.175 (cross-family pair, §2.3) to a
  median of 0.475 across the full zoo (§2.3) — well below the program's
  own 0.8x confirm bar, and the cross-family pair specifically falls below
  even the 0.5x FALSIFIER line (§6.2).
- The judge-mediated defended court, tested against 42 planted defects
  with construction-time ground truth, catches only 11.9% of them overall
  and 0% on five of six defect classes (§2.5) — a large, real error rate
  in the direction of letting genuine defects through.
- Error rates are highly judge-identity-dependent: `judge_liability_index`
  measures a 4.35x spread between the most- and least-liable seat
  configuration (§2.3) from cross-instrument contradiction alone.
- One live counter-example exists: `glm_judge_v1`'s court sustained 2 of 32
  refutations on crisp, quantitative claims (§2.9) — showing the court CAN
  convict correctly when the target is formally checkable-adjacent, not
  only that it fails to.

**Verdict: SUPPORTED**, with a specific shape the flat hypothesis does not
capture — the record shows judges (and the judge-gated court) erring
mostly by UNDER-catching, especially on anything outside the certified
taxonomy, not by convicting indiscriminately. "Judges rule incorrectly" is
true; "incorrectly" here usually means "too lenient," which is a real but
different worry than the operator's "prosecute" framing suggests.

### 7b. Judges rule WITHOUT DISCRIMINATION (pass/fail insensitive to case quality)

The record splits sharply by WHICH stage of the pipeline is measured
(§2.0's critic/judge distinction is load-bearing here):

- At the CRITIC's raw objection stage: `court_calibration_v1` measured
  `critic_objection_rate` of exactly 1.0 on both clean and corrupted
  content (§2.5) — literally content-blind. `bronze_court_cross_v1`
  reproduced this on REAL harness output across three different critic
  families, spread only 1.18 percentage points (§2.5). `schema_comparator_v1`
  found the same 1.0 objection rate is invariant across four different
  presentation forms (§2.5). At THIS stage, the operator's hypothesis is
  **directly and repeatedly confirmed** by three independent live studies.
- At the JUDGE-gated conviction stage (the actual status-changing
  mechanism): the picture is different. Known-vs-unknown-flaw catch rates
  differ by 40-75 percentage points depending on pairing (§2.3) — that IS
  discrimination between content classes, just weighted toward the
  familiar. `e02_t2_voting`'s vote-rule study (§2.4) found the sharpest
  single number against "judges discriminate": loosening the aggregation
  rule from unanimous to either-suffices bought +57.5pp more true catches
  at the cost of +57.5pp more false convictions — a NET of exactly 0.0
  percentage points (§2.4). A mechanism with real discriminating power
  would show positive net signal from more data (two opinions instead of
  one); an exact wash is consistent with the aggregation rule adding noise
  cancellation, not added judgment.
- The live order-swap consistency guard (§3.3) fired only 8 times against
  1,801 live judge calls inside trials (~0.4%) — the SAME judge ensemble
  is usually self-consistent when the same content is re-presented in
  swapped order, which argues judges are not randomly guessing on
  individual rulings, only that they generalize poorly ACROSS genuinely
  different content (§7a) and vary wildly by identity on FALSE POSITIVES
  (§7c).

**Verdict: MIXED**, and the split is not noise — it is the record's most
important structural finding. The pre-court CRITIC step is
content-blind (near-universal objection, confirmed three independent
ways). The JUDGE-gated conviction step that actually changes `Status`
discriminates between content classes it recognizes and content classes it
does not, is internally self-consistent under order-swap, but shows no net
benefit from looser aggregation. A flat "judges never discriminate" is
FALSE of the status-changing mechanism and TRUE of the upstream objection
mechanism; conflating the two (as this record's own `bronze_flat_v1`
original write-up did, §2.7) is the exact trap this review exists to
avoid.

### 7c. Judges OVER-PROSECUTE (fail-rate bias vs ground truth)

Two sub-questions, scored separately because the evidence for them differs
sharply:

**Self-preference and verbosity bias specifically** (the operator's
"discernable discrimination" phrase most literally maps to systematic
favoritism): **INSUFFICIENT EVIDENCE.** The only numbers in the entire
committed record are the synthetic test fixtures in `tests/test_audits.py`
(§2.2) — a scripted mock judge, not a real model. `bias_probes` has never
produced a live `judge-self-preference:` or `judge-verbosity-bias:` log
entry anywhere in the committed record (§2.2, §3.3). This specific,
literal reading of "over-prosecute due to bias" is untested, not refuted
and not confirmed.

**Over-prosecution of sound/clean work in general** (broader reading —
does the mechanism convict good work at a high rate): **MIXED, and the
split is configuration-dependent, not universal.** The record's own
strictest, actually-frozen configuration (cross-family, unanimous
`require_both`, which is what a defended rubric trial demands per
`docs/map/CON-authority.md`'s cross-family requirement) shows the OPPOSITE
of over-prosecution: `false_conviction: 0.0` in `court_calibration_v1`
(§2.5) and `clean.rate: 0.025` (2.5%) in `e02_t2_voting`'s require_both
cross-family cell (§2.4). But two adjacent, weaker configurations in the
SAME dataset show severe over-prosecution: same-family unanimous convicts
47.5% of clean items (§2.4), and cross-family either-suffices convicts
60% (§2.4, confirmed not an artifact by `e02_t2b`'s independent
re-adjudication finding zero of the top 11 flagged "clean" items actually
defective, §2.4). The judge-zoo study shows clean-FP spanning 0% to 80%
depending purely on which single model judges (§2.3-2.4). And upstream of
all of this, the bare CRITIC (not judge) convicts 67.5% of verified-sound
work before any judge is even consulted (§2.5).

**Verdict: MIXED.** The specific bias-probe reading of the operator's
worry is untested (insufficient evidence). The broader over-prosecution
reading is FALSE of the harness's actual frozen, cross-family-unanimous
status-changing configuration (which under-prosecutes, §7a) and TRUE of
every looser configuration this record measured (same-family pairing, any
form of either-suffices voting, and the pre-judge critic stage). This is a
genuine warning about what happens if a future run relaxes those specific
guards, not evidence that the guarded mechanism as it stands today
over-prosecutes.

## §8. Design consequence: a judge-free or judge-minimal road for solo runs

Two standing operator design laws bound this section (both quoted from
CLAUDE.md, both binding, neither derived from §7's findings — they hold
regardless of what the numbers said): **"A solo run with everything on
must be an option"** — no harness capability, including status-changing
criticism, may be structurally locked out of sole-model operation; and
**"Formalism is an option, never an obligation"** — nothing may penalize
a conjecture, or a criticism, for being informal. A judge-free road
therefore cannot simply say "criticism now requires a formal commitment";
it must ADD non-judge routes without narrowing what an informal
conjecture may already do. §7's findings bound the DESIGN, not the LAW —
even if §7 had come back "judges are perfectly calibrated," these two laws
would still require a solo-compatible, non-formalism-obligated path to
exist.

### 8.1 Candidate mechanisms already in the tree

**Program/predicate commitments** (`programs.py::evaluate`,
`EXEC_PROGRAMS = {"exec_oracle", "property_oracle", "dataset_oracle"}`,
per `docs/map/SUB-evaluation.md`).
CAN: adjudicate any commitment a machine can decide from the artifact's
real bytes alone — `predicate:` expressions and any `program:` name in
`PROGRAMS`/`BLOB_PROGRAMS`. This is a pure function of content (§0 of
`docs/map/SUB-evaluation.md`: "no wall-clock reaches a verdict"),
zero-token, fully deterministic, and already the majority mechanism in the
richest live record this review found — 30 of 32 refutations in the GLM
flat run (§2.9) were program checks, not judge rulings.
CANNOT: adjudicate anything requiring judgment of PROSE — relevance,
argument quality, whether a claim actually answers the question. A target
can immunize itself against this route entirely by attaching only a
structural commitment (`json-wf`, `skeleton_wf`) — `_STRUCTURAL_PROGRAMS`
exists specifically to stop that trick from also blocking prose criticism
(`docs/map/SUB-evaluation.md` Traps). Program commitments are therefore
NECESSARY infrastructure but cannot by themselves replace what prose
criticism does.
PRICE: near-zero — this mechanism is fully built and already the
dominant conviction path in the one live run that measured its share.
RECOMMENDATION: no design work needed; the gap is coverage (how many
conjectures ship a machine-decidable commitment at all), not mechanism.

**Counterexample execution**
(`oracle.py::admit_counterexample`, `fuzz_property`).
CAN: give a critic a GROUNDED, non-judge route to refute a proposed
property or checker — `admit_counterexample` gates a proposed input and
mints a single-input property oracle with a deterministic rejection
reason; `fuzz_property` enumerates generator outputs with no model in the
loop at all. Both produce a verdict from execution, which the record
treats as `EXEC_PROGRAMS`-grade evidence, immune to a prose case
(`formally_backed`, `docs/map/SUB-evaluation.md`).
CANNOT: apply to anything that is not itself a checkable property or
executable claim — a historical-mechanism conjecture (the bronze runs'
entire subject matter, §2.7) has no counterexample to execute.
PRICE: near-zero for domains that are already property/executable
(formal, code, simulation workloads); not applicable to open-ended text
domains, which is most of the record's live evidence.
RECOMMENDATION: already the right tool where it applies; no new design
needed, only broader authorship of properties/checkers per problem.

**Referential integrity** (`trial.py:362-381`, confirmed by §3.1/3.3).
CAN: catch a judge citing a `decisive_point` that is not actually present
in the exchange it ruled on — a real, cheap, zero-additional-provider-call
consistency check on a ruling the harness ALREADY paid for. It is live
and firing: 31 hits across 7 committed roots (§3.3), plus the retired
2026-07-05 harness's larger count of 88 (§3.3, historical, not
independently re-verifiable from the current tree). `circularity_verifier`
(§2.6) is a second, structurally similar example already in the tree —
a fully mechanical, 0-token screen that catches 8/10 constructed circular
arguments.
CANNOT: judge whether the judge's VERDICT was right — only whether its
STATED grounds are real. A judge can cite a real, present sentence and
still misjudge its significance; referential integrity would not catch
that. `circularity_verifier`'s own numbers (§2.6) show a mechanical screen
is not automatically well-calibrated either — 60% clean-item FP, the same
order of magnitude as the worst LLM judges (§2.4).
PRICE: near-zero — already built, already firing, requires no new judge
call.
RECOMMENDATION: this is the cheapest available discrimination the tree
already has for the harness's own judge output; nothing to build, keep as
a mandatory precondition on every trial (it already is one).

**Order-swap consistency** (`trial.py:383-431`, `pairwise_discriminate`
`trial.py:874-897`).
CAN: catch a judge disagreeing with itself when the same content is
re-presented in a different order — a real self-consistency screen, live
and firing (8 hits across 5 roots, §3.3).
CANNOT — and this is the distinction §3.1 flagged as easy to overstate —
**eliminate the judge from the loop.** It requires one additional judge
call under the swapped presentation; it screens the judge's OWN output
against itself, it is not a judge-free mechanism. Framing it as part of a
"judge-minimal" road is correct (it adds no NEW judge dependency beyond
the ensemble already required) but framing it as "judge-free" would be
wrong.
PRICE: one extra judge call per screened ruling — already paid in every
live trial today.
RECOMMENDATION: keep; correctly labeled as a consistency screen ON
judge output, not a substitute for it, in any future design document.

**`observe_only` as the existing default** (`docs/map/CON-authority.md`).
CAN: already deliver a genuinely judge-FREE road for status-changing
criticism, TODAY, with no design work — `ARGUMENTATIVE_AUTHORITY`,
`TEXT_RUBRIC_AUTHORITY`, `PAIRWISE_AUTHORITY`, and
`INFRASTRUCTURE_REVIEW_AUTHORITY` all default to `observe_only`
(`CON-authority.md`, checked live), and §4's blast-radius measurement
(from the adjudication-blindness tranche) shows 26 of 31 openable roots
in the current record already ran this way — no warrant, no status
change, criticism recorded as scrutiny only. This mode is explicitly
solo-compatible (no cross-family requirement applies; `observe_only`
never calls `require_cross_family_judges` at all).
CANNOT: change `Status` from prose at all — a run in `observe_only` gets
the "no judge can misjudge you" property by giving up the "prose CAN
refute you" property entirely. This is the OPPOSITE end of the tradeoff
from what R8 is asking about (a road for solo runs to still get
status-changing criticism, just not FROM a judge) — `observe_only` is a
valid answer only if the operator is content with prose remaining
advisory-only in solo mode, same as most of the record already is.
PRICE: zero — already the default, already proven at scale (26/31 roots).
RECOMMENDATION: worth stating explicitly as the FLOOR any new mechanism
must beat: if a proposed judge-minimal mechanism cannot outperform
`observe_only`'s "no false convictions, no status change" balance on §7's
own evidence, `observe_only` remains the safer solo default.

### 8.2 What none of these can do

None of the four "can-adjudicate" mechanisms above (program/predicate
commitments, counterexample execution, referential integrity,
order-swap) can perform the one thing a judge ruling actually does:
decide whether a piece of PROSE — a historical mechanism, an argued
claim, a piece of open-ended reasoning with no executable ground truth —
is sound. That is definitionally what `informal/` exists for
(`docs/map/SUB-evaluation.md`: "the guarded rubric court for claims no
program can decide"). §7's own evidence is double-edged here: the
judge-mediated court is real but severely under-powered (7a, 11.9%
sensitivity) and its raw upstream critic stage is content-blind (7b);
neither fact makes a NON-judge alternative for prose-quality adjudication
appear anywhere in the tree. This review found no existing mechanism that
adjudicates prose without an LLM in some role.

### 8.3 Decisions not made (forks this review surfaces but does not resolve)

- Whether `observe_only`'s current default is SUFFICIENT for solo runs
  going forward, or whether the operator wants a genuinely new
  non-judge-mediated status-changing path built for prose specifically.
  This review supplies the evidence (§7) and the floor (§8.1's
  `observe_only` entry) but the choice between "accept the floor" and
  "fund new machinery none of which currently exists" is the operator's,
  not this review's.
- Whether referential-integrity's demonstrated 2% combined block rate
  (§3.3: 39 blocks / 1801 trial-llm calls) is itself worth widening —
  e.g. to a stricter same-content-verbatim-quote requirement — as a
  cheap, already-proven lever, independent of any judge-identity
  question.
- Whether the aggregation-rule finding in §7b (net 0.0pp from loosening
  unanimous to either-suffices) generalizes beyond the two seat pairs
  `e02_t2_voting` tested, or is specific to that pairing — the record
  does not have a third aggregation rule's data to check monotonicity.
- Whether `bias_probes`' complete absence of live data (§2.2, §7c) is
  worth closing before any judge-authority decision is made, given the
  operator's own standing law ("judge seats are suspect-by-default...
  must first consult the judge-audit evidence") — this review is that
  consultation, and it found the self-preference/verbosity strand of the
  audit machinery has never been run live. Closing that gap is priced as
  a live-run/API-experiment task (per CLAUDE.md's "tokens are cheap, the
  agent is not" law) if the operator wants it filled before deciding.
