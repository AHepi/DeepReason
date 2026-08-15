<!-- DR-SUB-rules -->
Verified-at: 546544b5
Verify: python -m pytest tests/test_relapse_domains.py tests/test_criticism_authority.py tests/test_crit_batch.py tests/test_act.py tests/test_vision.py -q
Owns: src/deepreason/rules/
Seams: DR-SEAM-adjudication-x-rules, DR-SEAM-capabilities-x-rules, DR-SEAM-evaluation-x-rules, DR-SEAM-llm-x-rules, DR-SEAM-ontology-x-rules, DR-SEAM-rules-x-scratch, DR-SEAM-rules-x-workflow, DR-SEAM-scheduler-x-rules
Seams-undocumented: authority x rules, harness x rules, manifest x rules

# The rules — the epistemic moves: conjecture, criticism, spawn, warrant

## What it is

`rules/` is where a provider call, a program verdict, or a browser run becomes
an *epistemic move*: a candidate admitted to the graph, an attack edge, a new
open problem. Every module here takes a live `harness` as its first argument and
calls back into it to commit; nothing here writes the log, computes a label, or
decides a status — it constructs the records that make the harness do so. That
asymmetry is the design: the rules answer "what may be proposed and what may be
attacked", `adjudication/` answers "what therefore stands", and neither can
reach into the other. The package is duck-typed on the harness rather than
importing it, so the dependency arrow points one way only and every rule is
testable against a fake.
`check: ! grep -rqE "deepreason\.(harness|adjudication)|from deepreason import [^#]*\b(harness|adjudication)\b" --include=*.py src/deepreason/rules/ && ! grep -rqE "deepreason\.rules|from deepreason import [^#]*\brules\b" --include=*.py src/deepreason/adjudication/ src/deepreason/harness.py`

Because most of this package's work is agreeing with a neighbour, the `Seams:`
header above is load-bearing: every seam document that names `DR-SUB-rules` as a
side must be listed there, or a reader routing through the map silently misses
one side of the change they are making.
`check: for d in docs/map/SEAM-*.md; do grep -q "^Sides:.*DR-SUB-rules" "$d" || continue; id=$(sed -n '1s/.*\(DR-SEAM-[a-z0-9-]*\).*/\1/p' "$d"); grep -q "^Seams:.*$id" docs/map/SUB-rules.md || exit 1; done`

The moves are unequal on purpose. A demonstrative warrant (a program verdict, a
counterexample that was RUN, a browser failure) changes status under every
configuration; a prose case can only be observed or routed into a defended
trial, and never against a target that formal evaluation already backs.
`Config.ARGUMENTATIVE_AUTHORITY` selects which — the manifest may not, because
that would move every qualification subject digest (`DR-INV-frozen-surfaces`).

## Seams

| Side | Status | What the agreement is (one line) |
|---|---|---|
| `DR-SEAM-adjudication-x-rules` | documented | the rules construct attackable objects; adjudication alone decides what they do to the graph |
| `DR-SEAM-capabilities-x-rules` | documented | a capability proposal is filed only from inside a conjecture turn, only as semantic intent the model authored |
| `DR-SEAM-evaluation-x-rules` | documented | evaluation answers exactly one question for the rules — can a machine settle this commitment, and what does it say |
| `DR-SEAM-llm-x-rules` | documented | a rule decides what to ask and what the answer means; `llm/` decides how it is asked and refuses anything the answer may not contain |
| `DR-SEAM-ontology-x-rules` | documented | the ontology lends the rules a vocabulary and keeps the right to define it |
| `DR-SEAM-rules-x-scratch` | documented | the scratchpad offers `conj` a bounded, single-use view of the model's own prior thinking; criticism receives none of it, structurally |
| `DR-SEAM-rules-x-workflow` | documented | `rules/` decides what may be proposed and attacked; `workflow/` decides by what recorded authority a provider may be asked |
| `DR-SEAM-scheduler-x-rules` | documented | the scheduler decides what is worked on, by whom, how often; the rules decide what that work means epistemically |
| authority x rules | undocumented | real: `rules/crit.py` is jointly `Owns:`-listed by `DR-CON-authority` — the manifest-word-to-Config-word translation (`_resolve_authority`) lives here |
| harness x rules | **deliberately absent** | this document's own top-level check proves it: `rules/` never imports `harness` (or `adjudication`) — the package is duck-typed on the harness rather than importing it, so the dependency arrow points one way |
| manifest x rules | **deliberately absent** | confirmed from the manifest side too: `DR-SUB-manifest`'s own exclusion-list check names `rules` explicitly among what it never imports |

