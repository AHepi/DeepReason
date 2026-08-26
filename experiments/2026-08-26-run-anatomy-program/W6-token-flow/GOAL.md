# GOAL — W6, the token-flow map

Tranche directory: `experiments/2026-08-26-run-anatomy-program/W6-token-flow/`
Route: `deepreason-orchestrator`. Window: W6 of the RUN ANATOMY PROGRAM
(registered in `../PROGRAM.md`). Dimension: **D10 — run economy**, "where
the tokens went, by seat, contract, cycle and phase".

## The one goal

**Account for every provider token in every committed run root — by
purpose, by outcome, prompt-side and completion-side separately — and
reduce the P-C1 arms to one comparable number: cost per valid candidate.**

This is a MEASUREMENT tranche, not a defect tranche. Nothing under `src/`
or `tests/` is touched. Every defect the map surfaces is PARKED with a
ready-to-send prompt; none is fixed here.

## Falsifiable success criterion

The tranche succeeds if and only if all six hold:

1. A machine-readable per-call flow table exists covering EVERY provider
   attempt in EVERY inventoried root, carrying: root, log seq, cycle,
   role, seat, model, contract id, purpose class, repair flag, prompt
   tokens, completion tokens, work id, work-terminal status and
   `reason_code`, and semantic-admission outcome. Purpose and outcome
   classes are taken from the record's OWN fields (`contract_id`,
   `repair_scope`, `reason_code`, `status`, `outcome`) — no taxonomy is
   invented here.
2. Aggregate BY-PURPOSE and BY-OUTCOME tables exist over those rows,
   prompt-side and completion-side reported separately, per root and
   program-wide.
3. The three token instruments in each root — `run-status.json`
   `token_spend`, `TOKEN_ACCOUNTING.json` `inquiry_provider_tokens`, and
   the sum over `log.jsonl` — are reconciled root by root, with every
   disagreement classified and its residual attributed to named
   contracts. A disagreement is reported as a finding, never smoothed.
4. Pack anatomy is reported for a sample of at least 10 packs per
   priority root, spread across cycles: the prompt blob is split into
   preamble / output-contract schema / `## <section>` sections using the
   allocator's own emission format, and each part is sized with the
   allocator's own `approximate_tokens`. Growth across cycles is emitted
   as data, not prose.
5. The two-call (split-budget) protocol is answered from the record:
   how many attempts in how many roots carry a non-empty `split_leg`,
   what those legs cost, and what they recovered. If the answer is zero,
   that is the finding and it is stated as one.
6. The cross-arm ratio is computed for P-C1: tokens per valid candidate
   for ARM H and ARM S, from `TOKEN_ACCOUNTING.json` / `arm_h_scores.json`
   and `arm_s_merged.jsonl` / `arm_s_summary.json` respectively.

The tranche FAILS if any number is reported that cannot be re-derived by
running the committed instruments against the committed roots.

## Priority order (per the W6 prompt)

1. **P-C1 ARM H** — `experiments/2026-08-25-change-constructive-frontier/run`
   (run id `1950b3d0ee228113`, 292 attempts, 702 789 tokens). It lost a
   33x race; its budget gets a line-item post-mortem.
2. **P-R1** — `experiments/2026-08-25-poietics-program/run`
   (run id `1b31f0065687bd24`, 163 attempts, 521 838 tokens), the
   committed attempt after three refused/failed launches.
3. The remaining 52 roots, for the program-wide tables.

## Scope contract

- READ-ONLY on `src/` and `tests/`. Proven at the gate by
  `git diff --stat origin/main -- src tests` being empty.
- No committed run root is opened writable, and none is modified. Roots
  are read with plain file reads only.
- W4 and W5 run concurrently. W6 writes ONLY this subdirectory. It does
  NOT touch `../PROGRAM.md`, `../inventory.py`, or `../ROOT_INVENTORY.json`
  (W1's files this round); it CONSUMES `ROOT_INVENTORY.json` read-only.

## Map ids resolved (map preflight)

Read before designing, per CLAUDE.md and `dr-drive-harness` §4:

| id | why it is in scope |
|---|---|
| `DR-CON-packs-and-token-economy` | read FIRST: owns pack construction, section allocation and the budget meter — the whole substrate of this window. States that `render_conj_pack` has 17 section slots, `render_crit_pack` 13, and that `render_batch_crit_pack` is NOT on the IR, which bounds what pack anatomy can be measured on |
| `DR-SUB-llm` | `budget.py` `TokenMeter.reserve` / `Reservation.settle`, `adapter.py` prompt assembly, `split.py` — where a token is metered and where a call is split |
| `DR-SUB-workflow` | the v6 objects the flow table joins on: `workflow-provider-attempt-v1` (exact prompt/completion split), `workflow-work-terminal-v1` (`status`, `reason_code`), `workflow-semantic-admission-v1` (`outcome`), `workflow-token-reservation-v2` |
| `DR-SUB-harness` | `log.jsonl` and `blobs/` — the append-only record read here. **Frozen**; read-only in this tranche |
| `DR-SUB-scheduler` | cycles and budgets — the cycle axis the flow table bins on |
| `DR-CON-seats` | seat instance vs role: the flow table keys by seat, not role alone |
| `DR-CON-run-identity` | which directories are roots at all, and the retirement prefixes |
| `DR-INV-frozen-surfaces` | read before designing: the record formats this window reads are frozen, which is why this window only reads them |

## What this window will NOT do

- It will not fix the metering disagreements it finds. They become
  PARKED prompts.
- It will not report a pack section that the allocator dropped. A
  dropped section leaves no header and no placeholder in the rendered
  prompt (`DR-CON-packs-and-token-economy`, "NO SILENT CAPS"), so what
  the blob does not carry cannot be recovered from the blob. Absence is
  reported as absence.
- It will not treat model prose as evidence.
