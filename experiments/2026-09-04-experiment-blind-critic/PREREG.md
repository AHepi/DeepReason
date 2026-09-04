# Pre-registration — does a blind critic perform better?

Written 2026-09-04, BEFORE any experimental provider call. The only live
calls made before this file was written were four reachability probes
against the provider (SPEC M5), which read no target and produced no
measurement. The commit that seals this file (`PREREG.sha256`) precedes,
in `git log`, the commit that adds anything under `raw/`, and that
ordering is the evidence that nothing here was chosen after a number was
seen.

Answers the operator's question of 2026-09-04: *"Can you establish that a
blind critic, not judge, actually performs better?"* — and the earlier
hypothesis of 2026-09-03: *"criticism without fully understanding the
reasoning behind a conjecture might help sharpen critiques."*

---

## 1. Why this exists at all

The one previous attempt at this question came back INCONCLUSIVE on every
registered measure, and not from bad luck: its measures were computed
over `att`, the relation of attacks that landed, so "of the attacks that
landed, how many landed" could only ever be 1.000. That was recorded, in
its own tranche, as the standing lesson — a measure computed over a
relation defined by the property being measured cannot fail.

This design's first obligation is not to repeat it. Every measure below
is computed over EVERY criticism call, from the typed form the critic
filled, not from `att`. `att` appears in exactly one measure, M3, where
it is the numerator and the call count is the denominator, and M3 carries
a floor warning stating in advance that it is not expected to
discriminate.

---

## 2. The census — what the critic is shown TODAY

Measured by rendering, not by reading (`cells.py --census`).
`seat-pack.critic.legacy-v0` has thirteen sections:

| plugin id | section | carries provenance? | carries history? |
|---|---|---|---|
| `dr.problem-context` | problem-context | no — the problem's own text | no |
| `dr.target-commitments` | target-commitments | no — commitment ids and their eval | no |
| `dr.machine-evaluation-boundary` | machine-evaluation-boundary | no — a fixed note | no |
| `dr.standing-attacks` | standing-attacks | no | PARTLY — attacker ids and the target's own status label, when `att` holds edges; never a rebuttal, never a discharge, and empty on every target in this set |
| `dr.target.support-chain` | target-support-chain | no — ref ids and roles | no |
| `dr.target.support-content` | target-support-content | no — the refs' text | no |
| `dr.frame.crisis` | frame-crisis | no | no |
| `dr.frame.slice` | frame-slice | no | no |
| `dr.target` | target | no — the id and the body, nothing about who wrote it | no |
| `dr.counterexample-recourse` | counterexample-recourse | no — a fixed note | no |
| `dr.premise-invitation` | premise-invitation | no | no |
| `dr.evidence.citable` | citable-evidence-blocks | no | no |
| `dr.output-contract.critic` | output-contract | no — a fixed directive | no |

**Verdict of the census: both blindnesses are real and both are today's
default.** No section names a school, an author seat or an origin — and
that is structural, not incidental: `render_crit_pack`'s signature has no
parameter that could carry them, and a committed check pins that
(`DR-CON-criticism-source`). No section carries a rebuttal or a
discharge. The one partial exception, `dr.standing-attacks`, renders
LANDED attacks only, and no target in this set has one.

Rendered proof, on a target authored by `school-2` with one recorded
objection against it: the shipped brief names neither. Pasted in full in
step 3's checklist entry.

---

## 3. The two factors and the four cells

    F1 provenance   OMITTED (today)  vs  PRESENT: author seat, school, origin
    F2 history      OMITTED (today)  vs  PRESENT: the objections already
                                          raised against this target, and
                                          what became of each

    C00  labels OMITTED, history OMITTED   <- today's shipped brief, byte-identical
    C10  labels PRESENT, history OMITTED
    C01  labels OMITTED, history PRESENT
    C11  labels PRESENT, history PRESENT

Each cell is one registered layout: the shipped thirteen entries plus
zero, one or two more. Selection is one environment assignment. The
epistemic state is byte-identical across all four cells, so nothing
varies but the brief. Zero bytes under `src/` change, measured by sha256
over every `.py` in the package before and after the registration.

**F1's "origin" carries no variance, and that is stated here rather than
discovered later.** The record's `Provenance` holds `role`, `school` and
`event_seq`; there is no `origin` field, so origin is read off `role`
(SPEC A1). Every target in this set is conjecturer-authored, so the
origin line reads "harness-minted" on all 120. The school line varies
across four schools. F1 is therefore, in practice, a school-and-seat
label test, and no claim about origin exposure may be drawn from it.

