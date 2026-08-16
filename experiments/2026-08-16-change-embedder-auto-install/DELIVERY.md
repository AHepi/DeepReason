# Delivered: "the neural embedder installs automatically — no run silently measures with the hash fallback again"

Branch: `claude/embedder-auto-install-239s5x` @ `5d86ddeb3` (pushed,
tree clean, head matches origin).

## What changed

`fastembed` moved out of the optional `deepreason[embed]` extra and into
`pyproject.toml`'s core dependency list, so the plain `pip install -e .`
that every container preflight already runs now arms the neural embedder
that `config.EMBEDDER_MODEL` has named all along. The `[embed]` group
stays declared as an empty alias, so the committed ladders and handovers
that say `pip install 'deepreason[embed]'` keep resolving instead of
erroring.

A new `deepreason embedder-warmup` command pays the ~523 MB ONNX weight
fetch in the setup phase behind a visible progress line and prints the
fingerprint the run will stamp on its log; `deepreason doctor`'s existing
embedder-readiness block now names that command. The cache location is
derived the way fastembed derives it rather than hardcoded, because on a
container it lands in the system temp directory — `/tmp` — which a
rollback wipes. `CLAUDE.md`'s environment section and `config.py`'s
`EMBEDDER_MODEL` comment record the cost and the location.

Because a fallback can still happen on a genuinely offline machine, it is
now loud where operators look. `deepreason results` gained a
"Measurement instrument" section that reads
`hashing (fallback) — this run was configured for
nomic-ai/nomic-embed-text-v1.5 but could not build it, so it measured
with hashing-128 instead`, and `deepreason reason` prints the same line
to stderr when a run ends. Both derive from Measure events the scheduler
was already stamping; nothing new is written to the record, and
`run-result.json` is untouched.

`HashingEmbedder` and the deliberate `EMBEDDER_MODEL=None` escape are
unchanged. The grounded-extension tranche's `RESULTS.md` gained a dated
addendum stating that its runs measured with `hashing-128`, and
`llm/embedder.py`'s now-misleading error message stopped pointing at an
extra that installs nothing.

## The threshold question, answered from the record

The scope item that could have doubled this tranche resolves to
**neither branch**. Every shipped absolute distance threshold is `None`:
`NEAR_DUP_EPS`, `RESEED_DIST_MIN`, and the scratchpad's
`similarity_threshold`. Their consumer confirms `None` means off
(`rules/guards/anti_relapse.py`: its stages "run ONLY when a
RelapseDomain, an embedder, AND a calibrated `NEAR_DUP_EPS` are all"
present), and no "atlas radii" knob exists in config at all. The two
convergence knobs that DO ship armed are embedder-safe by construction —
`RESEED_RATIO_MAX` is a ratio of distances within one space, and E0.1's
M4 already measured it under a neural embedder without it firing;
`GATE_ORBIT_MIN` is a count of gate blocks, not a distance.

