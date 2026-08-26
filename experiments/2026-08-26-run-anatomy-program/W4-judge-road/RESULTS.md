# W4 — the judge-road autopsy: why no defended trial ran, and whether the
# commitments that did rule ruled correctly

**Tranche.** `experiments/2026-08-26-run-anatomy-program/W4-judge-road/`,
RUN ANATOMY PROGRAM measurement tranche W4 (D5 judge activity, D6 judge form
filling, and the adjudication end of D8). Read-only on `src/` and `tests/`.
**Branch.** `claude/w4-judge-road-autopsy-754boo`. **Base.** `origin/main`
at `00e3f8afc`.
**Every number below is generated**, not typed: `FUNNEL.md`,
`ADJUDICATION_SAMPLE.md` and `EXEMPLARS.md` are emitted by `tables.py` and
`exemplars.py` from `trial_sweep.json`, `road_census.json`,
`verdict_sample.json`, `handcheck.json` and `criterion_proxy_probe.json`.
If a figure here is not in one of those, it is not this tranche's figure.

---

## 2026-08-26 — segment 1: the standing fact is false, and that is the
## first result

**Defended trials have run in this repository. 161 of them, in one root, on
2026-08-13 — and 8 of those trials sustained, minting argumentative
warrants that refuted 8 artifacts.** The poietics tranche's PARKED **P5**
says the opposite: *"A census of every committed root in `experiments/`
that reports the field returns judge calls 0, adjudication ran: no, in
every one... No defended trial has ever run in this repository."* The
qualifier is where it went wrong. `trial_sweep.py` re-derives
`application/results.py::_adjudication`'s own four counters straight from
`log.jsonl` for **all 54 roots** in W1's `ROOT_INVENTORY.json`, with no
"reports the field" filter, and finds
`experiments/2026-08-12-live-grounded-extension-expansion/run` (GEX):

    judge calls        342   (qwen3.5:397b 171, mistral-large-3:675b 171)
    defender calls     122
    variator calls      30
    trials entered     161   = 153 declined + 8 sustained
    argtrial warrants    8   -> 8 attack edges -> 8 REFUTED artifacts

Those 8 are **half of that run's 16 refutations** (304 artifacts, 287
accepted, 16 refuted, 1 suspended-unsupported, read from the root
`read_only=True`). And the tranche said so at the time. Its RESULTS.md
reports judge calls per PHASE rather than per root — "162 of the 485
calls were `judge` calls — the two-member cross-family ensemble
(qwen3.5:397b, mistral-large-3:675b) was heavily exercised, consistent
with `ENGAGED_CRITICISM_AUTHORITY=defended_trial` actually routing
criticism through real defended trials" for the initial run, and "By
role: judge 104" for the post-amendment epoch. Neither is this
tranche's 342, which is the whole committed log across every epoch, and
this census does not reconcile the three; what matters here is that the
evidence was written down, in the tree, and the P5 census walked past
it.

**The corrected fact is narrower and still worth having.** Across the 54
roots, the manifest field `criticism_policy.authority` reads
`observe_only` 41 times, absent 9 times, and `defended_trial` 4 times. All
four `defended_trial` roots are the same run id `8e22d0431fd2b98d`; the
three that are not GEX died at cycle 0 with zero criticism events. So:

> **Every root that ever compiled a defended-trial criticism policy and
> reached a criticism cycle ran defended trials. No root that did not,
> ever did.** Whether a criticism can become a trial is decided at COMPILE
> time, by one manifest field, and never by the criticism's merit.

## 2026-08-26 — segment 2: the road, and where P-R1's ended

`FUNNEL.md` walks both legs gate by gate. Leg 1 is upstream
(`rules/crit.py::_crit_argumentative_batch_result`), leg 2 is the trial
itself (`informal/trial.py::_argument_trial_steps`); each gate is
transcribed in source order with the typed marker the record leaves when a
case terminates there. Leg 2 is an exact chain — every trial leaves by one
door — and it closes: 161 entered − 153 declined = 8 minted, and
`objects/warrant/` holds exactly 8 `w:argtrial:` warrants.

**P-R1's funnel, in one line: 126 dispatches → 123 cases → 94 attacks → 91
with case text → 89 observed only → 0 escalated → 0 trials.** The binding
gate is **U5, the authority gate** (`rules/crit.py:2159`), and its
terminator is typed: 89 `scrutiny` Measures, the marker
`_observe_case` leaves when authority is `observe_only`. Not one case
reached leg 2. Nothing was declined; nothing was blocked; the trial path
was never entered, exactly as `results.txt` reported and could not explain.

