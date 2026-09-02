# Fix: the v6 deferral gate consults a declared phase-to-contract table instead of `schema_version` alone

Guarantee restored: **a v6 legacy model phase dispatches when, and only when, the
seat it names holds a behavioural contract grant the declared table says that
phase requires — and defers with today's typed notice, byte-identical, when it
does not.**

Status: **DESIGN COMPLETE, ONE OPERATOR DECISION OUTSTANDING.** Everything below
is settled except which of two roads `hv-floor` takes (§7). The brief made that
an explicit STOP AND ASK, and the record says the stop is real rather than
procedural. No production code has been changed.

---

## 1. What the gate becomes

`src/deepreason/scheduler/scheduler.py:715-717`, today:

    manifest = self.run_manifest
    if manifest is None or manifest.schema_version != 6:
        return False
    # ... 33 lines that only RECORD; nothing below can change the answer ...
    return True

becomes:

    manifest = self.run_manifest
    if manifest is None or manifest.schema_version != 6:
        return False
    if seat_may_dispatch_legacy_phase(manifest, phase=phase, role=role):
        return False
    # ... the same 33 lines, unchanged ...
    return True

Three properties of that shape, each load-bearing:

- **The new consultation sits BEFORE the marker.** A phase that dispatches writes
  no `v6-model-phase-deferred.v1` event, which is what makes the soak's
  before/after difference observable in the record rather than only in memory.
- **The deferral branch is untouched.** Same marker string, same six-element
  `inputs` tuple, same `transaction-contract-unavailable` reason code, same
  dedup set, same diagnostics dict. **No record format changes.** A grant-less
  run's log is byte-identical to today's.
- **`schema_version != 6` still returns False first**, so the docstring's stated
  promise ("historical schedulers retain their byte-for-byte call paths") holds
  unchanged.

## 2. The declared table — new file, `src/deepreason/workflow/legacy_phase_contracts.py`

The brief requires the phase-to-grant mapping be "a declared table, VERSIONED and
readable, not scattered literals". One frozen mapping, one accessor, no literals
anywhere else:

    LEGACY_PHASE_CONTRACTS_VERSION = "legacy-phase-contracts.v1"

    @dataclass(frozen=True)
    class LegacyPhaseContractRow:
        phase: str                    # the gate's own first argument
        role: str                     # the seat the phase names
        contract_ids: frozenset[str]  # any one of these is sufficient authority
        dispatch: str                 # "v6_transactional" | "unconverted"

    LEGACY_PHASE_CONTRACTS = MappingProxyType({ ...one row per phase... })

    def seat_may_dispatch_legacy_phase(manifest, *, phase, role, seat=0) -> bool

**`dispatch` is not decoration and the fix is wrong without it.** Nine of the
eleven phases have no transactional dispatch path written yet. If the gate
returned False for them the moment a grant existed, they would dispatch UNBOUND
and trip exactly the fail-closed adapter guard the gate was written to prevent —
turning a silent inertness into nine killed roots. So `dispatch="unconverted"`
means "defer even with the grant", and the table is simultaneously the registry,
the conversion ledger, and the work list for the nine follow-up tranches.

The eleven rows, from the call-site census in DIAGNOSIS.md (phase, role,
contract set, dispatch):

| phase | role | contracts | dispatch |
|---|---|---|---|
| `hv-floor` | `variator` | `variator.direct.v1`, `variator.compact.v1` | see §7 |
| `hv-spot-check` | `variator` | `variator.direct.v1`, `variator.compact.v1` | `v6_transactional` |
| `premise-demarcation-variation` | `variator` | (variator pair) | `unconverted` |
| `paraphrase-audit-variation` | `variator` | (variator pair) | `unconverted` |
| `rubric-trial` | `judge` | `judgeruling.direct.v1`, `judgeruling.compact.v1` | `unconverted` |
| `pairwise-discrimination` | `judge` | (judge pair) | `unconverted` |
| `paraphrase-audit-judgment` | `judge` | (judge pair) | `unconverted` |
| `property-relevance-trial` | `judge` | (judge pair) | `unconverted` |
| `experiment-generator-authoring` | `conjecturer` | `conjecturer.turn.v6`, `conjecturer.atomic-candidate.v1` | `unconverted` |
| `property-design` | `property_designer` | none granted today | `unconverted` |
| `vision-criticism` | `vision_critic` | none granted today | `unconverted` |

