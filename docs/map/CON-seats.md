<!-- DR-CON-seats -->
Verified-at: 5e0d5bab
Verify: python tools/docs_verify.py
Owns: src/deepreason/llm/roles.py, src/deepreason/llm/firewall.py, src/deepreason/llm/adapter.py, src/deepreason/preparation.py, src/deepreason/provider_profile.py, src/deepreason/cli/doctor.py, src/deepreason/seat_bindings.py, src/deepreason/readiness.py, src/deepreason/seat_events.py
Seams: DR-SEAM-llm-x-manifest, DR-SEAM-llm-x-rules, DR-SEAM-llm-x-scheduler
Seams-undocumented: capabilities x seats, scratch x seats, workloads x seats, doctor x seats

# Seats — how a role becomes a provider request today

## What it is

A **role** (`llm/roles.py`: `conjecturer`, `argumentative_critic`,
`judge`, ...) is a prompt template plus an output contract. A **seat**
is one `(role, seat-index)` pair — `judge[0]`, `judge[1]` for a
two-member ensemble. `select_lease` resolves a seat to an
`EndpointLease`, which permanently binds that seat to one immutable
`Route`: a complete, independent `model_id`/`endpoint_id`/`base_url`/
`provider`/`family`/`reasoning`/`temperature`/`output_mechanism`
identity. Nothing in this mechanism forces two roles, or two seats of
one role's ensemble, to share a model — the routing seam already
supports per-seat model assignment.

What every run does BY DEFAULT (no `--seat` flags at `deepreason
setup`) is mint ONE `ProviderProfileV1` (one provider/endpoint/model/
model_profile bundle) and copy its `endpoint_spec()` into every
canonical role identically. So "which model answers role X" is
uniform across a run not because the mechanism can't vary it, but
because nothing upstream of `select_lease` populated the table with
more than one distinct `Route` — until Rung S3 (role-seat separation)
gave `deepreason setup` an OPT-IN way to do exactly that: `--seat
<group>=<path>` binds an existing profile file to a role group
(`conjecture`, `coder`, `scratch`, `simulation`, the last an alias of
the first), persisted separately from the default profile and
resolved into per-role `Route`s at manifest-compile time — never a new
`Config`/`RunManifest` field (see `seat_bindings.py`). Absent any
`--seat` flag, behavior is exactly the historical uniform broadcast,
byte-identical.

Rung S4 (qualification per seat) added the readiness half of the same
story: `readiness.py::get_seat_readiness` answers, per bound seat
group, "is THIS seat's own profile provably capable" — independent of
whether the run's actual COMBINATION (default + every bound profile,
qualified as one subject per M5/M6 of `experiments/
2026-08-06-change-qualification-per-seat-s4/SPEC.md`) has itself been
qualified. It is a pure readiness PROJECTION, computed via the exact
same per-profile uniform-subject logic `get_readiness` already uses
(shared helper `_readiness_fields`) — it answers a DIFFERENT question
than launch readiness, not a finer-grained version of the same one.

## Rung S4 — a per-profile qualify loop is additive to combination-qualify, never a replacement for it

`cli/main.py::_cmd_qualify` runs the EXISTING combination-qualify pass
(one subject for the whole bound manifest — S3's mechanism, unchanged,
M5-measured dispatch-pure) and, when seat bindings exist, ADDITIONALLY
loops over each distinct bound profile (deduped by `profile_digest`)
qualifying it UNIFORMLY (no seat_bindings — `_qualify_one_profile`,
the extracted single-profile body). The per-profile loop exists for
`status`/readiness granularity only; a run's actual launch depends
solely on the combination subject (M6: `RunPreparationService.prepare`
already refuses typed for an unqualified combination, unmodified).
A single-profile home (no `--seat`) has exactly one loop iteration —
the combination call IS that iteration — so output stays byte-
identical to pre-S4.
`check: grep -q "^def get_seat_readiness(" src/deepreason/readiness.py && grep -q "^class SeatReadinessV1" src/deepreason/readiness.py && grep -q "    group: str$" src/deepreason/readiness.py && grep -q "^def _readiness_fields(" src/deepreason/readiness.py && test "$(grep -c "fields = _readiness_fields(" src/deepreason/readiness.py)" = 2`

## Rung S5 — seats in the typed record

