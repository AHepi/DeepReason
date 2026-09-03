# Pre-registration — M1, M2, M3

Written 2026-09-03, BEFORE any arm has been launched and before any API key
for this tranche exists in the container. Nothing below may be edited after a
launch except by a dated, numbered amendment that says what it changes and why,
on the pattern the copied judging protocol already uses.

Authority: the window instruction's M1/M2/M3 block, ledgered verbatim in
`REQUEST.md`. Constraints C10 (comparability), C11 (per-problem unit), C12
(budget, credentials, honest residue).

Judging protocol: `JUDGING_PREREG_COPIED.md` — the 2026-09-02 protocol copied
verbatim from branch `claude/model-profile-registry-opkgal` per C10, criteria
and aggregation adopted unchanged.

---

## 0. What is fixed for every arm

| | |
|---|---|
| Model, every seat | `qwen3.5:397b`, `reasoning: none`, per its committed profile (C10) |
| Seed question | `experiments/2026-09-02-full-harness-diversity/QUESTION.txt`, sha256 `626e8f78…` (C10) |
| Qualification | cached `full` tier; the profile is NOT varied between arms, so no arm pays a requalification the others do not |
| Diversity unit | ONE problem — the seed problem's candidates only (C11) |
| Instrument | `measure_diversity_per_problem.py` (committed before launch) |
| Quality | blind three-judge median, `JUDGING_PREREG_COPIED.md`, keymap shut until scores are committed |
| Budget | ~3 M tokens across all three measurements (C12) |
| Credentials | one API key, gitignored, never committed (C12). The ignore gap at `experiments/<tranche>/<arm>/env` was closed in this tranche's first commit and verified |

**Episodes are OFF in every arm of M1, M2 and M3.** The operator's R10/R11
episode config lives on a branch this tranche may not merge (C9), and the
monitor's reading point 5 holds that history and episodes are orthogonal.
Turning both at once would confound them. Whether history helps is therefore
measured on the SHIPPED engine, and the episode interaction is explicitly NOT
measured here — recorded as residue, not as a result.

**No production code is written for any arm.** Both history arms (M1 H1, M3 C1)
render their section OFFLINE from the committed record with a script under this
tranche directory and inject it through the existing scratch channel or a
pre-built pack file, exactly as the window instruction specifies. That is a
deliberate weakening of external validity and it is stated as one in §5.

---

## 1. M1 — history ON/OFF for conjecturers (answers R6)

**Arms.** H0 = the shipped conjecturer pack, unaltered. H1 = the same pack plus
a rendered HISTORY section. 4 cycles each, same seeds, same everything else.

**What goes in the H1 section, fixed now.** Refuted lineages and failed attacks
on the problem's artifacts, capped. Specifically, and in this order:

1. every artifact on the seed problem whose status is REFUTED, with the claim
   and the warrant that refuted it;
2. every attack edge that did NOT change a status (a failed attack);
3. nothing else — no winning lineage, no accepted claim the seat would
   otherwise not see.

That composition is the monitor's reading point 4 ("refuted lineages and failed
attacks are anti-attractor information; the winning lineage is shown only on
request") turned into a fixed render, so that M1 tests it rather than assumes
it. The cap is 4,000 characters, chosen against the measured non-schema
remainder rather than picked: `conjecturer.turn.v6` prompts on committed roots
run 19,976–26,867 chars of which 60.0–81.4% is the JSON schema
(`SCHEMA_SHARE.txt`), leaving roughly 5,000–11,000 chars of everything else. A
4,000-char section is therefore a large but not dominating share of the part a
pack budget actually controls.

**Measures.** Per-problem D5 and D4; near-duplicate rate (pairs below 0.20
Jaccard distance, fixed in the instrument before launch); hv where measurable;
blind-judged quality by the copied protocol; tokens per admitted artifact.

**PREDICTION, registered before launch.**

- **Primary, directional:** H1 lowers the near-duplicate rate relative to H0.
  This is the anti-attractor claim (R8) in its most falsifiable form: showing a
  seat what has already been refuted should reduce restatement of it.
- **Secondary, directional:** H1's per-problem D5 is HIGHER than H0's. Stated
  separately because D5 and the near-duplicate rate can move independently, and
  because a wide spread of off-topic claims scores well on D5 — the failure mode
  the source branch's RESULTS.md already documented.
- **Cost, directional:** H1 spends MORE tokens per admitted artifact than H0.
  The section is pure prompt overhead; anything else would be a surprise.
