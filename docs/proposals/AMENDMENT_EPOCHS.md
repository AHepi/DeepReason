# Proposal: amendment epochs — reshape the question and inject evidence
# after a stop, without corrupting ledger, state, or evidence

Status: implemented (all four tranches). See "As implemented" at the end
for the one place the realization departs from this sketch, and why.
Motivated by the operator requirement: after a run, inject more content
and reshape the central question before continuing, with zero corruption
of the append-only ledger, the epistemic state, or already-submitted
evidence.

## The insight

DeepReason already treats ANSWERS as supersedable epochs (bridge
terminals chain parent -> successor; "no answer is final"). The
solution is to make the QUESTION and the EVIDENCE DOSSIER supersedable
by exactly the same mechanism. Nothing is ever edited; everything new
is appended and chained.

## The blockers today

1. The run manifest freezes the question (run-input digest) and the
   evidence dossier digest. `continue_run` validates against them.
2. The deterministic run identity derives from question + config: a
   changed question today means a NEW root and a lost epistemic state.
3. Replay validation checks every event against the single bound
   manifest.

## Design: `deepreason amend`, a typed in-root epoch

    deepreason amend [--attach FILE ...] [--reshape-question "TEXT"] \
        [--root ROOT]
    deepreason continue --tokens N

`amend` refuses (typed) unless the run stands at a typed terminal
stop. It appends ONE atomic chain of typed events to the SAME root:

1. **Supplemental admission** — each `--attach` file is admitted as a
   NEW dossier (dossier-2) with its own digest and its own
   attached-source records (import-role artifacts, which since the
   scheduler fix never count as survivors). Dossier-1 is never
   touched; its digest and its already-verified citations remain
   byte-checkable forever. The citation checker consults the UNION of
   dossiers, each block verified against its own dossier's digest.
2. **Question supersession** — `--reshape-question` registers a NEW
   problem whose provenance is `{trigger: seed, from: [old-question-id]}`.
   The old question problem is not deleted, not edited, not
   re-statused: its rivalry, discrimination spawns, and accepted
   positions all stand. Lineage records the reshaping as an event in
   the record, not a mutation of it. The seed trigger means the
   scheduler's seed-priority guarantee gives the reshaped question
   first claim on the continuation budget.
3. **Manifest epoch record** — `run-amendment.v1`, carrying
   `parent_manifest_digest`, `successor_manifest_digest`, the
   supplemental dossier digest(s), the new problem id, and the fence
   seq. The successor manifest is the parent manifest with ONLY the
   run-input reference and dossier list extended — capability
   policies, allowlists, budgets, and provider profile are copied
   verbatim, so the qualification subject is unchanged and the cached
   qualification remains valid (no requalify).

`continue` then resumes the same root: the epistemic state loads from
the unbroken ledger; new cycles work the reshaped question against
the union of old positions and new evidence.

## Why nothing corrupts

- **Ledger**: append-only is preserved — amendment is new events
  behind a fence, exactly like a bridge terminal. Crash mid-amendment
  leaves a typed partial chain that recovery refuses to continue past
  (fail-closed), and a re-run of `amend` supersedes it with a fresh
  chain; nothing is rewritten.
- **Replay**: piecewise validation, mirroring the existing
  epoch-aware bridge machinery — events before the amendment fence
  validate against the parent manifest, events after against the
  successor. `verify_root` walks the `run-amendment.v1` chain the
  same way it already walks superseding bridge terminals.
- **Epistemic state**: strictly additive — one new problem, new
  import artifacts, zero status flips. Every prior acceptance,
  refutation, rivalry, and criticism-debt record stands. The old
  question's positions remain attackable and citable; the record can
  show the operator exactly what the question USED to be and what
  survived it.
- **Evidence**: dossiers are immutable and cumulative. A citation
  verified against dossier-1 before the amendment verifies

  identically after it. New evidence can only ADD citable blocks.
- **Run identity**: unchanged — the root continues, so no epoch
  renames of the directory are needed for this path (those remain
  for failed/restarted runs).

