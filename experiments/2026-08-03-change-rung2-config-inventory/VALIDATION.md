# Validation for: rung 2, tranche 1 — buried choices become visible switches (inventory)

## Acceptance checks

S1 (R1, R2): `test -f experiments/2026-08-03-change-rung2-config-inventory/INVENTORY.md`
-> exit 0. `grep -q "observe_only" .../INVENTORY.md` -> exit 0 (present,
Group A, row 1 — the named candidate).

Fresh, independent spot-checks against the real files (not reused from
CHECKLIST.md's pasted output):
```
sed -n '212p' src/deepreason/v6_policy.py -> authority="observe_only",
sed -n '115p' src/deepreason/v6_policy.py -> mode="conditioning_only",
sed -n '122p' src/deepreason/v6_policy.py -> mode="harness_plus_model_request",
sed -n '72p'  src/deepreason/v6_policy.py -> mode="disabled",
sed -n '352p' src/deepreason/v6_policy.py -> env.get("DEEPREASON_CONFIG_REFEREE", "")
```
All five match INVENTORY.md's tables exactly : PASS.

**A sixth spot-check found a real inaccuracy, not caught during
execution:**
```
sed -n '22p' src/deepreason/runtime/launch_policy.py
V6_LAUNCH_DISABLE_ENV = "DEEPREASON_DISABLE_V6_LAUNCHES"
```
INVENTORY.md's Group C table (and its prose paragraph immediately below
the table) names this candidate's env var as
`DEEPREASON_DISABLE_V6_LAUNCH_ENV` — a name that does not exist anywhere
in the source. The actual STRING VALUE read from `os.environ` is
`DEEPREASON_DISABLE_V6_LAUNCHES` (plural "LAUNCHES", no "_ENV" suffix);
`DEEPREASON_DISABLE_V6_LAUNCH_ENV` appears to be an accidental splice of
the Python constant's NAME (`V6_LAUNCH_DISABLE_ENV`) with the word
"launch" from the surrounding prose, producing a third string that
matches neither. `grep -rn "DEEPREASON_DISABLE_V6_LAUNCH_ENV"
src/deepreason/` returns nothing — an operator who set that env var
believing it would disable v6 launches would set NOTHING, silently: the
real switch would remain off. This is exactly the kind of pointer
accuracy R2 ("a map/code pointer ... for each candidate") requires and
this row fails it. Independent re-check of the OTHER five Group C rows
(`DEEPREASON_SIMULATION_RUNNER`, `DEEPREASON_RESEARCH_ALLOWLIST`,
`DEEPREASON_RESEARCH_MAX_REQUESTS`/`_MAX_SOURCES`,
`DEEPREASON_CONFIG_REFEREE`, `DEEPREASON_RELEASE_POLICY`) confirms all
five are correct as written.

