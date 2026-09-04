# Request: does a blind critic perform better?
Captured: 2026-09-04, from the executor-window prompt that opened this
session (delivered twice, byte-identical; quoted once below), plus the
two dated operator quotes it carries and one mid-turn operator message.

Tranche directory: `experiments/2026-09-04-experiment-blind-critic/`
Base: `main` at `0f6bf2c854` (branch `claude/blind-critic-experiment-synir6`).

---

## Verbatim — the operator's own words, as quoted in the prompt

> "Can you establish that a blind critic, not judge, actually performs
> better?"
> — operator, 2026-09-04

> "criticism without fully understanding the reasoning behind a
> conjecture might help sharpen critiques."
> — operator, 2026-09-03 (the earlier hypothesis; carried into this
> tranche by the prompt)

## Verbatim — the executor-window prompt, in full

> EXECUTOR WINDOW — EXPERIMENT TRANCHE: does a blind critic perform better?
> Two blindnesses, measured separately, on planted defects and blind-judged
> sharpness
>
> Read CLAUDE.md IN FULL (especially the laws of 2026-08-28 on judges, and
> 2026-09-03: success is progress over the no-harness baseline). Load
> dr-change-orchestrator, dr-drive-harness, dr-ask-the-right-question and
> pinker-write-for-readers. Start at dr-capture-request with THIS prompt as
> the operator's authority. Base on main at or after 0f6bf2c854. Tranche
> directory: experiments/2026-09-04-experiment-blind-critic/. Commit and
> push at every phase boundary.
>
> OPERATOR'S WORDS, verbatim (2026-09-04): "Can you establish that a blind
> critic, not judge, actually performs better?" Earlier hypothesis, verbatim
> (2026-09-03): "criticism without fully understanding the reasoning behind a
> conjecture might help sharpen critiques."
>
> WHAT THE RECORD ALREADY HOLDS — read these in full before designing:
> - docs/RESEARCH_JUDGE_BLINDING_2026-08-22.md and
>   experiments/2026-08-09-change-judge-evidence-review/REVIEW.md: judges
>   measured, label exposure carries the bias, a blank slot is worse than an
>   omitted one; the planted-defect method (sensitivity / false conviction).
> - experiments/2026-09-03-change-provenance-history-channel/RESULTS_M3.md
>   and PARKED.md P7: the one critic experiment, INCONCLUSIVE because attack
>   edges exist only for WARRANTED attacks and sustain rate saturated at
>   1.000. Your instrument must not repeat that: read EVERY criticism
>   attempt from the typed attempt objects the record holds per criticism
>   call, not from attack edges alone.
> - What the critic sees today: the seat-shell build
>   (experiments/2026-09-03-change-conjecturer-pluggable-interface/,
>   seat-pack.critic.legacy-v0) lists every section. Census it and state,
>   in the PREREG, exactly which provenance and which history the default
>   critic brief carries, section by section. Do not assume.
>
> TWO BLINDNESSES, TWO FACTORS, never conflated:
>   F1 provenance: labels OMITTED (today) vs labels PRESENT (school id,
>      origin: seed / harness-minted / capability, author seat).
>   F2 history: rebuttal + discharge history OMITTED (today) vs PRESENT.
> Four cells, the seat-shell layouts make each a configuration (a registered
> layout per cell; no code edit — if a cell needs a source edit, that is a
> finding, PARK it and stop).
>
> THE TARGETS: a fixed set of accepted artifacts drawn from committed roots
> (P-A2 epoch 4's frontier and the history experiment's candidates are the
> obvious pool), split in a pre-registered way: half UNTOUCHED, half with ONE
> planted defect each, planted by the same method the judge study used, with
> the ground-truth key committed BEFORE any call and sealed by digest.
>
> MEASURES, fixed in PREREG.md before any call (no model self-reported number
> enters any of them):
>   M1 sensitivity: planted defects the critic's criticism names.
>   M2 false attack: sound artifacts the critic attacks.
>   M3 warrant rate: criticisms that become attack edges, per cell.
>   M4 spend per criticism, per cell (matched caps across cells).
>   M5 sharpness, BLIND-judged by the committed three-judge protocol
>      (experiments/2026-09-03-change-provenance-history-channel/
>      JUDGING_PREREG_COPIED.md), with cell and provenance fields OMITTED
>      ENTIRELY from what judges see — omitted, never blanked.
> "Performs better" is decided per the 2026-09-03 law: more real error
> found (M1) at no worse false attack (M2), not "more criticism".
>
> SAMPLE SIZE is decided by the record, not by hope: use M3's saturation
> numbers to set targets per cell so that a 20-point difference in M1 is
> detectable; state the number and its arithmetic in PREREG.
>
> LIVE RUNS, tokens are cheap: critic model as configured on main's launch
> config; at most 3 concurrent calls on the key; the key comes from the
> gitignored env file, asked for at the launch step only, never committed,
> never echoed. Green cycle_soak.py on the launch config before any live
> launch; detached launch; snapshot loop armed.
>
> DELIVERABLES: PREREG.md (frozen, digest committed before calls), the
> sealed defect key, raw records preserved, RESULTS.md with one verdict per
> factor — BLIND BETTER / INFORMED BETTER / INCONCLUSIVE — and the residue.
> An inconclusive result is recorded as one. The default critic exposure on
> main is NOT changed by this tranche; the result goes to the operator as a
> decision with the numbers.
>
> OUT OF SCOPE: judge blinding (measured); changing any default; any frozen
> surface; the batch critic renderer.

