# Validation for: "the neural embedder installs automatically — no run silently measures with the hash fallback again"

Tranche base: `d52c739ff`. Every output below is pasted from a real run
on this container.

## Acceptance checks

**S1 (R1, R2) — fastembed is a core dependency; `[embed]` survives as an
empty alias.**

    $ python -c "...tomllib...assert fastembed in dependencies; assert embed == []..."
    ok
    $ python -c "import fastembed; print(fastembed.__version__)"
    fastembed 0.8.0

Stronger evidence than this check asks for, recorded at CHECKLIST step 3:
fastembed was UNINSTALLED first (`ModuleNotFoundError`), then a plain
`pip install -e .` brought it back. : **PASS**

**S2 (R3) — HashingEmbedder and the `EMBEDDER_MODEL=None` escape are
untouched.** The whole diff to `llm/embedder.py` over the tranche is the
`EmbedderUnavailable` message and its comment — no line of
`class HashingEmbedder` moved:

    +            # fastembed is a CORE dependency: reaching this branch means the
    +            # environment was not installed from pyproject.toml, so the fix
    +            # names the install, not an extra to add.
    -                f"fastembed not installed (pip install 'deepreason[embed]'): {e}"
    +                f"fastembed not importable — reinstall the package "
    +                f"(pip install -e . / pip install deepreason): {e}"

    $ git diff d52c739ff..HEAD -- src/deepreason/config.py | grep "^[-+].*EMBEDDER_MODEL:"
    (default line unchanged)

: **PASS**

**S3 (R4) — the warm-up step exists and reports the typed fingerprint.**

    $ deepreason embedder-warmup --model nomic-ai/nomic-embed-text-v1.5
    keys ok: True
    (stderr) embedder-warmup: initializing nomic-ai/nomic-embed-text-v1.5
      (~523 MB of ONNX weights on first use, cached at
      /tmp/fastembed_cache); this is a one-time cost per cache, not per run ...
    (stderr) embedder-warmup: ready in 2.7s

Doctor's readiness block carries `"warmup_command": "deepreason
embedder-warmup"` (CHECKLIST step 7, direct call pasted there, which also
showed `dependency_available: true` / `fallback_active: false` where the
same call returned false/true before step 2). : **PASS**

**S4 (R5) — the disk cost is documented where costs are documented.**

    $ grep -c "fastembed_cache" CLAUDE.md src/deepreason/config.py
    CLAUDE.md:1
    src/deepreason/config.py:1

: **PASS**

**S5 (R6, R7) — the threshold verdict is recorded and the false comment
is corrected.** SPEC.md's "S3 THRESHOLD TRUTH" section is the R6
deliverable and states the verdict (NEITHER branch fires; every shipped
absolute distance threshold is `None`).

    $ grep -c "deepreason\[embed\]\|atlas radii" src/deepreason/config.py
    0

: **PASS**

**S6 (R8) — the fallback is loud where operators look.**

    $ deepreason results experiments/2026-08-12-live-grounded-extension-expansion/run
    ## Measurement instrument
      embedder (the model that turned this run's text into vectors, so its
      novelty, near-duplicate and school-distance readings are on that
      model's scale): hashing (fallback) — this run was configured for
      nomic-ai/nomic-embed-text-v1.5 but could not build it, so it
      measured with hashing-128 instead; distance readings are on the
      lexical scale, not the configured one

The run's terminal surface carries the same line on stderr from
`deepreason reason` (CHECKLIST steps 16 and 21). : **PASS**

**S7 (R9) — the `"error"` default is priced, not taken.**

    $ grep -n 'EMBEDDER_FAILURE_POLICY: Literal\["fallback", "error"\] = "fallback"' src/deepreason/config.py
    548:    EMBEDDER_FAILURE_POLICY: Literal["fallback", "error"] = "fallback"

Pricing line carried into DELIVERY.md. : **PASS**

**S8 (R10, R11) — preflight currency.**

    $ grep -rn "deepreason\[embed\]\|\.\[embed\]" --include=*.md --include=*.py --include=*.sh . \
        | grep -v .git | grep -v <this tranche> | grep -v <2026-08-13 PARKED ledger>
    ./experiments/2026-08-12-live-grounded-extension-expansion/RESULTS.md:346:
        'deepreason[embed]'): No module named 'fastembed'"]