## Entry points

- `conj.conj` — the conjecture rule. Gated on a registered problem, renders the
  conjecturer pack, compiles each candidate's interface from the problem's
  criteria, runs the anti-relapse gate, and commits the survivors in one
  `register_batch`. Dispatches by manifest `schema_version` (v4/v5/v6 turn
  contracts, plus the v6 atomic-candidate fallback).
- `conj.root_problem_family` — the provenance-root key anti-relapse domains are
  scoped by; delegates to the scheduler's `problem_family_key`.
- `crit.crit_program` — evaluate every evaluable commitment on a target and
  register one demonstrative critic per FAIL. No LLM.
- `crit.crit_fuzz` — deterministic property fuzzing: enumerate gate-valid inputs
  from the spec generator and every ACCEPTED experimenter generator, then from
  active proposed properties. No LLM.
- `crit.try_counterexample` — the critic's grounded recourse: admit a proposed
  input through the property oracle's gate, RUN the target, and mint a
  content-addressed counterexample commitment iff the property is violated.
  Returns `(critic | None, deterministic reason)`; the reason is echoed back on
  retry.
- `crit.crit_argumentative`, `crit.crit_argumentative_batch` — one prose case
  against one target, or one call over K targets (§14). Same warrant structure
  either way; batching is a call-shape optimisation, not an epistemology.
- `spawn.spawn`, `spawn.scan_spawns` — mint a new problem, and the idempotent
  post-registration sweep over every structural trigger. Problem ids are
  deterministic, so rescans are free.
- `warrants.register_fail_warrant` — the single constructor for the
  (attackable ν, DEMONSTRATIVE `w:<κ>:<target>`, critic artifact) triple. Eight
  modules call it, from twelve call sites; nobody hand-builds the triple —
  `WarrantType.DEMONSTRATIVE` is constructed in this one file and nowhere else.
- `warrants.execution_backed`, `warrants.formally_backed`,
  `warrants.verdict_on_record` — the supremacy and duplicate-verdict guards.
- `guards.anti_relapse.check` — the mandatory pre-commit gate: hash, then
  domain-scoped semantic trigger, then battery equivalence. Returns
  `(admit, reason)`.
`check: for s in conj root_problem_family; do grep -q "^def $s(" src/deepreason/rules/conj.py || exit 1; done; for s in crit_program crit_fuzz crit_argumentative crit_argumentative_batch try_counterexample; do grep -q "^def $s(" src/deepreason/rules/crit.py || exit 1; done; for s in spawn scan_spawns; do grep -q "^def $s(" src/deepreason/rules/spawn.py || exit 1; done; for s in execution_backed formally_backed register_fail_warrant verdict_on_record; do grep -q "^def $s(" src/deepreason/rules/warrants.py || exit 1; done`

- `synth.synthesize` — the crossover operator: propose one relation artifact for
  a connection/integration problem, then let it face the ordinary loop.
- `vision.crit_vision` — a multimodal critic that LOOKS at recorded screenshots
  and mounts an ARGUMENTATIVE case.
- `act.needs_browser_run`, `act.run_browser_evidence`, `act.browser_evidence` —
  run an app candidate in a real browser ONCE per (candidate, commitment) and
  materialize the outcome as import-role evidence artifacts.
- `experiment.propose_generators`, `experiment.propose_properties` — the system
  designing its own experiments and its own ground truth; each proposal is an
  ordinary artifact adjudicated on arrival.
- `experiment.accepted_generators`, `experiment.active_properties`,
  `experiment.promoted_properties` — what is currently live for `crit_fuzz`.
- `guards.anti_relapse.relapse_domain`, `record_domain`, `recorded_domains`,
  `verdict_vector` — compile, persist and re-read a candidate's comparison scope.
`check: for s in propose_generators propose_properties accepted_generators active_properties promoted_properties relevance_trial; do grep -q "^def $s(" src/deepreason/rules/experiment.py || exit 1; done; for s in check relapse_domain record_domain recorded_domains verdict_vector; do grep -q "^def $s(" src/deepreason/rules/guards/anti_relapse.py || exit 1; done; grep -q "^def synthesize(" src/deepreason/rules/synth.py || exit 1; grep -q "^def crit_vision(" src/deepreason/rules/vision.py || exit 1; for s in browser_evidence needs_browser_run run_browser_evidence; do grep -q "^def $s(" src/deepreason/rules/act.py || exit 1; done`