- **Quality, NO DIRECTION PREDICTED.** The operator's R6 says history "might
  help LLMs craft better conjectures", and the honest state of this question is
  that nobody knows. Registering a direction here would be inventing a prior.

**What would falsify the monitor's reading point 4.** If H1 raises the
near-duplicate rate — if showing refutations makes the seat orbit them — the
anti-attractor shaping rule is wrong as specified and SPEC.md may not adopt it
as designed. That is a C13 stop.

**Decision rule, fixed now.** With 4 cycles per arm and n=1 question, no
threshold below is a significance test and none is claimed to be. A difference
is reported as SUGGESTIVE if it exceeds 20% relative on the near-duplicate rate
and INCONCLUSIVE otherwise, and the word inconclusive is used in RESULTS.md
where it applies.

---

## 2. M2 — pack budget sweep (answers R9)

**Arms.** `PACK_TOKEN_BUDGET` at 2500 (shipped default,
`src/deepreason/config.py:732`), 6000 (the value `easy.py:219` already ships for
its preset), 12000, 24000. 2 cycles each. Seats identical across rungs.

**Measures.** Blind-judged quality; tokens per admitted artifact; and,
separately, the schema share of every prompt.

**The schema share is ALREADY MEASURED, offline, before launch**
(`SCHEMA_SHARE.txt`, 532 prompt blobs over three committed roots). It is
recorded here so the sweep is read correctly rather than over-read:

| contract | prompt chars | schema chars | share |
|---|---|---|---|
| `conjecturer.turn.v6` | 19,976–26,867 | 16,141–18,951 | **60.0–81.4%** |
| `conjecturer.atomic-candidate.v1` | 11,179 | 6,154 | 55.1% |
| `batch-critic.v2` | 3,055–5,726 | a flat 1,275 | 27.0–42.2% |
| `critic.atomic-target.v1` | 3,287–5,794 | a flat 1,253 | 21.7–38.2% |

P-A1's "~19k of 30k chars" is confirmed almost exactly on pc2-rematch (18,951
of 26,214).

**PREDICTION, registered before launch.**

- **Primary:** the quality curve is FLAT or NON-MONOTONIC across the four rungs
  — 24000 is not better than 6000. The reasoning is the table above: the budget
  governs only the non-schema remainder, so quadrupling it from 6000 moves a
  minority of an already schema-dominated prompt.
- **Cost:** tokens per admitted artifact rises monotonically with the budget.
- **A specific risk, registered as a prediction so it cannot be explained away
  afterwards:** at 24000 some calls will produce NO admitted artifact, because
  a larger pack crowds the completion cap. CLAUDE.md records this failure mode
  for reasoning models; `qwen3.5:397b` runs `reasoning: none`, so the
  prediction is weaker here than it would be on glm-5.2, and it is registered
  as possible rather than expected.

**What the schema finding already licenses for SPEC.md, regardless of how the
sweep comes out.** The per-seat asymmetry is a measurement, not an opinion: a
critic's schema is a flat ~1.3k against a conjecturer's ~16–19k, so a critic
pack has far more unspent room for a history section than a conjecturer pack
does. R6 and R7 point the other way. SPEC.md must state which wins and why.

**Explicitly NOT in scope (window instruction):** fixing the schema-every-call
cost. It is a finding for SPEC.md, not a change here.

---

## 3. M3 — critic blind vs informed (answers R7)

**Arms.** C0 = the shipped critic pack, unaltered — which is BLIND today:
`rules/crit.py` contains no context-policy, context-request or
retrieval-channel path at all (verified at base; the grep is empty), so a
critic cannot ask for anything and is shown the target whole with no history.
C1 = the same pack plus the target's rebuttal/discharge history, rendered
offline, capped at 4,000 characters on the same reasoning as M1.

**Measures.**

- blind-judged case sharpness, by the copied protocol's criteria;
- **rate of re-raised already-rebutted objections** — counted from the record,
  never judged: an objection is "already rebutted" when a prior criticism on the
  same target carries a recorded discharge, and "re-raised" when a later
  objection on that target matches it above the 0.80 Jaccard similarity the
  near-duplicate rate already uses. The threshold is the same one, fixed in the
  instrument before launch, so it cannot be tuned to the answer;
- **rate of cases the defender sustains** — from the recorded adjudication
  outcome, not from reading.

**PREDICTION, registered before launch.**

