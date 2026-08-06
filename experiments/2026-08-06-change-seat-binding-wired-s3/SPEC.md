# Spec for: the binding, wired — Rung S3 of role-seat separation
Traces: every item cites R/C numbers. Untraceable items are bugs.

Map preflight: `docs/map/INDEX.md` resolves this work to `DR-CON-seats`
(the document this tranche's Item S9 updates — its `_config_for_profile`
check WILL break, see Blast-radius census), `DR-SUB-manifest`
(`RunManifest`/`compile_run_manifest` — read, not modified),
`DR-SUB-llm` (`select_lease`/`EndpointLease` — read, not modified),
`DR-SUB-application` (`easy.py` — read; NOT modified, see Item S1
reasoning). `docs/map/INV-frozen-surfaces.md` re-read before writing
this spec; its five surfaces are the reference frame for the forecast
below.

## Concrete design (resolving R1/R2/R4/R10 into exact functions)

**New module `src/deepreason/seat_bindings.py`:**
- `GROUP_ROLES: dict[str, frozenset[str]]` — the role-group -> role-name
  expansion table:
  - `"conjecture": frozenset({"conjecturer", "variator"})` — the plan's
    own gloss (ROLE_SEAT_SEPARATION_PLAN.md line 37: "'Conjecturer' =
    the conjecturer/variator text roles").
  - `"coder": frozenset({"property_designer"})` — see Assumption A4
    below for why `experimenter`-templated content (CENSUS.md M20,
    `rules/experiment.py`'s generator-authoring call, which dispatches
    on `role="conjecturer"` with `template_role="experimenter"`) is
    NOT independently controllable by "coder" today.
  - `"scratch": frozenset({"conjecturer", "synthesizer", "summarizer"})`
    — CENSUS.md M41/M42's measured role set for
    `scratch/authoring.py`'s `ScratchAuthoringService` (`block_role`
    default `"conjecturer"`, `link_role` fixed `"synthesizer"`,
    `guide_role` fixed `"summarizer"`).
