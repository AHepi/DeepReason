<!-- DR-CON-authority -->
Verified-at: d057f306
Verify: python tools/docs_verify.py
Owns: src/deepreason/authority.py, src/deepreason/config.py, src/deepreason/rules/crit.py, src/deepreason/informal/trial.py, src/deepreason/run_manifest.py, src/deepreason/jolts.py, src/deepreason/ops.py, src/deepreason/scheduler/scheduler.py, src/deepreason/v6_policy.py, src/deepreason/preparation.py
Seams: DR-SEAM-adjudication-x-authority
Seams-undocumented: authority x manifest, authority x rules, authority x scheduler

# Authority — who may change a Status

## What it is

Authority is the answer to one question: may THIS judgement move an artifact's
`Status`, or may it only be recorded? The argument graph owns `Status` values;
authority decides which surfaces are permitted to reach them. Only
LLM-mediated *text* judgements pass through this policy — deterministic,
execution, formal, browser and verifier-backed paths keep their established
status-changing behaviour and never consult it. The concept has no single home
because the decision is made in three stages: a per-run knob on `Config`, a
translation into a concrete per-call mode in `authority.py`, and a gate inside
the adjudication routine (`rules/crit.py`, `informal/trial.py`) that decides
between minting a warrant and filing an observation. Four further files freeze
the policy or call it: `run_manifest.py`, `jolts.py`, `ops.py`,
`scheduler.py`. What makes it hard to navigate is that the *manifest* has its own
authority vocabulary, closed and frozen, which is not the same set of words as
the `Config` one.

## The socket contract — what it promises, what it is handed, what it must never do

An index into the checked claims above and below, for a reader who wants the
socket's contract without reading the whole document. Every bullet cites a
check already proven elsewhere in this file.

**Promises:** everything defaults to `observe_only`, and the calibration
receipt defaults to absent — a run that configures nothing spends no judge
tokens on status-bearing text adjudication.
`check: python -c "from deepreason.config import Config; c = Config(); assert c.ARGUMENTATIVE_AUTHORITY == 'observe_only'; assert {c.TEXT_RUBRIC_AUTHORITY.value, c.PAIRWISE_AUTHORITY.value, c.INFRASTRUCTURE_REVIEW_AUTHORITY.value} == {'observe_only'}; assert c.CALIBRATION_RECEIPT is None"`

The `Config` vocabulary and the manifest vocabulary are two closed sets
that share exactly one word (`observe_only`) and neither may be handed the
other's value.
`check: python -c "import typing; from deepreason.authority import _ARGUMENTATIVE_VALUES as v; from deepreason.config import Config; assert v == set(typing.get_args(Config.model_fields['ARGUMENTATIVE_AUTHORITY'].annotation)) == {'observe_only', 'trial_required', 'single_family_trial'}, v"`
`check: python -c "import typing; from deepreason.rules.crit import _POLICY_AUTHORITIES as p; from deepreason.run_manifest import CriticismPolicyV1 as C; assert set(typing.get_args(C.model_fields['authority'].annotation)) == p == {'observe_only', 'defended_trial'}"`

**What it is handed:** the five per-run `Config` knobs
(`ARGUMENTATIVE_AUTHORITY`, `TEXT_RUBRIC_AUTHORITY`, `PAIRWISE_AUTHORITY`,
`INFRASTRUCTURE_REVIEW_AUTHORITY`, `CALIBRATION_RECEIPT`), each backed by a
real field so a surface with none would silently read the `observe_only`
default forever; and, on a manifest-bound call, the already-frozen
`CriticismPolicyV1.authority` value, passed explicitly rather than
re-derived.
`check: python -c "from deepreason.authority import _SURFACE_FIELDS, AuthoritySurface; from deepreason.config import Config; assert len(_SURFACE_FIELDS) == len(AuthoritySurface) == 3; assert set(_SURFACE_FIELDS.values()) <= set(Config.model_fields)"`