**GEX's funnel, where the road ran to the end:**

| gate | demands | arrives | leaves |
|---|---|---:|---:|
| T4 | formal supremacy does not take it | 161 | 39 `execution-backed` |
| T6 | the two judge seats agree | 122 | 43 `ensemble-split` |
| T7 | the agreed verdict is `fail` | 79 | 37 `defence-sustained` |
| T8 | every `decisive_point` quotes the exchange | 42 | 12 `referential-integrity` |
| T9 | the ruling survives paraphrase | 30 | 22 (19 re-ruling split, 3 flip) |
| T10 | **warrant minted** | 8 | — |

The dominant terminator INSIDE a trial is the ensemble itself: 62 of 153
declines (41%) are `ensemble-split` — the two families disagreed. Add the
37 `defence-sustained` and the picture is that **the guards did most of the
work the operator's standing caution about judges would want them to do**:
only 8 of 122 convened trials (6.6%) survived unanimity, referential
integrity and paraphrase invariance. `ensemble-split` is spelled
identically at T6 and T9 by design; two independent structural
discriminators place every one of the 62, with none unplaced.

## 2026-08-26 — segment 3: design, defect, or gap — the verdict

**GAP, with a defect underneath it, and the defect is in `src/`.**

Not *design*: P-R1's operator did not choose `observe_only`. Its
`run-config.yaml` says `ENGAGED_CRITICISM_AUTHORITY: defended_trial`,
`ADJUDICATION_STATUS_AUTHORITY_ENABLED: true`, `JUDGE_SEATS_ENABLED: true`,
`LEGACY_CRITICISM_ENABLED: false`, and names a two-family judge ensemble
that was compiled, qualified and paid for.

Not *defect-as-unsatisfiable-gate*: the same gate was satisfied 161 times
in GEX, and 8 cases went all the way through it.

**Gap, precisely:** `ENGAGED_CRITICISM_AUTHORITY` reaches the run through
exactly ONE carrier — the compiled manifest's `criticism_policy` — and
P-R1's manifest carries `null`. `preparation.py:499` builds that policy from
the knob; GEX's `build_manifest.py:136-145` copies the same three lines;
P-R1's `build_manifest_pr1.py:216` calls `compile_run_manifest` and never
passes `criticism_policy=`, whose default is `None`. With the field null,
`scheduler.py:1346` takes the legacy branch, `crit.py:_authority` applies
the master gate to `ARGUMENTATIVE_AUTHORITY` — which P-R1 deliberately left
at `observe_only` to dodge `CALIBRATION_RECEIPT_REQUIRED` — and every case
is observed. The same omission is in the epoch3, rung7 and P-C1 builders:
**four tranches asked for a defended trial and three of the four builders
after GEX dropped the line.**

**The defect underneath: compile discloses nothing.** `run_manifest.py`
drops `ENGAGED_CRITICISM_AUTHORITY` from `engine_config_json` on purpose
(docs/ERRATA.md E44 — leaving it in moves every qualification subject
digest), and emits **no compile notice** when a Config asking for
`defended_trial` compiles to a manifest with no criticism policy. So the
operator's instruction vanishes at compile with no denial and no
disclosure, which is the shape the 2026-08-12 all-configurations law
forbids: *"what used to be a compile-time refusal... becomes a typed
disclosure recorded alongside the compiled result... never a stop."* There
is no stop here, and no disclosure either.

`disclosure_probe.py` reproduces it offline from P-R1's own committed
config, and is mutation-proven (forcing a policy into its P2 call turns it
red):

    P1  config as written                 ENGAGED_CRITICISM_AUTHORITY=defended_trial
    P2  compiled the builder's way        criticism_policy None · compile_notices []
                                          · knob absent from engine_config echo
                                          · 2 judge seats frozen anyway
    P3  compiled the managed way          criticism_policy defended_trial

Same bytes. The difference is the door.

Nothing here is fixed. Two parked prompts in `PARKED.md`.

## 2026-08-26 — segment 4: were the commitments attacked correctly

**Yes — 60 of 60, ruled independently.** W2 re-derived all 463 mechanical
verdicts with `deepreason.programs.evaluate`, the same evaluator that wrote
them, and got 463/463; that proves internal consistency and cannot catch an
evaluator bug, which would reproduce itself on both sides. This tranche
re-implements both predicate families from the commitments' own `eval`
text, in `handcheck.py`, which **imports nothing from `deepreason`**, and
prints the decisive fact for every row so a reader can check it by eye.