ONE hit, and it must stay: it is a VERBATIM QUOTE of the historical log's
error message inside the evidence addendum this tranche wrote — the
`embedder-fallback` Measure at seq 2. Editing it to satisfy a grep would
falsify the record the segment exists to report. It instructs nobody; it
quotes what the run recorded. R10's own verification is pasted at
CHECKLIST step 10: the only `pip install -e .` line in the CLAUDE.md diff
is an addition, so both pre-existing install lines are byte-identical.
: **PASS**

**S9 (R14, R15) — regression tests.** `tests/test_embedder.py` 17 passed;
`tests/test_results_command.py` 26 passed. Mutation proofs pasted at
CHECKLIST step 4 (both new tests go red with fastembed uninstalled, and
the weight-fetch test FAILS rather than skips). : **PASS**

**S10 (R12, R13) — evidence honesty, append-only.**

    $ git diff --numstat experiments/2026-08-12-live-grounded-extension-expansion/RESULTS.md
    102     0     experiments/.../RESULTS.md

102 added, 0 removed. R13 scan verdict (no ERRATA entry; E32 unused) is
recorded inside that segment with its evidence. : **PASS**

**S11 (R16) — wheel smokes.** See "Packaging surface" below. : **PASS
(wheel_smoke) / PARKED (operational, pre-existing)**

**S12 (R18) — the map moved in the same commits.** `SUB-llm.md` gained a
Traps entry and a new mutation-proven check; `SUB-application.md` gained
the new entry points and an AST check that also guards the CLI/MCP parity
constraint; `SEAM-scheduler-x-workflow.md`'s census was corrected 13 → 14
with the reason written down. : **PASS**

**S13 (R17, R19, R20) — process.** Full gate below; commits and pushes at
every phase boundary; DELIVERY.md carries the R-by-R table. : **PASS**

## Full gate

    3702 passed, 6 skipped in 1068.34s (0:17:48)

**0 failed** : **PASS**

Run detached and ALONE on the box, after confirming no other
worker-spawning instrument was running. Nothing was weakened to reach
green: the only two assertions this tranche moved were STRENGTHENED (the
`EmbedderUnavailable` message test gained two checks) or EXTENDED by
exactly one key (the doctor readiness dict) — both predicted in advance,
at SPEC time and at CHECKLIST step 1 respectively. None of
`docs/AUDIT_BASELINES.md`'s known `-n 4` flakes fired, so no serial
re-run was owed.

## Record-behavior preservation

This change touched a READER of the append-only record
(`application/results.py` now derives the embedder from the log), so the
spot-check is owed and was run:

    defect-era (grounded-extension, carries embedder-fallback):
        verify_root -> violations=0  CLEAN
    known-good (live_run_v7, clean embedder stamp):
        verify_root -> violations=0  CLEAN

Both verdicts unchanged. The reader writes nothing — it opens roots
read-only — and no writer, digest or record format moved.

## Frozen-surface diff

    $ git diff --stat d52c739ff..HEAD -- \
        src/deepreason/capabilities/state.py src/deepreason/harness.py \
        src/deepreason/invariants.py src/deepreason/run_manifest.py \
        src/deepreason/qualification.py
    [empty]

**Empty**, as `tools/blast_radius.py` forecast at SPEC time
(`frozen_surface_verdict: CLEAR`, contact lists `[]`). : **PASS**

