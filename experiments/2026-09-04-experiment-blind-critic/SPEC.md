# Spec for: does a blind critic perform better?
Traces: every item cites R/C numbers from REQUEST.md. Untraceable items
are bugs.

This tranche is an EXPERIMENT. It changes nothing a run does. Its
deliverables are a frozen pre-registration, a sealed ground-truth key,
raw records, and a verdict per factor. Zero bytes change under `src/`,
and that is an acceptance check on every commit (S0).

---

## The shape of the instrument, in one paragraph

Four critic briefs, one target at a time, same target to all four. Each
brief is a registered LAYOUT over the shipped section plugins plus at
most two new ones; selecting a brief is one environment assignment, and
the state the critic reads is byte-identical across all four cells, so
the only thing that varies is what the brief SHOWS. 120 targets — 60
untouched, 60 each carrying one mechanically planted defect — go to all
four cells: 480 real criticism calls through `rules/crit.py` against the
live provider, each leaving the typed record the harness always writes.

---

## Items

**S0 (C1, R5).** Standing acceptance check on EVERY commit in this
tranche: no byte under `src/` changes.
    accept: `git diff --stat 0f6bf2c854 -- src/ | wc -l` -> `0`
    accept: `git status --porcelain src/ | wc -l` -> `0`

**S1 (R1).** Section-by-section census of `seat-pack.critic.legacy-v0`,
written into PREREG.md: all thirteen entries, each with what it renders
and whether it carries provenance (school id / origin / author seat) or
history (rebuttal / discharge). Derived by rendering, not by reading.
    accept: PREREG.md contains a 13-row table whose plugin ids equal
    `[e.plugin_id for e in CRITIC_LEGACY_LAYOUT.entries]`, and a pasted
    default render of a target artifact showing neither a provenance nor
    a history section.

**S2 (R2, R5).** F1 provenance is one operator-authored section plugin,
`dr.exp.provenance`, rendering three lines from
`state.artifacts[target_id].provenance`: author seat (`role`), school
(`school`), origin (the mapping fixed in A1).
    accept: rendering cell C10 on a target with `role=conjecturer,
    school=school-2` emits a `target-provenance` section naming all
    three; rendering cell C00 on the same state emits none.

**S3 (R3, R5).** F2 history is one operator-authored section plugin,
`dr.exp.history-critic`, rendering, per prior objection against this
target: the objection, its outcome (landed / not landed), and the
author's answer where the source root recorded one.
    accept: rendering cell C01 on a state carrying two history records
    for the target emits a `target-criticism-history` section listing
    both; cell C00 on the same state emits none.

**S4 (R4, R5).** Four registered layouts, one per cell, each the shipped
critic layout's thirteen entries plus zero, one or two of the above:
    C00 = shipped thirteen (labels OMITTED, history OMITTED) — today
    C10 = + provenance          (labels PRESENT, history OMITTED)
    C01 = + history             (labels OMITTED, history PRESENT)
    C11 = + provenance + history (both PRESENT)
    accept: C00's render is BYTE-IDENTICAL to the default render on the
    same state; the four renders are pairwise distinct; selection is one
    `DEEPREASON_SEAT_PACK_LAYOUT=argumentative_critic=<id>` assignment;
    and S0 holds across the whole registration.
    MEASURED ALREADY — see M3 below.

**S5 (R6).** The target set: 120 accepted conjecturer artifacts drawn
from the six roots named in M1, selected by a pre-registered
deterministic rule (sort every eligible artifact by `sha256(artifact_id)`
and take the first 120), then split by the same rule (the first 60 of
that order are PLANTED, the last 60 are CLEAN). Copied into the bench,
never edited in place in any committed root.
    accept: `SELECTION.json` lists 120 ids with the source root of each;
    re-running the selector reproduces the same 120 ids and the same
    split, byte-for-byte.

**S6 (R7).** The planting method is `scripts/court_calibration_corpus.py`'s:
deterministic, no randomness, no model call, mechanical single-field
edits to a parsed copy, one defect per artifact, six classes balanced
10/10/10/10/10/10, and an `assert_single_difference` check that exactly
one field differs and nothing else moved. Three classes are the source's
verbatim; three are adapted because this pool's artifacts do not carry
the source pool's fields (A2, measured in M2).
    accept: `plant.py` re-run reproduces `DEFECT_KEY.json` byte-for-byte;
    every pair passes a single-difference assertion; class counts are
    10 each.