S1 (Group B finding, independently re-verified via AST rather than grep,
since it is the deliverable's one substantive analytical claim): parsed
`BridgeConfig`'s field defaults directly from `config.py`'s AST —
`mode='legacy_thesis'`, `grounding_review=True`,
`max_schema_repair_attempts` default `2`,
`max_grounding_repair_attempts` default `4`, `output_section_limit`
default `32` — against `engaged_bridge_source()`'s literal returned dict
(`v6_policy.py` lines 179-185, re-pasted above): `mode='grounded_two_stage'`,
`grounding_review=True` (agrees), `max_schema_repair_attempts=1`,
`max_grounding_repair_attempts=0`, `output_section_limit=4`. Matches
INVENTORY.md's Group B table exactly on all five fields : PASS,
confirmed independently.

S2 (R3): `git diff --stat b73db3ba..HEAD -- src/` -> empty output, exit 0
(re-run fresh at validation time, tranche base `b73db3ba` — the merge
commit that brought in the executor-errata ledger, immediately preceding
this tranche's first commit) : PASS.

Also checked, per SPEC.md's A2 (this tranche is an `experiments/`
deliverable, not a `docs/map/` document): `git diff --stat b73db3ba..HEAD
-- docs/map/` -> empty output, exit 0. Confirmed: this tranche changed
exactly four files, all under
`experiments/2026-08-03-change-rung2-config-inventory/`
(`REQUEST.md`, `SPEC.md`, `CHECKLIST.md`, `INVENTORY.md`) — 586 insertions,
0 deletions, nothing outside that directory.

S3 (R4): tranche stops after the inventory; no tranche-2 work (the
`engaged_criticism_policy` switch), no rung 3, opened in this tranche —
confirmed by the diff above (no `src/` or `docs/map/` file touched at
all) and by this being the first validation pass, not a continuation.

## Full gate

Not applicable in the usual sense — zero `src/` files changed, so no
regression is possible and the ~10-minute `pytest tests/ -q -n 4` run
would only reconfirm a result nothing in this tranche could have moved.
Not run, by the same citation logic used at the end of rung 1's tranche
(cite the "no src/ diff" proof rather than re-prove an unmoved number).

## Record-behavior preservation

n/a — no reader, guard, code path, or record format changed.

## Frozen-surface diff

```
git diff --stat b73db3ba..HEAD -- \
  src/deepreason/capabilities/state.py src/deepreason/harness.py \
  src/deepreason/invariants.py src/deepreason/run_manifest.py \
  src/deepreason/qualification.py
```
Empty output. PASS.

## Map

Not applicable — this tranche's deliverable is an `experiments/`
document, not a `docs/map/` one (SPEC.md's A2), and the diff above
confirms zero `docs/map/` files were touched. `docs_verify` was not
re-run because nothing it checks could have changed; a fresh
`python tools/docs_verify.py --fast` confirms this directly:

```
docs_verify [fast]: 49 documents, 793 checks, 793 reused
docs_verify: 0 failed
```

(793 reused of 793 — every check served from cache, since no map file's
mtime changed. This is the honest confirmation that nothing here touched
the map, not a claim that this tranche added map checks — R2's own words
never asked for any.)

New checks added by this change: none — R2 asked for an inventory
document, not a falsifiable map claim (A2). This is not a gap: an
`experiments/` deliverable carries no `Verify:`/`check:` obligation under
`docs/map/SCHEMA.md`'s contract, which governs `docs/map/` only.

## Requirement sweep

R1: demonstrated by S1 (the bounded sweep methodology, executed and
recorded in CHECKLIST.md steps 1-3) — **with one gap**: see Verdict below.

R2: demonstrated by S1 — the inventory document exists with map/code
pointers and current values for each candidate — **with one pointer
found inaccurate this pass** (the `DEEPREASON_DISABLE_V6_LAUNCH_ENV` row).

R3: demonstrated by S2 (empty `src/` diff, re-confirmed fresh).

R4: demonstrated by S3 (no tranche-2 or rung-3 work present in the diff).

R5-R8 (tranche 2, the `engaged_criticism_policy` switch): correctly NOT
addressed by this tranche — `deferred (operator's own words: "TRANCHE 2
— one switch: ...", explicitly split from "TRANCHE 1 — inventory only")`.
Not a gap in this tranche's scope.

## Assumptions carried

A1: the inventory sweep is general ("hard-coded behavior choices"), not
narrowed to authority-shaped values, but practically bounded to
preset/policy-shaped files plus rung 1's five mapped sockets plus
`config.py` as baseline.

A2: inventory format is a plain `experiments/`-tranche Markdown document,
not a `docs/map/SCHEMA.md`-anatomy document.

## Verdict: FAIL

FAIL detail: `INVENTORY.md`'s Group C table names one candidate's
environment variable as `DEEPREASON_DISABLE_V6_LAUNCH_ENV`, which does
not exist anywhere in the source (`grep -rn "DEEPREASON_DISABLE_V6_LAUNCH_ENV"
src/deepreason/` returns nothing). The real string, read at
`runtime/launch_policy.py` line 22 (`V6_LAUNCH_DISABLE_ENV =
"DEEPREASON_DISABLE_V6_LAUNCHES"`) and consumed at line 99
(`os.environ.get(V6_LAUNCH_DISABLE_ENV)`), is
`DEEPREASON_DISABLE_V6_LAUNCHES`. This fails R2's own words — "a map/code
pointer ... for each candidate" — for exactly this one row; every other
pointer in the document (11 other candidates across Groups A-D, all
spot-checked this pass, several independently) is accurate. Suspected
step: CHECKLIST.md step 1, where the six env-var pointers were
transcribed from a single read of both files — five were copied
correctly and this one was misremembered as a hybrid of the Python
constant's name and the surrounding prose rather than the actual string
literal. Route: back to `dr-plan-steps` for a one-line correction to
`INVENTORY.md`, then re-validate.