Two contract ids per role because `wire_contract_for` resolves the id from the
seat's own PROFILE (`compact` -> `*.compact.v1`; `standard`/`frontier` ->
`*.direct.v1`), per seat, not from the manifest default. A table naming only
`variator.direct.v1` would silently fail every compact seat.

`seat=0` is not a simplification: the dispatch resolves its route through
`adapter.bound_v6_default_lease(role, 0)`, so seat 0 is the seat the call will
actually reach, and a grant on a seat the call never reaches is not authority for
that call. The parameter is explicit so the nine follow-ups cannot forget it.

The module reads the plan by DUCK TYPING (`.entries`, `.role`, `.seat`,
`.contracts`, `.contract_id`) and imports `run_manifest` **not at all** — no
import cycle, and no dependency on a frozen module's internals. It uses
`getattr(manifest, "route_seat_behavioral_capability_plan", None)`, which also
keeps the existing `SimpleNamespace` fixtures in
`tests/test_v6_scheduler_model_phase_deferral.py` working unchanged (§6).

## 3. The dispatch — generalising the existing recipe, not copying it

`informal/trial.py:61-272::_v6_transactional_trial_call` gains three keyword
parameters with today's values as defaults, and a public alias:

    task_payload_schema: str = "defended-trial-step.v1"
    trigger_prefix: str = "trial"
    reason_prefix: str = "trial"        # feeds the five `trial_*` reason codes
    ...
    v6_transactional_phase_call = _v6_transactional_trial_call   # public name

Every existing caller passes none of them, so trial behaviour — the judge canary
included — is byte-identical. That is the whole change to `trial.py`: about
twelve lines, no restructuring.

`measures/hv.py` then self-detects and dispatches, following the repo's own
established precedent rather than a new one. `crit_argumentative_batch` was
given exactly this treatment on 2026-08-10 (tranche
`adjudication-judge-seats-optins`, S13i), and `DR-SEAM-scheduler-x-rules`
records why it must be done this way: **the scheduler's call to a rule stays
keyword-free**, so the rule self-detects the bound manifest instead of being
handed one. Both `scheduler.py:1364` and `scheduler.py:2953` therefore keep
their current signatures untouched.

    def _v6_manifest(adapter):                    # mirrors trial.py:47-58
        if not getattr(adapter, "transaction_authority_required", False):
            return None
        return adapter.bound_v6_manifest()

    def _sample_edits(harness, adapter, artifact, k, *, manifest=None):
        ...
        if manifest is not None:
            output, _call = v6_transactional_phase_call(
                harness, adapter, manifest,
                role="variator", target_id=artifact.id, step="hv-variation",
                pack=pack, output_model=VariatorOutput,
                task_payload_schema="hv-variation-step.v1",
                trigger_prefix="hv", reason_prefix="hv",
            )
            llm_call = None          # the transaction is the accounting
        else:
            output, llm_call = adapter.call("variator", pack, VariatorOutput)

**`llm_call = None` under v6 is the correctness point, not a shortcut.**
`Harness.record_llm_calls`'s own docstring states the rule: *"Every call reaches
the log exactly once ... or replay and eval_report silently under-count real
spend."* Under v6 the transaction records the spend
(`record_provider_attempt` + `terminate(prompt_tokens=…, completion_tokens=…)`),
so attaching the same call to `event.llm` would DOUBLE-count it. `rules/crit.py`
solves this with `llm_already_recorded=(transactional_call is not None)` and sets
its pending call to `None`; this is the same move. Returning `None` from
`_sample_edits` makes all five downstream sites correct with **zero** edits to
them: `record_llm_calls` skips `None` by its own guard, `run_hv_floor:284` is
already `if llm_call is not None:`, and `record_measure(llm=None)` and
`register_fail_warrant(llm=None)` are both existing supported values.

`VariationSampler` (`hv.py:218`) keeps the `manifest=None` default and is
therefore untouched — `premise-demarcation-variation` stays deferred, as the
brief requires.

## 4. Frozen surfaces: NO CONTACT, argued rather than asserted

Both forecast stops were checked in DIAGNOSIS.md and re-checked against the
design:

- **No new contract id.** `wire_contract_for("variator", VariatorOutput, profile)`
  resolves to `variator.direct.v1` / `variator.compact.v1`, which already exist
  and are already granted by the compiler. Nothing is minted.
