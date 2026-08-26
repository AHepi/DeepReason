# W4 — parked findings

This tranche fixes nothing, anywhere. Each finding below is a
ready-to-send prompt for one of the two fixing families, per the RUN
ANATOMY PROGRAM's Round 3 discipline. Nothing here has been implemented,
and no `src/` or `tests/` byte was touched.

---

## W4-P1 — compile silently discards `ENGAGED_CRITICISM_AUTHORITY`

**Route.** `dr-change-orchestrator` (it is a disclosure the compiler owes,
not a broken behaviour to diagnose).

**What.** A `Config` declaring `ENGAGED_CRITICISM_AUTHORITY: defended_trial`
reaches the run through exactly one carrier, the compiled manifest's
`criticism_policy`. `compile_run_manifest`'s `criticism_policy` parameter
defaults to `None`, the knob is dropped from `engine_config_json` on
purpose (docs/ERRATA.md E44), and no compile notice is emitted when the two
disagree. So a configuration asking for a defended trial compiles into a
manifest that mentions it nowhere and says nothing about having dropped it.
Measured: `disclosure_probe.py` in this tranche, mutation-proven.

**Why it matters.** Four tranches asked for `defended_trial` in their
`run-config.yaml`. GEX (2026-08-12) carried it into the manifest and ran
161 defended trials. Epoch3, rung7, P-C1 and P-R1 did not, and ran zero —
P-R1 after compiling, qualifying and paying for a two-family judge
ensemble. The operator's caution about judges has been untestable for
three months partly because of this.

**Why it is a defect and not a preference.** The 2026-08-12
all-configurations law: "what used to be a compile-time refusal... becomes
a typed disclosure recorded alongside the compiled result... never a stop."
Here there is neither the refusal nor the disclosure.

**Ready-to-send prompt:**

