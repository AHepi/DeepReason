# Proposal: amendment epochs — reshape the question and inject evidence
# after a stop, without corrupting ledger, state, or evidence

Status: implemented (all four tranches), validated against this document
as its specification; see "As implemented" at the end for the durable
shapes and the ordering guarantees. Motivated by the operator
requirement: after a run, inject more content and reshape the central
question before continuing, with zero corruption of the append-only
ledger, the epistemic state, or already-submitted evidence.

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

    deepreason --root ROOT amend [--attach FILE ...] \
        [--reshape-question "TEXT"] [--allow-partial]
    deepreason --root ROOT continue --budget cycles=N \
        [--token-budget N|unlimited]

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
   seq. The manifest itself is copied VERBATIM across the epoch —
   capability policies, allowlists, budgets, and provider profile
   included — so the qualification subject is unchanged and the cached
   qualification remains valid (no requalify). What supersedes is the
   RUN INPUT and the DOSSIER, and the amendment record is what names
   them: the successor run-input is its own canonical, digest-bound
   document, chained to its parent by this record rather than by a
   re-pointed manifest. The manifest keeps naming epoch 0's input as
   the run's one input identity, which is what lets every work order,
   terminal commitment, and capability transition in the root keep
   binding a single stable pair.

   Minting a distinct successor manifest digest instead would not be
   additive: the controller's process state, the capability transition
   chain, terminal authority, and continuation history each bind that
   one pair for a root's whole life, so a second digest mid-root would
   invalidate the authority chain of the epoch BELOW the fence. That
   variant is parked, not required.

`continue` then resumes the same root: the epistemic state loads from
the unbroken ledger; new cycles work the reshaped question against
the union of old positions and new evidence.

## Why nothing corrupts

- **Ledger**: append-only is preserved — amendment is new events
  behind a fence, exactly like a bridge terminal. Crash mid-amendment
  leaves a typed partial chain that recovery refuses to continue past
  (fail-closed). A re-run of `amend` supersedes it with a fresh chain
  when that staged epoch has applied no ledger events yet — nothing can
  be orphaned, so nothing needs to be. Once it HAS applied events, they
  belong to that epoch: the re-run completes it instead, and a different
  amendment becomes the next epoch. Nothing is rewritten either way.
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
`CONTINUE_AMENDMENT_INCOMPLETE` and `verify_root` reports
`amendment-chain`. Recovery from there has exactly two shapes, decided
by whether the staged epoch had already reached the ledger:

- **Nothing applied** (`fence_seq == harness._next_seq`): a different
  amendment supersedes the staged one outright. The staged epoch
  directory is discarded and restaged; no ledger event exists to orphan,
  and the committed chain was never written.
- **Events applied**: those events belong to that epoch, so it is
  completed rather than replaced. A byte-identical re-run of `amend`
  finishes it — problem registration and source admission are both
  content-addressed, so completion appends only what the first attempt
  did not — and a *different* amendment is refused
  `AMEND_PENDING_CONFLICT`, whose message names the route: complete this
  epoch, then amend again for the next one.

**Manifest and run input.** `successor_manifest_digest ==
parent_manifest_digest`: the manifest is copied verbatim, and
`manifest.run_input_digest` keeps naming epoch 0 as the run's one input
identity. The superseding run-input is a real, canonical, digest-bound
document, named by the amendment record and validated by `verify_root`;
it is deliberately not what work orders bind. That is what keeps the
qualification subject unchanged by construction — no requalify — and
what keeps every work order, terminal commitment, and capability
transition below the fence binding the same stable pair they always did.
The per-epoch `run-manifest.json` slot is kept, and validated, so
`verify_root` already checks each side of the fence against "its own"
manifest; materializing a distinct successor digest there is parked
(see the tranche's `PARKED.md`), not required.

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