- **No new work kind.** The call reuses `WorkflowTaskKind.DEFENDED_TRIAL_STEP`.
  This is the operator's own instruction ("prefer the existing … contract and
  existing work kinds"), and it is also the honest choice: `trial.py:839-851`
  already dispatches the *identical* call — role `variator`, model
  `VariatorOutput` — under that kind, for the paraphrase spot-check. Adding a
  kind would additionally require a decision at
  `workflow/nonconjecture_recovery.py:52-61`, whose `_RECOVERABLE_TASKS` set
  does not contain `DEFENDED_TRIAL_STEP` either, so reuse inherits exactly the
  recovery treatment this call shape already has. The payload's own
  `schema` field carries `"hv-variation-step.v1"`, so the record still says
  truthfully what the call was; nothing validates that string against the kind
  (`grep` finds `"defended-trial-step.v1"` at exactly one site, its writer).
- **No qualification-battery change.** `cli/doctor.py:385-420` projects battery
  pairs from the manifest's plan. This fix READS that plan and adds no contract
  to any seat, so the pair set is unchanged and the subject digest cannot move.
- **`run_manifest.py` is read, never written.** Worth stating explicitly because
  the *other* road was tempting: widening the grant compiler so v6 runs get the
  variator grant by default. That road is closed on its own evidence — the plan
  is RE-DERIVED and compared on every manifest reload
  (`run_manifest.py:1595-1604`, raising
  `V6_ROUTE_SEAT_BEHAVIORAL_CAPABILITY_PLAN_MISMATCH`), so changing the compiler
  would invalidate every committed v6 root on load. Reader-side is not merely
  preferred here; it is the only road that does not break the corpus.

`python tools/blast_radius.py` is run before the implementing commit and its
verdict pasted into VERIFY.md, so this claim is measured and not just argued.

## 5. Change sites (exhaustive)

| file | lines | what changes |
|---|---|---|
| `src/deepreason/workflow/legacy_phase_contracts.py` | ~75 new | the versioned table, the row dataclass, `seat_may_dispatch_legacy_phase` |
| `src/deepreason/scheduler/scheduler.py:715-718` | ~4 | one consultation before the marker block; one deferred import |
| `src/deepreason/informal/trial.py:61-120` | ~12 | three keyword parameters with today's defaults; public alias |
| `src/deepreason/measures/hv.py` | ~28 | `_v6_manifest` helper; `_sample_edits` gains `manifest=`; `hv_spot_check` (and `run_hv_floor`, per §7) self-detect and pass it |

Estimated `src/` diff: **~119 lines across 4 files**, within GOAL.md's 150-line
budget. Riding in the same commit, outside that count and required by repo law:

- `tests/test_hv_v6_reachability.py` (new, ~190 lines) — §6
- a grant-bearing and a no-grant cycle-soak case — §6
- `docs/map/SUB-scheduler.md`, `docs/map/SEAM-scheduler-x-workflow.md`,
  `docs/map/SUB-evaluation.md` — updated claims, checks and Traps
- `docs/map/REC-give-a-legacy-phase-v6-transactional-dispatch.md` (new)
- `docs/ERRATA.md` — one entry

**One thing deliberately NOT done, and the reason is engineering rather than
budget.** The brief asks for "one helper the scheduler can use for any legacy
phase". The right long-term home for
`v6_transactional_phase_call` is `src/deepreason/workflow/`, since the nine
follow-up phases live in `rules/`, `scratch/` and `informal/audits.py` — three
different subsystems from `measures/`. Moving it there is 212 lines of pure
relocation with no behavioural content. Mixing a 212-line move into the same
commit as a behavioural change makes the behavioural change unreviewable, and it
would take this tranche to ~330 changed lines. So the helper is generalised IN
PLACE (`informal/` and `measures/` are both owned by `DR-SUB-evaluation`, so no
seam is crossed by hv importing it), and the promotion is PARKED as P6 — a pure
move a reviewer can verify by diffing, in its own commit, before the first
follow-up that needs it from outside `DR-SUB-evaluation`.

## 6. Regression artifact and the tests

**Inverts:** `experiments/2026-09-02-defect-hv-v6-reachability/repro_gate.py`
must go from exit 0 to exit 1, with `_defer(...)` returning `False/False` on the
grant-bearing manifest and `True/True` on the control. That exact pair of
assertions lands in `tests/` as the regression.

`tests/test_hv_v6_reachability.py`, new:

1. `test_a_granted_variator_seat_dispatches_hv_under_v6` — the inverted repro,
   built on the real committed grant-bearing manifest.
2. `test_an_ungranted_variator_seat_still_defers_with_the_same_typed_notice` —
   the control, asserting the six-element `inputs` tuple element by element so a
   changed reason code or a reordered tuple fails.
