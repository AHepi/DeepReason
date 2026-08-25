# SPEC — the Poietics program, and P-R1 the explanation run

Traces to REQUEST.md R1-R17 and C1-C6. Every acceptance check below is a
command or a typed artifact, never a reading.

Map ids: `DR-SUB-evidence`, `DR-CON-run-identity`, `DR-SUB-scheduler`,
`DR-SUB-manifest` (FROZEN), `DR-CON-seats`, `DR-SUB-llm`. Frozen-surface
check ran before design (REQUEST.md header): the only source edit this
tranche makes is inside `scripts/cycle_soak.py`, outside all five surfaces.

## Order of work, and one honest note about it

Phases ran REQUEST → (offline design probes) → SPEC. The probes came first
deliberately: every assumption below is MEASURED rather than guessed — the
model ids against the live catalogue, the manifest against the compiler, the
criteria against a discrimination control. `dr-change-orchestrator` puts SPEC
before any tree change, and the config, builder and preflight scripts existed
before this file did. Recording that here rather than back-dating the order.
No `src/` or `tests/` file was touched by any probe (C3).

## S1 — the record, curated (R5, R6, R7)  ✅ DELIVERED

Twelve of the bundle's 118 files under `record/`, byte-identical to the
operator's zip. Provenance header in the tranche README quotes both of the
bundle README's cautions and §14's own statement of the mechanism.

**Acceptance:** `sha256sum` over `record/` matches the manifest printed in
`README.md` (12/12 OK, pasted in the commit). `git show --stat` shows no file
outside `experiments/2026-08-25-poietics-program/`.

## S2 — PROGRAM.md registering three runs (R8, R9)

P-R1 (explanation) is RUN here. P-R2 (premises) and P-R3 (succession trial)
are REGISTERED ONLY — questions, dossiers, milestones and preconditions
written down, nothing launched. One tranche, one run (C2).

**Acceptance:** `PROGRAM.md` exists; each of P-R1/P-R2/P-R3 carries a
question, a dossier, registered milestones, and an explicit RUN/REGISTERED
status line; P-R2 and P-R3 say what must be true before they may launch.

## S3 — P-R1 design frozen in PREREG before any API call (R10, C5)

### S3a — question (R10a)

`build_manifest_pr1.py::QUESTION` is R10a verbatim, including the em-dashes.
One byte of drift mints a different run id and a different dossier
`problem_ref`.

**Acceptance:** a diff of `QUESTION` against REQUEST.md R10a's quoted text
is empty.

### S3b — dossier (R10b)

All twelve committed files are admitted through
`admission.attach.admit_attachment_paths` — the one shared admission path —
and bound at seed, not at an amendment. Measured: **12 sources, 623 blocks,
0 refusals**, no `--allow-partial` needed. Blocks are what makes
quoted-evidence citability work: a critic cites a block and
`check_candidate_citations` byte-checks it.

Assumption A-1, recorded: R10b says "the six committed documents". The
committed set is twelve FILES which form six DOCUMENTS — `README.md`, four
`report/` sections, and `data/` as one seven-file evidence bundle. All twelve
files are bound; 12 is inside the policy's `maximum_sources=16`.

**Acceptance:** `build_manifest_pr1.py` reports `dossier_sources: 12`,
`dossier_blocks: 623`, and the run root binds `evidence-dossier.json`.

### S3c — configuration (R10c as amended by R17)

Cross-family, everything on. Measured against the LIVE Ollama Cloud
catalogue (`https://ollama.com/v1/models`, which answers unauthenticated —
so Q6 cost no operator time and no API key): all four ids are present.

| seat | model | family |
|---|---|---|
| conjecturer | `deepseek-v4-pro:0813` | deepseek |
| argumentative_critic | `kimi-k3` | kimi |
| judge seat 1 | `qwen3.5:397b` | qwen |
| judge seat 2 | `glm-5.2` | glm |
| the other seven roles | `glm-5.2` | glm |

Assumption A-2, recorded: A3 named "judge one" and "judge 3" and skipped
judge 2. Built as a TWO-seat ensemble. This is the smallest reading that
compiles and it satisfies the gate exactly —
`firewall.py::require_cross_family_judge_ensemble` demands ≥2 seats AND ≥2
families (lines 389-392). A third seat would need a model the operator did
not name, and inventing one is not available to this workflow.

