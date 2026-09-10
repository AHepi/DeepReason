# Goal: the managed launch path either carries a host-owned configuration value or says on the record that it took it

Class: defect

Observed: `preparation._config_for_profile` replaces SEVEN values of the
operator's loaded configuration with host values whatever that configuration
says (`preparation.py:374-394`), and `preparation.py:505-508` states in prose
that all seven are exempt from the compiler's own
`ENGINE_CONFIG_FIELD_NOT_CARRIED` disclosure channel. The record shows both
halves of the consequence. For the embedder: all five arms of
`experiments/2026-09-04-experiment-brief-variation-step1/roots/{A0,A1,A1P,A2,A3}-run-fe00609058e10605590206d51ab2b7a0`
compiled `scratch_policy.embedder_model = null`,
`scratch_policy.embedder_backend = "deterministic_hashing"` with
`compile_notices` EMPTY, and stamped `Measure inputs
["embedder","hashing-128",...]` at seq 8 — so every distance reading in that
experiment is on the hashing scale and nothing in any of the five records says
a configured value was replaced
(`experiments/2026-09-09-neural-embedder-fallback/DIAGNOSIS.md`, Evidence
rows 1-2). Since 2026-09-09 the same condition also writes an
`embedder-unconfigured` Measure naming the loss
(`src/deepreason/ops.py`), which says WHY the run measured on hashing but not
that a configuration asked for something else. For the other six
(`engine_profile`, `model_profile`, `scratchpad`, `bridge`,
`CHANNELS_DISABLED`, `roles`) nothing in the record distinguishes "the
operator did not set this" from "the operator set this and the host took it"
(`experiments/2026-09-09-neural-embedder-fallback/PARKED.md` P1). This
contradicts a documented guarantee twice: `preparation.py:505-508`'s own
sentence ("every field it sets is either carried into the compiled manifest or
disclosed by the compiler as a typed `ENGINE_CONFIG_FIELD_NOT_CARRIED`
notice"), and the 2026-08-28 ungated-seats law's requirement that switching a
gate produce a typed WARNING and never silence — whose recorded precedent is
audit finding P10, five switches silently reverted by the manifest echo with
zero notices
(`experiments/2026-08-28-defect-manifest-config-disclosure/`).

Map ids resolved for this tranche (map preflight; recorded here so every later
phase starts from the same map):

- `DR-CON-configuration-stages` — where a setting is lost between the
  operator's file and the seat; stages 2 and 3 are the two this tranche works
- `DR-CON-seats` — already names the seven host-owned values (CON-seats.md:116)
- `DR-SUB-manifest` — `compile_run_manifest`, `CompileNoticeV1`,
  `_versioned_source_config_data`, `config_from_run_manifest`. **Frozen,
  surface 4**
- `DR-SUB-llm` — `build_embedder`, `make_embedder`, the `embedder` /
  `embedder-fallback` / `embedder-unconfigured` Measures
- `DR-SUB-application` — `embedder_summary_for_root` and the `results` line
- `DR-INV-frozen-surfaces` — read before designing (below)
- Seams read BEFORE the subsystems, per the map's one ordering rule:
  `DR-SEAM-llm-x-manifest` (the compiled scratch policy is where an embedder
  choice crosses from configuration into a run's identity),
  `DR-SEAM-llm-x-verification` (pins `HashingEmbedder` for `detection-total`;
  this tranche must not disturb it)

Frozen surfaces, stated BEFORE designing: `INV-frozen-surfaces.md` names five
surfaces spanning seven paths — `capabilities/state.py`, `harness.py`,
`invariants.py`, `verification/`, `run_manifest.py`, `qualification.py` — plus
the frozen-adjacent `route_fingerprint`. TWO of them are in this tranche's
line of fire and the tranche STOPS at FIX.md for a grant if either is
contacted:

- **Surface 4, `run_manifest.py`.** Carrying a value may need the compiler to
  admit something it does not admit today. If it does, FIX.md stops with
  `tools/blast_radius.py`'s own contact rows pasted and the roads priced.
- **Surface 5, `qualification.py`.** A compile notice enters the qualification
  subject unless its CODE is stripped, and only
  `ENGINE_CONFIG_FIELD_NOT_CARRIED` is stripped today
  (`INV-frozen-surfaces.md` §5, the 2026-08-28 grant). A new notice code that
  is not stripped MOVES the subject digest of every managed run that emits it
  and costs each home a ~14-minute battery. Whether the fix reuses the
  stripped code or asks for a second one is a FIX.md decision with a grant
  request, not an implementation detail.

Success criterion (machine-decidable):

    (1) python -u experiments/2026-09-10-defect-managed-path-host-owned-overrides/repro_managed_override.py
        exit 0 after the fix, exit 1 before it. Offline, deterministic stub,
        no provider call. A managed run prepared through the same call
        `deepreason reason` uses, from an operator configuration that names
        EMBEDDER_MODEL, reaches a terminal whose `log.jsonl` carries a Measure
        `["embedder", "<neural fingerprint>", ...]` and no
        `embedder-unconfigured`, and whose `deepreason results` embedder line
        names the neural model rather than `hashing (hashing-128)`.

    (2) python -m pytest tests/test_managed_path_host_owned_values.py -q
        0 failed. SEVEN parametrised cases, one per host-owned value
        (`engine_profile`, `model_profile`, `scratchpad`, `bridge`,
        `EMBEDDER_MODEL`, `CHANNELS_DISABLED`, `roles`): for each, a manifest
        compiled from an operator configuration that sets that value
        DIFFERENTLY from the host either carries the operator's value or
        carries exactly one typed notice naming that field. No case may be
        silent. Every case mutation-proven: it fails when its own fix line is
        reverted.

    (3) python -m pytest tests/test_reusable_qualification.py -q
        0 failed, INCLUDING a new pin that the DEFAULT managed subject digest
        is byte-identical to its committed value
        (`02ee7e098bb9239011708a4aa0bce4b7479619b3aff28eff46188125a869e713`
        for the committed fixture profile). The digest may move only where a
        FIX.md grant says it may, and the test states which cases those are.

    (4) python -m pytest tests/ -q -n 4
        0 failed, once, at the boundary.

In scope (max 3): `src/deepreason/preparation.py` (the `owned` dictionary and
its disclosure), `src/deepreason/run_manifest.py` (ONLY if a grant is
requested and given), `src/deepreason/application/results.py` (only if the
carried embedder must be rendered differently).

NOT in scope, the nearest tempting neighbour: WHICH embedder the shipped
default names, and the `EMBEDDER_MODEL` default in `config.py`. This tranche
makes the operator's stated value reach the run or be recorded as refused; it
does not change what a run gets when the operator states nothing. Also not in
scope: the five sealed arm roots (a committed root's contents are never
edited — `PARKED.md` P2 of the 2026-09-09 tranche), the `pyproject.toml`
declaration gap (parked 2026-08-30 S5), and any re-reading of the sealed
step-1 distance numbers beyond the statement VERIFY.md owes them.

Budget: <=150 changed lines, 1 commit, ~5 hours.

Stop conditions inherited from orchestrator: yes
