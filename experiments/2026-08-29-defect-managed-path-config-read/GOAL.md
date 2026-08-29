# Goal: `deepreason reason` must compile its manifest from the operator's own Config, not from one synthesised out of the provider profile

Class: defect

Observed: on the managed path the operator's config file is never read.
`_cmd_reason` (`src/deepreason/cli/main.py:2395`) builds a
`RunPreparationRequestV1` (`preparation.py:108-130`) that has NO field for a
config path, and never touches `args.config`; `RunPreparationService.prepare`
calls `build_preparation_manifest` (`preparation.py:421`), which calls
`_config_for_profile` (`preparation.py:308-354`) and CONSTRUCTS a fresh
`Config` from the provider profile with every field at its default except
`engine_profile`, `model_profile`, `scratchpad`, `bridge`, `EMBEDDER_MODEL`,
`CHANNELS_DISABLED` and `roles`. Evidence, committed:
`experiments/2026-08-28-defect-manifest-config-disclosure/REPRO.md` "A separate
finding this reproduction surfaced", `.../PARKED.md` P14, `.../DELIVERY.md`
residue item 2.

Consequence, stated exactly: a `run-config.yaml` naming `JUDGE_SEATS_ENABLED:
true` has no effect of any kind on `deepreason reason` — it is not carried, not
dropped-with-a-notice, not read. The 2026-08-28 disclosure
(`ENGINE_CONFIG_FIELD_NOT_CARRIED`) cannot fire on this path, because the
`Config` handed to `compile_run_manifest` never differs from its defaults in
any dropped field.

Authority: CLAUDE.md, operator 2026-08-28, verbatim — "configuration of seats
need to be able to turn gates on and off at will ... Gates are always optional:
with warnings." A gate that no configuration file can even be READ to request
is neither optional nor on, and is not warned about either.

Success criterion (machine-decidable):

    python -m pytest tests/test_managed_path_config_read.py -q
    -> passed, 0 failed

    where, for every `Config` field an operator config file sets away from its
    default, the manifest the managed path prepares satisfies
        carried:   config_from_run_manifest(manifest).<FIELD> == configured
        OR disclosed: an ENGINE_CONFIG_FIELD_NOT_CARRIED notice at
                      /engine_config/<FIELD> naming the configured value
    and the disjunction holds field by field, not in aggregate.

    Plus, unchanged:
    python -m pytest tests/ -q -n 4          -> 0 failed
    python tools/docs_verify.py              -> 4 failed (stated baseline) + at
                                                most the P16 tripwire, and no
                                                other new failure

Failure criterion (any one trips the tranche): a committed manifest's canonical
bytes or `sha256` moves; a qualification subject digest moves for a
DEFAULT-valued config; a committed digest pin is re-pinned; or the fix requires
contact with any frozen surface other than 4.

PRICED STOP, declared before design (brief requirement): the qualification
subject is built from the manifest (`qualification.py:248-289`), so admitting
operator `Config` values into preparation moves the subject digest for every
non-default config that reaches the echo. That cost is measured in `PRICE.md`
BEFORE any fix is designed. If it moves, the lane STOPS and the operator
decides the spend (~14 min, ~1160 provider calls per home).

In scope:
  - `src/deepreason/preparation.py` (`_config_for_profile`,
    `build_preparation_manifest`, `RunPreparationRequestV1`, `prepare`)
  - `src/deepreason/cli/main.py` — the `reason` -> preparation wiring only
  - `src/deepreason/config.py` — only if carriage requires a declared field

NOT in scope (the nearest tempting thing): carrying the 22 BEHAVIOURAL dropped
fields through the engine-config echo into the running cycle. That is P15, the
second limb of the same operator law, and it is tranche B2's question. This
tranche decides only whether the operator's file is READ at all; what a read
field then does is the next question, not this one.

Also NOT in scope: `run_manifest.py`'s drop list (`_versioned_source_config_data`).
No `data.pop` line is added, removed or made conditional here.

Budget: <=150 changed lines, 1 commit per phase boundary.

Stop conditions inherited from orchestrator: yes.

## MAP PREFLIGHT — resolved ids (CLAUDE.md requirement)

Read in this order: `docs/map/INDEX.md`, `docs/map/INV-frozen-surfaces.md`
(before any design), then the covering concept documents. There is no SEAM
document for the pair this defect lives on — see the finding below.

| id | document | why it covers this work |
|---|---|---|
| `DR-INV-frozen-surfaces` | `INV-frozen-surfaces.md` | surface 4 `run_manifest.py`, surface 5 `qualification.py`; read in full before designing |
| `DR-CON-authority` | `CON-authority.md` | the ONLY document owning `config.py`, `preparation.py` and `run_manifest.py` together — the covering document for this defect; its Traps entry "Both master gates are invisible to the run that executes them" is the recorded predecessor |
| `DR-CON-run-identity` | `CON-run-identity.md` | owns `preparation.py`; the managed run id is a digest over the preparation REQUEST, so any new request field changes run identity |
| `DR-CON-seats` | `CON-seats.md` | owns `preparation.py`; `_config_for_profile` is where a role becomes a route |
| `DR-SUB-manifest` | `SUB-manifest.md` | RunManifest schema, validators, qualification subject — FROZEN surface 4/5 |
| `DR-SUB-application` | `SUB-application.md` | owns the `cli/main.py` dispatch rows for `reason` |

### Map findings recorded at preflight (not fixed here — outside this goal)

1. **No SEAM document joins the sides this defect lives on.** The agreement
   broken here is "a compiled manifest is the only carrier of a run's Config",
   which spans `DR-SUB-manifest` and `DR-SUB-application`/`DR-CON-run-identity`.
   `INDEX.md`'s seam matrix lists `manifest x workflow` as "not yet written"
   and has no `manifest x application` row at all. Already recorded as residue
   item 4 of `experiments/2026-08-28-defect-manifest-config-disclosure/DELIVERY.md`;
   restated here because this tranche is the second defect on that same
   unwritten agreement.
2. **Eight map documents exist but `INDEX.md` routes to none of them**:
   `SUB-application.md`, `SUB-amendment.md`, `SUB-periphery.md`,
   `CON-problem-layer-lifecycle.md`, `INV-signal-contract.md`,
   `REC-add-signal.md`, `REC-revise-allocation-policy.md`,
   `SEAM-schools-x-scheduler.md`. `INDEX.md` is the declared entry point, so a
   document it does not route to is a document the next reader will not find.
   Re-derivable:
   `for d in SUB-application SUB-amendment SUB-periphery CON-problem-layer-lifecycle INV-signal-contract REC-add-signal REC-revise-allocation-policy SEAM-schools-x-scheduler; do grep -q "$d" docs/map/INDEX.md || echo "UNROUTED: $d"; done`
   NOT fixed here: `INDEX.md` is outside this lane's file cone and is being
   edited by other windows. Parked, with a ready-to-send prompt, in `PARKED.md`.

### Line references confirmed against THIS tree (the brief's may have moved)

| brief said | this tree | verdict |
|---|---|---|
| `preparation.py:308-352` `_config_for_profile` | `preparation.py:308-354` | same function, 2 lines longer |
| `preparation.py:499-511` criticism_policy wiring | `preparation.py:493-512` (the `compile_run_manifest(...)` call; `criticism_policy=` at 500-512) | same wiring, shifted |
| `cli/main.py:2395` `_cmd_reason` | `cli/main.py:2395` | exact |
| `RunPreparationService().prepare` call | `cli/main.py:2456` | exact |
