# PREREG — STEP 1 LIVE: hold the form, vary the brief, judge against the
# no-harness baseline with length held constant

Tranche: `experiments/2026-09-04-experiment-brief-variation-step1/`.
Written: 2026-09-04, **BEFORE ANY PROVIDER CALL ON ANY ARM**. The commit that
carries this file is the evidence for that sentence; `SEALED.txt` in the same
commit carries its digest.

Authority: `REQUEST.md` R1-R34 (the operator's verbatim words).
Parent instrument: `experiments/2026-09-03-change-conjecturer-pluggable-
interface/PREREG.md`, whose §8 says **NOT RUN**. This document is the run,
with the operator's three amendments folded in.

Everything the parent registered stands unless a section below supersedes it,
and each supersession says so in its own first line.

---

## §1 What success is (unchanged from the parent; restated because it decides)

CLAUDE.md, 2026-09-03, the operator's words: *"a complete answer isn't the
goal. Neither is correctness. The condition of success it something materially
better than what's produced without it."*

So the question this experiment answers is not "did an arm finish" and not
"was the answer right". It is: **did any harness arm produce conjectures a
blind panel scored higher than what the same model writes in one call on the
same question — after the panel's known appetite for length is taken out?**

## §2 The arms

Form fixed at `conjecturer.turn.v6` in every arm (R10). One brief parameter
varies per arm; the rig that varies it is `rig/armrig.py` and it changes
nothing under `src/`.

| arm | what varies | selected by |
|---|---|---|
| `A0` | nothing — the shipped default | rig inert |
| `A1` | `dr.history.v1`: `include_refuted=true`, `refuted_n=3` | registered layout `seat-pack.conjecturer.step1-a1` |
| `A1P` | `dr.history.v1` removed from the layout entirely | `…step1-a1p` |
| `A2` | `dr.active-properties`: `claim_chars` 200 → 800 | `…step1-a2` |
| `A3` | `dr.neighbourhood` replaced by an operator `.tmpl` | `…step1-a3` + the template |
| `B0` | NO HARNESS: one call, same question, same model, same settings | `baseline_b0.py` |

## §3 MEASURED BEFORE ANY CALL: three of the six arms cannot differ, and that
## is the experiment's biggest single finding so far

`prove_arms.py` renders each arm's conjecturer brief over the committed golden
fixture inputs (`tests/conj_pack_golden_cases.py` — the input shape the gate
already pins) and diffs it against A0's. Output, committed in
`PROVE_ARMS.txt` before this file was sealed:

    A0 control: 5511 bytes
    A1     5886 bytes  differs, 4 lines
    A1P    5511 bytes  IDENTICAL TO A0
    A2     5511 bytes  IDENTICAL TO A0
    A3     5323 bytes  differs, 9 lines

### §3.1 Why `A1P` is identical to `A0`, and why the operator's amendment 3
### rests on a false premise

Amendment 3 says: *"A0 (history ON, the shipped default) vs A1' (history
plugin OFF entirely)"*. **The shipped default does not show history.**

`src/deepreason/llm/layout.py` sets `superseded_summary_n = 0` in BOTH
registered arrangements (`ROBUST_LAYOUT_POLICY` line 122,
`LEGACY_LAYOUT_POLICY` line 128). `_History.render`
(`llm/seat_plugins.py:380`) reads exactly that number and returns `None` when
it is zero, unless `include_refuted` raises it. So at the shipped default the
history section renders nothing, and deleting the plugin cannot change a byte.
The committed golden suite says the same thing in its own words: it had to
register a THIRD arrangement (`render-layout.golden-superseded`,
`superseded_summary_n=3`) or "the golden would never see
`superseded-conjectures` render at all".

And the "ON default" the amendment points at was never built. The history
tranche's `CHECKLIST.md` line 3 reads **"State: NOT STARTED"**, and that
directory has no `VALIDATION.md` and no `DELIVERY.md`. `SPEC.md` S10's
"conjecturer: history ON by default" is a specified decision awaiting operator
approval, not shipped behaviour. Its own M1 arms delivered history through
`reason --attach`, not through this plugin at all.

**So the contrast that carries amendment 3's meaning is `A1` (history really
rendered) against `A0`/`A1P` (history absent), and that is what §7's decision
rule uses.** Nothing is dropped: A1P still runs.

### §3.2 Why `A2` cannot differ on this question

`dr.active-properties` renders the docstring claims of ACCEPTED
`code:python-prop` artifacts (`packs.py::_active_property_claims`). The seed
question produced **zero** of them: across the 139 committed artifacts of the
M1 control root, the codec census is `{utf8: 133, json: 6}`. A section that
never renders cannot be widened, so `claim_chars` 200 → 800 changes nothing.

**Registered as falsifiable, not as certain:** if any arm's record carries an
accepted `code:python-prop` artifact whose docstring claim exceeds 200
characters, A2 becomes a real treatment and RESULTS.md must report it as one.

### §3.3 What this converts the design into — and why it is a better
### experiment than the one commissioned