- **Primary, directional:** C1 lowers the re-raised-objection rate. This is
  nearly mechanical — a critic shown the rebuttal has less excuse to repeat the
  objection — and if it fails, the render or the injection is broken, not the
  hypothesis.
- **Secondary, and this is the real question:** C1's blind-judged sharpness is
  NOT higher than C0's, and may be lower. This registers the operator's own
  hypothesis (R7) as the prediction rather than the monitor's convenience:
  "criticism without fully understanding the reasoning behind a conjecture might
  help sharpen critiques."
- **Sustain rate, NO DIRECTION PREDICTED.**

**What decides the SPEC's default, fixed now so it is not decided by whoever
reads the numbers.**

| M3 outcome | SPEC.md default for critics |
|---|---|
| C1 sharpness clearly lower | critic BLIND by default; history available but off |
| C1 sharpness clearly higher AND re-raise rate lower | critic INFORMED by default |
| anything else, including a split | critic BLIND by default — and this goes to the operator as a stop, per C13, rather than being settled here |

Blind is the standing default in the last row for a stated reason rather than
by coin-toss: it is the shipped behaviour, it is what R7 conjectures is better,
and the monitor's reading point 3 requires it stay available as the default
regardless. Choosing it on an inconclusive result changes nothing about the
system and preserves the operator's own hypothesis until evidence moves it.

---

## 4. What every RESULTS.md must carry (C12)

One RESULTS.md per measurement, each stating: the arms as run; the numbers with
the instrument that produced each; whether the registered prediction held,
failed, or was inconclusive, in those words; and the residue — what remains
unproven. An inconclusive result is recorded as inconclusive. "Accepted does
not mean true."

---

## 5. Residue registered IN ADVANCE

Stated now, before any number exists, so that no favourable result can be
reported without them.

1. **n = 1 question, one model, 4 cycles (M1/M3) or 2 (M2).** Both engines are
   stochastic. A second run of any arm could move every number.
2. **The history arms are OFFLINE PROTOTYPES.** H1 and C1 inject a section
   rendered by a script outside `src/`. They test whether the CONTENT helps.
   They do NOT test the mechanism SPEC.md will specify — a seat ASKING through
   the context-request path — because no such path exists for critics at all
   and none exists for provenance queries for anyone. A positive M1 licenses
   "history content helps"; it does not license "the query surface works".
3. **The judges share one model family.** The copied protocol says it: three
   judges from one family are not three people, and the panel narrows variance,
   not bias. The monitor also designed the arms.
4. **Episodes are off everywhere**, so nothing here speaks to R10/R11, and the
   interaction between history and the episode pool is unmeasured.
5. **Capability-channel use is stochastic across identical runs** (CLAUDE.md).
   One arm missing a path is inconclusive for that path.
6. **The 4,000-character cap is a judgement**, anchored to the measured
   non-schema remainder but not itself measured. A different cap could produce
   a different M1.
7. **The near-duplicate and re-raise thresholds (0.20 distance / 0.80
   similarity) are fixed before launch but arbitrary.** They are the same
   number used consistently, which makes arms comparable to each other; it does
   not make either an absolute measure of restatement.


---

## Amendment 1 — M2 DESCOPED, 2026-09-03, on operator instruction

Operator, verbatim, while eight arms were in flight:

> "You can only run 3 concurrently. And I may run out of tokens. SO ID prefer a
>  run complete than have a bunch incomplete"

**What changed.** Two binding constraints: a hard cap of 3 concurrent runs, and
a preference for COMPLETE measurements over a larger number of partial ones.
Eight arms at once satisfied neither.

**What was cut, and why M2 rather than M1 or M3.** The four M2 pack-budget
rungs were stopped and are NOT RUN. M2 was chosen on three grounds, stated so
the choice can be argued with:

1. **Its most valuable part is already measured, and measured offline.** The
   window instruction asks M2 to "record separately the share of each prompt
   that is the JSON schema". That is done, from 532 committed prompt blobs, with
   no API calls at all (`SCHEMA_SHARE.txt`, §2 above): 60.0-81.4% of a
   `conjecturer.turn.v6` prompt is schema, confirming P-A1 almost exactly. That
   finding is what §5 of SPEC.md actually leans on. The live sweep would have
   added a quality curve, not the structural fact.
2. **It was the most expensive of the three.** `PACK_TOKEN_BUDGET` moves the
   qualification subject digest, so each rung pays its own full battery — four
   batteries before a single reasoning cycle. M1 and M3 pay two each.