## Implementation sketch (one tranche each)

1. `run-amendment.v1` record + state application (additive) +
   `verify_root` piecewise manifest validation.  [frozen-surface
   adjacent: operator approval required]
2. Supplemental admission path (reuse the attach compiler against a
   second dossier slot; citation checker unions dossiers).
3. `amend` CLI + typed refusals (not-at-terminal, empty amendment,
   partial-chain recovery) + `continue` fence check.
4. MCP: `amend_run` tool beside `continue_run`.

Regression fixtures: a completed root amended offline, then
(a) `verify_root` valid across the fence, (b) old citations still
verified, (c) reshaped question wins cycle 0 of the continuation,
(d) crash-mid-amend leaves a typed refusal and an intact parent
epoch.

## As implemented

Code: `src/deepreason/amendment/` (`models.py`, `state.py`, `apply.py`).
Durable shape: `run-amendments.jsonl` is the committed chain; each epoch's
complete documents live in `run-epochs/NNN/` (`run-manifest.json`,
`run-input.json`, `evidence-dossier.json`, `text-workload.json`, and the
staged `run-amendment.json`). Epoch 0 is the root's own bound documents
and is never touched. Source bytes are never copied: later dossiers
reference the same content-addressed blob store.

Order of durable writes is fail-closed: stage the epoch documents, then
apply the ledger chain, then commit the chain line. A crash leaves a
staged record with no committed line — `continue` refuses with
`CONTINUE_AMENDMENT_INCOMPLETE`, `verify_root` reports
`amendment-chain`, and a byte-identical re-run of `amend` completes the
same epoch (problem registration and source admission are both
content-addressed, so completion appends only what the first attempt did
not). A *different* amendment over a staged one is refused
`AMEND_PENDING_CONFLICT` rather than silently superseding it; that is
stricter than the sketch's "supersedes it with a fresh chain", and it
avoids leaving orphan events that no fence accounts for.

**The one departure.** The sketch mints a distinct successor manifest
whose `run_input_digest` names the new epoch's input. This codebase
cannot carry that today, and the reason is structural rather than
incidental: the controller's process state binds one manifest digest for
the life of a root (`workflow/state.py`, `apply_decision`), capability
transitions require `transition.run_input_digest == previous.
run_input_digest` (`capabilities/state.py`, a frozen surface), and every
work order, terminal commitment, and replay-validation binding is minted
against that one pair. A second digest mid-root would not be additive —
it would invalidate the authority chain of the epoch below the fence.

So an amendment supersedes the QUESTION and the EVIDENCE, and copies the
manifest verbatim: `successor_manifest_digest == parent_manifest_digest`,
and `manifest.run_input_digest` keeps naming epoch 0 as the run's one
input identity. The successor run-input is still a real, canonical,
digest-bound document — it is named by the amendment record and validated
by `verify_root` — it simply is not what work orders bind. The
qualification subject is therefore unchanged by construction, which is
what the sketch wanted anyway (no requalify). The per-epoch
`run-manifest.json` slot is kept so a future manifest-superseding epoch
has somewhere to go and `verify_root` already validates each side of the
fence against "its own" manifest.

Piecewise replay validation is by fence: `_amendment_epochs` in
`invariants.py` returns one `(fence, next_fence, dossier)` window per
epoch, and the attached-evidence checks (unique source record per source,
admitted before that epoch's first provider call) run per window. The
manifest's frozen attached-evidence budget binds the union of all bound
dossiers, and a dossier-pack receipt drawn in epoch N may cite every
source bound at or before N. An unamended root yields exactly one window
covering the whole log, so its validation is byte-for-byte what it was.

Operator surfaces: `deepreason amend --attach FILE --reshape-question
TEXT`, and the MCP `amend_run` tool (listed in `get_capabilities` under
the `amendment` area). Regression coverage is
`tests/test_amendment_epochs.py`, which runs (a)-(d) plus a real
`continue_run` across the fence.
