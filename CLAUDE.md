# CLAUDE.md — operating DeepReason

DeepReason is a Popperian reasoning harness: it drives a provider model
(currently glm-5.2 on Ollama Cloud) through conjecture–criticism cycles
over an append-only, replay-verifiable record. Everything meaningful is
TYPED — stops, denials, refusals, capability lifecycles — and the record
is the only admissible evidence about what a run did. Model prose is
never evidence; `log.jsonl`, `objects/`, `progress.jsonl`,
`run-status.json`, `REPLAY_VALIDATION.json`, and `verify_root` are.

## Which workflow to use

Both families now begin with a MAP PREFLIGHT: resolve the work to
`DR-SUB-`/`DR-CON-`/`DR-SEAM-` ids from `docs/map/INDEX.md`, read the seam
before the subsystems, and read `INV-frozen-surfaces.md` before designing.
Record the ids in the tranche's first artifact so every later phase starts
from the same map.

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

Cutting across both families, two skills:

- `dr-drive-harness` — the driving manual. Load it at the start of any
  session that runs, modifies, or diagnoses the harness: session
  preflight, the public CLI lifecycle, live-run ladder rules, and where
  to look before modifying (map order, frozen surfaces) or when
  diagnosing (record first).
- `dr-ask-the-right-question` — question discipline. Load it before
  acting on any ambiguous or terse operator message, whenever a phase
  says "stop and ask", and whenever evidence contradicts your
  expectation: it routes each question to the cheapest authority
  (record → framework → operator) and kills false forks before they
  spend operator attention.

`.claude/skills/README.md` is the index of the whole skill set — both
families phase by phase, with the artifact each phase owns.

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

Iterate on the RING, gate at the BOUNDARY. The full suite is a gate, not a
feedback loop: run the affected test files while iterating, and the whole
suite only at a phase boundary. `.pytest_cache` already holds `lastfailed`
and every collected nodeid, so use it instead of re-deriving it:

    pytest tests/test_<subsystem>*.py -q      # the ring, while iterating
    pytest tests/ -q -n 4 --lf                # only what failed last time
    pytest tests/ -q -n 4                     # the gate, at the boundary

This is a recorded mistake, not a style note: one tranche ran the full gate
four times (9:17, 9:19, 10:53, 14:02 — ~44 minutes) to learn about roughly
forty tests that could have been affected, with `--lf` available and unused
throughout. Preserve results and re-derive only what moved.

The 42-root sweep obeys the same rule for the same reason. A committed root
is immutable, so its verdict can only move if the READER moved; when no
reader changed, the previous sweep IS the current answer.