3. `test_an_unconverted_phase_defers_even_when_its_seat_holds_the_grant` — the
   nine-phase safety property from §2. Mutation-proven by flipping one row's
   `dispatch` in the test and asserting the gate's answer flips.
4. **The architecture test the modularity law requires**, in two limbs, because
   one limb alone is not failable enough:
   - *behavioural*: two manifests differing ONLY in the grant must get different
     answers from the gate. Goes RED if the consultation is deleted **or made
     inert** — which an AST check alone would miss.
   - *structural*: `inspect.getsource(_defer_untransactional_v6_phase)` must
     contain the call to `seat_may_dispatch_legacy_phase`, and the phase-name
     string literals must appear in the registry module and NOT in
     `scheduler.py` outside the eleven call sites. Goes RED when a consumer
     bypasses the interface — the law's own words.
5. `test_the_registry_covers_every_call_site` — parses `scheduler.py`, extracts
   the first positional argument of all eleven `_defer_untransactional_v6_phase`
   calls, and asserts the set equals the registry's keys. A twelfth call site
   added without a row fails here rather than silently dispatching or silently
   deferring.
6. `test_hv_changes_no_status_on_a_fixed_stub` — §7's evidence guard.

**Soak cases.** No committed case can exercise the grant-bearing path, because
`run_manifest.py:2059-2065` mints the variator grant only under
`criticism_policy.authority == "defended_trial"`, and all five committed cases
lack it (REPRO.md). Measured this session, the three `Config` fields that produce
the grant are `LEGACY_CRITICISM_ENABLED=False`,
`ADJUDICATION_STATUS_AUTHORITY_ENABLED=True`,
`ENGAGED_CRITICISM_AUTHORITY="defended_trial"`. A committed
`run-config.yaml` in this tranche directory carrying those three, plus a sibling
identical but for `LEGACY_CRITICISM_ENABLED=True`, gives the grant/no-grant pair
GOAL.md's criteria 1 and 2 need. `SoakCase`'s own contract is honoured: the case
READS the committed config and restates nothing.

**Existing tests at risk** — from `grep`, each classified:

| test | verdict |
|---|---|
| `test_v6_audit_vision_and_lazy_hv_defer_without_dispatch` | **KEEPS PASSING, unchanged.** Its `_scheduler()` helper builds `SimpleNamespace(schema_version=6, criticism_policy=None)` with no plan attribute at all, so `getattr(..., None)` yields no grant and every phase still defers. This is why the accessor must use `getattr` and not attribute access — the alternative raises `AttributeError` and turns a green test red for the wrong reason. |
| `test_v6_pairwise_discrimination_never_reaches_unbound_judge` | **KEEPS PASSING.** `pairwise-discrimination` is `dispatch="unconverted"`, so it defers whatever the grant says. |
| `test_legacy_argumentative_criticism_dispatches_under_v6` | **KEEPS PASSING.** Argumentative criticism does not go through this gate at all. |
| `test_v6_deferral_marker_is_durable_bounded_and_resume_deduplicated` | **KEEPS PASSING.** Its phase is the literal `"phase"`, absent from the registry, so it defers. |
| `tests/test_v6_defended_trial_transaction_wiring.py` | **KEEPS PASSING.** `trial.py`'s three new parameters default to today's values. |
| `tests/test_signals.py` | **KEEPS PASSING**, and keeps its existing hole — see PARKED P4. |

No fixture depends on the defective behaviour, so none is updated. That is a
consequence of the design, not luck: the gate's new branch only ever turns a
`True` into a `False`, and only for a manifest carrying a plan that no existing
fixture builds.

## 7. THE ONE OPEN DECISION — `hv-floor` mints refutations, and the brief's own stop fires

**The brief's constraint and the brief's goal disagree, and the record says the
constraint's premise is the part that is wrong.** The constraint reads: *"hv is
an EFFICIENCY/ranking measure … Nothing in this change may alter what counts as
accepted, refuted, or warranted."* The goal names both producers.

Measured, not inferred: the two producers are not the same kind of thing.

- `hv_spot_check` (`hv.py:170`) writes `state.hv` and nothing else. Pure
  ranking. The constraint holds for it exactly as written.
- `run_hv_floor` (`hv.py:267`) evaluates a pinned `hv-floor` criterion and, when
  `hv < hv_min`, calls `register_fail_warrant(...)` — **which refutes the
  target.** It is a criticism-ladder criterion evaluator, not a ranking measure.

