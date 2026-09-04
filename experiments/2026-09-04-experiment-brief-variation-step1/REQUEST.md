<!-- Phase: dr-capture-request. Authority for everything in this tranche. -->

# REQUEST — STEP 1 live: hold the form, vary the brief, measure against
# the no-harness baseline with length held constant

Captured: 2026-09-04, before any file in this directory was written and
before any provider call was made.
Branch: `claude/brief-variation-harness-experiment-fhv8qu`.
Base: `main` at `33f92e88c` (the required "at or after 33f92e88c7").

## §0 Map preflight — the ids this tranche resolved BEFORE designing

Recorded here because CLAUDE.md requires the map ids in the tranche's
first artifact, and because two of them decided the rig.

| id | why it is in scope |
|---|---|
| `DR-INV-seat-section-plugins` | owns the layout/plugin/shell registries the arms select |
| `DR-INV-seat-section-sources` | owns where a section's CONTENT comes from |
| `DR-REC-add-a-section-plugin` | the recipe the arms are supposed to follow |
| `DR-SEAM-packs-and-token-economy-x-rules` | the seam, read before either side |
| `DR-CON-packs-and-token-economy` | what a pack shows and what the budget cuts |
| `DR-INV-render-layout` | the allocation policy the arms hold constant |
| `DR-INV-frozen-surfaces` | read before designing; this tranche forecasts NO CONTACT (it changes nothing under `src/`) |

## §1 The operator's words, verbatim

The message below is reproduced unaltered. It arrived three times,
byte-identical; the repetition carries no additional instruction and is
recorded here rather than treated as three requests.

> EXECUTOR WINDOW — LIVE EXPERIMENT: hold the form, vary one piece of the
> brief, and measure against the no-harness baseline with length held
> constant
>
> Read CLAUDE.md IN FULL — the 2026-09-03 law is the acceptance criterion:
> success is output MATERIALLY BETTER than the same model without the
> harness, judged blind against criteria written before any output is
> read. Load dr-change-orchestrator, dr-drive-harness,
> dr-ask-the-right-question and pinker-write-for-readers. Base on main at
> or after 33f92e88c7. Tranche directory:
> experiments/2026-09-04-experiment-brief-variation-step1/. Commit and push
> at every phase boundary; snapshot loop armed during runs.
>
> THE RECIPE IS COMMITTED AND YOU RUN IT, WITH THREE AMENDMENTS FIRST.
> Read experiments/2026-09-03-change-conjecturer-pluggable-interface/
> PREREG.md, SPEC.md §12 and analyse_form_arms.py in full. The arms are
> A0 (shipped default), A1 (history plugin: include_refuted=true,
> refuted_n=3), A2 (claim_chars 800), A3 (neighbourhood via an operator
> .tmpl), B0 (no harness: one call, same question, same model). Form fixed
> at conjecturer.turn.v6.
>
> Amend the PREREG before any call and re-seal its digest:
>  1. ADD the blind-judged quality comparison against B0 as the PRIMARY
>     success measure. PREREG §6 lists diversity and admission measures
>     only; the law's own criterion is missing from it. Use the committed
>     three-judge protocol (experiments/2026-09-03-change-provenance-
>     history-channel/JUDGING_PREREG_COPIED.md, judge.py) whose scores
>     have real spread (0-14 over 167). Provenance, arm and layout fields
>     OMITTED entirely from what judges see.
>  2. CONTROL FOR LENGTH, structurally. RESULTS_M1_QUALITY.md in that same
>     directory measured Spearman 0.797 between candidate length and judged
>     score. Pre-register: character count recorded per candidate; the arm
>     comparison reported raw AND with log-length as a covariate AND within
>     length quintiles (analyse_length_bias.py exists — call it). A verdict
>     is stated only on the length-held-constant figure. Prompt-level
>     "ignore length" instructions do NOT count (judge law: prompt-level
>     fixes do not hold).
>  3. ADD arm A1' = history plugin OFF entirely, so A0 (history ON, the
>     shipped default) vs A1' directly replicates the M1 contrast whose
>     blind judging came back "worse, suggestive": mean 5.02 vs 6.58,
>     p=0.082 raw, -0.78 adjusted. This experiment is what decides the
>     history default (SPEC.md S10 of the history tranche); say so in the
>     PREREG and name the decision rule before any call.
>
> LAUNCH DISCIPLINE, no exceptions: green `python -u scripts/cycle_soak.py
> --case <case>` on the exact launch config (all nine cases compile again
> as of 2026-09-04); model settings from the model-profile registry; at
> most 3 concurrent processes on the key; detached launch (setsid nohup,
> disown); a monitor on progress.jsonl and the driver log's rc= lines; the
> key from the gitignored env file, asked for at launch only, never
> committed, never echoed. Container restarts happen roughly every two
> hours: keep each arm inside that, and use `deepreason continue` on a
> killed run rather than relaunching. KNOWN SHAPE, not an arm death: a run
> that ends operational_failure with "token budget denied transactional
> work" near its budget ceiling is the parked defect P3 of
> experiments/2026-09-04-fix-provider-reasoning-contract/; read its
> stop-report, confirm that shape, and treat the arm as budget-complete.
>
> MEASURES: PREREG §6's four through the committed instruments, plus the
> two added above. Nothing a model says about itself enters any number.
> Matched spend: report tokens per arm and per admitted artifact; B0's
> spend is the comparison floor.
>
> RESULT: RESULTS.md — predictions restated, then the numbers, then one
> verdict per arm against B0 (better / not better / inconclusive) on the
> length-held-constant figure, then the history-default recommendation
> with its numbers, then the residue. A harness arm not better than the
> single call is a FAILED arm and is written up as one. Change no default
> yourself.
>
> FINAL MESSAGE: plain words; first sentence says whether any harness arm
> beat the plain model call once length is held constant; then what the
> history contrast showed; then what is unproven. One closing analogy.

