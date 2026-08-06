<!-- DR-CON-seats -->
Verified-at: 43a485a9
Verify: python tools/docs_verify.py
Owns: src/deepreason/llm/roles.py, src/deepreason/llm/firewall.py, src/deepreason/llm/adapter.py, src/deepreason/preparation.py, src/deepreason/provider_profile.py, src/deepreason/cli/doctor.py
Seams: DR-SEAM-llm-x-manifest, DR-SEAM-llm-x-rules
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

What every ordinary run does today, instead, is mint ONE
`ProviderProfileV1` at `deepreason setup` (one provider/endpoint/
model/model_profile bundle) and copy its `endpoint_spec()` into every
canonical role identically. So "which model answers role X" is
uniform across a run not because the mechanism can't vary it, but
because nothing upstream of `select_lease` ever populates the table
with more than one distinct `Route`. This is measured, not designed,
territory — see `docs/proposals/ROLE_SEAT_SEPARATION_PLAN.md` for the
program that would spend this slack; this document describes only
what exists.

## Where it lives

| Aspect | File | Symbol |
|---|---|---|
| Role prompt templates and the closed role name set | `llm/roles.py` | `ROLES`, `TEMPLATES`, `COMPACT_TEMPLATES`, `render_role_prompt` |
| One role-seat bound to one immutable route | `llm/firewall.py` | `EndpointLease`, `Route` (`run_manifest.py`) |
| The seat lookup itself: `(role, seat) -> EndpointLease` | `llm/firewall.py` | `select_lease` |
| Building the frozen table once per adapter | `llm/firewall.py` | `leases_from_endpoints` (legacy `config.roles`), `leases_from_manifest` (v6 `RunManifest.roles`) |
| Ordinary dispatch: render, resolve seat, call the provider | `llm/adapter.py` | `LLMAdapter.call`, `LLMAdapter._render_request` |
| Presentation profile (compact/standard/frontier) — per-run today; per-`(role, seat, endpoint_id)` already possible in v6 | `llm/adapter.py`, `run_manifest.py` | `LLMAdapter.profile_for`/`base_profile_for` (legacy, one `self.base_model_profile`); `resolve_route_seat_base_profile` (v6, already seat-scoped) |
| The one place every canonical role gets its route today | `preparation.py` | `_config_for_profile` |
| The setup-time provider/model/transport bundle | `provider_profile.py` | `ProviderProfileV1` |
| The ONE call site that bypasses `LLMAdapter.call` entirely | `cli/doctor.py` | qualification battery: `render_role_prompt` + inline `EndpointLease` construction, dispatched via `endpoint.complete` directly |

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

**Every canonical role is populated from the SAME single endpoint at
setup time.** This, not a limitation in `select_lease`, is why no
call site's presentation is frozen per-role today.
`check: grep -q "roles={role: dict(endpoint) for role in V3_CANONICAL_ROLES}" src/deepreason/preparation.py`

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
44 call sites (43 through `LLMAdapter.call`/subclass `.call`, 1 through
`cli/doctor.py`'s direct render).** A full enumeration, classification
by role/template_role/lease-path, and the select_lease degrees-of-
freedom measurement live in
`experiments/2026-08-06-change-seat-census-s1/CENSUS.md` (Rung S1 of
the role-seat separation plan) — this document names the mechanism;
that tranche is the measured evidence trail.
`check: test "$(grep -rn '\.call(' src/deepreason --include='*.py' | wc -l)" = "43"`

## Traps

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