3. **It gates the least.** SPEC.md's pending items are S10 (defaults), S11
   (critic ask path) and S15 (anti-attractor rule); every one of them is blocked
   on M1 or M3, none on M2. M2's contribution to the spec, S13/S14, is already
   written from the offline measurement.

**State at the stop, recorded rather than rounded off.** No rung reached a run
root; all four died in qualification, at 268, 271, 270 and 262 cases of 360.
The tokens spent on those four partial batteries bought nothing and are a real
cost of the original eight-arm plan. Recorded as a cost, not written off.

**What M2's result is now.** PARTIAL, and it must be reported that way in
RESULTS.md: the schema-share sub-measurement is COMPLETE and stands; the
four-rung quality-and-cost sweep is NOT RUN and its registered predictions in
§2 above — a flat or non-monotonic quality curve, monotonically rising cost,
possible starvation at 24000 — are UNTESTED. They are left in this document
unchanged rather than deleted, so a later tranche can run the sweep against
predictions that were registered before anyone saw a number.

**Sequencing under the new cap.** M1 completes first: H0 then H1, so if the
budget runs out mid-way the tranche holds one whole measurement rather than two
halves. M3 follows: C0 (already in flight beside H0, giving 2 concurrent) then
C1. Concurrency never exceeds 2 under this plan, against the cap of 3.

**One thing this amendment does not do.** It does not touch the criteria, the
arms, the measures, the thresholds or the predictions of M1 and M3. Those stay
exactly as registered before any arm launched.


---

## Amendment 2 — the H1/C1 history section is scoped to the WHOLE RUN, 2026-09-03

Written after the M1 CONTROL completed and BEFORE any treatment arm produced a
single conjecture, so no result influenced it. Forced by a measured property of
the control's record, not by a preference.

**What §1 said.** "every artifact on the SEED PROBLEM whose status is REFUTED"
and "every attack edge that did NOT change a status".

**Why that cannot stand.** Measured on the completed M1-H0 control
(`run-fe00609058e10605590206d51ab2b7a0`): the run holds **6 REFUTED artifacts
and 6 attack edges, all present in `state.addr`, and ZERO of either inside the
seed problem's scope**. Criticism in that run landed on the problems the
investigation spawned (`disc:question-…`, `conn:…`), not on the seed problem's
own artifacts. The seed-scoped render therefore produced a section reading
"(nothing refuted yet)" and "(no failed attacks yet)" — 668 characters of
headings — on a run that had refuted six things.

An empty section makes H1 the control wearing a treatment label. M1 would then
have returned "history makes no difference", which would have looked like a
finding and been an artifact of the render.

**What changes.** The rendered history covers the whole run — every problem it
has opened. Nothing else about M1 or M3 changes.

**This is NOT a loosening of C11**, and the distinction matters. C11 fixes the
unit of the DIVERSITY MEASUREMENT — seed-question candidates only — and that is
untouched: `measure_diversity_per_problem.py` still reports the seed problem
alone, and the H0 control's numbers above were computed that way. This
amendment is about a different thing: what history a seat is SHOWN. The
operator's R6 is "conjectures themselves usually have a long history", and a
conjecture's history plainly includes the criticism that landed on the problems
its own investigation opened.

**Verified before relaunch, not after.** The widened render on the same control
root produces 6 refuted claims each with the criticism that refuted it. A guard
in `arm.sh` now REFUSES a treatment arm whose rendered history has no content
(exit 6), so this specific failure can never again be paid for with a full
battery and four cycles.

---

## Amendment 3 — where the history is injected, 2026-09-03

Also written before any treatment arm produced a conjecture.

`deepreason scratch add` writes into a RUN ROOT, not into a home. Called
against a home with no run yet it fails `MANIFEST_FILE_UNAVAILABLE at
/run-manifest.json`. The pre-seed design in §0 ("inject it through the existing
scratch channel … before the run") is therefore impossible as written: the
first H1 attempt's injection returned rc=1 and the run proceeded anyway, giving
a treatment arm with nothing injected.

`deepreason --root <root> scratch add` DOES work (verified rc=0). So the arm now
launches the run in the background, waits for its root to appear, and injects
into it. **Consequence, stated rather than hidden: the block lands during cycle
0 and is available to the cycles after it.** Cycle 0 of a treatment arm is
therefore comparable to cycle 0 of its control, and only cycles 1-3 carry the
treatment. That is the same exposure profile the original cycle-by-cycle design
would have produced, and it is the residue to state in RESULTS.md: M1 and M3
measure the effect of history on three of four cycles, not four of four.
