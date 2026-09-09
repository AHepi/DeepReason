# AUDIT REPORT — four questions about language models, answered from this record

Read-only audit of `main`, 2026-09-08. **This is an audit of language-model
behaviour, not of the harness.** The harness appears only where it decides
whether an observation is about the model or about the code, or where it
decides whether a number can be trusted. No verification instrument was run:
this is a review-kind task and the operator's standing rule (CLAUDE.md,
2026-09-05) forbids it without permission stated for the task. Every number
below was read out of a committed artifact.

**The harness changed continuously while this record was being made, and each
change maps to its own test records.** That fact does more work in this report
than any single measurement, so it is stated at the top rather than buried in
a caveat — §0.1 works out what follows from it.

**How to read the standing of a number.** Three tiers, and the audit says
which tier every load-bearing claim sits in:

- **Tier 1 — re-derivable today.** The raw responses or the report JSON sit
  in the repository, so anyone can recompute the number on `main` right now.
- **Tier 2 — pre-registered, outcome recorded, raw data absent.** The
  prediction is frozen in a committed file and the outcome is written beside
  it, but the run roots and report files are gone. Better than prose, short
  of replay.
- **Tier 3 — narrative only.** A committed document states a number and
  nothing in the tree produces it.
- **Demoted.** A pre-registered falsifier fired against the *instrument* that
  produced the number, and the repository's own registered consequence was to
  mark such numbers unverified. One family of numbers in this report is in this
  state and §6.4 is about it.

Tier matters because this repository's own rule is that the record is the
only admissible evidence and model prose never is. An audit that quotes a
Tier 3 number as if it were Tier 1 breaks the rule it is auditing under.

**One scope warning that shapes all four answers.** Most of what this record
measures is language models sitting in *evaluator* seats — critic, judge,
grader — and a smaller part measures them *generating*. Where a finding comes
from evaluation and I generalise it to models at large, I say so and say what
the generalisation costs.

---

## Part 0 — What the corpus is

### 0.1 A moving harness, and what follows for reading this record

The record was not produced by one system observed over time. It was produced by
a system under continuous change, where each change brought its own tests and its
own runs. Three consequences, and they pull in different directions:

**A behaviour that replicates across harness versions is worth more than its
sample size suggests.** When the same property turns up in 2026-07 and again in
2026-09, the two measurements were taken on materially different machines, with
different briefs, different forms, different authority defaults and often
different models. The harness is not a constant that could be silently causing
both. This is why the strongest claims in Part 1 are the ones with dates far
apart: the argumentative critic objecting to everything, measured four times
between 2026-07-13 and 2026-09-04; the two fault classes never caught, measured
in 2026-07 and again eighteen months later; the harness losing to the plain
model, measured in 2026-07, 2026-08 and 2026-09 on three different task families
and three different builds. Read those as replications across implementations,
which is a stronger thing than three trials of one.

**A pooled census mixes versions, and must be read as a corpus property rather
than a system property.** The two censuses below sweep 96 run roots produced over
months of change. Their numbers are true of *the corpus*. They are not a
measurement of any one build's behaviour, and where they look like devastating
capability findings, Part 2 §2.3 says why they are not.

**An old finding may have been superseded by a change rather than by a
measurement.** The record's own remedy for this is `docs/ERRATA.md` — eighty
entries — and the retirement and withdrawal notes in
`experiments/results/INDEX_2026-07-13.md`. Where this audit relies on a pre-2026-08
number, it says so, and §6.4 is what happens when a superseding measurement
exists and the document it supersedes was never updated.

### 0.2 What this audit read, and what it did not

Stated because the operator asked for unsupported things to be named, and
coverage is one of them.

**Read closely, and every load-bearing number in this report re-derived from the
committed artifact rather than taken from a narrative:** the judge and critic
calibration corpus in full (the 2026-07-13 red-team including its 480-row
judgment blob, the eleven-model zoo including its 1,561-row blob, the court
calibration corpus item by item, critic specificity, the defended trial, the
clean-item re-adjudication, the cross-family court, the schema comparator, the
detector calibration, the liability index); the construction tranche and its
rematch including their raw score files; the diversity experiment; the
blind-critic tranche; the reach and attack censuses; the run-anatomy criticism
and evidence censuses; the live module census; the mini isolation measure; the
history channel including its replication; the poietics run; the July live
research campaign; the record-claims instrument; the exploration and basin
documents and the embedder recalibration that bears on them; the errata ledger;
the two experiment-record indexes; and the pre-registrations of all of the above.

**Not read closely, and therefore not represented here:** the oldest cross-model
generator campaigns (gemma, bronze, the jolt series, the schema comparator's
sibling runs) beyond the report files quoted; the July live campaigns other than
the research one; the form-compliance defect tranches beyond their headlines; the
channel and two-call tranches; and the prior audits' own reports. A fan-out over
those was started and stopped when it became clear it would take hours for
material with less bearing on the four questions than what is above. If a claim
in this report is wrong, that is where the correction is most likely to come
from.

### 0.3 The corpus

128 dated tranches plus a dozen earlier campaigns; 63 results documents; 415
test files; 41 report files under `experiments/results/`. The measurement
spine of this audit is nine bodies of evidence, all Tier 1:

| body | date | volume | what it measured |
|---|---|---|---|
| `e02_judge_redteam_t1_report.json` | 2026-07-13 | 120 items, 681 calls | fault detection with and without a supplied fault category |
| `e02_t3_judge_zoo_report.json` | 2026-07-13 | **11 models**, 120 items, 1,561 judgments | the same, across eleven models at temperature 0 |
| `court_calibration_v1_report.json` | 2026-07-14 | 42 constructed pairs, 529 calls | six fault classes with ground truth by construction |
| `2026-08-25-change-constructive-frontier` | 2026-08-25 | 1.4M tokens, 2 arms + 1 void | construction against an exact checker, harness vs plain sampling |
| `2026-08-28-diversity-generation` | 2026-08-28 | 2,243,500 tokens, 12,794 candidates | how many distinct ideas four ways of asking produce |
| `2026-09-04-experiment-blind-critic` | 2026-09-04 | 480 criticism calls | planted-fault detection under four exposures |
| `2026-08-27-pc2b-symmetric-reasoning` | 2026-08-27 | 2 arms, reasoning on both | the construction rematch, and the record's sharpest self-scoring instance |
| `2026-09-01-live-all-modules-p-a1` | 2026-09-01 | 24 modules, live census | which channels a model used when every channel was armed |
| `2026-08-26-run-anatomy-w2` / `-w3` | 2026-08-26 | 196 attacks, 623 evidence blocks | whether criticism and evidence ever reached the model at all |

Two more bodies carry a lot of weight and sit lower: the basin/exploration
study (Tier 2) and the grounding comparison in `docs/REPORT.md` (Tier 3).
Part 6 explains why, because it is itself a finding.

Two census tranches give the shape of the whole corpus and both are Tier 1:

- **Attack census** (`2026-08-22-measure-grounded-flip-rate`): across 96
  readable run roots, 6,370 artifacts carry 5,165 support links and **60
  attack links**. 76 of the 96 roots have no attack link at all. Every attack
  relation in the corpus is one hop deep — no artifact is attacked twice, no
  attacker is itself attacked, and there is no defence chain longer than a
  single step anywhere in 6,370 artifacts.
- **Reach census** (`2026-08-21-measure-reach-firing`): across those same 96
  roots, 1,178,430 candidate pairs, **zero** cases of a settled idea being
  reused to account for a further question. Not one.

Hold those two next to each other. In this entire record, criticism almost
never changed anything, no criticism was ever itself criticised, and no idea
was ever carried to a second question. That is the ceiling on what any answer
below can claim.

---

## Part 1 — Why following instructions fails, and what that says about the thing

**The answer in three sentences.** These models do not fail at instructions in
the way the word "fail" suggests — they satisfy the *form* of an instruction
almost perfectly, and they answer in its *vocabulary* essentially always. What
they do not reliably do is *perform the operation the instruction names*: when
an instruction says "check whether this claim contradicts its stated scope",
the record shows the model producing a well-formed, scope-flavoured objection
while the actual contradiction goes unnoticed. So the failure is not
disobedience and not inattention; it is that an instruction reaches the model
as a description of what its output should look like, and not as a procedure
to run.

Five shapes, in the order of how well the record supports them.

### 1.1 Form compliance is not the problem — it is nearly perfect

Before anything else, the obvious hypothesis has to be killed. Across 480
evaluator calls in the 2026-07-13 red-team, **parse failures: 0 of 480**
(`experiments/results/e02_judge_redteam_t1_report.json`, `caveats[3]`). Across
7,236 generation calls in the 2026-08-28 diversity experiment, the invalid
rate was **0.25% to 0.55%** in every one of four conditions
(`experiments/2026-08-28-diversity-generation/RESULTS.md`, the M3 table). One
model of eleven is an exception worth naming — `minimax-m2.7` took 64 parse
failures and 354 retries where nine others took zero
(`e02_t3_judge_zoo_report.json`, `exploratory.wire_discipline`) — and it is an
exception, not the pattern.

So "LLMs struggle to follow instructions" is false as stated about output
shape. Something else is going on.

### 1.2 The decisive measurement: detection collapses when the category is withheld

This is the sharpest result in the whole corpus, and it is measured on
**eleven models** at temperature 0 over 120 items with ground truth by
construction (`e02_t3_judge_zoo_report.json`, 1,561 judgments).

Each model was asked the same question about each item: is there a fault here?
Items came in three kinds — a fault whose category the seat's own rubric
named, a fault outside that rubric, and a clean item.