So live runs were **not** applying neural-calibrated numbers to hashing
geometry — there were none to apply. `deepreason calibrate` stayed out of
scope, and one config comment that implied otherwise was corrected.

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "move fastembed ... into the core dependency list" | done | `f6a9…` step 2; VALIDATION S1 — uninstall → `ModuleNotFoundError` → plain install → `fastembed 0.8.0` |
| R2 | "Keep the [embed] extra as an empty/alias group" | done | step 2; VALIDATION S1 — `optional-dependencies['embed'] == []` |
| R3 | "HashingEmbedder stays ... untouched" | done | VALIDATION S2 — whole `embedder.py` diff is one message; `test_hashing_escape_survives_the_armed_neural_default` |
| R4 | "Add an explicit warm-up hook ... visible progress line, never silently inside cycle 1" | done-with-assumption **A1, A2** | steps 6-8; VALIDATION S3 |
| R5 | "Document the disk cost where the environment section documents costs" | done | steps 9-10; VALIDATION S4 — 523 MB + `/tmp/fastembed_cache` in CLAUDE.md and config.py |
| R6 | "Establish ... which embedder the SHIPPED thresholds were calibrated against, and record the verdict in SPEC.md" | done | SPEC.md "S3 THRESHOLD TRUTH"; VALIDATION S5 |
| R7 | "if neural — ... if hashing — a `deepreason calibrate` recalibration step is IN scope" | done (**neither antecedent holds**) | SPEC.md S3 — all shipped absolute thresholds are `None`; recalibration correctly not performed |
| R8 | "make the fallback loud ... `deepreason results` and the run's terminal summary" | done-with-assumption **A3** | steps 13-17, 21; VALIDATION S6 |
| R9 | "Flipping the default to 'error' is NOT granted — record it as an option ... with one line of pricing" | done | default unchanged (VALIDATION S7); pricing line below |
| R10 | "CLAUDE.md's environment/build lines ... keep working unchanged by S1 — verify by grep and say so" | done | step 10 — the only `pip install -e .` line in the diff is an addition; both pre-existing lines byte-identical |
| R11 | "update any doc that instructs installing [embed] manually" | done | VALIDATION S8 — no instruction survives; the one grep hit is a quoted log line |
| R12 | "the grounded-extension tranche's RESULTS.md gains a dated segment" | done | step 19; VALIDATION S10 — +102/−0, append-only |
| R13 | "Check PATROL_DETERMINISM_REPORT.md and any document claiming 'embeddings corroborate'" | done | scan recorded in that segment; **no ERRATA warranted** — see Errata below |
| R14 | "plain install imports fastembed and build_embedder returns NeuralEmbedder" | done-with-assumption **A4** | step 4; VALIDATION S9 — mutation-proven, and the packaging half never skips |
| R15 | "the fallback path still works with EMBEDDER_MODEL=None; the embedder-fallback measure still records" | done | step 4; VALIDATION S9 |
| R16 | "Wheel smokes: if the required-modules pin covers dependencies, re-pin in the SAME commit" | done-with-assumption **A5** | VALIDATION "Packaging surface" — `wheel_smoke` green; pins are file paths, not dependencies, so no re-pin was owed |
| R17 | "ring while iterating; full gate at the boundary; docs_verify full" | done | full gate **3702 passed, 6 skipped, 0 failed**; docs_verify **3 failed, all baseline** |
| R18 | "Map moves in the same commits" | done | 3 map documents, 2 new mutation-proven checks — see Map delta |
| R19 | "Commit and push every phase boundary (retry ...)" | done | 27 commits, each pushed |
| R20 | "Deliver R-by-R with pasted PROOF" | done | this table + the closing line |
| R21 (Amendment 1) | "Continue from where you left off." | done | STOP.md resolution — ceiling raised, no scope change |

No requirement is `not-done`, and none is deferred.

## R9's pricing line, as requested

Flipping `EMBEDDER_FAILURE_POLICY` to `"error"` would stop any run that
cannot build the neural backend *before its first model call*: it buys
"no run ever measures with a geometry it did not ask for", and costs "a
genuinely offline container can no longer run at all". It is available
per-run today without changing the shipped default.

## Assumptions the operator may override

- **A1** — the warm-up is a dedicated `deepreason embedder-warmup`
  command rather than a side effect of `deepreason doctor`; doctor stays
  a read-only preflight and merely names it.
- **A2** — doctor does not probe whether weights are already cached; a
  confidently wrong "already warm" is worse than no claim, and the
  warm-up is idempotent (2.7 s when cached).
- **A3** — the run's terminal report prints the embedder to **stderr**,
  not as a field on stdout's JSON. Revised mid-tranche: the first version
  did add a field, and the operational wheel smoke caught that this broke
  an exactness guarantee between the command's output and the same result
  fetched over MCP.
- **A4** — R14's two halves are separate tests; only the weight-fetch
  half may skip, and only after proving fastembed itself is present.
- **A5** — no wheel-smoke re-pin, resolved by reading the smoke's source
  rather than assuming.
- **A6** — no ERRATA entry, resolved from the committed cross-check data.

