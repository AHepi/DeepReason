# Validation for: rung 2, tranche 2 — the engaged_criticism_policy Config switch

## Validation history (honest — the first pass is not deleted)

**Pass 1** (commit `03b2d2fe`, branch head `e01d4738` at the time):
verdict **FAIL**, solely on the frozen-surface mechanical tripwire
(4a2) — `src/deepreason/run_manifest.py` was touched (Amendment 2's
fix) with no operator quote in REQUEST.md approving that specific
surface. Every other check in that pass — all S1-S8 acceptance checks,
the full gate, the root sweep, all five `docs_verify` modes, and the
requirement sweep — already read PASS. That pass also named one
secondary, lower-stakes finding: a missing `Traps` entry in
`docs/map/INV-frozen-surfaces.md` for the Config-field-addition failure
mode this tranche discovered.

**Between passes:** the monitoring session put the exact question to
the operator directly and recorded the verbatim answer as REQUEST.md
Amendment 3 (commit `87b2828d`) — resolving the tripwire. Separately,
this tranche's own CHECKLIST.md gained steps 13-14 (commits `51ceaa58`,
`74a27bb5`), adding the Traps entry Pass 1 named as outstanding.

**Pass 2** (this document, re-verified fresh below, branch head
`74a27bb5` at the start of this pass): both gaps are closed. Verdict
**PASS**.

## Acceptance checks (re-run fresh, Pass 2)

S1: `grep -q 'ENGAGED_CRITICISM_AUTHORITY: Literal\["observe_only", "defended_trial"\] = "observe_only"' src/deepreason/config.py && python -c "from deepreason.config import Config; assert Config().ENGAGED_CRITICISM_AUTHORITY == 'observe_only'"`
-> `grep: PASS` / `assert: PASS` : PASS

S2: `python -c "from deepreason.v6_policy import engaged_criticism_policy as f; assert f('e').authority == 'observe_only'; assert f('e', authority='defended_trial').authority == 'defended_trial'"`
-> exits 0 : PASS

S3: `python -c "import inspect; from deepreason import preparation as p; src = inspect.getsource(p.build_preparation_manifest); assert 'config.ENGAGED_CRITICISM_AUTHORITY' in src"`
-> exits 0 : PASS

S4: `python -m pytest tests/test_v6_policy_preset.py -q`
-> `14 passed in 0.10s` : PASS

S5: `grep -q "ENGAGED_CRITICISM_AUTHORITY" docs/map/CON-authority.md`
-> `grep: PASS` : PASS

S6: full gate + root sweep — see below.

S7 (Amendment 1): `SEAM-manifest-x-schools.md`'s corrected call-site
check re-verified as part of the full `docs_verify.py` run below : PASS

S8 (Amendment 2, revised — unconditional pop): `python -m pytest tests/test_run_manifest_v4.py tests/test_run_manifest_v5_inquiry.py tests/test_incident_wave_a_v2_fixtures.py -q`
-> `37 passed in 1.23s` : PASS

## Full gate

