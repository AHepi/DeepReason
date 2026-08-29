# Fix: one configuration, one subject, one lifecycle

Tranche: `experiments/2026-08-29-defect-managed-path-config-read/` (defect P14).
Stage 2 (`dr-propose-fix`). **No production code changed by this stage.**
Inputs: `GOAL.md`, `DIAGNOSIS.md`, `REPRO.md`, `PRICE.md`, `STOP.md`.

**Guarantee restored:** `deepreason reason --config F` compiles its run from
`F`; every field of `F` is either CARRIED into the manifest the run executes or
DISCLOSED as a typed compile notice naming the configured value; and the same
`F` reaches `deepreason qualify --config F`, so a configuration that compiles
can also be qualified and run.

**Verdict on the brief's first question, stated plainly:** the managed path does
NOT read the operator `Config` today — not partially, not late, not at all —
and after this fix it does.

---

## 0. Approval gate — this fix is a PRICED STOP, not a proceed

`dr-propose-fix`'s gate: class `defect`, diff <= 150 lines, no frozen surface
=> proceed. Two of three hold. The third does not, on the batch disposition's
own terms:

> IF carriage moves ANY QUALIFICATION SUBJECT DIGEST, that is a PRICED STOP,
> NOT a grant. The operator decides that spend, not you.

This design moves the qualification subject digest for a configuration that
changes what the run is contracted to do (measured: 3 of the 8 committed
`run-config.yaml` files via `RESEARCH_BACKEND`, 5 of 8 via
`LEGACY_CRITICISM_ENABLED=False`). §3 proves that NO design delivers carriage
without that movement. The lane therefore stops here with the design complete
and priced; `STOP_STAGE2.md` carries the decision.

Frozen surfaces: **none contacted.** `tools/blast_radius.py` over the planned
targets returns `"frozen_surface_verdict": "CLEAR"`,
`"frozen_surface_contacts": []`, `"qualification_digest": []`,
`"wheel_smoke_pins": []` (`proof/blast_radius.out`). The conditional grant for
SURFACE 4 (`run_manifest.py`) forecast for tranche B2 is **not used and not
requested by this fix**: the disclosure machinery this design relies on already
exists there (`_emit_uncarried_config_notices`, landed 2026-08-28) and is only
CONSUMED, never edited. One residue does need surfaces 4 AND 5 and is parked
rather than designed — §7, P22.

---

## 1. What stage 2 found that stage 1 could not

Three measurements, all offline, all re-runnable, all made before this design
was written. Each changes the fix.

### 1a. Carriage alone would make every committed configuration UNRUNNABLE

`probe/lifecycle_gap.py` -> `probe/lifecycle_gap.out`.

`deepreason reason` prepares through `RunPreparationService()` with
`qualification_executor=None`, so a subject the cache does not hold is a typed
REFUSAL, not an automatic battery (`qualification.py:804-818`). The battery is
run only by `deepreason qualify`, whose subject comes from
`preparation.qualification_subject_manifest(profile, *, attached_evidence,
seat_bindings)` — **which has no `config` parameter.**

Measured on a home that has already qualified and passed:

    CONTROL  reason, no --config                    STARTS (cache hit)
    8 of 8 committed run-config.yaml files          REFUSED QUALIFICATION_NOT_CONFIGURED

and no committed command can clear that refusal, because no command can address
a configured subject. Stage 1 priced carriage at "one battery per home". The
true price of stage 1's road A or road B AS STATED is *infinite*: the battery
can never be run. **The qualify wiring is therefore part of the fix, not an
extra** (§4, change site 6). This is exactly the operations-parity failure mode
CLAUDE.md already records — "a root that ran real cycles and that no operation
can touch".

### 1b. `--school-seat` and `--criticism-seat` are unreachable on the managed path

`probe/school_seat_deadlock.out`:

    managed-path Config.SCHOOL_SEATS_ENABLED     = False
    reason --school-seat popper=<profile>        -> REFUSED SCHOOL_SEATS_DISABLED
    reason --criticism-seat popper=<profile>     -> REFUSED SCHOOL_SEATS_DISABLED

for EVERY provider profile, because `_config_for_profile` always synthesises the
default `False` and no route exists by which the operator's value could reach
it. The shipped help text for `--school-seat` states the intended workflow
verbatim: *"Requires SCHOOL_SEATS_ENABLED in your config profile (this flag only
persists the binding; the master gate itself is still set via `--config`)"*
(`cli/main.py:96-99`). The documented workflow is broken end to end. This is the
sharpest form of the 2026-08-28 law's violation: not a missing warning but a
flag that gates a seat-configuration path and cannot be turned on.