| model | fault it had the category for | fault it did not | clean work it flagged anyway |
|---|---|---|---|
| minimax-m2.7 * | 0.950 | 0.150 | 0.075 |
| qwen3-coder:480b | 0.950 | 0.225 | 0.075 |
| mistral-large-3:675b | 0.975 | 0.250 | 0.000 |
| gemma3:27b | 0.950 | 0.325 | 0.075 |
| nemotron-3-ultra | 0.975 | 0.325 | 0.150 |
| deepseek-v4-pro | 1.000 | 0.475 | 0.125 |
| glm-5.2 | 0.925 | 0.575 | 0.275 |
| qwen3.5:397b | 1.000 | 0.600 | 0.325 |
| deepseek-v4-flash | 0.975 | 0.625 | 0.350 |
| gpt-oss:120b | 0.975 | 0.700 | 0.600 |
| kimi-k2.6 | 0.950 | 0.900 | 0.800 |

Read the first column: **every model of eleven, from 27B to 675B, across six
families, lands between 0.925 and 1.000.** Naming a fault whose category you
were handed is a solved problem. Read the second column: the same models,
same items, same day, range from 0.150 to 0.900. The registered median ratio
of the two is **0.475** (prediction P1, CONFIRMED against a 0.8 threshold).

Now read the second and third columns together. They move as one. The
registered prediction P3 asked whether **any single seat of the eleven** could
reach half the unlabelled faults while flagging at most 15% of clean work.
**P3: REFUTED. Zero qualifying seats.** Not one model could.

Computed post-hoc by this audit from the same committed table — this
correlation was not pre-registered and is offered as the shape of the
registered result, not as a separate finding — the two columns correlate at
Pearson **0.928**, Spearman **0.964**, across the eleven models.

That is the signature of a single dial, not of eleven different abilities.
What differs between these models is not how well they tell a flaw from sound
work; it is how readily they object. Detection of an unlabelled fault is
bought almost one-for-one with false alarms on good work.

**The same fault, labelled and unlabelled — the cleanest form of this
result.** The zoo's exploratory tables break both batteries down by fault
class, and two classes appear in both, which makes them a matched pair. Mean
catch across all eleven seats:

| fault | in the rubric's own vocabulary | the same fault, unlabelled |
|---|---|---|
| circular support | `circularity` — **1.000** (n=5) | `circular_support` — **0.173** (n=10) |
| explaining nothing | `dormitive_vacuity` — **0.970** (n=3) | `vacuous_generality` — **0.491** (n=10) |

Eleven models. Same items' construction, same day, same temperature. Circular
support named as "circularity" is caught by every one of eleven seats; the same
fault not named is caught at 0.173, with **five of the eleven seats at exactly
0.000** (`gemma3:27b`, `minimax-m2.7`, `mistral-large-3:675b`,
`nemotron-3-ultra`, `qwen3-coder:480b`). The pre-registration's own appended
reading adds that the only three items missed by *every* seat are all circular.

Nothing about the fault changed. The label changed. If one measurement in this
audit should be remembered, it is this one.

For completeness, the labelled battery's other classes sit where the first
column predicts — `affirming_the_consequent`, `base_rate_neglect`,
`conjunction_fallacy`, `denying_the_antecedent`, `hasty_generalization`,
`post_hoc_causation` all at 1.000; `composition` 0.970; `false_arithmetic_premise`
0.864; `equivocation` 0.841 — and the unlabelled battery's others at 0.491 to
0.609.

One more line from the same tranche, because it cuts against the intuitive
remedy: turning reasoning on **lowered** unlabelled detection on the model
where it was measured most cleanly — `deepseek-v4-flash` went from 0.625 to
0.400, a 22.5 point fall (prediction P4, per-model rule).

*\* One row must not be read as a measurement.* `minimax-m2.7` failed the
strict-output contract on **64 of its 120 calls**, and those failures are
recorded as "no fault found" — distributed 36 of 40 on clean items, 28 of 40 on
unlabelled faults, and **0 of 40 on labelled faults**. Among its 12 parseable
unlabelled responses it flagged 6, a rate of 0.5 rather than 0.15. Its
apparently excellent specificity is an artifact of not answering, and the
report does not flag it. Both CONFIRMED verdicts survive dropping the seat —
the median ratio becomes 0.5375, still far below the 0.8 line — and P3's zero is
untouched, since minimax was never a candidate to qualify. Every other headline
figure in §1.2 and §1.3 was independently recomputed from the raw judgment
blobs during this audit and matched to the digit.

*Limits, stated because they matter.* Every unlabelled-fault item and every
clean item in this corpus was written by one model, `deepseek-v4-pro`
(`caveats[2]`), so family effects on those two batteries are tangled with the
author's family. And 40 items per cell puts roughly ±0.08 on a rate near 0.5.
Neither touches the first column's saturation, the matched pairs, or P3's zero.

*One aggregation warning, because the record's own headline invites a wrong
reading.* The 2026-07-13 red-team reported cross-family pairs 41 points *worse*
than same-family pairs at unlabelled faults, which reads as a family effect and
is not one. Inside that cross pair, the single `gpt-oss` seat caught 30 of 40
unlabelled faults on its own — better than either same-family seat and better
than every pair. Requiring both seats to agree, with a split counted as no
catch, turned the best single seat into the worst pair. The lesson is about the
vote rule, not about families.

### 1.3 The vocabulary is adopted; the operation is not performed

The 2026-07-14 court calibration built 42 pairs whose faults were known by
construction and put them to a defended court. Its registered verdict P2 is
worth quoting exactly, because it is the cleanest statement of this failure
anywhere in the record:

> `REFUTED - the scope-obsessed court caught 0/7 planted GENUINE scope
> contradictions while grounding most objections in scope formalism`

The court talked about scope constantly and checked scope never. Its per-class
detection:

| planted fault class | caught |
|---|---|
| causal non sequitur | **5 / 7** |
| chronology error | 0 / 7 |
| evidence misquotation | 0 / 7 |
| scope contradiction | 0 / 7 |
| unsupported comparison | 0 / 7 |
| vacuous forbidden case | 0 / 7 |

Overall sensitivity **0.119** against a registered bound of 0.80 (P1:
REFUTED). False conviction of sound work: **0.0**.

**And the fault was not subtle.** This audit opened the corpus. All seven
planted scope contradictions are an exact string appearing in both
`scope.covers` and `scope.excludes`, with the intersection empty in all seven
clean twins. All seven planted vacuous forbidden cases are the *same
byte-identical sentence* inserted into the forbidden-case list: *"Evidence
emerges that contradicts the central claim of this account."* Fourteen items
whose fault is a set intersection or a string match on two adjacent fields.
Caught: 0 of 14. The court meanwhile grounded 74–93% of its objections in scope
formalism.

Eighteen months later, a different model, a different brief, a different
domain, and a sealed pre-registration reproduced the two extremes. In the
2026-09-04 blind-critic tranche, across 480 calls in four conditions,
`scope-contradiction` ran at 0.0 to 0.2 and `vacuous-forbidden-case` at
**0.00 in every single cell** — while overall planted-fault naming sat at
about 0.50.

**Objecting unconditionally is now measured four times, not twice, and it is
not the prompt's fault.** Beyond the two above: on 85 *real* harness artifacts,
three different critic families objected at 85/85, 85/85 and 84/85 — a spread of
1.18 points against a pre-registered 25-point bar
(`bronze_court_cross_v1_report.json`, P1 REFUTED). And across six cells of
critic family × how the artifact was presented, the objection rate was 1.0 in
**all six** (`schema_comparator_v1_report.json`) — so it survives changing the
representation as well as the model, the brief and the domain.

Those four measurements span 2026-07-13 to 2026-09-04 — different harness
builds, different briefs, different forms, different authority defaults,
different models, curated corpora and real run output. Per §0.1 that is what
makes this the best-supported behavioural claim in the report: no constant in
the apparatus could be producing all four, because the apparatus was not
constant.

The obvious explanation is that the brief tells the critic to prosecute. That
was tested and **refuted, and inverted**. Stripping the prompt to a neutral
*"assess for one material, checkable defect"* made things worse: acquittal of
sound work fell from 0.325 to 0.20 — 32 of 40 sound arguments convicted — while
conviction of genuinely flawed work stayed at 1.0
(`defended_trial_v1_report.json`, arm B, P1 REFUTED). Adding a defender and a
two-pass adjudicator then moved the failure rather than fixing it: acquittal of
sound work rose to 0.95, and conviction of genuinely flawed work **collapsed to
0.375** (arm C). This is the single dial of §1.2 again, found by a different
route: every configuration that bought specificity paid for it in sensitivity.

**What the critic convicts sound work *of* is the sharpest part.** On 40
arguments whose central claim a trusted local checker had verified TRUE, the
bare critic convicted 27. Of those 27, **18 named the machine-verified-true
number itself as the defect** (`critic_specificity_report.json`). The
pre-registered falsifier fired — specificity 0.325 against a 0.60 bar and a
0.40 falsifier line — and the tranche's registered consequence was to demote
"survived criticism" as a metric **record-wide**. That demotion is a
pre-registered instrument judgement in this repository's own record, and it is
why no claim in this audit rests on an artifact having survived criticism.

**Two models scoring the same items can disagree completely.** In the clean-item
re-adjudication, the argumentative critic convicted 11 of 11 suspect items,
naming a specific and checkable-looking defect in each, and the strict judge
acquitted 11 of 11 with `flawed: false, kind: none`. All three of that
tranche's predictions were refuted and nothing was reclassified
(`e02_t2b_readjudication_report.json`).

Look at what separates the one class that is caught from the five that are
not. A causal non sequitur is visible in the prose: the sentences do not
follow, and reading them is enough. Every one of the other five requires
holding one part of the document against another part — the claim against its
stated scope, a quotation against its source, an event against a date, a
comparison against its missing baseline, a forbidden case against whether it
forbids anything. **The record's consistent finding is that these models
assess prose for plausibility and do not perform cross-field consistency
checks, even when the instruction names the field.**