A0, A1P and A2 are **three independent runs of the same brief**. That is not
waste; it is the measurement the parent tranche said it was missing.
`RESULTS_M1_QUALITY.md` §6 residue 6: *"Two more runs per arm on the same
question, judged by the same sealed protocol, would separate W from R."* Three
identical-brief arms give exactly that — a measured NOISE FLOOR for this
design, on this question, under this panel.

Registered consequence, before any number exists: **no arm gap is called real
unless it exceeds the largest gap among A0, A1P and A2**, which is defined in
§7 and computed by the same instrument on the same scale.

### §3.4 What A3 actually varies, stated before the numbers

A3 is a FORMAT change **with content loss**, not the same content in a
different shape. The template language sees `SectionRequestV1.supplied` only,
and the conjecturer's `supplied["accepted"]` is a tuple of artifact IDS; the
distilled claim text `dr.neighbourhood` prints beside each id is computed
inside that plugin from state and blobs, which no template can reach. The
measured diff shows it exactly: two ids with their claims become four ids
without them — and the four include the two that the separate
`live-neighbourhood` section already renders whole, so A3 also duplicates
those two ids.

The parent PREREG called A3 *"the one that answers R9 directly: same
information, different shape"*. **On this section, the shipped template
channel cannot do that.** A3 as run therefore answers a narrower question:
what does a conjecturer do when its neighbourhood arrives as bare identifiers
instead of distilled claims? The gap is `PARKED.md` F3.

## §4 AMENDMENT 1 (operator) — blind-judged quality against B0 is the PRIMARY
## measure

Supersedes the parent PREREG §6, which listed diversity and admission measures
only and so omitted the law's own criterion.

- The instrument is the committed three-judge protocol:
  `experiments/2026-09-03-change-provenance-history-channel/
  JUDGING_PREREG_COPIED.md` and its `judge.py`. Criteria, 0-3 scoring,
  tie-breaks (criterion 4 then 1), three-judge MEDIAN, contested flag at >4 of
  15 spread, and the keymap-stays-shut rule are ADOPTED UNCHANGED. Only the
  arm labels differ, exactly as that protocol's own copy header anticipates.
- The question is the same seed question, so criteria 2-5 — written about that
  question's specific machinery — transfer verbatim.
- **Blinding is STRUCTURAL.** `blind/candidates.jsonl` carries `{bid, text}`
  and nothing else; `bid` is a uuid4; rows are emitted sorted by `bid` so file
  position carries no origin signal. `layout_id`, `form_id`, `shell_id`, `arm`
  and `plugin_id` are provenance and are OMITTED ENTIRELY, never blanked
  (`docs/RESEARCH_JUDGE_BLINDING_2026-08-22.md`: a present-but-blank slot
  draws more attention than a filled one).
- `blind/keymap.json` is not opened until `blind/scores.json` exists and its
  digest is committed in `blind/SCORES_SEALED.txt`.
- **B0's candidates enter the same pool, blinded the same way.** A judge
  cannot tell a harness conjecture from a one-call answer, which is the whole
  point of the law's "measured blind".

### §4.1 The one place B0 is not comparable, named now

A harness conjecture is one `claim` field. A single model call answers the
whole question in one piece. Scoring them on the same 0-15 criteria means a
B0 answer is judged as one candidate, and a harness arm contributes dozens.
This is registered rather than corrected, and it cuts BOTH ways:

- it favours the harness on the MAXIMUM (dozens of draws beat one draw), so
  the pre-registered comparison against B0 is on the arm's **mean** and its
  **best**, reported side by side, with the mean as the verdict figure;
- it favours B0 on completeness (criteria 1, 3 and 4 ask for both cases, a
  verdict and a cost, and a single answer is written to carry all three while
  one conjecture need not be).

**B0 therefore runs `n = 12` independent calls, not one**, so its own scatter
is measured rather than assumed, and its mean has an interval. Twelve is the
number that keeps B0's spend inside the same order as one harness arm's.

## §5 AMENDMENT 2 (operator) — length is controlled STRUCTURALLY

Supersedes nothing; adds. `RESULTS_M1_QUALITY.md` §3.4 measured Spearman
ρ = +0.797 between candidate characters and judged total, R² = 0.589 on
log-length alone. A panel that pays that much for length can manufacture an
arm gap out of verbosity.

Registered, before any call:

1. Character count is recorded for every candidate in every arm, including
   B0's.
2. Every arm comparison is reported THREE ways: **raw** mean gap; **length-
   adjusted**, the arm term of `total ~ 1 + log(chars) + arm` with its
   permutation p; and **quintile-held**, the length-stratified gap.
3. **A verdict is stated only on the length-held-constant figure** (R15). The
   raw gap is reported and is never the verdict.
4. The instrument is the committed `analyse_length_bias.py` — IMPORTED and
   called (`ols`, `spearman`, `r2`, `arm_term`, `perm_p`, `stratified`), never
   reimplemented. Its arm pairs are hard-coded to the M1/M3 labels, so this
   tranche drives its functions over this tranche's pairs; the estimators are
   its, byte for byte.