**S7 (R8, R20).** `DEFECT_KEY.json` (the ground-truth key: pair id,
source root, artifact id, defect class, changed field, the defect note,
and the clean/planted bodies) is committed, and its sha256 is recorded
in `PREREG.md`, and PREREG.md's own sha256 is recorded in
`PREREG.sha256`, and both are committed and pushed BEFORE the first
experimental provider call.
    accept: the commit that adds `PREREG.sha256` precedes, in
    `git log`, the commit that adds any file under `raw/`; and
    `sha256sum -c PREREG.sha256` passes at delivery.

**S8 (R9, R10, R11, R12, R13, C4).** M1-M4 are computed only from the
typed record the bench writes, by `measure.py`. No number any model
reported about its own performance enters any of them. The critic's
`attack` boolean and `case` text are FORM FIELDS, not self-reports, and
are admissible; a model-produced score, confidence or self-rating is not
and none is requested.
    accept: `measure.py` contains no read of any field named
    `score|confidence|rating|self`; its inputs are `log.jsonl`,
    `run-status.json`, the state's `att`, and the recorded
    `ArgumentativeCriticOutput` payloads.

**S9 (R10).** M1 sensitivity = share of the 60 planted targets, per
cell, whose criticism NAMES the planted defect. Two detectors, both
pre-registered, both blind to cell:
  - PRIMARY: a three-grader panel; each grader sees the clean body, the
    planted body, the defect note, and the criticism text — never the
    cell, never the layout, never which arm. Majority of three.
  - SECONDARY: a deterministic lexical detector keyed on the mutation's
    own distinctive tokens.
  Agreement between the two is reported, never reconciled after the
  fact.
    accept: `M1.json` carries per-cell numerator/denominator for both
    detectors and the pairwise agreement; the grader inputs carry no
    cell field (checked by asserting the key set of every grader row).

**S10 (R11).** M2 false attack = share of the 60 CLEAN targets, per
cell, on which `attack` is true.
    accept: `M2.json` carries per-cell numerator/denominator.
    SATURATION RULE, fixed here (A3): if `min(M2) >= 0.95` or
    `max(M2) <= 0.05` across the four cells, M2 is declared
    NON-DISCRIMINATING in RESULTS.md, the verdict's M2 clause is
    reported as unmet-by-saturation rather than silently dropped, and
    the verdict for each factor is stated with that caveat attached.

**S11 (R12, R17).** M3 warrant rate = (criticisms that became attack
edges) / (all criticism attempts), per cell — attempts read from EVERY
recorded criticism call, not from `att` alone. The denominator is the
number of criticism calls that returned a parsed
`ArgumentativeCriticOutput`; the numerator is the number of `att` edges
minted. Unwarranted attacks (`attack=true`, no edge) and non-attacks
(`attack=false`) are counted separately and reported.
    accept: `M3.json` reports, per cell, `calls`, `attack_true`,
    `att_edges`, `scrutiny_events`; and `attack_true >= att_edges`
    holds, which is the check that the denominator is not `att` again
    (the defect PARKED P7 CORRECTED names).

**S12 (R13).** M4 spend per criticism = completion + prompt tokens per
criticism call, per cell, from the endpoint's recorded usage. Caps are
matched across cells: identical `max_tokens`, `timeout_s`,
`PACK_TOKEN_BUDGET` and model for all four.
    accept: `M4.json` reports per-cell mean/median prompt, completion
    and total tokens over calls; and a config-identity assertion that
    the four cells' endpoint parameters and pack budget are equal.

**S13 (R14).** M5 sharpness, by the three-judge protocol copied from
`JUDGING_PREREG_COPIED.md`. ADOPTED UNCHANGED: three independent judges,
0-3 per criterion, median-of-three total, the >4-point-span contested
flag, structural blinding, and the keymap-stays-shut rule. RE-FIXED for
this tranche because the copied criteria 1-5 are written about one seed
question's Popperian content and criticism text is a different object
(A4): five criteria for a criticism, stated in PREREG before any judging
call. Cell, layout, provenance and history fields are OMITTED ENTIRELY
from what a judge sees — omitted, never blanked (the placebo finding,
`docs/RESEARCH_JUDGE_BLINDING_2026-08-22.md`).
    accept: `blind/criticisms.jsonl` rows carry exactly the keys
    `{bid, target_text, criticism_text}` and nothing else — asserted on
    the key set, not inspected by eye; `blind/keymap.json` is committed
    in the SAME commit as `blind/scores.json` and not before.

