<!-- COPIED VERBATIM, NOT AUTHORED HERE.

Source: experiments/2026-09-02-episode-config/JUDGING_PREREG.md
Branch: claude/model-profile-registry-opkgal (fetched read-only; NOT merged --
        C9 puts merging that branch out of scope)
Copied: 2026-09-03, by instruction C10 ("copy it, cite it").

Everything below this comment is that file's bytes, unaltered, including its
three amendments and its closing statement that the pick is "a ranked opinion
with its criteria and its blinding written down in advance" rather than a
measurement.

WHAT THIS TRANCHE CHANGES, stated here so no reader mistakes the copy for the
whole protocol. The criteria (1-5), the 0-3 scoring, the tie-breaks (criterion
4 then 1), the blinding, the keymap-stays-shut rule and the three-judge median
are ADOPTED UNCHANGED. Two things are re-fixed in PREREG.md because this
tranche measures different arms:

  * the QUESTION is the same seed question (C10), so criteria 2-5, which are
    written about that question's specific machinery, transfer verbatim;
  * the ARM LABELS differ (H0/H1, the four budget rungs, C0/C1), so the keymap
    maps to those instead, and M3 adds two measures the copied protocol has no
    criterion for -- re-raised already-rebutted objections, and cases the
    defender sustains -- which are counted from the record, never judged.
-->

# Pre-registered blind judging protocol — episode config, arms A/B/C

Written 2026-09-02, WHILE ALL THREE ARMS WERE STILL AT CYCLE 0 and before
any candidate text from any arm had been read by the monitor. Commit
timestamp is the evidence; the harvest script (`harvest_candidates.py`)
was written and committed after this file and is the first thing that
reads candidate text.

## Why this exists

The monitor designed two of the three configurations under test (A and B).
A pick made after reading candidates already labelled by arm is not a
measurement, it is a preference. So the criteria are fixed here first, the
candidates are stripped of every provenance marker before they are read,
and the winner is mapped back to its origin only after the scores are
written down.

## What is judged

EVERY candidate conjecture from all three arms, including discarded ones.
"Discarded" means: candidates inside a `workflow-provider-attempt-v1`
payload that were not admitted, candidates from attempts that failed
semantic admission entirely, and candidates from any attempt superseded by
a later one in the same work item. The unit of judgement is one candidate
claim (the `claim` field, falling back to `content` — 40 of 82 candidates
in the prior tranche used `content`, and reading only `claim` silently
produced empty strings and artefactual diversity numbers; see
2026-09-02 mini-as-generator RESULTS.md).

Episode-generator output that never reached a conjecture artifact is NOT
judged as an answer. It is material, not a submission. It is counted in
cost and in variety, not in the answer pick.

## Blinding

`analyse.py --blind` writes `blind/candidates.jsonl` with fields
`{bid, text}` only. `bid` is a random UUID4 with no arm, cycle, run,
object-hash or ordering information in it. The arm/cycle mapping goes to
`blind/keymap.json`, which the monitor does not open until
`blind/scores.json` is committed. Candidates are emitted in an order
seeded by sorting on `bid`, so file position carries no origin signal.

Residual leakage the monitor cannot remove and states rather than hides:
a candidate's own text may name its stance, school, or the fact that it
was built from a ranked pool. If a candidate's text betrays its arm, the
score for it is still recorded, and the leak is noted in the scoring file
against that `bid`.

## Criteria — fixed here, applied unchanged

The question asks for three things: the strongest case for EACH answer,
a verdict on which survives, and what accepting the verdict COSTS. A
candidate that does one of the three well and skips the others is not a
better answer than one that does all three adequately. Scored 0-3 each:

1. **Both cases made, and made at strength.** Is the case for "the
   preference is defensible on Popper's own terms" and the case for "it
   smuggles induction back in" each stated in its strongest form, rather
   than one being set up to lose? 0 = one side only or a straw man;
   3 = both sides stated as a competent proponent of each would state them.

2. **Engagement with the actual Popperian machinery.** Does it turn on
   what corroboration IS in Popper (a report on past test performance,
   explicitly not a probability, explicitly not a prediction) and on the
   specific move that is contested (the pragmatic preference of
   *Objective Knowledge* / the *Realism and the Aim of Science* reply to
   Salmon)? 0 = generic philosophy-of-science prose that would fit any
   question; 3 = the load-bearing distinction is named and used.

3. **A verdict that is actually a verdict.** Does it say which one
   survives and commit to it? 0 = "both have merit"; 3 = a stated
   survivor with the reason it survives.