---

## Requirements

R1 (artifact): "Census it and state, in the PREREG, exactly which
provenance and which history the default critic brief carries, section by
section. Do not assume." — a section-by-section census of
`seat-pack.critic.legacy-v0`, written into PREREG.md.

R2 (behavior): "F1 provenance: labels OMITTED (today) vs labels PRESENT
(school id, origin: seed / harness-minted / capability, author seat)."

R3 (behavior): "F2 history: rebuttal + discharge history OMITTED (today)
vs PRESENT."

R4 (process): "TWO BLINDNESSES, TWO FACTORS, never conflated" — F1 and F2
are measured separately; four cells.

R5 (behavior): "Four cells, the seat-shell layouts make each a
configuration (a registered layout per cell; no code edit — if a cell
needs a source edit, that is a finding, PARK it and stop)."

R6 (artifact): "THE TARGETS: a fixed set of accepted artifacts drawn from
committed roots (P-A2 epoch 4's frontier and the history experiment's
candidates are the obvious pool), split in a pre-registered way: half
UNTOUCHED, half with ONE planted defect each".

R7 (process): "planted by the same method the judge study used".

R8 (artifact): "with the ground-truth key committed BEFORE any call and
sealed by digest."

R9 (artifact): "MEASURES, fixed in PREREG.md before any call (no model
self-reported number enters any of them)".

R10 (behavior): "M1 sensitivity: planted defects the critic's criticism
names."

R11 (behavior): "M2 false attack: sound artifacts the critic attacks."

R12 (behavior): "M3 warrant rate: criticisms that become attack edges,
per cell."

R13 (behavior): "M4 spend per criticism, per cell (matched caps across
cells)."

R14 (behavior): "M5 sharpness, BLIND-judged by the committed three-judge
protocol (experiments/2026-09-03-change-provenance-history-channel/
JUDGING_PREREG_COPIED.md), with cell and provenance fields OMITTED
ENTIRELY from what judges see — omitted, never blanked."

R15 (process): "'Performs better' is decided per the 2026-09-03 law: more
real error found (M1) at no worse false attack (M2), not 'more
criticism'."

R16 (artifact): "SAMPLE SIZE is decided by the record, not by hope: use
M3's saturation numbers to set targets per cell so that a 20-point
difference in M1 is detectable; state the number and its arithmetic in
PREREG."

R17 (process): "Your instrument must not repeat that: read EVERY
criticism attempt from the typed attempt objects the record holds per
criticism call, not from attack edges alone."

R18 (process): "critic model as configured on main's launch config; at
most 3 concurrent calls on the key".

R19 (process): "Green cycle_soak.py on the launch config before any live
launch; detached launch; snapshot loop armed."

R20 (artifact): "DELIVERABLES: PREREG.md (frozen, digest committed before
calls), the sealed defect key, raw records preserved, RESULTS.md with one
verdict per factor — BLIND BETTER / INFORMED BETTER / INCONCLUSIVE — and
the residue."

R21 (process): "An inconclusive result is recorded as one."

R22 (process): "The default critic exposure on main is NOT changed by
this tranche; the result goes to the operator as a decision with the
numbers."

R23 (process): "Read CLAUDE.md IN FULL (especially the laws of 2026-08-28
on judges, and 2026-09-03: success is progress over the no-harness
baseline)."

R24 (process): "Commit and push at every phase boundary."