`refl.refl` is declared and raises `NotImplementedError`: rule-artifacts are in
the spec, not in the code. Do not describe it as working.
`check: grep -q "raise NotImplementedError" src/deepreason/rules/refl.py`

## State it owns

Almost nothing durable, deliberately. Every epistemic record — artifacts,
warrants, problems, commitments, `Measure` receipts — is handed to the harness,
which owns placement and lifecycle (`DR-SUB-harness`).

The one exception is `relapse.log.jsonl` under the run root: the anti-relapse
gate's **operational** log (domain records, degraded-gate and structural-only
receipts, near-miss diagnostics, block receipts naming the prior's refuter ids).
It is append-only, fsynced, skipped on read-only harnesses, and deliberately NOT
the epistemic log — gate telemetry must not perturb the scheduler's
event-sequence policy. `recorded_domains` still backward-reads the short-lived
`Measure`/event-input encoding that development builds emitted. This is the only
place in the whole package that touches a file.
`check: test "$(grep -rlE 'path\.open|write_text|write_bytes|read_text|read_bytes|\bopen\(' --include=*.py src/deepreason/rules | wc -l)" -eq 1 && grep -q '_RELAPSE_LOG = "relapse.log.jsonl"' src/deepreason/rules/guards/anti_relapse.py && grep -q 'os\.fsync' src/deepreason/rules/guards/anti_relapse.py && grep -q 'if getattr(harness, "_read_only", False)' src/deepreason/rules/guards/anti_relapse.py`

In memory: `crit.QUARANTINE_TICK` is a module-level counter the scheduler
snapshots so a fuzz sweep does not mark a target clean when the oracle was
merely unavailable. It is derived from deterministic control flow, so it is
replay-safe; it is not persisted.
`check: grep -q "^QUARANTINE_TICK = \[0\]" src/deepreason/rules/crit.py && grep -q "QUARANTINE_TICK" src/deepreason/scheduler/scheduler.py`

Every `Measure` tag this package emits (`arg-crit`, `scrutiny`, `gate:`,
`conj-noregister`, `synth-noregister`, `vision-crit`, `browser-pass`, …) must be
registered in `src/deepreason/signals.py`, which is AST-scanned by the gate.
`check: for tag in arg-crit arg-crit-overridden-by-execution scrutiny conj-noregister synth-noregister "gate:" vision-crit browser-pass; do grep -q "\"$tag\"" src/deepreason/signals.py || exit 1; done && python -m pytest tests/test_signals.py -q`

`scan_spawns` covers seven of the nine `SpawnTrigger` values. `SEED` is the
operator's; `AUDIT_CRITIC` is raised by the response ladder (§11.4), not here.
`check: for t in SUCCESSOR DISCRIMINATION REMOVE_ARBITRARINESS EXPLANATION_DEBT CONNECTION RESEARCH INTEGRATION; do grep -q "SpawnTrigger.$t" src/deepreason/rules/spawn.py || exit 1; done && test "$(python -c 'from deepreason.ontology import SpawnTrigger; print(len(list(SpawnTrigger)))')" -eq 9 && ! grep -qE "SpawnTrigger\.(SEED|AUDIT_CRITIC)" src/deepreason/rules/spawn.py`

## Where to change what