> Route through `dr-change-orchestrator`. The operator's request, to be
> captured verbatim in REQUEST.md, is this paragraph:
>
> *"When a run configuration asks for `ENGAGED_CRITICISM_AUTHORITY:
> defended_trial` and the compiled manifest ends up with no
> `criticism_policy`, compile must say so in a typed notice on the
> manifest. It must not refuse — all configurations are allowed — and it
> must not change any qualification subject digest. I want the run's own
> record to state that the authority I asked for was not carried."*
>
> Map preflight before designing: `DR-SEAM-adjudication-x-authority` (which
> owns the rule that authority may be consulted where a warrant is MINTED
> and never where a label is COMPUTED — a notice is neither, but check the
> mint/label boundary before choosing where the notice lands),
> `DR-SUB-manifest`, `DR-CON-authority`, and `DR-INV-frozen-surfaces`.
>
> The hard constraint is docs/ERRATA.md E44 and the frozen-surfaces law:
> the knob must stay OUT of `engine_config_json` and out of
> `source_config_hash`, because putting it back moves every qualification
> subject digest (measured 2026-08-22: 40 red goldens, 22 of them frozen
> manifest goldens). `compile_notices` is a schema-v6 manifest field that
> is already excluded from those digests — verify that before designing on
> it, do not assume it.
>
> Acceptance: a test that compiles a Config with
> `ENGAGED_CRITICISM_AUTHORITY=defended_trial` and no `criticism_policy`
> argument and asserts a typed notice naming the dropped authority; a test
> that the notice does NOT appear when the policy is carried; and a
> before/after qualification subject digest over a committed fixture
> proving it is byte-identical. Full gate green.
>
> The reproduction already exists and should be reused rather than
> rewritten:
> `experiments/2026-08-26-run-anatomy-program/W4-judge-road/disclosure_probe.py`.

---

## W4-P2 — the poietics P5 finding is factually wrong and is still on main

**Route.** `dr-change-orchestrator` (a correction to a committed document,
which is `docs/ERRATA.md`'s business, not a code change).

**What.** `experiments/2026-08-25-poietics-program/PARKED.md` P5, under
"STRENGTHENED 2026-08-25", states: *"No defended trial has ever run in this
repository."* Re-derived over all 54 committed roots in
`trial_sweep.json`: `experiments/2026-08-12-live-grounded-extension-
expansion/run` ran 161 defended trials, spent 342 judge calls across
qwen3.5:397b and mistral-large-3:675b, and 8 trials sustained — minting 8
`w:argtrial:` ARGUMENTATIVE warrants that carried into 8 attack edges and
refuted 8 artifacts, half that run's 16 refutations. The root's own
RESULTS.md said so when it was written.

**Why it matters beyond the correction.** P5's own closing sentence — "the
operator's standing caution about judges... has never been testable here,
because they have never prosecuted anything" — is the reason a fix tranche
would be scoped one way rather than another. It is false: there is live
judge evidence, one root's worth, and the guards in it turned away 114 of
122 convened trials.

**Ready-to-send prompt:**

> Route through `dr-change-orchestrator`. Append an entry to
> `docs/ERRATA.md` correcting
> `experiments/2026-08-25-poietics-program/PARKED.md` P5's strengthened
> claim, and rewrite P5's own paragraph in place per `SCHEMA.md`'s
> correct-in-place rule (a `Traps`-style entry is never deleted, only
> rewritten to say when it was found wrong).
>
> The correction, with its evidence:
> `experiments/2026-08-26-run-anatomy-program/W4-judge-road/trial_sweep.py`
> and `road_census.py` re-derive
> `application/results.py::_adjudication`'s counters over all 54 roots
> without the "reports the field" filter that produced the wrong census.
> State the corrected fact rather than only the negation: **whether a
> criticism can become a trial is decided at COMPILE time by
> `criticism_policy.authority`, and every root that compiled
> `defended_trial` and reached a criticism cycle ran trials.**
>
> Also record WHY the original census missed it, because the way it went
> wrong recurs: it counted only roots whose summary "reports the field",
> which silently excluded the one root that had the field set.

---

## W4-P3 — `poietics-installation-mechanism@v1` misses the question's own
## spelling of the distribution

**Route.** none yet — this is a finding about a COMMITTED ROOT's problem
criteria, and committed roots are never edited. It is parked as a lesson
for the next tranche that authors machine-evaluable criteria, not as a fix.

**What.** The criterion demands one of nine spellings of the distribution.
The operator's question, verbatim in `run-config.yaml`, writes it as "the
3-of-26 result" and "compile.py 1/9 mutations lost". The hyphenated
spellings are not on the list. Over all 527 P-R1 artifacts with inline
content, 18 name the distribution in the question's own spelling and match
nothing on the list; 6 of the 8 verdicts this criterion issued in the whole
run landed on one of them. Every verdict is CORRECT as specified
(`ADJUDICATION_SAMPLE.md`, 60 of 60). The criterion is the bad part.

**The lesson, stated so a later tranche can act on it:** a term-list
criterion should be generated from, or at minimum diffed against, the
question's own text before the run launches. The poietics tranche already
had the instrument for this — `preflight_criteria.py`, its discrimination
control — and that control tests whether the ATTACHED RECORD satisfies a
criterion by itself. It does not test whether the QUESTION's own phrasing
clears it, which is the miss here.

**Ready-to-send prompt:** none. Do not fix a committed root. If a later
tranche authors criteria for a live run, add a preflight assertion that
every term list matches the question's own spellings, and cite this
finding.

---

## W4-P4 — judge FORM FILLING (D6) is unmeasured and now measurable

**Route.** RUN ANATOMY PROGRAM, a later window — not a fix family.

**What.** This tranche establishes that GEX carries 342 judge rulings with
their `verdict` and `decisive_point` fields in its blobs, plus 62 recorded
ensemble splits, 12 referential-integrity failures and 3 paraphrase flips.
D6 ("how were they filling out forms") has a real corpus for the first
time, and this tranche did not read it: it counted what judges DID, not
what they WROTE. The 62 splits in particular are recorded by `_judge_all`'s
docstring as a "critic-gaming signal", and nothing distinguishes a critic
gaming the ensemble from two families honestly disagreeing.

**Ready-to-send prompt:**

> Route through `deepreason-orchestrator`, measurement variant, as a RUN
> ANATOMY PROGRAM window. Read `PROGRAM.md` and the W4 RESULTS first; do
> not re-measure the funnel. Goal: D6, judge form filling, on
> `experiments/2026-08-12-live-grounded-extension-expansion/run` — the only
> root that ever ran a defended trial.
>
> Census, from the blobs and the log only: for each of the 342 judge calls,
> the seat, the model, the `verdict` chosen, and whether the
> `decisive_point` resolves into the exchange it was given. Then the
> ensemble question: on the 62 `ensemble-split` declines, WHICH seat said
> what, whether splits cluster by model family, by cycle, by target, or by
> critic, and whether the 3 `paraphrase-flip` cases flipped on a
> paraphrase that a reader would call meaning-preserving (quote them).
>
> Read-only on `src/` and `tests/`. Write only under your own window
> directory. Model prose is the OBJECT of measurement here, never evidence
> for a count.
