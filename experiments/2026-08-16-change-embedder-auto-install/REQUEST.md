# Request: "the neural embedder installs automatically — no run silently measures with the hash fallback again"

Captured: 2026-08-16 from the operator's tranche-launch message (this
session, single message), which itself quotes an earlier operator
statement of 2026-08-13 as the standing AUTHORITY.

## Map preflight (resolved before any phase, per CLAUDE.md)

- `DR-SUB-llm` — owns `src/deepreason/llm/`, including
  `embedder.py::build_embedder`, `HashingEmbedder`, `NeuralEmbedder`,
  `EmbedderUnavailable`. Its "What can break" table already names
  "The embedding backend or its drift stamp" with test file
  `tests/test_embedder.py`. This is the covering document for the
  code change and moves in the same commit.
- `DR-SUB-scheduler` — stamps the embedder fingerprint on the log and
  records the `embedder-fallback` measure.
- `DR-SUB-scratch` — `scratch/similarity.py` calls `build_embedder`.
- `DR-SEAM-llm-x-rules` — mentions the embedder; read before touching
  either side.
- `docs/map/INV-frozen-surfaces.md` — read before designing. None of
  the five frozen surfaces (state digests, harness event application,
  replay-validation formats, manifest schemas, qualification subjects)
  is a packaging or default-dependency surface; confirmed in SPEC.md.
- No map document currently covers `pyproject.toml` packaging. That is
  a map gap, recorded here; whether it earns a document is decided in
  SPEC.md.

## Verbatim

The operator's tranche-launch message, in full:

> Change tranche: the neural embedder installs automatically — no run
> silently measures with the hash fallback again. Route through
> dr-change-orchestrator; the workflow's own stop conditions apply,
> nothing else stops.
>
> SETUP (fresh container): git fetch origin main && git checkout -B
> claude/embedder-auto-install-n38xqt origin/main; git merge-base
> --is-ancestor d52c739ff HEAD || re-fetch. pip install -e .
> --break-system-packages -q; pip install pytest pytest-xdist jsonschema
> --break-system-packages -q. Use `python -m pytest`, never bare pytest.
> Read CLAUDE.md in full; load dr-drive-harness, dr-explain-to-operator.
>
> AUTHORITY for REQUEST.md, operator verbatim (2026-08-13): "It found
> that hash embedding was used, not the actual embedder. That needs to be
> installed automatically." The mechanism (verified, cite in SPEC):
> config.py EMBEDDER_MODEL defaults to the neural model
> (nomic-ai/nomic-embed-text-v1.5, via fastembed), but fastembed lives in
> the optional dependency group `deepreason[embed]`; every container
> preflight runs plain `pip install -e .`, so NeuralEmbedder raises
> EmbedderUnavailable and EMBEDDER_FAILURE_POLICY="fallback" degrades
> every live run to HashingEmbedder with an `embedder-fallback` measure —
> typed, recorded, and read by nobody. The grounded-extension run and its
> continuation measured with hashing-128 (their logs' embedder Measure
> events are the proof).
>
> SCOPE, in order:
> S1 CORE DEPENDENCY: move fastembed from the [embed] extra into the core
>    dependency list in pyproject.toml so `pip install -e .` installs it.
>    Keep the [embed] extra as an empty/alias group so existing
>    'deepreason[embed]' instructions keep working. HashingEmbedder stays
>    (EMBEDDER_MODEL=None escape, controlled experiments — untouched).
> S2 WEIGHTS WARM-UP: first neural use fetches ~0.5 GB of ONNX weights.
>    Add an explicit warm-up hook where ladders already do setup work
>    (deepreason doctor, or a `deepreason embedder-warmup` step) so the
>    fetch happens in the setup phase with a visible progress line, never
>    silently inside cycle 1. Document the disk cost where the
>    environment section documents costs.
> S3 THRESHOLD TRUTH: the config's own comment says every distance
>    threshold (NEAR_DUP_EPS, RESEED_DIST_MIN, atlas radii) is
>    scale-specific per embedder. Establish from the committed record
>    (experiments/results/e01_embedder_recalibration_report.json) which
>    embedder the SHIPPED thresholds were calibrated against, and record
>    the verdict in SPEC.md: if neural — this tranche closes a real
>    mismatch (live runs were applying neural-calibrated thresholds to
>    hashing geometry) and say so; if hashing — a `deepreason calibrate`
>    recalibration step is IN scope before the neural default is
>    armed-by-install, with the new values committed and their derivation
>    pasted.
> S4 FALLBACK POLICY DECISION, recorded not assumed: with the dependency
>    now core, EmbedderUnavailable should be rare (truly offline
>    environments). Keep EMBEDDER_FAILURE_POLICY="fallback" as the
>    shipped default BUT make the fallback loud where operators look:
>    `deepreason results` and the run's terminal summary surface
>    "embedder: hashing (fallback)" so it can never again be a log line
>    nobody reads. Flipping the default to "error" is NOT granted —
>    record it as an option for the operator with one line of pricing.
> S5 PREFLIGHT CURRENCY: CLAUDE.md's environment/build lines and any
>    skill preflight naming the plain install keep working unchanged by
>    S1 — verify by grep and say so; update any doc that instructs
>    installing [embed] manually as the required step (it is now
>    automatic). Same-commit rule for every doc touched.
>
> EVIDENCE HONESTY (append, never edit): the grounded-extension tranche's
> RESULTS.md gains a dated segment stating its runs measured with
> hashing-128 under the S3 verdict's threshold regime, and what that does
> NOT change (LLM calls, judge verdicts, artifact statuses are
> embedder-independent; the affected instruments are novelty/dup/atlas
> distance measures). Check PATROL_DETERMINISM_REPORT.md and any document
> claiming "embeddings corroborate": if one asserts NEURAL embeddings
> were used where the record shows hashing, that is a docs/ERRATA.md
> entry (next free number — check the ledger tail); if the claim is
> embedder-agnostic, record the scan and move on.
>
> TESTS: regression — plain install imports fastembed and build_embedder
> returns NeuralEmbedder without EmbedderUnavailable (skip-marked only
> for genuinely offline CI, with the skip reason naming this tranche);
> the fallback path still works with EMBEDDER_MODEL=None; the
> embedder-fallback measure still records when forced. Wheel smokes: if
> the required-modules pin covers dependencies, re-pin in the SAME commit
> (four-pin rule if the MCP surface moves, which it should not).
>
> GATE: ring while iterating; full gate at the boundary; docs_verify full
> (baselines per docs/AUDIT_BASELINES.md — gate expectation is 0 failed).
> Embedder identity is recorded per-run; changing the default changes
> FUTURE runs only — cross-version replay proofs are retired (CLAUDE.md
> 2026-08-14 law). Map moves in the same commits (the doc covering
> llm/embedder.py). Commit and push every phase boundary (retry
> 2s/4s/8s/16s). Deliver R-by-R with pasted PROOF, closing with one line:
> what a fresh container now gets from `pip install -e .` alone, and
> which embedder the next live run will actually use.

