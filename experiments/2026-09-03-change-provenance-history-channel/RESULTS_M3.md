# M3 — does a critic that sees the rebuttal history sharpen or dull?

Answers R7 ("criticism without fully understanding the reasoning behind a
conjecture might help sharpen critiques").

**VERDICT: INCONCLUSIVE on every pre-registered measure.** Not "no effect" —
inconclusive, and for a structural reason that was identified and recorded
BEFORE the arms finished (PARKED P7).

---

## The arms as actually run

| | CONTROL (C0P) — blind | TREATMENT (C1I) — informed |
|---|---|---|
| attachment | criticism history of an UNRELATED run, 2,575 bytes | this problem's own rebuttal/discharge history, 2,596 bytes |
| root | `run-5565bd1ef7011e3d25fef3197bdf1cdb` | `run-7a8fc89b33f8e055a212fafa09acd83f` |
| terminal | completed, `budget_exhausted`, rc=0 | completed, `budget_exhausted`, rc=0 |
| cycles | 4 | 4 |
| tokens | 381,548 | 375,172 |

Same question, model, config and home as M1; one shared qualification; run ids
separated by dossier digest.

## The registered measures, and why neither could answer

| measure | CONTROL | TREATMENT | verdict |
|---|---|---|---|
| sustain rate | **1.000** (3/3) | **1.000** (1/1) | SATURATED — cannot discriminate |
| re-raise rate | **n/a** (0 comparable pairs) | **n/a** (0 comparable pairs) | UNDEFINED — no target survived an objection |
| blind-judged sharpness | — | — | **NOT RUN** |

**This was predicted, not discovered afterwards.** PARKED P7 was written from
six OTHER roots while M3's control was still running, and it stated that both
measures must fail: an attack edge is minted only by a WARRANTED attack, so
criticism that warrants nothing leaves no trace in `att` at all. Sustain rate
was 1.000 on 6 of 6 prior roots and 630+ targets; the re-raise rate is defined
only over targets that survived an objection, of which there are none. Both M3
arms then behaved exactly as predicted on roots that did not exist when the
prediction was made. That is the one genuinely confirmed thing in this
measurement, and what it confirms is a limitation of the instrument, not a fact
about critics.

## The one difference visible, and why it is not a result

The control attacked **3** targets; the treatment attacked **1**.

This is NOT reported as a finding. It was not pre-registered; n = 3 against
n = 1 cannot separate any hypothesis from chance; and the direction is
consistent with several incompatible stories (an informed critic attacks less
because it sees objections already made, or because it is distracted, or
because this run simply criticised less). Recorded because suppressing it would
be worse, and labelled exploratory so no later reader promotes it.

Conjecture-side figures, for completeness — M3 varies the CRITIC's input, so
these are not what M3 is about and no claim is made from them:

| | CONTROL | TREATMENT |
|---|---|---|
| conjectures | 43 | 39 |
| D4 | 0.876 | 0.865 |
| D5 | 0.192 | 0.171 |

## What decides the SPEC's default

`PREREG.md` §3 fixed this before any arm ran, precisely so an inconclusive
result could not be resolved by whoever read the numbers:

> anything else, including a split → critic BLIND by default — and this goes to
> the operator as a stop, per C13

So **SPEC.md S10 sets the critic default to BLIND**, and C13's stop condition
("the default exposure for critics if M3 is inconclusive") is triggered and is
put to the operator.

Blind is not a coin-toss fallback. It is the shipped behaviour today
(`rules/crit.py` has no context-request path at all), it is what R7 conjectures
is better, and the monitor's reading point 3 requires it stay available as a
default regardless of outcome. Choosing it on an inconclusive result changes
nothing about the system and preserves the operator's own hypothesis until
evidence moves it.

## What would actually answer R7

Three things, in order of how much they would buy:

1. **Run the blind-judging protocol.** It is committed, unchanged, and
   unrun. It is the only registered measure that could have discriminated, and
   it does not depend on `att` at all — it scores the criticism text.
2. **Fix the instrument P7 identified.** A "failed objection" has to be read
   from criticism records that warranted nothing, not from `att`. Until that
   exists, no record-derived measure of criticism quality can see the half of
   the phenomenon that matters.
3. **A question that provokes more criticism.** Four cycles produced 3 and 1
   attacked targets. Any measure over so few events is underpowered whatever
   its definition.

## Honest residue

- **n = 1 question, ONE run per arm.** No significance test is possible.
- **The channel is evidence, not the scratchpad** — as in M1, so this speaks to
  history CONTENT, not to the channel SPEC.md designs.
- **The critic arms' history had its failed-attacks limb empty** for the P7
  reason, so the "informed" critic was informed only about objections that
  LANDED. A critic told only about successful objections is not the critic R7
  imagines, which is one told what has already been answered.
- **Nothing here measures sharpness.** The word appears in the prediction and
  in no measurement that ran.