**S14 (R15, R20).** The verdict rule, fixed here, applied per factor to
the two levels (each level pools its two cells):
    d1 = M1(OMITTED) - M1(PRESENT);  d2 = M2(OMITTED) - M2(PRESENT)
  BLIND BETTER iff d1 >= 0.20 AND the two-proportion z-test on M1 gives
    p < 0.05 AND d2 <= 0.05.
  INFORMED BETTER iff -d1 >= 0.20 AND p < 0.05 AND -d2 <= 0.05.
  INCONCLUSIVE otherwise — including a significant M1 difference bought
    at a worse false-attack rate, which is exactly what R15 forbids
    calling "better".
    accept: RESULTS.md states one of the three words per factor, with
    d1, d2, p and the counts beside it.

**S15 (R16).** Sample size and its arithmetic, in PREREG (A5, computed
in M4 below): 60 planted + 60 clean per cell; each factor level pools
two cells, so 120 planted observations per level, against the 99 a
two-proportion test needs for a 20-point difference at the least
favourable base rate. The matched design (same targets in every cell)
is additionally reported by McNemar, which needs fewer.
    accept: PREREG.md contains the arithmetic as a runnable expression
    whose output is pasted beside it.

**S16 (R18, R19, C3, C6).** Live operation: one model for the critic
seat in all four cells (A6); at most 3 concurrent calls; the key read at
call time from the tranche's gitignored `env`; a green
`scripts/cycle_soak.py` recorded before the first experimental call; the
bench launched detached with a snapshot loop armed.
    accept: `SOAK.txt` holds the soak's own output with rc=0;
    `raw/driver.log` exists and its process was launched with
    `setsid nohup`; `git check-ignore experiments/2026-09-04-experiment-blind-critic/env`
    exits 0; no committed file in this tranche contains the key.

**S17 (R20, R21).** Deliverables: `PREREG.md` + `PREREG.sha256`,
`DEFECT_KEY.json`, `SELECTION.json`, `raw/` (every call's request pack,
reply payload and usage, plus the bench run roots), `RESULTS.md` with
one verdict per factor and a residue section. An inconclusive result is
recorded as inconclusive, with what would have decided it.
    accept: all named paths exist and are committed; RESULTS.md carries
    a "Residue" section.

**S18 (R22).** No default changes. `seat-pack.critic.legacy-v0`,
`seat.critic.legacy-v0`, and every registration in
`src/deepreason/llm/seat_layouts.py` are untouched; the four cell
layouts are registered by the tranche's own driver at runtime and exist
nowhere else.
    accept: S0's checks, plus
    `python -m pytest tests/test_crit_pack_legacy_golden.py tests/test_seat_section_architecture.py tests/test_seat_pack_layout.py -q` -> 0 failed.

**S19 (R23).** CLAUDE.md read in full, including the 2026-08-28 judge
law and the 2026-09-03 progress law. Consequences carried into the
design, each named in PREREG: judges are used only where the operator's
own protocol uses them (M5 sharpness and the M1 naming panel), blinding
is STRUCTURAL (fields omitted, never blanked), and "performs better"
means more real error found at no worse false attack — never "more
criticism" and never "correct".
    accept: PREREG.md's "What this tranche is allowed to conclude"
    section states all three.

**S20 (R24).** Commit and push at every phase boundary and every
executed step.
    accept: `git log --oneline` shows one commit per checklist step, and
    `git status --porcelain` is empty at delivery.

---

## Assumptions (operator may override)

