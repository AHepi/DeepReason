# Request: implement amendment epochs

## Ledger note on this tranche's provenance

This tranche was executed directly (implementation, then commit
`0a946726`) BEFORE the change workflow was invoked. There is therefore
no `SPEC.md` and no `CHECKLIST.md`: the execution trail for those phases
does not exist and is not reconstructed here, because a retroactive
checklist would be a fabricated audit trail, not a record. What follows
is honest about what authority actually existed.

The operator designated an existing document as the specification, so
`SPEC.md`'s role is played by `docs/proposals/AMENDMENT_EPOCHS.md`
sections "Design", "Why nothing corrupts", "Implementation sketch", and
"Regression fixtures" (the "As implemented" section is the implementer's
own report and is NOT treated as spec — it is the thing under audit).

## Operator words (verbatim)

Turn 1:

> You are to implement the instructions in docs/proposals/AMENDMENT_EPOCHS.md

Turn 2:

> On branch claude/amendment-epochs-om0ztb, run the dr-validate-change
> skill against docs/proposals/AMENDMENT_EPOCHS.md as the spec, then
> dr-deliver-change. Do not merge until DELIVERY.md shows every
> requirement done

## Requirements (derived from the designated spec, quoted)

### Command surface

- **R1** — "`deepreason amend [--attach FILE ...] [--reshape-question
  "TEXT"] [--root ROOT]`"
- **R2** — "`deepreason continue --tokens N`" resumes afterwards.

### Preconditions and atomicity

- **R3** — "`amend` refuses (typed) unless the run stands at a typed
  terminal stop."
- **R4** — "It appends ONE atomic chain of typed events to the SAME
  root."

### 1. Supplemental admission

- **R5** — "each `--attach` file is admitted as a NEW dossier
  (dossier-2) with its own digest and its own attached-source records
  (import-role artifacts, which since the scheduler fix never count as
  survivors)."
- **R6** — "Dossier-1 is never touched; its digest and its
  already-verified citations remain byte-checkable forever."
- **R7** — "The citation checker consults the UNION of dossiers, each
  block verified against its own dossier's digest."

### 2. Question supersession

- **R8** — "`--reshape-question` registers a NEW problem whose
  provenance is `{trigger: seed, from: [old-question-id]}`."
- **R9** — "The old question problem is not deleted, not edited, not
  re-statused: its rivalry, discrimination spawns, and accepted
  positions all stand."
- **R10** — "The seed trigger means the scheduler's seed-priority
  guarantee gives the reshaped question first claim on the continuation
  budget."

### 3. Manifest epoch record

- **R11** — "`run-amendment.v1`, carrying `parent_manifest_digest`,
  `successor_manifest_digest`, the supplemental dossier digest(s), the
  new problem id, and the fence seq."
- **R12** — "The successor manifest is the parent manifest with ONLY the
  run-input reference and dossier list extended — capability policies,
  allowlists, budgets, and provider profile are copied verbatim, so the
  qualification subject is unchanged and the cached qualification
  remains valid (no requalify)."

### Continuation

- **R13** — "`continue` then resumes the same root: the epistemic state
  loads from the unbroken ledger; new cycles work the reshaped question
  against the union of old positions and new evidence."

### Why nothing corrupts

- **R14** — Ledger: "append-only is preserved — amendment is new events
  behind a fence, exactly like a bridge terminal."
- **R15** — "Crash mid-amendment leaves a typed partial chain that
  recovery refuses to continue past (fail-closed), and a re-run of
  `amend` supersedes it with a fresh chain; nothing is rewritten."
- **R16** — Replay: "piecewise validation ... events before the
  amendment fence validate against the parent manifest, events after
  against the successor. `verify_root` walks the `run-amendment.v1`
  chain."
- **R17** — Epistemic state: "strictly additive — one new problem, new
  import artifacts, zero status flips. Every prior acceptance,
  refutation, rivalry, and criticism-debt record stands."
- **R18** — Evidence: "dossiers are immutable and cumulative. A citation
  verified against dossier-1 before the amendment verifies identically
  after it. New evidence can only ADD citable blocks."
- **R19** — Run identity: "unchanged — the root continues, so no epoch
  renames of the directory are needed for this path."

### Implementation tranches

- **R20** (T1) — "`run-amendment.v1` record + state application
  (additive) + `verify_root` piecewise manifest validation.
  [frozen-surface adjacent: operator approval required]"
- **R21** (T2) — "Supplemental admission path (reuse the attach compiler
  against a second dossier slot; citation checker unions dossiers)."
- **R22** (T3) — "`amend` CLI + typed refusals (not-at-terminal, empty
  amendment, partial-chain recovery) + `continue` fence check."
- **R23** (T4) — "MCP: `amend_run` tool beside `continue_run`."

### Regression fixtures

- **R24** — "a completed root amended offline, then (a) `verify_root`
  valid across the fence, (b) old citations still verified, (c)
  reshaped question wins cycle 0 of the continuation, (d)
  crash-mid-amend leaves a typed refusal and an intact parent epoch."

## Amendments (operator ruling on VALIDATION.md's FAIL, 2026-07-30)

Asked: how should R12's mechanism clause resolve, and should R15/R1 be
fixed in this tranche. Operator selected:

> **Amend the spec to match** — "Rewrite R12 in AMENDMENT_EPOCHS.md so
> the successor run-input is carried by the amendment record rather than
> by a re-pointed manifest, keeping the outcome clause (no requalify) as
> the requirement. The implementation then satisfies R12 as written, and
> DELIVERY.md can show it done. Cheapest, and preserves every existing
> replay-valid root."

> **Fix both now** — "R15: allow a different amendment to supersede a
> staged epoch exactly when it has applied no ledger events yet
> (fence_seq == _next_seq), so nothing is orphaned; keep the fail-closed
> refusal once events exist. R1: correct the spec's usage line to the
> CLI's global --root rather than shadowing it with a subcommand
> duplicate. Then re-validate and deliver."

- **R12a** supersedes **R12**. The manifest is copied verbatim across an
  amendment epoch; the successor run-input and dossier are named by the
  `run-amendment.v1` record, not by a re-pointed manifest. The binding
  requirement is the outcome: capability policies, allowlists, budgets,
  and provider profile unchanged, so the qualification subject is
  unchanged and the cached qualification stays valid (no requalify).
  Carries with it: `docs/proposals/AMENDMENT_EPOCHS.md` must be edited so
  the design section states this, and the "As implemented" section must
  stop describing it as a departure.
- **R15a** refines **R15** (does not supersede it). Supersession of a
  staged-but-uncommitted epoch is required exactly when that epoch has
  applied no ledger events (`fence_seq == harness._next_seq`), because
  nothing can be orphaned. Once events exist, the fail-closed refusal
  stands and the refusal must name the operator's actual route forward.
- **R1a** supersedes **R1**'s `[--root ROOT]` placement. The root is
  given by this CLI's global `--root` option
  (`deepreason --root ROOT amend`); the spec's usage line is corrected
  rather than the CLI gaining a subcommand-level duplicate that would
  shadow it.

### Operator message mid-tranche (verbatim)

> Approved: amend R12's mechanism clause to match the implemented design
> — manifest copied verbatim, successor run-input carried by the
> amendment record. Park the successor-manifest digest materialization in
> PARKED.md as a possible future tranche; do not implement it now.

- **R12b** confirms **R12a** and adds: materializing a distinct successor
  manifest digest is PARKED, not implemented in this tranche. It goes in
  `PARKED.md` as a candidate future tranche.

### Operator message on PARKED P2 (verbatim)

> Yup. Amend needs to reject up front.  This is good news. Ok so after
> you've made the change, push to branch please.

- **R25** unparks **PARKED P2** and rules its open design question:
  `amend` refuses, before any parsing or staging, when an attached file's
  content is already admitted to this run. Refusal is whole-invocation,
  matching `collect_attachment_inputs`' existing rule that admitting a
  subset of what the operator pointed at would misrepresent the evidence
  base. The cross-epoch uniqueness rule in `verify_root` is left alone.

### Operator message on the coverage gaps (verbatim)

> Do all 3. Don't worry about cost.  Here is an Ollama API key. If you
> judge a live run might help, do it. Don't worry about token spend. You
> do whatever it takes to close all the gaps

- **R26** closes all three coverage gaps named in the post-delivery
  review: (1) `verify_root`'s amendment failure branches, which had never
  fired in a test; (2) an amendment beside a commitment-bound bridge
  episode past one terminal horizon; (3) three or more chained epochs.
  Plus the dead-export cleanup noted with them.
- **R27** authorizes a live run at the implementer's judgement, with the
  supplied Ollama credential and without a token-spend constraint.