5. **No prompt-level de-biasing is attempted** (R16). No judge prompt says
   anything about length. The judge law's finding is that prompt-level fixes
   do not hold, so one would be a fix that could not be trusted and would
   contaminate the only committed judge protocol this tree has.

## §6 AMENDMENT 3 (operator) — A1P, and the history-default decision

The arm is added (§2). Its intended contrast is corrected on measurement in
§3.1, and the decision rule is §7.

## §7 THE DECISION RULE — named here, before any call (R18)

**What is being decided.** Whether a conjecturer should be shown the refuted
artifacts of its own problem by default. Today it is not: the shipped layout
carries `dr.history.v1` with `include_refuted=false`, which renders nothing
(§3.1). `SPEC.md` S10 of the history tranche specifies ON and is NOT STARTED.
This experiment supplies the quality evidence S10 recorded as blank, and
`RESULTS_M1_QUALITY.md` §5 already filled that blank with a mild negative from
a different channel (attached dossier, not this plugin).

**The quantities**, all on the 0-15 judged scale, all length-adjusted by §5's
committed instrument:

- `d_hist` = the arm term for A1 against the pooled identical-brief arms
  (A0 + A1P + A2), with its permutation p.
- `d_noise` = the LARGEST absolute length-adjusted arm term among the three
  pairwise comparisons of A0, A1P and A2 — arms whose briefs are byte-
  identical, so any gap between them is scatter by construction.

**The rule:**

| condition | recommendation to the operator |
|---|---|
| `d_hist > 0` and `d_hist > d_noise` | history ON by default |
| `d_hist < 0` and `\|d_hist\| > d_noise` | history OFF by default; S10's ON is not supported |
| otherwise | NO CHANGE — the evidence does not separate history from scatter |

**The recommendation is a recommendation.** R33: "Change no default
yourself." No config, spec or source file is edited by this tranche whatever
the numbers say.

## §8 Predictions, registered before any call

Each is falsifiable and each is scored in RESULTS.md whichever way it lands.

| # | prediction | why it is registered |
|---|---|---|
| P1 | **No direction predicted for A1 vs the null arms.** | The parent tranche registered no direction for history quality and nobody knows. Registering one now, after `RESULTS_M1_QUALITY.md` reported −1.558 raw, would be borrowing a prior from a different channel. |
| P2 | A3 scores LOWER than the null arms on the length-adjusted figure. | A3 removes content (§3.4). A brief carrying less about what already stands should not produce better conjectures. If it does, that is the finding. |
| P3 | A1P and A2 are each within `d_noise` of A0 — i.e. `d_noise` is small. | They are byte-identical briefs. A large `d_noise` would mean this design cannot detect any brief effect at all, which is itself the result. |
| P4 | **At least one harness arm's MEAN does NOT beat B0's mean** on the length-adjusted figure. | Registered as the failure the operator's law requires be written up as failure (R32). |
| P5 | B0's candidates are LONGER than any harness arm's per candidate. | One call answers the whole question; a conjecture is one claim. This makes the length control load-bearing rather than decorative. |

## §9 The measures, and the instruments that own them

| measure | instrument | status |
|---|---|---|
| **PRIMARY** — blind-judged quality, length-held-constant, each arm vs B0 | `judge.py` (copied) + `analyse_length_bias.py` (imported) | added by amendment 1+2 |
| admission rate per contract and per endpoint | `census_conjecturer_failures.py` (parent directory), re-run over the new roots | parent §6 |
| M1 distinct-idea count per cell | `experiments/2026-08-28-diversity-generation/analyse.py` | parent §6 |
| M2 mean pairwise embedding distance | same | parent §6 |
| M3 yield per cell | same | parent §6 |
| criticism outcomes | each root's own typed record | parent §6 |
| spend: tokens per arm and per admitted artifact, B0 as the floor | `deepreason results --json` per root | R30 |

**No measure is invented here.** `analyse_arms.py` CALLS the committed
instruments; a second implementation of a measure is a second answer to the
same question.

## §10 Two binding rules, carried unchanged from the parent

**No self-reported number enters any metric, rank, filter or ordering.** A
model's estimate of its own typicality, novelty or confidence is content, not
measurement (R29).

**Blinding is structural, never prompt-level** (§4).

## §11 What would falsify the premise this whole step rests on

R14 — "the input interface materially changes outputs". If A1 and A3 are
indistinguishable from the three identical-brief arms on every measure in §9,
the premise is not supported on this record, and RESULTS.md records a negative
result as a negative result. Given §3, the step already has the control it
needs to tell "the brief does not matter" from "the arms did not differ".

## §12 Status at seal

**NO PROVIDER CALL HAS BEEN MADE.** `PROVE_ARMS.txt` is offline rendering
only. The credential file is absent from this container and is requested at
launch (`REQUEST.md` §3).
