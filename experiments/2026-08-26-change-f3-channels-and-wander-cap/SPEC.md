<!-- DR-TRANCHE-F3 -->
# Spec for: "turning research and, simulation and coding permanently on" + the wander cap

Traces: every item cites R/C numbers from REQUEST.md. Untraceable items are bugs.

Read REQUEST.md in full first, Amendment 1 included.

**Why this belongs in the REBUILD (R7, the one line the instruction asked for):**
a critic that can run a checker or a simulation produces DEMONSTRATIVE verdicts
— the only criticism class the anatomy program found doing real work — so the
three evidence-minting channels are not a convenience, they are the supply of
the only criticism that survives.

## The shape of the change

Two halves, and one law over both. H1 makes the three evidence-minting channels
default ON through a DECLARED CHANNEL REGISTRY rather than through scattered
env-var opt-ins. H2 ships the wander cap as a SELECTABLE, VERSIONED ALLOCATION
POLICY consumed only through its interface. Amendment 1's modularity law is
what makes both a registry rather than a pair of `if` statements: a new channel
or a new lineage policy enters by DECLARATION, and every knob either half
introduces is a `Config` field.

## Items

### H1 — the channels

**S1 (R1, R2, R3, R4, R18, C1, C2) — the channel registry.**
Files: `src/deepreason/channels.py` (new).
Before: channel enablement is three unrelated facts — simulation ON via
`v6_policy.engaged_simulation_policy`, research OFF unless
`DEEPREASON_RESEARCH_ALLOWLIST` names hosts, code-testing ungated and
undeclared anywhere.
After: one registry, on the signal-contract pattern. `ChannelDeclaration`
carries `id`, `mints` (what evidence the channel mints, in the operator's own
2026-08-14 terms), `default_enabled`, `toggle` (the `Config` field that turns
it off), `enforcement` (where that toggle is read) and `authority` (the ruling
that protects the channel). `CHANNEL_DECLARATIONS` declares exactly three —
`research`, `simulation`, `code-testing` — each `default_enabled=True`.
`DECOMMISSIONED = frozenset({"website"})` states C2 as a declared absence, so
the registry can be asked and answers "not a channel" rather than being silent.
`enabled(channel_id, config)`, `disabled_channels(config)` and
`unknown_channel_notices(config)` are the whole consumer interface.

    accept: python -c "
    from deepreason import channels
    from deepreason.config import Config
    c = Config()
    assert set(channels.CHANNEL_DECLARATIONS) == {'research','simulation','code-testing'}
    assert all(d.default_enabled for d in channels.CHANNEL_DECLARATIONS.values())
    assert all(channels.enabled(i, c) for i in channels.CHANNEL_DECLARATIONS)
    assert 'website' in channels.DECOMMISSIONED
    assert 'website' not in channels.CHANNEL_DECLARATIONS
    print('ok')" -> ok

