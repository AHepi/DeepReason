# Spec for: rung 2, tranche 2 — the engaged_criticism_policy Config switch
Traces: every item cites R/C numbers. Untraceable items are bugs.

Map preflight: `DR-CON-authority` (rung 1; already documents the four
existing authority `Config` knobs and the "two vocabularies" design —
this switch adds a fifth, differently-shaped knob), `DR-INV-frozen-
surfaces` (surface 4: manifest schemas AND validators frozen; "Where
authority is allowed to live instead" is this switch's precedent
section). `src/deepreason/v6_policy.py` and `src/deepreason/preparation.py`
are NOT currently `Owns:`-listed by any `docs/map/` document — this is a
map gap the tranche must close (R7), not scope creep: the smallest fix
is adding both files to `DR-CON-authority`'s `Owns:` (it already governs
"where authority is allowed to live"; the compiled-preset authority
choice belongs there, not a new document).

## Resolving Q1-Q3 (dr-ask-the-right-question applied; record first)

**Q1 (field name).** Resolved from the record: the four existing
authority fields follow `<WHAT>_AUTHORITY` (`ARGUMENTATIVE_AUTHORITY`,
`TEXT_RUBRIC_AUTHORITY`, `PAIRWISE_AUTHORITY`,
`INFRASTRUCTURE_REVIEW_AUTHORITY`). The new field governs the ENGAGED
preset's compiled criticism policy specifically — matching
INVENTORY.md's own label ("Criticism authority") and distinguishing it
from `ARGUMENTATIVE_AUTHORITY`, which CON-authority.md already
documents as governing "a *different* code path." Name:
**`ENGAGED_CRITICISM_AUTHORITY`**. Recorded as **A1**.

**Q2 (test location).** Resolved from the record: `grep` found
`tests/test_v6_policy_preset.py` already exercises
`engaged_criticism_policy` directly (including
`test_engaged_criticism_policy_binds_every_public_school_observe_only`,
which asserts `policy.authority == "observe_only"` on a no-kwarg call —
this test must keep passing UNCHANGED, which is itself part of the
default-preservation proof) and
`tests/test_v6_engaged_public_defaults.py` exercises it end-to-end
through a compiled manifest (`criticism == engaged_criticism_policy(
profile.endpoint_id)`, `criticism.authority == "observe_only"`). Smallest
reasonable choice: ADD one new test function to
`tests/test_v6_policy_preset.py` (the file already dedicated to this
preset's construction functions) rather than a new file. Recorded as
**A2**.

**Q3 (Config field's value-space — mirror the manifest's 2 values, or
translate through a different vocabulary like `ARGUMENTATIVE_AUTHORITY`
does?).** Resolved from the record, not a real fork: re-reading
CON-authority.md's "two vocabularies" section, the translation pattern
exists BECAUSE `ARGUMENTATIVE_AUTHORITY` expresses a THIRD, Config-only
mode (`single_family_trial`) that has no manifest counterpart at all —
the two vocabularies diverge because one side has an extra option the
other cannot express. This switch has no such extra option: it exists
only to pick between the manifest's own two already-valid values
(`observe_only`/`defended_trial`) for the compiled preset. Inventing a
third value or a differently-shaped vocabulary here would be adding
complexity the requirement never asked for. The new field is
**`Literal["observe_only", "defended_trial"]`**, mirroring
`CriticismPolicyV1.authority` exactly. Recorded as **A3**.

Also resolved without asking, from reading `preparation.py` and
`qualification.py` directly: `engaged_policy_digest()` (called at
`v6_policy.py:461` with the template endpoint, and consumed by
`qualification.py` as a SEPARATE `policy_preset_digest` field) does
**not** need to change. The qualification subject's sensitivity to a
changed authority value already flows through
`qualification_subject_payload`'s `behavior = manifest.model_dump(...)`
dump of the WHOLE compiled manifest — `criticism_policy.authority` is
already part of that dump today (it would just never vary, since the
value was hard-coded). `engaged_policy_digest()`'s own template call
represents the preset's fixed nominal identity and correctly keeps its
default-only behavior via `engaged_criticism_policy`'s own default
parameter (see S2). No frozen-surface-5 (qualification subject) code
changes — only its ALREADY-EXISTING dependency on the compiled
manifest's contents does the work, exactly as `DR-INV-frozen-surfaces`'
existing precedent describes for the research allowlist and simulation
runner. Recorded as **A4**.

No reading above differs materially enough to warrant a stop.
**Questions for operator: none.**

## Items

S1 (R1, R2, C1): Add `ENGAGED_CRITICISM_AUTHORITY:
Literal["observe_only", "defended_trial"] = "observe_only"` to
`src/deepreason/config.py`, placed beside the four existing authority
fields (near line 389). Before: no field exists. After: the field exists,
defaults to `"observe_only"` (A1, A3).
accept: `grep -q 'ENGAGED_CRITICISM_AUTHORITY: Literal\["observe_only", "defended_trial"\] = "observe_only"' src/deepreason/config.py`
(or equivalent exact match) AND `python -c "from deepreason.config import Config; assert Config().ENGAGED_CRITICISM_AUTHORITY == 'observe_only'"`.

S2 (R1, R2): Change `src/deepreason/v6_policy.py::engaged_criticism_policy`'s
signature from `(endpoint_id: str) -> CriticismPolicyV1` to
`(endpoint_id: str, *, authority: str = "observe_only") -> CriticismPolicyV1`
(keyword-only, default matching the current hard-coded literal exactly,
so EVERY existing call site — including `engaged_policy_digest()`'s
template call at line 461, which passes no `authority` kwarg — keeps
byte-identical behavior). Replace the hard-coded `authority="observe_only"`
at line 212 with `authority=authority`.
accept: `python -c "from deepreason.v6_policy import engaged_criticism_policy as f; assert f('e').authority == 'observe_only'; assert f('e', authority='defended_trial').authority == 'defended_trial'"`.

S3 (R1, R2): In `src/deepreason/preparation.py::build_preparation_manifest`,
capture `_config_for_profile(profile)` in a local variable and thread its
new field into the `engaged_criticism_policy` call: change
`criticism_policy=engaged_criticism_policy(profile.endpoint_id)` to
`criticism_policy=engaged_criticism_policy(profile.endpoint_id, authority=config.ENGAGED_CRITICISM_AUTHORITY)`
where `config = _config_for_profile(profile)` is now a named local passed
unchanged as `compile_run_manifest`'s first positional argument (no
behavior change to that argument).
accept: `python -c "import inspect; from deepreason import preparation as p; src = inspect.getsource(p.build_preparation_manifest); assert 'config.ENGAGED_CRITICISM_AUTHORITY' in src"`.