### 1c. Every committed configuration sets `roles`; none of the eight can have it honoured

`probe/profile_owned_fields.out`: 8 of 8 set `roles`; 3 of 8 set an echoed field
(`RESEARCH_BACKEND`); 7 of 8 set at least one echo-dropped field. On the managed
path `roles` is host-owned — the provider profile owns the credentialed endpoint
and the seat-binding mechanism owns per-role divergence. So the resolution rule
"the profile wins the seven fields it owns" fires for every real configuration,
and its DISCLOSURE is the one limb this design cannot land inside its cone
(§7, P22).

---

## 2. Correction to stage 1's fork — the three roads are two

`STOP.md` recommended road A (carry only the 25 echo-dropped fields) on the
ground that it "satisfies the 2026-08-28 law's second limb for every switch the
law names, at zero qualification cost for all but one." **That is wrong, and the
error is mine to state plainly.** `config_from_run_manifest` rebuilds the run's
`Config` from `engine_config_json` and nothing else, and a dropped field is by
definition absent from `engine_config_json`. So carrying a dropped field into
preparation's `Config` cannot make it reach the run. Road A's 23 "free" fields
are free *precisely because they deliver nothing*: their only effects are the
compile-time trio (`LEGACY_CRITICISM_ENABLED`, `ENGAGED_CRITICISM_AUTHORITY`,
`SCHOOL_SEATS_ENABLED`, which land in typed manifest policy fields) and the
disclosure notices. Road A minus its priced field IS road C.

The real choice is binary:

| | what the operator gets | price |
|---|---|---|
| **disclose only** | the record says, per field, that the setting was not honoured | zero |
| **carriage** (this design) | the setting changes the run; the record discloses the ones the manifest cannot carry | one battery per home per configuration that changes the run |

---

## 3. Why no cheaper design exists (state this before pricing anything)

Three committed facts, composed:

1. `config_from_run_manifest(manifest)` is the ONLY source of a run's `Config`
   (`run_manifest.py:2539` docstring, landed with the 2026-08-28 grant).
2. `engine_config_json` — the thing that function reads — is a field of the
   manifest.
3. `qualification_subject_payload` is `manifest.model_dump(...)` minus exactly
   `compiled_at`, `run_input_digest`, and notices whose code is
   `ENGINE_CONFIG_FIELD_NOT_CARRIED` (`qualification.py:262-270`).

Therefore: **any setting that reaches the run moves the qualification subject,
and any setting that does not move the subject does not reach the run.** The
price is not an implementation flaw to be engineered around; it is the
architecture stating that a differently-configured run is a different thing to
certify. The 2026-08-28 surface-5 grant already carved out the one exception
that can exist — disclosure notices about subject-excluded fields — and this
design consumes that exception rather than widening it.

Corollary the operator should know: the shipped `--school-seat` help text
already declares this cost as normal — *"moving a school to a different seat
changes the qualification battery's pair inventory, which changes the
qualification subject digest — this is a cache miss, not a routing tweak, and
reruns the full battery"*. The product's own surface already tells the operator
that configuring seats costs a battery.

---

## 4. Change sites (exhaustive; every one inside the lane cone)