**Must never do:** widen the manifest's authority vocabulary — it is a
frozen `Literal`, and every qualification subject digest derives from the
manifest.
`check: grep -q 'TEXT_AUTHORITY_POLICY_MANIFEST_MISMATCH' src/deepreason/run_manifest.py && ! grep -q 'ARGUMENTATIVE_AUTHORITY' src/deepreason/run_manifest.py`

Let a trial read the authority knob directly — it arrives only as a
parameter, from a caller that has already gated.
`check: python -c "import inspect; from deepreason.informal import trial; assert 'authority' not in inspect.signature(trial._argument_trial_steps).parameters; assert 'authority' in inspect.signature(trial._trial_steps).parameters"`
`check: ! grep -qE 'ARGUMENTATIVE_AUTHORITY|argumentative_authority_mode' src/deepreason/informal/trial.py`

Let `calibrated_status` yield status without a verified receipt —
`calibration_receipt_is_verified` returns `False` unconditionally today; no
receipt verifier exists.
`check: python -c "from deepreason.authority import AuthoritySurface as S, TrialAuthority as T, trial_authority_for as f, calibration_receipt_is_verified as v; from deepreason.config import Config; assert not v(Config(CALIBRATION_RECEIPT='sha256:x')); assert f(Config(TEXT_RUBRIC_AUTHORITY='calibrated_status', CALIBRATION_RECEIPT='sha256:x'), 'text', S.RUBRIC) == T.OBSERVE_ONLY"`

## Where it lives