**F2 is PRIOR-OBJECTION exposure, not rebuttal history.** Measured across
every source root: zero discharges of any kind ever recorded (`revised`,
`rebutted`, `departure_declared` — none), zero landed objections. The
record holds the objections and the fact that nobody answered them. That
is what C01 and C11 carry, because it is all any configuration could
carry. The half of the operator's F2 that names rebuttals cannot be
tested here, and the residue says so.

---

## 4. The targets

120 accepted conjectures from five committed roots, selected by a rule
fixed before any of them was read: order every eligible artifact by
`sha256(artifact_id)`, take the first 120, the first 60 are PLANTED and
the last 60 CLEAN. Eligible = accepted, not import bookkeeping,
conjecturer-authored, a body carrying `claim`, `mechanism` and a `scope`
object, and at least one recorded objection against it (137 of 238
qualify; the history clause is a power requirement — SPEC A9).

The same 120 targets go to all four cells. This is a matched design: any
difference between cells is a difference in the brief, never in what was
criticised.

    SELECTION.sha256  b07661e35069277c476a994420af14a5eec629e29e9be9f2a0978a7e60ce4e53
    schools: school-0 33, school-1 28, school-2 27, school-3 32

## 5. The planted defects

Six classes, ten each, by the judge study's own method
(`scripts/court_calibration_corpus.py`): deterministic, no model call, a
mechanical edit to a parsed copy, exactly one defect per artifact, and an
assertion after every mutation that exactly one field differs.

| class | field | source |
|---|---|---|
| `unsupported-comparison` | `mechanism` | the source's, verbatim shape |
| `causal-non-sequitur` | `mechanism` | the source's, verbatim shape |
| `vacuous-forbidden-case` | `counterconditions[0].case` | the source's, including its verbatim vacuous-case string |
| `evidence-misquotation` | `mechanism` | the source's semantics; its `prose_notes` field does not exist in this shape |
| `scope-contradiction` | `scope.excludes` | the source's semantics — the same case in scope and out of it — realised by writing the claim's own leading sentence into `excludes` |
| `circular-mechanism` | `mechanism` | NEW, replacing `chronology-error`, which needs a year this domain has none of |

    DEFECT_KEY.sha256  b1813c10848092fe849a53a611146bf86a6c609e1eccbdbd6671af82d95b4b74

---

## 6. The measures — fixed here, computed only from the record

**No number a model reported about its own performance enters any
measure.** The critic's `attack` boolean and `case` text are fields of
the typed form it was asked to fill, not self-assessments; no score,
confidence or rating is requested from any critic, and none would be
admitted.

### M1 sensitivity — planted defects the critic's criticism NAMES

Denominator: the 60 planted targets, per cell. Numerator: those whose
criticism names the planted defect. Two detectors, both blind to cell,
both fixed here:

- **PRIMARY — a three-grader panel.** Each grader independently sees the
  clean body, the planted body, the defect note, and the criticism text.
  It never sees the cell, the layout, the arm, or any other grader's
  answer. Question: *does this criticism identify THIS specific defect?*
  Answer: `yes` / `no`, plus one line of justification. Majority of
  three decides.
- **SECONDARY — a deterministic lexical detector.** Fixed per class
  before any call:

      unsupported-comparison   the case names the comparison, the
                               reference class, or its unsupportedness
      causal-non-sequitur      the case names the appended conclusion
                               or calls the step a non-sequitur
      evidence-misquotation    the case names the attribution, Erdos,
                               Renyi, 1959, or the fabricated citation
      circular-mechanism       the case names circularity, begging the
                               question, or the claim-as-its-own-reason
      scope-contradiction      the case names the scope exclusion or the
                               contradiction between claim and scope
      vacuous-forbidden-case   the case names the countercondition as
                               vacuous, circular, or forbidding nothing

  The exact token lists live in `measure.py` and are frozen by this
  file's digest.

Agreement between the two detectors is REPORTED, never reconciled. Where
they disagree, the panel governs and the disagreement rate is stated
beside every M1 number.

### M2 false attack — sound artifacts the critic attacks

Denominator: the 60 CLEAN targets, per cell. Numerator: those where
`attack` is true.

