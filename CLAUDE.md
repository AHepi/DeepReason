# CLAUDE.md — operating DeepReason

DeepReason is a Popperian reasoning harness: it drives a provider model
(currently glm-5.2 on Ollama Cloud) through conjecture–criticism cycles
over an append-only, replay-verifiable record. Everything meaningful is
TYPED — stops, denials, refusals, capability lifecycles — and the record
is the only admissible evidence about what a run did. Model prose is
never evidence; `log.jsonl`, `objects/`, `progress.jsonl`,
`run-status.json`, `REPLAY_VALIDATION.json`, and `verify_root` are.

## Which workflow to use

Two skill families live in `.claude/skills/`. Route ALL substantive work
through one of them — they exist to prevent scope creep, missed steps,
and forgotten inputs:

- **Something is broken / suspicious** → `deepreason-orchestrator`
  (phases: dr-set-goal → dr-diagnose → dr-reproduce → dr-propose-fix →
  dr-implement-fix → dr-verify-outcome). Diagnosis comes from the typed
  record BEFORE code reading.
- **The operator suggests a change** → `dr-change-orchestrator`
  (phases: dr-capture-request → dr-spec-change → dr-plan-steps →
  dr-execute-step (one step per invocation) → dr-validate-change →
  dr-deliver-change). Authority is the operator's verbatim words,
  ledgered in REQUEST.md; every artifact traces to requirement numbers.

Cross-routing: a defect found mid-change is PARKED, not fixed; a change
wished for mid-defect is PARKED, not implemented. One tranche, one goal.

## Environment (cloud container — read first, every session)

The container can ROLL BACK silently to a stale checkout, killing
background processes and deleting gitignored files. After any gap:

    git log --oneline -1        # stale head? resync:
    git fetch origin <branch> && git checkout -B <branch> origin/<branch>
    which deepreason || pip install -e . --break-system-packages -q
    ls experiments/live_research_*/env   # gitignored credential file

The `env` file (OLLAMA_API_KEY=...) is gitignored and never committed;
recreate it from the operator's handover if missing. Because work can
vanish, commit and push the working branch at every phase boundary, and
run a snapshot loop (see `experiments/live_research_2026-07-29/
snapshot_loop.sh <driver>.sh`) during any long live run.

## Build and test

    pip install -e . --break-system-packages    # editable install; the
                                                # CLI and live runs share it
    pytest tests/ -q -n 4                       # full gate, ~8 min
                                                # expect ~3100 passed, 0 failed

Gate discipline: 0 failed is the only acceptable result. Never weaken an
assertion to get green. A fixture that depended on defective behavior may
be minimally updated only when the fix's design doc predicted it.
Regression tests name their motivating run in the docstring
("Regression (selfstudy run-9175f0ec): ...").

## Live runs (ladders)

Ladders are shell scripts (`experiments/*/**_run.sh`) that do
setup → qualify → reason → audit against a `DEEPREASON_HOME`.

- **Run identity is deterministic.** Same question + config → same
  run id. A leftover root refuses relaunch with RUN_ALREADY_STARTED.
  Retire it — `git mv run-<id> <failed|completed>-epochN-run-<id>` —
  and COMMIT THE RENAME FIRST. Never edit a committed root's contents.
  To change the QUESTION or add evidence without losing the epistemic
  state, do not mint a new root: `deepreason amend` appends an amendment
  epoch to the stopped one (docs/proposals/AMENDMENT_EPOCHS.md), then
  `deepreason continue` resumes it.
- **Qualification caches by subject digest.** Same home + same provider
  profile + same opt-ins → cache hit (~1 s). Changing the profile (e.g.
  completion tokens) or the home reruns the full battery (~14 min,
  ~1160 calls). This is by design; budget for it.
- **Launch detached, never foreground:** from the ladder's directory,
  `setsid nohup ./<ladder>.sh & disown`. Arm the snapshot loop and a
  monitor on the newest root's `progress.jsonl` (state/phase/tokens)
  plus the driver log's `rc=` lines — alert on failure signatures, not
  just success.
