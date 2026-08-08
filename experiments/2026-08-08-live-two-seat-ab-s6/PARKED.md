# Parked — Rung S6 (the live two-seat A/B)

Noticed during this tranche, deliberately NOT fixed here — this is a
LIVE-RUN tranche; `src/`, `tests/`, `tools/`, `docs/map/` stay
byte-untouched throughout, so a defect found here routes to
`deepreason-orchestrator`, not to an inline fix.

## P1 (DEFECT, found by the live run — parked, NOT fixed): `property_designer` has no public path to ever fire

**What's broken:** the `coder` seat group (`GROUP_ROLES["coder"] =
{"property_designer"}`) binds a real profile correctly and is stamped
correctly into the typed record (Rung S5's own mechanism, proven both
offline and live), but the role it binds can never actually be
DISPATCHED through any path reachable from the public CLI. This was
first mischaracterized in this tranche's own `RESULTS.md` (initial
segment) as a "stochastic miss," matching CLAUDE.md's own documented
capability-channel stochasticity doctrine — that characterization is
WRONG and has been corrected in a dated `RESULTS.md` segment (never
editing the original) rather than silently fixed in place.

**The diagnosis chain, verbatim from the correcting `RESULTS.md`
segment — reproduced here so this parked item carries its own complete
evidence, not a pointer that could rot:**

1. `GROUP_ROLES["coder"] = frozenset({"property_designer"})`
   (`seat_bindings.py`) — the `coder` group's ONLY role.
2. `property_designer` is dispatched from exactly one call site,
   `rules/experiment.py::propose_properties`, which early-returns `[]`
   unless `oracle.py::checker_wf_commitment(base)` returns non-`None`.
3. `checker_wf_commitment(base)` (`oracle.py:776`) itself early-returns
   `None` unless `base.eval == f"program:{PROPERTY_PROGRAM}"` — i.e.
   unless an ACTIVE property-oracle commitment already exists in the
   run's own graph.
4. The only function anywhere in `src/deepreason/` that constructs a
   NEW `Commitment` with `eval == "program:property_oracle"` is
   `oracle.py::property_oracle_commitment` (line 335).
5. `property_oracle_commitment`'s only caller in the entire tree is
   `oracle.py::admit_counterexample` (line 431 — confirmed the exact
   one call site outside the function's own definition).
6. `admit_counterexample` (`oracle.py:386`) itself REQUIRES `base.eval
   == f"program:{PROPERTY_PROGRAM}"` as its own precondition (line
   397) — it mints a counterexample-derived oracle INHERITING an
   existing base oracle's own spec; it does not mint the first one.
7. Every other reference to `PROPERTY_PROGRAM` in the tree
   (`run_manifest.py:3830`, `rules/crit.py:779,813,942`,
   `scheduler/scheduler.py:2201,2246,2288`) READS `commitment.eval ==
   f"program:{PROPERTY_PROGRAM}"` to gate some OTHER behavior; none of
   them constructs one.

**The circularity, stated plainly:** minting a property-oracle
commitment requires an existing property-oracle commitment as input.
No public path — the CLI, the seed-problem admission path, or any rule
this tranche's live run actually exercised — constructs the FIRST one.
`property_designer` therefore has no way to ever fire on ANY run
launched through the public surface, structurally, independent of
question, cycle budget, or which models are bound to which seats. This
is consistent with an independent, standing observation: no
`log.jsonl` under `experiments/` or `runs/` in this repository's entire
history has ever carried a `"role": "property_designer"` LLM-call
record.

**Why this was missed on first read:** reasoning by analogy to
CLAUDE.md's documented capability-channel stochasticity doctrine
(which genuinely does govern OTHER, live-model-driven proposal paths)
without tracing `property_oracle_commitment`'s own caller graph to its
end — the same shape as `docs/map/INV-frozen-surfaces.md`'s own
recorded trap "reading a model and not its validator," applied here to
a different mechanism entirely.

**Not fixed here, on purpose:** whether property oracles should be
publicly mintable at all — e.g. a new CLI path, an attached-evidence
shape that seeds one, or some other bootstrap — is an OPERATOR DESIGN
DECISION, not a bug this live-run tranche is positioned to fix. Building
one unilaterally would be scope creep into a feature question dressed
as a defect fix. This tranche's own live-demonstration need was
satisfied by re-running on a seat proven to do real work
(`conjecture`, binding `conjecturer`+`variator`) instead — see
`RESULTS.md`'s own re-run segment.

**Ready-to-send prompt:** "Diagnose whether `property_designer` /
`coder`-seat work should ever be publicly reachable, and if so design
the bootstrap path for the FIRST `program:property_oracle` commitment
— via `deepreason-orchestrator`, starting from `dr-set-goal` with this
PARKED.md's P1 entry (the full call-graph evidence chain above) as the
starting diagnosis. This is a design question first (does the operator
want this path open at all) and only a `dr-implement-fix` matter
second, once that's answered."

## P2 (DEFECT, found by the live run — parked, NOT fixed): run identity does not include seat bindings, so rebinding a seat for the SAME question collides with the earlier run

**What's broken:** `deepreason reason`'s managed run identity
(`managed_run_id`, and the `request_digest` it is derived from) is
computed by `preparation.py::_request_digest` (line 249) from exactly
`{schema, question, budget, provider_profile_digest, policy_preset_id,
policy_preset_digest}` — the DEFAULT/broadcast provider profile's own
digest, plus the question text and budget. `--seat GROUP=PATH`
bindings are never an input to this hash; they are folded in later,
only when building the run's live provider config
(`_config_for_profile`, line 268) and as a sibling snapshot file
written into the run root, never into the identity itself.

**Consequence:** two `deepreason setup` + `deepreason reason` attempts
that ask the SAME question against the SAME base profile but bind
DIFFERENT seat groups (e.g. `coder=...` vs. `conjecture=...`) compute
the IDENTICAL `managed_run_id`. The second attempt does not silently
overwrite the first (the harness's append-only discipline holds) — it
refuses typed, `PREPARATION_QUALIFICATION_BUNDLE_MISMATCH`
(`preparation.py:776-780`, `_load_existing` finding the existing root's
frozen `qualification_bundle_digest` does not match the newly
recomputed one for the new seat combination). This is a safe refusal,
not data loss, but it means **the same question cannot be run twice
under two different seat-binding configurations without changing the
question itself** — a real friction against exactly the kind of
same-question, different-seat-assignment A/B this role-seat separation
program exists to support.

**Found by:** this tranche's own second live-run attempt
(`s6_run_v2.sh`, Failure #3 in `RESULTS.md`), which hit this refusal
directly when reusing the first run's question verbatim after only
changing which seat group the second profile was bound to.

**Not fixed here, on purpose:** this is a live-run tranche; `src/` stays
byte-untouched. Whether `_request_digest` SHOULD fold in the seat
bindings snapshot digest (making seat rebinding mint a new run, the
behavior this tranche initially assumed existed) or whether the
current behavior is intentional (seat bindings are meant to be
reassignable within one run's identity, e.g. for a future
`deepreason amend`-driven reseat) is an operator design decision, not
a bug this tranche is positioned to adjudicate unilaterally.

**Work-around used, no code changed:** gave the second demonstration a
question text that differs from the first (see `RESULTS.md`'s Failure
#3 segment) — `question` is a direct input to `_request_digest`, so
this reliably mints an unrelated `managed_run_id` with no interaction
with the already-committed first run root.

**Ready-to-send prompt:** "Decide whether `_request_digest`
(`src/deepreason/preparation.py:249`) should include the seat-bindings
digest as an identity input, given it currently excludes seat bindings
entirely — meaning the same question run twice with two different
`--seat` configurations against the same base profile collides on
identity and refuses typed (`PREPARATION_QUALIFICATION_BUNDLE_MISMATCH`).
Start from `dr-set-goal` with this PARKED.md's P2 entry as the starting
diagnosis; this is a design question (should reseating mint a new run
identity) before it is an implementation question."

## P3 (DEFECT, found by the live run — parked, NOT fixed): `continue` can crash resuming an in-flight criticism-recovery decomposition, `NonConjectureRecoveryAuthorityError("unknown critic task")`

**What's broken:** when an `argumentative_critic` batch call
(`batch-critic.v2`) repeatedly returns malformed JSON, the harness's own
recovery machinery (`src/deepreason/workflow/nonconjecture_recovery.py`)
declares `schema_exhausted` and decomposes the batch into individual
`critic.atomic-target.v1` children, switching that route to a "compact"
recovery profile (`route_seat_compact_recovery`). This is a
pre-existing, seat-independent self-healing path for ordinary model
flakiness (CLAUDE.md's own documented failure mode: a reasoning model
can burn its output on malformed structure). If a run stops
(`budget_exhausted`) with one of these decompositions still in flight
(some atomic children completed, others not yet attempted), a later
`deepreason --root <run> continue` can crash trying to resume it:

```
error: "unknown critic task"
error_type: "NonConjectureRecoveryAuthorityError"
state: "failed"
stop_reason: "operational_failure"
```

**Traced to** `src/deepreason/workflow/nonconjecture_recovery.py:644`:

```python
def _criticism_contract(harness, manifest, item, preparation, payload):
    _authority(payload.get("schema") == "criticism.semantic-task.v1", "unknown critic task")