| # | site | change |
|---|---|---|
| 1 | `src/deepreason/preparation.py` `RunPreparationRequestV1` (108-130) | add `config_path: str | None = None`, validated exactly as `profile_path` is (min 1, max 4096). Absent => today, byte for byte. |
| 2 | `src/deepreason/preparation.py` `_config_for_profile` (308-354) | add keyword `base: Config | None = None`. Build the seven profile-owned values into one `owned` dict; `if base is None: return Config(**owned)` (today's expression, unchanged); else `data = base.model_dump(mode="python"); data.update(owned); return Config.model_validate(data)`. **`model_validate`, never `model_copy`** — `model_copy` does not revalidate and carries typed submodels (`scratchpad`, `bridge`) as bare dicts, which moves the serialized bytes for no reason; stage 1's pricing probe was written wrong this way once and its control caught it. |
| 3 | `src/deepreason/preparation.py` `build_preparation_manifest` (421-...) | add keyword `config: Config | None = None`, threaded to `_config_for_profile(base=config)`. Nothing else in the function changes: the existing `SCHOOL_SEATS_DISABLED` and `CRITICISM_SEATS_REQUIRE_SCHOOL_ROUTED_CRITICISM` gates now become reachable-as-passing for the first time (§1b). |
| 4 | `src/deepreason/preparation.py` `qualification_subject_manifest` (530-551) | add keyword `config: Config | None = None`, threaded through. **This is the operations-parity limb** (§1a). |
| 5 | `src/deepreason/preparation.py` `prepare` (702-...) and `_request_digest` (254-270) | `prepare` loads `request.config_path` via `deepreason.config.load`, threads it to `build_preparation_manifest(config=...)`, and passes it to `_request_digest`. `_request_digest` gains `config: Config | None = None` and adds ONE key, `"config_digest"`, **only when a config is present** — mirroring the `dossier_digest` conditional two lines above it, whose comment already states the reason ("question-only request digests remain byte-identical to their historical values"). Digest form: `sha256_hex(_CONFIG_DOMAIN + canonical_json(config.model_dump(mode="json", by_alias=True)))` — semantic, not textual, so reformatting a YAML file does not mint a new run. Disposes **P18** (§6). A malformed file raises typed `RunPreparationError("CONFIG_PROFILE_INVALID", ...)`; per the all-configurations law a parse/shape error is not a configuration and stays refused. |
| 6 | `src/deepreason/cli/main.py` `_cmd_reason` (2457) | pass `config_path=args.config` into `RunPreparationRequestV1(...)`. |
| 7 | `src/deepreason/cli/main.py` qualify subject (1955) | pass `config=load_config(Path(args.config) if args.config else None)` into `qualification_subject_manifest(...)`, the idiom already used at ten sites in this file. **Cone note:** the lane cone says `cli/main.py (only the reason/config wiring)`. This is config wiring in `cli/main.py` and I read it as inside the cone; it is also load-bearing — without it the fix ships a permanent refusal (§1a) — so it is named here for the operator to confirm along with the price. |

`src/deepreason/config.py`: **not touched.** Carriage requires no new declared
field. (The cone permits it "only if carriage requires a declared field"; it
does not.)

Estimated diff: **~42 production lines across 2 files** (preparation.py ~37,
cli/main.py ~5), plus tests and map. Well inside the 150-line budget.

---

## 5. Regression tests, and the mutation that turns each one red

Mutation-proven means: run RED against the unchanged tree, capture the output
into `proof/`, then GREEN after the fix. R1-R3 are ALREADY committed red
(`proof/repro_red.out`: 2 failed, 1 skipped).

| id | test | what it pins | mutation that turns it RED |
|---|---|---|---|
| **R1** | `tests/test_managed_path_config_read.py::test_reason_forwards_the_operator_config_to_preparation` | something about `--config` reaches `RunPreparationService` | drop `config_path=args.config` from `_cmd_reason` (site 6) |
| **R2** | `...::test_managed_manifest_carries_or_discloses_every_operator_setting` | GOAL.md's disjunction, field by field | drop the `config` parameter from `build_preparation_manifest`, or stop threading it into `_config_for_profile` (sites 2-3) |
| **R3** | `...::test_a_default_valued_operator_config_changes_nothing` (today SKIP) | a defaults-only config compiles byte-identically: `sha256` AND `source_config_hash` unchanged — no home owes a battery for asking for nothing | use `model_copy` instead of `model_validate` in site 2, or merge the seven BEFORE the base instead of after |
| **R4** | NEW `tests/test_managed_path_config_read.py::test_qualify_and_reason_agree_on_the_subject_for_every_configuration` | THE ARCHITECTURE TEST (modularity law): for each of the 8 committed `run-config.yaml` files plus defaults, `qualification_subject_digest(qualification_subject_manifest(profile, config=C), profile)` equals the digest of the manifest `prepare` would compile for `C`. One door, and both consumers go through it. | drop `config=` from site 7 — i.e. exactly the bypass the modularity law says a check must catch |
| **R5** | NEW `...::test_a_configured_run_is_refused_nowhere_a_default_run_starts` | the operational consequence of R4: seed the cache through the QUALIFY subject for config `C`, then `resolve_completed_qualification` on the manifest `prepare` compiles for `C` must hit. Built from `probe/lifecycle_gap.py`. | revert site 7 => `QUALIFICATION_NOT_CONFIGURED`, the 8-of-8 refusal measured in `probe/lifecycle_gap.out` |
| **R6** | NEW `...::test_run_identity_covers_the_configuration` | two requests, same question, different configs => DIFFERENT managed run ids; and a question-only request digest stays byte-identical to its measured historical value `7ea3afd5a387993d19999918ea26698529245bbf1c1ba23dc5ac6a22e03c93e9` (`probe/request_identity_baseline.out`) | omit `config_digest` from `_request_digest` => the two ids collide; add it UNCONDITIONALLY => the pinned historical digest moves. Two mutations, opposite directions, one test. Disposes P18. |
| **R7** | NEW `...::test_the_provider_profile_owns_routes_under_a_configured_run` | the deterministic resolution rule: a config whose `roles` names a different endpoint does not redirect the managed run; the compiled `roles` equal the profile's | let `base` win on `roles` in site 2 |
| **R8** | NEW `...::test_a_configured_school_seat_opt_in_compiles` | §1b: with `SCHOOL_SEATS_ENABLED: true` in the config, `build_preparation_manifest(..., school_seats={...}, config=C)` compiles instead of refusing `SCHOOL_SEATS_DISABLED` | revert site 3 |

**Existing tests at risk** (from `proof/blast_radius.out`'s consumer census —
5 test files and 6 map documents assert on the touched targets). Every change
site is ADDITIVE with a `None` default, so each of these must keep passing
UNCHANGED; not one is a fixture that depended on defective behaviour, and none
may be edited:

- `tests/test_run_preparation_service.py` (13 tests; builds requests via
  `RunPreparationRequestV1(**values)`, `extra="forbid"` — an optional field with
  a default is safe)
- `tests/test_reusable_qualification.py` — including the four
  `*_excluded_from_subject_digest` guarantees. **These are the tests the
  2026-08-28 surface-5 grant calls "a guarantee, not a fixture".** They stay
  green under this design because carrying a dropped field into preparation's
  `Config` never puts its NAME into the echo. `LEGACY_CRITICISM_ENABLED`'s own
  test explicitly permits its downstream effect (`criticism_policy` populated)
  to differ — which is precisely the priced move, sanctioned in advance.
- `tests/test_v6_engaged_public_defaults.py` (44 call sites on
  `build_preparation_manifest`), `tests/test_qualification_per_seat.py`,
  `tests/test_qualification_tier.py`, `tests/test_seat_bindings*.py`,
  `tests/test_public_v6_facade.py`, `tests/test_wheel_operational.py`,
  `tests/test_manifest_config_disclosure.py`, `tests/test_single_run_path.py`.

**Instruments the implementation owes at its gate**, beyond the ring:
`python -m pytest tests/ -q -n 4` (0 failed); `python tools/docs_verify.py`
(the batch baseline of 4). The P16 tripwire at `INV-frozen-surfaces.md:297`
matches only `capabilities/state.py|/harness.py|/invariants.py|/run_manifest.py|
/qualification.py|llm/firewall.py`; this design's diff contains none of them, so
the tripwire must stay GREEN — measured on this branch at stage 2, exit 0. If it
fires after implementation, the diff grew beyond this design and that is a stop,
not a check to file down. Also `python scripts/wheel_smoke.py`
plus `python -u scripts/wheel_operational_smoke.py`, because `mcp_server.py:576`
also constructs `RunPreparationRequestV1` and the MCP tool schema sha is pinned
by an instrument no gate runs.

---

## 6. P18 disposed in writing, before code (required by STOP.md)

**P18:** run identity does not cover configuration (`preparation.py:722`,
`_request_digest` over a request with no configuration field). Today harmless
because configuration cannot vary; the moment it can, two runs of the same
question under different configurations collide on one managed run id and the
second is refused `RUN_ALREADY_STARTED` against the first's root.

**Disposition: admit the configuration into run identity** (change site 5),
conditionally, exactly as `dossier_digest` was admitted — so every historical
question-only run id is byte-identical and only a configured request gets a new
identity. Pinned by R6 in both directions. The alternative — leaving identity
config-blind and refusing the second run — was rejected: it would make the
launch verb refuse a configuration that compiled, which the all-configurations
law forbids.

---

## 7. How this design satisfies each standing law (and where it falls short)

**All configurations are allowed (2026-08-12).** Nothing new refuses. Every
`Config` that parses compiles into a run. A field the managed path cannot
honour gets a deterministic resolution rule (the seven profile-owned fields:
the profile wins) or the existing typed disclosure
(`ENGINE_CONFIG_FIELD_NOT_CARRIED`, one per echo-dropped field whose value
differs from its default), never a stop. The only refusals added are parse/shape
errors, which the law leaves refused. **Shortfall, stated rather than hidden:**
the profile-owned resolution rule (§1c) is deterministic and documented but is
NOT recorded as a typed notice on the manifest, because doing so needs a new
notice code emitted inside `compile_run_manifest` (surface 4) AND excluded from
the qualification subject (surface 5) — otherwise the disclosure would itself
move the subject for all 8 committed configurations, which is exactly the
failure the 2026-08-28 surface-5 grant exists to prevent. Surface 5 is granted
to no tranche in this batch. **Parked as P22 with its grant request drafted.**

**Operations parity (2026-08-13).** This is the half stage 1 did not see. Both
launch paths keep entering through
`application/text_runs.py::TextRunApplicationService.start_manifest_run`, which
is untouched. What the fix adds is the missing parity one level up: the subject
`deepreason qualify` warms is now the subject `deepreason reason` needs, for the
same configuration (R4), so a configuration that compiles gets the same
lifecycle — amend, continue, cancel, result, finalize all follow unchanged.
Without change site 7 the fix would create precisely the defect this law was
written about.

**Seat configuration is ungated; gates are optional with warnings (2026-08-28).**
No flag gates a seat-configuration path after this fix; one does today (§1b:
`SCHOOL_SEATS_DISABLED` is unconditional on the managed path, and the CLI's own
help says the gate is set via `--config`). Every gate switch the operator writes
now reaches the record: carried where the manifest carries it, disclosed by
typed notice where it does not — never silence, never a refusal. **Honest limit:**
for the 25 echo-dropped switches this tranche delivers the DISCLOSURE limb plus
the compile-time trio; the CARRIAGE limb for the other 22 requires the echo
itself to change, which moves every manifest golden and every pinned digest.
That is P15 and belongs to tranche B2, exactly as GOAL.md scoped it.

**Modularity is enforced, customisation is easy (2026-08-26).** Behaviour that
was reachable only by editing `_config_for_profile` becomes reachable as
CONFIGURATION. One declared door — `config=` on the two manifest builders,
`config_path` on the request — and R4 is the architecture test that goes RED
when a consumer bypasses it: it fails the moment `reason` and `qualify` stop
agreeing on the subject for a configuration, which is what a bypass produces.

**The judge law as amended (2026-08-28).** `JUDGE_SEATS_ENABLED` is one of the
switches this fix makes disclosable rather than carriable; judge use stays a
per-run configuration choice and no default changes. Nothing here leans on
judges, so the blinding and under-conviction evidence is not engaged.

---

## 8. Explicitly NOT changed (the tempting neighbours)

- **`run_manifest.py`'s drop list.** No `data.pop` line is added, removed or
  made conditional — GOAL.md forbids it and the 2026-08-28 grant's whole
  preservation argument rests on it. Surface 4's conditional grant is not used.
- **`qualification.py`.** Not touched. The subject formula is unchanged; what
  moves is the manifest fed into it, and only for a configuration that changes
  the run.
- **`RunPreparationRecordV1`.** Not touched, deliberately.
  `_write_preparation_record` compares canonical bytes on read without
  `exclude_none`, so ANY new field would emit `"...": null` and break every
  committed record's canonical comparison. The configuration's contribution is
  already recorded through `request_digest` (site 5) and through the bound
  manifest.
- **`readiness.py` / `webapp.py`.** Outside the cone; they keep reporting the
  default subject. Parked as P21.
- **`mcp_server.py`.** Outside the cone; `reason` over MCP gains no
  configuration. Parked as P23.
- **Letting the operator's `roles` win.** Considered and rejected: it would let
  a YAML file redirect a managed run to an arbitrary endpoint, bypassing the
  provider-profile credential model and the seat-binding mechanism that already
  implements "any model in any seat" on this path.

---

## 9. What this fix does NOT prove

It does not prove what a carried switch then DOES inside a running cycle — that
is the second limb (P15), tranche B2's question. It has no live evidence: the
batch is offline by construction and there is no provider credential in this
container, so every claim here is a compile-time or read-time property of
committed code and committed records. And the disclosure limb it delivers for
the 22 dispatch-site switches is a warning, not a switch: after this fix the
record will say, in typed form, that `JUDGE_SEATS_ENABLED: true` was not carried
— which is the law's "never silence", not its "at will".
