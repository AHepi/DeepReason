# Parked — noticed in this tranche, deliberately not done

## P1 — Materialize a distinct successor manifest digest per amendment epoch

Parked by operator instruction (REQUEST.md R12b): *"Park the
successor-manifest digest materialization in PARKED.md as a possible
future tranche; do not implement it now."*

**What it would be.** Today an amendment epoch copies the run manifest
verbatim, so `successor_manifest_digest == parent_manifest_digest`, and
the epoch's superseding run-input and dossier are named by the
`run-amendment.v1` record. The parked alternative mints a genuinely
distinct successor manifest whose `run_input_digest` points at the
epoch's own input, making the manifest — not the record — the authority
for which input an epoch runs under.

**Why it is not a small change.** The run's `(manifest digest,
run_input_digest)` pair is bound for the life of a root by:

- `workflow/state.py` — `WorkflowProcessStateV1.manifest_digest`, and
  `apply_decision` refusing any transition whose `manifest_digest`
  differs from the state's;
- `capabilities/state.py` — the capability transition chain requiring
  `transition.run_input_digest == previous.run_input_digest` (a
  CLAUDE.md frozen surface);
- `workflow/lifecycle.py` — `build_resumed_lifecycle` requiring
  `terminal.manifest_digest == manifest_digest`;
- `runtime/terminal_authority.py` — `derive_terminal_authority` requiring
  the passed manifest to equal the root-bound one, plus the terminal
  commitment and replay-validation bindings minted against it;
- `runtime/continuation.py` — `_continuation_history` requiring every
  record to carry one manifest digest;
- `cli/doctor.py` — the qualification report bound to one manifest
  digest;
- roughly twenty further identity comparisons in `invariants.py`.

Making those epoch-aware is not additive. Records below the fence carry
the parent digest and would have to keep validating against it while
records above carry the successor — which means every one of those sites
needs per-record epoch attribution, several of them on surfaces the
project has declared frozen precisely because getting this wrong
invalidates existing replay-valid roots.

**What would justify unparking it.** A concrete need the record-carried
design cannot serve — for example an amendment that must change routing,
budgets, or capability policy, not just the question and the evidence.
Nothing in the current requirement calls for that: the qualification
subject is meant to stay unchanged across an amendment, which is exactly
what copying the manifest verbatim guarantees by construction.

**Cost if unparked.** A full tranche of its own, with a real risk of
invalidating committed roots; it should carry its own goal, its own
frozen-surface approval, and a before/after `verify_root` sweep over
every committed root as its acceptance check.