**Saturation rule, fixed in advance.** The record holds two disagreeing
prior measurements of the bare critic on sound work — an objection rate
of 1.0, and an acquittal rate of 0.325 — both on other models and other
briefs. So M2 may saturate. If `min(M2) >= 0.95` or `max(M2) <= 0.05`
across the four cells, M2 is declared NON-DISCRIMINATING; the verdict
rule's M2 clause is then reported as unmet-by-saturation and carried
explicitly into every verdict sentence, never silently dropped.

### M3 warrant rate — criticisms that become attack edges

Per cell: `att` edges minted, over criticism calls that returned a parsed
form. Reported alongside `attack=true` counts and scrutiny events, and
the identity `attack_true >= att_edges` is asserted — that assertion is
what proves the denominator is not `att` again.

**Floor warning, fixed in advance.** Criticism authority is `observe_only`
in all four cells (SPEC A8: the operator asked about a CRITIC, and a
trial authority would put a judge ensemble between the critic and every
measure). Under `observe_only` an edge arises only from a grounded
counterexample, and the prior tranche's land rates were 3/52 and 1/38.
M3 is therefore expected at or near zero in every cell. **M3 is
pre-registered as UNDERPOWERED and may not decide a verdict.** It is
reported descriptively.

### M4 spend per criticism

Prompt, completion and total tokens per call, per cell, from the
endpoint's recorded usage. Caps are matched: identical model,
`max_tokens`, `timeout_s` and pack token budget in all four cells, and a
config-identity assertion proves it rather than asserting it.

### M5 sharpness — blind-judged

The three-judge protocol of
`experiments/2026-09-03-change-provenance-history-channel/JUDGING_PREREG_COPIED.md`.

**ADOPTED UNCHANGED:** three judges scoring independently; 0-3 per
criterion; the MEDIAN of three totals, not the mean, so one outlier
cannot carry a candidate; the contested flag on any item whose three
totals span more than 4 points; structural blinding; and the keymap
stays shut until the scores are committed. Also adopted unchanged: that
document's own closing statement — this is a ranked opinion with its
criteria written down in advance, not a measurement.

**RE-FIXED, because the copied criteria 1-5 are written about one seed
question's Popperian content and a criticism is a different object.**
Five criteria for a criticism, each scored 0-3:

1. **Specific rather than generic.** Does the case turn on something in
   THIS target's text — a named step, a named claim, a named condition —
   rather than on a complaint that would fit any conjecture?
   0 = would fit anything; 3 = quotes or names the load-bearing part.
2. **The fault is real.** Is what it points at actually a fault, rather
   than a restatement of the claim, a preference, or a demand for more
   detail? 0 = no fault identified; 3 = a defect a competent defender
   would have to answer.
3. **The case is made, not asserted.** Does it say WHY the thing it
   names is wrong? 0 = a verdict with no argument; 3 = an argument whose
   steps a reader can check.
4. **It is answerable.** Does it state what would rebut it — a condition,
   a counterexample, a piece of evidence? 0 = unfalsifiable disapproval;
   3 = names what would settle it.
5. **Non-evasion.** Does it resist the two cheap exits: (a) attacking the
   target's framing instead of its content, (b) hedging into "further
   work is needed". 0 = takes an exit; 3 = holds the point.

Total 0-15. Ties broken by criterion 2, then 1.

**Blinding.** `blind/criticisms.jsonl` rows carry exactly `{bid,
target_text, criticism_text}` and nothing else, asserted on the key set
rather than inspected. `bid` is a random UUID4 carrying no cell, target,
ordering or arm information; rows are emitted sorted by `bid`. The cell,
the layout, the school, the author seat and the arm are OMITTED
ENTIRELY — never blanked, never marked redacted. That is structural and
it follows the record's own finding: a present-but-empty provenance slot
draws MORE attention than a populated one, so there is no slot.
`blind/keymap.json` is written in the same commit as `blind/scores.json`
and never before.

**Residual leakage the panel cannot remove, stated rather than hidden:**
a criticism's own text may name the school it was told about. Cell C10
and C11 criticisms could therefore self-identify. Any such row is scored
anyway and flagged in the scoring file against its `bid`, and the
flagged count is reported beside M5.

---

## 7. Sample size, and its arithmetic

Two-proportion test, alpha 0.05 two-sided, power 0.80, detecting a
20-point difference at the least favourable base rate (p = 0.5):

    (1.96 + 0.8416)**2 * 2 * 0.25 / 0.20**2  =  98.11

