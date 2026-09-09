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

## A1 — history really rendered (`include_refuted=true`, `refuted_n=3`)

Launched 08:04:53Z. Rig receipt:
`{"arm": "A1", "installed": true, "layout_id": "seat-pack.conjecturer.step1-a1"}`.
Qualification was a **3-second cache hit**, as `arm.sh`'s shared home is meant
to produce.

*(in flight)*