## §2 The numbered requirements

Split from §1. Nothing here adds an obligation the operator's words do
not carry; where a word is ambiguous the ambiguity is recorded, not
resolved silently.

| R | the operator's words (short form) | what it obliges |
|---|---|---|
| R1 | "hold the form, vary one piece of the brief" | form fixed at `conjecturer.turn.v6`; exactly one brief parameter varies per arm |
| R2 | "measure against the no-harness baseline with length held constant" | B0 exists; every verdict is stated on the length-adjusted figure |
| R3 | "Read CLAUDE.md IN FULL — the 2026-09-03 law is the acceptance criterion" | success = materially better than the same model without the harness |
| R4 | "Load dr-change-orchestrator, dr-drive-harness, dr-ask-the-right-question and pinker-write-for-readers" | four skills loaded this session |
| R5 | "Base on main at or after 33f92e88c7" | base recorded; `33f92e88c` is the head |
| R6 | "Tranche directory: experiments/2026-09-04-experiment-brief-variation-step1/" | this directory |
| R7 | "Commit and push at every phase boundary; snapshot loop armed during runs" | a commit per phase; a snapshot loop for every live arm |
| R8 | "THE RECIPE IS COMMITTED AND YOU RUN IT" | the committed PREREG/S12 recipe is executed, not redesigned |
| R9 | "The arms are A0 … A1 … A2 … A3 … B0" | five arms as specified |
| R10 | "Form fixed at conjecturer.turn.v6" | no form varies in step 1 |
| R11 | amendment 1: "ADD the blind-judged quality comparison against B0 as the PRIMARY success measure" | judged quality is primary; diversity/admission become secondary |
| R12 | amendment 1: "Use the committed three-judge protocol … judge.py" | the copied protocol and its instrument, not a new one |
| R13 | amendment 1: "Provenance, arm and layout fields OMITTED entirely" | structural blinding, per the judge law |
| R14 | amendment 2: "CONTROL FOR LENGTH, structurally" | characters per candidate recorded; raw + covariate + quintile reporting |
| R15 | amendment 2: "A verdict is stated only on the length-held-constant figure" | the verdict sentence quotes the adjusted number |
| R16 | amendment 2: "Prompt-level 'ignore length' instructions do NOT count" | no prompt-level de-biasing is attempted |
| R17 | amendment 3: "ADD arm A1' = history plugin OFF entirely" | a sixth arm |
| R18 | amendment 3: "This experiment is what decides the history default … name the decision rule before any call" | the decision rule is in the PREREG, pre-sealed |
| R19 | "Amend the PREREG before any call and re-seal its digest" | amendment and digest both precede the first call |
| R20 | "green cycle_soak.py --case <case> on the exact launch config" | a green soak before any launch |
| R21 | "model settings from the model-profile registry" | the profile registry supplies the model settings |
| R22 | "at most 3 concurrent processes on the key" | concurrency ceiling 3 |
| R23 | "detached launch (setsid nohup, disown)" | no foreground ladder |
| R24 | "a monitor on progress.jsonl and the driver log's rc= lines" | a monitor per arm |
| R25 | "the key … asked for at launch only, never committed, never echoed" | the key is requested at launch; never written to git; never printed |
| R26 | "keep each arm inside [two hours]… use `deepreason continue` on a killed run" | arms sized under the restart window; continue, never relaunch |
| R27 | "KNOWN SHAPE … treat the arm as budget-complete" | the P3 stop shape is read from the stop-report and not called an arm death |
| R28 | "MEASURES: PREREG §6's four … plus the two added above" | six measures |
| R29 | "Nothing a model says about itself enters any number" | no self-reported number is a measurement |
| R30 | "Matched spend: report tokens per arm and per admitted artifact; B0's spend is the comparison floor" | a spend table with B0 as floor |
| R31 | "RESULT: RESULTS.md — predictions restated, then the numbers, then one verdict per arm against B0 …, then the history-default recommendation …, then the residue" | RESULTS.md in exactly that order |
| R32 | "A harness arm not better than the single call is a FAILED arm and is written up as one" | failure is written as failure |
| R33 | "Change no default yourself" | no default, config or source file is edited by this tranche |
| R34 | "FINAL MESSAGE: plain words … One closing analogy" | the final message's shape |

## §3 The one thing the operator's words do not settle

R25 says the key comes "from the gitignored env file, asked for at launch
only". **This container has no such file.** It was checked before anything
was built:

    $ ls experiments/live_research_*/env        # no output
    $ env | grep -i ollama                      # no output
    $ grep -rl 'OLLAMA_API_KEY=' . | grep -v .git/   # only scripts that READ it

The container was cloned fresh, and the file is gitignored by design
(`.gitignore` lines 31-51), so its absence is expected rather than a
defect. It is recorded here because it is the one input this tranche
cannot derive from the record, the framework, or the operator's recorded
values — every other question in §2 was answered from one of those. It is
asked once, at launch, and nowhere else.