Every run's own record now permanently says which model sat in which
seat, following the rung-4 module-fingerprint template exactly: a new
sibling payload (`seat_events.py`'s `SeatBindingV1`/
`SeatBindingsEventPayloadV1`, schema `seat-bindings.v1` — a sibling of
`module-fingerprints.v1`, not an extension of it, since a role-group ->
profile mapping is a LIST of typed entries, not one opaque mapping
dict), an absence-tolerant reader (`recorded_seat_bindings`, returning
EVERY stamp found, never a single-unpack, so a continuation carrying
more than one is read correctly rather than crashing a test), a
contract-fencing clause on `Event` (rides only `Rule.MEASURE`, exactly
mirroring `module_fingerprints`'s own fence), and the writer
(`Harness.record_seat_bindings`, R19-authorized to exactly an appender
plus one `_commit` keyword — zero `_apply_event` contact).

A default home (no `--seat` binding at `setup`) never gets a stored
event at all: `seat_bindings_for_run(harness, manifest)` instead
PROJECTS a single synthesized `group="default"` entry from the
manifest's own uniform route, which is what "every existing committed
root reads as single seat, the manifest's provider" (R5) actually means
in code — a reader-side projection, not a writer backfilling old roots.

The stamp cannot be resolved live at label time the way readiness is:
`RunManifest.roles` cannot losslessly recover whether an operator wrote
`--seat simulation=X` or `--seat conjecture=X` (both are the identical
alias, expanding to the same role set), so the literal group name is
captured once, at MINT time, by `RunPreparationService.prepare` into a
conditional sibling file (`preparation.py`'s
`SEAT_BINDINGS_SNAPSHOT_NAME`, absent for a default home) via a new
group-keyed helper, `resolve_seat_bindings_by_group`.
`Scheduler._record_seat_bindings` reads that snapshot at run time — RIGHT
beside `_record_module_fingerprints`, same placement, same per-instance
idempotency gate, same `ReadOnlyHarnessError` catch — rather than
re-resolving `seat-bindings.yaml` live, which would be a label-time read
of information the manifest already froze at mint time.
`check: python -c "from deepreason.seat_events import SeatBindingV1, SeatBindingsEventPayloadV1, recorded_seat_bindings, seat_bindings_for_run; from deepreason.seat_bindings import resolve_seat_bindings_by_group; from deepreason.preparation import SEAT_BINDINGS_SNAPSHOT_NAME; from deepreason.harness import Harness; assert hasattr(Harness, 'record_seat_bindings')" && grep -q "def _record_seat_bindings" src/deepreason/scheduler/scheduler.py`

## Where it lives

| Aspect | File | Symbol |
|---|---|---|
| Role prompt templates and the closed role name set | `llm/roles.py` | `ROLES`, `TEMPLATES`, `COMPACT_TEMPLATES`, `render_role_prompt` |
| One role-seat bound to one immutable route | `llm/firewall.py` | `EndpointLease`, `Route` (`run_manifest.py`) |
| The seat lookup itself: `(role, seat) -> EndpointLease` | `llm/firewall.py` | `select_lease` |
| Building the frozen table once per adapter | `llm/firewall.py` | `leases_from_endpoints` (legacy `config.roles`), `leases_from_manifest` (v6 `RunManifest.roles`) |
| Ordinary dispatch: render, resolve seat, call the provider | `llm/adapter.py` | `LLMAdapter.call`, `LLMAdapter._render_request` |
| Presentation profile (compact/standard/frontier) — per-run today; per-`(role, seat, endpoint_id)` already possible in v6 | `llm/adapter.py`, `run_manifest.py` | `LLMAdapter.profile_for`/`base_profile_for` (legacy, one `self.base_model_profile`); `resolve_route_seat_base_profile` (v6, already seat-scoped) |
| Where every canonical role's route is built (uniform by default, per-role override when bound) | `preparation.py` | `_config_for_profile` |
| Whether the compiled manifest's criticism goes through a school seat at all — a Config-driven branch, not a seat mechanism itself (adjudication-judge-seats-optins tranche, S2c/R3, 2026-08-10; full detail in `DR-CON-authority`) | `preparation.py` | `build_preparation_manifest`; `Config.LEGACY_CRITICISM_ENABLED` |
| The setup-time provider/model/transport bundle | `provider_profile.py` | `ProviderProfileV1` |
| Role-group -> role-name expansion, binding persistence, and deterministic conflict RESOLUTION (a direct group beats an alias, then alphabetically-last-group-wins — all-configs-allowed, 2026-08-12: was a refusal, "never last-one-wins"; SeatBindingError now covers only malformed/unknown-group shape errors) | `seat_bindings.py` | `GROUP_ROLES`, `GROUP_ALIASES`, `resolve_seat_bindings`, `SeatBindingError` |
| Group-keyed binding view, no role expansion (Rung S5's mint-time carrier) | `seat_bindings.py` | `resolve_seat_bindings_by_group` |
| Which provider/model sat in which seat, in the append-only record (Rung S5) | `seat_events.py`, `harness.py`, `scheduler/scheduler.py` | `SeatBindingV1`, `SeatBindingsEventPayloadV1`, `recorded_seat_bindings`, `seat_bindings_for_run`, `Harness.record_seat_bindings`, `Scheduler._record_seat_bindings` |
| The ONE call site that bypasses `LLMAdapter.call` entirely | `cli/doctor.py` | qualification battery: `render_role_prompt` + inline `EndpointLease` construction, dispatched via `endpoint.complete` directly |
| Whether a judge ROLE dispatches at all (mint-time, upstream of and orthogonal to `require_cross_family_judges`'s cross-family diversity guarantee below — a run can have `JUDGE_SEATS_ENABLED=False` and a fully cross-family judge ensemble configured and still never fire a single judge call) | `config.py`, `scheduler/scheduler.py` | `Config.JUDGE_SEATS_ENABLED` (default `False`); consulted at `_criticize`'s rubric-trial branch, `_audit_step`, `_property_step`, and `authority.py::trial_authority_for`'s non-text branch (adjudication-judge-seats-optins tranche, S2b, 2026-08-10) |
| Whether that diversity guarantee itself must be cross-FAMILY, or may instead be a same-model ensemble relying on judge-pack blindness (Amendment 9/R24, 2026-08-10 — a structural substitute keyed off the frozen route shape, same pattern as the pre-existing cross-school substitute just above: no separate boolean flag, unlocked only by actually constructing >=2 identical-model judge seats via `--blind-same-model-judges` on the manifest-compile CLI) | `llm/firewall.py`, `run_manifest.py` | `require_cross_family_judge_ensemble`; `compile_run_manifest`'s `blind_same_model_judges` parameter |

## The rules it obeys

**`select_lease` is a pure `(role, seat) -> EndpointLease` lookup; nothing
else keys it.** No call-site identity, workload kind, or profile
override reaches it.
`check: grep -n "^def select_lease" -A 4 src/deepreason/llm/firewall.py | grep -q "role: str, seat: int"`

**Exactly two mechanisms render a role prompt for a live provider
request: `LLMAdapter.call` (all ordinary rules/informal/scratch/
capabilities/workflow call sites) and `cli/doctor.py`'s qualification
battery, which renders and dispatches on its own.** No third path
exists.
`check: ! grep -rn "render_role_prompt(" src/deepreason --include="*.py" | grep -qv "src/deepreason/llm/roles.py\|src/deepreason/llm/adapter.py\|src/deepreason/cli/doctor.py"`

**Every canonical role is populated from the SAME single endpoint by
default; `seat_bindings` overrides specific roles onto a different
endpoint when bound.** The uniform default, not a limitation in
`select_lease`, is why presentation was frozen per-role before Rung S3
— and the override is resolved entirely before `Config` is built, so
`RunManifest.roles`/`compile_run_manifest` need no schema change to
carry it (already-heterogeneous-capable, per this document's own
"one role-seat bound to one immutable route" row).
`check: grep -q "seat_bindings and role in seat_bindings" src/deepreason/preparation.py`

**A role bound by two different `--seat` groups with two different
profiles resolves deterministically; it never silently picks whichever
group happened to sort or load first** (all-configs-allowed, 2026-08-12 —
was a typed refusal; a direct group now outranks one reaching the role only
through `GROUP_ALIASES`, and two equally-direct groups resolve to the
alphabetically later group name, proved by firing the conflict both ways,
not by grepping a retired string).
`check: python -c "
from unittest.mock import patch
from deepreason.seat_bindings import resolve_seat_bindings
from deepreason.provider_profile import ProviderProfileV1
common = dict(provider='fixture', endpoint='https://x.invalid/v1', family='f', context_window_tokens=1024, maximum_completion_tokens=256, credential_env='K')
a = ProviderProfileV1.create(model_id='a', **common)
b = ProviderProfileV1.create(model_id='b', **common)
with patch('deepreason.seat_bindings.resolve_seat_bindings_by_group', return_value={'conjecture': a, 'simulation': b}):
    direct = resolve_seat_bindings()
with patch('deepreason.seat_bindings.resolve_seat_bindings_by_group', return_value={'conjecture': a, 'scratch': b}):
    tie = resolve_seat_bindings()
assert direct['conjecturer'] == a, 'direct group must outrank its own alias'
assert tie['conjecturer'] == b, 'alphabetically later group must win a same-directness tie'
"`

**The qualification battery never calls `select_lease`; it builds its
own `EndpointLease` straight from the manifest's per-`(role, seat)`
route.** A real divergence from the ordinary dispatch path, not an
oversight to paper over.
`check: ! grep -q select_lease src/deepreason/cli/doctor.py && grep -q "EndpointLease(role=pair.role" src/deepreason/cli/doctor.py`

**v6 transactional runs already resolve PRESENTATION profile
(compact/standard/frontier) per `(role, seat, endpoint_id)` — this is
the one place per-seat variance already reaches production, though it
never changes which model/endpoint answers.**
`check: grep -n "^def resolve_route_seat_base_profile" -A 8 src/deepreason/run_manifest.py | grep -q "seat: int"`

**Every provider dispatch in the tree resolves through one of exactly
46 call sites (45 through `LLMAdapter.call`/subclass `.call`, 1 through
`cli/doctor.py`'s direct render).** A full enumeration, classification
by role/template_role/lease-path, and the select_lease degrees-of-
freedom measurement live in
`experiments/2026-08-06-change-seat-census-s1/CENSUS.md` (Rung S1 of
the role-seat separation plan) — this document names the mechanism;
that tranche is the measured evidence trail. Two of the 45 were added
by D2 rev 2 (`experiments/2026-08-08-change-pipeline-design-d2/`):
`rules/encoding.py::draft_encoded_commitment` and
`rules/relatedness.py::relatedness_trial`, both reusing an EXISTING
role's endpoint (`property_designer`/`judge`) rather than adding a new
one — no new manifest role, no change to the degrees-of-freedom count.
`check: test "$(grep -rn '\.call(' src/deepreason --include='*.py' | wc -l)" = "45"`

## Traps

- **"This configuration compiles" says nothing about what its seats may
  do.** Since 2026-08-16 (`experiments/2026-08-16-change-configs-complete-
  seats-test/`, completing the all-configurations law) a seat topology can
  compile while being unable to dispatch at all: an incomplete school
  binding roster, a criticism binding naming a generation role, a shared
  seat under `allow_shared=False`, a `defended_trial` with no defender
  route, a single-family judge matrix. Each carries a `CompileNoticeV1`
  saying so. The seats/evidence law — "seats change how content is
  GENERATED, never what counts as EVIDENCE" — is enforced entirely at the
  POINT OF USE for these shapes: `resolve_school_role_lease`'s typed
  codes, `require_cross_family_judge_ensemble` reading the immutable
  leases, `informal/trial.py`'s typed `_block`/`_decline`, and
  `Harness._validate_warrant`'s frozen rubric-transcript guard. Do not
  read a clean compile as a working seat topology, and do not add a
  compile-time refusal to "fix" one — read the notices.
`check: python -m pytest tests/test_seats_evidence_law.py -q`

- Reading `ProviderProfileV1.model_profile` (compact/standard/
  frontier — a presentation preset) and "the provider profile `setup`
  bound" (the plan document's own phrase, meaning the WHOLE endpoint/
  model/transport bundle) as the same thing collapses two genuinely
  different concepts. Both live in `provider_profile.py`, but only the
  bundle is what "frozen per role" is about; the presentation preset
  is a field on it.
- `cli/doctor.py`'s qualification battery LOOKS like a second adapter
  implementation at a skim. It is not: it deliberately never calls
  `LLMAdapter.call` because it must dispatch against `manifest.roles`
  routes directly, one case at a time, outside any run's token meter
  or attempt-trace machinery — conflating the two paths in a future
  change would silently change what qualification measures.
- **A lease is not one uniform freeze — one field is a ceiling, the rest are
  identities.** Everything `EndpointLease.verify` compares is an exact equality
  except `max_tokens` on a route declaring `context_window_tokens`, where the
  leased value bounds the seat from above and anything at or below it is
  admitted. That asymmetry is deliberate and load-bearing: the completion cap
  is a process-health control the allocation controller retunes mid-run, and
  freezing it by identity terminated reach-rich epoch 2 (run `40e713b3…`) at
  cycle 2 of 24. Reading the lease as "every field frozen" is the specific
  mistake to avoid here, and reading it as "max_tokens is unchecked" is the
  opposite one — an escape ABOVE the qualified allowance is still
  `ROUTE_LEASE_MISMATCH`. FIXED 2026-08-22
  (`experiments/2026-08-22-fix-route-lease-maxtokens/`); the two-sided
  agreement is `DR-SEAM-llm-x-scheduler`.
`check: python -m pytest tests/test_route_lease_maxtokens_tuning.py -q`