- `GROUP_ALIASES: dict[str, str] = {"simulation": "conjecture"}` — R8.
- `class SeatBindingError(ValueError)` with `.code`/`.message`
  (mirrors `ProviderProfileError`'s shape, `provider_profile.py:42-48`).
- `SEAT_BINDINGS_FILENAME = "seat-bindings.yaml"`.
- `seat_bindings_path(*, home=None, environ=None) -> Path` — mirrors
  `setup_provider_profile_path` (`provider_profile.py:297-302`)
  exactly, swapping the filename.
- `parse_seat_flags(values: list[str] | None) -> dict[str, str]` —
  parses `["conjecture=/path/a.yaml", ...]` into `{group: path}`;
  raises `SeatBindingError("SEAT_BINDING_GROUP_UNKNOWN", ...)` for a
  group not in `GROUP_ROLES | GROUP_ALIASES`, and
  `SeatBindingError("SEAT_BINDING_GROUP_DUPLICATED", ...)` if the same
  group appears twice in one invocation. Returns `{}` for `None`/`[]`
  (R3's default case).
- `write_seat_bindings(bindings: dict[str, str], target) -> Path` —
  atomic write, same pattern as `write_provider_profile`
  (`provider_profile.py:346-361`: temp file + rename), YAML,
  secret-free (paths only).
- `load_seat_bindings(path) -> dict[str, str]` — returns `{}` if the
  file is absent (R3's default case: no file, no bindings, byte-
  identical output).
- `resolve_seat_bindings(*, home=None, environ=None) -> dict[str, "ProviderProfileV1"]`
  — loads the persisted `{group: path}` mapping, resolves each path
  via the EXISTING `resolve_provider_profile(explicit_path=path,
  environ=environ, home=home)` (`provider_profile.py:305-333`, reused
  unchanged), expands `GROUP_ALIASES` then `GROUP_ROLES` to build
  `role -> ProviderProfileV1`, and raises
  `SeatBindingError("SEAT_BINDING_ROLE_CONFLICT", ...)` naming the
  role and both conflicting groups whenever two DIFFERENT bound groups
  claim the same role with DIFFERENT resolved profiles (compared by
  `profile_digest`, the same identity CENSUS.md/S2's SM7 already uses
  to distinguish profiles) — this generalizes R9's named case
  (simulation vs conjecture) to the scratch/conjecture overlap this
  spec ALSO discovers below (both share `"conjecturer"`), since both
  are the identical failure shape and the operator's words ("never
  last-one-wins") name the general rule, not only the specific pair.
  Returns `{}` when no `--seat` flags were ever set (R3).

**`src/deepreason/cli/main.py`:** add
`setup_cmd.add_argument("--seat", action="append", default=None, metavar="GROUP=PATH", help=...)`
next to the existing `setup_cmd` arguments (`main.py:36-54`). In the
`setup` dispatch (`main.py:571-587`), AFTER `easy.setup_wizard(...)`
succeeds (unchanged call, unchanged behavior — R1 does not touch
`setup_wizard`/`apply_setup` at all, see Assumption A5), if
`args.seat` is not `None`: `parsed = parse_seat_flags(args.seat)`,
then `write_seat_bindings(parsed, seat_bindings_path())`, wrapped in
the same `except ValueError` pattern the command already uses.

**`src/deepreason/preparation.py`:** generalize `_config_for_profile`
(`preparation.py:263-277`) to accept the resolved bindings:
```python
def _config_for_profile(
    profile: ProviderProfileV1,
    *,
    seat_bindings: Mapping[str, ProviderProfileV1] | None = None,
) -> Config:
    endpoint = profile.endpoint_spec()
    roles = {
        role: dict(
            seat_bindings[role].endpoint_spec()
            if seat_bindings and role in seat_bindings
            else endpoint
        )
        for role in V3_CANONICAL_ROLES
    }
    return Config(
        engine_profile="full",
        model_profile=profile.model_profile,
        scratchpad=engaged_scratchpad_source(),
        bridge=engaged_bridge_source(),
        EMBEDDER_MODEL=None,
        roles=roles,
    )
```
`seat_bindings=None` (the default, unchanged call shape
`_config_for_profile(profile)`) produces the EXACT same `roles` dict
as today — `dict(endpoint)` per role, R3. `build_preparation_manifest`
(`preparation.py:344-363`) gains the same optional
`seat_bindings: Mapping[str, ProviderProfileV1] | None = None`
parameter, passed straight through to `_config_for_profile`. Its two
callers each resolve it themselves (matching how each already resolves
`profile`, never a new shared cache):
- `qualification_subject_manifest` (`preparation.py:387-402`) gains
  the same optional parameter, passed through; `_cmd_qualify`
  (`cli/main.py:1520-1545`) calls `resolve_seat_bindings()` right
  alongside its existing `resolve_provider_profile(args.provider_profile)`
  call and passes the result in.
- `RunPreparationService.prepare` (`preparation.py:554-591`) calls
  `resolve_seat_bindings(environ=self._environ, home=self._home)`
  right alongside its existing `resolve_provider_profile(...)` call
  (`preparation.py:560-564`) and passes the result to
  `build_preparation_manifest`.

This is the SM2/SM1-cited generalization: `Config.roles`'s already-
heterogeneous type and `compile_run_manifest`'s already-independent
per-role compile path (both measured in S2's SPEC.md, unchanged here)
do the rest — no new manifest field, no new validator, per R10/S2's
approved 2a.

## Assumptions (operator may override)

A1 (role->group mapping, "coder"): "coder" = `{property_designer}` —
see A4 for the measured reason `experimenter`-templated content is
excluded. Traces S2's SPEC.md Assumption A1, refined with the M20
finding this tranche's spec-writing surfaced.

A2 (role->group mapping, "scratch"): `{conjecturer, synthesizer,
summarizer}` — traces S2's SPEC.md Assumption A2 (CENSUS.md M41/M42)
unchanged.

A3 (role->group mapping, "conjecture"/"simulation"): `{conjecturer,
variator}`, with "simulation" a true alias (R8) — traces the plan's
own gloss and the operator's Q1 answer verbatim.

A4 (NEW finding, not previously surfaced): `rules/experiment.py`'s
generator-authoring call (CENSUS.md M20) dispatches on
`role="conjecturer"` with `template_role="experimenter"` — the LEASE/
ENDPOINT is selected by `role`, never `template_role`
(`adapter.py`'s `_render_request`: `select_lease(self.leases, role,
endpoint_index)`). So binding "coder" to a profile different from
"conjecture" does NOT redirect M20's calls — they still ride whatever
"conjecture" (or the default, if "conjecture" is unbound) resolves to.
Making "coder" control M20 independently would require adapter-level
routing surgery (a `template_role`-aware lease key), which is
materially more work and risk than anything S2 priced or approved —
assumed OUT of this rung's scope, named here rather than silently
gapped; `property_designer` (M22, no `template_role`, its own
independent role) is the one call site "coder" genuinely controls
today. Operator may override toward the larger change if this gap
matters now.

A5 (`setup_wizard`/`apply_setup` untouched): the new `--seat` flags
are handled entirely in `cli/main.py`'s `setup` dispatch, AFTER
`easy.setup_wizard(...)` returns — `setup_wizard`
(`easy.py:408-511`) and `apply_setup` (`easy.py:533-...`, the webapp's
non-interactive twin) are both single-profile-minting functions by
design and are not touched; their ~10 existing tests
(`tests/test_easy.py`) are therefore MUST NOT MOVE, not MUST UPDATE
(Blast-radius census).

A6 (Q1 — unit test, not a live CLI run): "a unit run with two
MockEndpoint-backed seats" (R7) is read as a pytest unit test using
`llm.endpoints.MockEndpoint` (`endpoints.py:139-...`, the existing
test double, unmodified) and `LLMAdapter` directly — not a literal
`deepreason reason`/`setup` subprocess invocation. The plan's own
phrasing ("asserted from the typed attempt records, which already
carry work attribution per call") names `LLMCall`'s fields as the
evidence, which is exactly what a unit-level `adapter.call(...)`
assertion reads; a live CLI run would additionally require live
credentials/network and cannot use `MockEndpoint` at all (`MockEndpoint`
is a `llm.endpoints` test double, never wired to the CLI's
`_endpoint_from_spec` production path) — the two readings are not
close in cost, but only one is even possible with the named tool
(`MockEndpoint`), so this is not a genuine fork.

A7 (Q2 — CLI flag shape confirmed): `--seat GROUP=PATH`, repeated
(`action="append"`), exactly the plan's own example syntax
(`--seat conjecture=<profile> --seat coder=<profile> ...`) — REQUEST.md
Q2 already noted this as "not genuinely open."

A8 (conflict detection generalizes beyond R9's named pair): R9's words
("conflicting --seat values for the shared role set... never
last-one-wins") are implemented as ONE general mechanism in
`resolve_seat_bindings` (any two bound groups sharing a role with
different resolved profiles refuse), which also catches the
scratch/conjecture `"conjecturer"`-role overlap this spec's writing
discovered (A2/A3) — not only the simulation/conjecture pair the
operator named. Applying the identical, already-approved rule to an
identically-shaped newly-found instance is not treated as a material
fork requiring a fresh stop; operator may override if scratch/conjecture
should be exempted.

## Questions for operator (STOP if non-empty)

(empty — Q1/Q2 from REQUEST.md resolved above as A6/A7; no other
reading differs materially in files touched or behavior.)

## Out of scope (explicit)

- Wiring `deepreason reason`'s live end-to-end CLI path beyond
  `RunPreparationService.prepare` (already covered, R4) — no new
  CLI command, no `deepreason status`/`qualify` output-format change
  beyond what threading `seat_bindings` through requires.
- The `experimenter`-template routing gap (A4) — named, not fixed;
  candidate for a future rung if it matters.
- Rung S4 (qualification-per-seat orchestration walking distinct bound
  profiles) — S2's SPEC.md already scoped this separately; this
  tranche's `resolve_seat_bindings`/`_config_for_profile` generalization
  is a PREREQUISITE S4 will consume, not S4 itself.
- Rung S5 (seats in the typed record) — no new manifest field, per
  R10/2a.
- Per-seat token budget allocation — S2's SPEC.md already deferred
  this (kill-risk 3, defused).

## Frozen-surface contact forecast

**None expected — checked against `INV-frozen-surfaces.md`'s five
surfaces, matching S2's SPEC.md forecast for Option A/2a exactly:**

| Surface | Contact |
|---|---|
| 1. `capabilities/state.py` | none — untouched |
| 2. `harness.py` event application | none — untouched |
| 3. Replay-validation formats | none — untouched; `verify_root` re-derives from the log, which this change never writes to differently |
| 4. `run_manifest.py` schemas/validators | none — `_config_for_profile`'s generalization only changes WHICH endpoint dict gets written into `Config.roles` per role; `Config.roles`'s type (SM1) and `compile_run_manifest`'s grouped branch (SM2) are read, not modified; no new `RunManifest` field, no new `Literal`, no new validator |
| 5. Qualification subject digests | none in the digest function (`qualification_subject_payload` is read, not modified) — `qualification_subject_manifest` gaining an optional `seat_bindings` parameter changes what MANIFEST gets built (still an ordinary, valid `RunManifest`), never how the digest is computed from whatever manifest it is given |

`Config.ENGAGED_CRITICISM_AUTHORITY` trap (`INV-frozen-surfaces.md`
Traps) does not apply: this tranche adds NO new `Config` field (R10,
2a) — `_config_for_profile`'s new `seat_bindings` parameter is a
plain Python function argument, never persisted onto `Config` itself,
so `_versioned_source_config_data` needs no change and was not touched.

## Blast-radius census

```
$ grep -rn "_config_for_profile" tests/ docs/map/
tests/test_reusable_qualification.py:10:from deepreason.preparation import _config_for_profile, _records_for_question
tests/test_reusable_qualification.py:54:    config = _config_for_profile(profile)
docs/map/CON-seats.md:44:| The one place every canonical role gets its route today | `preparation.py` | `_config_for_profile` |
```
`tests/test_reusable_qualification.py:54` — MUST NOT MOVE: calls
`_config_for_profile(profile)` positionally with no `seat_bindings`;
the generalized signature keeps this call byte-identical (R3).
`docs/map/CON-seats.md:44` — MUST UPDATE: this row's claim ("the ONE
place every canonical role gets its route") stops being literally true
once `seat_bindings` can override specific roles; Item S9 updates this
row in the same commit as the code change (`docs/map/SCHEMA.md`'s own
rule).

```
$ grep -rn "build_preparation_manifest" tests/ docs/map/
tests/test_v6_engaged_public_defaults.py: 5 call sites (lines 87,132,212,607,739)
tests/test_schema_v3_consumers.py:46: 1 call site
docs/map/CON-authority.md:82: named in a "where the knob threads" table row
```
All 6 test call sites — MUST NOT MOVE: every one passes `profile`
positionally plus `question=`/`compiled_at=`/etc. keywords; the new
`seat_bindings` parameter is optional and appended, so none of these
calls change shape or behavior (R3). `docs/map/CON-authority.md:82` —
MUST NOT MOVE: names `build_preparation_manifest` only as "where the
criticism-authority knob threads," a claim this change does not alter.

```
$ grep -rn "setup_wizard" tests/ docs/map/
tests/test_easy.py: ~9 call sites
docs/map/SUB-application.md: 3 references (a `check:` line asserting `^def setup_wizard(` exists, a prose row, a doc-check listing it among `easy.py` functions)
```
All MUST NOT MOVE — A5: `setup_wizard` itself is not modified; every
cited check greps only for the function's continued existence /
prose mention, none pin its exact parameter list.

```
$ grep -rn "V3_CANONICAL_ROLES" tests/ docs/map/
docs/map/SUB-manifest.md:154, 165 (two check-bearing references)
docs/map/CON-seats.md:65 (a `check:` line)
```
MUST NOT MOVE — this tranche reads `V3_CANONICAL_ROLES`, never
redefines or extends it; `SUB-manifest.md`'s checks pin the tuple's
OWN definition (`run_manifest.py`), untouched. `CON-seats.md:65`'s
check is discussed in the next block (it does move, but for a
different reason — the `_config_for_profile` BODY it pins, not
`V3_CANONICAL_ROLES` itself).

```
$ grep -rn "resolve_provider_profile" tests/ docs/map/ | wc -l
8
```
MUST NOT MOVE — this tranche calls `resolve_provider_profile`
additional times (once per bound seat path) but never changes its
signature, return type, or resolution order; existing tests assert
its behavior for the single-profile case, unaffected.

```
$ grep -rn "PROFILE_FILENAME\|setup_provider_profile_path" tests/ docs/map/ | wc -l
9
```
MUST NOT MOVE — `seat_bindings_path`/`SEAT_BINDINGS_FILENAME` are NEW,
separate names (a sibling file, not a rename); nothing here is
touched.

**New symbols this tranche introduces have no existing hits by
definition** (`seat_bindings.py`'s entire contents, the `--seat` CLI
flag, `_config_for_profile`'s `seat_bindings` parameter) — their tests
are written fresh in Item S8/S11 below, not "moved."

## Items

S1 (R1, A5, A7): Add `--seat GROUP=PATH` (repeated) to `deepreason
setup`'s argparse registration (`cli/main.py:36-54`) and dispatch
(`cli/main.py:571-587`), calling `parse_seat_flags`/`write_seat_bindings`
from the new `seat_bindings.py` module AFTER `easy.setup_wizard`
succeeds. `setup_wizard`/`apply_setup` unmodified (A5).
accept: `deepreason setup --provider ... --seat conjecture=<path>`
(scripted, non-interactive args) writes `seat-bindings.yaml` under
`provider_state_dir()` containing `{"conjecture": "<path>"}`; a bare
`deepreason setup --provider ...` (no `--seat`) writes NO such file.

S2 (R1, R8, R9, A8): Implement `seat_bindings.py`'s `GROUP_ROLES`,
`GROUP_ALIASES`, `parse_seat_flags`, `write_seat_bindings`,
`load_seat_bindings`, `SeatBindingError`.
accept: unit tests — unknown group raises
`SeatBindingError` code `SEAT_BINDING_GROUP_UNKNOWN`; duplicate group
in one call raises code `SEAT_BINDING_GROUP_DUPLICATED`; `simulation`
parses without error (alias, not unknown).

S3 (R2, R10): Implement `resolve_seat_bindings`, including the
conflict check (A8).
accept: unit test — binding `conjecture=A.yaml` and
`simulation=B.yaml` (A != B) raises `SeatBindingError` code
`SEAT_BINDING_ROLE_CONFLICT` naming `conjecturer`; binding
`conjecture=A.yaml` and `scratch=B.yaml` (A != B) ALSO raises the same
code (the newly-discovered overlap, A8) naming `conjecturer`; binding
`conjecture=A.yaml` and `simulation=A.yaml` (same profile) does NOT
raise.

S4 (R2, R3, R10): Generalize `_config_for_profile` and
`build_preparation_manifest` per the Concrete design section.
accept: `_config_for_profile(profile)` (no `seat_bindings`) produces a
`roles` dict identical, key-for-key and value-for-value, to today's
`{role: dict(endpoint) for role in V3_CANONICAL_ROLES}`; with
`seat_bindings={"conjecturer": other_profile}`,
`config.roles["conjecturer"] == dict(other_profile.endpoint_spec())`
while every other role still equals `dict(profile.endpoint_spec())`.

S5 (R2, R4): Thread `seat_bindings` through
`qualification_subject_manifest` and `RunPreparationService.prepare`
per the Concrete design section.
accept: `RunPreparationService.prepare` with a seat-bindings file
present on disk produces a compiled `RunManifest.roles` reflecting the
bound profiles on their roles and the default profile everywhere else;
with no file present, produces the exact manifest bytes prepare would
have produced before this tranche (a golden/before-after diff on a
fixed question+profile).

S6 (R5): Full gate.
accept: `pytest tests/ -q -n 4` ends with `0 failed`.

S7 (R6): Sweep byte-identical.
accept: `python tools/root_sweep.py <before.txt>` (captured before any
S1-S5 edit lands) vs. `python tools/root_sweep.py <after.txt>`
(captured after) — `diff before.txt after.txt` empty.

S8 (R7, A6): The two-`MockEndpoint` routing proof.
accept: a new test builds `seat_bindings={"conjecturer": profile_a,
"judge": profile_b}` (two distinct `ProviderProfileV1` fixtures),
calls `_config_for_profile(default_profile, seat_bindings=...)`,
asserts the resulting `Config.roles["conjecturer"]["endpoint"] ==
profile_a.endpoint` and `Config.roles["judge"]["endpoint"] ==
profile_b.endpoint`; separately (or in the same test) builds an
`LLMAdapter` from `endpoints={"conjecturer": MockEndpoint(["..."],
name="A", model="model-a"), "judge": MockEndpoint(["..."], name="B",
model="model-b")}`, dispatches `adapter.call("conjecturer", ...)` and
`adapter.call("judge", ...)`, and asserts the returned `LLMCall.model`
(the typed attempt record, per R7's own words) is `"model-a"` for the
first and `"model-b"` for the second — proving role-correct routing
from the typed record, not from internal state.

S9 (map maintenance, `docs/map/SCHEMA.md`'s own rule, same commit as
S4): update `docs/map/CON-seats.md`'s row 44 (the "one place every
canonical role gets its route" claim) and its `check:` at line 65
(which pins the OLD literal `_config_for_profile` body line) to
reflect the generalized function; advance `Verified-at:` since the
document's claims are re-checked as part of this edit.
accept: `python tools/docs_verify.py` (full mode) 0 failed, including
`CON-seats.md`'s updated checks.

S10 (R11): No later rung begun — no qualification-per-seat
orchestration (S4), no manifest-level binding record (S5), no
per-seat budgets.
accept: manual re-read confirms no such content landed; `PARKED.md`
records anything noticed but not fixed.

## Measurements

(This tranche is EXECUTE, not DESIGN-AND-STOP — the Measurements/
Options sections dr-spec-change's procedure marks "DESIGN-AND-STOP
only" are not required. The Concrete design section above already
cites file:line for every function this spec touches, verified fresh
against the live tree in this session.)

## Budget

Estimated ~250-350 changed/added lines: `seat_bindings.py` (~120-150
new lines: constants, parse/write/load/resolve, `SeatBindingError`),
`cli/main.py` (~15-25 lines: one argparse entry, dispatch block),
`preparation.py` (~15-20 lines: `_config_for_profile`'s generalization,
`build_preparation_manifest`'s new parameter, two callers' threading),
`docs/map/CON-seats.md` (~10-15 lines, S9), tests (~100-150 lines
across S2/S3/S4/S5/S8's acceptance tests). Estimated 4-6 commits
(one per Item cluster, per `dr-plan-steps`' checkpoint convention).
Frozen surfaces touched: **none** (forecast table above).

Rubric: 6/6 yes — every R (R1-R11, R4 folded into S5, R8/R9 folded
into S2/S3/A8) has a spec item with a machine-decidable accept;
blast-radius census pasted and every hit classified (MUST NOT MOVE /
MUST UPDATE, the latter itemized as S9); frozen-surface contact
forecast recorded (none, matching S2's own forecast); every mechanism
REQUEST.md/the plan names (`--seat` syntax, `MockEndpoint`, "typed
attempt records") traced to code it actually reaches (A4's
`experimenter`-template limitation is the one place a named mechanism
does NOT reach as far as a first reading might assume, and it is
recorded, not glossed); DESIGN-AND-STOP sections correctly marked N/A
(this is EXECUTE); nothing above is untraceable to an R/C number.