**A1 (Q1) — F1's "origin" is read off `Provenance.role`.** The record
has no field named `origin`. `Provenance` carries `role`, `school` and
`event_seq` and nothing else, and `role` is the only recorded fact that
distinguishes the operator's three origin values. Fixed mapping:
`seed` -> "seed (the operator's own question)"; `conjecturer`, `critic`,
`controller` -> "harness-minted"; `import`, `experimenter` -> "capability".
Assumed, operator may override. Consequence, stated because it matters:
every target in the selected pool is `role=conjecturer`, so the origin
line reads "harness-minted" on all 120 and carries no variance. The
school line DOES vary (four schools). F1 is therefore, in practice,
mostly a SCHOOL-and-SEAT label test, and PREREG says so rather than
claiming to have varied origin.

**A2 (Q1, R7) — three of six defect classes are adapted.** Measured
(M2): across all 238 eligible artifacts, `scope.covers`,
`scope.excludes`, `derivation`, `premises`, `uncertainties` and
`definitions` are EMPTY, and only 9-11% carry a number. The source's
`chronology-error` (needs a year) and its `scope-contradiction` (needs
`scope.covers`) therefore cannot be applied as written, and its
`evidence-misquotation` targets a `prose_notes` field this shape does
not have. The six classes are: `unsupported-comparison` and
`causal-non-sequitur` (source-identical, appended to `mechanism`);
`vacuous-forbidden-case` (source-identical, including its verbatim
VACUOUS_CASE string, applied to `counterconditions[0].case`, which is
this shape's `forbidden`); `evidence-misquotation` (source's semantics,
appended to `mechanism` because `prose_notes` does not exist);
`scope-contradiction` (source's semantics — the same case in scope and
out of it — realised by writing the claim's own leading sentence into
`scope.excludes`); and `circular-mechanism` (NEW, replacing
`chronology-error`, which this domain cannot carry: appends to
`mechanism` a sentence giving the claim as the reason for the claim).
Assumed, operator may override. Cost of the adaptation, stated: four of
six classes now mutate `mechanism`, where the source had two of six.

**A3 (Q3) — M2's saturation rule is fixed before any call.** The record
holds two disagreeing measurements of the bare critic on sound work —
objection rate 1.0 on clean items
(`experiments/results/court_calibration_v1_report.json`) and 0.325
acquittal, i.e. 0.675 objection, on verified-sound items
(`experiments/results/critic_specificity_report.json`) — both on other
models and other packs. Either way M2 may saturate. S10 fixes what
happens then, in advance, so nobody resolves it by reading the numbers.
This is the P7-CORRECTED lesson applied ahead of the evidence: a measure
that cannot fail is not a measure.

**A4 (Q4) — the judging protocol's machinery transfers; its criteria do
not.** The copied criteria 1-5 are written about a specific seed
question's Popperian machinery ("the pragmatic preference of *Objective
Knowledge*"). Criticism text is a different object, so five criteria for
a criticism are fixed in PREREG before any judging call, and the copied
document's own header contemplates exactly this ("the ARM LABELS
differ ... so the keymap maps to those instead"). Everything else is
adopted unchanged and named in S13.

**A5 (Q5) — sample size comes from the objection VOLUMES, not from the
saturated rate.** M3's sustain rate was 1.000 in every cell and carries
no variance to power anything; PARKED P7 CORRECTED gives the usable
numbers (52 and 38 criticism artifacts; 3 and 1 warranted). Two
consequences, both pre-registered: the land rate is near 0.03-0.06,
so M3 is FLOOR-limited and is reported descriptively — it is
pre-registered as underpowered for a 20-point difference and may not
decide a verdict; and the sample size is set from M1, which is what R16
actually asks to be detectable. Arithmetic in M4 below.

**A6 (Q2, R18) — a controlled bench, not a managed run; glm-5.2 as the
critic seat.** Two readings of "live runs" were open. A managed
`deepreason reason` run cannot be used: R6 fixes the TARGETS, and a
managed run generates its own, so the four cells would criticise four
different things and no difference could be attributed to the factor.
Planting a defect into a committed root is forbidden outright. So the
targets are copied into a fresh bench run root per cell, and the REAL
`rules/crit.py::crit_argumentative` is driven against the live provider
— giving real typed records, real warrants, real `att` edges and real
token accounting. `cycle_soak.py`, the detached launch and the snapshot
loop (R19) are honoured as written. Model: CLAUDE.md's own header names
main's provider as glm-5.2 on Ollama Cloud; the last two live tranches
bound the critic seat to `deepseek-v4-pro:0813` (P-A2) and
`qwen3.5:397b` (the history experiment). CLAUDE.md is the higher
authority, so glm-5.2 it is, identically in all four cells. Assumed,
operator may override; the choice affects how far the result travels to
other models, never the comparison between cells.