| root | sampled | correct | incorrect | ambiguous |
|---|---:|---:|---:|---:|
| P-R1 | 30 of 118 | **30** | 0 | 0 |
| P-C1 | 30 of 345 | **30** | 0 | 0 |

Stratification is deliberately NOT proportional — every row of each small
criterion family, the remainder from the largest — so each family gets a
real test rather than 25 rows on the best-evidenced one. Selection inside a
family is by even stride over log seq, so the sample spans the run's
timeline; no clock, no RNG.

The decisive facts are checkable without trusting the checker. Of the 30
P-C1 rows, 13 have **no POINT lines at all** — the artifact described a
construction in prose and never emitted one; one submits 12 points where 13
are demanded, and says so itself ("4-3-2-3 Layered"); the rest are
collinear triples a reader can verify by looking, like (0, 0), (0.25,
0.25), (0.5, 0.5) on the line y = x.

**The verdicts are right and one of the criteria is not.** Separately
measured, over all 527 P-R1 artifacts with inline content:
`poietics-installation-mechanism@v1` demands one of nine spellings of the
distribution, and the operator's own question writes it as **"the 3-of-26
result"** — hyphenated, which is not on the list. **18 artifacts name the
distribution in the question's own spelling and match nothing on the
criterion's list, and 6 of the 8 verdicts that criterion issued in the
entire run landed on one of them.** Every one of those verdicts is correct
as specified. The criterion is the thing at fault, and this is a finding
about criterion quality, deliberately reported in a different file from the
ruling sample (`criterion_proxy_probe.json`) so the two are never conflated.

---

## 2026-08-26 — segment 5: the residue

*Accepted does not mean true, and correct does not mean well-aimed.* What
this tranche did NOT establish:

1. **"Correct" means "correct as specified", and nothing more.** All 60
   rulings compare a predicate's truth value on the artifact's bytes
   against the recorded verdict. Whether the artifact DESERVED refuting —
   whether the criterion measures the thing the question asked about — is
   answered for exactly one criterion (the hyphen finding above) and left
   open for the other five.
2. **The P-C1 geometric rows are not literally hand-arithmetic.** A
   13-point minimum-area check is 286 triangles; ruling those in a head is
   less reliable than a second implementation, not more. `handcheck.py` is
   that second implementation, written from the `eval` text by a different
   author than `programs.evaluate`, and every row also prints a witness
   triple that IS eyeball-checkable. Where a row's decisive fact is "0
   POINT lines" the artifact bytes were read directly (E2 and E1 in
   `EXEMPLARS.md`).
3. **A shared regex is a shared assumption.** For the `frontier-*` family,
   both the harness's predicate and this checker use the same `POINT ...`
   regex, because it is IN the commitment. So "0 POINT lines" is not an
   independent confirmation that the artifact emitted no construction — it
   is a confirmation that the artifact emitted none in the form the
   criterion demands. The bytes in E2 settle that particular case; the
   general point stands for the family.
4. **The checker's own parser was wrong once, and the ruling survived by
   luck.** `terms_from_eval` originally handled only `any(...)` and
   `sum(...) >= n` and silently dropped the bare `'refuted if' in
   content.lower()` conjunct of `relation-form@578e42df713e` — modelling a
   two-clause predicate as one. The two affected rulings happened to be
   unchanged because the dropped conjunct was the TRUE one. It now returns
   its conjunct count and refuses to rule when the reconstruction is
   incomplete (`ambiguous`), and the refusal is mutation-proven. Recorded
   here rather than quietly fixed, because "the instrument agreed with the
   record" is worth exactly nothing if the instrument was not modelling
   the record.
5. **119 `defended-trial-deferred` Measures in GEX are unreconciled.**
   Crash recovery has no provider boundary by design, so the case is left
   OPEN for a later live cycle. A deferred case may therefore ALSO be one
   of the 161 trials entered, and this census cannot tell which. They are
   reported in the funnel and excluded from its arithmetic, in both
   directions explicitly.
6. **Leg 1 is not a chain and is not presented as one.** Its stages are
   measured independently; the P-R1 gap between 91 non-empty attacking
   cases and 89 `scrutiny` markers is 2 (dedup or out-of-batch targets,
   which `continue` with no marker at all), and GEX's gap is −2 against 4
   unreadable completion blobs. Both are printed.