**S2 (R4, R18) — the one toggle, and it is pure configuration.**
Files: `src/deepreason/config.py`.
Before: no per-channel setting exists.
After: `Config.CHANNELS_DISABLED: tuple[str, ...] = ()`. A channel is ON unless
its id is named here. ONE field for every channel present and future — a new
channel gets a toggle by registering, never by adding a `Config` field
(Amendment 1's "customizing it must not require editing code"). An id in the
tuple that names no declared channel is a typed `CompileNoticeV1`
(`CHANNEL_UNKNOWN`), never a refusal — the all-configurations law.

    accept: python -c "
    from deepreason import channels
    from deepreason.config import Config
    off = Config(CHANNELS_DISABLED=('research',))
    assert not channels.enabled('research', off)
    assert channels.enabled('simulation', off)
    n = channels.unknown_channel_notices(Config(CHANNELS_DISABLED=('nope',)))
    assert len(n) == 1 and n[0].code == 'CHANNEL_UNKNOWN'
    print('ok')" -> ok

**S3 (R1, R6, C1) — research defaults ON.**
Files: `src/deepreason/v6_policy.py`.
Before: `engaged_research_policy` returns a DISABLED policy unless
`DEEPREASON_RESEARCH_ALLOWLIST` is set.
After: it takes an optional `config` and returns an ENABLED policy whenever the
`research` channel is enabled, over `channels.DEFAULT_RESEARCH_ALLOWLIST` when
the env var names nothing. The env var keeps its exact meaning and still
overrides — a different allowlist is still a different qualification subject.
`engaged_inquiry_capability_policy` threads `config` to both channel-aware
builders and keeps its current signature working with `config=None`.

    accept: python -c "
    from deepreason.v6_policy import engaged_research_policy
    from deepreason.config import Config
    on = engaged_research_policy({}, config=Config())
    assert on.enabled and on.domain_allowlist
    off = engaged_research_policy({}, config=Config(CHANNELS_DISABLED=('research',)))
    assert not off.enabled and not off.domain_allowlist
    print('ok')" -> ok

**S4 (R2, R4) — simulation stays ON and gains its lawful OFF.**
Files: `src/deepreason/v6_policy.py`.
Before: `engaged_simulation_policy` always returns an enabled policy.
After: unchanged when the channel is enabled (byte-identical for both runner
profiles — this is the property the accept check pins); a disabled channel
returns the all-zero `SimulationCapabilityPolicyV1()`, which is a valid,
compiling policy and not a refusal.

    accept: python -m pytest tests/test_evidence_channels.py -q -k "simulation" -> 0 failed

**S5 (R3, R5, C1, C2) — code-testing is declared ON, and its always-on-ness is
CHECKED rather than assumed.**
Files: `src/deepreason/channels.py`, `tests/test_evidence_channels.py`.
Before: nothing declares that the code-testing channel exists or that it is on.
After: the registry declares it with `enforcement="unconditional"`, and a test
proves the claim two ways rather than asserting it: the execution program
classes are present in `programs.PROGRAMS`, and `programs.evaluate` runs a
`program:` commitment with no enablement consulted anywhere on the path. Its
`toggle` field records `CHANNELS_DISABLED` as the field a future off-switch
must read — see A3 for why this tranche ships no such switch, and PARKED.md P1
for the follow-up it becomes.

    accept: python -m pytest tests/test_evidence_channels.py -q -k "code_testing" -> 0 failed

**S6 (R5, C2) — the website stays decommissioned.**
Files: `tests/test_evidence_channels.py`.
Before: `tests/test_decommissioned_pipeline_stays_out.py` guards the pipeline;
nothing connects that guard to the channel registry.
After: a test asserts `"website" in channels.DECOMMISSIONED`, that no
declaration carries it, and that `enabled("website", config)` is False for
every configuration including one that names it in `CHANNELS_DISABLED`.

    accept: python -m pytest tests/test_evidence_channels.py tests/test_decommissioned_pipeline_stays_out.py -q -> 0 failed

**S7 (R6) — the qualification-digest cost, priced.**
Files: `experiments/.../VALIDATION.md` (the measurement), `DELIVERY.md` (the
report).
Measured at spec time, pasted under Measurements below: enabling research moves
the inquiry-capability policy digest, therefore the compiled manifest sha,
therefore every qualification subject digest built from the engaged preset.
The cost is one full requalification battery per `DEEPREASON_HOME` (~14 min,
~1160 calls, CLAUDE.md "Live runs") plus every committed test golden that pins
engaged-preset manifest bytes. Priced, not stopped, exactly as R6 directs.

    accept: VALIDATION.md contains the before/after subject digest pair and the
    count of goldens updated -> present


### S0 — the decision-to-dispatch verification (R20), done BEFORE any code

**Verdict: W7 is TRUE NOW. The connection is BROKEN on the current tree, and
E43's incident is not in conflict with that — the two are true at different
times.**

`Controller._apply_cap` writes exactly one thing: `endpoint.max_tokens`
(`controller.py`, "One seat's endpoint, never the role's whole ensemble").
`Adapter._completion_cap` — the ONE definition of the completion envelope a
dispatch books and is checked against — reads that value only when the route
declares NO qualified capacity:

    maximum = (
        lease.route.max_tokens
        if lease.route.context_window_tokens is not None
        else getattr(endpoint, "max_tokens", lease.route.max_tokens)
    )

Every qualified route declares `context_window_tokens`, so on every engaged run
the first branch is taken and the settled cap is never consulted. That is W7's
finding, re-derived from the current source rather than from its report (M4).

**Reconciliation with E43.** Both are true, in sequence, and the record dates
them. Before 2026-08-22 the endpoint's settled cap WAS what the firewall checked
— which is exactly why run `40e713b30a147dfc` died: the controller narrowed to
20 480, the route firewall demanded equality with 32 768, and the run ended at
cycle 2 with a typed `ROUTE_LEASE_MISMATCH`. E43's fix relaxed that check from
an identity to a CEILING, so a narrowing stopped being terminal. Then, on
2026-08-23, run `bb0455384ea09b5b` attempt 3 died because the preview and the
call each recomputed the cap and a controller settled the seat between them;
that fix made `_completion_cap` return the route ceiling. Each fix was right for
the failure in front of it. Their COMPOSITION severed the controller from the
wire — and, as W7 says, changed the failure mode from loud to silent.

**What makes the wiring safe now, and it is a fact about the current tree
rather than an argument.** The two defects the ceiling rule was standing in for
are BOTH already closed by other machinery that still stands:

* the mid-cycle divergence is closed by the RESERVATION READ-BACK — under a
  dispatch authorization `transport_limits["max_tokens"]` is
  `reservation_record.completion_bound_tokens`, CONSUMED, not recomputed
  (`adapter.py`, the comment that names the epoch-3 run). The cap is computed
  once at preview, booked, and read back. A second recompute is what broke; it
  is gone and this item does not restore it. (M6)
* the terminal-narrowing defect is closed by E43's ceiling in
  `EndpointLease.verify`: `cap > route.max_tokens` raises, `cap <=` passes
  (`firewall.py`). A narrowed cap is lawful today. (M5)
* the controller cannot propose above the seat's lease at all —
  `Controller._lease_ceiling` bounds `_propose` and `_apply_cap` both
  (`INV-signal-contract`'s last trap).

So the ceiling-only rule in `_completion_cap` is now the ONLY thing severing
the connection, and removing it re-arms nothing that killed a run.

**S19 (R21, R9) — wire the decision to the dispatch.**
Files: `src/deepreason/llm/adapter.py`.
Before: `_completion_cap` returns the route CEILING whenever the route declares
qualified capacity, so no controller decision reaches a dispatch.
After: it returns the seat's SETTLED cap BOUNDED BY that ceiling —
`min(endpoint.max_tokens or route.max_tokens, route.max_tokens)` on the
qualified branch, the unqualified branch untouched. The route ceiling still
binds absolutely (nothing can book above what qualification certified), the
booking is still computed once and consumed from the reservation, and a lawful
narrowing now travels to the wire. This is the smallest change that turns 47
inert decisions into 47 acting ones, and it is the same one-expression shape
the two prior fixes took.

    accept: python -c "
    from deepreason.llm.adapter import Adapter
    class R:
        max_tokens = 32768; context_window_tokens = 131072
    class L: route = R()
    class E: max_tokens = 8000
    assert Adapter._completion_cap(E(), L()) == 8000
    class W: max_tokens = 99999
    assert Adapter._completion_cap(W(), L()) == 32768
    print('ok')" -> ok
    accept: python -m pytest tests/test_v6_reservation_bound_authority.py tests/test_route_lease_maxtokens_tuning.py -q -> 0 failed
    accept: python -m pytest tests/test_controller_reaches_the_wire.py -q -> 0 failed

**S20 (R20, R21) — the regression that would have caught this, and keeps it
caught.**
Files: `tests/test_controller_reaches_the_wire.py` (new).
Before: nothing asserts that a controller decision changes what a dispatch
books; W5 had to measure 54 committed roots to discover it did not.
After: an offline test drives a controller decision through `_completion_cap`
on a QUALIFIED route and asserts the booked envelope equals the settled cap,
not the ceiling; a second asserts a settled cap ABOVE the ceiling still books
the ceiling; a third asserts the unqualified-route branch is unchanged; a
fourth drives `Controller.step()` on a stub and asserts the applied knob is the
number a following dispatch would book. Written to go RED on the exact
reversion — re-introducing the ceiling-only expression — rather than on a
rename.

    accept: python -m pytest tests/test_controller_reaches_the_wire.py -q -> 0 failed

**Ordering.** S0's verification is complete and recorded ABOVE, before any code,
as R20 requires. S19/S20 land in H2's FIRST commit, before the wander policy, so
the cap this tranche ships is connected to the wire on the day it is written
rather than joining the 47.

### H2 — the wander cap

**S8 (R8, R12, R18) — the floor knob and the policy selector.**
Files: `src/deepreason/config.py`, `src/deepreason/run_manifest.py`.
Before: no lineage budget-share knob exists; `INTEGRATION_BUDGET_SHARE` is the
only share knob and it governs reflexive housekeeping.
After: `Config.SEED_LINEAGE_BUDGET_FLOOR: float = Field(default=0.5, ge=0.0,
le=1.0)` — the FLOOR of worked cycles guaranteed to the operator-seeded
lineage — and `Config.LINEAGE_ALLOCATION_POLICY: str = "wander-cap.v1"`, which
selects the policy from the registry. Both get an unconditional
`data.pop` line in `_versioned_source_config_data`, per schema version, so no
qualification subject digest moves (frozen surface 4's own rule; see the
Frozen-surface contact forecast).

    accept: python -c "
    from deepreason.config import Config
    from deepreason.run_manifest import source_config_hash
    import json
    from tests.test_reusable_qualification import _manifest, _profile
    c = json.loads(_manifest(_profile()).engine_config_json)
    leaked = sorted(k for k in c if k in ('SEED_LINEAGE_BUDGET_FLOOR','LINEAGE_ALLOCATION_POLICY','CHANNELS_DISABLED'))
    assert not leaked, leaked
    h = [source_config_hash(Config(), schema_version=v) for v in (1,2,3,4,5,6)]
    assert h[0]==h[1] and h[2]==h[3]==h[4]==h[5]
    print('ok')" -> ok

**S9 (R9, R12, R18, C6) — the policy, as a declared interface with a registry.**
Files: `src/deepreason/wander.py` (new).
Before: nothing.
After: `LineageReading` (frozen: `cycles`, `seed_worked`, `other_worked`,
`floor`) is the whole input; `LineageDecision` (frozen: `policy_id`, `engaged`,
`share`, `floor`, `disclosure()`) is the whole output; `LINEAGE_POLICIES` is
the VERSIONED registry keyed by policy id, with `wander-cap.v1` shipped;
`decide(config, reading)` is the ONE entry point a consumer may call. The
scheduler consumes this and nothing else — never the policy function by name.
An unknown `LINEAGE_ALLOCATION_POLICY` falls back to the shipped default and
discloses; it never refuses (all-configurations law).
`wander-cap.v1`: `share = seed_worked / cycles` (1.0 before the first cycle);
`engaged = cycles > 0 and share < floor`. Efficiency only — the decision names
no artifact, no status and no warrant.

    accept: python -c "
    from deepreason import wander
    from deepreason.config import Config
    r = wander.LineageReading(cycles=10, seed_worked=3, other_worked=7, floor=0.5)
    d = wander.decide(Config(), r)
    assert d.engaged and abs(d.share - 0.3) < 1e-9 and d.policy_id == 'wander-cap.v1'
    assert not wander.decide(Config(), wander.LineageReading(cycles=10, seed_worked=8, other_worked=2, floor=0.5)).engaged
    print('ok')" -> ok

**S10 (R9, R10) — the scheduler applies it, through the existing machinery.**
Files: `src/deepreason/scheduler/scheduler.py`.
Before: `_select_problem` gates reflexive problems out of candidacy when
`INTEGRATION_BUDGET_SHARE` is exceeded, and ranks `SpawnTrigger.SEED` first.
After: the same shape, one lineage class up. The scheduler counts worked cycles
per lineage class (`self._seed_cycles`, incremented when the selected problem's
trigger is `SEED`), builds a `LineageReading`, calls `wander.decide`, and when
the decision is `engaged` restricts candidacy to seed-trigger problems FOR THAT
CYCLE — and only while at least one such problem is available, so nothing
starves and no cycle is ever lost to the throttle. Rank terms are untouched:
the seed's tie-break win, the wound term's position after it, and the
`INTEGRATION_BUDGET_SHARE` gate all stay exactly as `DR-CON-scheduler-ranking`
pins them.

    accept: python -m pytest tests/test_wander_cap.py -q -k "floor_holds or never_starves" -> 0 failed
    accept: python -m pytest tests/test_scheduler_promotion_rank.py tests/test_controller.py::test_operator_question_outranks_spawns_at_cycle_zero -q -> 0 failed

**S11 (R10, R12) — the typed disclosure, and the policy as a recorded artifact.**
Files: `src/deepreason/scheduler/scheduler.py`.
Before: nothing records that attention was steered by lineage.
After: two records. Every cycle emits the reading as
`allocation.seed-lineage-share.v1`. On the transition into throttling the
scheduler emits `allocation.wander-throttled.v1` carrying the policy id, the
share and the floor, AND registers the decision as an ordinary Refl artifact
(`allocation.wander-cap.v1`, provenance role `controller`) so the policy is
attackable — recipe step 2, and calculus P6: a policy nobody can attack is a
status privilege by another name. Emitting on the TRANSITION, not every cycle,
keeps the record proportional to the decision.

    accept: python -m pytest tests/test_wander_cap.py -q -k "discloses or policy_artifact" -> 0 failed

**S12 (R11) — attention only, never labels, mutation-proven.**
Files: `tests/test_wander_cap.py`.
Before: no guard exists for this policy.
After: the guard is a DIFFERENTIAL on one scripted record, the same instrument
`DR-INV-signal-contract` requires of allocation and of `capture/hysteresis.py`:
the record is adjudicated with the throttle engaged and with it disabled, and
every status, attack edge and warrant must be identical. The wander policy's
OWN artifact is excluded — that is the design (P6), exactly as allocation's own
policy artifact is excluded — and nothing else may move. Plus a structural
check that `wander.py` mints no warrant, edge or status. Both are
MUTATION-PROVEN in a scratch copy before the tranche closes: teaching the
adjudicator to read the throttle turns the differential red, and minting a
warrant when the throttle engages turns both red. The mutation transcripts are
committed under the tranche's `proof/`.

    accept: python -m pytest tests/test_wander_cap.py -q -k "evidence or differential" -> 0 failed
    accept: experiments/.../proof/s12_mutation.txt exists and shows RED on both mutations -> present

**S13 (R13) — the phantom signals: EMIT all four, none struck.**
Files: `src/deepreason/controller.py`.
Before: W5's census — `allocation.seat-truncation.v1`,
`allocation.seat-repair.v1`, `allocation.policy-authorized.v1` and
`allocation.policy-contested.v1` are declared, consumed IN-PROCESS, and have no
emit site anywhere in `src/`, so the registry claims four readings the record
never carries.
After: each is emitted at the point where the controller ACTS on it, which is
the only emission that is honest — the reading that changed nothing is not a
signal. `seat-truncation`/`seat-repair`: once per cycle per seat instance, from
`step()` over the values `_process_signals` computed. `policy-contested`: when
fail-static engages. `policy-authorized`: when the controller reverts or
rehydrates to an authorized policy. NONE is struck: striking would make the
registry LESS true, because all four are genuinely consumed — the gap is
emission, not declaration.

    accept: python -m pytest tests/test_wander_cap.py -q -k "phantom" -> 0 failed
    accept: python -c "
    import ast, pathlib
    src = pathlib.Path('src/deepreason/controller.py').read_text()
    for n in ('allocation.seat-truncation.v1','allocation.seat-repair.v1','allocation.policy-authorized.v1','allocation.policy-contested.v1'):
        assert n in src, n
    print('ok')" -> ok

**S14 (R13, R16, R12) — the shipped policy emits the signals it consumes.**
Files: `src/deepreason/allocation.py`, `src/deepreason/signals.py`.
Before: `POLICY_SIGNALS` names five signals; none of the new lineage readings
exist.
After: `allocation.seed-lineage-share.v1` (unit `ratio`, staleness `cycle`) and
`allocation.wander-throttled.v1` (unit `event`, staleness `cycle`) are declared
in `signals.py` with a real unit and a real staleness — no new signal may carry
the migration-debt marker — added to `POLICY_SIGNALS`, and given a
`_PRODUCERS` predicate and a `_RESOLUTIONS` line each. Both are produced by any
topology that runs cycles, so both use `_has_any_seat`.

    accept: python -m pytest tests/test_signal_contract.py tests/test_allocation_signal_consumption.py -q -> 0 failed
    accept: python -c "
    from deepreason import allocation
    from deepreason.signals import declaration as d
    for n in ('allocation.seed-lineage-share.v1','allocation.wander-throttled.v1'):
        assert n in allocation.POLICY_SIGNALS
        x = d(n); assert x and x.unit != 'unspecified' and x.staleness != 'unspecified'
    print('ok')" -> ok

### Both halves

**S15 (R14) — every configuration class still compiles.**
Files: `tests/test_evidence_channels.py`.
Before: `tests/test_allocation_signal_consumption.py -k matrix` compiles solo,
no-schools, judges-off and legacy-on.
After: the matrix gains channels-off-by-choice (each channel alone, and all
three at once) and an unknown-channel configuration. Every one compiles, and
the typed notices are asserted where relevant.

    accept: python -m pytest tests/test_allocation_signal_consumption.py -q -k matrix -> 0 failed
    accept: python -m pytest tests/test_evidence_channels.py -q -k "compiles" -> 0 failed

**S16 (R15) — the offline stub run with an aggressive self-spawner.**
Files: `tests/test_wander_cap.py`.
Before: nothing drives the scheduler against a self-spawning workload offline.
After: a deterministic stub run seeds one operator question and a spawner that
mints a new self-spawned problem every cycle. Over N cycles the seed lineage's
worked share must stay at or above the floor, the throttle disclosure must be
in the record, and the same graph adjudicated without the cap must produce
identical labels (S12's differential is the same instrument, applied here).

    accept: python -m pytest tests/test_wander_cap.py -q -k "stub_run" -> 0 failed

**S17 (R19, R18, C6) — the architecture test.**
Files: `tests/test_channel_and_wander_modularity.py` (new).
Before: the modularity claim would be prose.
After: five failable checks. (1) A channel toggle is PURE CONFIGURATION: two
`Config` values produce two different compiled policies with no source edit.
(2) A floor change is PURE CONFIGURATION: two `Config` values produce two
different decisions. (3) The scheduler consumes ONLY the wander interface —
`scheduler.py` names `wander.decide` and never a policy implementation, and
`wander.py` imports nothing from `scheduler`. (4) Every declared channel has a
toggle field that exists on `Config`, and every registry policy id is reachable
through `LINEAGE_ALLOCATION_POLICY`. (5) Every `wander.SIGNALS` name is
declared AND has a producer predicate — the pair, never half of it. Each is
written so it goes RED on the bypass it names, not merely on a rename.

    accept: python -m pytest tests/test_channel_and_wander_modularity.py -q -> 0 failed

**S21 (R22, R7, C1) — the design consequence, stated.**

**A configuration with channels on gives the criticism machinery a ROAD TO
MACHINE VERDICTS on testable claims.** That is what the three channels are for,
and it is why they belong in the REBUILD rather than in a preferences menu. The
operator's own question names the stake: "Otherwise how is an LLM supposed to
test code". With the channels off, every criticism a run can produce is prose
about prose — a case that must be believed, adjudicated by a judge seat the
operator has recorded as suspect-by-default. With them on, a critic can COMPUTE
a verdict: run a checker against a claim's own counterconditions
(code-testing), execute a declarative program and read its observables
(simulation), or fetch a document and cite bytes out of it (research). W7's
anatomy found the demonstrative class is the one doing real work; the prose
class, measured over the two newest large runs, showed 0 of 196 model-written
attacks ever reaching a later dispatch. So H1 is a supply decision about the
only criticism class that has been shown to bite.

It follows that the DEFAULT matters more than the toggle. A channel that is on
only when an operator remembers an environment variable is, for every run
nobody configured, a channel that does not exist — which is precisely the state
research was in before this tranche.

    accept: this section exists in SPEC.md and is cited by S22's docstring
    -> present

**S22 (R23) — the road exists in every launch path, not merely the flags.**
Files: `tests/test_channel_and_wander_modularity.py`.
Before: S17's five checks prove the toggles are pure configuration. They do NOT
prove a compiled run can actually reach a machine verdict — a default that is
`True` while the road downstream is severed is exactly the failure S0 found in
the allocation controller, and it is the failure this check exists to forbid
for the channels.
After: a sixth architecture check, one row per launch path. The
operations-parity law means there is ONE run path
(`application/text_runs.py::TextRunApplicationService.start_manifest_run`), so
"every launch path" is every entry that COMPILES a manifest into it: the
managed `deepreason reason` preparation, a precompiled
`deepreason run --run-manifest`, and a ladder's own preparation. For each, the
check asserts the ROAD and not the flag:

* the compiled `InquiryCapabilityPolicyV1` has `research.enabled` and
  `simulation.enabled` True, AND the enabled policies carry the finite bounds
  their validators require — an enabled channel with a zero budget is a severed
  road wearing an enabled flag;
* research's `domain_allowlist` is non-empty, since an enabled research policy
  with no reachable host can mint no evidence;
* the simulation controller CONSTRUCTS against that compiled manifest —
  `SimulationCapabilityController(harness, manifest)` "refuses to exist
  without one", so construction is the road's first real gate;
* the code-testing road is reachable end to end: a `program:` commitment
  registered on a run evaluates through `programs.evaluate` to a PASS/FAIL
  verdict with no enablement consulted anywhere on the path.

Written so it goes RED on a severed road, not on a renamed flag: each assertion
names the value a dispatch or a controller would actually consume.

    accept: python -m pytest tests/test_channel_and_wander_modularity.py -q -k
    "road" -> 0 failed

**S18 (R17) — the gates, and the map moving with the code.**
Files: `docs/map/INV-evidence-channels.md` (new), `docs/map/INV-signal-contract.md`,
`docs/map/REC-revise-allocation-policy.md`, `docs/map/CON-scheduler-ranking.md`,
`docs/map/SUB-capabilities.md`, `docs/map/INDEX.md`,
`docs/map/INV-frozen-surfaces.md`.
Before: no map document owns channel enablement; the signal contract's
`Seams-undocumented` still lists `scheduler x signal-contract`, which this
tranche makes load-bearing for the first time.
After: `INV-evidence-channels.md` owns `channels.py` and the three protected
channels with their authority; `INV-signal-contract.md` gains the lineage
policy layer and the wander policy's own efficiency-never-evidence row;
`CON-scheduler-ranking.md` gains the throttle as a CANDIDACY gate stated as
sitting beside `INTEGRATION_BUDGET_SHARE` and never in the rank key;
`INV-frozen-surfaces.md` gains the granted-contact row for the three
`data.pop` lines with its digest-preservation proof. Every new claim carries a
`check:` that would fail if the behaviour regressed. Map and code move in the
SAME commits.

    accept: python tools/docs_verify.py -> 0 failed
    accept: python tools/docs_verify.py --audit -> 0 refused
    accept: python tools/docs_verify.py --links -> 0 unresolved
    accept: python -m pytest tests/ -q -n 4 -> 0 failed

## Assumptions (operator may override)

**A1 (Q1) — "coding" is the CODE-TESTING/EXECUTION channel**, the operator's
own 2026-08-14 name for it, not model-authored Python inside the simulation
capability. Settled by the record rather than assumed: the operator's standing
ruling names four channels ("Code testing, simulation, scratch pad and research
backends") and the tranche instruction spells H1's third channel
"code-testing". `DEEPREASON_SIMULATION_RUNNER=contained` remains available and
untouched — it is a simulation RUNNER PROFILE, not a channel.

**A2 (Q2) — research's default allowlist is a declared registry constant.**
`channels.DEFAULT_RESEARCH_ALLOWLIST = ("arxiv.org", "en.wikipedia.org")`.
Research cannot be enabled with an empty allowlist — the policy validator
refuses it ("enabled research requires a frozen domain allowlist") — so
"permanently on" REQUIRES some default, and the smallest honest one is two
stable, citable hosts. It is pure configuration in both directions:
`DEEPREASON_RESEARCH_ALLOWLIST` overrides it exactly as today, and the constant
is one declared line. The operator may name a different set at no cost beyond
one requalification.

**A3 (Q1) — code-testing ships DECLARED-ON with no off-switch, and this is
stated rather than hidden.** The operator's own instruction bounds H1: "this is
config defaults, not path surgery". Code-testing has no enablement gate today,
and its only live entry points are the commitment compilers in
`workloads/text.py` and `informal/skeleton.py`, whose commitment ids are
CONTENT-ADDRESSED digests over the compiled shape. An off-switch there would
drop counterconditions from the record — path surgery on the evidence road,
which this instruction excludes and which the "seats change GENERATION, never
EVIDENCE" law would need its own tranche to get right. So R3 ("permanently on")
is delivered in full and CHECKED; R4's off-switch is delivered for research and
simulation, and PARKED for code-testing (PARKED.md P1) with a ready-to-send
prompt. **What this tranche does NOT do is stated in DELIVERY.md, not left to
be discovered.**

**A4 (Q3) — the floor defaults to 0.5.** W6 measured the operator's question at
53.2 % of ARM H's budget overall and 48.3 % after the self-spawn, so a floor of
one half is the value that would have bound on the recorded run and not before
it. It is a FREE-layer parameter: changing it is one `Config` value.

**A5 (Q4) — "deprioritized" is CANDIDACY GATING for the cycle, not rank
demotion.** R9 requires "the existing attention/allocation machinery", and the
existing machinery for a budget share is `INTEGRATION_BUDGET_SHARE`, which
gates candidacy rather than reweighting a rank key. Using the same shape keeps
the rank key — and every guarantee `DR-CON-scheduler-ranking` pins on it —
untouched. The gate yields whenever no seed-lineage problem is available, so it
can never lose a cycle.

**A6 (Q4) — the seed lineage is `SpawnTrigger.SEED`, not the family closure.**
`problem_family` would transitively swallow `audit:ritual` (spawned from
artifacts addressing the seed problem) and the floor would never bind — the
exact spend W6 measured would be invisible to it. The cut W6 itself used is the
problem's own trigger, and it is the cut the scheduler's rank key already
knows. An alternative lineage rule is a different registered policy, not a code
edit.

**A7 (Q5) — all four phantoms are EMITTED, none struck.** Each is genuinely
consumed by `controller.py` today; the gap is that no consumption was ever
written down. Striking a consumed signal would make the registry less true, not
more.

## Questions for operator (STOP if non-empty)

None. Every fork above was decided by the operator's own recorded words or by a
measurement, and each decision is recorded as an assumption the operator can
reverse in one line.

One GRANT is requested below rather than asked here, because the operator
forecast the contact in the tranche instruction itself and the three
precedents in `INV-frozen-surfaces.md` direct such a request into SPEC.md.

## Frozen-surface contact forecast

`tools/blast_radius.py` verdict: **CONTACT**. Its computed
`frozen_surface_contacts`, pasted verbatim:

```json
[
 {
  "surface": "manifest schemas and validators (run_manifest.py)",
  "tier": "DIRECT",
  "target": "src/deepreason/run_manifest.py",
  "detail": "target file is surface path src/deepreason/run_manifest.py"
 }
]
```

`frozen_adjacent_contacts`, pasted verbatim:

```json
[]
```

**Grant requested, and its content named before a line of code exists.** The
contact is THREE `data.pop` lines in `_versioned_source_config_data` —
`CHANNELS_DISABLED`, `SEED_LINEAGE_BUDGET_FLOOR`, `LINEAGE_ALLOCATION_POLICY` —
joining the sixteen already there. No schema, no validator, no Pydantic model,
no check name, no record format.

The operator FORECAST this contact in the tranche instruction's own words:
"the operator-seeded lineage gets a declared budget-share FLOOR (**Config knob,
versioned-source line for every schema version**)". That sentence names the
exact content of the contact, which is the same shape the three prior grants
took (2026-08-21 Rung 1b-ii, 2026-08-22 Rung 4, 2026-08-24 Rung 7): forecast in
the instruction, requested in the tranche's own spec, reviewed there.

**Insertions only, and the effect is to PRESERVE digests, not move them.** This
is the identical argument the 2026-08-23 split-budget grant and the Rung 5/Rung 8
grants made, and it is checkable rather than asserted: with the three lines, no
key reaches `engine_config_json` and `source_config_hash` is byte-identical at
every schema version; without them, every qualification subject digest moves and
22 frozen manifest goldens go red. S8's accept check IS that proof.

**Surface 5 is a different matter and is NOT a code contact.** Enabling research
by default changes the COMPILED MANIFEST's content — measured, M1 below — so
every qualification subject digest built from the engaged preset moves. No line
of `qualification.py` is touched; the subject legitimately changed because the
run's authority changed. R6 directs this be PRICED and not stopped, and S7
prices it.

## Blast-radius census

`tools/blast_radius.py` `consumers.tests`, every hit classified. No hit omitted.

| target | test hits | verdict |
|---|---|---|
| `src/deepreason/run_manifest.py` | `test_decommissioned_pipeline_stays_out.py:116` | MUST NOT MOVE — C2; the three `data.pop` lines cannot reach it |
| `src/deepreason/signals.py` | `test_signals.py:52` | EXPECTED TO MOVE — the declared census grows by two |
| `engaged_research_policy` | `test_v6_policy_preset.py:279,282,290,306` | EXPECTED TO MOVE — S3 inverts the default; these pin "off unless the env var" |
| `engaged_simulation_policy` | `test_contained_simulation_runner.py:18,263,269,279,283,289`; `test_v6_engaged_public_defaults.py:64,563`; `test_v6_policy_preset.py:19,132,204` | MUST NOT MOVE — S4 is byte-identical when the channel is enabled, which is every one of these calls |
| `engaged_inquiry_capability_policy` | `test_single_run_path.py:45,141,529`; `test_v6_engaged_public_defaults.py:62,561,622,753`; `test_v6_policy_preset.py:15,157,278,306,313,323,326` | EXPECTED TO MOVE — research turning on changes the policy digest (M1) and any manifest sha derived from it |
| `POLICY_SIGNALS` | `test_signal_contract.py:140,145,147,160,163` | EXPECTED TO MOVE — two rows added; the pinned count moves by exactly two |
| `open_loop_signals` | `test_allocation_signal_consumption.py:249,509,510,536`; `test_capture14_hysteresis.py:262` | MUST NOT MOVE — both new producers are `_has_any_seat`, so no topology gains an open loop |
| `_select_problem` | `test_amendment_epochs.py:340,490`; `test_controller.py:172,225,234,237`; `test_import_role_survivors.py:4,127`; `test_oracle.py:261`; `test_premise_channel_loop.py:311,320,339,347`; `test_scheduler_promotion_rank.py:109,119,128,142` | MUST NOT MOVE — S10 adds a candidacy gate that is inert unless the seed share falls below the floor; none of these drives a run past the floor |
| `_process_signals` | `test_allocation_signal_consumption.py:409`; `test_controller.py:94,96` | MUST NOT MOVE — S13 emits from `step()`, reading what `_process_signals` already returns; the function's own contract is unchanged |
| `exec_oracle_commitment` | `test_experiment.py:95,97`; `test_oracle.py:14,155,166,296,398,429,526`; `test_prose_refutation_boundaries.py:516,527` | MUST NOT MOVE — A3: no off-switch ships, so `oracle.py` is not edited |
| `candidate_checker_commitment` | `test_oracle.py:12,196,207,214,248`; `test_prose_refutation_boundaries.py:615,619` | MUST NOT MOVE — same |
| `property_oracle_commitment` | 33 hits across `test_crit_batch.py`, `test_criticism_authority.py`, `test_criticism_school_execution_c3.py`, `test_evidence_view.py`, `test_experiment.py`, `test_oracle.py`, `test_properties.py`, `test_text_authority_policy.py`, `test_v6_nonconjecture_recovery.py`, `test_v6_transaction_qualification.py`, `test_vision.py` | MUST NOT MOVE — same. **A3 exists to keep this column empty**, and this row is why it is worth stating: 33 evidence-path assertions is the price of the off-switch this tranche declines to improvise. |

`consumers.map_checks` — 14 map documents assert on the touched targets. The
three that carry claims this change makes false are `INV-signal-contract.md`
(the `POLICY_SIGNALS` census and the five-signal open-loop table),
`REC-revise-allocation-policy.md` (its `POLICY_SIGNALS` sentence) and
`CON-scheduler-ranking.md` (its list of `Config` knobs `_select_problem`
reads). All three are EXPECTED TO MOVE and are S18's work, in the same commits.
The remaining eleven are `SUB-scheduler.md`, `SUB-capabilities.md`,
`SUB-evaluation.md`, `SEAM-evaluation-x-ontology.md`, `SEAM-evaluation-x-rules.md`,
`SEAM-scheduler-x-rules.md`, `SEAM-capabilities-x-rules.md`,
`SEAM-llm-x-rules.md`, `SEAM-ontology-x-rules.md`, `CON-conjecture-kinds.md`,
`CON-warrants-and-attacks.md`, `SUB-ontology.md`, `SUB-verification.md` and
`INDEX.md`: MUST NOT MOVE except `SUB-capabilities.md` and `INDEX.md`, which
gain the new invariant's row.

Manual cross-check, required because the gate reports the two commitment
constructors as having no live call path and cannot judge string-keyed channel
ids:

    grep -rn "DEEPREASON_RESEARCH_ALLOWLIST" tests/ docs/
      tests/test_v6_policy_preset.py:292        -> EXPECTED TO MOVE (S3)
      tests/test_contained_simulation_runner.py:118 -> MUST NOT MOVE (sets the
        env var explicitly; S3 leaves the override path identical)
      docs/RESEARCH_BACKEND.md:177              -> EXPECTED TO MOVE (S18)

## Measurements

**M1** — enabling research moves the compiled inquiry-capability policy digest,
and therefore every qualification subject built from the engaged preset.

    $ python - <<'PY'
    from deepreason.v6_policy import engaged_inquiry_capability_policy
    off = engaged_inquiry_capability_policy({})
    on  = engaged_inquiry_capability_policy({"DEEPREASON_RESEARCH_ALLOWLIST": "arxiv.org,en.wikipedia.org"})
    print("research OFF digest:", off.digest)
    print("research ON  digest:", on.digest)
    print("identical:", off.model_dump(by_alias=True) == on.model_dump(by_alias=True))
    PY
    research OFF digest: b1aa948f8aa0201b551a5f1bdbd6e7f6def4f5e51bfdb7ce670c448910fdd431
    research ON  digest: 6fb099ad932fa1afe06e4321936b5f797f0204d8f6ef0a39b49510f87a6c0b08
    identical: False

Supports S3, S7 and the surface-5 paragraph above: the digest cost is real,
measured before the code, and is the price R6 directs be reported rather than
avoided.

**M2** — the four phantom signals have no emit site, which is what S13 fixes.

    $ grep -rn "allocation.seat-truncation.v1\|allocation.seat-repair.v1\|allocation.policy-authorized.v1\|allocation.policy-contested.v1" src/ --include=*.py | grep -c "record_measure"
    0

Supports S13 and R13, and agrees with W5's own census
(`experiments/2026-08-26-run-anatomy-program/W5-signals-controller/DECLARED_VS_EMITTED.md`,
"Structural silence — five names nothing can ever emit").

**M3** — the two commitment constructors an off-switch would have to gate have
no production call site, and the compilers that DO mint code-testing
commitments key their ids on the compiled shape.

    $ grep -rn "exec_oracle_commitment\|candidate_checker_commitment" src/deepreason/ --include=*.py | grep -v "^src/deepreason/oracle.py"
    src/deepreason/informal/skeleton.py:139:        # convention exec_oracle_commitment already uses for its own spec.

Supports A3: gating the constructors would gate nothing a live run reaches, and
gating the real compilers changes content-addressed commitment ids.

**M4** — the connection is broken on the CURRENT tree (R20).

    $ sed -n '795,800p' src/deepreason/llm/adapter.py
        maximum = (
            lease.route.max_tokens
            if lease.route.context_window_tokens is not None
            else getattr(endpoint, "max_tokens", lease.route.max_tokens)
        )
        return int(maximum or 0)

The settled endpoint cap — the only value `Controller._apply_cap` writes — is
unreachable on the qualified branch. Supports S0 and S19.

**M5** — a narrowed cap is LAWFUL today, so wiring it re-arms no killer.

    $ grep -n "cap > route.max_tokens" src/deepreason/llm/firewall.py
    287:            if cap is not None and cap > route.max_tokens:

E43's ceiling: only a cap ABOVE the route allowance raises. Supports S0.

**M6** — the mid-cycle recompute that killed run `bb0455384ea09b5b` is gone: the
call CONSUMES the booked bound.

    $ grep -n "reservation_record.completion_bound_tokens" src/deepreason/llm/adapter.py
    1413:                    dispatch_authorization.reservation_record.completion_bound_tokens

Supports S0 — the defect the ceiling rule was standing in for is closed by
different machinery, which this item does not touch.

**M7** — the wiring's blast radius is CLEAR of every frozen surface.

    $ python tools/blast_radius.py --files src/deepreason/llm/adapter.py --symbols _completion_cap
    frozen_surface_verdict: CLEAR
    frozen_surface_contacts: []
    frozen_adjacent_contacts: []
    consumers.tests: _completion_cap -> tests/test_v6_reservation_bound_authority.py:223,225

Supports S19. Both hits are EXPECTED TO MOVE only if they pin the ceiling rule;
S19's accept check runs them.

## Out of scope (explicit)

- **Pack sections and wire-contract rendering** — C3. F1 and F2 own them. No
  item above touches `llm/packs.py`, `llm/wire.py` or `llm/contracts.py`. If an
  item turns out to need one, that is a STOP, not a widening.
- **A code-testing off-switch** — A3, PARKED.md P1. Not requested as such; R3
  asked for ON.
- **The scratch pad** — the operator's own same-day correction removed it from
  the evidence-minting channels ("Sorry not scratch pad. that doesn't mint
  evidence"). It stays protected-live and advisory; nothing here touches it.
- **Reviving the website pipeline** — C2, and S6 checks it.
- **Retiring the other 79 silent signals** in W5's census. R13 names the four
  `allocation.*` phantoms and the policy this tranche ships. The rest is a
  different worklist.
- **A live run** — the gate this tranche must pass is offline (R14–R17). Live
  evidence for the cap is a later, separately-budgeted question.

## Budget

    $ python -c "print(sum([130,140,22,8,55,22,18,30,70,12,150,170,260,210,90,60,55,30]))"
    1532

~1532 insertions (ceiling), 7 commits — one per phase boundary plus one per
half. Frozen surfaces touched: **surface 4, `run_manifest.py`, three `data.pop`
lines, grant requested above with the tool's own contact list pasted.**

Itemization, which sums to the headline above:

| lines | item |
|---:|---|
| 130 | `channels.py` (new registry + notices) |
| 140 | `wander.py` (new policy interface + registry) |
| 22 | `config.py` (3 fields + comments) |
| 8 | `run_manifest.py` (3 `data.pop` lines + comment) |
| 55 | `v6_policy.py` (channel-aware research/simulation/inquiry) |
| 22 | `allocation.py` (2 `POLICY_SIGNALS` rows + producers + resolutions) |
| 18 | `signals.py` (2 declarations) |
| 30 | `controller.py` (4 phantom emit sites) |
| 70 | `scheduler/scheduler.py` (reading, decide, candidacy, emission, artifact) |
| 12 | `llm/adapter.py` (S19, the one-expression wiring fix) |
| 150 | `tests/test_controller_reaches_the_wire.py` (S20) |
| 170 | `tests/test_evidence_channels.py` |
| 260 | `tests/test_wander_cap.py` |
| 210 | `tests/test_channel_and_wander_modularity.py` (S17 + S22) |
| 90 | map: `INV-evidence-channels.md` (new) |
| 60 | map: `INV-signal-contract.md`, `REC-revise-allocation-policy.md` |
| 55 | map: `CON-scheduler-ranking.md`, `SUB-capabilities.md`, `INDEX.md` |
| 30 | map: `INV-frozen-surfaces.md` (granted-contact row) |

Goldens that will need regeneration are NOT in this ceiling and are counted
separately in VALIDATION.md, per S7.

Rubric: 6/6 yes — every R has a spec item with a machine-decidable accept
(R1→S1/S3, R2→S1/S4, R3→S1/S5, R4→S2/S4, R5→S6, R6→S7, R7→the headline line,
R8→S8, R9→S9/S10, R10→S11, R11→S12, R12→S9/S11/S14, R13→S13/S14, R14→S15,
R15→S16, R16→S14/S16, R17→S18, R18→S1/S2/S8/S9/S17, R19→S17, R20→S0 with M4-M6, R21→S19/S20, R22→S21, R23→S22); blast-radius
census pasted from the tool and every hit classified; frozen-surface contact
forecast recorded with the tool's verbatim list and the grant requested; every
named mechanism traced to code it reaches (M3 is the trace that killed one);
nothing untraceable to an R or C number.