The wheel smokes (`python scripts/wheel_smoke.py`; `python -u
scripts/wheel_operational_smoke.py`) are the third instrument, and NO
gate runs them. They pin the public surface — console entry points, MCP
tool set + schema sha, wheel layout — so any commit changing that
surface updates the pins and re-runs the smoke in the same commit.

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
  (Both specific encodings were FIXED 2026-08-01 — SWEEP.md/
  REPAIR_OSCILLATION.md; live simulation SUCCEEDED events recorded
  2026-08-09, overnight-omnibus Block B — the examples are historical,
  the blob-first discipline is the enduring rule.)
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
- The operator's explanation style (recorded 2026-08-06; extended
  2026-08-08 at their request, and BINDING for every operator-facing
  message, intermediary and final alike — load
  `dr-explain-to-operator` at session start): answer their actual
  worry in the FIRST sentence, before any mechanism. When a finding
  sounds like bad news, state what it does NOT mean for their intent
  before what it does. Present forks as real-world roads priced in
  their terms (what they can do, when, at what cost), with a
  recommendation. Own your part plainly when a prior instruction or
  workflow rule caused the confusion. In every INTERMEDIARY message
  (status updates, phase reports, STOP questions, failure notices),
  gloss every technical term conservatively in-line — the precise term
  plus, in plain words, what it is and what it does; when unsure
  whether a term needs glossing, gloss it. Close every FINAL output
  with ONE short, accurate everyday analogy ("the fire marshal
  certifies the room as arranged, or each chair individually") —
  required on the last message, never on intermediaries. Internal
  artifacts keep full precision; anything shown to the operator
  carries its plain-language meaning alongside.
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
- Prompts written for the operator to paste into executor windows are
  delivered inline in the chat reply as ONE fenced code block (easy to
  copy whole), never only in a committed file or spread across prose
  (operator request, 2026-08-11).

## Operator design laws (stated by the operator, standing, not
## derived from defects)

- **Formalism is an option, never an obligation** (2026-08-08,
  repeated by the operator "endlessly" — do not make them repeat it
  again): nothing may force a conjecture to be formal, and nothing may
  penalize a conjecture for being informal — not admission, not rank,
  not criticism exposure, not acceptance. Formal backing may grant
  protection (prose-immunity); its absence grants no disadvantage.
  Any design that weights outcomes on conjecture KIND violates this
  law. See DUAL_MODE_CONJECTURE_PREPLAN.md R-g for the full binding
  form.
- **Seats change how content is GENERATED, never what counts as
  EVIDENCE** (the modes/packages guardrail, BEHAVIOR_MODES_PREPLAN /
  ROLE_SEAT_SEPARATION_PLAN S7): no seat, mode, or package may let a
  generation seat's prose skip criticism.
- **A solo run with everything on must be an option** (2026-08-09,
  operator's words verbatim: "A solo run with everything on should be
  an option. That's what solo run option should always have been.
  However, turning on judges at all should be done with caution. I
  would prefer to do without, since they prosecute without any
  discernable discrimination."): sole-model operation may never be
  structurally locked out of any harness capability — including
  status-changing criticism; designs gated on multi-family judge
  ensembles need a solo-compatible road. And judge seats are
  suspect-by-default: any design leaning on LLM judges must first
  consult the judge-audit evidence in the committed record (see the
  judge-evidence review tranche) rather than assume judges
  discriminate.
- **Tokens are cheap; the agent is not** (2026-08-08, operator's words
  verbatim: "Ollama API tokens are cheap, you are not. Running endless
  API experiments is preferred if it means you do less work. Creating
  evidence from live runs is preferred if it means less work."): when a
  question can be answered by live runs or API experiments, run them
  instead of building machinery or reasoning it out offline; prefer
  evidence generated by live runs over hand-crafted synthetic fixtures
  when that saves agent work; build only what generated evidence
  demands. The evidence discipline itself is unchanged — experiments
  stay pre-registered and raw-preserved, and model prose is still
  never evidence.

## The map — `docs/map/` (read this before scoping any change)

125 000 lines across 34 packages. Do not scope a change by grepping; scope it
from the map. **`docs/map/INDEX.md` is the entry point** and routes to
everything else. `docs/map/SCHEMA.md` is the contract for reading and writing
map documents — read it once, before you touch one.

Five kinds of document; the filename is the identifier:

    SUB-<pkg>.md         a subsystem: what it owns, entry points, state
    CON-<slug>.md        a cross-cutting concept that is NOT a package
                         (schools, authority, warrants, run identity)
    SEAM-<a>-x-<b>.md    how two of them meet — sides alphabetical
    INV-<slug>.md        an invariant / frozen surface
    REC-<slug>.md        a change recipe

**How to read it.** `INDEX.md` → the routing table. For a change that spans two
things, read the SEAM document BEFORE either subsystem: it says which fraction
of each side is actually involved, and it is usually small. Read
`INV-frozen-surfaces.md` before designing anything — discovering a frozen
surface after the code is written is the expensive order to discover it in. For
a defect, read the covering document's `Traps` section before the record: a
recurrence is the cheapest diagnosis available.

**Documents are authenticated by RE-DERIVATION, not by signature.** Every
load-bearing claim carries a `check:` shell command at column 0 that must exit
0. A signature would prove who wrote a sentence; this proves the sentence is
still true, which is the property that decays.

    python tools/docs_verify.py           # every check; 0 failed required
    python tools/docs_verify.py --audit   # refuses checks that cannot fail
    python tools/docs_verify.py --links   # every DR- reference resolves
    python tools/docs_verify.py --stale   # advisory: docs worth re-reading

**How to modify it.** The map moves in the SAME COMMIT as the code — a separate
"update docs" commit is the commit that gets dropped. Advance `Verified-at:`
only if you actually re-ran that document's checks; a stale stamp is honest, a
false one is not. New behaviour needs a new check that would fail if the
behaviour regressed — run it before you write it down. Every fix earns a
`Traps` entry naming its run id, and a `Traps` entry is never deleted, only
rewritten to say when it was fixed. The orchestrator skills enforce all of
this; `SCHEMA.md` states it in full.

A seam document that does not exist means the pair has not been written up —
`INDEX.md`'s matrix says which. It never means the two do not interact.

## Directory map

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
    docs/                      specs (harness v1.3 + v1.4/v1.5/v1.6/v1.7
                               amendments — read ALL amendments; note
                               "V6" elsewhere names the RunManifest/
                               policy generation and the wire-contract
                               series, NOT this spec document series),
                               STATE_OF_THE_THEORY, TOKEN_ECONOMY,
                               BASIN_REPORT
    .claude/skills/            the two workflow families

Start any session by reading the newest RESULTS.md segments — they are
the running truth of what has been proven, broken, fixed, and parked —
and `docs/ERRATA.md`, the append-only ledger of corrections to committed
documents: it says which document claims have already been found wrong,
so you do not re-trust them.