So **99 planted observations per factor level**. Each factor level pools
two cells (F1 OMITTED = C00 + C01; F1 PRESENT = C10 + C11), so 60 planted
targets per cell gives **120 observations per level** — a margin that
survives up to 17% unusable calls. The same arithmetic covers M2 over 60
clean targets per cell.

Total: 120 targets x 4 cells = **480 criticism calls**.

The matched design is additionally analysed by McNemar over the
target-matched cell pairs, which needs fewer observations than the
unpaired test above; the unpaired test is the PRIMARY and the paired one
is reported beside it.

The request asked that the number come from "M3's saturation numbers".
It cannot: the prior tranche's sustain rate was 1.000 in every cell and
carries no variance to power anything. The usable numbers from that
tranche are its objection volumes (52 and 38 criticism artifacts; 3 and
1 warranted), and what they determine is that M3 is floor-limited — which
is why the sample size is set from M1, the measure the request actually
asks to be sensitive.

---

## 8. The verdict rule

Applied per factor, to the two levels, each pooling its two cells:

    d1 = M1(OMITTED) - M1(PRESENT)        (the blind side minus the informed side)
    d2 = M2(OMITTED) - M2(PRESENT)

**BLIND BETTER** iff `d1 >= 0.20` AND the two-proportion z-test on M1
gives `p < 0.05` AND `d2 <= 0.05`.

**INFORMED BETTER** iff `-d1 >= 0.20` AND `p < 0.05` AND `-d2 <= 0.05`.

**INCONCLUSIVE** otherwise — including the case of a significant M1
difference bought at a worse false-attack rate. That case is not
"better": the operator's own law of 2026-09-03 makes "performs better"
mean more real error found at no worse false attack, and more criticism
is not more error found.

If M2 is declared non-discriminating by section 6's saturation rule, the
`d2` clause cannot be evaluated; the verdict is then stated on M1 alone
WITH that caveat attached in the same sentence.

M5 does not enter the verdict. It is a ranked opinion and is reported as
supporting or not supporting the M1 verdict, with the reason it is not
decisive.

---

## 9. What this tranche is allowed to conclude

Three limits, from CLAUDE.md's standing laws, each binding on the
RESULTS:

- **Better means more real error found at no worse false attack, never
  "more criticism" and never "correct."** Success is progress over what
  the same model does without the harness (2026-09-03). A cell that
  attacks more is not a cell that performs better, and a cell whose
  criticisms are more correct-sounding is not either.
- **Judges are used only where the operator's own protocol uses them,
  and blinding is structural.** The 2026-08-28 judge law: label exposure
  carries the bias, and the fix is that renderers OMIT provenance fields
  entirely rather than blanking them. This tranche uses graders for M1's
  primary detector and judges for M5, both blind by omission, and puts
  no judge between the critic and any measure.
- **This is not a no-harness baseline.** The 2026-09-03 law asks every
  live experiment to carry or cite a baseline arm against what the model
  produces WITHOUT the harness. This tranche compares four harness
  configurations against each other and carries no such arm. It
  therefore cannot say whether critic exposure makes the harness better
  than a single model call — only which of four briefs finds more of a
  known defect. Recorded here so the omission is a decision.

## 10. Falsifiers, named in advance

- If M1 is at or near 1.0 in every cell, the planted defects were too
  easy and the instrument cannot discriminate. Reported as a failed
  instrument, not as "no effect".
- If M1 is at or near 0.0 in every cell, the planted defects were too
  subtle for this seat at this cap, or the naming criterion is too
  strict. Same disposition.
- If M2 saturates, section 6's rule fires.
- If the two M1 detectors disagree on more than 25% of planted targets,
  the M1 number is reported with that disagreement as its headline
  caveat and no verdict is asserted on M1 alone.
- If fewer than 100 of the 120 observations per factor level parse, the
  level is underpowered against section 7's arithmetic and the verdict is
  INCONCLUSIVE by construction.

## 11. Operating conditions, fixed here

    critic seat      one model, identical in all four cells
    authority        observe_only, all four cells
    concurrency      at most 3 concurrent provider calls
    credential       read at call time from the tranche's gitignored env
                     file; never committed, never echoed, never logged
    caps             identical max_tokens, timeout_s and pack token
                     budget across cells; asserted, not assumed
    launch           detached, snapshot loop armed
    raw evidence     every call's rendered pack, reply payload and usage
                     preserved under raw/

Every one of the 480 calls is preserved. Nothing is re-run to get a
better number; a call that fails is recorded as a failure and counted in
the denominator's shortfall, per section 10's last falsifier.
