# Validation for: rung 2, tranche 1 — buried choices become visible switches (inventory)
(Second, fresh pass — the first VALIDATION.md, commit `5489d501`,
returned FAIL on one gap: `INVENTORY.md`'s
`DEEPREASON_DISABLE_V6_LAUNCH_ENV` pointer. That gap is fixed, commits
`835248fb`/`4e4c26e8`. This document supersedes the first entirely —
every check re-run from scratch, including every pointer this time, not
only the ones the first pass happened to check.)

## Acceptance checks

S1 (R1, R2): `test -f .../INVENTORY.md` -> exit 0. `grep -q "observe_only"
.../INVENTORY.md` -> exit 0.

**The specific FAIL condition from the first pass, re-checked directly:**
```
grep -n "DEEPREASON_DISABLE_V6_LAUNCH" .../INVENTORY.md
67: ... | `DEEPREASON_DISABLE_V6_LAUNCHES` | unset (launches enabled) |
71: launch-policy pair (`DEEPREASON_DISABLE_V6_LAUNCHES`, ...
```
Correct string present twice; the wrong string (`..._ENV` suffix) is
absent. Fixed.

**All twelve candidate pointers re-verified fresh this pass** (the first
pass checked five and missed the sixth env-var row before finding it via
a further ad-hoc check; this pass checks every one, not a sample):

Group A (5):
```
sed -n '212p' v6_policy.py -> authority="observe_only",
sed -n '115p' v6_policy.py -> mode="conditioning_only",
sed -n '122p' v6_policy.py -> mode="harness_plus_model_request",
sed -n '180p' v6_policy.py -> "mode": "grounded_two_stage",
sed -n '181p' v6_policy.py -> "grounding_review": True,
```
Group B (BridgeConfig, 5 fields) — re-parsed via AST from `config.py`
directly (mode default `'legacy_thesis'`, `grounding_review` default
`True`, `max_schema_repair_attempts` default `2`,
`max_grounding_repair_attempts` default `4`, `output_section_limit`
default `32`) against `engaged_bridge_source()`'s literal dict — matches
INVENTORY.md's table on all five fields.
Group C (6):
```
sed -n '230p' v6_policy.py -> DEEPREASON_SIMULATION_RUNNER
sed -n '321p' v6_policy.py -> DEEPREASON_RESEARCH_ALLOWLIST
sed -n '334,335p' v6_policy.py -> DEEPREASON_RESEARCH_MAX_REQUESTS / _MAX_SOURCES (lines match INVENTORY.md exactly)
sed -n '352p' v6_policy.py -> DEEPREASON_CONFIG_REFEREE
sed -n '22p,99p' launch_policy.py -> V6_LAUNCH_DISABLE_ENV = "DEEPREASON_DISABLE_V6_LAUNCHES"; os.environ.get(V6_LAUNCH_DISABLE_ENV) at line 99 (matches INVENTORY.md's cited line)
sed -n '23p,110p' launch_policy.py -> RELEASE_POLICY_ENV = "DEEPREASON_RELEASE_POLICY"; os.environ.get(RELEASE_POLICY_ENV) at line 110 (matches INVENTORY.md's cited line)
```
Group D (1): `grep -n "STANCE_LIBRARY" capture/schools.py` -> line 18,
`STANCE_LIBRARY = {`. Matches.

All twelve : PASS, no further inaccuracies found.

S2 (R3): `git diff --stat b73db3ba..HEAD -- src/` -> empty, exit 0 : PASS.

Also re-confirmed per A2: `git diff --stat b73db3ba..HEAD -- docs/map/`
-> empty, exit 0.

S3 (R4): confirmed — the full tranche diff (below) shows only
`experiments/2026-08-03-change-rung2-config-inventory/*` and
`docs/ERRATA_EXECUTOR.md`; no tranche-2 or rung-3 work.

## Full gate

Not re-run: `git diff --stat b73db3ba..HEAD -- src/` is empty (proof
above) — no `src/` file has moved since the last time it was run for
this session (rung 1's tranche), so nothing here could have changed that
result. Cited rather than re-proven, same reasoning as the first pass.

## Record-behavior preservation

n/a — no reader, guard, or record format changed.

## Frozen-surface diff

```
git diff --stat b73db3ba..HEAD -- \
  src/deepreason/capabilities/state.py src/deepreason/harness.py \
  src/deepreason/invariants.py src/deepreason/run_manifest.py \
  src/deepreason/qualification.py
```
Empty output. PASS.

## Map

Not applicable — zero `docs/map/` changes (re-confirmed above), per
SPEC.md's A2 (this tranche's deliverable is an `experiments/` document).
`docs_verify` not re-run a third time this session for the same reason:
nothing it checks moved.

New checks added by this change: none (A2 — not a `docs/map/` document,
carries no `check:` obligation).

**One file OUTSIDE the tranche directory was touched, by design, not
scope creep:** `docs/ERRATA_EXECUTOR.md` gained entry X5, logging that
this tranche's own validation FAIL→re-plan→fix loop fired correctly
(commit `4e4c26e8`). This is C3's standing constraint from the operator's
opening message ("append an entry ... whenever ... a guardrail fires as
designed"), binding on the whole session, not only this tranche's
R1-R4 — recorded here so its presence in the diff is never mistaken for
an unexplained change.

## Requirement sweep

R1: demonstrated by S1 (bounded sweep, CHECKLIST steps 1-3).

R2: demonstrated by S1 — **and this pass confirms the gap the first
validation caught is closed, with every pointer (not only a sample)
re-verified accurate.**

R3: demonstrated by S2 (empty `src/` diff, re-confirmed fresh).

R4: demonstrated by S3 (no tranche-2/rung-3 work present).

R5-R8 (tranche 2): correctly deferred, not this tranche's scope.

## Assumptions carried

A1: general-but-bounded sweep methodology (preset/policy files + rung 1's
five sockets + `config.py` baseline).
A2: `experiments/`-tranche Markdown format, not `docs/map/SCHEMA.md`
anatomy.

## Verdict: PASS

Every acceptance check (S1-S3), both process constraints (R3, R4), all
four requirements this tranche addresses (R1-R4), the frozen-surface
diff, and the zero-`src/`/zero-`docs/map/` scope boundary are green on a
fresh, independent re-run that checked ALL twelve candidate pointers this
time (not a sample) specifically to guard against repeating the class of
miss the first pass caught. Route: `dr-deliver-change`.