7. **One normalization is applied to raw completions: a markdown code
   fence is stripped.** The harness's own repair path accepts a fenced
   body, and refusing it would have reported 100 of GEX's 123 dispatches as
   unreadable. Nothing else is repaired; a body that is still not JSON is
   counted unreadable, never dropped.
8. **This tranche does not measure judge FORM FILLING (D6) at the field
   level.** It counts what judges did — 342 calls, 62 splits, 37
   defences sustained, 12 referential-integrity failures — and not what
   they wrote into `verdict` / `decisive_point`. The rulings are in GEX's
   blobs, unread here. That is the natural next window and is parked.
9. **Why the ensemble split 62 times is unexplained.** A split is recorded
   as a "critic-gaming signal" by `_judge_all`'s docstring, but nothing in
   this census distinguishes a critic gaming the ensemble from two model
   families honestly disagreeing on a hard case. Both are consistent with
   41% of declines.
10. **The judge road was measured on ONE root that ran it.** GEX is a
    single run, one question, one 2-family ensemble. Its 6.6% survival
    through the guards is a fact about that run, not a rate. The operator's
    standing caution — that judges "prosecute without any discernable
    discrimination" — is neither confirmed nor refuted by 8 sustained
    trials out of 122; it now has live evidence to be tested against for
    the first time, which it did not have before this tranche.
11. **W2's `dispatch_authority: observe_only` and this tranche's U5
    terminator are the same fact from two directions**, not two
    independent confirmations. W2 read the dispatch records; this reads the
    `scrutiny` Measures and the manifest. They agree at 89, which is worth
    stating, but a common upstream cause would move both.

---

## What this does NOT mean

It does not mean the harness's adjudication is unsound: 60 of 60 sampled
verdicts rule correctly on their artifacts' own bytes, by an independent
implementation, and the 8 trial-minted warrants in GEX each carried into
exactly one attack edge against exactly their named target. It does not
mean the judge ensemble is worthless — on its one live outing its guards
turned away 114 of 122 convened trials, which is the opposite of
prosecuting indiscriminately. And it does not mean P-R1's 419 acceptances
are wrong; it means they are acceptances under the legacy criticism path,
because the road to the other one was never opened for that run — and the
run's own record could not say so, because compile never wrote down that it
had dropped the request.

## Instruments (all committed, all re-runnable)

    python3 trial_sweep.py            # all 54 roots, _adjudication re-derived
    python3 road_census.py            # both legs, gate by gate, 2 roots
    python3 disclosure_probe.py       # P-R1's terminator, offline, from its config
    python3 verdict_sample.py         # the stratified 60 rows + artifact bytes
    python3 handcheck.py              # independent re-derivation (no deepreason import)
    python3 criterion_proxy_probe.py  # criterion quality, measured separately
    python3 tables.py                 # FUNNEL.md + ADJUDICATION_SAMPLE.md
    python3 exemplars.py              # EXEMPLARS.md

---

## 2026-08-26 — segment 6: the gate

    $ git diff --stat origin/main | tail -1
     21 files changed, 9444 insertions(+)  # all under
                                           # W4-judge-road/

    $ git diff --name-only origin/main | grep -E '^(src|tests)/'
    (no output)                            # READ-ONLY GATE PASS

    $ git diff --name-only origin/main         | grep -v '^experiments/2026-08-26-run-anatomy-program/W4-judge-road/'
    (no output)                            # SCOPE PASS: W5 and W6 run
                                           # concurrently; this window wrote
                                           # only inside its own directory,
                                           # and appended nothing to
                                           # PROGRAM.md, which is W1's.

    $ git status --short experiments/2026-08-25-poietics-program                          experiments/2026-08-25-change-constructive-frontier                          experiments/2026-08-12-live-grounded-extension-expansion
    (no output)                            # no committed root modified

No pytest gate is owed: no `src/` or `tests/` byte changed. Every root was
opened `read_only=True` where a Harness was opened at all; most instruments
read the roots as text and never construct one.

**Reproducibility, checked rather than asserted.** Every generated file was
deleted and all eight instruments re-run from scratch; the three JSONs that
were already committed came back byte-identical (`git diff` empty). No
instrument reads a clock or an RNG.

Gate for a read-only tranche: `git diff --stat origin/main` names no path
under `src/` or `tests/`.
