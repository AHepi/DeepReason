# Parked by the stop-report tranche

Nothing here was fixed. REQUEST.md C3 parks these by name, and CLAUDE.md's
cross-routing rule is absolute: a defect found mid-change is PARKED, not
fixed. Each entry is one line of WHAT, then a ready-to-send prompt — the
follow-up should cost the operator a paste, not an authoring session.

---

## P1 — the six engine-config fields the manifest does not carry

**What.** Six settings compile into `ENGINE_CONFIG_FIELD_NOT_CARRIED`
notices instead of into the manifest, and are restored at run time from
those notices. They do take effect, but the manifest alone does not show
them, so any reader inspecting the manifest reports them unset. This is
the STRUCTURAL cause underneath the whole tranche: the stop report now
MARKS these fields rather than being misled by them, which is a
mitigation, not a fix. Touching the manifest schema is frozen surface 4,
so it is priced and parked rather than attempted here.

```
EXECUTOR WINDOW — CHANGE TRANCHE: carry the six engine-config fields in
the compiled manifest (FROZEN SURFACE 4 — grant required before code)

Read CLAUDE.md fully, then load dr-change-orchestrator, dr-drive-harness,
dr-ask-the-right-question and dr-explain-to-operator. Start at
dr-capture-request. Base on main at or after the stop-report tranche
(branch claude/executor-stop-report-paiagc). Work on your window's
assigned branch; commit and push at every phase boundary.

THE DEFECT, from the record. Six engine-config fields are not carried by
the compiled manifest. They compile into ENGINE_CONFIG_FIELD_NOT_CARRIED
notices and are restored at run time from those notices. Measured on the
P-A1 root (origin/claude/live-reasoning-p-a1-bv65kl,
experiments/2026-09-01-live-all-modules-p-a1/run/run-manifest.json):

  ADJUDICATION_STATUS_AUTHORITY_ENABLED = true    resolution null
  ENGAGED_CRITICISM_AUTHORITY = "defended_trial"  -> /criticism_policy/authority
  JUDGE_SEATS_ENABLED = true                      resolution null
  JUDGE_SUMMONS_PER_CYCLE = 2                     resolution null
  LEGACY_CRITICISM_ENABLED = false                -> /criticism_policy
  SCHOOL_SEATS_ENABLED = true  -> /control_plane_policy/school_execution

WHY IT MATTERS BEYOND TIDINESS. The 2026-08-28 operator law requires
every gate to be switchable per run and every switch-off to emit a typed
WARNING, never silence. Audit finding P10 (2026-08-28) recorded five
switches silently reverted by the manifest echo with zero notices. A
field the manifest does not carry cannot be echoed back, so the
disclosure the law demands has nowhere to live.

FROZEN SURFACE. This is surface 4 (manifest schemas + validators),
INV-frozen-surfaces.md. DESIGN AND STOP: write SPEC.md with
tools/blast_radius.py's own frozen_surface_contacts list pasted verbatim
and request the grant THERE, before any code, per the documented recipe
(the operator's standing instruction: "Don't grant it verbally in
chat"). Do not write the change until the grant is on the record.

PRICE THE THREE ROADS in SPEC.md, each with the qualification-subject
consequence stated (changing the subject digest re-runs a ~14-minute,
~1160-call battery per home):
  A. carry the six fields in engine_config; notices become confirmations
  B. carry them in their resolution policies only, leaving engine_config
     as-is (three of the six already name a resolution pointer)
  C. leave carriage alone and make the notices a first-class typed
     disclosure the run echoes back

EVIDENCE ALREADY ON THE RECORD, do not re-derive: the stop report's
section 1 marks each of these "restored at run time from notice" with its
pointer, value and resolution — see docs/map/CON-configuration-stages.md
stage 3, and experiments/2026-09-03-change-stop-report/.

VALIDATION: full gate 0 failed; docs_verify 0 failed; the map moves in
the SAME commit; DELIVERY.md reconciles requirement by requirement.
```

---

## P2 — the installed-wheel operational smoke fails at `continuation_resume`