4. **The cost is named and is a real cost.** Does it say what accepting
   the surviving answer gives up — and is that a genuine loss rather than
   a restatement of the verdict? 0 = no cost, or a cost that costs
   nothing; 3 = a specific concession that a defender of the surviving
   answer would find uncomfortable.

5. **Non-evasion.** Does it resist the two cheap exits: (a) dissolving
   the question by redefining corroboration until the tension vanishes,
   (b) conceding Salmon's point and calling the residue "pragmatic" as
   though naming it settled it. 0 = takes an exit; 3 = the tension is
   held and answered.

Total 0-15. Ties are broken by criterion 4, then 1.

## What "best" means for the report

The single highest total wins. If two candidates tie after both
tie-breaks, both are reported. The monitor also reports the highest
scorer from EACH arm, so the operator can see whether the winner's arm
won on its best candidate or on its floor.

## What the pick is NOT

The pick is one reader's scored judgement against fixed criteria on
blinded text. It is not a measurement of arm quality: n=1 question, one
judge, no inter-rater check, and the judge built two of the three arms.
The variety and cost tables are measurements; this is a ranked opinion
with its criteria and its blinding written down in advance so the
operator can discount it accurately.

---

## Amendment 1 — a panel replaces the single reader (2026-09-02)

Written BEFORE any arm completed a cycle and before any candidate from the
scored epoch existed. The criteria above are UNCHANGED; only who applies
them changes.

The protocol above ended by admitting its own weakness: "one reader, no
inter-rater check, and the judge built two of the three arms." That is
fixable, and leaving it unfixed when it is fixable would be a choice.

**What changes.** Each blinded candidate is scored independently by THREE
judges that do not see each other's scores, against the five criteria
exactly as written above. Each judge returns the five sub-scores and a
one-line justification per criterion, so a score can be checked against
its own reasoning rather than taken on trust.

**Aggregation, fixed here.** A candidate's total is the MEDIAN of the three
judges' totals, not the mean — one judge scoring an outlier cannot carry a
candidate. Disagreement is reported, not hidden: any candidate whose three
totals span more than 4 points of 15 is flagged in the output as contested,
and the operator sees that flag next to the winner if it applies.

**Runoff.** The top 5 by median go to a second round in which each is
compared head-to-head against the others by three fresh judges, again
blind. This exists because scoring in isolation and ranking against rivals
are different judgements, and the operator asked for the single best answer.

**What does not change.** The criteria, the tie-breaks (criterion 4 then
1), the blinding, the keymap-stays-shut rule, and the closing statement
that this is a ranked opinion rather than a measurement. Three judges
sharing one model family are not independent in the way three people would
be; correlated error stays correlated. The panel narrows variance, not
bias.

**Why this is not a post-hoc change.** No candidate from the scored epoch
exists yet — four earlier epochs were retired without being judged, and
their candidates are excluded from the pick. This amendment is recorded
here, in git, ahead of the evidence, for the same reason the original was.


---

## Amendment 2 — measurement corrections found before scoring (2026-09-03)

Still ahead of the evidence: no arm has completed, no candidate has been
scored, and the keymap has never been opened. An adversarial audit of the
measurement code found defects that would have decided or distorted the
pick, and they are recorded here because two of them touch this protocol
rather than the tables.

**The blinding was compromised by the tooling, not the protocol.** The
documented order runs `analyse.py`, then the blind harvest, then scoring,
then the keymap. But `analyse.py` wrote `A-ranking-on.candidates.json` and
its siblings — full claim text, arm in the filename, cycle in every row —
into the working directory two steps BEFORE scoring. One grep of any
candidate's first sentence returned its arm. The keymap-stays-shut rule
protects nothing while the same mapping lies beside it. Those files are now
written only under `--reveal`, which belongs after the scores are committed.

**Two bugs in the panel would have decided the winner.** The median helper
returned `sorted[floor(n/2)]`, which is the median only for odd counts; the
judge array is filtered for failures, so two survivors were explicitly
possible, and with two it returned the HIGHER total — the exact inverse of
the rule pre-registered above, that one judge scoring an outlier cannot
carry a candidate. And the runoff decoded the winning label by taking the
first capital letter of free-form model text, so a schema-valid reply of
"Candidate B" resolved to C and the report would have named the THIRD
finalist's arm and cycle as the source of the best answer, silently. The
label is now constrained to a bare letter and decoded by exact match, with
an undecodable answer surfaced rather than swallowed.

**What the winner can now be said to be.** The keymap previously carried the
provider attempt's `outcome`, which is constant across every harvested row
and therefore could not distinguish an admitted answer from a discarded one
— the very thing the operator asked to be told. Each candidate now carries
its semantic-admission outcome, so "including discarded answers" can be
answered from the record instead of asserted.

None of the criteria changed.