S4 (R6): Add ONE new test to `tests/test_v6_policy_preset.py` (A2)
proving the switch's default equals prior behavior: `Config()`'s new
field is `"observe_only"`, and `engaged_criticism_policy(endpoint,
authority=Config().ENGAGED_CRITICISM_AUTHORITY)` produces a policy equal
(`==`, full pydantic model equality) to the pre-existing no-kwarg call
`engaged_criticism_policy(endpoint)`.
accept: `python -m pytest tests/test_v6_policy_preset.py -q` 0 failed,
new test named and collectable.

S5 (R7): Update `docs/map/CON-authority.md` in the SAME commit as S1-S3:
add `src/deepreason/v6_policy.py` and `src/deepreason/preparation.py` to
its `Owns:` header; add `ENGAGED_CRITICISM_AUTHORITY` to its "Where it
lives" table (the fifth per-run authority knob); add one new checked
claim to "The rules it obeys" proving the default-preservation property
with a real check (reusing/citing S4's test, not re-deriving a duplicate
check); extend the existing "Every surface knob is a real Config field"
style claim if it enumerates the four knobs by count (verify whether it
does before deciding to touch it — see PARKED.md if a count-check would
need updating and isn't touched here).
accept: `grep -q "ENGAGED_CRITICISM_AUTHORITY" docs/map/CON-authority.md`
AND `python tools/docs_verify.py` 0 failed AND `--audit` 0 findings.

S6 (R4, R5): Full gate and root sweep, run and pasted, after S1-S5 land:
`python -m pytest tests/ -q -n 4` (expect ~3290 passed, 0 failed — rerun
once if only the known flake,
`test_grounded_counterexample_recovery_does_not_invent_override_on_repeat`,
fails under `-n 4`, per C3); `python tools/root_sweep.py` compared
before/after this tranche's code changes — must be byte-identical (42
rows, 11 ERROR expected per ERRATA E5/E6/E8).

## Assumptions (operator may override)

A1 (Q1): field name `ENGAGED_CRITICISM_AUTHORITY`, following the existing
`<WHAT>_AUTHORITY` convention and distinguishing this code path from
`ARGUMENTATIVE_AUTHORITY`'s different one.