A fourth independent measurement of the same class. The 2026-07-13 red-team
built 40 "toothless envelopes" — answers that fill every required field
correctly and commit to nothing falsifiable. Cross-family evaluators caught
**10 of 40** (0.25). And in the live republic run, three prose accounts that
"forbade nothing checkable" were killed — by `skeleton-wf`, a deterministic
program (`docs/STATE_OF_THE_THEORY.md` §II). Across four measurements, the
answer that satisfies the form and says nothing is the fault models do not
see, and the only thing that ever caught it was code.

One arithmetic line from the committed placement analysis puts the whole
section in a sentence. On the 84-item calibration corpus the critic's
item-level objection precision is **42/84 = 0.5 — exactly the base rate of
corrupted items** — so, in that report's own words, *"at this unit level the
objection carries zero information."* Every bit of clean-from-corrupted
separation in that dataset came from the court, which convicted 5 items, all 5
correctly, at a recall of 5 in 42.

### 1.4 A model's report on its own work is not reliable, and this is the model, not the harness

On a construction task with an exact rational checker
(`2026-08-25-change-constructive-frontier`), the model was asked to produce a
configuration and to state its score. **114 of 132** stated scores were wrong
under the checker, and wrong substantively: every one of the 114 belonged to a
configuration whose true value was exactly zero, while the model claimed
positive values up to 0.066.

The tranche's own summary: *"A model asked to construct AND to score its
construction is reliably competent at the first and unreliable at the
second."*

Three arms make this the model's property and not the harness's:

| arm | overclaimed |
|---|---|
| harness arm | 114 / 132 |
| the void run (harness without checker feedback) | 147 / 183 |
| **plain repeated sampling, no harness at all** | **30 / 53** |

The plain-sampling arm has no harness in it. The behaviour survives its
removal.

**The sharpest instance in the record, from the rematch two days later.** The
same problem was re-run with reasoning on in both arms
(`2026-08-27-pc2b-symmetric-reasoning`). Its four scored candidates are in
`arm_h_scores.json`, and every one reads:

    "claim": 0.005,  "score": 0.0,  "score_exact": "0",  "code": "CLAIM_INFLATED"

0.005 is the pre-registered acceptance floor. Four times, for configurations
worth exactly nothing, the model stated **precisely the number that would let the
candidate through** — not a plausible estimate, not a rounding error, the
threshold itself. The same file records `accepted_count: 25` beside
`best_artifact: null`.

That is the whole of §1.4 in one line of JSON. Asked for a measurement of an
object, the model produced the value that satisfies the criterion the
measurement was going to be checked against.

Two more instances of the same shape, from different tranches:

- Told to cite only from a supplied 32-item legend, a seat produced **58**
  citations of identifiers that **do not exist in the record at all** — the
  typed class is `EVIDENCE_REF_UNKNOWN_BLOCK`, first at `log.jsonl` seq 42,
  found mechanically by `tools/record_claims.py`
  (`2026-09-06-change-record-claims/DELIVERY.md`). The distinction matters and
  runs the strong way: the harness has a separate typed class for citing a real
  block that was withheld from the legend, `EVIDENCE_REF_NOT_EXPOSED`, and that
  class appears **nowhere** in the run. So these were not real sources the seat
  was forbidden to name. They were identifiers with no referent.
- A judge ruled against a survivor and cited a decisive point that appeared
  nowhere in the trial exchange. A referential-integrity check — again a
  program — blocked the warrant (`docs/STATE_OF_THE_THEORY.md` §II).

And the corresponding failure of models to catch this in each other: in the
blind-critic tranche a three-reader panel scoring criticisms against five
criteria written in advance gave **1,436 of 1,436** perfect marks on "specific
rather than generic" and on "non-evasion", 1,427 of 1,436 on "the fault is
real", and 1,430 of 1,436 on "the case is made". Only "is it answerable"
varied. The tranche records the rubric as **a failed instrument** — four of
five questions had no variance left to measure.

### 1.5 An instruction can be followed exactly and do nothing

The basin study's complement arm was told, every cycle, to avoid the most
likely continuation. Measured against its own prompt, it obeyed harder than
any other arm: its output landed nearest its displayed examples at **0.49×
chance**, the lowest of seven arms — it genuinely steered away. Novelty gain:
**0.865 against the control's 0.846**, against a registered threshold of
+0.1. Registered verdict: **REFUTED — placebo**.

The tranche's own reading is exact: the directive *"moves the model relative
to its prompt, not out of its own repertoire."* This is a compliance success
and an intent failure at the same time, and it is the shape most likely to be
misread as disobedience by someone who only sees the outcome. (Tier 2 — see
Part 6.)

### 1.6 What these models do follow

The record is not one-sided, and an honest answer has to carry this half.

- **A constraint stated in prose that the model can grasp semantically.** Told
  in the question text that research was confined to a frozen list of two
  hosts (and in another run, one), `glm-5.2` proposed directed research
  unprompted in all three runs, three proposals each, every URL on topic, and
  **never once targeted an off-list host**
  (`experiments/live_research_2026-07-29/RESULTS.md`).
- **A directive to vary.** Across every healthy arm of the basin study, the
  nearest earlier idea was one the prompt had displayed *below* chance —
  0.22× to 0.87×. Told to return diverse candidates, strong models steer away
  from what they were shown.
- **Reporting its own missing evidence.** When fetches were refused, the
  composed answer recorded that the verbatim sources were unavailable and
  downgraded exactly the claims that needed them.

Set the allowlist against the legend, because the contrast is the finding. Two
hostnames the model understands: honoured across nine proposals. Thirty-two
hash-ordered identifiers with no meaning of their own: violated 58 times. The
constraint a model can satisfy by understanding the domain, it satisfies. The
constraint that requires carrying an arbitrary set through generation, it does
not.

### 1.7 What this says about the nature of the thing

Deducible from the above, and stated no more strongly than the record allows:

1. **Instruction-following here is a property of generation, not of
   execution.** There is no step where the instruction becomes a procedure
   that runs. The instruction conditions what the output looks like — its
   form, its vocabulary, its topic — and it is satisfied when the output looks
   right. That single hypothesis predicts all five shapes above: perfect form,
   saturated detection when the category is handed over, vocabulary without
   the operation, self-reports that read as competent and are wrong,
   compliance that achieves nothing.
2. **What varies across models is willingness to object, not discrimination.**
   Eleven models, one dial (§1.2). This is a specific and testable claim about
   what model choice buys you in an evaluator seat: not accuracy, threshold.
3. **Some fields of a structured input are effectively never read.** The two
   classes never caught, in two independent studies eighteen months apart, are
   exactly the fields a checking procedure would have to consult. This is not
   about attention span — the items are short — it is about which operations
   the instruction actually triggers.
4. **A model's claim about its own output carries no information about that
   output.** Measured three ways, including with the harness removed. Every
   place this record catches such a claim, the catcher is a deterministic
   check, never another model.

**Where this generalises and where it does not.** Points 1, 3 and 4 rest on
evaluator seats plus one construction task; point 2 rests on evaluator seats
only. The record does not establish that a model generating open prose fails
in the same way, because the corpus contains no comparable ground-truth
generation battery. Point 4 is the best-supported of the four, because it is
the only one measured with the harness taken away.

---

## Part 2 — What these models could not do here

**The answer in four sentences.** The record supports two limits, not a long
list. The first is that these models cannot check a thing against a standard
when the checking has to be *done* rather than described — they produce the
check's output reliably and its result unreliably. The second is separate and
was the surprise of this audit: offered a working tool, a budget, and an
explicit invitation to do second-order work — answer this objection, cite this
premise, run this simulation — they decline, at 129 declines out of 130
invitations across two runs. Everything else the record might look like it
shows about "cannot" is either a single run, a task the models were never
given, or something this repository's own code prevented, and I separate those
below because conflating them is how a code defect becomes a false claim about
language models.

**The discipline used.** Four buckets, and only the first supports a limit
claim: (i) failure repeated under measurement, (ii) failure in one run, (iii)
never attempted, (iv) prevented by the harness's own code. Even bucket (i)
licenses only *"not observed to, under these conditions"* — never *"cannot in
principle"*. Nothing in this record could establish the latter.

### 2.1 Bucket (i) — measured repeated failure

**Scoring its own construction against an exact criterion.** 297 attempts
across three arms, one of which had no harness in it: 114/132, 147/183, 30/53
wrong. This is the best-supported limit in the record, because it survives
removal of every part of the apparatus except the model
(`2026-08-25-change-constructive-frontier`).

**Finding a fault it was not given the category for, without paying for it in
false alarms.** Eleven models, zero qualifying seats against a registered bar
of "half the unlabelled faults at no more than 15% false alarms"
(`e02_t3_judge_zoo_report.json`, P3 REFUTED). This is the widest-support limit
in the record — eleven models, six families, 27B to 675B, temperature 0.

**Checking one part of a document against another.** Scope against claim,
quotation against source, event against date, comparison against baseline,
forbidden case against whether it forbids anything. Four independent
measurements, two of them eighteen months apart with different models and
briefs, agreeing on which classes are never caught (§1.3). The record's own
strongest instance: 0 of 7 planted scope contradictions caught by a court that
grounded most of its objections in scope formalism.

**Detecting an answer that satisfies every requirement and commits to
nothing.** 10 of 40 cross-family (`e02` toothless envelopes), 0.00 in every
cell of the blind-critic tranche, and in live running the only thing that ever
caught one was a deterministic program.

