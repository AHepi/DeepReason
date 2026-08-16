# Spec for: "the neural embedder installs automatically — no run silently measures with the hash fallback again"

Traces: every item cites R/C numbers from REQUEST.md. Untraceable items
are bugs.

Map ids (from REQUEST.md's preflight): `DR-SUB-llm` (covering document
for `llm/embedder.py`), `DR-SUB-application` (covers
`application/results.py` and `cli/main.py`), `DR-SUB-scheduler`,
`DR-SUB-periphery` (covers `pyproject.toml`), `DR-SEAM-llm-x-rules`.

---

## The premise, re-derived (not assumed)

P1 — fastembed is absent under a plain install. Measured on this
container at HEAD `d52c739ff`, after `pip install -e .
--break-system-packages -q`:

    $ python -c "import fastembed"
    ModuleNotFoundError: No module named 'fastembed'

P2 — the live consequence is on the record. The grounded-extension run
`experiments/2026-08-12-live-grounded-extension-expansion/run/log.jsonl`
carries both halves, at seq 2 and seq 8:

    seq 2  Measure inputs=['embedder-fallback',
             'nomic-ai/nomic-embed-text-v1.5',
             "fastembed not installed (pip install 'deepreason[embed]'):
              No module named 'fastembed'"]
    seq 8  Measure inputs=['embedder', 'hashing-128', '1',
             '4226e035204776db']

and again at seq 9969 / 10045 / 10092 for the continuation epoch. The
run configured the neural model, could not build it, and measured with
hashing-128. C1's complaint is exactly this.

P3 — fastembed installs and the neural backend builds in this
environment. Measured:

    $ pip install "fastembed>=0.3" --break-system-packages -q ; echo rc=$?
    rc=0
    $ python -c "... build_embedder(DEFAULT_NEURAL_MODEL) ..."
    OK NeuralEmbedder nomic-ai/nomic-embed-text-v1.5
       fastembed-0.8.0+onnxruntime-1.28.0
    fingerprint {'model': 'nomic-ai/nomic-embed-text-v1.5',
                 'version': 'fastembed-0.8.0+onnxruntime-1.28.0',
                 'sentinel': 'd6e3599ce0377000'}
    elapsed 14.2s

P4 — the weights cost 523 MB on disk, at fastembed's default cache
directory, which is `/tmp/fastembed_cache` (NOT `~/.cache/huggingface`,
which held 100 KB after the fetch):

    $ du -sh /tmp/fastembed_cache
    523M    /tmp/fastembed_cache

This is a fact R5 must document, and it is sharper than the "~0.5 GB"
the request estimated: the cache lands in `/tmp`, which containers
routinely clear.

---

## S3 THRESHOLD TRUTH — the verdict (R6), and why R7 fires NEITHER branch

R7 offered a two-way fork: the shipped distance thresholds were
calibrated against neural (→ this tranche closes a real mismatch) or
against hashing (→ a `deepreason calibrate` recalibration enters
scope). **The committed record answers neither: every shipped absolute
distance threshold is `None`, i.e. unset and inert.** Measured:

    src/deepreason/config.py:259   RESEED_DIST_MIN: float | None = None
    src/deepreason/config.py:277   NEAR_DUP_EPS:    float | None = None
    src/deepreason/config.py:168   similarity_threshold: float | None = None   (scratch)
    $ grep -rniE "radius" src/deepreason/config.py   -> no hits
      (the config comment's "atlas radii" names no shipped knob)

What `None` means at the consumer, not merely at the declaration:

    src/deepreason/rules/guards/anti_relapse.py:7-8
      "Stages 2-3 run ONLY when a RelapseDomain, an embedder, AND a
       calibrated NEAR_DUP_EPS are all [present]"

So the near-dup gate and the absolute reseed tripwire are OFF in the
shipped configuration and cannot be mis-scaled by an embedder swap,
because they never fire under either embedder.

The two convergence knobs that DO ship armed are both embedder-safe by
construction, and E0.1 measured the first one under the neural embedder:

- `RESEED_RATIO_MAX = 0.3` — a RATIO of distances within one space
  (min inter-school centroid distance / mean within-stream pairwise
  distance), therefore scale-free. Its own comment says so and says it
  is "safe under any embedder including the hashing default". E0.1's M4
  measured it under the candidate NEURAL embedder on both roots
  (`inter_school_dist_ratio` 1.9391 and 0.93) with
  `"ratio_would_fire_at_0.3": false` — the armed knob was already
  checked against neural geometry and does not fire there either.
- `GATE_ORBIT_MIN = 5` — a COUNT of gate blocks per event window
  (`capture/detection.py:345-346`), not a distance at all.

Why no absolute value was ever adopted, from the same report: E0.1
records `"separable": {"near_dup_gate": false}` for BOTH embedders, and
its P3 note says "the neural embedder is ALSO not duplicate-vs-sibling
separable on this corpus ... the calibration question is ill-posed when
siblings are duplicates". Adopting either recommendation (hashing
`NEAR_DUP_EPS` 1.1925 / neural-candidate 0.5072) would have shipped a
threshold the record says is not separable. Leaving them `None` was the
correct call and remains it.

Consequence for scope, stated plainly: **R7's recalibration branch does
NOT trigger. `deepreason calibrate` stays out of this tranche.** No
threshold value is added, changed, or recalibrated here. The residue,
recorded honestly: E0.1's candidate embedder was
`BAAI/bge-small-en-v1.5`, NOT the shipped default
`nomic-ai/nomic-embed-text-v1.5`, and its n=2 roots were both gemma4
website runs — so nothing above is a calibration OF the shipped model;
it is a demonstration that there is no shipped absolute threshold FOR
an embedder swap to invalidate. `deepreason calibrate` remains the
documented instrument for anyone who arms one.

One config comment is factually wrong today and is corrected by S5: it
tells the reader to "recalibrate ... before trusting a config on a new
embedder" while listing knobs that ship unset, and it names "atlas
radii", which do not exist as config knobs.

---

## Items

**S1 (R1, R2) — fastembed becomes a core dependency.**
`pyproject.toml`. Before: `dependencies = ["pydantic>=2.7",
"pyyaml>=6.0"]` and `[project.optional-dependencies] embed =
["fastembed>=0.3"]`. After: `fastembed>=0.3` moves into `dependencies`;
the `embed` extra stays declared as an empty alias group (`embed = []`)
with a comment saying it is retained so `pip install 'deepreason[embed]'`
keeps resolving.
  accept: `python -c "import tomllib,pathlib; d=tomllib.loads(pathlib.Path('pyproject.toml').read_text()); assert any(r.startswith('fastembed') for r in d['project']['dependencies']); assert d['project']['optional-dependencies']['embed'] == []; print('ok')"` → `ok`
  accept: `pip install -e . --break-system-packages -q && python -c "import fastembed; print(fastembed.__version__)"` → a version string.

**S2 (R3) — HashingEmbedder and the `EMBEDDER_MODEL=None` escape are
untouched.** No file changes. Proven by test, not by assertion.
  accept: `git diff --stat` over the tranche shows no edit to
  `class HashingEmbedder` or to the `EMBEDDER_MODEL` default value; and
  `python -m pytest tests/test_embedder.py -q` includes the S9 test
  asserting `build_embedder(None)` is a `HashingEmbedder`.

**S3 (R4) — an explicit warm-up step.** New CLI subcommand
`deepreason embedder-warmup` in `src/deepreason/cli/main.py`
(parser + `_cmd_embedder_warmup`). Before: the first neural use is
whatever code path touches an embedder first — inside cycle 1 of a run.
After: an explicit setup-phase command that prints a visible progress
line to stderr before the fetch ("fetching ONNX weights for <model>
(~523 MB, one time; cached at <dir>) ..."), constructs the embedder,
embeds the sentinel, and prints the resulting fingerprint JSON to
stdout. `--model` overrides `config.EMBEDDER_MODEL`. Exit 0 on success;
on `EmbedderUnavailable` it prints the typed reason to stderr and
returns 1 — a runtime failure at the point of use, which C6's
all-configurations law explicitly permits (only COMPILE may not refuse).
`deepreason doctor`'s existing `embedder` block gains one constant
field, `warmup_command: "deepreason embedder-warmup"`, so the preflight
that already reports `dependency_available` also names the next action.
  accept: `deepreason embedder-warmup --model nomic-ai/nomic-embed-text-v1.5` → exit 0, stdout parses as JSON with keys `model`/`version`/`sentinel`, stderr contains the progress line.
  accept: `deepreason doctor --dry-run ... | python -c "...json...['embedder']['warmup_command']"` → `deepreason embedder-warmup`.

**S4 (R5) — the disk cost is documented where costs are documented.**
`CLAUDE.md`'s "Environment (cloud container)" section gains one line
naming 523 MB and the `/tmp/fastembed_cache` location and the warm-up
command; `config.py`'s EMBEDDER_MODEL comment is corrected from
"Requires the optional dependency group" to the new truth.
  accept: `grep -n "fastembed_cache" CLAUDE.md` → a hit; `grep -n "deepreason\[embed\]" src/deepreason/config.py` → no hit.

**S5 (R6, R7) — the threshold verdict is recorded.** This document's
"S3 THRESHOLD TRUTH" section above IS the deliverable for R6. R7's
recalibration branch does not fire (reason above). `config.py`'s
comment loses its false "atlas radii" reference and states that the
absolute knobs ship unset.
  accept: this SPEC.md contains the verdict section (it does); `grep -n "atlas radii" src/deepreason/config.py` → no hit.

**S6 (R8) — the fallback becomes loud where operators look.**
New `embedder_summary(harness)` in
`src/deepreason/application/results.py`, deriving from the log's own
Measure events (`embedder` and `embedder-fallback` first-inputs, the
same pattern `_adjudication` already uses at results.py:222-251) a
typed block:

    {"backend": "hashing"|"neural", "model": "hashing-128",
     "version": "1", "fingerprint": "4226e035204776db",
     "fallback": true, "configured_model": "nomic-ai/...",
     "fallback_reason": "<the recorded message>"}

or the typed absence `{"absent": true, "reason":
"NO_EMBEDDER_RECORD"}` (a new member of `ABSENCE_REASONS`, which is a
closed vocabulary the tests assert against). `results_summary` gains
`summary["embedder"]`; `render_results` prints a glossed line reading
`embedder: hashing (fallback)` when `fallback` is true and
`embedder: neural (nomic-ai/nomic-embed-text-v1.5)` otherwise. The
run's terminal summary — the JSON `_cmd_reason` prints from
`terminal.presentation_payload()` — gains `payload["embedder"]` at the
same site and in the same manner as the two decorations already there
(`payload["run_id"]`, `payload["evidence_dossier_digest"]`,
`cli/main.py:2315-2318`). PRESENTATION ONLY: `run-result.json` on disk
is not modified, so no durable record format moves.
  accept: `python -m pytest tests/test_results_command.py -q` → 0 failed, including the S9 test that a root whose log carries `embedder-fallback` renders `embedder: hashing (fallback)`.
  accept: `deepreason results experiments/2026-08-12-live-grounded-extension-expansion/run | grep -i embedder` → a line containing `hashing (fallback)`.

**S7 (R9) — the "error" default is priced, not taken.**
`EMBEDDER_FAILURE_POLICY` keeps its shipped value `"fallback"` (no
code change). DELIVERY.md records the option in one line: *flipping the
default to `"error"` would stop any run that cannot build the neural
backend before its first model call — it buys "no run ever measures
with a geometry it did not ask for" and costs "a genuinely offline
container can no longer run at all", which is a road the operator may
take by setting the knob per-run today.*
  accept: `grep -n 'EMBEDDER_FAILURE_POLICY: Literal\["fallback", "error"\] = "fallback"' src/deepreason/config.py` → a hit (unchanged); DELIVERY.md contains the pricing line.

**S8 (R10, R11) — preflight currency.** R10 is a verification, pasted:
CLAUDE.md's build line is `pip install -e .
--break-system-packages`, which S1 leaves working and strictly
improves. Docs that instruct installing the extra as the required step
are updated: `docs/EXPERIMENT_PROGRAM_2026-07.md:101` ("Install the
`.[embed]` extra") and `docs/SCRATCHPAD_GROUNDED_BRIDGE.md:83`; the
error message in `llm/embedder.py:107-109` is reworded (it currently
tells a user to install an extra that is now empty). Same-commit rule
for every doc touched.
  accept: `grep -rn "deepreason\[embed\]\|\.\[embed\]" --include=*.md --include=*.py . | grep -v experiments/2026-08-16-change-embedder-auto-install | grep -v experiments/2026-08-13-change-lifecycle-operation-parity` → no hits (the 2026-08-13 PARKED.md is an immutable historical ledger entry and is exempt).
  accept: `grep -n "pip install -e \." CLAUDE.md` → unchanged hits.

**S9 (R14, R15) — regression tests**, in `tests/test_embedder.py` and
`tests/test_results_command.py`:
  - `test_fastembed_is_a_core_dependency` — `importlib.util.find_spec("fastembed") is not None`. NEVER skips: this is the packaging regression itself. Docstring: "Regression (tranche 2026-08-16-change-embedder-auto-install): fastembed left the [embed] extra; a plain `pip install -e .` must carry it, or every live run silently measures with hashing-128 again (grounded-extension run log.jsonl seq 2/8)."
  - `test_build_embedder_returns_neural_under_plain_install` — asserts `build_embedder(DEFAULT_NEURAL_MODEL)` is a `NeuralEmbedder`. Skips ONLY when construction raises `EmbedderUnavailable` whose message does NOT name a missing fastembed (i.e. the weight fetch is impossible — genuinely offline CI); a missing-fastembed message is a hard FAIL, never a skip. Skip reason names this tranche.
  - `test_hashing_escape_survives` — `build_embedder(None)` is a `HashingEmbedder` with model `hashing-128` (R3, R15).
  - `test_forced_unavailable_still_records_embedder_fallback` — the existing pattern at `tests/test_embedder.py:54-63`, kept green (R15).
  - `test_results_surfaces_embedder_fallback` — a root whose log carries the two Measure events renders `embedder: hashing (fallback)` and its summary block carries `fallback: True` (R8).
  - `test_results_embedder_absence_is_typed` — a root with no embedder Measure event yields `{"absent": True, "reason": "NO_EMBEDDER_RECORD"}` and that reason is in `ABSENCE_REASONS` (R8, and the reader-before-writer guardrail: every committed root predating the stamp stays readable).
  accept: `python -m pytest tests/test_embedder.py tests/test_results_command.py -q` → 0 failed.

**S10 (R12, R13) — evidence honesty, appended never edited.**
`experiments/2026-08-12-live-grounded-extension-expansion/RESULTS.md`
gains a dated 2026-08-16 segment: its runs measured with hashing-128
(seq 2/8 and 9969/10045/10092 pasted), under the S3 verdict's regime —
every shipped absolute distance threshold was `None`, so no
neural-calibrated number was applied to hashing geometry; what this
does NOT change (LLM calls, judge verdicts, artifact statuses, stop
reasons are embedder-independent); what it DOES affect
(novelty/dup/atlas distance measures and school-convergence
diagnostics read on the lexical scale). R13's scan is recorded there
too, with its verdict: **no ERRATA entry is needed.**
  accept: `grep -n "2026-08-16" experiments/2026-08-12-live-grounded-extension-expansion/RESULTS.md` → a hit; the file's pre-existing bytes are unchanged above the new segment (`git diff` shows additions only).

**S11 (R16) — the wheel smokes need no re-pin.** Verified, pasted:
`scripts/wheel_smoke.py:64-73`'s `REQUIRED_MODULES` is a set of FILE
PATHS INSIDE the wheel, not a dependency list; its only METADATA
assertion is `"Summary: DeepReason V6-only deterministic reasoning
harness" not in metadata` (line 150), which a new `Requires-Dist` does
not move. `console_help` is pinned only for four REMOVED commands and
the presence of `shallow` (lines 305-309), so S3's new subcommand does
not move it. The MCP surface is untouched, so the four-pin rule does
not engage.
  accept: `python scripts/wheel_smoke.py; echo rc=$?` → `rc=0`; `python -u scripts/wheel_operational_smoke.py; echo rc=$?` → `rc=0`.

**S12 (R18) — the map moves in the same commit.**
`docs/map/SUB-llm.md` is the covering document for `llm/embedder.py`.
Its "What can break" row for the embedding backend gains a `Traps`
entry naming the grounded-extension run, and one new executable
`check:` that would FAIL if fastembed left the core dependency list —
i.e. a check on `pyproject.toml`'s dependency list, not on the import
(an import check would pass on any container that happens to have
fastembed for another reason). `Verified-at:` advances only if that
document's checks are actually re-run.
  accept: `python tools/docs_verify.py` → 0 failed beyond the 3 baseline `CON-run-identity.md` git-history failures (docs/AUDIT_BASELINES.md); `python tools/docs_verify.py --audit` → the new check is not refused as unfailable.

**S13 (R17, R19, R20) — process.** Ring while iterating
(`tests/test_embedder.py`, `tests/test_results_command.py`,
`tests/test_scratch_similarity.py`, `tests/test_manifest_integration.py`,
`tests/test_schema_v3_consumers.py`); full gate at the boundary;
`docs_verify` full (never concurrently with the gate — `dr-drive-harness`
§5b); commit and push at every phase boundary with 2s/4s/8s/16s retry;
DELIVERY.md carries the R-by-R table with pasted proof.
  accept: `python -m pytest tests/ -q -n 4` → `0 failed`; DELIVERY.md has one row per R1..R20.

---

## Assumptions (operator may override)

A1 (Q2) — **`deepreason embedder-warmup`, not `deepreason doctor`.**
The request named both and chose neither. `doctor` is a read-only
preflight that today reports `dependency_available` without side
effects (`cli/main.py:1449-1500`); making it fetch 523 MB would turn a
diagnostic into a downloader, which is the same class of surprise this
tranche exists to remove. Smallest reading: a dedicated explicit
command, plus one constant field in `doctor`'s existing `embedder`
block pointing at it. Assumed, operator may override.

A2 (Q2/A1 corollary) — **doctor does NOT probe whether the weights are
already cached.** A cache probe would have to guess fastembed's
internal layout, and a wrong `cached: true` is worse than no claim.
`warmup_command` is a constant string; the warm-up itself is cheap and
idempotent when the weights are present. Assumed, operator may override.

A3 (Q3) — **the terminal summary is decorated at the print site, not in
`run-result.json`.** `_cmd_reason` already adds `run_id` and
`evidence_dossier_digest` to the printed payload after
`presentation_payload()` (`cli/main.py:2315-2318`); `embedder` joins
them there. This keeps the durable sidecar and
`TextRunTerminalResultV1`'s strict schema untouched, which is the whole
reason it is the smallest reading. Assumed, operator may override.

A4 (Q4) — **the two halves of R14 are separate tests** (S9): the
packaging half never skips, only the weight-fetch half may, and only
when the failure is a fetch failure rather than a missing fastembed.
Assumed, operator may override.

A5 (Q5) — resolved by the record, not assumed: S11's pasted evidence
shows the wheel smokes pin no dependency list. No re-pin.

A6 (R13) — **no ERRATA entry.** The one document claiming "embeddings
corroborate" (`docs/HANDOVER_MONITOR_2026-08-10.md:100`) points at
`PATROL_DETERMINISM_REPORT.md`, whose claim is EXPLICIT about running
two embedders, one neural — and its raw output proves the neural pass
really ran: `semantic_crosscheck.jsonl` (9,277 rows) carries distinct
`hashing_cosine` and `neural_cosine` columns per row (e.g. 0.799416 vs
0.871452), and `RESULTS.md:422` names
`NeuralEmbedder(BAAI/bge-small-en-v1.5)`. That analysis was an offline
cross-check script, not a live harness run, so the live-run fallback
does not touch it. No document asserts neural embeddings where the
record shows hashing. Scan recorded in S10; ledger tail checked — the
next free number would have been E32, unused.

---

## Questions for operator (STOP if non-empty)

None. Q1 was answered by the committed record (the verdict section
above), Q5 by the wheel-smoke source, and Q2/Q3/Q4 resolved to the
smallest reading under A1-A4 — each a presentation or setup-surface
choice, none changing which files move by more than one function.

---

## Out of scope (explicit)

- `deepreason calibrate` recalibration and any new threshold value —
  R7's branch does not fire (verdict above). Not requested otherwise.
- Flipping `EMBEDDER_FAILURE_POLICY` to `"error"` — R9 explicitly
  withholds the grant.
- Changing `EMBEDDER_MODEL`'s default model — not requested.
- Adding the embedder to `run-result.json`, `run-status.json`, or any
  durable sidecar — not requested, and A3's presentation decoration
  delivers R8's stated property without it.
- Re-running or re-verifying committed roots — C4 retires that
  obligation.
- `docs/map` documents for `pyproject.toml` packaging (the gap
  REQUEST.md recorded) — creating a new map document is not requested;
  `SUB-periphery.md` and `SUB-application.md` already carry checks
  referencing the file, and S12 puts the load-bearing new check in
  `SUB-llm.md` where the behaviour lives. Parked.

---

## Frozen-surface contact forecast

Gate run (`tools/blast_radius.py --files pyproject.toml
src/deepreason/llm/embedder.py src/deepreason/config.py
src/deepreason/cli/main.py src/deepreason/application/results.py
src/deepreason/ops.py --symbols build_embedder NeuralEmbedder
EmbedderUnavailable make_embedder results_summary render_results`),
verbatim fields:

    "frozen_surface_contacts": []
    "frozen_adjacent_contacts": []
    "frozen_surface_verdict": "CLEAR"
    "qualification_digest": []
    "wheel_smoke_pins": []

Reachability, verbatim:

    build_embedder        REACHABLE
    NeuralEmbedder        UNKNOWN
    EmbedderUnavailable   UNKNOWN
    make_embedder         UNREACHABLE
    results_summary       REACHABLE
    render_results        REACHABLE

Required manual cross-check for the two `UNKNOWN` entries (the gate
states in writing that it cannot judge them), pasted:

    $ grep -rn "NeuralEmbedder\|EmbedderUnavailable\|build_embedder" \
        src/deepreason/capabilities/state.py src/deepreason/harness.py \
        src/deepreason/invariants.py src/deepreason/run_manifest.py \
        src/deepreason/qualification.py
    src/deepreason/harness.py:1911:  models give distinct vectors — two
                                     NeuralEmbedders with different

The single hit is a DOCSTRING inside `Harness.embed_artifact`
(harness.py:1904-1919), an in-process memo cache keyed by embedder
model id. The frozen surface in `harness.py` is event application and
well-formedness; `embed_artifact` applies no event, computes no digest,
and this tranche does not modify it. `capabilities/state.py`,
`invariants.py`, `run_manifest.py` and `qualification.py` have no hits
at all. Verdict: no contact, no STOP.

`make_embedder` reporting UNREACHABLE is a pre-existing property of the
gate's syntactic analysis, disclosed here and NOT a finding of this
tranche: `ops.make_embedder` is passed by reference through the
scheduler construction path. This tranche does not modify it.

---

## Blast-radius census

From the same gate run's `consumers` field, every hit classified.

`consumers.tests`:

| target | hits | classification |
|---|---|---|
| `pyproject.toml` | `tests/test_blast_radius.py:48,76` | MUST NOT MOVE — the gate's own fixture references the path, not its contents |
| `pyproject.toml` | `tests/test_wheel_operational.py:4220` | MUST NOT MOVE — verify at ring time; if it asserts on the dependency list it becomes EXPECTED TO MOVE and the change is stated in the commit |
| `src/deepreason/application/results.py` | `tests/test_error_catalog.py:66` | MUST NOT MOVE — S6 adds no new error code, only an `ABSENCE_REASONS` member |
| `build_embedder` | `tests/test_embedder.py:17,35,36,44,192` | 44 EXPECTED TO MOVE (asserts the message matches `deepreason\[embed\]`, which S8 rewords); 17/35/36/192 MUST NOT MOVE |
| `build_embedder` | `tests/test_manifest_integration.py:102`, `tests/test_scratch_similarity.py:163,187` | MUST NOT MOVE — all monkeypatch the builder; S1 does not change its signature |
| `EmbedderUnavailable` | `tests/test_embedder.py:15,43,193` | 43 EXPECTED TO MOVE (same message assertion); 15/193 MUST NOT MOVE |
| `EmbedderUnavailable` | `tests/test_manifest_integration.py:97,100,107`, `tests/test_scratch_similarity.py:161,185` | MUST NOT MOVE — forced-unavailable fixtures, the exact paths R15 requires stay working |
| `make_embedder` | `tests/test_embedder.py:21,56,68,76`; `test_manifest_integration.py:103,108,111`; `test_runtime_workload_integration.py:417`; `test_simulation_capability_v5.py:287`; `test_v6_global_dispatch_guard.py:287,970` | MUST NOT MOVE — S2/R3 keeps the fallback contract identical |
| `results_summary` | `tests/test_results_command.py` ×34 | MUST NOT MOVE except where a test enumerates the summary's top-level keys or `ABSENCE_REASONS` — those are EXPECTED TO MOVE, since S6 adds `embedder` and `NO_EMBEDDER_RECORD` |
| `render_results` | `tests/test_results_command.py:485,492,515,518` | EXPECTED TO MOVE if they assert the rendered line set; otherwise MUST NOT MOVE |

Manual cross-check for a shape the gate cannot resolve (a string key,
not a Python identifier), required by step 5:

    $ grep -rn "dependency_available" tests/
    tests/test_schema_v3_consumers.py:102:  "dependency_available": False,

EXPECTED TO MOVE **only if** that fixture derives the value from the
live environment; if it is a hand-written literal in a schema fixture
it MUST NOT MOVE. This is the highest-risk single hit in the census —
S1 flips `dependency_available` to `True` on every machine that now
installs fastembed — and it is checked FIRST in the checklist, before
any other test is touched.

`consumers.map_checks` — every document whose `check:` line references
a touched file:

| target | map documents | classification |
|---|---|---|
| `pyproject.toml` | `SUB-application.md:34`, `SUB-periphery.md:119` | MUST NOT MOVE — verify at ring time |
| `src/deepreason/llm/embedder.py` | `SUB-llm.md:90` | EXPECTED TO MOVE — S12 owns this document |
| `src/deepreason/config.py` | `CON-authority.md:4,72,81,82,84,85`, `CON-packs-and-token-economy.md:47`, `INV-frozen-surfaces.md:99`, `SEAM-manifest-x-schools.md:196`, `SUB-evaluation.md:176,177`, `SUB-periphery.md:211`, `SUB-scheduler.md:147` | MUST NOT MOVE — S4/S5 change only COMMENT text in `config.py`, no field name, type, or default |
| `src/deepreason/cli/main.py` | `CON-run-identity.md:131,249`, `SEAM-schools-x-scheduler.md:81`, `SUB-amendment.md:139`, `SUB-application.md:48,132,162,199,219,230,247,374`, `SUB-manifest.md:140`, `SUB-periphery.md:44`, `SUB-verification.md:249` | MUST NOT MOVE — S3/S6 add a subcommand and a printed key; if any check enumerates the subcommand set it becomes EXPECTED TO MOVE and is updated in the same commit |
| `src/deepreason/application/results.py` | `SUB-application.md:97,219` | MUST NOT MOVE unless a check enumerates the summary keys |
| `src/deepreason/ops.py` | `CON-authority.md:4,97`, `SUB-scheduler.md:85` | MUST NOT MOVE — `ops.py` is not modified by any item |
| `build_embedder` | `SUB-llm.md:87,90,151` | MUST NOT MOVE — the symbol keeps its name and signature |
| `NeuralEmbedder` | `SUB-harness.md:195`, `SUB-llm.md:151` | MUST NOT MOVE |
| `results_summary`, `render_results` | `SUB-application.md:90,97,180` | MUST NOT MOVE unless key-enumerating |

`qualification_digest`: `[]` — empty, pasted. `wheel_smoke_pins`: `[]`
— empty, pasted, and independently confirmed by S11's source reading.

---

## Record-observable guardrails

S6 adds no data to the typed record — it READS the `embedder` /
`embedder-fallback` Measure events the scheduler has stamped since
before this tranche (`scheduler/scheduler.py:1915-1924`,
`ops.py:174-176`). Nothing is written, so no root's bytes move and no
`root_sweep.py` probe is owed. The reader is absence-tolerant by
construction: `NO_EMBEDDER_RECORD` is a declared `ABSENCE_REASONS`
member, and S9's `test_results_embedder_absence_is_typed` proves a root
without the events still reads cleanly.

---

## Budget

Itemized: S1 8, S2 0, S3 55, S4 12, S5 6, S6 60, S7 0, S8 15, S9 90,
S10 40, S11 0, S12 15.

    $ python3 -c "print(sum([8,0,55,12,6,60,0,15,90,40,0,15]))"
    301

**~301 lines, 3 code/doc commits** inside this one tranche (packaging +
warm-up + docs + map + their tests; the results/terminal surfacing +
its tests; the evidence-honesty append), plus the artifact commits
(REQUEST/SPEC/CHECKLIST/VALIDATION/DELIVERY). Frozen surfaces touched:
**none** (`frozen_surface_verdict: CLEAR`, pasted above).

Not split into sub-tranches despite sitting on the ~300 guidance line:
S1 arms the neural default by install and S6 is the instrument that
makes a failure of that arming visible. Shipping S1 without S6 is the
exact defect C1 names, one layer up. They deliver together or not at
all; the three ordered commits give the reviewable granularity a split
would have bought.

---

Rubric: 6/6 yes — every R1..R20 has a spec item with a machine-decidable
accept (R1-R2→S1, R3→S2, R4→S3, R5→S4, R6-R7→S5, R8→S6, R9→S7,
R10-R11→S8, R12-R13→S10, R14-R15→S9, R16→S11, R17→S13, R18→S12,
R19→S13, R20→S13); blast-radius census pasted from the gate with every
hit classified plus the two manual cross-checks the gate said it could
not judge; frozen-surface contact forecast recorded with the tool's
verbatim fields; every mechanism the request named traced to code it
actually reaches (the `[embed]` extra, `deepreason doctor`, `deepreason
results`, `deepreason calibrate`, `e01_embedder_recalibration_report.json`,
`REQUIRED_MODULES` — each read, and the two that do NOT reach are
documented as such: `deepreason calibrate` because R7's branch does not
fire, `REQUIRED_MODULES` because it pins files not dependencies); not a
DESIGN-AND-STOP request; nothing untraceable to an R/C number.