A2 (Q2): the new test lands in `tests/test_v6_policy_preset.py` (already
the dedicated file for these preset-construction functions), as one new
function, not a new file and not an edit to the existing observe-only
assertion test.

A3 (Q3): the new field's value-space is `Literal["observe_only",
"defended_trial"]`, mirroring `CriticismPolicyV1.authority` directly —
no translation layer, because (unlike `ARGUMENTATIVE_AUTHORITY`) there is
no third, Config-only value to express.

A4 (frozen-surface reasoning, not itself an open question but recorded
for the operator's visibility): `engaged_policy_digest()` and
`qualification.py` need NO code change — the qualification subject
already picks up a criticism-authority change through the compiled
manifest's own field dump, and `engaged_policy_digest()`'s template call
preserves its default via `engaged_criticism_policy`'s own default
parameter.

## Questions for operator

None.

## Out of scope (explicit)

- Rung 2's `Group B` finding (`BridgeConfig` vs `engaged_bridge_source()`)
  and any other inventory candidate. Not requested this tranche — that
  is the operator's later "TRANCHE 3" (or beyond).
- Flipping `ENGAGED_CRITICISM_AUTHORITY`'s default to anything other than
  `"observe_only"` (R3, hard prohibition). If a case exists for
  `"defended_trial"` as the intended default, it goes in `PARKED.md`,
  never implemented here.
- Touching `qualification.py` or `engaged_policy_digest()`'s signature —
  A4 establishes neither needs to change for this switch to be correct.
- Any change to `run_manifest.py`'s `CriticismPolicyV1.authority`
  `Literal` (frozen surface 4) — this switch selects between its two
  EXISTING values, never widens them.
- Wiring `ENGAGED_CRITICISM_AUTHORITY` into any code path other than the
  engaged preset's compiled `criticism_policy` (e.g. the `conservative`
  preset, which hard-codes no criticism policy at all today and is out
  of this switch's stated scope).

## Amendment 1 (discovered executing step 4/S3, R7)

S7 (R7): `docs/map/SEAM-manifest-x-schools.md`'s checked claim at line 153
("The only in-tree author") greps the exact literal call-site text
`criticism_policy=engaged_criticism_policy(profile.endpoint_id)` in
`src/deepreason/preparation.py` as part of proving `engaged_criticism_policy`
is `preparation.py`'s only in-tree caller of that shape. S3's edit
(threading `authority=config.ENGAGED_CRITICISM_AUTHORITY` into that call)
changes the literal text without changing the property the check exists to
prove (the call still passes `profile.endpoint_id` positionally, still
defaults to `observe_only`). This was not anticipated by S1-S6 — SPEC.md's
own preflight only flagged `v6_policy.py`/`preparation.py` as un-owned by
any document, not that a THIRD document's check depended on the literal
call-site substring. Not new scope: `docs_verify.py` must be 0 failed
before any commit (standing rule), and R7 requires map and code to move
together — this is the same requirement surfacing in a second document.
Fix: update the trailing `grep` to match the new call-site text
(`criticism_policy=engaged_criticism_policy(\n            profile.endpoint_id, authority=config.ENGAGED_CRITICISM_AUTHORITY\n        )` or an equivalent substring proving the same wiring), changing no other
part of the check (the `E('ep')` no-kwarg assertions above it already prove
default preservation and are untouched).
accept: `python tools/docs_verify.py --fast` 0 failed (SEAM-manifest-x-schools.md's check specifically passing).

## Amendment 2 (discovered executing step 8/S5, R4 + DR-INV-frozen-surfaces surface 4)

S8 (R4, C1): the full `docs_verify.py` run surfaced a THIRD-order break:
`tests/test_run_manifest_v4.py::test_v1_v2_v3_canonical_shapes_and_hashes_remain_byte_identical`
fails for schema_version 1, 2, AND 3 after S1's `Config` field addition.
Root cause: `src/deepreason/run_manifest.py::_source_config_data` does
`config.model_dump(mode="json")` unconditionally, so ANY new `Config`
field appears in `source_config_hash`/`engine_config_json`/the compiled
manifest's `sha256` for every schema version — unless scrubbed by
`_versioned_source_config_data`, whose own docstring names exactly this
failure mode: "`Config.model_dump` necessarily gains the typed scratch
and bridge defaults in this tranche. Those keys did not exist when v1/v2
source hashes... were defined, so retaining them would make the same old
profile acquire a different identity after an upgrade." The established,
precedented fix (commit `2d6c2a4c`, "config: freeze scratch and bridge
policy in RunManifest v3") pops newly-added keys from
`_versioned_source_config_data`'s output for the schema versions that
predate them (`schema_version < 3` for scratch/bridge). Verified via git
archaeology: the pinned v1/v2/v3 hash literals were last set by commit
`bf4d2709` (2026-07-16), AFTER both `ARGUMENTATIVE_AUTHORITY`-family
fields (`053a297e`, 2026-07-14) and the scratch/bridge freeze (`2d6c2a4c`,
2026-07-15) — those fields were already part of `Config`'s dump when the
pins were last computed, which is why they cause no drift today. This is
the FIRST new top-level `Config` field added since `bf4d2709`, so it is
the first to hit the un-scrubbed case.

This is `DR-INV-frozen-surfaces` surface 4 territory (`run_manifest.py`),
but the governing principle there is explicit: "a change that alters
what a FUTURE run may do is ordinary work... fix READERS so old roots
stay valid." Popping the new key from schema versions 1-3's echoed
source config is exactly a reader fix, preserving v1/v2/v3's frozen
identity against an otherwise-ordinary `Config` addition — not a widened
validator, not a changed schema shape, not new manifest semantics. It is
NOT flipping any default or authority value (R3 remains untouched).

Fix, first attempt (superseded — see below): pop the key only for
`schema_version < 4`, on the assumption that "no schema version above 3
has any pinned-hash test today." **That assumption was wrong.** The
first full-gate run (step 10) surfaced TWO further failures the
`schema_version < 4` guard did not cover:
`tests/test_run_manifest_v5_inquiry.py::test_v5_canonical_bytes_match_incident_head_golden`
(a schema-v5 canonical-bytes-length-and-hash golden, docstring: "V6
installation must not change the last active-inquiry wire bytes") and
`tests/test_incident_wave_a_v2_fixtures.py::test_incident_descriptors_and_generated_roots_are_frozen_and_deterministic`
(schema-v5 incident-fixture root digests, pinned in
`tests/fixtures/incidents/DR-2026-07-16-AUTONOMOUS-INQUIRY-WAVE-A/PROVENANCE.json`
against `repository_commit: 056af85e4c6018bcdf44e73c2ada78fabccb4a81`).
Both are v5, both assert byte-for-byte stability against exactly this
kind of addition, and neither is named anything like "v1_v2_v3" — so
"no test above v3" was a false inference from an incomplete grep, not a
verified fact.

Fix, corrected: pop `ENGAGED_CRITICISM_AUTHORITY` from
`_versioned_source_config_data`'s output UNCONDITIONALLY (every schema
version, not just `< 3` or `< 4`). This is safe and loses no
information: the field's actual runtime effect is already visible in
the compiled manifest's own first-class `criticism_policy.authority`
field (present since schema v4, where `criticism_policy` became
manifest-bound) — the `Config` echo in `engine_config_json`/
`source_config_hash` is a redundant reflection of raw `Config` state,
not the authoritative record of what a run did. Scrubbing it
unconditionally sidesteps needing to enumerate every present-and-future
schema version's golden-test coverage, matching the more conservative
of the two options considered rather than continuing to whack-a-mole
one schema version at a time.

accept: `python -m pytest tests/test_run_manifest_v4.py tests/test_run_manifest_v5_inquiry.py tests/test_incident_wave_a_v2_fixtures.py -q` 0 failed AND `python -m pytest tests/ -q -n 4` 0 failed (full gate, S6/R4).

## Budget

~15 lines (`config.py` field + docstring), ~5 lines (`v6_policy.py`
signature + one-line body change), ~5 lines (`preparation.py` local
variable + call-site change), ~20 lines (one new test), ~20-30 lines
(`CON-authority.md` update). Total ~65-75 lines, 1-2 commits (code+map
together per R7, then a gate-confirmation commit). Well under the
300-line guideline.

Frozen surfaces touched, revised after Amendment 2: `run_manifest.py`
(surface 4) IS written — one line added to `_versioned_source_config_data`
(the existing, precedented pop-list mechanism, widened by one key), per
Amendment 2's own reasoning (a reader-preserving fix, not a widened
validator or changed schema shape). `qualification.py` remains untouched;
A4's reasoning there is unaffected by Amendment 2.
