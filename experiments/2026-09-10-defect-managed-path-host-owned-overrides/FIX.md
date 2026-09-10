# Fix: the managed path carries a configured embedder and says on the manifest which of the operator's values it took

Guarantee restored: on the managed `deepreason reason` path, every value the
operator's configuration states is either carried into the run or named by a
typed notice on the compiled manifest saying the host took it — so no
configured setting, the measurement scale included, can be replaced in
silence.

## The two halves, and why they are shaped differently

**Half 1 — the embedder is CARRIED.** `EMBEDDER_MODEL` needs no new machinery
anywhere: `compile_run_manifest` already compiles
`scratch_policy.embedder_backend = "neural"` from a configured model
(`run_manifest.py:2962-2996`), and `ops.make_embedder` already builds it,
already falls back typed when the backend cannot be built, and already reports
both through `deepreason results`. Six committed non-managed manifests compile
`neural` today (`probe/census.out`). Only `preparation`'s override stands
between the managed door and that road, and REPRO.md observation 3 measures
exactly that: the same rebuilt configuration with the one field restored
stamps the neural fingerprint in the same process.

**Half 2 — the other six are DISCLOSED, not carried.** Stated plainly as the
brief requires: this is a disclosure-only road for `engine_profile`,
`model_profile`, `scratchpad`, `bridge`, `CHANNELS_DISABLED` and `roles`. The
host keeps its value for all six and the record says so. Two of them are the
reason the override exists at all — `roles` and `model_profile` bind the
endpoint and the credential, and a configuration file that could redirect a
managed run to another endpoint is a security hole, not a feature. The other
four are preset choices with no such argument, and whether they should be
carried is the operator's call, parked with a ready-to-send prompt
(`PARKED.md` P5). Nothing in this tranche decides it; closing the silence is
what the 2026-08-28 law requires and what GOAL.md asks for.

## Why the disclosure reuses `ENGINE_CONFIG_FIELD_NOT_CARRIED`

A new notice code was designed first and REJECTED on a measurement, recorded
here so a reviewer does not re-derive it.

`qualification_subject_payload` strips exactly one code from the subject —
`ENGINE_CONFIG_FIELD_NOT_CARRIED` (`qualification.py:264-273`) — and keeps
every other notice. So a new code would enter the qualification subject and
move the digest of every managed run that emits one. Fifteen committed
run-configs name `roles`; two name `CHANNELS_DISABLED`; the operator's own
`config/deepseek.yaml` and `config/ollama-live.yaml` are two of the fifteen.
Every one of them would newly owe each home a ~14-minute, ~1160-call battery
for a run whose compiled behaviour is byte-identical to what it compiles
today — the exact waste the 2026-08-28 grant to frozen surface 5 was granted
to prevent, whose own rule reads: "a disclosure that a subject-excluded
`Config` field was not carried must not itself enter the qualification
subject, or the exclusion is defeated by its own disclosure"
(`INV-frozen-surfaces.md` §5). Excluding a second code means editing
`qualification.py` — frozen surface 5, a grant, and a stop.

The existing code needs neither, and it is not a second meaning smuggled into
one signal. The code names a fact — this `Config` field's configured value is
not carried by this manifest's engine config — and that fact is true of all
six: three (`engine_profile`, `model_profile`, `roles`) sit in the echo
holding the HOST's value, and three (`scratchpad`, `bridge`,
`CHANNELS_DISABLED`) are absent from it entirely
(`run_manifest.py:4031-4036`, and the census in DIAGNOSIS.md). What the
notice's `value` field decides is RESTORATION, and the reader already
implements both arms deliberately: `_carried_config_values` skips any notice
whose `value` is None before it checks anything else
(`run_manifest.py:4562`), and `CompileNoticeV1`'s own field documentation says
"None when the notice carries nothing" (`run_manifest.py:1202-1205`). That
second arm has had no producer until now. This fix is its first.

`value=None` is not a convenience here, it is mandatory. A notice carrying the
overridden value would restore it at run time — `run_manifest.py:1203`, "a
disclosure is also the road back" — which for `roles` and `model_profile`
would re-arm precisely the endpoint redirection the override exists to
forbid.

## Change sites (exhaustive)

- `src/deepreason/preparation.py:374-394` — the `owned` dictionary moves into
  a new `_host_owned_values(profile, *, base, channels_disabled, roles)`
  helper so the configuration builder and the notice builder read ONE
  definition of the seven. No value changes here.
- `src/deepreason/preparation.py`, inside that helper — `EMBEDDER_MODEL` is
  omitted from the host-owned set when `base is not None and
  "EMBEDDER_MODEL" in base.model_fields_set`, so `data.update(owned)` leaves
  the operator's stated model in place. When the operator states nothing the
  host's `None` stands exactly as today, which is what keeps the default
  managed manifest and its qualification subject digest byte-identical.