**A7 (C1) — the batch critic renderer is not used.** `crit_argumentative`
(single target per call), never `crit_argumentative_batch`. Out of scope
by C1 and, independently, one target per call is what a matched design
needs.

**A8 (S11) — criticism authority is `observe_only` in all four cells.**
The operator's question is about a CRITIC, not a judge (R's headline
words), and the 2026-08-28 judge law makes judge use a per-run choice
rather than a default. `observe_only` records every objection as a
critic-role artifact with a `["scrutiny", target, critic]` Measure and
mints no edge; a `defended_trial` authority would put a JUDGE ensemble
between the critic and every measure, which is the confound this tranche
exists to avoid. Consequence, stated so M3 is not over-read: under
`observe_only`, `att` edges arise only from a grounded COUNTEREXAMPLE,
so M3 will be at or near zero in every cell. M3 is reported; it is not
expected to decide anything, and A5 already says so.

---

## Questions for operator (STOP if non-empty)

None. Every open question in REQUEST.md was answered from the record or
decided under the operator's recorded values and written into
Assumptions above, where any of them can be overridden.

One thing is DISCLOSED rather than asked, because the operator should
see it and because the gate's verdict depends on how the declaration is
written — see the Frozen-surface contact forecast below.

---

## Out of scope (explicit)

- Judge blinding — measured already (C1). Not re-measured.
- Changing any default critic exposure (C1, R22). The result goes to the
  operator as a decision.
- Any frozen surface (C1). Zero bytes change under `src/` (S0).
- The batch critic renderer (C1, A7).
- Fixing anything this tranche notices. Findings go to PARKED.md with a
  ready-to-send prompt, per the cross-routing rule.