**Taking up an invitation to do second-order work.** This is the finding that
most changed during the audit, and it is measured on live runs with the
occasion actually offered:

| what was offered | what happened |
|---|---|
| an invitation to answer a premise question and cite it (run P-S1) | **1 accepted, 122 declined** |
| the same, run P-A1 | **0 accepted, 7 declined** of 2 invitations and 6 batch offers |
| an objection to discharge, P-A1 | **19 left undischarged, 6 re-asks issued, 0 discharges recorded** |
| a working contained simulation runner with a 12-of-12 budget, on a question whose pre-registration says its natural moves are small exhaustive checks and Monte Carlo | **0 simulation proposals in 5 cycles** |
| an enabled scratchpad | **no event carries a scratch payload** |

Sources: `2026-09-01-live-all-modules-p-a1/module_census.json`
(`top_signals`, `measured.D3_premise_citation_rate`) and `MODULE_COVERAGE.md`
rows D3 and the did-not-fire table; the P-S1 comparison is registered at
`PREREG.md:394`.

Read the last two rows carefully, because they are the strongest form of this
finding. The tool was configured, budgeted, probed available, and the question
was chosen *because* its natural moves would exercise it. The model used
neither. Across 130 invitations to answer a premise, one was taken.

Two caveats that keep this in bucket (i) rather than making it decisive: the
P-A1 run died at cycle 5 of 24 on a typed operational failure, so its numbers
are five cycles' worth; and "declined" is a typed disposition the harness
records, which means the model produced a well-formed refusal rather than
silence — consistent with §1.1, and worth noting because it means the channel
worked and the answer was no.

### 2.2 Bucket (ii) — measured once, and reported as once

**Beating blind repeated sampling where an exact checker exists.** On one
instance of one construction problem, at a matched measured budget (ratio
1.009), the full conjecture-and-criticism harness scored 0.0004075 and plain
repeated sampling of the same model scored 0.0135949 — a factor of 33. The
harness's best construction was worse than the best of 2,000 random uniform
draws (0.002824). Non-degenerate constructions: sampling 74%, harness 0.8%.

The tranche argues its early stop does not explain the gap (the harness
reached its ceiling by cycle 10 and did not move for five more cycles) and
records honestly that its one pre-authorised repeat was never run. **One
instance, one model, one run per arm, no repeat.** It is a real result and it
is not a law.

**Converting a correct diagnosis into a search.** In that same run, the
vocabulary census found the trap named in all 15 valid candidates
(`avoid-collinearity`, 15/15) and **zero** mentions of any search strategy —
nothing about local refinement, symmetry breaking, or targeting the binding
triple. The run diagnosed the problem and did not attack it. One run, and the
tranche attaches no threshold to it; it is quoted because it is the most
legible thing the record says about what imagination looked like there.

**Abandoning an idea that has been refuted.** One refutation drove a
stance-pinned arm to re-propose equivalents of the dead idea 54 times, plus 27
cycles registering nothing, at 4.3× the tokens per idea that stuck; a weak
model run hot did the same at 36. Every arm with no refutation had no such
activity. This is a conjunction — a refuted idea exists *and* the generator
cannot rotate off it — and neither half alone produced it. (Two arms, n=1
each, and Tier 2: see Part 6.)

**Producing an answer a blind panel rates as well as one plain call.** Three
plain calls scored a saturated 15/15; the stripped-down harness flow's eight
candidates scored 5.62 mean, best 10, at 7.6× the spend. The pre-registered
verdict is INDISTINGUISHABLE and improvement is **NOT SHOWN**, because the two
arms did not overlap in length (7,645 against 546 characters) and the rubric
was written for an essay
(`2026-09-05-change-mini-isolation-programme/RESULTS.md`, D8). This is a null
result about the harness, not a limit of the model.

### 2.3 Bucket (iv) — what this repository's own code prevented, and must not be reported as a model limit

Three absences in the corpus look like devastating capability findings and are
not. I state them because they bound every claim above, and because reporting
them as model limits would be the central error available to this audit.

**No idea was ever carried to a second question.** Zero reach events across 96
roots and 1,178,430 candidate pairs. The cause is in the code, not the model:
the corpus's entire qualifying vocabulary is **two form gates**, and an
artifact passes a form gate exactly when it was built carrying it — so the
cell that reach requires (a criterion novel to the artifact *and* passed by
it) is empty **by construction**, 0 in every case for both criteria. The
model was never in a position to demonstrate reach. The tranche's own verdict
is that zero is the correct answer
(`2026-08-21-measure-reach-firing/RESULTS.md`).

**Criticism almost never changed anything.** 60 attack links against 5,165
support links in 6,370 artifacts; 76 of 96 roots with none at all. The cause
is configuration: the argumentative critic's authority defaults to
observe-only, so a critic files scrutiny and mints no warrant. The judge-
evidence review states the consequence plainly — 26 of 31 measured roots are
in the state where prose cannot refute anything, **by default**
(`2026-08-09-change-judge-evidence-review/REVIEW.md` §4, §8.1).

**No criticism was ever itself criticised, and no objection was ever
answered.** Every attack relation in the corpus is one hop deep, and there are
zero recorded discharges across every source root of the blind-critic tranche.

**Partly corrected, and this is the audit correcting itself.** I first wrote
that the record could not tell whether this was an inability or an absence of
the occasion. That is too weak. In the P-A1 live run the occasion WAS offered
and typed: the discharge channel fired, 6 re-asks were issued, **19 objections
were left undischarged, and no discharge was recorded**; the premise channel
offered work and got 7 declines, against P-S1's 1 accepted and 122 declined
(§2.1). So for *answering* an objection the record does show repeated failure
under measurement, on the occasion being given.

What remains genuinely untested is the other half — a model criticising a
criticism. No run in the corpus granted the authority and exercised the road
that would produce a second hop, so the depth-1 shape of all 6,370 artifacts
still cannot be read as a limit.

### 2.3a The strongest confound in the corpus: criticism was never shown to the thing that writes the next candidate

This deserves its own heading because it bounds every criticism finding in this
report, and it is measured rather than inferred.

The run-anatomy tranche W2 took the two priority live roots and asked whether
criticism did causal work. Its answer, from generated tables rather than prose:

- **0 of 196 model-written attacks were ever exposed to a later conjecture
  dispatch.** Not a low rate — zero. The criticism was written, recorded, and
  never put in front of the seat that makes the next candidate.
- **Every status any criticism moved was moved by the problem's own admission
  criteria.** All 118 attack edges in one root and all 345 in the other come
  from demonstrative warrants minted by mechanical commitment verdicts; **0 come
  from a model-written attack**, and no model attack in either run carried a
  warrant at all. Every criticism dispatch was `observe_only`.
- The tranche's own summary: *"two organs called criticism, one of which is
  load-bearing and is not criticism, and one of which is criticism and is
  inert."*

And the measurement discipline is worth copying. Because candidates are
generated in batches, the candidate following a criticism is usually a fresh
construction that would have differed anyway — so every rate was computed twice,
once on the candidate *after* the criticism and once on the candidate *before*
it, which cannot have been influenced. The difference is the only evidence:

| root | n | coupling | placebo | **difference** | did any coupled change improve the score? |
|---|---|---|---|---|---|
| P-R1, mechanical | 118 | 17.8% | 30.5% | **−12.7 pp** | — |
| P-R1, prose-quote | 54 | 98.1% | 100.0% | **−1.9 pp** | — |
| P-C1, mechanical | 341 | 9.4% | 3.5% | **+5.9 pp** | **not one of 32** |
| P-C1, prose-quote | 60 | 100.0% | 100.0% | **+0.0 pp** | — |

Three of four placebo-corrected effects are zero or negative, and the fourth
bought nothing. Note what that means: it is not a finding that criticism does
not work. **It is the correct result for a channel that was shut**, and it
validates the instrument. Any apparent coupling without that placebo column is
an artifact.

A companion finding from W3 bounds the evidence channel the same way: **591 of
623 admitted evidence blocks were never shown to any model**, because the
citable legend caps at 32 — 93% of the dossier by bytes, admitted, digested and
frozen, and *"nothing in the record discloses that the truncation happened."*

**What this does to the rest of this report.** It strengthens §2.3's attribution
of the corpus's near-empty attack graph to configuration rather than to the
models, and it means Part 5's third gap is worse than "unmeasured": in the two
roots examined closely, the mechanism whose value was in question was not
connected. Every statement in this report about what criticism did or did not
achieve should be read as a statement about criticism that could not have
achieved anything.

### 2.3b One experiment could not run because the models were right

Recorded here because an audit of limits that omits it is dishonest. The
decisive-criticism experiment was pre-registered to measure whether criticism
fixes errors, and it needed a baseline error rate of at least 0.10 to have
anything to fix. Two independently constructed 8-question probes returned **80
of 80 candidates correct** — a base error of 0.0. An escalation arm on a smaller
cross-family model reached a base error of 0.023, with every error a minority of
4-of-5 or 3-of-5, so no majority was ever contested. Registered outcome:
`regime_not_reached` (`experiments/criticism_decisive_prereg.yaml`).

The experiment failed because the models did not make mistakes. That is a
capability finding, and it belongs beside the others.

### 2.4 What the record cannot support, and why