Run ISOLATED this pass (nothing else concurrent, learning from Pass
1's resource-contention false-failure):

    3291 passed, 7 skipped in 581.22s (0:09:41)

**Verdict: PASS.**

## Record-behavior preservation / root sweep

`python tools/root_sweep.py` run fresh this pass: `SWEEP COMPLETE: 42
roots`, `11 ERROR` lines (all `UnsupportedRunManifestVersionError`).
Diffed against Pass 1's own capture (`root_sweep_after.txt`): **empty
diff** — byte-identical. This is now the THIRD independent byte-
identical sweep for this tranche (Pass 1's own two runs, plus the
monitoring session's X8 entry — independent worktrees at base
`e0d4eacb` / head `50e4eb89`, "identical sha256... diff empty, 42
rows, 11 ERROR"). No committed root's verdict has moved at any point.

**Verdict: PASS.**

## Frozen-surface diff

    git diff --stat 23df6e20..HEAD -- \
      src/deepreason/capabilities/state.py src/deepreason/harness.py \
      src/deepreason/invariants.py src/deepreason/run_manifest.py \
      src/deepreason/qualification.py

    src/deepreason/run_manifest.py | 7 +++++++
    1 file changed, 7 insertions(+)

**Non-empty, as in Pass 1** — this is `DR-INV-frozen-surfaces` surface
4. Pass 1's blocking finding was that REQUEST.md contained no operator
quote approving this. That gap is now closed:

> Operator authorization for rung 2, TRANCHE 3 (after the
> engaged_criticism_policy switch tranche is delivered...)
>
> [monitoring session's question, verbatim, per REQUEST.md Amendment 3]
> "Approve the 7-line fix in run_manifest.py so tranche 2 can finish?"
>
> [operator's verbatim answer, per REQUEST.md Amendment 3]
> "Approve it"

REQUEST.md Amendment 3 (commit `87b2828d`) records this exchange in
full, including the consequences of both options as stated to the
operator before they answered (approve = fix stays, proven safe by the
full gate and independent sweeps; reject = re-plan avoiding the frozen
file). This is exactly the operator sign-off the rule requires — not
the monitor's own technical endorsement (X8), which was evidence
supporting the question, not a substitute for asking it.

**Verdict: PASS** (non-empty diff, operator-approved per Amendment 3).

## Map

`python tools/docs_verify.py`: 49 documents, **795** checks (up from
794 in Pass 1 — the new Traps-entry claim), 0 failed : PASS
`python tools/docs_verify.py --audit`: 0 finding(s) : PASS
`python tools/docs_verify.py --links`: 0 dangling reference(s), 49
documents : PASS
`python tools/docs_verify.py --coverage`: 6 seams swept, 14 without a
`Sweep:` header, 0 findings — same pre-existing 14 as Pass 1, none
touched by this tranche : PASS, nothing to dismiss

`python tools/docs_verify.py --stale`: 11 documents (same list as Pass
1, plus `REC-change-a-seam.md` now also citing this tranche's step-13
commit `51ceaa58` since it touched a file `REC-change-a-seam.md` owns —
re-verified clean, no content update needed, same disposition as its
Pass-1 listing). Every entry dismissed with a reason, carried forward
from Pass 1 with one update:
- `CON-authority.md`, `CON-schools.md`, `SEAM-bridge-x-manifest.md`,
  `SEAM-llm-x-manifest.md`, `SEAM-manifest-x-schools.md`,
  `SUB-manifest.md`, `CON-run-identity.md`, `REC-change-a-seam.md` —
  flagged because this tranche's commits touched files they own;
  re-verified clean by the full run above; no content update needed
  beyond what already landed.
- `INV-frozen-surfaces.md` — flagged in Pass 1 as **not dismissed**
  (the missing Traps entry). **Now dismissed**: CHECKLIST.md steps
  13-14 added the entry (commit `51ceaa58`), with its own new checked
  claim (`grep -q "ENGAGED_CRITICISM_AUTHORITY" src/deepreason/run_manifest.py`),
  confirmed passing in the full run above.
- `SEAM-harness-x-verification.md`, `SUB-verification.md` — flagged
  because of `2456da55`, a commit from before this tranche, unrelated
  to it. Not this tranche's responsibility, same as Pass 1.

New map checks added by this change: `CON-authority.md`'s
default-preservation claim (S4/S5), `SEAM-manifest-x-schools.md`'s
repaired call-site check (S7), and `INV-frozen-surfaces.md`'s new Traps
claim (step 13) pinning `ENGAGED_CRITICISM_AUTHORITY`'s presence in
`run_manifest.py`'s pop-list.

## Requirement sweep

R1 (behavior — preserves observe_only default): demonstrated by
S1/S2/S4 — `Config().ENGAGED_CRITICISM_AUTHORITY == 'observe_only'`,
and `test_engaged_criticism_authority_config_default_preserves_prior_behavior`
proves full pydantic equality between the parameterized and no-kwarg
calls.

R2 (creating the switch is in scope): demonstrated by S1-S3 landing.

R3 (flipping any default forbidden): demonstrated — default is
`"observe_only"` everywhere; both existing call sites
(`v6_policy.py:463`, `preparation.py:371`) still resolve to
`observe_only` with no explicit override, re-confirmed this pass.

R4 (full gate 0 failed): demonstrated above — PASS, isolated run.

R5 (root sweep byte-identical): demonstrated above — PASS, now a
three-way independent confirmation (this pass, Pass 1, the monitor's
X8).

R6 (test proving default equals prior behavior): demonstrated by S4.

R7 (map updated in the SAME commit as the code): demonstrated for the
main tranche (commit `9607f739`: code + `CON-authority.md` +
`SEAM-manifest-x-schools.md` together). The Amendment-2-revision
follow-up (`f642f980`) needed no map-document content change at the
time (no `Owns:`/checked-claim quoted the internals of the fix). The
ONE thing that should have moved alongside the discovery — the Traps
entry — is now in place (step 13, commit `51ceaa58`), closing what Pass
1 correctly flagged as a partial miss on R7's spirit.

R8 (do the switch tranche first): demonstrated — this tranche is
complete; bridge-unification "TRANCHE 3" untouched (confirmed:
`git diff --stat 23df6e20..HEAD -- src/deepreason/v6_policy.py` shows
only the `engaged_criticism_policy` change, no `engaged_bridge_source`
lines).

## Assumptions carried

A1: field name `ENGAGED_CRITICISM_AUTHORITY`.
A2: new test lands in `tests/test_v6_policy_preset.py`, one new
function.
A3: value-space is `Literal["observe_only", "defended_trial"]`, no
translation layer.
A4: `qualification.py`/`engaged_policy_digest()` need no code change —
holds; `qualification.py` has zero lines changed across the whole
tranche.

## Verdict: PASS

Every acceptance check (S1-S8), the full gate (3291 passed, 0 failed,
isolated), the root sweep (42 rows / 11 ERROR, byte-identical across
three independent captures), all five `docs_verify` modes, and all
eight requirements (R1-R8) pass. The frozen-surface diff is non-empty
but now carries the operator's own verbatim approval (REQUEST.md
Amendment 3). The one map-completeness gap Pass 1 named (the missing
Traps entry) is closed. Ready for `dr-deliver-change`.