| Aspect | File | Symbol |
|---|---|---|
| The master reachability gate all six knobs below sit behind (adjudication-judge-seats-optins tranche, S2a/R1, 2026-08-10): each of the six stays independently settable, but stays observe_only-equivalent unless this is ALSO True. Applied at each knob's own operational consumption site, never inside a shared resolution function preflight also reads: `ARGUMENTATIVE_AUTHORITY`/`TEXT_RUBRIC_AUTHORITY`/`PAIRWISE_AUTHORITY`/`INFRASTRUCTURE_REVIEW_AUTHORITY` at `rules/crit.py::_authority`/`authority.py::trial_authority_for`; `ENGAGED_CRITICISM_AUTHORITY` at `preparation.py::build_preparation_manifest` (found missing and fixed while writing this row) | `src/deepreason/config.py` | `ADJUDICATION_STATUS_AUTHORITY_ENABLED` |
| Surface-mode enum (what a surface is configured to have) | `src/deepreason/authority.py` | `TextAuthorityMode` — `observe_only`, `calibrated_status` |
| Call-mode enum (what one trial is handed) | `src/deepreason/authority.py` | `TrialAuthority` — `observe_only`, `status` |
| The three independently-configured surfaces | `src/deepreason/authority.py` | `AuthoritySurface`, `_SURFACE_FIELDS` |
| Surface knob → per-call mode translation | `src/deepreason/authority.py` | `trial_authority_for` |
| The unconditional block on calibrated status | `src/deepreason/authority.py` | `calibration_receipt_is_verified` |
| Prose-criticism vocabulary (Config side) | `src/deepreason/authority.py` | `argumentative_authority_mode`, `_ARGUMENTATIVE_VALUES`, `_TRIAL_AUTHORITIES` |
| Prospective manifest violations | `src/deepreason/authority.py` | `text_status_authority_issues`, `AuthorityPolicyIssue` |
| The frozen fields compared runtime-vs-manifest | `src/deepreason/authority.py` | `authority_policy_snapshot` |
| The five per-run knobs | `src/deepreason/config.py` | `ARGUMENTATIVE_AUTHORITY`, `TEXT_RUBRIC_AUTHORITY`, `PAIRWISE_AUTHORITY`, `INFRASTRUCTURE_REVIEW_AUTHORITY`, `CALIBRATION_RECEIPT` |
| The engaged preset's compiled criticism authority (a sixth, differently-shaped knob: mirrors the manifest's two values directly, no translation) | `src/deepreason/config.py` | `ENGAGED_CRITICISM_AUTHORITY` |
| Where the knob is threaded into the compiled preset | `src/deepreason/v6_policy.py`, `src/deepreason/preparation.py` | `engaged_criticism_policy`, `build_preparation_manifest` |
| Whether the engaged preset routes criticism through a school at all (adjudication-judge-seats-optins tranche, S2c/R3, 2026-08-10: True compiles `criticism_policy=None`, Road E's school-free circuit, instead of `engaged_criticism_policy(...)`) | `src/deepreason/config.py`, `src/deepreason/preparation.py` | `LEGACY_CRITICISM_ENABLED` |
| Token budget for observe-only trials | `src/deepreason/config.py` | `ADVISORY_TRIALS_PER_CYCLE` |
| Prose-criticism vocabulary (manifest side) | `src/deepreason/rules/crit.py` | `_POLICY_AUTHORITIES` |
| Manifest word → Config word translation | `src/deepreason/rules/crit.py` | `_resolve_authority`, `_authority` |
| Observe-or-try branch | `src/deepreason/rules/crit.py` | `_TRIAL_MODES` (two call sites) |
| What `observe_only` actually records | `src/deepreason/rules/crit.py` | `_observe_case` |
| Rubric trial, both modes | `src/deepreason/informal/trial.py` | `run_trial` → `_trial_steps`, `_advisory_trial_result` |
| Precomputed-case trial, both modes | `src/deepreason/informal/trial.py` | `run_argument_trial_from_case` → `_argument_trial_steps` |
| Pairwise comparison | `src/deepreason/informal/trial.py` | `pairwise_discriminate` |
| String → enum coercion (the fail-fast boundary) | `src/deepreason/informal/trial.py` | `_coerce_trial_authority` |
| The frozen manifest field | `src/deepreason/run_manifest.py` | `CriticismPolicyV1.authority` |
| Compile-time and pre-adapter preflight | `src/deepreason/run_manifest.py` | `_preflight_text_authority`, `preflight_harness` |
| Rubric / pairwise call sites | `src/deepreason/scheduler/scheduler.py` | `Scheduler._criticize`, `Scheduler.step` |
| Infrastructure-review call site | `src/deepreason/ops.py` | `review_infrastructure` |
| Judge-ensemble independence: cross-family diversity, OR a structural same-model substitute (Amendment 9/R24, 2026-08-10 — narrower than same-family, so a same-family-different-model pair still fails; relies on the judge pack's content-blindness guarantee, `tests/test_judge_ensemble_boundary.py::test_judge_pack_never_names_an_author_school_or_model`; reachable only via `--blind-same-model-judges` on the manifest-compile CLI, mirrors the existing cross-school substitute's no-separate-flag shape) | `src/deepreason/llm/firewall.py`, `src/deepreason/run_manifest.py` | `require_cross_family_judge_ensemble`; `RunManifest`'s `rubric_policy` model-validator, `compile_run_manifest`'s own pre-check, `_validate_v4_criticism_policy`'s `defended_trial` branch |
| Pilot preflight that forbids all of it | `src/deepreason/jolts.py` | `JOLT_STATUS_AUTHORITY_FORBIDDEN` |
| Which ensemble a status trial must convene | `src/deepreason/llm/adapter.py` | `_select_judge_ensemble` |

## The rules it obeys

**Everything defaults to observe_only, and the receipt defaults to absent.** A
run that configures nothing spends no judge tokens on status-bearing text
adjudication.
`check: python -c "from deepreason.config import Config; c = Config(); assert c.ARGUMENTATIVE_AUTHORITY == 'observe_only'; assert {c.TEXT_RUBRIC_AUTHORITY.value, c.PAIRWISE_AUTHORITY.value, c.INFRASTRUCTURE_REVIEW_AUTHORITY.value} == {'observe_only'}; assert c.CALIBRATION_RECEIPT is None"`

**There are TWO vocabularies, and they share exactly one word.** `Config`'s
`ARGUMENTATIVE_AUTHORITY` admits three values; the manifest's
`CriticismPolicyV1.authority` admits two. `observe_only` is in both.
`trial_required` and `single_family_trial` are Config-only; `defended_trial` is
manifest-only.
`check: python -c "import typing; from deepreason.authority import _ARGUMENTATIVE_VALUES as v; from deepreason.config import Config; assert v == set(typing.get_args(Config.model_fields['ARGUMENTATIVE_AUTHORITY'].annotation)) == {'observe_only', 'trial_required', 'single_family_trial'}, v"`
`check: python -c "import typing; from deepreason.rules.crit import _POLICY_AUTHORITIES as p; from deepreason.run_manifest import CriticismPolicyV1 as C; assert set(typing.get_args(C.model_fields['authority'].annotation)) == p == {'observe_only', 'defended_trial'}"`

**`ENGAGED_CRITICISM_AUTHORITY` mirrors the manifest directly — no second
vocabulary.** Unlike `ARGUMENTATIVE_AUTHORITY`, this knob's value-space is
exactly `CriticismPolicyV1.authority`'s two values, and
`engaged_criticism_policy` passes it straight through with no translation
step, so the knob and the manifest field can never diverge into two closed
sets sharing one word. The knob defaults to `observe_only`, and passing it
explicitly reproduces the pre-switch hard-coded call byte-for-byte.
`check: python -m pytest tests/test_v6_policy_preset.py -k test_engaged_criticism_authority_config_default_preserves_prior_behavior -q`

**Neither vocabulary may be handed the other's word**, but only one of the two
refusals says which vocabulary the value belongs to. `_resolve_authority` does:
`ARGUMENTATIVE_AUTHORITY_NOT_MANIFEST_BOUND: ... 'single_family_trial' is a
Config-only mode`, so the caller learns the value is real and misplaced, not
misspelled. `argumentative_authority_mode` does not — a manifest word arriving
on the Config side gets `unsupported argumentative authority: defended_trial`,
indistinguishable from a typo. The asymmetry is real and unfixed; the check pins
both messages, so improving the weaker one shows up as a failing check rather
than passing silently.
`check: python -c "import pytest; from deepreason.authority import argumentative_authority_mode as m; from deepreason.rules.crit import _resolve_authority as r; pytest.raises(ValueError, m, {'ARGUMENTATIVE_AUTHORITY': 'defended_trial'}).match('^unsupported argumentative authority: defended_trial$'); pytest.raises(ValueError, r, None, 'single_family_trial', policy_call=True).match('ARGUMENTATIVE_AUTHORITY_NOT_MANIFEST_BOUND')"`

**The manifest vocabulary may never be widened.** `CriticismPolicyV1.authority`
is a frozen manifest `Literal`, and every qualification subject digest derives
from the manifest: admitting a third value there changes the schema and makes
roots that are replay-valid today read against a schema they were never written
under. A per-run mode goes on `Config`, which is invisible to replay. This is
DR-INV-frozen-surfaces surface 4, and `ARGUMENTATIVE_AUTHORITY` is deliberately
absent from `run_manifest.py` as a schema field.
`check: grep -q 'TEXT_AUTHORITY_POLICY_MANIFEST_MISMATCH' src/deepreason/run_manifest.py && ! grep -q 'ARGUMENTATIVE_AUTHORITY' src/deepreason/run_manifest.py`

**A manifest-bound criticism call may never rediscover authority from a mutable
`Config`.** It must carry the already-frozen policy value explicitly; passing
`None` on a policy call raises. Only direct (non-manifest) helpers read the
knob. `defended_trial` translates to `trial_required` on the way in, so the
value that reaches the branch is never the value stored in the manifest.
`check: python -c "import pytest; from deepreason.rules.crit import _resolve_authority as r; pytest.raises(ValueError, r, None, None, policy_call=True); assert r({}, None, policy_call=False) == 'observe_only'; assert r(None, 'defended_trial', policy_call=True) == 'trial_required'"`

**The criticism rule decides observe-or-try and nothing finer.** Both branches
read `authority in _TRIAL_MODES`; no branch tests a specific trial mode, so a
new mode cannot silently acquire a second, parallel route to a warrant. Which
judge ensemble the trial then demands is decided downstream by route topology.
`check: ! grep -q 'if authority == "trial_required"' src/deepreason/rules/crit.py && test "$(grep -c 'if authority in _TRIAL_MODES:' src/deepreason/rules/crit.py)" = 2`

**The trial never reads a knob.** Authority arrives as a parameter. The status
path (`_argument_trial_steps`) takes no `authority` argument at all — it is
reachable only through a caller that has already gated — while `_trial_steps`
carries the mode because the rubric trial has advisory exits at every guard.
`check: ! grep -qE 'ARGUMENTATIVE_AUTHORITY|argumentative_authority_mode' src/deepreason/informal/trial.py`
`check: python -c "import inspect; from deepreason.informal import trial; assert 'authority' not in inspect.signature(trial._argument_trial_steps).parameters; assert 'authority' in inspect.signature(trial._trial_steps).parameters"`

**An unrecognised authority string dies before any provider call.**
`_coerce_trial_authority` constructs the enum first, so a stale caller costs a
`ValueError`, not a partially-spent trial.
`check: python -m pytest tests/test_text_authority_policy.py -k legacy_trial_authority_is_rejected_before_provider_use -q`

**`observe_only` records scrutiny and mints nothing** — a critic-role artifact
with no warrants and a `["scrutiny", target, critic]` Measure. The target's
`Status` and the attack set are untouched.
`check: python -m pytest tests/test_text_authority_policy.py -k 'keeps_prose_criticism_as_scrutiny or keeps_infrastructure_review_as_scrutiny' -q`

**`calibrated_status` never yields status today.**
`calibration_receipt_is_verified` returns False unconditionally: no receipt
verifier exists, and a reference string is a claim about a receipt rather than a
checked one.
`check: python -c "from deepreason.authority import AuthoritySurface as S, TrialAuthority as T, trial_authority_for as f, calibration_receipt_is_verified as v; from deepreason.config import Config; assert not v(Config(CALIBRATION_RECEIPT='sha256:x')); assert f(Config(TEXT_RUBRIC_AUTHORITY='calibrated_status', CALIBRATION_RECEIPT='sha256:x'), 'text', S.RUBRIC) == T.OBSERVE_ONLY; assert f(Config(), 'code', S.RUBRIC) == T.OBSERVE_ONLY; assert f(Config(JUDGE_SEATS_ENABLED=True), 'code', S.RUBRIC) == T.STATUS"`

**This policy governs text workloads only.** The same check above records the
other half: for any `workload_profile` other than `"text"`,
`trial_authority_for` returns `STATUS` without reading a text-authority knob
-- but only once `JUDGE_SEATS_ENABLED` is on (Part D's master judge-dispatch
gate, off by default); at the default `False` it returns `OBSERVE_ONLY`
regardless of workload.

**Every surface knob is a real `Config` field**, and the surface enum and the
field map are the same size — a surface with no field would silently read the
`observe_only` default forever.
`check: python -c "from deepreason.authority import _SURFACE_FIELDS, AuthoritySurface; from deepreason.config import Config; assert len(_SURFACE_FIELDS) == len(AuthoritySurface) == 3; assert set(_SURFACE_FIELDS.values()) <= set(Config.model_fields)"`

**Manifest-mediated runs fail closed twice**: at compile, and again before the
adapter is built. A status mode without a receipt is `CALIBRATION_RECEIPT_REQUIRED`;
with an unverified reference it is `CALIBRATION_RECEIPT_UNVERIFIED`; a runtime
`Config` whose authority snapshot differs from the frozen manifest's is
`TEXT_AUTHORITY_POLICY_MANIFEST_MISMATCH`.
`check: python -m pytest tests/test_manifest_integration.py -k 'calibration_receipt or frozen_text_authority' -q`

**V6 refuses `defended_trial` at manifest compile**, not during dispatch: the
mode has no transactional dispatch contract, so the failure belongs to
compilation rather than to a half-spent cycle.
`check: python -m pytest tests/test_v6_manifest_defended_trial.py -q`

**A jolt pilot may hold no authority at all.** All four authority fields —
`ARGUMENTATIVE_AUTHORITY` plus the three surface knobs — must be `observe_only`,
and `CALIBRATION_RECEIPT` must be unset. The four share one typed refusal,
`JOLT_STATUS_AUTHORITY_FORBIDDEN`; the receipt has its own,
`JOLT_CALIBRATION_RECEIPT_FORBIDDEN`.
`check: python -c "import ast, inspect; from deepreason import jolts; s = inspect.getsource(jolts); f = [{e.attr for e in n.value.elts} for n in ast.walk(ast.parse(s)) if isinstance(n, ast.Assign) and any(getattr(x, 'id', None) == 'authority_fields' for x in n.targets)]; assert f == [{'ARGUMENTATIVE_AUTHORITY', 'TEXT_RUBRIC_AUTHORITY', 'PAIRWISE_AUTHORITY', 'INFRASTRUCTURE_REVIEW_AUTHORITY'}], f; assert 'JOLT_STATUS_AUTHORITY_FORBIDDEN' in s and 'JOLT_CALIBRATION_RECEIPT_FORBIDDEN' in s"`

## Where to change what

| To change... | Edit | Test |
|---|---|---|
| Add a per-run authority mode | `config.py` `ARGUMENTATIVE_AUTHORITY` Literal, `authority.py` `_ARGUMENTATIVE_VALUES` + `_TRIAL_AUTHORITIES`, `rules/crit.py` `_TRIAL_MODES` | `python -m pytest tests/test_prose_refutation_boundaries.py -k "config_only or routes_to_the_same" -q` |
| Make a mode reachable at all | Nothing — reachability is `ADJUDICATION_STATUS_AUTHORITY_ENABLED`'s job, the master gate every knob above (and `ENGAGED_CRITICISM_AUTHORITY`) sits behind; a new mode inherits it automatically at whichever consumption site it's read from | `python -m pytest tests/test_text_authority_policy.py::test_master_gate_forces_observe_only_even_when_trial_configured tests/test_v6_engaged_public_defaults.py::test_engaged_criticism_authority_inert_without_the_master_gate -q` |
| Land a calibration-receipt verifier | `authority.py` `calibration_receipt_is_verified` — the single attachment point | `python -m pytest tests/test_text_authority_policy.py -k unverified_calibrated -q` |
| Add a fourth adjudication surface | `authority.py` `AuthoritySurface` + `_SURFACE_FIELDS`, a `Config` field, `jolts.py` `authority_fields` | `python -m pytest tests/test_manifest_integration.py -k calibration_receipt -q` |
| Change what `observe_only` files | `rules/crit.py` `_observe_case` (Measure inputs are compared against recorded roots — see Traps) | `python -m pytest tests/test_text_authority_policy.py -k scrutiny -q` |
| Add or move an advisory exit in the rubric trial | `informal/trial.py` `_trial_steps` + `_advisory_trial_result` | `python -m pytest tests/test_trial.py tests/test_text_authority_policy.py -k rubric -q` |
| Change which ensemble a status trial convenes | `llm/adapter.py` `_select_judge_ensemble` — not an authority decision | `python -m pytest tests/test_prose_refutation_boundaries.py -k cross_school -q` |
| Widen the manifest authority vocabulary | Don't. DR-INV-frozen-surfaces surface 4; put the mode on `Config` | `python -m pytest tests/test_v6_manifest_defended_trial.py -q` |

## Traps

- **Reading one vocabulary and assuming the other.** `_POLICY_AUTHORITIES`
  (manifest) and `_ARGUMENTATIVE_VALUES` (Config) are separate closed sets, and
  the 2026-08-01 tranche had to choose between reconciling them and keeping them
  apart. It kept them apart, because admitting `single_family_trial` to the
  manifest set would have changed a frozen `Literal` and every qualification
  subject digest derived from it. Evidence:
  `experiments/2026-08-01-change-prose-can-refute/CHECKLIST.md` step 11.
- **A computed authority silently discarded.** `trial_authority_for` once
  returned unconditionally, so `TEXT_RUBRIC_AUTHORITY`, `PAIRWISE_AUTHORITY` and
  `INFRASTRUCTURE_REVIEW_AUTHORITY` were unreadable from the code — the value
  was computed and thrown away. Fixed in step 10 of the same tranche by naming
  the block (`calibration_receipt_is_verified`) instead of honouring the knob,
  because honouring it would have deleted the only safeguard on that path.
  Behaviour was unchanged; readability was the whole point.
- **Assuming the manifest preflight covers every path.** It does not.
  `ops.review_infrastructure` and both scheduler call sites reach
  `trial_authority_for` with no manifest in play, so
  `text_status_authority_issues` — the function that refuses an unverified
  receipt — never runs for them. On those three paths
  `calibration_receipt_is_verified` is the entire gate between a reference
  string in a config file and live status authority.
- **Treating a receipt reference as a receipt.** `calibration_receipt` only
  strips whitespace and rejects blanks. A declared reference upgrades the
  refusal from `CALIBRATION_RECEIPT_REQUIRED` to `CALIBRATION_RECEIPT_UNVERIFIED`;
  it never upgrades it to acceptance.
- **Assuming authority picks the judge ensemble.** It does not. Cross-family
  governs whenever more than one route family is present; the cross-school
  substitute is reachable only under `is_single_family_run` with school
  bindings configured. Route topology decides, and no configuration value can
  prefer the substitute where the guarantee it substitutes for is obtainable.
- **Assuming everything is advisory by default.** True for `workload_profile ==
  "text"` only. A `code` or `formal` run's rubric trial gets `TrialAuthority.STATUS`
  without consulting any knob.
- **Renaming what `observe_only` writes.** The `["scrutiny", target, critic]`
  Measure inputs are compared against recorded roots, exactly as
  `execution-backed` was kept spelled that way when its guard widened. Changing
  the strings reinterprets stored evidence — see DR-INV-frozen-surfaces.

## Adjacent, not authority: preset-construction hygiene in `v6_policy.py`

This document is the established `Owns:` home for `v6_policy.py` and
`preparation.py` (added when `ENGAGED_CRITICISM_AUTHORITY` landed), not
because every claim about those files is about authority — the claim
below is not. It lives here because no other `docs/map/` document owns
these two files, and creating a new one for a single hygiene fix would
be disproportionate; `docs/map/INDEX.md` was checked first and lists no
better home.

**`engaged_bridge_source()` builds through `BridgeConfig`, not a
parallel hard-coded literal.** The engaged preset's compiled bridge
settings (`mode`, `grounding_review`, `max_schema_repair_attempts`,
`max_grounding_repair_attempts`, `output_section_limit`) are constructed
by instantiating `BridgeConfig` with the preset's override values and
projecting onto those five fields — not by writing a bare dict that
could silently drift from `BridgeConfig`'s own field names, types, and
validators. `BridgeConfig`'s own class-level defaults (`config.py`,
`mode="legacy_thesis"` etc.) are deliberately UNCHANGED: they are the
tested "safe by default, features remain opt-in" contract every bare
`Config()` relies on (`tests/test_config_scratch_bridge.py::
test_safe_defaults_are_bounded_and_features_remain_opt_in`), not a dead
value — only the engaged preset's explicit override differs from them.
`check: python -c "import inspect; from deepreason import v6_policy as p; src = inspect.getsource(p.engaged_bridge_source); assert 'BridgeConfig(' in src"`