## Requirements

R1 (behavior): "move fastembed from the [embed] extra into the core
dependency list in pyproject.toml so `pip install -e .` installs it."

R2 (behavior): "Keep the [embed] extra as an empty/alias group so
existing 'deepreason[embed]' instructions keep working."

R3 (behavior): "HashingEmbedder stays (EMBEDDER_MODEL=None escape,
controlled experiments — untouched)."

R4 (behavior): "Add an explicit warm-up hook where ladders already do
setup work (deepreason doctor, or a `deepreason embedder-warmup` step)
so the fetch happens in the setup phase with a visible progress line,
never silently inside cycle 1."

R5 (artifact): "Document the disk cost where the environment section
documents costs."

R6 (artifact): "Establish from the committed record
(experiments/results/e01_embedder_recalibration_report.json) which
embedder the SHIPPED thresholds were calibrated against, and record the
verdict in SPEC.md".

R7 (behavior, CONDITIONAL on R6): "if neural — this tranche closes a
real mismatch (live runs were applying neural-calibrated thresholds to
hashing geometry) and say so; if hashing — a `deepreason calibrate`
recalibration step is IN scope before the neural default is
armed-by-install, with the new values committed and their derivation
pasted."

R8 (behavior): "Keep EMBEDDER_FAILURE_POLICY="fallback" as the shipped
default BUT make the fallback loud where operators look: `deepreason
results` and the run's terminal summary surface "embedder: hashing
(fallback)" so it can never again be a log line nobody reads."

R9 (artifact): "Flipping the default to "error" is NOT granted — record
it as an option for the operator with one line of pricing."

R10 (process): "CLAUDE.md's environment/build lines and any skill
preflight naming the plain install keep working unchanged by S1 —
verify by grep and say so".

R11 (artifact): "update any doc that instructs installing [embed]
manually as the required step (it is now automatic). Same-commit rule
for every doc touched."

R12 (artifact): "the grounded-extension tranche's RESULTS.md gains a
dated segment stating its runs measured with hashing-128 under the S3
verdict's threshold regime, and what that does NOT change (LLM calls,
judge verdicts, artifact statuses are embedder-independent; the
affected instruments are novelty/dup/atlas distance measures)."

R13 (artifact): "Check PATROL_DETERMINISM_REPORT.md and any document
claiming "embeddings corroborate": if one asserts NEURAL embeddings
were used where the record shows hashing, that is a docs/ERRATA.md
entry (next free number — check the ledger tail); if the claim is
embedder-agnostic, record the scan and move on."