- **Judge only typed outcomes:** run state, stop_reason, the ladder's
  audit JSON, `verify_root`, FINDINGS.md. Known facts: glm-5.2 is a
  reasoning model — a hard question can burn the whole completion cap
  on hidden reasoning and emit nothing (typed seat failure; raise
  `--maximum-completion-tokens`). Capability-channel use (typed
  simulation/research proposals) is STOCHASTIC across identical runs;
  one live attempt that misses a path is inconclusive for that path,
  and the offline regression remains the proof.

## Frozen surfaces (never touch without explicit operator approval)

- `src/deepreason/capabilities/state.py` digests and event application
- `src/deepreason/harness.py` event application / well-formedness
- Replay-validation record formats; manifest schemas
- Anything altering qualification subject digests
- The append-only record itself: fix READERS so old roots stay valid;
  a change that invalidates existing replay-valid roots is wrong by
  definition.

## Hard-won invariants (violations of these were real, recorded defects)

- When a run dies at cycle 0, READ THE DIAGNOSTIC BLOB before theorising.
  Both cycle-0 deaths so far were misattributed on first reading. turmite
  (`_not_a_self_link`) really was a rule JSON Schema cannot express; jolt was
  first written up the same way and was not — the blob said
  `simulation observables must be plain identifiers`, a plain `pattern` the
  sweep had missed on `requested_observables`. The `attempt_trace` gives
  `validation_path` and `diagnostic_ref`; the blob under `blobs/` gives the
  verbatim error and the rejected value. Check SWEEP.md's not-expressible list
  only AFTER the blob rules out a rule that could have been encoded.
- The operator's seed question always wins scheduler rank ties;
  import-role admission records never count as "survivors".
- Per-capability budgets meter only their own capability's records —
  the shared capability-state maps pool ALL capabilities' proposals
  and work orders; always filter by type.
- Render-receipt handle maps reload key-sorted (B1, B10, B2, ...);
  compare by handle index (`ordered_refs`), never by `.values()`.
- Within one capability proposal's transition chain, manifest sha and
  fence seqs are frozen; test fixtures must respect this.

## Conventions

- Reporting to the operator: lead with the result in one or two sentences.
  Detail goes in the experiment's RESULTS.md, not the reply. Do not restate
  the reasoning that produced a finding once the finding is stated. Say
  corrections plainly and move on.
- Commits: one defect or one change per commit; message states what,
  why, the live evidence (run ids), and "Full gate: N passed, 0
  failed" when code changed. Push with retry (2s/4s/8s/16s backoff).
- Comments state constraints the code cannot show — never narration of
  the change or its history.
- Experiment narrative lives in the experiment's RESULTS.md as dated,
  honest-ledger segments: what the record shows, and the residue —
  what remains unproven. "Accepted does not mean true." Never claim
  more than the record shows; a negative or inconclusive result is
  recorded as one.
- Scratch/temp files go in the session scratchpad, never the repo.

## Map

    src/deepreason/
      scheduler/scheduler.py   problem selection, cycles, budgets
      rules/                   spawn (conn/disc/succ/debt), conjecture
      amendment/               post-stop epochs: reshape the question,
                               admit more evidence, chain, never edit
      capabilities/            simulation + research controllers, state
      scratch/                 attention, render receipts, authoring
      workflow/                v6 transactional work lifecycle
      invariants.py            verify_root (replay validation)
      harness.py               append-only log, state application
    tests/                     the gate; helpers worth reusing:
                               _prepare_run, controller fixtures
    experiments/               live evidence; RESULTS.md = narrative
    docs/                      specs (harness v1.3 + v1.5 amendment,
                               STATE_OF_THE_THEORY, TOKEN_ECONOMY,
                               BASIN_REPORT)
    .claude/skills/            the two workflow families

Start any session by reading the newest RESULTS.md segments — they are
the running truth of what has been proven, broken, fixed, and parked.