Assumption A-3, recorded: A3 named four seats; the remaining seven canonical
roles stay on `glm-5.2` — the profile R10c originally named and the one this
repository has the most live evidence for. `Config.roles` defaults to `{}`,
so silence would give them zero routes.

"Everything on" is written out rather than inherited, because several fields
ship the other way: `JUDGE_SEATS_ENABLED`, `ADJUDICATION_STATUS_AUTHORITY_
ENABLED`, `SCHOOL_SEATS_ENABLED` true; `ENGAGED_CRITICISM_AUTHORITY:
defended_trial`; `LEGACY_CRITICISM_ENABLED` false so the engaged engine runs;
`RESEARCH_BACKEND: agent`; inquiry policy engaged with attached evidence,
simulation, research and config referee all on.

`ARGUMENTATIVE_AUTHORITY` stays `observe_only`. Declaring it
`trial_required` trips `CALIBRATION_RECEIPT_REQUIRED` for any text workload
against a verifier that is a permanent stub. Status-changing authority
reaches this run through the engaged criticism engine instead.

Two compile arguments move against every committed predecessor:
`single_model=None` (four models across eleven roles; `single_model`
collapses the matrix and does not consult the others) and
`rubric_policy="require_cross_family"` (the judge ensemble is the point).
`toolchains=(engaged_local_simulation_toolchain(),)` is forced: an enabled
simulation policy must bind exactly one frozen toolchain.

Budget (R10c, "bounded budget stated in PREREG"; "cycles sized by the
attempt-4 precedent (8+)"): **cycles 12, token budget 3 000 000.** Sized so
the CYCLE budget binds first, as it did in attempt-4 — a token-bound stop
truncates mid-cycle, a cycle-bound stop does not. attempt-4 spent 371 169
tokens over 8 cycles solo with no dossier and no judges; P-R1 adds dossier
packs, a judge ensemble and school seats, so per-cycle cost is expected
several times higher.

**Acceptance:** `build_manifest_pr1.py` compiles with **zero** compile
notices; the bound `run-manifest.json` shows `rubric_policy:
require_cross_family` and the seat matrix above.

### S3d — registered milestones (R10d)

Typed outcomes only (C1). Registered in PREREG.md §5 before launch, with
stochastic extras named as such.

**Acceptance:** PREREG.md §5 lists each milestone with the typed artifact
and field that decides it, and marks which are stochastic.

## S4 — soak law (R11)

`scripts/cycle_soak.py` gains a `pr1` case reading THIS tranche's
`run-config.yaml` and importing QUESTION/CRITERIA/COMPILED_AT from
`build_manifest_pr1.py`. Run it; paste exit 0. Only then ask for the key
(C6).

Assumption A-4, recorded: `_case_symbols` hard-codes the reach-rich
directory on `sys.path`, so a builder living in another tranche cannot be
imported. The case table therefore gains a `builder_dir` field defaulting to
the existing directory. This is part of "extend the case table" (R11) — the
table cannot hold this case without it — and it is additive: both existing
cases keep their exact behaviour.

**Acceptance:** `python -u scripts/cycle_soak.py --case pr1` exits 0, output
pasted into the tranche. `python -u scripts/cycle_soak.py --case epoch3`
still exits 0 or 3 unchanged. `git diff --stat` shows no `src/` or `tests/`
file touched (R15, C3).

## S5 — launch (R12, R13, R14)

Detached (`setsid nohup ./pr1_run.sh & disown`), snapshot loop armed,
monitor on the newest root's `progress.jsonl` and the driver log's `rc=`
lines.

**Success (R13):** typed terminal; `verify_root` 0 violations; the
registered milestones present. Then commit the root and write RESULTS.md
naming what the accepted-and-surviving conjectures actually claim, with the
residue — "accepted does not mean true", doubly so for an explanation of
someone else's evidence.

**Operational death (R14):** park the cause for the soak's ledger and STOP.
One repeat pre-authorized.

## Stop conditions

Beyond the orchestrator's standing list: any need to touch `src/` or
`tests/` (C3) is a STOP, not a workaround. A model id that fails at qualify
is a STOP with the typed refusal quoted, not a substitution — the seats are
the operator's, verbatim.

## Budget

Diff outside `experiments/2026-08-25-poietics-program/`: `scripts/
cycle_soak.py` only, one case row plus the `builder_dir` field it needs.
Zero files under `src/` or `tests/`.