| a claim one might want to make | why the record cannot carry it |
|---|---|
| LLMs cannot criticise their own criticism | never attempted: authority defaults to observe-only and no run exercised a second hop, so depth-1 everywhere is an absence of occasion (§2.3). Note this is now narrower than it was: *answering* an objection WAS offered and failed, 19 undischarged after 6 re-asks |
| LLMs cannot explore beyond their training data | explicitly not measured anywhere. Every novelty number in this record is distance from the model's *own earlier answers in the same run*. `docs/CAN_LLMS_EXPLORE.md` says so in its own boundary paragraph and asks for help closing exactly this gap |
| criticism does not improve output | two instances where the harness did not beat plain calls, both single-run, both with named measurement defects, and neither designed to isolate criticism |
| these limits hold for language models generally | most of the corpus is one provider model (`glm-5.2` on Ollama Cloud). The one broad result is the eleven-model zoo, and its unlabelled-fault and clean items were all authored by a single model |
| a limit is intrinsic rather than conditional | nothing here separates "this model, this prompt, this budget" from "models of this kind". No experiment in the corpus varies the prompt shape and the model together on a ground-truth battery |
| reasoning effort helps | measured once, on three models, and it *lowered* unlabelled detection on the cleanest arm by 22.5 points |

**The honest form of the answer to Q2.** Two classes, and the record reaches
both from several directions.

*The first is applying a criterion and returning the result*, as opposed to
producing text of the shape that applying it would produce. Everything the
models were asked to check — their own scores, a claim against its scope, a
quotation against its source, a form against whether it forbids anything — they
described competently and got wrong. Everything they were asked to *produce* —
candidates, objections, essays, research proposals, well-formed envelopes — they
produced fluently and in volume. Six independent measurements, one of them
across eleven models.

*The second is taking up work that is offered rather than asked for.* An
objection to answer, a premise to cite, a simulation to run on a question chosen
because simulation was its natural move, a scratchpad to think in: each was
configured, budgeted and reachable, and each went unused — 129 declines in 130
invitations, 19 objections undischarged after 6 re-asks, zero simulation
proposals, zero scratch payloads. This is a weaker finding than the first (two
runs, one of them five cycles long) and it is a different shape: not an
operation performed wrongly, but an available move not made. If one thing in
this report deserves a dedicated experiment, it is this.

---

## Part 3 — Are these models creative?

**The answer in four sentences.** On the one sense of the word this record
measures well, yes, and by more than the project previously believed: the same
model at the same temperature yields three to four times as many genuinely
distinct ideas depending only on how you ask for them, at roughly eight times
the distinct ideas per token. On the sense most people mean — producing
something outside what the model was trained on — the record says nothing at
all, and says so itself. On whether the extra ideas are any *good*, the record
is explicitly silent, by a decision taken before the data existed. And on the
one thing that would settle the question in this project's own terms — whether
the harness makes the model's output better than the model alone — the two
measurements that exist both came back null or worse.

The word does four jobs. Taken separately, they get four different verdicts.

### 3.1 Sense one — how many distinct ideas can be got out of it: MEASURED, and the answer is "far more than repeated asking suggests"

This is the strongest creativity evidence in the repository and it is Tier 1:
2,243,500 tokens, 216 cells, 7,236 calls, 12,794 candidate ideas, raw responses
committed, every metric recomputable
(`2026-08-28-diversity-generation`). One model, `glm-5.2`, one temperature
(0.9), thinking off, three questions, four ways of asking.

Distinct ideas per 49 candidates, averaged over nine repetitions:

| how it was asked | open question A | construction question | open question B | overall |
|---|---|---|---|---|
| ask directly, repeatedly | 8.0 | **1.7** | 5.6 | 5.1 |
| ask with named directions first | 5.7 | **6.0** | 7.7 | 6.4 |
| ask for ten at once, self-rated | 27.0 | **3.4** | 22.3 | 17.6 |
| both | 23.7 | **12.0** | 24.2 | 20.0 |

And the cost, which is the number that should change behaviour:

| how it was asked | distinct ideas per 1,000 tokens |
|---|---|
| ask directly, repeatedly | 0.38 |
| ask for ten at once | **3.16** |

**Eight times more distinct ideas per token.** Not bought by degrading
anything: the invalid rate of the cheap method was 0.12 percentage points
*below* the expensive one, and no condition exceeded 0.55%. An external note
had projected the ten-at-once method would cost about 1.1× more; measured here
it is **2.4× cheaper per candidate**, so this repository's own measurement
refuted an external projection rather than importing it.

Two disciplines make this trustworthy. The ordering holds at every threshold
in the registered grid. And leg 1 of the experiment had a broken primary
measure that could not have separated anything — it was diagnosed, the rule was
fixed, and **leg 1 was deliberately not re-scored**, because tuning a measure
on the data that exposed its flaw and then reporting the result is how a
pre-registration is quietly spent. Leg 2 measured on data that did not exist
when the new rule was frozen.

**The exception is as important as the rule.** On the tightly constrained
construction question, asking for ten at once barely helped (3.4 against 1.7)
and only the arms carrying an explicit planning step lifted it (6.0, 12.0).
Whatever the cheap method does, it does not do it where the problem is tightly
constrained. There, being made to plan first is what worked.

**A cross-tranche inference, marked as an inference and now carrying a
demotion.** The basin study concluded that novelty fades because the model runs
out of distinct answers, having ruled out the prompt as the cause — it removed
the model's view of its own prior output and the fade continued at the same rate
(0.888 against 0.846). The diversity experiment then got three to four times as
many distinct ideas from the same model by changing not what it was *shown* but
what it was *asked for*. Both can be true, and together they say something
neither says alone: **the ceiling the basin study found looks like a property of
asking the same question over and over, not a property of the model's
repertoire.** The project's phrase "repertoire exhaustion" is better read as
exhaustion of what one prompt regime can reach.

Two things weaken this and must travel with it. It is an inference across two
tranches, not a result either registered. And the basin half of it rests on
novelty numbers this repository has itself demoted to unverified — see §6.4,
which is the most consequential finding of this audit for Q3.

### 3.2 Sense two — distance from what it was trained on: NOT MEASURED, and the record says so

Every novelty number in this repository is distance from the model's own
earlier answers within one run. `docs/CAN_LLMS_EXPLORE.md` states this in its
own boundary paragraph before any result, repeats it in its "does not show"
section, and ends by asking outside readers for the one thing that would close
the gap — problems where what lies outside the model's training is
independently known.

So the question most people mean by "are LLMs creative" is **untouched by this
record**. No amount of careful reading of these documents will produce an
answer to it, and any answer that appears to come from them is an
overreading. Part 5 says what would be needed.

### 3.3 Sense three — are the extra ideas good: DELIBERATELY NOT MEASURED

The diversity experiment measured distinctness and nothing else, and registered
that limit in §9 of its pre-registration before any call: whether a more
distinct population of ideas is a more *valuable* one, whether the extra ideas
survive criticism, and whether the cheap method buys variety by wandering
further from the question, are all parked and unmeasured. Its own words:
*"Nothing in section 2 licenses a claim about conjecture quality."*

The record also contains a sharp warning against reading the harness's own
acceptance as quality. In the construction run, **909 artifacts were accepted
and 163 refuted while every one of the run's 132 actual constructions failed
the checker.** The tranche's conclusion: acceptance in this harness is survival
of whatever criticism happened to be generated, and here demonstrably not a
statement that the artifact is any good.

### 3.4 Sense four — originating something by its own work: one suggestive instance, and the record's weakest standing

Two instances are worth the operator's attention, and both need their standing
stated.

