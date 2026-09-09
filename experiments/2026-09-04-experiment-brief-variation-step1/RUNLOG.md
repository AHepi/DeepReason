# RUNLOG — the arms as they ran, 2026-09-09

An honest ledger written arm by arm, from each root's own typed record via
`deepreason results`. Nothing here is a comparison and nothing here is a
verdict: those wait for the blind judging and `analyse_arms.py`, exactly as
`PREREG.md` §4-§7 register them. Model prose is not evidence; every number
below came from a record.

Head: `d7c87473e`. Gate: `SOAK_2026-09-09.md`, five arms green.
Question: `QUESTION.txt` (unchanged, sha matches the parent tranche's).
Shared home, one arm at a time, each root retired by `arm.sh` before the next
arm launches (run identity is deterministic, so two arms cannot hold the home
at once).

## Conditions that hold for every arm, recorded once

- **`MODEL_PROFILE_MISSING`, disclosed and proceeding.** No profile document
  describes `qwen3.5:397b` in this home, so nothing can say whether
  `reasoning='none'` leaves hidden reasoning on. The registry is home-only by
  the operator's 2026-09-01 decision ("nothing ships"), a fresh container
  therefore knows no model, and the all-configurations law makes this a
  disclosure rather than a refusal. The run sends exactly what `arm.sh`
  configured.
- **The measurement instrument is the FALLBACK, not the neural embedder.**
  Every arm reports `embedder: hashing (hashing-128)`, although
  `deepreason embedder-warmup` fetched the neural weights at session start and
  `fastembed` imports. Consequence, stated before any number: M2 (mean
  pairwise embedding distance) and the novelty/near-duplicate readings are on
  the hashing scale, not the neural one. Held CONSTANT across every arm rather
  than fixed mid-experiment — a between-arm comparison needs one scale more
  than it needs the better scale — and it touches no primary measure, since
  the blind judging that decides §4 and §7 reads text, not vectors.
- **No judges.** Solo configuration; adjudication did not run in any arm and
  judge calls are 0. Criticism still ran: the rounds below are the critic
  seat's, not a judge ensemble's.

## A0 — the control, rig inert

Launched 07:18:55Z, finished 08:04:42Z (45m47s, including the one full
qualification battery this home will ever pay).
Rig receipt: `{"arm": "A0", "installed": true, "layout_id": null}` — the
control is the shipped default and the rig registered nothing.

| | |
|---|---|
| state / stop_reason | **completed / `budget_exhausted`** — a clean typed terminal, not the P3 operational-failure shape |
| cycles | 4 of 4 |
| tokens | 417,053 of 600,000 |
| qualification | tier **full**, state ready (full battery, 300 cases, ~6m30s) |
| accepted / refuted / suspended | 104 / 2 / 0 |
| survivors | 50 |
| frontier | 50 artifacts on the seed problem |
| criticism rounds | 9 of 9 ran to the end, covering 50 artifacts |
| evidence states | 58 untested, 50 came through, 2 fell, 0 both-ways |
| provider health | 110 calls, **0 transport faults**, 0 returning nothing (critic 70, conjecturer 40) |
| verify_root | **yes, 0 violations** |
| amend/continue ready | yes |
| embedder | hashing (hashing-128) |

Root: `roots/A0-run-fe00609058e10605590206d51ab2b7a0`.

## B0 — the no-harness baseline: 12 independent calls, no brief at all

Ran 08:12-08:20Z alongside A1, not after it: only two processes call the
provider (`deepreason reason` and `baseline_b0.py`), inside R22's ceiling of
three, and the container's ~2-hour restart window is what binds six arms.

| | |
|---|---|
| calls | 12 of 12, **0 empty answers** (the reasoning-effort failure this model has on this endpoint did not occur) |
| characters per answer | mean **7,775.5**, median 7,693.5, range 6,853-8,873 |
| tokens | **21,284 total**, 1,774 per call (prompt 1,260, completion 20,024) |

**PREREG §8 P5 is already looking right**, and it is why the length control is
load-bearing rather than decorative: a B0 answer averages 7,776 characters
because one call answers the whole question, while a harness candidate is one
`claim` field. The panel's known appetite for length (Spearman +0.797 in the
parent tranche) would hand B0 the comparison on raw scores alone. No verdict
is stated on a raw figure; §5's length-adjusted figure decides.

**B0's spend is the comparison floor** (R30): 21,284 tokens for 12 answers,
against A0's 417,053 for one arm. That ratio is itself a result and RESULTS.md
reports it beside the quality numbers, because the law asks whether the
harness is materially better than the plain call — not whether it is better at
any price.

## A1 — history really rendered (`include_refuted=true`, `refuted_n=3`)

Launched 08:04:53Z. Rig receipt:
`{"arm": "A1", "installed": true, "layout_id": "seat-pack.conjecturer.step1-a1"}`.
Qualification was a **3-second cache hit**, as `arm.sh`'s shared home is meant
to produce. Finished 08:56:20Z.

| | | A0 for comparison |
|---|---|---|
| state / stop_reason | **completed / `budget_exhausted`** | same |
| cycles | 4 of 4 | 4 of 4 |
| tokens | **560,500** of 600,000 | 417,053 |
| accepted / refuted | 150 / 4 | 104 / 2 |
| survivors | 68 | 50 |
| criticism rounds | 12 of 12 | 9 of 9 |
| evidence states | 86 untested, 68 came through, 4 fell | 58 / 50 / 2 |
| verify_root | pending the retired-root read | yes, 0 violations |

Root: `roots/A1-run-fe00609058e10605590206d51ab2b7a0` (the directory name
repeats A0's because run identity is deterministic — same question, same
compiled configuration; the run IDS differ, `f0a233e2…` against `7fcfbcd9…`).

### The receipts: A1 really was shown history, and A0 really was not

From the runs' own typed section receipts (`verify_arms.py`), not from the
rig's environment variable:

    A0   dr.history.v1   never rendered   n= 0   bytes=    0   dropped=12
    A1   dr.history.v1   rendered         n= 4   bytes= 4228   dropped=14

So the contrast §3.1 corrected the operator's amendment 3 into — A1 (history
really rendered) against the identical-brief arms (history absent) — is real
in the record, and PREREG §3.1's claim that the SHIPPED DEFAULT SHOWS NO
HISTORY is now confirmed from a live run rather than from reading source.
`dr.active-properties` rendered in neither arm, which is §3.2 confirmed the
same way: there is nothing for A2 to widen.

**The dose is small, and saying so is not a hedge.** History rendered on 4 of
A1's 18 conjecturer dispatches, because the section has content only once
something has been refuted and A1 refuted 4 artifacts all run. Whatever the
judged numbers say, they are about a brief that carried refuted work on
roughly a fifth of its turns — not about a conjecturer steeped in its own
history. RESULTS.md states this beside the verdict rather than under it.

## A1P — history plugin removed entirely (an identical-brief arm)

Launched by the chain 08:56:38Z.

*(in flight)*