- A no-harness baseline arm. The 2026-09-03 progress law asks every live
  experiment to carry or cite one; this tranche compares four HARNESS
  configurations against each other, so the law's comparison is between
  cells and the baseline question ("is the harness better than one
  call") is a different tranche. Named here so the omission is a
  decision, not an oversight, and recorded in PREREG's residue.

---

## Frozen-surface contact forecast

Run twice, and both runs are pasted because the first shows how the
verdict depends on the declaration and the second is the honest one.

**Run 1 — over-declared** (`--symbols ... Harness OpenAICompatEndpoint
LLMAdapter SeatPackLayoutV1 SectionRenderV1`), verbatim:

    frozen_surface_verdict : CONTACT
    frozen_surface_contacts:
      harness.py event application and well-formedness | SYMBOL_INDIRECT | Harness
      replay-validation record formats (invariants.py) | SYMBOL_INDIRECT | Harness
      manifest schemas and validators (run_manifest.py) | SYMBOL_INDIRECT | Harness
    frozen_adjacent_contacts: []
    detail (gate's own words): "'Harness' referenced in
      src/deepreason/harness.py (grep-based; not proof of semantic contact)"

**Run 2 — honest declaration** (the symbols this tranche calls; it
modifies none of them and declares no `src/` file as a target),
verbatim:

    frozen_surface_verdict : CLEAR
    frozen_surface_contacts: []
    frozen_adjacent_contacts: []
    reachability: render_crit_pack REACHABLE, crit_argumentative
      REACHABLE, register_seat_pack_layout REACHABLE,
      register_section_plugin REACHABLE, resolve_seat_pack_layout
      REACHABLE
    disclosure_summary: "This change touches none of the five frozen
      surfaces. 5 test file(s) and 4 map document(s) assert on the
      touched targets today."

**Why run 1 fires and why run 2 governs.** `--symbols` declares what a
change TARGETS. This tranche targets no symbol: it CALLS `Harness` the
way every test in the tree calls it, and the gate's SYMBOL_INDIRECT tier
is a grep hit, which the gate's own detail line says is "not proof of
semantic contact". The claim that nothing is touched is not left to that
argument, though — it is checked byte-for-byte on every commit (S0), and
the probe that built all four cells already measured it: `src/` mtimes
unchanged and `src/` content sha256 unchanged (M3 below). Recorded as a
decision the operator can reverse: no operator words were sought,
because seeking them for a grep hit in a tranche that provably changes
zero bytes would spend the scarcest budget in the system on a false
fork.

**UNKNOWN reachability entries** (run 1: `SeatPackLayoutV1`,
`SectionRenderV1`, `Harness`, `OpenAICompatEndpoint`, `LLMAdapter` —
class names the gate cannot resolve to a call path) are cross-checked by
the retained manual grep, in the Blast-radius census below.

---

## Blast-radius census

From run 2's `consumers`, every hit classified. Nothing in this tranche
changes any of these, so every single hit is MUST NOT MOVE, and S18's
targeted gate plus S0's byte check are how that is proven rather than
asserted.

    render_crit_pack        -> 42 test hits across 16 files      MUST NOT MOVE
                               27 map-check hits across 8 docs   MUST NOT MOVE
    crit_argumentative      -> 41 test hits across 11 files      MUST NOT MOVE
                               13 map-check hits across 6 docs   MUST NOT MOVE
    register_seat_pack_layout -> 18 test hits across 4 files     MUST NOT MOVE
    register_section_plugin -> 15 test hits across 3 files       MUST NOT MOVE
                               1 map-check hit                   MUST NOT MOVE
    resolve_seat_pack_layout -> 13 test hits across 3 files      MUST NOT MOVE
                               1 map-check hit                   MUST NOT MOVE
    consumers.qualification_digest: []   (empty census, valid)
    consumers.wheel_smoke_pins:     []   (empty census, valid)

Manual cross-check for the five UNKNOWN-reachability symbols, per the
retained-grep rule:

    $ grep -rln "SeatPackLayoutV1\|SectionRenderV1\|OpenAICompatEndpoint" tests/ docs/map/
    -> tests only construct these; docs/map/INV-seat-section-plugins.md
       and CON-packs-and-token-economy.md name them in checks that read
       `src/`, not this tranche.               ALL MUST NOT MOVE

The one hit that could plausibly move if this tranche were wrong is
`tests/test_crit_pack_legacy_golden.py` — it pins the shipped critic
brief byte-for-byte. S18 runs it as an acceptance check precisely
because registering four new layouts beside the shipped one must leave
the shipped one alone.

---

## Measurements

Every load-bearing design claim below is a pasted command output.

**M1 — the target pool exists and is big enough.** Eligible = accepted,
non-import, `role=conjecturer`, JSON body carrying `claim`, `mechanism`
and a `scope` object:

    24 eligible  experiments/2026-09-02-live-p-a2-corrected/run
    39 eligible  .../runs/home-m3/runs/run-7a8fc89b33f8e055a212fafa09acd83f
    43 eligible  .../runs/home-m3/runs/run-5565bd1ef7011e3d25fef3197bdf1cdb
    42 eligible  .../runs/home-m1/runs/run-f23da86ddfd5ab820957221cfebe4b2e
    43 eligible  .../runs/home-m1/runs/run-ad41064484366337ed61a9d5a58de58f
    47 eligible  .../runs/home-default/runs/run-fe00609058e10605590206d51ab2b7a0
    TOTAL 238

Supports S5 (120 needed, 238 available) and names the two pools the
request pointed at — P-A2 and the history experiment's candidates.

**M2 — which defect classes the pool can actually carry.** Over all 238:

    cc>=1                   238  (100%)
    mechanism>200ch         235  (99%)
    number in mechanism      26  (11%)
    number in claim          22  (9%)
    covers>=1                 0  (0%)
    excludes>=1               0  (0%)
    derivation>=1             0  (0%)
    premises>=1               0  (0%)
    uncertainties>=1          0  (0%)
    definitions>=1            0  (0%)
    claim len median 358, min 167, max 1048

Supports A2: the source's `chronology-error` and its `scope-contradiction`
cannot be applied as written, and `prose_notes` does not exist here.

**M3 — the four cells are configuration, and `src/` does not move.**
Probe output, verbatim:

    default == C00 : True
    C00-blind-blind            bytes= 1282 prov=False hist=False
    C10-labels-only            bytes= 1476 prov=True  hist=False
    C01-history-only           bytes= 1635 prov=False hist=True
    C11-labels-and-history     bytes= 1829 prov=True  hist=True
    all four distinct: True
    src/ mtimes unchanged: True
    src/ bytes unchanged : True

Supports S2, S3, S4, S0 and R5's "no code edit". This is the measurement
that decides C2's stop condition does NOT fire.

**M4 — the sample-size arithmetic.** Two-proportion test, alpha 0.05
two-sided, power 0.80, at the least favourable base rate (p = 0.5):

    n_per_level = (1.96 + 0.8416)**2 * 2 * 0.25 / 0.20**2
    $ python3 -c "print((1.96+0.8416)**2 * 2 * 0.25 / 0.2**2)"
    98.11

So 99 planted observations per factor level. Each level pools two cells,
so 60 planted targets per cell gives 120 per level — a margin that
survives up to 17% unusable calls. Same arithmetic for M2 over 60 clean
targets per cell. Total calls: 120 targets x 4 cells = 480.
Supports S15 and R16.

**M5 — the provider is reachable and the seat's cap must clear the
model's hidden reasoning.** Probe, verbatim, at `max_tokens` 2000 with
`response_format: json_object`:

    qwen3.5:397b           content= '{"ok":true}' reas=1392 ct=382
    deepseek-v4-pro:0813   content= '{"ok":true}' reas=  45 ct= 17
    glm-5.2                content= '{"ok":true}' reas= 698 ct=190
    glm-5.3                content= '{"ok":true}' reas= 165 ct= 44

And a finding, recorded here and PARKED: the provider now REJECTS
`"reasoning":"none"` as a bare string ("cannot unmarshal string into Go
struct field ChatCompletionRequest.reasoning"), which is what the last
committed launch config sends. Supports A6's cap choice and S12's
matched caps; the rejection itself is not this tranche's to fix.

---

## Options

**A — a managed `deepreason reason` run per cell.** Files: a ladder per
cell. Frozen contact: none. ~120 lines. REJECTED, cites M1 and R6: a
managed run generates its own conjectures, so the four cells would
criticise four different target sets and no difference could be
attributed to the factor; and the 120 planted targets could not enter it
at all without editing a record, which is forbidden.

**B — render-only comparison (no provider calls).** Files: one script.
Frozen contact: none. ~80 lines. REJECTED, cites the request itself: it
would measure what the brief SAYS, not what a critic DOES. M1, M2, M3
and M5 all require a real reply.

**C — a controlled bench driving the real `crit_argumentative` against
the live provider, one bench run root per cell, matched targets.**
Files: `plant.py`, `select.py`, `bench.py`, `measure.py`, `judge.py`,
all under `experiments/`. Frozen contact: none (run 2 above). ~900 lines
of experiment code. CHOSEN, cites M3 (the four cells are pure
configuration and `src/` provably does not move) and M1 (the matched
target set exists).

---

## Budget

Itemised, experiment files only:

    select.py    80   plant.py    170   bench.py   300
    measure.py  220   judge.py    240   PREREG.md  420
    RESULTS.md  300   PARKED.md    80   CHECKLIST/DELIVERY 200

    $ python3 -c "print(sum([80,170,300,220,240,420,300,80,200]))"
    2010

~2010 lines, all under `experiments/2026-09-04-experiment-blind-critic/`,
across ~12 commits (one per checklist step).
**Lines changed under `src/`: 0.** Frozen surfaces touched: none.
The ~300-line ceiling governs `src/` diffs; this tranche's diff to `src/`
is zero and its own artifacts are instruments and data, which the ceiling
was never about. Stated rather than assumed.

Rubric: 6/6 yes — every R has a machine-decidable accept (R1-R24 appear
in S1-S20); the blast-radius census is pasted and every hit classified;
the frozen-surface forecast is recorded with the gate's own output
verbatim, both runs; every mechanism the request named was traced to
code it actually reaches (`JUDGING_PREREG_COPIED.md` read and its
transferable half separated in A4; `court_calibration_corpus.py` read
and its inapplicable half measured in M2; `seat-pack.critic.legacy-v0`
censused by rendering in M3); options priced with rejections citing
measurements; nothing in this spec is untraceable to an R or C number.