## Map

    docs_verify --audit:    0 finding(s) : PASS
    docs_verify --links:    0 dangling reference(s), 60 document(s) : PASS
    docs_verify --coverage: 6 seams swept, 16 without a Sweep: header,
                            2 finding(s) : PASS (neither finding is this
                            tranche's — see below)
    docs_verify (full):     see the re-run note below

**`--coverage`'s 2 findings are pre-existing and untouched**, proven
mechanically rather than asserted:

    $ git diff --stat d52c739ff..HEAD -- \
        docs/map/SEAM-periphery-x-verification.md docs/map/SEAM-schools-x-scratch.md \
        src/deepreason/amendment/apply.py src/deepreason/informal/trial.py
    [empty]

Both findings ("enforcement site not named":
`amendment/apply.py`, `informal/trial.py`) sit on seams this tranche
never opened, naming source files it never edited.

**The 16 "no Sweep: header" lines are advisory, not findings** (the
tool's own summary counts them separately). One deserves an explicit
decision rather than silence, because this tranche DID touch the file:
`SEAM-scheduler-x-workflow.md` is listed "add when next touched", and
this tranche touched it — but only to correct a coincidence census from
13 to 14 and explain why. DISMISSED with reason: authoring a `Sweep:`
header means specifying which enforcement sites the seam must sweep,
which is a design act about scheduler/workflow coupling that this
tranche has no evidence for and no requirement authorising. Inventing
one to clear an advisory line would put an unfounded claim into the map
— the opposite of what the header is for. Recorded here so the omission
is a decision, not an oversight.

**`--stale`: 4 documents, all dismissed, none this tranche's:**

- `SUB-calculus.md` (2 commits since `e901bb05`) — moved by the v2
  calculus program (`1a32fb193` P4 citable evidence, `3e4ea4031` Rung
  3c). DISMISSED: this tranche edits no calculus-owned file.
- `SUB-evidence.md` (1 commit) — same P4 tranche. DISMISSED, same reason.
- `SUB-scheduler.md` (4 commits) — Rung 1/Rung 2 of the calculus program.
  DISMISSED: this tranche edits no `scheduler/`-owned file; it only READS
  the Measure events the scheduler already stamped.
- `SUB-verification.md` (1 commit, `d127a6b59` control-barrier envelopes)
  — DISMISSED: predates this branch's first commit and touches no file
  here.

Proven by the same empty diff pasted above, which covers all four.

**New checks added by this change** — every one mutation-proven red then
green before being written down:

- `SUB-llm.md`: a check asserting `pyproject.toml`'s CORE dependency list
  carries fastembed AND that `[embed]` stays declared-and-empty AND that
  the warm-up command exists. Mutation: fastembed moved back into the
  extra → check red.
- `SUB-application.md`: an AST check over `_cmd_reason` asserting it
  reports the embedder, does NOT assign an `embedder` key to the durable
  payload (the CLI/MCP parity constraint the operational smoke caught),
  and contains no `Harness(` (the thin-client boundary). Mutation:
  decoration commented out → check red. Its first form was a `grep` that
  still matched the commented-out line — i.e. a check that could not
  fail — and was replaced for exactly that reason.

**Record observables added vs sweep probes**: NONE. This change writes
nothing to the record. `embedder_summary` READS `embedder` /
`embedder-fallback` Measure events the scheduler has stamped since before
this tranche, so no root's bytes move and no `root_sweep.py` probe is
owed. The reader is absence-tolerant by construction —
`NO_EMBEDDER_RECORD` is a declared `ABSENCE_REASONS` member with a test
against the two committed roots that predate the stamp.

## Packaging surface

The surface moved (`pyproject.toml` dependencies, one new CLI verb), so
the smokes are owed and were run.

    $ python scripts/wheel_smoke.py
    wheel smoke passed: isolated V6-only contents, clean imports, exact
    entry points, module parity, MCP registration, and exact MCP schemas
    rc=0

**No re-pin was needed, and that was verified from the source rather than
assumed** (SPEC S11): `REQUIRED_MODULES` pins wheel FILE PATHS, the only
METADATA assertion is the `Summary:` line, and the console-help pin
covers four REMOVED verbs plus the presence of `shallow` — a new
`Requires-Dist` and a new subcommand move none of them. The MCP surface
did not move, so the four-pin rule never engaged. : **PASS**

`wheel_operational_smoke.py` fails at its `reason` stage — **proven
pre-existing** by running it in a clean worktree at the unmodified base
`d52c739ff`, where it fails identically. PARKED as P1 with a
ready-to-send diagnosis prompt. It caught one real defect of this
tranche's along the way (a payload key breaking CLI/MCP result parity),
which is fixed; because the re-run died earlier, at `reason`, the smoke
never re-reached the comparison, so **that fix is not claimed to be
verified by this instrument** — it is guarded by the mutation-proven
`SUB-application.md` AST check instead.

## Requirement sweep

| R | demonstrated by |
|---|---|
| R1 core dependency | S1 — uninstall → `ModuleNotFoundError` → plain install → `fastembed 0.8.0` |
| R2 `[embed]` alias kept | S1 — `optional-dependencies['embed'] == []` |
| R3 HashingEmbedder untouched | S2 diff + `test_hashing_escape_survives_the_armed_neural_default` |
| R4 warm-up hook | S3 — `deepreason embedder-warmup`, visible stderr line, typed fingerprint; doctor names it |
| R5 disk cost documented | S4 — 523 MB and `/tmp/fastembed_cache` in CLAUDE.md and config.py |
| R6 threshold verdict recorded | S5 — SPEC.md "S3 THRESHOLD TRUTH": NEITHER branch; every shipped absolute threshold is `None` |
| R7 conditional branch | S5 — recalibration branch does NOT fire; `deepreason calibrate` correctly out of scope |
| R8 loud fallback, both surfaces | S6 — `results` "Measurement instrument" section; `reason` stderr line |
| R9 `"error"` recorded as an option | S7 — default unchanged; pricing line in DELIVERY.md |
| R10 plain install still works | S8 — grep proof: both CLAUDE.md install lines byte-identical |
| R11 docs updated | S8 — no manual `[embed]` instruction survives; the one hit is a quoted log line |
| R12 evidence honesty | S10 — RESULTS.md +102/−0 |
| R13 ERRATA scan | S10 — no entry warranted; `semantic_crosscheck.jsonl`'s distinct columns prove the neural claim true; E32 unused |
| R14 plain-install regression | S9 — never-skips test + weight-fetch test, both mutation-proven |
| R15 fallback path intact | S9 — `EMBEDDER_MODEL=None` → hashing, no measure; forced-unavailable still records |
| R16 wheel smokes | Packaging surface — `wheel_smoke` green, no re-pin owed (verified from source); operational parked as pre-existing |
| R17 gates | Full gate 3702 passed / 0 failed; docs_verify triaged to baseline |
| R18 map same-commit | S12 — three map documents, two new mutation-proven checks |
| R19 commit/push each boundary | 25 commits, each pushed with retry |
| R20 R-by-R delivery | this table, carried into DELIVERY.md with pasted proof |
| R21 finish as specified | STOP.md resolution; ceiling raised, no scope change |

Every R demonstrated. None deferred.

## Assumptions carried (operator may override)

- **A1** — the warm-up is a dedicated `deepreason embedder-warmup`
  command, not a side effect of `deepreason doctor`; doctor stays
  read-only and merely names it.
- **A2** — doctor does not probe whether the weights are already cached;
  a wrong "already warm" is worse than no claim.
- **A3** — the run's terminal surface is decorated at the print site, and
  (revised at CHECKLIST step 21, after the operational smoke caught it)
  on **stderr**, never as a key on stdout's JSON, because that JSON is
  the durable result contract MCP must return byte-identically.
- **A4** — R14's two halves are separate tests; only the weight-fetch
  half may skip, and only after proving fastembed is present.
- **A5** — no wheel-smoke re-pin (resolved from source, not assumed).
- **A6** — no ERRATA entry (resolved from the committed cross-check data).

## Verdict: PASS

Two caveats stated plainly rather than buried, neither of which blocks:

1. `wheel_operational_smoke.py` does not pass — and does not pass on the
   unmodified base either. Parked as P1, not fixed here, per the
   cross-routing law.
2. The full `docs_verify` re-run confirming 3-baseline-only is in flight
   at the time of writing; the earlier full run's 5 failures were triaged
   individually (3 baseline, 1 mine and fixed with its check re-run
   green, 1 load-induced and green idle). If the re-run shows anything
   beyond the 3 baseline failures, this verdict must be revisited.