**The self-directed creativity run** (Tier 3 — `mini_creativity_report.json`
is not in the tree; see Part 6). Asked why an LLM's novelty collapses when it
keeps generating, a small model produced 27 surviving ideas, two of which
(#18, #27) named self-conditioning converging to a fixed-point attractor — the
exact framing this harness was built around — and one of which (#22) proposed
periodically refreshing the prompt with diverse ideas, which is this harness's
own remedy. Neither was in its prompt. `docs/CAN_LLMS_EXPLORE.md` is careful
about what this is and the care should be preserved: attractor dynamics, mode
collapse and diversity prompting are all documented ideas, so this is
recombination, not evidence of reaching past the data. A footnote with teeth:
the calibrated judge ranked the attractor theory first and the
prompt-refreshing remedy **dead last** — the theory that best matched the
harness's own findings was the judge's least favourite.

**The poietics run** (Tier 1 — run root, `verify_root.json` and
`milestones.json` committed). Asked when a test constrains its subject rather
than merely describing it, and given this repository's own evidence to work
from, the largest group of surviving ideas was *deflationary*: it argued the
evidence could not support a general condition. One of them located the
underdetermination exactly — that the repository's own 3-of-26 result *"cannot
distinguish between 'the test constrained its subject' and 'the subject was
never mutated in a way that would test the constraint'"*. That is a correct and
useful criticism of the evidence it was handed, and it was not in the prompt.
It is one run, it is prose, and the audit records it as the clearest instance
in the corpus of a model producing a criticism worth having — which is a
different and lesser claim than origination.

### 3.5 Sense five — better than the same model without the harness: MEASURED FOUR TIMES, NEVER SHOWN

This is the project's own success criterion (the operator's law of
2026-09-03: the condition of success is something materially better than what
the same model produces without the harness). Two measurements exist:

- **Construction** (`2026-08-25-change-constructive-frontier`): harness
  0.0004075, plain repeated sampling 0.0135949, matched budget. The harness
  claims no value on that instance, and `milestones.json` records
  `harness_claims_value: false`. One instance, no repeat.
- **Composition** (`2026-09-05-change-mini-isolation-programme` D8): three
  plain calls scored 15/15 median on a blind three-reader rubric; the harness
  flow's best candidate scored 10, mean 5.62, at 7.6× the spend. Verdict
  INDISTINGUISHABLE, improvement NOT SHOWN, with the measurement's own defect
  named — the arms did not overlap in length and the rubric was written for the
  essay shape only one arm produced.

**And this is a replication, not a first.** In 2026-07, with a pre-validated
scoring instrument and decision rules committed in advance, the
rank-concentration experiment tested whether the criticism-and-adjudication
apparatus improved the *best* artifact over raw generation plus self-selection.
Its registered result, verbatim from
`experiments/rank_concentration_prereg.yaml`: *"the criticism/adjudication
apparatus showed NO measurable quality advantage over raw generation +
self-selection on these informal problems — and lost outright on one."*
H_rank REFUTED on both fresh problems: one at a margin of −0.372, the other
+0.055 against a +0.15 bar, and pooled ranks all ≤ 0. Its control gates passed,
so the instrument was discriminating.

A fourth: the reasoning-on rematch of the construction problem two days after
P-C1 also lost, and the size of the loss is itself the finding — **4%**
(0.013308 against 0.012778) where P-C1 had been 33×, at a budget match of
1.0248, with the harness terminating `completed`/`converged` at cycle 17 of 24
(`2026-08-27-pc2b-symmetric-reasoning/RESULTS.md`). Turning reasoning on in both
arms shrank the gap by nearly two orders of magnitude and did not close it.

That makes **four** independent occasions, spread over fourteen months and
three different task families — informal prose, exact construction, and
composition — on which this apparatus was measured against the plain model and
did not win. Per §0.1, and this is the part that matters: those were three
*different builds* of the apparatus, not three trials of one. No single
implementation was tested three times, which is a weakness; but no single
implementation's defect can explain all three either, which is a strength, and
the second outweighs the first here because the three tasks share nothing but
the model.

Neither of the 2026 tranches is a fair test of criticism's value and both say
so. What can be said is narrower and still worth saying: **in this record there
is no measured case of the harness making the model's output better than the
model alone, and four cases of it not doing so.** Every other live tranche either has
no such arm or records its absence as a decision — the blind-critic tranche,
the history-channel tranche and the conjecturer-interface tranche each state in
their own residue sections that no baseline arm exists.

### 3.6 The verdict, per sense

| sense of "creative" | verdict | standing |
|---|---|---|
| produces many genuinely distinct ideas | **YES**, and 3-4× more than repeated asking reveals, at ~8× per token | Tier 1, 2.24M tokens, one model |
| sustains distinctness under repeated asking on one question | **NO** — it fades, and the fade is inside the model, not the prompt | **DEMOTED** (§6.4), n=1 per condition |
| the distinctness can be restored by structural means | **YES** for rotating the angle (0.973 vs 0.846) and changing the question (1.12); **NO** for telling it to be different (placebo) | **DEMOTED** (§6.4), n=1 per condition |
| cannot let go of an idea already refuted | **YES** — 54 and 36 blocked re-proposals from single refutations, at 4.3× the tokens per idea that stuck | Tier 2 and **NOT** demoted: these are counts of a gate that ran hash-and-verdict-only, so they do not depend on the demoted instrument (§6.4) |
| the extra ideas are *good* | **NOT MEASURED**, registered out of scope in advance | — |
| reaches outside its training distribution | **NOT MEASURED**, and the record says so in its own words | — |
| originates something by its own construction | one suggestive instance, self-described as recombination; one clear instance of useful criticism | Tier 3 and Tier 1 respectively |
| beats the same model without the harness | **NOT SHOWN**, four times across three task families and four builds; margins from 33× to 4% against it | Tier 1, single-run each |

The one-line answer, if only one line is wanted: **these models hold far more
distinct ideas than the ordinary way of asking gets out of them, and this
record cannot tell you whether any of those ideas were new to the world or
merely new to the conversation.**

---

## Part 4 — What this record can prove incorrect in the semantics document

**Scope, first, because the operator narrowed it.** The document is a guide and
the target of this question, not the audited artifact. I have not audited its
mathematics, its internal consistency, or its cross-references, and its own
defeat condition 6 — a mathematical counterexample to a displayed theorem — is
therefore out of scope here. The question I answer is the one that stays inside
the record: **which of the document's claims does this repository's evidence
bear against?**

**The structural answer, before the tally.** Very little of the document *can*
be proved incorrect by any record, and the document says so itself: its
closing section calls it a contract for attribution claims and concedes it is
"unfalsifiable in the harmless way checklists are." A condition that says what
would have to be true for an attribution to hold cannot be refuted by
measurement; only the document's claims *about the world* can. There are few of
those, which is why the tally below is small — and it is why the one hit is
worth more than a longer list would be.

Nine contacts were worked. One is proved incorrect, two are confirmed (one of
them substantively), one exhibits a gap the framework's vocabulary cannot
express, and five are not testable from this record.

### 4.1 PROVED INCORRECT — that nothing operational follows from receipts

The document demotes its receipt construction to an appendix and gives the
reason (§5.5): *"Its value is diagnostic: it forces an interpretation of an
argument's actual dependencies. Its cost is that nothing operational follows
from it, and 2.0 declines to pretend otherwise."* Appendix A repeats that no
downstream definition depends on it.

The load-bearing property of that construction is that an argument's leaves
are references to actual events plus their interpretation, so a leaf can be
checked against what is really there. This repository implemented that
property, and three operational consequences followed:

1. **A status change was prevented.** A judge ruled "fail" against a surviving
   account and cited a decisive point that appeared nowhere in the trial
   exchange. The referential-integrity check blocked the warrant. The
   run's own narrative calls it *"arguably the run's most important moment,
   because it is the guard doing precisely what it exists for against a real
   model's confabulation"* (`docs/STATE_OF_THE_THEORY.md` §II).
2. **A pre-registered claim was mechanically refuted.** Told to cite only from
   a supplied legend, a seat produced 58 citations of identifiers not in it,
   recorded as typed `EVIDENCE_REF_UNKNOWN_BLOCK` measures, the first at
   `log.jsonl` seq 42. `tools/record_claims.py` read those and returned claim
   `ORG-CITE-01` as REFUTED with its counterexample named
   (`2026-09-06-change-record-claims/DELIVERY.md`).
3. **A defect was found and fixed because the check re-derives what the writer
   wrote.** `experiments/2026-08-03-fix-attached-evidence-integrity` exists
   because `invariants.py` re-derives the attached-evidence triple that
   `evidence/render.py` writes; `docs/ERRATA.md` E2 records that no document
   told the reader's author what the writer guaranteed.

A blocked conviction, a refuted claim, and a fixed defect are operational
outcomes. **The claim that nothing operational follows from requiring an
argument's leaves to resolve is false on this record.**

Two boundaries on the hit, so it is not oversold. The document's full receipt
construction is richer than what this repository built — distinct sufficient
routes as distinct receipts, negation exchanging positive and negative receipt
sets, timeout as delivery evidence — and this record exercises none of those.
The refutation reaches the *"nothing operational follows"* clause about
checkable leaves, not every clause of Appendix A. And this is good news for the
document rather than bad: it says a part 2.0 demoted was worth more than 2.0
credited it with.

### 4.2 CONFIRMED, substantively — the grain-fixing discipline works, and the record prices it

Section 9.4 requires that the grain, boundary and contrast contract be fixed
*before* the contrast evidence is examined, forbids absorbing a counterexample
by re-graining afterwards, and accepts a cost: *"it removes the framework's one
structural escape hatch, at the price of making applications slower. That price
is accepted deliberately."*

This repository is the closest thing to an empirical test of that discipline
that exists anywhere in this record: 52 pre-registrations, several sealed by
digest in the commit that carries them. The discipline holds, and it holds
where it costs something:

- **Predictions were refuted and recorded as refuted, repeatedly.** Basin P1
  refuted as its committed conjunction, P3 *refuted and inverted*, P4 refuted
  as a placebo; red-team P1 and P3 refuted; judge-zoo P3 refuted with zero
  qualifying seats; court calibration P1 and P2 refuted; diversity H1, H2 and
  H3 inconclusive by rules frozen in advance; the rank-concentration hypothesis
  refuted on two fresh problems; the history channel's cost prediction
  falsified and then, on replication, unresolved.
- **The bar was not moved once the numbers were visible, and the record says so
  in as many words.** Diversity leg 1 had a saturated primary measure; the rule
  was repaired and **leg 1 was not re-scored**, because *"tuning a metric on
  the data that diagnosed its flaw and then reporting the result is how a
  pre-registration is quietly spent."* The blind-critic tranche, holding a
  matched-pairs split at p = 0.066 against its own 0.05 bar: *"the bar is not
  being moved now that the numbers are visible."* Those are two instances of
  exactly the escape hatch 9.4 exists to close, being closed.
- **The registration caught an instrument failure from inside itself.** Leg 1's
  primary measure could not have separated anything — and the threshold curve
  and a threshold-free second measure had been registered in advance precisely
  so a saturated primary could not hide a real signal. Both separated the arms
  while the primary reported nothing.
- **The price is real and this record quotes it.** Leg 1 spent **1,118,171
  tokens** and produced an instrument diagnosis and no verdict. The mini D8
  measure met its registered floor and still could not answer its question
  because the arms did not overlap in length. That is 9.4's "applications
  slower" clause, in tokens.

Confirmed, then, with one addition the document does not make: the discipline's
benefit arrives mostly as *catching your own broken instrument*, not as
catching a wrong hypothesis.

### 4.3 CONFIRMED — graded accounting with exposed residue

Section 2.3 says an attribution that displays its residue is a complete and
honest claim at its stated coverage. The record supplies the cleanest possible
test and confirms it, in the strong form: **when these documents were wrong,
the correction landed inside the residue they had already exposed.**

`docs/ERRATA.md` E79 corrected "history-ON conjectures are judged worse" to a
length effect — and adds, unprompted: *"Not a defect in the original reading:
that document measured the same length coupling on its own 167 candidates
(ρ = +0.797), reported the length-adjusted gap beside the raw one, and named the
possibility that the gap 'was the length shift wearing a merit label'. The
replication cashed the caveat."* E78 corrected a cost finding that did not
replicate, and notes both originals *"said in their own text that one pair could
not settle it."*

Eighty errata entries, and the two that touch a capability claim both
landed where the residue pointed. That is what 2.3 predicts.

*One thing the record adds against the claim's practical value:* exposing the
residue did not prevent either error from being asserted as a finding and, in
E78's case, being cited by a specification section to set a shipped default.
Honest form is not the same as a claim that will not mislead a reader in a
hurry.

### 4.4 A GAP THE FRAMEWORK CANNOT EXPRESS — help that supplies nothing

Section 8.3 tests an enabling condition by what it *supplies*: it must be
described by "physically and semantically meaningful resources and
contributions", must not deliver the target achievement, and must not include a
complete functioning solution. Primitive P5 requires those resources be stated
independently of the success claim.

The diversity experiment exhibits something that apparatus has no slot for.
Asking one model, at one temperature, for ten candidates in a single request
rather than asking it ten times, yielded **3 to 4 times as many distinct ideas
and about 8 times as many per token** — with the same question, the same
content, the same information supplied. Nothing was added. The request was
restructured.

By the document's own line this is admissible help, because the model still
does all the construction. But the framework has no way to *describe* it: it is
neither a resource supplied nor an achievement delivered. A capability
attribution stated in this vocabulary would come out identical across two
conditions whose measured output differs by a factor of four. That is not a
defeat under any item of section 10.2 — but it is a place where the framework
cannot say what this record clearly measures, and it is the honest answer to
"what is wrong with the document" for this contact: not an error, a blind spot.

### 4.5 NOT TESTABLE FROM THIS RECORD — five contacts, and what each is missing

| the document's claim | why this record cannot reach it | what is missing |
|---|---|---|
| §3.4 (H-int): the admitted variation family is generated by the account's own content, and reach tightens it | the mechanism never operated once. Zero reach across 96 roots and 1,178,430 pairs — and the cause is in this harness's code, not the claim: the only criteria in the corpus are two form gates whose pass condition is identical to their carry condition, so the cell reach needs is empty by construction | a corpus with content criteria an artifact can pass without having been built carrying them |
| §3.5 reach | same reason | same |
| §2.4: an answer table without anchoring fails (E) | the record never states (E)'s conjuncts for any artifact. The court's scope formalism with 0 of 7 detection is a candidate for "satisfies the form, explains nothing", but nobody established structural, composition and question fidelity for it, so satisfaction is unproven | an artifact for which each conjunct of (E) is separately evidenced |
| §9.3: no merit function is supplied "and not missed" | nothing here refutes it, and the record leans mildly *for* it — a rank tournament put the theory best matching the harness's own findings last, and 909 artifacts were accepted in a run where every one of 132 constructions failed the checker. Supportive, not decisive | a case where a count was needed and its absence blocked a correct verdict |
| Appendix B: no experiment establishes that any actual system satisfies any class defined here | **the record agrees**, and for recursive critical capacity it agrees more sharply than Appendix B claims: 96 runs and 6,370 artifacts produced no chain of criticism longer than one hop, no attacker was ever itself attacked, and no objection was ever answered. But the authority to attack defaults to observe-only, so the record cannot say whether that is a limit of the models or an absence of the occasion | one run with criticism authority granted and a discharge road exercised |

### 4.6 The tally

| contact | verdict |
|---|---|
| §5.5 / Appendix A — nothing operational follows from receipts | **PROVED INCORRECT** |
| §9.4 — grain-fixing discipline | **CONFIRMED**, with its price measured |
| §2.3 — exposed residue is honest at its coverage | **CONFIRMED**, twice, mechanism visible |
| §8.3 / P5 — enabling conditions described by what they supply | **GAP** — cannot express a measured 4× effect |
| §3.4, §3.5, §2.4, §9.3, Appendix B | **NOT TESTABLE** from this record |

One proved incorrect out of nine, and the one that lands is a claim the
document made *against its own machinery*. That is the honest result. A record
of experiments about language models is simply not the instrument that refutes
a framework of satisfaction conditions — and the document's section 10.3 says
as much, which this audit reads as accurate rather than evasive.

---

## Part 5 — What cannot be supported, and exactly what is missing

The operator asked for this explicitly, and it is the half of the audit most
worth acting on. Each row is a claim someone reading this record might want to
make, why it cannot be made, and the one measurement that would settle it.

### 5.1 The gaps that matter most

**1. Whether these models can explore past their training data.** Untouched.
Every novelty number in the record is distance from the model's own earlier
answers inside one run. *Missing:* problems where what lies outside the model's
training is independently known — post-cutoff facts, held-out mathematical
constructions, or domains generated after training — put through the same
instruments. `docs/CAN_LLMS_EXPLORE.md` names this itself and asks outside
readers for it.

**2. Whether more distinct ideas are better ideas.** The largest and cleanest
experiment in the corpus measured distinctness and registered quality out of
scope before any call. So the eight-times-per-token result buys variety of
unknown worth. *Missing:* the same four conditions with the candidates put
through criticism, and survival rates compared. The tranche's own `PARKED.md`
holds this.

**3. Whether criticism improves anything.** Worse than unmeasured. In the two
live roots examined closely, **not one of 196 model-written attacks was ever
shown to the seat that writes the next candidate** (§2.3a), and every status
change came from mechanical verdicts instead. So the three occasions on which
this apparatus lost to the plain model (§3.5) tested a pipeline in which the
organ under suspicion was not connected. *Missing:* one question, matched
budget, four arms — plain repeated sampling; generation with criticism actually
rendered into the next dispatch; generation with an equal quantity of vacuous
criticism; and the same with authority granted — judged blind with length held
constant, with W2's before-and-after placebo column computed. The vacuous arm is
what turns a pipeline comparison into a measurement of criticism; the rendering
is what makes the comparison mean anything at all.

**4. Whether a model can criticise a criticism.** Still never attempted:
every attack relation in 6,370 artifacts is one hop deep and no run exercised a
second hop. *Missing:* one run with criticism authority granted and a
criticism-of-criticism road actually reachable. **Answering** an objection is no
longer in this gap — P-A1 offered it and got 19 undischarged after 6 re-asks —
but the run died at cycle 5 of 24, so *missing* there too: the same run
completed.

**5. Whether the failure shapes in Part 1 hold for generation as well as
evaluation.** Points 1, 3 and 4 of §1.7 rest mostly on evaluator seats.
*Missing:* a ground-truth generation battery — items where the correct output
is known by construction — run against the same models.

**6. Whether varying what a seat is shown changes what it produces, against a
no-harness baseline with length held constant.** This experiment exists. It is
designed, its arms are built, its pre-registration is sealed by digest, and it
**was never run** — `experiments/2026-09-04-experiment-brief-variation-step1/`
has a `PREREG.md`, five arm definitions, a rig, soak logs and no results
document. It is the single highest-value unrun experiment in the repository for
Q1, and it needs only a credential.

### 5.2 The limits that bound every number above

**Run-to-run variance is comparable to every effect the corpus reports.** This
is the most important methodological fact in the record and it is easy to miss.
`docs/ERRATA.md` E78, correcting the history-channel tranche: across three
paired runs with **every input identical**, the control arm alone ranged from
314,220 to 541,666 tokens and from 4.71 to 6.70 judged of 15 — *"a run-to-run
spread comparable to every between-arm difference the experiment has
reported."* Any single-run comparison in this corpus, including the 33× margin
in Part 2 and the null in §3.5, sits inside noise of that order until repeated.

**One provider model carries most of the corpus.** `glm-5.2` on Ollama Cloud.
The one broad result is the eleven-model zoo, and its unlabelled-fault and
clean items were all authored by a single model, so family effects there are
tangled with the author's family.

**n = 1 per condition is the norm.** The basin study, the constructive-frontier
arms, the mini D8 arms, the reach-rich run. The two exceptions are the
diversity experiment (nine repetitions per cell, and an unplanned independent
replication of 1.1M tokens in which three of four arms reproduced to within
0.002–0.015) and the judge zoo (eleven models, 40 items per cell).

**The older instrument understates.** The basin work used a 128-dimension
hashing embedder deliberately, because it is the one the production detector
used. It cannot separate within-question from cross-question distance at all
(medians 0.645 against 0.671). Real effects there are, if anything, understated
— which makes its confirmations conservative and its refutations of small
predicted effects weak.

**Capability use is stochastic across identical runs.** The repository's own
operating rule states it: one live attempt that misses a path is inconclusive
for that path. So an absence in a single live run is not evidence of inability.

**One confound to carry into any re-reading of pre-2026-08-28 live tranches.**
`2026-08-28-audit-run-problems` P10 found five "everything on" switches that
never reached a manifest-launched run, with nothing recording the fact — so
runs launched that way executed under a criticism authority their configuration
did not declare. Any earlier live measurement of criticism behaviour should be
re-read with that in mind.

---

## Part 6 (appendix) — Findings about evidence standing, not about models

**Why this is here at all, given the scope.** None of what follows is a finding
about language-model behaviour, and the operator has said plainly that the
harness is not the subject. It is included for one reason: each item decides
whether a number in Parts 1 to 4 can be relied on. §6.4 in particular determines
the standing of the answer to Q3, so leaving it out would make Part 3 dishonest.
Read this as the audit showing its working on evidence quality, not as a second
audit of the machine.

### 6.1 The oldest capability evidence is archived, not lost — and the signposts do not reach the reader

**This section replaces a wrong finding, and the correction is the point.** The
audit first recorded that thirteen report files cited by nine committed
documents were absent from the tree and not excluded by `.gitignore`, and read
that as evidence gone missing. That framing is wrong, and the repository itself
says why.

`experiments/results/INDEX_2026-07-13.md` records one deliberate act: the 61
pre-rebuild result files under `experiments/results/` were **removed from the
working tree on purpose**, with the reason given, a recovery point named — commit
`3d839b3`, *"the last commit containing the complete record"* — and an explicit
paragraph headed **"Citations elsewhere"** which names `docs/CAN_LLMS_EXPLORE.md`,
`docs/BASIN_REPORT.md`, `docs/STATE_OF_THE_THEORY.md` and `docs/MINI_PLAN.md` as
documents that cite retired paths, stating that those citations refer to the
archived commit and the claims they back are unchanged.

So the evidence was retired with a pointer, not lost. An audit that had stopped
at "the file is not there" would have filed a false finding against a
repository that had already done the honest thing.

**What survives the correction, and it is narrower and worth acting on:**

1. **The pointer is a bare commit hash, and it does not resolve here.**
   `git cat-file -t 3d839b3` returns *"Not a valid object name"* in this
   container, because this is a shallow clone truncated at 2026-08-30. Any
   session, contributor or CI job working from a shallow clone — which is how
   this environment gets the repository — cannot follow the pointer.
2. **The citing documents do not carry the pointer.** `docs/BASIN_REPORT.md`
   opens with a `Data:` line naming `basin_offline_report.json` and
   `basin_live_report.json`, with nothing to say the files were retired or where
   they went. `docs/CAN_LLMS_EXPLORE.md` invites outside readers to
   *"re-derive it from the log or re-run the arm yourself"* — a reader who
   accepts that invitation gets a dead path, and the note that would rescue
   them lives in a file those documents do not link. The retirement is
   documented in the index; it is not documented where a reader arrives.
3. **Ten of the thirteen appear in neither index.** Only `basin_offline_report`,
   `basin_live_report` and `operator_probes` are named in the pre-rebuild
   `INDEX_2026-07-05.md`. `mini_creativity_report`, `mini_chaos_report`,
   `mini_gauntlet_report`, `mini_smoke_report`, `mini_seat_certification`,
   `lambda_v2_report`, `stress_campaign_report`, `controller_ab_report`,
   `cache_design_report` and `cachebench_report` are named by no index at all —
   while `docs/MINI_STRESS_REPORT.md`, `docs/REPORT.md`, `docs/STRESS_INSIGHTS.md`,
   `docs/CONTROLLER_SPEC.md`, `docs/CACHE_DESIGN.md` and
   `docs/CAN_LLMS_EXPLORE.md` cite them as their evidence. The repository's own
   standing guidance in that same index reads *"An experiment that isn't in an
   index does not exist."* By that rule these ten are unresolved: not retired
   with a pointer, not present, not indexed.

**What none of this changes.** The tiering used throughout this report stands
exactly as written, because it was always about what a reader of `main` can
re-derive today, and that is unchanged: the basin and exploration numbers stay
Tier 2 (their pre-registration and verdicts are committed in
`experiments/basin_study_prereg.yaml`), and the λ grounding comparison in
`docs/REPORT.md` stays Tier 3.

**The cheap fix, which is now a documentation task rather than a data
recovery.** A one-line note in each of the nine citing documents saying the
data is archived and where — and, for the ten unindexed files, an index line or
a note that they are not recoverable. Neither costs a measurement.

**One methodological note on the audit itself.** The wrong version of this
finding was produced by reading the working tree and the ignore rules and
stopping there. It was caught by reading a file that documents the act. That is
the same failure shape this report attributes to the models in Part 1 — a check
performed on the fields in front of it, not on the fields that would settle it —
and it is recorded here rather than quietly fixed.

### 6.2 The strongest capability evidence and the most-cited capability evidence are not the same documents

`docs/CAN_LLMS_EXPLORE.md` is the document written for outside readers, and it
is Tier 2 with n = 1 per condition on a deliberately scale-blind instrument.
Meanwhile the eleven-model judge zoo — 1,561 judgments, temperature 0, ground
truth by construction, three pre-registered verdicts, report committed — is
cited by no capability-facing document at all, and it carries the single widest
result in the repository: **no model of eleven could find half the unlabelled
faults without flagging more than fifteen percent of sound work.**

That is a presentation gap, not an evidence gap, and it is cheap to close.

### 6.3 Two capability claims in standing documents that the record does not carry as stated

**The judge law in `CLAUDE.md` compresses two different units into one range.**
Its amended text reads *"0-2.5% false conviction of sound work"*. The 0.0 is the
defended court's *sustain* rate on 42 clean items
(`court_calibration_v1_report.json`); the 0.025 is an unanimous judge *pair's*
flag rate on 40 clean items with no defender present
(`e02_t2_voting_report.json`). Two instruments, two units, two corpora. The
review tranche that produced the amendment names both sources in the same
sentence and is scrupulous about it; the compression into one range happened
when the finding was carried into the standing law. Not wrong, but a reader who
takes "0-2.5%" as one measured interval is reading something the record does not
have. The same law's *"11.9% sensitivity"* is single-sourced and exact.

**A precedent worth citing for how to fix that.** `experiments/results/`'s own
index carries a model for it: `INDEX_2026-07-13.md` records that the
`bronze_flat_v1` interpretation was superseded and lists the **withdrawn
claims** by name — among them *"F4 as model circling (gate-manufactured
embargo)"* and *"'zero novel mechanisms' as a measured result"* — with the
original report, pre-registration and corrections all left unedited. Two
capability claims withdrawn, in writing, with the reason. That is the pattern
§6.1's fix should follow.

