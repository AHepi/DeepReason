# Goal: a run launched after a successful embedder warmup either uses the neural embedder or records a typed reason it could not

Class: defect

Observed: all five live arms of
`experiments/2026-09-04-experiment-brief-variation-step1/` report
`embedder: hashing (hashing-128)` from `deepreason results`
(RUNLOG.md:24-32 and :58; RESULTS.md §5 item 4; PARKED.md F6) although
`deepreason embedder-warmup` had returned
`{"model": "nomic-ai/nomic-embed-text-v1.5", "sentinel": "d6e3599ce0377000"}`
in the same container and session, and no `embedder-fallback` Measure names a
cause in any of the five roots' `log.jsonl`. The record therefore cannot say
which measurement scale the run used or why it changed.

Map ids resolved for this tranche (map preflight, recorded here so every later
phase starts from the same map):

- `DR-SUB-llm` — `build_embedder`, `HashingEmbedder.fingerprint`,
  `NeuralEmbedder` (SUB-llm.md:182-183)
- `DR-SUB-scheduler` — the once-per-run embedder geometry stamp
  (`record_measure(inputs=["embedder", ...])`, SUB-scheduler.md:132)
- `DR-SUB-application` — `embedder_summary` / `embedder_summary_for_root`,
  which derive the embedder a run ACTUALLY measured with from the log's own
  `embedder` / `embedder-fallback` Measure events (SUB-application.md:98-99)
- `DR-INV-frozen-surfaces` — read before designing; see the frozen-surface
  line below
- Seams read before the subsystems: `DR-SEAM-llm-x-scheduler` (no embedder
  row — the stamp is not a documented crossing there),
  `DR-SEAM-llm-x-verification` (pins `HashingEmbedder` as the deliberate
  choice for `detection-total`, which this tranche must not disturb)

Frozen surfaces: NONE EXPECTED. `INV-frozen-surfaces.md` names five surfaces
spanning seven paths — `capabilities/state.py`, `harness.py`, `invariants.py`,
`verification/`, `run_manifest.py`, `qualification.py` — plus the
frozen-adjacent `route_fingerprint` in `llm/firewall.py`. The `embedder` and
`embedder-fallback` Measure kinds and the `signals.py` catalogue that declares
them are none of those. If the fix turns out to need `run_manifest.py`'s
`embedder_backend` / `embedder_model` / `embedder_failure_policy` fields
(surface 4) the tranche STOPS and asks for a grant before writing code.

Success criterion (machine-decidable):

    (1) python -m pytest tests/test_embedder.py tests/test_results_command.py -q
        0 failed, and the file carries a NEW regression test, mutation-proven
        (it fails when the fix line is reverted), asserting BOTH halves:
          a. a run whose neural backend builds stamps the neural fingerprint,
             so `embedder_summary_for_root` reports the neural model;
          b. a run whose neural backend cannot build stamps a typed
             `embedder-fallback` Measure whose inputs carry the CAUSE, so
             `embedder_summary_for_root` reports the fallback AND the reason.

    (2) python -u scripts/<repro script committed in this tranche>
        an offline run against the deterministic stub, launched with the
        environment the detached arm scripts ran under (a cache location the
        process cannot read), reaches a terminal whose `log.jsonl` contains an
        `embedder-fallback` Measure naming the cause. Before the fix the same
        script shows a silent hashing stamp.

    (3) python -m pytest tests/ -q -n 4
        0 failed, once, at the boundary.

In scope (max 3): `src/deepreason/llm/embedder.py`,
`src/deepreason/scheduler/scheduler.py` (the once-per-run stamp only),
`src/deepreason/application/results.py` (only if the reason must be rendered).

NOT in scope: the `EMBEDDER_MODEL` default itself, `preparation.py`'s
host-owned config list, and anything that changes WHICH embedder a
configuration selects. This tranche makes the decision VISIBLE and correct
given the configuration; it does not re-decide the configuration. Also not in
scope: the `pyproject.toml` dependency-declaration gap parked at
`experiments/2026-08-30-change-execution-safety-parks/PARKED.md` S5.

Budget: <=150 changed lines, 1 commit, ~4 hours.

Stop conditions inherited from orchestrator: yes