**What.** `python -u scripts/wheel_operational_smoke.py` exits 1 at
`stage: continuation_resume`, `failure_kind: assertion_failed`. NOT this
tranche's: the same smoke fails identically in a clean worktree at the
tranche base `7653b04393`, which carries none of this tranche's commits.
Envelope captured at `proof/wheel_operational_base_failure.json`.
`docs/AUDIT_BASELINES.md` (lines 195-202) baselines only smoke failures
naming the MCP schema sha or tool-set pins, so by that document this is a
finding, not a baseline. No gate runs this smoke, so nothing else will
catch it.

```
EXECUTOR WINDOW — DEFECT TRANCHE: the installed-wheel operational smoke
fails at continuation_resume, and no gate runs it

Read CLAUDE.md fully, then load deepreason-orchestrator, dr-drive-harness,
dr-ask-the-right-question and dr-explain-to-operator. Start at
dr-set-goal. Work on your window's assigned branch; commit and push at
every phase boundary.

THE DEFECT. `python -u scripts/wheel_operational_smoke.py` exits 1:

  "schema": "deepreason-wheel-operational-failure-v4"
  "stage": "continuation_resume"
  "failure_kind": "assertion_failed"
  "detail_code": null
  "first_lifecycle_state": "not_observed"
  "last_lifecycle_state": "not_observed"
  "timeout": false
  "cleanup_completed": true

MEASURED AS PRE-EXISTING, do not re-derive: the same smoke run in a clean
`git worktree add /tmp/base-tree 7653b04393` fails identically — same
stage, same failure_kind, same rc. Captured envelope:
experiments/2026-09-03-change-stop-report/proof/
wheel_operational_base_failure.json

WHY IT MATTERS. The wheel smokes are the third instrument and NO GATE
RUNS THEM (CLAUDE.md, "Build and test"). They pin the public surface over
the INSTALLED package. A silent failure here is exactly the class of rot
nothing else catches. docs/AUDIT_BASELINES.md:195-202 baselines only
failures naming the MCP schema sha or tool-set pins and says plainly that
"any OTHER smoke failure is a finding" — this names neither.

START AT THE RECORD, NOT THE CODE. dr-diagnose now REQUIRES the stop
report's classification section pasted verbatim at the top of
DIAGNOSIS.md when a run root exists. This failure is in a smoke harness
rather than a run root; say so explicitly in DIAGNOSIS.md and use the
smoke's own typed failure envelope as the equivalent first evidence.

FRAME IT AS A FORK THE RECORD CAN DECIDE, not a fix to apply:
  W: the smoke's continuation_resume assertion is stale and the product
     is fine (then the smoke is the defect)
  R: continuation genuinely regressed on the installed wheel (then the
     product is the defect, and the gate never saw it)
The first evidence that separates them: whether the same continuation
path passes in-tree under the full gate but fails on the built wheel.

VALIDATION: full gate 0 failed; both wheel smokes rc 0; if a pin moves,
it moves in the SAME commit and the smoke is re-run there.
```

---

## P3 — R18's own root inventory was written from narrative, not from `git ls-tree`

**What.** Not a code defect: a WORKFLOW finding, recorded because it is
the same failure mode this tranche exists to remove, committed one level
up. The window prompt's regression list named six failures and said "Run
the report against these committed roots". Three produced no run root at
all, and a fourth was miscast. Verified against each tranche's own
committed narrative and reconciled in SPEC.md's "THE MATERIAL
CONTRADICTION" section; the tranche delivered the PROPERTY (every box
demonstrated on committed evidence) rather than the literal naming.

No prompt is offered, deliberately. The remedy is not a tranche — it is
that a prompt naming committed evidence should cite it by a `git ls-tree`
line, the way this tranche's own proof script does. If a future window
wants that as a rule, it belongs in `authoring-skills`, and it should be
raised only after a SECOND recorded instance (the `authoring-skills` E1
tripwire: a workflow rule earns its place after two failures, not one).
This is instance one.