R14 (behavior): "regression — plain install imports fastembed and
build_embedder returns NeuralEmbedder without EmbedderUnavailable
(skip-marked only for genuinely offline CI, with the skip reason naming
this tranche)".

R15 (behavior): "the fallback path still works with EMBEDDER_MODEL=None;
the embedder-fallback measure still records when forced."

R16 (process): "Wheel smokes: if the required-modules pin covers
dependencies, re-pin in the SAME commit (four-pin rule if the MCP
surface moves, which it should not)."

R17 (process): "ring while iterating; full gate at the boundary;
docs_verify full (baselines per docs/AUDIT_BASELINES.md — gate
expectation is 0 failed)."

R18 (process): "Map moves in the same commits (the doc covering
llm/embedder.py)."

R19 (process): "Commit and push every phase boundary (retry
2s/4s/8s/16s)."

R20 (artifact): "Deliver R-by-R with pasted PROOF, closing with one
line: what a fresh container now gets from `pip install -e .` alone,
and which embedder the next live run will actually use."

## Standing constraints

C1: "It found that hash embedding was used, not the actual embedder.
That needs to be installed automatically." — operator verbatim
2026-08-13, quoted by the tranche-launch message as the AUTHORITY for
this REQUEST.md. This is the root obligation; R1..R20 serve it.

C2: "Route through dr-change-orchestrator; the workflow's own stop
conditions apply, nothing else stops." — tranche-launch message,
opening paragraph.

C3: "Use `python -m pytest`, never bare pytest." — tranche-launch
SETUP paragraph.

C4: "Embedder identity is recorded per-run; changing the default
changes FUTURE runs only — cross-version replay proofs are retired
(CLAUDE.md 2026-08-14 law)." — tranche-launch GATE paragraph. Removes
the obligation to prove committed roots' verdicts unmoved by the
default change.

C5: "EVIDENCE HONESTY (append, never edit)" — tranche-launch, governs
R12/R13: existing RESULTS.md and reports gain dated segments; nothing
already written is rewritten.

C6 (from CLAUDE.md, standing): the shipped default must not lock a solo
run out of any capability, and only parse/shape errors refuse — the
all-configurations law bears on R8/R9 (a missing backend must not
become a compile-time stop).

## Open questions (for dr-spec-change)

Q1: R6/R7 is a fork whose branch is decided by the committed record,
not by the operator: which embedder were the shipped thresholds
calibrated against? If "hashing", a `deepreason calibrate` step enters
scope and the tranche roughly doubles.

Q2: R4 offers two named sites — "deepreason doctor, or a `deepreason
embedder-warmup` step" — and does not choose. Which one, and does the
choice add a new CLI entry point (which the wheel smoke pins)?

Q3: R8 names "`deepreason results` and the run's terminal summary" as
the two surfaces. Whether the run's typed record already carries enough
to render "embedder: hashing (fallback)" at `results` time, or whether
a new stored field is needed, is undetermined by the words.

Q4: R14's regression asks that a plain install import fastembed. In a
container with no network at test time the ~0.5 GB weight fetch cannot
happen; the words allow a skip "only for genuinely offline CI". Whether
importing fastembed (no fetch) and constructing NeuralEmbedder (fetch)
are separable obligations is undetermined.

Q5: R16 asks to re-pin the wheel smoke "if the required-modules pin
covers dependencies" — whether it does is a fact to look up, not a
question for the operator.

## Amendments

(append-only; later operator messages land here as R21... or
"R2a supersedes R2", each with its verbatim quote)

### Amendment 1 — 2026-08-16, resolving the phase-A budget STOP

Context: STOP.md put three priced options to the operator after
`tools/diff_budget.py` returned `EXCEEDED` (324 insertions against a
301 ceiling) at the end of phase A, recommending option A — raise the
ceiling and finish as specified. The operator's reply, verbatim and in
full:

> Continue from where you left off.

R21 (process): "Continue from where you left off." — read as choosing
STOP.md option A, the recommended one: the ceiling is raised and the
tranche finishes as SPEC.md specifies, with no scope change. Read this
way and not as a bare "carry on with whatever" because the message
answers a question that offered exactly three roads and named a
recommendation; the only road that IS "where I left off" is finishing
the specified work — B and C both change the scope of what remains.

Consequences, all recorded rather than assumed:
- SPEC.md's Budget ceiling moves 301 → 450 (the STOP's projected ~424
  plus headroom), noted in SPEC.md as amended by R21 rather than
  silently rewritten. No SPEC item is added, removed, or altered.
- Nothing in R1..R20 changes. S6 (the loud fallback) and S10 (the
  evidence-honesty append) stay IN scope, which is the substance of
  the choice: options B and C would each have dropped part of R8 or
  deferred R8/R12 to a later tranche.
- Execution resumes at CHECKLIST.md step 13.