## Map delta

    changed: docs/map/SUB-llm.md, docs/map/SUB-application.md,
             docs/map/SEAM-scheduler-x-workflow.md
    created: none
    new checks: 2 (both mutation-proven red, then green, before being
             written down)
    left stale: SUB-calculus.md, SUB-evidence.md, SUB-scheduler.md,
             SUB-verification.md — all four moved by OTHER tranches (the
             v2 calculus program and the control-barrier work); proven
             untouched here by an empty diff over exactly those files.
             Also SEAM-scheduler-x-workflow.md still has no `Sweep:`
             header: authoring one means specifying which enforcement
             sites the seam must sweep, a design claim about
             scheduler/workflow coupling this tranche has no evidence for
             and no requirement authorising. Dismissed deliberately, not
             overlooked.

`SUB-llm.md` gained a Traps entry naming the grounded-extension run and a
check asserting fastembed stays in the CORE dependency list, `[embed]`
stays declared-and-empty, and the warm-up command exists.
`SUB-application.md` gained the new reader entry points and an AST check
that guards two boundaries at once — that the printed terminal payload
reports the embedder, and that it must NOT become a key on the durable
payload. `SEAM-scheduler-x-workflow.md`'s coincidence census moved 13 →
14 with the reason recorded (a docstring here names the scheduler in a
file that already imported `workflow`; prose, not new coupling).

## Errata

**errata: none.** The R13 scan found one document claiming "embeddings
corroborate" (`docs/HANDOVER_MONITOR_2026-08-10.md:100`), pointing at
`PATROL_DETERMINISM_REPORT.md` — and that claim is TRUE with committed
evidence: the report states it ran two embedders, one neural, and its raw
output `semantic_crosscheck.jsonl` carries 9,277 rows with DISTINCT
`hashing_cosine` and `neural_cosine` values per row. That was an offline
cross-check script with the extra installed, not a live harness run, so
the live-run fallback does not touch it. Ledger tail checked; the next
free number, E32, stays unused.

## Parked (not done, not promised)

**P1 — `wheel_operational_smoke.py` fails at its `reason` stage on an
UNMODIFIED tree.** Proven pre-existing by running it in a clean worktree
at `d52c739ff`, which fails identically; flaky across 3 observations
(pass, fail, fail). It is a FINDING rather than baseline, because
`docs/AUDIT_BASELINES.md` excuses only failures naming the MCP schema sha
or tool-set pins. `AUDIT_BASELINES.md` was deliberately left unedited —
recording an undiagnosed failure there would turn a finding into an
expectation. Full ready-to-send prompt in `PARKED.md`.

**P2 — `experiments/jolt_architecture_2026-07-16/run` cannot be opened by
any Harness-based reader** (`UnsupportedRunManifestVersionError`, schema
version 3). Probably the 2026-08-14 "old runs owe the future nothing" law
working as intended, recorded only so the next person does not spend a
diagnosis on it. Prompt in `PARKED.md`, to be used only if the operator
decides pre-v6 roots should stay readable.

**recommended next: P1.** It is the one instrument in the repo that
builds the wheel and drives a real run through it, no test gate runs it,
and it is currently unable to give a verdict on anything — including on
this tranche's own CLI/MCP parity fix, which is why that fix is guarded
by a map check instead of by the smoke.

## Honest overruns

- The line estimate missed by roughly 2x, twice: SPEC said ~301, the
  phase-B gate measured 541, the tranche closed near 580. The overrun was
  in test docstrings and comments, not in behaviour surface. Recorded in
  STOP.md rather than smoothed over.
- Two defects of mine were caught by instruments rather than by the test
  ring: constructing a `Harness` inside a CLI command (caught by the map
  check), and adding a payload key that broke CLI/MCP result parity
  (caught by the operational wheel smoke). Both fixed without weakening
  any assertion.
- I killed a healthy 15-minute documentation-gate run after misreading
  multiprocessing worker timings as restarts. Cost time only; the gate
  was re-run to completion.