| To change... | Edit | Test |
|---|---|---|
| When a new problem is spawned, or add a trigger | `scan_spawns` in `rules/spawn.py`, plus `SpawnTrigger` in `ontology/problem.py` | `tests/test_harness_fixes.py::test_connection_problem_pins_lineage_ref_commitment` |
| What a successor / remove-arbitrariness problem inherits from its parent | the `rsplit("Original problem: ")` and `criteria=parent.criteria` clauses in `scan_spawns` | `tests/test_chaos_invariants.py::test_successor_descriptions_do_not_nest` |
| What prose criticism may refute | `formally_backed` in `rules/warrants.py` — consumed by `informal/trial.py`, NOT by the criticism rule | `tests/test_prose_refutation_boundaries.py::test_formal_backing_covers_the_whole_formal_set_not_only_execution` |
| Whether a sustained prose case changes a status or is only recorded | `_resolve_authority` / `_TRIAL_MODES` in `rules/crit.py` and `Config.ARGUMENTATIVE_AUTHORITY` — never the manifest (`DR-INV-frozen-surfaces`) | `tests/test_criticism_authority.py::test_observe_only_no_status_change` |
| Which candidates the anti-relapse gate blocks, or the scope it compares within | `RelapseDomain.compatible` and `check` in `rules/guards/anti_relapse.py` | `tests/test_relapse_domains.py::test_archived_gemma_shape_scopes_battery_equivalence` |
| Counterexample admission, or the deterministic reason echoed on retry | `try_counterexample` in `rules/crit.py`; retry count is `Config.CX_RETRY_MAX` | `tests/test_criticism_authority.py::test_execution_counterexample_still_refutes_under_observe_only` |
| The shape of every demonstrative fail warrant (ν, id scheme, critic wiring) | `register_fail_warrant` in `rules/warrants.py`, once — all thirteen call sites, in nine modules, inherit it | `tests/test_act.py::test_fail_registers_demonstrative_warrant` |
| Which generators or properties `crit_fuzz` probes with | `accepted_generators` / `active_properties` / `promoted_properties` in `rules/experiment.py` | `tests/test_experiment.py::test_refuted_generators_are_never_used` |
| When a proposed property earns promotion | `promoted_properties` (age + attack-survival-or-witness) and `population_supports` in `rules/experiment.py` | `tests/test_experiment.py::test_fuzz_kills_trap_with_a_proposed_generator` |
| The conjecture turn contract version or its dispatch | the `active_v4` / `active_v5` / `active_v6` branch in `conj`, against `llm/wire.py` contracts. Within `active_v6`, `configured_turn_contract` (P-CEPP-1) reads the manifest's own configured `conjecturer.turn.v6`/`v7` value once and threads it through `expected_contract`, `effective_contract`, and the atomic-decomposition bookkeeping, rather than five independent hardcoded literals | `tests/test_v6_conjecture_component_atomicity.py`, `tests/test_v6_transaction_qualification.py::test_live_v7_conjecture_dispatch_mints_a_v7_contracted_commitment` |
| Browser evidence or the visual critic | `run_browser_evidence` in `rules/act.py`; `crit_vision` in `rules/vision.py` | `tests/test_act.py::test_overrun_is_a_spec_defect_not_a_refutation`, `tests/test_vision.py::test_supremacy_boundary_in_process_oracle_blocks_visual_argument` |
| Giving criticism any scratchpad context | refused by contract — see `DR-SEAM-rules-x-scratch` | `python -m pytest tests/test_prose_refutation_boundaries.py -k scratch` |

`check: python -m pytest tests/test_relapse_domains.py tests/test_criticism_authority.py tests/test_harness_fixes.py::test_connection_problem_pins_lineage_ref_commitment tests/test_harness_fixes.py::test_remove_arbitrariness_carries_root_description_and_criteria tests/test_chaos_invariants.py::test_successor_descriptions_do_not_nest tests/test_experiment.py::test_refuted_generators_are_never_used tests/test_experiment.py::test_fuzz_kills_trap_with_a_proposed_generator tests/test_act.py::test_fail_registers_demonstrative_warrant tests/test_act.py::test_overrun_is_a_spec_defect_not_a_refutation tests/test_vision.py::test_supremacy_boundary_in_process_oracle_blocks_visual_argument -q`
`check: python -m pytest tests/test_prose_refutation_boundaries.py -q -k "scratch or formal_backing or structural_program or execution_guard" && test "$(grep -rl 'register_fail_warrant(' --include=*.py src/deepreason | grep -vc 'rules/warrants.py')" -eq 9 && test "$(grep -rn 'register_fail_warrant(' --include=*.py src/deepreason | grep -vc '^src/deepreason/rules/warrants.py:')" -eq 13 && test "$(grep -rl 'WarrantType.DEMONSTRATIVE' --include=*.py src/deepreason)" = "src/deepreason/rules/warrants.py"`

## Traps

- **The two supremacy guards are not interchangeable, and they sit in different
  files.** `crit.py` consults `execution_backed` (narrow) because its guard also
  decides whether a case is RECORDED as scrutiny; `informal/trial.py` consults
  `formally_backed` (wide) because its guard decides a STATUS. Widening the
  criticism rule's guard to match the trial's deletes scrutiny evidence for
  every target carrying a passing problem criterion — and the criteria are
  instantiated into every candidate's interface. See `DR-INV-frozen-surfaces`.