### 6.4 The project measured that its own novelty instrument was wrong, set a gate on repeating the claim, never ran the gate, and published the claim

This is the most consequential finding in the audit, because it decides the
standing of the answer to Q3, and every word of it is the repository's own.

**What was measured.** `E0.1`, a zero-token recalibration, compared the hashing
embedder every novelty number in this record was computed with against a real
neural embedder (`BAAI/bge-small-en-v1.5`). **All four pre-registered
predictions were REFUTED.** The decisive one: the proportion of
"hash-novel" ideas that a real embedder scores as near-duplicates was predicted
at 20% or less, with a falsifier at 40%. Measured: **1.0 on both roots.** In the
report's own words — *"under the neural embedder the corpus cross-problem median
distance (0.26) sits BELOW the planted-paraphrase median (0.32): the entire
conjecture stream is more homogeneous than typical paraphrase pairs. What
hashing scored as variation is near-duplication at neural scale."*

**What the pre-registration said would follow, written before the numbers.**
From `docs/EXPERIMENT_PROGRAM_2026-07.md:135-137`: *"Falsifier: > 40%, and the
soft-basin finding may be an embedder artifact; **E2.3 must run before the basin
claim is repeated anywhere.**"* And the program's own reason for running E0.1 at
all, at line 143: the scale-blind embedder *"can hide real convergence, meaning
every self-diversity number in `docs/CAN_LLMS_EXPLORE.md` is suspect."*