And the criterion is not opt-in. `rules/spawn.py:150-172` pins
`hv_floor_commitment(config)` onto **every connection problem** the harness mints
("Connection: isolation floor (§7 L2); hv-floor + lineage-ref pinned as
criteria"). So converting `run_hv_floor` changes refutation outcomes on ordinary
runs, with no configuration having asked for it.

Priced from the record, read-only:

| root | connection problems spawned | distinct artifacts whose `hv-floor` was deferred |
|---|---|---|
| `2026-08-12-live-grounded-extension-expansion/run` (grant present) | 53 | **95** |
| `2026-08-25-poietics-program/run` | 30 | 42 |
| `2026-08-27-pc2b-symmetric-reasoning/run` | 0 | 0 |

On the grant-bearing root, 95 artifacts would have faced a criterion that can
refute them. That is the size of the change, and it is why this is a real stop
rather than a procedural one.

**Two roads.**

**Road A — convert both producers (the goal's literal scope).** `hv-floor`'s
criterion starts being evaluated again. Argument for: the criterion is pinned by
the harness's own §7 design, the gate has been silently suppressing an
evaluation the spawn rule explicitly asked for, and today the deferred criterion
is *completely inert* — it neither refutes nor lowers coverage, because an
`hv-floor` commitment is not registry-evaluable and `pareto_scores`' coverage
denominator does not count it. So a pinned criterion currently costs nothing and
proves nothing. Cost: refutation outcomes change on any run that spawns
connection problems, and no offline instrument can tell you in advance whether
those refutations are correct. Test 6 becomes a bounded claim rather than the
one the brief asked for: *no status moves except on artifacts carrying an
`hv-floor` commitment, and only from that commitment's own FAIL verdict.*

**Road B — convert `hv-spot-check` only; leave `hv-floor` as a registry row with
`dispatch="unconverted"`.** GOAL.md's machine criteria all still pass:
`hv_spot_check` is a producer of `hv_set`, so "≥1 `hv_set` within 8 cycles" is
met, the frontier gets its second axis back, and the modularity law is satisfied
— `hv` becomes reachable by configuration and the architecture test can fail.
Test 6 is then the literal assertion the brief asked for: identical status sets,
grant or no grant. Cost: one of the eleven phases stays parked, and `hv-floor`
becomes the twelfth item on the follow-up list rather than the ninth.

**Recommendation: Road B, then Road A as its own one-step tranche.** The reason
is not caution about the code — the dispatch is identical either way and already
written. It is that Road A's *consequence* is epistemic and unmeasurable
offline: the only way to learn whether reinstated `hv-floor` refutations are
sound is a live run that produces some, and that is a run tranche, not a fix
tranche. Road B delivers the whole mechanism, the whole law-enforcing check, and
a measurable `hv`, while leaving the one decision that needs evidence to a
tranche that can gather it. Road A remains one table-row edit away, and the
follow-up prompt for it is already written in PARKED.md (P7).

Everything in §§1-6 is identical under both roads. Only the `hv-floor` row's
`dispatch` value differs.

## 8. Explicitly not changed

- **`capture/programs.py` and the Pareto sort.** Restoring `hv` gives the
  frontier a second axis; how coverage scores counterconditions is a separate
  defect (PARKED P2).
- **`reach`.** Ungated, deterministic, empirically zero. Untouched.
- **The nine other gated phases.** Registry rows only, `dispatch="unconverted"`.
  The `REC-` document turns each into a one-step follow-up (PARKED P1).
- **The grant-minting rule** (`run_manifest.py:2059-2065`). Frozen surface 4,
  and the re-derivation check makes the writer road corpus-invalidating (§4).
  PARKED P5.
- **The unregistered deferral signal.** PARKED P4.
- **Anything owned by the three concurrent windows** — `llm/providers.py`,
  `llm/split.py`, `application/text_runs.py`, `runtime/continuation.py`,
  `llm/endpoints.py`. None appears in §5.

## 9. Approval gate

GOAL.md classes this `defect`; the `src/` diff estimate is ~119 lines; no frozen
surface is contacted. On the orchestrator's own rule that is clear to proceed to
`dr-implement-fix` — **except** for §7, which the brief made a STOP AND ASK in
terms this design meets exactly ("any change that would alter
acceptance/refutation on a fixed stub"). The stop is therefore taken on the
`hv-floor` row only, with a recommendation, and everything else proceeds.