- `src/deepreason/preparation.py`, new `_host_override_notices(base, owned)` —
  one `CompileNoticeV1` per host-owned field the operator EXPLICITLY stated
  (`base.model_fields_set`) to a value the host does not use: code
  `ENGINE_CONFIG_FIELD_NOT_CARRIED`, pointer `/engine_config/<field>`,
  `value=None`, a message naming the operator's value and the host's, and a
  `resolution` pointing at the manifest field that DOES carry what the run got
  (`/roles`, `/scratch_policy`, `/bridge_policy`, `/inquiry_capability_policy`)
  where one exists.
- `src/deepreason/preparation.py:549` (`build_preparation_manifest`'s return) —
  when there are notices, the compiled manifest is re-validated with them
  appended (`RunManifest.model_validate({**manifest.model_dump(mode="json"),
  "compile_notices": [...]})`); when there are none the compiled manifest is
  returned untouched, so a run with no operator configuration is byte-identical
  to today. Re-validation rather than `model_copy` so the model's own
  validators still run; measured to round-trip to the same sha.
- `src/deepreason/application/stop_report.py:202-215` — each gate row gains
  `"restored": notice.get("value") is not None`, and the four render sites
  that today say "restored at run time from notice"
  (`:214`, `:558-561`, `:735`, `:898-901`) say instead, for a value-less
  notice, that the host owns the value on the managed path and it was NOT
  restored. A reader fix: the report must not tell an operator their setting
  took effect when it did not.
- `src/deepreason/application/stop_report.py:591-593` — the ruling-out
  sentence counts only rows whose `restored` is true, so "N field(s) were
  restored" stays a true sentence.

## Regression artifact

Must invert: `python -u experiments/2026-09-10-defect-managed-path-host-owned-overrides/repro_managed_override.py`
— exit 0, with observation 1 reporting `neither carried nor disclosed: 0 of 7`,
observation 2 reporting `backend='neural'`, `Measure kinds on the log:
['embedder']` and `embedder: neural (nomic-ai/nomic-embed-text-v1.5)`, and
observation 3 unchanged. REPRO.md's post-fix section states the one legitimate
alternative for observation 2 (a container with no weights records
`embedder-fallback`), and the script already accepts it.

New conditions this fix must be tested against, in
`tests/test_managed_path_host_owned_values.py`, each mutation-proven (it fails
when its own fix line is reverted):

1. SEVEN parametrised cases, one per host-owned value: an operator
   configuration stating that value away from the host's own compiles a
   manifest that either carries it or names it in exactly one
   `ENGINE_CONFIG_FIELD_NOT_CARRIED` notice. No case may be silent.
2. `EMBEDDER_MODEL` specifically is CARRIED: `scratch_policy.embedder_backend
   == "neural"`, `scratch_policy.embedder_model` is the operator's model, and
   `config_from_run_manifest(manifest).EMBEDDER_MODEL` is that model — the
   arm roots' exact condition, and the test the five arms would have failed.
3. The six are disclosed and NOT restored: each notice has `value is None`,
   and `config_from_run_manifest` returns the HOST's value for every one of
   them — the endpoint boundary holds. `roles` and `model_profile` are named
   in the test's docstring as the reason.
4. A configuration that states NOTHING compiles a manifest byte-identical to
   one compiled with no configuration at all: same `sha256`, same
   `source_config_hash`, zero notices.
5. The DEFAULT managed qualification subject digest is byte-identical to its
   committed value, and so is the digest of a configuration that sets one of
   the six — carrying no notice into the subject is the property, and it is
   asserted, not argued.
6. A configuration that names an embedder DOES move its own subject digest,
   and the test says so rather than hiding it: a different scratch policy is
   a different subject, and that home owes one battery. This is the price,
   stated where a reader will meet it.
7. `deepreason results` on a run prepared from an embedder-naming
   configuration prints the neural model — through `embedder_summary_for_root`
   and `embedder_line`, the functions the CLI calls.

## Existing tests at risk (from grep over the changed symbols)

- `tests/test_managed_path_config_read.py::test_a_default_valued_operator_config_changes_nothing`
  — asserts an empty operator configuration compiles byte-identically. MUST
  KEEP PASSING; it is the reason the fix keys on `model_fields_set` instead of
  on a comparison against `Config()`'s defaults, whose `EMBEDDER_MODEL` is the
  neural model and therefore indistinguishable from a stated one.
- `tests/test_managed_path_config_read.py::test_managed_manifest_carries_or_discloses_every_operator_setting`
  — the same law over five switches that are not among the seven. Keeps
  passing unchanged; the new file extends it to the seven rather than
  rewriting a committed fixture.
- `tests/test_manifest_config_disclosure.py::test_every_dropped_field_the_managed_path_can_set_round_trips`
  — skips `CHANNELS_DISABLED` because the host overwrites it and no round trip
  is possible. Keeps passing and stays correct: after this fix a value-less
  notice says so, and still does not restore. Its comment gains one line.
- `tests/test_manifest_config_disclosure.py::test_carriage_moves_no_qualification_subject_digest_it_did_not_already_move`
  — keeps passing: the new notices ride the stripped code.
- `tests/test_stop_report.py:223` — builds a notice under that code with a
  value; the restored wording is unchanged for it. Keeps passing.
- `tests/test_single_run_path.py:383-395` — asserts five expected
  `(code, pointer)` pairs from a configuration setting none of the seven.
  Keeps passing.
- `tests/test_reusable_qualification.py` — the digest pins. Keeps passing, and
  gains condition 5 above.
- `tests/test_seat_bindings.py:159` and `tests/test_reusable_qualification.py:55`
  call `_config_for_profile` directly and use its return as a `Config`. Its
  signature and return type are unchanged by design, for exactly this reason.
- `tests/test_embedder.py:479` — a docstring naming the host-owned exemption.
  Reworded in this commit to say what is now true.
- UNKNOWN until measured: any test asserting a managed manifest's exact
  `compile_notices` length under a configuration that sets one of the seven.
  The ring (`tests/test_managed_path_config_read.py
  tests/test_manifest_config_disclosure.py tests/test_reusable_qualification.py
  tests/test_stop_report.py tests/test_single_run_path.py
  tests/test_embedder.py tests/test_results_command.py
  tests/test_seat_bindings.py`) runs first for exactly this; the full gate at
  the boundary decides it.

## Map, in the same commit

- `docs/map/CON-configuration-stages.md` — stage 3 gains the second arm: a
  notice with no `value` discloses a value the host TOOK and does not restore
  it, so a reader who sees the notice must not conclude the setting took
  effect. New `check:` that fails if the disclosure stops being emitted.
- `docs/map/CON-seats.md` (the line naming the seven) — six are host-owned and
  disclosed; `EMBEDDER_MODEL` is carried when the operator states it.
- `docs/map/SUB-llm.md` Traps — a new entry beside the 2026-08-16 and
  2026-09-09 embedder entries, naming the five brief-variation arm roots
  (`experiments/2026-09-04-experiment-brief-variation-step1/roots/{A0,A1,A1P,A2,A3}-run-fe00609058e10605590206d51ab2b7a0`)
  and stating what closed: the managed door can now reach the neural scale,
  and a value it keeps is named on the manifest. Existing entries are not
  deleted or reworded.

## Explicitly not changed

- `WHICH` embedder a configuration gets when the operator states nothing. The
  host's `None` stands, so the shipped default managed run keeps measuring on
  hashing and its qualification subject digest does not move. GOAL.md's
  NOT-in-scope line.
- The six host-owned values themselves. Disclosure only; `PARKED.md` P5
  carries the question of whether four of them should become carryable.
- `run_manifest.py` and `qualification.py`. Not one line. The road that would
  have touched them is priced above and rejected on a measurement.
- `config.apply_overrides`, whose rebuild reports all 106 fields as set. It has
  no caller in `src/`, so nothing this fix reads can be fed by it today;
  `PARKED.md` P4 carries it with a ready-to-send prompt.
- The five sealed arm roots and the other 58 committed managed roots. A
  committed root's contents are never edited; `PARKED.md` P6 and VERIFY.md say
  what their readings mean.

## Frozen surfaces

NONE, and this is measured rather than asserted. `INV-frozen-surfaces.md`
names five surfaces across seven paths — `capabilities/state.py`,
`harness.py`, `invariants.py`, `verification/`, `run_manifest.py`,
`qualification.py` — plus the frozen-adjacent `route_fingerprint` in
`llm/firewall.py`. This fix touches `preparation.py` and
`application/stop_report.py` and nothing else in `src/`. It adds no record
kind, alters no event application, changes no manifest schema, model or
validator, and adds no notice code. `tools/blast_radius.py` is run before
implementation and its verdict is pasted into VERIFY.md; if it reports CONTACT
on either frozen file the tranche STOPS there and requests the grant rather
than proceeding.

The one thing that DOES move is a qualification subject digest, and only for a
configuration that names an embedder — because that configuration now compiles
a different scratch policy, which is the configuration taking effect rather
than a code change moving what enters the digest. Conditions 5 and 6 above pin
both halves: the default digest still, the embedder-naming digest moved and
priced.

Estimated diff: ~80 lines of production code across 2 files, plus tests and
three map entries. Under the 150-line budget.

## Approval gate

Class `defect` per GOAL.md, diff estimate <=150 lines, no frozen surface, no
grant required. Proceeds to `dr-implement-fix`.
