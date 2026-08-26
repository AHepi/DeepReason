# W1 — the form-filling census

Dimension **D2** of the RUN ANATOMY PROGRAM (`../PROGRAM.md`): what the
provider models actually wrote into every typed form, over every committed
run root on `main`.

Read-only. `src/` and `tests/` are untouched; no run root was modified.

## Read in this order

| file | what it is |
|---|---|
| `RESULTS.md` | the findings, as a dated honest ledger, with the residue |
| `PARKED.md` | six findings as ready-to-send prompts. Nothing was fixed |
| `EXEMPLARS.md` | the blobs behind the numbers, quoted verbatim with paths |
| `AGGREGATE.md` | the aggregate tables |
| `PER_ROOT.md` | one row per root |
| `GOAL.md` | the tranche's bounded goal and its map preflight |

## Machine-readable output

| file | schema |
|---|---|
| `census/<root>.json` | `run-anatomy.form-census.root.v1` — one row per provider attempt |
| `CENSUS_PER_ROOT.json` | `run-anatomy.form-census.per-root.v1` |
| `CENSUS_AGGREGATE.json` | `run-anatomy.form-census.aggregate.v1` |
| `PC1_HEADLINE.json` | `run-anatomy.pc1-headline.v1` |
| `COERCION_PROBE.json` | `run-anatomy.coercion-probe.v1` |
| `MESSAGE_CODE_TABLE.json` | `run-anatomy.message-code-table.v1` |

## Re-derive everything

Every number in `RESULTS.md` comes out of these, in this order. The committed
outputs are byte-identical to a fresh run:

    python3 ../inventory.py
    python3 census.py
    python3 aggregate.py
    python3 pc1_headline.py
    python3 coercion_probe.py
    python3 exemplars.py

## Two join hazards this census had to survive

Both are the same mistake — joining on the convenient key instead of the
frozen one — and `docs/ERRATA.md` E42 is the recorded instance.

1. `attempt_trace[].diagnostic_ref` is written as
   `trace_ref or next_diagnostic_ref`, so on a repair attempt it names the
   diagnostic derived AFTER the patch. Join through
   `workflow-semantic-admission-v1.provider_attempt_ref` instead.
2. `attempt_trace[].attempt` is the index within that log record's own trace
   list and is 0 for every attempt in every committed root. The workflow
   attempt index the repair grant meters lives only on
   `workflow-provider-attempt-v1.attempt_index`.

And one that is not a join at all: read the model's answer in EVERY spelling
the record contains. Reading only the canonical `operations`/`path` patch
shape scored 398 convergent repairs as off-target — E42's exact false
finding, reproduced by this census before it was caught.
