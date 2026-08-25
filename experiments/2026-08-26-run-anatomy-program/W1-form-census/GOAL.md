# GOAL — W1, the form-filling census

Tranche directory: `experiments/2026-08-26-run-anatomy-program/W1-form-census/`
Route: `deepreason-orchestrator`. Window: W1 of the RUN ANATOMY PROGRAM
(registered in `../PROGRAM.md`).

## The one goal

**Measure what the provider models actually wrote into every typed form,
across every committed run root on main, and attribute P-C1 ARM H's
recorded invalidity to named field-level causes.**

This is a MEASUREMENT tranche, not a defect tranche. Nothing under `src/`
or `tests/` is touched. Every defect the census surfaces is PARKED with a
ready-to-send prompt; none is fixed here.

## Falsifiable success criterion

The tranche succeeds if and only if all five hold:

1. A machine-readable per-root table exists covering EVERY inventoried
   root, with one row per provider attempt carrying: contract id, seat,
   role, cycle, arrival validity, and — for invalid arrivals — the failing
   field pointer and a named failure code taken from the record's own
   `code` field, not from a taxonomy invented here.
2. A machine-readable aggregate table exists over the same rows.
3. Content classes are reported per field kind: enum-like fields
   (fabrication and escape-hatch use), free strings, numeric arrays.
4. Repair fights are reported as attempts consumed per contract against
   the manifest's own `contract_schema_repair_policy` grant, and the E42
   lossless-spelling class is counted separately before and after its
   2026-08-22 fix.
5. The P-C1 headline (ARM H 15/132 valid vs ARM S 23/54) is attributed to
   named field-level causes, with exemplar blobs quoted verbatim.

The tranche FAILS if any number is reported that cannot be re-derived by
running the committed instrument against the committed roots.

## Scope contract

- READ-ONLY on `src/` and `tests/`. Proven at the gate by
  `git diff --stat origin/main -- src tests` being empty.
- No committed run root is opened writable, and none is modified.
- W2 and W3 run concurrently. W1 writes ONLY this subdirectory and the
  program-level files it is assigned (`../PROGRAM.md`, `../inventory.py`,
  `../ROOT_INVENTORY.json`). No file outside those is touched.

## Map ids resolved (map preflight)

Read before designing, per CLAUDE.md and `dr-drive-harness` §4:

| id | why it is in scope |
|---|---|
| `DR-SEAM-llm-x-workflow` | read FIRST: the seam that owns provider attempts, contract validation, repair and decomposition — the census's whole substrate |
| `DR-SUB-llm` | wire contracts, repair, route firewall — where a form is defined and where arrival validity is decided |
| `DR-SUB-workflow` | the v6 transactional lifecycle objects the census joins on (`workflow-provider-attempt-v1`, `workflow-semantic-admission-v1`, `workflow-work-terminal-v1`, `workflow-contract-decomposition-transition-v1`) |
| `DR-SUB-harness` | `log.jsonl` and `blobs/` — the append-only record read here. **Frozen**; read-only in this tranche |
| `DR-CON-seats` | seat instance vs role: the census keys by seat, because signals and throttling are seat-keyed |
| `DR-CON-run-identity` | root naming, retirement prefixes, and which directories are roots at all |
| `DR-INV-frozen-surfaces` | read before designing: three of the four object families above sit on frozen surfaces, which is why this tranche only reads them |

No map document is modified: nothing in this tranche changes code, so
nothing here may advance a `Verified-at:` stamp.

## The E42 join hazard, recorded before it can be repeated

`docs/ERRATA.md` E42 records a census that got causation backwards by
joining on the convenient key: `attempt_trace.diagnostic_ref` is written by
`workflow/repair_transaction.py::_terminalize_invalid` as
`trace_ref or next_diagnostic_ref`, so on a REPAIR attempt it names the
diagnostic derived AFTER the patch was applied — attempt N's response
scored against attempt N+1's authority.

This census therefore joins an attempt to its failure through
`workflow-semantic-admission-v1.provider_attempt_ref`, whose
`diagnostic_refs` are the diagnostics derived from THAT attempt, and never
through `attempt_trace.diagnostic_ref`. The instrument carries this as a
comment at the join site so the constraint cannot be edited away silently.

## What this tranche will NOT do

- Not fix anything. Not the P-C1 death, not any spelling class, not any
  fabrication site.
- Not judge whether a criticism was correct, a judge fair, or a conjecture
  good. That is W2/W3 territory and a judgment, not a form measurement.
- Not run the harness. No live call is made; the record is already written.