`check: grep -q "formally_backed" src/deepreason/informal/trial.py && ! grep -q "formally_backed" src/deepreason/rules/crit.py`
- **Evaluability is not backing.** `formally_backed` requires SUBSTANTIVE
  commitments because `program:` checks can be model-authored (safe skeleton
  compilation turns a conjecturer's own forbidden cases into commitments). Were
  mere evaluability enough, a candidate could attach `program:json-wf` — which
  passes for anything well-formed — and immunise itself against all criticism.
  `measures/reach.py::_substantive` is the shared predicate; keep them one.
`check: grep -q "_substantive" src/deepreason/rules/warrants.py && grep -q "def _substantive" src/deepreason/measures/reach.py`
- **Successor descriptions nested the whole ancestor chain.** Observed live at 7
  levels deep with 52/70 problems multi-nested, compounding pack size every
  refutation generation. The `rsplit("Original problem: ", 1)[-1]` is the fix and
  is load-bearing at any depth. The symmetric failure on the other side —
  dropping the parent description entirely — starved the generator of the
  format contract and bred prose that `skeleton_wf` refuted, cascading
  successors. Both remove-arbitrariness and successor carry the ROOT
  description; a 200k resume where `ra:` had no anchor wandered into unrelated
  abstract mathematics.
- **A degraded anti-relapse gate must fail OPEN, with a receipt.** Missing
  domain, embedder, or `NEAR_DUP_EPS` degrades to hash-only and appends a
  `relapse-gate-degraded` record; the bronze run's gate instead compared every
  refuted prior globally and closed the search. Likewise a battery made only of
  structural well-formedness programs establishes no equivalence (RC2) — those
  pass on every valid candidate, so they cannot distinguish ideas.
`check: grep -q "admitted-degraded:" src/deepreason/rules/guards/anti_relapse.py && grep -q "relapse-structural-only" src/deepreason/rules/guards/anti_relapse.py`
- **A gate block is a block; a content duplicate is a dedupe.** They are
  different outcomes with different receipts, and conflating them makes the gate
  adjudicate — forbidden by §0. Blocks emit a `gate:<reason>` `Measure` and
  register no commitments and no `Register` event.
- **Promotion by neglect.** A conjectured checker once survived 14 quarantines
  untouched — no critic read it, no candidate satisfied it — aged past
  probation, and then executed seven correct candidates (intervals/boot
  postmortem). `promoted_properties` now requires age AND either survived attack
  or a witness. Age alone is seniority masquerading as corroboration.
- **A crashing checker is not a refutation of the candidate.** `checker_crashed`
  and `crash_probe` exist because a conjectured checker that throws on the
  problem's own domain is at least as likely buggy as the code it judges
  (observed live: `for a, b in inp` on the args wrapper). A well-formed checker
  rejects; it does not raise.
- **A provider call must reach the log exactly once.** Every rule that may
  register nothing carries an `llm_pending`-style handoff: the call is attached
  to the registration event if one commits, and to a `Measure`
  (`conj-noregister`, `synth-noregister`, `arg-crit`, `scrutiny`) if none does.
  Get this wrong in either direction and replay and `eval_report` misreport real
  spend. Sandbox aborts and oracle overruns are the same shape of hazard on the
  deterministic side: they are *pending*, never clean, which is what
  `QUARANTINE_TICK` and `harness._oracle_pending` record.
- **`single_family_trial` is a `Config` value, not a manifest one.**
  `_POLICY_AUTHORITIES` is deliberately not extended with it:
  `CriticismPolicyV1.authority` is a frozen manifest `Literal`, and admitting a
  value there would move every qualification subject digest and make existing
  replay-valid roots read against a schema they were never written under.
`check: python -m pytest tests/test_prose_refutation_boundaries.py::test_the_new_mode_is_config_only_and_refused_by_the_manifest_path tests/test_prose_refutation_boundaries.py::test_the_single_family_authority_value_exists -q`
- **The criticism side's separation from the scratchpad is enforced by an AST
  walk, not a header grep.** A function-local `import deepreason.scratch...`
  inside `crit.py` would pass a naive check and still couple them. The single
  legitimate appearance of the word on that side is `scratch_fence_seq`, which
  is transactional ordering and reads no content.
`check: python -m pytest tests/test_prose_refutation_boundaries.py::test_the_criticism_rule_imports_no_scratch_module tests/test_prose_refutation_boundaries.py::test_the_criticism_rule_touches_scratch_only_as_an_ordering_fence -q && grep -q "ast.walk" tests/test_prose_refutation_boundaries.py && test "$(grep -c scratch src/deepreason/rules/crit.py)" -eq "$(grep -c scratch_fence_seq src/deepreason/rules/crit.py)"`
