# DELIVERY — STEP 1 live, brief variation against the no-harness baseline

Tranche: `experiments/2026-09-04-experiment-brief-variation-step1/`.
Sealed 2026-09-04 at `8f4410159`; **run 2026-09-09 at `d7c87473e`** on the
operator's "do it" (`REQUEST.md` §4). Narrative: `RESULTS.md`. Per-arm record:
`RUNLOG.md`. Gate: `SOAK_2026-09-09.md`.

## 1. Prediction by prediction

| # | registered prediction | outcome | evidence |
|---|---|---|---|
| **P1** | **No direction predicted** for A1 (history) vs the null arms | **Honoured — none was registered, and none is claimed now.** Observed: −0.803 of 15 length-adjusted (p=0.057), **inside** `d_noise` = 1.312 | RESULTS §2.5, §4 |
| **P2** | A3 scores **LOWER** than the null arms | **NOT SUPPORTED — and wrong in direction.** A3 scored **+1.105** length-adjusted (p=0.011), higher not lower — but **inside** `d_noise`, so the correct reading is *inconclusive*, not "A3 helped" | RESULTS §2.5 |
| **P3** | A1P and A2 within `d_noise` of A0 — i.e. **`d_noise` is small** | **FALSIFIED in substance.** Trivially true that they are within it (`d_noise` is defined from them), but `d_noise` = **1.312 of 15 is larger than both treatments**. The design cannot detect brief effects of the size these treatments produce | RESULTS §2.4 |
| **P4** | **At least one harness arm's mean does NOT beat B0's** on the length-adjusted figure | **CANNOT BE SCORED as registered** — that figure is undefined (zero length overlap). On every figure that IS defined, **no arm beat B0** (5.35-6.73 vs 14.75 raw; quintile-held −5.5) | RESULTS §2.6, §3 |
| **P5** | B0's candidates **LONGER** than any harness arm's | **CONFIRMED, decisively.** B0 mean 7,775.5 chars vs 346.8-381.0; ranges do not overlap at all (8.1× separation) | RESULTS §2.3, LENGTH_OVERLAP.txt |
| §3.2 clause | an accepted `code:python-prop` claim over 200 chars would make A2 a real treatment | **NOT TRIGGERED.** `dr.active-properties` rendered **zero bytes in every arm** | RESULTS §2.2 |
| §11 premise | if A1 and A3 are indistinguishable from the identical-brief arms, "the input interface materially changes outputs" is unsupported on this record | **Both treatments landed inside the noise floor.** The premise is **not supported on this record** — and the record cannot distinguish "the brief does not matter" from "this n cannot tell", which is why §3.3's control existed | RESULTS §2.5, §5.2 |

## 2. Requirement by requirement (REQUEST.md R1-R34)

| R | obligation | how it was met |
|---|---|---|
| R1 | form held, one brief parameter per arm | form fixed at `conjecturer.turn.v6` in every arm; `PROVE_ARMS.txt` re-measured on this head, byte-identical to the sealed output |
| R2 | B0 exists; verdicts on the length-adjusted figure | B0 ran (12 calls). The figure is undefined here, so **no verdict is stated** rather than one stated on a different figure |
| R3 | the 2026-09-03 law is the criterion | applied — and the honest finding is that this design cannot measure it (RESULTS §2.6) |
| R4 | four skills loaded | CLAUDE.md, `pinker-write-for-readers`, `dr-drive-harness` read this session; `.claude/skills/README.md` **does not exist** (recorded, not invented) |
| R5 | base at or after `33f92e88c7` | sealed at `8f4410159`; run at `d7c87473e`, amendment A1 |
| R6 | this directory | yes |
| R7 | commit per phase; snapshot loop armed | ~30 commits; snapshot loop ran through every arm |
| R8 | run the committed recipe, do not redesign | run as sealed. Three unsealed scripts were repaired where they could not execute their own design (`soak_arms.sh`, `resume.sh`, `arm.sh`); all sealed files still verify |
| R9-R10 | five arms, form fixed | A0, A1, A1P, A2, A3 + B0; form fixed |
| R11-R13 | blind quality primary; copied protocol; provenance omitted | 248 candidates, 3 judges, 0 failed; `{bid, text}` only, key set **read** to confirm; scores sealed and committed **before** the keymap opened |
| R14-R16 | length controlled structurally; verdict only on the adjusted figure; no prompt-level de-biasing | chars recorded per candidate; all three views reported; **the adjusted figure's absence is why no verdict is stated**; no judge prompt mentions length |
| R17-R18 | A1P added; decision rule pre-sealed | A1P ran; §7's rule was sealed 2026-09-04 and applied unchanged |
| R19 | amend and re-seal before any call | `PREREG_AMENDMENT_2026-09-09.md`, digest in `SEALED.txt`, committed before the first call |
| R20 | green soak on the launch config | `SOAK_2026-09-09.md`, five arms green on this head |
| R21 | model settings from the profile registry | the registry holds **no document** for this model on a fresh container; the harness disclosed `MODEL_PROFILE_MISSING` and proceeded with the configured settings (recorded as a condition of every arm) |
| R22 | ≤3 concurrent processes on the key | max 2 (one arm + B0), verified by process listing |
| R23 | detached launch | `setsid nohup ... & disown` throughout |
| R24 | monitor on progress and rc lines | `monitor.sh` plus watches on every driver log |
| R25 | key from the gitignored file, never committed, never echoed | mode 600, `git check-ignore` confirmed, untracked; the run home carries a credential **reference** only, verified by searching the whole home for the value |
| R26 | arms inside the restart window; continue, never relaunch | each arm 40-45 min; no arm was killed. The one relaunch (A3) was of an arm that had **made no provider call** and had no root to continue |
| R27 | the P3 stop shape is not an arm death | did not occur; all five arms stopped `budget_exhausted` |
| R28 | six measures | primary + length control computed; the four secondary measures **not computed**, stated as not done (RESULTS §5.5) |
| R29 | no self-reported number | none entered any metric |
| R30 | spend per arm, B0 as floor | RESULTS §2.1; B0 21,284 tokens against 417k-560k per arm |
| R31 | RESULTS.md in the stated order | predictions → numbers → verdict per arm → history recommendation → residue |
| R32 | a not-better arm is written up as failed | no admissible verdict exists, so no arm is labelled either way — and RESULTS §3 states plainly that on every defined figure every arm scores far below B0, rather than reporting a pass |
| R33 | change no default | none changed; the history recommendation is **NO CHANGE** and is a recommendation |
| R34 | final message shape | delivered in chat |

## 3. What the operator gets to decide

**Nothing is waiting on a decision to close this tranche.** Two things are
worth a decision when convenient:

1. **The history default.** The recommendation is NO CHANGE, on the rule sealed
   before any call. `SPEC.md` S10 of the history tranche still specifies ON;
   this experiment supplies the quality evidence that section recorded as
   blank, and it does not support ON.
2. **Whether to fix the comparison and re-run.** The law's question is still
   open. `PARKED.md` F5 carries the ready-to-send prompt for the instrument;
   the deeper fix is comparing like with like — the harness's composed answer
   against B0's answer, or B0's answers split into claims.

## 4. Scope

`src/`, `tests/` and `mini/` byte-untouched (`git diff origin/main..HEAD --
src/ tests/ mini/` is empty). No gate run: no product code changed. Findings
that were not fixed are parked as F1-F6 with ready-to-send prompts.