```

The recovered `run-result.json` (`model_execution.contract_decompositions`)
shows the pending item at resume time was an ATOMIC child of the
original `batch-critic.v2` call (`atomic_contract_id:
"critic.atomic-target.v1"`, two sibling children already
`terminal_status: "completed"`). `_criticism_contract` is written for
the top-level batch contract's own payload shape
(`criticism.semantic-task.v1`); the most likely explanation, from
reading the surrounding dispatch code, is that resuming a
partially-decomposed batch routes the atomic child's own (different)
payload schema through the handler built for the batch, which then
correctly refuses it as unrecognized — the resume path does not know
how to hand a mid-decomposition item back to the right handler.

**Not a `--seat` interaction:** nothing in the failing function
branches on seat bindings; the crash is on `argumentative_critic`,
which is bound to the same default endpoint regardless of which group
(`coder` or `conjecture`) the operator's `--seat` flag targets in this
tranche's runs. This is a general harness defect in the
compact-recovery resume path, found incidentally by this tranche's live
run, not a consequence of role-seat separation.

**Consequence:** a `continue` on a run stopped mid-decomposition is not
safe to assume will succeed just because `stop_reason` says
`budget_exhausted`/resumable — it can instead crash the run into a
terminal `failed` state, losing the chance to reach a clean stop or
gather further seat-bindings evidence on that root. The affected root
must be retired (never edited) and re-attempted from a fresh identity.

**Not fixed here, on purpose:** `src/` stays byte-untouched this
tranche (live-run rule). The right fix belongs to whoever owns
`nonconjecture_recovery.py`'s dispatch-by-contract logic, and needs to
decide the right resume semantics for a partially-decomposed batch
(re-derive the correct child handler? refuse resume and require a fresh
attempt of the whole batch? something else) — a design question, not
just a bug-swat.

**Ready-to-send prompt:** "`deepreason --root <run> continue` can raise
`NonConjectureRecoveryAuthorityError('unknown critic task')`
(`src/deepreason/workflow/nonconjecture_recovery.py:644`,
`_criticism_contract`) when resuming a run that stopped with an
in-flight `route_seat_compact_recovery` decomposition of a
`schema_exhausted` `argumentative_critic` batch — two atomic children
completed, more pending, when `continue` tried to resume. Diagnose the
correct resume semantics starting from `dr-set-goal` with this
PARKED.md's P3 entry (full repro context: run
`experiments/2026-08-08-live-two-seat-ab-s6/home-s6/runs/failed-epoch1-run-8c77c6588485304d1f73416318c62949`,
retired but not deleted, as a live reproduction fixture) as the
starting diagnosis."

## In-flight note

The re-run reuses `home-s6/` (same `DEEPREASON_HOME`). It does NOT get
a fresh run identity purely from the seat-group change (P2, above,
corrects the opposite assumption originally written here) — the
work-around is a distinguishing question text instead. Its new run
root is committed only after the ladder exits and `verify_root` has
judged it — never mid-append, per this program's own established rule
(`DR-SEAM-harness-x-verification`'s torn-tail concern).
