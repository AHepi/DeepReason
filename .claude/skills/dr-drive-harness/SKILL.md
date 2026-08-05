---
name: dr-drive-harness
description: The driving manual for DeepReason - how to run the harness properly (session preflight, the public CLI lifecycle, live-run ladders) and where to look before modifying anything or when diagnosing a problem. An index over the owning authorities (CLAUDE.md, docs/map, the workflow skills), not a replacement for them. Load at the start of any session that will run, modify, or diagnose the harness, especially a first session in this repo.
---

# Drive the harness

You are operating a Popperian reasoning harness whose entire epistemology
rests on one rule: **the typed record is the only admissible evidence**.
`log.jsonl`, `objects/`, `progress.jsonl`, `run-status.json`,
`REPLAY_VALIDATION.json`, `verify_root` — those are evidence. Model prose,
including yours, is not. Every section below is an index: it tells you the
load-bearing command and WHERE the full authority lives, so you never
operate from a half-remembered copy.

## 1. Session preflight (before anything else)

The cloud container rolls back silently — stale checkout, dead processes,
deleted gitignored files. CLAUDE.md's "Environment" section is the
authority; the sequence is:

    git log --oneline -1                      # stale head? resync:
    git fetch origin <branch> && git checkout -B <branch> origin/<branch>
    python -c "import deepreason" || pip install -e . --break-system-packages -q
    ls experiments/*/env 2>/dev/null          # gitignored credentials survive?

Always `python -m pytest`, never bare `pytest` (PATH shim). Credentials
are recreated from the operator's handover, never committed. Commit and
push at every phase boundary — work between pushes is work at risk. Then
read, in order: CLAUDE.md, the newest `experiments/*/RESULTS.md` segments,
`docs/ERRATA.md`.

Re-entering mid-tranche needs no conversation history: every tranche is
resumable from its committed artifacts alone. Read the tranche dir's
CHECKLIST.md `State:` line, then REQUEST.md/SPEC.md, and continue. The
whole fresh-window prompt is one line — "Resume tranche <dir> from its
artifacts." If a session cannot resume from the artifacts, the previous
session under-committed; record that gap, reconstruct, and commit.

## 2. Running it — the public lifecycle

The supported product surface (authority: `README.md`):

    deepreason setup                 # one strict provider profile
    deepreason qualify --yes         # explicit; tier ladder full/shallow/unqualified
    deepreason status [--json]       # readiness + the one next action
    deepreason reason "QUESTION" [--cycles N] [--token-budget N]
    deepreason reason "Q" --attach file.pdf        # frozen evidence, dossier digest
    deepreason --root ROOT amend --attach f --reshape-question "Q2"
    deepreason --root ROOT continue --budget cycles=N
    deepreason reason --shallow "Q"  # MiniReason reduced engine
    deepreason web                   # loopback-only page over the MCP facade

Facts that bite (authority: CLAUDE.md "Live runs"): qualification caches
by subject digest — same home + profile + opt-ins is a ~1s cache hit,
any change reruns a ~14-minute battery; qualify opt-ins must match reason
opt-ins (`--attached-evidence` ⇔ `--attach`); provider reasoning must be
EXPLICITLY disabled for ollama when required (unset is not off — the
refusal is typed).

## 3. Running it — live experiment ladders

Ladders are shell scripts (`experiments/*/**_run.sh`): setup → qualify →
reason → audit against a `DEEPREASON_HOME`. The rules, each learned the
expensive way (authority: CLAUDE.md "Live runs"):

- **Run identity is deterministic.** Same question + config → same run
  id; a leftover root refuses with RUN_ALREADY_STARTED. Retire by rename
  (`git mv run-<id> <state>-epochN-run-<id>`) and COMMIT THE RENAME FIRST.
  Never edit a committed root — to change the question or add evidence,
  `deepreason amend` then `continue`.
- **Launch detached, never foreground:** from the ladder's directory,
  `setsid nohup ./<ladder>.sh & disown`. Arm the snapshot loop
  (`snapshot_loop.sh`) and a monitor on the newest root's
  `progress.jsonl` plus the driver log's `rc=` lines — alert on failure
  signatures, not just success.
- **Judge only typed outcomes:** run state, stop_reason, the audit JSON,
  `verify_root`, FINDINGS.md. Capability-channel use is stochastic across
  identical runs — one live miss is inconclusive; the offline regression
  is the proof.

## 4. Where to look BEFORE modifying anything

Never scope a change by grepping 125k lines. The map is the navigation
layer, and the reading order is fixed:

1. `docs/map/INDEX.md` — resolve the work to ids (`DR-SUB-<pkg>`,
   `DR-CON-<concept>`, `DR-SEAM-<a>-x-<b>`).
2. `docs/map/INV-frozen-surfaces.md` — **first, always**: five surfaces
   are not yours to change (state digests, harness event application,
   replay-validation formats, manifest schemas + validators,
   qualification subjects). Readers may be fixed; formats may not.
3. If the change spans two things, the seam document BEFORE either
   subsystem: the file is `docs/map/SEAM-<a>-x-<b>.md`, sides in
   alphabetical order. It names the small fraction of each side actually
   involved. The worked recipe for any seam change is
   `docs/map/REC-change-a-seam.md`.
4. `docs/map/SCHEMA.md` before writing or editing any map document. The
   map moves in the SAME commit as the code, or it becomes a document
   that lies.

Instruments that prove you broke nothing: the full gate
(`python -m pytest tests/ -q -n 4`, 0 failed only) and the root sweep
(`python tools/root_sweep.py` — no committed root's verdict may move).
Third instrument, which NO gate runs for you: the wheel smokes
(`python scripts/wheel_smoke.py`; `python -u
scripts/wheel_operational_smoke.py`) — build-and-operate checks over
the INSTALLED package. They pin the public surface (console entry
points, MCP tool set + schema sha, wheel layout), so any change to that
surface updates the pins and re-runs the smoke in the SAME commit — or
the instrument rots silently (found 2026-08-05: red for a week after an
entry-point addition, unnoticed, because nothing named it).
`python tools/docs_verify.py` is the same gate for the map — and its
`--fast` mode reuses cached results, so it CANNOT catch a document your
`src/` change just broke. Iterate with `--fast`; run the FULL mode at
least once before any commit that touches `src/` (proven at commit
`55b16ce9`: the full run caught a fifth affected map document that
`--fast` had passed clean).

## 5. Where to look WHEN something breaks

Record first, code second, theory last. In order:

| Look at | It tells you |
|---|---|
| `<root>/run-status.json` | state, stop_reason, message — often the whole answer |
| `<root>/progress.jsonl` | which cycle/phase/token count it died at |
| `<root>/REPLAY_VALIDATION.json`, `verify_root(<root>)` | typed violations: check name + detail (open the root READ-ONLY — a writable open repairs, i.e. destroys, the evidence) |
| the violation's blob under `<root>/blobs/` | the verbatim error and the rejected value — read this BEFORE theorizing; both recorded cycle-0 deaths were misattributed by readers who skipped it |
| the covering map document's **Traps** section | whether this exact failure happened before — the cheapest diagnosis available |
| `docs/ERRATA.md` | whether the document you are trusting was already corrected |

Two instruments can disagree and both be right (`verify_root` vs
`verify_root_report` vs the sweep) — always cite the instrument with the
number. When the cause is located, do not fix it inline: route it.

## 5b. Process hygiene (each rule paid for in the record)

- **Kill by PID, never by pattern.** `pkill -f`/`pgrep -f` match your
  own shell's command line — the 2026-08-05 smoke tranche killed its
  own session twice this way.
- **Never run the full gate concurrently with `docs_verify`** (or any
  other worker-spawning instrument): both fan out processes, and the
  contention manufactures failures — three corrupted gate measurements
  across two tranches (P1 verify; T2's U3), each costing a re-run and
  a re-diagnosis. One instrument at a time, on an otherwise idle box.
- **A surprising measurement taken under load is not a measurement.**
  Re-run idle before recording it, and say which run you recorded.
- **Long work launches detached** (`setsid nohup ... & disown`, §3) —
  a foreground process dies with the session.
- Scratch and temp files go to the session scratchpad, never the repo.

## 6. Routing to the workflows

All substantive work goes through a workflow family — that is repo law
(CLAUDE.md), not preference. `.claude/skills/README.md` is the index of
all of them.

- Something is broken or suspicious → `deepreason-orchestrator`
  (dr-set-goal → dr-diagnose → dr-reproduce → dr-propose-fix →
  dr-implement-fix → dr-verify-outcome). Diagnosis from the typed record
  BEFORE code reading.
- The operator suggests a change → `dr-change-orchestrator`
  (dr-capture-request → dr-spec-change → dr-plan-steps → dr-execute-step
  → dr-validate-change → dr-deliver-change). Authority is the operator's
  verbatim words, ledgered in REQUEST.md.
- The operator's message is ambiguous or terse, a phase says "stop and
  ask", or evidence contradicts your expectation →
  `dr-ask-the-right-question` first: route the question to the cheapest
  authority (record → framework → operator) before spending operator
  attention.

Cross-routing is strict: a defect found mid-change is PARKED, not fixed;
a change wished for mid-defect is PARKED, not implemented. One tranche,
one goal.

**Calibration for less capable executors.** The documents this manual
points at are complete by design — execute them literally rather than
improvising a summary of them. Never generalize an instruction beyond its
stated scope; if a spec seems silent about your case, that is a question
(load `dr-ask-the-right-question`), not an invitation to infer. A
multi-step program (a handover, a checklist, a ladder) runs one step per
tranche — finishing a step early is never a reason to start the next in
the same tranche. Stop conditions and DESIGN-AND-STOP gates are hard
stops: the deliverable at a gate is a committed document and an ended
turn, not an implementation. And every stop presented to the operator
leads with the decision needed in ONE sentence, the options priced, and
a recommendation with its reason — the operator should be able to
answer with a word.

**Exit criterion.** You know you are driving properly when every claim
you make about a run ends in a typed artifact, every modification you
plan started from `INDEX.md` and `INV-frozen-surfaces.md`, and every
problem you chase entered a workflow tranche with its evidence committed.
