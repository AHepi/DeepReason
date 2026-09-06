# RESULTS — the mini isolation programme

Honest-ledger segments, dated. "Accepted does not mean true." Nothing here
claims more than the record shows; a negative or inconclusive result is
recorded as one.

## 2026-09-06 — D8, the measure (T7, SPEC S12, C6)

**Verdict under the pre-registered rule (PREREG_D8.md §4): INDISTINGUISHABLE
— and the rule could not do its job here.** The rule fired because its two
estimators point in opposite directions: on the panel's raw scale the three
single calls scored a perfect 15 of 15 each while the best of mini's eight
conjectures scored 10, yet the length-adjusted term comes out large and
POSITIVE for mini — the sign flips because the two arms barely overlap in
length (essays of ~7 600 characters against conjectures of ~550), so the
regression attributes the whole gap to length and the arm term is an
extrapolation, exactly the failure mode §4 named. What the record supports
without any adjustment: **in this configuration, on this rubric, mini's
isolation flow produced no text the blind panel rated as good an answer as
one plain call, at 7.6 times the spend.** Under the operator's success law
(C6, "materially better than what the same model produces without the
harness") that is a NULL result — improvement NOT shown — not a proof of
harm, because the pre-registered length control cannot separate merit from
length when the arms do not overlap in length, and because the judged unit
(one conjecture) is not the unit the rubric was written for. Both limits were
foreseeable, one was foreseen (§4's overlap clause), and they are the
measure's residue, not the harness's. A design for a measure that can
actually answer C6 for mini is parked as P11.

### 1. What was sealed, and when

| | |
|---|---|
| PREREG_D8.md | sha256 `fedc813eb1afc2759e55fd4ba50748b990ac2e3946a77aa7adf18858b4d2265c`, commit `f1b47d270`, 2026-09-06 before any call |
| standard input | `runs/input-d8`, problem `question-corroboration-d8`, criteria `[]`, `run_input_digest 63d2a653…`; question sha `626e8f78…` |
| soak | `cycle_soak --case epoch3` exit 0 (commit `6bd723025`); disclosed: no soak case drives mini |
| transport probe | one throwaway call through the reasoning-off override: `{"ok": true}`, 30 tokens (`d8/PROBE.txt`) |
| ARM 0 | 04:07:42Z–04:08:45Z, commit `c69129453` |
| ARM M | 04:08:46Z–04:10:33Z, root `runs/home-m/shallow-runs/shallow-b4dcb1c81ea7af2e5ecd5faa`, commit `4f91ec43f` |
| blind scores | `d8/blind/scores.json` sha256 `ea3bc38b253af5c949bb95caf2831354a783500fbc57dd75c925ed87784c9661`, 11 of 11 scored, 3 judges each, 0 failed, 0 contested; keymap opened only after |
| instruments | `d8/judge_d8.py`, `d8/analyse_d8.py` — committed with the pre-registration, unchanged since |

Every number below was produced by a committed instrument; the command is
named with it.

### 2. The arms' typed outputs

**ARM 0 — three single calls, no harness** (`d8/arm0/ARM0_RESULT.json`).
User message = the frozen question, reasoning off, cap 8192, no response
format.

| call | finish | chars | prompt / completion / total tokens | seconds |
|---|---|---|---|---|
| 1 | stop | 7262 | 105 / 1526 / 1631 | 19.5 |
| 2 | stop | 7688 | 105 / 1699 / 1804 | 21.7 |
| 3 | stop | 7985 | 105 / 1699 / 1804 | 22.3 |

Typed terminal (PREREG §1): COMPLETE, 3 of 3.

**ARM M — `mini.flow.isolation.v1`** (`d8/armM/ARMM_TERMINAL.json`), through
the managed shallow entry with the one disclosed override (P10).

    completed true   stop queue-exhausted   cycles 3   model profile compact (vs_k 4)
    conjectures admitted 8 (4 / 2 / 2 by cycle)   refuted 0
    records: mini.criticism.v1 24   mini.commitment-proposal.v1 14
    calls 19 (3 conjecture + 8 critic + 8 commitment)   tokens 39 577 of 400 000
    meter_equals_log true   verify_root 0 violations   replay digest == live
    TYPED_TERMINAL: COMPLETE (all five instruments of PREREG §2)

`deepreason results` on the root prints the typed absences PREREG §2
predicted (NO_RUN_STATUS_JSON, NO_STOP_RECORD, NO_REPLAY_VALIDATION_JSON …)
and, from what it can read: accepted 8 / refuted 0, provider health 19 calls,
0 faults. Pasted in full in `d8/armM.log`.

### 3. Blind judging (`judge_d8.py reveal`)

    BLIND_JUDGING_RESULT_V1  (median of 3 judges per candidate, 0-15)
      candidates scored : 11      contested (>4 spread of 15): 0
      ARM0-single-call   n=  3  mean=15.00  median=15.00  best=15.0  worst=15.0
      ARMM-isolation     n=  8  mean=5.62   median=5.00   best=10.0  worst=1.0

Per candidate (judge totals in brackets; ARM M by the cycle that wrote it):

| arm | cycle | median | judges | chars |
|---|---|---|---|---|
| ARM 0 | – | 15 | [15, 15, 15] | 7262 |
| ARM 0 | – | 15 | [15, 15, 15] | 7688 |
| ARM 0 | – | 15 | [15, 15, 15] | 7985 |
| ARM M | 1 | 7 | [7, 7, 9] | 561 |
| ARM M | 1 | 7 | [6, 7, 8] | 580 |
| ARM M | 1 | 5 | [5, 5, 5] | 628 |
| ARM M | 1 | 5 | [5, 5, 6] | 615 |
| ARM M | 2 | 5 | [5, 5, 6] | 458 |
| ARM M | 2 | 1 | [1, 1, 4] | 464 |
| ARM M | 3 | 10 | [10, 10, 10] | 551 |
| ARM M | 3 | 5 | [4, 5, 8] | 510 |

Per criterion, mean over the nine judge readings per arm: ARM 0 scores 3.0
on every criterion (the rubric is SATURATED — a ceiling, stated as residue in
§8); ARM M scores c1 0.71 (both cases made), c2 1.38 (Popperian machinery),
c3 1.92 (a verdict), c4 1.46 (a real cost), c5 0.54 (non-evasion). The
judges' own lines for the best ARM M candidate say what a 550-character
conjecture cannot do on this rubric: "The case for 'smuggling induction' is
entirely absent; only the defense is presented" — three judges, the same
point, on a text that is one side of an argument by construction.

Per cycle (mean of the per-candidate medians): cycle 1 → 6.0 (n 4), cycle 2 →
3.0 (n 2), cycle 3 → 7.5 (n 2). Cycle 3, whose conjecturer had seen
criticism and proposals of cycles 1–2, holds the best candidate (10) and the
cycle-2 seat wrote the worst (1). Two candidates per cycle is too few to call
that a trend; it is recorded, not claimed.

### 4. Length held constant (`analyse_d8.py`, PREREG §4)

    1. length per arm (characters)
       ARM0-single-call   n=  3 mean=  7645.0 median=  7688.0 min= 7262 max= 7985
       ARMM-isolation     n=  8 mean=   545.9 median=   556.0 min=  458 max=  628
       pooled quintile boundaries: [482, 559, 618, 7518]
    2. does the panel pay for length (pooled)
       Spearman rho(chars, total) = +0.716
       total ~ -16.94 +3.58*log(chars)   R^2 = 0.828
    3. raw gap (ARMM - ARM0, of 15)
       ARM0 mean 15.00  ARMM mean 5.62  gap -9.375  p=0.0061
       length gap: ARM0 7645 -> ARMM 546 chars  p=0.0061
    4. length-adjusted gap  (total ~ 1 + log(chars) + [arm=ARMM])
       arm coefficient +13.499 of 15  p=0.0063  (model R^2 0.840)
    5. quintile-held gap
       q1: ARM0 n=0 | ARMM n=2 3.00      q2: ARM0 n=0 | ARMM n=2 7.50
       q3: ARM0 n=0 | ARMM n=3 6.33      q4: ARM0 n=1 15.00 | ARMM n=1 5.00
       q5: ARM0 n=2 15.00 | ARMM n=0
       strata holding both arms: 1   gap: -10.000
    VERDICT (PREREG_D8 §4 rule): INDISTINGUISHABLE -- floor met and neither
    directional rule fired

Reading, in the order the rule was written. The floor was met by its letter:
8 usable ARM M candidates (the floor is 8), 3 ARM 0, and ONE pooled quintile
holding both arms — with one candidate from each. "M WORSE" needed the
adjusted coefficient ≤ 0; it is +13.5. That coefficient is not evidence for
mini: with length and arm almost perfectly confounded (Spearman +0.716 on
eleven points, the length gap itself p = 0.006), the model has one stratum
of overlap to identify the arm term from and the fit R² = 0.84 is the length
term doing all the work. §4 said in advance that with no overlap the adjusted
term "is an extrapolation and the stratified term does not exist"; with one
1-versus-1 stratum it exists and says −10, on two candidates. The rule is
recorded as it fired and is not re-litigated; what it fired on is stated so
nobody reads INDISTINGUISHABLE as "as good".

### 5. Per-seat spend (`analyse_d8.py`, PREREG §5) and the predictions

    D8_PER_SEAT_SPEND_V1  (ARM M, from the record's llm.tokens)
      seat                             calls    tokens   share
      commitment                           8     24280   61.3%
      critic                               8      8561   21.6%
      conjecturer                          3      6736   17.0%
      TOTAL                               19     39577
      cross-check: rows sum 39577 == logged_tokens_this_run 39577: True; meter_equals_log: True
      ARM0 (single call x3): calls 3  tokens 5239
      ARMM total / ARM0 total = 7.55x ; ARMM conjecturer / ARM0 total = 1.29x

The commitment seat is the expensive one: its brief carries the
everything-so-far section (5 823 characters at seq 16, 7 307 by seq 51) and
it answered at length. No dropped call, no stage-empty, no retry: every one
of the 19 calls landed on its first attempt (`attempts=1`, `truncated=False`
throughout).

| prediction (PREREG §4) | outcome |
|---|---|
| quality — no direction predicted | none claimed; §4's verdict and its reading above |
| length — ARM 0 longer | **HELD**: 7 645 vs 546 characters, p = 0.006 |
| cost — ARM M total > 3 × ARM 0 | **HELD**: 7.55× |
| cost — ARM M conjecturer within 2× of ARM 0 total | **HELD**: 1.29× |
| operational — `max-cycles` at cycle 3, refuted 0, verify clean, replay equal | held on every part but the stop's NAME: the loop reports `queue-exhausted` when the queue empties on the last cycle (the same name T6's offline run carried); a typed stop, listed in §2 |

### 6. What the record shows about the harness in this run

These are facts a reader of the root can re-derive; none is a verdict.

- **The conjecturer answered with fewer candidates as the run went on**: 4
  returned and admitted in cycle 1 (561–628 characters each), 2 in cycle 2
  (458, 464), 2 in cycle 3 (551, 510), against a directive asking for 4.
  Nothing was gated or deduplicated (`gate_blocks 0`, no `gate:` marker); the
  model simply returned two.
- **"Everything so far" was, under the compact budget, the newest four
  entries.** The everything-so-far section had 60 % of a 4 800-character
  prompt clip; its retention rule withheld the oldest entries and SAID SO in
  the brief: cycle 2's conjecturer read "WITHHELD UNDER RULE
  mini.retention.everything.v1: 22 earlier entries exist in this run and are
  not shown here", cycle 3's "33 earlier entries"; what remained was the
  last few commitment proposals. The typed notice worked exactly as T3
  designed it; what it discloses is that R6's "everything" needs a budget the
  compact profile does not give it. Not a defect; a configuration fact,
  carried into P11.
- **Ten briefs still overran the clip after retention and were cut by the
  call layer**, each written to the record as `mini:brief-clipped` with both
  sizes (commitment stage: 4 919 → 7 307 characters over the run; conjecture
  stage cycles 2–3: 5 028 and 6 030). The P8 disposal made the cut visible;
  it did not make it small.
- **Criticism and proposals were written and shown, and overturned nothing**
  (R13): 24 objections (mean 624 characters) and 14 proposals (mean 647),
  every one about a named conjecture; `refuted 0`. The critic's brief was 2
  380 characters — schema, problem, target, directive — and carried no
  proposal and no other conjecture (R5, structural). Sample, verbatim from the
  record (criticism #1, about `9843f16c…`): "…preferring the
  better-corroborated theory over a worse one for practical application is
  functionally identical to acting as if the future will resemble the past,
  which is the very principle of induction Popper sought to reject." The
  proposal about the same conjecture: "The conjecture must be refuted if it
  can be demonstrated that Popper's preference … logically entails an
  inductive assumption about the uniformity of nature…". Content of that
  kind is what mini exists to generate in this programme; what it is worth
  is for the full harness to decide (Amendment 1).
- **Every call carried role `conjecturer`** (P9): `deepreason results` counts
  "conjecturer: 19 calls"; the seat that spoke is on the record event, not
  the call.

### 7. Exploratory, NOT pre-registered (`d8/explore_composed.py`)

The obvious objection to §3 is that a 550-character conjecture was scored on
a rubric for a complete answer. One follow-up that needs no new arm: ARM M's
eight conjectures composed into one text, oldest first (4 493 characters),
scored by the same three judges under the same criteria.

    judges 3   totals [8, 8, 8]   median 8 of 15

The judges' lines: "Both sides are presented clearly…", "Identifies a
survivor in Conjecture 7 but dilutes the commitment by presenting eight
separate 'conjectures' rather than a single synthesized verdict", "Fails to
name specific Popperian texts…". So the composed run holds both cases and a
verdict that no single conjecture held, and it still trails the single
call by 7 points on a rubric the single call saturates. Descriptive only; it
decides nothing under §4 and is reported so the unit mismatch is measured
rather than argued.

### 8. Residue — what remains unproven, and what this does NOT mean

- **It does not mean mini's content is worse than a single call.** The
  pre-registered unit (one conjecture) cannot score c1, c3 and c4 of a rubric
  written for a whole answer; the panel said so in its own words for every
  ARM M candidate. The measure compared a part against a whole.
- **It does not mean the harness cannot beat a single call.** It means THIS
  configuration — compact profile, 4 800-character clip, three cycles, no
  criteria, criticism that overturns nothing (by the operator's ruling) — did
  not, on this rubric, with this unit.
- **Ceiling.** Nine judge readings of ARM 0, nine 15s. The copied rubric
  cannot rank the single call's essays against anything better; a
  comparison that needs headroom needs a harder rubric or a harder question.
- **The length control failed by construction**, not by execution: the arms
  did not overlap in length, so the adjusted term is unidentified and the
  quintile term rests on one pair. §4 foresaw the no-overlap case and set
  the floor at one stratum; one stratum of one-versus-one met the floor and
  is not a control.
- **Same-model judging**; self-preference and verbosity bias measured only
  as §4's pooled ρ = +0.716 on eleven points.
- **n = 3 vs 8.** Every p above is a permutation p on eleven points.
- **ARM M ran through the reasoning-field override** (P10); one request field,
  disclosed, in the committed driver.
- **The "better-criticised conjectures" question** (SPEC §Q-A's consequence
  for D8) has two candidates per cycle to answer it with. Cycle 3's best
  (10) is the run's best and came after criticism was shown; cycle 2's worst
  (1) came after criticism was shown too. Not called.

**Disposition under C6:** improvement over the no-harness baseline NOT
demonstrated for `mini.flow.isolation.v1` on the compact profile; the
pre-registered verdict is INDISTINGUISHABLE on a control that could not
discriminate; the raw panel scores favour the single call on every candidate.
No arm was re-run. The next measure is designed, not run, in P11.