**What the index recorded as the consequence**, verbatim from
`experiments/results/INDEX_2026-07-13.md:75-77*: *"Consequences: prior hash-based
novelty numbers demoted to unverified; E2.3 now gates any repetition of the
soft-basin claim."*

**What then happened.** `E2.3` exists only as a plan. There is no report in
`experiments/results/`, no tranche directory, and no run. By the same index's own
standing rule — *"An experiment that isn't in an index does not exist"* — it did
not happen. And `docs/CAN_LLMS_EXPLORE.md`, the document written for outside
readers and inviting them to replicate, presents the soft-basin claim as its
Result 1 and contains **no mention** of E0.1, of the contamination measurement,
of the neural embedder, or of the demotion. Neither does `docs/BASIN_REPORT.md`.
Both discuss the embedder's weakness at length — and both argue it in the
*opposite* direction, that the instrument's blindness makes real effects
understated and confirmations conservative. E0.1 measured the error running the
other way.

**How far the demotion reaches, precisely, because this decides what survives.**

- **Demoted:** every novelty *level* and every late/early *ratio* in the basin
  study and in `docs/CAN_LLMS_EXPLORE.md` — 0.846, 0.888, 0.973, 0.865, 1.037,
  1.12 — and the echo-vs-chance figures, which locate a nearest neighbour with
  the same embedder. These are hash-based novelty numbers and the registered
  consequence names them.
- **Not demoted, and this preserves the strongest basin finding:** the
  gate-block counts (0 in every healthy arm, 54 and 36 in the two orbiting
  arms) and the 4.3× cost figure. The anti-relapse gate has three paths — hash
  identity against a refuted prior, an embedding path, and battery equivalence
  over a verdict vector — and the embedding path ships disarmed
  (`config.py:350`, `NEAR_DUP_EPS: float | None = None`, with the comment at
  line 704 confirming none ship armed). So in this era the gate was
  hash-and-verdict-only. **Refuted-attractor orbiting does not depend on the
  demoted instrument.**
- **Scope that cuts both ways:** E0.1's own caveat is *"n=2 roots, both
  gemma4:31b website runs"*, and the basin live phase was a different model on a
  different workload. So the contamination measurement does not directly cover
  the basin corpus — which is precisely why E2.3 was made the gate rather than
  the demotion being called final. The honest state is not "the basin finding is
  false". It is **"the basin finding is unverified by this repository's own
  ruling, and the experiment appointed to resolve it was never run."**

**Why this matters more than a bookkeeping lapse.** Q3 is the operator's
creativity question. The repository's most quotable creativity evidence, in its
most public document, is evidence its own calibration study demoted — and the
strongest *undemoted* creativity result in the whole corpus, the 2.24M-token
diversity experiment with its raw responses committed and a neural embedder, is
cited by no capability-facing document at all (§6.2). The evidence is in better
shape than the documents are. Part 3 is written that way deliberately: its
verdict rests on the diversity experiment, and the basin material carries its
demotion wherever it appears.