## Standing constraints

C1: "OUT OF SCOPE: judge blinding (measured); changing any default; any
frozen surface; the batch critic renderer." — executor prompt, closing
paragraph.

C2: "if a cell needs a source edit, that is a finding, PARK it and stop"
— executor prompt, F1/F2 paragraph. A hard stop condition.

C3: "the key comes from the gitignored env file, asked for at the launch
step only, never committed, never echoed." — executor prompt, LIVE RUNS.

C4: "no model self-reported number enters any of them" — executor
prompt, MEASURES.

C5: "Base on main at or after 0f6bf2c854." — executor prompt.

C6: "LIVE RUNS, tokens are cheap" — executor prompt; and CLAUDE.md's
standing law "Tokens are cheap; the agent is not" (2026-08-08).

## Open questions (for dr-spec-change)

Q1: F1's "origin: seed / harness-minted / capability" — the record's
`Provenance` carries `role` and `school`, not a field named "origin".
Which recorded field(s) realise the operator's three origin values?

Q2: Does the criticism run as a full managed harness run per cell, or as
a controlled bench that puts the SAME fixed targets to the critic under
each cell? The prompt fixes the targets ("a fixed set of accepted
artifacts"), which a managed run cannot control, but also names
`cycle_soak.py`, detached launch and a snapshot loop, which are ladder
apparatus.

Q3: The record already measures the bare critic's objection rate at 1.0
on clean and 1.0 on corrupted items
(`experiments/results/court_calibration_v1_report.json`, via REVIEW.md
§2.5). M2 ("sound artifacts the critic attacks") may therefore be
saturated in exactly the way M3's sustain rate was in the prior tranche.
What does PREREG fix in advance for that case?

Q4: "the committed three-judge protocol" is written for scoring
CANDIDATE CONJECTURES against a specific seed question's criteria (1-5).
Criticism text is a different object. Which parts transfer unchanged and
which must be re-fixed for this tranche's arms, as that document's own
copy-header contemplates?

Q5: R16 asks that sample size be set from "M3's saturation numbers".
Which measured quantity is meant — the prior tranche's saturated sustain
rate (which carries no variance to power a calculation), or the
unwarranted/warranted criticism counts that P7 CORRECTED reports?

## Amendments

**A1 (2026-09-04, mid-turn operator message).** The operator supplied the
provider API key in the chat, before the launch step. Verbatim of the
non-secret part: "API key: <redacted — 40 chars, glm/Ollama Cloud
shape>". Disposition, per C3: written to
`experiments/2026-09-04-experiment-blind-critic/env` as
`OLLAMA_API_KEY=...`, mode 600; confirmed ignored by
`.gitignore:50 experiments/**/env` via `git check-ignore -v`; never
echoed to any output, log, artifact or commit. The key's value appears in
no committed file in this tranche.

## Map ids resolved (map preflight, per dr-drive-harness §4)

Read before designing, in this order:

| id | document | why it is in scope |
|---|---|---|
| `DR-INV-frozen-surfaces` | `docs/map/INV-frozen-surfaces.md` | read first, always (C1 puts frozen surfaces out of scope) |
| `DR-INV-seat-section-plugins` | `docs/map/INV-seat-section-plugins.md` | owns the brief-as-configuration interface the four cells are built from (R5) |
| `DR-REC-add-a-section-plugin` | `docs/map/REC-add-a-section-plugin.md` | the recipe R5 requires ("no code edit") |
| `DR-CON-criticism-source` | `docs/map/CON-criticism-source.md` | owns `rules/crit.py`: what the critic is handed and what it must never be handed |
| `DR-CON-warrants-and-attacks` | `docs/map/CON-warrants-and-attacks.md` | M3's chain: no warrant, no edge (R12, R17) |
| `DR-CON-discharge-channel` | `docs/map/CON-discharge-channel.md` | F2's "discharge history" (R3) |
| `DR-SEAM-packs-and-token-economy-x-rules` | `docs/map/SEAM-packs-and-token-economy-x-rules.md` | seam BEFORE the subsystems: which sections `rules/` supplies vs. which a plugin computes |
| `DR-CON-packs-and-token-economy` | `docs/map/CON-packs-and-token-economy.md` | M4's matched caps (R13) |
| `DR-INV-render-layout` | `docs/map/INV-render-layout.md` | where a layout may put a section |

No map document is missing for this work; nothing here proposes a map
change, because nothing here changes `src/`.
