# Delivered: rung 2, tranche 2 — the engaged_criticism_policy Config switch
Branch: `claude/delivery-rungs-handover-m22sdy` @ `6ae1f382` (pushed, tree
clean).

## What changed

`engaged_criticism_policy`'s hard-coded `authority="observe_only"` in
`src/deepreason/v6_policy.py` is now a `Config`-driven switch:
`Config.ENGAGED_CRITICISM_AUTHORITY` (a `Literal["observe_only",
"defended_trial"]`, default `"observe_only"`) threads through
`src/deepreason/preparation.py::build_preparation_manifest` into the
compiled preset. Every existing caller keeps byte-identical behavior —
both call sites (`v6_policy.py`'s own digest template,
`preparation.py`'s manifest-build path) pass no override and get
`observe_only`, proven by a new test
(`test_engaged_criticism_authority_config_default_preserves_prior_behavior`,
`tests/test_v6_policy_preset.py`). `docs/map/CON-authority.md` was
extended in the same commit as the code (`9607f739`): a sixth per-run
authority knob, a new checked claim, `Owns:` grown to cover both touched
files.

Two things surfaced mid-flight that the original spec did not
anticipate, both resolved and both landing in the commit history rather
than being smoothed over: (1) a third map document
(`docs/map/SEAM-manifest-x-schools.md`) had a check that literal-greped
`preparation.py`'s exact old call-site text; fixed to check the same
property (the wiring survives) against the new call shape. (2) Adding
the `Config` field broke pinned canonical-hash goldens in THREE places
across two rounds — schema v1/v2/v3 first (fixed by scrubbing the new
key from `run_manifest.py`'s `_versioned_source_config_data` for
`schema_version < 4`, commit `9607f739`), then the full gate refuted
that scope by finding two more goldens at schema v5
(`test_v5_canonical_bytes_match_incident_head_golden`,
`test_incident_descriptors_and_generated_roots_are_frozen_and_deterministic`)
still failing — the "no test above v3" assumption was a false inference
from an incomplete grep. Fixed by widening the scrub to UNCONDITIONAL,
every schema version (commit `f642f980`): the field's actual effect now
flows solely through the compiled manifest's own first-class
`criticism_policy.authority`, never through the raw `Config` echo.

This second fix touches `DR-INV-frozen-surfaces` surface 4
(`run_manifest.py`). Validation's first pass (`03b2d2fe`) correctly
FAILED on exactly this: the touch was technically sound and verified
three ways (this session twice in isolation, plus the monitoring
session's own independent before/after worktree sweep, `ERRATA_
EXECUTOR.md` X8) but landed with no operator quote in REQUEST.md
approving it — a real process gap, not a code defect. The monitoring
session put the question to the operator directly; the answer ("Approve
it") is recorded verbatim as REQUEST.md Amendment 3. Separately, Pass 1
named one more outstanding item — a `Traps` entry in `docs/map/INV-
frozen-surfaces.md` recording the newly-discovered failure mode (ANY new
`Config` field can silently break goldens across multiple, non-obvious
schema versions) — added via CHECKLIST steps 13-14 (commit `51ceaa58`).
A second, from-scratch validation pass (`6ae1f382`) then returned PASS
on every check: full gate (3291 passed, 0 failed, isolated), root sweep
(42 rows / 11 ERROR, byte-identical across three independent captures),
all five `docs_verify` modes, and all eight requirements.

One further, self-reported process note: this session's own executor
copy skipped re-running session preflight (`dr-drive-harness` §1) at
this continuation's actual start, which meant a directly-relevant
precedent — the immediately-prior tranche's `RESULTS.md` stating a
frozen-surface fix needs "operator approval" sought BEFORE landing, not
after — was missed until validation's own mechanical tripwire caught the
gap downstream. Logged as `docs/ERRATA_EXECUTOR.md` XE1 (commit
`de2b5826`), written before that ledger's charter changed
(commit `87b2828d`) to single-writer/monitor-only. No further executor
entries will be added there; XE1 stands as committed history.

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "engaged_criticism_policy... becomes a Config value PRESERVING observe_only as the default" | done | commits `9607f739`, `f642f980`; VALIDATION.md Pass 2, S1/S2/S4 |
| R2 | "Creating the switch is in scope" | done | S1-S3 landed, commit `9607f739` |
| R3 | "FLIPPING ANY DEFAULT IS THE OPERATOR'S DECISION, NEVER YOURS" | done | default is `observe_only` everywhere, both call sites unchanged behaviorally; VALIDATION.md Pass 2 R3 |
| R4 | "full gate ... 0 failed (never bare pytest)" | done | `python -m pytest tests/ -q -n 4` -> 3291 passed, 0 failed, isolated; VALIDATION.md Pass 2 |
| R5 | "root sweep ... byte-identical before/after (42 rows, 11 ERROR expected)" | done | 42 rows, 11 ERROR, byte-identical across three independent captures (this session x2, monitor's X8); VALIDATION.md Pass 2 |
| R6 | "a test proving the switch's default equals prior behavior" | done | `test_engaged_criticism_authority_config_default_preserves_prior_behavior`, `tests/test_v6_policy_preset.py` |
| R7 | "map updated in the SAME commit as the code" | done-with-note | main switch: same commit (`9607f739`). The Amendment-2-revision follow-up (`f642f980`) needed no map CONTENT change at landing time (nothing quoted the fix's internals); the Traps entry that should have accompanied the discovery landed two phases later (CHECKLIST steps 13-14, `51ceaa58`) rather than in the same commit — a partial miss on R7's spirit, closed before delivery, not before commit |
| R8 | "Do the switch tranche first" | done | this tranche opened and completed before any bridge-unification ("TRANCHE 3") work; confirmed zero `engaged_bridge_source` lines touched |

## Assumptions the operator may override

A1: field name `ENGAGED_CRITICISM_AUTHORITY` (matches the existing
`<WHAT>_AUTHORITY` convention).
A2: the new test lands in `tests/test_v6_policy_preset.py`, one new
function, not a new file.
A3: the field's value-space is `Literal["observe_only",
"defended_trial"]`, mirroring `CriticismPolicyV1.authority` directly —
no translation layer.
A4: `qualification.py`/`engaged_policy_digest()` need no code change —
the qualification subject already picks up an authority change through
the compiled manifest's own field dump; confirmed zero lines changed in
`qualification.py` across the whole tranche.

## Map delta

Changed: `docs/map/CON-authority.md` (new field entry, `Owns:` grown to
include `v6_policy.py`/`preparation.py`, one new checked claim),
`docs/map/SEAM-manifest-x-schools.md` (one check repaired to match the
new call-site shape), `docs/map/INV-frozen-surfaces.md` (one new Traps
entry with a new checked claim). Created: none. New checks: 2 (`CON-
authority.md`'s default-preservation claim; `INV-frozen-surfaces.md`'s
Traps claim). Repaired (not new): `SEAM-manifest-x-schools.md`'s
call-site check.

Left stale (advisory `--stale`, all dismissed in VALIDATION.md Pass 2
with reasons — none need further action from this tranche):
`CON-run-identity.md`, `CON-schools.md`, `REC-change-a-seam.md`,
`SEAM-bridge-x-manifest.md`, `SEAM-llm-x-manifest.md`, `SUB-manifest.md`
(flagged only because this tranche's commits touched files they own;
re-verified clean, no content update needed); `SEAM-harness-x-
verification.md`, `SUB-verification.md` (flagged for an unrelated,
pre-existing commit, not this tranche's responsibility).

## Parked (not done, not promised)

See `PARKED.md`. Summary: an overstated sentence in `INV-frozen-
surfaces.md` ("A Config value... is invisible to replay") that this
tranche's own discovery partially contradicts, noted for a future
`docs/ERRATA.md` correction rather than edited here (out of step 13's
stated scope); rung 2's remaining inventory candidates (bridge settings,
env-var switches, `STANCE_LIBRARY`) — the operator's call, unchanged
from the inventory tranche; a possible future hardening (a structural
test catching ANY untracked new top-level `Config` field, not just the
one this tranche happened to add) — not designed or requested here.

Rung 2's bridge-settings unification ("TRANCHE 3") remains a separate,
not-yet-opened tranche, per the operator's own instruction that it comes
after this one and never in the same tranche.
